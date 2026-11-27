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

override_data {
  target = data.google_kms_key_ring.default
  values = {
    id = "projects/my-core-project/locations/us-east4/keyRings/my-kr"
  }
}

override_data {
  target = data.google_kms_crypto_key.default
  values = {
    id = "projects/my-core-project/locations/us-east4/keyRings/my-kr/cryptoKeys/default"
  }
}

variables {
  main_project_id             = "my-bt-project"
  core_project_id             = "my-core-project"
  instance_name               = "my-bt-instance"
  cluster_id                  = "my-bt-cluster"
  bigtable_service_account_id = "bigtable-sa"
  kms_keyring_name            = "my-kr"
  kms_key_name                = "default"
  region                      = "us-east4"
  zone                        = "us-east4-a"
}

run "plan_bigtable_cmek" {
  command = plan

  assert {
    condition     = google_project_service_identity.bigtable_sa.service == "bigtableadmin.googleapis.com"
    error_message = "Expected Bigtable service identity to be created."
  }

  assert {
    condition     = google_kms_crypto_key_iam_member.bigtable_agent_kms_access.role == "roles/cloudkms.cryptoKeyEncrypterDecrypter"
    error_message = "Expected Bigtable service agent KMS EncrypterDecrypter grant."
  }
}
