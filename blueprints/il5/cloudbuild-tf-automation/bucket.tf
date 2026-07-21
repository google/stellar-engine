/**
 * Copyright 2024 Google LLC
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

module "cloud-build-log-gcs" {
  source         = "../../../modules/gcs"
  project_id     = var.core_project_id
  name           = "cloud-build-logs"
  prefix         = local.prefix
  location       = local.locations.gcs
  storage_class  = local.gcs_storage_class
  versioning     = true
  encryption_key = module.gcs-kms.keys.gcs.id
  depends_on     = [google_kms_crypto_key_iam_member.gcs_sa_kms_access]
}

module "cloud-build-terraform-state-gcs" {
  source         = "../../../modules/gcs"
  project_id     = var.core_project_id
  name           = "cloud-build-state"
  prefix         = local.prefix
  location       = local.locations.gcs
  storage_class  = local.gcs_storage_class
  versioning     = true
  encryption_key = module.gcs-kms.keys.gcs.id
  depends_on     = [google_kms_crypto_key_iam_member.gcs_sa_kms_access]
}

module "cloud-build-source-gcs" {
  source         = "../../../modules/gcs"
  project_id     = var.core_project_id
  name           = "${var.core_project_id}_cloudbuild"
  location       = local.locations.gcs
  storage_class  = local.gcs_storage_class
  versioning     = true
  encryption_key = module.gcs-kms.keys.gcs.id
  depends_on     = [google_kms_crypto_key_iam_member.gcs_sa_kms_access]
}