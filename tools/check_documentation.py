#!/usr/bin/env python3
#
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "click",
#   "marko",
# ]
# ///
# Copyright 2023 Google LLC
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
"""Recursively check freshness of tfdoc's generated tables in README files.

This tool recursively checks that the embedded variables and outputs tables in
README files, match what is generated at runtime by tfdoc based on current
sources. As such, it accepts pretty much the same options as tfdoc does. Its
main use is in CI pipelines triggered by pull requests.
"""

import difflib
import enum
import os
import pathlib
import re

import click
import tfdoc

BASEDIR = pathlib.Path(__file__).resolve().parents[1]
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
TFDOCS_BEGIN = "<!-- BEGIN_TF_DOCS -->"
TFDOCS_END = "<!-- END_TF_DOCS -->"
LEGACY_TOC_MARK = "<!-- TOC -->"
# Paired legacy TOC markers in gitlab/README.md are updated in PR #556 (#546).
LEGACY_TOC_EXEMPT_DOCS = frozenset(
    {"blueprints/third-party-solutions/gitlab/README.md"}
)
_FENCE_OR_CODE_RE = re.compile(r"```.*?```|`[^`\n]+`", re.S)
_CFF_META_RE = re.compile(
    r"cloud-foundation-fabric/modules/[A-Za-z0-9_.-]+:v[0-9]+\.[0-9]+\.[0-9]+-tf"
)
_TAG_CANDIDATE_RE = re.compile(
    r"<!--[-!\s]*(?:(?:START|BEGIN|END)[_\s-]+)?"
    r"(?:TOC|TFDOC|TF_DOCS)\b[^>]*-->",
    re.IGNORECASE,
)
_CANONICAL_TAGS = frozenset(
    {
        tfdoc.MARK_BEGIN,
        tfdoc.MARK_END,
        TFDOCS_BEGIN,
        TFDOCS_END,
        tfdoc.TOC_BEGIN,
        tfdoc.TOC_END,
    }
)


class State(enum.IntEnum):
    SKIP = enum.auto()
    OK = enum.auto()
    FAIL_STALE_README = enum.auto()
    FAIL_STALE_TOC = enum.auto()
    FAIL_UNSORTED_VARS = enum.auto()
    FAIL_UNSORTED_OUTPUTS = enum.auto()
    FAIL_VARIABLE_PERIOD = enum.auto()
    FAIL_OUTPUT_PERIOD = enum.auto()
    FAIL_VARIABLE_DESCRIPTION = enum.auto()
    FAIL_OUTPUT_DESCRIPTION = enum.auto()
    FAIL_MISSING_TYPES = enum.auto()
    FAIL_MISSING_README = enum.auto()
    FAIL_MISSING_TFDOC = enum.auto()
    FAIL_MALFORMED_MARKERS = enum.auto()

    @property
    def failed(self):
        return self.value > State.OK

    @property
    def label(self):
        return {
            State.SKIP: "  ",
            State.OK: "✓",
            State.FAIL_STALE_README: "✗FAIL_STALE_README",
            State.FAIL_STALE_TOC: "✗FAIL_STALE_TOC",
            State.FAIL_UNSORTED_VARS: "✗FAIL_UNSORTED_VARS",
            State.FAIL_UNSORTED_OUTPUTS: "✗FAIL_UNSORTED_OUTPUTS",
            State.FAIL_VARIABLE_PERIOD: "✗FAIL_VARIABLE_PERIOD",
            State.FAIL_OUTPUT_PERIOD: "✗FAIL_OUTPUT_PERIOD",
            State.FAIL_VARIABLE_DESCRIPTION: "✗FAIL_VARIABLE_DESCRIPTION",
            State.FAIL_OUTPUT_DESCRIPTION: "✗FAIL_OUTPUT_DESCRIPTION",
            State.FAIL_MISSING_TYPES: "✗FAIL_MISSING_TYPES",
            State.FAIL_MISSING_README: "✗FAIL_MISSING_README",
            State.FAIL_MISSING_TFDOC: "✗FAIL_MISSING_TFDOC",
            State.FAIL_MALFORMED_MARKERS: "✗FAIL_MALFORMED_MARKERS",
        }[self.value]


