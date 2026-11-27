# Bigtable

<!-- BEGIN TOC -->
- [Introduction Google Bigtable Instance](#introduction-google-bigtable-instance)
- [Bigtable Blueprint](#bigtable-blueprint)
- [Disclaimer](#disclaimer)
- [Deployment Steps](#deployment-steps)
- [Verification of a successful deployment](#verification-of-a-successful-deployment)
- [Variables](#variables)
- [Outputs](#outputs)
<!-- END TOC -->

## Introduction Google Bigtable Instance
Bigtable is a fully managed, scalable NoSQL wide-column database service for large analytical and operational workloads. 

## Bigtable Blueprint
This blueprint utilizes Terraform to automate the deployment of a Bigtable instance and configure CMEK using Cloud KMS, allowing you to control and manage your encryption keys. This enhances the security posture of your Bigtable deployment. The blueprint also includes optional table creation during instance deployment.

CMEK allows you to encrypt your Bigtable data at rest using keys that you manage in Cloud KMS. This provides greater control over key lifecycle management, including key rotation and access control. This blueprint references pre-existing Cloud KMS key rings and keys via `core_project_id`, `kms_keyring_name`, and `kms_key_name`.

## Disclaimer
- The present GCP Terraform Module in this project is set up and intended to be implemented in a FEDRAMP High environment using the Assured Workloads within the Google Cloud Platform (GCP) organization.

## Deployment Steps

You should see this README and Terraform configuration files.
1. Update the variables in `terraform.tfvars` (copied from `terraform.tfvars.sample`):
   - `main_project_id` and `core_project_id`: Main workload project ID and core KMS project ID.
   - `instance_name`, `cluster_id`, `bigtable_service_account_id`: Bigtable instance name, cluster ID, and service account ID.
   - `kms_keyring_name` and `kms_key_name`: Pre-existing Cloud KMS keyring and key names in `core_project_id`.
   - `region` and `zone`: Deployment region and zone matching your Cloud KMS key region.
2. Run the usual Terraform commands from within this directory:

```terraform init ```<br />
```terraform plan``` to see the infrastructure plan<br />
```terraform apply``` to apply the infrastructure build<br />
```terraform destroy``` to destroy the built infrastructure<br />

## Verification of a successful deployment
The instance in Bigtable will be available through the Bigtable console with the set Table, Cluster, and Instance name you provided.

It will take a few minutes. When complete, you should see an output stating the command completed successfully, a list of the created resources.
The Output will look like following

```
Outputs:

bigtable_service_identity_email = "service-{id}@gcp-sa-bigtable.iam.gserviceaccount.com"
bigtable_service_identity_uid = "projects/project_id/services/bigtableadmin.googleapis.com"
cluster_info = {
  "cluster_id" = "bigtable-test-5"
  "num_nodes" = 3
  "storage_type" = "SSD"
  "zone" = "us-east4-a"
}
instance_name = "bigtable-test-5"
table_info = {
  "Test" = {
    "automated_backup_policy" = toset([])
    "change_stream_retention" = tostring(null)
    "column_family" = toset([])
    "deletion_protection" = "UNPROTECTED"
    "id" = "projects/project_id/instances/bigtable-test-5/tables/Test"
    "instance_name" = "bigtable-test-5"
    "name" = "Test"
    "project" = "project_id"
    "split_keys" = tolist([])
    "timeouts" = null /* object */
  }
}
```
<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [bigtable_service_account_id](variables.tf#L15) | The Service Account for Bigtable. | <code>string</code> | ✓ |  |
| [cluster_id](variables.tf#L20) | The Bigtable cluster ID. | <code>string</code> | ✓ |  |
| [core_project_id](variables.tf#L25) | Core project ID. | <code>string</code> | ✓ |  |
| [instance_name](variables.tf#L36) | Provide the name of the Bigtable. | <code>string</code> | ✓ |  |
| [kms_key_name](variables.tf#L41) | The Cloud KMS key for encryption. | <code>string</code> | ✓ |  |
| [kms_keyring_name](variables.tf#L46) | KMS Keyring. | <code>string</code> | ✓ |  |
| [main_project_id](variables.tf#L51) | Main project ID. | <code>string</code> | ✓ |  |
| [deletion_protection](variables.tf#L30) | Prevent Terraform from destroying the Bigtable instance. | <code>bool</code> |  | <code>true</code> |
| [num_nodes](variables.tf#L56) | Number of nodes in the Bigtable cluster. | <code>number</code> |  | <code>1</code> |
| [region](variables.tf#L62) | Google Cloud Region. | <code>string</code> |  | <code>&#34;us-east4&#34;</code> |
| [storage_type](variables.tf#L68) | Either SSD or HDD. | <code>string</code> |  | <code>&#34;SSD&#34;</code> |
| [table](variables.tf#L74) | Table to create in the bigtable instance. Default is null. | <code>map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> |  | <code>null</code> |
| [zone](variables.tf#L83) | Google Cloud Zone. | <code>string</code> |  | <code>&#34;us-east4-a&#34;</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [bigtable_service_identity_email](outputs.tf#L15) | The email of the Bigtable Service Identity. |  |
| [bigtable_service_identity_uid](outputs.tf#L20) | The ID of the Bigtable Service Identity. |  |
| [cluster_info](outputs.tf#L25) | Information about the created Bigtable cluster. |  |
| [instance_name](outputs.tf#L35) | Bigtable instance name. |  |
| [table_info](outputs.tf#L40) | Information about the tables created (if any). |  |
<!-- END TFDOC -->
