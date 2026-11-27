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
}

mock_provider "google-beta" {
  mock_resource "google_project_service_identity" {
    defaults = {
      email  = "service-123456789012@gcp-sa-secretmanager.iam.gserviceaccount.com"
      member = "serviceAccount:service-123456789012@gcp-sa-secretmanager.iam.gserviceaccount.com"
    }
  }
}

mock_provider "tls" {
  mock_resource "tls_private_key" {
    defaults = {
      private_key_pem = "MOCK-PRIVATE-KEY"
    }
  }
  mock_resource "tls_self_signed_cert" {
    defaults = {
      cert_pem = "MOCK-CERT-PEM"
    }
  }
}

mock_provider "time" {}

variables {
  gitlab_uri   = "https://gitlab.example.com"
  kms_key      = "projects/core-project/locations/us-east4/keyRings/my-kr/cryptoKeys/default"
  net_project  = "test-net-host"
  network      = "projects/test-net-host/global/networks/prod-spoke-0"
  network_name = "prod-spoke-0"
  nodepool_node_count = {
    initial = 1
  }
  project_id = "my-project"
  region     = "us-east4"
  sa         = "gitlab-sa"
  subnetwork = "projects/test-net-host/regions/us-east4/subnetworks/prod-tenant-1-subnet"
  zone       = "us-east4-a"
}

run "default_self_signed_https_load_balancer_and_secret_manager" {
  command = apply

  assert {
    condition     = module.application-lb.forwarding_rule.port_range == "443"
    error_message = "Application LB must expose HTTPS on port 443."
  }

  assert {
    condition     = tls_self_signed_cert.default[0].subject[0].common_name == "gitlab.example.com"
    error_message = "Self-signed certificate common_name must be the hostname without scheme."
  }

  assert {
    condition     = tolist(tls_self_signed_cert.default[0].dns_names) == tolist(["gitlab.example.com"])
    error_message = "Self-signed certificate dns_names must include the GitLab hostname."
  }

  assert {
    condition     = length(module.tls-private-key-secret) == 1 && output.tls_private_key_secret_id != null
    error_message = "Generated TLS private key must be stored in CMEK-encrypted Secret Manager."
  }

  assert {
    condition     = strcontains(module.compute-vm.instance.metadata["startup-script"], "nginx['listen_https'] = false") && strcontains(module.compute-vm.instance.metadata["startup-script"], "nginx['listen_port'] = 80") && strcontains(module.compute-vm.instance.metadata["startup-script"], "X-Forwarded-Proto")
    error_message = "Startup script must configure GitLab Nginx for HTTP backend behind HTTPS ALB."
  }

  assert {
    condition     = module.gke-node-pool.service_account_email == module.gke-node-sa.email && module.gke-node-sa.email != google_service_account.gitlab_sa.email
    error_message = "GKE node pool must use dedicated least-privilege gke-node-sa."
  }
}

run "custom_certificate_id_skips_self_signed_generation" {
  command = plan

  variables {
    ssl_certificate = {
      certificate_id = "projects/my-project/regions/us-east4/sslCertificates/gitlab-cert"
    }
  }

  assert {
    condition     = length(tls_private_key.default) == 0 && length(tls_self_signed_cert.default) == 0 && length(module.tls-private-key-secret) == 0
    error_message = "Custom certificate_id must skip self-signed TLS generation and Secret Manager storage."
  }

  assert {
    condition     = module.application-lb.forwarding_rule.port_range == "443"
    error_message = "Custom certificate_id deployment must still serve HTTPS."
  }
}

run "custom_inline_certificate_skips_self_signed_generation" {
  command = plan

  variables {
    ssl_certificate = {
      certificate = "MOCK-CERT"
      private_key = "MOCK-KEY"
    }
  }

  assert {
    condition     = length(tls_private_key.default) == 0 && length(module.tls-private-key-secret) == 0
    error_message = "Custom inline certificate must skip self-signed TLS generation."
  }
}

run "rejects_http_gitlab_uri" {
  command = plan

  variables {
    gitlab_uri = "http://gitlab.example.com"
  }

  expect_failures = [
    var.gitlab_uri,
  ]
}

run "rejects_incomplete_ssl_certificate" {
  command = plan

  variables {
    ssl_certificate = {
      certificate = "ONLY-CERT"
    }
  }

  expect_failures = [
    var.ssl_certificate,
  ]
}

run "rejects_empty_ssl_certificate_id" {
  command = plan

  variables {
    ssl_certificate = {
      certificate_id = "   "
    }
  }

  expect_failures = [
    var.ssl_certificate,
  ]
}

run "rejects_empty_inline_ssl_certificate" {
  command = plan

  variables {
    ssl_certificate = {
      certificate = ""
      private_key = "MOCK-KEY"
    }
  }

  expect_failures = [
    var.ssl_certificate,
  ]
}
