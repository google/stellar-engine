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
  main_project_id = "my-secret-project"
  gcp_region      = "us-east4"
  secrets = {
    app-secret-one = {
      location = "us-east4"
      key      = "projects/my-kms-project/locations/us-east4/keyRings/my-kr/cryptoKeys/secret-key-1"
    }
    app-secret-two = {
      location = "us-east4"
      key      = "projects/my-kms-project/locations/us-east4/keyRings/my-kr/cryptoKeys/secret-key-1"
    }
  }
}

run "plan_secrets_with_cmek" {
  command = plan

  assert {
    condition     = length(google_kms_crypto_key_iam_member.secretmanager) == 1
    error_message = "Expected distinct KMS keys to deduplicate IAM grants."
  }

  assert {
    condition     = length(time_sleep.secretmanager_agent_propagation) == 1
    error_message = "Expected 60s propagation wait before Secret Manager CMEK grants."
  }

  assert {
    condition     = google_kms_crypto_key_iam_member.secretmanager["projects/my-kms-project/locations/us-east4/keyRings/my-kr/cryptoKeys/secret-key-1"].role == "roles/cloudkms.cryptoKeyEncrypterDecrypter"
    error_message = "Expected Secret Manager service agent to receive EncrypterDecrypter role."
  }
}

run "plan_empty_secrets" {
  command = plan

  variables {
    secrets = {}
  }

  assert {
    condition     = length(google_kms_crypto_key_iam_member.secretmanager) == 0
    error_message = "Expected no KMS grants when secrets is empty."
  }

  assert {
    condition     = length(time_sleep.secretmanager_agent_propagation) == 0
    error_message = "Expected no propagation delay when secrets is empty."
  }
}
