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

"""Extractor and generator fail closed with exit 1 and a one-line error."""

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

_SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
_TF = 'resource "google_storage_bucket" "b" {\n  name     = "b"\n  location = "US"\n}\n'


def _run(script: str, target: Path) -> subprocess.CompletedProcess:
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", COMPLIANCE_DISABLE_LIVE_SCANNERS="1")
    return subprocess.run([sys.executable, str(_SCRIPTS / script), str(target)], cwd=str(target.parent), env=env,
                          capture_output=True, text=True, timeout=300, check=False)


class CliExitCodeTest(unittest.TestCase):
    """Empty, unreadable or unparseable inputs and malformed config are errors, not empty packages."""

    def _target(self, tmp: str) -> Path:
        target = Path(tmp) / "blueprints" / "il5" / "t"
        target.mkdir(parents=True)
        return target

    def _assert_failed(self, proc: subprocess.CompletedProcess, target: Path) -> None:
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertNotIn("Traceback", proc.stderr)
        self.assertIn("[ERROR]", proc.stderr)
        self.assertFalse((target / "system_inventory.json").exists())

    def test_extract_empty_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = self._target(tmp)
            self._assert_failed(_run("extract_system_data.py", target), target)

    def test_extract_all_unparseable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = self._target(tmp)
            (target / "main.tf").write_text("this is {{{ not terraform\n", encoding="utf-8")
            self._assert_failed(_run("extract_system_data.py", target), target)

    @unittest.skipIf(hasattr(os, "geteuid") and os.geteuid() == 0, "root can read chmod 000 files")
    def test_extract_unreadable_tf(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = self._target(tmp)
            tf = target / "main.tf"
            tf.write_text(_TF, encoding="utf-8")
            tf.chmod(0)
            try:
                self._assert_failed(_run("extract_system_data.py", target), target)
            finally:
                tf.chmod(0o644)

    def test_generate_malformed_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = self._target(tmp)
            (target / "main.tf").write_text(_TF, encoding="utf-8")
            (target / "compliance_config.yaml").write_text("system_information: [unclosed\n  : :\n", encoding="utf-8")
            proc = _run("generate_compliance_artifacts.py", target)
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertNotIn("Traceback", proc.stderr)
            self.assertIn("[ERROR]", proc.stderr)


if __name__ == "__main__":
    unittest.main()
