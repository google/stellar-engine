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
import sys
import tempfile
import unittest

import yaml

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


def _install_stub_bins(stub_bin: Path) -> None:
    """Installs lightweight stub binaries for uv and terraform in stub_bin."""
    stub_bin.mkdir(parents=True, exist_ok=True)
    uv_stub = stub_bin / "uv"
    uv_stub.write_text(
        "#!/bin/sh\n"
        'if [ "$1" = "run" ]; then shift; fi\n'
        'if [ "$1" = "--locked" ]; then shift; fi\n'
        'if [ "$1" = "python" ]; then\n'
        "  shift\n"
        f'  exec "{sys.executable}" "$@"\n'
        "fi\n"
        "exit 0\n",
        encoding="utf-8",
    )
    uv_stub.chmod(uv_stub.stat().st_mode | stat.S_IXUSR)

    tf_stub = stub_bin / "terraform"
    tf_stub.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    tf_stub.chmod(tf_stub.stat().st_mode | stat.S_IXUSR)


class TestLintSh(unittest.TestCase):
    """Validates tools/lint.sh syntax and fail-closed error handling."""

    @classmethod
    def setUpClass(cls):
        cls.repo_root = Path(__file__).resolve().parent.parent
        cls.lint_script = cls.repo_root / "tools" / "lint.sh"

    def _build_version_check_sandbox(
        self, td: str
    ) -> tuple[Path, dict[str, str]]:
        """Creates a minimal repo sandbox to isolate tools/lint.sh checks."""
        sandbox = Path(td)
        tools_dir = sandbox / "tools"
        tools_dir.mkdir()
        shutil.copy2(self.lint_script, tools_dir / "lint.sh")
        shutil.copy2(
            self.repo_root / "tools" / "check_boilerplate.py",
            tools_dir / "check_boilerplate.py",
        )
        tflint_stub = tools_dir / "tflint.sh"
        tflint_stub.write_text(
            "#!/bin/bash\n" + _APACHE_HEADER + "\nexit 0\n",
            encoding="utf-8",
        )
        tflint_stub.chmod(tflint_stub.stat().st_mode | stat.S_IXUSR)

        for stub_py in (
            "check_documentation.py",
            "check_links.py",
            "check_names.py",
            "validate_metadata.py",
        ):
            script_path = tools_dir / stub_py
            script_path.write_text(
                "#!/usr/bin/env python3\n"
                + _APACHE_HEADER
                + "\nimport sys\n\nsys.exit(0)\n",
                encoding="utf-8",
            )
            script_path.chmod(script_path.stat().st_mode | stat.S_IXUSR)

        for dname in ("modules", "fast", "blueprints"):
            (sandbox / dname).mkdir()
        (sandbox / "fast" / "stages-aw").mkdir()
        (sandbox / "default-versions.tf").write_text(
            _VALID_VERSIONS_TF, encoding="utf-8"
        )

        stub_bin = sandbox / ".git" / "stub_bin"
        _install_stub_bins(stub_bin)
        env = os.environ.copy()
        env["PATH"] = f"{stub_bin}:{env.get('PATH', '')}"
        return sandbox, env

    def test_lint_sh_bash_syntax_valid(self):
        """tools/lint.sh must have valid bash syntax."""
        proc = subprocess.run(
            ["bash", "-n", str(self.lint_script)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(
            proc.returncode,
            0,
            f"Bash syntax error in lint.sh: {proc.stderr}",
        )

    def test_lint_sh_fails_closed_when_checks_fail(self):
        """tools/lint.sh must exit non-zero when a check fails."""
        with tempfile.TemporaryDirectory() as td:
            sandbox, env = self._build_version_check_sandbox(td)
            (sandbox / "blueprints" / "missing_header.py").write_text(
                "x = 1\n", encoding="utf-8"
            )
            proc = subprocess.run(
                ["bash", str(sandbox / "tools" / "lint.sh")],
                cwd=str(sandbox),
                env=env,
                capture_output=True,
                text=True,
                timeout=60,
            )
            self.assertNotEqual(
                proc.returncode,
                0,
                "lint.sh must exit non-zero when boilerplate fails",
            )
            self.assertIn("Lint checks FAILED", proc.stdout)
            self.assertIn("Boilerplate check", proc.stdout)

    def test_lint_sh_ignores_mismatched_versions_tf_in_excluded_dirs(self):
        """Mismatched versions.tf under .terraform/ or .venv/ are ignored."""
        with tempfile.TemporaryDirectory() as td:
            sandbox, env = self._build_version_check_sandbox(td)
            valid_bp = sandbox / "blueprints" / "sample"
            valid_bp.mkdir(parents=True)
            (valid_bp / "versions.tf").write_text(
                _VALID_VERSIONS_TF, encoding="utf-8"
            )

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
                f"Expected lint.sh to pass.\nSTDOUT:\n{proc.stdout}\n"
                f"STDERR:\n{proc.stderr}",
            )
            self.assertIn("[PASS] Version checks", proc.stdout)
            self.assertNotIn("Invalid versions.tf", proc.stdout)

    def test_lint_sh_fails_on_mismatched_versions_tf_outside_excluded_dirs(
        self,
    ):
        """Mismatched versions.tf outside excluded dirs fails lint.sh."""
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
            self.assertNotEqual(
                proc.returncode,
                0,
                "lint.sh must fail on invalid versions.tf",
            )
            self.assertIn("Invalid versions.tf", proc.stdout)
            self.assertIn("[FAIL] Version checks", proc.stdout)
            self.assertIn("- Version checks", proc.stdout)

    def test_ci_workflow_runs_repo_lint_on_push_and_pull_request(self):
        """CI workflow must run tools/lint.sh on push and pull_request."""
        ci_workflow = yaml.safe_load(
            (self.repo_root / ".github" / "workflows" / "ci.yml").read_text(
                encoding="utf-8"
            )
        )
        triggers = ci_workflow.get("on", ci_workflow.get(True, {}))
        self.assertIn("main", triggers["push"]["branches"])
        self.assertIn("main", triggers["pull_request"]["branches"])

        repo_lint = ci_workflow["jobs"]["repo-lint"]
        self.assertEqual(repo_lint["name"], "Repository Lint")
        run_commands = [
            step.get("run", "") for step in repo_lint.get("steps", [])
        ]
        self.assertTrue(
            any("bash tools/lint.sh" in cmd for cmd in run_commands),
            "repo-lint job must execute bash tools/lint.sh",
        )
