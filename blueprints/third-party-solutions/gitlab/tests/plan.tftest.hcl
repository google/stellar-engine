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

mock_provider "google" {
  mock_data "google_project" {
    defaults = {
      number     = "123456789012"
      project_id = "my-project"
    }
  }
  mock_resource "google_compute_disk" {
    defaults = {
      name = "mock-zonal-disk"
    }
  }
  mock_resource "google_compute_region_disk" {
    defaults = {
      id = "projects/my-project/regions/us-east4/disks/mock-regional-disk"
    }
  }
  mock_resource "google_service_account" {
    defaults = {
      email = "mock-sa@my-project.iam.gserviceaccount.com"
      name  = "projects/my-project/serviceAccounts/mock-sa@my-project.iam.gserviceaccount.com"
    }
  }
}

mock_provider "google-beta" {
  mock_resource "google_compute_disk" {
    defaults = {
      name = "mock-zonal-disk"
    }
  }
  mock_resource "google_compute_region_disk" {
    defaults = {
      id = "projects/my-project/regions/us-east4/disks/mock-regional-disk"
    }
  }
  mock_resource "google_service_account" {
    defaults = {
      email = "mock-sa@my-project.iam.gserviceaccount.com"
      name  = "projects/my-project/serviceAccounts/mock-sa@my-project.iam.gserviceaccount.com"
    }
  }
}

mock_provider "null" {}

mock_provider "random" {}

mock_provider "tls" {
  mock_resource "tls_private_key" {
    defaults = {
      private_key_pem = "MOCK-PRIVATE-KEY"
    }
  }
  mock_resource "tls_self_signed_cert" {
    defaults = {
      cert_pem = "MOCK-CA-CERT"
    }
  }
  mock_resource "tls_cert_request" {
    defaults = {
      cert_request_pem = "MOCK-CSR"
    }
  }
  mock_resource "tls_locally_signed_cert" {
    defaults = {
      cert_pem = "MOCK-SIGNED-CERT"
    }
  }
}

variables {
  network_config = {
    host_project      = "test-net-host"
    network_self_link = "projects/test-net-host/global/networks/prod-spoke-0"
    subnet_self_link  = "projects/test-net-host/regions/us-east4/subnetworks/prod-tenant-1-subnet"
  }
  prefix     = "pfx"
  project_id = "my-project"
  region     = "us-east4"
}

run "default_gcs_location_follows_region_and_data_disk_defaults_pd_balanced" {
  command = plan

  providers = {
    google      = google
    google-beta = google-beta
    null        = null
    random      = random
    tls         = tls
  }

  assert {
    condition = alltrue([
      for k, mod in module.gitlab-object-storage :
      mod.bucket.location == "us-east4"
    ])
    error_message = "Default GCS bucket location must derive from var.region rather than EU."
  }

  assert {
    condition     = var.gitlab_instance_config.data_disk.type == "pd-balanced"
    error_message = "Default data_disk.type must preserve pd-balanced."
  }
}

run "respects_custom_gcs_location_and_data_disk_type" {
  command = plan

  providers = {
    google      = google
    google-beta = google-beta
    null        = null
    random      = random
    tls         = tls
  }

  variables {
    gcs_config = {
      location = "US"
    }
    gitlab_instance_config = {
      data_disk = {
        type = "pd-ssd"
      }
    }
  }

  assert {
    condition = alltrue([
      for k, mod in module.gitlab-object-storage :
      mod.bucket.location == "US"
    ])
    error_message = "Custom gcs_config.location must override default region."
  }

  assert {
    condition     = var.gitlab_instance_config.data_disk.type == "pd-ssd"
    error_message = "Custom gitlab_instance_config.data_disk.type must be accepted."
  }
}

run "data_disk_replica_zone_creates_regional_disk" {
  command = apply

  providers = {
    google      = google
    google-beta = google-beta
    null        = null
    random      = random
    tls         = tls
  }

  variables {
    gitlab_instance_config = {
      data_disk = {
        replica_zone = "us-east4-b"
        type         = "pd-ssd"
      }
    }
  }

  assert {
    condition     = length(nonsensitive(module.gitlab-instance.instance.attached_disk)) == 1
    error_message = "Expected one attached data disk on gitlab-instance."
  }

  assert {
    condition     = nonsensitive(module.gitlab-instance.instance.attached_disk[0].source) == "projects/my-project/regions/us-east4/disks/mock-regional-disk"
    error_message = "Setting data_disk.replica_zone must attach a google_compute_region_disk rather than a zonal disk."
  }
}

run "legacy_replica_zone_fallback_creates_regional_disk" {
  command = apply

  providers = {
    google      = google
    google-beta = google-beta
    null        = null
    random      = random
    tls         = tls
  }

  variables {
    gitlab_instance_config = {
      replica_zone = "us-east4-c"
    }
  }

  assert {
    condition     = nonsensitive(module.gitlab-instance.instance.attached_disk[0].source) == "projects/my-project/regions/us-east4/disks/mock-regional-disk"
    error_message = "Top-level gitlab_instance_config.replica_zone must remain supported as a fallback."
  }
}
