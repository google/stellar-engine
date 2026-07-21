# Assured Compliance Assessment Solution (ACAS) Blueprint

This blueprint provisions an ACAS solution (Tenable SecurityCenter and Nessus Scanners) on Google Cloud Platform (GCP), designed for IL5 compliance under DoD Assured Workloads requirements.

<!-- BEGIN TOC -->
- [Introduction to ACAS](#introduction-to-acas)
- [Architecture Overview](#architecture-overview)
- [Disclaimer](#disclaimer)
- [Directory Structure](#directory-structure)
- [Workflow](#workflow)
  - [Connecting to an External SecurityCenter (AWS/Azure)](#connecting-to-an-external-securitycenter-awsazure)
- [Prerequisites](#prerequisites)
<!-- END TOC -->

## Introduction to ACAS
The Assured Compliance Assessment Solution (ACAS) is a suite of tools used by the Department of Defense (DoD) to assess the security posture of its networks and systems. It consists of:
- **Tenable SecurityCenter (SC)**: Centralized management console for vulnerability management and reporting.
- **Tenable Nessus Scanners**: Distributed vulnerability scanning agents that report back to SecurityCenter.

## Architecture Overview

This blueprint is structured as two independent, sequenced Terraform workspaces:

```
blueprints/il5/acas/
├── image-factory/    # Step 1: Build CMEK-encrypted Golden Images from ACAS RPMs
└── deployment/       # Step 2: Deploy production VMs from the Golden Images
```

All VMs are deployed with the following IL5 security controls:
- **Confidential Compute** (AMD SEV — optional, can be disabled for STIG-hardened base images)
- **Shielded VM** (Secure Boot, vTPM, Integrity Monitoring)
- **OS Login** (explicitly enabled at the instance level, with project-wide SSH keys blocked)
- **Customer-Managed Encryption Keys (CMEK)** on all disks
- **No external IP addresses** — all access via Cloud Identity-Aware Proxy (IAP)
- **Standard RHEL 8 or CIS STIG-hardened RHEL 8 base image**

## Disclaimer
- This blueprint is designed and intended for deployment in an IL5 environment using Google Cloud Assured Workloads.
- ACAS requires valid licenses from DISA/Tenable to function. This blueprint only provisions the underlying infrastructure.
- ACAS RPM packages must be obtained directly from the [DoD Patch Repository](https://patches.csd.disa.mil) using a valid CAC.

## Directory Structure

| Directory | Purpose |
|---|---|
| [`image-factory/`](./image-factory/README.md) | Provisions an Artifact Registry YUM repository for ACAS RPMs and Cloud Build triggers that bake immutable Golden Images from those RPMs. Run this **first** when deploying a new ACAS version. |
| [`deployment/`](./deployment/README.md) | Deploys the production ACAS VMs (SecurityCenter and/or Nessus Scanner), firewall rules, and associated IAM using the Golden Images produced by `image-factory`. |

## Workflow

This blueprint follows an **Immutable Infrastructure** pattern. The full lifecycle for deploying a new ACAS version is:

```
1. Download new ACAS RPMs from DoD Patch Repository (CAC required)
      ↓
2. Upload RPMs to Artifact Registry (acas/image-factory)
      ↓
3. Trigger Cloud Build to bake a new Golden Image (acas/image-factory)
      ↓
4. Deploy VMs from the Golden Image (acas/deployment)
```

### Connecting to an External SecurityCenter (AWS/Azure)
If deploying Nessus Scanners only (`build_scanner_image = true` and `build_sc_image = false`) and an external SecurityCenter exists (AWS, Azure, etc), then ensure:
1. A site-to-site VPN or Cloud Interconnect is active between GCP and the external environment.
2. Set the `securitycenter_source_ranges` variable in `deployment/scanner/terraform.tfvars` to the SecurityCenter's IP range. This controls the `acas-scanner-sc-mgmt` firewall rule that allows port `8834` access.

## Prerequisites

1. **ACAS RPMs**: Obtain from [patches.csd.disa.mil](https://patches.csd.disa.mil) using a valid CAC:
   - `SecurityCenter-<version>-el8.x86_64.rpm`
   - `Nessus-<version>-el8.x86_64.rpm`
2. **KMS Key**: A Cloud KMS key ring and key must exist in your core/KMS project.
3. **Networking**: A VPC and subnetwork must exist in your network project.
4. **IAP Access**: Cloud Identity-Aware Proxy must be enabled for SSH and port-forwarding access (`35.235.240.0/20` is included in firewall rules by default).
5. **Marketplace Access**: The GCP project must be able to pull images from `rhel-cloud` (for standard RHEL) or `cis-public` (for CIS STIG-hardened RHEL). Verify this is not blocked by an Assured Workloads org policy.
6. **Hardened Image Boot Compatibility**: If using a hardened base image like the CIS STIG image, Confidential Compute (AMD SEV) must be disabled (via `enable_confidential_compute = false` in `terraform.tfvars`) because the security policies and drivers of some hardened OS environments prevent proper boot with AMD SEV enabled.

<!-- BEGIN TFDOC -->
<!-- END TFDOC -->