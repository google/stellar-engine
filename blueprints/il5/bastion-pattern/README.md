# Bastion pattern blueprint

<!-- BEGIN TOC -->
- [1 Bastion overview](#1-bastion-overview)
- [2 Blueprint scope](#2-blueprint-scope)
- [3 Compliance scope](#3-compliance-scope)
- [4 Prerequisites](#4-prerequisites)
- [5 Deployment steps](#5-deployment-steps)
- [6 Bastion host connection](#6-bastion-host-connection)
- [Variables](#variables)
- [Outputs](#outputs)
<!-- END TOC -->

## 1 Bastion overview

A bastion host centralizes administrative SSH and local port-forwarding access into private VPC networks that block direct internet ingress and egress. Operators establish an Identity-Aware Proxy SSH tunnel through the bastion VM to reach internal web consoles and management interfaces without exposing public IP addresses, while CMEK disk encryption uses `roles/cloudkms.cryptoKeyEncrypterDecrypter` on the configured Cloud KMS key.

## 2 Blueprint scope

This blueprint provisions a CMEK-encrypted Compute Engine bastion VM, least-privilege service account, and VPC ingress firewall rule on an existing Shared VPC subnet.

## 3 Compliance scope

- Deploy this blueprint inside a FedRAMP High or IL5 Assured Workloads folder within your Google Cloud organization.
- Assured Workloads enforces regional data residency and encryption guardrails required for federal and defense workloads.

## 4 Prerequisites

1. Identify your workload (`main_project_id`), Shared VPC host (`network_project_id`), and KMS (`core_project_id`) Google Cloud project IDs.
2. Ensure the target [project](https://cloud.google.com/resource-manager/docs/creating-managing-projects) has [billing enabled](https://cloud.google.com/billing/docs/how-to/modify-project) and your deploying identity holds required [IAM](https://cloud.google.com/iam) roles, following [Granting, changing, and revoking access](https://cloud.google.com/iam/docs/granting-changing-revoking-access#grant-single-role).

## 5 Deployment steps

1. Copy `terraform.tfvars.sample` to `terraform.tfvars` and configure your project IDs, VPC network and subnet, Cloud KMS key self-link, instance settings, and allowed firewall source ranges.
2. Initialize and apply the Terraform configuration:

```bash
terraform init
terraform plan
terraform apply
```

Applying the configuration outputs the bastion service account email and VPC network and subnet self-links:

```text
Apply complete! Resources: 6 added, 0 changed, 0 destroyed.

Outputs:

compute_service_account_email = "compute-engine-sa@xxxx-xxxx-xxxx-main-0.iam.gserviceaccount.com"
subnet_self_link              = "https://www.googleapis.com/compute/v1/projects/xxxx-xxxx-net-host/regions/us-east4/subnetworks/default-us-east4"
vpc_self_link                 = "https://www.googleapis.com/compute/v1/projects/xxxx-xxxx-net-host/global/networks/xxxx-spoke-0"
```

## 6 Bastion host connection

Follow these steps to forward local ports to internal web services through the bastion host over Identity-Aware Proxy:

1. Set the active `gcloud` project to the project hosting the bastion VM:

```bash
gcloud config set project <your-project-id>
```

2. Open an IAP-tunneled SSH session with local port forwarding to the target internal IP and ports:

```bash
gcloud compute ssh <your-bastion-host-name> --zone <your-zone> --tunnel-through-iap --project <your-project-id> -- \
-L 8443:<target-internal-ip>:<remote-port1> \
-L 8444:<target-internal-ip>:<remote-port2> \
-L 8445:<target-internal-ip>:<remote-port3>
```

For example, to forward local ports `8443`, `8444`, and `8445` to remote ports `443`, `8443`, and `8444` on `192.168.1.10`:

```bash
gcloud compute ssh management-bastion --zone us-east4-a --tunnel-through-iap --project my-main-project -- \
-L 8443:192.168.1.10:443 \
-L 8444:192.168.1.10:8443 \
-L 8445:192.168.1.10:8444
```

- Flag `-L 8443:192.168.1.10:443` forwards local port `8443` to remote port `443`.
- Flag `-L 8444:192.168.1.10:8443` forwards local port `8444` to remote port `8443`.
- Flag `-L 8445:192.168.1.10:8444` forwards local port `8445` to remote port `8444`.

3. Open `https://localhost:8443`, `https://localhost:8444`, or `https://localhost:8445` in your browser while the SSH tunnel remains active.

<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [allowed_firewall_ports](variables.tf#L17) | The allowed ports for the firewall. | <code>list&#40;string&#41;</code> | ✓ |  |
| [allowed_source_ranges](variables.tf#L22) | These are the allowed source ranges. | <code>list&#40;string&#41;</code> | ✓ |  |
| [compute_service_account_id](variables.tf#L27) | This is the compute service account id. | <code>string</code> | ✓ |  |
| [core_project_id](variables.tf#L32) | Core project ID. | <code>string</code> | ✓ |  |
| [disk_name](variables.tf#L37) | This is the disk name. | <code>string</code> | ✓ |  |
| [instance_name](variables.tf#L48) | This is the instance name. | <code>string</code> | ✓ |  |
| [kms_key_name](variables.tf#L59) | The full self-link (projects/../locations/../keyRings/../cryptoKeys/..) of the existing KMS key to use for disk encryption. | <code>string</code> | ✓ |  |
| [kms_keyring_name](variables.tf#L64) | Keyring attributes. | <code>string</code> | ✓ |  |
| [main_project_id](variables.tf#L69) | This is the ID of project. | <code>string</code> | ✓ |  |
| [network_name](variables.tf#L74) | VPC to use. | <code>string</code> | ✓ |  |
| [network_project_id](variables.tf#L79) | Project that the Compute Engine VPC is located. | <code>string</code> | ✓ |  |
| [region](variables.tf#L84) | GCP Region to deploy into. | <code>string</code> | ✓ |  |
| [subnetwork_name](variables.tf#L89) | Subnet to use. | <code>string</code> | ✓ |  |
| [zone](variables.tf#L94) | This is the zone of the instance. | <code>string</code> | ✓ |  |
| [image](variables.tf#L42) | Disk image. | <code>string</code> |  | <code>&#34;cos-cloud&#47;cos-stable&#34;</code> |
| [instance_type](variables.tf#L53) | Instance type. | <code>string</code> |  | <code>&#34;n2d-standard-2&#34;</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [compute_service_account_email](outputs.tf#L17) | The email of the compute service account. |  |
| [subnet_self_link](outputs.tf#L22) | The self link of the subnet. |  |
| [vpc_self_link](outputs.tf#L27) | The self link of the VPC. |  |
<!-- END TFDOC -->
