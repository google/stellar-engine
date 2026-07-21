# Enable the API service
resource "google_project_service" "documentai" {
  project = var.main_project_id
  for_each = toset([
    "documentai.googleapis.com",
    "workflows.googleapis.com",
  ])
  service            = each.key
  disable_on_destroy = false
}

resource "google_document_ai_processor" "processor" {
  location     = "us"
  display_name = var.name
  type         = var.type

  depends_on = [
    google_project_service.documentai,
  ]
}

#Get the latest stable version of the selected processor
resource "google_document_ai_processor_default_version" "processor" {
  processor = google_document_ai_processor.processor.id
  version   = "${google_document_ai_processor.processor.id}/processorVersions/stable"

  lifecycle {
    ignore_changes = [
      version
    ]
  }
}

module "input_bucket" {
  source                      = "../../../modules/gcs"
  project_id                  = var.main_project_id
  prefix                      = var.main_project_id
  name                        = "doc-ai-input"
  location                    = var.region
  force_destroy               = true
  uniform_bucket_level_access = true
}

module "output_bucket" {
  source                      = "../../../modules/gcs"
  project_id                  = var.main_project_id
  prefix                      = var.main_project_id
  name                        = "doc-ai-output"
  location                    = var.region
  force_destroy               = true
  uniform_bucket_level_access = true
}

module "workflows" {
  source              = "../../../modules/workflows"
  project             = var.main_project_id
  name                = "doc-ai-workflow"
  region              = var.region
  deletion_protection = var.deletion_protection
  description         = "Document AI example workflow."
  file                = var.file
  service_account     = google_service_account.workflow_sa.email
  env_vars = {
    project_id    = var.main_project_id
    input_bucket  = module.input_bucket.url
    output_bucket = module.output_bucket.url
    processor_id  = google_document_ai_processor.processor.id
    location      = var.region
  }
  iam = {
    "roles/workflows.invoker"                 = [google_service_account.workflow_sa.member],
    "roles/logging.logWriter"                 = [google_service_account.workflow_sa.member],
    "roles/serviceusage.serviceUsageConsumer" = [google_service_account.workflow_sa.member],
    "roles/documentai.apiUser"                = [google_service_account.workflow_sa.member],
    "roles/storage.objectViewer"              = [google_service_account.workflow_sa.member],
    "roles/storage.objectCreator"             = [google_service_account.workflow_sa.member],
    "roles/storage.objectUser"                = [google_service_account.workflow_sa.member],
  }
  depends_on = [
    google_project_service.documentai,
    google_service_account.workflow_sa,
  ]
}