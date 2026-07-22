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

# Optional Shared Services Stages

The stages contained in this directory (`shared-services/`) provide **optional, modular enterprise services** that can be selectively deployed based on an organization's specific compliance, security, and networking requirements.

> [!NOTE]
> **None of these stages are required** to deploy or operate the baseline `stellar-engine` landing zone. Stages 0 through 5 form the core landing zone infrastructure. The shared services stages below can be deployed independently as needed.

---

## Available Optional Services

| Service Stage | Purpose & Description | Typical Use Case |
| :--- | :--- | :--- |
| **`acas`** | **Assured Compliance Assessment Solution**<br>Provisions Tenable SecurityCenter and Nessus vulnerability scanners on GCP. | Mandated for DoD/defense compliance regimes requiring centralized vulnerability and compliance scanning. |
| **`bcap`** | **Boundary Cloud Access Point**<br>Provisions high-availability boundary routing and inspection infrastructure. | Used for connecting the landing zone to dedicated external boundary networks (such as NIPRNet, DISA BCAP, or private enterprise boundary access points). |
| **`ad`** | **Active Directory Domain Controllers**<br>Deploys high-availability Windows Server Active Directory DCs in dedicated shared VPC subnets. | Organizations requiring native on-cloud Active Directory domain services and Kerberos/LDAP authentication. |
| **`dns`** | **Enterprise DNS Forwarding**<br>Configures centralized DNS forwarding rules and inbound/outbound server policies. | Environments integrating GCP Cloud DNS with on-premises or external enterprise DNS resolvers. |
| **`ntp`** | **Network Time Protocol (NTP) Servers**<br>Deploys dedicated internal Chrony/NTP servers for time synchronization. | Air-gapped or restricted networks requiring authenticated, centralized internal time synchronization. |
| **`smtp`** | **Internal SMTP Relay**<br>Deploys postfix mail relay instances for internal alert and notification delivery. | Internal workloads and appliances requiring local mail relay without direct public internet egress. |

---

## Deployment Model

All shared services stages are decoupled from the core landing zone stages (Stages 0–5). To deploy any shared service:
1. Ensure Stages 0 through 3 (Networking & Security) are deployed.
2. Navigate to the desired service directory (e.g. `fast/stages-aw/shared-services/bcap`).
3. Populate `terraform.tfvars` and run `terraform apply`.
