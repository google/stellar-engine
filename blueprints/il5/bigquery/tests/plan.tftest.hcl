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
  target = data.google_bigquery_default_service_account.bq_sa
  values = {
    email  = "bq-123456789012@bigquery-encryption.iam.gserviceaccount.com"
    member = "serviceAccount:bq-123456789012@bigquery-encryption.iam.gserviceaccount.com"
  }
}

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

variables {
  main_project_id     = "test-workload"
  core_project_id     = "test-core"
  dataset_id          = "test_dataset"
  dataset_description = "Test dataset"
  region              = "us-east4"
  kms_keyring_name    = "test-kr"
  kms_key_name        = "default"
  tables = {
    table_1 = {
      deletion_protection = false
      labels              = {}
      options = {
        encryption_key = "projects/test-core/locations/us-east4/keyRings/test-kr/cryptoKeys/default"
      }
    }
  }
}

run "apply_bigquery_dataset_with_cmek_and_tables" {
  command = apply

  assert {
    condition     = google_project_service.bigquery_api.service == "bigquery.googleapis.com"
    error_message = "Expected bigquery.googleapis.com API resource to be enabled."
  }

  assert {
    condition     = google_kms_crypto_key_iam_member.bq_sa_kms_access.member == "serviceAccount:bq-123456789012@bigquery-encryption.iam.gserviceaccount.com"
    error_message = "Expected BigQuery default service account to receive KMS access."
  }

  assert {
    condition     = contains(keys(output.tables), "table_1")
    error_message = "Expected table_1 to be created."
  }
}
