#!/usr/bin/env python3
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Shared File I/O and String Manipulation Utilities for Compliance Engine.

This module provides common, OS-agnostic filesystem operations, path resolution
using pathlib, schema validation, path traversal defense, and sanitized
string/XML manipulation utilities used across the compliance generation,
hydration, extraction, and validation pipeline.
"""

import enum
import errno
try:
    import fcntl
except ImportError:  # pragma: no cover - Windows
    fcntl = None  # type: ignore[assignment]
import glob
import html
import json
import logging
import os
import random
import subprocess
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import re
import stat
import sys
import tempfile
from typing import Any, Callable, Dict, Final, List, Mapping, Optional, Sequence, Tuple, Union
import unicodedata
import urllib.parse

logger = logging.getLogger(__name__)


def current_utc_datetime() -> datetime:
    """Returns UTC datetime from SOURCE_DATE_EPOCH if set, otherwise wall-clock UTC now."""
    epoch_raw = os.environ.get("SOURCE_DATE_EPOCH", "").strip()
    if epoch_raw:
        try:
            epoch_val = max(315532800, int(epoch_raw))
            return datetime.fromtimestamp(epoch_val, tz=timezone.utc)
        except (ValueError, OSError, OverflowError):
            pass
    return datetime.now(timezone.utc)


def zip_entry_date_time() -> Tuple[int, int, int, int, int, int]:
    """Returns a deterministic 6-tuple (Y, M, D, H, M, S) >= 1980-01-01 for ZipInfo."""
    dt = current_utc_datetime()
    if dt.year < 1980:
        return (1980, 1, 1, 0, 0, 0)
    return (dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)


# Environment variable holding an explicit, operator-curated list of additional
# site-packages directories (os.pathsep separated).
_SITE_PACKAGES_ENV: Final[str] = "COMPLIANCE_SITE_PACKAGES"

# When set to a truthy value, sys.path is never extended: COMPLIANCE_SITE_PACKAGES and
# the foreign-virtualenv discovery below are both skipped, even if
# COMPLIANCE_ALLOW_BORROWED_DEPS is also set. Accredited deployments set this so that
# every dependency comes from the pinned interpreter environment.
_STRICT_DEPS_ENV: Final[str] = "COMPLIANCE_STRICT_DEPS"

# When set to a truthy value (and strict mode is off), a missing PyYAML triggers a
# search of the pipx/Homebrew checkov virtualenvs listed below. Off by default:
# packages found there are versioned by checkov's releases rather than by
# requirements.txt, and checkov's bc-python-hcl2 fork is refused by the HCL backend
# canary in hcl_parser.py.
_ALLOW_BORROWED_DEPS_ENV: Final[str] = "COMPLIANCE_ALLOW_BORROWED_DEPS"

# Last-resort discovery patterns for environments where the operator installed the
# supporting toolchain via pipx/Homebrew rather than into the active interpreter.
_FOREIGN_TOOLCHAIN_PATTERNS: Final[Tuple[str, ...]] = (
    "~/.local/share/pipx/venvs/checkov/lib/python*/site-packages",
    "/opt/homebrew/Cellar/checkov/*/libexec/lib/python*/site-packages",
    "/usr/local/Cellar/checkov/*/libexec/lib/python*/site-packages",
)


def env_flag_enabled(env_var: str) -> bool:
    """Returns True when an environment variable holds an affirmative value.

    This is the single parser for operator switches such as
    COMPLIANCE_DISABLE_LIVE_SCANNERS, so every module agrees on what "set" means.

    Args:
        env_var: Name of the environment variable to inspect.

    Returns:
        True when the variable is set to 1/true/yes/on (case-insensitive).
    """
    return os.environ.get(env_var, "").strip().lower() in {"1", "true", "yes", "on"}


def _is_safe_site_packages_dir(candidate: str) -> bool:
    """Validates that a candidate import directory is safe to place on ``sys.path``.

    Anything placed on ``sys.path`` is arbitrary code execution at import time, so
    a candidate is accepted only when it is an absolute, existing, non-symlinked
    directory that is not group- or world-writable (CWE-426, CWE-732).

    Args:
        candidate: Filesystem path proposed for ``sys.path`` insertion.

    Returns:
        True when the directory passes every safety check.
    """
    if not candidate or not os.path.isabs(candidate):
        logger.warning("Refusing non-absolute import path %r", candidate)
        return False
    try:
        # lstat first so a symlinked directory is rejected rather than followed.
        link_info = os.lstat(candidate)
        if stat.S_ISLNK(link_info.st_mode):
            logger.warning("Refusing symlinked import path %r", candidate)
            return False
        info = os.stat(candidate)
    except OSError as err:
        logger.debug("Skipping unusable import path %r: %s", candidate, err)
        return False

    if not stat.S_ISDIR(info.st_mode):
        logger.warning("Refusing non-directory import path %r", candidate)
        return False
    if info.st_mode & (stat.S_IWGRP | stat.S_IWOTH):
        logger.warning(
            "Refusing group/world-writable import path %r (mode %o); a writable "
            "sys.path entry permits arbitrary code injection",
            candidate,
            stat.S_IMODE(info.st_mode),
        )
        return False
    return True


def _append_validated_paths(candidates: Sequence[str], provenance: str) -> List[str]:
    """Appends validated directories to ``sys.path`` and records their provenance.

    Args:
        candidates: Proposed import directories.
        provenance: Human-readable description of where the candidates came from.

    Returns:
        The list of paths actually appended to ``sys.path``.
    """
    appended: List[str] = []
    for candidate in candidates:
        resolved = os.path.abspath(os.path.expanduser(candidate))
        if resolved in sys.path:
            continue
        if not _is_safe_site_packages_dir(resolved):
            continue
        sys.path.append(resolved)
        appended.append(resolved)
        logger.warning(
            "Supply-chain notice: added import path %r to sys.path (source: %s). "
            "Dependency provenance is now outside the active interpreter environment.",
            resolved,
            provenance,
        )
    return appended


def _bootstrap_environment() -> None:
    """Extends ``sys.path`` with operator-approved dependency locations.

    When ``COMPLIANCE_STRICT_DEPS`` is truthy nothing is added and the function
    returns immediately. Otherwise the resolution order is:

    1. Directories explicitly listed in ``COMPLIANCE_SITE_PACKAGES``.
    2. Only if PyYAML still cannot be imported and ``COMPLIANCE_ALLOW_BORROWED_DEPS``
       is truthy: a last-resort scan of known pipx/Homebrew checkov virtualenvs.

    Every accepted directory is validated (absolute, real directory, not a symlink,
    not group/world-writable) and logged at WARNING level, because borrowing a
    dependency from a foreign virtualenv means the engine's dependency versions are
    controlled by an unrelated tool's release cadence rather than by this project's
    pinned manifest. Strict mode makes an accredited deployment fail closed (PyYAML
    ImportError at import time) instead of importing from an unattested location.
    """
    if env_flag_enabled(_STRICT_DEPS_ENV):
        logger.debug(
            "%s is enabled; restricting imports to the active interpreter environment.",
            _STRICT_DEPS_ENV,
        )
        return

    explicit = [p for p in os.environ.get(_SITE_PACKAGES_ENV, "").split(os.pathsep) if p.strip()]
    if explicit:
        _append_validated_paths(explicit, f"{_SITE_PACKAGES_ENV} environment variable")

    # Availability probe, not an operation: PyYAML being absent is the precondition
    # for the last-resort discovery below, so the ImportError is the expected signal
    # rather than a swallowed error. Success short-circuits any sys.path mutation.
    try:
        import yaml as _probe
        _ = _probe
    except ImportError:
        pass
    else:
        return

    if not env_flag_enabled(_ALLOW_BORROWED_DEPS_ENV):
        logger.debug(
            "PyYAML is not importable and %s is not set; not searching other tools' "
            "virtualenvs.",
            _ALLOW_BORROWED_DEPS_ENV,
        )
        return

    discovered: List[str] = []
    for pattern in _FOREIGN_TOOLCHAIN_PATTERNS:
        discovered.extend(sorted(glob.glob(os.path.expanduser(pattern))))
    if discovered:
        _append_validated_paths(discovered, "foreign toolchain virtualenv discovery (last resort)")


_bootstrap_environment()

try:
    import yaml
except ImportError as err:
    raise ImportError(
        "PyYAML is a required dependency for secure and accurate YAML parsing. "
        "Install the pinned dependency set with "
        "'python3 -m pip install -r .gemini/skills/compliance/requirements.txt'."
    ) from err

# ---------------------------------------------------------------------------
# Resource budgets (CWE-400: Uncontrolled Resource Consumption)
# ---------------------------------------------------------------------------

# Maximum size of a single text artifact read into memory.
MAX_TEXT_FILE_BYTES: Final[int] = 64 * 1024 * 1024  # 64 MiB

# Maximum size of a YAML document accepted for parsing.
MAX_YAML_BYTES: Final[int] = 16 * 1024 * 1024  # 16 MiB

# Maximum number of YAML alias references permitted in a single document.
# PyYAML's SafeLoader expands aliases eagerly and applies no expansion budget, so a
# nested-alias document ("YAML billion laughs", CWE-776) can exhaust memory even
# under safe_load. Bounding alias count bounds the expansion factor.
MAX_YAML_ALIASES: Final[int] = 512

# Maximum recursion depth honored when walking nested structures.
MAX_STRUCTURE_DEPTH: Final[int] = 128

# Maximum number of percent-decoding rounds applied to an untrusted filename before
# it is rejected as deliberately obfuscated.
MAX_PERCENT_DECODE_ROUNDS: Final[int] = 8

# Maximum characters of a single string value inspected by the secret scrubber.
# Strings longer than this are redacted outright rather than scanned, which bounds
# regex work and fails closed on values too large to inspect.
MAX_SECRET_SCAN_CHARS: Final[int] = 1 * 1024 * 1024  # 1 MiB

# Maximum allowable characters in an Excel cell (Excel limit 32,767 with injection headroom)
MAX_EXCEL_CELL_LENGTH: int = 32760

# Leading characters that make a spreadsheet treat a cell as a formula (CWE-1236).
# '+' and '-' are handled in clean_cell_value so that plain numbers stay numeric.
FORMULA_TRIGGER_CHARS = frozenset({
    "=", "@", "|", "%", "\t", "\r", "\n", ";",
    "\uff1d",  # Fullwidth Equals Sign (＝)
    "\uff20",  # Fullwidth Commercial At (＠)
    "\uff5c",  # Fullwidth Vertical Line (｜)
    "\uff05",  # Fullwidth Percent Sign (％)
})

# Regular expression matching leading whitespace, ASCII control characters, Unicode
# whitespace, zero-width characters, byte-order marks, and bidirectional control
# characters.
#
# The bidirectional ranges matter for two reasons:
#   * U+202A-U+202E (embeddings/overrides) and U+2066-U+2069 (isolates) can be placed
#     ahead of a formula trigger so that the payload is not recognized as leading, which
#     bypasses spreadsheet formula-injection quoting (CWE-1236).
#   * The same characters reorder rendered text, so a cell can display something other
#     than what it contains - the "Trojan Source" homoglyph/reordering class
#     (CVE-2021-42574). In an authorization artifact, text that renders differently to
#     the assessor than it evaluates is an integrity defect in its own right.
LEADING_DANGEROUS_CHARS_PATTERN = re.compile(
    r"^[\s\x00-\x1f\x7f-\x9f\u00a0\u00ad\u1680\u2000-\u200f\u2028\u2029"
    r"\u202a-\u202f\u205f\u2066-\u2069\u3000\ufeff\ufff9-\ufffb;]+",
    re.UNICODE,
)

# Matches a YAML alias or anchor reference (``*anchor``). Deliberately
# linear with no nested quantifiers so scanning an untrusted document cannot itself
# become a ReDoS vector. Matches aliases (including numeric/hyphen anchor names) at
# line start or after whitespace, commas, or flow-collection brackets ``[`` / ``{``.
YAML_ALIAS_PATTERN = re.compile(r"(?:^|[\s,\[\{])\*[A-Za-z0-9_-][\w.-]*")

# Maximum number of extra nodes that alias references may add when the loaded YAML
# document is expanded (serialized, deep-copied or walked). PyYAML loads aliases as
# shared references, so a small alias DAG loads quickly and only explodes later.
MAX_YAML_EXPANDED_NODES: Final[int] = 10_000


class YamlBudgetError(ValueError):
    """A YAML/JSON document exceeds a size, alias, expansion or nesting budget."""


def _yaml_expansion(root: Any) -> Tuple[int, int]:
    """Returns (expanded_nodes, distinct_nodes) without expanding shared references.

    Sizes are memoized per container identity, so the walk is linear in the number
    of distinct containers even when the expanded size is exponential.

    Raises:
        YamlBudgetError: If the structure contains a reference cycle.
    """
    sizes: Dict[int, int] = {}
    distinct = 0
    on_path: set = set()
    stack: List[Tuple[Any, bool]] = [(root, False)]
    while stack:
        node, finished = stack.pop()
        if not isinstance(node, (dict, list)):
            continue
        node_id = id(node)
        children = list(node.values()) if isinstance(node, dict) else node
        if finished:
            on_path.discard(node_id)
            total = 1
            for child in children:
                total += sizes[id(child)] if isinstance(child, (dict, list)) else 1
            sizes[node_id] = total
            distinct += 1 + sum(1 for child in children if not isinstance(child, (dict, list)))
            continue
        if node_id in sizes:
            continue
        if node_id in on_path:
            raise YamlBudgetError("YAML document contains a recursive alias reference")
        on_path.add(node_id)
        stack.append((node, True))
        stack.extend((child, False) for child in children if isinstance(child, (dict, list)) and id(child) not in sizes)
    expanded = sizes.get(id(root), 1) if isinstance(root, (dict, list)) else 1
    return expanded, max(distinct, 1)


# Regular expression matching credential and secret variable names
SENSITIVE_KEY_PATTERNS = re.compile(
    r"(password|passwd|pwd|passphrase|secret|private[_-]?key|privkey|token|credential|"
    r"api[_-]?key|auth[_-]?token|access[_-]?token|client[_-]?secret|master[_-]?key|cert[_-]?key|"
    r"ssh[_-]?key|signing[_-]?key|encryption[_-]?key|session[_-]?key|"
    r"raw[_-]?key|csek|disk[_-]?encryption[_-]?key[_-]?raw|disk[_-]?encryption[_-]?key[_-]?rsa|"
    r"auth[_-]?string|auth[_-]?key|bearer|passcode|\.pfx|\.pem|\.key|\.pkcs12)",
    re.IGNORECASE,
)

# Regular expression matching PEM formatted private keys (PKCS#1, PKCS#8, EC, OpenSSH, PGP, etc.)
# Bounded to 8192 characters between delimiters to eliminate catastrophic backtracking (ReDoS) on large files
PRIVATE_KEY_PATTERN = re.compile(
    r"-----BEGIN\s+[A-Z0-9\s_-]*(?:PRIVATE KEY|PRIVATE KEY BLOCK|SECRET KEY|RSA PRIVATE KEY|EC PRIVATE KEY|DSA PRIVATE KEY|OPENSSH PRIVATE KEY)-----"
    r"[\s\S]{0,8192}?"
    r"-----END\s+[A-Z0-9\s_-]*(?:PRIVATE KEY|PRIVATE KEY BLOCK|SECRET KEY|RSA PRIVATE KEY|EC PRIVATE KEY|DSA PRIVATE KEY|OPENSSH PRIVATE KEY)-----|"
    r"-----BEGIN[^\n\r]*PRIVATE KEY[^\n\r]*-----[\s\S]{0,8192}?-----END[^\n\r]*PRIVATE KEY[^\n\r]*-----",
    re.IGNORECASE,
)

# High-entropy cloud credentials, API tokens, and bearer credentials.
#
# Every alternative is anchored so it cannot fire on ordinary dotted identifiers.
# This matters specifically for the HashiCorp Vault forms: an unanchored
# ``(?:hvs|s)\.[0-9A-Za-z_-]{20,}`` matches any word ending in "s" followed by a
# dot and a long identifier, which in this domain means `modules.network_hub_...`,
# `docs.security_control_...`, `requirements.txt_...` and Semgrep rule IDs all
# register as credentials. Redaction is destructive, so a false positive silently
# deletes real content from an accreditation deliverable.
HIGH_ENTROPY_SECRET_PATTERN = re.compile(
    r"(?:AIza[0-9A-Za-z_-]{35}|"  # GCP API Key
    r"ya29\.[0-9A-Za-z_-]{20,}|"  # GCP OAuth token
    r"GOCSPX-[0-9A-Za-z_-]{20,}|"  # Google OAuth client secret
    r"AKIA[0-9A-Z]{16}|"  # AWS Access Key ID
    r"gh[pousr]_[A-Za-z0-9_]{20,}|"  # GitHub Personal Access Token
    r"xox[baprs]-[0-9a-zA-Z-]{20,}|"  # Slack Token
    r"https://hooks\.slack\.com/services/[A-Za-z0-9/_-]+|"  # Slack incoming webhook
    r"(?<![a-zA-Z0-9+.-])[a-zA-Z][a-zA-Z0-9+.-]{0,31}://[^/\s:@\"']{1,256}:[^/\s@\"']{1,256}@[^\s\"']+|"  # URI-embedded credentials
    r"(?<![0-9A-Za-z_-])eyJ[0-9A-Za-z_-]{15,}\.[0-9A-Za-z_-]{15,}\.[0-9A-Za-z_-]{15,}(?![0-9A-Za-z_-])|"  # JWT (OIDC, OAuth, Service Account identity tokens)
    # Vault batch/recovery/service tokens: 'hvs.', 'hvb.', 'hvr.' prefixes.
    r"(?<![0-9A-Za-z_-])hv[sbr]\.[0-9A-Za-z_-]{20,}|"
    # Legacy Vault service token: literal 's.' followed by 24+ alphanumerics.
    # Alphanumeric-only (no '_' or '-') is what Vault actually emits, and it is
    # what separates a token from a snake_case identifier.
    r"(?<![0-9A-Za-z_-])s\.[0-9A-Za-z]{24,}(?![0-9A-Za-z])|"
    r"(?<![A-Za-z0-9+/._-])[A-Za-z0-9+/]{43}=(?![A-Za-z0-9+/=])|"  # 32-byte (256-bit) base64 raw key (e.g. CSEK)
    r"(?<![0-9a-fA-F-])[0-9a-fA-F]{32}(?![0-9a-fA-F-])|"  # Continuous 32-char Hex Secret
    # Continuous 64-char Hex Secret (exempting sha256:/sha384:/sha512: container/file digests)
    r"(?<!sha256:)(?<!sha256-)(?<!sha384:)(?<!sha512:)(?<![0-9a-fA-F-])[0-9a-fA-F]{64}(?![0-9a-fA-F-])|"
    r"\"private_key\"\s*:\s*\"-----BEGIN[^\"]+\")",  # GCP Service Account JSON key
    re.IGNORECASE,
)

#: Replacement text substituted for any detected credential.
REDACTION_MARKER: Final[str] = "[REDACTED_SENSITIVE]"

#: FedRAMP Marketplace package identifier for the inherited cloud provider
#: authorization, quoted in every inheritance narrative in the SSP and SCTM.
#:
#: This is a factual assertion an assessor will independently look up, and it is
#: correct only for a Google Cloud tenancy holding the current package. Override
#: it with ``system_information.csp_pato_package_id`` in ``compliance_config.yaml``
#: for any other CSP, and re-verify it against marketplace.fedramp.gov before the
#: package is submitted -- provisional authorizations are re-issued.
DEFAULT_CSP_PATO_PACKAGE_ID: Final[str] = "FR1805751477"

#: Collapses runs of adjacent markers (with optional separating punctuation or
#: whitespace) left behind when several credentials appear back to back.
ADJACENT_REDACTION_PATTERN = re.compile(
    r"(?:" + re.escape(REDACTION_MARKER) + r")(?:[\s,;:.\-_/\\]*" + re.escape(REDACTION_MARKER) + r")+"
)

# Illegal XML 1.0 Fourth/Fifth Edition characters:
# XML 1.0 valid chars: #x9 | #xA | #xD | [#x20-#xD7FF] | [#xE000-#xFFFD] | [#x10000-#x10FFFF]
# Disallowed: C0 controls (0x00-0x08, 0x0B-0x0C, 0x0E-0x1F), DEL and C1 controls (0x7F-0x84, 0x86-0x9F),
# surrogates (0xD800-0xDFFF), and noncharacters (0xFFFE, 0xFFFF).
XML_ILLEGAL_CHARS_PATTERN = re.compile(
    r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x84\x86-\x9F\uD800-\uDFFF\uFFFE\uFFFF]"
)

# Windows reserved device names (CWE-22 / OS command injection / device locking)
WINDOWS_RESERVED_DEVICE_NAMES = frozenset({
    "CON", "PRN", "AUX", "NUL",
    "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
    "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9",
})

#: Canonical set of directory names pruned during workspace traversal across the
#: extraction, scanner, and validation modules.
IGNORED_TRAVERSAL_DIRS: Final[frozenset] = frozenset({
    ".git",
    ".terraform",
    "node_modules",
    "vendor",
    "ato_artifacts",
    "__pycache__",
    ".venv",
    "venv",
    "env",
    ".tox",
    "dist",
    "build",
    ".eggs",
})

# Percent-encoded path separator or dot characters (e.g. %2e, %2f, %5c, %00)
# that would cause a check-vs-use differential if unquoted only during validation
# while the caller opens the literal path.
_ENCODED_TRAVERSAL_OR_SEP_RE: Final[re.Pattern[str]] = re.compile(
    r"%(?:2e|2f|5c|00)", re.IGNORECASE
)


def is_ignored_traversal_dir(dirname: str) -> bool:
    """Returns True if ``dirname`` is an excluded build/cache/artifact directory.

    Args:
        dirname: Single directory basename inspected during ``os.walk`` pruning.

    Returns:
        True when the directory should be excluded from workspace traversal.
    """
    return (
        dirname in IGNORED_TRAVERSAL_DIRS
        or dirname.startswith("ato_artifacts_backup")
    )


def _safe_exists(path: Path) -> bool:
    """Returns ``path.exists()`` while guarding against ``OSError`` (e.g. ELOOP)."""
    try:
        return path.exists()
    except OSError:
        return False


def _safe_is_file(path: Path) -> bool:
    """Returns ``path.is_file()`` while guarding against ``OSError`` (e.g. ELOOP)."""
    try:
        return path.is_file()
    except OSError:
        return False


def _safe_is_dir(path: Path) -> bool:
    """Returns ``path.is_dir()`` while guarding against ``OSError`` (e.g. ELOOP)."""
    try:
        return path.is_dir()
    except OSError:
        return False


def _safe_is_symlink(path: Path) -> bool:
    """Returns ``path.is_symlink()`` while guarding against ``OSError``."""
    try:
        return path.is_symlink()
    except OSError:
        return False


def get_skill_root() -> Path:
    """Returns the absolute Path to the compliance skill root directory (or installed package root)."""
    cur = Path(__file__).resolve().parent
    if _safe_is_dir(cur / "templates") and _safe_is_dir(cur / "config"):
        return cur
    for p in (cur.parent, cur.parent.parent, cur.parent.parent.parent):
        if (
            _safe_exists(p / "SKILL.md")
            or _safe_exists(p / "pyproject.toml")
            or (_safe_is_dir(p / "templates") and _safe_is_dir(p / "config"))
        ):
            return p
    try:
        import importlib.resources as _pkg_resources
        pkg_root = Path(str(_pkg_resources.files("compliance_engine")))
        if _safe_is_dir(pkg_root / "templates") and _safe_is_dir(pkg_root / "config"):
            return pkg_root
    except (ImportError, TypeError, ValueError):
        pass
    return cur.parent.parent


def get_templates_dir() -> Path:
    """Returns the absolute Path to the compliance templates directory.

    Returns:
        Path object pointing to .gemini/skills/compliance/templates.
    """
    return get_skill_root() / "templates"


def get_scripts_dir() -> Path:
    """Returns the absolute Path to the compliance scripts directory.

    Returns:
        Path object pointing to .gemini/skills/compliance/scripts.
    """
    return get_skill_root() / "scripts"


def resolve_path(target_path: Union[str, Path]) -> Path:
    """Resolves an absolute or relative path into a normalized Path object.

    Args:
        target_path: String or Path representing a filesystem path.

    Returns:
        Fully resolved absolute Path object.
    """
    return Path(target_path).resolve()


def ensure_directory(
    dir_path: Union[str, Path],
    allowed_boundary: Optional[Union[str, Path]] = None,
) -> Path:
    """Ensures a directory and any intermediate parent directories exist.

    Args:
        dir_path: String or Path representing the directory to create.
        allowed_boundary: Optional root boundary directory; when supplied,
            ``ensure_path_within_boundary`` is enforced with ``allow_symlinks=False``
            before ``mkdir`` is invoked (VULN-12b).

    Returns:
        Resolved Path object of the created or existing directory.

    Raises:
        PermissionError: If ``dir_path`` traverses a symlink or escapes
            ``allowed_boundary``.
    """
    supplied = Path(dir_path)
    if _safe_is_symlink(supplied):
        raise PermissionError(
            f"Refusing to create directory through symbolic link '{supplied}' (CWE-59)"
        )
    if allowed_boundary is not None:
        resolved = ensure_path_within_boundary(
            supplied, allowed_boundary, allow_symlinks=False
        )
    else:
        resolved = supplied.resolve()
    resolved.mkdir(parents=True, exist_ok=True)
    return resolved


def find_enclosing_repo_root(start_dir: Union[str, Path]) -> Optional[Path]:
    """Returns the nearest ancestor (or ``start_dir``) that holds a ``.git`` entry.

    Only the git work-tree marker counts; a directory merely containing ``modules/``
    is not a boundary.
    """
    try:
        curr = Path(start_dir).resolve()
    except (OSError, ValueError):
        return None
    for parent in [curr] + list(curr.parents):
        try:
            if os.path.lexists(parent / ".git"):
                return parent
        except (OSError, ValueError):
            continue
    return None


def resolve_module_root(target_boundary: Path, module_root: Optional[Union[str, Path]] = None) -> Tuple[Path, str]:
    """Returns (read boundary for child modules, label describing where it came from).

    An explicit ``module_root`` must be an existing ancestor of the target; otherwise
    the enclosing git work tree is used, falling back to the target itself.

    Raises:
        ValueError: If ``module_root`` is not an existing directory containing the target.
    """
    target = Path(target_boundary).resolve()
    if module_root is not None:
        root = Path(module_root).resolve()
        if not root.is_dir():
            raise ValueError(f"--module-root '{module_root}' is not an existing directory")
        try:
            target.relative_to(root)
        except ValueError as err:
            raise ValueError(f"--module-root '{module_root}' does not contain the target '{target}'") from err
        return root, "operator --module-root"
    repo_root = find_enclosing_repo_root(target)
    if repo_root is not None:
        return repo_root, "git work tree"
    return target, "target"


def resolve_local_child_module_dir(
    current_file_dir: Union[str, Path],
    source: str,
    target_boundary: Path,
    module_root: Optional[Union[str, Path]] = None,
) -> Optional[Path]:
    """Resolves a relative child module source inside the module read boundary.

    The boundary comes from :func:`resolve_module_root`. The unresolved path is
    checked for symlinked components, so a link cannot redirect the read.
    Returns None for non-local sources, encoded traversal, missing directories,
    paths outside the boundary or paths through a symlink.
    """
    if not source or not (source.startswith("./") or source.startswith("../")):
        return None
    if "\0" in source or "%" in source:
        return None
    try:
        boundary, _ = resolve_module_root(Path(target_boundary), module_root)
    except ValueError:
        return None
    lexical = Path(os.path.normpath(Path(current_file_dir).absolute() / source))
    try:
        resolved_path = lexical.resolve()
        if not resolved_path.is_dir():
            return None
        resolved_path.relative_to(boundary)
        _reject_symlinked_components(lexical, boundary)
    except (OSError, ValueError, PermissionError):
        return None
    return resolved_path


def resolve_cli_target(target_dir: Union[str, Path]) -> Path:
    """Validates a CLI target directory and returns its resolved path.

    Raises:
        FileNotFoundError / NotADirectoryError: If the target is missing or not a directory.
        PermissionError: If the target is, or sits below, a symbolic link inside its
            repository (outputs would land in the link destination), or if it is a
            repository root (outputs would be written into the repository root).
    """
    raw = Path(target_dir)
    lexical = Path(os.path.normpath(raw.absolute()))
    if not os.path.lexists(lexical):
        raise FileNotFoundError(f"Target directory does not exist: {lexical}")
    if not lexical.is_dir():
        raise NotADirectoryError(f"Target path is not a directory: {lexical}")
    # Check the target and its ancestors up to (not including) the lexical repository
    # root; system-level links above a checkout (e.g. /bin -> /usr/bin) are irrelevant.
    for component in [lexical, *lexical.parents]:
        if component != lexical and os.path.lexists(component / ".git"):
            break
        if component.is_symlink():
            raise PermissionError(
                f"Target '{raw}' is or contains a symbolic link ('{component}' -> '{os.readlink(component)}'); "
                "copy the blueprint to a real directory or pass its real path"
            )
        if component == component.parent:
            break
    resolved = lexical.resolve()
    if os.path.lexists(resolved / ".git"):
        raise PermissionError(f"Target '{raw}' is a repository root; pass the blueprint directory instead")
    return resolved


def ensure_path_within_boundary(
    target_path: Union[str, Path],
    allowed_boundary: Union[str, Path],
    allow_symlinks: bool = False,
) -> Path:
    """Enforces strict path confinement preventing directory traversal attacks (CWE-22).

    Verifies that ``target_path`` resolves strictly within ``allowed_boundary``. Both
    paths are canonicalized via ``resolve()``, which collapses ``..`` segments and
    follows symlinks, so a symlink planted inside the boundary that points outside is
    caught by the containment check.

    Additionally, unless ``allow_symlinks`` is set, every component of the path as the
    caller supplied it, from just below the boundary down to the target, is checked
    with ``lstat`` and rejected if it is a symlink. Containment alone is not
    sufficient: a symlink that stays *inside* the boundary can still be repointed
    between validation and use, and rejecting links outright removes that TOCTOU
    window (CWE-367, CWE-59). Links at or above the boundary root (for example
    ``/var`` -> ``/private/var`` on macOS) are not rejected.

    Null bytes, URL percent-encoded traversal/separator sequences, and Windows
    reserved device names below the boundary are rejected without mutating literal
    ``%XX`` characters in the returned path.

    Args:
        target_path: Proposed destination file or directory path.
        allowed_boundary: Root directory that target_path must be confined inside.
        allow_symlinks: When True, symlinked components inside the boundary are
            tolerated. Only enable this for read paths that are known to be operator
            controlled.

    Returns:
        Resolved canonical Path object of target_path.

    Raises:
        PermissionError: If target_path escapes allowed_boundary, contains null bytes
            or percent-encoded traversal sequences, targets a reserved device name,
            or traverses a symlink when disallowed.
    """
    str_target = str(target_path)
    str_boundary = str(allowed_boundary)
    if "\0" in str_target:
        raise PermissionError(f"Null byte detected in target path: {target_path!r}")
    if "\0" in str_boundary:
        raise PermissionError(f"Null byte detected in boundary path: {allowed_boundary!r}")

    # Inspect percent-decoded representations for encoded null bytes, path separators,
    # or '..' traversal segments without rewriting literal '%XX' characters in the
    # filesystem path opened by the caller.
    probe_target = str_target
    probe_boundary = str_boundary
    for _ in range(3):
        if _ENCODED_TRAVERSAL_OR_SEP_RE.search(probe_target):
            raise PermissionError(
                f"Encoded path traversal or separator sequence rejected in target path: {target_path!r}"
            )
        if _ENCODED_TRAVERSAL_OR_SEP_RE.search(probe_boundary):
            raise PermissionError(
                f"Encoded path traversal or separator sequence rejected in boundary path: {allowed_boundary!r}"
            )
        next_target = urllib.parse.unquote(probe_target)
        next_boundary = urllib.parse.unquote(probe_boundary)
        if "\0" in next_target or "\0" in next_boundary:
            raise PermissionError(f"Encoded null byte detected in path: {target_path!r}")
        if next_target == probe_target and next_boundary == probe_boundary:
            break
        probe_target = next_target
        probe_boundary = next_boundary

    resolved_target = Path(str_target).resolve()
    resolved_boundary = Path(str_boundary).resolve()

    try:
        relative = resolved_target.relative_to(resolved_boundary)
    except ValueError as err:
        raise PermissionError(
            f"Path traversal detected: Target path '{resolved_target}' "
            f"resolves outside allowed boundary '{resolved_boundary}'"
        ) from err

    # Only names below the boundary are checked. The boundary is trusted, and on
    # POSIX a directory above it may legitimately be called "aux" or "con".
    for part in relative.parts:
        device_stem = part.split(".")[0].upper()
        if device_stem in WINDOWS_RESERVED_DEVICE_NAMES:
            raise PermissionError(
                f"Target path contains Windows reserved device name '{device_stem}': {resolved_target}"
            )

    if not allow_symlinks:
        _reject_symlinked_components(Path(str_target), resolved_boundary)

    return resolved_target


def _reject_symlinked_components(supplied: Path, boundary: Path) -> None:
    """Rejects a path that passes through a symbolic link below ``boundary``.

    The walk uses the path as the caller supplied it. ``resolve()`` replaces every
    link with its destination, so a walk over the resolved path never sees a link.

    Args:
        supplied: Target path as given by the caller. A relative path is taken
            against the current working directory. ``..`` segments are kept, so a
            link that a later ``..`` steps back out of is still inspected.
        boundary: Canonical (resolved) boundary root, assumed trusted.

    Raises:
        PermissionError: If a component below the boundary is a symbolic link, if the
            path reaches the boundary only through a link that points below the
            boundary root, or if a component cannot be inspected for a reason other
            than not existing yet.
    """
    lexical = supplied.absolute()
    chain = [*reversed(lexical.parents), lexical]
    # The first ancestor, from the root down, that resolves to the boundary is where
    # the supplied path enters it; every later component is inside the boundary.
    for index, ancestor in enumerate(chain):
        if ancestor.resolve() == boundary:
            inside = chain[index + 1:]
            break
    else:
        raise PermissionError(
            f"Path '{supplied}' enters boundary '{boundary}' through a symbolic link "
            "that points below the boundary root (CWE-59)"
        )

    for component in inside:
        try:
            mode = os.lstat(component).st_mode
        except OSError as err:
            if err.errno in (errno.ENOENT, errno.ENOTDIR):
                # The rest of the path does not exist yet, which is normal for a write
                # target, and nothing below a missing component can be a link.
                return
            raise PermissionError(f"Unable to verify path component '{component}': {err}") from err
        if stat.S_ISLNK(mode):
            raise PermissionError(
                f"Refusing to traverse symbolic link '{component}' inside boundary "
                f"'{boundary}'; symlinked components permit TOCTOU redirection (CWE-59)"
            )


def sanitize_filename(filename: str) -> str:
    r"""Sanitizes an untrusted filename to prevent path traversal and unsafe characters.

    Removes directory separators (/ and \), null bytes, parent traversal references (..),
    and leading/trailing whitespace or dots. Rejects Windows reserved device names.

    Percent-decoding is applied repeatedly so that multiply-encoded traversal payloads
    (``%252e%252e%252f``) are normalized before filtering, but the number of decoding
    rounds is bounded so a crafted name cannot drive an unbounded decode loop.

    Args:
        filename: Untrusted file name string.

    Returns:
        Sanitized base filename string.

    Raises:
        ValueError: If the resulting filename is empty, entirely dots, or a Windows
            reserved device name.
    """
    clean = str(filename)
    for _ in range(MAX_PERCENT_DECODE_ROUNDS):
        unquoted = urllib.parse.unquote(clean)
        if unquoted == clean:
            break
        clean = unquoted
    else:
        raise ValueError(
            f"Invalid filename: '{filename}' exceeds {MAX_PERCENT_DECODE_ROUNDS} "
            "percent-decoding rounds, indicating a deliberately obfuscated payload"
        )

    clean = clean.replace("\0", "").strip()
    clean = clean.replace("/", "_").replace("\\", "_")
    clean = re.sub(r"\.{2,}", ".", clean)
    clean = clean.strip(". ")
    if not clean:
        raise ValueError(f"Invalid filename: '{filename}' resolves to empty after sanitization")

    device_stem = clean.split(".")[0].upper()
    if device_stem in WINDOWS_RESERVED_DEVICE_NAMES:
        raise ValueError(f"Filename uses Windows reserved device name: '{clean}'")

    return clean


def read_text_file(
    filepath: Union[str, Path],
    encoding: str = "utf-8",
    errors: str = "ignore",
    allowed_boundary: Optional[Union[str, Path]] = None,
    max_bytes: int = MAX_TEXT_FILE_BYTES,
    allow_symlinks: bool = False,
) -> str:
    """Reads and returns the complete text contents of a file.

    The file is opened once and its size is measured from the open descriptor rather
    than from a separate ``stat`` call on the path, which removes the check-then-use
    window a concurrent rename or symlink swap could exploit (CWE-367).

    Args:
        filepath: Path to the text file to read.
        encoding: Character encoding to use (defaults to 'utf-8').
        errors: Error handling scheme for encoding errors.
        allowed_boundary: Optional root boundary to prevent path traversal.
        max_bytes: Maximum permitted file size; larger files are rejected rather than
            being partially read, so a truncated artifact is never mistaken for a
            complete one.
        allow_symlinks: Without ``allowed_boundary``, a symlinked final path component
            is refused unless this is True. With a boundary, links are followed but the
            destination must stay inside it.

    Returns:
        String containing file contents.

    Raises:
        FileNotFoundError: If the target file does not exist.
        PermissionError: If allowed_boundary is specified and filepath escapes it.
        ValueError: If the file exceeds ``max_bytes`` or is not a regular file.
    """
    if allowed_boundary is not None:
        target = ensure_path_within_boundary(filepath, allowed_boundary, allow_symlinks=True)
    else:
        if not allow_symlinks and os.path.islink(filepath):
            raise PermissionError(f"Refusing to follow symbolic link '{filepath}' without an allowed boundary")
        target = Path(filepath).resolve()

    try:
        pre_info = os.lstat(target)
        if stat.S_ISDIR(pre_info.st_mode):
            raise ValueError(f"Refusing to read directory as text: {target}")
        if not stat.S_ISREG(pre_info.st_mode):
            raise ValueError(f"Refusing to read non-regular file: {target}")

        open_flags = (
            os.O_RDONLY
            | getattr(os, "O_NONBLOCK", 0)
            | getattr(os, "O_NOFOLLOW", 0)
        )
        fd = os.open(target, open_flags)
        with os.fdopen(fd, "rb") as handle:
            info = os.fstat(handle.fileno())
            if stat.S_ISDIR(info.st_mode):
                raise ValueError(f"Refusing to read directory as text: {target}")
            if not stat.S_ISREG(info.st_mode):
                raise ValueError(f"Refusing to read non-regular file: {target}")
            if fcntl is not None and getattr(os, "O_NONBLOCK", None):
                fl = fcntl.fcntl(handle.fileno(), fcntl.F_GETFL)
                fcntl.fcntl(handle.fileno(), fcntl.F_SETFL, fl & ~os.O_NONBLOCK)
            if info.st_size > max_bytes:
                raise ValueError(
                    f"File '{target}' is {info.st_size} bytes, exceeding the "
                    f"{max_bytes} byte read budget"
                )
            raw = handle.read(max_bytes + 1)
    except FileNotFoundError as err:
        raise FileNotFoundError(f"File not found: {target}") from err
    except IsADirectoryError as err:
        raise ValueError(f"Refusing to read directory as text: {target}") from err

    if len(raw) > max_bytes:
        # The file grew between fstat and read; reject rather than silently truncate.
        raise ValueError(f"File '{target}' grew beyond the {max_bytes} byte read budget")

    return raw.decode(encoding, errors=errors)


def write_text_file(
    filepath: Union[str, Path],
    content: str,
    encoding: str = "utf-8",
    allowed_boundary: Optional[Union[str, Path]] = None,
) -> Path:
    """Atomically writes string content to a file, creating parent directories if needed.

    The content is written to a uniquely named temporary file in the destination
    directory (created with ``O_EXCL`` so an attacker cannot pre-create it) and then
    moved into place with ``os.replace``. This guarantees that a reader never observes
    a partially written compliance artifact, and that a symlink planted at the
    destination cannot redirect the write (CWE-59, CWE-367).

    Args:
        filepath: Target file path to write.
        content: String content to write into the file.
        encoding: Character encoding to use (defaults to 'utf-8').
        allowed_boundary: Optional root boundary to prevent path traversal.

    Returns:
        Resolved Path object of the written file.

    Raises:
        PermissionError: If allowed_boundary is specified and filepath escapes it,
            or if the destination path is a symbolic link.
        OSError: If the file cannot be written.
    """
    # The symlink checks must use the caller-supplied path. Path.resolve()
    # dereferences links, so checking the resolved path would inspect the link's
    # target and never observe the link itself.
    supplied = Path(filepath)
    if _safe_is_symlink(supplied):
        raise PermissionError(
            f"Refusing to write through symbolic link '{supplied}'; the link could "
            "redirect the artifact outside the authorization boundary (CWE-59)"
        )

    if allowed_boundary is not None:
        ensure_path_within_boundary(supplied, allowed_boundary)
    target = supplied.resolve()

    target.parent.mkdir(parents=True, exist_ok=True)

    fd, temp_name = tempfile.mkstemp(
        prefix=f".{target.name}.", suffix=".tmp", dir=str(target.parent)
    )
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding=encoding, newline="") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        # mkstemp creates 0600; compliance artifacts are read by the operator's
        # toolchain, so widen to the process umask default for regular files.
        os.chmod(temp_path, 0o644 & ~_current_umask())
        os.replace(temp_path, target)
    except BaseException:
        # Never leave a partial temporary artifact behind on any failure path.
        try:
            temp_path.unlink()
        except OSError as cleanup_err:
            logger.debug("Could not remove temporary file '%s': %s", temp_path, cleanup_err)
        raise
    return target


def _current_umask() -> int:
    """Reads the process umask without permanently changing it.

    Returns:
        The current umask value.
    """
    current = os.umask(0o022)
    os.umask(current)
    return current


def read_json_file(
    filepath: Union[str, Path],
    allowed_boundary: Optional[Union[str, Path]] = None,
) -> Dict[str, Any]:
    """Loads and parses a JSON file into a Python dictionary with explicit error handling.

    Args:
        filepath: Path to the JSON file to read.
        allowed_boundary: Optional root boundary to prevent path traversal.

    Returns:
        Parsed dictionary data.

    Raises:
        FileNotFoundError: If the target file does not exist.
        ValueError: If the file content is malformed or not valid JSON.
        PermissionError: If allowed_boundary is specified and filepath escapes it.
    """
    content = read_text_file(filepath, allowed_boundary=allowed_boundary)
    target = Path(filepath).resolve()
    try:
        parsed = json.loads(content)
    except RecursionError as err:
        raise YamlBudgetError(f"JSON document '{target}': nesting exceeds budget") from err
    except (json.JSONDecodeError, ValueError) as err:
        line_no = getattr(err, "lineno", "unknown")
        col_no = getattr(err, "colno", "unknown")
        msg = getattr(err, "msg", str(err))
        raise ValueError(
            f"Malformed JSON in '{target}' at line {line_no}, column {col_no}: {msg}"
        ) from err

    if isinstance(parsed, dict):
        return parsed
    return {"data": parsed}


def write_json_file(
    filepath: Union[str, Path],
    data: Any,
    indent: int = 2,
    allowed_boundary: Optional[Union[str, Path]] = None,
) -> Path:
    """Serializes data to a formatted JSON file, ensuring parent directories exist.

    Args:
        filepath: Target file path to write.
        data: Data structure to serialize into JSON.
        indent: Indentation level for pretty printing.
        allowed_boundary: Optional root boundary to prevent path traversal.

    Returns:
        Resolved Path object of the written JSON file.

    Raises:
        PermissionError: If allowed_boundary is specified and filepath escapes it.
    """
    content = json.dumps(data, indent=indent, default=str)
    return write_text_file(filepath, content, allowed_boundary=allowed_boundary)


def write_yaml_file(
    filepath: Union[str, Path],
    data: Any,
    allowed_boundary: Optional[Union[str, Path]] = None,
    sort_keys: bool = False,
) -> Path:
    """Serializes data to a formatted YAML file using PyYAML safe_dump.

    Args:
        filepath: Target file path to write.
        data: Data structure to serialize into YAML.
        allowed_boundary: Optional root boundary to prevent path traversal.
        sort_keys: Whether to sort dictionary keys alphabetically (default False).

    Returns:
        Resolved Path object of the written YAML file.

    Raises:
        PermissionError: If allowed_boundary is specified and filepath escapes it.
    """
    content = yaml.safe_dump(data, sort_keys=sort_keys, default_flow_style=False, allow_unicode=True)
    return write_text_file(filepath, content, allowed_boundary=allowed_boundary)


def safe_yaml_scalar(val: Any) -> str:
    """Encodes a scalar value into a valid, safe YAML 1.2 double-quoted scalar.

    Uses json.dumps to safely escape internal quotes, backslashes, tabs,
    and control characters, producing a double-quoted string valid in YAML.

    Args:
        val: Any Python primitive (str, int, float, bool, None, etc.).

    Returns:
        Safely formatted YAML scalar representation.
    """
    if val is None:
        return '""'
    if isinstance(val, bool):
        return "true" if val else "false"
    if isinstance(val, (int, float)):
        return str(val)
    return json.dumps(str(val), ensure_ascii=False)


def parse_yaml_safe(content: str, source_name: str = "YAML content") -> Dict[str, Any]:
    """Safely parses YAML content enforcing safe loading via PyYAML.

    Unsafe loaders (e.g. ``yaml.load`` with a non-safe Loader) are strictly prohibited.

    Two resource budgets are enforced before parsing, because ``yaml.safe_load`` alone
    does not bound work:

    * **Document size** - capped at :data:`MAX_YAML_BYTES`.
    * **Alias references** - capped at :data:`MAX_YAML_ALIASES`. PyYAML's SafeLoader
      expands anchors and aliases eagerly with no expansion budget, so a small document
      of nested aliases expands combinatorially and exhausts memory (the "YAML billion
      laughs" variant of CWE-776). Bounding the number of alias references bounds the
      achievable expansion factor.

    Args:
        content: Raw YAML text string.
        source_name: Optional name of the source for error context.

    Returns:
        Parsed dictionary data structure.

    Raises:
        ValueError: If the YAML content is malformed or exceeds a resource budget.
    """
    if not content or not content.strip():
        return {}

    encoded_length = len(content.encode("utf-8", errors="ignore"))
    if encoded_length > MAX_YAML_BYTES:
        raise YamlBudgetError(
            f"YAML document {source_name} is {encoded_length} bytes, exceeding the "
            f"{MAX_YAML_BYTES} byte parse budget"
        )

    alias_count = len(YAML_ALIAS_PATTERN.findall(content))
    if alias_count > MAX_YAML_ALIASES:
        raise YamlBudgetError(
            f"YAML document {source_name} contains {alias_count} alias references, "
            f"exceeding the {MAX_YAML_ALIASES} alias budget; this is characteristic of "
            "an entity-expansion (billion laughs) payload"
        )

    try:
        parsed = yaml.safe_load(content)
    except RecursionError as err:
        raise YamlBudgetError(f"YAML document {source_name}: nesting exceeds budget") from err
    except (yaml.YAMLError, ValueError, TypeError) as y_err:
        raise ValueError(f"Malformed YAML in {source_name}: {y_err}") from y_err
    if alias_count:
        expanded, distinct = _yaml_expansion(parsed)
        if expanded - distinct > MAX_YAML_EXPANDED_NODES:
            raise YamlBudgetError(
                f"YAML document {source_name} expands to {expanded} nodes through alias references, "
                f"exceeding the {MAX_YAML_EXPANDED_NODES} expanded-node budget (entity-expansion payload)"
            )
    if parsed is None:
        return {}
    if isinstance(parsed, dict):
        return parsed
    return {"data": parsed}


def read_yaml_file(
    filepath: Union[str, Path],
    allowed_boundary: Optional[Union[str, Path]] = None,
) -> Dict[str, Any]:
    """Safely reads and parses a YAML file from disk.

    Args:
        filepath: Filesystem path to the YAML file.
        allowed_boundary: Optional root boundary to prevent path traversal.

    Returns:
        Parsed dictionary configuration.

    Raises:
        FileNotFoundError: If the target file does not exist.
        ValueError: If the YAML content is malformed.
        PermissionError: If allowed_boundary is specified and filepath escapes it.
    """
    content = read_text_file(filepath, allowed_boundary=allowed_boundary)
    target = Path(filepath).resolve()
    return parse_yaml_safe(content, source_name=str(target))


def parse_yaml_robust_file(
    filepath: Union[str, Path],
    allowed_boundary: Optional[Union[str, Path]] = None,
) -> Dict[str, Any]:
    """Parses a YAML file from disk into a dictionary using PyYAML safe loading.

    Args:
        filepath: Filesystem path to the YAML file.
        allowed_boundary: Optional root boundary to prevent path traversal.

    Returns:
        Parsed configuration dictionary, or empty dict if reading fails.
    """
    try:
        content = read_text_file(filepath, allowed_boundary=allowed_boundary)
        resolved = Path(filepath).resolve()
        return parse_yaml_safe(content, source_name=str(resolved))
    except YamlBudgetError:
        raise
    except (OSError, UnicodeDecodeError, ValueError, PermissionError) as err:
        logger.warning("Failed to parse YAML file %s: %s", filepath, err)
        return {}


def validate_system_inventory_schema(
    inventory: Any,
    source_path: Optional[Union[str, Path]] = None,
) -> None:
    """Validates that system_inventory dictionary conforms to required schema.

    Rejects invalid data structures, missing required top-level sections,
    or missing required attributes immediately with actionable error messages.

    Args:
        inventory: Parsed dictionary to validate.
        source_path: Optional path for error context.

    Returns:
        None.

    Raises:
        ValueError: If schema validation fails.
    """
    ctx = f" in '{source_path}'" if source_path else ""
    if not isinstance(inventory, dict):
        raise ValueError(f"Invalid system_inventory schema{ctx}: Expected a dictionary, got {type(inventory).__name__}")

    required_top_sections = [
        "system_information",
        "personnel_roles",
        "infrastructure_components",
    ]
    for section in required_top_sections:
        if section not in inventory:
            raise ValueError(f"Invalid system_inventory schema{ctx}: Missing required top-level section '{section}'")
        if not isinstance(inventory[section], dict):
            raise ValueError(f"Invalid system_inventory schema{ctx}: Section '{section}' must be a dictionary, got {type(inventory[section]).__name__}")

    # Validate system_information
    sys_info = inventory["system_information"]
    required_sys_keys = ["system_name", "organization", "impact_level", "compliance_baseline"]
    for k in required_sys_keys:
        if k not in sys_info:
            raise ValueError(f"Invalid system_inventory schema{ctx}: Missing required attribute 'system_information.{k}'")
        if not isinstance(sys_info[k], str) or not sys_info[k].strip():
            raise ValueError(f"Invalid system_inventory schema{ctx}: 'system_information.{k}' must be a non-empty string")

    # Validate personnel_roles
    roles = inventory["personnel_roles"]
    required_roles = ["authorizing_official", "system_owner", "issm", "isso"]
    for r in required_roles:
        if r not in roles:
            raise ValueError(f"Invalid system_inventory schema{ctx}: Missing required role 'personnel_roles.{r}'")
        if not isinstance(roles[r], dict):
            raise ValueError(f"Invalid system_inventory schema{ctx}: Role 'personnel_roles.{r}' must be a dictionary")

    # Validate infrastructure_components
    infra = inventory["infrastructure_components"]
    if "services_enabled" in infra and not isinstance(infra["services_enabled"], list):
        raise ValueError(f"Invalid system_inventory schema{ctx}: 'infrastructure_components.services_enabled' must be a list")

    # If network_architecture is present, validate it
    if "network_architecture" in inventory:
        net = inventory["network_architecture"]
        if not isinstance(net, dict):
            raise ValueError(f"Invalid system_inventory schema{ctx}: 'network_architecture' must be a dictionary")

    # If application_components is present, validate it
    if "application_components" in inventory:
        app = inventory["application_components"]
        if not isinstance(app, dict):
            raise ValueError(f"Invalid system_inventory schema{ctx}: 'application_components' must be a dictionary")


def validate_compliance_config_schema(
    config: Any,
    source_path: Optional[Union[str, Path]] = None,
) -> None:
    """Validates compliance_config dictionary structure before processing.

    Args:
        config: Parsed configuration dictionary to validate.
        source_path: Optional path for error context.

    Returns:
        None.

    Raises:
        ValueError: If configuration fails schema validation.
    """
    ctx = f" in '{source_path}'" if source_path else ""
    if not isinstance(config, dict):
        raise ValueError(f"Invalid compliance_config schema{ctx}: Expected a dictionary, got {type(config).__name__}")

    # If system_information is present, validate it
    if "system_information" in config:
        sys_info = config["system_information"]
        if not isinstance(sys_info, dict):
            raise ValueError(f"Invalid compliance_config schema{ctx}: 'system_information' must be a dictionary")

    # If personnel_roles is present, validate roles
    if "personnel_roles" in config:
        roles = config["personnel_roles"]
        if not isinstance(roles, dict):
            raise ValueError(f"Invalid compliance_config schema{ctx}: 'personnel_roles' must be a dictionary")
        for role_key, role_val in roles.items():
            if not isinstance(role_val, dict):
                raise ValueError(f"Invalid compliance_config schema{ctx}: 'personnel_roles.{role_key}' must be a dictionary")

    # If export_preferences is present, validate preferences
    if "export_preferences" in config:
        prefs = config["export_preferences"]
        if not isinstance(prefs, dict):
            raise ValueError(f"Invalid compliance_config schema{ctx}: 'export_preferences' must be a dictionary")
        if "policy_formats" in prefs and not isinstance(prefs["policy_formats"], str):
            raise ValueError(f"Invalid compliance_config schema{ctx}: 'export_preferences.policy_formats' must be a string")
        if "structured_data_formats" in prefs and not isinstance(prefs["structured_data_formats"], str):
            raise ValueError(f"Invalid compliance_config schema{ctx}: 'export_preferences.structured_data_formats' must be a string")

    # If disa_stigs is present, validate structure
    if "disa_stigs" in config:
        stigs_cfg = config["disa_stigs"]
        if not isinstance(stigs_cfg, dict):
            raise ValueError(f"Invalid compliance_config schema{ctx}: 'disa_stigs' must be a dictionary")
        if "update_mode" in stigs_cfg and not isinstance(stigs_cfg["update_mode"], str):
            raise ValueError(f"Invalid compliance_config schema{ctx}: 'disa_stigs.update_mode' must be a string")
        if "catalog_source" in stigs_cfg and not isinstance(stigs_cfg["catalog_source"], str):
            raise ValueError(f"Invalid compliance_config schema{ctx}: 'disa_stigs.catalog_source' must be a string")
        if "version_overrides" in stigs_cfg and not isinstance(stigs_cfg["version_overrides"], dict):
            raise ValueError(f"Invalid compliance_config schema{ctx}: 'disa_stigs.version_overrides' must be a dictionary")
        if "custom_checklists" in stigs_cfg and not isinstance(stigs_cfg["custom_checklists"], list):
            raise ValueError(f"Invalid compliance_config schema{ctx}: 'disa_stigs.custom_checklists' must be a list")

    # If security_operations is present, validate structure
    if "security_operations" in config:
        secops_cfg = config["security_operations"]
        if not isinstance(secops_cfg, dict):
            raise ValueError(f"Invalid compliance_config schema{ctx}: 'security_operations' must be a dictionary")

    # If external_systems is present, validate structure
    if "external_systems" in config:
        ext_cfg = config["external_systems"]
        if not isinstance(ext_cfg, dict):
            raise ValueError(f"Invalid compliance_config schema{ctx}: 'external_systems' must be a dictionary")


def is_sensitive_key(key: str) -> bool:
    """Checks if a variable or attribute name suggests sensitive credentials.

    Args:
        key: Variable or attribute name string.

    Returns:
        True if the key matches sensitive credential patterns.
    """
    return bool(SENSITIVE_KEY_PATTERNS.search(str(key)))


_BASE64_RAW_KEY_VALUE_RE: Final[re.Pattern[str]] = re.compile(
    r"^[A-Za-z0-9+/]{24,}={1,2}$"
)

# Inventory containers whose key matches SENSITIVE_KEY_PATTERNS but whose value is a
# list of resource names (for example Secret Manager secret names), keyed by
# (parent key, key). Their string entries are still span-scrubbed.
_STRUCTURAL_NAME_LIST_KEYS: Final[frozenset] = frozenset({
    ("infrastructure_components", "secrets"),
})


def _is_structural_name_list(parent_key: Optional[str], key: str, value: Any) -> bool:
    """Returns True for an exempt inventory container holding only name strings."""
    return (
        (parent_key, key) in _STRUCTURAL_NAME_LIST_KEYS
        and isinstance(value, (list, tuple))
        and all(isinstance(item, str) for item in value)
    )


def scrub_sensitive_data(
    data: Any,
    _depth: int = 0,
    _seen: Optional[set] = None,
    _memo: Optional[Dict[Any, Any]] = None,
    _parent_key: Optional[str] = None,
) -> Any:
    """Recursively redacts sensitive credentials, secrets, and private keys.

    Inspects dictionary keys against sensitive naming patterns, and inspects string
    values for embedded PEM private keys or high-entropy credentials.

    The traversal is hardened for untrusted input:

    * **Cycle safety** - already-visited containers on the active call stack are
      tracked by identity, so a self-referential structure (which ``json.load``
      cannot produce but a programmatically assembled inventory can) terminates
      instead of recursing forever (CWE-674).
    * **DAG memoization** - completed container objects are memoized in ``_memo`` by
      ``id(data)`` across the full call so shared YAML anchor/alias references are
      scrubbed in linear $O(N)$ time rather than $O(2^d)$.
    * **Depth budget** - nesting deeper than :data:`MAX_STRUCTURE_DEPTH` is replaced
      with a truncation marker rather than raising ``RecursionError`` mid-redaction,
      which would otherwise abort the run *after* unredacted data had been assembled.
    * **Bounded scanning** - only the first :data:`MAX_SECRET_SCAN_CHARS` characters of
      a string are pattern-scanned; anything longer is redacted outright. Failing
      closed here is correct: an unscannable value must never be emitted verbatim.

    Args:
        data: Any nested dictionary, list, tuple, set, or scalar value.
        _depth: Internal recursion depth counter.
        _seen: Internal set of active ancestor container object identities.
        _memo: Internal memoization table mapping completed container ``id`` (dicts:
            ``(id, parent key)``) to its scrubbed result.
        _parent_key: Internal key under which ``data`` sits, used for the
            structural name-list exemptions in ``_STRUCTURAL_NAME_LIST_KEYS``.

    Returns:
        Scrubbed data structure with sensitive values replaced with
        ``[REDACTED_SENSITIVE]``.
    """
    if _depth > MAX_STRUCTURE_DEPTH:
        return "[REDACTED_DEPTH_LIMIT]"

    if _seen is None:
        _seen = set()
    if _memo is None:
        _memo = {}

    if isinstance(data, (dict, list, tuple, set)):
        identity = id(data)
        if identity in _seen:
            return "[REDACTED_CYCLE]"
        # A dict's result depends on the key it sits under (structural exemptions),
        # so dicts are memoized per (identity, parent key).
        memo_key: Any = (identity, _parent_key) if isinstance(data, dict) else identity
        if memo_key in _memo:
            return _memo[memo_key]
        active_seen = _seen | {identity}

        if isinstance(data, dict):
            scrubbed: Dict[Any, Any] = {}
            for key, value in data.items():
                key_str = str(key)
                if _is_structural_name_list(_parent_key, key_str, value):
                    scrubbed[key] = [_scrub_string(item) for item in value]
                elif is_sensitive_key(key_str):
                    scrubbed[key] = "[REDACTED_SENSITIVE]"
                elif (
                    key_str.lower() in ("kms_key", "kms_key_name")
                    and isinstance(value, str)
                    and _BASE64_RAW_KEY_VALUE_RE.match(value.strip())
                ):
                    scrubbed[key] = "[REDACTED_SENSITIVE]"
                else:
                    scrubbed[key] = scrub_sensitive_data(
                        value, _depth + 1, active_seen, _memo, key_str
                    )
            _memo[memo_key] = scrubbed
            return scrubbed

        if isinstance(data, list):
            res_list = [
                scrub_sensitive_data(item, _depth + 1, active_seen, _memo)
                for item in data
            ]
            _memo[identity] = res_list
            return res_list

        if isinstance(data, tuple):
            res_tuple = tuple(
                scrub_sensitive_data(item, _depth + 1, active_seen, _memo)
                for item in data
            )
            _memo[identity] = res_tuple
            return res_tuple

        res_set = {
            scrub_sensitive_data(item, _depth + 1, active_seen, _memo)
            for item in data
        }
        _memo[identity] = res_set
        return res_set

    if isinstance(data, str):
        return _scrub_string(data)

    return data


def _scrub_string(text: str) -> str:
    """Span-redacts credentials in ``text``; unscannably long values are redacted whole."""
    if len(text) > MAX_SECRET_SCAN_CHARS:
        # Fail closed: a value too large to inspect is treated as sensitive.
        return "[REDACTED_UNSCANNABLE]"
    return _redact_secret_spans(text)


def _redact_secret_spans(text: str) -> str:
    """Replaces credential substrings in ``text`` with a redaction marker.

    Redaction is span-targeted rather than whole-value. Compliance deliverables
    carry narrative prose (POA&M weakness titles, SSP control narratives, scanner
    messages) in the same fields that may carry raw credentials, and discarding an
    entire narrative because it embedded one token loses real content without
    improving confidentiality. Only the credential itself is removed.

    When the redacted spans account for essentially the whole value, the value was
    a bare secret rather than prose, and it collapses to a single marker so that
    no residual framing characters remain.

    Args:
        text: A string already known to be within the scannable size budget.

    Returns:
        The input with any private key blocks and high-entropy credentials
        replaced by ``[REDACTED_SENSITIVE]``.
    """
    redacted = PRIVATE_KEY_PATTERN.sub(REDACTION_MARKER, text)
    redacted = HIGH_ENTROPY_SECRET_PATTERN.sub(REDACTION_MARKER, redacted)

    if redacted == text:
        return text

    # Collapse runs of adjacent markers produced by back-to-back credentials.
    redacted = ADJACENT_REDACTION_PATTERN.sub(REDACTION_MARKER, redacted)

    # If nothing of substance survived, emit the bare marker rather than the
    # marker wrapped in leftover punctuation or whitespace.
    residue = redacted.replace(REDACTION_MARKER, "").strip()
    if not residue or not any(char.isalnum() for char in residue):
        return REDACTION_MARKER
    return redacted


def escape_xml_text(val: Optional[Any]) -> str:
    """Escapes XML special characters for safe insertion into OpenXML elements.

    Normalizes Unicode to NFC form, strips illegal XML 1.0 control characters,
    and escapes XML special characters (&, <, >, ", ').

    Args:
        val: Input string or object to convert and escape.

    Returns:
        Escaped string safe for OpenXML/Word text nodes.
    """
    if val is None:
        return ""
    text = str(val)
    text = unicodedata.normalize("NFC", text)
    text = XML_ILLEGAL_CHARS_PATTERN.sub("", text)
    return html.escape(text)


def clean_cell_value(val: Any) -> Union[str, int, float, bool, date, datetime]:
    """Sanitizes spreadsheet values and defends against formula injection (CWE-1236).

    Normalizes text to NFC form, strips non-printable control characters,
    truncates text exceeding Excel's cell limit (MAX_EXCEL_CELL_LENGTH) while preserving
    multi-byte/combining character boundaries, and prepends a single quote to
    strings starting with formula execution triggers (=, +, -, @, |, %, etc.) unless
    representing a valid numeric literal.

    Args:
        val: The raw value to be inserted into a spreadsheet cell.

    Returns:
        The sanitized cell value safe for spreadsheet insertion.
    """
    if val is None:
        return ""
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)):
        return val
    if isinstance(val, (date, datetime)):
        return val
    s = str(val)
    s = unicodedata.normalize("NFC", s)
    s = XML_ILLEGAL_CHARS_PATTERN.sub("", s)
    s = s.strip()

    # Excel cell text length limit is 32,767 characters. Leave headroom for formula injection quote.
    if len(s) > MAX_EXCEL_CELL_LENGTH:
        cutoff = MAX_EXCEL_CELL_LENGTH - 3
        while cutoff > 0 and (unicodedata.combining(s[cutoff]) != 0 or s[cutoff - 1] == "\u200D"):
            cutoff -= 1
        while cutoff > 0 and (unicodedata.combining(s[cutoff - 1]) != 0 or s[cutoff - 1] == "\u200D"):
            cutoff -= 1
        s = s[:cutoff] + "..."

    # Check for formula injection prepending idempotency (prevent ''=cmd accumulation)
    if s.startswith("'"):
        inner = s[1:]
        inner_stripped = LEADING_DANGEROUS_CHARS_PATTERN.sub("", inner)
        if inner_stripped and (
            inner_stripped[0] in FORMULA_TRIGGER_CHARS
            or inner_stripped[0] in ("+", "-", "\uff0b", "\uff0d")
        ):
            return s  # Already safely quote-prefixed

    # Detect formula injection even if masked by leading whitespace, zero-width chars, or control chars
    stripped = LEADING_DANGEROUS_CHARS_PATTERN.sub("", s)
    if stripped:
        first_char = stripped[0]
        if first_char in FORMULA_TRIGGER_CHARS:
            s = "'" + stripped
        elif first_char in ("+", "-", "\uff0b", "\uff0d"):
            # Check for valid integer, decimal, or scientific notation numbers
            if not re.match(r"^[+-]?\d+(\.\d+)?([eE][+-]?\d+)?$", stripped.strip()):
                s = "'" + stripped
            else:
                s = stripped
    return s


def sanitize_container_image_tag(
    raw_img: Any, default_img: str = "container-image"
) -> Tuple[str, str]:
    """Sanitizes a container image string and extracts clean image name and version tag.

    Eliminates unresolved variable interpolation patterns (${...}, $var) and ensures
    deterministic fallback to valid OCI tags (e.g. 'latest').

    Args:
        raw_img: Raw image name or URI (e.g. 'nginx:1.25' or '${var.repo}/app:${var.tag}').
        default_img: Default fallback image name if raw input is empty.

    Returns:
        A tuple of (sanitized_image_name, sanitized_version_tag).
    """
    s = str(raw_img or default_img).strip()
    if not s or s == "None":
        s = default_img
    if "${" in s or "$" in s:
        s = re.sub(r"\$\{[^}]+\}", "latest", s)
        s = re.sub(r"\$[a-zA-Z0-9_]+", "latest", s)
    s = s.strip()
    if not s:
        s = default_img
    ver = s.split(":")[-1] if ":" in s else "latest"
    if "${" in ver or "$" in ver or not ver:
        ver = "latest"
    return s, ver


def sanitize_software_package_identity(
    raw_name: Any, raw_ver: Any = "Latest", default_name: str = "unknown-package"
) -> Tuple[str, str]:
    """Sanitizes software package name and version identifiers.

    Strips unresolved template syntax and variable interpolations to produce clean
    package coordinates safe for compliance matrices.

    Args:
        raw_name: Raw package name or identifier.
        raw_ver: Raw version string.
        default_name: Default package name fallback.

    Returns:
        A tuple of (sanitized_package_name, sanitized_version).
    """
    p_name = str(raw_name or default_name).strip()
    if not p_name or p_name == "None":
        p_name = default_name
    if "${" in p_name or "$" in p_name:
        p_name = re.sub(r"\$\{[^}]+\}", "", p_name).strip()
        p_name = re.sub(r"\$[a-zA-Z0-9_]+", "", p_name).strip()
        if not p_name:
            p_name = default_name

    p_ver = str(raw_ver or "Latest").strip()
    if not p_ver or p_ver == "None":
        p_ver = "Latest"
    if "${" in p_ver or "$" in p_ver or not p_ver:
        p_ver = p_name.split(":")[-1] if ":" in p_name else "Latest"
        if "${" in p_ver or "$" in p_ver:
            p_ver = "Latest"
    return p_name, p_ver


_CIDR_PATTERN = re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}/\d{1,2}\b")


def extract_clean_subnets(raw_cidrs: Any) -> List[str]:
    """Extracts IPv4 CIDR strings from lists, sets, or string representations.

    Accepts input serialized as a stringified Python container or a comma-separated
    string. Only dotted-quad IPv4 CIDRs are matched, and octet values are not
    range-checked. When no IPv4 CIDR is found and the input is a container, items
    that contain '/' and do not start with '$' are returned unchanged, so an IPv6
    range is kept only when the input holds no IPv4 range.

    Args:
        raw_cidrs: Raw subnets data (list, set, tuple, or string).

    Returns:
        A sorted list of unique CIDR strings.
    """
    if isinstance(raw_cidrs, (list, tuple, set)):
        text = " ".join(str(c) for c in raw_cidrs)
    else:
        text = str(raw_cidrs or "")
    found = _CIDR_PATTERN.findall(text)
    if found:
        return sorted(set(found))
    if isinstance(raw_cidrs, (list, tuple, set)):
        clean: List[str] = []
        for item in raw_cidrs:
            s = str(item).strip()
            if "/" in s and not s.startswith("$"):
                clean.append(s)
        return sorted(set(clean))
    return []


def split_markdown_table_row(row_str: str) -> List[str]:
    r"""Splits a Markdown table row into trimmed cell contents, respecting escaped pipes.

    Preserves escaped pipe characters (\|) within cell values without splitting on them.

    Args:
        row_str: A single line string representing a Markdown table row.

    Returns:
        List of cell string values with escaped pipes unescaped.
    """
    stripped = row_str.strip()
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|"):
        stripped = stripped[:-1]

    raw_cells = re.split(r"(?<!\\)\|", stripped)
    cleaned_cells: List[str] = []
    for cell in raw_cells:
        cleaned = cell.replace(r"\|", "|").strip()
        cleaned_cells.append(cleaned)

    return cleaned_cells


def has_terraform_infrastructure(inventory: Dict[str, Any]) -> bool:
    """Returns True if the inventory contains evidence of Terraform Infrastructure as Code.

    Evaluates whether the system boundary includes Terraform configuration files,
    resource definitions, provider version blocks, or unparsed IaC assets.

    Args:
        inventory: System inventory dictionary.

    Returns:
        True if Terraform resources, engine version, or .tf files exist in the boundary.
    """
    if not inventory:
        return False
    infra_info = inventory.get("infrastructure_components", {})
    if (
        inventory.get("terraform_engine_version")
        or infra_info.get("terraform_engine_version")
        or inventory.get("provider_versions")
        or infra_info.get("provider_versions")
        or inventory.get("unparsed_terraform_files")
        or infra_info.get("terraform_resources")
    ):
        return True
    for cat in (
        "compute_instances",
        "storage_buckets",
        "databases",
        "kms_keys",
        "service_accounts",
        "gke_clusters",
        "networks",
        "firewall_rules",
    ):
        for item in infra_info.get(cat, []):
            if isinstance(item, dict) and str(item.get("file", "")).endswith((".tf", ".tf.json")):
                return True
    return False


# ---------------------------------------------------------------------------
# Regime classification (single source of truth)
# ---------------------------------------------------------------------------


class Regime(str, enum.Enum):
    """Authorization regimes the engine can recognize from system_information."""

    FEDRAMP_HIGH = "FedRAMP High"
    FEDRAMP_MODERATE = "FedRAMP Moderate"
    FEDRAMP_LOW = "FedRAMP Low"
    FISMA_HIGH = "FISMA High"
    FISMA_MODERATE = "FISMA Moderate"
    FISMA_LOW = "FISMA Low"
    GOVRAMP = "GovRAMP / StateRAMP"
    DOD_IL2 = "DoD IL2"
    DOD_IL4 = "DoD IL4"
    DOD_IL5 = "DoD IL5"
    DOD_IL6 = "DoD IL6"
    CJIS = "CJIS"
    UNKNOWN = "unknown"


#: Single support table: whether templates, parameter values and an OSCAL profile
#: exist for a regime. Enabling a regime is a data change here (plus its template,
#: profile and parameter set); no call site tests regimes individually.
REGIME_SUPPORT: Final[Dict[Regime, bool]] = {
    Regime.FEDRAMP_HIGH: True,
    Regime.FEDRAMP_MODERATE: True,
    Regime.FEDRAMP_LOW: True,
    Regime.FISMA_HIGH: True,
    Regime.FISMA_MODERATE: True,
    Regime.FISMA_LOW: True,
    Regime.GOVRAMP: False,
    Regime.DOD_IL2: True,
    Regime.DOD_IL4: True,
    Regime.DOD_IL5: True,
    Regime.DOD_IL6: True,
    Regime.CJIS: True,
    Regime.UNKNOWN: False,
}

SUPPORTED_REGIMES: Final[frozenset] = frozenset(r for r, on in REGIME_SUPPORT.items() if on)

DOD_REGIMES: Final[frozenset] = frozenset({Regime.DOD_IL2, Regime.DOD_IL4, Regime.DOD_IL5, Regime.DOD_IL6})

#: Regimes whose control baseline is High (IL5 and IL6 overlay High; IL2, IL4, and CJIS overlay Moderate).
HIGH_BASELINE_REGIMES: Final[frozenset] = frozenset({
    Regime.FEDRAMP_HIGH,
    Regime.FISMA_HIGH,
    Regime.DOD_IL5,
    Regime.DOD_IL6,
})
MODERATE_BASELINE_REGIMES: Final[frozenset] = frozenset({
    Regime.FEDRAMP_MODERATE,
    Regime.FISMA_MODERATE,
    Regime.DOD_IL2,
    Regime.DOD_IL4,
    Regime.CJIS,
})
LOW_BASELINE_REGIMES: Final[frozenset] = frozenset({Regime.FEDRAMP_LOW, Regime.FISMA_LOW})

DOD_IL6_CSP_PATO_PLACEHOLDER: Final[str] = "[CONFIG_REQUIRED: DoD IL6 Secret Enclave PA Package ID]"
CJIS_CSP_PATO_PLACEHOLDER: Final[str] = (
    "[CONFIG_REQUIRED: State CJIS Systems Agency (CSA) Information Exchange Agreement / Package ID]"
)

_REGIME_FIELDS: Final[Tuple[str, ...]] = ("impact_level", "compliance_baseline", "governance_regime")

_NB = r"(?<![A-Z0-9])"
_NA = r"(?![A-Z0-9])"
_HIGH_RE = re.compile(_NB + r"HIGH" + _NA)
_MODERATE_RE = re.compile(_NB + r"MODERATE" + _NA)
_LOW_RE = re.compile(_NB + r"LOW" + _NA)
_IL2_RE = re.compile(_NB + r"(?:IL|IMPACT LEVEL)[ _-]?2" + _NA)
_TAILORED_RE = re.compile(_NB + r"(?:LI[ _-]?SAAS|TAILORED)" + _NA)
_THIRD_PARTY_FRAMEWORK_RE = re.compile(
    _NB + r"(?:SOC[ _-]?2|ISO[ _/-]?27001|HIPAA|PCI[ _-]?DSS|PCIDSS|GDPR)" + _NA
)
_FEDRAMP_RE = re.compile(_NB + r"FEDRAMP" + _NA)
# Ordered: specific programs first, then DoD levels (highest first, so "IL6" is never
# read as a weaker level), then Tailored/LI-SaaS guard, then FIPS 199 high-water mark.
_REGIME_RULES: Final[Tuple[Tuple[re.Pattern, Regime], ...]] = (
    (re.compile(_NB + r"CJIS" + _NA), Regime.CJIS),
    (re.compile(_NB + r"(?:GOVRAMP|STATERAMP)" + _NA), Regime.GOVRAMP),
    (re.compile(_NB + r"(?:IL|IMPACT LEVEL)[ _-]?6" + _NA), Regime.DOD_IL6),
    (re.compile(_NB + r"(?:IL|IMPACT LEVEL)[ _-]?5" + _NA), Regime.DOD_IL5),
    (re.compile(_NB + r"(?:IL|IMPACT LEVEL)[ _-]?4" + _NA), Regime.DOD_IL4),
    (_IL2_RE, Regime.DOD_IL2),
    (_TAILORED_RE, Regime.UNKNOWN),
    (_HIGH_RE, Regime.FEDRAMP_HIGH),
    (_MODERATE_RE, Regime.FEDRAMP_MODERATE),
    (_LOW_RE, Regime.FEDRAMP_LOW),
)
_FISMA_RE = re.compile(_NB + r"FISMA" + _NA)


class UnsupportedRegimeError(ValueError):
    """Raised when a package is requested for a regime the engine does not support."""


def _regime_text(source: Union[Mapping[str, Any], str, None]) -> str:
    if source is None:
        return ""
    if isinstance(source, Mapping):
        raw = " ".join(str(source.get(k) or "") for k in _REGIME_FIELDS)
    else:
        raw = str(source)
    # Underscores are kept (DOD_IL5); whitespace runs collapse to one space.
    return re.sub(r"\s+", " ", raw.upper()).strip()


def classify_regime(source: Union[Mapping[str, Any], str, None]) -> Regime:
    """Classifies system_information (or a bare regime string) into a :class:`Regime`.

    A bare "DoD" or "FISMA" without a level is UNKNOWN: the level decides the baseline.
    Unrecognized third-party frameworks (SOC 2, ISO 27001, HIPAA, PCI-DSS, GDPR) in
    compliance_baseline or governance_regime are rejected as UNKNOWN before matching
    bare High/Moderate/Low impact words.
    """
    text = _regime_text(source)
    if not text:
        return Regime.UNKNOWN
    if isinstance(source, Mapping):
        baseline_text = re.sub(
            r"\s+",
            " ",
            f"{source.get('compliance_baseline') or ''} {source.get('governance_regime') or ''}".upper(),
        ).strip()
    else:
        baseline_text = text
    for pattern, regime in _REGIME_RULES[:7]:
        if pattern.search(text):
            return regime
    if _FISMA_RE.search(text):
        if _THIRD_PARTY_FRAMEWORK_RE.search(baseline_text) and not _FISMA_RE.search(baseline_text):
            return Regime.UNKNOWN
        for pattern, regime in ((_HIGH_RE, Regime.FISMA_HIGH), (_MODERATE_RE, Regime.FISMA_MODERATE), (_LOW_RE, Regime.FISMA_LOW)):
            if pattern.search(text):
                return regime
        return Regime.UNKNOWN
    if _THIRD_PARTY_FRAMEWORK_RE.search(baseline_text) and not _FEDRAMP_RE.search(baseline_text):
        return Regime.UNKNOWN
    for pattern, regime in _REGIME_RULES[7:]:
        if pattern.search(text):
            return regime
    return Regime.UNKNOWN


def is_supported_regime(regime: Regime) -> bool:
    """True when the engine has templates, parameters and a profile for ``regime``."""
    return REGIME_SUPPORT.get(regime, False)


def _check_fips_199_ceiling(regime: Regime, source: Union[Mapping[str, Any], str, None]) -> None:
    """Raise :class:`UnsupportedRegimeError` if explicit C/I/A overrides exceed the baseline ceiling."""
    if not isinstance(source, Mapping):
        return
    rank = {"LOW": 1, "MODERATE": 2, "HIGH": 3}
    if regime in LOW_BASELINE_REGIMES:
        ceiling = 1
    elif regime in MODERATE_BASELINE_REGIMES:
        ceiling = 2
    else:
        return
    for key in ("confidentiality_impact", "integrity_impact", "availability_impact"):
        val = str(source.get(key) or "").strip().upper()
        if rank.get(val, 0) > ceiling:
            raise UnsupportedRegimeError(
                f"Unsupported regime configuration: {key}='{source.get(key)}' exceeds the {regime.value} "
                "baseline impact ceiling. Select the corresponding High/Moderate baseline (e.g. DoD IL5, "
                "FedRAMP High, or FISMA High)."
            )


def require_supported_regime(source: Union[Mapping[str, Any], str, None]) -> Regime:
    """Returns the supported regime or raises :class:`UnsupportedRegimeError` (fail closed)."""
    regime = classify_regime(source)
    supported_set = frozenset(r for r, on in REGIME_SUPPORT.items() if on)
    if is_supported_regime(regime):
        _check_fips_199_ceiling(regime, source)
        return regime
    supported = ", ".join(r.value for r in sorted(supported_set, key=lambda r: r.value))
    if isinstance(source, Mapping):
        raw = " / ".join(str(source[k]) for k in _REGIME_FIELDS if source.get(k))
    else:
        raw = str(source or "")
    raw_label = raw or "not configured"
    if regime == Regime.GOVRAMP:
        detail = ": GovRAMP proprietary baselines have no official OSCAL profile and are not supported"
    else:
        detail = ""
    raise UnsupportedRegimeError(
        f"Unsupported regime '{raw_label}' (classified as {regime.value}){detail}; "
        f"supported regimes are: {supported}. Set system_information.impact_level / compliance_baseline accordingly."
    )


def is_dod_regime(source: Union[Mapping[str, Any], str, None]) -> bool:
    """True for a DoD Cloud Computing SRG impact level (IL2, IL4, IL5, IL6)."""
    return classify_regime(source) in DOD_REGIMES


def is_high_baseline_regime(source: Union[Mapping[str, Any], str, None]) -> bool:
    """True when the control baseline is High (FedRAMP High, FISMA High, IL5, IL6)."""
    return classify_regime(source) in HIGH_BASELINE_REGIMES


def resolve_default_csp_pato_package_id(sys_info: Mapping[str, Any]) -> str:
    """Return configured ``csp_pato_package_id`` or regime-accurate default."""
    explicit = sys_info.get("csp_pato_package_id")
    if explicit and str(explicit).strip():
        return str(explicit).strip()
    regime = classify_regime(sys_info)
    if regime == Regime.DOD_IL6:
        return DOD_IL6_CSP_PATO_PLACEHOLDER
    if regime == Regime.CJIS:
        return CJIS_CSP_PATO_PLACEHOLDER
    return DEFAULT_CSP_PATO_PACKAGE_ID


def derive_fips_199_impacts(sys_info: Mapping[str, Any]) -> Tuple[str, str, str]:
    """Returns (confidentiality, integrity, availability) impacts.

    Explicit configuration wins per objective; otherwise the value follows the regime
    baseline (High for High-baseline regimes, Moderate for Moderate-baseline regimes except
    DoD IL2 which defaults to Low/Low/Low with a Moderate ceiling, and Low for Low-baseline
    regimes) and is left as a configuration token when the regime does not determine it.
    """
    regime = classify_regime(sys_info)
    if regime in HIGH_BASELINE_REGIMES:
        default = "High"
    elif regime == Regime.DOD_IL2 or regime in LOW_BASELINE_REGIMES:
        default = "Low"
    elif regime in MODERATE_BASELINE_REGIMES:
        default = "Moderate"
    else:
        default = ""
    impacts = []
    for key, label in (
        ("confidentiality_impact", "Confidentiality Impact"),
        ("integrity_impact", "Integrity Impact"),
        ("availability_impact", "Availability Impact"),
    ):
        impacts.append(str(sys_info.get(key) or default or f"[CONFIG_REQUIRED: {label}]"))
    return impacts[0], impacts[1], impacts[2]


# ---------------------------------------------------------------------------
# Bounded subprocess execution (single runner for every external command)
# ---------------------------------------------------------------------------

#: Default cap on captured child output; larger stdout is rejected, not truncated.
MAX_SUBPROCESS_OUTPUT_BYTES: Final[int] = 5 * 1024 * 1024


def run_bounded_command(
    argv: Sequence[str],
    *,
    timeout: float,
    env: Optional[Mapping[str, str]] = None,
    cwd: Optional[Union[str, Path]] = None,
    max_output_bytes: int = MAX_SUBPROCESS_OUTPUT_BYTES,
    attempts: int = 1,
    retry_on_nonzero: bool = False,
    retry_base_seconds: float = 1.0,
    popen: Callable[..., Any] = subprocess.Popen,
) -> "subprocess.CompletedProcess[str]":
    """Runs ``argv`` without a shell, spooling output to temporary files.

    Output never accumulates in memory beyond ``max_output_bytes + 1`` characters:
    stdout larger than the cap raises MemoryError (a clipped report must not be
    parsed as a smaller one); stderr is truncated. Timeouts and OSErrors are retried
    up to ``attempts`` times; a non-zero exit is returned as-is unless
    ``retry_on_nonzero`` is set. Missing or non-executable binaries fail at once.

    Raises:
        ValueError: If ``argv`` is empty or ``attempts`` is below 1.
        FileNotFoundError / PermissionError / NotADirectoryError: Non-transient launch failures.
        MemoryError: If stdout exceeds ``max_output_bytes``.
        subprocess.TimeoutExpired / OSError: If the final attempt fails.
    """
    if not argv or not argv[0]:
        raise ValueError("Empty command")
    if attempts < 1:
        raise ValueError(f"attempts must be at least 1, got {attempts}")
    command = [str(arg) for arg in argv]
    for attempt in range(1, attempts + 1):
        final = attempt == attempts
        try:
            with (
                tempfile.TemporaryFile(mode="w+", encoding="utf-8", errors="replace") as out_f,
                tempfile.TemporaryFile(mode="w+", encoding="utf-8", errors="replace") as err_f,
            ):
                with popen(
                    command,
                    stdout=out_f,
                    stderr=err_f,
                    text=True,
                    env=None if env is None else dict(env),
                    cwd=None if cwd is None else str(cwd),
                    shell=False,
                ) as proc:
                    try:
                        proc.wait(timeout=timeout)
                    except subprocess.TimeoutExpired:
                        proc.kill()
                        proc.wait()
                        raise
                out_f.seek(0)
                stdout_data = out_f.read(max_output_bytes + 1)
                err_f.seek(0)
                stderr_data = err_f.read(max_output_bytes + 1)
            if len(stdout_data) > max_output_bytes:
                raise MemoryError(
                    f"{command[0]} emitted more than {max_output_bytes} bytes on stdout; "
                    "refusing to parse a truncated result."
                )
            result = subprocess.CompletedProcess(command, proc.returncode, stdout_data, stderr_data[:max_output_bytes])
            if result.returncode == 0 or not retry_on_nonzero or final:
                return result
        except (FileNotFoundError, PermissionError, NotADirectoryError, MemoryError):
            raise
        except (subprocess.TimeoutExpired, OSError):
            if final:
                raise
        delay = retry_base_seconds * (2 ** (attempt - 1))
        delay += random.uniform(0, delay / 2)
        logger.warning("Command '%s' attempt %d/%d unsuccessful; retrying in %.2fs", command[0], attempt, attempts, delay)
        time.sleep(delay)
    raise RuntimeError(f"{command[0]} exhausted {attempts} attempts")  # pragma: no cover - loop returns or raises


def compute_poam_target_date(days: int, base: Optional[Union[str, datetime]] = None) -> str:
    """Returns an ISO date ``days`` after max(today, base); a past base never yields a past target."""
    today = current_utc_datetime().replace(tzinfo=None)
    base_dt = today
    if isinstance(base, datetime):
        base_dt = base
    elif base:
        try:
            base_dt = datetime.strptime(str(base)[:10], "%Y-%m-%d")
        except ValueError:
            logger.warning("Ignoring unparseable POA&M base date %r", base)
    return (max(today, base_dt) + timedelta(days=days)).strftime("%Y-%m-%d")


# ---------------------------------------------------------------------------
# Cryptographic module attribution for Cloud KMS keys
# ---------------------------------------------------------------------------

#: Validation level per protection level. Cloud HSM modules hold FIPS 140-2 Level 3 certificates;
#: software keys run in BoringCrypto.
CLOUD_HSM_FIPS: Final[str] = "FIPS 140-2 Level 3 (Cloud HSM)"
KMS_SOFTWARE_FIPS: Final[str] = "FIPS 140-3 Level 1 (BoringCrypto)"
KMS_EXTERNAL_FIPS: Final[str] = "[CONFIG_REQUIRED: EKM module certificate]"
NOT_DETERMINED: Final[str] = "[NOT DETERMINED FROM SOURCE]"


def kms_protection_level(key: Mapping[str, Any]) -> str:
    """Normalized protection level of a KMS key record ('' when unknown)."""
    return str(key.get("protection_level") or "").strip().upper()


def kms_key_fips_attribute(key: Mapping[str, Any]) -> str:
    """FIPS validation statement for one KMS key, from its protection level only."""
    level = kms_protection_level(key)
    if level == "HSM":
        return CLOUD_HSM_FIPS
    if level == "SOFTWARE":
        return KMS_SOFTWARE_FIPS
    if level.startswith("EXTERNAL"):
        return KMS_EXTERNAL_FIPS
    return NOT_DETERMINED


def kms_key_algorithm(key: Mapping[str, Any]) -> str:
    """Key algorithm from the Terraform version_template, or the not-determined token."""
    return str(key.get("algorithm") or "").strip() or NOT_DETERMINED


def summarize_kms_protection(kms_keys: Sequence[Mapping[str, Any]]) -> str:
    """One-line description of the protection levels actually present in ``kms_keys``."""
    parts = []
    levels = {kms_protection_level(k) for k in kms_keys if isinstance(k, Mapping)}
    if "HSM" in levels:
        parts.append(f"Cloud HSM keys, {CLOUD_HSM_FIPS.split(' (')[0]}")
    if "SOFTWARE" in levels:
        parts.append(f"Cloud KMS software keys, {KMS_SOFTWARE_FIPS.split(' (')[0]} (BoringCrypto)")
    if any(level.startswith("EXTERNAL") for level in levels):
        parts.append("Cloud EKM external keys (module certificate configuration required)")
    if not parts:
        return f"Customer-managed encryption keys (protection level {NOT_DETERMINED})"
    return "CMEK: " + "; ".join(parts)
