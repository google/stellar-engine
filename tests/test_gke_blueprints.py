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

"""Checks node privacy, identifier, and Config Sync inputs of GKE blueprints."""

import pathlib
import re
import unittest

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
_GKE_DIR = _REPO_ROOT / "blueprints/il5/gke"
_GKE_HARDENED_DIR = _REPO_ROOT / "blueprints/il5/gke-hardened"

# The secret types the gke-hardened blueprint accepts for a Git repository.
# Config Sync also defines gcenode, which needs Workload Identity disabled,
# and the blueprint cluster always enables Workload Identity.
_GIT_SECRET_TYPES = {
    "cookiefile",
    "gcpserviceaccount",
    "githubapp",
    "none",
    "ssh",
    "token",
}


def _read(directory, name):
    return (directory / name).read_text(encoding="utf-8")


def _top_block(text, header):
    """Returns the top-level HCL block that starts with header."""
    match = re.search(re.escape(header) + r"\s*\{[\s\S]*?\n\}", text)
    if match is None:
        raise AssertionError(f"Block not found: {header}")
    return match.group(0)


def _account_id(block):
    """Returns the account_id expression of a block without whitespace."""
    match = re.search(r"\n\s*account_id\s*=\s*([\s\S]*?\)\n|[^\n]*\n)", block)
    if match is None:
        raise AssertionError("account_id not found")
    return re.sub(r"\s+", "", match.group(1))


class TestGkeBlueprints(unittest.TestCase):
    def test_nodes_are_always_private(self):
        # Node privacy must not follow the control plane endpoint toggle.
        for directory in (_GKE_DIR, _GKE_HARDENED_DIR):
            with self.subTest(blueprint=directory.name):
                cluster = _top_block(
                    _read(directory, "main.tf"), 'module "cluster"'
                )
                self.assertEqual(
                    re.findall(r"private_nodes\s*=\s*(\S+)", cluster),
                    ["true"],
                )

    def test_service_account_ids_fit_the_length_limit(self):
        # Account IDs allow at most 30 characters and no trailing hyphen,
        # so the blueprints cut the ID and strip every trailing hyphen.
        cases = (
            (
                _GKE_DIR,
                'resource "google_service_account" "gke_cluster_sa"',
                '"gke-sa-${var.gke_cluster_name}"',
            ),
            (
                _GKE_HARDENED_DIR,
                'resource "google_service_account" "gke"',
                '"gke-${var.main_project_id}"',
            ),
        )
        for directory, header, name in cases:
            with self.subTest(blueprint=directory.name):
                block = _top_block(_read(directory, "main.tf"), header)
                self.assertEqual(
                    _account_id(block),
                    f'replace(substr({name},0,30),"/-+$/","")',
                )

    def test_config_sync_secret_type_is_a_validated_variable(self):
        main_tf = _read(_GKE_HARDENED_DIR, "main.tf")
        self.assertEqual(
            re.findall(r"secret_type\s*=\s*(\S+)", main_tf),
            ["var.config_sync_secret_type"],
        )
        variable = _top_block(
            _read(_GKE_HARDENED_DIR, "variables.tf"),
            'variable "config_sync_secret_type"',
        )
        # The default keeps the behavior of unauthenticated repositories.
        self.assertRegex(variable, r'\n\s*default\s*=\s*"none"\n')
        condition = re.search(
            r"condition\s*=\s*contains\(\s*\[([^\]]*)\]", variable
        )
        self.assertIsNotNone(condition)
        self.assertEqual(
            set(re.findall(r'"([^"]+)"', condition.group(1))),
            _GIT_SECRET_TYPES,
        )
        # The error message names the same values as the condition.
        message = re.search(r'error_message\s*=\s*"([^"]*)"', variable)
        self.assertIsNotNone(message)
        self.assertEqual(
            set(re.findall(r"[a-z]{3,}", message.group(1).split(" of ")[1]))
            - {"and", "or"},
            _GIT_SECRET_TYPES,
        )
        # The description tells operators which values need the Secret.
        self.assertIn("git-creds", variable)

    def test_cluster_keeps_workload_identity_enabled(self):
        # Leaving gcenode out of the accepted secret types relies on the
        # cluster module default, which enables Workload Identity.
        cluster = _top_block(
            _read(_GKE_HARDENED_DIR, "main.tf"), 'module "cluster"'
        )
        self.assertNotIn("workload_identity", cluster)
        module_variables = _read(
            _REPO_ROOT / "modules/gke-cluster-standard-se", "variables.tf"
        )
        self.assertRegex(
            module_variables,
            r"workload_identity\s*=\s*optional\(bool, true\)",
        )

    def test_config_sync_service_account_email_is_validated(self):
        git = re.search(
            r"\n\s*git\s*\{([^}]*)\}", _read(_GKE_HARDENED_DIR, "main.tf")
        )
        self.assertIsNotNone(git)
        self.assertEqual(
            re.findall(r"gcp_service_account_email\s*=\s*(\S+)", git.group(1)),
            ["var.config_sync_service_account_email"],
        )
        variable = _top_block(
            _read(_GKE_HARDENED_DIR, "variables.tf"),
            'variable "config_sync_service_account_email"',
        )
        # The null default leaves the planned git block unchanged.
        self.assertRegex(variable, r"\n\s*default\s*=\s*null\n")
        # The description states the binding the operator must grant.
        self.assertIn("roles/iam.workloadIdentityUser", variable)
        self.assertIn(
            "svc.id.goog[config-management-system/root-reconciler]", variable
        )
        compact = re.sub(r"\s+", "", variable)
        # The email is set when and only when the secret type needs it.
        self.assertIn(
            '(var.config_sync_secret_type=="gcpserviceaccount")=='
            "(var.config_sync_service_account_email!=null)",
            compact,
        )
        pattern = re.search(r'regex\(\s*"([^"]+)"', variable)
        self.assertIsNotNone(pattern)
        # HCL escapes each backslash of the regular expression.
        email = re.compile(pattern.group(1).replace("\\\\", "\\"))
        accepted = (
            "config-sync@my-project.iam.gserviceaccount.com",
            "config-sync@my-project.example.com.iam.gserviceaccount.com",
        )
        rejected = (
            "",
            "config-sync",
            "serviceAccount:config-sync@my-project.iam.gserviceaccount.com",
            "123456789012-compute@developer.gserviceaccount.com",
            "config-sync@my-project.iam.gserviceaccount.com.example.com",
            "Config-Sync@my-project.iam.gserviceaccount.com",
            "sync@my-project.iam.gserviceaccount.com",
        )
        for value in accepted:
            with self.subTest(accepted=value):
                self.assertIsNotNone(email.search(value))
        for value in rejected:
            with self.subTest(rejected=value):
                self.assertIsNone(email.search(value))


if __name__ == "__main__":
    unittest.main()
