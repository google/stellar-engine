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

# Google Cloud Data Fusion Module

This module allows simple management of ['Google Data Fusion'](https://cloud.google.com/data-fusion) instances. It supports creating Basic or Enterprise, public or private instances.

## Examples

## Without CMEK 

```hcl
module "datafusion" {
  source                   = "../../../modules/datafusion"
  name                     = var.name
  region                   = var.region
  project_id               = var.project_id
  network                  = var.network
  subnet                   = var.subnet
  firewall_create          = false
  landing_project_id       = var.landing_project_id
  private_instance         = true
  ip_allocation_create     = false
  network_peering          = false

  depends_on = [google_kms_crypto_key_iam_binding.datafusion]
}
```
<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [accelerators](variables.tf#L20) | Accelerators. | <code title="object&#40;&#123;&#10;  accelerator_type &#61; optional&#40;string&#41;&#10;  state            &#61; optional&#40;string&#41;&#10;&#125;&#41;&#10;&#10;&#10;default &#61; null">object&#40;&#123;&#8230;default &#61; null</code> | ✓ |  |
| [landing_project_id](variables.tf#L95) | Landing project ID. | <code>string</code> | ✓ |  |
| [name](variables.tf#L100) | Name of the DataFusion instance. | <code>string</code> | ✓ |  |
| [network](variables.tf#L105) | Name of the network in the project with which the tenant project will be peered for executing pipelines in the form of projects/{project-id}/global/networks/{network}. | <code>string</code> | ✓ |  |
| [project_id](variables.tf#L122) | Project ID. | <code>string</code> | ✓ |  |
| [region](variables.tf#L127) | DataFusion region. | <code>string</code> | ✓ |  |
| [subnet](variables.tf#L132) | Full path to subnet. | <code>string</code> | ✓ |  |
| [connection_type](variables.tf#L30) | Connection type for datafusion. | <code>string</code> |  | <code>&#34;PRIVATE_SERVICE_CONNECT_INTERFACES&#34;</code> |
| [dataproc_service_account](variables.tf#L41) | Service account for DataProc connection. | <code>string</code> |  | <code>null</code> |
| [description](variables.tf#L47) | DataFusion instance description. | <code>string</code> |  | <code>&#34;Terraform managed.&#34;</code> |
| [enable_stackdriver_logging](variables.tf#L53) | Option to enable Stackdriver Logging. | <code>bool</code> |  | <code>false</code> |
| [enable_stackdriver_monitoring](variables.tf#L59) | Option to enable Stackdriver Monitorig. | <code>bool</code> |  | <code>false</code> |
| [firewall_create](variables.tf#L65) | Create Network firewall rules to enable SSH. | <code>bool</code> |  | <code>true</code> |
| [ip_allocation](variables.tf#L71) | Ip allocated for datafusion instance when not using the auto created one and created outside of the module. | <code>string</code> |  | <code>null</code> |
| [ip_allocation_create](variables.tf#L77) | Create Ip range for datafusion instance. | <code>bool</code> |  | <code>true</code> |
| [kms_key](variables.tf#L83) | Full path to KMS key. | <code>string</code> |  | <code>null</code> |
| [labels](variables.tf#L89) | The resource labels for instance to use to annotate any related underlying resources, such as Compute Engine VMs. | <code>map&#40;string&#41;</code> |  | <code>&#123;&#125;</code> |
| [network_peering](variables.tf#L110) | Create Network peering between project and DataFusion tenant project. | <code>bool</code> |  | <code>true</code> |
| [private_instance](variables.tf#L116) | Create private instance. | <code>bool</code> |  | <code>true</code> |
| [type](variables.tf#L137) | Datafusion Instance type. It can be BASIC or ENTERPRISE (default value). | <code>string</code> |  | <code>&#34;BASIC&#34;</code> |
| [unreachable_cidr_block](variables.tf#L143) | The CIDR block to which the CDF instance can't route traffic to in the consumer project VPC. | <code>string</code> |  | <code>null</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [id](outputs.tf#L17) | Fully qualified instance id. |  |
| [ip_allocation](outputs.tf#L22) | IP range reserved for Data Fusion instance in case of a private instance. |  |
| [resource](outputs.tf#L27) | DataFusion resource. |  |
| [service_account](outputs.tf#L32) | DataFusion DataProc connector Service Account. |  |
| [service_endpoint](outputs.tf#L37) | DataFusion Service Endpoint. |  |
| [version](outputs.tf#L42) | DataFusion version. |  |
<!-- END TFDOC -->
