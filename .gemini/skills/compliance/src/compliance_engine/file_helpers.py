#!/usr/bin/env python3
"""Shared File I/O and String Manipulation Utilities for Compliance Engine.

This module provides common, OS-agnostic filesystem operations, path resolution
using pathlib, schema validation, path traversal defense, and sanitized
string/XML manipulation utilities used across the compliance generation,
hydration, extraction, and validation pipeline.
"""

import glob
import html
import json
import logging
import os
from datetime import date, datetime
from pathlib import Path
import re
import stat
import sys
import tempfile
from typing import Any, Dict, Final, List, Optional, Sequence, Tuple, Union
import unicodedata
import urllib.parse

logger = logging.getLogger(__name__)

# Environment variable holding an explicit, operator-curated list of additional
# site-packages directories (os.pathsep separated).
_SITE_PACKAGES_ENV: Final[str] = "COMPLIANCE_SITE_PACKAGES"

# When set to a truthy value, dependency resolution is restricted to the active
# interpreter environment. Accredited deployments should enable this so that the
# provenance of every dependency is the pinned, attested environment and nothing else.
_STRICT_DEPS_ENV: Final[str] = "COMPLIANCE_STRICT_DEPS"

# Last-resort discovery patterns for environments where the operator installed the
# supporting toolchain via pipx/Homebrew rather than into the active interpreter.
_FOREIGN_TOOLCHAIN_PATTERNS: Final[Tuple[str, ...]] = (
    "~/.local/share/pipx/venvs/checkov/lib/python*/site-packages",
    "/opt/homebrew/Cellar/checkov/*/libexec/lib/python*/site-packages",
    "/usr/local/Cellar/checkov/*/libexec/lib/python*/site-packages",
)


def _is_truthy_env(env_var: str) -> bool:
    """Returns True when an environment variable holds an affirmative value.

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

    Resolution order:

    1. Directories explicitly listed in ``COMPLIANCE_SITE_PACKAGES``.
    2. If, and only if, PyYAML still cannot be imported, a last-resort scan of
       known pipx/Homebrew toolchain virtualenvs.

    Every accepted directory is validated (absolute, real directory, not a symlink,
    not group/world-writable) and logged at WARNING level, because borrowing a
    dependency from a foreign virtualenv means the engine's dependency versions are
    controlled by an unrelated tool's release cadence rather than by this project's
    pinned manifest. Setting ``COMPLIANCE_STRICT_DEPS=1`` disables both mechanisms so
    that an accredited deployment fails closed instead of silently importing from an
    unattested location.
    """
    if _is_truthy_env(_STRICT_DEPS_ENV):
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
        import yaml as _probe  # noqa: F401
    except ImportError:
        pass
    else:
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

# Comprehensive formula execution triggers (CWE-1236)
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

# Matches a YAML alias reference (``*anchor``). Deliberately linear with no nested
# quantifiers so scanning an untrusted document cannot itself become a ReDoS vector.
YAML_ALIAS_PATTERN = re.compile(r"(?<![\w*])\*[A-Za-z_][\w.-]*")

# Regular expression matching credential and secret variable names
SENSITIVE_KEY_PATTERNS = re.compile(
    r"(password|passwd|pwd|passphrase|secret|private[_-]?key|privkey|token|credential|"
    r"api[_-]?key|auth[_-]?token|access[_-]?token|client[_-]?secret|master[_-]?key|cert[_-]?key|"
    r"ssh[_-]?key|signing[_-]?key|encryption[_-]?key|session[_-]?key|"
    r"auth[_-]?string|auth[_-]?key|bearer|passcode|\.pfx|\.pem|\.key|\.pkcs12)",
    re.IGNORECASE,
)

