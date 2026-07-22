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

# Optional Shared Services Template — Vulnerability Scanner (Nessus & SecurityCenter / ACAS)

This reference template provisions an optional vulnerability scanning solution (Tenable SecurityCenter and Nessus Scanners) on Google Cloud Platform (GCP). Organizations can deploy or adapt this template to meet centralized vulnerability assessment and security compliance scanning requirements.

> [!NOTE]
> This is an **optional reference template**. It is fully decoupled from the core landing zone (Stages 0–5) and can be adapted or omitted based on your security and scanning architecture.

---

## 1. Directory Structure & Workspace Layout

All configuration and code is located under `fast/stages-aw/shared-services/acas/`:

```
acas/
├── README.md               # Deployment Guide
├── data/
│   └── config.yml          # Centralized Configuration
├── image-factory/          # Provisions Private YUM Repo & Cloud Build Triggers
├── scanner/                # Nessus Scanner VM Module
└── securitycenter/         # Tenable SecurityCenter VM Module
```

---

## 2. End-to-End Operational Lifecycle

The following diagram illustrates the end-to-end operational flow:

```text
  [1. INGESTION]
  ├── Download CAC-protected RHEL8 RPMs from DISA Patch Repo
  └── Stage packages in gs://<PREFIX>-il5-prod-iac-core-outputs/acas-staging/

  [2. ACAS IMAGE FACTORY]
  ├── Synchronize staged RPMs into private YUM repository
  └── Trigger Cloud Build to bake CMEK-encrypted Golden Images

  [3. VM DEPLOYMENTS]
  ├── Query latest Golden Image families (acas-scanner-golden / acas-sc-golden)
  └── Terraform provisions private VMs on vdms-default subnet

  [4. CONNECTIVITY]
  └── Tunnel administrative SSH & Web Console traffic securely via Cloud IAP
```

---

## 3. Core Architectural Principles

All VMs are deployed with strict IL5 security controls:
* **Immutable Infrastructure:** Cloud Build uses private YUM repos to bake CMEK-encrypted Golden Images from a CIS STIG-hardened base RHEL image.
* **Dynamic Image Families:** VM deployments resolve and mount target boot disks dynamically using GCP Image Families (`acas-scanner-golden` and `acas-sc-golden`).
* **Custom VPC Integration:** Deploys directly into custom host VPC subnetworks, parsing details dynamically from resource self-links.
* **Secure, Zero-Trust Ingress:** All VMs have no public IP addresses; administrative SSH and web access is proxied exclusively via Cloud Identity-Aware Proxy (IAP).
* **Self-Contained KMS Keys:** Disks are encrypted with Customer-Managed Encryption Keys (CMEK) managed natively directly inside the project.

---

## 4. Configuration & Package Ingestion

* **Package Ingestion:** Because ACAS RPMs are CAC-protected, download them manually from the [DoD Patch Repository](https://patches.csd.disa.mil) and copy them to your secure staging GCS bucket:
  ```bash
  gcloud storage cp *.rpm "gs://<PREFIX>-il5-prod-iac-core-outputs/acas-staging/"
  ```
  The deployment automation automatically pulls, stages, and hosts these packages inside a private Artifact Registry YUM repository.

---

## 5. Deployment Options

### Option A: Interactive Local Execution
Execute the automated Shared Services interactive shell script:
```bash
./automation/shared-services-deploy.sh
```
Follow the prompts to run the **Image Factory**, **Nessus Scanner**, or **SecurityCenter** phases. The script automatically handles local variables, states, and RPM staging.

### Option B: GitLab CI/CD Pipelines
Trigger jobs via tag pushes matching `dev/v*` or `prod/v*`, or specify the variables `DEPLOY_STAGES` as `SERVICES` or `ACAS`.

The pipeline implements the following execution workflow:
1. **`plan/apply-acas-factory`:** Stages RPMs, sets up the private YUM repo, and bakes the CMEK-encrypted Golden Images.
2. **`plan-acas-scanner` & `plan-acas-sc`:** Run downstream of the factory. By utilizing GitLab `needs` with `optional: true`, these planning jobs automatically pause until the Golden Images have been compiled. If you are deploying changes *only* to the VMs (skipping the factory), they run immediately.
3. **`apply-acas-scanner` & `apply-acas-sc`:** Trigger manually to provision the Nessus Scanner or SecurityCenter instances once their respective downstream plans pass.

---

## 6. Verification & Connection Guide

### A. Accessing the Nessus Scanner Console
1. Establish a local-to-remote secure IAP tunnel:
   ```bash
   gcloud compute start-iap-tunnel <SCANNER_INSTANCE_NAME> 8834 \
     --local-host-port=localhost:8834 \
     --project=<SHARED_SERVICES_PROJECT_ID> \
     --zone=<ZONE>
   ```
2. Open your browser and navigate to **https://localhost:8834**.

### B. Accessing the SecurityCenter Console
1. Establish a local-to-remote secure IAP tunnel:
   ```bash
   gcloud compute start-iap-tunnel <SC_INSTANCE_NAME> 443 \
     --local-host-port=localhost:8443 \
     --project=<SHARED_SERVICES_PROJECT_ID> \
     --zone=<ZONE>
   ```
2. Open your browser and navigate to **https://localhost:8443**.

### C. SSH Access
To securely open a command terminal to your private instances, simply run:
```bash
gcloud compute ssh <INSTANCE_NAME> \
  --project=<SHARED_SERVICES_PROJECT_ID> \
  --zone=<ZONE> \
  --tunnel-through-iap
```