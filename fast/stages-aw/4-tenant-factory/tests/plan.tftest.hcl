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

variables {
  automation = {
    kms_keys = {
      gcs = "projects/iac-0/locations/us-east4/keyRings/g/cryptoKeys/gcs"
    }
    outputs_bucket = "test-iac-core-outputs-0"
    project_id     = "test-iac-core-0"
  }
  billing_account = {
    id = "012345-67890A-BCDEF0"
  }
  environment_folders = {
    dev  = "folders/100000000001"
    test = "folders/100000000002"
    prod = "folders/100000000003"
  }
  kms_keys = {
    us-east4-tenant = (
      "projects/sec-0/locations/us-east4/keyRings/t/cryptoKeys/k"
    )
  }
  prefix = "se"
  shared_vpc_host_projects = {
    dev  = "se-dev-net-host-0"
    prod = "se-prod-net-host-0"
  }
}

# 1. Default multi-project YAML + HCL tenants under environment-separated dev
#    and prod folders, multi-subnet Shared VPC, BigQuery + GCS CMEK, VPC-SC,
#    controlling-project automation, and deletion_policy = PREVENT.
run "plan_yaml_and_hcl_multi_project_tenants" {
  command = plan

  variables {
    tenants = {
      beta = {
        descriptive_name = "Beta Prod"
        environment      = "prod"
        lifecycle_state  = "active"
        automation = {
          service_accounts = {
            rw = { description = "Beta read/write automation." }
            ro = { description = "Beta read-only plan automation." }
          }
        }
        iam = {
          "roles/browser" = ["group:beta-prod-ops@example.com"]
        }
        projects = {
          web-0 = {
            name             = "prod-beta-web-0"
            descriptive_name = "Beta Prod Web 0"
            services = [
              "compute.googleapis.com",
              "storage.googleapis.com",
            ]
            kms_services = {
              "storage.googleapis.com" = ["us-east4-tenant"]
            }
            shared_vpc_subnets = [
              "us-east4/prod-beta-web",
              "us-east4/prod-beta-api",
            ]
            shared_vpc_network_users = [
              "group:beta-prod-ops@example.com",
            ]
            vpc_sc_perimeter = {
              perimeter_name = (
                "accessPolicies/123456789/servicePerimeters/prod_0"
              )
              is_dry_run = true
            }
            iam = {
              "roles/compute.viewer" = ["group:beta-prod-ops@example.com"]
            }
          }
          analytics-0 = {
            name             = "prod-beta-data-0"
            descriptive_name = "Beta Prod Analytics 0"
            services = [
              "bigquery.googleapis.com",
              "storage.googleapis.com",
            ]
            kms_services = {
              "bigquery.googleapis.com" = ["us-east4-tenant"]
            }
            iam = {
              "roles/bigquery.dataViewer" = ["group:beta-prod-ops@example.com"]
            }
          }
        }
      }
    }
  }

  assert {
    condition = (
      contains(keys(local.pf_folders), "dev/acme") &&
      contains(keys(local.pf_folders), "prod/beta")
    )
    error_message = "Expected dev/acme (YAML) and prod/beta (HCL) folders."
  }

  assert {
    condition = (
      local.pf_folders["dev/acme"].parent == "folders/100000000001" &&
      local.pf_folders["prod/beta"].parent == "folders/100000000003"
    )
    error_message = "Expected folders to attach to environment parents."
  }

  assert {
    condition = (
      local.pf_folders["dev/acme"].deletion_protection == true &&
      local.pf_folders["prod/beta"].deletion_protection == true
    )
    error_message = "Expected active folders to enable deletion_protection."
  }

  assert {
    condition     = length(keys(module.tenant-projects)) == 4
    error_message = "Expected 4 projects across YAML acme and HCL beta."
  }

  assert {
    condition = alltrue([
      for k, p in local.tenant_projects :
      p.deletion_policy == "PREVENT" &&
      p.lien_reason != null &&
      p.billing_account == "012345-67890A-BCDEF0"
    ])
    error_message = "Expected PREVENT deletion_policy, liens, and billing."
  }

  assert {
    condition = (
      var.storage_location == "us-east4" &&
      local.pf_folders["prod/beta"].automation.bucket.location == "us-east4" &&
      local.pf_folders["prod/beta"].automation.bucket.encryption_key == (
        var.automation.kms_keys.gcs
      ) &&
      local.pf_folders["prod/beta"].automation.bucket.force_destroy == false
    )
    error_message = "Expected us-east4 default and Stage 0 GCS CMEK fallback."
  }

  assert {
    condition = (
      !contains(
        keys(
          local.tenant_projects["dev/acme/data-0"].service_encryption_key_ids
        ),
        "bigquery.googleapis.com"
      ) &&
      contains(
        local.tenant_projects["dev/acme/data-0"].services,
        "bigquery.googleapis.com"
      ) &&
      contains(keys(local.tenant_bigquery_projects), "dev/acme/data-0") &&
      contains(
        keys(local.tenant_bigquery_projects),
        "prod/beta/analytics-0"
      ) &&
      time_sleep.tenant_bq_sa_propagation[
        "dev/acme/data-0"
      ].create_duration == "60s" &&
      google_kms_crypto_key_iam_member.tenant_bigquery_cmek[
        "dev/acme/data-0/0"
      ].role == "roles/cloudkms.cryptoKeyEncrypterDecrypter" &&
      google_kms_crypto_key_iam_member.tenant_bigquery_cmek[
        "prod/beta/analytics-0/0"
      ].crypto_key_id == var.kms_keys["us-east4-tenant"]
    )
    error_message = "Expected BigQuery CMEK via tenant_bq SA and 60s sleep."
  }

  assert {
    condition = (
      length(keys(
        local.tenant_project_shared_vpc["dev/acme/app-0"].network_subnet_users
      )) == 2 &&
      length(keys(
        local.tenant_project_shared_vpc["prod/beta/web-0"].network_subnet_users
      )) == 2 &&
      length(
        local.tenant_project_shared_vpc["dev/acme/app-0"].network_users
      ) == 0
    )
    error_message = "Expected multi-subnet Shared VPC IAM per listed subnet."
  }

  assert {
    condition = (
      local.tenant_projects["prod/beta/web-0"].vpc_sc.is_dry_run == true &&
      local.tenant_projects["prod/beta/web-0"].vpc_sc.perimeter_name == (
        "accessPolicies/123456789/servicePerimeters/prod_0"
      )
    )
    error_message = "Expected additive VPC-SC perimeter enrollment."
  }

  assert {
    condition = (
      contains(
        keys(local.tenant_workload_sas),
        "dev/acme/app-0/app-runtime"
      ) &&
      contains(
        keys(local.pf_folders["prod/beta"].automation.service_accounts),
        "rw"
      ) &&
      contains(
        keys(local.pf_folders["prod/beta"].automation.service_accounts),
        "ro"
      )
    )
    error_message = "Expected workload and automation SAs to be planned."
  }

  assert {
    condition = (
      output.tenant_projects["dev/acme/app-0"] == "se-dev-acme-app-0" &&
      output.tenant_projects["dev/acme/data-0"] == "se-dev-acme-data-0" &&
      output.tenant_projects["prod/beta/web-0"] == "se-prod-beta-web-0" &&
      output.tenant_projects["prod/beta/analytics-0"] == "se-prod-beta-data-0"
    )
    error_message = "Expected deterministic prefixed tenant_projects output."
  }

  assert {
    condition = (
      contains(keys(output.tenant_folders), "dev/acme") &&
      contains(keys(output.tenant_folders), "prod/beta") &&
      contains(
        keys(output.tenant_service_accounts),
        "dev/acme/app-0/app-runtime"
      ) &&
      contains(
        keys(output.tenant_service_accounts),
        "prod/beta/automation/rw"
      ) &&
      contains(
        keys(output.tenant_service_accounts),
        "prod/beta/automation/ro"
      ) &&
      contains(
        keys(output.tenant_state_buckets),
        "prod/beta/automation/tf-state"
      )
    )
    error_message = "Expected outputs for folders, SAs, and state buckets."
  }
}

