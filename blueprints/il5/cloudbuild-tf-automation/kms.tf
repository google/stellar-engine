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
