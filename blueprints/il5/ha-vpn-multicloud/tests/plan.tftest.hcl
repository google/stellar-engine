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
mock_provider "random" {}

override_data {
  target = data.google_secret_manager_secret_version.tunnel_psk
  values = {
    secret_data = "mock-test-psk-value"
  }
}

override_data {
  target = data.google_secret_manager_regional_secret_version.tunnel_psk
  values = {
    secret_data = "mock-regional-psk-value"
  }
}

variables {
  project_id  = "test-net-hub-0"
  network     = "projects/test-net-hub-0/global/networks/test-vpc-hub-0"
  region      = "us-east4"
  name_prefix = "ha-vpn"
  router_asn  = 64514
  peers = {
    aws = {
      description     = "External AWS VPN gateway"
      redundancy_type = "FOUR_IPS_REDUNDANCY"
      external_interfaces = [
        "198.51.100.1",
        "198.51.100.2",
        "198.51.100.3",
        "198.51.100.4",
      ]
      tunnels = {
        tun-0 = {
          bgp_peer_address                = "169.254.21.1"
          bgp_peer_asn                    = 64512
          bgp_session_range               = "169.254.21.2/30"
          peer_external_gateway_interface = 0
          psk_secret_id                   = "vpn-aws-tun-0-psk"
          vpn_gateway_interface           = 0
        }
        tun-1 = {
          bgp_peer_address                = "169.254.21.5"
          bgp_peer_asn                    = 64512
          bgp_session_range               = "169.254.21.6/30"
          peer_external_gateway_interface = 1
          psk_secret_id                   = "vpn-aws-tun-1-psk"
          vpn_gateway_interface           = 0
        }
        tun-2 = {
          bgp_peer_address                = "169.254.21.9"
          bgp_peer_asn                    = 64512
          bgp_session_range               = "169.254.21.10/30"
          peer_external_gateway_interface = 2
          psk_secret_id                   = "vpn-aws-tun-2-psk"
          vpn_gateway_interface           = 1
        }
        tun-3 = {
          bgp_peer_address                = "169.254.21.13"
          bgp_peer_asn                    = 64512
          bgp_session_range               = "169.254.21.14/30"
          peer_external_gateway_interface = 3
          psk_secret_id                   = "vpn-aws-tun-3-psk"
          vpn_gateway_interface           = 1
        }
      }
    }
    azure = {
      description     = "External Azure active-active VPN gateway"
      redundancy_type = "TWO_IPS_REDUNDANCY"
      external_interfaces = [
        "203.0.113.1",
        "203.0.113.2",
      ]
      tunnels = {
        tun-0 = {
          bgp_peer_address                = "169.254.22.2"
          bgp_peer_asn                    = 65515
          bgp_session_range               = "169.254.22.1/30"
          peer_external_gateway_interface = 0
          psk_secret_id                   = "vpn-azure-tun-0-psk"
          vpn_gateway_interface           = 0
        }
        tun-1 = {
          bgp_peer_address                = "169.254.22.6"
          bgp_peer_asn                    = 65515
          bgp_session_range               = "169.254.22.5/30"
          peer_external_gateway_interface = 1
          psk_secret_id                   = "vpn-azure-tun-1-psk"
          vpn_gateway_interface           = 0
        }
        tun-2 = {
          bgp_peer_address                = "169.254.22.10"
          bgp_peer_asn                    = 65515
          bgp_session_range               = "169.254.22.9/30"
          peer_external_gateway_interface = 0
          psk_secret_id                   = "vpn-azure-tun-2-psk"
          vpn_gateway_interface           = 1
        }
        tun-3 = {
          bgp_peer_address                = "169.254.22.14"
          bgp_peer_asn                    = 65515
          bgp_session_range               = "169.254.22.13/30"
          peer_external_gateway_interface = 1
          psk_secret_id                   = "vpn-azure-tun-3-psk"
          vpn_gateway_interface           = 1
        }
      }
    }
  }
}

