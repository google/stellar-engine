# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Validates opt-in org policy guardrail packs and Day-2 ATO documentation."""

import json
import pathlib
import re
import unittest

import jsonschema
import yaml

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
_PACKS_DIR = _REPO_ROOT / "fast/assets/org-policy-packs"
_STAGE0_ORG_POLICIES_DIR = (
    _REPO_ROOT / "fast/stages-aw/0-bootstrap/data/org-policies"
)
_SCHEMAS_DIR = _REPO_ROOT / "modules/organization-se/schemas"
_ORG_POLICIES_SCHEMA = _SCHEMAS_DIR / "org-policies.schema.json"
_CUSTOM_CONSTRAINTS_SCHEMA = (
    _SCHEMAS_DIR / "org-policy-custom-constraint.schema.json"
)

_EXPECTED_GKE_MANAGED_CONSTRAINTS = {
    "container.managed.denyServiceExternalIPs",
    "container.managed.disableInsecureKubeletReadOnlyPort",
    "container.managed.disableRBACSystemBindings",
    "container.managed.disallowDefaultComputeServiceAccount",
    "container.managed.enableBinaryAuthorization",
    "container.managed.enableCloudLogging",
    "container.managed.enableNetworkPolicy",
    "container.managed.enablePrivateNodes",
    "container.managed.enableSecretsEncryption",
    "container.managed.enableSecurityBulletinNotifications",
    "container.managed.enableWorkloadIdentityFederation",
    "container.managed.restrictControlPlaneEgress",
}

_EXPECTED_COMPUTE_DATA_BOOLEAN_CONSTRAINTS = {
    "compute.managed.disableNonFIPSMachineTypes",
    "compute.managed.disableVmsWithContainerStartupAgent",
    "compute.managed.vmCanIpForward",
    "dataflow.managed.disableUsePublicIps",
}

_EXPECTED_CUSTOM_CONSTRAINTS = {
    "custom.artifactRegistryDisallowRemoteRepos",
    "custom.bigqueryDisallowExternalDatasets",
    "custom.cloudBuildWorkerPoolNoPublicEgress",
    "custom.composerRequirePrivateIp",
    "custom.composerRestrictWebServerAccess",
    "custom.dataprocRequireInternalIp",
    "custom.dnsDisallowPublicZones",
    "custom.gkeRequirePrivateControlPlane",
    "custom.preventServiceAccountPrivilegeEscalation",
    "custom.pubsubDisallowPushSubscriptions",
}

_ALLOWED_METHOD_TYPES = {"CREATE", "UPDATE", "DELETE"}
_ALLOWED_ACTION_TYPES = {"ALLOW", "DENY"}
_ALLOWED_PLACEHOLDER_IDS = {"123456789012", "987654321098"}
_ALLOWED_TICKET_PREFIXES = {"ADR", "ISSUE"}
_DOC_FILES = [
    _PACKS_DIR / "README.md",
    _REPO_ROOT / "docs/guardrails-rubric-and-test-plan.md",
    _REPO_ROOT / "docs/assured-workloads-operations.md",
    _REPO_ROOT / "docs/adr/template.md",
]

_NUMERIC_ID_RE = re.compile(r"\b\d{10,13}\b")
_EMAIL_RE = re.compile(r"[\w.+-]+@([\w.-]+\.[a-zA-Z]{2,})")
_INTERNAL_LINK_OR_DOMAIN_RE = re.compile(
    r"(?:\.(?:mil|corp\.google\.com)\b|\b(?:go|b|cl)/[a-zA-Z0-9_-]+)",
    re.IGNORECASE,
)
_TICKET_ID_RE = re.compile(r"\b([A-Z]{2,6})-\d{4,}\b")
_TEMPLATE_EXPR_RE = re.compile(r"[\$%]\{")
_BOLD_COLON_BULLET_RE = re.compile(r"^\s*[-*]\s+\*\*[^*]+:\*\*")
_HEADING_RE = re.compile(r"^#{1,6}\s+(.*)$")
_INLINE_CODE_RE = re.compile(r"`[^`]+`")
_FIRST_PERSON_RE = re.compile(r"\b(?:I|we|my|our)\b", re.IGNORECASE)


def _strip_fenced_code_blocks(text):
    """Returns non-code lines outside triple-backtick fenced blocks."""
    in_fence = False
    prose_lines = []
    for line in text.splitlines():
        if line.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if not in_fence:
            prose_lines.append(line)
    return prose_lines


