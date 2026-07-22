/**
 * Copyright 2026 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
# Enable the PAM API
resource "google_project_service" "pam" {
  project            = var.main_project_id
  service            = "privilegedaccessmanager.googleapis.com"
  disable_on_destroy = false
}

# Create the PAM service identity to ensure the service agent exists
resource "google_project_service_identity" "pam_service_agent" {
  provider = google-beta
  project  = var.main_project_id
  service  = "privilegedaccessmanager.googleapis.com"

  depends_on = [google_project_service.pam]
}

# Use the PAM module to create entitlements
module "pam" {
  for_each = var.entitlements
  source   = "../../../modules/privileged-access-manager"

  entitlement_id                                   = each.key
  location                                         = each.value.location
  max_request_duration_hours                       = each.value.max_request_duration_hours
  parent_type                                      = each.value.parent_type
  parent_id                                        = each.value.parent_id
  organization_id                                  = var.organization_id
  grant_service_agent_permissions                  = each.value.grant_service_agent_permissions
  entitlement_requesters                           = each.value.requesters
  entitlement_approvers                            = each.value.approvers
  entitlement_approval_notification_recipients     = each.value.notification_recipients.approval
  entitlement_pending_notification_recipients      = each.value.notification_recipients.pending
  entitlement_availability_notification_recipients = each.value.notification_recipients.availability
  role_bindings                                    = each.value.role_bindings
  auto_approve_entitlement                         = each.value.auto_approve_entitlement
  require_approver_justification                   = each.value.require_approver_justification
  requester_justification                          = each.value.requester_justification

  depends_on = [
    google_project_service_identity.pam_service_agent
  ]
}
