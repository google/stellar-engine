#!/usr/bin/env python3
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

"""Regression tests for Incident Response runbook operator placeholder hydration.

These tests exist because IR runbooks were being delivered inside signed ATO
packages with raw ``[KMS_PROJECT_ID]`` / ``[KEYRING_NAME]`` / ``[SA_EMAIL]``
tokens in the copy/paste ``gcloud`` commands, even though the engine had already
extracted those values from the Terraform. They pin down three properties that
must never regress:

1. DERIVABLE placeholders are hydrated with the real discovered value.
2. A DERIVABLE placeholder with no source value fails closed as
   ``[NOT DETERMINED FROM SOURCE]`` -- it is never replaced with a
   plausible-looking invention.
3. RUNTIME placeholders (the attacker's IP, the compromised Pod) are never
   guessed; they become unmistakable operator fill-in markers.
"""

import json
import os
import re
import sys
import tempfile
import unittest
from typing import Any, Dict

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.abspath(os.path.join(TESTS_DIR, "..", "scripts"))
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

import generate_compliance_artifacts
from audit_log import reset_audit_log
from runbook_hydration import (
    DERIVABLE_TOKENS,
    NOT_DETERMINED,
    RUNTIME_TOKENS,
    build_operator_context,
    collect_service_account_emails,
    find_operator_tokens,
    hydrate_operator_placeholders,
    render_discovered_context_block,
    resolve_organization_domain,
)


def _rich_inventory() -> Dict[str, Any]:
    """Builds an inventory where every DERIVABLE placeholder is resolvable.

    Returns:
        A system inventory dictionary with multiple buckets, KMS keys and
        service accounts, so deterministic selection can also be asserted.
    """
    return {
        "system_information": {
            "system_name": "Hydration Test Platform",
            "system_abbreviation": "HTP",
            "organization": "Department of Example",
            "organization_domain": "example-agency.gov",
            "org_id": "123456789012",
            "impact_level": "IL5",
            "compliance_baseline": "NIST SP 800-53 Rev. 5 / DoD IL5",
        },
        "personnel_roles": {
            "authorizing_official": {"name": "Alex Taylor", "email": "ao@example.gov"},
            "system_owner": {"name": "Jordan Smith", "email": "so@example.gov"},
            "issm": {"name": "Morgan Johnson", "email": "issm@example.gov"},
            "isso": {"name": "Riley Davis", "email": "isso@example.gov"},
        },
        "security_scanners": {
            "enabled": False,
            "run_checkov": False,
            "run_semgrep": False,
            "ingest_sarif": False,
        },
        "infrastructure_components": {
            "storage_buckets": [
                {"name": "bkt-zeta-audit-logs", "location": "us-east4"},
                {"name": "bkt-alpha-artifacts", "location": "us-east4"},
            ],
            "kms_keys": [
                {
                    "name": "key-zeta-bucket-cmek",
                    "key_ring": "projects/prj-security/locations/us-east4/keyRings/kr-htp",
                },
                {
                    "name": "key-alpha-disk-cmek",
                    "key_ring": "projects/prj-security/locations/us-east4/keyRings/kr-htp",
                },
            ],
            "service_accounts": [
                {
                    "account_id": "sa-zeta-pipeline",
                    "project": "prj-tooling",
                    "email": "sa-zeta-pipeline@prj-tooling.iam.gserviceaccount.com",
                },
                {
                    "account_id": "sa-alpha-workload",
                    "project": "prj-workload",
                    "email": "sa-alpha-workload@prj-workload.iam.gserviceaccount.com",
                },
            ],
        },
    }


def _barren_inventory() -> Dict[str, Any]:
    """Builds an inventory from which no DERIVABLE placeholder can be resolved.

    Returns:
        A system inventory dictionary carrying only an organization display
        name, which must never be converted into a DNS domain.
    """
    return {
        "system_information": {
            "system_name": "Barren Platform",
            "system_abbreviation": "BP",
            "organization": "Department of Example",
            "impact_level": "IL4",
            "compliance_baseline": "NIST SP 800-53 Rev. 5 / DoD IL4",
        },
        "personnel_roles": {
            "authorizing_official": {"name": "Alex Taylor", "email": "ao@example.gov"},
            "system_owner": {"name": "Jordan Smith", "email": "so@example.gov"},
            "issm": {"name": "Morgan Johnson", "email": "issm@example.gov"},
            "isso": {"name": "Riley Davis", "email": "isso@example.gov"},
        },
        "security_scanners": {
            "enabled": False,
            "run_checkov": False,
            "run_semgrep": False,
            "ingest_sarif": False,
        },
        "infrastructure_components": {
            "storage_buckets": [],
            "kms_keys": [],
            "service_accounts": [],
        },
    }


