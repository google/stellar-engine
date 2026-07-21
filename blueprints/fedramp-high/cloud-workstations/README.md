# Cloud Workstations Blueprint
This blueprint demonstrates how to create Workstations on Google Cloud Platform (GCP) with Customer-Managed Encryption Keys (CMEK) using Cloud KMS.

<!-- BEGIN TOC -->
- [Introduction to Cloud Workstations](#introduction-to-cloud-workstations)
- [Disclaimer](#disclaimer)
- [Note](#note)
- [Deployment Steps](#deployment-steps)
- [Variables](#variables)
- [Outputs](#outputs)
<!-- END TOC -->

## Introduction to Cloud Workstations
Cloud Workstations provides preconfigured, customizable, and secure managed development environments on Google Cloud. Cloud Workstations is accessible through a browser-based IDE, from multiple local code editors (such as IntelliJ IDEA Ultimate or VS Code), or through SSH. Instead of manually setting up development environments, you can create a workstation configuration specifying your environment in a reproducible way.

## Disclaimer
- The present GCP Terraform Module in this project is set up and intended to be implemented in a FedRAMP-High environment using the Assured Workloads within the Google Cloud Platform (GCP) organization.

## Note
- You have a few options when selecting an image. Either don't set the ```image``` variable to use the default image, check out the list of [preconfigured base images](https://cloud.google.com/workstations/docs/preconfigured-base-images), or use artifact registry to specify your own custom image.
- When adding users to workstations, remember that users and groups with the Owner, Editor, Workstations Admin, or Workstations Creator roles on a parent resource (e.g. at the project level) will also be able to create workstations.
- If you need to delete the cluster or rerun ```terraform apply```, you must manually delete the workstation cluster, as ```terraform destroy``` currently has issues with nested resources.

## Deployment Steps

1. Copy the contents of the terraform.tfvars.sample file into your own terraform.tfvars file, then update the variables as necessary. 
2. The usual terraform commands will be used to deploy the secrets. To provision this example, run the following from within this directory:

```terraform init```<br />
```terraform plan``` to see the infrastructure plan<br />
```terraform apply``` to apply the infrastructure build<br />

3. Deploying the cluster will take ~20 minutes. To verify a successful deployment, check that the cluster, configuration, and all of your workstations were created. Then start a workstation and launch it to use the Web IDE.

<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [kms_key_name](variables.tf#L25) | The name of the kms key. | <code>string</code> | ✓ |  |
| [kms_keyring_name](variables.tf#L30) | The keyring of the kms key. | <code>string</code> | ✓ |  |
| [main_project_id](variables.tf#L41) | The Project ID where the workstations will be created. | <code>string</code> | ✓ |  |
| [network_name](variables.tf#L46) | The name of the network. | <code>string</code> | ✓ |  |
| [region](variables.tf#L57) | The Google Cloud region. | <code>string</code> | ✓ |  |
| [subnetwork_name](variables.tf#L62) | The name of the subnet. | <code>string</code> | ✓ |  |
| [workstations](variables.tf#L67) | The workstations that will be created based on the configuration. | <code title="map&#40;object&#40;&#123;&#10;  env   &#61; optional&#40;map&#40;string&#41;&#41;&#10;  users &#61; optional&#40;list&#40;string&#41;&#41;&#10;&#125;&#41;&#41;">map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> | ✓ |  |
| [cluster_id](variables.tf#L1) | The ID of the workstation cluster. | <code>string</code> |  | <code>&#34;example-workstation-cluster&#34;</code> |
| [config_id](variables.tf#L7) | The ID of the workstation configuration. | <code>string</code> |  | <code>&#34;example-workstation-config&#34;</code> |
| [core_project_id](variables.tf#L13) | The Project ID where the kms key is located. | <code>string</code> |  | <code>null</code> |
| [machine_type](variables.tf#L35) | Type of GCE machine for the workstation configuration. | <code>string</code> |  | <code>&#34;e2-standard-4&#34;</code> |
| [network_project_id](variables.tf#L51) | The ID of the landing zone project where the VPC is located. | <code>string</code> |  | <code>null</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [workstation_cluster](outputs.tf#L1) | The cluster that was created to host the workstations. |  |
| [workstation_config](outputs.tf#L6) | The workstation config that is used to create workstation instances. |  |
| [workstation_key_sa](outputs.tf#L11) | The service account that was created to use the KMS key. |  |
| [workstations](outputs.tf#L16) | The created workstation instances. |  |
<!-- END TFDOC -->
