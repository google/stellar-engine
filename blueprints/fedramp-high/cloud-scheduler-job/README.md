# Cloud Scheduler job blueprint

This blueprint schedules a managed Cloud Scheduler cron job that publishes messages to an existing Pub/Sub topic.

<!-- BEGIN TOC -->
- [1 Cloud Scheduler overview](#1-cloud-scheduler-overview)
- [2 Compliance scope](#2-compliance-scope)
- [3 Prerequisites](#3-prerequisites)
- [4 Deployment steps](#4-deployment-steps)
- [5 Deployment verification](#5-deployment-verification)
- [6 Operational notes](#6-operational-notes)
- [Variables](#variables)
- [Outputs](#outputs)
<!-- END TOC -->

## 1 Cloud Scheduler overview

Cloud Scheduler is a managed cron service that triggers batch jobs, App Engine handlers, HTTP endpoints, and Pub/Sub topics on a recurring schedule. Publishing scheduled messages to an existing Pub/Sub topic decouples job scheduling from downstream consumers.

## 2 Compliance scope

- Deploy this blueprint inside a FedRAMP High or IL5 Assured Workloads folder within your Google Cloud organization.
- Assured Workloads enforces regional data residency and encryption guardrails required for federal and defense workloads.

## 3 Prerequisites

Verify that the following resources and permissions exist before running Terraform:

- Provision a target workload project (`main_project_id`) to host the Cloud Scheduler job, plus `core_project_id` if the target Pub/Sub topic uses a Cloud KMS key in a separate security project.
- Provision the target Pub/Sub topic ahead of time, such as through `blueprints/fedramp-high/pub-sub-project`, and record its full resource path `projects/<project-id>/topics/<topic-name>`.
- If the Pub/Sub topic uses CMEK, record the Cloud KMS CryptoKey path in `kms_key_name` so Terraform can grant `roles/cloudkms.cryptoKeyEncrypterDecrypter` to the Pub/Sub service agent.
- Grant the deploying identity `roles/cloudscheduler.admin`, `roles/pubsub.publisher`, `roles/serviceusage.serviceUsageAdmin`, and `roles/resourcemanager.projectIamAdmin` on `main_project_id`, and ensure `cloudscheduler.googleapis.com` and `pubsub.googleapis.com` can be enabled.

## 4 Deployment steps

1. Copy the sample variables file and update `terraform.tfvars` with your project ID, region, schedule, existing Pub/Sub topic path, and optional KMS key path:

```bash
cp terraform.tfvars.sample terraform.tfvars
```

2. Initialize the Terraform working directory:

```bash
terraform init
```

3. Review the execution plan to verify the Cloud Scheduler job and IAM bindings:

```bash
terraform plan
```

4. Apply the configuration to create the Cloud Scheduler job:

```bash
terraform apply
```

5. If you need to remove the Cloud Scheduler job without affecting the existing Pub/Sub topic or KMS key, run `terraform destroy`:

```bash
terraform destroy
```

## 5 Deployment verification

Verify the scheduled job in the Google Cloud console or with the `gcloud` CLI:

- In the Google Cloud console, open Cloud Scheduler in `main_project_id`, confirm the job configured by `name` is enabled, trigger a manual run, and verify message delivery on a test Pub/Sub subscription.
- List and inspect the job from the command line, then trigger an on-demand execution:

```bash
gcloud scheduler jobs list --project=<MAIN_PROJECT_ID> --location=<REGION>
gcloud scheduler jobs describe <JOB_NAME> --location=<REGION> --project=<MAIN_PROJECT_ID>
gcloud scheduler jobs run <JOB_NAME> --location=<REGION> --project=<MAIN_PROJECT_ID>
```

## 6 Operational notes

- This blueprint targets an existing Pub/Sub topic and does not create new topics.
- Set `schedule` using standard [crontab syntax](https://en.wikipedia.org/wiki/Cron#CRON_expression).
- Cloud Scheduler jobs are regional resources, so match `gcp_region` to your Assured Workloads deployment region.
- Update `main.tf` if your workload requires HTTP or App Engine targets instead of Pub/Sub targets.

<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [description](variables.tf#L22) | Description of the Cloud Scheduler job. | <code>string</code> | ✓ |  |
| [gcp_region](variables.tf#L27) | The Google Cloud region where the Cloud Scheduler job will be deployed. | <code>string</code> | ✓ |  |
| [main_project_id](variables.tf#L38) | The Google Cloud Project ID where the Cloud Scheduler job will be created. | <code>string</code> | ✓ |  |
| [name](variables.tf#L67) | The name of the Cloud Scheduler job. | <code>string</code> | ✓ |  |
| [schedule](variables.tf#L78) | The schedule in the [Crontab format](https://en.wikipedia.org/wiki/Cron#CRON_expression) (e.g., '*/2 * * * *' for every two minutes). | <code>string</code> | ✓ |  |
| [topic_id](variables.tf#L83) | The full resource path of the existing Pub/Sub topic (e.g., `projects/<PROJECT_ID>/topics/<TOPIC_NAME>`) to which messages will be published. | <code>string</code> | ✓ |  |
| [data](variables.tf#L15) | The base64-encoded data to be sent as the Pub/Sub message payload. | <code>string</code> |  | <code>null</code> |
| [kms_key_name](variables.tf#L32) | The full resource path of the existing Cloud KMS CryptoKey used for CMEK on the Pub/Sub topic. This key is assumed to be in the `core_project_id`. | <code>string</code> |  | <code>null</code> |
| [max_backoff_duration](variables.tf#L43) | The maximum amount of time to wait before retrying a failed attempt, as a duration string (e.g., '5s', '2m', '1h'). | <code>string</code> |  | <code>null</code> |
| [max_doublings](variables.tf#L49) | The maximum number of times to double the retry delay, up to `max_retry_duration`. | <code>number</code> |  | <code>null</code> |
| [max_retry_duration](variables.tf#L55) | The maximum cumulative time in which retries are attempted, as a duration string. | <code>string</code> |  | <code>null</code> |
| [min_backoff_duration](variables.tf#L61) | The minimum amount of time to wait before retrying a failed attempt, as a duration string. | <code>string</code> |  | <code>null</code> |
| [retry_count](variables.tf#L72) | The number of attempts that the system will make to run the job if the first attempt fails. Retries are attempted over a longer period of time than the schedule. | <code>number</code> |  | <code>null</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [id](outputs.tf#L15) | Job ID. |  |
| [state](outputs.tf#L20) | Job state. |  |
<!-- END TFDOC -->
