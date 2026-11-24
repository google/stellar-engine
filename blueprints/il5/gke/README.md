# GKE cluster blueprint

<!-- BEGIN TOC -->
- [1 Purpose](#1-purpose)
- [2 Prerequisites](#2-prerequisites)
- [3 Compliance scope](#3-compliance-scope)
- [4 Deployment steps](#4-deployment-steps)
  - [Node pool strategy](#node-pool-strategy)
  - [Cluster verification](#cluster-verification)
- [Variables](#variables)
- [Outputs](#outputs)
<!-- END TOC -->

## 1 Purpose

This blueprint deploys a private Google Kubernetes Engine Standard cluster and bastion VM in a dedicated workload service project while consuming Shared VPC networking and Cloud KMS encryption keys from central platform projects:

- Consumes an existing Shared VPC subnet and secondary Pod and Service CIDR ranges from `landing_project_id`.
- Encrypts node boot disks and bastion disks with an existing Customer-Managed Encryption Key from `core_project_id`.
- Encrypts Kubernetes Secrets in etcd (`database_encryption`, application-layer secrets encryption) with the same Cloud KMS key.

Separating network, encryption, and cluster projects lets platform teams govern VPC and KMS controls centrally while application teams manage GKE workloads in isolated service projects.

## 2 Prerequisites

Ensure the following projects, network ranges, keys, and IAM bindings exist before running Terraform:

- Provision three billing-enabled Google Cloud projects: `main_project_id` for the GKE cluster, `landing_project_id` for the Shared VPC host network, and `core_project_id` for the Cloud KMS key ring and CryptoKey.
- Attach `main_project_id` to `landing_project_id` as a Shared VPC service project.
- Configure the target Shared VPC subnet with two secondary IP CIDR ranges dedicated to GKE Pods and GKE Services.
- Provision the Cloud KMS key ring and CryptoKey in `core_project_id` in the target `gcp_region`.
- Grant required IAM roles across all three projects:
  - On `main_project_id`, grant the deploying identity `roles/container.admin` and `roles/iam.serviceAccountAdmin`.
  - On `landing_project_id`, grant `roles/compute.networkUser` on the target subnet to the `main_project_id` GKE service agent, Google APIs service agent, and Compute Engine service agent, and grant `roles/container.hostServiceAgentUser` to the `main_project_id` GKE service agent.
  - On `core_project_id`, grant `roles/cloudkms.cryptoKeyEncrypterDecrypter` on the KMS CryptoKey to the `main_project_id` GKE service agent and Compute Engine service agent.

## 3 Compliance scope

- Deploy this blueprint inside a FedRAMP High or IL5 Assured Workloads folder within your Google Cloud organization.
- Assured Workloads enforces regional data residency and encryption guardrails required for federal and defense workloads.

## 4 Deployment steps

1. Copy `terraform.tfvars.sample` to `terraform.tfvars` and populate all required input variables listed in [Variables](#variables).
2. Initialize the Terraform working directory:

```bash
terraform init
```

3. Review the execution plan and apply the configuration:

```bash
terraform plan
terraform apply
```

### Node pool strategy

By default, `remove_default_node_pool = true` removes GKE's initial `default-pool` after creating a dedicated custom node pool via `modules/gke-nodepool`, and you can set `remove_default_node_pool = false` if you want to retain `default-pool` for system workloads. Separating workloads across custom node pools provides four operational advantages:

- Select high-CPU, high-memory, or GPU machine types tailored to specific workloads.
- Isolate sensitive workloads onto dedicated nodes with distinct service accounts and network tags.
- Run fault-tolerant batch or CI/CD workloads on lower-cost machine families.
- Upgrade node pools incrementally to validate Kubernetes version upgrades before rolling out to critical pools.

See the [GKE node pools documentation](https://cloud.google.com/kubernetes-engine/docs/concepts/node-pools) for sizing and lifecycle guidance.

### Cluster verification

Connect to the private GKE control plane from the deployed bastion host VM in `main_project_id`:

1. Open an SSH session to the bastion VM:

```bash
gcloud compute ssh <BASTION_VM_NAME> --zone <BASTION_VM_ZONE> --tunnel-through-iap --project <MAIN_PROJECT_ID>
```

The bastion VM has no external IP address (its network interface does not set `nat`), so the SSH session has to go through Identity-Aware Proxy.

2. Fetch cluster credentials inside the bastion `toolbox` container environment and verify node readiness:

```bash
kubectl get nodes
```

<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [bastion_vm_zone](variables.tf#L36) | The zone for the bastion host VM. | <code>string</code> | ✓ |  |
| [core_project_id](variables.tf#L41) | The Google Cloud Project ID where the existing Cloud KMS key is located. | <code>string</code> | ✓ |  |
| [existing_kms_key_name](variables.tf#L52) | The name of the existing Cloud KMS CryptoKey for boot disk encryption. | <code>string</code> | ✓ |  |
| [existing_kms_keyring_name](variables.tf#L57) | The name of the existing Cloud KMS Key Ring. | <code>string</code> | ✓ |  |
| [existing_network_name](variables.tf#L63) | The name of the existing Shared VPC network to use for the GKE cluster. | <code>string</code> | ✓ |  |
| [existing_subnetwork_name](variables.tf#L68) | The name of the existing subnetwork to use for the GKE cluster. | <code>string</code> | ✓ |  |
| [existing_subnetwork_secondary_range_pods_name](variables.tf#L73) | The name of the existing secondary IP range for GKE Pods. | <code>string</code> | ✓ |  |
| [existing_subnetwork_secondary_range_services_name](variables.tf#L78) | The name of the existing secondary IP range for GKE Services. | <code>string</code> | ✓ |  |
| [gcp_region](variables.tf#L84) | The Google Cloud region where all resources will be deployed. | <code>string</code> | ✓ |  |
| [landing_project_id](variables.tf#L121) | The Google Cloud Project ID where the existing Shared VPC network is located. | <code>string</code> | ✓ |  |
| [main_project_id](variables.tf#L126) | The Google Cloud Project ID where the GKE cluster will be created. | <code>string</code> | ✓ |  |
| [bastion_vm_image](variables.tf#L17) | The boot disk image for the bastion host VM. | <code>string</code> |  | <code>&#34;projects&#47;cos-cloud&#47;global&#47;images&#47;family&#47;cos-stable&#34;</code> |
| [bastion_vm_machine_type](variables.tf#L23) | The machine type for the bastion host VM. | <code>string</code> |  | <code>&#34;e2-medium&#34;</code> |
| [bastion_vm_name](variables.tf#L30) | The name for the bastion host VM. | <code>string</code> |  | <code>&#34;gke-bastion-vm&#34;</code> |
| [enable_deletion_protection](variables.tf#L46) | Whether or not to allow Terraform to destroy the cluster. Recommended to be true for production. | <code>bool</code> |  | <code>true</code> |
| [gke_cluster_enable_private_endpoint](variables.tf#L89) | Enable a private endpoint for the GKE cluster master, disabling public access. | <code>bool</code> |  | <code>true</code> |
| [gke_cluster_master_global_access](variables.tf#L95) | WARNING: Expands the internal attack surface. Enable global access for the private master endpoint. If false, access is limited to the cluster's region. | <code>bool</code> |  | <code>false</code> |
| [gke_cluster_name](variables.tf#L102) | The name of the GKE cluster. | <code>string</code> |  | <code>&#34;gke-cluster&#34;</code> |
| [gke_initial_node_per_zone](variables.tf#L109) | The initial number of nodes for the default node pool. | <code>number</code> |  | <code>1</code> |
| [gke_nodepool_name](variables.tf#L115) | The name of the additional GKE node pool. | <code>string</code> |  | <code>&#34;default-nodepool&#34;</code> |
| [master_authorized_ranges](variables.tf#L131) | A map of authorized networks that can access the GKE master endpoint. The key is a display name and the value is the CIDR range. Should be scoped as tightly as possible. | <code>map&#40;string&#41;</code> |  | <code>&#123;&#125;</code> |
| [node_config_tags](variables.tf#L137) | A list of network tags to apply to the GKE nodes. | <code>list&#40;string&#41;</code> |  | <code>&#91;&#93;</code> |
| [node_disk_size_gb](variables.tf#L143) | The boot disk size in GB for each GKE node. | <code>number</code> |  | <code>20</code> |
| [node_machine_type](variables.tf#L149) | The machine type for the GKE nodes. | <code>string</code> |  | <code>&#34;n2d-standard-2&#34;</code> |
| [nodepool_node_count](variables.tf#L155) | The initial number of nodes per zone for the additional node pool. | <code>object&#40;&#123; initial &#61; number &#125;&#41;</code> |  | <code>&#123; initial &#61; 1 &#125;</code> |
| [remove_default_node_pool](variables.tf#L161) | Set to true to remove the default node pool created with the cluster. Requires at least one other node pool to be created. | <code>bool</code> |  | <code>true</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [bastion_vm_name](outputs.tf#L17) | The name of the created bastion Compute Engine VM. |  |
| [bastion_vm_public_ip](outputs.tf#L22) | The external IP address of the bastion Compute Engine VM, or null when the VM has no external IP. |  |
| [cluster_master_version](outputs.tf#L27) | The master version of the GKE cluster. |  |
| [consumed_kms_key_id](outputs.tf#L32) | The ID of the existing KMS CryptoKey used by the GKE cluster for boot disk encryption. |  |
| [consumed_network_self_link](outputs.tf#L37) | The self-link of the existing VPC network used by the GKE cluster. |  |
| [consumed_subnetwork_self_link](outputs.tf#L42) | The self-link of the existing subnetwork used by the GKE cluster. |  |
| [gke_cluster_endpoint](outputs.tf#L47) | The endpoint of the GKE cluster. |  |
| [gke_cluster_name](outputs.tf#L52) | The name of the GKE cluster. |  |
| [gke_cluster_sa_email](outputs.tf#L57) | The email address of the custom service account created for the GKE cluster. |  |
| [nodepool_id](outputs.tf#L62) | The fully qualified ID of the additional GKE nodepool. |  |
| [nodepool_name](outputs.tf#L67) | The name of the additional GKE nodepool. |  |
| [nodepool_service_account_email](outputs.tf#L72) | The service account email used by the additional GKE nodepool. |  |
<!-- END TFDOC -->
