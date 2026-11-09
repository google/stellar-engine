# Boundary Cloud Access Point (BCAP)

This Terraform blueprint provisions the necessary Google Cloud infrastructure to establish a highly available connection to a Boundary Cloud Access Point (BCAP) provider, such as DISA, using Google Cloud Partner Interconnect.

The BCAP architecture follows the **99.99% Availability for Partner Interconnect** topology as recommended in the [GCP Documentation](https://cloud.google.com/network-connectivity/docs/interconnect/tutorials/partner-creating-9999-availability) and referenced in the BCAP Customer Guide for GCP.

Google BCAP Contact: <trusted-networks@gss.google>

<!-- BEGIN TOC -->
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Deployment](#deployment)
- [Disclaimer](#disclaimer)
- [Variables](#variables)
- [Outputs](#outputs)
<!-- END TOC -->

## Architecture

This blueprint creates the following resources:

1.  **VPC Network**
    * A custom-mode VPC (`auto_create_subnetworks = false`), named using `network_name`.
2.  **Two VPC Subnets**
    * Names are defined via `subnet_configs`.
    * Their regions are automatically assigned to `region1` (for `subnet1`) and `region2` (for `subnet2`).
    * The IP CIDRs are calculated and split into two /25s from the /24 `dod_base_cidr_block` variable.
    * Private Google Access and Flow Logs are enabled by default.
3.  **Two Cloud Routers**
    * Names are defined via `router_configs` (`router1` is placed in `region1` and `router2` in `region2`).
    * Each router is attached to the created VPC, uses the `router_google_asn` (16550 for Partner Interconnect), and by default, advertises **both** calculated DoD /25 subnets.
4.  **Four VLAN Attachments**
    * Defined via the `attachment_configs` variable and configured as `PARTNER` type.
    * The region for each attachment is derived from the region of the router it's linked to via `router_key`.
    * MTU is set to 1440 by default as recommended for BCAP.

## Prerequisites

* Review the BCAP Customer Guide for GCP.
* The **base /24 CIDR block** assigned by the Department of Defense Network Information Center (DoD NIC) (`dod_base_cidr_block`).
* Completion of BCAP onboarding steps (Phase 1 & 2 from the guide), including obtaining necessary approvals (e.g., Cloud Permission to Connect (CPTC)) and the official IP space from DoD NIC.
* MD5 Authentication Keys (provided by customer/mission owner) to be configured on the Cloud Router BGP sessions *after* the attachments are provisioned and activated by the partner.

## Deployment

1.  Create a `terraform.tfvars` file based on the example provided (`terraform.tfvars.sample`).
2.  Populate the `terraform.tfvars` file with values specific to your environment.
3.  Run `terraform init`.
4.  Run `terraform plan`.
5.  Run `terraform apply`.

**Post-Apply Steps:**

1.  Retrieve the `pairing_keys` from the Terraform output (`terraform output -json pairing_keys`) or from the Google Cloud web console within each VLAN Attachment's detail screen.
2.  Provide these keys to the BCAP provider (DISA/Google BCAP Team) to activate the connections.
3.  Once attachments are active, configure BGP peering on the Cloud Routers, including Peer ASN (e.g., 64519 for DISA) and MD5 authentication using the keys provided by the mission owner.

**Deployment Verification**

***VPC and Subnetworks***

1. Navigate to the [VPC Network](https://console.cloud.google.com/networking/networks/list) within your hub network project.
2. Click on the BCAP VPC name.
3. Click on the Subnets tab.
4. Confirm that the (x1) VPC and (x2) Subnets exist and that the DISA provided /24 `dod_base_cidr_block` is split into two /25 `dod_split_cidr_blocks` for each subnet.

***Cloud Routers and VLAN Attachments***

1. Navigate to the [Cloud Router](https://console.cloud.google.com/hybrid/routers/list) resource within your hub network project.
2. Confirm that (x2) BCAP Cloud Routers exist with their specified VPC, region, and that (x2) VLAN Attachments exist per Cloud router.

## Disclaimer
- The present GCP Terraform Blueprint in this project is set up and intended to be implemented in an Impact Level 4 (IL4) and Impact Level 5 (IL5) environments using the Assured Workloads within the Google Cloud Platform (GCP) organization.
<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [attachment_configs](variables.tf#L15) | Configuration map for the four Partner VLAN attachments required for 99.99% availability. The region for each attachment is derived from its associated `router_key`. | <code>map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> | ✓ |  |
| [dod_base_cidr_block](variables.tf#L49) | The base /24 CIDR block assigned by the Department of Defense Network Information Center (DoD NIC), which will be programmatically split into two /25 subnets. | <code>string</code> | ✓ |  |
| [hub_project_id](variables.tf#L58) | The GCP project ID where BCAP resources (VPC, Subnets, Routers, Attachments) will be deployed. | <code>string</code> | ✓ |  |
| [network_name](variables.tf#L63) | The name for the Virtual Private Cloud (VPC) network to be created. | <code>string</code> | ✓ |  |
| [region1](variables.tf#L68) | The primary GCP region for BCAP deployment (hosts router1, subnet1, and their associated VLAN attachments). | <code>string</code> | ✓ |  |
| [region2](variables.tf#L73) | The secondary GCP region for BCAP deployment (hosts router2, subnet2, and their associated VLAN attachments). | <code>string</code> | ✓ |  |
| [router_configs](variables.tf#L78) | Configuration map for the two Cloud Routers. Names are user-defined; regions are derived from `region1` (for router1) and `region2` (for router2). Keys must be 'router1' and 'router2'. | <code>map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> | ✓ |  |
| [subnet_configs](variables.tf#L96) | Configuration map for the two DoD subnets. Names are user-defined; IP CIDRs are derived from 'dod_base_cidr_block'; regions are derived from `region1` (for subnet1) and `region2` (for subnet2). Keys must be 'subnet1' and 'subnet2'. | <code>map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> | ✓ |  |
| [router_google_asn](variables.tf#L90) | Autonomous System Number (ASN) for the Google side of the BGP sessions on Cloud Routers (should be 16550 for Partner Interconnect). | <code>number</code> |  | <code>16550</code> |
| [subnet_enable_flow_logs](variables.tf#L108) | Enable VPC flow logs for the created DoD subnets. | <code>bool</code> |  | <code>true</code> |
| [subnet_private_ip_google_access](variables.tf#L114) | Enable Private Google Access for the created DoD subnets. | <code>bool</code> |  | <code>true</code> |

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
