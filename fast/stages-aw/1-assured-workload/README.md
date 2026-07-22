# Google Cloud Assured Workload Bootstrap

The purpose of this stage is to enable critical Google Cloud Assured Workload level functionalities that prepare the prerequisites needed to enable automation in this and future stages. In addition, this stage ensures that all future fast stages are compliant with the selected compliance regime.

<!-- BEGIN TOC -->
- [Design Overview and Choices](#design-overview-and-choices)
  - [Assured Workloads](#assured-workloads)
  - [User Groups](#user-groups)
  - [Automation Google Cloud Project and Resources](#automation-google-cloud-project-and-resources)
  - [Billing Account](#billing-account)
  - [Tenant Log Sinks](#tenant-log-sinks)
  - [Log Sinks and Log Destinations](#log-sinks-and-log-destinations)
  - [Naming](#naming)
  - [Workload Identity Federation and CI/CD](#workload-identity-federation-and-cicd)
- [How to Run This Stage](#how-to-run-this-stage)
- [Customizations](#customizations)
  - [Group Names](#group-names)
  - [IAM](#iam)
  - [Names and Naming Convention](#names-and-naming-convention)
  - [Workload Identity Federation](#workload-identity-federation)
  - [CI/CD Repositories](#cicd-repositories)
  - [Toggling features](#toggling-features)
- [Variables](#variables)
- [Outputs](#outputs)
<!-- END TOC -->

## Design Overview and Choices

This stage only does the bare minimum required to bootstrap Assured Workloads, automation, and common services. It ensures that base audit and billing exports are in place from the start to provide some measure of accountability, before the security configurations are applied in a later stage.

### Assured Workloads

Assured Workloads Google Cloud Folders are provisioned in this stage to ensure all future Google Cloud Folders, Google Cloud Projects, and services are deployed within scope of the selected Assured Workloads compliance regime. More information on Assured Workloads is highlighted [here](https://cloud.google.com/security/products/assured-workloads).

### User Groups

User groups are important, not only here but throughout the whole automation process. They provide a stable frame of reference that allows decoupling the final set of permissions for each group, from the stage where entities and resources are created and their IAM bindings defined. For example, the final set of roles for the networking group is contributed by this stage at the Google Cloud Organization level (XPN Admin, Cloud Asset Viewer, etc.), and by the Resource Management stage at the Google Cloud Folder level.

We have standardized the initial set of groups on those outlined in the [GCP Enterprise Setup Checklist](https://cloud.google.com/docs/enterprise/setup-checklist) to simplify adoption. They provide a comprehensive and flexible starting point that can suit most users. Adding new groups, or deviating from the initial setup is possible and reasonably simple, and it's briefly outlined in the customization section below.

### Automation Google Cloud Project and Resources

One other design choice worth mentioning here is using a single automation Google Cloud Project for all foundational stages. We trade off some complexity on the API side (single source for usage quota, multiple service activation) for increased flexibility and simpler operations, while still effectively providing the same degree of separation via resource-level IAM.

### Billing Account

We support three use cases in regards to billing:

- the billing account is part of this same Google Cloud Organization, IAM bindings will be set at the Google Cloud Organization level
- the billing account is not considered part of an Google Cloud Organization (even though it might be), billing IAM bindings are set on the billing account itself
- billing IAM is managed separately, and no bindings should (or can) be set via Terraform, this requires a few extra steps and is definitely not recommended and mainly used for development purposes

For same Google Cloud Organization billing, we configure a custom Google Cloud Organization role that can set IAM bindings, via a delegated role grant to limit its scope to the relevant roles.

For details on configuring the different billing account modes, refer to the [How to run this stage](#how-to-run-this-stage) section below.

Due to limitations of API availability, manual steps have to be followed to enable billing export within the billing Google Cloud Project to BigQuery dataset `billing_export`, which will be created as part of the bootstrap stage. The process to share billing data [is outlined here](https://cloud.google.com/billing/docs/how-to/export-data-bigquery-setup#enable-bq-export).

### Tenant Log Sinks

Organization-level logging sinks for tenants creates centralized log routing from tenant folders to dedicated log buckets during the stage they are created. This customization is integrated from the bootstrap stage where outputs are staged. It captures logs from the tenant folders, projects, and all their related activities including automated tenant mappings for routing and ingestion into Google SecOps.

### Log Sinks and Log Destinations

You can customize Google Cloud Organization level logs through the `log_sinks` variable in two ways

- creating additional log sinks to capture more logs
- changing the destination of captured logs

By default, all logs are exported to a log bucket, but FAST can create sinks to BigQuery, GCS, or PubSub.

If you need to capture additional logs, please refer to GCP's documentation on [Scenarios for Exporting Logging Data](https://cloud.google.com/architecture/exporting-stackdriver-logging-for-security-and-access-analytics), where you can find ready-made filter expressions for different use cases.

### Naming

We are intentionally not supporting random prefix/suffixes for names, as that is an anti-pattern typically only used in development. It does not map to our customer's actual production usage, where they always adopt a fixed naming convention.

What is implemented here is a fairly common convention, composed of tokens ordered by relative importance

- an Google Cloud Organization level static prefix less or equal to 9 characters (e.g. `myco` or `myco-gcp`)
- an environment identifier (e.g. `prod`)
- a team/owner identifier (e.g. `sec` for Security)
- a context identifier (e.g. `core` or `kms`)
- an arbitrary identifier used to distinguish similar resources (e.g. `0`, `1`)

Tokens are joined by a `-` character, making it easy to separate the individual tokens visually, and to programmatically split them in billing exports to derive initial high-level groupings for cost attribution.

The convention is used in its full form only for specific resources with globally unique names (Google Cloud Projects, GCS buckets). Other resources adopt a shorter version for legibility, as the full context can always be derived from their Google Cloud Project.

The [Customizations](#names-and-naming-convention) section on names below explains how to configure tokens, or implement a different naming convention.

### Workload Identity Federation and CI/CD

This stage also implements initial support for two interrelated features

- configuration of [Workload Identity Federation](https://cloud.google.com/iam/docs/workload-identity-federation) pools and providers
- configuration of CI/CD repositories to allow impersonation via Workload identity Federation, and stage running via provided workflow templates

Workload Identity Federation support allows configuring external providers independently from CI/CD, and offers predefined attributes for a few well known ones (more can be easily added by editing the `identity-providers.tf` file). Once providers have been configured their names are passed to the following stages via interface outputs, and can be leveraged to set up access or impersonation in IAM bindings.

CI/CD support is fully implemented for GitHub, Gitlab, and Cloud Source Repositories / Cloud Build. For GitHub, we also offer a [separate supporting setup](../0-organization-bootstrap/) to quickly create/configure repositories.

For details on how to configure both features, refer to the Customizations sections below on [Workload Identity Federation](#workload-identity-federation) and [CI/CD repositories](#cicd-repositories).

These features are optional and only enabled if the relevant variables have been populated.

## How to Run This Stage

For detailed information on prerequisites and steps to deploy this stage, please see the latest [stellar-engine Cloud Engineer Development Guide](https://docs.google.com/document/d/1o39QZ-K5CTP8FdTs9Jgz3JRF7HZ8in-1QoM0SCcIEAk/edit?tab=t.0#heading=h.tvlxzbk3nqgs) and scroll down to stellar-engine - Automation section. If you do not have access, you will have to request it.

## Customizations

Most variables (e.g. `billing_account` and `organization`) are only used to input actual values and should be self-explanatory. The only meaningful customizations that apply here are groups, and IAM roles.

### Group Names

As we mentioned above, groups reflect the convention used in the [GCP Enterprise Setup Checklist](https://cloud.google.com/docs/enterprise/setup-checklist), with an added level of indirection: the `groups` variable maps logical names to actual names, so that you don't need to delve into the code if your group names do not comply with the checklist convention.

Each group also has an individual variable (e.g., `gcp_vpc_network_admins_group`) to allow for easy overrides via environment variables.

For example, if your network admins team is called `network-admins@example.com`, you can set the name (minus the domain) in either the `groups` variable or the individual `gcp_vpc_network_admins_group` variable:

```hcl
# Option 1: Using the individual variable (easiest for environment variables)
gcp_vpc_network_admins_group = "network-admins"

# Option 2: Using the groups object
groups = {
  gcp-vpc-network-admins = "network-admins"
}
```

If your groups layout differs substantially from the checklist, define all relevant groups in the `groups` variable, then rearrange IAM roles in the code to match your setup.

### IAM

One other area where we directly support customizations is IAM. The code here, as in all stages, follows a simple pattern derived from best practices

- operational roles for humans are assigned to groups
- any other principal is a service account

In code, the distinction above reflects on how IAM bindings are specified in the underlying module variables

- group roles "for humans" always use `iam_groups` variables
- service account roles always use `iam` variables

This makes it easy to tweak user roles by adding mappings to the `iam_groups` variables of the relevant resources, without having to understand and deal with the details of service account roles.

One more critical difference in IAM bindings is between authoritative and additive:

- authoritative bindings have complete control on principals for a given role; this is the recommended best practice when a single automation actor controls the role, as it removes drift each time Terraform runs
- additive bindings have control only on given role/principal pairs, and need to be used whenever multiple automation actors need to control the role, as is the case for the network user role in Shared VPC setups, and many other situations

This stage groups all IAM definitions in the [organization-iam.tf](./organization-iam.tf) file, to allow easy parsing of roles assigned to each group and machine identity.

When customizations are needed, three stage-level variables allow injecting additional bindings to match the desired setup

- `group_iam` allows adding authoritative bindings for groups
- `iam` allows adding authoritative bindings for any type of supported principal, and is merged with the internal `iam` local and then with group bindings at the module level
- `iam_bindings_additive` allows adding individual role/member pairs, and also supports IAM conditions

Refer to the [project module](../../../modules/project/) for examples on how to use the IAM variables, and they are an interface shared across all our modules.

### Names and Naming Convention

Configuring the individual tokens for the naming convention described above, has varying degrees of complexity

- the static prefix can be set via the `prefix` variable once
- the environment identifier is set to `prod` as resources here influence production and are considered as such, and can be changed in `main.tf` locals

All other tokens are set directly in resource names, as providing abstractions to manage them would have added too much complexity to the code, making it less readable and more fragile.

If a different convention is needed, identify names via search/grep (e.g. with `^\s+name\s+=\s+"`) and change them in an editor it should take a couple of minutes at most, as there's just a handful of modules and resources to change.

Names used in internal references (e.g. `module.foo-prod.id`) are only used by Terraform and do not influence resource naming, so they are best left untouched to avoid having to debug complex errors.

### Workload Identity Federation

At any time during this stage's lifecycle you can configure a Workload Identity Federation pool, and one or more providers. These are part of this stage's interface, included in the automatically generated `.tfvars` files and accepted by the Resource Manager stage that follows.

The variable maps each provider's `issuer` attribute with the definitions in the `identity-providers.tf` file. We currently support GitHub and Gitlab directly, and extending to definitions to support more providers is trivial (send us a PR if you do!).

Provider key names are used by the `cicd_repositories` variable to configure authentication for CI/CD repositories, and generally from your Terraform code whenever you need to configure IAM access or impersonation for federated identities.

This is a sample configuration of a GitHub and a Gitlab provider. Every parameter is optional.

The `custom_settings` attributes are used to configure the provider to work with privately managed installations of Github and Gitlab

- `issuer_uri` (defaults to the public platforms one if not set)
- `audience` (defaults to the public URL of the provider if not set, as recommended in the [WIF FAQ section](https://cloud.google.com/iam/docs/best-practices-for-using-workload-identity-federation#provider-audience))
- `jwks_json` for public key upload

```tfvars
workload_identity_providers = {
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

### CI/CD Repositories

FAST is designed to directly support running in automated workflows from separate repositories for each stage. The `cicd_repositories` variable allows you to configure impersonation from external repositories leveraging Workload identity Federation, and pre-configures a FAST workflow file that can be used to validate and apply the code in each repository.

The repository design we support is fairly simple, with a repository for modules that enables centralization and versioning, and one repository for each stage optionally configured from the previous stage.

This is an example of configuring the bootstrap and resource management repositories in this stage. CI/CD configuration is optional, so the entire variable or any of its attributes can be set to null if not needed.

```tfvars
cicd_repositories = {
  bootstrap = {
    branch            = null
    identity_provider = "github-sample"
    name              = "my-gh-org/fast-bootstrap"
    type              = "github"
  }
  resman = {
    branch            = "main"
    identity_provider = "github-sample"
    name              = "my-gh-org/fast-resman"
    type              = "github"
  }
}
```

The `type` attribute can be set to one of the supported repository types: `github`, `gitlab`, or `sourcerepo`.

Once the stage is applied the generated output files will contain pre-configured workflow files for each repository, that will use Workload Identity Federation via a dedicated service account for each repository to impersonate the automation service account for the stage.

You can use Terraform to automate creation of the repositories using the extra stage defined in [fast/extras/0-cicd-github](../0-organization-bootstrap/) (only for Github for now).

The remaining configuration is manual, as it regards the repositories themselves

- create a repository for modules
  - clone and populate it with the Fabric modules
  - configure authentication to the modules repository
    - for GitHub
      - create a key pair
      - create a [deploy key](https://docs.github.com/en/developers/overview/managing-deploy-keys#deploy-keys) in the modules repository with the public key
      - create a `CICD_MODULES_KEY` secret with the private key in each of the repositories that need to access modules (for Gitlab, please Base64 encode the private key for masking)
    - for Gitlab
      - TODO
    - for Source Repositories
      - assign the reader role to the CI/CD service accounts
- create one repository for each stage
  - clone and populate them with the stage source
  - edit the modules source to match your modules repository
    - a simple way is using the "Replace in files" function of your editor
      - search for `source\s*= "../../../modules/([^"]+)"`
      - replace with:
        - modules stored on GitHub: `source = "git@github.com:my-org/fast-modules.git//$1?ref=v1.0"`
        - modules stored on Gitlab: `source = "git::ssh://git@gitlab.com/my-org/fast-modules.git//$1?ref=v1.0"`
        - modules stored on Source Repositories: `"source = git::https://source.developers.google.com/p/my-project/r/my-repository//$1?ref=v1.0"`. You may need to run `git config --global credential.'https://source.developers.google.com'.helper gcloud.sh` first as documented [here](https://cloud.google.com/source-repositories/docs/adding-repositories-as-remotes#add_the_repository_as_a_remote)
  - copy the generated workflow file for the stage from the GCS output files bucket or from the local clone if enabled
    - for GitHub, place it in a `.github/workflows` folder in the repository root
    - for Gitlab, rename it to `.gitlab-ci.yml` and place it in the repository root
    - for Source Repositories, place it in `.cloudbuild/workflow.yaml`

### Toggling features

Note: This is not currently officially supported in Stellar Engine Landing Zone, but is left in as an experimental feature.

Some FAST features can be enabled or disabled using the `fast_features` variables. While this variable is not directly used in the bootstrap stage, it can instruct the following stages to create certain resources only if needed.

The `fast_features` variable consists of 4 toggles

- **`data_platform`** controls the creation of required resources (Google Cloud Folders, service accounts, buckets, IAM bindings) to deploy the [3-data-platform](https://github.com/GoogleCloudPlatform/cloud-foundation-fabric/tree/master/fast/stages/3-data-platform) stage
- **`gke`** controls the creation of required resources (Google Cloud Folders, service accounts, buckets, IAM bindings) to deploy the [3-gke-multitenant](https://github.com/GoogleCloudPlatform/cloud-foundation-fabric/tree/master/fast/stages/3-gke-multitenant) stage
- **`project_factory`** controls the creation of required resources (Google Cloud Folders, service accounts, buckets, IAM bindings) to deploy the [3-project-factory](https://github.com/GoogleCloudPlatform/cloud-foundation-fabric/tree/master/fast/stages/3-project-factory) stage
- **`sandbox`** controls the creation of a "Sandbox" top level Google Cloud Folder with relaxed policies, intended for sandbox environments where users can experiment
- **`teams`** controls the creation of the top level "Teams" Google Cloud Folder used by the [teams feature in resman](https://github.com/GoogleCloudPlatform/cloud-foundation-fabric/tree/master/fast/stages/2-resman#team-folders).

---
<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [alert_email](variables.tf#L17) | Email to receive log alerts. | <code>string</code> | ✓ |  |
| [billing_account](variables.tf#L42) | Billing account id. If billing account is not part of the same org set `is_org_level` to `false`. To disable handling of billing IAM roles set `no_iam` to `true`. | <code title="object&#40;&#123;&#10;  id           &#61; string&#10;  is_org_level &#61; optional&#40;bool, true&#41;&#10;  no_iam       &#61; optional&#40;bool, false&#41;&#10;&#125;&#41;">object&#40;&#123;&#8230;&#125;&#41;</code> | ✓ |  |
| [bootstrap_project](variables.tf#L52) | Bootstrap project ID. | <code>string</code> | ✓ |  |
| [organization](variables.tf#L229) | Organization details. | <code title="object&#40;&#123;&#10;  id          &#61; number&#10;  domain      &#61; optional&#40;string&#41;&#10;  customer_id &#61; optional&#40;string&#41;&#10;&#125;&#41;">object&#40;&#123;&#8230;&#125;&#41;</code> | ✓ |  |
| [prefix](variables.tf#L244) | Prefix used for resources that need unique names. Use 9 characters or less. | <code>string</code> | ✓ |  |
| [top_level_folder](variables.tf#L297) | Top Level Folder Details. | <code title="object&#40;&#123;&#10;  name &#61; string&#10;  id   &#61; string&#10;&#125;&#41;">object&#40;&#123;&#8230;&#125;&#41;</code> | ✓ |  |
| [apply_tier_1_pubsub_sink](variables.tf#L22) | Toggles whether to apply org tier-1 pubsub sink. | <code>bool</code> |  | <code>true</code> |
| [assured_workloads](variables.tf#L29) | Configuration for Assured Workloads. | <code title="object&#40;&#123;&#10;  regime   &#61; string&#10;  location &#61; string&#10;&#125;&#41;">object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code title="&#123;&#10;  regime   &#61; &#34;IL5&#34;&#10;  location &#61; &#34;US&#34;&#10;&#125;">&#123;&#8230;&#125;</code> |
| [bootstrap_user](variables.tf#L57) | Email of the nominal user running this stage for the first time. | <code>string</code> |  | <code>null</code> |
| [cicd_repositories](variables.tf#L63) | CI/CD repository configuration. Identity providers reference keys in the `federated_identity_providers` variable. Set to null to disable, or set individual repositories to null if not needed. | <code title="object&#40;&#123;&#10;  bootstrap &#61; optional&#40;object&#40;&#123;&#10;    name              &#61; string&#10;    type              &#61; string&#10;    branch            &#61; optional&#40;string&#41;&#10;    identity_provider &#61; optional&#40;string&#41;&#10;  &#125;&#41;&#41;&#10;  resman &#61; optional&#40;object&#40;&#123;&#10;    name              &#61; string&#10;    type              &#61; string&#10;    branch            &#61; optional&#40;string&#41;&#10;    identity_provider &#61; optional&#40;string&#41;&#10;  &#125;&#41;&#41;&#10;  tenant &#61; optional&#40;object&#40;&#123;&#10;    name              &#61; string&#10;    type              &#61; string&#10;    branch            &#61; optional&#40;string&#41;&#10;    identity_provider &#61; optional&#40;string&#41;&#10;  &#125;&#41;&#41;&#10;&#125;&#41;">object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>null</code> |
| [essential_contacts](variables.tf#L115) | Email used for essential contacts, unset if null. | <code>string</code> |  | <code>null</code> |
| [factories_config](variables.tf#L121) | Configuration for the resource factories or external data. | <code title="object&#40;&#123;&#10;  checklist_data    &#61; optional&#40;string&#41;&#10;  checklist_org_iam &#61; optional&#40;string&#41;&#10;  custom_roles      &#61; optional&#40;string, &#34;data&#47;custom-roles&#34;&#41;&#10;  org_policy        &#61; optional&#40;string, &#34;data&#47;org-policies&#34;&#41;&#10;&#125;&#41;">object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>&#123;&#125;</code> |
| [fast_features](variables.tf#L133) | Selective control for top-level FAST features. | <code title="object&#40;&#123;&#10;  data_platform   &#61; optional&#40;bool, false&#41;&#10;  gcve            &#61; optional&#40;bool, false&#41;&#10;  gke             &#61; optional&#40;bool, false&#41;&#10;  project_factory &#61; optional&#40;bool, false&#41;&#10;  sandbox         &#61; optional&#40;bool, false&#41;&#10;  teams           &#61; optional&#40;bool, false&#41;&#10;  envs            &#61; optional&#40;bool, false&#41;&#10;&#125;&#41;">object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>&#123;&#125;</code> |
| [gcp_billing_admins_group](variables.tf#L148) | GCP Billing Admins group name. | <code>string</code> |  | <code>&#34;gcp-billing-admins&#34;</code> |
| [gcp_devops_group](variables.tf#L154) | GCP DevOps group name. | <code>string</code> |  | <code>&#34;gcp-devops&#34;</code> |
| [gcp_organization_admins_group](variables.tf#L160) | GCP Organization Admins group name. | <code>string</code> |  | <code>&#34;gcp-organization-admins&#34;</code> |
| [gcp_security_admins_group](variables.tf#L166) | GCP Security Admins group name. | <code>string</code> |  | <code>&#34;gcp-security-admins&#34;</code> |
| [gcp_support_group](variables.tf#L172) | GCP Support group name. | <code>string</code> |  | <code>null</code> |
| [gcp_vpc_network_admins_group](variables.tf#L178) | GCP VPC Network Admins group name. | <code>string</code> |  | <code>&#34;gcp-vpc-network-admins&#34;</code> |
| [groups](variables.tf#L184) | Group names or IAM-format principals to grant organization-level permissions. If just the name is provided, the 'group:' principal and organization domain are interpolated. | <code title="object&#40;&#123;&#10;  gcp-billing-admins      &#61; optional&#40;string&#41;&#10;  gcp-devops              &#61; optional&#40;string&#41;&#10;  gcp-vpc-network-admins  &#61; optional&#40;string&#41;&#10;  gcp-organization-admins &#61; optional&#40;string&#41;&#10;  gcp-security-admins     &#61; optional&#40;string&#41;&#10;  gcp-support &#61; optional&#40;string&#41;&#10;&#125;&#41;">object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>&#123;&#125;</code> |
| [locations](variables.tf#L200) | Optional locations for GCS, BigQuery, and logging buckets created here. | <code title="object&#40;&#123;&#10;  bq      &#61; optional&#40;string, &#34;US&#34;&#41;&#10;  gcs     &#61; optional&#40;list&#40;string&#41;, &#91;&#34;US&#34;&#93;&#41;&#10;  logging &#61; optional&#40;list&#40;string&#41;, &#91;&#34;global&#34;&#93;&#41;&#10;  pubsub  &#61; optional&#40;list&#40;string&#41;, &#91;&#93;&#41;&#10;  kms     &#61; optional&#40;list&#40;string&#41;, &#91;&#34;US&#34;&#93;&#41;&#10;&#125;&#41;">object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>&#123;&#125;</code> |
| [log_sinks](variables.tf#L213) | Organization-level log sinks configuration. | <code title="map&#40;object&#40;&#123;&#10;  filter &#61; string&#10;  type   &#61; string&#10;&#125;&#41;&#41;">map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> |  | <code>&#123;&#125;</code> |
| [logging_kms_key](variables.tf#L223) | value of the KMS key used for logging. | <code>string</code> |  | <code>null</code> |
| [outputs_location](variables.tf#L238) | Enable writing provider, tfvars and CI/CD workflow files to local filesystem. Leave null to disable. | <code>string</code> |  | <code>null</code> |
| [project_parent_ids](variables.tf#L253) | Optional parents for projects created here in folders/nnnnnnn format. Null values will use the organization as parent. | <code title="object&#40;&#123;&#10;  automation &#61; optional&#40;string&#41;&#10;  billing    &#61; optional&#40;string&#41;&#10;  logging    &#61; optional&#40;string&#41;&#10;&#125;&#41;">object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>&#123;&#125;</code> |
| [regime_mapping](variables.tf#L264) | Mapping of compliance regime names to short codes. | <code>map&#40;string&#41;</code> |  | <code title="&#123;&#10;  &#34;COMPLIANCE_REGIME_UNSPECIFIED&#34; &#61; &#34;CRU&#34;&#10;  &#34;IL2&#34;                           &#61; &#34;IL2&#34;&#10;  &#34;IL4&#34;                           &#61; &#34;IL4&#34;&#10;  &#34;IL5&#34;                           &#61; &#34;IL5&#34;&#10;  &#34;FEDRAMP_HIGH&#34;                  &#61; &#34;FRH&#34;&#10;  &#34;FEDRAMP_MODERATE&#34;              &#61; &#34;FRM&#34;&#10;  &#34;CJIS&#34;                                              &#61; &#34;CJIS&#34;&#10;  &#34;US_REGIONAL_ACCESS&#34;                                &#61; &#34;USRE&#34;&#10;  &#34;HIPAA&#34;                                             &#61; &#34;HIPAA&#34;&#10;  &#34;HITRUST&#34;                                           &#61; &#34;HITRUST&#34;&#10;  &#34;EU_REGIONS_AND_SUPPORT&#34;                            &#61; &#34;EURS&#34;&#10;  &#34;CA_REGIONS_AND_SUPPORT&#34;                            &#61; &#34;CARS&#34;&#10;  &#34;ITAR&#34;                                              &#61; &#34;ITAR&#34;&#10;  &#34;AU_REGIONS_AND_US_SUPPORT&#34;                         &#61; &#34;AUUSRS&#34;&#10;  &#34;ASSURED_WORKLOADS_FOR_PARTNERS&#34;                    &#61; &#34;PART&#34;&#10;  &#34;ISR_REGIONS&#34;                                       &#61; &#34;ISR&#34;&#10;  &#34;ISR_REGIONS_AND_SUPPORT&#34;                           &#61; &#34;ISRSUPP&#34;&#10;  &#34;CA_PROTECTED_B&#34;                                    &#61; &#34;CA_PROT_B&#34;&#10;  &#34;JP_REGIONS_AND_SUPPORT&#34;                            &#61; &#34;JP_REGIONS&#34;&#10;  &#34;KSA_REGIONS_AND_SUPPORT_WITH_SOVEREIGNTY_CONTROLS&#34; &#61; &#34;KSA_SOV&#34;&#10;  &#34;REGIONAL_CONTROLS&#34;                                 &#61; &#34;REGIONAL&#34;&#10;  &#34;HEALTHCARE_AND_LIFE_SCIENCES_CONTROLS&#34;             &#61; &#34;HCLS&#34;&#10;  &#34;HEALTHCARE_AND_LIFE_SCIENCES_CONTROLS_US_SUPPORT&#34;  &#61; &#34;HCLS_US&#34;&#10;  &#34;IRS_1075&#34;                                          &#61; &#34;IRS_1075&#34;&#10;  &#34;CANADA_CONTROLLED_GOODS&#34;                           &#61; &#34;CAGOODS&#34;&#10;&#125;">&#123;&#8230;&#125;</code> |
| [workload_identity_providers](variables.tf#L305) | Workload Identity Federation pools. The `cicd_repositories` variable references keys here. | <code title="map&#40;object&#40;&#123;&#10;  attribute_condition &#61; optional&#40;string&#41;&#10;  issuer              &#61; string&#10;  custom_settings &#61; optional&#40;object&#40;&#123;&#10;    issuer_uri &#61; optional&#40;string&#41;&#10;    audiences  &#61; optional&#40;list&#40;string&#41;, &#91;&#93;&#41;&#10;    jwks_json  &#61; optional&#40;string&#41;&#10;  &#125;&#41;, &#123;&#125;&#41;&#10;&#125;&#41;&#41;">map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> |  | <code>&#123;&#125;</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [alert_email](outputs.tf#L155) | Email to receive log alerts. |  |
| [assured_workload](outputs.tf#L160) | Assured Workload folder for the deployment. |  |
| [automation](outputs.tf#L165) | Automation resources. |  |
| [automation_project_id](outputs.tf#L170) | The ID of the IaC Core project. |  |
| [billing_dataset](outputs.tf#L175) | BigQuery dataset prepared for billing export. |  |
| [cicd_repositories](outputs.tf#L180) | CI/CD repository configurations. |  |
| [common_services_folder](outputs.tf#L192) | Common services folder where non-tenant related resources should be kept. |  |
| [custom_roles](outputs.tf#L197) | Organization-level custom roles. |  |
| [folder_ids](outputs.tf#L202) | The Assured Workloads Folder i.e. DEV (IL5 AW). |  |
| [outputs_bucket](outputs.tf#L207) | GCS bucket where generated output files are stored. |  |
| [project_ids](outputs.tf#L212) | Projects created by this stage. |  |
| [providers](outputs.tf#L222) | Terraform provider files for this stage and dependent stages. | ✓ |
| [pubsub-topics-id](outputs.tf#L229) | Pubsub topics used for C5ISR logging. |  |
| [service_accounts](outputs.tf#L236) | Automation service accounts created by this stage. |  |
| [shared_services_project_id](outputs.tf#L245) | Project ID for NetSec Shared Services. |  |
| [tenants_container_ids](outputs.tf#L259) | Folder IDs for the 'Tenants' sub-folders where tenant projects will live. |  |
| [tfvars](outputs.tf#L264) | Terraform variable files for the following stages. | ✓ |
| [workload_identity_pool](outputs.tf#L270) | Workload Identity Federation pool and providers. |  |
<!-- END TFDOC -->
