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

data "google_project" "current" {
  project_id = var.project_id
}

data "google_project" "peered_network_host" {
  count      = local._peered_network_project_is_number ? 0 : 1
  project_id = local._peered_network_parts[0]
}

# Resolve the VPC network that actually owns builder_subnetwork so the SSH
# firewall rule and the peering alignment check never trust peered_network.
data "google_compute_subnetwork" "builder" {
  project = local.subnetwork_host_project
  region  = local.subnetwork_region
  name    = local.subnetwork_name
}

data "google_project" "builder_subnetwork_host" {
  count      = var.allow_builder_network_mismatch ? 0 : 1
  project_id = local.subnetwork_host_project
}

locals {
  _peered_network_parts = regex(
    "^projects/([^/]+)/global/networks/([^/]+)$",
    var.peered_network,
  )
  _peered_network_project_is_number = can(
    regex("^[0-9]+$", local._peered_network_parts[0])
  )
  _prefix = var.prefix == null ? "" : "${var.prefix}-"
  _subnetwork_parts = regex(
    "^projects/([^/]+)/regions/([^/]+)/subnetworks/([^/]+)$",
    var.builder_subnetwork,
  )
  _cloudbuild_parsed = yamldecode(local.cloudbuild_config)
  _cloudbuild_steps  = local._cloudbuild_parsed.steps
  _trigger_is_pubsub = (
    var.trigger_config != null && var.trigger_config.pubsub_topic != null
  )
  _trigger_is_repo = (
    var.trigger_config != null && var.trigger_config.repository_event != null
  )
  _trigger_substitutions = var.trigger_config == null ? {} : merge(
    local.default_substitutions,
    var.trigger_config.substitutions,
  )

  builder_network_name = reverse(
    split("/", data.google_compute_subnetwork.builder.network)
  )[0]
  # Same projects/<number>/global/networks/<name> shape as
  # peered_network_normalized, or null when the check is disabled.
  builder_network_normalized = (
    var.allow_builder_network_mismatch ? null : format(
      "projects/%s/global/networks/%s",
      data.google_project.builder_subnetwork_host[0].number,
      local.builder_network_name,
    )
  )
  builder_project_roles = [
    "roles/compute.instanceAdmin.v1",
    "roles/compute.osAdminLogin",
    "roles/compute.storageAdmin",
    "roles/logging.logWriter",
  ]
  cloudbuild_agent_iam = format(
    "serviceAccount:service-%s@gcp-sa-cloudbuild.iam.gserviceaccount.com",
    data.google_project.current.number,
  )
  cloudbuild_config = templatefile(
    "${path.module}/templates/cloudbuild-rhel9-stig.yaml.tpl",
    {
      base_image                        = var.base_image
      build_timeout                     = var.build_timeout
      builder_confidential_compute_type = var.builder_confidential_compute_type
      builder_image_digest              = var.builder_image_digest
      builder_machine_type              = var.builder_machine_type
      builder_sa_email                  = module.builder-sa.email
      builder_subnetwork                = var.builder_subnetwork
      builder_zone                      = var.builder_zone
      guest_os_features                 = join(",", var.guest_os_features)
      image_family                      = var.image_family
      image_name_prefix                 = var.image_name_prefix
      kms_key_id                        = var.kms_key_id
      project_id                        = var.project_id
      region                            = var.region
      worker_pool_id                    = local.worker_pool_id
    },
  )
  default_substitutions = {
    _BASE_IMAGE           = var.base_image
    _BUILDER_MACHINE_TYPE = var.builder_machine_type
    _GUEST_OS_FEATURES    = join(",", var.guest_os_features)
    _IMAGE_FAMILY         = var.image_family
    _IMAGE_NAME_PREFIX    = var.image_name_prefix
    _KMS_KEY              = var.kms_key_id
    _PROJECT_ID           = var.project_id
    _REGION               = var.region
    _SUBNETWORK           = var.builder_subnetwork
    _ZONE                 = var.builder_zone
  }
  kms_service_agents = var.grant_service_agent_kms_iam ? {
    artifact_registry = format(
      "serviceAccount:service-%s@%s",
      data.google_project.current.number,
      "gcp-sa-artifactregistry.iam.gserviceaccount.com",
    )
    compute_engine = format(
      "serviceAccount:service-%s@%s",
      data.google_project.current.number,
      "compute-system.iam.gserviceaccount.com",
    )
    storage = format(
      "serviceAccount:service-%s@%s",
      data.google_project.current.number,
      "gs-project-accounts.iam.gserviceaccount.com",
    )
  } : {}
  peered_network_normalized = format(
    "projects/%s/global/networks/%s",
    (
      local._peered_network_project_is_number
      ? local._peered_network_parts[0]
      : data.google_project.peered_network_host[0].number
    ),
    local._peered_network_parts[1],
  )
  required_apis = toset([
    "artifactregistry.googleapis.com",
    "cloudbuild.googleapis.com",
    "compute.googleapis.com",
    "containerscanning.googleapis.com",
    "oslogin.googleapis.com",
    "storage.googleapis.com",
  ])
  staging_bucket_builder_role = "roles/storage.objectViewer"
  subnetwork_host_project     = local._subnetwork_parts[0]
  subnetwork_name             = local._subnetwork_parts[2]
  subnetwork_region           = local._subnetwork_parts[1]
  worker_pool_id = format(
    "projects/%s/locations/%s/workerPools/%s",
    var.project_id,
    var.region,
    local.worker_pool_name,
  )
  worker_pool_name = "${local._prefix}${var.worker_pool_name}"
}

