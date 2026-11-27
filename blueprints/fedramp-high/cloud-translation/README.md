# Cloud Translation blueprint

<!-- BEGIN TOC -->
- [1 Cloud Translation overview](#1-cloud-translation-overview)
- [2 Blueprint scope](#2-blueprint-scope)
- [3 Compliance scope](#3-compliance-scope)
- [4 Deployment steps](#4-deployment-steps)
- [5 Deployment verification](#5-deployment-verification)
- [6 Batch translation demo](#6-batch-translation-demo)
- [Variables](#variables)
- [Outputs](#outputs)
<!-- END TOC -->

## 1 Cloud Translation overview

Google Cloud Translation provides real-time text translation, document and batch translation, language detection, custom AutoML Translation models, and terminology glossaries across supported languages.

## 2 Blueprint scope

This blueprint enables the Cloud Translation, Cloud Storage, and Workflows APIs, provisions service identities and Cloud KMS IAM grants when `kms_key_self_link` is set, creates CMEK-encrypted input and output Cloud Storage buckets in `region`, and deploys a `translate-workflow` Workflows pipeline that calls Cloud Translation in `locations/<region>` for asynchronous batch translation.

## 3 Compliance scope

- Deploy this blueprint inside a FedRAMP High Assured Workloads folder within your Google Cloud organization.
- Set `kms_key_self_link` to a Cloud KMS CryptoKey in `region` so both Cloud Storage buckets and the Workflows pipeline use Customer-Managed Encryption Keys. Terraform grants `roles/cloudkms.cryptoKeyEncrypterDecrypter` to the Cloud Storage, Cloud Translation, and Workflows service agents after a 60-second propagation wait.

## 4 Deployment steps

1. Copy `terraform.tfvars.sample` to `terraform.tfvars` and configure your input values:
   - Set `main_project_id` to the target Google Cloud project ID.
   - Set `region` to the target Google Cloud region.
   - Set `kms_key_self_link` to the regional Cloud KMS CryptoKey resource ID in `region`.
   - Set `deletion_protection` to control workflow deletion protection.
   - Set `src_lang` and `target_lang` to [supported language codes](https://cloud.google.com/translate/docs/languages).
2. Initialize and apply the Terraform configuration from this directory:

```bash
terraform init
terraform plan
terraform apply
```

Run `terraform destroy` if you need to tear down the deployed resources.

## 5 Deployment verification

Verify in the Google Cloud console that the [Cloud Translation API](https://cloud.google.com/translate) is enabled, the `translate-workflow` workflow exists in Workflows, and the `<main_project_id>-translate-input` and `<main_project_id>-translate-output` buckets exist in Cloud Storage.

## 6 Batch translation demo

To test interactive translation directly in the console, open [Vertex AI Studio Translation](https://console.cloud.google.com/vertex-ai/studio/translation). To run the batch translation workflow:

1. Download a sample text file from [Project Gutenberg](https://www.gutenberg.org/) or fetch an example file directly:

```bash
curl https://www.gutenberg.org/cache/epub/2554/pg2554.txt > ./samples/crime-and-punishment.txt
```

2. Upload the sample files from `./samples/` to `<main_project_id>-translate-input`.
3. Open `translate-workflow` in Workflows and select Execute twice to start the run.
4. Inspect the translated documents inside `<main_project_id>-translate-output` once execution completes.
<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [main_project_id](variables.tf#L43) | The Google Project ID. | <code>string</code> | ✓ |  |
| [region](variables.tf#L54) | The Google Cloud region. | <code>string</code> | ✓ |  |
| [deletion_protection](variables.tf#L15) | Deletion protection. | <code>bool</code> |  | <code>true</code> |
| [file](variables.tf#L21) | File path of the yaml instructions for the workflow. | <code>string</code> |  | <code>&#34;code&#47;example.yaml&#34;</code> |
| [kms_key_self_link](variables.tf#L27) | The full self-link of the existing Cloud KMS CryptoKey in var.region to use for Cloud Storage bucket and Workflow encryption (CMEK). | <code>string</code> |  | <code>null</code> |
| [output_folder](variables.tf#L48) | Name of the folder that will be created in the output bucket to store the translated text. | <code>string</code> |  | <code>&#34;output&#34;</code> |
| [src_lang](variables.tf#L59) | The source language of the text. | <code>string</code> |  | <code>&#34;es&#34;</code> |
| [target_lang](variables.tf#L65) | The target language to translate into. | <code>string</code> |  | <code>&#34;en&#34;</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [input_bucket](outputs.tf#L15) | Bucket that takes documents as input. |  |
| [output_bucket](outputs.tf#L20) | Bucket that stores translated output. |  |
| [workflow](outputs.tf#L25) | Workflow that runs the batch processing. |  |
<!-- END TFDOC -->
