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

"""Non-regular files such as FIFOs must be rejected without blocking."""

import os
from pathlib import Path
import signal
import tempfile
import time
import unittest

from compliance_engine import extract_system_data
from compliance_engine import file_helpers


class _FifoHangError(BaseException):
    """Alarm exception that is not a subclass of Exception/OSError."""


class SpecialFilesTest(unittest.TestCase):
    """FIFOs inside a target directory must not stall file reads or extraction."""

    def test_fifo_rejected_quickly(self) -> None:
        if not hasattr(os, "mkfifo"):
            self.skipTest("os.mkfifo is not available on this platform")
        with tempfile.TemporaryDirectory() as tmp:
            fifo = Path(tmp) / "zz_blocking.tf"
            os.mkfifo(fifo)

            def _on_alarm(_signum: int, _frame: object) -> None:
                raise _FifoHangError("read_text_file blocked on FIFO for >= 1s")

            old_handler = signal.signal(signal.SIGALRM, _on_alarm)
            signal.setitimer(signal.ITIMER_REAL, 1.0)
            start = time.monotonic()
            try:
                with self.assertRaises(ValueError):
                    file_helpers.read_text_file(fifo, allowed_boundary=tmp)
            finally:
                signal.setitimer(signal.ITIMER_REAL, 0.0)
                signal.signal(signal.SIGALRM, old_handler)
            self.assertLess(time.monotonic() - start, 1.0)

    def test_deep_scan_skips_fifo(self) -> None:
        if not hasattr(os, "mkfifo"):
            self.skipTest("os.mkfifo is not available on this platform")
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            (target / "main.tf").write_text(
                'resource "google_storage_bucket" "audit_logs" {\n  name = "audit-logs-bucket"\n  location = "US"\n}\n',
                encoding="utf-8",
            )
            os.mkfifo(target / "zz_blocking.tf")

            def _on_alarm(_signum: int, _frame: object) -> None:
                raise _FifoHangError("deep_scan_tf_files blocked on FIFO for >= 2s")

            old_handler = signal.signal(signal.SIGALRM, _on_alarm)
            signal.setitimer(signal.ITIMER_REAL, 2.0)
            try:
                scanned = extract_system_data.deep_scan_tf_files(str(target))
            finally:
                signal.setitimer(signal.ITIMER_REAL, 0.0)
                signal.signal(signal.SIGALRM, old_handler)

            buckets = [b.get("name") for b in scanned.get("storage_buckets", [])]
            self.assertIn("audit-logs-bucket", buckets)


if __name__ == "__main__":
    unittest.main()
