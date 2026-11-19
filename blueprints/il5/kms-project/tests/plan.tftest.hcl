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

mock_provider "google" {}

override_data {
  target = data.google_kms_key_ring.existing_keyring
  values = {
    id = "projects/test-core-project/locations/us-east4/keyRings/test-kr"
  }
}

override_data {
  target = data.google_kms_crypto_key.existing_keys["test-key"]
  values = {
    id = "projects/test-core-project/locations/us-east4/keyRings/test-kr/cryptoKeys/test-key"
  }
}

variables {
  main_project_id           = "test-core-project"
  core_project_id           = "test-core-project"
  gcp_region                = "us-east4"
  existing_kms_keyring_name = "test-kr"
  email                     = "alice@example.com"
  group_email               = "kms-admins@example.com"
  existing_kms_keys = {
    "test-key" = {
      iam_members = {
        "roles/cloudkms.cryptoKeyViewer" = [
          "user:bob@example.com",
          "user:bob@example.com",
          "",
        ]
      }
    }
  }
}

run "plan_additive_iam_members" {
  command = plan

  assert {
    condition     = length(google_kms_crypto_key_iam_member.existing_keys) == 1
    error_message = "Expected duplicate and empty members to be deduplicated."
  }

  assert {
    condition     = google_kms_crypto_key_iam_member.default_encrypter_decrypter["test-key"].member == "user:alice@example.com"
    error_message = "Expected default user encrypter/decrypter binding."
  }

  assert {
    condition     = google_kms_crypto_key_iam_member.default_group_encrypter_decrypter["test-key"].member == "group:kms-admins@example.com"
    error_message = "Expected default group encrypter/decrypter binding."
  }
}

run "plan_without_default_emails" {
  command = plan

  variables {
    email       = null
    group_email = null
  }

  assert {
    condition     = length(google_kms_crypto_key_iam_member.default_encrypter_decrypter) == 0
    error_message = "Expected no default user binding when email is null."
  }

  assert {
    condition     = length(google_kms_crypto_key_iam_member.default_group_encrypter_decrypter) == 0
    error_message = "Expected no default group binding when group_email is null."
  }
}
