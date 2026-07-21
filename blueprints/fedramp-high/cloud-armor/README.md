# Google Cloud Armor

<!-- BEGIN TOC -->
- [Introduction to Google Cloud Armor](#introduction-to-google-cloud-armor)
- [Cloud Armor Blueprint](#cloud-armor-blueprint)
- [Disclaimer](#disclaimer)
- [Deployment Steps](#deployment-steps)
- [Verification of a successful deployment](#verification-of-a-successful-deployment)
- [Troubleshooting](#troubleshooting)
- [Variables](#variables)
- [Outputs](#outputs)
<!-- END TOC -->

## Introduction to Google Cloud Armor
Google Cloud Armor helps you protect your Google Cloud deployments from multiple types of threats, including distributed denial-of-service (DDoS) attacks and application attacks like cross-site scripting (XSS) and SQL injection (SQLi). Google Cloud Armor features some automatic protections and some that you need to configure manually.

## Cloud Armor Blueprint
This blueprint demonstrates how to use Google Cloud Armor to create policies and rules that can be applied to backend services. Enforced at the HTTP(S) Load Balancer's edge locations, Google Cloud Armor protects from traffic at the root. The framework of the application is by defining security policies with specific rules, using them to monitor against incoming traffic. There are 4 possible actions allow, deny, redirect or throttle, this provides a level of security before the request attributes reach the application instances. 

## Disclaimer
- The present GCP Terraform Module in this project is set up and intended to be implemented in a FEDRAMP High environment using the Assured Workloads within the Google Cloud Platform (GCP) organization.

## Deployment Steps

You should see this README, some terraform files, and a .yaml file in the directory.
1. Copy the contents of the terraform.tfvars.sample file into your own terraform.tfvars file, then update the variables in this file. For reference update the following variables:

- ```project_id```  with your GCP Project ID <br />
- ```region``` with the GCP Location <br />
- ```rules_file``` with the path to the rules.yaml file <br />

2. The rules file is called "rules.yaml" by default. If you would like to change its name or location, the rules_file variable in "terraform.tfvars" must reflect those changes.
3. Change the values in "rules.yaml" to create policies and attach rules to them. This file has examples of acceptable values.
4. The usual terraform commands will be used to deploy the policies. To provision this example, run the following from within this directory:

```terraform init ```<br />
```terraform plan``` to see the infrastructure plan<br />
```terraform apply``` to apply the infrastructure build<br />
```terraform destroy``` only if you wish to destroy the built infrastructure<br />

## Verification of a successful deployment
All of the policies will be created and available through the Cloud Console. They will be located under Network Security in the Cloud Armor policies tab (or you can just search "cloud armor" in the console). Upon clicking on each policy, you should see each associated rule that has been assigned to the policy. From here you can apply each of these policies to existing resources, or apply them to new resources when they are created.

To apply these policies to existing resources:

1. Click on the policy name to see the Policy Details page.
2. Click on the Targets tab to see which targets the policy is applied to.
3. Click "Apply Policy to New Target" to add this policy to targets of your choosing.

## Troubleshooting
Many of the options in the rules variable have requirements that must be followed.
A few examples are:
- If you specify the action as "rate_based_ban" or "throttle", you must create a rate_limit_options block.
- When choosing the interval time in "rate_limit_threshold", you can only select 10, 30, 60, 120, 180, 240, 300, 600, 900, 1200, 1800, 2700, or 3600 seconds.
- When selecting "deny(STATUS)" for the "action", STATUS must be 403, 404, or 502.
<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [main_project_id](variables.tf#L1) | Main project ID for Cloud Armor policies. | <code>string</code> | ✓ |  |
| [region](variables.tf#L6) | Google Cloud Region. | <code>string</code> |  | <code>&#34;us-east4&#34;</code> |
| [rules_file](variables.tf#L12) | Path to the YAML file containing the rules. | <code>string</code> |  | <code>&#34;rules.yaml&#34;</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [policies](outputs.tf#L1) | All created policy resources. |  |
| [policy_names](outputs.tf#L6) | All created policy names. |  |
| [policy_rules](outputs.tf#L13) | All created policy rule resources. |  |
<!-- END TFDOC -->
