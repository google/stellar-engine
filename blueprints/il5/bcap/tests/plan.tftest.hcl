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
  hub_project_id      = "test-net-hub-0"
  network_name        = "bcap-vpc-0"
  region1             = "us-central1"
  region2             = "us-east4"
  dod_base_cidr_block = "192.0.2.0/24"
  subnet_configs = {
    subnet1 = { name = "bcap-subnet-1" }
    subnet2 = { name = "bcap-subnet-2" }
  }
  router_configs = {
    router1 = { name = "bcap-router-1" }
    router2 = { name = "bcap-router-2" }
  }
  attachment_configs = {
    r1-ad1 = {
      name                     = "bcap-r1-ad1"
      router_key               = "router1"
      edge_availability_domain = "AVAILABILITY_DOMAIN_1"
      vlan_id                  = null
    }
    r1-ad2 = {
      name                     = "bcap-r1-ad2"
      router_key               = "router1"
      edge_availability_domain = "AVAILABILITY_DOMAIN_2"
    }
    r2-ad1 = {
      name                     = "bcap-r2-ad1"
      router_key               = "router2"
      edge_availability_domain = "AVAILABILITY_DOMAIN_1"
    }
    r2-ad2 = {
      name                     = "bcap-r2-ad2"
      router_key               = "router2"
      edge_availability_domain = "AVAILABILITY_DOMAIN_2"
    }
  }
}

run "plan_partner_attachments_without_vlan_id_and_with_explicit_null" {
  command = plan

  assert {
    condition     = length(google_compute_interconnect_attachment.attachments) == 4
    error_message = "Expected four Partner interconnect attachments."
  }

  assert {
    condition = alltrue([
      for a in google_compute_interconnect_attachment.attachments :
      a.type == "PARTNER" &&
      a.candidate_cloud_router_ip_address == null &&
      a.candidate_customer_router_ip_address == null
    ])
    error_message = "Default Partner attachments must omit candidate BGP IPs."
  }
}

run "plan_partner_attachments_with_candidate_bgp_ips" {
  command = plan

  variables {
    attachment_configs = {
      r1-ad1 = {
        name                                 = "bcap-r1-ad1"
        router_key                           = "router1"
        edge_availability_domain             = "AVAILABILITY_DOMAIN_1"
        candidate_cloud_router_ip_address    = "169.254.0.1/29"
        candidate_customer_router_ip_address = "169.254.0.2/29"
      }
      r1-ad2 = {
        name                                 = "bcap-r1-ad2"
        router_key                           = "router1"
        edge_availability_domain             = "AVAILABILITY_DOMAIN_2"
        candidate_cloud_router_ip_address    = "169.254.0.9/29"
        candidate_customer_router_ip_address = "169.254.0.10/29"
      }
      r2-ad1 = {
        name                                 = "bcap-r2-ad1"
        router_key                           = "router2"
        edge_availability_domain             = "AVAILABILITY_DOMAIN_1"
        candidate_cloud_router_ip_address    = "169.254.0.17/29"
        candidate_customer_router_ip_address = "169.254.0.18/29"
      }
      r2-ad2 = {
        name                                 = "bcap-r2-ad2"
        router_key                           = "router2"
        edge_availability_domain             = "AVAILABILITY_DOMAIN_2"
        candidate_cloud_router_ip_address    = "169.254.0.25/29"
        candidate_customer_router_ip_address = "169.254.0.26/29"
      }
    }
  }

  assert {
    condition     = google_compute_interconnect_attachment.attachments["r1-ad1"].candidate_cloud_router_ip_address == "169.254.0.1/29"
    error_message = "Expected candidate_cloud_router_ip_address to pass through."
  }

  assert {
    condition     = google_compute_interconnect_attachment.attachments["r1-ad1"].candidate_customer_router_ip_address == "169.254.0.2/29"
    error_message = "Expected candidate_customer_router_ip_address to pass through."
  }
}

run "rejects_non_null_vlan_id" {
  command = plan

  variables {
    attachment_configs = {
      r1-ad1 = {
        name                     = "bcap-r1-ad1"
        router_key               = "router1"
        edge_availability_domain = "AVAILABILITY_DOMAIN_1"
        vlan_id                  = 100
      }
      r1-ad2 = {
        name                     = "bcap-r1-ad2"
        router_key               = "router1"
        edge_availability_domain = "AVAILABILITY_DOMAIN_2"
      }
      r2-ad1 = {
        name                     = "bcap-r2-ad1"
        router_key               = "router2"
        edge_availability_domain = "AVAILABILITY_DOMAIN_1"
      }
      r2-ad2 = {
        name                     = "bcap-r2-ad2"
        router_key               = "router2"
        edge_availability_domain = "AVAILABILITY_DOMAIN_2"
      }
    }
  }

  expect_failures = [var.attachment_configs]
}

