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

data "google_project" "project" {}

data "google_storage_project_service_account" "gcs_account" {
}

resource "google_service_account" "gitlab-sa" {
  account_id   = var.sa
  display_name = "gitlab-sa"
}

resource "google_project_iam_member" "gke_cluster_admin" {
  count   = var.existing_cluster ? 0 : 1
  project = data.google_project.project.project_id
  role    = "roles/container.admin"
  member  = "serviceAccount:${google_service_account.gitlab-sa.email}"
}

resource "google_project_service" "storagetransfer_api" {
  project = var.project_id
  service = "storagetransfer.googleapis.com"
}

# Grant GKE Host Service Agent User Role
resource "google_project_iam_member" "gke_host_agent_use" {
  count   = var.existing_cluster ? 0 : 1
  project = var.net_project # Project where the GKE cluster is being created
  role    = "roles/container.hostServiceAgentUser"
  member  = "serviceAccount:service-${data.google_project.project.number}@container-engine-robot.iam.gserviceaccount.com" # Use project where the GKE cluster is being created
}

resource "google_project_iam_binding" "compute_agent_subnet_user" {
  count   = var.existing_cluster ? 0 : 1
  project = var.net_project
  role    = "roles/compute.networkUser"
  members = [
    "serviceAccount:service-${data.google_project.project.number}@compute-system.iam.gserviceaccount.com",
    "serviceAccount:service-${data.google_project.project.number}@container-engine-robot.iam.gserviceaccount.com",
    "serviceAccount:${data.google_project.project.number}@cloudservices.gserviceaccount.com",
    "serviceAccount:${google_service_account.gitlab-sa.email}"
  ]
}

resource "google_kms_crypto_key_iam_binding" "compute_service_agent_kms_permissions" {
  crypto_key_id = var.kms_key
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  members = [
    "serviceAccount:service-${data.google_project.project.number}@compute-system.iam.gserviceaccount.com",
    "serviceAccount:service-${data.google_project.project.number}@container-engine-robot.iam.gserviceaccount.com",
    "serviceAccount:${data.google_project.project.number}@cloudservices.gserviceaccount.com",
    "serviceAccount:${google_service_account.gitlab-sa.email}",
    "serviceAccount:${data.google_storage_project_service_account.gcs_account.email_address}"
  ]
}

module "net-firewall" {
  count      = var.existing_cluster ? 0 : 1
  source     = "../../../modules/net-vpc-firewall"
  project_id = var.net_project
  network    = var.network_name
  ingress_rules = {
    gitlab-allow = {
      description   = "Allow health checks to GitLab load balancer."
      source_ranges = var.gitlab_allow_source_ranges
      targets       = ["gitlab"]
      rules         = [{ protocol = "tcp", ports = [80, 443] }]
    }
  }
}

module "cluster" {
  count      = var.existing_cluster ? 0 : 1
  source     = "../../../modules/gke-cluster-standard"
  project_id = var.project_id
  location   = var.region
  name       = var.gke_name
  vpc_config = {
    network    = var.network
    subnetwork = var.subnetwork
    secondary_range_names = {
      pods     = var.subnet_pod_range
      services = var.subnet_service_range
    }
  }
  default_nodepool = {
    remove_pool              = true
    remove_default_node_pool = true
  }
  node_config = {
    boot_disk_kms_key = var.kms_key

    machine_type = "n2d-standard-2"
    confidential_nodes = {
      enabled = true
    }
  }
  access_config = {
    private_nodes = true
    ip_access = {
      private_endpoint_config = {
        global_access = false
      }
    }
  }
  deletion_protection = false
  depends_on          = [google_kms_crypto_key_iam_binding.compute_service_agent_kms_permissions, google_project_iam_binding.compute_agent_subnet_user, google_project_iam_member.gke_host_agent_use, google_project_iam_member.gke_cluster_admin]
}

module "gke_node_pool" {
  count        = var.existing_cluster ? 0 : 1
  source       = "../../../modules/gke-nodepool"
  project_id   = var.project_id
  location     = var.region
  cluster_name = var.gke_name
  service_account = {
    email = google_service_account.gitlab-sa.email
  }
  name       = "nodes"
  node_count = var.nodepool_node_count

  nodepool_config = {
    autoscaling = {
      min_node_count = 1
      max_node_count = 5
    }
  }

  node_config = {
    boot_disk_kms_key = var.kms_key
    disk_size_gb      = 20
    machine_type      = "n2d-standard-2"
    shielded_instance_config = {
      enable_secure_boot          = true
      enable_integrity_monitoring = true
    }
  }
  depends_on = [module.cluster]
}

module "config-bucket" {
  source         = "../../../modules/gcs"
  project_id     = var.project_id
  name           = "${var.project_id}-${var.bucket_name}"
  location       = var.region
  encryption_key = var.kms_key
  iam = {
    "roles/storage.objectViewer" = ["serviceAccount:${google_service_account.gitlab-sa.email}"]
  }
  objects_to_upload = {
    omniauth_secret = {
      name         = "omniauth_secret.yaml"
      source       = "scripts/omniauth_secret.yaml"
      content_type = "text/yaml"
    }
    generate_certs = {
      name         = "generate_certs.sh"
      source       = "scripts/generate_certs.sh"
      content_type = "application/x-sh"
    }
  }
  depends_on = [google_kms_crypto_key_iam_binding.compute_service_agent_kms_permissions, google_service_account.gitlab-sa]
}
