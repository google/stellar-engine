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

# GCP to AWS HA VPN Module

This Terraform module establishes a Highly Available (HA) IPsec VPN connection with BGP dynamic routing between Google Cloud Platform (GCP) and Amazon Web Services (AWS).

It implements the 4-tunnel active-active redundancy architecture utilizing the interfaces of GCP's HA VPN Gateway connected to an AWS Virtual Private Gateway.

## Features

- **GCP-Only Mode (Default)**: Creates the GCP HA VPN Gateway, Peer External Gateway, Tunnels, and Cloud Router BGP configuration by ingesting existing AWS Public IPs and BGP IP ranges. Perfect for environments where AWS and GCP are managed by different teams/pipelines.
- **Full-Stack Mode (`create_aws_resources = true`)**: Connects to the AWS API, provisions the Virtual Private Gateway into an existing VPC, and automatically creates the Site-to-Site VPN connections completely natively.

## Example Usage

We provide two complete, production-grade examples in the `examples/` directory depending on your deployment model:

### 1. [GCP-Only Deployment](./options/gcp-only)
For environments where the AWS resources are already provisioned. You must provide the AWS Public IPs and BGP IPs manually via the `aws_tunnel_details` input map.

### 2. [GCP & AWS Managed Deployment](./options/gcp-and-aws)
For environments where you want this Terraform module to dynamically provision the AWS Virtual Private Gateway and Site-to-Site connections automatically.

<!-- BEGIN_TF_DOCS -->
## Requirements

The following requirements are needed by this module:

- <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) (>=1.0)

