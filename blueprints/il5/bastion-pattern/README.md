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

## Bastion Pattern

<!-- BEGIN TOC -->
- [Introduction Bastion Pattern (Bastion Pattern Project)](#introduction-bastion-pattern-bastion-pattern-project)
- [Blueprint](#blueprint)
- [Disclaimer](#disclaimer)
- [Pre-requisite for Bastion Pattern Project (Bastion Pattern Project)](#pre-requisite-for-bastion-pattern-project-bastion-pattern-project)
- [How to  deploy the Terraform Code. The Deployment Steps](#how-to-deploy-the-terraform-code-the-deployment-steps)
- [How to connect to the Bastion Host](#how-to-connect-to-the-bastion-host)
- [Variables](#variables)
- [Outputs](#outputs)
<!--- END TOC -->

## Introduction Bastion Pattern (Bastion Pattern Project)
Bastions simplify security administration. The internal network can be configured to block all the internet-bound traffic. It only allows SSH communications with the bastion host. The bastion pattern grants authorized users access access to a private network from an external network such as internet. By following these steps, you will securely access multiple web services via the bastion host using port forwarding. This README section explains how to set up port forwarding for multiple ports and access the corresponding web services.
1. The IAM Permissions and Roles ```roles/cloudkms.cryptoKeyEncrypterDecrypter``` is assigned
Obtains access credentials for your user account via a web-based authorization flow. When this command completes successfully, it sets the active account in the current configuration to the account specified.

## Blueprint
This blueprint contains all the necessary Terraform modules to build and deploy a bastion VM on Google Cloud.

## Disclaimer
- The present GCP Terraform Module in this project is set up and intended to be implemented in either a FedRAMP-High or IL5 (Impact Level 5) environment using the Assured Workloads within the Google Cloud Platform (GCP) organization.
- An Assured Workloads in both environments ensures that sensitive data and workloads in GCP adhere to the rigorous security standards mandated by the DoD, making it suitable for government agencies.

## Pre-requisite for Bastion Pattern Project (Bastion Pattern Project)
1. Have access to the GCP Project ID
2. You will need an existing [project](https://cloud.google.com/resource-manager/docs/creating-managing-projects) with [billing enabled](https://cloud.google.com/billing/docs/how-to/modify-project) and a user with the “Project owner” [IAM](https://cloud.google.com/iam) role on that project.
3. __Note__: to grant a user a role, take a look at the [Granting and Revoking Access](https://cloud.google.com/iam/docs/granting-changing-revoking-access#grant-single-role) documentation.

## How to deploy the Terraform Code. The Deployment Steps
You should see this README and some terraform files.
1. Update the Variables in the variables.tf and also the properties within the keys variables. For reference update the following variables and associated properties
2. There is a sample ```terraform.tfvars.sample``` available as well.
3. Although each use case is somehow built around the previous one they are self-contained so you can deploy any of them at your will. The usual terraform commands will do the work:

```bash
terraform init
terraform plan
terraform apply
```

It will take a few minutes. When complete, you should see an output stating the command completed successfully, a list of the created resources.

```bash
Apply complete! Resources: 6 added, 0 changed, 0 destroyed.

Outputs:

compute_service_account_email = "compute-engine-sa@xxxx-xxxx-xxxx-main-0.iam.gserviceaccount.com"
subnet_self_link              = "https://www.googleapis.com/compute/v1/projects/xxxx-xxxx-net-host/regions/us-east4/subnetworks/default-us-east4"
vpc_self_link                 = "https://www.googleapis.com/compute/v1/projects/xxxx-xxxx-net-host/global/networks/xxxx-spoke-0"
```

## How to connect to the Bastion Host
To access the web portal through the bastion host, follow these steps:

1. **Set the Active Project** :
```bash
gcloud config set project <your-project-id>
```

This command will configure the gcloud CLI to utilize the specified project for every subsequent command. Thus, you should replace your project ID of your project with the ID of your Google Cloud Platform project.

2. **SSH into the Bastion Host via Port Forwarding**:
Use the following command to create an SSH tunnel through the bastion host and set up port forwarding for multiple ports:
```
gcloud compute ssh <your-bastion-host-name> --zone <your-zone> --tunnel-through-iap --project <your-project-id> -- \
-L 8443:<ip-of-bastion>:<remote-port1> \
-L 8444:<ip-of-bastion>:<remote-port2>\
-L 8445:<ip-of-bastion>::<remote-port3>
```

For example, if you need to forward local ports 8443, 8444, and 8445 to remote ports 443, 8443, and 8444 on <ip-of-bastion>, respectively, you would use:
```bash
gcloud compute ssh management-bastion --zone us-east4-a --tunnel-through-iap --project example-prod-iac-core-0 -- \
-L 8443:192.168.1.10:443 \
-L 8444:192.168.1.10:8443 \
-L 8445:192.168.1.10:8444
```

In this example:
- -L 8443:192.168.1.10:443: Forwards local port 8443 to port 443 on the remote server.
- -L 8444:192.168.1.10:8443: Forwards local port 8444 to port 8443 on the remote server.
- -L 8445:192.168.1.10:8444: Forwards local port 8445 to port 8444 on the remote server.

3. **Access the Web Portals**:
Once the SSH tunnel is established, you can access the web services by navigating to these websites in your web browser:
- https://localhost:8443 for the service on remote port 443.
- https://localhost:8444 for the service on remote port 8443.
- https://localhost:8445 for the service on remote port 8444.
<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [allowed_firewall_ports](variables.tf#L17) | The allowed ports for the firewall. | <code>list&#40;string&#41;</code> | ✓ |  |
| [allowed_source_ranges](variables.tf#L22) | These are the allowed source ranges. | <code>list&#40;string&#41;</code> | ✓ |  |
| [compute_service_account_id](variables.tf#L27) | This is the compute service account id. | <code>string</code> | ✓ |  |
| [core_project_id](variables.tf#L32) | Core project ID. | <code>string</code> | ✓ |  |
| [disk_name](variables.tf#L37) | This is the disk name. | <code>string</code> | ✓ |  |
| [instance_name](variables.tf#L48) | This is the instance name. | <code>string</code> | ✓ |  |
| [kms_key_name](variables.tf#L59) | The full self-link (projects/../locations/../keyRings/../cryptoKeys/..) of the existing KMS key to use for disk encryption. | <code>string</code> | ✓ |  |
| [kms_keyring_name](variables.tf#L64) | Keyring attributes. | <code>string</code> | ✓ |  |
| [main_project_id](variables.tf#L69) | This is the ID of project. | <code>string</code> | ✓ |  |
| [network_name](variables.tf#L74) | VPC to use. | <code>string</code> | ✓ |  |
| [network_project_id](variables.tf#L79) | Project that the Compute Engine VPC is located. | <code>string</code> | ✓ |  |
| [region](variables.tf#L84) | GCP Region to deploy into. | <code>string</code> | ✓ |  |
| [subnetwork_name](variables.tf#L89) | Subnet to use. | <code>string</code> | ✓ |  |
| [zone](variables.tf#L94) | This is the zone of the instance. | <code>string</code> | ✓ |  |
| [image](variables.tf#L42) | Disk image. | <code>string</code> |  | <code>&#34;cos-cloud&#47;cos-stable&#34;</code> |
| [instance_type](variables.tf#L53) | Instance type. | <code>string</code> |  | <code>&#34;n2d-standard-2&#34;</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [compute_service_account_email](outputs.tf#L17) | The email of the compute service account. |  |
| [subnet_self_link](outputs.tf#L22) | The self link of the subnet. |  |
| [vpc_self_link](outputs.tf#L27) | The self link of the VPC. |  |
<!-- END TFDOC -->
