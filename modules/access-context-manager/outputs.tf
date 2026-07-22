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

output "access_levels" {
  description = "The list of created access levels."
  value = {
    for access_level in google_access_context_manager_access_level.access_levels : access_level.name => {
      id          = access_level.id
      name        = access_level.name
      description = access_level.description
    }
  }
}

output "service_perimeters" {
  description = "The list of created service perimeters."
  value = {
    for perimeter in google_access_context_manager_service_perimeter.service_perimeters : perimeter.name => {
      id          = perimeter.id
      name        = perimeter.name
      description = perimeter.description
    }
  }
}