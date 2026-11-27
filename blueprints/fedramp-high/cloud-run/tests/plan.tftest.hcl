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
  main_project_id  = "my-cr-project"
  core_project_id  = "my-core-project"
  name             = "my-cr-service"
  region           = "us-east4"
  kms_keyring_name = "my-kr"
  kms_key_name     = "default"
  container_image  = "us-docker.pkg.dev/cloudrun/container/hello"
}

run "plan_service_mode" {
  command = plan

  assert {
    condition     = google_project_service.cloud_run.project == "my-cr-project"
    error_message = "Expected run API service enablement to target var.main_project_id."
  }

  assert {
    condition     = google_kms_crypto_key_iam_member.cloud_run_service_agent_kms_permissions.role == "roles/cloudkms.cryptoKeyEncrypterDecrypter"
    error_message = "Expected Cloud Run service agent to receive CMEK key grant."
  }

  assert {
    condition     = length(google_cloud_run_v2_service_iam_member.cloud_run_invoker) == 1
    error_message = "Expected service invoker binding in service mode."
  }
}

run "plan_job_mode_deletion_unprotected" {
  command = plan

  variables {
    is_job              = true
    deletion_protection = false
  }

  assert {
    condition     = length(google_cloud_run_v2_job_iam_member.cloud_run_invoker) == 1
    error_message = "Expected job invoker binding in job mode."
  }
}
