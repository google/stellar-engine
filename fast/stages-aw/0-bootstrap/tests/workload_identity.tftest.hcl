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

run "merges_github_defaults_and_binds_branch_and_repo" {
  command = plan

  providers = {
    google      = google
    google-beta = google-beta
    local       = local
    null        = null
    time        = time
  }

  override_resource {
    target          = google_iam_workload_identity_pool.default
    override_during = plan
    values = {
      name = "projects/111111111111/locations/global/workloadIdentityPools/test-prod-bootstrap"
    }
  }

  override_resource {
    target          = google_iam_workload_identity_pool_provider.default
    override_during = plan
    values = {
      name = "projects/111111111111/locations/global/workloadIdentityPools/test-prod-bootstrap/providers/github-ci"
    }
  }

  variables {
    federated_identity_providers = {
      github-ci = {
        attribute_condition = "attribute.repository_owner==\"example-org\""
        issuer              = "github"
      }
    }
    cicd_repositories = {
      bootstrap = {
        branch            = "main"
        identity_provider = "github-ci"
        name              = "example-org/bootstrap"
        type              = "github"
      }
    }
  }

  assert {
    condition     = google_iam_workload_identity_pool_provider.default["github-ci"].oidc[0].issuer_uri == "https://token.actions.githubusercontent.com"
    error_message = "GitHub provider must inherit the default GitHub OIDC issuer_uri."
  }

  assert {
    condition     = length(google_iam_workload_identity_pool.default[0].display_name) <= 32
    error_message = "Workload identity pool display_name must not exceed 32 characters."
  }

  assert {
    condition     = length(google_iam_workload_identity_pool_provider.default["github-ci"].display_name) <= 32
    error_message = "Workload identity provider display_name must not exceed 32 characters."
  }

  assert {
    condition     = google_iam_workload_identity_pool_provider.default["github-ci"].attribute_mapping["attribute.fast_sub"] == "\"repo:\" + assertion.repository + \":ref:\" + assertion.ref"
    error_message = "GitHub provider must inherit default attribute_mapping."
  }

  assert {
    condition     = length(local.cicd_providers["github-ci"].audiences) == 1
    error_message = "Null or empty allowed_audiences must fall back to the provider resource audience."
  }

  assert {
    condition = tolist(local._cicd_sa_iam["bootstrap"]["roles/iam.workloadIdentityUser"]) == tolist([
      "principalSet://iam.googleapis.com/projects/111111111111/locations/global/workloadIdentityPools/test-prod-bootstrap/attribute.fast_sub/repo:example-org/bootstrap:ref:refs/heads/main"
    ])
    error_message = "Apply CI/CD SA must bind strictly to the configured GitHub branch."
  }

  assert {
    condition = tolist(local._cicd_r_sa_iam["bootstrap"]["roles/iam.workloadIdentityUser"]) == tolist([
      "principalSet://iam.googleapis.com/projects/111111111111/locations/global/workloadIdentityPools/test-prod-bootstrap/attribute.repository/example-org/bootstrap"
    ])
    error_message = "Read-only CI/CD SA must bind to the repository principalSet."
  }
}

run "gitlab_custom_settings_and_fail_closed_null_branch" {
  command = plan

  providers = {
    google      = google
    google-beta = google-beta
    local       = local
    null        = null
    time        = time
  }

  override_resource {
    target          = google_iam_workload_identity_pool.default
    override_during = plan
    values = {
      name = "projects/111111111111/locations/global/workloadIdentityPools/test-prod-bootstrap"
    }
  }

  override_resource {
    target          = google_iam_workload_identity_pool_provider.default
    override_during = plan
    values = {
      name = "projects/111111111111/locations/global/workloadIdentityPools/test-prod-bootstrap/providers/gitlab-ci"
    }
  }

  variables {
    federated_identity_providers = {
      gitlab-ci = {
        attribute_condition = "attribute.namespace_path==\"example-group\""
        issuer              = "gitlab"
        custom_settings = {
          audiences  = ["https://gitlab.example.com"]
          issuer_uri = "https://gitlab.example.com"
          jwks_json  = "{\"keys\":[]}"
        }
      }
    }
    cicd_repositories = {
      bootstrap = {
        branch            = null
        identity_provider = "gitlab-ci"
        name              = "example-group/bootstrap"
        type              = "gitlab"
      }
    }
  }

  assert {
    condition     = google_iam_workload_identity_pool_provider.default["gitlab-ci"].oidc[0].issuer_uri == "https://gitlab.example.com"
    error_message = "custom_settings.issuer_uri must override the default GitLab issuer_uri."
  }

  assert {
    condition     = google_iam_workload_identity_pool_provider.default["gitlab-ci"].oidc[0].jwks_json == "{\"keys\":[]}"
    error_message = "custom_settings.jwks_json must pass through to the OIDC provider."
  }

  assert {
    condition     = contains(local.cicd_providers["gitlab-ci"].audiences, "https://gitlab.example.com")
    error_message = "cicd_providers.audiences must include custom_settings.audiences."
  }

  assert {
    condition     = length(local._cicd_sa_iam["bootstrap"]["roles/iam.workloadIdentityUser"]) == 0
    error_message = "Null branch must fail closed with an empty WIF principal list on the apply SA."
  }

  assert {
    condition = tolist(local._cicd_r_sa_iam["bootstrap"]["roles/iam.workloadIdentityUser"]) == tolist([
      "principalSet://iam.googleapis.com/projects/111111111111/locations/global/workloadIdentityPools/test-prod-bootstrap/attribute.repository/example-group/bootstrap"
    ])
    error_message = "Read-only GitLab SA must bind to attribute.repository rather than ref:main."
  }
}

