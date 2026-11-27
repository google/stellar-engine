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

variables {
  alert_email = "admin@example.com"
  assured_workloads = {
    regime = "FEDRAMP_HIGH"
    folder = "folders/123456789012"
  }
  automation = {
    outputs_bucket = "test-bucket"
  }
  billing_account = {
    id = "000000-AAAAAA-000000"
  }
  envs_folders = {
    Prod = { admin = "group:prod-admins@example.com" }
    Int  = { admin = "group:int-admins@example.com" }
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
  }
  tenant_accounts = {
    Prod-ten-1 = {
      tenant          = "ten-1"
      env             = "Prod"
      main_project    = "test-prod-ten-1"
      admin_principal = "group:ten-1-admins@example.com"
    }
    Int-ten-1 = {
      tenant          = "ten-1"
      env             = "Int"
      main_project    = "test-int-ten-1"
      admin_principal = "group:ten-1-admins@example.com"
    }
  }
}

run "plan_single_subnet_preserves_legacy_state_key" {
  command = plan

  providers = {
    google              = google
    google.billing      = google.billing
    google-beta         = google-beta
    google-beta.billing = google-beta.billing
  }

  assert {
    condition = (
      toset(keys(google_compute_subnetwork_iam_member.allow_admin_principals)) ==
      toset(["test-prod-ten-1-us-east4", "test-int-ten-1-us-east4"])
    )
    error_message = "Single-subnet tenant mappings must preserve legacy <main_project>-<region> state keys."
  }
}

run "plan_unmapped_tenant_skips_iam_and_warns" {
  command = plan

  providers = {
    google              = google
    google.billing      = google.billing
    google-beta         = google-beta
    google-beta.billing = google-beta.billing
  }

  variables {
    tenant_accounts = {
      Prod-app-1 = {
        tenant          = "app-1"
        env             = "Prod"
        main_project    = "test-prod-app-1"
        admin_principal = "group:app-1-admins@example.com"
      }
      Int-app-1 = {
        tenant          = "app-1"
        env             = "Int"
        main_project    = "test-int-app-1"
        admin_principal = "group:app-1-admins@example.com"
      }
    }
  }

  expect_failures = [
    check.tenant_subnet_mapping,
  ]

  assert {
    condition     = length(google_compute_subnetwork_iam_member.allow_admin_principals) == 0
    error_message = "Unmapped tenants must produce zero allow_admin_principals bindings without failing plan."
  }
}

run "plan_multiple_subnets_per_tenant" {
  command = plan

  providers = {
    google              = google
    google.billing      = google.billing
    google-beta         = google-beta
    google-beta.billing = google-beta.billing
  }

  variables {
    subnets = {
      hub = [
        { name = "hub-default", ip_cidr_range = "10.64.0.0/24", region = "us-east4" },
      ]
      prod = [
        { name = "prod-tenant-1-subnet", ip_cidr_range = "10.202.0.0/16", region = "us-east4", tenant = "ten-1" },
        { name = "prod-tenant-1-db-subnet", ip_cidr_range = "10.203.0.0/16", region = "us-east4", tenant = "ten-1" },
      ]
      int = [
        { name = "int-tenant-1-subnet", ip_cidr_range = "10.30.0.0/16", region = "us-east4", tenant = "ten-1" },
      ]
    }
  }

  assert {
    condition = (
      toset(keys(google_compute_subnetwork_iam_member.allow_admin_principals)) ==
      toset([
        "test-prod-ten-1-us-east4",
        "test-prod-ten-1-us-east4-prod-tenant-1-db-subnet",
        "test-int-ten-1-us-east4",
      ])
    )
    error_message = "Multiple subnets for one tenant must each receive an allow_admin_principals binding."
  }
}

run "plan_renamed_and_additional_tenants_with_matching_subnets" {
  command = plan

  providers = {
    google              = google
    google.billing      = google.billing
    google-beta         = google-beta
    google-beta.billing = google-beta.billing
  }

  variables {
    subnets = {
      hub = [
        { name = "hub-default", ip_cidr_range = "10.64.0.0/24", region = "us-east4" },
      ]
      prod = [
        { name = "prod-app-1-subnet", ip_cidr_range = "10.202.0.0/16", region = "us-east4", tenant = "app-1" },
        { name = "prod-app-2-subnet", ip_cidr_range = "10.204.0.0/16", region = "us-east4", tenant = "app-2" },
      ]
      int = [
        { name = "int-app-1-subnet", ip_cidr_range = "10.30.0.0/16", region = "us-east4", tenant = "app-1" },
        { name = "int-app-2-subnet", ip_cidr_range = "10.31.0.0/16", region = "us-east4", tenant = "app-2" },
      ]
    }
    tenant_accounts = {
      Prod-app-1 = {
        tenant          = "app-1"
        env             = "Prod"
        main_project    = "test-prod-app-1"
        admin_principal = "group:app-1-admins@example.com"
      }
      Prod-app-2 = {
        tenant          = "app-2"
        env             = "Prod"
        main_project    = "test-prod-app-2"
        admin_principal = "group:app-2-admins@example.com"
      }
      Int-app-1 = {
        tenant          = "app-1"
        env             = "Int"
        main_project    = "test-int-app-1"
        admin_principal = "group:app-1-admins@example.com"
      }
      Int-app-2 = {
        tenant          = "app-2"
        env             = "Int"
        main_project    = "test-int-app-2"
        admin_principal = "group:app-2-admins@example.com"
      }
    }
  }

  assert {
    condition = (
      toset(keys(google_compute_subnetwork_iam_member.allow_admin_principals)) ==
      toset([
        "test-prod-app-1-us-east4",
        "test-prod-app-2-us-east4",
        "test-int-app-1-us-east4",
        "test-int-app-2-us-east4",
      ])
    )
    error_message = "Custom tenant keys with matching subnets must plan subnet IAM bindings cleanly."
  }
}
