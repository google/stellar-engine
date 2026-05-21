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
  - [Deleting the bootstrap project](#deleting-the-bootstrap-project)
- [Customizations](#customizations)
  - [KMS keys](#kms-keys)
  - [VPC Service Controls configuration](#vpc-service-controls-configuration)
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
- sa: comma-separated list of service account names if you don't want to enable/disable all of them (possible values are: bootstrap, resman, networking, security).

```bash
./sa_lockdown.sh --enable --sa "bootstrap,networking"
```

Some common troubleshooting steps:

- Ensure the file is executable by running
  
```bash
chmod +x sa_lockdown.sh
```
- Ensure the user running the command has the Service Account Admin role

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
- `perimeter_default` configures the single organization-wide perimeter by referencing access levels and policies by key, setting included Google Cloud Projects, and allowing to turn on dry run mode
- `resource_discovery` controls automatic discovery of Google Cloud Projects via Asset Inventory, and allows defining inclusion and exclusions lists

A few things to note on the default perimeter

- writer identities for sinks defined in the bootstrap stage are passed through via output files, and automatically included in an ingress policy
- the perimeter is brought up in enforced mode by default
- Google Cloud Project discovery is turned on by default and includes all Google Cloud Projects in the Google Cloud Organization

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

## Notes

Some references that might be useful in setting up this stage

- [VPC SC CSCC requirements](https://cloud.google.com/security-command-center/docs/troubleshooting).

---
<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [alert_email](variables.tf#L16) | Email to receive log alerts. | <code>string</code> | ✓ |  |
| [automation](variables.tf#L21) | Automation resources created by the bootstrap stage. | <code title="object&#40;&#123;&#10;  outputs_bucket &#61; string&#10;&#125;&#41;">object&#40;&#123;&#8230;&#125;&#41;</code> | ✓ |  |
| [billing_account](variables.tf#L29) | Billing account id. If billing account is not part of the same org set `is_org_level` to false. | <code title="object&#40;&#123;&#10;  id           &#61; string&#10;  is_org_level &#61; optional&#40;bool, true&#41;&#10;&#125;&#41;">object&#40;&#123;&#8230;&#125;&#41;</code> | ✓ |  |
| [folder_ids](variables.tf#L62) | Folder name => id mappings, the 'security' folder name must exist. | <code title="object&#40;&#123;&#10;  security &#61; string&#10;&#125;&#41;">object&#40;&#123;&#8230;&#125;&#41;</code> | ✓ |  |
| [organization](variables.tf#L123) | Organization details. | <code title="object&#40;&#123;&#10;  domain      &#61; string&#10;  id          &#61; number&#10;  customer_id &#61; string&#10;&#125;&#41;">object&#40;&#123;&#8230;&#125;&#41;</code> | ✓ |  |
| [prefix](variables.tf#L139) | Prefix used for resources that need unique names. Use 9 characters or less. | <code>string</code> | ✓ |  |
| [service_accounts](variables.tf#L149) | Automation service accounts that can assign the encrypt/decrypt roles on keys. | <code title="object&#40;&#123;&#10;  data-platform-dev    &#61; string&#10;  data-platform-prod   &#61; string&#10;  project-factory-dev  &#61; string&#10;  project-factory-prod &#61; string&#10;&#125;&#41;">object&#40;&#123;&#8230;&#125;&#41;</code> | ✓ |  |
| [assured_workloads](variables.tf#L199) | Assured Workloads configuration. | <code>any</code> |  | <code>null</code> |
| [billing_override](variables.tf#L184) | Optional billing override configuration. If set, disables service account impersonation for project billing linkage and runs under the user account using the specified quota projects. | <code title="object&#40;&#123;&#10;  project         &#61; string&#10;  billing_project &#61; string&#10;&#125;&#41;">object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>null</code> |
| [common_services_folder](variables.tf#L259) | Common services folder ID. | <code>any</code> |  | <code>null</code> |
| [custom_roles](variables.tf#L193) | Custom IAM roles defined during bootstrap. | <code>any</code> |  | <code>null</code> |
| [envs_folders](variables.tf#L235) | Environment folders mappings. | <code>any</code> |  | <code>null</code> |
| [essential_contacts](variables.tf#L42) | Email used for essential contacts, unset if null. | <code>string</code> |  | <code>null</code> |
| [factories_config](variables.tf#L48) | Paths to folders that enable factory functionality. | <code title="object&#40;&#123;&#10;  vpc_sc &#61; optional&#40;object&#40;&#123;&#10;    access_levels       &#61; optional&#40;string, &#34;data&#47;vpc-sc&#47;access-levels&#34;&#41;&#10;    egress_policies     &#61; optional&#40;string, &#34;data&#47;vpc-sc&#47;egress-policies&#34;&#41;&#10;    ingress_policies    &#61; optional&#40;string, &#34;data&#47;vpc-sc&#47;ingress-policies&#34;&#41;&#10;    restricted_services &#61; optional&#40;string, &#34;data&#47;vpc-sc&#47;restricted-services.yaml&#34;&#41;&#10;  &#125;&#41;, &#123;&#125;&#41;&#10;&#125;&#41;">object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>&#123;&#125;</code> |
| [fast_features](variables.tf#L253) | FAST features mapping. | <code>any</code> |  | <code>null</code> |
| [federated_identity_providers](variables.tf#L223) | Federated identity providers configuration. | <code>any</code> |  | <code>null</code> |
| [gcp_ranges](variables.tf#L229) | GCP address ranges configuration. | <code>any</code> |  | <code>null</code> |
| [groups](variables.tf#L211) | IAM groups configuration. | <code>any</code> |  | <code>null</code> |
| [kms_keys](variables.tf#L70) | KMS keys to create, keyed by name. | <code title="map&#40;object&#40;&#123;&#10;  rotation_period &#61; optional&#40;string, &#34;7776000s&#34;&#41; &#35; CIS Compliance Benchmark 1.10&#10;  labels          &#61; optional&#40;map&#40;string&#41;&#41;&#10;  locations &#61; optional&#40;list&#40;string&#41;, &#91;&#10;    &#34;us&#34;,          &#35; Multi-region&#10;    &#34;us-east4&#34;,    &#35; Primary region&#10;    &#34;us-central1&#34;, &#35; Secondary region&#10;  &#93;&#41;&#10;  purpose                       &#61; optional&#40;string, &#34;ENCRYPT_DECRYPT&#34;&#41;&#10;  skip_initial_version_creation &#61; optional&#40;bool, false&#41;&#10;  version_template &#61; optional&#40;object&#40;&#123;&#10;    algorithm        &#61; string&#10;    protection_level &#61; optional&#40;string, &#34;HSM&#34;&#41;&#10;  &#125;&#41;&#41;&#10;&#10;&#10;  iam &#61; optional&#40;map&#40;list&#40;string&#41;&#41;, &#123;&#125;&#41;&#10;  iam_bindings &#61; optional&#40;map&#40;object&#40;&#123;&#10;    members &#61; list&#40;string&#41;&#10;    role    &#61; string&#10;    condition &#61; optional&#40;object&#40;&#123;&#10;      expression  &#61; string&#10;      title       &#61; string&#10;      description &#61; optional&#40;string&#41;&#10;    &#125;&#41;&#41;&#10;  &#125;&#41;&#41;, &#123;&#125;&#41;&#10;  iam_bindings_additive &#61; optional&#40;map&#40;object&#40;&#123;&#10;    member &#61; string&#10;    role   &#61; string&#10;    condition &#61; optional&#40;object&#40;&#123;&#10;      expression  &#61; string&#10;      title       &#61; string&#10;      description &#61; optional&#40;string&#41;&#10;    &#125;&#41;&#41;&#10;  &#125;&#41;&#41;, &#123;&#125;&#41;&#10;&#125;&#41;&#41;">map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> |  | <code>&#123;&#125;</code> |
| [logging](variables.tf#L113) | Log writer identities for organization / folders. | <code title="object&#40;&#123;&#10;  project_number    &#61; string&#10;  writer_identities &#61; map&#40;string&#41;&#10;&#125;&#41;">object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>null</code> |
| [org_policy_classification_tags](variables.tf#L247) | Org policy classification tags configuration. | <code>any</code> |  | <code>null</code> |
| [outputs_location](variables.tf#L133) | Path where providers, tfvars files, and lists for the following stages are written. Leave empty to disable. | <code>string</code> |  | <code>null</code> |
| [regime_mapping](variables.tf#L217) | Compliance regime shorthand mapping. | <code>any</code> |  | <code>null</code> |
| [regions](variables.tf#L205) | GCP regions configuration. | <code>any</code> |  | <code>null</code> |
| [tenant_accounts](variables.tf#L241) | Tenant accounts configuration. | <code>any</code> |  | <code>null</code> |
| [vpc_sc](variables.tf#L160) | VPC SC configuration. | <code title="object&#40;&#123;&#10;  access_levels    &#61; optional&#40;map&#40;any&#41;, &#123;&#125;&#41;&#10;  egress_policies  &#61; optional&#40;map&#40;any&#41;, &#123;&#125;&#41;&#10;  ingress_policies &#61; optional&#40;map&#40;any&#41;, &#123;&#125;&#41;&#10;  perimeter_default &#61; optional&#40;object&#40;&#123;&#10;    access_levels    &#61; optional&#40;list&#40;string&#41;, &#91;&#93;&#41;&#10;    dry_run          &#61; optional&#40;bool, false&#41;&#10;    egress_policies  &#61; optional&#40;list&#40;string&#41;, &#91;&#93;&#41;&#10;    ingress_policies &#61; optional&#40;list&#40;string&#41;, &#91;&#93;&#41;&#10;    resources        &#61; optional&#40;list&#40;string&#41;, &#91;&#93;&#41;&#10;  &#125;&#41;&#41;&#10;  resource_discovery &#61; optional&#40;object&#40;&#123;&#10;    enabled          &#61; optional&#40;bool, true&#41;&#10;    ignore_folders   &#61; optional&#40;list&#40;string&#41;, &#91;&#93;&#41;&#10;    ignore_projects  &#61; optional&#40;list&#40;string&#41;, &#91;&#93;&#41;&#10;    include_projects &#61; optional&#40;list&#40;string&#41;, &#91;&#93;&#41;&#10;  &#125;&#41;, &#123;&#125;&#41;&#10;&#125;&#41;">object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>&#123;&#125;</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [kms_keys](outputs.tf#L55) | KMS key ids. |  |
| [tfvars](outputs.tf#L60) | Terraform variable files for the following stages. | ✓ |
| [vpc_sc_perimeter_default](outputs.tf#L66) | Raw default perimeter resource. | ✓ |
<!-- END TFDOC -->
