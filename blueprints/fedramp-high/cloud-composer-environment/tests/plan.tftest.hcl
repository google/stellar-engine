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

# The mock provider returns a random string for the service agent, which the
# provider rejects as an IAM member, so the lookup gets a well-formed value.
override_data {
  target = data.google_storage_project_service_account.gcs
  values = {
    email_address = "service-123456789012@gs-project-accounts.iam.gserviceaccount.com"
    member        = "serviceAccount:service-123456789012@gs-project-accounts.iam.gserviceaccount.com"
  }
}

variables {
  main_project_id    = "test-composer-project"
  network_project_id = "test-net-host-project"
  composer_env_name  = "test-composer-env"
  network_name       = "test-spoke-0"
  subnetwork_name    = "test-subnet-us-east4"
  region             = "us-east4"
  kms_key_name       = "projects/test-kms-project/locations/us-east4/keyRings/test-kr/cryptoKeys/test-key"
}

run "plan_with_cmek" {
  command = plan

  assert {
    condition     = google_composer_environment.main.config[0].encryption_config[0].kms_key_name == var.kms_key_name
    error_message = "Expected the environment to be encrypted with var.kms_key_name."
  }

  assert {
    condition     = length(data.google_storage_project_service_account.gcs) == 1
    error_message = "Expected the Cloud Storage service agent lookup when kms_key_name is set."
  }

  assert {
    condition     = length(google_kms_crypto_key_iam_member.composer_agent_cmek) == 1
    error_message = "Expected a key grant for the Composer service agent."
  }

  assert {
    condition     = google_kms_crypto_key_iam_member.composer_agent_cmek[0].role == "roles/cloudkms.cryptoKeyEncrypterDecrypter"
    error_message = "Expected cryptoKeyEncrypterDecrypter for the Composer service agent."
  }

  assert {
    condition     = google_kms_crypto_key_iam_member.composer_agent_cmek[0].crypto_key_id == var.kms_key_name
    error_message = "Expected the Composer service agent grant on var.kms_key_name."
  }

  assert {
    condition     = length(google_kms_crypto_key_iam_member.storage_agent_cmek) == 1
    error_message = "Expected a key grant for the Cloud Storage service agent."
  }

  assert {
    condition     = google_kms_crypto_key_iam_member.storage_agent_cmek[0].role == "roles/cloudkms.cryptoKeyEncrypterDecrypter"
    error_message = "Expected cryptoKeyEncrypterDecrypter for the Cloud Storage service agent."
  }

  assert {
    condition     = google_kms_crypto_key_iam_member.storage_agent_cmek[0].crypto_key_id == var.kms_key_name
    error_message = "Expected the Cloud Storage service agent grant on var.kms_key_name."
  }

  assert {
    condition     = google_kms_crypto_key_iam_member.storage_agent_cmek[0].member == "serviceAccount:service-123456789012@gs-project-accounts.iam.gserviceaccount.com"
    error_message = "Expected the key grant to go to the Cloud Storage service agent."
  }
}

run "plan_without_cmek" {
  command = plan

  variables {
    kms_key_name = null
  }

  assert {
    condition     = length(google_composer_environment.main.config[0].encryption_config) == 0
    error_message = "Expected no encryption configuration when kms_key_name is null."
  }

  assert {
    condition     = length(data.google_storage_project_service_account.gcs) == 0
    error_message = "Expected no Cloud Storage service agent lookup when kms_key_name is null."
  }

  assert {
    condition     = length(google_kms_crypto_key_iam_member.composer_agent_cmek) == 0
    error_message = "Expected no Composer service agent key grant when kms_key_name is null."
  }

  assert {
    condition     = length(google_kms_crypto_key_iam_member.storage_agent_cmek) == 0
    error_message = "Expected no Cloud Storage service agent key grant when kms_key_name is null."
  }
}

run "rejects_invalid_kms_key" {
  command = plan

  variables {
    kms_key_name = "invalid-kms-key"
  }

  expect_failures = [var.kms_key_name]
}

run "rejects_kms_key_version" {
  command = plan

  variables {
    kms_key_name = "projects/test-kms-project/locations/us-east4/keyRings/test-kr/cryptoKeys/test-key/cryptoKeyVersions/1"
  }

  expect_failures = [var.kms_key_name]
}
