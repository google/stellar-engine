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

variable "data" {
  description = "The base64-encoded data to be sent as the Pub/Sub message payload."
  type        = string
  default     = null
}

variable "description" {
  description = "Description of the Cloud Scheduler job."
  type        = string
}

variable "kms_key_name" {
  description = "The full resource path of the existing Cloud KMS CryptoKey used for CMEK on the Pub/Sub topic. This key is assumed to be in the `core_project_id`."
  type        = string
  default     = null
}

variable "main_project_id" {
  description = "The Google Cloud Project ID where the Cloud Scheduler job will be created."
  type        = string
}

variable "max_backoff_duration" {
  description = "The maximum amount of time to wait before retrying a failed attempt, as a duration string (e.g., '5s', '2m', '1h')."
  type        = string
  default     = null
}

variable "max_doublings" {
  description = "The maximum number of times to double the retry delay, up to `max_retry_duration`."
  type        = number
  default     = null
}

variable "max_retry_duration" {
  description = "The maximum cumulative time in which retries are attempted, as a duration string."
  type        = string
  default     = null
}

variable "min_backoff_duration" {
  description = "The minimum amount of time to wait before retrying a failed attempt, as a duration string."
  type        = string
  default     = null
}

variable "name" {
  description = "The name of the Cloud Scheduler job."
  type        = string
}

variable "gcp_region" {
  description = "The Google Cloud region where the Cloud Scheduler job will be deployed."
  type        = string
}

variable "retry_count" {
  description = "The number of attempts that the system will make to run the job if the first attempt fails. Retries are attempted over a longer period of time than the schedule."
  type        = number
  default     = null
}

variable "schedule" {
  description = "The schedule in the [Crontab format](https://en.wikipedia.org/wiki/Cron#CRON_expression) (e.g., '*/2 * * * *' for every two minutes)."
  type        = string
}

variable "topic_id" {
  description = "The full resource path of the existing Pub/Sub topic (e.g., `projects/<PROJECT_ID>/topics/<TOPIC_NAME>`) to which messages will be published."
  type        = string
}

