<!--
Copyright 2026 Google LLC

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
-->

# Access Control Manager

<!-- BEGIN TOC -->
- [Introduction to ACM](#introduction-to-acm)
- [Access Context Manager Blueprint](#access-context-manager-blueprint)
- [Disclaimer](#disclaimer)
- [Prerequisites Steps](#prerequisites-steps)
- [Deployment Steps](#deployment-steps)
- [Verification of a successful deployment](#verification-of-a-successful-deployment)
- [Variables](#variables)
- [Outputs](#outputs)
<!-- END TOC -->

## Introduction to ACM
The primary purpose of ACM is to define and manage access levels and access policies to control access to GCP resources based on contextual attributes, such as:

<mark>User identity:</mark> Restrict access to specific users or groups. <br />
<mark>Device attributes:</mark> Require users to access resources only from approved devices. <br />
<mark>Location:</mark> Allow or deny access based on geographic location. <br />
<mark>IP address:</mark> Restrict access to specific IP ranges. <br />

These controls help implement zero-trust security, ensuring that access is granted only under specific conditions, regardless of whether the request originates from inside or outside your network. <br />

# Access Context Manager Blueprint
This blueprint demonstrates how to deploy Access Context Manager (ACM) on Google Cloud Platform (GCP). Access Context Manager (ACM) in Google Cloud Platform (GCP) is a security service that allows you to define and enforce fine-grained access controls for your resources. This blueprint runs create two different resources:

<mark>Service Perimeters:</mark> A core feature of Access Context Manager, service perimeters provide a way to define and enforce boundaries around GCP services to enhance security and control data access. They help protect sensitive data, restrict access to services (based on defined policies) and prevent data from being exfiltrated to unauthorized networks or regions.

<mark>Access Levels:</mark> Allow you to define and enforce fine-grained access control policies for resources and services; providing an additional layer of security

By using Access Levels and Service Perimeters, you can control access based on attributes like user identity, device security, IP address, and more. For more information: please look at the Access Context Manager [Overview](https://cloud.google.com/access-context-manager/docs/overview#:~:text=Service%20perimeters%20define%20sandboxes%20of,to%20describe%20the%20desired%20rules.).

## Disclaimer
This blueprint uses the CNAP Blueprint deployment as its foundation.
To view and manage Access levels in your project, an access policy must be created in the organization level that is scoped to the project.
You cannot edit the policy title once it is created.
An access policy collects the service perimeters and access levels you create for your organization. An organization can have one access policy for the entire organization and multiple scoped access policies for the folders and projects.

## Prerequisites Steps
Determine your Organization number
```gcloud organizations list```

Determine if there is a policy
```gcloud access-context-manager policies list --organization="<ORGANIZATION_ID>"```

Note: Replace `ORGANIZATION_ID` (numeric ID of your organization) and `POLICY_TITLE` (human-readable title for your policy) with the appropriate values in the commands below where:

If no results were returned, then an Access Policy doesn't exist. Please follow the [Create an Organization-Level Access Policy](https://cloud.google.com/access-context-manager/docs/create-access-policy#organization-access-policy) instructions or use the gcloud command below before proceeding to the [Deployment Steps](#deployment-steps).
   * `gcloud access-context-manager policies create --organization="<ORGANIZATION_ID>" --title="<POLICY_TITLE>"`

## Deployment Steps
1. Review and follow necessary [Prerequisites Steps](#prerequisites-steps).
2. Run ```cp terraform.tfvars.sample terraform.tfvars``` to copy the sample variables to your own tfvars file & update the variables as necessary in your tfvars file.
3. Set your region (https://cloud.google.com/compute/docs/regions-zones). 
4. Create a new `access_policy_title` ; "default" is the default policy title.
5. Create a new `access_levels` i.e. ```gcloud access-context-manager levels list```
  a. REGIONS should contains ISO3166-1 alpha-2 country code.
6. Create a new `service_perimeter` i.e., like restrict_storage.
  a. Obtain your projectNumber if you're identifying resources using ```'gcloud projects describe <project ID> --format='value(projectNumber'``` (In the sample provided is based off utility from the CNAP Blueprint).
7. The usual terraform commands will do the work. To provision this example, run the following from within this directory:

```terraform init```<br />
```terraform plan``` to see the infrastructure plan<br />
```terraform apply``` to apply the infrastructure build<br />
```terraform destroy``` only if you wish to destroy the built infrastructure<br />

## Verification of a successful deployment
Use GCP console to verify if the resources have been created. NOTE: Everything is checked on the ORG level <br />
To check access level: Go to Access Context Manager and it should be listed if it was created. <br />
To check service perimeters: Go to VPC Service Control and it should be listed if it was created. <br />

<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [access_levels](variables.tf#L1) | List of access levels to create. Each access level is a map containing 'name', 'description', and 'conditions'. | <code title="list&#40;object&#40;&#123;&#10;  name        &#61; string&#10;  description &#61; string&#10;  conditions &#61; list&#40;object&#40;&#123;&#10;    ip_subnetworks &#61; list&#40;string&#41;&#10;    members        &#61; list&#40;string&#41;&#10;    negate         &#61; bool&#10;    device_policy &#61; object&#40;&#123;&#10;      require_screen_lock &#61; bool&#10;    &#125;&#41;&#10;    regions &#61; list&#40;string&#41;&#10;  &#125;&#41;&#41;&#10;&#125;&#41;&#41;">list&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> | ✓ |  |
| [access_policy_title](variables.tf#L18) | The title for the Access Context Manager policy. | <code>string</code> | ✓ |  |
| [domain](variables.tf#L23) | Domain of the project that you will be using. | <code>string</code> | ✓ |  |
| [main_project_id](variables.tf#L28) | The project ID where the Access Context Manager resources will be created. | <code>string</code> | ✓ |  |
| [organization_id](variables.tf#L33) | The organization ID. | <code>string</code> | ✓ |  |
| [region](variables.tf#L38) | GCP Region to deploy into. | <code>string</code> | ✓ |  |
| [service_perimeters](variables.tf#L43) | List of service perimeters to create. Each service perimeter is a map containing 'name', 'description', 'status', and 'resources'. | <code title="list&#40;object&#40;&#123;&#10;  name        &#61; string&#10;  description &#61; string&#10;  status &#61; object&#40;&#123;&#10;    restricted_services &#61; list&#40;string&#41;&#10;    resources           &#61; list&#40;string&#41;&#10;  &#125;&#41;&#10;&#125;&#41;&#41;">list&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> | ✓ |  |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [access_levels](outputs.tf#L1) | The list of created access levels with their details. |  |
| [service_perimeters](outputs.tf#L6) | The list of created service perimeters with their details. |  |
<!-- END TFDOC -->