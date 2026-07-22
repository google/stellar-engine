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
  description = "Unencoded data to be sent."
  type        = string
  default     = ""
}

variable "description" {
  description = "Description of job."
  type        = string
}

variable "kms_key_name" {
  description = "Full path to KMS key for pubsub."
  type        = string
  default     = null
}

variable "main_project_id" {
  description = "Project id."
  type        = string
}

variable "name" {
  description = "Name of the Cloud Scheduler job."
  type        = string
}

variable "new_topic_name" {
  description = "Name for new PubSub topic if creating one."
  type        = string
  default     = null
}

variable "region" {
  description = "Location to deploy job."
  type        = string
}

variable "retry_count" {
  description = "Number of retries."
  type        = number
  default     = null
}

variable "schedule" {
  description = "Schedule to implement the job -- use cron-based syntax."
  type        = string
}

variable "topic_id" {
  description = "PubSub topic ID."
  type        = string
  default     = null
}