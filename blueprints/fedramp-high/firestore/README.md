# Firestore

<!-- BEGIN TOC -->
- [Introduction](#introduction)
- [Firestore Blueprint](#firestore-blueprint)
- [Prerequisites and notes](#prerequisites-and-notes)
- [Deployment Steps](#deployment-steps)
- [Verification of a successful deployment](#verification-of-a-successful-deployment)
- [Prerequisites](#prerequisites)
- [Variables](#variables)
- [Outputs](#outputs)
<!-- END TOC -->

## Introduction

Cloud Firestore is a flexible, scalable database for mobile, web, and server development from Firebase and Google Cloud. It's cloud hosted NoSQL database available in Node.js, Java, Python, Unity, C++, and Go client libraries, in addition to REST and RPC APIs. Apple, Android, and web apps can access the database directory using the client libraries. Following Firestore's NoSQL data model, you store data in documents that contain fields mapping to values. These documents are stored in collections, which are containers for your documents that you can use to organize your data and build queries.

Keeping your data in sync across client apps through realtime listeners and offers offline support for mobile and web so you can build responsive apps that work regardless of network latency or Internet connectivity. And also offers seamless integration with other Firebase and Google Cloud products, including Cloud Functions.

## Firestore Blueprint

This blueprint deploys a Firestore Native database with optional Cloud KMS encryption (`kms_key_name`) and optional scheduled backups (`backup_schedule`, disabled by default when `null`).

## Prerequisites and notes

When `kms_key_name` is set, Terraform creates the Firestore service identity (`firestore.googleapis.com`), waits 60s for IAM propagation, and grants it `roles/cloudkms.cryptoKeyEncrypterDecrypter` on the configured key. Confirm that your project is eligible for Firestore CMEK and that the Cloud KMS key region matches `region`.

Database backups default to disabled (`backup_schedule = null`). Set `backup_schedule` in `terraform.tfvars` to enable either `daily_recurrence` or `weekly_recurrence`.

## Deployment Steps

1. Update variables in `terraform.tfvars` (copied from `terraform.tfvars.sample`) and optionally set `kms_key_name` or `backup_schedule` (`daily_recurrence` or `weekly_recurrence`).
2. Run the following commands in this directory:

```bash
terraform init
terraform plan
terraform apply
```

Wait a few minutes for deployment to finish. When complete, Terraform outputs the created database attributes. 

## Verification of a successful deployment

Go to Firestore in the GCP Console. Select Firestore Studio to "Start Collection" or Indexes to "Create" new if need be. 

## Prerequisites

1. Have access to the main GCP Project ID (main_project_id)
2. You will need an existing project with billing enabled.
<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [firestore_database_name](variables.tf#L25) | The name of the Firestore database instance. | <code>string</code> | ✓ |  |
| [main_project_id](variables.tf#L36) | The main project ID of the Google Cloud project. | <code>string</code> | ✓ |  |
| [region](variables.tf#L41) | The location ID where the Firestore database will be created. | <code>string</code> | ✓ |  |
| [backup_schedule](variables.tf#L15) | The Backup schedule - select daily or weekly in your tfvars. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>null</code> |
| [kms_key_name](variables.tf#L30) | The KMS key name used to encrypt the Firestore database. | <code>string</code> |  | <code>null</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [firestore_earliest_version_time](outputs.tf#L15) | The earliest timestamp at which older versions of the data can be read from the database. |  |
| [firestore_etag](outputs.tf#L20) | This checksum is computed by the server based on the value of other fields. |  |
| [firestore_id](outputs.tf#L25) | The identifier for the Firestore resource. |  |
| [firestore_uid](outputs.tf#L30) | The system-generated UUID4 for this Database. |  |
| [firestore_version_retention_period](outputs.tf#L36) | The period during which past versions of data are retained in the database. |  |
<!-- END TFDOC -->
