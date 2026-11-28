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

locals {
  # Registry hosts that need the gcloud Docker credential helper.
  _docker_registry_hosts = sort(distinct([
    for image in concat(
      [var.docker_image],
      local.allowed_docker_images,
      var.allowed_docker_services,
    ) : split("/", lower(image))[0]
  ]))
  _iap_ssh_rule_name = "${var.instance_name}-allow-iap-ssh"
  _runner_dropin = chomp(templatefile(
    "${local._templates}/runner-dropin.conf.tpl",
    {
      executor          = var.executor
      stop_timeout_secs = local.runner_stop_timeout_secs
    }
  ))
  _snapshot_schedules = var.enable_boot_disk_snapshots ? {
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
      snapshot_properties = {
        storage_locations = [var.region]
      }
    }
  } : {}
  _startup_template = "${local._templates}/startup.sh.tpl"
  _templates        = "${path.module}/templates"
  allowed_docker_images = (
    var.allowed_docker_images == null
    ? [var.docker_image]
    : var.allowed_docker_images
  )
  artifact_registry_readers = {
    for repo in var.artifact_registry_repositories :
    "${repo.project_id}/${repo.location}/${repo.repository}" => repo
  }
  compute_service_agent = format(
    "serviceAccount:service-%s@compute-system.iam.gserviceaccount.com",
    data.google_project.current.number
  )
  # Hash of every input that shapes the runner registration, including the
  # startup template itself. The startup script stores it after registering
  # and re-registers on the next boot when it differs.
  registration_fingerprint = sha256(jsonencode({
    allowed_docker_images   = local.allowed_docker_images
    allowed_docker_services = var.allowed_docker_services
    docker_cap_add          = var.docker_cap_add
    docker_image            = var.docker_image
    executor                = var.executor
    gitlab_url              = var.gitlab_url
    region                  = var.region
    runner_name             = var.instance_name
    secret_id               = var.runner_token_secret_id
    secret_project_id       = local.runner_token_secret_project_id
    secret_version          = var.runner_token_secret_version
    secret_wo_version       = local.runner_token_wo_version
    startup_template        = filesha256(local._startup_template)
  }))
  required_apis = toset([
    "compute.googleapis.com",
    "logging.googleapis.com",
    "monitoring.googleapis.com",
    "secretmanager.googleapis.com",
  ])
  # Unwrap only the structural presence, file path, and version counter so
  # modules/secret-manager for_each keys stay non-sensitive while value stays
  # sensitive.
  runner_secret_versions = (
    nonsensitive(var.runner_token_secret_wo == null) ? {} : {
      runner = {
        data = {
          path       = nonsensitive(var.runner_token_secret_wo.path)
          value      = var.runner_token_secret_wo.value
          wo_version = nonsensitive(var.runner_token_secret_wo.wo_version)
        }
      }
    }
  )
  # SIGQUIT drain budget: the graceful shutdown period plus 90 of the 120
  # seconds Compute Engine gives the guest OS, which leaves 30 seconds for
  # unregister and the rest of the OS shutdown.
  runner_stop_timeout_secs = coalesce(var.graceful_shutdown_secs, 0) + 90
  runner_token_secret_project_id = coalesce(
    var.runner_token_secret_project_id,
    var.project_id
  )
  runner_token_wo_version = try(
    nonsensitive(var.runner_token_secret_wo.wo_version), null
  )
  secretmanager_service_agent = format(
    "serviceAccount:service-%s@gcp-sa-secretmanager.iam.gserviceaccount.com",
    data.google_project.current.number
  )
  shutdown_script = file("${local._templates}/shutdown.sh")
  startup_script = templatefile(local._startup_template, {
    allowed_images    = local.allowed_docker_images
    allowed_services  = var.allowed_docker_services
    cap_add           = var.docker_cap_add
    docker_image      = var.docker_image
    executor          = var.executor
    fingerprint       = local.registration_fingerprint
    gitlab_url        = var.gitlab_url
    graceful_shutdown = var.graceful_shutdown_secs != null
    guard_script      = chomp(file("${local._templates}/metadata-guard.sh"))
    guard_unit = chomp(
      file("${local._templates}/metadata-guard.service")
    )
    region            = var.region
    registry_hosts    = join(",", local._docker_registry_hosts)
    runner_dropin     = local._runner_dropin
    runner_name       = var.instance_name
    secret_id         = var.runner_token_secret_id
    secret_project_id = local.runner_token_secret_project_id
    secret_version    = var.runner_token_secret_version
    watcher_script = chomp(
      file("${local._templates}/shutdown-watcher.sh")
    )
    watcher_unit = chomp(
      file("${local._templates}/shutdown-watcher.service")
    )
  })
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

