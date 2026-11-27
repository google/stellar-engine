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

mock_provider "google" {
  alias = "billing"
}

mock_provider "google-beta" {}

mock_provider "google-beta" {
  alias = "billing"
}

mock_provider "external" {}

mock_provider "local" {}

mock_provider "random" {}

mock_provider "time" {}

mock_provider "tls" {}

override_data {
  target = data.google_compute_zones.available
  values = {
    names = ["us-east4-a", "us-east4-b", "us-east4-c"]
  }
}

override_data {
  target = data.external.openssl
  values = {
    result = {
      hash = "$5$testsalt$testhashvalue"
    }
  }
}

variables {
  alert_email = "admin@example.com"
  automation = {
    outputs_bucket = "test-bucket"
  }
  billing_account = {
    id = "000000-AAAAAA-000000"
  }
  cidrs = {
    healthchecks = ["35.191.0.0/16", "130.211.0.0/22"]
    iap          = ["35.235.240.0/20"]
    internal     = ["10.0.0.0/8"]
  }
  envs_folders = {
    Prod = { admin = "group:prod-admins@example.com" }
    Int  = { admin = "group:int-admins@example.com" }
  }
  folder_ids = {
    networking = "folders/123456789012"
  }
  organization = {
    domain      = "example.com"
    id          = 123456789012
    customer_id = "C00000000"
  }
  prefix = "test"
  proxy_subnets = {
    Prod = "10.1.1.0/24"
    Int  = "10.1.2.0/24"
  }
  regions = {
    primary = "us-east4"
  }
  subnets = {
    landing = [
      { name = "landing-default", ip_cidr_range = "10.64.0.0/24", region = "us-east4" },
    ]
    dmz = [
      { name = "dmz-default", ip_cidr_range = "10.64.128.0/24", region = "us-east4" },
    ]
    mgmt = [
      { name = "mgmt-default", ip_cidr_range = "10.64.129.0/24", region = "us-east4" },
    ]
    prod = [
      { name = "prod-tenant-1-subnet", ip_cidr_range = "10.201.0.0/16", region = "us-east4", tenant = "ten-1" },
    ]
    int = [
      { name = "int-tenant-1-subnet", ip_cidr_range = "10.150.0.0/16", region = "us-east4", tenant = "ten-1" },
    ]
  }
  tenant_accounts = {}
}

