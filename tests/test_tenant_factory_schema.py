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
_EXAMPLE_MANIFEST_PATH = _STAGE_DIR / "data/tenants/example-tenant.yaml"

_FORBIDDEN_ROLES = (
    "roles/compute.xpnAdmin",
    "roles/editor",
    "roles/iam.organizationRoleAdmin",
    "roles/iam.securityAdmin",
    "roles/iam.serviceAccountKeyAdmin",
    "roles/orgpolicy.policyAdmin",
    "roles/owner",
    "roles/resourcemanager.folderAdmin",
    "roles/resourcemanager.folderIamAdmin",
    "roles/resourcemanager.lienModifier",
    "roles/resourcemanager.organizationAdmin",
    "roles/resourcemanager.projectIamAdmin",
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


class TestTenantFactorySchema(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
        jsonschema.Draft7Validator.check_schema(cls.schema)
        cls.validator = jsonschema.Draft7Validator(cls.schema)
        cls.example_manifest = yaml.safe_load(
            _EXAMPLE_MANIFEST_PATH.read_text(encoding="utf-8")
        )

    def test_example_manifest_validates_against_schema(self):
        errors = list(self.validator.iter_errors(self.example_manifest))
        self.assertEqual(
            errors,
            [],
            f"Unexpected schema errors in example-tenant.yaml: {errors}",
        )
        self.assertGreaterEqual(
            len(self.example_manifest["projects"]),
            2,
            "Example tenant manifest should demonstrate multiple projects.",
        )
        app_project = self.example_manifest["projects"]["app-0"]
        self.assertGreaterEqual(
            len(app_project["shared_vpc_subnets"]),
            2,
            "Example app-0 project needs multi-subnet Shared VPC.",
        )

    def test_rejects_forbidden_roles_in_tenant_folder_iam(self):
        for role in _FORBIDDEN_ROLES:
            with self.subTest(role=role):
                manifest = copy.deepcopy(self.example_manifest)
                manifest["iam"][role] = ["group:bad-admins@example.com"]
                with self.assertRaises(jsonschema.ValidationError):
                    self.validator.validate(manifest)

    def test_rejects_forbidden_roles_in_project_iam(self):
        for role in _FORBIDDEN_ROLES:
            with self.subTest(role=role):
                manifest = copy.deepcopy(self.example_manifest)
                manifest["projects"]["app-0"]["iam"][role] = [
                    "group:bad-admins@example.com"
                ]
                with self.assertRaises(jsonschema.ValidationError):
                    self.validator.validate(manifest)

    def test_rejects_forbidden_roles_in_iam_by_principals(self):
        for role in _FORBIDDEN_ROLES:
            with self.subTest(role=role):
                manifest = copy.deepcopy(self.example_manifest)
                manifest["projects"]["app-0"]["iam_by_principals"] = {
                    "group:bad-admins@example.com": [role]
                }
                with self.assertRaises(jsonschema.ValidationError):
                    self.validator.validate(manifest)

    def test_rejects_forbidden_roles_in_iam_bindings_additive(self):
        for role in _FORBIDDEN_ROLES:
            with self.subTest(role=role):
                manifest = copy.deepcopy(self.example_manifest)
                manifest["projects"]["app-0"]["iam_bindings_additive"] = {
                    "bad-binding": {
                        "member": "group:bad-admins@example.com",
                        "role": role,
                    }
                }
                with self.assertRaises(jsonschema.ValidationError):
                    self.validator.validate(manifest)

    def test_rejects_forbidden_roles_in_service_account_self_roles(self):
        for role in _FORBIDDEN_ROLES:
            with self.subTest(role=role):
                manifest = copy.deepcopy(self.example_manifest)
                manifest["projects"]["app-0"]["service_accounts"][
                    "app-runtime"
                ]["iam_self_roles"].append(role)
                with self.assertRaises(jsonschema.ValidationError):
                    self.validator.validate(manifest)

    def test_shared_vpc_service_agent_iam_rejects_bad_roles_and_principals(
        self,
    ):
        for bad_role in (
            "roles/owner",
            "roles/compute.networkAdmin",
            "roles/iam.securityAdmin",
        ):
            with self.subTest(bad_role=bad_role):
                manifest = copy.deepcopy(self.example_manifest)
                manifest["projects"]["app-0"]["shared_vpc_service_agent_iam"][
                    bad_role
                ] = ["$service_agents:cloudservices"]
                with self.assertRaises(jsonschema.ValidationError):
                    self.validator.validate(manifest)

        for bad_member in (
            "group:attacker@example.com",
            "user:attacker@example.com",
            "serviceAccount:sa@example.iam.gserviceaccount.com",
        ):
            with self.subTest(bad_member=bad_member):
                manifest = copy.deepcopy(self.example_manifest)
                manifest["projects"]["app-0"]["shared_vpc_service_agent_iam"][
                    "roles/container.hostServiceAgentUser"
                ] = [bad_member]
                with self.assertRaises(jsonschema.ValidationError):
                    self.validator.validate(manifest)

    def test_shared_vpc_service_grants_requires_service_agent_api_format(self):
        for bad_grant in (
            "compute.googleapis.com",
            "$service_agents:compute",
            "group:attacker@example.com",
        ):
            with self.subTest(bad_grant=bad_grant):
                manifest = copy.deepcopy(self.example_manifest)
                manifest["projects"]["app-0"]["shared_vpc_service_grants"] = [
                    bad_grant
                ]
                with self.assertRaises(jsonschema.ValidationError):
                    self.validator.validate(manifest)

        valid_manifest = copy.deepcopy(self.example_manifest)
        valid_manifest["projects"]["app-0"]["shared_vpc_service_grants"] = [
            "$service_agents:compute.googleapis.com"
        ]
        self.validator.validate(valid_manifest)

    def test_rejects_invalid_gcp_ids_and_automation_sa_keys(self):
        bad_project_name = copy.deepcopy(self.example_manifest)
        bad_project_name["projects"]["app-0"]["name"] = "dev-acme-app-"
        with self.assertRaises(jsonschema.ValidationError):
            self.validator.validate(bad_project_name)

        bad_host_project = copy.deepcopy(self.example_manifest)
        bad_host_project["projects"]["app-0"]["shared_vpc_host_project"] = (
            "host-"
        )
        with self.assertRaises(jsonschema.ValidationError):
            self.validator.validate(bad_host_project)

        bad_workload_sa = copy.deepcopy(self.example_manifest)
        bad_sas = bad_workload_sa["projects"]["app-0"]["service_accounts"]
        bad_sas["bad-sa-"] = {}
        with self.assertRaises(jsonschema.ValidationError):
            self.validator.validate(bad_workload_sa)

        bad_auto_sa = copy.deepcopy(self.example_manifest)
        bad_auto_sa["automation"] = {
            "project_id": "test-iac-core-0",
            "service_accounts": {"admin": {}},
        }
        with self.assertRaises(jsonschema.ValidationError):
            self.validator.validate(bad_auto_sa)

        valid_auto = copy.deepcopy(self.example_manifest)
        valid_auto["automation"] = {
            "project_id": "test-iac-core-0",
            "service_accounts": {"rw": {}, "ro": {}},
        }
        self.validator.validate(valid_auto)

    def test_rejects_per_tenant_org_policies_override(self):
        manifest = copy.deepcopy(self.example_manifest)
        manifest["org_policies"] = {
            "gcp.restrictServiceUsage": {"inherit_from_parent": False}
        }
        with self.assertRaises(jsonschema.ValidationError):
            self.validator.validate(manifest)

    def test_rejects_invalid_lifecycle_state_and_subnet_format(self):
        bad_lifecycle = copy.deepcopy(self.example_manifest)
        bad_lifecycle["lifecycle_state"] = "deleted"
        with self.assertRaises(jsonschema.ValidationError):
            self.validator.validate(bad_lifecycle)

        bad_subnet = copy.deepcopy(self.example_manifest)
        bad_subnet["projects"]["app-0"]["shared_vpc_subnets"] = [
            "missing-region-slash"
        ]
        with self.assertRaises(jsonschema.ValidationError):
            self.validator.validate(bad_subnet)

    def test_stage_files_contain_no_opsec_or_customer_terms(self):
        checked = 0
        for path in sorted(_STAGE_DIR.rglob("*")):
            if not path.is_file() or ".terraform" in path.parts:
                continue
            content = path.read_text(encoding="utf-8")
            checked += 1
            for pattern in _DISALLOWED_OPSEC_PATTERNS:
                self.assertIsNone(
                    pattern.search(content),
                    f"Disallowed OPSEC match {pattern.pattern!r} in {path}",
                )
        self.assertGreaterEqual(checked, 6)

    def test_stage_il5_guardrails_and_cmek_wiring(self):
        versions_tf = (_STAGE_DIR / "versions.tf").read_text(encoding="utf-8")
        vars_tf = (_STAGE_DIR / "variables.tf").read_text(encoding="utf-8")
        main_tf = (_STAGE_DIR / "main.tf").read_text(encoding="utf-8")
        self.assertIn('source  = "hashicorp/time"', versions_tf)
        self.assertIn('default     = "us-east4"', vars_tf)
        self.assertIn('variable "force_destroy"', vars_tf)
        self.assertIn('variable "folder_ids"', vars_tf)
        self.assertIn(
            'data "google_bigquery_default_service_account" "tenant_bq"',
            main_tf,
        )
        self.assertIn(
            'resource "time_sleep" "tenant_bq_sa_propagation"', main_tf
        )
        self.assertIn(
            'resource "google_kms_crypto_key_iam_member" '
            '"tenant_bigquery_cmek"',
            main_tf,
        )
        self.assertIn("_cmek_companion_apis", main_tf)


if __name__ == "__main__":
    unittest.main()