resource "google_project_service_identity" "secretmanager" {
  provider   = google-beta
  count      = var.create_runner_token_secret ? 1 : 0
  project    = var.project_id
  service    = "secretmanager.googleapis.com"
  depends_on = [google_project_service.apis]
}

# Wait 60s after enabling APIs and creating the Secret Manager service
# identity so IAM recognizes new service agents on fresh projects.
resource "time_sleep" "service_agent_propagation" {
  create_duration = "60s"
  depends_on = [
    google_project_service.apis,
    google_project_service_identity.secretmanager,
  ]
}

data "google_compute_network" "network" {
  name    = var.network_name
  project = var.network_project_id
}

data "google_compute_subnetwork" "subnetwork" {
  name    = var.subnetwork_name
  region  = var.region
  project = var.network_project_id
}

# Dedicated least-privilege service account so the runner never uses the
# default Compute Engine service account.
module "runner-sa" {
  source       = "../../../modules/iam-service-account"
  project_id   = var.project_id
  name         = var.service_account_id
  display_name = "GitLab Runner service account."
  description  = "Least-privilege identity for the hardened GitLab Runner VM."
  iam_project_roles = {
    (var.project_id) = [
      "roles/logging.logWriter",
      "roles/monitoring.metricWriter",
    ]
  }
  depends_on = [google_project_service.apis]
}

# Repository-scoped Artifact Registry read access for the default, job, and
# service images instead of a project-wide reader grant.
resource "google_artifact_registry_repository_iam_member" "runner_reader" {
  for_each   = local.artifact_registry_readers
  project    = each.value.project_id
  location   = each.value.location
  repository = each.value.repository
  role       = "roles/artifactregistry.reader"
  member     = module.runner-sa.iam_email
}

resource "google_kms_crypto_key_iam_member" "compute_cmek" {
  count         = var.manage_kms_iam ? 1 : 0
  crypto_key_id = var.kms_key_id
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = local.compute_service_agent
  depends_on    = [time_sleep.service_agent_propagation]
}

resource "google_kms_crypto_key_iam_member" "secretmanager_cmek" {
  count         = var.create_runner_token_secret && var.manage_kms_iam ? 1 : 0
  crypto_key_id = var.kms_key_id
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = local.secretmanager_service_agent
  depends_on = [
    google_project_service_identity.secretmanager,
    time_sleep.service_agent_propagation,
  ]
}

# Optional CMEK-encrypted regional secret managed via modules/secret-manager
# with write-only versions so runner tokens never persist in Terraform state.
module "runner-token-secret" {
  source     = "../../../modules/secret-manager"
  count      = var.create_runner_token_secret ? 1 : 0
  project_id = var.project_id
  secrets = {
    (var.runner_token_secret_id) = {
      location = var.region
      kms_key  = var.kms_key_id
      iam_bindings_additive = {
        runner_accessor = {
          member = module.runner-sa.iam_email
          role   = "roles/secretmanager.secretAccessor"
        }
      }
      versions = local.runner_secret_versions
    }
  }
  depends_on = [
    google_kms_crypto_key_iam_member.secretmanager_cmek,
    time_sleep.service_agent_propagation,
  ]
}

