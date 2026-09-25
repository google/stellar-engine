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
import unittest

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
_FEDRAMP_NET_DIR = _REPO_ROOT / 'fast/stages-aw/2-networking-a-fedramp'
_IL5_NET_DIR = _REPO_ROOT / 'fast/stages-aw/2-networking-b-il5-ngfw'


class TestStage2Networking(unittest.TestCase):

  def test_nva_routing_config_flattens_all_tenant_subnets(self):
    nva_tf = (_FEDRAMP_NET_DIR / 'nva.tf').read_text(encoding='utf-8')
    self.assertIn('routes = flatten([', nva_tf)
    self.assertNotIn('s.name if s.tenant != null][0]', nva_tf)

  def test_firewall_policy_name_defaults_to_prefixed_name(self):
    for stage_dir in (_FEDRAMP_NET_DIR, _IL5_NET_DIR):
      with self.subTest(stage=stage_dir.name):
        main_tf = (stage_dir / 'main.tf').read_text(encoding='utf-8')
        vars_tf = (stage_dir / 'variables.tf').read_text(encoding='utf-8')
        self.assertIn(
            'coalesce(var.factories_config.firewall_policy_name,'
            ' "${var.prefix}-net-default")',
            main_tf,
        )
        self.assertIn('firewall_policy_name  = optional(string)', vars_tf)


if __name__ == '__main__':
  unittest.main()

