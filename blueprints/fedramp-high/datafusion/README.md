# Data Fusion

<!-- BEGIN TOC -->
- [Introduction to Data Fusion](#introduction-to-data-fusion)
- [Data Fusion Blueprint](#data-fusion-blueprint)
- [Deployment Steps](#deployment-steps)
  - [Troubleshooting](#troubleshooting)
- [Verification of a successful deployment](#verification-of-a-successful-deployment)
- [Variables](#variables)
- [Outputs](#outputs)
<!-- END TOC -->

## Introduction to Data Fusion
Cloud Data Fusion is a fully managed, cloud-native data integration service for building and managing ETL and ELT pipelines.

## Data Fusion Blueprint
This blueprint deploys a private Cloud Data Fusion instance encrypted with Cloud KMS in a Shared VPC environment.

## Deployment Steps
You should see this README and some Terraform files.
1. Update the variables in `terraform.tfvars` (copied from `terraform.tfvars.sample`) to match your environment:
   - `main_project_id`: Project ID where the Data Fusion instance is created.
   - `core_project_id`: Core project ID hosting `kms_keyring_name` and `kms_key_name`.
   - `network_project_id`, `network_name`, and `subnetwork_name`: Shared VPC host project, VPC name, and subnet name.
   - `region` and `name`: Deployment region and Data Fusion instance name.
   - `connection_type`, `unreachable_cidr_block`, and `ip_allocation`: Defaults to Private Service Connect (`PRIVATE_SERVICE_CONNECT_INTERFACES`, creating a Compute Engine network attachment; set `unreachable_cidr_block` if a dedicated `/25` range is needed). Set `connection_type = "VPC_PEERING"` with an explicit `ip_allocation` CIDR block only when legacy VPC peering is required.
2. Run the usual Terraform commands from within this directory:

```bash
terraform init
terraform plan
terraform apply
terraform destroy
```

### Troubleshooting

Service account and service-agent IAM propagation waits 3 minutes (`time_sleep.datafusion_service_propagation`) before instance creation. If creation still encounters a transient API permission error on initial deployment, confirm the deploying identity holds `roles/compute.networkAdmin` (or `compute.networkAttachments.create`) in `network_project_id` and re-run `terraform apply`.

## Verification of a successful deployment
Navigate to [Data Fusion](https://console.cloud.google.com/data-fusion) within the GCP console to verify whether the resources have been created.
<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [core_project_id](variables.tf#L25) | Core project ID. | <code>string</code> | ✓ |  |
| [kms_keyring_name](variables.tf#L46) | KMS Keyring. | <code>string</code> | ✓ |  |
| [main_project_id](variables.tf#L51) | Project id. | <code>string</code> | ✓ |  |
| [name](variables.tf#L56) | Name of DataFusion instance. | <code>string</code> | ✓ |  |
| [network_name](variables.tf#L61) | Full path to VPC. | <code>string</code> | ✓ |  |
| [network_project_id](variables.tf#L66) | Landing project id. | <code>string</code> | ✓ |  |
| [region](variables.tf#L71) | Location to deploy job. | <code>string</code> | ✓ |  |
| [subnetwork_name](variables.tf#L76) | Full path to subnet. | <code>string</code> | ✓ |  |
| [connection_type](variables.tf#L15) | Private Data Fusion connection type ('PRIVATE_SERVICE_CONNECT_INTERFACES' or 'VPC_PEERING'). | <code>string</code> |  | <code>&#34;PRIVATE_SERVICE_CONNECT_INTERFACES&#34;</code> |
| [ip_allocation](variables.tf#L30) | Allocated /22 CIDR range for Data Fusion private instances when connection_type is VPC_PEERING. | <code>string</code> |  | <code>null</code> |
| [kms_key_name](variables.tf#L40) | Full path to KMS key for pubsub. | <code>string</code> |  | <code>null</code> |
| [unreachable_cidr_block](variables.tf#L81) | Optional /25 CIDR block to assign to the Data Fusion PSC instance when connection_type is PRIVATE_SERVICE_CONNECT_INTERFACES. | <code>string</code> |  | <code>null</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [id](outputs.tf#L15) | Fully qualified instance id. |  |
| [resource](outputs.tf#L20) | DataFusion resource. |  |
| [service_endpoint](outputs.tf#L25) | DataFusion Service Endpoint. |  |
| [version](outputs.tf#L30) | DataFusion version. |  |
<!-- END TFDOC -->
