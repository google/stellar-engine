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
mock_provider "google-beta" {}
mock_provider "time" {}

variables {
  main_project_id         = "my-firestore-project"
  firestore_database_name = "(default)"
  region                  = "us-east4"
  kms_key_name            = "projects/my-kms-project/locations/us-east4/keyRings/my-kr/cryptoKeys/default"
}

run "plan_with_cmek" {
  command = plan

  assert {
    condition     = length(google_project_service_identity.firestore) == 1
    error_message = "Expected Firestore service identity to be created when kms_key_name is set."
  }

  assert {
    condition     = length(time_sleep.firestore_agent_propagation) == 1
    error_message = "Expected 60s propagation wait before Firestore KMS grant."
  }

  assert {
    condition     = length(google_kms_crypto_key_iam_member.firestore_cmek) == 1 && google_kms_crypto_key_iam_member.firestore_cmek[0].role == "roles/cloudkms.cryptoKeyEncrypterDecrypter"
    error_message = "Expected Firestore service agent to receive CMEK EncrypterDecrypter role."
  }
}

run "plan_without_cmek" {
  command = plan

  variables {
    kms_key_name = null
  }

  assert {
    condition     = length(google_project_service_identity.firestore) == 0 && length(google_kms_crypto_key_iam_member.firestore_cmek) == 0
    error_message = "Expected no service identity or KMS grant when kms_key_name is null."
  }
}
