# PSC Blueprint
This blueprint demonstrates how to deploy a Private Service Connection on Google Cloud Platform (GCP). It provides a secure and flexible solution for consumers to access managed services.

<!-- BEGIN TOC -->
- [Introduction to PSC](#introduction-to-psc)
- [Disclaimer](#disclaimer)
- [Deployment Steps](#deployment-steps)
- [Variables](#variables)
- [Outputs](#outputs)
<!-- END TOC -->

## Introduction to PSC
Private Service Connect is a capability of Google Cloud networking that allows consumers to access managed services privately from inside their VPC network. Similarly, it allows managed service producers to host these services in their own separate VPC networks and offer a private connection to their consumers.

## Disclaimer
- The present GCP Terraform Module in this project is set up and intended to be implemented in an IL5 or FEDRAMP High environment using the Assured Workloads within the Google Cloud Platform (GCP) organization.

## Deployment Steps
1. Run ```cp terraform.tfvars.sample terraform.tfvars``` to copy the sample variables to your own tfvars file.
2. Update the variables as necessary in your tfvars file.
3. The usual terraform commands will do the work. To provision this example, run the following from within this directory:

```terraform init```<br />
```terraform plan``` to see the infrastructure plan<br />
```terraform apply``` to apply the infrastructure build<br />
```terraform destroy``` only if you wish to destroy the built infrastructure<br />

Verification of a successful deployment?
Look at the Private Service Connect tab under Network Services. You should see the newly created PSC under 'Endpoints'. You can also view the newly created DNS zones under the Cloud DNS tab.
<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [main_project_id](variables.tf#L33) | The GCP Project ID where the PSC will be created. | <code>string</code> | ✓ |  |
| [network_name](variables.tf#L38) | The network ID where the PSC will be created. | <code>string</code> | ✓ |  |
| [region](variables.tf#L49) | The GCP region. | <code>string</code> | ✓ |  |
| [address](variables.tf#L15) | The IP address of the private service connection. | <code>string</code> |  | <code>&#34;10.5.5.5&#34;</code> |
| [dns_code](variables.tf#L21) | Code to identify DNS resources in the form of `{dns_code}-{dns_type}`. | <code>string</code> |  | <code>&#34;dz&#34;</code> |
| [ip_name](variables.tf#L27) | Name of the private IP allocation. | <code>string</code> |  | <code>&#34;psconnect-ip&#34;</code> |
| [psc_name](variables.tf#L43) | Name of the forwarding rule used to create the PSC. | <code>string</code> |  | <code>&#34;pscforwardingrule&#34;</code> |
| [service](variables.tf#L54) | Target resource to receive the matched traffic. Only `all-apis` and `vpc-sc` are valid. | <code>string</code> |  | <code>&#34;vpc-sc&#34;</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [dns_zone_gcr_name](outputs.tf#L15) | Name for Managed DNS zone for GCR. |  |
| [dns_zone_googleapis_name](outputs.tf#L20) | Name for Managed DNS zone for GoogleAPIs. |  |
| [dns_zone_pkg_dev_name](outputs.tf#L25) | Name for Managed DNS zone for PKG_DEV. |  |
| [global_address_id](outputs.tf#L30) | An identifier for the global address created for the private service connect with format `projects/{{project}}/global/addresses/{{name}}`. |  |
| [private_ip_allocation](outputs.tf#L35) | The IP that was allocated for this service connection. |  |
<!-- END TFDOC -->
