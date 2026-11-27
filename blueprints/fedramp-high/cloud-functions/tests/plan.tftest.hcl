# Copyright 2026 Google LLC
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

mock_provider "google" {}
mock_provider "google-beta" {}
mock_provider "archive" {}
mock_provider "time" {}

override_data {
  target = data.google_project.current
  values = {
    number = "123456789012"
  }
}

override_data {
  target = data.google_storage_project_service_account.gcs_sa
  values = {
    email_address = "service-123456789012@gs-project-accounts.iam.gserviceaccount.com"
    member        = "serviceAccount:service-123456789012@gs-project-accounts.iam.gserviceaccount.com"
  }
}

variables {
  main_project_id = "my-functions-project"
  function_name   = "my_function_00"
  bucket_name     = "my-functions-bucket-00"
  region          = "us-east4"
  kms_key_name    = "projects/my-kms-project/locations/us-east4/keyRings/my-kr/cryptoKeys/default"
}

run "plan_cloud_function_v2" {
  command = plan

  assert {
    condition     = google_cloud_run_v2_service_iam_member.cloud_invoker.name == "my-function-00"
    error_message = "Expected invoker IAM binding name to normalize underscores to hyphens."
  }

  assert {
    condition     = length(google_kms_crypto_key_iam_member.cloud_storage) == 5
    error_message = "Expected five KMS service-agent grants."
  }

  assert {
    condition     = google_kms_crypto_key_iam_member.cloud_storage["compute"].member == "serviceAccount:service-123456789012@compute-system.iam.gserviceaccount.com"
    error_message = "Expected compute service agent KMS binding."
  }
}
