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

override_data {
  target = data.google_compute_network.existing_vpc
  values = {
    id        = "projects/test-hub/global/networks/existing-stage2-vpc"
    self_link = "https://www.googleapis.com/compute/v1/projects/test-hub/global/networks/existing-stage2-vpc"
  }
}

variables {
  hub_project_id      = "test-hub"
  network_name        = "test-bcap-vpc"
  region1             = "us-central1"
  region2             = "us-east4"
  dod_base_cidr_block = "10.0.0.0/24"
  subnet_configs = {
    subnet1 = {
      name = "bcap-dod-subnet-primary"
    }
    subnet2 = {
      name = "bcap-dod-subnet-secondary"
    }
  }
  router_configs = {
    router1 = {
      name = "bcap-router-primary"
    }
    router2 = {
      name = "bcap-router-secondary"
    }
  }
  attachment_configs = {
    router1-attachment1 = {
      name                     = "bcap-r1-ad1"
      router_key               = "router1"
      edge_availability_domain = "AVAILABILITY_DOMAIN_1"
    }
    router1-attachment2 = {
      name                     = "bcap-r1-ad2"
      router_key               = "router1"
      edge_availability_domain = "AVAILABILITY_DOMAIN_2"
    }
    router2-attachment1 = {
      name                     = "bcap-r2-ad1"
      router_key               = "router2"
      edge_availability_domain = "AVAILABILITY_DOMAIN_1"
    }
    router2-attachment2 = {
      name                     = "bcap-r2-ad2"
      router_key               = "router2"
      edge_availability_domain = "AVAILABILITY_DOMAIN_2"
    }
  }
}

run "plan_default_two_region_create_vpc" {
  command = plan

  assert {
    condition     = length(google_compute_network.vpc_network) == 1
    error_message = "Expected a new VPC network when create_vpc is true."
  }

  assert {
    condition     = length(data.google_compute_network.existing_vpc) == 0
    error_message = "Expected no existing VPC lookup when create_vpc is true."
  }

  assert {
    condition     = length(google_compute_subnetwork.bcap_subnets) == 2
    error_message = "Expected 2 DoD subnets in the default 2-region topology."
  }

  assert {
    condition     = google_compute_subnetwork.bcap_subnets["subnet1"].ip_cidr_range == "10.0.0.0/25"
    error_message = "Expected subnet1 to receive the first /25 CIDR block."
  }

  assert {
    condition     = google_compute_subnetwork.bcap_subnets["subnet2"].ip_cidr_range == "10.0.0.128/25"
    error_message = "Expected subnet2 to receive the second /25 CIDR block."
  }

  assert {
    condition     = google_compute_subnetwork.bcap_subnets["subnet1"].log_config[0].flow_sampling == 1.0
    error_message = "Expected full VPC flow log sampling (1.0) on BCAP subnets."
  }

  assert {
    condition     = length(google_compute_router.routers) == 2
    error_message = "Expected 2 Cloud Routers in the default 2-region topology."
  }

  assert {
    condition     = length(google_compute_interconnect_attachment.attachments) == 4
    error_message = "Expected 4 Partner VLAN attachments in the default 2-region topology."
  }

  assert {
    condition     = google_compute_interconnect_attachment.attachments["router1-attachment1"].type == "PARTNER"
    error_message = "Expected PARTNER interconnect attachment type."
  }

  assert {
    condition     = google_compute_interconnect_attachment.attachments["router1-attachment1"].mtu == "1440"
    error_message = "Expected default MTU 1440 on PARTNER attachments."
  }
}

run "plan_existing_vpc_reuse" {
  command = plan

  variables {
    create_vpc   = false
    network_name = "existing-stage2-vpc"
  }

  assert {
    condition     = length(google_compute_network.vpc_network) == 0
    error_message = "Expected no new VPC creation when create_vpc is false."
  }

  assert {
    condition     = length(data.google_compute_network.existing_vpc) == 1
    error_message = "Expected existing VPC data source lookup when create_vpc is false."
  }

  assert {
    condition     = google_compute_subnetwork.bcap_subnets["subnet1"].network == "https://www.googleapis.com/compute/v1/projects/test-hub/global/networks/existing-stage2-vpc"
    error_message = "Expected BCAP subnets to attach to the existing VPC self link."
  }

  assert {
    condition     = google_compute_router.routers["router1"].network == "https://www.googleapis.com/compute/v1/projects/test-hub/global/networks/existing-stage2-vpc"
    error_message = "Expected Cloud Routers to attach to the existing VPC self link."
  }

  assert {
    condition     = output.vpc_network == null
    error_message = "Expected vpc_network output to be null when create_vpc is false."
  }

  assert {
    condition     = output.vpc_network_id == "projects/test-hub/global/networks/existing-stage2-vpc"
    error_message = "Expected vpc_network_id output to resolve from existing_vpc."
  }

  assert {
    condition     = output.vpc_network_self_link == "https://www.googleapis.com/compute/v1/projects/test-hub/global/networks/existing-stage2-vpc"
    error_message = "Expected vpc_network_self_link output to resolve from existing_vpc."
  }
}

