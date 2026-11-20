# Datastore blueprint

<!-- BEGIN TOC -->
- [1 Datastore overview](#1-datastore-overview)
- [2 Blueprint scope](#2-blueprint-scope)
- [3 Operational notes](#3-operational-notes)
- [4 Prerequisites](#4-prerequisites)
- [5 Deployment steps](#5-deployment-steps)
- [6 Deployment verification](#6-deployment-verification)
- [Variables](#variables)
<!-- END TOC -->

## 1 Datastore overview

Firestore in Datastore mode is a managed NoSQL document database for web and mobile applications that provides automatic scaling, atomic transactions, and high availability without manual database administration.

## 2 Blueprint scope

This blueprint enables the Datastore API, initializes the App Engine application prerequisite when needed, and deploys custom composite indexes from `index.yaml`.

## 3 Operational notes

Monitor runs carefully because this blueprint invokes `local-exec` commands for index deployment. Running `terraform destroy` does not delete Firestore in Datastore mode databases automatically, so clean up databases manually when retiring a project. If the target project already contains an App Engine application, verify compatibility before applying.

## 4 Prerequisites

1. Deploy the App Engine blueprint in the target project if an App Engine application does not yet exist.
2. Enable the Datastore API on `main_project_id`.
3. Update `index.yaml` to match your application query index requirements.

## 5 Deployment steps

1. Complete the steps in [Prerequisites](#4-prerequisites).
2. Select your target Google Cloud region.
3. Run `cp terraform.tfvars.sample terraform.tfvars` and set `main_project_id` and `region` in `terraform.tfvars`.
4. Initialize and apply the Terraform configuration from this directory:

```bash
terraform init
terraform plan
terraform apply
```

Run `terraform destroy` if you need to remove Terraform-managed resources.

## 6 Deployment verification

Confirm the database and composite indexes in the Google Cloud console:

- Search for Datastore in the console search bar and open the service.
- Select the `default` database to confirm the database mode and configuration.
- Open Indexes in the navigation menu and verify the composite indexes match `index.yaml`.

<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [main_project_id](variables.tf#L15) | The ID of your project. This project must contain an app engine instance. | <code>string</code> | ✓ |  |
| [region](variables.tf#L20) | The region of your project. | <code>string</code> | ✓ |  |
<!-- END TFDOC -->
