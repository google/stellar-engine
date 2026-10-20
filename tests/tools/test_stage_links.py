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

  def _sa(self, account_id):
    return f'{account_id}@test-prod-iac-core-0.iam.gserviceaccount.com'

  def test_stage_impersonation_context_printed(self):
    # account ID suffixes come from 0-bootstrap/automation.tf and
    # 1-resman/branch-networking.tf and 1-resman/branch-security.tf
    expected_patterns = {
        '0-bootstrap': ('bootstrap-0', 'bootstrap-0r'),
        '1-resman': ('resman-0', 'resman-0r'),
        '2-networking-a-fedramp': ('prod-resman-net-0', 'prod-resman-net-0r'),
        '2-networking-b-il5-ngfw': ('prod-resman-net-0', 'prod-resman-net-0r'),
        '3-security': ('security-0', 'prod-resman-sec-0r'),
    }
    for stage_name, (sa_pattern, ro_pattern) in expected_patterns.items():
      with self.subTest(stage=stage_name):
        output = self._run_stage_links(stage_name)
        self.assertIn(f'expects *-{sa_pattern}@*.iam.gserviceaccount.com',
                      output)
        self.assertIn(
            f'or the read-only *-{ro_pattern}@*.iam.gserviceaccount.com',
            output,
        )
        self.assertNotIn('WARNING: Active shell impersonation', output)

  def test_no_warning_for_real_stage_service_accounts(self):
    real_service_accounts = {
        '0-bootstrap': ['test-prod-bootstrap-0', 'test-prod-bootstrap-0r'],
        '1-resman': ['test-prod-resman-0', 'test-prod-resman-0r'],
        '2-networking-a-fedramp': [
            'test-prod-resman-net-0', 'test-prod-resman-net-0r'
        ],
        '2-networking-b-il5-ngfw': [
            'test-prod-resman-net-0', 'test-prod-resman-net-0r'
        ],
        '3-security': ['test-security-0', 'test-prod-resman-sec-0r'],
    }
    for stage_name, account_ids in real_service_accounts.items():
      for account_id in account_ids:
        for env_var in (
            'GOOGLE_IMPERSONATE_SERVICE_ACCOUNT',
            'CLOUDSDK_AUTH_IMPERSONATE_SERVICE_ACCOUNT',
        ):
          with self.subTest(stage=stage_name, account_id=account_id,
                            env_var=env_var):
            output = self._run_stage_links(
                stage_name, env_overrides={env_var: self._sa(account_id)})
            self.assertNotIn('WARNING: Active shell impersonation', output)

  def test_warns_on_stale_cross_stage_impersonation_env_var(self):
    stale_service_accounts = {
        '0-bootstrap': ['test-prod-resman-0', 'test-prod-bootstrap-0-old'],
        '1-resman': ['test-prod-bootstrap-0', 'test-prod-resman-net-0'],
        '2-networking-a-fedramp': [
            'test-prod-bootstrap-0', 'test-prod-resman-0', 'test-security-0',
            'test-prod-networking-0'
        ],
        '2-networking-b-il5-ngfw': [
            'test-prod-bootstrap-0', 'test-prod-resman-0', 'test-security-0',
            'test-prod-networking-0'
        ],
        '3-security': [
            'test-prod-resman-net-0', 'test-prod-resman-sec-0',
            'test-prod-security-0x'
        ],
    }
    for stage_name, account_ids in stale_service_accounts.items():
      for account_id in account_ids:
        for env_var in (
            'GOOGLE_IMPERSONATE_SERVICE_ACCOUNT',
            'CLOUDSDK_AUTH_IMPERSONATE_SERVICE_ACCOUNT',
        ):
          with self.subTest(stage=stage_name, account_id=account_id,
                            env_var=env_var):
            output = self._run_stage_links(
                stage_name, env_overrides={env_var: self._sa(account_id)})
            self.assertIn('WARNING: Active shell impersonation', output)
            self.assertIn(
                'unset GOOGLE_IMPERSONATE_SERVICE_ACCOUNT'
                ' CLOUDSDK_AUTH_IMPERSONATE_SERVICE_ACCOUNT',
                output,
            )

  def test_no_warning_when_networking_impersonation_matches_stage(self):
    service_account = self._sa('test-prod-resman-net-0')
    output = self._run_stage_links(
        '2-networking-a-fedramp',
        env_overrides={'GOOGLE_IMPERSONATE_SERVICE_ACCOUNT': service_account},
    )
    self.assertNotIn('WARNING: Active shell impersonation', output)

  def test_warns_on_bootstrap_impersonation_in_networking_stage(self):
    service_account = self._sa('test-prod-bootstrap-0')
    output = self._run_stage_links(
        '2-networking-a-fedramp',
        env_overrides={'GOOGLE_IMPERSONATE_SERVICE_ACCOUNT': service_account},
    )
    self.assertIn('WARNING: Active shell impersonation', output)


if __name__ == '__main__':
  unittest.main()
