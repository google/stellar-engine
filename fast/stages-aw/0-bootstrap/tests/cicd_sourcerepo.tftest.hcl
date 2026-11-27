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

mock_provider "local" {}

mock_provider "null" {}

mock_provider "time" {}

variables {
  alert_email = "admin@example.com"
  assured_workloads = {
    regime   = "COMPLIANCE_REGIME_UNSPECIFIED"
    location = "us-east4"
  }
  billing_account = {
    id = "000000-AAAAAA-000000"
  }
  bootstrap_project = "test-bootstrap-0"
  cicd_repositories = {
    bootstrap = {
      name   = "test-bootstrap-repo"
      type   = "sourcerepo"
      branch = "main"
    }
    resman = {
      name   = "test-resman-repo"
      type   = "sourcerepo"
      branch = "main"
    }
  }
  kms_protection_level = "HSM"
  organization = {
    domain      = "example.com"
    id          = 123456789012
    customer_id = "C00000000"
  }
  prefix = "test"
  regions = {
    primary = "us-east4"
  }
}

run "plan_sourcerepo_cicd_triggers" {
  command = plan

  providers = {
    google      = google
    google-beta = google-beta
    local       = local
    null        = null
    time        = time
  }

  assert {
    condition     = length(module.automation-tf-cicd-repo) == 2
    error_message = "Expected both bootstrap and resman sourcerepo modules to plan."
  }
}
