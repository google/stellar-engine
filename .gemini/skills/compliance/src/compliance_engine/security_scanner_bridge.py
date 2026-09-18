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
import copy
import functools
import hashlib
import json
import logging
import os
from pathlib import Path
import random
import shutil
import subprocess
import tempfile
import time
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, Union

try:
    from .audit_log import get_audit_logger, AuditOutcome, AuditEvent
except (ImportError, ValueError):
    from audit_log import get_audit_logger, AuditOutcome, AuditEvent

try:
    from .file_helpers import (
        scrub_sensitive_data,
        read_json_file,
        get_skill_root,
    )
except ImportError:
    from file_helpers import (
        scrub_sensitive_data,
        read_json_file,
        get_skill_root,
    )

logger = logging.getLogger(__name__)

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
    "22": ("AC-03", "AC-03 Access Enforcement (Path Traversal)"),
    "798": ("IA-05", "IA-05 Authenticator Management (Hardcoded Credentials)"),
    "259": ("IA-05", "IA-05 Authenticator Management (Hardcoded Password)"),
    "321": ("IA-05", "IA-05 Authenticator Management (Hardcoded Cryptographic Key)"),
    "327": ("SC-13", "SC-13 Cryptographic Protection (Broken/Risky Algorithm)"),
    "328": ("SC-13", "SC-13 Cryptographic Protection (Reversible One-Way Hash)"),
    "287": ("IA-02", "IA-02 Identification and Authentication (Improper Authentication)"),
    "306": ("IA-02", "IA-02 Identification and Authentication (Missing Authentication)"),
    "502": ("SI-10", "SI-10 Information Input Validation (Insecure Deserialization)"),
    "611": ("SI-10", "SI-10 Information Input Validation (XML External Entity - XXE)"),
    "918": ("SC-07", "SC-07 Boundary Protection (Server-Side Request Forgery - SSRF)"),
}


def map_cwe_to_nist(cwe_id: Union[str, int]) -> Tuple[str, str]:
    """Maps a CWE identifier to its corresponding NIST SP 800-53 Rev. 5 control.

    Args:
        cwe_id: Raw CWE identifier (e.g., 'CWE-89' or 89).

    Returns:
        A tuple of (Control Enhancement Identifier, Full Control Title).
    """
    clean_id = str(cwe_id).upper().replace("CWE-", "").strip()
    if ":" in clean_id:
        clean_id = clean_id.split(":", 1)[0].strip()
    if clean_id in ("CA-02", "CA-2", "RA-05", "RA-5", "SCANNER_ERROR", "SCANNER_TIMEOUT", "CA-02 / RA-05"):
        return ("CA-02 / RA-05", "CA-02 / RA-05 Security Assessment and Vulnerability Monitoring (Automated Scanner Failure)")
    if clean_id in CWE_NIST_MAP:
        return CWE_NIST_MAP[clean_id]
    return ("SA-11", f"SA-11 Developer Security Testing (CWE-{clean_id})")


