# Hardened GKE cluster blueprint

<!-- BEGIN TOC -->
- [1 Purpose](#1-purpose)
- [2 Prerequisites](#2-prerequisites)
- [3 Compliance scope](#3-compliance-scope)
- [4 Deployment steps](#4-deployment-steps)
- [5 Deployment verification](#5-deployment-verification)
- [Variables](#variables)
- [Outputs](#outputs)
<!-- END TOC -->

## 1 Purpose

This blueprint deploys a hardened Google Kubernetes Engine Standard cluster, a dedicated VPC, a Cloud KMS key ring and CryptoKey, a Cloud NAT gateway, a bastion VM, and Fleet Config Management with Policy Controller and Config Sync.

- Enables required Google Cloud APIs (`anthosconfigmanagement`, `cloudkms`, `cloudresourcemanager`, `compute`, `container`, `gkehub`, `iam`, `logging`, `monitoring`, `storage`, and `storagetransfer`) before creating cluster, network, and KMS resources.
- Enforces private nodes, Shielded GKE Nodes, Confidential GKE Nodes, Dataplane V2, Binary Authorization, and Cloud KMS encryption for node boot disks and cluster etcd secrets using the `default` key in `kms_key_names`.
- Registers the cluster with a Fleet and configures Config Management to reconcile Kubernetes policies from the Git repository in `source_repo`, branch in `source_branch`, and directory in `source_dir`.

## 2 Prerequisites

Ensure the target project and deploying identity satisfy these requirements before running Terraform:

- Provision an existing Google Cloud project (`main_project_id`) with billing enabled.
- Grant the deploying identity permissions to enable service APIs, create VPC networks, manage Cloud KMS key rings and CryptoKeys, create GKE clusters and Fleet memberships, manage Compute Engine instances, and create service accounts and IAM bindings (`roles/serviceusage.serviceUsageAdmin`, `roles/compute.networkAdmin`, `roles/compute.securityAdmin`, `roles/compute.instanceAdmin.v1`, `roles/cloudkms.admin`, `roles/container.admin`, `roles/gkehub.admin`, `roles/iam.serviceAccountAdmin`, and `roles/resourcemanager.projectIamAdmin`).
- When setting `config_sync_secret_type` to `gcpserviceaccount`, create the user-managed service account ahead of time, grant it `roles/iam.workloadIdentityUser` for `serviceAccount:MAIN_PROJECT_ID.svc.id.goog[config-management-system/root-reconciler]`, and grant it read access to `source_repo`.
- Cloud KMS CryptoKeys support scheduled destruction through `destroy_scheduled_duration` (default 30 days) rather than immediate deletion.

## 3 Compliance scope

- Deploy this blueprint inside a FedRAMP High or IL5 Assured Workloads folder within your Google Cloud organization.
- Assured Workloads enforces regional data residency and FIPS cryptographic guardrails required for federal and defense workloads.
- Select a `node_machine_type` that supports Confidential GKE Nodes, such as `n2d-*`, `c2d-*`, or `c3d-*`.

## 4 Deployment steps

1. Copy the sample variables file and populate `terraform.tfvars` with your project ID, network CIDRs, Cloud KMS keyring settings, and Config Sync repository details:

```bash
cp terraform.tfvars.sample terraform.tfvars
```

2. Initialize Terraform and review the planned infrastructure changes:

```bash
terraform init
terraform plan
```

3. Apply the configuration:

```bash
terraform apply
```

4. To tear down the blueprint resources when no longer needed, run `terraform destroy`:

```bash
terraform destroy
```

## 5 Deployment verification

Verify the cluster, node pool, and Policy Controller configuration from the bastion host or an authorized workstation:

1. Connect to the bastion VM through Identity-Aware Proxy:

```bash
gcloud compute ssh bastion-vm --zone <REGION>-a --tunnel-through-iap --project <MAIN_PROJECT_ID>
```

2. Confirm cluster status and Fleet Config Management sync health:

```bash
gcloud container clusters describe <GKE_CLUSTER_NAME> --location <REGION> --project <MAIN_PROJECT_ID>
gcloud container fleet config-management status --project <MAIN_PROJECT_ID>
```
<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [gatekeeper_sa](variables.tf#L69) | The service account Gatekeeper uses to push metrics to GCP. | <code>string</code> | ✓ |  |
| [gke_cluster_enable_private_endpoint](variables.tf#L74) | The Private Cluster configuration to enable private end point. | <code>bool</code> | ✓ |  |
| [gke_cluster_master_global_access](variables.tf#L80) | The Private Cluster configuration to check the master Global Access. | <code>bool</code> | ✓ |  |
| [gke_cluster_name](variables.tf#L86) | The GKE Kubernetes Cluster Name. | <code>string</code> | ✓ |  |
| [gke_initial_node_per_zone](variables.tf#L92) | The intial number of Node per each zone. | <code>number</code> | ✓ |  |
| [gke_nodepool_name](variables.tf#L98) | The GKE Kubernetes Cluster Name. | <code>string</code> | ✓ |  |
| [gke_vpc_master_ipv4_cidr_block](variables.tf#L104) | The CIDR Range for the GKE Master IP CIDR Ranges for the k8s used for VPC configuration. | <code>string</code> | ✓ |  |
| [kms_keyring_name](variables.tf#L163) | Keyring attributes. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> | ✓ |  |
| [local_admin_external_ip](variables.tf#L171) | local admin workstation external ip to ssh into bastion vm. | <code>list&#40;string&#41;</code> | ✓ |  |
| [main_project_id](variables.tf#L176) | The ID of the project in which to create the GKE cluster. | <code>string</code> | ✓ |  |
| [master_authorized_ranges_ip_ranges](variables.tf#L181) | The CIDR Range for the GKE Nodes Pool when enabled Private End Point with master aurhotized ranges of CIDR. | <code>string</code> | ✓ |  |
| [nat_gateway_name](variables.tf#L186) | The nat gateway for outboud routing from the cluster. | <code>string</code> | ✓ |  |
| [nat_router_name](variables.tf#L191) | The nat router for outboud routing from the cluster. | <code>string</code> | ✓ |  |
| [network_name](variables.tf#L196) | The VPC Name. | <code>string</code> | ✓ |  |
| [node_config_tags](variables.tf#L202) | The Tags on the Node Configuration. | <code>list&#40;string&#41;</code> | ✓ |  |
| [node_disk_size_gb](variables.tf#L208) | The disk size in GB to be given to each node. | <code>number</code> | ✓ |  |
| [nodepool_node_count](variables.tf#L219) | Number of node per zone in the Nodepool. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> | ✓ |  |
| [region](variables.tf#L234) | The GCP region to use for the resources. | <code>string</code> | ✓ |  |
| [source_dir](variables.tf#L258) | The directory in the repository containing policies. | <code>string</code> | ✓ |  |
| [source_repo](variables.tf#L263) | The repository used for config sync gitops. | <code>string</code> | ✓ |  |
| [subnetwork_ip_cidr_range_1](variables.tf#L268) | The CIDR Range for the VPC Subnet. | <code>string</code> | ✓ |  |
| [subnetwork_name](variables.tf#L274) | The Subnet Name. | <code>string</code> | ✓ |  |
| [subnetwork_secondary_ip_range_pods_1](variables.tf#L280) | The CIDR Range for the secondary IP CIDR Ranges for the k8s pods. | <code>string</code> | ✓ |  |
| [subnetwork_secondary_ip_range_services_1](variables.tf#L286) | The CIDR Range for the secondary IP CIDR Ranges for the k8s services. | <code>string</code> | ✓ |  |
| [bastion_vm_zone](variables.tf#L15) | Optional GCP zone for the bastion host VM. Defaults to `<region>-a` when null. | <code>string</code> |  | <code>null</code> |
| [config_sync_secret_type](variables.tf#L28) | The type of secret Config Sync uses to authenticate to the Git repository in source_repo. The cookiefile, githubapp, ssh, and token values need a git-creds Kubernetes Secret that you create out of band in the config-management-system namespace. The gcpserviceaccount value needs config_sync_service_account_email. The none value needs no credentials. | <code>string</code> |  | <code>&#34;none&#34;</code> |
| [config_sync_service_account_email](variables.tf#L46) | The email of the user-managed service account Config Sync uses to authenticate to the Git repository in source_repo. Set it when and only when config_sync_secret_type is gcpserviceaccount. This blueprint creates no IAM binding for the account, so grant roles/iam.workloadIdentityUser on it to the member serviceAccount:MAIN_PROJECT_ID.svc.id.goog[config-management-system/root-reconciler], and grant the account read access to the repository. | <code>string</code> |  | <code>null</code> |
| [kms_key_names](variables.tf#L110) | Key names and base attributes, which must include a `default` entry referenced by the cluster, node pool, and bastion VM. Set attributes to null if not needed. | <code>map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> |  | <code>&#123;&#8230;&#125;</code> |
| [node_machine_type](variables.tf#L213) | The node machine type, which must support Confidential GKE Nodes, such as the N2D, C2D or C3D series. | <code>string</code> |  | <code>&#34;n2d-standard-2&#34;</code> |
| [policy_controller_exemptable_namespaces](variables.tf#L228) | The exemted namespaces for policy controller. | <code>list&#40;any&#41;</code> |  | <code>&#91;&#93;</code> |
| [remove_default_node_pool](variables.tf#L239) | Remove the default node pool, which runs without the hardened node settings of the cluster node pool. | <code>bool</code> |  | <code>true</code> |
| [snapshot_max_retention_days](variables.tf#L246) | The maximum number of days to retain snapshots. | <code>number</code> |  | <code>14</code> |
| [source_branch](variables.tf#L252) | The branch of the repository used for config sync gitops. | <code>string</code> |  | <code>&#34;main&#34;</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [cluster_master_version](outputs.tf#L15) | Master version. |  |
| [gke_cluster_endpoint](outputs.tf#L20) | The endpoint of the GKE cluster. |  |
| [gke_cluster_name](outputs.tf#L25) | The name of the GKE cluster. |  |
| [keyring_id](outputs.tf#L30) | Fully qualified keyring id. |  |
| [keyring_location](outputs.tf#L35) | Keyring location. |  |
| [keyring_name](outputs.tf#L40) | Keyring name. |  |
| [keyring_resource](outputs.tf#L45) | Keyring resource. |  |
| [keyrings_keys](outputs.tf#L50) | Key resources. |  |
| [nodepool_id](outputs.tf#L55) | Fully qualified nodepool id. |  |
| [nodepool_name](outputs.tf#L60) | Nodepool name. |  |
| [nodepool_service_account_email](outputs.tf#L65) | Service account email. |  |
| [subnet_regions](outputs.tf#L70) | Map of subnet regions keyed by name. |  |
| [subnets](outputs.tf#L75) | Subnet resources. |  |
| [vpc_network](outputs.tf#L80) | Network resource. |  |
| [vpc_subnet_ids](outputs.tf#L85) | Map of subnet IDs keyed by name. |  |
| [vpc_subnet_ips](outputs.tf#L90) | Map of subnet address ranges keyed by name. |  |
<!-- END TFDOC -->
