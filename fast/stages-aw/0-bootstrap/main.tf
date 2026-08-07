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
  principals = {
    for k, v in var.groups : k => (
      can(regex("^[a-zA-Z]+:", v))
      ? v
      : "group:${v}@${var.organization.domain}"
    )
  }
  locations = {
    bq      = var.regions.primary
    gcs     = var.regions.primary
    logging = coalesce(try(local.checklist.location, null), var.regions.primary)
    pubsub  = [var.regions.primary]
    kms     = var.regions.primary
  }
  # naming: environment used in most resource names
  prefix               = join("-", compact([var.prefix, "prod"]))
  kms_protection_level = coalesce(var.kms_protection_level, var.assured_workloads.regime == "FEDRAMP_MODERATE" ? "SOFTWARE" : "HSM")
  assured_workloads_folder = (
    var.assured_workloads.regime != "COMPLIANCE_REGIME_UNSPECIFIED"
    ? format("folders/%s", try(
      coalesce(
        one([
          for r in try(google_assured_workloads_workload.primary[0].resources, []) :
          tostring(r.resource_id) if r.resource_type == "CONSUMER_FOLDER"
        ]),
        try(tostring(google_assured_workloads_workload.primary[0].resources[0].resource_id), null)
      ),
      ""
    ))
    : try(module.no-compliance-folder[0].id, null)
  )
}
