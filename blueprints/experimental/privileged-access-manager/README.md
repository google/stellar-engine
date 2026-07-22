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

# Privileged Access Manager (PAM) Blueprint

This blueprint demonstrates how to configure [Privileged Access Manager (PAM)](https://cloud.google.com/iam/docs/pam-overview) entitlements. PAM is a Google Cloud native solution to secure, manage, and audit privileged access by enabling just-in-time, time-bound, approval-based access elevations.

## Disclaimer

- The present GCP Terraform Module in this project is set up and intended to be implemented in either a FedRAMP-High or IL5 (Impact Level 5) environment using the Assured Workloads within the Google Cloud Platform (GCP) organization.

## Requirements

### IAM
The following roles must be used to provision the resources of this module:
- Project IAM Admin: `roles/resourcemanager.projectIamAdmin` (to create service identity)
- Service Usage Admin: `roles/serviceusage.serviceUsageAdmin` (to enable API)
- PAM Admin: `roles/privilegedaccessmanager.admin` (to create entitlements)
- Organization/Folder/Project IAM Admin: `roles/resourcemanager.organizationAdmin`, `roles/resourcemanager.folderAdmin`, or `roles/resourcemanager.projectIamAdmin` (depending on where the entitlement is created and if `grant_service_agent_permissions` is true)

## Deployment Steps

1. Copy the contents of the `terraform.tfvars.sample` file into your own `terraform.tfvars` file, then update the variables.
2. Run `terraform init`.
3. Run `terraform plan` to see the infrastructure plan.
4. Run `terraform apply` to apply the infrastructure build.
<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [main_project_id](variables.tf#L43) | Project ID where PAM API will be enabled and service identity created. | <code>string</code> | ✓ |  |
| [organization_id](variables.tf#L48) | Organization ID used for the PAM service agent. | <code>string</code> | ✓ |  |
| [entitlements](variables.tf#L17) | PAM entitlements configuration. | <code title="map&#40;object&#40;&#123;&#10;  location                        &#61; optional&#40;string, &#34;global&#34;&#41;&#10;  max_request_duration_hours      &#61; optional&#40;number, 1&#41;&#10;  parent_type                     &#61; optional&#40;string, &#34;organization&#34;&#41; &#35; organization, folder, project&#10;  parent_id                       &#61; string&#10;  grant_service_agent_permissions &#61; optional&#40;bool, true&#41;&#10;  requesters                      &#61; list&#40;string&#41;&#10;  approvers                       &#61; optional&#40;list&#40;string&#41;, &#91;&#93;&#41;&#10;  notification_recipients &#61; optional&#40;object&#40;&#123;&#10;    approval     &#61; optional&#40;list&#40;string&#41;, &#91;&#93;&#41;&#10;    pending      &#61; optional&#40;list&#40;string&#41;, &#91;&#93;&#41;&#10;    availability &#61; optional&#40;list&#40;string&#41;, &#91;&#93;&#41;&#10;  &#125;&#41;, &#123;&#125;&#41;&#10;  role_bindings &#61; list&#40;object&#40;&#123;&#10;    role                 &#61; string&#10;    condition_expression &#61; optional&#40;string&#41;&#10;  &#125;&#41;&#41;&#10;  auto_approve_entitlement       &#61; optional&#40;bool, false&#41;&#10;  require_approver_justification &#61; optional&#40;bool, true&#41;&#10;  requester_justification        &#61; optional&#40;bool, true&#41;&#10;&#125;&#41;&#41;">map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> |  | <code>&#123;&#125;</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [entitlements](outputs.tf#L17) | PAM entitlements. |  |
<!-- END TFDOC -->
