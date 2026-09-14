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

import unittest
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

import security_scanner_bridge as ssb
import file_helpers

class TestReviewScannerRegression(unittest.TestCase):
    def test_semgrep_http_rejection(self):
        findings = ssb.run_semgrep_scan(".", semgrep_config="http://malicious.com/rules.yml")
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["check_id"], "SEMGREP_SCANNER_ERROR")
        self.assertIn("Refusing cleartext HTTP", findings[0]["message"])

    def test_file_helpers_strict_deps(self):
        # By default COMPLIANCE_ALLOW_BORROWED_DEPS is not set, meaning strict deps is active
        # _bootstrap_environment shouldn't mutate sys.path with foreign toolchains
        with patch("os.environ.get", return_value=""):
            with patch("file_helpers._append_validated_paths") as mock_append:
                file_helpers._bootstrap_environment()
                mock_append.assert_not_called()

    def test_tool_path_validation(self):
        # Create a mock path
        candidate = Path("/tmp/mock_tool")
        if candidate.exists():
            candidate.unlink()
            
        # Should reject because it doesn't exist
        self.assertFalse(ssb._is_safe_binary_path(candidate))

if __name__ == "__main__":
    unittest.main()
