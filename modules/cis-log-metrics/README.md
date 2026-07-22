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

# CIS Log Metrics Module

This module creates log-based metrics to satisfy the CIS Google Cloud Computing Foundation Benchmark requirements for monitoring and alerting.

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

This module creates the underlying log-based metrics required for CIS compliance alerts. It parses Cloud Logging data to track specific events like project ownership changes, IAM modifications, and network firewall changes.

```hcl
module "cis_log_metrics" {
  source  = "./fabric/modules/cis-log-metrics"
  project = var.project_id
}
# tftest modules=1 resources=8
```

<!-- BEGIN_TF_DOCS -->

## Requirements

No requirements.

## Providers

| Name                                                      | Version |
| --------------------------------------------------------- | ------- |
| <a name="provider_google"></a> [google](#provider_google) | n/a     |

## Modules

No modules.

## Resources

| Name                                                                                                                                  | Type     |
| ------------------------------------------------------------------------------------------------------------------------------------- | -------- |
| [google_logging_metric.logging_metric](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/logging_metric) | resource |

## Inputs

| Name                                                   | Description | Type     | Default | Required |
| ------------------------------------------------------ | ----------- | -------- | ------- | :------: |
| <a name="input_project"></a> [project](#input_project) | Project ID. | `string` | n/a     |   yes    |

## Outputs

No outputs.

<!-- END_TF_DOCS -->
