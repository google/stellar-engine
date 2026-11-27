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
  target = data.google_storage_project_service_account.gcs_sa
  values = {
    member = "serviceAccount:service-123456789012@gs-project-accounts.iam.gserviceaccount.com"
  }
}

variables {
  main_project_id   = "my-translate-project"
  region            = "us-east4"
  kms_key_self_link = "projects/my-kms-project/locations/us-east4/keyRings/kr-reg/cryptoKeys/translate-key"
}

run "plan_with_cmek" {
  command = plan

  assert {
    condition     = contains(keys(google_project_service.translate), "storage.googleapis.com")
    error_message = "Expected storage.googleapis.com to be enabled."
  }

  assert {
    condition     = google_project_service_identity.translate_sa.service == "translate.googleapis.com"
    error_message = "Expected Cloud Translation service identity to be provisioned."
  }

  assert {
    condition     = google_project_service_identity.workflows_sa.service == "workflows.googleapis.com"
    error_message = "Expected Workflows service identity to be provisioned."
  }

  assert {
    condition     = length(time_sleep.service_agent_propagation) == 1
    error_message = "Expected propagation wait when kms_key_self_link is set."
  }

  assert {
    condition     = length(google_kms_crypto_key_iam_member.gcs_cmek) == 1
    error_message = "Expected GCS KMS grant when kms_key_self_link is set."
  }

  assert {
    condition     = length(google_kms_crypto_key_iam_member.translate_cmek) == 1
    error_message = "Expected Cloud Translation KMS grant when kms_key_self_link is set."
  }

  assert {
    condition     = length(google_kms_crypto_key_iam_member.workflows_cmek) == 1
    error_message = "Expected Workflows KMS grant when kms_key_self_link is set."
  }

  assert {
    condition     = google_service_account.workflow_sa.project == var.main_project_id
    error_message = "Expected workflow service account project to match var.main_project_id."
  }

  assert {
    condition     = module.workflows.workflow.user_env_vars["parent"] == "projects/my-translate-project/locations/us-east4"
    error_message = "Expected workflow parent env var to use var.region."
  }
}

run "plan_without_cmek" {
  command = plan

  variables {
    kms_key_self_link = null
  }

  assert {
    condition     = length(time_sleep.service_agent_propagation) == 0
    error_message = "Expected no propagation wait when kms_key_self_link is null."
  }

  assert {
    condition     = length(google_kms_crypto_key_iam_member.gcs_cmek) == 0
    error_message = "Expected no GCS KMS grant when kms_key_self_link is null."
  }

  assert {
    condition     = length(google_kms_crypto_key_iam_member.workflows_cmek) == 0
    error_message = "Expected no Workflows KMS grant when kms_key_self_link is null."
  }

  assert {
    condition     = module.workflows.workflow.user_env_vars["parent"] == "projects/my-translate-project/locations/us-east4"
    error_message = "Expected workflow parent env var to use var.region."
  }
}

run "rejects_mismatched_region_key" {
  command = plan

  variables {
    kms_key_self_link = "projects/my-kms-project/locations/us-central1/keyRings/kr-reg/cryptoKeys/translate-key"
  }

  expect_failures = [var.kms_key_self_link]
}
