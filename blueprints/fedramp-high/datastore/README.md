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

# Datastore Blueprint

<!-- BEGIN TOC -->
- [Introduction to Datastore](#introduction-to-datastore)
- [Datastore Blueprint](#datastore-blueprint)
- [Disclaimer](#disclaimer)
- [Prerequisites](#prerequisites)
- [Deployment Steps](#deployment-steps)
- [Verification of a successful deployment](#verification-of-a-successful-deployment)
- [Variables](#variables)
<!-- END TOC -->

## Introduction to Datastore
Google Cloud Datastore is a highly scalable, fully managed NoSQL document database built for web and mobile applications. Firestore is the next generation of Datastore. It automatically scales to handle vast amounts of data and high transaction loads without requiring database administration. Datastore offers rich query capabilities, atomic transactions, and high availability, making it ideal for storing non-relational data.

# Datastore Blueprint
This Terraform blueprint primarily focuses on provisioning and configuring Google Cloud Datastore for a project. It first enables the necessary Datastore API and then establishes a Google App Engine application, which is a prerequisite for Datastore. The blueprint strategically incorporates delays to ensure the App Engine instance is fully initialized before proceeding to deploy and configure the Datastore instance, including the custom indexes.

## Disclaimer
This module leverages local execs and should be carefully monitored. Datastore Mode databases are not automatically deleted by `terraform destroy` and serves as an important warning and a reminder for manual cleanup. If App Engine has been previously deployed, the datastore may not deploy properly.

## Prerequisites
1. For projects using Datastore, the App Engine Blueprint must be installed.
2. Enable Datastore API
3. Modify index.yaml per your datastore requirements

## Deployment Steps
1. Review and follow necessary [Prerequisites Steps](#prerequisites-steps).
2. Determine your GCP region for deployment
3. Run ```cp terraform.tfvars.sample terraform.tfvars``` to copy the sample variables to your own tfvars file & update the variables as necessary in your tfvars file.
  a. edit the project ID and region
4. The usual terraform commands will do the work. To provision this example, run the following from within this directory:

```terraform init```<br />
```terraform plan``` to see the infrastructure plan<br />
```terraform apply``` to apply the infrastructure build<br />
```terraform destroy``` only if you wish to destroy the built infrastructure<br />

## Verification of a successful deployment
To confirm your deployment was successful, follow these steps in the GCP Console:

- Search for "Datastore" in the search bar
- Select the Datastore service in the dropdown
- Select the "default" database
- Here, you can review the structure of the database to ensure it's set up as expected.
- Select "Indexes" in the left side menu
- Ensure the indexes are set as configured in the index.yaml file
<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [main_project_id](variables.tf#L1) | The ID of your project. This project must contain an app engine instance. | <code>string</code> | ✓ |  |
| [region](variables.tf#L6) | The region of your project. | <code>string</code> | ✓ |  |
<!-- END TFDOC -->