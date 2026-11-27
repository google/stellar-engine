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

mock_provider "google" {}
mock_provider "google-beta" {}

override_data {
  target = module.project.data.google_project.project[0]
  values = {
    number = "123456789012"
  }
}

override_data {
  target = module.project.data.google_storage_project_service_account.gcs_sa[0]
  values = {
    email_address = "service-123456789012@gs-project-accounts.iam.gserviceaccount.com"
  }
}

variables {
  project_config = {
    project_id = "my-vertex-project"
  }
  network_config = {
    network_project_id = "my-net-host"
    network_name       = "prod-spoke-0"
    subnetwork_name    = "prod-tenant-1-subnet"
  }
  bucket_name  = "my-vertex-bucket"
  dataset_name = "my_vertex_dataset"
  prefix       = "pfx"
  region       = "us-east4"
  notebooks = {
    notebook-00 = {
      type  = "USER_MANAGED"
      owner = "admin@example.com"
    }
  }
  service_encryption_keys = {
    aiplatform = "projects/my-kms-project/locations/us-east4/keyRings/my-kr/cryptoKeys/default"
    bq         = "projects/my-kms-project/locations/us-east4/keyRings/my-kr/cryptoKeys/default"
    notebooks  = "projects/my-kms-project/locations/us-east4/keyRings/my-kr/cryptoKeys/default"
    storage    = "projects/my-kms-project/locations/us-east4/keyRings/my-kr/cryptoKeys/default"
  }
}

run "plan_reuse_existing_project" {
  command = plan

  assert {
    condition     = module.project.number == "123456789012"
    error_message = "Expected project_reuse path to look up existing project data when billing_account_id is null."
  }

  assert {
    condition     = local.attach_shared_vpc == false
    error_message = "Expected Shared VPC attachment to default to false when reusing a project."
  }

  assert {
    condition     = length(google_compute_subnetwork_iam_member.notebooks_subnet_user) == 1
    error_message = "Expected direct subnetwork IAM binding for Notebooks agent when not attaching Shared VPC."
  }

  assert {
    condition     = google_compute_subnetwork_iam_member.notebooks_subnet_user[0].subnetwork == "prod-tenant-1-subnet"
    error_message = "Expected subnetwork IAM binding to target prod-tenant-1-subnet."
  }

  assert {
    condition     = google_workbench_instance.playground["notebook-00"].gce_setup[0].container_image[0].repository == "us-docker.pkg.dev/deeplearning-platform-release/gcr.io/base-cpu"
    error_message = "Expected Workbench container image to use Artifact Registry rather than legacy gcr.io."
  }
}

run "plan_create_project_attaches_shared_vpc" {
  command = plan

  variables {
    project_config = {
      billing_account_id = "012345-6789AB-CDEF01"
      parent             = "folders/123456789012"
      project_id         = "my-new-vertex-project"
    }
  }

  assert {
    condition     = local.attach_shared_vpc == true
    error_message = "Expected Shared VPC attachment to default to true when creating a new project."
  }

  assert {
    condition     = length(google_compute_subnetwork_iam_member.notebooks_subnet_user) == 0
    error_message = "Expected module.project to manage subnet IAM when attaching Shared VPC."
  }
}

run "plan_reuse_project_explicit_attach" {
  command = plan

  variables {
    network_config = {
      attach             = true
      network_project_id = "my-net-host"
      network_name       = "prod-spoke-0"
      subnetwork_name    = "prod-tenant-1-subnet"
    }
  }

  assert {
    condition     = local.attach_shared_vpc == true
    error_message = "Expected explicit network_config.attach = true to enable Shared VPC attachment."
  }

  assert {
    condition     = length(google_compute_subnetwork_iam_member.notebooks_subnet_user) == 0
    error_message = "Expected no duplicate subnetwork IAM resource when module.project manages Shared VPC."
  }
}
