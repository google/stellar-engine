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
| [endpoint_name](variables.tf#L1) | Name for endpoint. | <code>string</code> | ✓ |  |
| [iap_user_email](variables.tf#L6) | User or group email for IAP access. | <code>string</code> | ✓ |  |
| [oauth_client_id](variables.tf#L11) | OAuth Client ID for IAP. | <code>string</code> | ✓ |  |
| [oauth_client_secret](variables.tf#L16) | OAuth Client Secret for IAP. | <code>string</code> | ✓ |  |
| [organization_id](variables.tf#L21) | GCP Organization ID. | <code>string</code> | ✓ |  |
| [project_id](variables.tf#L32) | GCP Project ID. | <code>string</code> | ✓ |  |
| [region](variables.tf#L37) | Region. | <code>string</code> | ✓ |  |
| [policy_title](variables.tf#L26) | Title for the Access Context Manager Policy. | <code>string</code> |  | <code>&#34;BeyondCorp Policy&#34;</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [endpoint_name](outputs.tf#L1) | Name of the endpoint that was created. |  |
<!-- END TFDOC -->
