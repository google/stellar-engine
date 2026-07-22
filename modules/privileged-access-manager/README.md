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

# Cloud Privileged Access Manager (PAM) Module
This module makes it easy to set up [Privileged Access Manager](https://cloud.google.com/iam/docs/pam-overview). Privileged Access Manager (PAM) is a Google Cloud native, managed solution to secure, manage and audit privileged access while ensuring operational velocity and developer productivity. PAM enables just-in-time, time-bound, approval-based access elevations, and auditing of privileged access elevations and activity. PAM lets you define the rules of who can access, what they can access, and if they should be granted access with or without approvals based on the sensitivity of the access and emergency of the situation.

Functional examples are included in the [examples](https://github.com/GoogleCloudPlatform/terraform-google-pam/tree/main/examples) directory

##  Usage

```tf
# Configure Cloud Privilege Access Management (PAM) 
module "entitlement_project" {
  source  = "GoogleCloudPlatform/pam/google"
  version = "~> 3.1"

  entitlement_id                  = "example-entitlement-project"
  parent_id                       = var.project_id
  parent_type                     = "project"
  grant_service_agent_permissions = true

  organization_id = var.org_id

  entitlement_requesters = [
    "serviceAccount:${var.entitlement_requester}",
  ]
  entitlement_approvers = [
    "domain:google.com",
  ]
  role_bindings = [
    {
      role                 = "roles/storage.admin"
      condition_expression = "request.time < timestamp(\"2024-04-23T18:30:00.000Z\")"
    },
    {
      role = "roles/bigquery.admin"
    }
  ]
}
```

<!-- BEGINNING OF PRE-COMMIT-TERRAFORM DOCS HOOK -->
## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| auto_approve_entitlement | Whether or not to auto approve the entitlement. If true, entitlement will be auto approved without any manual approval | `bool` | `false` | no |
| entitlement_approval_notification_recipients | List of email addresses to be notified when a request is granted | `list(string)` | `[]` | no |
| entitlement_approvers | List of users, groups or domain who can approve this entitlement. Can be one or more of Google Account email, Google Group or Google Workspace domain. Required if auto_approve_entitlement is false (default) | `list(string)` | `[]` | no |
| entitlement_availability_notification_recipients | List of email addresses to be notified when a entitlement is created. These email addresses will receive an email about availability of the entitlement | `list(string)` | `[]` | no |
| entitlement_id | The ID to use for this Entitlement. This will become the last part of the resource name. This value should be 4-63 characters. This value should be unique among all other Entitlements under the specified parent | `string` | n/a | yes |
| entitlement_pending_notification_recipients | List of additional email addresses to be notified when a grant is pending approval | `list(string)` | `[]` | no |
| entitlement_requesters | Required List of users, groups, service accounts or domains who can request grants using this entitlement. Can be one or more of Google Account email, Google Group, Service account or Google Workspace domain | `list(string)` | n/a | yes |
| grant_service_agent_permissions | Whether or not to grant roles/privilegedaccessmanager.serviceAgent role to PAM service account | `bool` | `false` | no |
| location | The region of the Entitlement resource | `string` | `"global"` | no |
| max_request_duration_hours | The maximum amount of time for which access would be granted for a request. A requester can choose to ask for access for less than this duration but never more | `number` | `1` | no |
| organization_id | Organization id | `string` | n/a | yes |
| parent_id | The ID of organization, folder, or project to create the entitlement in | `string` | n/a | yes |
| parent_type | Parent type. Can be organization, folder, or project to create the entitlement in | `string` | n/a | yes |
| requester_justification | If the requester is required to provide a justification | `bool` | `true` | no |
| require_approver_justification | Do the approvers need to provide a justification for their actions | `bool` | `true` | no |
| role_bindings | The maximum amount of time for which access would be granted for a request. A requester can choose to ask for access for less than this duration but never more | <pre>list(object({
    role                 = string
    condition_expression = optional(string)
  }))</pre> | n/a | yes |

## Outputs

| Name | Description |
|------|-------------|
| entitlement | Entitlement created |

<!-- END OF PRE-COMMIT-TERRAFORM DOCS HOOK -->

## Requirements

These sections describe requirements for using this module.

### Software

The following dependencies must be available:

- [Terraform][terraform] v1.3+
- [Terraform Provider for GCP][terraform-provider-gcp] plugin v6.5+

### Service Account and User Permissions

A service account with the following roles must be used to provision
this module:

- PAM Service Agent : `roles/privilegedaccessmanager.serviceAgent`


The [Project Factory module][project-factory-module] and the
[IAM module][iam-module] may be used in combination to provision a
service account with the necessary roles applied.

### APIs

A project with the following APIs enabled must be used to host the
resources of this module:

- Cloud API: `privilegedaccessmanager.googleapis.com`

The [Project Factory module][project-factory-module] can be used to
provision a project with the necessary APIs enabled.

## Contributing

Refer to the [contribution guidelines](../../docs/CONTRIBUTING.md) for
information on contributing to this module.
