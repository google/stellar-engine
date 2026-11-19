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

# roles/composer.worker stays on the project. Its permissions span several
# services, and Composer creates the resources they apply to, such as the
# environment bucket, while it creates the environment.
resource "google_project_iam_member" "composer_worker" {
  project = var.main_project_id
  role    = "roles/composer.worker"
  member  = google_service_account.composer.member
}

# The role in var.service_agent_version stays on the project. The caller
# selects the role, so this blueprint cannot assume that every value is
# grantable on the environment service account alone.
resource "google_project_iam_member" "composer_service_agent" {
  project = var.main_project_id
  role    = var.service_agent_version
  member  = google_project_service_identity.composer_agent.member
}

# roles/compute.networkUser is bound on the environment subnetwork instead of
# the Shared VPC host project, so this role grants no access to the other
# subnetworks of the host project.
resource "google_compute_subnetwork_iam_member" "composer_network_user" {
  project    = data.google_compute_subnetwork.subnetwork.project
  region     = data.google_compute_subnetwork.subnetwork.region
  subnetwork = data.google_compute_subnetwork.subnetwork.name
  role       = "roles/compute.networkUser"
  member     = google_project_service_identity.composer_agent.member
}

# roles/composer.sharedVpcAgent stays on the Shared VPC host project. Private
# IP environments need it there, and it carries network-scoped permissions,
# such as VPC peering management, that a subnetwork binding cannot grant.
resource "google_project_iam_member" "composer_vpc_agent" {
  project = var.network_project_id
  role    = "roles/composer.sharedVpcAgent"
  member  = google_project_service_identity.composer_agent.member
}
