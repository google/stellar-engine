# App Engine blueprint

<!-- BEGIN TOC -->
- [1 App Engine overview](#1-app-engine-overview)
- [2 Blueprint scope](#2-blueprint-scope)
- [3 Deletion behavior](#3-deletion-behavior)
- [4 Deployment steps](#4-deployment-steps)
- [5 Deployment verification](#5-deployment-verification)
- [6 Deployer permissions](#6-deployer-permissions)
  - [Service account impersonation](#service-account-impersonation)
- [Variables](#variables)
- [Outputs](#outputs)
<!-- END TOC -->

## 1 App Engine overview

App Engine is a managed serverless platform for hosting web applications and APIs on Google Cloud with built-in runtime libraries, automatic instance scaling, and versioned service routing.

## 2 Blueprint scope

This blueprint initializes a regional App Engine application inside `main_project_id` so application teams can deploy versioned services with managed instance classes that scale automatically with request traffic.

## 3 Deletion behavior

Google Cloud does not support deleting an App Engine application without deleting its parent project. Running `terraform destroy` removes the resource from Terraform state without deleting the underlying App Engine application, as documented in the [`google_app_engine_application` provider reference](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/app_engine_application).

## 4 Deployment steps

1. Run `cp terraform.tfvars.sample terraform.tfvars` to create your local variable file.
2. Set `main_project_id` and `region` in `terraform.tfvars`.
3. Initialize and apply the Terraform configuration from this directory:

```bash
terraform init
terraform plan
terraform apply
```

## 5 Deployment verification

Open App Engine in the Google Cloud console for `main_project_id` and inspect the Dashboard and Instances views to confirm the application is initialized in the configured `region`.

## 6 Deployer permissions

Grant the deploying service account or user identity the following IAM roles on the workload project (`main_project_id`):

- `roles/appengine.appCreator` or `roles/appengine.appAdmin`
- `roles/serviceusage.serviceUsageAdmin`

### Service account impersonation

When deploying via service account impersonation, configure `user_project_override = true` and set `billing_project` to the workload project on both the `google` and `google-beta` providers so quota and API enablement checks evaluate against `main_project_id` rather than the automation service account project:

```hcl
provider "google" {
  project                     = "<workload-project-id>"
  region                      = "<region>"
  impersonate_service_account = "<deployer-sa>@<iac-project-id>.iam.gserviceaccount.com"
  user_project_override       = true
  billing_project             = "<workload-project-id>"
}

provider "google-beta" {
  project                     = "<workload-project-id>"
  region                      = "<region>"
  impersonate_service_account = "<deployer-sa>@<iac-project-id>.iam.gserviceaccount.com"
  user_project_override       = true
  billing_project             = "<workload-project-id>"
}
```

<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [main_project_id](variables.tf#L15) | Main project ID. | <code>string</code> | ✓ |  |
| [region](variables.tf#L20) | Google Cloud Region. | <code>string</code> |  | <code>&#34;us-east4&#34;</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [app_id](outputs.tf#L15) | Identifier of the app. |  |
| [code_bucket](outputs.tf#L20) | GCS bucket where the app code is stored. |  |
| [default_bucket](outputs.tf#L25) | GCS bucket where the app content is stored. |  |
| [default_hostname](outputs.tf#L30) | Default hostname for the app. |  |
| [gcr_domain](outputs.tf#L35) | GCR domain used for storing managed Docker images. |  |
| [id](outputs.tf#L40) | An identifier for the resource. |  |
| [name](outputs.tf#L45) | Unique name of the app. |  |
<!-- END TFDOC -->
