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

mock_provider "google" {}

mock_provider "google-beta" {}

variables {
  project_id = "my-project"
  location   = "us-east4"
  cluster_id = "test-cluster"
  capacity_config = {
    vcpu_count   = 3
    memory_bytes = 3221225472
  }
  subnets = [
    "projects/my-project/regions/us-east4/subnetworks/test-subnet",
  ]
}

run "plan_without_rebalance_mode" {
  command = plan

  assert {
    condition     = length(google_managed_kafka_cluster.cluster.rebalance_config) == 0
    error_message = "Expected no rebalance_config block when rebalance_mode is null."
  }
}

run "plan_with_auto_rebalance_on_scale_up" {
  command = plan

  variables {
    rebalance_mode = "AUTO_REBALANCE_ON_SCALE_UP"
  }

  assert {
    condition     = length(google_managed_kafka_cluster.cluster.rebalance_config) == 1
    error_message = "Expected one rebalance_config block when rebalance_mode is set."
  }

  assert {
    condition     = google_managed_kafka_cluster.cluster.rebalance_config[0].mode == "AUTO_REBALANCE_ON_SCALE_UP"
    error_message = "Expected rebalance_config.mode to equal var.rebalance_mode."
  }
}

run "plan_with_no_rebalance" {
  command = plan

  variables {
    rebalance_mode = "NO_REBALANCE"
  }

  assert {
    condition     = google_managed_kafka_cluster.cluster.rebalance_config[0].mode == "NO_REBALANCE"
    error_message = "Expected rebalance_config.mode to equal var.rebalance_mode."
  }
}
