# Syslog collector blueprint

<!-- BEGIN TOC -->
- [1 Collector overview](#1-collector-overview)
- [2 Architecture scope](#2-architecture-scope)
- [3 Security controls](#3-security-controls)
- [4 Deployment prerequisites](#4-deployment-prerequisites)
- [5 Deployment steps](#5-deployment-steps)
- [6 Verification steps](#6-verification-steps)
- [Variables](#variables)
- [Outputs](#outputs)
<!-- END TOC -->

## 1 Collector overview

Deploy a highly available, mutual TLS syslog collector tier inside a FedRAMP High or DoD IL5 Assured Workloads environment. Collector instances receive RFC 5425 TLS syslog streams over TCP port `6514` behind a regional internal passthrough network load balancer and forward structured JSON entries to Cloud Logging.

The collector avoids persisting private key material in Terraform state, Compute Engine metadata, startup scripts, outputs, or boot disks. Each instance retrieves its TLS server certificate, server private key, and client certificate authority bundle directly from Regional CMEK Secret Manager into a RAM-backed `tmpfs` directory at `/run/fluent-bit-tls` on boot.

## 2 Architecture scope

This blueprint composes reusable repository modules to deploy a private regional collector fleet:

- Project API enablement (`enable_apis = true` by default) for Compute Engine, Cloud Logging, Cloud Monitoring, and Secret Manager, paired with a 60-second IAM propagation wait before CMEK key bindings and instance templates execute on fresh projects.
- A dedicated service account created with [`modules/iam-service-account`](../../../modules/iam-service-account) holds only `roles/logging.logWriter`, `roles/monitoring.metricWriter`, and per-secret `roles/secretmanager.secretAccessor` bindings.
- A regional Compute Engine instance template created with [`modules/compute-vm`](../../../modules/compute-vm) provisions private AMD SEV Confidential VMs with Shielded VM controls, CMEK boot disks, OS Login, disabled serial ports, and a pre-baked golden image.
- A regional Managed Instance Group created with [`modules/compute-mig`](../../../modules/compute-mig) maintains at least two instances across zones with `PROACTIVE` rolling replacement, zero unavailable instances during updates, and active HTTP autohealing against `/api/v1/health`.
- A regional internal passthrough network load balancer created with [`modules/net-lb-int`](../../../modules/net-lb-int) exposes only the configured TLS syslog TCP port, enables backend connection logging, and runs a dedicated regional HTTP health check.
- Service-account-targeted ingress firewall rules created with [`modules/net-vpc-firewall`](../../../modules/net-vpc-firewall) permit traffic only from approved client CIDR ranges on the syslog port and from Google Cloud health check ranges `35.191.0.0/16` and `130.211.0.0/22` on the health check port with `INCLUDE_ALL_METADATA` logging.

## 3 Security controls

This configuration enforces runtime and infrastructure guardrails aligned with FedRAMP High and DoD IL5 requirements:

- Regional Secret Manager secrets keep TLS key material outside Terraform variables, state files, instance metadata, and persistent disks.
- Startup initialization fails closed when `/run` is not a `tmpfs` mount or when pre-baked `fluent-bit` and `gcloud` binaries are absent, copies `/opt/fluent-bit/etc/parsers.conf` into `/etc/fluent-bit/parsers.conf` when needed for `/opt/fluent-bit` builds, and prevents unverified runtime downloads.
- Fluent Bit enforces RFC 5425 octet-counting framing by default via `Format octet_counting`, TLS 1.2 or higher, and mutual TLS client certificate verification via `tls.verify_client_cert On` on the TCP syslog listener, validates configuration with `--dry-run` before service restart, and keeps `firewalld` policies intact without flushing `nftables`.
- Plan-time variable validations reject wildcard `0.0.0.0/0` or `::/0` client CIDR ranges, single-replica non-HA sizing, privileged (`< 1024`) or colliding port numbers so non-root `fluent-bit.service` units never fail `bind()` with `EACCES`, unsupported framing formats, non-SEV or non-existent custom machine types, global or cross-region Cloud KMS keys, and inline PEM strings in secret ID inputs.

## 4 Deployment prerequisites

1. Deploy the workload project inside a FedRAMP High or DoD IL5 Assured Workloads folder. When `enable_apis = true` (default), Terraform enables `compute.googleapis.com`, `logging.googleapis.com`, `monitoring.googleapis.com`, and `secretmanager.googleapis.com` on `project_id`; ensure `cloudkms.googleapis.com` is enabled on the Cloud KMS host project.
2. Bake a hardened golden image containing Fluent Bit `>= 5.0`, with `>= 5.1.3` recommended for `tls.verify_client_cert On` support, plus `gcloud` and `fluent-bit.service` configured for your operating system baseline.
3. Provision three Regional CMEK Secret Manager secrets in `var.region` using [`modules/secret-manager`](../../../modules/secret-manager) or your enterprise certificate pipeline, and populate versions for the server certificate, server private key, and client CA bundle.
4. Enable Private Google Access on `subnetwork_name` and configure Cloud DNS private zones in `network_name` routing both `*.googleapis.com` and regional `*.rep.googleapis.com` (such as `secretmanager.<region>.rep.googleapis.com`) to `restricted.googleapis.com` (`199.36.153.4/30`) or `private.googleapis.com` (`199.36.153.8/30`) so private-only collector VMs (`nat = false`) reach Regional Secret Manager, Cloud Logging, and Cloud Monitoring without internet egress.
5. When `network_project_id` differs from `project_id`, either set `grant_shared_vpc_subnet_iam = true` or centrally grant `roles/compute.networkUser` on `subnetwork_name` to both the collector service account and `<project_number>@cloudservices.gserviceaccount.com` so the regional MIG can create instances.
6. Ensure your Terraform toolchain satisfies the version constraints declared in [`versions.tf`](versions.tf) and your deploying identity holds permissions to manage Compute Engine, IAM, Secret Manager IAM, and Shared VPC firewall rules.

## 5 Deployment steps

1. Copy [`terraform.tfvars.sample`](terraform.tfvars.sample) to `terraform.tfvars` and populate your workload project ID, Shared VPC project and network details, Cloud KMS key ID, pre-baked golden image path, Regional Secret Manager secret IDs, and authorized syslog client CIDR ranges.
2. Initialize, review, and apply the Terraform configuration:

```bash
terraform init
terraform plan
terraform apply
```

3. Point authorized syslog shippers at the `ilb_ip_address` output on the configured `syslog_port` using client certificates signed by the CA stored in `tls_secret_ids.client_ca_cert`.

## 6 Verification steps

1. Confirm that the regional MIG reports at least `min_replicas` healthy instances across zones and that the internal load balancer backend reports healthy targets.
2. Verify from an authorized client subnet that a mutual TLS handshake against the `ilb_ip_address` endpoint succeeds with a valid client certificate and rejects connections without a trusted client certificate or below TLS 1.2.
3. Confirm that structured syslog records appear in Cloud Logging under the target `project_id` and that `/run/fluent-bit-tls/server.key` on collector instances resides on `tmpfs` with mode `0600`.
<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [allowed_source_ranges](variables.tf#L15) | CIDR ranges permitted to send RFC 5425 TLS syslog traffic. | <code>list&#40;string&#41;</code> | ✓ |  |
| [golden_image](variables.tf#L89) | Hardened Compute Engine golden image with Fluent Bit. | <code>string</code> | ✓ |  |
| [kms_key_id](variables.tf#L171) | Regional Cloud KMS CryptoKey ID in var.region for boot disks. | <code>string</code> | ✓ |  |
| [network_name](variables.tf#L277) | Name of the existing VPC network in var.network_project_id. | <code>string</code> | ✓ |  |
| [network_project_id](variables.tf#L290) | Project ID hosting the Shared VPC network and firewall rules. | <code>string</code> | ✓ |  |
| [project_id](variables.tf#L303) | Workload project ID hosting the collector MIG, ILB, and SA. | <code>string</code> | ✓ |  |
| [region](variables.tf#L316) | US Google Cloud region for MIG, ILB, and regional secrets. | <code>string</code> | ✓ |  |
| [subnetwork_name](variables.tf#L344) | Name of the regional subnetwork in var.network_project_id. | <code>string</code> | ✓ |  |
| [tls_secret_ids](variables.tf#L392) | Regional CMEK Secret Manager IDs for TLS cert, key, and CA. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> | ✓ |  |
| [boot_disk_size_gb](variables.tf#L44) | Size in GiB for each CMEK-encrypted collector boot disk. | <code>number</code> |  | <code>50</code> |
| [distribution_zones](variables.tf#L60) | Optional list of at least two compute zones in var.region. | <code>list&#40;string&#41;</code> |  | <code>null</code> |
| [enable_apis](variables.tf#L82) | Enable required Google Cloud APIs on var.project_id. | <code>bool</code> |  | <code>true</code> |
| [grant_shared_vpc_subnet_iam](variables.tf#L109) | Grant Shared VPC subnet networkUser IAM to collector agents. | <code>bool</code> |  | <code>false</code> |
| [health_check_port](variables.tf#L116) | Unprivileged TCP port for Fluent Bit /api/v1/health. | <code>number</code> |  | <code>2020</code> |
| [ilb_global_access](variables.tf#L139) | Allow clients in other regions to reach the ILB VIP. | <code>bool</code> |  | <code>false</code> |
| [ilb_ip_address](variables.tf#L146) | Optional static internal IPv4 address or self-link for ILB. | <code>string</code> |  | <code>null</code> |
| [labels](variables.tf#L196) | Labels applied to collector Compute Engine and ILB resources. | <code>map&#40;string&#41;</code> |  | <code>&#123;&#125;</code> |
| [machine_type](variables.tf#L203) | AMD SEV-compatible machine type for collector instances. | <code>string</code> |  | <code>&#34;n2d-standard-2&#34;</code> |
| [manage_kms_iam](variables.tf#L224) | Grant Cloud KMS encrypter/decrypter IAM to Compute agent. | <code>bool</code> |  | <code>true</code> |
| [max_replicas](variables.tf#L231) | Maximum collector instances maintained by the autoscaler. | <code>number</code> |  | <code>6</code> |
| [min_replicas](variables.tf#L246) | Minimum collector instances maintained across zones for HA. | <code>number</code> |  | <code>2</code> |
| [name_prefix](variables.tf#L261) | Lowercase naming prefix applied to collector resources. | <code>string</code> |  | <code>&#34;syslog-collector&#34;</code> |
| [secret_project_id](variables.tf#L327) | Optional project ID hosting Regional Secret Manager secrets. | <code>string</code> |  | <code>null</code> |
| [syslog_framing_format](variables.tf#L357) | TCP framing format for RFC 5425 syslog. | <code>string</code> |  | <code>&#34;octet_counting&#34;</code> |
| [syslog_port](variables.tf#L374) | Unprivileged TCP port for RFC 5425 mutual TLS syslog. | <code>number</code> |  | <code>6514</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [ilb_ip_address](outputs.tf#L15) | Internal load balancer IPv4 address for TLS syslog ingestion. |  |
| [instance_group_manager_id](outputs.tf#L20) | Fully qualified ID of the regional managed instance group. |  |
| [service_account_email](outputs.tf#L25) | Email of the dedicated syslog collector service account. |  |
<!-- END TFDOC -->
