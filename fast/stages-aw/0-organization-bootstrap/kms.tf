locals {
  version_template = {
    algorithm        = "GOOGLE_SYMMETRIC_ENCRYPTION"
    protection_level = "HSM"
  }
}

module "logging-kms" {
  source     = "../../../modules/kms"
  for_each   = toset(local.locations.logging)
  project_id = module.centralized-logging-project.project_id

  keyring = {
    location = each.value
    name     = "logging-${each.key}"
  }
  keys = {
    "log-sink" = {
      rotation_period  = "7776000s" # CIS Compliance Benchmark 1.10
      version_template = local.version_template
    }
  }
  iam_bindings_additive = {
    "logging" = {
      member = "serviceAccount:service-${module.centralized-logging-project.number}@gcp-sa-logging.iam.gserviceaccount.com"
      role   = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
    }
  }
  depends_on = [data.google_logging_project_cmek_settings.settings]
}

module "gcs-kms" {
  source     = "../../../modules/kms"
  for_each   = toset(local.locations.gcs)
  project_id = module.centralized-logging-project.project_id

  keyring = {
    location = each.value
    name     = "gcs-${each.key}"
  }
  keys = {
    "gcs" = {
      rotation_period  = "7776000s" # CIS Compliance Benchmark 1.10
      version_template = local.version_template
    }
  }
  iam = {
    "roles/cloudkms.cryptoKeyEncrypterDecrypter" = [
      "serviceAccount:service-${module.centralized-logging-project.number}@gs-project-accounts.iam.gserviceaccount.com",
      # module.automation-tf-resman-sa.iam_email
    ]
  }
}