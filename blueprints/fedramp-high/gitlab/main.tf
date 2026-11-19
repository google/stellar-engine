# Copyright 2025 Google LLC
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

data "google_project" "project" {
  project_id = var.project_id
}

moved {
  from = google_service_account.gitlab-sa
  to   = google_service_account.gitlab_sa
}

resource "google_service_account" "gitlab_sa" {
  project      = var.project_id
  account_id   = var.sa
  display_name = "gitlab-sa"
}
resource "google_project_iam_member" "gke_cluster_admin" {
  project = data.google_project.project.project_id
  role    = "roles/container.admin"
  member  = "serviceAccount:${google_service_account.gitlab_sa.email}"
}

# GKE nodes run as their own account so they do not inherit the roles of the
# GitLab VM account. The account needs no Shared VPC or KMS grant: the GKE and
# Google APIs service agents use the subnet, and the Compute Engine service
# agent uses the boot disk key.
module "gke-node-sa" {
  source = "../../../modules/iam-service-account"
  # Service account IDs allow at most 30 characters.
  name         = "${substr(var.gke_name, 0, 24)}-nodes"
  project_id   = var.project_id
  display_name = "GitLab GKE nodes."
  iam_project_roles = {
    (var.project_id) = [
      "roles/artifactregistry.reader",
      "roles/autoscaling.metricsWriter",
      "roles/logging.logWriter",
      "roles/monitoring.metricWriter",
      "roles/monitoring.viewer",
    ]
  }
}

resource "google_project_service" "compute_api" {
  project            = var.project_id
  service            = "compute.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "container_api" {
  project            = var.project_id
  service            = "container.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "storagetransfer_api" {
  project            = var.project_id
  service            = "storagetransfer.googleapis.com"
  disable_on_destroy = false
}

# Only container.googleapis.com exposes a primary service identity via
# serviceusage.services.generateServiceIdentity; compute.googleapis.com returns
# an empty identity from that API and provisions its agent on API enablement.
resource "google_project_service_identity" "gke_agent" {
  provider   = google-beta
  project    = var.project_id
  service    = "container.googleapis.com"
  depends_on = [google_project_service.container_api]
}

# IAM does not recognize newly created service agents right away, so IAM
# bindings added immediately can fail on first apply.
resource "time_sleep" "service_agent_propagation" {
  create_duration = "60s"

  depends_on = [
    google_project_service.compute_api,
    google_project_service_identity.gke_agent,
  ]
}

# Grant GKE Host Service Agent User Role
resource "google_project_iam_member" "gke_host_agent_use" {
  project    = var.net_project # Project where the GKE cluster is being created
  role       = "roles/container.hostServiceAgentUser"
  member     = google_project_service_identity.gke_agent.member # Use project where the GKE cluster is being created
  depends_on = [time_sleep.service_agent_propagation]
}

resource "google_project_iam_member" "compute_agent_subnet_user" {
  for_each = {
    compute_agent = "serviceAccount:service-${data.google_project.project.number}@compute-system.iam.gserviceaccount.com"
    gke_agent     = google_project_service_identity.gke_agent.member
    cloudservices = "serviceAccount:${data.google_project.project.number}@cloudservices.gserviceaccount.com"
    gitlab_sa     = "serviceAccount:${google_service_account.gitlab_sa.email}"
  }
  project    = var.net_project
  role       = "roles/compute.networkUser"
  member     = each.value
  depends_on = [time_sleep.service_agent_propagation]
}

resource "google_kms_crypto_key_iam_member" "compute_service_agent_kms_permissions" {
  for_each = {
    compute_agent = "serviceAccount:service-${data.google_project.project.number}@compute-system.iam.gserviceaccount.com"
    gke_agent     = google_project_service_identity.gke_agent.member
    cloudservices = "serviceAccount:${data.google_project.project.number}@cloudservices.gserviceaccount.com"
    gitlab_sa     = "serviceAccount:${google_service_account.gitlab_sa.email}"
  }
  crypto_key_id = var.kms_key
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = each.value
  depends_on    = [time_sleep.service_agent_propagation]
}

resource "google_compute_instance_group" "umig" {
  project = var.project_id
  name    = var.instance_name

  instances = [
    module.compute-vm.id
  ]

  named_port {
    name = "http"
    port = "80"
  }

  named_port {
    name = "https"
    port = "443"
  }

  zone = var.zone

  depends_on = [module.compute-vm]
}

# Used for health checks
module "net-firewall" {
  source     = "../../../modules/net-vpc-firewall"
  project_id = var.net_project
  network    = var.network_name
  ingress_rules = {
    gitlab-allow = {
      description   = "Allow health checks to GitLab load balancer."
      source_ranges = ["35.191.0.0/16", "130.211.0.0/22", "209.85.204.0/22", "209.85.152.0/22", "10.1.3.0/24"]
      targets       = ["gitlab"]
      rules         = [{ protocol = "tcp", ports = [80, 443] }]
    }
  }
}

module "compute-vm" {
  source       = "../../../modules/compute-vm"
  name         = var.vm_name
  project_id   = var.project_id
  zone         = var.zone
  machine_type = "n1-standard-8"
  tags         = ["gitlab"]
  shielded_config = {
    enable_secure_boot          = true
    enable_vtpm                 = true
    enable_integrity_monitoring = true
  }
  snapshot_schedules = {
    daily-backup = {
      schedule = {
        daily = {
          days_in_cycle = 1
          start_time    = "04:00"
        }
      }
      retention_policy = {
        max_retention_days = 14
      }
    }
  }

