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

# Network Connectivity Center Blueprint
This blueprint demonstrates how to create a Google Cloud Network Connectivity Center (NCC) Hub and connect existing VPC networks as spokes, supporting various network topologies (MESH/STAR) within a multi-project GCP environment.

<!-- BEGIN TOC -->
- [Network Connectivity Center Blueprint](#network-connectivity-center-blueprint)
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
Network Connectivity Center is an orchestration framework that simplifies network connectivity among spoke resources that are connected to a central management resource called a hub. It enables you to manage connectivity between multiple VPC networks, on-premise networks, or other cloud provider networks.

This blueprint specifically focuses on establishing hub-and-spoke connectivity with existing Google Cloud VPC networks.

## Disclaimer
- The present GCP Terraform Module in this project is set up and intended to be implemented in either a FedRAMP-High or IL5 (Impact Level 5) environment using Assured Workloads within the Google Cloud Platform (GCP) organization.
- Assured Workloads in both environments ensures that sensitive data and workloads in GCP adhere to the rigorous security standards mandated by the DoD, making it suitable for government agencies.

## Prerequisites
Before deploying this blueprint, ensure the following are in place:

1.  **Google Cloud Projects:**
    * A **main project** (`var.main_project_id`) where the NCC Hub will be created.
    * **Network projects** (where your VPCs reside) from which you intend to attach spokes. These can include your `main_project_id` or other distinct projects.
2.  **Existing VPC Networks:** The VPC networks intended to be attached as spokes must already exist. This blueprint consumes existing VPCs; it does not create them. You will need their full self-links (e.g., `projects/<PROJECT_ID>/global/networks/<VPC_NETWORK_NAME>`).
3.  **Permissions:** The service account or user deploying this blueprint must have:
    * `roles/owner` or sufficient granular permissions (e.g., `networkconnectivity.admin`, `compute.networkAdmin`, `serviceusage.serviceUsageAdmin`, `resourcemanager.projectIamAdmin`) in the `main_project_id`.
    * `roles/networkconnectivity.admin` (or `roles/owner`) in any **spoke project** where the VPC networks reside, as NCC Spoke resources are created within the VPC's project.
    * The `Network Connectivity Center API` (`networkconnectivity.googleapis.com`) enabled in the `main_project_id`. This blueprint attempts to enable it automatically.

## Deployment Steps
1.  **Configure Variables:**
    * Copy the sample variables file:
        ```bash
        cp terraform.tfvars.sample terraform.tfvars
        ```
    * Open `terraform.tfvars` and update the placeholder values (`xxxx-xxxx-main-0`, `my-network-project-id-1`, etc.) with your actual project IDs, NCC hub name, and VPC network self-links.

2.  **Initialize Terraform:**
    ```bash
    terraform init
    ```

3.  **Review Plan:**
    ```bash
    terraform plan
    ```
    Carefully review the proposed infrastructure changes before applying.

4.  **Apply Changes:**
    ```bash
    terraform apply
    ```
    Type `yes` when prompted to confirm the deployment.

5.  **Destroy Infrastructure (Optional):**
    If you wish to remove the deployed NCC Hub and Spokes:
    ```bash
    terraform destroy
    ```
    Type `yes` when prompted to confirm.

## Verification
To verify a successful deployment:

1.  **Google Cloud Console:**
    * Navigate to **Network Connectivity** > **Network Connectivity Center** in your `main_project_id`.
    * Confirm that a new **Hub** with the specified `ncc_hub_name` has been created.
    * Click on the Hub and navigate to the **Spokes** tab.
    * Verify that all specified VPC networks from your `spokes` variable are listed as attached spokes.

2.  **`gcloud` CLI:**
    * **Describe the Hub:**
        ```bash
        gcloud network-connectivity hubs describe <NCC_HUB_NAME> --project=<MAIN_PROJECT_ID>
        ```
    * **List Spokes:**
        ```bash
        gcloud network-connectivity spokes list --hub=<NCC_HUB_NAME> --project=<MAIN_PROJECT_ID>
        ```
        (You may need to filter by location or project if there are many spokes)

## Important Notes
-   This blueprint currently supports **VPC spokes only**. For information on other types of NCC spokes (e.g., VPN, Cloud Interconnect, Router appliance), refer to the official [Network Connectivity Center documentation](https://cloud.google.com/network-connectivity/docs/network-connectivity-center/concepts/overview).
-   **STAR Topology Behavior:** If you choose the `STAR` topology, VPCs located in the same project as the hub (`main_project_id`) will be automatically placed into the "center" connectivity group. All other VPCs from different projects will be placed into the "edge" connectivity group. For `MESH` topology, all spokes are in the "default" group.
-   **Private Service Connect (PSC) Propagation:** You can enable Private Service Connect [connection propagation](https://cloud.google.com/network-connectivity/docs/network-connectivity-center/concepts/psc-propagated-connection-overview) via the `psc_prop` variable.

<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [main_project_id](variables.tf#L1) | The Google Cloud Project ID where the NCC hub will be created. | <code>string</code> | ✓ |  |
| [ncc_hub_name](variables.tf#L6) | The name of the created Network Connectivity Center hub. | <code>string</code> |  | <code>&#34;example-ncc-hub&#34;</code> |
| [psc_prop](variables.tf#L12) | Whether or not Private Service Connect connections can be propagated to other spokes in the network. | <code>bool</code> |  | <code>false</code> |
| [gcp_region](variables.tf#L18) | The Google Cloud region to be used as the default for regional resources and the provider. Note: NCC Hubs are global resources. | <code>string</code> | ✓ |  |
| [spokes](variables.tf#L23) | A map of spoke names to VPC Network self-links (e.g., &#39;projects/&lt;PROJECT_ID&gt;/global/networks/&lt;VPC_NAME&gt;&#39;) to be added to the NCC hub. | <code>map&#40;string&#41;</code> |  | <code>&#123;&#125;</code> |
| [topology](variables.tf#L30) | The topology of the network. Can be MESH or STAR. | <code>string</code> |  | <code>&#34;MESH&#34;</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [hub](outputs.tf#L1) | The NCC hub ID. |  |
| [spokes](outputs.tf#L6) | The NCC spokes. |  |
<!-- END TFDOC -->
