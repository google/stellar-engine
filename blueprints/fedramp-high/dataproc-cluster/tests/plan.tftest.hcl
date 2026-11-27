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
  target = data.google_project.current
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
    id            = "projects/my-net-host/regions/us-east4/subnetworks/prod-tenant-1-subnet"
    ip_cidr_range = "10.0.0.0/24"
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
  target = data.google_storage_project_service_account.gcs_sa
  values = {
    member = "serviceAccount:service-123456789012@gs-project-accounts.iam.gserviceaccount.com"
  }
}

variables {
  main_project_id       = "my-dp-project"
  core_project_id       = "my-core-project"
  network_project_id    = "my-net-host"
  dataproc_cluster_name = "dp-cluster-00"
  dataproc_bucket_name  = "dp-bucket-00"
  network_name          = "prod-spoke-0"
  subnetwork_name       = "prod-tenant-1-subnet"
  firewall_name         = "allow-dataproc"
  kms_keyring_name      = "my-kr"
  kms_key_name          = "default"
  region                = "us-east4"
}

run "plan_dataproc_cmek" {
  command = plan

  assert {
    condition     = google_service_account.dataproc_vm.project == "my-dp-project"
    error_message = "Expected Dataproc VM service account to bind explicitly to main_project_id."
  }

  assert {
    condition     = length(google_kms_crypto_key_iam_member.dataproc_kms) == 4
    error_message = "Expected four KMS grants covering VM SA, GCS, Dataproc, and Compute service agents."
  }

  assert {
    condition     = google_kms_crypto_key_iam_member.dataproc_kms["compute_agent"].member == "serviceAccount:service-123456789012@compute-system.iam.gserviceaccount.com"
    error_message = "Expected Compute service agent KMS access."
  }
}
