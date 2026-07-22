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

# Google Cloud NetSec Services

The NetSec folder acts as the foundation for the landing zone’s shared infrastructure. It centralizes critical governance and operational projects that support the entire IL5 environment, ensuring that core infrastructure such as infrastructure-as-code (IaC), billing exports, and audit logs—is decoupled from specific tenant workloads for better security and stability.

# Table of Contents
<!-- BEGIN TOC -->
- [Shared Core Projects](#shared-core-projects)
  - [Prefix-Compliance-Regime-Prod-Iac-Core](#prefix-compliance-regime-prod-iac-core)
  - [Prefix-Compliance-Regime-Prod-Billing-Exp](#prefix-compliance-regime-prod-billing-exp)
  - [Prefix-Compliance-Regime-Prod-Audit-Logs](#prefix-compliance-regime-prod-audit-logs)
- [Networking Folder](#networking-folder)
  - [Prefix-Compliance-Regime-Net-Vdss-Host](#prefix-compliance-regime-net-vdss-host)
  - [Prefix-Compliance-Regime-Env-Net-Host](#prefix-compliance-regime-Env-net-host)
- [Security Folder](#security-folder)
  - [Prefix-Compliance-Regime-Prod-Sec-Core](#prefix-compliance-regimel5-prod-sec-core)
  - [Prefix-Compliance-Regime-Env-Sec-Core](#prefix-compliance-regime-Env-sec-core)
<!-- END TOC -->

## Shared Core Projects

#### prefix-compliance-regime-prod-iac-core
This is the authoritative project for managing the lifecycle of common resources. It hosts Terraform state files, CI/CD runners (like Cloud Build), and Artifact Registry repositories for shared container images. 

#### prefix-compliance-regime-prod-billing-exp
This project is dedicated to financial governance and granular cost tracking. It leverages BigQuery for billing export data and Looker Studio for visualization, allowing to generate tenant-specific reports and set budget alerts to prevent cost overruns for the environment.

#### prefix-compliance-regime-prod-audit-logs 
A compliance project that serves as the central sink for all Cloud Audit Logs. By using Log Sinks to aggregate data here, ensure that logs are immutable and stored in a highly-protected location.

## Networking Folder
The Networking folder serves as the "Hub" in Hub-and-Spoke network architecture. It centralizes connectivity, hosting the host VPCs that provide shared network services and routing logic to all tenant spokes, effectively controlling the data perimeter for the environment.

### Networking Projects

#### prefix-compliance-regime-net-vdss-host
This project hosts the Virtual Datacenter Security Stack (VDSS). It is the primary ingress/egress point for the environment, containing high-performance Next-Generation Firewalls (NGFWs), Cloud Armor for DDoS protection, and Cloud Load Balancing. 

#### prefix-compliance-regime-env-net-host 
Serving as the Shared VPC Host for the environment-specific landing zone, this project contains the env-spoke-0 network. It acts as the authoritative source for IP Address Management (IPAM), manages Private Service Connect (PSC) endpoints for Google APIs, and hosts the Cloud DNS zones required for internal service resolution across all development tenants, like MACOM.

## Security Folder
The Security folder isolates the most sensitive security operations and identity management functions. By siloing these projects, ensures that infrastructure administrators do not have lateral access to the keys and security policies that protect the environment.

### Security Projects

#### prefix-compliance-regime-prod-sec-core 
The production security hub, hosting the Cloud Key Management Service (Cloud KMS) for production encryption keys and Secret Manager for sensitive credentials.

#### prefix-compliance-regime-env-sec-core
This project mirrors the production security setup but is tailored for development environments. It allows for IAM policies testing, key rotations, and security scanners without risking production configurations.