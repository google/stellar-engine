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
  project = "my-project"
}

run "plan_cis_log_metrics" {
  command = plan

  assert {
    condition     = length(google_logging_metric.logging_metric) == 8
    error_message = "Expected all eight CIS log metrics to be planned."
  }

  assert {
    condition     = google_logging_metric.logging_metric["project-owner-log"].project == "my-project"
    error_message = "Expected CIS log metrics to target var.project."
  }
}
