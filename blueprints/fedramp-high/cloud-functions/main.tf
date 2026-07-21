data "google_project" "current" {
  project_id = var.main_project_id
}

resource "google_project_service" "cloud_functions_apis" {
  for_each = toset([
    "artifactregistry.googleapis.com",
    "cloudbuild.googleapis.com",
    "cloudfunctions.googleapis.com",
    "logging.googleapis.com",
    "pubsub.googleapis.com",
    "run.googleapis.com",
    "binaryauthorization.googleapis.com",
  ])

  project            = var.main_project_id
  service            = each.value
  disable_on_destroy = false
}

resource "google_project_service_identity" "artifact_registry_agent" {
  provider = google-beta
  project  = var.main_project_id
  service  = "artifactregistry.googleapis.com"

  depends_on = [
    google_project_service.cloud_functions_apis
  ]
}

resource "google_service_account" "cloud_function_sa" {
  project      = data.google_project.current.project_id
  account_id   = "cloud-function-sa"
  display_name = "Service account for cloud function tasks"
}

resource "google_service_account" "custom_build_sa" {
  project      = data.google_project.current.project_id
  account_id   = "cf-custom-builder-sa"
  display_name = "Custom SA for Cloud Function builds"
}

resource "google_project_iam_member" "cloud_build" {
  project = var.main_project_id
  role    = "roles/cloudbuild.builds.builder"
  member  = "serviceAccount:${google_service_account.cloud_function_sa.email}"
}

resource "google_project_iam_member" "cloud_invoker" {
  project = var.main_project_id
  role    = "roles/run.invoker"
  member  = "serviceAccount:${google_service_account.cloud_function_sa.email}"
}

resource "google_project_iam_member" "build_sa_run_admin" {
  project = data.google_project.current.project_id
  role    = "roles/run.admin"
  member  = "serviceAccount:${google_service_account.custom_build_sa.email}"
}

resource "google_service_account_iam_member" "build_sa_impersonator" {
  service_account_id = google_service_account.cloud_function_sa.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.custom_build_sa.email}"
}

resource "google_kms_crypto_key_iam_binding" "cloud_storage" {
  crypto_key_id = var.kms_key_name
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  members = [
    "serviceAccount:service-${data.google_project.current.number}@gs-project-accounts.iam.gserviceaccount.com",
    "serviceAccount:service-${data.google_project.current.number}@compute-system.iam.gserviceaccount.com",
    "serviceAccount:service-${data.google_project.current.number}@gcf-admin-robot.iam.gserviceaccount.com",
    "serviceAccount:service-${data.google_project.current.number}@serverless-robot-prod.iam.gserviceaccount.com",
    "serviceAccount:${google_project_service_identity.artifact_registry_agent.email}",
    google_service_account.custom_build_sa.member
  ]
}

resource "google_project_iam_member" "artifactregistry_createOnPushWriter" {
  project = var.main_project_id
  role    = "roles/artifactregistry.createOnPushWriter"
  member  = "serviceAccount:${google_service_account.custom_build_sa.email}"
}

resource "google_project_iam_member" "logging_logWriter" {
  project = var.main_project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.custom_build_sa.email}"
}

resource "google_project_iam_member" "storage_objectUser" {
  project = var.main_project_id
  role    = "roles/storage.objectUser"
  member  = "serviceAccount:${google_service_account.custom_build_sa.email}"
}

resource "null_resource" "cloud_function_deploy" {
  depends_on = [
    module.bucket,
    module.registry-docker,
    google_project_iam_member.build_sa_run_admin,
    google_service_account_iam_member.build_sa_impersonator,
    google_kms_crypto_key_iam_binding.cloud_storage,
    google_project_iam_member.artifactregistry_createOnPushWriter,
    google_project_iam_member.storage_objectUser
  ]
  triggers = {
    project_id       = var.main_project_id
    region           = var.region
    function_name    = var.function_name
    runtime          = var.function_runtime
    entry_point      = var.function_entry_point
    memory           = var.function_memory_mb
    timeout          = var.function_timeout_seconds
    source_code_hash = sha256(join("", [for f in fileset("./src-code", "**") : file("./src-code/${f}")]))
  }
  provisioner "local-exec" {
    command = <<EOT
      gcloud functions deploy "${var.function_name}" \
        --project="${var.main_project_id}" \
        --region="${var.region}" \
        --runtime="${var.function_runtime}" \
        --trigger-http \
        --source="./src-code" \
        --entry-point="${var.function_entry_point}" \
        --memory="${var.function_memory_mb}MB" \
        --timeout="${var.function_timeout_seconds}s" \
        --ingress-settings="internal-and-gclb" \
        --binary-authorization default \
        --docker-repository="${module.registry-docker.id}" \
        --kms-key="${var.kms_key_name}"\
        --no-allow-unauthenticated \
        --service-account="${google_service_account.cloud_function_sa.email}" \
        --build-service-account="${google_service_account.custom_build_sa.name}" \
        --gen2
    EOT
  }
}


module "bucket" {
  source         = "../../../modules/gcs"
  project_id     = var.main_project_id
  name           = var.bucket_name
  location       = var.region
  encryption_key = var.kms_key_name
  iam = {
    "roles/storage.objectUser" = [
      "serviceAccount:${data.google_project.current.number}-compute@developer.gserviceaccount.com",
      "serviceAccount:service-${data.google_project.current.number}@gs-project-accounts.iam.gserviceaccount.com",
      "serviceAccount:service-${data.google_project.current.number}@compute-system.iam.gserviceaccount.com"
    ]
  }
  depends_on = [
    google_kms_crypto_key_iam_binding.cloud_storage
  ]
}

module "registry-docker" {
  source         = "../../../modules/artifact-registry"
  project_id     = var.main_project_id
  location       = var.region
  name           = var.artifact_registry_name
  encryption_key = var.kms_key_name
  format = {
    docker = {
      standard = {
        immutable_tags = true
      }
    }
  }
  depends_on = [google_kms_crypto_key_iam_binding.cloud_storage]
}
