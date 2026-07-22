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
This blueprint demonstrates how to create a Google Cloud Workflow in a multi-project environment, utilizing existing KMS infrastructure for Customer-Managed Encryption Keys (CMEK) and adhering to FedRAMP High / IL5 compliance standards.

## Introduction to Workflows
Workflows is a fully managed orchestration platform that executes services in an order that you define. These workflows can combine services including custom services hosted on Cloud Run or Cloud Run functions, Google Cloud services such as Cloud Vision AI and BigQuery, and any HTTP-based API.
By incorporating Workflows into solutions, you can make service dependencies explicit and observable end-to-end. A workflow that specifies an application, operational, or business process provides a source-of-truth or canonical narrative for the process.

This blueprint specifically configures Google Cloud Workflows to leverage **CMEK** for enhanced data security, utilizing a key provisioned in a dedicated core project.

## Disclaimer
- The present GCP Terraform Module in this project is set up and intended to be implemented in either a FedRAMP-High or IL5 (Impact Level 5) environment using Assured Workloads within the Google Cloud Platform (GCP) organization.
- Assured Workloads in both environments ensures that sensitive data and workloads in GCP adhere to the rigorous security standards mandated by the DoD, making it suitable for government agencies.

## Deployment Steps
1.  **Ensure Prerequisites:** Before deploying this blueprint, you must have the following resources already provisioned, ideally in their respective designated projects:
    * An existing KMS Key Ring in the `core_project_id`.
    * An existing KMS Crypto Key within that Key Ring in the `core_project_id`, configured for encryption purposes.

2.  Copy the contents of the `terraform.tfvars.sample` file into your own `terraform.tfvars` file, then update the variables in this file to match your environment.

3.  The usual Terraform commands will be used to deploy the workflow. To provision this example, run the following from within this directory:

    ```bash
    terraform init
    terraform plan # to see the infrastructure plan
    terraform apply # to apply the infrastructure build
    ```

4.  **API Enablement & Service Agent:** The blueprint automatically enables the Workflows API and ensures the necessary Google-managed service identity for Workflows is created and granted appropriate KMS permissions. Manual intervention for API enablement or service agent creation should generally not be required. If a `Service account ... does not exist` error is encountered during the first `terraform apply`, a simple retry of the `terraform apply` command often resolves it due to Google Cloud's eventual consistency.

5.  To verify a successful deployment, search for "Workflows" in the Google Cloud Console. From here, you will be able to view your newly created workflow and confirm its CMEK configuration.

6.  To destroy the deployed infrastructure:
    ```bash
    terraform destroy # only if you wish to destroy the built infrastructure
    ```

## Demo
1.  Click on your newly created workflow in the Google Cloud Console.
2.  Click the `Execute` button.
3.  For the `code/example.yaml` workflow provided, you can leave the input and logging level empty. Then, click `Execute` at the bottom of the screen.
4.  Wait for the workflow to run, then view the output in the output box. The `example.yaml` fetches the current time and retrieves Wikipedia articles related to the day of the week.

## Next Steps
Workflows can be used to automate various processes, connect different GCP services, and create end-to-end solutions. View the [workflow documentation](https://cloud.google.com/workflows/docs/best-practice) to learn about some of the capabilities of workflows.
You can also start a workflow execution through Eventarc triggers, Cloud Scheduler, Cloud Tasks, or even another workflow. Configure the workflow for your specific use case.

## Note
This blueprint has been refactored to resolve the prior limitation regarding CMEK. The Workflows Google-managed service agent (e.g., `service-PROJECT_NUMBER@gcp-sa-workflows.iam.gserviceaccount.com`) now receives explicit `roles/cloudkms.cryptoKeyEncrypterDecrypter` permissions on the specified KMS key. This allows the Workflows instance to be created successfully with CMEK enabled, ensuring data encryption at rest via customer-managed keys.

## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [main_project_id](variables.tf#L31) | The Google Cloud Project ID where the Workflows resource will be deployed. | <code>string</code> | ✓ |  |
| [name](variables.tf#L36) | Name of the workflow. | <code>string</code> | ✓ |  |
| [region](variables.tf#L41) | The Google Cloud region where the Workflows resource will be deployed and where the KMS key is located (if using CMEK in the same region). | <code>string</code> | ✓ |  |
| [core_project_id](variables.tf#L46) | The Google Cloud Project ID where shared core services like KMS keys are located. | <code>string</code> | ✓ |  |
| [kms_keyring_name](variables.tf#L51) | The name of the existing KMS Key Ring to use for workflow encryption CMEK. | <code>string</code> | ✓ |  |
| [kms_key_name](variables.tf#L56) | The name of the existing KMS Crypto Key to use for workflow encryption CMEK. | <code>string</code> | ✓ |  |
| [deletion_protection](variables.tf#L1) | Deletion protection for the workflow. | <code>bool</code> |  | <code>true</code> |
| [description](variables.tf#L7) | Description of the workflow. | <code>string</code> |  | <code>null</code> |
| [env_vars](variables.tf#L13) | Environment variables made available to your workflow execution. | <code>map&#40;string&#41;</code> |  | <code>null</code> |
| [file](variables.tf#L19) | File path to the instructions for the workflow (e.g., example.yaml). | <code>string</code> |  | <code>&#34;code&#47;example.yaml&#34;</code> |
| [logging_level](variables.tf#L25) | Logging level of workflow executions. Options: CALL_LOG_LEVEL_UNSPECIFIED, LOG_ALL_CALLS, LOG_ERRORS_ONLY, LOG_NONE. | <code>string</code> |  | <code>&#34;LOG_ERRORS_ONLY&#34;</code> |
| [workflow_service_account_id](variables.tf#L61) | The ID for the custom service account created for the workflow (e.g., 'my-workflow-sa'). | <code>string</code> |  | <code>&#34;workflows-sa&#42;</code> |

