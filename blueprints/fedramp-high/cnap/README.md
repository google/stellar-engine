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

# Cloud Native Access Point

This blueprint bootstraps a minimal environment using the concepts for a Cloud Native Access Point and BeyondCorp. For more information about the CNAP, please see the [Department of Defence Cloud Native Access Point Reference Design](https://dodcio.defense.gov/Portals/0/Documents/Library/CNAP_RefDesign_v1.0.pdf).

## Description

This is an implementation of the CNAP Reference Design using the native Zero Trust functionality of Google Cloud.

This is by no means complete, and we expect to add more functionality to this blueprint as we build out our CNAP solution. For example, it currently only deploys demo apps to Cloud Run. It is intended to

Features to be developed:
- [ ] Cloud Armor WAF policies
- [ ] Cloud IDS

## Prerequisites

Before running `terraform apply` some setup is required in the environment

### 1. Gcloud Authentication Configuration

Make sure your gcloud cli is authenticated and configured for the correct project `gcloud auth login`, `gcloud config set project <project-id>`, `gcloud auth application-default login`, and `gcloud auth application-default set-quota-project <project-id>`

### 2. Enable APIs

Before you can run `terraform apply`, you must enable some basic APIs.


Run `for api in  "serviceusage" "compute" "accesscontextmanager" "cloudresourcemanager" "orgpolicy" "iap"; do  gcloud services enable $api.googleapis.com; done`

We recommend waiting about 10 minutes for this change to propogate within the system.

### 3. Access Policies

Access policies are defined at the organization level, and there can only be one declared per organization. Each one can have multiple access levels within it. In order to correctly associate the access levels created in the blueprint with your organizions access policy, we need to populate that variable in the `.tfvars` file.

To list the access policies in your org, run `gcloud access-context-manager policies list --organization <org-id>` and find the `NAME:` of the access policy associated with the org.

If this is a completely new org and you need to create an access policy, you may use `gcloud access-context-manager policies create --organization <org-id> --title CNAP-policy`, and use the number returned after creation.

### 4. Oauth2 Consent Screen

Configure an Oauth2 Consent screen for your project here https://console.cloud.google.com/apis/credentials/consent

It doesn't matter if it's external or internal, so do whatever meets your system requirements. Internal is better for testing.
For test setup, just use all the defaults and don't assign any extra scopes.

Once it's created, run `gcloud alpha iap oauth-brands list` to look up the number and add the value to `.tfvars`

### 5. Proxy Only Subnet

Your VPC network must have a dedicated "Proxy Only" subnet configured for "Regional Managed Proxy".
Your VPC may already have a dedicated "Proxy Only" subnet in your region, but if it does not you will need to deploy one.

The command to create a new "Proxy Only" subnet is as follows:
```
gcloud compute networks subnets create vpc-proxies \
    --purpose=REGIONAL_MANAGED_PROXY \
    --role=ACTIVE \
    --region=<us-region> \
    --network=<vpc-network> \
    --range=10.40.2.0/24
```
Note: You will need to adjust the subnet range to be outside of any other allocated ranges within the VPC. If the subnet range listed above does not work, you will need to find a usable /24 range, which is outside the scope of this guide.

### 6. DNS

To make this blueprint work, you will need to create a wildcard DNS entry for your domain pointing to your Regional Load Balancer front-end. Oftentimes the DNS control will be outside of the project, and exact instructions very between providers. Work with whoever manages your DNS entries to make the appropriate changes once the load balancer is deployed.

### 7. Groups

The groups specified in the `cloud-run.yaml` and `compute-engine.yaml` files must be present in https://groups.google.com/ for your domain before running `terraform apply`.


## Configuration

There are two sources of configuration for this blueprint: The `cloudrun.yaml` file in the `data/` folder, as well as normal `.tfvars`. In the `.tfvars` file, there are parameters that define this deployment, such as organization information and domains. In the cloudrun.yaml, we define the Cloud Run applications that will be created, as well as the IAM configuration for how these will be protected behind the IAP.

In the `cloudrun.yaml` file, certain variables are templated in using the standard Terraform templating language, Jinja2.

| Variable in template | Value Source | Description |
|----|----|----|
| DOMAIN | var.domain, from the `.tfvars` file | The domain for the application, here used for templating out groups. Groups in the IAM policy must be valid at the time of apply | google_access_context_manager_access_policy.access-policy.id | This policy ID is required to form the name of the access levels for creating IAM rules, but the specific value is not known until the resource is created. |
## Deploying the Blueprint

Because deploying this blueprint may require updating your org policy to allow external load balancers, you must use a `-target` apply to make sure that change is made first, then the rest of the application will deploy.

Run `terraform apply -target google_org_policy_policy.allow_external_lb` after configuring the `cloudrun.yaml` and `terraform.tfvars` files appropriately. This setting may take a few minutes to work after the `terraform apply` completes.
<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [access_policy_number](variables.tf#L17) | There can only be one Access Policy per GCP Org. Use gcloud access-context-manager policies list --organization <org-number> to list it. | <code>number</code> | ✓ |  |
| [default_backend](variables.tf#L22) | The default backend for traffic at the load-balancer. Must match the key of one of the backends in the data/apps.yaml file. | <code>string</code> | ✓ |  |
| [domain](variables.tf#L27) | FQDN for the load-balancer hosted apps, where the subdomain will be prepended to. | <code>string</code> | ✓ |  |
| [main_project_id](variables.tf#L50) | The GCP Project name. | <code>string</code> | ✓ |  |
| [network_name](variables.tf#L62) | Host network for IDS and GCE instance deployment. | <code>string</code> | ✓ |  |
| [network_project_id](variables.tf#L67) | The Landing Project ID. | <code>string</code> | ✓ |  |
| [oauth_brand_number](variables.tf#L72) | External Oauth2 consent screens can only be configured via the interactive console. After configuring it, use `gcloud alpha iap oauth-brands list` to lookup the brand id number. | <code>number</code> | ✓ |  |
| [region](variables.tf#L89) | GCP Region to deploy into. | <code>string</code> | ✓ |  |
| [ids_name](variables.tf#L32) | Name of IDS. | <code>string</code> |  | <code>&#34;cnap-ids&#34;</code> |
| [ids_private_ip_prefix_length](variables.tf#L38) | The length of the IDS Private IP Prefix. | <code>number</code> |  | <code>24</code> |
| [machine_type](variables.tf#L44) | The type of machine to use. | <code>string</code> |  | <code>&#34;n2d-highcpu-2&#34;</code> |
| [net_project](variables.tf#L55) | GCP Project to the VPC belongs to. (Defaults to the variable project if not defined). | <code>string</code> |  | <code>null</code> |
| [packet_mirroring_policy_name](variables.tf#L77) | Name of packet mirror policy. | <code>string</code> |  | <code>&#34;cnap-packet-mirror&#34;</code> |
| [prefix](variables.tf#L83) | Prefix for naming resources in this blueprint. | <code>string</code> |  | <code>&#34;cnap&#34;</code> |
| [severity](variables.tf#L94) | Display name of the service account to create. | <code>string</code> |  | <code>&#34;MEDIUM&#34;</code> |
| [subnetwork_list](variables.tf#L100) | Subnet list to monitor with Cloud IDS. | <code>list&#40;any&#41;</code> |  | <code>null</code> |
| [subnetwork_name](variables.tf#L106) | Subnet for deploying the instances. | <code>string</code> |  | <code>&#34;default-us-east4&#34;</code> |
<!-- END TFDOC -->