# Secret-scoped regional accessor binding when referencing an existing
# regional Secret Manager secret instead of creating one in this blueprint.
resource "google_secret_manager_regional_secret_iam_member" "runner_token" {
  count      = var.create_runner_token_secret ? 0 : 1
  project    = local.runner_token_secret_project_id
  location   = var.region
  secret_id  = var.runner_token_secret_id
  role       = "roles/secretmanager.secretAccessor"
  member     = module.runner-sa.iam_email
  depends_on = [google_project_service.apis]
}

module "runner-vm" {
  source               = "../../../modules/compute-vm"
  project_id           = var.project_id
  zone                 = var.zone
  name                 = var.instance_name
  machine_type         = var.machine_type
  confidential_compute = "SEV"
  labels               = var.labels
  boot_disk = {
    snapshot_schedule = (
      var.enable_boot_disk_snapshots ? ["daily-backup"] : null
    )
    initialize_params = {
      size = var.boot_disk_size_gb
      type = var.boot_disk_type
    }
    source = {
      image = var.golden_image
    }
  }
  encryption = {
    encrypt_boot      = true
    kms_key_self_link = var.kms_key_id
  }
  # Optional graceful shutdown period; the startup script installs a
  # watcher that drains the runner when the VM enters PENDING_STOP.
  lifecycle_config = {
    graceful_shutdown = var.graceful_shutdown_secs == null ? null : {
      enabled           = true
      max_duration_secs = var.graceful_shutdown_secs
    }
  }
  metadata = {
    block-project-ssh-keys = "TRUE"
    enable-oslogin         = "TRUE"
    serial-port-enable     = "false"
    shutdown-script        = local.shutdown_script
    startup-script         = local.startup_script
  }
  network_interfaces = [{
    network    = data.google_compute_network.network.self_link
    subnetwork = data.google_compute_subnetwork.subnetwork.self_link
    nat        = false
  }]
  service_account = {
    email = module.runner-sa.email
  }
  shielded_config = {
    enable_secure_boot          = true
    enable_vtpm                 = true
    enable_integrity_monitoring = true
  }
  snapshot_schedules = local._snapshot_schedules
  # Ensure IAM, KMS, and Secret Manager bindings exist before first boot so
  # startup registration succeeds without transient permission errors.
  depends_on = [
    module.runner-sa,
    module.runner-token-secret,
    google_artifact_registry_repository_iam_member.runner_reader,
    google_kms_crypto_key_iam_member.compute_cmek,
    google_secret_manager_regional_secret_iam_member.runner_token,
    time_sleep.service_agent_propagation,
  ]
}

# Opt-in IAP TCP SSH ingress rule managed through modules/net-vpc-firewall,
# scoped strictly to the runner service account with full metadata logging.
module "iap-ssh-firewall" {
  source     = "../../../modules/net-vpc-firewall"
  count      = var.enable_iap_ssh ? 1 : 0
  project_id = var.network_project_id
  network    = data.google_compute_network.network.self_link
  default_rules_config = {
    disabled = true
  }
  ingress_rules = {
    (local._iap_ssh_rule_name) = {
      description          = "Allow IAP TCP SSH to the GitLab Runner SA."
      source_ranges        = ["35.235.240.0/20"]
      targets              = [module.runner-sa.email]
      use_service_accounts = true
      enable_logging = {
        include_metadata = true
      }
      rules = [{
        protocol = "tcp"
        ports    = ["22"]
      }]
    }
  }
}

# Opt-in Shared VPC Cloud NAT deployed in network_project_id and scoped to
# the runner subnetwork primary range with full NAT logging enabled.
module "cloud-nat" {
  source         = "../../../modules/net-cloudnat"
  count          = var.enable_cloud_nat ? 1 : 0
  project_id     = var.network_project_id
  region         = var.region
  name           = "${var.instance_name}-nat"
  router_name    = "${var.instance_name}-router"
  router_network = data.google_compute_network.network.self_link
  logging_filter = "ALL"
  config_source_subnetworks = {
    all = false
    subnetworks = [
      {
        self_link     = data.google_compute_subnetwork.subnetwork.self_link
        all_ranges    = false
        primary_range = true
      }
    ]
  }
}
