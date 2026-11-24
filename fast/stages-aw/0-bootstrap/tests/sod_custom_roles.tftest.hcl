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

mock_provider "google" {
  mock_resource "google_assured_workloads_workload" {
    defaults = {
      resources = [
        {
          resource_id   = "123456789012"
          resource_type = "CONSUMER_FOLDER"
        }
      ]
    }
  }
  mock_data "google_logging_project_settings" {
    defaults = {
      kms_service_account_id = "service-123456789012@gcp-sa-logging.iam.gserviceaccount.com"
    }
  }
}

mock_provider "google-beta" {}

mock_provider "local" {}

mock_provider "time" {}

variables {
  alert_email = "alerts@example.com"
  assured_workloads = {
    regime   = "IL5"
    location = "us-east4"
  }
  billing_account = {
    id = "000000-AAAAAA-000000"
  }
  bootstrap_project    = "my-bootstrap-project"
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

run "plan_default_disabled" {
  command = plan

  providers = {
    google      = google
    google-beta = google-beta
    local       = local
    time        = time
  }

  assert {
    condition     = length(google_organization_iam_custom_role.sod) == 0
    error_message = "Expected no SoD custom role resources when enable_tenant_sod_roles is false."
  }

  assert {
    condition = alltrue([
      for role in [
        "tag_editor",
        "tenant_key_manager",
        "tenant_project_admin",
        "tenant_readonly",
      ] : !contains(keys(output.custom_roles), role)
    ])
    error_message = "Expected SoD custom roles not to be exported when enable_tenant_sod_roles is false."
  }

  assert {
    condition = (
      contains(keys(output.custom_roles), "organization_iam_admin") &&
      contains(keys(output.custom_roles), "tag_viewer")
    )
    error_message = "Expected baseline custom roles from data/custom-roles to remain created by default."
  }
}

run "plan_opt_in_enabled" {
  command = plan

  providers = {
    google      = google
    google-beta = google-beta
    local       = local
    time        = time
  }

  variables {
    enable_tenant_sod_roles = true
  }

  assert {
    condition = alltrue([
      for role in [
        "tag_editor",
        "tenant_key_manager",
        "tenant_project_admin",
        "tenant_readonly",
      ] : contains(keys(google_organization_iam_custom_role.sod), role) &&
      contains(keys(output.custom_roles), role)
    ])
    error_message = "Expected all four opt-in SoD custom roles to be created and exported with snake_case keys when enable_tenant_sod_roles is true."
  }

  assert {
    condition = (
      google_organization_iam_custom_role.sod["tag_editor"].role_id == "tagEditor" &&
      google_organization_iam_custom_role.sod["tenant_key_manager"].role_id == "tenantKeyManager" &&
      google_organization_iam_custom_role.sod["tenant_project_admin"].role_id == "tenantProjectAdmin" &&
      google_organization_iam_custom_role.sod["tenant_readonly"].role_id == "tenantReadOnly"
    )
    error_message = "Expected each SoD custom role resource role_id to match its camelCase YAML name."
  }

  assert {
    condition     = output.custom_roles["tenant_key_manager"] == "organizations/123456789012/roles/tenantKeyManager"
    error_message = "Expected tenant_key_manager output role ID to use camelCase YAML name."
  }

  assert {
    condition     = google_organization_iam_custom_role.sod["tenant_key_manager"].title == "Tenant Cryptographic Key Manager"
    error_message = "Expected tenant_key_manager title to be populated from YAML."
  }

  assert {
    condition     = google_organization_iam_custom_role.sod["tenant_key_manager"].stage == "GA"
    error_message = "Expected tenant_key_manager stage to be GA."
  }

  assert {
    condition = (
      !contains(
        google_organization_iam_custom_role.sod["tenant_key_manager"].permissions,
        "cloudkms.cryptoKeyVersions.useToDecrypt"
      ) &&
      !contains(
        google_organization_iam_custom_role.sod["tenant_key_manager"].permissions,
        "logging.logEntries.list"
      ) &&
      !contains(
        google_organization_iam_custom_role.sod["tenant_key_manager"].permissions,
        "logging.views.access"
      )
    )
    error_message = "Expected tenant_key_manager to exclude crypto data-plane and log entry payload read permissions."
  }

  assert {
    condition = (
      !contains(
        google_organization_iam_custom_role.sod["tenant_readonly"].permissions,
        "storage.objects.get"
      ) &&
      !contains(
        google_organization_iam_custom_role.sod["tenant_readonly"].permissions,
        "secretmanager.versions.access"
      ) &&
      !contains(
        google_organization_iam_custom_role.sod["tenant_readonly"].permissions,
        "bigquery.tables.getData"
      ) &&
      !contains(
        google_organization_iam_custom_role.sod["tenant_readonly"].permissions,
        "logging.logEntries.list"
      ) &&
      !contains(
        google_organization_iam_custom_role.sod["tenant_readonly"].permissions,
        "logging.views.access"
      )
    )
    error_message = "Expected tenant_readonly to exclude object, secret, table data, and log entry payload read permissions."
  }

  assert {
    condition = (
      !contains(
        google_organization_iam_custom_role.sod["tenant_project_admin"].permissions,
        "iam.serviceAccounts.setIamPolicy"
      ) &&
      !contains(
        google_organization_iam_custom_role.sod["tenant_project_admin"].permissions,
        "iam.serviceAccounts.getAccessToken"
      ) &&
      !contains(
        google_organization_iam_custom_role.sod["tenant_project_admin"].permissions,
        "resourcemanager.projects.setIamPolicy"
      ) &&
      !contains(
        google_organization_iam_custom_role.sod["tenant_project_admin"].permissions,
        "cloudbuild.builds.create"
      ) &&
      !contains(
        google_organization_iam_custom_role.sod["tenant_project_admin"].permissions,
        "compute.instances.setMetadata"
      )
    )
    error_message = "Expected tenant_project_admin to exclude SA impersonation, metadata injection, Cloud Build execution, and IAM escalation permissions."
  }

  assert {
    condition     = output.custom_roles["tag_editor"] == "organizations/123456789012/roles/tagEditor"
    error_message = "Expected Stage 0 custom_roles output to export enabled SoD role IDs under snake_case keys."
  }
}

run "plan_opt_in_respects_deploy_org_resources_false" {
  command = plan

  providers = {
    google      = google
    google-beta = google-beta
    local       = local
    time        = time
  }

  variables {
    enable_tenant_sod_roles = true
    deploy_org_resources = {
      custom_roles = false
    }
  }

  assert {
    condition = (
      length(module.organization.custom_role_id) == 0 &&
      length(google_organization_iam_custom_role.sod) == 0 &&
      length(output.custom_roles) == 0
    )
    error_message = "Expected no org custom roles when deploy_org_resources.custom_roles is false."
  }
}

run "plan_opt_in_merges_with_caller_custom_roles" {
  command = plan

  providers = {
    google      = google
    google-beta = google-beta
    local       = local
    time        = time
  }

  variables {
    enable_tenant_sod_roles = true
    custom_roles = {
      customCallerRole = ["resourcemanager.projects.get"]
    }
  }

  assert {
    condition = (
      contains(keys(output.custom_roles), "tenant_key_manager") &&
      contains(keys(output.custom_roles), "customCallerRole")
    )
    error_message = "Expected opt-in SoD roles and caller-supplied custom_roles to merge cleanly."
  }
}
