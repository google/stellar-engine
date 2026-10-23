# Organization Module

This module allows managing several organization properties:

- IAM bindings, both authoritative and additive
- custom IAM roles
- audit logging configuration for services
- organization policies
- organization policy custom constraints

To manage organization policies, the `orgpolicy.googleapis.com` service should be enabled in the quota project.

## TOC

<!-- BEGIN TOC -->
- [TOC](#toc)
- [Example](#example)
- [IAM](#iam)
- [Organization Policies](#organization-policies)
  - [Organization Policy Factory](#organization-policy-factory)
  - [Organization Policy Custom Constraints](#organization-policy-custom-constraints)
  - [Organization Policy Custom Constraints Factory](#organization-policy-custom-constraints-factory)
- [Hierarchical Firewall Policy Attachments](#hierarchical-firewall-policy-attachments)
- [Log Sinks](#log-sinks)
- [Data Access Logs](#data-access-logs)
- [Custom Roles](#custom-roles)
  - [Custom Roles Factory](#custom-roles-factory)
- [Tags](#tags)
- [Files](#files)
- [Variables](#variables)
- [Outputs](#outputs)
<!-- END TOC -->

## Example

```hcl
module "org" {
  source          = "./fabric/modules/organization"
  organization_id = var.organization_id
  iam_by_principals = {
    "group:${var.group_email}" = ["roles/owner"]
  }
  iam = {
    "roles/resourcemanager.projectCreator" = ["group:${var.group_email}"]
  }
  iam_bindings_additive = {
    am1-storage-admin = {
      member = "group:${var.group_email}"
      role   = "roles/storage.admin"
    }
  }
  tags = {
    allowexternal = {
      description = "Allow external identities."
      values = {
        true = {}, false = {}
      }
    }
  }
  org_policies = {
    "compute.disableGuestAttributesAccess" = {
      rules = [{ enforce = true }]
    }
    "compute.skipDefaultNetworkCreation" = {
      rules = [{ enforce = true }]
    }
    "iam.disableServiceAccountKeyCreation" = {
      rules = [{ enforce = true }]
    }
    "iam.disableServiceAccountKeyUpload" = {
      rules = [
        {
          condition = {
            expression  = "resource.matchTagId('tagKeys/1234', 'tagValues/1234')"
            title       = "condition"
            description = "test condition"
            location    = "somewhere"
          }
          enforce = true
        },
        {
          enforce = false
        }
      ]
    }
    "iam.allowedPolicyMemberDomains" = {
      rules = [
        {
          allow = { all = true }
          condition = {
            expression  = "resource.matchTag('1234567890/allowexternal', 'true')"
            title       = "Allow external identities"
            description = "Allow external identities when resource has the `allowexternal` tag set to true."
          }
        },
        {
          allow = { values = ["C0xxxxxxx", "C0yyyyyyy"] }
          condition = {
            expression  = "!resource.matchTag('1234567890/allowexternal', 'true')"
            title       = ""
            description = "For any resource without allowexternal=true, only allow identities from restricted domains."
          }
        }
      ]
    }
    "compute.trustedImageProjects" = {
      rules = [{
        allow = {
          values = ["projects/my-project"]
        }
      }]
    }
    "compute.vmExternalIpAccess" = {
      rules = [{ deny = { all = true } }]
    }
  }
}
# tftest modules=1 resources=13 inventory=basic.yaml e2e serial
```

## IAM

IAM is managed via several variables that implement different features and levels of control:

- `iam` and `iam_by_principals` configure authoritative bindings that manage individual roles exclusively, and are internally merged
- `iam_bindings` configure authoritative bindings with optional support for conditions, and are not internally merged with the previous two variables
- `iam_bindings_additive` configure additive bindings via individual role/member pairs with optional support  conditions

The authoritative and additive approaches can be used together, provided different roles are managed by each. Some care must also be taken with the `iam_by_principals` variable to ensure that variable keys are static values, so that Terraform is able to compute the dependency graph.

Refer to the [project module](../project/README.md#iam) for examples of the IAM interface.

## Organization Policies

### Organization Policy Factory

See the [organization policy factory in the project module](../project#organization-policy-factory).

### Organization Policy Custom Constraints

Refer to the [Creating and managing custom constraints](https://cloud.google.com/resource-manager/docs/organization-policy/creating-managing-custom-constraints) documentation for details on usage.
To manage organization policy custom constraints, the `orgpolicy.googleapis.com` service should be enabled in the quota project.

```hcl
module "org" {
  source          = "./fabric/modules/organization"
  organization_id = var.organization_id
  org_policy_custom_constraints = {
    "custom.gkeEnableAutoUpgrade" = {
      resource_types = ["container.googleapis.com/NodePool"]
      method_types   = ["CREATE"]
      condition      = "resource.management.autoUpgrade == true"
      action_type    = "ALLOW"
      display_name   = "Enable node auto-upgrade"
      description    = "All node pools must have node auto-upgrade enabled."
    }
  }
  # not necessarily to enforce on the org level, policy may be applied on folder/project levels
  org_policies = {
    "custom.gkeEnableAutoUpgrade" = {
      rules = [{ enforce = true }]
    }
  }
}
# tftest modules=1 resources=2 inventory=custom-constraints.yaml
```

You can use the `id` or `custom_constraint_ids` outputs to prevent race conditions between the creation of a custom constraint and an organization policy using that constraint. Both of these outputs depend on the actual constraint, which would make any resource referring to them to wait for the creation of the constraint.

### Organization Policy Custom Constraints Factory

Org policy custom constraints can be loaded from a directory containing YAML files where each file defines one or more custom constraints. The structure of the YAML files is exactly the same as the `org_policy_custom_constraints` variable.

The example below deploys a few org policy custom constraints split between two YAML files.

```hcl
module "org" {
  source          = "./fabric/modules/organization"
  organization_id = var.organization_id
  factories_config = {
    org_policy_custom_constraints = "configs/custom-constraints"
  }
  org_policies = {
    "custom.gkeEnableAutoUpgrade" = {
      rules = [{ enforce = true }]
    }
  }
}
# tftest modules=1 resources=3 files=gke inventory=custom-constraints.yaml
```

```yaml
custom.gkeEnableLogging:
  resource_types:
  - container.googleapis.com/Cluster
  method_types:
  - CREATE
  - UPDATE
  condition: resource.loggingService == "none"
  action_type: DENY
  display_name: Do not disable Cloud Logging
custom.gkeEnableAutoUpgrade:
  resource_types:
  - container.googleapis.com/NodePool
  method_types:
  - CREATE
  condition: resource.management.autoUpgrade == true
  action_type: ALLOW
  display_name: Enable node auto-upgrade
  description: All node pools must have node auto-upgrade enabled.

# tftest-file id=gke path=configs/custom-constraints/gke.yaml
```

```yaml
custom.dataprocNoMoreThan10Workers:
  resource_types:
  - dataproc.googleapis.com/Cluster
  method_types:
  - CREATE
  - UPDATE
  condition: resource.config.workerConfig.numInstances + resource.config.secondaryWorkerConfig.numInstances > 10
  action_type: DENY
  display_name: Total number of worker instances cannot be larger than 10
  description: Cluster cannot have more than 10 workers, including primary and secondary workers.

# tftest-file id=dataproc path=configs/custom-constraints/dataproc.yaml
```

## Hierarchical Firewall Policy Attachments

Hierarchical firewall policies can be managed via the [`net-firewall-policy`](../net-firewall-policy/) module, including support for factories. Once a policy is available, attaching it to the organization can be done either in the firewall policy module itself, or here:

```hcl
module "firewall-policy" {
  source    = "./fabric/modules/net-firewall-policy"
  name      = "test-1"
  parent_id = var.organization_id
  # attachment via the firewall policy module
  # attachments = {
  #   org = var.organization_id
  # }
}

module "org" {
  source          = "./fabric/modules/organization"
  organization_id = var.organization_id
  # attachment via the organization module
  firewall_policy = {
    name   = "test-1"
    policy = module.firewall-policy.id
  }
}
# tftest modules=2 resources=2 e2e serial
```

## Log Sinks

The following example shows how to define organization-level log sinks:

```hcl
module "gcs" {
  source        = "./fabric/modules/gcs"
  project_id    = var.project_id
  prefix        = var.prefix
  name          = "gcs_sink"
  location      = "EU"
  force_destroy = true
}

module "dataset" {
  source     = "./fabric/modules/bigquery-dataset"
  project_id = var.project_id
  id         = "bq_sink"
}

module "pubsub" {
  source     = "./fabric/modules/pubsub"
  project_id = var.project_id
  name       = "pubsub_sink"
}

module "bucket" {
  source      = "./fabric/modules/logging-bucket"
  parent_type = "project"
  parent      = var.project_id
  id          = "${var.prefix}-bucket"
}

module "destination-project" {
  source          = "./fabric/modules/project"
  name            = "dest-prj"
  billing_account = var.billing_account_id
  parent          = var.folder_id
  prefix          = var.prefix
  services = [
    "logging.googleapis.com"
  ]
}

module "org" {
  source          = "./fabric/modules/organization"
  organization_id = var.organization_id

  logging_sinks = {
    warnings = {
      destination = module.gcs.id
      filter      = "severity=WARNING"
      type        = "storage"
    }
    info = {
      bq_partitioned_table = true
      destination          = module.dataset.id
      filter               = "severity=INFO"
      type                 = "bigquery"
    }
    notice = {
      destination = module.pubsub.id
      filter      = "severity=NOTICE"
      type        = "pubsub"
    }
    debug = {
      destination = module.bucket.id
      filter      = "severity=DEBUG"
      exclusions = {
        no-compute = "logName:compute"
      }
      type = "logging"
    }
    alert = {
      destination = module.destination-project.id
      filter      = "severity=ALERT"
      type        = "project"
    }
  }
  logging_exclusions = {
    no-gce-instances = "resource.type=gce_instance"
  }
}
# tftest modules=6 resources=17 inventory=logging.yaml e2e serial
```

## Data Access Logs

Activation of data access logs can be controlled via the `logging_data_access` variable.

```hcl
module "org" {
  source          = "./fabric/modules/organization"
  organization_id = var.organization_id
  logging_data_access = {
    allServices = {
      ADMIN_READ = {
        exempted_members = ["group:${var.group_email}"]
      }
    }
    "storage.googleapis.com" = {
      DATA_READ  = {}
      DATA_WRITE = {}
    }
  }
}
# tftest modules=1 resources=2 inventory=logging-data-access.yaml e2e serial
```

## Custom Roles

Custom roles can be defined via the `custom_roles` variable, and referenced via the `custom_role_id` output (this also provides explicit dependency on the custom role):

```hcl
module "org" {
  source          = "./fabric/modules/organization"
  organization_id = var.organization_id
  custom_roles = {
    "myRole" = [
      "compute.instances.list",
    ]
  }
  iam = {
    (module.org.custom_role_id.myRole) = ["group:${var.group_email}"]
  }
}
# tftest modules=1 resources=2 inventory=roles.yaml e2e serial
```

### Custom Roles Factory

Custom roles can also be specified via a factory in a similar way to organization policies and policy constraints. Each file is mapped to a custom role, where

- the role name defaults to the file name but can be overridden via a `name` attribute in the yaml
- role permissions are defined in an `includedPermissions` map

Custom roles defined via the variable are merged with those coming from the factory, and override them in case of duplicate names.

```hcl
module "org" {
  source          = "./fabric/modules/organization"
  organization_id = var.organization_id
  factories_config = {
    custom_roles = "data/custom_roles"
  }
}
# tftest modules=1 resources=2 files=custom-role-1,custom-role-2 inventory=custom-roles.yaml
```

```yaml
# tftest-file id=custom-role-1 path=data/custom_roles/test_1.yaml

includedPermissions:
 - compute.globalOperations.get
```

```yaml
# tftest-file id=custom-role-2 path=data/custom_roles/test_2.yaml

name: projectViewer
includedPermissions:
  - resourcemanager.projects.get
  - resourcemanager.projects.getIamPolicy
  - resourcemanager.projects.list
```

## Tags

Refer to the [Creating and managing tags](https://cloud.google.com/resource-manager/docs/tags/tags-creating-and-managing) documentation for details on usage.

```hcl
module "org" {
  source          = "./fabric/modules/organization"
  organization_id = var.organization_id
  tags = {
    environment = {
      description = "Environment specification."
      iam = {
        "roles/resourcemanager.tagAdmin" = ["group:${var.group_email}"]
      }
      iam_bindings = {
        viewer = {
          role    = "roles/resourcemanager.tagViewer"
          members = ["group:gcp-support@example.org"]
        }
      }
      iam_bindings_additive = {
        user_app1 = {
          role   = "roles/resourcemanager.tagUser"
          member = "group:app1-team@example.org"
        }
      }
      values = {
        dev = {
          iam_bindings_additive = {
            user_app2 = {
              role   = "roles/resourcemanager.tagUser"
              member = "group:app2-team@example.org"
            }
          }
        }
        prod = {
          description = "Environment: production."
          iam = {
            "roles/resourcemanager.tagViewer" = ["group:app1-team@example.org"]
          }
          iam_bindings = {
            admin = {
              role    = "roles/resourcemanager.tagAdmin"
              members = ["group:gcp-support@example.org"]
              condition = {
                title      = "gcp_support"
                expression = <<-END
                  request.time.getHours("Europe/Berlin") <= 9 &&
                  request.time.getHours("Europe/Berlin") >= 17
                END
              }
            }
          }
        }
      }
    }
  }
  tag_bindings = {
    env-prod = module.org.tag_values["environment/prod"].id
  }
}
# tftest modules=1 resources=10 inventory=tags.yaml
```

You can also define network tags, through a dedicated variable *network_tags*:

```hcl
module "org" {
  source          = "./fabric/modules/organization"
  organization_id = var.organization_id
  network_tags = {
    net-environment = {
      description = "This is a network tag."
      network     = "${var.project_id}/${var.vpc.name}"
      iam = {
        "roles/resourcemanager.tagAdmin" = ["group:${var.group_email}"]
      }
      values = {
        dev = {}
        prod = {
          description = "Environment: production."
          iam = {
            "roles/resourcemanager.tagUser" = ["group:${var.group_email}"]
          }
        }
      }
    }
  }
}
# tftest modules=1 resources=5 inventory=network-tags.yaml e2e serial
```

<!-- TFDOC OPTS files:1 -->
<!-- BEGIN TFDOC -->
## Files

| name | description | resources |
|---|---|---|
| [assets.tf](./assets.tf) | None | <code>google_cloud_asset_organization_feed</code> |
| [context_aware_access.tf](./context_aware_access.tf) | Context-Aware Access resources and factory. | <code>google_access_context_manager_access_level</code> · <code>google_access_context_manager_gcp_user_access_binding</code> |
| [deny-policies.tf](./deny-policies.tf) | IAM Deny policies. | <code>google_iam_deny_policy</code> |
| [iam.tf](./iam.tf) | IAM bindings. | <code>google_organization_iam_binding</code> · <code>google_organization_iam_custom_role</code> · <code>google_organization_iam_member</code> |
| [identity-providers.tf](./identity-providers.tf) | Workforce Identity Federation provider definitions. | <code>google_iam_workforce_pool</code> · <code>google_iam_workforce_pool_provider</code> · <code>google_iam_workforce_pool_provider_scim_tenant</code> |
| [logging.tf](./logging.tf) | Log sinks and data access logs. | <code>google_bigquery_dataset_iam_member</code> · <code>google_logging_organization_exclusion</code> · <code>google_logging_organization_settings</code> · <code>google_logging_organization_sink</code> · <code>google_organization_iam_audit_config</code> · <code>google_project_iam_member</code> · <code>google_pubsub_topic_iam_member</code> · <code>google_storage_bucket_iam_member</code> |
| [main.tf](./main.tf) | Module-level locals and resources. | <code>google_compute_firewall_policy_association</code> · <code>google_essential_contacts_contact</code> |
| [org-policy-custom-constraints.tf](./org-policy-custom-constraints.tf) | None | <code>google_org_policy_custom_constraint</code> |
| [organization-policies.tf](./organization-policies.tf) | Organization-level organization policies. | <code>google_org_policy_policy</code> |
| [outputs.tf](./outputs.tf) | Module outputs. |  |
| [pam.tf](./pam.tf) | None | <code>google_privileged_access_manager_entitlement</code> |
| [scc-mute-configs.tf](./scc-mute-configs.tf) | Organization-level SCC mute configurations. | <code>google_scc_v2_organization_mute_config</code> |
| [scc-sha-custom-modules.tf](./scc-sha-custom-modules.tf) | Organization-level Custom modules with Security Health Analytics. | <code>google_scc_management_organization_security_health_analytics_custom_module</code> |
| [service-agents.tf](./service-agents.tf) | Service agents supporting resources. | <code>google_organization_service_identity</code> |
| [variables-iam.tf](./variables-iam.tf) | None |  |
| [variables-identity-providers.tf](./variables-identity-providers.tf) | None |  |
| [variables-logging.tf](./variables-logging.tf) | None |  |
| [variables-pam.tf](./variables-pam.tf) | None |  |
| [variables-scc.tf](./variables-scc.tf) | None |  |
| [variables.tf](./variables.tf) | Module variables. |  |
| [versions.tf](./versions.tf) | Version pins. |  |

## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [organization_id](variables.tf#L316) | Organization id in organizations/nnnnnn format. | <code>string</code> | ✓ |  |
| [access_levels](variables.tf#L18) | Access level definitions. | <code>map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> |  | <code>&#123;&#125;</code> |
| [access_policy](variables.tf#L118) | Access Policy name or ID, required if creating access levels. | <code>string</code> |  | <code>null</code> |
| [asset_feeds](variables.tf#L124) | Cloud Asset Inventory feeds. | <code>map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> |  | <code>&#123;&#125;</code> |
| [asset_search](variables.tf#L157) | Cloud Asset Inventory search configurations. | <code>map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> |  | <code>&#123;&#125;</code> |
| [contacts](variables.tf#L167) | List of essential contacts for this resource. Must be in the form EMAIL -> [NOTIFICATION_TYPES]. Valid notification types are ALL, SUSPENSION, SECURITY, TECHNICAL, BILLING, LEGAL, PRODUCT_UPDATES. | <code>map&#40;list&#40;string&#41;&#41;</code> |  | <code>&#123;&#125;</code> |
| [context](variables.tf#L185) | Context-specific interpolations. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>&#123;&#125;</code> |
| [context_aware_access_bindings](variables.tf#L211) | GCP User Access Bindings for securing Console and APIs. | <code>map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> |  | <code>&#123;&#125;</code> |
| [custom_roles](variables.tf#L229) | Map of role name => role attributes to create in this organization. | <code>map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> |  | <code>&#123;&#125;</code> |
| [factories_config](variables.tf#L250) | Paths to data files and folders that enable factory functionality. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>&#123;&#125;</code> |
| [firewall_policy](variables.tf#L265) | Hierarchical firewall policies to associate to the organization. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>null</code> |
| [iam](variables-iam.tf#L17) | Authoritative IAM bindings in {ROLE => [MEMBERS]} format. | <code>map&#40;list&#40;string&#41;&#41;</code> |  | <code>&#123;&#125;</code> |
| [iam_bindings](variables-iam.tf#L24) | Authoritative IAM bindings in {KEY => {role = ROLE, members = [], condition = {}}}. Keys are arbitrary. | <code>map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> |  | <code>&#123;&#125;</code> |
| [iam_bindings_additive](variables-iam.tf#L39) | Individual additive IAM bindings. Keys are arbitrary. | <code>map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> |  | <code>&#123;&#125;</code> |
| [iam_by_principals](variables-iam.tf#L61) | Authoritative IAM binding in {PRINCIPAL => [ROLES]} format. Principals need to be statically defined to avoid errors. Merged internally with the `iam` variable. | <code>map&#40;list&#40;string&#41;&#41;</code> |  | <code>&#123;&#125;</code> |
| [iam_by_principals_additive](variables-iam.tf#L54) | Additive IAM binding in {PRINCIPAL => [ROLES]} format. Principals need to be statically defined to avoid errors. Merged internally with the `iam_bindings_additive` variable. | <code>map&#40;list&#40;string&#41;&#41;</code> |  | <code>&#123;&#125;</code> |
| [iam_by_principals_conditional](variables-iam.tf#L68) | Authoritative IAM binding in {PRINCIPAL => {roles = [roles], condition = {cond}}} format. Principals need to be statically defined to avoid errors. Condition is required. | <code>map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> |  | <code>&#123;&#125;</code> |
| [iam_deny_policies](variables-iam.tf#L98) | IAM Deny policies to be applied to the organization. | <code>map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> |  | <code>&#123;&#125;</code> |
| [logging_data_access](variables-logging.tf#L17) | Control activation of data access logs. The special 'allServices' key denotes configuration for all services. | <code>map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> |  | <code>&#123;&#125;</code> |
| [logging_exclusions](variables-logging.tf#L28) | Logging exclusions for this organization in the form {NAME -> FILTER}. | <code>map&#40;string&#41;</code> |  | <code>&#123;&#125;</code> |
| [logging_settings](variables-logging.tf#L35) | Default settings for logging resources. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>null</code> |
| [logging_sinks](variables-logging.tf#L45) | Logging sinks to create for the organization. | <code>map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> |  | <code>&#123;&#125;</code> |
| [org_policies](variables.tf#L274) | Organization policies applied to this organization keyed by policy name. | <code>map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> |  | <code>&#123;&#125;</code> |
| [org_policy_custom_constraints](variables.tf#L302) | Organization policy custom constraints keyed by constraint name. | <code>map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> |  | <code>&#123;&#125;</code> |
| [pam_entitlements](variables-pam.tf#L17) | Privileged Access Manager entitlements for this resource, keyed by entitlement ID. | <code>map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> |  | <code>&#123;&#125;</code> |
| [prefix](variables.tf#L325) | Prefix to avoid conflicts with redeploying custom organization policies. | <code>string</code> |  | <code>&#34;&#34;</code> |
| [scc_mute_configs](variables-scc.tf#L17) | SCC mute configurations keyed by name. | <code>map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> |  | <code>&#123;&#125;</code> |
| [scc_sha_custom_modules](variables-scc.tf#L28) | SCC custom modules keyed by module name. | <code>map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> |  | <code>&#123;&#125;</code> |
| [service_agents_config](variables.tf#L332) | Service agents configuration. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>&#123;&#125;</code> |
| [workforce_identity_pools](variables-identity-providers.tf#L17) | Workforce Identity Federation pools and providers. | <code>map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> |  | <code>&#123;&#125;</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [access_levels](outputs.tf#L17) | Access level resources. |  |
| [asset_search_results](outputs.tf#L22) | Cloud Asset Inventory search results. |  |
| [context_aware_access_bindings](outputs.tf#L29) | GCP User Access Bindings for securing Console and APIs. |  |
| [custom_constraint_ids](outputs.tf#L37) | Map of CUSTOM_CONSTRAINTS => ID in the organization. |  |
| [custom_role_id](outputs.tf#L42) | Map of custom role IDs created in the organization. |  |
| [custom_roles](outputs.tf#L47) | Map of custom roles resources created in the organization. |  |
| [id](outputs.tf#L52) | Fully qualified organization id. |  |
| [logging_identities](outputs.tf#L66) | Principals used for logging sinks. |  |
| [logging_sinks](outputs.tf#L78) | Logging sink resources. |  |
| [organization_id](outputs.tf#L88) | Organization id dependent on module resources. |  |
| [organization_policies_ids](outputs.tf#L101) | Map of ORGANIZATION_POLICIES => ID in the organization. |  |
| [scc_custom_sha_modules_ids](outputs.tf#L106) | Map of SCC CUSTOM SHA MODULES => ID in the organization. |  |
| [scc_mute_configs](outputs.tf#L111) | SCC mute configurations. |  |
| [scim_tenants](outputs.tf#L116) | Workforce Identity provider SCIM tenants. |  |
| [service_agents](outputs.tf#L130) | Identities of all organization-level service agents. |  |
| [sink_writer_identities](outputs.tf#L138) | Writer identities created for each sink. |  |
| [workforce_identity_pool_ids](outputs.tf#L146) | Workforce identity pool ids. |  |
| [workforce_identity_provider_names](outputs.tf#L153) | Workforce Identity provider names. |  |
| [workforce_identity_providers](outputs.tf#L160) | Workforce Identity provider attributes. |  |
<!-- END TFDOC -->
