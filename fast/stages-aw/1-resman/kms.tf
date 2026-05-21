# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

module "tenant-project-keys" {
  source     = "../../../modules/kms"
  project_id = module.tenant-self-iac-projects[each.key].project_id
  for_each   = local.tenant_envs
  depends_on = [time_sleep.tenant_project_iam_propagation_delay]
  iam = {
    "roles/cloudkms.cryptoKeyEncrypterDecrypter" = [
      module.tenant-core-sa[each.key].iam_email,
      "serviceAccount:service-${var.automation.project_number}@gs-project-accounts.iam.gserviceaccount.com"
    ]
  }
  keyring = {
    name     = "${each.key}-keyring"
    location = try(each.value.locations.kms != "", false) ? each.value.locations.kms : var.regions.primary
  }
  keys = {
    gcs = {
      purpose         = "ENCRYPT_DECRYPT"
      labels          = { service = "gcs" }
      locations       = try(each.value.locations.kms != "", false) ? each.value.locations.kms : var.regions.primary
      rotation_period = "7776000s" # CIS Compliance Benchmark 1.10
      version_template = {
        algorithm        = "GOOGLE_SYMMETRIC_ENCRYPTION"
        protection_level = "HSM"
      }
    },
    default = {
      purpose         = "ENCRYPT_DECRYPT"
      labels          = { service = "iac-core" }
      locations       = try(each.value.locations.kms != "", false) ? each.value.locations.kms : var.regions.primary
      rotation_period = "7776000s"
      version_template = {
        algorithm        = "GOOGLE_SYMMETRIC_ENCRYPTION"
        protection_level = "HSM"
      }
    }
  }
}

resource "google_kms_crypto_key_iam_member" "resman_bootstrap_kms" {
  for_each      = local.tenant_envs
  crypto_key_id = "projects/${var.automation.project_id}/locations/${var.regions.primary}/keyRings/gcs/cryptoKeys/gcs"
  member        = "serviceAccount:service-${module.tenant-self-iac-projects[each.key].number}@gs-project-accounts.iam.gserviceaccount.com"
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
}

resource "google_kms_crypto_key_iam_member" "tenant_kms" {
  for_each      = local.tenant_envs
  crypto_key_id = module.tenant-project-keys[each.key].key_ids["gcs"]
  member        = "serviceAccount:service-${module.tenant-self-iac-projects[each.key].number}@gs-project-accounts.iam.gserviceaccount.com"
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
}
