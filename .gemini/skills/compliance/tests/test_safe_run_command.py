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

"""Single bounded subprocess runner."""

from pathlib import Path
import re
import sys
import unittest

from compliance_engine import file_helpers


class SafeRunCommandTest(unittest.TestCase):
    """run_bounded_command spools output, bounds it, and does not retry non-zero exits."""

    def test_output_bounded(self) -> None:
        cmd = [sys.executable, "-c", "import sys; sys.stdout.write('x' * 200000)"]
        with self.assertRaises(MemoryError):
            file_helpers.run_bounded_command(cmd, timeout=30, max_output_bytes=1000)
        ok = file_helpers.run_bounded_command(cmd, timeout=30, max_output_bytes=300000)
        self.assertEqual(len(ok.stdout), 200000)
        err = file_helpers.run_bounded_command(
            [sys.executable, "-c", "import sys; sys.stderr.write('e' * 5000)"], timeout=30, max_output_bytes=100
        )
        self.assertEqual(len(err.stderr), 100)

    def test_no_retry_on_nonzero(self) -> None:
        calls = []

        class _Proc:
            returncode = 3
            args = ["fake"]

            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

            def wait(self, timeout=None):
                return 3

        def fake_popen(argv, **kwargs):
            calls.append(argv)
            return _Proc()

        res = file_helpers.run_bounded_command(["fake"], timeout=5, attempts=3, popen=fake_popen)
        self.assertEqual(res.returncode, 3)
        self.assertEqual(len(calls), 1)
        res = file_helpers.run_bounded_command(["fake"], timeout=5, attempts=2, retry_on_nonzero=True, retry_base_seconds=0, popen=fake_popen)
        self.assertEqual(len(calls), 3)

    def test_only_file_helpers_spawns_processes(self) -> None:
        pkg = Path(file_helpers.__file__).parent
        pattern = re.compile(r"subprocess\.(?:run|call|check_output|check_call)\(|subprocess\.Popen\(")
        hits = [
            f"{p.name}:{n}"
            for p in sorted(pkg.glob("*.py"))
            if p.name != "file_helpers.py"
            for n, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1)
            if pattern.search(line)
        ]
        self.assertEqual(hits, [])


if __name__ == "__main__":
    unittest.main()
