# Google BigQuery (BigQuery) Project

<!-- BEGIN TOC -->
- [Introduction Google BigQuery (BigQuery)](#introduction-google-bigquery-bigquery)
- [Blueprint](#blueprint)
- [Prerequisites for Google BigQuery (BigQuery)](#prerequisites-for-google-bigquery-bigquery)
- [Disclaimer](#disclaimer)
- [How to deploy the Terraform Code. The Deployment Steps](#how-to-deploy-the-terraform-code-the-deployment-steps)
- [Verification of a successful deployment](#verification-of-a-successful-deployment)
- [Table creation notes](#table-creation-notes)
- [Variables](#variables)
- [Outputs](#outputs)
<!-- END TOC -->

## Introduction Google BigQuery (BigQuery)
Google BigQuery is a fully-managed, serverless data system in which querying data is made possible. Database does not need to be constantly monitored, and users can levarage data and analyze the data.
1. The Rotation Period ``` rotation_period ``` is set to 90 days indicated by 7776000s seconds,
2. The Destory Schedulded Duration is ``` destroy_scheduled_duration ``` is set to 30 days indicated by 2592000 seconds.
3. The IAM Permissions and Roles ```roles/cloudkms.cryptoKeyEncrypterDecrypter``` is assigned

## Blueprint
This blueprint contains all the necessary Terraform modules to build and deploy a BigQuery project on Google Cloud.

## Prerequisites for Google BigQuery (BigQuery)
1. Have access to the GCP Project ID
2. You will need an existing [project](https://cloud.google.com/resource-manager/docs/creating-managing-projects) with [billing enabled](https://cloud.google.com/billing/docs/how-to/modify-project) and a user with the “Project owner” [IAM](https://cloud.google.com/iam) role on that project.
3.  __Note__: to grant a user a role, take a look at the [Granting and Revoking Access](https://cloud.google.com/iam/docs/granting-changing-revoking-access#grant-single-role) documentation.

## Disclaimer
- The present GCP Terraform Module in this project is set up and intended to be implemented in either a FedRAMP-High or IL5 (Impact Level 5) environment using the Assured Workloads within the Google Cloud Platform (GCP) organization.
- Assured Workloads in both environments ensures that sensitive data and workloads in GCP adhere to the rigorous security standards mandated by the DoD, making it suitable for government agencies.

## How to deploy the Terraform Code. The Deployment Steps
You should see this README and some terraform files.
1. Review and follow the [Prerequisite for Google Bigquery (Bigquery)](#pre-requisite-for-google-bigquery-bigquery)
2. Run ```cp terraform.tfvars.sample terraform.tfvars``` to copy the sample variables to your own tfvars file.
3. Update the variables as necessary in your tfvars file.

- ```main_project_id``` with your main GCP Project ID<br />
- ```core_project_id``` with your core GCP Project ID<br />
- ```dataset_id``` with the name of your dataset<br />
- ```dataset_description``` with a description for your dataset<br />
- ```tables``` with a map of the BigQuery tables<br />
- ```region``` with the region to deploy the BigQuery dataset to.
- ```kms_keyring_name``` with the name of the KMS keyring<br />
- ```kms_key_name``` with the name of the KMS key to be used within the KMS keyring<br />

4. Although each use case is somehow built around the previous one they are self-contained so you can deploy any of them at your will. The usual terraform commands will do the work. To provision this example, run the following from within this directory:

```terraform init ``` to get the plugins<br />
```terraform plan``` to see the infrastructure plan<br />
```terraform apply``` to apply the infrastructure build<br />
```terraform destroy``` to destroy the built infrastructure<br />

## Verification of a successful deployment
The dataset will be deployed to BigQuery in the main project. To see the dataset, go to [Google BigQuery](https://console.cloud.google.com/bigquery) and search for your dataset_id. Expand the dropdown to the left of the dataset_id to see any tables that were created.

It will take a few minutes. When complete, you should see an output stating the command completed successfully, a list of the created resources.
The Output will look like following if you deploy with an empty table.
```
Apply complete! Resources: 3 added, 0 changed, 0 destroyed.

Outputs:

dataset_name = "projects/my-project/datasets/dataset"
materialized_view_ids = {}
materialized_views = {}
table_ids = {}
tables = {}
view_ids = {}
views = {}
```

## Table creation notes
1. If generating a table and the ```options.encryption_key``` setting is not set with the self_link for your KMS key, there will be Terraform drift on subsequent plans/applies where Terraform will try to replace the table and remove the KMS key. If applied through, the KMS key will not be removed as the table will inherit the same KMS key used for the dataset. To avoid this drift, pass the ```options.encryption_key``` setting in the "table" variable in the tfvars file.
2. If the ```deletion_protection``` setting is not set to ```false``` for your table, any terraform destroy will fail. Adding the setting and applying it will then allow you to delete a table through Terraform. NOTE: If not set at all, ```deletion_protection``` defaults to ```true```
<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [core_project_id](variables.tf#L17) | Core project ID. | <code>string</code> | ✓ |  |
| [dataset_description](variables.tf#L22) | Provides a discription of the deployed BigQuery Dataset. | <code>string</code> | ✓ |  |
| [dataset_id](variables.tf#L27) | This is the dataset id. | <code>string</code> | ✓ |  |
| [kms_key_name](variables.tf#L32) | The full self-link (projects/../locations/../keyRings/../cryptoKeys/..) of the existing KMS key to use for encryption. | <code>string</code> | ✓ |  |
| [kms_keyring_name](variables.tf#L37) | KMS Keyring. | <code>string</code> | ✓ |  |
| [main_project_id](variables.tf#L42) | Project ID. | <code>string</code> | ✓ |  |
| [region](variables.tf#L47) | GCP Region to deploy into. | <code>string</code> | ✓ |  |
| [tables](variables.tf#L52) | BigQuery tables. | <code>map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> | ✓ |  |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [dataset_name](outputs.tf#L17) | Dataset name. |  |
| [materialized_view_ids](outputs.tf#L22) | Materialized view IDs. |  |
| [materialized_views](outputs.tf#L27) | Materialized views. |  |
| [table_ids](outputs.tf#L32) | Table IDs. |  |
| [tables](outputs.tf#L37) | Tables. |  |
| [view_ids](outputs.tf#L42) | View IDs. |  |
| [views](outputs.tf#L47) | Views. |  |
<!-- END TFDOC -->
