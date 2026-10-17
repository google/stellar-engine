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

"""Package import hygiene: lazy submodules, no bare-name aliases, thin script entrypoints."""

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

_SKILL_ROOT = Path(__file__).resolve().parents[1]
_SRC = _SKILL_ROOT / "src"
_PKG = _SRC / "compliance_engine"
_SCRIPTS = _SKILL_ROOT / "scripts"


def _run_python(code: str, cwd: str) -> subprocess.CompletedProcess:
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONPATH=str(_SRC))
    return subprocess.run([sys.executable, "-c", code], cwd=cwd, env=env, capture_output=True, text=True, timeout=120, check=False)


class PackageImportTest(unittest.TestCase):
    """Importing the package must not inject bare module names or eagerly load submodules."""

    def test_import_does_not_pollute_sys_modules(self) -> None:
        code = (
            "import sys, compliance_engine\n"
            "bare = [m for m in ('utils', 'file_helpers', 'poam_rules', 'extract_system_data') if m in sys.modules]\n"
            "eager = [m for m in sys.modules if m.startswith('compliance_engine.')]\n"
            "print(bare, eager)\n"
            "assert not bare, bare\n"
            "assert 'compliance_engine.extract_system_data' not in eager, eager\n"
            "from compliance_engine import parse_yaml_safe, file_helpers\n"
            "assert callable(parse_yaml_safe) and file_helpers.parse_yaml_safe is parse_yaml_safe\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            proc = _run_python(code, tmp)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_no_dual_import_fallbacks(self) -> None:
        offenders = [p.name for p in _PKG.glob("*.py") if "except (ImportError, ValueError)" in p.read_text(encoding="utf-8")]
        self.assertEqual(offenders, [])

    def test_facade_shims_removed(self) -> None:
        self.assertFalse((_PKG / "utils.py").exists())
        self.assertFalse((_SCRIPTS / "test_compliance_engine.py").exists())

    def test_scripts_entrypoints_help(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            for cwd in (str(_SKILL_ROOT.parents[2]), tmp):
                for script in ("extract_system_data.py", "generate_compliance_artifacts.py", "validate_compliance_artifacts.py"):
                    with self.subTest(cwd=cwd, script=script):
                        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
                        env.pop("PYTHONPATH", None)
                        proc = subprocess.run(
                            [sys.executable, str(_SCRIPTS / script), "--help"],
                            cwd=cwd, env=env, capture_output=True, text=True, timeout=120, check=False,
                        )
                        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
                        self.assertIn("usage", (proc.stdout + proc.stderr).lower())
                        self.assertEqual(os.listdir(tmp), [], "--help must not write files")


if __name__ == "__main__":
    unittest.main()
