# CIS Compliance Benchmark 2.1 - Folder Scope

resource "google_folder_iam_audit_config" "folder_audit_logs" {
  folder  = var.top_level_folder.id # Replaces 'org_id'. Expects format "folders/1234567" or just "1234567"
  service = "allServices"

  audit_log_config {
    log_type = "ADMIN_READ"
  }
  audit_log_config {
    log_type = "DATA_WRITE"
  }
  audit_log_config {
    log_type = "DATA_READ"
  }
}
