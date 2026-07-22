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

# VPC Peering Project Blueprint
This blueprint provides a self-contained solution for creating two new Google Cloud VPC networks and establishing a peering connection between them. It is intended for customers who want to develop their own network infrastructure without the full Stellar Engine deployment.

<!-- BEGIN TOC -->
- [VPC Peering Project Blueprint](#vpc-peering-project-blueprint)
- [Introduction](#introduction)
- [Disclaimer](#disclaimer)
- [Prerequisites](#prerequisites)
- [Deployment Steps](#deployment-steps)
- [Verification](#verification)
- [Important Notes](#important-notes)
- [Variables](#variables)
- [Outputs](#outputs)
<!-- END TOC -->

## Introduction
VPC Network Peering allows you to connect two Virtual Private Cloud (VPC) networks so that workloads in each network can communicate with each other using internal IP addresses. This enables you to share services, data, and applications across different VPC networks, whether they are in the same or different Google Cloud projects and organizations, without using external IP addresses or VPNs.

This blueprint offers a complete solution to demonstrate VPC peering by provisioning two distinct VPC networks and configuring their peering connection.

## Disclaimer
- The present GCP Terraform Module in this project is set up and intended to be implemented in either a FedRAMP-High or IL5 (Impact Level 5) environment using the Assured Workloads within the Google Cloud Platform (GCP) organization.
- Assured Workloads in both environments ensures that sensitive data and workloads in GCP adhere to the rigorous security standards mandated by the DoD, making it suitable for government agencies.

## Prerequisites
Before deploying this blueprint, ensure the following are in place:

1.  **Google Cloud Projects:**
    * You will need two Google Cloud projects where the VPCs will be created. These can be the same project (e.g., if `local_vpc_project_id` and `peer_vpc_project_id_to_create` are the same).
    * `var.main_project_id` should typically be one of these two project IDs, as it's where the peering connection resource will be managed.
2.  **Permissions:** The service account or user deploying this blueprint must have:
    * `roles/owner` or sufficient granular permissions (e.g., `compute.admin`, `serviceusage.serviceUsageAdmin`, `resourcemanager.projectIamAdmin`) in **both** `local_vpc_project_id` and `peer_vpc_project_id_to_create`. This is because the blueprint will create VPCs in both projects.
    * The `Compute Engine API` (`compute.googleapis.com`) enabled in both `local_vpc_project_id` and `peer_vpc_project_id_to_create`. This blueprint attempts to enable it automatically.

## Deployment Steps
1.  **Configure Variables:**
    * Copy the sample variables file:
        ```bash
        cp terraform.tfvars.sample terraform.tfvars
        ```
    * Open `terraform.tfvars` and update the placeholder values (`xxxx-xxxx-main-0`, `my-local-vpc`, `my-peer-vpc`, etc.) with your actual project IDs, VPC names, and CIDR ranges for both the local and peer VPCs.

2.  **Initialize Terraform:**
    ```bash
    terraform init
    ```

3.  **Review Plan:**
    ```bash
    terraform plan
    ```
    Carefully review the proposed infrastructure changes (e.g., creation of two VPCs and one peering connection) before applying.

4.  **Apply Changes:**
    ```bash
    terraform apply
    ```
    Type `yes` when prompted to confirm the deployment.

5.  **Destroy Infrastructure (Optional):**
    If you wish to remove the deployed VPCs and peering connection:
    ```bash
    terraform destroy
    ```
    Type `yes` when prompted to confirm.

## Verification
To verify a successful deployment:

1.  **Google Cloud Console:**
    * Navigate to **VPC network** > **VPC networks** in both your `local_vpc_project_id` and `peer_vpc_project_id_to_create`.
    * Confirm that `var.local_vpc_name` and `var.peer_vpc_name_to_create` VPCs (with their subnets) have been created.
    * In the Console, navigate to **VPC network** > **VPC Network Peering** (in `var.main_project_id`).
    * Verify that a peering connection exists and is in an `ACTIVE` state, connecting your `local_vpc_name` and `peer_vpc_name_to_create`.

2.  **`gcloud` CLI:**
    * **List Peering Connections:**
        ```bash
        gcloud compute network-peering list --project=<MAIN_PROJECT_ID>
        ```
    * **Describe a VPC Network:**
        ```bash
        gcloud compute networks describe <VPC_NAME> --project=<PROJECT_ID>
        ```
        (Do this for both `local_vpc_name` and `peer_vpc_name_to_create` in their respective projects).
    * **Test Connectivity (Optional, requires VMs):** Deploy simple Compute Engine VMs in subnets within each peered VPC, and try to ping/connect them via their internal IP addresses.

## Important Notes
-   This blueprint strictly **creates two VPC networks and a peering connection between them.** It is a standalone deployment and does not consume pre-existing VPCs for its core function.
-   **Do NOT use this blueprint within an environment provisioned by Stellar Engine** where networking (including VPCs and peering) is already managed by Stage 2 of the foundational deployment. Using this blueprint in such an environment will cause conflicts.
-   VPC Peering requires non-overlapping IP CIDR ranges between the peered networks. Ensure your `local_subnetwork_cidr_*` and `peer_subnetwork_cidr_*` ranges do not overlap.
-   VPC Peering connections are **global** resources, but they connect regional VPC networks. Ensure `var.gcp_region` is consistent for both VPCs.

<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [main_project_id](variables.tf#L1) | The Google Cloud Project ID where the peering connection will be managed (should be one of the VPC projects). | <code>string</code> | ✓ |  |
| [gcp_region](variables.tf#L6) | The Google Cloud region where both VPCs and their subnets will be deployed. | <code>string</code> | ✓ |  |
| [local_vpc_name](variables.tf#L11) | The name of the first VPC network to be created by this blueprint. | <code>string</code> | ✓ |  |
| [local_vpc_project_id](variables.tf#L16) | The Google Cloud Project ID where the first VPC network will be created. | <code>string</code> | ✓ |  |
| [local_subnetwork_prefix_name](variables.tf#L21) | The prefix name for subnets within the first VPC network. | <code>string</code> |  | <code>&#34;local-subnet&#34;</code> |
| [local_subnetwork_cidr_a](variables.tf#L27) | The primary IP CIDR range for the first subnet in the local VPC (e.g., &#39;10.100.0.0&#47;24&#39;). | <code>string</code> | ✓ |  |
| [local_subnetwork_cidr_b](variables.tf#L32) | The primary IP CIDR range for the second subnet in the local VPC (e.g., &#39;10.100.1.0&#47;24&#39;). | <code>string</code> | ✓ |  |
| [local_subnetwork_cidr_c](variables.tf#L37) | The primary IP CIDR range for the third subnet in the local VPC (e.g., &#39;10.100.2.0&#47;24&#39;). | <code>string</code> | ✓ |  |
| [local_secondary_ip_ranges_cidr_a](variables.tf#L42) | The secondary IP CIDR range &#39;a&#39; for a subnet in the local VPC (e.g., &#39;192.168.0.0&#47;24&#39;). | <code>string</code> | ✓ |  |
| [local_secondary_ip_ranges_cidr_b](variables.tf#L47) | The secondary IP CIDR range &#39;b&#39; for a subnet in the local VPC (e.g., &#39;192.168.1.0&#47;24&#39;). | <code>string</code> | ✓ |  |
| [peer_vpc_name_to_create](variables.tf#L52) | The name of the second VPC network to be created by this blueprint (this will be the &#39;peer&#39; side). | <code>string</code> | ✓ |  |
| [peer_vpc_project_id_to_create](variables.tf#L57) | The Google Cloud Project ID where the second VPC network will be created (this will be the &#39;peer&#39; side). | <code>string</code> | ✓ |  |
| [peer_subnetwork_prefix_name](variables.tf#L62) | The prefix name for subnets within the second VPC network (the &#39;peer&#39; side). | <code>string</code> |  | <code>&#34;peer-subnet&#34;</code> |
| [peer_subnetwork_cidr_a](variables.tf#L68) | The primary IP CIDR range for the first subnet in the peer VPC (e.g., &#39;10.200.0.0&#47;24&#39;). | <code>string</code> | ✓ |  |
| [peer_subnetwork_cidr_b](variables.tf#L73) | The primary IP CIDR range for the second subnet in the peer VPC (e.g., &#39;10.200.1.0&#47;24&#39;). | <code>string</code> | ✓ |  |
| [peer_subnetwork_cidr_c](variables.tf#L78) | The primary IP CIDR range for the third subnet in the peer VPC (e.g., &#39;10.200.2.0&#47;24&#39;). | <code>string</code> | ✓ |  |
| [peer_secondary_ip_ranges_cidr_a](variables.tf#L83) | The secondary IP CIDR range &#39;a&#39; for a subnet in the peer VPC (e.g., &#39;192.168.2.0&#47;24&#39;). | <code>string</code> | ✓ |  |
| [peer_secondary_ip_ranges_cidr_b](variables.tf#L88) | The secondary IP CIDR range &#39;b&#39; for a subnet in the peer VPC (e.g., &#39;192.168.3.0&#47;24&#39;). | <code>string</code> | ✓ |  |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [local_network_peering](outputs.tf#L16) | The peering resource for the local VPC side of the connection. |  |
| [peer_network_peering](outputs.tf#L21) | The peering resource for the peer VPC side of the connection. |  |
| [local_vpc_network](outputs.tf#L26) | The network resource object for the local VPC created by this blueprint. |  |
| [local_vpc_network_self_link](outputs.tf#L31) | The self-link for the local VPC created by this blueprint. |  |
| [local_vpc_subnet_ids](outputs.tf#L36) | A map of subnet IDs keyed by name for the local VPC. |  |
| [local_vpc_subnet_ips](outputs.tf#L41) | A map of subnet address ranges keyed by name for the local VPC. |  |
| [local_vpc_subnet_self_links](outputs.tf#L46) | A map of subnet self links keyed by name for the local VPC. |  |
| [local_vpc_subnet_regions](outputs.tf#L51) | A map of subnet regions keyed by name for the local VPC. |  |
| [local_vpc_subnets](outputs.tf#L56) | List of subnet resources for the local VPC. |  |
| [local_vpc_subnet_secondary_ranges](outputs.tf#L61) | Map of subnet secondary ranges keyed by name for the local VPC. |  |
| [local_vpc_subnet_ipv6_external_prefixes](outputs.tf#L66) | Map of subnet external IPv6 prefixes keyed by name for the local VPC. |  |
| [local_vpc_network_attachment_ids](outputs.tf#L71) | IDs of network attachments for the local VPC. |  |
| [peer_vpc_network](outputs.tf#L76) | The network resource object for the peer VPC created by this blueprint. |  |
| [peer_vpc_network_self_link](outputs.tf#L81) | The self-link for the peer VPC created by this blueprint. |  |
| [peer_vpc_subnet_ids](outputs.tf#L86) | A map of subnet IDs keyed by name for the peer VPC. |  |
| [peer_vpc_subnet_ips](outputs.tf#L91) | A map of subnet address ranges keyed by name for the peer VPC. |  |
| [peer_vpc_subnet_self_links](outputs.tf#L96) | A map of subnet self links keyed by name for the peer VPC. |  |
| [peer_vpc_subnet_regions](outputs.tf#L101) | A map of subnet regions keyed by name for the peer VPC. |  |
| [peer_vpc_subnets](outputs.tf#L106) | List of subnet resources for the peer VPC. |  |
| [peer_vpc_subnet_secondary_ranges](outputs.tf#L111) | Map of subnet secondary ranges keyed by name for the peer VPC. |  |
| [peer_vpc_subnet_ipv6_external_prefixes](outputs.tf#L116) | Map of subnet external IPv6 prefixes keyed by name for the peer VPC. |  |
| [peer_vpc_network_attachment_ids](outputs.tf#L121) | IDs of network attachments for the peer VPC. |  |
<!-- END TOC -->

