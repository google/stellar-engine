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
  main_project_id = "my-project"
  network_name    = "projects/my-project/global/networks/my-vpc"
  region          = "us-east4"
}

run "plan_default_vpc_sc" {
  command = plan

  assert {
    condition     = module.psc.forwarding_rule_target == "vpc-sc"
    error_message = "Expected default service target vpc-sc."
  }

  assert {
    condition     = module.psc.private_service_connect_ip == "10.5.5.5"
    error_message = "Expected default PSC IP address."
  }

  assert {
    condition     = module.psc.private_service_connect_name == "psconnect-ip"
    error_message = "Expected default PSC endpoint name."
  }
}

run "plan_all_apis_override" {
  command = plan

  variables {
    address = "10.9.9.9"
    service = "all-apis"
  }

  assert {
    condition     = module.psc.forwarding_rule_target == "all-apis"
    error_message = "Expected all-apis forwarding rule target override."
  }

  assert {
    condition     = module.psc.private_service_connect_ip == "10.9.9.9"
    error_message = "Expected custom PSC IP override."
  }
}

run "rejects_invalid_service" {
  command = plan

  variables {
    service = "invalid-service"
  }

  expect_failures = [
    var.service
  ]
}
