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

# Google Kubernetes Engine (GKE) Standard Project
This blueprint contains all the necessary Terraform modules to build and deploy a Google Kubernetes Engine (GKE), a managed Kubernetes cluster having encryption using the Cloud Key Management Service (KMS).

## Introduction
- GKE is a Google-managed implementation of the Kubernetes open source container orchestration platform.  In GKE Standard mode, there are flexible node upgrade strategies to optimize availability and manage disruptions.
- In GKE Standard mode, you pay for all resources on nodes, regardless of Pod requests. A GKE environment consists of nodes, which are Compute Engine virtual machines (VMs) with Customer-Managed Encryption Keys (CMEK) Cloud KMS that are grouped together to form a cluster.
- This implementation offers a way to create and manage Google Kubernetes Engine (GKE) [Standard clusters](https://cloud.google.com/kubernetes-engine/docs/concepts/choose-cluster-mode#why-standard).
- In GKE, the allocation of the nodes is done as per the Zone. For more details refer to the GKE cluster configuration choices  [GKE cluster configuration choices](https://cloud.google.com/kubernetes-engine/docs/concepts/types-of-clusters)
- For example, If there are 3 Zone gcp-region-name-a, gcp-region-name-b, gcp-region-name-c. The initial node allocation per zone is 1. Then the total number of nodes shall be 3 x 1 = 3 total nodes in the cluster.
- GKE yaml files are hosted in the policies folder and will be applied to the deployed cluster automatically. Only yaml files in the policies folder. Do not remove the disable-priv-pods.yaml as that is responsible for creating a cron job that will disable privileged pods in the cluster every hour.

## Pre-requisite
1. The Principal (user or group) must have Cloud KMS Admin, Able to Deploy a Google VPC, GKE Create, permission at the GCP Level.
2. Have access to the GCP Project ID
3.  You will need an existing [project](https://cloud.google.com/resource-manager/docs/creating-managing-projects) with [billing enabled](https://cloud.google.com/billing/docs/how-to/modify-project) and a user with the “Project owner” [IAM](https://cloud.google.com/iam) role on that project. __Note__: to grant a user a role, take a look at the [Granting and Revoking Access](https://cloud.google.com/iam/docs/granting-changing-revoking-access#grant-single-role) documentation.

## Disclaimer
- The present GCP Terraform Module in this project is set up and intended to be implemented in either a FedRAMP-High or IL5 (Impact Level 5) environment using the Assured Workloads within the Google Cloud Platform (GCP) organization.
- Assured Workloads in both environments ensures that sensitive data and workloads in GCP adhere to the rigorous security standards mandated by the DoD, making it suitable for government agencies.

## How to deploy the Terraform Code.
The Deployment Steps are outlined in the [Stellar Engine GKE Deployment Guide.](https://docs.google.com/document/d/1N14MwvzrYV2lHhXfH3oVTU-cAk-HXXLhPF9mfm0ieoA/edit?tab=t.0)
<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [gatekeeper_sa](variables.tf#L1) | The service account Gatekeeper uses to push metrics to GCP. | <code>string</code> | ✓ |  |
| [gke_cluster_enable_private_endpoint](variables.tf#L6) | The Private Cluster configuration to enable private end point. | <code>bool</code> | ✓ |  |
| [gke_cluster_master_global_access](variables.tf#L12) | The Private Cluster configuration to check the master Global Access. | <code>bool</code> | ✓ |  |
| [gke_cluster_name](variables.tf#L18) | The GKE Kubernetes Cluster Name. | <code>string</code> | ✓ |  |
| [gke_initial_node_per_zone](variables.tf#L24) | The intial number of Node per each zone. | <code>number</code> | ✓ |  |
| [gke_nodepool_name](variables.tf#L30) | The GKE Kubernetes Cluster Name. | <code>string</code> | ✓ |  |
| [gke_vpc_master_ipv4_cidr_block](variables.tf#L36) | The CIDR Range for the GKE Master IP CIDR Ranges for the k8s used for VPC configuration. | <code>string</code> | ✓ |  |
| [kms_keyring_name](variables.tf#L93) | Keyring attributes. | <code title="object&#40;&#123;&#10;  location &#61; string&#10;  name     &#61; string&#10;&#125;&#41;">object&#40;&#123;&#8230;&#125;&#41;</code> | ✓ |  |
| [local_admin_external_ip](variables.tf#L101) | local admin workstation external ip to ssh into bastion vm. | <code>list&#40;string&#41;</code> | ✓ |  |
| [main_project_id](variables.tf#L106) | The ID of the project in which to create the GKE cluster. | <code>string</code> | ✓ |  |
| [master_authorized_ranges_ip_ranges](variables.tf#L111) | The CIDR Range for the GKE Nodes Pool when enabled Private End Point with master aurhotized ranges of CIDR. | <code>string</code> | ✓ |  |
| [nat_gateway_name](variables.tf#L116) | The nat gateway for outboud routing from the cluster. | <code>string</code> | ✓ |  |
| [nat_router_name](variables.tf#L121) | The nat router for outboud routing from the cluster. | <code>string</code> | ✓ |  |
| [network_name](variables.tf#L126) | The VPC Name. | <code>string</code> | ✓ |  |
| [node_config_tags](variables.tf#L132) | The Tags on the Node Configuration. | <code>list&#40;string&#41;</code> | ✓ |  |
| [node_disk_size_gb](variables.tf#L138) | The disk size in GB to be given to each node. | <code>number</code> | ✓ |  |
| [nodepool_node_count](variables.tf#L149) | Number of node per zone in the Nodepool. | <code title="object&#40;&#123;&#10;  current &#61; optional&#40;number&#41;&#10;  initial &#61; number&#10;&#125;&#41;">object&#40;&#123;&#8230;&#125;&#41;</code> | ✓ |  |
| [region](variables.tf#L164) | The GCP region to use for the resources. | <code>string</code> | ✓ |  |
| [remove_default_node_pool](variables.tf#L171) | The Default NodePool remove it or not. | <code>bool</code> | ✓ |  |
| [source_dir](variables.tf#L183) | The directory in the repository containing policies. | <code>string</code> | ✓ |  |
| [source_repo](variables.tf#L188) | The repository used for config sync gitops. | <code>string</code> | ✓ |  |
| [subnetwork_ip_cidr_range_1](variables.tf#L193) | The CIDR Range for the VPC Subnet. | <code>string</code> | ✓ |  |
| [subnetwork_name](variables.tf#L199) | The Subnet Name. | <code>string</code> | ✓ |  |
| [subnetwork_secondary_ip_range_pods_1](variables.tf#L205) | The CIDR Range for the secondary IP CIDR Ranges for the k8s pods. | <code>string</code> | ✓ |  |
| [subnetwork_secondary_ip_range_services_1](variables.tf#L211) | The CIDR Range for the secondary IP CIDR Ranges for the k8s services. | <code>string</code> | ✓ |  |
| [kms_key_names](variables.tf#L42) | Key names and base attributes. Set attributes to null if not needed. | <code title="map&#40;object&#40;&#123;&#10;  destroy_scheduled_duration    &#61; optional&#40;string&#41;&#10;  rotation_period               &#61; optional&#40;string, &#34;7776000s&#34;&#41; &#35; CIS Compliance Benchmark 1.10&#10;  labels                        &#61; optional&#40;map&#40;string&#41;&#41;&#10;  purpose                       &#61; optional&#40;string, &#34;ENCRYPT_DECRYPT&#34;&#41;&#10;  skip_initial_version_creation &#61; optional&#40;bool, false&#41;&#10;  version_template &#61; optional&#40;object&#40;&#123;&#10;    algorithm        &#61; string&#10;    protection_level &#61; optional&#40;string, &#34;SOFTWARE&#34;&#41;&#10;  &#125;&#41;&#41;&#10;  iam &#61; optional&#40;map&#40;list&#40;string&#41;&#41;, &#123;&#125;&#41;&#10;  iam_bindings &#61; optional&#40;map&#40;object&#40;&#123;&#10;    members &#61; list&#40;string&#41;&#10;    role    &#61; string&#10;    condition &#61; optional&#40;object&#40;&#123;&#10;      expression  &#61; string&#10;      title       &#61; string&#10;      description &#61; optional&#40;string&#41;&#10;    &#125;&#41;&#41;&#10;  &#125;&#41;&#41;, &#123;&#125;&#41;&#10;  iam_bindings_additive &#61; optional&#40;map&#40;object&#40;&#123;&#10;    member &#61; string&#10;    role   &#61; string&#10;    condition &#61; optional&#40;object&#40;&#123;&#10;      expression  &#61; string&#10;      title       &#61; string&#10;      description &#61; optional&#40;string&#41;&#10;    &#125;&#41;&#41;&#10;  &#125;&#41;&#41;, &#123;&#125;&#41;&#10;&#125;&#41;&#41;">map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> |  | <code title="&#123;&#10;  &#34;key-gke&#34; &#61; &#123;&#10;    rotation_period            &#61; &#34;7776000s&#34;&#10;    destroy_scheduled_duration &#61; &#34;2592000s&#34;&#10;    labels &#61; &#123;&#10;      team &#61; &#34;gke-team&#34;&#10;    &#125;&#10;    version_template &#61; &#123;&#10;      algorithm        &#61; &#34;GOOGLE_SYMMETRIC_ENCRYPTION&#34;&#10;      protection_level &#61; &#34;SOFTWARE&#34;&#10;    &#125;&#10;    lifecycle &#61; &#123;&#10;      prevent_destroy &#61; true&#10;    &#125;&#10;  &#125;&#10;&#125;">&#123;&#8230;&#125;</code> |
| [node_machine_type](variables.tf#L143) | The Node Machine type to be used in the NodePool. | <code>string</code> |  | <code>&#34;n2d-standard-2&#34;</code> |
| [policy_controller_exemptable_namespaces](variables.tf#L158) | The exemted namespaces for policy controller. | <code>list&#40;any&#41;</code> |  | <code>&#91;&#93;</code> |
| [source_branch](variables.tf#L177) | The branch of the repository used for config sync gitops. | <code>string</code> |  | <code>&#34;main&#34;</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [cluster_master_version](outputs.tf#L1) | Master version. |  |
| [gke_cluster_endpoint](outputs.tf#L6) | The endpoint of the GKE cluster. |  |
| [gke_cluster_name](outputs.tf#L11) | The name of the GKE cluster. |  |
| [keyring_id](outputs.tf#L16) | Fully qualified keyring id. |  |
| [keyring_location](outputs.tf#L21) | Keyring location. |  |
| [keyring_name](outputs.tf#L26) | Keyring name. |  |
| [keyring_resource](outputs.tf#L31) | Keyring resource. |  |
| [keyrings_keys](outputs.tf#L36) | Key resources. |  |
| [nodepool_id](outputs.tf#L41) | Fully qualified nodepool id. |  |
| [nodepool_name](outputs.tf#L46) | Nodepool name. |  |
| [nodepool_service_account_email](outputs.tf#L51) | Service account email. |  |
| [subnet_regions](outputs.tf#L56) | Map of subnet regions keyed by name. |  |
| [subnets](outputs.tf#L61) | Subnet resources. |  |
| [vpc-network](outputs.tf#L66) | Network resource. |  |
| [vpc-subnet_ids](outputs.tf#L71) | Map of subnet IDs keyed by name. |  |
| [vpc-subnet_ips](outputs.tf#L76) | Map of subnet address ranges keyed by name. |  |
<!-- END TFDOC -->
