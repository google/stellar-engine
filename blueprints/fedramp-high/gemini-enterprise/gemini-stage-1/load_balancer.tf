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

# Data source to read Stage 0 state
data "terraform_remote_state" "stage_0" {
  backend = "gcs"
  config = {
    bucket = var.stage_0_state_bucket
    prefix = "terraform/state/stage-0"
  }
}

# Data source to get the details of the customer's pre-uploaded SSL certificate
data "google_compute_region_ssl_certificate" "gemini_enterprise_cert" {
  count   = data.terraform_remote_state.stage_0.outputs.deployment_type != "none" && var.cert_management_choice == "self_managed" ? 1 : 0
  project = data.terraform_remote_state.stage_0.outputs.main_project_id
  name    = var.ssl_certificate_name
  region  = data.terraform_remote_state.stage_0.outputs.region
}

# Data source to get the backend service created in stage-0
data "google_compute_region_backend_service" "gemini_enterprise_backend" {
  count   = data.terraform_remote_state.stage_0.outputs.deployment_type != "none" ? 1 : 0
  project = data.terraform_remote_state.stage_0.outputs.main_project_id
  name    = "${data.terraform_remote_state.stage_0.outputs.prefix}-backend-service"
  region  = data.terraform_remote_state.stage_0.outputs.region
}

# Data source to get the network created in stage-0 or Shared VPC
data "google_compute_network" "gemini_enterprise_vpc" {
  count   = data.terraform_remote_state.stage_0.outputs.deployment_type != "none" ? 1 : 0
  project = var.host_project_id != "" ? var.host_project_id : (
    try(data.terraform_remote_state.stage_0.outputs.use_shared_vpc, false) ? data.terraform_remote_state.stage_0.outputs.network_project_id : data.terraform_remote_state.stage_0.outputs.main_project_id
  )
  name = var.network_name != "" ? var.network_name : (
    try(data.terraform_remote_state.stage_0.outputs.use_shared_vpc, false) ? data.terraform_remote_state.stage_0.outputs.shared_vpc_network_name : "${data.terraform_remote_state.stage_0.outputs.prefix}-vpc"
  )
}

# Data source to get the IP address created in stage-0
data "google_compute_address" "gemini_enterprise_ip" {
  count   = data.terraform_remote_state.stage_0.outputs.deployment_type != "none" ? 1 : 0
  project = data.terraform_remote_state.stage_0.outputs.main_project_id
  name    = "${data.terraform_remote_state.stage_0.outputs.prefix}-${data.terraform_remote_state.stage_0.outputs.deployment_type}-ip"
  region  = data.terraform_remote_state.stage_0.outputs.region
}

locals {
  load_balancing_scheme = data.terraform_remote_state.stage_0.outputs.deployment_type == "internal" ? "INTERNAL_MANAGED" : "EXTERNAL_MANAGED"
}

# This resource defines the URL map with the specified routing rules.
resource "google_compute_region_url_map" "gemini_enterprise_load_balancer" {
  count           = data.terraform_remote_state.stage_0.outputs.deployment_type != "none" ? 1 : 0
  project         = data.terraform_remote_state.stage_0.outputs.main_project_id
  name            = "${data.terraform_remote_state.stage_0.outputs.prefix}-gemini-enterprise-url-map"
  region          = data.terraform_remote_state.stage_0.outputs.region
  description     = "URL map for ${data.terraform_remote_state.stage_0.outputs.prefix}-gemini-enterprise"
  default_service = data.google_compute_region_backend_service.gemini_enterprise_backend[0].id

  host_rule {
    hosts        = ["${var.gemini_enterprise_domain}"]
    path_matcher = "path-matcher-1"
  }

  dynamic "path_matcher" {
    for_each = data.terraform_remote_state.stage_0.outputs.acl_idp_type == "GSUITE" ? ["gsuite"] : []
    content {
      name            = "path-matcher-1"
      default_service = data.google_compute_region_backend_service.gemini_enterprise_backend[0].id

      route_rules {
        priority = 100
        match_rules {
          prefix_match = "/"
        }
        service = data.google_compute_region_backend_service.gemini_enterprise_backend[0].id
        route_action {
          url_rewrite {
            host_rewrite        = "vertexaisearch.cloud.google.com"
            path_prefix_rewrite = "/us/home/cid/${var.gemini_config_id}?hl=en_US"
          }
        }
      }
    }
  }

  dynamic "path_matcher" {
    for_each = data.terraform_remote_state.stage_0.outputs.acl_idp_type == "THIRD_PARTY" ? ["third_party"] : []
    content {
      name = "path-matcher-1"
      default_url_redirect {
        https_redirect         = true
        host_redirect          = "auth.cloud.google"
        path_redirect          = "/signin/${data.terraform_remote_state.stage_0.outputs.acl_workforce_pool_name}/providers/${data.terraform_remote_state.stage_0.outputs.acl_workforce_provider_id}?continueUrl=https%3A%2F%2Fvertexaisearch.cloud.google%2Fus%2Fhome%2Fcid%2F${var.gemini_config_id}&hl=en_US"
        redirect_response_code = "FOUND"
        strip_query            = false
      }
    }
  }
}

