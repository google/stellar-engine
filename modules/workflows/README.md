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
| [file](variables.tf#L33) | File path to the instructions for the workflow. | <code>string</code> | ✓ |  |
| [kms_key_self_link](variables.tf#L45) | The full self-link (projects/../locations/../keyRings/../cryptoKeys/..) of the existing KMS key to use for Workflow encryption (CMEK). | <code>string</code> | ✓ |  |
| [name](variables.tf#L56) | Name of the workflow. | <code>string</code> | ✓ |  |
| [project](variables.tf#L61) | The Google Project ID. | <code>string</code> | ✓ |  |
| [region](variables.tf#L66) | The Google Cloud region. | <code>string</code> | ✓ |  |
| [service_account](variables.tf#L71) | Service account for Workflows. | <code>string</code> | ✓ |  |
| [deletion_protection](variables.tf#L15) | Deletion proteciton. | <code>bool</code> |  | <code>true</code> |
| [description](variables.tf#L21) | Description of the workflow. | <code>string</code> |  | <code>null</code> |
| [env_vars](variables.tf#L27) | Environment variables made available to your workflow execution. | <code>map&#40;string&#41;</code> |  | <code>null</code> |
| [iam](variables.tf#L38) | Keyring IAM bindings in {ROLE => [MEMBERS]} format. | <code>map&#40;list&#40;string&#41;&#41;</code> |  | <code>&#123;&#125;</code> |
| [logging_level](variables.tf#L50) | Logging level of workflow executions. | <code>string</code> |  | <code>&#34;LOG_ERRORS_ONLY&#34;</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [service_account](outputs.tf#L15) | The workflow service account. |  |
| [workflow](outputs.tf#L20) | The newly created workflow. |  |
<!-- END TFDOC -->
