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
data "google_project" "current" {
  project_id = var.shared_services_project_id
}

locals {
  prefix = var.prefix == null ? "" : "${var.prefix}-"
}

# --- Project Services ---

resource "google_project_service" "factory_services" {
  for_each = toset([
    "compute.googleapis.com",
    "cloudbuild.googleapis.com",
    "artifactregistry.googleapis.com",
    "cloudkms.googleapis.com",
    "iam.googleapis.com",
    "osconfig.googleapis.com"
  ])
  project            = var.shared_services_project_id
  service            = each.value
  disable_on_destroy = false
}

resource "google_project_service_identity" "ar_identity" {
  provider = google-beta
  project  = google_project_service.factory_services["artifactregistry.googleapis.com"].project
  service  = "artifactregistry.googleapis.com"
}

# --- Cloud KMS: Native CMEK Keyring & Key ---

resource "google_kms_key_ring" "default" {
  name     = "${local.prefix}acas-keyring-${var.region}"
  location = var.region
  project  = var.shared_services_project_id

  depends_on = [
    google_project_service.factory_services
  ]
}

resource "google_kms_crypto_key" "acas" {
  name            = "acas"
  key_ring        = google_kms_key_ring.default.id
  rotation_period = "7776000s"
  purpose         = "ENCRYPT_DECRYPT"
  deletion_policy = var.kms_deletion_policy

  labels = {
    service = "acas-shared-service"
  }

  version_template {
    algorithm        = "GOOGLE_SYMMETRIC_ENCRYPTION"
    protection_level = "HSM"
  }
}

# --- Cloud KMS IAM: Non-authoritative permissions for CMEK Encryption ---

resource "google_kms_crypto_key_iam_member" "compute_system_kms" {
  crypto_key_id = google_kms_crypto_key.acas.id
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = "serviceAccount:service-${data.google_project.current.number}@compute-system.iam.gserviceaccount.com"
}

resource "google_kms_crypto_key_iam_member" "artifact_registry_kms" {
  crypto_key_id = google_kms_crypto_key.acas.id
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = "serviceAccount:${google_project_service_identity.ar_identity.email}"

  depends_on = [
    google_project_service_identity.ar_identity
  ]
}

# --- Service Account for Custom Image Builder ---

resource "google_service_account" "image_builder" {
  account_id   = "acas-image-builder"
  display_name = "ACAS Custom Image Builder Service Account"
  project      = var.shared_services_project_id
}

resource "google_kms_crypto_key_iam_member" "cloudbuild_kms" {
  crypto_key_id = google_kms_crypto_key.acas.id
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = google_service_account.image_builder.member
}

# --- Artifact Registry: YUM Repository for ACAS RPMs ---

resource "google_artifact_registry_repository" "acas_rpms" {
  project       = var.shared_services_project_id
  location      = var.region
  repository_id = var.artifact_registry_repo_id
  description   = "YUM repository hosting ACAS RPMs (SecurityCenter and Nessus Scanner) sourced from the DoD Patch Repository."
  format        = "YUM"

  # CMEK encryption for IL5 compliance
  kms_key_name = google_kms_crypto_key.acas.id

  depends_on = [
    google_project_service.factory_services,
    google_kms_crypto_key.acas,
    google_kms_crypto_key_iam_member.artifact_registry_kms
  ]
}

# --- IAM: Grant Artifact Registry Reader to Cloud Build SA ---

resource "google_artifact_registry_repository_iam_member" "cloudbuild_reader" {
  project    = google_artifact_registry_repository.acas_rpms.project
  location   = google_artifact_registry_repository.acas_rpms.location
  repository = google_artifact_registry_repository.acas_rpms.name
  role       = "roles/artifactregistry.reader"
  member     = google_service_account.image_builder.member
}

resource "google_artifact_registry_repository_iam_member" "compute_default_reader" {
  project    = google_artifact_registry_repository.acas_rpms.project
  location   = google_artifact_registry_repository.acas_rpms.location
  repository = google_artifact_registry_repository.acas_rpms.name
  role       = "roles/artifactregistry.reader"
  member     = "serviceAccount:${data.google_project.current.number}-compute@developer.gserviceaccount.com"
}

# --- IAM: Allow Cloud Build/Compute Default SA to build images ---

resource "google_project_iam_member" "cloudbuild_image_builder" {
  project = var.shared_services_project_id
  role    = "roles/compute.imageUser"
  member  = google_service_account.image_builder.member
}

resource "google_project_iam_member" "cloudbuild_compute_admin" {
  project = var.shared_services_project_id
  role    = "roles/compute.instanceAdmin.v1"
  member  = google_service_account.image_builder.member
}

resource "google_project_iam_member" "cloudbuild_iap_tunnel" {
  project = var.shared_services_project_id
  role    = "roles/iap.tunnelResourceAccessor"
  member  = google_service_account.image_builder.member
}

resource "google_service_account_iam_member" "cloudbuild_service_account_user" {
  service_account_id = "projects/${var.shared_services_project_id}/serviceAccounts/${data.google_project.current.number}-compute@developer.gserviceaccount.com"
  role               = "roles/iam.serviceAccountUser"
  member             = google_service_account.image_builder.member
}