def _relative_display(path):
    """Return path relative to BASEDIR when inside it, otherwise str(path)."""
    try:
        return str(path.relative_to(BASEDIR))
    except ValueError:
        return str(path)


def _check_markers(content, doc_rel, require_tfdoc=False, allow_tf_docs=False):
    """Validate TFDOC and TOC markers in a Markdown document."""
    cleaned = _FENCE_OR_CODE_RE.sub("", content)
    legacy_toc_allowed = (
        doc_rel in LEGACY_TOC_EXEMPT_DOCS
        and cleaned.count(LEGACY_TOC_MARK) == 2
    )

    bad_tags = [
        tag
        for tag in _TAG_CANDIDATE_RE.findall(cleaned)
        if tag not in _CANONICAL_TAGS
        and not tfdoc.MARK_OPTS_RE.fullmatch(tag)
        and not (legacy_toc_allowed and tag == LEGACY_TOC_MARK)
    ]
    if bad_tags:
        return (
            State.FAIL_MALFORMED_MARKERS,
            f"----- {doc_rel} malformed markers -----\n"
            f"Unexpected marker tag(s): {', '.join(bad_tags)}",
        )

    marker_spans = []
    for begin_mark, end_mark in (
        (tfdoc.MARK_BEGIN, tfdoc.MARK_END),
        (TFDOCS_BEGIN, TFDOCS_END),
        (tfdoc.TOC_BEGIN, tfdoc.TOC_END),
    ):
        begin_count = cleaned.count(begin_mark)
        end_count = cleaned.count(end_mark)
        if begin_count != end_count or begin_count > 1:
            return (
                State.FAIL_MALFORMED_MARKERS,
                f"----- {doc_rel} malformed markers -----\n"
                f"Expected paired {begin_mark} ({begin_count}) and "
                f"{end_mark} ({end_count}) at most once.",
            )
        if begin_count == 1:
            start = cleaned.find(begin_mark)
            end = cleaned.find(end_mark)
            if start > end:
                return (
                    State.FAIL_MALFORMED_MARKERS,
                    f"----- {doc_rel} malformed markers -----\n"
                    f"{end_mark} appears before {begin_mark}.",
                )
            marker_spans.append((begin_mark, start, end + len(end_mark)))

    has_tfdoc = cleaned.count(tfdoc.MARK_BEGIN) == 1
    has_tfdocs = cleaned.count(TFDOCS_BEGIN) == 1
    if has_tfdoc and has_tfdocs:
        return (
            State.FAIL_MALFORMED_MARKERS,
            f"----- {doc_rel} malformed markers -----\n"
            "Cannot mix TFDOC and TF_DOCS markers in one file.",
        )

    marker_spans.sort(key=lambda item: item[1])
    for (_, _, prev_end), (_, next_start, _) in zip(
        marker_spans, marker_spans[1:]
    ):
        if next_start < prev_end:
            return (
                State.FAIL_MALFORMED_MARKERS,
                f"----- {doc_rel} malformed markers -----\n"
                "Marker blocks must not overlap.",
            )

    if require_tfdoc and not (has_tfdoc or (allow_tf_docs and has_tfdocs)):
        return (
            State.FAIL_MISSING_TFDOC,
            f"----- {doc_rel} missing TFDOC markers -----\n"
            f"Expected {tfdoc.MARK_BEGIN} and {tfdoc.MARK_END}.",
        )

    return None


def _load_cff_base_modules():
    """Return bare module names tracked from CFF in tools/cff-sync.bases."""
    bases_path = BASEDIR / "tools" / "cff-sync.bases"
    if not bases_path.is_file():
        return frozenset()
    modules = set()
    for raw in bases_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        target = line.split()[0]
        if "/" not in target:
            modules.add(target)
    return frozenset(modules)


