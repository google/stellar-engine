/**
 * Copyright 2024 Google LLC
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
  prefix = var.prefix == null ? "" : "${var.prefix}-"

  dc_nodes = {
    for k, v in var.domain_controllers : k => {
      region     = v.region
      zone       = v.zone
      subnetwork = v.subnetwork
      vm_name    = "${local.prefix}gcp-dc-${k}"
      ip_name    = "${local.prefix}gcp-dc-ip-${k}"
    }
  }

  unique_dc_regions = distinct([
    for k, v in var.domain_controllers : v.region
  ])

  dc_ips_config = {
    for k, v in local.dc_nodes : v.ip_name => {
      region     = v.region
      subnetwork = v.subnetwork
      name       = v.ip_name
    }
  }
}

data "google_project" "shared_services" {
  project_id = var.shared_services_project_id
}

resource "google_compute_shared_vpc_service_project" "service_attachment" {
  host_project    = var.hub_project_id
  service_project = var.shared_services_project_id
}

module "domain-controller-sa" {
  source       = "../../../../modules/iam-service-account"
  project_id   = var.shared_services_project_id
  name         = "ad-dc"
  display_name = "AD Domain controller service account."
  prefix       = var.prefix
  iam          = {}
}

module "domain-controller-vms" {
  source        = "../../../../modules/compute-vm"
  for_each      = local.dc_nodes
  name          = each.value.vm_name
  project_id    = var.shared_services_project_id
  zone          = each.value.zone
  instance_type = var.machine_type
  tags          = ["domain-controller"]

  attached_disks = [{
    name        = "${each.value.vm_name}-data"
    device_name = "ad-data-disk"
    size        = var.data_disk_size
    source_type = null
    options = {
      auto_delete = false
      mode        = "READ_WRITE"
      type        = "pd-ssd"
    }
  }]

  boot_disk = {
    initialize_params = {
      image = var.boot_disk_image
      size  = var.boot_disk_size
    }
  }

  shielded_config = {
    enable_secure_boot          = true
    enable_vtpm                 = true
    enable_integrity_monitoring = true
  }

  encryption = {
    kms_key_self_link = module.kms[each.value.region].keys["ad"].id
  }

  network_interfaces = [{
    network    = var.network
    subnetwork = each.value.subnetwork
    addresses = {
      internal = module.domain-controller-ips.internal_addresses[each.value.ip_name].address
    }
  }]

  service_account = {
    email = module.domain-controller-sa.email
  }

  metadata = {
    block-project-ssh-keys = "true"
    serial-port-enable     = "false"
    ntp-server-ip          = var.gcp_ntp_relay_ip

    windows-startup-script-bat = <<EOF
@echo off

echo 199.36.153.7 secretmanager.googleapis.com >> %windir%\system32\drivers\etc\hosts

FOR /F "tokens=*" %%g IN ('powershell -NoProfile -ExecutionPolicy Bypass -Command "$headers = @{'Metadata-Flavor'='Google'}; (Invoke-RestMethod -Headers $headers -Uri 'http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token' -TimeoutSec 5).access_token"') DO SET "TOKEN=%%g"
FOR /F "tokens=*" %%g IN ('powershell -NoProfile -ExecutionPolicy Bypass -Command "$headers = @{'Authorization'='Bearer %TOKEN%'}; $resp = Invoke-RestMethod -Headers $headers -Uri 'https://secretmanager.googleapis.com/v1/projects/${data.google_project.shared_services.number}/secrets/ad-initial-boot-password/versions/latest:access' -TimeoutSec 5; [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($resp.payload.data))"') DO SET "SECURE_PASSWORD=%%g"
net user gcpadmin "%SECURE_PASSWORD%" /add /y /comment:"GCP Admin Bypass" /passwordchg:no
net user gcpadmin "%SECURE_PASSWORD%"
net localgroup Administrators gcpadmin /add
net user gcpadmin /active:yes
SET "SECURE_PASSWORD="
SET "TOKEN="
EOF
  }
  depends_on = [
    google_secret_manager_secret.ad_bootstrap_password,
    google_secret_manager_secret_iam_member.ad_password_accessor
  ]
}

module "domain-controller-ips" {
  source             = "../../../../modules/net-address"
  project_id         = var.shared_services_project_id
  internal_addresses = local.dc_ips_config
  depends_on = [
    google_compute_shared_vpc_service_project.service_attachment
  ]
}

module "kms" {
  source     = "../../../../modules/kms"
  project_id = var.shared_services_project_id
  for_each   = toset(local.unique_dc_regions)
  keys = {
    "ad" = {
      rotation_period = "7776000s"
      labels          = { service = "active-directory" }
      purpose         = "ENCRYPT_DECRYPT"
      version_template = {
        algorithm        = "GOOGLE_SYMMETRIC_ENCRYPTION"
        protection_level = "HSM"
      }
    }
  }

  iam = {
    "roles/cloudkms.cryptoKeyEncrypterDecrypter" = [
      "serviceAccount:service-${data.google_project.shared_services.number}@compute-system.iam.gserviceaccount.com",
    ]
  }
  keyring = {
    location = each.value
    name     = "shdsvr-ad-keyring-${each.value}"
  }
}

resource "google_secret_manager_secret" "ad_bootstrap_password" {
  project   = var.shared_services_project_id
  secret_id = "ad-initial-boot-password"

  replication {
    user_managed {
      dynamic "replicas" {
        for_each = toset(local.unique_dc_regions)
        content {
          location = replicas.value
          customer_managed_encryption {
            kms_key_name = module.kms[replicas.value].keys["ad"].id
          }
        }
      }
    }
  }
  depends_on = [
    google_project_service.secretmanager_api,
    google_kms_crypto_key_iam_member.secretmanager_kms_binding
  ]
}

resource "google_secret_manager_secret_iam_member" "ad_password_accessor" {
  project   = var.shared_services_project_id
  secret_id = google_secret_manager_secret.ad_bootstrap_password.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${module.domain-controller-sa.email}"
}

resource "google_secret_manager_secret_version" "ad_password_payload" {
  secret                 = google_secret_manager_secret.ad_bootstrap_password.id
  secret_data_wo         = ephemeral.random_password.windows_bootstrap_password.result
  secret_data_wo_version = 3
  depends_on = [
    google_project_service.secretmanager_api
  ]
}

resource "google_project_service_identity" "secretmanager_identity" {
  provider = google-beta
  project  = var.shared_services_project_id
  service  = "secretmanager.googleapis.com"
}

resource "google_kms_crypto_key_iam_member" "secretmanager_kms_binding" {
  for_each      = toset(local.unique_dc_regions)
  crypto_key_id = module.kms[each.value].keys["ad"].id
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = "serviceAccount:${google_project_service_identity.secretmanager_identity.email}"
}

ephemeral "random_password" "windows_bootstrap_password" {
  length           = 24
  special          = true
  override_special = "!#$^&*()-_=+[]{}<>?"
  min_upper        = 2
  min_lower        = 2
  min_numeric      = 2
  min_special      = 2
}

resource "google_project_service" "secretmanager_api" {
  project            = var.shared_services_project_id
  service            = "secretmanager.googleapis.com"
  disable_on_destroy = false
}

resource "google_compute_firewall" "allow_rdp_from_iap_to_dcs" {
  name    = "${local.prefix}allow-rdp-from-iap-to-dc"
  network = var.network
  project = var.hub_project_id

  direction     = "INGRESS"
  source_ranges = ["35.235.240.0/20"]

  allow {
    protocol = "tcp"
    ports    = ["3389"]
  }

  target_tags = ["domain-controller"]
}

resource "google_compute_firewall" "allow_restricted_egress_to_google_apis" {
  name    = "${local.prefix}allow-restricted-egress-to-google-apis"
  network = var.network
  project = var.hub_project_id

  direction          = "EGRESS"
  destination_ranges = ["199.36.153.4/30"]

  allow {
    protocol = "tcp"
    ports    = ["443"]
  }

  target_tags = ["domain-controller"]
}