run "plan_four_region_eight_attachments" {
  command = plan

  variables {
    create_vpc = false
    additional_regions = {
      region3 = "us-west1"
      region4 = "us-west2"
    }
    subnet_configs = {
      subnet1 = {
        name = "bcap-dod-subnet-r1"
      }
      subnet2 = {
        name = "bcap-dod-subnet-r2"
      }
      subnet3 = {
        name = "bcap-dod-subnet-r3"
      }
      subnet4 = {
        name = "bcap-dod-subnet-r4"
      }
    }
    router_configs = {
      router1 = {
        name = "bcap-router-r1"
      }
      router2 = {
        name = "bcap-router-r2"
      }
      router3 = {
        name = "bcap-router-r3"
      }
      router4 = {
        name = "bcap-router-r4"
      }
    }
    attachment_configs = {
      router1-attachment1 = {
        name                     = "bcap-r1-ad1"
        router_key               = "router1"
        edge_availability_domain = "AVAILABILITY_DOMAIN_1"
      }
      router1-attachment2 = {
        name                     = "bcap-r1-ad2"
        router_key               = "router1"
        edge_availability_domain = "AVAILABILITY_DOMAIN_2"
      }
      router2-attachment1 = {
        name                     = "bcap-r2-ad1"
        router_key               = "router2"
        edge_availability_domain = "AVAILABILITY_DOMAIN_1"
      }
      router2-attachment2 = {
        name                     = "bcap-r2-ad2"
        router_key               = "router2"
        edge_availability_domain = "AVAILABILITY_DOMAIN_2"
      }
      router3-attachment1 = {
        name                     = "bcap-r3-ad1"
        router_key               = "router3"
        edge_availability_domain = "AVAILABILITY_DOMAIN_1"
      }
      router3-attachment2 = {
        name                     = "bcap-r3-ad2"
        router_key               = "router3"
        edge_availability_domain = "AVAILABILITY_DOMAIN_2"
      }
      router4-attachment1 = {
        name                     = "bcap-r4-ad1"
        router_key               = "router4"
        edge_availability_domain = "AVAILABILITY_DOMAIN_1"
      }
      router4-attachment2 = {
        name                     = "bcap-r4-ad2"
        router_key               = "router4"
        edge_availability_domain = "AVAILABILITY_DOMAIN_2"
      }
    }
  }

  assert {
    condition     = length(google_compute_subnetwork.bcap_subnets) == 4
    error_message = "Expected 4 DoD subnets in the 4-region topology."
  }

  assert {
    condition     = google_compute_subnetwork.bcap_subnets["subnet1"].ip_cidr_range == "10.0.0.0/26"
    error_message = "Expected subnet1 to receive 10.0.0.0/26 in the 4-region topology."
  }

  assert {
    condition     = google_compute_subnetwork.bcap_subnets["subnet2"].ip_cidr_range == "10.0.0.64/26"
    error_message = "Expected subnet2 to receive 10.0.0.64/26 in the 4-region topology."
  }

  assert {
    condition     = google_compute_subnetwork.bcap_subnets["subnet3"].ip_cidr_range == "10.0.0.128/26"
    error_message = "Expected subnet3 to receive 10.0.0.128/26 in the 4-region topology."
  }

  assert {
    condition     = google_compute_subnetwork.bcap_subnets["subnet4"].ip_cidr_range == "10.0.0.192/26"
    error_message = "Expected subnet4 to receive 10.0.0.192/26 in the 4-region topology."
  }

  assert {
    condition     = google_compute_subnetwork.bcap_subnets["subnet3"].region == "us-west1"
    error_message = "Expected subnet3 to map to additional_regions.region3."
  }

  assert {
    condition     = google_compute_subnetwork.bcap_subnets["subnet4"].region == "us-west2"
    error_message = "Expected subnet4 to map to additional_regions.region4."
  }

  assert {
    condition     = google_compute_subnetwork.bcap_subnets["subnet3"].log_config[0].flow_sampling == 1.0
    error_message = "Expected full flow sampling (1.0) on additional region subnets."
  }

  assert {
    condition     = length(google_compute_router.routers) == 4
    error_message = "Expected 4 Cloud Routers in the 4-region topology."
  }

  assert {
    condition     = google_compute_router.routers["router3"].region == "us-west1"
    error_message = "Expected router3 to map to additional_regions.region3."
  }

  assert {
    condition     = google_compute_router.routers["router4"].region == "us-west2"
    error_message = "Expected router4 to map to additional_regions.region4."
  }

  assert {
    condition     = length(google_compute_interconnect_attachment.attachments) == 8
    error_message = "Expected 8 Partner VLAN attachments in the 4-region topology."
  }

  assert {
    condition     = google_compute_interconnect_attachment.attachments["router3-attachment1"].region == "us-west1"
    error_message = "Expected router3 attachments to inherit us-west1."
  }

  assert {
    condition     = google_compute_interconnect_attachment.attachments["router3-attachment1"].type == "PARTNER"
    error_message = "Expected PARTNER type on 4-region interconnect attachments."
  }
}

