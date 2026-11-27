# Access Context Manager

<!-- BEGIN TOC -->
- [Introduction to ACM](#introduction-to-acm)
- [Access Context Manager blueprint](#access-context-manager-blueprint)
- [Disclaimer](#disclaimer)
- [Prerequisites steps](#prerequisites-steps)
- [Deployment steps](#deployment-steps)
- [Verification of a successful deployment](#verification-of-a-successful-deployment)
- [Variables](#variables)
- [Outputs](#outputs)
<!-- END TOC -->

## Introduction to ACM
The primary purpose of ACM is to define and manage access levels and access policies to control access to GCP resources based on contextual attributes, such as:

- User identity to restrict access to specific users or groups.
- Device attributes to require users to access resources only from approved devices.
- Location to allow or deny access based on geographic location.
- IP address to restrict access to specific IP ranges.

These controls help implement zero-trust security, ensuring that access is granted only under specific conditions, regardless of whether the request originates from inside or outside your network.

## Access Context Manager blueprint
This blueprint demonstrates how to deploy Access Context Manager (ACM) on Google Cloud Platform (GCP). Access Context Manager (ACM) in Google Cloud Platform (GCP) is a security service that allows you to define and enforce fine-grained access controls for your resources. This blueprint creates two different resources:

- Service perimeters define and enforce boundaries around GCP services to enhance security and control data access. They protect sensitive data, restrict access to services based on defined policies, and prevent data from being exfiltrated to unauthorized networks or regions.
- Access levels define and enforce fine-grained access control policies for resources and services, providing an additional layer of security.

By using Access Levels and Service Perimeters, you can control access based on attributes like user identity, device security, IP address, and more. For more information, review the Access Context Manager [Overview](https://cloud.google.com/access-context-manager/docs/overview).

## Disclaimer
This blueprint uses the CNAP Blueprint deployment as its foundation.
To view and manage Access levels in your project, an access policy must exist at the organization level and be scoped appropriately.
An access policy collects the service perimeters and access levels you create for your organization. An organization can have one access policy for the entire organization and multiple scoped access policies for folders and projects.

## Prerequisites steps
Determine your Organization number:

```bash
gcloud organizations list
```

Determine if there is an existing access policy:

```bash
gcloud access-context-manager policies list --organization="<ORGANIZATION_ID>"
```

Replace `ORGANIZATION_ID` (numeric ID of your organization) and `POLICY_TITLE` (human-readable title for your policy) with the appropriate values in the commands below.

If no results are returned, an Access Policy does not exist yet. Follow the [Create an Organization-Level Access Policy](https://cloud.google.com/access-context-manager/docs/create-access-policy#organization-access-policy) instructions or run the following command before proceeding to [Deployment steps](#deployment-steps):

```bash
gcloud access-context-manager policies create --organization="<ORGANIZATION_ID>" --title="<POLICY_TITLE>"
```

## Deployment steps
1. Review and follow the [Prerequisites steps](#prerequisites-steps).
2. Run `cp terraform.tfvars.sample terraform.tfvars` to copy the sample variables to your own tfvars file and update the variables as necessary.
3. Set `region` to your Google Cloud region (`us-east4` is used in the sample) for provider quota billing context.
4. Note that `access_policy_title` and `domain` are optional unused legacy variables retained for backwards compatibility because the module looks up the existing organization access policy automatically.
5. Configure `access_levels` (compare existing levels with `gcloud access-context-manager levels list --policy=<POLICY_ID>`):
   - Set `regions` to ISO 3166-1 alpha-2 country codes such as `["US"]`, not GCP region names.
   - Set `ip_subnetworks` to valid CIDR blocks such as `["203.0.113.0/24"]`.
6. Configure `service_perimeters` (for example `gcs_perimeter` using `name`, `description`, and `status`, without an extra `parent` key):
   - Obtain the numeric project number for each project in `status.resources` (`projects/<PROJECT_NUMBER>`) by running:

```bash
gcloud projects describe <PROJECT_ID> --format='value(projectNumber)'
```

7. Provision the resources from within this directory:

```bash
terraform init
terraform plan
terraform apply
```

Run `terraform destroy` only if you wish to destroy the built infrastructure.

## Verification of a successful deployment
Use the Google Cloud console to verify that the organization-level resources exist:
- Open Access Context Manager in the console to verify the access levels.
- Open VPC Service Controls in the console to verify the service perimeters.
<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [access_levels](variables.tf#L15) | List of access levels to create. Each access level is a map containing 'name', 'description', and 'conditions'. | <code>list&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> | ✓ |  |
| [main_project_id](variables.tf#L44) | The project ID where the Access Context Manager resources will be created. | <code>string</code> | ✓ |  |
| [organization_id](variables.tf#L49) | The organization ID. | <code>string</code> | ✓ |  |
| [region](variables.tf#L54) | GCP Region to deploy into. | <code>string</code> | ✓ |  |
| [service_perimeters](variables.tf#L59) | List of service perimeters to create. Each service perimeter is a map containing 'name', 'description', 'status', and 'resources'. | <code>list&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> | ✓ |  |
| [access_policy_title](variables.tf#L32) | Deprecated unused input retained for backwards compatibility; the module looks up the existing organization access policy. | <code>string</code> |  | <code>null</code> |
| [domain](variables.tf#L38) | Deprecated unused input retained for backwards compatibility. | <code>string</code> |  | <code>null</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [access_levels](outputs.tf#L15) | The list of created access levels with their details. |  |
| [service_perimeters](outputs.tf#L20) | The list of created service perimeters with their details. |  |
<!-- END TFDOC -->
