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

# Postgressql

<!-- BEGIN TOC -->
- [Introduction to PostgreSQL](#introduction-to-postgresql)
- [Requirements](#requirements)
- [Notes](#notes)
- [Deployment Steps](#deployment-steps)
- [Verification of a successful deployment](#verification-of-a-successful-deployment)
- [Variables](#variables)
- [Outputs](#outputs)
<!-- END TOC -->

## Introduction to PostgreSQL
PostgreSQL provides a fully managed database service that automates backups, replication, and failover.

## Requirements
1. An existing VPC
1. Copy terraform.tfvars.sample to terraform.tfvars
1. Updated terraform.tfvars

## Notes
1. There seems to be a provider bug that will not allow a full terraform delete to complete due to the following error:

```
Unable to remove Service Networking Connection, err: Error waiting for Delete Service Networking Connection: Error code 9, message: Failed to delete connection; Producer services (e.g. CloudSQL, Cloud Memstore, etc.) are still using this connection.
```

To ensure proper deletion, please manually delete the peered network that is created, release the allocated ip address, and remove the following three services from the terraform state (terraform state rm <service-name>)
```
data.google_compute_network.network
google_compute_global_address.postgres
google_service_networking_connection.postgres
```

## Deployment Steps
You should see this README and some terraform files.
1. Run ```cp terraform.tfvars.sample terraform.tfvars``` to copy the sample variables to your own tfvars file.

2. Update the variables as necessary in your tfvars file.
3. The usual terraform commands will do the work. To provision this example, run the following from within this directory:

```terraform init ```<br />
```terraform plan``` to see the infrastructure plan<br />
```terraform apply``` to apply the infrastructure build<br />

## Verification of a successful deployment
Use GCP console to verify if the resources have been created.
https://console.cloud.google.com/marketplace/vm/config/click-to-deploy-images/postgresql

<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [database_name](variables.tf#L29) | This is the name of the database. | <code>string</code> | ✓ |  |
| [firewall_name](variables.tf#L59) | Firewall name. | <code>string</code> | ✓ |  |
| [firewall_source_range](variables.tf#L64) | Firewall source IP range. | <code>list&#40;any&#41;</code> | ✓ |  |
| [kms_key_name](variables.tf#L69) | Full path to KMS key. | <code>string</code> | ✓ |  |
| [main_project_id](variables.tf#L162) | This is the project ID. Please set using a terraform.tfvars file. | <code>string</code> | ✓ |  |
| [network_name](variables.tf#L167) | This is the name of the network. | <code>string</code> | ✓ |  |
| [network_project_id](variables.tf#L172) | Project that the Compute Engine VPC is located. | <code>string</code> | ✓ |  |
| [allowed_firewall_ports](variables.tf#L17) | Allowed firewall ports. Postgresql used 5432. | <code>list&#40;number&#41;</code> |  | <code>&#91;5432&#93;</code> |
| [database_instance_tier](variables.tf#L23) | This specifies the kind of machine-type that we will be running it from. | <code>string</code> |  | <code>&#34;db-g1-small&#34;</code> |
| [database_version](variables.tf#L34) | This is the database type that we are running the cloud sql instance. | <code>string</code> |  | <code>&#34;POSTGRES_13&#34;</code> |
| [deletion_protection](variables.tf#L40) | Terraform deletion protection. | <code>bool</code> |  | <code>true</code> |
| [enable_pgaudit](variables.tf#L46) | This extension provides detailed session and object logging to comply with government, financial & ISO standards and provides auditing capabilities to mitigate threats by monitoring security events on the instance. | <code>string</code> |  | <code>&#34;on&#34;</code> |
| [log_connections](variables.tf#L74) | Enabling the log_connections setting causes each attempted connection to the server to be logged, along with successful completion of client authentication. | <code>string</code> |  | <code>&#34;on&#34;</code> |
| [log_disconnections](variables.tf#L87) | Enabling the log_disconnections setting logs the end of each session, including the session duration. | <code>string</code> |  | <code>&#34;on&#34;</code> |
| [log_error_verbosity](variables.tf#L100) | The log_error_verbosity flag controls the verbosity/details of messages logged. | <code>string</code> |  | <code>&#34;default&#34;</code> |
| [log_min_duration_statement](variables.tf#L113) | Type the minimum amount of execution time of a statement in milliseconds where the total duration of the statement is logged or \"-1\" to disable. | <code>number</code> |  | <code>-1</code> |
| [log_min_error_statement](variables.tf#L125) | The log_min_error_statement flag defines the minimum message severity level that are considered as an error statement. | <code>string</code> |  | <code>&#34;error&#34; &#35; Required for CIS Compliance Benchmark 6.2&#34;</code> |
| [log_min_messages](variables.tf#L136) | The log_min_messages flag defines the minimum message severity level that is considered as an error statement. | <code>string</code> |  | <code>&#34;warning&#34;</code> |
| [log_statement](variables.tf#L149) | The value of log_statement flag determines the SQL statements that are logged. | <code>string</code> |  | <code>&#34;ddl&#34;</code> |
| [region](variables.tf#L177) | This is the region that we are going to be running the cloud sql instance from. | <code>string</code> |  | <code>&#34;us-east4&#34;</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [connection_internal_ip](outputs.tf#L17) | Connection internal IP address. |  |
<!-- END TFDOC -->
