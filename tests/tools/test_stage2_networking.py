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

  def test_peering_envs_depends_on_per_instance_sleep(self):
    for stage_dir in (_FEDRAMP_NET_DIR, _IL5_NET_DIR):
      with self.subTest(stage=stage_dir.name):
        branch_tf = (stage_dir / 'branch-net-envs.tf').read_text(
            encoding='utf-8'
        )
        self.assertIn(
            'local_network ='
            ' time_sleep.peering_delay[each.key].triggers["local_network"]',
            branch_tf,
        )
        self.assertNotIn('depends_on = [\n    time_sleep.peering_delay\n  ]', branch_tf)

  def test_nva_defaults_to_standard_on_demand_vms(self):
    nva_tf = (_FEDRAMP_NET_DIR / 'nva.tf').read_text(encoding='utf-8')
    vars_tf = (_FEDRAMP_NET_DIR / 'variables.tf').read_text(encoding='utf-8')
    self.assertIn('spot                      = var.nva_spot_vms', nva_tf)
    self.assertIn(
        'termination_action        = var.nva_spot_vms ? "STOP" : null', nva_tf
    )
    self.assertIn('variable "nva_spot_vms"', vars_tf)
    self.assertIn('default     = false', vars_tf)

  def test_nva_and_ngfw_service_account_and_helper_hardening(self):
    nva_tf = (_FEDRAMP_NET_DIR / 'nva.tf').read_text(encoding='utf-8')
    self.assertNotIn('google_service_account_key', nva_tf)

    ngfw_tf = (_IL5_NET_DIR / 'ngfw.tf').read_text(encoding='utf-8')
    self.assertNotIn('-compute@developer.gserviceaccount.com', ngfw_tf)

    openssl_sh = (_IL5_NET_DIR / 'openssl-helper.sh').read_text(encoding='utf-8')
    self.assertIn('-stdin', openssl_sh)



  def test_stage2_and_ato_documentation_coherence(self):
    """Verify ATO baseline guidance (#232), Stage 2a TDD and regional docs (#195), and firewall policy docs (#117)."""
    ato_doc = (_REPO_ROOT / "docs/path-to-authorization.md").read_text(encoding="utf-8")
    self.assertIn("FedRAMP High", ato_doc)
    self.assertIn("FedRAMP Moderate", ato_doc)
    self.assertIn("IL5", ato_doc)

    tdd_doc = (_REPO_ROOT / "docs/tdd.md").read_text(encoding="utf-8")
    self.assertIn("2-networking-a-fedramp", tdd_doc)
    self.assertIn("us-east4", tdd_doc)
    self.assertIn("us-west1", tdd_doc)
    self.assertIn("IL2", tdd_doc)

    stage2a_readme = (_REPO_ROOT / "fast/stages-aw/2-networking-a-fedramp/README.md").read_text(encoding="utf-8")
    self.assertIn("FedRAMP Moderate", stage2a_readme)
    self.assertIn("IL2", stage2a_readme)
    self.assertIn("hierarchical firewall policy", stage2a_readme)

    for bp in ["fedramp-high/postgresql", "il5/postgresql"]:
      bp_readme = (_REPO_ROOT / f"blueprints/{bp}/README.md").read_text(encoding="utf-8")
      self.assertEqual(bp_readme.count("## Firewall Policy Coexistence and Auditing"), 1)
      self.assertIn("gcloud compute firewall-policies rules list", bp_readme)
      self.assertIn("gcloud compute firewall-rules list", bp_readme)


if __name__ == '__main__':
  unittest.main()



