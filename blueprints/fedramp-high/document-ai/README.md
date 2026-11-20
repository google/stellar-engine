# Document AI blueprint

<!-- BEGIN TOC -->
- [1 Document AI overview](#1-document-ai-overview)
- [2 Blueprint scope](#2-blueprint-scope)
- [3 Compliance notes](#3-compliance-notes)
- [4 Deployment steps](#4-deployment-steps)
- [5 Deployment verification](#5-deployment-verification)
- [6 Processor demo](#6-processor-demo)
- [Variables](#variables)
- [Outputs](#outputs)
<!-- END TOC -->

## 1 Document AI overview

Document AI extracts structured JSON fields from unstructured documents using pre-trained and custom Vertex AI models so applications and databases can ingest document data without custom machine learning pipelines.

## 2 Blueprint scope

This blueprint enables the Document AI API, provisions a Document AI processor alongside input and output Cloud Storage buckets, and deploys a Workflows pipeline for batch document processing.

See the [Document AI batch processing guide](https://cloud.google.com/document-ai/docs/send-request#documentai_batch_process_document-python) for client library usage and the [Workflows Terraform guide](https://cloud.google.com/workflows/docs/create-workflow-terraform) for workflow orchestration details.

## 3 Compliance notes

- Deploy this blueprint inside a FedRAMP High Assured Workloads folder within your Google Cloud organization.
- Provisioning a Document AI processor with CMEK in a single Terraform pass triggers a circular dependency because the Document AI service agent is created during first processor creation, after Cloud KMS IAM grants would need to exist. To use CMEK with Document AI, pre-create a processor or service identity first so the Document AI service agent can receive Cloud KMS permissions before processor creation.

## 4 Deployment steps

1. Copy `terraform.tfvars.sample` to `terraform.tfvars` and configure your input values:
   - Set `name` to the Document AI processor display name.
   - Set `main_project_id` to the target Google Cloud project ID.
   - Set `kms_key_name` to the Cloud KMS CryptoKey resource ID for bucket and workflow encryption.
   - Set `region` to the target Google Cloud location.
   - Set `type` to a supported [Document AI processor type](https://cloud.google.com/document-ai/docs/processors-list).
2. Initialize and apply the Terraform configuration from this directory:

```bash
terraform init
terraform plan
terraform apply
```

Run `terraform destroy` if you need to tear down the deployed resources.

## 5 Deployment verification

Open [Document AI](https://console.cloud.google.com/ai/document-ai) in the Google Cloud console and select `My processors` in the navigation menu to confirm your processor appears.

## 6 Processor demo

Test the default `OCR_PROCESSOR` deployment using either single-document upload or batch workflow execution:

1. For manual single-file testing, open the processor details page, select Upload Test Document, upload `samples/Winnie_the_Pooh_3_Pages.pdf`, and inspect the parsed fields.
2. For batch processing, upload the sample PDF to `<main_project_id>-docai-input-bucket` in Cloud Storage, open `docai-workflow` in Workflows, select Execute, and inspect the generated JSON output in `<main_project_id>-docai-output-bucket`.

<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [kms_key_name](variables.tf#L27) | KMS customer managed encryption key (CMEK) name. | <code>string</code> | ✓ |  |
| [main_project_id](variables.tf#L32) | The Google Project ID. | <code>string</code> | ✓ |  |
| [name](variables.tf#L37) | Name of the Document AI processor. | <code>string</code> | ✓ |  |
| [region](variables.tf#L42) | The Google Cloud region. | <code>string</code> | ✓ |  |
| [deletion_protection](variables.tf#L15) | Deletion proteciton. | <code>bool</code> |  | <code>true</code> |
| [file](variables.tf#L21) | File path of the yaml instructions for the workflow. | <code>string</code> |  | <code>&#34;code&#47;example.yaml&#34;</code> |
| [type](variables.tf#L47) | Type of Document AI model. | <code>string</code> |  | <code>&#34;OCR_PROCESSOR&#34;</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [id](outputs.tf#L15) | Document AI processor id. |  |
| [input_bucket](outputs.tf#L20) | Bucket that takes documents as input. |  |
| [output_bucket](outputs.tf#L25) | Bucket that stores document processor output. |  |
| [processor](outputs.tf#L30) | Document AI processor. |  |
| [workflow](outputs.tf#L35) | Workflow that runs the batch processing. |  |
<!-- END TFDOC -->
