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

"""One placeholder vocabulary shared by the template engine, validator and linter."""

from pathlib import Path
import re
import unittest

from compliance_engine import oscal_generator
from compliance_engine import semantic_linter
from compliance_engine import template_engine
from compliance_engine import validate_compliance_artifacts
from compliance_engine.template_engine import TemplateEngine


class PlaceholderDetectionTest(unittest.TestCase):
    """PENDING_PLACEHOLDER_RE / contains_unfilled_placeholder cover every token the engine writes."""

    def test_pending_regex_cases(self) -> None:
        pending = [
            "[CONFIG_REQUIRED: ISSO Name]",
            "[CONFIG_REQUIRED]",
            "[EXAMPLE_DATA_REQUIRED: AO]",
            "[NOT DETERMINED FROM SOURCE]",
            "[NOT DETERMINED FROM SOURCE: region]",
            "[ISSM_NAME]",
            "[AO_EMAIL]",
            "[YOUR_ORG_NAME]",
            "[YYYY-MM-DD]",
            "FR-XXXXXXXX",
            "FR9999999999",
        ]
        for text in pending:
            with self.subTest(text=text):
                self.assertTrue(template_engine.contains_unfilled_placeholder(f"Value: {text}."))
        for text in ("[REDACTED_SENSITIVE]", "[r5] AC-2", "> [!NOTE]", "[AC-2]", "FR1805751477", "plain text"):
            with self.subTest(text=text):
                self.assertFalse(template_engine.contains_unfilled_placeholder(text))

    def test_not_determined_preserved(self) -> None:
        engine = TemplateEngine(target_format="markdown")
        marker = "[NOT DETERMINED FROM SOURCE] No subnet CIDR ranges were found."
        self.assertEqual(engine.render("{{ SUBNET_BOUNDARY_TABLE }}", {"SUBNET_BOUNDARY_TABLE": marker}), marker)
        yaml_engine = TemplateEngine(target_format="yaml")
        self.assertIn("[NOT DETERMINED FROM SOURCE]", yaml_engine.render('key: "{{ X }}"', {"X": marker}))
        self.assertIn("[CONFIG_REQUIRED", TemplateEngine(target_format="markdown", fill_examples=False).render("{{ X }}", {"X": None}))

    def test_validator_oscal_versions_match_generator(self) -> None:
        self.assertIs(validate_compliance_artifacts.SUPPORTED_OSCAL_VERSIONS, oscal_generator.SUPPORTED_OSCAL_VERSIONS)
        for ver in ("1.0.1", "1.0.2", "1.0.3"):
            self.assertIn(ver, validate_compliance_artifacts.SUPPORTED_OSCAL_VERSIONS)

    def test_consumers_share_one_pattern(self) -> None:
        self.assertIs(validate_compliance_artifacts.PENDING_PLACEHOLDER_RE, template_engine.PENDING_PLACEHOLDER_RE)
        ok, status, _ = semantic_linter.evaluate_control_substance(
            "AC-3", "Access is enforced by IAM roles bound to [ISSM_NAME] groups across the project boundary.", {}
        )
        self.assertFalse(ok)
        self.assertIn("Untailored", status)
        pkg = Path(template_engine.__file__).parent
        hits = [
            f"{p.name}:{n}"
            for p in sorted(pkg.glob("*.py"))
            if p.name != "template_engine.py"
            for n, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1)
            if re.search(r"re\.(?:compile|sub|search)\(r?\"\\\\\[CONFIG_REQUIRED", line)
        ]
        self.assertEqual(hits, [])


if __name__ == "__main__":
    unittest.main()
