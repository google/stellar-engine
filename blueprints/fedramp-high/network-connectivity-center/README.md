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

# Network Connectivity Center Blueprint
This blueprint demonstrates how to use the Network Connectivity Center on Google Cloud Platform (GCP).

<!-- BEGIN TOC -->
- [Introduction to NCC](#introduction-to-ncc)
- [Notes](#notes)
- [Disclaimer](#disclaimer)
- [Deployment Steps](#deployment-steps)
- [Variables](#variables)
- [Outputs](#outputs)
<!-- END TOC -->

## Introduction to NCC
Network Connectivity Center is an orchestration framework that simplifies network connectivity among spoke resources that are connected to a central management resource called a hub.
With the hub and spoke connectivity, you can do the following:

- Connect multiple VPC networks to one another. The VPC networks can be located across different projects in the same Google Cloud organization or different organizations.
- Connect multiple VPC networks to on-premise or other cloud provider networks. These external networks can be reachable through any type of hybrid spoke. This approach is known as site-to-cloud connectivity.
- Use Router appliance VMs to manage connectivity between your VPC networks.
- Use a Google Cloud VPC network as an enterprise wide area network (WAN) to connect networks that are outside of Google Cloud. You can establish connectivity between your external sites by using any type of hybrid spoke. This approach is known as site-to-site connectivity.

## Notes
- This blueprint only supports VPC spokes, if you wish to learn more about what is possible with NCC use this [link](https://cloud.google.com/network-connectivity/docs/network-connectivity-center/concepts/overview).
- If you choose the STAR topology, any VPCs in the same project as the hub will be considered "center" spokes. All other VPCs will be considered "edge" spokes.
- You can choose to enable Private Service Connect [connection propagation](https://cloud.google.com/network-connectivity/docs/network-connectivity-center/concepts/psc-propagated-connection-overview).

## Disclaimer
- The present GCP Terraform Module in this project is set up and intended to be implemented in a FEDRAMP High environment using the Assured Workloads within the Google Cloud Platform (GCP) organization.

## Deployment Steps
1. Run ```cp terraform.tfvars.sample terraform.tfvars``` to copy the sample variables to your own tfvars file.
2. Update the variables as necessary in your tfvars file.
3. The usual terraform commands will do the work. To provision this example, run the following from within this directory:

```terraform init```<br />
```terraform plan``` to see the infrastructure plan<br />
```terraform apply``` to apply the infrastructure build<br />
```terraform destroy``` only if you wish to destroy the built infrastructure<br />

To verify a successful deployment, look for NCC in the Google Cloud Console. You should see a newly created hub with any specified spokes attached.
<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [main_project_id](variables.tf#L1) | The GCP Project ID where the hub will be created. | <code>string</code> | ✓ |  |
| [region](variables.tf#L18) | The GCP region. | <code>string</code> | ✓ |  |
| [name](variables.tf#L6) | The name of the created NCC hub. | <code>string</code> |  | <code>&#34;example-ncc-hub&#34;</code> |
| [psc_prop](variables.tf#L12) | Whether or not private service connections can be propagated to other spokes in the network. | <code>bool</code> |  | <code>false</code> |
| [spokes](variables.tf#L23) | A list of spokes to be added to the NCC hub. | <code>map&#40;string&#41;</code> |  | <code>&#123;&#125;</code> |
| [topology](variables.tf#L30) | The topology of the network. Can be MESH or STAR. | <code>string</code> |  | <code>&#34;MESH&#34;</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [hub](outputs.tf#L1) | The NCC hub ID. |  |
| [spokes](outputs.tf#L6) | The NCC spokes. |  |
<!-- END TFDOC -->
