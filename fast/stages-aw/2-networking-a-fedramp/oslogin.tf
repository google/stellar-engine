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

# tfdoc:file:description OS Login metadata for the hub and spoke host projects.

locals {
  # Stage 0 enforces compute.requireOsLogin on the organization, or on the
  # Assured Workloads folder, for every regime except IL4 and IL5. Under that
  # constraint Compute Engine writes enable-oslogin = "true" on each new
  # project and rejects any request that removes the key, so a metadata item
  # for the same key fails on create with "already present" and can never be
  # destroyed. The stage therefore sets the key itself only where the
  # constraint is not expected, or where the regime is unknown.
  _oslogin_metadata_managed = (
    var.manage_oslogin_metadata != null
    ? var.manage_oslogin_metadata
    : (
      var.assured_workloads.regime == null ||
      contains(["IL4", "IL5"], coalesce(var.assured_workloads.regime, "-"))
    )
  )
  _oslogin_host_projects = !local._oslogin_metadata_managed ? {} : merge(
    { hub = module.hub-project.project_id },
    { for k, v in module.env-spoke-projects : lower(k) => v.project_id }
  )
}

resource "google_compute_project_metadata_item" "oslogin" {
  provider = google.billing
  for_each = local._oslogin_host_projects
  project  = each.value
  key      = "enable-oslogin"
  value    = "true" # CIS Compliance Benchmark 4.4
}

# Earlier releases set enable-oslogin through the compute_metadata argument of
# the host project modules, so existing states track the key at the module
# addresses below, either created by Terraform or imported after the
# "already present" error. Dropping the key from compute_metadata alone makes
# Terraform plan to delete it, which compute.requireOsLogin rejects and which
# disables OS Login where the constraint is absent. A removed block cannot
# target one for_each key of a resource that is still declared, so each
# tracked key first moves to an address that this stage does not declare and
# is then released from state with destroy = false. The key stays on the
# project. The spoke entries cover the default Prod, Int, and Test
# environments; see the README for other envs_folders keys.
moved {
  from = module.hub-project.google_compute_project_metadata_item.default["enable-oslogin"]
  to   = google_compute_project_metadata_item.oslogin_released["hub"]
}

moved {
  from = module.env-spoke-projects["Prod"].google_compute_project_metadata_item.default["enable-oslogin"]
  to   = google_compute_project_metadata_item.oslogin_released["prod"]
}

moved {
  from = module.env-spoke-projects["Int"].google_compute_project_metadata_item.default["enable-oslogin"]
  to   = google_compute_project_metadata_item.oslogin_released["int"]
}

moved {
  from = module.env-spoke-projects["Test"].google_compute_project_metadata_item.default["enable-oslogin"]
  to   = google_compute_project_metadata_item.oslogin_released["test"]
}

removed {
  from = google_compute_project_metadata_item.oslogin_released

  lifecycle {
    destroy = false
  }
}