run "standalone_custom_url_oidc_and_audiences_precedence" {
  command = plan

  providers = {
    google      = google
    google-beta = google-beta
    local       = local
    null        = null
    time        = time
  }

  override_resource {
    target          = google_iam_workload_identity_pool.default
    override_during = plan
    values = {
      name = "projects/111111111111/locations/global/workloadIdentityPools/test-prod-bootstrap"
    }
  }

  variables {
    federated_identity_providers = {
      custom-idp = {
        attribute_mapping = {
          "google.subject" = "assertion.sub"
        }
        audiences = []
        custom_settings = {
          audiences = ["https://idp.example.com"]
        }
        issuer = "https://idp.example.com"
      }
      github-default-aud = {
        attribute_condition = "attribute.repository_owner==\"example-org\""
        issuer              = "github"
      }
    }
  }

  assert {
    condition     = google_iam_workload_identity_pool_provider.default["custom-idp"].oidc[0].issuer_uri == "https://idp.example.com"
    error_message = "Custom issuer URL must pass through to oidc.issuer_uri."
  }

  assert {
    condition     = contains(google_iam_workload_identity_pool_provider.default["custom-idp"].oidc[0].allowed_audiences, "https://idp.example.com")
    error_message = "Empty top-level audiences must fall back to custom_settings.audiences."
  }

  assert {
    condition     = google_iam_workload_identity_pool_provider.default["github-default-aud"].oidc[0].allowed_audiences == null
    error_message = "Unset audiences must pass null rather than an empty list to oidc.allowed_audiences."
  }
}

run "rejects_custom_url_issuer_referenced_by_cicd_repositories" {
  command = plan

  providers = {
    google      = google
    google-beta = google-beta
    local       = local
    null        = null
    time        = time
  }

  variables {
    federated_identity_providers = {
      custom-gitlab = {
        attribute_mapping = {
          "google.subject" = "assertion.sub"
        }
        issuer = "https://gitlab.corp.example.com"
      }
    }
    cicd_repositories = {
      bootstrap = {
        branch            = "main"
        identity_provider = "custom-gitlab"
        name              = "example-group/bootstrap"
        type              = "gitlab"
      }
    }
  }

  expect_failures = [var.cicd_repositories]
}

run "rejects_builtin_provider_attribute_mapping_without_google_subject" {
  command = plan

  providers = {
    google      = google
    google-beta = google-beta
    local       = local
    null        = null
    time        = time
  }

  variables {
    federated_identity_providers = {
      github-bad-map = {
        attribute_mapping = {
          "attribute.sub" = "assertion.sub"
        }
        issuer = "github"
      }
    }
  }

  expect_failures = [var.federated_identity_providers]
}

run "rejects_invalid_workforce_pool_session_duration" {
  command = plan

  providers = {
    google      = google
    google-beta = google-beta
    local       = local
    null        = null
    time        = time
  }

  variables {
    workforce_identity_pool = {
      session_duration = "600s"
    }
  }

  expect_failures = [var.workforce_identity_pool]
}

run "wires_workforce_identity_pool_attributes_and_safe_defaults" {
  command = plan

  providers = {
    google      = google
    google-beta = google-beta
    local       = local
    null        = null
    time        = time
  }

  variables {
    workforce_identity_pool = {}
  }

  assert {
    condition     = length(google_iam_workforce_pool.default[0].display_name) <= 32
    error_message = "Default workforce pool display_name must not exceed 32 characters."
  }
}

run "wires_custom_workforce_identity_pool_attributes" {
  command = plan

  providers = {
    google      = google
    google-beta = google-beta
    local       = local
    null        = null
    time        = time
  }

  variables {
    workforce_identity_pool = {
      display_name     = "Custom workforce pool"
      description      = "Custom pool description"
      disabled         = true
      session_duration = "7200s"
    }
  }

  assert {
    condition     = google_iam_workforce_pool.default[0].display_name == "Custom workforce pool"
    error_message = "workforce_identity_pool.display_name must be wired."
  }

  assert {
    condition     = google_iam_workforce_pool.default[0].description == "Custom pool description"
    error_message = "workforce_identity_pool.description must be wired."
  }

  assert {
    condition     = google_iam_workforce_pool.default[0].disabled == true
    error_message = "workforce_identity_pool.disabled must be wired."
  }

  assert {
    condition     = google_iam_workforce_pool.default[0].session_duration == "7200s"
    error_message = "workforce_identity_pool.session_duration must be wired."
  }
}

run "rejects_custom_oidc_issuer_without_attribute_mapping" {
  command = plan

  providers = {
    google      = google
    google-beta = google-beta
    local       = local
    null        = null
    time        = time
  }

  variables {
    federated_identity_providers = {
      custom-idp = {
        issuer = "https://idp.example.com"
      }
    }
  }

  expect_failures = [var.federated_identity_providers]
}

run "rejects_workforce_pool_display_name_over_32_chars" {
  command = plan

  providers = {
    google      = google
    google-beta = google-beta
    local       = local
    null        = null
    time        = time
  }

  variables {
    workforce_identity_pool = {
      display_name = "This display name exceeds thirty two characters"
    }
  }

  expect_failures = [var.workforce_identity_pool]
}
