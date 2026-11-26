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

This blueprint provisions four core networking components inside `hub_project_id`, supporting either a standard 2-region 4-attachment topology or a 4-region 8-attachment multi-region topology when `additional_regions` defines two additional region slots:

- A custom-mode VPC network named by `network_name` with `auto_create_subnetworks = false` and `GLOBAL` routing mode when `create_vpc` is `true`, or a lookup of an existing VPC network in `hub_project_id` when `create_vpc` is `false`. An existing VPC reused with `create_vpc = false` should use `GLOBAL` dynamic routing mode so Cloud Router BGP routes propagate across all BCAP regions.
- Regional subnets defined in `subnet_configs` across `region1`, `region2`, and optional `additional_regions`, programmatically split from the DoD `/24` `dod_base_cidr_block` into two `/25` subnets or four `/26` subnets with Private Google Access and VPC Flow Logs at `flow_sampling = 1.0` enabled by default.
- Regional Cloud Routers defined in `router_configs` across each configured region using ASN `16550` (`router_google_asn`) for Partner Interconnect and advertising all split DoD subnets by default.
- Four or eight `PARTNER` VLAN attachments defined in `attachment_configs` with MTU `1440`, two availability domains per router, and regions derived from each linked `router_key`.
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

1. Copy `terraform.tfvars.sample` to `terraform.tfvars` and populate values for your environment. Set `create_vpc = false` when attaching BCAP resources to an existing Stage 2 VPC, and populate `additional_regions` with two additional region entries for a 4-region 8-attachment deployment.
2. Initialize and apply the Terraform configuration:

```bash
terraform init
terraform plan
terraform apply
```

### Post-apply activation

1. Retrieve the VLAN attachment pairing keys via `terraform output -json pairing_keys` or from each attachment detail page in the Google Cloud console.
2. Deliver the pairing keys to DISA and the Google BCAP team to activate the Partner Interconnect connections.
3. Once the attachments are active, configure BGP peering on each Cloud Router with the partner ASN, such as `64519` for DISA, and the mission-owner MD5 authentication keys.

## 4 Deployment verification

### VPC and subnets

1. Open [VPC networks](https://console.cloud.google.com/networking/networks/list) in `hub_project_id` and select the BCAP VPC network.
2. Open the Subnets tab and confirm that the split `/25` or `/26` subnets from `dod_base_cidr_block` exist in every configured region.

### Routers and VLAN attachments

1. Open [Cloud Routers](https://console.cloud.google.com/hybrid/routers/list) in `hub_project_id`.
2. Confirm that one BCAP Cloud Router exists in each configured region, each with two attached Partner Interconnect VLAN attachments.

## 5 Compliance scope

- Deploy this blueprint inside an IL4 or IL5 Assured Workloads folder within your Google Cloud organization.
<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [attachment_configs](variables.tf#L50) | Configuration map for the Partner VLAN attachments required for 99.99% availability (4 for 2-region topology or 8 for 4-region topology). The region for each attachment is derived from its associated `router_key`. For Layer 2 Partner Interconnect, optionally specify paired `candidate_cloud_router_ip_address` and `candidate_customer_router_ip_address` IPv4 CIDRs. | <code>map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> | ✓ |  |
| [dod_base_cidr_block](variables.tf#L246) | The base IPv4 /24 CIDR block assigned by the Department of Defense Network Information Center (DoD NIC), programmatically split into two /25 subnets (2-region) or four /26 subnets (4-region). | <code>string</code> | ✓ |  |
| [hub_project_id](variables.tf#L259) | The GCP project ID where BCAP resources (VPC, Subnets, Routers, Attachments) will be deployed. | <code>string</code> | ✓ |  |
| [network_name](variables.tf#L264) | The name for the Virtual Private Cloud (VPC) network to create when create_vpc is true, or look up when create_vpc is false. | <code>string</code> | ✓ |  |
| [region1](variables.tf#L269) | The primary GCP region for BCAP deployment (hosts router1, subnet1, and their associated VLAN attachments). | <code>string</code> | ✓ |  |
| [region2](variables.tf#L278) | The secondary GCP region for BCAP deployment (hosts router2, subnet2, and their associated VLAN attachments). | <code>string</code> | ✓ |  |
| [router_configs](variables.tf#L287) | Configuration map for the Cloud Routers (2 for 2-region topology or 4 for 4-region topology). Keys must include 'router1' and 'router2'; additional routers match additional_regions keys or set region. | <code>map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> | ✓ |  |
| [subnet_configs](variables.tf#L342) | Configuration map for the DoD subnets (2 for 2-region topology or 4 for 4-region topology). IP CIDRs are split from dod_base_cidr_block. Keys must include 'subnet1' and 'subnet2'; additional subnets match additional_regions keys or set region. | <code>map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> | ✓ |  |
| [additional_regions](variables.tf#L15) | Optional map of 2 additional region slots (for example, { region3 = 'us-west1', region4 = 'us-west2' }) to expand from a 2-region 4-attachment topology to a 4-region 8-attachment topology. | <code>map&#40;string&#41;</code> |  | <code>&#123;&#125;</code> |
| [create_vpc](variables.tf#L239) | Create a new VPC network named by network_name. Set to false to attach BCAP subnets, routers, and VLAN attachments to an existing VPC network in hub_project_id. | <code>bool</code> |  | <code>true</code> |
| [router_google_asn](variables.tf#L336) | Autonomous System Number (ASN) for the Google side of the BGP sessions on Cloud Routers (should be 16550 for Partner Interconnect). | <code>number</code> |  | <code>16550</code> |
| [subnet_enable_flow_logs](variables.tf#L391) | Enable VPC flow logs for the created DoD subnets. | <code>bool</code> |  | <code>true</code> |
| [subnet_private_ip_google_access](variables.tf#L397) | Enable Private Google Access for the created DoD subnets. | <code>bool</code> |  | <code>true</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [attachment_names](outputs.tf#L15) | Names of the created VLAN attachments. |  |
| [bcap_subnets](outputs.tf#L23) | Details of the created BCAP subnets for DoD IP space keyed by subnet_configs keys. Includes calculated CIDRs. |  |
| [cloud_routers](outputs.tf#L28) | Details of the created Cloud Routers keyed by router_configs keys. |  |
| [dod_split_cidr_blocks](outputs.tf#L33) | The calculated /25 (2-region) or /26 (4-region) CIDR blocks for the DoD subnets. |  |
| [pairing_keys](outputs.tf#L38) | Pairing keys for each VLAN attachment. Provide these to the BCAP/DISA team. | ✓ |
| [vlan_attachments](outputs.tf#L47) | Details of the created VLAN attachments. | ✓ |
| [vpc_network](outputs.tf#L53) | Details of the created VPC network, or null when create_vpc is false. |  |
| [vpc_network_id](outputs.tf#L58) | Resource ID of the created or existing BCAP VPC network. |  |
| [vpc_network_self_link](outputs.tf#L63) | Self link of the created or existing BCAP VPC network. |  |
<!-- END TFDOC -->
