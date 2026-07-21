# Google Pub/Sub Project

<!-- BEGIN TOC -->
- [Introduction](#introduction)
- [Pub/Sub Blueprint](#pubsub-blueprint)
- [Disclaimer](#disclaimer)
- [Pre-requisite](#pre-requisite)
- [Deployment Steps](#deployment-steps)
- [Verification of a successful deployment](#verification-of-a-successful-deployment)
- [Variables](#variables)
- [Outputs](#outputs)
<!-- END TOC -->

## Introduction
Pub/Sub allows services to communicate asynchronously, and it is used for streamlining analytics and data integration pipelines. The purpose of pub-sub is to load as well as transfer data. Pub-Sub permits latencies on the order of 100 milliseconds. Moreover, it enables the creation of systems of event producers and consumers, referred to as publishers and subscribers. The way that this works is that publishers communicate with subscribers asynchronously by broadcasting events instead of the synchronous remote procedure calls (RPCs). Then, publishers send events to the Pub/Sub service, without regard to how or when these events are to be processed. Afterwards, Pub/Sub delivers events to all the services that react to them.

## Pub/Sub Blueprint
This blueprint contains all the necessary Terraform modules to build and deploy a Pub/Sub. This is an asynchronous and scalable messaging service that decouples services producing messages from services processing those messages.

## Disclaimer
- The present GCP Terraform Module in this project is set up and intended to be implemented in either a FedRAMP-High or IL5 (Impact Level 5) environment using the Assured Workloads within the Google Cloud Platform (GCP) organization.
- Assured Workloads in both environments ensures that sensitive data and workloads in GCP adhere to the rigorous security standards mandated by the DoD, making it suitable for government agencies.

## Pre-requisite
1. The Principal (user or group) must have Cloud KMS Admin permission at the GCP Level.
2. Have access to the GCP Project ID.
3.  You will need an existing [project](https://cloud.google.com/resource-manager/docs/creating-managing-projects) with [billing enabled](https://cloud.google.com/billing/docs/how-to/modify-project) and a user with the “Project owner” [IAM](https://cloud.google.com/iam) role on that project. __Note__: to grant a user a role, take a look at the [Granting and Revoking Access](https://cloud.google.com/iam/docs/granting-changing-revoking-access#grant-single-role) documentation.

## Deployment Steps
You should see this README and some terraform files.
1. Run ```cp terraform.tfvars.sample terraform.tfvars``` to copy the sample variables to your own tfvars file.
2. Update the variables as necessary in your tfvars file.
3. Although each use case is somehow built around the previous one they are self-contained so you can deploy any of them at your will. The usual terraform commands will do the work:

```bash
terraform init
terraform plan
terraform apply
```

## Verification of a successful deployment

Access the GCP Console, search for PubSub, select your Topic or Create Subscription under to your Topic.

It will take a few minutes. When complete, you should see an output stating the command completed successfully, a list of the created resources.

<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [core_project_id](variables.tf#L22) | Core project ID. | <code>string</code> | ✓ |  |
| [kms_key_name](variables.tf#L26) | The full self-link (projects/../locations/../keyRings/../cryptoKeys/..) of the existing KMS key to use for disk encryption. | <code>string</code> | ✓ |  |
| [kms_keyring_name](variables.tf#L31) | Keyring attributes. | <code>string</code> | ✓ |  |
| [main_project_id](variables.tf#L36) | Project ID. | <code>string</code> | ✓ |  |
| [publisher_account_id](variables.tf#L41) | Publisher account ID. | <code>string</code> | ✓ |  |
| [publisher_name](variables.tf#L46) | Publisher name. | <code>string</code> | ✓ |  |
| [pubsub_topic](variables.tf#L51) | PubSub topic. | <code>string</code> | ✓ |  |
| [region](variables.tf#L56) | GCP Region to deploy into. | <code>string</code> | ✓ |  |
| [subscriber_account_id](variables.tf#L61) | Subscriber account ID. | <code>string</code> | ✓ |  |
| [subscriber_name](variables.tf#L66) | Subscriber name. | <code>string</code> | ✓ |  |
| [allowed_persistence_regions](variables.tf#L17) | The allowed persistence regions for the Pub/Sub topic. | <code>list&#40;string&#41;</code> |  | <code>&#91;&#34;us-east4&#34;&#93;</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [publisher_service_account_email](outputs.tf#L17) | The email of the publisher service account. |  |
| [subscriber_service_account_email](outputs.tf#L22) | The email of the subscriber service account. |  |
<!-- END TFDOC -->
