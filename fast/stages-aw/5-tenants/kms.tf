locals {
  # Generating a map for each environment (d,t,p) and each location for kms
  tenant_envs_kms = {
    for pairing in setproduct(keys(local.tenant_projects), var.locations.kms) :
    "${pairing[0]}-${pairing[1]}" => {
      project_key = pairing[0]
      location    = pairing[1]
      project_id  = module.tenant-projects[pairing[0]].project_id
      sa_email    = module.tenant-sa[pairing[0]].iam_email
    }
  }
}

module "tenant-project-keys" {
  source     = "../../../modules/kms"
  for_each   = local.tenant_envs_kms
  project_id = each.value.project_id
  iam = {
    "roles/cloudkms.cryptoKeyEncrypterDecrypter" = [
      module.tenant-core-sa.iam_email,
      "serviceAccount:service-${module.tenant-projects[each.value.project_key].number}@gs-project-accounts.iam.gserviceaccount.com"
    ]
  }
  keyring = {
    name     = "${each.value.project_key}-keyring-${each.value.location}"
    location = each.value.location
  }
  keys = {
    gcs = {
      purpose         = "ENCRYPT_DECRYPT"
      labels          = { service = "gcs" }
      rotation_period = "7776000s" # CIS Compliance Benchmark 1.10
      version_template = {
        algorithm        = "GOOGLE_SYMMETRIC_ENCRYPTION"
        protection_level = "HSM"
      }
    },
    default = {
      purpose         = "ENCRYPT_DECRYPT"
      labels          = { service = "iac-core" }
      rotation_period = "7776000s"
      version_template = {
        algorithm        = "GOOGLE_SYMMETRIC_ENCRYPTION"
        protection_level = "HSM"
      }
    }
  }
}

resource "google_kms_crypto_key_iam_member" "resman_bootstrap_kms" {
  for_each      = local.tenant_envs_kms
  crypto_key_id = "projects/${var.automation.project_id}/locations/${each.value.location}/keyRings/gcs-${each.value.location}/cryptoKeys/gcs"
  member        = each.value.sa_email
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
}

resource "google_kms_crypto_key_iam_member" "tenant_kms" {
  for_each      = local.tenant_envs_kms
  crypto_key_id = module.tenant-project-keys[each.key].key_ids["gcs"]
  member        = each.value.sa_email
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
}
