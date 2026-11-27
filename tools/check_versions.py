#!/usr/bin/env python3
#
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Validate Terraform core and Google provider version constraints."""

import os
import pathlib
import re
import sys

SKIP_DIRS = frozenset(
    {
        ".git",
        ".terraform",
        ".venv",
        "venv",
        "node_modules",
        "__pycache__",
    }
)
VERSION_FILE_NAMES = ("versions.tf", "provider.tf", "providers.tf")
GOOGLE_PROVIDERS = frozenset({"hashicorp/google", "hashicorp/google-beta"})
MIN_TERRAFORM_VERSION = (1, 12, 2)
MIN_GOOGLE_VERSION = (8, 6, 0)
MAX_GOOGLE_VERSION_EXCL = (9, 0, 0)

_CLAUSE_RE = re.compile(r"^(~>|>=|<=|!=|=|>|<)?\s*(\d+(?:\.\d+){0,2})$")
_TERRAFORM_BLOCK_RE = re.compile(r"\bterraform\s*\{")
_REQUIRED_VERSION_RE = re.compile(r'\brequired_version\s*=\s*"([^"]*)"')
_REQUIRED_PROVIDERS_RE = re.compile(r"\brequired_providers\s*\{")
_PROVIDER_BLOCK_RE = re.compile(r"([A-Za-z0-9_-]+)\s*=\s*\{")
_SOURCE_RE = re.compile(r'\bsource\s*=\s*"([^"]*)"')
_VERSION_RE = re.compile(r'\bversion\s*=\s*"([^"]*)"')


def _format_ver(ver: tuple[int, int, int]) -> str:
    return ".".join(str(part) for part in ver)


def _strip_hcl_comments(body: str) -> str:
    """Strip HCL comments outside double-quoted strings and heredocs."""
    out: list[str] = []
    i = 0
    n = len(body)
    in_string = False
    heredoc_marker: str | None = None
    heredoc_indent = False

    while i < n:
        ch = body[i]
        if heredoc_marker is not None:
            line_end = body.find("\n", i)
            if line_end == -1:
                line_end = n
            line_text = body[i:line_end]
            check = line_text.lstrip(" \t") if heredoc_indent else line_text
            if check.rstrip("\r") == heredoc_marker:
                heredoc_marker = None
                heredoc_indent = False
            if line_end < n:
                out.append("\n")
                i = line_end + 1
            else:
                i = n
            continue

        if in_string:
            out.append(ch)
            if ch == "\\" and i + 1 < n:
                out.append(body[i + 1])
                i += 2
                continue
            if ch == '"':
                in_string = False
            i += 1
            continue

        if ch == "#" or body.startswith("//", i):
            line_end = body.find("\n", i)
            i = n if line_end == -1 else line_end
            continue

        if body.startswith("/*", i):
            end_idx = body.find("*/", i + 2)
            if end_idx != -1:
                out.append("\n" * body[i : end_idx + 2].count("\n"))
                i = end_idx + 2
                continue

        if ch == '"':
            in_string = True
            out.append(ch)
            i += 1
            continue

        if body.startswith("<<", i):
            match = re.match(r"<<(-?)\s*([A-Za-z_][A-Za-z0-9_]*)", body[i:])
            if match:
                out.append('""')
                line_end = body.find("\n", i + len(match.group(0)))
                if line_end == -1:
                    i = n
                else:
                    out.append("\n")
                    i = line_end + 1
                    heredoc_indent = match.group(1) == "-"
                    heredoc_marker = match.group(2)
                continue

        out.append(ch)
        i += 1

    return "".join(out)


def _extract_brace_body(text: str, open_brace_idx: int) -> tuple[str, int]:
    """Return body inside matching {...} starting at open_brace_idx."""
    depth = 0
    in_string = False
    i = open_brace_idx
    n = len(text)
    while i < n:
        ch = text[i]
        if in_string:
            if ch == "\\" and i + 1 < n:
                i += 2
                continue
            if ch == '"':
                in_string = False
        else:
            if ch == '"':
                in_string = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return text[open_brace_idx + 1 : i], i + 1
        i += 1
    return text[open_brace_idx + 1 :], n


def _parse_version_token(raw: str) -> tuple[tuple[int, int, int], int]:
    parts = [int(p) for p in raw.split(".")]
    precision = len(parts)
    while len(parts) < 3:
        parts.append(0)
    return (parts[0], parts[1], parts[2]), precision


def check_constraint(
    spec: str,
    min_lower: tuple[int, int, int],
    max_upper_excl: tuple[int, int, int] | None = None,
) -> str | None:
    """Validate a Terraform version constraint string against bounds."""
    clauses = [c.strip() for c in spec.split(",") if c.strip()]
    if not clauses:
        return "empty version constraint"

    eff_low: tuple[int, int, int] | None = None
    eff_low_inc = False
    eff_high: tuple[int, int, int] | None = None
    eff_high_inc = False
    excluded: set[tuple[int, int, int]] = set()

    def tighten_low(ver: tuple[int, int, int], inc: bool) -> None:
        nonlocal eff_low, eff_low_inc
        if eff_low is None or ver > eff_low:
            eff_low, eff_low_inc = ver, inc
        elif ver == eff_low and not inc:
            eff_low_inc = False

    def tighten_high(ver: tuple[int, int, int], inc: bool) -> None:
        nonlocal eff_high, eff_high_inc
        if eff_high is None or ver < eff_high:
            eff_high, eff_high_inc = ver, inc
        elif ver == eff_high and not inc:
            eff_high_inc = False

    for clause in clauses:
        match = _CLAUSE_RE.match(clause)
        if not match:
            return f"invalid constraint clause {clause!r}"
        op = match.group(1) or "="
        ver, precision = _parse_version_token(match.group(2))
        if op == "=":
            tighten_low(ver, True)
            tighten_high(ver, True)
        elif op == ">=":
            tighten_low(ver, True)
        elif op == ">":
            tighten_low(ver, False)
        elif op == "<=":
            tighten_high(ver, True)
        elif op == "<":
            tighten_high(ver, False)
        elif op == "!=":
            excluded.add(ver)
        elif op == "~>":
            tighten_low(ver, True)
            if precision <= 2:
                tighten_high((ver[0] + 1, 0, 0), False)
            else:
                tighten_high((ver[0], ver[1] + 1, 0), False)

    if eff_low is not None and eff_high is not None:
        if eff_low > eff_high or (
            eff_low == eff_high
            and (not eff_low_inc or not eff_high_inc or eff_low in excluded)
        ):
            return "contradictory version range"

    if eff_low is None or eff_low < min_lower:
        return f"must set lower bound >= {_format_ver(min_lower)}"

    if max_upper_excl is not None:
        if eff_high is None:
            return f"must set upper bound < {_format_ver(max_upper_excl)}"
        if eff_high > max_upper_excl or (
            eff_high == max_upper_excl and eff_high_inc
        ):
            return f"upper bound must be < {_format_ver(max_upper_excl)}"

    return None


def _parse_version_file(
    path: pathlib.Path,
) -> tuple[list[str], list[tuple[str, str | None, str | None]]]:
    """Extract required_version and required_providers from a .tf file."""
    cleaned = _strip_hcl_comments(path.read_text(encoding="utf-8"))
    required_versions: list[str] = []
    providers: list[tuple[str, str | None, str | None]] = []

    pos = 0
    while match := _TERRAFORM_BLOCK_RE.search(cleaned, pos):
        tf_body, end_pos = _extract_brace_body(cleaned, match.end() - 1)
        pos = end_pos
        for rv_match in _REQUIRED_VERSION_RE.finditer(tf_body):
            required_versions.append(rv_match.group(1))
        rp_pos = 0
        while rp_match := _REQUIRED_PROVIDERS_RE.search(tf_body, rp_pos):
            rp_body, rp_end = _extract_brace_body(tf_body, rp_match.end() - 1)
            rp_pos = rp_end
            prov_pos = 0
            while prov_match := _PROVIDER_BLOCK_RE.search(rp_body, prov_pos):
                prov_name = prov_match.group(1)
                prov_body, prov_end = _extract_brace_body(
                    rp_body, prov_match.end() - 1
                )
                prov_pos = prov_end
                src_m = _SOURCE_RE.search(prov_body)
                ver_m = _VERSION_RE.search(prov_body)
                providers.append(
                    (
                        prov_name,
                        src_m.group(1) if src_m else None,
                        ver_m.group(1) if ver_m else None,
                    )
                )

    return required_versions, providers


def _validate_file_constraints(
    vpath: pathlib.Path,
    rel_display: str,
    required_versions: list[str],
    providers: list[tuple[str, str | None, str | None]],
) -> list[str]:
    """Validate version constraints parsed from one file."""
    errors: list[str] = []
    vname = vpath.name
    for rv in required_versions:
        err = check_constraint(rv, MIN_TERRAFORM_VERSION)
        if err:
            errors.append(
                f"Invalid {vname} ({rel_display}): "
                f"required_version {rv!r} {err}"
            )
    for name, source, version in providers:
        if source is None and name in ("google", "google-beta"):
            errors.append(
                f"Invalid {vname} ({rel_display}): "
                f"missing source for provider {name!r}"
            )
            continue
        if source in GOOGLE_PROVIDERS:
            if not version:
                errors.append(
                    f"Invalid {vname} ({rel_display}): "
                    f"missing version for {source}"
                )
                continue
            err = check_constraint(
                version, MIN_GOOGLE_VERSION, MAX_GOOGLE_VERSION_EXCL
            )
            if err:
                errors.append(
                    f"Invalid {vname} ({rel_display}): "
                    f"{source} version {version!r} {err}"
                )
    return errors


def check_repo(basedir: pathlib.Path) -> list[str]:
    """Check all Terraform version and provider files under basedir."""
    errors: list[str] = []
    root = basedir.resolve()

    default_vfile = root / "default-versions.tf"
    if default_vfile.exists() and not default_vfile.is_symlink():
        rvs, providers = _parse_version_file(default_vfile)
        errors.extend(
            _validate_file_constraints(
                default_vfile, "default-versions.tf", rvs, providers
            )
        )
        missing = []
        if not rvs:
            missing.append("required_version")
        if not any(src == "hashicorp/google" for _, src, _ in providers):
            missing.append("hashicorp/google")
        if missing:
            errors.append(
                "Invalid default-versions.tf: missing " + ", ".join(missing)
            )

    for dp, dns, fns in os.walk(root, followlinks=False):
        cur_dir = pathlib.Path(dp)
        dns[:] = sorted(
            d
            for d in dns
            if d not in SKIP_DIRS and not (cur_dir / d).is_symlink()
        )
        rel_dir = cur_dir.relative_to(root)
        tf_files = [
            f
            for f in fns
            if f.endswith(".tf") and not (cur_dir / f).is_symlink()
        ]
        vfiles = [
            f
            for f in VERSION_FILE_NAMES
            if f in fns and not (cur_dir / f).is_symlink()
        ]

        if (
            rel_dir.parts
            and rel_dir.parts[0] == "blueprints"
            and tf_files
            and not vfiles
        ):
            errors.append(
                f"Invalid blueprint ({rel_dir.as_posix()}): "
                "missing versions.tf, provider.tf, or providers.tf"
            )
            continue

        if not vfiles:
            continue

        dir_rvs: list[str] = []
        dir_providers: list[tuple[str, str | None, str | None]] = []
        for vf in vfiles:
            vpath = cur_dir / vf
            rel_display = (rel_dir / vf).as_posix()
            rvs, providers = _parse_version_file(vpath)
            errors.extend(
                _validate_file_constraints(vpath, rel_display, rvs, providers)
            )
            dir_rvs.extend(rvs)
            dir_providers.extend(providers)

        is_non_google_recipe = (
            any(part.startswith("recipe-") for part in rel_dir.parts)
            and bool(dir_providers)
            and not any(src in GOOGLE_PROVIDERS for _, src, _ in dir_providers)
        )
        if is_non_google_recipe:
            continue

        missing_parts = []
        if not dir_rvs:
            missing_parts.append("required_version")
        if not any(src == "hashicorp/google" for _, src, _ in dir_providers):
            missing_parts.append("hashicorp/google")
        if missing_parts:
            primary_vf = vfiles[0]
            rel_primary = (rel_dir / primary_vf).as_posix()
            errors.append(
                f"Invalid {primary_vf} ({rel_primary}): "
                "missing " + ", ".join(missing_parts)
            )

    return errors


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint."""
    target = pathlib.Path(argv[0]) if argv else pathlib.Path(".")
    errors = check_repo(target)
    for err in errors:
        print(err)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
