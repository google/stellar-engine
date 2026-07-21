# ACAS SecurityCenter Deployment

This blueprint deploys the **ACAS SecurityCenter (Tenable.sc)** on Google Cloud.

SecurityCenter is deployed as a Shielded VM with OS Login explicitly enabled (blocking project-wide SSH keys) and optional Confidential Compute (AMD SEV) enabled. It includes a dedicated CMEK-encrypted data disk for vulnerability data, and boots from a Golden Image produced by the [`acas/image-factory`](../../image-factory/README.md).

> [!NOTE]
> When using a hardened base image (such as the CIS RHEL 8 STIG image), Confidential Compute (AMD SEV) must be disabled by setting `enable_confidential_compute = false` in `terraform.tfvars`. The security settings and custom kernel drivers in hardened OS images can cause silent boot failures when running as Confidential VMs.

> **Run `acas/image-factory` first** to build the SecurityCenter Golden Image before applying this blueprint.

<!-- BEGIN TOC -->
- [Accessing SecurityCenter](#accessing-securitycenter)
- [Linking Scanners](#linking-scanners)
- [Variables](#variables)
- [Outputs](#outputs)
<!-- END TOC -->

## Accessing SecurityCenter

**SecurityCenter Web UI (via IAP port forwarding)**
```bash
# 1. Start the web UI tunnel (keep this terminal open)
gcloud compute start-iap-tunnel acas-securitycenter 443 \
  --local-host-port=localhost:8443 \
  --project=xxxx-xxxx-xxxx-main-0 \
  --zone=us-east4-a

# 2. Then open https://localhost:8443 in your web browser
```

**SSH (via IAP)**
```bash
# In a separate terminal window:
gcloud compute ssh acas-securitycenter \
  --project=xxxx-xxxx-xxxx-main-0 \
  --zone=us-east4-a \
  --tunnel-through-iap
```

## Linking Scanners

To link Nessus Scanners deployed via the `scanner/` blueprint to this SecurityCenter:
1. Ensure both the SC and Scanner blueprints have been applied.
2. Note the `scanner_internal_ips` output from the `scanner/` blueprint.
3. Log into the SecurityCenter Web UI.
4. Navigate to **Resources → Nessus Scanners**, click **Add**, and enter the Scanner's internal IP.
<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [image](variables.tf#L41) | The Golden Image to use for SecurityCenter. | <code>string</code> | ✓ |  |
| [kms_key_name](variables.tf#L52) | Name of the KMS crypto key for disk encryption. | <code>string</code> | ✓ |  |
| [kms_keyring_name](variables.tf#L57) | Name of the KMS keyring used for disk encryption. | <code>string</code> | ✓ |  |
| [kms_project_id](variables.tf#L62) | Project ID where the KMS keyring resides (may differ from project_id in hub-and-spoke KMS architectures). | <code>string</code> | ✓ |  |
| [network_name](variables.tf#L73) | VPC network name. | <code>string</code> | ✓ |  |
| [network_project_id](variables.tf#L78) | Project ID that hosts the VPC (same as project_id for non-Shared VPC). | <code>string</code> | ✓ |  |
| [project_id](variables.tf#L83) | GCP project ID where SC resources will be created. | <code>string</code> | ✓ |  |
| [subnetwork_name](variables.tf#L106) | VPC subnetwork name. | <code>string</code> | ✓ |  |
| [boot_disk_size](variables.tf#L17) | Boot disk size in GB. | <code>number</code> |  | <code>100</code> |
| [data_disk_size](variables.tf#L23) | Additional data disk size in GB. | <code>number</code> |  | <code>500</code> |
| [enable_confidential_compute](variables.tf#L29) | Enable Confidential Compute for the SecurityCenter VM. | <code>bool</code> |  | <code>true</code> |
| [iap_source_ranges](variables.tf#L35) | List of IP ranges allowed to connect via Identity-Aware Proxy (IAP). | <code>list&#40;string&#41;</code> |  | <code>&#91;&#34;35.235.240.0&#47;20&#34;&#93;</code> |
| [instance_name](variables.tf#L46) | Name of the SecurityCenter instance. | <code>string</code> |  | <code>&#34;acas-securitycenter&#34;</code> |
| [machine_type](variables.tf#L67) | Machine type for the SecurityCenter instance. | <code>string</code> |  | <code>&#34;n2d-standard-8&#34;</code> |
| [region](variables.tf#L88) | GCP region for deployment. | <code>string</code> |  | <code>&#34;us-east4&#34;</code> |
| [sc_mgmt_source_ranges](variables.tf#L94) | List of IP ranges allowed to access the SecurityCenter Web UI (port 443). | <code>list&#40;string&#41;</code> |  | <code>&#91;&#34;10.0.0.0&#47;8&#34;&#93;</code> |
| [service_account_id](variables.tf#L100) | Service account ID for SC VM. | <code>string</code> |  | <code>&#34;acas-sc-sa&#34;</code> |
| [zone](variables.tf#L111) | GCP zone for the SC VM. | <code>string</code> |  | <code>&#34;us-east4-a&#34;</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [internal_ip](outputs.tf#L17) | Internal IP of the ACAS SecurityCenter instance. |  |
| [service_account_email](outputs.tf#L22) | Service account email attached to SecurityCenter. |  |
<!-- END TFDOC -->
