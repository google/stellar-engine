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

# Cloud Run

<!-- BEGIN TOC -->
- [Introduction to Google Cloud Run](#introduction-to-google-cloud-run)
- [Cloud Run Blueprint](#cloud-run-blueprint)
- [Disclaimer](#disclaimer)
- [Prerequisites](#prerequisites)
- [Deployment Steps](#deployment-steps)
- [Verification of a successful deployment](#verification-of-a-successful-deployment)
- [Variables](#variables)
- [Outputs](#outputs)
<!-- END TOC -->

## Introduction to Google Cloud Run
Google Cloud Platform's Cloud Run is a fully managed, serverless computing platform that enables developers to deploy and run containerized applications with ease. It abstracts away infrastructure management, automatically scaling applications up and down based on traffic, while only charging for the actual compute time used. Cloud Run supports stateless HTTP-based workloads, allowing applications to be deployed using any language or framework as long as they are packaged in a container. It offers both public and private access options, integrates with Google Cloud’s identity and access management (IAM) for secure access control, and can connect to various Google Cloud services, such as Cloud SQL, Pub/Sub, and Firestore. With built-in features for versioning, traffic splitting, and load balancing, Cloud Run is ideal for modern microservices architectures and applications that require scalability and low-latency response times.

## Cloud Run Blueprint
This blueprint configures and deploys a Cloud Run Service or Job based on your specified container image and settings. Beyond standard Cloud Run deployment, it integrates crucial security controls to meet enterprise or compliance requirements, including:

- Using a Customer-Managed Encryption Key (CMEK) from Cloud Key Management Service (KMS) for encryption.
- Enforcing Binary Authorization to ensure only trusted and verified container images can be deployed.
- Utilizing a dedicated Service Account with least privilege for the Cloud Run instance.

## Disclaimer
- The present GCP Terraform Module in this project is set up and intended to be implemented in a FEDRAMP High environment using the Assured Workloads within the Google Cloud Platform (GCP) organization.

## Prerequisites
Binary Authorization is enabled by default in FedRAMP High. To use a custom organization policy instead of this default, you must create the policy and configure the "policy" setting accordingly. The "policy" name needs to be updated in the binary_authorization_mode field.

## Deployment Steps

You should see this README and some terraform files.
1. Update the Variables in the variables.tf and also the properties within the keys variables. For reference update the following variables and associated properties

- ```project_id```  with your GCP Project ID<br />
- ```region``` with the GCP region <br />
- ```name``` with the desired cloud run name <br />
- ```kms_key``` with the full path to the CMEK key that will be used for encryption <br />
- ```container_image``` with the container to be hosted on the cloud run service <br />


2. There is a sample ```terraform.tfvars.sample``` available as well.
3. Although each use case is somehow built around the previous one they are self-contained so you can deploy any of them at your will. The usual terraform commands will do the work. To provision this example, run the following from within this directory:

```terraform init ```<br />
```terraform plan``` to see the infrastructure plan<br />
```terraform apply``` to apply the infrastructure build<br />
```terraform destroy``` to destroy the built infrastructure<br />

## Verification of a successful deployment
Use GCP console to verify if the resources have been created.
https://console.cloud.google.com/run

<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [container_image](variables.tf#L21) | Container image to be hosted on cloud run. | <code>string</code> | ✓ |  |
| [core_project_id](variables.tf#L26) | Core project ID. | <code>string</code> | ✓ |  |
| [kms_key_name](variables.tf#L61) | Path to the kms key to use. | <code>string</code> | ✓ |  |
| [kms_keyring_name](variables.tf#L66) | KMS Keyring. | <code>string</code> | ✓ |  |
| [main_project_id](variables.tf#L71) | Main Project ID. | <code>string</code> | ✓ |  |
| [name](variables.tf#L82) | Name of the cloud run instance to be created. | <code>string</code> | ✓ |  |
| [region](variables.tf#L93) | Google Cloud Region. | <code>string</code> | ✓ |  |
| [binary_authorization_mode](variables.tf#L1) | Binary Authorization mode for the Cloud Run service. | <code>string</code> |  | <code>&#34;default&#34;</code> |
| [binary_authorization_policy](variables.tf#L11) | The full resource name of the Binary Authorization policy (e.g., 'projects/YOUR_PROJECT_ID/policies/YOUR_POLICY_ID'). | <code>string</code> |  | <code>null</code> |
| [cpu](variables.tf#L31) | Sets the CPU limit. 1000m = 1 vCPU. | <code>string</code> |  | <code>&#34;1000m&#34;</code> |
| [cpu_idle](variables.tf#L37) | Allows the container to scale to zero. | <code>bool</code> |  | <code>true</code> |
| [env_vars](variables.tf#L43) | Environment variables for the Cloud Run service or job. | <code>map&#40;string&#41;</code> |  | <code>&#123;&#125;</code> |
| [ingress](variables.tf#L49) | Ingress settings. | <code>string</code> |  | <code>&#34;INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER&#34;</code> |
| [is_job](variables.tf#L55) | Set to true to create a job instead of a service. | <code>bool</code> |  | <code>false</code> |
| [memory](variables.tf#L76) | Sets the memory limit. 512Mi = 512MiB. | <code>string</code> |  | <code>&#34;512Mi&#34;</code> |
| [port](variables.tf#L87) | Mapping of port number and port name to open. | <code>number</code> |  | <code>8080</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [cloud_run](outputs.tf#L1) | Cloud Run Service that was created. |  |
| [service-account](outputs.tf#L6) | Service account that was created to run the Cloud Run Service. |  |
<!-- END TFDOC -->
