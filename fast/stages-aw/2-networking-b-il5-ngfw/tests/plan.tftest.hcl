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
      {
        name          = "landing-default"
        ip_cidr_range = "10.64.0.0/24"
        region        = "us-east4"
      },
    ]
    dmz = [
      {
        name          = "dmz-default"
        ip_cidr_range = "10.64.128.0/24"
        region        = "us-east4"
      },
    ]
    mgmt = [
      {
        name          = "mgmt-default"
        ip_cidr_range = "10.64.129.0/24"
        region        = "us-east4"
      },
    ]
    prod = [
      {
        name          = "prod-tenant-1-subnet"
        ip_cidr_range = "10.201.0.0/16"
        region        = "us-east4"
        tenant        = "ten-1"
      },
    ]
    int = [
      {
        name          = "int-tenant-1-subnet"
        ip_cidr_range = "10.150.0.0/16"
        region        = "us-east4"
        tenant        = "ten-1"
      },
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

run "plan_default_stage_and_write_only_ngfw_ssh_secrets" {
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
    condition     = nonsensitive(module.ngfw-ssh-secrets.versions["ngfw-ssh-private-key/latest"].secret_data) == null
    error_message = "Private SSH key version must use write-only secret_data_wo instead of secret_data."
  }

  assert {
    condition     = nonsensitive(module.ngfw-ssh-secrets.versions["ngfw-ssh-private-key/latest"].secret_data_wo_version) == "1"
    error_message = "Private SSH key version must set secret_data_wo_version to \"1\"."
  }

  assert {
    condition     = nonsensitive(module.ngfw-ssh-secrets.versions["ngfw-ssh-public-key/latest"].secret_data) == null
    error_message = "Public SSH key version must use write-only secret_data_wo instead of secret_data."
  }

  assert {
    condition     = nonsensitive(module.ngfw-ssh-secrets.versions["ngfw-ssh-public-key/latest"].secret_data_wo_version) == "1"
    error_message = "Public SSH key version must set secret_data_wo_version to \"1\"."
  }

  assert {
    condition = (
      module.ngfw-ssh-secrets.secrets["ngfw-ssh-private-key"].replication[0].user_managed[0].replicas[0].location == "us-east4" &&
      length(module.ngfw-ssh-secrets.secrets["ngfw-ssh-private-key"].replication[0].user_managed[0].replicas[0].customer_managed_encryption) == 1 &&
      module.ngfw-ssh-secrets.secrets["ngfw-ssh-public-key"].replication[0].user_managed[0].replicas[0].location == "us-east4" &&
      length(module.ngfw-ssh-secrets.secrets["ngfw-ssh-public-key"].replication[0].user_managed[0].replicas[0].customer_managed_encryption) == 1
    )
    error_message = "NGFW SSH secrets must use CMEK user-managed replication in regions.primary."
  }

  assert {
    condition     = length(google_compute_subnetwork_iam_member.allow_admin_principals) == 2
    error_message = "Stage 2b must plan subnet IAM bindings for configured tenant_accounts."
  }
}

run "plan_spoke_subnets_with_secondary_ip_cidr_ranges" {
  command = plan

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
        {
          name          = "landing-default"
          ip_cidr_range = "10.64.0.0/24"
          region        = "us-east4"
          secondary_ip_ranges = {
            appliance = { ip_cidr_range = "10.64.1.0/24" }
          }
        },
      ]
      dmz = [
        {
          name          = "dmz-default"
          ip_cidr_range = "10.64.128.0/24"
          region        = "us-east4"
        },
      ]
      mgmt = [
        {
          name          = "mgmt-default"
          ip_cidr_range = "10.64.129.0/24"
          region        = "us-east4"
        },
      ]
      prod = [
        {
          name          = "prod-tenant-1-subnet"
          ip_cidr_range = "10.201.0.0/16"
          region        = "us-east4"
          tenant        = "ten-1"
          secondary_ip_ranges = {
            pods     = { ip_cidr_range = "100.64.0.0/14" }
            services = { ip_cidr_range = "100.68.0.0/20" }
          }
        },
      ]
      int = [
        {
          name          = "int-tenant-1-subnet"
          ip_cidr_range = "10.150.0.0/16"
          region        = "us-east4"
          tenant        = "ten-1"
        },
      ]
    }
  }

  assert {
    condition     = contains(values(local.ngfw_return_routes), "100.64.0.0/14")
    error_message = "NGFW return routes must include the spoke pods secondary_ip_range."
  }

  assert {
    condition     = contains(values(local.ngfw_return_routes), "100.68.0.0/20")
    error_message = "NGFW return routes must include the spoke services secondary_ip_range."
  }

  assert {
    condition     = alltrue([for k in keys(local.ngfw_return_routes) : length(k) <= 31])
    error_message = "All NGFW return route names must stay within the 31-character PAN-OS limit."
  }
}

run "plan_spoke_subnets_with_reserved_internal_range" {
  command = plan

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
        {
          name          = "landing-default"
          ip_cidr_range = "10.64.0.0/24"
          region        = "us-east4"
        },
      ]
      dmz = [
        {
          name          = "dmz-default"
          ip_cidr_range = "10.64.128.0/24"
          region        = "us-east4"
        },
      ]
      mgmt = [
        {
          name          = "mgmt-default"
          ip_cidr_range = "10.64.129.0/24"
          region        = "us-east4"
        },
      ]
      prod = [
        {
          name          = "prod-tenant-1-subnet"
          ip_cidr_range = "10.201.0.0/16"
          region        = "us-east4"
          tenant        = "ten-1"
          secondary_ip_ranges = {
            pods = {
              reserved_internal_range = "projects/my-project/locations/global/internalRanges/pods"
            }
          }
        },
      ]
      int = [
        {
          name          = "int-tenant-1-subnet"
          ip_cidr_range = "10.150.0.0/16"
          region        = "us-east4"
          tenant        = "ten-1"
        },
      ]
    }
  }

  assert {
    condition = (
      module.env-spoke-vpc["Prod"].subnets["us-east4/prod-tenant-1-subnet"].secondary_ip_range[0].range_name == "pods" &&
      module.env-spoke-vpc["Prod"].subnets["us-east4/prod-tenant-1-subnet"].secondary_ip_range[0].reserved_internal_range == "networkconnectivity.googleapis.com/projects/my-project/locations/global/internalRanges/pods"
    )
    error_message = "Spoke subnet must forward reserved_internal_range on secondary_ip_range."
  }
}
