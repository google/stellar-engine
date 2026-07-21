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

data "google_project" "current" {}

data "google_kms_key_ring" "default" {
  name     = var.kms_keyring_name
  location = var.region
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
resource "google_project_iam_member" "pubsub_publisher" {
  project = var.main_project_id
  role    = "roles/pubsub.publisher"
  member  = google_service_account.publisher.member
}
resource "google_project_iam_member" "pubsub_subscriber" {
  project = var.main_project_id
  role    = "roles/pubsub.subscriber"
  member  = google_service_account.subscriber.member
}
module "pubsub" {
  source     = "../../../modules/pubsub"
  project_id = var.main_project_id
  name       = var.pubsub_topic
  regions    = var.allowed_persistence_regions
  kms_key    = data.google_kms_crypto_key.default.id
  depends_on = [
    google_kms_crypto_key_iam_member.crypto_key,
    google_kms_crypto_key_iam_member.subscriber_sa_kms_access,
    google_kms_crypto_key_iam_member.publisher_sa_kms_access
  ]
}
resource "google_kms_crypto_key_iam_member" "subscriber_sa_kms_access" {
  crypto_key_id = data.google_kms_crypto_key.default.id
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = google_service_account.subscriber.member
}
resource "google_kms_crypto_key_iam_member" "publisher_sa_kms_access" {
  crypto_key_id = data.google_kms_crypto_key.default.id
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = google_service_account.publisher.member
}
resource "google_kms_crypto_key_iam_member" "crypto_key" {
  crypto_key_id = data.google_kms_crypto_key.default.id
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = "serviceAccount:service-${data.google_project.current.number}@gcp-sa-pubsub.iam.gserviceaccount.com"
}