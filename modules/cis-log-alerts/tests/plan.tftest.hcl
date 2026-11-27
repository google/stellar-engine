# Copyright 2026 Google LLC
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

mock_provider "google" {}

variables {
  alert_email        = "security-alerts@example.com"
  alignment_period   = "60s"
  combiner           = "OR"
  comparison         = "COMPARISON_GT"
  duration           = "0s"
  per_series_aligner = "ALIGN_RATE"
  project            = "my-project"
}

run "plan_cis_log_alerts" {
  command = plan

  assert {
    condition     = length(google_monitoring_alert_policy.alert_policy) == 8
    error_message = "Expected all eight CIS log alert policies to be planned."
  }

  assert {
    condition     = google_monitoring_notification_channel.email.project == "my-project"
    error_message = "Expected notification channel to target var.project."
  }
}
