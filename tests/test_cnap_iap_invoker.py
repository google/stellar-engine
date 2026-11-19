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

"""Checks that the cnap blueprint scopes the IAP invoker role to services."""

import pathlib
import re
import unittest

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
_BLUEPRINT_DIR = _REPO_ROOT / "blueprints/fedramp-high/cnap"
_INVOKER_HEADER = (
    'resource "google_cloud_run_v2_service_iam_member" '
    '"iap_sa_cloudrun_invoker"'
)
_RESOURCE_RE = re.compile(
    r'^resource\s+"(?P<type>[^"]+)"\s+"(?P<label>[^"]+)"\s*\{[\s\S]*?^\}',
    re.MULTILINE,
)


def _resources(text):
    """Returns (type, label, body) for every top-level resource block."""
    return [
        (match.group("type"), match.group("label"), match.group(0))
        for match in _RESOURCE_RE.finditer(text)
    ]


class TestCnapIapInvoker(unittest.TestCase):
    def setUp(self):
        self.resources = []
        for path in sorted(_BLUEPRINT_DIR.glob("*.tf")):
            self.resources += _resources(path.read_text(encoding="utf-8"))
        self.invokers = [
            body
            for _, _, body in self.resources
            if body.startswith(_INVOKER_HEADER)
        ]

    def test_no_project_level_invoker_grant_remains(self):
        # A project-level grant lets the IAP service agent invoke every
        # Cloud Run service in the project, not only the ones behind IAP.
        for resource_type, label, body in self.resources:
            if resource_type.startswith("google_project_iam_"):
                self.assertNotIn(
                    "roles/run.invoker", body, f"{resource_type}.{label}"
                )

    def test_invoker_grant_targets_each_cloud_run_service(self):
        self.assertEqual(len(self.invokers), 1)
        invoker = self.invokers[0]
        self.assertRegex(
            invoker,
            r"\n\s*for_each\s*=\s*"
            r"google_cloud_run_v2_service\.cloud_run_apps\n",
        )
        # The provider defaults to the network project, so the binding
        # names the project, location and name of the service it covers.
        for argument in ("project", "location", "name"):
            self.assertRegex(
                invoker,
                rf"\n\s*{argument}\s*=\s*each\.value\.{argument}\n",
            )

    def test_invoker_grant_is_additive_for_the_iap_service_agent(self):
        invoker = self.invokers[0]
        self.assertRegex(invoker, r'\n\s*role\s*=\s*"roles/run\.invoker"\n')
        self.assertRegex(
            invoker,
            r"\n\s*member\s*=\s*"
            r"google_project_service_identity\.iap_sa\.member\n",
        )

    def test_grant_covers_every_cloud_run_service_in_the_blueprint(self):
        # The grant iterates one resource, so a second Cloud Run resource
        # behind IAP would be left without the invoker role.
        services = [
            (label, body)
            for resource_type, label, body in self.resources
            if resource_type == "google_cloud_run_v2_service"
        ]
        self.assertEqual([label for label, _ in services], ["cloud_run_apps"])
        # The service keys come from data/cloudrun.yaml, which keeps the
        # binding addresses stable when applications are added or removed.
        self.assertRegex(
            services[0][1], r"\n\s*for_each\s*=\s*local\.cloud_runs\n"
        )


if __name__ == "__main__":
    unittest.main()
