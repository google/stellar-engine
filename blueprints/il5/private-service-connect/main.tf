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

module "psc" {
  source                       = "../../../modules/private-service-connect"
  project_id                   = var.main_project_id
  service_directory_region     = var.region
  private_service_connect_name = var.ip_name
  forwarding_rule_name         = var.psc_name
  network_self_link            = var.network_name
  private_service_connect_ip   = var.address
  forwarding_rule_target       = var.service
  dns_code                     = var.dns_code
  psc_global_access            = false
}