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

locals {
  alert_filters = {
    project-owner-log     = "metric.type=\"logging.googleapis.com/user/project-owner-log\" AND resource.type=\"global\""
    audit-config-change   = "metric.type=\"logging.googleapis.com/user/audit-config-change\" AND resource.type=\"global\""
    custom-role-change    = "metric.type=\"logging.googleapis.com/user/custom-role-change\" AND resource.type=\"global\""
    vpc-firewall-change   = "metric.type=\"logging.googleapis.com/user/vpc-firewall-change\" AND resource.type=\"global\""
    vpc-route-change      = "metric.type=\"logging.googleapis.com/user/vpc-route-change\" AND resource.type=\"global\""
    vpc-networking-change = "metric.type=\"logging.googleapis.com/user/vpc-network-change\" AND resource.type=\"gce_network\""
    storage-iam-change    = "metric.type=\"logging.googleapis.com/user/storage-iam-change\" AND resource.type=\"gcs_bucket\""
    sql-config-change     = "metric.type=\"logging.googleapis.com/user/sql-config-change\" AND resource.type=\"global\""
  }
}

resource "google_monitoring_notification_channel" "email" {
  project      = var.project
  display_name = "Log Alert Email"
  type         = "email"
  labels = {
    email_address = var.alert_email
  }
}

resource "google_monitoring_alert_policy" "alert_policy" {
  for_each = local.alert_filters
  project  = var.project

  # notification_channels = var.notification_channels
  notification_channels = [google_monitoring_notification_channel.email.name]
  display_name          = each.key
  combiner              = var.combiner
  conditions {
    display_name = "each.key"
    condition_threshold {
      filter     = each.value
      duration   = var.duration
      comparison = var.comparison
      aggregations {
        alignment_period   = var.alignment_period
        per_series_aligner = var.per_series_aligner
      }
    }
  }
}