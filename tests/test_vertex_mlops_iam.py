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

"""Checks that the vertex-mlops blueprint scopes IAM bindings to resources."""

import pathlib
import re
import unittest

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
_BLUEPRINT_DIR = _REPO_ROOT / "blueprints/fedramp-high/vertex-mlops"

_MLOPS = "module.service-account-mlops.iam_email"
_NOTEBOOK = "module.service-account-notebook.iam_email"
_CLOUDBUILD = "module.project.service_agents.cloudbuild.iam_email"

# Roles that stay on the project. A new entry needs a comment in main.tf that
# states why the role cannot be bound to a resource.
_PROJECT_ROLES = {
    "roles/artifactregistry.reader",
    "roles/bigquery.jobUser",
    "roles/bigquery.user",
    "roles/cloudbuild.builds.editor",
    "roles/cloudfunctions.invoker",
    "roles/dataflow.developer",
    "roles/dataflow.worker",
    "roles/monitoring.metricWriter",
    "roles/run.invoker",
    "roles/serviceusage.serviceUsageConsumer",
}

# Roles that a narrower resource accepts, so no project binding may hold them.
_SCOPED_ROLES = (
    "roles/bigquery.dataEditor",
    "roles/compute.networkUser",
    "roles/iam.serviceAccountUser",
    "roles/storage.objectCreator",
    "roles/storage.objectViewer",
    "storage_iam",
)


def _block(text, header):
    """Returns the top-level block that starts with header."""
    match = re.search(re.escape(header) + r"\s*\{[\s\S]*?\n\}", text)
    if match is None:
        raise AssertionError(f"Block not found: {header}")
    return match.group(0)


def _argument(block, name):
    """Returns the map assigned to a first-level argument of a block."""
    match = re.search(
        r"\n  " + re.escape(name) + r"\s*=[^\n]*\{\n[\s\S]*?\n  \}", block
    )
    if match is None:
        raise AssertionError(f"Argument not found: {name}")
    return match.group(0)


def _bindings(text):
    """Returns {key: (member, role)} for a map of additive bindings."""
    return {
        key: (member, role)
        for key, member, role in re.findall(
            r"\n\s+([\w-]+)\s*=\s*\{\n\s+member\s*=\s*(\S+)\n"
            r"\s+role\s*=\s*(\S+)\n\s+\}",
            text,
        )
    }


