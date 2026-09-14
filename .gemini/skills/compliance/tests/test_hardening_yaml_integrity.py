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

"""Regression tests for structured-output integrity in the template engine.

These cover a defect class that unit tests missed entirely and only surfaced when
the real pipeline was executed: values crossing into a structured serialization
context (YAML) without escaping, producing deliverables that no parser can read.
"""

import sys
import unittest
from pathlib import Path

skill_root = Path(__file__).parent.parent
sys.path.insert(0, str(skill_root / "scripts"))

import file_helpers  # noqa: E402,F401  (bootstraps the dependency path)
import yaml  # noqa: E402
from template_engine import (  # noqa: E402
    TemplateEngine,
    _escape_yaml_double_quoted,
    _strip_html_badges,
)


class TestYamlScalarEscaping(unittest.TestCase):
    """A substituted value must never be able to break YAML structure."""

    def test_double_quote_is_escaped(self) -> None:
        self.assertEqual(_escape_yaml_double_quoted('say "hi"'), 'say \\"hi\\"')

    def test_backslash_is_escaped_before_quotes(self) -> None:
        """Backslash must be escaped first, or added escapes get double-escaped."""
        self.assertEqual(_escape_yaml_double_quoted('a\\"b'), 'a\\\\\\"b')

    def test_newlines_and_tabs_are_escaped(self) -> None:
        self.assertEqual(_escape_yaml_double_quoted("a\nb\tc"), "a\\nb\\tc")

    def test_other_control_characters_are_escaped(self) -> None:
        self.assertEqual(_escape_yaml_double_quoted("a\x07b"), "a\\x07b")

    def test_plain_text_is_unchanged(self) -> None:
        self.assertEqual(_escape_yaml_double_quoted("us-central1 (Iowa)"), "us-central1 (Iowa)")

    def test_escaped_output_round_trips_through_a_yaml_parser(self) -> None:
        """The escaping must produce a scalar that parses back to the original."""
        hostile = 'RTO: <mark style="color: #856404;">value</mark> "quoted" \\ back'
        document = f'key: "{_escape_yaml_double_quoted(hostile)}"'
        self.assertEqual(yaml.safe_load(document)["key"], hostile)


class TestHtmlBadgeStripping(unittest.TestCase):
    """Presentational markup must not reach machine-readable deliverables."""

    def test_badge_is_reduced_to_its_label(self) -> None:
        badge = '<mark style="background-color: #FFF3CD;">⚠️ [CONFIG_REQUIRED: RTO]</mark>'
        self.assertEqual(_strip_html_badges(badge), "⚠️ [CONFIG_REQUIRED: RTO]")

    def test_multiple_badges_are_all_stripped(self) -> None:
        text = '<mark style="a">one</mark> and <mark style="b">two</mark>'
        self.assertEqual(_strip_html_badges(text), "one and two")

    def test_text_without_badges_is_untouched(self) -> None:
        self.assertEqual(_strip_html_badges("no markup here"), "no markup here")


class TestYamlRenderingIntegrity(unittest.TestCase):
    """End-to-end: a YAML template must survive hostile substituted values."""

    def test_quoted_value_cannot_break_the_document(self) -> None:
        template = 'root:\n  detail: "Prefix {{ HOSTILE }} suffix"\n'
        engine = TemplateEngine(target_format="yaml")
        rendered = engine.render(
            template, {"{{ HOSTILE }}": 'has "double quotes" and a \\ backslash'}
        )
        parsed = yaml.safe_load(rendered)
        self.assertIn("double quotes", parsed["root"]["detail"])
        self.assertTrue(parsed["root"]["detail"].startswith("Prefix "))

    def test_badge_markup_does_not_corrupt_yaml(self) -> None:
        """The exact failure that made the SCTM matrix unparseable."""
        template = 'root:\n  detail: "RTO objective: {{ RTO }}."\n'
        badge = (
            '<mark style="background-color: #FFF3CD; color: #856404;">'
            "⚠️ [AI CONTEXTUAL EXAMPLE REQUIRED: Recovery Time Objective]</mark>"
        )
        engine = TemplateEngine(target_format="yaml")
        rendered = engine.render(template, {"{{ RTO }}": badge})
        parsed = yaml.safe_load(rendered)
        self.assertNotIn("<mark", parsed["root"]["detail"])
        self.assertIn("Recovery Time Objective", parsed["root"]["detail"])

    def test_markdown_target_still_renders_badges(self) -> None:
        """Stripping must be scoped to YAML; Markdown keeps its visual badges."""
        engine = TemplateEngine(target_format="markdown")
        rendered = engine.render(
            "Detail: {{ MISSING_VALUE }}", {"{{ MISSING_VALUE }}": ""}
        )
        self.assertIn("<mark", rendered)


if __name__ == "__main__":
    unittest.main()
