# Cloud Spanner

<!-- BEGIN TOC -->
- [Introduction to Cloud Spanner](#introduction-to-cloud-spanner)
- [Cloud Spanner Blueprint](#cloud-spanner-blueprint)
- [Disclaimer](#disclaimer)
- [Deployment Steps](#deployment-steps)
- [Destroying the Database](#destroying-the-database)
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
You should see this README and some terraform files.
1. Run ```cp terraform.tfvars.sample terraform.tfvars``` to copy the sample variables to your own tfvars file.

2. Update the variables as necessary in your tfvars file.
3. The usual terraform commands will do the work. To provision this example, run the following from within this directory:

```terraform init ```<br />
```terraform plan``` to see the infrastructure plan<br />
```terraform apply``` to apply the infrastructure build<br />

## Destroying the Database
When running ```terraform destroy``` to destroy the built infrastructure, an error will occur due to the 'enable_drop_protection' setting in cloud spanner.
1. ensure the ```database_drop_protection``` is set to "false" in the terraform.tfvars file.
2. run ```terraform apply```
3. run ```terraform destroy```

## Verification of a successful deployment
Use GCP console to verify if the resources have been created.
https://console.cloud.google.com/spanner

<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [database_drop_protection](variables.tf#L7) | Cloud spanner level protection against accidental deletion of database in Terraform, gcloud command or Cloud Console. | <code>bool</code> | ✓ |  |
| [database_name](variables.tf#L12) | Database name. | <code>string</code> | ✓ |  |
| [database_user](variables.tf#L17) | Database user or group. Must start with \"user:\" or \"group:\" or \"serviceAccount:\". | <code>string</code> | ✓ |  |
| [display_name](variables.tf#L22) | Cloud spanner display name. | <code>string</code> | ✓ |  |
| [instance_name](variables.tf#L43) | Cloud spanner instance name. | <code>string</code> | ✓ |  |
| [main_project_id](variables.tf#L48) | Project to deploy Cloud Spanner instance. | <code>string</code> | ✓ |  |
| [config_name](variables.tf#L1) | Cloud spanner instance config name. | <code>string</code> |  | <code>&#34;regional-us-east4&#34;</code> |
| [edition](variables.tf#L27) | The Spanner instance edition. Valid values are 'EDITION_UNSPECIFIED', 'STANDARD', 'ENTERPRISE', or 'ENTERPRISE_PLUS'. | <code>string</code> |  | <code>&#34;ENTERPRISE&#34;</code> |
| [high_priority_cpu_utilization_percent](variables.tf#L37) | High priority cpu utilization percent. | <code>number</code> |  | <code>75</code> |
| [max_processing_units](variables.tf#L53) | Max processing units for autoscaling. | <code>number</code> |  | <code>3000</code> |
| [min_processing_units](variables.tf#L59) | Min processing units for autoscaling. | <code>number</code> |  | <code>2000</code> |
| [region](variables.tf#L65) | Region to create your App Engine resource. | <code>string</code> |  | <code>&#34;us-east4&#34;</code> |
| [storage_utilization_percent](variables.tf#L71) | Storage utilization percent. | <code>number</code> |  | <code>90</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [instance](outputs.tf#L1) | Cloud spanner instance. |  |
<!-- END TFDOC -->
