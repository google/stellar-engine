#!/usr/bin/env python3
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

"""Regression tests for DOCX and Template Engine hardening."""

import os
import sys
import unittest
import tempfile

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.abspath(os.path.join(TESTS_DIR, "..", "scripts"))
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

from template_engine import evaluate_template_conditionals
from docx_generator import DocxRelationshipManager, trim_trailing_punctuation, convert_markdown_to_docx
from audit_log import configure_audit_log, reset_audit_log

class TestHardeningDocs(unittest.TestCase):

    def test_evaluate_template_conditionals_single_pass(self):
        """Verify nested conditionals are evaluated correctly without ReDoS tricks."""
        template = """
<!-- IF A -->
line1
<!-- IF B -->
line2
<!-- ENDIF B -->
line3
<!-- ENDIF A -->
"""
        # A True, B True
        res1 = evaluate_template_conditionals(template, {"A": True, "B": True})
        self.assertIn("line1", res1)
        self.assertIn("line2", res1)
        self.assertIn("line3", res1)

        # A True, B False
        res2 = evaluate_template_conditionals(template, {"A": True, "B": False})
        self.assertIn("line1", res2)
        self.assertNotIn("line2", res2)
        self.assertIn("line3", res2)

        # A False, B True (should omit all)
        res3 = evaluate_template_conditionals(template, {"A": False, "B": True})
        self.assertNotIn("line1", res3)
        self.assertNotIn("line2", res3)
        self.assertNotIn("line3", res3)

    def test_docx_hyperlink_evasion(self):
        """Verify whitespace/control chars cannot bypass URL scheme checks."""
        mgr = DocxRelationshipManager()
        
        # Bypass via embedded space
        res1 = mgr.add_hyperlink("java script:alert(1)")
        self.assertEqual(res1, "")

        # Bypass via control char
        res2 = mgr.add_hyperlink("java\nscript:alert(1)")
        self.assertEqual(res2, "")

        # Bypass via relative path trick
        res3 = mgr.add_hyperlink("java script:alert(1)#.html")
        self.assertEqual(res3, "")

        # Valid link works
        res4 = mgr.add_hyperlink("https://example.com")
        self.assertNotEqual(res4, "")

    def test_trim_trailing_punctuation_performance(self):
        """Verify O(n^2) fix in trim_trailing_punctuation."""
        url = "http://example.com" + ")" * 1000
        clean, trailing = trim_trailing_punctuation(url)
        self.assertEqual(clean, "http://example.com")
        self.assertEqual(trailing, ")" * 1000)

    def test_docx_audit_logging(self):
        """Verify that zip creation emits an audit log event."""
        with tempfile.TemporaryDirectory() as td:
            log_path = os.path.join(td, "audit.jsonl")
            configure_audit_log(sink_path=log_path, component="test")
            # The sink is process-wide; drop it before `td` is removed, or later
            # events in this interpreter would recreate the deleted directory.
            self.addCleanup(reset_audit_log)

            out_path = os.path.join(td, "out.docx")
            convert_markdown_to_docx("# Test", out_path)

            with open(log_path, "r") as f:
                logs = f.read()
            self.assertIn("artifact.generated", logs)
            self.assertIn("out.docx", logs)
            self.assertIn("docx", logs)

if __name__ == "__main__":
    unittest.main()
