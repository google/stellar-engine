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
module "cis-log-metrics" {
  source  = "./fabric/modules/cis-log-metrics"
  project = var.project_id
}
# tftest modules=1 resources=8
```

<!-- BEGIN_TF_DOCS -->

## Requirements

| Name                                                                     | Version           |
| ------------------------------------------------------------------------ | ----------------- |
| <a name="requirement_terraform"></a> [terraform](#requirement_terraform) | >= 1.12.2         |
| <a name="requirement_google"></a> [google](#requirement_google)          | >= 8.6.0, < 9.0.0 |

## Providers

| Name                                                      | Version           |
| --------------------------------------------------------- | ----------------- |
| <a name="provider_google"></a> [google](#provider_google) | >= 8.6.0, < 9.0.0 |

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
