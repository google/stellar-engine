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

# Google Compute Shielded VM Module
module "bastion-vm" {
  source               = "../../../modules/compute-vm"
  project_id           = module.vdss-host-project.project_id
  zone                 = "${var.regions["primary"]}-c"
  name                 = "management-bastion"
  confidential_compute = "SEV" # CIS Compliance Benchmark 4.11 - Must use compliant instance and image types
  shielded_config = {
    enable_secure_boot          = true
    enable_vtpm                 = true
    enable_integrity_monitoring = true
  }
  tags         = ["bastion"]
  machine_type = "n2d-highcpu-2"
  network_interfaces = [{
    network = module.mgmt-vpc.self_link
    subnetwork = try(
      module.mgmt-vpc.subnet_self_links["${var.regions["primary"]}/mgmt-default"], null
    )
  }]
  encryption = {
    kms_key_self_link = module.kms.keys.default.id
  }
  attached_disks = {
    data-disk = {
      auto_delete = true
      initialize_params = {
        size = 10
      }
    }
  }

  boot_disk = {
    source = {
      image = "projects/cos-cloud/global/images/family/cos-stable"
    }
  }

  service_account = {
    email = module.bastion-service-account.email
  }

  metadata = {
    block-project-ssh-keys = true # CIS Compliance Benchmark 4.3
  }

  depends_on = [module.kms]
}

module "bastion-service-account" {
  name       = "management-bastion"
  source     = "../../../modules/iam-service-account"
  project_id = module.vdss-host-project.project_id
  iam_project_roles = {
    (module.vdss-host-project.project_id) = [
      "roles/logging.logWriter",
      "roles/monitoring.metricWriter"
    ]
  }
}

# The secret-manager module rewrite in Cloud Foundation Fabric v44.2.0
# changed these state keys. The moves keep the IAM bindings in place, and
# Terraform replaces each key version once with the same data, because the
# module now sets a write-only version that older state lacks.
moved {
  from = module.ngfw-ssh-secrets.google_secret_manager_secret_version.default["ngfw-ssh-private-key:latest"]
  to   = module.ngfw-ssh-secrets.google_secret_manager_secret_version.default["ngfw-ssh-private-key/latest"]
}

moved {
  from = module.ngfw-ssh-secrets.google_secret_manager_secret_version.default["ngfw-ssh-public-key:latest"]
  to   = module.ngfw-ssh-secrets.google_secret_manager_secret_version.default["ngfw-ssh-public-key/latest"]
}

moved {
  from = module.ngfw-ssh-secrets.google_secret_manager_secret_iam_binding.default
  to   = module.ngfw-ssh-secrets.google_secret_manager_secret_iam_binding.authoritative
}

module "ngfw-ssh-secrets" {
  source     = "../../../modules/secret-manager"
  project_id = module.vdss-host-project.project_id
  secrets = {
    ngfw-ssh-private-key = {
      global_replica_locations = {
        (var.regions.primary) = module.kms.keys.default.id
      }
      iam = {
        "roles/secretmanager.secretAccessor" = [
          module.bastion-service-account.iam_email
        ]
      }
      versions = {
        latest = {
          enabled = true
          data    = tls_private_key.ngfw_ssh.private_key_openssh
          # Write-only data keeps a second copy of the key out of the secret
          # version state, as the module did before v44.2.0.
          data_config = { write_only_version = 1 }
        }
      }
    }
    ngfw-ssh-public-key = {
      global_replica_locations = {
        (var.regions.primary) = module.kms.keys.default.id
      }
      iam = {
        "roles/secretmanager.secretAccessor" = [
          module.bastion-service-account.iam_email
        ]
      }
      versions = {
        latest = {
          enabled     = true
          data        = tls_private_key.ngfw_ssh.public_key_openssh
          data_config = { write_only_version = 1 }
        }
      }
    }
  }
  depends_on = [module.kms]
}
