<!--
Copyright 2026 Google LLC

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
-->

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

CMEK allows you to encrypt your Bigtable data at rest using keys that you manage in Cloud KMS. This provides greater control over key lifecycle management, including key rotation and access control. This blueprint supports creating new KMS keys, using pre-existing keys, or not using any keys.

## Disclaimer
- The present GCP Terraform Module in this project is set up and intended to be implemented in a FEDRAMP High environment using the Assured Workloads within the Google Cloud Platform (GCP) organization.

## Deployment Steps

You should see this README and some terraform files.
1. Update the Variables in the variables.tf and also the properties within the keys variables. For reference update the following variables and associated properties

- ```project_id```  with your GCP Project ID<br />
-  ```instance_name```  with desired bigtable instance name<br />
- ```zone```  with the GCP Location<br />
- ```region``` with the GCP region inside of zone <br />
- ```cluster_id``` with the desired cluster ID to be created and deployed <br />


2. There is a sample ```terraform.tfvars.sample``` available as well.
3. Although each use case is somehow built around the previous one they are self-contained so you can deploy any of them at your will. The usual terraform commands will do the work. To provision this example, run the following from within this directory:

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
| [bigtable_service_account_id](variables.tf#L7) | The Service Account for Bigtable. | <code>string</code> | ✓ |  |
| [cluster_id](variables.tf#L12) | The Bigtable cluster ID. | <code>string</code> | ✓ |  |
| [core_project_id](variables.tf#L17) | Core project ID. | <code>string</code> | ✓ |  |
| [instance_name](variables.tf#L22) | Provide the name of the Bigtable. | <code>string</code> | ✓ |  |
| [kms_key_name](variables.tf#L27) | The Cloud KMS key for encryption. | <code>string</code> | ✓ |  |
| [kms_keyring_name](variables.tf#L32) | KMS Keyring. | <code>string</code> | ✓ |  |
| [main_project_id](variables.tf#L37) | Main project ID. | <code>string</code> | ✓ |  |
| [auto_delete](variables.tf#L1) | Persistent Disk auto delete options. | <code>bool</code> |  | <code>true</code> |
| [num_nodes](variables.tf#L42) | Number of nodes in the Bigtable cluster. | <code>number</code> |  | <code>1</code> |
| [region](variables.tf#L48) | Google Cloud Region. | <code>string</code> |  | <code>&#34;us-east4&#34;</code> |
| [storage_type](variables.tf#L54) | Either SSD or HDD. | <code>string</code> |  | <code>&#34;SSD&#34;</code> |
| [table](variables.tf#L60) | Table to create in the bigtable instance. Default is null. | <code title="map&#40;object&#40;&#123;&#10;  split_keys      &#61; optional&#40;list&#40;string&#41;&#41;&#10;  column_families &#61; map&#40;object&#40;&#123;&#125;&#41;&#41;&#10;&#125;&#41;&#41;">map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> |  | <code title="&#123;&#10;  &#34;Test&#34; &#61; &#123;&#10;    column_families &#61; &#123;&#125;&#10;  &#125;&#10;&#125;">&#123;&#8230;&#125;</code> |
| [zone](variables.tf#L73) | Google Cloud Zone. | <code>string</code> |  | <code>&#34;us-east4-a&#34;</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [bigtable_service_identity_email](outputs.tf#L1) | The email of the Bigtable Service Identity. |  |
| [bigtable_service_identity_uid](outputs.tf#L6) | The ID of the Bigtable Service Identity. |  |
| [cluster_info](outputs.tf#L11) | Information about the created Bigtable cluster. |  |
| [instance_name](outputs.tf#L21) | Bigtable instance name. |  |
| [table_info](outputs.tf#L26) | Information about the tables created (if any). |  |
<!-- END TFDOC -->
