# Beyondcorp

This module simplifies the deployment and configuration of BeyondCorp.

<!-- BEGIN TOC -->
- [Variables](#variables)
- [Outputs](#outputs)
<!-- END TOC -->
<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [endpoint_name](variables.tf#L15) | Name for endpoint. | <code>string</code> | ✓ |  |
| [iap_user_email](variables.tf#L20) | User or group email for IAP access. | <code>string</code> | ✓ |  |
| [oauth_client_id](variables.tf#L25) | OAuth Client ID for IAP. | <code>string</code> | ✓ |  |
| [oauth_client_secret](variables.tf#L30) | OAuth Client Secret for IAP. | <code>string</code> | ✓ |  |
| [organization_id](variables.tf#L35) | GCP Organization ID. | <code>string</code> | ✓ |  |
| [project_id](variables.tf#L46) | GCP Project ID. | <code>string</code> | ✓ |  |
| [region](variables.tf#L51) | Region. | <code>string</code> | ✓ |  |
| [policy_title](variables.tf#L40) | Title for the Access Context Manager Policy. | <code>string</code> |  | <code>&#34;BeyondCorp Policy&#34;</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [endpoint_name](outputs.tf#L15) | Name of the endpoint that was created. |  |
<!-- END TFDOC -->
