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
  # routing_config should be aligned to the NVA network interfaces - i.e.
  # local.routing_config[0] sets up the first interface, and so on.
  routing_config = [
    {
      name                = "dmz"
      enable_masquerading = true
      routes = [
        var.gcp_ranges.gcp_dmz_primary,
      ]
    },
    {
      name = "landing"
      routes = [for k, v in var.envs_folders : module.env-spoke-vpc[k].subnets[
        "${var.regions.primary}/${[for s in try(var.subnets[lower(k)], []) : s.name if s.tenant != null][0]}"
      ].ip_cidr_range]
    },
  ]
}

# Custom service account with compute engine role
resource "google_service_account" "compute" {
  account_id = "nva-sa"
  project    = module.vdss-host-project.project_id
}


# NVA config
module "nva-cloud-config" {
  source               = "../../../modules/cloud-config-container/simple-nva"
  enable_health_checks = true
  network_interfaces   = local.routing_config
}

module "nva-template" {
  for_each        = var.regions
  source          = "../../../modules/compute-vm"
  project_id      = module.vdss-host-project.project_id
  name            = "nva-template-${each.key}"
  zone            = "${each.value}-b"
  instance_type   = "n2d-standard-2"
  tags            = ["nva"]
  create_template = true
  can_ip_forward  = true
  network_interfaces = [
    {
      network    = module.dmz-vpc.self_link
      subnetwork = try(module.dmz-vpc.subnet_self_links["${each.value}/dmz-default"], null)
      nat        = false
      addresses  = null
    },
    {
      network    = module.vdss-vpc.self_link
      subnetwork = try(module.vdss-vpc.subnet_self_links["${each.value}/landing-default"], null)
      nat        = false
      addresses  = null
    }
  ]
  boot_disk = {
    initialize_params = {
      image = "cos-cloud/cos-stable"
    }
  }
  options = {
    allow_stopping_for_update = true
    deletion_protection       = false
    spot                      = true
    termination_action        = "STOP"
  }
  metadata = {
    user-data              = module.nva-cloud-config.cloud_config
    block-project-ssh-keys = true # CIS Compliance Benchmark 4.3
  }

  # CIS Compliance Benchmark 4.1
  # CIS Compliance Benchmark 4.2
  service_account = {
    email = google_service_account.compute.email
  }

  # CIS Compliance Benchmark 4.11
  confidential_compute = true
  shielded_config = {
    enable_secure_boot          = true
    enable_vtpm                 = true
    enable_integrity_monitoring = true
  }
  depends_on = [module.vdss-vpc, module.dmz-vpc]
}

module "nva-mig" {
  for_each          = var.regions
  source            = "../../../modules/compute-mig"
  project_id        = module.vdss-host-project.project_id
  location          = each.value
  name              = "nva-${each.key}"
  instance_template = module.nva-template[each.key].template.self_link
  target_size       = 2
  auto_healing_policies = {
    initial_delay_sec = 30
  }
  health_check_config = {
    enable_logging = true
    tcp = {
      port = 22
    }
  }
}

module "ilb-nva-dmz" {
  for_each      = var.regions
  source        = "../../../modules/net-lb-int"
  project_id    = module.vdss-host-project.project_id
  region        = each.value
  name          = "nva-dmz-${each.key}"
  service_label = var.prefix
  forwarding_rules_config = {
    "" = {
      global_access = true
    }
  }
  vpc_config = {
    network    = module.dmz-vpc.self_link
    subnetwork = try(module.dmz-vpc.subnet_self_links["${each.value}/dmz-default"], null)
  }
  backends = [
    for k, v in module.nva-mig :
    { group = v.group_manager.instance_group }
    if startswith(k, each.key)
  ]
  health_check_config = {
    enable_logging = true
    tcp = {
      port = 22
    }
  }
}

module "ilb-nva-vdss" {
  for_each      = var.regions
  source        = "../../../modules/net-lb-int"
  project_id    = module.vdss-host-project.project_id
  region        = each.value
  name          = "nva-vdss-${each.key}"
  service_label = var.prefix
  forwarding_rules_config = {
    "" = {
      global_access = true
    }
  }
  vpc_config = {
    network    = module.vdss-vpc.self_link
    subnetwork = try(module.vdss-vpc.subnet_self_links["${each.value}/landing-default"], null)
  }
  backends = [
    for k, v in module.nva-mig :
    { group = v.group_manager.instance_group }
    if startswith(k, each.key)
  ]
  health_check_config = {
    enable_logging = true
    tcp = {
      port = 22
    }
  }
}

resource "google_compute_route" "default" {
  name         = "default-route-nva"
  project      = module.vdss-host-project.project_id
  dest_range   = "0.0.0.0/0"
  network      = module.vdss-vpc.name
  next_hop_ilb = module.ilb-nva-vdss["primary"].forwarding_rules[""].id
  priority     = 100
}

# Google KMS Module
module "kms" {
  source     = "../../../modules/kms"
  project_id = module.vdss-host-project.project_id
  keys = {
    "default" = {
      rotation_period = "7776000s" # CIS Compliance Benchmark 1.10
      purpose         = "ENCRYPT_DECRYPT"
      version_template = {
        algorithm        = "GOOGLE_SYMMETRIC_ENCRYPTION"
        protection_level = "HSM"
      }
    }
  }

  iam = {
    "roles/cloudkms.cryptoKeyEncrypterDecrypter" = [
      google_service_account.compute.member,
      module.vdss-host-project.service_agents.compute.iam_email
    ]
  }
  keyring = {
    location = var.regions.primary
    name     = "vdss-keyring"
  }

}