run "plan_multicloud_aws_and_azure_cnsa_and_dns" {
  command = plan

  assert {
    condition     = length(module.vpn-ha) == 2
    error_message = "Expected two HA VPN module instances for AWS and Azure."
  }

  assert {
    condition     = length(module.vpn-ha["aws"].tunnels) == 4 && length(module.vpn-ha["azure"].tunnels) == 4
    error_message = "Expected four VPN tunnels per multi-cloud peer."
  }

  assert {
    condition     = length(data.google_secret_manager_secret_version.tunnel_psk) == 8
    error_message = "Expected one global Secret Manager PSK lookup per tunnel."
  }

  assert {
    condition     = length(data.google_secret_manager_regional_secret_version.tunnel_psk) == 0
    error_message = "Expected zero regional Secret Manager lookups when psk_secret_location is unset."
  }

  assert {
    condition = (
      tolist(local.normalized_cipher_suites["aws"].phase1.encryption) == tolist(["AES-GCM-16-256"]) &&
      tolist(local.normalized_cipher_suites["aws"].phase1.prf) == tolist(["PRF-HMAC-SHA2-384"]) &&
      tolist(local.normalized_cipher_suites["aws"].phase1.dh) == tolist(["Group-20"]) &&
      local.normalized_cipher_suites["aws"].phase1.integrity == null
    )
    error_message = "Expected CNSA IKEv2 Phase 1 AEAD cipher suite on AWS tunnels."
  }

  assert {
    condition = (
      tolist(local.normalized_cipher_suites["aws"].phase2.encryption) == tolist(["AES-GCM-16-256"]) &&
      tolist(local.normalized_cipher_suites["aws"].phase2.pfs) == tolist(["Group-20"]) &&
      local.normalized_cipher_suites["aws"].phase2.integrity == null
    )
    error_message = "Expected CNSA IKEv2 Phase 2 AEAD cipher suite on AWS tunnels."
  }

  assert {
    condition = (
      tolist(local.normalized_cipher_suites["azure"].phase1.encryption) == tolist(["AES-GCM-16-256"]) &&
      tolist(local.normalized_cipher_suites["azure"].phase2.pfs) == tolist(["Group-20"])
    )
    error_message = "Expected CNSA IKEv2 cipher suite on Azure tunnels."
  }

  assert {
    condition = (
      module.vpn-ha["aws"].router.bgp[0].advertise_mode == "CUSTOM" &&
      contains(module.vpn-ha["aws"].router.bgp[0].advertised_groups, "ALL_SUBNETS") &&
      contains([
        for r in module.vpn-ha["aws"].router.bgp[0].advertised_ip_ranges : r.range
      ], "35.199.192.0/19")
    )
    error_message = "Expected AWS Cloud Router to advertise 35.199.192.0/19 with ALL_SUBNETS."
  }

  assert {
    condition = (
      contains([
        for r in module.vpn-ha["azure"].router.bgp[0].advertised_ip_ranges : r.range
      ], "35.199.192.0/19")
    )
    error_message = "Expected Azure Cloud Router to advertise 35.199.192.0/19."
  }

  assert {
    condition     = data.google_secret_manager_secret_version.tunnel_psk["aws/tun-0"].secret_data == "mock-test-psk-value"
    error_message = "Expected Secret Manager secret_data payload rather than secret name string."
  }

  assert {
    condition     = module.vpn-ha["aws"].gateway.stack_type == "IPV4_ONLY"
    error_message = "Expected IPV4_ONLY stack type by default."
  }
}

