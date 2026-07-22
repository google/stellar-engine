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

This blueprint bootstraps a minimal environment using the concepts for a Cloud Native Access Point and BeyondCorp. For more information about the CNAP, please see the [Department of Defense Cloud Native Access Point Reference Design](https://dodcio.defense.gov/Portals/0/Documents/Library/CNAP_RefDesign_v1.0.pdf).

## Description

This is an implementation of the CNAP Reference Design using the native Zero Trust functionality of Google Cloud.

This is by no means complete, and we expect to add more functionality to this blueprint as we build out our CNAP solution. For example, it currently only deploys demo apps to Cloud Run.

## Prerequisites

Before running `terraform apply` some setup is required in the environment

### 1. Gcloud Authentication Configuration

Make sure your gcloud cli is authenticated and configured for the correct project 
```
gcloud auth login
gcloud config set project <project-id>
gcloud auth application-default login
gcloud auth application-default set-quota-project <project-id>
```

### 2. Enable APIs

Before you can run `terraform apply`, you must enable some basic APIs. Run the following command:

```
for api in  "serviceusage" "compute" "accesscontextmanager" "cloudresourcemanager" "orgpolicy" "iap"; do  gcloud services enable $api.googleapis.com; done
```

We recommend waiting about 10 minutes for this change to propagate within the system.

### 3. Access Policies

Access policies are defined at the organization level, and there can only be one declared per organization. Each one can have multiple access levels within it. In order to correctly associate the access levels created in the blueprint with your organizations access policy, we need to populate that variable in the `.tfvars` file.

To list the access policies in your org, run the following command to find the name of the access policy associated with the org.
```
gcloud access-context-manager policies list --organization <org-id>
```

If this is a completely new org and you need to create an access policy, run the following command to create the policy and add the number returned after creation to the .tfvars file.
```
gcloud access-context-manager policies create --organization <org-id> --title CNAP-policy
```

### 4. Oauth2 Consent Screen

Configure an Oauth2 Consent screen for your project here https://console.cloud.google.com/apis/credentials/consent

It doesn't matter if it's external or internal, so do whatever meets your system requirements. Internal is better for testing.
For test setup, just use all the defaults and don't assign any extra scopes.

Once it's created, run the following command to look up the number and add the value to .tfvars
```
gcloud alpha iap oauth-brands list
```

### 5. Proxy Only Subnet
As a part of deploying the stellar-engine environment, a proxy only subnet will be created that can be used for the CNAP. Run the following command to be able to grab the subnet name, the name will follow the format `<env>-<region>-proxy-0`:
```
gcloud compute networks subnets list
```

### 6. Groups

The groups specified in the `cloud-run.yaml` and `compute-engine.yaml` files must be present in https://groups.google.com/ for your domain before running `terraform apply`.

To add a group, select “Create group” in the top left and enter the following information:
* Group name
* Group email (should match what is set in the yaml files)
* Set the privacy settings that you want
* Add any members to the group as needed
* Select “Create group”

Repeat as needed

## Configuration

There are two sources of configuration for this blueprint: The `cloudrun.yaml` file in the `data/` folder, as well as normal `.tfvars`. In the `.tfvars` file, there are parameters that define this deployment, such as organization information and domains. In the cloudrun.yaml, we define the Cloud Run applications that will be created, as well as the IAM configuration for how these will be protected behind the IAP.

In the `cloudrun.yaml` file, certain variables are templated in using the standard Terraform templating language, Jinja2.

| Variable in template | Value Source | Description |
|----|----|----|
| DOMAIN | var.domain, from the `.tfvars` file | The domain for the application, here used for templating out groups. Groups in the IAM policy must be valid at the time of apply | google_access_context_manager_access_policy.access-policy.id | This policy ID is required to form the name of the access levels for creating IAM rules, but the specific value is not known until the resource is created. |

## Deploying the Blueprint

Because deploying this blueprint may require updating your org policy to allow external load balancers, you must use a `-target` apply to make sure that change is made first, then the rest of the application will deploy.

Run the following command after configuring the cloudrun.yaml and terraform.tfvars files appropriately. This setting may take a few minutes to work after the terraform apply completes.
```
terraform apply -target google_org_policy_policy.allow_external_lb
```
Once the targeted terraform apply completes, run another terraform apply to apply the rest of the configuration.
```
terraform apply
```
Once the terraform apply completes, you will have the framework for CNAP deployed to your environment.


## DNS
# Self-signed Certificate
If you plan to use the self-signed certificate created from the blueprint, you will need to create a wildcard DNS entry for your domain pointing to the Regional Load Balancer front end. Depending on where you control DNS, the exact instructions will vary between providers. Work with whoever manages your DNS entries to make the appropriate changes once the load balancer is deployed.

# Google Managed Certificate
If you want to take advantage of a Google managed certificate, follow these steps to create one and attach it to the load balancer. As of the latest version of the blueprint, we do not create and attach a Google managed certificate.
* In GCP console, browse to Certificate Manager
* Click “Add Certificate”
* Enter a name for the certificate
* For location, select Regional, as the Google Load Balancer is a Regional Load Balancer
* Leave scope as default
* For Certificate type, select “Create Google-managed certificate”
* Enter any domain names that you want added to the certificate. It should at least include any urls already added to the Google Load Balancer
* It should default to DNS Authorization
* For each url, select “Create missing DNS Authorization”
* A side window will pop up. Select “Create DNS Authorization”
* Add the CNAME record information to your DNS provider
* Once each url and corresponding CNAME records have been added to the certificate and DNS, click Create
* It will take some time for the DNS records to propagate and activate the Google-managed certificate. You can view the status of the certificate by clicking the certificate name on the Certificate Manager page
* To then attach the certificate to the Google Load Balancer, you will need to run a command as the GCP Console GUI does not allow attaching Google-managed certificates.
* Run the following commands to attach the certificate to the Google Load Balancer. The first command will allow you to grab the name of the Google Load Balancer. The second command will allow you to update the Google Load Balancer with the Google-managed certificate.
```
gcloud compute target-https-proxies list
gcloud compute target-https-proxies update <google-load-balancer-name> --region=<region> --certificate-manager-certificates=<certificate-name>
```

<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [access_policy_number](variables.tf#L17) | There can only be one Access Policy per GCP Org. Use gcloud access-context-manager policies list --organization <org-number> to list it. | <code>number</code> | ✓ |  |
| [default_backend](variables.tf#L22) | The default backend for traffic at the load-balancer. Must match the key of one of the backends in the data/apps.yaml file. | <code>string</code> | ✓ |  |
| [domain](variables.tf#L27) | FQDN for the load-balancer hosted apps, where the subdomain will be prepended to. | <code>string</code> | ✓ |  |
| [env](variables.tf#L32) | The environment you are deploying the CNAP to (int, test, prod). | <code>string</code> | ✓ |  |
| [main_project_id](variables.tf#L55) | The GCP Project name. | <code>string</code> | ✓ |  |
| [network_name](variables.tf#L67) | Host network for IDS and GCE instance deployment. | <code>string</code> | ✓ |  |
| [network_project_id](variables.tf#L72) | The Landing Project ID. | <code>string</code> | ✓ |  |
| [oauth_brand_number](variables.tf#L77) | External Oauth2 consent screens can only be configured via the interactive console. After configuring it, use `gcloud alpha iap oauth-brands list` to lookup the brand id number. | <code>number</code> | ✓ |  |
| [region](variables.tf#L94) | GCP Region to deploy into. | <code>string</code> | ✓ |  |
| [subnetwork_name](variables.tf#L111) | Subnet for deploying the instances. | <code>string</code> | ✓ |  |
| [ids_name](variables.tf#L37) | Name of IDS. | <code>string</code> |  | <code>&#34;cnap-ids&#34;</code> |
| [ids_private_ip_prefix_length](variables.tf#L43) | The length of the IDS Private IP Prefix. | <code>number</code> |  | <code>24</code> |
| [machine_type](variables.tf#L49) | The type of machine to use. | <code>string</code> |  | <code>&#34;n2d-highcpu-2&#34;</code> |
| [net_project](variables.tf#L60) | GCP Project to the VPC belongs to. (Defaults to the variable project if not defined). | <code>string</code> |  | <code>null</code> |
| [packet_mirroring_policy_name](variables.tf#L82) | Name of packet mirror policy. | <code>string</code> |  | <code>&#34;cnap-packet-mirror&#34;</code> |
| [prefix](variables.tf#L88) | Prefix for naming resources in this blueprint. | <code>string</code> |  | <code>&#34;cnap&#34;</code> |
| [severity](variables.tf#L99) | Display name of the service account to create. | <code>string</code> |  | <code>&#34;MEDIUM&#34;</code> |
| [subnetwork_list](variables.tf#L105) | Subnet list to monitor with Cloud IDS. | <code>list&#40;any&#41;</code> |  | <code>null</code> |
<!-- END TFDOC -->
