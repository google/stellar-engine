# VPC peering project blueprint

This standalone blueprint provisions two Google Cloud VPC networks with regional subnets and establishes an active VPC Network Peering connection between them for environments that do not use Stellar Engine Stage 2 networking.

<!-- BEGIN TOC -->
- [1 VPC peering overview](#1-vpc-peering-overview)
- [2 Compliance scope](#2-compliance-scope)
- [3 Prerequisites](#3-prerequisites)
- [4 Deployment steps](#4-deployment-steps)
- [5 Deployment verification](#5-deployment-verification)
- [6 Operational notes](#6-operational-notes)
- [Variables](#variables)
- [Outputs](#outputs)
<!-- END TOC -->

## 1 VPC peering overview

VPC Network Peering connects two VPC networks privately across internal IPv4 or IPv6 addresses within the same or separate projects and organizations without traversing external IP addresses or VPN tunnels.

## 2 Compliance scope

- Deploy this blueprint inside a FedRAMP High or IL5 Assured Workloads folder within your Google Cloud organization when operating outside Stellar Engine Stage 2.
- Assured Workloads enforces regional data residency and security guardrails required for federal and defense workloads.

## 3 Prerequisites

Verify that the target projects and IAM permissions exist before running Terraform:

- Provision `local_vpc_project_id` and `peer_vpc_project_id_to_create` to host the two VPC networks, which can reference the same project or two separate projects, and set `main_project_id` to manage the peering connection.
- Grant the deploying identity `roles/compute.admin`, `roles/serviceusage.serviceUsageAdmin`, and `roles/resourcemanager.projectIamAdmin` on both `local_vpc_project_id` and `peer_vpc_project_id_to_create` so Terraform can enable `compute.googleapis.com` and create both VPC networks.

## 4 Deployment steps

1. Copy the sample variables file and update `terraform.tfvars` with your project IDs, VPC names, and non-overlapping primary and secondary subnet CIDR ranges:

```bash
cp terraform.tfvars.sample terraform.tfvars
```

2. Initialize the Terraform working directory:

```bash
terraform init
```

3. Review the execution plan for both VPC networks and the bidirectional peering connection:

```bash
terraform plan
```

4. Apply the configuration:

```bash
terraform apply
```

5. Run `terraform destroy` if you need to remove both VPC networks and the peering connection:

```bash
terraform destroy
```

## 5 Deployment verification

Confirm the VPC networks and `ACTIVE` peering state in the Google Cloud console or with the `gcloud` CLI:

- In the Google Cloud console, verify that `local_vpc_name` and `peer_vpc_name_to_create` exist with their configured subnets under VPC networks, and open VPC Network Peering in `main_project_id` to confirm the peering state is `ACTIVE`.
- List peering connections and inspect both VPC networks from the command line:

```bash
gcloud compute network-peering list --project=<MAIN_PROJECT_ID>
gcloud compute networks describe <VPC_NAME> --project=<PROJECT_ID>
```

## 6 Operational notes

- This standalone blueprint creates two new VPC networks rather than peering pre-existing VPCs.
- Do not deploy this blueprint inside a landing zone already managed by Stellar Engine Stage 2 networking, where hub-and-spoke VPCs and peering are centrally provisioned.
- Primary (`local_subnetwork_cidr_*`, `peer_subnetwork_cidr_*`) and secondary CIDR ranges must never overlap across peered VPC networks.
- Keep `gcp_region` consistent with your Assured Workloads regional boundary.

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

