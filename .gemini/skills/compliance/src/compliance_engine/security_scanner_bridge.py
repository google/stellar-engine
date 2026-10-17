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

"""
Security Scanner Bridge for Automated POA&M Generation
======================================================
Integrates automated vulnerability & static analysis tools:
1. Checkov: Infrastructure-as-Code (Terraform, Kubernetes, Dockerfile, CloudFormation)
2. Semgrep: Application Static Application Security Testing (SAST / OWASP / CWE)
3. Trivy: Software Dependencies, Container Images, and CVEs
4. SARIF Ingestion: Universal ingestion of standard *.sarif report files

Maps scanner findings directly to NIST SP 800-53 Rev. 5 controls and emits
canonical POA&M items with exact file paths, line numbers, and remediation guidance.
"""

import collections
import contextlib
import contextvars
import copy
import dataclasses
import functools
import hashlib
import json
import logging
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from datetime import datetime
from typing import Any, Callable, Dict, Final, FrozenSet, Iterable, Iterator, List, Optional, Sequence, Tuple, Union

from .audit_log import get_audit_logger, AuditOutcome, AuditEvent

from .file_helpers import (
    current_utc_datetime,
    ensure_path_within_boundary,
    is_dod_regime,
    scrub_sensitive_data,
    read_json_file,
    get_skill_root,
    compute_poam_target_date,
    env_flag_enabled,
    run_bounded_command,
)

logger = logging.getLogger(__name__)

#: Operator kill switch; when set, no live scanner runs regardless of flags or config.
DISABLE_LIVE_SCANNERS_ENV: Final[str] = "COMPLIANCE_DISABLE_LIVE_SCANNERS"

#: Operator-only environment variable selecting a custom Semgrep ruleset.
SEMGREP_CONFIG_ENV: Final[str] = "COMPLIANCE_SEMGREP_CONFIG"

LIVE_SCANNERS: Final[FrozenSet[str]] = frozenset({"checkov", "semgrep", "trivy"})
DEFAULT_LIVE_SCANNERS: Final[FrozenSet[str]] = frozenset({"checkov", "semgrep"})


@dataclasses.dataclass(frozen=True)
class ScannerPolicy:
    """Which live scanners may run. Built only from operator CLI flags and environment."""

    run_live: bool = False
    scanners: FrozenSet[str] = frozenset()
    semgrep_config: Optional[str] = None

    def enabled(self, name: str) -> bool:
        return self.run_live and name in self.scanners


SCANNERS_OFF: Final[ScannerPolicy] = ScannerPolicy()


def resolve_scanner_policy(
    run_scanners: bool,
    scanners: Optional[Iterable[str]] = None,
    semgrep_config: Optional[str] = None,
) -> ScannerPolicy:
    """Returns the live-scanner policy for this run.

    Live scanners are an explicit operator opt-in (``--run-scanners``); the
    COMPLIANCE_DISABLE_LIVE_SCANNERS environment switch always wins. Target
    configuration and system_inventory.json are deliberately not inputs.
    """
    resolved_semgrep = (semgrep_config or os.environ.get(SEMGREP_CONFIG_ENV, "")).strip() or None
    if not run_scanners or env_flag_enabled(DISABLE_LIVE_SCANNERS_ENV):
        return ScannerPolicy(semgrep_config=resolved_semgrep) if resolved_semgrep else SCANNERS_OFF
    chosen = frozenset(s.strip().lower() for s in (scanners or DEFAULT_LIVE_SCANNERS) if s and s.strip())
    unknown = chosen - LIVE_SCANNERS
    if unknown:
        raise ValueError(f"Unknown scanner(s) {sorted(unknown)}; choose from {sorted(LIVE_SCANNERS)}")
    return ScannerPolicy(run_live=bool(chosen), scanners=chosen, semgrep_config=resolved_semgrep)


# Files a scanner may see in the private copy. Everything else (dotfiles and
# dot-directories such as .checkov.yaml, .semgrepignore, .git; scanner config files
# that are auto-discovered; symlinks) is left behind so target content cannot
# configure, extend or suppress a scanner.
_SCAN_COPY_SUFFIXES: Final[Tuple[str, ...]] = (
    ".tf", ".tfvars", ".tf.json", ".hcl", ".yaml", ".yml", ".json",
    ".py", ".js", ".jsx", ".ts", ".tsx", ".go", ".java", ".kt", ".rb", ".php", ".cs", ".sh",
    ".txt", ".toml", ".lock", ".mod", ".sum", ".xml", ".gradle",
)
_SCAN_COPY_NAMES: Final[FrozenSet[str]] = frozenset({"Dockerfile", "Containerfile", "go.mod", "go.sum", "Gemfile", "Pipfile"})
_SCAN_COPY_EXCLUDED_NAMES: Final[FrozenSet[str]] = frozenset({
    "checkov.yaml", "checkov.yml", "trivy.yaml", "trivy.yml", "semgrep.yaml", "semgrep.yml",
    "system_inventory.json",
})
_SCAN_COPY_EXCLUDED_DIRS: Final[FrozenSet[str]] = frozenset({"ato_artifacts", "node_modules", "__pycache__"})
_SCAN_COPY_MAX_FILES: Final[int] = 20_000
_SCAN_COPY_MAX_BYTES: Final[int] = 512 * 1024 * 1024


def _scan_copy_wanted(name: str) -> bool:
    if name.startswith(".") or name in _SCAN_COPY_EXCLUDED_NAMES:
        return False
    return name in _SCAN_COPY_NAMES or name.startswith("Dockerfile") or name.endswith(_SCAN_COPY_SUFFIXES)


def build_scan_copy(target_dir: Union[str, Path], dest: Union[str, Path]) -> Path:
    """Copies scanner inputs from ``target_dir`` into ``dest`` (which must not exist).

    Symlinks are never followed or copied, dot-entries and scanner configuration
    files are skipped, and the copy is bounded in file count and bytes.

    Returns:
        The copy root.
    """
    src_root = Path(target_dir).resolve()
    dest_root = Path(dest)
    dest_root.mkdir(parents=True)
    files = 0
    total = 0
    for dirpath, dirnames, filenames in os.walk(src_root, followlinks=False):
        dirnames[:] = sorted(
            d for d in dirnames
            if not d.startswith(".") and d not in _SCAN_COPY_EXCLUDED_DIRS and not os.path.islink(os.path.join(dirpath, d))
        )
        rel_dir = Path(dirpath).relative_to(src_root)
        for name in sorted(filenames):
            src = Path(dirpath) / name
            if not _scan_copy_wanted(name) or src.is_symlink() or not src.is_file():
                continue
            size = src.stat().st_size
            files += 1
            total += size
            if files > _SCAN_COPY_MAX_FILES or total > _SCAN_COPY_MAX_BYTES:
                raise MemoryError(
                    f"Scanner input under {src_root} exceeds {_SCAN_COPY_MAX_FILES} files or {_SCAN_COPY_MAX_BYTES} bytes"
                )
            out = dest_root / rel_dir / name
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, out, follow_symlinks=False)
    return dest_root


@dataclasses.dataclass(frozen=True)
class _ScanIsolation:
    home: str
    cwd: str
    checkov_config: str


_SCAN_ISOLATION: contextvars.ContextVar[Optional[_ScanIsolation]] = contextvars.ContextVar("scan_isolation", default=None)


@contextlib.contextmanager
def isolated_scan_workspace(target_dir: Union[str, Path], live: bool) -> Iterator[Optional[Path]]:
    """Yields a private sanitized copy of ``target_dir`` (or None when ``live`` is False).

    While active, scanner subprocesses run with an empty HOME / XDG config and an
    empty working directory, and Checkov receives an explicit operator config file,
    so no configuration is discovered from the target, the operator's home or CWD.
    """
    if not live:
        yield None
        return
    with tempfile.TemporaryDirectory(prefix="compliance-scan-") as private:
        root = Path(private)
        for sub in ("home", "cwd", "etc"):
            (root / sub).mkdir()
        checkov_cfg = root / "etc" / "checkov.yaml"
        checkov_cfg.write_text("compact: true\n", encoding="utf-8")
        copy_root = build_scan_copy(target_dir, root / "scan")
        token = _SCAN_ISOLATION.set(_ScanIsolation(home=str(root / "home"), cwd=str(root / "cwd"), checkov_config=str(checkov_cfg)))
        try:
            yield copy_root
        finally:
            _SCAN_ISOLATION.reset(token)


SEVERITY_ORDER: Dict[str, int] = {
    "CRITICAL": 5,
    "VERY HIGH": 5,
    "VERY_HIGH": 5,
    "HIGH": 4,
    "MODERATE": 3,
    "MEDIUM": 3,
    "MOD": 3,
    "LOW": 2,
    "VERY LOW": 1,
    "VERY_LOW": 1,
    "INFORMATIONAL": 0,
    "INFO": 0,
    "NONE": 0,
}

# ==============================================================================
# Pre-Installed Scanner Tooling (Deterministic Local Execution)
# ==============================================================================
# To ensure reliable, deterministic execution, the compliance engine relies
# on pre-installed, locally verified binaries resolved from system PATH,
# standard security directories, or environment variables.

# NIST SP 800-53 Rev. 5 Control Mapping for Common CWEs
CWE_NIST_MAP: Dict[str, Tuple[str, str]] = {
    "89": ("SI-10", "SI-10 Information Input Validation (SQL Injection)"),
    "79": ("SI-10", "SI-10 Information Input Validation (Cross-Site Scripting)"),
    "78": ("SI-10", "SI-10 Information Input Validation (OS Command Injection)"),
    "94": ("SI-10", "SI-10 Information Input Validation (Code Injection)"),
    "95": ("SI-10", "SI-10 Information Input Validation (Dynamic Code Evaluation)"),
    "22": ("AC-03", "AC-03 Access Enforcement (Path Traversal)"),
    "798": ("IA-05", "IA-05 Authenticator Management (Hardcoded Credentials)"),
    "259": ("IA-05", "IA-05 Authenticator Management (Hardcoded Password)"),
    "321": ("IA-05", "IA-05 Authenticator Management (Hardcoded Cryptographic Key)"),
    "295": ("SC-8", "SC-8 Transmission Confidentiality and Integrity (Improper Certificate Validation)"),
    "327": ("SC-13", "SC-13 Cryptographic Protection (Broken/Risky Algorithm)"),
    "328": ("SC-13", "SC-13 Cryptographic Protection (Reversible One-Way Hash)"),
    "330": ("SC-13", "SC-13 Cryptographic Protection (Insufficiently Random Values)"),
    "338": ("SC-13", "SC-13 Cryptographic Protection (Cryptographically Weak PRNG)"),
    "489": ("CM-7", "CM-7 Least Functionality (Active Debug Code)"),
    "287": ("IA-02", "IA-02 Identification and Authentication (Improper Authentication)"),
    "306": ("IA-02", "IA-02 Identification and Authentication (Missing Authentication)"),
    "502": ("SI-10", "SI-10 Information Input Validation (Insecure Deserialization)"),
    "611": ("SI-10", "SI-10 Information Input Validation (XML External Entity - XXE)"),
    "776": ("SI-10", "SI-10 Information Input Validation (XML Entity Expansion)"),
    "918": ("SC-07", "SC-07 Boundary Protection (Server-Side Request Forgery - SSRF)"),
}

