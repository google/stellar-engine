#!/usr/bin/env python3
"""Structured audit logging for the compliance engine (NIST SP 800-53 AU family).

Human-readable ``logger.info`` output is useful for operators but is not evidence.
An RMF/FedRAMP assessor needs machine-parseable records that answer *who did what,
to which resource, when, and with what outcome*. This module emits exactly that as
newline-delimited JSON, satisfying:

* **AU-2 (Event Logging)** - a fixed, enumerated set of security-relevant event types.
* **AU-3 (Content of Audit Records)** - every record carries timestamp, event type,
  outcome, subject, object, and source component.
* **AU-3(1) (Additional Audit Information)** - arbitrary structured detail fields.
* **AU-8 (Time Stamps)** - RFC 3339 timestamps in UTC with explicit offset.
* **AU-9 (Protection of Audit Information)** - records are append-only, written with
  owner-only permissions, and carry a monotonically increasing sequence number plus a
  per-record chain digest so that silent deletion or reordering is detectable.
* **AU-10 (Non-Repudiation)** - the chain digest binds each record to its predecessor.

Design constraints:

* Sensitive values are redacted through the shared scrubber before serialization, so
  the audit trail can never become the leak vector.
* Emission never raises into the caller. A compliance run must not abort because the
  audit sink is unavailable; instead the failure is surfaced on the standard logger
  and tracked in :attr:`AuditLogger.dropped_records`.
* The chain digest uses SHA-256, which is FIPS 140-3 approved. It is an integrity
  witness only - it is not a keyed MAC and is not a secret.
"""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import logging
import os
from pathlib import Path
import threading
import time
from typing import Any, Dict, Final, Iterator, Optional, Union
import uuid

try:
    from .file_helpers import ensure_path_within_boundary, scrub_sensitive_data
except (ImportError, ValueError):
    from file_helpers import ensure_path_within_boundary, scrub_sensitive_data

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
    ) -> None:
        """Initializes the audit logger.

        Args:
            sink_path: Optional path of the ``.jsonl`` audit trail. When None, records
                are not persisted to disk.
            component: Name of the emitting component, recorded on every event.
            allowed_boundary: Optional directory that ``sink_path`` must resolve inside,
                preventing an operator-supplied path from escaping the workspace.

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

        if sink_path is not None:
            resolved = Path(sink_path).resolve()
            if allowed_boundary is not None:
                resolved = ensure_path_within_boundary(resolved, allowed_boundary)
            self._sink_path = resolved
            self._resume_chain_if_present()

    def _resume_chain_if_present(self) -> None:
        """Resumes sequence and digest tracking from an existing audit trail on disk.

        If the sink path exists and contains prior records, reads the last valid
        record to initialize ``_sequence`` and ``_previous_digest``. This prevents
        breaking the tamper-evident hash chain when multiple engine invocations or
        re-initialized loggers append to the same audit log (NIST AU-9 / AU-10).
        """
        if self._sink_path is None or not self._sink_path.is_file():
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
        self._sequence += 1
        record: Dict[str, Any] = {
            "schema_version": AUDIT_SCHEMA_VERSION,
            "timestamp": _utc_timestamp(),
            "sequence": self._sequence,
            "session_id": self._session_id,
            "component": self.component,
            "event_type": event_type,
            "outcome": outcome,
            "subject": subject,
            "object": obj,
            # Redaction happens before the record is ever serialized, so the audit
            # trail cannot become an exfiltration channel for credentials.
            "detail": scrub_sensitive_data(detail or {}),
            "previous_digest": self._previous_digest,
        }
        record["digest"] = self._chain_digest(record)
        self._previous_digest = record["digest"]
        return record

    @staticmethod
    def _chain_digest(record: Dict[str, Any]) -> str:
        """Computes the SHA-256 chain digest binding a record to its predecessor.

        Args:
            record: Record contents excluding the ``digest`` field.

        Returns:
            Lowercase hexadecimal SHA-256 digest.
        """
        canonical = json.dumps(record, sort_keys=True, separators=(",", ":"), default=str)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

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

        Returns:
            True when the trail is absent, empty, or internally consistent; False when
            a record has been altered, reordered, or removed.
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
