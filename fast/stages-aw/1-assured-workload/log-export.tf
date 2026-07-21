/**
 * Copyright 2024 Google LLC
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

# tfdoc:file:description Audit log project and sink.

locals {
  # Organization and assured workload log buckets
  aw_log_buckets = {
    "${var.prefix}-${lower(replace(var.assured_workloads.regime, "_", "-"))}-logs" = {
      type        = "assured_workload"
      filter      = "" # Assured workload folder logs
      description = "Assured workload ${var.assured_workloads.regime} folder audit logs - captures compliance regime folder activities and events"
    }
    "${var.prefix}-common-services-logs" = {
      type        = "common_services"
      filter      = "" # Common services folder logs
      description = "Common Services folder audit logs - captures all activities from shared infrastructure projects (audit, automation, billing)"
    }
  }

  aw_log_buckets_redundant = merge([
    for bucket_key, bucket_val in local.aw_log_buckets : {
      for loc in local.locations.logging :
      "${bucket_key}-${loc}" => {
        name        = bucket_key
        location    = loc
        description = bucket_val.description
      }
    }
  ]...)

  pubsub_topics_tiers = [
    "tier-1",
    "tier-2",
    "tier-3"
  ]

  pubsub_tier_region_map = {
    for pair in setproduct(local.pubsub_topics_tiers, var.locations.pubsub) :
    pair[0] => {
      tier   = pair[0]
      region = pair[1]
    }
  }

  # Combine all log buckets
  all_log_buckets = merge(local.aw_log_buckets)

  # Updated log sink destinations to include all buckets
  log_sink_destinations_all = merge(
    module.aw-log-buckets
  )
  tier_1_audit_filter = "(logName:\"cloudaudit.googleapis.com\")"
  tier_1_vpc_filter   = "(resource.type=\"gce_subnetwork\" AND logName:\"logs/compute.googleapis.com%2Fvpc_flows\")"
  _tier_2_base_filter = join(" OR ", flatten([
    "resource.type=\"gce_firewall_rule\"",
    "resource.type=\"http_load_balancer\"",
    "resource.type=\"dns_query\"",
    "resource.type=\"cloud_armor_policy\"",
    "resource.type=\"networkconnectivity.googleapis.com/Hub\"",
    "resource.type=\"networkconnectivity.googleapis.com/Spoke\"",
    "logName:\"logs/networksecurity.googleapis.com%2Ffirewall_threat\"",
    "logName:\"logs/networksecurity.googleapis.com%2Ffirewall_url_filter\"",
    "logName:\"proxy\"",
    "logName:\"apache\"",
    "logName:\"nginx\"",
    "logName:\"iis\""
  ]))
  tier_2_filter = local._tier_2_base_filter
  _tier_3_base_filter = join(" OR ", flatten([
    "logName:\"logs/syslog\"",
    "logName:\"logs/auth.log\"",
    "logName:\"logs/windows.googleapis.com%2F\"",
    "logName:\"logs/application\"",
    "resource.type=\"k8s_container\"",
    "resource.type=\"k8s_node\"",
    "resource.type=\"k8s_pod\"",
    "resource.type=\"gce_instance\"",
    "logName:\"logs/gcce-agent\"",
    "logName:\"directory\""
  ]))
  tier_3_filter           = local._tier_3_base_filter
  tenant_exclusion_filter = "logName:\"${module.tenants-container-folders.folder.id}\" AND resource.labels.folder_id != \"${module.tenants-container-folders.folder.folder_id}\""
  tenant_exclusions_map = {
    "exclude_tenant_children" = local.tenant_exclusion_filter
  }
}

module "log-export-project" {
  source = "../../../modules/project"
  name   = local.project_map["log-export-project"]
  parent = coalesce(
    var.project_parent_ids.logging, module.branch-common-services-folder.folder.name
  )
  billing_account = var.billing_account.id
  contacts = (
    var.bootstrap_user != null || var.essential_contacts == null
    ? {}
    : { (var.essential_contacts) = ["ALL"] }
  )
  iam = {
    "roles/owner"  = [module.automation-tf-bootstrap-sa.iam_email, module.automation-tf-tenants-sa.iam_email]
    "roles/viewer" = [module.automation-tf-bootstrap-r-sa.iam_email]
  }
  services = [
    # "cloudresourcemanager.googleapis.com",
    # "iam.googleapis.com",
    # "serviceusage.googleapis.com",
    "bigquery.googleapis.com",
    "storage.googleapis.com",
    "stackdriver.googleapis.com",
    "cloudkms.googleapis.com",
    "pubsub.googleapis.com"
  ]
}

module "logging-c5isr-pubsub-sa" {
  source       = "../../../modules/iam-service-account"
  project_id   = module.log-export-project.project_id
  name         = "c5isr-pubsub-sa"
  display_name = "Pubsub service account for C5ISR logging."
  prefix       = local.prefix
  iam_project_roles = {
    (module.log-export-project.project_id) = [
      "roles/pubsub.viewer"
    ]
  }
}

# Organization and assured workload logging buckets
module "aw-log-buckets" {
  source        = "../../../modules/logging-bucket"
  for_each      = local.aw_log_buckets_redundant
  name          = "${each.value.name}-bucket-${each.value.location}"
  parent_type   = "project"
  parent        = module.log-export-project.project_id
  location      = each.value.location
  retention     = 365
  description   = each.value.description
  log_analytics = { enable = true }
  kms_key_name  = coalesce(var.logging_kms_key, module.logging-kms[each.value.location].keys["log-sink"].id)
}

resource "google_compute_project_metadata" "metadata-log-export" {
  project = module.log-export-project.project_id
  metadata = {
    block-project-ssh-keys = "TRUE" # CIS Compliance Benchmark 4.3
    enable-oslogin         = "TRUE" # CIS Compliance Benchmark 4.4
  }
}

resource "google_project_service_identity" "logging" {
  provider = google-beta
  project  = module.log-export-project.project_id
  service  = "logging.googleapis.com"
}

# tflint-ignore: terraform_unused_declarations
data "google_logging_project_cmek_settings" "settings" {
  project    = module.log-export-project.project_id
  depends_on = [google_project_service_identity.logging]
}

module "pubsub-topics" {
  source     = "../../../modules/pubsub"
  for_each   = local.pubsub_tier_region_map
  project_id = module.log-export-project.project_id
  name       = "${each.value.tier}-${each.value.region}-topic"
  regions    = [each.value.region]
  kms_key    = module.logging-kms[each.value.region].keys["pubsub"].id
  iam_bindings_additive = {
    "roles/pubsub.subscriber" = {
      role   = "roles/pubsub.subscriber"
      member = module.logging-c5isr-pubsub-sa.iam_email
    }
  }
  subscriptions = {
    "${each.value.tier}-${each.value.region}-sub" = {
      message_retention_duration = "604800s"
      expiration_policy_ttl      = ""
      ack_deadline_seconds       = 60
    }
  }
  depends_on = [
    module.logging-kms
  ]
}