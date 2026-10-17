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

"""Structured audit logging for the compliance engine (NIST SP 800-53 AU family).

Human-readable ``logger.info`` output is useful for operators but is not evidence.
An RMF/FedRAMP assessor needs machine-parseable records that answer *who did what,
to which resource, when, and with what outcome*. This module writes those records
as newline-delimited JSON:

* **AU-2 (Event Logging)** - a fixed, enumerated set of security-relevant event types.
* **AU-3 (Content of Audit Records)** - every record carries timestamp, event type,
  outcome, subject, object, and source component.
* **AU-3(1) (Additional Audit Information)** - arbitrary structured detail fields.
* **AU-8 (Time Stamps)** - RFC 3339 timestamps in UTC with explicit offset.
* **AU-9 (Protection of Audit Information)** - the sink is created owner-only (file
  0600, directory 0700) and written with ``O_APPEND``. Every record carries a
  sequence number and a SHA-256 digest chained to its predecessor, so editing,
  reordering, or deleting a record before the last one fails
  :meth:`AuditLogger.verify_chain`.

Limits of the chain:

* The digest is unkeyed. Anyone who can write the file can rewrite it and recompute
  the whole chain, and deleting records from the end leaves a valid chain. Forward
  the trail to a write-once store when AU-9 requires more than tamper evidence.
* It does not provide non-repudiation (AU-10), which requires signatures bound to
  an identity.

Design constraints:

* Sensitive values are redacted through the shared scrubber before serialization, so
  the audit trail can never become the leak vector.
* Emission never raises into the caller. A compliance run must not abort because the
  audit sink is unavailable; instead the failure is surfaced on the standard logger
  and tracked in :attr:`AuditLogger.dropped_records`.
* SHA-256 is a FIPS 180-4 hash function. Whether the hashlib/OpenSSL build in use is
  a FIPS 140-3 validated module depends on the host. The digest is an integrity
  witness only: it is not a keyed MAC and is not a secret.
"""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import hmac
import json
import logging
import os
from pathlib import Path
import threading
import time
from typing import Any, Dict, Final, Iterator, Optional, Union
import uuid

from .file_helpers import ensure_path_within_boundary, scrub_sensitive_data

logger = logging.getLogger(__name__)

__all__ = [
    "AuditEvent",
    "AuditLogger",
    "AuditOutcome",
    "audit_operation",
    "configure_audit_log",
    "get_audit_logger",
    "reset_audit_log",
]

#: Schema version, bumped when the record shape changes in a breaking way.
AUDIT_SCHEMA_VERSION: Final[str] = "1.0"

#: Owner read/write only. Audit evidence must not be world-readable (AU-9).
_AUDIT_FILE_MODE: Final[int] = 0o600
_AUDIT_DIR_MODE: Final[int] = 0o700

#: Upper bound on a single serialized record, preventing a pathological payload
#: from bloating the audit trail (AU-5 considerations).
_MAX_RECORD_BYTES: Final[int] = 64 * 1024


class AuditEvent:
    """Enumerated, security-relevant event types (AU-2).

    Using a closed enumeration rather than free-text strings keeps the audit trail
    queryable and prevents typo-driven gaps in assessor evidence.
    """

    ARTIFACT_GENERATED: Final[str] = "artifact.generated"
    ARTIFACT_VALIDATED: Final[str] = "artifact.validated"
    CONFIG_LOADED: Final[str] = "config.loaded"
    EXTERNAL_COMMAND: Final[str] = "external.command"
    INVENTORY_EXTRACTED: Final[str] = "inventory.extracted"
    PIPELINE_COMPLETED: Final[str] = "pipeline.completed"
    PIPELINE_STARTED: Final[str] = "pipeline.started"
    SECURITY_VIOLATION: Final[str] = "security.violation"
    SENSITIVE_DATA_REDACTED: Final[str] = "security.redaction"


class AuditOutcome:
    """Terminal outcome values recorded for every audited operation (AU-3)."""

    SUCCESS: Final[str] = "success"
    FAILURE: Final[str] = "failure"
    DENIED: Final[str] = "denied"


