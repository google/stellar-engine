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
  nva_zones   = { for k, v in toset([var.regions.primary]) : k => slice(data.google_compute_zones.available[k].names, 0, 2) }
  cidr_ranges = yamldecode(file("${path.module}/data/cidrs.yaml"))
  all_regions = flatten([var.regions.primary, var.regions.secondary])
  auth_code   = var.auth_code != "" ? var.auth_code : trimspace(file("${path.module}/templates/authcodes"))

  bootstrap-xml-local = {
    for reg in toset([var.regions.primary]) : reg => templatefile("${path.module}/templates/bootstrap.xml.tpl", {
      password_hash            = data.external.openssl.result.hash
      ssh_pubkey               = tls_private_key.ngfw-ssh.public_key_openssh
      healthcheck_cidrs        = local.cidr_ranges["healthchecks"]
      iap_cidrs                = local.cidr_ranges["iap"]
      lz_gateway_ip            = module.vdss-vpc.subnets["${reg}/landing-default"].gateway_address
      dmz_gateway_ip           = module.dmz-vpc.subnets["${reg}/dmz-default"].gateway_address
      tenant_gateway_ip        = module.tenant-transit-vpc.subnets["${reg}/tenant-transit"].gateway_address
      bcap_gateway_ip          = module.bcap-spoke-vpc.subnets["${reg}/bcap-landing"].gateway_address
      interconnect_gateway_ip  = module.interconnect-spoke-vpc.subnets["${reg}/interconnect-landing"].gateway_address
      lz_subnet_cidr           = module.vdss-vpc.subnets["${reg}/landing-default"].ip_cidr_range
      vdss_internal_cidr       = "10.84.0.0/14"
      elb_frontend_ip          = google_compute_address.elb_dmz_ip[reg].address
      ilb_frontend_ip          = google_compute_address.ilb_vdss_ip[reg].address
      tt_frontend_ip           = google_compute_address.ilb_tt_ip[reg].address
      bcap_frontend_ip         = google_compute_address.ilb_bcap_ip[reg].address
      interconnect_frontend_ip = google_compute_address.ilb_interconnect_ip[reg].address
    })
  }
  init-cfg-local = {
    for reg in toset([var.regions.primary]) : reg => templatefile("${path.module}/templates/init-cfg.txt.tpl", {
      op-command-modes = "mgmt-interface-swap"
      auth_code        = local.auth_code
      redis_endpoint   = "${google_redis_instance.session_resiliency.host}:6379"
      redis_auth       = random_password.redis_auth.result
    })
  }
}

data "google_storage_project_service_account" "gcs_account" {
  project    = module.vdss-host-project.project_id
  depends_on = [module.vdss-host-project]
}

data "google_compute_image" "vmseries" {
  filter      = "name=vmseries-flex-byol-1120"
  most_recent = true
  project     = "paloaltonetworksgcp-public"
}

