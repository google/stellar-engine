# Secret Manager blueprint

This blueprint provisions CMEK-encrypted Secret Manager secrets and IAM bindings in a multi-project Google Cloud environment while uploading secret payload versions outside Terraform state through `add_secret_versions.sh`.
<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [core_project_id](variables.tf#L15) | The Google Cloud Project ID where shared core services like KMS keys are located. Used for referencing existing KMS keys. | <code>string</code> | ✓ |  |
| [main_project_id](variables.tf#L32) | The Google Cloud Project ID where the secrets will be created. | <code>string</code> | ✓ |  |
| [gcp_region](variables.tf#L20) | The Google Cloud region to be used as the default for regional resources and the provider. Note: Secret Manager secrets are regional resources. | <code>string</code> |  | <code>&#34;us-east4&#34;</code> |
| [iam](variables.tf#L26) | IAM bindings in {SECRET => {ROLE => [MEMBERS]}} format. | <code>map&#40;map&#40;list&#40;string&#41;&#41;&#41;</code> |  | <code>&#123;&#125;</code> |
| [secrets](variables.tf#L37) | Map of secret configurations. Each key is the `secret_id` (name) of the secret. Each value is an object with optional `expire_time`, `version_destroy_ttl`, `locations` (list of regions for user-managed replication), and `keys` (a map where keys are replication locations (or 'global') and values are full KMS CryptoKey self-links for encryption). | <code>map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> |  | <code>&#123;&#125;</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [ids](outputs.tf#L15) | Secret IDs. |  |
| [secrets](outputs.tf#L20) | Secret resources. |  |
<!-- END TFDOC -->

## 1 Secret Manager overview

Secret Manager stores API keys, passwords, certificates, and other sensitive configuration values with IAM access control, audit logging, versioning, and automated rotation. Provisioning secret metadata and CMEK bindings in Terraform while uploading secret payloads out of band keeps plaintext secret values out of Terraform state files.

## 2 Compliance scope

- Deploy this blueprint inside a FedRAMP High or IL5 Assured Workloads folder within your Google Cloud organization.
- Assured Workloads enforces regional data residency and encryption guardrails required for federal and defense workloads.

## 3 Prerequisites

Verify that the following projects, keys, permissions, and scripts are available before running Terraform:

- Provision `main_project_id` to host the Secret Manager secrets and `core_project_id` to host your existing Cloud KMS key rings and encryption keys.
- Provision regional Cloud KMS keys in `core_project_id` ahead of time; this blueprint references existing KMS keys rather than creating new ones.
- Grant the deploying identity `roles/secretmanager.admin`, `roles/serviceusage.serviceUsageAdmin`, and `roles/resourcemanager.projectIamAdmin` on `main_project_id`, `roles/cloudkms.viewer` on `core_project_id`, and `roles/cloudkms.cryptoKeyEncrypterDecrypter` for the Secret Manager service agent on each referenced KMS key.
- Keep `add_secret_versions.sh` and the `gcloud` CLI available in your operator environment to upload secret payload versions outside Terraform state.

## 4 Deployment steps

1. Copy the sample variables file and update `terraform.tfvars` with your `main_project_id`, `core_project_id`, `gcp_region`, and Cloud KMS CryptoKey self-links:

```bash
cp terraform.tfvars.sample terraform.tfvars
```

2. Initialize the Terraform working directory:

```bash
terraform init
```

3. Review the execution plan for secret metadata and IAM bindings:

```bash
terraform plan
```

4. Apply the configuration to create the Secret Manager secret containers and IAM bindings without uploading secret payloads:

```bash
terraform apply
```

5. Upload secret versions outside Terraform state using `add_secret_versions.sh`:
   - Place secret payload files in `secrets/<secret-id>.txt`, matching each key in `secrets`.
   - Mark the helper script executable:

```bash
chmod +x add_secret_versions.sh
```

   - Authenticate `gcloud` as a principal with `roles/secretmanager.secretVersionManager` or `roles/secretmanager.admin` on `main_project_id`.
   - Upload all secret files from `secrets/` automatically, or target specific secret IDs and a custom directory:

```bash
./add_secret_versions.sh --project-id <YOUR_MAIN_PROJECT_ID>
./add_secret_versions.sh --project-id <YOUR_MAIN_PROJECT_ID> --secret-ids secret-id-one,secret-id-two --data-dir my-custom-secret-data-folder
```

   - Delete the local plaintext secret files once version upload succeeds.

6. Run `terraform destroy` if you need to delete the deployed Secret Manager secrets and all stored versions:

```bash
terraform destroy
```

## 5 Deployment verification

Verify secret creation, CMEK encryption, and uploaded versions in the Google Cloud console or with the `gcloud` CLI:

- In the Google Cloud console, open Secret Manager in `main_project_id`, select each secret, and confirm that an active version exists and Customer-managed encryption key points to your Cloud KMS key.
- List and inspect secrets and versions from the command line:

```bash
gcloud secrets list --project=<MAIN_PROJECT_ID>
gcloud secrets describe <SECRET_ID> --project=<MAIN_PROJECT_ID>
gcloud secrets versions list <SECRET_ID> --project=<MAIN_PROJECT_ID>
gcloud secrets versions access latest --secret=<SECRET_ID> --project=<MAIN_PROJECT_ID>
```

## 6 Operational notes

- Uploading secret versions via `add_secret_versions.sh` prevents Terraform from writing plaintext `secret_data` values into the Terraform state file.
- Secret Manager secrets in this blueprint use regional replication, and each secret `location` must match the region of its Cloud KMS key.
- To upload secrets from an isolated workstation inside the VPC rather than locally, deploy a temporary VM with `blueprints/il5/compute-engine`, run `add_secret_versions.sh`, shred local secret files, and destroy the VM after upload.

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
