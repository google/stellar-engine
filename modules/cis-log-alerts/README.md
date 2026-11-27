# CIS Log Alerts Module

This module provisions log-based alerts to satisfy the CIS Google Cloud Computing Foundation Benchmark requirements for monitoring and alerting.

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

This module creates a set of required log-based alerts using Cloud Monitoring. It provisions an email notification channel and links it to alert policies based on specific log metrics.

```hcl
module "cis-log-alerts" {
  source             = "./fabric/modules/cis-log-alerts"
  project            = var.project_id
  alert_email        = "security-alerts@example.com"
  combiner           = "OR"
  comparison         = "COMPARISON_GT"
  duration           = "0s"
  alignment_period   = "60s"
  per_series_aligner = "ALIGN_RATE"
}
# tftest modules=1 resources=9
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

| Name                                                                                                                                                           | Type     |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- |
| [google_monitoring_alert_policy.alert_policy](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/monitoring_alert_policy)          | resource |
| [google_monitoring_notification_channel.email](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/monitoring_notification_channel) | resource |

## Inputs

| Name                                                                                             | Description                                          | Type           | Default | Required |
| ------------------------------------------------------------------------------------------------ | ---------------------------------------------------- | -------------- | ------- | :------: |
| <a name="input_alert_email"></a> [alert_email](#input_alert_email)                               | Alert email.                                         | `string`       | n/a     |   yes    |
| <a name="input_alignment_period"></a> [alignment_period](#input_alignment_period)                | Alignment period.                                    | `string`       | n/a     |   yes    |
| <a name="input_combiner"></a> [combiner](#input_combiner)                                        | Combiner (AND/OR).                                   | `string`       | n/a     |   yes    |
| <a name="input_comparison"></a> [comparison](#input_comparison)                                  | Comparison.                                          | `string`       | n/a     |   yes    |
| <a name="input_duration"></a> [duration](#input_duration)                                        | Duration for alert.                                  | `string`       | n/a     |   yes    |
| <a name="input_notification_channels"></a> [notification_channels](#input_notification_channels) | Additional notification channels for alert policies. | `list(string)` | `[]`    |    no    |
| <a name="input_per_series_aligner"></a> [per_series_aligner](#input_per_series_aligner)          | Per series aligner.                                  | `string`       | n/a     |   yes    |
| <a name="input_project"></a> [project](#input_project)                                           | Project ID.                                          | `string`       | n/a     |   yes    |

## Outputs

No outputs.

<!-- END_TF_DOCS -->
