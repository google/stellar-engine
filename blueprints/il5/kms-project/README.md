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

# Cloud KMS Project Blueprint
This blueprint demonstrates how to manage existing Google Cloud Key Management Service (Cloud KMS) KeyRings and CryptoKeys, applying IAM policies and potentially other configurations (like rotation policies) to them within a multi-project GCP environment. It assumes KMS infrastructure is created by a foundational layer.

<!-- BEGIN TFDOC -->
- [Cloud KMS Project Blueprint](#cloud-kms-project-blueprint)
- [Introduction](#introduction)
- [Disclaimer](#disclaimer)
- [Prerequisites](#prerequisites)
- [Deployment Steps](#deployment-steps)
- [Verification](#verification)
- [Important Notes](#important-notes)
- [Variables](#variables)
- [Outputs](#outputs)
<!-- END TFDOC -->

## Introduction
Google Cloud Key Management Service (Cloud KMS) lets you create and manage encryption keys for use in compatible Google Cloud services and in your own applications. This blueprint facilitates central management by applying additional policies or configurations to KMS KeyRings and CryptoKeys that are already provisioned by your organization's foundational infrastructure.

It allows you to:
- Grant specific IAM roles to users or groups on existing CryptoKeys.
- Manage properties like key rotation periods on existing keys.
- Centralize management of access to critical encryption keys across different projects.

## Disclaimer
- The present GCP Terraform Module in this project is set up and intended to be implemented in either a FedRAMP-High or IL5 (Impact Level 5) environment using the Assured Workloads within the Google Cloud Platform (GCP) organization.
- Assured Workloads in both environments ensures that sensitive data and workloads in GCP adhere to the rigorous security standards mandated by the DoD, making it suitable for government agencies.

## Prerequisites
Before deploying this blueprint, ensure the following are in place:

1.  **Google Cloud Projects:**
    * A **main project** (`var.main_project_id`) which will host the IAM bindings managed by this blueprint (this should typically be the project where the existing KMS keys reside).
    * A **core project** (`var.core_project_id`) if your existing KMS KeyRings and CryptoKeys are provisioned in a different dedicated core project than your `main_project_id`.
2.  **Existing Cloud KMS Infrastructure:**
    * You must have an existing Cloud KMS KeyRing (`var.existing_kms_keyring_name`) and one or more existing CryptoKeys (`var.existing_kms_keys`) already provisioned in your `core_project_id` (or `main_project_id`).
    * This blueprint **consumes existing KMS infrastructure; it does not create new KeyRings or CryptoKeys.**
3.  **Permissions:** The service account or user deploying this blueprint must have:
    * `roles/owner` or sufficient granular permissions (e.g., `cloudkms.admin`, `serviceusage.serviceUsageAdmin`, `resourcemanager.projectIamAdmin`) in the `main_project_id` (and `core_project_id` if different).
    * Specific IAM roles to manage IAM on KMS keys (e.g., `roles/cloudkms.admin`, `roles/cloudkms.viewer`, `roles/resourcemanager.organizationViewer` if policies are org-level) on the project where the keys reside.
    * The `Cloud KMS API` (`cloudkms.googleapis.com`) enabled in the `main_project_id`. This blueprint attempts to enable it automatically.

## Deployment Steps
1.  **Configure Variables:**
    * Copy the sample variables file:
        ```bash
        cp terraform.tfvars.sample terraform.tfvars
        ```
    * Open `terraform.tfvars` and update the placeholder values (`xxxx-xxxx-main-0`, `my-existing-keyring`, `user@yourdomain.com`, etc.) with your actual project IDs, existing KMS KeyRing/CryptoKey names, and any IAM members you wish to manage.

2.  **Initialize Terraform:**
    ```bash
    terraform init
    ```

3.  **Review Plan:**
    ```bash
    terraform plan
    ```
    Carefully review the proposed changes (e.g., new IAM bindings, updated key properties) before applying.

4.  **Apply Changes:**
    ```bash
    terraform apply
    ```
    Type `yes` when prompted to confirm the deployment.

5.  **Destroy Infrastructure (Optional):**
    If you wish to remove the policies or configurations managed by this blueprint:
    ```bash
    terraform destroy
    ```
    Type `yes` when prompted to confirm.
    *Note: This will NOT destroy your underlying KMS KeyRings or CryptoKeys, only the policies and configurations managed by this blueprint.*

## Verification
To verify a successful deployment:

1.  **Google Cloud Console:**
    * Navigate to **Security** > **Key Management** in your `main_project_id` (or `core_project_id` where the keys reside).
    * Verify the existence of the KeyRing (`var.existing_kms_keyring_name`).
    * Click on the KeyRing, then click on a specific CryptoKey (`var.existing_kms_keys`).
    * On the CryptoKey's details page, check the **Permissions** tab to confirm that the specified IAM roles (e.g., `roles/cloudkms.cryptoKeyEncrypterDecrypter`) have been granted to the correct users/groups/service accounts.
    * If rotation policies were managed, confirm those settings as well.

2.  **`gcloud` CLI:**
    * **Describe the KeyRing:**
        ```bash
        gcloud kms key-rings describe <KEYRING_NAME> --location=<REGION> --project=<CORE_PROJECT_ID>
        ```
    * **Describe a CryptoKey:**
        ```bash
        gcloud kms keys describe <KEY_NAME> --keyring=<KEYRING_NAME> --location=<REGION> --project=<CORE_PROJECT_ID>
        ```
    * **Get IAM Policy for a CryptoKey:**
        ```bash
        gcloud secrets keys get-iam-policy <KEY_NAME> --keyring=<KEYRING_NAME> --location=<REGION> --project=<CORE_PROJECT_ID>
        ```

## Important Notes
-   This blueprint strictly **manages existing KMS KeyRings and CryptoKeys**; it does not create them. Your KMS infrastructure is assumed to be provisioned by a foundational Terraform layer or other means.
-   KMS KeyRings and CryptoKeys are **regional resources** (or global for multi-region KeyRings). Ensure `var.gcp_region` matches the location of your existing KeyRing.
-   The `roles/cloudkms.cryptoKeyEncrypterDecrypter` role is a common permission for services to use KMS keys for encryption/decryption. This blueprint allows you to grant this (and other) roles to specific principals on your existing keys.

<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [main_project_id](variables.tf#L1) | The Google Cloud Project ID where KMS-related IAM policies will be managed (i.e., the project where the existing KMS keys reside). | <code>string</code> | ✓ |  |
| [gcp_region](variables.tf#L6) | The Google Cloud region where the existing KMS KeyRing is located. This will also be used as the default region for the provider. | <code>string</code> | ✓ |  |
| [core_project_id](variables.tf#L11) | The Google Cloud Project ID where the existing KMS KeyRing and CryptoKeys are actually provisioned (this could be the same as `main_project_id`). | <code>string</code> | ✓ |  |
| [existing_kms_keyring_name](variables.tf#L16) | The name of the existing Cloud KMS KeyRing to manage or apply policies to. | <code>string</code> | ✓ |  |
| [existing_kms_keys](variables.tf#L20) | A map where keys are the names of existing CryptoKeys within the specified KeyRing, and values are objects defining additional properties (e.g., IAM members to add). | <code title="map&#40;object&#40;&#123;&#10;  iam_members &#61; optional&#40;map&#40;list&#40;string&#41;, &#123;&#125;&#41;&#10;  rotation_period_s &#61; optional&#40;number&#41;&#10;&#125;&#41;&#41;">map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> |  | <code>&#123;&#125;</code> |
| [email](variables.tf#L29) | Email address of a user to grant permissions on KMS keys (if used in `existing_kms_keys.iam_members`). | <code>string</code> |  | <code>null</code> |
| [group_email](variables.tf#L35) | An email address that represents a Google group to grant permissions on KMS keys (if used in `existing_kms_keys.iam_members`). | <code>string</code> |  | <code>null</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [managed_keyring_id](outputs.tf#L16) | The fully qualified ID of the existing KMS KeyRing being managed by this blueprint. |  |
| [managed_keyring_name](outputs.tf#L21) | The name of the existing KMS KeyRing being managed by this blueprint. |  |
| [managed_key_self_links](outputs.tf#L26) | A map of names to self-links for the existing CryptoKeys being managed by this blueprint. |  |
| [managed_key_ids](outputs.tf#L33) | A map of names to fully qualified IDs for the existing CryptoKeys being managed by this blueprint. |  |
<!-- END TFDOC -->
