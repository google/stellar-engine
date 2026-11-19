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

"""Checks that the kms-project blueprint applies iam_members on its keys."""

import pathlib
import re
import unittest

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
_BLUEPRINT_DIR = _REPO_ROOT / "blueprints/il5/kms-project"


def _block(text, header):
    """Returns the top-level block that starts with header."""
    match = re.search(re.escape(header) + r"\s*\{[\s\S]*?\n\}", text)
    if match is None:
        raise AssertionError(f"Block not found: {header}")
    return match.group(0)


class TestKmsProjectIam(unittest.TestCase):
    def setUp(self):
        self.main_tf = (_BLUEPRINT_DIR / "main.tf").read_text(encoding="utf-8")

    def test_variable_still_declares_iam_members(self):
        variables_tf = (_BLUEPRINT_DIR / "variables.tf").read_text(
            encoding="utf-8"
        )
        variable = _block(variables_tf, 'variable "existing_kms_keys"')
        self.assertRegex(
            variable,
            r"iam_members\s*=\s*optional\(map\(list\(string\)\), \{\}\)",
        )

    def test_locals_flatten_every_key_role_and_member(self):
        locals_block = _block(self.main_tf, "locals")
        self.assertRegex(
            locals_block,
            r"for key_name, key in var\.existing_kms_keys :",
        )
        # A null entry, a null member list and a null member are valid
        # for the variable type, so they must yield no grant, not an error.
        self.assertIn(
            "for role, members in(key == null ? {} : key.iam_members) :",
            locals_block,
        )
        # A member listed twice under one role would produce a duplicate
        # for_each key, which fails the plan.
        self.assertIn(
            "distinct(compact(members == null ? [] : members))", locals_block
        )

    def test_for_each_key_names_the_key_role_and_member(self):
        # The state address of a grant must not depend on the position of
        # the member in its list.
        locals_block = _block(self.main_tf, "locals")
        self.assertIn(
            '"${v.key_name}/${v.role}/${v.member}" => v', locals_block
        )

    def test_members_are_granted_on_the_existing_keys(self):
        resource = _block(
            self.main_tf,
            'resource "google_kms_crypto_key_iam_member" "existing_keys"',
        )
        self.assertRegex(
            resource, r"for_each\s*=\s*local\.existing_keys_iam_members\n"
        )
        self.assertIn(
            "data.google_kms_crypto_key.existing_keys[each.value.key_name].id",
            resource,
        )
        self.assertRegex(resource, r"\n\s*role\s*=\s*each\.value\.role\n")
        self.assertRegex(resource, r"\n\s*member\s*=\s*each\.value\.member\n")

    def test_grants_are_never_authoritative(self):
        # Authoritative resources would remove grants that other
        # configurations manage on the same keys.
        self.assertNotIn("google_kms_crypto_key_iam_binding", self.main_tf)
        self.assertNotIn("google_kms_crypto_key_iam_policy", self.main_tf)


if __name__ == "__main__":
    unittest.main()
