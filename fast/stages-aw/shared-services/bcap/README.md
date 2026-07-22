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

# Optional Shared Services Template — Boundary Access Point (BCAP) & Interconnect Routing

This reference template provisions the Google Cloud infrastructure required to establish a 99.99% highly available connection to a Boundary Access Point (BCAP) or external boundary provider using Google Cloud Partner Interconnect.

> [!NOTE]
> This is an **optional reference template**. It is fully decoupled from the core landing zone (Stages 0–5) and can be adapted or omitted based on your external network connectivity requirements.

The BCAP architecture follows the **99.99% Availability for Partner Interconnect** topology as recommended in the [GCP Documentation](https://cloud.google.com/network-connectivity/docs/interconnect/tutorials/partner-creating-9999-availability).

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

* Review the [GCP Documentation](https://cloud.google.com/network-connectivity/docs/interconnect/tutorials/partner-creating-9999-availability). 
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
| [attachment_configs](variables.tf#L1) | Configuration map for the four Partner VLAN attachments required for 99.99% availability. The region for each attachment is derived from its associated `router_key`. | <code title="map&#40;object&#40;&#123;&#10;  name                     &#61; string&#10;  description              &#61; optional&#40;string, &#34;BCAP VLAN Attachment&#34;&#41;&#10;  router_key               &#61; string&#10;  edge_availability_domain &#61; string&#10;  mtu                      &#61; optional&#40;number, 1440&#41;&#10;  vlan_id                  &#61; optional&#40;number, null&#41;&#10;&#125;&#41;&#41;">map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> | ✓ |  |
| [hub_project_id](variables.tf#L29) | The GCP project ID where BCAP resources (VPC, Subnets, Routers, Attachments) will be deployed. | <code>string</code> | ✓ |  |
| [network_name](variables.tf#L34) | VPC network name. | <code>string</code> | ✓ |  |
| [region1](variables.tf#L39) | The primary GCP region for BCAP deployment (hosts router1 and their associated VLAN attachments). | <code>string</code> | ✓ |  |
| [region2](variables.tf#L44) | The secondary GCP region for BCAP deployment (hosts router2 and their associated VLAN attachments). | <code>string</code> | ✓ |  |
| [router_configs](variables.tf#L49) | Configuration map for the two Cloud Routers. Names are user-defined; regions are derived from `region1` (for router1) and `region2` (for router2). Keys must be 'router1' and 'router2'. | <code title="map&#40;object&#40;&#123;&#10;  name        &#61; string&#10;  description &#61; optional&#40;string, &#34;BCAP Cloud Router&#34;&#41;&#10;&#125;&#41;&#41;">map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> | ✓ |  |
| [subnetwork_name](variables.tf#L67) | VPC subnetwork name. | <code>string</code> | ✓ |  |
| [subnetwork_region](variables.tf#L72) | VPC subnetwork region. | <code>string</code> | ✓ |  |
| [router_google_asn](variables.tf#L61) | Autonomous System Number (ASN) for the Google side of the BGP sessions on Cloud Routers (should be 16550 for Partner Interconnect). | <code>number</code> |  | <code>16550</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [attachment_names](outputs.tf#L1) | Names of the created VLAN attachments. |  |
| [cloud_routers](outputs.tf#L8) | Details of the created Cloud Routers (map keyed by 'router1', 'router2'). |  |
| [pairing_keys](outputs.tf#L13) | Pairing keys for each VLAN attachment. Provide these to the BCAP/DISA team. | ✓ |
| [vlan_attachments](outputs.tf#L21) | Details of the created VLAN attachments. |  |
<!-- END TFDOC -->
