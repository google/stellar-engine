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

# VPN Connectivity

This stage provisions hybrid cloud connectivity between Google Cloud, AWS, Azure, and on-premises environments via Panorama. It establishes HA VPN Gateways, External VPN Gateways, and BGP peering to ensure resilient, encrypted communication across the multi-cloud footprint.

# Table of Contents

<!-- BEGIN TOC -->
- [Table of Contents](#table-of-contents)
- [Design Overview and choices](#design-overview-and-choices)
  - [HA VPN Architecture](#ha-vpn-architecture)
  - [CNSA-Compliant Security](#cnsa-compliant-security)
  - [Multi-Cloud Connectivity](#multi-cloud-connectivity)
  - [Dynamic Routing and BGP](#dynamic-routing-and-bgp)
- [How to Run This Stage](#how-to-run-this-stage)
  - [Running the stage](#running-the-stage)
- [Variables](#variables)
- [Outputs](#outputs)
<!-- END TOC -->

## Design Overview and choices

### HA VPN Architecture
The team has chosen to implement Google Cloud HA VPN to provide a 99.99% service availability SLA. This architecture requires two interfaces on the GCP side, each with a distinct public IP address, connecting to a redundant peer gateway. This setup ensures that connectivity remains active even during maintenance or single-zone failures.

### CNSA-Compliant Security
In order to support high-security requirements, the default configuration utilizes CNSA-compliant cipher suites. By default, tunnels use AES-GCM-256 for encryption and Group 20 Diffie-Hellman for key exchange. These settings ensure that data in transit meets federal and enterprise security standards.

### Multi-Cloud Connectivity
The stage is designed to bridge disparate cloud ecosystems:

AWS: Implements a four-tunnel design to support maximum throughput and AWS's requirement for redundant tunnels across multiple peer IPs.

Azure: Utilizes a two-tunnel design matching Azure's standard VPN Gateway redundancy model.

Panorama: Specifically designed for security management and logging traffic, allowing administrative tools to reach the cloud environment securely.

### Dynamic Routing and BGP
Minimizing manual route management is critical for operational stability. This stage leverages Cloud Routers to establish BGP sessions with all peers.

BGP Masking: Uses a dynamic mask length variable (defaulting to /30) for transit subnets.

Custom Advertisements: Cloud Routers are configured to advertise specific IP ranges while excluding the default advertisement of all VPC ranges to stay within route quotas.

## How to Run This Stage

### Running the stage

Once provider and variable values are in place and the correct user is configured, the stage can be run:

```bash
terraform init
terraform plan
terraform apply
```

---
<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [gcp_bgp_asn](variables.tf#L123) | BGP Autonomous System Number for the GCP Cloud Router. | <code>number</code> | ✓ |  |
| [gcp_network_name](variables.tf#L138) | The name of your existing GCP VPC network. | <code>string</code> | ✓ |  |
| [project_id](variables.tf#L233) | The GCP Project ID where the resources will be created. | <code>string</code> | ✓ |  |
| [region](variables.tf#L238) | The GCP region where the resources will be created. | <code>string</code> | ✓ |  |
| [aws_bgp_asn](variables.tf#L1) | BGP Autonomous System Number for AWS side. | <code>number</code> |  | <code>64512</code> |
| [aws_redundancy_type](variables.tf#L7) | Redundancy type for the AWS external VPN gateway. | <code>string</code> |  | <code>&#34;FOUR_IPS_REDUNDANCY&#34;</code> |
| [aws_secret_version](variables.tf#L13) | The version of the secret to pull from Secret Manager for AWS VPN PSKs. | <code>string</code> |  | <code>&#34;latest&#34;</code> |
| [aws_tunnel_cipher_suite](variables.tf#L19) | The CNSA-compliant cipher suite for the AWS VPN tunnels. If null, the global tunnel_cipher_suite is used. | <code title="object&#40;&#123;&#10;  phase1 &#61; optional&#40;object&#40;&#123;&#10;    encryption &#61; optional&#40;list&#40;string&#41;&#41;&#10;    integrity  &#61; optional&#40;list&#40;string&#41;&#41;&#10;    prf        &#61; optional&#40;list&#40;string&#41;&#41;&#10;    dh         &#61; optional&#40;list&#40;string&#41;&#41;&#10;  &#125;&#41;&#41;&#10;  phase2 &#61; optional&#40;object&#40;&#123;&#10;    encryption &#61; optional&#40;list&#40;string&#41;&#41;&#10;    integrity  &#61; optional&#40;list&#40;string&#41;&#41;&#10;    pfs        &#61; optional&#40;list&#40;string&#41;&#41;&#10;  &#125;&#41;&#41;&#10;&#125;&#41;">object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>null</code> |
| [aws_tunnel_details](variables.tf#L37) | Explicit configuration for the AWS tunnel peers. | <code title="map&#40;object&#40;&#123;&#10;  external_ip &#61; string&#10;  gcp_bgp_ip  &#61; string&#10;  aws_bgp_ip  &#61; string&#10;&#125;&#41;&#41;">map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> |  | <code>null</code> |
| [azure_bgp_asn](variables.tf#L47) | BGP Autonomous System Number for Azure side. | <code>number</code> |  | <code>65515</code> |
| [azure_gateway_ip_0](variables.tf#L53) | The first public IP address of the Azure VPN gateway. | <code>string</code> |  | <code>null</code> |
| [azure_gateway_ip_1](variables.tf#L59) | The second public IP address of the Azure VPN gateway. | <code>string</code> |  | <code>null</code> |
| [azure_gcp_bgp_apipa_ip_0](variables.tf#L65) | GCP-side internal BGP IP for the first Azure tunnel. | <code>string</code> |  | <code>&#34;169.254.21.1&#34;</code> |
| [azure_gcp_bgp_apipa_ip_1](variables.tf#L71) | GCP-side internal BGP IP for the second Azure tunnel. | <code>string</code> |  | <code>&#34;169.254.21.5&#34;</code> |
| [azure_peer_bgp_apipa_ip_0](variables.tf#L77) | Azure-side internal BGP IP for the first Azure tunnel. | <code>string</code> |  | <code>&#34;169.254.21.2&#34;</code> |
| [azure_peer_bgp_apipa_ip_1](variables.tf#L83) | Azure-side internal BGP IP for the second Azure tunnel. | <code>string</code> |  | <code>&#34;169.254.21.6&#34;</code> |
| [azure_redundancy_type](variables.tf#L89) | Redundancy type for the Azure external VPN gateway. | <code>string</code> |  | <code>&#34;TWO_IPS_REDUNDANCY&#34;</code> |
| [create_gcp_vpn_tunnels_aws](variables.tf#L95) | Determines if the GCP VPN tunnels and BGP peering sessions for AWS should be created (gateways remain active). | <code>bool</code> |  | <code>true</code> |
| [enable_azure_vpn](variables.tf#L101) | Set to false to destroy the Azure-related VPN tunnels and BGP peering sessions (leaving the gateways intact). | <code>bool</code> |  | <code>true</code> |
| [enable_panorama_vpn](variables.tf#L107) | Set to false to destroy the Panorama-related VPN tunnels and BGP peering sessions (leaving the gateways and router intact). | <code>bool</code> |  | <code>true</code> |
| [gateway_ip_version](variables.tf#L113) | The IP family of the gateway IPs for the HA-VPN gateway interfaces. Possible values: IPV4, IPV6. | <code>string</code> |  | <code>&#34;IPV4&#34;</code> |
| [gcp_bgp_identifier_range](variables.tf#L132) | Explicitly specifies a range of valid BGP Identifiers for this Router. It is provided as a link-local IPv4 range (from 169.254.0.0/16), of size at least /30. If null, GCP will auto-assign. | <code>string</code> |  | <code>null</code> |
| [gcp_router_name](variables.tf#L143) | The name of the GCP Cloud Router. | <code>string</code> |  | <code>null</code> |
| [ike_version](variables.tf#L149) | The IKE protocol version used for the VPN tunnels. | <code>number</code> |  | <code>2</code> |
| [mgmt_bgp_asn](variables.tf#L155) | MGMT router ASN. | <code>number</code> |  | <code>65200</code> |
| [name_prefix](variables.tf#L161) | A prefix to use for resource names. | <code>string</code> |  | <code>&#34;ha-vpn&#34;</code> |
| [panorama_bgp_asn](variables.tf#L167) | BGP Autonomous System Number for Panorama side. | <code>number</code> |  | <code>65516</code> |
| [panorama_gateway_ip_0](variables.tf#L173) | The first public IP address of the Panorama VPN gateway. | <code>string</code> |  | <code>null</code> |
| [panorama_gateway_ip_1](variables.tf#L179) | The second public IP address of the Panorama VPN gateway. | <code>string</code> |  | <code>null</code> |
| [panorama_gcp_bgp_apipa_ip_0](variables.tf#L185) | GCP-side internal BGP IP for the first Panorama tunnel. | <code>string</code> |  | <code>&#34;169.254.22.1&#34;</code> |
| [panorama_gcp_bgp_apipa_ip_1](variables.tf#L191) | GCP-side internal BGP IP for the second Panorama tunnel. | <code>string</code> |  | <code>&#34;169.254.22.5&#34;</code> |
| [panorama_peer_bgp_apipa_ip_0](variables.tf#L197) | Panorama-side internal BGP IP for the first Panorama tunnel. | <code>string</code> |  | <code>&#34;169.254.22.2&#34;</code> |
| [panorama_peer_bgp_apipa_ip_1](variables.tf#L203) | Panorama-side internal BGP IP for the second Panorama tunnel. | <code>string</code> |  | <code>&#34;169.254.22.6&#34;</code> |
| [panorama_project_id](variables.tf#L209) | The GCP Project ID where Panorama resources will be created (if different from global project_id). | <code>string</code> |  | <code>null</code> |
| [panorama_redundancy_type](variables.tf#L215) | Redundancy type for the Panorama external VPN gateway. | <code>string</code> |  | <code>&#34;TWO_IPS_REDUNDANCY&#34;</code> |
| [panorama_router_name](variables.tf#L221) | The name of the Cloud Router for Panorama (if different from global gcp_router_name). | <code>string</code> |  | <code>null</code> |
| [panorama_vpc_name](variables.tf#L227) | The name of the VPC network for Panorama (if different from global gcp_network_name). | <code>string</code> |  | <code>null</code> |
| [secret_name_aws_conn1_tun1](variables.tf#L243) | Secret Manager secret name for AWS Connection 1 Tunnel 1 PSK. | <code>string</code> |  | <code>null</code> |
| [secret_name_aws_conn1_tun2](variables.tf#L249) | Secret Manager secret name for AWS Connection 1 Tunnel 2 PSK. | <code>string</code> |  | <code>null</code> |
| [secret_name_aws_conn2_tun1](variables.tf#L255) | Secret Manager secret name for AWS Connection 2 Tunnel 1 PSK. | <code>string</code> |  | <code>null</code> |
| [secret_name_aws_conn2_tun2](variables.tf#L261) | Secret Manager secret name for AWS Connection 2 Tunnel 2 PSK. | <code>string</code> |  | <code>null</code> |
| [secret_name_azure_tunnel0](variables.tf#L267) | Secret Manager secret name for Azure Tunnel 0 PSK. | <code>string</code> |  | <code>null</code> |
| [secret_name_azure_tunnel1](variables.tf#L273) | Secret Manager secret name for Azure Tunnel 1 PSK. | <code>string</code> |  | <code>null</code> |
| [secret_name_panorama_tunnel0](variables.tf#L279) | Secret Manager secret name for Panorama Tunnel 0 PSK. | <code>string</code> |  | <code>null</code> |
| [secret_name_panorama_tunnel1](variables.tf#L285) | Secret Manager secret name for Panorama Tunnel 1 PSK. | <code>string</code> |  | <code>null</code> |
| [stack_type](variables.tf#L291) | The stack type for this VPN gateway. Possible values: IPV4_ONLY, IPV4_IPV6, IPV6_ONLY. | <code>string</code> |  | <code>&#34;IPV4_ONLY&#34;</code> |
| [tunnel_cipher_suite](variables.tf#L301) | The CNSA-compliant cipher suite for the VPN tunnels. Phase 1 and Phase 2 configurations. | <code title="object&#40;&#123;&#10;  phase1 &#61; optional&#40;object&#40;&#123;&#10;    encryption &#61; optional&#40;list&#40;string&#41;&#41;&#10;    integrity  &#61; optional&#40;list&#40;string&#41;&#41;&#10;    prf        &#61; optional&#40;list&#40;string&#41;&#41;&#10;    dh         &#61; optional&#40;list&#40;string&#41;&#41;&#10;  &#125;&#41;&#41;&#10;  phase2 &#61; optional&#40;object&#40;&#123;&#10;    encryption &#61; optional&#40;list&#40;string&#41;&#41;&#10;    integrity  &#61; optional&#40;list&#40;string&#41;&#41;&#10;    pfs        &#61; optional&#40;list&#40;string&#41;&#41;&#10;  &#125;&#41;&#41;&#10;&#125;&#41;">object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code title="&#123;&#10;  phase1 &#61; &#123;&#10;    encryption &#61; &#91;&#34;AES-GCM-16-256&#34;&#93;&#10;    integrity  &#61; &#91;&#93;&#10;    prf        &#61; &#91;&#34;PRF-HMAC-SHA2-384&#34;&#93;&#10;    dh         &#61; &#91;&#34;Group-20&#34;&#93;&#10;  &#125;&#10;  phase2 &#61; &#123;&#10;    encryption &#61; &#91;&#34;AES-GCM-16-256&#34;&#93;&#10;    integrity  &#61; &#91;&#93;&#10;    pfs        &#61; &#91;&#34;Group-20&#34;&#93;&#10;  &#125;&#10;&#125;">&#123;&#8230;&#125;</code> |
| [vpn_bgp_mask](variables.tf#L331) | The subnet mask length for the BGP APIPA IP ranges. | <code>number</code> |  | <code>30</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [aws_gcp_ha_gateway_name](outputs.tf#L3) | The name of the GCP HA VPN Gateway for AWS. |  |
| [aws_tunnel_details](outputs.tf#L8) | Detailed mapping for AWS VPN tunnels. |  |
| [azure_gcp_ha_gateway_name](outputs.tf#L30) | The name of the GCP HA VPN Gateway for Azure. |  |
| [azure_tunnel_details](outputs.tf#L35) | Detailed mapping for Azure VPN tunnels. |  |
| [panorama_gcp_ha_gateway_name](outputs.tf#L71) | The name of the GCP HA VPN Gateway for Panorama. |  |
| [panorama_tunnel_details](outputs.tf#L76) | Detailed mapping for Panorama VPN tunnels. |  |
| [vpn_network_config](outputs.tf#L112) | Network-wide BGP and redundancy parameters. |  |
| [vpn_security_config](outputs.tf#L122) | Security parameters used for all VPN tunnels. |  |
<!-- END TFDOC -->