run "defaults_preserve_peering_and_legacy_behavior" {
  command = plan

  providers = {
    google              = google
    google.billing      = google.billing
    google-beta         = google-beta
    google-beta.billing = google-beta.billing
    external            = external
    local               = local
    random              = random
    time                = time
    tls                 = tls
  }

  assert {
    condition     = length(module.peering-envs) == 2
    error_message = "Default transit_mode = peering must plan classic VPC peering for every environment spoke."
  }

  assert {
    condition     = length(google_compute_route.ncc_spoke_default) == 0
    error_message = "Default transit_mode = peering must not plan NCC spoke default routes."
  }

  assert {
    condition     = length(google_network_connectivity_hub.default) == 0
    error_message = "Default transit_mode = peering must not plan NCC hubs."
  }

  assert {
    condition     = length(google_network_connectivity_spoke.vpcs) == 0
    error_message = "Default transit_mode = peering must not plan NCC spokes."
  }

  assert {
    condition     = length(module.hub-psc-addresses) == 0 && length(module.env-psc-addresses) == 0
    error_message = "PSC endpoints must remain disabled by default."
  }

  assert {
    condition     = length(module.vdss-mgmt-dmz-dns-policy-googleapis) == 0
    error_message = "Dedicated mgmt/dmz PGA DNS policy must remain disabled when PSC is disabled."
  }

  assert {
    condition     = length(module.env-dns-policy-googleapis) == 0
    error_message = "Per-spoke DNS response policies must remain disabled by default."
  }

  assert {
    condition     = length(module.landing-dns-forwarding-zones) == 0
    error_message = "Hybrid DNS forwarding zones must remain empty by default."
  }

  assert {
    condition     = length(module.ngfw-admin-password-secret) == 0
    error_message = "Regional NGFW admin password secret must remain disabled by default."
  }

  assert {
    condition     = length(module.ngfw-ilb-addresses) == 0
    error_message = "Static ILB VIP reservations must remain disabled by default."
  }

  assert {
    condition = (
      toset(keys(local.tfvars)) ==
      toset(["host_project_ids", "host_project_numbers", "envs", "vdss"])
    )
    error_message = "Default local.tfvars must keep the exact legacy key set when NCC and PSC are disabled."
  }

  assert {
    condition = (
      local._ngfw_mig_health_check_config.tcp.port == 22 &&
      local._ngfw_mig_health_check_config.enable_logging == false &&
      local._ngfw_ilb_health_check_config.tcp.port == 22 &&
      local._ngfw_ilb_health_check_config.enable_logging == true &&
      local._ngfw_ilb_health_check_config.https == null &&
      local._ngfw_ilb_backend_service_config.connection_tracking == null
    )
    error_message = "Default NGFW health check must remain TCP/22 with legacy MIG/ILB logging defaults."
  }

  assert {
    condition = (
      strcontains(
        templatefile("./templates/bootstrap.xml.tpl", {
          password_hash            = "mock"
          ssh_pubkey               = "ssh-rsa mock"
          healthcheck_cidrs        = var.cidrs["healthchecks"]
          iap_cidrs                = var.cidrs["iap"]
          return_routes            = {}
          lz_gateway_ip            = "10.64.0.1"
          min_password_length      = local._ngfw_min_password_length
          timezone                 = local._ngfw_timezone
          login_banner             = local._ngfw_login_banner
          enable_https_healthcheck = var.ngfw_health_check.protocol == "HTTPS"
        }),
        "<minimum-length>12</minimum-length>"
      ) &&
      local._ngfw_timezone == "US/Pacific" &&
      local._ngfw_login_banner == ""
    )
    error_message = "Default bootstrap XML must preserve legacy password length, timezone, and omitted login banner."
  }

  assert {
    condition     = !endswith(google_storage_bucket_object.init_cfg["primary"].content, "\n")
    error_message = "init-cfg.txt must preserve exact origin/main bytes without trailing newline."
  }
}

