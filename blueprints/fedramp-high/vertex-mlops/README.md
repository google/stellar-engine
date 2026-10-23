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
1. GCS buckets to host Vertex AI and Cloud Build Artifacts. By default the buckets will be regional and should match the Vertex AI region for the different resources (i.e. Vertex Managed Dataset) and processes (i.e. Vertex trainining).
1. BigQuery Dataset where the training data will be stored. This is optional, since the training data could be already hosted in an existing BigQuery dataset.

## Instructions
### Deploy the experimentation environment
- Create a `terraform.tfvars` file and specify the variables to match your desired configuration. You can use the provided `terraform.tfvars.sample` as reference.
- Set the optional `owner` of a notebook to the user email that should be listed as the Workbench instance owner.
- Before choosing a region to create your resources in, it is recommended to view your system [quotas](https://console.cloud.google.com/iam-admin/quotas) in order to check which regions have access to GPU and TPU accelerators. If you choose a region where the quota is 0, you will have to request a quota increase (common accelerators are NVIDIA_A100 and NVIDIA_H100). It is recommended to create project resources in the 'us-central1' region.
- When configuring your network settings, remeber that you must use a shared VPC. It is recomended that you have a separate 'networking project' that manages network traffic, and share this VPC to any projects that need access to it. This shared VPC must have internet access or JupyterLabs will not work. In addition, the account that runs the terraform code must have the Compute Shared VPC Admin role at an organization level. 
- Run `terraform init` and `terraform apply`
- Every entry in the `notebooks` variable creates a Vertex AI Workbench instance. The `type` attribute accepts only `USER_MANAGED`, because Google-managed notebooks reached end of life and Google provider 8 removed the `google_notebooks_runtime` resource.

## Demo
To try out the new notebook, you can use the provided code sample (the .ipynb file), adapted from [here](https://github.com/GoogleCloudPlatform/vertex-ai-samples/blob/main/notebooks/community/model_garden/model_garden_pytorch_flux.ipynb). Alternatively, you can view the list of [Vertex AI code samples](https://cloud.google.com/vertex-ai/docs/samples) to find one that you like. Simply open the Google Cloud Console and navigate to Vertex AI workbenches. Under the list of instances, you should see your newly created workbench instance. Click on the button that says "Open JupyterLab" to use your workbench. Within JupyterLab, you should see the option to upload files. Upload a demo notebook, then update the variables as necessary (in the provided demo, you will have to update BUCKET_URI, REGION, and PROJECT_ID).
<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [network_config](variables.tf#L43) | Shared VPC network configurations to use. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> | ✓ |  |
| [notebooks](variables.tf#L57) | Vertex AI Workbench instances to be deployed, keyed by name. | <code>map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> | ✓ |  |
| [project_config](variables.tf#L83) | Provide 'billing_account_id' value if project creation is needed, uses existing 'project_id' if null. Parent is in 'folders/nnn' or 'organizations/nnn' format. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> | ✓ |  |
| [bucket_name](variables.tf#L18) | GCS bucket name to store the Vertex AI artifacts. | <code>string</code> |  | <code>null</code> |
| [dataset_name](variables.tf#L24) | BigQuery Dataset to store the training data. | <code>string</code> |  | <code>null</code> |
| [deletion_protection](variables.tf#L30) | Prevent Terraform from destroying data storage resources (storage buckets, GKE clusters, CloudSQL instances) in this blueprint. When this field is set in Terraform state, a terraform destroy or terraform apply that would delete data storage resources will fail. | <code>bool</code> |  | <code>true</code> |
| [labels](variables.tf#L37) | Labels to be assigned at project level. | <code>map&#40;string&#41;</code> |  | <code>&#123;&#125;</code> |
| [prefix](variables.tf#L77) | Prefix used for various resource creation. | <code>string</code> |  | <code>null</code> |
| [region](variables.tf#L97) | Region used for regional resources. | <code>string</code> |  | <code>&#34;us-central1&#34;</code> |
| [service_encryption_keys](variables.tf#L103) | Cloud KMS to use to encrypt different services. Key location should match service region. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>&#123;&#125;</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [notebook](outputs.tf#L17) | Vertex AI notebook ids. |  |
| [project_id](outputs.tf#L24) | Project ID. |  |
<!-- END TFDOC -->
