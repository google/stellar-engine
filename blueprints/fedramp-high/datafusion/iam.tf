resource "google_service_account" "datafusion_sa" {
  project      = var.main_project_id
  account_id   = "df-${var.main_project_id}"
  display_name = "Dataproc Worker Service Account"
}

resource "google_project_iam_member" "datafusion_agent_network_user_main_project" {
  project    = var.main_project_id
  role       = "roles/compute.networkUser"
  member     = "serviceAccount:${google_project_service_identity.datafusion_agent.email}"
  depends_on = [time_sleep.datafusion_service_propagation]
}

resource "google_project_iam_member" "datafusion_agent_network_user_network_project" {
  project    = var.network_project_id
  role       = "roles/compute.networkUser"
  member     = "serviceAccount:${google_project_service_identity.datafusion_agent.email}"
  depends_on = [time_sleep.datafusion_service_propagation]
}

resource "google_project_iam_member" "datafusion_agent_spanner_viewer" {
  project    = var.main_project_id
  role       = "roles/spanner.viewer"
  member     = "serviceAccount:${google_project_service_identity.datafusion_agent.email}"
  depends_on = [time_sleep.datafusion_service_propagation]
}

resource "google_kms_crypto_key_iam_member" "datafusion_agent_kms_access" {
  crypto_key_id = data.google_kms_crypto_key.default.id
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = "serviceAccount:${google_project_service_identity.datafusion_agent.email}"
  depends_on    = [time_sleep.datafusion_service_propagation]
}

resource "google_kms_crypto_key_iam_member" "datafusion_sa_kms_access" {
  crypto_key_id = data.google_kms_crypto_key.default.id
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = "serviceAccount:${google_service_account.datafusion_sa.email}"
  depends_on    = [google_service_account.datafusion_sa]
}

resource "google_kms_crypto_key_iam_member" "gcs_sa_kms_access" {
  crypto_key_id = data.google_kms_crypto_key.default.id
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = "serviceAccount:${data.google_storage_project_service_account.gcs_account_main_project.email_address}"
}

resource "google_project_iam_member" "datafusion_service_agent" {
  project    = var.main_project_id
  role       = "roles/datafusion.serviceAgent"
  member     = "serviceAccount:${google_project_service_identity.datafusion_agent.email}"
  depends_on = [time_sleep.datafusion_service_propagation]
}
resource "google_project_iam_member" "dataproc_service_agent" {
  project    = var.main_project_id
  role       = "roles/dataproc.serviceAgent"
  member     = "serviceAccount:${google_project_service_identity.dataproc_agent.email}"
  depends_on = [time_sleep.datafusion_service_propagation]
}
