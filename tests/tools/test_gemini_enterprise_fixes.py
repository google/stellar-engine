# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for Gemini Enterprise compliance and deployment script fixes."""

import ast
import pathlib
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
GEM4GOV_PATH = (
    REPO_ROOT
    / "blueprints/fedramp-high/gemini-enterprise/gem4gov-cli/gem4gov.py"
)


class TestGeminiEnterpriseFixes(unittest.TestCase):
  """Verify Gemini Enterprise CLI, Terraform, and deploy.sh fixes."""

  def test_engine_patch_omits_immutable_disable_analytics(self):
    """Ensure update-compliance engine PATCH does not include immutable disableAnalytics (#259)."""
    content = GEM4GOV_PATH.read_text(encoding="utf-8")
    tree = ast.parse(content)
    self.assertNotIn(
        'engine_update_mask = "features,disableAnalytics"',
        content,
        "engine_update_mask must not include immutable disableAnalytics field",
    )

    for func_name in (
        "configure_gemini_enterprise_for_fedramp_high",
        "configure_gemini_enterprise_for_il4",
        "configure_gemini_enterprise_for_il5",
    ):
      func_node = next(
          node
          for node in tree.body
          if isinstance(node, ast.FunctionDef) and node.name == func_name
      )
      func_src = ast.get_source_segment(content, func_node)
      self.assertIn('engine_update_mask = "features"', func_src)
      self.assertNotIn('"disableAnalytics": True', func_src)
      self.assertIn("sys.exit(1)", func_src)

  def test_compliance_regime_respected_in_terraform_and_cli(self):
    """Ensure discovery-engine.tf and gem4gov.py respect compliance_regime (#190)."""
    tf_path = (
        REPO_ROOT
        / "blueprints/fedramp-high/gemini-enterprise/gemini-stage-0/discovery-engine.tf"
    )
    tf_content = tf_path.read_text(encoding="utf-8")
    self.assertIn("features = merge(", tf_content)
    self.assertIn('var.compliance_regime != "NONE" ? {', tf_content)

    py_content = GEM4GOV_PATH.read_text(encoding="utf-8")
    self.assertIn(
        "def create_engine(credentials, project_id, engine_id, display_name, company_name, data_store_list, enable_audit_logs=False, compliance_regime=None):",
        py_content,
    )
    self.assertIn("is_regulated = compliance_regime not in ('4', 'NONE')", py_content)
    self.assertNotIn("updateMask=agentConfigs", py_content)


if __name__ == "__main__":
  unittest.main()