def _utc_timestamp() -> str:
    """Returns the current time as an RFC 3339 UTC timestamp (AU-8).

    Returns:
        Timestamp string such as ``2026-09-11T01:23:45.678901+00:00``.
    """
    return datetime.now(timezone.utc).isoformat()


def _clip_strings(value: Any, depth: int = 0) -> Any:
    """Clips strings longer than one audit record before they reach the secret scrubber.

    A record above _MAX_RECORD_BYTES is truncated on write anyway, so scanning the
    excess only costs time.
    """
    if isinstance(value, str):
        return value if len(value) <= _MAX_RECORD_BYTES else value[:_MAX_RECORD_BYTES] + "...[truncated]"
    if depth > 32:
        return value
    if isinstance(value, dict):
        return {k: _clip_strings(v, depth + 1) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_clip_strings(v, depth + 1) for v in value]
    return value


def _sanitize_audit_paths(
    value: Any,
    base_dir: Optional[Path] = None,
    depth: int = 0,
) -> Any:
    """Relativizes target paths and replaces the operator home directory with ``~``."""
    if depth > 32:
        return value
    if isinstance(value, str):
        text = value
        if base_dir is not None:
            base_str = str(base_dir).rstrip("/")
            if len(base_str) > 1:
                if text == base_str or text == base_str + "/":
                    text = "."
                else:
                    text = text.replace(base_str + "/", "").replace(base_str, ".")
        try:
            home_str = str(Path.home()).rstrip("/")
        except (RuntimeError, OSError):
            home_str = ""
        if len(home_str) > 1 and home_str in text:
            text = text.replace(home_str, "~")
        return text
    if isinstance(value, dict):
        return {k: _sanitize_audit_paths(v, base_dir, depth + 1) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_sanitize_audit_paths(v, base_dir, depth + 1) for v in value]
    return value


def _normalize_detail(
    detail: Optional[Dict[str, Any]],
    base_dir: Optional[Path] = None,
) -> Any:
    """Redacts ``detail`` and converts it to plain JSON types.

    Redaction happens before the record is ever serialized, so the audit trail
    cannot become an exfiltration channel for credentials. The JSON round-trip then
    turns every dict key into a string: the chain digest serializes with
    ``sort_keys=True``, which raises ``TypeError`` on mixed key types such as
    ``{1: "a", "b": 2}``.

    Args:
        detail: Caller-supplied structured context, or None.
        base_dir: Optional target boundary used to relativize absolute paths.

    Returns:
        The redacted detail in JSON types, or a marker naming the error when the
        detail cannot be serialized at all (for example a tuple used as a key).
    """
    scrubbed = scrub_sensitive_data(_clip_strings(detail or {}))
    sanitized = _sanitize_audit_paths(scrubbed, base_dir=base_dir)
    try:
        return json.loads(json.dumps(sanitized, default=str))
    except (TypeError, ValueError) as err:
        logger.warning("Audit record detail could not be serialized and was replaced: %s", err)
        return {"unserializable_detail": type(err).__name__}


