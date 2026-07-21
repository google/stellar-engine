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

variable "core_project_id" {
  description = "Core project ID."
  type        = string
}

variable "dataset_description" {
  description = "Provides a description of the deployed BigQuery Dataset."
  type        = string
}

variable "dataset_id" {
  description = "This is the dataset id."
  type        = string
}

variable "kms_key_name" {
  description = "The full self-link (projects/../locations/../keyRings/../cryptoKeys/..) of the existing KMS key to use for encryption."
  type        = string
}

variable "kms_keyring_name" {
  description = "KMS Keyring."
  type        = string
}

variable "main_project_id" {
  description = "Project ID."
  type        = string
}

variable "region" {
  description = "GCP Region to deploy into."
  type        = string
}

variable "tables" {
  description = "BigQuery tables."
  type = map(object({
    deletion_protection      = optional(bool)
    description              = optional(string, "Terraform managed.")
    friendly_name            = optional(string)
    labels                   = optional(map(string), {})
    require_partition_filter = optional(bool)
    schema                   = optional(string)
    external_data_configuration = optional(object({
      autodetect                = bool
      source_uris               = list(string)
      avro_logical_types        = optional(bool)
      compression               = optional(string)
      connection_id             = optional(string)
      file_set_spec_type        = optional(string)
      ignore_unknown_values     = optional(bool)
      metadata_cache_mode       = optional(string)
      object_metadata           = optional(string)
      json_options_encoding     = optional(string)
      reference_file_schema_uri = optional(string)
      schema                    = optional(string)
      source_format             = optional(string)
      max_bad_records           = optional(number)
      csv_options = optional(object({
        quote                 = string
        allow_jagged_rows     = optional(bool)
        allow_quoted_newlines = optional(bool)
        encoding              = optional(string)
        field_delimiter       = optional(string)
        skip_leading_rows     = optional(number)
      }))
      google_sheets_options = optional(object({
        range             = optional(string)
        skip_leading_rows = optional(number)
      }))
      hive_partitioning_options = optional(object({
        mode                     = optional(string)
        require_partition_filter = optional(bool)
        source_uri_prefix        = optional(string)
      }))
      parquet_options = optional(object({
        enum_as_string        = optional(bool)
        enable_list_inference = optional(bool)
      }))

    }))
    options = optional(object({
      clustering      = optional(list(string))
      encryption_key  = optional(string)
      expiration_time = optional(number)
      max_staleness   = optional(string)
    }), {})
    partitioning = optional(object({
      field = optional(string)
      range = optional(object({
        end      = number
        interval = number
        start    = number
      }))
      time = optional(object({
        type          = string
        expiration_ms = optional(number)
        field         = optional(string)
      }))
    }))
    table_constraints = optional(object({
      primary_key_columns = optional(list(string))
      foreign_keys = optional(object({
        referenced_table = object({
          project_id = string
          dataset_id = string
          table_id   = string
        })
        column_references = object({
          referencing_column = string
          referenced_column  = string
        })
        name = optional(string)
      }))
    }))
  }))
}
