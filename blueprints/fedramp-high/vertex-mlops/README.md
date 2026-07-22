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

# MLOps with Vertex AI
This blueprint demonstrates how to create a Vertex AI Workbench on Google Cloud Platform (GCP) with Customer-Managed Encryption Keys (CMEK) using Cloud KMS. 

<!-- BEGIN TOC -->
- [Introduction to Vertex AI](#introduction-to-vertex-ai)
- [Disclaimer](#disclaimer)
- [Architecture](#architecture)
- [Instructions](#instructions)
  - [Deploy the experimentation environment](#deploy-the-experimentation-environment)
- [Demo](#demo)
- [Variables](#variables)
- [Outputs](#outputs)
<!-- END TOC -->

## Introduction to Vertex AI
Vertex AI is a fully-managed, unified AI development platform for building and using generative AI. Access and utilize Vertex AI Studio, Agent Builder, and 150+ foundation models. Evaluate, tune, and deploy generative AI models or train your own custom models. 
This example implements the infrastructure required to deploy an end-to-end [MLOps process](https://services.google.com/fh/files/misc/practitioners_guide_to_mlops_whitepaper.pdf) using [Vertex AI](https://cloud.google.com/vertex-ai) platform.

## Disclaimer
- The present GCP Terraform Module in this project is set up and intended to be implemented in either a FedRAMP-High or IL5 (Impact Level 5) environment using the Assured Workloads within the Google Cloud Platform (GCP) organization.

## Architecture
The blueprint will deploy all the required resources to have a fully functional MLOPs environment containing:

1. Vertex Workbench (for the experimentation environment).
1. An external Shared VPC must be configured using the `network_config`variable.
1. GCS buckets to host Vertex AI and Cloud Build Artifacts. By default the buckets will be regional and should match the Vertex AI region for the different resources (i.e. Vertex Managed Dataset) and processes (i.e. Vertex training).
1. BigQuery Dataset where the training data will be stored. This is optional, since the training data could be already hosted in an existing BigQuery dataset.

## Instructions
### Deploy the experimentation environment
- Create a `terraform.tfvars` file and specify the variables to match your desired configuration. You can use the provided `terraform.tfvars.sample` as reference.
- Before choosing a region to create your resources in, it is recommended to view your system [quotas](https://console.cloud.google.com/iam-admin/quotas) in order to check which regions have access to GPU and TPU accelerators. If you choose a region where the quota is 0, you will have to request a quota increase (common accelerators are NVIDIA_A100 and NVIDIA_H100). It is recommended to create project resources in the 'us-central1' region.
- When configuring your network settings, remember that you must use a shared VPC. It is recommended that you have a separate 'networking project' that manages network traffic, and share this VPC to any projects that need access to it. This shared VPC must have internet access or JupyterLabs will not work. In addition, the account that runs the terraform code must have the Compute Shared VPC Admin role at an organization level. 
- Run `terraform init` and `terraform apply`

## Demo
To try out the new notebook, you can use the provided code sample (the .ipynb file), adapted from [here](https://github.com/GoogleCloudPlatform/vertex-ai-samples/blob/main/notebooks/community/model_garden/model_garden_pytorch_flux.ipynb). Alternatively, you can view the list of [Vertex AI code samples](https://cloud.google.com/vertex-ai/docs/samples) to find one that you like. Simply open the Google Cloud Console and navigate to Vertex AI workbenches. Under the list of instances, you should see your newly created workbench instance. Click on the button that says "Open JupyterLab" to use your workbench. Within JupyterLab, you should see the option to upload files. Upload a demo notebook, then update the variables as necessary (in the provided demo, you will have to update BUCKET_URI, REGION, and PROJECT_ID).
<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [main_project_id](variables.tf#L42) | Project ID for the main project. | <code>string</code> | ✓ |  |
| [network_config](variables.tf#L47) | Shared VPC network configurations to use. | <code title="object&#40;&#123;&#10;  network_project_id &#61; string&#10;  network_name       &#61; string&#10;  subnetwork_name    &#61; string&#10;&#125;&#41;">object&#40;&#123;&#8230;&#125;&#41;</code> | ✓ |  |
| [notebooks](variables.tf#L61) | Vertex AI workbenches to be deployed. Service Account runtime/instances deployed. | <code title="map&#40;object&#40;&#123;&#10;  type             &#61; string&#10;  machine_type     &#61; optional&#40;string, &#34;n1-standard-4&#34;&#41;&#10;  internal_ip_only &#61; optional&#40;bool, true&#41;&#10;  idle_shutdown    &#61; optional&#40;bool, false&#41;&#10;  owner            &#61; optional&#40;string&#41;&#10;&#125;&#41;&#41;">map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> | ✓ |  |
| [bucket_name](variables.tf#L17) | GCS bucket name to store the Vertex AI artifacts. | <code>string</code> |  | <code>null</code> |
| [dataset_name](variables.tf#L23) | BigQuery Dataset to store the training data. | <code>string</code> |  | <code>null</code> |
| [deletion_protection](variables.tf#L29) | Prevent Terraform from destroying data storage resources (storage buckets, GKE clusters, CloudSQL instances) in this blueprint. When this field is set in Terraform state, a terraform destroy or terraform apply that would delete data storage resources will fail. | <code>bool</code> |  | <code>false</code> |
| [labels](variables.tf#L36) | Labels to be assigned at project level. | <code>map&#40;string&#41;</code> |  | <code>&#123;&#125;</code> |
| [prefix](variables.tf#L82) | Prefix used for various resource creation. | <code>string</code> |  | <code>null</code> |
| [region](variables.tf#L88) | Region used for regional resources. | <code>string</code> |  | <code>&#34;us-central1&#34;</code> |
| [service_encryption_keys](variables.tf#L94) | Cloud KMS to use to encrypt different services. Key location should match service region. | <code title="object&#40;&#123;&#10;  aiplatform &#61; optional&#40;string&#41;&#10;  bq         &#61; optional&#40;string&#41;&#10;  notebooks  &#61; optional&#40;string&#41;&#10;  storage    &#61; optional&#40;string&#41;&#10;&#125;&#41;">object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>&#123;&#125;</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [notebook](outputs.tf#L17) | Vertex AI notebook ids. |  |
| [project_id](outputs.tf#L22) | Project ID. |  |
<!-- END TFDOC -->
