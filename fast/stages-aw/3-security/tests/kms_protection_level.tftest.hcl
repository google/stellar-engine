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

mock_provider "google" {
  alias = "billing"
}

mock_provider "google-beta" {}

mock_provider "google-beta" {
  alias = "billing"
}

mock_provider "local" {}

mock_provider "time" {}

variables {
  alert_email = "admin@example.com"
  automation = {
    outputs_bucket = "test-bucket"
  }
  billing_account = {
    id = "000000-AAAAAA-000000"
  }
  envs_folders = {
    Prod = { admin = "group:prod-admins@example.com" }
  }
  folder_ids = {
    security = "folders/123456789012"
  }
  organization = {
    domain      = "example.com"
    id          = 123456789012
    customer_id = "C00000000"
  }
  prefix = "test"
  regions = {
    primary = "us-east4"
  }
  service_accounts = {
    data-platform-dev    = "dp-dev@example.iam.gserviceaccount.com"
    data-platform-prod   = "dp-prod@example.iam.gserviceaccount.com"
    project-factory-dev  = "pf-dev@example.iam.gserviceaccount.com"
    project-factory-prod = "pf-prod@example.iam.gserviceaccount.com"
  }
  tenant_accounts = {}
}

run "unset_version_template_inherits_software_protection_level" {
  command = plan

  providers = {
    google              = google
    google.billing      = google.billing
    google-beta         = google-beta
    google-beta.billing = google-beta.billing
    local               = local
    time                = time
  }

  variables {
    kms_protection_level = "SOFTWARE"
    kms_keys = {
      default = {
        rotation_period = "7776000s"
        locations       = ["us", "us-east4"]
      }
    }
  }

  assert {
    condition     = local.kms_locations_keys["us-east4"]["default"].version_template.protection_level == "SOFTWARE"
    error_message = "Expected default key with unset version_template to inherit SOFTWARE protection level."
  }

  assert {
    condition     = module.dev-sec-kms["us-east4"].keys["default"].version_template[0].protection_level == "SOFTWARE"
    error_message = "Expected dev KMS key to plan with SOFTWARE protection level."
  }

  assert {
    condition     = module.prod-sec-kms["us-east4"].keys["default"].version_template[0].protection_level == "SOFTWARE"
    error_message = "Expected prod KMS key to plan with SOFTWARE protection level."
  }
}

run "unset_version_template_inherits_hsm_and_explicit_overrides" {
  command = plan

  providers = {
    google              = google
    google.billing      = google.billing
    google-beta         = google-beta
    google-beta.billing = google-beta.billing
    local               = local
    time                = time
  }

  variables {
    kms_protection_level = "HSM"
    kms_keys = {
      default = {
        rotation_period = "7776000s"
        locations       = ["us-east4"]
      }
      override = {
        rotation_period = "7776000s"
        locations       = ["us-east4"]
        version_template = {
          algorithm        = "GOOGLE_SYMMETRIC_ENCRYPTION"
          protection_level = "SOFTWARE"
        }
      }
    }
  }

  assert {
    condition     = module.prod-sec-kms["us-east4"].keys["default"].version_template[0].protection_level == "HSM"
    error_message = "Expected default key to inherit HSM protection level."
  }

  assert {
    condition     = module.prod-sec-kms["us-east4"].keys["override"].version_template[0].protection_level == "SOFTWARE"
    error_message = "Expected explicit version_template to override stage kms_protection_level."
  }
}
