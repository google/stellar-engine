/**
 * Copyright 2022 Google LLC
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
  gcs_storage_class = (
    length(split("-", local.locations.gcs)) < 2
    ? "MULTI_REGIONAL"
    : "REGIONAL"
  )
  locations = {
    gcs = var.locations.gcs
    kms = var.locations.kms
  }
  # naming: environment used in most resource names
  prefix = join("-", compact([var.prefix, "prod"]))
}

resource "google_project_service" "project_services" {
  for_each           = var.services
  project            = var.core_project_id
  service            = each.value
  disable_on_destroy = false
}