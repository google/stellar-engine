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
1. Private connectivity for the instance on the target network (`network_name` / `network_project_id`). The default is an existing Private Services Access (PSA) connection on that network, and `psc_config` selects Private Service Connect (PSC) instead. See [Private connectivity](#private-connectivity).
1. Copy terraform.tfvars.sample to terraform.tfvars
1. Updated terraform.tfvars

## Private connectivity

The instance never has a public IP address. It connects through Private Services Access unless you set `psc_config`, which makes it use Private Service Connect instead.

### Private Services Access

The default mode needs a Private Services Access connection to `servicenetworking.googleapis.com` on the network before you deploy. The blueprint does not create that connection, and Cloud SQL cannot create a private IP instance without it.

- On FedRAMP Moderate and FedRAMP High, `fast/stages-aw/2-networking-a-fedramp` creates no Private Services Access connection unless you ask for one. Set `psa_ranges` for the environment of the spoke VPC in the Stage 2 `terraform.tfvars` file and apply Stage 2 first. See [Private services access](../../../fast/stages-aw/2-networking-a-fedramp/README.md#7-private-services-access) for an example.
- On IL4 and IL5, `fast/stages-aw/2-networking-b-il5-ngfw` creates a default `/22` connection on every spoke VPC, so this mode needs no extra step.
- Clients connect to the address in the `connection_internal_ip` output.

### Private Service Connect

Set `psc_config` to deploy the instance with Private Service Connect. The network then needs no Private Services Access connection, which matches the Stage 2 FedRAMP default.

```hcl
psc_config = {
  allowed_consumer_projects = ["<network-project-id>"]
}
```

- Cloud SQL accepts a Private Service Connect endpoint only from a project in `allowed_consumer_projects`. List the project that hosts each endpoint and no other project.
- The blueprint does not create the endpoint. Create it in a subnet of the spoke VPC, target the `psc_service_attachment_link` output, and add a private DNS record that points the `psc_dns_name` output to the endpoint address. The `modules/net-address` module creates the address and the forwarding rule, as the example after this list shows.
- Clients connect to the endpoint address. The `connection_internal_ip` output reports the Private Services Access address only, so do not use it in this mode.
- Choose the mode before the first apply. Setting or removing `psc_config` later plans an in-place change to the network settings of the instance, and Cloud SQL can reject that change, so treat it as a migration and test it outside production first.

```hcl
module "postgres-psc-endpoint" {
  source     = "../../../modules/net-address"
  project_id = "<network-project-id>"
  psc_addresses = {
    postgres = {
      region           = "<region>"
      subnet_self_link = "<subnet-self-link>"
      service_attachment = {
        psc_service_attachment_link = "<psc_service_attachment_link output>"
      }
    }
  }
}
```

## Deployer Permissions

The service account or identity deploying this blueprint requires the following roles:
- **Workload Project (`main_project_id`):**
  - `roles/cloudsql.admin`
  - `roles/serviceusage.serviceUsageAdmin`
- **Network Host Project (`network_project_id`):**
  - `roles/compute.networkUser`
- **KMS Key (`kms_key_name`):**
  - A custom role with `cloudkms.cryptoKeys.getIamPolicy` and `cloudkms.cryptoKeys.setIamPolicy`, or
    `roles/cloudkms.admin` when a custom role is not available, granted on the key only.
  - The blueprint uses these permissions to grant the Cloud SQL service agent
    `roles/cloudkms.cryptoKeyEncrypterDecrypter` on the key
    (`google_kms_crypto_key_iam_member.sql_sa` in `main.tf`).

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
| [database_name](variables.tf#L29) | This is the name of the database. | <code>string</code> | ✓ |  |
| [kms_key_name](variables.tf#L71) | Full path to KMS key. | <code>string</code> | ✓ |  |
| [main_project_id](variables.tf#L165) | This is the project ID. Please set using a terraform.tfvars file. | <code>string</code> | ✓ |  |
| [network_name](variables.tf#L170) | This is the name of the network. | <code>string</code> | ✓ |  |
| [network_project_id](variables.tf#L175) | Project that the Compute Engine VPC is located. | <code>string</code> | ✓ |  |
| [allowed_firewall_ports](variables.tf#L17) | Deprecated and ignored. The blueprint no longer creates a VPC firewall rule. | <code>list&#40;number&#41;</code> |  | <code>null</code> |
| [database_instance_tier](variables.tf#L23) | This specifies the kind of machine-type that we will be running it from. | <code>string</code> |  | <code>&#34;db-g1-small&#34;</code> |
| [database_version](variables.tf#L34) | This is the database type that we are running the cloud sql instance. | <code>string</code> |  | <code>&#34;POSTGRES_13&#34;</code> |
| [deletion_protection](variables.tf#L40) | Terraform deletion protection. | <code>bool</code> |  | <code>true</code> |
| [enable_pgaudit](variables.tf#L46) | This extension provides detailed session and object logging to comply with government, financial & ISO standards and provides auditing capabilities to mitigate threats by monitoring security events on the instance. | <code>string</code> |  | <code>&#34;on&#34;</code> |
| [firewall_name](variables.tf#L59) | Deprecated and ignored. The blueprint no longer creates a VPC firewall rule. | <code>string</code> |  | <code>null</code> |
| [firewall_source_range](variables.tf#L65) | Deprecated and ignored. The blueprint no longer creates a VPC firewall rule. | <code>list&#40;string&#41;</code> |  | <code>null</code> |
| [log_connections](variables.tf#L76) | Enabling the log_connections setting causes each attempted connection to the server to be logged, along with successful completion of client authentication. | <code>string</code> |  | <code>&#34;on&#34;</code> |
| [log_disconnections](variables.tf#L89) | Enabling the log_disconnections setting logs the end of each session, including the session duration. | <code>string</code> |  | <code>&#34;on&#34;</code> |
| [log_error_verbosity](variables.tf#L102) | The log_error_verbosity flag controls the verbosity/details of messages logged. | <code>string</code> |  | <code>&#34;default&#34;</code> |
| [log_min_duration_statement](variables.tf#L115) | Type the minimum amount of execution time of a statement in milliseconds where the total duration of the statement is logged or \"-1\" to disable. | <code>number</code> |  | <code>-1</code> |
| [log_min_error_statement](variables.tf#L127) | The log_min_error_statement flag defines the minimum message severity level that are considered as an error statement. | <code>string</code> |  | <code>&#34;error&#34;</code> |
| [log_min_messages](variables.tf#L139) | The log_min_messages flag defines the minimum message severity level that is considered as an error statement. | <code>string</code> |  | <code>&#34;warning&#34;</code> |
| [log_statement](variables.tf#L152) | The value of log_statement flag determines the SQL statements that are logged. | <code>string</code> |  | <code>&#34;ddl&#34;</code> |
| [psc_config](variables.tf#L180) | Private Service Connect configuration. When set, the instance uses Private Service Connect instead of Private Services Access, so the network needs no Private Services Access connection. List in allowed_consumer_projects each project that hosts a Private Service Connect endpoint for the instance. Leave null to use Private Services Access. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>null</code> |
| [region](variables.tf#L197) | This is the region that we are going to be running the cloud sql instance from. | <code>string</code> |  | <code>&#34;us-east4&#34;</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [connection_internal_ip](outputs.tf#L17) | Conntection internal IP address. |  |
| [psc_dns_name](outputs.tf#L22) | DNS name of the instance, for the DNS record of the Private Service Connect endpoint. Null unless psc_config is set. |  |
| [psc_service_attachment_link](outputs.tf#L27) | Service attachment that a Private Service Connect endpoint targets. Null unless psc_config is set. |  |
<!-- END TFDOC -->
## Firewall Policy Coexistence and Auditing

This blueprint creates no VPC firewall rule. The Cloud SQL instance connects through Private Services Access or Private Service Connect, so it runs in a Google-managed network rather than inside the Shared VPC (`network_name`). Ingress firewall rules in the Shared VPC apply only to instances in that VPC, so they do not control traffic to the database.

- To limit which clients reach the database, apply egress rules to the client workloads for the instance address (`connection_internal_ip`) on `tcp:5432`, in the Stage 2 firewall policies or through `modules/net-vpc-firewall`.
- Earlier releases created `google_compute_firewall.postgres` from the `firewall_name`, `firewall_source_range`, and `allowed_firewall_ports` variables. That rule had no target, so it allowed the database port to every instance in the Shared VPC and did not protect the database. The three variables are deprecated and ignored, and Terraform warns when one is set.
- The first apply after an upgrade destroys that rule, which requires the `compute.firewalls.delete` permission on the host project (`network_project_id`), for example through `roles/compute.securityAdmin`. The deployer does not need that role afterward.
- To confirm that no rule from an earlier release remains, and to collect evidence for the CM-6 and SC-7 controls, inspect both enforcement layers:
  - Folder hierarchical policy rules: `gcloud compute firewall-policies rules list --firewall-policy=<policy-name> --organization=<org-id>`
  - Host-project classic VPC firewall rules: `gcloud compute firewall-rules list --project=<network-project-id>`
