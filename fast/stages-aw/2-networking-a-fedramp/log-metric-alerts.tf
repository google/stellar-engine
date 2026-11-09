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

# CIS Compliance Benchmark 2.4 - 2.11

moved {
  from = module.vdss_log_metrics
  to   = module.vdss-log-metrics
}

moved {
  from = module.vdss-log-metrics
  to   = module.landing-log-metrics
}

module "landing-log-metrics" {
  source  = "../../../modules/cis-log-metrics"
  project = module.landing-project.id
}

moved {
  from = module.spoke_log_metrics
  to   = module.spoke-log-metrics
}

module "spoke-log-metrics" {
  source   = "../../../modules/cis-log-metrics"
  for_each = module.env-spoke-projects
  project  = module.env-spoke-projects[each.key].id
}

# Alerts require log metrics to be configured first.
resource "time_sleep" "networking_wait_10_seconds" {
  depends_on      = [module.landing-log-metrics, module.spoke-log-metrics]
  create_duration = "10s"
}

moved {
  from = module.vdss_log_alerts
  to   = module.vdss-log-alerts
}

moved {
  from = module.vdss-log-alerts
  to   = module.landing-log-alerts
}

module "landing-log-alerts" {
  source = "../../../modules/cis-log-alerts"

  project            = module.landing-project.id
  combiner           = "OR"
  duration           = "0s"
  comparison         = "COMPARISON_GT"
  alignment_period   = "60s"
  per_series_aligner = "ALIGN_RATE"
  alert_email        = var.alert_email

  depends_on = [time_sleep.networking_wait_10_seconds]
}

moved {
  from = module.spoke_log_alerts
  to   = module.spoke-log-alerts
}

module "spoke-log-alerts" {
  source = "../../../modules/cis-log-alerts"

  for_each = module.env-spoke-projects
  project  = module.env-spoke-projects[each.key].id

  combiner           = "OR"
  duration           = "0s"
  comparison         = "COMPARISON_GT"
  alignment_period   = "60s"
  per_series_aligner = "ALIGN_RATE"
  alert_email        = var.alert_email

  depends_on = [time_sleep.networking_wait_10_seconds]
}
