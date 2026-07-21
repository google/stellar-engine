output "artifact_registry_iam_member" {
  description = "IAM member assigned to roles/artifactregistry.createOnPushWriter."
  value       = google_project_iam_member.artifactregistry_createOnPushWriter.member
}

output "bucket" {
  description = "Bucket holding function source code."
  value       = module.bucket
}

output "cloud_build_iam_member" {
  description = "IAM member assigned to roles/cloudbuild.builds.builder."
  value       = google_project_iam_member.cloud_build.member
}

output "kms_crypto_key_iam_binding_members" {
  description = "IAM members assigned to roles/cloudkms.cryptoKeyEncrypterDecrypter for the specified KMS key."
  value       = google_kms_crypto_key_iam_binding.cloud_storage.members
}

output "logging_iam_member" {
  description = "IAM member assigned to roles/logging.logWriter."
  value       = google_project_iam_member.logging_logWriter.member
}

output "storage_object_admin_iam_member" {
  description = "IAM member assigned to roles/storage.objectAdmin."
  value       = google_project_iam_member.storage_objectUser.member
}
