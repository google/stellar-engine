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

# Document AI

<!-- BEGIN TOC -->
- [Introduction to Document AI](#introduction-to-document-ai)
- [Document AI Blueprint](#document-ai-blueprint)
- [Disclaimer](#disclaimer)
- [Deployment Steps](#deployment-steps)
- [Verification of a successful deployment](#verification-of-a-successful-deployment)
- [Demo](#demo)
- [Variables](#variables)
- [Outputs](#outputs)
<!-- END TOC -->

## Introduction to Document AI
Document AI is a document processing and understanding platform that takes unstructured data from documents and transforms it into structured data (specific fields, suitable for a database), making it easier to understand, analyze, and consume. Document AI is built on top of products within Vertex AI with generative AI to help you create scalable, end-to-end, cloud-based document processing applications without specialized machine learning expertise.

## Document AI Blueprint
This blueprint demonstrates how to create Processors in Document AI on Google Cloud Platform (GCP) by activating the Document AI API to utilize its diverse, Processors—encompassing. This includes both pre-trained Specialized Processors and Custom Processors developed with Document AI Workbench. This foundational setup enables online or batch document processing, transforming unstructured input into structured JSON for storage or database integration. Facilitating seamless application and workflow automation through API access and orchestration services, this blueprint ultimately enhances operational efficiency, mitigates manual errors, and bolsters compliance by converting document data into actionable insights within a secure Google Cloud environment.
Refer to the [Document AI documentation](https://cloud.google.com/document-ai/docs/send-request#documentai_batch_process_document-python) to learn how to use your processor through various client libraries. If you would like to continue using workflows, then you can view the [documentation](https://cloud.google.com/workflows/docs/create-workflow-terraform) here.

## Disclaimer
- The present GCP Terraform Module in this project is set up and intended to be implemented in a FEDRAMP High environment using the Assured Workloads within the Google Cloud Platform (GCP) organization.
- KMS/CMEK is not currently working for Document AI in Terraform as a cyclical dependency is created; the processor instance creates the Document AI Service Account, but the Service Account must have proper KMS permissions prior to the instance creation. If you would still like to use CMEKs with Document AI, you can manually create a processor first so that the Document AI Service Account will exist.

## Deployment Steps
1. Copy the contents of the terraform.tfvars.sample file into your own terraform.tfvars file, then update the variables in this file. For reference update the following variables:

- ```name```  with the name of your processor<br />
- ```project``` with the GCP project id<br />
- ```region``` with the GCP Location <br />
- ```type``` with the type of [Document AI processor](https://cloud.google.com/document-ai/docs/processors-list) you wish to create <br />

2. The usual terraform commands will be used to deploy the processor. To provision this example, run the following from within this directory:

```terraform init ```<br />
```terraform plan``` to see the infrastructure plan<br />
```terraform apply``` to apply the infrastructure build<br />
```terraform destroy``` only if you wish to destroy the built infrastructure<br />

## Verification of a successful deployment
Use GCP console to verify if the resources have been created. Go to [Document AI](https://console.cloud.google.com/ai/document-ai), then click on "My processors" in the side bar. From here, you will be able to view your newly created processor.

## Demo
This demo is meant to work with the default "OCR_PROCESSOR".
1. Manual file upload.
- Start by clicking on your newly created processor to pull up the "Processor Details" page. 
- At the bottom of this page, you should see an "Upload Test Document" button.
- Use this button to upload the sample file "Winnie_the_Pooh_3_Pages.pdf".
- View the output of the processor.
2. Batch processing.
- View your cloud storage buckets.
- Upload the sample document to "(your-project)-docai-input-bucket".
- View your workflows and click on "docai-workflow"
- Click the "execute" button and change your logging level if desired.
- Click "execute" at the bottom of the screen to start the workflow.
- After the workflow executes, view your buckets again.
- Click on "(your-project)-docai-output-bucket" to view the json output.
<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [main_project_id](variables.tf#L13) | The Google Project ID. | <code>string</code> | ✓ |  |
| [name](variables.tf#L18) | Name of the Document AI processor. | <code>string</code> | ✓ |  |
| [region](variables.tf#L23) | The Google Cloud region. | <code>string</code> | ✓ |  |
| [deletion_protection](variables.tf#L1) | Deletion protection. | <code>bool</code> |  | <code>true</code> |
| [file](variables.tf#L7) | File path of the yaml instructions for the workflow. | <code>string</code> |  | <code>&#34;code&#47;example.yaml&#34;</code> |
| [type](variables.tf#L28) | Type of Document AI model. | <code>string</code> |  | <code>&#34;OCR_PROCESSOR&#34;</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [id](outputs.tf#L1) | Document AI processor id. |  |
| [input_bucket](outputs.tf#L6) | Bucket that takes documents as input. |  |
| [output_bucket](outputs.tf#L11) | Bucket that stores document processor output. |  |
| [processor](outputs.tf#L16) | Document AI processor. |  |
| [workflow](outputs.tf#L21) | Workflow that runs the batch processing. |  |
<!-- END TFDOC -->
