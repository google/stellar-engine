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
  # tflint-ignore: terraform_unused_declarations
  nva_zones   = { for k, v in var.regions : k => slice(data.google_compute_zones.available[k].names, 0, 2) }
  cidr_ranges = yamldecode(file("${path.module}/data/cidrs.yaml"))
}

data "google_storage_project_service_account" "gcs_account" {
  project    = module.vdss-host-project.project_id
  depends_on = [module.vdss-host-project]
}

data "google_compute_image" "vmseries" {
  filter      = "name=vmseries-flex-byol-1120 AND family=${var.vmseries_image}"
  most_recent = true
  project     = "paloaltonetworksgcp-public"
}

data "google_compute_zones" "available" {
  for_each = var.regions
  region   = each.value
  project  = module.vdss-host-project.project_id
  status   = "UP"

  depends_on = [module.vdss-host-project]
}

resource "tls_private_key" "ngfw-ssh" {
  algorithm = "RSA"
  rsa_bits  = "4096"
}

# Shell out to openssl to get the password hash
resource "random_password" "password" {
  length           = 16
  special          = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
}

# Shell out to openssl to get the password hash
resource "random_password" "salt" {
  length  = 8
  special = false
}

resource "google_project_iam_custom_role" "ngfw-custom-role" {
  role_id = "ngfw.appliance"
  title   = "NGFW Appliance"
  project = module.vdss-host-project.project_id

  description = "Many of the permissions required for the Palo Alto NGFW, not including compute.viewer"
  permissions = [
    "storage.buckets.get",
    "logging.buckets.write",
    "opsconfigmonitoring.resourceMetadata.write",
    "autoscaling.sites.writeMetrics",
    "monitoring.metricDescriptors.create",
    "monitoring.metricDescriptors.get",
    "monitoring.metricDescriptors.list",
    "monitoring.monitoredResourceDescriptors.get",
    "monitoring.monitoredResourceDescriptors.list",
    "monitoring.timeSeries.create",
  ]
}

module "ngfw-service-account" {
  name       = "ngfw-compute"
  source     = "../../../modules/iam-service-account"
  project_id = module.vdss-host-project.project_id
  iam_project_roles = {
    (module.vdss-host-project.project_id) = [
      "projects/${module.vdss-host-project.project_id}/roles/ngfw.appliance",
      "roles/compute.viewer"
    ]
  }
  depends_on = [module.vdss-host-project, google_project_iam_custom_role.ngfw-custom-role]
}

data "external" "openssl" {
  program = ["bash", "${path.module}/openssl-helper.sh"]
  query = {
    # arbitrary map from strings to strings, passed
    # to the external program as the data query.
    algo      = "5"
    salt      = random_password.salt.result
    plaintext = random_password.password.result
  }
}

# Google Cloud Storage Module
module "ngfw-bootstrap-bucket" {
  source         = "../../../modules/gcs"
  for_each       = var.regions
  prefix         = var.prefix
  project_id     = module.vdss-host-project.project_id
  encryption_key = module.kms.keys.default.id
  storage_class  = "REGIONAL"
  name           = "ngfw-bootstrap-${each.value}"
  location       = upper(each.value)
  depends_on     = [module.kms]
}

resource "google_storage_bucket_iam_binding" "binding" {
  bucket   = module.ngfw-bootstrap-bucket[each.key].name
  for_each = var.regions
  role     = "roles/storage.objectUser"
  members = [
    "serviceAccount:service-${module.vdss-host-project.number}@compute-system.iam.gserviceaccount.com",
    module.ngfw-service-account.service_account.member
  ]
}

# I don't think we need this anymore, but who knows
# resource "time_sleep" "wait_180_seconds" {
#   depends_on = [module.vdss-host-project]
#   create_duration = "180s"
# }

resource "google_storage_bucket_object" "config_folders" {
  for_each = var.regions
  name     = "config/"
  bucket   = module.ngfw-bootstrap-bucket[each.key].name
  content  = " "
}

resource "google_storage_bucket_object" "content_folders" {
  for_each = var.regions
  name     = "content/"
  bucket   = module.ngfw-bootstrap-bucket[each.key].name
  content  = " "
}

resource "google_storage_bucket_object" "software_folders" {
  for_each = var.regions
  name     = "software/"
  bucket   = module.ngfw-bootstrap-bucket[each.key].name
  content  = " "
}

resource "google_storage_bucket_object" "license_folders" {
  for_each = var.regions
  name     = "license/"
  bucket   = module.ngfw-bootstrap-bucket[each.key].name
  content  = " "
}

