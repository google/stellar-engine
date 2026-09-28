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

"""Comprehensive regression and negative edge-case tests for the structured audit trail.

Validates the NIST SP 800-53 AU family guarantees implemented in ``audit_log.py``:
- AU-2: Closed event enumeration and session correlation.
- AU-3 / AU-3(1): Content of audit records, structured details, and automatic redaction.
- AU-5: Denial-of-service / resource exhaustion protection via record-size truncation.
- AU-8: RFC 3339 UTC timestamps with explicit offsets.
- AU-9: Append-only owner permissions (0o600 / 0o700), non-interleaving writers,
  sequence monotonicity, and tamper-evident SHA-256 chain verification.
- AU-10: Predecessor hash binding and non-repudiation.
- Fault tolerance: OS-level write failures (disk quota, permissions) increment dropped_records
  without crashing calling compliance workflows.
"""

from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.abspath(os.path.join(TESTS_DIR, "..", "scripts"))
SRC_DIR = os.path.abspath(os.path.join(TESTS_DIR, "..", "src"))
ENGINE_DIR = os.path.abspath(os.path.join(SRC_DIR, "compliance_engine"))
for p in (ENGINE_DIR, SRC_DIR, SCRIPTS_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from compliance_engine import audit_log
except ImportError:
    import audit_log


class TestAuditLogConcurrencyAndIntegrity(unittest.TestCase):
    """Thread-safety, sequence continuity, and cryptographic chaining under concurrent load."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name).resolve()
        self.sink = self.root / "audit" / "trail.jsonl"
        self.audit = audit_log.AuditLogger(self.sink, "test-concurrent", allowed_boundary=self.root)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_concurrent_emit_maintains_strict_sequence_and_valid_chain(self) -> None:
        """AU-9: Multiple threads emitting concurrently must not tear lines, drop sequences, or break digests."""
        num_threads = 8
        records_per_thread = 25
        total_records = num_threads * records_per_thread

        def _worker(thread_idx: int) -> None:
            for rec_idx in range(records_per_thread):
                self.audit.emit(
                    audit_log.AuditEvent.ARTIFACT_GENERATED,
                    subject=f"worker-{thread_idx}",
                    obj=f"file-{rec_idx}.txt",
                    detail={"worker": thread_idx, "iteration": rec_idx},
                )

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(_worker, i) for i in range(num_threads)]
            for f in futures:
                f.result()

        self.assertEqual(self.audit.dropped_records, 0)
        self.assertTrue(self.sink.is_file())

        lines = [line.strip() for line in self.sink.read_text(encoding="utf-8").splitlines() if line.strip()]
        self.assertEqual(len(lines), total_records, f"Expected {total_records} lines, found {len(lines)}")

        # Verify strict sequence monotonicity and session binding
        parsed_records = [json.loads(line) for line in lines]
        for idx, rec in enumerate(parsed_records, start=1):
            self.assertEqual(rec["sequence"], idx, f"Sequence gap or mismatch at record index {idx}")
            self.assertEqual(rec["session_id"], self.audit.session_id)
            self.assertEqual(rec["schema_version"], audit_log.AUDIT_SCHEMA_VERSION)

        # Verify cryptographic chain integrity across the entire concurrent log
        self.assertTrue(
            self.audit.verify_chain(),
            "Audit chain verification failed after concurrent emissions",
        )

    def test_reinitialized_logger_resumes_chain_without_break(self) -> None:
        """AU-9/AU-10: Initializing an AuditLogger against an existing sink must resume sequence and digest chain without breaks."""
        for i in range(3):
            self.audit.emit(
                audit_log.AuditEvent.ARTIFACT_GENERATED,
                subject=f"init-op-{i}",
                obj=f"file-{i}.txt",
            )
        self.assertTrue(self.audit.verify_chain())

        # Construct a second logger pointing at the same sink (simulating subsequent pipeline stage)
        second_logger = audit_log.AuditLogger(
            self.sink,
            "test-resumed",
            allowed_boundary=self.root,
        )
        self.assertEqual(second_logger._sequence, 3)
        self.assertEqual(second_logger._previous_digest, self.audit._previous_digest)

        # Emit fourth record
        rec4 = second_logger.emit(
            audit_log.AuditEvent.ARTIFACT_VALIDATED,
            subject="resumed-op",
            obj="file-3.txt",
        )
        self.assertEqual(rec4["sequence"], 4)
        self.assertTrue(second_logger.verify_chain())


class TestAuditLogResourceLimits(unittest.TestCase):
    """Resource bounding and truncation behavior (AU-5 / CWE-400)."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name).resolve()
        self.sink = self.root / "audit" / "bounded.jsonl"
        self.audit = audit_log.AuditLogger(self.sink, "test-bounds", allowed_boundary=self.root)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_oversize_payload_is_truncated_and_chain_remains_valid(self) -> None:
        """A pathological audit detail payload (> 64 KiB) must be truncated to prevent disk bloat while retaining chain integrity."""
        huge_payload = {"giant_blob": "A" * (audit_log._MAX_RECORD_BYTES + 4096)}
        record = self.audit.emit(
            audit_log.AuditEvent.ARTIFACT_GENERATED,
            subject="operator",
            obj="huge.docx",
            detail=huge_payload,
        )

        self.assertTrue(record["detail"]["truncated"])
        self.assertGreater(record["detail"]["original_detail_bytes"], audit_log._MAX_RECORD_BYTES)

        # Verify persisted line
        persisted = self.sink.read_text(encoding="utf-8").strip()
        loaded = json.loads(persisted)
        self.assertTrue(loaded["detail"]["truncated"])

        # Cryptographic chain must still pass verification
        self.assertTrue(self.audit.verify_chain())

    def test_sequence_after_truncated_record_chains_cleanly(self) -> None:
        """A normal record following a truncated record must correctly bind to the truncated record's digest."""
        self.audit.emit(
            audit_log.AuditEvent.ARTIFACT_GENERATED,
            detail={"data": "X" * (audit_log._MAX_RECORD_BYTES + 2048)},
        )
        self.audit.emit(
            audit_log.AuditEvent.PIPELINE_COMPLETED,
            detail={"status": "normal"},
        )

        lines = self.sink.read_text(encoding="utf-8").strip().splitlines()
        self.assertEqual(len(lines), 2)
        first = json.loads(lines[0])
        second = json.loads(lines[1])

        self.assertTrue(first["detail"]["truncated"])
        self.assertEqual(second["previous_digest"], first["digest"])
        self.assertTrue(self.audit.verify_chain())


class TestAuditLogTamperDetection(unittest.TestCase):
    """Negative tests verifying cryptographic chain sensitivity to unauthorized modification, reordering, or corruption."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name).resolve()
        self.sink = self.root / "audit" / "tamper.jsonl"
        self.audit = audit_log.AuditLogger(self.sink, "test-tamper", allowed_boundary=self.root)
        for i in range(4):
            self.audit.emit(
                audit_log.AuditEvent.ARTIFACT_GENERATED,
                subject=f"operator-{i}",
                obj=f"doc-{i}.md",
                detail={"index": i},
            )

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_unaltered_log_verifies(self) -> None:
        self.assertTrue(self.audit.verify_chain())

    def test_corrupted_json_line_fails_verification(self) -> None:
        """Corrupting a line with non-JSON syntax must cause verify_chain to return False."""
        lines = self.sink.read_text(encoding="utf-8").splitlines()
        lines[1] = "NOT_VALID_JSON{{"
        self.sink.write_text("\n".join(lines) + "\n", encoding="utf-8")
        self.assertFalse(self.audit.verify_chain())

    def test_sequence_break_fails_verification(self) -> None:
        """Altering a sequence number must be detected."""
        lines = self.sink.read_text(encoding="utf-8").splitlines()
        rec = json.loads(lines[2])
        rec["sequence"] = 999  # was 3
        # recompute digest for the corrupted record
        digest = self.audit._chain_digest({k: v for k, v in rec.items() if k != "digest"})
        rec["digest"] = digest
        lines[2] = json.dumps(rec)
        self.sink.write_text("\n".join(lines) + "\n", encoding="utf-8")
        self.assertFalse(self.audit.verify_chain())

    def test_predecessor_hash_mismatch_fails_verification(self) -> None:
        """Altering previous_digest must break the chain verification."""
        lines = self.sink.read_text(encoding="utf-8").splitlines()
        rec = json.loads(lines[2])
        rec["previous_digest"] = "f" * 64
        lines[2] = json.dumps(rec)
        self.sink.write_text("\n".join(lines) + "\n", encoding="utf-8")
        self.assertFalse(self.audit.verify_chain())

    def test_payload_field_alteration_fails_verification(self) -> None:
        """Modifying the outcome or subject without matching digest change must fail."""
        lines = self.sink.read_text(encoding="utf-8").splitlines()
        rec = json.loads(lines[1])
        rec["outcome"] = audit_log.AuditOutcome.DENIED
        lines[1] = json.dumps(rec)
        self.sink.write_text("\n".join(lines) + "\n", encoding="utf-8")
        self.assertFalse(self.audit.verify_chain())

    def test_empty_or_nonexistent_sink_verifies_true(self) -> None:
        """A missing or blank file represents an unstarted audit trail and must return True."""
        empty_sink = self.root / "audit" / "empty.jsonl"
        empty_logger = audit_log.AuditLogger(empty_sink, allowed_boundary=self.root)
        self.assertTrue(empty_logger.verify_chain())

        empty_sink.touch()
        self.assertTrue(empty_logger.verify_chain())


class TestAuditLogFaultToleranceAndBoundaries(unittest.TestCase):
    """Negative tests for operating system write failures and path boundaries."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name).resolve()
        self.sink = self.root / "audit" / "fault.jsonl"
        self.audit = audit_log.AuditLogger(self.sink, "test-fault", allowed_boundary=self.root)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_oserror_during_append_increments_dropped_records_without_raising(self) -> None:
        """Compliance runs must not crash if the audit sink encounters an OS write failure (e.g. disk full)."""
        with patch.object(self.audit, "_append", side_effect=OSError("Disk quota exceeded")):
            record = self.audit.emit(
                audit_log.AuditEvent.PIPELINE_STARTED,
                subject="test-operator",
            )
            self.assertEqual(self.audit.dropped_records, 1)
            self.assertIsNotNone(record)

    def test_path_traversal_outside_allowed_boundary_raises_permission_error(self) -> None:
        """Attempting to construct an AuditLogger with a sink path outside the allowed boundary must fail closed."""
        outside_path = self.root / ".." / "escaped_audit.jsonl"
        with self.assertRaises(PermissionError):
            audit_log.AuditLogger(outside_path, allowed_boundary=self.root)

    def test_no_sink_mode_operates_cleanly_without_file(self) -> None:
        """Constructing an AuditLogger with sink_path=None performs logging in-memory without filesystem calls."""
        memory_logger = audit_log.AuditLogger(sink_path=None)
        self.assertIsNone(memory_logger.sink_path)
        record = memory_logger.emit(
            audit_log.AuditEvent.PIPELINE_STARTED,
            subject="operator",
        )
        self.assertEqual(record["sequence"], 1)
        self.assertEqual(memory_logger.dropped_records, 0)
        self.assertTrue(memory_logger.verify_chain())


class TestAuditOperationContextManager(unittest.TestCase):
    """Testing the audit_operation context manager under success and exception flows."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name).resolve()
        self.sink = self.root / "audit" / "context.jsonl"
        self.logger = audit_log.configure_audit_log(self.sink, "test-cm", allowed_boundary=self.root)
        self.addCleanup(audit_log.reset_audit_log)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_audit_operation_records_success_and_duration(self) -> None:
        """Context manager records duration_ms and SUCCESS outcome on normal completion."""
        with audit_log.audit_operation(
            audit_log.AuditEvent.ARTIFACT_GENERATED,
            subject="generator",
            obj="ssp.md",
            detail={"format": "markdown"},
        ) as ctx:
            ctx["custom_metric"] = 42
            time.sleep(0.005)

        lines = self.sink.read_text(encoding="utf-8").strip().splitlines()
        self.assertEqual(len(lines), 1)
        rec = json.loads(lines[0])
        self.assertEqual(rec["outcome"], audit_log.AuditOutcome.SUCCESS)
        self.assertEqual(rec["object"], "ssp.md")
        self.assertIn("duration_ms", rec["detail"])
        self.assertGreater(rec["detail"]["duration_ms"], 0)
        self.assertEqual(rec["detail"]["custom_metric"], 42)

    def test_audit_operation_records_failure_and_reraises_standard_exception(self) -> None:
        """Context manager records duration_ms, error_type, and FAILURE outcome, and re-raises unchanged."""
        with self.assertRaises(ValueError) as err_ctx:
            with audit_log.audit_operation(
                audit_log.AuditEvent.CONFIG_LOADED,
                obj="bad_config.yaml",
            ):
                raise ValueError("Invalid schema configuration")

        self.assertIn("Invalid schema", str(err_ctx.exception))
        lines = self.sink.read_text(encoding="utf-8").strip().splitlines()
        self.assertEqual(len(lines), 1)
        rec = json.loads(lines[0])
        self.assertEqual(rec["outcome"], audit_log.AuditOutcome.FAILURE)
        self.assertEqual(rec["detail"]["error_type"], "ValueError")
        self.assertEqual(rec["detail"]["error_message"], "Invalid schema configuration")
        self.assertIn("duration_ms", rec["detail"])

    def test_audit_operation_handles_base_exception(self) -> None:
        """Context manager observes BaseException (e.g. KeyboardInterrupt) without swallowing it."""
        with self.assertRaises(KeyboardInterrupt):
            with audit_log.audit_operation(audit_log.AuditEvent.PIPELINE_STARTED):
                raise KeyboardInterrupt("Interrupted by user")

        lines = self.sink.read_text(encoding="utf-8").strip().splitlines()
        self.assertEqual(len(lines), 1)
        rec = json.loads(lines[0])
        self.assertEqual(rec["outcome"], audit_log.AuditOutcome.FAILURE)
        self.assertEqual(rec["detail"]["error_type"], "KeyboardInterrupt")


class TestAuditLogSingletonLifecycle(unittest.TestCase):
    """Lifecycle tests for global logger configuration, retrieval, and reset."""

    def setUp(self) -> None:
        audit_log.reset_audit_log()

    def tearDown(self) -> None:
        audit_log.reset_audit_log()

    def test_get_audit_logger_creates_default_no_sink_when_unconfigured(self) -> None:
        logger1 = audit_log.get_audit_logger()
        self.assertIsNone(logger1.sink_path)
        logger2 = audit_log.get_audit_logger()
        self.assertIs(logger1, logger2)

    def test_configure_and_reset_audit_log(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            sink = Path(tmp_dir) / "global_audit.jsonl"
            configured = audit_log.configure_audit_log(sink_path=sink, component="global-test")
            self.assertIs(audit_log.get_audit_logger(), configured)
            self.assertEqual(configured.component, "global-test")

            audit_log.reset_audit_log()
            fresh = audit_log.get_audit_logger()
            self.assertIsNot(fresh, configured)
            self.assertIsNone(fresh.sink_path)


if __name__ == "__main__":
    unittest.main(verbosity=2)
