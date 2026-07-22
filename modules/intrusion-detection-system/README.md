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

# Intrusion Detection System Module

This module implements Cloud Intrusion Detection System (Cloud IDS) resources, including IDS endpoints and endpoint attachments, for network threat detection.

## TOC

<!-- BEGIN TOC -->

- [TOC](#toc)
- [Basic Usage](#basic-usage)
- [Requirements](#requirements)
- [Providers](#providers)
- [Modules](#modules)
- [Resources](#resources)
- [Inputs](#inputs)
- [Outputs](#outputs)
<!-- END TOC -->

## Basic Usage

This module provisions a Cloud IDS endpoint and configures a packet mirroring policy to forward traffic from a specific subnet to the IDS endpoint for threat detection.

```hcl
module "intrusion_detection_system" {
  source                               = "./fabric/modules/intrusion-detection-system"
  project                              = var.project_id
  ids_name                             = "cloud-ids-endpoint"
  landing_network                      = "my-landing-vpc"
  landing_vpc_network                  = "my-landing-vpc"
  network_region                       = "us-east4"
  network_zone                         = "us-east4-c"
  subnet                               = "my-subnet-name"
  create_service_networking_connection = true
}
# tftest modules=1 resources=3
```

<!-- BEGIN_TF_DOCS -->

## Requirements

| Name                                                                           | Version            |
| ------------------------------------------------------------------------------ | ------------------ |
| <a name="requirement_terraform"></a> [terraform](#requirement_terraform)       | >= 1.7.4           |
| <a name="requirement_google"></a> [google](#requirement_google)                | >= 6.21.0, < 7.0.0 |
| <a name="requirement_google-beta"></a> [google-beta](#requirement_google-beta) | >= 6.21.0, < 7.0.0 |

## Providers

| Name                                                      | Version            |
| --------------------------------------------------------- | ------------------ |
| <a name="provider_google"></a> [google](#provider_google) | >= 6.21.0, < 7.0.0 |

## Modules

No modules.

## Resources

| Name                                                                                                                                                                        | Type        |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------- |
| [google_cloud_ids_endpoint.ids_endpoint](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/cloud_ids_endpoint)                                 | resource    |
| [google_compute_global_address.ids_private_ip](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/compute_global_address)                       | resource    |
| [google_compute_packet_mirroring.cloud_ids_packet_mirroring](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/compute_packet_mirroring)       | resource    |
| [google_service_networking_connection.private_vpc_connection](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/service_networking_connection) | resource    |
| [google_compute_network.vpc_network](https://registry.terraform.io/providers/hashicorp/google/latest/docs/data-sources/compute_network)                                     | data source |

## Inputs

| Name                                                                                                                                          | Description                                                                    | Type           | Default                   | Required |
| --------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------ | -------------- | ------------------------- | :------: |
| <a name="input_cidr_ranges_filter"></a> [cidr_ranges_filter](#input_cidr_ranges_filter)                                                       | ranges that apply as a filter on ingress or egress IP in the IPV4 header       | `list(any)`    | `null`                    |    no    |
| <a name="input_create_service_networking_connection"></a> [create_service_networking_connection](#input_create_service_networking_connection) | Whether to create service networking connection and IP range.                  | `bool`         | `true`                    |    no    |
| <a name="input_direction_filter"></a> [direction_filter](#input_direction_filter)                                                             | Direction of traffic to mirror. Possible values are INGRESS, EGRESS, and BOTH. | `string`       | `"BOTH"`                  |    no    |
| <a name="input_ids_name"></a> [ids_name](#input_ids_name)                                                                                     | Name of IDS.                                                                   | `string`       | n/a                       |   yes    |
| <a name="input_ids_private_ip_prefix_length"></a> [ids_private_ip_prefix_length](#input_ids_private_ip_prefix_length)                         | n/a                                                                            | `string`       | `24`                      |    no    |
| <a name="input_ids_private_ip_range_name"></a> [ids_private_ip_range_name](#input_ids_private_ip_range_name)                                  | n/a                                                                            | `string`       | `"ids-private-address-1"` |    no    |
| <a name="input_instance_list"></a> [instance_list](#input_instance_list)                                                                      | Instance list to monitor with Cloud IDS                                        | `list(string)` | `null`                    |    no    |
| <a name="input_ip_protocols_filter"></a> [ip_protocols_filter](#input_ip_protocols_filter)                                                    | IP Protocols filter for packet mirroing policy.                                | `list(any)`    | `null`                    |    no    |
| <a name="input_landing_network"></a> [landing_network](#input_landing_network)                                                                | Landing network name for IDS                                                   | `string`       | n/a                       |   yes    |
| <a name="input_landing_vpc_network"></a> [landing_vpc_network](#input_landing_vpc_network)                                                    | VPC network name for IDS                                                       | `string`       | n/a                       |   yes    |
| <a name="input_network_region"></a> [network_region](#input_network_region)                                                                   | Region that network exist in                                                   | `string`       | `"us-east4"`              |    no    |
| <a name="input_network_zone"></a> [network_zone](#input_network_zone)                                                                         | Network zone for IDS                                                           | `string`       | `"us-east4-c"`            |    no    |
| <a name="input_packet_mirroring_policy_name"></a> [packet_mirroring_policy_name](#input_packet_mirroring_policy_name)                         | Name of packet mirror policy                                                   | `string`       | `"testpolicy"`            |    no    |
| <a name="input_project"></a> [project](#input_project)                                                                                        | GCP Project ID to deploy into                                                  | `string`       | n/a                       |   yes    |
| <a name="input_project_id"></a> [project_id](#input_project_id)                                                                               | Id of the project you will like to use.                                        | `string`       | `null`                    |    no    |
| <a name="input_severity"></a> [severity](#input_severity)                                                                                     | Display name of the service account to create.                                 | `string`       | `"MEDIUM"`                |    no    |
| <a name="input_subnet"></a> [subnet](#input_subnet)                                                                                           | subnet used for IDS                                                            | `string`       | `null`                    |    no    |
| <a name="input_subnet_list"></a> [subnet_list](#input_subnet_list)                                                                            | Subnet list to monitor with Cloud IDS                                          | `list(any)`    | `null`                    |    no    |
| <a name="input_tag_list"></a> [tag_list](#input_tag_list)                                                                                     | Tag list to monitor with Cloud IDS                                             | `list(string)` | `null`                    |    no    |
| <a name="input_threat_exceptions"></a> [threat_exceptions](#input_threat_exceptions)                                                          | Threat_exceptions list to excluded from generating alerts. Limit: 99 IDs.      | `any`          | `null`                    |    no    |

## Outputs

| Name                                                                                                                    | Description           |
| ----------------------------------------------------------------------------------------------------------------------- | --------------------- |
| <a name="output_ids_endpoint_severity"></a> [ids_endpoint_severity](#output_ids_endpoint_severity)                      | IDS Endpoint severity |
| <a name="output_ids_name"></a> [ids_name](#output_ids_name)                                                             | n/a                   |
| <a name="output_ids_private_ip_range_name"></a> [ids_private_ip_range_name](#output_ids_private_ip_range_name)          | n/a                   |
| <a name="output_packet_mirroring_policy_name"></a> [packet_mirroring_policy_name](#output_packet_mirroring_policy_name) | n/a                   |

<!-- END_TF_DOCS -->
