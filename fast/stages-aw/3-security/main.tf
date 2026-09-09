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

locals {
  # additive IAM binding for delegated KMS admins
  kms_restricted_admin_template = {
    role = "roles/cloudkms.admin"
    condition = {
      title       = "kms_sa_delegated_grants"
      description = "Automation service account delegated grants."
      expression = format(
        <<-EOT
           api.getAttribute('iam.googleapis.com/modifiedGrantsByRole', []).hasOnly([%s]) &&
           resource.type == 'cloudkms.googleapis.com/CryptoKey'
        EOT
        , join(",", formatlist("'%s'", [
          "roles/cloudkms.cryptoKeyEncrypterDecrypter",
          "roles/cloudkms.cryptoKeyEncrypterDecrypterViaDelegation"
        ]))
      )
    }
  }

  # list of locations with keys
  kms_locations = distinct(flatten([
    for k, v in var.kms_keys : v.locations
  ]))
  # map { location -> { key_name -> key_details } }
  # Keys that do not set their own version_template inherit the stage-wide
  # protection level here. modules/kms only honours version_template per key
  # (its keyring object is {location, name}), so this is the only place the
  # stage can apply var.kms_protection_level.
  kms_locations_keys = {
    for loc in local.kms_locations :
    loc => {
      for k, v in var.kms_keys :
      k => merge(v, {
        version_template = (
          v.version_template != null
          ? v.version_template
          : var.kms_protection_level == null
          ? null
          : {
            algorithm        = "GOOGLE_SYMMETRIC_ENCRYPTION"
            protection_level = var.kms_protection_level
          }
        )
      })
      if contains(v.locations, loc)
    }
  }
  project_services = [
    "cloudkms.googleapis.com",
    "secretmanager.googleapis.com",
    "stackdriver.googleapis.com"
  ]
}

module "folder" {
  source        = "../../../modules/folder"
  parent        = "organizations/${var.organization.id}"
  name          = "Security"
  folder_create = var.folder_ids.security == null
  id            = var.folder_ids.security
  contacts = (
    var.essential_contacts == null
    ? {}
    : { (var.essential_contacts) = ["ALL"] }
  )
}