# 1b. Same tenant slug (acme) coexists across dev (YAML) and prod (HCL).
run "plan_same_tenant_slug_across_dev_and_prod" {
  command = plan

  variables {
    tenants = {
      prod-acme = {
        tenant_id        = "acme"
        descriptive_name = "Acme Prod"
        environment      = "prod"
        lifecycle_state  = "active"
        projects = {
          app-0 = {
            descriptive_name = "Acme Prod App 0"
            services         = ["logging.googleapis.com"]
          }
        }
      }
    }
  }

  assert {
    condition = (
      contains(keys(local.pf_folders), "dev/acme") &&
      contains(keys(local.pf_folders), "prod/acme") &&
      local.pf_folders["dev/acme"].parent == "folders/100000000001" &&
      local.pf_folders["prod/acme"].parent == "folders/100000000003"
    )
    error_message = "Expected dev/acme and prod/acme in separate env folders."
  }

  assert {
    condition = (
      output.tenant_projects["dev/acme/app-0"] == "se-dev-acme-app-0" &&
      output.tenant_projects["prod/acme/app-0"] == "se-prod-acme-app-0" &&
      local.tenant_projects["dev/acme/app-0"].labels.tenant == "acme" &&
      local.tenant_projects["prod/acme/app-0"].labels.tenant == "acme"
    )
    error_message = "Expected distinct project IDs and matching tenant labels."
  }
}

