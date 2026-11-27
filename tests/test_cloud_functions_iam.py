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

"""Checks the IAM scope of the Cloud Functions blueprint runner account."""

import pathlib
import re
import unittest

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
_BLUEPRINT_DIR = _REPO_ROOT / "blueprints/fedramp-high/cloud-functions"
_RUNNER = r"module\.service-account-runner\.iam_email"
# Roles that no resource below the project accepts.
_PROJECT_LEVEL_ROLES = {
    "roles/cloudbuild.builds.builder",
    "roles/logging.logWriter",
}


def _top_block(text, header):
    """Returns the top-level HCL block that starts with header."""
    match = re.search(re.escape(header) + r"\s*\{[\s\S]*?\n\}", text)
    if match is None:
        raise AssertionError(f"Block not found: {header}")
    return match.group(0)


def _leading_comment(text, header):
    """Returns the comment lines directly above the block header."""
    match = re.search(r"((?:^#.*\n)+)" + re.escape(header), text, re.MULTILINE)
    return "" if match is None else match.group(1)


class TestCloudFunctionsIam(unittest.TestCase):
    def setUp(self):
        self.main_tf = (_BLUEPRINT_DIR / "main.tf").read_text(encoding="utf-8")

    def test_project_grants_are_limited_to_project_only_roles(self):
        blocks = re.findall(
            r'resource "google_project_iam_member" "\w+"\s*\{[\s\S]*?\n\}',
            self.main_tf,
        )
        roles = set()
        for block in blocks:
            roles.update(re.findall(r'\n\s*role\s*=\s*"([^"]+)"', block))
        self.assertEqual(roles, _PROJECT_LEVEL_ROLES)

    def test_project_grants_state_why_they_stay_at_project_level(self):
        for label in ("cloud_build", "logging_log_writer"):
            header = f'resource "google_project_iam_member" "{label}"'
            self.assertIn(
                "narrowest resource",
                _leading_comment(self.main_tf, header),
                msg=label,
            )

    def test_project_iam_stays_additive(self):
        self.assertNotIn("google_project_iam_binding", self.main_tf)
        self.assertNotIn("google_project_iam_policy", self.main_tf)

    def test_scoped_roles_have_no_project_level_grant(self):
        for role in (
            "roles/run.invoker",
            "roles/storage.objectUser",
            "roles/artifactregistry.createOnPushWriter",
        ):
            for block in re.findall(
                r'resource "google_project_iam_\w+" "\w+"\s*\{[\s\S]*?\n\}',
                self.main_tf,
            ):
                self.assertNotIn(f'"{role}"', block)

    def test_invoker_is_bound_to_the_function_service(self):
        grant = _top_block(
            self.main_tf,
            'resource "google_cloud_run_v2_service_iam_member" "cloud_invoker"',
        )
        self.assertRegex(grant, r"\n\s*project\s*=\s*var\.main_project_id\n")
        self.assertRegex(grant, r"\n\s*location\s*=\s*var\.region\n")
        self.assertRegex(
            grant, r"\n\s*name\s*=\s*local\.function_service_name\n"
        )
        self.assertRegex(grant, r'\n\s*role\s*=\s*"roles/run\.invoker"\n')
        self.assertRegex(grant, r"\n\s*member\s*=\s*" + _RUNNER + r"\n")

    def test_invoker_grant_waits_for_the_function_deployment(self):
        # The function module creates the Cloud Run service, so a grant
        # issued before it fails with a not found error.
        grant = _top_block(
            self.main_tf,
            'resource "google_cloud_run_v2_service_iam_member" "cloud_invoker"',
        )
        self.assertRegex(
            grant,
            r"depends_on\s*=\s*\[module\.cloud-function\]",
        )

    def test_service_name_follows_the_cloud_run_naming_rules(self):
        # Cloud Run service names accept neither capitals nor underscores,
        # while function names accept both.
        locals_block = _top_block(self.main_tf, "locals")
        self.assertRegex(
            locals_block,
            r"function_service_name\s*=\s*"
            r'lower\(replace\(var\.function_name, "_", "-"\)\)\n',
        )

    def test_registry_grant_is_additive_and_scoped_to_the_repository(self):
        module = _top_block(self.main_tf, 'module "registry-docker"')
        additive = re.search(
            r"\n {2}iam_bindings_additive = \{([\s\S]*?)\n {2}\}", module
        )
        self.assertIsNotNone(additive)
        self.assertRegex(additive.group(1), r"member\s*=\s*" + _RUNNER + r"\n")
        self.assertRegex(
            additive.group(1), r'role\s*=\s*"roles/artifactregistry\.writer"\n'
        )
        self.assertNotIn("createOnPushWriter", additive.group(1))

    def test_bucket_grant_covers_the_runner(self):
        module = _top_block(self.main_tf, 'module "bucket"')
        grant = re.search(
            r'"roles/storage\.objectUser" = \[([\s\S]*?)\]', module
        )
        self.assertIsNotNone(grant)
        self.assertRegex(grant.group(1), _RUNNER)

    def test_outputs_do_not_reference_removed_grants(self):
        outputs_tf = (_BLUEPRINT_DIR / "outputs.tf").read_text(encoding="utf-8")
        for label in (
            "artifactregistry_create_on_push_writer",
            "cloud_invoker",
            "storage_object_user",
        ):
            self.assertNotIn(f"google_project_iam_member.{label}", outputs_tf)
        for name, role in (
            ("artifact_registry_iam_member", "roles/artifactregistry.writer"),
            ("storage_object_admin_iam_member", "roles/storage.objectUser"),
        ):
            output = _top_block(outputs_tf, f'output "{name}"')
            self.assertIn(role, output)
            self.assertRegex(output, r"\n\s*value\s*=\s*" + _RUNNER + r"\n")


if __name__ == "__main__":
    unittest.main()
