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

resource "google_project_service" "storagetransfer-api" {
  project            = var.project_id
  service            = "storagetransfer.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "cert_manager" {
  project            = var.project_id
  service            = "certificatemanager.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "container-api" {
  project            = var.project_id
  service            = "container.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "sql-api" {
  project            = var.project_id
  service            = "sqladmin.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "cloud-storage-api" {
  project            = var.project_id
  service            = "storage.googleapis.com"
  disable_on_destroy = false
}

resource "google_service_account" "keycloak-service-account" {
  account_id   = "keycloak-service-account"
  display_name = "keycloak-service-account"
  project      = var.project_id
}

resource "google_project_iam_member" "cm_editor" {
  project = var.project_id
  role    = "roles/certificatemanager.editor"
  member  = "serviceAccount:${google_service_account.keycloak-service-account.email}"
}

resource "google_project_iam_binding" "network-user" {
  project = var.network_project_id
  role    = "roles/compute.networkUser"
  members = [
    "serviceAccount:${google_service_account.keycloak-service-account.email}",
    "serviceAccount:${data.google_project.project.number}@cloudservices.gserviceaccount.com"
  ]
  depends_on = [google_service_account.keycloak-service-account]
}

resource "google_project_iam_member" "gke_host_agent_use" {
  project = var.network_project_id
  role    = "roles/container.hostServiceAgentUser"
  member  = "serviceAccount:service-${data.google_project.project.number}@container-engine-robot.iam.gserviceaccount.com"
}

resource "google_project_iam_member" "gke_admin" {
  project    = var.project_id
  role       = "roles/container.admin"
  member     = "serviceAccount:${google_service_account.keycloak-service-account.email}"
  depends_on = [google_service_account.keycloak-service-account]
}

resource "google_kms_crypto_key_iam_binding" "kms-key-permissions" {
  crypto_key_id = var.kms_key
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  members = [
    "serviceAccount:${google_service_account.keycloak-service-account.email}",
    "serviceAccount:service-${data.google_project.project.number}@gs-project-accounts.iam.gserviceaccount.com",
    "serviceAccount:service-${data.google_project.project.number}@container-engine-robot.iam.gserviceaccount.com",
    "serviceAccount:${data.google_project.project.number}-compute@developer.gserviceaccount.com",
    "serviceAccount:${data.google_project.project.number}@cloudservices.gserviceaccount.com",
    "serviceAccount:service-${data.google_project.project.number}@compute-system.iam.gserviceaccount.com"
  ]
  depends_on = [google_service_account.keycloak-service-account]
}

resource "google_project_iam_member" "storage-viewer" {
  project    = var.project_id
  role       = "roles/storage.objectViewer"
  member     = "serviceAccount:${google_service_account.keycloak-service-account.email}"
  depends_on = [google_service_account.keycloak-service-account]
}

resource "google_certificate_manager_dns_authorization" "keycloak-dns-auth" {
  project = var.project_id
  name    = "keycloak-dns-auth"
  domain  = var.domain
}

resource "google_certificate_manager_certificate" "keycloak-cert" {
  project = var.project_id
  name    = "keycloak-cert"
  scope   = "DEFAULT"
  managed {
    domains            = [var.domain]
    dns_authorizations = [google_certificate_manager_dns_authorization.keycloak-dns-auth.id]
  }
  depends_on = [google_certificate_manager_dns_authorization.keycloak-dns-auth]
}

resource "google_certificate_manager_certificate_map" "keycloak-map" {
  project = var.project_id
  name    = "keycloak-cert-map"
}

resource "google_certificate_manager_certificate_map_entry" "keycloak-entry" {
  project      = var.project_id
  name         = "keycloak-entry"
  map          = google_certificate_manager_certificate_map.keycloak-map.name
  hostname     = var.domain
  certificates = [google_certificate_manager_certificate.keycloak-cert.id]
}

