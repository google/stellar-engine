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

# Optional Shared Services Reference Templates

The stages contained in this directory (`shared-services/`) provide **optional, reusable reference templates** for common enterprise shared services. Organizations can selectively adopt, adapt, or omit any of these templates based on their specific infrastructure, compliance, and networking requirements.

> [!NOTE]
> **None of these templates are required** to deploy or operate the baseline `stellar-engine` landing zone. Stages 0 through 5 form the core landing zone foundation. The shared services templates below are decoupled reference examples that can be deployed independently as needed.

---

## Available Optional Templates

| Template Stage | Service Description | Example Use Case |
| :--- | :--- | :--- |
| **`acas`** | **Vulnerability Scanner Template**<br>Provisions Tenable SecurityCenter and Nessus vulnerability scanners on GCP. | Centralized vulnerability assessment, compliance auditing, and security scanning. |
| **`ad`** | **Active Directory Domain Controller Template**<br>Deploys high-availability Windows Server Active Directory DCs in dedicated shared VPC subnets. | Organizations extending existing on-premises or multi-cloud Active Directory domain services and Kerberos/LDAP authentication into GCP. |
| **`bcap`** | **Boundary Access Point & Interconnect Routing Template**<br>Provisions 99.99% high-availability boundary routing and Partner Interconnect infrastructure. | Connecting GCP host networks to dedicated external boundary networks, partner access points, or on-premises datacenters. |
| **`dns`** | **Enterprise Hybrid DNS Forwarding Template**<br>Configures centralized DNS forwarding rules and inbound/outbound server policies. | Integrating GCP Cloud DNS with on-premises or external enterprise DNS resolvers. |
| **`ntp`** | **Network Time Protocol (NTP) Synchronization Template**<br>Deploys dedicated internal Chrony/NTP servers for time synchronization. | Restricted or isolated networks requiring authenticated internal time synchronization. |
| **`smtp`** | **Internal Outbound Mail Relay (SMTP) Template**<br>Deploys Postfix mail relay instances for internal alert and notification delivery. | Internal workloads and management appliances requiring local mail relay without direct public internet egress. |

---

## Template Deployment Model

All shared services templates are modular and fully decoupled from the core landing zone stages (Stages 0–5). To use any template:
1. Ensure Stages 0 through 3 (Networking & Security) are deployed.
2. Navigate to the target template directory (e.g., `fast/stages-aw/shared-services/smtp`).
3. Populate `terraform.tfvars` from `terraform.tfvars.sample` and run `terraform apply`.
