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

# Google Compute Shielded VM

<!-- BEGIN TOC -->
- [Introduction to Shielded VM](#introduction-to-shielded-vm)
- [Blueprint](#blueprint)
- [Prerequisite for Shielded VM](#prerequisite-for-shielded-vm)
- [Disclaimer](#disclaimer)
- [The Deployment Steps](#the-deployment-steps)
- [Verification of a successful deployment](#verification-of-a-successful-deployment)
- [Variables](#variables)
- [Outputs](#outputs)
<!-- END TOC -->

## Introduction to Shielded VM
Shielded VMs are virtual machines (VMs) on Google Cloud hardened by a set of security controls that help defend against rootkits and bootkits. Using Shielded VMs helps protect enterprise workloads from threats like remote attacks, privilege escalation, and malicious insiders. Shielded VMs leverage advanced platform security capabilities such as secure and measured boot, a virtual trusted platform module (vTPM), UEFI firmware, and integrity monitoring.

1. Enforce the Best Practices for the Shielded VM to be Enable Secure Boot, Enable VTPM, Monitoring
```
    enable_secure_boot          = true
    enable_vtpm                 = true
    enable_integrity_monitoring = true

```
2. Enable the Customer-Managed Encryption Keys (CMEK) Cloud KMS for Google Compute Engine and Disk
3.  The IL5 Requirements as of the creation of the project the region of deployment to US Only for example in us-east4 and us-central1

## Blueprint
This blueprint contains all the necessary Terraform modules to build and deploy a Shielded virtual machines (VMs) on Google Cloud.

## Prerequisite for Shielded VM
1. The Principal (user or group) must have Cloud KMS Admin permission at the GCP Level.
2. Have access to the GCP Project ID
3.  You will need an existing [project](https://cloud.google.com/resource-manager/docs/creating-managing-projects) with [billing enabled](https://cloud.google.com/billing/docs/how-to/modify-project) and a user with the “Project owner” [IAM](https://cloud.google.com/iam) role on that project. __Note__: to grant a user a role, take a look at the [Granting and Revoking Access](https://cloud.google.com/iam/docs/granting-changing-revoking-access#grant-single-role) documentation.

## Disclaimer
- The present GCP Terraform Module in this project is set up and intended to be implemented in either a FedRAMP-High or IL5 (Impact Level 5) environment using the Assured Workloads within the Google Cloud Platform (GCP) organization.
- Assured Workloads in both environments ensures that sensitive data and workloads in GCP adhere to the rigorous security standards mandated by the DoD, making it suitable for government agencies.

## The Deployment Steps
You should see this README and some terraform files.
1. Review and follow the [Prerequisite for Dataflow](#prerequisite-for-dataflow).
2. Run ```cp terraform.tfvars.sample terraform.tfvars``` to copy the sample variables to your own tfvars file.
3. Update the variables as necessary in your tfvars file.

- ```main_project_id``` with your main GCP Project ID.<br />
- ```core_project_id``` with your core GCP Project ID.<br />
- ```network_project_id``` with your network GCP Project ID.<br />
- ```region``` with the region to deploy the Shielded VM to.<br />
- ```zone``` with the zone to deploy the Shielded VM to.<br />
- ```instance_name``` with the name of the Shielded VM instance.<br />
- ```instance_type``` with the type of instance for the Shielded VM.<br />
- ```disksize``` with the size of the data disk for the Shielded VM.<br />
- ```network_name``` with the name of the VPC network.<br />
- ```subnetwork_name``` with the name of the VPC subnetwork.<br />
- ```source_ranges_allowed``` with the source ranges allowed for the firewall rule.<br />
- ```allowed_firewall_ports``` with the ports to allow through the firewall rule.<br />
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
The apply will take about 1 minute to complete. The Shielded VM be deployed in the main project. To see the Shielded VM, browse to the [Compute Engine Instances](https://console.cloud.google.com/compute/instances) page. Select the VM. Scroll down to the "Security and access" block to see the "Shielded VM" options. Each option (Secure Boot, vTPM and Integrity Monitoring) will be set to ```On```. Additionally, both the boot disk and additional disk should list ```Customer-managed``` under "Encryption". Clicking on either disk will bring you to the "Manage disk" page. Here you will see the Key name for your KMS key.

<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [allowed_firewall_ports](variables.tf#L17) | The list of the Allowed Ports. | <code>list&#40;any&#41;</code> | ✓ |  |
| [compute_service_account_id](variables.tf#L23) | The Service Account for Compute Engine. | <code>string</code> | ✓ |  |
| [core_project_id](variables.tf#L29) | Core Project ID. | <code>string</code> | ✓ |  |
| [kms_key_name](variables.tf#L53) | The full self-link (projects/../locations/../cryptoKeys/..) of the existing KMS key to use for encryption. | <code>string</code> | ✓ |  |
| [kms_keyring_name](variables.tf#L58) | Keyring attributes. | <code>string</code> | ✓ |  |
| [main_project_id](variables.tf#L63) | Project ID. | <code>string</code> | ✓ |  |
| [network_name](variables.tf#L68) | The name of the VPC. | <code>string</code> | ✓ |  |
| [network_project_id](variables.tf#L73) | Project that the Compute Engine VPC is located. | <code>string</code> | ✓ |  |
| [source_ranges_allowed](variables.tf#L84) | The List of the source IP CIDR range allowed to connect to the Shieled Compute VM. | <code>list&#40;any&#41;</code> | ✓ |  |
| [subnetwork_name](variables.tf#L90) | The name of the subnet. | <code>string</code> | ✓ |  |
| [disksize](variables.tf#L34) | Provide the Size of the size in GB. | <code>number</code> |  | <code>40</code> |
| [instance_name](variables.tf#L40) | Provide the name of the Shielded Compute VM. | <code>string</code> |  | <code>&#34;shieled-vm-inst&#34;</code> |
| [instance_type](variables.tf#L46) | The Machine Type for the Shielded Compute VM. | <code>string</code> |  | <code>&#34;e2-micro&#34;</code> |
| [region](variables.tf#L78) | Region of the Shielded Compute VM. | <code>string</code> |  | <code>&#34;us-east4&#34;</code> |
| [zone](variables.tf#L95) | Zone of the Shielded Compute VM us-east4-c , us-east4-a, us-east4-b. | <code>string</code> |  | <code>&#34;us-east4-c&#34;</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [shielded-vm-instance](outputs.tf#L17) | Instance resource. | ✓ |
| [shielded-vm-instance-id](outputs.tf#L23) | Fully qualified instance id. |  |
| [shielded-vm-internal_ip](outputs.tf#L28) | Instance main interface internal IP address. |  |
| [shielded-vm-internal_ips](outputs.tf#L33) | Instance interfaces internal IP addresses. |  |
| [shielded-vm-service_account](outputs.tf#L38) | Service account resource. |  |
| [shielded-vm-service_account_email](outputs.tf#L43) | Service account email. |  |
<!-- END TFDOC -->
