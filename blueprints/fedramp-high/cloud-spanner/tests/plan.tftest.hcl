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
  main_project_id = "test-spanner-project"
  region          = "us-east4"
  instance_name   = "test-spanner-inst"
  display_name    = "Test Spanner"
  database_name   = "test-spanner-db"
  database_user   = "user:admin@example.com"
  kms_key_name    = "projects/test-kms-project/locations/us-east4/keyRings/test-kr/cryptoKeys/test-key"
}

run "plan_with_cmek" {
  command = plan

  assert {
    condition     = google_project_service.spanner_api.service == "spanner.googleapis.com"
    error_message = "Expected spanner.googleapis.com to be enabled."
  }

  assert {
    condition     = length(google_project_service_identity.spanner) == 1
    error_message = "Expected Spanner service identity when kms_key_name is set."
  }

  assert {
    condition     = length(time_sleep.spanner_agent_propagation) == 1
    error_message = "Expected propagation sleep before Spanner CMEK binding."
  }

  assert {
    condition     = google_kms_crypto_key_iam_member.spanner_cmek[0].role == "roles/cloudkms.cryptoKeyEncrypterDecrypter"
    error_message = "Expected cryptoKeyEncrypterDecrypter role for Spanner CMEK."
  }

  assert {
    condition     = google_kms_crypto_key_iam_member.spanner_cmek[0].crypto_key_id == var.kms_key_name
    error_message = "Expected CMEK IAM grant on var.kms_key_name."
  }
}

run "plan_without_cmek" {
  command = plan

  variables {
    kms_key_name = null
  }

  assert {
    condition     = length(google_project_service_identity.spanner) == 0
    error_message = "Expected no service identity when kms_key_name is null."
  }

  assert {
    condition     = length(google_kms_crypto_key_iam_member.spanner_cmek) == 0
    error_message = "Expected no CMEK IAM grant when kms_key_name is null."
  }
}

run "rejects_invalid_kms_key" {
  command = plan

  variables {
    kms_key_name = "invalid-kms-key"
  }

  expect_failures = [var.kms_key_name]
}

run "rejects_invalid_database_user" {
  command = plan

  variables {
    database_user = "admin@example.com"
  }

  expect_failures = [var.database_user]
}
