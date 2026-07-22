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

# Google Cloud Key Management Service (Cloud KMS) Project
This blueprint contains all the necessary Terraform modules to build and deploy a Cloud Key Management: Manage encryption keys on Google Cloud.


## Introduction Google Cloud Key Management Service (Cloud KMS)
Google Cloud Key Management Service (Cloud KMS) lets you create and manage encryption keys for use in compatible Google Cloud services and in your own applications. Using Cloud KMS, you can Generate software or hardware keys, import existing keys into Cloud KMS, or link external keys in your compatible external key management (EKM) system. Allows managing a keyring, zero or more keys in the keyring, and IAM role bindings on individual keys.

1. The Rotation Period ``` rotation_period ``` is set to 90 days,
2. The Destroy Scheduled Duration is ``` destroy_scheduled_duration ``` is set to 30 days
3. The IAM Permissions and Roles ```roles/cloudkms.cryptoKeyEncrypterDecrypter``` is assigned

## Pre-requisite for Google Cloud Key Management Service (Cloud KMS)
1. The Principal (user or group) must have Google Cloud Key Management Service (Cloud KMS) Admin permission at the GCP Level.
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
| [email](variables.tf#L17) | Email address of the user. | <code>string</code> | ✓ |  |
| [group_email](variables.tf#L23) | An email address that represents a Google group. For example, admins@example.com. | <code>string</code> | ✓ |  |
| [kms_keyring_name](variables.tf#L85) | Keyring attributes. | <code title="object&#40;&#123;&#10;  location &#61; string&#10;  name     &#61; string&#10;&#125;&#41;">object&#40;&#123;&#8230;&#125;&#41;</code> | ✓ |  |
| [main_project_id](variables.tf#L93) | Project ID. | <code>string</code> | ✓ |  |
| [region](variables.tf#L99) | GCP Region to deploy into. | <code>string</code> | ✓ |  |
| [kms_key_names](variables.tf#L29) | Key names and base attributes. Set attributes to null if not needed. | <code title="map&#40;object&#40;&#123;&#10;  destroy_scheduled_duration    &#61; optional&#40;string&#41;&#10;  rotation_period               &#61; optional&#40;string, &#34;7776000s&#34;&#41; &#35; CIS Compliance Benchmark 1.10&#10;  labels                        &#61; optional&#40;map&#40;string&#41;&#41;&#10;  purpose                       &#61; optional&#40;string, &#34;ENCRYPT_DECRYPT&#34;&#41;&#10;  skip_initial_version_creation &#61; optional&#40;bool, false&#41;&#10;  version_template &#61; optional&#40;object&#40;&#123;&#10;    algorithm        &#61; string&#10;    protection_level &#61; optional&#40;string, &#34;HSM&#34;&#41;&#10;  &#125;&#41;&#41;&#10;&#10;&#10;  iam &#61; optional&#40;map&#40;list&#40;string&#41;&#41;, &#123;&#125;&#41;&#10;  iam_bindings &#61; optional&#40;map&#40;object&#40;&#123;&#10;    members &#61; list&#40;string&#41;&#10;    role    &#61; string&#10;    condition &#61; optional&#40;object&#40;&#123;&#10;      expression  &#61; string&#10;      title       &#61; string&#10;      description &#61; optional&#40;string&#41;&#10;    &#125;&#41;&#41;&#10;  &#125;&#41;&#41;, &#123;&#125;&#41;&#10;  iam_bindings_additive &#61; optional&#40;map&#40;object&#40;&#123;&#10;    member &#61; string&#10;    role   &#61; string&#10;    condition &#61; optional&#40;object&#40;&#123;&#10;      expression  &#61; string&#10;      title       &#61; string&#10;      description &#61; optional&#40;string&#41;&#10;    &#125;&#41;&#41;&#10;  &#125;&#41;&#41;, &#123;&#125;&#41;&#10;&#125;&#41;&#41;">map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> |  | <code title="&#123;&#10;  &#34;update-the-keys-name&#34; &#61; &#123;&#10;    rotation_period            &#61; &#34;7776000s&#34;&#10;    destroy_scheduled_duration &#61; &#34;2592000s&#34;&#10;    labels &#61; &#123;&#10;      &#34;team&#34; &#61; &#34;update-the-team-label-here&#34;&#10;    &#125;&#10;    version_template &#61; &#123;&#10;      algorithm        &#61; &#34;GOOGLE_SYMMETRIC_ENCRYPTION&#34;&#10;      protection_level &#61; &#34;HSM&#34;&#10;    &#125;&#10;    iam &#61; &#123;&#10;      &#34;roles&#47;cloudkms.cryptoKeyEncrypterDecrypter&#34; &#61; &#91;&#34;user:update-the-email-address-here&#34;, &#34;group:update-group-email-address-here&#34;&#93;&#10;    &#125;&#10;    lifecycle &#61; &#123;&#10;      prevent_destroy &#61; true&#10;    &#125;&#10;  &#125;&#10;&#10;&#10;&#125;">&#123;&#8230;&#125;</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [keyring-id](outputs.tf#L17) | Fully qualified keyring id. |  |
| [keyring-location](outputs.tf#L22) | Keyring location. |  |
| [keyring-name](outputs.tf#L27) | Keyring name. |  |
| [keyring-resource](outputs.tf#L32) | Keyring resource. |  |
| [keyrings-keys](outputs.tf#L37) | Key resources. |  |
| [qualified_key_ids](outputs.tf#L42) | Fully qualified key ids. |  |
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
    name     = "may6v3-keyring"
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

Apply complete! Resources: 4 added, 0 changed, 0 destroyed.

Outputs:

keyring-id = "projects/project-id-123/locations/us-east4/keyRings/name-of-the-keyring"
keyring-location = "us-east4"
keyring-name = "name-of-the-keyring"
keyring-resource = {
  "id" = "projects/project-id-123/locations/us-east4/keyRings/name-of-the-keyring"
  "location" = "us-east4"
  "name" = "name-of-the-keyring"
  "project" = "project-id-123"
  "timeouts" = null /* object */
}
keyrings-keys = {
  "keyrings-key" = {
    "crypto_key_backend" = ""
    "destroy_scheduled_duration" = "2592000s"
    "effective_labels" = tomap({
      "team" = "dino-runner"
    })
    "id" = "projects/project-id-123/locations/us-east4/keyRings/name-of-the-keyring/cryptoKeys/keyrings-runner-key"
    "import_only" = false
    "key_ring" = "projects/project-id-123/locations/us-east4/keyRings/name-of-the-keyring"
    "labels" = tomap({
      "team" = "dino-runner"
    })
    "name" = "keyrings-runner-key"
    "primary" = tolist([
      {
        "name" = "projects/project-id-123/locations/us-east4/keyRings/name-of-the-keyring/cryptoKeys/keyrings-runner-key/cryptoKeyVersions/1"
        "state" = "ENABLED"
      },
    ])
    "purpose" = "ENCRYPT_DECRYPT"
    "rotation_period" = "7776000s"
    "skip_initial_version_creation" = false
    "terraform_labels" = tomap({
      "team" = "dino-runner"
    })
    "timeouts" = null /* object */
    "version_template" = tolist([
      {
        "algorithm" = "GOOGLE_SYMMETRIC_ENCRYPTION"
        "protection_level" = "HSM"
      },
    ])
  }
}
qualified_key_ids = {
  "keyrings-runner-key" = "projects/project-id-123/locations/us-east4/keyRings/name-of-the-keyring/cryptoKeys/keyrings-runner-key"
}


```