run "rejects_unpaired_candidate_ip" {
  command = plan

  variables {
    attachment_configs = {
      r1-ad1 = {
        name                              = "bcap-r1-ad1"
        router_key                        = "router1"
        edge_availability_domain          = "AVAILABILITY_DOMAIN_1"
        candidate_cloud_router_ip_address = "169.254.0.1/29"
      }
      r1-ad2 = {
        name                     = "bcap-r1-ad2"
        router_key               = "router1"
        edge_availability_domain = "AVAILABILITY_DOMAIN_2"
      }
      r2-ad1 = {
        name                     = "bcap-r2-ad1"
        router_key               = "router2"
        edge_availability_domain = "AVAILABILITY_DOMAIN_1"
      }
      r2-ad2 = {
        name                     = "bcap-r2-ad2"
        router_key               = "router2"
        edge_availability_domain = "AVAILABILITY_DOMAIN_2"
      }
    }
  }

  expect_failures = [var.attachment_configs]
}

run "rejects_mismatched_candidate_subnets" {
  command = plan

  variables {
    attachment_configs = {
      r1-ad1 = {
        name                                 = "bcap-r1-ad1"
        router_key                           = "router1"
        edge_availability_domain             = "AVAILABILITY_DOMAIN_1"
        candidate_cloud_router_ip_address    = "169.254.0.1/29"
        candidate_customer_router_ip_address = "169.254.0.10/29"
      }
      r1-ad2 = {
        name                     = "bcap-r1-ad2"
        router_key               = "router1"
        edge_availability_domain = "AVAILABILITY_DOMAIN_2"
      }
      r2-ad1 = {
        name                     = "bcap-r2-ad1"
        router_key               = "router2"
        edge_availability_domain = "AVAILABILITY_DOMAIN_1"
      }
      r2-ad2 = {
        name                     = "bcap-r2-ad2"
        router_key               = "router2"
        edge_availability_domain = "AVAILABILITY_DOMAIN_2"
      }
    }
  }

  expect_failures = [var.attachment_configs]
}

run "rejects_link_local_slash_30_prefix" {
  command = plan

  variables {
    attachment_configs = {
      r1-ad1 = {
        name                                 = "bcap-r1-ad1"
        router_key                           = "router1"
        edge_availability_domain             = "AVAILABILITY_DOMAIN_1"
        candidate_cloud_router_ip_address    = "169.254.0.1/30"
        candidate_customer_router_ip_address = "169.254.0.2/30"
      }
      r1-ad2 = {
        name                     = "bcap-r1-ad2"
        router_key               = "router1"
        edge_availability_domain = "AVAILABILITY_DOMAIN_2"
      }
      r2-ad1 = {
        name                     = "bcap-r2-ad1"
        router_key               = "router2"
        edge_availability_domain = "AVAILABILITY_DOMAIN_1"
      }
      r2-ad2 = {
        name                     = "bcap-r2-ad2"
        router_key               = "router2"
        edge_availability_domain = "AVAILABILITY_DOMAIN_2"
      }
    }
  }

  expect_failures = [var.attachment_configs]
}

run "plan_partner_attachments_with_non_link_local_slash_30_bgp_ips" {
  command = plan

  variables {
    attachment_configs = {
      r1-ad1 = {
        name                                 = "bcap-r1-ad1"
        router_key                           = "router1"
        edge_availability_domain             = "AVAILABILITY_DOMAIN_1"
        candidate_cloud_router_ip_address    = "192.169.0.1/30"
        candidate_customer_router_ip_address = "192.169.0.2/30"
      }
      r1-ad2 = {
        name                                 = "bcap-r1-ad2"
        router_key                           = "router1"
        edge_availability_domain             = "AVAILABILITY_DOMAIN_2"
        candidate_cloud_router_ip_address    = "192.169.0.5/30"
        candidate_customer_router_ip_address = "192.169.0.6/30"
      }
      r2-ad1 = {
        name                     = "bcap-r2-ad1"
        router_key               = "router2"
        edge_availability_domain = "AVAILABILITY_DOMAIN_1"
      }
      r2-ad2 = {
        name                     = "bcap-r2-ad2"
        router_key               = "router2"
        edge_availability_domain = "AVAILABILITY_DOMAIN_2"
      }
    }
  }

  assert {
    condition     = google_compute_interconnect_attachment.attachments["r1-ad1"].candidate_cloud_router_ip_address == "192.169.0.1/30"
    error_message = "Valid non-private /30 cloud router candidate IP must be accepted."
  }

  assert {
    condition     = google_compute_interconnect_attachment.attachments["r1-ad2"].candidate_customer_router_ip_address == "192.169.0.6/30"
    error_message = "Valid non-overlapping /30 customer router candidate IP must be accepted."
  }
}

