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

module "access_context_manager" {
  source = "../../../modules/access-context-manager"

  project_id          = var.main_project_id
  domain              = var.domain
  region              = var.region
  access_policy_title = var.access_policy_title
  access_levels       = var.access_levels
  service_perimeters  = var.service_perimeters
  organization_id     = var.organization_id
}

