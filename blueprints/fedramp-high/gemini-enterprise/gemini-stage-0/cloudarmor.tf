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

locals {
  waf = yamldecode(file("data/cloudarmor.yaml"))
}

resource "google_compute_region_security_policy" "gemini_enterprise_policy" {
  count    = var.deployment_type != "none" ? 1 : 0
  provider = google-beta
  project  = var.main_project_id
  region   = var.region

  name        = "${var.prefix}-security-policy"
  description = "WAF policy for Gemini Enterprise access"

  type = "CLOUD_ARMOR"

  # Rules: OWASP Preconfigured WAF rules (set in data/cloudarmor.yaml)
  dynamic "rules" {
    for_each = local.waf.basic_rules
    content {
      action   = "allow"
      priority = rules.value.priority
      preview  = rules.value.preview
      match {
        expr {
          expression = "evaluatePreconfiguredWaf('${rules.value.expression}', {'sensitivity': ${rules.value.sensitivity}})"
        }
      }
      description = "WAF rule: ${rules.key}"
    }
  }

  dynamic "rules" {
    for_each = length(var.allowed_ip_ranges) > 0 ? [1] : []
    content {
      # Custom Rule 1: Allow traffic from a specific IP range.
      action   = "allow"
      priority = 1000
      match {
        versioned_expr = "SRC_IPS_V1"
        config {
          src_ip_ranges = var.allowed_ip_ranges
        }
      }
      description = "Allow traffic from a set of IP ranges"
    }
  }

  rules {
    # Custom Rule 2: Allow traffic only from the United States.
    action   = "allow"
    priority = 2000
    match {
      expr {
        expression = "origin.region_code == 'US'"
      }
    }
    description = "Allow traffic from the US"
  }

  rules {
    # Default Rule: Deny all other traffic that doesn't match an allow rule.
    action   = "deny(403)"
    priority = 2147483647 # Lowest possible priority
    match {
      versioned_expr = "SRC_IPS_V1"
      config {
        src_ip_ranges = ["*"]
      }
    }
    description = "Default deny rule"
  }
}
