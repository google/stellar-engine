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

import unittest
import state_iam


class TestStateIam(unittest.TestCase):

  def setUp(self):
    state_iam.ORG_IDS.clear()

  def test_org_id_mapping(self):
    org1 = state_iam._org_id("123456789")
    self.assertEqual(org1, "[organization #0]")
    org2 = state_iam._org_id("987654321")
    self.assertEqual(org2, "[organization #1]")
    # Cached lookup returns same alias
    self.assertEqual(state_iam._org_id("123456789"), "[organization #0]")

  def test_get_bindings_empty(self):
    bindings = list(state_iam.get_bindings([]))
    self.assertEqual(bindings, [])

  def test_get_bindings_project_iam(self):
    resources = [
        {
            "type": "google_project_iam_binding",
            "instances": [
                {
                    "attributes": {
                        "project": "my-test-proj",
                        "role": "roles/viewer",
                        "members": ["group:viewers@example.com"],
                        "condition": []
                    }
                }
            ]
        }
    ]
    bindings = list(state_iam.get_bindings(resources))
    self.assertEqual(len(bindings), 1)
    b = bindings[0]
    self.assertTrue(b.authoritative)
    self.assertEqual(b.resource_type, "project")
    self.assertEqual(b.resource_id, "my-test-proj")
    self.assertEqual(b.role, "roles/viewer")
    self.assertEqual(b.member_type, "group")
    self.assertEqual(b.member_id, "viewers")

  def test_get_bindings_with_prefix(self):
    resources = [
        {
            "type": "google_project_iam_member",
            "instances": [
                {
                    "attributes": {
                        "project": "prefix-proj-1",
                        "role": "roles/editor",
                        "member": "serviceAccount:sa1@prefix-proj-1.iam.gserviceaccount.com",
                        "condition": []
                    }
                }
            ]
        }
    ]
    bindings = list(state_iam.get_bindings(resources, prefix="prefix"))
    self.assertEqual(len(bindings), 1)
    b = bindings[0]
    self.assertFalse(b.authoritative)
    self.assertEqual(b.resource_id, "proj-1")


if __name__ == '__main__':
  unittest.main()
