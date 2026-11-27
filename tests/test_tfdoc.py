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
import tempfile
import unittest

import tfdoc


class TestTfDoc(unittest.TestCase):
    def test_tftest_directive(self):
        directive = tfdoc.get_tftest_directive(
            "module {}\n# tftest modules=3 resources=12 inventory=a.yaml\n"
        )
        self.assertIsNotNone(directive)
        self.assertEqual(directive.name, "tftest")
        self.assertEqual(directive.kwargs["modules"], "3")
        self.assertEqual(directive.kwargs["resources"], "12")
        self.assertEqual(directive.kwargs["inventory"], "a.yaml")

    def test_tftest_directive_with_files_and_fixtures(self):
        directive = tfdoc.get_tftest_directive(
            "# tftest fixtures=fixtures/gcs.tf files=f1,f2 modules=1 e2e\n"
        )
        self.assertEqual(directive.kwargs["files"], "f1,f2")
        self.assertEqual(directive.kwargs["fixtures"], "fixtures/gcs.tf")
        self.assertEqual(directive.args, ["e2e"])
        self.assertIsNone(tfdoc.get_tftest_directive("# no directive\n"))

    def test_parse_fixtures_links_synced_fixtures(self):
        module = os.path.join(tfdoc.REPO_ROOT, "modules", "pubsub")
        readme = (
            "```hcl\nmodule {}\n"
            "# tftest modules=1 resources=1 fixtures=fixtures/gcs.tf\n```\n"
        )
        fixtures = list(tfdoc.parse_fixtures(module, readme))
        self.assertEqual(fixtures, ["../../tests/fixtures/gcs.tf"])
        self.assertIn(
            "- [gcs.tf](../../tests/fixtures/gcs.tf)",
            list(tfdoc.format_tfref_fixtures(fixtures)),
        )

    def test_parse_fixtures_rejects_unknown_fixtures(self):
        readme = (
            "```hcl\nmodule {}\n"
            "# tftest modules=1 resources=1 fixtures=fixtures/missing.tf\n"
            "```\n"
        )
        with self.assertRaises(SystemExit):
            list(tfdoc.parse_fixtures(tfdoc.REPO_ROOT, readme))

    def test_tag_re(self):
        tag_line = "# tfdoc:variable:source fast/stages-aw/0-bootstrap"
        m = tfdoc.TAG_RE.match(tag_line)
        self.assertIsNotNone(m)
        self.assertEqual(m.group(1), "variable:source")
        self.assertEqual(m.group(2), "fast/stages-aw/0-bootstrap")

    def test_get_tfref_opts(self):
        self.assertEqual(
            tfdoc.get_tfref_opts("<!-- TFDOC OPTS files:1 -->"),
            {"files": True},
        )
        self.assertEqual(
            tfdoc.get_tfref_opts(
                "<!-- TFDOC OPTS files:1 show_extra:0 exclude:outputs.tf -->"
            ),
            {"files": True, "show_extra": False, "exclude": "outputs.tf"},
        )
        self.assertEqual(
            tfdoc.get_tfref_opts("<!-- TFDOC OPTS _:" + "!_:" * 500),
            {},
        )

    def test_file_desc_defaults(self):
        self.assertIn("main.tf", tfdoc.FILE_DESC_DEFAULTS)
        self.assertIn("variables.tf", tfdoc.FILE_DESC_DEFAULTS)
        self.assertIn("outputs.tf", tfdoc.FILE_DESC_DEFAULTS)
        self.assertIn("versions.tf", tfdoc.FILE_DESC_DEFAULTS)

    def test_variable_regex_parsing(self):
        sample_var = """
variable "project_id" {
  description = "The GCP project ID."
  type        = string
}
"""
        items = list(tfdoc._parse(sample_var))
        self.assertEqual(len(items), 1)
        item = items[0]
        self.assertEqual(item["name"], "project_id")
        self.assertIn("The GCP project ID.", "".join(item["description"]))

    def test_output_regex_parsing(self):
        sample_out = """
output "vpc_id" {
  description = "The VPC network self link."
  value       = google_compute_network.main.id
}
"""
        items = list(
            tfdoc._parse(
                sample_out,
                enum=tfdoc.OUT_ENUM,
                re=tfdoc.OUT_RE,
                template=tfdoc.OUT_TEMPLATE,
            )
        )
        self.assertEqual(len(items), 1)
        item = items[0]
        self.assertEqual(item["name"], "vpc_id")
        self.assertIn(
            "The VPC network self link.", "".join(item["description"])
        )

    def test_parse_files_skips_symlinks(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            real_tf = os.path.join(tmpdir, "main.tf")
            with open(real_tf, "w", encoding="utf-8") as f:
                f.write("# main\n")
            ext_tf = os.path.join(tmpdir, "external.txt")
            with open(ext_tf, "w", encoding="utf-8") as f:
                f.write("# external\n")
            os.symlink(ext_tf, os.path.join(tmpdir, "linked.tf"))
            files = list(tfdoc.parse_files(tmpdir))
            self.assertEqual(len(files), 1)
            self.assertEqual(files[0].name, "main.tf")

    def test_create_and_render_tfref_generates_expected_tables(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            vars_path = os.path.join(tmpdir, "variables.tf")
            with open(vars_path, "w", encoding="utf-8") as f:
                f.write(
                    'variable "project_id" {\n'
                    '  description = "Project ID."\n'
                    "  type        = string\n"
                    "}\n"
                )
            outs_path = os.path.join(tmpdir, "outputs.tf")
            with open(outs_path, "w", encoding="utf-8") as f:
                f.write(
                    'output "id" {\n'
                    '  description = "Output ID."\n'
                    "  value       = var.project_id\n"
                    "  sensitive   = true\n"
                    "}\n"
                )
            doc = tfdoc.create_tfref(
                tmpdir, files=False, show_extra=False, readme=""
            )
            rendered = tfdoc.render_tfref(
                f"# Mod\n{tfdoc.MARK_BEGIN}\n{tfdoc.MARK_END}\n", doc.content
            )
            self.assertIn(
                "| [project_id](variables.tf#L1) | Project ID."
                " | <code>string</code> | ✓ |  |",
                rendered,
            )
            self.assertIn("| [id](outputs.tf#L1) | Output ID. | ✓ |", rendered)

    def test_variable_inline_comments_and_quotes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            vars_path = os.path.join(tmpdir, "variables.tf")
            with open(vars_path, "w", encoding="utf-8") as f:
                f.write(
                    'variable "image" { # container image override\n'
                    "  # tfdoc:variable:source fast/stages-aw/0-bootstrap\n"
                    '  description = "Keep #1 and https://example.com."\n'
                    "  type        = string # image name\n"
                    '  default     = "ENTERPRISE" # requires autoscaling\n'
                    "}\n"
                    'variable "notes" {\n'
                    '  description = "Multiline script."\n'
                    "  type        = string\n"
                    "  default     = <<-END // heredoc opener note\n"
                    "    echo ok # keep heredoc comment\n"
                    "  END\n"
                    "}\n"
                )
            stripped = tfdoc._strip_inline_comments(
                "default = <<-END // strip\n# keep heredoc comment\nEND\n"
            )
            self.assertIn("# keep heredoc comment", stripped)
            self.assertNotIn("// strip", stripped)

            parsed = list(tfdoc.parse_variables(tmpdir))
            self.assertEqual(len(parsed), 2)
            image = parsed[0]
            self.assertEqual(image.name, "image")
            self.assertEqual(image.line, 1)
            self.assertEqual(
                image.description, "Keep #1 and https://example.com."
            )
            self.assertEqual(image.type, "string")
            self.assertEqual(image.default, '"ENTERPRISE"')
            self.assertEqual(image.source, "fast/stages-aw/0-bootstrap")
            self.assertFalse(image.required)

            notes = parsed[1]
            self.assertEqual(notes.line, 7)
            self.assertIn("echo ok # keep heredoc comment", notes.default)

    def test_variable_blank_line_before_default_or_nullable(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            vars_path = os.path.join(tmpdir, "variables.tf")
            with open(vars_path, "w", encoding="utf-8") as f:
                f.write(
                    'variable "feature_settings" {\n'
                    '  description = "Feature settings."\n'
                    "  type = object({\n"
                    "    enabled = optional(bool, true)\n"
                    "  })\n"
                    "\n"
                    "  nullable = true\n"
                    "  default  = {}\n"
                    "}\n"
                    'variable "cleanup_policies" {\n'
                    '  description = "Cleanup policies."\n'
                    "  type = map(object({\n"
                    "    action = string\n"
                    "  }))\n"
                    "\n"
                    "  default = null\n"
                    "}\n"
                )
            parsed = {v.name: v for v in tfdoc.parse_variables(tmpdir)}
            fs = parsed["feature_settings"]
            self.assertEqual(
                fs.type, "object({\n    enabled = optional(bool, true)\n  })"
            )
            self.assertFalse(fs.required)
            self.assertEqual(fs.default, "{}")

            cp = parsed["cleanup_policies"]
            self.assertEqual(
                cp.type, "map(object({\n    action = string\n  }))"
            )
            self.assertFalse(cp.required)
            self.assertEqual(cp.default, "null")

    def test_output_depends_on_after_description(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            outs_path = os.path.join(tmpdir, "outputs.tf")
            with open(outs_path, "w", encoding="utf-8") as f:
                f.write(
                    'output "endpoint" {\n'
                    '  description = "Endpoint IP."\n'
                    "  depends_on = [\n"
                    "    google_compute_forwarding_rule.default\n"
                    "  ]\n"
                    "  value = google_compute_address.default.address\n"
                    "}\n"
                )
            parsed = list(tfdoc.parse_outputs(tmpdir))
            self.assertEqual(len(parsed), 1)
            self.assertEqual(parsed[0].name, "endpoint")
            self.assertEqual(parsed[0].description, "Endpoint IP.")


if __name__ == "__main__":
    unittest.main()
