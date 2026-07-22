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

# Google Cloud Pub/Sub Project Blueprint
This blueprint creates a Google Cloud Pub/Sub topic and associated service accounts, configured for Customer-Managed Encryption Keys (CMEK) from an existing KMS key, and supports various subscription types.

<!-- BEGIN TOC -->
- [Google Cloud Pub/Sub Project Blueprint](#google-cloud-pubsub-project-blueprint)
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
Google Cloud Pub/Sub is an asynchronous and scalable messaging service that decouples services producing messages (publishers) from services processing those messages (subscribers). It's commonly used for streamlining analytics, data integration pipelines, and event-driven architectures.

This blueprint provisions a Pub/Sub topic, sets up custom publisher and subscriber service accounts, grants necessary IAM roles, and integrates with your existing Cloud KMS infrastructure for Customer-Managed Encryption Keys (CMEK).

## Disclaimer
- The present GCP Terraform Module in this project is set up and intended to be implemented in either a FedRAMP-High or IL5 (Impact Level 5) environment using the Assured Workloads within the Google Cloud Platform (GCP) organization.
- Assured Workloads in both environments ensures that sensitive data and workloads in GCP adhere to the rigorous security standards mandated by the DoD, making it suitable for government agencies.

## Prerequisites
Before deploying this blueprint, ensure the following are in place:

1.  **Google Cloud Projects:**
    * A **main project** (`var.main_project_id`) where the Pub/Sub topic and associated service accounts will be created.
    * A **core project** (`var.core_project_id`) where your existing Cloud KMS Key Ring and CryptoKey (used for Pub/Sub topic encryption) are provisioned.
2.  **Existing Cloud KMS Infrastructure:**
    * You must have an existing Cloud KMS Key Ring (`var.kms_keyring_name`) and CryptoKey (`var.kms_key_name`) provisioned in your `core_project_id`. These keys will be used for CMEK on your Pub/Sub topic.
    * This blueprint **consumes existing KMS infrastructure**; it does not create new KMS KeyRings or CryptoKeys.
3.  **Permissions:** The service account or user deploying this blueprint must have:
    * `roles/owner` or sufficient granular permissions (e.g., `pubsub.admin`, `serviceusage.serviceUsageAdmin`, `resourcemanager.projectIamAdmin`) in the `main_project_id`.
    * `roles/cloudkms.viewer` in the `core_project_id` (to read KMS key details).
    * `roles/cloudkms.cryptoKeyEncrypterDecrypter` on the specific KMS key used by the Pub/Sub service account. This blueprint handles that grant.
    * The `Cloud Pub/Sub API` (`pubsub.googleapis.com`) and `Cloud KMS API` (`cloudkms.googleapis.com`) enabled in the `main_project_id`. This blueprint attempts to enable the Pub/Sub API automatically.

## Deployment Steps
1.  **Configure Variables:**
    * Copy the sample variables file:
        ```bash
        cp terraform.tfvars.sample terraform.tfvars
        ```
    * Open `terraform.tfvars` and update the placeholder values (`xxxx-xxxx-main-0`, `xxxx-xxxx-iac-core-0`, etc.) with your actual project IDs, Pub/Sub topic name, region, and existing KMS key details.

2.  **Initialize Terraform:**
    ```bash
    terraform init
    ```

3.  **Review Plan:**
    ```bash
    terraform plan
    ```
    Carefully review the proposed infrastructure changes (e.g., new Pub/Sub topic, service accounts, IAM bindings) before applying.

4.  **Apply Changes:**
    ```bash
    terraform apply
    ```
    Type `yes` when prompted to confirm the deployment.

5.  **Destroy Infrastructure (Optional):**
    If you wish to remove the deployed Pub/Sub topic and associated resources:
    ```bash
    terraform destroy
    ```
    Type `yes` when prompted to confirm.
    *Note: This will NOT destroy your underlying KMS KeyRing or CryptoKey; only the Pub/Sub resources and the IAM permissions granted by this blueprint on your existing KMS key.*

## Verification
To verify a successful deployment:

1.  **Google Cloud Console:**
    * Navigate to **Cloud Pub/Sub** > **Topics** in your `main_project_id`.
    * Confirm that a new topic with the name specified in `var.pubsub_topic` has been created.
    * Click on the topic and check its "Encryption" section to confirm it is using "Customer-managed encryption key" with the correct KMS key.
    * Check **IAM & Admin** > **Service Accounts** for your `publisher_account_id` and `subscriber_account_id`.
    * Check **IAM & Admin** > **IAM** for your `main_project_id` and the KMS key (`core_project_id`) to confirm `pubsub.publisher` and `pubsub.subscriber` roles (project level), and `cloudkms.cryptoKeyEncrypterDecrypter` (on KMS key) are granted to the correct service accounts/principals.

2.  **`gcloud` CLI:**
    * **Describe the Topic:**
        ```bash
        gcloud pubsub topics describe <TOPIC_NAME> --project=<MAIN_PROJECT_ID>
        ```
    * **List Topics:**
        ```bash
        gcloud pubsub topics list --project=<MAIN_PROJECT_ID>
        ```
    * **Get Topic IAM Policy:**
        ```bash
        gcloud pubsub topics get-iam-policy <TOPIC_NAME> --project=<MAIN_PROJECT_ID>
        ```
    * **Get KMS Key IAM Policy:**
        ```bash
        gcloud kms keys get-iam-policy <KMS_KEY_NAME> --keyring=<KMS_KEYRING_NAME> --location=<REGION> --project=<CORE_PROJECT_ID>
        ```

## Important Notes
-   This blueprint strictly **creates a Pub/Sub topic and its associated resources**; it does not consume an existing topic.
-   Pub/Sub topics are **regional or global** resources depending on configuration. `var.gcp_region` will determine the topic's location (persistence region).
-   The `kms_key_name` and `kms_keyring_name` inputs refer to **existing** Cloud KMS resources. This blueprint consumes these existing keys for CMEK on the topic.

<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [allowed_persistence_regions](variables.tf#L1) | A list of Google Cloud regions where messages are allowed to be stored. If empty, the topic will use the default global storage policy. | <code>list&#40;string&#41;</code> |  | <code>&#91;&#34;us-east4&#34;&#93;</code> |
| [core_project_id](variables.tf#L8) | The Google Cloud Project ID where the existing KMS KeyRing and CryptoKeys are provisioned. | <code>string</code> | ✓ |  |
| [kms_key_name](variables.tf#L13) | The full resource path of the existing Cloud KMS CryptoKey to use for Customer-Managed Encryption Keys (CMEK) on the Pub/Sub topic. | <code>string</code> | ✓ |  |
| [kms_keyring_name](variables.tf#L18) | The name of the existing Cloud KMS Key Ring to use for Pub/Sub topic encryption. | <code>string</code> | ✓ |  |
| [main_project_id](variables.tf#L22) | The Google Cloud Project ID where the Pub/Sub topic and associated service accounts will be created. | <code>string</code> | ✓ |  |
| [publisher_account_id](variables.tf#L27) | The ID for the custom service account created for the Pub/Sub publisher (e.g., &#39;my-publisher-sa&#39;). | <code>string</code> |  | <code>&#34;pubsub-publisher-sa&#34;</code> |
| [publisher_name](variables.tf#L33) | The display name for the custom Pub/Sub publisher service account. | <code>string</code> |  | <code>&#34;Pub&#47;Sub Publisher Service Account&#34;</code> |
| [pubsub_topic](variables.tf#L39) | The name of the Pub/Sub topic to be created by this blueprint. | <code>string</code> | ✓ |  |
| [gcp_region](variables.tf#L43) | The Google Cloud region to be used for Pub/Sub topic deployment and as the default for the provider. | <code>string</code> | ✓ |  |
| [subscriber_account_id](variables.tf#L48) | The ID for the custom service account created for the Pub/Sub subscriber (e.g., &#39;my-subscriber-sa&#39;). | <code>string</code> |  | <code>&#34;pubsub-subscriber-sa&#34;</code> |
| [subscriber_name](variables.tf#L54) | The display name for the custom Pub/Sub subscriber service account. | <code>string</code> |  | <code>&#34;Pub&#47;Sub Subscriber Service Account&#34;</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [pubsub_topic_name](outputs.tf#L14) | The name of the created Pub/Sub topic. |  |
| [pubsub_topic_self_link](outputs.tf#L19) | The full resource path (self-link) of the created Pub/Sub topic. |  |
| [publisher_service_account_email](outputs.tf#L24) | The email of the publisher service account. |  |
| [subscriber_service_account_email](outputs.tf#L29) | The email of the subscriber service account. |  |
<!-- END TFDOC -->

