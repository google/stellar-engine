# Google BigQuery (BigQuery) Project
This blueprint contains all the necessary Terraform modules to build and deploy a BigQuery project on Google Cloud.

## Introduction Google BigQuery (BigQuery)
Google BigQuery is a fully-managed, serverless data system in which querying data is made possible. Database does not need to be constantly monitored, and users can levarage data and analyze the data.
1. The Rotation Period ``` rotation_period ``` is set to 90 days indicated by 7776000s seconds,
2. The Destory Schedulded Duration is ``` destroy_scheduled_duration ``` is set to 30 days indicated by 2592000 seconds.
3. The IAM Permissions and Roles ```roles/cloudkms.cryptoKeyEncrypterDecrypter``` is assigned

## Pre-requisite for Google BigQuery (BigQuery)
1. The Principal (user or group) must enablw BigQuery API in their Google Cloud Project
2. Have access to the GCP Project ID
3.  You will need an existing [project](https://cloud.google.com/resource-manager/docs/creating-managing-projects) with [billing enabled](https://cloud.google.com/billing/docs/how-to/modify-project) and a user with the “Project owner” [IAM](https://cloud.google.com/iam) role on that project.
4.  __Note__: to grant a user a role, take a look at the [Granting and Revoking Access](https://cloud.google.com/iam/docs/granting-changing-revoking-access#grant-single-role) documentation.

## Disclaimer
- The present GCP Terraform Module in this project is set up and intended to be implemented in either a FedRAMP-High or IL5 (Impact Level 5) environment using the Assured Workloads within the Google Cloud Platform (GCP) organization.
- Assured Workloads in both environments ensures that sensitive data and workloads in GCP adhere to the rigorous security standards mandated by the DoD, making it suitable for government agencies.
<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [dataset_description](variables.tf#L17) | Provides a discription of the deployed BigQuery Dataset. | <code>string</code> | ✓ |  |
| [dataset_id](variables.tf#L22) | This is the dataset id. | <code>string</code> | ✓ |  |
| [kms_key_names](variables.tf#L27) | Key names and base attributes. Set attributes to null if not needed. | <code title="map&#40;object&#40;&#123;&#10;  destroy_scheduled_duration    &#61; optional&#40;string&#41;&#10;  rotation_period               &#61; optional&#40;string, &#34;7776000s&#34;&#41; &#35; CIS Compliance Benchmark 1.10&#10;  labels                        &#61; optional&#40;map&#40;string&#41;&#41;&#10;  purpose                       &#61; optional&#40;string, &#34;ENCRYPT_DECRYPT&#34;&#41;&#10;  skip_initial_version_creation &#61; optional&#40;bool, false&#41;&#10;  version_template &#61; optional&#40;object&#40;&#123;&#10;    algorithm        &#61; string&#10;    protection_level &#61; optional&#40;string, &#34;HSM&#34;&#41;&#10;  &#125;&#41;&#41;&#10;&#10;&#10;  iam &#61; optional&#40;map&#40;list&#40;string&#41;&#41;, &#123;&#125;&#41;&#10;  iam_bindings &#61; optional&#40;map&#40;object&#40;&#123;&#10;    members &#61; list&#40;string&#41;&#10;    role    &#61; string&#10;    condition &#61; optional&#40;object&#40;&#123;&#10;      expression  &#61; string&#10;      title       &#61; string&#10;      description &#61; optional&#40;string&#41;&#10;    &#125;&#41;&#41;&#10;  &#125;&#41;&#41;, &#123;&#125;&#41;&#10;&#10;&#10;  iam_bindings_additive &#61; optional&#40;map&#40;object&#40;&#123;&#10;    member &#61; string&#10;    role   &#61; string&#10;    condition &#61; optional&#40;object&#40;&#123;&#10;      expression  &#61; string&#10;      title       &#61; string&#10;      description &#61; optional&#40;string&#41;&#10;    &#125;&#41;&#41;&#10;  &#125;&#41;&#41;, &#123;&#125;&#41;&#10;&#125;&#41;&#41;&#10;&#10;&#10;default &#61; &#123;&#10;  &#34;default&#34; &#61; &#123;&#10;    destroy_scheduled_duration    &#61; null&#10;    rotation_period               &#61; null&#10;    labels                        &#61; null&#10;    purpose                       &#61; &#34;ENCRYPT_DECRYPT&#34;&#10;    skip_initial_version_creation &#61; false&#10;    version_template &#61; &#123;&#10;      algorithm        &#61; &#34;GOOGLE_SYMMETRIC_ENCRYPTION&#34;&#10;      protection_level &#61; &#34;HSM&#34;&#10;    &#125;&#10;&#10;&#10;    iam                   &#61; &#123;&#125;&#10;    iam_bindings          &#61; &#123;&#125;&#10;    iam_bindings_additive &#61; &#123;&#125;&#10;  &#125;&#10;&#125;">map&#40;object&#40;&#123;&#8230;&#125;</code> | ✓ |  |
| [kms_keyring_name](variables.tf#L82) | Keyring attributes. | <code title="object&#40;&#123;&#10;  location &#61; string&#10;  name     &#61; string&#10;&#125;&#41;">object&#40;&#123;&#8230;&#125;&#41;</code> | ✓ |  |
| [main_project_id](variables.tf#L90) | Project ID. | <code>string</code> | ✓ |  |
| [region](variables.tf#L95) | GCP Region to deploy into. | <code>string</code> | ✓ |  |
| [tables](variables.tf#L100) | BigQuery tables. | <code>map&#40;map&#40;string&#41;&#41;</code> |  | <code>&#123;&#125;</code> |

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
## How to deploy the Terraform Code. The Deployment Steps
You should see this README and some terraform files.
1. Update the Variables in the variables.tf and also the properties within the keys variables. For reference update the following variables and associated properties

- ```project_id```  with your GCP Project ID<br />
-  ```email```  with your email address<br />
- ```location```  with the GCP Location<br />
- ```keyring``` with the location of the keyring and the name of the
keyring, for example <br />
```bash
  default = {
    location = "us-east4"
    name     = "may-bq-keyring"
  }
```
- ```keys```  with the right properties, update the ```updated-the-runner-key-name``` , ```labels = { "team" = ``` ,
```iam = { roles/cloudkms.cryptoKeyEncrypterDecrypter = ["user:YOUR-EMAIL-ADDRESS]```

2. There is a sample ```terraform.tfvars.sample``` available as well.
3. Although each use case is somehow built around the previous one they are self-contained so you can deploy any of them at your will. The usual terraform commands will do the work. To provision this example, run the following from within this directory:

```terraform init ``` to get the plugins<br />
```terraform plan``` to see the infrastructure plan<br />
```terraform apply``` to apply the infrastructure build<br />
```terraform destroy``` to destroy the built infrastructure<br />

It will take a few minutes. When complete, you should see an output stating the command completed successfully, a list of the created resources.
The Output will look like following
```

Outputs:

id = "projects/my-project/datasets/dataset_name"
keyring = {
  "id" = "projects/my-project/locations/us-east4/keyRings/may-bq-keyring-"
  "location" = "us-east4"
  "name" = "may-bq-keyring-8"
  "project" = "my-project"
  "timeouts" = null /* object */
}
materialized_view_ids = {}
materialized_views = {}
self_link = "https://bigquery.googleapis.com/bigquery/v2/projects/my-project/datasets/dataset_name"
table_ids = {}
tables = {}
view_ids = {}
views = {}
```