# 1c. Composite CMEK companion APIs and Shared VPC service-agent backing APIs
#     auto-populate into services so modules/project never hits Invalid index.
run "plan_composite_cmek_and_svpc_agent_backing_apis" {
  command = plan

  variables {
    tenants = {
      gamma = {
        descriptive_name = "Gamma Dev"
        environment      = "dev"
        lifecycle_state  = "active"
        projects = {
          gke-0 = {
            kms_services = {
              "container.googleapis.com"  = ["us-east4-tenant"]
              "datafusion.googleapis.com" = ["us-east4-tenant"]
            }
            shared_vpc_service_agent_iam = {
              "roles/composer.sharedVpcAgent" = ["$service_agents:composer"]
            }
            shared_vpc_service_grants = [
              "$service_agents:vpcaccess.googleapis.com",
            ]
          }
        }
      }
    }
  }

  assert {
    condition = alltrue([
      for svc in [
        "composer.googleapis.com",
        "compute.googleapis.com",
        "container.googleapis.com",
        "datafusion.googleapis.com",
        "dataproc.googleapis.com",
        "pubsub.googleapis.com",
        "spanner.googleapis.com",
        "storage.googleapis.com",
        "vpcaccess.googleapis.com",
      ] : contains(local.tenant_projects["dev/gamma/gke-0"].services, svc)
    ])
    error_message = "Expected composite CMEK and SVPC backing APIs enabled."
  }
}

# 2. billing_linkage_mode = external_gate with billing_account = null plans.
run "plan_external_gate_billing_mode" {
  command = plan

  variables {
    billing_account      = null
    billing_linkage_mode = "external_gate"
  }

  assert {
    condition = alltrue([
      for k, p in local.tenant_projects : p.billing_account == null
    ])
    error_message = "Expected external_gate mode to set billing_account null."
  }
}

# 3a. lifecycle_state = archived (force_destroy = false) switches
#     deletion_policy to ABANDON and removes project liens.
run "plan_archived_tenant_abandons_and_removes_lien" {
  command = plan

  variables {
    tenants = {
      acme = {
        descriptive_name = "Acme Dev"
        environment      = "dev"
        lifecycle_state  = "archived"
        projects = {
          app-0 = {
            name             = "dev-acme-app-0"
            descriptive_name = "Acme Dev App 0"
            services         = ["logging.googleapis.com"]
          }
          data-0 = {
            name             = "dev-acme-data-0"
            descriptive_name = "Acme Dev Data 0"
            services         = ["logging.googleapis.com"]
          }
        }
      }
    }
  }

  assert {
    condition = (
      contains(keys(module.tenant-projects), "dev/acme/app-0") &&
      contains(keys(module.tenant-projects), "dev/acme/data-0")
    )
    error_message = "Expected archived projects to remain in Terraform state."
  }

  assert {
    condition = alltrue([
      for k, p in local.tenant_projects :
      p.deletion_policy == "ABANDON" && p.lien_reason == null
    ])
    error_message = "Expected archived projects to use ABANDON without liens."
  }

  assert {
    condition     = local.pf_folders["dev/acme"].deletion_protection == false
    error_message = "Expected archived folder deletion_protection = false."
  }
}

# 3b. lifecycle_state = archived + force_destroy = true switches archived
#     projects to DELETE and sets force_destroy on state buckets while keeping
#     active tenants at PREVENT.
run "plan_archived_tenant_with_force_destroy_deletes" {
  command = plan

  variables {
    force_destroy = true
    tenants = {
      sandbox = {
        descriptive_name = "Sandbox Dev"
        environment      = "dev"
        lifecycle_state  = "archived"
        automation = {
          service_accounts = {
            rw = {}
          }
        }
        projects = {
          app-0 = {
            services = ["logging.googleapis.com"]
          }
        }
      }
    }
  }

  assert {
    condition = (
      local.tenant_projects["dev/sandbox/app-0"].deletion_policy == "DELETE" &&
      local.tenant_projects["dev/sandbox/app-0"].lien_reason == null &&
      local.pf_folders["dev/sandbox"].deletion_protection == false &&
      local.pf_folders[
        "dev/sandbox"
      ].automation.bucket.force_destroy == true &&
      local.tenant_projects["dev/acme/app-0"].deletion_policy == "PREVENT"
    )
    error_message = "Expected DELETE on archived and PREVENT on active."
  }
}