CHECKOV_NIST_MAP: Dict[str, Tuple[str, str]] = {
    "CKV_GCP_34": ("IA-02 / AC-02", "IA-02 / AC-02 Identification, Authentication, and Account Management (OS Login)"),
    "CKV_GCP_32": ("IA-02 / AC-17", "IA-02 / AC-17 Remote Access and SSH Key Management"),
}

_CHECKOV_AUDIT_WORD_RE: Final[re.Pattern[str]] = re.compile(
    r"\b(logs?|logging|audit|auditing|sinks?|monitoring)\b"
)
_CHECKOV_AUTH_WORD_RE: Final[re.Pattern[str]] = re.compile(
    r"\b(oslogin|login|ssh|mfa|2fa|password\s+policy)\b"
)


def _clean_cwe_token(raw: Union[str, int]) -> str:
    clean_id = str(raw).upper().replace("CWE-", "").strip()
    if ":" in clean_id:
        clean_id = clean_id.split(":", 1)[0].strip()
    return clean_id


def map_cwe_to_nist(cwe_id: Union[str, int, Sequence[Union[str, int]]]) -> Tuple[str, str]:
    """Maps a CWE identifier (or sequence of CWEs) to its NIST SP 800-53 Rev. 5 control."""
    candidates: Sequence[Union[str, int]] = (
        [cwe_id] if isinstance(cwe_id, (str, int)) else list(cwe_id)
    )
    cleaned = [_clean_cwe_token(c) for c in candidates if str(c).strip()]
    if not cleaned:
        return ("SA-11", "SA-11 Developer Security Testing (CWE-General)")
    for cid in cleaned:
        if cid in ("CA-02", "CA-2", "RA-05", "RA-5", "SCANNER_ERROR", "SCANNER_TIMEOUT", "CA-02 / RA-05"):
            return ("CA-02 / RA-05", "CA-02 / RA-05 Security Assessment and Vulnerability Monitoring (Automated Scanner Failure)")
        if cid in CWE_NIST_MAP:
            return CWE_NIST_MAP[cid]
    return ("SA-11", f"SA-11 Developer Security Testing (CWE-{cleaned[0]})")


def map_semgrep_to_nist(
    cwe: Union[str, int, Sequence[Union[str, int]]],
    nist_controls: Optional[Sequence[str]] = None,
) -> Tuple[str, str]:
    """Maps a Semgrep finding to NIST SP 800-53, preferring rule metadata over CWE."""
    if nist_controls:
        controls = [str(c).strip() for c in nist_controls if str(c).strip()]
        if controls:
            aps = " / ".join(controls)
            _, cwe_title = map_cwe_to_nist(cwe)
            suffix = cwe_title.split(" ", 1)[1] if " " in cwe_title else cwe_title
            return (aps, f"{aps} {suffix}")
    return map_cwe_to_nist(cwe)


def map_checkov_to_nist(check_id: str, check_name: str) -> Tuple[str, str]:
    """Maps a Checkov static analysis check to its relevant NIST SP 800-53 control.

    Args:
        check_id: Checkov check identifier (e.g., 'CKV_GCP_114').
        check_name: Human-readable name or description of the check.

    Returns:
        A tuple of (Control Enhancement Identifier, Full Control Title).
    """
    cid = str(check_id).upper().strip()
    cname = str(check_name).lower()

    if any(k in cid for k in ["SCANNER", "TIMEOUT", "ERROR"]):
        return ("CA-02 / RA-05", "CA-02 / RA-05 Security Assessment and Vulnerability Monitoring (Automated Scanner Failure)")
    if cid in CHECKOV_NIST_MAP:
        return CHECKOV_NIST_MAP[cid]
    if any(k in cname for k in ["in transit", "in-transit", "tls", "ssl", "https"]):
        return ("SC-08 / SC-13", "SC-08 / SC-13 Transmission Confidentiality and Cryptographic Protection")
    if any(k in cname for k in ["encrypt", "cmek", "csek", "kms", "crypto"]):
        return ("SC-28", "SC-28 Protection of Information at Rest (Cryptographic Hardening)")
    if any(k in cname for k in ["public", "ingress", "firewall", "firewall rule", "0.0.0.0", "exposure"]):
        return ("AC-03 / SC-07", "AC-03 / SC-07 Boundary Protection & Public Ingress Remediation")
    if _CHECKOV_AUTH_WORD_RE.search(cname):
        return ("IA-02 / AC-02", "IA-02 / AC-02 Identification, Authentication, and Account Management")
    if _CHECKOV_AUDIT_WORD_RE.search(cname):
        return ("AU-02 / AU-12", "AU-02 / AU-12 Audit Event Logging and Continuous Review")
    if any(k in cname for k in ["backup", "recovery", "retention", "restore"]):
        return ("CP-09", "CP-09 Information System Backup Automated Implementation")
    if any(k in cname for k in ["iam", "least privilege", "service account", "role", "admin", "privilege"]):
        return ("AC-02 / AC-06", "AC-02 / AC-06 Least Privilege and Access Enforcement")
    if any(k in cname for k in ["shielded", "integrity", "vtpm", "secure boot"]):
        return ("SI-07", "SI-07 Software, Firmware, and Information Integrity")
    if any(k in cname for k in ["versioning", "lifecycle"]):
        return ("SI-12", "SI-12 Information Output Handling and Retention")

    return ("CM-06", f"CM-06 Configuration Settings ({cid})")


#: Upper bound on captured scanner output. Scanner JSON is spooled to a temporary
#: file rather than a pipe so a runaway scanner cannot exhaust memory (CWE-400),
#: and an oversize report is rejected rather than truncated into a partial result
#: that would silently under-report findings.
MAX_OUTPUT_SIZE: int = 50 * 1024 * 1024  # 50 MiB

#: Environment variables propagated to scanner subprocesses. Everything else is
#: dropped so credentials and proxy overrides in the parent environment are not
#: inherited by third-party binaries (SC-7, SA-9).
_ALLOWED_ENV_KEYS: frozenset = frozenset(
    {"PATH", "HOME", "SEMGREP_USER_AGENT_APPEND", "LANG", "LC_ALL", "USER", "XDG_CONFIG_HOME", "SEMGREP_SETTINGS_FILE"}
)

#: Bounded retry policy for transient execution faults.
SUBPROCESS_RETRY_ATTEMPTS: int = 3
SUBPROCESS_RETRY_BASE_SECONDS: float = 1.0

#: Directory holding the default bundled Semgrep ruleset shipped with this skill.
SEMGREP_RULES_DIR: Path = get_skill_root() / "config" / "semgrep_rules"

#: Default bundled Semgrep baseline ruleset file used when --config auto or offline mode is active.
SEMGREP_BUNDLED_RULES_FILE: Path = SEMGREP_RULES_DIR / "public_sector_baseline.yaml"

#: Substrings that identify a synthetic finding representing a scanner outage
#: rather than a real code or infrastructure weakness. These are reported as
#: assessment coverage gaps (CA-2 / RA-5), never as exploitable vulnerabilities.
_SCANNER_FAILURE_MARKERS: Tuple[str, ...] = ("SCANNER_ERROR", "SCANNER_TIMEOUT")

#: Maximum number of characters of third-party scanner stderr retained in a
#: finding. Scanner stderr is diagnostic text, not an accreditation narrative, so
#: it is truncated and scrubbed before it can reach a deliverable.
_MAX_SCANNER_DIAGNOSTIC_CHARS: int = 300


def is_scanner_failure_check_id(check_id: str) -> bool:
    """Reports whether a check identifier denotes a scanner outage.

    Args:
        check_id: Finding check identifier emitted by a scanner adapter.

    Returns:
        True when the identifier represents a scanner execution failure or
        timeout rather than a genuine security weakness.
    """
    upper_id = str(check_id).upper()
    return any(marker in upper_id for marker in _SCANNER_FAILURE_MARKERS)


def _summarize_scanner_diagnostic(raw: Optional[str]) -> str:
    """Scrubs and truncates raw scanner diagnostic output for safe reporting.

    Args:
        raw: Untrusted stderr or exception text emitted by a scanner binary.

    Returns:
        A single-line, secret-scrubbed, length-bounded diagnostic string. Returns
        an empty string when no usable diagnostic text was provided.
    """
    if not raw:
        return ""
    scrubbed = scrub_sensitive_data(str(raw))
    collapsed = " ".join(scrubbed.split())
    if len(collapsed) > _MAX_SCANNER_DIAGNOSTIC_CHARS:
        collapsed = collapsed[:_MAX_SCANNER_DIAGNOSTIC_CHARS].rstrip() + " [truncated]"
    return collapsed


# ==============================================================================
# Raw Scan Memoization
# ==============================================================================
# A single artifact-generation run invokes the POA&M derivation from three call
# sites (the POA&M workbook sheet, the SCTM workbook sheet, and the POA&M YAML),
# which previously meant running every external scanner three times over the same
# unchanged tree. On a realistic estate that is the dominant cost of the whole
# generate stage.
#
# CRITICAL CORRECTNESS CONSTRAINT. An earlier attempt at caching in this codebase
# corrupted deliverables because it memoized *derived* POA&M items. Derivation is
# date-sensitive -- the SCTM hydrator deliberately derives against a past date to
# populate historical risk columns, while the POA&M sheet derives against the
# package effective date -- so sharing derived items across those callers silently
# rewrote one deliverable with the other's dates.
#
# What is cached here is only the RAW scanner output: the set of findings a
# scanner reports for a given tree. That is a pure function of (scanner, target
# bytes, invocation parameters) and contains no date, no system abbreviation, and
# no scheduling. Derivation is always recomputed by the caller.

#: Process-local memo of raw scanner findings. Never persisted to disk: a stale
#: on-disk cache would be indistinguishable from a real scan result.
_SCAN_CACHE: Dict[Tuple[Any, ...], List[Dict[str, Any]]] = {}

#: Directories excluded from the content fingerprint. These are either generated
#: by this engine (and so change on every run, which would defeat the cache) or
#: are not scanner inputs.
_FINGERPRINT_IGNORED_DIRS: frozenset = frozenset(
    {".git", ".terraform", "node_modules", "vendor", "ato_artifacts", "__pycache__", ".venv"}
)

#: Upper bound on files walked when fingerprinting. Beyond this the fingerprint is
#: abandoned and the scan runs uncached, trading speed for guaranteed freshness.
_MAX_FINGERPRINT_FILES: int = 20000


