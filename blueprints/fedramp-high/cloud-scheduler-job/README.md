# Cloud Scheduler

<!-- BEGIN TOC -->
- [Cloud Scheduler Blueprint](#cloud-scheduler-blueprint)
- [Deployment Steps](#deployment-steps)
- [Verification of a successful deployment](#verification-of-a-successful-deployment)
- [Variables](#variables)
- [Outputs](#outputs)
<!-- END TOC -->

## Cloud Scheduler Blueprint
This blueprint schedules a cron job to publish a PubSub message or an HTTP request every X interval of time.

## Deployment Steps
You should see this README and some terraform files.
1. Run ```cp terraform.tfvars.sample terraform.tfvars``` to copy the sample variables to your own tfvars file.

2. Update the variables as necessary in your tfvars file.
3. The usual terraform commands will do the work. To provision this example, run the following from within this directory:

```terraform init ```<br />
```terraform plan``` to see the infrastructure plan<br />
```terraform apply``` to apply the infrastructure build<br />

## Verification of a successful deployment
Use GCP console to verify if the resources have been created.
https://console.cloud.google.com/cloudscheduler

<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [description](variables.tf#L7) | Description of job. | <code>string</code> | ✓ |  |
| [main_project_id](variables.tf#L18) | Project id. | <code>string</code> | ✓ |  |
| [name](variables.tf#L23) | Name of the Cloud Scheduler job. | <code>string</code> | ✓ |  |
| [region](variables.tf#L34) | Location to deploy job. | <code>string</code> | ✓ |  |
| [schedule](variables.tf#L45) | Schedule to implement the job -- use cron-based syntax. | <code>string</code> | ✓ |  |
| [data](variables.tf#L1) | Unencoded data to be sent. | <code>string</code> |  | <code>&#34;&#34;</code> |
| [kms_key_name](variables.tf#L12) | Full path to KMS key for pubsub. | <code>string</code> |  | <code>null</code> |
| [new_topic_name](variables.tf#L28) | Name for new PubSub topic if creating one. | <code>string</code> |  | <code>null</code> |
| [retry_count](variables.tf#L39) | Number of retries. | <code>number</code> |  | <code>null</code> |
| [topic_id](variables.tf#L50) | PubSub topic ID. | <code>string</code> |  | <code>null</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [id](outputs.tf#L1) | Job ID. |  |
| [state](outputs.tf#L6) | Job state. |  |
<!-- END TFDOC -->
