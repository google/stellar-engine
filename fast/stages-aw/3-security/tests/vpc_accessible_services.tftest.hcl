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

run "default_omits_vpc_accessible_services" {
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
    condition     = length(module.vpc-sc[0].perimeters["default"].status[0].vpc_accessible_services) == 0
    error_message = "Omitting vpc_accessible_services must not enable restriction."
  }
}

run "enforced_perimeter_sets_vpc_accessible_services" {
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
      perimeter_default = {
        vpc_accessible_services = {
          allow_all_restricted_services = true
          enable_restriction            = true
        }
      }
    }
  }

  assert {
    condition     = length(module.vpc-sc[0].perimeters["default"].status[0].vpc_accessible_services) == 1
    error_message = "Setting vpc_accessible_services must populate status.vpc_accessible_services."
  }

  assert {
    condition     = module.vpc-sc[0].perimeters["default"].status[0].vpc_accessible_services[0].enable_restriction == true
    error_message = "vpc_accessible_services.enable_restriction must match the input."
  }

  assert {
    condition     = contains(module.vpc-sc[0].perimeters["default"].status[0].vpc_accessible_services[0].allowed_services, "RESTRICTED-SERVICES")
    error_message = "allow_all_restricted_services = true must include RESTRICTED-SERVICES."
  }
}

run "dry_run_spec_combines_vpc_accessible_services_and_list_override" {
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
      perimeter_default = {
        dry_run_spec = {
          restricted_services = ["storage.googleapis.com"]
          vpc_accessible_services = {
            allow_all_restricted_services = true
            enable_restriction            = true
          }
        }
      }
    }
  }

  assert {
    condition     = length(module.vpc-sc[0].perimeters["default"].status[0].vpc_accessible_services) == 0
    error_message = "Enforced status must not pick up dry_run_spec.vpc_accessible_services."
  }

  assert {
    condition     = length(module.vpc-sc[0].perimeters["default"].spec[0].vpc_accessible_services) == 1
    error_message = "Dry-run spec must include the overridden vpc_accessible_services."
  }

  assert {
    condition     = toset(module.vpc-sc[0].perimeters["default"].spec[0].restricted_services) == toset(["storage.googleapis.com"])
    error_message = "Dry-run spec must combine list and object overrides cleanly."
  }
}

run "dry_run_spec_inherits_enforced_vpc_accessible_services" {
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
      perimeter_default = {
        vpc_accessible_services = {
          allow_all_restricted_services = true
          enable_restriction            = true
        }
        dry_run_spec = {
          restricted_services = ["storage.googleapis.com"]
        }
      }
    }
  }

  assert {
    condition     = length(module.vpc-sc[0].perimeters["default"].spec[0].vpc_accessible_services) == 1
    error_message = "Dry-run spec must inherit enforced vpc_accessible_services when omitted."
  }

  assert {
    condition     = module.vpc-sc[0].perimeters["default"].spec[0].vpc_accessible_services[0].enable_restriction == true
    error_message = "Inherited vpc_accessible_services must keep enable_restriction = true."
  }
}

run "dry_run_spec_disables_vpc_accessible_services_with_enable_restriction_false" {
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
      perimeter_default = {
        vpc_accessible_services = {
          allow_all_restricted_services = true
          enable_restriction            = true
        }
        dry_run_spec = {
          vpc_accessible_services = {
            enable_restriction = false
          }
        }
      }
    }
  }

  assert {
    condition     = module.vpc-sc[0].perimeters["default"].status[0].vpc_accessible_services[0].enable_restriction == true
    error_message = "Enforced status must remain restricted during dry-run disable trial."
  }

  assert {
    condition     = module.vpc-sc[0].perimeters["default"].spec[0].vpc_accessible_services[0].enable_restriction == false
    error_message = "Dry-run spec must disable restriction when enable_restriction = false."
  }

  assert {
    condition     = length(module.vpc-sc[0].perimeters["default"].spec[0].vpc_accessible_services[0].allowed_services) == 0
    error_message = "Disabling enable_restriction alone must clear RESTRICTED-SERVICES."
  }
}

run "dry_run_true_passes_vpc_accessible_services_to_spec_only" {
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
      perimeter_default = {
        dry_run = true
        vpc_accessible_services = {
          allow_all_restricted_services = true
          enable_restriction            = true
        }
      }
    }
  }

  assert {
    condition     = length(module.vpc-sc[0].perimeters["default"].status) == 0
    error_message = "dry_run = true must leave enforced status unset."
  }

  assert {
    condition     = length(module.vpc-sc[0].perimeters["default"].spec[0].vpc_accessible_services) == 1
    error_message = "dry_run = true must pass vpc_accessible_services into spec."
  }
}

run "rejects_empty_dry_run_spec" {
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
      perimeter_default = {
        dry_run_spec = {}
      }
    }
  }

  expect_failures = [var.vpc_sc]
}
