# Google Virtual Private Cloud (VPC) Project
This blueprint contains all of the necessary Terraform modules to build and deploy a Virtual Private Cloud (VPC) and allows creation and management of VPC networks including VPC Peering.

## Introduction
Google Cloud VPC is global, scalable, and flexible. It provides networking for Compute Engine VM, GKE containers, and the App Engine environment.

1. Enforce the Best Practices for the Google VPC with Subnet CIDR, VPC Peering to the Host Main Project
2. The CIDR's are divided starting from 10.200.12.0/23, Subnet A = 10.200.12.0/25, Subnet B = 10.200.12.0/25, Subnet C = 10.200.12.0/25
3. The VPC is created and it is Peered/Connected to Another Main Landing VPC that is in another Project

## Pre-requisite
1. The Principal (user or group) must have GCP VPC Networking Admin permission at the GCP Level.
2. Have access to the GCP Project ID
3.  You will need an existing [project](https://cloud.google.com/resource-manager/docs/creating-managing-projects) with [billing enabled](https://cloud.google.com/billing/docs/how-to/modify-project) and a user with the "Project owner" [IAM](https://cloud.google.com/iam) role on that project. __Note__: to grant a user a role, take a look at the [Granting and Revoking Access](https://cloud.google.com/iam/docs/granting-changing-revoking-access#grant-single-role) documentation.

## Disclaimer
- The present GCP Terraform Module in this project is set up and intended to be implemented in either a FedRAMP-High or IL5 (Impact Level 5) environment using the Assured Workloads within the Google Cloud Platform (GCP) organization.
- Assured Workloads in both environments ensures that sensitive data and workloads in GCP adhere to the rigorous security standards mandated by the DoD, making it suitable for government agencies.

## How to deploy the Terraform Code. The Deployment Steps
You should see this README and some terraform files.
1. Update the Variables in the variables.tf
2. There is a sample ```terraform.tfvars.sample``` available as well.
3. Although each use case is somehow built around the previous one they are self-contained so you can deploy any of them at your will. The usual terraform commands will do the work:

```bash
terraform init
terraform plan
terraform apply
terraform destroy
```
<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [main_project_id](variables.tf#L17) | The Main Project ID. | <code>string</code> | ✓ |  |
| [network_name](variables.tf#L22) | The name of the VPC. | <code>string</code> | ✓ |  |
| [network_project_id](variables.tf#L28) | Project that the VPC is located. | <code>string</code> | ✓ |  |
| [peer_network_name](variables.tf#L33) | The name of the peering VPC. | <code>string</code> | ✓ |  |
| [peer_project_id](variables.tf#L38) | The peering project ID. | <code>string</code> | ✓ |  |
| [region](variables.tf#L43) | GCP Region to deploy into. | <code>string</code> | ✓ |  |
| [secondary_ip_ranges_cidr_a](variables.tf#L48) | The Secondary IP CIDR. | <code>string</code> | ✓ |  |
| [secondary_ip_ranges_cidr_b](variables.tf#L54) | The Secondary IP CIDR. | <code>string</code> | ✓ |  |
| [subnetwork_cidr_a](variables.tf#L60) | The Subnet CIDR. | <code>string</code> | ✓ |  |
| [subnetwork_cidr_b](variables.tf#L66) | The Subnet CIDR. | <code>string</code> | ✓ |  |
| [subnetwork_cidr_c](variables.tf#L72) | The Subnet CIDR. | <code>string</code> | ✓ |  |
| [subnetwork_prefix_name](variables.tf#L78) | The name of the Subnet Prefix. | <code>string</code> | ✓ |  |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [local_network_peering](outputs.tf#L17) | Network peering resource. |  |
| [peer_network_peering](outputs.tf#L22) | Peer network peering resource. |  |
| [subnet_ipv6_external_prefixes](outputs.tf#L27) | Map of subnet external IPv6 prefixes keyed by name. |  |
| [subnet_regions](outputs.tf#L32) | Map of subnet regions keyed by name. |  |
| [subnet_secondary_ranges](outputs.tf#L37) | Map of subnet secondary ranges keyed by name. |  |
| [subnet_self_links](outputs.tf#L42) | Map of subnet self links keyed by name. |  |
| [subnets](outputs.tf#L47) | Subnet resources. |  |
| [vpc-network](outputs.tf#L52) | Network resource. |  |
| [vpc-network-self_link](outputs.tf#L57) | Network self link. |  |
| [vpc-network_attachment_ids](outputs.tf#L62) | IDs of network attachments. |  |
| [vpc-subnet_ids](outputs.tf#L67) | Map of subnet IDs keyed by name. |  |
| [vpc-subnet_ips](outputs.tf#L72) | Map of subnet address ranges keyed by name. |  |
<!-- END TFDOC -->
