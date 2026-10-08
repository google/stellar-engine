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
import shutil
import sys
import tempfile
import unittest
import zipfile
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))

import validate_compliance_artifacts
import oscal_generator


class _StopValidation(Exception):
    """Sentinel used to abort a run at a specific seam.

    A dedicated type keeps the test from accidentally passing on a genuine
    failure raised by the code under test.
    """


class TestHardeningValidate(unittest.TestCase):
    def test_docx_zip_bomb(self):
        with tempfile.TemporaryDirectory() as td:
            tf_path = os.path.join(td, "test.docx")
            with zipfile.ZipFile(tf_path, "w") as z:
                z.writestr("word/document.xml", "test")
            
            with patch("zipfile.ZipFile.getinfo") as mock_getinfo:
                mock_info = MagicMock()
                mock_info.file_size = 101 * 1024 * 1024 # > 100MB
                mock_info.compress_size = 100
                mock_getinfo.return_value = mock_info
                
                results = validate_compliance_artifacts.audit_docx_policies(td)
                self.assertEqual(len(results), 1)
                self.assertEqual(results[0]["status"], "UNVERIFIED")
                self.assertIn("exceeds safe size/compression", results[0]["issues"][0])

    def test_oscal_deterministic_uuid_fips(self):
        # UUID should be formatted properly as a string
        uuid_val = oscal_generator._deterministic_uuid("test-string")
        self.assertTrue(isinstance(uuid_val, str))
        self.assertEqual(len(uuid_val), 36)
        
        import uuid
        parsed = uuid.UUID(uuid_val)
        self.assertEqual(parsed.version, 4)

    def test_ssp_text_redos_fix(self):
        # Ensure audit_senior_compliance_quality doesn't crash on long texts
        target_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, target_dir, True)
        ato_dir = os.path.join(target_dir, "ato_artifacts")
        ssp_dir = os.path.join(ato_dir, "SSP")
        os.makedirs(ssp_dir)
        ssp_md = os.path.join(ssp_dir, "System_Security_Plan.md")

        content = "### SC-7 \nSome long text here\n" + ("x" * 10000) + "\n### SC-8\n"
        with open(ssp_md, "w") as f:
            f.write(content)

        # Test it processes
        res = validate_compliance_artifacts.audit_senior_compliance_quality(
            target_dir=target_dir,
            inventory={},
            ato_dir=ato_dir,
            alignment_res={"discrepancies": []},
            excel_results=[],
            docx_results=[],
            oscal_results=[],
            unresolved_tokens=[],
            config_required_vars=[],
            stigs_required=[],
            rmf_action_items=[]
        )
        self.assertIn("atc_records", res)

    def test_subprocess_command_injection_prevention(self):
        """A target directory that looks like a CLI flag must not be parsed as one."""
        # The target path is relative, so the validator materializes directories
        # beneath the current working directory. Run inside a throwaway cwd so the
        # test cannot leave a literal '-evil-flag' tree in the repository.
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory(prefix="compliance-injection-test-") as sandbox_cwd:
            try:
                os.chdir(sandbox_cwd)
                with patch("subprocess.run") as mock_run, \
                        patch("os.path.exists", return_value=True), \
                        patch("shutil.copytree"), \
                        patch("validate_compliance_artifacts.read_json_file", return_value={"dummy": "data"}):
                    # Abort the run at the first subprocess boundary; we only care
                    # about the argv that was about to be executed.
                    mock_run.side_effect = _StopValidation("halt after first subprocess call")
                    with self.assertRaises(_StopValidation):
                        validate_compliance_artifacts.validate_compliance_package("-evil-flag", fix_drift=True)
            finally:
                os.chdir(original_cwd)

        self.assertTrue(
            mock_run.called,
            "validate_compliance_package never reached subprocess.run; the argv assertion below "
            "would silently vacuous-pass, so fail loudly instead.",
        )
        call_args = mock_run.call_args[0][0]
        self.assertIn("--", call_args, f"missing end-of-options separator in {call_args!r}")
        self.assertLess(
            call_args.index("--"),
            len(call_args) - 1,
            f"'--' must precede the operand, not trail it: {call_args!r}",
        )
        self.assertTrue(call_args[-1].endswith("-evil-flag"))

    def test_injection_test_leaves_no_residue(self):
        """The injection test must not create a '-evil-flag' directory in the repo."""
        skill_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        for probe_root in (skill_root, os.getcwd()):
            residue = os.path.join(probe_root, "-evil-flag")
            self.assertFalse(
                os.path.exists(residue),
                f"test residue directory was left behind at {residue}",
            )

if __name__ == "__main__":
    unittest.main()
