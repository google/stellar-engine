# Google Cloud organization bootstrap

Stage 0 enables organization-level Google Cloud capabilities that require broad administrative permissions, provisions automation prerequisites for downstream stages, and establishes the Assured Workloads compliance boundary for the landing zone.

<!-- BEGIN TOC -->
- [1 Design overview](#1-design-overview)
  - [Assured Workloads](#assured-workloads)
  - [User groups](#user-groups)
  - [Organization IAM](#organization-iam)
  - [Organization policy tags](#organization-policy-tags)
  - [Automation project](#automation-project)
  - [Billing account](#billing-account)
    - [Billing budgets](#billing-budgets)
  - [Organization logging](#organization-logging)
  - [Resource naming](#resource-naming)
  - [Workforce Identity Federation](#workforce-identity-federation)
  - [Workload Identity Federation](#workload-identity-federation)
- [2 Stage deployment](#2-stage-deployment)
- [3 Customizations](#3-customizations)
  - [Group names](#group-names)
  - [IAM bindings](#iam-bindings)
  - [Log sinks](#log-sinks)
  - [Naming convention](#naming-convention)
  - [Pre-created resources](#pre-created-resources)
  - [Federated identity providers](#federated-identity-providers)
  - [CI/CD repositories](#cicd-repositories)
  - [Feature toggles](#feature-toggles)
  - [Organization-level resources](#organization-level-resources)
- [Variables](#variables)
- [Outputs](#outputs)
<!-- END TOC -->

## 1 Design overview

Stage 0 bootstraps Assured Workloads, automation projects, service accounts, and foundational audit and billing exports before downstream stages deploy network, resource hierarchy, and security controls.

### Assured Workloads

Stage 0 provisions the top-level [Assured Workloads](https://cloud.google.com/security/products/assured-workloads) folder so every downstream folder, project, and workload stays within the selected compliance regime.

### User groups

User groups decouple human operational permissions from the stages where individual resources are created. For example, the networking group receives organization-level roles such as Shared VPC Admin and Cloud Asset Viewer in Stage 0 and folder-level roles in Stage 1.

Stage 0 standardizes the initial group keys on the [Google Cloud Enterprise Setup Checklist](https://cloud.google.com/docs/enterprise/setup-checklist) to simplify adoption. You can map custom group names or add groups as described in [Customizations](#3-customizations).

### Organization IAM

The [Stage 1 resource management](../1-resman) service account grants targeted organization-level permissions required by downstream network, security, and billing workflows.

To avoid granting full Organization Admin privileges, Stage 0 defines a custom role scoped to setting organization IAM policies and binds it through a [delegated role grant](https://cloud.google.com/iam/docs/setting-limits-on-granting-roles) limited to an explicit allowlist of roles. Because both Stage 0 and Stage 1 manage bindings for those delegated roles, Stage 0 configures them as additive bindings so neither stage overwrites the other during `terraform apply`.

See [IAM.md](./IAM.md) for the full list of IAM roles managed by this stage.

### Organization policy tags

Deploying organization policies during Stage 0 enforces location restrictions, default network removal, and IAM guardrails before downstream projects exist.

Stage 0 manages organization policy exceptions through a dedicated tag hierarchy rooted at the `org-policies` tag key. A built-in condition on `iam.allowedPolicyMemberDomains` relaxes domain restrictions on resources that bind or inherit the `org-policies/allowed-policy-member-domains-all` tag value.

- Define additional tag values and `tagUser` IAM bindings through the `org_policies_config.tag_values` variable.
- Stage 0 exports managed tag keys and values into `0-bootstrap.auto.tfvars` so downstream stages can reference their IDs.
- Stage 1 manages the remaining resource hierarchy tags alongside the folder structure.

The following example defines a custom tag value under `org-policies` via `org_policies_config` and grants `roles/resourcemanager.tagUser` to a group:

```hcl
# stage 0 custom tfvars
org_policies_config = {
  tag_values = {
    compute-require-oslogin-false = {
      description = "Bind this tag to set oslogin to false."
      iam = {
        "roles/resourcemanager.tagUser" = [
          "group:foo@example.com"
        ]
      }
    }
  }
}
```

Reference that tag value inside a constraint condition in `data/org-policies/compute.yaml` or another policy factory file using your numeric organization ID and tag key name:

```yaml
compute.requireOsLogin:
  rules:
  - enforce: true
  - enforce: false
    condition:
      expression: resource.matchTag('12345678/org-policies-config', 'compute-require-oslogin-false')
```

### Automation project

Stage 0 uses a single automation Google Cloud project across all foundational stages. Consolidating API quota usage and service activation into one project simplifies operations while preserving separation through resource-level IAM on state buckets and service accounts.

### Billing account

Stage 0 supports three billing account models:

- When the billing account belongs to the same Google Cloud organization, Stage 0 manages billing IAM bindings at the organization level using a custom role and delegated role grant.
- When the billing account belongs to an external organization or stands alone, Stage 0 sets billing IAM bindings directly on the billing account.
- When billing IAM is managed outside Terraform (`no_iam = true`), Terraform skips billing IAM bindings for development environments that require manual billing linkage.

See [Stage deployment](#2-stage-deployment) for prerequisites and setup steps.

Because Cloud Billing export to BigQuery is not configurable via API, enable export to the Stage 0 `billing_export` BigQuery dataset manually in the Cloud Console by following the [BigQuery billing export guide](https://cloud.google.com/billing/docs/how-to/export-data-bigquery-setup#enable-bq-export).

#### Billing budgets

Set the `billing_budget_amount` variable to create a default billing budget covering all projects under the Assured Workloads folder or fallback root folder. The object variable accepts the budget amount and optional alert threshold rules, which default to `0.5`, `0.75`, and `0.9`.

### Organization logging

Stage 0 creates organization-level log sinks during bootstrap so audit trails are active before downstream resources deploy. Default log filters route [Cloud Audit Logs](https://cloud.google.com/logging/docs/audit), [VPC Service Controls violations](https://cloud.google.com/vpc-service-controls/docs/troubleshooting#vpc-sc-errors), and [Google Workspace logs](https://cloud.google.com/logging/docs/audit/configure-gsuite-audit-logs) into Cloud Logging buckets in the top-level audit logging project, alongside an unfiltered sink for [CIS Benchmark](https://cloud.google.com/security/compliance/cis) compliance.

See [Log sinks](#log-sinks) to customize log filters or export destinations.

### Resource naming

Stage 0 uses deterministic resource naming rather than random prefixes or suffixes so production deployments follow a predictable naming convention.

Globally unique resources such as Google Cloud projects and Cloud Storage buckets combine five hyphen-separated tokens ordered by scope:

- Static organization prefix up to 7 characters in `prefix`, such as `myco`
- Environment identifier, such as `prod`
- Team or owner identifier, such as `sec`
- Context identifier, such as `core` or `kms`
- Instance sequence identifier, such as `0` or `1`

Joining tokens with `-` keeps resource names readable and enables automated cost attribution in BigQuery billing exports. Project-scoped resources use shorter names because their parent project provides the organization and environment context.

See [Naming convention](#naming-convention) for token customization options.

### Workforce Identity Federation

Stage 0 supports [Workforce Identity Federation](https://cloud.google.com/iam/docs/workforce-identity-federation) so external identity providers can authenticate and authorize workforce users through IAM.

The following example configures an organization-level Workforce Identity pool:

```hcl
# stage 0 wif tfvars
workforce_identity_pool = {
  display_name     = "Bootstrap workforce pool"
  description      = "Workforce Identity pool"
  disabled         = false
  session_duration = "3600s"
}
```

### Workload Identity Federation

Stage 0 optionally configures two related automation capabilities when their variables are populated:

- [Workload Identity Federation](https://cloud.google.com/iam/docs/workload-identity-federation) pools and OIDC providers exported to downstream stages for IAM bindings and service account impersonation.
- CI/CD repository bindings and generated workflow templates for GitHub, GitLab, and Cloud Build.

See [Federated identity providers](#federated-identity-providers) and [CI/CD repositories](#cicd-repositories) for configuration details.

## 2 Stage deployment

Follow the [Detailed Deployment Guide](/docs/ddg.md) for prerequisites, bootstrap permissions, and step-by-step deployment commands.

## 3 Customizations

Most required variables such as `billing_account` and `organization` supply environment identifiers directly. Use the variables below to customize group mappings, IAM bindings, log exports, naming, and CI/CD integration.

### Group names

The `groups` variable maps logical group keys from the [Google Cloud Enterprise Setup Checklist](https://cloud.google.com/docs/enterprise/setup-checklist) to your organization's group local-parts so you can customize group addresses without modifying module code.

For example, to map the network administrator group to `net-rockstars@example.com`, specify the group name without the domain, which Terraform appends from `organization.domain`:

```hcl
variable "groups" {
  description = "Group names to grant organization-level permissions."
  type        = map(string)
  default = {
    gcp-vpc-network-admins = "net-rockstars"
    # [...]
  }
}
```

If your group structure differs from the checklist layout, define your group keys in `groups` and update the role mappings in `organization-iam.tf`.

### IAM bindings

All FAST stages separate human and machine principals across module IAM inputs:

- Human operational roles bind to groups through `iam_groups` variables.
- Automation roles bind to service accounts through `iam` variables.

Stage 0 also distinguishes between authoritative and additive IAM bindings:

- Authoritative bindings manage the complete principal list for a role and prevent configuration drift when a single Terraform stage owns that role.
- Additive bindings manage individual role-and-principal pairs and prevent conflicts when multiple stages grant the same role, such as `roles/compute.networkUser` on Shared VPCs.

All default organization IAM bindings live in [organization-iam.tf](./organization-iam.tf). Use three stage variables to inject custom organization-level bindings:

- Set `group_iam` to add authoritative role bindings for groups.
- Set `iam` to add authoritative role bindings for any principal type, merged with internal `iam` locals and group bindings.
- Set `iam_bindings_additive` to add individual role-and-principal pairs with optional IAM conditions.

See the [project module](../../../modules/project/) documentation for examples of this shared IAM variable interface.

### Log sinks

Customize organization-level log exports through the `log_sinks` variable to add sinks with custom filters or route logs to Cloud Logging buckets, BigQuery datasets, Cloud Storage buckets, or Pub/Sub topics.

See [Scenarios for exporting Cloud Logging data](https://cloud.google.com/architecture/exporting-stackdriver-logging-for-security-and-access-analytics) for filter examples.

### Naming convention

Customize resource naming tokens according to scope:

- Set the organization prefix once through the `prefix` variable.
- Change the default `prod` environment token in `main.tf` `locals` if required.
- Edit resource-specific context tokens directly in module `name` attributes while keeping internal Terraform module labels unchanged to preserve state addresses and references.

### Pre-created resources

Import Stage 0 projects and the Assured Workloads workload when an administrator provisions them ahead of time, such as when only a human principal holds billing linkage permissions.

- The workload resource ignores changes to `billing_account` and `resource_settings` because the Assured Workloads API does not return those fields on read.
- Pre-create the workload with the billing account, regime, and location matching `google_assured_workloads_workload.primary`.
- Configure a `CONSUMER_FOLDER` resource setting named `StellarEngine-<prefix>` and enable violation notifications on the workload.
- Import the workload into `google_assured_workloads_workload.primary[0]` using `organizations/<organization_id>/locations/<location>/workloads/<workload_id>`.
- Import pre-created projects into `module.automation-project.google_project.project[0]` and `module.log-export-project.google_project.project[0]` using their project IDs.
- Run `terraform plan` after each import and halt if Terraform proposes replacing an imported resource.

Set `project_deletion_policies` to retain pre-created projects during `terraform destroy`:

- Valid map keys `automation`, `billing`, and `logging` match `project_parent_ids` and default to `DELETE`.
- Setting `ABANDON` removes the project from Terraform state on destroy while still deleting stage-managed resources and liens inside the project.
- Setting `PREVENT` blocks any Terraform destroy plan that targets the project.

```hcl
project_deletion_policies = {
  automation = "ABANDON"
  logging    = "ABANDON"
}
```

### Federated identity providers

Configure a Workload Identity Federation pool and OIDC providers at any point in Stage 0 through `federated_identity_providers`. Stage 0 exports configured provider names in generated `.auto.tfvars.json` files for Stage 1 and `cicd_repositories`.

The `workload-identity.tf` file includes built-in issuer definitions for GitHub and GitLab, and you can extend it to support additional OIDC providers. For self-hosted GitHub Enterprise or GitLab instances used with `cicd_repositories`, keep `issuer` set to `"github"` or `"gitlab"` so both Stage 0 and Stage 1 inherit the default attribute mappings and principal templates, and configure `custom_settings`:

- Set `issuer_uri` to override the public platform issuer URL.
- Set `audiences` to override the default [Workload Identity Federation provider audience](https://cloud.google.com/iam/docs/best-practices-for-using-workload-identity-federation#provider-audience).
- Set `jwks_json` to upload custom signing keys.
- Set `attribute_condition` on multi-tenant providers such as public GitHub or GitLab to restrict authentication to your organization or namespace and exclude `pull_request_target` workflows where applicable.

```tfvars
federated_identity_providers = {
  # Use the public GitHub and specify an attribute condition
  github-public-sample = {
    attribute_condition = "attribute.repository_owner==\"my-github-org\""
    issuer              = "github"
  }
  # Use a private instance of Gitlab and specify a custom issuer_uri
  gitlab-private-sample = {
    issuer              = "gitlab"
    custom_settings     = {
      issuer_uri = "https://gitlab.fast.example.com"
    }
  }
  # Use a private instance of Gitlab.
  # Specify a custom audience and a custom issuer_uri
  gitlab-private-aud-sample = {
    attribute_condition = "attribute.namespace_path==\"my-gitlab-org\""
    issuer              = "gitlab"
    custom_settings = {
      audiences = ["https://gitlab.fast.example.com"]
      issuer_uri        = "https://gitlab.fast.example.com"
    }
  }
}
```

### CI/CD repositories

Configure external CI/CD repository impersonation and workflow generation through the optional `cicd_repositories` variable. The multi-repository layout uses one central repository for shared Terraform modules and one repository per stage:

```tfvars
cicd_repositories = {
  bootstrap = {
    branch            = "main"
    identity_provider = "github-public-sample"
    name              = "my-gh-org/fast-bootstrap"
    type              = "github"
  }
  resman = {
    branch            = "main"
    identity_provider = "github-public-sample"
    name              = "my-gh-org/fast-resman"
    type              = "github"
  }
}
```

Set `type` to `github`, `gitlab`, or `sourcerepo`. For external repositories, `branch` scopes Workload Identity Federation impersonation of the `-1` apply service account to that branch; leaving `branch` set to `null` grants no Workload Identity Federation binding on the apply service account while still allowing pull-request plans through the `-1r` read-only account. Applying Stage 0 writes pre-configured workflow files that authenticate via Workload Identity Federation using a dedicated CI/CD service account per repository.

Complete the repository setup manually after `terraform apply`:

- Create a central modules repository populated with the repository `modules/` directory and configure read access for CI/CD runners:
  - On GitHub, generate an SSH key pair, register the public key as a [deploy key](https://docs.github.com/en/developers/overview/managing-deploy-keys#deploy-keys) on the modules repository, and store the private key in a `CICD_MODULES_KEY` secret in each stage repository.
  - On GitLab, Base64-encode the SSH private key before storing it in `CICD_MODULES_KEY` so runner log masking applies.
  - On Cloud Source Repositories, grant `roles/source.reader` to each CI/CD service account.
- Create one repository per stage populated with that stage's Terraform files and rewrite relative module `source` paths (`source\s*= "../../../modules/([^"]+)"`) to reference your versioned modules repository:
  - For GitHub, use `source = "git@github.com:my-org/fast-modules.git//$1?ref=v1.0"`.
  - For GitLab, use `source = "git::ssh://git@gitlab.com/my-org/fast-modules.git//$1?ref=v1.0"`.
  - For Cloud Source Repositories, use `source = "git::https://source.developers.google.com/p/my-project/r/my-repository//$1?ref=v1.0"` after configuring the `gcloud.sh` credential helper as documented in the [Cloud Source Repositories remote setup guide](https://cloud.google.com/source-repositories/docs/adding-repositories-as-remotes#add_the_repository_as_a_remote).
- Copy each generated workflow file from the Stage 0 outputs bucket or local `outputs_location` directory into `.github/workflows/` for GitHub, `.gitlab-ci.yml` for GitLab, or `.cloudbuild/workflow.yaml` for Cloud Build.

### Feature toggles

Feature toggles in `fast_features` are experimental and not officially supported in Stellar Engine. Downstream stages read `fast_features` to conditionally provision optional hierarchy branches:

- The `data_platform` toggle provisions folders, service accounts, buckets, and IAM bindings for the [3-data-platform](https://github.com/GoogleCloudPlatform/cloud-foundation-fabric/tree/master/fast/stages/3-data-platform) stage.
- The `gke` toggle provisions prerequisites for the [3-gke-multitenant](https://github.com/GoogleCloudPlatform/cloud-foundation-fabric/tree/master/fast/stages/3-gke-multitenant) stage.
- The `project_factory` toggle provisions prerequisites for the [3-project-factory](https://github.com/GoogleCloudPlatform/cloud-foundation-fabric/tree/master/fast/stages/3-project-factory) stage.
- The `sandbox` toggle creates a top-level `Sandbox` folder with relaxed policies for experimentation.
- The `teams` toggle creates a top-level `Teams` folder for the [Stage 1 teams feature](https://github.com/GoogleCloudPlatform/cloud-foundation-fabric/tree/master/fast/stages/1-resman#team-folders).

### Organization-level resources

Use `deploy_org_resources` when sharing a Google Cloud organization across multiple environments or lacking organization-level administrative permissions:

- Each attribute (`iam`, `custom_roles`, `logging_sinks`, `logging_settings`, `audit_config`, `org_policies`, and `workforce_identity_pool`) defaults to `true` and can be set to `false` independently.
- Setting `deploy_org_resources.org_policies = false` omits organization-level policy deployment and applies non-Assured Workloads baseline policies on `module.root-folder-config[0]` instead (excluding `custom.*`, `org_only_policies`, and the 12 Assured Workloads baseline policies).
- Running `./import.sh` detects `var.deploy_org_resources.org_policies`: when `true`, it imports organization policies into `module.organization`; when `false`, it queries `local.assured_workload_folder` and imports folder-level policies into `module.root-folder-config[0]`.
<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [alert_email](variables.tf#L17) | Email to receive log alerts. | <code>string</code> | ✓ |  |
| [billing_account](variables.tf#L35) | Billing account id. If billing account is not part of the same org set `is_org_level` to `false`. To disable handling of billing IAM roles set `no_iam` to `true`. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> | ✓ |  |
| [bootstrap_project](variables.tf#L63) | Bootstrap project ID. | <code>string</code> | ✓ |  |
| [organization](variables.tf#L382) | Organization details. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> | ✓ |  |
| [prefix](variables.tf#L397) | Prefix used for resources that need unique names. Use 7 characters or less. | <code>string</code> | ✓ |  |
| [assured_workloads](variables.tf#L22) | Configuration for Assured Workloads. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>&#123;&#8230;&#125;</code> |
| [billing_budget_amount](variables.tf#L45) | Optional Budget configuration for the AW folder. Includes amount and optional threshold rules (defaults to 0.5, 0.75, 0.9). If null, no budget will be created. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>null</code> |
| [billing_override](variables.tf#L54) | Optional billing override configuration. If set, disables service account impersonation for project billing linkage and runs under the user account using the specified quota projects. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>null</code> |
| [bootstrap_user](variables.tf#L68) | Email of the nominal user running this stage for the first time. | <code>string</code> |  | <code>null</code> |
| [cicd_repositories](variables.tf#L74) | CI/CD repository configuration. Identity providers reference keys in the `federated_identity_providers` variable. Set to null to disable, or set individual repositories to null if not needed. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>null</code> |
| [custom_roles](variables.tf#L141) | Map of role names => list of permissions to additionally create at the organization level. | <code>map&#40;list&#40;string&#41;&#41;</code> |  | <code>&#123;&#125;</code> |
| [deploy_org_resources](variables.tf#L148) | Selective control for deploying organization-level resources. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>&#123;&#125;</code> |
| [essential_contacts](variables.tf#L163) | Email or map of emails to notification category lists used for essential contacts, unset if null or empty. | <code>any</code> |  | <code>&#123;&#125;</code> |
| [factories_config](variables.tf#L177) | Configuration for the resource factories or external data. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>&#123;&#125;</code> |
| [fast_features](variables.tf#L189) | Selective control for top-level FAST features. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>&#123;&#125;</code> |
| [federated_identity_providers](variables.tf#L204) | Workload Identity Federation providers. | <code>map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> |  | <code>&#123;&#125;</code> |
| [force_destroy](variables.tf#L238) | Toggles force_destroy for GCS buckets. | <code>bool</code> |  | <code>false</code> |
| [groups](variables.tf#L244) | Group names or IAM-format principals to grant organization-level permissions. If just the name is provided, the 'group:' principal and organization domain are interpolated. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>&#123;&#125;</code> |
| [iam](variables.tf#L260) | Organization-level custom IAM settings in role => [principal] format. | <code>map&#40;list&#40;string&#41;&#41;</code> |  | <code>&#123;&#125;</code> |
| [iam_bindings_additive](variables.tf#L267) | Organization-level custom additive IAM bindings. Keys are arbitrary. | <code>map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> |  | <code>&#123;&#125;</code> |
| [iam_by_principals](variables.tf#L282) | Authoritative IAM binding in {PRINCIPAL => [ROLES]} format. Principals need to be statically defined to avoid cycle errors. Merged internally with the `iam` variable. | <code>map&#40;list&#40;string&#41;&#41;</code> |  | <code>&#123;&#125;</code> |
| [kms_protection_level](variables.tf#L289) | KMS protection level. | <code>string</code> |  | <code>null</code> |
| [locations](variables.tf#L300) | Optional locations for GCS, BigQuery, and logging buckets created here. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>&#123;&#125;</code> |
| [log_sinks](variables.tf#L316) | Org-level log sinks, in name => {type, filter} format. Valid types: 'logging' (routes to Cloud Logging bucket with 365-day default retention), 'pubsub' (routes to Pub/Sub topic with 7-day default retention; requires an active consumer to avoid log loss), 'storage' (routes to GCS bucket), 'bigquery' (routes to BigQuery dataset). | <code>map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> |  | <code>&#123;&#8230;&#125;</code> |
| [logging_bucket_retention](variables.tf#L352) | Retention period (in days) for the Cloud Logging buckets created for organization log exports. | <code>number</code> |  | <code>365</code> |
| [logging_kms_key](variables.tf#L358) | value of the KMS key used for logging. | <code>string</code> |  | <code>null</code> |
| [org_policies_config](variables.tf#L364) | Organization policies customization. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>&#123;&#125;</code> |
| [outputs_location](variables.tf#L391) | Enable writing provider, tfvars and CI/CD workflow files to local filesystem. Leave null to disable. | <code>string</code> |  | <code>null</code> |
| [project_deletion_policies](variables.tf#L406) | Deletion policy of each Stage 0 project. Use ABANDON for projects that you create outside Terraform and import, so terraform destroy leaves them in place. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>&#123;&#125;</code> |
| [project_parent_ids](variables.tf#L424) | Optional parents for projects created here in folders/nnnnnnn format. Null values will use the organization as parent. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>&#123;&#125;</code> |
| [regime_mapping](variables.tf#L435) | Mapping of compliance regime names to short codes. | <code>map&#40;string&#41;</code> |  | <code>&#123;&#8230;&#125;</code> |
| [regions](variables.tf#L468) | Region definitions. Must be specified in terraform.tfvars. Example: us-east4 for FedRAMP High compliance. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>&#123;&#8230;&#125;</code> |
| [workforce_identity_pool](variables.tf#L479) | Workforce Identity Federation pool configuration. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>null</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [alert_email](outputs.tf#L133) | Email to receive log alerts. |  |
| [assured_workload](outputs.tf#L138) | Assured Workload folder for the deployment. |  |
| [automation](outputs.tf#L143) | Automation resources. |  |
| [billing_dataset](outputs.tf#L148) | BigQuery dataset prepared for billing export. |  |
| [cicd_repositories](outputs.tf#L153) | CI/CD repository configurations. |  |
| [common_services_folder](outputs.tf#L165) | Common services folder where non-tenant related resources should be kept. |  |
| [custom_roles](outputs.tf#L170) | Organization-level custom roles. |  |
| [kms_protection_level](outputs.tf#L175) | KMS protection level. |  |
| [outputs_bucket](outputs.tf#L180) | GCS bucket where generated output files are stored. |  |
| [project_ids](outputs.tf#L185) | Projects created by this stage. |  |
| [providers](outputs.tf#L195) | Terraform provider files for this stage and dependent stages. | ✓ |
| [service_accounts](outputs.tf#L202) | Automation service accounts created by this stage. |  |
| [tfvars](outputs.tf#L220) | Terraform variable files for the following stages. | ✓ |
| [workforce_identity_pool](outputs.tf#L226) | Workforce Identity Federation pool. |  |
| [workload_identity_pool](outputs.tf#L235) | Workload Identity Federation pool and providers. |  |
<!-- END TFDOC -->
