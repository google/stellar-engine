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

# Secret Manager Blueprint
This blueprint demonstrates how to create Google Secret Manager secrets, configure them with Customer-Managed Encryption Keys (CMEK) using Cloud KMS, and manage their IAM permissions, all within a multi-project GCP environment. It guides users on securely adding secret versions outside of Terraform state using a bash script.

<!-- BEGIN TFDOC -->
- [Secret Manager Blueprint](#secret-manager-blueprint)
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
Secret Manager is a secure and convenient storage system for API keys, passwords, certificates, and other sensitive data. It enables robust secret management with Cloud IAM roles, versioning, audit logging, and automated rotation capabilities.

This blueprint focuses on securely provisioning Secret Manager secrets with CMEK, emphasizing a method to prevent sensitive data from being stored in your Terraform state file.

## Disclaimer
- The present GCP Terraform Module in this project is set up and intended to be implemented in either a FedRAMP-High or IL5 (Impact Level 5) environment using the Assured Workloads within the Google Cloud Platform (GCP) organization.
- Assured Workloads in both environments ensures that sensitive data and workloads in GCP adhere to the rigorous security standards mandated by the DoD, making it suitable for government agencies.

## Prerequisites
Before deploying this blueprint, ensure the following are in place:

1.  **Google Cloud Projects:**
    * A **main project** (`var.main_project_id`) where the Secret Manager secrets will be created.
    * A **core project** (`var.core_project_id`) where your existing Cloud KMS Key Rings and Crypto Keys (used for secret encryption) are located.
2.  **Existing Cloud KMS Keys:**
    * You must have existing Cloud KMS Key Rings and Crypto Keys provisioned in your `core_project_id`. These keys will be used for Customer-Managed Encryption Keys (CMEK) for your secrets.
    * This blueprint consumes existing KMS keys; it does not create them.
3.  **Permissions:** The service account or user deploying this blueprint must have:
    * `roles/owner` or sufficient granular permissions (e.g., `secretmanager.admin`, `serviceusage.serviceUsageAdmin`, `resourcemanager.projectIamAdmin`) in the `main_project_id`.
    * `roles/cloudkms.viewer` in the `core_project_id` (to read KMS key details).
    * `roles/cloudkms.cryptoKeyEncrypterDecrypter` on the specific KMS keys used by the Secret Manager service account.
    * The `Secret Manager API` (`secretmanager.googleapis.com`) and `Cloud KMS API` (`cloudkms.googleapis.com`) enabled in the `main_project_id`. This blueprint attempts to enable them automatically.
4.  **Bash Script for Secret Versions (Security Best Practice):**
    * This blueprint explicitly avoids managing secret *versions* (the actual sensitive data) directly in Terraform state for security reasons. Instead, it relies on a separate bash script (`add_secret_versions.sh`) and the `gcloud` CLI.
    * Ensure this script is available in your deployment environment and configured correctly (see Deployment Steps).

## Deployment Steps
1.  **Configure Variables:**
    * Copy the sample variables file:
        ```bash
        cp terraform.tfvars.sample terraform.tfvars
        ```
    * Open `terraform.tfvars` and update the placeholder values (`xxxx-xxxx-main-0`, `xxxx-xxxx-iac-core-0`, etc.) with your actual project IDs, region, and existing KMS key self-links.

2.  **Initialize Terraform:**
    ```bash
    terraform init
    ```

3.  **Review Plan:**
    ```bash
    terraform plan
    ```
    Carefully review the proposed infrastructure (secrets and IAM) changes before applying.

4.  **Apply Changes (Provision Secrets Metadata & IAM):**
    ```bash
    terraform apply
    ```
    Type `yes` when prompted to confirm the deployment.
    *This step creates the secret resources in Secret Manager and assigns IAM roles, but does NOT upload secret data (versions).*

5.  **Add Secret Versions (Securely, using Bash Script):**
    * **Step 5.1: Prepare Secret Data Files:**
        * There is an example directory named `secrets/` in the same root location as your `add_secret_versions.sh` script.
        * There are example files in this `secrets/` directory, named as `<SECRET_ID>.txt` (e.g., `secrets/secret-id-one.txt` for a secret named `secret-id-one`). You can use these for example purposes, and add others you want to upload.
    * **Step 5.2: Ensure Script Executability:**
        ```bash
        chmod +x add_secret_versions.sh
        ```
    * **Step 5.3: Authenticate `gcloud` CLI:** Ensure your `gcloud` CLI is authenticated with a service account or user that has the required permissions to create and manage secret versions (`roles/secretmanager.secretVersionManager` or `roles/secretmanager.admin`).
    * **Step 5.4: Run the Script with Arguments:**
        * The script now accepts command-line arguments. You can run it with just the project ID to auto-discover secrets from the `secrets/` directory:
            ```bash
            ./add_secret_versions.sh --project-id <YOUR_MAIN_PROJECT_ID>
            ```
        * Alternatively, you can specify individual secret IDs and/or a custom data directory:
            ```bash
            ./add_secret_versions.sh --project-id <YOUR_MAIN_PROJECT_ID> --secret-ids secret-id-one,secret-id-two --data-dir my-custom-secret-data-folder
            ```
        * You should see messages indicating successful version uploads. If not, check the script output for errors related to permissions or file paths.
    * **Step 5.5 (Recommended): Clean Up Local Secret Files:** It is highly recommended to delete the local secret data files after you successfully run this script and the versions are uploaded.

6.  **Destroy Infrastructure (Optional):**
    If you wish to remove the deployed Secret Manager secrets (and their versions):
    ```bash
    terraform destroy
    ```
    Type `yes` when prompted to confirm.

## Verification
To verify a successful deployment:

1.  **Google Cloud Console:**
    * Navigate to **Security** > **Secret Manager** in your `main_project_id`.
    * Confirm that your secrets (e.g., "secret-id-one", "secret-id-two") have been created.
    * Click on each secret. Verify that it has a **version** associated with it (from the script) and that its **encryption status** shows "Customer-managed encryption key" with the correct KMS key linked.

2.  **`gcloud` CLI:**
    * **List Secrets:**
        ```bash
        gcloud secrets list --project=<MAIN_PROJECT_ID>
        ```
    * **Describe a Secret (and its versions):**
        ```bash
        gcloud secrets describe <SECRET_ID> --project=<MAIN_PROJECT_ID>
        gcloud secrets versions list <SECRET_ID> --project=<MAIN_PROJECT_ID>
        ```
    * **Access Secret Data (for testing, use with caution):**
        ```bash
        gcloud secrets versions access latest --secret=<SECRET_ID> --project=<MAIN_PROJECT_ID>
        ```

## Important Notes
-   This blueprint explicitly uses a **bash script (`add_secret_versions.sh`) to upload secret versions**, rather than managing `secret_data` directly in Terraform. This is a crucial **security best practice** to prevent sensitive secret values from being stored in your Terraform state file in unencrypted form, accessible to anyone who can read or pull the state.
-   Secret Manager secrets are **regional resources**. The `location` specified for each secret determines where its encrypted replicas are stored.
-   **GCE Instance for Secret Upload (Optional):** If you prefer to upload secrets from a Compute Engine instance instead of doing it locally, you can provision a compatible VM using the `blueprints/il5/compute-engine` blueprint.
    * Once the VM is provisioned, you would then copy the `add_secret_versions.sh` script and your secret data files to this VM, and run the script from within the instance. Remember to delete the secret files from the VM and terminate the instance after use.

<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [main_project_id](variables.tf#L1) | The Google Cloud Project ID where the NCC hub will be created. | <code>string</code> | ✓ |  |
| [iam](variables.tf#L1) | IAM bindings in {SECRET => {ROLE => [MEMBERS]}} format. | <code>map&#40;map&#40;list&#40;string&#41;&#41;&#41;</code> |  | <code>&#123;&#125;</code> |
| [gcp_region](variables.tf#L12) | The Google Cloud region to be used as the default for regional resources and the provider. Note: Secret Manager secrets are regional resources. | <code>string</code> |  | <code>&#34;us-east4&#34;</code> |
| [secrets](variables.tf#L18) | Map of secret configurations. Each key is the `secret_id` (name) of the secret. Each value is an object with optional `expire_time`, `version_destroy_ttl`, `locations` (list of regions for user-managed replication), and `keys` (a map where keys are replication locations (or 'global') and values are full KMS CryptoKey self-links for encryption). | <code title="map&#40;object&#40;&#123;&#10;  location &#61; string &#35; A location is required for every secret&#10;  key      &#61; string &#35; A key is required for the location &#40;the key and secret must be in the same region&#41;&#10;  expire_time &#61; optional&#40;string&#41;&#10;  version_destroy_ttl &#61; optional&#40;string&#41;&#10;&#125;&#41;&#41;">map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> |  | <code>&#123;&#125;</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [ids](outputs.tf#L1) | Secret IDs. |  |
| [secrets](outputs.tf#L6) | Secret resources. |  |
<!-- END TFDOC -->