run "ncc_transit_and_per_vpc_psc_plan_cleanly" {
  command = plan

  override_resource {
    target          = module.ilb-nva-vdss["primary"].google_compute_forwarding_rule.default[""]
    override_during = plan
    values = {
      id         = "projects/test-net-vdss-host/regions/us-east4/forwardingRules/nva-vdss-primary"
      ip_address = "10.64.0.10"
    }
  }

  providers = {
    google              = google
    google.billing      = google.billing
    google-beta         = google-beta
    google-beta.billing = google-beta.billing
    external            = external
    local               = local
    random              = random
    time                = time
    tls                 = tls
  }

  variables {
    transit_mode = "ncc"
    psc_google_apis = {
      enabled = true
      bundle  = "vpc-sc"
    }
  }

  assert {
    condition     = length(module.peering-envs) == 0 && length(time_sleep.peering_delay) == 0
    error_message = "transit_mode = ncc must skip classic spoke-to-landing VPC peering."
  }

  assert {
    condition = (
      toset(keys(google_compute_route.ncc_spoke_default)) ==
      toset(["Prod", "Int"]) &&
      alltrue([
        for _, r in google_compute_route.ncc_spoke_default :
        r.dest_range == "0.0.0.0/0" &&
        r.priority == 100 &&
        r.next_hop_ilb == "10.64.0.10"
      ])
    )
    error_message = "transit_mode = ncc must create one 0.0.0.0/0 priority-100 NVA ILB route per environment spoke targeting the ILB IPv4 VIP."
  }

  assert {
    condition = (
      contains(keys(google_network_connectivity_hub.default), "main") &&
      google_network_connectivity_hub.default["main"].preset_topology == "STAR"
    )
    error_message = "transit_mode = ncc must create the main STAR NCC hub."
  }

  assert {
    condition = (
      toset(keys(google_network_connectivity_spoke.vpcs)) ==
      toset(["main/landing", "main/prod", "main/int"])
    )
    error_message = "NCC spokes must include landing and environment spokes only, excluding mgmt-vpc."
  }

  assert {
    condition = alltrue(flatten([
      for _, grp in google_network_connectivity_group.default : [
        for aa in grp.auto_accept : [
          for p in aa.auto_accept_projects : p != "*"
        ]
      ]
    ]))
    error_message = "NCC groups must never configure wildcard '*' auto_accept."
  }

  assert {
    condition     = length(module.hub-psc-addresses) == 1
    error_message = "psc_google_apis.enabled = true must plan a hub PSC endpoint."
  }

  assert {
    condition     = length(module.vdss-mgmt-dmz-dns-policy-googleapis) == 1
    error_message = "psc_google_apis.enabled = true must plan a dedicated PGA DNS policy for vdss-mgmt-0 and vdss-dmz-0."
  }

  assert {
    condition = (
      local._pga_mgmt_dmz_dns_rules["googleapis-restricted"].local_data["A"].rrdatas ==
      ["199.36.153.4", "199.36.153.5", "199.36.153.6", "199.36.153.7"] &&
      local._pga_mgmt_dmz_dns_rules["accounts"].behavior == "bypassResponsePolicy"
    )
    error_message = "mgmt/dmz PGA DNS policy must map restricted.googleapis.com. to 199.36.153.4/30 and bypass accounts.google.com."
  }

  assert {
    condition     = toset(keys(module.env-psc-addresses)) == toset(["Prod", "Int"])
    error_message = "psc_google_apis.enabled = true must plan one PSC endpoint per environment spoke."
  }

  assert {
    condition     = toset(keys(module.env-dns-policy-googleapis)) == toset(["Prod", "Int"])
    error_message = "psc_google_apis.enabled = true must plan one DNS response policy per environment spoke."
  }

  assert {
    condition = (
      local._psc_service_directory_registration.region == "us-east4" &&
      local._psc_service_directory_registration.namespace == null
    )
    error_message = "PSC endpoints must default Service Directory registration region to regions.primary when service_directory_registration is unset."
  }

  assert {
    condition = (
      local._psc_hub_dns_rules["accounts"].behavior == "bypassResponsePolicy" &&
      local._psc_hub_dns_rules["googleapis-restricted"].local_data["A"].rrdatas == [var.psc_google_apis.hub_ip] &&
      local._psc_hub_dns_rules["googleapis-private"].behavior == "bypassResponsePolicy" &&
      length(local._psc_hub_dns_rules["googleapis-private"].local_data) == 0 &&
      local._psc_hub_dns_rules["dl"].behavior == "bypassResponsePolicy" &&
      local._psc_hub_dns_rules["packages-cloud"].behavior == "bypassResponsePolicy"
    )
    error_message = "Under bundle = vpc-sc, PSC DNS policies must map restricted.googleapis.com. to the PSC IP and bypass accounts and non-VPC-SC private domains."
  }
}

