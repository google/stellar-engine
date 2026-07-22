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

# GCP to Azure HA VPN Module

This Terraform module establishes a Highly Available (HA) IPsec VPN connection with BGP dynamic routing between Google Cloud Platform (GCP) and Microsoft Azure.

It follows Google's recommended topology for achieving a 99.99% SLA by utilizing the two Active-Active interfaces of GCP's HA VPN Gateway mapped correctly against Azure's Virtual Network Gateway infrastructure using APIPA BGP ranges.

## Features

- **GCP-Only Mode (Default)**: Creates the GCP HA VPN Gateway, Peer External Gateway, Tunnels, and Cloud Router BGP configuration by ingesting existing Azure Public IPs. Perfect for environments where Azure and GCP are managed by different teams/pipelines.
- **Full-Stack Mode (`create_azure_resources = true`)**: Connects to the Azure API, dynamically scrapes the Virtual Network Gateway's Public IPs, and creates the corresponding Azure Local Network Gateways and VPN Connections entirely from this module.

## Example Usage

We provide two complete, production-grade examples in the `examples/` directory depending on your deployment model:

### 1. [GCP-Only Deployment](./examples/gcp-only)
For environments where the Azure resources (Virtual Network Gateway, Public IPs) are already provisioned or managed by a separate team. You must provide the Azure Public IPs manually.

### 2. [GCP & Azure Managed Deployment](./examples/gcp-and-azure)
For environments where you want this Terraform module to dynamically discover the Azure Virtual Network Gateway IPs and automatically build the local network gateways and IPsec connections directly in Azure.

<!-- BEGIN_TF_DOCS -->
## Requirements

The following requirements are needed by this module:

- <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) (>=1.0)

