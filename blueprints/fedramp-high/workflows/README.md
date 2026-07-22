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

<!-- BEGIN TOC -->
- [Introduction to Workflows](#introduction-to-workflows)
- [Disclaimer](#disclaimer)
- [Deployment Steps](#deployment-steps)
- [Demo](#demo)
- [Next Steps](#next-steps)
- [Note](#note)
- [Variables](#variables)
- [Outputs](#outputs)
<!-- END TOC -->

# Workflows Blueprint
This blueprint demonstrates how to create a workflow on Google Cloud Platform (GCP) with Customer-Managed Encryption Keys (CMEK) using Cloud KMS.

## Introduction to Workflows
Workflows is a fully managed orchestration platform that executes services in an order that you define. These workflows can combine services including custom services hosted on Cloud Run or Cloud Run functions, Google Cloud services such as Cloud Vision AI and BigQuery, and any HTTP-based API.
By incorporating Workflows into solutions, you can make service dependencies explicit and observable end-to-end. A workflow that specifies an application, operational, or business process provides a source-of-truth or canonical narrative for the process.

## Disclaimer
- The present GCP Terraform Module in this project is set up and intended to be implemented in a FEDRAMP High environment using the Assured Workloads within the Google Cloud Platform (GCP) organization.

## Deployment Steps
1. Copy the contents of the terraform.tfvars.sample file into your own terraform.tfvars file, then update the variables in this file.
1. The usual terraform commands will be used to deploy the workflow. To provision this example, run the following from within this directory:

```terraform init ```<br />
```terraform plan``` to see the infrastructure plan<br />
```terraform apply``` to apply the infrastructure build<br />
```terraform destroy``` only if you wish to destroy the built infrastructure<br />

1. Attempt to run terraform apply again. If this doesn't work, you should also manually enable the [workflows api](https://console.developers.google.com/apis/api/workflows.googleapis.com). After enabling the API, you may need to wait a few minutes for the changes to propagate.
1. If none of the previous steps work, manually create a workflow in your project (you do not need to configure anything in this workflow, GCP will create the necessary service agent after you deploy at least one workflow).
1. To verify a successful deployment, search for "Workflows" in the Google Cloud Console. From here, you will be able to view your newly created workflow.

## Demo
1. Click on your newly created workflow.
2. Click the ```Execute``` button.
3. For this demo, you can leave the input and logging level empty, then click ```Execute``` at the bottom of the screen.
4. Wait for the workflow to run, then view the output in the output box.

## Next Steps
Workflows can be used to automate various processes, connect different GCP services, and create end to end solutions. View the [workflow documentation](https://cloud.google.com/workflows/docs/best-practice) to learn about some of the capabilities of workflows.
You can also start a workflow execution through Eventarc triggers, Cloud Scheduler, Cloud Tasks, or even another workflow. Configure the workflow for your specific use case.

## Note
KMS/CMEK is not currently working for Workflows in Terraform as a cyclical dependency is created; the Workflow instance creates the Workflow Service Account, but the Service Account must have proper KMS permissions prior to the instance creation.
<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [main_project_id](variables.tf#L31) | The Google Project ID. | <code>string</code> | ✓ |  |
| [name](variables.tf#L36) | Name of the workflow. | <code>string</code> | ✓ |  |
| [region](variables.tf#L41) | The Google Cloud region. | <code>string</code> | ✓ |  |
| [deletion_protection](variables.tf#L1) | Deletion protection. | <code>bool</code> |  | <code>true</code> |
| [description](variables.tf#L7) | Description of the workflow. | <code>string</code> |  | <code>null</code> |
| [env_vars](variables.tf#L13) | Environment variables made available to your workflow execution. | <code>map&#40;string&#41;</code> |  | <code>null</code> |
| [file](variables.tf#L19) | File path to the instructions for the workflow. | <code>string</code> |  | <code>&#34;code&#47;example.yaml&#34;</code> |
| [logging_level](variables.tf#L25) | Logging level of workflow executions. | <code>string</code> |  | <code>&#34;LOG_ERRORS_ONLY&#34;</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [service_account](outputs.tf#L1) | The workflow service account. |  |
| [workflow](outputs.tf#L6) | The newly created workflow. |  |
<!-- END TFDOC -->
