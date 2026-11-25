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

A bastion host centralizes administrative SSH and local port-forwarding access into private VPC networks that block direct internet ingress and egress. Operators connect either through an Identity-Aware Proxy SSH tunnel when `access_mode` is `iap` or from private DoD source ranges over Boundary Cloud Access Point when `access_mode` is `bcap`, without exposing public IP addresses, while CMEK disk encryption uses `roles/cloudkms.cryptoKeyEncrypterDecrypter` on the configured Cloud KMS key.

## 2 Blueprint scope

This blueprint provisions one primary hardened bastion VM and optional additional multi-role or per-tenant bastion VMs through `additional_bastions` on an existing Shared VPC subnet. Every bastion host enforces Confidential Compute SEV, Shielded VM, CMEK disk encryption, 14-day daily snapshots, disabled serial port access, OS Login, blocked project SSH keys, an optional static internal IPv4 address, least-privilege observability IAM grants, and a service-account-targeted VPC ingress firewall rule with full metadata logging.

## 3 Compliance scope

- Deploy this blueprint inside a FedRAMP High or IL5 Assured Workloads folder within your Google Cloud organization.
- Assured Workloads enforces regional data residency and encryption guardrails required for federal and defense workloads.
- Plan-time validations reject blanket ingress ranges with prefix length under `/8` and block any IPv4 CIDR overlapping the Identity-Aware Proxy range `35.235.240.0/20` when `access_mode` is `bcap`.

## 4 Prerequisites

1. Identify your workload `main_project_id`, Shared VPC host `network_project_id`, and KMS `core_project_id` Google Cloud project IDs.
2. Ensure the target [project](https://cloud.google.com/resource-manager/docs/creating-managing-projects) has [billing enabled](https://cloud.google.com/billing/docs/how-to/modify-project) and your deploying identity holds required [IAM](https://cloud.google.com/iam) roles, following [Granting, changing, and revoking access](https://cloud.google.com/iam/docs/granting-changing-revoking-access#grant-single-role).
3. When `enable_observability_iam` is `true`, ensure your deploying identity holds `resourcemanager.projects.setIamPolicy` on `main_project_id`. Upgrading an existing deployment from an earlier version creates two `google_project_iam_member` bindings (`roles/logging.logWriter` and `roles/monitoring.metricWriter`) for `google_service_account.compute`. Restricted or brownfield deployers can set `enable_observability_iam = false` to manage those bindings out of band.

## 5 Deployment steps

1. Copy `terraform.tfvars.sample` to `terraform.tfvars` and configure your project IDs, VPC network and subnet, Cloud KMS key name, instance settings, `access_mode`, optional `static_internal_ip`, optional `additional_bastions`, and allowed firewall source ranges.
2. Initialize and apply the Terraform configuration:

```bash
terraform init
terraform plan
terraform apply
```

Applying the configuration outputs the bastion service account email, internal IP address, optional additional bastion details, and VPC network and subnet self-links:

```text
Apply complete! Resources: 8 added, 0 changed, 0 destroyed.

Outputs:

additional_bastions           = {}
compute_service_account_email = "compute-engine-sa@my-main-project.iam.gserviceaccount.com"
internal_ip                   = "10.0.0.10"
subnet_self_link              = "https://www.googleapis.com/compute/v1/projects/my-net-host/regions/us-east4/subnetworks/default-us-east4"
vpc_self_link                 = "https://www.googleapis.com/compute/v1/projects/my-net-host/global/networks/my-spoke-0"
```

## 6 Bastion host connection

Follow these steps to forward local ports to internal web services through the bastion host over Identity-Aware Proxy when `access_mode` is `iap`:

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

When `access_mode` is `bcap`, connect over the private BCAP network path directly to the bastion internal IP address from an authorized source range in `allowed_source_ranges`.
<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [allowed_firewall_ports](variables.tf#L165) | The allowed ports for the firewall. | <code>list&#40;string&#41;</code> | ✓ |  |
| [allowed_source_ranges](variables.tf#L170) | Allowed ingress CIDR ranges for the primary bastion firewall rule. Must be non-empty, use prefix length >= 8, and not overlap the IAP range 35.235.240.0/20 when access_mode is 'bcap'. | <code>list&#40;string&#41;</code> | ✓ |  |
| [compute_service_account_id](variables.tf#L210) | This is the compute service account id. | <code>string</code> | ✓ |  |
| [core_project_id](variables.tf#L215) | Core project ID. | <code>string</code> | ✓ |  |
| [disk_name](variables.tf#L220) | This is the disk name. | <code>string</code> | ✓ |  |
| [instance_name](variables.tf#L238) | This is the instance name. | <code>string</code> | ✓ |  |
| [kms_key_name](variables.tf#L249) | The Cloud KMS crypto key name within kms_keyring_name. | <code>string</code> | ✓ |  |
| [kms_keyring_name](variables.tf#L254) | Keyring attributes. | <code>string</code> | ✓ |  |
| [main_project_id](variables.tf#L259) | This is the ID of project. | <code>string</code> | ✓ |  |
| [network_name](variables.tf#L264) | VPC to use. | <code>string</code> | ✓ |  |
| [network_project_id](variables.tf#L269) | Project that the Compute Engine VPC is located. | <code>string</code> | ✓ |  |
| [region](variables.tf#L274) | GCP Region to deploy into. | <code>string</code> | ✓ |  |
| [subnetwork_name](variables.tf#L295) | Subnet to use. | <code>string</code> | ✓ |  |
| [zone](variables.tf#L300) | This is the zone of the instance. | <code>string</code> | ✓ |  |
| [access_mode](variables.tf#L17) | Ingress access mode for bastion hosts. Allowed values are 'iap' for Identity-Aware Proxy tunneling and 'bcap' for private DoD Boundary Cloud Access Point source ranges. | <code>string</code> |  | <code>&#34;iap&#34;</code> |
| [additional_bastions](variables.tf#L28) | Optional map of additional multi-role or per-tenant bastion hosts. Each entry provisions a dedicated service account, SA-targeted logged firewall rule, and hardened Confidential Compute VM. | <code>map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> |  | <code>&#123;&#125;</code> |
| [enable_observability_iam](variables.tf#L225) | Grant roles/logging.logWriter and roles/monitoring.metricWriter on main_project_id to bastion service accounts. | <code>bool</code> |  | <code>true</code> |
| [image](variables.tf#L232) | Disk image. | <code>string</code> |  | <code>&#34;cos-cloud&#47;cos-stable&#34;</code> |
| [instance_type](variables.tf#L243) | Instance type. | <code>string</code> |  | <code>&#34;n2d-standard-2&#34;</code> |
| [static_internal_ip](variables.tf#L279) | Optional static internal IPv4 address assigned to the primary bastion VM network interface. | <code>string</code> |  | <code>null</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [additional_bastions](outputs.tf#L17) | Details of additional multi-role bastion hosts keyed by additional_bastions key. |  |
| [compute_service_account_email](outputs.tf#L29) | The email of the compute service account. |  |
| [internal_ip](outputs.tf#L34) | The internal IP address of the primary bastion VM. |  |
| [subnet_self_link](outputs.tf#L39) | The self link of the subnet. |  |
| [vpc_self_link](outputs.tf#L44) | The self link of the VPC. |  |
<!-- END TFDOC -->