# 4a. Reject roles/owner in tenant project IAM at plan time.
run "reject_owner_role_in_tenant_iam" {
  command = plan

  variables {
    tenants = {
      bad = {
        environment     = "dev"
        lifecycle_state = "active"
        projects = {
          app-0 = {
            iam = {
              "roles/owner" = ["group:bad-admins@example.com"]
            }
          }
        }
      }
    }
  }

  expect_failures = [
    var.tenants,
  ]
}

# 4b. Reject roles/editor in tenant folder IAM at plan time.
run "reject_editor_role_in_tenant_folder_iam" {
  command = plan

  variables {
    tenants = {
      bad = {
        environment     = "dev"
        lifecycle_state = "active"
        iam = {
          "roles/editor" = ["group:bad-admins@example.com"]
        }
        projects = {
          app-0 = {}
        }
      }
    }
  }

  expect_failures = [
    var.tenants,
  ]
}

# 4c. Reject roles/resourcemanager.organizationAdmin in tenant IAM.
run "reject_org_admin_role_in_tenant_iam" {
  command = plan

  variables {
    tenants = {
      bad = {
        environment     = "dev"
        lifecycle_state = "active"
        projects = {
          app-0 = {
            iam_by_principals = {
              "group:bad-admins@example.com" = [
                "roles/resourcemanager.organizationAdmin",
              ]
            }
          }
        }
      }
    }
  }

  expect_failures = [
    var.tenants,
  ]
}

# 4d. Reject expanded privilege-escalation denylist roles at plan time.
run "reject_expanded_denylist_roles" {
  command = plan

  variables {
    tenants = {
      bad = {
        environment     = "dev"
        lifecycle_state = "active"
        iam = {
          "roles/orgpolicy.policyAdmin" = ["group:bad-admins@example.com"]
        }
        projects = {
          app-0 = {
            iam = {
              "roles/iam.securityAdmin" = ["group:bad-admins@example.com"]
            }
          }
        }
      }
    }
  }

  expect_failures = [
    var.tenants,
  ]
}

# 4e. Reject non-allowlisted role in shared_vpc_service_agent_iam at plan time.
run "reject_non_allowlisted_role_in_shared_vpc_service_agent_iam" {
  command = plan

  variables {
    tenants = {
      bad = {
        environment     = "dev"
        lifecycle_state = "active"
        projects = {
          app-0 = {
            services = ["compute.googleapis.com"]
            shared_vpc_service_agent_iam = {
              "roles/compute.networkAdmin" = ["$service_agents:cloudservices"]
            }
          }
        }
      }
    }
  }

  expect_failures = [
    var.tenants,
  ]
}

# 4f. Reject raw principal in shared_vpc_service_agent_iam at plan time.
run "reject_raw_principal_in_shared_vpc_service_agent_iam" {
  command = plan

  variables {
    tenants = {
      bad = {
        environment     = "dev"
        lifecycle_state = "active"
        projects = {
          app-0 = {
            services = ["container.googleapis.com"]
            shared_vpc_service_agent_iam = {
              "roles/container.hostServiceAgentUser" = [
                "group:attacker@example.com",
              ]
            }
          }
        }
      }
    }
  }

  expect_failures = [
    var.tenants,
  ]
}

# 4g. Reject malformed shared_vpc_service_grants entry at plan time.
run "reject_invalid_shared_vpc_service_grants" {
  command = plan

  variables {
    tenants = {
      bad = {
        environment     = "dev"
        lifecycle_state = "active"
        projects = {
          app-0 = {
            shared_vpc_service_grants = ["compute.googleapis.com"]
          }
        }
      }
    }
  }

  expect_failures = [
    var.tenants,
  ]
}

# 4h. Reject invalid lifecycle_state at plan time.
run "reject_invalid_lifecycle_state" {
  command = plan

  variables {
    tenants = {
      bad = {
        environment     = "dev"
        lifecycle_state = "deleted"
        projects = {
          app-0 = {}
        }
      }
    }
  }

  expect_failures = [
    var.tenants,
  ]
}

# 4i. Reject billing_linkage_mode = managed when billing_account is null.
run "reject_managed_billing_with_null_account" {
  command = plan

  variables {
    billing_account      = null
    billing_linkage_mode = "managed"
  }

  expect_failures = [
    var.billing_linkage_mode,
  ]
}

