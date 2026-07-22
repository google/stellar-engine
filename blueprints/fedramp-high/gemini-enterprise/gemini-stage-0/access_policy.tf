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

# Access level for allowlisted source IP ranges
resource "google_access_context_manager_access_level" "ip_based_access" {
  count  = var.access_policy_number != "" && length(var.allowed_ip_ranges) > 0 && var.create_ip_based_access ? 1 : 0
  parent = "accessPolicies/${var.access_policy_number}"
  name   = "accessPolicies/${var.access_policy_number}/accessLevels/ip_based_access"
  title  = "IP-Based Access Control"
  basic {
    conditions {
      ip_subnetworks = var.allowed_ip_ranges
    }
  }
}

# Access level for US Region
resource "google_access_context_manager_access_level" "us" {
  count  = var.access_policy_number != "" && var.create_us_access ? 1 : 0
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
}

# Access level for Time (7AM-9PM Monday-Friday)
resource "google_access_context_manager_access_level" "time" {
  count  = var.access_policy_number != "" && var.create_time_access ? 1 : 0
  parent = "accessPolicies/${var.access_policy_number}"
  name   = "accessPolicies/${var.access_policy_number}/accessLevels/time"
  title  = "Business Hours East Coast"
  custom {
    expr {
      expression = ("request.time.getHours(\"${var.access_time_zone}\") >= ${var.access_start_hour} && request.time.getHours(\"${var.access_time_zone}\") <= ${var.access_end_hour} && request.time.getDayOfWeek(\"${var.access_time_zone}\") >= ${var.access_start_day} && request.time.getDayOfWeek(\"${var.access_time_zone}\") <= ${var.access_end_day}")
      title      = "TimeBasedControls"
    }
  }
}

# Access level for expiring access at midnight of 2026-12-31.
resource "google_access_context_manager_access_level" "expire" {
  count  = var.access_policy_number != "" && var.create_expire_access ? 1 : 0
  parent = "accessPolicies/${var.access_policy_number}"
  name   = "accessPolicies/${var.access_policy_number}/accessLevels/expire"
  title  = "Expire Access 2026"
  custom {
    expr {
      expression = ("request.time < timestamp(\"${var.access_expiration_timestamp}\")")
    }
  }
}

# Access level for "Lenient" policies, limiting access to only the US Region.
resource "google_access_context_manager_access_level" "lenient_device" {
  count  = var.access_policy_number != "" && var.create_lenient_device_access ? 1 : 0
  parent = "accessPolicies/${var.access_policy_number}"
  name   = "accessPolicies/${var.access_policy_number}/accessLevels/lenient_device"
  title  = "Lenient Device Policy"
  basic {
    conditions {
      required_access_levels = var.lenient_device_access_levels
    }
  }
  depends_on = [google_access_context_manager_access_level.us]
}

# Access level for "Moderate" policies, limiting access to only the US Region, Time (7AM-9PM Monday-Friday) & Expiring Access after a date (example: by end of 2027).
resource "google_access_context_manager_access_level" "moderate_device" {
  count  = var.access_policy_number != "" && var.create_moderate_device_access ? 1 : 0
  parent = "accessPolicies/${var.access_policy_number}"
  name   = "accessPolicies/${var.access_policy_number}/accessLevels/moderate_device"
  title  = "Moderate Device Policy"
  basic {
    conditions {
      required_access_levels = var.moderate_device_access_levels
    }
  }
  depends_on = [
    google_access_context_manager_access_level.us,
    google_access_context_manager_access_level.time,
    google_access_context_manager_access_level.expire
  ]
}

# Access level for "strict" service, including Mac/Windows OS, Encryption enabled, Corp owned device, Expiring Access by end of 2024, Time (7AM-9PM Monday-Friday), & US Region.
resource "google_access_context_manager_access_level" "strict_device" {
  count  = var.access_policy_number != "" && var.enable_chrome_enterprise_premium && var.create_strict_device_access ? 1 : 0
  parent = "accessPolicies/${var.access_policy_number}"
  name   = "accessPolicies/${var.access_policy_number}/accessLevels/strict_device"
  title  = "Strict Device Policy"
  basic {
    conditions {
      required_access_levels = ["accessPolicies/${var.access_policy_number}/accessLevels/us", "accessPolicies/${var.access_policy_number}/accessLevels/time", "accessPolicies/${var.access_policy_number}/accessLevels/expire"]
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
  depends_on = [
    google_access_context_manager_access_level.us,
    google_access_context_manager_access_level.time,
    google_access_context_manager_access_level.expire
  ]
}
