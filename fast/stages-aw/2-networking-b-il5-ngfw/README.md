# Networking with Network Virtual Appliance

This stage sets up the shared network infrastructure for the whole Google Cloud Organization.

It is designed for those who would like to leverage Network Virtual Appliances (NVAs) between landing and dmz areas of the network, for example for Intrusion Prevention System (IPS) purposes.

It adopts the common “hub and spoke” reference design, which is well suited for multiple scenarios, and it offers several advantages versus other designs:

- the "landing hub" VPC centralizes the external connectivity towards landing network resources (e.g. on-prem, other cloud environments and the spokes), and it is ready to host cross-environment services like CI/CD, code repositories, and monitoring probes
- the "spoke" VPCs allow partitioning workloads (e.g. by environment like in this setup), while still retaining controlled access to central connectivity and services
- Shared VPCs -both in hub and spokes- split the management of the network resources into specific (host) Google Cloud Projects, while still allowing them to be consumed from the workload (service) Google Cloud Project
- the design facilitates DNS centralization

Connectivity between the hub and the spokes is established via [VPC network peerings](https://cloud.google.com/vpc/docs/vpc-peering), which offer uncapped bandwidth, lower latencies, at no additional costs and with a very low management overhead. Different ways of implementing connectivity, and related some pros and cons, are discussed below.

The diagram shows the high-level design and it should be used as a reference throughout the following sections.

The final number of subnets, and their IP addressing will depend on the user-specific requirements. It can be easily changed via variables or external data files, without any need to edit the code.

<p align="center">
  <img src="diagram.svg" alt="Networking diagram">
</p>

# Table of Contents

<!-- BEGIN TOC -->
- [Table of Contents](#table-of-contents)
- [Design overview and choices](#design-overview-and-choices)
  - [Palo Alto NGFW](#palo-alto-ngfw)
  - [Multi-regional deployment](#multi-regional-deployment)
  - [VPC design](#vpc-design)
  - [Internal connectivity](#internal-connectivity)
  - [IP ranges, subnetting, routing](#ip-ranges-subnetting-routing)
  - [Internet egress](#internet-egress)
  - [VPC and Hierarchical Firewall](#vpc-and-hierarchical-firewall)
  - [DNS](#dns)
- [Stage structure and files layout](#stage-structure-and-files-layout)
  - [VPCs](#vpcs)
  - [VPNs](#vpns)
  - [Routing and BGP](#routing-and-bgp)
  - [Firewall](#firewall)
  - [DNS architecture](#dns-architecture)
    - [Cloud environment](#cloud-environment)
- [How to run this stage](#how-to-run-this-stage)
  - [Provider and Terraform variables](#provider-and-terraform-variables)
  - [Impersonating the automation service account](#impersonating-the-automation-service-account)
  - [Setting default Google Cloud Projects for manual run](#setting-default-google-cloud-projects-for-manual-run)
  - [Variable configuration](#variable-configuration)
  - [Using delayed billing association for Google Cloud Project](#using-delayed-billing-association-for-google-cloud-project)
  - [Running the stage](#running-the-stage)
    - [Private Google Access](#private-google-access)
- [Customizations](#customizations)
  - [Changing default regions](#changing-default-regions)
- [Configuring Palo Alto NGFWs](#configuring-palo-alto-ngfws)
  - [Reaching the Management Console](#reaching-the-management-console)
  - [Updating configuration](#updating-configuration)
- [Redeployment](#redeployment)
- [Variables](#variables)
- [Outputs](#outputs)
<!-- END TOC -->

## Design overview and choices

### Palo Alto NGFW

In order to support full NGFW capabilities, including IDS/IPS and TLS break-and-inspect, the team has chosen to implement Palo Alto NGFWs. While there are other vendor products that can support these requirements, our team has the most experience getting accreditations using Palo Alto NGFW. In future iterations of this codebase, we intend on expanding this capability to include: GCP Cloud NGFW, Barracuda, and Cisco.

### Multi-regional deployment

The stage can optionally deploy the infrastructure into one or two regions. Due to current restrictions for the IL5 overlay, the two available regions are typically us-east4 and us-central1 (nam4). Regional resources include NVAs (templates, MIGs, LBs) and test VMs. The specific regions can be configured via the `regions` variable.
As part of your design, you should weigh the additional maintenance cost of operating in two regions against your availability requirements to decide what is best for your deployment.

### VPC design

The "landing zone" is divided into two VPC networks

- the landing VPC: the connectivity hub towards other landing networks
- the dmz VPC: the connectivity hub towards any other dmz network

The VPCs are connected with two sets of sample NVA machines, grouped in regional (multi-zone) [Managed Instance Groups (MIGs)](https://cloud.google.com/compute/docs/instance-groups). The appliances are currently unlicensed Palo Alto NGFWs. In their unlicensed state, they are capable of basic routing and NAT functionality, as well as a subset of the traffic identification and security policies. They are not intended to be used in this way long term, but instead as a way to get the network bootstrapped while the security configurations are further developed.
The traffic destined to the VMs in each MIG is mediated through regional internal load balancers, both in the landing and in the dmz networks.

By default, the design assumes the following:

- on-premise networks (and related resources) are considered landing. As such, the VPNs connecting with on-premises are terminated in GCP, in the landing VPC
- the public Internet is considered dmz. As such [Cloud NAT](https://cloud.google.com/nat/docs/overview) is deployed in the dmz landing VPC only
- cross-environment traffic and traffic from any dmz network to any landing network (and vice versa) pass through the NVAs. For demo purposes, the current NVA performs simple routing/natting only
- any traffic from a landing network to an dmz network (e.g. Internet) is natted by the NVAs. Users can configure further exclusions

The landing landing VPC acts as a hub: it bridges internal resources with the outside world and it hosts the shared services consumed by the spoke VPCs, connected to the hub through VPC network peerings. Spokes are used to partition the environments. These environments are inherited from the `0-bootstrap` and `1-resman` stages.

Each virtual network is a [shared VPC](https://cloud.google.com/vpc/docs/shared-vpc): shared VPCs are managed in dedicated *host Google Cloud Project* and shared with other *service Google Cloud Projects* that consume the network resources.
Shared VPC lets Google Cloud Organization administrators delegate administrative responsibilities, such as creating and managing instances, to Service Google Cloud Projects Admins while maintaining centralized control over network resources like subnets, routes, and firewalls.

Users can easily extend the design to host additional environments, or adopt different logical mappings for the spokes (for example, in order to create a new spoke for each company entity). Adding spokes is trivial and it does not increase the design complexity. The steps to add more spokes are provided in the following sections.

In multi-organization scenarios, where production and non-production resources use different Cloud Identity and GCP organizations, the hub/landing VPC is usually part of the production organization. It establishes connections with the production spokes within the same organization, and with non-production spokes in a different organization.

### Internal connectivity

Internal connectivity (e.g. between the landing landing VPC and the spokes) is realized with VPC network peerings. As mentioned, there are other ways to implement connectivity. These can be easily retrofitted with minimal code changes, although they introduce additional considerations on service interoperability, quotas and management.

This is an options summary

- [VPC Peering](https://cloud.google.com/vpc/docs/vpc-peering) (used here to connect the landing landing VPC with the spokes, also used by [02-networking-vpn](../2-networking-b-vpn/))
  - Pros: no additional costs, full bandwidth with no configurations, no extra latency
  - Cons: no transitivity (e.g. to GKE masters, Cloud SQL, etc.), no selective exchange of routes, several quotas and limits shared between VPCs in a peering group
- [Multi-NIC appliances](https://cloud.google.com/architecture/best-practices-vpc-design#multi-nic) (used here to connect the landing landing and dmz VPCs) and multi-NIC appliances with NCC/BGP support implemented [here](../2-networking-e-nva-bgp/)
  - Pros: provides additional security features (e.g. IPS), potentially better integration with on-prem systems by using the same vendor
  - Cons: complex HA/failover setup, limited by VM bandwidth and scale, additional costs for VMs and licenses, out of band management of a critical cloud component

### IP ranges, subnetting, routing

Minimizing the number of routes (and subnets) in the cloud environment is important, as it simplifies management and it avoids hitting [Cloud Router](https://cloud.google.com/network-connectivity/docs/router/quotas) and [VPC](https://cloud.google.com/vpc/docs/quota) quotas and limits. For this reason, we recommend to carefully plan the IP space used in your cloud environment. This allows the use of larger IP CIDR blocks in routes, whenever possible.

This stage uses a dedicated `/11` block (`10.64.0.0/11`), which should be sized to the own needs. The subnets created in each VPC derive from this range.

The `/11` block is evenly split in eight, smaller `/16` blocks, assigned to different areas of the Google Cloud network across the configured regions: *landing dmz primary-region*, *landing dmz secondary-region*, *landing landing primary-region*, *landing dmz secondary-region*, *development primary-region*, *development secondary-region*, *production primary-region*, *production secondary-region*.

The first `/24` range in every area is allocated for a default subnet, which can be removed or modified as needed. The last three `/24` ranges can be used for [PSA (Private Service Access)](https://cloud.google.com/vpc/docs/private-services-access)via the `psa_ranges` variable, or for [Internal Application Load Balancers (L7 LBs)](https://cloud.google.com/load-balancing/docs/l7-internal) subnets via the factory.

This is a summary of the VPC Networks deployed into the `<prefix>-net-vdss-host` Google Cloud Projects by this stage:

| name | description |
| ---- | ------------|
| `vdss-mgmt-0` | Management network for the Palo Alto deployments. |
| `vdss-dmz-0` | The Internet facing network for the DMZ |
| `vdss-landing-0` | The landing network on the "trust" side of the Palo Alto NGFW deployments |

Additionally, a VPC is created for each of the `net-<env>-net-host` Google Cloud Project deployed in `1-resman`, and those are all peered to the `landing-vdss-0` VPC.

This is a summary of the subnets allocated by default in this setup:

| name | region | VPC network | description | CIDR |
|---|---|---|---|---|
| `mgmt-default` | `<primary-region>` | `prod-mgmt-0` | `10.64.128.0/24` |
| `dmz-default`  | `<primary-region>` | `prod-dmz-0` | `10.64.128.0/24` |
| `landing-default` | `<primary-region>` | `prod-landing-0` | `10.64.0.0/24` |

Within each environment, there is a shared-subnet deployed and a proxy-only subnet deployed.

Routes in Google Cloud are either automatically created (for example, when a subnet is added to a VPC), manually created via static routes, dynamically exchanged through VPC peerings, or dynamically programmed by [Cloud Routers](https://cloud.google.com/network-connectivity/docs/router#docs) when a BGP session is established. BGP sessions can be configured to advertise VPC ranges, and/or custom ranges via custom advertisements.

In this setup

- routes between multiple subnets within the same VPC are automatically exchanged by Google Cloud
- the spokes and the landing landing VPC exchange routes through VPC peerings
- for cross-environment (spokes) communications, and for connections to on-premises and to the Internet, the spokes leverage some default tagged routes that send the traffic of each region (whose machines are identified by a dedicated network tag, e.g. *ew1*) to a corresponding regional NVA in the landing VPC, through an ILB (whose VIP is set as the route next-hop)
- the NVAs are configured with static routes that allow the communication with the GCP resources (including the cross-environment communication)

The Cloud Routers (connected to the VPN gateways in the landing VPC) are configured to exclude the default advertisement of VPC ranges and they only advertise their respective aggregate ranges, via custom advertisements. This greatly simplifies the routing configuration and avoids quota or limit issues, by keeping the number of routes small, instead of making it proportional to the subnets and to the secondary ranges in the VPCs.

### Internet egress

In this setup, Internet egress is realized through a NAT policy between landing->DMZ on the Palo Alto NGFW. There is also an option to implement the [Cloud NAT](https://cloud.google.com/nat/docs/overview), deployed in the dmz landing VPC. This allows instances in all other VPCs to reach the Internet, passing through the NVAs (being the public Internet considered dmz). Cloud NAT is disabled by default; enable it by setting the `enable_cloud_nat` variable

Several other scenarios are possible, with various degrees of complexity

- deploy Cloud NAT in every VPC
- add forwarding proxies, with optional URL filters
- send Internet traffic to on-premises, so the existing egress infrastructure can be leveraged

Future pluggable modules will allow users to easily experiment with the above scenarios.

### VPC and Hierarchical Firewall

The Google Cloud Firewall is a stateful, distributed feature that allows the creation of L4 policies, either via VPC-level rules or -more recently- via hierarchical policies, applied on the resource hierarchy (Google Cloud Organization, Google CLoud Folders).

The current setup adopts both firewall types. Hierarchical firewall rules are applied in the networking Google Cloud Folder for common ingress rules (egress is open by default): for example, it allows the health checks and the IAP forwarders traffic to reach the VMs.

Rules and policies are defined in simple YAML files, described below.

### DNS

DNS goes hand in hand with networking, especially on Google Cloud where Cloud DNS zones and policies are associated at the VPC level. This setup implements both DNS flows:

- on-prem to cloud via private zones for cloud-managed domains, and an [inbound policy](https://cloud.google.com/dns/docs/server-policies-overview#dns-server-policy-in) used as forwarding target or via delegation (requires some extra configuration) from on-prem DNS resolvers
- cloud to on-prem via forwarding zones for the on-prem managed domains

DNS configuration is further centralized by leveraging peering zones, so that

- the hub/landing Cloud DNS hosts configurations for on-prem forwarding, Google API domains, and the top-level private zone/s (e.g. gcp.example.com)
- the spokes Cloud DNS host configurations for the environment-specific domains (e.g. prod.gcp.example.com), which are bound to the hub/landing leveraging [cross-project binding](https://cloud.google.com/dns/docs/zones/zones-overview#cross-project_binding); a peering zone for the `.` (root) zone is then created on each spoke, delegating all DNS resolution to hub/landing.
- Private Google Access is enabled via [DNS Response Policies](https://cloud.google.com/dns/docs/zones/manage-response-policies#create-response-policy-rule) for most of the [supported domains](https://cloud.google.com/vpc/docs/configure-private-google-access#domain-options)

To complete the configuration, the 35.199.192.0/19 range should be routed to the VPN tunnels from on-premises, and the following names should be configured for DNS forwarding to cloud:

- `private.googleapis.com`
- `restricted.googleapis.com`
- `gcp.example.com` (used as a placeholder)

In Google Cloud, a forwarding zone in the landing Google Cloud Projects is configured to forward queries to the placeholder domain `onprem.example.com` to on-premises.

This configuration is battle-tested, and flexible enough to lend itself to simple modifications without subverting its design.

## Stage structure and files layout

### VPCs

VPCs are defined in separate files, one for `landing` (landing and dmz), one for `prod` and one for `dev`.

These files contain different resources:

- **project** ([`projects`](../../../modules/project)): the "[host Google Cloud Project](https://cloud.google.com/vpc/docs/shared-vpc)" containing the VPCs and enabling the required APIs.
- **VPCs** ([`net-vpc`](../../../modules/net-vpc)): manages the subnets, the explicit routes for `{private,restricted}.googleapis.com` and the DNS inbound policy for the landing landing VPC. Non-infrastructural subnets are created leveraging resource factories. Sample subnets are shipped in [data/subnets](./data/subnets) and can be easily customized to fit users' needs. [PSA](https://cloud.google.com/vpc/docs/configure-private-services-access#allocating-range) are configured by the variable `psa_ranges` if managed services are needed.
- **Cloud NAT** ([`net-cloudnat`](../../../modules/net-cloudnat)) (in the dmz landing VPC only): it manages the networking infrastructure required to enable the Internet egress.

### VPNs

The connectivity between on-premises and GCP (the landing landing VPC) is implemented with Cloud HA VPN ([`net-vpn`](../../../modules/net-vpn-ha)) and defined in [`vpn-onprem.tf`](./vpn-onprem.tf). The file implements a single logical connection between on-premises and the landing landing VPC, both in `us-east4` and `us-central1`. The relevant parameters for its configuration are found in the variables `vpn_onprem_primary_config` and `vpn_onprem_secondary_config`.

### Routing and BGP

Each VPC network ([`net-vpc`](../../../modules/net-vpc)) manages a separate routing table, which can define static routes (e.g. to private.googleapis.com) and receives dynamic routes through VPC peering and BGP sessions established with the neighbor networks (e.g. the landing landing VPC receives routes from on-premises, and the spokes receive RFC1918 from the landing landing VPC).

Static routes are defined in `vpc-*.tf` files in the `routes` section of each `net-vpc` module.

BGP sessions for landing landing to on-premises are configured through the variable `vpn_onprem_configs`.

### Firewall

**VPC firewall rules** ([`net-vpc-firewall`](../../../modules/net-vpc-firewall)) are defined per-vpc on each `vpc-*.tf` file and leverage a resource factory to massively create rules.
To add a new firewall rule, create a new file or edit an existing one in the `data_folder` directory defined in the module `net-vpc-firewall`, following the examples of the "[Rules factory](../../../modules/net-vpc-firewall#rules-factory)" section of the module documentation. Sample firewall rules are shipped in [data/firewall-rules/dmz](./data/firewall-rules/dmz) and in [data/firewall-rules/landing](./data/firewall-rules/landing), and can be easily customized.

**Hierarchical firewall policies** ([`folder`](../../../modules/folder)) are defined in `main.tf` and managed through a policy factory implemented by the `net-firewall-policy` module, which is then applied to the `Networking` folder containing all the core networking infrastructure. Policies are defined in the `rules_file` file, to define a new one simply use the [firewall policy module documentation](../../../modules/net-firewall-policy/README.md#factory)". Sample hierarchical firewall rules are shipped in [data/hierarchical-ingress-rules.yaml](./data/hierarchical-ingress-rules.yaml) and can be easily customised.

### DNS architecture

The DNS ([`dns`](../../../modules/dns)) infrastructure is defined in [`dns-*.tf`] files.

Cloud DNS manages onprem forwarding, the main GCP zone (in this example `gcp.example.com`) and environment-specific zones (i.e. `dev.gcp.example.com` and `prod.gcp.example.com`).

#### Cloud environment

The root DNS zone defined in the landing Google Cloud Projects acts as the source of truth for DNS within the Cloud environment. The resources defined in the spoke VPCs consume the landing DNS infrastructure through DNS peering (e.g. `prod-landing-root-dns-peering`).
The spokes can optionally define private zones (e.g. `prod-dns-private-zone`). Granting visibility both to the landing and dmz landing VPCs ensures that the whole cloud environment can query such zones.

## How to run this stage

This stage is meant to be executed after the [resource management](../1-resman) stage has run, as it leverages the automation service account and bucket created there, and additional resources configured in the [bootstrap](../0-bootstrap) stage.

It's of course possible to run this stage in isolation, but that's outside the scope of this document, and you would need to refer to the code for the previous stages for the environmental requirements.

Before running this stage, you need to make sure you have the correct credentials and permissions, and localize variables by assigning values that match your configuration.

### Provider and Terraform variables

As all other FAST stages, the [mechanism used to pass variable values and pre-built provider files from one stage to the next](../0-bootstrap/README.md#output-files-and-cross-stage-variables) is also leveraged here.

The commands to link or copy the provider and terraform variable files can be easily derived from the `stage-links.sh` script in the FAST root git folder, passing it a single argument with the local output files git folder (if configured) or the Google Cloud output bucket in the automation Google Cloud Projects (derived from stage 0 outputs). The following examples demonstrate both cases, and the resulting commands that then need to be copy/pasted and run.

```bash
../../stage-links.sh gs://xxx-prod-iac-core-outputs-0
```

_copy and paste the following commands for '`2-networking-a-peering`'_

```
gcloud alpha storage cp gs://xxx-prod-iac-core-outputs-0/providers/2-networking-providers.tf ./
gcloud alpha storage cp gs://xxx-prod-iac-core-outputs-0/tfvars/0-globals.auto.tfvars.json ./
gcloud alpha storage cp gs://xxx-prod-iac-core-outputs-0/tfvars/0-bootstrap.auto.tfvars.json ./
gcloud alpha storage cp gs://xxx-prod-iac-core-outputs-0/tfvars/1-resman.auto.tfvars.json ./
```

### Impersonating the automation service account

The preconfigured provider file uses impersonation to run with this stage's automation service account's credentials. The `gcp-devops` and `organization-admins` groups have the necessary IAM bindings in place to do that, so make sure the current user is a member of one of those groups.

### Setting default Google Cloud Projects for manual run

**Important**: Before running this, make sure that if you are running these stages manually from the command line, that your default Google Cloud Projects is set to the 'automation' Google Cloud Projects created in 0-bootstrap.

To find the 'automation' Google Cloud Projects

```bash
cd ../0-bootstrap
terraform output project_ids
```
And to set the gcloud Google Cloud Projects default in your CLI

```bash
gcloud config set project <prefix>-prod-iac-core-0
```

Return to the Networking directory

```bash
cd ../2-networking-b-il5-ngfw
```

### Variable configuration

Variables in this stage -- like most other FAST stages -- are broadly divided into three separate sets:

- variables which refer to global values for the whole organization (org id, billing account id, prefix, etc.), which are pre-populated via the `0-globals.auto.tfvars.json` file linked or copied above
- variables which refer to resources managed by previous stage, which are prepopulated here via the `0-bootstrap.auto.tfvars.json` and `1-resman.auto.tfvars.json` files linked or copied above
- and finally variables that optionally control this stage's behaviour and customizations, and can to be set in a custom `terraform.tfvars` file

The latter set is explained in the [Customization](#customizations) sections below, and the full list can be found in the [Variables](#variables) table at the bottom of this document.

Note that the `outputs_location` variable is disabled by default, you need to explicitly set it in your `terraform.tfvars` file if you want output files to be generated by this stage. This is a sample `terraform.tfvars` that configures it, refer to the [bootstrap stage documentation](../0-bootstrap/README.md#output-files-and-cross-stage-variables) for more details:

```tfvars
outputs_location = "~/fast-config"
```

### Using delayed billing association for Google Cloud Project

This configuration is possible but unsupported and only exists for development purposes, use at your own risk:

- temporarily switch `billing_account.id` to `null` in `0-globals.auto.tfvars.json`
- for each Google Cloud Projects resources in the Google Cloud Projects modules used in this stage (`dev-spoke-project`, `landing-project`, `prod-spoke-project`)
  - apply using `-target`, for example
    `terraform apply -target 'module.landing-project.google_project.project[0]'`
  - untaint the Google Cloud Projects resource after applying, for example
    `terraform untaint 'module.landing-project.google_project.project[0]'`
- go through the process to associate the billing account with the two Google Cloud Projects
- switch `billing_account.id` back to the real billing account id
- resume applying normally

### Running the stage

Once provider and variable values are in place and the correct user is configured, the stage can be run:

```bash
terraform init
terraform plan
terraform apply
```

#### Private Google Access

[Private Google Access](https://cloud.google.com/vpc/docs/private-google-access) (or PGA) enables VMs and on-prem systems to consume Google APIs from within the Google network, and is already fully configured on this environment:

- DNS response policies in the landing Google Cloud Projects implement rules for all supported domains reachable via PGA
- routes for the private and restricted ranges are defined in all VPCs except dmz

To enable PGA access from on premises advertise the private/restricted ranges via the `vpn_onprem_primary_config` and `vpn_onprem_secondary_config` variables, using router or tunnel custom advertisements.

## Customizations

### Changing default regions

Regions are defined via the `regions` variable which sets up a mapping between the `regions.primary` and `regions.secondary` logical names and actual GCP region names. If you need to change regions from the defaults:

- change the values of the mappings in the `regions` variable to the regions you are going to use
- change the regions in the factory subnet files in the `data` folder

##  Configuring Palo Alto NGFWs

### Reaching the Management Console

In order to access the Palo Alto managment console, you will need 3 things

  1. The admin password is stored in the terraform state file, use this command to get it `terraform output -json | jq ".ngfw_password.value.result"`
  2. The terraform code should have automatically created a small VM on the mgmt network that will work as a bastion. You may have to start it, if it is not already running.
  3. Each NGFW instance will have at least 3 interfaces, but only the second one, connected to `prod-mgmt-0` is usable for administration.

Use the following command to access the web portal `gcloud compute ssh management-bastion --zone <ZONE> --tunnel-through-iap -- -L 8443:<ip-of-ngfw>:443`. From here, you should be able to access the management interface at the url https://localhost:8443/ and log in with the username `admin` and the password you found using in the terraform output command.

*Note*: Replace `<ZONE>` with the zone where your management bastion host was deployed. You can find this in the Terraform outputs or by running `terraform show | grep zone`.

If you wish to ssh into the NGFWs, you can copy the `id_rsa` and `id_rsa.pub` files that are output by the terraform process over to the `.ssh/` folder on the bastion host.

### Updating configuration

These Palo Alto NGFWs operate the same as normal ones. But, in order to update the Bootstrap autoconfig XML file after changing a setting, you must take additional steps. In the device settings, under the operations tab, there is an option to export the running config. This will produce a tar file with the `running-config.xml` file in it. You must merge this into the XML file stored under `templates/bootstrap.xml.tpl` by replacing key fields with the terraform template tags.

There is currently no way to automate this process, but take the version of the file committed in Git and find where these template tags are
* `password_hash`: Used 1 time near the top of the document
* `ssh_pubkey`: Used 2 times, once near the top and once near the middle
* `healthcheck_cidrs`: Used 1 time as part of a Jinja template loop. Make sure to copy the entire loop starting with `%{ for` and ending with `%{ endfor`
* `iap_cidrs`: Used 1 time as part of a Jinja template loop. Make sure to copy the entire loop starting with `%{ for` and ending with `%{ endfor`

# Redeployment
If you are redeploying this stage with the same prefix, please run "pre-redeploy.sh" to handle imports.

---
<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [alert_email](variables.tf#L16) | Email to receive log alerts. | <code>string</code> | ✓ |  |
| [automation](variables.tf#L21) | Automation resources created by the bootstrap stage. | <code title="object&#40;&#123;&#10;  outputs_bucket &#61; string&#10;&#125;&#41;">object&#40;&#123;&#8230;&#125;&#41;</code> | ✓ |  |
| [billing_account](variables.tf#L29) | Billing account id. If billing account is not part of the same org set `is_org_level` to false. | <code title="object&#40;&#123;&#10;  id           &#61; string&#10;  is_org_level &#61; optional&#40;bool, true&#41;&#10;&#125;&#41;">object&#40;&#123;&#8230;&#125;&#41;</code> | ✓ |  |
| [envs_folders](variables.tf#L52) | List of environments to be created for projects to go into. | <code title="map&#40;object&#40;&#123;&#10;  admin &#61; string&#10;&#125;&#41;&#41;">map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> | ✓ |  |
| [folder_ids](variables.tf#L86) | Folders to be used for the networking resources in folders/nnnnnnnnnnn format. If null, folder will be created. | <code title="object&#40;&#123;&#10;  networking &#61; string&#10;  envs       &#61; optional&#40;map&#40;string&#41;&#41;&#10;&#125;&#41;">object&#40;&#123;&#8230;&#125;&#41;</code> | ✓ |  |
| [organization](variables.tf#L95) | Organization details. | <code title="object&#40;&#123;&#10;  domain      &#61; string&#10;  id          &#61; number&#10;  customer_id &#61; string&#10;&#125;&#41;">object&#40;&#123;&#8230;&#125;&#41;</code> | ✓ |  |
| [prefix](variables.tf#L111) | Prefix used for resources that need unique names. Use 9 characters or less. | <code>string</code> | ✓ |  |
| [regions](variables.tf#L142) | Region definitions. Inherited from 0-bootstrap outputs. Must be specified in bootstrap terraform.tfvars. | <code title="object&#40;&#123;&#10;  primary &#61; string&#10;&#125;&#41;">object&#40;&#123;&#8230;&#125;&#41;</code> | ✓ |  |
| [tenant_accounts](variables.tf#L164) | Base Tenant accounts that are created for each folder, provided as a combination of environment and tenant. | <code title="map&#40;object&#40;&#123;&#10;  tenant          &#61; string&#10;  env             &#61; string&#10;  main_project    &#61; string&#10;  admin_principal &#61; string&#10;&#125;&#41;&#41;">map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> | ✓ |  |
| [assured_workloads](variables.tf#L193) | Assured Workloads configuration. | <code>any</code> |  | <code>null</code> |
| [billing_override](variables.tf#L184) | Optional billing override configuration. If set, disables service account impersonation for project billing linkage and runs under the user account using the specified quota projects. | <code title="object&#40;&#123;&#10;  project         &#61; string&#10;  billing_project &#61; string&#10;&#125;&#41;">object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>null</code> |
| [cidrs](variables.tf#L274) | Named CIDR ranges to use in firewall rules. | <code>map&#40;list&#40;string&#41;&#41;</code> |  | <code>&#123;&#125;</code> |
| [common_services_folder](variables.tf#L199) | Common services folder ID. | <code>string</code> |  | <code>null</code> |
| [dns](variables.tf#L42) | DNS configuration. | <code title="object&#40;&#123;&#10;  enable_logging &#61; optional&#40;bool, true&#41;&#10;  resolvers      &#61; optional&#40;list&#40;string&#41;, &#91;&#93;&#41;&#10;&#125;&#41;">object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>&#123;&#125;</code> |
| [dns_policy_rules](variables.tf#L260) | DNS response policy rules in name => rule format. | <code title="map&#40;object&#40;&#123;&#10;  dns_name &#61; string&#10;  behavior &#61; optional&#40;string, &#34;bypassResponsePolicy&#34;&#41;&#10;  local_data &#61; optional&#40;map&#40;object&#40;&#123;&#10;    ttl     &#61; optional&#40;number&#41;&#10;    rrdatas &#61; optional&#40;list&#40;string&#41;, &#91;&#93;&#41;&#10;  &#125;&#41;&#41;, &#123;&#125;&#41;&#10;&#125;&#41;&#41;">map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> |  | <code>&#123;&#125;</code> |
| [essential_contacts](variables.tf#L59) | Email used for essential contacts, unset if null. | <code>string</code> |  | <code>null</code> |
| [factories_config](variables.tf#L65) | Configuration for network resource factories. | <code title="object&#40;&#123;&#10;  data_dir              &#61; optional&#40;string, &#34;data&#34;&#41;&#10;  dns_policy_rules_file &#61; optional&#40;string, &#34;data&#47;dns-policy-rules.yaml&#34;&#41;&#10;  firewall_policy_name  &#61; optional&#40;string, &#34;net-default&#34;&#41;&#10;&#125;&#41;">object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code title="&#123;&#10;  data_dir &#61; &#34;data&#34;&#10;&#125;">&#123;&#8230;&#125;</code> |
| [fast_features](variables.tf#L211) | FAST features enabled. | <code>any</code> |  | <code>null</code> |
| [firewall_rules](variables.tf#L281) | Firewall rules for each VPC / environment spoke. | <code title="map&#40;object&#40;&#123;&#10;  ingress &#61; optional&#40;map&#40;object&#40;&#123;&#10;    description          &#61; optional&#40;string&#41;&#10;    deny                 &#61; optional&#40;bool, false&#41;&#10;    source_ranges        &#61; optional&#40;list&#40;string&#41;&#41;&#10;    sources              &#61; optional&#40;list&#40;string&#41;&#41;&#10;    targets              &#61; optional&#40;list&#40;string&#41;&#41;&#10;    use_service_accounts &#61; optional&#40;bool, false&#41;&#10;    rules &#61; optional&#40;list&#40;object&#40;&#123;&#10;      protocol &#61; string&#10;      ports    &#61; optional&#40;list&#40;string&#41;&#41;&#10;    &#125;&#41;&#41;&#41;&#10;  &#125;&#41;&#41;, &#123;&#125;&#41;&#10;  egress &#61; optional&#40;map&#40;object&#40;&#123;&#10;    description          &#61; optional&#40;string&#41;&#10;    deny                 &#61; optional&#40;bool, true&#41;&#10;    destination_ranges   &#61; optional&#40;list&#40;string&#41;&#41;&#10;    targets              &#61; optional&#40;list&#40;string&#41;&#41;&#10;    use_service_accounts &#61; optional&#40;bool, false&#41;&#10;    rules &#61; optional&#40;list&#40;object&#40;&#123;&#10;      protocol &#61; string&#10;      ports    &#61; optional&#40;list&#40;string&#41;&#41;&#10;    &#125;&#41;&#41;&#41;&#10;  &#125;&#41;&#41;, &#123;&#125;&#41;&#10;&#125;&#41;&#41;">map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> |  | <code>&#123;&#125;</code> |
| [groups](variables.tf#L217) | IAM groups mapping. | <code>any</code> |  | <code>null</code> |
| [logging](variables.tf#L205) | Logging configuration. | <code>any</code> |  | <code>null</code> |
| [outputs_location](variables.tf#L105) | Path where providers and tfvars files for the following stages are written. Leave empty to disable. | <code>string</code> |  | <code>null</code> |
| [proxy_subnets](variables.tf#L253) | VPC proxy-only subnet CIDRs keyed by environment. | <code>map&#40;string&#41;</code> |  | <code>&#123;&#125;</code> |
| [psa_ranges](variables.tf#L122) | IP ranges used for Private Service Access (e.g. CloudSQL). Ranges is in name => range format. | <code title="object&#40;&#123;&#10;  dev &#61; optional&#40;list&#40;object&#40;&#123;&#10;    ranges         &#61; map&#40;string&#41;&#10;    export_routes  &#61; optional&#40;bool, false&#41;&#10;    import_routes  &#61; optional&#40;bool, false&#41;&#10;    peered_domains &#61; optional&#40;list&#40;string&#41;, &#91;&#93;&#41;&#10;  &#125;&#41;&#41;, &#91;&#93;&#41;&#10;  prod &#61; optional&#40;list&#40;object&#40;&#123;&#10;    ranges         &#61; map&#40;string&#41;&#10;    export_routes  &#61; optional&#40;bool, false&#41;&#10;    import_routes  &#61; optional&#40;bool, false&#41;&#10;    peered_domains &#61; optional&#40;list&#40;string&#41;, &#91;&#93;&#41;&#10;  &#125;&#41;&#41;, &#91;&#93;&#41;&#10;&#125;&#41;">object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>&#123;&#125;</code> |
| [regime_mapping](variables.tf#L223) | Compliance regime shorthand mapping. | <code>any</code> |  | <code>null</code> |
| [service_accounts](variables.tf#L150) | Automation service accounts in name => email format. | <code title="object&#40;&#123;&#10;  data-platform-dev    &#61; string&#10;  data-platform-prod   &#61; string&#10;  gke-dev              &#61; string&#10;  gke-prod             &#61; string&#10;  project-factory-dev  &#61; string&#10;  project-factory-prod &#61; string&#10;&#125;&#41;">object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>null</code> |
| [subnets](variables.tf#L229) | VPC subnet configurations keyed by network name. | <code title="map&#40;list&#40;object&#40;&#123;&#10;  name                             &#61; string&#10;  ip_cidr_range                    &#61; string&#10;  region                           &#61; string&#10;  description                      &#61; optional&#40;string&#41;&#10;  enable_private_access            &#61; optional&#40;bool, true&#41;&#10;  allow_subnet_cidr_routes_overlap &#61; optional&#40;bool&#41;&#10;  flow_logs_config &#61; optional&#40;object&#40;&#123;&#10;    aggregation_interval &#61; optional&#40;string&#41;&#10;    filter_expression    &#61; optional&#40;string&#41;&#10;    flow_sampling        &#61; optional&#40;number&#41;&#10;    metadata             &#61; optional&#40;string&#41;&#10;    metadata_fields      &#61; optional&#40;list&#40;string&#41;&#41;&#10;  &#125;&#41;&#41;&#10;  secondary_ip_ranges &#61; optional&#40;map&#40;string&#41;&#41;&#10;  iam                 &#61; optional&#40;map&#40;list&#40;string&#41;&#41;, &#123;&#125;&#41;&#10;  tenant              &#61; optional&#40;string&#41;&#10;&#125;&#41;&#41;&#41;">map&#40;list&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;&#41;</code> |  | <code>&#123;&#125;</code> |
| [vmseries_image](variables.tf#L178) | The image name from which to boot an instance, including a license type (bundle/flex) and version. | <code>string</code> |  | <code>&#34;vmseries-112&#34;</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [host_project_ids](outputs.tf#L62) | Network project ids. |  |
| [host_project_numbers](outputs.tf#L67) | Network project numbers. |  |
| [ngfw_password](outputs.tf#L82) | Password for authenticating to the NGFW. | ✓ |
| [tfvars](outputs.tf#L88) | Terraform variables file for the following stages. | ✓ |
<!-- END TFDOC -->
