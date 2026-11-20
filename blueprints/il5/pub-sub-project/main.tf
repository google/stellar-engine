/**
 * Copyright 2024 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

data "google_project" "current" {
  project_id = var.main_project_id
}

# Explicitly enable the Pub/Sub API
resource "google_project_service" "pubsub_api" {
  project            = var.main_project_id
  service            = "pubsub.googleapis.com"
  disable_on_destroy = false
}

# Enabling the API does not create the Pub/Sub service agent on a new project,
# and the key grant below fails with "Service account ... does not exist"
# until the agent exists.
resource "google_project_service_identity" "pubsub_sa" {
  provider   = google-beta
  project    = var.main_project_id
  service    = "pubsub.googleapis.com"
  depends_on = [google_project_service.pubsub_api]
}

# IAM does not recognize a new service agent right away, so a grant issued
# right after the agent is created can fail on the first apply.
resource "time_sleep" "pubsub_sa_propagation" {
  create_duration = "60s"

  depends_on = [google_project_service_identity.pubsub_sa]
}

data "google_kms_key_ring" "default" {
  name     = var.kms_keyring_name
  location = var.gcp_region
  project  = var.core_project_id
}

data "google_kms_crypto_key" "default" {
  name     = var.kms_key_name
  key_ring = data.google_kms_key_ring.default.id
}

resource "google_service_account" "publisher" {
  account_id   = var.publisher_account_id
  display_name = var.publisher_name
}

resource "google_service_account" "subscriber" {
  account_id   = var.subscriber_account_id
  display_name = var.subscriber_name
}

# Pub/Sub accepts roles/pubsub.publisher on a topic and roles/pubsub.subscriber
# on a subscription, so neither role needs a project-level grant. The module
# binds each role additively on the resource that the service account uses.
# The subscriber role is not bound on the topic, where it only allows attaching
# new subscriptions, which the subscriber service account does not create.
module "pubsub" {
  source     = "../../../modules/pubsub"
  project_id = var.main_project_id
  name       = var.pubsub_topic
  regions    = var.allowed_persistence_regions

  kms_key = data.google_kms_crypto_key.default.id
  iam_bindings_additive = {
    publisher = {
      member = google_service_account.publisher.member
      role   = "roles/pubsub.publisher"
    }
  }
  subscriptions = {
    for k, v in var.subscriptions : k => merge(v, {
      iam_bindings_additive = {
        "${k}-subscriber" = {
          member = google_service_account.subscriber.member
          role   = "roles/pubsub.subscriber"
        }
      }
    })
  }
  depends_on = [
    google_project_service.pubsub_api,
    google_kms_crypto_key_iam_member.kms_access
  ]
}

# Pub/Sub encrypts and decrypts messages through its service agent, so only the
# service agent needs the key. The publisher and subscriber service accounts get
# no access to the key. The for_each key stays the member string, so that the
# grant keeps its state address on existing deployments.
resource "google_kms_crypto_key_iam_member" "kms_access" {
  for_each = toset([
    "serviceAccount:service-${data.google_project.current.number}@gcp-sa-pubsub.iam.gserviceaccount.com"
  ])
  crypto_key_id = data.google_kms_crypto_key.default.id
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = each.key
  # The for_each key is built from the project number rather than from
  # google_project_service_identity.pubsub_sa.member, which is unknown until
  # apply. The plan stays valid on a new project, and the grant keeps its state
  # address on existing deployments.
  depends_on = [time_sleep.pubsub_sa_propagation]
}

