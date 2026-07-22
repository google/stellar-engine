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

resource "google_workflows_workflow" "workflow" {
  depends_on = [
    google_project_iam_binding.bindings,
  ]
  name                = var.name
  region              = var.region
  description         = var.description
  service_account     = var.service_account
  call_log_level      = var.logging_level
  deletion_protection = var.deletion_protection
  user_env_vars       = var.env_vars
  crypto_key_name     = var.kms_key_self_link # Note: the resource argument is 'crypto_key_name', but it takes the self-link

  source_contents = file(var.file)
}
