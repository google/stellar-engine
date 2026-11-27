/**
 * Copyright 2022 Google LLC
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

/******************************************
  Private Google APIs DNS Zone & records.
 *****************************************/

module "googleapis" {
  source      = "../dns"
  project_id  = var.project_id
  name        = "${local.dns_code}apis"
  description = "Private DNS zone to configure ${local.googleapis_url}"
  zone_config = {
    domain = "googleapis.com."
    private = {
      client_networks = [var.network_self_link]
    }
  }
  recordsets = {
    "CNAME *" = {
      ttl     = 300
      records = [local.googleapis_url]
    }
    "A ${local.recordsets_name}" = {
      ttl     = 300
      records = [var.private_service_connect_ip]
    }
  }
}

/******************************************
  GCR DNS Zone & records.
 *****************************************/

module "gcr" {
  source      = "../dns"
  project_id  = var.project_id
  name        = "${local.dns_code}gcr"
  description = "Private DNS zone to configure gcr.io"
  zone_config = {
    domain = "gcr.io."
    private = {
      client_networks = [var.network_self_link]
    }
  }
  recordsets = {
    "CNAME *" = {
      ttl     = 300
      records = ["gcr.io."]
    }
    "A " = {
      ttl     = 300
      records = [var.private_service_connect_ip]
    }
  }
}

/***********************************************
  Artifact Registry DNS Zone & records.
 ***********************************************/

moved {
  from = module.pkg_dev
  to   = module.pkg-dev
}

module "pkg-dev" {
  source      = "../dns"
  project_id  = var.project_id
  name        = "${local.dns_code}pkg-dev"
  description = "Private DNS zone to configure pkg.dev"
  zone_config = {
    domain = "pkg.dev."
    private = {
      client_networks = [var.network_self_link]
    }
  }
  recordsets = {
    "CNAME *" = {
      ttl     = 300
      records = ["pkg.dev."]
    }
    "A " = {
      ttl     = 300
      records = [var.private_service_connect_ip]
    }
  }
}