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

# Cloud Functions

<!-- BEGIN TOC -->
- [Cloud Functions Blueprint](#cloud-functions-blueprint)
- [Pre-requisites](#pre-requisites)
- [Deployment Steps](#deployment-steps)
- [Verification of a successful deployment](#verification-of-a-successful-deployment)
- [Variables](#variables)
- [Outputs](#outputs)
<!-- END TOC -->

## Cloud Functions Blueprint
This blueprint deploys a 2nd Generation Cloud Function. The Cloud Function Module and resource do not have the ability to set the binary authorization to default, so the only way around this is to deploy the cloud function with the gcloud command. 

## Pre-requisites
Replace the sample code with your function source code in the ./src-code folder.

## Deployment Steps
You should see this README and some terraform files.
1. Run ```cp terraform.tfvars.sample terraform.tfvars``` to copy the sample variables to your own tfvars file.

2. Update the variables as necessary in your tfvars file.
3. The usual terraform commands will do the work. To provision this example, run the following from within this directory:

```terraform init ```<br />
```terraform plan``` to see the infrastructure plan<br />
```terraform apply``` to apply the infrastructure build<br />

## Verification of a successful deployment
Use GCP console to verify if the resources have been created.
https://console.cloud.google.com/run/overview

<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [bucket_name](variables.tf#L7) | The name of the Cloud Storage bucket where the Cloud Function source code is stored. | <code>string</code> | ✓ |  |
| [function_name](variables.tf#L24) | The name of the Cloud Function. | <code>string</code> | ✓ |  |
| [kms_key_name](variables.tf#L41) | Path to the kms key. | <code>string</code> | ✓ |  |
| [main_project_id](variables.tf#L46) | The GCP project ID. | <code>string</code> | ✓ |  |
| [region](variables.tf#L51) | The GCP region where the Cloud Function will be deployed. | <code>string</code> | ✓ |  |
| [artifact_registry_name](variables.tf#L1) | Name of the Artifact Registry being deployed. | <code>string</code> |  | <code>&#34;cloud-func-reg&#34;</code> |
| [function_entry_point](variables.tf#L12) | The entry point for the Cloud Function. | <code>string</code> |  | <code>&#34;helloHttp&#34;</code> |
| [function_memory_mb](variables.tf#L18) | The amount of memory (in MB) allocated for the Cloud Function. | <code>number</code> |  | <code>256</code> |
| [function_runtime](variables.tf#L29) | The runtime to use for the Cloud Function (e.g., nodejs18, python39, etc.). | <code>string</code> |  | <code>&#34;nodejs20&#34;</code> |
| [function_timeout_seconds](variables.tf#L35) | The maximum amount of time (in seconds) the Cloud Function is allowed to run. | <code>number</code> |  | <code>60</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [artifact_registry_iam_member](outputs.tf#L1) | IAM member assigned to roles/artifactregistry.createOnPushWriter. |  |
| [bucket](outputs.tf#L6) | Bucket holding function source code. |  |
| [cloud_build_iam_member](outputs.tf#L11) | IAM member assigned to roles/cloudbuild.builds.builder. |  |
| [kms_crypto_key_iam_binding_members](outputs.tf#L16) | IAM members assigned to roles/cloudkms.cryptoKeyEncrypterDecrypter for the specified KMS key. |  |
| [logging_iam_member](outputs.tf#L21) | IAM member assigned to roles/logging.logWriter. |  |
| [storage_object_admin_iam_member](outputs.tf#L26) | IAM member assigned to roles/storage.objectAdmin. |  |
<!-- END TFDOC -->
