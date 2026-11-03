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

module "service-account-notebook" {
  source     = "../../../modules/iam-service-account"
  project_id = module.project.project_id
  name       = "notebook-sa"
}

resource "google_workbench_instance" "playground" {
  for_each = var.notebooks
  name     = "${local.prefix}${each.key}"
  location = "${var.region}-b"
  project  = module.project.project_id

  gce_setup {
    machine_type      = var.notebooks[each.key].machine_type
    disable_public_ip = var.notebooks[each.key].internal_ip_only

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

    data_disks {
      disk_size_gb    = 100
      disk_type       = "PD_STANDARD"
      disk_encryption = var.service_encryption_keys.notebooks != null ? "CMEK" : null
      kms_key         = var.service_encryption_keys.notebooks
    }

    shielded_instance_config {
      enable_secure_boot          = true
      enable_vtpm                 = true
      enable_integrity_monitoring = true
    }

    metadata = {
      notebook-disable-downloads = "true"
      notebook-disable-root      = "true"
    }

    network_interfaces {
      network = local.vpc
      subnet  = local.subnet
    }

    service_accounts {
      email = module.service-account-notebook.email
    }
  }

  disable_proxy_access = false

  instance_owners = var.notebooks[each.key].owner == null ? null : [var.notebooks[each.key].owner]

  depends_on = [
    google_project_iam_member.shared_vpc,
  ]
}