resource "google_project_iam_member" "cloudbuild_logger" {
  project = var.shared_services_project_id
  role    = "roles/logging.logWriter"
  member  = google_service_account.image_builder.member
}

# Allow Cloud Build to act as/impersonate the custom image builder service account
resource "google_service_account_iam_member" "cloudbuild_agent_impersonate" {
  service_account_id = google_service_account.image_builder.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:service-${data.google_project.current.number}@gcp-sa-cloudbuild.iam.gserviceaccount.com"
}

resource "google_service_account_iam_member" "cloudbuild_legacy_impersonate" {
  service_account_id = google_service_account.image_builder.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${data.google_project.current.number}@cloudbuild.gserviceaccount.com"
}

# --- Auto-Upload and Trigger: SecurityCenter ---

resource "null_resource" "upload_and_build_sc" {
  count = var.build_sc_image && var.sc_rpm_filename != null ? 1 : 0

  triggers = {
    # Re-runs if the RPM file changes
    rpm_hash = filemd5("${path.module}/rpms/${var.sc_rpm_filename}")
  }

  provisioner "local-exec" {
    command = <<-EOT
      gcloud artifacts yum upload ${google_artifact_registry_repository.acas_rpms.repository_id} \
        --location=${var.region} --project=${var.shared_services_project_id} \
        --source="${path.module}/rpms/${var.sc_rpm_filename}"

      gcloud builds submit --no-source \
        --config="${path.module}/cloudbuild-sc.yaml" \
        --project=${var.shared_services_project_id} \
        --region=${var.region} \
        --service-account="projects/${var.shared_services_project_id}/serviceAccounts/${google_service_account.image_builder.email}" \
        --substitutions="_PROJECT_ID=${var.shared_services_project_id},_ZONE=${var.zone},_BASE_IMAGE=${var.base_image},_IMAGE_FAMILY=${var.sc_image_family},_ARTIFACT_REGISTRY=${var.region}-yum.pkg.dev/projects/${var.shared_services_project_id}/${var.artifact_registry_repo_id},_KMS_KEY=${google_kms_crypto_key.acas.id},_SUBNETWORK=${var.subnetwork}"
    EOT
  }
}

# --- Auto-Upload and Trigger: Nessus Scanner ---

resource "null_resource" "upload_and_build_scanner" {
  count = var.build_scanner_image && var.scanner_rpm_filename != null ? 1 : 0

  triggers = {
    # Re-runs if the RPM file changes
    rpm_hash = filemd5("${path.module}/rpms/${var.scanner_rpm_filename}")
  }

  provisioner "local-exec" {
    command = <<-EOT
      gcloud artifacts yum upload ${google_artifact_registry_repository.acas_rpms.repository_id} \
        --location=${var.region} --project=${var.shared_services_project_id} \
        --source="${path.module}/rpms/${var.scanner_rpm_filename}"

      gcloud builds submit --no-source \
        --config="${path.module}/cloudbuild-scanner.yaml" \
        --project=${var.shared_services_project_id} \
        --region=${var.region} \
        --service-account="projects/${var.shared_services_project_id}/serviceAccounts/${google_service_account.image_builder.email}" \
        --substitutions="_PROJECT_ID=${var.shared_services_project_id},_ZONE=${var.zone},_BASE_IMAGE=${var.base_image},_IMAGE_FAMILY=${var.scanner_image_family},_ARTIFACT_REGISTRY=${var.region}-yum.pkg.dev/projects/${var.shared_services_project_id}/${var.artifact_registry_repo_id},_KMS_KEY=${google_kms_crypto_key.acas.id},_SUBNETWORK=${var.subnetwork}"
    EOT
  }
}

# --- Firewall: Allow IAP to SSH into the ephemeral builder VM ---
resource "google_compute_firewall" "allow_iap_ssh_builder" {
  name        = "allow-iap-ssh-image-builder"
  network     = var.network
  project     = var.hub_project_id != null ? var.hub_project_id : var.shared_services_project_id
  description = "Allow IAP TCP forwarding to SSH port on image-builder VMs."
  direction   = "INGRESS"
  priority    = 1000

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  source_ranges = ["35.235.240.0/20"]
  target_tags   = ["image-builder"]
}

# --- Private Google Access Route ---
# The VPC's 0.0.0.0/0 route points to an ILB firewall which drops traffic to Google APIs.
# This route ensures traffic to the Private Google Access VIP goes through the default internet gateway,
# allowing the builder VMs to reach Artifact Registry natively.

resource "google_compute_route" "pga_route" {
  name             = "allow-pga-for-image-builder"
  project          = var.hub_project_id
  network          = var.network
  dest_range       = "199.36.153.8/30"
  next_hop_gateway = "default-internet-gateway"
  priority         = 0
  tags             = ["image-builder"]
}

# --- IAM: Grant networkUser role on Host Project's subnet to Custom Builder SA ---

resource "google_compute_subnetwork_iam_member" "cloudbuild_network_user" {
  count      = var.hub_project_id != null && var.hub_project_id != var.shared_services_project_id ? 1 : 0
  project    = var.hub_project_id
  region     = var.region
  subnetwork = var.subnetwork
  role       = "roles/compute.networkUser"
  member     = google_service_account.image_builder.member
}
