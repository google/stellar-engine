Copyright 2023 Google LLC

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

## Requirements
1. An existing VPC with Private Service Access (PSA) peering already configured on the target network (`network_name` / `network_project_id`).
1. Copy terraform.tfvars.sample to terraform.tfvars
1. Updated terraform.tfvars

## Deployer Permissions

The service account or identity deploying this blueprint requires the following roles:
- **Workload Project (`main_project_id`):**
  - `roles/cloudsql.admin`
  - `roles/serviceusage.serviceUsageAdmin`
- **Network Host Project (`network_project_id`):**
  - `roles/compute.networkUser`
  - `roles/compute.securityAdmin` (for managing the firewall rule)
- **KMS Project / Key (`kms_key_name`):**
  - `roles/cloudkms.cryptoKeyEncrypterDecrypter`

### Impersonated Deployment Configuration

When deploying through service account impersonation, the Terraform `google` and `google-beta` providers must specify `user_project_override = true` and `billing_project` set to the workload project. Without this setting, provider-level quota and API enablement checks resolve against the deploying service account's project rather than the target workload project, leading to false `SERVICE_DISABLED` errors.

Example provider configuration:

```hcl
provider "google" {
  project                     = "<workload-project-id>"
  region                      = "<region>"
  impersonate_service_account = "<deployer-sa>@<iac-project-id>.iam.gserviceaccount.com"
  user_project_override       = true
  billing_project             = "<workload-project-id>"
}

provider "google-beta" {
  project                     = "<workload-project-id>"
  region                      = "<region>"
  impersonate_service_account = "<deployer-sa>@<iac-project-id>.iam.gserviceaccount.com"
  user_project_override       = true
  billing_project             = "<workload-project-id>"
}
```

<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [core_project_id](variables.tf#L23) | This is the core project ID. Please set using a terraform.tfvars file. | <code>string</code> | ✓ |  |
| [database_name](variables.tf#L34) | This is the name of the database. | <code>string</code> | ✓ |  |
| [firewall_name](variables.tf#L64) | Firewall name. | <code>string</code> | ✓ |  |
| [firewall_source_range](variables.tf#L69) | Firewall source IP range. | <code>list&#40;any&#41;</code> | ✓ |  |
| [kms_key_name](variables.tf#L80) | Full path to KMS key. | <code>string</code> | ✓ |  |
| [main_project_id](variables.tf#L173) | This is the project ID. Please set using a terraform.tfvars file. | <code>string</code> | ✓ |  |
| [network_name](variables.tf#L178) | This is the name of the network. | <code>string</code> | ✓ |  |
| [network_project_id](variables.tf#L183) | Project that the Compute Engine VPC is located. | <code>string</code> | ✓ |  |
| [subnetwork_name](variables.tf#L194) | This is the name of the subnetwork. | <code>string</code> | ✓ |  |
| [allowed_firewall_ports](variables.tf#L17) | Allowed firewall ports. Postgresql used 5432. | <code>list&#40;number&#41;</code> |  | <code>&#91;5432&#93;</code> |
| [database_instance_tier](variables.tf#L28) | This specifies the kind of machine-type that we will be running it from. | <code>string</code> |  | <code>&#34;db-g1-small&#34;</code> |
| [database_version](variables.tf#L39) | This is the database type that we are running the cloud sql instance. | <code>string</code> |  | <code>&#34;POSTGRES_13&#34;</code> |
| [deletion_protection](variables.tf#L45) | Terraform deletion protection. | <code>bool</code> |  | <code>true</code> |
| [enable_pgaudit](variables.tf#L51) | This extension provides detailed session and object logging to comply with government, financial & ISO standards and provides auditing capabilities to mitigate threats by monitoring security events on the instance. | <code>string</code> |  | <code>&#34;on&#34;</code> |
| [google_compute_global_address_name](variables.tf#L74) | Global address for VPC name. | <code>string</code> |  | <code>&#34;postgres&#34;</code> |
| [log_connections](variables.tf#L85) | Enabling the log_connections setting causes each attempted connection to the server to be logged, along with successful completion of client authentication. | <code>string</code> |  | <code>&#34;on&#34;</code> |
| [log_disconnections](variables.tf#L98) | Enabling the log_disconnections setting logs the end of each session, including the session duration. | <code>string</code> |  | <code>&#34;on&#34;</code> |
| [log_error_verbosity](variables.tf#L111) | The log_error_verbosity flag controls the verbosity/details of messages logged. | <code>string</code> |  | <code>&#34;default&#34;</code> |
| [log_min_duration_statement](variables.tf#L124) | Type the minimum amount of execution time of a statement in milliseconds where the total duration of the statement is logged or \"-1\" to disable. | <code>number</code> |  | <code>-1</code> |
| [log_min_error_statement](variables.tf#L136) | The log_min_error_statement flag defines the minimum message severity level that are considered as an error statement. | <code>string</code> |  | <code>&#34;error&#34; &#35; Required for CIS Compliance Benchmark 6.2&#34;</code> |
| [log_min_messages](variables.tf#L147) | The log_min_messages flag defines the minimum message severity level that is considered as an error statement. | <code>string</code> |  | <code>&#34;warning&#34;</code> |
| [log_statement](variables.tf#L160) | The value of log_statement flag determines the SQL statements that are logged. | <code>string</code> |  | <code>&#34;ddl&#34;</code> |
| [region](variables.tf#L188) | This is the region that we are going to be running the cloud sql instance from. | <code>string</code> |  | <code>&#34;us-east4&#34;</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [connection_internal_ip](outputs.tf#L17) | Connection internal IP address. |  |
<!-- END TFDOC -->
