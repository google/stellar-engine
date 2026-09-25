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

import pathlib
import re
import unittest

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
_WORKFLOW_TEMPLATES = (
    _REPO_ROOT / 'fast/stages-aw/0-bootstrap/templates/workflow-github.yaml',
    _REPO_ROOT / 'fast/stages-aw/1-resman/templates/workflow-github.yaml',
    _REPO_ROOT / 'fast/assets/templates/workflow-github.yaml',
)
_DIRECT_STEP_OUTPUT_IN_SCRIPT_RE = re.compile(
    r'script:\s*\|[\s\S]*?\$\$\{\{\s*steps\.[^}]+\.outputs\.[^}]+\}\}'
)


class TestWorkflowTemplatesSecurity(unittest.TestCase):

  def test_tf_validate_stdout_passed_via_env_in_github_script(self):
    for template_path in _WORKFLOW_TEMPLATES:
      with self.subTest(template=str(template_path.relative_to(_REPO_ROOT))):
        content = template_path.read_text(encoding='utf-8')
        self.assertIn(
            'tf_validate: $${{steps.tf-validate.outputs.stdout}}', content
        )
        self.assertIn('$${process.env.tf_validate}', content)
        self.assertNotIn(
            '            $${{steps.tf-validate.outputs.stdout}}', content
        )
        self.assertIsNone(
            _DIRECT_STEP_OUTPUT_IN_SCRIPT_RE.search(content),
            'Step outputs must be passed via env rather than interpolated'
            ' directly into github-script blocks.',
        )


if __name__ == '__main__':
  unittest.main()
