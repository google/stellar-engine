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
# tfdoc:file:description Tenant logging sinks for organization-level log routing.

# Data source to get bootstrap stage outputs
# data "terraform_remote_state" "bootstrap" {
#   backend = "gcs"
#   config = {
#     bucket = var.automation.outputs_bucket
#     prefix = "terraform/bootstrap/state"
#   }
# }

locals {
  tenant_log_buckets = {
    for loc in toset(var.locations.logging) :
    "${var.prefix}-${var.tenant.name}-audit-logs-${loc}" => {
      tenant      = var.tenant.name
      filter      = "" # Empty filter captures all logs for the tenant
      location    = loc
      description = "Centralized audit logs for tenant ${var.tenant.name} - captures all activity including admin, data access, system events, security events, and policy violations"
    }
  }

  tenant_pubsub_topics = {
    for loc in toset(var.locations.pubsub) :
    "${var.prefix}-${var.tenant.name}-tier-1-${loc}" => {
      tenant      = var.tenant.name
      filter      = ""
      location    = loc
      description = "Centralized audit pubsub topic for tenant ${var.tenant.name} - captures all activity including admin, data access, system events, security events, and policy violations"
    }
  }

  log_sink_filter = flatten([
    for folder_id in lookup(local.tenant_folder_mapping, var.tenant.name, []) : [
      # Complete folder capture
      "(resource.type=\"folder\" AND resource.labels.folder_id=\"${replace(folder_id, "folders/", "")}\")",
      "(protoPayload.resourceName:\"${folder_id}\" OR protoPayload.resourceName:\"${folder_id}/*\")",

      # Complete project capture under tenant folders
      "(resource.type=\"project\" AND resource.labels.parent_id=\"${replace(folder_id, "folders/", "")}\")",

      # All tenant project activities
      "(resource.labels.project_id:\"${var.prefix}-${var.tenant.name}-*\")",
      "(protoPayload.resourceName:\"projects/${var.prefix}-${var.tenant.name}-*\")",
      "(protoPayload.resourceName:\"projects/${var.prefix}-${var.tenant.name}-*/*\")"
    ]
  ])

  pubsub_log_tier_filters = {
    tier_1 = join(" OR ", [
      "protoPayload.serviceName=\"cloudaudit.googleapis.com\"",
      "resource.type=\"gce_subnetwork\" AND logName:\"logs/compute.googleapis.com%2Fvpc_flows\""
    ])
  }

  # Create mapping of tenant names to their folder IDs
  tenant_folder_mapping = {
    for k, v in local.tenant_envs : v.tenant => module.tenant-top-folders.id...
  }

  tenant_log_bucket_sink = {
    for bucket, config in local.tenant_log_buckets : bucket => {
      bq_partitioned_table = false
      destination          = module.tenant-log-buckets[bucket].id
      filter               = join(" OR ", local.log_sink_filter)
      include_children     = true
      type                 = "logging"
    }
  }

  tenant_pubsub_sink = {
    for pubsub, config in local.tenant_pubsub_topics : pubsub => {
      bq_partitioned_table = false
      destination          = module.tenant-pubsub-topic[pubsub].id
      filter               = local.pubsub_log_tier_filters.tier_1
      include_children     = true
      type                 = "pubsub"
    }
  }

  tenant_log_sinks = merge(
    local.tenant_log_bucket_sink,
    local.tenant_pubsub_sink
  )
}

module "tenant-log-buckets" {
  source        = "../../../modules/logging-bucket"
  for_each      = local.tenant_log_buckets
  name          = "${each.key}-log-bucket"
  parent_type   = "project"
  parent        = var.logging.project_id
  location      = each.value.location
  retention     = 30
  description   = each.value.description
  log_analytics = { enable = true }
  kms_key_name  = "projects/${var.logging.project_id}/locations/${each.value.location}/keyRings/logging-${each.value.location}/cryptoKeys/log-sink"
}

module "tenant-pubsub-topic" {
  source     = "../../../modules/pubsub"
  for_each   = local.tenant_pubsub_topics
  project_id = var.logging.project_id
  name       = "${each.key}-pubsub-topic"
  regions    = [each.value.location]
  kms_key    = "projects/${var.logging.project_id}/locations/${local.primary_location_pubsub}/keyRings/logging-${local.primary_location_pubsub}/cryptoKeys/pubsub"
  iam_bindings_additive = {
    "roles/pubsub.subscriber" = {
      role   = "roles/pubsub.subscriber"
      member = "serviceAccount:${var.logging.service_accounts.c5isr-pubsub}"
    }
  }
  subscriptions = {
    "${each.key}-pull-sub" = {
      message_retention_duration = "604800s"
      expiration_policy_ttl      = ""
      ack_deadline_seconds       = 60
    }
  }
  depends_on = [
    module.tenant-project-keys
  ]
}
