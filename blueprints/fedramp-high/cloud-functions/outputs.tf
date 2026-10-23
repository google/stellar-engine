# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

output "artifact_registry_iam_member" {
  description = "IAM member assigned to Artifact Registry repository permissions."
  value       = module.service-account-runner.iam_email
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
  value       = [for m in google_kms_crypto_key_iam_member.cloud_storage : m.member]
}

output "logging_iam_member" {
  description = "IAM member assigned to roles/logging.logWriter."
  value       = google_project_iam_member.logging_log_writer.member
}

output "storage_object_admin_iam_member" {
  description = "IAM member assigned to Cloud Storage bucket objectUser permissions."
  value       = module.service-account-runner.iam_email
}
