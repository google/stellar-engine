# Workflows blueprint

This blueprint provisions a CMEK-encrypted Google Cloud Workflows workflow in a multi-project Assured Workloads environment targeting FedRAMP High and IL5 compliance regimes.

<!-- BEGIN TOC -->
- [1 Workflows overview](#1-workflows-overview)
- [2 Compliance scope](#2-compliance-scope)
- [3 Deployment steps](#3-deployment-steps)
- [4 Execution demo](#4-execution-demo)
- [5 Next steps](#5-next-steps)
- [6 Service agent notes](#6-service-agent-notes)
- [Variables](#variables)
<!-- END TOC -->

## 1 Workflows overview

Workflows is a managed orchestration platform that executes Cloud Run services, Cloud Run functions, Google Cloud APIs such as BigQuery and Vision AI, and external HTTP endpoints in a deterministic sequence. Defining operational or application workflows declaratively makes service dependencies explicit and observable end to end while encrypting workflow state with a Cloud KMS key hosted in `core_project_id`.

## 2 Compliance scope

- Deploy this blueprint inside a FedRAMP High or IL5 Assured Workloads folder within your Google Cloud organization.
- Assured Workloads enforces regional data residency and encryption guardrails required for federal and defense workloads.

## 3 Deployment steps

1. Verify that an existing Cloud KMS key ring and encryption key exist in `core_project_id` in the same region as the workflow.
2. Copy `terraform.tfvars.sample` to `terraform.tfvars` and update the project, key, and workflow settings to match your environment.
3. Initialize and apply the Terraform configuration from this directory:

```bash
terraform init
terraform plan
terraform apply
```

4. The blueprint automatically enables the Workflows API, provisions the Workflows Google-managed service identity, and grants `roles/cloudkms.cryptoKeyEncrypterDecrypter` on the configured KMS key. If the first `terraform apply` reports that the service agent does not yet exist due to IAM propagation delay, re-run `terraform apply`.
5. Open Workflows in the Google Cloud console to confirm the deployed workflow and its CMEK configuration.
6. Run `terraform destroy` if you need to tear down the deployed workflow.

## 4 Execution demo

1. Select your deployed workflow in the Google Cloud console.
2. Select `Execute`.
3. Leave the input payload empty for the default `code/example.yaml` workflow and select `Execute` to run it.
4. Inspect the execution output after completion.

## 5 Next steps

Review the [Workflows best practices documentation](https://cloud.google.com/workflows/docs/best-practice) to trigger workflows from Eventarc, Cloud Scheduler, Cloud Tasks, or parent workflows.

## 6 Service agent notes

This blueprint explicitly provisions the Workflows service agent `service-<project-number>@gcp-sa-workflows.iam.gserviceaccount.com` and grants `roles/cloudkms.cryptoKeyEncrypterDecrypter` on the configured KMS key before creating the workflow so CMEK encryption succeeds on initial deployment.

## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [main_project_id](variables.tf#L31) | The Google Cloud Project ID where the Workflows resource will be deployed. | <code>string</code> | ✓ |  |
| [name](variables.tf#L36) | Name of the workflow. | <code>string</code> | ✓ |  |
| [region](variables.tf#L41) | The Google Cloud region where the Workflows resource will be deployed and where the KMS key is located (if using CMEK in the same region). | <code>string</code> | ✓ |  |
| [core_project_id](variables.tf#L46) | The Google Cloud Project ID where shared core services like KMS keys are located. | <code>string</code> | ✓ |  |
| [kms_keyring_name](variables.tf#L51) | The name of the existing KMS Key Ring to use for workflow encryption CMEK. | <code>string</code> | ✓ |  |
| [kms_key_name](variables.tf#L56) | The name of the existing KMS Crypto Key to use for workflow encryption CMEK. | <code>string</code> | ✓ |  |
| [deletion_protection](variables.tf#L1) | Deletion protection for the workflow. | <code>bool</code> |  | <code>true</code> |
| [description](variables.tf#L7) | Description of the workflow. | <code>string</code> |  | <code>null</code> |
| [env_vars](variables.tf#L13) | Environment variables made available to your workflow execution. | <code>map&#40;string&#41;</code> |  | <code>null</code> |
| [file](variables.tf#L19) | File path to the instructions for the workflow (e.g., example.yaml). | <code>string</code> |  | <code>&#34;code&#47;example.yaml&#34;</code> |
| [logging_level](variables.tf#L25) | Logging level of workflow executions. Options: CALL_LOG_LEVEL_UNSPECIFIED, LOG_ALL_CALLS, LOG_ERRORS_ONLY, LOG_NONE. | <code>string</code> |  | <code>&#34;LOG_ERRORS_ONLY&#34;</code> |
| [workflow_service_account_id](variables.tf#L61) | The ID for the custom service account created for the workflow (e.g., 'my-workflow-sa'). | <code>string</code> |  | <code>&#34;workflows-sa&#42;</code> |

