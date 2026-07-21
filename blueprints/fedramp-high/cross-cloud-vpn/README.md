# Cross Cloud VPN (GCP to AWS)
This blueprint contains all the necessary Terraform modules to build and deploy a cross cloud VPN from GCP to AWS using pre-existing secrets stored in GCP Secret Manager

## Introduction
This solution provisions a robust, redundant network connection between Google Cloud Platform (GCP) and Amazon Web Services (AWS).

It utilizes GCP's HA VPN Gateway (which provides two active interfaces) and connects them to an AWS Virtual Private Gateway via two separate Site-to-Site VPN Connections. This results in a mesh of four active tunnels for maximum availability.

1. High Availability: Four IPsec tunnels ensure that traffic automatically reroutes if any single tunnel or gateway interface fails.
2. Dynamic Routing (BGP): Routes are automatically exchanged between the clouds. No manual static route management is required.
3. Secure Secret Management: Pre-shared keys are fetched securely from GCP Secret Manager at runtime, ensuring no sensitive secrets are stored in plain text in the code.
4. Modular Design: The logic is encapsulated in a reusable module, making it easy to deploy multiple environments (dev, prod, etc.).

## Pre-requisite
1. Cloud Credentials: Active accounts for both AWS and GCP with permissions to create networking resources (VPCs, VPNs, Gateways).
2. Existing Networks:
    - An existing AWS VPC and its ID.
    - An existing GCP VPC Network and its name.