- <a name="requirement_azurerm"></a> [azurerm](#requirement\_azurerm) (>= 3.0)

- <a name="requirement_google"></a> [google](#requirement\_google) (>= 5.0)

## Providers

The following providers are used by this module:

- <a name="provider_azurerm"></a> [azurerm](#provider\_azurerm) (4.62.1)

- <a name="provider_google"></a> [google](#provider\_google) (7.21.0)

## Modules

No modules.

## Resources

The following resources are used by this module:

- [azurerm_local_network_gateway.gcp_lng_0](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/local_network_gateway) (resource)
- [azurerm_local_network_gateway.gcp_lng_1](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/local_network_gateway) (resource)
- [azurerm_virtual_network_gateway_connection.azure_conn_0](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/virtual_network_gateway_connection) (resource)
- [azurerm_virtual_network_gateway_connection.azure_conn_1](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/virtual_network_gateway_connection) (resource)
- [google_compute_external_vpn_gateway.azure_peer_gw](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/compute_external_vpn_gateway) (resource)
- [google_compute_ha_vpn_gateway.gcp_ha_gw](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/compute_ha_vpn_gateway) (resource)
- [google_compute_router.gcp_router](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/compute_router) (resource)
- [google_compute_router_interface.if0](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/compute_router_interface) (resource)
- [google_compute_router_interface.if1](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/compute_router_interface) (resource)
- [google_compute_router_peer.peer0](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/compute_router_peer) (resource)
- [google_compute_router_peer.peer1](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/compute_router_peer) (resource)
- [google_compute_vpn_tunnel.tunnel0](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/compute_vpn_tunnel) (resource)
- [google_compute_vpn_tunnel.tunnel1](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/compute_vpn_tunnel) (resource)
- [azurerm_public_ip.gw_ip0](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/data-sources/public_ip) (data source)
- [azurerm_public_ip.gw_ip1](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/data-sources/public_ip) (data source)
- [azurerm_resource_group.rg](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/data-sources/resource_group) (data source)
- [azurerm_virtual_network_gateway.existing](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/data-sources/virtual_network_gateway) (data source)
- [google_compute_network.existing](https://registry.terraform.io/providers/hashicorp/google/latest/docs/data-sources/compute_network) (data source)

## Required Inputs

The following input variables are required:

### <a name="input_azure_bgp_asn"></a> [azure\_bgp\_asn](#input\_azure\_bgp\_asn)

Description: BGP Autonomous System Number for Azure side.

Type: `number`

### <a name="input_gcp_bgp_asn"></a> [gcp\_bgp\_asn](#input\_gcp\_bgp\_asn)

Description: BGP Autonomous System Number for the GCP Cloud Router.

Type: `number`

### <a name="input_gcp_network_name"></a> [gcp\_network\_name](#input\_gcp\_network\_name)

Description: The name of your existing GCP VPC network.

Type: `string`

### <a name="input_preshared_keys"></a> [preshared\_keys](#input\_preshared\_keys)

Description: Map of pre-shared keys for the IPsec tunnels.  
Required keys: 'tunnel0', 'tunnel1'.  

Example:  
preshared\_keys = {  
  tunnel0 = "your-strong-preshared-key-1"  
  tunnel1 = "your-strong-preshared-key-2"
}

Type: `map(string)`

### <a name="input_project_id"></a> [project\_id](#input\_project\_id)

Description: The GCP Project ID where the resources will be created.

Type: `string`

## Optional Inputs

The following input variables are optional (have default values):

### <a name="input_azure_bgp_apipa_ip_0"></a> [azure\_bgp\_apipa\_ip\_0](#input\_azure\_bgp\_apipa\_ip\_0)

Description: The Azure BGP APIPA IP for Tunnel 0 (e.g. 169.254.21.2)

Type: `string`

Default: `"169.254.21.2"`

### <a name="input_azure_bgp_apipa_ip_1"></a> [azure\_bgp\_apipa\_ip\_1](#input\_azure\_bgp\_apipa\_ip\_1)

Description: The Azure BGP APIPA IP for Tunnel 1 (e.g. 169.254.21.6)

Type: `string`

Default: `"169.254.21.6"`

### <a name="input_azure_gateway_ip_0"></a> [azure\_gateway\_ip\_0](#input\_azure\_gateway\_ip\_0)

Description: The public IP of the first instance of the Azure VPN Gateway. REQUIRED if create\_azure\_resources is false. If create\_azure\_resources is true, this can be left null and will be automatically discovered via the Azure API.

Type: `string`

Default: `null`

### <a name="input_azure_gateway_ip_1"></a> [azure\_gateway\_ip\_1](#input\_azure\_gateway\_ip\_1)

Description: The public IP of the second instance of the Azure VPN Gateway. REQUIRED if create\_azure\_resources is false. If create\_azure\_resources is true, this can be left null and will be automatically discovered via the Azure API.

Type: `string`

Default: `null`

### <a name="input_azure_resource_group_name"></a> [azure\_resource\_group\_name](#input\_azure\_resource\_group\_name)

Description: The name of the Azure Resource Group containing the existing Virtual Network Gateway. REQUIRED ONLY if create\_azure\_resources is true. Ignored if create\_azure\_resources is false.

Type: `string`

Default: `null`

### <a name="input_azure_vpn_gateway_name"></a> [azure\_vpn\_gateway\_name](#input\_azure\_vpn\_gateway\_name)

Description: The name of the existing Azure Virtual Network Gateway to attach connections to. REQUIRED ONLY if create\_azure\_resources is true. Ignored if create\_azure\_resources is false.

Type: `string`

Default: `null`

### <a name="input_create_azure_resources"></a> [create\_azure\_resources](#input\_create\_azure\_resources)

Description: Determines if Terraform should manage the Azure side of the VPN (Local Network Gateways and Connections). If false (default), Terraform only creates GCP resources and assumes no API access to Azure. When false, you MUST provide azure\_gateway\_ip\_0 and azure\_gateway\_ip\_1.

Type: `bool`

Default: `false`

### <a name="input_gateway_ip_version"></a> [gateway\_ip\_version](#input\_gateway\_ip\_version)

Description: The IP family of the gateway IPs for the HA-VPN gateway interfaces. Possible values: IPV4, IPV6.

Type: `string`

Default: `"IPV4"`

### <a name="input_gcp_bgp_apipa_ip_0"></a> [gcp\_bgp\_apipa\_ip\_0](#input\_gcp\_bgp\_apipa\_ip\_0)

Description: The GCP BGP APIPA IP for Tunnel 0 (e.g. 169.254.21.1)

Type: `string`

Default: `"169.254.21.1"`

### <a name="input_gcp_bgp_apipa_ip_1"></a> [gcp\_bgp\_apipa\_ip\_1](#input\_gcp\_bgp\_apipa\_ip\_1)

Description: The GCP BGP APIPA IP for Tunnel 1 (e.g. 169.254.21.5)

Type: `string`

Default: `"169.254.21.5"`

### <a name="input_gcp_bgp_identifier_range"></a> [gcp\_bgp\_identifier\_range](#input\_gcp\_bgp\_identifier\_range)

Description: Explicitly specifies a range of valid BGP Identifiers for this Router. It is provided as a link-local IPv4 range (from 169.254.0.0/16), of size at least /30. If null, GCP will auto-assign.

Type: `string`

Default: `null`

### <a name="input_gcp_router_name"></a> [gcp\_router\_name](#input\_gcp\_router\_name)

Description: The name of the GCP Cloud Router to create.

Type: `string`

Default: `null`

### <a name="input_name_prefix"></a> [name\_prefix](#input\_name\_prefix)

Description: A prefix to use for all resource names.

Type: `string`

Default: `"ha-vpn-gcp-azure"`

### <a name="input_stack_type"></a> [stack\_type](#input\_stack\_type)

Description: The stack type for this VPN gateway to identify the IP protocols that are enabled. Possible values: IPV4\_ONLY, IPV4\_IPV6, IPV6\_ONLY.

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

Default:

```json
{
  "phase1": {
    "dh": [
      "Group-20"
    ],
    "encryption": [
      "AES-GCM-16-256"
    ],
    "integrity": [],
    "prf": [
      "PRF-HMAC-SHA2-384"
    ]
  },
  "phase2": {
    "encryption": [
      "AES-GCM-16-256"
    ],
    "integrity": [],
    "pfs": [
      "Group-20"
    ]
  }
}
```

## Outputs

The following outputs are exported:

### <a name="output_azure_bgp_asn"></a> [azure\_bgp\_asn](#output\_azure\_bgp\_asn)

Description: The BGP ASN for the Azure side.

### <a name="output_azure_virtual_network_gateway_ip_0"></a> [azure\_virtual\_network\_gateway\_ip\_0](#output\_azure\_virtual\_network\_gateway\_ip\_0)

Description: The public IP address for Azure's Virtual Network Gateway Interface 0.

### <a name="output_azure_virtual_network_gateway_ip_1"></a> [azure\_virtual\_network\_gateway\_ip\_1](#output\_azure\_virtual\_network\_gateway\_ip\_1)

Description: The public IP address for Azure's Virtual Network Gateway Interface 1.

### <a name="output_gcp_bgp_asn"></a> [gcp\_bgp\_asn](#output\_gcp\_bgp\_asn)

Description: The BGP ASN for the GCP side.

### <a name="output_gcp_ha_gateway_interface_0_ip"></a> [gcp\_ha\_gateway\_interface\_0\_ip](#output\_gcp\_ha\_gateway\_interface\_0\_ip)

Description: The public IP address for GCP's HA VPN Interface 0.

### <a name="output_gcp_ha_gateway_interface_1_ip"></a> [gcp\_ha\_gateway\_interface\_1\_ip](#output\_gcp\_ha\_gateway\_interface\_1\_ip)

Description: The public IP address for GCP's HA VPN Interface 1.

### <a name="output_gcp_ha_gateway_name"></a> [gcp\_ha\_gateway\_name](#output\_gcp\_ha\_gateway\_name)

Description: The name of the GCP HA VPN Gateway.

### <a name="output_tunnel_details"></a> [tunnel\_details](#output\_tunnel\_details)

Description: Detailed mapping of both GCP and Azure sides for each VPN tunnel.
<!-- END_TF_DOCS -->
