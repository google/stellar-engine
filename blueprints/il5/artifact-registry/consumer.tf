resource "google_service_account" "consumer" {
  account_id   = "compute-service-account"
  display_name = "Customized service account for consumer"
}

resource "google_project_iam_member" "consumer-readonly" {
  project = var.main_project_id
  role    = "roles/artifactregistry.reader"
  member  = google_service_account.consumer.member
}

resource "google_kms_crypto_key_iam_member" "consumer_sa_kms_access" {
  crypto_key_id = data.google_kms_crypto_key.default.id
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = google_service_account.consumer.member
}

resource "google_kms_crypto_key_iam_member" "compute_agent_kms_access" {
  crypto_key_id = data.google_kms_crypto_key.default.id
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = "serviceAccount:service-${data.google_project.project.number}@compute-system.iam.gserviceaccount.com"
}

data "google_compute_network" "network" {
  name    = var.vpc_network_name
  project = var.network_project_id
}

data "google_compute_subnetwork" "subnetwork" {
  name    = var.subnetwork_name
  region  = var.region
  project = var.network_project_id
}

data "google_compute_image" "centos" {
  family  = "centos-stream-9"
  project = "centos-cloud"
}

module "compute-engine-vm" {
  source     = "../../../modules/compute-vm"
  project_id = var.main_project_id
  zone       = "${var.region}-b"
  name       = "rpm-consumer"

  instance_type        = "n2d-standard-2"
  confidential_compute = true # CIS Compliance Benchmark 4.11 - Must use compliant instance type

  network_interfaces = [{
    network    = data.google_compute_network.network.id
    subnetwork = data.google_compute_subnetwork.subnetwork.self_link
  }]
  encryption = {
    kms_key_self_link = data.google_kms_crypto_key.default.id
  }
  metadata = {
    startup-script = templatefile("./templates/userdata.tftpl",
      {
        project          = var.main_project_id
        region           = var.region
        yum_repositories = google_artifact_registry_repository.yum-repos
      },
    )
    block-project-ssh-keys = true # CIS Compliance Benchmark 4.3
  }

  # CIS Compliance Benchmark 4.1/4.2
  service_account = {
    email = google_service_account.consumer.email
  }

  boot_disk = {
    initialize_params = {
      auto_delete       = true
      size              = 20
      type              = "pd-balanced"
      image             = data.google_compute_image.centos.self_link
      kms_key_self_link = data.google_kms_crypto_key.default.id
    }
  }
}