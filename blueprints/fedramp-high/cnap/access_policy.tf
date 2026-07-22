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

resource "google_access_context_manager_access_levels" "access-levels" {
  parent = "accessPolicies/${var.access_policy_number}"

  # Access level for US Region
  access_levels {
    name  = "accessPolicies/${var.access_policy_number}/accessLevels/us"
    title = "US Traffic Source IP"
    basic {
      conditions {
        regions = [
          "US",
        ]
      }
    }
  }

  # Access level for Time (7AM-9PM Monday-Friday)
  access_levels {
    name  = "accessPolicies/${var.access_policy_number}/accessLevels/time"
    title = "Business Hours East Coast"
    custom {
      expr {
        expression = ("request.time.getHours(\"America/New_York\") >= 7 && request.time.getHours(\"America/New_York\") <= 21 && request.time.getDayOfWeek(\"America/New_York\") >= 1 && request.time.getDayOfWeek(\"America/New_York\") <= 5")
        title      = "TimeBasedControls"
      }
    }
  }

  # Access level for expiring access at midnight of 2024-12-31.
  access_levels {
    name  = "accessPolicies/${var.access_policy_number}/accessLevels/expire"
    title = "Expire Access 2024"
    custom {
      expr {
        expression = ("request.time < timestamp(\"2025-01-01T00:00:00Z\")")
      }
    }
  }

  # Access level for "easy" service, including US Region devices.
  access_levels {
    name  = "accessPolicies/${var.access_policy_number}/accessLevels/lenient_device"
    title = "Lenient Device Policy"
    basic {
      conditions {
        required_access_levels = ["accessPolicies/${var.access_policy_number}/accessLevels/us"]
      }
    }
  }

  # Access level for "moderate" service, including US Region, Time (7AM-9PM Monday-Friday) & Expiring Access by end of 2024.
  access_levels {
    name  = "accessPolicies/${var.access_policy_number}/accessLevels/moderate_device"
    title = "Moderate Device Policy"
    basic {
      conditions {
        required_access_levels = ["accessPolicies/${var.access_policy_number}/accessLevels/us", "accessPolicies/${var.access_policy_number}/accessLevels/time", "accessPolicies/${var.access_policy_number}/accessLevels/expire"]
      }
    }
  }

  # Access level for "strict" service, including Mac/Windows OS, Encryption enabled, Corp owned device, Expiring Access by end of 2024, Time (7AM-9PM Monday-Friday), & US Region.
  access_levels {
    name  = "accessPolicies/${var.access_policy_number}/accessLevels/strict_device"
    title = "Strict Device Policy"
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
  }
}