resource "google_project_service" "apis" {
  for_each           = var.enable_apis ? local.required_apis : toset([])
  project            = var.project_id
  service            = each.value
  disable_on_destroy = false
}

resource "google_project_service_identity" "artifact_registry_sa" {
  provider   = google-beta
  project    = var.project_id
  service    = "artifactregistry.googleapis.com"
  depends_on = [google_project_service.apis]
}

resource "google_project_service_identity" "cloudbuild_sa" {
  provider   = google-beta
  project    = var.project_id
  service    = "cloudbuild.googleapis.com"
  depends_on = [google_project_service.apis]
}

data "google_storage_project_service_account" "gcs_sa" {
  count      = var.grant_service_agent_kms_iam ? 1 : 0
  project    = var.project_id
  depends_on = [google_project_service.apis]
}

# Wait 60s after enabling APIs and provisioning service identities so IAM
# recognizes newly created service agents on fresh projects.
resource "time_sleep" "service_agent_propagation" {
  create_duration = "60s"
  depends_on = [
    data.google_storage_project_service_account.gcs_sa,
    google_project_service.apis,
    google_project_service_identity.artifact_registry_sa,
    google_project_service_identity.cloudbuild_sa,
  ]
}

resource "google_kms_crypto_key_iam_member" "service_agents" {
  for_each      = local.kms_service_agents
  crypto_key_id = var.kms_key_id
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = each.value
  depends_on    = [time_sleep.service_agent_propagation]
}

module "builder-sa" {
  source       = "../../../modules/iam-service-account"
  project_id   = var.project_id
  prefix       = var.prefix
  name         = var.builder_sa_name
  display_name = "Image Factory Cloud Build Service Account"
  description  = "Least-privilege service account for private image builds."

  iam_project_roles = {
    (var.project_id) = local.builder_project_roles
  }

  depends_on = [google_project_service.apis]
}

resource "google_service_account_iam_member" "cloudbuild_token_creator" {
  service_account_id = module.builder-sa.id
  role               = "roles/iam.serviceAccountTokenCreator"
  member             = local.cloudbuild_agent_iam
  depends_on         = [time_sleep.service_agent_propagation]
}

resource "google_compute_subnetwork_iam_member" "builder_network_user" {
  count      = local.subnetwork_host_project != var.project_id ? 1 : 0
  project    = local.subnetwork_host_project
  region     = local.subnetwork_region
  subnetwork = local.subnetwork_name
  role       = "roles/compute.networkUser"
  member     = module.builder-sa.iam_email
}

