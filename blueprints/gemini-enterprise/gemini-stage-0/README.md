# Gemini Enterprise Stage 0 foundation

<!-- BEGIN TOC -->
- [1 Stage scope](#1-stage-scope)
- [2 Deployment steps](#2-deployment-steps)
- [Variables](#variables)
- [Outputs](#outputs)
<!-- END TOC -->

This stage deploys the foundational infrastructure, security controls, data stores, and Discovery Engine applications for Gemini Enterprise across FedRAMP Moderate, FedRAMP High, IL4, and IL5 environments. See the parent [Gemini Enterprise guide](../README.md) for full architecture and `deploy.sh` details.

## 1 Stage scope

This configuration provisions:

- VPC or Shared VPC attachment, load balancer IP reservation, and Discovery Engine network endpoint group.
- Cloud Armor regional security policy, Access Context Manager access levels, and Discovery Engine ACL and CMEK configuration.
- Cloud KMS encryption resources, GCS and BigQuery data stores, Discovery Engine search apps, Model Armor templates, and optional analytics pipelines.

## 2 Deployment steps

1. Configure remote GCS backend settings and `terraform.tfvars` from `terraform.tfvars.sample`.
2. Initialize, plan, and apply this stage before deploying `gemini-stage-1`:

```bash
terraform init -backend-config="bucket=my-state-bucket"
terraform plan
terraform apply
```
<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [access_policy_number](variables.tf#L43) | There can only be one Access Policy per GCP Org. Use gcloud access-context-manager policies list --organization <org-number> to list it. | <code>number</code> | ✓ |  |
| [admin_group](variables.tf#L96) | The email address of the admin user group for Gemini Enterprise. | <code>string</code> | ✓ |  |
| [domain](variables.tf#L226) | FQDN for the load-balancer hosted apps, where the subdomain will be prepended to. | <code>string</code> | ✓ |  |
| [environment](variables.tf#L249) | The environment identifier (e.g. prod, dev, staging). | <code>string</code> | ✓ |  |
| [main_project_id](variables.tf#L310) | The GCP Project name. | <code>string</code> | ✓ |  |
| [region](variables.tf#L333) | GCP Region to deploy into. | <code>string</code> | ✓ |  |
| [tenant](variables.tf#L356) | The tenant identifier (e.g. g4g). | <code>string</code> | ✓ |  |
| [user_groups](variables.tf#L373) | A list of email addresses or principal sets for the Gemini Enterprise users group. | <code>list&#40;string&#41;</code> | ✓ |  |
| [access_end_day](variables.tf#L17) | The day of the week when access ends, evaluated using CEL getDayOfWeek() where 0 is Sunday, 1 is Monday, ..., 6 is Saturday (0-6). | <code>number</code> |  | <code>5</code> |
| [access_end_hour](variables.tf#L27) | The hour (0-23) in the configured access_time_zone (default America/New_York) when access ends. | <code>number</code> |  | <code>21</code> |
| [access_expiration_timestamp](variables.tf#L33) | The timestamp when access expires (RFC 3339 format, e.g. 2028-01-01T00:00:00Z). | <code>string</code> |  | <code>&#34;2028-01-01T00:00:00Z&#34;</code> |
| [access_start_day](variables.tf#L48) | The day of the week when access starts, evaluated using CEL getDayOfWeek() where 0 is Sunday, 1 is Monday, ..., 6 is Saturday (0-6). | <code>number</code> |  | <code>1</code> |
| [access_start_hour](variables.tf#L58) | The hour (0-23) in the configured access_time_zone (default America/New_York) when access starts. | <code>number</code> |  | <code>7</code> |
| [access_time_zone](variables.tf#L64) | The timezone for time-based access controls (e.g. America/New_York). | <code>string</code> |  | <code>&#34;America&#47;New_York&#34;</code> |
| [acl_idp_type](variables.tf#L74) | The Identity Provider type for Discovery Engine ACLs. Options: 'GSUITE', 'THIRD_PARTY', 'GOOGLE_CLOUD_IDENTITY'. | <code>string</code> |  | <code>&#34;GOOGLE_CLOUD_IDENTITY&#34;</code> |
| [acl_workforce_pool_name](variables.tf#L84) | The resource name of the Workforce Identity Pool (required if acl_idp_type is 'THIRD_PARTY'). Format: locations/global/workforcePools/<pool_id>. | <code>string</code> |  | <code>&#34;&#34;</code> |
| [acl_workforce_provider_id](variables.tf#L90) | The ID of the Workforce Identity Pool Provider (required if acl_idp_type is 'THIRD_PARTY'). Format: <provider_id> (without acl_workforce_pool_name prefix). | <code>string</code> |  | <code>&#34;&#34;</code> |
| [allowed_ip_ranges](variables.tf#L101) | The IP range to allow traffic from. | <code>list&#40;string&#41;</code> |  | <code>&#91;&#93;</code> |
| [bq_data_store_configs](variables.tf#L107) | A map of configurations for BigQuery Data Stores. If create_dataset is true, it creates the dataset. Schema provides the structure for the data. | <code>map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> |  | <code>&#123;&#125;</code> |
| [cert_management_choice](variables.tf#L119) | Certificate management choice for external deployments: 'google_managed' or 'self_managed'. | <code>string</code> |  | <code>&#34;self_managed&#34;</code> |
| [cloud_armor_request_body_limit](variables.tf#L129) | Maximum request body size, based on the Content-Length header, allowed through the Cloud Armor policy. Regional policies only inspect the first 8KB of the body with preconfigured WAF rules, so larger requests are denied to prevent WAF bypass via oversized payloads. The rule runs in preview when cloud_armor_waf_preview is true or every WAF rule in data/cloudarmor.yaml is in preview. Set to null to disable. | <code>string</code> |  | <code>&#34;8KB&#34;</code> |
| [cloud_armor_waf_preview](variables.tf#L139) | Optional override for Cloud Armor WAF preview mode across OWASP rules and the request body size limit rule. When null, uses per-rule preview values from data/cloudarmor.yaml (false by default). | <code>bool</code> |  | <code>null</code> |
| [compliance_regime](variables.tf#L145) | Compliance regime this environment is deployed in (e.g. FEDRAMP_MODERATE, FEDRAMP_HIGH, IL4, IL5, NONE). | <code>string</code> |  | <code>&#34;NONE&#34;</code> |
| [create_data_stores](variables.tf#L161) | Whether to create example Data Stores (BigQuery, GCS) and associated CMEK config. | <code>bool</code> |  | <code>true</code> |
| [create_expire_access](variables.tf#L167) | Whether to create the Expiration access level. | <code>bool</code> |  | <code>true</code> |
| [create_ip_based_access](variables.tf#L173) | Whether to create the IP-based access level. | <code>bool</code> |  | <code>true</code> |
| [create_lenient_device_access](variables.tf#L179) | Whether to create the Lenient device access level. | <code>bool</code> |  | <code>true</code> |
| [create_moderate_device_access](variables.tf#L185) | Whether to create the Moderate device access level. | <code>bool</code> |  | <code>true</code> |
| [create_strict_device_access](variables.tf#L191) | Whether to create the Strict device access level. | <code>bool</code> |  | <code>true</code> |
| [create_time_access](variables.tf#L197) | Whether to create the Time-based access level. | <code>bool</code> |  | <code>true</code> |
| [create_us_access](variables.tf#L203) | Whether to create the US-only access level. | <code>bool</code> |  | <code>true</code> |
| [custom_domain](variables.tf#L209) | The fully qualified domain name (FQDN) to use for the Google-managed certificate. | <code>string</code> |  | <code>&#34;&#34;</code> |
| [deployment_type](variables.tf#L215) | Type of deployment: 'internal', 'external', or 'none'. | <code>string</code> |  | <code>&#34;external&#34;</code> |
| [enable_analytics](variables.tf#L231) | Enable analytics for Gemini Enterprise via Discovery Engine Audit Logs. | <code>bool</code> |  | <code>false</code> |
| [enable_chrome_enterprise_premium](variables.tf#L237) | Enable Chrome Enterprise Premium features (e.g., Zero Trust). | <code>bool</code> |  | <code>false</code> |
| [enable_data_store_cmek](variables.tf#L243) | Whether to encrypt Data Stores with CMEK. If false, Google-managed keys will be used. | <code>bool</code> |  | <code>true</code> |
| [gcs_data_store_configs](variables.tf#L254) | A map of configurations for Google Cloud Storage (GCS) Data Stores. If create_bucket is true, the script will create the bucket. | <code>map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> |  | <code>&#123;&#125;</code> |
| [gemini_apps](variables.tf#L264) | A map of Gemini Enterprise Search Application configurations. | <code>map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> |  | <code>&#123;&#125;</code> |
| [gemini_enterprise_gcs_bucket_name](variables.tf#L280) | The name of the GCS bucket to be used as the data source for the Discovery Engine Data Connector. | <code>string</code> |  | <code>&#34;your-bucket-name-placeholder&#34;</code> |
| [geolocation](variables.tf#L286) | Location for Discovery Engine resources (us, eu, or global). | <code>string</code> |  | <code>&#34;us&#34;</code> |
| [internal_lb_subnet_range](variables.tf#L292) | The IP CIDR range for the internal load balancer subnet. | <code>string</code> |  | <code>&#34;10.10.10.0&#47;24&#34;</code> |
| [kms_key_id](variables.tf#L298) | The full resource name of the Cloud KMS key to use for CMEK (e.g. projects/p/locations/l/keyRings/r/cryptoKeys/k). If not provided, a new key will be created. | <code>string</code> |  | <code>null</code> |
| [lenient_device_access_levels](variables.tf#L304) | List of Access Levels to include in the Lenient Device Policy. | <code>list&#40;string&#41;</code> |  | <code>&#91;&#93;</code> |
| [moderate_device_access_levels](variables.tf#L315) | List of Access Levels to include in the Moderate Device Policy. | <code>list&#40;string&#41;</code> |  | <code>&#91;&#93;</code> |
| [network_project_id](variables.tf#L321) | The Project ID where the Shared VPC resides (Host Project). Required if use_shared_vpc is true. | <code>string</code> |  | <code>&#34;&#34;</code> |
| [prefix](variables.tf#L327) | Prefix for naming resources in this blueprint. | <code>string</code> |  | <code>&#34;cnap&#34;</code> |
| [shared_vpc_network_name](variables.tf#L338) | The name of the existing Shared VPC network. Required if use_shared_vpc is true. | <code>string</code> |  | <code>&#34;&#34;</code> |
| [shared_vpc_proxy_subnet_name](variables.tf#L344) | The name of the existing proxy-only subnetwork to use. Required if use_shared_vpc is true. | <code>string</code> |  | <code>&#34;&#34;</code> |
| [shared_vpc_subnet_name](variables.tf#L350) | The name of the existing subnetwork to use. Required if use_shared_vpc is true. | <code>string</code> |  | <code>&#34;&#34;</code> |
| [terraform_state_bucket](variables.tf#L361) | The name of the Terraform state bucket. If not provided, it will be constructed from prefix and project ID. | <code>string</code> |  | <code>null</code> |
| [use_shared_vpc](variables.tf#L367) | Whether to use an existing Shared VPC instead of creating a new one. | <code>bool</code> |  | <code>false</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [access_policy_number](outputs.tf#L15) | The Access Policy number. |  |
| [acl_idp_type](outputs.tf#L20) | The Identity Provider type for Discovery Engine ACLs. Options: 'GSUITE', 'THIRD_PARTY'. |  |
| [acl_workforce_pool_name](outputs.tf#L25) | The resource name of the Workforce Identity Pool (required if acl_idp_type is 'THIRD_PARTY'). Format: locations/global/workforcePools/<pool_id>. |  |
| [acl_workforce_provider_id](outputs.tf#L30) | The ID of the Workforce Identity Pool Provider (required if acl_idp_type is 'THIRD_PARTY'). Format: <provider_id> (without acl_workforce_pool_name prefix). |  |
| [admin_group](outputs.tf#L35) | The principal for the Gemini Enterprise administrators group. |  |
| [analytics_dataset_id](outputs.tf#L40) | The BigQuery dataset ID for Gemini Analytics. |  |
| [analytics_repo_name](outputs.tf#L45) | The name of the Artifact Registry repository for Gemini Analytics. |  |
| [analytics_sa_email](outputs.tf#L50) | The email of the service account for Gemini Analytics. |  |
| [bq_data_stores](outputs.tf#L55) | A mapping of formatted data store keys to their configuration, ID, dataset, and table details. |  |
| [compliance_regime](outputs.tf#L65) | The compliance regime selected during deployment. |  |
| [deployment_type](outputs.tf#L70) | The deployment type of the load balancer (internal or external). |  |
| [dns_auth_records](outputs.tf#L75) | DNS Authorization resource records for Google-managed certificate. |  |
| [enable_chrome_enterprise_premium](outputs.tf#L80) | Whether Chrome Enterprise Premium (Zero Trust) is enabled. |  |
| [gcs_data_stores](outputs.tf#L85) | A mapping of formatted data store keys to their configuration, ID, and bucket details. |  |
| [gemini_apps_audit_logs](outputs.tf#L94) | A map of Engine IDs to their enable_audit_logs configuration. |  |
| [gemini_apps_model_armor](outputs.tf#L99) | A map of Engine IDs to their enable_model_armor configuration. |  |
| [gemini_apps_widget_ids](outputs.tf#L104) | A map of Widget Config IDs for each Gemini Enterprise app. |  |
| [gemini_enterprise_ip](outputs.tf#L109) | The reserved IP address for the load balancer. |  |
| [main_project_id](outputs.tf#L114) | The GCP Project name. |  |
| [model_armor_template_name](outputs.tf#L119) | The name of the Model Armor template resource. |  |
| [network_project_id](outputs.tf#L124) | The Host Project ID. |  |
| [prefix](outputs.tf#L129) | Prefix for naming resources. |  |
| [region](outputs.tf#L134) | GCP Region. |  |
| [shared_vpc_network_name](outputs.tf#L139) | The Shared VPC Network Name. |  |
| [shared_vpc_proxy_subnet_name](outputs.tf#L144) | The Shared VPC Proxy Subnet Name. |  |
| [shared_vpc_subnet_name](outputs.tf#L149) | The Shared VPC Subnet Name. |  |
| [tf_state_bucket_name](outputs.tf#L154) | The name of the GCS bucket used for Terraform state. |  |
| [use_shared_vpc](outputs.tf#L159) | Whether Shared VPC is used. |  |
| [user_groups](outputs.tf#L164) | The principals for the Gemini Enterprise users groups. |  |
<!-- END TFDOC -->
