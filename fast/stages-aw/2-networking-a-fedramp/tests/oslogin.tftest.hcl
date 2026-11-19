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

# The stage root references the default google-beta provider only through its
# child modules, so each run passes every mock explicitly. Without the
# providers map Terraform leaves the default google-beta unmocked and the run
# fails while loading credentials.
mock_provider "google" {}

mock_provider "google" {
  alias = "billing"
}

mock_provider "google-beta" {}

mock_provider "google-beta" {
  alias = "billing"
}

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
    Int  = { admin = "group:int-admins@example.com" }
    Test = { admin = "group:test-admins@example.com" }
  }
  folder_ids = {
    networking = "folders/123456789012"
  }
  organization = {
    domain      = "example.com"
    id          = 123456789012
    customer_id = "C00000000"
  }
  prefix = "test"
  proxy_subnets = {
    Prod = "10.1.1.0/24"
    Int  = "10.1.2.0/24"
    Test = "10.1.3.0/24"
  }
  regions = {
    primary = "us-east4"
  }
  subnets = {
    hub = [
      { name = "hub-default", ip_cidr_range = "10.64.0.0/24", region = "us-east4" },
    ]
    prod = [
      { name = "prod-tenant-1-subnet", ip_cidr_range = "10.202.0.0/16", region = "us-east4", tenant = "ten-1" },
    ]
    int = [
      { name = "int-tenant-1-subnet", ip_cidr_range = "10.30.0.0/16", region = "us-east4", tenant = "ten-1" },
    ]
    test = [
      { name = "test-tenant-1-subnet", ip_cidr_range = "10.40.0.0/16", region = "us-east4", tenant = "ten-1" },
    ]
  }
  tenant_accounts = {}
}

# compute.requireOsLogin already sets enable-oslogin on new projects for these
# regimes, so a metadata item for the same key fails with "already present".
run "fedramp_high_leaves_oslogin_to_the_constraint" {
  command = plan

  providers = {
    google              = google
    google.billing      = google.billing
    google-beta         = google-beta
    google-beta.billing = google-beta.billing
  }

  variables {
    assured_workloads = {
      regime = "FEDRAMP_HIGH"
      folder = "folders/123456789012"
    }
  }

  assert {
    condition     = length(google_compute_project_metadata_item.oslogin) == 0
    error_message = "FEDRAMP_HIGH must not plan enable-oslogin metadata items."
  }
}

run "fedramp_moderate_leaves_oslogin_to_the_constraint" {
  command = plan

  providers = {
    google              = google
    google.billing      = google.billing
    google-beta         = google-beta
    google-beta.billing = google-beta.billing
  }

  variables {
    assured_workloads = {
      regime = "FEDRAMP_MODERATE"
      folder = "folders/123456789012"
    }
  }

  assert {
    condition     = length(google_compute_project_metadata_item.oslogin) == 0
    error_message = "FEDRAMP_MODERATE must not plan enable-oslogin metadata items."
  }
}

# Stage 0 does not enforce compute.requireOsLogin for IL4 and IL5, so the
# stage has to set the key itself on every host project.
run "il5_sets_oslogin_on_every_host_project" {
  command = plan

  providers = {
    google              = google
    google.billing      = google.billing
    google-beta         = google-beta
    google-beta.billing = google-beta.billing
  }

  variables {
    assured_workloads = {
      regime = "IL5"
      folder = "folders/123456789012"
    }
  }

  assert {
    condition = (
      toset(keys(google_compute_project_metadata_item.oslogin)) ==
      toset(["hub", "prod", "int", "test"])
    )
    error_message = "IL5 must plan one enable-oslogin item per host project."
  }

  assert {
    condition = alltrue([
      for item in google_compute_project_metadata_item.oslogin :
      item.key == "enable-oslogin" && item.value == "true"
    ])
    error_message = "Every item must set enable-oslogin to true."
  }
}

run "unknown_regime_sets_oslogin" {
  command = plan

  providers = {
    google              = google
    google.billing      = google.billing
    google-beta         = google-beta
    google-beta.billing = google-beta.billing
  }

  assert {
    condition     = length(google_compute_project_metadata_item.oslogin) == 4
    error_message = "An unset regime must plan enable-oslogin items."
  }
}

run "override_sets_oslogin_without_the_constraint" {
  command = plan

  providers = {
    google              = google
    google.billing      = google.billing
    google-beta         = google-beta
    google-beta.billing = google-beta.billing
  }

  variables {
    assured_workloads = {
      regime = "FEDRAMP_HIGH"
      folder = "folders/123456789012"
    }
    manage_oslogin_metadata = true
  }

  assert {
    condition     = length(google_compute_project_metadata_item.oslogin) == 4
    error_message = "manage_oslogin_metadata = true must plan enable-oslogin items."
  }
}

run "override_skips_oslogin_under_an_external_constraint" {
  command = plan

  providers = {
    google              = google
    google.billing      = google.billing
    google-beta         = google-beta
    google-beta.billing = google-beta.billing
  }

  variables {
    assured_workloads = {
      regime = "IL5"
      folder = "folders/123456789012"
    }
    manage_oslogin_metadata = false
  }

  assert {
    condition     = length(google_compute_project_metadata_item.oslogin) == 0
    error_message = "manage_oslogin_metadata = false must not plan enable-oslogin items."
  }
}
