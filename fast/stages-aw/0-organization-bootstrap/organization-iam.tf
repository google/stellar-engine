/**
 * Copyright 2023 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

# tfdoc:file:description Organization-level IAM bindings locals.

locals {
  # IAM roles in the org to reset (remove principals)
  iam_delete_roles = [
    "roles/billing.creator"
  ]
  # domain IAM bindings
  iam_domain_bindings = var.organization.domain == null ? {} : {
    "domain:${var.organization.domain}" = {
      authoritative = ["roles/browser"]
      additive      = []
    }
  }
  # human (groups) IAM bindings
  iam_principal_bindings = {
    (local.principals.gcp-billing-admins) = {
      authoritative = []
      additive = (
        local.billing_mode != "org" ? [] : [
          "roles/billing.admin"
        ]
      )
    }
    (local.principals.gcp-vpc-network-admins) = {
      authoritative = [
        "roles/cloudasset.owner",
        "roles/cloudsupport.techSupportEditor",
      ]
      additive = [
        "roles/compute.orgFirewallPolicyAdmin",
        "roles/compute.xpnAdmin"
      ]
    }
    (local.principals.gcp-organization-admins) = {
      authoritative = [
        "roles/axt.admin",
        "roles/cloudasset.owner",
        "roles/cloudsupport.admin",
        "roles/compute.osAdminLogin",
        "roles/compute.osLoginExternalUser",
        "roles/owner",
        "roles/iam.workforcePoolAdmin",
      ]
      additive = concat(
        [
          "roles/assuredworkloads.admin",
          "roles/resourcemanager.folderAdmin",
          "roles/resourcemanager.organizationAdmin",
          "roles/resourcemanager.projectCreator",
          "roles/resourcemanager.tagAdmin",
          "roles/orgpolicy.policyAdmin"
        ],
        local.billing_mode != "org" ? [] : [
          "roles/billing.admin"
        ]
      )
    }
    (local.principals.gcp-security-admins) = {
      authoritative = [
        "roles/cloudasset.owner",
        "roles/cloudsupport.techSupportEditor",
        "roles/iam.securityReviewer",
        "roles/logging.admin",
        "roles/securitycenter.admin",
      ]
      additive = [
        "roles/accesscontextmanager.policyAdmin",
        "roles/iam.organizationRoleAdmin",
        "roles/orgpolicy.policyAdmin",
      ]
    }
    (local.principals.gcp-support) = {
      authoritative = [
        "roles/cloudsupport.techSupportEditor",
        "roles/monitoring.viewer",
      ]
      additive = [
        "roles/logging.viewer",
      ]
    }
  }
}
