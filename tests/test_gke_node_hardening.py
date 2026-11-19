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

"""Checks the GKE node hardening that blueprints rely on."""

import pathlib
import re
import unittest

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
_GKE_HARDENED_DIR = _REPO_ROOT / "blueprints/il5/gke-hardened"
_NODEPOOL_DIR = _REPO_ROOT / "modules/gke-nodepool"
_GITLAB_DIR = _REPO_ROOT / "blueprints/fedramp-high/gitlab"


def _block(text, header):
    """Returns the HCL block that starts with header."""
    match = re.search(re.escape(header) + r"\s*\{[\s\S]*?\n\s*\}", text)
    if match is None:
        raise AssertionError(f"Block not found: {header}")
    return match.group(0)


def _top_block(text, header):
    """Returns the top-level HCL block that starts with header."""
    match = re.search(re.escape(header) + r"\s*\{[\s\S]*?\n\}", text)
    if match is None:
        raise AssertionError(f"Block not found: {header}")
    return match.group(0)


class TestGkeNodeHardening(unittest.TestCase):
    def test_gke_hardened_removes_the_default_pool(self):
        # The default pool runs without the hardened settings of the
        # cluster node pool, so the blueprint removes it by default.
        main_tf = (_GKE_HARDENED_DIR / "main.tf").read_text(encoding="utf-8")
        default_pool = _block(main_tf, "default_nodepool =")
        self.assertRegex(
            default_pool, r"remove_pool\s*=\s*var\.remove_default_node_pool"
        )
        self.assertNotIn("remove_default_node_pool =", default_pool)
        variables_tf = (_GKE_HARDENED_DIR / "variables.tf").read_text(
            encoding="utf-8"
        )
        variable = _block(variables_tf, 'variable "remove_default_node_pool"')
        self.assertRegex(variable, r"\n\s*default\s*=\s*true\n")

    def test_nodepool_always_disables_legacy_endpoints(self):
        main_tf = (_NODEPOOL_DIR / "main.tf").read_text(encoding="utf-8")
        self.assertRegex(
            main_tf,
            r"node_metadata\s*=\s*merge\(\s*"
            r"coalesce\(var\.node_config\.metadata, \{\}\),\s*"
            r'\{ disable-legacy-endpoints = "true" \}',
        )

    def test_gitlab_confidential_pool_meets_gke_limits(self):
        main_tf = (_GITLAB_DIR / "main.tf").read_text(encoding="utf-8")
        pool = _top_block(main_tf, 'module "gke-node-pool"')
        self.assertRegex(pool, r"confidential_nodes\s*=\s*true")
        # The GKE API rejects Confidential GKE Nodes on a boot disk of
        # 15 GB or less.
        disk = re.search(r"disk_size_gb\s*=\s*(\d+)", pool)
        self.assertIsNotNone(disk)
        self.assertGreater(int(disk.group(1)), 15)
        self.assertRegex(pool, r'block-project-ssh-keys\s*=\s*"true"')

    def test_gitlab_nodes_run_as_a_dedicated_account(self):
        main_tf = (_GITLAB_DIR / "main.tf").read_text(encoding="utf-8")
        account = _top_block(main_tf, 'module "gke-node-sa"')
        self.assertIn("modules/iam-service-account", account)
        self.assertRegex(account, r"project_id\s*=\s*var\.project_id")
        # Service account IDs allow at most 30 characters, so the name
        # keeps 24 characters of the cluster name before the suffix.
        name = re.search(
            r'name\s*=\s*"\$\{substr\(var\.gke_name, 0, (\d+)\)\}([a-z-]+)"',
            account,
        )
        self.assertIsNotNone(name)
        self.assertLessEqual(int(name.group(1)) + len(name.group(2)), 30)
        self.assertRegex(account, r"\(var\.project_id\)\s*=\s*\[")
        self.assertEqual(
            sorted(re.findall(r'"(roles/[^"]+)"', account)),
            [
                "roles/artifactregistry.reader",
                "roles/autoscaling.metricsWriter",
                "roles/logging.logWriter",
                "roles/monitoring.metricWriter",
                "roles/monitoring.viewer",
            ],
        )
        # Both the node pool and the short-lived default pool of the
        # cluster use the node account instead of the GitLab VM account.
        for header in ('module "gke-node-pool"', 'module "cluster"'):
            block = _top_block(main_tf, header)
            self.assertRegex(
                block, r"=\s*module\.gke-node-sa\.email", msg=header
            )
            self.assertNotIn("gitlab_sa.email", block, msg=header)
        # Service agents hold the Shared VPC and KMS grants, so the node
        # account appears in neither set of members.
        for header in (
            'resource "google_project_iam_member" "compute_agent_subnet_user"',
            'resource "google_kms_crypto_key_iam_member" '
            '"compute_service_agent_kms_permissions"',
        ):
            self.assertNotIn(
                "gke-node-sa", _top_block(main_tf, header), msg=header
            )


if __name__ == "__main__":
    unittest.main()
