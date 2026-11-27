# BeyondCorp blueprint

<!-- BEGIN TOC -->
- [Introduction to BeyondCorp](#introduction-to-beyondcorp)
- [BeyondCorp blueprint](#beyondcorp-blueprint)
- [Disclaimer](#disclaimer)
- [OAuth2 consent screen](#oauth2-consent-screen)
- [Access Policy ID number](#access-policy-id-number)
- [Deployment steps](#deployment-steps)
- [Successful deployment verification](#successful-deployment-verification)
- [Variables](#variables)
- [Outputs](#outputs)
<!-- END TOC -->

## Introduction to BeyondCorp
BeyondCorp is Google Cloud's zero-trust network security framework, enabling secure access to applications and resources without relying on traditional VPNs.

## BeyondCorp blueprint
This blueprint simplifies the deployment and configuration of BeyondCorp resources in your cloud environment. It enables required project APIs and creates Access Context Manager and IAP resources:

- Required APIs enabled in the specified GCP project include `accesscontextmanager.googleapis.com`, `cloudresourcemanager.googleapis.com`, `compute.googleapis.com`, and `iap.googleapis.com`.
- An access level for device endpoint verification enforces device-based security policies so only encrypted devices with screen lock enabled are allowed.
- An Identity-Aware Proxy (IAP) backend service configures a Compute Engine backend service with IAP enabled using your OAuth2 credentials.
- An IAP IAM binding grants `roles/iap.httpsResourceAccessor` to `iap_user_email` conditioned on the endpoint verification access level.

For more information, read the Google Cloud Community [article on securing Google Workspace environments](https://www.googlecloudcommunity.com/gc/Community-Blogs/Improve-the-security-of-your-Google-Workspace-Environment/ba-p/714629).

## Disclaimer
- This blueprint is configured for FedRAMP High environments using Assured Workloads within a Google Cloud organization.

## OAuth2 consent screen

At the organization level, configure an OAuth2 consent screen for your project at `https://console.cloud.google.com/apis/credentials/consent`.

Use Internal if only members of your Google Cloud organization access the application, or External if required by your architecture. For test setup, keep the defaults and do not assign extra scopes.

Once the consent screen is created, go to APIs and Services > Credentials, select Create Credentials, choose OAuth client ID with Web Application as the application type, and save `oauth_client_id` and `oauth_client_secret` in `terraform.tfvars`.

## Access Policy ID number

To get the Access Policy ID number, run the following command:

```bash
gcloud access-context-manager policies list --organization=<ORGANIZATION_ID>
```

The numeric resource name returned by the command is the Access Policy ID.

## Deployment steps

1. Copy the sample variables file to `terraform.tfvars` and populate your organization ID, project ID, OAuth2 client credentials, IAP user or group email, and `endpoint_name`:

```bash
cp terraform.tfvars.sample terraform.tfvars
```

2. Initialize, preview, and apply the Terraform configuration from this directory:

```bash
terraform init
terraform plan
terraform apply
```

Run `terraform destroy` when you need to tear down the deployed resources.

## Successful deployment verification

Use the Google Cloud console to verify the deployed resources:

- Open Access Context Manager at the organization level to confirm the endpoint verification access level exists.
- Open Network Services > Load balancing > Backends to confirm `iap-backend-service` has IAP enabled.
- Open IAM and Admin > IAM for the project and search for the configured user or group to confirm `IAP-secured Web App User` is bound with the `endpoint_verified` condition.
- Open APIs and Services > Enabled APIs and services for `main_project_id` to confirm `accesscontextmanager.googleapis.com`, `cloudresourcemanager.googleapis.com`, `compute.googleapis.com`, and `iap.googleapis.com` are enabled.
<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [endpoint_name](variables.tf#L15) | Name for endpoint. | <code>string</code> | ✓ |  |
| [iap_user_email](variables.tf#L20) | User or group email for IAP access. | <code>string</code> | ✓ |  |
| [main_project_id](variables.tf#L25) | GCP Project ID. | <code>string</code> | ✓ |  |
| [oauth_client_id](variables.tf#L30) | OAuth Client ID for IAP. | <code>string</code> | ✓ |  |
| [oauth_client_secret](variables.tf#L35) | OAuth Client Secret for IAP. | <code>string</code> | ✓ |  |
| [organization_id](variables.tf#L41) | GCP Organization ID. | <code>string</code> | ✓ |  |
| [policy_title](variables.tf#L46) | Title for the Access Context Manager Policy. | <code>string</code> | ✓ |  |
| [region](variables.tf#L51) | Region for deployment. | <code>string</code> | ✓ |  |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [endpoint_name](outputs.tf#L15) | Name of the endpoint that was created. |  |
<!-- END TFDOC -->
