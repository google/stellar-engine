# Copyright 2025 Google LLC
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

locals {
  _yaml_doc = (
    var.indexes != null || var.index_file == null
    ? null
    : yamldecode(file("${path.module}/${var.index_file}"))
  )
  _raw_indexes = [
    for idx in try([for i in local._yaml_doc.indexes : i], []) : {
      kind = tostring(idx.kind)
      ancestor = lower(
        try(idx.ancestor, null) == null ? "no" : tostring(idx.ancestor)
      )
      properties = [
        for p in try([for prop in idx.properties : prop], []) : {
          name = tostring(p.name)
          direction = upper(
            try(p.direction, null) == null ? "asc" : tostring(p.direction)
          )
        }
      ]
    }
  ]
  _yaml_index_entries = [
    for idx in local._raw_indexes : {
      key = format(
        "%s-%s-%s",
        idx.kind,
        contains(["yes", "true"], idx.ancestor) ? "anc" : "noanc",
        join("-", [
          for p in idx.properties : format(
            "%s-%s",
            p.name,
            contains(["DESC", "DESCENDING"], p.direction) ? "desc" : "asc"
          )
        ])
      )
      value = {
        api_scope = "DATASTORE_MODE_API"
        query_scope = (
          contains(["yes", "true"], idx.ancestor)
          ? "COLLECTION_RECURSIVE"
          : "COLLECTION_GROUP"
        )
        collection = idx.kind
        fields = [
          for p in idx.properties : {
            field_path    = p.name
            array_config  = null
            vector_config = null
            order = (
              contains(["DESC", "DESCENDING"], p.direction)
              ? "DESCENDING"
              : "ASCENDING"
            )
          }
        ]
      }
    }
  ]
  _yaml_index_groups = {
    for entry in local._yaml_index_entries : entry.key => entry.value...
  }
  _yaml_indexes = {
    for key, group in local._yaml_index_groups : key => group[0]
  }
  indexes = var.indexes != null ? var.indexes : local._yaml_indexes
}

resource "google_project_service" "apis" {
  for_each = toset([
    "datastore.googleapis.com",
    "firestore.googleapis.com",
  ])
  project            = var.main_project_id
  service            = each.value
  disable_on_destroy = false
  lifecycle {
    precondition {
      condition = alltrue([
        for idx in local._raw_indexes :
        contains(["no", "false", "yes", "true"], idx.ancestor)
      ])
      error_message = "Index ancestor attribute must be one of no, false, yes, or true."
    }
    precondition {
      condition = alltrue(flatten([
        for idx in local._raw_indexes : [
          for p in idx.properties :
          contains(["ASC", "ASCENDING", "DESC", "DESCENDING"], p.direction)
        ]
      ]))
      error_message = "Index property direction must be one of asc, ascending, desc, or descending."
    }
    precondition {
      condition     = length(local._yaml_index_groups) == length(local._raw_indexes)
      error_message = "Duplicate index definitions in index_file produce duplicate resource keys."
    }
  }
}

resource "google_project_service_identity" "firestore" {
  count      = var.kms_key_name == null ? 0 : 1
  provider   = google-beta
  project    = var.main_project_id
  service    = "firestore.googleapis.com"
  depends_on = [google_project_service.apis]
}

resource "google_kms_crypto_key_iam_member" "firestore_cmek" {
  count         = var.kms_key_name == null ? 0 : 1
  crypto_key_id = var.kms_key_name
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = google_project_service_identity.firestore[0].member
}

module "firestore" {
  source          = "../../../modules/firestore"
  project_id      = var.main_project_id
  database_create = var.database_create
  database = {
    name                        = var.database_name
    location_id                 = var.region
    type                        = "DATASTORE_MODE"
    app_engine_integration_mode = var.app_engine_integration_mode
    concurrency_mode            = var.concurrency_mode
    delete_protection_state = (
      var.deletion_protection
      ? "DELETE_PROTECTION_ENABLED"
      : "DELETE_PROTECTION_DISABLED"
    )
    deletion_policy = var.deletion_policy
    kms_key_name    = var.kms_key_name
  }
  backup_schedule = var.backup_schedule
  indexes         = {}
  depends_on = [
    google_project_service.apis,
    google_kms_crypto_key_iam_member.firestore_cmek,
  ]
}

# Managed here until upstream CFF modules/firestore wires api_scope and query_scope (#659).
resource "google_firestore_index" "firestore_indexes" {
  for_each    = local.indexes
  project     = var.main_project_id
  database    = var.database_create ? module.firestore.firestore_database.name : var.database_name
  collection  = each.value.collection
  api_scope   = each.value.api_scope
  query_scope = each.value.query_scope

  dynamic "fields" {
    for_each = each.value.fields
    content {
      field_path   = fields.value.field_path
      order        = fields.value.order
      array_config = fields.value.array_config
      dynamic "vector_config" {
        for_each = fields.value.vector_config == null ? [] : [""]
        content {
          dimension = fields.value.vector_config.dimension
          dynamic "flat" {
            for_each = coalesce(fields.value.vector_config.flat, false) ? [""] : []
            content {}
          }
        }
      }
    }
  }

  depends_on = [google_project_service.apis]
}
