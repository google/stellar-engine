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

# CIS Compliance Benchmark 2.4
# CIS Compliance Benchmark 2.5
# CIS Compliance Benchmark 2.6
# CIS Compliance Benchmark 2.7
# CIS Compliance Benchmark 2.8
# CIS Compliance Benchmark 2.9
# CIS Compliance Benchmark 2.10
# CIS Compliance Benchmark 2.11

moved {
  from = module.core_log_metrics
  to   = module.core-log-metrics
}

module "core-log-metrics" {
  source = "../../../modules/cis-log-metrics"

  for_each = module.tenant-self-iac-projects
  project  = module.tenant-self-iac-projects[each.key].id
}

moved {
  from = module.main_log_metrics
  to   = module.main-log-metrics
}

module "main-log-metrics" {
  source = "../../../modules/cis-log-metrics"

  for_each = module.tenant-self-main-projects
  project  = module.tenant-self-main-projects[each.key].id
}

# Alerts require log-metrics to be configure
resource "time_sleep" "resman_wait_10_seconds" {
  depends_on      = [module.core-log-metrics, module.main-log-metrics]
  create_duration = "10s"
}

moved {
  from = module.core_log_alerts
  to   = module.core-log-alerts
}

module "core-log-alerts" {
  source = "../../../modules/cis-log-alerts"

  for_each = module.tenant-self-iac-projects

  project            = module.tenant-self-iac-projects[each.key].id
  combiner           = "OR"
  duration           = "0s"
  comparison         = "COMPARISON_GT"
  alignment_period   = "60s"
  per_series_aligner = "ALIGN_RATE"
  alert_email        = var.alert_email

  depends_on = [time_sleep.resman_wait_10_seconds]
}

moved {
  from = module.main_log_alerts
  to   = module.main-log-alerts
}

module "main-log-alerts" {
  source = "../../../modules/cis-log-alerts"

  for_each = module.tenant-self-main-projects

  project            = module.tenant-self-main-projects[each.key].id
  combiner           = "OR"
  duration           = "0s"
  comparison         = "COMPARISON_GT"
  alignment_period   = "60s"
  per_series_aligner = "ALIGN_RATE"
  alert_email        = var.alert_email

  depends_on = [time_sleep.resman_wait_10_seconds]
}