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

override_data {
  target = data.google_compute_network.network
  values = {
    self_link = "https://www.googleapis.com/compute/v1/projects/my-net-host/global/networks/prod-spoke-0"
  }
}

override_data {
  target = data.google_compute_subnetwork.subnetwork
  values = {
    self_link = "https://www.googleapis.com/compute/v1/projects/my-net-host/regions/us-east4/subnetworks/prod-tenant-1-subnet"
  }
}

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

override_data {
  target = data.google_storage_project_service_account.gcs_account_main_project
  values = {
    email_address = "service-123456789012@gs-project-accounts.iam.gserviceaccount.com"
  }
}

variables {
  main_project_id    = "my-df-project"
  core_project_id    = "my-core-project"
  network_project_id = "my-net-host"
  name               = "df-instance-00"
  region             = "us-east4"
  kms_keyring_name   = "my-kr"
  kms_key_name       = "default"
  network_name       = "prod-spoke-0"
  subnetwork_name    = "prod-tenant-1-subnet"
}

run "plan_psc_default" {
  command = apply

  assert {
    condition     = output.service_endpoint == module.datafusion.service_endpoint
    error_message = "Expected blueprint service_endpoint output to reference module.datafusion.service_endpoint."
  }

  assert {
    condition     = google_service_account.datafusion_sa.account_id == "df-my-df-project"
    error_message = "Expected Dataproc worker service account ID to be configured."
  }
}

run "rejects_vpc_peering_without_ip_allocation" {
  command = plan

  variables {
    connection_type = "VPC_PEERING"
  }

  expect_failures = [
    var.ip_allocation,
  ]
}
