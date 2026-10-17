# App Engine
This module deploys a Google Cloud App Engine Instance

# Note
App Engine applications cannot be deleted once they're created; you have to delete the entire project to delete the application. Terraform will report the application has been successfully deleted; this is a limitation of Terraform, and will go away in the future. Terraform is not able to delete App Engine applications. https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/app_engine_application

<!-- BEGIN TOC -->
- [Note](#note)
- [Variables](#variables)
- [Outputs](#outputs)
<!-- END TOC -->
<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [location_id](variables.tf#L48) | Region to create your App Engine resource. | <code>string</code> | ✓ |  |
| [project](variables.tf#L53) | Project to create your App Engine resource. | <code>string</code> | ✓ |  |
| [auth_domain](variables.tf#L15) | The domain to authenticate users with when using App Engine's User API. | <code>string</code> |  | <code>null</code> |
| [database_type](variables.tf#L21) | The type of the Cloud Firestore or Cloud Datastore database associated with this application. | <code>string</code> |  | <code>null</code> |
| [feature_settings](variables.tf#L27) | A block of optional settings to configure specific App Engine features. | <code title="object&#40;&#123;&#10;  split_health_checks &#61; optional&#40;bool, true&#41;&#10;&#125;&#41;&#10;&#10;&#10;nullable &#61; true">object&#40;&#123;&#8230;nullable &#61; true</code> |  | <code>&#123;&#125;</code> |
| [iap](variables.tf#L37) | Settings for enabling Cloud Identity Aware Proxy. | <code title="object&#40;&#123;&#10;  oauth2_client_id     &#61; optional&#40;string, &#34;&#34;&#41;&#10;  oauth2_client_secret &#61; optional&#40;string, &#34;&#34;&#41;&#10;&#125;&#41;&#10;&#10;&#10;nullable &#61; true">object&#40;&#123;&#8230;nullable &#61; true</code> |  | <code>&#123;&#125;</code> |
| [serving_status](variables.tf#L58) | The serving status of the app. | <code>string</code> |  | <code>null</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [app_id](outputs.tf#L15) | Identifier of the app. |  |
| [code_bucket](outputs.tf#L20) | GCS bucket where the app code is stored. |  |
| [default_bucket](outputs.tf#L25) | GCS bucket where the app content is stored. |  |
| [default_hostname](outputs.tf#L30) | Default hostname for the app. |  |
| [gcr_domain](outputs.tf#L35) | GCR domain used for storing managed Docker images. |  |
| [iap_config](outputs.tf#L40) | IAP configuration. |  |
| [id](outputs.tf#L45) | An identifier for the resource. |  |
| [name](outputs.tf#L50) | Unique name of the app. |  |
| [url_dispatch_rules](outputs.tf#L55) | List of dispatch rule blocks. |  |
<!-- END TFDOC -->