run "rejects_network_address_candidate_ip" {
  command = plan

  variables {
    attachment_configs = {
      r1-ad1 = {
        name                                 = "bcap-r1-ad1"
        router_key                           = "router1"
        edge_availability_domain             = "AVAILABILITY_DOMAIN_1"
        candidate_cloud_router_ip_address    = "169.254.0.0/29"
        candidate_customer_router_ip_address = "169.254.0.2/29"
      }
      r1-ad2 = {
        name                     = "bcap-r1-ad2"
        router_key               = "router1"
        edge_availability_domain = "AVAILABILITY_DOMAIN_2"
      }
      r2-ad1 = {
        name                     = "bcap-r2-ad1"
        router_key               = "router2"
        edge_availability_domain = "AVAILABILITY_DOMAIN_1"
      }
      r2-ad2 = {
        name                     = "bcap-r2-ad2"
        router_key               = "router2"
        edge_availability_domain = "AVAILABILITY_DOMAIN_2"
      }
    }
  }

  expect_failures = [var.attachment_configs]
}

run "rejects_broadcast_address_candidate_ip" {
  command = plan

  variables {
    attachment_configs = {
      r1-ad1 = {
        name                                 = "bcap-r1-ad1"
        router_key                           = "router1"
        edge_availability_domain             = "AVAILABILITY_DOMAIN_1"
        candidate_cloud_router_ip_address    = "169.254.0.1/29"
        candidate_customer_router_ip_address = "169.254.0.7/29"
      }
      r1-ad2 = {
        name                     = "bcap-r1-ad2"
        router_key               = "router1"
        edge_availability_domain = "AVAILABILITY_DOMAIN_2"
      }
      r2-ad1 = {
        name                     = "bcap-r2-ad1"
        router_key               = "router2"
        edge_availability_domain = "AVAILABILITY_DOMAIN_1"
      }
      r2-ad2 = {
        name                     = "bcap-r2-ad2"
        router_key               = "router2"
        edge_availability_domain = "AVAILABILITY_DOMAIN_2"
      }
    }
  }

  expect_failures = [var.attachment_configs]
}

run "rejects_private_ipv4_candidate_range" {
  command = plan

  variables {
    attachment_configs = {
      r1-ad1 = {
        name                                 = "bcap-r1-ad1"
        router_key                           = "router1"
        edge_availability_domain             = "AVAILABILITY_DOMAIN_1"
        candidate_cloud_router_ip_address    = "10.0.0.1/29"
        candidate_customer_router_ip_address = "10.0.0.2/29"
      }
      r1-ad2 = {
        name                     = "bcap-r1-ad2"
        router_key               = "router1"
        edge_availability_domain = "AVAILABILITY_DOMAIN_2"
      }
      r2-ad1 = {
        name                     = "bcap-r2-ad1"
        router_key               = "router2"
        edge_availability_domain = "AVAILABILITY_DOMAIN_1"
      }
      r2-ad2 = {
        name                     = "bcap-r2-ad2"
        router_key               = "router2"
        edge_availability_domain = "AVAILABILITY_DOMAIN_2"
      }
    }
  }

  expect_failures = [var.attachment_configs]
}

run "rejects_duplicate_candidate_subnets_across_attachments" {
  command = plan

  variables {
    attachment_configs = {
      r1-ad1 = {
        name                                 = "bcap-r1-ad1"
        router_key                           = "router1"
        edge_availability_domain             = "AVAILABILITY_DOMAIN_1"
        candidate_cloud_router_ip_address    = "169.254.0.1/29"
        candidate_customer_router_ip_address = "169.254.0.2/29"
      }
      r1-ad2 = {
        name                                 = "bcap-r1-ad2"
        router_key                           = "router1"
        edge_availability_domain             = "AVAILABILITY_DOMAIN_2"
        candidate_cloud_router_ip_address    = "169.254.0.3/29"
        candidate_customer_router_ip_address = "169.254.0.4/29"
      }
      r2-ad1 = {
        name                     = "bcap-r2-ad1"
        router_key               = "router2"
        edge_availability_domain = "AVAILABILITY_DOMAIN_1"
      }
      r2-ad2 = {
        name                     = "bcap-r2-ad2"
        router_key               = "router2"
        edge_availability_domain = "AVAILABILITY_DOMAIN_2"
      }
    }
  }

  expect_failures = [var.attachment_configs]
}

