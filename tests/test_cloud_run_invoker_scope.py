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

"""Checks that the Cloud Run blueprint scopes its invoker grant."""

import pathlib
import re
import unittest

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
_MAIN_TF = _REPO_ROOT / "blueprints/fedramp-high/cloud-run/main.tf"
_MODULE_OUTPUTS_TF = _REPO_ROOT / "modules/cloud-run-v2/outputs.tf"
_SERVICE_ACCOUNT = "google_service_account.cloud_run_service_account"


def _top_block(text, header):
    """Returns the top-level HCL block that starts with header."""
    match = re.search(re.escape(header) + r"\s*\{[\s\S]*?\n\}", text)
    if match is None:
        raise AssertionError(f"Block not found: {header}")
    return match.group(0)


class TestCloudRunInvokerScope(unittest.TestCase):
    def setUp(self):
        self.main_tf = _MAIN_TF.read_text(encoding="utf-8")

    def _assert_scoped_invoker(self, resource_type, count):
        resource = _top_block(
            self.main_tf, f'resource "{resource_type}" "cloud_run_invoker"'
        )
        self.assertRegex(resource, r"\n\s*count\s*=\s*" + re.escape(count))
        self.assertRegex(resource, r"\n\s*project\s*=\s*var\.main_project_id\n")
        self.assertRegex(resource, r"\n\s*location\s*=\s*var\.region\n")
        # The name comes from the module, so the grant waits for the
        # resource and follows it when the name changes.
        self.assertRegex(
            resource,
            r"\n\s*name\s*=\s*module\.cloud-run\.resource_name\n",
        )
        self.assertRegex(resource, r'\n\s*role\s*=\s*"roles/run\.invoker"\n')
        self.assertRegex(
            resource,
            r"\n\s*member\s*=\s*" + re.escape(_SERVICE_ACCOUNT) + r"\.member\n",
        )

    def test_service_mode_grants_invoker_on_the_service(self):
        self._assert_scoped_invoker(
            "google_cloud_run_v2_service_iam_member", "var.is_job ? 0 : 1\n"
        )

    def test_job_mode_grants_invoker_on_the_job(self):
        self._assert_scoped_invoker(
            "google_cloud_run_v2_job_iam_member", "var.is_job ? 1 : 0\n"
        )

    def test_no_project_level_grant_remains(self):
        # A project-level invoker grant covers every Cloud Run service
        # and job in the project.
        self.assertNotIn("google_project_iam_", self.main_tf)

    def test_grants_are_never_authoritative(self):
        # Authoritative resources would remove invoker grants that other
        # configurations manage on the same service or job.
        self.assertNotRegex(
            self.main_tf, r"google_cloud_run_v2_\w+_iam_(binding|policy)"
        )
        module = _top_block(self.main_tf, 'module "cloud-run"')
        self.assertNotRegex(module, r"\n\s*iam\s*=")

    def test_module_exposes_the_resource_name(self):
        outputs_tf = _MODULE_OUTPUTS_TF.read_text(encoding="utf-8")
        _top_block(outputs_tf, 'output "resource_name"')


if __name__ == "__main__":
    unittest.main()
