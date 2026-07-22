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

# Cloud Composer

<!-- BEGIN TOC -->
- [Introduction of Cloud Composer](#introduction-of-cloud-composer)
- [Cloud Composer Blueprint](#cloud-composer-blueprint)
- [Disclaimer](#disclaimer)
- [Prerequisites](#prerequisites)
- [Deployment Steps](#deployment-steps)
- [Verification of a successful deployment](#verification-of-a-successful-deployment)
- [Variables](#variables)
- [Outputs](#outputs)
<!-- END TOC -->

## Introduction of Cloud Composer  
Based on the open source Apache Airflow project, the Cloud Composer provides infrastructural support for workflows. It supports creating, scheduling, monitoring and managing workflows environments across clouds and data centers. 

## Cloud Composer Blueprint
This blueprint demonstrates how to deploy cloud composer on Google Cloud Platform (GCP). Directed Acyclic Graphs (DAGs) are created as a collection of tasks or workflows in a schedule. The purpose is ensuring the execution of tasks are completed in a particular order at the correct times, this is because each task can perform multiple functions. There are 4 main components: GKE Cluster, Airflow Web Server, Airflow Database, Cloud Storage Bucket. The GKE Cluster is where the DAG's can be triggered to run automatically in the existing workflow sequence, as a response or manually. In the Cloud Composer's core, the environment, the composer components run instances. The Airflow Web Server is a log to monitor progress of the workflows, the Database stores long term details of the flow. Finally the Cloud storage bucket, stores access to files of the flow. In order for there to be a flow in the access of files, Connections provide access to each of the various services, and hooks will provide access with other external services through the connections. Uploaded DAG's are sent to the composer environment where each individual tasks is executed by leveraging connections and hooks to interact with other systems. 

## Disclaimer 
The present GCP Terraform Module in this project is set up and intended to be implemented in a FEDRAMP High environment using the Assured Workloads within the Google Cloud Platform (GCP) organization. For Cloud Composer, the core components must be placed directly into the specific network area. The main project must have access/permission from the Shared VPC owner to build in the network or there will be a failed deployment. For a successful deployment, run time is around 25 minutes and destroying it will take around 8 minutes.

## Prerequisites
1. Service Account User role (roles/iam.serviceAccountUser) for deploying user.


## Deployment Steps
You should see this README and some terraform files.
1. Run cp terraform.tfvars.sample terraform.tfvars to copy the sample variables to your own tfvars file.

2. Update the variables as necessary in your tfvars file.
3. To provision this example, run the following from within this directory:

```terraform init ```<br />
```terraform plan``` to see the infrastructure plan<br />
```terraform apply``` to apply the infrastructure build<br />
```terraform destroy``` to destroy the built infrastructure<br />

## Verification of a successful deployment
Use GCP console to verify if the resources have been created.

<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [composer_env_name](variables.tf#L2) | Name of the Composer environment. | <code>string</code> | ✓ |  |
| [main_project_id](variables.tf#L13) | Main project ID. | <code>string</code> | ✓ |  |
| [network_name](variables.tf#L18) | Full path to VPC. | <code>string</code> | ✓ |  |
| [network_project_id](variables.tf#L23) | The ID of the landing zone project where the VPC is. | <code>string</code> | ✓ |  |
| [subnetwork_name](variables.tf#L52) | The name of the existing subnetwork to use within the specified VPC network and region. | <code>string</code> | ✓ |  |
| [composer_version](variables.tf#L7) | Cloud composer version. | <code>string</code> |  | <code>&#34;composer-3-airflow-2&#34;</code> |
| [region](variables.tf#L28) | Google Cloud Region. | <code>string</code> |  | <code>&#34;us-east4&#34;</code> |
| [sa_account_id](variables.tf#L34) | Service account id. | <code>string</code> |  | <code>&#34;composer-env-account&#34;</code> |
| [sa_display_name](variables.tf#L40) | Service account display name. | <code>string</code> |  | <code>&#34;Service Account for Composer Environment&#34;</code> |
| [service_agent_version](variables.tf#L46) | Composer Service Agent version. This must correspond to Composer version. | <code>string</code> |  | <code>&#34;roles&#47;composer.ServiceAgentV2Ext&#34;</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [airflow_uri](outputs.tf#L1) | URI for Airflow. |  |
| [composer_id](outputs.tf#L6) | Cloud composer id. |  |
<!-- END TFDOC -->
