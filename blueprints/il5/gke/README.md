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

# GKE Cluster with Shared VPC and KMS Blueprint
<!-- BEGIN TOC -->
- [Purpose](#purpose)
- [Prerequisites](#prerequisites)
- [Disclaimer](#disclaimer)
- [Usage](#usage)
- [Inputs](#inputs)
- [Outputs](#outputs)
<!-- END TOC -->

## Purpose

This blueprint deploys a Google Kubernetes Engine (GKE) Standard cluster designed for enterprise environments that require a separation of duties. It follows security best practices by consuming pre-existing network and encryption resources from separate, dedicated Google Cloud projects.

The key feature of this blueprint is its **decoupling** from the underlying infrastructure. It does not create its own VPC network or KMS keys. Instead, it securely connects to and utilizes:
* A **Shared VPC** from a central landing zone project.
* A **Customer-Managed Encryption Key (CMEK)** from a central core/security project for node boot disk encryption.

This allows platform teams to manage the network and security resources centrally while enabling application teams to deploy GKE clusters in their own service projects.

## Prerequisites

Before running this blueprint, the following resources and permissions must be in place:

1.  **Three distinct Google Cloud projects** with billing enabled:
    * A **Main Project** to host the GKE cluster.
    * A **Landing Zone / Host Project** that contains the Shared VPC.
    * A **Core / Security Project** that contains the Cloud KMS key.
2.  **Shared VPC Configuration**: The Main Project must be attached to the Host Project's Shared VPC as a service project.
3.  **Network Resources**: The subnetwork within the Shared VPC must have at least **two secondary IP ranges** available. GKE requires one dedicated range for Pods and a separate range for Services.
4.  **KMS Resources**: A Cloud KMS Key Ring and CryptoKey must exist in the Core Project.
5.  **Permissions**: The user or service account running `terraform apply` needs specific permissions in all three projects. The necessary roles are:
    * **On the Main Project:**
        * `roles/container.admin`: To create and manage the GKE cluster.
        * `roles/iam.serviceAccountAdmin`: To create the GKE service account.
    * **On the Host Project:**
        * `roles/compute.networkUser`: Must be assigned to the **GKE Service Agent**, **Google APIs Service Agent**, and **Compute Engine Service Agent** of the Main Project.
        * `roles/container.hostServiceAgentUser`: Must be assigned to the **GKE Service Agent** of the Main Project.
    * **On the Core Project:**
        * `roles/cloudkms.cryptoKeyEncrypterDecrypter`: Must be assigned to the **GKE Service Agent** and the **Compute Engine Service Agent** of the Main Project.

## Disclaimer
The present GCP Terraform Module in this project is set up and intended to be implemented in either a FedRAMP-High or IL5 (Impact Level 5) environment using the Assured Workloads within the Google Cloud Platform (GCP) organization. Assured Workloads in both environments ensures that sensitive data and workloads in GCP adhere to the rigorous security standards mandated by the DoD, making it suitable for government agencies.

## Usage

1.  **Configure Variables**: Create a `terraform.tfvars` file and provide values for all the required input variables. See the auto-generated Inputs section below for details.

2.  **Initialize Terraform**:
    ```bash
    terraform init
    ```

3.  **Plan and Apply**:
    ```bash
    terraform plan
    terraform apply
    ```

### Node Pool Strategy

This blueprint creates two node pools by default: `default-pool` and a separate custom node pool (e.g., `gke-nodepool-name-00`). This is an intentional design choice and a GKE best practice.

* **`default-pool`**: This pool is created automatically by GKE and is suitable for running system components. By default, this blueprint keeps it.
* **Custom Node Pool**: This pool is created by the `cluster_nodepool` module and is intended for your specific applications.

Using separate node pools allows you to optimize performance, security, and cost by running different types of applications on different kinds of machines. Key benefits include:

* **Specialized Hardware**: Create pools with high-CPU, high-memory, or GPU-enabled machines for specific workloads.
* **Security & Isolation**: Run sensitive applications on dedicated nodes with unique service accounts or network tags.
* **Cost Optimization**: Use cheaper machine types or fault-tolerant Spot VMs for batch jobs or CI/CD workloads.
* **Controlled Upgrades**: Upgrade your cluster one node pool at a time, testing on less critical workloads first.

If you wish to only use a single custom node pool, you can set the `remove_default_node_pool` variable to `true`.

This approach is a documented best practice for production clusters. For more information, you can refer to the official [Google Cloud documentation on Node Pools](https://cloud.google.com/kubernetes-engine/docs/concepts/node-pools).

### Testing the Cluster

A bastion host VM is deployed in the Main Project to provide a secure way to access and test the GKE cluster.

1.  **SSH to the bastion host**:
    ```bash
    gcloud compute ssh [BASTION_VM_NAME] --zone [BASTION_VM_ZONE] --project [MAIN_PROJECT_ID]
    ```

2.  **Configure `kubectl`**: Follow the on-screen instructions inside the bastion host's `toolbox` environment to install the necessary tools and get cluster credentials.

3.  **Test the connection**:
    ```bash
    kubectl get nodes
    ```

<!-- BEGIN TFDOC -->
## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| **bastion_vm_zone** | The zone for the bastion host VM. | `string` | n/a | yes |
| **core_project_id** | The Google Cloud Project ID where the existing Cloud KMS key is located. | `string` | n/a | yes |
| **existing_kms_key_name** | The name of the existing Cloud KMS CryptoKey for boot disk encryption. | `string` | n/a | yes |
| **existing_kms_keyring_name** | The name of the existing Cloud KMS Key Ring. | `string` | n/a | yes |
| **existing_network_name** | The name of the existing Shared VPC network to use for the GKE cluster. | `string` | n/a | yes |
| **existing_subnetwork_name** | The name of the existing subnetwork to use for the GKE cluster. | `string` | n/a | yes |
| **existing_subnetwork_secondary_range_pods_name** | The name of the existing secondary IP range for GKE Pods. | `string` | n/a | yes |
| **existing_subnetwork_secondary_range_services_name** | The name of the existing secondary IP range for GKE Services. | `string` | n/a | yes |
| **gcp_region** | The Google Cloud region where all resources will be deployed. | `string` | n/a | yes |
| **landing_project_id** | The Google Cloud Project ID where the existing Shared VPC network is located. | `string` | n/a | yes |
| **main_project_id** | The Google Cloud Project ID where the GKE cluster will be created. | `string` | n/a | yes |
| **bastion_vm_image** | The boot disk image for the bastion host VM. | `string` | `"projects/cos-cloud/global/images/family/cos-stable"` | no |
| **bastion_vm_machine_type** | The machine type for the bastion host VM. | `string` | `"e2-medium"` | no |
| **bastion_vm_name** | The name for the bastion host VM. | `string` | `"gke-bastion-vm"` | no |
| **enable_deletion_protection** | Whether or not to allow Terraform to destroy the cluster. Recommended to be true for production. | `bool` | `true` | no |
| **gke_cluster_enable_private_endpoint** | Enable a private endpoint for the GKE cluster master, disabling public access. | `bool` | `true` | no |
| **gke_cluster_master_global_access** | WARNING: Expands the internal attack surface. Enable global access for the private master endpoint. If false, access is limited to the cluster's region. | `bool` | `false` | no |
| **gke_cluster_name** | The name of the GKE cluster. | `string` | `"gke-cluster"` | no |
| **gke_initial_node_per_zone** | The initial number of nodes for the default node pool. | `number` | `1` | no |
| **gke_nodepool_name** | The name of the additional GKE node pool. | `string` | `"default-nodepool"` | no |
| **master_authorized_ranges** | A map of authorized networks that can access the GKE master endpoint. The key is a display name and the value is the CIDR range. Should be scoped as tightly as possible. | `map(string)` | `{}` | no |
| **node_config_tags** | A list of network tags to apply to the GKE nodes. | `list(string)` | `[]` | no |
| **node_disk_size_gb** | The boot disk size in GB for each GKE node. | `number` | `20` | no |
| **node_machine_type** | The machine type for the GKE nodes. | `string` | `"n2d-standard-2"` | no |
| **nodepool_node_count** | The initial number of nodes per zone for the additional node pool. | `object({ initial = number })` | `{ initial = 1 }` | no |
| **remove_default_node_pool** | Set to true to remove the default node pool created with the cluster. Requires at least one other node pool to be created. | `bool` | `false` | no |

## Outputs

| Name | Description |
|------|-------------|
| **bastion_vm_name** | The name of the created bastion Compute Engine VM. |
| **bastion_vm_public_ip** | The public IP address of the bastion Compute Engine VM (if ephemeral public IP is enabled). |
| **cluster_master_version** | The master version of the GKE cluster. |
| **consumed_kms_key_id** | The ID of the existing KMS CryptoKey used by the GKE cluster for boot disk encryption. |
| **consumed_network_self_link** | The self-link of the existing VPC network used by the GKE cluster. |
| **consumed_subnetwork_self_link** | The self-link of the existing subnetwork used by the GKE cluster. |
| **gke_cluster_endpoint** | The endpoint of the GKE cluster. |
| **gke_cluster_name** | The name of the GKE cluster. |
| **gke_cluster_sa_email** | The email address of the custom service account created for the GKE cluster. |
| **nodepool_id** | The fully qualified ID of the additional GKE nodepool. |
| **nodepool_name** | The name of the additional GKE nodepool. |
| **nodepool_service_account_email** | The service account email used by the additional GKE nodepool. |
<!-- END TFDOC -->

