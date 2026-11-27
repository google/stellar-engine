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

variables {
  main_project_id = "my-project"
  region          = "us-east4"
}

run "plan_default_from_index_yaml" {
  command = plan

  assert {
    condition     = module.firestore.firestore_database.type == "DATASTORE_MODE"
    error_message = "Expected DATASTORE_MODE database."
  }

  assert {
    condition     = module.firestore.firestore_database.delete_protection_state == "DELETE_PROTECTION_ENABLED"
    error_message = "Expected deletion protection enabled by default."
  }

  assert {
    condition     = length(module.firestore.firestore_indexes) == 0
    error_message = "Expected module.firestore to manage zero indexes directly."
  }

  assert {
    condition     = length(google_firestore_index.firestore_indexes) == 2
    error_message = "Expected two composite indexes parsed from index.yaml."
  }

  assert {
    condition     = contains(keys(google_firestore_index.firestore_indexes), "Task-noanc-done-asc-priority-desc")
    error_message = "Expected deterministic Task composite index key."
  }

  assert {
    condition     = google_firestore_index.firestore_indexes["Task-noanc-done-asc-priority-desc"].api_scope == "DATASTORE_MODE_API"
    error_message = "Expected DATASTORE_MODE_API api_scope on YAML composite index."
  }

  assert {
    condition     = google_firestore_index.firestore_indexes["Task-noanc-done-asc-priority-desc"].query_scope == "COLLECTION_GROUP"
    error_message = "Expected COLLECTION_GROUP query_scope on non-ancestor Datastore mode composite index."
  }

  assert {
    condition     = google_firestore_index.firestore_indexes["Task-noanc-done-asc-priority-desc"].database == "(default)"
    error_message = "Expected default database name when database_create is true."
  }

  assert {
    condition     = length(google_kms_crypto_key_iam_member.firestore_cmek) == 0
    error_message = "Expected no KMS IAM member when kms_key_name is null."
  }
}

run "plan_empty_index_yaml" {
  command = plan

  variables {
    index_file = "tests/fixtures/empty_indexes.yaml"
  }

  assert {
    condition     = length(google_firestore_index.firestore_indexes) == 0
    error_message = "Expected empty indexes key in YAML to plan zero composite indexes."
  }
}

run "plan_descending_and_null_yaml_defaults" {
  command = plan

  variables {
    index_file = "tests/fixtures/descending_nulls.yaml"
  }

  assert {
    condition     = google_firestore_index.firestore_indexes["Event-noanc-created_at-desc-severity-asc"].fields[0].order == "DESCENDING"
    error_message = "Expected descending in YAML to map to DESCENDING."
  }

  assert {
    condition     = google_firestore_index.firestore_indexes["Event-noanc-created_at-desc-severity-asc"].fields[1].order == "ASCENDING"
    error_message = "Expected null direction in YAML to default to ASCENDING."
  }

  assert {
    condition     = google_firestore_index.firestore_indexes["Event-noanc-created_at-desc-severity-asc"].query_scope == "COLLECTION_GROUP"
    error_message = "Expected null ancestor in YAML to map to COLLECTION_GROUP."
  }
}

run "plan_ancestor_yes_maps_to_collection_recursive" {
  command = plan

  variables {
    index_file = "tests/fixtures/ancestor_yes.yaml"
  }

  assert {
    condition     = google_firestore_index.firestore_indexes["Task-anc-done-asc-priority-desc"].api_scope == "DATASTORE_MODE_API"
    error_message = "Expected DATASTORE_MODE_API on ancestor index."
  }

  assert {
    condition     = google_firestore_index.firestore_indexes["Task-anc-done-asc-priority-desc"].query_scope == "COLLECTION_RECURSIVE"
    error_message = "Expected COLLECTION_RECURSIVE query_scope when ancestor is yes."
  }
}

run "plan_with_cmek_and_existing_database" {
  command = plan

  variables {
    database_create     = false
    database_name       = "existing-datastore"
    deletion_protection = false
    kms_key_name        = "projects/core-project/locations/us-east4/keyRings/kr/cryptoKeys/k1"
    indexes = {
      custom-idx = {
        api_scope   = "DATASTORE_MODE_API"
        collection  = "Orders"
        query_scope = "COLLECTION_GROUP"
        fields = [
          {
            field_path = "status"
            order      = "ASCENDING"
          }
        ]
      }
    }
  }

  assert {
    condition     = length(google_kms_crypto_key_iam_member.firestore_cmek) == 1
    error_message = "Expected KMS IAM member when kms_key_name is configured."
  }

  assert {
    condition     = length(google_firestore_index.firestore_indexes) == 1
    error_message = "Expected explicit indexes variable to override index.yaml."
  }

  assert {
    condition     = google_firestore_index.firestore_indexes["custom-idx"].database == "existing-datastore"
    error_message = "Expected database_create = false to pass var.database_name to google_firestore_index."
  }
}

run "plan_rejects_invalid_ancestor" {
  command = plan

  variables {
    index_file = "tests/fixtures/invalid_ancestor.yaml"
  }

  expect_failures = [
    google_project_service.apis
  ]
}

run "plan_rejects_invalid_direction" {
  command = plan

  variables {
    index_file = "tests/fixtures/invalid_direction.yaml"
  }

  expect_failures = [
    google_project_service.apis
  ]
}

run "plan_rejects_duplicate_indexes" {
  command = plan

  variables {
    index_file = "tests/fixtures/duplicate_indexes.yaml"
  }

  expect_failures = [
    google_project_service.apis
  ]
}
