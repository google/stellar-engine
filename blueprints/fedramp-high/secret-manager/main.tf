
locals {
  # Grab all the keys from the secrets variable in order to grant permissions to secret manager service account
  all_kms_keys = distinct(flatten([
    for secret_id, secret_data in var.secrets : [
      secret_data.key
    ]
  ]))

  # Convert the secret variable to a format that is usable by the module
  secrets = {
    for secret_id, secret_data in var.secrets :
    secret_id => {
      locations = [secret_data.location]                       # Convert single string to list of strings
      keys      = { (secret_data.location) = secret_data.key } # Convert single string to map of strings
    }
  }
}

data "google_project" "project" {
  project_id = var.main_project_id
}

# Enable the API service
resource "google_project_service" "secretmanager" {
  project            = var.main_project_id
  service            = "secretmanager.googleapis.com"
  disable_on_destroy = false
}

# Create service account
resource "google_project_service_identity" "secretmanager" {
  provider = google-beta
  project  = var.main_project_id
  service  = "secretmanager.googleapis.com"

  depends_on = [google_project_service.secretmanager]
}

# Grant permissions to secret manager service account
resource "google_kms_crypto_key_iam_member" "secretmanager" {
  for_each      = toset(local.all_kms_keys)
  crypto_key_id = each.value
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = "serviceAccount:service-${data.google_project.project.number}@gcp-sa-secretmanager.iam.gserviceaccount.com"

  depends_on = [google_project_service_identity.secretmanager]
}

# Use the secret manager module to create the secrets
module "secret-manager" {
  source     = "../../../modules/secret-manager"
  project_id = var.main_project_id
  secrets    = local.secrets
  iam        = var.iam
  depends_on = [
    google_project_service.secretmanager,
    google_project_service_identity.secretmanager,
    google_kms_crypto_key_iam_member.secretmanager,
  ]
}