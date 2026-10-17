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

import os
from pathlib import Path
import shutil
import stat
import subprocess
import tempfile
import unittest

_APACHE_HEADER = """\
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

_VALID_VERSIONS_TF = (
    _APACHE_HEADER
    + """
terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 5.0.0"
    }
  }
}
"""
)


class TestLintSh(unittest.TestCase):
    """Validates tools/lint.sh syntax, clean-repo exit 0, and fail-closed error handling."""

    @classmethod
    def setUpClass(cls):
        cls.repo_root = Path(__file__).resolve().parent.parent.parent
        cls.lint_script = cls.repo_root / "tools" / "lint.sh"

    def _build_version_check_sandbox(self, td: str) -> tuple[Path, dict[str, str]]:
        """Creates a minimal repo sandbox to isolate tools/lint.sh version checks."""
        sandbox = Path(td)
        tools_dir = sandbox / "tools"
        tools_dir.mkdir()
        shutil.copy2(self.lint_script, tools_dir / "lint.sh")
        shutil.copy2(
            self.repo_root / "tools" / "check_boilerplate.py",
            tools_dir / "check_boilerplate.py",
        )
        for stub_py in (
            "check_documentation.py",
            "check_links.py",
            "check_names.py",
            "validate_metadata.py",
        ):
            script_path = tools_dir / stub_py
            script_path.write_text(
                "#!/usr/bin/env python3\n" + _APACHE_HEADER + "\nimport sys\n\nsys.exit(0)\n",
                encoding="utf-8",
            )
            script_path.chmod(script_path.stat().st_mode | stat.S_IXUSR)

        for dname in ("modules", "fast", "blueprints"):
            (sandbox / dname).mkdir()
        (sandbox / "fast" / "stages").mkdir()
        (sandbox / "default-versions.tf").write_text(_VALID_VERSIONS_TF, encoding="utf-8")

        stub_bin = sandbox / ".git" / "stub_bin"
        stub_bin.mkdir(parents=True)
        for tool_name in ("terraform", "yapf"):
            stub_path = stub_bin / tool_name
            stub_path.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            stub_path.chmod(stub_path.stat().st_mode | stat.S_IXUSR)

        env = os.environ.copy()
        env["PATH"] = f"{env.get('PATH', '')}:{stub_bin}"
        return sandbox, env

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

    def test_lint_sh_ignores_mismatched_versions_tf_in_excluded_dirs(self):
        """Mismatched versions.tf under .terraform/ or virtualenv dirs must be ignored."""
        with tempfile.TemporaryDirectory() as td:
            sandbox, env = self._build_version_check_sandbox(td)
            valid_bp = sandbox / "blueprints" / "sample"
            valid_bp.mkdir(parents=True)
            (valid_bp / "versions.tf").write_text(_VALID_VERSIONS_TF, encoding="utf-8")

            for excluded_rel in (
                ".terraform/modules/net/versions.tf",
                ".venv/lib/versions.tf",
                "venv/lib/versions.tf",
                "node_modules/pkg/versions.tf",
                "__pycache__/versions.tf",
                ".git/hooks/versions.tf",
            ):
                bad_vfile = sandbox / excluded_rel
                bad_vfile.parent.mkdir(parents=True, exist_ok=True)
                bad_vfile.write_text("terraform {}\n", encoding="utf-8")

            # Also verify yapf ignores unformatted Python inside blueprints/.venv
            bad_venv_py = valid_bp / ".venv" / "bad.py"
            bad_venv_py.parent.mkdir(parents=True, exist_ok=True)
            bad_venv_py.write_text("def f( ):\n    x=1\n", encoding="utf-8")

            proc = subprocess.run(
                ["bash", str(sandbox / "tools" / "lint.sh")],
                cwd=str(sandbox),
                env=env,
                capture_output=True,
                text=True,
                timeout=60,
            )
            self.assertEqual(
                proc.returncode,
                0,
                f"Expected lint.sh to pass when bad versions.tf is inside excluded dirs.\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}",
            )
            self.assertIn("[PASS] Version checks", proc.stdout)
            self.assertNotIn("Invalid versions.tf", proc.stdout)

    def test_lint_sh_fails_on_mismatched_versions_tf_outside_excluded_dirs(self):
        """Mismatched versions.tf outside excluded dirs must still fail lint.sh."""
        with tempfile.TemporaryDirectory() as td:
            sandbox, env = self._build_version_check_sandbox(td)
            bad_bp = sandbox / "blueprints" / "bad_module"
            bad_bp.mkdir(parents=True)
            (bad_bp / "versions.tf").write_text(
                _APACHE_HEADER + "\nterraform {}\n",
                encoding="utf-8",
            )

            proc = subprocess.run(
                ["bash", str(sandbox / "tools" / "lint.sh")],
                cwd=str(sandbox),
                env=env,
                capture_output=True,
                text=True,
                timeout=60,
            )
            self.assertNotEqual(proc.returncode, 0, "lint.sh must fail on invalid versions.tf")
            self.assertIn("Invalid versions.tf", proc.stdout)
            self.assertIn("[FAIL] Version checks", proc.stdout)
            self.assertIn("- Version checks", proc.stdout)