def _is_vendored_cff_module(mod_dir, cff_bases=None):
    """Return True for plain upstream-vendored CFF modules (#660)."""
    name = mod_dir.name
    if name.endswith("-se"):
        return False
    if cff_bases is None:
        cff_bases = _load_cff_base_modules()
    if name in cff_bases:
        return True
    vfile = mod_dir / "versions.tf"
    if vfile.is_file() and not vfile.is_symlink():
        return bool(_CFF_META_RE.search(vfile.read_text(encoding="utf-8")))
    return False


def _check_dir(dir_name, exclude_files=None, files=False, show_extra=False):
    "Invoke tfdoc on folder, using the relevant options."
    dir_path = pathlib.Path(dir_name)
    if not dir_path.is_absolute():
        dir_path = BASEDIR / dir_path
    if not dir_path.exists():
        raise SystemExit(f"Directory not found: {dir_path}")

    cff_bases = _load_cff_base_modules()
    for dp, dns, fns in os.walk(dir_path, followlinks=False):
        cur_dir = pathlib.Path(dp)
        try:
            rel_parts = cur_dir.relative_to(BASEDIR).parts
        except ValueError:
            rel_parts = ()
        in_modules = len(rel_parts) > 0 and rel_parts[0] == "modules"
        # Skip plain vendored CFF modules and prune their subdirs (#660).
        if (
            in_modules
            and len(rel_parts) >= 2
            and _is_vendored_cff_module(
                BASEDIR / "modules" / rel_parts[1], cff_bases
            )
        ):
            dns[:] = []
            continue
        dns[:] = sorted(
            d
            for d in dns
            if d not in SKIP_DIRS and not (cur_dir / d).is_symlink()
        )
        is_tf_dir = any(
            f.endswith(".tf") and not (cur_dir / f).is_symlink() for f in fns
        )
        md_names = sorted(
            f
            for f in fns
            if f.endswith(".md") and not (cur_dir / f).is_symlink()
        )

        if is_tf_dir and "README.md" not in md_names:
            missing_rel = _relative_display(cur_dir / "README.md")
            yield (
                missing_rel,
                State.FAIL_MISSING_README,
                f"----- {missing_rel} missing -----\n"
                "Terraform directory is missing README.md.",
            )

        for md_name in md_names:
            readme_path = cur_dir / md_name
            diff = None
            readme = readme_path.read_text(encoding="utf-8")
            readme_rel = _relative_display(readme_path)
            marker_err = _check_markers(
                readme,
                readme_rel,
                require_tfdoc=is_tf_dir and md_name == "README.md",
                allow_tf_docs=in_modules,
            )
            if marker_err:
                state, diff = marker_err
                yield readme_rel, state, diff
                continue

            current_doc = tfdoc.get_tfref_parts(readme)
            current_toc = tfdoc.get_toc_parts(readme)
            if not (current_doc or current_toc):
                continue

            new_doc = (
                tfdoc.create_tfref(
                    readme_path.parent, files, show_extra, exclude_files, readme
                )
                if current_doc
                else None
            )
            new_toc = tfdoc.create_toc(readme) if current_toc else None
            newvars = new_doc.variables if new_doc else []
            newouts = new_doc.outputs if new_doc else []
            variables = [
                v.name for v in newvars if v.file.endswith("variables.tf")
            ]
            outputs = [o.name for o in newouts if o.file.endswith("outputs.tf")]

            state = State.OK

            if current_doc and new_doc.content != current_doc["doc"]:
                state = State.FAIL_STALE_README
                header = f"----- {readme_rel} diff -----\n"
                ndiff = difflib.ndiff(
                    current_doc["doc"].splitlines(keepends=True),
                    new_doc.content.splitlines(keepends=True),
                )
                diff = "".join([header] + [x for x in ndiff if x[0] != " "])

            elif current_toc and new_toc != current_toc["toc"]:
                state = State.FAIL_STALE_TOC
                header = f"----- {readme_rel} diff -----\n"
                ndiff = difflib.ndiff(
                    current_toc["toc"].splitlines(keepends=True),
                    new_toc.splitlines(keepends=True),
                )
                diff = "".join([header] + [x for x in ndiff if x[0] != " "])

            elif current_doc and (
                empty := [v.name for v in newvars if not v.description]
            ):
                state = State.FAIL_VARIABLE_DESCRIPTION
                diff = "\n".join(
                    [
                        f"----- {readme_rel} variables missing description "
                        "-----",
                        ", ".join(empty),
                    ]
                )

            elif current_doc and (
                empty := [o.name for o in newouts if not o.description]
            ):
                state = State.FAIL_OUTPUT_DESCRIPTION
                diff = "\n".join(
                    [
                        f"----- {readme_rel} outputs missing description -----",
                        ", ".join(empty),
                    ]
                )

            elif current_doc and variables != sorted(variables):
                state = State.FAIL_UNSORTED_VARS
                diff = "\n".join(
                    [
                        f"----- {readme_rel} variables -----",
                        "variables should be in this order: ",
                        ", ".join(sorted(variables)),
                    ]
                )

            elif current_doc and outputs != sorted(outputs):
                state = State.FAIL_UNSORTED_OUTPUTS
                diff = "\n".join(
                    [
                        f"----- {readme_rel} outputs -----",
                        "outputs should be in this order: ",
                        ", ".join(sorted(outputs)),
                    ]
                )

            elif current_doc and (
                nc := [
                    v.name for v in newvars if not v.description.endswith(".")
                ]
            ):
                state = State.FAIL_VARIABLE_PERIOD
                diff = "\n".join(
                    [
                        f"----- {readme_rel} variable descriptions missing "
                        "ending period -----",
                        ", ".join(nc),
                    ]
                )

            elif current_doc and (
                nc := [
                    o.name for o in newouts if not o.description.endswith(".")
                ]
            ):
                state = State.FAIL_OUTPUT_PERIOD
                diff = "\n".join(
                    [
                        f"----- {readme_rel} output descriptions missing "
                        "ending period -----",
                        ", ".join(nc),
                    ]
                )

            elif current_doc and (
                no_types := [v.name for v in newvars if not v.type]
            ):
                state = State.FAIL_MISSING_TYPES
                diff = "\n".join(
                    [
                        f"----- {readme_rel} variables without types -----",
                        ", ".join(no_types),
                    ]
                )

            yield readme_rel, state, diff


@click.command()
@click.argument("dirs", type=str, nargs=-1)
@click.option("--exclude-file", "-x", multiple=True)
@click.option("--files/--no-files", default=False)
@click.option("--show-diffs/--no-show-diffs", default=False)
@click.option("--show-extra/--no-show-extra", default=False)
@click.option("--show-summary/--no-show-summary", default=True)
def main(
    dirs,
    exclude_file=None,
    files=False,
    show_diffs=False,
    show_extra=False,
    show_summary=True,
):
    "Cycle through modules and ensure READMEs are up-to-date."
    # print(f'files: {files}, extra: {show_extra}, diffs: {show_diffs}\n')
    errors = []
    for dir_name in dirs:
        result = _check_dir(dir_name, exclude_file, files, show_extra)
        for readme_path, state, diff in result:
            if state.failed:
                errors.append((readme_path, diff))
            if show_summary:
                print(f"[{state.label}] {readme_path}")

    if errors:
        print("\nErrored modules:\n")
        for e in errors:
            module, diff = e
            print(f"- {module}")
            if show_diffs:
                print()
                print("".join(diff))
                print()
        print()
        raise SystemExit("Errors found.")


if __name__ == "__main__":
    main()
