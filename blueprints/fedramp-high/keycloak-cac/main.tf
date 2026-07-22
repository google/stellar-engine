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
    lb = {
      name         = "lb.yaml"
      source       = "keycloak-config/lb.yaml"
      content_type = "text/yaml"
    }
    keycloak = {
      name         = "keycloak.yaml"
      source       = "keycloak-config/keycloak.yaml"
      content_type = "text/yaml"
    }
    namespace = {
      name         = "namespace.yaml"
      source       = "keycloak-config/namespace.yaml"
      content_type = "text/yaml"
    }
    dod_chain = {
      name         = "dod_chain.pem"
      source       = "keycloak-config/dod_chain.pem"
      content_type = "text"
    }
    configure_kc = {
      name         = "configure_keycloak.sh"
      source       = "keycloak-config/configure_keycloak.sh"
      content_type = "application/x-sh"
    }
    config_env_sample = {
      name         = "config.env.sample"
      source       = "keycloak-config/config.env.sample"
      content_type = "text"
    }
  }
  depends_on = [google_kms_crypto_key_iam_binding.kms-key-permissions]
}

resource "google_storage_bucket_object" "deploy_script" {
  name   = "deploy.sh"
  bucket = module.config-bucket.name

  content = <<-EOT
    #!/bin/bash
    set -euo pipefail

    echo "--- 1. Configuring Environment ---"
    # Cloud Shell already has kubectl, gcloud, and plugins installed.
    # We just need to set the project and get credentials.
    
    PROJECT_ID="${var.project_id}"
    REGION="${var.region}"
    CLUSTER_NAME="${module.gke-cluster.name}"
    BUCKET_NAME="${module.config-bucket.name}"
    HOST_NAME="keycloak.${var.domain}"

    gcloud config set project "$PROJECT_ID"

    echo "--- 2. Authenticating to GKE ---"
    gcloud container clusters get-credentials "$CLUSTER_NAME" \
        --region "$REGION" \
        --project "$PROJECT_ID" \
        --dns-endpoint

    echo "--- 3. Downloading Configs from Bucket ---"
    # Create a clean temp directory
    WORK_DIR=$(mktemp -d)
    cd "$WORK_DIR"
    
    echo "Working in $WORK_DIR"
    
    # Download the files Terraform uploaded previously
    gcloud storage cp "gs://$BUCKET_NAME/namespace.yaml" .
    gcloud storage cp "gs://$BUCKET_NAME/keycloak.yaml" .
    gcloud storage cp "gs://$BUCKET_NAME/lb.yaml" .
    gcloud storage cp "gs://$BUCKET_NAME/dod_chain.pem" .

    echo "--- 4. Generating Internal TLS Certificates ---"
    openssl req -x509 -newkey rsa:2048 -nodes -keyout tls.key -out tls.crt -days 365 -subj "/CN=$HOST_NAME" -addext "subjectAltName=DNS:$HOST_NAME"
    
    echo "--- 5. Updating URL for Kubernetes in yaml file ---"
    sed -i "s|__KC_HOSTNAME__|$HOST_NAME|g" keycloak.yaml
    
    echo "--- 6. Applying Kubernetes Manifests ---"
    
    # Create the Secret (Dry run ensures idempotency)
    kubectl -n default create secret generic keycloak-truststores \
      --from-file=dod_chain.pem \
      --dry-run=client -o yaml | kubectl apply -f -
    
    # Create TLS Secret
    kubectl -n default create secret tls keycloak-tls \
      --cert=tls.crt \
      --key=tls.key \
      --dry-run=client -o yaml | kubectl apply -f -

    # Apply Cert Manager CRDs (Idempotent)
    kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.18.2/cert-manager.crds.yaml

    # Apply Application Manifests
    kubectl apply -f ./namespace.yaml
    kubectl apply -f ./keycloak.yaml
    kubectl apply -f ./lb.yaml

    echo "Deployment Complete!"
  EOT
}
