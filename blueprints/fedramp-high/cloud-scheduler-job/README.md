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

# Cloud Scheduler Job Blueprint
This blueprint schedules a cron job to publish messages to an *existing* Google Cloud Pub/Sub topic.

<!-- BEGIN TOC -->
- [Cloud Scheduler Job Blueprint](#cloud-scheduler-job-blueprint)
- [Introduction](#introduction)
- [Disclaimer](#disclaimer)
- [Prerequisites](#prerequisites)
- [Deployment Steps](#deployment-steps)
- [Verification](#verification)
- [Important Notes](#important-notes)
- [Variables](#variables)
- [Outputs](#outputs)
<!-- END TOC -->

## Introduction
Google Cloud Scheduler is a fully managed enterprise-grade cron job service. It allows you to schedule virtually any batch job, big data job, cloud operation, or even trigger App Engine, Cloud Pub/Sub, or HTTP endpoints.

This blueprint specifically focuses on creating a Cloud Scheduler job that publishes a message to an *existing* Cloud Pub/Sub topic on a defined schedule. This approach leverages your existing Pub/Sub infrastructure and aligns with decoupled service patterns.

## Disclaimer
- The present GCP Terraform Module in this project is set up and intended to be implemented in either a FedRAMP-High or IL5 (Impact Level 5) environment using the Assured Workloads within the Google Cloud Platform (GCP) organization.
- Assured Workloads in both environments ensures that sensitive data and workloads in GCP adhere to the rigorous security standards mandated by the DoD, making it suitable for government agencies.

## Prerequisites
Before deploying this blueprint, ensure the following are in place:

1.  **Google Cloud Projects:**
    * A **main project** (`var.main_project_id`) where the Cloud Scheduler job will be created.
    * The Pub/Sub topic you intend to use may reside in this project or a separate project.
    * If the Pub/Sub topic uses CMEK, your KMS key is assumed to be in a `core_project_id`.
2.  **Existing Pub/Sub Topic:**
    * A Pub/Sub topic must already exist to which the Cloud Scheduler job will publish messages. This blueprint **consumes an existing topic**; it does not create it.
    * You will need its full resource path (e.g., `projects/<PROJECT_ID>/topics/<TOPIC_NAME>`).
    * You can provision a Pub/Sub topic using the `blueprints/fedramp-high/pub-sub-project` blueprint.
3.  **Existing Cloud KMS Key (if Pub/Sub Topic uses CMEK):**
    * If your existing Pub/Sub topic uses Customer-Managed Encryption Keys (CMEK), you must have the corresponding Cloud KMS CryptoKey provisioned.
    * This blueprint will grant the Pub/Sub service account (`gcp-sa-pubsub.iam.gserviceaccount.com`) permissions on this KMS key.
4.  **Permissions:** The service account or user deploying this blueprint must have:
    * `roles/owner` or sufficient granular permissions (e.g., `cloudscheduler.admin`, `pubsub.publisher`, `serviceusage.serviceUsageAdmin`, `resourcemanager.projectIamAdmin`) in the `main_project_id`.
    * If the Pub/Sub topic uses CMEK, `roles/cloudkms.cryptoKeyEncrypterDecrypter` should be granted to the Pub/Sub service account (`service-PROJECT_NUMBER@gcp-sa-pubsub.iam.gserviceaccount.com`) on the specific KMS key. This blueprint handles that grant.
    * The `Cloud Scheduler API` (`cloudscheduler.googleapis.com`) and `Cloud Pub/Sub API` (`pubsub.googleapis.com`) enabled in the `main_project_id`. This blueprint attempts to enable the Cloud Scheduler API automatically.

## Deployment Steps
1.  **Configure Variables:**
    * Copy the sample variables file:
        ```bash
        cp terraform.tfvars.sample terraform.tfvars
        ```
    * Open `terraform.tfvars` and update the placeholder values (`xxxx-xxxx-main-0`, `YOUR_PUBSUB_PROJECT_ID`, etc.) with your actual project IDs, existing Pub/Sub topic path, and KMS key path (if applicable).

2.  **Initialize Terraform:**
    ```bash
    terraform init
    ```

3.  **Review Plan:**
    ```bash
    terraform plan
    ```
    Carefully review the proposed infrastructure (Cloud Scheduler job and IAM) changes before applying.

4.  **Apply Changes:**
    ```bash
    terraform apply
    ```
    Type `yes` when prompted to confirm the deployment.

5.  **Destroy Infrastructure (Optional):**
    If you wish to remove the deployed Cloud Scheduler job:
    ```bash
    terraform destroy
    ```
    Type `yes` when prompted to confirm.
    *Note: This will NOT destroy the underlying Pub/Sub topic or KMS key; only the Cloud Scheduler job.*

## Verification
To verify a successful deployment:

1.  **Google Cloud Console:**
    * Navigate to **Operations** > **Cloud Scheduler** in your `main_project_id`.
    * Confirm that your job (`var.name`) has been created and its status is healthy.
    * You can manually "RUN NOW" to trigger the job immediately.
    * To verify the Pub/Sub message: Subscribe a test subscriber to your target Pub/Sub topic and observe if messages are received after the job executes.

2.  **`gcloud` CLI:**
    * **List Jobs:**
        ```bash
        gcloud scheduler jobs list --project=<MAIN_PROJECT_ID> --location=<REGION>
        ```
    * **Describe a Job:**
        ```bash
        gcloud scheduler jobs describe <JOB_NAME> --location=<REGION> --project=<MAIN_PROJECT_ID>
        ```
    * **Manually Run Job:**
        ```bash
        gcloud scheduler jobs run <JOB_NAME> --location=<REGION> --project=<MAIN_PROJECT_ID>
        ```

## Important Notes
-   This blueprint explicitly uses an **existing Pub/Sub topic** as its target. It does not create new Pub/Sub topics.
-   The `schedule` variable uses the [Crontab format](https://en.wikipedia.org/wiki/Cron#CRON_expression).
-   Cloud Scheduler jobs are **regional resources**. Ensure `var.gcp_region` matches your desired deployment region.
-   This blueprint configures a **Pub/Sub target**. Cloud Scheduler also supports HTTP and App Engine targets, which would require modifications to the `main.tf` if desired.

<!-- BEGIN TFDOC -->
## Variables
| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [data](variables.tf#L1) | The base64-encoded data to be sent as the Pub/Sub message payload. | <code>string</code> |  | <code>null</code> |
| [description](variables.tf#L7) | Description of the Cloud Scheduler job. | <code>string</code> | ✓ |  |
| [kms_key_name](variables.tf#L12) | The full resource path of the existing Cloud KMS CryptoKey used for CMEK on the Pub/Sub topic. This key is assumed to be in the `core_project_id`. | <code>string</code> |  | <code>null</code> |
| [main_project_id](variables.tf#L18) | The Google Cloud Project ID where the Cloud Scheduler job will be created. | <code>string</code> | ✓ |  |
| [max_backoff_duration](variables.tf#L23) | The maximum amount of time to wait before retrying a failed attempt, as a duration string (e.g., &#39;5s&#39;, &#39;2m&#39;, &#39;1h&#39;). | <code>string</code> |  | <code>null</code> |
| [max_doublings](variables.tf#L29) | The maximum number of times to double the retry delay, up to `max_retry_duration`. | <code>number</code> |  | <code>null</code> |
| [max_retry_duration](variables.tf#L35) | The maximum cumulative time in which retries are attempted, as a duration string. | <code>string</code> |  | <code>null</code> |
| [min_backoff_duration](variables.tf#L41) | The minimum amount of time to wait before retrying a failed attempt, as a duration string. | <code>string</code> |  | <code>null</code> |
| [name](variables.tf#L47) | The name of the Cloud Scheduler job. | <code>string</code> | ✓ |  |
| [gcp_region](variables.tf#L52) | The Google Cloud region where the Cloud Scheduler job will be deployed. | <code>string</code> | ✓ |  |
| [retry_count](variables.tf#L57) | The number of attempts that the system will make to run the job if the first attempt fails. Retries are attempted over a longer period of time than the schedule. | <code>number</code> |  | <code>null</code> |
| [schedule](variables.tf#L63) | The schedule in the [Crontab format](https://en.wikipedia.org/wiki/Cron#CRON_expression) (e.g., &#39;*/2 * * * *&#39; for every two minutes). | <code>string</code> | ✓ |  |
| [topic_id](variables.tf#L68) | The full resource path of the existing Pub/Sub topic (e.g., `projects/<PROJECT_ID>/topics/<TOPIC_NAME>`) to which messages will be published. | <code>string</code> | ✓ |  |
| [core_project_id](variables.tf#L73) | The Google Cloud Project ID where shared core services like KMS keys are located. Used for referencing existing Pub/Sub topic KMS keys. | <code>string</code> | ✓ |  |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [id](outputs.tf#L1) | Job ID. |  |
| [state](outputs.tf#L6) | Job state. |  |
<!-- END TFDOC -->