def reset_scan_cache() -> None:
    """Clears the process-local raw scan memo.

    Tests that assert on scanner invocation counts, and any long-lived process
    that scans a mutating tree, must call this between runs.
    """
    _SCAN_CACHE.clear()


def _workspace_fingerprint(root: str) -> Optional[str]:
    """Computes a content fingerprint of the scan target tree.

    The fingerprint covers every non-ignored file's path, size, and modification
    time. It is intentionally a superset of any single scanner's real inputs, so
    an edit anywhere in the tree invalidates every cached scan rather than only
    the one whose file type changed.

    Args:
        root: Absolute path to the scan target directory.

    Returns:
        A hex digest, or None when the tree could not be fingerprinted reliably
        (too large to walk, or unreadable). None means "do not cache", which
        degrades to the previous always-rescan behaviour rather than risking a
        stale result.
    """
    digest = hashlib.sha256()
    seen = 0
    try:
        for current_root, dirs, files in os.walk(root, onerror=_raise_walk_error):
            dirs[:] = sorted(
                d
                for d in dirs
                if d not in _FINGERPRINT_IGNORED_DIRS
                and not d.startswith("ato_artifacts_backup")
            )
            for name in sorted(files):
                seen += 1
                if seen > _MAX_FINGERPRINT_FILES:
                    logger.debug(
                        "Scan target %s exceeds the fingerprint budget; scanning uncached.", root
                    )
                    return None
                path = os.path.join(current_root, name)
                try:
                    stat = os.lstat(path)
                except OSError:
                    # A file that vanished mid-walk makes the fingerprint
                    # unreliable; refuse to cache rather than guess.
                    return None
                digest.update(os.path.relpath(path, root).encode("utf-8", "replace"))
                digest.update(f"|{stat.st_size}|{stat.st_mtime_ns}|".encode("ascii"))
    except OSError as walk_err:
        logger.debug("Could not fingerprint scan target %s: %s", root, walk_err)
        return None
    return digest.hexdigest()


def _raise_walk_error(err: OSError) -> None:
    """Propagates directory-walk errors instead of silently skipping subtrees.

    Args:
        err: The error raised while listing a directory.

    Raises:
        OSError: Always, so the caller abandons the fingerprint.
    """
    raise err


def _cached_scan(
    scanner_key: str,
    target_dir: str,
    invocation_key: Tuple[Any, ...],
    scan_fn: Callable[[], List[Dict[str, Any]]],
) -> List[Dict[str, Any]]:
    """Runs a scanner, reusing an identical prior result within this process.

    Args:
        scanner_key: Stable identifier for the scanner being run.
        target_dir: Resolved scan target directory.
        invocation_key: Every parameter that can change the scanner's output
            (timeout, ruleset, feature flags). Must not include dates or any
            derivation-time value.
        scan_fn: Zero-argument callable performing the real scan.

    Returns:
        The scanner's findings. A copy is returned so a caller that mutates the
        list cannot corrupt the memo for subsequent callers.
    """
    if env_flag_enabled("COMPLIANCE_DISABLE_SCAN_CACHE"):
        return scan_fn()

    fingerprint = _workspace_fingerprint(target_dir)
    if fingerprint is None:
        return scan_fn()

    key = (scanner_key, target_dir, fingerprint) + invocation_key
    if key in _SCAN_CACHE:
        logger.debug("Reusing cached %s results for %s", scanner_key, target_dir)
        return copy.deepcopy(_SCAN_CACHE[key])

    findings = scan_fn()
    _SCAN_CACHE[key] = copy.deepcopy(findings)
    return findings


def _sanitize_scanner_path_env(raw_path: str, cwd: Optional[str] = None) -> str:
    """Strips empty, '.', relative, and working-directory entries from PATH."""
    forbidden: set[str] = set()
    for candidate_cwd in (cwd, os.getcwd()):
        if candidate_cwd:
            try:
                forbidden.add(str(Path(candidate_cwd).resolve()))
            except OSError:
                forbidden.add(candidate_cwd)
    kept: List[str] = []
    for entry in raw_path.split(os.pathsep):
        stripped = entry.strip()
        if not stripped or stripped == "." or not os.path.isabs(stripped):
            continue
        try:
            resolved = str(Path(stripped).resolve())
        except OSError:
            continue
        if resolved in forbidden:
            continue
        kept.append(stripped)
    return os.pathsep.join(kept)


def _safe_run_subprocess(
    cmd: Sequence[str],
    timeout_seconds: float,
    env: Optional[Dict[str, str]] = None,
    retries: int = SUBPROCESS_RETRY_ATTEMPTS,
    cwd: Optional[str] = None,
    runner: Optional[Callable] = None,
) -> "subprocess.CompletedProcess[str]":
    """Executes a scanner binary with a scrubbed environment and bounded output.

    Hardening applied beyond a plain ``subprocess.run``:

    * **No shell** - the command is always executed as an argument vector, so a
      hostile path or filename can never be reinterpreted as shell syntax (CWE-78).
    * **Environment allowlist** - only :data:`_ALLOWED_ENV_KEYS` are propagated.
    * **Bounded capture** - output is spooled to a temporary file and rejected past
      :data:`MAX_OUTPUT_SIZE` rather than buffered without limit (CWE-400).
    * **Fail fast on non-transient faults** - a missing or non-executable binary is
      raised immediately instead of being retried with backoff, which would only
      delay a failure that cannot succeed.

    Args:
        cmd: Command argument vector. The first element is resolved against the
            scrubbed PATH. The caller's sequence is never mutated.
        timeout_seconds: Per-attempt wall-clock timeout.
        env: Optional environment to filter. Defaults to the process environment.
        retries: Total attempts for transient faults. Must be at least 1.
        cwd: Optional working directory for the child. Scanners are always given
            absolute target paths, so this exists to contain incidental scratch
            output (grammar caches, lock files) that a scanner writes relative to
            its own working directory.

    Returns:
        The completed process, with decoded stdout and stderr.

    Raises:
        ValueError: If the command vector is empty or ``retries`` is below 1.
        FileNotFoundError: If the binary cannot be resolved or does not exist.
        PermissionError: If the binary is not executable.
        subprocess.TimeoutExpired: If every attempt exceeds ``timeout_seconds``.
        MemoryError: If the scanner emits more than :data:`MAX_OUTPUT_SIZE`.
    """
    if not cmd:
        raise ValueError("Command cannot be empty")
    if retries < 1:
        raise ValueError(f"retries must be at least 1, got {retries}")

    source_env = env if env is not None else os.environ
    safe_env: Dict[str, str] = {
        key: value for key, value in source_env.items() if key in _ALLOWED_ENV_KEYS
    }
    isolation = _SCAN_ISOLATION.get()
    if isolation is not None:
        safe_env["HOME"] = isolation.home
        safe_env["XDG_CONFIG_HOME"] = isolation.home
        safe_env.pop("SEMGREP_SETTINGS_FILE", None)
        cwd = isolation.cwd
    safe_env["PATH"] = _sanitize_scanner_path_env(
        safe_env.get("PATH", os.defpath), cwd=cwd
    )

    # Resolve into a new list; mutating the caller's vector would corrupt any
    # command the caller intends to reuse, log, or assert against.
    argv: List[str] = [str(arg) for arg in cmd]
    executable = shutil.which(argv[0], path=safe_env.get("PATH", os.defpath))
    if executable:
        argv[0] = executable

    audit = get_audit_logger()
    try:
        completed = run_bounded_command(
            argv,
            timeout=timeout_seconds,
            env=safe_env,
            cwd=cwd,
            max_output_bytes=MAX_OUTPUT_SIZE,
            attempts=retries,
            retry_base_seconds=SUBPROCESS_RETRY_BASE_SECONDS,
            popen=runner or subprocess.Popen,
        )
    except (OSError, MemoryError, subprocess.TimeoutExpired) as exc:
        audit.emit(
            event_type=AuditEvent.EXTERNAL_COMMAND,
            outcome=AuditOutcome.FAILURE,
            subject="security_scanner_bridge",
            obj=argv[0],
            detail={"error": str(exc)},
        )
        raise
    audit.emit(
        event_type=AuditEvent.EXTERNAL_COMMAND,
        outcome=AuditOutcome.SUCCESS,
        subject="security_scanner_bridge",
        obj=argv[0],
        detail={"exit_code": completed.returncode},
    )
    return completed


def _is_safe_binary_path(candidate: Path) -> bool:
    """Validates that a binary path is safe to execute (absolute, exists, executable, not group/world-writable)."""
    import stat
    if not candidate.is_absolute():
        return False
    if not candidate.is_file():
        return False
    if not os.access(candidate, os.X_OK):
        return False
    try:
        info = candidate.stat()
        if info.st_mode & (stat.S_IWGRP | stat.S_IWOTH):
            logger.warning(
                "Refusing group/world-writable binary path %r; permits arbitrary code execution.",
                str(candidate)
            )
            return False
    except OSError:
        return False
    return True


def resolve_preinstalled_scanner_binary(
    tool_name: str,
    custom_path: Optional[str] = None,
) -> Optional[str]:
    """Resolves a pre-installed, locally verified scanner binary.

    Resolution precedence:
    1. Direct explicit custom_path (if provided, exists, and is executable).
    2. Environment variable: {TOOL}_PATH, {TOOL}_BIN, or {TOOL}_BINARY.
    3. System PATH lookup via shutil.which().
    4. Standard secure system binary directories (/usr/local/bin, /usr/bin, /opt/homebrew/bin, etc.).

    Args:
        tool_name: Name of tool binary (e.g. 'trivy', 'syft', 'checkov', 'semgrep').
        custom_path: Optional explicit binary path to verify.

    Returns:
        Absolute path to verified executable binary, or None if unavailable.
    """
    clean_name = os.path.basename(tool_name.strip())
    if not clean_name:
        return None

    # 1. Explicit custom path
    if custom_path:
        cand = Path(custom_path).expanduser().resolve()
        if _is_safe_binary_path(cand):
            return str(cand)

    # 2. Environment variables (e.g. TRIVY_PATH, TRIVY_BIN)
    norm_tool = clean_name.upper().replace("-", "_")
    for env_var in [f"{norm_tool}_PATH", f"{norm_tool}_BIN", f"{norm_tool}_BINARY"]:
        val = os.environ.get(env_var)
        if val:
            cand = Path(val).expanduser().resolve()
            if _is_safe_binary_path(cand):
                return str(cand)

    # 3. System PATH lookup (reject relative / CWD-resolved paths from empty/dot PATH entries)
    found = shutil.which(clean_name)
    if found and os.path.isabs(found):
        found_path = Path(found)
        try:
            cwd_resolved = Path.cwd().resolve()
            found_resolved = found_path.resolve()
            in_cwd = found_resolved.parent == cwd_resolved
        except OSError:
            in_cwd = False
        if not in_cwd and (not found_path.exists() or _is_safe_binary_path(found_path)):
            return found

    # 4. Standard secure directories
    standard_dirs = [
        "/usr/local/bin",
        "/usr/bin",
        "/bin",
        "/opt/homebrew/bin",
        "/opt/bin",
    ]
    for sdir in standard_dirs:
        cand = Path(sdir) / clean_name
        if cand.is_file() and os.access(cand, os.X_OK):
            return str(cand.resolve())

    logger.debug("Scanner binary '%s' is not pre-installed in standard paths or environment.", clean_name)
    return None


