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
mock_provider "time" {}

override_data {
  target = data.google_compute_network.network
  values = {
    self_link = "https://www.googleapis.com/compute/v1/projects/test-net-host/global/networks/test-vpc"
  }
}

variables {
  main_project_id    = "test-workload"
  network_project_id = "test-net-host"
  network_name       = "test-vpc"
  database_name      = "test-postgres"
  kms_key_name       = "projects/test-core/locations/us-east4/keyRings/test-kr/cryptoKeys/test-key"
}

# The blueprint plans without any firewall input, because it creates no VPC
# firewall rule.
run "plan_without_firewall_inputs" {
  command = plan

  assert {
    condition     = module.postgres.name == "test-postgres"
    error_message = "Expected the Cloud SQL instance to be planned."
  }

  assert {
    condition     = google_kms_crypto_key_iam_member.sql_sa.crypto_key_id == var.kms_key_name
    error_message = "Expected the Cloud SQL service agent CMEK binding."
  }
}

# Existing callers that still set the deprecated firewall inputs keep
# planning, and the deprecation check reports the ignored inputs.
run "plan_with_deprecated_firewall_inputs" {
  command = plan

  variables {
    allowed_firewall_ports = [5432]
    firewall_name          = "allow-postgres"
    firewall_source_range  = ["192.168.1.0/24"]
  }

  expect_failures = [
    check.deprecated_firewall_inputs,
  ]
}

# Without psc_config the instance keeps using Private Services Access on the
# network, which is the behavior of earlier releases.
run "plan_default_uses_private_services_access" {
  command = plan

  assert {
    condition = (
      module.postgres.instances["primary"].settings[0].ip_configuration[0].private_network
      == "https://www.googleapis.com/compute/v1/projects/test-net-host/global/networks/test-vpc"
    )
    error_message = "Expected the instance to attach to the network through Private Services Access."
  }

  assert {
    condition = (
      module.postgres.instances["primary"].settings[0].ip_configuration[0].psc_config[0].psc_enabled
      == false
    )
    error_message = "Expected Private Service Connect to stay disabled by default."
  }

  assert {
    condition = (
      module.postgres.instances["primary"].settings[0].ip_configuration[0].ipv4_enabled
      == false
    )
    error_message = "Expected the instance to have no public IPv4 address."
  }

  assert {
    condition     = output.psc_dns_name == null && output.psc_service_attachment_link == null
    error_message = "Expected the Private Service Connect outputs to be null by default."
  }
}

# With psc_config the instance uses Private Service Connect only, so the
# network needs no Private Services Access connection.
run "plan_psc_config_uses_private_service_connect" {
  command = plan

  variables {
    psc_config = {
      allowed_consumer_projects = ["test-net-host"]
    }
  }

  assert {
    condition = (
      module.postgres.instances["primary"].settings[0].ip_configuration[0].psc_config[0].psc_enabled
      == true
    )
    error_message = "Expected Private Service Connect to be enabled."
  }

  assert {
    condition = (
      module.postgres.instances["primary"].settings[0].ip_configuration[0].psc_config[0].allowed_consumer_projects
      == toset(["test-net-host"])
    )
    error_message = "Expected only the listed projects to be allowed to connect."
  }

  assert {
    condition = (
      module.postgres.instances["primary"].settings[0].ip_configuration[0].private_network
      == null
    )
    error_message = "Expected no Private Services Access attachment with Private Service Connect."
  }

  assert {
    condition = (
      module.postgres.instances["primary"].settings[0].ip_configuration[0].ipv4_enabled
      == false
    )
    error_message = "Expected the instance to have no public IPv4 address."
  }
}

# An empty allowlist creates an instance that no endpoint can reach, so the
# blueprint rejects it at plan time.
run "plan_rejects_empty_allowed_consumer_projects" {
  command = plan

  variables {
    psc_config = {
      allowed_consumer_projects = []
    }
  }

  expect_failures = [
    var.psc_config,
  ]
}