run "apply_mock_verifies_tunnel_ciphers_secret_wiring_and_outputs" {
  command = apply

  assert {
    condition = (
      module.vpn-ha["aws"].tunnels["tun-0"].ike_version == 2 &&
      tolist(module.vpn-ha["aws"].tunnels["tun-0"].cipher_suite[0].phase1[0].encryption) == tolist(["AES-GCM-16-256"]) &&
      tolist(module.vpn-ha["aws"].tunnels["tun-0"].cipher_suite[0].phase1[0].prf) == tolist(["PRF-HMAC-SHA2-384"]) &&
      tolist(module.vpn-ha["aws"].tunnels["tun-0"].cipher_suite[0].phase1[0].dh) == tolist(["Group-20"]) &&
      module.vpn-ha["aws"].tunnels["tun-0"].cipher_suite[0].phase1[0].integrity == null &&
      tolist(module.vpn-ha["aws"].tunnels["tun-0"].cipher_suite[0].phase2[0].encryption) == tolist(["AES-GCM-16-256"]) &&
      tolist(module.vpn-ha["aws"].tunnels["tun-0"].cipher_suite[0].phase2[0].pfs) == tolist(["Group-20"]) &&
      module.vpn-ha["aws"].tunnels["tun-0"].cipher_suite[0].phase2[0].integrity == null
    )
    error_message = "Expected CNSA IKEv2 AEAD cipher_suite propagated into google_compute_vpn_tunnel resources."
  }

  assert {
    condition = (
      tolist(module.vpn-ha["azure"].tunnels["tun-0"].cipher_suite[0].phase1[0].encryption) == tolist(["AES-GCM-16-256"]) &&
      tolist(module.vpn-ha["azure"].tunnels["tun-0"].cipher_suite[0].phase2[0].pfs) == tolist(["Group-20"])
    )
    error_message = "Expected CNSA IKEv2 cipher_suite propagated into Azure tunnel resources."
  }

  assert {
    condition     = module.vpn-ha["aws"].tunnels["tun-0"].shared_secret == "mock-test-psk-value"
    error_message = "Expected tunnel shared_secret to match Secret Manager payload."
  }

  assert {
    condition = (
      output.vpn_gateway_ids["aws"] == "projects/test-net-hub-0/regions/us-east4/vpnGateways/ha-vpn-aws" &&
      output.vpn_gateway_ids["azure"] == "projects/test-net-hub-0/regions/us-east4/vpnGateways/ha-vpn-azure" &&
      output.external_gateway_ids["aws"] != null &&
      output.router_names["aws"] == "vpn-ha-vpn-aws" &&
      length(output.tunnel_self_links["aws"]) == 4 &&
      length(output.tunnel_self_links["azure"]) == 4
    )
    error_message = "Expected non-secret gateway, router, and tunnel outputs for both peers."
  }
}