class TestRunbookOperatorHydration(unittest.TestCase):
    """Unit-level tests over the placeholder classification and substitution."""

    def test_derivable_tokens_are_hydrated_with_real_values(self) -> None:
        """Every DERIVABLE token resolves to the value discovered in the inventory."""
        template = (
            "gcloud kms keys versions disable [VERSION] --key=[KEY_NAME] "
            "--keyring=[KEYRING_NAME] --location=[LOCATION] --project=[KMS_PROJECT_ID]\n"
            "gcloud storage rewrite gs://[BUCKET_NAME]/**\n"
            'logName="organizations/[ORG_ID]/logs/cloudaudit.googleapis.com"\n'
            "user.sample@[ORGANIZATION_DOMAIN]\n"
        )
        result = hydrate_operator_placeholders(template, _rich_inventory())

        self.assertIn("--key=key-alpha-disk-cmek", result)
        self.assertIn("--keyring=kr-htp", result)
        self.assertIn("--location=us-east4", result)
        self.assertIn("--project=prj-security", result)
        self.assertIn("gs://bkt-alpha-artifacts/**", result)
        self.assertIn("organizations/123456789012/logs", result)
        self.assertIn("user.sample@example-agency.gov", result)
        self.assertNotIn(NOT_DETERMINED, result)

    def test_selection_is_deterministic_sorted_first(self) -> None:
        """Multiple candidates resolve to the first in sorted order, every run."""
        inventory = _rich_inventory()
        first = build_operator_context(inventory)
        second = build_operator_context(inventory)

        self.assertEqual(first.values["BUCKET_NAME"], "bkt-alpha-artifacts")
        self.assertEqual(first.values["KEY_NAME"], "key-alpha-disk-cmek")
        self.assertEqual(first.values, second.values)

    def test_alternatives_are_listed_not_silently_dropped(self) -> None:
        """The provenance table names every other discovered candidate."""
        context = build_operator_context(_rich_inventory())
        block = render_discovered_context_block(
            context, tokens=["BUCKET_NAME", "KEY_NAME", "SA_EMAIL"]
        )

        self.assertIn("`bkt-alpha-artifacts`", block)
        self.assertIn("`bkt-zeta-audit-logs`", block)
        self.assertIn("`key-zeta-bucket-cmek`", block)
        self.assertIn("sa-zeta-pipeline@prj-tooling.iam.gserviceaccount.com", block)
        self.assertIn("examples drawn from the discovered inventory", block)

    def test_missing_derivable_values_fail_closed(self) -> None:
        """An unresolvable DERIVABLE token renders as the fail-closed marker."""
        template = (
            "--key=[KEY_NAME] --keyring=[KEYRING_NAME] --location=[LOCATION] "
            "--project=[KMS_PROJECT_ID] gs://[BUCKET_NAME] "
            "organizations/[ORG_ID] user@[ORGANIZATION_DOMAIN] [SA_EMAIL] [PROJECT_ID]"
        )
        result = hydrate_operator_placeholders(template, _barren_inventory())

        self.assertEqual(result.count(NOT_DETERMINED), 9)
        for token in DERIVABLE_TOKENS:
            self.assertNotIn(f"[{token}]", result)

    def test_missing_values_are_not_replaced_with_fabrications(self) -> None:
        """Fail-closed output contains no invented identifiers of any kind."""
        template = "--project=[KMS_PROJECT_ID] [SA_EMAIL] user@[ORGANIZATION_DOMAIN]"
        result = hydrate_operator_placeholders(template, _barren_inventory())

        for invention in (
            ".iam.gserviceaccount.com",
            "workload",
            "departmentofexample",
            ".gov",
            ".mil",
            "example.com",
        ):
            self.assertNotIn(invention, result, f"fabricated fragment {invention!r} leaked")

    def test_organization_display_name_is_never_mangled_into_a_domain(self) -> None:
        """A display name such as "Department of Example" yields no domain."""
        self.assertIsNone(resolve_organization_domain(_barren_inventory()))

        context = build_operator_context(_barren_inventory())
        block = render_discovered_context_block(context, tokens=["ORGANIZATION_DOMAIN"])
        self.assertIn(NOT_DETERMINED, block)
        self.assertIn("organization.domain_name", block)

    def test_service_account_email_not_synthesised_without_a_project(self) -> None:
        """A service account with no project yields no email, only guidance."""
        inventory = _barren_inventory()
        inventory["infrastructure_components"]["service_accounts"] = [
            {"account_id": "sa-pipeline", "display_name": "Pipeline"}
        ]

        self.assertEqual(collect_service_account_emails(inventory), [])

        context = build_operator_context(inventory)
        self.assertIsNone(context.values["SA_EMAIL"])
        block = render_discovered_context_block(context, tokens=["SA_EMAIL"])
        self.assertIn("`sa-pipeline`", block)
        self.assertNotIn("sa-pipeline@", block)

    def test_extractor_placeholder_project_email_is_discarded(self) -> None:
        """An email in the historical placeholder project "workload" is rejected."""
        inventory = _barren_inventory()
        inventory["infrastructure_components"]["service_accounts"] = [
            {
                "account_id": "sa-pipeline",
                "email": "sa-pipeline@workload.iam.gserviceaccount.com",
            }
        ]
        self.assertEqual(collect_service_account_emails(inventory), [])

    def test_runtime_tokens_become_operator_fill_in_markers(self) -> None:
        """RUNTIME tokens are never guessed and are unmistakably marked."""
        template = (
            "src_ip=[SOURCE_IP] pod=[POD_NAME] ns=[NAMESPACE] node=[NODE_NAME] "
            "vm=[INSTANCE_NAME] zone=[ZONE] disk=[DISK_NAME] id=[INSTANCE_ID] "
            "ts=[TIMESTAMP] v=[VERSION] nv=[NEW_VERSION] p=[NEW_KEY_RESOURCE_PATH] "
            "k=[KEY_ID] who=[COMPROMISED_IDENTITY_EMAIL]"
        )
        result = hydrate_operator_placeholders(template, _rich_inventory())

        for token in RUNTIME_TOKENS:
            self.assertIn(f"<{token}: fill in", result, f"{token} lacks a fill-in marker")
            self.assertNotIn(f"[{token}]", result)

        # Nothing that could be mistaken for a real attacker IP was invented.
        self.assertIsNone(re.search(r"\b\d{1,3}(?:\.\d{1,3}){3}\b", result))

    def test_runtime_tokens_are_not_hydrated_even_when_inventory_is_rich(self) -> None:
        """A discovered VM name must not be substituted for the compromised one."""
        inventory = _rich_inventory()
        inventory["infrastructure_components"]["compute_instances"] = [
            {"name": "prod-bastion-vm-0", "zone": "us-east4-a"}
        ]
        result = hydrate_operator_placeholders(
            "gcloud compute instances delete [INSTANCE_NAME] --zone=[ZONE]", inventory
        )
        self.assertNotIn("prod-bastion-vm-0", result)
        self.assertNotIn("us-east4-a", result)
        self.assertIn("<INSTANCE_NAME: fill in", result)

    def test_citation_shorthand_is_left_untouched(self) -> None:
        """Bracketed NIST citations and blank-template scaffolding survive intact."""
        template = (
            "in accordance with the [EVIDACT] and [OMB M-19-23]; a [PRIVACT] system; "
            "continuity of operations [COOP] plan; Runbook ID IR-[XYZ]-00[X]; "
            "www.[agency].gov/privacy"
        )
        self.assertEqual(hydrate_operator_placeholders(template, _rich_inventory()), template)

    def test_project_id_and_service_account_stay_in_the_same_project(self) -> None:
        """A combined disable command must not name a foreign project."""
        template = "gcloud iam service-accounts disable [SA_EMAIL] --project=[PROJECT_ID]"
        tokens, _ = find_operator_tokens(template)
        context = build_operator_context(_rich_inventory(), tokens=tokens)
        result = hydrate_operator_placeholders(template, _rich_inventory(), context=context)

        self.assertIn("sa-alpha-workload@prj-workload.iam.gserviceaccount.com", result)
        self.assertIn("--project=prj-workload", result)

    def test_explicit_project_id_wins_over_inferred(self) -> None:
        """An operator-configured project ID overrides any inferred candidate."""
        inventory = _rich_inventory()
        inventory["system_information"]["project_id"] = "prj-configured"
        context = build_operator_context(inventory, tokens=["PROJECT_ID", "SA_EMAIL"])
        self.assertEqual(context.values["PROJECT_ID"], "prj-configured")

    def test_hydration_rejects_non_string_content(self) -> None:
        """Passing a non-string surfaces a TypeError rather than corrupting output."""
        with self.assertRaises(TypeError):
            hydrate_operator_placeholders(None, _rich_inventory())  # type: ignore[arg-type]


