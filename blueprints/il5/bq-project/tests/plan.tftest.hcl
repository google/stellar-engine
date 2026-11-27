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

variables {
  main_project_id     = "test-workload"
  dataset_id          = "test_dataset"
  dataset_description = "Test dataset"
  region              = "us-east4"
  kms_keyring_name = {
    location = "us-east4"
    name     = "test-bq-keyring"
  }
}

run "apply_default_dataset_and_bigquery_api" {
  command = apply

  assert {
    condition     = google_project_service.bigquery_api.service == "bigquery.googleapis.com"
    error_message = "Expected bigquery.googleapis.com API resource to be enabled."
  }

  assert {
    condition     = length(module.kms.keys) == 1 && contains(keys(module.kms.keys), "default")
    error_message = "Expected default KMS key to be provisioned for dataset encryption."
  }

  assert {
    condition     = length(output.table_ids) == 0
    error_message = "Expected no tables when var.tables uses its empty default."
  }
}

run "apply_structured_tables_object_schema" {
  command = apply

  variables {
    tables = {
      events = {
        deletion_protection = false
        description         = "Sample partitioned table."
        labels = {
          env = "test"
        }
        options = {
          clustering = ["event_type"]
        }
        partitioning = {
          time = {
            type  = "DAY"
            field = "event_ts"
          }
        }
      }
    }
  }

  assert {
    condition     = contains(keys(output.tables), "events")
    error_message = "Expected events table to be created via structured var.tables schema."
  }

  assert {
    condition     = module.bigquery-dataset.tables["events"].deletion_protection == false
    error_message = "Expected boolean deletion_protection = false to propagate cleanly."
  }
}
