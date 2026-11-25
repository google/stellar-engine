# Multi-cloud HA VPN blueprint

This blueprint provisions CNSA-compliant [Cloud HA VPN](https://cloud.google.com/network-connectivity/docs/vpn/concepts/overview#ha-vpn) connectivity from a Google Cloud VPC to external peers across AWS, Azure, and on-premises networks. It composes `modules/net-vpn-ha` per peer via `for_each`, reads every IPsec pre-shared key from global or regional Secret Manager without plaintext fallback, and advertises the Cloud DNS forwarding return range by default.

<!-- BEGIN TOC -->
- [1 Architecture](#1-architecture)
- [2 Prerequisites](#2-prerequisites)
- [3 Deployment steps](#3-deployment-steps)
- [4 Compliance scope](#4-compliance-scope)
- [Variables](#variables)
- [Outputs](#outputs)
<!-- END TOC -->

## 1 Architecture

Each entry in the `peers` map creates an isolated HA VPN gateway, external VPN gateway, Cloud Router, and set of IKEv2 BGP-peered tunnels in `project_id` and `region` through `modules/net-vpn-ha`.

- Leaving `peers` empty provisions zero gateways, routers, tunnels, or Secret Manager lookups.
- Tunnels default to CNSA IKEv2 AEAD parameters using `AES-GCM-16-256`, `PRF-HMAC-SHA2-384`, and `Group-20` for Phase 1 alongside `AES-GCM-16-256` and `Group-20` for Phase 2, with `integrity` unset because AEAD provides authenticated encryption.
- Per-peer `cipher_suite` overrides inherit unspecified phases from `var.cipher_suite`, preventing partial configurations with null Phase 1 or Phase 2 blocks.
- Setting `advertise_dns_forwarding_range` to `true` switches each Cloud Router to `CUSTOM` advertisement mode with `ALL_SUBNETS` enabled and adds `35.199.192.0/19` so [Cloud DNS outbound forwarding](https://cloud.google.com/dns/docs/zones/forwarding-zones) replies route back over the tunnels.
- Every tunnel fetches its pre-shared key from global Secret Manager via `data.google_secret_manager_secret_version` when `psk_secret_location` is unset, or from regional Secret Manager via `data.google_secret_manager_regional_secret_version` when `psk_secret_location` or a regional secret resource path is provided, with fail-closed postconditions rejecting empty payloads and outputs omitting pre-shared keys and raw tunnel objects.
- Plan-time validations enforce unique BGP `/30` session ranges across all peers on the VPC, reject the Compute Engine metadata server range `169.254.169.252/30`, and enforce RFC1035 lowercase tunnel keys within the 63-character Compute Engine resource name limit.
- Supported gateway IP stacks are `IPV4_ONLY` and `IPV4_IPV6` via `stack_type`, where `IPV4_IPV6` configures IPv4 BGP sessions carrying IPv6 routes rather than IPv6-only BGP over `2600:2d00:0:2::/63`.

## 2 Prerequisites

- Provision the target VPC network in `project_id` or pass its full self-link in `network`.
- Store each tunnel IPsec pre-shared key as a global CMEK-encrypted or regional Secret Manager secret version before running `terraform plan`.
- Grant the deploying identity `roles/compute.networkAdmin` on `project_id` and `roles/secretmanager.secretAccessor` on each referenced PSK secret.
- Confirm your Terraform binary and Google provider plugins satisfy the constraints declared in `versions.tf`.
- Coordinate peer gateway public IPs, ASNs, and unique link-local `/30` BGP APIPA ranges in `169.254.0.0/16` with the remote cloud or on-premises network team, avoiding `169.254.169.252/30` on GCP and `169.254.0.0/30` through `169.254.5.0/30` on AWS.

## 3 Deployment steps

1. Copy `terraform.tfvars.sample` to `terraform.tfvars` and configure `project_id`, `network`, `region`, `router_asn`, and each external entry under `peers`.
2. Initialize, review, and apply the Terraform configuration:

```bash
terraform init
terraform plan
terraform apply
```

3. Retrieve the allocated HA VPN gateway public interface IPs via `terraform output vpn_gateway_interfaces` and configure the matching peer gateways in AWS, Azure, or your on-premises router.
4. Verify BGP session status and learned routes in [Cloud Routers](https://console.cloud.google.com/hybrid/routers/list) and [Cloud VPN tunnels](https://console.cloud.google.com/hybrid/vpn/list).

## 4 Compliance scope

- Deploy this blueprint inside a FedRAMP High or IL5 Assured Workloads folder within your Google Cloud organization.
- Ensure global or regional Secret Manager secrets storing IPsec pre-shared keys use regional data residency and CMEK-backed encryption policies matching your compliance boundary.
- Treat Terraform state files as sensitive because `google_compute_vpn_tunnel` stores `shared_secret` in state, and restrict state bucket IAM access to authorized automation identities.
<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [network](variables.tf#L94) | Self-link or name of the VPC network hosting the VPN gateways. | <code>string</code> | ✓ |  |
| [project_id](variables.tf#L376) | GCP project ID hosting HA VPN gateways, external gateways, and routers. | <code>string</code> | ✓ |  |
| [region](variables.tf#L390) | GCP region where HA VPN gateways, tunnels, and routers are created. | <code>string</code> | ✓ |  |
| [advertise_dns_forwarding_range](variables.tf#L15) | Advertise 35.199.192.0/19 on routers for Cloud DNS return traffic. | <code>bool</code> |  | <code>true</code> |
| [cipher_suite](variables.tf#L22) | Default IKEv2 Phase 1 and Phase 2 cipher suite for VPN tunnels. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>&#123;&#8230;&#125;</code> |
| [custom_advertised_ip_ranges](variables.tf#L64) | Extra CIDR ranges and descriptions advertised on Cloud Routers. | <code>map&#40;string&#41;</code> |  | <code>&#123;&#125;</code> |
| [name_prefix](variables.tf#L79) | Prefix for HA VPN gateway, router, and tunnel resource names. | <code>string</code> |  | <code>&#34;ha-vpn&#34;</code> |
| [peers](variables.tf#L105) | External multi-cloud or on-premises VPN peers keyed by peer ID. | <code>map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> |  | <code>&#123;&#125;</code> |
| [router_asn](variables.tf#L401) | Default private BGP ASN for Cloud Routers created by this blueprint. | <code>number</code> |  | <code>64514</code> |
| [stack_type](variables.tf#L416) | Gateway IP stack type (IPV4_ONLY or IPV4_IPV6). IPV4_IPV6 uses IPv4 BGP sessions carrying IPv6 routes, not IPv6-only BGP over 2600:2d00:0:2::/63. | <code>string</code> |  | <code>&#34;IPV4_ONLY&#34;</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [external_gateway_ids](outputs.tf#L15) | External VPN gateway resource IDs keyed by peer identifier. |  |
| [router_names](outputs.tf#L23) | Cloud Router names keyed by peer identifier. |  |
| [tunnel_names](outputs.tf#L30) | VPN tunnel names keyed by peer identifier and tunnel key. |  |
| [tunnel_self_links](outputs.tf#L37) | VPN tunnel self-links keyed by peer and tunnel key. |  |
| [vpn_gateway_ids](outputs.tf#L44) | HA VPN gateway resource IDs keyed by peer identifier. |  |
| [vpn_gateway_interfaces](outputs.tf#L51) | HA VPN gateway interface IP configs keyed by peer. |  |
| [vpn_gateway_self_links](outputs.tf#L58) | HA VPN gateway self-links keyed by peer identifier. |  |
<!-- END TFDOC -->
