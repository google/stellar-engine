locals {
  landing_project = var.network_project_id == null ? var.main_project_id : var.network_project_id
  kms_project     = var.core_project_id == null ? var.main_project_id : var.core_project_id

  network_config = {
    network    = "projects/${local.landing_project}/global/networks/${var.network_name}"
    subnetwork = "projects/${local.landing_project}/regions/${var.region}/subnetworks/${var.subnetwork_name}"
  }
  key = "projects/${local.kms_project}/locations/${var.region}/keyRings/${var.kms_keyring_name}/cryptoKeys/${var.kms_key_name}"

  workstations = {
    for workstation, config in var.workstations : workstation => merge(
      config,
      {
        iam = (
          lookup(config, "users", null) != null ? {
            "roles/workstations.user" = config.users
          } : {}
        )
      }
    )
  }
}

# Enable the API service
resource "google_project_service" "workstations" {
  project = var.main_project_id
  for_each = toset([
    "workstations.googleapis.com",
    "compute.googleapis.com",
  ])
  service            = each.key
  disable_on_destroy = false
}

resource "google_project_service_identity" "workstations_sa" {
  provider = google-beta
  project  = var.main_project_id
  service  = "workstations.googleapis.com"

  depends_on = [google_project_service.workstations]
}

module "workstations" {
  source         = "../../../modules/workstation-cluster"
  id             = var.cluster_id
  project_id     = var.main_project_id
  location       = var.region
  network_config = local.network_config
  workstation_configs = {
    (var.config_id) = {
      container = var.image == null ? null : {
        image = var.image
      }
      encryption_key = {
        kms_key                 = local.key
        kms_key_service_account = google_service_account.workstation_config_key_user.email
      }
      gce_instance = {
        machine_type                = var.machine_type
        disable_public_ip_addresses = true
        shielded_instance_config = {
          enable_secure_boot          = true
          enable_vtpm                 = true
          enable_integrity_monitoring = true
        }
        service_account = google_service_account.workstation_runtime_sa.email
      }
      workstations = local.workstations
    }
  }
  depends_on = [
    google_kms_crypto_key_iam_member.workstations_sa_kms_permissions,
    google_project_iam_member.artifact_registry_reader,
    google_project_iam_member.network_user
  ]
}