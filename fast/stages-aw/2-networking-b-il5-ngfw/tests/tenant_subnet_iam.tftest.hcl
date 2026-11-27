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

# Pass every mock provider explicitly in each run block because child modules
# reference google-beta and auxiliary providers that have no stage-root block.
mock_provider "google" {}

mock_provider "google" {
  alias = "billing"
}

mock_provider "google-beta" {}

mock_provider "google-beta" {
  alias = "billing"
}

mock_provider "external" {}

mock_provider "tls" {}

mock_provider "random" {}

mock_provider "time" {}

mock_provider "local" {}

mock_provider "null" {}

variables {
  alert_email = "admin@example.com"
  automation = {
    outputs_bucket = "test-outputs-bucket"
  }
  billing_account = {
    id = "000000-AAAAAA-000000"
  }
  cidrs = {
    healthchecks = ["35.191.0.0/16"]
    iap          = ["35.235.240.0/20"]
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
    landing = [
      { name = "landing-default", ip_cidr_range = "10.64.0.0/24", region = "us-east4" },
    ]
    dmz = [
      { name = "dmz-default", ip_cidr_range = "10.64.128.0/24", region = "us-east4" },
    ]
    mgmt = [
      { name = "mgmt-default", ip_cidr_range = "10.64.129.0/24", region = "us-east4" },
    ]
    prod = [
      { name = "prod-tenant-1-subnet", ip_cidr_range = "10.201.0.0/16", region = "us-east4", tenant = "ten-1" },
    ]
    int = [
      { name = "int-tenant-1-subnet", ip_cidr_range = "10.150.0.0/16", region = "us-east4", tenant = "ten-1" },
    ]
  }
  tenant_accounts = {
    prod-ten-1 = {
      tenant          = "ten-1"
      env             = "Prod"
      main_project    = "test-prod-ten-1"
      admin_principal = "group:ten-1-admins@example.com"
    }
    int-ten-1 = {
      tenant          = "ten-1"
      env             = "Int"
      main_project    = "test-int-ten-1"
      admin_principal = "group:ten-1-admins@example.com"
    }
  }
}

run "plan_single_subnet_preserves_legacy_state_key" {
  command = plan

  override_resource {
    target          = module.kms.google_kms_crypto_key.default["default"]
    override_during = plan
    values = {
      id = "projects/test-net-vdss-host/locations/us-east4/keyRings/vdss-keyring/cryptoKeys/default"
    }
  }

  providers = {
    google              = google
    google.billing      = google.billing
    google-beta         = google-beta
    google-beta.billing = google-beta.billing
    external            = external
    tls                 = tls
    random              = random
    time                = time
    local               = local
    null                = null
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

  override_resource {
    target          = module.kms.google_kms_crypto_key.default["default"]
    override_during = plan
    values = {
      id = "projects/test-net-vdss-host/locations/us-east4/keyRings/vdss-keyring/cryptoKeys/default"
    }
  }

  providers = {
    google              = google
    google.billing      = google.billing
    google-beta         = google-beta
    google-beta.billing = google-beta.billing
    external            = external
    tls                 = tls
    random              = random
    time                = time
    local               = local
    null                = null
  }

  variables {
    tenant_accounts = {
      prod-app-1 = {
        tenant          = "app-1"
        env             = "Prod"
        main_project    = "test-prod-app-1"
        admin_principal = "group:app-1-admins@example.com"
      }
      int-app-1 = {
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

  override_resource {
    target          = module.kms.google_kms_crypto_key.default["default"]
    override_during = plan
    values = {
      id = "projects/test-net-vdss-host/locations/us-east4/keyRings/vdss-keyring/cryptoKeys/default"
    }
  }

  providers = {
    google              = google
    google.billing      = google.billing
    google-beta         = google-beta
    google-beta.billing = google-beta.billing
    external            = external
    tls                 = tls
    random              = random
    time                = time
    local               = local
    null                = null
  }

  variables {
    subnets = {
      landing = [
        { name = "landing-default", ip_cidr_range = "10.64.0.0/24", region = "us-east4" },
      ]
      dmz = [
        { name = "dmz-default", ip_cidr_range = "10.64.128.0/24", region = "us-east4" },
      ]
      mgmt = [
        { name = "mgmt-default", ip_cidr_range = "10.64.129.0/24", region = "us-east4" },
      ]
      prod = [
        { name = "prod-tenant-1-subnet", ip_cidr_range = "10.201.0.0/16", region = "us-east4", tenant = "ten-1" },
        { name = "prod-tenant-1-db-subnet", ip_cidr_range = "10.202.0.0/16", region = "us-east4", tenant = "ten-1" },
      ]
      int = [
        { name = "int-tenant-1-subnet", ip_cidr_range = "10.150.0.0/16", region = "us-east4", tenant = "ten-1" },
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

  override_resource {
    target          = module.kms.google_kms_crypto_key.default["default"]
    override_during = plan
    values = {
      id = "projects/test-net-vdss-host/locations/us-east4/keyRings/vdss-keyring/cryptoKeys/default"
    }
  }

  providers = {
    google              = google
    google.billing      = google.billing
    google-beta         = google-beta
    google-beta.billing = google-beta.billing
    external            = external
    tls                 = tls
    random              = random
    time                = time
    local               = local
    null                = null
  }

  variables {
    subnets = {
      landing = [
        { name = "landing-default", ip_cidr_range = "10.64.0.0/24", region = "us-east4" },
      ]
      dmz = [
        { name = "dmz-default", ip_cidr_range = "10.64.128.0/24", region = "us-east4" },
      ]
      mgmt = [
        { name = "mgmt-default", ip_cidr_range = "10.64.129.0/24", region = "us-east4" },
      ]
      prod = [
        { name = "prod-app-1-subnet", ip_cidr_range = "10.201.0.0/16", region = "us-east4", tenant = "app-1" },
        { name = "prod-app-2-subnet", ip_cidr_range = "10.202.0.0/16", region = "us-east4", tenant = "app-2" },
      ]
      int = [
        { name = "int-app-1-subnet", ip_cidr_range = "10.150.0.0/16", region = "us-east4", tenant = "app-1" },
        { name = "int-app-2-subnet", ip_cidr_range = "10.151.0.0/16", region = "us-east4", tenant = "app-2" },
      ]
    }
    tenant_accounts = {
      prod-app-1 = {
        tenant          = "app-1"
        env             = "Prod"
        main_project    = "test-prod-app-1"
        admin_principal = "group:app-1-admins@example.com"
      }
      prod-app-2 = {
        tenant          = "app-2"
        env             = "Prod"
        main_project    = "test-prod-app-2"
        admin_principal = "group:app-2-admins@example.com"
      }
      int-app-1 = {
        tenant          = "app-1"
        env             = "Int"
        main_project    = "test-int-app-1"
        admin_principal = "group:app-1-admins@example.com"
      }
      int-app-2 = {
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
