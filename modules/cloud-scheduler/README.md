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
module "pubsub_job" {
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
module "http_job" {
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
| [description](variables.tf#L1) | Job description. | <code>string</code> | ✓ |  |
| [http_target](variables.tf#L6) | HTTP Target for job. | <code title="object&#40;&#123;&#10;  http_method &#61; optional&#40;string&#41;&#10;  uri         &#61; optional&#40;string&#41;&#10;  body        &#61; optional&#40;string&#41;&#10;  headers     &#61; optional&#40;map&#40;string&#41;&#41;&#10;&#125;&#41;&#10;&#10;&#10;default &#61; null">object&#40;&#123;&#8230;default &#61; null</code> | ✓ |  |
| [name](variables.tf#L24) | Job name. | <code>string</code> | ✓ |  |
| [project_id](variables.tf#L29) | Project ID. | <code>string</code> | ✓ |  |
| [pubsub_target](variables.tf#L34) | Pubsub target for job. | <code title="object&#40;&#123;&#10;  topic_id &#61; optional&#40;string&#41;&#10;  data     &#61; optional&#40;string&#41;&#10;  attributes &#61; optional&#40;map&#40;string&#41;&#41;&#10;  new_topic &#61; optional&#40;object&#40;&#123;&#10;    create       &#61; optional&#40;bool&#41;&#10;    name         &#61; optional&#40;string&#41;&#10;    kms_key_name &#61; optional&#40;string&#41;&#10;  &#125;&#41;&#41;&#10;&#125;&#41;&#10;&#10;&#10;default &#61; &#123;&#10;  topic_id   &#61; null&#10;  data       &#61; null&#10;  new_topic  &#61; null&#10;  attributes &#61; null&#10;&#125;">object&#40;&#123;&#8230;&#125;</code> | ✓ |  |
| [retry_config](variables.tf#L55) | Retry config. | <code title="object&#40;&#123;&#10;  retry_count          &#61; optional&#40;number, null&#41;&#10;  max_retry_duration   &#61; optional&#40;string, null&#41;&#10;  min_backoff_duration &#61; optional&#40;string, null&#41;&#10;  max_backoff_duration &#61; optional&#40;string, null&#41;&#10;  max_doublings        &#61; optional&#40;number, null&#41;&#10;&#125;&#41;&#10;&#10;&#10;default &#61; null">object&#40;&#123;&#8230;default &#61; null</code> | ✓ |  |
| [schedule](variables.tf#L68) | Schedule to run job. | <code>string</code> | ✓ |  |
| [trigger_type](variables.tf#L74) | Type of trigger for the function. Valid values are 'pubsub' or 'http'. | <code>string</code> | ✓ |  |
| [kms_key](variables.tf#L18) | KMS key name. | <code>string</code> |  | <code>null</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [id](outputs.tf#L1) | Job ID. |  |
| [state](outputs.tf#L6) | Job state. |  |
<!-- END TFDOC -->
