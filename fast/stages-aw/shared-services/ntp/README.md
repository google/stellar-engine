# Shared Services — NTP Relay

This module deploys a DISA STIG-compliant NTP relay in the shared-services VPC.
Relay VMs synchronize against US Naval Observatory (USNO) authoritative sources over the public internet and serve all spoke VMs internally over UDP 123.

## Architecture

```
USNO (192.5.41.40/41/209)            ← Stratum 1
    │  UDP 123 outbound (Cloud NAT)
    ▼
NTP Relay VM in shared-services      ← Stratum 2
    │  UDP 123 internal only
    ▼
All spoke VMs (dev/prod tenants)     ← Stratum 3
```

## Architecture

### VM Relay

A dedicated VM in the shared-services VPC runs `chronyd` and relays time to all spoke VMs.

## STIG Compliance

This module addresses the following DISA STIG rules:

| Rule                       | Requirement                                  | How Met                                                                   |
| -------------------------- | -------------------------------------------- | ------------------------------------------------------------------------- |
| SV-230484 (RHEL-08-030740) | Sync to USNO/DoD/GPS; `maxpoll ≤ 16`         | Relay upstreams to USNO; `maxpoll 6` in chrony.conf (within STIG ceiling) |
| SV-204603 (RHEL-07-040500) | `chronyd` or `ntpd` must be running (CAT II) | Startup script enables and starts `chronyd`                               |

## Spoke VM Configuration

After deployment, configure each spoke VM's `/etc/chrony.conf` to point at the relay IPs output by this module:

```
server <relay-ip> iburst maxpoll 6
```

Remove any existing `metadata.google.internal` or `pool.ntp.org` lines — mixing GCP's leap-smeared source with a strict UTC relay causes unpredictable time behavior.

## Verification

On a relay VM:

```bash
chronyc tracking   # check sync status and offset
chronyc sources    # verify USNO servers are reachable
```

On a spoke VM:

```bash
chronyc sources    # should show relay IP(s) as source
```

## Deployment

Deploy via the shared-services automation script:

```bash
cd automation
bash shared-services-deploy.sh
```

The script walks you through pulling providers from GCS, creating `terraform.tfvars`, and running init/plan/apply. After apply, relay IPs are automatically published to GCS at `tfvars/shared-services-ntp.auto.tfvars.json` for downstream consumption.

Retrieve relay IPs:

```bash
gcloud storage cat gs://<prefix>-<regime>-prod-iac-core-outputs/tfvars/shared-services-ntp.auto.tfvars.json
```

## Notes
## Known Gaps

**VPC Service Controls:** VPC-SC restricts Google Cloud API access, not network-level traffic. NTP relay VMs communicate with USNO via Cloud NAT over UDP 123, which is unaffected by VPC-SC perimeters.

**BCAP routing to USNO:** When BCAP is live and DoD network routes are in place, NTP traffic should route through BCAP instead of the public internet. Set `create_cloud_nat = false` and ensure BCAP advertises routes to USNO IPs (192.5.41.x).

**Multi-region:** This module deploys to a single region. For multi-region deployments, create a second NTP root with its own `terraform.tfvars` targeting the second region.

**Monitoring:** No automated alerting if the relay loses sync or goes offline. Operators should periodically verify with `chronyc tracking` on the relay VM. For automated monitoring, consider Cloud Monitoring uptime checks or Ops Agent integration as a future enhancement.

## Usage