run "apply_mock_supports_regional_and_global_secret_manager_lookups" {
  command = apply

  variables {
    peers = {
      hybrid = {
        redundancy_type     = "TWO_IPS_REDUNDANCY"
        external_interfaces = ["192.0.2.10", "192.0.2.11"]
        tunnels = {
          tun-global = {
            bgp_peer_address                = "169.254.24.2"
            bgp_peer_asn                    = 65516
            bgp_session_range               = "169.254.24.1/30"
            peer_external_gateway_interface = 0
            psk_secret_id                   = "projects/test-sec-0/secrets/vpn-global-psk"
            psk_secret_version              = "3"
            vpn_gateway_interface           = 0
          }
          tun-regional-short = {
            bgp_peer_address                = "169.254.24.6"
            bgp_peer_asn                    = 65516
            bgp_session_range               = "169.254.24.5/30"
            peer_external_gateway_interface = 1
            psk_secret_id                   = "vpn-regional-psk"
            psk_secret_location             = "us-east4"
            psk_secret_project_id           = "test-sec-0"
            psk_secret_version              = "2"
            vpn_gateway_interface           = 1
          }
          tun-regional-path = {
            bgp_peer_address                = "169.254.24.10"
            bgp_peer_asn                    = 65516
            bgp_session_range               = "169.254.24.9/30"
            peer_external_gateway_interface = 0
            psk_secret_id                   = "projects/test-sec-1/locations/us-central1/secrets/vpn-regional-path-psk"
            psk_secret_location             = "us-central1"
            vpn_gateway_interface           = 0
          }
        }
      }
    }
  }

  assert {
    condition = (
      length(data.google_secret_manager_secret_version.tunnel_psk) == 1 &&
      length(data.google_secret_manager_regional_secret_version.tunnel_psk) == 2
    )
    error_message = "Expected one global and two regional Secret Manager lookups."
  }

  assert {
    condition = (
      data.google_secret_manager_regional_secret_version.tunnel_psk["hybrid/tun-regional-short"].location == "us-east4" &&
      data.google_secret_manager_regional_secret_version.tunnel_psk["hybrid/tun-regional-short"].project == "test-sec-0" &&
      data.google_secret_manager_regional_secret_version.tunnel_psk["hybrid/tun-regional-short"].secret == "vpn-regional-psk" &&
      data.google_secret_manager_regional_secret_version.tunnel_psk["hybrid/tun-regional-short"].version == "2" &&
      data.google_secret_manager_regional_secret_version.tunnel_psk["hybrid/tun-regional-path"].location == "us-central1" &&
      data.google_secret_manager_regional_secret_version.tunnel_psk["hybrid/tun-regional-path"].project == "test-sec-1" &&
      data.google_secret_manager_regional_secret_version.tunnel_psk["hybrid/tun-regional-path"].secret == "vpn-regional-path-psk"
    )
    error_message = "Expected regional Secret Manager lookups to resolve location, project, secret, and version."
  }

  assert {
    condition = (
      module.vpn-ha["hybrid"].tunnels["tun-global"].shared_secret == "mock-test-psk-value" &&
      module.vpn-ha["hybrid"].tunnels["tun-regional-short"].shared_secret == "mock-regional-psk-value" &&
      module.vpn-ha["hybrid"].tunnels["tun-regional-path"].shared_secret == "mock-regional-psk-value"
    )
    error_message = "Expected global and regional Secret Manager payloads to wire into tunnel shared_secret."
  }
}

run "plan_partial_peer_cipher_override_inherits_missing_phase" {
  command = plan

  variables {
    peers = {
      onprem = {
        redundancy_type     = "SINGLE_IP_INTERNALLY_REDUNDANT"
        external_interfaces = ["192.0.2.20"]
        cipher_suite = {
          phase2 = {
            encryption = ["AES-CBC-256"]
            integrity  = ["HMAC-SHA2-384-192"]
            pfs        = ["Group-20"]
          }
        }
        tunnels = {
          tun-0 = {
            bgp_peer_address                = "169.254.25.2"
            bgp_peer_asn                    = 65516
            bgp_session_range               = "169.254.25.1/30"
            peer_external_gateway_interface = 0
            psk_secret_id                   = "vpn-onprem-psk"
            vpn_gateway_interface           = 0
          }
        }
      }
    }
  }

  assert {
    condition = (
      tolist(local.normalized_cipher_suites["onprem"].phase1.encryption) == tolist(["AES-GCM-16-256"]) &&
      local.normalized_cipher_suites["onprem"].phase1.integrity == null &&
      tolist(local.normalized_cipher_suites["onprem"].phase2.encryption) == tolist(["AES-CBC-256"]) &&
      tolist(local.normalized_cipher_suites["onprem"].phase2.integrity) == tolist(["HMAC-SHA2-384-192"])
    )
    error_message = "Expected partial peer cipher_suite override to inherit phase1 from var.cipher_suite."
  }
}

run "plan_disable_dns_forwarding_range_omits_route" {
  command = plan

  variables {
    advertise_dns_forwarding_range = false
    custom_advertised_ip_ranges = {
      "10.84.0.0/14" = "Primary pod range"
    }
  }

  assert {
    condition = (
      !contains([
        for r in module.vpn-ha["aws"].router.bgp[0].advertised_ip_ranges : r.range
      ], "35.199.192.0/19") &&
      contains([
        for r in module.vpn-ha["aws"].router.bgp[0].advertised_ip_ranges : r.range
      ], "10.84.0.0/14")
    )
    error_message = "Expected 35.199.192.0/19 to be omitted while preserving custom_advertised_ip_ranges."
  }
}

