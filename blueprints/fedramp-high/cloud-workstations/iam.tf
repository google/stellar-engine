resource "google_service_account" "workstation_config_key_user" {
  project      = var.main_project_id
  account_id   = "workstation-config-kms"
  display_name = "Workstation Config Service Account"
}

resource "google_service_account" "workstation_runtime_sa" {
  project      = var.main_project_id
  account_id   = "workstation-runtime-sa"
  display_name = "Workstation Runtime Service Account"
}

resource "google_kms_crypto_key_iam_member" "workstations_sa_kms_permissions" {
  crypto_key_id = local.key
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = "serviceAccount:${google_service_account.workstation_config_key_user.email}"
}

resource "google_project_iam_member" "network_user" {
  project = var.network_project_id
  role    = "roles/compute.networkUser"
  member  = "serviceAccount:${google_project_service_identity.workstations_sa.email}"
}

resource "google_project_iam_member" "artifact_registry_reader" {
  project    = var.main_project_id
  role       = "roles/artifactregistry.reader"
  member     = google_service_account.workstation_runtime_sa.member
  depends_on = [google_project_service.workstations]
}