run "reject_invalid_attachment_count" {
  command = plan

  variables {
    attachment_configs = {
      router1-attachment1 = {
        name                     = "bcap-r1-ad1"
        router_key               = "router1"
        edge_availability_domain = "AVAILABILITY_DOMAIN_1"
      }
      router2-attachment1 = {
        name                     = "bcap-r2-ad1"
        router_key               = "router2"
        edge_availability_domain = "AVAILABILITY_DOMAIN_1"
      }
    }
  }

  expect_failures = [
    var.attachment_configs,
  ]
}

run "reject_mismatched_four_region_attachment_count" {
  command = plan

  variables {
    additional_regions = {
      region3 = "us-west1"
      region4 = "us-west2"
    }
    subnet_configs = {
      subnet1 = { name = "bcap-dod-subnet-r1" }
      subnet2 = { name = "bcap-dod-subnet-r2" }
      subnet3 = { name = "bcap-dod-subnet-r3" }
      subnet4 = { name = "bcap-dod-subnet-r4" }
    }
    router_configs = {
      router1 = { name = "bcap-router-r1" }
      router2 = { name = "bcap-router-r2" }
      router3 = { name = "bcap-router-r3" }
      router4 = { name = "bcap-router-r4" }
    }
  }

  expect_failures = [
    var.attachment_configs,
  ]
}

run "reject_invalid_additional_regions_count" {
  command = plan

  variables {
    additional_regions = {
      region3 = "us-west1"
    }
  }

  expect_failures = [
    var.additional_regions,
  ]
}

run "reject_vlan_id_on_partner_attachment" {
  command = plan

  variables {
    attachment_configs = {
      router1-attachment1 = {
        name                     = "bcap-r1-ad1"
        router_key               = "router1"
        edge_availability_domain = "AVAILABILITY_DOMAIN_1"
        vlan_id                  = 100
      }
      router1-attachment2 = {
        name                     = "bcap-r1-ad2"
        router_key               = "router1"
        edge_availability_domain = "AVAILABILITY_DOMAIN_2"
      }
      router2-attachment1 = {
        name                     = "bcap-r2-ad1"
        router_key               = "router2"
        edge_availability_domain = "AVAILABILITY_DOMAIN_1"
      }
      router2-attachment2 = {
        name                     = "bcap-r2-ad2"
        router_key               = "router2"
        edge_availability_domain = "AVAILABILITY_DOMAIN_2"
      }
    }
  }

  expect_failures = [
    var.attachment_configs,
  ]
}

run "reject_ipv6_dod_base_cidr_block" {
  command = plan

  variables {
    dod_base_cidr_block = "2001:db8::/24"
  }

  expect_failures = [
    var.dod_base_cidr_block,
  ]
}

run "reject_empty_additional_regions_value" {
  command = plan

  variables {
    additional_regions = {
      region3 = ""
      region4 = "us-west2"
    }
  }

  expect_failures = [
    var.additional_regions,
  ]
}

run "reject_duplicate_attachment_name_in_region" {
  command = plan

  variables {
    attachment_configs = {
      router1-attachment1 = {
        name                     = "bcap-r1-dup"
        router_key               = "router1"
        edge_availability_domain = "AVAILABILITY_DOMAIN_1"
      }
      router1-attachment2 = {
        name                     = "bcap-r1-dup"
        router_key               = "router1"
        edge_availability_domain = "AVAILABILITY_DOMAIN_2"
      }
      router2-attachment1 = {
        name                     = "bcap-r2-ad1"
        router_key               = "router2"
        edge_availability_domain = "AVAILABILITY_DOMAIN_1"
      }
      router2-attachment2 = {
        name                     = "bcap-r2-ad2"
        router_key               = "router2"
        edge_availability_domain = "AVAILABILITY_DOMAIN_2"
      }
    }
  }

  expect_failures = [
    var.attachment_configs,
  ]
}
