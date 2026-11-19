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

"""Checks the Shared VPC networking of the Dataflow blueprint job."""

import pathlib
import re
import unittest

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
_DATAFLOW_DIR = _REPO_ROOT / "blueprints/il5/dataflow"


def _top_block(text, header):
    """Returns the top-level HCL block that starts with header."""
    match = re.search(re.escape(header) + r"\s*\{[\s\S]*?\n\}", text)
    if match is None:
        raise AssertionError(f"Block not found: {header}")
    return match.group(0)


class TestDataflowNetwork(unittest.TestCase):
    def test_job_derives_the_network_from_the_subnetwork(self):
        main_tf = (_DATAFLOW_DIR / "main.tf").read_text(encoding="utf-8")
        job = _top_block(main_tf, 'resource "google_dataflow_job" "job"')
        # The subnetwork lives in the Shared VPC host project, so the job
        # passes its complete URL and Dataflow derives the network from it.
        self.assertRegex(
            job,
            r"\n\s*subnetwork\s*=\s*"
            r"data\.google_compute_subnetwork\.subnetwork\.self_link\n",
        )
        # The network argument takes a name that Dataflow resolves in the
        # job project, which cannot address a Shared VPC host network.
        self.assertNotRegex(job, r"\n\s*network\s*=")

    def test_apis_and_service_agents_wait_before_iam_grants(self):
        main_tf = (_DATAFLOW_DIR / "main.tf").read_text(encoding="utf-8")
        expected_apis = {
            "compute_api": "compute.googleapis.com",
            "dataflow_api": "dataflow.googleapis.com",
            "storage_api": "storage.googleapis.com",
        }
        for res_name, service in expected_apis.items():
            api = _top_block(
                main_tf, f'resource "google_project_service" "{res_name}"'
            )
            self.assertRegex(api, rf'service\s*=\s*"{re.escape(service)}"')

        agent = _top_block(
            main_tf,
            'resource "google_project_service_identity" "dataflow_agent"',
        )
        self.assertRegex(agent, r'service\s*=\s*"dataflow\.googleapis\.com"')
        self.assertRegex(
            agent,
            r"depends_on\s*=\s*\[google_project_service\.dataflow_api\]",
        )
        # compute.googleapis.com and storage.googleapis.com are non-primary
        # service identities that return an empty member from
        # google_project_service_identity.
        self.assertNotIn(
            'resource "google_project_service_identity" "compute_agent"',
            main_tf,
        )
        self.assertNotIn(
            'resource "google_project_service_identity" "storage_agent"',
            main_tf,
        )

        gcs_sa = _top_block(
            main_tf,
            'data "google_storage_project_service_account" "gcs_sa"',
        )
        self.assertRegex(
            gcs_sa,
            r"depends_on\s*=\s*\[google_project_service\.storage_api\]",
        )

        wait = _top_block(
            main_tf, 'resource "time_sleep" "service_agent_propagation"'
        )
        self.assertRegex(wait, r'create_duration\s*=\s*"\d+[sm]"')
        for dep in (
            "google_project_service.compute_api",
            "google_project_service_identity.dataflow_agent",
            "data.google_storage_project_service_account.gcs_sa",
        ):
            self.assertIn(dep, wait)

        compute_kms = _top_block(
            main_tf,
            'resource "google_kms_crypto_key_iam_member" '
            '"compute_system_sa_kms_access"',
        )
        self.assertIn(
            "@compute-system.iam.gserviceaccount.com",
            compute_kms,
        )
        gcs_kms = _top_block(
            main_tf,
            'resource "google_kms_crypto_key_iam_member" "gcs_sa_kms_access"',
        )
        self.assertIn(
            "data.google_storage_project_service_account.gcs_sa.member",
            gcs_kms,
        )

        provider_tf = (_DATAFLOW_DIR / "provider.tf").read_text(
            encoding="utf-8"
        )
        self.assertRegex(provider_tf, r'source\s*=\s*"hashicorp/time"')

        iam_headers = (
            'resource "google_compute_subnetwork_iam_member" '
            '"dataflow_sa_compute_network_user"',
            'resource "google_kms_crypto_key_iam_member" '
            '"compute_system_sa_kms_access"',
            'resource "google_kms_crypto_key_iam_member" '
            '"dataflow_sa_kms_access"',
            'resource "google_kms_crypto_key_iam_member" "gcs_sa_kms_access"',
        )
        for header in iam_headers:
            grant = _top_block(main_tf, header)
            self.assertRegex(
                grant,
                r"depends_on\s*=\s*\[time_sleep\.service_agent_propagation\]",
                msg=header,
            )

    def test_worker_account_project_and_default_zone(self):
        main_tf = (_DATAFLOW_DIR / "main.tf").read_text(encoding="utf-8")
        worker = _top_block(
            main_tf, 'resource "google_service_account" "dataflow_worker"'
        )
        self.assertRegex(worker, r"project\s*=\s*var\.main_project_id")

        variables_tf = (_DATAFLOW_DIR / "variables.tf").read_text(
            encoding="utf-8"
        )
        zone = _top_block(variables_tf, 'variable "zone"')
        self.assertRegex(zone, r'default\s*=\s*"us-east4-a"')


if __name__ == "__main__":
    unittest.main()
