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


resource "google_project_service" "project_service" {
  project = var.main_project_id
  service = "iap.googleapis.com"
}

resource "google_iap_client" "project_client" {
  display_name = "CNAP Client"
  brand        = "projects/${data.google_project.project.number}/brands/${var.oauth_brand_number}"
}

resource "google_iap_web_region_backend_service_iam_binding" "binding" {
  for_each                   = local.apps
  project                    = var.main_project_id
  web_region_backend_service = module.cnap-0.backend_service_names[each.key]
  role                       = "roles/iap.httpsResourceAccessor"
  # Individual users or RBAC via groups made in Cloud Identity.
  members = each.value.members

  condition {
    title       = lookup(each.value, "condition", { "title" = "" }).title
    description = lookup(each.value, "condition", { "description" = "" }).description
    expression  = lookup(each.value, "condition", { "expression" = "" }).expression
  }
}

resource "google_project_service_identity" "iap_sa" {
  provider = google-beta

  project = var.main_project_id
  service = "iap.googleapis.com"
}

resource "google_project_iam_member" "iap_sa_cloudrun_invoker" {
  project = var.main_project_id
  role    = "roles/run.invoker"
  member  = google_project_service_identity.iap_sa.member
}