resource "google_storage_bucket_object" "bootstrap-xml" {
  name     = "config/bootstrap.xml"
  for_each = var.regions
  content = templatefile("./templates/bootstrap.xml.tpl", {
    password_hash     = data.external.openssl.result.hash
    ssh_pubkey        = tls_private_key.ngfw-ssh.public_key_openssh
    healthcheck_cidrs = local.cidr_ranges["healthchecks"]
    iap_cidrs         = local.cidr_ranges["iap"]
    tenants_subnets = { for k, v in var.envs_folders : k => module.env-spoke-vpc[k].subnets[
      "${var.regions.primary}/${[for s in try(var.subnets[lower(k)], []) : s.name if s.tenant != null][0]}"
    ].ip_cidr_range }
    lz_gateway_ip = module.vdss-vpc.subnets["us-east4/landing-default"].gateway_address # This doesn't support dual region yet

  })
  bucket = module.ngfw-bootstrap-bucket[each.key].name
}

resource "google_storage_bucket_object" "init-cfg" {
  name     = "config/init-cfg.txt"
  for_each = var.regions

  content = templatefile("./templates/init-cfg.txt.tpl", {
    op-command-modes = "mgmt-interface-swap"
  })
  bucket = module.ngfw-bootstrap-bucket[each.key].name
}

resource "google_compute_region_instance_template" "ngfw-template" {
  for_each = var.regions
  project  = module.vdss-host-project.project_id

  name_prefix = "ngfw-template-${each.key}-"
  description = "This template is used to create and configure Palo Alto NGFW instances."

  tags           = ["nva"]
  region         = var.regions["primary"]
  machine_type   = "n2d-standard-4"
  can_ip_forward = true

  scheduling {
    automatic_restart   = true
    on_host_maintenance = "MIGRATE"
  }

  // Create a new boot disk from an image
  disk {
    source_image = data.google_compute_image.vmseries.id
    disk_size_gb = 60
    type         = "PERSISTENT"
    disk_encryption_key {
      kms_key_self_link = module.kms.keys.default.id
    }
  }

  network_interface {
    network    = module.dmz-vpc.self_link
    subnetwork = try(module.dmz-vpc.subnet_self_links["${each.value}/dmz-default"], null)
  }

  network_interface {
    network = module.mgmt-vpc.self_link
    subnetwork = try(
      module.mgmt-vpc.subnet_self_links["${each.value}/mgmt-default"], null
    )
  }
  network_interface {
    network    = module.vdss-vpc.self_link
    subnetwork = try(module.vdss-vpc.subnet_self_links["${each.value}/landing-default"], null)
  }

  metadata = {
    mgmt-interface-swap                  = "enable"
    type                                 = "dhcp-client"
    op-command-modes                     = "mgmt-interface-swap"
    dhcp-accept-server-domain            = "yes"
    dhcp-accept-server-hostname          = "yes"
    ssh-keys                             = "admin:${tls_private_key.ngfw-ssh.public_key_openssh}"
    serial-port-enable                   = true
    serial-port-logging-enable           = true
    vmseries-bootstrap-gce-storagebucket = module.ngfw-bootstrap-bucket[each.key].name
    bootstrap-xml-md5                    = google_storage_bucket_object.bootstrap-xml[each.key].md5hash # Roll out a new template when our bootstrap.xml file changes
  }

  service_account {
    # Google recommends custom service accounts that have cloud-platform scope and permissions granted via IAM Roles.
    email  = module.ngfw-service-account.email
    scopes = ["cloud-platform"]
  }
  # CIS Compliance Benchmark 4.11
  # Palo Alto VM images aren't UEFI and can't secureboot
  # confidential_instance_config {
  #   enable_confidential_compute = true
  # }
  # shielded_instance_config {
  #   enable_secure_boot          = true
  #   enable_vtpm                 = true
  #   enable_integrity_monitoring = true
  # }
  lifecycle {
    create_before_destroy = true
  }
}

module "ngfw-mig" {
  for_each   = var.regions
  source     = "../../../modules/compute-mig"
  project_id = module.vdss-host-project.project_id
  location   = each.value
  name       = "nva-ngfw-${each.key}"
  distribution_policy = {
    target_shape = "EVEN"
    zones        = local.nva_zones[each.key]
  }

  instance_template = google_compute_region_instance_template.ngfw-template[each.key].self_link
  target_size       = 2
  auto_healing_policies = {
    initial_delay_sec = 900
  }
  health_check_config = {
    tcp = {
      port = 22
    }
  }
  update_policy = {
    minimal_action = "REPLACE"
    type           = "PROACTIVE"
    min_ready_sec  = 300
    max_surge = {
      fixed = length(local.nva_zones[each.key])
    }
    max_unavailable = {
      fixed = 0
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
    for k, v in module.ngfw-mig :
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
    for k, v in module.ngfw-mig :
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
      module.vdss-host-project.service_agents.compute.iam_email,
      "serviceAccount:${data.google_storage_project_service_account.gcs_account.email_address}"
    ]
  }
  keyring = {
    location = var.regions.primary
    name     = "vdss-keyring"
  }
}
