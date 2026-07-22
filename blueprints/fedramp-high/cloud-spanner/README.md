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

# Cloud Spanner

- [Introduction to Cloud Spanner](#introduction-to-cloud-spanner)
- [Cloud Spanner Blueprint](#cloud-spanner-blueprint)
- [Disclaimer](#disclaimer)
- [Deployment Steps](#deployment-steps)
- [Verification of a successful deployment](#verification-of-a-successful-deployment)
- [Variables](#variables)
- [Outputs](#outputs)

## Introduction to Cloud Spanner
Google Cloud Spanner is a fully managed, globally distributed relational database offering strong consistency and a familiar SQL interface. Its core components are highly available instances that provide ACID-compliant transactions and horizontal scalability. Spanner supports features like automatic sharding, managed backup and restore, point-in-time recovery, and Change Streams for real-time data integration, all within a "no-ops" managed service designed for mission-critical workloads.

## Cloud Spanner Blueprint
A Cloud Spanner blueprint enables the creation of Spanner Instances (regional or multi-regional, impacting latency and availability) and databases with defined SQL schemas. Key configurations include Change Streams for real-time data synchronization and establishing managed backup and restore policies for data protection. This blueprint delivers transactional consistency at global scale, supports high query volumes, simplifies operations through full management, and provides enterprise-grade security and compliance for critical applications.

## Disclaimer
- The present GCP Terraform Module in this project is set up and intended to be implemented in a FEDRAMP High environment using the Assured Workloads within the Google Cloud Platform (GCP) organization.

## Deployment Steps
You should see this README and some terraform files.
1. Update the Variables in the variables.tf and also the properties within the keys variables. For reference update the following variables and associated properties

- ```project_id```  with your GCP Project ID<br />
- ```region``` with the GCP region <br />
- ```name``` with the desired cloud run name <br />
- ```kms_key``` with the full path to the CMEK key that will be used for encryption <br />
- ```container_image``` with the container to be hosted on the cloud run service <br />


2. There is a sample ```terraform.tfvars.sample``` available as well.
3. Although each use case is somehow built around the previous one they are self-contained so you can deploy any of them at your will. The usual terraform commands will do the work. To provision this example, run the following from within this directory:

```terraform init ```<br />
```terraform plan``` to see the infrastructure plan<br />
```terraform apply``` to apply the infrastructure build<br />
```terraform destroy``` to destroy the built infrastructure<br />

## Verification of a successful deployment
Use GCP console to verify if the resources have been created.
https://console.cloud.google.com/spanner
<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [database_name](variables.tf#L7) | Database name. | <code>string</code> | ✓ |  |
| [database_user](variables.tf#L12) | Database user or group. Must start with \"user:\" or \"group:\" or \"serviceAccount:\". | <code>string</code> | ✓ |  |
| [display_name](variables.tf#L17) | Cloud spanner display name. | <code>string</code> | ✓ |  |
| [instance_name](variables.tf#L38) | Cloud spanner instance name. | <code>string</code> | ✓ |  |
| [main_project_id](variables.tf#L43) | Project to deploy Cloud Spanner instance. | <code>string</code> | ✓ |  |
| [config_name](variables.tf#L1) | Cloud spanner instance config name. | <code>string</code> |  | <code>&#34;regional-us-east4&#34;</code> |
| [edition](variables.tf#L22) | The Spanner instance edition. Valid values are 'EDITION_UNSPECIFIED', 'STANDARD', 'ENTERPRISE', or 'ENTERPRISE_PLUS'. | <code>string</code> |  | <code>&#34;ENTERPRISE&#34;</code> |
| [high_priority_cpu_utilization_percent](variables.tf#L32) | High priority cpu utilization percent. | <code>number</code> |  | <code>75</code> |
| [max_processing_units](variables.tf#L48) | Max processing units for autoscaling. | <code>number</code> |  | <code>3000</code> |
| [min_processing_units](variables.tf#L54) | Min processing units for autoscaling. | <code>number</code> |  | <code>2000</code> |
| [region](variables.tf#L60) | Region to create your App Engine resource. | <code>string</code> |  | <code>&#34;us-east4&#34;</code> |
| [storage_utilization_percent](variables.tf#L66) | Storage utilization percent. | <code>number</code> |  | <code>90</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [instance](outputs.tf#L1) | Cloud spanner instance. |  |
<!-- END TFDOC -->
