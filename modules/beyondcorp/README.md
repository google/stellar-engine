# Beyondcorp

This module simplifies the deployment and configuration of BeyondCorp.

<!-- BEGIN TOC -->
- [Provider configuration](#provider-configuration)
- [Variables](#variables)
- [Outputs](#outputs)
<!-- END TOC -->

## Provider configuration

This module declares no `provider` blocks. It inherits the `google` provider configuration of the calling root module, or the configuration that you pass through the `providers` argument. Every project-scoped resource reads the project from the `project_id` variable, so the module takes no region input.

When you authenticate with user Application Default Credentials, the Access Context Manager API needs a quota project. Set `billing_project` and `user_project_override` on the provider in the root module:

```hcl
provider "google" {
  billing_project       = "my-project"
  user_project_override = true
}
```
<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [endpoint_name](variables.tf#L15) | Name for endpoint. | <code>string</code> | ✓ |  |
| [iap_user_email](variables.tf#L20) | User or group email for IAP access. | <code>string</code> | ✓ |  |
| [oauth_client_id](variables.tf#L25) | OAuth Client ID for IAP. | <code>string</code> | ✓ |  |
| [oauth_client_secret](variables.tf#L30) | OAuth Client Secret for IAP. | <code>string</code> | ✓ |  |
| [organization_id](variables.tf#L36) | GCP Organization ID. | <code>string</code> | ✓ |  |
| [project_id](variables.tf#L47) | GCP Project ID. | <code>string</code> | ✓ |  |
| [policy_title](variables.tf#L41) | Title for the Access Context Manager Policy. | <code>string</code> |  | <code>&#34;BeyondCorp Policy&#34;</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [endpoint_name](outputs.tf#L15) | Name of the endpoint that was created. |  |
<!-- END TFDOC -->
