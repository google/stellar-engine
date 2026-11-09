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

import json
import pathlib
import unittest

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
_FEDRAMP_NET_DIR = _REPO_ROOT / "fast/stages-aw/2-networking-a-fedramp"
_IL5_NET_DIR = _REPO_ROOT / "fast/stages-aw/2-networking-b-il5-ngfw"


class TestStage2Networking(unittest.TestCase):
    def test_fedramp_stage_uses_central_hub_vpc_and_default_ncc_hub(self):
        """Verify Stage 2a replaces VDSS and NVA with central Hub and NCC."""
        self.assertFalse((_FEDRAMP_NET_DIR / "nva.tf").exists())
        self.assertFalse((_FEDRAMP_NET_DIR / "net-vdss.tf").exists())
        self.assertFalse((_FEDRAMP_NET_DIR / "net-landing.tf").exists())
        self.assertFalse((_FEDRAMP_NET_DIR / "psc.tf").exists())
        self.assertTrue((_IL5_NET_DIR / "psc.tf").is_file())
        self.assertTrue((_FEDRAMP_NET_DIR / "net-hub.tf").is_file())
        self.assertTrue((_FEDRAMP_NET_DIR / "psc-google-apis.tf").is_file())
        self.assertTrue((_FEDRAMP_NET_DIR / "egress.tf").is_file())

        net_hub = (_FEDRAMP_NET_DIR / "net-hub.tf").read_text(encoding="utf-8")
        branch_tf = (_FEDRAMP_NET_DIR / "branch-net-envs.tf").read_text(
            encoding="utf-8"
        )
        psc_tf = (_FEDRAMP_NET_DIR / "psc-google-apis.tf").read_text(
            encoding="utf-8"
        )
        egress_tf = (_FEDRAMP_NET_DIR / "egress.tf").read_text(encoding="utf-8")
        conn_tf = (_FEDRAMP_NET_DIR / "connectivity-tests.tf").read_text(
            encoding="utf-8"
        )
        main_tf = (_FEDRAMP_NET_DIR / "main.tf").read_text(encoding="utf-8")
        vars_tf = (_FEDRAMP_NET_DIR / "variables.tf").read_text(
            encoding="utf-8"
        )
        outputs_tf = (_FEDRAMP_NET_DIR / "outputs.tf").read_text(
            encoding="utf-8"
        )

        self.assertIn('module "hub-project"', net_hub)
        self.assertIn('name                    = "net-hub-host"', net_hub)
        self.assertIn('default_service_account = "deprivilege"', net_hub)
        self.assertIn("compute_metadata = {", net_hub)
        self.assertNotIn("google_compute_project_metadata", net_hub)
        self.assertIn('module "hub-vpc"', net_hub)
        self.assertIn('module "hub-firewall-policy"', net_hub)
        self.assertIn("context   = local._fw_policy_context", net_hub)
        self.assertIn("ingress_mirroring_rules = lookup(", net_hub)
        self.assertIn('module "hub-nat"', net_hub)
        self.assertIn('logging_filter = "ALL"', net_hub)
        self.assertIn(
            'firewall_policy_enforcement_order = "BEFORE_CLASSIC_FIREWALL"',
            net_hub,
        )
        self.assertNotIn('module "dmz-vpc"', net_hub)
        self.assertNotIn('module "hub-firewall"', net_hub)
        self.assertNotIn("moved {", net_hub)
        self.assertNotIn("vdss", net_hub)
        self.assertIn("export_psc      = true", net_hub)
        self.assertIn('preset_topology = "STAR"', net_hub)
        self.assertIn(
            'group                 = "$ncc_groups:main/center"', net_hub
        )
        self.assertIn(
            'group                 = "$ncc_groups:main/edge"', net_hub
        )

        self.assertIn('default_service_account = "deprivilege"', branch_tf)
        self.assertIn('module "env-spoke-firewall-policy"', branch_tf)
        self.assertIn('module "env-spoke-nat"', branch_tf)
        self.assertIn('logging_filter = "ALL"', branch_tf)
        self.assertIn(
            'firewall_policy_enforcement_order = "BEFORE_CLASSIC_FIREWALL"',
            branch_tf,
        )
        self.assertNotIn('module "env-spoke-firewall"', branch_tf)
        self.assertNotIn('module "peering-envs"', branch_tf)
        self.assertNotIn("moved {", branch_tf)
        self.assertNotIn("vdss", branch_tf)

        self.assertIn('module "hub-psc-addresses"', psc_tf)
        self.assertIn('module "env-psc-addresses"', psc_tf)
        self.assertIn("service_directory_registration = (", psc_tf)
        self.assertIn('domain = "p.googleapis.com."', psc_tf)
        self.assertIn('module "env-dns-policy-googleapis"', psc_tf)

        self.assertIn('module "hub-test-addresses"', conn_tf)
        self.assertIn('module "env-test-addresses"', conn_tf)
        self.assertNotIn('resource "google_compute_address"', conn_tf)

        self.assertIn('module "egress-vpc"', egress_tf)
        self.assertIn('module "egress-firewall-policy"', egress_tf)
        self.assertIn('module "egress-nat"', egress_tf)
        self.assertIn('endpoint_types = ["ENDPOINT_TYPE_SWG"]', egress_tf)
        self.assertIn('logging_filter = "ALL"', egress_tf)
        self.assertIn("flow_logs_config = {", egress_tf)
        self.assertIn('module "egress-dns-peer-hub-root"', egress_tf)
        self.assertIn('module "egress-swp"', egress_tf)
        self.assertIn(
            "tls_inspection_config = "
            "var.centralized_egress.tls_inspection_config",
            egress_tf,
        )
        self.assertIn("next_hop_routing_mode = true", egress_tf)
        self.assertIn('module "egress-psc-addresses"', egress_tf)
        self.assertIn("_fw_policy_context = {", main_tf)
        self.assertIn("next_hop      = var.centralized_egress.swp_ip", main_tf)

        self.assertIn('variable "centralized_egress"', vars_tf)
        self.assertIn('variable "enable_cloud_nat"', vars_tf)
        self.assertIn('variable "enable_default_ncc_hub"', vars_tf)
        self.assertIn('variable "firewall_policy_rules"', vars_tf)
        self.assertIn('variable "psc_google_apis"', vars_tf)
        self.assertIn('variable "security_profile_group_ids"', vars_tf)
        self.assertNotIn('variable "firewall_rules"', vars_tf)
        self.assertNotIn('variable "nva_spot_vms"', vars_tf)
        self.assertNotIn('variable "enable_hub_and_spoke_peering"', vars_tf)
        self.assertIn('output "hub"', outputs_tf)
        self.assertIn('output "psc_google_apis_endpoints"', outputs_tf)

    def test_firewall_policy_name_defaults_to_prefixed_name(self):
        for stage_dir in (_FEDRAMP_NET_DIR, _IL5_NET_DIR):
            with self.subTest(stage=stage_dir.name):
                main_tf = (stage_dir / "main.tf").read_text(encoding="utf-8")
                vars_tf = (stage_dir / "variables.tf").read_text(
                    encoding="utf-8"
                )
                self.assertIn(
                    "coalesce(var.factories_config.firewall_policy_name,"
                    ' "${var.prefix}-net-default")',
                    main_tf,
                )
                self.assertIn(
                    "firewall_policy_name  = optional(string)", vars_tf
                )

    def test_il5_peering_envs_depends_on_per_instance_sleep(self):
        branch_tf = (_IL5_NET_DIR / "branch-net-envs.tf").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            "local_network = "
            "time_sleep.peering_delay[each.key]"
            '.triggers["local_network"]',
            branch_tf,
        )
        self.assertNotIn(
            "depends_on = [\n    time_sleep.peering_delay\n  ]",
            branch_tf,
        )

    def test_il5_ngfw_service_account_and_helper_hardening(self):
        ngfw_tf = (_IL5_NET_DIR / "ngfw.tf").read_text(encoding="utf-8")
        self.assertNotIn("-compute@developer.gserviceaccount.com", ngfw_tf)

        openssl_sh = (_IL5_NET_DIR / "openssl-helper.sh").read_text(
            encoding="utf-8"
        )
        self.assertIn("-stdin", openssl_sh)

    def test_stage2_and_ato_documentation_coherence(self):
        """Verify ATO baseline guidance and Stage 2a/firewall docs."""
        ato_doc = (_REPO_ROOT / "docs/path-to-authorization.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("FedRAMP High", ato_doc)
        self.assertIn("FedRAMP Moderate", ato_doc)
        self.assertIn("IL5", ato_doc)

        tdd_doc = (_REPO_ROOT / "docs/tdd.md").read_text(encoding="utf-8")
        self.assertIn("2-networking-a-fedramp", tdd_doc)
        self.assertIn("us-east4", tdd_doc)
        self.assertIn("us-west1", tdd_doc)
        self.assertIn("IL2", tdd_doc)

        stage2a_readme = (
            _REPO_ROOT / "fast/stages-aw/2-networking-a-fedramp/README.md"
        ).read_text(encoding="utf-8")
        self.assertIn("FedRAMP Moderate", stage2a_readme)
        self.assertIn("IL2", stage2a_readme)
        self.assertIn("hierarchical firewall policy", stage2a_readme)

        for bp in ["fedramp-high/postgresql", "il5/postgresql"]:
            bp_readme = (_REPO_ROOT / f"blueprints/{bp}/README.md").read_text(
                encoding="utf-8"
            )
            self.assertEqual(
                bp_readme.count("## Firewall Policy Coexistence and Auditing"),
                1,
            )
            self.assertIn(
                "gcloud compute firewall-policies rules list", bp_readme
            )
            self.assertIn("gcloud compute firewall-rules list", bp_readme)

    def test_essential_contacts_spoke_iam_and_ngfw_secrets(self):
        """Verify essential_contacts, spoke_project_iam, and NGFW secrets."""
        for stage in [
            "0-bootstrap",
            "2-networking-a-fedramp",
            "2-networking-b-il5-ngfw",
            "3-security",
        ]:
            var_text = (
                _REPO_ROOT / f"fast/stages-aw/{stage}/variables.tf"
            ).read_text(encoding="utf-8")
            self.assertIn(
                "can({ for k, v in tomap(var.essential_contacts)"
                " : k => tolist(v) })",
                var_text,
            )
            self.assertIn("can(tostring(var.essential_contacts))", var_text)

        org_tf = (
            _REPO_ROOT / "fast/stages-aw/0-bootstrap/organization.tf"
        ).read_text(encoding="utf-8")
        self.assertRegex(
            org_tf,
            r"contacts\s*=\s*\(\s*!var\.deploy_org_resources\.iam"
            r" \|\| var\.bootstrap_user != null\s*\?\s*\{\}\s*:\s*"
            r"local\.essential_contacts",
        )
        self.assertIn(
            '{ (tostring(var.essential_contacts)) = ["ALL"] }', org_tf
        )

        for stage in ["2-networking-a-fedramp", "2-networking-b-il5-ngfw"]:
            branch_tf = (
                _REPO_ROOT / f"fast/stages-aw/{stage}/branch-net-envs.tf"
            ).read_text(encoding="utf-8")
            expected_lookup = (
                "lookup(var.spoke_project_iam, lower(each.key), "
                "lookup(var.spoke_project_iam, each.key, {}))"
            )
            self.assertIn(expected_lookup, branch_tf)
            stage_vars = (
                _REPO_ROOT / f"fast/stages-aw/{stage}/variables.tf"
            ).read_text(encoding="utf-8")
            self.assertIn('variable "spoke_project_iam"', stage_vars)

        bastion_tf = (
            _REPO_ROOT / "fast/stages-aw/2-networking-b-il5-ngfw/bastion.tf"
        ).read_text(encoding="utf-8")
        ngfw_tf = (
            _REPO_ROOT / "fast/stages-aw/2-networking-b-il5-ngfw/ngfw.tf"
        ).read_text(encoding="utf-8")
        outputs_tf = (
            _REPO_ROOT / "fast/stages-aw/2-networking-b-il5-ngfw/outputs.tf"
        ).read_text(encoding="utf-8")
        readme_md = (
            _REPO_ROOT / "fast/stages-aw/2-networking-b-il5-ngfw/README.md"
        ).read_text(encoding="utf-8")
        self.assertIn('module "ngfw-ssh-secrets"', bastion_tf)
        self.assertIn("ngfw-ssh-private-key", bastion_tf)
        self.assertIn("ngfw-ssh-public-key", bastion_tf)
        self.assertIn("module.bastion-service-account.email", bastion_tf)
        self.assertIn("roles/secretmanager.secretAccessor", bastion_tf)
        # The secrets keep a CMEK replica in the primary region and
        # write-only data.
        self.assertIn("global_replica_locations = {", bastion_tf)
        self.assertIn(
            "(var.regions.primary) = module.kms.keys.default.id", bastion_tf
        )
        self.assertIn("data_config = { write_only_version = 1 }", bastion_tf)
        self.assertIn(
            "module.vdss-host-project.service_agents.secretmanager.iam_email",
            ngfw_tf,
        )
        self.assertNotIn('resource "local_file" "rsa-out"', outputs_tf)
        self.assertIn('output "ngfw_ssh_private_key_secret_id"', outputs_tf)
        self.assertIn("--secret=ngfw-ssh-private-key", readme_md)

    def test_ngfw_landing_gateway_and_samples_follow_configured_region(self):
        ngfw_tf = (_IL5_NET_DIR / "ngfw.tf").read_text(encoding="utf-8")
        self.assertNotIn('"us-east4/', ngfw_tf)
        self.assertIn(
            'module.vdss-vpc.subnets["${each.value}/landing-default"]'
            ".gateway_address",
            ngfw_tf,
        )

        vars_tf = (_IL5_NET_DIR / "variables.tf").read_text(encoding="utf-8")
        self.assertIn('for net in ["landing", "dmz", "mgmt"]', vars_tf)
        self.assertIn('s.region if s.name == "${net}-default"', vars_tf)

        for stage_dir in (_FEDRAMP_NET_DIR, _IL5_NET_DIR):
            with self.subTest(stage=stage_dir.name):
                sample = (stage_dir / "terraform.tfvars.sample").read_text(
                    encoding="utf-8"
                )
                self.assertIn('region        = "<region>"', sample)
                self.assertNotRegex(sample, r'region\s*=\s*"us-')

    def test_fedramp_ncc_factory_schema_and_stage_integration(self):
        """Verify FedRAMP Stage 2 NCC factory, schema, APIs, and outputs."""
        fedramp_factory = _FEDRAMP_NET_DIR / "factory-ncc.tf"
        fedramp_schema = _FEDRAMP_NET_DIR / "schemas/ncc-hub.schema.json"
        self.assertTrue(fedramp_factory.is_file())
        self.assertFalse(fedramp_factory.is_symlink())
        self.assertTrue(fedramp_schema.is_file())
        self.assertFalse((_FEDRAMP_NET_DIR / "schemas").is_symlink())
        self.assertFalse((_IL5_NET_DIR / "factory-ncc.tf").exists())
        self.assertFalse((_IL5_NET_DIR / "schemas").exists())

        schema = json.loads(fedramp_schema.read_text(encoding="utf-8"))
        self.assertEqual(
            set(schema["$defs"]["groups"]["properties"]),
            {"default", "center", "edge"},
        )
        self.assertEqual(
            set(schema["$defs"]["spokes"]["properties"]),
            {"vpcs", "tunnels", "vlan_attachments", "router_appliances"},
        )

        factory_tf = fedramp_factory.read_text(encoding="utf-8")
        for expected in (
            'resource "google_network_connectivity_hub" "default"',
            'resource "google_network_connectivity_group" "default"',
            'resource "google_network_connectivity_spoke" "vpcs"',
            'resource "google_network_connectivity_spoke" "tunnels"',
            'resource "google_network_connectivity_spoke" "vlan_attachments"',
            'resource "google_network_connectivity_spoke" "router_appliances"',
            'resource "terraform_data" "ncc_ra_instances"',
            "replace_triggered_by = "
            "[terraform_data.ncc_ra_instances[each.key]]",
        ):
            self.assertIn(expected, factory_tf)

        ncc_api_gate = (
            'local._ncc_enabled ? ["networkconnectivity.googleapis.com"]'
        )
        hub_tf = (_FEDRAMP_NET_DIR / "net-hub.tf").read_text(encoding="utf-8")
        branch_tf = (_FEDRAMP_NET_DIR / "branch-net-envs.tf").read_text(
            encoding="utf-8"
        )
        vars_tf = (_FEDRAMP_NET_DIR / "variables.tf").read_text(
            encoding="utf-8"
        )
        outputs_tf = (_FEDRAMP_NET_DIR / "outputs.tf").read_text(
            encoding="utf-8"
        )
        self.assertIn("_hub_vpcs = merge(", hub_tf)
        self.assertIn("_default_ncc_hubs", hub_tf)
        self.assertIn(ncc_api_gate, hub_tf)
        self.assertIn(ncc_api_gate, branch_tf)
        self.assertIn("ncc_hubs              = optional(string)", vars_tf)
        self.assertIn('variable "ncc_hubs"', vars_tf)
        for out_name in ("ncc_groups", "ncc_hubs", "ncc_spokes"):
            self.assertIn(f'output "{out_name}"', outputs_tf)


if __name__ == "__main__":
    unittest.main()