module "builder-ssh-firewall" {
  source     = "../../../modules/net-vpc-firewall"
  count      = var.enable_ssh_firewall_rule ? 1 : 0
  project_id = local.subnetwork_host_project
  network    = local.builder_network_name
  default_rules_config = {
    disabled = true
  }
  ingress_rules = {
    ("${local._prefix}allow-builder-ssh") = {
      description          = "Allow Cloud Build workers SSH to image builders."
      source_ranges        = [var.peered_network_ip_range]
      targets              = ["image-builder"]
      use_service_accounts = false
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

module "staging-bucket" {
  source                      = "../../../modules/gcs"
  project_id                  = var.project_id
  prefix                      = var.prefix
  name                        = var.staging_bucket_name
  location                    = var.region
  encryption_key              = var.kms_key_id
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"
  versioning                  = true
  force_destroy               = var.staging_bucket_force_destroy
  labels                      = var.labels

  iam_bindings_additive = {
    builder_object_viewer = {
      member = module.builder-sa.iam_email
      role   = local.staging_bucket_builder_role
    }
  }

  objects_to_upload = {
    cloudbuild_config = {
      name         = var.cloudbuild_config_object_name
      content      = local.cloudbuild_config
      content_type = "application/x-yaml"
      kms_key_name = var.kms_key_id
    }
  }

  depends_on = [
    google_kms_crypto_key_iam_member.service_agents,
    time_sleep.service_agent_propagation,
  ]
}

module "builder-registry" {
  source                        = "../../../modules/artifact-registry"
  project_id                    = var.project_id
  location                      = var.region
  name                          = var.artifact_registry_name
  description                   = "Private CMEK mirror for image builders."
  encryption_key                = var.kms_key_id
  enable_vulnerability_scanning = true
  labels                        = var.labels

  format = {
    docker = {
      standard = {
        immutable_tags = true
      }
    }
  }

  iam_bindings_additive = {
    builder_reader = {
      member = module.builder-sa.iam_email
      role   = "roles/artifactregistry.reader"
    }
  }

  depends_on = [
    google_kms_crypto_key_iam_member.service_agents,
    time_sleep.service_agent_propagation,
  ]
}

resource "google_cloudbuild_worker_pool" "default" {
  project      = var.project_id
  name         = local.worker_pool_name
  location     = var.region
  display_name = "Image Factory Private Worker Pool"

  network_config {
    peered_network          = local.peered_network_normalized
    peered_network_ip_range = var.peered_network_ip_range
  }

  worker_config {
    disk_size_gb   = var.worker_pool_disk_size_gb
    machine_type   = var.worker_pool_machine_type
    no_external_ip = true
  }

  lifecycle {
    # Private pools attach through non-transitive VPC Network Peering, so
    # workers only reach builders that live in peered_network itself.
    precondition {
      condition = (
        var.allow_builder_network_mismatch
        || local.builder_network_normalized == local.peered_network_normalized
      )
      error_message = join(" ", [
        "The builder_subnetwork VPC must match peered_network because VPC",
        "Network Peering is non-transitive. Set",
        "allow_builder_network_mismatch = true only when HA VPN or NCC",
        "routes peered_network_ip_range to the builder network.",
      ])
    }
  }

  depends_on = [time_sleep.service_agent_propagation]
}

resource "google_cloudbuild_trigger" "default" {
  count           = var.trigger_config == null ? 0 : 1
  project         = var.project_id
  location        = var.region
  name            = var.trigger_config.name
  description     = var.trigger_config.description
  disabled        = var.trigger_config.disabled
  service_account = module.builder-sa.id
  tags            = var.trigger_config.tags
  filename        = local._trigger_is_repo ? var.trigger_config.filename : null
  substitutions = (
    local._trigger_is_repo ? local._trigger_substitutions : null
  )

  dynamic "approval_config" {
    for_each = var.trigger_config.approval_required ? [""] : []
    content {
      approval_required = true
    }
  }

  dynamic "repository_event_config" {
    for_each = local._trigger_is_repo ? [""] : []
    content {
      repository = var.trigger_config.repository_event.repository
      push {
        branch       = var.trigger_config.repository_event.branch
        invert_regex = var.trigger_config.repository_event.invert_regex
        tag          = var.trigger_config.repository_event.tag
      }
    }
  }

  dynamic "pubsub_config" {
    for_each = local._trigger_is_pubsub ? [""] : []
    content {
      topic = var.trigger_config.pubsub_topic
    }
  }

  dynamic "build" {
    for_each = local._trigger_is_pubsub ? [""] : []
    content {
      substitutions = local._trigger_substitutions
      timeout       = var.build_timeout

      options {
        logging     = "CLOUD_LOGGING_ONLY"
        worker_pool = google_cloudbuild_worker_pool.default.id
      }

      dynamic "step" {
        for_each = local._cloudbuild_steps
        content {
          id         = step.value.id
          name       = step.value.name
          entrypoint = step.value.entrypoint
          args       = step.value.args
          wait_for   = try(step.value.waitFor, null)
        }
      }
    }
  }

  depends_on = [
    google_cloudbuild_worker_pool.default,
    google_service_account_iam_member.cloudbuild_token_creator,
    module.builder-registry,
    module.staging-bucket,
  ]
}
