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
  main_project_id        = "my-docai-project"
  name                   = "my-processor"
  region                 = "us-east4"
  processor_kms_key_name = "projects/my-kms-project/locations/us/keyRings/kr-us/cryptoKeys/docai-key"
  regional_kms_key_name  = "projects/my-kms-project/locations/us-east4/keyRings/kr-reg/cryptoKeys/regional-key"
}

run "plan_split_cmek_keys" {
  command = plan

  assert {
    condition     = contains(keys(google_project_service.documentai), "storage.googleapis.com")
    error_message = "Expected storage.googleapis.com to be enabled."
  }

  assert {
    condition     = google_project_service_identity.documentai_sa.service == "documentai.googleapis.com"
    error_message = "Expected Document AI service identity to be provisioned."
  }

  assert {
    condition     = google_project_service_identity.workflows_sa.service == "workflows.googleapis.com"
    error_message = "Expected Workflows service identity to be provisioned."
  }

  assert {
    condition     = time_sleep.service_agent_propagation.create_duration == "60s"
    error_message = "Expected 60s propagation wait for service agents."
  }

  assert {
    condition     = google_document_ai_processor.processor.project == var.main_project_id
    error_message = "Expected processor project to match var.main_project_id."
  }

  assert {
    condition     = google_document_ai_processor.processor.location == "us"
    error_message = "Expected processor location to remain us."
  }

  assert {
    condition     = google_document_ai_processor.processor.kms_key_name == var.processor_kms_key_name
    error_message = "Expected processor to use var.processor_kms_key_name."
  }

  assert {
    condition     = google_service_account.workflow_sa.project == var.main_project_id
    error_message = "Expected workflow service account project to match var.main_project_id."
  }

  assert {
    condition     = google_kms_crypto_key_iam_member.documentai_cmek.crypto_key_id == var.processor_kms_key_name
    error_message = "Expected Document AI KMS grant on processor_kms_key_name."
  }

  assert {
    condition     = google_kms_crypto_key_iam_member.gcs_cmek.crypto_key_id == var.regional_kms_key_name
    error_message = "Expected GCS KMS grant on regional_kms_key_name."
  }

  assert {
    condition     = google_kms_crypto_key_iam_member.workflows_cmek.crypto_key_id == var.regional_kms_key_name
    error_message = "Expected Workflows KMS grant on regional_kms_key_name."
  }
}

run "rejects_regional_key_for_processor" {
  command = plan

  variables {
    processor_kms_key_name = "projects/my-kms-project/locations/us-east4/keyRings/kr-reg/cryptoKeys/regional-key"
  }

  expect_failures = [var.processor_kms_key_name]
}

run "rejects_mismatched_region_key" {
  command = plan

  variables {
    regional_kms_key_name = "projects/my-kms-project/locations/us/keyRings/kr-us/cryptoKeys/docai-key"
  }

  expect_failures = [var.regional_kms_key_name]
}