# 4j. Reject unknown environment key not in environment_folders.
run "reject_unknown_environment_key" {
  command = plan

  variables {
    tenants = {
      bad = {
        environment     = "staging"
        lifecycle_state = "active"
        projects = {
          app-0 = {}
        }
      }
    }
  }

  expect_failures = [
    var.tenants,
  ]
}

# 4k. Reject duplicate computed project IDs across tenants/projects.
run "reject_duplicate_computed_project_ids" {
  command = plan

  variables {
    tenants = {
      dup = {
        environment     = "dev"
        lifecycle_state = "active"
        projects = {
          app-0 = {
            name = "dev-acme-app-0"
          }
        }
      }
    }
  }

  expect_failures = [
    terraform_data.tenant_validation,
  ]
}

# 4l. Reject computed project ID with trailing hyphen.
run "reject_project_id_with_trailing_hyphen" {
  command = plan

  variables {
    tenants = {
      bad = {
        environment     = "dev"
        lifecycle_state = "active"
        projects = {
          app-0 = {
            name = "dev-bad-app-"
          }
        }
      }
    }
  }

  expect_failures = [
    terraform_data.tenant_validation,
  ]
}

# 4m. Reject tenant automation when neither tenant nor stage sets project_id.
run "reject_automation_without_project_id" {
  command = plan

  variables {
    automation = {
      outputs_bucket = "test-iac-core-outputs-0"
      project_id     = null
    }
    tenants = {
      bad = {
        environment     = "dev"
        lifecycle_state = "active"
        automation = {
          create_bucket = true
        }
        projects = {
          app-0 = {}
        }
      }
    }
  }

  expect_failures = [
    var.tenants,
  ]
}

# 4n. Reject invalid vpc_sc_perimeter format at plan time.
run "reject_invalid_vpc_sc_perimeter_name" {
  command = plan

  variables {
    tenants = {
      bad = {
        environment     = "dev"
        lifecycle_state = "active"
        projects = {
          app-0 = {
            vpc_sc_perimeter = {
              perimeter_name = "not-a-perimeter-resource-name"
            }
          }
        }
      }
    }
  }

  expect_failures = [
    var.tenants,
  ]
}

# 4o. Reject unknown $service_agents alias before modules/project fallback.
run "reject_unknown_service_agent_alias" {
  command = plan

  variables {
    tenants = {
      bad = {
        environment     = "dev"
        lifecycle_state = "active"
        projects = {
          app-0 = {
            shared_vpc_service_agent_iam = {
              "roles/compute.networkUser" = ["$service_agents:bogus-agent"]
            }
          }
        }
      }
    }
  }

  expect_failures = [
    terraform_data.tenant_validation,
  ]
}

# 5a. Curated Stage 1 GCS manifest read resolves environment folders without
#     accessing core Terraform state buckets.
run "plan_curated_gcs_stage_outputs_read" {
  command = plan

  override_data {
    target = data.google_storage_bucket_object_content.resman_outputs[0]
    values = {
      content = "{\"folder_ids\":{\"envs\":{\"Dev\":\"folders/2001\"}}}"
    }
  }

  variables {
    environment_folders         = {}
    read_stage_outputs_from_gcs = true
  }

  assert {
    condition = (
      local.environment_folders["dev"] == "folders/2001" &&
      local.pf_folders["dev/acme"].parent == "folders/2001"
    )
    error_message = "Expected curated Stage 1 JSON to populate env folders."
  }
}

# 5b. Stage 1 1-resman.auto.tfvars.json folder_ids.envs auto-wires environment
#     folders, with explicit environment_folders taking precedence.
run "plan_stage_1_folder_ids_envs_auto_wiring" {
  command = plan

  variables {
    environment_folders = {
      prod = "folders/399999999999"
    }
    folder_ids = {
      envs = {
        Dev  = "folders/300000000001"
        Prod = "folders/300000000003"
      }
    }
    tenants = {
      beta = {
        environment     = "prod"
        lifecycle_state = "active"
        projects = {
          web-0 = {
            services = ["logging.googleapis.com"]
          }
        }
      }
    }
  }

  assert {
    condition = (
      local.environment_folders["dev"] == "folders/300000000001" &&
      local.environment_folders["prod"] == "folders/399999999999" &&
      local.pf_folders["dev/acme"].parent == "folders/300000000001" &&
      local.pf_folders["prod/beta"].parent == "folders/399999999999"
    )
    error_message = "Expected folder_ids.envs fallback with explicit override."
  }
}
