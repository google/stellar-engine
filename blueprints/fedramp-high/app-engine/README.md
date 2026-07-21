# App Engine

<!-- BEGIN TOC -->
- [Introduction to App Engine](#introduction-to-app-engine)
- [App Engine Blueprint](#app-engine-blueprint)
- [Disclaimer](#disclaimer)
- [Deployment Steps](#deployment-steps)
- [Verification of a successful deployment](#verification-of-a-successful-deployment)
- [Variables](#variables)
- [Outputs](#outputs)
<!-- END TOC -->

## Introduction to App Engine
App Engine is a platform-as-a-service (PaaS) application to develop and host serverless web applications in Google Cloud. It has various built in libraries, framework and languages that provide resource to building the application. With real time analysis on demand, will take care of provisioning services and app scaling. 

## App Engine Blueprint
This blueprint demonstrates how to deploy App Engine to begin building an application on Google Cloud Platform (GCP). It provides a baseline with built in features ranging from security to handling web requests. After deployment, based on complexity of the application, services will be created as the overarching grouping for the version(s) of the application code. 

App engine will create instance classes inside of the services where requests will be processed. Each of the different instances will have varying levels of resources to fit the requirement of the application. As the app grows, the instances automatically scale to accommodate for fluctuating traffic and update configurations of each service. 

## Disclaimer
App Engine applications cannot be deleted once they're created; you have to delete the entire project to delete the application. Terraform will report the application has been successfully deleted; this is a limitation of Terraform, and will go away in the future. Terraform is not able to delete App Engine applications. https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/app_engine_application

## Deployment Steps
You should see this README and some terraform files.
1. Run cp terraform.tfvars.sample terraform.tfvars to copy the sample variables to your own tfvars file.

2. Update the variables as necessary in your tfvars file.
3. The usual terraform commands will do the work. To provision this example, run the following from within this directory:

```terraform init ```<br />
```terraform plan``` to see the infrastructure plan<br />
```terraform apply``` to apply the infrastructure build<br />
```terraform destroy``` to destroy the built infrastructure<br />

## Verification of a successful deployment
Use the GCP console to verify if the resources have been created. 

```To verify the creation of Instance classes: Go to Instances in your landing project``` <br />
<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [main_project_id](variables.tf#L1) | Main project ID. | <code>string</code> | ✓ |  |
| [region](variables.tf#L6) | Google Cloud Region. | <code>string</code> |  | <code>&#34;us-east4&#34;</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [app_id](outputs.tf#L1) | Identifier of the app. |  |
| [code_bucket](outputs.tf#L6) | GCS bucket where the app code is stored. |  |
| [default_bucket](outputs.tf#L11) | GCS bucket where the app content is stored. |  |
| [default_hostname](outputs.tf#L16) | Default hostname for the app. |  |
| [gcr_domain](outputs.tf#L21) | GCR domain used for storing managed Docker images. |  |
| [id](outputs.tf#L26) | An identifier for the resource. |  |
| [name](outputs.tf#L31) | Unique name of the app. |  |
<!-- END TFDOC -->
