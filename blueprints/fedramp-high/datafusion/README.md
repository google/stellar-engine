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

# Data Fusion

<!-- BEGIN TOC -->
- [Introduction to Data Fusion](#introduction-to-data-fusion)
- [Data Fusion Blueprint](#data-fusion-blueprint)
- [Deployment Steps](#deployment-steps)
  - [Troubleshooting](#troubleshooting)
- [Verification of a successful deployment](#verification-of-a-successful-deployment)
- [Variables](#variables)
- [Outputs](#outputs)
<!-- END TOC -->

## Introduction to Data Fusion


## Data Fusion Blueprint
This blueprint deploys Data Fusion.


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

### Troubleshooting

If you receive any errors during the `terraform apply`, run the apply two or three more times until a successful deployment is achieved.

## Verification of a successful deployment
Navigate to [Data Fusion](https://console.cloud.google.com/data-fusion) within the GCP console to verify whether the resources have been created.
<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [core_project_id](variables.tf#L1) | Core project ID. | <code>string</code> | ✓ |  |
| [kms_keyring_name](variables.tf#L12) | KMS Keyring. | <code>string</code> | ✓ |  |
| [main_project_id](variables.tf#L17) | Project id. | <code>string</code> | ✓ |  |
| [name](variables.tf#L22) | Name of DataFusion instance. | <code>string</code> | ✓ |  |
| [network_name](variables.tf#L27) | Full path to VPC. | <code>string</code> | ✓ |  |
| [network_project_id](variables.tf#L32) | Landing project id. | <code>string</code> | ✓ |  |
| [region](variables.tf#L37) | Location to deploy job. | <code>string</code> | ✓ |  |
| [subnetwork_name](variables.tf#L42) | Full path to subnet. | <code>string</code> | ✓ |  |
| [kms_key_name](variables.tf#L6) | Full path to KMS key for pubsub. | <code>string</code> |  | <code>null</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [id](outputs.tf#L1) | Fully qualified instance id. |  |
| [resource](outputs.tf#L6) | DataFusion resource. |  |
| [service_endpoint](outputs.tf#L11) | DataFusion Service Endpoint. |  |
| [version](outputs.tf#L16) | DataFusion version. |  |
<!-- END TFDOC -->
