Copyright 2023 Google LLC

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

## Dataflow

<!-- BEGIN TOC -->
- [Introduction Dataflow](#introduction-dataflow)
- [Blueprint](#blueprint)
- [Prerequisite for Dataflow](#prerequisite-for-dataflow)
- [Disclaimer](#disclaimer)
- [The Deployment Steps](#the-deployment-steps)
- [Verification of a successful deployment](#verification-of-a-successful-deployment)
- [Notes](#notes)
- [Variables](#variables)
- [Outputs](#outputs)
<!-- END TOC -->

## Introduction Dataflow
Dataflow is a Google Cloud service that provides unified stream and batch data processing at scale. Use Dataflow to create data pipelines that read from one or more sources, transform the data, and write the data to a destination.

Typical use cases for Dataflow include the following:

* Data movement: Ingesting data or replicating data across subsystems.
* ETL (extract-transform-load) workflows that ingest data into a data warehouse such as BigQuery.
* Powering BI dashboards.
* Applying ML in real time to streaming data.
* Processing sensor data or log data at scale.

## Blueprint
- This blueprint demonstrates how to deploy a Dataflow job and the related Google Cloud infrastructure. It ensures that the Dataflow API is enabled, creates a Cloud Storage Bucket to store files in, deploys a firewall rule for the Dataflow job's needs and launches the Dataflow job.
- This blueprint deploys the WordCount Example Pipeline. It will run the pipeline against Shakespeare's King Lear Dataflow sample. Once complete, it will send the output from the pipeline to the Cloud Storage Bucket that is created in this blueprint.

## Prerequisite for Dataflow
1. Have access to the GCP Project ID.
2. You will need an existing [project](https://cloud.google.com/resource-manager/docs/creating-managing-projects) with [billing enabled](https://cloud.google.com/billing/docs/how-to/modify-project) and a user with the “Project owner” [IAM](https://cloud.google.com/iam) role on that project.
3.  __Note__: to grant a user a role, take a look at the [Granting and Revoking Access](https://cloud.google.com/iam/docs/granting-changing-revoking-access#grant-single-role) documentation.

## Disclaimer
- The present GCP Terraform Module in this project is set up and intended to be implemented in an FedRAMP-High or IL5 (Impact Level 5) environment using the Assured Workloads within the Google Cloud Platform (GCP) organization.
- An Assured Workloads in both environments ensures that sensitive data and workloads in GCP adhere to the rigorous security standards mandated by the DoD, making it suitable for government agencies.

## The Deployment Steps
You should see this README and some terraform files.
1. Review and follow the [Prerequisite for Dataflow](#prerequisite-for-dataflow).
2. Run ```cp terraform.tfvars.sample terraform.tfvars``` to copy the sample variables to your own tfvars file.
3. Update the variables as necessary in your tfvars file.

- ```main_project_id``` with your main GCP Project ID.<br />
- ```core_project_id``` with your core GCP Project ID.<br />
- ```network_project_id``` with your network GCP Project ID.<br />
- ```prefix``` with a prefix for all of the resources.<br />
- ```storage_class``` with the storage class to assign to the Cloud Storage Bucket.<br />
- ```dataflow_name``` with the name of the Dataflow project.<br />
- ```zone``` with the zone to deploy the Dataflow project to.<br />
- ```bucket_name``` with the name for the bucket. This will be combined with the prefix to create the full bucket name.<br />
- ```template_gcs_path``` with the path to the Dataflow job template.<br />
- ```parameters``` with a key/value pair. This is specific to the template.<br />
- ```inputFile``` with the name of the file to pass into the Dataflow pipeline.<br />
- ```output``` with the location for the output from the Dataflow pipeline.<br />
- ```network_name``` with the name of the VPC network.<br />
- ```subnetwork_name``` with the name of the VPC subnetwork.<br />
- ```firewall_name``` with the name for the firewall rule.<br />
- ```allowed_source_ranges``` with the allowed source ranges for the firewall rule.<br />
- ```kms_keyring_name``` with the name of the KMS keyring.<br />
- ```kms_key_name``` with the name of the KMS key to be used within the KMS keyring.<br />

4. Run the following Terraform commands and type "yes" when prompted:

```bash
terraform init
terraform plan
terraform apply
terraform destroy
```

## Verification of a successful deployment
The apply will take about 30 seconds to a minute to complete. The Dataflow job will be deployed in the main project. It will take about 3-4 minutes to the job to complete. To see the status of the Dataflow job, go to [Dataflow](https://console.cloud.google.com/dataflow) and look for the latest instance of your dataflow_name. Once it completes, browse to the [Cloud Storage Bucket](https://console.cloud.google.com/storage/browser) and open the bucket that matches your ```prefix-bucket_name```. There will be a folder with the same name set as ```output``` that will contain the output of the Dataflow job.
Once the job completes, any additional applies will create a new Dataflow job with the same name rather than re-run the existing Dataflow.

## Notes
The Apache Beam SDK for Java has a warning about a bug in the latest version as of this blueprint (2.64.0).
<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [allowed_source_ranges](variables.tf#L23) | These are the allowed source ranges. | <code>list&#40;string&#41;</code> | ✓ |  |
| [bucket_name](variables.tf#L28) | This is the name of the bucket. | <code>string</code> | ✓ |  |
| [core_project_id](variables.tf#L33) | Core Project ID. | <code>string</code> | ✓ |  |
| [dataflow_name](variables.tf#L38) | Name of the Dataflow project. | <code>string</code> | ✓ |  |
| [firewall_name](variables.tf#L43) | The firewall name. | <code>string</code> | ✓ |  |
| [kms_key_name](variables.tf#L48) | The full self-link (projects/../locations/../cryptoKeys/..) of the existing KMS key to use for encryption. | <code>string</code> | ✓ |  |
| [kms_keyring_name](variables.tf#L53) | Keyring attributes. | <code>string</code> | ✓ |  |
| [main_project_id](variables.tf#L58) | The ID of the project in which to provision resources. | <code>string</code> | ✓ |  |
| [network_name](variables.tf#L63) | The network name. | <code>string</code> | ✓ |  |
| [network_project_id](variables.tf#L68) | Project that the Compute Engine VPC is located. | <code>string</code> | ✓ |  |
| [parameters](variables.tf#L73) | Dataflow Parameters. | <code>map&#40;string&#41;</code> | ✓ |  |
| [prefix](variables.tf#L78) | This is the prefix for all resources. | <code>string</code> | ✓ |  |
| [storage_class](variables.tf#L89) | This is the storage class of the storage bucket. | <code>string</code> | ✓ |  |
| [subnetwork_name](variables.tf#L94) | The subnet name. | <code>string</code> | ✓ |  |
| [template_gcs_path](variables.tf#L99) | This is the template path of the dataflow job. | <code>string</code> | ✓ |  |
| [allowed_firewall_ports](variables.tf#L17) | The allowed ports for the firewall. Dataflow requires 12345 and 12346. | <code>list&#40;string&#41;</code> |  | <code>&#91;12345, 12346&#93;</code> |
| [region](variables.tf#L83) | The region in which to provision resources. | <code>string</code> |  | <code>&#34;us-east4&#34;</code> |
| [zone](variables.tf#L104) | This is the name of the zone. | <code>string</code> |  | <code>&#34;us-east4&#34;</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [dataflow-job](outputs.tf#L1) | Dataflow job. |  |
| [gcs-bucket](outputs.tf#L6) | GCS Bucket. |  |
<!-- END TFDOC -->
