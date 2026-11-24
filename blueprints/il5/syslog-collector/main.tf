# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

locals {
  health_check_ranges = [
    "35.191.0.0/16",
    "130.211.0.0/22",
  ]
  # Regional MIGs require max_surge.fixed to be 0 or >= the number of zones.
  max_surge_fixed = max(
    3,
    length(coalesce(var.distribution_zones, []))
  )
  required_apis = toset([
    "compute.googleapis.com",
    "logging.googleapis.com",
    "monitoring.googleapis.com",
    "secretmanager.googleapis.com",
  ])
  secret_project_id = coalesce(var.secret_project_id, var.project_id)
  shared_vpc_subnet_members = (
    var.grant_shared_vpc_subnet_iam
    && var.network_project_id != var.project_id
    ? {
      cloudservices = format(
        "serviceAccount:%s@cloudservices.gserviceaccount.com",
        data.google_project.current.number,
      )
      syslog_sa = module.syslog-sa.iam_email
    }
    : {}
  )
  startup_script = templatefile(
    "${path.module}/templates/startup.sh.tpl",
    {
      client_ca_secret_id   = var.tls_secret_ids.client_ca_cert
      health_check_port     = var.health_check_port
      log_project_id        = var.project_id
      region                = var.region
      secret_project_id     = local.secret_project_id
      server_cert_secret_id = var.tls_secret_ids.server_cert
      server_key_secret_id  = var.tls_secret_ids.server_key
      syslog_framing_format = var.syslog_framing_format
      syslog_port           = var.syslog_port
    }
  )
  template_zone = (
    var.distribution_zones == null
    ? "${var.region}-a"
    : var.distribution_zones[0]
  )
  tls_secret_ids = {
    client_ca_cert = var.tls_secret_ids.client_ca_cert
    server_cert    = var.tls_secret_ids.server_cert
    server_key     = var.tls_secret_ids.server_key
  }
}

data "google_project" "current" {
  project_id = var.project_id
}

resource "google_project_service" "apis" {
  for_each           = var.enable_apis ? local.required_apis : toset([])
  project            = var.project_id
  service            = each.value
  disable_on_destroy = false
}

# Wait 60s after enabling APIs so IAM recognizes the Compute Engine and
# Google APIs service agents on fresh workload projects.
resource "time_sleep" "service_agent_propagation" {
  count           = var.enable_apis || var.manage_kms_iam ? 1 : 0
  create_duration = "60s"
  depends_on      = [google_project_service.apis]
}

data "google_compute_network" "vpc" {
  name    = var.network_name
  project = var.network_project_id
}

data "google_compute_subnetwork" "subnet" {
  name    = var.subnetwork_name
  project = var.network_project_id
  region  = var.region
}

module "syslog-sa" {
  source       = "../../../modules/iam-service-account"
  project_id   = var.project_id
  name         = "${var.name_prefix}-sa"
  display_name = "Syslog Collector Service Account"
  description  = "Least-privilege service account for syslog collectors."
  iam_project_roles = {
    (var.project_id) = [
      "roles/logging.logWriter",
      "roles/monitoring.metricWriter",
    ]
  }
  depends_on = [google_project_service.apis]
}

resource "google_compute_subnetwork_iam_member" "shared_vpc_network_user" {
  for_each   = local.shared_vpc_subnet_members
  project    = var.network_project_id
  region     = var.region
  subnetwork = var.subnetwork_name
  role       = "roles/compute.networkUser"
  member     = each.value
  depends_on = [time_sleep.service_agent_propagation]
}

# Grant Secret Manager access strictly per TLS secret, never project-wide.
resource "google_secret_manager_regional_secret_iam_member" "tls_secret" {
  for_each   = local.tls_secret_ids
  project    = local.secret_project_id
  location   = var.region
  secret_id  = each.value
  role       = "roles/secretmanager.secretAccessor"
  member     = module.syslog-sa.iam_email
  depends_on = [google_project_service.apis]
}

resource "google_kms_crypto_key_iam_member" "compute_cmek" {
  count         = var.manage_kms_iam ? 1 : 0
  crypto_key_id = var.kms_key_id
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member = format(
    "serviceAccount:service-%s@compute-system.iam.gserviceaccount.com",
    data.google_project.current.number
  )
  depends_on = [time_sleep.service_agent_propagation]
}

