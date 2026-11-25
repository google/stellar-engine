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
  bootstrap_project = "test-bootstrap-0"
  deploy_org_resources = {
    org_policies = false
  }
  factories_config = {
    org_policy = "./tests/fixtures/org-policies"
  }
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

run "il5_folder_mode_excludes_aw_managed_baseline_policies" {
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
    condition     = length(local.aw_managed_policies) == 12
    error_message = "IL5 must populate all 12 AW-managed baseline policies."
  }

  assert {
    condition = alltrue([
      for c in local.aw_managed_policies : contains(keys(local.org_policies), c)
    ])
    error_message = "Test inputs must include all 12 AW-managed policies in local.org_policies."
  }

  assert {
    condition     = !contains(keys(local._root_folder_org_policies), "compute.disableGlobalCloudArmorPolicy")
    error_message = "IL5 folder mode must exclude compute.disableGlobalCloudArmorPolicy."
  }

  assert {
    condition     = !contains(keys(local._root_folder_org_policies), "compute.disableGlobalLoadBalancing")
    error_message = "IL5 folder mode must exclude compute.disableGlobalLoadBalancing."
  }

  assert {
    condition     = !contains(keys(local._root_folder_org_policies), "compute.setNewProjectDefaultToZonalDNSOnly")
    error_message = "IL5 folder mode must exclude compute.setNewProjectDefaultToZonalDNSOnly."
  }

  assert {
    condition     = !contains(keys(local._root_folder_org_policies), "compute.skipDefaultNetworkCreation")
    error_message = "IL5 folder mode must exclude compute.skipDefaultNetworkCreation."
  }

  assert {
    condition     = !contains(keys(local._root_folder_org_policies), "gcp.resourceLocations")
    error_message = "IL5 folder mode must exclude gcp.resourceLocations."
  }

  assert {
    condition     = !contains(keys(local._root_folder_org_policies), "gcp.restrictCmekCryptoKeyProjects")
    error_message = "IL5 folder mode must exclude gcp.restrictCmekCryptoKeyProjects."
  }

  assert {
    condition     = !contains(keys(local._root_folder_org_policies), "gcp.restrictNonCmekServices")
    error_message = "IL5 folder mode must exclude gcp.restrictNonCmekServices."
  }

  assert {
    condition     = !contains(keys(local._root_folder_org_policies), "gcp.restrictServiceUsage")
    error_message = "IL5 folder mode must exclude gcp.restrictServiceUsage."
  }

  assert {
    condition     = !contains(keys(local._root_folder_org_policies), "gcp.restrictTLSVersion")
    error_message = "IL5 folder mode must exclude gcp.restrictTLSVersion."
  }

  assert {
    condition     = !contains(keys(local._root_folder_org_policies), "iam.automaticIamGrantsForDefaultServiceAccounts")
    error_message = "IL5 folder mode must exclude iam.automaticIamGrantsForDefaultServiceAccounts."
  }

  assert {
    condition     = !contains(keys(local._root_folder_org_policies), "iam.disableServiceAccountKeyCreation")
    error_message = "IL5 folder mode must exclude iam.disableServiceAccountKeyCreation."
  }

  assert {
    condition     = !contains(keys(local._root_folder_org_policies), "storage.publicAccessPrevention")
    error_message = "IL5 folder mode must exclude storage.publicAccessPrevention."
  }

  assert {
    condition     = contains(keys(local._root_folder_org_policies), "storage.uniformBucketLevelAccess")
    error_message = "IL5 folder mode must keep non-AW-managed folder policies."
  }
}

run "unspecified_regime_folder_mode_keeps_baseline_policies" {
  command = plan

  providers = {
    google      = google
    google-beta = google-beta
    local       = local
    null        = null
    time        = time
  }

  variables {
    assured_workloads = {
      regime   = "COMPLIANCE_REGIME_UNSPECIFIED"
      location = "us-east4"
    }
  }

  assert {
    condition     = length(local.aw_managed_policies) == 0
    error_message = "COMPLIANCE_REGIME_UNSPECIFIED must not exclude AW policies."
  }

  assert {
    condition     = contains(keys(local._root_folder_org_policies), "compute.disableGlobalCloudArmorPolicy")
    error_message = "Non-AW folder mode must retain compute.disableGlobalCloudArmorPolicy."
  }

  assert {
    condition     = contains(keys(local._root_folder_org_policies), "compute.disableGlobalLoadBalancing")
    error_message = "Non-AW folder mode must retain compute.disableGlobalLoadBalancing."
  }

  assert {
    condition     = contains(keys(local._root_folder_org_policies), "compute.setNewProjectDefaultToZonalDNSOnly")
    error_message = "Non-AW folder mode must retain compute.setNewProjectDefaultToZonalDNSOnly."
  }

  assert {
    condition     = contains(keys(local._root_folder_org_policies), "compute.skipDefaultNetworkCreation")
    error_message = "Non-AW folder mode must retain compute.skipDefaultNetworkCreation."
  }

  assert {
    condition     = contains(keys(local._root_folder_org_policies), "gcp.resourceLocations")
    error_message = "Non-AW folder mode must retain gcp.resourceLocations."
  }

  assert {
    condition     = contains(keys(local._root_folder_org_policies), "gcp.restrictCmekCryptoKeyProjects")
    error_message = "Non-AW folder mode must retain gcp.restrictCmekCryptoKeyProjects."
  }

  assert {
    condition     = contains(keys(local._root_folder_org_policies), "gcp.restrictNonCmekServices")
    error_message = "Non-AW folder mode must retain gcp.restrictNonCmekServices."
  }

  assert {
    condition     = contains(keys(local._root_folder_org_policies), "gcp.restrictServiceUsage")
    error_message = "Non-AW folder mode must retain gcp.restrictServiceUsage."
  }

  assert {
    condition     = contains(keys(local._root_folder_org_policies), "gcp.restrictTLSVersion")
    error_message = "Non-AW folder mode must retain gcp.restrictTLSVersion."
  }

  assert {
    condition     = contains(keys(local._root_folder_org_policies), "iam.automaticIamGrantsForDefaultServiceAccounts")
    error_message = "Non-AW folder mode must retain iam.automaticIamGrantsForDefaultServiceAccounts."
  }

  assert {
    condition     = contains(keys(local._root_folder_org_policies), "iam.disableServiceAccountKeyCreation")
    error_message = "Non-AW folder mode must retain iam.disableServiceAccountKeyCreation."
  }

  assert {
    condition     = contains(keys(local._root_folder_org_policies), "storage.publicAccessPrevention")
    error_message = "Non-AW folder mode must retain storage.publicAccessPrevention."
  }
}
