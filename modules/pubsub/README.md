# Google Cloud Pub/Sub Module

This module allows managing a single Pub/Sub topic, including multiple subscriptions and IAM bindings at the topic and subscriptions levels, as well as schemas.

<!-- BEGIN TOC -->
- [Simple topic with IAM](#simple-topic-with-iam)
- [Topic with schema](#topic-with-schema)
- [Subscriptions](#subscriptions)
- [Push subscriptions](#push-subscriptions)
- [BigQuery subscriptions](#bigquery-subscriptions)
- [BigQuery Subscription with service account email](#bigquery-subscription-with-service-account-email)
- [Cloud Storage subscriptions](#cloud-storage-subscriptions)
- [Subscriptions with IAM](#subscriptions-with-iam)
- [Variables](#variables)
- [Outputs](#outputs)
- [Fixtures](#fixtures)
<!-- END TOC -->

## Simple topic with IAM

```hcl
module "pubsub" {
  source     = "./fabric/modules/pubsub"
  project_id = var.project_id
  name       = "my-topic"
  iam = {
    "roles/pubsub.viewer"     = ["group:${var.group_email}"]
    "roles/pubsub.subscriber" = ["serviceAccount:${var.service_account.email}"]
  }
}
# tftest modules=1 resources=3  inventory=simple.yaml e2e
```

## Topic with schema

```hcl
module "topic_with_schema" {
  source     = "./fabric/modules/pubsub"
  project_id = var.project_id
  name       = "my-topic"
  schema = {
    msg_encoding = "JSON"
    schema_type  = "AVRO"
    definition = jsonencode({
      "type" = "record",
      "name" = "Avro",
      "fields" = [{
        "name" = "StringField",
        "type" = "string"
        },
        {
          "name" = "FloatField",
          "type" = "float"
        },
        {
          "name" = "BooleanField",
          "type" = "boolean"
        },
      ]
    })
  }
}
# tftest modules=1 resources=2 inventory=schema.yaml e2e
```

## Subscriptions

Subscriptions are defined with the `subscriptions` variable, allowing optional configuration of per-subscription defaults. Push subscriptions need extra configuration, shown in the following example.

```hcl
module "pubsub" {
  source     = "./fabric/modules/pubsub"
  project_id = var.project_id
  name       = "my-topic"
  labels     = { test = "default" }
  subscriptions = {
    test-pull = {}
    test-pull-override = {
      labels                = { test = "override" }
      retain_acked_messages = true
    }
  }
}
# tftest modules=1 resources=3 inventory=subscriptions.yaml e2e
```

## Push subscriptions

Push subscriptions need extra configuration in the `push_configs` variable.

```hcl
module "pubsub" {
  source     = "./fabric/modules/pubsub"
  project_id = var.project_id
  name       = "my-topic"
  subscriptions = {
    test-push = {
      push = {
        endpoint = "https://example.com/foo"
      }
    }
  }
}
# tftest modules=1 resources=2 inventory=push-subscription.yaml e2e
```

## BigQuery subscriptions

BigQuery subscriptions need extra configuration in the `bigquery_subscription_configs` variable.

```hcl
module "pubsub" {
  source     = "./fabric/modules/pubsub"
  project_id = var.project_id
  name       = "my-topic"
  subscriptions = {
    test-bigquery = {
      bigquery = {
        table               = "${module.bigquery-dataset.tables["my_table"].project}:${module.bigquery-dataset.tables["my_table"].dataset_id}.${module.bigquery-dataset.tables["my_table"].table_id}"
        use_topic_schema    = true
        write_metadata      = false
        drop_unknown_fields = true
      }
    }
  }
}
# tftest modules=2 resources=5 fixtures=fixtures/bigquery-dataset.tf inventory=bigquery-subscription.yaml e2e
```

## BigQuery Subscription with service account email

BigQuery subscription example configuration with service account email.

```hcl
module "iam-service-account" {
  source     = "./fabric/modules/iam-service-account"
  project_id = var.project_id
  name       = "fixture-service-account"
  iam_project_roles = {
    "${var.project_id}" = [
      "roles/bigquery.dataEditor",
    ]
  }
}

module "pubsub" {
  source     = "./fabric/modules/pubsub"
  project_id = var.project_id
  name       = "my-topic"
  subscriptions = {
    test-bigquery-with-service-account = {
      bigquery = {
        table                 = "${module.bigquery-dataset.tables["my_table"].project}:${module.bigquery-dataset.tables["my_table"].dataset_id}.${module.bigquery-dataset.tables["my_table"].table_id}"
        use_table_schema      = true
        write_metadata        = false
        service_account_email = module.iam-service-account.email
      }
    }
  }
  depends_on = [
    module.iam-service-account # wait for IAM grants to finish
  ]
}
# tftest fixtures=fixtures/bigquery-dataset.tf inventory=bigquery-subscription-with-service-account.yaml e2e
```

## Cloud Storage subscriptions

Cloud Storage subscriptions need extra configuration in the `cloud_storage_subscription_configs` variable.

```hcl
module "pubsub" {
  source     = "./fabric/modules/pubsub"
  project_id = var.project_id
  name       = "my-topic"
  subscriptions = {
    test-cloudstorage = {
      cloud_storage = {
        bucket          = module.gcs.name
        filename_prefix = var.prefix
        filename_suffix = "test_suffix"
        max_duration    = "100s"
        max_bytes       = 1000
        avro_config = {
          write_metadata = true
        }
      }
    }
  }
}
# tftest modules=2 resources=4 fixtures=fixtures/gcs.tf inventory=cloud-storage-subscription.yaml e2e
```

## Subscriptions with IAM

```hcl
module "pubsub" {
  source     = "./fabric/modules/pubsub"
  project_id = var.project_id
  name       = "my-topic"
  subscriptions = {
    test-1 = {
      iam = {
        "roles/pubsub.subscriber" = ["serviceAccount:${var.service_account.email}"]
      }
    }
  }
}
# tftest modules=1 resources=3 inventory=subscription-iam.yaml e2e
```
<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [name](variables.tf#L73) | The name of the Pub/Sub topic to be created. | <code>string</code> | ✓ |  |
| [project_id](variables.tf#L78) | The Google Cloud Project ID where the Pub/Sub topic and subscriptions will be created. | <code>string</code> | ✓ |  |
| [iam](variables.tf#L17) | Topic-level IAM bindings (non-authoritative) in {ROLE => [MEMBERS]} format. | <code>map&#40;list&#40;string&#41;&#41;</code> |  | <code>&#123;&#125;</code> |
| [iam_bindings](variables.tf#L24) | Authoritative IAM bindings for the Pub/Sub topic in {KEY => {role = ROLE, members = [], condition = {}}}. Keys are arbitrary identifiers. Use this to explicitly define all roles/members for a topic. | <code title="map&#40;object&#40;&#123;&#10;  members &#61; list&#40;string&#41;&#10;  role    &#61; string&#10;  condition &#61; optional&#40;object&#40;&#123;&#10;    expression  &#61; string&#10;    title       &#61; string&#10;    description &#61; optional&#40;string&#41;&#10;  &#125;&#41;&#41;&#10;&#125;&#41;&#41;">map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> |  | <code>&#123;&#125;</code> |
| [iam_bindings_additive](variables.tf#L39) | Additive (non-authoritative) IAM bindings for the Pub/Sub topic. Keys are arbitrary identifiers. Use this to add individual members to specific roles without managing all members for that role. | <code title="map&#40;object&#40;&#123;&#10;  member &#61; string&#10;  role   &#61; string&#10;  condition &#61; optional&#40;object&#40;&#123;&#10;    expression  &#61; string&#10;    title       &#61; string&#10;    description &#61; optional&#40;string&#41;&#10;  &#125;&#41;&#41;&#10;&#125;&#41;&#41;">map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> |  | <code>&#123;&#125;</code> |
| [kms_key](variables.tf#L54) | The full resource path of the Cloud KMS CryptoKey to use for Customer-Managed Encryption Keys (CMEK) on the Pub/Sub topic. Set to `null` to use Google-managed encryption. | <code>string</code> |  | <code>null</code> |
| [labels](variables.tf#L60) | Optional labels to apply to the Pub/Sub topic. | <code>map&#40;string&#41;</code> |  | <code>&#123;&#125;</code> |
| [message_retention_duration](variables.tf#L67) | The minimum duration (e.g., '10s', '24h', '7d') to retain a message after it is published to the topic. Minimum is 10 minutes, maximum is 7 days. Set to `null` to use default. | <code>string</code> |  | <code>null</code> |
| [regions](variables.tf#L83) | A list of Google Cloud regions where messages published to the topic are allowed to be stored. If empty, the topic will use the default global storage policy. | <code>list&#40;string&#41;</code> |  | <code>&#91;&#93;</code> |
| [schema](variables.tf#L90) | Optional topic schema configuration. If set, all messages in this topic should follow this schema. | <code title="object&#40;&#123;&#10;  definition   &#61; string&#10;  msg_encoding &#61; optional&#40;string, &#34;ENCODING_UNSPECIFIED&#34;&#41;&#10;  schema_type  &#61; string&#10;&#125;&#41;">object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>null</code> |
| [subscriptions](variables.tf#L100) | Map of subscriptions to create for the topic. Keys are subscription names. Each value is an object configuring subscription properties (e.g., push configs, dead-letter policies, BigQuery/Cloud Storage exports, retry policies, IAM). | <code title="map&#40;object&#40;&#123;&#10;  ack_deadline_seconds         &#61; optional&#40;number&#41;&#10;  enable_exactly_once_delivery &#61; optional&#40;bool, false&#41;&#10;  enable_message_ordering      &#61; optional&#40;bool, false&#41;&#10;  expiration_policy_ttl        &#61; optional&#40;string&#41;&#10;  filter                       &#61; optional&#40;string&#41;&#10;  iam                          &#61; optional&#40;map&#40;list&#40;string&#41;&#41;, &#123;&#125;&#41; &#35; Non-authoritative IAM on subscription&#10;  labels                       &#61; optional&#40;map&#40;string&#41;&#41;&#10;  message_retention_duration   &#61; optional&#40;string&#41;&#10;  retain_acked_messages        &#61; optional&#40;bool, false&#41;&#10;  bigquery &#61; optional&#40;object&#40;&#123;&#10;    table                 &#61; string&#10;    drop_unknown_fields   &#61; optional&#40;bool, false&#41;&#10;    service_account_email &#61; optional&#40;string&#41;&#10;    use_table_schema      &#61; optional&#40;bool, false&#41;&#10;    use_topic_schema      &#61; optional&#40;bool, false&#41;&#10;    write_metadata        &#61; optional&#40;bool, false&#41;&#10;  &#125;&#41;&#41;&#10;  cloud_storage &#61; optional&#40;object&#40;&#123;&#10;    bucket          &#61; string&#10;    filename_prefix &#61; optional&#40;string&#41;&#10;    filename_suffix &#61; optional&#40;string&#41;&#10;    max_duration    &#61; optional&#40;string&#41;&#10;    max_bytes       &#61; optional&#40;number&#41;&#10;    avro_config &#61; optional&#40;object&#40;&#123;&#10;      write_metadata &#61; optional&#40;bool, false&#41;&#10;    &#125;&#41;&#41;&#10;  &#125;&#41;&#41;&#10;  dead_letter_policy &#61; optional&#40;object&#40;&#123;&#10;    topic                 &#61; string&#10;    max_delivery_attempts &#61; optional&#40;number&#41;&#10;  &#125;&#41;&#41;&#10;  iam_bindings &#61; optional&#40;map&#40;object&#40;&#123;&#10;    members &#61; list&#40;string&#41;&#10;    role    &#61; string&#10;    condition &#61; optional&#40;object&#40;&#123;&#10;      expression  &#61; string&#10;      title       &#61; string&#10;      description &#61; optional&#40;string&#41;&#10;    &#125;&#41;&#41;&#10;  &#125;&#41;&#41;, &#123;&#125;&#41; &#35; Authoritative IAM on subscription&#10;  iam_bindings_additive &#61; optional&#40;map&#40;object&#40;&#123;&#10;    member &#61; string&#10;    role   &#61; string&#10;    condition &#61; optional&#40;object&#40;&#123;&#10;      expression  &#61; string&#10;      title       &#61; string&#10;      description &#61; optional&#40;string&#41;&#10;    &#125;&#41;&#41;&#10;  &#125;&#41;&#41;, &#123;&#125;&#41; &#35; Additive IAM on subscription&#10;  push &#61; optional&#40;object&#40;&#123;&#10;    endpoint   &#61; string&#10;    attributes &#61; optional&#40;map&#40;string&#41;&#41;&#10;    no_wrapper &#61; optional&#40;bool, false&#41;&#10;    oidc_token &#61; optional&#40;object&#40;&#123;&#10;      audience              &#61; optional&#40;string&#41;&#10;      service_account_email &#61; string&#10;    &#125;&#41;&#41;&#10;  &#125;&#41;&#41;&#10;  retry_policy &#61; optional&#40;object&#40;&#123;&#10;    minimum_backoff &#61; optional&#40;string&#41;&#10;    maximum_backoff &#61; optional&#40;string&#41;&#10;  &#125;&#41;&#41;&#10;&#125;&#41;&#41;">map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> |  | <code>&#123;&#125;</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [id](outputs.tf#L17) | The full ID (self-link) of the created Pub/Sub topic. |  |
| [name](outputs.tf#L22) | The name of the created Pub/Sub topic. |  |
| [schema](outputs.tf#L27) | Schema resource. |  |
| [schema_id](outputs.tf#L32) | Schema resource id. |  |
| [subscription_id](outputs.tf#L37) | Subscription ids. |  |
| [subscriptions](outputs.tf#L44) | Subscription resources. |  |
| [topic](outputs.tf#L49) | Topic resource. |  |
| [topic_id_static](outputs.tf#L54) | The statically constructed topic ID/self-link based on project_id and name. |  |

## Fixtures

- bigquery-dataset.tf
- gcs.tf
<!-- END TFDOC -->
