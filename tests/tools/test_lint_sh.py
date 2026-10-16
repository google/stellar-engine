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

"""Tests for tools/lint.sh fail-closed execution and clean-repo pass."""

from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


class TestLintSh(unittest.TestCase):
    """Validates tools/lint.sh syntax, clean-repo exit 0, and fail-closed error handling."""

    @classmethod
    def setUpClass(cls):
        cls.repo_root = Path(__file__).resolve().parent.parent.parent
        cls.lint_script = cls.repo_root / "tools" / "lint.sh"

    def test_lint_sh_bash_syntax_valid(self):
        """tools/lint.sh must have valid bash syntax."""
        proc = subprocess.run(
            ["bash", "-n", str(self.lint_script)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, f"Bash syntax error in lint.sh: {proc.stderr}")

    def test_lint_sh_fails_closed_when_checks_fail(self):
        """tools/lint.sh must exit non-zero when a check fails."""
        with tempfile.TemporaryDirectory() as td:
            sandbox = Path(td)
            tools_dir = sandbox / "tools"
            tools_dir.mkdir()
            for fname in ("lint.sh", "check_boilerplate.py", "check_documentation.py", "check_links.py", "check_names.py", "validate_metadata.py", "tfdoc.py", "bpmetadataschema.json"):
                src = self.repo_root / "tools" / fname
                if src.is_file():
                    shutil.copy2(src, tools_dir / fname)
            for dname in ("modules", "fast", "blueprints"):
                (sandbox / dname).mkdir()
            (sandbox / "fast" / "stages").mkdir()
            (sandbox / "default-versions.tf").write_text("# Copyright 2026 Google LLC\n", encoding="utf-8")
            # Write a Python file missing the Apache 2.0 header
            (sandbox / "blueprints" / "missing_header.py").write_text("x = 1\n", encoding="utf-8")

            proc = subprocess.run(
                ["bash", str(tools_dir / "lint.sh")],
                cwd=str(sandbox),
                capture_output=True,
                text=True,
                timeout=60,
            )
            self.assertNotEqual(proc.returncode, 0, "lint.sh must exit non-zero when boilerplate fails")
            self.assertIn("Lint checks FAILED", proc.stdout)
            self.assertIn("Boilerplate check", proc.stdout)
