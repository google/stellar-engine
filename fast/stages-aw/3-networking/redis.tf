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

# tfdoc:file:description Redis and encryption.

resource "random_password" "redis_auth" {
  length  = 32
  special = false
}

resource "google_kms_crypto_key_iam_member" "redis_kms" {
  crypto_key_id = module.kms[var.regions.primary].keys.default.id
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = "serviceAccount:service-${module.vdss-host-project.number}@cloud-redis.iam.gserviceaccount.com"
}

resource "google_redis_instance" "session_resiliency" {
  name                    = "${var.prefix}-sess-res"
  tier                    = "STANDARD_HA"
  memory_size_gb          = 1
  region                  = var.regions.primary
  location_id             = "${var.regions.primary}-a"
  alternative_location_id = "${var.regions.primary}-b"

  authorized_network = module.mgmt-vpc.id
  connect_mode       = "PRIVATE_SERVICE_ACCESS"

  redis_version = "REDIS_7_0"
  display_name  = "Session Resiliency for NGFW"

  auth_enabled            = true
  transit_encryption_mode = "SERVER_AUTHENTICATION"

  customer_managed_key = module.kms[var.regions.primary].keys.default.id

  project = module.vdss-host-project.project_id

  depends_on = [
    module.mgmt-vpc,
    google_kms_crypto_key_iam_member.redis_kms
  ]
}