# Certificate Manager Certificate for Google Managed Option
resource "google_certificate_manager_certificate" "gemini_enterprise_managed_cert" {
  count       = data.terraform_remote_state.stage_0.outputs.deployment_type != "none" && var.cert_management_choice == "google_managed" ? 1 : 0
  name        = "${data.terraform_remote_state.stage_0.outputs.prefix}-managed-cert"
  description = "Google-managed certificate for Gemini Enterprise"
  location    = data.terraform_remote_state.stage_0.outputs.region
  project     = data.terraform_remote_state.stage_0.outputs.main_project_id
  managed {
    domains = [var.gemini_enterprise_domain]
    dns_authorizations = [
      "projects/${data.terraform_remote_state.stage_0.outputs.main_project_id}/locations/${data.terraform_remote_state.stage_0.outputs.region}/dnsAuthorizations/${data.terraform_remote_state.stage_0.outputs.prefix}-dns-auth"
    ]
  }
}

# This resource creates the target HTTPS proxy for the load balancer.
resource "google_compute_region_target_https_proxy" "gemini_enterprise_https_proxy" {
  count            = data.terraform_remote_state.stage_0.outputs.deployment_type != "none" ? 1 : 0
  project          = data.terraform_remote_state.stage_0.outputs.main_project_id
  name             = "${data.terraform_remote_state.stage_0.outputs.prefix}-gemini-enterprise-https-proxy"
  region           = data.terraform_remote_state.stage_0.outputs.region
  url_map          = google_compute_region_url_map.gemini_enterprise_load_balancer[0].id
  
  ssl_certificates = var.cert_management_choice == "self_managed" ? [data.google_compute_region_ssl_certificate.gemini_enterprise_cert[0].self_link] : []
  certificate_manager_certificates = var.cert_management_choice == "google_managed" ? [google_certificate_manager_certificate.gemini_enterprise_managed_cert[0].id] : []
}

# This resource creates the forwarding rule for the load balancer.
resource "google_compute_forwarding_rule" "gemini_enterprise_forwarding_rule" {
  count                 = data.terraform_remote_state.stage_0.outputs.deployment_type != "none" ? 1 : 0
  project               = data.terraform_remote_state.stage_0.outputs.main_project_id
  name                  = "${data.terraform_remote_state.stage_0.outputs.prefix}-gemini-enterprise-forwarding-rule"
  region                = data.terraform_remote_state.stage_0.outputs.region
  ip_protocol           = "TCP"
  port_range            = "443"
  load_balancing_scheme = local.load_balancing_scheme
  network               = data.google_compute_network.gemini_enterprise_vpc[0].self_link
  subnetwork            = data.terraform_remote_state.stage_0.outputs.deployment_type == "internal" ? data.google_compute_subnetwork.gemini_enterprise_vpc_subnet[0].self_link : null
  ip_address            = data.google_compute_address.gemini_enterprise_ip[0].address
  target                = google_compute_region_target_https_proxy.gemini_enterprise_https_proxy[0].id
}

# Data source to get the subnet created in stage-0
data "google_compute_subnetwork" "gemini_enterprise_vpc_subnet" {
  count   = data.terraform_remote_state.stage_0.outputs.deployment_type == "internal" ? 1 : 0
  project = data.terraform_remote_state.stage_0.outputs.main_project_id
  name    = "gemini-enterprise-vpc-subnet"
  region  = data.terraform_remote_state.stage_0.outputs.region
}

# --- IAP Access Roles ---
# Grant a user or group access through IAP.
resource "google_iap_web_region_backend_service_iam_member" "iap_admin" {
  count                      = data.terraform_remote_state.stage_0.outputs.deployment_type != "none" ? 1 : 0
  project                    = data.terraform_remote_state.stage_0.outputs.main_project_id
  region                     = data.terraform_remote_state.stage_0.outputs.region
  web_region_backend_service = data.google_compute_region_backend_service.gemini_enterprise_backend[0].name
  role                       = "roles/iap.httpsResourceAccessor"
  member                     = data.terraform_remote_state.stage_0.outputs.admin_group
  condition {
    title       = "Admin Access"
    description = data.terraform_remote_state.stage_0.outputs.enable_chrome_enterprise_premium ? "Access for Admins with Strict Device Policy" : "Access for Admins with Moderate Policy"
    expression  = data.terraform_remote_state.stage_0.outputs.enable_chrome_enterprise_premium ? format("\"accessPolicies/%s/accessLevels/strict_device\" in request.auth.access_levels", data.terraform_remote_state.stage_0.outputs.access_policy_number) : format("\"accessPolicies/%s/accessLevels/moderate_device\" in request.auth.access_levels", data.terraform_remote_state.stage_0.outputs.access_policy_number)
  }
}

resource "google_iap_web_region_backend_service_iam_member" "iap_user" {
  for_each                   = data.terraform_remote_state.stage_0.outputs.deployment_type != "none" ? toset(data.terraform_remote_state.stage_0.outputs.user_groups) : toset([])
  project                    = data.terraform_remote_state.stage_0.outputs.main_project_id
  region                     = data.terraform_remote_state.stage_0.outputs.region
  web_region_backend_service = data.google_compute_region_backend_service.gemini_enterprise_backend[0].name
  role                       = "roles/iap.httpsResourceAccessor"
  member                     = each.value
  condition {
    title       = "User Access"
    description = data.terraform_remote_state.stage_0.outputs.enable_chrome_enterprise_premium ? "Access for Users with Moderate Device Policy" : "Access for Users with Basic Policy"
    expression  = data.terraform_remote_state.stage_0.outputs.enable_chrome_enterprise_premium ? format("\"accessPolicies/%s/accessLevels/moderate_device\" in request.auth.access_levels", data.terraform_remote_state.stage_0.outputs.access_policy_number) : format("\"accessPolicies/%s/accessLevels/lenient_device\" in request.auth.access_levels", data.terraform_remote_state.stage_0.outputs.access_policy_number)
  }
}