# Regular expression matching PEM formatted private keys (PKCS#1, PKCS#8, EC, OpenSSH, PGP, etc.)
# Bounded to 8192 characters between delimiters to eliminate catastrophic backtracking (ReDoS) on large files
PRIVATE_KEY_PATTERN = re.compile(
    r"-----BEGIN\s+[A-Z0-9\s_-]*(?:PRIVATE KEY|PRIVATE KEY BLOCK|SECRET KEY|RSA PRIVATE KEY|EC PRIVATE KEY|DSA PRIVATE KEY|OPENSSH PRIVATE KEY)-----[\s\S]{0,8192}?-----END\s+[A-Z0-9\s_-]*(?:PRIVATE KEY|PRIVATE KEY BLOCK|SECRET KEY|RSA PRIVATE KEY|EC PRIVATE KEY|DSA PRIVATE KEY|OPENSSH PRIVATE KEY)-----|"
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
    r"AKIA[0-9A-Z]{16}|"  # AWS Access Key ID
    r"gh[pousr]_[A-Za-z0-9_]{36,}|"  # GitHub Personal Access Token
    r"xox[baprs]-[0-9a-zA-Z-]{20,}|"  # Slack Token
    r"(?<![0-9A-Za-z_-])eyJ[0-9A-Za-z_-]{15,}\.[0-9A-Za-z_-]{15,}\.[0-9A-Za-z_-]{15,}(?![0-9A-Za-z_-])|"  # JWT (OIDC, OAuth, Service Account identity tokens)
    # Vault batch/recovery/service tokens: 'hvs.', 'hvb.', 'hvr.' prefixes.
    r"(?<![0-9A-Za-z_-])hv[sbr]\.[0-9A-Za-z_-]{20,}|"
    # Legacy Vault service token: literal 's.' followed by 24+ alphanumerics.
    # Alphanumeric-only (no '_' or '-') is what Vault actually emits, and it is
    # what separates a token from a snake_case identifier.
    r"(?<![0-9A-Za-z_-])s\.[0-9A-Za-z]{24,}(?![0-9A-Za-z])|"
    r"(?<![0-9a-fA-F-])[0-9a-fA-F]{32}(?![0-9a-fA-F-])|"  # Continuous 32-char Hex Secret
    r"(?<![0-9a-fA-F-])[0-9a-fA-F]{64}(?![0-9a-fA-F-])|"  # Continuous 64-char Hex Secret
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


def get_skill_root() -> Path:
    """Returns the absolute Path to the compliance skill root directory.

    Returns:
        Path object pointing to .gemini/skills/compliance.
    """
    cur = Path(__file__).resolve().parent
    for p in (cur, cur.parent, cur.parent.parent, cur.parent.parent.parent):
        if (p / "SKILL.md").exists() or (p / "pyproject.toml").exists() or ((p / "templates").is_dir() and (p / "config").is_dir()):
            return p
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


def get_src_dir() -> Path:
    """Returns the absolute Path to the compliance src directory.

    Returns:
        Path object pointing to .gemini/skills/compliance/src.
    """
    return get_skill_root() / "src"


def resolve_path(target_path: Union[str, Path]) -> Path:
    """Resolves an absolute or relative path into a normalized Path object.

    Args:
        target_path: String or Path representing a filesystem path.

    Returns:
        Fully resolved absolute Path object.
    """
    return Path(target_path).resolve()


def ensure_directory(dir_path: Union[str, Path]) -> Path:
    """Ensures a directory and any intermediate parent directories exist.

    Args:
        dir_path: String or Path representing the directory to create.

    Returns:
        Resolved Path object of the created or existing directory.
    """
    resolved = Path(dir_path).resolve()
    resolved.mkdir(parents=True, exist_ok=True)
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

    Additionally, unless ``allow_symlinks`` is set, every path component from the
    boundary down to the target is checked with ``lstat`` and rejected if it is a
    symlink. Containment alone is not sufficient: a symlink that stays *inside* the
    boundary can still be repointed between validation and use, and rejecting links
    outright removes that TOCTOU window (CWE-367, CWE-59).

    Null bytes, URL percent-encoding, and Windows reserved device names are rejected.

    Args:
        target_path: Proposed destination file or directory path.
        allowed_boundary: Root directory that target_path must be confined inside.
        allow_symlinks: When True, symlinked components inside the boundary are
            tolerated. Only enable this for read paths that are known to be operator
            controlled.

    Returns:
        Resolved canonical Path object of target_path.

    Raises:
        PermissionError: If target_path escapes allowed_boundary, contains null bytes,
            targets a reserved device name, or traverses a symlink when disallowed.
    """
    str_target = urllib.parse.unquote(str(target_path))
    if "\0" in str_target:
        raise PermissionError(f"Null byte detected in target path: {target_path!r}")

    str_boundary = urllib.parse.unquote(str(allowed_boundary))
    if "\0" in str_boundary:
        raise PermissionError(f"Null byte detected in boundary path: {allowed_boundary!r}")

    resolved_target = Path(str_target).resolve()
    resolved_boundary = Path(str_boundary).resolve()

    # Check for Windows reserved device names across all path components
    for part in resolved_target.parts:
        device_stem = part.split(".")[0].upper()
        if device_stem in WINDOWS_RESERVED_DEVICE_NAMES:
            raise PermissionError(
                f"Target path contains Windows reserved device name '{device_stem}': {resolved_target}"
            )

    try:
        relative = resolved_target.relative_to(resolved_boundary)
    except ValueError as err:
        raise PermissionError(
            f"Path traversal detected: Target path '{resolved_target}' "
            f"resolves outside allowed boundary '{resolved_boundary}'"
        ) from err

    if not allow_symlinks:
        _reject_symlinked_components(resolved_boundary, relative)

    return resolved_target


def _reject_symlinked_components(boundary: Path, relative: Path) -> None:
    """Rejects a path whose components between boundary and leaf include a symlink.

    Args:
        boundary: Canonical boundary root, assumed trusted.
        relative: Path of the target relative to ``boundary``.

    Raises:
        PermissionError: If any intermediate or leaf component is a symbolic link.
    """
    current = boundary
    for part in relative.parts:
        current = current / part
        try:
            if current.is_symlink():
                raise PermissionError(
                    f"Refusing to traverse symbolic link '{current}' inside boundary "
                    f"'{boundary}'; symlinked components permit TOCTOU redirection (CWE-59)"
                )
        except OSError as err:
            # A component that cannot be stat'ed simply does not exist yet, which is
            # legitimate for write targets. Any other OS error is reported.
            if err.errno not in (2, 20):  # ENOENT, ENOTDIR
                raise PermissionError(
                    f"Unable to verify path component '{current}': {err}"
                ) from err
            return


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

    Returns:
        String containing file contents.

    Raises:
        FileNotFoundError: If the target file does not exist.
        PermissionError: If allowed_boundary is specified and filepath escapes it.
        ValueError: If the file exceeds ``max_bytes`` or is not a regular file.
    """
    target = Path(filepath).resolve()
    if allowed_boundary is not None:
        ensure_path_within_boundary(target, allowed_boundary, allow_symlinks=True)

    try:
        with open(target, "rb") as handle:
            info = os.fstat(handle.fileno())
            if not stat.S_ISREG(info.st_mode):
                raise ValueError(f"Refusing to read non-regular file: {target}")
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
    # The symlink check must happen on the caller-supplied path. Path.resolve()
    # dereferences links, so checking the resolved path would inspect the link's
    # target and never observe the link itself.
    supplied = Path(filepath)
    if supplied.is_symlink():
        raise PermissionError(
            f"Refusing to write through symbolic link '{supplied}'; the link could "
            "redirect the artifact outside the authorization boundary (CWE-59)"
        )

    target = supplied.resolve()
    if allowed_boundary is not None:
        ensure_path_within_boundary(target, allowed_boundary)

    if target.is_symlink():
        raise PermissionError(
            f"Refusing to write through symbolic link '{target}'; the link could "
            "redirect the artifact outside the authorization boundary (CWE-59)"
        )

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
    target = Path(filepath).resolve()
    content = read_text_file(target, allowed_boundary=allowed_boundary)
    try:
        parsed = json.loads(content)
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


def strip_yaml_comment(line_str: str) -> str:
    """Strips comments from a YAML line while preserving # inside quotes.

    Args:
        line_str: A single raw line string from a YAML file.

    Returns:
        The line string stripped of any unquoted trailing comment.
    """
    in_single = False
    in_double = False
    for idx, ch in enumerate(line_str):
        if ch == "'" and not in_double:
            in_single = not in_single
        elif ch == '"' and not in_single:
            in_double = not in_double
        elif ch == "#" and not in_single and not in_double:
            return line_str[:idx].rstrip()
    return line_str.rstrip()


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


def parse_yaml_scalar(v_str: str) -> Any:
    """Parses a YAML scalar value using PyYAML safe loading.

    Args:
        v_str: Raw scalar string value from a YAML key-value pair.

    Returns:
        Converted Python primitive (None, bool, int, float, list, or str).
    """
    v = v_str.strip()
    if not v:
        return ""
    if v in ("null", "Null", "NULL", "~", "none", "None", "NONE"):
        return None
    try:
        return yaml.safe_load(v)
    except (yaml.YAMLError, ValueError):
        return v


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
        raise ValueError(
            f"YAML document {source_name} is {encoded_length} bytes, exceeding the "
            f"{MAX_YAML_BYTES} byte parse budget"
        )

    alias_count = len(YAML_ALIAS_PATTERN.findall(content))
    if alias_count > MAX_YAML_ALIASES:
        raise ValueError(
            f"YAML document {source_name} contains {alias_count} alias references, "
            f"exceeding the {MAX_YAML_ALIASES} alias budget; this is characteristic of "
            "an entity-expansion (billion laughs) payload"
        )

    try:
        parsed = yaml.safe_load(content)
        if parsed is None:
            return {}
        if isinstance(parsed, dict):
            return parsed
        return {"data": parsed}
    except (yaml.YAMLError, ValueError, TypeError) as y_err:
        raise ValueError(f"Malformed YAML in {source_name}: {y_err}") from y_err


def parse_yaml_robust_text(text: str) -> Dict[str, Any]:
    """Parses YAML text safely via PyYAML.

    Backward compatibility alias for parse_yaml_safe.

    Args:
        text: Raw YAML content string.

    Returns:
        Dictionary representation of the parsed YAML hierarchy.
    """
    return parse_yaml_safe(text)


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
    target = Path(filepath).resolve()
    content = read_text_file(target, allowed_boundary=allowed_boundary)
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
        resolved = Path(filepath).resolve()
        content = read_text_file(resolved, allowed_boundary=allowed_boundary)
        return parse_yaml_safe(content, source_name=str(resolved))
    except (OSError, UnicodeDecodeError, ValueError, PermissionError) as err:
        logger.warning("Failed to parse YAML file %s: %s", filepath, err)
        return {}


def parse_yaml_simple(filepath: Union[str, Path]) -> Dict[str, Any]:
    """Backward compatibility wrapper for parse_yaml_robust_file.

    Args:
        filepath: Filesystem path to the YAML file.

    Returns:
        Parsed configuration dictionary.
    """
    return parse_yaml_robust_file(filepath)


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


def scrub_sensitive_data(data: Any, _depth: int = 0, _seen: Optional[set] = None) -> Any:
    """Recursively redacts sensitive credentials, secrets, and private keys.

    Inspects dictionary keys against sensitive naming patterns, and inspects string
    values for embedded PEM private keys or high-entropy credentials.

    The traversal is hardened for untrusted input:

    * **Cycle safety** - already-visited containers are tracked by identity, so a
      self-referential structure (which ``json.load`` cannot produce but a
      programmatically assembled inventory can) terminates instead of recursing
      forever (CWE-674).
    * **Depth budget** - nesting deeper than :data:`MAX_STRUCTURE_DEPTH` is replaced
      with a truncation marker rather than raising ``RecursionError`` mid-redaction,
      which would otherwise abort the run *after* unredacted data had been assembled.
    * **Bounded scanning** - only the first :data:`MAX_SECRET_SCAN_CHARS` characters of
      a string are pattern-scanned; anything longer is redacted outright. Failing
      closed here is correct: an unscannable value must never be emitted verbatim.

    Args:
        data: Any nested dictionary, list, tuple, set, or scalar value.
        _depth: Internal recursion depth counter.
        _seen: Internal set of visited container object identities.

    Returns:
        Scrubbed data structure with sensitive values replaced with
        ``[REDACTED_SENSITIVE]``.
    """
    if _depth > MAX_STRUCTURE_DEPTH:
        return "[REDACTED_DEPTH_LIMIT]"

    if _seen is None:
        _seen = set()

    if isinstance(data, (dict, list, tuple, set)):
        identity = id(data)
        if identity in _seen:
            return "[REDACTED_CYCLE]"
        _seen = _seen | {identity}

    if isinstance(data, dict):
        scrubbed: Dict[Any, Any] = {}
        for key, value in data.items():
            if is_sensitive_key(str(key)):
                scrubbed[key] = "[REDACTED_SENSITIVE]"
            else:
                scrubbed[key] = scrub_sensitive_data(value, _depth + 1, _seen)
        return scrubbed

    if isinstance(data, list):
        return [scrub_sensitive_data(item, _depth + 1, _seen) for item in data]

    if isinstance(data, tuple):
        return tuple(scrub_sensitive_data(item, _depth + 1, _seen) for item in data)

    if isinstance(data, set):
        return {scrub_sensitive_data(item, _depth + 1, _seen) for item in data}

    if isinstance(data, str):
        if len(data) > MAX_SECRET_SCAN_CHARS:
            # Fail closed: a value too large to inspect is treated as sensitive.
            return "[REDACTED_UNSCANNABLE]"
        return _redact_secret_spans(data)

    return data


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
    """Extracts valid IPv4/IPv6 CIDR strings from lists, sets, or string representations.

    Guarantees resilient parsing even if the input was serialized as a stringified
    Python container or comma-separated string.

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


def format_markdown_table(headers: Sequence[str], rows: Sequence[Sequence[Any]]) -> str:
    """Formats headers and data rows into a standard GFM Markdown table.

    Args:
        headers: Sequence of column header names.
        rows: Sequence of rows, each containing cell values corresponding to headers.

    Returns:
        Multi-line string representing the formatted Markdown table.
    """
    if not headers:
        return ""
    header_line = "| " + " | ".join(str(h) for h in headers) + " |"
    separator_line = "| " + " | ".join("---" for _ in headers) + " |"
    data_lines: List[str] = []
    for row in rows:
        row_line = "| " + " | ".join(str(cell).replace("|", r"\|") for cell in row) + " |"
        data_lines.append(row_line)

    return "\n".join([header_line, separator_line] + data_lines)


def format_bullet_list(items: Sequence[str], indent_spaces: int = 2) -> str:
    """Formats a sequence of items into an indented Markdown bulleted list.

    Args:
        items: Sequence of string items.
        indent_spaces: Number of spaces for indentation.

    Returns:
        Formatted multi-line Markdown bullet list string.
    """
    if not items:
        return " " * indent_spaces + "- None defined"
    prefix = " " * indent_spaces + "- "
    return "\n".join(f"{prefix}{item}" for item in items)


def sanitize_identifier(name: str) -> str:
    """Normalizes an arbitrary string into a safe identifier (lowercase, underscored).

    Args:
        name: Raw name or title.

    Returns:
        Normalized identifier string containing only lowercase alphanumeric chars and underscores.
    """
    cleaned = re.sub(r"[^a-zA-Z0-9_-]", "_", name.strip().lower())
    cleaned = re.sub(r"_+", "_", cleaned)
    return cleaned.strip("_")


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