def map_checkov_to_nist(check_id: str, check_name: str) -> Tuple[str, str]:
    """Maps a Checkov static analysis check to its relevant NIST SP 800-53 control.

    Args:
        check_id: Checkov check identifier (e.g., 'CKV_GCP_114').
        check_name: Human-readable name or description of the check.

    Returns:
        A tuple of (Control Enhancement Identifier, Full Control Title).
    """
    cid = str(check_id).upper()
    cname = str(check_name).lower()

    if any(k in cid for k in ["SCANNER", "TIMEOUT", "ERROR"]):
        return ("CA-02 / RA-05", "CA-02 / RA-05 Security Assessment and Vulnerability Monitoring (Automated Scanner Failure)")
    if any(k in cname for k in ["encrypt", "cmek", "kms", "crypto"]):
        return ("SC-28", "SC-28 Protection of Information at Rest (Cryptographic Hardening)")
    if any(k in cname for k in ["public", "ingress", "firewall", "firewall rule", "0.0.0.0", "exposure"]):
        return ("AC-03 / SC-07", "AC-03 / SC-07 Boundary Protection & Public Ingress Remediation")
    if any(k in cname for k in ["log", "audit", "sink", "monitor"]) and "blog" not in cname:
        return ("AU-02 / AU-12", "AU-02 / AU-12 Audit Event Logging and Continuous Review")
    if any(k in cname for k in ["backup", "recovery", "retention", "restore"]):
        return ("CP-09", "CP-09 Information System Backup Automated Implementation")
    if any(k in cname for k in ["iam", "least privilege", "service account", "role", "admin", "privilege"]):
        return ("AC-02 / AC-06", "AC-02 / AC-06 Least Privilege and Access Enforcement")
    if any(k in cname for k in ["shielded", "integrity", "vtpm", "secure boot"]):
        return ("SI-07", "SI-07 Software, Firmware, and Information Integrity")
    if any(k in cname for k in ["versioning", "lifecycle"]):
        return ("SI-12", "SI-12 Information Output Handling and Retention")
    if any(k in cname for k in ["tls", "ssl", "https"]):
        return ("SC-08 / SC-13", "SC-08 / SC-13 Transmission Confidentiality and Cryptographic Protection")

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
            dirs[:] = sorted(d for d in dirs if d not in _FINGERPRINT_IGNORED_DIRS)
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
    if os.getenv("COMPLIANCE_DISABLE_SCAN_CACHE") == "1":
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

    # Resolve into a new list; mutating the caller's vector would corrupt any
    # command the caller intends to reuse, log, or assert against.
    argv: List[str] = [str(arg) for arg in cmd]
    executable = shutil.which(argv[0], path=safe_env.get("PATH", os.defpath))
    if executable:
        argv[0] = executable

    runner_func = runner or subprocess.Popen

    audit = get_audit_logger()
    last_error: Optional[BaseException] = None

    for attempt in range(1, retries + 1):
        try:
            with (
                tempfile.TemporaryFile(mode="w+", encoding="utf-8") as out_f,
                tempfile.TemporaryFile(mode="w+", encoding="utf-8") as err_f,
            ):
                with runner_func(
                    argv,
                    stdout=out_f,
                    stderr=err_f,
                    text=True,
                    env=safe_env,
                    cwd=cwd,
                    shell=False,
                ) as proc:
                    try:
                        proc.wait(timeout=timeout_seconds)
                    except subprocess.TimeoutExpired:
                        proc.kill()
                        proc.wait()
                        raise

                    out_f.seek(0)
                    stdout_data = out_f.read(MAX_OUTPUT_SIZE + 1)
                    err_f.seek(0)
                    stderr_data = err_f.read(MAX_OUTPUT_SIZE + 1)

                if len(stdout_data) > MAX_OUTPUT_SIZE or len(stderr_data) > MAX_OUTPUT_SIZE:
                    raise MemoryError(
                        f"{argv[0]} emitted more than {MAX_OUTPUT_SIZE} bytes; "
                        "refusing to process a truncated scanner report."
                    )

                completed = subprocess.CompletedProcess(
                    proc.args, proc.returncode, stdout_data, stderr_data
                )

            audit.emit(
                event_type=AuditEvent.EXTERNAL_COMMAND,
                outcome=AuditOutcome.SUCCESS,
                subject="security_scanner_bridge",
                obj=argv[0],
                detail={"attempt": attempt, "exit_code": completed.returncode},
            )
            return completed

        except (FileNotFoundError, PermissionError, NotADirectoryError, MemoryError) as exc:
            # Non-transient: the binary is absent, unusable, or the report is
            # oversize. Retrying cannot change the outcome.
            audit.emit(
                event_type=AuditEvent.EXTERNAL_COMMAND,
                outcome=AuditOutcome.FAILURE,
                subject="security_scanner_bridge",
                obj=argv[0],
                detail={"attempt": attempt, "error": str(exc), "transient": False},
            )
            raise

        except (subprocess.TimeoutExpired, OSError) as exc:
            last_error = exc
            audit.emit(
                event_type=AuditEvent.EXTERNAL_COMMAND,
                outcome=AuditOutcome.FAILURE,
                subject="security_scanner_bridge",
                obj=argv[0],
                detail={"attempt": attempt, "error": str(exc), "transient": True},
            )
            if attempt == retries:
                raise
            delay = SUBPROCESS_RETRY_BASE_SECONDS * (2 ** (attempt - 1))
            # Jitter prevents concurrent runs from synchronizing their retries.
            delay += random.uniform(0, delay / 2)
            logger.warning(
                "%s attempt %d/%d failed (%s); retrying in %.2fs",
                argv[0],
                attempt,
                retries,
                exc,
                delay,
            )
            time.sleep(delay)

    # Defensive: the loop either returns or raises on its final attempt.
    raise RuntimeError(f"{argv[0]} exhausted {retries} attempts") from last_error



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
        if cand.is_file() and os.access(cand, os.X_OK):
            return str(cand)

    # 2. Environment variables (e.g. TRIVY_PATH, TRIVY_BIN)
    norm_tool = clean_name.upper().replace("-", "_")
    for env_var in [f"{norm_tool}_PATH", f"{norm_tool}_BIN", f"{norm_tool}_BINARY"]:
        val = os.environ.get(env_var)
        if val:
            cand = Path(val).expanduser().resolve()
            if _is_safe_binary_path(cand):
                return str(cand)

    # 3. System PATH lookup
    found = shutil.which(clean_name)
    if found:
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


