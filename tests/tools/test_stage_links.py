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
import pathlib
import subprocess
import tempfile
import unittest

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
_STAGE_LINKS = _REPO_ROOT / 'fast/stage-links.sh'


class TestStageLinksImpersonation(unittest.TestCase):

  def _run_stage_links(self, stage_dir_name, env_overrides=None):
    with tempfile.TemporaryDirectory() as tmpdir:
      stage_dir = pathlib.Path(tmpdir) / stage_dir_name
      stage_dir.mkdir(parents=True, exist_ok=True)
      outputs_dir = pathlib.Path(tmpdir) / 'outputs'
      outputs_dir.mkdir(parents=True, exist_ok=True)

      env = os.environ.copy()
      env.pop('GOOGLE_IMPERSONATE_SERVICE_ACCOUNT', None)
      env.pop('CLOUDSDK_AUTH_IMPERSONATE_SERVICE_ACCOUNT', None)
      if env_overrides:
        env.update(env_overrides)

      result = subprocess.run(
          ['bash', str(_STAGE_LINKS), str(outputs_dir)],
          cwd=str(stage_dir),
          env=env,
          capture_output=True,
          text=True,
          check=True,
      )
      return result.stdout

  def test_stage_impersonation_context_printed(self):
    expected_patterns = {
        '0-bootstrap': 'bootstrap-0',
        '1-resman': 'resman-0',
        '2-networking-a-fedramp': 'networking-0',
        '3-security': 'security-0',
    }
    for stage_name, sa_pattern in expected_patterns.items():
      with self.subTest(stage=stage_name):
        output = self._run_stage_links(stage_name)
        self.assertIn(
            f'expects *-{sa_pattern}@*.iam.gserviceaccount.com', output
        )
        self.assertNotIn('WARNING: Active shell impersonation', output)

  def test_warns_on_stale_cross_stage_impersonation_env_var(self):
    output = self._run_stage_links(
        '2-networking-a-fedramp',
        env_overrides={
            'GOOGLE_IMPERSONATE_SERVICE_ACCOUNT': (
                'test-prod-bootstrap-0@test-prod-iac-core-0.iam.gserviceaccount.com'
            )
        },
    )
    self.assertIn('WARNING: Active shell impersonation', output)
    self.assertIn(
        'unset GOOGLE_IMPERSONATE_SERVICE_ACCOUNT'
        ' CLOUDSDK_AUTH_IMPERSONATE_SERVICE_ACCOUNT',
        output,
    )

  def test_no_warning_when_impersonation_matches_stage(self):
    output = self._run_stage_links(
        '2-networking-a-fedramp',
        env_overrides={
            'GOOGLE_IMPERSONATE_SERVICE_ACCOUNT': (
                'test-prod-networking-0@test-prod-iac-core-0.iam.gserviceaccount.com'
            )
        },
    )
    self.assertNotIn('WARNING: Active shell impersonation', output)


if __name__ == '__main__':
  unittest.main()
