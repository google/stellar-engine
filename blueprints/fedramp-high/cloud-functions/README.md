# Cloud Functions
This blueprint deploys a 2nd Generation Cloud Function. The Cloud Function Module and resource do not have the ability to set the binary authorization to default, so the only way around this is to deploy the cloud function with the gcloud command. 

## Pre-requsites
Enable the following APIs in your GCP project by running the enable-apis.sh script in the blueprint directory. Put your function source code in the ./src-code folder.
<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [bucket_name](variables.tf#L21) | The name of the Cloud Storage bucket where the Cloud Function source code is stored. | <code>string</code> | ✓ |  |
| [function_name](variables.tf#L68) | The name of the Cloud Function. | <code>string</code> | ✓ |  |
| [kms_key_name](variables.tf#L85) | Path to the kms key. | <code>string</code> | ✓ |  |
| [main_project_id](variables.tf#L99) | The GCP project ID. | <code>string</code> | ✓ |  |
| [region](variables.tf#L104) | The GCP region where the Cloud Function will be deployed. | <code>string</code> | ✓ |  |
| [artifact_registry_name](variables.tf#L15) | Name of the Artifact Registry being deployed. | <code>string</code> |  | <code>&#34;cloud-func-reg&#34;</code> |
| [bundle_config](variables.tf#L26) | The configuration for the Cloud Function source bundle. | <code>any</code> |  | <code>null</code> |
| [description](variables.tf#L32) | The description of the Cloud Function. | <code>string</code> |  | <code>&#34;My Cloud Function using a blueprint&#34;</code> |
| [environment_variables](variables.tf#L38) | Environment variables for the Cloud Function. | <code>map&#40;string&#41;</code> |  | <code>&#123;&#125;</code> |
| [function_cpu](variables.tf#L44) | The number of CPUs allocated for the Cloud Function. | <code>number</code> |  | <code>1</code> |
| [function_entry_point](variables.tf#L50) | The entry point for the Cloud Function. | <code>string</code> |  | <code>&#34;helloHttp&#34;</code> |
| [function_instance_count](variables.tf#L56) | The maximum number of instances for the Cloud Function. | <code>number</code> |  | <code>1</code> |
| [function_memory_mb](variables.tf#L62) | The amount of memory (in MB) allocated for the Cloud Function. | <code>number</code> |  | <code>256</code> |
| [function_runtime](variables.tf#L73) | The runtime to use for the Cloud Function (e.g., nodejs18, python39, etc.). | <code>string</code> |  | <code>&#34;nodejs20&#34;</code> |
| [function_timeout_seconds](variables.tf#L79) | The maximum amount of time (in seconds) the Cloud Function is allowed to run. | <code>number</code> |  | <code>60</code> |
| [labels](variables.tf#L90) | Labels to attach to the Cloud Function resources. | <code>map&#40;string&#41;</code> |  | <code title="&#123;&#10;  environment &#61; &#34;development&#34;&#10;  team        &#61; &#34;devops&#34;&#10;&#125;">&#123;&#8230;&#125;</code> |
| [secrets](variables.tf#L109) | Secrets for the Cloud Function (can be environment variables or volume mounts). | <code title="map&#40;object&#40;&#123;&#10;  project_id &#61; string&#10;  secret     &#61; string&#10;  versions   &#61; list&#40;string&#41;&#10;  is_volume  &#61; bool&#10;&#125;&#41;&#41;">map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> |  | <code>&#123;&#125;</code> |
| [service_account](variables.tf#L120) | The service account email to associate with the Cloud Function. | <code>string</code> |  | <code>null</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [artifact_registry_iam_member](outputs.tf#L15) | IAM member assigned to Artifact Registry repository permissions. |  |
| [bucket](outputs.tf#L20) | Bucket holding function source code. |  |
| [cloud_build_iam_member](outputs.tf#L25) | IAM member assigned to roles/cloudbuild.builds.builder. |  |
| [kms_crypto_key_iam_binding_members](outputs.tf#L30) | IAM members assigned to roles/cloudkms.cryptoKeyEncrypterDecrypter for the specified KMS key. |  |
| [logging_iam_member](outputs.tf#L35) | IAM member assigned to roles/logging.logWriter. |  |
| [storage_object_admin_iam_member](outputs.tf#L40) | IAM member assigned to Cloud Storage bucket objectUser permissions. |  |
<!-- END TFDOC -->