run "plan_disable_dns_forwarding_without_custom_ranges_uses_default_mode" {
  command = plan

  variables {
    advertise_dns_forwarding_range = false
    custom_advertised_ip_ranges    = {}
  }

  assert {
    condition = (
      module.vpn-ha["aws"].router.bgp[0].advertise_mode == "DEFAULT" &&
      length(module.vpn-ha["aws"].router.bgp[0].advertised_ip_ranges) == 0
    )
    error_message = "Expected DEFAULT advertise mode with zero advertised_ip_ranges."
  }
}

run "plan_empty_peers_creates_zero_resources" {
  command = plan

  variables {
    peers = {}
  }

  assert {
    condition     = length(module.vpn-ha) == 0
    error_message = "Expected zero HA VPN module instances when peers is empty."
  }

  assert {
    condition = (
      length(data.google_secret_manager_secret_version.tunnel_psk) == 0 &&
      length(data.google_secret_manager_regional_secret_version.tunnel_psk) == 0
    )
    error_message = "Expected zero Secret Manager lookups when peers is empty."
  }

  assert {
    condition     = length(output.vpn_gateway_ids) == 0 && length(output.router_names) == 0
    error_message = "Expected empty gateway and router outputs when peers is empty."
  }
}

run "plan_dual_stack_ipv4_ipv6" {
  command = plan

  variables {
    stack_type = "IPV4_IPV6"
  }

  assert {
    condition     = module.vpn-ha["aws"].gateway.stack_type == "IPV4_IPV6"
    error_message = "Expected IPV4_IPV6 stack_type on HA VPN gateway."
  }
}

run "plan_normalizes_empty_integrity_list_and_full_secret_path" {
  command = plan

  variables {
    cipher_suite = {
      phase1 = {
        dh         = ["Group-20"]
        encryption = ["AES-GCM-16-256"]
        integrity  = []
        prf        = ["PRF-HMAC-SHA2-384"]
      }
      phase2 = {
        encryption = ["AES-GCM-16-256"]
        integrity  = []
        pfs        = ["Group-20"]
      }
    }
    peers = {
      onprem = {
        redundancy_type     = "SINGLE_IP_INTERNALLY_REDUNDANT"
        external_interfaces = ["192.0.2.10"]
        tunnels = {
          tun-0 = {
            bgp_peer_address                = "169.254.23.2"
            bgp_peer_asn                    = 65516
            bgp_session_range               = "169.254.23.1/30"
            peer_external_gateway_interface = 0
            psk_secret_id                   = "projects/test-sec-0/secrets/vpn-onprem-psk"
            psk_secret_version              = "2"
            vpn_gateway_interface           = 0
          }
        }
      }
    }
  }

  assert {
    condition = (
      local.normalized_cipher_suites["onprem"].phase1.integrity == null &&
      local.normalized_cipher_suites["onprem"].phase2.integrity == null
    )
    error_message = "Expected empty integrity lists to normalize to null for AEAD ciphers."
  }

  assert {
    condition = (
      data.google_secret_manager_secret_version.tunnel_psk["onprem/tun-0"].project == "test-sec-0" &&
      data.google_secret_manager_secret_version.tunnel_psk["onprem/tun-0"].secret == "vpn-onprem-psk" &&
      data.google_secret_manager_secret_version.tunnel_psk["onprem/tun-0"].version == "2"
    )
    error_message = "Expected full Secret Manager resource path to resolve project, secret ID, and pinned version."
  }
}

run "plan_rejects_invalid_stack_type" {
  command = plan

  variables {
    stack_type = "IPV6_ONLY"
  }

  expect_failures = [
    var.stack_type,
  ]
}

run "plan_rejects_invalid_redundancy_type" {
  command = plan

  variables {
    peers = {
      bad = {
        redundancy_type     = "THREE_IPS_REDUNDANCY"
        external_interfaces = ["198.51.100.1", "198.51.100.2", "198.51.100.3"]
        tunnels             = {}
      }
    }
  }

  expect_failures = [
    var.peers,
  ]
}

