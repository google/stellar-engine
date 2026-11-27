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

"""Schema, IAM guardrail, and OPSEC tests for Stage 4 tenant factory."""

import copy
import json
import pathlib
import re
import unittest

import jsonschema
import yaml

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
_STAGE_DIR = _REPO_ROOT / "fast/stages-aw/4-tenant-factory"
_SCHEMA_PATH = _STAGE_DIR / "schemas/tenant.schema.json"
_SAMPLE_PATH = _STAGE_DIR / "data/tenants/example-tenant.yaml.sample"
_FIXTURES_DIR = _STAGE_DIR / "tests/fixtures"
_FIXTURE_PATH = _FIXTURES_DIR / "tenants/example-tenant.yaml"

_FORBIDDEN_ROLES = (
    "roles/cloudkms.admin",
    "roles/compute.networkAdmin",
    "roles/compute.securityAdmin",
    "roles/compute.xpnAdmin",
    "roles/dns.admin",
    "roles/editor",
    "roles/iam.denyAdmin",
    "roles/iam.organizationRoleAdmin",
    "roles/iam.roleAdmin",
    "roles/iam.securityAdmin",
    "roles/iam.serviceAccountAdmin",
    "roles/iam.serviceAccountKeyAdmin",
    "roles/iam.serviceAccountTokenCreator",
    "roles/iam.serviceAccountUser",
    "roles/iam.workloadIdentityPoolAdmin",
    "roles/iam.workloadIdentityUser",
    "roles/logging.admin",
    "roles/logging.configWriter",
    "roles/orgpolicy.policyAdmin",
    "roles/owner",
    "roles/resourcemanager.folderAdmin",
    "roles/resourcemanager.folderIamAdmin",
    "roles/resourcemanager.lienModifier",
    "roles/resourcemanager.organizationAdmin",
    "roles/resourcemanager.projectIamAdmin",
    "roles/resourcemanager.tagAdmin",
    "roles/resourcemanager.tagUser",
    "roles/serviceusage.serviceUsageAdmin",
)

# Granting these on one service account is legitimate (actAs, token
# minting, Workload Identity), so only service_accounts.*.iam allows them.
_SA_SCOPED_ROLES = (
    "roles/iam.serviceAccountTokenCreator",
    "roles/iam.serviceAccountUser",
    "roles/iam.workloadIdentityUser",
)

_SERVICE_AGENT_ROLES = (
    "roles/compute.serviceAgent",
    "roles/composer.ServiceAgentV2Ext",
    "roles/container.serviceAgent",
)

_DISALLOWED_OPSEC_PATTERNS = (
    re.compile(r"@google\.com\b", re.IGNORECASE),
    re.compile(r"\.corp\.google\.com\b", re.IGNORECASE),
    re.compile(r"\bgo/[a-z0-9_-]+\b", re.IGNORECASE),
    re.compile(r"\bb/[0-9]{6,}\b", re.IGNORECASE),
    re.compile(r"\bcl/[0-9]{6,}\b", re.IGNORECASE),
    re.compile(r"\.mil\b", re.IGNORECASE),
    re.compile(r"\.gov\b", re.IGNORECASE),
)

# Invalid fixtures that the schema alone rejects.
_SCHEMA_REJECTED_FIXTURES = (
    "invalid/empty/tenant.yaml",
    "invalid/forbidden-role/tenant.yaml",
    "invalid/network-users/tenant.yaml",
    "invalid/not-mapping/tenant.yaml",
)

# Invalid fixtures whose rules depend on stage variables, so only the
# Terraform layers (variables.tf and tenant_validation) reject them.
_PLAN_TIME_ONLY_FIXTURES = ("invalid/host-override/tenant.yaml",)


def _read(path):
    return path.read_text(encoding="utf-8")


def _hcl_toset_strings(source, name):
    """Returns the string literals of a toset() HCL local called name."""
    match = re.search(
        rf"^\s*{re.escape(name)}\s*=\s*toset\(\[(.*?)\]\)",
        source,
        re.MULTILINE | re.DOTALL,
    )
    if match is None:
        raise AssertionError(f"{name} not found")
    return set(re.findall(r'"([^"]+)"', match.group(1)))