run "ngfw_hardening_stig_secret_and_dns_forwarding_plan_cleanly" {
  command = plan

  providers = {
    google              = google
    google.billing      = google.billing
    google-beta         = google-beta
    google-beta.billing = google-beta.billing
    external            = external
    local               = local
    random              = random
    time                = time
    tls                 = tls
  }

  variables {
    psc_google_apis = {
      enabled = true
      bundle  = "vpc-sc"
    }
    ngfw_health_check = {
      protocol       = "HTTPS"
      port           = 443
      request_path   = "/unauth/php/health.php"
      enable_logging = true
    }
    ngfw_ilb_config = {
      connection_draining_timeout_sec = 0
      persist_conn_on_unhealthy       = "NEVER_PERSIST"
      trusted_static_ips = {
        "us-east4" = "10.64.0.10"
      }
      untrusted_static_ips = {
        "us-east4" = "10.64.128.10"
      }
    }
    ngfw_stig_config = {
      min_password_length = 16
      login_banner        = "Authorized USG use only & monitored."
      timezone            = "UTC"
    }
    ngfw_admin_password_secret = {
      enabled          = true
      wo_version       = 1
      accessor_members = ["group:net-admins@example.com"]
    }
    dns_forwarding_zones = {
      onprem = {
        domain = "onprem.example.com."
        forwarders = {
          "10.10.0.53" = "private"
          "10.10.0.54" = "private"
        }
      }
    }
  }

  assert {
    condition = (
      local._ngfw_mig_health_check_config.https.port == 443 &&
      local._ngfw_mig_health_check_config.enable_logging == true &&
      local._ngfw_ilb_health_check_config.https.port == 443 &&
      local._ngfw_ilb_health_check_config.https.request_path == "/unauth/php/health.php" &&
      local._ngfw_ilb_health_check_config.enable_logging == true &&
      local._ngfw_ilb_health_check_config.tcp == null &&
      local._ngfw_ilb_backend_service_config.connection_tracking.persist_conn_on_unhealthy == "NEVER_PERSIST"
    )
    error_message = "HTTPS 443 health check, explicit enable_logging, and NEVER_PERSIST ILB settings must wire into MIG and ILB configs."
  }

  assert {
    condition = (
      strcontains(
        templatefile("./templates/bootstrap.xml.tpl", {
          password_hash            = "mock"
          ssh_pubkey               = "ssh-rsa mock"
          healthcheck_cidrs        = var.cidrs["healthchecks"]
          iap_cidrs                = var.cidrs["iap"]
          return_routes            = {}
          lz_gateway_ip            = "10.64.0.1"
          min_password_length      = local._ngfw_min_password_length
          timezone                 = local._ngfw_timezone
          login_banner             = local._ngfw_login_banner
          enable_https_healthcheck = var.ngfw_health_check.protocol == "HTTPS"
        }),
        "<minimum-length>16</minimum-length>"
      ) &&
      strcontains(
        templatefile("./templates/bootstrap.xml.tpl", {
          password_hash            = "mock"
          ssh_pubkey               = "ssh-rsa mock"
          healthcheck_cidrs        = var.cidrs["healthchecks"]
          iap_cidrs                = var.cidrs["iap"]
          return_routes            = {}
          lz_gateway_ip            = "10.64.0.1"
          min_password_length      = local._ngfw_min_password_length
          timezone                 = local._ngfw_timezone
          login_banner             = local._ngfw_login_banner
          enable_https_healthcheck = var.ngfw_health_check.protocol == "HTTPS"
        }),
        "<login-banner>Authorized USG use only &amp; monitored.</login-banner>"
      ) &&
      strcontains(
        templatefile("./templates/bootstrap.xml.tpl", {
          password_hash            = "mock"
          ssh_pubkey               = "ssh-rsa mock"
          healthcheck_cidrs        = var.cidrs["healthchecks"]
          iap_cidrs                = var.cidrs["iap"]
          return_routes            = {}
          lz_gateway_ip            = "10.64.0.1"
          min_password_length      = local._ngfw_min_password_length
          timezone                 = local._ngfw_timezone
          login_banner             = local._ngfw_login_banner
          enable_https_healthcheck = var.ngfw_health_check.protocol == "HTTPS"
        }),
        "<https>yes</https>"
      ) &&
      local._ngfw_timezone == "UTC"
    )
    error_message = "STIG and HTTPS health check settings must render cleanly in bootstrap.xml."
  }

  assert {
    condition     = length(module.ngfw-ilb-addresses) == 1
    error_message = "Static ILB VIP configuration must reserve internal addresses."
  }

  assert {
    condition     = length(module.ngfw-admin-password-secret) == 1 && output.ngfw_password == null
    error_message = "Enabling ngfw_admin_password_secret must create the regional secret and null out ngfw_password."
  }

  assert {
    condition     = contains(keys(module.landing-dns-forwarding-zones), "onprem")
    error_message = "dns_forwarding_zones must create forwarding zones in the VDSS host project."
  }

  assert {
    condition = (
      toset(keys(module.env-dns-peer-forwarding-zones)) ==
      toset(["prod-onprem", "int-onprem"])
    )
    error_message = "With per-VPC PSC enabled, each spoke must peer hybrid forwarding domains to landing."
  }
}

