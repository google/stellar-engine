# Shared security resources and VPC Service Controls

This stage sets up security resources and configurations which impact the whole Google Cloud Organization, or are shared across the hierarchy to other projects and teams.

The design of this stage is fairly general, providing

- a reference example for [Cloud KMS](https://cloud.google.com/security-key-management)
- a simplified implementation of [VPC Service Controls](https://cloud.google.com/vpc-service-controls) that should work for most users

Expanding this stage to include other security-related services like Secret Manager is fairly simple by adapting the provided implementation for Cloud KMS, and leveraging the broad permissions granted on the top-level Security folder to the automation service account used here.

The following diagram illustrates the high-level design of created resources and a schema of the VPC SC design:

<p align="center">
  <img src="diagram.png" alt="Security diagram">
</p>

# Table of Contents

<!-- BEGIN TOC -->
- [Table of Contents](#table-of-contents)
- [Design overview and choices](#design-overview-and-choices)
  - [Cloud KMS](#cloud-kms)
  - [VPC Service Controls](#vpc-service-controls)
- [How to run this stage](#how-to-run-this-stage)
  - [Provider and Terraform variables](#provider-and-terraform-variables)
  - [Impersonating the automation service account](#impersonating-the-automation-service-account)
  - [Setting default project for manual run](#setting-default-project-for-manual-run)
  - [Variable configuration](#variable-configuration)
  - [Using delayed billing association for Google Cloud Projects](#using-delayed-billing-association-for-google-cloud-projects)
  - [Running the stage](#running-the-stage)
  - [Disabling overpermissive service accounts](#disabling-overpermissive-service-accounts)
    - [Environment folders account](#environment-folders-account)
    - [CI/CD service accounts](#cicd-service-accounts)
    - [Tenant service accounts](#tenant-service-accounts)
  - [Verifying service account lockdown](#verifying-service-account-lockdown)
  - [Deleting the bootstrap project](#deleting-the-bootstrap-project)
- [Customizations](#customizations)
  - [KMS keys](#kms-keys)
  - [VPC Service Controls configuration](#vpc-service-controls-configuration)
    - [Trial a candidate configuration](#trial-a-candidate-configuration)
- [Notes](#notes)
- [Variables](#variables)
- [Outputs](#outputs)
<!-- END TOC -->

## Design overview and choices

Google Cloud Project level security resources are grouped into two separate Google Cloud Projects, one per environment. This setup matches requirements we frequently observe in real life and provides enough separation without needlessly complicating operations.

Cloud KMS is configured and designed mainly to encrypt Google Cloud resources with a [Customer-managed encryption key](https://cloud.google.com/kms/docs/cmek) but it may be used to create cryptokeys used to [encrypt application data](https://cloud.google.com/kms/docs/encrypting-application-data) too.

IAM for day to day operations is already assigned at the folder level to the security team by the previous stage, but more granularity can be added here at the project level, to grant control of separate services across environments to different actors.

### Cloud KMS

A reference Cloud KMS implementation is part of this stage, to provide a simple way of managing centralized keys, that are then shared and consumed widely across the organization to enable customer-managed encryption. The implementation is also easy to clone and modify to support other services like Secret Manager.

The Cloud KMS configuration allows defining keys by name (typically matching the downstream service that uses them) in different locations. It then takes care internally of provisioning the relevant `keyrings` and creating keys in the appropriate location.

IAM roles on keys can be configured at the logical level for all locations where a logical key is created. Their management can also be delegated via [delegated role grants](https://cloud.google.com/iam/docs/setting-limits-on-granting-roles) exposed through a simple variable, to allow other identities to set IAM policies on keys. This is particularly useful in setups like project factories, making it possible to configure IAM bindings during project creation for team groups or service agent accounts (compute, storage, etc.).

### VPC Service Controls

This stage also provisions the VPC Service Controls configuration that protects the whole Google Cloud Organization, implementing a simplified design that leverages a single perimeter and optionally provides automatic enrollment of Google Cloud Projects in the perimeter.

The VPC SC configuration is controlled via the top-level `vpc_sc` variable, and is disabled by default unless `vpc_sc.perimeter_default` is populated. Access levels and ingress/egress policies can be defined in code via the respective `vpc_sc` variable attributes, or via YAML-based factories configured via the usual `factories_config` variable.

## How to run this stage

This stage is meant to be executed after the [resource management](../1-resman) stage has run, as it leverages the automation service account and bucket created there, and additional resources configured in the [bootstrap](../0-bootstrap) stage.

It's of course possible to run this stage in isolation, but that's outside the scope of this document, and you would need to refer to the code for the previous stages for the environmental requirements.

Before running this stage, you need to make sure you have the correct credentials and permissions, and localize variables by assigning values that match your configuration.

### Provider and Terraform variables

As all other FAST stages, the [mechanism used to pass variable values and pre-built provider files from one stage to the next](../0-bootstrap/README.md#output-files-and-cross-stage-variables) is also leveraged here.

The commands to link or copy the provider and terraform variable files can be easily derived from the `stage-links.sh` script in the FAST root folder, passing it a single argument with the local output files folder (if configured) or the GCS output bucket in the automation project (derived from stage 0 outputs). The following examples demonstrate both cases, and the resulting commands that then need to be copy/pasted and run.

```bash
../../stage-links.sh gs://xxx-prod-iac-core-outputs-0
```

_Copy and paste the following commands for '3-security'_

```bash
gcloud alpha storage cp gs://xxx-prod-iac-core-outputs-0/providers/3-security-providers.tf ./
gcloud alpha storage cp gs://xxx-prod-iac-core-outputs-0/tfvars/0-globals.auto.tfvars.json ./
gcloud alpha storage cp gs://xxx-prod-iac-core-outputs-0/tfvars/0-bootstrap.auto.tfvars.json ./
gcloud alpha storage cp gs://xxx-prod-iac-core-outputs-0/tfvars/1-resman.auto.tfvars.json ./
```

### Impersonating the automation service account

The preconfigured provider file uses impersonation to run with this stage's automation service account's credentials. The `gcp-devops` and `organization-admins` groups have the necessary IAM bindings in place to do that, so make sure the current user is a member of one of those groups.

Make sure the `network` service account has the `Service Usage Consumer` role.

Find the network service account by changing directories to `1-resman` in order to run Terraform to query the values needed.

```bash
cd ../1-resman/
terraform output security
```

And make sure it has the "Service Usage Consumer" role in the project that you are using to bootstrap.

### Setting default project for manual run

**Important**: Before running this, make sure that if you are running these stages manually from the command line, that your default project is set to the 'automation' Google Cloud Project created in 0-bootstrap.

To find the 'automation' project,

```bash
cd ../0-bootstrap
terraform output project_ids
```

And to set the gcloud project default in your CLI
```bash
gcloud config set project <prefix>-prod-iac-core-0
```

Now return to the Security directory.

```bash
cd ../3-security
```

### Variable configuration

Variables in this stage -- like most other FAST stages -- are broadly divided into three separate sets:

- variables which refer to global values for the whole Google Cloud Organization (org id, billing account id, prefix, etc.), which are pre-populated via the `0-globals.auto.tfvars.json` file linked or copied above
- variables which refer to resources managed by previous stages, which are prepopulated here via the `0-bootstrap.auto.tfvars.json` and `1-resman.auto.tfvars.json` files linked or copied above
- and finally variables that optionally control this stage's behavior and customizations, and can to be set in a custom `terraform.tfvars` file

The latter set is explained in the [Customization](#customizations) sections below, and the full list can be found in the [Variables](#variables) table at the bottom of this document.

Note that the `outputs_location` variable is disabled by default, you need to explicitly set it in your `terraform.tfvars` file if you want output files to be generated by this stage. This is a sample `terraform.tfvars` that configures it, refer to the [bootstrap stage documentation](../0-bootstrap/README.md#output-files-and-cross-stage-variables) for more details:

```tfvars
outputs_location = "~/fast-config"
```

### Using delayed billing association for Google Cloud Projects

This configuration is possible but unsupported and only exists for development purposes, use at your own risk:

- temporarily switch `billing_account.id` to `null` in `0-globals.auto.tfvars.json`
- for each project resources in the project modules used in this stage (`dev-sec-project`, `prod-sec-project`)
  - apply using `-target`, for example
    `terraform apply -target 'module.prod-sec-project.google_project.project[0]'`
  - untaint the project resource after applying, for example
    `terraform untaint 'module.prod-sec-project.google_project.project[0]'`
- go through the process to associate the billing account with the two Google Cloud Projects
- switch `billing_account.id` back to the real billing account id
- resume applying normally

### Running the stage

Once provider and variable values are in place and the correct user is configured, the stage can be run:

```bash
terraform init
terraform plan
terraform apply
```
### Disabling overpermissive service accounts

Each stage of this deployment uses service accounts with admin roles. Once the deployment has been completed, these service accounts should be disabled for security reasons. You can disable the service accounts by running:

```bash
./sa_lockdown.sh
```

You can also run this script with the following flags

- enable: enables the service accounts instead of disabling them (useful if you would like to rerun a stage or make customizations).
- sa: comma-separated list of service account names if you don't want to enable/disable all of them. The possible values are the keys that the `0-bootstrap` and `1-resman` stages write under `service_accounts` in their tfvars files:
  - bootstrap, resman, networking, security
  - bootstrap-r, resman-r, networking-r, security-r for the read-only plan accounts
  - data-platform-dev, data-platform-prod, gcve-dev, gcve-prod, gke-dev, gke-prod, project-factory-dev, project-factory-prod, each also with an `-r` suffix for its read-only plan account
  - envs for the `prod-resman-envs-0` account, which holds `roles/owner` on every environment folder
  - sandbox, teams, one `team-<name>` value for each entry in `team_folders`, and one `tenant-core-<env>-<tenant>` value for each lightweight tenant environment (`tn-<env>-<tenant>-prod-0`, lowercased)

Without the `sa` flag, the script covers every value in this list. It skips the accounts of branches that are not deployed. Re-enable the accounts of a branch before you run that branch again.

```bash
./sa_lockdown.sh --enable --sa "bootstrap,networking"
```

Some common troubleshooting steps:

- Ensure the file is executable by running
  
```bash
chmod +x sa_lockdown.sh
```
- Ensure the user running the command has the Service Account Admin role

#### Environment folders account

Stage 1 creates the `prod-resman-envs-0` account when `fast_features.envs` is `true`, and grants it `roles/owner` on every environment folder. The script disables this account through the `envs` key that Stage 1 writes under `service_accounts` in `1-resman.auto.tfvars.json`.

A tfvars file that an earlier Stage 1 release wrote has no `envs` key, so the script skips the account without a message. To lock down a deployment in that state, use one of the following options:

- Run `./sa_lockdown.sh --enable --sa resman`, apply Stage 1 again so that it writes the `envs` key, refresh the `1-resman.auto.tfvars.json` file in this directory if it is a copy, then run `./sa_lockdown.sh` again.
- Disable the account directly:

```bash
gcloud iam service-accounts disable \
  <prefix>-prod-resman-envs-0@<iac-core-project-id>.iam.gserviceaccount.com \
  --project <iac-core-project-id>
```

Run `./validation.sh` afterward. The script prints a `FAILED` line for the account while the account is still enabled.

#### CI/CD service accounts

The script does not disable the CI/CD service accounts that the `0-bootstrap` and `1-resman` stages create when you set `cicd_repositories`. The IDs of these accounts end in `-1` for apply pipelines and in `-1r` for plan pipelines, such as `bootstrap-1`, `resman-1r`, `prod-resman-net-1`, and `prod-teams-<name>-1`. The stages do not write these accounts to the tfvars files that the script reads, and `validation.sh` does not check them.

The script leaves these accounts enabled for the following reasons:

- A CI/CD account holds no administrative role of its own. It acts on the deployment by impersonating its matching `-0` or `-0r` account through `roles/iam.serviceAccountTokenCreator`. Google Cloud rejects that impersonation while the target account is disabled, so the default run already blocks every pipeline from acting on the deployment.
- A Day-2 GitOps pipeline works again after you re-enable its target account alone, for example with `./sa_lockdown.sh --enable --sa networking`.

A CI/CD account that stays enabled keeps the following direct grants:

- `roles/logging.logWriter` on the IaC core project
- `roles/storage.objectViewer` on the outputs bucket, which holds the provider, tfvars, and workflow files of the stages
- `roles/source.reader` on its repository, when the repository type is `sourcerepo`
- The Workload Identity Federation binding that lets its external repository obtain tokens for the account

Disable these accounts as well when the deployment runs no CI/CD pipeline after the lockdown, or when the authorization boundary requires every automation identity to be disabled. List the accounts, review the list, and disable each account:

```bash
gcloud iam service-accounts list --project <iac-core-project-id> \
  --filter="email ~ '-1r?@'" --format="value(email)"
gcloud iam service-accounts disable <account-email> --project <iac-core-project-id>
```

The filter also matches any other account in the project whose ID ends in `-1` or `-1r`, so review each email before you disable the account. Enable the account again with `gcloud iam service-accounts enable` before the pipeline runs.

#### Tenant service accounts

Stage 1 creates two automation service accounts per lightweight `(env, tenant)` pair when `tenants` is configured:

- Lowercased core tenant service accounts (`<prefix>-tn-<env>-<tenant>-prod-0`) reside in the organization `<prefix>-prod-iac-core-0` project and hold broad privileges (`roles/owner` and folder and project administration) on the tenant top folder (`Project <tenant> <env>`). Stage 1 exports them under `tenant-core-<env>-<tenant>` keys in `1-resman.auto.tfvars.json`, so `sa_lockdown.sh` disables them by default (`--sa tenant-core-<env>-<tenant>` targets one directly) and `validation.sh` checks them.
- Self-service tenant IaC service accounts (`<prefix>-<env>-<tenant>-iac-0`) reside inside each tenant-managed `<prefix>-<env>-<tenant>-iac-core-0` project rather than the organization IaC core project. As a documented operational exception, `sa_lockdown.sh` leaves `<env>-<tenant>-iac-0` enabled by default so tenant teams can run Day-2 infrastructure pipelines autonomously within their tenant boundary without re-enabling organization automation.

Each enabled `<env>-<tenant>-iac-0` account retains these residual grants (project `roles/owner` on `<prefix>-<env>-<tenant>-iac-core-0` and `<prefix>-<env>-<tenant>-main-0` is held by Stage 1 `var.automation.service_accounts.resman` and inherited by `<prefix>-tn-<env>-<tenant>-prod-0`, not `<env>-<tenant>-iac-0`):

- `roles/viewer` on the tenant top folder (`Project <tenant> <env>`), plus any optional custom folder roles in `var.tenants_config` (`top_folder_roles`, `core_folder_roles`, and `tenant_folder_roles`, all empty by default)
- `roles/storage.admin` on the tenant outputs and state buckets (`<prefix>-<env>-<tenant>-iac-outputs-0` and `<prefix>-<env>-<tenant>-iac-0`)

If your authorization boundary requires disabling tenant self-service accounts after initial provisioning, run the command below against each tenant IaC core project and re-enable the account before Day-2 tenant applies:

```bash
gcloud iam service-accounts disable \
  <prefix>-<env>-<tenant>-iac-0@<prefix>-<env>-<tenant>-iac-core-0.iam.gserviceaccount.com \
  --project <prefix>-<env>-<tenant>-iac-core-0
```

### Verifying service account lockdown

After running `sa_lockdown.sh`, verify that the deployment service accounts in the IaC core project are disabled:

```bash
./validation.sh
```

The script checks the same accounts that `sa_lockdown.sh` disables by default, which are the apply accounts, the read-only plan accounts, the Stage 1 branch accounts, the `team-<name>` accounts, and the `tenant-core-<env>-<tenant>` accounts (`tn-<env>-<tenant>-prod-0`). Run the script from this directory so that it also checks the accounts listed in the tfvars files that `sa_lockdown.sh` reads.

When multiple `-prod-iac-core-0` projects exist in the same organization (multi-tenant or multi-enclave deployments), target a single enclave using one of the following mutually exclusive flags:

- `--prefix PREFIX`: filters project discovery to `^<PREFIX>-prod-iac-core-0$`.
- `--project PROJECT_ID`: checks the specified IaC core project ID directly without running `gcloud projects list`.

```bash
./validation.sh --prefix myencl
./validation.sh --project myencl-prod-iac-core-0
```

With either flag, the script skips the tfvars accounts that are not in the selected project and prints a warning for them.

The script exits with status `0` only when every checked account is disabled. It exits with status `1` when an account is still enabled, when it finds no account to check, or when a `gcloud` or `jq` call fails, so a pipeline can stop on an incomplete lockdown.

### Deleting the bootstrap project

Once Stellar Engine has been deployed, the bootstrap Google Cloud Project is no longer necessary. You can delete the bootstrap Google Cloud Project by running the following script within the "3-security" directory.  Be sure to insert your appropriate boostrap Google Cloud Project ID.

```bash
./delete_gcp_project.sh --project-id=<bootstrap-project-id>
```

Troubleshooting Steps

- Ensure that you are authenticated with `gcloud auth login`
- Ensure the file is executable by running

```bash
chmod +x delete_gcp_project.sh
```

## Customizations

### KMS keys

Cloud KMS configuration is controlled by `kms_keys`, which configures the actual keys to create, and also allows configuring their IAM bindings, labels, locations and rotation period. When configuring locations for a key, please consider the limitations each cloud product may have.

> [!NOTE]
> Stage 3 produces **no** KMS keyrings or keys by default since `var.kms_keys` defaults to `{}`. Key provisioning is entirely opt-in. A reference configuration is provided in `terraform.tfvars.sample`.
> Downstream stages and blueprints can query created key paths via `terraform output kms_keys`, which returns a map of key IDs keyed by `{env}-{name}:{location}` (for example, `dev-default:us-east4` or `prod-default:us-east4`).

The additional `kms_restricted_admins` variable allows granting `roles/cloudkms.admin` to specified principals, restricted via [delegated role grants](https://cloud.google.com/iam/docs/setting-limits-on-granting-roles) so that it only allows granting the roles needed for encryption/decryption on keys. This allows safe delegation of key management to subsequent Terraform stages like the Project Factory, for example to grant usage access on relevant keys to the service agent accounts for compute, storage, etc.

To support these scenarios, key IAM bindings are configured by default to be additive, to enable other stages or Terraform configuration to safely co-manage bindings on the same keys. If this is not desired, follow the comments in the `core-dev.tf` and `core-prod.tf` files to switch to authoritative bindings on keys.

An example of how to configure keys:

```tfvars
# terraform.tfvars

kms_keys = {
  compute = {
    iam = {
      "roles/cloudkms.cryptoKeyEncrypterDecrypter" = [
        "user:user1@example.com"
      ]
    }
    labels          = { service = "compute" }
    locations       = ["us-east4", "europe-west3", "global"]
    rotation_period = "7776000s"
  }
  storage = {
    iam             = null
    labels          = { service = "compute" }
    locations       = ["europe"]
    rotation_period = null
  }
}
```

The script will create one keyring for each specified location and keys on each keyring.

### VPC Service Controls configuration

The `vpc_sc` variable controls VPC-SC configuration and project auto-discovery via Cloud Asset Inventory. VPC-SC configuration can also leverage YAML factories via the `factories_config` variable. Both variables mostly pass through to the underlying [`vpc-sc` module](../../../modules/vpc-sc/), which serves as a reference for their individual types.

The `vpc_sc` variable has the following attributes

- `access_levels`, `egress_policies`, `ingress_policies` define the corresponding objects, internally merged with any data coming from the YAML factories
- `access_policy` specifies the numeric ID of an existing Access Context Manager policy without the `accessPolicies/` prefix so the stage reuses it instead of creating a new organization-level policy; in folder-scoped deployments, bind `roles/accesscontextmanager.policyAdmin` on `accessPolicies/<id>` or at the organization level
- `perimeter_default` configures the single organization-wide perimeter by referencing access levels and policies by key, setting included Google Cloud Projects, optionally restricting `vpc_accessible_services`, and allowing to turn on dry run mode
- `project_id_search_scope` sets an organization `organizations/<id>` or folder `folders/<id>` Cloud Asset Inventory scope so the `vpc-sc` module translates `projects/<project-id>` references to project numbers
- `resource_discovery` controls automatic discovery of Google Cloud Projects via Asset Inventory, including an optional `parent` scope in `organizations/<id>` or `folders/<id>` format that defaults to the organization, plus inclusion and exclusion lists

A few things to note on the default perimeter

- writer identities for sinks defined in the bootstrap stage are passed through via output files, and automatically included in an ingress policy
- the perimeter is brought up in enforced mode by default
- setting `dry_run` to `true` configures only the dry-run spec and removes the enforced configuration, so nothing is enforced
- setting `dry_run_spec` keeps the perimeter enforced and trials a candidate configuration in the dry-run spec, as the next section describes
- Google Cloud Project discovery is turned on by default and includes all Google Cloud Projects in the Google Cloud Organization unless `resource_discovery.parent` scopes discovery to a folder
- the stage resolves access level names in `perimeter_default` and in policies defined through the `vpc_sc` variable, while ingress and egress policy YAML files reference access levels as `$access_levels:<name>`

The following example configures the default perimeter, with a single broad geo-based access level. Refer to the [vpc-sc module](../../../modules/vpc-sc/) for details on how to configure ingress/egress policies, and how to leverage the YAML factories. The perimeter is set to enforced mode and leverages auto discovery of Google Cloud Projects.

The following YAML file leverages factories to configure the broad geo-based access level (the factory path can be changed via the `factories_config` variable):

```yaml
# data/vpc-sc/access-levels/geo-default.yaml
conditions:
  - regions:
      - IT
      - ES
```

```tfvars
# terraform.tfvars

vpc_sc = {
  perimeter_default = {
    access_levels = ["geo-default"]
    # dry run is disabled by default
    dry_run = true
    # resource discovery is enabled by default
  }
}
```

#### Trial a candidate configuration

The `dry_run_spec` attribute of `perimeter_default` lets you trial a change to an enforced perimeter before you enforce it. The enforced status keeps the `perimeter_default` configuration, the dry-run spec receives the candidate, and VPC Service Controls logs the requests that the candidate would deny without blocking them.

- each `dry_run_spec` attribute you set replaces the matching enforced value in the dry-run spec only, and an empty list clears a list attribute
- setting `vpc_accessible_services = {}` enables restriction with `RESTRICTED-SERVICES` because `enable_restriction` defaults to `true`; to disable restriction in `dry_run_spec`, set `{ enable_restriction = false }`
- each attribute you omit or set to `null` inherits the enforced value
- `access_levels`, `egress_policies`, `ingress_policies`, `resources`, and `vpc_accessible_services` override the `perimeter_default` attributes with the same names, and `restricted_services` overrides the list in the restricted services YAML file
- the dry-run spec still receives the log sink ingress policy and the discovered Google Cloud Projects
- the stage rejects `dry_run_spec` when `dry_run` is `true`, and rejects a `dry_run_spec` that sets no attribute

The following example keeps the perimeter enforced and trials one more ingress policy and a shorter list of restricted services.

```tfvars
# terraform.tfvars

vpc_sc = {
  perimeter_default = {
    access_levels    = ["geo-default"]
    ingress_policies = ["partner-read"]
    dry_run_spec = {
      ingress_policies    = ["partner-read", "partner-write"]
      restricted_services = ["bigquery.googleapis.com", "storage.googleapis.com"]
    }
  }
}
```

To promote the candidate, copy the `dry_run_spec` values into `perimeter_default` or the restricted services YAML file, and remove `dry_run_spec`.

The enforced status and the dry-run spec share the access level definitions, the ingress and egress policy definitions, and the discovered Google Cloud Projects, so only the `dry_run_spec` attributes are safe to change during a trial.

- editing an access level or a policy that `perimeter_default` references changes the enforced perimeter on the same apply, so define the candidate under a new key and reference that key in `dry_run_spec`
- a change to `resource_discovery` adds or removes Google Cloud Projects in both the enforced status and the dry-run spec, so to trial a new Google Cloud Project keep it in `resource_discovery.ignore_projects` and add `projects/<number>` to `dry_run_spec.resources` together with the enforced `perimeter_default.resources` values

## Notes

Some references that might be useful in setting up this stage

- [VPC SC CSCC requirements](https://cloud.google.com/security-command-center/docs/troubleshooting).

---
<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [alert_email](variables.tf#L17) | Email to receive log alerts. | <code>string</code> | ✓ |  |
| [automation](variables.tf#L35) | Automation resources created by the bootstrap stage. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> | ✓ |  |
| [billing_account](variables.tf#L43) | Billing account id. If billing account is not part of the same org set `is_org_level` to false. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> | ✓ |  |
| [envs_folders](variables.tf#L84) | List of environments to be created for projects to go into. | <code>map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> | ✓ |  |
| [folder_ids](variables.tf#L136) | Folder name => id mappings, the 'security' folder name must exist. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> | ✓ |  |
| [organization](variables.tf#L218) | Organization details. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> | ✓ |  |
| [prefix](variables.tf#L234) | Prefix used for resources that need unique names. Use 9 characters or less. | <code>string</code> | ✓ |  |
| [regions](variables.tf#L251) | Region definitions. Inherited from 0-bootstrap outputs. Must be specified in bootstrap terraform.tfvars. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> | ✓ |  |
| [service_accounts](variables.tf#L260) | Automation service accounts that can assign the encrypt/decrypt roles on keys. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> | ✓ |  |
| [tenant_accounts](variables.tf#L275) | Base Tenant accounts that are created for each folder, provided as a combination of environment and tenant. | <code>map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> | ✓ |  |
| [assured_workloads](variables.tf#L23) | Configuration for Assured Workloads. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>&#123;&#125;</code> |
| [billing_override](variables.tf#L56) | Optional billing override configuration. If set, disables service account impersonation for project billing linkage and runs under the user account using the specified quota projects. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>null</code> |
| [common_services_folder](variables.tf#L65) | Common services folder where non-tenant related resources should be kept. | <code>string</code> |  | <code>null</code> |
| [custom_roles](variables.tf#L72) | Custom roles defined at the org level, in key => id format. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>null</code> |
| [essential_contacts](variables.tf#L92) | Email or map of emails to notification category lists used for essential contacts, unset if null or empty. | <code>any</code> |  | <code>&#123;&#125;</code> |
| [factories_config](variables.tf#L106) | Paths to folders that enable factory functionality. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>&#123;&#125;</code> |
| [fast_features](variables.tf#L120) | Selective control for top-level FAST features. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>&#123;&#125;</code> |
| [gcp_ranges](variables.tf#L144) | GCP address ranges configuration. | <code>any</code> |  | <code>null</code> |
| [groups](variables.tf#L151) | IAM groups configuration. | <code>any</code> |  | <code>null</code> |
| [kms_keys](variables.tf#L158) | KMS keys to create, keyed by name. | <code>map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> |  | <code>&#123;&#125;</code> |
| [kms_protection_level](variables.tf#L201) | Protection level (HSM or SOFTWARE) applied to every key in kms_keys that does not set its own version_template. | <code>string</code> |  | <code>null</code> |
| [logging](variables.tf#L208) | Log writer identities for organization / folders. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>null</code> |
| [outputs_location](variables.tf#L228) | Path where providers, tfvars files, and lists for the following stages are written. Leave empty to disable. | <code>string</code> |  | <code>null</code> |
| [regime_mapping](variables.tf#L244) | Compliance regime shorthand mapping. | <code>any</code> |  | <code>null</code> |
| [vpc_sc](variables.tf#L286) | VPC SC configuration. Setting `perimeter_default.dry_run_spec` keeps the perimeter enforced and trials the overridden attributes in the dry-run spec. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>&#123;&#125;</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [kms_keys](outputs.tf#L55) | KMS key ids. |  |
| [tfvars](outputs.tf#L60) | Terraform variable files for the following stages. | ✓ |
| [vpc_sc_perimeter_default](outputs.tf#L66) | Raw default perimeter resource. | ✓ |
<!-- END TFDOC -->