  boot_disk = {
    snapshot_schedule = ["daily-backup"]
    source = {
      image = var.compute_image
    }
    initialize_params = {
      size = 40
    }
  }
  network_interfaces = [
    {
      network    = var.network
      subnetwork = var.subnetwork
    }
  ]
  encryption = {
    kms_key_self_link = var.kms_key
  }
  service_account = {
    email = google_service_account.gitlab_sa.email
  }
  metadata = {
    block-project-ssh-keys = "true" # CIS Compliance Benchmark 4.3
    enable-oslogin         = "TRUE" # CIS Compliance Benchmark 4.4
    startup-script         = <<-EOT
#!/bin/bash
sudo apt update -y
sudo apt upgrade -y
sudo apt install -y curl openssh-server ca-certificates tzdata perl
sudo apt install -y postfix
curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg
echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | sudo tee -a /etc/apt/sources.list.d/google-cloud-sdk.list
sudo apt update -y 
sudo apt install google-cloud-cli -y
sudo apt install kubectl -y
sudo apt install google-cloud-cli-gke-gcloud-auth-plugin -y
GITLAB_INSTALL_SCRIPT="$(mktemp)"
trap 'rm -f "$GITLAB_INSTALL_SCRIPT"' EXIT
curl --fail --show-error --location --output "$GITLAB_INSTALL_SCRIPT" https://packages.gitlab.com/install/repositories/gitlab/gitlab-ee/script.deb.sh
echo "${var.gitlab_install_script_sha256}  $GITLAB_INSTALL_SCRIPT" | sha256sum --check - && sudo bash "$GITLAB_INSTALL_SCRIPT"

sudo EXTERNAL_URL="${var.gitlab_uri}" apt install gitlab-ee -y
      EOT
  }

  depends_on = [google_kms_crypto_key_iam_member.compute_service_agent_kms_permissions]
}

// This creates a self signed certificate
resource "tls_private_key" "default" {
  algorithm = "RSA"
  rsa_bits  = 2048
}

resource "tls_self_signed_cert" "default" {
  private_key_pem = tls_private_key.default.private_key_pem
  subject {
    common_name  = var.gitlab_uri
    organization = "STELLAR EXAMPLE DEPLOYMENT, INC"
  }
  validity_period_hours = 720
  allowed_uses = [
    "key_encipherment",
    "digital_signature",
    "server_auth"
  ]
}

module "application-lb" {
  source     = "../../../modules/net-lb-app-ext-regional"
  project_id = var.project_id
  name       = var.lb_name
  vpc_config = { network = var.network }
  region     = var.region
  backend_service_configs = {
    default = {
      backends = [
        { group = google_compute_instance_group.umig.id }
      ]
      protocol = "HTTP"
    }
  }
  health_check_configs = {
    default = {
      tcp = {
        port = 80
      }
    }
  }
  ssl_certificates = {
    create_configs = {
      default = {
        private_key = tls_private_key.default.private_key_pem
        certificate = tls_self_signed_cert.default.cert_pem
      }
    }
  }
  protocol   = "HTTP"
  depends_on = [google_compute_instance_group.umig]
}

module "cluster" {
  source     = "../../../modules/gke-cluster-standard"
  project_id = var.project_id
  location   = var.region
  name       = var.gke_name
  vpc_config = {
    network    = var.network
    subnetwork = var.subnetwork
    secondary_range_names = {
      pods     = "gitlab-pod-range"
      services = "gitlab-service-range"
    }
  }
  default_nodepool = {
    remove_pool = true
  }
  node_config = {
    boot_disk_kms_key = var.kms_key
    # The default pool exists until Terraform removes it after cluster creation.
    service_account = module.gke-node-sa.email
  }
  access_config = {
    private_nodes = true
    ip_access = {
      authorized_ranges = {
        internal-vms = "10.203.0.0/16"
      }
      private_endpoint_config = {
        global_access = false
      }
    }
  }
  deletion_protection = false
  depends_on          = [google_kms_crypto_key_iam_member.compute_service_agent_kms_permissions, google_project_iam_member.compute_agent_subnet_user, google_project_iam_member.gke_host_agent_use, google_project_iam_member.gke_cluster_admin]
}

moved {
  from = module.gke_node_pool
  to   = module.gke-node-pool
}

module "gke-node-pool" {
  source       = "../../../modules/gke-nodepool"
  project_id   = var.project_id
  location     = var.region
  cluster_name = var.gke_name
  service_account = {
    email = module.gke-node-sa.email
  }
  name       = "nodes"
  node_count = var.nodepool_node_count
  node_config = {
    boot_disk_kms_key = var.kms_key
    # Confidential GKE Nodes need a boot disk larger than 15 GB.
    disk_size_gb = 30
    # Confidential GKE Nodes need a confidential machine type such as N2D.
    confidential_nodes = true
    machine_type       = "n2d-standard-2"
    # CIS GKE Benchmark 4.3.
    metadata = {
      block-project-ssh-keys = "true"
    }
    shielded_instance_config = {
      enable_secure_boot          = true
      enable_integrity_monitoring = true
    }
  }
  # The service account module outputs do not wait for its role grants.
  depends_on = [module.cluster, module.gke-node-sa]
}
