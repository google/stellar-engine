# Networking with network virtual appliances

Stage 2 deploys centralized hub-and-spoke Shared VPC infrastructure inspected by Network Virtual Appliances between the landing and DMZ zones for IL4 and IL5 Assured Workloads environments:

- The landing hub VPC centralizes connectivity to on-premises networks, spoke VPCs, and shared services such as CI/CD, repositories, and monitoring.
- Environment spoke VPCs isolate workloads per environment while preserving controlled transit to central services.
- Dedicated Shared VPC host projects separate network administration from workload service projects.
- Cloud DNS peering and forwarding zones centralize hybrid and internal name resolution across the hub and spokes.

[VPC network peering](https://cloud.google.com/vpc/docs/vpc-peering) connects the landing hub VPC to environment spoke VPCs with full bandwidth and low latency. Customize subnet counts and CIDR allocations through Terraform variables or YAML factory files without modifying module code.

<p align="center">
  <img src="images/Stellar-Engine-Network-IL-5.png" alt="Networking diagram">
</p>

<!-- BEGIN TOC -->
- [1 Design overview](#1-design-overview)
  - [Palo Alto NGFW](#palo-alto-ngfw)
  - [Multi-regional deployment](#multi-regional-deployment)
  - [VPC design](#vpc-design)
  - [Internal connectivity](#internal-connectivity)
  - [IP addressing and routing](#ip-addressing-and-routing)
  - [Internet egress](#internet-egress)
  - [VPC and hierarchical firewalls](#vpc-and-hierarchical-firewalls)
  - [DNS design](#dns-design)
- [2 Stage file layout](#2-stage-file-layout)
  - [VPCs](#vpcs)
  - [Hybrid connectivity](#hybrid-connectivity)
  - [Routing](#routing)
  - [Firewalls](#firewalls)
  - [DNS architecture](#dns-architecture)
    - [Cloud environment](#cloud-environment)
- [3 Stage deployment](#3-stage-deployment)
  - [Provider and variable files](#provider-and-variable-files)
  - [Service account impersonation](#service-account-impersonation)
  - [Default gcloud project](#default-gcloud-project)
  - [Variable configuration](#variable-configuration)
  - [Delayed billing association](#delayed-billing-association)
  - [Terraform execution](#terraform-execution)
    - [Private Google Access](#private-google-access)
- [4 Customizations](#4-customizations)
  - [Default regions](#default-regions)
- [5 Palo Alto NGFW configuration](#5-palo-alto-ngfw-configuration)
  - [Management console access](#management-console-access)
  - [Bootstrap XML updates](#bootstrap-xml-updates)
- [6 Redeployment](#6-redeployment)
- [Variables](#variables)
- [Outputs](#outputs)
<!-- END TOC -->

## 1 Design overview

### Palo Alto NGFW

This stage deploys Palo Alto VM-Series Next-Generation Firewalls to provide intrusion detection, intrusion prevention, and TLS inspection for IL4 and IL5 accreditations.

### Multi-regional deployment

Configure the `regions` variable to deploy regional NVA instance templates, managed instance groups, internal load balancers, and test VMs into one or two Assured Workloads regions supported for IL4 or IL5. Weigh the operational cost of running dual-region firewall appliances against your availability requirements when selecting single-region versus multi-region topology.

### VPC design

The central VDSS inspection boundary separates traffic across two transit VPC networks connected by regional multi-zone [Managed Instance Groups](https://cloud.google.com/compute/docs/instance-groups) of Palo Alto VM-Series appliances fronted by regional internal passthrough Network Load Balancers:

- The landing VPC serves as the trusted hub peered with environment spoke VPCs and terminates Cloud VPN tunnels from on-premises networks.
- The DMZ VPC serves as the untrusted boundary towards the public internet and hosts [Cloud NAT](https://cloud.google.com/nat/docs/overview).
- Cross-environment traffic and north-south traffic between landing and DMZ networks traverse the NVA appliances, which come up unlicensed for initial routing and NAT bootstrap until you apply production licenses and security policies.
- Outbound traffic from landing networks to DMZ networks undergoes source NAT on the NVAs unless excluded by policy.

Each VPC operates as a [Shared VPC](https://cloud.google.com/vpc/docs/shared-vpc) in a dedicated host project so organization administrators retain central control over subnets, routes, and firewalls while delegating workload deployment to service project administrators. Environment spoke definitions flow directly from `0-bootstrap` and `1-resman`, and you can extend spokes across single-organization or multi-organization layouts.

### Internal connectivity

Environment spokes peer directly with the landing hub VPC while multi-NIC appliances bridge the landing and DMZ VPCs:

- [VPC Network Peering](https://cloud.google.com/vpc/docs/vpc-peering) connects the landing VPC to spoke VPCs with zero per-GB transit cost, full line-rate bandwidth, and no added latency, though peering is non-transitive, exchanges all subnet routes without granular filtering, and shares peering-group quotas.
- [Multi-NIC NVA appliances](https://cloud.google.com/architecture/best-practices-vpc-design#multi-nic) connect the landing and DMZ VPCs to enforce Layer 7 IPS inspection and vendor policy parity with on-premises firewalls, trading off higher VM and licensing costs, VM throughput ceilings, and HA failover management.

### IP addressing and routing

Plan your cloud IP address space up front so routes aggregate into larger CIDR blocks and stay well within [Cloud Router](https://cloud.google.com/network-connectivity/docs/router/quotas) and [VPC](https://cloud.google.com/vpc/docs/quota) quotas.

By default, `terraform.tfvars.sample` places the three VDSS transit subnets inside `10.64.0.0/11` in `regions.primary` and assigns dedicated `/16` tenant workload ranges, `/24` proxy-only subnets (`proxy_subnets`), and optional [Private Services Access](https://cloud.google.com/vpc/docs/private-services-access) ranges (`psa_ranges`) per environment in `terraform.tfvars`.

The `<prefix>-net-vdss-host` project hosts three VDSS networks alongside one peered spoke VPC in a dedicated `<prefix>-<env>-net-host` Shared VPC host project created for each `<env>` environment defined in `1-resman`:

| name | description |
| --- | --- |
| `vdss-mgmt-0` | Management network for the Palo Alto NGFW appliances and bastion host. |
| `vdss-dmz-0` | Internet-facing untrusted DMZ network. |
| `vdss-landing-0` | Trusted landing hub network peered with environment spoke VPCs. |

Default VDSS subnets allocate from the primary region:

| name | region | VPC network | CIDR |
| --- | --- | --- | --- |
| `mgmt-default` | `<primary-region>` | `vdss-mgmt-0` | `10.64.129.0/24` |
| `dmz-default` | `<primary-region>` | `vdss-dmz-0` | `10.64.128.0/24` |
| `landing-default` | `<primary-region>` | `vdss-landing-0` | `10.64.0.0/24` |

Each environment spoke VPC also receives workload subnets (`subnets`) and a regional proxy-only subnet (`proxy_subnets`).

Routing combines automatic subnet routes, VPC peering route exchange, and static routes on the VPCs and NVA appliances:

- Subnets within the same VPC exchange routes automatically.
- Environment spoke VPCs and the landing hub VPC exchange subnet routes over VPC peering.
- Static routes in `vdss-landing-0` and `vdss-mgmt-0` steer default egress traffic toward the regional NVA internal load balancer VIP and the management default internet gateway respectively.
- Static routes on the NVA trusted interface return traffic to every spoke primary subnet, secondary subnet range, and proxy-only subnet. Because the NVAs hold a default route on the DMZ interface only, a reply to any spoke range missing a static route exits through the DMZ. Private Services Access ranges have no static route because VPC peering is not transitive.
- When extending `vdss-landing-0` with Cloud VPN or Cloud Interconnect, configure Cloud Routers to disable default subnet advertisements and advertise aggregated CIDR blocks through custom advertisements to conserve route quotas.

### Internet egress

Outbound internet traffic traverses a NAT policy from the landing zone to the DMZ zone on the Palo Alto NGFW. This stage deploys [Cloud NAT](https://cloud.google.com/nat/docs/overview) unconditionally in `vdss-dmz-0` (`module.dmz-nat-primary`) and `vdss-mgmt-0` (`module.dmz-nat-mgmt`) via `net-vdss.tf`. You can also adapt the design for per-VPC Cloud NAT, explicit forwarding proxies with URL filtering, or hairpinned egress through on-premises firewalls.

### VPC and hierarchical firewalls

Stage 2 combines a folder-level hierarchical firewall policy on the `Networking` folder with per-VPC firewall rules configured through `firewall_rules` and `cidrs`.

### DNS design

Cloud DNS private zones, peering zones, and response policies centralize name resolution across the VDSS hub and environment spokes:

- The `<prefix>-net-vdss-host` project hosts the root private zone (`<organization.domain>`) attached to `vdss-landing-0` and a `googleapis` response policy attached to `vdss-dmz-0`, `vdss-landing-0`, and `vdss-mgmt-0`.
- Environment spoke host projects host environment subdomains (`<env>.<organization.domain>`) visible to `vdss-landing-0` and delegate root `.` resolution to `vdss-landing-0` via DNS peering.
- [Cloud DNS response policies](https://cloud.google.com/dns/docs/zones/manage-response-policies#create-response-policy-rule) resolve [Private Google Access domains](https://cloud.google.com/vpc/docs/configure-private-google-access#domain-options) privately.

If adding hybrid Cloud VPN connectivity, route `35.199.192.0/19` from on-premises networks into the tunnels and forward `private.googleapis.com`, `restricted.googleapis.com`, and `<organization.domain>` queries to inbound DNS addresses on `vdss-landing-0`.

## 2 Stage file layout

### VPCs

The `net-vdss.tf` and `branch-net-envs.tf` files define the VDSS transit networks and environment spoke networks:

- The [`project`](../../../modules/project) module provisions `<prefix>-net-vdss-host` and each `<prefix>-<env>-net-host` [Shared VPC host project](https://cloud.google.com/vpc/docs/shared-vpc) and enables required APIs.
- The [`net-vpc`](../../../modules/net-vpc) module manages subnets from `subnets` and `proxy_subnets`, Private Google Access routes, landing DNS inbound policies, and [Private Services Access](https://cloud.google.com/vpc/docs/configure-private-services-access#allocating-range) ranges via `psa_ranges`, while `psc.tf` falls back to a default `/22` `default-peering` range when `psa_ranges` is empty for an environment (or its `dev` fallback).
- The [`net-cloudnat`](../../../modules/net-cloudnat) module provisions Cloud NAT in `vdss-dmz-0` and `vdss-mgmt-0`.

### Hybrid connectivity

This stage does not deploy VPN or Interconnect tunnels by default. When hybrid connectivity is required, add [`net-vpn-ha`](../../../modules/net-vpn-ha) resources targeting `vdss-landing-0` or deploy `blueprints/il5/ha-vpn-multicloud`.

### Routing

Each [`net-vpc`](../../../modules/net-vpc) call in `net-vdss.tf` and `branch-net-envs.tf` configures Private Google Access routes, while `ngfw-routes.tf` computes NGFW return routes across every spoke primary subnet, secondary range, and proxy-only subnet for `templates/bootstrap.xml.tpl`, `ngfw.tf` configures `default-route-nva` in `vdss-landing-0`, and `net-vdss.tf` configures `default-route-mgmt` in `vdss-mgmt-0`.

### Firewalls

Per-VPC firewall rules use [`net-vpc-firewall`](../../../modules/net-vpc-firewall) configured via `firewall_rules` and `cidrs` in `net-vdss.tf` and `branch-net-envs.tf`.

Folder-level hierarchical firewall policies in `main.tf` attach to the `Networking` folder via [`folder`](../../../modules/folder) and [`net-firewall-policy`](../../../modules/net-firewall-policy/README.md#factory) using optional factory files under `factories_config.data_dir` (`cidrs.yaml` and `hierarchical-ingress-rules.yaml`).

### DNS architecture

Both `net-vdss.tf` and `branch-net-envs.tf` configure [`dns`](../../../modules/dns) and [`dns-response-policy`](../../../modules/dns-response-policy) resources for the root domain (`org-domain`), Google APIs response policy (`googleapis`), and per-environment subdomains (`<env>-org-domain` and `<env>-root-dns-peering`).

#### Cloud environment

The root DNS zone in `<prefix>-net-vdss-host` acts as the central resolver for spoke VPCs through root DNS peering (`<env>-root-dns-peering`). Grant visibility to both `vdss-landing-0` and `vdss-dmz-0` when adding spoke private zones (`<env>-org-domain`) if DMZ workloads also need to resolve spoke names.

## 3 Stage deployment

Deploy this stage after [0-bootstrap](../0-bootstrap) and [1-resman](../1-resman) so the Stage 2 automation service account, state bucket, and upstream `.auto.tfvars.json` files exist.

### Provider and variable files

Stage 2 consumes generated provider and `.auto.tfvars.json` files from [Stage 0 and Stage 1](../0-bootstrap/README.md). Run `stage-links.sh` from the FAST root directory with your Stage 0 outputs bucket or local outputs path to print the `gcloud storage cp` commands:

```bash
../../stage-links.sh gs://xxx-prod-iac-core-outputs-0
```

Copy the generated provider and variable files into the stage directory:

```bash
gcloud storage cp gs://xxx-prod-iac-core-outputs-0/providers/2-networking-providers.tf ./
gcloud storage cp gs://xxx-prod-iac-core-outputs-0/tfvars/0-globals.auto.tfvars.json ./
gcloud storage cp gs://xxx-prod-iac-core-outputs-0/tfvars/0-bootstrap.auto.tfvars.json ./
gcloud storage cp gs://xxx-prod-iac-core-outputs-0/tfvars/1-resman.auto.tfvars.json ./
```

### Service account impersonation

The generated provider file impersonates the Stage 2 automation service account. Ensure your active user identity belongs to `gcp-devops` or `gcp-organization-admins`.

### Default gcloud project

Set your default `gcloud` project to the Stage 0 automation project before running Terraform manually from the command line.

Look up the automation project ID from Stage 0 outputs:

```bash
cd ../0-bootstrap
terraform output project_ids
```

Configure the default project in `gcloud` and return to the Stage 2 directory:

```bash
gcloud config set project <prefix>-prod-iac-core-0
cd ../2-networking-b-il5-ngfw
```

### Variable configuration

Stage 2 inputs fall into three groups:

- Organization-wide globals populated from `0-globals.auto.tfvars.json`.
- Upstream stage resource identifiers populated from `0-bootstrap.auto.tfvars.json` and `1-resman.auto.tfvars.json`.
- Stage-specific customizations set in `terraform.tfvars`, documented in [Customizations](#4-customizations) and the [Variables](#variables) table.

To write downstream stage output files to a local directory, set `outputs_location` in `terraform.tfvars`:

```tfvars
outputs_location = "~/fast-config"
```

### Delayed billing association

Delayed billing linkage is unsupported for production and intended only for development environments where Terraform cannot attach billing accounts directly:

- Set `billing_account.id` to `null` temporarily in `0-globals.auto.tfvars.json`.
- Target each project resource (`module.vdss-host-project`, `module.env-spoke-projects["Prod"]`, `module.env-spoke-projects["Int"]`, `module.env-spoke-projects["Test"]`) individually and untaint it if needed:
  `terraform apply -target 'module.vdss-host-project.google_project.project[0]'`
  `terraform untaint 'module.vdss-host-project.google_project.project[0]'`
- Link the billing account to the created projects manually.
- Restore `billing_account.id` in `0-globals.auto.tfvars.json` and run `terraform apply`.

### Terraform execution

Initialize and apply the stage once provider and variable files are in place:

```bash
terraform init
terraform plan
terraform apply
```

#### Private Google Access

[Private Google Access](https://cloud.google.com/vpc/docs/private-google-access) comes preconfigured across Stage 2:

- Cloud DNS response policies in the landing project resolve supported Google API domains to Private Google Access VIPs.
- Static routes for `private.googleapis.com` and `restricted.googleapis.com` VIP ranges exist on every VPC except the DMZ VPC.
- Advertise the Private Google Access VIP ranges through custom Cloud Router or VPN tunnel advertisements if adding hybrid connectivity so on-premises networks can reach Google APIs privately.

## 4 Customizations

### Default regions

The `regions` variable maps `regions.primary` to a Google Cloud region. Replace every `<region>` placeholder in `terraform.tfvars` with the `regions.primary` value from Stage 0:

- Update the region values in `regions` to match your target Assured Workloads regions.
- Keep `landing-default`, `dmz-default`, and `mgmt-default` in `regions.primary` because the NGFW instance templates and bootstrap configuration look up those subnets by primary region.

## 5 Palo Alto NGFW configuration

### Management console access

Gather three prerequisites to reach the Palo Alto web management console:

1. Retrieve the initial administrator password from Terraform outputs with `terraform output -json | jq ".ngfw_password.value.result"`.
2. Start the `management-bastion` VM on the management network if it is stopped.
3. Target the second network interface (`nic1`) attached to `vdss-mgmt-0`, which is the only NGFW interface enabled for administration.

Open an Identity-Aware Proxy SSH tunnel through `management-bastion` in its deployed `<ZONE>` (`${var.regions.primary}-c`), targeting the `<vdss-host-project-id>` (`<prefix>-net-vdss-host`) project:

```bash
gcloud compute ssh management-bastion --project=<vdss-host-project-id> --zone <ZONE> --tunnel-through-iap -- -L 8443:<ip-of-ngfw>:443
```

Sign in at `https://localhost:8443/` with username `admin` and the password from Terraform outputs.

To connect to the NGFW over SSH from `management-bastion`, fetch the SSH private key from Secret Manager on the bastion host:

```bash
mkdir -p ~/.ssh && gcloud secrets versions access latest --secret=ngfw-ssh-private-key --project=<vdss-host-project-id> > ~/.ssh/id_rsa && chmod 600 ~/.ssh/id_rsa
```

### Bootstrap XML updates

After changing firewall settings in the Palo Alto console, export the running configuration archive from the Device Operations tab to extract `running-config.xml`, then merge your changes back into `templates/bootstrap.xml.tpl` while preserving these Terraform template expressions across five blocks:

- `password_hash` appears once near the top of `templates/bootstrap.xml.tpl`.
- `ssh_pubkey` appears twice, once near the top and once near the middle of the template.
- `healthcheck_cidrs` wraps a template loop from `%{ for` to `%{ endfor`.
- `iap_cidrs` wraps a template loop from `%{ for` to `%{ endfor`.
- `return_routes` and `lz_gateway_ip` wrap the static-route template loop from `%{ for` to `%{ endfor`.

Terraform builds `return_routes` from every spoke subnet, secondary range, and proxy-only subnet, and the NGFW instance template tracks the hash of the rendered `bootstrap.xml` file. Adding or removing a spoke range causes the next `terraform apply` to create a new instance template and replace running NGFW instances through the managed instance group, dropping active connections on replaced instances and discarding any live NGFW changes not merged into `templates/bootstrap.xml.tpl`.

## 6 Redeployment

When redeploying this stage with the same `prefix` after teardown or state loss, recover soft-deleted host projects and KMS key versions and import retained resources (`module.vdss-host-project.google_project.project[0]`, `module.env-spoke-projects["<Env>"].google_project.project[0]`, `module.kms.google_kms_key_ring.default[0]`, and `module.kms.google_kms_crypto_key.default["default"]`) into Terraform state before running `terraform apply`. See [the experimental restore script](../../../scripts/restore.sh) for the reference `gcloud` and `terraform import` sequence.
<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [alert_email](variables.tf#L17) | Email to receive log alerts. | <code>string</code> | ✓ |  |
| [automation](variables.tf#L33) | Automation resources created by the bootstrap stage. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> | ✓ |  |
| [billing_account](variables.tf#L41) | Billing account id. If billing account is not part of the same org set `is_org_level` to false. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> | ✓ |  |
| [envs_folders](variables.tf#L109) | List of environments to be created for projects to go into. | <code>map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> | ✓ |  |
| [folder_ids](variables.tf#L184) | Folders to be used for the networking resources in folders/nnnnnnnnnnn format. If null, folder will be created. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> | ✓ |  |
| [organization](variables.tf#L229) | Organization details. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> | ✓ |  |
| [prefix](variables.tf#L245) | Prefix used for resources that need unique names. Use 9 characters or less. | <code>string</code> | ✓ |  |
| [regions](variables.tf#L289) | Region definitions. Inherited from 0-bootstrap outputs. Must be specified in bootstrap terraform.tfvars. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> | ✓ |  |
| [tenant_accounts](variables.tf#L366) | Base Tenant accounts that are created for each folder, provided as a combination of environment and tenant. | <code>map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> | ✓ |  |
| [assured_workloads](variables.tf#L22) | Configuration for Assured Workloads. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>&#123;&#125;</code> |
| [billing_override](variables.tf#L54) | Optional billing override configuration. If set, disables service account impersonation for project billing linkage and runs under the user account using the specified quota projects. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>null</code> |
| [cidrs](variables.tf#L63) | Named CIDR ranges to use in firewall rules. | <code>map&#40;list&#40;string&#41;&#41;</code> |  | <code>&#123;&#125;</code> |
| [common_services_folder](variables.tf#L70) | Common services folder ID. | <code>string</code> |  | <code>null</code> |
| [custom_roles](variables.tf#L76) | Custom roles defined at the org level, in key => id format. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>null</code> |
| [dns](variables.tf#L85) | DNS configuration. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>&#123;&#125;</code> |
| [dns_policy_rules](variables.tf#L95) | DNS response policy rules in name => rule format. | <code>map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> |  | <code>&#123;&#125;</code> |
| [essential_contacts](variables.tf#L116) | Email or map of emails to notification category lists used for essential contacts, unset if null or empty. | <code>any</code> |  | <code>&#123;&#125;</code> |
| [factories_config](variables.tf#L130) | Configuration for network resource factories. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>&#123;&#8230;&#125;</code> |
| [fast_features](variables.tf#L147) | FAST features enabled. | <code>any</code> |  | <code>null</code> |
| [firewall_rules](variables.tf#L153) | Firewall rules for each VPC / environment spoke. | <code>map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> |  | <code>&#123;&#125;</code> |
| [force_destroy](variables.tf#L193) | Toggles force_destroy for GCS buckets. | <code>bool</code> |  | <code>false</code> |
| [groups](variables.tf#L199) | IAM groups mapping. | <code>any</code> |  | <code>null</code> |
| [kms_protection_level](variables.tf#L205) | Cloud KMS protection level for the VDSS keyring key (defaults to HSM when null). | <code>string</code> |  | <code>null</code> |
| [logging](variables.tf#L223) | Logging configuration. | <code>any</code> |  | <code>null</code> |
| [outputs_location](variables.tf#L239) | Path where providers and tfvars files for the following stages are written. Leave empty to disable. | <code>string</code> |  | <code>null</code> |
| [proxy_subnets](variables.tf#L256) | VPC proxy-only subnet CIDRs keyed by environment. | <code>map&#40;string&#41;</code> |  | <code>&#123;&#125;</code> |
| [psa_ranges](variables.tf#L263) | IP ranges used for Private Service Access (e.g. CloudSQL) keyed by lowercase environment name (for example prod, int, test, or dev fallback). | <code>map&#40;list&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;&#41;</code> |  | <code>&#123;&#125;</code> |
| [regime_mapping](variables.tf#L283) | Compliance regime shorthand mapping. | <code>any</code> |  | <code>null</code> |
| [service_accounts](variables.tf#L297) | Automation service accounts in name => email format. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>null</code> |
| [spoke_project_iam](variables.tf#L311) | Additional authoritative IAM bindings for environment spoke host projects, keyed by environment name (for example dev or prod) and role. | <code>map&#40;map&#40;list&#40;string&#41;&#41;&#41;</code> |  | <code>&#123;&#125;</code> |
| [subnets](variables.tf#L318) | VPC subnet configurations keyed by network name. | <code>map&#40;list&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;&#41;</code> |  | <code>&#123;&#125;</code> |
| [vmseries_image](variables.tf#L380) | The image name from which to boot an instance, including a license type (bundle/flex) and version. | <code>string</code> |  | <code>&#34;vmseries-112&#34;</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [host_project_ids](outputs.tf#L64) | Network project ids. |  |
| [host_project_numbers](outputs.tf#L69) | Network project numbers. |  |
| [ngfw_password](outputs.tf#L74) | Password for authenticating to the NGFW. | ✓ |
| [ngfw_ssh_private_key_secret_id](outputs.tf#L80) | Secret Manager secret ID storing the NGFW SSH private key. |  |
| [tfvars](outputs.tf#L85) | Terraform variables file for the following stages. | ✓ |
<!-- END TFDOC -->
