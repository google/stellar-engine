# Dataproc blueprint

<!-- BEGIN TOC -->
- [1 Dataproc overview](#1-dataproc-overview)
- [2 Blueprint scope](#2-blueprint-scope)
- [3 Prerequisites](#3-prerequisites)
- [4 Compliance scope](#4-compliance-scope)
- [5 Deployment steps](#5-deployment-steps)
- [6 Deployment verification](#6-deployment-verification)
- [7 Troubleshooting](#7-troubleshooting)
- [Variables](#variables)
- [Outputs](#outputs)
<!-- END TOC -->

## 1 Dataproc overview

Dataproc is a managed Apache Spark and Apache Hadoop service for batch processing, querying, streaming, and machine learning on Google Cloud:

- Per-second billing with a one-minute minimum and optional Spot VMs reduces cluster compute costs when you shut down idle clusters.
- Automated cluster provisioning, scaling, and teardown typically complete in 90 seconds or less.
- Native integration with BigQuery, Cloud Storage, Bigtable, Cloud Logging, and Cloud Monitoring connects Spark and Hadoop jobs directly to managed storage and observability services.
- Managed cluster operations let you submit jobs through the Google Cloud console, `gcloud` CLI, or Dataproc REST API while persisting data in Cloud Storage or BigQuery across cluster lifecycles.
- Standard open-source Spark, Hadoop, Pig, and Hive versions let you migrate existing pipelines without rewriting application code.

## 2 Blueprint scope

This blueprint deploys a CMEK-encrypted Dataproc cluster, staging bucket, and VPC firewall rule configured for Assured Workloads FedRAMP High environments.

## 3 Prerequisites

1. Identify your target workload, Shared VPC host, and KMS core Google Cloud project IDs.
2. Ensure the target [project](https://cloud.google.com/resource-manager/docs/creating-managing-projects) has [billing enabled](https://cloud.google.com/billing/docs/how-to/modify-project) and your deploying principal holds required [IAM](https://cloud.google.com/iam) permissions, following [Granting, changing, and revoking access](https://cloud.google.com/iam/docs/granting-changing-revoking-access#grant-single-role).

## 4 Compliance scope

- Deploy this blueprint inside a FedRAMP High Assured Workloads folder within your Google Cloud organization.
- Assured Workloads enforces regional data residency and encryption guardrails required for federal workloads.

## 5 Deployment steps

1. Complete the steps in [Prerequisites](#3-prerequisites).
2. Copy the sample variables file with `cp terraform.tfvars.sample terraform.tfvars`.
3. Update `terraform.tfvars` with values for your environment:
   - Set `main_project_id` to the workload Google Cloud project ID.
   - Set `core_project_id` to the core project ID hosting the Cloud KMS key.
   - Set `network_project_id` to the Shared VPC host project ID.
   - Set `dataproc_cluster_name` to the Dataproc cluster name.
   - Set `dataproc_bucket_name` to a globally unique Cloud Storage staging bucket name.
   - Set `network_name` and `subnetwork_name` to your target VPC network and subnet names.
   - Set `firewall_name` to the intra-cluster VPC firewall rule name.
   - Set `kms_keyring_name` and `kms_key_name` to the Cloud KMS key ring and key used for CMEK encryption.
   - Set `region` to the target Google Cloud region.
4. Initialize and apply the Terraform configuration:

```bash
terraform init
terraform plan
terraform apply
```

Run `terraform destroy` when you want to tear down the cluster and associated resources.

## 6 Deployment verification

Open [Dataproc Clusters](https://console.cloud.google.com/dataproc/clusters) in the Google Cloud console after `terraform apply` completes:

- Select the cluster name and inspect the VM Instances tab to confirm the master and worker nodes are running.
- Inspect the Configuration tab to confirm the staging Cloud Storage bucket and Customer-Managed Encryption Key are attached.

## 7 Troubleshooting

If `terraform destroy` fails with a `403` error reporting that `spark-job-history/` is under an active temporary hold:

```text
Error: could not delete non-empty bucket due to error when deleting contents: googleapi: Error 403: Object 'tmp-dataproc-bucket-00/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/spark-job-history/' is under active Temporary hold and cannot be deleted, overwritten or archived until hold is removed., forbidden
```

1. Open [Cloud Storage](https://console.cloud.google.com/storage/browser) in the Google Cloud console and locate the `spark-job-history` object path inside the staging bucket.
2. Release the temporary hold from your terminal:

```bash
gsutil retention temp release gs://tmp-dataproc-bucket-00/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxx/spark-job-history/
```

3. Re-run `terraform destroy` to delete the bucket cleanly.

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
| [dataproc_bucket](outputs.tf#L15) | GCS Bucket for DataProc. |  |
| [dataproc_cluster](outputs.tf#L20) | Dataproc cluster name. |  |
<!-- END TFDOC -->