module "bastion-vm" {
  source     = "../../../modules/compute-vm"
  name       = "keycloak-bastion-vm"
  project_id = var.project_id
  zone       = var.zone
  service_account = {
    email  = google_service_account.keycloak-service-account.email
    scopes = ["https://www.googleapis.com/auth/cloud-platform"]
  }
  network_interfaces = [{
    network    = var.network
    subnetwork = var.subnetwork
  }]
  instance_type = "n1-standard-8"
  boot_disk = {
    initialize_params = {
      image = "projects/ubuntu-os-cloud/global/images/ubuntu-minimal-2504-plucky-amd64-v20250828"
      size  = 20
    }
  }
  encryption = {
    kms_key_self_link = var.kms_key
  }
  metadata = {
    startup-script = <<-EOF
    #!/bin/bash
set -euo pipefail
exec > >(tee -a /var/log/startup-script.log /dev/ttyS0) 2>&1
export DEBIAN_FRONTEND=noninteractive

export HOME=/root
export CLOUDSDK_CONFIG=/root/.config/gcloud
export KUBECONFIG=/root/.kube/config
export USE_GKE_GCLOUD_AUTH_PLUGIN=True
mkdir -p "$CLOUDSDK_CONFIG" "$(dirname "$KUBECONFIG")"
chmod 700 /root/.kube

apt-get update -y
apt-get -y upgrade
apt-get install -y curl gnupg openssh-server ca-certificates tzdata perl \
  -o Dpkg::Options::=--force-confdef -o Dpkg::Options::=--force-confold
apt-get install -y postfix -o Dpkg::Options::=--force-confdef -o Dpkg::Options::=--force-confold || true

install -d -m 0755 /usr/share/keyrings
curl -fsSL https://packages.cloud.google.com/apt/doc/apt-key.gpg \
  | gpg --dearmor --batch --yes --no-tty --output /usr/share/keyrings/cloud.google.gpg

echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" \
  > /etc/apt/sources.list.d/google-cloud-sdk.list

apt-get update -y
apt-get install -y google-cloud-cli kubectl google-cloud-cli-gke-gcloud-auth-plugin

for i in {1..30}; do
  if gcloud container clusters get-credentials "${module.gke-cluster.name}" \
      --region "${var.region}" --project "${var.project_id}" --dns-endpoint; then
    break
  fi
  echo "Waiting for cluster API (attempt $i/30)…"
  sleep 10
done

gcloud storage cp "gs://${module.config-bucket.name}/keycloak.yaml" ./
gcloud storage cp "gs://${module.config-bucket.name}/gateway.yaml" ./
gcloud storage cp "gs://${module.config-bucket.name}/gateway-healthcheck.yaml" ./
gcloud storage cp "gs://${module.config-bucket.name}/http-route.yaml" ./

kubectl apply -f ./keycloak.yaml
kubectl apply -f ./gateway.yaml
kubectl apply -f ./gateway-healthcheck.yaml
kubectl apply -f ./http-route.yaml

echo "Startup script complete."
    EOF
  }
  depends_on = [module.database, module.config-bucket, google_project_iam_member.cm_editor, google_certificate_manager_certificate_map_entry.keycloak-entry]
}

module "gke-cluster" {
  source     = "../../../modules/gke-cluster-standard"
  project_id = var.project_id
  name       = "keycloak-cluster"
  location   = var.region
  vpc_config = {
    network    = var.network
    subnetwork = var.subnetwork
    secondary_range_names = {
      pods     = var.pod_range
      services = var.service_range
    }
  }
  enable_features = {
    gateway_api              = true
    vertical_pod_autoscaling = true
  }
  default_nodepool = {
    remove_pool        = false
    initial_node_count = var.node_count
  }
  cluster_autoscaling = {
    enabled             = true
    autoscaling_profile = "BALANCED"

    auto_provisioning_defaults = {
      image_type        = "COS_CONTAINERD"
      service_account   = google_service_account.keycloak-service-account.email
      boot_disk_kms_key = var.kms_key
      disk_type         = "pd-balanced"
      disk_size         = 50
      management = {
        auto_repair  = true
        auto_upgrade = true
      }
      shielded_instance_config = {
        integrity_monitoring = true
        secure_boot          = true
      }
    }
    cpu_limits = { min = 0, max = 32 }
    mem_limits = { min = 0, max = 128 }
  }
  node_config = {
    service_account   = google_service_account.keycloak-service-account.email
    boot_disk_kms_key = var.kms_key
    machine_type      = "n2d-standard-4"
    image_type        = "COS_CONTAINERD"
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
  depends_on = [google_project_iam_binding.network-user, google_project_iam_member.gke_host_agent_use]
}

module "config-bucket" {
  source         = "../../../modules/gcs"
  project_id     = var.project_id
  name           = var.bucket-name
  location       = var.region
  encryption_key = var.kms_key
  iam = {
    "roles/storage.objectViewer" = ["serviceAccount:${google_service_account.keycloak-service-account.email}"]
  }
  objects_to_upload = {
    gateway-healthcheck = {
      name         = "gateway-healthcheck.yaml"
      source       = "keycloak-config/gateway-healthcheck.yaml"
      content_type = "text/yaml"
    }
    gateway = {
      name         = "gateway.yaml"
      source       = "keycloak-config/gateway.yaml"
      content_type = "text/yaml"
    }
    http-route = {
      name         = "http-route.yaml"
      content      = templatefile("keycloak-config/http-route.yaml", { domain = var.domain })
      content_type = "text/yaml"
    }
    keycloak = {
      name         = "keycloak.yaml"
      source       = "keycloak-config/keycloak.yaml"
      content_type = "text/yaml"
    }
  }
  depends_on = [google_kms_crypto_key_iam_binding.kms-key-permissions]
}

module "database" {
  source           = "../../../modules/cloudsql-instance"
  project_id       = var.project_id
  region           = var.region
  name             = "keycloak-db-1"
  tier             = "db-g1-small"
  database_version = "POSTGRES_17"
  network_config = {
    connectivity = {
      psa_config = {
        private_network = var.network
      }
    }
  }
  root_password = {
    random_password = true
  }
  users = {
    (google_service_account.keycloak-service-account.email) = {
      type = "CLOUD_IAM_SERVICE_ACCOUNT"
    }
  }
  depends_on = [module.gke-cluster]
}
