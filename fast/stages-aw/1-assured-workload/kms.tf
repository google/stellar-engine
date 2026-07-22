/**
 * Copyright 2026 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

locals {
  version_template = {
    algorithm        = "GOOGLE_SYMMETRIC_ENCRYPTION"
    protection_level = "HSM"
  }
  primary_location_gcs = element(local.locations.gcs, 0)
}
module "logging-kms" {
  source     = "../../../modules/kms"
  for_each   = toset(local.locations.logging)
  project_id = module.log-export-project.project_id

  keyring = {
    location = each.value
    name     = "logging-${each.value}"
  }
  keys = {
    "log-sink" = {
      rotation_period  = "7776000s" # CIS Compliance Benchmark 1.10
      version_template = local.version_template
    }
    "pubsub" = {
      rotation_period  = "7776000s"
      version_template = local.version_template
      iam_bindings = {
        "pubsub" = {
          members = [module.logging-c5isr-pubsub-sa.iam_email]
          role    = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
        }
      }
    }
  }

  iam_bindings_additive = {
    "pubsub" = {
      member = "serviceAccount:service-${module.log-export-project.number}@gcp-sa-pubsub.iam.gserviceaccount.com"
      role   = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
    },
    "bq" = {
      member = "serviceAccount:bq-${module.log-export-project.number}@bigquery-encryption.iam.gserviceaccount.com"
      role   = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
    },
    "gcs" = {
      member = "serviceAccount:service-${module.log-export-project.number}@gs-project-accounts.iam.gserviceaccount.com"
      role   = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
    },
    "logging" = {
      member = "serviceAccount:service-${module.log-export-project.number}@gcp-sa-logging.iam.gserviceaccount.com"
      role   = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
    }
  }
  iam = {
    "roles/cloudkms.viewer" = [
      module.automation-tf-tenants-sa.iam_email,
    ]
  }
}

module "gcs-kms" {
  source     = "../../../modules/kms"
  for_each   = toset(local.locations.gcs)
  project_id = module.automation-project.project_id

  keyring = {
    location = each.value
    name     = "gcs-${each.value}"
  }
  keys = {
    "gcs" = {
      rotation_period  = "7776000s" # CIS Compliance Benchmark 1.10
      version_template = local.version_template
    }
  }
  iam = {
    "roles/cloudkms.cryptoKeyEncrypterDecrypter" = [
      "serviceAccount:service-${module.automation-project.number}@gs-project-accounts.iam.gserviceaccount.com",
      "serviceAccount:service-${module.log-export-project.number}@gs-project-accounts.iam.gserviceaccount.com",
      module.automation-tf-resman-sa.iam_email
    ],
    "roles/cloudkms.admin" = [
      module.automation-tf-resman-r-sa.iam_email,
      module.automation-tf-resman-sa.iam_email, # This might work as viewer
      module.automation-tf-tenants-sa.iam_email
    ],
    "roles/cloudkms.viewer" = [
      module.automation-tf-tenants-sa.iam_email,
    ]
  }
}
