resource "google_service_account" "workflow_sa" {
  account_id   = "docai-workflow-sa"
  display_name = "Workflows Service Account."
}