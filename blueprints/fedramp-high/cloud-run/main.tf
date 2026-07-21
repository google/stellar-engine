data "google_project" "project" {
  project_id = var.main_project_id
}

data "google_kms_key_ring" "default" {
  name     = var.kms_keyring_name
  location = var.region
  project  = var.core_project_id
}

data "google_kms_crypto_key" "default" {
  name     = var.kms_key_name
  key_ring = data.google_kms_key_ring.default.id
}

resource "google_project_service" "cloud_run" {
  service            = "run.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "binary_authorization" {
  service            = "binaryauthorization.googleapis.com"
  disable_on_destroy = false
}

resource "google_service_account" "cloud_run_service_account" {
  account_id   = var.name
  display_name = "Cloud Run Service Account for ${var.name}"
  project      = var.main_project_id
}

resource "google_project_iam_member" "cloud_run_permissions" {
  project = var.main_project_id
  role    = "roles/run.invoker"
  member  = "serviceAccount:${google_service_account.cloud_run_service_account.email}"
}

resource "google_kms_crypto_key_iam_member" "cloud_run_sa_kms_access" {
  crypto_key_id = data.google_kms_crypto_key.default.id
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = google_service_account.cloud_run_service_account.member
}

resource "google_kms_crypto_key_iam_member" "cloud_run_service_agent_kms_permissions" {
  crypto_key_id = data.google_kms_crypto_key.default.id
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = "serviceAccount:service-${data.google_project.project.number}@serverless-robot-prod.iam.gserviceaccount.com"
}

module "cloud_run" {
  source                      = "../../../modules/cloud-run-v2-se/"
  project_id                  = var.main_project_id
  name                        = var.name
  region                      = var.region
  encryption_key              = data.google_kms_crypto_key.default.id
  create_job                  = var.is_job
  ingress                     = var.ingress
  binary_authorization_mode   = var.binary_authorization_mode
  binary_authorization_policy = var.binary_authorization_policy

  containers = {
    (var.name) = {
      image = var.container_image
      env   = var.env_vars
      ports = {
        port = {
          container_port = var.port
        }
      }
      resources = {
        limits = {
          cpu    = var.cpu
          memory = var.memory
        }
        cpu_idle = var.cpu_idle
      }
    }
  }
  service_account     = google_service_account.cloud_run_service_account.email
  deletion_protection = false
}