run "rejects_invalid_transit_mode" {
  command = plan

  providers = {
    google              = google
    google.billing      = google.billing
    google-beta         = google-beta
    google-beta.billing = google-beta.billing
    external            = external
    local               = local
    random              = random
    time                = time
    tls                 = tls
  }

  variables {
    transit_mode = "invalid"
  }

  expect_failures = [
    var.transit_mode,
  ]
}

run "rejects_wildcard_ncc_auto_accept" {
  command = plan

  providers = {
    google              = google
    google.billing      = google.billing
    google-beta         = google-beta
    google-beta.billing = google-beta.billing
    external            = external
    local               = local
    random              = random
    time                = time
    tls                 = tls
  }

  variables {
    ncc_hubs = {
      custom = {
        groups = {
          edge = {
            auto_accept = ["*"]
          }
        }
      }
    }
  }

  expect_failures = [
    var.ncc_hubs,
  ]
}

run "rejects_mgmt_vpc_on_ncc_hub" {
  command = plan

  providers = {
    google              = google
    google.billing      = google.billing
    google-beta         = google-beta
    google-beta.billing = google-beta.billing
    external            = external
    local               = local
    random              = random
    time                = time
    tls                 = tls
  }

  variables {
    ncc_hubs = {
      custom = {
        spokes = {
          vpcs = {
            mgmt = {
              vpc = "projects/my-project/global/networks/vdss-mgmt-0"
            }
          }
        }
      }
    }
  }

  expect_failures = [
    var.ncc_hubs,
  ]
}

run "rejects_root_domain_dns_forwarding_zone" {
  command = plan

  providers = {
    google              = google
    google.billing      = google.billing
    google-beta         = google-beta
    google-beta.billing = google-beta.billing
    external            = external
    local               = local
    random              = random
    time                = time
    tls                 = tls
  }

  variables {
    dns_forwarding_zones = {
      root = {
        domain = "."
        forwarders = {
          "10.10.0.53" = "private"
        }
      }
    }
  }

  expect_failures = [
    var.dns_forwarding_zones,
  ]
}

run "rejects_short_stig_password_length" {
  command = plan

  providers = {
    google              = google
    google.billing      = google.billing
    google-beta         = google-beta
    google-beta.billing = google-beta.billing
    external            = external
    local               = local
    random              = random
    time                = time
    tls                 = tls
  }

  variables {
    ngfw_stig_config = {
      min_password_length = 12
    }
  }

  expect_failures = [
    var.ngfw_stig_config,
  ]
}

