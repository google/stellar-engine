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

# Optional Shared Services Template — Enterprise Hybrid DNS Forwarding

This reference template deploys optional enterprise DNS forwarding zones and policies for hybrid name resolution. Domain-specific forwarding zones route queries to external or on-premises enterprise DNS resolvers via hybrid network connections (VPN or Cloud Interconnect).

> [!NOTE]
> This is an **optional reference template**. It is fully decoupled from the core landing zone (Stages 0–5) and can be adapted or omitted based on your DNS resolution architecture.

## Architecture

```
Spoke VPCs ──DNS peering──▶ Landing VPC ──DNS peering──▶ CSP Landing VPC ──forwarding──▶ Enterprise DNS (Azure)
(shared-services,                                              (VPN tunnel)
 tenant-transit)
```

### Resolution Order

1. Response policy catches `*.googleapis.com` → PSC endpoint (stage 3-networking)
2. Private zone catches org domain → internal records (stage 3-networking)
3. Forwarding zones catch configured domains (e.g. `mil.`, `gov.`) → Enterprise DNS
4. Compute Engine internal DNS resolves `*.internal` → VM IPs (preserved)
5. Google public DNS resolves everything else

### Why Domain-Specific Zones

A root `"."` forwarding zone would intercept Compute Engine internal DNS names
at step 3 before they reach step 4, breaking `.internal` resolution. A validation
rule prevents this. See [Cloud DNS best practices](https://docs.cloud.google.com/dns/docs/best-practices).

### DNS Forwarding Constraint

Cloud DNS forwarding cannot use NCC transitive routing. The forwarding zone must
be authorized for the CSP Landing VPC where VPN tunnels terminate. Other VPCs
reach it via DNS peering zones (a control-plane feature, no data-plane transit).

## Prerequisites

1. **Enterprise DNS resolver IP** — get from Brian Cunningham
2. **Azure VPN tunnel** must be UP (`3-vpn/` stage)
3. **BGP advertisement** — Cloud Router must advertise `35.199.192.0/19` to Azure
   (`3-vpn/gcp_common.tf`). This is the source IP range Cloud DNS uses for
   forwarding queries; without it, responses cannot route back through the VPN.
4. **Azure firewall** must allow UDP/TCP 53 from `35.199.192.0/19`
5. **Shared-services SA** must have `roles/dns.admin` on the VDSS host project
   (granted by the IAM bindings in `3-networking/projects.tf`)

## Deployment

```bash
cd automation
bash shared-services-deploy.sh
```

After apply, forwarding zone info is published to GCS at
`tfvars/shared-services-dns.auto.tfvars.json`.

## Verification

```bash
# From a GCP VM in the landing VPC:
dig test.example.internal @35.199.192.0              # forwarded → Enterprise DNS
dig vm-name.us-east4-a.c.project.internal    # internal DNS preserved
dig storage.googleapis.com @35.199.192.0     # googleapis → PSC endpoint
```

## Usage

```hcl
module "dns" {
  source          = "./shared-services/dns"
  host_project_id = "my-vdss-host"
  prefix          = "da1"
  automation      = { outputs_bucket = "my-prod-iac-core-outputs" }
  vpc_self_links = {
    csp_landing     = module.csp-landing-vpc.self_link
    landing         = module.vdss-vpc.self_link
    shared_services = module.shared-services-vpc.self_link
    tenant_transit  = module.tenant-transit-vpc.self_link
  }
  forwarding_zones = {
    mil = {
      domain     = "mil."
      forwarders = { "10.200.0.4" = "private" }
    }
  }
  private_zone_domain   = "da1-il5-vdss.private.example.internal."
  dns_policy_rules_file = "../../3-networking/data/dns-policy-rules.yaml"
}
```
<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [automation](variables.tf#L1) | Automation resources created by the bootstrap stage. | <code title="object&#40;&#123;&#10;  outputs_bucket &#61; string&#10;&#125;&#41;">object&#40;&#123;&#8230;&#125;&#41;</code> | ✓ |  |
| [host_project_id](variables.tf#L29) | The GCP project ID where DNS zones will be created (the VDSS host project that owns the VPCs). | <code>string</code> | ✓ |  |
| [vpc_self_links](variables.tf#L50) | VPC self-links used for DNS zone authorization and peering. | <code title="object&#40;&#123;&#10;  csp_landing     &#61; string&#10;  landing         &#61; string&#10;  shared_services &#61; string&#10;  tenant_transit  &#61; string&#10;&#125;&#41;">object&#40;&#123;&#8230;&#125;&#41;</code> | ✓ |  |
| [dns_policy_rules_file](variables.tf#L8) | Path to the YAML file containing DNS response policy rules for Private Google Access (googleapis.com, gcr.io, etc.). If set, a response policy is created for the shared-services VPC. | <code>string</code> |  | <code>null</code> |
| [forwarding_zones](variables.tf#L14) | DNS forwarding zones keyed by name. Each zone forwards queries for the specified domain to the given forwarder IPs via the cross-cloud VPN tunnel. Use domain-specific zones (e.g. 'mil.', 'Enterprise.mil.') — root domain '.' breaks Compute Engine internal DNS. | <code title="map&#40;object&#40;&#123;&#10;  domain     &#61; string&#10;  forwarders &#61; map&#40;string&#41;&#10;&#125;&#41;&#41;">map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> |  | <code>&#123;&#125;</code> |
| [prefix](variables.tf#L34) | Prefix applied to resource names for org-level naming consistency (e.g. 'da1'). Set to null to disable prefixing. | <code>string</code> |  | <code>null</code> |
| [private_zone_domain](variables.tf#L44) | Domain of the existing private DNS zone in the landing VPC (e.g. 'da1-il5-vdss.private.example.internal.'). A peering zone is created so shared-services and tenant-transit VPCs can resolve records in it. | <code>string</code> |  | <code>null</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [forwarding_zones](outputs.tf#L1) | Map of forwarding zone names to their domains. |  |
| [peering_zones](outputs.tf#L11) | Map of peering zone names for the landing VPC. |  |
<!-- END TFDOC -->
