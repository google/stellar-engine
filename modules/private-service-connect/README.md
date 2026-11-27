# Private Service Connect

<!-- BEGIN TOC -->
- [Usage](#usage)
- [Requirements](#requirements)
- [Variables](#variables)
- [Outputs](#outputs)
<!-- END TOC -->

This module enables the usage of [Private Service Connect](https://cloud.google.com/vpc/docs/private-service-connect) for a specific subnetwork.

The resources created by this module are:

- Private DNS zone to configure `private.googleapis.com.` or `restricted.googleapis.com.`
- Private DNS zone to configure `gcr.io.`
- Private DNS zone to configure `pkg.dev.`
- Global Address resource to configure Private Service Connect endpoint
- Global Forwarding Rule resource to forward traffic to Google APIs

## Usage

Basic usage of this module is as follows:

```hcl
module "private-service-connect" {
  source = "./fabric/modules/private-service-connect"

  project_id                 = "my-project"
  network_self_link          = "projects/my-project/global/networks/my-vpc"
  private_service_connect_ip = "10.3.0.5"
  forwarding_rule_target     = "all-apis"
}
# tftest skip
```

Private Service Connect IP must fulfill requirements detailed in [IP address requirements](https://cloud.google.com/vpc/docs/configure-private-service-connect-apis#ip-address-requirements).

Target subnetwork must have Private Google Access enabled.

All egress traffic is allowed from VPC internal networks by default.

If a firewall rule blocks egress traffic, configure a [new egress rule](https://cloud.google.com/vpc/docs/using-firewalls#creating_firewall_rules) with these attributes:

- Direction of Egress
- Priority higher than the blocking egress rule
- Target tags matching your workload instances
- Destination filters for the Private Service Connect IP on `tcp:443`

## Requirements

- Cloud DNS API must be enabled.
- Service account running Terraform must have `dns.managedZones.*` permissions via `roles/dns.admin`.
<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [forwarding_rule_target](variables.tf#L29) | Target resource to receive the matched traffic. Only `all-apis` and `vpc-sc` are valid. | <code>string</code> | ✓ |  |
| [network_self_link](variables.tf#L39) | Network self link for Private Service Connect. | <code>string</code> | ✓ |  |
| [private_service_connect_ip](variables.tf#L44) | The internal IP to be used for the private service connect. | <code>string</code> | ✓ |  |
| [project_id](variables.tf#L55) | Project ID for Private Service Connect. | <code>string</code> | ✓ |  |
| [dns_code](variables.tf#L17) | Code to identify DNS resources in the form of `{dns_code}-{dns_type}`. | <code>string</code> |  | <code>&#34;dz&#34;</code> |
| [forwarding_rule_name](variables.tf#L23) | Forwarding rule resource name. The forwarding rule name for PSC Google APIs must be an 1-20 characters string with lowercase letters and numbers and must start with a letter. | <code>string</code> |  | <code>&#34;psc-forwarding-rule&#34;</code> |
| [private_service_connect_name](variables.tf#L49) | Private Service Connect endpoint name. Defaults to `psconnect-ip`. | <code>string</code> |  | <code>&#34;psconnect-ip&#34;</code> |
| [psc_global_access](variables.tf#L60) | This is used in PSC consumer ForwardingRule to control whether the PSC endpoint can be accessed from another region. Defaults to `false`. | <code>bool</code> |  | <code>false</code> |
| [service_directory_namespace](variables.tf#L66) | Service Directory namespace to register the forwarding rule under. | <code>string</code> |  | <code>null</code> |
| [service_directory_region](variables.tf#L72) | Service Directory region to register this global forwarding rule under. Defaults to `us-central1` if not defined. | <code>string</code> |  | <code>null</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [dns_zone_gcr_name](outputs.tf#L17) | Name for Managed DNS zone for GCR. |  |
| [dns_zone_googleapis_name](outputs.tf#L22) | Name for Managed DNS zone for GoogleAPIs. |  |
| [dns_zone_pkg_dev_name](outputs.tf#L27) | Name for Managed DNS zone for PKG_DEV. |  |
| [forwarding_rule_name](outputs.tf#L32) | Forwarding rule resource name. |  |
| [forwarding_rule_target](outputs.tf#L37) | Target resource to receive the matched traffic. Only `all-apis` and `vpc-sc` are valid. |  |
| [global_address_id](outputs.tf#L42) | An identifier for the global address created for the private service connect with format `projects/{{project}}/global/addresses/{{name}}`. |  |
| [private_service_connect_ip](outputs.tf#L47) | Private service connect IP. |  |
| [private_service_connect_name](outputs.tf#L56) | Private service connect name. |  |
<!-- END TFDOC -->
