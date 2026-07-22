/**
 * Copyright 2026 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
locals {
  # --- General Configuration ---
  # A 30-second delay to ensure IAM permissions fully propagate before dependent
  # resources are created, preventing common race condition errors.
  iam_propagation_wait_duration = "30s"

  # --- API Enablement ---
  # Collect all unique project IDs where resources are provisioned or consumed.
  all_gke_project_ids_for_api_enablement = toset(distinct(
    [
      var.main_project_id,
      var.landing_project_id,
      var.core_project_id
    ]
  ))

  # Common set of APIs required for GKE clusters and related resources.
  gke_required_apis = toset([
    "container.googleapis.com",
    "containerregistry.googleapis.com",
    "gkehub.googleapis.com",
    "iam.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "compute.googleapis.com",
    "logging.googleapis.com",
    "monitoring.googleapis.com",
    "cloudkms.googleapis.com"
  ])

  # Create a flattened map of all project-service pairs for the for_each loop.
  api_services_to_enable = { for pair in flatten([
    for p_id in local.all_gke_project_ids_for_api_enablement : [
      for s_name in local.gke_required_apis : {
        project = p_id
        service = s_name
      }
    ]
    ]) : "${pair.project}_${pair.service}" => pair
  }
}

# --- CIS Compliance Project Metadata ---
# Only uncomment if no organization policies enforce the below.
# resource "google_compute_project_metadata" "cis_compliance" {
#   project = var.main_project_id
#   metadata = {
#     enable-oslogin  = "TRUE" # CIS Compliance Benchmark 4.4
#     enable-osconfig = "TRUE" # CIS Compliance Benchmark 4.12
#   }
# }

# --- API Enablement ---
resource "google_project_service" "gke_core_api_enablement" {
  for_each           = local.api_services_to_enable
  project            = each.value.project
  service            = each.value.service
  disable_on_destroy = false
}

# --- Service Accounts and Identities ---
resource "google_service_account" "gke_cluster_sa" {
  project      = var.main_project_id
  account_id   = "gke-sa-${var.gke_cluster_name}"
  display_name = "GKE Cluster Service Account for ${var.gke_cluster_name}"
}

resource "google_project_service_identity" "container_engine_robot" {
  provider   = google-beta
  project    = var.main_project_id
  service    = "container.googleapis.com"
  depends_on = [google_project_service.gke_core_api_enablement]
}

data "google_project" "main" {
  project_id = var.main_project_id
}

# --- Data Sources for Existing Infrastructure ---
data "google_compute_network" "existing_network" {
  project    = var.landing_project_id
  name       = var.existing_network_name
  depends_on = [google_project_service.gke_core_api_enablement]
}

data "google_compute_subnetwork" "existing_subnetwork" {
  project    = var.landing_project_id
  name       = var.existing_subnetwork_name
  region     = var.gcp_region
  depends_on = [google_project_service.gke_core_api_enablement]
}

data "google_kms_key_ring" "existing_kms_keyring" {
  project    = var.core_project_id
  name       = var.existing_kms_keyring_name
  location   = var.gcp_region
  depends_on = [google_project_service.gke_core_api_enablement]
}

data "google_kms_crypto_key" "existing_kms_key" {
  name       = var.existing_kms_key_name
  key_ring   = data.google_kms_key_ring.existing_kms_keyring.id
  depends_on = [google_project_service.gke_core_api_enablement]
}

# --- IAM Bindings ---
resource "google_kms_crypto_key_iam_member" "gke_kms_access" {
  for_each = {
    custom_sa = "serviceAccount:${google_service_account.gke_cluster_sa.email}",
    gke_agent = "serviceAccount:${google_project_service_identity.container_engine_robot.email}"
  }
  crypto_key_id = data.google_kms_crypto_key.existing_kms_key.id
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = each.value
}

resource "google_kms_crypto_key_iam_member" "compute_agent_kms_access" {
  crypto_key_id = data.google_kms_crypto_key.existing_kms_key.id
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = "serviceAccount:service-${data.google_project.main.number}@compute-system.iam.gserviceaccount.com"
}

resource "google_project_iam_member" "gke_host_service_agent_user" {
  project = var.landing_project_id
  role    = "roles/container.hostServiceAgentUser"
  member  = "serviceAccount:${google_project_service_identity.container_engine_robot.email}"
}

resource "google_project_iam_member" "gke_compute_network_user" {
  project = var.landing_project_id
  role    = "roles/compute.networkUser"
  member  = "serviceAccount:${google_project_service_identity.container_engine_robot.email}"
}

resource "google_project_iam_member" "apis_service_agent_network_user" {
  project = var.landing_project_id
  role    = "roles/compute.networkUser"
  member  = "serviceAccount:${data.google_project.main.number}@cloudservices.gserviceaccount.com"
}

# --- Shared VPC Firewall Rule ---
resource "google_compute_firewall" "allow_gke_nodes_to_master" {
  project       = var.landing_project_id
  name          = "${var.gke_cluster_name}-nodes-to-master"
  network       = data.google_compute_network.existing_network.self_link
  direction     = "INGRESS"
  description   = "Allow GKE nodes to communicate with the GKE master control plane."
  source_ranges = [data.google_compute_subnetwork.existing_subnetwork.ip_cidr_range]
  allow {
    protocol = "tcp"
    ports    = ["10250", "443"]
  }
  allow {
    protocol = "udp"
    ports    = ["10250", "443"]
  }
  log_config {
    metadata = "INCLUDE_ALL_METADATA"
  }
}

# --- IAM Propagation Delay ---
resource "time_sleep" "iam_propagation_delay" {
  create_duration = local.iam_propagation_wait_duration
  depends_on = [
    google_kms_crypto_key_iam_member.gke_kms_access,
    google_kms_crypto_key_iam_member.compute_agent_kms_access,
    google_project_iam_member.gke_host_service_agent_user,
    google_project_iam_member.gke_compute_network_user,
    google_project_iam_member.apis_service_agent_network_user,
  ]
}

# --- GKE Cluster and Nodepool Creation ---
module "cluster" {
  source              = "../../../modules/gke-cluster-standard"
  project_id          = var.main_project_id
  name                = var.gke_cluster_name
  location            = var.gcp_region
  deletion_protection = var.enable_deletion_protection

  vpc_config = {
    network    = data.google_compute_network.existing_network.self_link
    subnetwork = data.google_compute_subnetwork.existing_subnetwork.self_link
    secondary_range_names = {
      pods     = var.existing_subnetwork_secondary_range_pods_name
      services = var.existing_subnetwork_secondary_range_services_name
    }
  }

  access_config = {
    private_nodes = var.gke_cluster_enable_private_endpoint
    ip_access = {
      disable_public_endpoint = var.gke_cluster_enable_private_endpoint
      authorized_ranges       = { for k, v in var.master_authorized_ranges : k => v }
      private_endpoint_config = {
        global_access = var.gke_cluster_master_global_access
      }
    }
  }

  default_nodepool = {
    remove_pool        = var.remove_default_node_pool
    initial_node_count = var.gke_initial_node_per_zone
  }

  node_config = {
    boot_disk_kms_key = data.google_kms_crypto_key.existing_kms_key.id
    service_account   = google_service_account.gke_cluster_sa.email
    tags              = var.node_config_tags
    metadata = {
      "block-project-ssh-keys" = "true" # CIS Compliance Benchmark 4.3 - Block project-wide SSH keys.
    }
  }

  enable_features = {
    shielded_nodes       = true
    dataplane_v2         = true
    binary_authorization = true
    database_encryption = {
      state    = "ENCRYPTED"
      key_name = data.google_kms_crypto_key.existing_kms_key.id
    }
  }

  depends_on = [
    time_sleep.iam_propagation_delay,
    google_compute_firewall.allow_gke_nodes_to_master,
  ]
}

module "cluster_nodepool" {
  source       = "../../../modules/gke-nodepool"
  project_id   = var.main_project_id
  cluster_name = module.cluster.name
  location     = var.gcp_region
  name         = var.gke_nodepool_name
  node_count   = var.nodepool_node_count

  service_account = {
    email = google_service_account.gke_cluster_sa.email
  }

  node_config = {
    boot_disk_kms_key = data.google_kms_crypto_key.existing_kms_key.id
    disk_size_gb      = var.node_disk_size_gb
    machine_type      = var.node_machine_type
    shielded_instance_config = {
      enable_secure_boot          = true
      enable_integrity_monitoring = true
    }
    metadata = {
      "block-project-ssh-keys" = "true"
    }
  }
}

# --- Bastion Host ---
module "bastion_vm" {
  source        = "../../../modules/compute-vm"
  project_id    = var.main_project_id
  name          = var.bastion_vm_name
  zone          = var.bastion_vm_zone
  instance_type = var.bastion_vm_machine_type
  service_account = {
    scopes = ["cloud-platform"]
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
    initialize_params = {
      image = var.bastion_vm_image
    }
  }
  network_interfaces = [{
    network    = data.google_compute_network.existing_network.self_link
    subnetwork = data.google_compute_subnetwork.existing_subnetwork.self_link
  }]
  encryption = {
    kms_key_self_link = data.google_kms_crypto_key.existing_kms_key.id
  }
}

