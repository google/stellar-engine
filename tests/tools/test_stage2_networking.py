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
_FEDRAMP_NET_DIR = _REPO_ROOT / "fast/stages-aw/2-networking-a-fedramp"
_IL5_NET_DIR = _REPO_ROOT / "fast/stages-aw/2-networking-b-il5-ngfw"


class TestStage2Networking(unittest.TestCase):
    def test_nva_routing_config_flattens_all_tenant_subnets(self):
        nva_tf = (_FEDRAMP_NET_DIR / "nva.tf").read_text(encoding="utf-8")
        self.assertIn("routes = flatten([", nva_tf)
        self.assertNotIn("s.name if s.tenant != null][0]", nva_tf)

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

    def test_peering_envs_depends_on_per_instance_sleep(self):
        for stage_dir in (_FEDRAMP_NET_DIR, _IL5_NET_DIR):
            with self.subTest(stage=stage_dir.name):
                branch_tf = (stage_dir / "branch-net-envs.tf").read_text(
                    encoding="utf-8"
                )
                self.assertIn(
                    "local_network ="
                    " "
                    'time_sleep.peering_delay[each.key].triggers["local_network"]',
                    branch_tf,
                )
                self.assertNotIn(
                    "depends_on = [\n    time_sleep.peering_delay\n  ]",
                    branch_tf,
                )

    def test_nva_defaults_to_standard_on_demand_vms(self):
        nva_tf = (_FEDRAMP_NET_DIR / "nva.tf").read_text(encoding="utf-8")
        vars_tf = (_FEDRAMP_NET_DIR / "variables.tf").read_text(
            encoding="utf-8"
        )
        self.assertIn("spot                      = var.nva_spot_vms", nva_tf)
        self.assertIn(
            'termination_action        = var.nva_spot_vms ? "STOP" : null',
            nva_tf,
        )
        self.assertIn('variable "nva_spot_vms"', vars_tf)
        self.assertIn("default     = false", vars_tf)

    def test_nva_and_ngfw_service_account_and_helper_hardening(self):
        nva_tf = (_FEDRAMP_NET_DIR / "nva.tf").read_text(encoding="utf-8")
        self.assertNotIn("google_service_account_key", nva_tf)

        ngfw_tf = (_IL5_NET_DIR / "ngfw.tf").read_text(encoding="utf-8")
        self.assertNotIn("-compute@developer.gserviceaccount.com", ngfw_tf)

        openssl_sh = (_IL5_NET_DIR / "openssl-helper.sh").read_text(
            encoding="utf-8"
        )
        self.assertIn("-stdin", openssl_sh)

    def test_stage2_and_ato_documentation_coherence(self):
        """Verify ATO baseline guidance (#232), Stage 2a TDD and regional docs
        (#195), and firewall policy docs (#117).
        """
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
        """Verify essential_contacts map support (#119), spoke_project_iam
        (#120), and NGFW Secret Manager keys (#20).
        """
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
                "can({ for k, v in tomap(var.essential_contacts) : k => "
                "tolist(v) })",
                var_text,
            )
            self.assertIn("can(tostring(var.essential_contacts))", var_text)

        org_tf = (
            _REPO_ROOT / "fast/stages-aw/0-bootstrap/organization.tf"
        ).read_text(encoding="utf-8")
        self.assertIn(
            "contacts     = var.bootstrap_user != null ? {} : "
            "local.essential_contacts",
            org_tf,
        )
        self.assertIn(
            '{ (tostring(var.essential_contacts)) = ["ALL"] }', org_tf
        )

        for stage in ["2-networking-a-fedramp", "2-networking-b-il5-ngfw"]:
            branch_tf = (
                _REPO_ROOT / f"fast/stages-aw/{stage}/branch-net-envs.tf"
            ).read_text(encoding="utf-8")
            self.assertIn(
                "lookup(var.spoke_project_iam, lower(each.key), "
                "lookup(var.spoke_project_iam, each.key, {}))",
                branch_tf,
            )
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

    def test_stage2_outputs_data_and_psc_hardening(self):
        """Verify Stage 2 outputs, policy factory data, and PSC gating."""
        for stage_dir in (_FEDRAMP_NET_DIR, _IL5_NET_DIR):
            with self.subTest(stage=stage_dir.name):
                outputs_tf = (stage_dir / "outputs.tf").read_text(
                    encoding="utf-8"
                )
                self.assertIn(
                    "host_project_ids = [for k, v in "
                    "module.env-spoke-projects : v.project_id]",
                    outputs_tf,
                )
                self.assertTrue((stage_dir / "data/cidrs.yaml").is_file())
                self.assertTrue(
                    (
                        stage_dir / "data/hierarchical-ingress-rules.yaml"
                    ).is_file()
                )
                net_vdss = (stage_dir / "net-vdss.tf").read_text(
                    encoding="utf-8"
                )
                self.assertIn("private    = false", net_vdss)
                self.assertNotIn("private    = true", net_vdss)
                psc_tf = (stage_dir / "psc.tf").read_text(encoding="utf-8")
                self.assertIn(
                    "if length(try(var.psa_ranges[lower(k)], "
                    "var.psa_ranges.dev)) == 0",
                    psc_tf,
                )

        il5_vdss = (_IL5_NET_DIR / "net-vdss.tf").read_text(encoding="utf-8")
        self.assertNotIn(
            'resource "google_compute_route" "mgmt-default"', il5_vdss
        )
        self.assertNotIn('module "dmz-nat-mgmt"', il5_vdss)

        ngfw_tf = (_IL5_NET_DIR / "ngfw.tf").read_text(encoding="utf-8")
        self.assertIn(
            "module.vdss-vpc.subnets["
            '"${each.value}/landing-default"].gateway_address',
            ngfw_tf,
        )
        self.assertIn("region         = each.value", ngfw_tf)
        self.assertIn("block-project-ssh-keys               = true", ngfw_tf)
        self.assertIn("serial-port-enable                   = false", ngfw_tf)

        bootstrap_xml = (
            _IL5_NET_DIR / "templates/bootstrap.xml.tpl"
        ).read_text(encoding="utf-8")
        self.assertNotIn("<member>3des</member>", bootstrap_xml)
        self.assertNotIn("<member>sha1</member>", bootstrap_xml)
        self.assertNotIn("<member>group2</member>", bootstrap_xml)
        self.assertIn(
            "<interface-management-profile>ping</interface-management-profile>",
            bootstrap_xml,
        )
        self.assertIn("<log-end>yes</log-end>", bootstrap_xml)

    def test_stage3_security_and_tools_hardening(self):
        """Verify Stage 3 KMS, VPC-SC, outputs, and script hardening."""
        sec_dir = _REPO_ROOT / "fast/stages-aw/3-security"
        sec_outputs = (sec_dir / "outputs.tf").read_text(encoding="utf-8")
        self.assertIn('file_permission = "0600"', sec_outputs)
        self.assertIn(
            "content      = sensitive(jsonencode(local.tfvars))", sec_outputs
        )
        self.assertIn("kms_key_name =", sec_outputs)

        vpc_sc = (sec_dir / "vpc-sc.tf").read_text(encoding="utf-8")
        self.assertIn(
            "coalesce(var.logging.project_number, var.logging.project_id)",
            vpc_sc,
        )
        self.assertIn(
            "status                    = local.vpc_sc_perimeter", vpc_sc
        )

        core_dev = (sec_dir / "core-dev.tf").read_text(encoding="utf-8")
        self.assertNotIn("var.service_accounts.project-factory-prod", core_dev)
        self.assertIn("var.service_accounts.gke-dev", core_dev)
        self.assertIn("var.service_accounts.gcve-dev", core_dev)

        core_prod = (sec_dir / "core-prod.tf").read_text(encoding="utf-8")
        self.assertIn("var.service_accounts.gke-prod", core_prod)
        self.assertIn("var.service_accounts.gcve-prod", core_prod)

        sa_lockdown = (sec_dir / "sa_lockdown.sh").read_text(encoding="utf-8")
        self.assertIn("shopt -s nullglob", sa_lockdown)
        self.assertIn('"project-factory-prod"', sa_lockdown)

        validation_sh = (sec_dir / "validation.sh").read_text(encoding="utf-8")
        self.assertIn("projectId~'-iac-core-0$'", validation_sh)

        destroy_sh = (_REPO_ROOT / "scripts/destroy.sh").read_text(
            encoding="utf-8"
        )
        self.assertIn('printf -v "$var_name" \'%s\' "$input"', destroy_sh)
        self.assertNotIn('eval "$var_name=\\"$input\\""', destroy_sh)

        sandbox_sh = (_REPO_ROOT / "tools/create_e2e_sandbox.sh").read_text(
            encoding="utf-8"
        )
        self.assertIn("umask 077", sandbox_sh)
        self.assertIn('touch "${DEST}/main.tf"', sandbox_sh)
        self.assertNotIn("tocuh", sandbox_sh)

        mocks_sh = (_REPO_ROOT / "generate-mocks.sh").read_text(
            encoding="utf-8"
        )
        self.assertIn("2-networking-a-fedramp/mock-versions.tf", mocks_sh)
        self.assertNotIn("2-networking-a-fedramp-high", mocks_sh)


if __name__ == "__main__":
    unittest.main()
