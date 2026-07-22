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

# Full-Stack GCP & AWS Managed HA VPN Example

This example demonstrates how to provision both the Google Cloud side and the AWS side of an HA VPN connection using the `gcp-aws-ha-vpn` module.

It connects to the AWS API, provisions the Virtual Private Gateway, connects it to the specified VPC, and configures the Site-to-Site VPN connections dynamically.

<!-- BEGIN_TF_DOCS -->
## Requirements

The following requirements are needed by this module:

- <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) (>=1.0)

- <a name="requirement_aws"></a> [aws](#requirement\_aws) (>= 5.0)

- <a name="requirement_google"></a> [google](#requirement\_google) (>= 5.0)

## Providers

The following providers are used by this module:

- <a name="provider_google"></a> [google](#provider\_google) (7.21.0)

## Modules

The following Modules are called:

### <a name="module_gcp_aws_vpn_both"></a> [gcp\_aws\_vpn\_both](#module\_gcp\_aws\_vpn\_both)

Source: ../../

Version:

## Resources

The following resources are used by this module:

- [google_secret_manager_regional_secret_version.psk_conn1_tun1](https://registry.terraform.io/providers/hashicorp/google/latest/docs/data-sources/secret_manager_regional_secret_version) (data source)
- [google_secret_manager_regional_secret_version.psk_conn1_tun2](https://registry.terraform.io/providers/hashicorp/google/latest/docs/data-sources/secret_manager_regional_secret_version) (data source)
- [google_secret_manager_regional_secret_version.psk_conn2_tun1](https://registry.terraform.io/providers/hashicorp/google/latest/docs/data-sources/secret_manager_regional_secret_version) (data source)
- [google_secret_manager_regional_secret_version.psk_conn2_tun2](https://registry.terraform.io/providers/hashicorp/google/latest/docs/data-sources/secret_manager_regional_secret_version) (data source)

## Required Inputs

The following input variables are required:

### <a name="input_aws_bgp_asn"></a> [aws\_bgp\_asn](#input\_aws\_bgp\_asn)

Description: The BGP ASN configured on the AWS side.

Type: `number`

### <a name="input_aws_region"></a> [aws\_region](#input\_aws\_region)

Description: The AWS region.

Type: `string`

### <a name="input_aws_vpc_id"></a> [aws\_vpc\_id](#input\_aws\_vpc\_id)

Description: The ID of the existing AWS VPC to attach connections to.

Type: `string`

### <a name="input_gcp_bgp_asn"></a> [gcp\_bgp\_asn](#input\_gcp\_bgp\_asn)

Description: BGP Autonomous System Number for the GCP Cloud Router.

Type: `number`

### <a name="input_gcp_network_name"></a> [gcp\_network\_name](#input\_gcp\_network\_name)

Description: The name of the existing GCP VPC network.

Type: `string`

### <a name="input_project_id"></a> [project\_id](#input\_project\_id)

Description: The GCP Project ID.

Type: `string`

### <a name="input_region"></a> [region](#input\_region)

Description: The GCP region for regional resources and secrets.

Type: `string`

### <a name="input_secret_name_conn1_tun1"></a> [secret\_name\_conn1\_tun1](#input\_secret\_name\_conn1\_tun1)

Description: The name of the regional secret in GCP Secret Manager for Connection 1 Tunnel 1.

Type: `string`

### <a name="input_secret_name_conn1_tun2"></a> [secret\_name\_conn1\_tun2](#input\_secret\_name\_conn1\_tun2)

Description: The name of the regional secret in GCP Secret Manager for Connection 1 Tunnel 2.

Type: `string`

### <a name="input_secret_name_conn2_tun1"></a> [secret\_name\_conn2\_tun1](#input\_secret\_name\_conn2\_tun1)

Description: The name of the regional secret in GCP Secret Manager for Connection 2 Tunnel 1.

Type: `string`

### <a name="input_secret_name_conn2_tun2"></a> [secret\_name\_conn2\_tun2](#input\_secret\_name\_conn2\_tun2)

Description: The name of the regional secret in GCP Secret Manager for Connection 2 Tunnel 2.

Type: `string`

## Optional Inputs

The following input variables are optional (have default values):

### <a name="input_gateway_ip_version"></a> [gateway\_ip\_version](#input\_gateway\_ip\_version)

Description: The IP family of the gateway IPs for the HA-VPN gateway interfaces. Possible values: IPV4, IPV6.

Type: `string`

Default: `"IPV4"`

### <a name="input_gcp_router_name"></a> [gcp\_router\_name](#input\_gcp\_router\_name)

Description: The name of the GCP Cloud Router to create.

Type: `string`

Default: `null`

### <a name="input_name_prefix"></a> [name\_prefix](#input\_name\_prefix)

Description: The prefix to apply to the generated VPN resources across both clouds.

Type: `string`

Default: `"ha-vpn-gcp-aws"`

### <a name="input_stack_type"></a> [stack\_type](#input\_stack\_type)

Description: The stack type for this VPN gateway. Possible values: IPV4\_ONLY, IPV4\_IPV6, IPV6\_ONLY.

Type: `string`

Default: `"IPV4_ONLY"`

### <a name="input_tunnel_cipher_suite"></a> [tunnel\_cipher\_suite](#input\_tunnel\_cipher\_suite)

Description: The CNSA-compliant cipher suite for the VPN tunnels. Phase 1 and Phase 2 configurations.

Type:

```hcl
object({
    phase1 = optional(object({
      encryption = optional(list(string))
      integrity  = optional(list(string))
      prf        = optional(list(string))
      dh         = optional(list(string))
    }))
    phase2 = optional(object({
      encryption = optional(list(string))
      integrity  = optional(list(string))
      pfs        = optional(list(string))
    }))
  })
```

Default: `null`

## Outputs

The following outputs are exported:

### <a name="output_gcp_ha_gateway_name"></a> [gcp\_ha\_gateway\_name](#output\_gcp\_ha\_gateway\_name)

Description: The name of the provisioned GCP HA VPN Gateway.

### <a name="output_tunnel_details"></a> [tunnel\_details](#output\_tunnel\_details)

Description: Detailed mapping of the IPs and ASNs for both sides of the VPN tunnels.
<!-- END_TF_DOCS -->
