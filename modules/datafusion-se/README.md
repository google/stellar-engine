# Google Cloud Data Fusion Module

This module allows simple management of ['Google Data Fusion'](https://cloud.google.com/data-fusion) instances. It supports creating Basic or Enterprise, public or private instances.

## Examples

### Private instance with CMEK

The example creates a private Basic instance that reaches the shared VPC through Private Service Connect interfaces and encrypts its data with a customer-managed key. Grant the Data Fusion service agent access to the key before you create the instance.

```hcl
module "datafusion" {
  source               = "../../../modules/datafusion-se"
  name                 = "my-datafusion"
  region               = "us-east4"
  project_id           = "my-project"
  network              = "projects/my-host-project/global/networks/my-network"
  subnet               = "projects/my-host-project/regions/us-east4/subnetworks/my-subnet"
  landing_project_id   = "my-host-project"
  kms_key              = "projects/my-project/locations/us-east4/keyRings/my-keyring/cryptoKeys/my-key"
  firewall_create      = false
  ip_allocation_create = false
  network_peering      = false
  private_instance     = true
}
```
<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [landing_project_id](variables.tf#L94) | Landing project ID. | <code>string</code> | ✓ |  |
| [name](variables.tf#L99) | Name of the DataFusion instance. | <code>string</code> | ✓ |  |
| [network](variables.tf#L104) | Name of the network in the project with which the tenant project will be peered for executing pipelines in the form of projects/{project-id}/global/networks/{network}. | <code>string</code> | ✓ |  |
| [project_id](variables.tf#L121) | Project ID. | <code>string</code> | ✓ |  |
| [region](variables.tf#L126) | DataFusion region. | <code>string</code> | ✓ |  |
| [subnet](variables.tf#L131) | Full path to subnet. | <code>string</code> | ✓ |  |
| [accelerators](variables.tf#L20) | Accelerators. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>null</code> |
| [connection_type](variables.tf#L29) | Connection type for datafusion. | <code>string</code> |  | <code>&#34;PRIVATE_SERVICE_CONNECT_INTERFACES&#34;</code> |
| [dataproc_service_account](variables.tf#L40) | Service account for DataProc connection. | <code>string</code> |  | <code>null</code> |
| [description](variables.tf#L46) | DataFusion instance description. | <code>string</code> |  | <code>&#34;Terraform managed.&#34;</code> |
| [enable_stackdriver_logging](variables.tf#L52) | Option to enable Stackdriver Logging. | <code>bool</code> |  | <code>false</code> |
| [enable_stackdriver_monitoring](variables.tf#L58) | Option to enable Stackdriver Monitorig. | <code>bool</code> |  | <code>false</code> |
| [firewall_create](variables.tf#L64) | Create Network firewall rules to enable SSH. | <code>bool</code> |  | <code>true</code> |
| [ip_allocation](variables.tf#L70) | Ip allocated for datafusion instance when not using the auto created one and created outside of the module. | <code>string</code> |  | <code>null</code> |
| [ip_allocation_create](variables.tf#L76) | Create Ip range for datafusion instance. | <code>bool</code> |  | <code>true</code> |
| [kms_key](variables.tf#L82) | Full path to KMS key. | <code>string</code> |  | <code>null</code> |
| [labels](variables.tf#L88) | The resource labels for instance to use to annotate any related underlying resources, such as Compute Engine VMs. | <code>map&#40;string&#41;</code> |  | <code>&#123;&#125;</code> |
| [network_peering](variables.tf#L109) | Create Network peering between project and DataFusion tenant project. | <code>bool</code> |  | <code>true</code> |
| [private_instance](variables.tf#L115) | Create private instance. | <code>bool</code> |  | <code>true</code> |
| [type](variables.tf#L136) | Datafusion Instance type. It can be BASIC or ENTERPRISE (default value). | <code>string</code> |  | <code>&#34;BASIC&#34;</code> |
| [unreachable_cidr_block](variables.tf#L142) | The CIDR block to which the CDF instance can't route traffic to in the consumer project VPC. | <code>string</code> |  | <code>null</code> |

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
