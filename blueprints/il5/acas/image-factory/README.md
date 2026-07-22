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

# ACAS Image Factory

This Terraform blueprint provisions the **image building pipeline** for the ACAS solution. It creates an Artifact Registry YUM repository to store ACAS RPM packages and Cloud Build triggers that bake those RPMs into immutable, CMEK-encrypted Compute Engine Golden Images based on standard RHEL 8 or CIS STIG-hardened RHEL 8 base images from the GCP Marketplace.

> **Run this blueprint before `acas/deployment`.** The deployment blueprint boots VMs directly from the Golden Images produced here.

<!-- BEGIN TOC -->
- [Architecture](#architecture)
- [How it Works](#how-it-works)
- [Automated Workflow](#automated-workflow)
- [Variables](#variables)
- [Outputs](#outputs)
<!-- END TOC -->

## Architecture

```
DoD Patch Repository (CAC)
        ↓
  ACAS RPMs (.rpm)
        ↓
  Artifact Registry (YUM repo: acas-rpms)
        ↓
  Cloud Build trigger → ephemeral VM (RHEL 8 base)
        ↓          → dnf install <RPM>
        ↓          → stop VM, capture disk
        ↓
  Compute Engine Golden Image (CMEK encrypted)
        ↓
  acas/deployment consumes the image family
```

## How it Works

1. **Artifact Registry** hosts a private YUM repository (`acas-rpms`) where you upload ACAS `.rpm` files obtained from the DoD Patch Repository.
2. **Cloud Build** (`cloudbuild-scanner.yaml` / `cloudbuild-sc.yaml`) provisions an ephemeral RHEL 8 VM, configures it to pull from the Artifact Registry YUM repo, installs the ACAS RPM via `dnf`, stops the VM, and captures the disk as a named Compute Engine Image under the configured image family.
3. **The ephemeral VM is automatically deleted** after the image is captured to avoid ongoing compute costs.
4. The resulting image is available under the `acas-scanner-golden` / `acas-sc-golden` image family and is consumed by `acas/deployment`.

## Automated Workflow

After downloading the RPMs from [patches.csd.disa.mil](https://patches.csd.disa.mil), you no longer need to upload them manually.

1. Ensure that the `acas/image-factory/rpms/` directory exists (git ignored).
2. Move your downloaded RPMs into the `rpms/` directory.
3. Update `terraform.tfvars` to set `scanner_rpm_filename` (and/or `sc_rpm_filename`) to the exact names of the files you placed in the `rpms/` directory.
4. Initialize and apply Terraform:

```bash
terraform init
terraform apply
```

**Note:** Terraform uses a `local-exec` provisioner to automatically upload the RPM to Artifact Registry and then synchronously trigger the Cloud Build. Because it waits for the build to finish, **`terraform apply` will take 10-15 minutes** depending on the image.
<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [kms_key_name](variables.tf#L41) | Name of the KMS crypto key for encryption. | <code>string</code> | ✓ |  |
| [kms_keyring_name](variables.tf#L46) | Name of the KMS key ring used to encrypt images and Artifact Registry. | <code>string</code> | ✓ |  |
| [kms_project_id](variables.tf#L51) | Project ID where the KMS keyring resides. | <code>string</code> | ✓ |  |
| [network_name](variables.tf#L56) | VPC network to use for the image builder VM. | <code>string</code> | ✓ |  |
| [project_id](variables.tf#L67) | GCP project ID where the image factory resources will be created. | <code>string</code> | ✓ |  |
| [subnetwork_name](variables.tf#L102) | VPC subnetwork to use for the image builder VM. | <code>string</code> | ✓ |  |
| [artifact_registry_repo_id](variables.tf#L17) | Name/ID for the Artifact Registry YUM repository. | <code>string</code> |  | <code>&#34;acas-rpms&#34;</code> |
| [base_image](variables.tf#L23) | The base image to use as the foundation for Golden Images. Specify as 'projects/PROJECT/global/images/IMAGE' or 'projects/PROJECT/global/images/family/FAMILY'. | <code>string</code> |  | <code>&#34;projects&#47;rhel-cloud&#47;global&#47;images&#47;family&#47;rhel-8&#34;</code> |
| [build_sc_image](variables.tf#L29) | Whether to trigger the Cloud Build job for the SecurityCenter Golden Image. | <code>bool</code> |  | <code>false</code> |
| [build_scanner_image](variables.tf#L35) | Whether to trigger the Cloud Build job for the Nessus Scanner Golden Image. | <code>bool</code> |  | <code>true</code> |
| [network_project_id](variables.tf#L61) | Project ID that hosts the VPC network. Defaults to project_id. Set this when using a Shared VPC where the network lives in a different host project than the image factory. | <code>string</code> |  | <code>null</code> |
| [region](variables.tf#L72) | GCP region for regional resources (e.g., Artifact Registry repository). | <code>string</code> |  | <code>&#34;us-east4&#34;</code> |
| [sc_image_family](variables.tf#L78) | Image family name for the SecurityCenter Golden Image. | <code>string</code> |  | <code>&#34;acas-sc-golden&#34;</code> |
| [sc_rpm_filename](variables.tf#L84) | Filename of the SecurityCenter RPM as uploaded to Artifact Registry (e.g., SecurityCenter-6.8.0-el8.x86_64.rpm). | <code>string</code> |  | <code>null</code> |
| [scanner_image_family](variables.tf#L90) | Image family name for the Nessus Scanner Golden Image. | <code>string</code> |  | <code>&#34;acas-scanner-golden&#34;</code> |
| [scanner_rpm_filename](variables.tf#L96) | Filename of the Nessus Scanner RPM as uploaded to Artifact Registry (e.g., Nessus-10.12.0-el8.x86_64.rpm). | <code>string</code> |  | <code>null</code> |
| [zone](variables.tf#L107) | GCP zone where the image builder VM will run. | <code>string</code> |  | <code>&#34;us-east4-a&#34;</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [artifact_registry_id](outputs.tf#L17) | Artifact Registry repository resource ID. |  |
| [artifact_registry_repo_id](outputs.tf#L22) | Name/ID for the Artifact Registry YUM repository. |  |
| [artifact_registry_repository](outputs.tf#L27) | The full Artifact Registry repository URI. Upload ACAS RPMs here. |  |
| [base_image](outputs.tf#L32) | The base image to use as the foundation for Golden Images. Specify as 'projects/PROJECT/global/images/IMAGE' or 'projects/PROJECT/global/images/family/FAMILY'. |  |
| [kms_key_id](outputs.tf#L37) | ID for the KMS key. |  |
| [network_project_id](outputs.tf#L42) | Project ID that hosts the VPC network. Defaults to project_id. Set this when using a Shared VPC where the network lives in a different host project than the image factory. |  |
| [project_id](outputs.tf#L47) | GCP project ID where the image factory resources will be created. |  |
| [region](outputs.tf#L52) | GCP region for regional resources (e.g., Artifact Registry repository). |  |
| [repository_id](outputs.tf#L57) | ID for the created Artifact Registry repository. |  |
| [sc_golden_image_family](outputs.tf#L62) | Compute Image family for the SecurityCenter Golden Image. |  |
| [sc_image_family](outputs.tf#L67) | Compute Image family for the SecurityCenter Golden Image. |  |
| [scanner_golden_image_family](outputs.tf#L72) | Compute Image family for the Nessus Scanner Golden Image. Use this value in acas/deployment/terraform.tfvars. |  |
| [scanner_image_family](outputs.tf#L77) | Compute Image family for the Nessus Scanner Golden Image. Use this value in acas/deployment/terraform.tfvars. |  |
| [subnetwork_name](outputs.tf#L82) | VPC subnetwork to use for the image builder VM. |  |
| [zone](outputs.tf#L87) | GCP zone where the image builder VM will run. |  |
<!-- END TFDOC -->