run "rejects_colliding_psc_forwarding_rule_names" {
  command = plan

  providers = {
    google              = google
    google.billing      = google.billing
    google-beta         = google-beta
    google-beta.billing = google-beta.billing
    external            = external
    local               = local
    random              = random
    time                = time
    tls                 = tls
  }

  variables {
    prefix = "a"
    envs_folders = {
      "env01234567890123a" = { admin = "group:a-admins@example.com" }
      "env01234567890123b" = { admin = "group:b-admins@example.com" }
    }
    proxy_subnets = {
      "env01234567890123a" = "10.1.1.0/24"
      "env01234567890123b" = "10.1.2.0/24"
    }
    subnets = {
      landing = [
        { name = "landing-default", ip_cidr_range = "10.64.0.0/24", region = "us-east4" },
      ]
      dmz = [
        { name = "dmz-default", ip_cidr_range = "10.64.128.0/24", region = "us-east4" },
      ]
      mgmt = [
        { name = "mgmt-default", ip_cidr_range = "10.64.129.0/24", region = "us-east4" },
      ]
      env01234567890123a = [
        { name = "a-tenant-1-subnet", ip_cidr_range = "10.201.0.0/16", region = "us-east4", tenant = "ten-1" },
      ]
      env01234567890123b = [
        { name = "b-tenant-1-subnet", ip_cidr_range = "10.150.0.0/16", region = "us-east4", tenant = "ten-1" },
      ]
    }
    psc_google_apis = {
      enabled = true
      bundle  = "vpc-sc"
    }
  }

  expect_failures = [
    var.psc_google_apis,
  ]
}

run "defaults_keep_legacy_dns_policy_rules_without_psc" {
  command = plan

  providers = {
    google              = google
    google.billing      = google.billing
    google-beta         = google-beta
    google-beta.billing = google-beta.billing
    external            = external
    local               = local
    random              = random
    time                = time
    tls                 = tls
  }

  variables {
    dns_policy_rules = {
      googleapis-all = {
        dns_name   = "*.googleapis.com."
        local_data = { CNAME = { rrdatas = ["private.googleapis.com."] } }
      }
      googleapis-private = {
        dns_name = "private.googleapis.com."
        local_data = {
          A = {
            rrdatas = [
              "199.36.153.8", "199.36.153.9", "199.36.153.10", "199.36.153.11"
            ]
          }
        }
      }
    }
  }

  assert {
    condition     = local._psc_hub_dns_rules == var.dns_policy_rules
    error_message = "Default mode must pass dns_policy_rules through as-is."
  }

  assert {
    condition = (
      length(module.vdss-mgmt-dmz-dns-policy-googleapis) == 0 &&
      length(module.env-dns-policy-googleapis) == 0
    )
    error_message = "Default mode must not plan PSC DNS response policies."
  }
}

run "psc_keeps_custom_dns_rules_and_factory_google_api_rules" {
  command = plan

  providers = {
    google              = google
    google.billing      = google.billing
    google-beta         = google-beta
    google-beta.billing = google-beta.billing
    external            = external
    local               = local
    random              = random
    time                = time
    tls                 = tls
  }

  variables {
    factories_config = {
      data_dir = "./data"
    }
    psc_google_apis = {
      enabled = true
      bundle  = "vpc-sc"
    }
    dns_policy_rules = {
      onprem = {
        dns_name = "onprem.example.com."
        behavior = "bypassResponsePolicy"
      }
      onprem-api = {
        dns_name   = "api.onprem.example.com."
        local_data = { A = { rrdatas = ["10.10.0.80"] } }
      }
    }
  }

  assert {
    condition = (
      local._psc_dns_policy_rules_file == "./data/dns-policy-rules.yaml"
    )
    error_message = "An unset dns_policy_rules_file must follow data_dir."
  }

  assert {
    condition = (
      local._psc_reserved_dns_rules["googleapis-all"] == "*.googleapis.com" &&
      local._dns_policy_context.addresses.googleapis_cname ==
      "restricted.googleapis.com."
    )
    error_message = "The rules factory must own googleapis-all under vpc-sc."
  }

  assert {
    condition = alltrue([
      for rules in [
        local._psc_hub_dns_rules,
        local._psc_spoke_dns_rules["Prod"],
        local._psc_spoke_dns_rules["Int"],
        local._pga_mgmt_dmz_dns_rules,
      ] :
      rules["onprem"].behavior == "bypassResponsePolicy" &&
      contains(keys(rules), "onprem-api") &&
      !contains(keys(rules), "googleapis-all")
    ])
    error_message = "Custom rules must merge without overriding the factory."
  }

  assert {
    condition = (
      local._psc_hub_dns_rules["googleapis-restricted"].local_data["A"]
      .rrdatas == ["10.255.255.1"]
    )
    error_message = "Hub PSC DNS must answer with the hub PSC endpoint IP."
  }
}

