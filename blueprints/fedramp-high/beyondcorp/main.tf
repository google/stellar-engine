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

module "beyondcorp" {
  source              = "../../../modules/beyondcorp"
  project_id          = var.main_project_id
  region              = var.region
  organization_id     = var.organization_id
  oauth_client_id     = var.oauth_client_id
  oauth_client_secret = var.oauth_client_secret
  iap_user_email      = var.iap_user_email
  endpoint_name       = var.endpoint_name
  policy_title        = var.policy_title
}