run "plan_rejects_invalid_bgp_cidr_non_apipa" {
  command = plan

  variables {
    peers = {
      bad = {
        redundancy_type     = "SINGLE_IP_INTERNALLY_REDUNDANT"
        external_interfaces = ["198.51.100.10"]
        tunnels = {
          tun-0 = {
            bgp_peer_address                = "10.0.0.2"
            bgp_peer_asn                    = 64512
            bgp_session_range               = "10.0.0.1/30"
            peer_external_gateway_interface = 0
            psk_secret_id                   = "vpn-bad-tun-0-psk"
            vpn_gateway_interface           = 0
          }
        }
      }
    }
  }

  expect_failures = [
    var.peers,
  ]
}

run "plan_rejects_invalid_bgp_cidr_wrong_prefix" {
  command = plan

  variables {
    peers = {
      bad = {
        redundancy_type     = "SINGLE_IP_INTERNALLY_REDUNDANT"
        external_interfaces = ["198.51.100.10"]
        tunnels = {
          tun-0 = {
            bgp_peer_address                = "169.254.21.2"
            bgp_peer_asn                    = 64512
            bgp_session_range               = "169.254.21.1/29"
            peer_external_gateway_interface = 0
            psk_secret_id                   = "vpn-bad-tun-0-psk"
            vpn_gateway_interface           = 0
          }
        }
      }
    }
  }

  expect_failures = [
    var.peers,
  ]
}

run "plan_rejects_metadata_bgp_cidr" {
  command = plan

  variables {
    peers = {
      bad = {
        redundancy_type     = "SINGLE_IP_INTERNALLY_REDUNDANT"
        external_interfaces = ["198.51.100.10"]
        tunnels = {
          tun-0 = {
            bgp_peer_address                = "169.254.169.254"
            bgp_peer_asn                    = 64512
            bgp_session_range               = "169.254.169.253/30"
            peer_external_gateway_interface = 0
            psk_secret_id                   = "vpn-bad-meta-psk"
            vpn_gateway_interface           = 0
          }
        }
      }
    }
  }

  expect_failures = [
    var.peers,
  ]
}

run "plan_rejects_cross_peer_bgp_cidr_collision" {
  command = plan

  variables {
    peers = {
      aws = {
        redundancy_type     = "SINGLE_IP_INTERNALLY_REDUNDANT"
        external_interfaces = ["198.51.100.1"]
        tunnels = {
          tun-0 = {
            bgp_peer_address                = "169.254.30.1"
            bgp_peer_asn                    = 64512
            bgp_session_range               = "169.254.30.2/30"
            peer_external_gateway_interface = 0
            psk_secret_id                   = "vpn-aws-tun-0-psk"
            vpn_gateway_interface           = 0
          }
        }
      }
      azure = {
        redundancy_type     = "SINGLE_IP_INTERNALLY_REDUNDANT"
        external_interfaces = ["203.0.113.1"]
        tunnels = {
          tun-0 = {
            bgp_peer_address                = "169.254.30.2"
            bgp_peer_asn                    = 65515
            bgp_session_range               = "169.254.30.1/30"
            peer_external_gateway_interface = 0
            psk_secret_id                   = "vpn-azure-tun-0-psk"
            vpn_gateway_interface           = 0
          }
        }
      }
    }
  }

  expect_failures = [
    var.peers,
  ]
}

run "plan_rejects_invalid_tunnel_key_characters" {
  command = plan

  variables {
    peers = {
      bad = {
        redundancy_type     = "SINGLE_IP_INTERNALLY_REDUNDANT"
        external_interfaces = ["198.51.100.10"]
        tunnels = {
          "Bad_Tunnel" = {
            bgp_peer_address                = "169.254.31.2"
            bgp_peer_asn                    = 64512
            bgp_session_range               = "169.254.31.1/30"
            peer_external_gateway_interface = 0
            psk_secret_id                   = "vpn-bad-tun-psk"
            vpn_gateway_interface           = 0
          }
        }
      }
    }
  }

  expect_failures = [
    var.peers,
  ]
}