module "syslog-template" {
  source               = "../../../modules/compute-vm"
  project_id           = var.project_id
  zone                 = local.template_zone
  name                 = "${var.name_prefix}-tpl"
  description          = "Hardened Fluent Bit mTLS syslog collector template."
  machine_type         = var.machine_type
  confidential_compute = "SEV"
  create_template = {
    regional = true
  }
  boot_disk = {
    auto_delete = true
    initialize_params = {
      size = var.boot_disk_size_gb
      type = "pd-balanced"
    }
    source = {
      image = var.golden_image
    }
  }
  encryption = {
    encrypt_boot      = true
    kms_key_self_link = var.kms_key_id
  }
  labels = var.labels
  metadata = {
    block-project-ssh-keys = "TRUE"
    enable-oslogin         = "TRUE"
    serial-port-enable     = "false"
  }
  metadata_startup_script = local.startup_script
  network_interfaces = [{
    nat        = false
    network    = data.google_compute_network.vpc.self_link
    subnetwork = data.google_compute_subnetwork.subnet.self_link
  }]
  service_account = {
    email  = module.syslog-sa.email
    scopes = ["https://www.googleapis.com/auth/cloud-platform"]
  }
  shielded_config = {
    enable_integrity_monitoring = true
    enable_secure_boot          = true
    enable_vtpm                 = true
  }
  depends_on = [
    google_kms_crypto_key_iam_member.compute_cmek,
    google_secret_manager_regional_secret_iam_member.tls_secret,
    time_sleep.service_agent_propagation,
  ]
}

module "syslog-mig" {
  source            = "../../../modules/compute-mig"
  project_id        = var.project_id
  location          = var.region
  name              = "${var.name_prefix}-mig"
  description       = "Regional HA Fluent Bit mTLS syslog collector MIG."
  instance_template = module.syslog-template.template.self_link
  auto_healing_policies = {
    initial_delay_sec = 180
  }
  autoscaler_config = {
    cooldown_period = 90
    max_replicas    = var.max_replicas
    min_replicas    = var.min_replicas
    scaling_signals = {
      cpu_utilization = {
        optimize_availability = true
        target                = 0.7
      }
    }
  }
  distribution_policy = {
    target_shape = "EVEN"
    zones        = var.distribution_zones
  }
  health_check_config = {
    check_interval_sec  = 10
    description         = "MIG autohealing probe for Fluent Bit health API."
    enable_logging      = true
    healthy_threshold   = 2
    timeout_sec         = 5
    unhealthy_threshold = 3
    http = {
      port         = var.health_check_port
      request_path = "/api/v1/health"
    }
  }
  instance_lifecycle_policy = {
    default_action_on_failure = "REPAIR"
    on_failed_health_check    = "DEFAULT_ACTION"
    on_repair = {
      allow_changing_zone = "YES"
      force_update        = "YES"
    }
  }
  update_policy = {
    minimal_action               = "REPLACE"
    most_disruptive_action       = "REPLACE"
    min_ready_sec                = 60
    regional_redistribution_type = "PROACTIVE"
    replacement_method           = "SUBSTITUTE"
    type                         = "PROACTIVE"
    max_surge = {
      fixed = local.max_surge_fixed
    }
    max_unavailable = {
      fixed = 0
    }
  }
  depends_on = [google_compute_subnetwork_iam_member.shared_vpc_network_user]
}

module "syslog-ilb" {
  source      = "../../../modules/net-lb-int"
  project_id  = var.project_id
  region      = var.region
  name        = "${var.name_prefix}-ilb"
  description = "Internal passthrough NLB for RFC 5425 mTLS syslog."
  labels      = var.labels
  vpc_config = {
    network    = data.google_compute_network.vpc.self_link
    subnetwork = data.google_compute_subnetwork.subnet.self_link
  }
  backend_service_config = {
    connection_draining_timeout_sec = 60
    protocol                        = "TCP"
    session_affinity                = "CLIENT_IP"
    log_config = {
      enable      = true
      sample_rate = 1.0
    }
  }
  backends = [{
    group = module.syslog-mig.group_manager.instance_group
  }]
  forwarding_rules_config = {
    "" = {
      address       = var.ilb_ip_address
      global_access = var.ilb_global_access
      ports         = [tostring(var.syslog_port)]
      protocol      = "TCP"
    }
  }
  health_check_config = {
    check_interval_sec  = 5
    description         = "Regional ILB probe for Fluent Bit health API."
    enable_logging      = true
    healthy_threshold   = 2
    is_regional         = true
    timeout_sec         = 5
    unhealthy_threshold = 2
    http = {
      port         = var.health_check_port
      request_path = "/api/v1/health"
    }
  }
}

module "syslog-firewall" {
  source     = "../../../modules/net-vpc-firewall"
  project_id = var.network_project_id
  network    = data.google_compute_network.vpc.self_link
  default_rules_config = {
    disabled = true
  }
  ingress_rules = {
    "${var.name_prefix}-allow-syslog" = {
      description          = "Allow RFC 5425 mTLS syslog from approved CIDRs."
      source_ranges        = var.allowed_source_ranges
      targets              = [module.syslog-sa.email]
      use_service_accounts = true
      enable_logging = {
        include_metadata = true
      }
      rules = [{
        ports    = [tostring(var.syslog_port)]
        protocol = "tcp"
      }]
    }
    "${var.name_prefix}-allow-hc" = {
      description          = "Allow Google Cloud health probes to Fluent Bit."
      source_ranges        = local.health_check_ranges
      targets              = [module.syslog-sa.email]
      use_service_accounts = true
      enable_logging = {
        include_metadata = true
      }
      rules = [{
        ports    = [tostring(var.health_check_port)]
        protocol = "tcp"
      }]
    }
  }
}