```hcl
module "ntp" {
  source         = "./shared-services/ntp"
  hub_project_id = "my-vdss-host"
  region         = "us-east4"
  network        = module.shared-services-vpc.self_link
  subnetwork     = module.shared-services-vpc.subnet_self_links["us-east4/shared-services-default"]
  encryption_key = module.kms["us-east4"].keys.ntp.id
  automation     = { outputs_bucket = "my-prod-iac-core-outputs" }
}
```
<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [automation](variables.tf#L7) | Automation resources created by the bootstrap stage. Used to write NTP relay IPs to the GCS outputs bucket for downstream consumption. | <code title="object&#40;&#123;&#10;  outputs_bucket &#61; string&#10;&#125;&#41;">object&#40;&#123;&#8230;&#125;&#41;</code> | ✓ |  |
| [encryption_key](variables.tf#L32) | KMS key self-link for CMEK disk encryption on NTP relay VMs. Required for IL5 deployments where constraints/gcp.restrictNonCmekServices is enforced. | <code>string</code> | ✓ |  |
| [hub_project_id](variables.tf#L37) | The GCP project ID where NTP relay resources will be deployed. Must be the project that owns the VPC (the VDSS host project), since Cloud Router, Cloud NAT, and firewall rules cannot cross-project reference networks. | <code>string</code> | ✓ |  |
| [network](variables.tf#L54) | Self-link of the VPC network to attach NTP relay VMs to. | <code>string</code> | ✓ |  |
| [region](variables.tf#L79) | GCP region for NTP relay VM deployment. | <code>string</code> | ✓ |  |
| [subnetwork](variables.tf#L84) | Self-link of the subnetwork to attach NTP relay VMs to. | <code>string</code> | ✓ |  |
| [allowed_client_ranges](variables.tf#L1) | Internal CIDR ranges permitted to query the NTP relay over UDP 123. Defaults to all RFC 1918 space. | <code>list&#40;string&#41;</code> |  | <code>&#91;&#34;10.0.0.0&#47;8&#34;, &#34;172.16.0.0&#47;12&#34;, &#34;192.168.0.0&#47;16&#34;&#93;</code> |
| [boot_disk_image](variables.tf#L14) | Boot disk image for NTP relay VMs. The image must have chrony pre-installed — the startup script only configures it, it does not install packages. Use a hardened RHEL 8 image for full STIG compliance. | <code>string</code> |  | <code>&#34;projects&#47;rhel-cloud&#47;global&#47;images&#47;family&#47;rhel-8&#34;</code> |
| [boot_disk_size](variables.tf#L20) | Boot disk size in GB for NTP relay VMs. Must be at least as large as the boot image (20 GB for RHEL 8). | <code>number</code> |  | <code>20</code> |
| [create_cloud_nat](variables.tf#L26) | Create a Cloud NAT and router to provide NTP relay VMs with outbound internet access to USNO. Set to false if the shared-services VPC already has a Cloud NAT. | <code>bool</code> |  | <code>true</code> |
| [instance_name_prefix](variables.tf#L42) | Name prefix for NTP relay VM instances. | <code>string</code> |  | <code>&#34;ntp-relay&#34;</code> |
| [machine_type](variables.tf#L48) | Machine type for NTP relay VMs. e2-micro is sufficient for NTP workloads. | <code>string</code> |  | <code>&#34;e2-micro&#34;</code> |
| [ntp_servers](variables.tf#L59) | Upstream NTP server IP addresses to configure on relay VMs. Must be IP addresses (not hostnames) as they are also used in firewall destination_ranges. Defaults to USNO authoritative DoD sources as required by DISA STIG SV-230484. | <code>list&#40;string&#41;</code> |  | <code>&#91;&#34;192.5.41.40&#34;, &#34;192.5.41.41&#34;, &#34;192.5.41.209&#34;&#93;</code> |
| [prefix](variables.tf#L69) | Prefix applied to resource names for org-level naming consistency (e.g. 'da1'). Set to null to disable prefixing. | <code>string</code> |  | <code>null</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [relay_ip](outputs.tf#L1) | Internal IP address of the NTP relay VM. |  |
| [relay_self_link](outputs.tf#L6) | Self-link of the NTP relay VM instance. |  |
| [service_account](outputs.tf#L11) | Service account email used by the NTP relay VM. |  |
<!-- END TFDOC -->