def _hcl_string_map(source, name):
    """Returns the key and string value pairs of an HCL map local."""
    match = re.search(
        rf"^\s*{re.escape(name)}\s*=\s*\{{(.*?)\n\s*\}}",
        source,
        re.MULTILINE | re.DOTALL,
    )
    if match is None:
        raise AssertionError(f"{name} not found")
    pairs = re.findall(
        r'^\s*([a-z_]+)\s*=\s*"((?:[^"\\]|\\.)*)"',
        match.group(1),
        re.MULTILINE,
    )
    return {key: value.replace("\\\\", "\\") for key, value in pairs}


def _hcl_string(source, name):
    """Returns the unescaped value of a string HCL local called name."""
    match = re.search(
        rf'^\s*{re.escape(name)}\s*=\s*"((?:[^"\\]|\\.)*)"$',
        source,
        re.MULTILINE,
    )
    if match is None:
        raise AssertionError(f"{name} not found")
    return match.group(1).replace("\\\\", "\\")


class TestTenantFactorySchema(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = json.loads(_read(_SCHEMA_PATH))
        jsonschema.Draft7Validator.check_schema(cls.schema)
        cls.validator = jsonschema.Draft7Validator(cls.schema)
        cls.sample = yaml.safe_load(_read(_SAMPLE_PATH))
        cls.manifest = yaml.safe_load(_read(_FIXTURE_PATH))
        cls.main_tf = _read(_STAGE_DIR / "main.tf")
        cls.variables_tf = _read(_STAGE_DIR / "variables.tf")

    def _assert_rejected(self, manifest):
        with self.assertRaises(jsonschema.ValidationError):
            self.validator.validate(manifest)

    def test_sample_manifest_validates_against_schema(self):
        errors = list(self.validator.iter_errors(self.sample))
        self.assertEqual(errors, [], f"Unexpected sample errors: {errors}")
        self.assertGreaterEqual(
            len(self.sample["projects"]),
            2,
            "Sample tenant manifest should demonstrate multiple projects.",
        )
        app_project = self.sample["projects"]["app-0"]
        self.assertGreaterEqual(
            len(app_project["shared_vpc_subnets"]),
            2,
            "Sample app-0 project needs multi-subnet Shared VPC.",
        )

    def test_fixture_manifest_mirrors_sample_and_validates(self):
        self.assertEqual(self.manifest, self.sample)
        self.validator.validate(self.manifest)
        sample_dir = _SAMPLE_PATH.parent
        self.assertEqual(sorted(sample_dir.glob("*.yaml")), [])

    def test_rejects_forbidden_roles_in_tenant_folder_iam(self):
        for role in _FORBIDDEN_ROLES:
            with self.subTest(role=role):
                manifest = copy.deepcopy(self.manifest)
                manifest["iam"][role] = ["group:bad-admins@example.com"]
                self._assert_rejected(manifest)

    def test_rejects_forbidden_roles_in_project_iam(self):
        for role in _FORBIDDEN_ROLES:
            with self.subTest(role=role):
                manifest = copy.deepcopy(self.manifest)
                manifest["projects"]["app-0"]["iam"][role] = [
                    "group:bad-admins@example.com"
                ]
                self._assert_rejected(manifest)

    def test_rejects_forbidden_roles_in_iam_by_principals(self):
        for role in _FORBIDDEN_ROLES:
            with self.subTest(role=role):
                manifest = copy.deepcopy(self.manifest)
                manifest["projects"]["app-0"]["iam_by_principals"] = {
                    "group:bad-admins@example.com": [role]
                }
                self._assert_rejected(manifest)

    def test_rejects_forbidden_roles_in_iam_bindings_additive(self):
        for role in _FORBIDDEN_ROLES:
            with self.subTest(role=role):
                manifest = copy.deepcopy(self.manifest)
                manifest["projects"]["app-0"]["iam_bindings_additive"] = {
                    "bad-binding": {
                        "member": "group:bad-admins@example.com",
                        "role": role,
                    }
                }
                self._assert_rejected(manifest)

    def test_rejects_forbidden_roles_in_service_account_self_roles(self):
        for role in _FORBIDDEN_ROLES:
            with self.subTest(role=role):
                manifest = copy.deepcopy(self.manifest)
                manifest["projects"]["app-0"]["service_accounts"][
                    "app-runtime"
                ]["iam_self_roles"].append(role)
                self._assert_rejected(manifest)

    def test_service_account_iam_allows_only_sa_scoped_roles(self):
        for role in _FORBIDDEN_ROLES:
            with self.subTest(role=role):
                manifest = copy.deepcopy(self.manifest)
                sa = manifest["projects"]["app-0"]["service_accounts"][
                    "app-runtime"
                ]
                sa["iam"] = {role: ["group:deployers@example.com"]}
                if role in _SA_SCOPED_ROLES:
                    self.validator.validate(manifest)
                else:
                    self._assert_rejected(manifest)

    def test_rejects_service_agent_roles_in_every_iam_input(self):
        member = "group:bad-admins@example.com"
        for role in _SERVICE_AGENT_ROLES:
            with self.subTest(role=role):
                folder = copy.deepcopy(self.manifest)
                folder["iam"][role] = [member]
                self._assert_rejected(folder)
                project = copy.deepcopy(self.manifest)
                project["projects"]["app-0"]["iam_by_principals"] = {
                    member: [role]
                }
                self._assert_rejected(project)
                additive = copy.deepcopy(self.manifest)
                additive["projects"]["app-0"]["iam_bindings_additive"] = {
                    "agent": {"member": member, "role": role}
                }
                self._assert_rejected(additive)
                sa_scoped = copy.deepcopy(self.manifest)
                sa_scoped["projects"]["app-0"]["service_accounts"][
                    "app-runtime"
                ]["iam"] = {role: [member]}
                self._assert_rejected(sa_scoped)

    def test_role_id_format(self):
        # The schema checks shape only; allowlists apply at plan time.
        valid_roles = (
            "$custom_roles:tenant_readonly",
            "organizations/123456789012/roles/tenantViewer",
            "projects/se-dev-ops-0/roles/opsViewer",
            "roles/viewer",
        )
        invalid_roles = (
            " roles/viewer",
            "$custom_roles:bad key",
            "organizations/acme/roles/tenantViewer",
            "owner",
            "roles/viewer ",
        )
        for role in valid_roles:
            with self.subTest(role=role):
                manifest = copy.deepcopy(self.manifest)
                manifest["iam"][role] = ["group:readers@example.com"]
                self.validator.validate(manifest)
        for role in invalid_roles:
            with self.subTest(role=role):
                manifest = copy.deepcopy(self.manifest)
                manifest["iam"][role] = ["group:readers@example.com"]
                self._assert_rejected(manifest)

    def test_kms_services_keys_and_key_references(self):
        key_id = "projects/sec-0/locations/us-east4/keyRings/t/cryptoKeys/k"
        valid = copy.deepcopy(self.manifest)
        valid["projects"]["app-0"]["kms_services"] = {
            "compute.googleapis.com": ["us-east4-tenant"],
            "storage.googleapis.com": [key_id],
        }
        valid["automation"] = {"bucket_kms_key": "dev-gcs:us-east4"}
        self.validator.validate(valid)

        bad_key = copy.deepcopy(self.manifest)
        bad_key["projects"]["app-0"]["kms_services"] = {
            "storage": ["us-east4-tenant"]
        }
        self._assert_rejected(bad_key)

        for bad_ref in ("projects/sec-0/locations/us-east4", "a b"):
            with self.subTest(bad_ref=bad_ref):
                bad_service_ref = copy.deepcopy(self.manifest)
                bad_service_ref["projects"]["app-0"]["kms_services"] = {
                    "storage.googleapis.com": [bad_ref]
                }
                self._assert_rejected(bad_service_ref)
                bad_bucket_ref = copy.deepcopy(self.manifest)
                bad_bucket_ref["automation"] = {"bucket_kms_key": bad_ref}
                self._assert_rejected(bad_bucket_ref)

    def test_network_users_require_subnets(self):
        manifest = copy.deepcopy(self.manifest)
        del manifest["projects"]["app-0"]["shared_vpc_subnets"]
        self._assert_rejected(manifest)

        empty_subnets = copy.deepcopy(self.manifest)
        empty_subnets["projects"]["app-0"]["shared_vpc_subnets"] = []
        self._assert_rejected(empty_subnets)

        no_users = copy.deepcopy(manifest)
        no_users["projects"]["app-0"]["shared_vpc_network_users"] = []
        self.validator.validate(no_users)

    def test_invalid_fixtures_split_between_schema_and_plan(self):
        for fixture in _SCHEMA_REJECTED_FIXTURES:
            with self.subTest(fixture=fixture):
                document = yaml.safe_load(_read(_FIXTURES_DIR / fixture))
                self._assert_rejected(document)
        for fixture in _PLAN_TIME_ONLY_FIXTURES:
            with self.subTest(fixture=fixture):
                document = yaml.safe_load(_read(_FIXTURES_DIR / fixture))
                self.validator.validate(document)

    def test_shared_vpc_service_agent_iam_rejects_bad_roles_and_principals(
        self,
    ):
        for bad_role in (
            "roles/owner",
            "roles/compute.networkAdmin",
            "roles/iam.securityAdmin",
        ):
            with self.subTest(bad_role=bad_role):
                manifest = copy.deepcopy(self.manifest)
                manifest["projects"]["app-0"]["shared_vpc_service_agent_iam"][
                    bad_role
                ] = ["$service_agents:cloudservices"]
                self._assert_rejected(manifest)

        for bad_member in (
            "group:attacker@example.com",
            "user:attacker@example.com",
            "serviceAccount:sa@example.iam.gserviceaccount.com",
        ):
            with self.subTest(bad_member=bad_member):
                manifest = copy.deepcopy(self.manifest)
                manifest["projects"]["app-0"]["shared_vpc_service_agent_iam"][
                    "roles/container.hostServiceAgentUser"
                ] = [bad_member]
                self._assert_rejected(manifest)

    def test_shared_vpc_service_grants_requires_service_agent_api_format(self):
        for bad_grant in (
            "compute.googleapis.com",
            "$service_agents:compute",
            "group:attacker@example.com",
        ):
            with self.subTest(bad_grant=bad_grant):
                manifest = copy.deepcopy(self.manifest)
                manifest["projects"]["app-0"]["shared_vpc_service_grants"] = [
                    bad_grant
                ]
                self._assert_rejected(manifest)

        valid_manifest = copy.deepcopy(self.manifest)
        valid_manifest["projects"]["app-0"]["shared_vpc_service_grants"] = [
            "$service_agents:compute.googleapis.com"
        ]
        self.validator.validate(valid_manifest)

    def test_rejects_invalid_gcp_ids_and_automation_sa_keys(self):
        bad_project_name = copy.deepcopy(self.manifest)
        bad_project_name["projects"]["app-0"]["name"] = "dev-acme-app-"
        self._assert_rejected(bad_project_name)

        bad_host_project = copy.deepcopy(self.manifest)
        bad_host_project["projects"]["app-0"]["shared_vpc_host_project"] = (
            "host-"
        )
        self._assert_rejected(bad_host_project)

        bad_workload_sa = copy.deepcopy(self.manifest)
        bad_sas = bad_workload_sa["projects"]["app-0"]["service_accounts"]
        bad_sas["bad-sa-"] = {}
        self._assert_rejected(bad_workload_sa)

        bad_auto_sa = copy.deepcopy(self.manifest)
        bad_auto_sa["automation"] = {
            "project_id": "test-iac-core-0",
            "service_accounts": {"admin": {}},
        }
        self._assert_rejected(bad_auto_sa)

        valid_auto = copy.deepcopy(self.manifest)
        valid_auto["automation"] = {
            "project_id": "test-iac-core-0",
            "service_accounts": {"rw": {}, "ro": {}},
        }
        self.validator.validate(valid_auto)

    def test_rejects_per_tenant_org_policies_override(self):
        manifest = copy.deepcopy(self.manifest)
        manifest["org_policies"] = {
            "gcp.restrictServiceUsage": {"inherit_from_parent": False}
        }
        self._assert_rejected(manifest)

    def test_rejects_invalid_lifecycle_state_and_subnet_format(self):
        bad_lifecycle = copy.deepcopy(self.manifest)
        bad_lifecycle["lifecycle_state"] = "deleted"
        self._assert_rejected(bad_lifecycle)

        bad_subnet = copy.deepcopy(self.manifest)
        bad_subnet["projects"]["app-0"]["shared_vpc_subnets"] = [
            "missing-region-slash"
        ]
        self._assert_rejected(bad_subnet)

    def test_denylist_parity_across_layers(self):
        definitions = self.schema["definitions"]
        hcl_forbidden = _hcl_toset_strings(self.main_tf, "_forbidden_roles")
        self.assertEqual(hcl_forbidden, set(_FORBIDDEN_ROLES))
        self.assertEqual(
            set(definitions["forbidden_role"]["enum"]), set(_FORBIDDEN_ROLES)
        )
        hcl_sa_scoped = _hcl_toset_strings(
            self.main_tf, "_sa_scoped_privileged_roles"
        )
        self.assertEqual(hcl_sa_scoped, set(_SA_SCOPED_ROLES))
        self.assertEqual(
            set(definitions["sa_scoped_role"]["enum"]), set(_SA_SCOPED_ROLES)
        )
        # variables.tf reuses the main.tf locals instead of a copied list.
        for local_name in (
            "local._forbidden_project_roles",
            "local._forbidden_sa_roles",
            "local._allowed_privileged_roles",
            "local._role_id_regexes",
        ):
            with self.subTest(local_name=local_name):
                self.assertIn(local_name, self.variables_tf)
        for role in _FORBIDDEN_ROLES:
            with self.subTest(role=role):
                self.assertNotIn(f'"{role}"', self.variables_tf)

    def test_regex_parity_across_layers(self):
        definitions = self.schema["definitions"]
        hcl_role_regexes = _hcl_string_map(self.main_tf, "_role_id_regexes")
        schema_role_regexes = {
            entry["pattern"] for entry in definitions["role_id"]["anyOf"]
        }
        self.assertEqual(set(hcl_role_regexes.values()), schema_role_regexes)

        api_regex = _hcl_string(self.main_tf, "_api_regex")
        project = self.schema["properties"]["projects"]["patternProperties"][
            "^[a-z][a-z0-9-]{0,20}$"
        ]["properties"]
        kms_names = project["kms_services"]["propertyNames"]["pattern"]
        self.assertEqual(kms_names, api_regex)
        self.assertEqual(project["services"]["items"]["pattern"], api_regex)

        subnet_regex = _hcl_string(self.main_tf, "_subnet_regex")
        subnet_items = project["shared_vpc_subnets"]["items"]
        self.assertEqual(subnet_items["pattern"], subnet_regex)

    def test_yaml_manifests_are_not_wrapped_in_try(self):
        for pattern in (
            r"try\(\s*yamldecode",
            r"try\(\s*\{\s*for\s+\w+,\s*\w+\s+in\s+yamldecode",
        ):
            with self.subTest(pattern=pattern):
                self.assertIsNone(re.search(pattern, self.main_tf))

    def test_lifecycle_and_dependency_guards(self):
        self.assertIn(
            'tv.lifecycle_state == "archived" && var.force_destroy',
            self.main_tf,
        )
        self.assertNotIn("force_destroy = var.force_destroy", self.main_tf)
        self.assertNotIn("depends_on = [module.tenant-projects]", self.main_tf)

    def test_stage_files_contain_no_opsec_or_customer_terms(self):
        checked = 0
        for path in sorted(_STAGE_DIR.rglob("*")):
            if not path.is_file() or ".terraform" in path.parts:
                continue
            content = _read(path)
            checked += 1
            for pattern in _DISALLOWED_OPSEC_PATTERNS:
                self.assertIsNone(
                    pattern.search(content),
                    f"Disallowed OPSEC match {pattern.pattern!r} in {path}",
                )
        self.assertGreaterEqual(checked, 6)

    def test_stage_il5_guardrails_and_cmek_wiring(self):
        versions_tf = _read(_STAGE_DIR / "versions.tf")
        self.assertIn('source  = "hashicorp/time"', versions_tf)
        self.assertIn('default     = "us-east4"', self.variables_tf)
        self.assertIn('variable "force_destroy"', self.variables_tf)
        self.assertIn('variable "folder_ids"', self.variables_tf)
        self.assertIn(
            'data "google_bigquery_default_service_account" "tenant_bq"',
            self.main_tf,
        )
        self.assertIn(
            'resource "time_sleep" "tenant_bq_sa_propagation"', self.main_tf
        )
        self.assertIn(
            'resource "google_kms_crypto_key_iam_member" '
            '"tenant_bigquery_cmek"',
            self.main_tf,
        )
        self.assertIn("_cmek_companion_apis", self.main_tf)


if __name__ == "__main__":
    unittest.main()
