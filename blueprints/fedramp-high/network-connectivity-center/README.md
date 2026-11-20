# Network Connectivity Center blueprint

This blueprint creates a Google Cloud Network Connectivity Center hub and attaches existing VPC networks as spokes using `MESH` or `STAR` topologies across multiple projects.

<!-- BEGIN TOC -->
- [1 NCC overview](#1-ncc-overview)
- [2 Compliance scope](#2-compliance-scope)
- [3 Prerequisites](#3-prerequisites)
- [4 Deployment steps](#4-deployment-steps)
- [5 Deployment verification](#5-deployment-verification)
- [6 Operational notes](#6-operational-notes)
- [Variables](#variables)
- [Outputs](#outputs)
<!-- END TOC -->

## 1 NCC overview

Network Connectivity Center provides centralized transit and route exchange across spoke resources connected to a hub. Attaching existing Google Cloud VPC networks as spokes unifies multi-project connectivity under either full-mesh or hub-and-spoke group policies.

## 2 Compliance scope

- Deploy this blueprint inside a FedRAMP High or IL5 Assured Workloads folder within your Google Cloud organization.
- Assured Workloads enforces regional data residency and security guardrails required for federal and defense workloads.

## 3 Prerequisites

Verify that the following projects, networks, and IAM roles are in place before applying Terraform:

- Identify `main_project_id` to host the Network Connectivity Center hub and any host projects containing spoke VPC networks.
- Provision all spoke VPC networks ahead of time and collect their full self-links in `projects/<project-id>/global/networks/<vpc-name>` format.
- Grant the deploying identity `roles/networkconnectivity.admin`, `roles/compute.networkAdmin`, `roles/serviceusage.serviceUsageAdmin`, and `roles/resourcemanager.projectIamAdmin` on `main_project_id`, plus `roles/networkconnectivity.admin` on every project hosting an attached VPC spoke.

## 4 Deployment steps

1. Copy the sample variables file and update `terraform.tfvars` with your hub project ID, `ncc_hub_name`, `topology`, and `spokes` VPC self-links:

```bash
cp terraform.tfvars.sample terraform.tfvars
```

2. Initialize the Terraform working directory:

```bash
terraform init
```

3. Review the execution plan:

```bash
terraform plan
```

4. Apply the configuration to create the hub and attach VPC spokes:

```bash
terraform apply
```

5. Run `terraform destroy` if you need to remove the Network Connectivity Center hub and spoke attachments:

```bash
terraform destroy
```

## 5 Deployment verification

Confirm the hub and attached VPC spokes in the Google Cloud console or with the `gcloud` CLI:

- In the Google Cloud console, open Network Connectivity Center in `main_project_id`, select the hub named by `ncc_hub_name`, and verify on the Spokes tab that every VPC from `spokes` is attached.
- Inspect the hub and list attached spokes from the command line:

```bash
gcloud network-connectivity hubs describe <NCC_HUB_NAME> --project=<MAIN_PROJECT_ID>
gcloud network-connectivity spokes list --hub=<NCC_HUB_NAME> --project=<MAIN_PROJECT_ID>
```

## 6 Operational notes

- This blueprint attaches VPC spokes only; see the [Network Connectivity Center overview](https://cloud.google.com/network-connectivity/docs/network-connectivity-center/concepts/overview) for Cloud VPN, Cloud Interconnect, and router appliance spokes.
- Under `STAR` topology, VPCs residing in `main_project_id` join the `center` group while VPCs in other projects join the `edge` group; under `MESH` topology, all spokes join the `default` group.
- Set `psc_prop = true` to enable Private Service Connect [connection propagation](https://cloud.google.com/network-connectivity/docs/network-connectivity-center/concepts/psc-propagated-connection-overview) across spokes.

<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [gcp_region](variables.tf#L15) | The Google Cloud region to be used as the default for regional resources and the provider. Note: NCC Hubs are global resources. | <code>string</code> | ✓ |  |
| [main_project_id](variables.tf#L20) | The Google Cloud Project ID where the NCC hub will be created. | <code>string</code> | ✓ |  |
| [ncc_hub_name](variables.tf#L25) | The name of the created Network Connectivity Center hub. | <code>string</code> |  | <code>&#34;example-ncc-hub&#34;</code> |
| [psc_prop](variables.tf#L31) | Whether or not Private Service Connect connections can be propagated to other spokes in the network. | <code>bool</code> |  | <code>false</code> |
| [spokes](variables.tf#L37) | A map of spoke names to VPC Network self-links (e.g., 'projects/<PROJECT_ID>/global/networks/<VPC_NAME>') to be added to the NCC hub. | <code>map&#40;string&#41;</code> |  | <code>&#123;&#125;</code> |
| [topology](variables.tf#L44) | The topology of the network. Can be MESH or STAR. | <code>string</code> |  | <code>&#34;MESH&#34;</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [hub](outputs.tf#L15) | The NCC hub ID. |  |
| [spokes](outputs.tf#L20) | The NCC spokes. |  |
<!-- END TFDOC -->
