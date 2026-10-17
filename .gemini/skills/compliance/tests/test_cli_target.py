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

"""CLI target resolution: required, never a symlink or repository root."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from compliance_engine import extract_system_data
from compliance_engine import file_helpers

_SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
_CLIS = ("extract_system_data.py", "generate_compliance_artifacts.py", "validate_compliance_artifacts.py")
_TF = 'resource "google_storage_bucket" "b" {\n  name     = "b"\n  location = "US"\n}\n'


def _run(script: str, *args: str, cwd: str) -> subprocess.CompletedProcess:
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", COMPLIANCE_DISABLE_LIVE_SCANNERS="1")
    return subprocess.run([sys.executable, str(_SCRIPTS / script), *args], cwd=cwd, env=env,
                          capture_output=True, text=True, timeout=300, check=False)


def _snapshot(root: Path) -> dict:
    return {str(p.relative_to(root)): p.stat().st_mtime_ns for p in sorted(root.rglob("*"))}


class CliTargetTest(unittest.TestCase):
    """resolve_cli_target and the three CLI entrypoints."""

    def test_symlinked_target_refused_without_writes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            real = root / "blueprints" / "il5" / "postgresql"
            real.mkdir(parents=True)
            (real / "main.tf").write_text(_TF, encoding="utf-8")
            (root / "blueprints" / "fedramp-high").mkdir()
            link = root / "blueprints" / "fedramp-high" / "postgresql"
            os.symlink("../il5/postgresql", link)
            before = _snapshot(real)
            for script in _CLIS:
                with self.subTest(script=script):
                    proc = _run(script, str(link), cwd=tmp)
                    self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
                    self.assertIn("symbolic link", proc.stderr)
                    self.assertNotIn("Traceback", proc.stderr)
            self.assertEqual(_snapshot(real), before)
            with self.assertRaises(PermissionError):
                file_helpers.resolve_cli_target(link)

    def test_target_required(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            for script in _CLIS:
                with self.subTest(script=script):
                    proc = _run(script, cwd=tmp)
                    self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
                    self.assertIn("usage", (proc.stdout + proc.stderr).lower())
                    self.assertEqual(os.listdir(tmp), [])

    def test_repo_root_refused(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".git").mkdir()
            (root / "main.tf").write_text(_TF, encoding="utf-8")
            for script in _CLIS:
                with self.subTest(script=script):
                    proc = _run(script, str(root), cwd=tmp)
                    self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
                    self.assertIn("repository root", proc.stderr)
            self.assertEqual(sorted(os.listdir(tmp)), [".git", "main.tf"])

    def test_double_dash_end_of_options(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = os.getcwd()
            os.chdir(tmp)
            try:
                with self.assertRaises(SystemExit) as ctx:
                    extract_system_data.main(["--", "--allow-scanners"])
            finally:
                os.chdir(cwd)
            self.assertEqual(ctx.exception.code, 1)
            self.assertEqual(os.listdir(tmp), [])

    def test_symlinked_inventory_outside_target_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "blueprints" / "il5" / "t"
            target.mkdir(parents=True)
            (target / "main.tf").write_text(_TF, encoding="utf-8")
            outside = root / "outside_inventory.json"
            outside.write_text(json.dumps({"system_information": {"system_name": "OUTSIDE_MARKER", "impact_level": "IL5"}}), encoding="utf-8")
            os.symlink(outside, target / "system_inventory.json")
            proc = _run("generate_compliance_artifacts.py", str(target), "--data-format=yaml", "--policy-format=markdown", cwd=tmp)
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertNotIn("Traceback", proc.stderr)
            outputs = list((target / "ato_artifacts").rglob("*.md")) if (target / "ato_artifacts").exists() else []
            self.assertFalse(any("OUTSIDE_MARKER" in p.read_text(errors="ignore") for p in outputs))
            with self.assertRaises(PermissionError):
                file_helpers.read_text_file(target / "system_inventory.json")
            self.assertIn("OUTSIDE_MARKER", file_helpers.read_text_file(target / "system_inventory.json", allow_symlinks=True))


if __name__ == "__main__":
    unittest.main()