class TestRunbookHydrationEndToEnd(unittest.TestCase):
    """Full-pipeline tests over the bytes actually written to the ATO package."""

    def setUp(self) -> None:
        """Creates an isolated target directory holding a system inventory."""
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        # generate_ato_artifacts installs a process-wide audit sink inside the
        # target directory; drop it before the directory is removed.
        self.addCleanup(reset_audit_log)
        self.target_dir = self._tmp.name

    def _generate(self, inventory: Dict[str, Any]) -> str:
        """Runs the real generator and returns the KMS runbook Markdown.

        Args:
            inventory: System inventory to write into the target directory.

        Returns:
            The generated IR_KMS_CMEK_Compromise_Runbook.md contents.
        """
        inv_path = os.path.join(self.target_dir, "system_inventory.json")
        with open(inv_path, "w", encoding="utf-8") as handle:
            json.dump(inventory, handle)

        generate_compliance_artifacts.generate_ato_artifacts(
            self.target_dir, policy_format="markdown", data_format="yaml", oscal_format="none"
        )
        rb_path = os.path.join(
            self.target_dir,
            "ato_artifacts",
            "Incident_Response_Runbooks",
            "IR_KMS_CMEK_Compromise_Runbook.md",
        )
        self.assertTrue(os.path.exists(rb_path), "KMS runbook was not generated")
        with open(rb_path, "r", encoding="utf-8") as handle:
            return handle.read()

    def test_generated_runbook_has_no_unhydrated_command_placeholders(self) -> None:
        """The delivered runbook contains real values inside its gcloud commands."""
        content = self._generate(_rich_inventory())

        self.assertIn("--key=key-alpha-disk-cmek", content)
        self.assertIn("--keyring=kr-htp", content)
        self.assertIn("--location=us-east4", content)
        self.assertIn("--project=prj-security", content)
        self.assertIn("gs://bkt-alpha-artifacts/**", content)
        self.assertIn("organizations/123456789012/logs", content)

        # No allow-listed operator token survives outside the provenance table,
        # whose rows intentionally quote the token name in backticks.
        command_lines = [
            line for line in content.splitlines() if not line.lstrip().startswith("| `[")
        ]
        for token in list(DERIVABLE_TOKENS) + list(RUNTIME_TOKENS):
            for line in command_lines:
                self.assertNotIn(f"[{token}]", line, f"un-hydrated [{token}] in: {line!r}")

    def test_generated_runbook_documents_provenance_and_alternatives(self) -> None:
        """The runbook states its values are examples and names the alternatives."""
        content = self._generate(_rich_inventory())

        self.assertIn("## Discovered Environment Context", content)
        self.assertIn("examples drawn from the discovered inventory", content)
        self.assertIn("`key-zeta-bucket-cmek`", content)
        self.assertIn("`bkt-zeta-audit-logs`", content)

    def test_generated_runbook_fails_closed_without_fabricating(self) -> None:
        """With a barren inventory the runbook says so instead of inventing values."""
        content = self._generate(_barren_inventory())

        self.assertIn(NOT_DETERMINED, content)
        self.assertIn("--key=" + NOT_DETERMINED, content)
        self.assertNotIn("[KEY_NAME]", content.replace("| `[KEY_NAME]`", ""))
        # No invented KMS resource path or service account principal.
        self.assertNotIn(".iam.gserviceaccount.com", content)
        self.assertNotIn("keyRings/kr-", content)


if __name__ == "__main__":
    unittest.main()
