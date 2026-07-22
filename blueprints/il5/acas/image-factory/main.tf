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
  project_id = var.project_id
}

data "google_kms_key_ring" "default" {
  name     = var.kms_keyring_name
  location = var.region
  project  = var.kms_project_id
}

data "google_kms_crypto_key" "default" {
  name     = var.kms_key_name
  key_ring = data.google_kms_key_ring.default.id
}

# --- Firewall: Allow IAP to SSH into the ephemeral builder VM ---
# IAP TCP forwarding requires ingress from 35.235.240.0/20 to port 22.
# This rule is scoped to VMs tagged "image-builder" to minimize blast radius.

resource "google_compute_firewall" "allow_iap_ssh_builder" {
  name        = "allow-iap-ssh-image-builder"
  network     = "projects/${coalesce(var.network_project_id, var.project_id)}/global/networks/${var.network_name}"
  project     = coalesce(var.network_project_id, var.project_id)
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
  project            = var.project_id
  service            = each.value
  disable_on_destroy = false
}

resource "google_project_service_identity" "ar_identity" {
  provider = google-beta
  project  = google_project_service.factory_services["artifactregistry.googleapis.com"].project
  service  = "artifactregistry.googleapis.com"
}

# --- Artifact Registry: YUM Repository for ACAS RPMs ---

resource "google_artifact_registry_repository" "acas_rpms" {
  project       = var.project_id
  location      = var.region
  repository_id = var.artifact_registry_repo_id
  description   = "YUM repository hosting ACAS RPMs (SecurityCenter and Nessus Scanner) sourced from the DoD Patch Repository."
  format        = "YUM"

  # CMEK encryption for IL5 compliance
  kms_key_name = data.google_kms_crypto_key.default.id

  depends_on = [
    google_project_service.factory_services,
    google_project_iam_member.artifact_registry_kms
  ]
}

# --- IAM: Allow Artifact Registry SA to encrypt/decrypt with KMS ---

resource "google_project_iam_member" "artifact_registry_kms" {
  project = var.kms_project_id
  role    = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member  = "serviceAccount:${google_project_service_identity.ar_identity.email}"
}

# --- IAM: Allow Compute Engine Service Agent to encrypt/decrypt with KMS ---

resource "google_project_iam_member" "compute_engine_kms" {
  project = var.kms_project_id
  role    = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member  = "serviceAccount:service-${data.google_project.current.number}@compute-system.iam.gserviceaccount.com"
}

# --- IAM: Allow the Compute SA to read# Grant Artifact Registry Reader to Cloud Build SA
resource "google_artifact_registry_repository_iam_member" "cloudbuild_reader" {
  project    = google_artifact_registry_repository.acas_rpms.project
  location   = google_artifact_registry_repository.acas_rpms.location
  repository = google_artifact_registry_repository.acas_rpms.name
  role       = "roles/artifactregistry.reader"
  member     = "serviceAccount:${data.google_project.current.number}-compute@developer.gserviceaccount.com"
}

# --- IAM: Allow Compute SA to create Compute Images & VMs ---

resource "google_project_iam_member" "cloudbuild_image_builder" {
  # checkov:skip=CKV_GCP_46: The default compute service account requires imageUser to create images.
  # investigate/justify/resolve in future iterations
  project = var.project_id
  role    = "roles/compute.imageUser"
  member  = "serviceAccount:${data.google_project.current.number}-compute@developer.gserviceaccount.com"
}

resource "google_project_iam_member" "cloudbuild_compute_admin" {
  # checkov:skip=CKV_GCP_42: roles/compute.instanceAdmin.v1 is the minimum predefined role required
  # for the ephemeral image builder VM lifecycle (create, start, stop, delete).
  # investigate/justify/resolve in future iterations
  # checkov:skip=CKV_GCP_46: The default compute service account requires this role for builder lifecycle.
  # investigate/justify/resolve in future iterations
  project = var.project_id
  role    = "roles/compute.instanceAdmin.v1"
  member  = "serviceAccount:${data.google_project.current.number}-compute@developer.gserviceaccount.com"
}

