# Google Cloud Organization Bootstrap

The purpose of this stage is to enable critical Google Cloud Organization level functionalities that depend on broad administrative permissions, and prepare the prerequisites needed to enable automation in this and future stages. In addition, this stage ensures that all future fast stages are compliant with the selected compliance regime.

<!-- BEGIN TOC -->
- [Design Overview and Choices](#design-overview-and-choices)
  - [Assured Workloads](#assured-workloads)
  - [User Groups](#user-groups)
  - [Google Cloud Organization Level IAM](#google-cloud-organization-level-iam)
  - [Google Cloud Organization Policies and Tag-Based Conditions](#google-cloud-organization-policies-and-tag-based-conditions)
  - [Automation Google Cloud Project and Resources](#automation-google-cloud-project-and-resources)
  - [Billing Account](#billing-account)
  - [Google Cloud Organization Level Logging](#google-cloud-organization-level-logging)
  - [Naming](#naming)
  - [Workforce Identity Federation](#workforce-identity-federation)
  - [Workload Identity Federation and CI/CD](#workload-identity-federation-and-cicd)
- [How to Run This Stage](#how-to-run-this-stage)
- [Customizations](#customizations)
  - [Group Names](#group-names)
  - [IAM](#iam)
  - [Log Sinks and Log Destinations](#log-sinks-and-log-destinations)
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

We have standardized the initial set of groups on those outlined in the [GCP Enterprise Setup Checklist](https://cloud.google.com/docs/enterprise/setup-checklist) to simplify adoption. They provide a comprehensive and flexible starting point that can suit most users. Adding new groups, or deviating from the initial setup is  possible and reasonably simple, and it's briefly outlined in the customization section below.

### Google Cloud Organization Level IAM

The service account used in the [Resource Management stage](../1-resman) needs to be able to grant specific permissions at the Google Cloud Organization level, to enable specific functionality for subsequent stages that deal with network or security resources, or billing-related activities.

In order to be able to assign those roles without having the full authority of the Google Cloud Organization Admin role, this stage defines a custom role that only allows setting IAM policies on the Google Cloud Organization, and grants it via a [delegated role grant](https://cloud.google.com/iam/docs/setting-limits-on-granting-roles) that only allows it to be used to grant a limited subset of roles.

In this way, the Resource Management service account can effectively act as a Google Cloud Organization Admin, but only to grant the specific roles it needs to control.

One consequence of the above setup is the need to configure IAM bindings that can be assigned via the condition as non-authoritative, since those same roles are effectively under the control of two stages: this one and Resource Management. Using authoritative bindings for these roles (instead of non-authoritative ones) would generate potential conflicts, where each stage could try to overwrite and negate the bindings applied by the other at each `apply` cycle.

A full reference of IAM roles managed by this stage [is available here](./IAM.md).

### Google Cloud Organization Policies and Tag-Based Conditions

It's often desirable to have Google Cloud Organization policies deployed before any other resource in the org, so as to ensure compliance with specific requirements (e.g. location restrictions), or control the configuration of specific resources (e.g. default network at Google Cloud Project creation or service account grants).

Google Cloud Organization policy exceptions are managed via a dedicated resource management tag hierarchy, rooted in the `org-policies` tag key. A default condition is already present for the `iam.allowedPolicyMemberDomains` constraint, that relaxes the policy on resources that have the `org-policies/allowed-policy-member-domains-all` tag value bound or inherited.

Further tag values can be defined via the `org_policies_config.tag_values` variable, and IAM access can be granted on them via the same variable. Once a tag value has been created, its id can be used in constraint rule conditions.

Management of the rest of the tag hierarchy is delegated to the resource management stage, as that is often intimately tied to the Google Cloud Folder hierarchy design.

The Google Cloud Organization policy tag key and values managed by this stage have been added to the `0-bootstrap.auto.tfvars` stage, so that IAM can be delegated to the resource management or successive stages via their ids.

The following example shows an example on how to define an additional tag value, and use it in a boolean constraint rule.

This snippet defines a new tag value under the `org-policies` tag key via the `org_policies_config` variable, and assigns the permission to bind it to a group.

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

The above tag can be used to define a constraint condition via the `data/org-policies/compute.yaml` or similar factory file. The id in the condition is the Google Cloud Organization id, followed by the name of the Google Cloud Organization policy tag key (defaults to `org-policies`).

```yaml
compute.requireOsLogin:
  rules:
  - enforce: true
  - enforce: false
    condition:
      expression: resource.matchTag('12345678/org-policies-config', 'compute-require-oslogin-false')
```

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

### Google Cloud Organization Level Logging

We create Google Cloud Organization level log sinks early in the bootstrap process to ensure a proper audit trail is in place from the very beginning. By default, we provide log filters to capture [Cloud Audit Logs](https://cloud.google.com/logging/docs/audit), [VPC Service Controls violations](https://cloud.google.com/vpc-service-controls/docs/troubleshooting#vpc-sc-errors) and [Workspace Logs](https://cloud.google.com/logging/docs/audit/configure-gsuite-audit-logs) into logging buckets in the top-level audit logging Google Cloud Project. In addition, a log sink with an empty filter is included to comply with [Center for Internet Security (CIS) Benchmarks](https://cloud.google.com/security/compliance/cis) related to log sinks.

The [Customizations](#log-sinks-and-log-destinations) section explains how to change the logs captured and their destination.

### Naming

We are intentionally not supporting random prefix/suffixes for names, as that is an antipattern typically only used in development. It does not map to our customer's actual production usage, where they always adopt a fixed naming convention.

What is implemented here is a fairly common convention, composed of tokens ordered by relative importance

- an Google Cloud Organization level static prefix less or equal to 9 characters (e.g. `myco` or `myco-gcp`)
- an environment identifier (e.g. `prod`)
- a team/owner identifier (e.g. `sec` for Security)
- a context identifier (e.g. `core` or `kms`)
- an arbitrary identifier used to distinguish similar resources (e.g. `0`, `1`)

Tokens are joined by a `-` character, making it easy to separate the individual tokens visually, and to programmatically split them in billing exports to derive initial high-level groupings for cost attribution.

The convention is used in its full form only for specific resources with globally unique names (Google Cloud Projects, GCS buckets). Other resources adopt a shorter version for legibility, as the full context can always be derived from their Google Cloud Project.

The [Customizations](#names-and-naming-convention) section on names below explains how to configure tokens, or implement a different naming convention.

### Workforce Identity Federation

This stage supports configuration of [Workforce Identity Federation](https://cloud.google.com/iam/docs/workforce-identity-federation) which lets an external identity provider (IdP) to authenticate and authorize a group of users (usually employees) using IAM, so that the users can access Google Cloud services.

The following example shows an example on how to define a Workforce Identity pool for the Google Cloud Organization.

```hcl
# stage 0 wif tfvars
workforce_identity_providers = {
  test = {
    issuer       = "azuread"
    display_name = "wif-provider"
    description  = "Workforce Identity pool"
    saml         = {
      idp_metadata_xml = "<?xml version=\"1.0\" encoding=\"utf-8\"?>..."
    }
  }
}
```

### Workload Identity Federation and CI/CD

This stage also implements initial support for two interrelated features

- configuration of [Workload Identity Federation](https://cloud.google.com/iam/docs/workload-identity-federation) pools and providers
- configuration of CI/CD repositories to allow impersonation via Workload identity Federation, and stage running via provided workflow templates

Workload Identity Federation support allows configuring external providers independently from CI/CD, and offers predefined attributes for a few well known ones (more can be easily added by editing the `identity-providers.tf` file). Once providers have been configured their names are passed to the following stages via interface outputs, and can be leveraged to set up access or impersonation in IAM bindings.

CI/CD support is fully implemented for GitHub, Gitlab, and Cloud Source Repositories / Cloud Build. For GitHub, we also offer a [separate supporting setup](../../extras/0-cicd-github/) to quickly create/configure repositories.

For details on how to configure both features, refer to the Customizations sections below on [Workload Identity Federation](#workload-identity-federation) and [CI/CD repositories](#cicd-repositories).

These features are optional and only enabled if the relevant variables have been populated.

## How to Run This Stage

For detailed information on prerequisites and steps to deploy this stage, please see the latest [Detailed Deployment Guide (DDG)](https://drive.google.com/drive/u/0/folders/1OLgdf_VnY8zdkcmxHPwhEVoidGAqY6PX) If you do not have access, you will have to request it.

## Customizations

Most variables (e.g. `billing_account` and `organization`) are only used to input actual values and should be self-explanatory. The only meaningful customizations that apply here are groups, and IAM roles.

### Group Names

As we mentioned above, groups reflect the convention used in the [GCP Enterprise Setup Checklist](https://cloud.google.com/docs/enterprise/setup-checklist), with an added level of indirection: the `groups` variable maps logical names to actual names, so that you don't need to delve into the code if your group names do not comply with the checklist convention.

For example, if your network admins team is called `net-rockstars@example.com`, simply set that name in the variable, minus the domain which is interpolated internally with the Google Cloud Organization domain:

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

### Log Sinks and Log Destinations

You can customize Google Cloud Organization level logs through the `log_sinks` variable in two ways

- creating additional log sinks to capture more logs
- changing the destination of captured logs

By default, all logs are exported to a log bucket, but FAST can create sinks to BigQuery, GCS, or PubSub.

If you need to capture additional logs, please refer to GCP's documentation on [scenarios for exporting logging data](https://cloud.google.com/architecture/exporting-stackdriver-logging-for-security-and-access-analytics), where you can find ready-made filter expressions for different use cases.

### Names and Naming Convention

Configuring the individual tokens for the naming convention described above, has varying degrees of complexity

- the static prefix can be set via the `prefix` variable once
- the environment identifier is set to `prod` as resources here influence production and are considered as such, and can be changed in `main.tf` locals

All other tokens are set directly in resource names, as providing abstractions to manage them would have added too much complexity to the code, making it less readable and more fragile.

If a different convention is needed, identify names via search/grep (e.g. with `^\s+name\s+=\s+"`) and change them in an editor it should take a couple of  minutes at most, as there's just a handful of modules and resources to change.

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

You can use Terraform to automate creation of the repositories using the extra stage defined in [fast/extras/0-cicd-github](../../extras/0-cicd-github/) (only for Github for now).

The remaining configuration is manual, as it regards the repositories themselves

- create a repository for modules
  - clone and populate it with the Fabric modules
  - configure authentication to the modules repository
    - for GitHub
      - create a key pair
      - create a [deploy key](https://docs.github.com/en/developers/overview/managing-deploy-keys#deploy-keys) in the modules repository with the public key
      - create a `CICD_MODULES_KEY` secret with the private key in each of the repositories that need to access modules (for Gitlab, please Base64 encode the private key for masking)
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

Note: This is not currently officially supported in Stellar Engine, but is left in as an experimental feature.

Some FAST features can be enabled or disabled using the `fast_features` variables. While this variable is not directly used in the bootstrap stage, it can instruct the following stages to create certain resources only if needed.

The `fast_features` variable consists of 4 toggles

- **`data_platform`** controls the creation of required resources (Google Cloud Folders, service accounts, buckets, IAM bindings) to deploy the [3-data-platform](https://github.com/GoogleCloudPlatform/cloud-foundation-fabric/tree/master/fast/stages/3-data-platform) stage
- **`gke`** controls the creation of required resources (Google Cloud Folders, service accounts, buckets, IAM bindings) to deploy the [3-gke-multitenant](https://github.com/GoogleCloudPlatform/cloud-foundation-fabric/tree/master/fast/stages/3-gke-multitenant) stage
- **`project_factory`** controls the creation of required resources (Google Cloud Folders, service accounts, buckets, IAM bindings) to deploy the [3-project-factory](https://github.com/GoogleCloudPlatform/cloud-foundation-fabric/tree/master/fast/stages/3-project-factory) stage
- **`sandbox`** controls the creation of a "Sandbox" top level Google Cloud Folder with relaxed policies, intended for sandbox environments where users can experiment
- **`teams`** controls the creation of the top level "Teams" Google Cloud Folder used by the [teams feature in resman](https://github.com/GoogleCloudPlatform/cloud-foundation-fabric/tree/master/fast/stages/1-resman#team-folders).

---
<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [alert_email](variables.tf#L16) | Email to receive log alerts. | <code>string</code> | ✓ |  |
| [billing_account](variables.tf#L34) | Billing account id. If billing account is not part of the same org set `is_org_level` to `false`. To disable handling of billing IAM roles set `no_iam` to `true`. | <code title="object&#40;&#123;&#10;  id           &#61; string&#10;  is_org_level &#61; optional&#40;bool, true&#41;&#10;  no_iam       &#61; optional&#40;bool, false&#41;&#10;&#125;&#41;">object&#40;&#123;&#8230;&#125;&#41;</code> | ✓ |  |
| [bootstrap_project](variables.tf#L44) | Bootstrap project ID. | <code>string</code> | ✓ |  |
| [organization](variables.tf#L260) | Organization details. | <code title="object&#40;&#123;&#10;  id          &#61; number&#10;  domain      &#61; optional&#40;string&#41;&#10;  customer_id &#61; optional&#40;string&#41;&#10;&#125;&#41;">object&#40;&#123;&#8230;&#125;&#41;</code> | ✓ |  |
| [prefix](variables.tf#L275) | Prefix used for resources that need unique names. Use 9 characters or less. | <code>string</code> | ✓ |  |
| [assured_workloads](variables.tf#L21) | Configuration for Assured Workloads. | <code title="object&#40;&#123;&#10;  regime   &#61; string&#10;  location &#61; string&#10;&#125;&#41;">object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code title="&#123;&#10;  regime   &#61; &#34;IL5&#34;&#10;  location &#61; &#34;US&#34;&#10;&#125;">&#123;&#8230;&#125;</code> |
| [bootstrap_user](variables.tf#L49) | Email of the nominal user running this stage for the first time. | <code>string</code> |  | <code>null</code> |
| [cicd_repositories](variables.tf#L55) | CI/CD repository configuration. Identity providers reference keys in the `federated_identity_providers` variable. Set to null to disable, or set individual repositories to null if not needed. | <code title="object&#40;&#123;&#10;  bootstrap &#61; optional&#40;object&#40;&#123;&#10;    name              &#61; string&#10;    type              &#61; string&#10;    branch            &#61; optional&#40;string&#41;&#10;    identity_provider &#61; optional&#40;string&#41;&#10;  &#125;&#41;&#41;&#10;  resman &#61; optional&#40;object&#40;&#123;&#10;    name              &#61; string&#10;    type              &#61; string&#10;    branch            &#61; optional&#40;string&#41;&#10;    identity_provider &#61; optional&#40;string&#41;&#10;  &#125;&#41;&#41;&#10;&#125;&#41;">object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>null</code> |
| [custom_roles](variables.tf#L101) | Map of role names => list of permissions to additionally create at the organization level. | <code>map&#40;list&#40;string&#41;&#41;</code> |  | <code>&#123;&#125;</code> |
| [essential_contacts](variables.tf#L108) | Email used for essential contacts, unset if null. | <code>string</code> |  | <code>null</code> |
| [factories_config](variables.tf#L114) | Configuration for the resource factories or external data. | <code title="object&#40;&#123;&#10;  checklist_data    &#61; optional&#40;string&#41;&#10;  checklist_org_iam &#61; optional&#40;string&#41;&#10;  custom_roles      &#61; optional&#40;string, &#34;data&#47;custom-roles&#34;&#41;&#10;  org_policy        &#61; optional&#40;string, &#34;data&#47;org-policies&#34;&#41;&#10;&#125;&#41;">object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>&#123;&#125;</code> |
| [fast_features](variables.tf#L126) | Selective control for top-level FAST features. | <code title="object&#40;&#123;&#10;  data_platform   &#61; optional&#40;bool, false&#41;&#10;  gcve            &#61; optional&#40;bool, false&#41;&#10;  gke             &#61; optional&#40;bool, false&#41;&#10;  project_factory &#61; optional&#40;bool, false&#41;&#10;  sandbox         &#61; optional&#40;bool, false&#41;&#10;  teams           &#61; optional&#40;bool, false&#41;&#10;  envs            &#61; optional&#40;bool, false&#41;&#10;&#125;&#41;">object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>&#123;&#125;</code> |
| [groups](variables.tf#L141) | Group names or IAM-format principals to grant organization-level permissions. If just the name is provided, the 'group:' principal and organization domain are interpolated. | <code title="object&#40;&#123;&#10;  gcp-billing-admins      &#61; optional&#40;string, &#34;gcp-billing-admins&#34;&#41;&#10;  gcp-devops              &#61; optional&#40;string, &#34;gcp-devops&#34;&#41;&#10;  gcp-vpc-network-admins  &#61; optional&#40;string, &#34;gcp-vpc-network-admins&#34;&#41;&#10;  gcp-organization-admins &#61; optional&#40;string, &#34;gcp-organization-admins&#34;&#41;&#10;  gcp-security-admins     &#61; optional&#40;string, &#34;gcp-security-admins&#34;&#41;&#10;  gcp-support &#61; optional&#40;string, &#34;gcp-devops&#34;&#41;&#10;&#125;&#41;">object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>&#123;&#125;</code> |
| [iam](variables.tf#L157) | Organization-level custom IAM settings in role => [principal] format. | <code>map&#40;list&#40;string&#41;&#41;</code> |  | <code>&#123;&#125;</code> |
| [iam_bindings_additive](variables.tf#L164) | Organization-level custom additive IAM bindings. Keys are arbitrary. | <code title="map&#40;object&#40;&#123;&#10;  member &#61; string&#10;  role   &#61; string&#10;  condition &#61; optional&#40;object&#40;&#123;&#10;    expression  &#61; string&#10;    title       &#61; string&#10;    description &#61; optional&#40;string&#41;&#10;  &#125;&#41;&#41;&#10;&#125;&#41;&#41;">map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> |  | <code>&#123;&#125;</code> |
| [iam_by_principals](variables.tf#L179) | Authoritative IAM binding in {PRINCIPAL => [ROLES]} format. Principals need to be statically defined to avoid cycle errors. Merged internally with the `iam` variable. | <code>map&#40;list&#40;string&#41;&#41;</code> |  | <code>&#123;&#125;</code> |
| [locations](variables.tf#L186) | Optional locations for GCS, BigQuery, and logging buckets created here. | <code title="object&#40;&#123;&#10;  bq      &#61; optional&#40;string, &#34;US&#34;&#41;&#10;  gcs     &#61; optional&#40;string, &#34;US&#34;&#41;&#10;  logging &#61; optional&#40;string, &#34;global&#34;&#41;&#10;  pubsub  &#61; optional&#40;list&#40;string&#41;, &#91;&#93;&#41;&#10;  kms     &#61; optional&#40;string, &#34;US&#34;&#41;&#10;&#125;&#41;">object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>&#123;&#125;</code> |
| [log_sinks](variables.tf#L202) | Org-level log sinks, in name => {type, filter} format. | <code title="map&#40;object&#40;&#123;&#10;  filter &#61; string&#10;  type   &#61; string&#10;&#125;&#41;&#41;">map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> |  | <code title="&#123;&#10;  audit-logs &#61; &#123;&#10;    filter &#61; &#34;logName:&#92;&#34;&#47;logs&#47;cloudaudit.googleapis.com&#37;2Factivity&#92;&#34; OR logName:&#92;&#34;&#47;logs&#47;cloudaudit.googleapis.com&#37;2Fsystem_event&#92;&#34; OR protoPayload.metadata.&#64;type&#61;&#92;&#34;type.googleapis.com&#47;google.cloud.audit.TransparencyLog&#92;&#34;&#34;&#10;    type   &#61; &#34;logging&#34;&#10;  &#125;&#10;  vpc-sc &#61; &#123;&#10;    filter &#61; &#34;protoPayload.metadata.&#64;type&#61;&#92;&#34;type.googleapis.com&#47;google.cloud.audit.VpcServiceControlAuditMetadata&#92;&#34;&#34;&#10;    type   &#61; &#34;logging&#34;&#10;  &#125;&#10;  workspace-audit-logs &#61; &#123;&#10;    filter &#61; &#34;logName:&#92;&#34;&#47;logs&#47;cloudaudit.googleapis.com&#37;2Fdata_access&#92;&#34; and protoPayload.serviceName:&#92;&#34;login.googleapis.com&#92;&#34;&#34;&#10;    type   &#61; &#34;logging&#34;&#10;  &#125;&#10;  empty-audit-logs &#61; &#123;&#10;    filter &#61; &#34;&#34;&#10;    type   &#61; &#34;logging&#34;&#10;  &#125;&#10;&#125;">&#123;&#8230;&#125;</code> |
| [logging_kms_key](variables.tf#L237) | value of the KMS key used for logging. | <code>string</code> |  | <code>null</code> |
| [org_policies_config](variables.tf#L243) | Organization policies customization. | <code title="object&#40;&#123;&#10;  constraints &#61; optional&#40;object&#40;&#123;&#10;    allowed_policy_member_domains &#61; optional&#40;list&#40;string&#41;, &#91;&#93;&#41;&#10;  &#125;&#41;, &#123;&#125;&#41;&#10;  import_defaults &#61; optional&#40;bool, false&#41;&#10;  tag_name        &#61; optional&#40;string, &#34;org-policies&#34;&#41;&#10;  tag_values &#61; optional&#40;map&#40;object&#40;&#123;&#10;    description &#61; optional&#40;string, &#34;Managed by the Terraform organization module.&#34;&#41;&#10;    iam         &#61; optional&#40;map&#40;list&#40;string&#41;&#41;, &#123;&#125;&#41;&#10;    id          &#61; optional&#40;string&#41;&#10;  &#125;&#41;&#41;, &#123;&#125;&#41;&#10;&#125;&#41;">object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>&#123;&#125;</code> |
| [outputs_location](variables.tf#L269) | Enable writing provider, tfvars and CI/CD workflow files to local filesystem. Leave null to disable. | <code>string</code> |  | <code>null</code> |
| [project_parent_ids](variables.tf#L284) | Optional parents for projects created here in folders/nnnnnnn format. Null values will use the organization as parent. | <code title="object&#40;&#123;&#10;  automation &#61; optional&#40;string&#41;&#10;  billing    &#61; optional&#40;string&#41;&#10;  logging    &#61; optional&#40;string&#41;&#10;&#125;&#41;">object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>&#123;&#125;</code> |
| [regime_mapping](variables.tf#L295) | Mapping of compliance regime names to short codes. | <code>map&#40;string&#41;</code> |  | <code title="&#123;&#10;  &#34;COMPLIANCE_REGIME_UNSPECIFIED&#34; &#61; &#34;CRU&#34;&#10;  &#34;IL2&#34;                           &#61; &#34;IL2&#34;&#10;  &#34;IL4&#34;                           &#61; &#34;IL4&#34;&#10;  &#34;IL5&#34;                           &#61; &#34;IL5&#34;&#10;  &#34;FEDRAMP_HIGH&#34;                  &#61; &#34;FRH&#34;&#10;  &#34;FEDRAMP_MODERATE&#34;              &#61; &#34;FRM&#34;&#10;  &#34;CJIS&#34;                                              &#61; &#34;CJIS&#34;&#10;  &#34;US_REGIONAL_ACCESS&#34;                                &#61; &#34;USRE&#34;&#10;  &#34;HIPAA&#34;                                             &#61; &#34;HIPAA&#34;&#10;  &#34;HITRUST&#34;                                           &#61; &#34;HITRUST&#34;&#10;  &#34;EU_REGIONS_AND_SUPPORT&#34;                            &#61; &#34;EURS&#34;&#10;  &#34;CA_REGIONS_AND_SUPPORT&#34;                            &#61; &#34;CARS&#34;&#10;  &#34;ITAR&#34;                                              &#61; &#34;ITAR&#34;&#10;  &#34;AU_REGIONS_AND_US_SUPPORT&#34;                         &#61; &#34;AUUSRS&#34;&#10;  &#34;ASSURED_WORKLOADS_FOR_PARTNERS&#34;                    &#61; &#34;PART&#34;&#10;  &#34;ISR_REGIONS&#34;                                       &#61; &#34;ISR&#34;&#10;  &#34;ISR_REGIONS_AND_SUPPORT&#34;                           &#61; &#34;ISRSUPP&#34;&#10;  &#34;CA_PROTECTED_B&#34;                                    &#61; &#34;CA_PROT_B&#34;&#10;  &#34;JP_REGIONS_AND_SUPPORT&#34;                            &#61; &#34;JP_REGIONS&#34;&#10;  &#34;KSA_REGIONS_AND_SUPPORT_WITH_SOVEREIGNTY_CONTROLS&#34; &#61; &#34;KSA_SOV&#34;&#10;  &#34;REGIONAL_CONTROLS&#34;                                 &#61; &#34;REGIONAL&#34;&#10;  &#34;HEALTHCARE_AND_LIFE_SCIENCES_CONTROLS&#34;             &#61; &#34;HCLS&#34;&#10;  &#34;HEALTHCARE_AND_LIFE_SCIENCES_CONTROLS_US_SUPPORT&#34;  &#61; &#34;HCLS_US&#34;&#10;  &#34;IRS_1075&#34;                                          &#61; &#34;IRS_1075&#34;&#10;  &#34;CANADA_CONTROLLED_GOODS&#34;                           &#61; &#34;CAGOODS&#34;&#10;&#125;">&#123;&#8230;&#125;</code> |
| [workforce_identity_providers](variables.tf#L328) | Workforce Identity Federation pools. | <code title="map&#40;object&#40;&#123;&#10;  attribute_condition &#61; optional&#40;string&#41;&#10;  issuer              &#61; string&#10;  display_name        &#61; string&#10;  description         &#61; string&#10;  disabled            &#61; optional&#40;bool, false&#41;&#10;  saml &#61; optional&#40;object&#40;&#123;&#10;    idp_metadata_xml &#61; string&#10;  &#125;&#41;, null&#41;&#10;&#125;&#41;&#41;">map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> |  | <code>&#123;&#125;</code> |
| [workload_identity_providers](variables.tf#L344) | Workload Identity Federation pools. The `cicd_repositories` variable references keys here. | <code title="map&#40;object&#40;&#123;&#10;  attribute_condition &#61; optional&#40;string&#41;&#10;  issuer              &#61; string&#10;  custom_settings &#61; optional&#40;object&#40;&#123;&#10;    issuer_uri &#61; optional&#40;string&#41;&#10;    audiences  &#61; optional&#40;list&#40;string&#41;, &#91;&#93;&#41;&#10;    jwks_json  &#61; optional&#40;string&#41;&#10;  &#125;&#41;, &#123;&#125;&#41;&#10;&#125;&#41;&#41;">map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> |  | <code>&#123;&#125;</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [alert_email](outputs.tf#L120) | Email to receive log alerts. |  |
| [assured_workload](outputs.tf#L125) | Assured Workload folder for the deployment. |  |
| [automation](outputs.tf#L130) | Automation resources. |  |
| [billing_dataset](outputs.tf#L135) | BigQuery dataset prepared for billing export. |  |
| [cicd_repositories](outputs.tf#L140) | CI/CD repository configurations. |  |
| [common_services_folder](outputs.tf#L152) | Common services folder where non-tenant related resources should be kept. |  |
| [custom_roles](outputs.tf#L157) | Organization-level custom roles. |  |
| [outputs_bucket](outputs.tf#L162) | GCS bucket where generated output files are stored. |  |
| [project_ids](outputs.tf#L167) | Projects created by this stage. |  |
| [providers](outputs.tf#L177) | Terraform provider files for this stage and dependent stages. | ✓ |
| [service_accounts](outputs.tf#L184) | Automation service accounts created by this stage. |  |
| [tfvars](outputs.tf#L202) | Terraform variable files for the following stages. | ✓ |
| [workforce_identity_pool](outputs.tf#L208) | Workforce Identity Federation pool. |  |
| [workload_identity_pool](outputs.tf#L217) | Workload Identity Federation pool and providers. |  |
<!-- END TFDOC -->
