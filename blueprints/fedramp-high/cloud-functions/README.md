# Cloud Functions
This blueprint deploys a 2nd Generation Cloud Function natively through Terraform using `modules/cloud-function-v2`, configuring Customer-Managed Encryption Keys (CMEK), default Binary Authorization policy enforcement, internal-and-GCLB ingress, and scoped IAM bindings.

<!-- BEGIN TOC -->
- [Prerequisites](#prerequisites)
- [IAM scope](#iam-scope)
- [Variables](#variables)
- [Outputs](#outputs)
<!-- END TOC -->

## Prerequisites
Terraform enables the required Google Cloud APIs automatically (`artifactregistry.googleapis.com`, `binaryauthorization.googleapis.com`, `cloudbuild.googleapis.com`, `cloudfunctions.googleapis.com`, `compute.googleapis.com`, `logging.googleapis.com`, `pubsub.googleapis.com`, `run.googleapis.com`, and `storage.googleapis.com`), creates the required service identities, and grants `roles/cloudkms.cryptoKeyEncrypterDecrypter` on `kms_key_name` after a 60s propagation wait.

- Ensure the deploying identity has `roles/cloudkms.admin` (or `cloudkms.cryptoKeys.setIamPolicy`) on `kms_key_name`.
- Place your function source code in `./src-code` or set `bundle_config` to a custom local directory, zip archive, or Cloud Storage zip object URI.

## IAM scope
The blueprint grants each role to the runner service account on the narrowest resource that accepts it.

| Role | Resource |
|---|---|
| `roles/run.invoker` | The Cloud Run service behind the function. |
| `roles/artifactregistry.writer` | The Artifact Registry repository. |
| `roles/storage.objectUser` | The Cloud Storage bucket. |
| `roles/cloudbuild.builds.builder` | The project, because Cloud Build does not support IAM policies on builds. |
| `roles/logging.logWriter` | The project, because Cloud Logging authorizes log entry writes against the project. |

The `roles/cloudbuild.builds.builder` role also carries project-wide Cloud Storage object and Artifact Registry write permissions.
<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [bucket_name](variables.tf#L21) | The name of the Cloud Storage bucket where the Cloud Function source code is stored. | <code>string</code> | ✓ |  |
| [function_name](variables.tf#L74) | The name of the Cloud Function. | <code>string</code> | ✓ |  |
| [kms_key_name](variables.tf#L91) | Path to the kms key. | <code>string</code> | ✓ |  |
| [main_project_id](variables.tf#L105) | The GCP project ID. | <code>string</code> | ✓ |  |
| [region](variables.tf#L110) | The GCP region where the Cloud Function will be deployed. | <code>string</code> | ✓ |  |
| [artifact_registry_name](variables.tf#L15) | Name of the Artifact Registry being deployed. | <code>string</code> |  | <code>&#34;cloud-func-reg&#34;</code> |
| [bundle_config](variables.tf#L26) | The configuration for the Cloud Function source bundle. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>null</code> |
| [description](variables.tf#L38) | The description of the Cloud Function. | <code>string</code> |  | <code>&#34;My Cloud Function using a blueprint&#34;</code> |
| [environment_variables](variables.tf#L44) | Environment variables for the Cloud Function. | <code>map&#40;string&#41;</code> |  | <code>&#123;&#125;</code> |
| [function_cpu](variables.tf#L50) | The number of CPUs allocated for the Cloud Function. | <code>number</code> |  | <code>1</code> |
| [function_entry_point](variables.tf#L56) | The entry point for the Cloud Function. | <code>string</code> |  | <code>&#34;helloHttp&#34;</code> |
| [function_instance_count](variables.tf#L62) | The maximum number of instances for the Cloud Function. | <code>number</code> |  | <code>1</code> |
| [function_memory_mb](variables.tf#L68) | The amount of memory (in MB) allocated for the Cloud Function. | <code>number</code> |  | <code>256</code> |
| [function_runtime](variables.tf#L79) | The runtime to use for the Cloud Function (e.g., nodejs18, python39, etc.). | <code>string</code> |  | <code>&#34;nodejs20&#34;</code> |
| [function_timeout_seconds](variables.tf#L85) | The maximum amount of time (in seconds) the Cloud Function is allowed to run. | <code>number</code> |  | <code>60</code> |
| [labels](variables.tf#L96) | Labels to attach to the Cloud Function resources. | <code>map&#40;string&#41;</code> |  | <code>&#123;&#8230;&#125;</code> |
| [secrets](variables.tf#L115) | Secrets for the Cloud Function (can be environment variables or volume mounts). | <code>map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> |  | <code>&#123;&#125;</code> |
| [service_account](variables.tf#L126) | The service account email to associate with the Cloud Function. | <code>string</code> |  | <code>null</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [artifact_registry_iam_member](outputs.tf#L15) | IAM member assigned to roles/artifactregistry.writer on the Artifact Registry repository. |  |
| [bucket](outputs.tf#L21) | Bucket holding function source code. |  |
| [cloud_build_iam_member](outputs.tf#L26) | IAM member assigned to roles/cloudbuild.builds.builder. |  |
| [kms_crypto_key_iam_binding_members](outputs.tf#L31) | IAM members assigned to roles/cloudkms.cryptoKeyEncrypterDecrypter for the specified KMS key. |  |
| [logging_iam_member](outputs.tf#L36) | IAM member assigned to roles/logging.logWriter. |  |
| [storage_object_admin_iam_member](outputs.tf#L41) | IAM member assigned to roles/storage.objectUser on the bucket. |  |
<!-- END TFDOC -->
