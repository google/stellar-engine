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
  main_project_id                  = "xxxx-xxxx-main-0"
  gcp_region                       = "us-east4"
  local_vpc_name                   = "my-local-vpc"
  local_vpc_project_id             = "xxxx-xxxx-local-project"
  local_subnetwork_prefix_name     = "local-subnet"
  local_subnetwork_cidr_a          = "10.100.0.0/24"
  local_subnetwork_cidr_b          = "10.100.1.0/24"
  local_subnetwork_cidr_c          = "10.100.2.0/24"
  local_secondary_ip_ranges_cidr_a = "192.168.0.0/24"
  local_secondary_ip_ranges_cidr_b = "192.168.1.0/24"
  peer_vpc_name_to_create          = "my-peer-vpc"
  peer_vpc_project_id_to_create    = "xxxx-xxxx-peer-project"
  peer_subnetwork_prefix_name      = "peer-subnet"
  peer_subnetwork_cidr_a           = "10.200.0.0/24"
  peer_subnetwork_cidr_b           = "10.200.1.0/24"
  peer_subnetwork_cidr_c           = "10.200.2.0/24"
  peer_secondary_ip_ranges_cidr_a  = "192.168.2.0/24"
  peer_secondary_ip_ranges_cidr_b  = "192.168.3.0/24"
}

run "plan_secondary_ip_ranges_from_string_cidrs" {
  command = plan

  assert {
    condition = module.vpc-networks["local"].subnet_secondary_ranges["us-east4/local-subnet-c-secondary-ranges"] == {
      a = "192.168.0.0/24"
      b = "192.168.1.0/24"
    }
    error_message = "Expected local subnet c to have secondary ranges a and b from the string CIDR inputs."
  }

  assert {
    condition = module.vpc-networks["peer"].subnet_secondary_ranges["us-east4/peer-subnet-c-secondary-ranges"] == {
      a = "192.168.2.0/24"
      b = "192.168.3.0/24"
    }
    error_message = "Expected peer subnet c to have secondary ranges a and b from the string CIDR inputs."
  }
}
