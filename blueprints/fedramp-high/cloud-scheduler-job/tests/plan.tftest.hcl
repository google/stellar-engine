# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

mock_provider "google" {
  mock_data "google_project" {
    defaults = {
      number     = "123456789012"
      project_id = "my-project"
    }
  }
}

mock_provider "google-beta" {
  mock_resource "google_project_service_identity" {
    defaults = {
      email  = "service-123456789012@gcp-sa-cloudscheduler.iam.gserviceaccount.com"
      member = "serviceAccount:service-123456789012@gcp-sa-cloudscheduler.iam.gserviceaccount.com"
    }
  }
}

variables {
  description     = "Scheduled trigger"
  gcp_region      = "us-east4"
  main_project_id = "my-scheduler-project"
  name            = "daily-job"
  schedule        = "0 * * * *"
  topic_id        = "projects/my-pubsub-project/topics/target-topic"
}

run "plan_with_null_data_and_pubsub_publisher_grant" {
  command = apply

  assert {
    condition     = local.pubsub_data == null
    error_message = "Null data must pass null to pubsub_target without crashing base64encode."
  }

  assert {
    condition     = google_pubsub_topic_iam_member.scheduler_publisher.project == "my-pubsub-project" && google_pubsub_topic_iam_member.scheduler_publisher.role == "roles/pubsub.publisher" && google_pubsub_topic_iam_member.scheduler_publisher.member == "serviceAccount:service-123456789012@gcp-sa-cloudscheduler.iam.gserviceaccount.com"
    error_message = "Cloud Scheduler service agent must receive roles/pubsub.publisher on the target topic."
  }
}

run "plan_encodes_plaintext_data_once" {
  command = plan

  variables {
    data = "hello"
  }

  assert {
    condition     = local.pubsub_data == base64encode("hello")
    error_message = "Plaintext data must be base64-encoded once."
  }
}

run "plan_preserves_preencoded_base64_data" {
  command = plan

  variables {
    data           = "aGVsbG8="
    data_is_base64 = true
  }

  assert {
    condition     = local.pubsub_data == "aGVsbG8="
    error_message = "Pre-encoded base64 data must not be double-encoded."
  }
}

run "rejects_short_topic_id" {
  command = plan

  variables {
    topic_id = "target-topic"
  }

  expect_failures = [
    var.topic_id,
  ]
}

run "plan_cross_project_topic_cmek_uses_topic_project_service_agent" {
  command = apply

  variables {
    kms_key_name = "projects/my-core-project/locations/us-east4/keyRings/my-kr/cryptoKeys/default"
  }

  override_data {
    target = data.google_project.topic
    values = {
      number     = "999888777666"
      project_id = "my-pubsub-project"
    }
  }

  assert {
    condition     = data.google_project.topic.project_id == "my-pubsub-project" && google_kms_crypto_key_iam_member.pubsub[0].member == "serviceAccount:service-999888777666@gcp-sa-pubsub.iam.gserviceaccount.com"
    error_message = "CMEK IAM grant must target the Pub/Sub service agent of local.topic_project_id, not main_project_id."
  }

  assert {
    condition     = google_pubsub_topic_iam_member.scheduler_publisher.member == "serviceAccount:service-123456789012@gcp-sa-cloudscheduler.iam.gserviceaccount.com"
    error_message = "Cloud Scheduler service agent must remain in main_project_id."
  }
}