run "psc_rejects_legacy_google_api_dns_policy_rules" {
  command = plan

  providers = {
    google              = google
    google.billing      = google.billing
    google-beta         = google-beta
    google-beta.billing = google-beta.billing
    external            = external
    local               = local
    random              = random
    time                = time
    tls                 = tls
  }

  variables {
    psc_google_apis = {
      enabled = true
      bundle  = "vpc-sc"
    }
    dns_policy_rules = {
      googleapis-all = {
        dns_name   = "*.googleapis.com."
        local_data = { CNAME = { rrdatas = ["private.googleapis.com."] } }
      }
    }
  }

  expect_failures = [
    var.dns_policy_rules,
  ]
}

run "psc_rejects_dns_policy_rule_dns_name_collision" {
  command = plan

  providers = {
    google              = google
    google.billing      = google.billing
    google-beta         = google-beta
    google-beta.billing = google-beta.billing
    external            = external
    local               = local
    random              = random
    time                = time
    tls                 = tls
  }

  variables {
    psc_google_apis = {
      enabled = true
      bundle  = "vpc-sc"
    }
    dns_policy_rules = {
      custom-storage = {
        dns_name = "Storage.Cloud.Google.com"
        behavior = "bypassResponsePolicy"
      }
    }
  }

  expect_failures = [
    var.dns_policy_rules,
  ]
}

run "psc_rejects_dns_policy_rule_targeting_pga_name" {
  command = plan

  providers = {
    google              = google
    google.billing      = google.billing
    google-beta         = google-beta
    google-beta.billing = google-beta.billing
    external            = external
    local               = local
    random              = random
    time                = time
    tls                 = tls
  }

  variables {
    psc_google_apis = {
      enabled = true
      bundle  = "all-apis"
    }
    dns_policy_rules = {
      googleusercontent-all = {
        dns_name   = "*.googleusercontent.com."
        local_data = { CNAME = { rrdatas = ["restricted.googleapis.com"] } }
      }
    }
  }

  expect_failures = [
    var.dns_policy_rules,
  ]
}

run "psc_rejects_dns_policy_rule_targeting_pga_vip" {
  command = plan

  providers = {
    google              = google
    google.billing      = google.billing
    google-beta         = google-beta
    google-beta.billing = google-beta.billing
    external            = external
    local               = local
    random              = random
    time                = time
    tls                 = tls
  }

  variables {
    psc_google_apis = {
      enabled = true
      bundle  = "vpc-sc"
    }
    dns_policy_rules = {
      apis-onprem-alias = {
        dns_name   = "apis.onprem.example.com."
        local_data = { A = { rrdatas = ["199.36.153.8"] } }
      }
    }
  }

  expect_failures = [
    var.dns_policy_rules,
  ]
}

run "psc_rejects_missing_dns_policy_rules_file" {
  command = plan

  providers = {
    google              = google
    google.billing      = google.billing
    google-beta         = google-beta
    google-beta.billing = google-beta.billing
    external            = external
    local               = local
    random              = random
    time                = time
    tls                 = tls
  }

  variables {
    factories_config = {
      dns_policy_rules_file = "data/missing-dns-policy-rules.yaml"
    }
    psc_google_apis = {
      enabled = true
      bundle  = "vpc-sc"
    }
  }

  expect_failures = [
    var.factories_config,
  ]
}

run "rejects_http_ngfw_health_check" {
  command = plan

  providers = {
    google              = google
    google.billing      = google.billing
    google-beta         = google-beta
    google-beta.billing = google-beta.billing
    external            = external
    local               = local
    random              = random
    time                = time
    tls                 = tls
  }

  variables {
    ngfw_health_check = {
      protocol = "HTTP"
      port     = 80
    }
  }

  expect_failures = [
    var.ngfw_health_check,
  ]
}
