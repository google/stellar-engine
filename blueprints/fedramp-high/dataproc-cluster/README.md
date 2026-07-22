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

Copyright 2023 Google LLC

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

## Dataproc

<!-- START TOC -->
- [Introduction to Dataproc](#introduction-to-dataproc)
- [Blueprint](#blueprint)
- [Prerequisites for Dataproc](#prequisites-for-dataproc)
- [Disclaimer](#disclaimer)
- [The Deployment Steps](#the-deployment-steps)
- [Verification of a successful deployment](#verification-of-a-successful-deployment)
- [Troubleshooting](#troubleshooting)
- [Variables](#variables)
- [Outputs](#outputs)
<!-- END TOC -->

## Introduction to Dataproc
Dataproc is a managed Spark and Hadoop service that lets you take advantage of open source data tools for batch processing, querying, streaming, and machine learning. Dataproc automation helps you create clusters quickly, manage them easily, and save money by turning clusters off when you don't need them. With less time and money spent on administration, you can focus on your jobs and your data.

When compared to traditional, on-premises products and competing cloud services, Dataproc has a number of unique advantages for clusters of three to hundreds of nodes:

* Low cost — Dataproc is priced at only 1 cent per virtual CPU in your cluster per hour, on top of the other Cloud Platform resources you use. In addition to this low price, Dataproc clusters can include preemptible instances that have lower compute prices, reducing your costs even further. Instead of rounding your usage up to the nearest hour, Dataproc charges you only for what you really use with second-by-second billing and a low, one-minute-minimum billing period.
* Super fast — Without using Dataproc, it can take from five to 30 minutes to create Spark and Hadoop clusters on-premises or through IaaS providers. By comparison, Dataproc clusters are quick to start, scale, and shutdown, with each of these operations taking 90 seconds or less, on average. This means you can spend less time waiting for clusters and more hands-on time working with your data.
* Integrated — Dataproc has built-in integration with other Google Cloud Platform services, such as BigQuery, Cloud Storage, Cloud Bigtable, Cloud Logging, and Cloud Monitoring, so you have more than just a Spark or Hadoop cluster—you have a complete data platform. For example, you can use Dataproc to effortlessly ETL terabytes of raw log data directly into BigQuery for business reporting.
* Managed — Use Spark and Hadoop clusters without the assistance of an administrator or special software. You can easily interact with clusters and Spark or Hadoop jobs through the Google Cloud console, the Cloud SDK, or the Dataproc REST API. When you're done with a cluster, you can simply turn it off, so you don’t spend money on an idle cluster. You won’t need to worry about losing data, because Dataproc is integrated with Cloud Storage, BigQuery, and Cloud Bigtable.
* Simple and familiar — You don't need to learn new tools or APIs to use Dataproc, making it easy to move existing projects into Dataproc without redevelopment. Spark, Hadoop, Pig, and Hive are frequently updated, so you can be productive faster.

## Blueprint
This blueprint deploys a dataproc cluster and meets all compliane with Assured Workloads FedRAMP High environments.

## Prequisites for Dataproc
1. Have access to the GCP Project ID.
2. You will need an existing [project](https://cloud.google.com/resource-manager/docs/creating-managing-projects) with [billing enabled](https://cloud.google.com/billing/docs/how-to/modify-project) and a user with the “Project owner” [IAM](https://cloud.google.com/iam) role on that project.
3.  __Note__: to grant a user a role, take a look at the [Granting and Revoking Access](https://cloud.google.com/iam/docs/granting-changing-revoking-access#grant-single-role) documentation.

## Disclaimer
- The present GCP Terraform Module in this project is set up and intended to be implemented in an FedRAMP-High environment using the Assured Workloads within the Google Cloud Platform (GCP) organization.
- An Assured Workloads in FedRAMP-High environments ensures that sensitive data and workloads in GCP adhere to the rigorous security standards mandated by the DoD, making it suitable for government agencies.

## The Deployment Steps
You should see this README and some terraform files.
1. Review and follow the [Prerequisites for Dataproc](#prerequisite-for-dataproc).
2. Run ```cp terraform.tfvars.sample terraform.tfvars``` to copy the sample variables to your own tfvars file.
3. Update the variables as necessary in your tfvars file.

- ```main_project_id``` with your main GCP Project ID.<br />
- ```core_project_id``` with your core GCP Project ID.<br />
- ```network_project_id``` with your network GCP Project ID.<br />
- ```dataproc_cluster_name``` with the name for your Dataproc cluster.<br />
- ```dataproc_bucket_name``` with the name of the Cloud Storage Bucket 
- ```network_name``` with the name of the VPC network.<br />
- ```subnetwork_name``` with the name of the VPC subnetwork.<br />
- ```firewall_name``` with the name for the firewall rule.<br />
- ```kms_keyring_name``` with the name of the KMS keyring.<br />
- ```kms_key_name``` with the name of the KMS key to be used within the KMS keyring.<br />
- ```region``` with the region to deploy the Dataproc cluster to.<br />

```bash
terraform init
terraform plan
terraform apply
terraform destroy
```

## Verification of a successful deployment
The apply will take a couple of minutes to complete. Once done, the Dataproc cluster will be deployed to the main project. Browse to [Dataproc Clusters](https://console.cloud.google.com/dataproc/clusters) to view the cluster. Click the cluster name to see more details about the cluster. Under "VM Instances" you will see the VMs that were created for the Dataproc cluster along with which is the master and which are the workers. Under "Configuration" you see the Cloud Storage bucket that is linked to the cluster. You will also see the KMS key used for encryption.

## Troubleshooting
* If you encounter the error below when running a ```terraform destroy```, you will need to run a command to remove the Temporary hold.
```bash
Error: could not delete non-empty bucket due to error when deleting contents: googleapi: Error 403: Object 'tmp-dataproc-bucket-00/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/spark-job-history/' is under active Temporary hold and cannot be deleted, overwritten or archived until hold is removed., forbidden
```
Go to the [Cloud Storage Bucket](https://console.cloud.google.com/storage/browser) and open the Cloud Storage bucket created by this blueprint. There will be a bucket with a long the same name as recorded in the error message. Under that bucket, there will be a bucket called "spark-job-history". Click the "spark-job-history" bucket and copy the full path. In the terminal you are running the Terraform commands from, run the following command to remove the Temporary hold.
```bash
gsutil retention temp release gs://tmp-dataproc-bucket-00/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxx/spark-job-history/
```
Once ran, re-running a ```terraform destroy``` will succesfully destroy the Google Cloud bucket.
<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [core_project_id](variables.tf#L17) | The ID of the iac core project where the KMS key is. | <code>string</code> | ✓ |  |
| [dataproc_bucket_name](variables.tf#L22) | Name of the gcs bucket that will be created and used with Dataproc. This must be globally unique. | <code>string</code> | ✓ |  |
| [dataproc_cluster_name](variables.tf#L27) | Name of the Dataproc cluster. | <code>string</code> | ✓ |  |
| [firewall_name](variables.tf#L32) | The Dataproc firewall name. | <code>string</code> | ✓ |  |
| [kms_key_name](variables.tf#L37) | KMS key name. | <code>string</code> | ✓ |  |
| [kms_keyring_name](variables.tf#L42) | KMS keyring name. | <code>string</code> | ✓ |  |
| [main_project_id](variables.tf#L47) | The ID of the main project. | <code>string</code> | ✓ |  |
| [network_name](variables.tf#L52) | The network name. | <code>string</code> | ✓ |  |
| [network_project_id](variables.tf#L57) | The ID of the landing zone project where the VPC is. | <code>string</code> | ✓ |  |
| [subnetwork_name](variables.tf#L68) | The subnet name. | <code>string</code> | ✓ |  |
| [region](variables.tf#L62) | The region in which to provision resources. | <code>string</code> |  | <code>&#34;us-east4&#34;</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [dataproc_bucket](outputs.tf#L1) | GCS Bucket for DataProc. |  |
| [dataproc_cluster](outputs.tf#L6) | Dataproc cluster name. |  |
<!-- END TFDOC -->
