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

# ACAS Nessus Scanner Deployment

This blueprint deploys one or more **ACAS Nessus Scanners** on Google Cloud.

Scanners are deployed as Shielded VMs with OS Login explicitly enabled (blocking project-wide SSH keys) and optional Confidential Compute (AMD SEV) enabled. They boot directly from immutable, CMEK-encrypted Golden Images produced by the [`acas/image-factory`](../../image-factory/README.md).

> [!NOTE]
> When using a hardened base image (such as the CIS RHEL 8 STIG image), Confidential Compute (AMD SEV) must be disabled by setting `enable_confidential_compute = false` in `terraform.tfvars`. The security settings and custom kernel drivers in hardened OS images can cause silent boot failures when running as Confidential VMs.

> **Run `acas/image-factory` first** to build the Scanner Golden Image before applying this blueprint.

<!-- BEGIN TOC -->
- [Accessing the Scanner](#accessing-the-scanner)
- [Connecting to an External SecurityCenter](#connecting-to-an-external-securitycenter)
- [Variables](#variables)
- [Outputs](#outputs)
<!-- END TOC -->

## Accessing the Scanner

**Nessus Web UI (via IAP port forwarding)**
```bash
# 1. Start the web UI tunnel (keep this terminal open)
gcloud compute start-iap-tunnel acas-nessus-scanner-01 8834 \
  --local-host-port=localhost:8834 \
  --project=xxxx-xxxx-xxxx-main-0 \
  --zone=us-east4-a

# 2. Then open https://localhost:8834 in your web browser
```

**SSH (via IAP)**

```bash
# In a separate terminal window:
gcloud compute ssh acas-nessus-scanner-01 \
  --project=xxxx-xxxx-xxxx-main-0 \
  --zone=us-east4-a \
  --tunnel-through-iap
```

## Connecting to an External SecurityCenter

By default, Nessus Scanners must connect to a SecurityCenter (often running in AWS or Azure). To enable cross-cloud communication:

1. Ensure a site-to-site VPN or Cloud Interconnect is active between your GCP VPC and the AWS/Azure environment hosting SecurityCenter.
2. Set the `securitycenter_source_ranges` variable in `terraform.tfvars` to the SecurityCenter's IP range. This controls the `acas-scanner-sc-mgmt` firewall rule that allows port `8834` access.
3. In your SecurityCenter UI, navigate to **Resources → Nessus Scanners**, click **Add**, and enter the scanner's internal IP (`scanner_internal_ips` output).
<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [kms_key_name](variables.tf#L29) | Name of the KMS crypto key for disk encryption. | <code>string</code> | ✓ |  |
| [kms_keyring_name](variables.tf#L34) | Name of the KMS keyring used for disk encryption. | <code>string</code> | ✓ |  |
| [kms_project_id](variables.tf#L39) | Project ID where the KMS keyring resides (may differ from project_id in hub-and-spoke KMS architectures). | <code>string</code> | ✓ |  |
| [network_name](variables.tf#L44) | VPC network name. | <code>string</code> | ✓ |  |
| [network_project_id](variables.tf#L49) | Project ID that hosts the VPC (same as project_id for non-Shared VPC). | <code>string</code> | ✓ |  |
| [project_id](variables.tf#L54) | GCP project ID where scanner resources will be created. | <code>string</code> | ✓ |  |
| [scanner_configs](variables.tf#L71) | Map of ACAS Nessus Scanner instances to create. Keys are logical scanner names. | <code title="map&#40;object&#40;&#123;&#10;  instance_name               &#61; optional&#40;string&#41;&#10;  machine_type                &#61; optional&#40;string, &#34;n2d-standard-2&#34;&#41;&#10;  boot_disk_size              &#61; optional&#40;number, 100&#41;&#10;  image                       &#61; string&#10;  zone                        &#61; optional&#40;string&#41;&#10;  enable_confidential_compute &#61; optional&#40;bool&#41;&#10;&#125;&#41;&#41;">map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> | ✓ |  |
| [subnetwork_name](variables.tf#L95) | VPC subnetwork name. | <code>string</code> | ✓ |  |
| [enable_confidential_compute](variables.tf#L17) | Enable Confidential Compute for the Nessus Scanner VMs. | <code>bool</code> |  | <code>true</code> |
| [iap_source_ranges](variables.tf#L23) | List of IP ranges allowed to connect via Identity-Aware Proxy (IAP). | <code>list&#40;string&#41;</code> |  | <code>&#91;&#34;35.235.240.0&#47;20&#34;&#93;</code> |
| [region](variables.tf#L59) | GCP region for deployment. | <code>string</code> |  | <code>&#34;us-east4&#34;</code> |
| [scan_target_destination_ranges](variables.tf#L65) | List of IP ranges that the Nessus Scanner is allowed to scan. | <code>list&#40;string&#41;</code> |  | <code>&#91;&#34;10.0.0.0&#47;8&#34;&#93;</code> |
| [securitycenter_source_ranges](variables.tf#L83) | List of SecurityCenter IP ranges allowed to connect to the Scanner (port 8834). | <code>list&#40;string&#41;</code> |  | <code>&#91;&#34;10.0.0.0&#47;8&#34;&#93;</code> |
| [service_account_id](variables.tf#L89) | Service account ID for Nessus Scanner VMs. | <code>string</code> |  | <code>&#34;acas-scanner-sa&#34;</code> |
| [zone](variables.tf#L100) | Default GCP zone for scanner VMs. Can be overridden per scanner in scanner_configs. | <code>string</code> |  | <code>&#34;us-east4-a&#34;</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [scanner_internal_ips](outputs.tf#L17) | Map of Nessus Scanner instance names to internal IP addresses. |  |
| [service_account_email](outputs.tf#L22) | Service account email attached to the Nessus Scanner VMs. |  |
<!-- END TFDOC -->
