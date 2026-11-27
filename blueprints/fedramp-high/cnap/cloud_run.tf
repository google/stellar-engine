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

# These Cloud Run services are meant to represent real applications deployed behind the CNAP
# This isn't mean to imply that *only* Cloud Run applications can be hosted behind the CNAP

resource "google_project_service_identity" "cloudrun_sa" {
  provider   = google-beta
  project    = data.google_project.project.project_id
  service    = "run.googleapis.com"
  depends_on = [google_project_service.services]
}

resource "google_cloud_run_v2_service" "cloud_run_apps" {
  project  = data.google_project.project.project_id
  for_each = local.cloud_runs
  name     = "${var.prefix}-${each.key}"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER"

  template {
    encryption_key = module.kms.keys.default.id
    containers {
      image = each.value.cloud_run_image
    }
  }
  binary_authorization {
    use_default = true
  }
  depends_on = [google_project_service.services, module.kms]
}