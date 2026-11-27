# Google BigQuery Project
This blueprint contains the Terraform configuration to deploy a BigQuery dataset, tables, and a dedicated Cloud KMS key ring and key in a single Google Cloud project.

## Introduction Google BigQuery
Google BigQuery is a fully-managed, serverless data warehouse that supports CMEK encryption for datasets and tables.
1. The default key `rotation_period` is `7776000s` (90 days).
2. `destroy_scheduled_duration` on the `"default"` key in `var.kms_key_names` defaults to `null` (which uses Cloud KMS's default scheduled destruction duration) and can be set per key.
3. `roles/cloudkms.cryptoKeyEncrypterDecrypter` is granted on the generated key to the project's BigQuery default service account (`data.google_bigquery_default_service_account.bq_sa`).

## Prerequisites for Google BigQuery Project
1. Terraform enables the BigQuery API (`bigquery.googleapis.com`) on `main_project_id`. Ensure the Cloud KMS API (`cloudkms.googleapis.com`) is enabled on `main_project_id` before applying.
2. Have access to an existing [Google Cloud project](https://cloud.google.com/resource-manager/docs/creating-managing-projects) with [billing enabled](https://cloud.google.com/billing/docs/how-to/modify-project) and grant the deploying identity the required BigQuery, Cloud KMS, and Service Usage permissions (such as `roles/bigquery.admin`, `roles/cloudkms.admin`, and `roles/serviceusage.serviceUsageAdmin`).
3. Refer to the [Granting and Revoking Access](https://cloud.google.com/iam/docs/granting-changing-revoking-access#grant-single-role) documentation for granting IAM roles.

## Disclaimer
- The present GCP Terraform Module in this project is set up and intended to be implemented in either a FedRAMP-High or IL5 (Impact Level 5) environment using the Assured Workloads within the Google Cloud Platform (GCP) organization.
- Assured Workloads in both environments ensures that sensitive data and workloads in GCP adhere to the rigorous security standards mandated by the DoD, making it suitable for government agencies.
<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [dataset_description](variables.tf#L17) | Provides a discription of the deployed BigQuery Dataset. | <code>string</code> | ✓ |  |
| [dataset_id](variables.tf#L22) | This is the dataset id. | <code>string</code> | ✓ |  |
| [kms_keyring_name](variables.tf#L81) | Keyring attributes. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> | ✓ |  |
| [main_project_id](variables.tf#L89) | Project ID. | <code>string</code> | ✓ |  |
| [region](variables.tf#L94) | GCP Region to deploy into. | <code>string</code> | ✓ |  |
| [kms_key_names](variables.tf#L27) | Key names and base attributes. Set attributes to null if not needed. | <code>map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> |  | <code>&#123;&#8230;&#125;</code> |
| [tables](variables.tf#L99) | BigQuery tables. | <code>map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> |  | <code>&#123;&#125;</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [dataset_name](outputs.tf#L17) | Dataset name. |  |
| [keyring](outputs.tf#L22) | Keyring name. |  |
| [materialized_view_ids](outputs.tf#L27) | Materialized view IDs. |  |
| [materialized_views](outputs.tf#L32) | Materialized views. |  |
| [table_ids](outputs.tf#L37) | Table IDs. |  |
| [tables](outputs.tf#L42) | Tables. |  |
| [view_ids](outputs.tf#L47) | View IDs. |  |
| [views](outputs.tf#L52) | Views. |  |
<!-- END TFDOC -->
## Deployment Steps
1. Review the prerequisites above and copy the sample variables file:

```bash
cp terraform.tfvars.sample terraform.tfvars
```

2. Update the variables in `terraform.tfvars` for your environment:
   - `main_project_id`: Target Google Cloud project ID where the dataset and Cloud KMS resources are created.
   - `dataset_id`: BigQuery dataset ID.
   - `dataset_description`: Description of the deployed BigQuery dataset.
   - `region`: Google Cloud region where the BigQuery dataset and Cloud KMS key ring are deployed.
   - `tables`: Map of BigQuery table configurations following the `modules/bigquery-dataset` `tables` object schema.
   - `kms_keyring_name`: Object containing `location` and `name` for the Cloud KMS key ring:

```hcl
kms_keyring_name = {
  location = "us-east4"
  name     = "example-bq-keyring"
}
```

   - `kms_key_names`: Map of Cloud KMS key definitions (must include a `"default"` key used to encrypt the BigQuery dataset).

3. Initialize, review, and apply the configuration:

```bash
terraform init
terraform plan
terraform apply
terraform destroy
```

When `terraform apply` completes, the outputs match `outputs.tf`:

```text
Outputs:

dataset_name = "projects/example-project/datasets/dataset_id_00"
keyring = {
  "id" = "projects/example-project/locations/us-east4/keyRings/example-bq-keyring"
  "location" = "us-east4"
  "name" = "example-bq-keyring"
  "project" = "example-project"
  "timeouts" = null /* object */
}
materialized_view_ids = {}
materialized_views = {}
table_ids = {}
tables = {}
view_ids = {}
views = {}
```