- <a name="requirement_aws"></a> [aws](#requirement\_aws) (>= 5.0)

- <a name="requirement_google"></a> [google](#requirement\_google) (>= 5.0)

## Providers

The following providers are used by this module:

- <a name="provider_aws"></a> [aws](#provider\_aws) (6.34.0)

- <a name="provider_google"></a> [google](#provider\_google) (7.21.0)

## Modules

No modules.

## Resources

The following resources are used by this module:

- [aws_customer_gateway.cgw_gcp_if0](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/customer_gateway) (resource)
- [aws_customer_gateway.cgw_gcp_if1](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/customer_gateway) (resource)
- [aws_vpn_connection.conn1_to_gcp_if0](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/vpn_connection) (resource)
- [aws_vpn_connection.conn2_to_gcp_if1](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/vpn_connection) (resource)
- [aws_vpn_gateway.aws_vgw](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/vpn_gateway) (resource)
- [aws_vpn_gateway_route_propagation.main](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/vpn_gateway_route_propagation) (resource)
- [google_compute_external_vpn_gateway.aws_peer_gw](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/compute_external_vpn_gateway) (resource)
- [google_compute_ha_vpn_gateway.gcp_ha_gw](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/compute_ha_vpn_gateway) (resource)
- [google_compute_router.gcp_router](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/compute_router) (resource)
- [google_compute_router_interface.if](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/compute_router_interface) (resource)
- [google_compute_router_peer.peer](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/compute_router_peer) (resource)
- [google_compute_vpn_tunnel.tunnel](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/compute_vpn_tunnel) (resource)
- [aws_route_table.main](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/route_table) (data source)
- [aws_vpc.existing](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/vpc) (data source)
- [google_compute_network.existing](https://registry.terraform.io/providers/hashicorp/google/latest/docs/data-sources/compute_network) (data source)

## Required Inputs

The following input variables are required:

### <a name="input_aws_bgp_asn"></a> [aws\_bgp\_asn](#input\_aws\_bgp\_asn)

Description: BGP Autonomous System Number for AWS side.

Type: `number`

### <a name="input_gcp_bgp_asn"></a> [gcp\_bgp\_asn](#input\_gcp\_bgp\_asn)

Description: BGP Autonomous System Number for the GCP Cloud Router.

Type: `number`

### <a name="input_gcp_network_name"></a> [gcp\_network\_name](#input\_gcp\_network\_name)

Description: The name of your existing GCP VPC network.

Type: `string`

### <a name="input_preshared_keys"></a> [preshared\_keys](#input\_preshared\_keys)

Description: Map of pre-shared keys for the IPsec tunnels.  
Required keys: 'conn1\_tun1', 'conn1\_tun2', 'conn2\_tun1', 'conn2\_tun2'.  

Example:  
preshared\_keys = {  
  conn1\_tun1 = "your-strong-preshared-key-1"  
  conn1\_tun2 = "your-strong-preshared-key-2"  
  conn2\_tun1 = "your-strong-preshared-key-3"  
  conn2\_tun2 = "your-strong-preshared-key-4"
}

Type: `map(string)`

### <a name="input_project_id"></a> [project\_id](#input\_project\_id)

Description: The GCP Project ID where the resources will be created.

Type: `string`

## Optional Inputs

The following input variables are optional (have default values):

### <a name="input_aws_tunnel_details"></a> [aws\_tunnel\_details](#input\_aws\_tunnel\_details)

Description: The explicit configuration for the AWS tunnel peers. REQUIRED ONLY if create\_aws\_resources is false.   
Map of 4 AWS tunnels with their external IPs and BGP IPs.  
Must contain exactly 4 keys: 'tun1', 'tun2', 'tun3', 'tun4'.  

Example:  
aws\_tunnel\_details = {  
  tun1 = { external\_ip = "203.0.113.1", gcp\_bgp\_ip = "169.254.21.2/30", aws\_bgp\_ip = "169.254.21.1" }  
  tun2 = { external\_ip = "203.0.113.2", gcp\_bgp\_ip = "169.254.22.2/30", aws\_bgp\_ip = "169.254.22.1" }  
  tun3 = { external\_ip = "203.0.113.3", gcp\_bgp\_ip = "169.254.23.2/30", aws\_bgp\_ip = "169.254.23.1" }  
  tun4 = { external\_ip = "203.0.113.4", gcp\_bgp\_ip = "169.254.24.2/30", aws\_bgp\_ip = "169.254.24.1" }
}

Type:

```hcl
map(object({
    external_ip = string
    gcp_bgp_ip  = string
    aws_bgp_ip  = string
  }))
```

Default: `null`

### <a name="input_aws_vpc_id"></a> [aws\_vpc\_id](#input\_aws\_vpc\_id)

Description: The ID of the existing AWS VPC to attach connections to. REQUIRED ONLY if create\_aws\_resources is true. Ignored if create\_aws\_resources is false.

Type: `string`

Default: `null`

### <a name="input_create_aws_resources"></a> [create\_aws\_resources](#input\_create\_aws\_resources)

Description: Determines if Terraform should manage the AWS side of the VPN (Virtual Private Gateways and Connections). If false (default), Terraform only creates GCP resources and assumes no API access to AWS. When false, you MUST provide aws\_tunnel\_details.

Type: `bool`

Default: `false`

### <a name="input_gateway_ip_version"></a> [gateway\_ip\_version](#input\_gateway\_ip\_version)

Description: The IP family of the gateway IPs for the HA-VPN gateway interfaces. Possible values: IPV4, IPV6.

Type: `string`

Default: `"IPV4"`

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

Default: `"ha-vpn-gcp-aws"`

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

### <a name="output_aws_bgp_asn"></a> [aws\_bgp\_asn](#output\_aws\_bgp\_asn)

Description: The BGP ASN for the AWS side.

### <a name="output_aws_vpn_gateway_id"></a> [aws\_vpn\_gateway\_id](#output\_aws\_vpn\_gateway\_id)

Description: The ID of the AWS Virtual Private Gateway (VGW).

### <a name="output_gcp_bgp_asn"></a> [gcp\_bgp\_asn](#output\_gcp\_bgp\_asn)

Description: The BGP ASN for the GCP side.

### <a name="output_gcp_ha_gateway_name"></a> [gcp\_ha\_gateway\_name](#output\_gcp\_ha\_gateway\_name)

Description: The name of the GCP HA VPN Gateway.

### <a name="output_tunnel_details"></a> [tunnel\_details](#output\_tunnel\_details)

Description: Detailed mapping of both GCP and AWS sides for each VPN tunnel.
<!-- END_TF_DOCS -->
