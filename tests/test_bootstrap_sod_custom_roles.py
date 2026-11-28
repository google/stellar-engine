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

"""Unit tests for Stage 0 opt-in separation-of-duties custom IAM roles."""

import pathlib
import re
import unittest

import yaml

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
_BOOTSTRAP_DIR = _REPO_ROOT / "fast/stages-aw/0-bootstrap"
_BASE_ROLES_DIR = _BOOTSTRAP_DIR / "data/custom-roles"
_SOD_ROLES_DIR = _BOOTSTRAP_DIR / "data/custom-roles-sod"

_EXPECTED_SOD_FILES = {
    "tag_editor.yaml": "tagEditor",
    "tenant_key_manager.yaml": "tenantKeyManager",
    "tenant_project_admin.yaml": "tenantProjectAdmin",
    "tenant_readonly.yaml": "tenantReadOnly",
}

_ROLE_ID_RE = re.compile(r"^[a-zA-Z0-9_.]{3,64}$")
_PERM_RE = re.compile(r"^[a-z][a-z0-9]*\.[a-zA-Z][a-zA-Z0-9_]*\.[a-zA-Z0-9_]+$")

_FORBIDDEN_LOG_PAYLOAD_READ_PERMS = {
    "logging.logEntries.list",
    "logging.views.access",
}

_FORBIDDEN_KEY_MANAGER_PERMS = {
    "cloudkms.cryptoKeyVersions.useToEncrypt",
    "cloudkms.cryptoKeyVersions.useToDecrypt",
    "cloudkms.cryptoKeyVersions.rawEncrypt",
    "cloudkms.cryptoKeyVersions.rawDecrypt",
    "cloudkms.cryptoKeyVersions.macSign",
    "cloudkms.cryptoKeyVersions.macVerify",
    "cloudkms.cryptoKeyVersions.asymmetricSign",
    "cloudkms.cryptoKeyVersions.asymmetricDecrypt",
    "cloudkms.cryptoKeyVersions.useToEncryptViaDelegation",
    "cloudkms.cryptoKeyVersions.useToDecryptViaDelegation",
    "cloudkms.cryptoKeys.setIamPolicy",
    "cloudkms.keyRings.setIamPolicy",
    "cloudkms.importJobs.setIamPolicy",
    "resourcemanager.projects.setIamPolicy",
    *_FORBIDDEN_LOG_PAYLOAD_READ_PERMS,
}

_FORBIDDEN_READONLY_PERMS = {
    "storage.objects.get",
    "secretmanager.versions.access",
    "bigquery.tables.getData",
    "compute.instances.getSerialPortOutput",
    "compute.instances.getScreenshot",
    "compute.instances.getGuestAttributes",
    "container.clusters.getCredentials",
    "redis.instances.getAuthString",
    *_FORBIDDEN_LOG_PAYLOAD_READ_PERMS,
}

_FORBIDDEN_READONLY_VERB_PREFIXES = (
    "access",
    "actAs",
    "add",
    "attach",
    "cancel",
    "connect",
    "consume",
    "create",
    "delete",
    "destroy",
    "detach",
    "disable",
    "drop",
    "enable",
    "execute",
    "impersonate",
    "import",
    "instantiate",
    "login",
    "patch",
    "pause",
    "publish",
    "purge",
    "put",
    "remove",
    "reset",
    "restart",
    "restore",
    "resume",
    "run",
    "set",
    "sign",
    "snapshot",
    "start",
    "stop",
    "suspend",
    "undelete",
    "update",
    "upload",
    "use",
    "write",
)

_FORBIDDEN_PROJECT_ADMIN_PERMS = {
    "cloudbuild.builds.create",
    "compute.instances.setMetadata",
    "compute.instances.setTags",
    "iam.serviceAccounts.delete",
    "iam.serviceAccounts.disable",
    "iam.serviceAccounts.enable",
    "iam.serviceAccounts.undelete",
    "iam.serviceAccounts.setIamPolicy",
    "iam.serviceAccounts.getAccessToken",
    "iam.serviceAccounts.getOpenIdToken",
    "iam.serviceAccounts.signBlob",
    "iam.serviceAccounts.signJwt",
    "iam.serviceAccounts.implicitDelegation",
    "iam.serviceAccounts.actAs",
    "iam.serviceAccountKeys.create",
    "iam.serviceAccountApiKeyBindings.create",
    "iam.serviceAccountApiKeyBindings.delete",
    "iam.serviceAccountApiKeyBindings.undelete",
    "resourcemanager.projects.setIamPolicy",
    "resourcemanager.tagValueBindings.create",
    "resourcemanager.tagValueBindings.delete",
    "secretmanager.versions.access",
}

