# Cloud Schedulder Module
This module manages the creation of a Cloud Scheduler Job

<!-- BEGIN TOC -->
- [Example Usage](#example-usage)
  - [PubSub Job](#pubsub-job)
  - [HTTP Job](#http-job)
- [Variables](#variables)
- [Outputs](#outputs)
<!-- END TOC -->

## Example Usage
### PubSub Job
```hcl
module "pubsub-job" {
  source      = "../../../modules/cloud-scheduler"
  name        = "name"
  description = "description"
  project_id  = "your-project"
  schedule    = "schedule

  trigger_type = "pubsub"
  pubsub_target = {
    data     = base64encode("test")
    topic_id = "projects/<your-project>/topics/<your-topic>"
  }
}
```

### HTTP Job

```hcl
module "http-job" {
  source      = "../../../modules/cloud-scheduler"
  name        = "name"
  description = "description"
  project_id  = "your-project"
  schedule    = "schedule"

  trigger_type = "http"
  http_target = {
    http_method = "POST"
    uri = "http://www.example.com"
    body = base64encode("{\"foo\":\"bar\"}")
    headers = {
      "Content-Type" = "application/json"
    }
  }
}
```
<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [description](variables.tf#L15) | Job description. | <code>string</code> | ✓ |  |
| [http_target](variables.tf#L20) | HTTP Target for job. | <code>object&#40;&#123;&#8230;default &#61; null</code> | ✓ |  |
| [name](variables.tf#L38) | Job name. | <code>string</code> | ✓ |  |
| [project_id](variables.tf#L43) | Project ID. | <code>string</code> | ✓ |  |
| [pubsub_target](variables.tf#L48) | Pubsub target for job. | <code>object&#40;&#123;&#8230;&#125;</code> | ✓ |  |
| [retry_config](variables.tf#L69) | Retry config. | <code>object&#40;&#123;&#8230;default &#61; null</code> | ✓ |  |
| [schedule](variables.tf#L82) | Schedule to run job. | <code>string</code> | ✓ |  |
| [trigger_type](variables.tf#L88) | Type of trigger for the function. Valid values are 'pubsub' or 'http'. | <code>string</code> | ✓ |  |
| [kms_key](variables.tf#L32) | KMS key name. | <code>string</code> |  | <code>null</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [id](outputs.tf#L15) | Job ID. |  |
| [state](outputs.tf#L20) | Job state. |  |
<!-- END TFDOC -->
