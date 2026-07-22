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

# Optional Shared Services Template — Active Directory Domain Controllers

This reference template deploys optional high-availability Windows Server Domain Controllers (DCs) on Google Cloud Platform (GCP). This infrastructure extends an existing identity perimeter into GCP, acting as a replication partner to an existing on-premises or multi-cloud Active Directory environment.

> [!NOTE]
> This is an **optional reference template**. It is fully decoupled from the core landing zone (Stages 0–5) and can be adapted or omitted based on your identity architecture.

## Architecture Overview
The configuration is designed to satisfy strict DoD Impact Level 5 (IL5) and DISA STIG compliance requirements while ensuring high availability for authentication services. 

**High Availability**: 
Two Windows Server Compute Engine instances are deployed across separate availability zones (-a and -b) within your chosen region.  

**Static Internal Networking**: 
Fixed internal IP addresses are reserved before VM creation using the net-address core module. These IPs must be provided to your Azure AD administration team to pre-stage AD Sites and Services. 

**Data Disks Segmentation**: 
The Active Directory database (NTDS.dit) and SYSVOL logs are mapped to a secondary persistent SSD (pd-ssd). The auto_delete = false flag protects this directory from an accidental teardown. 

**DoD Hardening and CMEK**: 
Computes utilize Shielded VM configurations (Secure Boot, vTPM, Integrity Monitoring) and Customer-Managed Encryption Keys (CMEK) via Cloud KMS to comply with IL5 organizational constraints. 

**Network Isolation**:
Internet egress paths like Cloud NAT are bypassed entirely. Internal APIs securely process logs or monitor platforms using Private Google Access.

## Deployment Instructions
1. Preparing the terraform.tfvars fileCopy the provided sample file to your active local sheet:
```
cp terraform.tfvars.sample terraform.tfvars
```
Fill out your required project IDs, VPC network strings, and the Azure DC IPs. To fetch your active ad service CMEK encryption key reference from your previous networking stage, run:
```
gcloud storage cat gs://<your-tf-state-outputs-bucket>/tfvars/3-networking.auto.tfvars.json | jq -r '.kms_keys["us-east4"].ad'
```
2. Execution PipelineInitialize your backend space and execute a dry-run plan to verify structural dependencies hold:
```
terraform init
terraform plan
```
If your deployment matches compliance validations, execute the apply 
```
terraform apply
```

## Post-Deployment Verification
Once `terraform apply` completes successfully, the infrastructure engineer must coordinate with the identity team to execute the following validation steps:

### Step 1: Connecting to DCs
1. Open a terminal and run `gcloud auth login` to authenticate.
2. Run `gcloud compute start-iap-tunnel DC_NAME 3389 --local-host-port=127.0.0.1:PORT --zone=DC_ZONE --project=SHARED_SERVICES_PROJECT`, this will create an IAP tunnel through the bastion host to 1 of the DC servers. NOTE: Select a port from the dynamic/private port range (49152-65535)
3. Open an RDP client and create a new connection. Enter the following info then save the connection:
```
PC name: 127.0.0.1:PORT
Credentials: .\gcpadmin
```
4. If the servers just deployed, wait about 5 minutes then try to connect. If it has been longer than 5 minutes, then you can connect immediately.
5. In the Shared Services project, go to Secret Manager and grab the password from `ad-initial-boot-password`.
6. Enter the password at the prompt and sign in.


### Step 2: Subnet Staging in AD Sites and Services
1. Open **Active Directory Sites and Services** (`dssite.msc`) from a management workstation.
2. Create a new Site object named `GCP-Region-Shared-Services` (or your local naming baseline).
3. Right-click **Subnets** -> **New Subnet**. 
4. Enter your GCP subnetwork CIDR footprint (e.g., matching your deployed `var.subnetwork` range) and link it directly to the new GCP Site object.

### Step 3: Run Active Directory Replica Promotion
Execute your target domain promotion path on the new GCP Windows VMs (either via an automated Offline Domain Join blob loop file or by utilizing `Install-ADDSDomainController` targeting the Azure cross-cloud IP addresses).

### Step 4: Verify High-Availability Replication Topology
Log into your new GCP Domain Controllers via an approved secure access path, open an administrative PowerShell terminal, and run:
```
repadmin /showrepl
```
<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [domain_controllers](variables.tf#L19) | Detailed topology map of the target domain controllers. | <code title="map&#40;object&#40;&#123;&#10;  region     &#61; string&#10;  zone       &#61; string&#10;  subnetwork &#61; string&#10;&#125;&#41;&#41;">map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> | ✓ |  |
| [gcp_ntp_relay_ip](variables.tf#L28) | The internal IP address of the local GCP NTP Relay server that the DCs will sync time against. | <code>string</code> | ✓ |  |
| [hub_project_id](variables.tf#L33) | The GCP project ID where Domain Controller resources will be deployed. Must be the project that owns the VPC (the Security Host Project), since Cloud Router, Cloud NAT, and firewall rules cannot cross-project reference networks. | <code>string</code> | ✓ |  |
| [network](variables.tf#L44) | Self-link of the VPC network to attach Domain Controller VMs to. | <code>string</code> | ✓ |  |
| [shared_services_project_id](variables.tf#L59) | The GCP project ID where Domain Controller resources will be deployed. | <code>string</code> | ✓ |  |
| [boot_disk_image](variables.tf#L1) | Boot disk image for Domain Controller VMs. Must be an approved, hardened Windows Server image (e.g., Windows Server 2022 Datacenter) meeting DISA STIG baselines. | <code>string</code> |  | <code>&#34;projects&#47;windows-cloud&#47;global&#47;images&#47;family&#47;windows-2022&#34;</code> |
| [boot_disk_size](variables.tf#L7) | Boot disk size in GB for Domain Controller VMs. Must be at least as large as the boot image (100 GB recommended for Windows Server system files and updates). | <code>number</code> |  | <code>100</code> |
| [data_disk_size](variables.tf#L13) | Size in GB for the secondary persistent disk dedicated to the Active Directory database (NTDS) and SYSVOL logs. | <code>number</code> |  | <code>50</code> |
| [machine_type](variables.tf#L38) | Machine type for Domain r VMs. n2-standard-2 is sufficient for basic AD workloads. Change to n2-standard-4 for a larger VM. | <code>string</code> |  | <code>&#34;n2-standard-2&#34;</code> |
| [prefix](variables.tf#L49) | Prefix applied to resource names for org-level naming consistency (e.g. 'da1'). Set to null to disable prefixing. | <code>string</code> |  | <code>null</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [domain_controller_ips](outputs.tf#L1) | The static internal IP addresses reserved and assigned to the GCP Domain Controllers. Hand these to the Azure AD team for Site-and-Services configuration. |  |
| [domain_controller_names](outputs.tf#L9) | The exact names of the provisioned Compute Engine instances. |  |
| [security_compliance](outputs.tf#L14) | A snapshot of the active security features verified at deployment time. |  |
| [service_account_email](outputs.tf#L23) | The dedicated, least-privilege service account email assigned to the DCs. |  |
<!-- END TFDOC -->
