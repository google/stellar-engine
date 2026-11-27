# MLOps with Vertex AI
This blueprint demonstrates how to create a Vertex AI Workbench on Google Cloud Platform (GCP) with Customer-Managed Encryption Keys (CMEK) using Cloud KMS. 

<!-- BEGIN TOC -->
- [Introduction to Vertex AI](#introduction-to-vertex-ai)
- [Disclaimer](#disclaimer)
- [Architecture](#architecture)
- [IAM](#iam)
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

## IAM
The blueprint creates the `sa-mlops` and `notebook-sa` service accounts, and binds each role on the narrowest resource that the service supports.

| Role | Principal | Bound on |
|---|---|---|
| `roles/compute.networkUser` | Notebooks service agent | The Shared VPC subnet named by `network_config.subnetwork_name` in `region`. |
| `roles/storage.objectViewer`, `roles/storage.objectCreator` | `sa-mlops`, `notebook-sa` | The `bucket_name` bucket and the Cloud Build bucket. |
| `storage_iam` custom role | `notebook-sa` | The `bucket_name` bucket and the Cloud Build bucket. |
| `roles/bigquery.dataEditor` | `sa-mlops`, `notebook-sa` | The `dataset_name` dataset. |
| `roles/iam.serviceAccountUser` | `sa-mlops`, Cloud Build service agent | The `sa-mlops` service account. |
| `roles/iam.serviceAccountUser` | `notebook-sa` | The `notebook-sa` service account. |

The other roles stay on the project, because the service has no narrower resource or the workload creates the resource at run time. The comments in the `main.tf` file state the reason for each role.

The service accounts have no access to a bucket, dataset, subnet or service account that the blueprint does not create or receive as a variable. Grant that access outside the blueprint when a workload needs it, for example `roles/bigquery.dataEditor` on an existing dataset when `dataset_name` is not set.

## Instructions
### Deploy the experimentation environment
- Create a `terraform.tfvars` file and specify the variables to match your desired configuration. You can use the provided `terraform.tfvars.sample` as reference.
- Set `project_config.billing_account_id` to `null` (default in the sample) to reuse an existing Stage 1 tenant project without creating a new project, or set `billing_account_id` and `parent` to create a new project.
- Set `network_config.attach` to `true` only when Terraform should manage the Shared VPC service project attachment (default is `true` for newly created projects and `false` when reusing an existing project so `terraform destroy` does not detach it and `roles/compute.xpnAdmin` is not required).
- Set the optional `owner` of a notebook to the user email that should be listed as the Workbench instance owner.
- Before choosing a region to create your resources in, view your system [quotas](https://console.cloud.google.com/iam-admin/quotas) to check which regions have access to GPU and TPU accelerators. If you choose a region where the quota is 0, request a quota increase (common accelerators are NVIDIA_A100 and NVIDIA_H100). Ensure `region` matches the Cloud KMS key region (for example `us-east4`).
- When configuring your network settings, remember that you must use a Shared VPC. Have a separate networking host project that shares the VPC to workload projects, with internet access or JupyterLab will not work. When `network_config.attach` is `true`, the deploying principal needs `roles/compute.xpnAdmin` at the organization level; when `false`, the principal only needs subnet IAM permission (`roles/compute.networkAdmin` or `roles/compute.securityAdmin` on the host subnet) to bind `roles/compute.networkUser` for the Notebooks service agent.
- Run `terraform init` and `terraform apply`.
- Every entry in the `notebooks` variable creates a Vertex AI Workbench instance. The `type` attribute accepts only `USER_MANAGED`, because Google-managed notebooks reached end of life and Google provider 8 removed the `google_notebooks_runtime` resource.

## Demo
To try out the new notebook, you can use the provided code sample (the .ipynb file), adapted from [here](https://github.com/GoogleCloudPlatform/vertex-ai-samples/blob/main/notebooks/community/model_garden/model_garden_pytorch_flux.ipynb). Alternatively, you can view the list of [Vertex AI code samples](https://cloud.google.com/vertex-ai/docs/samples) to find one that you like. Simply open the Google Cloud Console and navigate to Vertex AI workbenches. Under the list of instances, you should see your newly created workbench instance. Click on the button that says "Open JupyterLab" to use your workbench. Within JupyterLab, you should see the option to upload files. Upload a demo notebook, then update the variables as necessary (in the provided demo, you will have to update BUCKET_URI, REGION, and PROJECT_ID). The demo deploys the model as the `notebook-sa` service account, which is the only service account that a notebook can act as.
<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [network_config](variables.tf#L43) | Shared VPC network configurations to use. Set attach to false when reusing an existing project already attached to the Shared VPC host project; defaults to true when creating a new project and false when reusing one. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> | ✓ |  |
| [notebooks](variables.tf#L58) | Vertex AI Workbench instances to be deployed, keyed by name. | <code>map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> | ✓ |  |
| [project_config](variables.tf#L84) | Provide 'billing_account_id' value if project creation is needed, uses existing 'project_id' if null. Parent is in 'folders/nnn' or 'organizations/nnn' format. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> | ✓ |  |
| [bucket_name](variables.tf#L18) | GCS bucket name to store the Vertex AI artifacts. | <code>string</code> |  | <code>null</code> |
| [dataset_name](variables.tf#L24) | BigQuery Dataset to store the training data. | <code>string</code> |  | <code>null</code> |
| [deletion_protection](variables.tf#L30) | Prevent Terraform from destroying data storage resources (storage buckets, GKE clusters, CloudSQL instances) in this blueprint. When this field is set in Terraform state, a terraform destroy or terraform apply that would delete data storage resources will fail. | <code>bool</code> |  | <code>true</code> |
| [labels](variables.tf#L37) | Labels to be assigned at project level. | <code>map&#40;string&#41;</code> |  | <code>&#123;&#125;</code> |
| [prefix](variables.tf#L78) | Prefix used for various resource creation. | <code>string</code> |  | <code>null</code> |
| [region](variables.tf#L98) | Region used for regional resources. | <code>string</code> |  | <code>&#34;us-central1&#34;</code> |
| [service_encryption_keys](variables.tf#L104) | Cloud KMS to use to encrypt different services. Key location should match service region. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>&#123;&#125;</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [notebook](outputs.tf#L17) | Vertex AI notebook ids. |  |
| [project_id](outputs.tf#L24) | Project ID. |  |
<!-- END TFDOC -->
