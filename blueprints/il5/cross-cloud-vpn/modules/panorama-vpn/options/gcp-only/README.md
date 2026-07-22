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

# GCP-Only HA VPN Example

This example demonstrates how to provision the Google Cloud side of an HA VPN connection to Azure using the `gcp-azure-vpn` module.

It assumes that the Azure Virtual Network Gateway and its Public IPs are already created and managed elsewhere (e.g., by another team or pipeline). You must manually provide the Azure Public IPs.

<!-- BEGIN_TF_DOCS -->
## Requirements

The following requirements are needed by this module:

- <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) (>=1.0)

- <a name="requirement_google"></a> [google](#requirement\_google) (>= 5.0)

## Providers

The following providers are used by this module:

- <a name="provider_google"></a> [google](#provider\_google) (7.21.0)

## Modules

The following Modules are called:

### <a name="module_gcp_azure_vpn_gcp_only"></a> [gcp\_azure\_vpn\_gcp\_only](#module\_gcp\_azure\_vpn\_gcp\_only)

Source: ../../

Version:

## Resources

The following resources are used by this module:

- [google_secret_manager_regional_secret_version.psk_tun0](https://registry.terraform.io/providers/hashicorp/google/latest/docs/data-sources/secret_manager_regional_secret_version) (data source)
- [google_secret_manager_regional_secret_version.psk_tun1](https://registry.terraform.io/providers/hashicorp/google/latest/docs/data-sources/secret_manager_regional_secret_version) (data source)

## Required Inputs

The following input variables are required:

### <a name="input_azure_bgp_asn"></a> [azure\_bgp\_asn](#input\_azure\_bgp\_asn)

Description: The BGP ASN configured on the Azure side.

Type: `number`

### <a name="input_azure_gateway_ip_0"></a> [azure\_gateway\_ip\_0](#input\_azure\_gateway\_ip\_0)

Description: The public IP of the first instance of the Azure Virtual Network Gateway.

Type: `string`

### <a name="input_azure_gateway_ip_1"></a> [azure\_gateway\_ip\_1](#input\_azure\_gateway\_ip\_1)

Description: The public IP of the second instance of the Azure Virtual Network Gateway.

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

### <a name="input_secret_name_tunnel0"></a> [secret\_name\_tunnel0](#input\_secret\_name\_tunnel0)

Description: The name of the regional secret in GCP Secret Manager for Tunnel 0.

Type: `string`

### <a name="input_secret_name_tunnel1"></a> [secret\_name\_tunnel1](#input\_secret\_name\_tunnel1)

Description: The name of the regional secret in GCP Secret Manager for Tunnel 1.

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

Description: The prefix to apply to the generated GCP VPN resources.

Type: `string`

Default: `"ha-vpn-gcp-only"`

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

### <a name="output_gcp_bgp_asn"></a> [gcp\_bgp\_asn](#output\_gcp\_bgp\_asn)

Description: The BGP ASN for the GCP Cloud Router.

### <a name="output_gcp_ha_gateway_name"></a> [gcp\_ha\_gateway\_name](#output\_gcp\_ha\_gateway\_name)

Description: The name of the provisioned GCP HA VPN Gateway.

### <a name="output_tunnel_details"></a> [tunnel\_details](#output\_tunnel\_details)

Description: Detailed mapping of the IPs and ASNs for both sides of the VPN tunnels.
<!-- END_TF_DOCS -->
