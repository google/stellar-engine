# Enable the API service
resource "google_project_service" "translate" {
  project = var.main_project_id
  for_each = toset([
    "translate.googleapis.com",
    "workflows.googleapis.com",
  ])
  service            = each.key
  disable_on_destroy = false
}

module "input_bucket" {
  source                      = "../../../modules/gcs"
  project_id                  = var.main_project_id
  prefix                      = var.main_project_id
  name                        = "translate-input"
  location                    = var.region
  force_destroy               = true
  uniform_bucket_level_access = true
}

module "output_bucket" {
  source                      = "../../../modules/gcs"
  project_id                  = var.main_project_id
  prefix                      = var.main_project_id
  name                        = "translate-output"
  location                    = var.region
  force_destroy               = true
  uniform_bucket_level_access = true
}

resource "google_service_account" "workflow_sa" {
  account_id   = "translate-workflow-sa"
  display_name = "Workflows Service Account."
}

module "workflows" {
  source              = "../../../modules/workflows"
  project             = var.main_project_id
  name                = "translate-workflow"
  region              = var.region
  deletion_protection = var.deletion_protection
  description         = "Translation LLM example workflow."
  file                = var.file
  service_account     = google_service_account.workflow_sa.email
  env_vars = {
    input_bucket  = "${module.input_bucket.url}/*.txt"
    output_bucket = "${module.output_bucket.url}/${var.output_folder}/"
    src_lang      = var.src_lang
    target_lang   = var.target_lang
    parent        = "projects/${var.main_project_id}/locations/us-central1"
  }
  iam = {
    "roles/workflows.invoker"                 = [google_service_account.workflow_sa.member],
    "roles/logging.logWriter"                 = [google_service_account.workflow_sa.member],
    "roles/serviceusage.serviceUsageConsumer" = [google_service_account.workflow_sa.member],
    "roles/storage.objectViewer"              = [google_service_account.workflow_sa.member],
    "roles/storage.objectCreator"             = [google_service_account.workflow_sa.member],
    "roles/storage.objectUser"                = [google_service_account.workflow_sa.member],
    "roles/storage.insightsCollectorService"  = [google_service_account.workflow_sa.member],
    "roles/cloudtranslate.user"               = [google_service_account.workflow_sa.member],
    "roles/cloudtranslate.viewer"             = [google_service_account.workflow_sa.member],
    "roles/cloudtranslate.editor"             = [google_service_account.workflow_sa.member],
  }
  depends_on = [
    google_project_service.translate,
    google_service_account.workflow_sa,
  ]
}