class TestOrgPolicyGuardrailPacks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.org_policies_schema = json.loads(
            _ORG_POLICIES_SCHEMA.read_text(encoding="utf-8")
        )
        cls.custom_constraints_schema = json.loads(
            _CUSTOM_CONSTRAINTS_SCHEMA.read_text(encoding="utf-8")
        )

    def _load_yaml(self, path):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        self.assertIsInstance(
            data,
            dict,
            f"Expected YAML mapping in {path.relative_to(_REPO_ROOT)}",
        )
        self.assertTrue(
            data, f"Expected non-empty YAML in {path.relative_to(_REPO_ROOT)}"
        )
        return data

    def test_all_pack_yamls_parse_cleanly(self):
        yaml_files = sorted(_PACKS_DIR.rglob("*.yaml"))
        self.assertTrue(yaml_files, "No guardrail pack YAML files found.")
        for path in yaml_files:
            self._load_yaml(path)

    def test_gke_managed_pack_contains_all_twelve_constraints(self):
        gke_path = _PACKS_DIR / "gke-managed/gke_managed_policy.yaml"
        data = self._load_yaml(gke_path)
        jsonschema.validate(instance=data, schema=self.org_policies_schema)

        self.assertEqual(set(data.keys()), _EXPECTED_GKE_MANAGED_CONSTRAINTS)
        for name, spec in data.items():
            self.assertEqual(
                spec.get("rules"),
                [{"enforce": True}],
                f"{name} should enforce true by default.",
            )

    def test_compute_data_managed_pack_schema_and_values(self):
        managed_path = _PACKS_DIR / "compute-data-managed/managed_policy.yaml"
        data = self._load_yaml(managed_path)
        jsonschema.validate(instance=data, schema=self.org_policies_schema)

        expected_keys = _EXPECTED_COMPUTE_DATA_BOOLEAN_CONSTRAINTS | {
            "cloudkms.allowedProtectionLevels"
        }
        self.assertEqual(set(data.keys()), expected_keys)

        for name in _EXPECTED_COMPUTE_DATA_BOOLEAN_CONSTRAINTS:
            self.assertEqual(
                data[name].get("rules"),
                [{"enforce": True}],
                f"{name} should enforce true by default.",
            )

        self.assertEqual(
            data["cloudkms.allowedProtectionLevels"].get("rules"),
            [{"allow": {"values": ["is:HSM"]}}],
        )

    def test_policy_pack_filenames_match_stage0_factory_without_collision(self):
        stage0_names = {p.name for p in _STAGE0_ORG_POLICIES_DIR.glob("*.yaml")}
        self.assertTrue(stage0_names, "No Stage 0 org policy YAML files found.")

        constraints_dir = (
            _PACKS_DIR / "custom-constraints-dry-run/constraints"
        ).resolve()
        policy_files = [
            p
            for p in sorted(_PACKS_DIR.rglob("*.yaml"))
            if constraints_dir not in p.resolve().parents
        ]
        self.assertTrue(policy_files, "No pack policy YAML files found.")

        for path in policy_files:
            rel = path.relative_to(_REPO_ROOT)
            self.assertTrue(
                path.name.endswith("_policy.yaml"),
                f"Policy pack file {rel} must end in _policy.yaml.",
            )
            self.assertNotIn(
                path.name,
                stage0_names,
                f"Policy pack file {rel} collides with Stage 0 org-policies.",
            )

    def test_custom_constraints_definitions_and_dry_run_bindings(self):
        constraints_dir = _PACKS_DIR / "custom-constraints-dry-run/constraints"
        constraint_files = sorted(constraints_dir.glob("*.yaml"))
        self.assertTrue(
            constraint_files, "No custom constraint YAML files found."
        )

        merged_constraints = {}
        for path in constraint_files:
            data = self._load_yaml(path)
            jsonschema.validate(
                instance=data, schema=self.custom_constraints_schema
            )
            for name, definition in data.items():
                self.assertNotIn(
                    name,
                    merged_constraints,
                    f"Duplicate custom constraint key: {name}",
                )
                merged_constraints[name] = definition

        self.assertEqual(
            set(merged_constraints.keys()), _EXPECTED_CUSTOM_CONSTRAINTS
        )

        for name, definition in merged_constraints.items():
            self.assertIn(
                definition.get("action_type"),
                _ALLOWED_ACTION_TYPES,
                f"{name} has invalid action_type.",
            )
            resource_types = definition.get("resource_types")
            self.assertIsInstance(resource_types, list)
            self.assertTrue(
                resource_types, f"{name} must specify resource_types."
            )
            for rtype in resource_types:
                self.assertRegex(
                    rtype,
                    r"^[a-z0-9.-]+\.googleapis\.com/[A-Za-z0-9]+$",
                    f"{name} has invalid resource_type {rtype}.",
                )

            method_types = definition.get("method_types")
            self.assertIsInstance(method_types, list)
            self.assertTrue(method_types, f"{name} must specify method_types.")
            self.assertTrue(
                set(method_types).issubset(_ALLOWED_METHOD_TYPES),
                f"{name} has unsupported method_types: {method_types}",
            )

            for text_field in ("display_name", "description", "condition"):
                value = definition.get(text_field)
                self.assertIsInstance(value, str)
                self.assertTrue(
                    value.strip(), f"{name} must define non-empty {text_field}."
                )

            self.assertIsNone(
                _TEMPLATE_EXPR_RE.search(definition["condition"]),
                f"{name} condition contains Terraform template syntax.",
            )

        iam_cond = merged_constraints[
            "custom.preventServiceAccountPrivilegeEscalation"
        ]["condition"]
        self.assertIn("MemberTypeMatches", iam_cond)
        self.assertIn("iam.googleapis.com/ServiceAccount", iam_cond)
        self.assertIn("developer.gserviceaccount.com", iam_cond)
        self.assertIn("appspot.gserviceaccount.com", iam_cond)
        self.assertNotIn("iam.gserviceaccount.com", iam_cond)
        self.assertNotIn(".contains(", iam_cond)

        bindings_path = (
            _PACKS_DIR
            / "custom-constraints-dry-run"
            / "policies"
            / "custom_constraints_dry_run_policy.yaml"
        )
        bindings = self._load_yaml(bindings_path)
        jsonschema.validate(instance=bindings, schema=self.org_policies_schema)

        expected_dry_run_keys = {
            f"dry_run:{name}" for name in _EXPECTED_CUSTOM_CONSTRAINTS
        }
        self.assertEqual(set(bindings.keys()), expected_dry_run_keys)
        for key, spec in bindings.items():
            self.assertEqual(
                spec.get("rules"),
                [{"enforce": True}],
                f"{key} should set rules: [{{enforce: true}}].",
            )

    def test_no_sensitive_identifiers_in_packs_or_docs(self):
        target_files = sorted(_PACKS_DIR.rglob("*.yaml")) + _DOC_FILES
        for path in target_files:
            self.assertTrue(path.exists(), f"Missing expected file: {path}")
            rel = path.relative_to(_REPO_ROOT)
            text = path.read_text(encoding="utf-8")

            bad_ids = [
                match
                for match in _NUMERIC_ID_RE.findall(text)
                if match not in _ALLOWED_PLACEHOLDER_IDS
            ]
            self.assertEqual(
                bad_ids, [], f"Non-placeholder numeric IDs in {rel}: {bad_ids}"
            )

            bad_emails = []
            for match in _EMAIL_RE.finditer(text):
                domain = match.group(1).lower()
                if domain != "example.com" and not (
                    domain.startswith("acme-")
                    and domain.endswith(".iam.gserviceaccount.com")
                ):
                    bad_emails.append(match.group(0))
            self.assertEqual(
                bad_emails,
                [],
                f"Non-placeholder email addresses in {rel}: {bad_emails}",
            )

            internal_matches = _INTERNAL_LINK_OR_DOMAIN_RE.findall(text)
            self.assertEqual(
                internal_matches,
                [],
                f"Internal link or domain found in {rel}: {internal_matches}",
            )

            bad_tickets = [
                m.group(0)
                for m in _TICKET_ID_RE.finditer(text)
                if m.group(1) not in _ALLOWED_TICKET_PREFIXES
            ]
            self.assertEqual(
                bad_tickets,
                [],
                f"Unexpected ticket identifier in {rel}: {bad_tickets}",
            )

    def test_docs_follow_styleguide_prose_conventions(self):
        for path in _DOC_FILES:
            rel = path.relative_to(_REPO_ROOT)
            prose_lines = _strip_fenced_code_blocks(
                path.read_text(encoding="utf-8")
            )
            for idx, line in enumerate(prose_lines, start=1):
                self.assertNotIn(
                    "\u2014", line, f"Em-dash found in {rel} prose line {idx}."
                )
                self.assertNotIn(
                    "...", line, f"Ellipsis found in {rel} prose line {idx}."
                )
                self.assertNotEqual(
                    line.strip(),
                    "---",
                    f"Horizontal rule divider found in {rel} prose line {idx}.",
                )
                self.assertIsNone(
                    _BOLD_COLON_BULLET_RE.match(line),
                    f"Bold colon bullet lead-in in {rel} line {idx}: {line}",
                )
                heading_match = _HEADING_RE.match(line)
                if heading_match:
                    heading_text = heading_match.group(1)
                    self.assertNotIn(
                        "`",
                        heading_text,
                        f"Backtick inside heading in {rel}: {line}",
                    )
                    self.assertNotIn(
                        "&",
                        heading_text,
                        f"Ampersand inside heading in {rel}: {line}",
                    )
                prose_no_code = _INLINE_CODE_RE.sub("", line)
                self.assertNotIn(
                    "&",
                    prose_no_code,
                    f"Ampersand in prose in {rel} line {idx}: {line}",
                )
                self.assertIsNone(
                    _FIRST_PERSON_RE.search(prose_no_code),
                    f"First-person pronoun in {rel} line {idx}: {line}",
                )


if __name__ == "__main__":
    unittest.main()