class AuditLogger:
    """Thread-safe, append-only JSON-lines audit sink with chained integrity digests.

    The logger is safe to construct without a sink path: records are then emitted only
    to the standard Python logger at DEBUG level, which keeps unit tests and read-only
    invocations free of filesystem side effects.
    """

    def __init__(
        self,
        sink_path: Optional[Union[str, Path]] = None,
        component: str = "compliance-engine",
        allowed_boundary: Optional[Union[str, Path]] = None,
        hmac_key: Optional[str] = None,
    ) -> None:
        """Initializes the audit logger.

        Args:
            sink_path: Optional path of the ``.jsonl`` audit trail. When None, records
                are not persisted to disk.
            component: Name of the emitting component, recorded on every event.
            allowed_boundary: Optional directory that ``sink_path`` must resolve inside,
                preventing an operator-supplied path from escaping the workspace.
            hmac_key: Optional HMAC-SHA256 key (defaults to
                ``COMPLIANCE_AUDIT_HMAC_KEY`` environment variable when set) to
                authenticate chain digests against pre-seeded tampering.

        Raises:
            PermissionError: If ``sink_path`` escapes ``allowed_boundary``.
        """
        self._lock = threading.Lock()
        self._sequence = 0
        self._previous_digest = "0" * 64
        self._session_id = str(uuid.uuid4())
        self.component = component
        self.dropped_records = 0
        self._sink_path: Optional[Path] = None
        self._boundary_root: Optional[Path] = (
            Path(allowed_boundary).resolve() if allowed_boundary is not None else None
        )
        env_key = os.environ.get("COMPLIANCE_AUDIT_HMAC_KEY", "").strip()
        self._hmac_key: Optional[str] = hmac_key if hmac_key is not None else (env_key or None)

        if sink_path is not None:
            supplied = Path(sink_path)
            if allowed_boundary is not None:
                # Check the path as supplied: resolve() would replace a symlinked
                # directory inside the boundary with its target before the check.
                resolved = ensure_path_within_boundary(supplied, allowed_boundary)
            else:
                resolved = supplied.resolve()
            self._sink_path = resolved
            if self._boundary_root is None:
                self._boundary_root = (
                    resolved.parent.parent
                    if resolved.parent.name == "ato_artifacts"
                    else resolved.parent
                )
            self._resume_chain_if_present()

    def _resume_chain_if_present(self) -> None:
        """Resumes sequence and digest tracking from an existing audit trail on disk.

        If the sink path exists and contains prior records, verifies that the existing
        chain is intact (including HMAC verification when ``COMPLIANCE_AUDIT_HMAC_KEY``
        is configured) and reads the last valid record to initialize ``_sequence`` and
        ``_previous_digest``. This prevents breaking the hash chain across invocations
        while refusing to chain onto tampered or unauthenticated records (NIST AU-9,
        tampering).
        """
        if self._sink_path is None or not self._sink_path.is_file():
            return
        if not self.verify_chain():
            logger.warning(
                "Existing audit log '%s' failed integrity verification; refusing to resume chain",
                self._sink_path,
            )
            return
        try:
            last_line: Optional[str] = None
            with self._sink_path.open("r", encoding="utf-8") as handle:
                for line in handle:
                    stripped = line.strip()
                    if stripped:
                        last_line = stripped
            if last_line:
                record = json.loads(last_line)
                if not isinstance(record, dict):
                    logger.warning("Last audit record in '%s' is not a JSON object; starting a new chain", self._sink_path)
                    return
                seq = record.get("sequence")
                digest = record.get("digest")
                if isinstance(seq, int) and isinstance(digest, str) and len(digest) == 64:
                    self._sequence = seq
                    self._previous_digest = digest
        except (OSError, json.JSONDecodeError, UnicodeDecodeError) as err:
            logger.warning("Could not inspect existing audit log to resume chain: %s", err)

    @property
    def sink_path(self) -> Optional[Path]:
        """Returns the resolved audit trail path, or None when persistence is disabled."""
        return self._sink_path

    @property
    def session_id(self) -> str:
        """Returns the unique identifier correlating all records from this process run."""
        return self._session_id

    def _build_record(
        self,
        event_type: str,
        outcome: str,
        subject: str,
        obj: Optional[str],
        detail: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Assembles a fully populated, redacted audit record.

        Args:
            event_type: One of the :class:`AuditEvent` constants.
            outcome: One of the :class:`AuditOutcome` constants.
            subject: The actor performing the operation.
            obj: The resource acted upon, if any.
            detail: Optional structured context.

        Returns:
            The complete audit record, ready for serialization.
        """
        # Normalize first: nothing below may raise after the sequence number is taken,
        # or the next record would leave a gap that verify_chain() reports as tampering.
        if (
            self._boundary_root is None
            and isinstance(detail, dict)
            and isinstance(detail.get("target_dir"), (str, Path))
            and os.path.isabs(str(detail["target_dir"]))
        ):
            self._boundary_root = Path(detail["target_dir"]).resolve()
        normalized_detail = _normalize_detail(detail, base_dir=self._boundary_root)
        normalized_obj = (
            _sanitize_audit_paths(str(obj), base_dir=self._boundary_root)
            if obj is not None
            else None
        )
        sequence = self._sequence + 1
        record: Dict[str, Any] = {
            "schema_version": AUDIT_SCHEMA_VERSION,
            "timestamp": _utc_timestamp(),
            "sequence": sequence,
            "session_id": self._session_id,
            "component": self.component,
            "event_type": event_type,
            "outcome": outcome,
            "subject": subject,
            "object": normalized_obj,
            "detail": normalized_detail,
            "previous_digest": self._previous_digest,
        }
        record["digest"] = self._chain_digest(record)
        self._sequence = sequence
        self._previous_digest = record["digest"]
        return record

    def _chain_digest(self, record: Dict[str, Any]) -> str:
        """Computes the SHA-256 or HMAC-SHA256 chain digest binding a record to its predecessor.

        Args:
            record: Record contents excluding the ``digest`` field.

        Returns:
            Lowercase hexadecimal SHA-256 / HMAC-SHA256 digest.
        """
        canonical = json.dumps(record, sort_keys=True, separators=(",", ":"), default=str)
        payload = canonical.encode("utf-8")
        if self._hmac_key:
            return hmac.new(self._hmac_key.encode("utf-8"), payload, hashlib.sha256).hexdigest()
        return hashlib.sha256(payload).hexdigest()

    def emit(
        self,
        event_type: str,
        outcome: str = AuditOutcome.SUCCESS,
        subject: str = "compliance-engine",
        obj: Optional[str] = None,
        detail: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Records a single audit event.

        This method never propagates an exception to the caller: an unavailable audit
        sink degrades to standard-logger reporting rather than aborting a compliance run.

        Args:
            event_type: One of the :class:`AuditEvent` constants.
            outcome: One of the :class:`AuditOutcome` constants.
            subject: The actor performing the operation.
            obj: The resource acted upon, if any.
            detail: Optional structured context; sensitive values are redacted.

        Returns:
            The emitted audit record.
        """
        with self._lock:
            record = self._build_record(event_type, outcome, subject, obj, detail)
            serialized = json.dumps(record, sort_keys=True, default=str)

            if len(serialized) > _MAX_RECORD_BYTES:
                truncated = dict(record)
                truncated["detail"] = {
                    "truncated": True,
                    "original_detail_bytes": len(serialized),
                }
                truncated["digest"] = self._chain_digest(
                    {k: v for k, v in truncated.items() if k != "digest"}
                )
                self._previous_digest = truncated["digest"]
                record = truncated
                serialized = json.dumps(record, sort_keys=True, default=str)

            logger.debug("AUDIT %s", serialized)

            if self._sink_path is None:
                return record

            try:
                self._append(serialized)
            except OSError as err:
                self.dropped_records += 1
                logger.error(
                    "Audit record could not be persisted to '%s' (dropped=%d): %s",
                    self._sink_path,
                    self.dropped_records,
                    err,
                )
            return record

    def _append(self, serialized: str) -> None:
        """Appends one serialized record to the sink with owner-only permissions.

        The file is opened with ``O_APPEND`` and ``O_NOFOLLOW`` so that a symlink
        planted at the sink path cannot redirect audit evidence elsewhere, and so
        concurrent writers cannot interleave partial lines.

        Args:
            serialized: The JSON-serialized record, without a trailing newline.

        Raises:
            OSError: If the sink cannot be opened or written.
        """
        assert self._sink_path is not None  # guarded by the caller
        parent = self._sink_path.parent
        parent.mkdir(parents=True, exist_ok=True, mode=_AUDIT_DIR_MODE)

        flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND
        # O_NOFOLLOW is POSIX-only; on platforms lacking it the boundary check plus
        # owner-only mode remain in force.
        flags |= getattr(os, "O_NOFOLLOW", 0)
        fd = os.open(self._sink_path, flags, _AUDIT_FILE_MODE)
        try:
            os.write(fd, (serialized + "\n").encode("utf-8"))
        finally:
            os.close(fd)

    def verify_chain(self) -> bool:
        """Re-computes the digest chain over the persisted trail to detect tampering.

        Records removed from the end of the trail, and a trail rewritten with a
        recomputed chain, are not detected (the digest is unkeyed).

        Returns:
            True when the trail is absent, empty, or internally consistent; False when
            a record has been altered, reordered, or removed before the last record.
        """
        if self._sink_path is None or not self._sink_path.is_file():
            return True

        expected_previous = "0" * 64
        expected_sequence = 0
        try:
            with self._sink_path.open("r", encoding="utf-8") as handle:
                for line_number, line in enumerate(handle, start=1):
                    line = line.strip()
                    if not line:
                        continue
                    record = json.loads(line)
                    if not isinstance(record, dict):
                        logger.error("Audit chain break at line %d: record is not a JSON object", line_number)
                        return False
                    expected_sequence += 1
                    if record.get("sequence") != expected_sequence:
                        logger.error(
                            "Audit chain break at line %d: expected sequence %d, found %r",
                            line_number,
                            expected_sequence,
                            record.get("sequence"),
                        )
                        return False
                    if record.get("previous_digest") != expected_previous:
                        logger.error("Audit chain break at line %d: predecessor mismatch", line_number)
                        return False
                    stored_digest = record.pop("digest", None)
                    if self._chain_digest(record) != stored_digest:
                        logger.error("Audit chain break at line %d: record digest mismatch", line_number)
                        return False
                    expected_previous = stored_digest
        except (OSError, json.JSONDecodeError, ValueError) as err:
            logger.error("Audit chain verification failed for '%s': %s", self._sink_path, err)
            return False
        return True


_default_logger: Optional[AuditLogger] = None
_default_logger_lock = threading.Lock()


def configure_audit_log(
    sink_path: Optional[Union[str, Path]] = None,
    component: str = "compliance-engine",
    allowed_boundary: Optional[Union[str, Path]] = None,
) -> AuditLogger:
    """Installs the process-wide audit logger.

    Args:
        sink_path: Optional path of the ``.jsonl`` audit trail.
        component: Name of the emitting component.
        allowed_boundary: Optional directory that ``sink_path`` must resolve inside.

    Returns:
        The newly installed :class:`AuditLogger`.

    Raises:
        PermissionError: If ``sink_path`` escapes ``allowed_boundary``.
    """
    global _default_logger
    instance = AuditLogger(
        sink_path=sink_path, component=component, allowed_boundary=allowed_boundary
    )
    with _default_logger_lock:
        _default_logger = instance
    return instance


def get_audit_logger() -> AuditLogger:
    """Returns the process-wide audit logger, creating a no-sink default if needed.

    Returns:
        The active :class:`AuditLogger`.
    """
    global _default_logger
    with _default_logger_lock:
        if _default_logger is None:
            _default_logger = AuditLogger()
        return _default_logger


def reset_audit_log() -> None:
    """Discards the process-wide audit logger so the next call rebuilds a no-sink default.

    A sink installed by :func:`configure_audit_log` outlives the scope that created
    it. When that sink lived in a directory that has since been removed, later
    events would silently recreate the directory (``_append`` calls ``mkdir``) and
    write audit evidence somewhere nobody is watching. Callers that install a
    scoped sink must drop it again when the scope ends.
    """
    global _default_logger
    with _default_logger_lock:
        _default_logger = None


@contextmanager
def audit_operation(
    event_type: str,
    subject: str = "compliance-engine",
    obj: Optional[str] = None,
    detail: Optional[Dict[str, Any]] = None,
) -> Iterator[Dict[str, Any]]:
    """Context manager that records the outcome and duration of an operation.

    On a clean exit a ``success`` record is emitted. If the body raises, a ``failure``
    record capturing the exception type and message is emitted and the exception is
    re-raised unchanged - the audit trail never swallows an error.

    Args:
        event_type: One of the :class:`AuditEvent` constants.
        subject: The actor performing the operation.
        obj: The resource acted upon, if any.
        detail: Mutable structured context; the body may add keys before completion.

    Yields:
        The mutable detail dictionary that will be recorded.
    """
    context: Dict[str, Any] = dict(detail or {})
    started = time.monotonic()
    try:
        yield context
    except BaseException as err:
        context["duration_ms"] = round((time.monotonic() - started) * 1000, 3)
        context["error_type"] = type(err).__name__
        context["error_message"] = str(err)
        get_audit_logger().emit(
            event_type, outcome=AuditOutcome.FAILURE, subject=subject, obj=obj, detail=context
        )
        raise
    context["duration_ms"] = round((time.monotonic() - started) * 1000, 3)
    get_audit_logger().emit(
        event_type, outcome=AuditOutcome.SUCCESS, subject=subject, obj=obj, detail=context
    )
