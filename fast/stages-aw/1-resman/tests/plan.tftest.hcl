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

mock_provider "google" {
  alias = "billing"
}

mock_provider "google-beta" {
  alias = "billing"
}

variables {
  alert_email = "alerts@example.com"
  assured_workloads = {
    regime   = "IL5"
    location = "us"
    folder   = "folders/123456789012"
  }
  automation = {
    outputs_bucket               = "test-outputs-bucket"
    project_id                   = "test-automation"
    project_number               = "123456789012"
    federated_identity_pool      = null
    federated_identity_providers = {}
    service_accounts = {
      resman   = "resman@test-automation.iam.gserviceaccount.com"
      resman-r = "resman-r@test-automation.iam.gserviceaccount.com"
    }
  }
  billing_account = {
    id = "000000-AAAAAA-000000"
  }
  common_services_folder = "folders/123456789012"
  envs_folders = {
    Prod = { admin = "gcp-organization-admins@example.com" }
  }
  fast_features = {
    envs = true
  }
  organization = {
    domain      = "example.com"
    id          = 123456789012
    customer_id = "C00000000"
  }
  prefix = "test"
  regime_mapping = {
    IL5 = "il5"
  }
  regions = {
    primary = "us-east4"
  }
  tenants = {
    empty = {
      admin_principal  = "group:gcp-devops@example.com"
      descriptive_name = "Empty GCS location"
      locations        = { gcs = "", kms = "us-east4" }
    }
    gnull = {
      admin_principal  = "group:gcp-devops@example.com"
      descriptive_name = "Null GCS location"
      locations        = { gcs = null, kms = "us-east4" }
    }
    lnull = {
      admin_principal  = "group:gcp-devops@example.com"
      descriptive_name = "Null locations"
      locations        = null
    }
    multi = {
      admin_principal  = "group:gcp-devops@example.com"
      descriptive_name = "Multi-region GCS location"
      locations        = { gcs = "US", kms = "us" }
    }
    omit = {
      admin_principal  = "group:gcp-devops@example.com"
      descriptive_name = "Omitted locations"
    }
    reg = {
      admin_principal  = "group:gcp-devops@example.com"
      descriptive_name = "Regional GCS location"
      locations        = { gcs = "us-central1", kms = "us-east4" }
    }
  }
}

# The stage declares no google-beta resource in its root module, so the run
# maps every provider explicitly to keep child modules on the mocks.
run "plan_tenant_gcs_locations" {
  command = plan

  providers = {
    google              = google
    google-beta         = google-beta
    google.billing      = google.billing
    google-beta.billing = google-beta.billing
  }

  assert {
    condition = local.gcs_locations == {
      empty = "us-east4"
      gnull = "us-east4"
      lnull = "us-east4"
      multi = "US"
      omit  = "us-east4"
      reg   = "us-central1"
    }
    error_message = "Expected null, empty, and omitted tenant GCS locations to fall back to regions.primary, and explicit locations to apply."
  }

  assert {
    condition = alltrue([
      for k, v in local.tenant_envs : alltrue([
        for bucket in [
          module.tenant-core-gcs[k].bucket,
          module.tenant-self-iac-gcs-outputs[k].bucket,
          module.tenant-self-iac-gcs-states[k].bucket,
        ] : bucket.location == local.gcs_locations[v.tenant]
      ])
    ])
    error_message = "Expected every tenant bucket to use the resolved tenant GCS location."
  }

  assert {
    condition = alltrue([
      for k, v in local.tenant_envs : alltrue([
        for bucket in [
          module.tenant-core-gcs[k].bucket,
          module.tenant-self-iac-gcs-outputs[k].bucket,
          module.tenant-self-iac-gcs-states[k].bucket,
        ] : bucket.storage_class == (v.tenant == "multi" ? "MULTI_REGIONAL" : "REGIONAL")
      ])
    ])
    error_message = "Expected tenant buckets to be REGIONAL unless the tenant sets a multi-region GCS location."
  }
}

run "plan_sourcerepo_cicd_triggers" {
  command = plan

  providers = {
    google              = google
    google-beta         = google-beta
    google.billing      = google.billing
    google-beta.billing = google-beta.billing
  }

  variables {
    cicd_repositories = {
      data_platform_dev = {
        branch = "dev"
        name   = "test-dp-dev"
        type   = "sourcerepo"
      }
      data_platform_prod = {
        branch = "main"
        name   = "test-dp-prod"
        type   = "sourcerepo"
      }
      gcve_dev = {
        branch = "dev"
        name   = "test-gcve-dev"
        type   = "sourcerepo"
      }
      gcve_prod = {
        branch = "main"
        name   = "test-gcve-prod"
        type   = "sourcerepo"
      }
      gke_dev = {
        branch = "dev"
        name   = "test-gke-dev"
        type   = "sourcerepo"
      }
      gke_prod = {
        branch = "main"
        name   = "test-gke-prod"
        type   = "sourcerepo"
      }
      networking = {
        branch = "main"
        name   = "test-networking"
        type   = "sourcerepo"
      }
      project_factory_dev = {
        branch = "dev"
        name   = "test-pf-dev"
        type   = "sourcerepo"
      }
      project_factory_prod = {
        branch = "main"
        name   = "test-pf-prod"
        type   = "sourcerepo"
      }
      security = {
        branch = "main"
        name   = "test-security"
        type   = "sourcerepo"
      }
    }
    fast_features = {
      data_platform   = true
      envs            = true
      gcve            = true
      gke             = true
      project_factory = true
      teams           = true
    }
    team_folders = {
      alpha = {
        descriptive_name         = "Alpha team"
        iam_by_principals        = {}
        impersonation_principals = []
        cicd = {
          branch            = "main"
          identity_provider = null
          name              = "test-team-alpha"
          type              = "sourcerepo"
        }
      }
    }
  }

  assert {
    condition = (
      length(module.branch-dp-dev-cicd-repo) == 1
      && length(module.branch-dp-prod-cicd-repo) == 1
      && length(module.branch-gcve-dev-cicd-repo) == 1
      && length(module.branch-gcve-prod-cicd-repo) == 1
      && length(module.branch-gke-dev-cicd-repo) == 1
      && length(module.branch-gke-prod-cicd-repo) == 1
      && length(module.branch-network-cicd-repo) == 1
      && length(module.branch-pf-dev-cicd-repo) == 1
      && length(module.branch-pf-prod-cicd-repo) == 1
      && length(module.branch-security-cicd-repo) == 1
      && length(module.branch-teams-team-cicd-repo) == 1
    )
    error_message = "Expected all 11 sourcerepo CI/CD modules across 1-resman to plan cleanly."
  }
}
