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

run "default_creates_access_policy_and_uses_org_discovery" {
  command = plan

  providers = {
    google              = google
    google.billing      = google.billing
    google-beta         = google-beta
    google-beta.billing = google-beta.billing
    local               = local
    time                = time
  }

  override_resource {
    target          = module.vpc-sc[0].google_access_context_manager_access_policy.default
    override_during = plan
    values = {
      name = "123456789"
    }
  }

  variables {
    vpc_sc = {
      perimeter_default = {}
    }
  }

  assert {
    condition     = module.vpc-sc[0].access_policy.parent == "organizations/${var.organization.id}"
    error_message = "Omitting access_policy must create the default org access policy."
  }

  assert {
    condition     = module.vpc-sc[0].access_policy.title == "default"
    error_message = "Autocreated access policy must use the default title."
  }

  assert {
    condition     = length(module.vpc-sc-discovery) == 1
    error_message = "Resource discovery must be enabled by default."
  }

  assert {
    condition     = local._vpc_sc_discovery_parent == "organizations/${var.organization.id}"
    error_message = "Omitting resource_discovery.parent must default to the organization."
  }
}

run "reuses_existing_access_policy_scopes_discovery_and_translates_project_ids" {
  command = plan

  providers = {
    google              = google
    google.billing      = google.billing
    google-beta         = google-beta
    google-beta.billing = google-beta.billing
    local               = local
    time                = time
  }

  override_data {
    target = module.vpc-sc[0].data.google_cloud_asset_search_all_resources.projects[0]
    values = {
      results = [
        {
          name    = "//cloudresourcemanager.googleapis.com/projects/test-app-0"
          project = "projects/555555555555"
        }
      ]
    }
  }

  variables {
    vpc_sc = {
      access_policy           = "987654321"
      project_id_search_scope = "folders/111111111111"
      resource_discovery = {
        parent = "folders/111111111111"
      }
      perimeter_default = {
        resources = ["projects/test-app-0"]
      }
    }
  }

  assert {
    condition     = module.vpc-sc[0].access_policy == null
    error_message = "Setting access_policy must skip creating a new access policy."
  }

  assert {
    condition     = module.vpc-sc[0].id == "987654321"
    error_message = "Module must use the provided existing access_policy ID."
  }

  assert {
    condition     = module.vpc-sc[0].perimeters["default"].parent == "accessPolicies/987654321"
    error_message = "Default perimeter must attach to the existing access policy."
  }

  assert {
    condition     = local._vpc_sc_discovery_parent == "folders/111111111111"
    error_message = "resource_discovery.parent must override the default organization scope."
  }

  assert {
    condition     = contains(module.vpc-sc[0].perimeters["default"].status[0].resources, "projects/555555555555")
    error_message = "project_id_search_scope must translate project IDs into project numbers."
  }
}

run "null_resource_discovery_uses_default_org_discovery_and_disabled_sets_count_zero" {
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
    vpc_sc = {
      access_policy      = "987654321"
      resource_discovery = null
      perimeter_default  = {}
    }
  }

  assert {
    condition     = length(module.vpc-sc-discovery) == 1
    error_message = "Explicit resource_discovery = null coerces to the optional default and keeps discovery enabled."
  }

  assert {
    condition     = local._vpc_sc_discovery_parent == "organizations/${var.organization.id}"
    error_message = "Explicit resource_discovery = null must default discovery parent to the organization."
  }
}

run "disabled_resource_discovery_omits_discovery_module" {
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
    vpc_sc = {
      access_policy = "987654321"
      resource_discovery = {
        enabled = false
      }
      perimeter_default = {}
    }
  }

  assert {
    condition     = length(module.vpc-sc-discovery) == 0
    error_message = "Setting resource_discovery.enabled = false must disable module.vpc-sc-discovery."
  }
}

run "rejects_prefixed_access_policy" {
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
    vpc_sc = {
      access_policy     = "accessPolicies/987654321"
      perimeter_default = {}
    }
  }

  expect_failures = [var.vpc_sc]
}

run "rejects_invalid_project_id_search_scope" {
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
    vpc_sc = {
      project_id_search_scope = "projects/123456789012"
      perimeter_default       = {}
    }
  }

  expect_failures = [var.vpc_sc]
}

run "rejects_invalid_resource_discovery_parent" {
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
    vpc_sc = {
      resource_discovery = {
        parent = "projects/123456789012"
      }
      perimeter_default = {}
    }
  }

  expect_failures = [var.vpc_sc]
}

run "rejects_prefix_over_7_chars" {
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
    prefix = "abcdefgh"
  }

  expect_failures = [var.prefix]
}
