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

import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from compliance_engine import file_helpers
from compliance_engine import security_scanner_bridge as ssb


class TestReviewScannerRegression(unittest.TestCase):
    def test_semgrep_http_rejection(self):
        with patch("compliance_engine.security_scanner_bridge.shutil.which", return_value="/usr/bin/semgrep"):
            findings = ssb.run_semgrep_scan(".", semgrep_config="http://malicious.com/rules.yml")
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["check_id"], "SEMGREP_SCANNER_ERROR")
        self.assertTrue(
            "Refusing remote or URL-scheme" in findings[0]["message"]
            or "Refusing cleartext HTTP" in findings[0]["message"]
        )

    def test_file_helpers_strict_deps(self):
        # When PyYAML is absent (sys.modules['yaml'] = None raises ImportError) and
        # foreign toolchains exist on disk, _bootstrap_environment must NOT append
        # borrowed site-packages unless COMPLIANCE_ALLOW_BORROWED_DEPS is enabled.
        with (
            patch.dict(os.environ, {}, clear=True),
            patch.dict("sys.modules", {"yaml": None}),
            patch.object(file_helpers.glob, "glob", return_value=["/opt/foreign/site-packages"]),
            patch.object(file_helpers, "_append_validated_paths") as mock_append,
        ):
            file_helpers._bootstrap_environment()
            mock_append.assert_not_called()

        # When COMPLIANCE_STRICT_DEPS=1 is set, even explicit COMPLIANCE_SITE_PACKAGES is ignored.
        with (
            patch.dict(
                os.environ,
                {"COMPLIANCE_STRICT_DEPS": "1", "COMPLIANCE_SITE_PACKAGES": "/opt/custom/site-packages"},
                clear=True,
            ),
            patch.object(file_helpers, "_append_validated_paths") as mock_append_strict,
        ):
            file_helpers._bootstrap_environment()
            mock_append_strict.assert_not_called()

    def test_tool_path_validation(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            missing = tmp_dir / "missing_tool"
            self.assertFalse(ssb._is_safe_binary_path(missing))
            self.assertFalse(ssb._is_safe_binary_path(Path("relative/tool")))

            tool = tmp_dir / "mock_tool"
            tool.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")

            # Non-executable file must be rejected.
            os.chmod(tool, 0o600)
            self.assertFalse(ssb._is_safe_binary_path(tool))

            # Group-writable and world-writable executables must be rejected.
            os.chmod(tool, 0o770)
            self.assertFalse(ssb._is_safe_binary_path(tool))
            os.chmod(tool, 0o757)
            self.assertFalse(ssb._is_safe_binary_path(tool))

            # Owner-only executable regular file is accepted.
            os.chmod(tool, 0o700)
            self.assertTrue(ssb._is_safe_binary_path(tool))


if __name__ == "__main__":
    unittest.main()