def scanner_subprocess_runner(
    scanner_name: str,
    error_check_id: str,
    timeout_check_id: str,
    source_name: str,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Unified execution decorator wrapping scanner subprocess invocations with standardized error handling."""
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            timeout = kwargs.get("timeout_seconds", 300)
            try:
                proc = func(*args, **kwargs)
                if proc is None:
                    return []
                if isinstance(proc, list):
                    return proc
                if proc.returncode not in (0, 1):
                    # Third-party stderr is untrusted, multi-line, and may echo
                    # credentials supplied on the failing command line. Scrub and
                    # flatten it before it can reach a deliverable (SI-11, AU-9).
                    diagnostic = _summarize_scanner_diagnostic(proc.stderr) or "Execution error"
                    logger.error(
                        "%s scanner failed with exit code %d: %s",
                        scanner_name,
                        proc.returncode,
                        diagnostic,
                    )
                    failure_text = (
                        f"{scanner_name} scanner execution failed with exit code "
                        f"{proc.returncode}: {diagnostic}"
                    )
                    return [{
                        "source": source_name,
                        "check_id": error_check_id,
                        "check_name": (
                            f"{scanner_name} automated IaC scan execution failed with exit code {proc.returncode}"
                            if "Checkov" in scanner_name else failure_text
                        ),
                        "message": failure_text,
                        "cwe": "CA-02 / RA-05",
                        "resource": "Terraform Infrastructure" if "Checkov" in scanner_name else "codebase",
                        "location": "codebase",
                        "guideline": f"Investigate {scanner_name} execution failure and ensure automated checks complete without error.",
                        "severity": "High",
                    }]
                if not proc.stdout.strip():
                    if proc.returncode == 0:
                        return []
                    logger.error("%s returned empty output with code %d", scanner_name, proc.returncode)
                    return [{
                        "source": source_name,
                        "check_id": error_check_id,
                        "check_name": (
                            f"{scanner_name} automated IaC scan produced empty output without valid JSON"
                            if "Checkov" in scanner_name
                            else f"{scanner_name} scanner exited with code {proc.returncode} and produced empty output."
                        ),
                        "message": f"{scanner_name} scanner exited with code {proc.returncode} and produced empty output.",
                        "cwe": "CA-02 / RA-05",
                        "resource": "Terraform Infrastructure" if "Checkov" in scanner_name else "codebase",
                        "location": "codebase",
                        "guideline": f"Verify {scanner_name} installation and ensure valid JSON report generation.",
                        "severity": "High",
                    }]
                return json.loads(proc.stdout)
            except subprocess.TimeoutExpired as tex:
                cur_timeout = tex.timeout or timeout
                logger.error("%s scanner timed out after %d seconds.", scanner_name, cur_timeout)
                return [{
                    "source": source_name,
                    "check_id": timeout_check_id,
                    "check_name": (
                        f"{scanner_name} automated IaC scan timed out after {cur_timeout} seconds"
                        if "Checkov" in scanner_name
                        else f"{scanner_name} application SAST scan timed out after {cur_timeout} seconds."
                    ),
                    "message": f"{scanner_name} scan timed out after {cur_timeout} seconds.",
                    "cwe": "CA-02 / RA-05",
                    "resource": "Terraform Infrastructure" if "Checkov" in scanner_name else "codebase",
                    "location": "codebase",
                    "guideline": f"Optimize {scanner_name} scan paths or increase scanner timeout to avoid compliance gaps.",
                    "severity": "High",
                }]
            except (subprocess.SubprocessError, OSError, MemoryError) as proc_err:
                logger.error("%s process execution error: %s", scanner_name, proc_err)
                return [{
                    "source": source_name,
                    "check_id": error_check_id,
                    "check_name": f"{scanner_name} process execution failed: {proc_err}",
                    "message": f"{scanner_name} process execution failed: {proc_err}",
                    "cwe": "CA-02 / RA-05",
                    "resource": "Terraform Infrastructure" if "Checkov" in scanner_name else "codebase",
                    "location": "codebase",
                    "guideline": f"Ensure {scanner_name} dependencies and execution permissions are properly configured.",
                    "severity": "High",
                }]
            except (json.JSONDecodeError, ValueError) as json_err:
                logger.error("%s JSON output parsing failed: %s", scanner_name, json_err)
                return [{
                    "source": source_name,
                    "check_id": error_check_id,
                    "check_name": f"{scanner_name} output was corrupted and could not be parsed as JSON: {json_err}",
                    "message": f"{scanner_name} output could not be parsed as JSON: {json_err}",
                    "cwe": "CA-02 / RA-05",
                    "resource": "Terraform Infrastructure" if "Checkov" in scanner_name else "codebase",
                    "location": "codebase",
                    "guideline": f"Ensure {scanner_name} outputs valid JSON format.",
                    "severity": "High",
                }]
        return wrapper
    return decorator


def run_checkov_scan(target_dir: str, timeout_seconds: int = 300, runner: Optional[Callable] = None) -> List[Dict[str, Any]]:
    """Runs Checkov static analysis and extracts failed IaC checks.

    Args:
        target_dir: Root directory containing Terraform configurations.
        timeout_seconds: Maximum seconds to wait for Checkov execution.

    Returns:
        A list of standardized Checkov finding dictionaries.
    """
    if not runner and not shutil.which("checkov"):
        logger.debug("Checkov executable not found on PATH; skipping IaC scan.")
        return []

    resolved_dir = str(Path(target_dir).resolve())
    if not os.path.isdir(resolved_dir):
        logger.debug("Checkov target directory does not exist: %s", target_dir)
        return []

    if resolved_dir.startswith("-"):
        return []

    cmd = [
        "checkov",
        "-o",
        "json",
        "--compact",
        "--quiet",
        "--skip-path",
        ".terraform",
        "--skip-path",
        "ato_artifacts",
        "--directory",
        resolved_dir,
    ]
    isolation = _SCAN_ISOLATION.get()
    if isolation is not None:
        cmd[1:1] = ["--config-file", isolation.checkov_config]

    @scanner_subprocess_runner(
        scanner_name="Checkov",
        error_check_id="CKV_SCANNER_ERROR",
        timeout_check_id="CKV_SCANNER_TIMEOUT",
        source_name="Checkov IaC Static Security Scanner",
    )
    def _execute_checkov(
        cmd_args: List[str],
        timeout_seconds: int = timeout_seconds,
        scratch_cwd: Optional[Union[str, Path]] = None,
    ) -> Any:
        return _safe_run_subprocess(
            cmd_args, timeout_seconds=timeout_seconds, cwd=str(scratch_cwd) if scratch_cwd is not None else None, runner=runner
        )

    # Checkov embeds a lark-based HCL parser that serializes its compiled grammar
    # into its *current working directory* on first parse. The target is passed as
    # an absolute --directory, so the scan is launched from a throwaway directory
    # to keep that cache out of the operator's workspace.
    with tempfile.TemporaryDirectory(prefix="compliance-checkov-") as scratch:
        data = _execute_checkov(cmd, timeout_seconds=timeout_seconds, scratch_cwd=scratch)

    if isinstance(data, list) and data and "check_id" in data[0] and str(data[0]["check_id"]).startswith("CKV_SCANNER_"):
        return data
    if not data:
        return []

    # Checkov output can be a dict (single framework) or list (multiple frameworks)
    reports = data if isinstance(data, list) else [data]
    findings: List[Dict[str, Any]] = []

    for report in reports:
        failed_checks = report.get("results", {}).get("failed_checks", [])
        for fc in failed_checks:
            check_id = fc.get("check_id", "CKV_UNKNOWN")
            check_name = fc.get("check_name", "IaC Security Misconfiguration")
            resource = fc.get("resource", "resource")
            file_path = fc.get("file_path", "unknown.tf")
            lines = fc.get("file_line_range", [])
            guideline = (
                fc.get("guideline")
                or fc.get("check_name")
                or "Remediate infrastructure configuration in Terraform."
            )
            raw_sev = fc.get("severity")
            if raw_sev:
                severity = str(raw_sev).capitalize()
                sev_source = "reported"
            else:
                text_probe = f"{check_id} {check_name}".lower()
                if any(
                    kw in text_probe
                    for kw in (
                        "public",
                        "0.0.0.0/0",
                        "admin",
                        "impersonat",
                        "kms",
                        "cmek",
                        "csek",
                        "encrypt",
                        "secret",
                        "password",
                        "credential",
                        "ssh",
                        "rdp",
                        "tls",
                        "ssl",
                        "privilege",
                        "root",
                    )
                ):
                    severity = "High"
                elif any(
                    kw in text_probe
                    for kw in ("label", "description", "tag", "naming", "versioning", "retention")
                ):
                    severity = "Low"
                else:
                    severity = "Moderate"
                sev_source = "derived"

            line_str = f":L{lines[0]}-{lines[1]}" if len(lines) >= 2 else ""
            loc_str = f"{file_path}{line_str}"

            findings.append({
                "source": "Checkov IaC Static Security Scanner",
                "check_id": check_id,
                "check_name": check_name,
                "resource": resource,
                "location": loc_str,
                "guideline": guideline,
                "severity": severity,
                "severity_source": sev_source,
            })

    return findings


_SEMGREP_REGISTRY_REF_RE: Final[re.Pattern[str]] = re.compile(
    r"^(?:p|r)/[A-Za-z0-9_./-]+$"
)


def _resolve_semgrep_config(
    semgrep_config: Optional[str] = None,
    target_dir: Optional[Union[str, Path]] = None,
) -> Tuple[Optional[str], Optional[str]]:
    """Resolves which Semgrep ruleset to scan with.

    Resolution order is:
    1. When ``semgrep_config`` is ``None``, empty, ``'bundled'``, or ``'auto'``,
       resolves directly to the bundled offline ruleset
       (``public_sector_baseline.yaml``). Because ``run_semgrep_scan`` always passes
       ``--metrics=off`` for telemetry isolation, Semgrep's CLI refuses
       ``--config auto``; resolving directly to the bundled ruleset avoids spawning
       a guaranteed-to-fail subprocess first.
    2. Registry ruleset references (``p/...`` or ``r/...`` without ``..``) are
       permitted when offline mode is not active.
    3. Arbitrary remote URLs (``http://``, ``https://``, ``file://``) are rejected
       to prevent untrusted configuration from fetching external rulesets.
    4. Local filesystem paths must exist and reside within ``SEMGREP_RULES_DIR`` or
       ``target_dir`` (when ``target_dir`` is supplied).

    Args:
        semgrep_config: Optional operator-supplied ruleset path, registry
            reference, or 'auto'/'bundled'.
        target_dir: Optional target directory boundary used to confine relative or
            project-local custom ruleset paths.

    Returns:
        A tuple of ``(config_reference, error_reason)``. Exactly one element is
        populated: on success ``config_reference`` is the value to pass to
        ``--config``; on failure ``error_reason`` explains why no usable ruleset
        could be resolved.
    """
    is_offline = (
        os.environ.get("COMPLIANCE_OFFLINE", "").strip().lower() in ("1", "true", "yes")
        or os.environ.get("SEMGREP_OFFLINE", "").strip().lower() in ("1", "true", "yes")
    )
    bundled_rules = SEMGREP_BUNDLED_RULES_FILE

    from_operator_env = False
    if semgrep_config is None:
        env_override = os.environ.get(SEMGREP_CONFIG_ENV, "").strip()
        if env_override:
            semgrep_config = env_override
            from_operator_env = True

    if semgrep_config is None:
        if bundled_rules.is_file():
            return str(bundled_rules), None
        return None, "Bundled ruleset missing and external ruleset use must be explicitly enabled."

    override = str(semgrep_config).strip()
    if not override or override.lower() in (
        "bundled",
        "local",
        "baseline",
        "public_sector_baseline",
        "auto",
    ):
        if bundled_rules.is_file():
            return str(bundled_rules), None
        return None, f"Configured semgrep_config '{override or 'bundled'}' requested but bundled ruleset is missing."

    lower_override = override.lower()
    if lower_override.startswith(("http://", "https://", "file://", "ftp://")):
        return None, f"Refusing remote or URL-scheme Semgrep ruleset '{override}'"

    if _SEMGREP_REGISTRY_REF_RE.match(override) and ".." not in override.split("/"):
        if is_offline:
            if bundled_rules.is_file():
                return str(bundled_rules), None
            return None, f"Registry ruleset '{override}' requested in offline mode and bundled ruleset is missing."
        return override, None

    candidate = Path(override).expanduser()
    if not candidate.is_absolute() and target_dir is not None and not candidate.exists():
        candidate = Path(target_dir) / candidate
    try:
        candidate_exists = candidate.exists()
    except OSError as err:
        return None, f"Configured semgrep_config path is not accessible: {override} ({err})"
    if not candidate_exists:
        return None, f"Configured semgrep_config path does not exist: {override}"

    try:
        resolved_candidate = candidate.resolve()
        rules_root = SEMGREP_RULES_DIR.resolve()
        in_skill_rules = (
            resolved_candidate == rules_root
            or rules_root in resolved_candidate.parents
        )
        if not in_skill_rules and not from_operator_env and _SCAN_ISOLATION.get() is None and target_dir is not None:
            resolved_candidate = ensure_path_within_boundary(
                candidate, target_dir, allow_symlinks=False
            )
    except PermissionError as perm_err:
        return None, f"Configured semgrep_config path '{override}' escapes target boundary: {perm_err}"
    except OSError as err:
        return None, f"Configured semgrep_config path is not accessible: {override} ({err})"

    return str(resolved_candidate), None


def _semgrep_coverage_gap_finding(reason: str) -> List[Dict[str, Any]]:
    """Builds the fail-closed finding emitted when Semgrep cannot be configured.

    Args:
        reason: Human-readable explanation of the configuration failure.

    Returns:
        A single-element list holding a CA-2 / RA-5 assessment coverage finding.
    """
    logger.error("Semgrep SAST scan could not be configured: %s", reason)
    return [{
        "source": "Semgrep Application SAST Scanner",
        "check_id": "SEMGREP_SCANNER_ERROR",
        "check_name": "Semgrep static application security testing did not execute.",
        "message": _summarize_scanner_diagnostic(reason),
        "cwe": "CA-02 / RA-05",
        "resource": "codebase",
        "location": "codebase",
        "guideline": (
            "Restore Semgrep SAST coverage so application code is assessed before "
            "the authorization decision."
        ),
        "severity": "High",
    }]


def run_semgrep_scan(
    target_dir: str,
    timeout_seconds: int = 300,
    semgrep_config: Optional[str] = None,
    runner: Optional[Callable] = None,
) -> List[Dict[str, Any]]:
    """Runs a Semgrep SAST scan against application code.

    Args:
        target_dir: Target directory containing application source code.
        timeout_seconds: Maximum seconds to wait for Semgrep execution.
        semgrep_config: Optional ruleset override (local path or internal
            registry reference). Defaults to 'auto' to pull managed rulesets.

    Returns:
        A list of standardized Semgrep finding dictionaries. If Semgrep cannot be
        configured, a single CA-2 / RA-5 assessment coverage finding is returned
        rather than an empty list, so a missing scan is never mistaken for a
        clean scan.
    """
    if not runner and not shutil.which("semgrep"):
        logger.debug("Semgrep executable not found on PATH; skipping SAST scan.")
        return []

    resolved_dir = str(Path(target_dir).resolve())
    if not os.path.isdir(resolved_dir):
        logger.debug("Semgrep target directory does not exist: %s", target_dir)
        return []

    # A target beginning with '-' would be parsed by semgrep as an option.
    if resolved_dir.startswith("-"):
        logger.error("Refusing to scan option-like target path: %s", resolved_dir)
        return []

    config_ref, config_error = _resolve_semgrep_config(semgrep_config, target_dir=resolved_dir)
    if config_error or not config_ref:
        return _semgrep_coverage_gap_finding(config_error or "No Semgrep ruleset resolved.")

    # Use an isolated temporary directory for HOME so semgrep does not pollute the
    # workspace or crash when the source repository is mounted read-only in CI/CD.
    with tempfile.TemporaryDirectory(prefix="semgrep_home_") as temp_home:
        env = os.environ.copy()
        env["HOME"] = temp_home
        env["XDG_CONFIG_HOME"] = os.path.join(temp_home, ".config")
        env["SEMGREP_SETTINGS_FILE"] = os.path.join(temp_home, "settings.yml")
        env["SEMGREP_USER_AGENT_APPEND"] = "ComplianceEngine"

        # 'scan' must immediately follow the binary: semgrep parses any token
        # after a global flag as a scan target, so a trailing subcommand becomes
        # the bogus target 'scan' and the run aborts.
        cmd = [
            "semgrep",
            "scan",
            "--metrics=off",
        ]
        cmd.extend([
            "--disable-version-check",
            # Assessment scope is the accreditation boundary, not the VCS working
            # set. Without this, any gitignored target scans to zero findings and
            # reports as clean.
            "--no-git-ignore",
            "--config",
            config_ref,
            "--json",
            "--quiet",
            "--exclude",
            ".terraform",
            "--exclude",
            "ato_artifacts",
            "--",
            resolved_dir,
        ])

        @scanner_subprocess_runner(
            scanner_name="Semgrep",
            error_check_id="SEMGREP_SCANNER_ERROR",
            timeout_check_id="SEMGREP_SCANNER_TIMEOUT",
            source_name="Semgrep Application SAST Scanner",
        )
        def _execute_semgrep(
            cmd_args: List[str],
            env_vars: Dict[str, str],
            timeout_seconds: int = timeout_seconds,
        ) -> Any:
            return _safe_run_subprocess(cmd_args, env=env_vars, timeout_seconds=timeout_seconds, runner=runner)

        data = _execute_semgrep(cmd, env, timeout_seconds=timeout_seconds)
        bundled_rules = SEMGREP_BUNDLED_RULES_FILE
        if (
            isinstance(data, list)
            and data
            and "check_id" in data[0]
            and str(data[0]["check_id"]).startswith("SEMGREP_SCANNER_")
            and (
                config_ref.lower() == "auto"
                or (
                    "metrics are off" in str(data[0].get("message", "")).lower()
                    and config_ref != str(bundled_rules)
                )
            )
        ):
            if bundled_rules.is_file():
                logger.info(
                    "Semgrep scan with --config %s failed; falling back to bundled baseline ruleset at %s",
                    config_ref,
                    bundled_rules,
                )
                fallback_cmd = [
                    "semgrep",
                    "scan",
                    "--metrics=off",
                    "--disable-version-check",
                    "--no-git-ignore",
                    "--config",
                    str(bundled_rules),
                    "--json",
                    "--quiet",
                    "--exclude",
                    ".terraform",
                    "--exclude",
                    "ato_artifacts",
                    "--",
                    resolved_dir,
                ]
                data = _execute_semgrep(fallback_cmd, env, timeout_seconds=timeout_seconds)

        if isinstance(data, list) and data and "check_id" in data[0] and str(data[0]["check_id"]).startswith("SEMGREP_SCANNER_"):
            return data
        if not data:
            return []

    return _parse_semgrep_results(data.get("results", []))


def _parse_semgrep_results(results: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Normalizes raw Semgrep JSON result entries into finding dictionaries."""
    findings: List[Dict[str, Any]] = []
    for item in results:
        check_id = item.get("check_id", "semgrep.finding")
        extra = item.get("extra", {})
        message = extra.get("message", "Application security concern detected.")
        metadata = extra.get("metadata", {})
        cwe = metadata.get("cwe", ["CWE-General"])
        cwe_list = [str(x).strip() for x in cwe if str(x).strip()] if isinstance(cwe, list) else [str(cwe).strip()]
        cwe_str = cwe_list[0] if cwe_list else "CWE-General"
        nist_raw = metadata.get("nist-800-53") or metadata.get("nist_800_53")
        nist_controls = [
            str(x).strip()
            for x in (nist_raw if isinstance(nist_raw, list) else [nist_raw] if nist_raw else [])
            if str(x).strip()
        ]
        sev_upper = str(extra.get("severity", "WARNING")).upper()
        if sev_upper == "WARNING":
            severity = "Moderate"
        elif sev_upper in ("ERROR", "CRITICAL"):
            severity = "High"
        elif sev_upper == "INFO":
            severity = "Low"
        else:
            severity = sev_upper.capitalize()

        path = item.get("path", "unknown")
        start_l = item.get("start", {}).get("line", 1)
        end_l = item.get("end", {}).get("line", start_l)
        loc_str = f"{path}:L{start_l}-{end_l}"

        findings.append({
            "source": "Semgrep Application SAST Scanner",
            "check_id": check_id,
            "cwe": cwe_str,
            "cwe_list": cwe_list,
            "nist_controls": nist_controls,
            "message": message,
            "location": loc_str,
            "severity": severity,
        })
    return findings


def run_trivy_scan(
    target_dir: str,
    timeout_seconds: int = 300,
    enable_bootstrap: bool = False,
    custom_binary_path: Optional[str] = None,
    runner: Optional[Callable] = None,
) -> List[Dict[str, Any]]:
    """Runs Trivy vulnerability and misconfiguration scanner using pre-installed tooling.

    Args:
        target_dir: Root directory to scan for vulnerabilities and misconfigurations.
        timeout_seconds: Maximum seconds to wait for Trivy execution.
        enable_bootstrap: Deprecated parameter; dynamic downloading is permanently disabled.
        custom_binary_path: Optional explicit path to pre-installed trivy binary.

    Returns:
        List of standardized Trivy finding dictionaries.
    """
    trivy_bin = resolve_preinstalled_scanner_binary("trivy", custom_path=custom_binary_path)
    if not trivy_bin and not runner:
        logger.debug("Trivy executable not found on PATH or standard locations; skipping CVE scan.")
        return []
    if not trivy_bin:
        trivy_bin = "trivy"
        logger.debug("Trivy executable not found on PATH or standard locations; skipping CVE scan.")
        return []

    resolved_dir = str(Path(target_dir).resolve())
    if not os.path.isdir(resolved_dir):
        return []

    if resolved_dir.startswith("-"):
        return []

    cmd = [
        trivy_bin,
        "fs",
        "--format", "json",
        "--quiet",
        "--skip-dirs", ".terraform,ato_artifacts,node_modules",
        "--",
        resolved_dir,
    ]

    @scanner_subprocess_runner(
        scanner_name="Trivy",
        error_check_id="TRIVY_SCANNER_ERROR",
        timeout_check_id="TRIVY_SCANNER_TIMEOUT",
        source_name="Trivy Vulnerability Scanner",
    )
    def _execute_trivy(
        cmd_args: List[str],
        timeout_seconds: int = timeout_seconds,
    ) -> Any:
        return _safe_run_subprocess(cmd_args, timeout_seconds=timeout_seconds, runner=runner)

    data = _execute_trivy(cmd, timeout_seconds=timeout_seconds)
    if isinstance(data, list) and data and "check_id" in data[0] and str(data[0]["check_id"]).startswith("TRIVY_SCANNER_"):
        return data
    if not data:
        return []

    findings: List[Dict[str, Any]] = []
    for target in data.get("Results", []):
        target_path = target.get("Target", "codebase")
        for vuln in target.get("Vulnerabilities", []):
            vid = vuln.get("VulnerabilityID", "CVE-UNKNOWN")
            pkg_name = vuln.get("PkgName", "package")
            inst_ver = vuln.get("InstalledVersion", "unknown")
            fix_ver = vuln.get("FixedVersion", "N/A")
            title = vuln.get("Title") or vuln.get("Description") or f"Vulnerability in {pkg_name}"
            sev = str(vuln.get("Severity", "MEDIUM")).capitalize()
            sev_mapped = "High" if sev.upper() in ("HIGH", "CRITICAL") else "Moderate" if sev.upper() == "MEDIUM" else "Low"

            findings.append({
                "source": "Trivy Vulnerability Scanner",
                "check_id": vid,
                "cwe": "SI-02",
                "message": f"{vid} ({pkg_name} {inst_ver} -> {fix_ver}): {title}",
                "location": f"{target_path}:{pkg_name}",
                "severity": sev_mapped,
            })
    return findings


_GCP_PROJECT_ID_RE: Final[re.Pattern[str]] = re.compile(
    r"^[a-z][a-z0-9-]{4,28}[a-z0-9]$"
)


def fetch_live_scc_findings(
    project_id: Optional[str] = None,
    impact_level: Optional[str] = None,
    timeout_seconds: int = 30,
    runner: Optional[Callable] = None,
) -> List[Dict[str, Any]]:
    """Queries live Google Cloud Security Command Center (SCC) active findings.

    Reconciles real-world cloud posture findings against static code analysis.
    Gracefully degrades with an informative audit log if unauthenticated or offline.
    In DoD IL4/IL5/IL6 environments, skips unaccredited commercial telemetry polling.

    Args:
        project_id: GCP project ID to query findings for.
        impact_level: Optional classification impact level (e.g. 'IL5', 'FedRAMP High').
        timeout_seconds: Maximum duration for API execution.

    Returns:
        List of standardized finding dictionaries with live cloud provenance.
    """
    if impact_level and is_dod_regime(str(impact_level)):
        logger.info("DoD Impact Level %s detected: Skipping unaccredited commercial SCC telemetry calls", impact_level)
        return []

    if not project_id or "[CONFIG_REQUIRED" in str(project_id):
        return []

    clean_project_id = str(project_id).strip()
    if not _GCP_PROJECT_ID_RE.match(clean_project_id):
        logger.warning(
            "Refusing live SCC telemetry query for invalid GCP project_id %r",
            project_id,
        )
        return []

    findings: List[Dict[str, Any]] = []
    if runner or shutil.which("gcloud"):
        cmd = [
            "gcloud", "scc", "findings", "list",
            "--project", clean_project_id,
            "--filter=state=\"ACTIVE\"",
            "--format=json",
            "--limit=50",
        ]
        try:
            proc = _safe_run_subprocess(cmd, timeout_seconds=timeout_seconds, runner=runner)

            if proc.returncode == 0 and proc.stdout.strip():
                raw_findings = json.loads(proc.stdout)
                for item in (raw_findings if isinstance(raw_findings, list) else []):
                    f_obj = item.get("finding", item)
                    cat = f_obj.get("category", "SCC_DEFICIENCY")
                    desc = f_obj.get("description") or f_obj.get("explanation") or cat
                    res_name = f_obj.get("resourceName", project_id)
                    sev = str(f_obj.get("severity", "MEDIUM")).capitalize()
                    sev_mapped = "High" if sev.upper() in ("HIGH", "CRITICAL") else "Moderate" if sev.upper() == "MEDIUM" else "Low"

                    findings.append({
                        "source": "Live Cloud Telemetry (Google SCC v1)",
                        "check_id": f"SCC_{cat}",
                        "check_name": desc,
                        "resource": res_name,
                        "location": f"projects/{project_id}",
                        "guideline": f"Remediate active SCC deficiency: {desc}",
                        "severity": sev_mapped,
                    })
                if findings:
                    logger.info("Successfully ingested %d live findings from Google SCC for project %s", len(findings), project_id)
                    return findings
        except (subprocess.SubprocessError, OSError, json.JSONDecodeError, ValueError, MemoryError) as err:
            logger.debug("Live SCC query via gcloud was non-blocking: %s", err)
            findings.append({
                "source": "Live Cloud Telemetry (Google SCC v1)",
                "check_id": "SCC_QUERY_FAILURE",
                "check_name": f"Live SCC query failed: {err}",
                "resource": project_id,
                "location": f"projects/{project_id}",
                "guideline": "Investigate SCC telemetry query failure.",
                "severity": "High",
            })

    return findings


def parse_sarif_file(fpath: str, allowed_boundary: Optional[str] = None) -> List[Dict[str, Any]]:
    """Parses an individual SARIF report file into standardized findings.

    Args:
        fpath: Path to the *.sarif or *.sarif.json file.
        allowed_boundary: Optional root boundary directory to enforce safe path containment.

    Returns:
        A list of normalized finding dictionaries.
    """
    findings: List[Dict[str, Any]] = []
    try:
        data = read_json_file(fpath, allowed_boundary=allowed_boundary)
        if not isinstance(data, dict):
            return []
        for run in data.get("runs", []):
            tool_name = run.get("tool", {}).get("driver", {}).get("name", "Static Analyzer")
            for res in run.get("results", []):
                rule_id = res.get("ruleId", "RULE_UNKNOWN")
                msg = res.get("message", {}).get("text", "Security issue identified.")
                level = str(res.get("level", "warning")).lower()
                sev = "High" if level in ["error", "critical"] else "Moderate" if level == "warning" else "Low"
                locs = res.get("locations", [])
                loc_str = "codebase"
                if locs:
                    phys = locs[0].get("physicalLocation", {})
                    uri = phys.get("artifactLocation", {}).get("uri", "file")
                    line = phys.get("region", {}).get("startLine", "")
                    loc_str = f"{uri}:{line}" if line else uri

                findings.append({
                    "source": f"{tool_name} (SARIF Ingestion)",
                    "check_id": rule_id,
                    "message": msg,
                    "location": loc_str,
                    "severity": sev,
                })
    except (OSError, json.JSONDecodeError, ValueError, KeyError, PermissionError) as err:
        logger.debug("Failed parsing SARIF file %s: %s", fpath, err)

    return findings


def ingest_sarif_files(target_dir: str) -> List[Dict[str, Any]]:
    """Discovers and parses any *.sarif or *.sarif.json files in target_dir.

    Args:
        target_dir: Root directory to search recursively for SARIF files.

    Returns:
        Aggregated list of findings extracted across all discovered SARIF files.
    """
    findings: List[Dict[str, Any]] = []
    ignored = {".git", ".terraform", "node_modules", "vendor", "ato_artifacts"}
    for root, dirs, files in os.walk(target_dir):
        dirs[:] = [
            d
            for d in dirs
            if d not in ignored and not d.startswith("ato_artifacts_backup")
        ]
        for f in files:
            if f.endswith((".sarif", ".sarif.json")):
                fpath = os.path.join(root, f)
                findings.extend(parse_sarif_file(fpath, allowed_boundary=target_dir))
    return findings


def _rebase_paths(value: Any, old_root: str, new_root: str) -> Any:
    """Rewrites private scan-copy paths in scanner output to the target path."""
    if isinstance(value, str):
        return value.replace(old_root, new_root)
    if isinstance(value, dict):
        return {k: _rebase_paths(v, old_root, new_root) for k, v in value.items()}
    if isinstance(value, list):
        return [_rebase_paths(v, old_root, new_root) for v in value]
    return value


def _highest_group_severity(group: Sequence[Dict[str, Any]]) -> str:
    """Returns the highest-weight severity label across a group of findings."""
    best_sev = "Low"
    best_weight = -1
    for finding in group:
        sev = finding.get("severity", "Low")
        weight = SEVERITY_ORDER.get(str(sev).upper(), 1)
        if weight > best_weight:
            best_weight = weight
            best_sev = sev
    return best_sev


def _dedupe_pair_occurrences(
    group: Sequence[Dict[str, Any]],
    first_keys: Tuple[str, ...] = ("resource",),
) -> List[Tuple[str, str]]:
    """Collects unique ``(resource/target, location)`` pairs preserving order."""
    seen: set = set()
    occurrences: List[Tuple[str, str]] = []
    for finding in group:
        first = ""
        for k in first_keys:
            if finding.get(k):
                first = str(finding[k])
                break
        loc = str(finding.get("location") or "")
        pair = (first, loc)
        if pair not in seen:
            seen.add(pair)
            occurrences.append(pair)
    return occurrences


def _dedupe_loc_occurrences(group: Sequence[Dict[str, Any]]) -> List[str]:
    """Collects unique non-empty ``location`` strings preserving order."""
    seen: set = set()
    occurrences: List[str] = []
    for finding in group:
        loc = str(finding.get("location") or "")
        if loc and loc not in seen:
            seen.add(loc)
            occurrences.append(loc)
    return occurrences


def _format_pair_bullets(
    occurrences: Sequence[Tuple[str, str]],
    noun: str,
    max_display: int = 25,
) -> str:
    """Formats ``(resource, location)`` pairs as an indented bullet list."""
    lines: List[str] = []
    for res, loc in occurrences[:max_display]:
        if res and loc:
            lines.append(f"  - {res} ({loc})")
        elif res:
            lines.append(f"  - {res}")
        elif loc:
            lines.append(f"  - {loc}")
    if len(occurrences) > max_display:
        lines.append(f"  - ... and {len(occurrences) - max_display} additional affected {noun}.")
    return "\n".join(lines)


def _format_loc_bullets(occurrences: Sequence[str], max_display: int = 25) -> str:
    """Formats location strings as an indented bullet list."""
    lines = [f"  - {loc}" for loc in occurrences[:max_display]]
    if len(occurrences) > max_display:
        lines.append(f"  - ... and {len(occurrences) - max_display} additional affected locations.")
    return "\n".join(lines)


def _make_poam_record(
    *,
    sys_abbr: str,
    item_counter: int,
    control_title: str,
    short_title: str,
    desc: str,
    aps: str,
    checks: str,
    target_date: str,
    m_desc: str,
    source: str,
    best_sev: str,
    fixed_low_threat: bool = False,
) -> Dict[str, Any]:
    """Builds a canonical POA&M dictionary for a grouped scanner finding."""
    is_high = best_sev in ("High", "Very High") and not fixed_low_threat
    return {
        "control": control_title,
        "item_id": f"POAM-{sys_abbr}-{item_counter:03d}",
        "title": short_title,
        "desc": desc,
        "aps": aps,
        "checks": checks,
        "status": "Ongoing",
        "sched_date": target_date,
        "milestone_id": f"M-{item_counter:03d}-1",
        "milestone_desc": m_desc,
        "milestone_status": "Open",
        "source": source,
        "severity": best_sev,
        "threat": "Moderate" if is_high else "Low",
        "likelihood": "Moderate" if is_high else "Low",
        "impact": "High" if is_high else "Moderate",
        "residual": "Low",
    }


def _derive_checkov_poam_items(
    live_root: str,
    sys_abbr: str,
    base_dt: datetime,
    item_counter: int,
    checkov_timeout: int,
    include_scanner_failures: bool,
) -> Tuple[List[Dict[str, Any]], int]:
    """Runs Checkov and converts grouped findings into POA&M items."""
    if not shutil.which("checkov"):
        logger.warning("Checkov executable not found on PATH; IaC security scan was skipped.")
    checkov_findings = _cached_scan(
        "checkov",
        str(Path(live_root).resolve()),
        (checkov_timeout,),
        lambda: run_checkov_scan(live_root, timeout_seconds=checkov_timeout),
    )
    grouped: Dict[str, List[Dict[str, Any]]] = collections.defaultdict(list)
    for finding in checkov_findings:
        ck = finding.get("check_id") or finding.get("check_name") or "CHECK_UNKNOWN"
        grouped[ck].append(finding)

    items: List[Dict[str, Any]] = []
    for check_id, group in grouped.items():
        f0 = group[0]
        check_name = f0.get("check_name") or check_id
        guideline = f0.get("guideline") or check_name
        source = f0.get("source") or "Checkov IaC Static Security Scanner"
        best_sev = _highest_group_severity(group)
        aps, control_title = map_checkov_to_nist(check_id, check_name)
        sched_days = 30 if best_sev in ("High", "Very High") else 60 if best_sev in ("Moderate", "Medium") else 90
        target_date = compute_poam_target_date(sched_days, base_dt)
        occurrences = _dedupe_pair_occurrences(group, ("resource",))
        total_count = len(occurrences)

        if is_scanner_failure_check_id(check_id):
            if not include_scanner_failures:
                logger.warning(
                    "Scanner outage detected for %s (%s); omitting from POA&M (only true security issues are tracked in POA&M).",
                    source,
                    check_id,
                )
                continue
            scanner_label = source or "Infrastructure-as-Code scanner"
            diagnostic = _summarize_scanner_diagnostic(check_name)
            short_title = f"{scanner_label} did not complete; Terraform infrastructure was not assessed."
            desc = (
                f"{short_title} Automated infrastructure-as-code analysis produced "
                f"no results for this assessment run, so the deployed baseline has "
                f"no configuration-scan evidence supporting the authorization decision."
            )
            if diagnostic:
                desc = f"{desc} Scanner diagnostic: {diagnostic}"
            m_desc = (
                f"Restore {scanner_label} coverage, re-run the assessment against "
                f"the full Terraform boundary, and confirm the resulting findings "
                f"are reflected in this POA&M."
            )
        elif total_count <= 1:
            res, loc = occurrences[0] if occurrences else ("", "")
            loc_str = f" ({loc})" if loc else ""
            on_res = f" on {res}" if res else ""
            desc = f"[{check_id}] {check_name}{on_res}{loc_str}."
            short_title = desc
            m_desc = f"Remediate {res or check_id} in Terraform: {guideline}"
        else:
            short_title = f"[{check_id}] {check_name} ({total_count} affected locations)"
            bullets = _format_pair_bullets(occurrences, "locations")
            desc = f"[{check_id}] {check_name} across {total_count} affected locations:\n{bullets}"
            m_desc = f"Remediate {total_count} affected resources in Terraform ({guideline}). Verify configuration across all affected modules."

        items.append(
            _make_poam_record(
                sys_abbr=sys_abbr,
                item_counter=item_counter,
                control_title=control_title,
                short_title=short_title,
                desc=desc,
                aps=aps,
                checks=check_id,
                target_date=target_date,
                m_desc=m_desc,
                source=source,
                best_sev=best_sev,
            )
        )
        item_counter += 1
    return items, item_counter


def _derive_semgrep_poam_items(
    live_root: str,
    sys_abbr: str,
    base_dt: datetime,
    item_counter: int,
    semgrep_timeout: int,
    semgrep_config: Optional[str],
    include_scanner_failures: bool,
) -> Tuple[List[Dict[str, Any]], int]:
    """Runs Semgrep and converts grouped findings into POA&M items."""
    if not shutil.which("semgrep"):
        logger.warning("Semgrep executable not found on PATH; SAST security scan was skipped.")
    semgrep_findings = _cached_scan(
        "semgrep",
        str(Path(live_root).resolve()),
        (semgrep_timeout, semgrep_config or ""),
        lambda: run_semgrep_scan(
            live_root,
            timeout_seconds=semgrep_timeout,
            semgrep_config=semgrep_config,
        ),
    )
    grouped: Dict[str, List[Dict[str, Any]]] = collections.defaultdict(list)
    for finding in semgrep_findings:
        ck = finding.get("check_id") or "SEMGREP_FINDING"
        grouped[ck].append(finding)

    items: List[Dict[str, Any]] = []
    for check_id, group in grouped.items():
        sf0 = group[0]
        msg = sf0.get("message") or check_id
        cwe = sf0.get("cwe") or ""
        source = sf0.get("source") or "Semgrep SAST Code Scanner"
        best_sev = _highest_group_severity(group)
        aps, control_title = map_semgrep_to_nist(
            sf0.get("cwe_list") or cwe,
            sf0.get("nist_controls"),
        )
        sched_days = 30 if best_sev in ("High", "Very High") else 60
        target_date = compute_poam_target_date(sched_days, base_dt)
        occurrences = _dedupe_loc_occurrences(group)
        total_count = len(occurrences)

        if is_scanner_failure_check_id(check_id):
            if not include_scanner_failures:
                logger.warning(
                    "Scanner outage detected for %s (%s); omitting from POA&M (only true security issues are tracked in POA&M).",
                    source,
                    check_id,
                )
                continue
            scanner_label = source or "Application SAST scanner"
            diagnostic = _summarize_scanner_diagnostic(
                sf0.get("message") or sf0.get("check_name") or ""
            )
            short_title = f"{scanner_label} did not complete; application code was not assessed."
            desc = (
                f"{short_title} Automated static application security testing "
                f"produced no results for this assessment run, so the codebase "
                f"has no SAST evidence supporting the authorization decision."
            )
            if diagnostic:
                desc = f"{desc} Scanner diagnostic: {diagnostic}"
            m_desc = (
                f"Restore {scanner_label} coverage, re-run the assessment against "
                f"the full boundary, and confirm the resulting findings are "
                f"reflected in this POA&M."
            )
        elif total_count <= 1:
            loc = occurrences[0] if occurrences else "codebase"
            desc = f"[{check_id}] {msg} at {loc}."
            short_title = desc
            m_desc = f"Sanitize and refactor code at {loc} to eliminate vulnerability."
        else:
            short_title = f"[{check_id}] {msg} ({total_count} affected locations)"
            bullets = _format_loc_bullets(occurrences)
            desc = f"[{check_id}] {msg} across {total_count} affected locations:\n{bullets}"
            m_desc = f"Sanitize and refactor code across {total_count} affected locations to eliminate vulnerability."

        items.append(
            _make_poam_record(
                sys_abbr=sys_abbr,
                item_counter=item_counter,
                control_title=control_title,
                short_title=short_title,
                desc=desc,
                aps=aps,
                checks=check_id,
                target_date=target_date,
                m_desc=m_desc,
                source=source,
                best_sev=best_sev,
            )
        )
        item_counter += 1
    return items, item_counter


def _derive_trivy_poam_items(
    live_root: str,
    sys_abbr: str,
    base_dt: datetime,
    item_counter: int,
    trivy_timeout: int,
    enable_bootstrap: bool,
    include_scanner_failures: bool,
) -> Tuple[List[Dict[str, Any]], int]:
    """Runs Trivy and converts grouped findings into POA&M items."""
    trivy_findings = run_trivy_scan(
        live_root,
        timeout_seconds=trivy_timeout,
        enable_bootstrap=enable_bootstrap,
    )
    grouped: Dict[str, List[Dict[str, Any]]] = collections.defaultdict(list)
    for finding in trivy_findings:
        ck = finding.get("check_id") or "TRIVY_CVE"
        grouped[ck].append(finding)

    items: List[Dict[str, Any]] = []
    for check_id, group in grouped.items():
        tf0 = group[0]
        msg = tf0.get("message") or tf0.get("title") or check_id
        cwe = tf0.get("cwe", "SI-02")
        source = tf0.get("source") or "Trivy Container & Dependency Scanner"

        if is_scanner_failure_check_id(check_id) and not include_scanner_failures:
            logger.warning(
                "Scanner outage detected for %s (%s); omitting from POA&M (only true security issues are tracked in POA&M).",
                source,
                check_id,
            )
            continue

        best_sev = _highest_group_severity(group)
        aps, control_title = map_cwe_to_nist(cwe)
        sched_days = 30 if best_sev in ("High", "Very High") else 60
        target_date = compute_poam_target_date(sched_days, base_dt)
        occurrences = _dedupe_pair_occurrences(group, ("target", "resource"))
        total_count = len(occurrences)

        if total_count <= 1:
            tgt, loc = occurrences[0] if occurrences else ("", "")
            loc_info = f" ({loc})" if loc else f" on {tgt}" if tgt else ""
            desc = f"[{check_id}] {msg}{loc_info}."
            short_title = desc
            m_desc = f"Upgrade and patch vulnerable package or fix configuration at {loc or tgt or 'affected target'}."
        else:
            short_title = f"[{check_id}] {msg} ({total_count} affected targets)"
            bullets = _format_pair_bullets(occurrences, "targets")
            desc = f"[{check_id}] {msg} across {total_count} affected targets:\n{bullets}"
            m_desc = f"Upgrade and patch vulnerable packages across {total_count} affected targets."

        items.append(
            _make_poam_record(
                sys_abbr=sys_abbr,
                item_counter=item_counter,
                control_title=control_title,
                short_title=short_title,
                desc=desc,
                aps=aps,
                checks=check_id,
                target_date=target_date,
                m_desc=m_desc,
                source=source,
                best_sev=best_sev,
            )
        )
        item_counter += 1
    return items, item_counter


def _derive_live_scc_poam_items(
    cfg: Dict[str, Any],
    sys_abbr: str,
    base_dt: datetime,
    item_counter: int,
) -> Tuple[List[Dict[str, Any]], int]:
    """Queries live Google SCC (when permitted) and converts findings into POA&M items."""
    allow_live_telemetry = env_flag_enabled("COMPLIANCE_ALLOW_LIVE_CLOUD_TELEMETRY")
    impact_level = str(
        cfg.get("impact_level")
        or cfg.get("baseline")
        or cfg.get("system_information", {}).get("impact_level")
        or cfg.get("system_information", {}).get("baseline")
        or os.environ.get("IMPACT_LEVEL", "")
    ).upper()
    if is_dod_regime(impact_level):
        logger.info("DoD Impact Level %s detected: Skipping unaccredited commercial cloud telemetry calls", impact_level)
        live_scc: List[Dict[str, Any]] = []
    elif not allow_live_telemetry:
        logger.warning(
            "Skipping live cloud telemetry query: set COMPLIANCE_ALLOW_LIVE_CLOUD_TELEMETRY=1 "
            "in the operator environment to authorize gcloud SCC queries."
        )
        live_scc = []
    else:
        project_id = cfg.get("project_id") or os.environ.get("GOOGLE_CLOUD_PROJECT")
        live_scc = fetch_live_scc_findings(project_id=project_id, impact_level=impact_level)

    grouped: Dict[str, List[Dict[str, Any]]] = collections.defaultdict(list)
    for finding in live_scc:
        ck = finding.get("check_id") or finding.get("check_name") or "SCC_FINDING"
        grouped[ck].append(finding)

    items: List[Dict[str, Any]] = []
    for check_id, group in grouped.items():
        sf0 = group[0]
        check_name = sf0.get("check_name") or check_id
        guideline = sf0.get("guideline") or check_name
        source = sf0.get("source") or "Live Cloud Telemetry (Google SCC v1)"
        best_sev = _highest_group_severity(group)
        aps, control_title = map_checkov_to_nist(check_id, check_name)
        sched_days = 30 if best_sev in ("High", "Very High") else 60
        target_date = compute_poam_target_date(sched_days, base_dt)
        occurrences = _dedupe_pair_occurrences(group, ("resource",))
        total_count = len(occurrences)

        if total_count <= 1:
            res, loc = occurrences[0] if occurrences else ("", "")
            loc_str = f" ({loc})" if loc else ""
            desc = f"[{check_id}] {check_name} on {res}{loc_str}."
            short_title = desc
            m_desc = f"Remediate live cloud finding in {loc or res}: {guideline}"
        else:
            short_title = f"[{check_id}] {check_name} ({total_count} affected resources)"
            bullets = _format_pair_bullets(occurrences, "resources")
            desc = f"[{check_id}] {check_name} across {total_count} affected cloud resources:\n{bullets}"
            m_desc = f"Remediate {total_count} affected cloud resources in cloud console / IaC: {guideline}"

        items.append(
            _make_poam_record(
                sys_abbr=sys_abbr,
                item_counter=item_counter,
                control_title=control_title,
                short_title=short_title,
                desc=desc,
                aps=aps,
                checks=check_id,
                target_date=target_date,
                m_desc=m_desc,
                source=source,
                best_sev=best_sev,
            )
        )
        item_counter += 1
    return items, item_counter


def _derive_sarif_poam_items(
    target_dir: str,
    sys_abbr: str,
    base_dt: datetime,
    item_counter: int,
    run_sarif: bool,
    explicit_sarifs: Sequence[str],
) -> Tuple[List[Dict[str, Any]], int]:
    """Ingests SARIF files under ``target_dir`` and converts findings into POA&M items."""
    sarif_findings: List[Dict[str, Any]] = []
    if run_sarif:
        sarif_findings.extend(ingest_sarif_files(target_dir))
    for sarif_path in explicit_sarifs or []:
        abs_p = sarif_path if os.path.isabs(sarif_path) else os.path.join(target_dir, sarif_path)
        if os.path.isfile(abs_p):
            sarif_findings.extend(parse_sarif_file(abs_p, allowed_boundary=target_dir))

    grouped: Dict[str, List[Dict[str, Any]]] = collections.defaultdict(list)
    for finding in sarif_findings:
        ck = finding.get("check_id") or "SARIF_FINDING"
        grouped[ck].append(finding)

    items: List[Dict[str, Any]] = []
    for rule_id, group in grouped.items():
        sar0 = group[0]
        msg = sar0.get("message", "")
        source = sar0.get("source", "SARIF Analysis Report")
        if rule_id.startswith("CKV_"):
            aps, control_title = map_checkov_to_nist(rule_id, msg)
        elif "CWE-" in rule_id or "CWE-" in msg:
            cwe_part = [w for w in (rule_id + " " + msg).split() if "CWE-" in w]
            aps, control_title = map_cwe_to_nist(cwe_part[0]) if cwe_part else ("SA-11", f"SA-11 Developer Security Testing ({rule_id})")
        else:
            aps, control_title = "SA-11(1)", f"SA-11 Developer Security Testing ({rule_id})"

        best_sev = _highest_group_severity(group)
        sched_days = 30 if best_sev in ("High", "Very High") else 60
        target_date = compute_poam_target_date(sched_days, base_dt)
        occurrences = _dedupe_loc_occurrences(group)
        total_count = len(occurrences)

        if total_count <= 1:
            loc = occurrences[0] if occurrences else "codebase"
            desc = f"[{rule_id}] {msg} ({loc})."
            short_title = desc
            m_desc = f"Address finding from {source} at {loc}."
        else:
            short_title = f"[{rule_id}] {msg} ({total_count} affected locations)"
            bullets = _format_loc_bullets(occurrences)
            desc = f"[{rule_id}] {msg} across {total_count} affected locations:\n{bullets}"
            m_desc = f"Address finding from {source} across {total_count} affected locations."

        items.append(
            _make_poam_record(
                sys_abbr=sys_abbr,
                item_counter=item_counter,
                control_title=control_title,
                short_title=short_title,
                desc=desc,
                aps=aps,
                checks=rule_id,
                target_date=target_date,
                m_desc=m_desc,
                source=source,
                best_sev=best_sev,
                fixed_low_threat=True,
            )
        )
        item_counter += 1
    return items, item_counter


def scan_and_derive_poam_items(
    target_dir: str,
    sys_abbr: str = "SYS",
    eff_date: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
    scan_root: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Executes available scanners and maps findings to NIST SP 800-53 Rev. 5 POA&M items."""
    if not eff_date:
        eff_date = current_utc_datetime().replace(tzinfo=None).strftime("%Y-%m-%d")
    try:
        base_dt = datetime.strptime(eff_date, "%Y-%m-%d")
    except (ValueError, TypeError):
        base_dt = current_utc_datetime().replace(tzinfo=None)

    cfg = config or {}
    include_scanner_failures = bool(cfg.get("include_scanner_failures_in_poam", False))
    live_root = scan_root or target_dir
    kill_switch = env_flag_enabled(DISABLE_LIVE_SCANNERS_ENV)
    run_checkov = bool(cfg.get("run_checkov", False)) and not kill_switch
    run_semgrep = bool(cfg.get("run_semgrep", False)) and not kill_switch
    run_trivy = bool(cfg.get("run_trivy", False)) and not kill_switch
    run_sarif = cfg.get("ingest_sarif", True)
    explicit_sarifs = cfg.get("sarif_reports", [])

    if "_operator_semgrep_config" in cfg:
        semgrep_config = cfg.get("_operator_semgrep_config") or None
    elif "security_scanners" in cfg or "infrastructure_components" in cfg:
        semgrep_config = os.environ.get(SEMGREP_CONFIG_ENV, "").strip() or None
    else:
        semgrep_config = cfg.get("semgrep_config") or os.environ.get(SEMGREP_CONFIG_ENV, "").strip() or None

    poam_items: List[Dict[str, Any]] = []
    item_counter = 100

    if run_checkov:
        new_items, item_counter = _derive_checkov_poam_items(
            live_root,
            sys_abbr,
            base_dt,
            item_counter,
            int(cfg.get("checkov_timeout", 300)),
            include_scanner_failures,
        )
        poam_items.extend(new_items)

    if run_semgrep:
        new_items, item_counter = _derive_semgrep_poam_items(
            live_root,
            sys_abbr,
            base_dt,
            item_counter,
            int(cfg.get("semgrep_timeout", 300)),
            semgrep_config,
            include_scanner_failures,
        )
        poam_items.extend(new_items)

    if run_trivy:
        new_items, item_counter = _derive_trivy_poam_items(
            live_root,
            sys_abbr,
            base_dt,
            item_counter,
            int(cfg.get("trivy_timeout", 300)),
            bool(cfg.get("enable_scanner_bootstrap", False)),
            include_scanner_failures,
        )
        poam_items.extend(new_items)

    if cfg.get("query_live_cloud_telemetry", False):
        new_items, item_counter = _derive_live_scc_poam_items(
            cfg, sys_abbr, base_dt, item_counter
        )
        poam_items.extend(new_items)

    new_items, item_counter = _derive_sarif_poam_items(
        target_dir, sys_abbr, base_dt, item_counter, bool(run_sarif), explicit_sarifs
    )
    poam_items.extend(new_items)

    if scan_root and str(scan_root) != str(target_dir):
        poam_items = _rebase_paths(poam_items, str(Path(scan_root).resolve()), str(Path(target_dir).resolve()))
    return scrub_sensitive_data(poam_items)
