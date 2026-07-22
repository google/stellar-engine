# Google Cloud Organization Bootstrap

The purpose of this stage is to enable critical Google Cloud Organization level functionalities that depend on broad administrative permissions, and prepare the prerequisites needed to enable automation in this and future stages. As multiple Stellar Engine Landing Zone (stellar-engine) instances can be deployed to a single Google Cloud Organization, the bootstrap phase has be separated into an Organization level and an Assured Workload level. This allows for the Organization level bootstrap to only need to be run once per Google Cloud Organization and for the Assured Workload level bootstrap to be ran as many times as needed.

<!-- BEGIN TOC -->
- [Design Overview and Choices](#design-overview-and-choices)
  - [User Groups](#user-groups)
  - [Google Cloud Organization Level IAM](#google-cloud-organization-level-iam)
  - [Google Cloud Organization Policies and Tag-Based Conditions](#google-cloud-organization-policies-and-tag-based-conditions)
  - [Automation Google Cloud Project and Resources](#automation-google-cloud-project-and-resources)
  - [Organization-Level Audit Project](#organization-level-audit-project)
  - [Billing Account](#billing-account)
  - [Google Cloud Organization Level Logging+](#google-cloud-organization-level-logging)
  - [Log Sinks and Log Destinations](#log-sinks-and-log-destinations)
  - [Workforce Identity Federation](#workforce-identity-federation)
- [How to Run This Stage](#how-to-run-this-stage)
- [Customizations](#customizations)
  - [Group Names](#group-names)
  - [IAM](#iam)
- [Variables](#variables)
- [Outputs](#outputs)
<!-- END TOC -->

## Design Overview and Choices

This stage only does the bare minimum required to configure a Google Cloud Organization so it can be used to bootstrap Assured Workloads, automation, and common services. It ensures that the Google Cloud Organization level auditing, IAM roles and organization policies are configured so multiple stellar-engine instances can be deployed to a single Google Cloud Organization without each deployment managing organization level resources.

### User Groups

User groups are important, not only here but throughout the whole automation process. They provide a stable frame of reference that allows decoupling the final set of permissions for each group, from the stage where entities and resources are created and their IAM bindings defined. For example, the final set of roles for the networking group is contributed by this stage at the Google Cloud Organization level (XPN Admin, Cloud Asset Viewer, etc.), and by the Resource Management stage at the Google Cloud Folder level.

We have standardized the initial set of groups on those outlined in the [GCP Enterprise Setup Checklist](https://cloud.google.com/docs/enterprise/setup-checklist) to simplify adoption. They provide a comprehensive and flexible starting point that can suit most users. Adding new groups, or deviating from the initial setup is possible and reasonably simple, and it's briefly outlined in the customization section below.

### Google Cloud Organization Level IAM

The service account used in the [Resource Management stage](../2-resman) needs to be able to grant specific permissions at the Google Cloud Organization level, to enable specific functionality for subsequent stages that deal with network or security resources, or billing-related activities.

In order to be able to assign those roles without having the full authority of the Google Cloud Organization Admin role, this stage defines a custom role that only allows setting IAM policies on the Google Cloud Organization, and grants it via a [delegated role grant](https://cloud.google.com/iam/docs/setting-limits-on-granting-roles) that only allows it to be used to grant a limited subset of roles.

In this way, the Resource Management service account can effectively act as a Google Cloud Organization Admin, but only to grant the specific roles it needs to control.

One consequence of the above setup is the need to configure IAM bindings that can be assigned via the condition as non-authoritative, since those same roles are effectively under the control of two stages: this one and Resource Management. Using authoritative bindings for these roles (instead of non-authoritative ones) would generate potential conflicts, where each stage could try to overwrite and negate the bindings applied by the other at each `apply` cycle.

A full reference of IAM roles managed by this stage [is available here](#).

### Google Cloud Organization Policies and Tag-Based Conditions

It's often desirable to have Google Cloud Organization policies deployed before any other resource in the org, so as to ensure compliance with specific requirements (e.g. location restrictions), or control the configuration of specific resources (e.g. default network at Google Cloud Project creation or service account grants).

Google Cloud Organization policy exceptions are managed via a dedicated resource management tag hierarchy, rooted in the `org-policies` tag key. A default condition is already present for the `iam.allowedPolicyMemberDomains` constraint, that relaxes the policy on resources that have the `org-policies/allowed-policy-member-domains-all` tag value bound or inherited.

Further tag values can be defined via the `org_policies_config.tag_values` variable, and IAM access can be granted on them via the same variable. Once a tag value has been created, its id can be used in constraint rule conditions.

Management of the rest of the tag hierarchy is delegated to the resource management stage, as that is often intimately tied to the Google Cloud Folder hierarchy design.

The Google Cloud Organization policy tag key and values managed by this stage have been added to the `0-organization-bootstrap.auto.tfvars` stage, so that IAM can be delegated to the resource management or successive stages via their ids.

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

### Organization-Level Audit Project

As multiple Stellar Engine Landing Zone instances can be deployed to a single Google Cloud Organization, a new project is created specifically for organization-level logging. This project contains the Logging bucket and M-21-31 compliant Google Cloud Storage bucket for the organization. Any logs relevant at the organization level will be stored in these locations. This allows each Stellar Engine Landing Zone instance to be deployed independently and no overlap with the organization.

### Billing Account

We support three use cases in regards to billing:

- the billing account is part of this same Google Cloud Organization, IAM bindings will be set at the Google Cloud Organization level
- the billing account is not considered part of an Google Cloud Organization (even though it might be), billing IAM bindings are set on the billing account itself
- billing IAM is managed separately, and no bindings should (or can) be set via Terraform, this requires a few extra steps and is definitely not recommended and mainly used for development purposes

For same Google Cloud Organization billing, we configure a custom Google Cloud Organization role that can set IAM bindings, via a delegated role grant to limit its scope to the relevant roles.

For details on configuring the different billing account modes, refer to the [How to run this stage](#how-to-run-this-stage) section below.

Due to limitations of API availability, manual steps have to be followed to enable billing export within the billing Google Cloud Project to BigQuery dataset `billing_export`, which will be created as part of the bootstrap stage. The process to share billing data [is outlined here](https://cloud.google.com/billing/docs/how-to/export-data-bigquery-setup#enable-bq-export).

### Google Cloud Organization Level Logging+

Google Cloud Organization level log sinks are created early in the bootstrap process to ensure a proper audit trail is in place from the very beginning. Multi-tenant log buckets are each customized to serve their purpose to supply dynamic creation based on `config.env` and the organization. Supported log exports for those dedicated projects including features like KMS encryption, log analytics, custom retention policies, and support for Google SecOps. The `tenant_log_bucket` output is used in the "2-resman" stage to ensure multi-tenancy logging to support Assured Workloads framework.

### Log Sinks and Log Destinations

You can customize Google Cloud Organization level logs through the `log_sinks` variable in two ways

- creating additional log sinks to capture more logs
- changing the destination of captured logs

By default, all logs are exported to a log bucket, but FAST can create sinks to BigQuery, GCS, or PubSub.

If you need to capture additional logs, please refer to GCP's documentation on [Scenarios for Exporting Logging Data](https://cloud.google.com/architecture/exporting-stackdriver-logging-for-security-and-access-analytics), where you can find ready-made filter expressions for different use cases.

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
<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [billing_account](variables.tf#L30) | Billing account id. If billing account is not part of the same org set `is_org_level` to `false`. To disable handling of billing IAM roles set `no_iam` to `true`. | <code title="object&#40;&#123;&#10;  id           &#61; string&#10;  is_org_level &#61; optional&#40;bool, true&#41;&#10;  no_iam       &#61; optional&#40;bool, false&#41;&#10;&#125;&#41;">object&#40;&#123;&#8230;&#125;&#41;</code> | ✓ |  |
| [bootstrap_project](variables.tf#L40) | Bootstrap project ID. | <code>string</code> | ✓ |  |
| [organization](variables.tf#L182) | Organization details. | <code title="object&#40;&#123;&#10;  id          &#61; number&#10;  domain      &#61; optional&#40;string&#41;&#10;  customer_id &#61; optional&#40;string&#41;&#10;&#125;&#41;">object&#40;&#123;&#8230;&#125;&#41;</code> | ✓ |  |
| [top_level_folder](variables.tf#L191) | Top Level Folder Details. | <code title="object&#40;&#123;&#10;  name &#61; string&#10;  id   &#61; string&#10;&#125;&#41;">object&#40;&#123;&#8230;&#125;&#41;</code> | ✓ |  |
| [assured_workloads](variables.tf#L17) | Configuration for Assured Workloads. | <code title="object&#40;&#123;&#10;  regime   &#61; string&#10;  location &#61; string&#10;&#125;&#41;">object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code title="&#123;&#10;  regime   &#61; &#34;IL5&#34;&#10;  location &#61; &#34;US&#34;&#10;&#125;">&#123;&#8230;&#125;</code> |
| [custom_roles](variables.tf#L45) | Map of role names => list of permissions to additionally create at the organization level. | <code>map&#40;list&#40;string&#41;&#41;</code> |  | <code>&#123;&#125;</code> |
| [factories_config](variables.tf#L52) | Configuration for the resource factories or external data. | <code title="object&#40;&#123;&#10;  checklist_data    &#61; optional&#40;string&#41;&#10;  checklist_org_iam &#61; optional&#40;string&#41;&#10;  custom_roles      &#61; optional&#40;string, &#34;data&#47;custom-roles&#34;&#41;&#10;  org_policy        &#61; optional&#40;string, &#34;data&#47;org-policies&#34;&#41;&#10;&#125;&#41;">object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>&#123;&#125;</code> |
| [gcp_billing_admins_group](variables.tf#L64) | GCP Billing Admins group name. | <code>string</code> |  | <code>&#34;gcp-billing-admins&#34;</code> |
| [gcp_devops_group](variables.tf#L70) | GCP DevOps group name. | <code>string</code> |  | <code>&#34;gcp-devops&#34;</code> |
| [gcp_organization_admins_group](variables.tf#L76) | GCP Organization Admins group name. | <code>string</code> |  | <code>&#34;gcp-organization-admins&#34;</code> |
| [gcp_security_admins_group](variables.tf#L82) | GCP Security Admins group name. | <code>string</code> |  | <code>&#34;gcp-security-admins&#34;</code> |
| [gcp_support_group](variables.tf#L88) | GCP Support group name. | <code>string</code> |  | <code>null</code> |
| [gcp_vpc_network_admins_group](variables.tf#L94) | GCP VPC Network Admins group name. | <code>string</code> |  | <code>&#34;gcp-vpc-network-admins&#34;</code> |
| [groups](variables.tf#L100) | Group names or IAM-format principals to grant organization-level permissions. If just the name is provided, the 'group:' principal and organization domain are interpolated. | <code title="object&#40;&#123;&#10;  gcp-billing-admins      &#61; optional&#40;string&#41;&#10;  gcp-devops              &#61; optional&#40;string&#41;&#10;  gcp-vpc-network-admins  &#61; optional&#40;string&#41;&#10;  gcp-organization-admins &#61; optional&#40;string&#41;&#10;  gcp-security-admins     &#61; optional&#40;string&#41;&#10;  gcp-support &#61; optional&#40;string&#41;&#10;&#125;&#41;">object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>&#123;&#125;</code> |
| [iam](variables.tf#L116) | Organization-level custom IAM settings in role => [principal] format. | <code>map&#40;list&#40;string&#41;&#41;</code> |  | <code>&#123;&#125;</code> |
| [iam_bindings_additive](variables.tf#L123) | Organization-level custom additive IAM bindings. Keys are arbitrary. | <code title="map&#40;object&#40;&#123;&#10;  member &#61; string&#10;  role   &#61; string&#10;  condition &#61; optional&#40;object&#40;&#123;&#10;    expression  &#61; string&#10;    title       &#61; string&#10;    description &#61; optional&#40;string&#41;&#10;  &#125;&#41;&#41;&#10;&#125;&#41;&#41;">map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> |  | <code>&#123;&#125;</code> |
| [iam_by_principals](variables.tf#L138) | Authoritative IAM binding in {PRINCIPAL => [ROLES]} format. Principals need to be statically defined to avoid cycle errors. Merged internally with the `iam` variable. | <code>map&#40;list&#40;string&#41;&#41;</code> |  | <code>&#123;&#125;</code> |
| [locations](variables.tf#L145) | Optional locations for GCS, BigQuery, and logging buckets created here. | <code title="object&#40;&#123;&#10;  bq      &#61; optional&#40;string, &#34;US&#34;&#41;&#10;  gcs     &#61; optional&#40;list&#40;string&#41;, &#91;&#34;US&#34;&#93;&#41;&#10;  logging &#61; optional&#40;list&#40;string&#41;, &#91;&#34;global&#34;&#93;&#41;&#10;  pubsub  &#61; optional&#40;list&#40;string&#41;, &#91;&#93;&#41;&#10;  kms     &#61; optional&#40;list&#40;string&#41;, &#91;&#34;US&#34;&#93;&#41;&#10;&#125;&#41;">object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>&#123;&#125;</code> |
| [logging_kms_key](variables.tf#L158) | value of the KMS key used for logging. | <code>string</code> |  | <code>null</code> |
| [org_policies_config](variables.tf#L164) | Organization policies customization. | <code title="object&#40;&#123;&#10;  constraints &#61; optional&#40;object&#40;&#123;&#10;    allowed_policy_member_domains &#61; optional&#40;list&#40;string&#41;, &#91;&#93;&#41;&#10;    allowed_access_boundaries     &#61; optional&#40;list&#40;string&#41;, &#91;&#93;&#41;&#10;  &#125;&#41;, &#123;&#125;&#41;&#10;  import_defaults &#61; optional&#40;bool, false&#41;&#10;  tag_name        &#61; optional&#40;string, &#34;org-policies&#34;&#41;&#10;  tag_values &#61; optional&#40;map&#40;object&#40;&#123;&#10;    description &#61; optional&#40;string, &#34;Managed by the Terraform organization module.&#34;&#41;&#10;    iam         &#61; optional&#40;map&#40;list&#40;string&#41;&#41;, &#123;&#125;&#41;&#10;    id          &#61; optional&#40;string&#41;&#10;  &#125;&#41;&#41;, &#123;&#125;&#41;&#10;&#125;&#41;">object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>&#123;&#125;</code> |
| [workforce_identity_providers](variables.tf#L199) | Workforce Identity Federation pools. | <code title="map&#40;object&#40;&#123;&#10;  attribute_condition &#61; optional&#40;string&#41;&#10;  issuer              &#61; string&#10;  display_name        &#61; string&#10;  description         &#61; string&#10;  disabled            &#61; optional&#40;bool, false&#41;&#10;  saml &#61; optional&#40;object&#40;&#123;&#10;    idp_metadata_xml &#61; string&#10;  &#125;&#41;, null&#41;&#10;&#125;&#41;&#41;">map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> |  | <code>&#123;&#125;</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [workforce_identity_pool](outputs.tf#L24) | Workforce Identity Federation pool. |  |
<!-- END TFDOC -->
