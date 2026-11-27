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

override_data {
  target = data.google_kms_key_ring.default
  values = {
    id = "projects/test-core/locations/us-east4/keyRings/test-kr"
  }
}

override_data {
  target = data.google_kms_crypto_key.default
  values = {
    id = "projects/test-core/locations/us-east4/keyRings/test-kr/cryptoKeys/default"
  }
}

override_data {
  target = data.google_storage_project_service_account.gcs_sa
  values = {
    email_address = "service-123456789012@gs-project-accounts.iam.gserviceaccount.com"
    member        = "serviceAccount:service-123456789012@gs-project-accounts.iam.gserviceaccount.com"
  }
}

variables {
  main_project_id  = "test-workload"
  core_project_id  = "test-core"
  prefix           = "test"
  bucket_name      = "bucket-00"
  region           = "us-east4"
  kms_keyring_name = "test-kr"
  kms_key_name     = "default"
}

run "apply_autoclass_default_and_service_agent_cmek" {
  command = apply

  assert {
    condition     = var.autoclass == true
    error_message = "Expected autoclass to default to true."
  }

  assert {
    condition     = google_project_service.storage_api.service == "storage.googleapis.com"
    error_message = "Expected storage.googleapis.com API resource to be enabled."
  }

  assert {
    condition     = google_kms_crypto_key_iam_member.gcs_sa_kms_access.member == "serviceAccount:service-123456789012@gs-project-accounts.iam.gserviceaccount.com"
    error_message = "Expected Cloud Storage service agent from data.google_storage_project_service_account."
  }

  assert {
    condition     = length(module.gcs.bucket.autoclass) == 1 && module.gcs.bucket.autoclass[0].enabled == true
    error_message = "Expected module.gcs bucket to enable autoclass when var.autoclass is true."
  }
}

run "plan_autoclass_disabled_allows_nearline" {
  command = plan

  variables {
    autoclass     = false
    storage_class = "NEARLINE"
  }

  assert {
    condition     = length(module.gcs.bucket.autoclass) == 1 && module.gcs.bucket.autoclass[0].enabled == false
    error_message = "Expected module.gcs bucket autoclass block to reflect enabled = false."
  }

  assert {
    condition     = module.gcs.bucket.storage_class == "NEARLINE"
    error_message = "Expected NEARLINE storage class when autoclass is disabled."
  }
}

run "reject_autoclass_true_with_non_standard_storage_class" {
  command = plan

  variables {
    autoclass     = true
    storage_class = "NEARLINE"
  }

  expect_failures = [
    var.storage_class,
  ]
}
