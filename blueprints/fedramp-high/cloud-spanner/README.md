# Cloud Spanner

<!-- BEGIN TOC -->
- [Introduction to Cloud Spanner](#introduction-to-cloud-spanner)
- [Cloud Spanner Blueprint](#cloud-spanner-blueprint)
- [Disclaimer](#disclaimer)
- [Deployment Steps](#deployment-steps)
- [Verification of a successful deployment](#verification-of-a-successful-deployment)
- [Variables](#variables)
- [Outputs](#outputs)
<!-- END TOC -->

## Introduction to Cloud Spanner
Google Cloud Spanner is a fully managed, globally distributed relational database offering strong consistency and a familiar SQL interface. Its core components are highly available instances that provide ACID-compliant transactions and horizontal scalability. Spanner supports features like automatic sharding, managed backup and restore, point-in-time recovery, and Change Streams for real-time data integration, all within a "no-ops" managed service designed for mission-critical workloads.

## Cloud Spanner Blueprint
A Cloud Spanner blueprint enables the creation of Spanner Instances (regional or multi-regional, impacting latency and availability) and databases with defined SQL schemas. Key configurations include Change Streams for real-time data synchronization and establishing managed backup and restore policies for data protection. This blueprint delivers transactional consistency at global scale, supports high query volumes, simplifies operations through full management, and provides enterprise-grade security and compliance for critical applications.

## Disclaimer
- The present GCP Terraform Module in this project is set up and intended to be implemented in a FEDRAMP High environment using the Assured Workloads within the Google Cloud Platform (GCP) organization.

## Deployment Steps
You should see this README and Terraform configuration files.
1. Update your variables in `terraform.tfvars` (copied from `terraform.tfvars.sample`):
   - `main_project_id`: Google Cloud project ID where the Spanner instance and database are created.
   - `region` and `config_name`: Deployment region (such as `us-east4`) and matching Spanner instance configuration (such as `regional-us-east4`).
   - `instance_name`, `display_name`, and `database_name`: Spanner instance ID, display name, and database name.
   - `database_user`: Database IAM principal (`user:...`, `group:...`, or `serviceAccount:...`) granted database admin access.
   - `kms_key_name`: Optional regional Cloud KMS CryptoKey resource path matching the Spanner instance location for CMEK encryption (leave `null` for Google-managed encryption).
2. Run the standard Terraform workflow from within this directory:

```bash
terraform init
terraform plan
terraform apply
terraform destroy
```

## Verification of a successful deployment
Use GCP console to verify if the resources have been created.
https://console.cloud.google.com/spanner
<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [database_name](variables.tf#L21) | Database name. | <code>string</code> | ✓ |  |
| [database_user](variables.tf#L26) | Database user or group. Must start with \"user:\" or \"group:\" or \"serviceAccount:\". | <code>string</code> | ✓ |  |
| [display_name](variables.tf#L35) | Cloud spanner display name. | <code>string</code> | ✓ |  |
| [instance_name](variables.tf#L56) | Cloud spanner instance name. | <code>string</code> | ✓ |  |
| [main_project_id](variables.tf#L77) | Project to deploy Cloud Spanner instance. | <code>string</code> | ✓ |  |
| [config_name](variables.tf#L15) | Cloud spanner instance config name. | <code>string</code> |  | <code>&#34;regional-us-east4&#34;</code> |
| [edition](variables.tf#L40) | The Spanner instance edition. Valid values are 'EDITION_UNSPECIFIED', 'STANDARD', 'ENTERPRISE', or 'ENTERPRISE_PLUS'. | <code>string</code> |  | <code>&#34;ENTERPRISE&#34;</code> |
| [high_priority_cpu_utilization_percent](variables.tf#L50) | High priority cpu utilization percent. | <code>number</code> |  | <code>75</code> |
| [kms_key_name](variables.tf#L61) | Cloud KMS crypto key that encrypts the Spanner database, in the format projects/../locations/../keyRings/../cryptoKeys/... The key location must match the location of the instance configuration, such as us-east4 for regional-us-east4. The blueprint passes a single key, so instance configurations that need one key per replica region are not supported. Leave null to use Google-managed encryption. Setting or changing the key on an existing database forces replacement of the database, which the database deletion protection blocks. | <code>string</code> |  | <code>null</code> |
| [max_processing_units](variables.tf#L82) | Max processing units for autoscaling. | <code>number</code> |  | <code>3000</code> |
| [min_processing_units](variables.tf#L88) | Min processing units for autoscaling. | <code>number</code> |  | <code>2000</code> |
| [region](variables.tf#L94) | Region to create your App Engine resource. | <code>string</code> |  | <code>&#34;us-east4&#34;</code> |
| [storage_utilization_percent](variables.tf#L100) | Storage utilization percent. | <code>number</code> |  | <code>90</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [instance](outputs.tf#L15) | Cloud spanner instance. |  |
<!-- END TFDOC -->
