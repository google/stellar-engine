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

# Firestore

<!-- BEGIN TOC -->
- [Introduction](#introduction)
- [Firestore Blueprint](#firestore-blueprint)
- [Disclaimer](#disclaimer)
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

This blueprint deploys a standard Firestore Native if the variables are untouched, leveraging its robust and scalable infrastructure. There you will benefit from automatic scaling, high availability, and powerful querying capabilities. Included at default is a weekly database backup to ensure the safety and reoceverability of your data.

## Disclaimer

CMEK is not supported out of the box - │ Error: Error creating Database: googleapi: Error 400: This project is not eligible to create CMEK databases. Please refer to https://cloud.google.com/firestore/docs/cmek to request access to this feature.

Be aware there default for the backup is weekly. The backup_schedule variable block in terraform.tfvars, can be set to use weekly_recurrence or daily_recurrence as needed. 

## Deployment Steps

1. Update the Variables in the variables.tf
    <br>a. There is a sample 'terraform.tfvars.sample' available as well that can be copied to create your own 'terraform.tfvars'.</br>
    <br>b. Choose your backup_schedule; Weekly or Daily options - edit your tfvars accordingly.</br>
2. Run the following command in this directory:

```bash
terraform init
terraform plan
terraform apply
```

It will take a few minutes. When complete, you shoud see an output stating the command completed successfully. 

## Verification of a successful deployment

Go to Firestore in the GCP Console. Select Firestore Studio to "Start Collection" or Indexes to "Create" new if need be. 

## Prerequisites

1. Have access to the main GCP Project ID (main_project_id)
2. You will need an existing project with billing enabled.
<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [firestore_database_name](variables.tf#L11) | The name of the Firestore database instance. | <code>string</code> | ✓ |  |
| [main_project_id](variables.tf#L22) | The main project ID of the Google Cloud project. | <code>string</code> | ✓ |  |
| [region](variables.tf#L27) | The location ID where the Firestore database will be created. | <code>string</code> | ✓ |  |
| [backup_schedule](variables.tf#L1) | The Backup schedule - select daily or weekly in your tfvars. | <code title="object&#40;&#123;&#10;  retention         &#61; string&#10;  daily_recurrence  &#61; optional&#40;bool, false&#41;&#10;  weekly_recurrence &#61; optional&#40;string&#41;&#10;&#125;&#41;">object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>null</code> |
| [kms_key_name](variables.tf#L16) | The KMS key name used to encrypt the Firestore database. | <code>string</code> |  | <code>null</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [firestore_earliest_version_time](outputs.tf#L1) | The earliest timestamp at which older versions of the data can be read from the database. |  |
| [firestore_etag](outputs.tf#L6) | This checksum is computed by the server based on the value of other fields. |  |
| [firestore_id](outputs.tf#L11) | The identifier for the Firestore resource. |  |
| [firestore_uid](outputs.tf#L16) | The system-generated UUID4 for this Database. |  |
| [firestore_version_retention_period](outputs.tf#L22) | The period during which past versions of data are retained in the database. |  |
<!-- END TFDOC -->
