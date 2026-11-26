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
  bootstrap_project    = "test-bootstrap-0"
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

run "il5_omits_bigquerydatatransfer_from_billing_export" {
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
    condition     = !contains(local.billing_export_services, "bigquerydatatransfer.googleapis.com")
    error_message = "IL5 must omit bigquerydatatransfer.googleapis.com."
  }

  assert {
    condition     = contains(local.billing_export_services, "bigquery.googleapis.com")
    error_message = "IL5 must keep bigquery.googleapis.com."
  }
}

run "data_boundary_for_il4_omits_bigquerydatatransfer" {
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
      regime   = "DATA_BOUNDARY_FOR_IL4"
      location = "us-east4"
    }
  }

  assert {
    condition     = !contains(local.billing_export_services, "bigquerydatatransfer.googleapis.com")
    error_message = "DATA_BOUNDARY_FOR_IL4 must omit bigquerydatatransfer.googleapis.com."
  }
}

run "fedramp_high_keeps_bigquerydatatransfer" {
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
      regime   = "FEDRAMP_HIGH"
      location = "us-east4"
    }
  }

  assert {
    condition     = contains(local.billing_export_services, "bigquerydatatransfer.googleapis.com")
    error_message = "FEDRAMP_HIGH must retain bigquerydatatransfer.googleapis.com."
  }
}