run "plan_rejects_overlong_tunnel_resource_name" {
  command = plan

  variables {
    name_prefix = "ha-vpn-multicloud-prod"
    peers = {
      aws-primary = {
        redundancy_type     = "SINGLE_IP_INTERNALLY_REDUNDANT"
        external_interfaces = ["198.51.100.10"]
        tunnels = {
          "tunnel-interface-exceeding-sixty-three-char-gcp-limit-0" = {
            bgp_peer_address                = "169.254.32.2"
            bgp_peer_asn                    = 64512
            bgp_session_range               = "169.254.32.1/30"
            peer_external_gateway_interface = 0
            psk_secret_id                   = "vpn-long-tun-psk"
            vpn_gateway_interface           = 0
          }
        }
      }
    }
  }

  expect_failures = [
    var.peers,
  ]
}

run "plan_rejects_partial_top_level_cipher_suite" {
  command = plan

  variables {
    cipher_suite = {
      phase1 = {
        dh         = ["Group-20"]
        encryption = ["AES-GCM-16-256"]
        prf        = ["PRF-HMAC-SHA2-384"]
      }
      phase2 = null
    }
  }

  expect_failures = [
    var.cipher_suite,
  ]
}

run "plan_rejects_partial_peer_cipher_suite_when_default_null" {
  command = plan

  variables {
    cipher_suite = null
    peers = {
      bad = {
        redundancy_type     = "SINGLE_IP_INTERNALLY_REDUNDANT"
        external_interfaces = ["198.51.100.10"]
        cipher_suite = {
          phase1 = {
            dh         = ["Group-20"]
            encryption = ["AES-GCM-16-256"]
            prf        = ["PRF-HMAC-SHA2-384"]
          }
        }
        tunnels = {}
      }
    }
  }

  expect_failures = [
    var.peers,
  ]
}

run "plan_rejects_invalid_regional_secret_location" {
  command = plan

  variables {
    peers = {
      bad = {
        redundancy_type     = "SINGLE_IP_INTERNALLY_REDUNDANT"
        external_interfaces = ["198.51.100.10"]
        tunnels = {
          tun-0 = {
            bgp_peer_address                = "169.254.33.2"
            bgp_peer_asn                    = 64512
            bgp_session_range               = "169.254.33.1/30"
            peer_external_gateway_interface = 0
            psk_secret_id                   = "vpn-bad-reg-psk"
            psk_secret_location             = "US_EAST4"
            vpn_gateway_interface           = 0
          }
        }
      }
    }
  }

  expect_failures = [
    var.peers,
  ]
}

run "plan_rejects_empty_psk_secret_payload" {
  command = plan

  override_data {
    target = data.google_secret_manager_secret_version.tunnel_psk
    values = {
      secret_data = ""
    }
  }

  expect_failures = [
    data.google_secret_manager_secret_version.tunnel_psk,
  ]
}

run "plan_rejects_empty_regional_psk_secret_payload" {
  command = plan

  variables {
    peers = {
      reg = {
        redundancy_type     = "SINGLE_IP_INTERNALLY_REDUNDANT"
        external_interfaces = ["198.51.100.10"]
        tunnels = {
          tun-0 = {
            bgp_peer_address                = "169.254.34.2"
            bgp_peer_asn                    = 64512
            bgp_session_range               = "169.254.34.1/30"
            peer_external_gateway_interface = 0
            psk_secret_id                   = "vpn-empty-reg-psk"
            psk_secret_location             = "us-east4"
            vpn_gateway_interface           = 0
          }
        }
      }
    }
  }

  override_data {
    target = data.google_secret_manager_regional_secret_version.tunnel_psk
    values = {
      secret_data = "   "
    }
  }

  expect_failures = [
    data.google_secret_manager_regional_secret_version.tunnel_psk,
  ]
}
