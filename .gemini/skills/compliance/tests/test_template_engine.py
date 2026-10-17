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

"""Unit test suite for template_engine.py."""

import os
import sys
import unittest

SCRIPTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts"))
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

from file_helpers import _bootstrap_environment
_bootstrap_environment()
import yaml

from template_engine import (
    TemplateEngine,
    evaluate_template_conditionals,
)


class TestTemplateEngine(unittest.TestCase):
    """Unit test suite for TemplateEngine and template evaluation helpers."""

    def test_evaluate_template_conditionals_multi_syntax(self) -> None:
        """Tests conditional evaluation across HTML comment, Mustache, and Jinja syntax."""
        # 1. HTML Comment syntax
        html_src = (
            "Start\n"
            "<!-- IF SCC_ENABLED -->\n"
            "SCC Active\n"
            "<!-- ENDIF -->\n"
            "<!-- IF NOT SCC_ENABLED -->\n"
            "SCC Inactive\n"
            "<!-- ENDIF -->\n"
            "End"
        )
        res_html_on = evaluate_template_conditionals(html_src, {"SCC_ENABLED": True})
        self.assertIn("SCC Active", res_html_on)
        self.assertNotIn("SCC Inactive", res_html_on)

        res_html_off = evaluate_template_conditionals(html_src, {"SCC_ENABLED": False})
        self.assertNotIn("SCC Active", res_html_off)
        self.assertIn("SCC Inactive", res_html_off)

        # 2. Mustache syntax
        mustache_src = (
            "{{#IF SECOPS_ENABLED}}\n"
            "SecOps Enclave Active\n"
            "{{/IF}}\n"
            "{{#IF_NOT SECOPS_ENABLED}}\n"
            "External SIEM Active\n"
            "{{/IF_NOT}}"
        )
        res_mustache_on = evaluate_template_conditionals(mustache_src, {"SECOPS_ENABLED": True})
        self.assertIn("SecOps Enclave Active", res_mustache_on)
        self.assertNotIn("External SIEM Active", res_mustache_on)

        res_mustache_off = evaluate_template_conditionals(mustache_src, {"SECOPS_ENABLED": False})
        self.assertNotIn("SecOps Enclave Active", res_mustache_off)
        self.assertIn("External SIEM Active", res_mustache_off)

        # 3. Jinja syntax
        jinja_src = (
            "{% if DOD_ENCLAVE %}\n"
            "DoD SRG IL5 Controls Applied\n"
            "{% endif %}\n"
            "{% if not DOD_ENCLAVE %}\n"
            "FedRAMP High Baseline Applied\n"
            "{% endif %}"
        )
        res_jinja_dod = evaluate_template_conditionals(jinja_src, {"DOD_ENCLAVE": True})
        self.assertIn("DoD SRG IL5 Controls Applied", res_jinja_dod)
        self.assertNotIn("FedRAMP High Baseline Applied", res_jinja_dod)

        res_jinja_fedramp = evaluate_template_conditionals(jinja_src, {"DOD_ENCLAVE": False})
        self.assertNotIn("DoD SRG IL5 Controls Applied", res_jinja_fedramp)
        self.assertIn("FedRAMP High Baseline Applied", res_jinja_fedramp)

        # 4. Nested conditionals
        nested_src = (
            "<!-- IF ROOT_FLAG -->\n"
            "Outer Enabled\n"
            "  {% if INNER_FLAG %}\n"
            "  Inner Enabled\n"
            "  {% endif %}\n"
            "<!-- ENDIF -->"
        )
        res_nested_both = evaluate_template_conditionals(nested_src, {"ROOT_FLAG": True, "INNER_FLAG": True})
        self.assertIn("Outer Enabled", res_nested_both)
        self.assertIn("Inner Enabled", res_nested_both)

        res_nested_outer_only = evaluate_template_conditionals(nested_src, {"ROOT_FLAG": True, "INNER_FLAG": False})
        self.assertIn("Outer Enabled", res_nested_outer_only)
        self.assertNotIn("Inner Enabled", res_nested_outer_only)

    def test_render_markdown_direct_badges(self) -> None:
        """Tests Markdown document rendering with bracketed badge notation for missing vars."""
        engine = TemplateEngine(target_format="markdown", fill_examples=True)

        template = (
            "# System {{ SYSTEM_NAME }}\n"
            "Organization: {{   ORGANIZATION_NAME   }}\n"
            "Abbreviation: { SYSTEM_ABBR }\n"
            "KMS CMEK: {{ KMS_KEY_NAME }}\n"
            "Regex Key: {{ CRYPTO_REGEX }}"
        )

        context = {
            "SYSTEM_NAME": "Tactical Intelligence Hub",
            "SYSTEM_ABBR": "TIH",
            "CRYPTO_REGEX": r"AES-256-GCM with \1 \g<0> path\to\key",
            # ORGANIZATION_NAME and KMS_KEY_NAME are missing
        }

        rendered = engine.render(template, context)

        # Verified tokens replaced
        self.assertIn("# System Tactical Intelligence Hub", rendered)
        self.assertIn("Abbreviation: TIH", rendered)
        self.assertIn(r"AES-256-GCM with \1 \g<0> path\to\key", rendered)

        # Missing tokens directly render bracketed badges without HTML mark tags
        self.assertNotIn("<mark", rendered)
        self.assertIn("[EXAMPLE_DATA_REQUIRED: Organization Name]", rendered)
        self.assertIn("[EXAMPLE_DATA_REQUIRED: Kms Key Name]", rendered)

    def test_render_yaml_safe_quotes(self) -> None:
        """Tests YAML deliverable rendering where missing placeholders directly produce valid safe scalars."""
        engine = TemplateEngine(target_format="yaml", fill_examples=True)

        template = (
            "system_metadata:\n"
            '  system_name: "{{ SYSTEM_NAME }}"\n'
            '  system_abbr: "{{ SYSTEM_ABBR }}"\n'
            "  impact_level: {{ IMPACT_LEVEL }}\n"
            '  organization: "{{ ORGANIZATION_NAME }}"\n'
            "  primary_location: {{ PRIMARY_LOCATION }}\n"
        )

        context = {
            "SYSTEM_NAME": "Tactical Intelligence Hub",
            "SYSTEM_ABBR": "TIH",
            # IMPACT_LEVEL, ORGANIZATION_NAME, PRIMARY_LOCATION are missing
        }

        rendered = engine.render(template, context)

        # Must not contain HTML mark tags
        self.assertNotIn("<mark", rendered)

        # Must not contain doubled quotes like ""[...]""
        self.assertNotIn('""[EXAMPLE_DATA_REQUIRED', rendered)

        # Must parse as clean, valid YAML
        parsed = yaml.safe_load(rendered)
        self.assertEqual(parsed["system_metadata"]["system_name"], "Tactical Intelligence Hub")
        self.assertEqual(parsed["system_metadata"]["system_abbr"], "TIH")
        self.assertEqual(
            parsed["system_metadata"]["impact_level"],
            "[EXAMPLE_DATA_REQUIRED: Impact Level]",
        )
        self.assertEqual(
            parsed["system_metadata"]["organization"],
            "[EXAMPLE_DATA_REQUIRED: Organization Name]",
        )
        self.assertEqual(
            parsed["system_metadata"]["primary_location"],
            "[EXAMPLE_DATA_REQUIRED: Primary Location]",
        )

        # Test embedded tokens inside larger quoted YAML string
        embedded_template = 'implementation_details: "RTO objective: {{ RTO }} and RPO: {{ RPO }}"\n'
        rendered_embedded = engine.render(embedded_template, {})
        self.assertNotIn('""[AI', rendered_embedded)
        parsed_emb = yaml.safe_load(rendered_embedded)
        self.assertEqual(
            parsed_emb["implementation_details"],
            "RTO objective: [EXAMPLE_DATA_REQUIRED: Rto] and RPO: [EXAMPLE_DATA_REQUIRED: Rpo]",
        )

    def test_filter_pipeline(self) -> None:
        """Tests variable expression filter pipeline (| default, | upper, | lower, | title)."""
        engine = TemplateEngine(target_format="markdown")

        template = (
            "Cluster: {{ CLUSTER_NAME | default('gke-production-enclave') }}\n"
            "Upper: {{ APP_ENV | upper }}\n"
            "Lower: {{ CLOUD_PROVIDER | lower }}\n"
            "Title: {{ SERVICE_NAME | title }}"
        )

        context = {
            # CLUSTER_NAME is missing, should use default
            "APP_ENV": "production",
            "CLOUD_PROVIDER": "GOOGLE CLOUD PLATFORM",
            "SERVICE_NAME": "cloud logging router",
        }

        rendered = engine.render(template, context)
        self.assertIn("Cluster: gke-production-enclave", rendered)
        self.assertIn("Upper: PRODUCTION", rendered)
        self.assertIn("Lower: google cloud platform", rendered)
        self.assertIn("Title: Cloud Logging Router", rendered)

    def test_hydrate_legacy_placeholders(self) -> None:
        """Tests backward-compatible legacy placeholder hydration on existing file content."""
        yaml_content = (
            "system:\n"
            "  name: [CONFIG_REQUIRED: System Name]\n"
            '  quoted_name: "[CONFIG_REQUIRED: Quoted Name]"\n'
            "  owner:\n"
            "    email: [CONFIG_REQUIRED: Owner Email]\n"
        )
        md_content = "# System [CONFIG_REQUIRED: System Name]\nOwner: [CONFIG_REQUIRED: Owner Email]"

        # Hydrate YAML
        hydrated_yaml = TemplateEngine.hydrate_legacy_placeholders(yaml_content, is_yaml=True)
        self.assertNotIn("<mark", hydrated_yaml)
        parsed_yaml = yaml.safe_load(hydrated_yaml)
        self.assertEqual(parsed_yaml["system"]["name"], "[EXAMPLE_DATA_REQUIRED: System Name]")
        self.assertEqual(parsed_yaml["system"]["quoted_name"], "[EXAMPLE_DATA_REQUIRED: Quoted Name]")
        self.assertEqual(parsed_yaml["system"]["owner"]["email"], "[EXAMPLE_DATA_REQUIRED: Owner Email]")

        # Hydrate Markdown
        hydrated_md = TemplateEngine.hydrate_legacy_placeholders(md_content, is_yaml=False)
        self.assertNotIn("<mark", hydrated_md)
        self.assertIn("[EXAMPLE_DATA_REQUIRED: System Name]", hydrated_md)
        self.assertIn("[EXAMPLE_DATA_REQUIRED: Owner Email]", hydrated_md)

    def test_inline_conditional_preserves_table_row_newline(self) -> None:
        """Inline <!-- IF ... -->...<!-- ENDIF --> inside a table row must not strip spaces or row newlines."""
        table_src = (
            "| Col A | Col B |\n"
            "| --- | --- |\n"
            "| IA-5(1) | Report to <!-- IF DOD_ENCLAVE -->USCYBERCOM<!-- ENDIF --><!-- IF NOT DOD_ENCLAVE -->CISA<!-- ENDIF --> |\n"
            "| IA-6 | Mask authenticators |\n"
        )
        dod_out = evaluate_template_conditionals(table_src, {"DOD_ENCLAVE": True})
        self.assertEqual(
            dod_out,
            "| Col A | Col B |\n"
            "| --- | --- |\n"
            "| IA-5(1) | Report to USCYBERCOM |\n"
            "| IA-6 | Mask authenticators |\n",
        )
        civ_out = evaluate_template_conditionals(table_src, {"DOD_ENCLAVE": False})
        self.assertEqual(
            civ_out,
            "| Col A | Col B |\n"
            "| --- | --- |\n"
            "| IA-5(1) | Report to CISA |\n"
            "| IA-6 | Mask authenticators |\n",
        )
        indented_inline = "    <!-- IF DOD_ENCLAVE -->USCYBERCOM<!-- ENDIF --> and CISA\nNext line"
        self.assertEqual(
            evaluate_template_conditionals(indented_inline, {"DOD_ENCLAVE": True}),
            "    USCYBERCOM and CISA\nNext line",
        )

    def test_unbalanced_conditional_raises(self) -> None:
        """Unclosed IF or extra ENDIF tags must raise ValueError instead of silently truncating."""
        with self.assertRaises(ValueError):
            evaluate_template_conditionals("Header\n<!-- IF DOD_ENCLAVE -->\nBody", {"DOD_ENCLAVE": False})
        with self.assertRaises(ValueError):
            evaluate_template_conditionals("Header\n<!-- ENDIF -->\nBody", {"DOD_ENCLAVE": True})

    def test_inline_values_escaped(self) -> None:
        """Inline fields normalize CR/LF and escape Markdown block/table triggers."""
        engine = TemplateEngine(target_format="markdown")
        tpl = (
            "Organization: {{ ORGANIZATION }}\n"
            "| Field | Value |\n"
            "| --- | --- |\n"
            "| Org | {{ ORGANIZATION }} |\n"
            "{{ ORGANIZATION }} mandates logging.\n"
        )
        rendered = engine.render(tpl, {"ORGANIZATION": "A\n# X | Injected"})
        for line in rendered.splitlines():
            self.assertFalse(line.startswith("# X"), f"Heading injected via newline: {line!r}")
        table_row = [ln for ln in rendered.splitlines() if ln.startswith("| Org |")][0]
        self.assertEqual(table_row, r"| Org | A # X \| Injected |")

    def test_unc_links_not_emitted(self) -> None:
        """Unsafe Markdown link schemes (UNC, file://, javascript:) are stripped in rendered Markdown."""
        engine = TemplateEngine(target_format="markdown")
        tpl = "Description: {{ SYSTEM_DESCRIPTION }}\nContact: {{ CONTACT_INFO }}\n"
        ctx = {
            "SYSTEM_DESCRIPTION": "See [UNC](\\\\evil.example\\share\\x.docx) and [Local](file:///etc/hostname) and [Safe](https://www.nist.gov/rmf).",
            "CONTACT_INFO": "[Bad](javascript:alert(1))",
        }
        rendered = engine.render(tpl, ctx)
        self.assertNotIn("](\\\\", rendered)
        self.assertNotIn("](file://", rendered)
        self.assertNotIn("](javascript:", rendered)
        self.assertIn("[Safe](https://www.nist.gov/rmf)", rendered)


if __name__ == "__main__":
    unittest.main(verbosity=2)