# Tag binding writes belong to tag_editor alone.
_TAG_BINDING_WRITE_VERBS = {"createTagBinding", "deleteTagBinding"}

_KNOWN_INVALID_OR_TESTING_GCP_PERMS = {
    "resourcemanager.resourceTagBindings.list",
    # TESTING-level custom role permissions prohibited in GA SoD roles.
    "cloudtasks.locations.get",
    "cloudtasks.locations.list",
    "cloudtasks.queues.getIamPolicy",
    "compute.instances.getGuestAttributes",
    "compute.interconnectAttachments.get",
    "compute.interconnectAttachments.list",
    "compute.interconnects.get",
    "compute.interconnects.list",
    "compute.securityPolicies.get",
    "compute.securityPolicies.list",
    "monitoring.notificationChannels.create",
    "monitoring.notificationChannels.delete",
    "monitoring.notificationChannels.get",
    "monitoring.notificationChannels.list",
    "monitoring.notificationChannels.update",
}

_OPSEC_FORBIDDEN_PATTERNS = (
    re.compile(r"\b(go|cl|b)/[a-zA-Z0-9_-]+"),
    re.compile(
        r"[a-zA-Z0-9._%+-]+@(?!example\.com\b)[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    ),
    re.compile(r"\b\d{10,}\b"),
    re.compile(r"\u2014|\.\.\."),
)


def _load_role(filename: str) -> dict:
    path = _SOD_ROLES_DIR / filename
    return yaml.safe_load(path.read_text(encoding="utf-8"))


class TestBootstrapSodCustomRoles(unittest.TestCase):
    def test_sod_roles_isolated_from_default_custom_roles_dir(self):
        base_files = {p.name for p in _BASE_ROLES_DIR.glob("*.yaml")}
        sod_files = {p.name for p in _SOD_ROLES_DIR.glob("*.yaml")}

        self.assertEqual(sod_files, set(_EXPECTED_SOD_FILES))
        self.assertTrue(
            base_files.isdisjoint(sod_files),
            f"SoD roles must not live in default data/custom-roles/: "
            f"{base_files & sod_files}",
        )

    def test_all_sod_yaml_schema_syntax_and_cleanliness(self):
        for filename, expected_name in _EXPECTED_SOD_FILES.items():
            with self.subTest(file=filename):
                path = _SOD_ROLES_DIR / filename
                raw = path.read_text(encoding="utf-8")
                self.assertIn("Copyright 2026 Google LLC", raw)
                self.assertIn("Apache License, Version 2.0", raw)

                for pattern in _OPSEC_FORBIDDEN_PATTERNS:
                    self.assertIsNone(
                        pattern.search(raw),
                        f"Forbidden pattern {pattern.pattern} matched in "
                        f"{filename}",
                    )

                data = yaml.safe_load(raw)
                self.assertIsInstance(data, dict)
                self.assertEqual(data.get("name"), expected_name)
                self.assertRegex(data["name"], _ROLE_ID_RE)
                self.assertIsInstance(data.get("title"), str)
                self.assertTrue(data["title"].strip())
                self.assertIsInstance(data.get("description"), str)
                self.assertTrue(data["description"].endswith("."))
                self.assertIn(
                    data.get("stage"),
                    {"ALPHA", "BETA", "GA", "DEPRECATED", "DISABLED", "EAP"},
                )

                perms = data.get("includedPermissions")
                self.assertIsInstance(perms, list)
                self.assertTrue(perms)
                self.assertEqual(
                    len(perms),
                    len(set(perms)),
                    f"Duplicate permissions found in {filename}",
                )
                for perm in perms:
                    self.assertIsInstance(perm, str)
                    self.assertRegex(
                        perm,
                        _PERM_RE,
                        f"Invalid GCP permission syntax in {filename}: {perm}",
                    )
                    self.assertNotIn(
                        perm,
                        _KNOWN_INVALID_OR_TESTING_GCP_PERMS,
                        f"Unsupported or TESTING GCP permission in "
                        f"{filename}: {perm}",
                    )

    def test_payload_read_prohibition_across_key_manager_and_readonly(self):
        for filename in ("tenant_key_manager.yaml", "tenant_readonly.yaml"):
            with self.subTest(file=filename):
                perms = set(_load_role(filename)["includedPermissions"])
                overlap = perms & _FORBIDDEN_LOG_PAYLOAD_READ_PERMS
                self.assertEqual(
                    overlap,
                    set(),
                    f"{filename} must exclude log payload read permissions: "
                    f"{overlap}",
                )

    def test_tenant_key_manager_excludes_crypto_data_plane_and_iam_writes(self):
        perms = set(
            _load_role("tenant_key_manager.yaml")["includedPermissions"]
        )

        # Required KMS lifecycle capabilities.
        for required in (
            "cloudkms.keyRings.create",
            "cloudkms.cryptoKeys.create",
            "cloudkms.cryptoKeyVersions.create",
            "cloudkms.cryptoKeyVersions.destroy",
        ):
            self.assertIn(required, perms)

        # Strictly exclude crypto data plane, log payload reads, and IAM writes.
        overlap = perms & _FORBIDDEN_KEY_MANAGER_PERMS
        self.assertEqual(overlap, set(), f"Forbidden KMS perms: {overlap}")
        for perm in perms:
            verb = perm.rsplit(".", 1)[-1]
            self.assertNotEqual(
                verb,
                "setIamPolicy",
                f"tenant_key_manager must not grant setIamPolicy: {perm}",
            )
            self.assertNotRegex(
                verb,
                r"(Encrypt|Decrypt|Sign|Verify|Decapsulate)",
                f"tenant_key_manager must exclude crypto data plane: {perm}",
            )

    def test_tenant_readonly_is_metadata_read_only(self):
        perms = set(_load_role("tenant_readonly.yaml")["includedPermissions"])

        overlap = perms & _FORBIDDEN_READONLY_PERMS
        self.assertEqual(
            overlap, set(), f"Forbidden read-only perms: {overlap}"
        )

        for perm in perms:
            verb = perm.rsplit(".", 1)[-1]
            self.assertFalse(
                verb.startswith(_FORBIDDEN_READONLY_VERB_PREFIXES),
                f"Non-read-only verb in tenant_readonly: {perm}",
            )
            self.assertNotIn(
                "setIamPolicy",
                perm,
                f"tenant_readonly must not grant setIamPolicy: {perm}",
            )

    def test_tag_editor_is_least_privilege_without_org_iam_or_policy_writes(
        self,
    ):
        perms = set(_load_role("tag_editor.yaml")["includedPermissions"])

        self.assertIn("resourcemanager.tagValueBindings.create", perms)
        self.assertIn("resourcemanager.tagValueBindings.delete", perms)
        self.assertIn("resourcemanager.hierarchyNodes.listTagBindings", perms)
        self.assertIn("resourcemanager.hierarchyNodes.listEffectiveTags", perms)

        allowed_verbs = {
            "get",
            "list",
            "createTagBinding",
            "deleteTagBinding",
            "listEffectiveTags",
            "listTagBindings",
        }
        allowed_special = {
            "resourcemanager.tagValueBindings.create",
            "resourcemanager.tagValueBindings.delete",
        }

        for perm in perms:
            self.assertFalse(
                perm.startswith("orgpolicy."),
                f"tag_editor must not touch orgpolicy: {perm}",
            )
            self.assertFalse(
                perm.startswith("accesscontextmanager."),
                f"tag_editor must not read VPC Service Controls: {perm}",
            )
            self.assertFalse(
                perm.endswith(".setIamPolicy"),
                f"tag_editor must not grant setIamPolicy: {perm}",
            )
            self.assertNotIn(
                perm,
                {
                    "resourcemanager.tagKeys.create",
                    "resourcemanager.tagKeys.update",
                    "resourcemanager.tagKeys.delete",
                    "resourcemanager.tagValues.create",
                    "resourcemanager.tagValues.update",
                    "resourcemanager.tagValues.delete",
                    "resourcemanager.hierarchyNodes.createTagBinding",
                    "resourcemanager.hierarchyNodes.deleteTagBinding",
                },
            )
            verb = perm.rsplit(".", 1)[-1]
            self.assertTrue(
                verb in allowed_verbs or perm in allowed_special,
                f"Unexpected permission in tag_editor: {perm}",
            )

    def test_only_tag_editor_writes_tag_bindings(self):
        tag_value_writes = {
            "resourcemanager.tagValueBindings.create",
            "resourcemanager.tagValueBindings.delete",
        }
        for path in sorted(_SOD_ROLES_DIR.glob("*.yaml")):
            if path.name == "tag_editor.yaml":
                continue
            perms = _load_role(path.name)["includedPermissions"]
            for perm in perms:
                with self.subTest(role=path.name, perm=perm):
                    self.assertNotIn(
                        perm.rsplit(".", 1)[-1], _TAG_BINDING_WRITE_VERBS
                    )
                    self.assertNotIn(perm, tag_value_writes)

    def test_tenant_project_admin_blocks_privilege_escalation(self):
        perms = set(
            _load_role("tenant_project_admin.yaml")["includedPermissions"]
        )

        overlap = perms & _FORBIDDEN_PROJECT_ADMIN_PERMS
        self.assertEqual(
            overlap, set(), f"Privilege escalation perms found: {overlap}"
        )

        for perm in perms:
            self.assertFalse(
                perm.endswith(".setIamPolicy"),
                f"tenant_project_admin must exclude setIamPolicy: {perm}",
            )
            self.assertFalse(
                perm.startswith("cloudkms."),
                f"tenant_project_admin must exclude Cloud KMS (SoD): {perm}",
            )
            self.assertFalse(
                perm.startswith("orgpolicy."),
                f"tenant_project_admin must exclude orgpolicy: {perm}",
            )
            self.assertFalse(
                perm.startswith("iam.serviceAccountKeys."),
                f"tenant_project_admin must exclude SA keys: {perm}",
            )
            self.assertFalse(
                perm.startswith("iam.serviceAccountApiKeyBindings."),
                f"tenant_project_admin must exclude SA API key bindings: "
                f"{perm}",
            )
            verb = perm.rsplit(".", 1)[-1]
            self.assertNotIn(
                verb,
                _TAG_BINDING_WRITE_VERBS,
                f"tenant_project_admin must leave tag binding writes to "
                f"tag_editor: {perm}",
            )
            self.assertFalse(
                perm.startswith("resourcemanager.tagValueBindings."),
                f"tenant_project_admin must leave tag value bindings to "
                f"tag_editor: {perm}",
            )
            if perm.startswith("resourcemanager.tagHolds."):
                self.assertEqual(
                    verb,
                    "list",
                    f"tenant_project_admin must not change tag holds: {perm}",
                )

    def test_stage0_wires_opt_in_default_false_and_snake_case_keys(self):
        variables_tf = (_BOOTSTRAP_DIR / "variables.tf").read_text(
            encoding="utf-8"
        )
        self.assertRegex(
            variables_tf,
            r'variable "enable_tenant_sod_roles"\s*\{[\s\S]*?'
            r"default\s*=\s*false[\s\S]*?\}",
        )

        org_tf = (_BOOTSTRAP_DIR / "organization.tf").read_text(
            encoding="utf-8"
        )
        self.assertIn("data/custom-roles-sod", org_tf)
        self.assertRegex(
            org_tf,
            r"var\.deploy_org_resources\.custom_roles\s*&&\s*"
            r"var\.enable_tenant_sod_roles",
        )
        self.assertRegex(
            org_tf,
            r"_sod_custom_roles\s*=\s*\{\s*for\s+k,\s*v\s+in\s+"
            r"local\._sod_custom_roles_raw\s*:\s*k\s*=>\s*\{\s*"
            r'name\s*=\s*lookup\(v,\s*"name",\s*k\)',
        )


if __name__ == "__main__":
    unittest.main()