def bootstrap_scanner_binary(tool_name: str, cache_dir: Optional[str] = None) -> Optional[str]:
    """Deprecated: Resolves a pre-installed binary.
    Use resolve_preinstalled_scanner_binary instead.
    """
    return resolve_preinstalled_scanner_binary(tool_name)


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
                        "check_name": f"{scanner_name} automated IaC scan execution failed with exit code {proc.returncode}" if "Checkov" in scanner_name else failure_text,
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
                        "check_name": f"{scanner_name} automated IaC scan produced empty output without valid JSON" if "Checkov" in scanner_name else f"{scanner_name} scanner exited with code {proc.returncode} and produced empty output.",
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
                    "check_name": f"{scanner_name} automated IaC scan timed out after {cur_timeout} seconds" if "Checkov" in scanner_name else f"{scanner_name} application SAST scan timed out after {cur_timeout} seconds.",
                    "message": f"{scanner_name} scan timed out after {cur_timeout} seconds.",
                    "cwe": "CA-02 / RA-05",
                    "resource": "Terraform Infrastructure" if "Checkov" in scanner_name else "codebase",
                    "location": "codebase",
                    "guideline": f"Optimize {scanner_name} scan paths or increase scanner timeout to avoid compliance gaps.",
                    "severity": "High",
                }]
            except (subprocess.SubprocessError, OSError) as proc_err:
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
            cmd_args, timeout_seconds=timeout_seconds, cwd=scratch_cwd, runner=runner
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
            severity = str(fc.get("severity") or "MODERATE").capitalize()

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
            })

    return findings


