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
module "service-account-notebook" {
  source     = "../../../modules/iam-service-account"
  project_id = var.main_project_id
  name       = "notebook-sa"
}

resource "google_workbench_instance" "playground" {
  for_each = var.notebooks
  name     = "${local.prefix}${each.key}"
  location = "${var.region}-b"
  project  = var.main_project_id

  gce_setup {
    machine_type      = var.notebooks[each.key].machine_type
    disable_public_ip = var.notebooks[each.key].internal_ip_only

    service_accounts {
      email = module.service-account-notebook.email
    }

    container_image {
      repository = "gcr.io/deeplearning-platform-release/base-cpu"
      tag        = "latest"
    }

    boot_disk {
      disk_size_gb    = 200
      disk_type       = "PD_SSD"
      disk_encryption = var.service_encryption_keys.notebooks != null ? "CMEK" : null
      kms_key         = var.service_encryption_keys.notebooks
    }

    network_interfaces {
      network = local.vpc
      subnet  = local.subnet
    }
  }

  disable_proxy_access = false

  instance_owners = try(tolist(var.notebooks[each.key].owner), null)

  labels = var.labels

  depends_on = [
    google_project_iam_member.shared_vpc,
    google_kms_crypto_key_iam_member.notebooks_kms,
    google_kms_crypto_key_iam_member.compute_kms,
  ]
}

resource "google_project_iam_member" "notebook_permissions" {
  for_each = toset([
    "roles/notebooks.runner",
    "roles/aiplatform.user",
    "roles/storage.objectViewer",
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter",
  ])
  project = var.main_project_id
  role    = each.key
  member  = "serviceAccount:${module.service-account-notebook.email}"
}

resource "google_service_account_iam_member" "notebook_acts_as_mlops" {
  service_account_id = module.service-account-mlops.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${module.service-account-notebook.email}"
}
