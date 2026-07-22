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

output "firestore_earliest_version_time" {
  value       = module.firestore.firestore_database.earliest_version_time
  description = "The earliest timestamp at which older versions of the data can be read from the database."
}

output "firestore_etag" {
  value       = module.firestore.firestore_database.etag
  description = "This checksum is computed by the server based on the value of other fields."
}

output "firestore_id" {
  value       = module.firestore.firestore_database.id
  description = "The identifier for the Firestore resource."
}

output "firestore_uid" {
  value       = module.firestore.firestore_database.uid
  description = "The system-generated UUID4 for this Database."
}


output "firestore_version_retention_period" {
  value       = module.firestore.firestore_database.version_retention_period
  description = "The period during which past versions of data are retained in the database."
}