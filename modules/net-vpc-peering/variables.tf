/**
 * Copyright 2026 Google LLC
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
variable "local_network" {
  description = "The full resource link (self-link) of the local VPC network for the peering connection."
  type        = string
}

variable "name" {
  description = "Optional names for the peering resources (local and peer sides). If not set, peering names will be generated based on the network names and prefix."
  type = object({
    local = optional(string)
    peer  = optional(string)
  })
  default  = {}
  nullable = false
}

variable "peer_create_peering" {
  description = "Set to `true` to create the peering connection from the peer side as well. If `false`, only the peering from the local network to the peer network is created (requires manual setup on the peer side)."
  type        = bool
  default     = true
}

variable "peer_network" {
  description = "The full resource link (self-link) of the peer VPC network for the peering connection."
  type        = string
}

variable "prefix" {
  description = "An optional name prefix for the network peerings. For example, 'prod-peering'."
  type        = string
  default     = null
  validation {
    condition     = var.prefix != ""
    error_message = "Prefix cannot be an empty string, please use `null` instead."
  }
}

variable "routes_config" {
  description = "Control import/export of custom and subnet routes with public IP for local and peer networks. Peer configuration is only used when `peer_create_peering` is `true`."
  type = object({
    local = optional(object({
      export        = optional(bool, true)
      import        = optional(bool, true)
      public_export = optional(bool)
      public_import = optional(bool)
    }), {})
    peer = optional(object({
      export        = optional(bool, true)
      import        = optional(bool, true)
      public_export = optional(bool)
      public_import = optional(bool)
    }), {})
  })
  nullable = false
  default  = {}
}

variable "stack_type" {
  description = "IP version(s) of traffic and routes that are allowed to be imported or exported between peer networks. Possible values: `IPV4_ONLY`, `IPV4_IPV6`."
  type        = string
  default     = null
  validation {
    condition     = var.stack_type == "IPV4_ONLY" || var.stack_type == "IPV4_IPV6" || var.stack_type == null
    error_message = "The `stack_type` must be either 'IPV4_ONLY', 'IPV4_IPV6', or `null`."
  }
}

