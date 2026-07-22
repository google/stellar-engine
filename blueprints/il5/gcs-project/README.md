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

# Google Cloud Storage

<!-- BEGIN TOC -->
- [Introduction Google Cloud Storage](#introduction-google-cloud-storage)
- [Blueprint](#blueprint)
- [Pre-requisite for Google Cloud Storage](#pre-requisite-for-google-cloud-storage)
- [Disclaimer](#disclaimer)
- [The Deployment Steps](#the-deployment-steps)
- [Verification of a successful deployment](#verification-of-a-successful-deployment)
- [Variables](#variables)
<!-- END TOC -->

## Introduction Google Cloud Storage
Cloud Storage is a service for storing your objects in Google Cloud. An object is an immutable piece of data consisting of a file of any format. You store objects in containers called buckets.

All buckets are associated with a project, and you can group your projects under an organization. Each project, bucket, managed folder, and object in Google Cloud is a resource in Google Cloud, as are things such as Compute Engine instances.

After you create a project, you can create Cloud Storage buckets, upload objects to your buckets, and download objects from your buckets. You can also grant permissions to make your data accessible to principals you specify or accessible to everyone on the public internet.

## Blueprint
This blueprint contains all the necessary Terraform modules to build and deploy a Google Cloud Storage Bucket meeting the following requirements.

1. Enforce that all the GCP Buckets are ONLY Private with NO PUBLIC access.
```
public_access_prevention = "enforced"
```
2.  Enable Use Autoclass, set it to true.
```
autoclass { enabled = true }
```
3. Force Customer-Managed Encryption Keys (CMEK) Cloud KMS for Google Cloud Storage.
4. Region of deployment to US Only. For example in us-east4 and us-central1.

## Pre-requisite for Google Cloud Storage
1. The Principal (user or group) must have Cloud KMS Admin permission at the GCP Level.

## Disclaimer
- The present GCP Terraform Module in this project is set up and intended to be implemented in either a FedRAMP-High or IL5 (Impact Level 5) environment using the Assured Workloads within the Google Cloud Platform (GCP) organization.
- Assured Workloads in both environments ensures that sensitive data and workloads in GCP adhere to the rigorous security standards mandated by the DoD, making it suitable for government agencies.

## The Deployment Steps
You should see this README and some terraform files.
1. Review and follow the [Prerequisite for Google Cloud Storage](#pre-requisite-for-google-cloud-storage)
2. Run ```cp terraform.tfvars.sample terraform.tfvars``` to copy the sample variables to your own tfvars file.
3. Update the variables as necessary in your tfvars file.

- ```main_project_id``` with your main GCP Project ID.<br />
- ```core_project_id``` with your core GCP Project ID.<br />
- ```prefix``` with a prefix for the Google Cloud Storage Bucket.<br />
- ```bucket_name``` with the name for the bucket. This will be combined with the prefix to create the full bucket name.<br />
- ```region``` with the region to deploy the Google Cloud Storage Bucket.<br />
- ```autoclass``` with true to enable autoclass on the Google Cloud Storage Bucket.<br />
- ```storage_class``` with the Storage Class for the Google Cloud Storage Bucket. This must be set to STANDARD if autoclass is set to true.<br />
- ```kms_keyring_name``` with the name of the KMS keyring.<br />
- ```kms_key_name``` with the name of the KMS key to be used within the KMS keyring.<br />

4. Run the following Terraform commands and type "yes" when prompted

```bash
terraform init
terraform plan
terraform apply
terraform destroy
```

## Verification of a successful deployment
The apply will take about 10 seconds to deploy. The Google Cloud Stroage Bucket will be deployed in the main project. 
To see the bucket, browse to [Cloud Storage Bucket](https://console.cloud.google.com/storage/browser) and open the bucket that matches your ```prefix-bucket_name```.
<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [bucket-name](variables.tf#L24) | Bucket name suffix. | <code>string</code> | ✓ |  |
| [core_project_id](variables.tf#L29) | Core Project ID. | <code>string</code> | ✓ |  |
| [kms_key_name](variables.tf#L34) | The full self-link (projects/../locations/../cryptoKeys/..) of the existing KMS key to use for encryption. | <code>string</code> | ✓ |  |
| [kms_keyring_name](variables.tf#L39) | Keyring attributes. | <code>string</code> | ✓ |  |
| [main_project_id](variables.tf#L44) | Project ID. | <code>string</code> | ✓ |  |
| [retention_policy](variables.tf#L75) | Retention policy. | <code title="object&#40;&#123;&#10;  is_locked        &#61; bool&#10;  retention_period &#61; number&#10;&#125;&#41;&#10;&#10;&#10;default &#61; &#123;&#10;  is_locked        &#61; false &#35; Change to true if storing logs here for CIS Compliance Benchmark 2.3&#10;  retention_period &#61; 7776000&#10;&#125;">object&#40;&#123;&#8230;&#125;</code> | ✓ |  |
| [autoclass](variables.tf#L18) | Enable autoclass to automatically transition objects to appropriate storage classes based on their access pattern. If set to true, storage_class must be set to STANDARD. When set to true, All objects added to the bucket begin in Standard storage, even if a different storage class is specified in the request. | <code>bool</code> |  | <code>true</code> |
| [prefix](variables.tf#L49) | Optional prefix used to generate the bucket name. | <code>string</code> |  | <code>&#34;string&#34;</code> |
| [public_access_prevention](variables.tf#L59) | This provides the ability to toggle Public Access Prevention for the GCS Storage bucket. By settng this variable to enforced, the CIS Compliance Benchmark 5.1 control is satsified. | <code>string</code> |  | <code>&#34;enforced&#34;</code> |
| [region](variables.tf#L69) | Bucket region. | <code>string</code> |  | <code>&#34;us-east4&#34;</code> |
| [storage_class](variables.tf#L88) | Bucket storage class. | <code>string</code> |  | <code>&#34;STANDARD&#34;</code> |
| [uniform_bucket_level_access](variables.tf#L98) | This provides the ability to toggle Uniform Bucket Level Acess for the GCS Storage bucket. By settng this variable to true, the CIS Compliance Benchmark 5.2 control is satsified. | <code>bool</code> |  | <code>true</code> |
<!-- END TFDOC -->