3. GCP Secret Manager: You must have 4 pre-shared keys stored in GCP Secret Manager (one for each tunnel endpoint).
4. IAM Permissions: The user or service account running Terraform must have the Secret Manager Secret Accessor role on the secrets.
<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [aws_bgp_asn](variables.tf#L1) | BGP Autonomous System Number for AWS side. | <code>number</code> | ✓ |  |
| [aws_region](variables.tf#L6) | The AWS region. | <code>string</code> | ✓ |  |
| [aws_vpc_id](variables.tf#L11) | The ID of your existing AWS VPC. | <code>string</code> | ✓ |  |
| [gcp_bgp_asn](variables.tf#L16) | BGP Autonomous System Number for GCP side. | <code>number</code> | ✓ |  |
| [gcp_network_name](variables.tf#L21) | The name of your existing GCP VPC network. | <code>string</code> | ✓ |  |
| [gcp_project_id](variables.tf#L26) | Your GCP Project ID. | <code>string</code> | ✓ |  |
| [gcp_region](variables.tf#L31) | The GCP region. | <code>string</code> | ✓ |  |
| [tunnel_secret_names](variables.tf#L36) | Map of secret names in GCP Secret Manager for the 4 tunnels. | <code>map&#40;string&#41;</code> | ✓ |  |
| [vpn_name](variables.tf#L41) | A prefix to use for all resource names. | <code>string</code> | ✓ |  |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [aws_bgp_asn](outputs.tf#L1) | The BGP ASN for the AWS side. |  |
| [aws_connection_1_tunnel_1_ip](outputs.tf#L6) | The public IP for AWS Connection 1, Tunnel 1. |  |
| [aws_connection_1_tunnel_2_ip](outputs.tf#L11) | The public IP for AWS Connection 1, Tunnel 2. |  |
| [aws_connection_2_tunnel_1_ip](outputs.tf#L16) | The public IP for AWS Connection 2, Tunnel 1. |  |
| [aws_connection_2_tunnel_2_ip](outputs.tf#L21) | The public IP for AWS Connection 2, Tunnel 2. |  |
| [aws_vpn_gateway_id](outputs.tf#L26) | The ID of the AWS Virtual Private Gateway (VGW). |  |
| [gcp_bgp_asn](outputs.tf#L31) | The BGP ASN for the GCP side. |  |
| [gcp_cloud_router_name](outputs.tf#L36) | The name of the GCP Cloud Router handling BGP. |  |
| [gcp_ha_gateway_interface_0_ip](outputs.tf#L41) | The public IP address for GCP's HA VPN Interface 0. |  |
| [gcp_ha_gateway_interface_1_ip](outputs.tf#L46) | The public IP address for GCP's HA VPN Interface 1. |  |
<!-- END TFDOC -->
## Disclaimer
- The present GCP Terraform Module in this project is set up and intended to be implemented in either a FedRAMP-High or IL5 (Impact Level 5) environment using the Assured Workloads within the Google Cloud Platform (GCP) organization.
- Assured Workloads in both environments ensures that sensitive data and workloads in GCP adhere to the rigorous security standards mandated by the DoD, making it suitable for government agencies.

## How to deploy the Terraform Code. The Deployment Steps
You should see this README and some terraform files.
1. Configure Secrets: Ensure your pre-shared keys are created in GCP Secret Manager.
2. Configure Variables: Update the terraform.tfvars file with your specific Project IDs, VPC IDs, and Secret Names.
3. Initialize and Apply: Run the following commands:

```bash
terraform init
terraform plan
terraform apply
```

The Output will look like following
```
Apply complete! Resources: 21 added, 0 changed, 0 destroyed.

Outputs:

aws_connection_1_tunnel_1_ip = "x.x.x.x"
aws_connection_1_tunnel_2_ip = "x.x.x.x"
aws_connection_2_tunnel_1_ip = "x.x.x.x"
aws_connection_2_tunnel_2_ip = "x.x.x.x"
aws_vpn_gateway_id = "vgw-xxxxxxxx"
gcp_cloud_router_name = "test1-gcp-router"
gcp_ha_gateway_interface_0_ip = "x.x.x.x"
gcp_ha_gateway_interface_1_ip = "x.x.x.x"
```

It will take a few minutes (typically 5-10 mins) for the VPN connections to provision and for BGP sessions to establish.
## Verification of a successful deployment?
1. GCP Console: Go to Hybrid Connectivity > VPN. You should see your HA VPN Gateway with 4 tunnels. The status should eventually turn green (Established).
2. AWS Console: Go to VPC > Site-to-Site VPN Connections. You should see two connections, each with 2 tunnels. The status should be UP.
3. Route Tables: Check the Route Tables in both AWS and GCP. You should see routes for the other cloud's CIDR block appearing automatically via BGP.
<!-- BEGIN_TF_DOCS -->
## Requirements

The following requirements are needed by this module:

- <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) (>=1.0)

- <a name="requirement_aws"></a> [aws](#requirement\_aws) (>= 5.0)

- <a name="requirement_google"></a> [google](#requirement\_google) (>= 5.0)

## Providers

The following providers are used by this module:

- <a name="provider_google"></a> [google](#provider\_google) (7.22.0)

## Modules

The following Modules are called:

### <a name="module_gcp_aws_ha_vpn"></a> [gcp\_aws\_ha\_vpn](#module\_gcp\_aws\_ha\_vpn)

Source: ./modules/gcp-aws-vpn

Version:

## Resources

The following resources are used by this module:

- [google_secret_manager_secret_version.vpn_keys](https://registry.terraform.io/providers/hashicorp/google/latest/docs/data-sources/secret_manager_secret_version) (data source)

## Required Inputs

The following input variables are required:

### <a name="input_aws_bgp_asn"></a> [aws\_bgp\_asn](#input\_aws\_bgp\_asn)

Description: BGP Autonomous System Number for AWS side.

Type: `number`

### <a name="input_aws_region"></a> [aws\_region](#input\_aws\_region)

Description: The AWS region.

Type: `string`

### <a name="input_aws_vpc_id"></a> [aws\_vpc\_id](#input\_aws\_vpc\_id)

Description: The ID of your existing AWS VPC.

Type: `string`

### <a name="input_gcp_bgp_asn"></a> [gcp\_bgp\_asn](#input\_gcp\_bgp\_asn)

Description: BGP Autonomous System Number for GCP side.

Type: `number`

### <a name="input_gcp_network_name"></a> [gcp\_network\_name](#input\_gcp\_network\_name)

Description: The name of your existing GCP VPC network.

Type: `string`

### <a name="input_gcp_project_id"></a> [gcp\_project\_id](#input\_gcp\_project\_id)

Description: Your GCP Project ID.

Type: `string`

### <a name="input_gcp_region"></a> [gcp\_region](#input\_gcp\_region)

Description: The GCP region.

Type: `string`

### <a name="input_tunnel_secret_names"></a> [tunnel\_secret\_names](#input\_tunnel\_secret\_names)

Description: Map of secret names in GCP Secret Manager for the 4 tunnels.

Type: `map(string)`

### <a name="input_vpn_name"></a> [vpn\_name](#input\_vpn\_name)

Description: A prefix to use for all resource names.

Type: `string`

## Optional Inputs

No optional inputs.

## Outputs

The following outputs are exported:

### <a name="output_aws_bgp_asn"></a> [aws\_bgp\_asn](#output\_aws\_bgp\_asn)

Description: The BGP ASN for the AWS side.

### <a name="output_aws_connection_1_tunnel_1_ip"></a> [aws\_connection\_1\_tunnel\_1\_ip](#output\_aws\_connection\_1\_tunnel\_1\_ip)

Description: The public IP for AWS Connection 1, Tunnel 1.

### <a name="output_aws_connection_1_tunnel_2_ip"></a> [aws\_connection\_1\_tunnel\_2\_ip](#output\_aws\_connection\_1\_tunnel\_2\_ip)

Description: The public IP for AWS Connection 1, Tunnel 2.

### <a name="output_aws_connection_2_tunnel_1_ip"></a> [aws\_connection\_2\_tunnel\_1\_ip](#output\_aws\_connection\_2\_tunnel\_1\_ip)

Description: The public IP for AWS Connection 2, Tunnel 1.

### <a name="output_aws_connection_2_tunnel_2_ip"></a> [aws\_connection\_2\_tunnel\_2\_ip](#output\_aws\_connection\_2\_tunnel\_2\_ip)

Description: The public IP for AWS Connection 2, Tunnel 2.

### <a name="output_aws_vpn_gateway_id"></a> [aws\_vpn\_gateway\_id](#output\_aws\_vpn\_gateway\_id)

Description: The ID of the AWS Virtual Private Gateway (VGW).

### <a name="output_gcp_bgp_asn"></a> [gcp\_bgp\_asn](#output\_gcp\_bgp\_asn)

Description: The BGP ASN for the GCP side.

### <a name="output_gcp_cloud_router_name"></a> [gcp\_cloud\_router\_name](#output\_gcp\_cloud\_router\_name)

Description: The name of the GCP Cloud Router handling BGP.

### <a name="output_gcp_ha_gateway_interface_0_ip"></a> [gcp\_ha\_gateway\_interface\_0\_ip](#output\_gcp\_ha\_gateway\_interface\_0\_ip)

Description: The public IP address for GCP's HA VPN Interface 0.

### <a name="output_gcp_ha_gateway_interface_1_ip"></a> [gcp\_ha\_gateway\_interface\_1\_ip](#output\_gcp\_ha\_gateway\_interface\_1\_ip)

Description: The public IP address for GCP's HA VPN Interface 1.
<!-- END_TF_DOCS -->