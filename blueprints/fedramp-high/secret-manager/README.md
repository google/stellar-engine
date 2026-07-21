# Secret Manager Blueprint
This blueprint demonstrates how to create Secrets on Google Cloud Platform (GCP) with Customer-Managed Encryption Keys (CMEK) using Cloud KMS.

## Introduction to Secret Manager
Secret Manager is a secure and convenient storage system for API keys, passwords, certificates, and other sensitive data.
- Easily follow the principle of least privilege with Secret Manager's Cloud IAM roles. You can grant individual permissions to secrets and separate the ability to manage secrets from the ability to access their data.
- Secret Manager enables simple life cycle management with first class versioning and the ability to pin requests to the latest version of a secret. You can use Cloud Functions to automate rotation.
- With Cloud Audit Logs integration, every interaction with Secret Manager generates an audit log. This integration makes meeting audit and compliance requirements easy.
- Secret data is immutable and most operations take place on secret versions. With Secret Manager, you can pin a secret to specific versions like "42" or floating aliases like "latest."

## Disclaimer
- The present GCP Terraform Module in this project is set up and intended to be implemented in either a FedRAMP-High or IL5 (Impact Level 5) environment using the Assured Workloads within the Google Cloud Platform (GCP) organization.
- Warning: This blueprint uses a bash script to update the secret versions so that Terraform doesn't store any secret data. If you chose to manage versions in Terraform, the data (the actual secret you want to protect) will be stored in the Terraform state in unencrypted form, accessible to any identity able to read or pull the state file.

## Requirements

These sections describe requirements for using this module.

### IAM
The following roles must be used to provision the resources of this module:

- Cloud KMS Admin: `roles/cloudkms.admin` or
- Owner: `roles/owner`

You also need the following role to manage secret versions:

- Secret Version Manager: `roles/secretmanager.secretVersionManager`

### APIs
A project with the following APIs enabled must be used to host the
resources of this module:

- Google Cloud Key Management Service: `cloudkms.googleapis.com`
- Google Cloud Secret Manager: `secretmanager.googleapis.com`
<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [main_project_id](variables.tf#L7) | The Project ID where the secrets will be created. | <code>string</code> | ✓ |  |
| [iam](variables.tf#L1) | IAM bindings in {SECRET => {ROLE => [MEMBERS]}} format. | <code>map&#40;map&#40;list&#40;string&#41;&#41;&#41;</code> |  | <code>&#123;&#125;</code> |
| [region](variables.tf#L12) | The Google Cloud region. | <code>string</code> |  | <code>&#34;us-east4&#34;</code> |
| [secrets](variables.tf#L18) | Map of secrets to manage, their locations and KMS keys in {LOCATION => KEY} format. | <code title="map&#40;object&#40;&#123;&#10;  location &#61; string &#35; A location is required for every secret&#10;  key      &#61; string &#35; A key is required for the location &#40;the key and secret must be in the same region&#41;&#10;&#125;&#41;&#41;">map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> |  | <code>&#123;&#125;</code> |
| [zone](variables.tf#L27) | The Google Cloud zone within the specified region. | <code>string</code> |  | <code>&#34;us-east4-a&#34;</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [ids](outputs.tf#L1) | Secret IDs. |  |
| [secrets](outputs.tf#L6) | Secret resources. |  |
<!-- END TFDOC -->
## Deployment Steps

You should see this README and some terraform files. There is also a bash script and a folder labeled "secrets" with some example secret files in it.
1. Copy the contents of the terraform.tfvars.sample file into your own terraform.tfvars file, then update the variables in this file. For reference update the following variables and associated properties:

- ```project_id```  with your GCP Project ID<br />
- ```region``` with the GCP Location <br />
- ```zone```  with the GCP zone within the region<br />
- ```secrets``` with the desired secret IDs to be created as well as their region and key <br />
-  ```iam```  with the desired iam roles assigned to each secret<br />

2. The usual terraform commands will be used to deploy the secrets. To provision this example, run the following from within this directory:

```terraform init ```<br />
```terraform plan``` to see the infrastructure plan<br />
```terraform apply``` to apply the infrastructure build<br />
```terraform destroy``` only if you wish to destroy the built infrastructure<br />

Verification of a successful deployment?
All of the secrets will be created and available through the Cloud Console in the Secret Manager. These secrets will simply have a region and a key associated with them. They will not have versions, which actually contain the secret data. In order to add versions to your newly created secrets, follow the remaining steps:

3. Go into the add_secret_versions.sh script and replace the PROJECT_ID variable with your Google Cloud project ID.
4. Replace the example SECRET_IDS array with your actual secret IDs.
5. Update the DATA_FILE path to point to the location where you store your secret data files. The example structure assumes you organize your secret data files by secret ID. Adapt this if necessary to match your file structure.
6. Run the script: ./add_secret_versions.sh

Troubleshooting: If the script doesn't run, try the following steps.
- Make it executable: chmod +x add_secret_versions.sh
- Authentication: Ensure that your gcloud CLI is authenticated with a service account or user that has the required permissions to create and manage secret versions.

You should see the message "Secret versions added successfully" after the script runs. If not, there may have been an error in your file structure/naming.
Now you can go into the Cloud Console and view your secrets again. This time they should have versions associated with them.

It is recommended to delete the local secret files after you run this script.


### GCE Option
If you would like to upload secrets from a GCE instance instead of doing it locally, you may do that as well.
Provision a GCE instance either manually through the Console, or in the Terraform:

<pre>
resource "google_service_account" "default" {
  account_id   = "my-custom-sa"
  display_name = "Custom SA for VM Instance"
}

resource "google_compute_instance" "default" {
  name         = "my-instance"
  machine_type = "n2-standard-2"
  zone         = "us-central1-a"

  tags = ["secret-uploader"]

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-11"
      labels = {
        my_label = "value"
      }
    }
  }

  // Local SSD disk
  scratch_disk {
    interface = "NVME"
  }

  network_interface {
    network = "default"

    access_config {
      // Ephemeral public IP
    }
  }

  service_account {
    # Google recommends custom service accounts that have cloud-platform scope and permissions granted via IAM Roles.
    email  = google_service_account.default.email
    scopes = ["cloud-platform"]
  }
}
</pre>

Within this VM, create the secret files containing your secret values and run the bash script to create the secret versions. Remember to delete the secret files and stop this GCE instance after you are done.