def _resolve_semgrep_config(semgrep_config: Optional[str] = None) -> Tuple[Optional[str], Optional[str]]:
    """Resolves which Semgrep ruleset to scan with.

    Resolution order is:
    1. An explicit override supplied by configuration or caller (e.g. a
       local directory/file path, or a remote/registry reference like 'p/ci').
    2. Defaults to 'auto', pulling Semgrep's managed ruleset automatically.
       Since the compliance engine evaluates codebase structure and uses LLM
       capabilities rather than processing production data in an air-gapped
       environment, external ruleset pulling is supported and expected.
    3. If an explicit local path is provided, verifies that the path exists.

    Args:
        semgrep_config: Optional operator-supplied ruleset path, registry
            reference, or 'auto'. Defaults to 'auto'.

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
    bundled_rules = SEMGREP_RULES_DIR / "public_sector_baseline.yaml"

    if semgrep_config is None:
        if bundled_rules.is_file():
            return str(bundled_rules.resolve()), None
        return None, "Bundled ruleset missing and external ruleset use must be explicitly enabled (e.g. semgrep_config='auto')."

    override = str(semgrep_config).strip()
    if override.lower() in ("bundled", "local", "baseline", "public_sector_baseline"):
        if bundled_rules.is_file():
            return str(bundled_rules.resolve()), None
        return None, f"Configured semgrep_config '{override}' requested but bundled ruleset is missing."
    if not override:
        if bundled_rules.is_file():
            return str(bundled_rules.resolve()), None
        return None, "Bundled ruleset missing and external ruleset use must be explicitly enabled."
        
    if override.lower() == "auto":
        if is_offline:
            if bundled_rules.is_file():
                return str(bundled_rules.resolve()), None
            return None, "auto ruleset requested but COMPLIANCE_OFFLINE is set and bundled ruleset is missing."
        return "auto", None

    if override.startswith("http://"):
        return None, f"Refusing cleartext HTTP ruleset URL '{override}'"


    # Registry references (e.g. 'p/ci', 'r/python.lang...') and remote URLs
    # are passed through untouched to Semgrep unless a matching local path
    # actually exists on disk. Filesystem paths must exist before scanning.
    is_registry_or_url = (
        override.startswith(("p/", "r/", "https://", "http://"))
        and not os.path.exists(override)
    )
    if not is_registry_or_url:
        looks_like_path = (
            os.sep in override
            or override.startswith((".", "~"))
            or override.endswith((".yaml", ".yml", ".json"))
            or os.path.exists(override)
        )
        if looks_like_path:
            candidate = Path(override).expanduser()
            if not candidate.exists():
                return None, f"Configured semgrep_config path does not exist: {override}"
            return str(candidate.resolve()), None

    return override, None


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

    config_ref, config_error = _resolve_semgrep_config(semgrep_config)
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
        if (
            isinstance(data, list)
            and data
            and "check_id" in data[0]
            and str(data[0]["check_id"]).startswith("SEMGREP_SCANNER_")
            and config_ref.lower() == "auto"
        ):
            bundled_rules = SEMGREP_RULES_DIR / "public_sector_baseline.yaml"
            if bundled_rules.is_file():
                logger.info(
                    "Semgrep scan with --config auto failed; falling back to bundled baseline ruleset at %s",
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


    results = data.get("results", [])
    findings: List[Dict[str, Any]] = []

    for item in results:
        check_id = item.get("check_id", "semgrep.finding")
        extra = item.get("extra", {})
        message = extra.get("message", "Application security concern detected.")
        metadata = extra.get("metadata", {})
        cwe = metadata.get("cwe", ["CWE-General"])
        cwe_str = cwe[0] if isinstance(cwe, list) and cwe else str(cwe)
        severity = str(extra.get("severity", "WARNING")).capitalize()
        if severity.upper() == "WARNING":
            severity = "Moderate"
        elif severity.upper() in ["ERROR", "CRITICAL"]:
            severity = "High"
        elif severity.upper() == "INFO":
            severity = "Low"

        path = item.get("path", "unknown")
        start_l = item.get("start", {}).get("line", 1)
        end_l = item.get("end", {}).get("line", start_l)
        loc_str = f"{path}:L{start_l}-{end_l}"

        findings.append({
            "source": "Semgrep Application SAST Scanner",
            "check_id": check_id,
            "cwe": cwe_str,
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
    if impact_level and any(il in str(impact_level).upper() for il in ("IL4", "IL5", "IL6", "DOD_IL4", "DOD_IL5", "DOD_IL6")):
        logger.info("DoD Impact Level %s detected: Skipping unaccredited commercial SCC telemetry calls", impact_level)
        return []

    if not project_id or "[CONFIG_REQUIRED" in str(project_id):
        return []

    findings: List[Dict[str, Any]] = []
    if runner or shutil.which("gcloud"):
        
        if str(project_id).startswith("-"):
            return []
        cmd = [
            "gcloud", "scc", "findings", "list",
            "--project", project_id,
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
        dirs[:] = [d for d in dirs if d not in ignored]
        for f in files:
            if f.endswith((".sarif", ".sarif.json")):
                fpath = os.path.join(root, f)
                findings.extend(parse_sarif_file(fpath, allowed_boundary=target_dir))
    return findings


def scan_and_derive_poam_items(
    target_dir: str,
    sys_abbr: str = "SYS",
    eff_date: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """Executes available scanners and maps findings to NIST SP 800-53 Rev. 5 POA&M items.

    Args:
        target_dir: Filesystem path to the root workspace.
        sys_abbr: System abbreviation for POA&M identifier formatting.
        eff_date: Effective date string for milestone scheduling.
        config: Optional dictionary of scanner configurations and report paths.

    Returns:
        List of canonical POA&M finding dictionaries.
    """
    if not eff_date:
        eff_date = datetime.now().strftime("%Y-%m-%d")
    try:
        base_dt = datetime.strptime(eff_date, "%Y-%m-%d")
    except (ValueError, TypeError):
        base_dt = datetime.now()

    cfg = config or {}
    include_scanner_failures = bool(cfg.get("include_scanner_failures_in_poam", False))
    run_checkov = cfg.get("run_checkov", True)
    run_semgrep = cfg.get("run_semgrep", True)
    if os.getenv("COMPLIANCE_DISABLE_LIVE_SCANNERS") == "1":
        if "run_checkov" not in cfg:
            run_checkov = False
        if "run_semgrep" not in cfg:
            run_semgrep = False
    run_sarif = cfg.get("ingest_sarif", True)
    explicit_sarifs = cfg.get("sarif_reports", [])

    poam_items = []
    item_counter = 100  # Start scanner findings at 100 to avoid ID collision

    checkov_timeout = int(cfg.get("checkov_timeout", 300))
    semgrep_timeout = int(cfg.get("semgrep_timeout", 300))
    semgrep_config = cfg.get("semgrep_config") or None

    # 1. Run Checkov IaC Scanner
    if run_checkov:
        checkov_findings = _cached_scan(
            "checkov",
            str(Path(target_dir).resolve()),
            (checkov_timeout,),
            lambda: run_checkov_scan(target_dir, timeout_seconds=checkov_timeout),
        )
        grouped_checkov = collections.defaultdict(list)
        for f in checkov_findings:
            ck = f.get("check_id") or f.get("check_name") or "CHECK_UNKNOWN"
            grouped_checkov[ck].append(f)

        for check_id, group in grouped_checkov.items():
            f0 = group[0]
            check_name = f0.get("check_name") or check_id
            guideline = f0.get("guideline") or check_name
            source = f0.get("source") or "Checkov IaC Static Security Scanner"

            # Highest severity
            best_sev = "Low"
            best_weight = -1
            for f in group:
                s = f.get("severity", "Low")
                w = SEVERITY_ORDER.get(str(s).upper(), 1)
                if w > best_weight:
                    best_weight = w
                    best_sev = s

            aps, control_title = map_checkov_to_nist(check_id, check_name)
            sched_days = 30 if best_sev in ("High", "Very High") else 60 if best_sev in ("Moderate", "Medium") else 90
            target_date = (base_dt + timedelta(days=sched_days)).strftime("%Y-%m-%d")

            # Collect unique occurrences
            seen_locs = set()
            occurrences = []
            for f in group:
                res = f.get("resource") or ""
                loc = f.get("location") or ""
                loc_key = (res, loc)
                if loc_key not in seen_locs:
                    seen_locs.add(loc_key)
                    occurrences.append((res, loc))

            total_count = len(occurrences)
            if is_scanner_failure_check_id(check_id):
                if not include_scanner_failures:
                    logger.warning(
                        "Scanner outage detected for %s (%s); omitting from POA&M (only true security issues are tracked in POA&M).",
                        source,
                        check_id,
                    )
                    continue
                # Coverage gap, not an infrastructure defect. See the equivalent
                # branch in the Semgrep section below.
                scanner_label = source or "Infrastructure-as-Code scanner"
                diagnostic = _summarize_scanner_diagnostic(check_name)
                short_title = (
                    f"{scanner_label} did not complete; Terraform infrastructure was not assessed."
                )
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
                bullet_lines = []
                max_display = 25
                for res, loc in occurrences[:max_display]:
                    if res and loc:
                        bullet_lines.append(f"  - {res} ({loc})")
                    elif res:
                        bullet_lines.append(f"  - {res}")
                    elif loc:
                        bullet_lines.append(f"  - {loc}")
                if total_count > max_display:
                    bullet_lines.append(f"  - ... and {total_count - max_display} additional affected locations.")
                desc = f"[{check_id}] {check_name} across {total_count} affected locations:\n" + "\n".join(bullet_lines)
                m_desc = f"Remediate {total_count} affected resources in Terraform ({guideline}). Verify configuration across all affected modules."

            poam_items.append({
                "control": control_title,
                "item_id": f"POAM-{sys_abbr}-{item_counter:03d}",
                "title": short_title,
                "desc": desc,
                "aps": aps,
                "checks": check_id,
                "status": "Ongoing",
                "sched_date": target_date,
                "milestone_id": f"M-{item_counter:03d}-1",
                "milestone_desc": m_desc,
                "milestone_status": "Open",
                "source": source,
                "severity": best_sev,
                "threat": "Moderate" if best_sev in ("High", "Very High") else "Low",
                "likelihood": "Moderate" if best_sev in ("High", "Very High") else "Low",
                "impact": "High" if best_sev in ("High", "Very High") else "Moderate",
                "residual": "Low",
            })
            item_counter += 1

    # 2. Run Semgrep SAST Scanner
    if run_semgrep:
        semgrep_findings = _cached_scan(
            "semgrep",
            str(Path(target_dir).resolve()),
            (semgrep_timeout, semgrep_config or ""),
            lambda: run_semgrep_scan(
                target_dir,
                timeout_seconds=semgrep_timeout,
                semgrep_config=semgrep_config,
            ),
        )
        grouped_semgrep = collections.defaultdict(list)
        for sf in semgrep_findings:
            ck = sf.get("check_id") or "SEMGREP_FINDING"
            grouped_semgrep[ck].append(sf)

        for check_id, group in grouped_semgrep.items():
            sf0 = group[0]
            msg = sf0.get("message") or check_id
            cwe = sf0.get("cwe") or ""
            source = sf0.get("source") or "Semgrep SAST Code Scanner"

            best_sev = "Low"
            best_weight = -1
            for sf in group:
                s = sf.get("severity", "Low")
                w = SEVERITY_ORDER.get(str(s).upper(), 1)
                if w > best_weight:
                    best_weight = w
                    best_sev = s

            aps, control_title = map_cwe_to_nist(cwe)
            sched_days = 30 if best_sev in ("High", "Very High") else 60
            target_date = (base_dt + timedelta(days=sched_days)).strftime("%Y-%m-%d")

            seen_locs = set()
            occurrences = []
            for sf in group:
                loc = sf.get("location") or ""
                if loc and loc not in seen_locs:
                    seen_locs.add(loc)
                    occurrences.append(loc)

            total_count = len(occurrences)
            if is_scanner_failure_check_id(check_id):
                if not include_scanner_failures:
                    logger.warning(
                        "Scanner outage detected for %s (%s); omitting from POA&M (only true security issues are tracked in POA&M).",
                        source,
                        check_id,
                    )
                    continue
                # A scanner outage is a gap in assessment coverage, not a defect
                # in the assessed code. Emitting it as a code vulnerability puts
                # raw tool stderr into an accreditation deliverable and pairs it
                # with a remediation that cannot be performed.
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
                bullet_lines = []
                max_display = 25
                for loc in occurrences[:max_display]:
                    bullet_lines.append(f"  - {loc}")
                if total_count > max_display:
                    bullet_lines.append(f"  - ... and {total_count - max_display} additional affected locations.")
                desc = f"[{check_id}] {msg} across {total_count} affected locations:\n" + "\n".join(bullet_lines)
                m_desc = f"Sanitize and refactor code across {total_count} affected locations to eliminate vulnerability."

            poam_items.append({
                "control": control_title,
                "item_id": f"POAM-{sys_abbr}-{item_counter:03d}",
                "title": short_title,
                "desc": desc,
                "aps": aps,
                "checks": check_id,
                "status": "Ongoing",
                "sched_date": target_date,
                "milestone_id": f"M-{item_counter:03d}-1",
                "milestone_desc": m_desc,
                "milestone_status": "Open",
                "source": source,
                "severity": best_sev,
                "threat": "Moderate" if best_sev in ("High", "Very High") else "Low",
                "likelihood": "Moderate" if best_sev in ("High", "Very High") else "Low",
                "impact": "High" if best_sev in ("High", "Very High") else "Moderate",
                "residual": "Low",
            })
            item_counter += 1

    # 3. Run Trivy Vulnerability Scanner (Optional / Dynamic Bootstrap)
    run_trivy = cfg.get("run_trivy", False)
    enable_bootstrap = cfg.get("enable_scanner_bootstrap", False)
    if run_trivy:
        trivy_timeout = int(cfg.get("trivy_timeout", 300))
        trivy_findings = run_trivy_scan(target_dir, timeout_seconds=trivy_timeout, enable_bootstrap=enable_bootstrap)
        grouped_trivy = collections.defaultdict(list)
        for tf in trivy_findings:
            ck = tf.get("check_id") or "TRIVY_CVE"
            grouped_trivy[ck].append(tf)

        for check_id, group in grouped_trivy.items():
            tf0 = group[0]
            msg = tf0.get("message") or tf0.get("title") or check_id
            cwe = tf0.get("cwe", "SI-02")
            source = tf0.get("source") or "Trivy Container & Dependency Scanner"

            if is_scanner_failure_check_id(check_id):
                if not include_scanner_failures:
                    logger.warning(
                        "Scanner outage detected for %s (%s); omitting from POA&M (only true security issues are tracked in POA&M).",
                        source,
                        check_id,
                    )
                    continue

            best_sev = "Low"
            best_weight = -1
            for tf in group:
                s = tf.get("severity", "Low")
                w = SEVERITY_ORDER.get(str(s).upper(), 1)
                if w > best_weight:
                    best_weight = w
                    best_sev = s

            aps, control_title = map_cwe_to_nist(cwe)
            sched_days = 30 if best_sev in ("High", "Very High") else 60
            target_date = (base_dt + timedelta(days=sched_days)).strftime("%Y-%m-%d")

            seen_locs = set()
            occurrences = []
            for tf in group:
                tgt = tf.get("target") or tf.get("resource") or ""
                loc = tf.get("location") or ""
                key = (tgt, loc)
                if key not in seen_locs:
                    seen_locs.add(key)
                    occurrences.append((tgt, loc))

            total_count = len(occurrences)
            if total_count <= 1:
                tgt, loc = occurrences[0] if occurrences else ("", "")
                loc_info = f" ({loc})" if loc else f" on {tgt}" if tgt else ""
                desc = f"[{check_id}] {msg}{loc_info}."
                short_title = desc
                m_desc = f"Upgrade and patch vulnerable package or fix configuration at {loc or tgt or 'affected target'}."
            else:
                short_title = f"[{check_id}] {msg} ({total_count} affected targets)"
                bullet_lines = []
                max_display = 25
                for tgt, loc in occurrences[:max_display]:
                    if tgt and loc:
                        bullet_lines.append(f"  - {tgt} ({loc})")
                    elif tgt:
                        bullet_lines.append(f"  - {tgt}")
                    elif loc:
                        bullet_lines.append(f"  - {loc}")
                if total_count > max_display:
                    bullet_lines.append(f"  - ... and {total_count - max_display} additional affected targets.")
                desc = f"[{check_id}] {msg} across {total_count} affected targets:\n" + "\n".join(bullet_lines)
                m_desc = f"Upgrade and patch vulnerable packages across {total_count} affected targets."

            poam_items.append({
                "control": control_title,
                "item_id": f"POAM-{sys_abbr}-{item_counter:03d}",
                "title": short_title,
                "desc": desc,
                "aps": aps,
                "checks": check_id,
                "status": "Ongoing",
                "sched_date": target_date,
                "milestone_id": f"M-{item_counter:03d}-1",
                "milestone_desc": m_desc,
                "milestone_status": "Open",
                "source": source,
                "severity": best_sev,
                "threat": "Moderate" if best_sev in ("High", "Very High") else "Low",
                "likelihood": "Moderate" if best_sev in ("High", "Very High") else "Low",
                "impact": "High" if best_sev in ("High", "Very High") else "Moderate",
                "residual": "Low",
            })
            item_counter += 1

    # 4. Ingest Live Cloud Posture Telemetry (Google Security Command Center)
    query_live = cfg.get("query_live_cloud_telemetry", False)
    if query_live:
        impact_level = str(
            cfg.get("impact_level")
            or cfg.get("baseline")
            or cfg.get("system_information", {}).get("impact_level")
            or cfg.get("system_information", {}).get("baseline")
            or os.environ.get("IMPACT_LEVEL", "")
        ).upper()
        if any(il in impact_level for il in ("IL4", "IL5", "IL6", "DOD_IL4", "DOD_IL5", "DOD_IL6")):
            logger.info("DoD Impact Level %s detected: Skipping unaccredited commercial cloud telemetry calls", impact_level)
            live_scc = []
        else:
            project_id = cfg.get("project_id") or os.environ.get("GOOGLE_CLOUD_PROJECT")
            live_scc = fetch_live_scc_findings(project_id=project_id, impact_level=impact_level)
        grouped_scc = collections.defaultdict(list)
        for sf in live_scc:
            ck = sf.get("check_id") or sf.get("check_name") or "SCC_FINDING"
            grouped_scc[ck].append(sf)

        for check_id, group in grouped_scc.items():
            sf0 = group[0]
            check_name = sf0.get("check_name") or check_id
            guideline = sf0.get("guideline") or check_name
            source = sf0.get("source") or "Live Cloud Telemetry (Google SCC v1)"

            best_sev = "Low"
            best_weight = -1
            for sf in group:
                s = sf.get("severity", "Low")
                w = SEVERITY_ORDER.get(str(s).upper(), 1)
                if w > best_weight:
                    best_weight = w
                    best_sev = s

            aps, control_title = map_checkov_to_nist(check_id, check_name)
            sched_days = 30 if best_sev in ("High", "Very High") else 60
            target_date = (base_dt + timedelta(days=sched_days)).strftime("%Y-%m-%d")

            seen_locs = set()
            occurrences = []
            for sf in group:
                res = sf.get("resource") or ""
                loc = sf.get("location") or ""
                key = (res, loc)
                if key not in seen_locs:
                    seen_locs.add(key)
                    occurrences.append((res, loc))

            total_count = len(occurrences)
            if total_count <= 1:
                res, loc = occurrences[0] if occurrences else ("", "")
                loc_str = f" ({loc})" if loc else ""
                desc = f"[{check_id}] {check_name} on {res}{loc_str}."
                short_title = desc
                m_desc = f"Remediate live cloud finding in {loc or res}: {guideline}"
            else:
                short_title = f"[{check_id}] {check_name} ({total_count} affected resources)"
                bullet_lines = []
                max_display = 25
                for res, loc in occurrences[:max_display]:
                    if res and loc:
                        bullet_lines.append(f"  - {res} ({loc})")
                    elif res:
                        bullet_lines.append(f"  - {res}")
                    elif loc:
                        bullet_lines.append(f"  - {loc}")
                if total_count > max_display:
                    bullet_lines.append(f"  - ... and {total_count - max_display} additional affected resources.")
                desc = f"[{check_id}] {check_name} across {total_count} affected cloud resources:\n" + "\n".join(bullet_lines)
                m_desc = f"Remediate {total_count} affected cloud resources in cloud console / IaC: {guideline}"

            poam_items.append({
                "control": control_title,
                "item_id": f"POAM-{sys_abbr}-{item_counter:03d}",
                "title": short_title,
                "desc": desc,
                "aps": aps,
                "checks": check_id,
                "status": "Ongoing",
                "sched_date": target_date,
                "milestone_id": f"M-{item_counter:03d}-1",
                "milestone_desc": m_desc,
                "milestone_status": "Open",
                "source": source,
                "severity": best_sev,
                "threat": "Moderate" if best_sev in ("High", "Very High") else "Low",
                "likelihood": "Moderate" if best_sev in ("High", "Very High") else "Low",
                "impact": "High" if best_sev in ("High", "Very High") else "Moderate",
                "residual": "Low",
            })
            item_counter += 1

    # 5. Ingest SARIF Reports
    sarif_findings = []
    if run_sarif:
        sarif_findings.extend(ingest_sarif_files(target_dir))
    if explicit_sarifs:
        for p in explicit_sarifs:
            abs_p = p if os.path.isabs(p) else os.path.join(target_dir, p)
            if os.path.isfile(abs_p):
                sarif_findings.extend(parse_sarif_file(abs_p, allowed_boundary=target_dir))

    grouped_sarif = collections.defaultdict(list)
    for sar in sarif_findings:
        ck = sar.get("check_id") or "SARIF_FINDING"
        grouped_sarif[ck].append(sar)

    for rule_id, group in grouped_sarif.items():
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

        best_sev = "Low"
        best_weight = -1
        for sar in group:
            s = sar.get("severity", "Low")
            w = SEVERITY_ORDER.get(str(s).upper(), 1)
            if w > best_weight:
                best_weight = w
                best_sev = s

        sched_days = 30 if best_sev in ("High", "Very High") else 60
        target_date = (base_dt + timedelta(days=sched_days)).strftime("%Y-%m-%d")

        seen_locs = set()
        occurrences = []
        for sar in group:
            loc = sar.get("location") or ""
            if loc and loc not in seen_locs:
                seen_locs.add(loc)
                occurrences.append(loc)

        total_count = len(occurrences)
        if total_count <= 1:
            loc = occurrences[0] if occurrences else "codebase"
            desc = f"[{rule_id}] {msg} ({loc})."
            short_title = desc
            m_desc = f"Address finding from {source} at {loc}."
        else:
            short_title = f"[{rule_id}] {msg} ({total_count} affected locations)"
            bullet_lines = []
            max_display = 25
            for loc in occurrences[:max_display]:
                bullet_lines.append(f"  - {loc}")
            if total_count > max_display:
                bullet_lines.append(f"  - ... and {total_count - max_display} additional affected locations.")
            desc = f"[{rule_id}] {msg} across {total_count} affected locations:\n" + "\n".join(bullet_lines)
            m_desc = f"Address finding from {source} across {total_count} affected locations."

        poam_items.append({
            "control": control_title,
            "item_id": f"POAM-{sys_abbr}-{item_counter:03d}",
            "title": short_title,
            "desc": desc,
            "aps": aps,
            "checks": rule_id,
            "status": "Ongoing",
            "sched_date": target_date,
            "milestone_id": f"M-{item_counter:03d}-1",
            "milestone_desc": m_desc,
            "milestone_status": "Open",
            "source": source,
            "severity": best_sev,
            "threat": "Low",
            "likelihood": "Low",
            "impact": "Moderate",
            "residual": "Low"
        })
        item_counter += 1

    return scrub_sensitive_data(poam_items)
