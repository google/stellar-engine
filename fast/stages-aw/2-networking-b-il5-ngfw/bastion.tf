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
  confidential_compute = true # CIS Compliance Benchmark 4.11 - Must use compliant instance and image types
  shielded_config = {
    enable_secure_boot          = true
    enable_vtpm                 = true
    enable_integrity_monitoring = true
  }
  tags          = ["bastion"]
  instance_type = "n2d-highcpu-2"
  network_interfaces = [{
    network = module.mgmt-vpc.self_link
    subnetwork = try(
      module.mgmt-vpc.subnet_self_links["${var.regions["primary"]}/mgmt-default"], null
    )
  }]
  encryption = {
    kms_key_self_link = module.kms.keys.default.id
  }
  attached_disks = [
    {
      auto_delete = true
      size        = 10
      name        = "data-disk"
      initialize_params = {
        image = "projects/cos-cloud/global/images/family/cos-stable"
      }
      kms_key_self_link = module.kms.keys.default.id
    }
  ]

  boot_disk = {
    initialize_params = {
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

module "ngfw-ssh-secrets" {
  source     = "../../../modules/secret-manager"
  project_id = module.vdss-host-project.project_id
  secrets = {
    ngfw-ssh-private-key = {
      locations = [var.regions.primary]
      keys = {
        (var.regions.primary) = module.kms.keys.default.id
      }
    }
    ngfw-ssh-public-key = {
      locations = [var.regions.primary]
      keys = {
        (var.regions.primary) = module.kms.keys.default.id
      }
    }
  }
  versions = {
    ngfw-ssh-private-key = {
      latest = {
        enabled = true
        data    = tls_private_key.ngfw-ssh.private_key_openssh
      }
    }
    ngfw-ssh-public-key = {
      latest = {
        enabled = true
        data    = tls_private_key.ngfw-ssh.public_key_openssh
      }
    }
  }
  iam = {
    ngfw-ssh-private-key = {
      "roles/secretmanager.secretAccessor" = [
        module.bastion-service-account.iam_email
      ]
    }
    ngfw-ssh-public-key = {
      "roles/secretmanager.secretAccessor" = [
        module.bastion-service-account.iam_email
      ]
    }
  }
  depends_on = [module.kms]
}
