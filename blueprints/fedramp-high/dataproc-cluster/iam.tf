# Copyright 2025 Google LLC
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

resource "google_project_iam_member" "worker" {
  project = var.main_project_id
  role    = "roles/dataproc.worker"
  member  = google_service_account.dataproc_vm.member
}

resource "google_project_iam_member" "dataproc_service_agent" {
  project    = var.main_project_id
  role       = "roles/dataproc.serviceAgent"
  member     = google_project_service_identity.dataproc_agent.member
  depends_on = [time_sleep.dataproc_agent_propagation]
}

resource "google_project_iam_member" "dataproc_network_user" {
  project    = var.network_project_id
  role       = "roles/compute.networkUser"
  member     = google_project_service_identity.dataproc_agent.member
  depends_on = [time_sleep.dataproc_agent_propagation]
}

# Required for delete
resource "google_project_iam_member" "dataproc_compute_viewer" {
  project    = var.main_project_id
  role       = "roles/compute.viewer"
  member     = google_project_service_identity.dataproc_agent.member
  depends_on = [time_sleep.dataproc_agent_propagation]
}

resource "google_kms_crypto_key_iam_member" "dataproc_kms" {
  for_each = {
    dataproc_vm    = google_service_account.dataproc_vm.member
    gcs_agent      = data.google_storage_project_service_account.gcs_sa.member
    dataproc_agent = google_project_service_identity.dataproc_agent.member
    compute_agent  = "serviceAccount:service-${data.google_project.current.number}@compute-system.iam.gserviceaccount.com"
  }
  crypto_key_id = data.google_kms_crypto_key.default.id
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = each.value
  depends_on    = [time_sleep.dataproc_agent_propagation]
}