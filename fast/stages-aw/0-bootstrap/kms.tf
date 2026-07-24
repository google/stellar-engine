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

locals {
  version_template = {
    algorithm        = "GOOGLE_SYMMETRIC_ENCRYPTION"
    protection_level = var.assured_workloads.regime == "FEDRAMP_MODERATE" ? "SOFTWARE" : "HSM"
  }
}
module "logging-kms" {
  source     = "../../../modules/kms"
  project_id = module.log-export-project.project_id

  keyring = {
    location = local.locations.logging
    name     = "logging"
  }
  keys = {
    "log-sink" = {
      rotation_period  = "7776000s" # CIS Compliance Benchmark 1.10
      version_template = local.version_template
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
    }
  }
}

module "gcs-kms" {
  source     = "../../../modules/kms"
  project_id = module.automation-project.project_id

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
      "serviceAccount:service-${module.automation-project.number}@gs-project-accounts.iam.gserviceaccount.com",
    ],
    "roles/cloudkms.admin" = [
      "serviceAccount:${var.prefix}-prod-resman-0@${var.prefix}-prod-iac-core-0.iam.gserviceaccount.com"
    ]
    "roles/cloudkms.viewer" = [
      "serviceAccount:${var.prefix}-prod-resman-0r@${var.prefix}-prod-iac-core-0.iam.gserviceaccount.com"
    ]
  }
}
