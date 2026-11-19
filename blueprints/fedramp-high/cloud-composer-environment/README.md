# Cloud Composer

<!-- BEGIN TOC -->
- [Introduction of Cloud Composer](#introduction-of-cloud-composer)
- [Cloud Composer Blueprint](#cloud-composer-blueprint)
- [Disclaimer](#disclaimer)
- [Prerequisites](#prerequisites)
- [IAM bindings](#iam-bindings)
- [Customer-managed encryption key](#customer-managed-encryption-key)
- [Deployment Steps](#deployment-steps)
- [Verification of a successful deployment](#verification-of-a-successful-deployment)
- [Variables](#variables)
- [Outputs](#outputs)
<!-- END TOC -->

## Introduction of Cloud Composer  
Based on the open source Apache Airflow project, the Cloud Composer provides infastructual support for worklows. It supports creating, scheduling, monitoring and managing workflows enviornments across clouds and data centers. 

## Cloud Composer Blueprint
This blueprint demonstrates how to deploy cloud composer on Google Cloud Platform (GCP). Directed Acryclic Graphs (DAGs) are created as a collection of tasks or workflows in a schedule. The purpose is ensuring the execution of tasks are completed in a particular order at the correct times, this is because each task can perform multiple functions. There are 4 main components: GKE Cluster, Airflow Web Server, Airflow Database, Cloud Storage Bucket. The GKE Cluster is where the DAG's can be triggered to run automatically in the existing workflow sequence, as a response or manually. In the Cloud Composer's core, the environment, the composer components run instances. The Airflow Web Server is a log to monitor progress of the workflows, the Database stores long term details of the flow. Finally the Cloud storage bucket, stores access to files of the flow. In order for there to be a flow in the access of files, Connections provide access to each of the various services, and hooks will provide access with other external services through the connections. Uploaded DAG's are sent to the composer environment where each individual tasks is executed by leveraging connections and hooks to interact with other systems. 

## Disclaimer 
The present GCP Terraform Module in this project is set up and intended to be implemented in a FEDRAMP High environment using the Assured Workloads within the Google Cloud Platform (GCP) organization. For Cloud Composer, the core components must be placed directly into the specific network area. The main project must have access/permission from the Shared VPC owner to build in the network or there will be a failed deployment. For a successful deployment, run time is around 25 minutes and destroying it will take around 8 minutes.

## Prerequisites
1. Service Account User role (roles/iam.serviceAccountUser) for deploying user.
2. The `compute.subnetworks.setIamPolicy` permission on the Shared VPC subnetwork for deploying user, because the blueprint grants a role on that subnetwork.

## IAM bindings
The blueprint grants each role on the narrowest resource it can confirm that Cloud Composer supports.

| role | principal | resource | rationale |
|---|---|---|---|
| `roles/composer.worker` | Environment service account | Main project | The permissions span several services, and Composer creates the resources they apply to while it creates the environment. |
| Role in `service_agent_version` | Composer service agent | Main project | The caller selects the role, so the blueprint cannot assume that it is grantable on the environment service account alone. |
| `roles/compute.networkUser` | Composer service agent | Environment subnetwork | The role only needs to cover the subnetwork that the environment uses. |
| `roles/composer.sharedVpcAgent` | Composer service agent | Shared VPC host project | Private IP environments need the role on the host project, and it carries network-scoped permissions that a subnetwork binding cannot grant. |

## Customer-managed encryption key
Set the `kms_key_name` variable to encrypt the environment with a Cloud KMS key. The variable is optional. When it is unset, the environment uses Google-managed encryption and the blueprint creates no key grants.

- Create the key in the same region as the environment, which the `region` variable sets. Cloud Composer does not accept multi-regional or global keys.
- Set the key before the first apply. Cloud Composer accepts a key only when it creates an environment, so setting or changing `kms_key_name` on an existing environment makes Terraform destroy and recreate the environment.
- Do not unset `kms_key_name` on an encrypted environment. The environment stays encrypted with the key, but Terraform removes the key grants that the environment still needs.
- The blueprint grants the `roles/cloudkms.cryptoKeyEncrypterDecrypter` role on the key to the Cloud Composer service agent and the Cloud Storage service agent of the main project, and creates the environment after both grants. The grants are additive, so other members on the key keep their access.
- These two service agents are the ones that [Cloud Composer 3 requires](https://cloud.google.com/composer/docs/composer-3/configure-cmek-encryption). Cloud Composer 2 image versions need more grants, which the blueprint does not create.
- Give the identity that runs Terraform permission to change the IAM policy of the key, for example with the `roles/cloudkms.admin` role on the key, and enable the Cloud Storage API in the main project.
- Keep the key enabled. An environment becomes unusable and cannot be recovered when its key is disabled or destroyed.


## Deployment Steps
You should see this README and some terraform files.
1. Run cp terraform.tfvars.sample terraform.tfvars to copy the sample variables to your own tfvars file.

2. Update the variables as necessary in your tfvars file.
3. To provision this example, run the following from within this directory:

```terraform init ```<br />
```terraform plan``` to see the infrastructure plan<br />
```terraform apply``` to apply the infrastructure build<br />
```terraform destroy``` to destroy the built infrastructure<br />

## Verification of a successful deployment
Use GCP console to verify if the resources have been created.
<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [composer_env_name](variables.tf#L16) | Name of the Composer environment. | <code>string</code> | ✓ |  |
| [main_project_id](variables.tf#L43) | Main project ID. | <code>string</code> | ✓ |  |
| [network_name](variables.tf#L48) | Full path to VPC. | <code>string</code> | ✓ |  |
| [network_project_id](variables.tf#L53) | The ID of the landing zone project where the VPC is. | <code>string</code> | ✓ |  |
| [subnetwork_name](variables.tf#L82) | The name of the existing subnetwork to use within the specified VPC network and region. | <code>string</code> | ✓ |  |
| [composer_version](variables.tf#L21) | Cloud composer version. | <code>string</code> |  | <code>&#34;composer-3-airflow-2&#34;</code> |
| [kms_key_name](variables.tf#L27) | Cloud KMS crypto key that encrypts the Composer environment, in the format projects/../locations/../keyRings/../cryptoKeys/... The key must be in the same region as the environment, and multi-regional or global keys are not supported. Leave null to use Google-managed encryption. Composer accepts a key only at creation, so setting or changing the key on an existing environment forces replacement of the environment. | <code>string</code> |  | <code>null</code> |
| [region](variables.tf#L58) | Google Cloud Region. | <code>string</code> |  | <code>&#34;us-east4&#34;</code> |
| [sa_account_id](variables.tf#L64) | Service account id. | <code>string</code> |  | <code>&#34;composer-env-account&#34;</code> |
| [sa_display_name](variables.tf#L70) | Service account display name. | <code>string</code> |  | <code>&#34;Service Account for Composer Environment&#34;</code> |
| [service_agent_version](variables.tf#L76) | Composer Service Agent version. This must correspond to Composer version. | <code>string</code> |  | <code>&#34;roles&#47;composer.ServiceAgentV3Ext&#34;</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [airflow_uri](outputs.tf#L15) | URI for Airflow. |  |
| [composer_id](outputs.tf#L20) | Cloud composer id. |  |
<!-- END TFDOC -->
