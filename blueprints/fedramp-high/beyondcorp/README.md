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

## Introduction to BeyondCorp
BeyondCorp is Google Cloud's zero-trust network security framework, enabling secure access to applications and resources without relying on traditional VPNs.

# BeyondCorp Blueprint
This blueprint simplifies the deployment and configuration of BeyondCorp resources in your cloud environment. This blueprint creates 4 different resources:

<mark>Required APIs:</mark> Enables the required APIs in the specified GCP project.<br />
- accesscontextmanager.googleapis.com: Manages Access Context Manager resources.<br />
- cloudresourcemanager.googleapis.com: Manages GCP resources like projects and IAM policies.<br />
- iap.googleapis.com: Enables Identity-Aware Proxy (IAP) functionality.<br />

<mark>Access Level for Device Endpoint Verification:</mark> Enforces device-based security policies. Endpoint verification enforces devices to access resources, ensuring only secure devices are allowed.<br />
<mark>Identity-Aware Proxy (IAP) backend:</mark> Configures a Compute Backend Service with IAP enabled (with OAuth2 credentials for authentication).<br />
<mark>Identity-Aware Proxy (IAP) user:</mark> Grants the specified user access to IAP-secured resources. <span style="color: grey">Roles/iap.httpsResourceAccessor:</span> Allows users to access HTTPS resources protected by IAP.<br/>

For more information, please look at this Google Cloud Communiity [Article](https://www.googlecloudcommunity.com/gc/Community-Blogs/Improve-the-security-of-your-Google-Workspace-Environment/ba-p/714629).


## Disclaimer
- The present GCP Terraform Module in this project is set up and intended to be implemented in a FEDRAMP High environment using the Assured Workdloads within the Google Cloud Platform (GCP) organization.

### Oauth2 Consent Screen

At the Org-level, configure an Oauth2 Consent screen for your project here https://console.cloud.google.com/apis/credentials/consent

It doesn't matter if it's external or internal, so do whatever meets your system requirements. Internal is better for testing.
For test setup, just use all the defaults and don't assign any extra scopes.


Once it's created, create credentials by going to the API&Services -> Credentials. Click on Create Credentials and use "Web Application" as an application type. Once Credentials are created, save the oauth_client_id and oauth_client_secret into your terraform.tfvars.

### Access Policy ID number

To get Access Policy ID number, run the following commmand:

gcloud access-context-manager policies list

The name is the ID.
## Sucessful Deployment

Use GCP Console to verify if resources were created

<mark>To check endpoint:</mark> Go to Access Context Manager (NOTE: This is created at the ORG level)<br/>
<mark>To check IAP backend:</mark> Go to Network Services -> Load balancer -> Backends<br/>
<mark>To check if IAP is attached to user:</mark> Go to IAMs and search for User. See if IAP-secured Web App User is listed<br/>
<mark>To check if iap.googleapis.com, cloudresourcemanager.googleapis.com and accesscontextmanager.googleapis.com is attached to project:</mark> Go to IAM and search for project. See if those roles are listed.<br/>
<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [endpoint_name](variables.tf#L1) | Name for endpoint. | <code>string</code> | ✓ |  |
| [iap_user_email](variables.tf#L6) | User or group email for IAP access. | <code>string</code> | ✓ |  |
| [main_project_id](variables.tf#L11) | GCP Project ID. | <code>string</code> | ✓ |  |
| [oauth_client_id](variables.tf#L16) | OAuth Client ID for IAP. | <code>string</code> | ✓ |  |
| [oauth_client_secret](variables.tf#L21) | OAuth Client Secret for IAP. | <code>string</code> | ✓ |  |
| [organization_id](variables.tf#L26) | GCP Organization ID. | <code>string</code> | ✓ |  |
| [policy_title](variables.tf#L31) | Title for the Access Context Manager Policy. | <code>string</code> | ✓ |  |
| [region](variables.tf#L36) | Region for deployment. | <code>string</code> | ✓ |  |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [endpoint_name](outputs.tf#L1) | Name of the endpoint that was created. |  |
<!-- END TFDOC -->
