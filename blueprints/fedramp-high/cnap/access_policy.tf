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

# Additive access levels avoid replacing existing organization-wide access levels.
resource "google_access_context_manager_access_level" "us" {
  parent = "accessPolicies/${var.access_policy_number}"
  name   = "accessPolicies/${var.access_policy_number}/accessLevels/us"
  title  = "US Traffic Source IP"
  basic {
    conditions {
      regions = [
        "US",
      ]
    }
  }
  depends_on = [google_project_service.services]
}

# Business hours (7 AM to 9 PM America/New_York, Monday through Friday).
resource "google_access_context_manager_access_level" "time" {
  parent = "accessPolicies/${var.access_policy_number}"
  name   = "accessPolicies/${var.access_policy_number}/accessLevels/time"
  title  = "Business Hours East Coast"
  custom {
    expr {
      expression = ("request.time.getHours(\"America/New_York\") >= 7 && request.time.getHours(\"America/New_York\") <= 21 && request.time.getDayOfWeek(\"America/New_York\") >= 1 && request.time.getDayOfWeek(\"America/New_York\") <= 5")
      title      = "TimeBasedControls"
    }
  }
  depends_on = [google_project_service.services]
}

# Optional expiring access level when access_expiry_timestamp is configured.
resource "google_access_context_manager_access_level" "expire" {
  count  = var.access_expiry_timestamp != null ? 1 : 0
  parent = "accessPolicies/${var.access_policy_number}"
  name   = "accessPolicies/${var.access_policy_number}/accessLevels/expire"
  title  = "Expiring Access"
  custom {
    expr {
      expression = "request.time < timestamp(\"${var.access_expiry_timestamp}\")"
    }
  }
  depends_on = [google_project_service.services]
}

# Lenient device access level requiring US region source IPs.
resource "google_access_context_manager_access_level" "lenient_device" {
  parent = "accessPolicies/${var.access_policy_number}"
  name   = "accessPolicies/${var.access_policy_number}/accessLevels/lenient_device"
  title  = "Lenient Device Policy"
  basic {
    conditions {
      required_access_levels = [
        google_access_context_manager_access_level.us.name,
      ]
    }
  }
}

# Moderate device access level requiring US region and business hours.
resource "google_access_context_manager_access_level" "moderate_device" {
  parent = "accessPolicies/${var.access_policy_number}"
  name   = "accessPolicies/${var.access_policy_number}/accessLevels/moderate_device"
  title  = "Moderate Device Policy"
  basic {
    conditions {
      required_access_levels = [
        google_access_context_manager_access_level.us.name,
        google_access_context_manager_access_level.time.name,
      ]
    }
  }
}

# Strict device access level requiring encrypted corp-owned Windows/macOS, business hours, and US region.
resource "google_access_context_manager_access_level" "strict_device" {
  parent = "accessPolicies/${var.access_policy_number}"
  name   = "accessPolicies/${var.access_policy_number}/accessLevels/strict_device"
  title  = "Strict Device Policy"
  basic {
    conditions {
      required_access_levels = [
        google_access_context_manager_access_level.us.name,
        google_access_context_manager_access_level.time.name,
      ]
      device_policy {
        require_screen_lock = true
        os_constraints {
          os_type = "DESKTOP_MAC"
        }
        os_constraints {
          os_type = "DESKTOP_WINDOWS"
        }

        allowed_encryption_statuses = [
          "ENCRYPTED",
        ]
        require_corp_owned = true
      }
    }
  }
}