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

# Access Context Manager 
This modules manages the creation ofAccess Context Manager (ACM). Access Context Manager (ACM) in Google Cloud Platform (GCP) is a security service that allows you to define and enforce fine-grained access controls for your resources.

## Introduction to ACM
The primary purpose of ACM is to define and manage access levels and access policies to control access to GCP resources based on contextual attributes, such as:

User identity: Restrict access to specific users or groups.
Device attributes: Require users to access resources only from approved devices.
Location: Allow or deny access based on geographic location.
IP address: Restrict access to specific IP ranges.
These controls help implement zero-trust security, ensuring that access is granted only under specific conditions, regardless of whether the request originates from inside or outside your network.

<!-- BEGIN TOC -->
- [Introduction to ACM](#introduction-to-acm)
- [Access Policy ID number](#access-policy-id-number)
- [Deployment Steps](#deployment-steps)
- [Verification of a successful deployment?](#verification-of-a-successful-deployment)
- [Variables](#variables)
- [Outputs](#outputs)
<!-- END TOC -->

## Access Policy ID number

To get Access Policy ID number, run the following commmand:

```gcloud access-context-manager policies list```

## Deployment Steps
1. Run ```cp terraform.tfvars.sample terraform.tfvars``` to copy the sample variables to your own tfvars file.
2. Update the variables as necessary in your tfvars file.
3. The usual terraform commands will do the work. To provision this example, run the following from within this directory:

```terraform init```<br />
```terraform plan``` to see the infrastructure plan<br />
```terraform apply``` to apply the infrastructure build<br />
```terraform destroy``` only if you wish to destroy the built infrastructure<br />

## Verification of a successful deployment?

Use GCP console to verify if the resources have been created. NOTE: Everything is checked on the ORG level
To check access level: Go to Access Context Manager and it should be listed if it was created.
To check service perimeters: Go to VPC Service Control and it should be listed if it was created.
<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [access_levels](variables.tf#L1) | List of access levels to create. Each access level is a map containing 'name', 'description', and 'conditions'. | <code title="list&#40;object&#40;&#123;&#10;  name        &#61; string&#10;  description &#61; string&#10;  conditions  &#61; list&#40;object&#40;&#123;&#10;    ip_subnetworks             &#61; list&#40;string&#41;&#10;    members                    &#61; list&#40;string&#41;&#10;    negate                     &#61; bool&#10;    device_policy              &#61; object&#40;&#123;&#10;      require_screen_lock &#61; bool&#10;    &#125;&#41;&#10;    regions                    &#61; list&#40;string&#41;&#10;  &#125;&#41;&#41;&#10;&#125;&#41;&#41;">list&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> | ✓ |  |
| [access_policy_title](variables.tf#L17) | The title for the Access Context Manager policy. | <code>string</code> | ✓ |  |
| [domain](variables.tf#L22) | Domain for ACM. | <code>string</code> | ✓ |  |
| [organization_id](variables.tf#L27) | The organization ID. | <code>string</code> | ✓ |  |
| [project_id](variables.tf#L32) | The project ID where the Access Context Manager resources will be created. | <code>string</code> | ✓ |  |
| [region](variables.tf#L37) | GCP Region to deploy into. | <code>string</code> | ✓ |  |
| [service_perimeters](variables.tf#L42) | List of service perimeters to create. Each service perimeter is a map containing 'name', 'description', 'status', and 'resources'. | <code title="list&#40;object&#40;&#123;&#10;  name        &#61; string&#10;  description &#61; string&#10;  status      &#61; object&#40;&#123;&#10;    restricted_services &#61; list&#40;string&#41;&#10;    resources           &#61; list&#40;string&#41;&#10;  &#125;&#41;&#10;&#125;&#41;&#41;">list&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> | ✓ |  |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [access_levels](outputs.tf#L1) | The list of created access levels. |  |
| [service_perimeters](outputs.tf#L12) | The list of created service perimeters. |  |
<!-- END TFDOC -->
