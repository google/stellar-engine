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

data "google_access_context_manager_access_policy" "policy" {
  parent = "organizations/${var.organization_id}"
}

resource "google_access_context_manager_access_level" "access_levels" {
  provider = google-beta
  for_each = { for level in var.access_levels : level.name => level }

  parent      = "accessPolicies/${data.google_access_context_manager_access_policy.policy.id}"
  name        = each.value.name
  title       = each.value.name
  description = each.value.description

  basic {
    conditions {
      ip_subnetworks = each.value.conditions[0].ip_subnetworks
      members        = each.value.conditions[0].members
      negate         = each.value.conditions[0].negate
      device_policy {
        require_screen_lock = each.value.conditions[0].device_policy.require_screen_lock
      }
      regions = each.value.conditions[0].regions
    }
  }
}

resource "google_access_context_manager_service_perimeter" "service_perimeters" {
  for_each = { for perimeter in var.service_perimeters : perimeter.name => perimeter }

  parent      = "accessPolicies/${data.google_access_context_manager_access_policy.policy.id}"
  name        = each.value.name
  title       = each.value.name
  description = each.value.description

  status {
    restricted_services = each.value.status.restricted_services
    resources           = each.value.status.resources
  }
}