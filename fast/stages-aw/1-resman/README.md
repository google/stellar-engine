# Resource hierarchy

Stage 1 provisions environment folders (`Int`, `Test`, and `Prod`), tenant projects, and the `Networking` and `Security` folders consumed by downstream stages. Unlike upstream Cloud Foundation Fabric, every folder and project resides beneath the Stage 0 Assured Workloads folder to keep all workloads and audit logs inside the compliance boundary.

<!-- BEGIN TOC -->
- [1 Design overview](#1-design-overview)
- [2 Stage deployment](#2-stage-deployment)
  - [Service account impersonation](#service-account-impersonation)
  - [Lightweight multitenancy](#lightweight-multitenancy)
  - [Team folders](#team-folders)
  - [IAM bindings](#iam-bindings)
  - [Additional folders](#additional-folders)
- [Variables](#variables)
- [Outputs](#outputs)
<!-- END TOC -->

## 1 Design overview

Placing the entire resource hierarchy inside the Assured Workloads folder ensures every tenant project, host network, and log sink inherits regional data residency and compliance guardrails automatically.

## 2 Stage deployment

Follow the [Detailed Deployment Guide](/docs/ddg.md) for prerequisites and step-by-step deployment commands.

### Service account impersonation

The generated provider configuration impersonates the Stage 1 automation service account. Ensure your active user identity belongs to `gcp-devops` or `gcp-organization-admins`, both of which receive impersonation permissions in Stage 0.

### Lightweight multitenancy

When your organization requires tenant isolation without separate per-tenant FAST pipelines, define lightweight tenants in the `tenants` variable and shared tenant IAM settings in the `tenants_config` variable.

This configuration creates one `Project <tenant> <env>` folder directly under each configured `<Regime> <Env>` environment folder beneath the Assured Workloads folder, with a centrally managed core automation account and state bucket in the Stage 0 automation project and tenant-managed IaC and main projects inside each tenant folder. Downstream stages can provision centralized networking for each tenant while tenant administrators manage their own application projects.

Stage 1 binds default IAM roles across three scopes for each `(env, tenant)` pair:

- Top-level tenant folder (`Project <tenant> <env>`) bindings:
  - `roles/cloudasset.owner`, `roles/compute.xpnAdmin`, `roles/logging.admin`, `roles/owner`, `roles/resourcemanager.folderAdmin`, `roles/resourcemanager.projectCreator`, and `roles/resourcemanager.tagUser` for the core tenant service account (`<prefix>-tn-<env>-<tenant>-prod-0`, which also receives `roles/serviceusage.serviceUsageConsumer` on the Stage 0 automation project and `roles/storage.objectAdmin` on `<prefix>-tn-<env>-<tenant>-0` and `<prefix>-<env>-<tenant>-iac-outputs-0`)
  - `roles/viewer` (plus any custom folder roles in `tenants_config`) for the tenant admin principal and tenant IaC service account (`<prefix>-<env>-<tenant>-iac-0`, which also receives `roles/storage.admin` on `<prefix>-<env>-<tenant>-iac-outputs-0` and `<prefix>-<env>-<tenant>-iac-0`)
  - `roles/browser` for the tenant admin principal unless `tenants_config` grants `roles/browser`
- Tenant IaC core project (`<prefix>-<env>-<tenant>-iac-core-0`) direct bindings (plus `roles/owner` inherited from the parent folder by `<prefix>-tn-<env>-<tenant>-prod-0`):
  - `roles/owner` for the Stage 1 automation service account (`var.automation.service_accounts.resman`)
  - `local.custom_roles.storage_viewer` and `roles/viewer` for the Stage 1 read-only automation service account (`var.automation.service_accounts.resman-r`)
  - `roles/iam.serviceAccountAdmin`, `roles/iam.serviceAccountTokenCreator`, and `roles/iam.workloadIdentityPoolAdmin` for the tenant admin principal
- Tenant main workload project (`<prefix>-<env>-<tenant>-main-0`) direct bindings (plus `roles/owner` inherited from the parent folder by `<prefix>-tn-<env>-<tenant>-prod-0`):
  - `roles/owner` for the Stage 1 automation service account (`var.automation.service_accounts.resman`)
  - `local.custom_roles.storage_viewer` and `roles/viewer` for the Stage 1 read-only automation service account (`var.automation.service_accounts.resman-r`)
  - `roles/iam.serviceAccountAdmin`, `roles/iam.serviceAccountTokenCreator`, and `roles/iam.workloadIdentityPoolAdmin` for the tenant admin principal

Customize the folder role grants through the `tenants_config` variable.

```mermaid
%%{init: {'theme':'base'}}%%
classDiagram
    Assured_Workloads~📁~ -- Environments_Env~📁~
    Assured_Workloads~📁~ -- org_iac
    Environments_Env~📁~ -- Tenant_0_folder~📁~
    Environments_Env~📁~ -- Tenant_1_folder~📁~
    Tenant_0_folder~📁~ -- tenant0_iac_core
    Tenant_0_folder~📁~ -- tenant0_main
    Tenant_1_folder~📁~ -- tenant1_iac_core
    Tenant_1_folder~📁~ -- tenant1_main
    class Assured_Workloads~📁~["Assured Workloads folder"] {
    }
    class org_iac["org_iac (from stage 0)"] {
        - GCS buckets (core tenant states)
        - service accounts (prefix-tn-env-tenant-prod-0)
    }
    class Environments_Env~📁~["<Regime> <Env>"] {
        - IAM bindings()
    }
    class Tenant_0_folder~📁~["Project <ten1> <Env>"] {
        - IAM bindings()
    }
    class tenant0_iac_core["<prefix>-<env>-<ten1>-iac-core-0"] {
        - GCS state and output buckets
        - <prefix>-<env>-<ten1>-iac-0 SA
        - IAM bindings()
    }
    class tenant0_main["<prefix>-<env>-<ten1>-main-0"] {
        - IAM bindings()
    }
    class Tenant_1_folder~📁~["Project <ten2> <Env>"] {
        - IAM bindings()
    }
    class tenant1_iac_core["<prefix>-<env>-<ten2>-iac-core-0"] {
        - GCS state and output buckets
        - <prefix>-<env>-<ten2>-iac-0 SA
        - IAM bindings()
    }
    class tenant1_main["<prefix>-<env>-<ten2>-main-0"] {
        - IAM bindings()
    }
```

Tenant keys must be shorter than 7 characters (`length(k) < 7`, such as `alpha` or `ten1`). The following example configures two tenants named `alpha` and `beta`, generating dedicated provider and `.tfvars` files for each tenant:

```tfvars
tenants = {
  alpha = {
    admin_principal  = "group:team-alpha-admins@example.com"
    descriptive_name = "Alpha Workload Group"
    locations = {
      gcs = "us-east4"
      kms = "us-east4" # Must match gcs region for tenant GCS CMEK
    }
  }
  beta = {
    admin_principal  = "group:team-beta-admins@example.com"
    descriptive_name = "Beta Analytics Group"
    locations = {
      gcs = "us-west1"
      kms = "us-west1" # Must match gcs region for tenant GCS CMEK
    }
  }
}
```

### Team folders

Enable `fast_features.teams = true` and set `team_folders` to group workloads by application or business unit under a `Teams` folder branch with dedicated automation service accounts and IAM bindings. Each entry requires `descriptive_name`, `iam_by_principals`, and `impersonation_principals`:

```tfvars
fast_features = {
  envs  = true
  teams = true
}

team_folders = {
  alpha = {
    descriptive_name = "Alpha Workload Group"
    iam_by_principals = {
      "group:team-alpha@example.com" = [
        "roles/viewer"
      ]
    }
    impersonation_principals = ["group:team-alpha-admins@example.com"]
  }
  beta = {
    descriptive_name = "Beta Analytics Group"
    iam_by_principals = {
      "group:team-beta@example.com" = [
        "roles/viewer"
      ]
    }
    impersonation_principals = ["group:team-beta-admins@example.com"]
  }
}
```

Applying this configuration provisions the team resources required to delegate folder management to a CI/CD pipeline or team administrator group:

- Team folders (`Alpha Workload Group` and `Beta Analytics Group`, each with `Development` and `Production` subfolders) under the `Teams` folder with `roles/viewer` bound to each team's configured group.
- CMEK-encrypted Cloud Storage state buckets in the automation project that satisfy IL5 encryption requirements.
- Per-team automation service accounts in the automation project with folder and bucket IAM bindings and group impersonation policies.

### IAM bindings

Use `folder_iam.envs` to manage environment folder IAM bindings; the optional `admin` attribute in `envs_folders` is unused and kept only for compatibility. Use the `folder_iam` variable to manage authoritative IAM bindings on top-level folders. For finer-grained adjustments, edit the `iam`, `iam_bindings`, and `iam_bindings_additive` module inputs in the corresponding `branch-*.tf` file following the human-versus-machine principal pattern documented in the [Stage 0 customizations](../0-bootstrap/README.md#3-customizations) section.

See [IAM.md](./IAM.md) for the full list of IAM roles managed by this stage.

### Additional folders

Clone an existing `branch-*.tf` file and update its module names and folder identifiers to add a new top-level hierarchy branch, such as shared GKE clusters.
<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [alert_email](variables.tf#L19) | Email to receive log alerts. | <code>string</code> | ✓ |  |
| [automation](variables.tf#L35) | Automation resources created by the bootstrap stage. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> | ✓ |  |
| [billing_account](variables.tf#L61) | Billing account id. If billing account is not part of the same org set `is_org_level` to `false`. To disable handling of billing IAM roles set `no_iam` to `true`. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> | ✓ |  |
| [common_services_folder](variables.tf#L175) | Common services folder where non-tenant related resources should be kept. | <code>string</code> | ✓ |  |
| [envs_folders](variables.tf#L208) | List of environments to be created for projects to go into. The optional admin attribute is unused and kept for compatibility; manage environment folder IAM via folder_iam.envs. | <code>map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> | ✓ |  |
| [organization](variables.tf#L287) | Organization details. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> | ✓ |  |
| [prefix](variables.tf#L303) | Prefix used for resources that need unique names. Use 7 characters or less. | <code>string</code> | ✓ |  |
| [regime_mapping](variables.tf#L314) | Mapping of compliance regime names to short codes. | <code>map&#40;string&#41;</code> | ✓ |  |
| [regions](variables.tf#L319) | Region definitions. Inherited from 0-bootstrap outputs. Must be specified in bootstrap terraform.tfvars. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> | ✓ |  |
| [assured_workloads](variables.tf#L24) | Configuration for Assured Workloads. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>&#123;&#125;</code> |
| [billing_override](variables.tf#L72) | Optional billing override configuration. If set, disables service account impersonation for project billing linkage and runs under the user account using the specified quota projects. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>null</code> |
| [cicd_repositories](variables.tf#L81) | CI/CD repository configuration. Identity providers reference keys in the `automation.federated_identity_providers` variable. Set to null to disable, or set individual repositories to null if not needed. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>null</code> |
| [custom_roles](variables.tf#L180) | Custom roles defined at the org level, in key => id format. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>null</code> |
| [deploy_org_resources](variables.tf#L192) | Granular control over the deployment of organization-level resources. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>&#123;&#125;</code> |
| [factories_config](variables.tf#L215) | Configuration for the resource factories or external data. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>&#123;&#125;</code> |
| [fast_features](variables.tf#L225) | Selective control for top-level FAST features. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>&#123;&#125;</code> |
| [folder_iam](variables.tf#L241) | Authoritative IAM for top-level folders. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>&#123;&#125;</code> |
| [force_destroy](variables.tf#L258) | Toggles force_destroy for GCS buckets. | <code>bool</code> |  | <code>false</code> |
| [groups](variables.tf#L264) | Group names or IAM-format principals to grant organization-level permissions. If just the name is provided, the 'group:' principal and organization domain are interpolated. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>&#123;&#125;</code> |
| [kms_protection_level](variables.tf#L279) | KMS protection level. | <code>string</code> |  | <code>null</code> |
| [outputs_location](variables.tf#L297) | Enable writing provider, tfvars and CI/CD workflow files to local filesystem. Leave null to disable. | <code>string</code> |  | <code>null</code> |
| [team_folders](variables.tf#L328) | Team folders to be created. Format is described in a code comment. | <code>map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> |  | <code>null</code> |
| [tenants](variables.tf#L344) | Lightweight tenant definitions. | <code>map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> |  | <code>&#123;&#125;</code> |
| [tenants_config](variables.tf#L373) | Lightweight tenants shared configuration. Roles will be assigned to tenant admin group and service accounts. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>&#123;&#125;</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [cicd_repositories](outputs.tf#L396) | WIF configuration for CI/CD repositories. |  |
| [dataplatform](outputs.tf#L410) | Data for the Data Platform stage. |  |
| [envs](outputs.tf#L426) | Environments folders created for the tenants. |  |
| [gcve](outputs.tf#L431) | Data for the GCVE stage. |  |
| [gke_multitenant](outputs.tf#L452) | Data for the GKE multitenant stage. |  |
| [networking](outputs.tf#L473) | Data for the networking stage. |  |
| [project_factories](outputs.tf#L482) | Data for the project factories stage. |  |
| [providers](outputs.tf#L497) | Terraform provider files for this stage and dependent stages. | ✓ |
| [sandbox](outputs.tf#L504) | Data for the sandbox stage. |  |
| [security](outputs.tf#L518) | Data for the security stage. |  |
| [team_cicd_repositories](outputs.tf#L528) | WIF configuration for Team CI/CD repositories. |  |
| [teams](outputs.tf#L542) | Data for the teams stage. |  |
| [tfvars](outputs.tf#L554) | Terraform variable files for the following stages. | ✓ |
<!-- END TFDOC -->
