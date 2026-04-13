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

# -----------------------------------------------------------------------------
# IAM ROLE ASSIGNMENTS
# -----------------------------------------------------------------------------
# Using google_project_iam_member to additively assign each role.
# This prevents conflicts with other IAM policies.

# --- Admin Group Roles ---
resource "google_project_iam_member" "admins_discoveryengine_admin" {
  project = var.main_project_id
  role    = "roles/discoveryengine.admin"
  member  = var.admin_group
}

resource "google_project_iam_member" "admins_aiplatform_admin" {
  project = var.main_project_id
  role    = "roles/aiplatform.admin"
  member  = var.admin_group
}

resource "google_project_iam_member" "admins_serviceusage_consumer" {
  project = var.main_project_id
  role    = "roles/serviceusage.serviceUsageConsumer"
  member  = var.admin_group
}

resource "google_project_iam_member" "admins_logging_viewer" {
  project = var.main_project_id
  role    = "roles/logging.viewer"
  member  = var.admin_group
}


# --- User Group Roles ---
resource "google_project_iam_member" "users_discoveryengine_user" {
  for_each = toset(var.user_groups)
  project  = var.main_project_id
  role     = "roles/discoveryengine.user"
  member   = each.value
}

resource "google_project_iam_member" "users_serviceusage_consumer" {
  for_each = toset(var.user_groups)
  project  = var.main_project_id
  role     = "roles/serviceusage.serviceUsageConsumer"
  member   = each.value
}
