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
  billing_account = {
    id = "000000-AAAAAA-000000"
  }
  bootstrap_project = "test-bootstrap-0"
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

run "omitted_fedramp_moderate_defaults_to_software" {
  command = plan

  providers = {
    google      = google
    google-beta = google-beta
    local       = local
    null        = null
    time        = time
  }

  override_resource {
    target          = google_assured_workloads_workload.primary
    override_during = plan
    values = {
      display_name = "StellarEngine-test"
      resources = [
        {
          resource_id   = 111111111111
          resource_type = "CONSUMER_FOLDER"
        }
      ]
    }
  }

  variables {
    assured_workloads = {
      regime   = "FEDRAMP_MODERATE"
      location = "us-east4"
    }
  }

  assert {
    condition     = local.kms_protection_level == "SOFTWARE"
    error_message = "FEDRAMP_MODERATE must default kms_protection_level to SOFTWARE when omitted."
  }
}

run "omitted_il5_defaults_to_hsm" {
  command = plan

  providers = {
    google      = google
    google-beta = google-beta
    local       = local
    null        = null
    time        = time
  }

  override_resource {
    target          = google_assured_workloads_workload.primary
    override_during = plan
    values = {
      display_name = "StellarEngine-test"
      resources = [
        {
          resource_id   = 111111111111
          resource_type = "CONSUMER_FOLDER"
        }
      ]
    }
  }

  variables {
    assured_workloads = {
      regime   = "IL5"
      location = "us-east4"
    }
  }

  assert {
    condition     = local.kms_protection_level == "HSM"
    error_message = "IL5 must default kms_protection_level to HSM when omitted."
  }
}

run "explicit_null_fedramp_high_defaults_to_hsm" {
  command = plan

  providers = {
    google      = google
    google-beta = google-beta
    local       = local
    null        = null
    time        = time
  }

  override_resource {
    target          = google_assured_workloads_workload.primary
    override_during = plan
    values = {
      display_name = "StellarEngine-test"
      resources = [
        {
          resource_id   = 111111111111
          resource_type = "CONSUMER_FOLDER"
        }
      ]
    }
  }

  variables {
    kms_protection_level = null
    assured_workloads = {
      regime   = "FEDRAMP_HIGH"
      location = "us-east4"
    }
  }

  assert {
    condition     = local.kms_protection_level == "HSM"
    error_message = "FEDRAMP_HIGH must default kms_protection_level to HSM when explicitly set to null."
  }
}

run "explicit_override_software_wins_for_il5" {
  command = plan

  providers = {
    google      = google
    google-beta = google-beta
    local       = local
    null        = null
    time        = time
  }

  override_resource {
    target          = google_assured_workloads_workload.primary
    override_during = plan
    values = {
      display_name = "StellarEngine-test"
      resources = [
        {
          resource_id   = 111111111111
          resource_type = "CONSUMER_FOLDER"
        }
      ]
    }
  }

  variables {
    kms_protection_level = "SOFTWARE"
    assured_workloads = {
      regime   = "IL5"
      location = "us-east4"
    }
  }

  assert {
    condition     = local.kms_protection_level == "SOFTWARE"
    error_message = "Explicit kms_protection_level = SOFTWARE must override regime default."
  }
}

run "rejects_empty_kms_protection_level" {
  command = plan

  providers = {
    google      = google
    google-beta = google-beta
    local       = local
    null        = null
    time        = time
  }

  variables {
    kms_protection_level = ""
    assured_workloads = {
      regime   = "IL5"
      location = "us-east4"
    }
  }

  expect_failures = [
    var.kms_protection_level
  ]
}

run "rejects_invalid_kms_protection_level" {
  command = plan

  providers = {
    google      = google
    google-beta = google-beta
    local       = local
    null        = null
    time        = time
  }

  variables {
    kms_protection_level = "EXTERNAL"
    assured_workloads = {
      regime   = "IL5"
      location = "us-east4"
    }
  }

  expect_failures = [
    var.kms_protection_level
  ]
}