class TestVertexMlopsIam(unittest.TestCase):
    def setUp(self):
        self.main_tf = (_BLUEPRINT_DIR / "main.tf").read_text(encoding="utf-8")
        self.vertex_tf = (_BLUEPRINT_DIR / "vertex.tf").read_text(
            encoding="utf-8"
        )
        self.project = _block(self.main_tf, 'module "project"')

    def test_network_user_is_granted_on_the_subnet(self):
        self.assertNotIn(
            'resource "google_project_iam_member" "shared_vpc"', self.main_tf
        )
        shared_vpc = _argument(self.project, "shared_vpc_service_config")
        self.assertRegex(
            shared_vpc,
            r"service_agent_subnet_iam\s*=\s*\{\s*"
            r'"\$\{var\.region\}/\$\{var\.network_config\.subnetwork_name\}"'
            r'\s*=\s*\["notebooks"\]\s*\}',
        )
        # These arguments of the project module grant the role on the whole
        # host project.
        for argument in ("network_users", "service_agent_iam"):
            self.assertNotRegex(shared_vpc, rf"\b{argument}\s*=")

    def test_workbench_instances_wait_for_the_subnet_grant(self):
        instance = _block(
            self.vertex_tf, 'resource "google_workbench_instance" "playground"'
        )
        self.assertRegex(
            instance, r"depends_on\s*=\s*\[\s*module\.project,?\s*\]"
        )

    def test_project_bindings_hold_no_scoped_role(self):
        project_bindings = (
            _argument(self.project, "iam_bindings_additive"),
            _argument(self.project, "iam"),
            _block(
                self.main_tf,
                'resource "google_project_iam_member" "service_permissions"',
            ),
        )
        for binding in project_bindings:
            for role in _SCOPED_ROLES:
                self.assertNotIn(role, binding)

    def test_project_roles_are_the_reviewed_set(self):
        iam = _argument(self.project, "iam")
        self.assertEqual(
            set(re.findall(r'\n    "(roles/[\w.]+)"\s*=', iam)), _PROJECT_ROLES
        )
        self.assertEqual(
            _bindings(_argument(self.project, "iam_bindings_additive")),
            {
                "aiplatform-user-mlops": (_MLOPS, '"roles/aiplatform.user"'),
                "aiplatform-user-notebook": (
                    _NOTEBOOK,
                    '"roles/aiplatform.user"',
                ),
            },
        )
        # The for_each keys that remain keep their state addresses.
        permissions = _block(
            self.main_tf,
            'resource "google_project_iam_member" "service_permissions"',
        )
        self.assertEqual(
            re.findall(r'\n    "([^"]+)",', permissions),
            ["roles/notebooks.runner", "roles/aiplatform.user"],
        )

    def test_every_project_role_states_why_it_stays(self):
        iam = _argument(self.project, "iam").splitlines()
        for index, line in enumerate(iam):
            if not re.match(r'\s+"roles/', line):
                continue
            # A role may share the comment of the role right above it.
            previous = iam[index - 1].strip()
            if re.match(r'"roles/[\w.]+"\s*=\s*\[.*\]$', previous):
                previous = iam[index - 2].strip()
            self.assertTrue(previous.startswith("#"), msg=line)

    def test_storage_roles_are_granted_on_the_blueprint_buckets(self):
        bindings = _bindings(
            _argument(
                _block(self.main_tf, "locals"), "bucket_iam_bindings_additive"
            )
        )
        custom_role = "google_project_iam_custom_role.storage_role.id"
        self.assertEqual(
            bindings,
            {
                "storage-creator-mlops": (
                    _MLOPS,
                    '"roles/storage.objectCreator"',
                ),
                "storage-creator-notebook": (
                    _NOTEBOOK,
                    '"roles/storage.objectCreator"',
                ),
                "storage-iam-notebook": (_NOTEBOOK, custom_role),
                "storage-viewer-mlops": (
                    _MLOPS,
                    '"roles/storage.objectViewer"',
                ),
                "storage-viewer-notebook": (
                    _NOTEBOOK,
                    '"roles/storage.objectViewer"',
                ),
            },
        )
        for header in ('module "gcs-bucket"', 'module "gcs-bucket-cloudbuild"'):
            self.assertRegex(
                _block(self.main_tf, header),
                r"\n  iam_bindings_additive\s*=\s*"
                r"local\.bucket_iam_bindings_additive\n",
                msg=header,
            )

    def test_custom_storage_role_is_valid_on_a_bucket(self):
        # Only bucket permissions can be granted through a bucket policy.
        role = _block(
            self.main_tf,
            'resource "google_project_iam_custom_role" "storage_role"',
        )
        self.assertEqual(
            re.findall(r'\n    "([^"]+)",', role),
            ["storage.buckets.getIamPolicy", "storage.buckets.setIamPolicy"],
        )

    def test_data_editor_is_granted_on_the_dataset(self):
        dataset = _block(self.main_tf, 'module "bq-dataset"')
        self.assertEqual(
            _bindings(_argument(dataset, "iam_bindings_additive")),
            {
                "data-editor-mlops": (_MLOPS, '"roles/bigquery.dataEditor"'),
                "data-editor-notebook": (
                    _NOTEBOOK,
                    '"roles/bigquery.dataEditor"',
                ),
            },
        )

    def test_service_account_user_is_granted_on_service_accounts(self):
        resource = _block(
            self.main_tf,
            'resource "google_service_account_iam_member" '
            '"service_account_user"',
        )
        mlops_id = "module.service-account-mlops.id"
        notebook_id = "module.service-account-notebook.id"
        self.assertEqual(
            {
                key: (member, service_account)
                for key, member, service_account in re.findall(
                    r"\n\s+([\w-]+)\s*=\s*\{\n\s+member\s*=\s*(\S+)\n"
                    r"\s+service_account_id\s*=\s*(\S+)\n\s+\}",
                    resource,
                )
            },
            {
                "service-account-user-cloudbuild": (_CLOUDBUILD, mlops_id),
                "service-account-user-mlops": (_MLOPS, mlops_id),
                "service-account-user-notebook": (_NOTEBOOK, notebook_id),
            },
        )
        self.assertRegex(
            resource,
            r"\n  service_account_id\s*=\s*each\.value\.service_account_id\n",
        )
        self.assertRegex(
            resource, r'\n  role\s*=\s*"roles/iam\.serviceAccountUser"\n'
        )
        self.assertRegex(resource, r"\n  member\s*=\s*each\.value\.member\n")

    def test_service_account_modules_do_not_read_their_own_outputs(self):
        # A module that reads its own outputs can produce a dependency cycle.
        modules = (
            (self.main_tf, "service-account-mlops"),
            (self.vertex_tf, "service-account-notebook"),
        )
        for text, name in modules:
            block = _block(text, f'module "{name}"')
            self.assertNotIn(f"module.{name}.", block, msg=name)
            self.assertNotIn("iam_bindings_additive", block, msg=name)

    def test_resource_grants_are_never_authoritative(self):
        # Authoritative arguments and resources would remove grants that
        # other configurations manage on the same resources.
        self.assertNotIn("google_service_account_iam_binding", self.main_tf)
        self.assertNotIn("google_service_account_iam_policy", self.main_tf)
        headers = (
            (self.main_tf, 'module "gcs-bucket"'),
            (self.main_tf, 'module "gcs-bucket-cloudbuild"'),
            (self.main_tf, 'module "bq-dataset"'),
            (self.main_tf, 'module "service-account-mlops"'),
            (self.vertex_tf, 'module "service-account-notebook"'),
        )
        for text, header in headers:
            self.assertNotRegex(
                _block(text, header),
                r"\n  (iam|iam_bindings|iam_by_principals)\s*=",
                msg=header,
            )

    def test_demo_notebook_acts_as_the_notebook_service_account(self):
        # The notebook service account can act as itself only, so the demo
        # cannot deploy with the Compute Engine default service account.
        notebook_path = _BLUEPRINT_DIR / "model_garden_pytorch_flux.ipynb"
        notebook = notebook_path.read_text(encoding="utf-8")
        self.assertNotIn("-compute@developer.gserviceaccount.com", notebook)
        self.assertIn(
            "notebook-sa@{PROJECT_ID}.iam.gserviceaccount.com", notebook
        )
        self.assertRegex(
            _block(self.vertex_tf, 'module "service-account-notebook"'),
            r'\n  name\s*=\s*"notebook-sa"\n',
        )


if __name__ == "__main__":
    unittest.main()
