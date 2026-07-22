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

# Shared Services — SMTP Relay

This module deploys a DISA STIG-compliant Postfix SMTP relay (smarthost) in the
shared-services VPC. All outbound email from spoke VMs is relayed through the
Enterprise Email Security Gateway (EESG) at `mail.example.com` via Cloud
Interconnect / BCAP. GCP blocks outbound port 25 on the public internet, but
traffic routed internally over Cloud Interconnect is permitted on port 25.

## Architecture

```
Spoke VMs (dev/prod tenants)
    │  TCP 25 internal only
    ▼
SMTP Relay VM in shared-services       ← Postfix smarthost
    │  TCP 25 via Cloud Interconnect / BCAP
    ▼
EESG (mail.example.com)                ← Enterprise Email Security Gateway
```

## STIG Compliance

| Rule                       | Requirement                          | How Met                                                        |
| -------------------------- | ------------------------------------ | -------------------------------------------------------------- |
| SV-230550 (RHEL-08-040290) | Prevent unrestricted mail relaying   | `smtpd_client_restrictions = permit_mynetworks, reject`        |
| SV-230489 (RHEL-08-040002) | Sendmail must not be installed       | Startup script removes sendmail if present                     |
| DoD TLS requirement        | Mandatory TLS 1.2+ for transit       | `smtp_tls_mandatory_protocols = !SSLv2, !SSLv3, !TLSv1, !TLSv1.1` |
| FIPS 140-2                 | FIPS-approved cryptographic modules  | `smtp_tls_fingerprint_digest = sha256`; FIPS mode is an image-level prerequisite |

## Prerequisites

1. **DISA EESG relay IP** — coordinate with DISA POC for IP whitelisting and
   mail envelope restrictions. Set `disa_relay_hosts` to the relay IP(s).
2. **BCAP / Cloud Interconnect** must be UP and routing traffic to the DISA
   relay IPs.
3. **KMS key** for CMEK disk encryption (IL5 requirement) — reference from the
   stage 3-networking keyring.
4. **Shared-services SA** must have appropriate IAM bindings on the VDSS host
   project (granted by `3-networking/projects.tf`).
5. **FIPS 140-2** should be enabled at the OS image level for IL5 compliance.
   This is an image-level concern, not module-level (same as NTP).

## Deployment

```bash
cd automation
bash shared-services-deploy.sh
```

After apply, the relay IP is published to GCS at
`tfvars/shared-services-smtp.auto.tfvars.json`.

Retrieve the relay IP:

```bash
gcloud storage cat gs://<prefix>-<regime>-prod-iac-core-outputs/tfvars/shared-services-smtp.auto.tfvars.json
```

## Spoke Application Configuration

Configure spoke applications to relay mail through the SMTP relay IP on port 25:

```
SMTP_HOST=<smtp_relay_ip>
SMTP_PORT=25
```

Applications should send mail to the relay VM's internal IP. The relay handles
TLS negotiation with the DISA EESG — spoke applications do not need to
configure TLS for the relay hop.

## Verification

On the relay VM:

```bash
systemctl status postfix          # verify service is active
postconf relayhost                # confirm DISA relay target
postconf smtpd_client_restrictions # confirm relay restrictions
```

From a spoke VM:

```bash
telnet <relay_ip> 25              # expect SMTP 220 banner
```

Check firewall logs in Cloud Logging for egress traffic to DISA IPs.

## Known Gaps

**DNS records (SPF/DKIM/DMARC):** Out of scope for this module. Managed in the
DNS shared-service module or by DISA as part of the EESG configuration.

**HA / MIG:** Single-VM deployment for initial rollout (matches NTP pattern).
Managed instance group is a future enhancement for high availability.

**DoD PKI certificates:** If the DISA EESG requires mutual TLS with DoD PKI
certificates, those must be provisioned separately and added to the Postfix
TLS configuration.

**RHUI access:** The module includes an egress firewall rule for Google's RHEL
Update Infrastructure (`35.190.247.13`) to enable Postfix installation at boot
time and ongoing `dnf-automatic` security updates. This requires Cloud NAT
(`create_cloud_nat = true`, the default).

## Usage