data "google_compute_zones" "available" {
  for_each = toset([var.regions.primary])
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

# Regional Secret Manager resource tracking the random password
resource "google_secret_manager_regional_secret" "ngfw_password" {
  secret_id = "ngfw-admin-password"
  project   = module.vdss-host-project.project_id
  location  = var.regions.primary
  customer_managed_encryption {
    kms_key_name = module.kms[var.regions.primary].keys["default"].id
  }
}

resource "google_secret_manager_regional_secret_version" "ngfw_password_version" {
  secret      = google_secret_manager_regional_secret.ngfw_password.id
  secret_data = random_password.password.result
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
  iam = {
    "roles/iam.serviceAccountUser" = [
      # FIX un-hardcode the prefix
      "serviceAccount:${var.automation.service_accounts.resman}"
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
  for_each       = toset([var.regions.primary])
  prefix         = var.prefix
  project_id     = module.vdss-host-project.project_id
  encryption_key = module.kms[each.value].keys.default.id
  storage_class  = "REGIONAL"
  name           = "ngfw-bootstrap-${each.value}"
  location       = upper(each.value)
  depends_on     = [module.kms]
}

resource "google_storage_bucket_iam_binding" "binding" {
  bucket   = module.ngfw-bootstrap-bucket[each.key].name
  for_each = toset([var.regions.primary])
  role     = "roles/storage.objectUser"
  members = [
    "serviceAccount:service-${module.vdss-host-project.number}@compute-system.iam.gserviceaccount.com",
    module.ngfw-service-account.service_account.member
  ]
}

resource "google_storage_bucket_object" "config_folders" {
  for_each = toset([var.regions.primary])
  name     = "config/"
  bucket   = module.ngfw-bootstrap-bucket[each.key].name
  content  = " "
}

resource "google_storage_bucket_object" "content_folders" {
  for_each = toset([var.regions.primary])
  name     = "content/"
  bucket   = module.ngfw-bootstrap-bucket[each.key].name
  content  = " "
}

resource "google_storage_bucket_object" "software_folders" {
  for_each = toset([var.regions.primary])
  name     = "software/"
  bucket   = module.ngfw-bootstrap-bucket[each.key].name
  content  = " "
}

resource "google_storage_bucket_object" "authcodes" {
  for_each = toset([var.regions.primary])
  name     = "license/authcodes"
  bucket   = module.ngfw-bootstrap-bucket[each.key].name
  source   = "${path.module}/templates/authcodes"
}
resource "google_compute_address" "elb_dmz_ip" {
  for_each     = toset([var.regions.primary])
  name         = "elb-dmz-ip-${each.key}"
  project      = module.vdss-host-project.project_id
  region       = each.value
  address_type = "EXTERNAL"
}

resource "google_compute_address" "ilb_vdss_ip" {
  for_each     = toset([var.regions.primary])
  name         = "ilb-vdss-ip-${each.key}"
  project      = module.vdss-host-project.project_id
  region       = each.value
  address_type = "INTERNAL"
  subnetwork   = try(module.vdss-vpc.subnet_self_links["${each.value}/landing-default"], null)
}

resource "google_compute_address" "ilb_tt_ip" {
  for_each     = toset([var.regions.primary])
  name         = "ilb-tt-ip-${each.key}"
  project      = module.vdss-host-project.project_id
  region       = each.value
  address_type = "INTERNAL"
  subnetwork   = try(module.tenant-transit-vpc.subnet_self_links["${each.value}/tenant-transit"], null)
}

resource "google_compute_address" "ilb_bcap_ip" {
  for_each     = toset([var.regions.primary])
  name         = "ilb-bcap-ip-${each.key}"
  project      = module.vdss-host-project.project_id
  region       = each.value
  address_type = "INTERNAL"
  subnetwork   = try(module.bcap-spoke-vpc.subnet_self_links["${each.value}/bcap-landing"], null)

  lifecycle {
    create_before_destroy = false
  }
}

resource "google_compute_address" "ilb_interconnect_ip" {
  for_each     = toset([var.regions.primary])
  name         = "ilb-interconnect-ip-${each.key}"
  project      = module.vdss-host-project.project_id
  region       = each.value
  address_type = "INTERNAL"
  subnetwork   = try(module.interconnect-spoke-vpc.subnet_self_links["${each.value}/interconnect-landing"], null)

  lifecycle {
    create_before_destroy = false
  }
}

resource "google_storage_bucket_object" "bootstrap-xml" {
  name     = "config/bootstrap.xml"
  for_each = toset([var.regions.primary])
  content  = local.bootstrap-xml-local[each.key]
  bucket   = module.ngfw-bootstrap-bucket[each.key].name
}

resource "google_storage_bucket_object" "init-cfg" {
  name     = "config/init-cfg.txt"
  for_each = toset([var.regions.primary])
  content  = local.init-cfg-local[each.key]
  bucket   = module.ngfw-bootstrap-bucket[each.key].name
}

resource "google_compute_region_instance_template" "ngfw-template" {
  for_each = toset([var.regions.primary])
  project  = module.vdss-host-project.project_id

  name_prefix = "ngfw-template-${each.key}-"
  description = "This template is used to create and configure Palo Alto NGFW instances."

  tags           = ["nva"]
  region         = each.value
  machine_type   = "n2d-standard-8"
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
      kms_key_self_link = module.kms[each.value].keys.default.id
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

  network_interface {
    network    = module.tenant-transit-vpc.self_link
    subnetwork = try(module.tenant-transit-vpc.subnet_self_links["${each.value}/tenant-transit"], null)
  }

  network_interface {
    network    = module.bcap-spoke-vpc.self_link
    subnetwork = try(module.bcap-spoke-vpc.subnet_self_links["${each.value}/bcap-landing"], null)
  }

  network_interface {
    network    = module.interconnect-spoke-vpc.self_link
    subnetwork = try(module.interconnect-spoke-vpc.subnet_self_links["${each.value}/interconnect-landing"], null)
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
    init-cfg-md5                         = google_storage_bucket_object.init-cfg[each.key].md5hash
    authcodes-md5                        = google_storage_bucket_object.authcodes[each.key].md5hash
  }
  lifecycle {
    create_before_destroy = false
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
}

resource "google_compute_region_health_check" "ngfw" {
  for_each = toset([var.regions.primary])
  name     = "ngfw-health-check-${each.key}"
  project  = module.vdss-host-project.project_id
  region   = each.value

  https_health_check {
    port         = 443
    request_path = "/unauth/php/health.php"
  }

  log_config {
    enable = true
  }
}

module "ngfw-mig" {
  for_each   = toset([var.regions.primary])
  source     = "../../../modules/compute-mig"
  project_id = module.vdss-host-project.project_id
  location   = each.key
  name       = "nva-ngfw-${each.key}"
  update_policy = {
    type                           = "PROACTIVE"
    minimal_action                 = "REPLACE"
    most_disruptive_allowed_action = "REPLACE"
    max_surge = {
      fixed = 3
    }
    max_unavailable = {
      fixed = 0
    }
  }
  distribution_policy = {
    target_shape = "EVEN"
    zones        = local.nva_zones[each.key]
  }

  instance_template = google_compute_region_instance_template.ngfw-template[each.key].self_link
  target_size       = 2
  auto_healing_policies = {
    initial_delay_sec = 900
    health_check      = google_compute_region_health_check.ngfw[each.key].id
  }

  health_check_config = null
}

module "ilb-nva-vdss" {
  for_each      = toset([var.regions.primary])
  source        = "../../../modules/net-lb-int"
  project_id    = module.vdss-host-project.project_id
  region        = each.value
  name          = "nva-vdss-${each.key}"
  service_label = var.prefix
  forwarding_rules_config = {
    "" = {
      address       = google_compute_address.ilb_vdss_ip[each.key].address
      global_access = true
    }
  }
  backend_service_config = {
    connection_tracking = {
      persist_conn_on_unhealthy = "NEVER_PERSIST"
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
  health_check        = google_compute_region_health_check.ngfw[each.key].id
  health_check_config = null
}

module "ilb-nva-tenant-transit" {
  for_each      = toset([var.regions.primary])
  source        = "../../../modules/net-lb-int"
  project_id    = module.vdss-host-project.project_id
  region        = each.value
  name          = "nva-tenant-transit-${each.key}"
  service_label = "${var.prefix}-tenant-transit"
  forwarding_rules_config = {
    "" = {
      address       = google_compute_address.ilb_tt_ip[each.key].address
      global_access = true
    }
  }
  backend_service_config = {
    connection_tracking = {
      persist_conn_on_unhealthy = "NEVER_PERSIST"
    }
  }
  vpc_config = {
    network    = module.tenant-transit-vpc.self_link
    subnetwork = try(module.tenant-transit-vpc.subnet_self_links["${each.value}/tenant-transit"], null)
  }
  backends = [
    for k, v in module.ngfw-mig :
    { group = v.group_manager.instance_group }
    if startswith(k, each.key)
  ]
  health_check        = google_compute_region_health_check.ngfw[each.key].id
  health_check_config = null
}

module "ilb-nva-bcap" {
  for_each      = toset([var.regions.primary])
  source        = "../../../modules/net-lb-int"
  project_id    = module.vdss-host-project.project_id
  region        = each.value
  name          = "nva-bcap-${each.key}"
  service_label = "${var.prefix}-bcap"
  forwarding_rules_config = {
    "" = {
      address       = google_compute_address.ilb_bcap_ip[each.key].address
      global_access = true
    }
  }
  backend_service_config = {
    connection_tracking = {
      persist_conn_on_unhealthy = "NEVER_PERSIST"
    }
  }
  vpc_config = {
    network    = module.bcap-spoke-vpc.self_link
    subnetwork = try(module.bcap-spoke-vpc.subnet_self_links["${each.value}/bcap-landing"], null)
  }
  backends = [
    for k, v in module.ngfw-mig :
    { group = v.group_manager.instance_group }
    if startswith(k, each.key)
  ]
  health_check        = google_compute_region_health_check.ngfw[each.key].id
  health_check_config = null
}

module "ilb-nva-interconnect" {
  for_each      = toset([var.regions.primary])
  source        = "../../../modules/net-lb-int"
  project_id    = module.vdss-host-project.project_id
  region        = each.value
  name          = "nva-interconnect-${each.key}"
  service_label = "${var.prefix}-interconnect"
  forwarding_rules_config = {
    "" = {
      address       = google_compute_address.ilb_interconnect_ip[each.key].address
      global_access = true
    }
  }
  backend_service_config = {
    connection_tracking = {
      persist_conn_on_unhealthy = "NEVER_PERSIST"
    }
  }
  vpc_config = {
    network    = module.interconnect-spoke-vpc.self_link
    subnetwork = try(module.interconnect-spoke-vpc.subnet_self_links["${each.value}/interconnect-landing"], null)
  }
  backends = [
    for k, v in module.ngfw-mig :
    { group = v.group_manager.instance_group }
    if startswith(k, each.key)
  ]
  health_check        = google_compute_region_health_check.ngfw[each.key].id
  health_check_config = null
}

module "elb-nva-dmz" {
  for_each   = toset([var.regions.primary])
  source     = "../../../modules/net-lb-ext"
  project_id = module.vdss-host-project.project_id
  region     = each.value
  name       = "elb-dmz-${each.key}"

  forwarding_rules_config = {
    "" = {
      address     = google_compute_address.elb_dmz_ip[each.key].address
      ip_protocol = "L3_DEFAULT"
      all_ports   = true
    }
  }

  backends = [
    for k, v in module.ngfw-mig :
    { group = v.group_manager.instance_group }
    if startswith(k, each.key)
  ]
  health_check        = google_compute_region_health_check.ngfw[each.key].id
  health_check_config = null
}

resource "google_compute_route" "default" {
  name         = "default-route-nva"
  project      = module.vdss-host-project.project_id
  dest_range   = "0.0.0.0/0"
  network      = module.vdss-vpc.name
  next_hop_ilb = module.ilb-nva-vdss[var.regions.primary].forwarding_rules[""].id
  priority     = 100
}

# Google KMS Module
module "kms" {
  source     = "../../../modules/kms"
  project_id = module.vdss-host-project.project_id
  for_each   = toset(local.all_regions)
  keys = {
    "default" = {
      rotation_period = "7776000s" # CIS Compliance Benchmark 1.10
      purpose         = "ENCRYPT_DECRYPT"
      version_template = {
        algorithm        = "GOOGLE_SYMMETRIC_ENCRYPTION"
        protection_level = "HSM"
      }
    }
    "ntp" = {
      rotation_period = "7776000s"
      labels          = { service = "ntp" }
      purpose         = "ENCRYPT_DECRYPT"
      version_template = {
        algorithm        = "GOOGLE_SYMMETRIC_ENCRYPTION"
        protection_level = "HSM"
      }
    }
    "smtp" = {
      rotation_period = "7776000s"
      labels          = { service = "smtp" }
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
      "serviceAccount:${data.google_storage_project_service_account.gcs_account.email_address}",
      # Fix make dynamic, number is {PREFIX}-{COMPLIANCE}-net-vdss-host project number
      "serviceAccount:service-${module.vdss-host-project.number}@compute-system.iam.gserviceaccount.com",
      "serviceAccount:service-${module.vdss-host-project.number}@gcp-sa-secretmanager.iam.gserviceaccount.com"
    ]
  }
  keyring = {
    location = each.value
    name     = "vdss-keyring-${each.value}"
  }
}
