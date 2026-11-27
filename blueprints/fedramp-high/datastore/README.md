# Datastore blueprint

<!-- BEGIN TOC -->
- [1 Datastore overview](#1-datastore-overview)
- [2 Blueprint scope](#2-blueprint-scope)
- [3 Operational notes](#3-operational-notes)
- [4 Prerequisites](#4-prerequisites)
- [5 Deployment steps](#5-deployment-steps)
- [6 Deployment verification](#6-deployment-verification)
- [Variables](#variables)
- [Outputs](#outputs)
<!-- END TOC -->

## 1 Datastore overview

Firestore in Datastore mode is a managed NoSQL document database for web and mobile applications that provides automatic scaling, atomic transactions, and high availability without manual database administration.

## 2 Blueprint scope

This blueprint enables the Datastore and Firestore APIs, provisions a Firestore in Datastore mode database via `modules/firestore` with deletion protection enabled by default, optionally configures Customer-Managed Encryption Keys and backup schedules, and manages composite indexes natively in Terraform from `index.yaml` or `var.indexes`.

## 3 Operational notes

- `deletion_protection` defaults to `true` and `deletion_policy` defaults to `ABANDON` so accidental `terraform destroy` runs do not remove stored data.
- Set `database_create = false` when managing composite indexes on an existing Datastore mode database.
- Entries in `index.yaml` map non-ancestor indexes (`ancestor: no` or omitted) to `COLLECTION_GROUP` and ancestor indexes (`ancestor: yes`) to `COLLECTION_RECURSIVE` under `api_scope = "DATASTORE_MODE_API"`.

## 4 Prerequisites

1. Grant the deploying identity `roles/datastore.owner` or Firestore database and index admin permissions and `roles/serviceusage.serviceUsageAdmin` on `main_project_id`.
2. When setting `kms_key_name`, grant the deploying identity `roles/cloudkms.admin` or a custom role with `cloudkms.cryptoKeys.getIamPolicy` and `cloudkms.cryptoKeys.setIamPolicy` on the KMS key so Terraform can grant `roles/cloudkms.cryptoKeyEncrypterDecrypter` to the Firestore service agent.
3. Update `index.yaml` or set `var.indexes` to match your application query index requirements.

## 5 Deployment steps

1. Complete the steps in [Prerequisites](#4-prerequisites).
2. Select your target Google Cloud region within your Assured Workloads compliance boundary.
3. Run `cp terraform.tfvars.sample terraform.tfvars` and set `main_project_id`, `region`, and optional `kms_key_name` in `terraform.tfvars`.
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
- Select the target database, `(default)` by default, to confirm the `DATASTORE_MODE` database configuration and CMEK settings.
- Open Indexes in the navigation menu and verify the composite indexes match `index.yaml` or `var.indexes`.
<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [main_project_id](variables.tf#L119) | Google Cloud project ID hosting the Datastore mode database and indexes. | <code>string</code> | ✓ |  |
| [region](variables.tf#L125) | Google Cloud location or region for the Datastore mode database. | <code>string</code> | ✓ |  |
| [app_engine_integration_mode](variables.tf#L15) | App Engine integration mode for the Datastore mode database: ENABLED or DISABLED. | <code>string</code> |  | <code>&#34;DISABLED&#34;</code> |
| [backup_schedule](variables.tf#L29) | Optional backup schedule configuration for the Datastore mode database. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>null</code> |
| [concurrency_mode](variables.tf#L39) | Optional concurrency control mode: OPTIMISTIC, PESSIMISTIC, or OPTIMISTIC_WITH_ENTITY_GROUPS. | <code>string</code> |  | <code>null</code> |
| [database_create](variables.tf#L56) | Whether to create the Firestore in Datastore mode database or manage indexes on an existing database. | <code>bool</code> |  | <code>true</code> |
| [database_name](variables.tf#L63) | Name of the Firestore in Datastore mode database. | <code>string</code> |  | <code>&#34;&#40;default&#41;&#34;</code> |
| [deletion_policy](variables.tf#L70) | Terraform deletion policy when destroying the database resource: ABANDON or DELETE. | <code>string</code> |  | <code>&#34;ABANDON&#34;</code> |
| [deletion_protection](variables.tf#L81) | Whether to enable GCP deletion protection on the Datastore mode database. | <code>bool</code> |  | <code>true</code> |
| [index_file](variables.tf#L88) | Path relative to the blueprint directory for a Datastore YAML index file used when `indexes` is null. | <code>string</code> |  | <code>&#34;index.yaml&#34;</code> |
| [indexes](variables.tf#L94) | Explicit composite index definitions managed via google_firestore_index; overrides `index_file` when set. | <code>map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> |  | <code>null</code> |
| [kms_key_name](variables.tf#L113) | Optional full Cloud KMS CryptoKey resource ID used for Customer-Managed Encryption Keys. | <code>string</code> |  | <code>null</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [firestore_database](outputs.tf#L15) | Provisioned Firestore in Datastore mode database resource. |  |
| [firestore_index_ids](outputs.tf#L20) | Map of Datastore composite index resource IDs. |  |
| [firestore_indexes](outputs.tf#L25) | Provisioned Datastore composite index resources. |  |
<!-- END TFDOC -->
