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
  # machine (service accounts) IAM bindings, in logical format
  # the service account module's "magic" outputs allow us to use dynamic values
  iam_sa_bindings = {
    (module.automation-tf-bootstrap-sa.iam_email) = {
      additive = concat(
        [
          "roles/essentialcontacts.admin",
          "roles/logging.admin",
          "roles/resourcemanager.organizationAdmin",
          "roles/resourcemanager.projectCreator",
          "roles/resourcemanager.projectMover",
          "roles/resourcemanager.tagAdmin",
          "roles/assuredworkloads.admin",
          "roles/iam.organizationRoleAdmin",
          # "roles/orgpolicy.policyAdmin",
          # "organizations/${var.organization.id}/roles/storageViewer",
          # "roles/viewer",
          # "roles/assuredworkloads.reader",
          # "roles/serviceusage.serviceUsageViewer",
          # "roles/bigquery.user",
          # "roles/compute.viewer",
          # "roles/logging.viewer",
          # "roles/iam.serviceAccountTokenCreator",
          # "roles/cloudkms.viewer",
          # "roles/policyanalyzer.activityAnalysisViewer" # TODO DELETE - here to test
        ],
        local.billing_mode != "org" ? [] : [
          "roles/billing.admin"
        ]
      )
    }
    (module.automation-tf-bootstrap-r-sa.iam_email) = {
      additive = concat(
        [
          # the organizationAdminViewer custom role is granted via the SA module
          "roles/iam.organizationRoleViewer",
          "roles/orgpolicy.policyViewer",
          "roles/essentialcontacts.viewer",
          "roles/logging.viewer",
          "roles/resourcemanager.folderViewer",
          "roles/resourcemanager.tagViewer",
          "roles/assuredworkloads.reader"
        ],
        local.billing_mode != "org" ? [] : [
          "roles/billing.viewer"
        ]
      )
    }
    (module.automation-tf-resman-sa.iam_email) = {
      additive = concat(
        [
          "roles/orgpolicy.policyAdmin",
          "roles/assuredworkloads.admin",
          "roles/logging.admin",
          "roles/resourcemanager.folderAdmin",
          "roles/resourcemanager.projectCreator",
          "roles/resourcemanager.tagAdmin",
          "roles/resourcemanager.tagUser",
          "roles/resourcemanager.organizationAdmin"
        ],
        local.billing_mode != "org" ? [] : [
          "roles/billing.admin"
        ]
      )
    }
    (module.automation-tf-resman-r-sa.iam_email) = {
      additive = concat(
        [
          # the organizationAdminViewer custom role is granted via the SA module
          "roles/orgpolicy.policyViewer",
          "roles/assuredworkloads.reader",
          "roles/logging.viewer",
          "roles/resourcemanager.folderViewer",
          "roles/resourcemanager.tagViewer",
          "roles/serviceusage.serviceUsageViewer"
        ],
        local.billing_mode != "org" ? [] : [
          "roles/billing.viewer",

        ]
      )
    }
    (module.automation-tf-tenants-sa.iam_email) = {
      additive = concat(
        [
          "roles/orgpolicy.policyAdmin",
          "roles/assuredworkloads.admin",
          "roles/logging.admin",
          "roles/resourcemanager.folderAdmin",
          "roles/resourcemanager.projectCreator",
          "roles/resourcemanager.tagAdmin",
          "roles/resourcemanager.tagUser",
          "roles/resourcemanager.organizationAdmin",
          "roles/compute.networkAdmin",
          "roles/compute.xpnAdmin",
          "roles/dns.admin",
          "roles/networkconnectivity.hubAdmin"
        ],
        local.billing_mode != "org" ? [] : [
          "roles/billing.user"
        ]
      )
    }
    (module.automation-tf-tenants-r-sa.iam_email) = {
      additive = concat(
        [],
        local.billing_mode != "org" ? [] : [
          "roles/billing.viewer"
        ]
      )
    }
  }
  # TODO - look at this
  # bootstrap user bindings
  iam_user_bootstrap_bindings = var.bootstrap_user == null ? {} : {
    "user:${var.bootstrap_user}" = {
      # TODO: align additive roles with the README
      additive = concat(
        [
          "roles/logging.admin",
          "roles/owner",
          "roles/resourcemanager.organizationAdmin",
          "roles/resourcemanager.projectCreator",
          "roles/resourcemanager.tagAdmin"
        ],
        local.billing_mode != "org" ? [] : [
          "roles/billing.admin"
        ]
      )
    }
  }
}
