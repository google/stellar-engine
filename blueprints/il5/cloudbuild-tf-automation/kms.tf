locals {
  version_template = {
    algorithm        = "GOOGLE_SYMMETRIC_ENCRYPTION"
    protection_level = "HSM"
  }
}

module "gcs-kms" {
  source     = "../../../modules/kms"
  project_id = var.core_project_id

  keyring = {
    location = local.locations.gcs
    name     = "gcs"
  }
  keys = {
    "gcs" = {
      rotation_period  = "7776000s" # CIS Compliance Benchmark 1.10
      version_template = local.version_template
    }
  }
  iam = {
    "roles/cloudkms.cryptoKeyEncrypterDecrypter" = [
      "serviceAccount:${google_service_account.cloud_build_sa.email}",
    ]
  }
}
