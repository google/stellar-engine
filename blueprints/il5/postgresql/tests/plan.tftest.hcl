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
  target = data.google_compute_network.network
  values = {
    self_link = "https://www.googleapis.com/compute/v1/projects/test-net-host/global/networks/test-vpc"
  }
}

variables {
  main_project_id    = "test-workload"
  network_project_id = "test-net-host"
  network_name       = "test-vpc"
  database_name      = "test-postgres"
  kms_key_name       = "projects/test-core/locations/us-east4/keyRings/test-kr/cryptoKeys/test-key"
}

# The blueprint plans without any firewall input, because it creates no VPC
# firewall rule.
run "plan_without_firewall_inputs" {
  command = plan

  assert {
    condition     = module.postgres.name == "test-postgres"
    error_message = "Expected the Cloud SQL instance to be planned."
  }

  assert {
    condition     = google_kms_crypto_key_iam_member.sql_sa.crypto_key_id == var.kms_key_name
    error_message = "Expected the Cloud SQL service agent CMEK binding."
  }
}

# Existing callers that still set the deprecated firewall inputs keep
# planning, and the deprecation check reports the ignored inputs.
run "plan_with_deprecated_firewall_inputs" {
  command = plan

  variables {
    allowed_firewall_ports = [5432]
    firewall_name          = "allow-postgres"
    firewall_source_range  = ["192.168.1.0/24"]
  }

  expect_failures = [
    check.deprecated_firewall_inputs,
  ]
}
