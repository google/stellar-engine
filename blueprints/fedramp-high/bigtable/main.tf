data "google_project" "project" {}

resource "google_project_service" "bigtable_api" {
  project            = var.main_project_id
  service            = "bigtableadmin.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service_identity" "bigtable_sa" {
  provider = google-beta
  project  = var.main_project_id
  service  = "bigtableadmin.googleapis.com"
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

resource "google_service_account" "bigtable" {
  account_id = var.bigtable_service_account_id
  project    = var.main_project_id
}

resource "google_kms_crypto_key_iam_member" "bigtable_sa_kms_access" {
  crypto_key_id = data.google_kms_crypto_key.default.id
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = google_service_account.bigtable.member
}

resource "google_kms_crypto_key_iam_member" "bigtable_agent_kms_access" {
  crypto_key_id = data.google_kms_crypto_key.default.id
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = "serviceAccount:service-${data.google_project.project.number}@gcp-sa-bigtable.iam.gserviceaccount.com"
}

module "bigtable-instance" {
  source         = "../../../modules/bigtable-instance"
  project_id     = var.main_project_id
  name           = var.instance_name
  encryption_key = data.google_kms_crypto_key.default.id
  clusters = {
    (var.cluster_id) = {
      cluster_id   = var.cluster_id
      zone         = var.zone
      num_nodes    = var.num_nodes
      storage_type = var.storage_type
    }
  }
  tables              = var.table
  deletion_protection = false
}