run "rejects_overlapping_slash_29_and_slash_30_candidate_subnets" {
  command = plan

  variables {
    attachment_configs = {
      r1-ad1 = {
        name                                 = "bcap-r1-ad1"
        router_key                           = "router1"
        edge_availability_domain             = "AVAILABILITY_DOMAIN_1"
        candidate_cloud_router_ip_address    = "192.169.0.1/29"
        candidate_customer_router_ip_address = "192.169.0.2/29"
      }
      r1-ad2 = {
        name                                 = "bcap-r1-ad2"
        router_key                           = "router1"
        edge_availability_domain             = "AVAILABILITY_DOMAIN_2"
        candidate_cloud_router_ip_address    = "192.169.0.5/30"
        candidate_customer_router_ip_address = "192.169.0.6/30"
      }
      r2-ad1 = {
        name                     = "bcap-r2-ad1"
        router_key               = "router2"
        edge_availability_domain = "AVAILABILITY_DOMAIN_1"
      }
      r2-ad2 = {
        name                     = "bcap-r2-ad2"
        router_key               = "router2"
        edge_availability_domain = "AVAILABILITY_DOMAIN_2"
      }
    }
  }

  expect_failures = [var.attachment_configs]
}

run "rejects_identical_candidate_ips" {
  command = plan

  variables {
    attachment_configs = {
      r1-ad1 = {
        name                                 = "bcap-r1-ad1"
        router_key                           = "router1"
        edge_availability_domain             = "AVAILABILITY_DOMAIN_1"
        candidate_cloud_router_ip_address    = "169.254.0.1/29"
        candidate_customer_router_ip_address = "169.254.0.1/29"
      }
      r1-ad2 = {
        name                     = "bcap-r1-ad2"
        router_key               = "router1"
        edge_availability_domain = "AVAILABILITY_DOMAIN_2"
      }
      r2-ad1 = {
        name                     = "bcap-r2-ad1"
        router_key               = "router2"
        edge_availability_domain = "AVAILABILITY_DOMAIN_1"
      }
      r2-ad2 = {
        name                     = "bcap-r2-ad2"
        router_key               = "router2"
        edge_availability_domain = "AVAILABILITY_DOMAIN_2"
      }
    }
  }

  expect_failures = [var.attachment_configs]
}

run "rejects_slash_31_candidate_ips" {
  command = plan

  variables {
    attachment_configs = {
      r1-ad1 = {
        name                                 = "bcap-r1-ad1"
        router_key                           = "router1"
        edge_availability_domain             = "AVAILABILITY_DOMAIN_1"
        candidate_cloud_router_ip_address    = "169.254.0.10/31"
        candidate_customer_router_ip_address = "169.254.0.11/31"
      }
      r1-ad2 = {
        name                     = "bcap-r1-ad2"
        router_key               = "router1"
        edge_availability_domain = "AVAILABILITY_DOMAIN_2"
      }
      r2-ad1 = {
        name                     = "bcap-r2-ad1"
        router_key               = "router2"
        edge_availability_domain = "AVAILABILITY_DOMAIN_1"
      }
      r2-ad2 = {
        name                     = "bcap-r2-ad2"
        router_key               = "router2"
        edge_availability_domain = "AVAILABILITY_DOMAIN_2"
      }
    }
  }

  expect_failures = [var.attachment_configs]
}

run "rejects_ipv6_candidate_ips" {
  command = plan

  variables {
    attachment_configs = {
      r1-ad1 = {
        name                                 = "bcap-r1-ad1"
        router_key                           = "router1"
        edge_availability_domain             = "AVAILABILITY_DOMAIN_1"
        candidate_cloud_router_ip_address    = "fd00::1/126"
        candidate_customer_router_ip_address = "fd00::2/126"
      }
      r1-ad2 = {
        name                     = "bcap-r1-ad2"
        router_key               = "router1"
        edge_availability_domain = "AVAILABILITY_DOMAIN_2"
      }
      r2-ad1 = {
        name                     = "bcap-r2-ad1"
        router_key               = "router2"
        edge_availability_domain = "AVAILABILITY_DOMAIN_1"
      }
      r2-ad2 = {
        name                     = "bcap-r2-ad2"
        router_key               = "router2"
        edge_availability_domain = "AVAILABILITY_DOMAIN_2"
      }
    }
  }

  expect_failures = [var.attachment_configs]
}
