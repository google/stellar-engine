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
  project_id                 = "my-project"
  network_self_link          = "projects/my-project/global/networks/my-vpc"
  private_service_connect_ip = "10.3.0.5"
  forwarding_rule_target     = "vpc-sc"
}

run "plan_vpc_sc_default" {
  command = plan

  assert {
    condition     = local.googleapis_url == "restricted.googleapis.com."
    error_message = "Expected restricted.googleapis.com. when forwarding_rule_target is vpc-sc."
  }

  assert {
    condition     = local.recordsets_name == "restricted"
    error_message = "Expected restricted recordset prefix for vpc-sc target."
  }

  assert {
    condition     = google_compute_global_forwarding_rule.forwarding_rule_private_service_connect.target == "vpc-sc"
    error_message = "Expected vpc-sc forwarding rule target."
  }

  assert {
    condition     = google_compute_global_forwarding_rule.forwarding_rule_private_service_connect.allow_psc_global_access == false
    error_message = "Expected allow_psc_global_access to default to false."
  }

  assert {
    condition     = module.googleapis.zone.name == "dz-apis"
    error_message = "Expected dz-apis private DNS zone name."
  }

  assert {
    condition     = module.gcr.zone.dns_name == "gcr.io."
    error_message = "Expected gcr.io. private DNS domain."
  }

  assert {
    condition     = module.pkg-dev.zone.dns_name == "pkg.dev."
    error_message = "Expected pkg.dev. private DNS domain."
  }
}

run "plan_all_apis_with_global_access_and_service_directory" {
  command = plan

  variables {
    dns_code                    = ""
    forwarding_rule_target      = "all-apis"
    psc_global_access           = true
    service_directory_namespace = "psc-ns"
    service_directory_region    = "us-east4"
  }

  assert {
    condition     = local.googleapis_url == "private.googleapis.com."
    error_message = "Expected private.googleapis.com. when forwarding_rule_target is all-apis."
  }

  assert {
    condition     = module.googleapis.zone.name == "apis"
    error_message = "Expected empty dns_code to omit the hyphen prefix."
  }

  assert {
    condition     = google_compute_global_forwarding_rule.forwarding_rule_private_service_connect.allow_psc_global_access == true
    error_message = "Expected allow_psc_global_access to reflect true."
  }

  assert {
    condition     = length(google_compute_global_forwarding_rule.forwarding_rule_private_service_connect.service_directory_registrations) == 1
    error_message = "Expected service_directory_registrations block when namespace or region is set."
  }
}

run "rejects_invalid_forwarding_rule_target" {
  command = plan

  variables {
    forwarding_rule_target = "invalid-target"
  }

  expect_failures = [
    var.forwarding_rule_target
  ]
}
