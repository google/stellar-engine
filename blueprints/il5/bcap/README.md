# Boundary Cloud Access Point blueprint

This blueprint provisions Google Cloud Partner Interconnect infrastructure for a redundant Boundary Cloud Access Point connection to providers such as DISA, implementing the [99.99% availability Partner Interconnect topology](https://cloud.google.com/network-connectivity/docs/interconnect/tutorials/partner-creating-9999-availability) described in the Google Cloud BCAP Customer Guide. Reach the Google BCAP team at `trusted-networks@gss.google` for onboarding coordination.

<!-- BEGIN TOC -->
- [1 Architecture](#1-architecture)
- [2 Prerequisites](#2-prerequisites)
- [3 Deployment steps](#3-deployment-steps)
  - [Post-apply activation](#post-apply-activation)
- [4 Deployment verification](#4-deployment-verification)
  - [VPC and subnets](#vpc-and-subnets)
  - [Routers and VLAN attachments](#routers-and-vlan-attachments)
- [5 Compliance scope](#5-compliance-scope)
- [Variables](#variables)
- [Outputs](#outputs)
<!-- END TOC -->

## 1 Architecture

This blueprint provisions four core networking components inside `hub_project_id`:

- A custom-mode VPC network named by `network_name` with `auto_create_subnetworks = false`.
- Two regional `/25` subnets defined in `subnet_configs` across `region1` and `region2`, programmatically split from the DoD `/24` `dod_base_cidr_block` with Private Google Access and VPC Flow Logs enabled by default.
- Two regional Cloud Routers defined in `router_configs` across `region1` and `region2` using ASN `16550` (`router_google_asn`) for Partner Interconnect and advertising both `/25` DoD subnets by default.
- Four `PARTNER` VLAN attachments defined in `attachment_configs` with MTU `1440` and regions derived from each linked `router_key`.
- Google and the partner assign the 802.1Q VLAN tag on `PARTNER` attachments, so `vlan_id` must remain unset.
- For Layer 2 Partner Interconnect connections requiring explicit BGP peering subnets, set paired `candidate_cloud_router_ip_address` and `candidate_customer_router_ip_address` IPv4 host CIDRs in non-overlapping `/29` or `/30` non-private subnets, using `/29` only within `169.254.0.0/16` and excluding network and broadcast addresses.
- Leave both candidate BGP IP attributes unset for Layer 3 Partner Interconnect or automatic IP allocation.

## 2 Prerequisites

- Review the Google Cloud BCAP Customer Guide.
- Obtain your assigned `/24` CIDR block (`dod_base_cidr_block`) from the Department of Defense Network Information Center.
- Complete BCAP onboarding Phases 1 and 2, including Cloud Permission to Connect approvals and official DoD NIC IP allocation.
- Obtain BGP MD5 authentication keys from the mission owner to configure on the Cloud Router BGP sessions after partner activation.
- If setting custom candidate BGP IPs on Layer 2 attachments, enable `networkconnectivity.googleapis.com` in `hub_project_id` and grant `networkconnectivity.internalRanges.create` such as via `roles/compute.networkAdmin`.

## 3 Deployment steps

1. Copy `terraform.tfvars.sample` to `terraform.tfvars` and populate values for your environment.
2. Initialize and apply the Terraform configuration:

```bash
terraform init
terraform plan
terraform apply
```

### Post-apply activation

1. Retrieve the VLAN attachment pairing keys via `terraform output -json pairing_keys` or from each attachment detail page in the Google Cloud console.
2. Deliver the pairing keys to DISA and the Google BCAP team to activate the Partner Interconnect connections.
3. Once the attachments are active, configure BGP peering on both Cloud Routers with the partner ASN, such as `64519` for DISA, and the mission-owner MD5 authentication keys.

## 4 Deployment verification

### VPC and subnets

1. Open [VPC networks](https://console.cloud.google.com/networking/networks/list) in `hub_project_id` and select the BCAP VPC network.
2. Open the Subnets tab and confirm that two `/25` subnets split from `dod_base_cidr_block` exist in `region1` and `region2`.

### Routers and VLAN attachments

1. Open [Cloud Routers](https://console.cloud.google.com/hybrid/routers/list) in `hub_project_id`.
2. Confirm that two BCAP Cloud Routers exist in `region1` and `region2`, each with two attached Partner Interconnect VLAN attachments.

## 5 Compliance scope

- Deploy this blueprint inside an IL4 or IL5 Assured Workloads folder within your Google Cloud organization.
<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [attachment_configs](variables.tf#L15) | Configuration map for the four Partner VLAN attachments required for 99.99% availability. The region for each attachment is derived from its associated `router_key`. For Layer 2 Partner Interconnect, optionally specify paired `candidate_cloud_router_ip_address` and `candidate_customer_router_ip_address` IPv4 CIDRs. | <code>map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> | ✓ |  |
| [dod_base_cidr_block](variables.tf#L184) | The base /24 CIDR block assigned by the Department of Defense Network Information Center (DoD NIC), which will be programmatically split into two /25 subnets. | <code>string</code> | ✓ |  |
| [hub_project_id](variables.tf#L193) | The GCP project ID where BCAP resources (VPC, Subnets, Routers, Attachments) will be deployed. | <code>string</code> | ✓ |  |
| [network_name](variables.tf#L198) | The name for the Virtual Private Cloud (VPC) network to be created. | <code>string</code> | ✓ |  |
| [region1](variables.tf#L203) | The primary GCP region for BCAP deployment (hosts router1, subnet1, and their associated VLAN attachments). | <code>string</code> | ✓ |  |
| [region2](variables.tf#L208) | The secondary GCP region for BCAP deployment (hosts router2, subnet2, and their associated VLAN attachments). | <code>string</code> | ✓ |  |
| [router_configs](variables.tf#L213) | Configuration map for the two Cloud Routers. Names are user-defined; regions are derived from `region1` (for router1) and `region2` (for router2). Keys must be 'router1' and 'router2'. | <code>map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> | ✓ |  |
| [subnet_configs](variables.tf#L231) | Configuration map for the two DoD subnets. Names are user-defined; IP CIDRs are derived from 'dod_base_cidr_block'; regions are derived from `region1` (for subnet1) and `region2` (for subnet2). Keys must be 'subnet1' and 'subnet2'. | <code>map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> | ✓ |  |
| [router_google_asn](variables.tf#L225) | Autonomous System Number (ASN) for the Google side of the BGP sessions on Cloud Routers (should be 16550 for Partner Interconnect). | <code>number</code> |  | <code>16550</code> |
| [subnet_enable_flow_logs](variables.tf#L243) | Enable VPC flow logs for the created DoD subnets. | <code>bool</code> |  | <code>true</code> |
| [subnet_private_ip_google_access](variables.tf#L249) | Enable Private Google Access for the created DoD subnets. | <code>bool</code> |  | <code>true</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [attachment_names](outputs.tf#L15) | Names of the created VLAN attachments. |  |
| [bcap_subnets](outputs.tf#L22) | Details of the created BCAP Subnets for DoD IP space (map keyed by 'subnet1', 'subnet2'). Includes calculated CIDRs. |  |
| [cloud_routers](outputs.tf#L27) | Details of the created Cloud Routers (map keyed by 'router1', 'router2'). |  |
| [dod_split_cidr_blocks](outputs.tf#L32) | The calculated /25 CIDR blocks for the two DoD subnets. |  |
| [pairing_keys](outputs.tf#L37) | Pairing keys for each VLAN attachment. Provide these to the BCAP/DISA team. | ✓ |
| [vlan_attachments](outputs.tf#L45) | Details of the created VLAN attachments. | ✓ |
| [vpc_network](outputs.tf#L51) | Details of the created VPC Network. |  |
<!-- END TFDOC -->
