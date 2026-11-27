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
  target = data.google_project.project
  values = {
    number = "123456789012"
  }
}

variables {
  main_project_id    = "my-ws-project"
  core_project_id    = "my-core-project"
  network_project_id = "my-net-host"
  kms_keyring_name   = "my-kr"
  kms_key_name       = "default"
  network_name       = "prod-spoke-0"
  subnetwork_name    = "prod-tenant-1-subnet"
  region             = "us-east4"
  workstations = {
    ws-00 = {
      users = ["user:admin@example.com"]
    }
  }
}

run "plan_workstations_cmek" {
  command = plan

  assert {
    condition     = google_kms_crypto_key_iam_member.compute_sa_kms_permissions.member == "serviceAccount:service-123456789012@compute-system.iam.gserviceaccount.com"
    error_message = "Expected Compute Engine service agent to receive CMEK key access."
  }

  assert {
    condition     = google_kms_crypto_key_iam_member.workstations_sa_kms_permissions.crypto_key_id == "projects/my-core-project/locations/us-east4/keyRings/my-kr/cryptoKeys/default"
    error_message = "Expected workstation config SA KMS binding to target the configured KMS key."
  }
}