resource "google_project_iam_member" "cloudbuild_iap_tunnel" {
  # checkov:skip=CKV_GCP_46: The default compute service account requires IAP access to download logs.
  # investigate/justify/resolve in future iterations
  project = var.project_id
  role    = "roles/iap.tunnelResourceAccessor"
  member  = "serviceAccount:${data.google_project.current.number}-compute@developer.gserviceaccount.com"
}

resource "google_project_iam_member" "cloudbuild_service_account_user" {
  # checkov:skip=CKV_GCP_41: The default compute SA requires serviceAccountUser to assign SAs to instances.
  # investigate/justify/resolve in future iterations
  # checkov:skip=CKV_GCP_46: The default compute SA requires serviceAccountUser to assign SAs to instances.
  # investigate/justify/resolve in future iterations
  project = var.project_id
  role    = "roles/iam.serviceAccountUser"
  member  = "serviceAccount:${data.google_project.current.number}-compute@developer.gserviceaccount.com"
}

resource "google_project_iam_member" "cloudbuild_kms" {
  # checkov:skip=CKV_GCP_46: The default compute service account requires KMS access to decrypt the boot image.
  # investigate/justify/resolve in future iterations
  project = var.kms_project_id
  role    = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member  = "serviceAccount:${data.google_project.current.number}-compute@developer.gserviceaccount.com"
}

resource "google_project_iam_member" "cloudbuild_logger" {
  # checkov:skip=CKV_GCP_46: The default compute service account requires logging access to write build logs.
  # investigate/justify/resolve in future iterations
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${data.google_project.current.number}-compute@developer.gserviceaccount.com"
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
        --location=${var.region} --project=${var.project_id} \
        --source="${path.module}/rpms/${var.sc_rpm_filename}"

      gcloud builds submit --no-source \
        --config="${path.module}/cloudbuild-sc.yaml" \
        --project=${var.project_id} \
        --region=${var.region} \
        --substitutions="_PROJECT_ID=${var.project_id},_REGION=${var.region},_ZONE=${var.zone},_BASE_IMAGE=${var.base_image},_IMAGE_FAMILY=${var.sc_image_family},_ARTIFACT_REGISTRY=${var.region}-yum.pkg.dev/projects/${var.project_id}/${var.artifact_registry_repo_id},_KMS_KEY=${data.google_kms_crypto_key.default.id},_SUBNETWORK=${var.subnetwork_name},_NETWORK_PROJECT=${coalesce(var.network_project_id, var.project_id)}"
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
        --location=${var.region} --project=${var.project_id} \
        --source="${path.module}/rpms/${var.scanner_rpm_filename}"

      gcloud builds submit --no-source \
        --config="${path.module}/cloudbuild-scanner.yaml" \
        --project=${var.project_id} \
        --region=${var.region} \
        --substitutions="_PROJECT_ID=${var.project_id},_REGION=${var.region},_ZONE=${var.zone},_BASE_IMAGE=${var.base_image},_IMAGE_FAMILY=${var.scanner_image_family},_ARTIFACT_REGISTRY=${var.region}-yum.pkg.dev/projects/${var.project_id}/${var.artifact_registry_repo_id},_KMS_KEY=${data.google_kms_crypto_key.default.id},_SUBNETWORK=${var.subnetwork_name},_NETWORK_PROJECT=${coalesce(var.network_project_id, var.project_id)}"
    EOT
  }
}

# --- Private Google Access Route ---
# The VPC's 0.0.0.0/0 route points to an ILB firewall which drops traffic to Google APIs.
# This route ensures traffic to the Private Google Access VIP goes through the default internet gateway,
# allowing the builder VMs to reach Artifact Registry natively.
resource "google_compute_route" "pga_route" {
  name             = "allow-pga-for-image-builder"
  project          = coalesce(var.network_project_id, var.project_id)
  network          = var.network_name
  dest_range       = "199.36.153.8/30"
  next_hop_gateway = "default-internet-gateway"
  priority         = 0
  tags             = ["image-builder"]
}