```hcl
module "smtp" {
  source           = "./shared-services/smtp"
  hub_project_id   = "my-vdss-host"
  region           = "us-east4"
  network          = module.shared-services-vpc.self_link
  subnetwork       = module.shared-services-vpc.subnet_self_links["us-east4/shared-services-default"]
  encryption_key   = module.kms["us-east4"].keys.smtp.id
  automation       = { outputs_bucket = "my-prod-iac-core-outputs" }
  disa_relay_hosts = ["<disa-eesg-ip>"]
}
```
<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [automation](variables.tf#L7) | Automation resources created by the bootstrap stage. Used to write SMTP relay IPs to the GCS outputs bucket for downstream consumption. | <code title="object&#40;&#123;&#10;  outputs_bucket &#61; string&#10;&#125;&#41;">object&#40;&#123;&#8230;&#125;&#41;</code> | ✓ |  |
| [disa_relay_hosts](variables.tf#L32) | DISA EESG relay IP addresses. Must be IP addresses (not hostnames) as they are also used in firewall destination_ranges. | <code>list&#40;string&#41;</code> | ✓ |  |
| [encryption_key](variables.tf#L47) | KMS key self-link for CMEK disk encryption on SMTP relay VMs. Required for IL5 deployments where constraints/gcp.restrictNonCmekServices is enforced. | <code>string</code> | ✓ |  |
| [hub_project_id](variables.tf#L52) | The GCP project ID where SMTP relay resources will be deployed. Must be the project that owns the VPC (the VDSS host project), since Cloud Router, Cloud NAT, and firewall rules cannot cross-project reference networks. | <code>string</code> | ✓ |  |
| [network](variables.tf#L69) | Self-link of the VPC network to attach SMTP relay VMs to. | <code>string</code> | ✓ |  |
| [region](variables.tf#L84) | GCP region for SMTP relay VM deployment. | <code>string</code> | ✓ |  |
| [subnetwork](variables.tf#L101) | Self-link of the subnetwork to attach SMTP relay VMs to. | <code>string</code> | ✓ |  |
| [allowed_client_ranges](variables.tf#L1) | Internal CIDR ranges permitted to send mail through the SMTP relay over TCP 25. Defaults to all RFC 1918 space. | <code>list&#40;string&#41;</code> |  | <code>&#91;&#34;10.0.0.0&#47;8&#34;, &#34;172.16.0.0&#47;12&#34;, &#34;192.168.0.0&#47;16&#34;&#93;</code> |
| [boot_disk_image](variables.tf#L14) | Boot disk image for SMTP relay VMs. The startup script installs Postfix via RHUI if not present. Use a hardened RHEL 8 image for full STIG compliance. | <code>string</code> |  | <code>&#34;projects&#47;rhel-cloud&#47;global&#47;images&#47;family&#47;rhel-8&#34;</code> |
| [boot_disk_size](variables.tf#L20) | Boot disk size in GB for SMTP relay VMs. Must be at least as large as the boot image (20 GB for RHEL 8). | <code>number</code> |  | <code>20</code> |
| [create_cloud_nat](variables.tf#L26) | Create a Cloud NAT and router to provide SMTP relay VMs with outbound access for RHUI package operations. Set to false if the shared-services VPC already has a Cloud NAT. | <code>bool</code> |  | <code>true</code> |
| [disa_relay_port](variables.tf#L41) | TCP port for the DISA EESG relay. Standard SMTP is 25. | <code>number</code> |  | <code>25</code> |
| [instance_name_prefix](variables.tf#L57) | Name prefix for SMTP relay VM instances. | <code>string</code> |  | <code>&#34;smtp-relay&#34;</code> |
| [machine_type](variables.tf#L63) | Machine type for SMTP relay VMs. e2-small provides sufficient resources for Postfix workloads. | <code>string</code> |  | <code>&#34;e2-small&#34;</code> |
| [prefix](variables.tf#L74) | Prefix applied to resource names for org-level naming consistency (e.g. 'da1'). Set to null to disable prefixing. | <code>string</code> |  | <code>null</code> |
| [smtp_domain](variables.tf#L89) | Domain name used in Postfix mydomain directive. | <code>string</code> |  | <code>&#34;example.com&#34;</code> |
| [smtp_hostname](variables.tf#L95) | Hostname used in Postfix myhostname directive. | <code>string</code> |  | <code>&#34;smtp.example.com&#34;</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [relay_ip](outputs.tf#L1) | Internal IP address of the SMTP relay VM. |  |
| [relay_self_link](outputs.tf#L6) | Self-link of the SMTP relay VM instance. |  |
| [service_account](outputs.tf#L11) | Service account email used by the SMTP relay VM. |  |
<!-- END TFDOC -->
