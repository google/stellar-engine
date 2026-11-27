# Cloud Native Access Point

This blueprint bootstraps a minimal environment using the concepts for a Cloud Native Access Point and BeyondCorp. For more information about the CNAP, please see the [Department of Defence Cloud Native Access Point Reference Design](https://dodcio.defense.gov/Portals/0/Documents/Library/CNAP_RefDesign_v1.0.pdf).

## Description

This blueprint implements the CNAP Reference Design using native Google Cloud Zero Trust capabilities (Identity-Aware Proxy, Access Context Manager access levels, Cloud Armor regional WAF, and Cloud IDS) across Cloud Run and confidential Compute Engine backends protected by CMEK.

## Prerequisites

Before running `terraform apply`, complete the following setup in the target environment.

### 1. Gcloud Authentication Configuration

Ensure the gcloud CLI is authenticated and configured for the target project: `gcloud auth login`, `gcloud config set project <project-id>`, `gcloud auth application-default login`, and `gcloud auth application-default set-quota-project <project-id>`.

### 2. Enable APIs

Enable baseline APIs in the deployment project before applying:

`for api in "serviceusage" "compute" "accesscontextmanager" "cloudresourcemanager" "cloudkms" "orgpolicy" "iap"; do gcloud services enable $api.googleapis.com; done`

Allow several minutes for API enablement to propagate before deploying resources.

### 3. Access Policies

Access policies are defined at the organization level, and only one policy can exist per organization. Set `access_policy_number` in `.tfvars` so the additive `google_access_context_manager_access_level` resources attach to that organization policy without overwriting existing Stage 0 or organization-wide access levels.

List the organization's access policy with `gcloud access-context-manager policies list --organization <org-id>` and copy its numeric `NAME` value.

If the organization does not yet have an access policy, create one with `gcloud access-context-manager policies create --organization <org-id> --title CNAP-policy` and set `access_policy_number` to the returned numeric policy ID.

### 4. OAuth2 Consent Screen

IAP uses a Google-managed OAuth client by default, so the blueprint needs no OAuth configuration for users in the same organization.

- To admit users outside the organization, configure the OAuth consent screen at https://console.cloud.google.com/apis/credentials/consent and create an OAuth client in the console.
- Pass that client to the blueprint through the `iap_oauth2_client` variable, with its `id` and `secret` attributes.
- Terraform can no longer create OAuth brands or clients, because Google shut down the IAP OAuth Admin API that the `google_iap_brand` and `google_iap_client` resources used.

### 5. Proxy Only Subnet

The VPC network must contain a regional `REGIONAL_MANAGED_PROXY` subnet for the Regional External Application Load Balancer. Stage 2 networking (`2-networking-a-fedramp` and `2-networking-b-il5-ngfw`) creates `proxy-<us-region>` automatically, which this blueprint resolves by default (or via `proxy_subnetwork_name`).

If deploying onto a custom VPC without an existing regional proxy subnet, create one first:
```
gcloud compute networks subnets create proxy-<us-region> \
    --purpose=REGIONAL_MANAGED_PROXY \
    --role=ACTIVE \
    --region=<us-region> \
    --network=<vpc-network> \
    --range=10.40.2.0/24
```
Adjust the CIDR range so it does not overlap any existing subnet ranges allocated in the VPC.

### 6. Stage 2 Shared VPC and Private Service Access

Stage 2 networking pre-configures the Shared VPC host project (`enable_shared_vpc_host = false`) and Private Service Access (`create_service_networking_connection = false`). Leave both variables at their `false` defaults when deploying into a Stage 2 spoke such as `prod-spoke-0` in `xxxx-prod-net-host`, or set them to `true` only for standalone test VPCs that lack Shared VPC registration or Private Service Access peering.

### 7. DNS

Create a wildcard DNS record for `domain` pointing to the Regional External Load Balancer frontend IP once deployed.

### 8. Groups

Create the Google Groups referenced in `data/cloudrun.yaml` and `data/compute-engine.yaml` before running `terraform apply`.


## Configuration

Application backends are configured through `data/cloudrun.yaml`, `data/compute-engine.yaml`, and `.tfvars` inputs. The blueprint grants the IAP service agent `roles/run.invoker` per Cloud Run service (rather than project-wide) so IAP can invoke only the applications behind the load balancer. Both Cloud Run services and Compute Engine disks encrypt data with the CMEK key created by `module.kms`.

Terraform `templatefile` injects the following variables into `data/cloudrun.yaml` and `data/compute-engine.yaml`:

| Variable in template | Value Source | Description |
|---|---|---|
| `DOMAIN` | `var.domain` from `.tfvars` | Domain used to template group principals in IAP IAM bindings; groups must exist before apply. |
| `ACCESSPOLICY` | `var.access_policy_number` from `.tfvars` | Organization Access Policy number used to build access level names in IAP CEL conditions. |

## Deploying the Blueprint

Allow external managed load balancers in `main_project_id` first so the Org Policy propagates before creating the regional external ALB:

`terraform apply -target google_org_policy_policy.allow_external_lb`

Wait a few minutes for Org Policy propagation, then run `terraform apply`.

When upgrading from an earlier release that managed the authoritative `google_access_context_manager_access_levels.access_levels` resource, remove that plural resource from Terraform state (`terraform state rm google_access_context_manager_access_levels.access_levels`) and import or manage the individual `google_access_context_manager_access_level` resources before applying so Terraform does not delete existing organization access levels.
<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [access_policy_number](variables.tf#L23) | There can only be one Access Policy per GCP Org. Use gcloud access-context-manager policies list --organization <org-number> to list it. | <code>number</code> | ✓ |  |
| [default_backend](variables.tf#L44) | The default backend for traffic at the load-balancer. Must match the key of one of the backends in the data/apps.yaml file. | <code>string</code> | ✓ |  |
| [domain](variables.tf#L49) | FQDN for the load-balancer hosted apps, where the subdomain will be prepended to. | <code>string</code> | ✓ |  |
| [main_project_id](variables.tf#L88) | The GCP Project name. | <code>string</code> | ✓ |  |
| [network_name](variables.tf#L100) | Host network for IDS and GCE instance deployment. | <code>string</code> | ✓ |  |
| [network_project_id](variables.tf#L105) | The Landing Project ID. | <code>string</code> | ✓ |  |
| [region](variables.tf#L128) | GCP Region to deploy into. | <code>string</code> | ✓ |  |
| [access_expiry_timestamp](variables.tf#L17) | Optional RFC3339 timestamp to create an expiring access level. Omitted when null. | <code>string</code> |  | <code>null</code> |
| [cloud_armor_request_body_limit](variables.tf#L28) | Maximum request body size, based on the Content-Length header, allowed through the Cloud Armor policy. Regional policies only inspect the first 8KB of the body with preconfigured WAF rules, so larger requests are denied to prevent WAF bypass via oversized payloads. Set to null to disable. | <code>string</code> |  | <code>&#34;8KB&#34;</code> |
| [create_service_networking_connection](variables.tf#L38) | Whether to create a new Service Networking private IP allocation and VPC peering connection for Cloud IDS. Leave false when reusing the Private Service Access allocation from Stage 2. | <code>bool</code> |  | <code>false</code> |
| [enable_shared_vpc_host](variables.tf#L54) | Whether to register network_project_id as a Shared VPC host project. Leave false when Stage 2 already configures the Shared VPC host project. | <code>bool</code> |  | <code>false</code> |
| [iap_oauth2_client](variables.tf#L60) | Optional custom OAuth client for IAP, created in the console. IAP uses a Google-managed OAuth client when this is null, which only admits users of the same organization. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>null</code> |
| [ids_name](variables.tf#L70) | Name of IDS. | <code>string</code> |  | <code>&#34;cnap-ids&#34;</code> |
| [ids_private_ip_prefix_length](variables.tf#L76) | The length of the IDS Private IP Prefix. | <code>number</code> |  | <code>24</code> |
| [machine_type](variables.tf#L82) | The type of machine to use. | <code>string</code> |  | <code>&#34;n2d-highcpu-2&#34;</code> |
| [net_project](variables.tf#L93) | Optional host project ID owning the VPC network and subnets. Defaults to network_project_id when null. | <code>string</code> |  | <code>null</code> |
| [packet_mirroring_policy_name](variables.tf#L110) | Name of packet mirror policy. | <code>string</code> |  | <code>&#34;cnap-packet-mirror&#34;</code> |
| [prefix](variables.tf#L116) | Prefix for naming resources in this blueprint. | <code>string</code> |  | <code>&#34;cnap&#34;</code> |
| [proxy_subnetwork_name](variables.tf#L122) | Optional name of the regional managed proxy subnetwork in the VPC host project. Defaults to proxy-<region> when null. | <code>string</code> |  | <code>null</code> |
| [severity](variables.tf#L133) | Minimum threat severity to report in Cloud IDS (INFORMATIONAL, LOW, MEDIUM, HIGH, or CRITICAL). | <code>string</code> |  | <code>&#34;MEDIUM&#34;</code> |
| [subnetwork_list](variables.tf#L139) | Subnet list to monitor with Cloud IDS. | <code>list&#40;any&#41;</code> |  | <code>null</code> |
| [subnetwork_name](variables.tf#L145) | Subnet for deploying the instances. | <code>string</code> |  | <code>&#34;prod-tenant-1-subnet&#34;</code> |
<!-- END TFDOC -->
