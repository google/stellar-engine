data "google_project" "project" {
  project_id = var.main_project_id
}

resource "google_project_service" "cloudscheduler_api" {
  project            = var.main_project_id
  service            = "cloudscheduler.googleapis.com"
  disable_on_destroy = false
}


resource "google_kms_crypto_key_iam_binding" "pubsub" {
  crypto_key_id = var.kms_key_name
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  members = [
    "serviceAccount:service-${data.google_project.project.number}@gcp-sa-pubsub.iam.gserviceaccount.com"
  ]
}

module "pubsub_job" {
  source      = "../../../modules/cloud-scheduler"
  name        = var.name
  description = var.description
  project_id  = var.main_project_id
  schedule    = var.schedule

  retry_config = {
    retry_count = var.retry_count
  }

  trigger_type = "pubsub"
  pubsub_target = {
    data     = base64encode(var.data)
    topic_id = var.topic_id
    new_topic = {
      create       = true
      name         = var.new_topic_name
      kms_key_name = var.kms_key_name
    }
  }
  depends_on = [google_project_service.cloudscheduler_api]
}
