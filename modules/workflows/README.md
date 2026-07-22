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

# Workflows Module
Simple module for creating a workflow encryped by a CMEK. 

Takes in a file path to a yaml file for the workflow source code.

<!-- BEGIN TOC -->
- [Example Usage](#example-usage)
- [Variables](#variables)
- [Outputs](#outputs)
<!-- END TOC -->

## Example Usage

```hcl
module "workflows" {
  source = "../../../modules/workflows"
  project = var.project
  name = "example-workflow"
  region = var.region
  logging_level = var.logging_level
  env_vars = var.env_vars
  key = var.key
  file = var.file
}
```
<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [file](variables.tf#L19) | File path to the instructions for the workflow. | <code>string</code> | ✓ |  |
| [name](variables.tf#L37) | Name of the workflow. | <code>string</code> | ✓ |  |
| [project](variables.tf#L42) | The Google Project ID. | <code>string</code> | ✓ |  |
| [region](variables.tf#L47) | The Google Cloud region. | <code>string</code> | ✓ |  |
| [service_account](variables.tf#L52) | Service account for Workflows. | <code>string</code> | ✓ |  |
| [deletion_protection](variables.tf#L1) | Deletion proteciton. | <code>bool</code> |  | <code>true</code> |
| [description](variables.tf#L7) | Description of the workflow. | <code>string</code> |  | <code>null</code> |
| [env_vars](variables.tf#L13) | Environment variables made available to your workflow execution. | <code>map&#40;string&#41;</code> |  | <code>null</code> |
| [iam](variables.tf#L24) | Keyring IAM bindings in {ROLE => [MEMBERS]} format. | <code>map&#40;list&#40;string&#41;&#41;</code> |  | <code>&#123;&#125;</code> |
| [logging_level](variables.tf#L31) | Logging level of workflow executions. | <code>string</code> |  | <code>&#34;LOG_ERRORS_ONLY&#34;</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [service_account](outputs.tf#L1) | The workflow service account. |  |
| [workflow](outputs.tf#L6) | The newly created workflow. |  |
<!-- END TFDOC -->
