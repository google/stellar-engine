# System Security Plan (SSP) - {{ SYSTEM_NAME }}
## System Impact Level: {{ IMPACT_LEVEL }}
## Compliance Baseline: {{ COMPLIANCE_BASELINE }}

# 1. System Identification

## 1.1 System Name & General Information
| Document Control Metadata | Value |
|---|---|
| **System Name** | {{ SYSTEM_NAME }} |
| **System Abbreviation** | {{ SYSTEM_ABBREVIATION }} |
| **Document Version** | {{ VERSION }} |
| **Effective Date** | {{ DATE }} |
| **Author / Organization** | {{ ORGANIZATION }} |
| **Primary GCP Location** | {{ PRIMARY_LOCATION }} |
| **Billing Account** | {{ BILLING_ACCOUNT }} |

## 1.2 System Categorization & Governance Baseline

[CONFIG_REQUIRED: CNSSI 1253 security categorization (confidentiality, integrity, availability), applicable CNSSI 1253 overlays, and DoD Impact Level]

### Document Change Record
| Date | Version | Author | Changes Made / Section(s) |
|---|---|---|---|
| {{ DATE }} | {{ VERSION }} | {{ ORGANIZATION }} | Initial Automated Provisioning & SSP Baseline for {{ SYSTEM_NAME }} |

> [!NOTE]
> **System Architecture & Security Control Implementation**
> This System Security Plan details technical, operational, and management controls for **{{ SYSTEM_NAME }}**.
> Technical controls implemented in the Terraform blueprints (IAM, VPC topology, Cloud KMS CMEK, Assured Workloads) are described from the extracted configuration.
> Inherited controls cite the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (FedRAMP package {{ CSP_PATO_PACKAGE_ID }}) and the {{ DOD_PA_FULL_LABEL }} that DISA issued for Google Cloud.
> Fields that the RMF team must confirm are marked with action callouts.


## 1.3 System Points of Contact & Other Designated POCs

> [!IMPORTANT]
> [WARNING: RMF TEAM ACTION REQUIRED: Verify and populate organizational contact details, secondary system points of contact (POCs), technical leads, and mission representatives in this section prior to formal ATO authorization submission.]

| Role / Designation | Name | Title | Organization / Office | Work Phone | Email Address |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **System Owner (SO)** | {{ SO_NAME }} | {{ SO_TITLE }} | {{ SO_ORG }} | {{ SO_PHONE }} | {{ SO_EMAIL }} |
| **ISSM** | {{ ISSM_NAME }} | {{ ISSM_TITLE }} | {{ ISSM_ORG }} | {{ ISSM_PHONE }} | {{ ISSM_EMAIL }} |
| **ISSO** | {{ ISSO_NAME }} | {{ ISSO_TITLE }} | {{ ISSO_ORG }} | {{ ISSO_PHONE }} | {{ ISSO_EMAIL }} |
| **Authorizing Official (AO)** | {{ AO_NAME }} | {{ AO_TITLE }} | {{ AO_ORG }} | {{ AO_PHONE }} | {{ AO_EMAIL }} |
| **Technical / DevSecOps Lead** | `[WARNING: RMF TEAM ACTION REQUIRED: Technical POC Name]` | DevSecOps Lead Engineer | `[WARNING: RMF TEAM ACTION REQUIRED: Office Address]` | `[WARNING: RMF TEAM ACTION REQUIRED: Phone]` | `[WARNING: RMF TEAM ACTION REQUIRED: Email]` |
| **Other Designated POC (Operations)** | `[INFORMATIONAL: OPTIONAL CONFIG: Secondary Ops Contact]` | Cloud Operations Lead | `[INFORMATIONAL: OPTIONAL CONFIG: Office Address]` | `[INFORMATIONAL: OPTIONAL CONFIG: Phone]` | `[INFORMATIONAL: OPTIONAL CONFIG: Email]` |


## 1.4 Information System Operational Status


| System Status | Details |
| --- | --- |
| **Operational** | The system is operating and in production |
| **Under Development** | The system is being designed, developed, or implemented |
| **Major Modification** | The system is undergoing a major change, development, or transition |

**Current status:** [CONFIG_REQUIRED: Operational, Under Development, or Major Modification]


## 1.5 Information System Type

{{ SYSTEM_NAME }} service model: [CONFIG_REQUIRED: IaaS, PaaS, and/or SaaS]


## 1.6 General System Description

{{ SYSTEM_DESCRIPTION }}


## 1.7 Types of Users & Codebase IAM Architecture

> [!IMPORTANT]
> [WARNING: RMF TEAM ACTION REQUIRED: Confirm system access roles, administrative groups, and separation of duties boundaries match operational organizational policies.]

The system enforces the principle of least privilege and separation of duties across Google Cloud organizations, folders, and application projects. Architectural security identities, administrative role groups, and cloud service accounts are dynamically extracted directly from source code and Terraform blueprints:

{{ SEPARATION_OF_DUTIES_TABLE }}


## 1.8 System Environment, Connectivity & Technical Architecture

The technical environment, connectivity mechanisms, authentication architecture, and cryptographic protection standards are dynamically discovered from the system's infrastructure blueprints and Terraform configurations:

| Architecture Domain | Discovered Technical Implementation Standard | Source Verification |
| :--- | :--- | :--- |
| **Network & Perimeter Connectivity** | {{ CONNECTIVITY }} | Cloud Interconnect, VPC Peering, and NCC topology |
| **Identity & Authentication** | {{ AUTHENTICATION_MECHANISM }} | Cloud Identity, Workforce Identity Federation, and IAM configuration |
| **Cryptographic Protection** | {{ ENCRYPTION_STANDARD }} | Cloud KMS CMEK and FIPS-validated cryptographic modules |


### 1.8.1 Logical Network Subnets & IP Allocation Boundaries

The system enforces logical network segregation across dedicated virtual subnets. Discovered IP ranges and boundaries extracted from infrastructure configurations include:

{{ SUBNET_BOUNDARY_TABLE }}


### 1.8.2 Workload Containers & Application Runtime Services

Containerized workload services, container base images, and runtime execution environments authorized within the boundary include:

{{ CONTAINER_WORKLOAD_TABLE }}


### 1.8.3 DoD Cloud Computing SRG ({{ DOD_IMPACT_SHORT }}) Enclave Requirements (BCAP/CAP, CSSP, DoD PKI & Data Residency)

<!-- IF DOD_IL6 -->
In accordance with the **DISA Cloud Service Provider (CSP) Security Requirements Guide (SRG) V1R7** for Impact Level 6 (IL6 — Classified Information up to SECRET and National Security Systems [NSS] / National Security Information [NSI] hosted on dedicated classified enclaves connected via SIPRNet or CNSSP-11 circuits), the system enforces the following mandatory DoD classified enclave requirements in addition to the NIST SP 800-53 Rev. 5 / CNSSI 1253 Classified Information Overlay baseline:
<!-- ENDIF -->
<!-- IF DOD_IL5 -->
In accordance with the **DISA Cloud Service Provider (CSP) Security Requirements Guide (SRG) V1R7** for Impact Level 5 (IL5 — unclassified National Security Systems [NSS], National Security Information [NSI], and Controlled Unclassified Information [CUI] requiring a higher level of protection than that afforded by Impact Level 4 as deemed necessary by the information owner), the system enforces the following mandatory DoD enclave requirements in addition to the NIST SP 800-53 Rev. 5 / CNSSI 1253 baseline:
<!-- ENDIF -->
<!-- IF DOD_IL4 -->
In accordance with the **DISA Cloud Service Provider (CSP) Security Requirements Guide (SRG) V1R7** for Impact Level 4 (IL4 — Controlled Unclassified Information [CUI] and non-CUI mission information requiring moderate confidentiality and integrity), the system enforces the following mandatory DoD enclave requirements in addition to the NIST SP 800-53 Rev. 5 / DISA CSP SRG V1R7 Table D-1 baseline:
<!-- ENDIF -->
<!-- IF DOD_IL2 -->
In accordance with the **DISA Cloud Service Provider (CSP) Security Requirements Guide (SRG) V1R7** for Impact Level 2 (IL2 — Noncontrolled Unclassified Information cleared for public release or non-CUI unclassified mission information leveraging FedRAMP Moderate/High P-ATO reciprocity), the system enforces the following DoD enclave requirements in addition to the NIST SP 800-53 Rev. 5 / FedRAMP Moderate baseline:
<!-- ENDIF -->

| DoD CC SRG Domain | Enclave Requirement & Governing Authority | System Implementation & Verification Status |
| :--- | :--- | :--- |
| **DoD Network Boundary & CAP / BCAP Routing (`SC-7`)** | All NIPRNet / DoD Information Network (DODIN) ingress and egress traffic MUST transit a DISA-accredited Cloud Access Point (CAP) or DoD Boundary Cloud Access Point (BCAP) over Dedicated or Partner Cloud Interconnect (`{{ CONNECTIVITY }}`) in accordance with the DISN Connection Process Guide (CPG). | `[CONFIG_REQUIRED: Document the DISA CAP / BCAP circuits, SNAP/SGS registration ID, and Authority to Connect (ATC) approval status]` |
| **Cybersecurity Service Provider (CSSP) Alignment (`DoDI 8530.01`, `AU-6`, `IR-6`, `SI-4`)** | The Mission Owner MUST maintain an active subscriber agreement with a DoD-accredited CSSP (`{{ CSSP_PROVIDER }}`) for 24x7x365 computer network defense (CND), continuous log streaming (`{{ TELEMETRY_PIPELINE }}`), and CJCSM 6510.01B cyber incident reporting to USCYBERCOM / JIMS. Note: Google Cloud Security Command Center (SCC) is not in the Assured Workloads {{ DOD_IMPACT_SHORT }} accredited product scope and MUST NOT be relied upon as the primary {{ DOD_IMPACT_SHORT }} boundary sensor. | `[CONFIG_REQUIRED: Reference the signed DoD CSSP Memorandum of Agreement (MOA) / Service Level Agreement (SLA) for {{ CSSP_PROVIDER }}]` |
| **DoD PKI / CAC Hardware Authentication (`IA-2(1)`, `IA-2(2)`, `IA-5(2)`, `SC-17`)** | Interactive administrative and user authentication (`{{ AUTHENTICATION_MECHANISM }}`) MUST enforce phishing-resistant DoD PKI X.509 client certificates (Common Access Card [CAC], Personal Identity Verification [PIV], or DoD External Certificate Authority [ECA]) chained to the DoD Root CA (`{{ PKI_TRUST_TYPE }}`). | `[CONFIG_REQUIRED: Verify DoD Root CA trust bundle configuration in the enterprise Identity Provider ({{ IDENTITY_PROVIDER }}) and Workforce Identity Federation]` |
| **U.S. Sovereign Data Location & U.S.-Person Administration (`SA-9(5)`, `PS-3`, `MA-5`)** | All customer data at rest, backups, KMS keys, and compute processing MUST remain exclusively within U.S. sovereign Google Cloud regions (`us-*`) enforced via Assured Workloads {{ DOD_IMPACT_SHORT }} Organization Policy (`constraints/gcp.resourceLocations`), and all CSP support and Mission Owner privileged operators MUST be screened U.S. citizens / U.S. persons meeting DoD IT-I (Tier 5) / IT-II (Tier 3) background investigation requirements. | Enforced at the Google Cloud Assured Workloads {{ DOD_IMPACT_SHORT }} folder boundary (`{{ PRIMARY_LOCATION }}`) and inherited from the Google Services {{ DOD_PA_FULL_LABEL }} (`{{ CSP_PATO_PACKAGE_ID }}`). |


# 2. Minimum Security Controls


## 2.1 Access Control


### AC-1 Policy and Procedures


a. Develop, document, and disseminate to [Assignment: organization-defined personnel or roles]:

  1. [Selection (one or more): organization-level; mission/business process-level; system-level] access control policy that:

    (a) Addresses purpose, scope, roles, responsibilities, management commitment, coordination among organizational entities, and compliance; and

    (b) Is consistent with applicable laws, executive orders, directives, regulations, policies, standards, and guidelines; and

  2. Procedures to facilitate the implementation of the access control policy and the associated access controls;


b. Designate an [Assignment: organization-defined official] to manage the development, documentation, and dissemination of the access control policy and procedures; and


c. Review and update the current access control:

  1. Policy [Assignment: organization-defined frequency — FedRAMP High: at least annually] and following [Assignment: organization-defined events — FedRAMP High: significant changes]; and

  2. Procedures [Assignment: organization-defined frequency — FedRAMP High: at least annually] and following [Assignment: organization-defined events].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure identity backends and hypervisor isolation. Where configured in the system's Terraform blueprints, the platform enforces least-privilege IAM bindings, Identity-Aware Proxy (IAP) TCP/HTTPS forwarding, VPC Service Controls perimeters, and Google Organization Policy constraints. |
| **FedRAMP High Parameter Values**: `ac-01_odp.05` (frequency): at least annually; `ac-01_odp.07` (frequency): at least annually; `ac-01_odp.08` (events): significant changes |


### AC-2 Account Management


a. Define and document the types of accounts allowed and specifically prohibited for use within the system;


b. Assign account managers;


c. Require [Assignment: organization-defined prerequisites and criteria] for group and role membership;


d. Specify:

  1. Authorized users of the system;

  2. Group and role membership; and

  3. Access authorizations (i.e., privileges) and [Assignment: organization-defined attributes (as required)] for each account;


e. Require approvals by [Assignment: organization-defined personnel or roles] for requests to create accounts;


f. Create, enable, modify, disable, and remove accounts in accordance with [Assignment: organization-defined policy, procedures, prerequisites, and criteria];


g. Monitor the use of accounts;


h. Notify account managers and [Assignment: organization-defined personnel or roles] within:

  1. [Assignment: organization-defined time period — FedRAMP High: twenty-four (24) hours] when accounts are no longer required;

  2. [Assignment: organization-defined time period — FedRAMP High: eight (8) hours] when users are terminated or transferred; and

  3. [Assignment: organization-defined time period — FedRAMP High: eight (8) hours] when system usage or need-to-know changes for an individual;


i. Authorize access to the system based on:

  1. A valid access authorization;

  2. Intended system usage; and

  3. [Assignment: organization-defined attributes (as required)];


j. Review accounts for compliance with account management requirements [Assignment: organization-defined frequency — FedRAMP High: monthly for privileged accessed, every six (6) months for non-privileged access];


k. Establish and implement a process for changing shared or group account authenticators (if deployed) when individuals are removed from the group; and


l. Align account management processes with personnel termination and transfer processes.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure identity backends and hypervisor isolation. Where configured in the system's Terraform blueprints, the platform enforces least-privilege IAM bindings, Identity-Aware Proxy (IAP) TCP/HTTPS forwarding, VPC Service Controls perimeters, and Google Organization Policy constraints. |
| **FedRAMP High Parameter Values**: `ac-02_odp.06` (time period): twenty-four (24) hours; `ac-02_odp.07` (time period): eight (8) hours; `ac-02_odp.08` (time period): eight (8) hours; `ac-02_odp.10` (frequency): monthly for privileged accessed, every six (6) months for non-privileged access |


### AC-2(1) Account Management | Automated System Account Management

Support the management of system accounts using [Assignment: organization-defined automated mechanisms].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure identity backends and hypervisor isolation. Where configured in the system's Terraform blueprints, the platform enforces least-privilege IAM bindings, Identity-Aware Proxy (IAP) TCP/HTTPS forwarding, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### AC-2(2) Account Management | Automated Temporary and Emergency Account Management

Automatically [Selection: remove; disable — FedRAMP High: Selection: disables] temporary and emergency accounts after [Assignment: organization-defined time period for each type of account — FedRAMP High: no more than 24 hours from last use].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure identity backends and hypervisor isolation. Where configured in the system's Terraform blueprints, the platform enforces least-privilege IAM bindings, Identity-Aware Proxy (IAP) TCP/HTTPS forwarding, VPC Service Controls perimeters, and Google Organization Policy constraints. |
| **FedRAMP High Parameter Values**: `ac-02.02_odp.01`: Selection: disables; `ac-02.02_odp.02` (time period): no more than 24 hours from last use |


### AC-2(3) Account Management | Disable Accounts

Disable accounts within [Assignment: organization-defined time period — FedRAMP High: 24 hours for user accounts] when the accounts:


(a) Have expired;


(b) Are no longer associated with a user or individual;


(c) Are in violation of organizational policy; or


(d) Have been inactive for [Assignment: organization-defined time period — FedRAMP High: thirty-five (35) days (See additional requirements and guidance.)].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure identity backends and hypervisor isolation. Where configured in the system's Terraform blueprints, the platform enforces least-privilege IAM bindings, Identity-Aware Proxy (IAP) TCP/HTTPS forwarding, VPC Service Controls perimeters, and Google Organization Policy constraints. |
| **FedRAMP High Parameter Values**: `ac-02.03_odp.01` (time period): 24 hours for user accounts; `ac-02.03_odp.02` (time period): thirty-five (35) days (See additional requirements and guidance.)<br>**FedRAMP Additional Guidance**: Requirement: The service provider defines the time period for non-user accounts (e.g., accounts associated with devices). The time periods are approved and accepted by the AO. Where user management is a function of the service, reports of activity of consumer users shall be made available. (d) Requirement: The service provider defines the time period of inactivity for device identifiers. Guidance: For DoD clouds, see DoD cloud website for specific DoD requirements that go above and beyond FedRAMP https://public.cyber.mil/dccs/. |


### AC-2(4) Account Management | Automated Audit Actions

Automatically audit account creation, modification, enabling, disabling, and removal actions.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure identity backends and hypervisor isolation. Where configured in the system's Terraform blueprints, the platform enforces least-privilege IAM bindings, Identity-Aware Proxy (IAP) TCP/HTTPS forwarding, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### AC-2(5) Account Management | Inactivity Logout

Require that users log out when [Assignment: organization-defined time period of expected inactivity or description of when to log out — FedRAMP High: inactivity is anticipated to exceed Fifteen (15) minutes].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure identity backends and hypervisor isolation. Where configured in the system's Terraform blueprints, the platform enforces least-privilege IAM bindings, Identity-Aware Proxy (IAP) TCP/HTTPS forwarding, VPC Service Controls perimeters, and Google Organization Policy constraints. |
| **FedRAMP High Parameter Values**: `ac-02.05_odp` (time period of expected inactivity or description of when to log out): inactivity is anticipated to exceed Fifteen (15) minutes<br>**FedRAMP Additional Guidance**: Guidance: Should use a shorter timeframe than AC-12. |


### AC-2(7) Account Management | Privileged User Accounts


(a) Establish and administer privileged user accounts in accordance with [Selection: a role-based access scheme; an attribute-based access scheme];


(b) Monitor privileged role or attribute assignments;


(c) Monitor changes to roles or attributes; and


(d) Revoke access when privileged role or attribute assignments are no longer appropriate.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure identity backends and hypervisor isolation. Where configured in the system's Terraform blueprints, the platform enforces least-privilege IAM bindings, Identity-Aware Proxy (IAP) TCP/HTTPS forwarding, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### AC-2(9) Account Management | Restrictions on Use of Shared and Group Accounts

Only permit the use of shared and group accounts that meet [Assignment: organization-defined conditions for establishing shared and group accounts — FedRAMP High: organization-defined need with justification statement that explains why such accounts are necessary].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure identity backends and hypervisor isolation. Where configured in the system's Terraform blueprints, the platform enforces least-privilege IAM bindings, Identity-Aware Proxy (IAP) TCP/HTTPS forwarding, VPC Service Controls perimeters, and Google Organization Policy constraints. |
| **FedRAMP High Parameter Values**: `ac-02.09_odp` (conditions): organization-defined need with justification statement that explains why such accounts are necessary<br>**FedRAMP Additional Guidance**: Requirement: Required if shared/group accounts are deployed. |


### AC-2(11) Account Management | Usage Conditions

Enforce [Assignment: organization-defined circumstances and/or usage conditions] for [Assignment: organization-defined system accounts].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure identity backends and hypervisor isolation. Where configured in the system's Terraform blueprints, the platform enforces least-privilege IAM bindings, Identity-Aware Proxy (IAP) TCP/HTTPS forwarding, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### AC-2(12) Account Management | Account Monitoring for Atypical Usage


(a) Monitor system accounts for [Assignment: organization-defined atypical usage]; and


(b) Report atypical usage of system accounts to [Assignment: organization-defined personnel or roles — FedRAMP High: at a minimum, the ISSO and/or similar role within the organization].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure identity backends and hypervisor isolation. Where configured in the system's Terraform blueprints, the platform enforces least-privilege IAM bindings, Identity-Aware Proxy (IAP) TCP/HTTPS forwarding, VPC Service Controls perimeters, and Google Organization Policy constraints. |
| **FedRAMP High Parameter Values**: `ac-02.12_odp.02` (personnel or roles): at a minimum, the ISSO and/or similar role within the organization<br>**FedRAMP Additional Guidance**: (a) Requirement: Required for privileged accounts. (b) Requirement: Required for privileged accounts. |


### AC-2(13) Account Management | Disable Accounts for High-risk Individuals

Disable accounts of individuals within [Assignment: organization-defined time period — FedRAMP High: one (1) hour] of discovery of [Assignment: organization-defined significant risks].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure identity backends and hypervisor isolation. Where configured in the system's Terraform blueprints, the platform enforces least-privilege IAM bindings, Identity-Aware Proxy (IAP) TCP/HTTPS forwarding, VPC Service Controls perimeters, and Google Organization Policy constraints. |
| **FedRAMP High Parameter Values**: `ac-02.13_odp.01` (time period): one (1) hour |


### AC-3 Access Enforcement

Enforce approved authorizations for logical access to information and system resources in accordance with applicable access control policies.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure identity backends and hypervisor isolation. Where configured in the system's Terraform blueprints, the platform enforces least-privilege IAM bindings, Identity-Aware Proxy (IAP) TCP/HTTPS forwarding, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### AC-3(4) Access Enforcement | Discretionary Access Control

Enforce [Assignment: organization-defined discretionary access control policy] over the set of covered subjects and objects specified in the policy, and where the policy specifies that a subject that has been granted access to information can do one or more of the following:


(a) Pass the information to any other subjects or objects;


(b) Grant its privileges to other subjects;


(c) Change security attributes on subjects, objects, the system, or the system's components;


(d) Choose the security attributes to be associated with newly created or revised objects; or


(e) Change the rules governing access control.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure identity backends and hypervisor isolation. Where configured in the system's Terraform blueprints, the platform enforces least-privilege IAM bindings, Identity-Aware Proxy (IAP) TCP/HTTPS forwarding, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### AC-4 Information Flow Enforcement

Enforce approved authorizations for controlling the flow of information within the system and between connected systems based on [Assignment: organization-defined information flow control policies].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure identity backends and hypervisor isolation. Where configured in the system's Terraform blueprints, the platform enforces least-privilege IAM bindings, Identity-Aware Proxy (IAP) TCP/HTTPS forwarding, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### AC-4(4) Information Flow Enforcement | Flow Control of Encrypted Information

Prevent encrypted information from bypassing [Assignment: organization-defined information flow control mechanisms — FedRAMP High: intrusion detection mechanisms] by [Selection (one or more): decrypting the information; blocking the flow of the encrypted information; terminating communications sessions attempting to pass encrypted information; [Assignment: organization-defined procedure or method]].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure identity backends and hypervisor isolation. Where configured in the system's Terraform blueprints, the platform enforces least-privilege IAM bindings, Identity-Aware Proxy (IAP) TCP/HTTPS forwarding, VPC Service Controls perimeters, and Google Organization Policy constraints. |
| **FedRAMP High Parameter Values**: `ac-04.04_odp.01` (information flow control mechanisms): intrusion detection mechanisms<br>**FedRAMP Additional Guidance**: Requirement: The service provider must support Agency requirements to comply with M-21-31 (https://www.whitehouse.gov/wp-content/uploads/2021/08/M-21-31-Improving-the-Federal-Governments-Investigative-and-Remediation-Capabilities-Related-to-Cybersecurity-Incidents.pdf) and M-22-09 (https://www.whitehouse.gov/wp-content/uploads/2022/01/M-22-09.pdf). |


### AC-4(21) Information Flow Enforcement | Physical or Logical Separation of Information Flows

Separate information flows logically or physically using [Assignment: organization-defined mechanisms and/or techniques] to accomplish [Assignment: organization-defined required separations by types of information].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure identity backends and hypervisor isolation. Where configured in the system's Terraform blueprints, the platform enforces least-privilege IAM bindings, Identity-Aware Proxy (IAP) TCP/HTTPS forwarding, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### AC-5 Separation of Duties


a. Identify and document [Assignment: organization-defined duties of individuals requiring separation]; and


b. Define system access authorizations to support separation of duties.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure identity backends and hypervisor isolation. Where configured in the system's Terraform blueprints, the platform enforces least-privilege IAM bindings, Identity-Aware Proxy (IAP) TCP/HTTPS forwarding, VPC Service Controls perimeters, and Google Organization Policy constraints. |
| **FedRAMP Additional Guidance**: Guidance: CSPs have the option to provide a separation of duties matrix as an attachment to the SSP. |


### AC-6 Least Privilege

Employ the principle of least privilege, allowing only authorized accesses for users (or processes acting on behalf of users) that are necessary to accomplish assigned organizational tasks.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure identity backends and hypervisor isolation. Where configured in the system's Terraform blueprints, the platform enforces least-privilege IAM bindings, Identity-Aware Proxy (IAP) TCP/HTTPS forwarding, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### AC-6(1) Least Privilege | Authorize Access to Security Functions

Authorize access for [Assignment: organization-defined individuals or roles] to:

(a) [Assignment: organization-defined security functions (deployed in hardware, software, and firmware) — FedRAMP High: all functions not publicly accessible]; and

(b) [Assignment: organization-defined security-relevant information — FedRAMP High: all security-relevant information not publicly available].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure identity backends and hypervisor isolation. Where configured in the system's Terraform blueprints, the platform enforces least-privilege IAM bindings, Identity-Aware Proxy (IAP) TCP/HTTPS forwarding, VPC Service Controls perimeters, and Google Organization Policy constraints. |
| **FedRAMP High Parameter Values**: `ac-06.01_odp.02` (security functions (deployed in hardware)): all functions not publicly accessible; `ac-06.01_odp.03` (security functions (deployed in software)): all functions not publicly accessible; `ac-06.01_odp.04` (security functions (deployed in firmware)): all functions not publicly accessible; `ac-06.01_odp.05` (security-relevant information): all security-relevant information not publicly available |


### AC-6(2) Least Privilege | Non-privileged Access for Nonsecurity Functions

Require that users of system accounts (or roles) with access to [Assignment: organization-defined security functions or security-relevant information — FedRAMP High: all security functions] use non-privileged accounts or roles, when accessing nonsecurity functions.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure identity backends and hypervisor isolation. Where configured in the system's Terraform blueprints, the platform enforces least-privilege IAM bindings, Identity-Aware Proxy (IAP) TCP/HTTPS forwarding, VPC Service Controls perimeters, and Google Organization Policy constraints. |
| **FedRAMP High Parameter Values**: `ac-06.02_odp` (security functions or security-relevant information): all security functions<br>**FedRAMP Additional Guidance**: Guidance: Examples of security functions include but are not limited to: establishing system accounts, configuring access authorizations (i.e., permissions, privileges), setting events to be audited, and setting intrusion detection parameters, system programming, system and security administration, other privileged functions. |


### AC-6(3) Least Privilege | Network Access to Privileged Commands

Authorize network access to [Assignment: organization-defined privileged commands — FedRAMP High: all privileged commands] only for [Assignment: organization-defined compelling operational needs] and document the rationale for such access in the security plan for the system.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure identity backends and hypervisor isolation. Where configured in the system's Terraform blueprints, the platform enforces least-privilege IAM bindings, Identity-Aware Proxy (IAP) TCP/HTTPS forwarding, VPC Service Controls perimeters, and Google Organization Policy constraints. |
| **FedRAMP High Parameter Values**: `ac-06.03_odp.01` (privileged commands): all privileged commands |


### AC-6(5) Least Privilege | Privileged Accounts

Restrict privileged accounts on the system to [Assignment: organization-defined personnel or roles].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure identity backends and hypervisor isolation. Where configured in the system's Terraform blueprints, the platform enforces least-privilege IAM bindings, Identity-Aware Proxy (IAP) TCP/HTTPS forwarding, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### AC-6(7) Least Privilege | Review of User Privileges


(a) Review [Assignment: organization-defined frequency — FedRAMP High: at a minimum, annually] the privileges assigned to [Assignment: organization-defined roles or classes of users — FedRAMP High: all users with privileges] to validate the need for such privileges; and


(b) Reassign or remove privileges, if necessary, to correctly reflect organizational mission and business needs.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure identity backends and hypervisor isolation. Where configured in the system's Terraform blueprints, the platform enforces least-privilege IAM bindings, Identity-Aware Proxy (IAP) TCP/HTTPS forwarding, VPC Service Controls perimeters, and Google Organization Policy constraints. |
| **FedRAMP High Parameter Values**: `ac-06.07_odp.01` (frequency): at a minimum, annually; `ac-06.07_odp.02` (roles and classes): all users with privileges |


### AC-6(8) Least Privilege | Privilege Levels for Code Execution

Prevent the following software from executing at higher privilege levels than users executing the software: [Assignment: organization-defined software — FedRAMP High: any software except software explicitly documented].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure identity backends and hypervisor isolation. Where configured in the system's Terraform blueprints, the platform enforces least-privilege IAM bindings, Identity-Aware Proxy (IAP) TCP/HTTPS forwarding, VPC Service Controls perimeters, and Google Organization Policy constraints. |
| **FedRAMP High Parameter Values**: `ac-06.08_odp` (software): any software except software explicitly documented |


### AC-6(9) Least Privilege | Log Use of Privileged Functions

Log the execution of privileged functions.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure identity backends and hypervisor isolation. Where configured in the system's Terraform blueprints, the platform enforces least-privilege IAM bindings, Identity-Aware Proxy (IAP) TCP/HTTPS forwarding, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### AC-6(10) Least Privilege | Prohibit Non-privileged Users from Executing Privileged Functions

Prevent non-privileged users from executing privileged functions.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure identity backends and hypervisor isolation. Where configured in the system's Terraform blueprints, the platform enforces least-privilege IAM bindings, Identity-Aware Proxy (IAP) TCP/HTTPS forwarding, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### AC-7 Unsuccessful Logon Attempts


a. Enforce a limit of [Assignment: organization-defined number] consecutive invalid logon attempts by a user during a [Assignment: organization-defined time period]; and


b. Automatically [Selection (one or more): lock the account or node for an [Assignment: organization-defined time period]; lock the account or node until released by an administrator; delay next logon prompt per [Assignment: organization-defined delay algorithm]; notify system administrator; take other [Assignment: organization-defined action]] when the maximum number of unsuccessful attempts is exceeded.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for the Google-managed infrastructure that hosts the system. [CONFIG_REQUIRED: Confirm in the Google Cloud {{ DOD_IMPACT_LABEL }} / {{ BASE_FEDRAMP_LABEL }} customer responsibility matrix whether AC-7 is inherited or shared; document customer-configured controls and verify Implementation Status] |
| **FedRAMP Additional Guidance**: Requirement: In alignment with NIST SP 800-63B. |


### AC-8 System Use Notification


a. Display [Assignment: organization-defined system use notification message or banner — FedRAMP High: see additional Requirements and Guidance] to users before granting access to the system that provides privacy and security notices consistent with applicable laws, executive orders, directives, regulations, policies, standards, and guidelines and state that:

  1. Users are accessing a U.S. Government system;

  2. System usage may be monitored, recorded, and subject to audit;

  3. Unauthorized use of the system is prohibited and subject to criminal and civil penalties; and

  4. Use of the system indicates consent to monitoring and recording;


b. Retain the notification message or banner on the screen until users acknowledge the usage conditions and take explicit actions to log on to or further access the system; and


c. For publicly accessible systems:

  1. Display system use information [Assignment: organization-defined conditions — FedRAMP High: see additional Requirements and Guidance], before granting further access to the publicly accessible system;

  2. Display references, if any, to monitoring, recording, or auditing that are consistent with privacy accommodations for such systems that generally prohibit those activities; and

  3. Include a description of the authorized uses of the system.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure identity backends and hypervisor isolation. Where configured in the system's Terraform blueprints, the platform enforces least-privilege IAM bindings, Identity-Aware Proxy (IAP) TCP/HTTPS forwarding, VPC Service Controls perimeters, and Google Organization Policy constraints. |
| **FedRAMP High Parameter Values**: `ac-08_odp.01` (system use notification): see additional Requirements and Guidance; `ac-08_odp.02` (conditions): see additional Requirements and Guidance<br>**FedRAMP Additional Guidance**: Requirement: The service provider shall determine elements of the cloud environment that require the System Use Notification control. The elements of the cloud environment that require System Use Notification are approved and accepted by the AO. Requirement: The service provider shall determine how System Use Notification is going to be verified and provide appropriate periodicity of the check. The System Use Notification verification and periodicity are approved and accepted by the AO. Requirement: If not performed as part of a Configuration Baseline check, then there must be documented agreement on how to provide results of verification and the necessary periodicity of the verification by the service provider. The documented agreement on how to provide verification of the results are approved and accepted by the AO. Guidance: If performed as part of a Configuration Baseline check, then the % of items requiring setting that are checked and that pass (or fail) check can be provided. |


### AC-10 Concurrent Session Control

Limit the number of concurrent sessions for each [Assignment: organization-defined account and/or account type] to [Assignment: organization-defined number — FedRAMP High: three (3) sessions for privileged access and two (2) sessions for non-privileged access].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for the Google-managed infrastructure that hosts the system. [CONFIG_REQUIRED: Confirm in the Google Cloud {{ DOD_IMPACT_LABEL }} / {{ BASE_FEDRAMP_LABEL }} customer responsibility matrix whether AC-10 is inherited or shared; document customer-configured controls and verify Implementation Status] |
| **FedRAMP High Parameter Values**: `ac-10_odp.02` (number): three (3) sessions for privileged access and two (2) sessions for non-privileged access |


### AC-11 Device Lock


a. Prevent further access to the system by [Selection (one or more): initiating a device lock after [Assignment: organization-defined time period — FedRAMP High: fifteen (15) minutes] of inactivity; requiring the user to initiate a device lock before leaving the system unattended]; and


b. Retain the device lock until the user reestablishes access using established identification and authentication procedures.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for the Google-managed infrastructure that hosts the system. [CONFIG_REQUIRED: Confirm in the Google Cloud {{ DOD_IMPACT_LABEL }} / {{ BASE_FEDRAMP_LABEL }} customer responsibility matrix whether AC-11 is inherited or shared; document customer-configured controls and verify Implementation Status] |
| **FedRAMP High Parameter Values**: `ac-11_odp.02` (time period): fifteen (15) minutes |


### AC-11(1) Device Lock | Pattern-hiding Displays

Conceal, via the device lock, information previously visible on the display with a publicly viewable image.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for the Google-managed infrastructure that hosts the system. [CONFIG_REQUIRED: Confirm in the Google Cloud {{ DOD_IMPACT_LABEL }} / {{ BASE_FEDRAMP_LABEL }} customer responsibility matrix whether AC-11(1) is inherited or shared; document customer-configured controls and verify Implementation Status] |


### AC-12 Session Termination

Automatically terminate a user session after [Assignment: organization-defined conditions or trigger events requiring session disconnect].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for the Google-managed infrastructure that hosts the system. [CONFIG_REQUIRED: Confirm in the Google Cloud {{ DOD_IMPACT_LABEL }} / {{ BASE_FEDRAMP_LABEL }} customer responsibility matrix whether AC-12 is inherited or shared; document customer-configured controls and verify Implementation Status] |


### AC-12(1) Session Termination | User-initiated Logouts

Provide a logout capability for user-initiated communications sessions whenever authentication is used to gain access to [Assignment: organization-defined information resources].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure identity backends and hypervisor isolation. Where configured in the system's Terraform blueprints, the platform enforces least-privilege IAM bindings, Identity-Aware Proxy (IAP) TCP/HTTPS forwarding, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### AC-12(2) Session Termination | Termination Message

Display an explicit logout message to users indicating the termination of authenticated communications sessions.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure identity backends and hypervisor isolation. Where configured in the system's Terraform blueprints, the platform enforces least-privilege IAM bindings, Identity-Aware Proxy (IAP) TCP/HTTPS forwarding, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### AC-14 Permitted Actions Without Identification or Authentication


a. Identify [Assignment: organization-defined user actions] that can be performed on the system without identification or authentication consistent with organizational mission and business functions; and


b. Document and provide supporting rationale in the security plan for the system, user actions not requiring identification or authentication.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure identity backends and hypervisor isolation. Where configured in the system's Terraform blueprints, the platform enforces least-privilege IAM bindings, Identity-Aware Proxy (IAP) TCP/HTTPS forwarding, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### AC-16 Security and Privacy Attributes


a. Provide the means to associate [Assignment: organization-defined types of security and privacy attributes] with [Assignment: organization-defined security and privacy attribute values] for information in storage, in process, and/or in transmission;


b. Ensure that the attribute associations are made and retained with the information;


c. Establish the following permitted security and privacy attributes from the attributes defined in AC-16a for [Assignment: organization-defined systems]: [Assignment: organization-defined security and privacy attributes];


d. Determine the following permitted attribute values or ranges for each of the established attributes: [Assignment: organization-defined attribute values or ranges for established attributes];


e. Audit changes to attributes; and


f. Review [Assignment: organization-defined security and privacy attributes] for applicability [Assignment: organization-defined frequency].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure identity backends and hypervisor isolation. Where configured in the system's Terraform blueprints, the platform enforces least-privilege IAM bindings, Identity-Aware Proxy (IAP) TCP/HTTPS forwarding, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### AC-16(6) Security and Privacy Attributes | Maintenance of Attribute Association

Require personnel to associate and maintain the association of [Assignment: organization-defined security and privacy attributes] with [Assignment: organization-defined subjects and objects] in accordance with [Assignment: organization-defined security and privacy policies].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure identity backends and hypervisor isolation. Where configured in the system's Terraform blueprints, the platform enforces least-privilege IAM bindings, Identity-Aware Proxy (IAP) TCP/HTTPS forwarding, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### AC-16(7) Security and Privacy Attributes | Consistent Attribute Interpretation

Provide a consistent interpretation of security and privacy attributes transmitted between distributed system components.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure identity backends and hypervisor isolation. Where configured in the system's Terraform blueprints, the platform enforces least-privilege IAM bindings, Identity-Aware Proxy (IAP) TCP/HTTPS forwarding, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### AC-17 Remote Access


a. Establish and document usage restrictions, configuration/connection requirements, and implementation guidance for each type of remote access allowed; and


b. Authorize each type of remote access to the system prior to allowing such connections.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure identity backends and hypervisor isolation. Where configured in the system's Terraform blueprints, the platform enforces least-privilege IAM bindings, Identity-Aware Proxy (IAP) TCP/HTTPS forwarding, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### AC-17(1) Remote Access | Monitoring and Control

Employ automated mechanisms to monitor and control remote access methods.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure identity backends and hypervisor isolation. Where configured in the system's Terraform blueprints, the platform enforces least-privilege IAM bindings, Identity-Aware Proxy (IAP) TCP/HTTPS forwarding, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### AC-17(2) Remote Access | Protection of Confidentiality and Integrity Using Encryption

Implement cryptographic mechanisms to protect the confidentiality and integrity of remote access sessions.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure identity backends and hypervisor isolation. Where configured in the system's Terraform blueprints, the platform enforces least-privilege IAM bindings, Identity-Aware Proxy (IAP) TCP/HTTPS forwarding, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### AC-17(3) Remote Access | Managed Access Control Points

Route remote accesses through authorized and managed network access control points.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure identity backends and hypervisor isolation. Where configured in the system's Terraform blueprints, the platform enforces least-privilege IAM bindings, Identity-Aware Proxy (IAP) TCP/HTTPS forwarding, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### AC-17(4) Remote Access | Privileged Commands and Access


(a) Authorize the execution of privileged commands and access to security-relevant information via remote access only in a format that provides assessable evidence and for the following needs: [Assignment: organization-defined needs]; and


(b) Document the rationale for remote access in the security plan for the system.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure identity backends and hypervisor isolation. Where configured in the system's Terraform blueprints, the platform enforces least-privilege IAM bindings, Identity-Aware Proxy (IAP) TCP/HTTPS forwarding, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### AC-17(6) Remote Access | Protection of Mechanism Information

Protect information about remote access mechanisms from unauthorized use and disclosure.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure identity backends and hypervisor isolation. Where configured in the system's Terraform blueprints, the platform enforces least-privilege IAM bindings, Identity-Aware Proxy (IAP) TCP/HTTPS forwarding, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### AC-17(9) Remote Access | Disconnect or Disable Access

Provide the capability to disconnect or disable remote access to the system within [Assignment: organization-defined time period].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure identity backends and hypervisor isolation. Where configured in the system's Terraform blueprints, the platform enforces least-privilege IAM bindings, Identity-Aware Proxy (IAP) TCP/HTTPS forwarding, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### AC-17(10) Remote Access | Authenticate Remote Commands

Implement [Assignment: organization-defined mechanisms] to authenticate [Assignment: organization-defined remote commands].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure identity backends and hypervisor isolation. Where configured in the system's Terraform blueprints, the platform enforces least-privilege IAM bindings, Identity-Aware Proxy (IAP) TCP/HTTPS forwarding, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### AC-18 Wireless Access


a. Establish configuration requirements, connection requirements, and implementation guidance for each type of wireless access; and


b. Authorize each type of wireless access to the system prior to allowing such connections.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for the Google-managed infrastructure that hosts the system. [CONFIG_REQUIRED: Confirm in the Google Cloud {{ DOD_IMPACT_LABEL }} / {{ BASE_FEDRAMP_LABEL }} customer responsibility matrix whether AC-18 is inherited or shared; document customer-configured controls and verify Implementation Status] |


### AC-18(1) Wireless Access | Authentication and Encryption

Protect wireless access to the system using authentication of [Selection (one or more): users; devices] and encryption.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for the Google-managed infrastructure that hosts the system. [CONFIG_REQUIRED: Confirm in the Google Cloud {{ DOD_IMPACT_LABEL }} / {{ BASE_FEDRAMP_LABEL }} customer responsibility matrix whether AC-18(1) is inherited or shared; document customer-configured controls and verify Implementation Status] |


### AC-18(3) Wireless Access | Disable Wireless Networking

Disable, when not intended for use, wireless networking capabilities embedded within system components prior to issuance and deployment.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for the Google-managed infrastructure that hosts the system. [CONFIG_REQUIRED: Confirm in the Google Cloud {{ DOD_IMPACT_LABEL }} / {{ BASE_FEDRAMP_LABEL }} customer responsibility matrix whether AC-18(3) is inherited or shared; document customer-configured controls and verify Implementation Status] |


### AC-18(4) Wireless Access | Restrict Configurations by Users

Identify and explicitly authorize users allowed to independently configure wireless networking capabilities.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for the Google-managed infrastructure that hosts the system. [CONFIG_REQUIRED: Confirm in the Google Cloud {{ DOD_IMPACT_LABEL }} / {{ BASE_FEDRAMP_LABEL }} customer responsibility matrix whether AC-18(4) is inherited or shared; document customer-configured controls and verify Implementation Status] |


### AC-18(5) Wireless Access | Antennas and Transmission Power Levels

Select radio antennas and calibrate transmission power levels to reduce the probability that signals from wireless access points can be received outside of organization-controlled boundaries.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for the Google-managed infrastructure that hosts the system. [CONFIG_REQUIRED: Confirm in the Google Cloud {{ DOD_IMPACT_LABEL }} / {{ BASE_FEDRAMP_LABEL }} customer responsibility matrix whether AC-18(5) is inherited or shared; document customer-configured controls and verify Implementation Status] |


### AC-19 Access Control for Mobile Devices


a. Establish configuration requirements, connection requirements, and implementation guidance for organization-controlled mobile devices, to include when such devices are outside of controlled areas; and


b. Authorize the connection of mobile devices to organizational systems.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for the Google-managed infrastructure that hosts the system. [CONFIG_REQUIRED: Confirm in the Google Cloud {{ DOD_IMPACT_LABEL }} / {{ BASE_FEDRAMP_LABEL }} customer responsibility matrix whether AC-19 is inherited or shared; document customer-configured controls and verify Implementation Status] |


### AC-19(5) Access Control for Mobile Devices | Full Device or Container-based Encryption

Employ [Selection: full-device encryption; container-based encryption] to protect the confidentiality and integrity of information on [Assignment: organization-defined mobile devices].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for the Google-managed infrastructure that hosts the system. [CONFIG_REQUIRED: Confirm in the Google Cloud {{ DOD_IMPACT_LABEL }} / {{ BASE_FEDRAMP_LABEL }} customer responsibility matrix whether AC-19(5) is inherited or shared; document customer-configured controls and verify Implementation Status] |


### AC-20 Use of External Systems

a. [Selection (one or more): Establish [Assignment: organization-defined terms and conditions]; Identify [Assignment: organization-defined controls asserted to be implemented on external systems]], consistent with the trust relationships established with other organizations owning, operating, and/or maintaining external systems, allowing authorized individuals to:

  1. Access the system from external systems; and

  2. Process, store, or transmit organization-controlled information using external systems; or


b. Prohibit the use of [Assignment: organizationally-defined types of external systems].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure identity backends and hypervisor isolation. Where configured in the system's Terraform blueprints, the platform enforces least-privilege IAM bindings, Identity-Aware Proxy (IAP) TCP/HTTPS forwarding, VPC Service Controls perimeters, and Google Organization Policy constraints. |
| **FedRAMP Additional Guidance**: Guidance: The interrelated controls of AC-20, CA-3, and SA-9 should be differentiated as follows: AC-20 describes system access to and from external systems. CA-3 describes documentation of an agreement between the respective system owners when data is exchanged between the CSO and an external system. SA-9 describes the responsibilities of external system owners. These responsibilities would typically be captured in the agreement required by CA-3. |


### AC-20(1) Use of External Systems | Limits on Authorized Use

Permit authorized individuals to use an external system to access the system or to process, store, or transmit organization-controlled information only after:


(a) Verification of the implementation of controls on the external system as specified in the organization's security and privacy policies and security and privacy plans; or


(b) Retention of approved system connection or processing agreements with the organizational entity hosting the external system.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure identity backends and hypervisor isolation. Where configured in the system's Terraform blueprints, the platform enforces least-privilege IAM bindings, Identity-Aware Proxy (IAP) TCP/HTTPS forwarding, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### AC-20(2) Use of External Systems | Portable Storage Devices — Restricted Use

Restrict the use of organization-controlled portable storage devices by authorized individuals on external systems using [Assignment: organization-defined restrictions].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure identity backends and hypervisor isolation. Where configured in the system's Terraform blueprints, the platform enforces least-privilege IAM bindings, Identity-Aware Proxy (IAP) TCP/HTTPS forwarding, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### AC-20(3) Use of External Systems | Non-organizationally Owned Systems — Restricted Use

Restrict the use of non-organizationally owned systems or system components to process, store, or transmit organizational information using [Assignment: organization-defined restrictions].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure identity backends and hypervisor isolation. Where configured in the system's Terraform blueprints, the platform enforces least-privilege IAM bindings, Identity-Aware Proxy (IAP) TCP/HTTPS forwarding, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### AC-21 Information Sharing


a. Enable authorized users to determine whether access authorizations assigned to a sharing partner match the information's access and use restrictions for [Assignment: organization-defined information sharing circumstances where user discretion is required]; and


b. Employ [Assignment: organization-defined automated mechanisms or manual processes] to assist users in making information sharing and collaboration decisions.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure identity backends and hypervisor isolation. Where configured in the system's Terraform blueprints, the platform enforces least-privilege IAM bindings, Identity-Aware Proxy (IAP) TCP/HTTPS forwarding, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### AC-22 Publicly Accessible Content


a. Designate individuals authorized to make information publicly accessible;


b. Train authorized individuals to ensure that publicly accessible information does not contain nonpublic information;


c. Review the proposed content of information prior to posting onto the publicly accessible system to ensure that nonpublic information is not included; and


d. Review the content on the publicly accessible system for nonpublic information [Assignment: organization-defined frequency — FedRAMP High: at least quarterly] and remove such information, if discovered.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure identity backends and hypervisor isolation. Where configured in the system's Terraform blueprints, the platform enforces least-privilege IAM bindings, Identity-Aware Proxy (IAP) TCP/HTTPS forwarding, VPC Service Controls perimeters, and Google Organization Policy constraints. |
| **FedRAMP High Parameter Values**: `ac-22_odp` (frequency): at least quarterly |


### AC-23 Data Mining Protection

Employ [Assignment: organization-defined data mining prevention and detection techniques] for [Assignment: organization-defined data storage objects] to detect and protect against unauthorized data mining.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure identity backends and hypervisor isolation. Where configured in the system's Terraform blueprints, the platform enforces least-privilege IAM bindings, Identity-Aware Proxy (IAP) TCP/HTTPS forwarding, VPC Service Controls perimeters, and Google Organization Policy constraints. |


## 2.2 Awareness and Training


### AT-1 Policy and Procedures


a. Develop, document, and disseminate to [Assignment: organization-defined personnel or roles]:

  1. [Selection (one or more): Organization-level; Mission/business process-level; System-level] awareness and training policy that:

    (a) Addresses purpose, scope, roles, responsibilities, management commitment, coordination among organizational entities, and compliance; and

    (b) Is consistent with applicable laws, executive orders, directives, regulations, policies, standards, and guidelines; and

  2. Procedures to facilitate the implementation of the awareness and training policy and the associated awareness and training controls;


b. Designate an [Assignment: organization-defined official] to manage the development, documentation, and dissemination of the awareness and training policy and procedures; and


c. Review and update the current awareness and training:

  1. Policy [Assignment: organization-defined frequency — FedRAMP High: at least annually] and following [Assignment: organization-defined events — FedRAMP High: significant changes]; and

  2. Procedures [Assignment: organization-defined frequency — FedRAMP High: at least annually] and following [Assignment: organization-defined events].


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC provides mandatory security and privacy awareness training for all Google personnel supporting Google Cloud infrastructure (Inherited). {{ ORGANIZATION }} provides role-based RMF compliance and security training for system administrators and users. |
| **FedRAMP High Parameter Values**: `at-01_odp.05` (frequency): at least annually; `at-01_odp.07` (frequency): at least annually; `at-01_odp.08` (events): significant changes |


### AT-2 Literacy Training and Awareness


a. Provide security and privacy literacy training to system users (including managers, senior executives, and contractors):

  1. As part of initial training for new users and [Assignment: organization-defined frequency — FedRAMP High: at least annually] thereafter; and

  2. When required by system changes or following [Assignment: organization-defined events];


b. Employ the following techniques to increase the security and privacy awareness of system users [Assignment: organization-defined awareness techniques];


c. Update literacy training and awareness content [Assignment: organization-defined frequency — FedRAMP High: at least annually] and following [Assignment: organization-defined events]; and


d. Incorporate lessons learned from internal or external security incidents or breaches into literacy training and awareness techniques.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC provides mandatory security and privacy awareness training for all Google personnel supporting Google Cloud infrastructure (Inherited). {{ ORGANIZATION }} provides role-based RMF compliance and security training for system administrators and users. |
| **FedRAMP High Parameter Values**: `at-02_odp.01` (frequency): at least annually; `at-02_odp.02` (frequency): at least annually; `at-02_odp.06` (frequency): at least annually |


### AT-2(2) Literacy Training and Awareness | Insider Threat

Provide literacy training on recognizing and reporting potential indicators of insider threat.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC provides mandatory security and privacy awareness training for all Google personnel supporting Google Cloud infrastructure (Inherited). {{ ORGANIZATION }} provides role-based RMF compliance and security training for system administrators and users. |


### AT-2(3) Literacy Training and Awareness | Social Engineering and Mining

Provide literacy training on recognizing and reporting potential and actual instances of social engineering and social mining.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC provides mandatory security and privacy awareness training for all Google personnel supporting Google Cloud infrastructure (Inherited). {{ ORGANIZATION }} provides role-based RMF compliance and security training for system administrators and users. |


### AT-2(4) Literacy Training and Awareness | Suspicious Communications and Anomalous System Behavior

Provide literacy training on recognizing suspicious communications and anomalous behavior in organizational systems using [Assignment: organization-defined indicators of malicious code].


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC provides mandatory security and privacy awareness training for all Google personnel supporting Google Cloud infrastructure (Inherited). {{ ORGANIZATION }} provides role-based RMF compliance and security training for system administrators and users. |


### AT-2(5) Literacy Training and Awareness | Advanced Persistent Threat

Provide literacy training on the advanced persistent threat.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC provides mandatory security and privacy awareness training for all Google personnel supporting Google Cloud infrastructure (Inherited). {{ ORGANIZATION }} provides role-based RMF compliance and security training for system administrators and users. |


### AT-2(6) Literacy Training and Awareness | Cyber Threat Environment


(a) Provide literacy training on the cyber threat environment; and


(b) Reflect current cyber threat information in system operations.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC provides mandatory security and privacy awareness training for all Google personnel supporting Google Cloud infrastructure (Inherited). {{ ORGANIZATION }} provides role-based RMF compliance and security training for system administrators and users. |


### AT-3 Role-based Training


a. Provide role-based security and privacy training to personnel with the following roles and responsibilities: [Assignment: organization-defined roles and responsibilities]:

  1. Before authorizing access to the system, information, or performing assigned duties, and [Assignment: organization-defined frequency — FedRAMP High: at least annually] thereafter; and

  2. When required by system changes;


b. Update role-based training content [Assignment: organization-defined frequency — FedRAMP High: at least annually] and following [Assignment: organization-defined events]; and


c. Incorporate lessons learned from internal or external security incidents or breaches into role-based training.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC provides mandatory security and privacy awareness training for all Google personnel supporting Google Cloud infrastructure (Inherited). {{ ORGANIZATION }} provides role-based RMF compliance and security training for system administrators and users. |
| **FedRAMP High Parameter Values**: `at-03_odp.03` (frequency): at least annually; `at-03_odp.04` (frequency): at least annually |


### AT-3(1) Role-based Training | Environmental Controls

Provide [Assignment: organization-defined personnel or roles] with initial and [Assignment: organization-defined frequency] training in the employment and operation of environmental controls.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC provides mandatory security and privacy awareness training for all Google personnel supporting Google Cloud infrastructure (Inherited). {{ ORGANIZATION }} provides role-based RMF compliance and security training for system administrators and users. |


### AT-3(2) Role-based Training | Physical Security Controls

Provide [Assignment: organization-defined personnel or roles] with initial and [Assignment: organization-defined frequency] training in the employment and operation of physical security controls.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC provides mandatory security and privacy awareness training for all Google personnel supporting Google Cloud infrastructure (Inherited). {{ ORGANIZATION }} provides role-based RMF compliance and security training for system administrators and users. |


### AT-3(5) Role-based Training | Processing Personally Identifiable Information

Provide [Assignment: organization-defined personnel or roles] with initial and [Assignment: organization-defined frequency] training in the employment and operation of personally identifiable information processing and transparency controls.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) & Privacy Official |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [x] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud infrastructure. [CONFIG_REQUIRED: Document the Mission Owner implementation and verification procedures for AT-3(5) (Processing Personally Identifiable Information) within the {{ DOD_IMPACT_LABEL }} boundary and confirm Implementation Status] |


### AT-4 Training Records


a. Document and monitor information security and privacy training activities, including security and privacy awareness training and specific role-based security and privacy training; and


b. Retain individual training records for [Assignment: organization-defined time period — FedRAMP High: five (5) years or 5 years after completion of a specific training program].


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC provides mandatory security and privacy awareness training for all Google personnel supporting Google Cloud infrastructure (Inherited). {{ ORGANIZATION }} provides role-based RMF compliance and security training for system administrators and users. |
| **FedRAMP High Parameter Values**: `at-04_odp` (time period): five (5) years or 5 years after completion of a specific training program |


### AT-6 Training Feedback

Provide feedback on organizational training results to the following personnel [Assignment: organization-defined frequency]: [Assignment: organization-defined personnel].


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC provides mandatory security and privacy awareness training for all Google personnel supporting Google Cloud infrastructure (Inherited). {{ ORGANIZATION }} provides role-based RMF compliance and security training for system administrators and users. |


## 2.3 Audit and Accountability


### AU-1 Policy and Procedures


a. Develop, document, and disseminate to [Assignment: organization-defined personnel or roles]:

  1. [Selection (one or more): Organization-level; Mission/business process-level; System-level] audit and accountability policy that:

    (a) Addresses purpose, scope, roles, responsibilities, management commitment, coordination among organizational entities, and compliance; and

    (b) Is consistent with applicable laws, executive orders, directives, regulations, policies, standards, and guidelines; and

  2. Procedures to facilitate the implementation of the audit and accountability policy and the associated audit and accountability controls;


b. Designate an [Assignment: organization-defined official] to manage the development, documentation, and dissemination of the audit and accountability policy and procedures; and


c. Review and update the current audit and accountability:

  1. Policy [Assignment: organization-defined frequency — FedRAMP High: at least annually] and following [Assignment: organization-defined events — FedRAMP High: significant changes]; and

  2. Procedures [Assignment: organization-defined frequency — FedRAMP High: at least annually] and following [Assignment: organization-defined events].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud audit infrastructure and Cloud Audit Logs backend. Where configured in the system's Terraform blueprints, Cloud Logging audit sinks export immutable log records to retention buckets and {{ SIEM_TOOL }} with alerting via {{ TELEMETRY_PIPELINE }} and {{ THREAT_DETECTION_ENGINE }}. |
| **FedRAMP High Parameter Values**: `au-01_odp.05` (frequency): at least annually; `au-01_odp.07` (frequency): at least annually; `au-01_odp.08` (events): significant changes |


### AU-2 Event Logging


a. Identify the types of events that the system is capable of logging in support of the audit function: [Assignment: organization-defined event types that the system is capable of logging — FedRAMP High: successful and unsuccessful account logon events, account management events, object access, policy change, privilege functions, process tracking, and system events. For Web applications: all administrator activity, authentication checks, authorization checks, data deletions, data access, data changes, and permission changes];


b. Coordinate the event logging function with other organizational entities requiring audit-related information to guide and inform the selection criteria for events to be logged;


c. Specify the following event types for logging within the system: [Assignment: organization-defined event types (subset of the event types defined in AU-2a.) along with the frequency of (or situation requiring) logging for each identified event type];


d. Provide a rationale for why the event types selected for logging are deemed to be adequate to support after-the-fact investigations of incidents; and


e. Review and update the event types selected for logging [Assignment: organization-defined frequency — FedRAMP High: annually and whenever there is a change in the threat environment].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud audit infrastructure and Cloud Audit Logs backend. Where configured in the system's Terraform blueprints, Cloud Logging audit sinks export immutable log records to retention buckets and {{ SIEM_TOOL }} with alerting via {{ TELEMETRY_PIPELINE }} and {{ THREAT_DETECTION_ENGINE }}. |
| **FedRAMP High Parameter Values**: `au-02_odp.01` (event types): successful and unsuccessful account logon events, account management events, object access, policy change, privilege functions, process tracking, and system events. For Web applications: all administrator activity, authentication checks, authorization checks, data deletions, data access, data changes, and permission changes; `au-02_odp.02` (event types (subset of AU-02_ODP\[01\])): organization-defined subset of the auditable events defined in AU-2a to be audited continually for each identified event.; `au-02_odp.03` (frequency or situation): organization-defined subset of the auditable events defined in AU-2a to be audited continually for each identified event.; `au-02_odp.04` (frequency): annually and whenever there is a change in the threat environment<br>**FedRAMP Additional Guidance**: Requirement: Coordination between service provider and consumer shall be documented and accepted by the AO. (e) Guidance: Annually or whenever changes in the threat environment are communicated to the service provider by the AO. |


### AU-3 Content of Audit Records

Ensure that audit records contain information that establishes the following:


a. What type of event occurred;


b. When the event occurred;


c. Where the event occurred;


d. Source of the event;


e. Outcome of the event; and


f. Identity of any individuals, subjects, or objects/entities associated with the event.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud audit infrastructure and Cloud Audit Logs backend. Where configured in the system's Terraform blueprints, Cloud Logging audit sinks export immutable log records to retention buckets and {{ SIEM_TOOL }} with alerting via {{ TELEMETRY_PIPELINE }} and {{ THREAT_DETECTION_ENGINE }}. |


### AU-3(1) Content of Audit Records | Additional Audit Information

Generate audit records containing the following additional information: [Assignment: organization-defined additional information — FedRAMP High: session, connection, transaction, or activity duration; for client-server transactions, the number of bytes received and bytes sent; additional informational messages to diagnose or identify the event; characteristics that describe or identify the object or resource being acted upon; individual identities of group account users; full-text of privileged commands].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud audit infrastructure and Cloud Audit Logs backend. Where configured in the system's Terraform blueprints, Cloud Logging audit sinks export immutable log records to retention buckets and {{ SIEM_TOOL }} with alerting via {{ TELEMETRY_PIPELINE }} and {{ THREAT_DETECTION_ENGINE }}. |
| **FedRAMP High Parameter Values**: `au-03.01_odp` (additional information): session, connection, transaction, or activity duration; for client-server transactions, the number of bytes received and bytes sent; additional informational messages to diagnose or identify the event; characteristics that describe or identify the object or resource being acted upon; individual identities of group account users; full-text of privileged commands<br>**FedRAMP Additional Guidance**: Guidance: For client-server transactions, the number of bytes sent and received gives bidirectional transfer information that can be helpful during an investigation or inquiry. |


### AU-3(3) Content of Audit Records | Limit Personally Identifiable Information Elements

Limit personally identifiable information contained in audit records to the following elements identified in the privacy risk assessment: [Assignment: organization-defined elements].


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [x] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud infrastructure. [CONFIG_REQUIRED: Document the Mission Owner implementation and verification procedures for AU-3(3) (Limit Personally Identifiable Information Elements) within the {{ DOD_IMPACT_LABEL }} boundary and confirm Implementation Status] |


### AU-4 Audit Log Storage Capacity

Allocate audit log storage capacity to accommodate [Assignment: organization-defined audit log retention requirements].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud audit infrastructure and Cloud Audit Logs backend. Where configured in the system's Terraform blueprints, Cloud Logging audit sinks export immutable log records to retention buckets and {{ SIEM_TOOL }} with alerting via {{ TELEMETRY_PIPELINE }} and {{ THREAT_DETECTION_ENGINE }}. |


### AU-4(1) Audit Log Storage Capacity | Transfer to Alternate Storage

Transfer audit logs [Assignment: organization-defined frequency] to a different system, system component, or media other than the system or system component conducting the logging.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud audit infrastructure and Cloud Audit Logs backend. Where configured in the system's Terraform blueprints, Cloud Logging audit sinks export immutable log records to retention buckets and {{ SIEM_TOOL }} with alerting via {{ TELEMETRY_PIPELINE }} and {{ THREAT_DETECTION_ENGINE }}. |


### AU-5 Response to Audit Logging Process Failures


a. Alert [Assignment: organization-defined personnel or roles] within [Assignment: organization-defined time period] in the event of an audit logging process failure; and


b. Take the following additional actions: [Assignment: organization-defined additional actions — FedRAMP High: overwrite oldest record].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud audit infrastructure and Cloud Audit Logs backend. Where configured in the system's Terraform blueprints, Cloud Logging audit sinks export immutable log records to retention buckets and {{ SIEM_TOOL }} with alerting via {{ TELEMETRY_PIPELINE }} and {{ THREAT_DETECTION_ENGINE }}. |
| **FedRAMP High Parameter Values**: `au-05_odp.03` (additional actions): overwrite oldest record |


### AU-5(1) Response to Audit Logging Process Failures | Storage Capacity Warning

Provide a warning to [Assignment: organization-defined personnel, roles, and/or locations] within [Assignment: organization-defined time period] when allocated audit log storage volume reaches [Assignment: organization-defined percentage — FedRAMP High: 75%, or one month before expected negative impact] of repository maximum audit log storage capacity.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud audit infrastructure and Cloud Audit Logs backend. Where configured in the system's Terraform blueprints, Cloud Logging audit sinks export immutable log records to retention buckets and {{ SIEM_TOOL }} with alerting via {{ TELEMETRY_PIPELINE }} and {{ THREAT_DETECTION_ENGINE }}. |
| **FedRAMP High Parameter Values**: `au-05.01_odp.03` (percentage): 75%, or one month before expected negative impact |


### AU-5(2) Response to Audit Logging Process Failures | Real-time Alerts

Provide an alert within [Assignment: organization-defined real-time period — FedRAMP High: real-time] to [Assignment: organization-defined personnel, roles, and/or locations — FedRAMP High: service provider personnel with authority to address failed audit events] when the following audit failure events occur: [Assignment: organization-defined audit logging failure events requiring real-time alerts — FedRAMP High: audit failure events requiring real-time alerts, as defined by organization audit policy].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud audit infrastructure and Cloud Audit Logs backend. Where configured in the system's Terraform blueprints, Cloud Logging audit sinks export immutable log records to retention buckets and {{ SIEM_TOOL }} with alerting via {{ TELEMETRY_PIPELINE }} and {{ THREAT_DETECTION_ENGINE }}. |
| **FedRAMP High Parameter Values**: `au-05.02_odp.01` (real-time period): real-time; `au-05.02_odp.02` (personnel, roles, and/or locations): service provider personnel with authority to address failed audit events; `au-05.02_odp.03` (audit logging failure events requiring real-time alerts): audit failure events requiring real-time alerts, as defined by organization audit policy |


### AU-6 Audit Record Review, Analysis, and Reporting


a. Review and analyze system audit records [Assignment: organization-defined frequency — FedRAMP High: at least weekly] for indications of [Assignment: organization-defined inappropriate or unusual activity] and the potential impact of the inappropriate or unusual activity;


b. Report findings to [Assignment: organization-defined personnel or roles]; and


c. Adjust the level of audit record review, analysis, and reporting within the system when there is a change in risk based on law enforcement information, intelligence information, or other credible sources of information.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud audit infrastructure and Cloud Audit Logs backend. Where configured in the system's Terraform blueprints, Cloud Logging audit sinks export immutable log records to retention buckets and {{ SIEM_TOOL }} with alerting via {{ TELEMETRY_PIPELINE }} and {{ THREAT_DETECTION_ENGINE }}. |
| **FedRAMP High Parameter Values**: `au-06_odp.01` (frequency): at least weekly<br>**FedRAMP Additional Guidance**: Requirement: Coordination between service provider and consumer shall be documented and accepted by the AO. In multi-tenant environments, capability and means for providing review, analysis, and reporting to consumer for data pertaining to consumer shall be documented. |


### AU-6(1) Audit Record Review, Analysis, and Reporting | Automated Process Integration

Integrate audit record review, analysis, and reporting processes using [Assignment: organization-defined automated mechanisms].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud audit infrastructure and Cloud Audit Logs backend. Where configured in the system's Terraform blueprints, Cloud Logging audit sinks export immutable log records to retention buckets and {{ SIEM_TOOL }} with alerting via {{ TELEMETRY_PIPELINE }} and {{ THREAT_DETECTION_ENGINE }}. |


### AU-6(3) Audit Record Review, Analysis, and Reporting | Correlate Audit Record Repositories

Analyze and correlate audit records across different repositories to gain organization-wide situational awareness.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud audit infrastructure and Cloud Audit Logs backend. Where configured in the system's Terraform blueprints, Cloud Logging audit sinks export immutable log records to retention buckets and {{ SIEM_TOOL }} with alerting via {{ TELEMETRY_PIPELINE }} and {{ THREAT_DETECTION_ENGINE }}. |


### AU-6(4) Audit Record Review, Analysis, and Reporting | Central Review and Analysis

Provide and implement the capability to centrally review and analyze audit records from multiple components within the system.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud audit infrastructure and Cloud Audit Logs backend. Where configured in the system's Terraform blueprints, Cloud Logging audit sinks export immutable log records to retention buckets and {{ SIEM_TOOL }} with alerting via {{ TELEMETRY_PIPELINE }} and {{ THREAT_DETECTION_ENGINE }}. |


### AU-6(5) Audit Record Review, Analysis, and Reporting | Integrated Analysis of Audit Records

Integrate analysis of audit records with analysis of [Selection (one or more): vulnerability scanning information; performance data; system monitoring information; [Assignment: organization-defined data/information collected from other sources — FedRAMP High: vulnerability scanning information; performance data; information system monitoring information; penetration test data; (au-06.05_odp.02)]] to further enhance the ability to identify inappropriate or unusual activity.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud audit infrastructure and Cloud Audit Logs backend. Where configured in the system's Terraform blueprints, Cloud Logging audit sinks export immutable log records to retention buckets and {{ SIEM_TOOL }} with alerting via {{ TELEMETRY_PIPELINE }} and {{ THREAT_DETECTION_ENGINE }}. |
| **FedRAMP High Parameter Values**: `au-06.05_odp.01`: vulnerability scanning information; performance data; information system monitoring information; penetration test data; (au-06.05_odp.02) |


### AU-6(6) Audit Record Review, Analysis, and Reporting | Correlation with Physical Monitoring

Correlate information from audit records with information obtained from monitoring physical access to further enhance the ability to identify suspicious, inappropriate, unusual, or malevolent activity.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud audit infrastructure and Cloud Audit Logs backend. Where configured in the system's Terraform blueprints, Cloud Logging audit sinks export immutable log records to retention buckets and {{ SIEM_TOOL }} with alerting via {{ TELEMETRY_PIPELINE }} and {{ THREAT_DETECTION_ENGINE }}. |
| **FedRAMP Additional Guidance**: Requirement: Coordination between service provider and consumer shall be documented and accepted by the AO. |


### AU-6(7) Audit Record Review, Analysis, and Reporting | Permitted Actions

Specify the permitted actions for each [Selection (one or more): system process; role; user — FedRAMP High: information system process; role; user] associated with the review, analysis, and reporting of audit record information.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for the Google Cloud audit infrastructure and Cloud Audit Logs backend. Where configured in the system's Terraform blueprints, Cloud Logging audit sinks export immutable log records to retention buckets and {{ SIEM_TOOL }} with alerting via {{ TELEMETRY_PIPELINE }} and {{ THREAT_DETECTION_ENGINE }}. |
| **FedRAMP High Parameter Values**: `au-06.07_odp`: information system process; role; user |


### AU-7 Audit Record Reduction and Report Generation

Provide and implement an audit record reduction and report generation capability that:


a. Supports on-demand audit record review, analysis, and reporting requirements and after-the-fact investigations of incidents; and


b. Does not alter the original content or time ordering of audit records.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for the Google-managed infrastructure that hosts the system. [CONFIG_REQUIRED: Confirm in the Google Cloud {{ DOD_IMPACT_LABEL }} / {{ BASE_FEDRAMP_LABEL }} customer responsibility matrix whether AU-7 is inherited or shared; document customer-configured controls and verify Implementation Status] |


### AU-7(1) Audit Record Reduction and Report Generation | Automatic Processing

Provide and implement the capability to process, sort, and search audit records for events of interest based on the following content: [Assignment: organization-defined fields within audit records].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud audit infrastructure and Cloud Audit Logs backend. Where configured in the system's Terraform blueprints, Cloud Logging audit sinks export immutable log records to retention buckets and {{ SIEM_TOOL }} with alerting via {{ TELEMETRY_PIPELINE }} and {{ THREAT_DETECTION_ENGINE }}. |


### AU-8 Time Stamps


a. Use internal system clocks to generate time stamps for audit records; and


b. Record time stamps for audit records that meet [Assignment: organization-defined granularity of time measurement — FedRAMP High: one second granularity of time measurement] and that use Coordinated Universal Time, have a fixed local time offset from Coordinated Universal Time, or that include the local time offset as part of the time stamp.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for the Google-managed infrastructure that hosts the system. [CONFIG_REQUIRED: Confirm in the Google Cloud {{ DOD_IMPACT_LABEL }} / {{ BASE_FEDRAMP_LABEL }} customer responsibility matrix whether AU-8 is inherited or shared; document customer-configured controls and verify Implementation Status] |
| **FedRAMP High Parameter Values**: `au-08_odp` (granularity of time measurement): one second granularity of time measurement |


### AU-9 Protection of Audit Information


a. Protect audit information and audit logging tools from unauthorized access, modification, and deletion; and


b. Alert [Assignment: organization-defined personnel or roles] upon detection of unauthorized access, modification, or deletion of audit information.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud audit infrastructure and Cloud Audit Logs backend. Where configured in the system's Terraform blueprints, Cloud Logging audit sinks export immutable log records to retention buckets and {{ SIEM_TOOL }} with alerting via {{ TELEMETRY_PIPELINE }} and {{ THREAT_DETECTION_ENGINE }}. |


### AU-9(2) Protection of Audit Information | Store on Separate Physical Systems or Components

Store audit records [Assignment: organization-defined frequency — FedRAMP High: at least weekly] in a repository that is part of a physically different system or system component than the system or component being audited.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud audit infrastructure and Cloud Audit Logs backend. Where configured in the system's Terraform blueprints, Cloud Logging audit sinks export immutable log records to retention buckets and {{ SIEM_TOOL }} with alerting via {{ TELEMETRY_PIPELINE }} and {{ THREAT_DETECTION_ENGINE }}. |
| **FedRAMP High Parameter Values**: `au-09.02_odp` (frequency): at least weekly |


### AU-9(3) Protection of Audit Information | Cryptographic Protection

Implement cryptographic mechanisms to protect the integrity of audit information and audit tools.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud audit infrastructure and Cloud Audit Logs backend. Where configured in the system's Terraform blueprints, Cloud Logging audit sinks export immutable log records to retention buckets and {{ SIEM_TOOL }} with alerting via {{ TELEMETRY_PIPELINE }} and {{ THREAT_DETECTION_ENGINE }}. |
| **FedRAMP Additional Guidance**: Guidance: Note that this enhancement requires the use of cryptography which must be compliant with Federal requirements and utilize FIPS validated or NSA approved cryptography (see SC-13.) |


### AU-9(4) Protection of Audit Information | Access by Subset of Privileged Users

Authorize access to management of audit logging functionality to only [Assignment: organization-defined subset of privileged users or roles].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud audit infrastructure and Cloud Audit Logs backend. Where configured in the system's Terraform blueprints, Cloud Logging audit sinks export immutable log records to retention buckets and {{ SIEM_TOOL }} with alerting via {{ TELEMETRY_PIPELINE }} and {{ THREAT_DETECTION_ENGINE }}. |


### AU-9(5) Protection of Audit Information | Dual Authorization

Enforce dual authorization for [Selection (one or more): movement; deletion] of [Assignment: organization-defined audit information].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud audit infrastructure and Cloud Audit Logs backend. Where configured in the system's Terraform blueprints, Cloud Logging audit sinks export immutable log records to retention buckets and {{ SIEM_TOOL }} with alerting via {{ TELEMETRY_PIPELINE }} and {{ THREAT_DETECTION_ENGINE }}. |


### AU-9(6) Protection of Audit Information | Read-only Access

Authorize read-only access to audit information to [Assignment: organization-defined subset of privileged users or roles].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud audit infrastructure and Cloud Audit Logs backend. Where configured in the system's Terraform blueprints, Cloud Logging audit sinks export immutable log records to retention buckets and {{ SIEM_TOOL }} with alerting via {{ TELEMETRY_PIPELINE }} and {{ THREAT_DETECTION_ENGINE }}. |


### AU-10 Non-repudiation

Provide irrefutable evidence that an individual (or process acting on behalf of an individual) has performed [Assignment: organization-defined actions to be covered by non-repudiation — FedRAMP High: minimum actions including the addition, modification, deletion, approval, sending, or receiving of data].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for the Google-managed infrastructure that hosts the system. [CONFIG_REQUIRED: Confirm in the Google Cloud {{ DOD_IMPACT_LABEL }} / {{ BASE_FEDRAMP_LABEL }} customer responsibility matrix whether AU-10 is inherited or shared; document customer-configured controls and verify Implementation Status] |
| **FedRAMP High Parameter Values**: `au-10_odp` (actions): minimum actions including the addition, modification, deletion, approval, sending, or receiving of data |


### AU-11 Audit Record Retention

Retain audit records for [Assignment: organization-defined time period consistent with records retention policy — FedRAMP High: a time period in compliance with M-21-31] to provide support for after-the-fact investigations of incidents and to meet regulatory and organizational information retention requirements.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud audit infrastructure and Cloud Audit Logs backend. Where configured in the system's Terraform blueprints, Cloud Logging audit sinks export immutable log records to retention buckets and {{ SIEM_TOOL }} with alerting via {{ TELEMETRY_PIPELINE }} and {{ THREAT_DETECTION_ENGINE }}. |
| **FedRAMP High Parameter Values**: `au-11_odp` (time period): a time period in compliance with M-21-31<br>**FedRAMP Additional Guidance**: Requirement: The service provider retains audit records on-line for at least ninety days and further preserves audit records off-line for a period that is in accordance with NARA requirements. Requirement: The service provider must support Agency requirements to comply with M-21-31 (https://www.whitehouse.gov/wp-content/uploads/2021/08/M-21-31-Improving-the-Federal-Governments-Investigative-and-Remediation-Capabilities-Related-to-Cybersecurity-Incidents.pdf) Guidance: The service provider is encouraged to align with M-21-31 where possible |


### AU-11(1) Audit Record Retention | Long-term Retrieval Capability

Employ [Assignment: organization-defined measures] to ensure that long-term audit records generated by the system can be retrieved.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud audit infrastructure and Cloud Audit Logs backend. Where configured in the system's Terraform blueprints, Cloud Logging audit sinks export immutable log records to retention buckets and {{ SIEM_TOOL }} with alerting via {{ TELEMETRY_PIPELINE }} and {{ THREAT_DETECTION_ENGINE }}. |


### AU-12 Audit Record Generation


a. Provide audit record generation capability for the event types the system is capable of auditing as defined in AU-2a on [Assignment: organization-defined system components — FedRAMP High: all information system and network components where audit capability is deployed/available];


b. Allow [Assignment: organization-defined personnel or roles] to select the event types that are to be logged by specific components of the system; and


c. Generate audit records for the event types defined in AU-2c that include the audit record content defined in AU-3.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud audit infrastructure and Cloud Audit Logs backend. Where configured in the system's Terraform blueprints, Cloud Logging audit sinks export immutable log records to retention buckets and {{ SIEM_TOOL }} with alerting via {{ TELEMETRY_PIPELINE }} and {{ THREAT_DETECTION_ENGINE }}. |
| **FedRAMP High Parameter Values**: `au-12_odp.01` (system components): all information system and network components where audit capability is deployed/available |


### AU-12(1) Audit Record Generation | System-wide and Time-correlated Audit Trail

Compile audit records from [Assignment: organization-defined system components — FedRAMP High: all network, data storage, and computing devices] into a system-wide (logical or physical) audit trail that is time-correlated to within [Assignment: organization-defined level of tolerance for the relationship between time stamps of individual records in the audit trail].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud audit infrastructure and Cloud Audit Logs backend. Where configured in the system's Terraform blueprints, Cloud Logging audit sinks export immutable log records to retention buckets and {{ SIEM_TOOL }} with alerting via {{ TELEMETRY_PIPELINE }} and {{ THREAT_DETECTION_ENGINE }}. |
| **FedRAMP High Parameter Values**: `au-12.01_odp.01` (system components): all network, data storage, and computing devices |


### AU-12(3) Audit Record Generation | Changes by Authorized Individuals

Provide and implement the capability for [Assignment: organization-defined individuals or roles — FedRAMP High: service provider-defined individuals or roles with audit configuration responsibilities] to change the logging to be performed on [Assignment: organization-defined system components — FedRAMP High: all network, data storage, and computing devices] based on [Assignment: organization-defined selectable event criteria] within [Assignment: organization-defined time thresholds].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud audit infrastructure and Cloud Audit Logs backend. Where configured in the system's Terraform blueprints, Cloud Logging audit sinks export immutable log records to retention buckets and {{ SIEM_TOOL }} with alerting via {{ TELEMETRY_PIPELINE }} and {{ THREAT_DETECTION_ENGINE }}. |
| **FedRAMP High Parameter Values**: `au-12.03_odp.01` (individuals or roles): service provider-defined individuals or roles with audit configuration responsibilities; `au-12.03_odp.02` (system components): all network, data storage, and computing devices |


### AU-14 Session Audit


a. Provide and implement the capability for [Assignment: organization-defined users or roles] to [Selection (one or more): record; view; hear; log] the content of a user session under [Assignment: organization-defined circumstances]; and


b. Develop, integrate, and use session auditing activities in consultation with legal counsel and in accordance with applicable laws, executive orders, directives, regulations, policies, standards, and guidelines.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud audit infrastructure and Cloud Audit Logs backend. Where configured in the system's Terraform blueprints, Cloud Logging audit sinks export immutable log records to retention buckets and {{ SIEM_TOOL }} with alerting via {{ TELEMETRY_PIPELINE }} and {{ THREAT_DETECTION_ENGINE }}. |


### AU-14(1) Session Audit | System Start-up

Initiate session audits automatically at system start-up.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud audit infrastructure and Cloud Audit Logs backend. Where configured in the system's Terraform blueprints, Cloud Logging audit sinks export immutable log records to retention buckets and {{ SIEM_TOOL }} with alerting via {{ TELEMETRY_PIPELINE }} and {{ THREAT_DETECTION_ENGINE }}. |


### AU-14(3) Session Audit | Remote Viewing and Listening

Provide and implement the capability for authorized users to remotely view and hear content related to an established user session in real time.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud audit infrastructure and Cloud Audit Logs backend. Where configured in the system's Terraform blueprints, Cloud Logging audit sinks export immutable log records to retention buckets and {{ SIEM_TOOL }} with alerting via {{ TELEMETRY_PIPELINE }} and {{ THREAT_DETECTION_ENGINE }}. |


### AU-16 Cross-organizational Audit Logging

Employ [Assignment: organization-defined methods] for coordinating [Assignment: organization-defined audit information] among external organizations when audit information is transmitted across organizational boundaries.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [x] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud infrastructure. [CONFIG_REQUIRED: Document the Mission Owner implementation and verification procedures for AU-16 (Cross-organizational Audit Logging) within the {{ DOD_IMPACT_LABEL }} boundary and confirm Implementation Status] |


### AU-16(1) Cross-organizational Audit Logging | Identity Preservation

Preserve the identity of individuals in cross-organizational audit trails.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [x] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud infrastructure. [CONFIG_REQUIRED: Document the Mission Owner implementation and verification procedures for AU-16(1) (Identity Preservation) within the {{ DOD_IMPACT_LABEL }} boundary and confirm Implementation Status] |


### AU-16(2) Cross-organizational Audit Logging | Sharing of Audit Information

Provide cross-organizational audit information to [Assignment: organization-defined organizations] based on [Assignment: organization-defined cross-organizational sharing agreements].


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [x] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud infrastructure. [CONFIG_REQUIRED: Document the Mission Owner implementation and verification procedures for AU-16(2) (Sharing of Audit Information) within the {{ DOD_IMPACT_LABEL }} boundary and confirm Implementation Status] |


## 2.4 Assessment, Authorization, and Monitoring


### CA-1 Policy and Procedures


a. Develop, document, and disseminate to [Assignment: organization-defined personnel or roles]:

  1. [Selection (one or more): Organization-level; Mission/business process-level; System-level] assessment, authorization, and monitoring policy that:

    (a) Addresses purpose, scope, roles, responsibilities, management commitment, coordination among organizational entities, and compliance; and

    (b) Is consistent with applicable laws, executive orders, directives, regulations, policies, standards, and guidelines; and

  2. Procedures to facilitate the implementation of the assessment, authorization, and monitoring policy and the associated assessment, authorization, and monitoring controls;


b. Designate an [Assignment: organization-defined official] to manage the development, documentation, and dissemination of the assessment, authorization, and monitoring policy and procedures; and


c. Review and update the current assessment, authorization, and monitoring:

  1. Policy [Assignment: organization-defined frequency — FedRAMP High: at least annually] and following [Assignment: organization-defined events — FedRAMP High: significant changes]; and

  2. Procedures [Assignment: organization-defined frequency — FedRAMP High: at least annually] and following [Assignment: organization-defined events].


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherits controls from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }}. The system platform enforces continuous monitoring through {{ THREAT_DETECTION_ENGINE }}, {{ SIEM_TOOL }}, and automated IaC drift analysis. Monitoring and control-effectiveness assessment are performed at the organization-defined frequency: {{ CONMON_REVIEW_FREQUENCY }}. Assessments are conducted as {{ CONMON_ASSESSMENT_TYPE }}, and security status, findings, and POA&M burndown are reported to the AO, ISSM, and ISSO through {{ GRC_TOOL_REFERENCE }}. |
| **FedRAMP High Parameter Values**: `ca-01_odp.05` (frequency): at least annually; `ca-01_odp.07` (frequency): at least annually; `ca-01_odp.08` (events): significant changes |


### CA-2 Control Assessments


a. Select the appropriate assessor or assessment team for the type of assessment to be conducted;


b. Develop a control assessment plan that describes the scope of the assessment including:

  1. Controls and control enhancements under assessment;

  2. Assessment procedures to be used to determine control effectiveness; and

  3. Assessment environment, assessment team, and assessment roles and responsibilities;


c. Ensure the control assessment plan is reviewed and approved by the authorizing official or designated representative prior to conducting the assessment;


d. Assess the controls in the system and its environment of operation [Assignment: organization-defined frequency — FedRAMP High: at least annually] to determine the extent to which the controls are implemented correctly, operating as intended, and producing the desired outcome with respect to meeting established security and privacy requirements;


e. Produce a control assessment report that document the results of the assessment; and


f. Provide the results of the control assessment to [Assignment: organization-defined individuals or roles — FedRAMP High: individuals or roles to include FedRAMP PMO].


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherits controls from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }}. The system platform enforces continuous monitoring through {{ THREAT_DETECTION_ENGINE }}, {{ SIEM_TOOL }}, and automated IaC drift analysis. Monitoring and control-effectiveness assessment are performed at the organization-defined frequency: {{ CONMON_REVIEW_FREQUENCY }}. Assessments are conducted as {{ CONMON_ASSESSMENT_TYPE }}, and security status, findings, and POA&M burndown are reported to the AO, ISSM, and ISSO through {{ GRC_TOOL_REFERENCE }}. |
| **FedRAMP High Parameter Values**: `ca-02_odp.01` (assessment frequency): at least annually; `ca-02_odp.02` (individuals or roles): individuals or roles to include FedRAMP PMO<br>**FedRAMP Additional Guidance**: Guidance: Reference FedRAMP Annual Assessment Guidance. |


### CA-2(1) Control Assessments | Independent Assessors

Employ independent assessors or assessment teams to conduct control assessments.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherits controls from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }}. The system platform enforces continuous monitoring through {{ THREAT_DETECTION_ENGINE }}, {{ SIEM_TOOL }}, and automated IaC drift analysis. Monitoring and control-effectiveness assessment are performed at the organization-defined frequency: {{ CONMON_REVIEW_FREQUENCY }}. Assessments are conducted as {{ CONMON_ASSESSMENT_TYPE }}, and security status, findings, and POA&M burndown are reported to the AO, ISSM, and ISSO through {{ GRC_TOOL_REFERENCE }}. |


### CA-2(2) Control Assessments | Specialized Assessments

Include as part of control assessments, [Assignment: organization-defined frequency — FedRAMP High: at least annually], [Selection: announced; unannounced], [Selection (one or more): in-depth monitoring; security instrumentation; automated security test cases; vulnerability scanning; malicious user testing; insider threat assessment; performance and load testing; data leakage or data loss assessment; [Assignment: organization-defined other forms of assessment]].


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherits controls from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }}. The system platform enforces continuous monitoring through {{ THREAT_DETECTION_ENGINE }}, {{ SIEM_TOOL }}, and automated IaC drift analysis. Monitoring and control-effectiveness assessment are performed at the organization-defined frequency: {{ CONMON_REVIEW_FREQUENCY }}. Assessments are conducted as {{ CONMON_ASSESSMENT_TYPE }}, and security status, findings, and POA&M burndown are reported to the AO, ISSM, and ISSO through {{ GRC_TOOL_REFERENCE }}. |
| **FedRAMP High Parameter Values**: `ca-02.02_odp.01` (specialized assessment frequency): at least annually<br>**FedRAMP Additional Guidance**: Requirement: To include 'announced', 'vulnerability scanning' |


### CA-2(3) Control Assessments | Leveraging Results from External Organizations

Leverage the results of control assessments performed by [Assignment: organization-defined external organization — FedRAMP High: any FedRAMP Accredited 3PAO] on [Assignment: organization-defined system] when the assessment meets [Assignment: organization-defined requirements — FedRAMP High: the conditions of the AO in the FedRAMP Repository].


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Leverages the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }}. The system platform performs continuous monitoring through {{ THREAT_DETECTION_ENGINE }}, {{ SIEM_TOOL }}, and automated IaC drift analysis. Monitoring and control-effectiveness assessment are performed at the organization-defined frequency: {{ CONMON_REVIEW_FREQUENCY }}. Assessments are conducted as {{ CONMON_ASSESSMENT_TYPE }}, and security status, findings, and POA&M burndown are reported to the AO, ISSM, and ISSO through {{ GRC_TOOL_REFERENCE }}. |
| **FedRAMP High Parameter Values**: `ca-02.03_odp.01` (external organization(s)): any FedRAMP Accredited 3PAO; `ca-02.03_odp.03` (requirements): the conditions of the AO in the FedRAMP Repository |


### CA-3 Information Exchange


a. Approve and manage the exchange of information between the system and other systems using [Selection (one or more): interconnection security agreements; information exchange security agreements; memoranda of understanding or agreement; service level agreements; user agreements; nondisclosure agreements; [Assignment: organization-defined type of agreement]];


b. Document, as part of each exchange agreement, the interface characteristics, security and privacy requirements, controls, and responsibilities for each system, and the impact level of the information communicated; and


c. Review and update the agreements [Assignment: organization-defined frequency — FedRAMP High: at least annually and on input from AO].


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherits controls from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }}. The system platform enforces continuous monitoring through {{ THREAT_DETECTION_ENGINE }}, {{ SIEM_TOOL }}, and automated IaC drift analysis. Monitoring and control-effectiveness assessment are performed at the organization-defined frequency: {{ CONMON_REVIEW_FREQUENCY }}. Assessments are conducted as {{ CONMON_ASSESSMENT_TYPE }}, and security status, findings, and POA&M burndown are reported to the AO, ISSM, and ISSO through {{ GRC_TOOL_REFERENCE }}. |
| **FedRAMP High Parameter Values**: `ca-03_odp.03` (frequency): at least annually and on input from AO |


### CA-3(6) Information Exchange | Transfer Authorizations

Verify that individuals or systems transferring data between interconnecting systems have the requisite authorizations (i.e., write permissions or privileges) prior to accepting such data.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherits controls from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }}. The system platform enforces continuous monitoring through {{ THREAT_DETECTION_ENGINE }}, {{ SIEM_TOOL }}, and automated IaC drift analysis. Monitoring and control-effectiveness assessment are performed at the organization-defined frequency: {{ CONMON_REVIEW_FREQUENCY }}. Assessments are conducted as {{ CONMON_ASSESSMENT_TYPE }}, and security status, findings, and POA&M burndown are reported to the AO, ISSM, and ISSO through {{ GRC_TOOL_REFERENCE }}. |


### CA-5 Plan of Action and Milestones


a. Develop a plan of action and milestones for the system to document the planned remediation actions of the organization to correct weaknesses or deficiencies noted during the assessment of the controls and to reduce or eliminate known vulnerabilities in the system; and


b. Update existing plan of action and milestones [Assignment: organization-defined frequency — FedRAMP High: at least monthly] based on the findings from control assessments, independent audits or reviews, and continuous monitoring activities.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherits controls from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }}. The system platform enforces continuous monitoring through {{ THREAT_DETECTION_ENGINE }}, {{ SIEM_TOOL }}, and automated IaC drift analysis. Monitoring and control-effectiveness assessment are performed at the organization-defined frequency: {{ CONMON_REVIEW_FREQUENCY }}. Assessments are conducted as {{ CONMON_ASSESSMENT_TYPE }}, and security status, findings, and POA&M burndown are reported to the AO, ISSM, and ISSO through {{ GRC_TOOL_REFERENCE }}. |
| **FedRAMP High Parameter Values**: `ca-05_odp` (frequency): at least monthly<br>**FedRAMP Additional Guidance**: Requirement: POA\&Ms must be provided at least monthly. Guidance: Reference FedRAMP-POAM-Template |


### CA-6 Authorization


a. Assign a senior official as the authorizing official for the system;


b. Assign a senior official as the authorizing official for common controls available for inheritance by organizational systems;


c. Ensure that the authorizing official for the system, before commencing operations:

  1. Accepts the use of common controls inherited by the system; and

  2. Authorizes the system to operate;


d. Ensure that the authorizing official for common controls authorizes the use of those controls for inheritance by organizational systems;


e. Update the authorizations [Assignment: organization-defined frequency — FedRAMP High: in accordance with OMB A-130 requirements or when a significant change occurs].


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherits controls from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }}. The system platform enforces continuous monitoring through {{ THREAT_DETECTION_ENGINE }}, {{ SIEM_TOOL }}, and automated IaC drift analysis. Monitoring and control-effectiveness assessment are performed at the organization-defined frequency: {{ CONMON_REVIEW_FREQUENCY }}. Assessments are conducted as {{ CONMON_ASSESSMENT_TYPE }}, and security status, findings, and POA&M burndown are reported to the AO, ISSM, and ISSO through {{ GRC_TOOL_REFERENCE }}. |
| **FedRAMP High Parameter Values**: `ca-06_odp` (frequency): in accordance with OMB A-130 requirements or when a significant change occurs<br>**FedRAMP Additional Guidance**: (e) Guidance: Significant change is defined in NIST Special Publication 800-37 Revision 2, Appendix F and according to FedRAMP Significant Change Policies and Procedures. The service provider describes the types of changes to the information system or the environment of operations that would impact the risk posture. The types of changes are approved and accepted by the AO. |


### CA-7 Continuous Monitoring

Develop a system-level continuous monitoring strategy and implement continuous monitoring in accordance with the organization-level continuous monitoring strategy that includes:


a. Establishing the following system-level metrics to be monitored: [Assignment: organization-defined system-level metrics];


b. Establishing [Assignment: organization-defined frequencies] for monitoring and [Assignment: organization-defined frequencies] for assessment of control effectiveness;


c. Ongoing control assessments in accordance with the continuous monitoring strategy;


d. Ongoing monitoring of system and organization-defined metrics in accordance with the continuous monitoring strategy;


e. Correlation and analysis of information generated by control assessments and monitoring;


f. Response actions to address results of the analysis of control assessment and monitoring information; and


g. Reporting the security and privacy status of the system to [Assignment: organization-defined personnel or roles — FedRAMP High: to include AO] [Assignment: organization-defined frequency].


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherits controls from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }}. The system platform enforces continuous monitoring through {{ THREAT_DETECTION_ENGINE }}, {{ SIEM_TOOL }}, and automated IaC drift analysis. Monitoring and control-effectiveness assessment are performed at the organization-defined frequency: {{ CONMON_REVIEW_FREQUENCY }}. Assessments are conducted as {{ CONMON_ASSESSMENT_TYPE }}, and security status, findings, and POA&M burndown are reported to the AO, ISSM, and ISSO through {{ GRC_TOOL_REFERENCE }}. |
| **FedRAMP High Parameter Values**: `ca-07_odp.04` (personnel or roles): to include AO; `ca-07_odp.06` (personnel or roles): to include AO<br>**FedRAMP Additional Guidance**: Requirement: Operating System, Database, Web Application, Container, and Service Configuration Scans: at least monthly. All scans performed by Independent Assessor: at least annually. Requirement: CSOs with more than one agency ATO must implement a collaborative Continuous Monitoring (ConMon) approach described in the FedRAMP Guide for Multi-Agency Continuous Monitoring. This requirement applies to CSOs authorized via the Agency path as each agency customer is responsible for performing ConMon oversight. Guidance: FedRAMP does not provide a template for the Continuous Monitoring Plan. CSPs should reference the FedRAMP Continuous Monitoring Strategy Guide when developing the Continuous Monitoring Plan. |


### CA-7(1) Continuous Monitoring | Independent Assessment

Employ independent assessors or assessment teams to monitor the controls in the system on an ongoing basis.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherits controls from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }}. The system platform enforces continuous monitoring through {{ THREAT_DETECTION_ENGINE }}, {{ SIEM_TOOL }}, and automated IaC drift analysis. Monitoring and control-effectiveness assessment are performed at the organization-defined frequency: {{ CONMON_REVIEW_FREQUENCY }}. Assessments are conducted as {{ CONMON_ASSESSMENT_TYPE }}, and security status, findings, and POA&M burndown are reported to the AO, ISSM, and ISSO through {{ GRC_TOOL_REFERENCE }}. |


### CA-7(3) Continuous Monitoring | Trend Analyses

Employ trend analyses to determine if control implementations, the frequency of continuous monitoring activities, and the types of activities used in the continuous monitoring process need to be modified based on empirical data.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherits controls from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }}. The system platform enforces continuous monitoring through {{ THREAT_DETECTION_ENGINE }}, {{ SIEM_TOOL }}, and automated IaC drift analysis. Monitoring and control-effectiveness assessment are performed at the organization-defined frequency: {{ CONMON_REVIEW_FREQUENCY }}. Assessments are conducted as {{ CONMON_ASSESSMENT_TYPE }}, and security status, findings, and POA&M burndown are reported to the AO, ISSM, and ISSO through {{ GRC_TOOL_REFERENCE }}. |


### CA-7(4) Continuous Monitoring | Risk Monitoring

Ensure risk monitoring is an integral part of the continuous monitoring strategy that includes the following:


(a) Effectiveness monitoring;


(b) Compliance monitoring; and


(c) Change monitoring.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherits controls from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }}. The system platform enforces continuous monitoring through {{ THREAT_DETECTION_ENGINE }}, {{ SIEM_TOOL }}, and automated IaC drift analysis. Monitoring and control-effectiveness assessment are performed at the organization-defined frequency: {{ CONMON_REVIEW_FREQUENCY }}. Assessments are conducted as {{ CONMON_ASSESSMENT_TYPE }}, and security status, findings, and POA&M burndown are reported to the AO, ISSM, and ISSO through {{ GRC_TOOL_REFERENCE }}. |


### CA-7(5) Continuous Monitoring | Consistency Analysis

Employ the following actions to validate that policies are established and implemented controls are operating in a consistent manner: [Assignment: organization-defined actions].


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherits controls from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }}. The system platform enforces continuous monitoring through {{ THREAT_DETECTION_ENGINE }}, {{ SIEM_TOOL }}, and automated IaC drift analysis. Monitoring and control-effectiveness assessment are performed at the organization-defined frequency: {{ CONMON_REVIEW_FREQUENCY }}. Assessments are conducted as {{ CONMON_ASSESSMENT_TYPE }}, and security status, findings, and POA&M burndown are reported to the AO, ISSM, and ISSO through {{ GRC_TOOL_REFERENCE }}. |


### CA-7(6) Continuous Monitoring | Automation Support for Monitoring

Ensure the accuracy, currency, and availability of monitoring results for the system using [Assignment: organization-defined automated mechanisms].


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherits controls from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }}. The system platform enforces continuous monitoring through {{ THREAT_DETECTION_ENGINE }}, {{ SIEM_TOOL }}, and automated IaC drift analysis. Monitoring and control-effectiveness assessment are performed at the organization-defined frequency: {{ CONMON_REVIEW_FREQUENCY }}. Assessments are conducted as {{ CONMON_ASSESSMENT_TYPE }}, and security status, findings, and POA&M burndown are reported to the AO, ISSM, and ISSO through {{ GRC_TOOL_REFERENCE }}. |


### CA-8 Penetration Testing

Conduct penetration testing [Assignment: organization-defined frequency — FedRAMP High: at least annually] on [Assignment: organization-defined systems or system components].


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherits controls from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }}. The system platform enforces continuous monitoring through {{ THREAT_DETECTION_ENGINE }}, {{ SIEM_TOOL }}, and automated IaC drift analysis. Monitoring and control-effectiveness assessment are performed at the organization-defined frequency: {{ CONMON_REVIEW_FREQUENCY }}. Assessments are conducted as {{ CONMON_ASSESSMENT_TYPE }}, and security status, findings, and POA&M burndown are reported to the AO, ISSM, and ISSO through {{ GRC_TOOL_REFERENCE }}. |
| **FedRAMP High Parameter Values**: `ca-08_odp.01` (frequency): at least annually<br>**FedRAMP Additional Guidance**: Guidance: Reference the FedRAMP Penetration Test Guidance. |


### CA-8(1) Penetration Testing | Independent Penetration Testing Agent or Team

Employ an independent penetration testing agent or team to perform penetration testing on the system or system components.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherits controls from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }}. The system platform enforces continuous monitoring through {{ THREAT_DETECTION_ENGINE }}, {{ SIEM_TOOL }}, and automated IaC drift analysis. Monitoring and control-effectiveness assessment are performed at the organization-defined frequency: {{ CONMON_REVIEW_FREQUENCY }}. Assessments are conducted as {{ CONMON_ASSESSMENT_TYPE }}, and security status, findings, and POA&M burndown are reported to the AO, ISSM, and ISSO through {{ GRC_TOOL_REFERENCE }}. |


### CA-8(2) Penetration Testing | Red Team Exercises

Employ the following red-team exercises to simulate attempts by adversaries to compromise organizational systems in accordance with applicable rules of engagement: [Assignment: organization-defined red team exercises].


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Leverages the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }}. The system platform performs continuous monitoring through {{ THREAT_DETECTION_ENGINE }}, {{ SIEM_TOOL }}, and automated IaC drift analysis. Monitoring and control-effectiveness assessment are performed at the organization-defined frequency: {{ CONMON_REVIEW_FREQUENCY }}. Assessments are conducted as {{ CONMON_ASSESSMENT_TYPE }}, and security status, findings, and POA&M burndown are reported to the AO, ISSM, and ISSO through {{ GRC_TOOL_REFERENCE }}. |
| **FedRAMP Additional Guidance**: Guidance: See the FedRAMP Documents page\> Penetration Test Guidance https://www.FedRAMP.gov/documents/ |


### CA-8(3) Penetration Testing | Facility Penetration Testing

> [!IMPORTANT]
> [WARNING: RMF TEAM ACTION REQUIRED: Verify and update operational procedure or contact details in this section.]

Employ a penetration testing process that includes [Assignment: organization-defined frequency] [Selection: announced; unannounced] attempts to bypass or circumvent controls associated with physical access points to the facility.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherits controls from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }}. The system platform enforces continuous monitoring through {{ THREAT_DETECTION_ENGINE }}, {{ SIEM_TOOL }}, and automated IaC drift analysis. Monitoring and control-effectiveness assessment are performed at the organization-defined frequency: {{ CONMON_REVIEW_FREQUENCY }}. Assessments are conducted as {{ CONMON_ASSESSMENT_TYPE }}, and security status, findings, and POA&M burndown are reported to the AO, ISSM, and ISSO through {{ GRC_TOOL_REFERENCE }}. |


### CA-9 Internal System Connections


a. Authorize internal connections of [Assignment: organization-defined system components or classes of components] to the system;


b. Document, for each internal connection, the interface characteristics, security and privacy requirements, and the nature of the information communicated;


c. Terminate internal system connections after [Assignment: organization-defined conditions]; and


d. Review [Assignment: organization-defined frequency — FedRAMP High: at least annually] the continued need for each internal connection.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherits controls from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }}. The system platform enforces continuous monitoring through {{ THREAT_DETECTION_ENGINE }}, {{ SIEM_TOOL }}, and automated IaC drift analysis. Monitoring and control-effectiveness assessment are performed at the organization-defined frequency: {{ CONMON_REVIEW_FREQUENCY }}. Assessments are conducted as {{ CONMON_ASSESSMENT_TYPE }}, and security status, findings, and POA&M burndown are reported to the AO, ISSM, and ISSO through {{ GRC_TOOL_REFERENCE }}. |
| **FedRAMP High Parameter Values**: `ca-09_odp.03` (frequency): at least annually |


## 2.5 Configuration Management


### CM-1 Policy and Procedures


a. Develop, document, and disseminate to [Assignment: organization-defined personnel or roles]:

  1. [Selection (one or more): Organization-level; Mission/business process-level; System-level] configuration management policy that:

    (a) Addresses purpose, scope, roles, responsibilities, management commitment, coordination among organizational entities, and compliance; and

    (b) Is consistent with applicable laws, executive orders, directives, regulations, policies, standards, and guidelines; and

  2. Procedures to facilitate the implementation of the configuration management policy and the associated configuration management controls;


b. Designate an [Assignment: organization-defined official] to manage the development, documentation, and dissemination of the configuration management policy and procedures; and


c. Review and update the current configuration management:

  1. Policy [Assignment: organization-defined frequency — FedRAMP High: at least annually] and following [Assignment: organization-defined events — FedRAMP High: significant changes]; and

  2. Procedures [Assignment: organization-defined frequency — FedRAMP High: at least annually] and following [Assignment: organization-defined events].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for underlying Google Cloud host baselines. Where configured in the system's Terraform blueprints, system configuration baselines are maintained as Infrastructure as Code (IaC) in version control with automated CI/CD validation and Terraform state/API resource inventory tracking within the accredited {{ DOD_IMPACT_LABEL }} boundary. |
| **FedRAMP High Parameter Values**: `cm-01_odp.05` (frequency): at least annually; `cm-01_odp.07` (frequency): at least annually; `cm-01_odp.08` (events): significant changes |


### CM-2 Baseline Configuration


a. Develop, document, and maintain under configuration control, a current baseline configuration of the system; and


b. Review and update the baseline configuration of the system:

  1. [Assignment: organization-defined frequency — FedRAMP High: at least annually and when a significant change occurs];

  2. When required due to [Assignment: organization-defined circumstances — FedRAMP High: to include when directed by the AO]; and

  3. When system components are installed or upgraded.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for underlying Google Cloud host baselines. Where configured in the system's Terraform blueprints, system configuration baselines are maintained as Infrastructure as Code (IaC) in version control with automated CI/CD validation and Terraform state/API resource inventory tracking within the accredited {{ DOD_IMPACT_LABEL }} boundary. |
| **FedRAMP High Parameter Values**: `cm-02_odp.01` (frequency): at least annually and when a significant change occurs; `cm-02_odp.02` (circumstances): to include when directed by the AO<br>**FedRAMP Additional Guidance**: (b)(1) Guidance: Significant change is defined in NIST Special Publication 800-37 Revision 2, Appendix F. |


### CM-2(2) Baseline Configuration | Automation Support for Accuracy and Currency

Maintain the currency, completeness, accuracy, and availability of the baseline configuration of the system using [Assignment: organization-defined automated mechanisms].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for underlying Google Cloud host baselines. Where configured in the system's Terraform blueprints, system configuration baselines are maintained as Infrastructure as Code (IaC) in version control with automated CI/CD validation and Terraform state/API resource inventory tracking within the accredited {{ DOD_IMPACT_LABEL }} boundary. |


### CM-2(3) Baseline Configuration | Retention of Previous Configurations

Retain [Assignment: organization-defined number — FedRAMP High: organization-defined number of previous versions of baseline configurations of the previously approved baseline configuration of IS components] of previous versions of baseline configurations of the system to support rollback.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for underlying Google Cloud host baselines. Where configured in the system's Terraform blueprints, system configuration baselines are maintained as Infrastructure as Code (IaC) in version control with automated CI/CD validation and Terraform state/API resource inventory tracking within the accredited {{ DOD_IMPACT_LABEL }} boundary. |
| **FedRAMP High Parameter Values**: `cm-02.03_odp` (number): organization-defined number of previous versions of baseline configurations of the previously approved baseline configuration of IS components |


### CM-2(7) Baseline Configuration | Configure Systems and Components for High-risk Areas


(a) Issue [Assignment: organization-defined systems or system components] with [Assignment: organization-defined configurations] to individuals traveling to locations that the organization deems to be of significant risk; and


(b) Apply the following controls to the systems or components when the individuals return from travel: [Assignment: organization-defined controls].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for underlying Google Cloud host baselines. Where configured in the system's Terraform blueprints, system configuration baselines are maintained as Infrastructure as Code (IaC) in version control with automated CI/CD validation and Terraform state/API resource inventory tracking within the accredited {{ DOD_IMPACT_LABEL }} boundary. |


### CM-3 Configuration Change Control


a. Determine and document the types of changes to the system that are configuration-controlled;


b. Review proposed configuration-controlled changes to the system and approve or disapprove such changes with explicit consideration for security and privacy impact analyses;


c. Document configuration change decisions associated with the system;


d. Implement approved configuration-controlled changes to the system;


e. Retain records of configuration-controlled changes to the system for [Assignment: organization-defined time period];


f. Monitor and review activities associated with configuration-controlled changes to the system; and


g. Coordinate and provide oversight for configuration change control activities through [Assignment: organization-defined configuration change control element] that convenes [Selection (one or more): [Assignment: organization-defined frequency]; when [Assignment: organization-defined configuration change conditions]].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for underlying Google Cloud host baselines. Where configured in the system's Terraform blueprints, system configuration baselines are maintained as Infrastructure as Code (IaC) in version control with automated CI/CD validation and Terraform state/API resource inventory tracking within the accredited {{ DOD_IMPACT_LABEL }} boundary. |
| **FedRAMP Additional Guidance**: Requirement: The service provider establishes a central means of communicating major changes to or developments in the information system or environment of operations that may affect its services to the federal government and associated service consumers (e.g., electronic bulletin board, web status page). The means of communication are approved and accepted by the AO. (e) Guidance: In accordance with record retention policies and procedures. |


### CM-3(1) Configuration Change Control | Automated Documentation, Notification, and Prohibition of Changes

Use [Assignment: organization-defined automated mechanisms] to:


(a) Document proposed changes to the system;


(b) Notify [Assignment: organization-defined approval authorities] of proposed changes to the system and request change approval;


(c) Highlight proposed changes to the system that have not been approved or disapproved within [Assignment: organization-defined time period — FedRAMP High: organization agreed upon time period];


(d) Prohibit changes to the system until designated approvals are received;


(e) Document all changes to the system; and


(f) Notify [Assignment: organization-defined personnel — FedRAMP High: organization defined configuration management approval authorities] when approved changes to the system are completed.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for underlying Google Cloud host baselines. Where configured in the system's Terraform blueprints, system configuration baselines are maintained as Infrastructure as Code (IaC) in version control with automated CI/CD validation and Terraform state/API resource inventory tracking within the accredited {{ DOD_IMPACT_LABEL }} boundary. |
| **FedRAMP High Parameter Values**: `cm-03.01_odp.03` (time period): organization agreed upon time period; `cm-03.01_odp.04` (personnel): organization defined configuration management approval authorities |


### CM-3(2) Configuration Change Control | Testing, Validation, and Documentation of Changes

Test, validate, and document changes to the system before finalizing the implementation of the changes.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for underlying Google Cloud host baselines. Where configured in the system's Terraform blueprints, system configuration baselines are maintained as Infrastructure as Code (IaC) in version control with automated CI/CD validation and Terraform state/API resource inventory tracking within the accredited {{ DOD_IMPACT_LABEL }} boundary. |


### CM-3(4) Configuration Change Control | Security and Privacy Representatives

Require [Assignment: organization-defined security and privacy representatives] to be members of the [Assignment: organization-defined configuration change control element — FedRAMP High: Configuration control board (CCB) or similar (as defined in CM-3)].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for underlying Google Cloud host baselines. Where configured in the system's Terraform blueprints, system configuration baselines are maintained as Infrastructure as Code (IaC) in version control with automated CI/CD validation and Terraform state/API resource inventory tracking within the accredited {{ DOD_IMPACT_LABEL }} boundary. |
| **FedRAMP High Parameter Values**: `cm-03.04_odp.03` (configuration change control element): Configuration control board (CCB) or similar (as defined in CM-3) |


### CM-3(5) Configuration Change Control | Automated Security Response

Implement the following security responses automatically if baseline configurations are changed in an unauthorized manner: [Assignment: organization-defined security responses].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for underlying Google Cloud host baselines. Where configured in the system's Terraform blueprints, system configuration baselines are maintained as Infrastructure as Code (IaC) in version control with automated CI/CD validation and Terraform state/API resource inventory tracking within the accredited {{ DOD_IMPACT_LABEL }} boundary. |


### CM-3(6) Configuration Change Control | Cryptography Management

Ensure that cryptographic mechanisms used to provide the following controls are under configuration management: [Assignment: organization-defined controls — FedRAMP High: All security safeguards that rely on cryptography].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for underlying Google Cloud host baselines. Where configured in the system's Terraform blueprints, system configuration baselines are maintained as Infrastructure as Code (IaC) in version control with automated CI/CD validation and Terraform state/API resource inventory tracking within the accredited {{ DOD_IMPACT_LABEL }} boundary. |
| **FedRAMP High Parameter Values**: `cm-03.06_odp` (controls): All security safeguards that rely on cryptography |


### CM-3(7) Configuration Change Control | Review System Changes

Review changes to the system [Assignment: organization-defined frequency] or when [Assignment: organization-defined circumstances] to determine whether unauthorized changes have occurred.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for underlying Google Cloud host baselines. Where configured in the system's Terraform blueprints, system configuration baselines are maintained as Infrastructure as Code (IaC) in version control with automated CI/CD validation and Terraform state/API resource inventory tracking within the accredited {{ DOD_IMPACT_LABEL }} boundary. |


### CM-3(8) Configuration Change Control | Prevent or Restrict Configuration Changes

Prevent or restrict changes to the configuration of the system under the following circumstances: [Assignment: organization-defined circumstances].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for underlying Google Cloud host baselines. Where configured in the system's Terraform blueprints, system configuration baselines are maintained as Infrastructure as Code (IaC) in version control with automated CI/CD validation and Terraform state/API resource inventory tracking within the accredited {{ DOD_IMPACT_LABEL }} boundary. |


### CM-4 Impact Analyses

Analyze changes to the system to determine potential security and privacy impacts prior to change implementation.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for underlying Google Cloud host baselines. Where configured in the system's Terraform blueprints, system configuration baselines are maintained as Infrastructure as Code (IaC) in version control with automated CI/CD validation and Terraform state/API resource inventory tracking within the accredited {{ DOD_IMPACT_LABEL }} boundary. |


### CM-4(1) Impact Analyses | Separate Test Environments

Analyze changes to the system in a separate test environment before implementation in an operational environment, looking for security and privacy impacts due to flaws, weaknesses, incompatibility, or intentional malice.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for underlying Google Cloud host baselines. Where configured in the system's Terraform blueprints, system configuration baselines are maintained as Infrastructure as Code (IaC) in version control with automated CI/CD validation and Terraform state/API resource inventory tracking within the accredited {{ DOD_IMPACT_LABEL }} boundary. |


### CM-4(2) Impact Analyses | Verification of Controls

After system changes, verify that the impacted controls are implemented correctly, operating as intended, and producing the desired outcome with regard to meeting the security and privacy requirements for the system.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for underlying Google Cloud host baselines. Where configured in the system's Terraform blueprints, system configuration baselines are maintained as Infrastructure as Code (IaC) in version control with automated CI/CD validation and Terraform state/API resource inventory tracking within the accredited {{ DOD_IMPACT_LABEL }} boundary. |


### CM-5 Access Restrictions for Change

Define, document, approve, and enforce physical and logical access restrictions associated with changes to the system.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for underlying Google Cloud host baselines. Where configured in the system's Terraform blueprints, system configuration baselines are maintained as Infrastructure as Code (IaC) in version control with automated CI/CD validation and Terraform state/API resource inventory tracking within the accredited {{ DOD_IMPACT_LABEL }} boundary. |


### CM-5(1) Access Restrictions for Change | Automated Access Enforcement and Audit Records


(a) Enforce access restrictions using [Assignment: organization-defined automated mechanisms]; and


(b) Automatically generate audit records of the enforcement actions.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for underlying Google Cloud host baselines. Where configured in the system's Terraform blueprints, system configuration baselines are maintained as Infrastructure as Code (IaC) in version control with automated CI/CD validation and Terraform state/API resource inventory tracking within the accredited {{ DOD_IMPACT_LABEL }} boundary. |


### CM-5(5) Access Restrictions for Change | Privilege Limitation for Production and Operation


(a) Limit privileges to change system components and system-related information within a production or operational environment; and


(b) Review and reevaluate privileges [Assignment: organization-defined frequency — FedRAMP High: at least quarterly].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for underlying Google Cloud host baselines. Where configured in the system's Terraform blueprints, system configuration baselines are maintained as Infrastructure as Code (IaC) in version control with automated CI/CD validation and Terraform state/API resource inventory tracking within the accredited {{ DOD_IMPACT_LABEL }} boundary. |
| **FedRAMP High Parameter Values**: `cm-05.05_odp.01` (frequency): at least quarterly; `cm-05.05_odp.02` (frequency): at least quarterly |


### CM-5(6) Access Restrictions for Change | Limit Library Privileges

Limit privileges to change software resident within software libraries.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for underlying Google Cloud host baselines. Where configured in the system's Terraform blueprints, system configuration baselines are maintained as Infrastructure as Code (IaC) in version control with automated CI/CD validation and Terraform state/API resource inventory tracking within the accredited {{ DOD_IMPACT_LABEL }} boundary. |


### CM-6 Configuration Settings


a. Establish and document configuration settings for components employed within the system that reflect the most restrictive mode consistent with operational requirements using [Assignment: organization-defined common secure configurations];


b. Implement the configuration settings;


c. Identify, document, and approve any deviations from established configuration settings for [Assignment: organization-defined system components] based on [Assignment: organization-defined operational requirements]; and


d. Monitor and control changes to the configuration settings in accordance with organizational policies and procedures.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for underlying Google Cloud host baselines. Where configured in the system's Terraform blueprints, system configuration baselines are maintained as Infrastructure as Code (IaC) in version control with automated CI/CD validation and Terraform state/API resource inventory tracking within the accredited {{ DOD_IMPACT_LABEL }} boundary. |
| **FedRAMP Additional Guidance**: (a) Requirement 1: The service provider shall use the DoD STIGs to establish configuration settings; Center for Internet Security up to Level 2 (CIS Level 2) guidelines shall be used if STIGs are not available; Custom baselines shall be used if CIS is not available. (a) Requirement 2: The service provider shall ensure that checklists for configuration settings are Security Content Automation Protocol (SCAP) validated or SCAP compatible (if validated checklists are not available). Guidance: Compliance checks are used to evaluate configuration settings and provide general insight into the overall effectiveness of configuration management activities. CSPs and 3PAOs typically combine compliance check findings into a single CM-6 finding, which is acceptable. However, for initial assessments, annual assessments, and significant change requests, FedRAMP requires a clear understanding, on a per-control basis, where risks exist. Therefore, 3PAOs must also analyze compliance check findings as part of the controls assessment. Where a direct mapping exists, the 3PAO must document additional findings per control in the corresponding SAR Risk Exposure Table (RET), which are then documented in the CSP's Plan of Action and Milestones (POA\&M). This will likely result in the details of individual control findings overlapping with those in the combined CM-6 finding, which is acceptable. During monthly continuous monitoring, new findings from CSP compliance checks may be combined into a single CM-6 POA\&M item. CSPs are not required to map the findings to specific controls because controls are only assessed during initial assessments, annual assessments, and significant change requests. |


### CM-6(1) Configuration Settings | Automated Management, Application, and Verification

Manage, apply, and verify configuration settings for [Assignment: organization-defined system components] using [Assignment: organization-defined automated mechanisms].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for underlying Google Cloud host baselines. Where configured in the system's Terraform blueprints, system configuration baselines are maintained as Infrastructure as Code (IaC) in version control with automated CI/CD validation and Terraform state/API resource inventory tracking within the accredited {{ DOD_IMPACT_LABEL }} boundary. |


### CM-6(2) Configuration Settings | Respond to Unauthorized Changes

Take the following actions in response to unauthorized changes to [Assignment: organization-defined configuration settings]: [Assignment: organization-defined actions].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for underlying Google Cloud host baselines. Where configured in the system's Terraform blueprints, system configuration baselines are maintained as Infrastructure as Code (IaC) in version control with automated CI/CD validation and Terraform state/API resource inventory tracking within the accredited {{ DOD_IMPACT_LABEL }} boundary. |


### CM-7 Least Functionality


a. Configure the system to provide only [Assignment: organization-defined mission essential capabilities]; and


b. Prohibit or restrict the use of the following functions, ports, protocols, software, and/or services: [Assignment: organization-defined prohibited or restricted functions, system ports, protocols, software, and/or services].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for underlying Google Cloud host baselines. Where configured in the system's Terraform blueprints, system configuration baselines are maintained as Infrastructure as Code (IaC) in version control with automated CI/CD validation and Terraform state/API resource inventory tracking within the accredited {{ DOD_IMPACT_LABEL }} boundary. |
| **FedRAMP Additional Guidance**: (b) Requirement: The service provider shall use Security guidelines (See CM-6) to establish list of prohibited or restricted functions, ports, protocols, and/or services or establishes its own list of prohibited or restricted functions, ports, protocols, and/or services if STIGs or CIS is not available. |


### CM-7(1) Least Functionality | Periodic Review


(a) Review the system [Assignment: organization-defined frequency — FedRAMP High: at least annually] to identify unnecessary and/or nonsecure functions, ports, protocols, software, and services; and


(b) Disable or remove [Assignment: organization-defined functions, ports, protocols, software, and services within the system deemed to be unnecessary and/or nonsecure].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for underlying Google Cloud host baselines. Where configured in the system's Terraform blueprints, system configuration baselines are maintained as Infrastructure as Code (IaC) in version control with automated CI/CD validation and Terraform state/API resource inventory tracking within the accredited {{ DOD_IMPACT_LABEL }} boundary. |
| **FedRAMP High Parameter Values**: `cm-07.01_odp.01` (frequency): at least annually |


### CM-7(2) Least Functionality | Prevent Program Execution

Prevent program execution in accordance with [Selection (one or more): [Assignment: organization-defined policies, rules of behavior, and/or access agreements regarding software program usage and restrictions]; rules authorizing the terms and conditions of software program usage].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for underlying Google Cloud host baselines. Where configured in the system's Terraform blueprints, system configuration baselines are maintained as Infrastructure as Code (IaC) in version control with automated CI/CD validation and Terraform state/API resource inventory tracking within the accredited {{ DOD_IMPACT_LABEL }} boundary. |
| **FedRAMP Additional Guidance**: Guidance: This control refers to software deployment by CSP personnel into the production environment. The control requires a policy that states conditions for deploying software. This control shall be implemented in a technical manner on the information system to only allow programs to run that adhere to the policy (i.e. allow-listing). This control is not to be based off of strictly written policy on what is allowed or not allowed to run. |


### CM-7(3) Least Functionality | Registration Compliance

Ensure compliance with [Assignment: organization-defined registration requirements for functions, ports, protocols, and services].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for underlying Google Cloud host baselines. Where configured in the system's Terraform blueprints, system configuration baselines are maintained as Infrastructure as Code (IaC) in version control with automated CI/CD validation and Terraform state/API resource inventory tracking within the accredited {{ DOD_IMPACT_LABEL }} boundary. |


### CM-7(5) Least Functionality | Authorized Software — Allow-by-exception


(a) Identify [Assignment: organization-defined software programs authorized to execute on the system];


(b) Employ a deny-all, permit-by-exception policy to allow the execution of authorized software programs on the system; and


(c) Review and update the list of authorized software programs [Assignment: organization-defined frequency — FedRAMP High: at least quarterly or when there is a change].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for underlying Google Cloud host baselines. Where configured in the system's Terraform blueprints, system configuration baselines are maintained as Infrastructure as Code (IaC) in version control with automated CI/CD validation and Terraform state/API resource inventory tracking within the accredited {{ DOD_IMPACT_LABEL }} boundary. |
| **FedRAMP High Parameter Values**: `cm-07.05_odp.02` (frequency): at least quarterly or when there is a change |


### CM-7(8) Least Functionality | Binary or Machine Executable Code


(a) Prohibit the use of binary or machine-executable code from sources with limited or no warranty or without the provision of source code; and


(b) Allow exceptions only for compelling mission or operational requirements and with the approval of the authorizing official.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for underlying Google Cloud host baselines. Where configured in the system's Terraform blueprints, system configuration baselines are maintained as Infrastructure as Code (IaC) in version control with automated CI/CD validation and Terraform state/API resource inventory tracking within the accredited {{ DOD_IMPACT_LABEL }} boundary. |


### CM-7(9) Least Functionality | Prohibiting The Use of Unauthorized Hardware


(a) Identify [Assignment: organization-defined hardware components authorized for system use];


(b) Prohibit the use or connection of unauthorized hardware components;


(c) Review and update the list of authorized hardware components [Assignment: organization-defined frequency].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for underlying Google Cloud host baselines. Where configured in the system's Terraform blueprints, system configuration baselines are maintained as Infrastructure as Code (IaC) in version control with automated CI/CD validation and Terraform state/API resource inventory tracking within the accredited {{ DOD_IMPACT_LABEL }} boundary. |


### CM-8 System Component Inventory


a. Develop and document an inventory of system components that:

  1. Accurately reflects the system;

  2. Includes all components within the system;

  3. Does not include duplicate accounting of components or components assigned to any other system;

  4. Is at the level of granularity deemed necessary for tracking and reporting; and

  5. Includes the following information to achieve system component accountability: [Assignment: organization-defined information deemed necessary to achieve effective system component accountability]; and


b. Review and update the system component inventory [Assignment: organization-defined frequency — FedRAMP High: at least monthly].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for underlying Google Cloud host baselines. Where configured in the system's Terraform blueprints, system configuration baselines are maintained as Infrastructure as Code (IaC) in version control with automated CI/CD validation and Terraform state/API resource inventory tracking within the accredited {{ DOD_IMPACT_LABEL }} boundary. |
| **FedRAMP High Parameter Values**: `cm-08_odp.02` (frequency): at least monthly<br>**FedRAMP Additional Guidance**: Requirement: must be provided at least monthly or when there is a change. |


### CM-8(1) System Component Inventory | Updates During Installation and Removal

Update the inventory of system components as part of component installations, removals, and system updates.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for underlying Google Cloud host baselines. Where configured in the system's Terraform blueprints, system configuration baselines are maintained as Infrastructure as Code (IaC) in version control with automated CI/CD validation and Terraform state/API resource inventory tracking within the accredited {{ DOD_IMPACT_LABEL }} boundary. |


### CM-8(2) System Component Inventory | Automated Maintenance

Maintain the currency, completeness, accuracy, and availability of the inventory of system components using [Assignment: organization-defined automated mechanisms].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for underlying Google Cloud host baselines. Where configured in the system's Terraform blueprints, system configuration baselines are maintained as Infrastructure as Code (IaC) in version control with automated CI/CD validation and Terraform state/API resource inventory tracking within the accredited {{ DOD_IMPACT_LABEL }} boundary. |


### CM-8(3) System Component Inventory | Automated Unauthorized Component Detection


(a) Detect the presence of unauthorized hardware, software, and firmware components within the system using [Assignment: organization-defined automated mechanisms — FedRAMP High: automated mechanisms with a maximum five-minute delay in detection] [Assignment: organization-defined frequency — FedRAMP High: continuously]; and


(b) Take the following actions when unauthorized components are detected: [Selection (one or more): disable network access by such components; isolate the components; notify [Assignment: organization-defined personnel or roles]].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for underlying Google Cloud host baselines. Where configured in the system's Terraform blueprints, system configuration baselines are maintained as Infrastructure as Code (IaC) in version control with automated CI/CD validation and Terraform state/API resource inventory tracking within the accredited {{ DOD_IMPACT_LABEL }} boundary. |
| **FedRAMP High Parameter Values**: `cm-08.03_odp.01` (automated mechanisms): automated mechanisms with a maximum five-minute delay in detection; `cm-08.03_odp.02` (automated mechanisms): automated mechanisms with a maximum five-minute delay in detection; `cm-08.03_odp.03` (automated mechanisms): automated mechanisms with a maximum five-minute delay in detection; `cm-08.03_odp.04` (frequency): continuously |


### CM-8(4) System Component Inventory | Accountability Information

Include in the system component inventory information, a means for identifying by [Selection (one or more): name; position; role — FedRAMP High: position and role], individuals responsible and accountable for administering those components.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for underlying Google Cloud host baselines. Where configured in the system's Terraform blueprints, system configuration baselines are maintained as Infrastructure as Code (IaC) in version control with automated CI/CD validation and Terraform state/API resource inventory tracking within the accredited {{ DOD_IMPACT_LABEL }} boundary. |
| **FedRAMP High Parameter Values**: `cm-08.04_odp`: position and role |


### CM-9 Configuration Management Plan

Develop, document, and implement a configuration management plan for the system that:


a. Addresses roles, responsibilities, and configuration management processes and procedures;


b. Establishes a process for identifying configuration items throughout the system development life cycle and for managing the configuration of the configuration items;


c. Defines the configuration items for the system and places the configuration items under configuration management;


d. Is reviewed and approved by [Assignment: organization-defined personnel or roles]; and


e. Protects the configuration management plan from unauthorized disclosure and modification.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for underlying Google Cloud host baselines. Where configured in the system's Terraform blueprints, system configuration baselines are maintained as Infrastructure as Code (IaC) in version control with automated CI/CD validation and Terraform state/API resource inventory tracking within the accredited {{ DOD_IMPACT_LABEL }} boundary. |


### CM-10 Software Usage Restrictions


a. Use software and associated documentation in accordance with contract agreements and copyright laws;


b. Track the use of software and associated documentation protected by quantity licenses to control copying and distribution; and


c. Control and document the use of peer-to-peer file sharing technology to ensure that this capability is not used for the unauthorized distribution, display, performance, or reproduction of copyrighted work.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for underlying Google Cloud host baselines. Where configured in the system's Terraform blueprints, system configuration baselines are maintained as Infrastructure as Code (IaC) in version control with automated CI/CD validation and Terraform state/API resource inventory tracking within the accredited {{ DOD_IMPACT_LABEL }} boundary. |


### CM-10(1) Software Usage Restrictions | Open-source Software

Establish the following restrictions on the use of open-source software: [Assignment: organization-defined restrictions].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for underlying Google Cloud host baselines. Where configured in the system's Terraform blueprints, system configuration baselines are maintained as Infrastructure as Code (IaC) in version control with automated CI/CD validation and Terraform state/API resource inventory tracking within the accredited {{ DOD_IMPACT_LABEL }} boundary. |


### CM-11 User-installed Software


a. Establish [Assignment: organization-defined policies] governing the installation of software by users;


b. Enforce software installation policies through the following methods: [Assignment: organization-defined methods]; and


c. Monitor policy compliance [Assignment: organization-defined frequency — FedRAMP High: Continuously (via CM-7 (5))].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for underlying Google Cloud host baselines. Where configured in the system's Terraform blueprints, system configuration baselines are maintained as Infrastructure as Code (IaC) in version control with automated CI/CD validation and Terraform state/API resource inventory tracking within the accredited {{ DOD_IMPACT_LABEL }} boundary. |
| **FedRAMP High Parameter Values**: `cm-11_odp.03` (frequency): Continuously (via CM-7 (5)) |


### CM-11(2) User-installed Software | Software Installation with Privileged Status

Allow user installation of software only with explicit privileged status.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for underlying Google Cloud host baselines. Where configured in the system's Terraform blueprints, system configuration baselines are maintained as Infrastructure as Code (IaC) in version control with automated CI/CD validation and Terraform state/API resource inventory tracking within the accredited {{ DOD_IMPACT_LABEL }} boundary. |


### CM-12 Information Location


a. Identify and document the location of [Assignment: organization-defined information] and the specific system components on which the information is processed and stored;


b. Identify and document the users who have access to the system and system components where the information is processed and stored; and


c. Document changes to the location (i.e., system or system components) where the information is processed and stored.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for underlying Google Cloud host baselines. Where configured in the system's Terraform blueprints, system configuration baselines are maintained as Infrastructure as Code (IaC) in version control with automated CI/CD validation and Terraform state/API resource inventory tracking within the accredited {{ DOD_IMPACT_LABEL }} boundary. |
| **FedRAMP Additional Guidance**: Requirement: According to FedRAMP Authorization Boundary Guidance |


### CM-12(1) Information Location | Automated Tools to Support Information Location

Use automated tools to identify [Assignment: organization-defined information by information type — FedRAMP High: Federal data and system data that must be protected at the High or Moderate impact levels] on [Assignment: organization-defined system components] to ensure controls are in place to protect organizational information and individual privacy.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for underlying Google Cloud host baselines. Where configured in the system's Terraform blueprints, system configuration baselines are maintained as Infrastructure as Code (IaC) in version control with automated CI/CD validation and Terraform state/API resource inventory tracking within the accredited {{ DOD_IMPACT_LABEL }} boundary. |
| **FedRAMP High Parameter Values**: `cm-12.01_odp.01` (information by information type): Federal data and system data that must be protected at the High or Moderate impact levels<br>**FedRAMP Additional Guidance**: Requirement: According to FedRAMP Authorization Boundary Guidance. |


### CM-14 Signed Components

Prevent the installation of [Assignment: organization-defined software and firmware components] without verification that the component has been digitally signed using a certificate that is recognized and approved by the organization.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for underlying Google Cloud host baselines. Where configured in the system's Terraform blueprints, system configuration baselines are maintained as Infrastructure as Code (IaC) in version control with automated CI/CD validation and Terraform state/API resource inventory tracking within the accredited {{ DOD_IMPACT_LABEL }} boundary. |


## 2.6 Contingency Planning


### CP-1 Policy and Procedures


a. Develop, document, and disseminate to [Assignment: organization-defined personnel or roles]:

  1. [Selection (one or more): Organization-level; Mission/business process-level; System-level] contingency planning policy that:

    (a) Addresses purpose, scope, roles, responsibilities, management commitment, coordination among organizational entities, and compliance; and

    (b) Is consistent with applicable laws, executive orders, directives, regulations, policies, standards, and guidelines; and

  2. Procedures to facilitate the implementation of the contingency planning policy and the associated contingency planning controls;


b. Designate an [Assignment: organization-defined official] to manage the development, documentation, and dissemination of the contingency planning policy and procedures; and


c. Review and update the current contingency planning:

  1. Policy [Assignment: organization-defined frequency — FedRAMP High: at least annually] and following [Assignment: organization-defined events — FedRAMP High: significant changes]; and

  2. Procedures [Assignment: organization-defined frequency — FedRAMP High: at least annually] and following [Assignment: organization-defined events].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited for physical data center redundancy, multi-region power backup, Google Cloud storage geo-replication, and automated live VM migration from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }}. Where configured in the system's Terraform blueprints, the platform provisions multi-region or dual-region Cloud Storage backup buckets, Cloud KMS key redundancy, and multi-zone compute or GKE workloads in accordance with system recovery objectives. |
| **FedRAMP High Parameter Values**: `cp-01_odp.05` (frequency): at least annually; `cp-01_odp.07` (frequency): at least annually; `cp-01_odp.08` (events): significant changes |


### CP-2 Contingency Plan

> [!IMPORTANT]
> [WARNING: RMF TEAM ACTION REQUIRED: Verify and update operational procedure or contact details in this section.]

a. Develop a contingency plan for the system that:

  1. Identifies essential mission and business functions and associated contingency requirements;

  2. Provides recovery objectives, restoration priorities, and metrics;

  3. Addresses contingency roles, responsibilities, assigned individuals with contact information;

  4. Addresses maintaining essential mission and business functions despite a system disruption, compromise, or failure;

  5. Addresses eventual, full system restoration without deterioration of the controls originally planned and implemented;

  6. Addresses the sharing of contingency information; and

  7. Is reviewed and approved by [Assignment: organization-defined personnel or roles];


b. Distribute copies of the contingency plan to [Assignment: organization-defined key contingency personnel (identified by name and/or by role) and organizational elements];


c. Coordinate contingency planning activities with incident handling activities;


d. Review the contingency plan for the system [Assignment: organization-defined frequency — FedRAMP High: at least annually];


e. Update the contingency plan to address changes to the organization, system, or environment of operation and problems encountered during contingency plan implementation, execution, or testing;


f. Communicate contingency plan changes to [Assignment: organization-defined key contingency personnel (identified by name and/or by role) and organizational elements];


g. Incorporate lessons learned from contingency plan testing, training, or actual contingency activities into contingency testing and training; and


h. Protect the contingency plan from unauthorized disclosure and modification.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited for physical data center redundancy, multi-region power backup, Google Cloud storage geo-replication, and automated live VM migration from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }}. Where configured in the system's Terraform blueprints, the platform provisions multi-region or dual-region Cloud Storage backup buckets, Cloud KMS key redundancy, and multi-zone compute or GKE workloads in accordance with system recovery objectives. |
| **FedRAMP High Parameter Values**: `cp-02_odp.05` (frequency): at least annually<br>**FedRAMP Additional Guidance**: Requirement: CSPs must use the FedRAMP Information System Contingency Plan (ISCP) Template (available on the fedramp.gov: https://www.fedramp.gov/assets/resources/templates/SSP-A06-FedRAMP-ISCP-Template.docx). |


### CP-2(1) Contingency Plan | Coordinate with Related Plans

Coordinate contingency plan development with organizational elements responsible for related plans.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited for physical data center redundancy, multi-region power backup, Google Cloud storage geo-replication, and automated live VM migration from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }}. Where configured in the system's Terraform blueprints, the platform provisions multi-region or dual-region Cloud Storage backup buckets, Cloud KMS key redundancy, and multi-zone compute or GKE workloads in accordance with system recovery objectives. |


### CP-2(2) Contingency Plan | Capacity Planning

Conduct capacity planning so that necessary capacity for information processing, telecommunications, and environmental support exists during contingency operations.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited for physical data center redundancy, multi-region power backup, Google Cloud storage geo-replication, and automated live VM migration from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }}. Where configured in the system's Terraform blueprints, the platform provisions multi-region or dual-region Cloud Storage backup buckets, Cloud KMS key redundancy, and multi-zone compute or GKE workloads in accordance with system recovery objectives. |


### CP-2(3) Contingency Plan | Resume Mission and Business Functions

Plan for the resumption of [Selection: all; essential — FedRAMP High: all] mission and business functions within [Assignment: organization-defined time period — FedRAMP High: time period defined in service provider and organization SLA] of contingency plan activation.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited for physical data center redundancy, multi-region power backup, Google Cloud storage geo-replication, and automated live VM migration from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }}. Where configured in the system's Terraform blueprints, the platform provisions multi-region or dual-region Cloud Storage backup buckets, Cloud KMS key redundancy, and multi-zone compute or GKE workloads in accordance with system recovery objectives. |
| **FedRAMP High Parameter Values**: `cp-02.03_odp.01`: all; `cp-02.03_odp.02` (time period): time period defined in service provider and organization SLA |


### CP-2(5) Contingency Plan | Continue Mission and Business Functions

Plan for the continuance of [Selection: all; essential — FedRAMP High: essential] mission and business functions with minimal or no loss of operational continuity and sustains that continuity until full system restoration at primary processing and/or storage sites.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for physical data center redundancy, backup power, storage replication in Google infrastructure, and live migration of VMs during host maintenance. Where configured in the system's Terraform blueprints, the platform provisions multi-region or dual-region Cloud Storage backup buckets, Cloud KMS key redundancy, and multi-zone compute or GKE workloads in accordance with system recovery objectives. |
| **FedRAMP High Parameter Values**: `cp-02.05_odp`: essential |


### CP-2(8) Contingency Plan | Identify Critical Assets

Identify critical system assets supporting [Selection: all; essential] mission and business functions.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited for physical data center redundancy, multi-region power backup, Google Cloud storage geo-replication, and automated live VM migration from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }}. Where configured in the system's Terraform blueprints, the platform provisions multi-region or dual-region Cloud Storage backup buckets, Cloud KMS key redundancy, and multi-zone compute or GKE workloads in accordance with system recovery objectives. |


### CP-3 Contingency Training


a. Provide contingency training to system users consistent with assigned roles and responsibilities:

  1. Within [Assignment: organization-defined time period — FedRAMP High: \*See Additional Requirements] of assuming a contingency role or responsibility;

  2. When required by system changes; and

  3. [Assignment: organization-defined frequency — FedRAMP High: at least annually] thereafter; and


b. Review and update contingency training content [Assignment: organization-defined frequency — FedRAMP High: at least annually] and following [Assignment: organization-defined events].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited for physical data center redundancy, multi-region power backup, Google Cloud storage geo-replication, and automated live VM migration from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }}. Where configured in the system's Terraform blueprints, the platform provisions multi-region or dual-region Cloud Storage backup buckets, Cloud KMS key redundancy, and multi-zone compute or GKE workloads in accordance with system recovery objectives. |
| **FedRAMP High Parameter Values**: `cp-03_odp.01` (time period): \*See Additional Requirements; `cp-03_odp.02` (frequency): at least annually; `cp-03_odp.03` (frequency): at least annually<br>**FedRAMP Additional Guidance**: (a) Requirement: Privileged admins and engineers must take the basic contingency training within 10 days. Consideration must be given for those privileged admins and engineers with critical contingency-related roles, to gain enough system context and situational awareness to understand the full impact of contingency training as it applies to their respective level. Newly hired critical contingency personnel must take this more in-depth training within 60 days of hire date when the training will have more impact. |


### CP-3(1) Contingency Training | Simulated Events

Incorporate simulated events into contingency training to facilitate effective response by personnel in crisis situations.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited for physical data center redundancy, multi-region power backup, Google Cloud storage geo-replication, and automated live VM migration from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }}. Where configured in the system's Terraform blueprints, the platform provisions multi-region or dual-region Cloud Storage backup buckets, Cloud KMS key redundancy, and multi-zone compute or GKE workloads in accordance with system recovery objectives. |


### CP-4 Contingency Plan Testing


a. Test the contingency plan for the system [Assignment: organization-defined frequency — FedRAMP High: at least annually] using the following tests to determine the effectiveness of the plan and the readiness to execute the plan: [Assignment: organization-defined tests — FedRAMP High: functional exercises].


b. Review the contingency plan test results; and


c. Initiate corrective actions, if needed.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited for physical data center redundancy, multi-region power backup, Google Cloud storage geo-replication, and automated live VM migration from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }}. Where configured in the system's Terraform blueprints, the platform provisions multi-region or dual-region Cloud Storage backup buckets, Cloud KMS key redundancy, and multi-zone compute or GKE workloads in accordance with system recovery objectives. |
| **FedRAMP High Parameter Values**: `cp-04_odp.01` (frequency): at least annually; `cp-04_odp.02` (tests): functional exercises; `cp-04_odp.03` (tests): functional exercises<br>**FedRAMP Additional Guidance**: (a) Requirement: The service provider develops test plans in accordance with NIST Special Publication 800-34 (as amended); plans are approved by the AO prior to initiating testing. (b) Requirement: The service provider must include the Contingency Plan test results with the security package within the Contingency Plan-designated appendix (Appendix G, Contingency Plan Test Report). |


### CP-4(1) Contingency Plan Testing | Coordinate with Related Plans

Coordinate contingency plan testing with organizational elements responsible for related plans.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited for physical data center redundancy, multi-region power backup, Google Cloud storage geo-replication, and automated live VM migration from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }}. Where configured in the system's Terraform blueprints, the platform provisions multi-region or dual-region Cloud Storage backup buckets, Cloud KMS key redundancy, and multi-zone compute or GKE workloads in accordance with system recovery objectives. |


### CP-4(2) Contingency Plan Testing | Alternate Processing Site

Test the contingency plan at the alternate processing site:


(a) To familiarize contingency personnel with the facility and available resources; and


(b) To evaluate the capabilities of the alternate processing site to support contingency operations.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited for physical data center redundancy, multi-region power backup, Google Cloud storage geo-replication, and automated live VM migration from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }}. Where configured in the system's Terraform blueprints, the platform provisions multi-region or dual-region Cloud Storage backup buckets, Cloud KMS key redundancy, and multi-zone compute or GKE workloads in accordance with system recovery objectives. |


### CP-6 Alternate Storage Site


a. Establish an alternate storage site, including necessary agreements to permit the storage and retrieval of system backup information; and


b. Ensure that the alternate storage site provides controls equivalent to that of the primary site.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited for physical data center redundancy, multi-region power backup, Google Cloud storage geo-replication, and automated live VM migration from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }}. Where configured in the system's Terraform blueprints, the platform provisions multi-region or dual-region Cloud Storage backup buckets, Cloud KMS key redundancy, and multi-zone compute or GKE workloads in accordance with system recovery objectives. |


### CP-6(1) Alternate Storage Site | Separation from Primary Site

Identify an alternate storage site that is sufficiently separated from the primary storage site to reduce susceptibility to the same threats.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited for physical data center redundancy, multi-region power backup, Google Cloud storage geo-replication, and automated live VM migration from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }}. Where configured in the system's Terraform blueprints, the platform provisions multi-region or dual-region Cloud Storage backup buckets, Cloud KMS key redundancy, and multi-zone compute or GKE workloads in accordance with system recovery objectives. |


### CP-6(2) Alternate Storage Site | Recovery Time and Recovery Point Objectives

Configure the alternate storage site to facilitate recovery operations in accordance with recovery time objective (`{{ RECOVERY_TIME_OBJECTIVE }}`) and recovery point objective (`{{ RECOVERY_POINT_OBJECTIVE }}`).


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited for physical data center redundancy, multi-region power backup, Google Cloud storage geo-replication, and automated live VM migration from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }}. Where configured in the system's Terraform blueprints, the platform provisions multi-region or dual-region Cloud Storage backup buckets, Cloud KMS key redundancy, and multi-zone compute or GKE workloads in accordance with system recovery objectives. |


### CP-6(3) Alternate Storage Site | Accessibility

Identify potential accessibility problems to the alternate storage site in the event of an area-wide disruption or disaster and outline explicit mitigation actions.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited for physical data center redundancy, multi-region power backup, Google Cloud storage geo-replication, and automated live VM migration from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }}. Where configured in the system's Terraform blueprints, the platform provisions multi-region or dual-region Cloud Storage backup buckets, Cloud KMS key redundancy, and multi-zone compute or GKE workloads in accordance with system recovery objectives. |


### CP-7 Alternate Processing Site


a. Establish an alternate processing site, including necessary agreements to permit the transfer and resumption of [Assignment: organization-defined system operations] for essential mission and business functions within [Assignment: organization-defined time period consistent with recovery time objective (`{{ RECOVERY_TIME_OBJECTIVE }}`) and recovery point objective (`{{ RECOVERY_POINT_OBJECTIVE }}`)] when the primary processing capabilities are unavailable;


b. Make available at the alternate processing site, the equipment and supplies required to transfer and resume operations or put contracts in place to support delivery to the site within the organization-defined time period for transfer and resumption; and


c. Provide controls at the alternate processing site that are equivalent to those at the primary site.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited for physical data center redundancy, multi-region power backup, Google Cloud storage geo-replication, and automated live VM migration from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }}. Where configured in the system's Terraform blueprints, the platform provisions multi-region or dual-region Cloud Storage backup buckets, Cloud KMS key redundancy, and multi-zone compute or GKE workloads in accordance with system recovery objectives. |
| **FedRAMP Additional Guidance**: (a) Requirement: The service provider defines a time period consistent with the recovery time objectives and business impact analysis. |


### CP-7(1) Alternate Processing Site | Separation from Primary Site

Identify an alternate processing site that is sufficiently separated from the primary processing site to reduce susceptibility to the same threats.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited for physical data center redundancy, multi-region power backup, Google Cloud storage geo-replication, and automated live VM migration from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }}. Where configured in the system's Terraform blueprints, the platform provisions multi-region or dual-region Cloud Storage backup buckets, Cloud KMS key redundancy, and multi-zone compute or GKE workloads in accordance with system recovery objectives. |
| **FedRAMP Additional Guidance**: Guidance: The service provider may determine what is considered a sufficient degree of separation between the primary and alternate processing sites, based on the types of threats that are of concern. For one particular type of threat (i.e., hostile cyber attack), the degree of separation between sites will be less relevant. |


### CP-7(2) Alternate Processing Site | Accessibility

Identify potential accessibility problems to alternate processing sites in the event of an area-wide disruption or disaster and outlines explicit mitigation actions.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited for physical data center redundancy, multi-region power backup, Google Cloud storage geo-replication, and automated live VM migration from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }}. Where configured in the system's Terraform blueprints, the platform provisions multi-region or dual-region Cloud Storage backup buckets, Cloud KMS key redundancy, and multi-zone compute or GKE workloads in accordance with system recovery objectives. |


### CP-7(3) Alternate Processing Site | Priority of Service

Develop alternate processing site agreements that contain priority-of-service provisions in accordance with availability requirements (including recovery time objective (`{{ RECOVERY_TIME_OBJECTIVE }}`)).


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited for physical data center redundancy, multi-region power backup, Google Cloud storage geo-replication, and automated live VM migration from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }}. Where configured in the system's Terraform blueprints, the platform provisions multi-region or dual-region Cloud Storage backup buckets, Cloud KMS key redundancy, and multi-zone compute or GKE workloads in accordance with system recovery objectives. |


### CP-7(4) Alternate Processing Site | Preparation for Use

Prepare the alternate processing site so that the site can serve as the operational site supporting essential mission and business functions.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited for physical data center redundancy, multi-region power backup, Google Cloud storage geo-replication, and automated live VM migration from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }}. Where configured in the system's Terraform blueprints, the platform provisions multi-region or dual-region Cloud Storage backup buckets, Cloud KMS key redundancy, and multi-zone compute or GKE workloads in accordance with system recovery objectives. |


### CP-8 Telecommunications Services

Establish alternate telecommunications services, including necessary agreements to permit the resumption of [Assignment: organization-defined system operations] for essential mission and business functions within [Assignment: organization-defined time period] when the primary telecommunications capabilities are unavailable at either the primary or alternate processing or storage sites.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited for physical data center redundancy, multi-region power backup, Google Cloud storage geo-replication, and automated live VM migration from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }}. Where configured in the system's Terraform blueprints, the platform provisions multi-region or dual-region Cloud Storage backup buckets, Cloud KMS key redundancy, and multi-zone compute or GKE workloads in accordance with system recovery objectives. |
| **FedRAMP Additional Guidance**: Requirement: The service provider defines a time period consistent with the recovery time objectives and business impact analysis. |


### CP-8(1) Telecommunications Services | Priority of Service Provisions


(a) Develop primary and alternate telecommunications service agreements that contain priority-of-service provisions in accordance with availability requirements (including recovery time objective (`{{ RECOVERY_TIME_OBJECTIVE }}`)); and


(b) Request Telecommunications Service Priority for all telecommunications services used for national security emergency preparedness if the primary and/or alternate telecommunications services are provided by a common carrier.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited for physical data center redundancy, multi-region power backup, Google Cloud storage geo-replication, and automated live VM migration from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }}. Where configured in the system's Terraform blueprints, the platform provisions multi-region or dual-region Cloud Storage backup buckets, Cloud KMS key redundancy, and multi-zone compute or GKE workloads in accordance with system recovery objectives. |


### CP-8(2) Telecommunications Services | Single Points of Failure

Obtain alternate telecommunications services to reduce the likelihood of sharing a single point of failure with primary telecommunications services.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited for physical data center redundancy, multi-region power backup, Google Cloud storage geo-replication, and automated live VM migration from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }}. Where configured in the system's Terraform blueprints, the platform provisions multi-region or dual-region Cloud Storage backup buckets, Cloud KMS key redundancy, and multi-zone compute or GKE workloads in accordance with system recovery objectives. |


### CP-8(3) Telecommunications Services | Separation of Primary and Alternate Providers

Obtain alternate telecommunications services from providers that are separated from primary service providers to reduce susceptibility to the same threats.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited for physical data center redundancy, multi-region power backup, Google Cloud storage geo-replication, and automated live VM migration from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }}. Where configured in the system's Terraform blueprints, the platform provisions multi-region or dual-region Cloud Storage backup buckets, Cloud KMS key redundancy, and multi-zone compute or GKE workloads in accordance with system recovery objectives. |


### CP-8(4) Telecommunications Services | Provider Contingency Plan


(a) Require primary and alternate telecommunications service providers to have contingency plans;


(b) Review provider contingency plans to ensure that the plans meet organizational contingency requirements; and


(c) Obtain evidence of contingency testing and training by providers [Assignment: organization-defined frequency — FedRAMP High: annually].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited for physical data center redundancy, multi-region power backup, Google Cloud storage geo-replication, and automated live VM migration from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }}. Where configured in the system's Terraform blueprints, the platform provisions multi-region or dual-region Cloud Storage backup buckets, Cloud KMS key redundancy, and multi-zone compute or GKE workloads in accordance with system recovery objectives. |
| **FedRAMP High Parameter Values**: `cp-08.04_odp.01` (frequency): annually; `cp-08.04_odp.02` (frequency): annually |


### CP-8(5) Telecommunications Services | Alternate Telecommunication Service Testing

Test alternate telecommunication services [Assignment: organization-defined frequency].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited for physical data center redundancy, multi-region power backup, Google Cloud storage geo-replication, and automated live VM migration from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }}. Where configured in the system's Terraform blueprints, the platform provisions multi-region or dual-region Cloud Storage backup buckets, Cloud KMS key redundancy, and multi-zone compute or GKE workloads in accordance with system recovery objectives. |


### CP-9 System Backup


a. Conduct backups of user-level information contained in [Assignment: organization-defined system components] [Assignment: organization-defined frequency consistent with recovery time objective (`{{ RECOVERY_TIME_OBJECTIVE }}`) and recovery point objective (`{{ RECOVERY_POINT_OBJECTIVE }}`) — FedRAMP High: daily incremental; weekly full];


b. Conduct backups of system-level information contained in the system [Assignment: organization-defined frequency consistent with recovery time objective (`{{ RECOVERY_TIME_OBJECTIVE }}`) and recovery point objective (`{{ RECOVERY_POINT_OBJECTIVE }}`) — FedRAMP High: daily incremental; weekly full];


c. Conduct backups of system documentation, including security- and privacy-related documentation [Assignment: organization-defined frequency consistent with recovery time objective (`{{ RECOVERY_TIME_OBJECTIVE }}`) and recovery point objective (`{{ RECOVERY_POINT_OBJECTIVE }}`) — FedRAMP High: daily incremental; weekly full]; and


d. Protect the confidentiality, integrity, and availability of backup information.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited for physical data center redundancy, multi-region power backup, Google Cloud storage geo-replication, and automated live VM migration from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }}. Where configured in the system's Terraform blueprints, the platform provisions multi-region or dual-region Cloud Storage backup buckets, Cloud KMS key redundancy, and multi-zone compute or GKE workloads in accordance with system recovery objectives. |
| **FedRAMP High Parameter Values**: `cp-09_odp.02` (frequency): daily incremental; weekly full; `cp-09_odp.03` (frequency): daily incremental; weekly full; `cp-09_odp.04` (frequency): daily incremental; weekly full<br>**FedRAMP Additional Guidance**: Requirement: The service provider shall determine what elements of the cloud environment require the Information System Backup control. The service provider shall determine how Information System Backup is going to be verified and appropriate periodicity of the check. (a) Requirement: The service provider maintains at least three backup copies of user-level information (at least one of which is available online) or provides an equivalent alternative. (b) Requirement: The service provider maintains at least three backup copies of system-level information (at least one of which is available online) or provides an equivalent alternative. (c) Requirement: The service provider maintains at least three backup copies of information system documentation including security information (at least one of which is available online) or provides an equivalent alternative. |


### CP-9(1) System Backup | Testing for Reliability and Integrity

Test backup information [Assignment: organization-defined frequency — FedRAMP High: at least monthly] to verify media reliability and information integrity.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited for physical data center redundancy, multi-region power backup, Google Cloud storage geo-replication, and automated live VM migration from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }}. Where configured in the system's Terraform blueprints, the platform provisions multi-region or dual-region Cloud Storage backup buckets, Cloud KMS key redundancy, and multi-zone compute or GKE workloads in accordance with system recovery objectives. |
| **FedRAMP High Parameter Values**: `cp-09.01_odp.01` (frequency): at least monthly; `cp-09.01_odp.02` (frequency): at least monthly |


### CP-9(2) System Backup | Test Restoration Using Sampling

Use a sample of backup information in the restoration of selected system functions as part of contingency plan testing.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited for physical data center redundancy, multi-region power backup, Google Cloud storage geo-replication, and automated live VM migration from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }}. Where configured in the system's Terraform blueprints, the platform provisions multi-region or dual-region Cloud Storage backup buckets, Cloud KMS key redundancy, and multi-zone compute or GKE workloads in accordance with system recovery objectives. |


### CP-9(3) System Backup | Separate Storage for Critical Information

> [!IMPORTANT]
> [WARNING: RMF TEAM ACTION REQUIRED: Verify and update operational procedure or contact details in this section.]

Store backup copies of [Assignment: organization-defined critical system software and other security-related information] in a separate facility or in a fire rated container that is not collocated with the operational system.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited for physical data center redundancy, multi-region power backup, Google Cloud storage geo-replication, and automated live VM migration from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }}. Where configured in the system's Terraform blueprints, the platform provisions multi-region or dual-region Cloud Storage backup buckets, Cloud KMS key redundancy, and multi-zone compute or GKE workloads in accordance with system recovery objectives. |


### CP-9(5) System Backup | Transfer to Alternate Storage Site

Transfer system backup information to the alternate storage site [Assignment: organization-defined time period and transfer rate consistent with the recovery time objective (`{{ RECOVERY_TIME_OBJECTIVE }}`) and recovery point objective (`{{ RECOVERY_POINT_OBJECTIVE }}`) — FedRAMP High: time period and transfer rate consistent with the recovery time and recovery point objectives defined in the service provider and organization SLA.].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited for physical data center redundancy, multi-region power backup, Google Cloud storage geo-replication, and automated live VM migration from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }}. Where configured in the system's Terraform blueprints, the platform provisions multi-region or dual-region Cloud Storage backup buckets, Cloud KMS key redundancy, and multi-zone compute or GKE workloads in accordance with system recovery objectives. |
| **FedRAMP High Parameter Values**: `cp-09.05_odp.01` (time period): time period and transfer rate consistent with the recovery time and recovery point objectives defined in the service provider and organization SLA.; `cp-09.05_odp.02` (transfer rate): time period and transfer rate consistent with the recovery time and recovery point objectives defined in the service provider and organization SLA. |


### CP-9(8) System Backup | Cryptographic Protection

Implement cryptographic mechanisms to prevent unauthorized disclosure and modification of [Assignment: organization-defined backup information — FedRAMP High: all backup files].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited for physical data center redundancy, multi-region power backup, Google Cloud storage geo-replication, and automated live VM migration from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }}. Where configured in the system's Terraform blueprints, the platform provisions multi-region or dual-region Cloud Storage backup buckets, Cloud KMS key redundancy, and multi-zone compute or GKE workloads in accordance with system recovery objectives. |
| **FedRAMP High Parameter Values**: `cp-09.08_odp` (backup information): all backup files<br>**FedRAMP Additional Guidance**: Guidance: Note that this enhancement requires the use of cryptography which must be compliant with Federal requirements and utilize FIPS validated or NSA approved cryptography (see SC-13.) |


### CP-10 System Recovery and Reconstitution

Provide for the recovery and reconstitution of the system to a known state within [Assignment: organization-defined time period consistent with recovery time objective (`{{ RECOVERY_TIME_OBJECTIVE }}`) and recovery point objective (`{{ RECOVERY_POINT_OBJECTIVE }}`)] after a disruption, compromise, or failure.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited for physical data center redundancy, multi-region power backup, Google Cloud storage geo-replication, and automated live VM migration from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }}. Where configured in the system's Terraform blueprints, the platform provisions multi-region or dual-region Cloud Storage backup buckets, Cloud KMS key redundancy, and multi-zone compute or GKE workloads in accordance with system recovery objectives. |


### CP-10(2) System Recovery and Reconstitution | Transaction Recovery

Implement transaction recovery for systems that are transaction-based.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited for physical data center redundancy, multi-region power backup, Google Cloud storage geo-replication, and automated live VM migration from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }}. Where configured in the system's Terraform blueprints, the platform provisions multi-region or dual-region Cloud Storage backup buckets, Cloud KMS key redundancy, and multi-zone compute or GKE workloads in accordance with system recovery objectives. |


### CP-10(4) System Recovery and Reconstitution | Restore Within Time Period

Provide the capability to restore system components within [Assignment: organization-defined restoration time periods — FedRAMP High: time period consistent with the restoration time-periods defined in the service provider and organization SLA] from configuration-controlled and integrity-protected information representing a known, operational state for the components.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited for physical data center redundancy, multi-region power backup, Google Cloud storage geo-replication, and automated live VM migration from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }}. Where configured in the system's Terraform blueprints, the platform provisions multi-region or dual-region Cloud Storage backup buckets, Cloud KMS key redundancy, and multi-zone compute or GKE workloads in accordance with system recovery objectives. |
| **FedRAMP High Parameter Values**: `cp-10.04_odp` (restoration time periods): time period consistent with the restoration time-periods defined in the service provider and organization SLA |


### CP-10(6) System Recovery and Reconstitution | Component Protection

Protect system components used for recovery and reconstitution.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited for physical data center redundancy, multi-region power backup, Google Cloud storage geo-replication, and automated live VM migration from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }}. Where configured in the system's Terraform blueprints, the platform provisions multi-region or dual-region Cloud Storage backup buckets, Cloud KMS key redundancy, and multi-zone compute or GKE workloads in accordance with system recovery objectives. |


## 2.7 Identification and Authentication


### IA-1 Policy and Procedures


a. Develop, document, and disseminate to [Assignment: organization-defined personnel or roles]:

  1. [Selection (one or more): Organization-level; Mission/business process-level; System-level] identification and authentication policy that:

    (a) Addresses purpose, scope, roles, responsibilities, management commitment, coordination among organizational entities, and compliance; and

    (b) Is consistent with applicable laws, executive orders, directives, regulations, policies, standards, and guidelines; and

  2. Procedures to facilitate the implementation of the identification and authentication policy and the associated identification and authentication controls;


b. Designate an [Assignment: organization-defined official] to manage the development, documentation, and dissemination of the identification and authentication policy and procedures; and


c. Review and update the current identification and authentication:

  1. Policy [Assignment: organization-defined frequency — FedRAMP High: at least annually] and following [Assignment: organization-defined events — FedRAMP High: significant changes]; and

  2. Procedures [Assignment: organization-defined frequency — FedRAMP High: at least annually] and following [Assignment: organization-defined events].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure identity backends and hypervisor isolation. Where configured in the system's Terraform blueprints, the platform enforces least-privilege IAM bindings, Identity-Aware Proxy (IAP) TCP/HTTPS forwarding, VPC Service Controls perimeters, and Google Organization Policy constraints. |
| **FedRAMP High Parameter Values**: `ia-01_odp.05` (frequency): at least annually; `ia-01_odp.07` (frequency): at least annually; `ia-01_odp.08` (events): significant changes |


### IA-2 Identification and Authentication (Organizational Users)

Uniquely identify and authenticate organizational users and associate that unique identification with processes acting on behalf of those users.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure identity backends and hypervisor isolation. Where configured in the system's Terraform blueprints, the platform enforces least-privilege IAM bindings, Identity-Aware Proxy (IAP) TCP/HTTPS forwarding, VPC Service Controls perimeters, and Google Organization Policy constraints. |
| **FedRAMP Additional Guidance**: Requirement: For all control enhancements that specify multifactor authentication, the implementation must adhere to the Digital Identity Guidelines specified in NIST Special Publication 800-63B. Requirement: Multi-factor authentication must be phishing-resistant. Requirement: All uses of encrypted virtual private networks must meet all applicable Federal requirements and architecture, dataflow, and security and privacy controls must be documented, assessed, and authorized to operate. Guidance: "Phishing-resistant" authentication refers to authentication processes designed to detect and prevent disclosure of authentication secrets and outputs to a website or application masquerading as a legitimate system. |


### IA-2(1) Identification and Authentication (Organizational Users) | Multi-factor Authentication to Privileged Accounts

Implement multi-factor authentication for access to privileged accounts.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure identity backends and hypervisor isolation. Where configured in the system's Terraform blueprints, the platform enforces least-privilege IAM bindings, Identity-Aware Proxy (IAP) TCP/HTTPS forwarding, VPC Service Controls perimeters, and Google Organization Policy constraints. |
| **FedRAMP Additional Guidance**: Requirement: According to SP 800-63-3, SP 800-63A (IAL), SP 800-63B (AAL), and SP 800-63C (FAL). Requirement: Multi-factor authentication must be phishing-resistant. Guidance: Multi-factor authentication to subsequent components in the same user domain is not required. |


### IA-2(2) Identification and Authentication (Organizational Users) | Multi-factor Authentication to Non-privileged Accounts

Implement multi-factor authentication for access to non-privileged accounts.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure identity backends and hypervisor isolation. Where configured in the system's Terraform blueprints, the platform enforces least-privilege IAM bindings, Identity-Aware Proxy (IAP) TCP/HTTPS forwarding, VPC Service Controls perimeters, and Google Organization Policy constraints. |
| **FedRAMP Additional Guidance**: Requirement: According to SP 800-63-3, SP 800-63A (IAL), SP 800-63B (AAL), and SP 800-63C (FAL). Requirement: Multi-factor authentication must be phishing-resistant. Guidance: Multi-factor authentication to subsequent components in the same user domain is not required. |


### IA-2(5) Identification and Authentication (Organizational Users) | Individual Authentication with Group Authentication

When shared accounts or authenticators are employed, require users to be individually authenticated before granting access to the shared accounts or resources.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure identity backends and hypervisor isolation. Where configured in the system's Terraform blueprints, the platform enforces least-privilege IAM bindings, Identity-Aware Proxy (IAP) TCP/HTTPS forwarding, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### IA-2(6) Identification and Authentication (Organizational Users) | Access to Accounts —separate Device

Implement multi-factor authentication for [Selection (one or more): local; network; remote — FedRAMP High: local, network and remote] access to [Selection (one or more): privileged accounts; non-privileged accounts — FedRAMP High: privileged accounts; non-privileged accounts] such that:


(a) One of the factors is provided by a device separate from the system gaining access; and


(b) The device meets [Assignment: organization-defined strength of mechanism requirements — FedRAMP High: FIPS-validated or NSA-approved cryptography].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure identity backends and hypervisor isolation. Where configured in the system's Terraform blueprints, the platform enforces least-privilege IAM bindings, Identity-Aware Proxy (IAP) TCP/HTTPS forwarding, VPC Service Controls perimeters, and Google Organization Policy constraints. |
| **FedRAMP High Parameter Values**: `ia-02.06_odp.01`: local, network and remote; `ia-02.06_odp.02`: privileged accounts; non-privileged accounts; `ia-02.06_odp.03` (strength of mechanism requirements): FIPS-validated or NSA-approved cryptography<br>**FedRAMP Additional Guidance**: Guidance: PIV=separate device. Please refer to NIST SP 800-157 Guidelines for Derived Personal Identity Verification (PIV) Credentials. Guidance: See SC-13 Guidance for more information on FIPS-validated or NSA-approved cryptography. |


### IA-2(8) Identification and Authentication (Organizational Users) | Access to Accounts — Replay Resistant

Implement replay-resistant authentication mechanisms for access to [Selection (one or more): privileged accounts; non-privileged accounts — FedRAMP High: privileged accounts; non-privileged accounts].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure identity backends and hypervisor isolation. Where configured in the system's Terraform blueprints, the platform enforces least-privilege IAM bindings, Identity-Aware Proxy (IAP) TCP/HTTPS forwarding, VPC Service Controls perimeters, and Google Organization Policy constraints. |
| **FedRAMP High Parameter Values**: `ia-02.08_odp`: privileged accounts; non-privileged accounts |


### IA-2(12) Identification and Authentication (Organizational Users) | Acceptance of PIV Credentials

Accept and electronically verify Personal Identity Verification-compliant credentials.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure identity backends and hypervisor isolation. Where configured in the system's Terraform blueprints, the platform enforces least-privilege IAM bindings, Identity-Aware Proxy (IAP) TCP/HTTPS forwarding, VPC Service Controls perimeters, and Google Organization Policy constraints. |
| **FedRAMP Additional Guidance**: Guidance: Include Common Access Card (CAC), i.e., the DoD technical implementation of PIV/FIPS 201/HSPD-12. |


### IA-3 Device Identification and Authentication

Uniquely identify and authenticate [Assignment: organization-defined devices and/or types of devices] before establishing a [Selection (one or more): local; remote; network] connection.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for the Google-managed infrastructure that hosts the system. [CONFIG_REQUIRED: Confirm in the Google Cloud {{ DOD_IMPACT_LABEL }} / {{ BASE_FEDRAMP_LABEL }} customer responsibility matrix whether IA-3 is inherited or shared; document customer-configured controls and verify Implementation Status] |


### IA-3(1) Device Identification and Authentication | Cryptographic Bidirectional Authentication

Authenticate [Assignment: organization-defined devices and/or types of devices] before establishing [Selection (one or more): local; remote; network] connection using bidirectional authentication that is cryptographically based.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure identity backends and hypervisor isolation. Where configured in the system's Terraform blueprints, the platform enforces least-privilege IAM bindings, Identity-Aware Proxy (IAP) TCP/HTTPS forwarding, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### IA-4 Identifier Management

Manage system identifiers by:


a. Receiving authorization from [Assignment: organization-defined personnel or roles — FedRAMP High: at a minimum, the ISSO (or similar role within the organization)] to assign an individual, group, role, service, or device identifier;


b. Selecting an identifier that identifies an individual, group, role, service, or device;


c. Assigning the identifier to the intended individual, group, role, service, or device; and


d. Preventing reuse of identifiers for [Assignment: organization-defined time period — FedRAMP High: at least two (2) years].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure identity backends and hypervisor isolation. Where configured in the system's Terraform blueprints, the platform enforces least-privilege IAM bindings, Identity-Aware Proxy (IAP) TCP/HTTPS forwarding, VPC Service Controls perimeters, and Google Organization Policy constraints. |
| **FedRAMP High Parameter Values**: `ia-04_odp.01` (personnel or roles): at a minimum, the ISSO (or similar role within the organization); `ia-04_odp.02` (time period): at least two (2) years |


### IA-4(4) Identifier Management | Identify User Status

Manage individual identifiers by uniquely identifying each individual as [Assignment: organization-defined characteristic identifying individual status — FedRAMP High: contractors; foreign nationals].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure identity backends and hypervisor isolation. Where configured in the system's Terraform blueprints, the platform enforces least-privilege IAM bindings, Identity-Aware Proxy (IAP) TCP/HTTPS forwarding, VPC Service Controls perimeters, and Google Organization Policy constraints. |
| **FedRAMP High Parameter Values**: `ia-04.04_odp` (characteristics): contractors; foreign nationals |


### IA-4(9) Identifier Management | Attribute Maintenance and Protection

Maintain the attributes for each uniquely identified individual, device, or service in [Assignment: organization-defined protected central storage].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure identity backends and hypervisor isolation. Where configured in the system's Terraform blueprints, the platform enforces least-privilege IAM bindings, Identity-Aware Proxy (IAP) TCP/HTTPS forwarding, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### IA-5 Authenticator Management

Manage system authenticators by:


a. Verifying, as part of the initial authenticator distribution, the identity of the individual, group, role, service, or device receiving the authenticator;


b. Establishing initial authenticator content for any authenticators issued by the organization;


c. Ensuring that authenticators have sufficient strength of mechanism for their intended use;


d. Establishing and implementing administrative procedures for initial authenticator distribution, for lost or compromised or damaged authenticators, and for revoking authenticators;


e. Changing default authenticators prior to first use;


f. Changing or refreshing authenticators [Assignment: organization-defined time period by authenticator type] or when [Assignment: organization-defined events] occur;


g. Protecting authenticator content from unauthorized disclosure and modification;


h. Requiring individuals to take, and having devices implement, specific controls to protect authenticators; and


i. Changing authenticators for group or role accounts when membership to those accounts changes.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure identity backends and hypervisor isolation. Where configured in the system's Terraform blueprints, the platform enforces least-privilege IAM bindings, Identity-Aware Proxy (IAP) TCP/HTTPS forwarding, VPC Service Controls perimeters, and Google Organization Policy constraints. |
| **FedRAMP Additional Guidance**: Requirement: Authenticators must be compliant with NIST SP 800-63-3 Digital Identity Guidelines IAL, AAL, FAL level 3. Link https://pages.nist.gov/800-63-3 Guidance: SP 800-63C Section 6.2.3 Encrypted Assertion requires that authentication assertions be encrypted when passed through third parties, such as a browser. For example, a SAML assertion can be encrypted using XML-Encryption, or an OpenID Connect ID Token can be encrypted using JSON Web Encryption (JWE). |


### IA-5(1) Authenticator Management | Password-based Authentication

For password-based authentication:


(a) Maintain a list of commonly-used, expected, or compromised passwords and update the list [Assignment: organization-defined frequency] and when organizational passwords are suspected to have been compromised directly or indirectly;


(b) Verify, when users create or update passwords, that the passwords are not found on the list of commonly-used, expected, or compromised passwords in IA-5(1)(a);


(c) Transmit passwords only over cryptographically-protected channels;


(d) Store passwords using an approved salted key derivation function, preferably using a keyed hash;


(e) Require immediate selection of a new password upon account recovery;


(f) Allow user selection of long passwords and passphrases, including spaces and all printable characters;


(g) Employ automated tools to assist the user in selecting strong password authenticators; and


(h) Enforce the following composition and complexity rules: [Assignment: organization-defined composition and complexity rules].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure identity backends and hypervisor isolation. Where configured in the system's Terraform blueprints, the platform enforces least-privilege IAM bindings, Identity-Aware Proxy (IAP) TCP/HTTPS forwarding, VPC Service Controls perimeters, and Google Organization Policy constraints. |
| **FedRAMP Additional Guidance**: Requirement: Password policies must be compliant with NIST SP 800-63B for all memorized, lookup, out-of-band, or One-Time-Passwords (OTP). Password policies shall not enforce special character or minimum password rotation requirements for memorized secrets of users. (h) Requirement: For cases where technology doesn't allow multi-factor authentication, these rules should be enforced: must have a minimum length of 14 characters and must support all printable ASCII characters. For emergency use accounts, these rules should be enforced: must have a minimum length of 14 characters, must support all printable ASCII characters, and passwords must be changed if used. Guidance: Note that (c) and (d) require the use of cryptography which must be compliant with Federal requirements and utilize FIPS validated or NSA approved cryptography (see SC-13). |


### IA-5(2) Authenticator Management | Public Key-based Authentication


(a) For public key-based authentication:

  (1) Enforce authorized access to the corresponding private key; and

  (2) Map the authenticated identity to the account of the individual or group; and


(b) When public key infrastructure (PKI) is used:

  (1) Validate certificates by constructing and verifying a certification path to an accepted trust anchor, including checking certificate status information; and

  (2) Implement a local cache of revocation data to support path discovery and validation.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure identity backends and hypervisor isolation. Where configured in the system's Terraform blueprints, the platform enforces least-privilege IAM bindings, Identity-Aware Proxy (IAP) TCP/HTTPS forwarding, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### IA-5(6) Authenticator Management | Protection of Authenticators

Protect authenticators commensurate with the security category of the information to which use of the authenticator permits access.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure identity backends and hypervisor isolation. Where configured in the system's Terraform blueprints, the platform enforces least-privilege IAM bindings, Identity-Aware Proxy (IAP) TCP/HTTPS forwarding, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### IA-5(7) Authenticator Management | No Embedded Unencrypted Static Authenticators

Ensure that unencrypted static authenticators are not embedded in applications or other forms of static storage.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure identity backends and hypervisor isolation. Where configured in the system's Terraform blueprints, the platform enforces least-privilege IAM bindings, Identity-Aware Proxy (IAP) TCP/HTTPS forwarding, VPC Service Controls perimeters, and Google Organization Policy constraints. |
| **FedRAMP Additional Guidance**: Guidance: In this context, prohibited static storage refers to any storage where unencrypted authenticators, such as passwords, persist beyond the time required to complete the access process. |


### IA-5(8) Authenticator Management | Multiple System Accounts

Implement [Assignment: organization-defined security controls — FedRAMP High: different authenticators in different user authentication domains] to manage the risk of compromise due to individuals having accounts on multiple systems.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure identity backends and hypervisor isolation. Where configured in the system's Terraform blueprints, the platform enforces least-privilege IAM bindings, Identity-Aware Proxy (IAP) TCP/HTTPS forwarding, VPC Service Controls perimeters, and Google Organization Policy constraints. |
| **FedRAMP High Parameter Values**: `ia-05.08_odp` (security controls): different authenticators in different user authentication domains<br>**FedRAMP Additional Guidance**: Guidance: If a single user authentication domain is used to access multiple systems, such as in single-sign-on, then only a single authenticator is required. |


### IA-5(13) Authenticator Management | Expiration of Cached Authenticators

Prohibit the use of cached authenticators after [Assignment: organization-defined time period].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure identity backends and hypervisor isolation. Where configured in the system's Terraform blueprints, the platform enforces least-privilege IAM bindings, Identity-Aware Proxy (IAP) TCP/HTTPS forwarding, VPC Service Controls perimeters, and Google Organization Policy constraints. |
| **FedRAMP Additional Guidance**: Guidance: For components subject to configuration baseline(s) (such as STIG or CIS,) the time period should conform to the baseline standard. |


### IA-5(14) Authenticator Management | Managing Content of PKI Trust Stores

For PKI-based authentication, employ an organization-wide methodology for managing the content of PKI trust stores installed across all platforms, including networks, operating systems, browsers, and applications.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure identity backends and hypervisor isolation. Where configured in the system's Terraform blueprints, the platform enforces least-privilege IAM bindings, Identity-Aware Proxy (IAP) TCP/HTTPS forwarding, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### IA-5(16) Authenticator Management | In-person or Trusted External Party Authenticator Issuance

Require that the issuance of [Assignment: organization-defined types of and/or specific authenticators] be conducted [Selection: in person; by a trusted external party] before [Assignment: organization-defined registration authority] with authorization by [Assignment: organization-defined personnel or roles].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure identity backends and hypervisor isolation. Where configured in the system's Terraform blueprints, the platform enforces least-privilege IAM bindings, Identity-Aware Proxy (IAP) TCP/HTTPS forwarding, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### IA-6 Authentication Feedback

Obscure feedback of authentication information during the authentication process to protect the information from possible exploitation and use by unauthorized individuals.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for the Google-managed infrastructure that hosts the system. [CONFIG_REQUIRED: Confirm in the Google Cloud {{ DOD_IMPACT_LABEL }} / {{ BASE_FEDRAMP_LABEL }} customer responsibility matrix whether IA-6 is inherited or shared; document customer-configured controls and verify Implementation Status] |


### IA-7 Cryptographic Module Authentication

Implement mechanisms for authentication to a cryptographic module that meet the requirements of applicable laws, executive orders, directives, policies, regulations, standards, and guidelines for such authentication.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for the Google-managed infrastructure that hosts the system. [CONFIG_REQUIRED: Confirm in the Google Cloud {{ DOD_IMPACT_LABEL }} / {{ BASE_FEDRAMP_LABEL }} customer responsibility matrix whether IA-7 is inherited or shared; document customer-configured controls and verify Implementation Status] |


### IA-8 Identification and Authentication (Non-organizational Users)

Uniquely identify and authenticate non-organizational users or processes acting on behalf of non-organizational users.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for the Google-managed infrastructure that hosts the system. [CONFIG_REQUIRED: Confirm in the Google Cloud {{ DOD_IMPACT_LABEL }} / {{ BASE_FEDRAMP_LABEL }} customer responsibility matrix whether IA-8 is inherited or shared; document customer-configured controls and verify Implementation Status] |


### IA-8(1) Identification and Authentication (Non-organizational Users) | Acceptance of PIV Credentials from Other Agencies

Accept and electronically verify Personal Identity Verification-compliant credentials from other federal agencies.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for the Google-managed infrastructure that hosts the system. [CONFIG_REQUIRED: Confirm in the Google Cloud {{ DOD_IMPACT_LABEL }} / {{ BASE_FEDRAMP_LABEL }} customer responsibility matrix whether IA-8(1) is inherited or shared; document customer-configured controls and verify Implementation Status] |


### IA-8(2) Identification and Authentication (Non-organizational Users) | Acceptance of External Authenticators


(a) Accept only external authenticators that are NIST-compliant; and


(b) Document and maintain a list of accepted external authenticators.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for the Google-managed infrastructure that hosts the system. [CONFIG_REQUIRED: Confirm in the Google Cloud {{ DOD_IMPACT_LABEL }} / {{ BASE_FEDRAMP_LABEL }} customer responsibility matrix whether IA-8(2) is inherited or shared; document customer-configured controls and verify Implementation Status] |


### IA-8(4) Identification and Authentication (Non-organizational Users) | Use of Defined Profiles

Conform to the following profiles for identity management [Assignment: organization-defined identity management profiles].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for the Google-managed infrastructure that hosts the system. [CONFIG_REQUIRED: Confirm in the Google Cloud {{ DOD_IMPACT_LABEL }} / {{ BASE_FEDRAMP_LABEL }} customer responsibility matrix whether IA-8(4) is inherited or shared; document customer-configured controls and verify Implementation Status] |


### IA-9 Service Identification and Authentication

Uniquely identify and authenticate [Assignment: organization-defined system services and applications] before establishing communications with devices, users, or other services or applications.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure identity backends and hypervisor isolation. Where configured in the system's Terraform blueprints, the platform enforces least-privilege IAM bindings, Identity-Aware Proxy (IAP) TCP/HTTPS forwarding, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### IA-10 Adaptive Authentication

Require individuals accessing the system to employ [Assignment: organization-defined supplemental authentication techniques or mechanisms] under specific [Assignment: organization-defined circumstances or situations].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure identity backends and hypervisor isolation. Where configured in the system's Terraform blueprints, the platform enforces least-privilege IAM bindings, Identity-Aware Proxy (IAP) TCP/HTTPS forwarding, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### IA-11 Re-authentication

Require users to re-authenticate when [Assignment: organization-defined circumstances or situations requiring re-authentication].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure identity backends and hypervisor isolation. Where configured in the system's Terraform blueprints, the platform enforces least-privilege IAM bindings, Identity-Aware Proxy (IAP) TCP/HTTPS forwarding, VPC Service Controls perimeters, and Google Organization Policy constraints. |
| **FedRAMP Additional Guidance**: Guidance: The fixed time period cannot exceed the limits set in SP 800-63. At this writing they are: - AAL3 (high baseline) - 12 hours or - 15 minutes of inactivity |


### IA-12 Identity Proofing


a. Identity proof users that require accounts for logical access to systems based on appropriate identity assurance level requirements as specified in applicable standards and guidelines;


b. Resolve user identities to a unique individual; and


c. Collect, validate, and verify identity evidence.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure identity backends and hypervisor isolation. Where configured in the system's Terraform blueprints, the platform enforces least-privilege IAM bindings, Identity-Aware Proxy (IAP) TCP/HTTPS forwarding, VPC Service Controls perimeters, and Google Organization Policy constraints. |
| **FedRAMP Additional Guidance**: Guidance: In accordance with NIST SP 800-63A Enrollment and Identity Proofing |


### IA-12(1) Identity Proofing | Supervisor Authorization

Require that the registration process to receive an account for logical access includes supervisor or sponsor authorization.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure identity backends and hypervisor isolation. Where configured in the system's Terraform blueprints, the platform enforces least-privilege IAM bindings, Identity-Aware Proxy (IAP) TCP/HTTPS forwarding, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### IA-12(2) Identity Proofing | Identity Evidence

Require evidence of individual identification be presented to the registration authority.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure identity backends and hypervisor isolation. Where configured in the system's Terraform blueprints, the platform enforces least-privilege IAM bindings, Identity-Aware Proxy (IAP) TCP/HTTPS forwarding, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### IA-12(3) Identity Proofing | Identity Evidence Validation and Verification

Require that the presented identity evidence be validated and verified through [Assignment: organizational defined methods of validation and verification].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure identity backends and hypervisor isolation. Where configured in the system's Terraform blueprints, the platform enforces least-privilege IAM bindings, Identity-Aware Proxy (IAP) TCP/HTTPS forwarding, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### IA-12(4) Identity Proofing | In-person Validation and Verification

Require that the validation and verification of identity evidence be conducted in person before a designated registration authority.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure identity backends and hypervisor isolation. Where configured in the system's Terraform blueprints, the platform enforces least-privilege IAM bindings, Identity-Aware Proxy (IAP) TCP/HTTPS forwarding, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### IA-12(5) Identity Proofing | Address Confirmation

Require that a [Selection: registration code; notice of proofing] be delivered through an out-of-band channel to verify the users address (physical or digital) of record.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure identity backends and hypervisor isolation. Where configured in the system's Terraform blueprints, the platform enforces least-privilege IAM bindings, Identity-Aware Proxy (IAP) TCP/HTTPS forwarding, VPC Service Controls perimeters, and Google Organization Policy constraints. |
| **FedRAMP Additional Guidance**: Guidance: In accordance with NIST SP 800-63A Enrollment and Identity Proofing |


## 2.8 Incident Response


### IR-1 Policy and Procedures


a. Develop, document, and disseminate to [Assignment: organization-defined personnel or roles]:

  1. [Selection (one or more): Organization-level; Mission/business process-level; System-level] incident response policy that:

    (a) Addresses purpose, scope, roles, responsibilities, management commitment, coordination among organizational entities, and compliance; and

    (b) Is consistent with applicable laws, executive orders, directives, regulations, policies, standards, and guidelines; and

  2. Procedures to facilitate the implementation of the incident response policy and the associated incident response controls;


b. Designate an [Assignment: organization-defined official] to manage the development, documentation, and dissemination of the incident response policy and procedures; and


c. Review and update the current incident response:

  1. Policy [Assignment: organization-defined frequency — FedRAMP High: at least annually] and following [Assignment: organization-defined events — FedRAMP High: significant changes]; and

  2. Procedures [Assignment: organization-defined frequency — FedRAMP High: at least annually] and following [Assignment: organization-defined events].


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Officer (ISSO) / IR Team & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC Incident Response team and Site Reliability Engineers (SREs) monitor and remediate infrastructure incidents (Inherited). System-level security events are detected via {{ THREAT_DETECTION_ENGINE }}, routed through Cloud Pub/Sub, and alerted to the organizational IR team and {{ CSSP_PROVIDER }}. |
| **FedRAMP High Parameter Values**: `ir-01_odp.05` (frequency): at least annually; `ir-01_odp.07` (frequency): at least annually; `ir-01_odp.08` (events): significant changes |


### IR-2 Incident Response Training


a. Provide incident response training to system users consistent with assigned roles and responsibilities:

  1. Within [Assignment: organization-defined time period — FedRAMP High: ten (10) days for privileged users, thirty (30) days for Incident Response roles] of assuming an incident response role or responsibility or acquiring system access;

  2. When required by system changes; and

  3. [Assignment: organization-defined frequency — FedRAMP High: at least annually] thereafter; and


b. Review and update incident response training content [Assignment: organization-defined frequency — FedRAMP High: at least annually] and following [Assignment: organization-defined events].


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Officer (ISSO) / IR Team & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC Incident Response team and Site Reliability Engineers (SREs) monitor and remediate infrastructure incidents (Inherited). System-level security events are detected via {{ THREAT_DETECTION_ENGINE }}, routed through Cloud Pub/Sub, and alerted to the organizational IR team and {{ CSSP_PROVIDER }}. |
| **FedRAMP High Parameter Values**: `ir-02_odp.01` (time period): ten (10) days for privileged users, thirty (30) days for Incident Response roles; `ir-02_odp.02` (frequency): at least annually; `ir-02_odp.03` (frequency): at least annually |


### IR-2(1) Incident Response Training | Simulated Events

Incorporate simulated events into incident response training to facilitate the required response by personnel in crisis situations.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Officer (ISSO) / IR Team & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC Incident Response team and Site Reliability Engineers (SREs) monitor and remediate infrastructure incidents (Inherited). System-level security events are detected via {{ THREAT_DETECTION_ENGINE }}, routed through Cloud Pub/Sub, and alerted to the organizational IR team and {{ CSSP_PROVIDER }}. |


### IR-2(2) Incident Response Training | Automated Training Environments

Provide an incident response training environment using [Assignment: organization-defined automated mechanisms].


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Officer (ISSO) / IR Team & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC Incident Response team and Site Reliability Engineers (SREs) monitor and remediate infrastructure incidents (Inherited). System-level security events are detected via {{ THREAT_DETECTION_ENGINE }}, routed through Cloud Pub/Sub, and alerted to the organizational IR team and {{ CSSP_PROVIDER }}. |


### IR-2(3) Incident Response Training | Breach

Provide incident response training on how to identify and respond to a breach, including the organization's process for reporting a breach.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) & Incident Response Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [x] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud infrastructure. [CONFIG_REQUIRED: Document the Mission Owner implementation and verification procedures for IR-2(3) (Breach) within the {{ DOD_IMPACT_LABEL }} boundary and confirm Implementation Status] |


### IR-3 Incident Response Testing

Test the effectiveness of the incident response capability for the system [Assignment: organization-defined frequency — FedRAMP High: at least every six (6) months, including functional at least annually] using the following tests: [Assignment: organization-defined tests].


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Officer (ISSO) / IR Team & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC Incident Response team and Site Reliability Engineers (SREs) monitor and remediate infrastructure incidents (Inherited). System-level security events are detected via {{ THREAT_DETECTION_ENGINE }}, routed through Cloud Pub/Sub, and alerted to the organizational IR team and {{ CSSP_PROVIDER }}. |
| **FedRAMP High Parameter Values**: `ir-03_odp.01` (frequency): at least every six (6) months, including functional at least annually<br>**FedRAMP Additional Guidance**: Requirement: The service provider defines tests and/or exercises in accordance with NIST Special Publication 800-61 (as amended). Functional testing must occur prior to testing for initial authorization. Annual functional testing may be concurrent with required penetration tests (see CA-8). The service provider provides test plans to the AO annually. Test plans are approved and accepted by the AO prior to test commencing. |


### IR-3(2) Incident Response Testing | Coordination with Related Plans

Coordinate incident response testing with organizational elements responsible for related plans.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Officer (ISSO) / IR Team & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC Incident Response team and Site Reliability Engineers (SREs) monitor and remediate infrastructure incidents (Inherited). System-level security events are detected via {{ THREAT_DETECTION_ENGINE }}, routed through Cloud Pub/Sub, and alerted to the organizational IR team and {{ CSSP_PROVIDER }}. |


### IR-4 Incident Handling


a. Implement an incident handling capability for incidents that is consistent with the incident response plan and includes preparation, detection and analysis, containment, eradication, and recovery;


b. Coordinate incident handling activities with contingency planning activities;


c. Incorporate lessons learned from ongoing incident handling activities into incident response procedures, training, and testing, and implement the resulting changes accordingly; and


d. Ensure the rigor, intensity, scope, and results of incident handling activities are comparable and predictable across the organization.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Officer (ISSO) / IR Team & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC Incident Response team and Site Reliability Engineers (SREs) monitor and remediate infrastructure incidents (Inherited). System-level security events are detected via {{ THREAT_DETECTION_ENGINE }}, routed through Cloud Pub/Sub, and alerted to the organizational IR team and {{ CSSP_PROVIDER }}. |
| **FedRAMP Additional Guidance**: Requirement: The FISMA definition of "incident" shall be used: "An occurrence that actually or imminently jeopardizes, without lawful authority, the confidentiality, integrity, or availability of information or an information system; or constitutes a violation or imminent threat of violation of law, security policies, security procedures, or acceptable use policies." Requirement: The service provider ensures that individuals conducting incident handling meet personnel security requirements commensurate with the criticality/sensitivity of the information being processed, stored, and transmitted by the information system. |


### IR-4(1) Incident Handling | Automated Incident Handling Processes

Support the incident handling process using [Assignment: organization-defined automated mechanisms].


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Officer (ISSO) / IR Team & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC Incident Response team and Site Reliability Engineers (SREs) monitor and remediate infrastructure incidents (Inherited). System-level security events are detected via {{ THREAT_DETECTION_ENGINE }}, routed through Cloud Pub/Sub, and alerted to the organizational IR team and {{ CSSP_PROVIDER }}. |


### IR-4(2) Incident Handling | Dynamic Reconfiguration

Include the following types of dynamic reconfiguration for [Assignment: organization-defined system components — FedRAMP High: all network, data storage, and computing devices] as part of the incident response capability: [Assignment: organization-defined types of dynamic reconfiguration].


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Officer (ISSO) / IR Team & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC Incident Response team and Site Reliability Engineers (SREs) monitor and remediate infrastructure incidents (Inherited). System-level security events are detected via {{ THREAT_DETECTION_ENGINE }}, routed through Cloud Pub/Sub, and alerted to the organizational IR team and {{ CSSP_PROVIDER }}. |
| **FedRAMP High Parameter Values**: `ir-04.02_odp.02` (system components): all network, data storage, and computing devices |


### IR-4(3) Incident Handling | Continuity of Operations

Identify [Assignment: organization-defined classes of incidents] and take the following actions in response to those incidents to ensure continuation of organizational mission and business functions: [Assignment: organization-defined actions to take in response to classes of incidents].


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Officer (ISSO) / IR Team & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC Incident Response team and Site Reliability Engineers (SREs) monitor and remediate infrastructure incidents (Inherited). System-level security events are detected via {{ THREAT_DETECTION_ENGINE }}, routed through Cloud Pub/Sub, and alerted to the organizational IR team and {{ CSSP_PROVIDER }}. |


### IR-4(4) Incident Handling | Information Correlation

Correlate incident information and individual incident responses to achieve an organization-wide perspective on incident awareness and response.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Officer (ISSO) / IR Team & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC Incident Response team and Site Reliability Engineers (SREs) monitor and remediate infrastructure incidents (Inherited). System-level security events are detected via {{ THREAT_DETECTION_ENGINE }}, routed through Cloud Pub/Sub, and alerted to the organizational IR team and {{ CSSP_PROVIDER }}. |


### IR-4(6) Incident Handling | Insider Threats

Implement an incident handling capability for incidents involving insider threats.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Officer (ISSO) / IR Team & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC Incident Response team and Site Reliability Engineers (SREs) monitor and remediate infrastructure incidents (Inherited). System-level security events are detected via {{ THREAT_DETECTION_ENGINE }}, routed through Cloud Pub/Sub, and alerted to the organizational IR team and {{ CSSP_PROVIDER }}. |


### IR-4(7) Incident Handling | Insider Threats — Intra-organization Coordination

Coordinate an incident handling capability for insider threats that includes the following organizational entities [Assignment: organization-defined entities].


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Officer (ISSO) / IR Team & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC Incident Response team and Site Reliability Engineers (SREs) monitor and remediate infrastructure incidents (Inherited). System-level security events are detected via {{ THREAT_DETECTION_ENGINE }}, routed through Cloud Pub/Sub, and alerted to the organizational IR team and {{ CSSP_PROVIDER }}. |


### IR-4(8) Incident Handling | Correlation with External Organizations

Coordinate with [Assignment: organization-defined external organizations] to correlate and share [Assignment: organization-defined incident information] to achieve a cross-organization perspective on incident awareness and more effective incident responses.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Officer (ISSO) / IR Team & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC Incident Response team and Site Reliability Engineers (SREs) monitor and remediate infrastructure incidents (Inherited). System-level security events are detected via {{ THREAT_DETECTION_ENGINE }}, routed through Cloud Pub/Sub, and alerted to the organizational IR team and {{ CSSP_PROVIDER }}. |


### IR-4(10) Incident Handling | Supply Chain Coordination

Coordinate incident handling activities involving supply chain events with other organizations involved in the supply chain.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Officer (ISSO) / IR Team & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC Incident Response team and Site Reliability Engineers (SREs) monitor and remediate infrastructure incidents (Inherited). System-level security events are detected via {{ THREAT_DETECTION_ENGINE }}, routed through Cloud Pub/Sub, and alerted to the organizational IR team and {{ CSSP_PROVIDER }}. |


### IR-4(11) Incident Handling | Integrated Incident Response Team

Establish and maintain an integrated incident response team that can be deployed to any location identified by the organization in [Assignment: organization-defined time period].


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Officer (ISSO) / IR Team & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC Incident Response team and Site Reliability Engineers (SREs) monitor and remediate infrastructure incidents (Inherited). System-level security events are detected via {{ THREAT_DETECTION_ENGINE }}, routed through Cloud Pub/Sub, and alerted to the organizational IR team and {{ CSSP_PROVIDER }}. |


### IR-4(12) Incident Handling | Malicious Code and Forensic Analysis

Analyze malicious code and/or other residual artifacts remaining in the system after the incident.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Officer (ISSO) / IR Team & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC Incident Response team and Site Reliability Engineers (SREs) monitor and remediate infrastructure incidents (Inherited). System-level security events are detected via {{ THREAT_DETECTION_ENGINE }}, routed through Cloud Pub/Sub, and alerted to the organizational IR team and {{ CSSP_PROVIDER }}. |


### IR-4(13) Incident Handling | Behavior Analysis

Analyze anomalous or suspected adversarial behavior in or related to [Assignment: organization-defined environments or resources].


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Officer (ISSO) / IR Team & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC Incident Response team and Site Reliability Engineers (SREs) monitor and remediate infrastructure incidents (Inherited). System-level security events are detected via {{ THREAT_DETECTION_ENGINE }}, routed through Cloud Pub/Sub, and alerted to the organizational IR team and {{ CSSP_PROVIDER }}. |


### IR-4(14) Incident Handling | Security Operations Center

Establish and maintain a security operations center.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Officer (ISSO) / IR Team & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC Incident Response team and Site Reliability Engineers (SREs) monitor and remediate infrastructure incidents (Inherited). System-level security events are detected via {{ THREAT_DETECTION_ENGINE }}, routed through Cloud Pub/Sub, and alerted to the organizational IR team and {{ CSSP_PROVIDER }}. |


### IR-5 Incident Monitoring

Track and document incidents.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Officer (ISSO) / IR Team & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC Incident Response team and Site Reliability Engineers (SREs) monitor and remediate infrastructure incidents (Inherited). System-level security events are detected via {{ THREAT_DETECTION_ENGINE }}, routed through Cloud Pub/Sub, and alerted to the organizational IR team and {{ CSSP_PROVIDER }}. |


### IR-5(1) Incident Monitoring | Automated Tracking, Data Collection, and Analysis

Track incidents and collect and analyze incident information using [Assignment: organization-defined automated mechanisms].


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Officer (ISSO) / IR Team & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC Incident Response team and Site Reliability Engineers (SREs) monitor and remediate infrastructure incidents (Inherited). System-level security events are detected via {{ THREAT_DETECTION_ENGINE }}, routed through Cloud Pub/Sub, and alerted to the organizational IR team and {{ CSSP_PROVIDER }}. |


### IR-6 Incident Reporting


a. Require personnel to report suspected incidents to the organizational incident response capability within [Assignment: organization-defined time period — FedRAMP High: US-CERT incident reporting timelines as specified in NIST Special Publication 800-61 (as amended)]; and


b. Report incident information to [Assignment: organization-defined authorities].


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Officer (ISSO) / IR Team & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC Incident Response team and Site Reliability Engineers (SREs) monitor and remediate infrastructure incidents (Inherited). System-level security events are detected via {{ THREAT_DETECTION_ENGINE }}, routed through Cloud Pub/Sub, and alerted to the organizational IR team and {{ CSSP_PROVIDER }}. |
| **FedRAMP High Parameter Values**: `ir-06_odp.01` (time period): US-CERT incident reporting timelines as specified in NIST Special Publication 800-61 (as amended)<br>**FedRAMP Additional Guidance**: Requirement: Reports security incident information according to FedRAMP Incident Communications Procedure. |


### IR-6(1) Incident Reporting | Automated Reporting

Report incidents using [Assignment: organization-defined automated mechanisms].


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Officer (ISSO) / IR Team & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC Incident Response team and Site Reliability Engineers (SREs) monitor and remediate infrastructure incidents (Inherited). System-level security events are detected via {{ THREAT_DETECTION_ENGINE }}, routed through Cloud Pub/Sub, and alerted to the organizational IR team and {{ CSSP_PROVIDER }}. |


### IR-6(2) Incident Reporting | Vulnerabilities Related to Incidents

Report system vulnerabilities associated with reported incidents to [Assignment: organization-defined personnel or roles].


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Officer (ISSO) / IR Team & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC Incident Response team and Site Reliability Engineers (SREs) monitor and remediate infrastructure incidents (Inherited). System-level security events are detected via {{ THREAT_DETECTION_ENGINE }}, routed through Cloud Pub/Sub, and alerted to the organizational IR team and {{ CSSP_PROVIDER }}. |


### IR-6(3) Incident Reporting | Supply Chain Coordination

Provide incident information to the provider of the product or service and other organizations involved in the supply chain or supply chain governance for systems or system components related to the incident.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Officer (ISSO) / IR Team & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC Incident Response team and Site Reliability Engineers (SREs) monitor and remediate infrastructure incidents (Inherited). System-level security events are detected via {{ THREAT_DETECTION_ENGINE }}, routed through Cloud Pub/Sub, and alerted to the organizational IR team and {{ CSSP_PROVIDER }}. |


### IR-7 Incident Response Assistance

Provide an incident response support resource, integral to the organizational incident response capability, that offers advice and assistance to users of the system for the handling and reporting of incidents.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Officer (ISSO) / IR Team & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC Incident Response team and Site Reliability Engineers (SREs) monitor and remediate infrastructure incidents (Inherited). System-level security events are detected via {{ THREAT_DETECTION_ENGINE }}, routed through Cloud Pub/Sub, and alerted to the organizational IR team and {{ CSSP_PROVIDER }}. |


### IR-7(1) Incident Response Assistance | Automation Support for Availability of Information and Support

Increase the availability of incident response information and support using [Assignment: organization-defined automated mechanisms].


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Officer (ISSO) / IR Team & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC Incident Response team and Site Reliability Engineers (SREs) monitor and remediate infrastructure incidents (Inherited). System-level security events are detected via {{ THREAT_DETECTION_ENGINE }}, routed through Cloud Pub/Sub, and alerted to the organizational IR team and {{ CSSP_PROVIDER }}. |


### IR-7(2) Incident Response Assistance | Coordination with External Providers


(a) Establish a direct, cooperative relationship between its incident response capability and external providers of system protection capability; and


(b) Identify organizational incident response team members to the external providers.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Officer (ISSO) / IR Team & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC Incident Response team and Site Reliability Engineers (SREs) monitor and remediate infrastructure incidents (Inherited). System-level security events are detected via {{ THREAT_DETECTION_ENGINE }}, routed through Cloud Pub/Sub, and alerted to the organizational IR team and {{ CSSP_PROVIDER }}. |


### IR-8 Incident Response Plan


a. Develop an incident response plan that:

  1. Provides the organization with a roadmap for implementing its incident response capability;

  2. Describes the structure and organization of the incident response capability;

  3. Provides a high-level approach for how the incident response capability fits into the overall organization;

  4. Meets the unique requirements of the organization, which relate to mission, size, structure, and functions;

  5. Defines reportable incidents;

  6. Provides metrics for measuring the incident response capability within the organization;

  7. Defines the resources and management support needed to effectively maintain and mature an incident response capability;

  8. Addresses the sharing of incident information;

  9. Is reviewed and approved by [Assignment: organization-defined personnel or roles] [Assignment: organization-defined frequency — FedRAMP High: at least annually]; and

  10. Explicitly designates responsibility for incident response to [Assignment: organization-defined entities, personnel, or roles].


b. Distribute copies of the incident response plan to [Assignment: organization-defined incident response personnel (identified by name and/or by role) and organizational elements — FedRAMP High: see additional FedRAMP Requirements and Guidance];


c. Update the incident response plan to address system and organizational changes or problems encountered during plan implementation, execution, or testing;


d. Communicate incident response plan changes to [Assignment: organization-defined incident response personnel (identified by name and/or by role) and organizational elements — FedRAMP High: see additional FedRAMP Requirements and Guidance]; and


e. Protect the incident response plan from unauthorized disclosure and modification.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Officer (ISSO) / IR Team & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC Incident Response team and Site Reliability Engineers (SREs) monitor and remediate infrastructure incidents (Inherited). System-level security events are detected via {{ THREAT_DETECTION_ENGINE }}, routed through Cloud Pub/Sub, and alerted to the organizational IR team and {{ CSSP_PROVIDER }}. |
| **FedRAMP High Parameter Values**: `ir-08_odp.02` (frequency): at least annually; `ir-08_odp.04` (incident response personnel): see additional FedRAMP Requirements and Guidance; `ir-08_odp.05` (organizational elements): see additional FedRAMP Requirements and Guidance; `ir-08_odp.06` (incident response personnel): see additional FedRAMP Requirements and Guidance; `ir-08_odp.07` (organizational elements): see additional FedRAMP Requirements and Guidance<br>**FedRAMP Additional Guidance**: (b) Requirement: The service provider defines a list of incident response personnel (identified by name and/or by role) and organizational elements. The incident response list includes designated FedRAMP personnel. (d) Requirement: The service provider defines a list of incident response personnel (identified by name and/or by role) and organizational elements. The incident response list includes designated FedRAMP personnel. |


### IR-8(1) Incident Response Plan | Breaches

Include the following in the Incident Response Plan for breaches involving personally identifiable information:

(a) A process to determine if notice to individuals or other organizations, including oversight organizations, is needed;

(b) An assessment process to determine the extent of the harm, embarrassment, inconvenience, or unfairness to affected individuals and any mechanisms to mitigate such harms; and

(c) Identification of applicable privacy requirements.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) & Incident Response Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [x] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud infrastructure. [CONFIG_REQUIRED: Document the Mission Owner implementation and verification procedures for IR-8(1) (Breaches) within the {{ DOD_IMPACT_LABEL }} boundary and confirm Implementation Status] |


### IR-9 Information Spillage Response

Respond to information spills by:


a. Assigning [Assignment: organization-defined personnel or roles] with responsibility for responding to information spills;


b. Identifying the specific information involved in the system contamination;


c. Alerting [Assignment: organization-defined personnel or roles] of the information spill using a method of communication not associated with the spill;


d. Isolating the contaminated system or system component;


e. Eradicating the information from the contaminated system or component;


f. Identifying other systems or system components that may have been subsequently contaminated; and


g. Performing the following additional actions: [Assignment: organization-defined actions].


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Officer (ISSO) / IR Team & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC Incident Response team and Site Reliability Engineers (SREs) monitor and remediate infrastructure incidents (Inherited). System-level security events are detected via {{ THREAT_DETECTION_ENGINE }}, routed through Cloud Pub/Sub, and alerted to the organizational IR team and {{ CSSP_PROVIDER }}. |


### IR-9(2) Information Spillage Response | Training

Provide information spillage response training [Assignment: organization-defined frequency — FedRAMP High: at least annually].


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Officer (ISSO) / IR Team & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC Incident Response team and Site Reliability Engineers (SREs) monitor and remediate infrastructure incidents (Inherited). System-level security events are detected via {{ THREAT_DETECTION_ENGINE }}, routed through Cloud Pub/Sub, and alerted to the organizational IR team and {{ CSSP_PROVIDER }}. |
| **FedRAMP High Parameter Values**: `ir-09.02_odp` (frequency): at least annually |


### IR-9(3) Information Spillage Response | Post-spill Operations

Implement the following procedures to ensure that organizational personnel impacted by information spills can continue to carry out assigned tasks while contaminated systems are undergoing corrective actions: [Assignment: organization-defined procedures].


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Officer (ISSO) / IR Team & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC Incident Response team and Site Reliability Engineers (SREs) monitor and remediate infrastructure incidents (Inherited). System-level security events are detected via {{ THREAT_DETECTION_ENGINE }}, routed through Cloud Pub/Sub, and alerted to the organizational IR team and {{ CSSP_PROVIDER }}. |


### IR-9(4) Information Spillage Response | Exposure to Unauthorized Personnel

Employ the following controls for personnel exposed to information not within assigned access authorizations: [Assignment: organization-defined controls].


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Officer (ISSO) / IR Team & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC Incident Response team and Site Reliability Engineers (SREs) monitor and remediate infrastructure incidents (Inherited). System-level security events are detected via {{ THREAT_DETECTION_ENGINE }}, routed through Cloud Pub/Sub, and alerted to the organizational IR team and {{ CSSP_PROVIDER }}. |


## 2.9 Maintenance


### MA-1 Policy and Procedures


a. Develop, document, and disseminate to [Assignment: organization-defined personnel or roles]:

  1. [Selection (one or more): Organization-level; Mission/business process-level; System-level] maintenance policy that:

    (a) Addresses purpose, scope, roles, responsibilities, management commitment, coordination among organizational entities, and compliance; and

    (b) Is consistent with applicable laws, executive orders, directives, regulations, policies, standards, and guidelines; and

  2. Procedures to facilitate the implementation of the maintenance policy and the associated maintenance controls;


b. Designate an [Assignment: organization-defined official] to manage the development, documentation, and dissemination of the maintenance policy and procedures; and


c. Review and update the current maintenance:

  1. Policy [Assignment: organization-defined frequency — FedRAMP High: at least annually] and following [Assignment: organization-defined events — FedRAMP High: significant changes]; and

  2. Procedures [Assignment: organization-defined frequency — FedRAMP High: at least annually] and following [Assignment: organization-defined events].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC maintains maintenance policy and procedures for Google infrastructure, inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }}. Policy and procedures controls are shared responsibilities and are not 100% inheritable (FedRAMP SSP Appendix A / DoD CC SRG). [CONFIG_REQUIRED: Reference the organization's maintenance policy and procedures that apply to the system, including the review frequency] |
| **FedRAMP High Parameter Values**: `ma-01_odp.05` (frequency): at least annually; `ma-01_odp.07` (frequency): at least annually; `ma-01_odp.08` (events): significant changes |


### MA-2 Controlled Maintenance


a. Schedule, document, and review records of maintenance, repair, and replacement on system components in accordance with manufacturer or vendor specifications and/or organizational requirements;


b. Approve and monitor all maintenance activities, whether performed on site or remotely and whether the system or system components are serviced on site or removed to another location;


c. Require that [Assignment: organization-defined personnel or roles] explicitly approve the removal of the system or system components from organizational facilities for off-site maintenance, repair, or replacement;


d. Sanitize equipment to remove the following information from associated media prior to removal from organizational facilities for off-site maintenance, repair, or replacement: [Assignment: organization-defined information];


e. Check all potentially impacted controls to verify that the controls are still functioning properly following maintenance, repair, or replacement actions; and


f. Include the following information in organizational maintenance records: [Assignment: organization-defined information].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for the Google-managed infrastructure that hosts the system. [CONFIG_REQUIRED: Confirm in the Google Cloud {{ DOD_IMPACT_LABEL }} / {{ BASE_FEDRAMP_LABEL }} customer responsibility matrix whether MA-2 is inherited or shared; document customer-configured controls and verify Implementation Status] |


### MA-2(2) Controlled Maintenance | Automated Maintenance Activities


(a) Schedule, conduct, and document maintenance, repair, and replacement actions for the system using [Assignment: organization-defined automated mechanisms]; and


(b) Produce up-to date, accurate, and complete records of all maintenance, repair, and replacement actions requested, scheduled, in process, and completed.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for the Google-managed infrastructure that hosts the system. [CONFIG_REQUIRED: Confirm in the Google Cloud {{ DOD_IMPACT_LABEL }} / {{ BASE_FEDRAMP_LABEL }} customer responsibility matrix whether MA-2(2) is inherited or shared; document customer-configured controls and verify Implementation Status] |


### MA-3 Maintenance Tools


a. Approve, control, and monitor the use of system maintenance tools; and


b. Review previously approved system maintenance tools [Assignment: organization-defined frequency — FedRAMP High: at least annually].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for the Google-managed infrastructure that hosts the system. [CONFIG_REQUIRED: Confirm in the Google Cloud {{ DOD_IMPACT_LABEL }} / {{ BASE_FEDRAMP_LABEL }} customer responsibility matrix whether MA-3 is inherited or shared; document customer-configured controls and verify Implementation Status] |
| **FedRAMP High Parameter Values**: `ma-03_odp` (frequency): at least annually |


### MA-3(1) Maintenance Tools | Inspect Tools

Inspect the maintenance tools used by maintenance personnel for improper or unauthorized modifications.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for the Google-managed infrastructure that hosts the system. [CONFIG_REQUIRED: Confirm in the Google Cloud {{ DOD_IMPACT_LABEL }} / {{ BASE_FEDRAMP_LABEL }} customer responsibility matrix whether MA-3(1) is inherited or shared; document customer-configured controls and verify Implementation Status] |


### MA-3(2) Maintenance Tools | Inspect Media

Check media containing diagnostic and test programs for malicious code before the media are used in the system.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for the Google-managed infrastructure that hosts the system. [CONFIG_REQUIRED: Confirm in the Google Cloud {{ DOD_IMPACT_LABEL }} / {{ BASE_FEDRAMP_LABEL }} customer responsibility matrix whether MA-3(2) is inherited or shared; document customer-configured controls and verify Implementation Status] |


### MA-3(3) Maintenance Tools | Prevent Unauthorized Removal

Prevent the removal of maintenance equipment containing organizational information by:


(a) Verifying that there is no organizational information contained on the equipment;


(b) Sanitizing or destroying the equipment;


(c) Retaining the equipment within the facility; or


(d) Obtaining an exemption from [Assignment: organization-defined personnel or roles — FedRAMP High: the information owner] explicitly authorizing removal of the equipment from the facility.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for the Google-managed infrastructure that hosts the system. [CONFIG_REQUIRED: Confirm in the Google Cloud {{ DOD_IMPACT_LABEL }} / {{ BASE_FEDRAMP_LABEL }} customer responsibility matrix whether MA-3(3) is inherited or shared; document customer-configured controls and verify Implementation Status] |
| **FedRAMP High Parameter Values**: `ma-03.03_odp` (personnel or roles): the information owner |


### MA-3(4) Maintenance Tools | Restricted Tool Use

Restrict the use of maintenance tools to authorized personnel only.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for the Google-managed infrastructure that hosts the system. [CONFIG_REQUIRED: Confirm in the Google Cloud {{ DOD_IMPACT_LABEL }} / {{ BASE_FEDRAMP_LABEL }} customer responsibility matrix whether MA-3(4) is inherited or shared; document customer-configured controls and verify Implementation Status] |


### MA-3(5) Maintenance Tools | Execution with Privilege

Monitor the use of maintenance tools that execute with increased privilege.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for the Google-managed infrastructure that hosts the system. [CONFIG_REQUIRED: Confirm in the Google Cloud {{ DOD_IMPACT_LABEL }} / {{ BASE_FEDRAMP_LABEL }} customer responsibility matrix whether MA-3(5) is inherited or shared; document customer-configured controls and verify Implementation Status] |


### MA-3(6) Maintenance Tools | Software Updates and Patches

Inspect maintenance tools to ensure the latest software updates and patches are installed.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for the Google-managed infrastructure that hosts the system. [CONFIG_REQUIRED: Confirm in the Google Cloud {{ DOD_IMPACT_LABEL }} / {{ BASE_FEDRAMP_LABEL }} customer responsibility matrix whether MA-3(6) is inherited or shared; document customer-configured controls and verify Implementation Status] |


### MA-4 Nonlocal Maintenance


a. Approve and monitor nonlocal maintenance and diagnostic activities;


b. Allow the use of nonlocal maintenance and diagnostic tools only as consistent with organizational policy and documented in the security plan for the system;


c. Employ strong authentication in the establishment of nonlocal maintenance and diagnostic sessions;


d. Maintain records for nonlocal maintenance and diagnostic activities; and


e. Terminate session and network connections when nonlocal maintenance is completed.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for the Google-managed infrastructure that hosts the system. [CONFIG_REQUIRED: Confirm in the Google Cloud {{ DOD_IMPACT_LABEL }} / {{ BASE_FEDRAMP_LABEL }} customer responsibility matrix whether MA-4 is inherited or shared; document customer-configured controls and verify Implementation Status] |


### MA-4(1) Nonlocal Maintenance | Logging and Review


(a) Log [Assignment: organization-defined audit events] for nonlocal maintenance and diagnostic sessions; and


(b) Review the audit records of the maintenance and diagnostic sessions to detect anomalous behavior.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for the Google-managed infrastructure that hosts the system. [CONFIG_REQUIRED: Confirm in the Google Cloud {{ DOD_IMPACT_LABEL }} / {{ BASE_FEDRAMP_LABEL }} customer responsibility matrix whether MA-4(1) is inherited or shared; document customer-configured controls and verify Implementation Status] |


### MA-4(3) Nonlocal Maintenance | Comparable Security and Sanitization


(a) Require that nonlocal maintenance and diagnostic services be performed from a system that implements a security capability comparable to the capability implemented on the system being serviced; or


(b) Remove the component to be serviced from the system prior to nonlocal maintenance or diagnostic services; sanitize the component (for organizational information); and after the service is performed, inspect and sanitize the component (for potentially malicious software) before reconnecting the component to the system.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for the Google-managed infrastructure that hosts the system. [CONFIG_REQUIRED: Confirm in the Google Cloud {{ DOD_IMPACT_LABEL }} / {{ BASE_FEDRAMP_LABEL }} customer responsibility matrix whether MA-4(3) is inherited or shared; document customer-configured controls and verify Implementation Status] |


### MA-4(4) Nonlocal Maintenance | Authentication and Separation of Maintenance Sessions

Protect nonlocal maintenance sessions by:


(a) Employing [Assignment: organization-defined authenticators that are replay resistant]; and


(b) Separating the maintenance sessions from other network sessions with the system by either:

  (1) Physically separated communications paths; or

  (2) Logically separated communications paths.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for the Google-managed infrastructure that hosts the system. [CONFIG_REQUIRED: Confirm in the Google Cloud {{ DOD_IMPACT_LABEL }} / {{ BASE_FEDRAMP_LABEL }} customer responsibility matrix whether MA-4(4) is inherited or shared; document customer-configured controls and verify Implementation Status] |


### MA-4(6) Nonlocal Maintenance | Cryptographic Protection

Implement the following cryptographic mechanisms to protect the integrity and confidentiality of nonlocal maintenance and diagnostic communications: [Assignment: organization-defined cryptographic mechanisms].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for the Google-managed infrastructure that hosts the system. [CONFIG_REQUIRED: Confirm in the Google Cloud {{ DOD_IMPACT_LABEL }} / {{ BASE_FEDRAMP_LABEL }} customer responsibility matrix whether MA-4(6) is inherited or shared; document customer-configured controls and verify Implementation Status] |


### MA-4(7) Nonlocal Maintenance | Disconnect Verification

Verify session and network connection termination after the completion of nonlocal maintenance and diagnostic sessions.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for the Google-managed infrastructure that hosts the system. [CONFIG_REQUIRED: Confirm in the Google Cloud {{ DOD_IMPACT_LABEL }} / {{ BASE_FEDRAMP_LABEL }} customer responsibility matrix whether MA-4(7) is inherited or shared; document customer-configured controls and verify Implementation Status] |


### MA-5 Maintenance Personnel


a. Establish a process for maintenance personnel authorization and maintain a list of authorized maintenance organizations or personnel;


b. Verify that non-escorted personnel performing maintenance on the system possess the required access authorizations; and


c. Designate organizational personnel with required access authorizations and technical competence to supervise the maintenance activities of personnel who do not possess the required access authorizations.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for the Google-managed infrastructure that hosts the system. [CONFIG_REQUIRED: Confirm in the Google Cloud {{ DOD_IMPACT_LABEL }} / {{ BASE_FEDRAMP_LABEL }} customer responsibility matrix whether MA-5 is inherited or shared; document customer-configured controls and verify Implementation Status] |


### MA-5(1) Maintenance Personnel | Individuals Without Appropriate Access

> [!IMPORTANT]
> [WARNING: RMF TEAM ACTION REQUIRED: Verify and update operational procedure or contact details in this section.]

(a) Implement procedures for the use of maintenance personnel that lack appropriate security clearances or are not U.S. citizens, that include the following requirements:

  (1) Maintenance personnel who do not have needed access authorizations, clearances, or formal access approvals are escorted and supervised during the performance of maintenance and diagnostic activities on the system by approved organizational personnel who are fully cleared, have appropriate access authorizations, and are technically qualified; and

  (2) Prior to initiating maintenance or diagnostic activities by personnel who do not have needed access authorizations, clearances or formal access approvals, all volatile information storage components within the system are sanitized and all nonvolatile storage media are removed or physically disconnected from the system and secured; and


(b) Develop and implement [Assignment: organization-defined alternate controls] in the event a system component cannot be sanitized, removed, or disconnected from the system.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for the Google-managed infrastructure that hosts the system. [CONFIG_REQUIRED: Confirm in the Google Cloud {{ DOD_IMPACT_LABEL }} / {{ BASE_FEDRAMP_LABEL }} customer responsibility matrix whether MA-5(1) is inherited or shared; document customer-configured controls and verify Implementation Status] |


### MA-5(2) Maintenance Personnel | Security Clearances for Classified Systems

Verify that personnel performing maintenance and diagnostic activities on a system processing, storing, or transmitting classified information possess security clearances and formal access approvals for at least the highest classification level and for compartments of information on the system.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider & Mission Owner Security Officer |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [x] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for classified cloud enclave facility and hardware maintenance personnel. [CONFIG_REQUIRED: Verify that all CSP and Mission Owner maintenance and diagnostic personnel hold active SECRET or higher security clearances and formal access approvals in DISS / JPAS for the {{ DOD_IMPACT_LABEL }} boundary and confirm Implementation Status] |


### MA-5(3) Maintenance Personnel | Citizenship Requirements for Classified Systems

Verify that personnel performing maintenance and diagnostic activities on a system processing, storing, or transmitting classified information are U.S. citizens.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider & Mission Owner Security Officer |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [x] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for classified cloud enclave maintenance personnel. [CONFIG_REQUIRED: Verify U.S. citizenship adjudication records for all CSP and Mission Owner personnel performing maintenance and diagnostic activities on the {{ DOD_IMPACT_LABEL }} classified system and confirm Implementation Status] |


### MA-5(4) Maintenance Personnel | Foreign Nationals

Ensure that:

  (a) Foreign nationals with appropriate security clearances are used to conduct maintenance and diagnostic activities on classified systems only when the systems are jointly owned and operated by the United States and foreign allied governments, or owned and operated solely by foreign allied governments; and

  (b) Approvals, consents, and detailed operational conditions regarding the use of foreign nationals to conduct maintenance and diagnostic activities on classified systems are fully documented within Memoranda of Agreements.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider & Mission Owner Authorizing Official |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [x] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for classified cloud enclave maintenance personnel. [CONFIG_REQUIRED: Confirm that foreign nationals are prohibited from conducting maintenance on {{ DOD_IMPACT_LABEL }} classified systems unless explicitly authorized under a joint allied Memorandum of Agreement (MOA) approved by the Authorizing Official, and confirm Implementation Status] |


### MA-5(5) Maintenance Personnel | Non-system Maintenance

Ensure that non-escorted personnel performing maintenance activities not directly associated with the system but in the physical proximity of the system, have required access authorizations.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & System Operations Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [x] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud infrastructure. [CONFIG_REQUIRED: Document the Mission Owner implementation and verification procedures for MA-5(5) (Non-system Maintenance) within the {{ DOD_IMPACT_LABEL }} boundary and confirm Implementation Status] |


### MA-6 Timely Maintenance

Obtain maintenance support and/or spare parts for [Assignment: organization-defined system components] within [Assignment: organization-defined time period — FedRAMP High: a timeframe to support advertised uptime and availability] of failure.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for the Google-managed infrastructure that hosts the system. [CONFIG_REQUIRED: Confirm in the Google Cloud {{ DOD_IMPACT_LABEL }} / {{ BASE_FEDRAMP_LABEL }} customer responsibility matrix whether MA-6 is inherited or shared; document customer-configured controls and verify Implementation Status] |
| **FedRAMP High Parameter Values**: `ma-06_odp.02` (time period): a timeframe to support advertised uptime and availability |


### MA-6(1) Timely Maintenance | Preventive Maintenance

Perform preventive maintenance on [Assignment: organization-defined system components] at [Assignment: organization-defined time intervals].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for the Google-managed infrastructure that hosts the system. [CONFIG_REQUIRED: Confirm in the Google Cloud {{ DOD_IMPACT_LABEL }} / {{ BASE_FEDRAMP_LABEL }} customer responsibility matrix whether MA-6(1) is inherited or shared; document customer-configured controls and verify Implementation Status] |


## 2.10 Media Protection


### MP-1 Policy and Procedures


a. Develop, document, and disseminate to [Assignment: organization-defined personnel or roles]:

  1. [Selection (one or more): Organization-level; Mission/business process-level; System-level] media protection policy that:

    (a) Addresses purpose, scope, roles, responsibilities, management commitment, coordination among organizational entities, and compliance; and

    (b) Is consistent with applicable laws, executive orders, directives, regulations, policies, standards, and guidelines; and

  2. Procedures to facilitate the implementation of the media protection policy and the associated media protection controls;


b. Designate an [Assignment: organization-defined official] to manage the development, documentation, and dissemination of the media protection policy and procedures; and


c. Review and update the current media protection:

  1. Policy [Assignment: organization-defined frequency — FedRAMP High: at least annually] and following [Assignment: organization-defined events — FedRAMP High: significant changes]; and

  2. Procedures [Assignment: organization-defined frequency — FedRAMP High: at least annually] and following [Assignment: organization-defined events].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for physical media sanitization and disk shredding in accordance with NIST SP 800-88, Guidelines for Media Sanitization. Digital media within customer VPCs is protected using FIPS 140-3 validated BoringCrypto modules and Cloud KMS Customer-Managed Encryption Keys (CMEK AES-256). |
| **FedRAMP High Parameter Values**: `mp-01_odp.05` (frequency): at least annually; `mp-01_odp.07` (frequency): at least annually; `mp-01_odp.08` (events): significant changes |


### MP-2 Media Access

Restrict access to [Assignment: organization-defined types of digital and/or non-digital media — FedRAMP High: all types of digital and/or non-digital media containing sensitive information] to [Assignment: organization-defined personnel or roles].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for physical media sanitization and disk shredding in accordance with NIST SP 800-88, Guidelines for Media Sanitization. Digital media within customer VPCs is protected using FIPS 140-3 validated BoringCrypto modules and Cloud KMS Customer-Managed Encryption Keys (CMEK AES-256). |
| **FedRAMP High Parameter Values**: `mp-02_odp.01` (types of digital media): all types of digital and/or non-digital media containing sensitive information; `mp-02_odp.03` (types of non-digital media): all types of digital and/or non-digital media containing sensitive information |


### MP-3 Media Marking


a. Mark system media indicating the distribution limitations, handling caveats, and applicable security markings (if any) of the information; and


b. Exempt [Assignment: organization-defined types of system media — FedRAMP High: no removable media types] from marking if the media remain within [Assignment: organization-defined controlled areas — FedRAMP High: organization-defined security safeguards not applicable].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for physical media sanitization and disk shredding in accordance with NIST SP 800-88, Guidelines for Media Sanitization. Digital media within customer VPCs is protected using FIPS 140-3 validated BoringCrypto modules and Cloud KMS Customer-Managed Encryption Keys (CMEK AES-256). |
| **FedRAMP High Parameter Values**: `mp-03_odp.01` (types of media exempted from marking): no removable media types; `mp-03_odp.02` (controlled areas): organization-defined security safeguards not applicable<br>**FedRAMP Additional Guidance**: (b) Guidance: Second parameter not-applicable |


### MP-4 Media Storage


a. Physically control and securely store [Assignment: organization-defined types of digital and/or non-digital media — FedRAMP High: all types of digital and non-digital media with sensitive information] within [Assignment: organization-defined controlled areas — FedRAMP High: see additional FedRAMP requirements and guidance]; and


b. Protect system media types defined in MP-4a until the media are destroyed or sanitized using approved equipment, techniques, and procedures.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for physical media sanitization and disk shredding in accordance with NIST SP 800-88, Guidelines for Media Sanitization. Digital media within customer VPCs is protected using FIPS 140-3 validated BoringCrypto modules and Cloud KMS Customer-Managed Encryption Keys (CMEK AES-256). |
| **FedRAMP High Parameter Values**: `mp-04_odp.01` (types of digital media): all types of digital and non-digital media with sensitive information; `mp-04_odp.02` (types of non-digital media): all types of digital and non-digital media with sensitive information; `mp-04_odp.03` (types of digital media): all types of digital and non-digital media with sensitive information; `mp-04_odp.04` (types of non-digital media): all types of digital and non-digital media with sensitive information; `mp-04_odp.05` (controlled areas): see additional FedRAMP requirements and guidance; `mp-04_odp.06` (controlled areas): see additional FedRAMP requirements and guidance<br>**FedRAMP Additional Guidance**: (a) Requirement: The service provider defines controlled areas within facilities where the information and information system reside. |


### MP-5 Media Transport


a. Protect and control [Assignment: organization-defined types of system media — FedRAMP High: all media with sensitive information] during transport outside of controlled areas using [Assignment: organization-defined controls — FedRAMP High: prior to leaving secure/controlled environment: for digital media, encryption in compliance with Federal requirements and utilizes FIPS validated or NSA approved cryptography (see SC-13.); for non-digital media, secured in locked container];


b. Maintain accountability for system media during transport outside of controlled areas;


c. Document activities associated with the transport of system media; and


d. Restrict the activities associated with the transport of system media to authorized personnel.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for physical media sanitization and disk shredding in accordance with NIST SP 800-88, Guidelines for Media Sanitization. Digital media within customer VPCs is protected using FIPS 140-3 validated BoringCrypto modules and Cloud KMS Customer-Managed Encryption Keys (CMEK AES-256). |
| **FedRAMP High Parameter Values**: `mp-05_odp.01` (types of system media): all media with sensitive information; `mp-05_odp.02` (controls): prior to leaving secure/controlled environment: for digital media, encryption in compliance with Federal requirements and utilizes FIPS validated or NSA approved cryptography (see SC-13.); for non-digital media, secured in locked container; `mp-05_odp.03` (controls): prior to leaving secure/controlled environment: for digital media, encryption in compliance with Federal requirements and utilizes FIPS validated or NSA approved cryptography (see SC-13.); for non-digital media, secured in locked container<br>**FedRAMP Additional Guidance**: (a) Requirement: The service provider defines security measures to protect digital and non-digital media in transport. The security measures are approved and accepted by the AO. |


### MP-6 Media Sanitization


a. Sanitize [Assignment: organization-defined system media — FedRAMP High: techniques and procedures IAW NIST SP 800-88 Section 4: Reuse and Disposal of Storage Media and Hardware] prior to disposal, release out of organizational control, or release for reuse using [Assignment: organization-defined sanitization techniques and procedures]; and


b. Employ sanitization mechanisms with the strength and integrity commensurate with the security category or classification of the information.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for physical media sanitization and disk shredding in accordance with NIST SP 800-88, Guidelines for Media Sanitization. Digital media within customer VPCs is protected using FIPS 140-3 validated BoringCrypto modules and Cloud KMS Customer-Managed Encryption Keys (CMEK AES-256). |
| **FedRAMP High Parameter Values**: `mp-06_odp.01` (system media): techniques and procedures IAW NIST SP 800-88 Section 4: Reuse and Disposal of Storage Media and Hardware; `mp-06_odp.02` (system media): techniques and procedures IAW NIST SP 800-88 Section 4: Reuse and Disposal of Storage Media and Hardware; `mp-06_odp.03` (system media): techniques and procedures IAW NIST SP 800-88 Section 4: Reuse and Disposal of Storage Media and Hardware |


### MP-6(1) Media Sanitization | Review, Approve, Track, Document, and Verify

Review, approve, track, document, and verify media sanitization and disposal actions.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for physical media sanitization and disk shredding in accordance with NIST SP 800-88, Guidelines for Media Sanitization. Digital media within customer VPCs is protected using FIPS 140-3 validated BoringCrypto modules and Cloud KMS Customer-Managed Encryption Keys (CMEK AES-256). |
| **FedRAMP Additional Guidance**: Requirement: Must comply with NIST SP 800-88 |


### MP-6(2) Media Sanitization | Equipment Testing

Test sanitization equipment and procedures [Assignment: organization-defined frequency — FedRAMP High: at least every six (6) months] to ensure that the intended sanitization is being achieved.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for physical media sanitization and disk shredding in accordance with NIST SP 800-88, Guidelines for Media Sanitization. Digital media within customer VPCs is protected using FIPS 140-3 validated BoringCrypto modules and Cloud KMS Customer-Managed Encryption Keys (CMEK AES-256). |
| **FedRAMP High Parameter Values**: `mp-06.02_odp.01` (frequency): at least every six (6) months; `mp-06.02_odp.02` (frequency): at least every six (6) months<br>**FedRAMP Additional Guidance**: Guidance: Equipment and procedures may be tested or validated for effectiveness |


### MP-6(3) Media Sanitization | Nondestructive Techniques

Apply nondestructive sanitization techniques to portable storage devices prior to connecting such devices to the system under the following circumstances: [Assignment: organization-defined circumstances requiring sanitization of portable storage devices].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for physical media sanitization and disk shredding in accordance with NIST SP 800-88, Guidelines for Media Sanitization. Digital media within customer VPCs is protected using FIPS 140-3 validated BoringCrypto modules and Cloud KMS Customer-Managed Encryption Keys (CMEK AES-256). |
| **FedRAMP Additional Guidance**: Requirement: Must comply with NIST SP 800-88 |


### MP-7 Media Use

a. [Selection: Restrict; Prohibit] the use of [Assignment: organization-defined types of system media] on [Assignment: organization-defined systems or system components] using [Assignment: organization-defined controls]; and


b. Prohibit the use of portable storage devices in organizational systems when such devices have no identifiable owner.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for physical media sanitization and disk shredding in accordance with NIST SP 800-88, Guidelines for Media Sanitization. Digital media within customer VPCs is protected using FIPS 140-3 validated BoringCrypto modules and Cloud KMS Customer-Managed Encryption Keys (CMEK AES-256). |


## 2.11 Physical and Environmental Protection


### PE-1 Policy and Procedures


a. Develop, document, and disseminate to [Assignment: organization-defined personnel or roles]:

  1. [Selection (one or more): Organization-level; Mission/business process-level; System-level] physical and environmental protection policy that:

    (a) Addresses purpose, scope, roles, responsibilities, management commitment, coordination among organizational entities, and compliance; and

    (b) Is consistent with applicable laws, executive orders, directives, regulations, policies, standards, and guidelines; and

  2. Procedures to facilitate the implementation of the physical and environmental protection policy and the associated physical and environmental protection controls;


b. Designate an [Assignment: organization-defined official] to manage the development, documentation, and dissemination of the physical and environmental protection policy and procedures; and


c. Review and update the current physical and environmental protection:

  1. Policy [Assignment: organization-defined frequency — FedRAMP High: at least annually] and following [Assignment: organization-defined events — FedRAMP High: significant changes]; and

  2. Procedures [Assignment: organization-defined frequency — FedRAMP High: at least annually] and following [Assignment: organization-defined events].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC maintains physical and environmental protection policy and procedures for Google infrastructure, inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }}. Policy and procedures controls are shared responsibilities and are not 100% inheritable (FedRAMP SSP Appendix A / DoD CC SRG). [CONFIG_REQUIRED: Reference the organization's physical and environmental protection policy and procedures that apply to the system, including the review frequency] |
| **FedRAMP High Parameter Values**: `pe-01_odp.05` (frequency): at least annually; `pe-01_odp.07` (frequency): at least annually; `pe-01_odp.08` (events): significant changes |


### PE-2 Physical Access Authorizations


a. Develop, approve, and maintain a list of individuals with authorized access to the facility where the system resides;


b. Issue authorization credentials for facility access;


c. Review the access list detailing authorized facility access by individuals [Assignment: organization-defined frequency — FedRAMP High: at least every ninety (90) days]; and


d. Remove individuals from the facility access list when access is no longer required.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }}: Google LLC implements PE-2 in the Google data centers that host the system. |
| **FedRAMP High Parameter Values**: `pe-02_odp` (frequency): at least every ninety (90) days |


### PE-3 Physical Access Control

> [!IMPORTANT]
> [WARNING: RMF TEAM ACTION REQUIRED: Verify and update operational procedure or contact details in this section.]

a. Enforce physical access authorizations at [Assignment: organization-defined entry and exit points to the facility where the system resides] by:

  1. Verifying individual access authorizations before granting access to the facility; and

  2. Controlling ingress and egress to the facility using [Selection (one or more): [Assignment: organization-defined physical access control systems or devices]; guards];


b. Maintain physical access audit logs for [Assignment: organization-defined entry or exit points];


c. Control access to areas within the facility designated as publicly accessible by implementing the following controls: [Assignment: organization-defined physical access controls];


d. Escort visitors and control visitor activity [Assignment: organization-defined circumstances requiring visitor escorts and control of visitor activity — FedRAMP High: in all circumstances within restricted access area where the information system resides];


e. Secure keys, combinations, and other physical access devices;


f. Inventory [Assignment: organization-defined physical access devices] every [Assignment: organization-defined frequency — FedRAMP High: at least annually or earlier as required by a security relevant event.]; and


g. Change combinations and keys [Assignment: organization-defined frequency — FedRAMP High: at least annually] and/or when keys are lost, combinations are compromised, or when individuals possessing the keys or combinations are transferred or terminated.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }}: Google LLC implements PE-3 in the Google data centers that host the system. |
| **FedRAMP High Parameter Values**: `pe-03_odp.02`: CSP defined physical access control systems/devices AND guards; `pe-03_odp.06` (circumstances): in all circumstances within restricted access area where the information system resides; `pe-03_odp.08` (frequency): at least annually; `pe-03_odp.09` (frequency): at least annually or earlier as required by a security relevant event.; `pe-03_odp.10` (frequency): at least annually or earlier as required by a security relevant event. |


### PE-3(1) Physical Access Control | System Access

> [!IMPORTANT]
> [WARNING: RMF TEAM ACTION REQUIRED: Verify and update operational procedure or contact details in this section.]

Enforce physical access authorizations to the system in addition to the physical access controls for the facility at [Assignment: organization-defined physical spaces containing one or more components of the system].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }}: Google LLC implements PE-3(1) in the Google data centers that host the system. |


### PE-4 Access Control for Transmission

Control physical access to [Assignment: organization-defined system distribution and transmission lines] within organizational facilities using [Assignment: organization-defined security controls].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }}: Google LLC implements PE-4 in the Google data centers that host the system. |


### PE-5 Access Control for Output Devices

Control physical access to output from [Assignment: organization-defined output devices] to prevent unauthorized individuals from obtaining the output.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }}: Google LLC implements PE-5 in the Google data centers that host the system. |


### PE-6 Monitoring Physical Access


a. Monitor physical access to the facility where the system resides to detect and respond to physical security incidents;


b. Review physical access logs [Assignment: organization-defined frequency — FedRAMP High: at least monthly] and upon occurrence of [Assignment: organization-defined events or potential indications of events]; and


c. Coordinate results of reviews and investigations with the organizational incident response capability.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }}: Google LLC implements PE-6 in the Google data centers that host the system. |
| **FedRAMP High Parameter Values**: `pe-06_odp.01` (frequency): at least monthly |


### PE-6(1) Monitoring Physical Access | Intrusion Alarms and Surveillance Equipment

> [!IMPORTANT]
> [WARNING: RMF TEAM ACTION REQUIRED: Verify and update operational procedure or contact details in this section.]

Monitor physical access to the facility where the system resides using physical intrusion alarms and surveillance equipment.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }}: Google LLC implements PE-6(1) in the Google data centers that host the system. |


### PE-6(4) Monitoring Physical Access | Monitoring Physical Access to Systems

> [!IMPORTANT]
> [WARNING: RMF TEAM ACTION REQUIRED: Verify and update operational procedure or contact details in this section.]

Monitor physical access to the system in addition to the physical access monitoring of the facility at [Assignment: organization-defined physical spaces containing one or more components of the system].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }}: Google LLC implements PE-6(4) in the Google data centers that host the system. |


### PE-8 Visitor Access Records


a. Maintain visitor access records to the facility where the system resides for [Assignment: organization-defined time period — FedRAMP High: for a minimum of one (1) year];


b. Review visitor access records [Assignment: organization-defined frequency — FedRAMP High: at least monthly]; and


c. Report anomalies in visitor access records to [Assignment: organization-defined personnel].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }}: Google LLC implements PE-8 in the Google data centers that host the system. |
| **FedRAMP High Parameter Values**: `pe-08_odp.01` (time period): for a minimum of one (1) year; `pe-08_odp.02` (frequency): at least monthly |


### PE-8(1) Visitor Access Records | Automated Records Maintenance and Review

Maintain and review visitor access records using [Assignment: organization-defined automated mechanisms].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }}: Google LLC implements PE-8(1) in the Google data centers that host the system. |


### PE-8(3) Visitor Access Records | Limit Personally Identifiable Information Elements

Limit personally identifiable information contained in visitor access records to the following elements identified in the privacy risk assessment: [Assignment: organization-defined elements].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }}: Google LLC implements PE-8(3) in the Google data centers that host the system. |


### PE-9 Power Equipment and Cabling

Protect power equipment and power cabling for the system from damage and destruction.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }}: Google LLC implements PE-9 in the Google data centers that host the system. |


### PE-10 Emergency Shutoff


a. Provide the capability of shutting off power to [Assignment: organization-defined system or individual system components] in emergency situations;


b. Place emergency shutoff switches or devices in [Assignment: organization-defined location by system or system component — FedRAMP High: near more than one egress point of the IT area and ensures it is labeled and protected by a cover to prevent accidental shut-off] to facilitate access for authorized personnel; and


c. Protect emergency power shutoff capability from unauthorized activation.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }}: Google LLC implements PE-10 in the Google data centers that host the system. |
| **FedRAMP High Parameter Values**: `pe-10_odp.02` (location): near more than one egress point of the IT area and ensures it is labeled and protected by a cover to prevent accidental shut-off |


### PE-11 Emergency Power

Provide an uninterruptible power supply to facilitate [Selection (one or more): an orderly shutdown of the system; transition of the system to long-term alternate power] in the event of a primary power source loss.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }}: Google LLC implements PE-11 in the Google data centers that host the system. |


### PE-11(1) Emergency Power | Alternate Power Supply — Minimal Operational Capability

Provide an alternate power supply for the system that is activated [Selection: manually; automatically — FedRAMP High: automatically] and that can maintain minimally required operational capability in the event of an extended loss of the primary power source.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }}: Google LLC implements PE-11(1) in the Google data centers that host the system. |
| **FedRAMP High Parameter Values**: `pe-11.01_odp`: automatically |


### PE-12 Emergency Lighting

> [!IMPORTANT]
> [WARNING: RMF TEAM ACTION REQUIRED: Verify and update operational procedure or contact details in this section.]

Employ and maintain automatic emergency lighting for the system that activates in the event of a power outage or disruption and that covers emergency exits and evacuation routes within the facility.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }}: Google LLC implements PE-12 in the Google data centers that host the system. |


### PE-13 Fire Protection

Employ and maintain fire detection and suppression systems that are supported by an independent energy source.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }}: Google LLC implements PE-13 in the Google data centers that host the system. |


### PE-13(1) Fire Protection | Detection Systems — Automatic Activation and Notification

Employ fire detection systems that activate automatically and notify [Assignment: organization-defined personnel or roles — FedRAMP High: service provider building maintenance/physical security personnel] and [Assignment: organization-defined emergency responders — FedRAMP High: service provider emergency responders with incident response responsibilities] in the event of a fire.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }}: Google LLC implements PE-13(1) in the Google data centers that host the system. |
| **FedRAMP High Parameter Values**: `pe-13.01_odp.01` (personnel or roles): service provider building maintenance/physical security personnel; `pe-13.01_odp.02` (emergency responders): service provider emergency responders with incident response responsibilities |


### PE-13(2) Fire Protection | Suppression Systems — Automatic Activation and Notification


(a) Employ fire suppression systems that activate automatically and notify [Assignment: organization-defined personnel or roles] and [Assignment: organization-defined emergency responders]; and


(b) Employ an automatic fire suppression capability when the facility is not staffed on a continuous basis.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }}: Google LLC implements PE-13(2) in the Google data centers that host the system. |


### PE-13(4) Fire Protection | Inspections

> [!IMPORTANT]
> [WARNING: RMF TEAM ACTION REQUIRED: Verify and update operational procedure or contact details in this section.]

Ensure that the facility undergoes [Assignment: organization-defined frequency] fire protection inspections by authorized and qualified inspectors and identified deficiencies are resolved within [Assignment: organization-defined time period].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }}: Google LLC implements PE-13(4) in the Google data centers that host the system. |


### PE-14 Environmental Controls


a. Maintain [Selection (one or more): temperature; humidity; pressure; radiation; [Assignment: organization-defined environmental control — FedRAMP High: consistent with American Society of Heating, Refrigerating and Air-conditioning Engineers (ASHRAE) document entitled Thermal Guidelines for Data Processing Environments]] levels within the facility where the system resides at [Assignment: organization-defined acceptable levels]; and


b. Monitor environmental control levels [Assignment: organization-defined frequency — FedRAMP High: continuously].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }}: Google LLC implements PE-14 in the Google data centers that host the system. |
| **FedRAMP High Parameter Values**: `pe-14_odp.01`: consistent with American Society of Heating, Refrigerating and Air-conditioning Engineers (ASHRAE) document entitled Thermal Guidelines for Data Processing Environments; `pe-14_odp.04` (frequency): continuously<br>**FedRAMP Additional Guidance**: (a) Requirement: The service provider measures temperature at server inlets and humidity levels by dew point. |


### PE-14(2) Environmental Controls | Monitoring with Alarms and Notifications

Employ environmental control monitoring that provides an alarm or notification of changes potentially harmful to personnel or equipment to [Assignment: organization-defined personnel or roles].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }}: Google LLC implements PE-14(2) in the Google data centers that host the system. |


### PE-15 Water Damage Protection

Protect the system from damage resulting from water leakage by providing master shutoff or isolation valves that are accessible, working properly, and known to key personnel.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }}: Google LLC implements PE-15 in the Google data centers that host the system. |


### PE-15(1) Water Damage Protection | Automation Support

Detect the presence of water near the system and alert [Assignment: organization-defined personnel or roles — FedRAMP High: service provider building maintenance/physical security personnel] using [Assignment: organization-defined automated mechanisms].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }}: Google LLC implements PE-15(1) in the Google data centers that host the system. |
| **FedRAMP High Parameter Values**: `pe-15.01_odp.01` (personnel or roles): service provider building maintenance/physical security personnel |


### PE-16 Delivery and Removal


a. Authorize and control [Assignment: organization-defined types of system components — FedRAMP High: all information system components] entering and exiting the facility; and


b. Maintain records of the system components.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }}: Google LLC implements PE-16 in the Google data centers that host the system. |
| **FedRAMP High Parameter Values**: `pe-16_odp.01` (types of system components): all information system components; `pe-16_odp.02` (types of system components): all information system components |


### PE-17 Alternate Work Site


a. Determine and document the [Assignment: organization-defined alternate work sites] allowed for use by employees;


b. Employ the following controls at alternate work sites: [Assignment: organization-defined controls];


c. Assess the effectiveness of controls at alternate work sites; and


d. Provide a means for employees to communicate with information security and privacy personnel in case of incidents.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for the Google-managed infrastructure that hosts the system. [CONFIG_REQUIRED: Confirm in the Google Cloud {{ DOD_IMPACT_LABEL }} / {{ BASE_FEDRAMP_LABEL }} customer responsibility matrix whether PE-17 is inherited or shared; document customer-configured controls and verify Implementation Status] |


### PE-18 Location of System Components

> [!IMPORTANT]
> [WARNING: RMF TEAM ACTION REQUIRED: Verify and update operational procedure or contact details in this section.]

Position system components within the facility to minimize potential damage from [Assignment: organization-defined physical and environmental hazards — FedRAMP High: physical and environmental hazards identified during threat assessment] and to minimize the opportunity for unauthorized access.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }}: Google LLC implements PE-18 in the Google data centers that host the system. |
| **FedRAMP High Parameter Values**: `pe-18_odp` (physical and environmental hazards): physical and environmental hazards identified during threat assessment |


### PE-22 Component Marking

Mark [Assignment: organization-defined system hardware components] indicating the impact level or classification level of the information permitted to be processed, stored, or transmitted by the hardware component.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }}: Google LLC implements PE-22 in the Google data centers that host the system. |


### PE-23 Facility Location


a. Plan the location or site of the facility where the system resides considering physical and environmental hazards; and


b. For existing facilities, consider the physical and environmental hazards in the organizational risk management strategy.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }}: Google LLC implements PE-23 in the Google data centers that host the system. |


## 2.12 Planning


### PL-1 Policy and Procedures


a. Develop, document, and disseminate to [Assignment: organization-defined personnel or roles]:

  1. [Selection (one or more): Organization-level; Mission/business process-level; System-level] planning policy that:

    (a) Addresses purpose, scope, roles, responsibilities, management commitment, coordination among organizational entities, and compliance; and

    (b) Is consistent with applicable laws, executive orders, directives, regulations, policies, standards, and guidelines; and

  2. Procedures to facilitate the implementation of the planning policy and the associated planning controls;


b. Designate an [Assignment: organization-defined official] to manage the development, documentation, and dissemination of the planning policy and procedures; and


c. Review and update the current planning:

  1. Policy [Assignment: organization-defined frequency — FedRAMP High: at least annually] and following [Assignment: organization-defined events — FedRAMP High: significant changes]; and

  2. Procedures [Assignment: organization-defined frequency — FedRAMP High: at least annually] and following [Assignment: organization-defined events].


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Owner & ISSO |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [x] Planned<br>- [ ] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>The System Security Plan (SSP), system architecture documentation, and the CNSSI 1253 control baseline (NIST SP 800-53 Rev. 5 controls) are developed and maintained by the System Owner and ISSO and reviewed at the frequency defined in PL-2. |
| **FedRAMP High Parameter Values**: `pl-01_odp.05` (frequency): at least annually; `pl-01_odp.07` (frequency): at least annually; `pl-01_odp.08` (events): significant changes |


### PL-2 System Security and Privacy Plans

> [!IMPORTANT]
> [WARNING: RMF TEAM ACTION REQUIRED: Verify and update operational procedure or contact details in this section.]

a. Develop security and privacy plans for the system that:

  1. Are consistent with the organization's enterprise architecture;

  2. Explicitly define the constituent system components;

  3. Describe the operational context of the system in terms of mission and business processes;

  4. Identify the individuals that fulfill system roles and responsibilities;

  5. Identify the information types processed, stored, and transmitted by the system;

  6. Provide the security categorization of the system, including supporting rationale;

  7. Describe any specific threats to the system that are of concern to the organization;

  8. Provide the results of a privacy risk assessment for systems processing personally identifiable information;

  9. Describe the operational environment for the system and any dependencies on or connections to other systems or system components;

  10. Provide an overview of the security and privacy requirements for the system;

  11. Identify any relevant control baselines or overlays, if applicable;

  12. Describe the controls in place or planned for meeting the security and privacy requirements, including a rationale for any tailoring decisions;

  13. Include risk determinations for security and privacy architecture and design decisions;

  14. Include security- and privacy-related activities affecting the system that require planning and coordination with [Assignment: organization-defined individuals or groups — FedRAMP High: to include chief privacy and ISSO and/or similar role or designees]; and

  15. Are reviewed and approved by the authorizing official or designated representative prior to plan implementation.


b. Distribute copies of the plans and communicate subsequent changes to the plans to [Assignment: organization-defined personnel or roles — FedRAMP High: to include chief privacy and ISSO and/or similar role];


c. Review the plans [Assignment: organization-defined frequency — FedRAMP High: at least annually];


d. Update the plans to address changes to the system and environment of operation or problems identified during plan implementation or control assessments; and


e. Protect the plans from unauthorized disclosure and modification.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Owner & ISSO |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [x] Planned<br>- [ ] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>The System Security Plan (SSP), system architecture documentation, and the CNSSI 1253 control baseline (NIST SP 800-53 Rev. 5 controls) are developed and maintained by the System Owner and ISSO and reviewed at the frequency defined in PL-2. |
| **FedRAMP High Parameter Values**: `pl-02_odp.01` (individuals or groups): to include chief privacy and ISSO and/or similar role or designees; `pl-02_odp.02` (personnel or roles): to include chief privacy and ISSO and/or similar role; `pl-02_odp.03` (frequency): at least annually |


### PL-4 Rules of Behavior


a. Establish and provide to individuals requiring access to the system, the rules that describe their responsibilities and expected behavior for information and system usage, security, and privacy;


b. Receive a documented acknowledgment from such individuals, indicating that they have read, understand, and agree to abide by the rules of behavior, before authorizing access to information and the system;


c. Review and update the rules of behavior [Assignment: organization-defined frequency — FedRAMP High: at least annually]; and


d. Require individuals who have acknowledged a previous version of the rules of behavior to read and re-acknowledge [Selection (one or more): [Assignment: organization-defined frequency — FedRAMP High: at least annually and when the rules are revised or changed]; when the rules are revised or updated].


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Owner & ISSO |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [x] Planned<br>- [ ] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>The System Security Plan (SSP), system architecture documentation, and the CNSSI 1253 control baseline (NIST SP 800-53 Rev. 5 controls) are developed and maintained by the System Owner and ISSO and reviewed at the frequency defined in PL-2. |
| **FedRAMP High Parameter Values**: `pl-04_odp.01` (frequency): at least annually; `pl-04_odp.02`: at least annually and when the rules are revised or changed |


### PL-4(1) Rules of Behavior | Social Media and External Site/Application Usage Restrictions

Include in the rules of behavior, restrictions on:


(a) Use of social media, social networking sites, and external sites/applications;


(b) Posting organizational information on public websites; and


(c) Use of organization-provided identifiers (e.g., email addresses) and authentication secrets (e.g., passwords) for creating accounts on external sites/applications.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Owner & ISSO |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [x] Planned<br>- [ ] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>The System Security Plan (SSP), system architecture documentation, and the CNSSI 1253 control baseline (NIST SP 800-53 Rev. 5 controls) are developed and maintained by the System Owner and ISSO and reviewed at the frequency defined in PL-2. |


### PL-7 Concept of Operations


a. Develop a Concept of Operations (CONOPS) for the system describing how the organization intends to operate the system from the perspective of information security and privacy; and


b. Review and update the CONOPS [Assignment: organization-defined frequency].


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Owner & ISSO |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [x] Planned<br>- [ ] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>The System Security Plan (SSP), system architecture documentation, and the CNSSI 1253 control baseline (NIST SP 800-53 Rev. 5 controls) are developed and maintained by the System Owner and ISSO and reviewed at the frequency defined in PL-2. |


### PL-8 Security and Privacy Architectures


a. Develop security and privacy architectures for the system that:

  1. Describe the requirements and approach to be taken for protecting the confidentiality, integrity, and availability of organizational information;

  2. Describe the requirements and approach to be taken for processing personally identifiable information to minimize privacy risk to individuals;

  3. Describe how the architectures are integrated into and support the enterprise architecture; and

  4. Describe any assumptions about, and dependencies on, external systems and services;


b. Review and update the architectures [Assignment: organization-defined frequency — FedRAMP High: at least annually and when a significant change occurs] to reflect changes in the enterprise architecture; and


c. Reflect planned architecture changes in security and privacy plans, Concept of Operations (CONOPS), criticality analysis, organizational procedures, and procurements and acquisitions.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Owner & ISSO |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [x] Planned<br>- [ ] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>The System Security Plan (SSP), system architecture documentation, and the CNSSI 1253 control baseline (NIST SP 800-53 Rev. 5 controls) are developed and maintained by the System Owner and ISSO and reviewed at the frequency defined in PL-2. |
| **FedRAMP High Parameter Values**: `pl-08_odp` (frequency): at least annually and when a significant change occurs<br>**FedRAMP Additional Guidance**: (b) Guidance: Significant change is defined in NIST Special Publication 800-37 Revision 2, Appendix F. |


### PL-8(1) Security and Privacy Architectures | Defense in Depth

Design the security and privacy architectures for the system using a defense-in-depth approach that:


(a) Allocates [Assignment: organization-defined controls] to [Assignment: organization-defined locations and architectural layers]; and


(b) Ensures that the allocated controls operate in a coordinated and mutually reinforcing manner.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Owner & ISSO |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [x] Planned<br>- [ ] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>The System Security Plan (SSP), system architecture documentation, and the CNSSI 1253 control baseline (NIST SP 800-53 Rev. 5 controls) are developed and maintained by the System Owner and ISSO and reviewed at the frequency defined in PL-2. |


### PL-8(2) Security and Privacy Architectures | Supplier Diversity

Require that [Assignment: organization-defined controls] allocated to [Assignment: organization-defined locations and architectural layers] are obtained from different suppliers.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Owner & ISSO |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [x] Planned<br>- [ ] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>The System Security Plan (SSP), system architecture documentation, and the CNSSI 1253 control baseline (NIST SP 800-53 Rev. 5 controls) are developed and maintained by the System Owner and ISSO and reviewed at the frequency defined in PL-2. |


### PL-9 Central Management

Centrally manage [Assignment: organization-defined controls and related processes].


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Owner & ISSO |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [x] Planned<br>- [ ] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>The System Security Plan (SSP), system architecture documentation, and the CNSSI 1253 control baseline (NIST SP 800-53 Rev. 5 controls) are developed and maintained by the System Owner and ISSO and reviewed at the frequency defined in PL-2. |


### PL-10 Baseline Selection

Select a control baseline for the system.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Owner & ISSO |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [x] Planned<br>- [ ] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>The System Security Plan (SSP), system architecture documentation, and the CNSSI 1253 control baseline (NIST SP 800-53 Rev. 5 controls) are developed and maintained by the System Owner and ISSO and reviewed at the frequency defined in PL-2. |
| **FedRAMP Additional Guidance**: Requirement: Select the appropriate FedRAMP Baseline |


### PL-11 Baseline Tailoring

Tailor the selected control baseline by applying specified tailoring actions.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Owner & ISSO |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [x] Planned<br>- [ ] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>The System Security Plan (SSP), system architecture documentation, and the CNSSI 1253 control baseline (NIST SP 800-53 Rev. 5 controls) are developed and maintained by the System Owner and ISSO and reviewed at the frequency defined in PL-2. |


## 2.13 Program Management


### PM-1 Information Security Program Plan


a. Develop and disseminate an organization-wide information security program plan that:

  1. Provides an overview of the requirements for the security program and a description of the security program management controls and common controls in place or planned for meeting those requirements;

  2. Includes the identification and assignment of roles, responsibilities, management commitment, coordination among organizational entities, and compliance;

  3. Reflects the coordination among organizational entities responsible for information security; and

  4. Is approved by a senior official with responsibility and accountability for the risk being incurred to organizational operations (including mission, functions, image, and reputation), organizational assets, individuals, other organizations, and the Nation;


b. Review and update the organization-wide information security program plan [Assignment: organization-defined frequency] and following [Assignment: organization-defined events]; and


c. Protect the information security program plan from unauthorized disclosure and modification.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [x] Planned<br>- [ ] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Organization-wide cybersecurity program management and risk governance. |


### PM-3 Information Security and Privacy Resources


a. Include the resources needed to implement the information security and privacy programs in capital planning and investment requests and document all exceptions to this requirement;


b. Prepare documentation required for addressing information security and privacy programs in capital planning and investment requests in accordance with applicable laws, executive orders, directives, policies, regulations, standards; and


c. Make available for expenditure, the planned information security and privacy resources.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [x] Planned<br>- [ ] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Organization-wide cybersecurity program management and risk governance. |


### PM-4 Plan of Action and Milestones Process


a. Implement a process to ensure that plans of action and milestones for the information security, privacy, and supply chain risk management programs and associated organizational systems:

  1. Are developed and maintained;

  2. Document the remedial information security, privacy, and supply chain risk management actions to adequately respond to risk to organizational operations and assets, individuals, other organizations, and the Nation; and

  3. Are reported in accordance with established reporting requirements.


b. Review plans of action and milestones for consistency with the organizational risk management strategy and organization-wide priorities for risk response actions.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [x] Planned<br>- [ ] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Organization-wide cybersecurity program management and risk governance. |


### PM-5 System Inventory

Develop and update [Assignment: organization-defined frequency] an inventory of organizational systems.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [x] Planned<br>- [ ] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Organization-wide cybersecurity program management and risk governance. |


### PM-5(1) System Inventory | Inventory of Personally Identifiable Information

Establish, maintain, and update [Assignment: organization-defined frequency] an inventory of all systems, applications, and projects that process personally identifiable information.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [x] Planned<br>- [ ] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Organization-wide cybersecurity program management and risk governance. |


### PM-6 Measures of Performance

Develop, monitor, and report on the results of information security and privacy measures of performance.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [x] Planned<br>- [ ] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Organization-wide cybersecurity program management and risk governance. |


### PM-7 Enterprise Architecture

Develop and maintain an enterprise architecture with consideration for information security, privacy, and the resulting risk to organizational operations and assets, individuals, other organizations, and the Nation.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [x] Planned<br>- [ ] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Organization-wide cybersecurity program management and risk governance. |


### PM-8 Critical Infrastructure Plan

Address information security and privacy issues in the development, documentation, and updating of a critical infrastructure and key resources protection plan.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [x] Planned<br>- [ ] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Organization-wide cybersecurity program management and risk governance. |


### PM-9 Risk Management Strategy


a. Develops a comprehensive strategy to manage:

  1. Security risk to organizational operations and assets, individuals, other organizations, and the Nation associated with the operation and use of organizational systems; and

  2. Privacy risk to individuals resulting from the authorized processing of personally identifiable information;


b. Implement the risk management strategy consistently across the organization; and


c. Review and update the risk management strategy [Assignment: organization-defined frequency] or as required, to address organizational changes.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [x] Planned<br>- [ ] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Organization-wide cybersecurity program management and risk governance. |


### PM-10 Authorization Process


a. Manage the security and privacy state of organizational systems and the environments in which those systems operate through authorization processes;


b. Designate individuals to fulfill specific roles and responsibilities within the organizational risk management process; and


c. Integrate the authorization processes into an organization-wide risk management program.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [x] Planned<br>- [ ] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Organization-wide cybersecurity program management and risk governance. |


### PM-11 Mission and Business Process Definition


a. Define organizational mission and business processes with consideration for information security and privacy and the resulting risk to organizational operations, organizational assets, individuals, other organizations, and the Nation; and


b. Determine information protection and personally identifiable information processing needs arising from the defined mission and business processes; and


c. Review and revise the mission and business processes [Assignment: organization-defined frequency].


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [x] Planned<br>- [ ] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Organization-wide cybersecurity program management and risk governance. |


### PM-13 Security and Privacy Workforce

Establish a security and privacy workforce development and improvement program.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [x] Planned<br>- [ ] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Organization-wide cybersecurity program management and risk governance. |


### PM-14 Testing, Training, and Monitoring


a. Implement a process for ensuring that organizational plans for conducting security and privacy testing, training, and monitoring activities associated with organizational systems:

  1. Are developed and maintained; and

  2. Continue to be executed; and


b. Review testing, training, and monitoring plans for consistency with the organizational risk management strategy and organization-wide priorities for risk response actions.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [x] Planned<br>- [ ] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Organization-wide cybersecurity program management and risk governance. |


### PM-17 Protecting Controlled Unclassified Information on External Systems


a. Establish policy and procedures to ensure that requirements for the protection of controlled unclassified information that is processed, stored or transmitted on external systems, are implemented in accordance with applicable laws, executive orders, directives, policies, regulations, and standards; and


b. Review and update the policy and procedures [Assignment: organization-defined frequency].


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [x] Planned<br>- [ ] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Organization-wide cybersecurity program management and risk governance. |


### PM-18 Privacy Program Plan


a. Develop and disseminate an organization-wide privacy program plan that provides an overview of the agency's privacy program, and:

  1. Includes a description of the structure of the privacy program and the resources dedicated to the privacy program;

  2. Provides an overview of the requirements for the privacy program and a description of the privacy program management controls and common controls in place or planned for meeting those requirements;

  3. Includes the role of the senior agency official for privacy and the identification and assignment of roles of other privacy officials and staff and their responsibilities;

  4. Describes management commitment, compliance, and the strategic goals and objectives of the privacy program;

  5. Reflects coordination among organizational entities responsible for the different aspects of privacy; and

  6. Is approved by a senior official with responsibility and accountability for the privacy risk being incurred to organizational operations (including mission, functions, image, and reputation), organizational assets, individuals, other organizations, and the Nation; and


b. Update the plan [Assignment: organization-defined frequency] and to address changes in federal privacy laws and policy and organizational changes and problems identified during plan implementation or privacy control assessments.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [x] Planned<br>- [ ] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Organization-wide cybersecurity program management and risk governance. |


### PM-19 Privacy Program Leadership Role

Appoint a senior agency official for privacy with the authority, mission, accountability, and resources to coordinate, develop, and implement, applicable privacy requirements and manage privacy risks through the organization-wide privacy program.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [x] Planned<br>- [ ] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Organization-wide cybersecurity program management and risk governance. |


### PM-20 Dissemination of Privacy Program Information

Maintain a central resource webpage on the organization's principal public website that serves as a central source of information about the organization's privacy program and that:


a. Ensures that the public has access to information about organizational privacy activities and can communicate with its senior agency official for privacy;


b. Ensures that organizational privacy practices and reports are publicly available; and


c. Employs publicly facing email addresses and/or phone lines to enable the public to provide feedback and/or direct questions to privacy offices regarding privacy practices.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [x] Planned<br>- [ ] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Organization-wide cybersecurity program management and risk governance. |


### PM-20(1) Dissemination of Privacy Program Information | Privacy Policies on Websites, Applications, and Digital Services

Develop and post privacy policies on all external-facing websites, mobile applications, and other digital services, that:


(a) Are written in plain language and organized in a way that is easy to understand and navigate;


(b) Provide information needed by the public to make an informed decision about whether and how to interact with the organization; and


(c) Are updated whenever the organization makes a substantive change to the practices it describes and includes a time/date stamp to inform the public of the date of the most recent changes.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [x] Planned<br>- [ ] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Organization-wide cybersecurity program management and risk governance. |


### PM-22 Personally Identifiable Information Quality Management

Develop and document organization-wide policies and procedures for:


a. Reviewing for the accuracy, relevance, timeliness, and completeness of personally identifiable information across the information life cycle;


b. Correcting or deleting inaccurate or outdated personally identifiable information;


c. Disseminating notice of corrected or deleted personally identifiable information to individuals or other appropriate entities; and


d. Appeals of adverse decisions on correction or deletion requests.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [x] Planned<br>- [ ] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Organization-wide cybersecurity program management and risk governance. |


### PM-23 Data Governance Body

Establish a Data Governance Body consisting of [Assignment: organization-defined roles] with [Assignment: organization-defined responsibilities].


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [x] Planned<br>- [ ] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Organization-wide cybersecurity program management and risk governance. |


### PM-24 Data Integrity Board

Establish a Data Integrity Board to:


a. Review proposals to conduct or participate in a matching program; and


b. Conduct an annual review of all matching programs in which the agency has participated.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [x] Planned<br>- [ ] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Organization-wide cybersecurity program management and risk governance. |


### PM-25 Minimization of Personally Identifiable Information Used in Testing, Training, and Research


a. Develop, document, and implement policies and procedures that address the use of personally identifiable information for internal testing, training, and research;


b. Limit or minimize the amount of personally identifiable information used for internal testing, training, and research purposes;


c. Authorize the use of personally identifiable information when such information is required for internal testing, training, and research; and


d. Review and update policies and procedures [Assignment: organization-defined frequency].


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [x] Planned<br>- [ ] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Organization-wide cybersecurity program management and risk governance. |


### PM-26 Complaint Management

Implement a process for receiving and responding to complaints, concerns, or questions from individuals about the organizational security and privacy practices that includes:


a. Mechanisms that are easy to use and readily accessible by the public;


b. All information necessary for successfully filing complaints;


c. Tracking mechanisms to ensure all complaints received are reviewed and addressed within [Assignment: organization-defined time period];


d. Acknowledgement of receipt of complaints, concerns, or questions from individuals within [Assignment: organization-defined time period]; and


e. Response to complaints, concerns, or questions from individuals within [Assignment: organization-defined time period].


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [x] Planned<br>- [ ] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Organization-wide cybersecurity program management and risk governance. |


### PM-27 Privacy Reporting


a. Develop [Assignment: organization-defined privacy reports] and disseminate to:

  1. [Assignment: organization-defined oversight bodies] to demonstrate accountability with statutory, regulatory, and policy privacy mandates; and

  2. [Assignment: organization-defined officials] and other personnel with responsibility for monitoring privacy program compliance; and


b. Review and update privacy reports [Assignment: organization-defined frequency].


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [x] Planned<br>- [ ] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Organization-wide cybersecurity program management and risk governance. |


### PM-28 Risk Framing


a. Identify and document:

  1. Assumptions affecting risk assessments, risk responses, and risk monitoring;

  2. Constraints affecting risk assessments, risk responses, and risk monitoring;

  3. Priorities and trade-offs considered by the organization for managing risk; and

  4. Organizational risk tolerance;


b. Distribute the results of risk framing activities to [Assignment: organization-defined personnel]; and


c. Review and update risk framing considerations [Assignment: organization-defined frequency].


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [x] Planned<br>- [ ] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Organization-wide cybersecurity program management and risk governance. |


### PM-29 Risk Management Program Leadership Roles


a. Appoint a Senior Accountable Official for Risk Management to align organizational information security and privacy management processes with strategic, operational, and budgetary planning processes; and


b. Establish a Risk Executive (function) to view and analyze risk from an organization-wide perspective and ensure management of risk is consistent across the organization.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [x] Planned<br>- [ ] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Organization-wide cybersecurity program management and risk governance. |


### PM-30 Supply Chain Risk Management Strategy


a. Develop an organization-wide strategy for managing supply chain risks associated with the development, acquisition, maintenance, and disposal of systems, system components, and system services;


b. Implement the supply chain risk management strategy consistently across the organization; and


c. Review and update the supply chain risk management strategy on [Assignment: organization-defined frequency] or as required, to address organizational changes.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [x] Planned<br>- [ ] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Organization-wide cybersecurity program management and risk governance. |


### PM-31 Continuous Monitoring Strategy

Develop an organization-wide continuous monitoring strategy and implement continuous monitoring programs that include:


a. Establishing the following organization-wide metrics to be monitored: [Assignment: organization-defined metrics];


b. Establishing [Assignment: organization-defined frequencies] for monitoring and [Assignment: organization-defined frequencies] for assessment of control effectiveness;


c. Ongoing monitoring of organizationally-defined metrics in accordance with the continuous monitoring strategy;


d. Correlation and analysis of information generated by control assessments and monitoring;


e. Response actions to address results of the analysis of control assessment and monitoring information; and


f. Reporting the security and privacy status of organizational systems to [Assignment: organization-defined personnel or roles] [Assignment: organization-defined frequency].


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [x] Planned<br>- [ ] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Organization-wide cybersecurity program management and risk governance. |


## 2.14 Personnel Security


### PS-1 Policy and Procedures


a. Develop, document, and disseminate to [Assignment: organization-defined personnel or roles]:

  1. [Selection (one or more): Organization-level; Mission/business process-level; System-level] personnel security policy that:

    (a) Addresses purpose, scope, roles, responsibilities, management commitment, coordination among organizational entities, and compliance; and

    (b) Is consistent with applicable laws, executive orders, directives, regulations, policies, standards, and guidelines; and

  2. Procedures to facilitate the implementation of the personnel security policy and the associated personnel security controls;


b. Designate an [Assignment: organization-defined official] to manage the development, documentation, and dissemination of the personnel security policy and procedures; and


c. Review and update the current personnel security:

  1. Policy [Assignment: organization-defined frequency — FedRAMP High: at least annually] and following [Assignment: organization-defined events — FedRAMP High: significant changes]; and

  2. Procedures [Assignment: organization-defined frequency — FedRAMP High: at least annually] and following [Assignment: organization-defined events].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & ISSM |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Background screening of Google personnel with administrative access to Google Cloud common infrastructure is inherited from Google LLC. {{ ORGANIZATION }} conducts background screening for system administrators before granting GCP IAM access. |
| **FedRAMP High Parameter Values**: `ps-01_odp.05` (frequency): at least annually; `ps-01_odp.07` (frequency): at least annually; `ps-01_odp.08` (events): significant changes |


### PS-2 Position Risk Designation


a. Assign a risk designation to all organizational positions;


b. Establish screening criteria for individuals filling those positions; and


c. Review and update position risk designations [Assignment: organization-defined frequency — FedRAMP High: at least annually].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & ISSM |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Background screening of Google personnel with administrative access to Google Cloud common infrastructure is inherited from Google LLC. {{ ORGANIZATION }} conducts background screening for system administrators before granting GCP IAM access. |
| **FedRAMP High Parameter Values**: `ps-02_odp` (frequency): at least annually |


### PS-3 Personnel Screening


a. Screen individuals prior to authorizing access to the system; and


b. Rescreen individuals in accordance with [Assignment: organization-defined conditions requiring rescreening and, where rescreening is so indicated, the frequency of rescreening — FedRAMP High: for national security clearances; a reinvestigation is required during the fifth (5th) year for top secret security clearance, the tenth (10th) year for secret security clearance, and fifteenth (15th) year for confidential security clearance. For moderate risk law enforcement and high impact public trust level, a reinvestigation is required during the fifth (5th) year. There is no reinvestigation for other moderate risk positions or any low risk positions].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & ISSM |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Background screening of Google personnel with administrative access to Google Cloud common infrastructure is inherited from Google LLC. {{ ORGANIZATION }} conducts background screening for system administrators before granting GCP IAM access. |
| **FedRAMP High Parameter Values**: `ps-03_odp.01` (conditions requiring rescreening): for national security clearances; a reinvestigation is required during the fifth (5th) year for top secret security clearance, the tenth (10th) year for secret security clearance, and fifteenth (15th) year for confidential security clearance. For moderate risk law enforcement and high impact public trust level, a reinvestigation is required during the fifth (5th) year. There is no reinvestigation for other moderate risk positions or any low risk positions; `ps-03_odp.02` (frequency): for national security clearances; a reinvestigation is required during the fifth (5th) year for top secret security clearance, the tenth (10th) year for secret security clearance, and fifteenth (15th) year for confidential security clearance. For moderate risk law enforcement and high impact public trust level, a reinvestigation is required during the fifth (5th) year. There is no reinvestigation for other moderate risk positions or any low risk positions |


### PS-3(3) Personnel Screening | Information Requiring Special Protective Measures

Verify that individuals accessing a system processing, storing, or transmitting information requiring special protection:


(a) Have valid access authorizations that are demonstrated by assigned official government duties; and


(b) Satisfy [Assignment: organization-defined additional personnel screening criteria — FedRAMP High: personnel screening criteria - as required by specific information].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & ISSM |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Background screening of Google personnel with administrative access to Google Cloud common infrastructure is inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }}. {{ ORGANIZATION }} screens system administrators before granting Google Cloud IAM access. |
| **FedRAMP High Parameter Values**: `ps-03.03_odp` (additional personnel screening criteria): personnel screening criteria - as required by specific information |


### PS-3(4) Personnel Screening | Citizenship Requirements

Verify that individuals accessing a system processing, storing, or transmitting [Assignment: organization-defined information types] meet [Assignment: organization-defined citizenship requirements].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & ISSM |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Background screening of Google personnel with administrative access to Google Cloud common infrastructure is inherited from Google LLC. {{ ORGANIZATION }} conducts background screening for system administrators before granting GCP IAM access. |


### PS-4 Personnel Termination

Upon termination of individual employment:


a. Disable system access within [Assignment: organization-defined time period — FedRAMP High: one (1) hour];


b. Terminate or revoke any authenticators and credentials associated with the individual;


c. Conduct exit interviews that include a discussion of [Assignment: organization-defined information security topics];


d. Retrieve all security-related organizational system-related property; and


e. Retain access to organizational information and systems formerly controlled by terminated individual.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & ISSM |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Background screening of Google personnel with administrative access to Google Cloud common infrastructure is inherited from Google LLC. {{ ORGANIZATION }} conducts background screening for system administrators before granting GCP IAM access. |
| **FedRAMP High Parameter Values**: `ps-04_odp.01` (time period): one (1) hour |


### PS-4(1) Personnel Termination | Post-employment Requirements


(a) Notify terminated individuals of applicable, legally binding post-employment requirements for the protection of organizational information; and


(b) Require terminated individuals to sign an acknowledgment of post-employment requirements as part of the organizational termination process.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & ISSM |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Background screening of Google personnel with administrative access to Google Cloud common infrastructure is inherited from Google LLC. {{ ORGANIZATION }} conducts background screening for system administrators before granting GCP IAM access. |


### PS-4(2) Personnel Termination | Automated Actions

Use [Assignment: organization-defined automated mechanisms] to [Selection (one or more): notify [Assignment: organization-defined personnel or roles — FedRAMP High: access control personnel responsible for disabling access to the system] of individual termination actions; disable access to system resources].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & ISSM |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Background screening of Google personnel with administrative access to Google Cloud common infrastructure is inherited from Google LLC. {{ ORGANIZATION }} conducts background screening for system administrators before granting GCP IAM access. |
| **FedRAMP High Parameter Values**: `ps-04.02_odp.02`: access control personnel responsible for disabling access to the system |


### PS-5 Personnel Transfer


a. Review and confirm ongoing operational need for current logical and physical access authorizations to systems and facilities when individuals are reassigned or transferred to other positions within the organization;


b. Initiate [Assignment: organization-defined transfer or reassignment actions] within [Assignment: organization-defined time period following the formal transfer action — FedRAMP High: twenty-four (24) hours];


c. Modify access authorization as needed to correspond with any changes in operational need due to reassignment or transfer; and


d. Notify [Assignment: organization-defined personnel or roles — FedRAMP High: including access control personnel responsible for the system] within [Assignment: organization-defined time period — FedRAMP High: twenty-four (24) hours].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & ISSM |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Background screening of Google personnel with administrative access to Google Cloud common infrastructure is inherited from Google LLC. {{ ORGANIZATION }} conducts background screening for system administrators before granting GCP IAM access. |
| **FedRAMP High Parameter Values**: `ps-05_odp.02` (time period following the formal transfer action): twenty-four (24) hours; `ps-05_odp.03` (personnel or roles): including access control personnel responsible for the system; `ps-05_odp.04` (time period): twenty-four (24) hours |


### PS-6 Access Agreements


a. Develop and document access agreements for organizational systems;


b. Review and update the access agreements [Assignment: organization-defined frequency — FedRAMP High: at least annually]; and


c. Verify that individuals requiring access to organizational information and systems:

  1. Sign appropriate access agreements prior to being granted access; and

  2. Re-sign access agreements to maintain access to organizational systems when access agreements have been updated or [Assignment: organization-defined frequency — FedRAMP High: at least annually and any time there is a change to the user's level of access].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & ISSM |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Background screening of Google personnel with administrative access to Google Cloud common infrastructure is inherited from Google LLC. {{ ORGANIZATION }} conducts background screening for system administrators before granting GCP IAM access. |
| **FedRAMP High Parameter Values**: `ps-06_odp.01` (frequency): at least annually; `ps-06_odp.02` (frequency): at least annually and any time there is a change to the user's level of access |


### PS-6(3) Access Agreements | Post-employment Requirements


(a) Notify individuals of applicable, legally binding post-employment requirements for protection of organizational information; and


(b) Require individuals to sign an acknowledgment of these requirements, if applicable, as part of granting initial access to covered information.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & ISSM |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Background screening of Google personnel with administrative access to Google Cloud common infrastructure is inherited from Google LLC. {{ ORGANIZATION }} conducts background screening for system administrators before granting GCP IAM access. |


### PS-7 External Personnel Security


a. Establish personnel security requirements, including security roles and responsibilities for external providers;


b. Require external providers to comply with personnel security policies and procedures established by the organization;


c. Document personnel security requirements;


d. Require external providers to notify [Assignment: organization-defined personnel or roles — FedRAMP High: including access control personnel responsible for the system and/or facilities, as appropriate] of any personnel transfers or terminations of external personnel who possess organizational credentials and/or badges, or who have system privileges within [Assignment: organization-defined time period — FedRAMP High: terminations: immediately; transfers: within twenty-four (24) hours]; and


e. Monitor provider compliance with personnel security requirements.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & ISSM |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Background screening of Google personnel with administrative access to Google Cloud common infrastructure is inherited from Google LLC. {{ ORGANIZATION }} conducts background screening for system administrators before granting GCP IAM access. |
| **FedRAMP High Parameter Values**: `ps-07_odp.01` (personnel or roles): including access control personnel responsible for the system and/or facilities, as appropriate; `ps-07_odp.02` (time period): terminations: immediately; transfers: within twenty-four (24) hours |


### PS-8 Personnel Sanctions


a. Employ a formal sanctions process for individuals failing to comply with established information security and privacy policies and procedures; and


b. Notify [Assignment: organization-defined personnel or roles — FedRAMP High: to include the ISSO and/or similar role within the organization] within [Assignment: organization-defined time period — FedRAMP High: 24 hours] when a formal employee sanctions process is initiated, identifying the individual sanctioned and the reason for the sanction.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & ISSM |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Background screening of Google personnel with administrative access to Google Cloud common infrastructure is inherited from Google LLC. {{ ORGANIZATION }} conducts background screening for system administrators before granting GCP IAM access. |
| **FedRAMP High Parameter Values**: `ps-08_odp.01` (personnel or roles): to include the ISSO and/or similar role within the organization; `ps-08_odp.02` (time period): 24 hours |


### PS-9 Position Descriptions

Incorporate security and privacy roles and responsibilities into organizational position descriptions.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & ISSM |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Background screening of Google personnel with administrative access to Google Cloud common infrastructure is inherited from Google LLC. {{ ORGANIZATION }} conducts background screening for system administrators before granting GCP IAM access. |


## 2.15 Personally Identifiable Information Processing and Transparency


### PT-1 Policy and Procedures


a. Develop, document, and disseminate to [Assignment: organization-defined personnel or roles]:

  1. [Selection (one or more): Organization-level; Mission/business process-level; System-level] personally identifiable information processing and transparency policy that:

    (a) Addresses purpose, scope, roles, responsibilities, management commitment, coordination among organizational entities, and compliance; and

    (b) Is consistent with applicable laws, executive orders, directives, regulations, policies, standards, and guidelines; and

  2. Procedures to facilitate the implementation of the personally identifiable information processing and transparency policy and the associated personally identifiable information processing and transparency controls;


b. Designate an [Assignment: organization-defined official] to manage the development, documentation, and dissemination of the personally identifiable information processing and transparency policy and procedures; and


c. Review and update the current personally identifiable information processing and transparency:

  1. Policy [Assignment: organization-defined frequency] and following [Assignment: organization-defined events]; and

  2. Procedures [Assignment: organization-defined frequency] and following [Assignment: organization-defined events].


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Owner & Privacy Official |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [x] Planned<br>- [ ] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>System privacy policies and PII processing procedures are established and reviewed in accordance with federal privacy regulations. |


## 2.16 Risk Assessment


### RA-1 Policy and Procedures


a. Develop, document, and disseminate to [Assignment: organization-defined personnel or roles]:

  1. [Selection (one or more): Organization-level; Mission/business process-level; System-level] risk assessment policy that:

    (a) Addresses purpose, scope, roles, responsibilities, management commitment, coordination among organizational entities, and compliance; and

    (b) Is consistent with applicable laws, executive orders, directives, regulations, policies, standards, and guidelines; and

  2. Procedures to facilitate the implementation of the risk assessment policy and the associated risk assessment controls;


b. Designate an [Assignment: organization-defined official] to manage the development, documentation, and dissemination of the risk assessment policy and procedures; and


c. Review and update the current risk assessment:

  1. Policy [Assignment: organization-defined frequency — FedRAMP High: at least annually] and following [Assignment: organization-defined events — FedRAMP High: significant changes]; and

  2. Procedures [Assignment: organization-defined frequency — FedRAMP High: at least annually] and following [Assignment: organization-defined events].


| Control Summary Information |
| :--- |
| **Responsible Role**: ISSO / DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC conducts platform-level threat modeling and vulnerability assessments for Google Cloud infrastructure (Inherited). Where configured in the system boundary, vulnerability scanning (via ACAS and CI/CD container scanners) and continuous monitoring are performed via {{ THREAT_DETECTION_ENGINE }} and {{ CSSP_PROVIDER }}. |
| **FedRAMP High Parameter Values**: `ra-01_odp.05` (frequency): at least annually; `ra-01_odp.07` (frequency): at least annually; `ra-01_odp.08` (events): significant changes |


### RA-2 Security Categorization


a. Categorize the system and information it processes, stores, and transmits;


b. Document the security categorization results, including supporting rationale, in the security plan for the system; and


c. Verify that the authorizing official or authorizing official designated representative reviews and approves the security categorization decision.


| Control Summary Information |
| :--- |
| **Responsible Role**: ISSO / DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC conducts platform-level threat modeling and vulnerability assessments for Google Cloud infrastructure (Inherited). Where configured in the system boundary, vulnerability scanning (via ACAS and CI/CD container scanners) and continuous monitoring are performed via {{ THREAT_DETECTION_ENGINE }} and {{ CSSP_PROVIDER }}. |


### RA-3 Risk Assessment


a. Conduct a risk assessment, including:

  1. Identifying threats to and vulnerabilities in the system;

  2. Determining the likelihood and magnitude of harm from unauthorized access, use, disclosure, disruption, modification, or destruction of the system, the information it processes, stores, or transmits, and any related information; and

  3. Determining the likelihood and impact of adverse effects on individuals arising from the processing of personally identifiable information;


b. Integrate risk assessment results and risk management decisions from the organization and mission or business process perspectives with system-level risk assessments;


c. Document risk assessment results in [Selection: security and privacy plans; risk assessment report; [Assignment: organization-defined document — FedRAMP High: security assessment report]];


d. Review risk assessment results [Assignment: organization-defined frequency — FedRAMP High: at least annually and whenever a significant change occurs];


e. Disseminate risk assessment results to [Assignment: organization-defined personnel or roles]; and


f. Update the risk assessment [Assignment: organization-defined frequency — FedRAMP High: annually] or when there are significant changes to the system, its environment of operation, or other conditions that may impact the security or privacy state of the system.


| Control Summary Information |
| :--- |
| **Responsible Role**: ISSO / DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC conducts platform-level threat modeling and vulnerability assessments for Google Cloud infrastructure (Inherited). Where configured in the system boundary, vulnerability scanning (via ACAS and CI/CD container scanners) and continuous monitoring are performed via {{ THREAT_DETECTION_ENGINE }} and {{ CSSP_PROVIDER }}. |
| **FedRAMP High Parameter Values**: `ra-03_odp.01`: security assessment report; `ra-03_odp.03` (frequency): at least annually and whenever a significant change occurs; `ra-03_odp.05` (frequency): annually<br>**FedRAMP Additional Guidance**: Guidance: Significant change is defined in NIST Special Publication 800-37 Revision 2, Appendix F. (e) Requirement: Include all Authorizing Officials. |


### RA-3(1) Risk Assessment | Supply Chain Risk Assessment


(a) Assess supply chain risks associated with [Assignment: organization-defined systems, system components, and system services]; and


(b) Update the supply chain risk assessment [Assignment: organization-defined frequency], when there are significant changes to the relevant supply chain, or when changes to the system, environments of operation, or other conditions may necessitate a change in the supply chain.


| Control Summary Information |
| :--- |
| **Responsible Role**: ISSO / DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC conducts platform-level threat modeling and vulnerability assessments for Google Cloud infrastructure (Inherited). Where configured in the system boundary, vulnerability scanning (via ACAS and CI/CD container scanners) and continuous monitoring are performed via {{ THREAT_DETECTION_ENGINE }} and {{ CSSP_PROVIDER }}. |


### RA-3(2) Risk Assessment | Use of All-source Intelligence

Use all-source intelligence to assist in the analysis of risk.


| Control Summary Information |
| :--- |
| **Responsible Role**: ISSO / DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC conducts platform-level threat modeling and vulnerability assessments for Google Cloud infrastructure (Inherited). Where configured in the system boundary, vulnerability scanning (via ACAS and CI/CD container scanners) and continuous monitoring are performed via {{ THREAT_DETECTION_ENGINE }} and {{ CSSP_PROVIDER }}. |


### RA-3(3) Risk Assessment | Dynamic Threat Awareness

Determine the current cyber threat environment on an ongoing basis using [Assignment: organization-defined means].


| Control Summary Information |
| :--- |
| **Responsible Role**: ISSO / DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC conducts platform-level threat modeling and vulnerability assessments for Google Cloud infrastructure (Inherited). Where configured in the system boundary, vulnerability scanning (via ACAS and CI/CD container scanners) and continuous monitoring are performed via {{ THREAT_DETECTION_ENGINE }} and {{ CSSP_PROVIDER }}. |


### RA-5 Vulnerability Monitoring and Scanning


a. Monitor and scan for vulnerabilities in the system and hosted applications [Assignment: organization-defined frequency and/or randomly in accordance with organization-defined process — FedRAMP High: monthly operating system/infrastructure; monthly web applications (including APIs) and databases] and when new vulnerabilities potentially affecting the system are identified and reported;


b. Employ vulnerability monitoring tools and techniques that facilitate interoperability among tools and automate parts of the vulnerability management process by using standards for:

  1. Enumerating platforms, software flaws, and improper configurations;

  2. Formatting checklists and test procedures; and

  3. Measuring vulnerability impact;


c. Analyze vulnerability scan reports and results from vulnerability monitoring;


d. Remediate legitimate vulnerabilities [Assignment: organization-defined response times — FedRAMP High: high-risk vulnerabilities mitigated within thirty (30) days from date of discovery; moderate-risk vulnerabilities mitigated within ninety (90) days from date of discovery; low risk vulnerabilities mitigated within one hundred and eighty (180) days from date of discovery] in accordance with an organizational assessment of risk;


e. Share information obtained from the vulnerability monitoring process and control assessments with [Assignment: organization-defined personnel or roles] to help eliminate similar vulnerabilities in other systems; and


f. Employ vulnerability monitoring tools that include the capability to readily update the vulnerabilities to be scanned.


| Control Summary Information |
| :--- |
| **Responsible Role**: ISSO / DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC conducts platform-level threat modeling and vulnerability assessments for Google Cloud infrastructure (Inherited). Where configured in the system boundary, vulnerability scanning (via ACAS and CI/CD container scanners) and continuous monitoring are performed via {{ THREAT_DETECTION_ENGINE }} and {{ CSSP_PROVIDER }}. |
| **FedRAMP High Parameter Values**: `ra-05_odp.01` (frequency and/or randomly in accordance with organization-defined process): monthly operating system/infrastructure; monthly web applications (including APIs) and databases; `ra-05_odp.02` (frequency and/or randomly in accordance with organization-defined process): monthly operating system/infrastructure; monthly web applications (including APIs) and databases; `ra-05_odp.03` (response times): high-risk vulnerabilities mitigated within thirty (30) days from date of discovery; moderate-risk vulnerabilities mitigated within ninety (90) days from date of discovery; low risk vulnerabilities mitigated within one hundred and eighty (180) days from date of discovery<br>**FedRAMP Additional Guidance**: Guidance: See the FedRAMP Documents page\> Vulnerability Scanning Requirements https://www.FedRAMP.gov/documents/ (a) Requirement: an accredited independent assessor scans operating systems/infrastructure, web applications, and databases once annually. (d) Requirement: If a vulnerability is listed among the CISA Known Exploited Vulnerability (KEV) Catalog (https://www.cisa.gov/known-exploited-vulnerabilities-catalog) the KEV remediation date supersedes the FedRAMP parameter requirement. (e) Requirement: to include all Authorizing Officials. Guidance: Informational findings from a scanner are detailed as a returned result that holds no vulnerability risk or severity and for FedRAMP does not require an entry onto the POA\&M or entry onto the RET during any assessment phase. Warning findings, on the other hand, are given a risk rating (low, moderate, high or critical) by the scanning solution and should be treated like any other finding with a risk or severity rating for tracking purposes onto either the POA\&M or RET depending on when the findings originated (during assessments or during monthly continuous monitoring). If a warning is received during scanning, but further validation turns up no actual issue then this item should be categorized as a false positive. If this situation presents itself during an assessment phase (initial assessment, annual assessment or any SCR), follow guidance on how to report false positives in the Security Assessment Report (SAR). If this situation happens during monthly continuous monitoring, a deviation request will need to be submitted per the FedRAMP Vulnerability Deviation Request Form. Warnings are commonly associated with scanning solutions that also perform compliance scans, and if the scanner reports a "warning" as part of the compliance scanning of a CSO, follow guidance surrounding the tracking of compliance findings during either the assessment phases (initial assessment, annual assessment or any SCR) or monthly continuous monitoring as it applies. Guidance on compliance scan findings can be found by searching on "Tracking of Compliance Scans" in FAQs. |


### RA-5(2) Vulnerability Monitoring and Scanning | Update Vulnerabilities to Be Scanned

Update the system vulnerabilities to be scanned [Selection (one or more): [Assignment: organization-defined frequency — FedRAMP High: within 24 hours prior to running scans]; prior to a new scan; when new vulnerabilities are identified and reported].


| Control Summary Information |
| :--- |
| **Responsible Role**: ISSO / DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC conducts platform-level threat modeling and vulnerability assessments for Google Cloud infrastructure (Inherited). Where configured in the system boundary, vulnerability scanning (via ACAS and CI/CD container scanners) and continuous monitoring are performed via {{ THREAT_DETECTION_ENGINE }} and {{ CSSP_PROVIDER }}. |
| **FedRAMP High Parameter Values**: `ra-05.02_odp.01`: within 24 hours prior to running scans |


### RA-5(3) Vulnerability Monitoring and Scanning | Breadth and Depth of Coverage

Define the breadth and depth of vulnerability scanning coverage.


| Control Summary Information |
| :--- |
| **Responsible Role**: ISSO / DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC conducts platform-level threat modeling and vulnerability assessments for Google Cloud infrastructure (Inherited). Where configured in the system boundary, container and infrastructure vulnerability scanning and continuous posture monitoring are performed via accredited scanners and {{ THREAT_DETECTION_ENGINE }}. |


### RA-5(4) Vulnerability Monitoring and Scanning | Discoverable Information

Determine information about the system that is discoverable and take [Assignment: organization-defined corrective actions — FedRAMP High: notify appropriate service provider personnel and follow procedures for organization and service provider-defined corrective actions].


| Control Summary Information |
| :--- |
| **Responsible Role**: ISSO / DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC conducts platform-level threat modeling and vulnerability assessments for Google Cloud infrastructure (Inherited). Where configured in the system boundary, vulnerability scanning (via ACAS and CI/CD container scanners) and continuous monitoring are performed via {{ THREAT_DETECTION_ENGINE }} and {{ CSSP_PROVIDER }}. |
| **FedRAMP High Parameter Values**: `ra-05.04_odp` (corrective actions): notify appropriate service provider personnel and follow procedures for organization and service provider-defined corrective actions |


### RA-5(5) Vulnerability Monitoring and Scanning | Privileged Access

Implement privileged access authorization to [Assignment: organization-defined system components — FedRAMP High: all components that support authentication] for [Assignment: organization-defined vulnerability scanning activities — FedRAMP High: all scans].


| Control Summary Information |
| :--- |
| **Responsible Role**: ISSO / DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC conducts platform-level threat modeling and vulnerability assessments for Google Cloud infrastructure (Inherited). Where configured in the system boundary, vulnerability scanning (via ACAS and CI/CD container scanners) and continuous monitoring are performed via {{ THREAT_DETECTION_ENGINE }} and {{ CSSP_PROVIDER }}. |
| **FedRAMP High Parameter Values**: `ra-05.05_odp.01` (system components): all components that support authentication; `ra-05.05_odp.02` (vulnerability scanning activities): all scans |


### RA-5(8) Vulnerability Monitoring and Scanning | Review Historic Audit Logs

Review historic audit logs to determine if a vulnerability identified in a [Assignment: organization-defined system] has been previously exploited within an [Assignment: organization-defined time period].


| Control Summary Information |
| :--- |
| **Responsible Role**: ISSO / DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC conducts platform-level threat modeling and vulnerability assessments for Google Cloud infrastructure (Inherited). Where configured in the system boundary, container and infrastructure vulnerability scanning and continuous posture monitoring are performed via accredited scanners and {{ THREAT_DETECTION_ENGINE }}. |
| **FedRAMP Additional Guidance**: Requirement: This enhancement is required for all high (or critical) vulnerability scan findings. |


### RA-5(10) Vulnerability Monitoring and Scanning | Correlate Scanning Information

Correlate the output from vulnerability scanning tools to determine the presence of multi-vulnerability and multi-hop attack vectors.


| Control Summary Information |
| :--- |
| **Responsible Role**: ISSO / DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC conducts platform-level threat modeling and vulnerability assessments for Google Cloud infrastructure (Inherited). Where configured in the system boundary, vulnerability scanning (via ACAS and CI/CD container scanners) and continuous monitoring are performed via {{ THREAT_DETECTION_ENGINE }} and {{ CSSP_PROVIDER }}. |


### RA-5(11) Vulnerability Monitoring and Scanning | Public Disclosure Program

Establish a public reporting channel for receiving reports of vulnerabilities in organizational systems and system components.


| Control Summary Information |
| :--- |
| **Responsible Role**: ISSO / DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC conducts platform-level threat modeling and vulnerability assessments for Google Cloud infrastructure (Inherited). Where configured in the system boundary, vulnerability scanning (via ACAS and CI/CD container scanners) and continuous monitoring are performed via {{ THREAT_DETECTION_ENGINE }} and {{ CSSP_PROVIDER }}. |


### RA-7 Risk Response

Respond to findings from security and privacy assessments, monitoring, and audits in accordance with organizational risk tolerance.


| Control Summary Information |
| :--- |
| **Responsible Role**: ISSO / DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC conducts platform-level threat modeling and vulnerability assessments for Google Cloud infrastructure (Inherited). Where configured in the system boundary, vulnerability scanning (via ACAS and CI/CD container scanners) and continuous monitoring are performed via {{ THREAT_DETECTION_ENGINE }} and {{ CSSP_PROVIDER }}. |


### RA-9 Criticality Analysis

Identify critical system components and functions by performing a criticality analysis for [Assignment: organization-defined systems, system components, or system services] at [Assignment: organization-defined decision points in the system development life cycle].


| Control Summary Information |
| :--- |
| **Responsible Role**: ISSO / DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC conducts platform-level threat modeling and vulnerability assessments for Google Cloud infrastructure (Inherited). Where configured in the system boundary, vulnerability scanning (via ACAS and CI/CD container scanners) and continuous monitoring are performed via {{ THREAT_DETECTION_ENGINE }} and {{ CSSP_PROVIDER }}. |


### RA-10 Threat Hunting


a. Establish and maintain a cyber threat hunting capability to:

  1. Search for indicators of compromise in organizational systems; and

  2. Detect, track, and disrupt threats that evade existing controls; and


b. Employ the threat hunting capability [Assignment: organization-defined frequency].


| Control Summary Information |
| :--- |
| **Responsible Role**: ISSO / DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC conducts platform-level threat modeling and vulnerability assessments for Google Cloud infrastructure (Inherited). Where configured in the system boundary, vulnerability scanning (via ACAS and CI/CD container scanners) and continuous monitoring are performed via {{ THREAT_DETECTION_ENGINE }} and {{ CSSP_PROVIDER }}. |


## 2.17 System and Services Acquisition


### SA-1 Policy and Procedures


a. Develop, document, and disseminate to [Assignment: organization-defined personnel or roles]:

  1. [Selection (one or more): Organization-level; Mission/business process-level; System-level] system and services acquisition policy that:

    (a) Addresses purpose, scope, roles, responsibilities, management commitment, coordination among organizational entities, and compliance; and

    (b) Is consistent with applicable laws, executive orders, directives, regulations, policies, standards, and guidelines; and

  2. Procedures to facilitate the implementation of the system and services acquisition policy and the associated system and services acquisition controls;


b. Designate an [Assignment: organization-defined official] to manage the development, documentation, and dissemination of the system and services acquisition policy and procedures; and


c. Review and update the current system and services acquisition:

  1. Policy [Assignment: organization-defined frequency — FedRAMP High: at least annually] and following [Assignment: organization-defined events — FedRAMP High: significant changes]; and

  2. Procedures [Assignment: organization-defined frequency — FedRAMP High: at least annually] and following [Assignment: organization-defined events].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |
| **FedRAMP High Parameter Values**: `sa-01_odp.05` (frequency): at least annually; `sa-01_odp.07` (frequency): at least annually; `sa-01_odp.08` (events): significant changes |


### SA-2 Allocation of Resources


a. Determine the high-level information security and privacy requirements for the system or system service in mission and business process planning;


b. Determine, document, and allocate the resources required to protect the system or system service as part of the organizational capital planning and investment control process; and


c. Establish a discrete line item for information security and privacy in organizational programming and budgeting documentation.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-3 System Development Life Cycle


a. Acquire, develop, and manage the system using [Assignment: organization-defined system development life cycle] that incorporates information security and privacy considerations;


b. Define and document information security and privacy roles and responsibilities throughout the system development life cycle;


c. Identify individuals having information security and privacy roles and responsibilities; and


d. Integrate the organizational information security and privacy risk management process into system development life cycle activities.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-3(1) System Development Life Cycle | Manage Preproduction Environment

Protect system preproduction environments commensurate with risk throughout the system development life cycle for the system, system component, or system service.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-3(2) System Development Life Cycle | Use of Live or Operational Data


(a) Approve, document, and control the use of live data in preproduction environments for the system, system component, or system service; and


(b) Protect preproduction environments for the system, system component, or system service at the same impact or classification level as any live data in use within the preproduction environments.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-3(3) System Development Life Cycle | Technology Refresh

Plan for and implement a technology refresh schedule for the system throughout the system development life cycle.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-4 Acquisition Process


Include the following requirements, descriptions, and criteria, explicitly or by reference, using [Selection (one or more): standardized contract language; [Assignment: organization-defined contract language]] in the acquisition contract for the system, system component, or system service:


a. Security and privacy functional requirements;


b. Strength of mechanism requirements;


c. Security and privacy assurance requirements;


d. Controls needed to satisfy the security and privacy requirements.


e. Security and privacy documentation requirements;


f. Requirements for protecting security and privacy documentation;


g. Description of the system development environment and environment in which the system is intended to operate;


h. Allocation of responsibility or identification of parties responsible for information security, privacy, and supply chain risk management; and


i. Acceptance criteria.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |
| **FedRAMP Additional Guidance**: Requirement: The service provider must comply with Federal Acquisition Regulation (FAR) Subpart 7.103, and Section 889 of the John S. McCain National Defense Authorization Act (NDAA) for Fiscal Year 2019 (Pub. L. 115-232), and FAR Subpart 4.21, which implements Section 889 (as well as any added updates related to FISMA to address security concerns in the system acquisitions process). Guidance: The use of Common Criteria (ISO/IEC 15408) evaluated products is strongly preferred. See https://www.niap-ccevs.org/Product/index.cfm or https://www.commoncriteriaportal.org/products/. |


### SA-4(1) Acquisition Process | Functional Properties of Controls

Require the developer of the system, system component, or system service to provide a description of the functional properties of the controls to be implemented.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-4(2) Acquisition Process | Design and Implementation Information for Controls

Require the developer of the system, system component, or system service to provide design and implementation information for the controls that includes: [Selection (one or more): security-relevant external system interfaces; high-level design; low-level design; source code or hardware schematics; [Assignment: organization-defined design and implementation information — FedRAMP High: at a minimum to include security-relevant external system interfaces; high-level design; low-level design; source code or network and data flow diagram; organization-defined design/implementation information]] at [Assignment: organization-defined level of detail].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |
| **FedRAMP High Parameter Values**: `sa-04.02_odp.01`: at a minimum to include security-relevant external system interfaces; high-level design; low-level design; source code or network and data flow diagram; organization-defined design/implementation information |


### SA-4(3) Acquisition Process | Development Methods, Techniques, and Practices

Require the developer of the system, system component, or system service to demonstrate the use of a system development life cycle process that includes:

(a) [Assignment: organization-defined systems engineering methods];

(b) [Assignment: organization-defined [Selection (one or more): systems security; privacy] engineering methods]; and

(c) [Assignment: organization-defined software development methods; testing, evaluation, assessment, verification, and validation methods; and quality control processes].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-4(5) Acquisition Process | System, Component, and Service Configurations

Require the developer of the system, system component, or system service to:


(a) Deliver the system, component, or service with [Assignment: organization-defined security configurations — FedRAMP High: The service provider shall use the DoD STIGs to establish configuration settings; Center for Internet Security up to Level 2 (CIS Level 2) guidelines shall be used if STIGs are not available; Custom baselines shall be used if CIS is not available.] implemented; and


(b) Use the configurations as the default for any subsequent system, component, or service reinstallation or upgrade.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |
| **FedRAMP High Parameter Values**: `sa-04.05_odp` (security configurations): The service provider shall use the DoD STIGs to establish configuration settings; Center for Internet Security up to Level 2 (CIS Level 2) guidelines shall be used if STIGs are not available; Custom baselines shall be used if CIS is not available. |


### SA-4(7) Acquisition Process | NIAP-approved Protection Profiles


(a) Limit the use of commercially provided information assurance and information assurance-enabled information technology products to those products that have been successfully evaluated against a National Information Assurance partnership (NIAP)-approved Protection Profile for a specific technology type, if such a profile exists; and


(b) Require, if no NIAP-approved Protection Profile exists for a specific technology type but a commercially provided information technology product relies on cryptographic functionality to enforce its security policy, that the cryptographic module is FIPS-validated or NSA-approved.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-4(9) Acquisition Process | Functions, Ports, Protocols, and Services in Use

Require the developer of the system, system component, or system service to identify the functions, ports, protocols, and services intended for organizational use.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-4(10) Acquisition Process | Use of Approved PIV Products

Employ only information technology products on the FIPS 201-approved products list for Personal Identity Verification (PIV) capability implemented within organizational systems.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-5 System Documentation


a. Obtain or develop administrator documentation for the system, system component, or system service that describes:

  1. Secure configuration, installation, and operation of the system, component, or service;

  2. Effective use and maintenance of security and privacy functions and mechanisms; and

  3. Known vulnerabilities regarding configuration and use of administrative or privileged functions;


b. Obtain or develop user documentation for the system, system component, or system service that describes:

  1. User-accessible security and privacy functions and mechanisms and how to effectively use those functions and mechanisms;

  2. Methods for user interaction, which enables individuals to use the system, component, or service in a more secure manner and protect individual privacy; and

  3. User responsibilities in maintaining the security of the system, component, or service and privacy of individuals;


c. Document attempts to obtain system, system component, or system service documentation when such documentation is either unavailable or nonexistent and take [Assignment: organization-defined actions] in response; and


d. Distribute documentation to [Assignment: organization-defined personnel or roles — FedRAMP High: at a minimum, the ISSO (or similar role within the organization)].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |
| **FedRAMP High Parameter Values**: `sa-05_odp.02` (personnel or roles): at a minimum, the ISSO (or similar role within the organization) |


### SA-8 Security and Privacy Engineering Principles

Apply the following systems security and privacy engineering principles in the specification, design, development, implementation, and modification of the system and system components: [Assignment: organization-defined systems security and privacy engineering principles].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-8(1) Security and Privacy Engineering Principles | Clear Abstractions

Implement the security design principle of clear abstractions.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-8(2) Security and Privacy Engineering Principles | Least Common Mechanism

Implement the security design principle of least common mechanism in [Assignment: organization-defined systems or system components].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-8(3) Security and Privacy Engineering Principles | Modularity and Layering

Implement the security design principles of modularity and layering in [Assignment: organization-defined systems or system components].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-8(4) Security and Privacy Engineering Principles | Partially Ordered Dependencies

Implement the security design principle of partially ordered dependencies in [Assignment: organization-defined systems or system components].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-8(5) Security and Privacy Engineering Principles | Efficiently Mediated Access

Implement the security design principle of efficiently mediated access in [Assignment: organization-defined systems or system components].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-8(6) Security and Privacy Engineering Principles | Minimized Sharing

Implement the security design principle of minimized sharing in [Assignment: organization-defined systems or system components].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-8(7) Security and Privacy Engineering Principles | Reduced Complexity

Implement the security design principle of reduced complexity in [Assignment: organization-defined systems or system components].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-8(8) Security and Privacy Engineering Principles | Secure Evolvability

Implement the security design principle of secure evolvability in [Assignment: organization-defined systems or system components].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-8(9) Security and Privacy Engineering Principles | Trusted Components

Implement the security design principle of trusted components in [Assignment: organization-defined systems or system components].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-8(10) Security and Privacy Engineering Principles | Hierarchical Trust

Implement the security design principle of hierarchical trust in [Assignment: organization-defined systems or system components].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-8(11) Security and Privacy Engineering Principles | Inverse Modification Threshold

Implement the security design principle of inverse modification threshold in [Assignment: organization-defined systems or system components].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-8(12) Security and Privacy Engineering Principles | Hierarchical Protection

Implement the security design principle of hierarchical protection in [Assignment: organization-defined systems or system components].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-8(13) Security and Privacy Engineering Principles | Minimized Security Elements

Implement the security design principle of minimized security elements in [Assignment: organization-defined systems or system components].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-8(14) Security and Privacy Engineering Principles | Least Privilege

Implement the security design principle of least privilege in [Assignment: organization-defined systems or system components].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-8(15) Security and Privacy Engineering Principles | Predicate Permission

Implement the security design principle of predicate permission in [Assignment: organization-defined systems or system components].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-8(16) Security and Privacy Engineering Principles | Self-reliant Trustworthiness

Implement the security design principle of self-reliant trustworthiness in [Assignment: organization-defined systems or system components].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-8(17) Security and Privacy Engineering Principles | Secure Distributed Composition

Implement the security design principle of secure distributed composition in [Assignment: organization-defined systems or system components].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-8(18) Security and Privacy Engineering Principles | Trusted Communications Channels

Implement the security design principle of trusted communications channels in [Assignment: organization-defined systems or system components].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-8(19) Security and Privacy Engineering Principles | Continuous Protection

Implement the security design principle of continuous protection in [Assignment: organization-defined systems or system components].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-8(20) Security and Privacy Engineering Principles | Secure Metadata Management

Implement the security design principle of secure metadata management in [Assignment: organization-defined systems or system components].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-8(21) Security and Privacy Engineering Principles | Self-analysis

Implement the security design principle of self-analysis in [Assignment: organization-defined systems or system components].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-8(22) Security and Privacy Engineering Principles | Accountability and Traceability

Implement the security design principle of accountability and traceability in [Assignment: organization-defined systems or system components].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-8(23) Security and Privacy Engineering Principles | Secure Defaults

Implement the security design principle of secure defaults in [Assignment: organization-defined systems or system components].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-8(24) Security and Privacy Engineering Principles | Secure Failure and Recovery

Implement the security design principle of secure failure and recovery in [Assignment: organization-defined systems or system components].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-8(25) Security and Privacy Engineering Principles | Economic Security

Implement the security design principle of economic security in [Assignment: organization-defined systems or system components].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-8(26) Security and Privacy Engineering Principles | Performance Security

Implement the security design principle of performance security in [Assignment: organization-defined systems or system components].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-8(27) Security and Privacy Engineering Principles | Human Factored Security

Implement the security design principle of human factored security in [Assignment: organization-defined systems or system components].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-8(28) Security and Privacy Engineering Principles | Acceptable Security

Implement the security design principle of acceptable security in [Assignment: organization-defined systems or system components].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-8(29) Security and Privacy Engineering Principles | Repeatable and Documented Procedures

Implement the security design principle of repeatable and documented procedures in [Assignment: organization-defined systems or system components].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-8(30) Security and Privacy Engineering Principles | Procedural Rigor

Implement the security design principle of procedural rigor in [Assignment: organization-defined systems or system components].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-8(31) Security and Privacy Engineering Principles | Secure System Modification

Implement the security design principle of secure system modification in [Assignment: organization-defined systems or system components].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-8(32) Security and Privacy Engineering Principles | Sufficient Documentation

Implement the security design principle of sufficient documentation in [Assignment: organization-defined systems or system components].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-8(33) Security and Privacy Engineering Principles | Minimization

Implement the privacy principle of minimization using [Assignment: organization-defined processes].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [x] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud infrastructure. [CONFIG_REQUIRED: Document the Mission Owner implementation and verification procedures for SA-8(33) (Minimization) within the {{ DOD_IMPACT_LABEL }} boundary and confirm Implementation Status] |


### SA-9 External System Services


a. Require that providers of external system services comply with organizational security and privacy requirements and employ the following controls: [Assignment: organization-defined controls — FedRAMP High: Appropriate FedRAMP Security Controls Baseline (s) if Federal information is processed or stored within the external system];


b. Define and document organizational oversight and user roles and responsibilities with regard to external system services; and


c. Employ the following processes, methods, and techniques to monitor control compliance by external service providers on an ongoing basis: [Assignment: organization-defined processes, methods, and techniques — FedRAMP High: Federal/FedRAMP Continuous Monitoring requirements must be met for external systems where Federal information is processed or stored].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |
| **FedRAMP High Parameter Values**: `sa-09_odp.01` (controls): Appropriate FedRAMP Security Controls Baseline (s) if Federal information is processed or stored within the external system; `sa-09_odp.02` (processes, methods, and techniques): Federal/FedRAMP Continuous Monitoring requirements must be met for external systems where Federal information is processed or stored |


### SA-9(1) External System Services | Risk Assessments and Organizational Approvals


(a) Conduct an organizational assessment of risk prior to the acquisition or outsourcing of information security services; and


(b) Verify that the acquisition or outsourcing of dedicated information security services is approved by [Assignment: organization-defined personnel or roles].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-9(2) External System Services | Identification of Functions, Ports, Protocols, and Services

Require providers of the following external system services to identify the functions, ports, protocols, and other services required for the use of such services: [Assignment: organization-defined external system services — FedRAMP High: all external systems where Federal information is processed or stored].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |
| **FedRAMP High Parameter Values**: `sa-09.02_odp` (external system services): all external systems where Federal information is processed or stored |


### SA-9(3) External System Services | Establish and Maintain Trust Relationship with Providers

Establish, document, and maintain trust relationships with external service providers based on the following requirements, properties, factors, or conditions: [Assignment: organization-defined security and privacy requirements, properties, factors, or conditions defining acceptable trust relationships].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-9(5) External System Services | Processing, Storage, and Service Location

Restrict the location of [Selection (one or more): information processing; information or data; system services — FedRAMP High: information processing, information or data, AND system services] to [Assignment: organization-defined locations — FedRAMP High: U.S./U.S. Territories or geographic locations where there is U.S. jurisdiction] based on [Assignment: organization-defined requirements or conditions — FedRAMP High: all High impact data, systems, or services].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Per DoD Cloud Computing SRG ({{ DOD_IMPACT_SHORT }}) and SA-9(5), all information processing, storage, and service locations are restricted strictly to U.S. sovereign regions (`us-*`) and CONUS/DoD-accredited facilities via Google Cloud Assured Workloads {{ DOD_IMPACT_SHORT }} (`constraints/gcp.resourceLocations`), operated by screened U.S. persons. Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for acquisition and development of the underlying Google infrastructure, including hardware procurement. The system is deployed from version-controlled Terraform modules that are reviewed before use, following a secure development life cycle. |
| **FedRAMP High Parameter Values**: `sa-09.05_odp.01`: information processing, information or data, AND system services; `sa-09.05_odp.02` (locations): U.S./U.S. Territories or geographic locations where there is U.S. jurisdiction; `sa-09.05_odp.03` (requirements): all High impact data, systems, or services |


### SA-9(6) External System Services | Organization-controlled Cryptographic Keys

Maintain exclusive control of cryptographic keys for encrypted material stored or transmitted through an external system.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [x] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud infrastructure. [CONFIG_REQUIRED: Document the Mission Owner implementation and verification procedures for SA-9(6) (Organization-controlled Cryptographic Keys) within the {{ DOD_IMPACT_LABEL }} boundary and confirm Implementation Status] |


### SA-9(7) External System Services | Organization-controlled Integrity Checking

Provide the capability to check the integrity of information while it resides in the external system.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [x] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud infrastructure. [CONFIG_REQUIRED: Document the Mission Owner implementation and verification procedures for SA-9(7) (Organization-controlled Integrity Checking) within the {{ DOD_IMPACT_LABEL }} boundary and confirm Implementation Status] |


### SA-9(8) External System Services | Processing and Storage Location — U.S. Jurisdiction

Restrict the geographic location of information processing and data storage to facilities located within in the legal jurisdictional boundary of the United States.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-10 Developer Configuration Management

Require the developer of the system, system component, or system service to:


a. Perform configuration management during system, component, or service [Selection (one or more): design; development; implementation; operation; disposal — FedRAMP High: development, implementation, AND operation];


b. Document, manage, and control the integrity of changes to [Assignment: organization-defined configuration items under configuration management];


c. Implement only organization-approved changes to the system, component, or service;


d. Document approved changes to the system, component, or service and the potential security and privacy impacts of such changes; and


e. Track security flaws and flaw resolution within the system, component, or service and report findings to [Assignment: organization-defined personnel].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |
| **FedRAMP High Parameter Values**: `sa-10_odp.01`: development, implementation, AND operation<br>**FedRAMP Additional Guidance**: (e) Requirement: track security flaws and flaw resolution within the system, component, or service and report findings to organization-defined personnel, to include FedRAMP. |


### SA-10(1) Developer Configuration Management | Software and Firmware Integrity Verification

Require the developer of the system, system component, or system service to enable integrity verification of software and firmware components.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-10(3) Developer Configuration Management | Hardware Integrity Verification

Require the developer of the system, system component, or system service to enable integrity verification of hardware components.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-10(7) Developer Configuration Management | Security and Privacy Representatives

Require [Assignment: organization-defined security and privacy representatives] to be included in the [Assignment: organization-defined configuration change management and control process].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-11 Developer Testing and Evaluation

Require the developer of the system, system component, or system service, at all post-design stages of the system development life cycle, to:


a. Develop and implement a plan for ongoing security and privacy control assessments;


b. Perform [Selection (one or more): unit; integration; system; regression] testing/evaluation [Assignment: organization-defined frequency] at [Assignment: organization-defined depth and coverage];


c. Produce evidence of the execution of the assessment plan and the results of the testing and evaluation;


d. Implement a verifiable flaw remediation process; and


e. Correct flaws identified during testing and evaluation.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-11(1) Developer Testing and Evaluation | Static Code Analysis

Require the developer of the system, system component, or system service to employ static code analysis tools to identify common flaws and document the results of the analysis.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |
| **FedRAMP Additional Guidance**: Requirement: The service provider must document its methodology for reviewing newly developed code for the Service in its Continuous Monitoring Plan. If Static code analysis cannot be performed (for example, when the source code is not available), then dynamic code analysis must be performed (see SA-11 (8)) |


### SA-11(2) Developer Testing and Evaluation | Threat Modeling and Vulnerability Analyses

Require the developer of the system, system component, or system service to perform threat modeling and vulnerability analyses during development and the subsequent testing and evaluation of the system, component, or service that:


(a) Uses the following contextual information: [Assignment: organization-defined information concerning impact, environment of operations, known or assumed threats, and acceptable risk levels];


(b) Employs the following tools and methods: [Assignment: organization-defined tools and methods];


(c) Conducts the modeling and analyses at the following level of rigor: [Assignment: organization-defined breadth and depth of modeling and analyses]; and


(d) Produces evidence that meets the following acceptance criteria: [Assignment: organization-defined acceptance criteria].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-15 Development Process, Standards, and Tools


a. Require the developer of the system, system component, or system service to follow a documented development process that:

  1. Explicitly addresses security and privacy requirements;

  2. Identifies the standards and tools used in the development process;

  3. Documents the specific tool options and tool configurations used in the development process; and

  4. Documents, manages, and ensures the integrity of changes to the process and/or tools used in development; and


b. Review the development process, standards, tools, tool options, and tool configurations [Assignment: organization-defined frequency — FedRAMP High: frequency as before first use and annually thereafter] to determine if the process, standards, tools, tool options and tool configurations selected and employed can satisfy the following security and privacy requirements: [Assignment: organization-defined security and privacy requirements — FedRAMP High: FedRAMP Security Authorization requirements].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |
| **FedRAMP High Parameter Values**: `sa-15_odp.01` (frequency): frequency as before first use and annually thereafter; `sa-15_odp.02` (security requirements): FedRAMP Security Authorization requirements |


### SA-15(3) Development Process, Standards, and Tools | Criticality Analysis

Require the developer of the system, system component, or system service to perform a criticality analysis:


(a) At the following decision points in the system development life cycle: [Assignment: organization-defined decision points in the system development life cycle]; and


(b) At the following level of rigor: [Assignment: organization-defined breadth and depth of criticality analysis].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-15(7) Development Process, Standards, and Tools | Automated Vulnerability Analysis

Require the developer of the system, system component, or system service [Assignment: organization-defined frequency] to:

(a) Perform an automated vulnerability analysis using [Assignment: organization-defined tools];

(b) Determine the exploitation potential for discovered vulnerabilities;

(c) Determine potential risk mitigations for delivered vulnerabilities; and

(d) Deliver the outputs of the tools and results of the analysis to [Assignment: organization-defined personnel or roles].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [x] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud infrastructure. [CONFIG_REQUIRED: Document the Mission Owner implementation and verification procedures for SA-15(7) (Automated Vulnerability Analysis) within the {{ DOD_IMPACT_LABEL }} boundary and confirm Implementation Status] |


### SA-16 Developer-provided Training

Require the developer of the system, system component, or system service to provide the following training on the correct use and operation of the implemented security and privacy functions, controls, and/or mechanisms: [Assignment: organization-defined training].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-17 Developer Security and Privacy Architecture and Design

Require the developer of the system, system component, or system service to produce a design specification and security and privacy architecture that:


a. Is consistent with the organization's security and privacy architecture that is an integral part the organization's enterprise architecture;


b. Accurately and completely describes the required security and privacy functionality, and the allocation of controls among physical and logical components; and


c. Expresses how individual security and privacy functions, mechanisms, and services work together to provide required security and privacy capabilities and a unified approach to protection.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-21 Developer Screening

Require that the developer of [Assignment: organization-defined system, system component, or system service]:


a. Has appropriate access authorizations as determined by assigned [Assignment: organization-defined official government duties]; and


b. Satisfies the following additional personnel screening criteria: [Assignment: organization-defined additional personnel screening criteria].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-22 Unsupported System Components


a. Replace system components when support for the components is no longer available from the developer, vendor, or manufacturer; or


b. Provide the following options for alternative sources for continued support for unsupported components [Selection (one or more): in-house support; [Assignment: organization-defined support from external providers]].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


## 2.18 System and Communications Protection


### SC-1 Policy and Procedures


a. Develop, document, and disseminate to [Assignment: organization-defined personnel or roles]:

  1. [Selection (one or more): Organization-level; Mission/business process-level; System-level] system and communications protection policy that:

    (a) Addresses purpose, scope, roles, responsibilities, management commitment, coordination among organizational entities, and compliance; and

    (b) Is consistent with applicable laws, executive orders, directives, regulations, policies, standards, and guidelines; and

  2. Procedures to facilitate the implementation of the system and communications protection policy and the associated system and communications protection controls;


b. Designate an [Assignment: organization-defined official] to manage the development, documentation, and dissemination of the system and communications protection policy and procedures; and


c. Review and update the current system and communications protection:

  1. Policy [Assignment: organization-defined frequency — FedRAMP High: at least annually] and following [Assignment: organization-defined events — FedRAMP High: significant changes]; and

  2. Procedures [Assignment: organization-defined frequency — FedRAMP High: at least annually] and following [Assignment: organization-defined events].


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure and FIPS 140-validated cryptographic backends. Where configured in the system's Terraform blueprints, the system provisions VPC Service Controls security perimeters, Cloud KMS CMEK encryption (AES-256), TLS 1.2+ transport security, Private Google Access, Cloud NAT, Cloud DNS, and regional Cloud Armor WAF protection. |
| **FedRAMP High Parameter Values**: `sc-01_odp.05` (frequency): at least annually; `sc-01_odp.07` (frequency): at least annually; `sc-01_odp.08` (events): significant changes |


### SC-2 Separation of System and User Functionality

Separate user functionality, including user interface services, from system management functionality.


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for the Google-managed infrastructure that hosts the system. [CONFIG_REQUIRED: Confirm in the Google Cloud {{ DOD_IMPACT_LABEL }} / {{ BASE_FEDRAMP_LABEL }} customer responsibility matrix whether SC-2 is inherited or shared; document customer-configured controls and verify Implementation Status] |


### SC-3 Security Function Isolation

Isolate security functions from nonsecurity functions.


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for the Google-managed infrastructure that hosts the system. [CONFIG_REQUIRED: Confirm in the Google Cloud {{ DOD_IMPACT_LABEL }} / {{ BASE_FEDRAMP_LABEL }} customer responsibility matrix whether SC-3 is inherited or shared; document customer-configured controls and verify Implementation Status] |


### SC-4 Information in Shared System Resources

Prevent unauthorized and unintended information transfer via shared system resources.


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for the Google-managed infrastructure that hosts the system. [CONFIG_REQUIRED: Confirm in the Google Cloud {{ DOD_IMPACT_LABEL }} / {{ BASE_FEDRAMP_LABEL }} customer responsibility matrix whether SC-4 is inherited or shared; document customer-configured controls and verify Implementation Status] |


### SC-5 Denial-of-service Protection

a. [Selection: Protect against; Limit] the effects of the following types of denial-of-service events: [Assignment: organization-defined types of denial-of-service events — FedRAMP High: at a minimum: ICMP (ping) flood, SYN flood, slowloris, buffer overflow attack, and volume attack]; and


b. Employ the following controls to achieve the denial-of-service objective: [Assignment: organization-defined controls by type of denial-of-service event].


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure and FIPS 140-validated cryptographic backends. Where configured in the system's Terraform blueprints, the system provisions VPC Service Controls security perimeters, Cloud KMS CMEK encryption (AES-256), TLS 1.2+ transport security, Private Google Access, Cloud NAT, Cloud DNS, and regional Cloud Armor WAF protection. |
| **FedRAMP High Parameter Values**: `sc-05_odp.01` (types of denial-of-service events): at a minimum: ICMP (ping) flood, SYN flood, slowloris, buffer overflow attack, and volume attack; `sc-05_odp.02`: Protect against |


### SC-5(1) Denial-of-service Protection | Restrict Ability to Attack Other Systems

Restrict the ability of individuals to launch the following denial-of-service attacks against other systems: [Assignment: organization-defined denial-of-service attacks].


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure and FIPS 140-validated cryptographic backends. Where configured in the system's Terraform blueprints, the system provisions VPC Service Controls security perimeters, Cloud KMS CMEK encryption (AES-256), TLS 1.2+ transport security, Private Google Access, Cloud NAT, Cloud DNS, and regional Cloud Armor WAF protection. |


### SC-5(2) Denial-of-service Protection | Capacity, Bandwidth, and Redundancy

Manage capacity, bandwidth, or other redundancy to limit the effects of information flooding denial-of-service attacks.


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure and FIPS 140-validated cryptographic backends. Where configured in the system's Terraform blueprints, the system provisions VPC Service Controls security perimeters, Cloud KMS CMEK encryption (AES-256), TLS 1.2+ transport security, Private Google Access, Cloud NAT, Cloud DNS, and regional Cloud Armor WAF protection. |


### SC-5(3) Denial-of-service Protection | Detection and Monitoring


(a) Employ the following monitoring tools to detect indicators of denial-of-service attacks against, or launched from, the system: [Assignment: organization-defined monitoring tools]; and


(b) Monitor the following system resources to determine if sufficient resources exist to prevent effective denial-of-service attacks: [Assignment: organization-defined system resources].


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure and FIPS 140-validated cryptographic backends. Where configured in the system's Terraform blueprints, the system provisions VPC Service Controls security perimeters, Cloud KMS CMEK encryption (AES-256), TLS 1.2+ transport security, Private Google Access, Cloud NAT, Cloud DNS, and regional Cloud Armor WAF protection. |


### SC-7 Boundary Protection


a. Monitor and control communications at the external managed interfaces to the system and at key internal managed interfaces within the system;


b. Implement subnetworks for publicly accessible system components that are [Selection: physically; logically] separated from internal organizational networks; and


c. Connect to external networks or systems only through managed interfaces consisting of boundary protection devices arranged in accordance with an organizational security and privacy architecture.


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for physical datacenter boundary isolation and Google Cloud common infrastructure edge routing. Where configured in the system's Terraform blueprints, logical network perimeters enforce VPC ingress/egress firewall rules, isolated multi-tier subnet topologies, VPC Service Controls security perimeters, regional Cloud Armor edge filtering, and Private Google Access to deny unauthorized cross-boundary communications. |
| **FedRAMP Additional Guidance**: (b) Guidance: SC-7 (b) should be met by subnet isolation. A subnetwork (subnet) is a physically or logically segmented section of a larger network defined at TCP/IP Layer 3, to both minimize traffic and, important for a FedRAMP Authorization, add a crucial layer of network isolation. Subnets are distinct from VLANs (Layer 2), security groups, and VPCs and are specifically required to satisfy SC-7 part b and other controls. See the FedRAMP Subnets White Paper (https://www.fedramp.gov/assets/resources/documents/FedRAMP_subnets_white_paper.pdf) for additional information. |


### SC-7(3) Boundary Protection | Access Points

Limit the number of external network connections to the system.


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for physical datacenter boundary isolation and Google Cloud common infrastructure edge routing. Where configured in the system's Terraform blueprints, logical network perimeters enforce VPC ingress/egress firewall rules, isolated multi-tier subnet topologies, VPC Service Controls security perimeters, regional Cloud Armor edge filtering, and Private Google Access to deny unauthorized cross-boundary communications. |


### SC-7(4) Boundary Protection | External Telecommunications Services


(a) Implement a managed interface for each external telecommunication service;


(b) Establish a traffic flow policy for each managed interface;


(c) Protect the confidentiality and integrity of the information being transmitted across each interface;


(d) Document each exception to the traffic flow policy with a supporting mission or business need and duration of that need;


(e) Review exceptions to the traffic flow policy [Assignment: organization-defined frequency — FedRAMP High: at least every ninety (90) days or whenever there is a change in the threat environment that warrants a review of the exceptions] and remove exceptions that are no longer supported by an explicit mission or business need;


(f) Prevent unauthorized exchange of control plane traffic with external networks;


(g) Publish information to enable remote networks to detect unauthorized control plane traffic from internal networks; and


(h) Filter unauthorized control plane traffic from external networks.


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for physical datacenter boundary isolation and Google Cloud common infrastructure edge routing. Where configured in the system's Terraform blueprints, logical network perimeters enforce VPC ingress/egress firewall rules, isolated multi-tier subnet topologies, VPC Service Controls security perimeters, regional Cloud Armor edge filtering, and Private Google Access to deny unauthorized cross-boundary communications. |
| **FedRAMP High Parameter Values**: `sc-07.04_odp` (frequency): at least every ninety (90) days or whenever there is a change in the threat environment that warrants a review of the exceptions |


### SC-7(5) Boundary Protection | Deny by Default — Allow by Exception

Deny network communications traffic by default and allow network communications traffic by exception [Selection (one or more): at managed interfaces; for [Assignment: organization-defined systems — FedRAMP High: any systems]].


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for physical datacenter boundary isolation and Google Cloud common infrastructure edge routing. Where configured in the system's Terraform blueprints, logical network perimeters enforce VPC ingress/egress firewall rules, isolated multi-tier subnet topologies, VPC Service Controls security perimeters, regional Cloud Armor edge filtering, and Private Google Access to deny unauthorized cross-boundary communications. |
| **FedRAMP High Parameter Values**: `sc-07.05_odp.01`: any systems |


### SC-7(7) Boundary Protection | Split Tunneling for Remote Devices

Prevent split tunneling for remote devices connecting to organizational systems unless the split tunnel is securely provisioned using [Assignment: organization-defined safeguards].


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for physical datacenter boundary isolation and Google Cloud common infrastructure edge routing. Where configured in the system's Terraform blueprints, logical network perimeters enforce VPC ingress/egress firewall rules, isolated multi-tier subnet topologies, VPC Service Controls security perimeters, regional Cloud Armor edge filtering, and Private Google Access to deny unauthorized cross-boundary communications. |


### SC-7(8) Boundary Protection | Route Traffic to Authenticated Proxy Servers

Route [Assignment: organization-defined internal communications traffic] to [Assignment: organization-defined external networks — FedRAMP High: any network outside of organizational control and any network outside the authorization boundary] through authenticated proxy servers at managed interfaces.


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for physical datacenter boundary isolation and Google Cloud common infrastructure edge routing. Where configured in the system's Terraform blueprints, logical network perimeters enforce VPC ingress/egress firewall rules, isolated multi-tier subnet topologies, VPC Service Controls security perimeters, regional Cloud Armor edge filtering, and Private Google Access to deny unauthorized cross-boundary communications. |
| **FedRAMP High Parameter Values**: `sc-07.08_odp.02` (external networks): any network outside of organizational control and any network outside the authorization boundary |


### SC-7(9) Boundary Protection | Restrict Threatening Outgoing Communications Traffic


(a) Detect and deny outgoing communications traffic posing a threat to external systems; and


(b) Audit the identity of internal users associated with denied communications.


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for physical datacenter boundary isolation and Google Cloud common infrastructure edge routing. Where configured in the system's Terraform blueprints, logical network perimeters enforce VPC ingress/egress firewall rules, isolated multi-tier subnet topologies, VPC Service Controls security perimeters, regional Cloud Armor edge filtering, and Private Google Access to deny unauthorized cross-boundary communications. |


### SC-7(10) Boundary Protection | Prevent Exfiltration


(a) Prevent the exfiltration of information; and


(b) Conduct exfiltration tests [Assignment: organization-defined frequency].


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for physical datacenter boundary isolation and Google Cloud common infrastructure edge routing. Where configured in the system's Terraform blueprints, logical network perimeters enforce VPC ingress/egress firewall rules, isolated multi-tier subnet topologies, VPC Service Controls security perimeters, regional Cloud Armor edge filtering, and Private Google Access to deny unauthorized cross-boundary communications. |


### SC-7(11) Boundary Protection | Restrict Incoming Communications Traffic

Only allow incoming communications from [Assignment: organization-defined authorized sources] to be routed to [Assignment: organization-defined authorized destinations].


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for physical datacenter boundary isolation and Google Cloud common infrastructure edge routing. Where configured in the system's Terraform blueprints, logical network perimeters enforce VPC ingress/egress firewall rules, isolated multi-tier subnet topologies, VPC Service Controls security perimeters, regional Cloud Armor edge filtering, and Private Google Access to deny unauthorized cross-boundary communications. |


### SC-7(12) Boundary Protection | Host-based Protection

Implement [Assignment: organization-defined host-based boundary protection mechanisms — FedRAMP High: Host Intrusion Prevention System (HIPS), Host Intrusion Detection System (HIDS), or minimally a host-based firewall] at [Assignment: organization-defined system components].


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for physical datacenter boundary isolation and Google Cloud common infrastructure edge routing. Where configured in the system's Terraform blueprints, logical network perimeters enforce VPC ingress/egress firewall rules, isolated multi-tier subnet topologies, VPC Service Controls security perimeters, regional Cloud Armor edge filtering, and Private Google Access to deny unauthorized cross-boundary communications. |
| **FedRAMP High Parameter Values**: `sc-07.12_odp.01` (host-based boundary protection mechanisms): Host Intrusion Prevention System (HIPS), Host Intrusion Detection System (HIDS), or minimally a host-based firewall |


### SC-7(13) Boundary Protection | Isolation of Security Tools, Mechanisms, and Support Components

Isolate [Assignment: organization-defined information security tools, mechanisms, and support components] from other internal system components by implementing physically separate subnetworks with managed interfaces to other components of the system.


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for physical datacenter boundary isolation and Google Cloud common infrastructure edge routing. Where configured in the system's Terraform blueprints, logical network perimeters enforce VPC ingress/egress firewall rules, isolated multi-tier subnet topologies, VPC Service Controls security perimeters, regional Cloud Armor edge filtering, and Private Google Access to deny unauthorized cross-boundary communications. |


### SC-7(14) Boundary Protection | Protect Against Unauthorized Physical Connections

Protect against unauthorized physical connections at [Assignment: organization-defined managed interfaces].


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for physical datacenter boundary isolation and Google Cloud common infrastructure edge routing. Where configured in the system's Terraform blueprints, logical network perimeters enforce VPC ingress/egress firewall rules, isolated multi-tier subnet topologies, VPC Service Controls security perimeters, regional Cloud Armor edge filtering, and Private Google Access to deny unauthorized cross-boundary communications. |


### SC-7(15) Boundary Protection | Networked Privileged Accesses

Route networked, privileged accesses through a dedicated, managed interface for purposes of access control and auditing.


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for physical datacenter boundary isolation and Google Cloud common infrastructure edge routing. Where configured in the system's Terraform blueprints, logical network perimeters enforce VPC ingress/egress firewall rules, isolated multi-tier subnet topologies, VPC Service Controls security perimeters, regional Cloud Armor edge filtering, and Private Google Access to deny unauthorized cross-boundary communications. |


### SC-7(18) Boundary Protection | Fail Secure

Prevent systems from entering unsecure states in the event of an operational failure of a boundary protection device.


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for physical datacenter boundary isolation and Google Cloud common infrastructure edge routing. Where configured in the system's Terraform blueprints, logical network perimeters enforce VPC ingress/egress firewall rules, isolated multi-tier subnet topologies, VPC Service Controls security perimeters, regional Cloud Armor edge filtering, and Private Google Access to deny unauthorized cross-boundary communications. |


### SC-7(20) Boundary Protection | Dynamic Isolation and Segregation

Provide the capability to dynamically isolate [Assignment: organization-defined system components] from other system components.


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for physical datacenter boundary isolation and Google Cloud common infrastructure edge routing. Where configured in the system's Terraform blueprints, logical network perimeters enforce VPC ingress/egress firewall rules, isolated multi-tier subnet topologies, VPC Service Controls security perimeters, regional Cloud Armor edge filtering, and Private Google Access to deny unauthorized cross-boundary communications. |


### SC-7(21) Boundary Protection | Isolation of System Components

Employ boundary protection mechanisms to isolate [Assignment: organization-defined system components] supporting [Assignment: organization-defined missions and/or business functions].


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for physical datacenter boundary isolation and Google Cloud common infrastructure edge routing. Where configured in the system's Terraform blueprints, logical network perimeters enforce VPC ingress/egress firewall rules, isolated multi-tier subnet topologies, VPC Service Controls security perimeters, regional Cloud Armor edge filtering, and Private Google Access to deny unauthorized cross-boundary communications. |


### SC-7(25) Boundary Protection | Unclassified National Security System Connections

Prohibit the direct connection of [Assignment: organization-defined unclassified national security system] to an external network without the use of [Assignment: organization-defined boundary protection device].


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for physical datacenter boundary isolation and Google Cloud common infrastructure edge routing. Where configured in the system's Terraform blueprints, logical network perimeters enforce VPC ingress/egress firewall rules, isolated multi-tier subnet topologies, VPC Service Controls security perimeters, regional Cloud Armor edge filtering, and Private Google Access to deny unauthorized cross-boundary communications. |


### SC-7(28) Boundary Protection | Connections to Public Networks

Prohibit the direct connection of [Assignment: organization-defined system] to a public network.


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for physical datacenter boundary isolation and Google Cloud common infrastructure edge routing. Where configured in the system's Terraform blueprints, logical network perimeters enforce VPC ingress/egress firewall rules, isolated multi-tier subnet topologies, VPC Service Controls security perimeters, regional Cloud Armor edge filtering, and Private Google Access to deny unauthorized cross-boundary communications. |


### SC-7(29) Boundary Protection | Separate Subnets to Isolate Functions

Implement [Selection: physically; logically] separate subnetworks to isolate the following critical system components and functions: [Assignment: organization-defined critical system components and functions].


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for physical datacenter boundary isolation and Google Cloud common infrastructure edge routing. Where configured in the system's Terraform blueprints, logical network perimeters enforce VPC ingress/egress firewall rules, isolated multi-tier subnet topologies, VPC Service Controls security perimeters, regional Cloud Armor edge filtering, and Private Google Access to deny unauthorized cross-boundary communications. |


### SC-8 Transmission Confidentiality and Integrity

Protect the [Selection (one or more): confidentiality; integrity — FedRAMP High: confidentiality AND integrity] of transmitted information.


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for physical inter-datacenter backbone MACsec encryption and internal RPC mTLS. All system communications across internal and external network interfaces enforce FIPS 140-validated TLS 1.2+ encryption for data in transit, disabling legacy cipher suites and unencrypted plaintext protocols across all public and internal service endpoints. |
| **FedRAMP High Parameter Values**: `sc-08_odp`: confidentiality AND integrity<br>**FedRAMP Additional Guidance**: Guidance: For each instance of data in transit, confidentiality AND integrity should be through cryptography as specified in SC-8 (1), physical means as specified in SC-8 (5), or in combination. For clarity, this control applies to all data in transit. Examples include the following data flows: - Crossing the system boundary - Between compute instances - including containers - From a compute instance to storage - Replication between availability zones - Transmission of backups to storage - From a load balancer to a compute instance - Flows from management tools required for their work - e.g. log collection, scanning, etc. The following applies only when choosing SC-8 (5) in lieu of SC-8 (1). FedRAMP-Defined Assignment / Selection Parameters SC-8 (5)-1 \[a hardened or alarmed carrier Protective Distribution System (PDS) when outside of Controlled Access Area (CAA)\] SC-8 (5)-2 \[prevent unauthorized disclosure of information AND detect changes to information\] Guidance: SC-8 (5) applies when physical protection has been selected as the method to protect confidentiality and integrity. For physical protection, data in transit must be in either a Controlled Access Area (CAA), or a Hardened or alarmed PDS. Hardened or alarmed PDS: Shall be as defined in SECTION X - CATEGORY 2 PDS INSTALLATION GUIDANCE of CNSSI No.7003, titled PROTECTED DISTRIBUTION SYSTEMS (PDS). Per the CNSSI No. 7003 Section VIII, PDS must originate and terminate in a Controlled Access Area (CAA). Controlled Access Area (CAA): Data will be considered physically protected, and in a CAA if it meets Section 2.3 of the DHS's Recommended Practice: Improving Industrial Control System Cybersecurity with Defense-in-Depth Strategies. CSPs can meet Section 2.3 of the DHS' recommended practice by satisfactory implementation of the following controls PE-2 (1), PE-2 (2), PE-2 (3), PE-3 (2), PE-3 (3), PE-6 (2), and PE-6 (3). Note: When selecting SC-8 (5), the above SC-8(5), and the above referenced PE controls must be added to the SSP. CNSSI No.7003 can be accessed here: https://www.dcsa.mil/Portals/91/documents/ctp/nao/CNSSI_7003_PDS_September_2015.pdf DHS Recommended Practice: Improving Industrial Control System Cybersecurity with Defense-in-Depth Strategies can be accessed here: https://us-cert.cisa.gov/sites/default/files/FactSheets/NCCIC%20ICS_FactSheet_Defense_in_Depth_Strategies_S508C.pdf |


### SC-8(1) Transmission Confidentiality and Integrity | Cryptographic Protection

Implement cryptographic mechanisms to [Selection (one or more): prevent unauthorized disclosure of information; detect changes to information — FedRAMP High: prevent unauthorized disclosure of information AND detect changes to information] during transmission.


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for physical inter-datacenter backbone MACsec encryption and internal RPC mTLS. All system communications across internal and external network interfaces enforce FIPS 140-validated TLS 1.2+ encryption for data in transit, disabling legacy cipher suites and unencrypted plaintext protocols across all public and internal service endpoints. |
| **FedRAMP High Parameter Values**: `sc-08.01_odp`: prevent unauthorized disclosure of information AND detect changes to information<br>**FedRAMP Additional Guidance**: Requirement: Please ensure SSP Section 10.3 Cryptographic Modules Implemented for Data At Rest (DAR) and Data In Transit (DIT) is fully populated for reference in this control. Guidance: See M-22-09, including "Agencies encrypt all DNS requests and HTTP traffic within their environment" SC-8 (1) applies when encryption has been selected as the method to protect confidentiality and integrity. Otherwise refer to SC-8 (5). SC-8 (1) is strongly encouraged. Guidance: Note that this enhancement requires the use of cryptography which must be compliant with Federal requirements and utilize FIPS validated or NSA approved cryptography (see SC-13.) Guidance: When leveraging encryption from the underlying IaaS/PaaS: While some IaaS/PaaS services provide encryption by default, many require encryption to be configured, and enabled by the customer. The CSP has the responsibility to verify encryption is properly configured. |


### SC-8(2) Transmission Confidentiality and Integrity | Pre- and Post-transmission Handling

Maintain the [Selection (one or more): confidentiality; integrity] of information during preparation for transmission and during reception.


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for physical inter-datacenter backbone MACsec encryption and internal RPC mTLS. All system communications across internal and external network interfaces enforce FIPS 140-validated TLS 1.2+ encryption for data in transit, disabling legacy cipher suites and unencrypted plaintext protocols across all public and internal service endpoints. |


### SC-10 Network Disconnect

Terminate the network connection associated with a communications session at the end of the session or after [Assignment: organization-defined time period — FedRAMP High: no longer than ten (10) minutes for privileged sessions and no longer than fifteen (15) minutes for user sessions] of inactivity.


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure and FIPS 140-validated cryptographic backends. Where configured in the system's Terraform blueprints, the system provisions VPC Service Controls security perimeters, Cloud KMS CMEK encryption (AES-256), TLS 1.2+ transport security, Private Google Access, Cloud NAT, Cloud DNS, and regional Cloud Armor WAF protection. |
| **FedRAMP High Parameter Values**: `sc-10_odp` (time period): no longer than ten (10) minutes for privileged sessions and no longer than fifteen (15) minutes for user sessions |


### SC-12 Cryptographic Key Establishment and Management

Establish and manage cryptographic keys when cryptography is employed within the system in accordance with the following key management requirements: [Assignment: organization-defined requirements for key generation, distribution, storage, access, and destruction — FedRAMP High: In accordance with Federal requirements].


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure and FIPS 140-validated cryptographic backends. Where configured in the system's Terraform blueprints, the system provisions VPC Service Controls security perimeters, Cloud KMS CMEK encryption (AES-256), TLS 1.2+ transport security, Private Google Access, Cloud NAT, Cloud DNS, and regional Cloud Armor WAF protection. |
| **FedRAMP High Parameter Values**: `sc-12_odp` (requirements): In accordance with Federal requirements<br>**FedRAMP Additional Guidance**: Guidance: See references in NIST 800-53 documentation. Guidance: Must meet applicable Federal Cryptographic Requirements. See References Section of control. Guidance: Wildcard certificates may be used internally within the system, but are not permitted for external customer access to the system. |


### SC-12(1) Cryptographic Key Establishment and Management | Availability

Maintain availability of information in the event of the loss of cryptographic keys by users.


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure and FIPS 140-validated cryptographic backends. Where configured in the system's Terraform blueprints, the system provisions VPC Service Controls security perimeters, Cloud KMS CMEK encryption (AES-256), TLS 1.2+ transport security, Private Google Access, Cloud NAT, Cloud DNS, and regional Cloud Armor WAF protection. |


### SC-12(6) Cryptographic Key Establishment and Management | Physical Control of Keys

Maintain physical control of cryptographic keys when stored information is encrypted by external service providers.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [x] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud infrastructure. [CONFIG_REQUIRED: Document the Mission Owner implementation and verification procedures for SC-12(6) (Physical Control of Keys) within the {{ DOD_IMPACT_LABEL }} boundary and confirm Implementation Status] |


### SC-13 Cryptographic Protection


a. Determine the [Assignment: organization-defined cryptographic uses]; and


b. Implement the following types of cryptography required for each specified cryptographic use: [Assignment: organization-defined types of cryptography for each specified cryptographic use — FedRAMP High: FIPS-validated or NSA-approved cryptography].


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure and FIPS 140-validated cryptographic backends. Where configured in the system's Terraform blueprints, the system provisions VPC Service Controls security perimeters, Cloud KMS CMEK encryption (AES-256), TLS 1.2+ transport security, Private Google Access, Cloud NAT, Cloud DNS, and regional Cloud Armor WAF protection. |
| **FedRAMP High Parameter Values**: `sc-13_odp.02` (types of cryptography): FIPS-validated or NSA-approved cryptography<br>**FedRAMP Additional Guidance**: Guidance: This control applies to all use of cryptography. In addition to encryption, this includes functions such as hashing, random number generation, and key generation. Examples include the following: - Encryption of data - Decryption of data - Generation of one time passwords (OTPs) for MFA - Protocols such as TLS, SSH, and HTTPS The requirement for FIPS 140 validation, as well as timelines for acceptance of FIPS 140-2, and 140-3 can be found at the NIST Cryptographic Module Validation Program (CMVP). https://csrc.nist.gov/projects/cryptographic-module-validation-program Guidance: For NSA-approved cryptography, the National Information Assurance Partnership (NIAP) oversees a national program to evaluate Commercial IT Products for Use in National Security Systems. The NIAP Product Compliant List can be found at the following location: https://www.niap-ccevs.org/Product/index.cfm Guidance: When leveraging encryption from underlying IaaS/PaaS: While some IaaS/PaaS provide encryption by default, many require encryption to be configured, and enabled by the customer. The CSP has the responsibility to verify encryption is properly configured. Guidance: Moving to non-FIPS CM or product is acceptable when: - FIPS validated version has a known vulnerability - Feature with vulnerability is in use - Non-FIPS version fixes the vulnerability - Non-FIPS version is submitted to NIST for FIPS validation - POA\&M is added to track approval, and deployment when ready Guidance: At a minimum, this control applies to cryptography in use for the following controls: AU-9(3), CP-9(8), IA-2(6), IA-5(1), MP-5, SC-8(1), and SC-28(1). |


### SC-15 Collaborative Computing Devices and Applications


a. Prohibit remote activation of collaborative computing devices and applications with the following exceptions: [Assignment: organization-defined exceptions where remote activation is to be allowed — FedRAMP High: no exceptions for computing devices]; and


b. Provide an explicit indication of use to users physically present at the devices.


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for the Google-managed infrastructure that hosts the system. [CONFIG_REQUIRED: Confirm in the Google Cloud {{ DOD_IMPACT_LABEL }} / {{ BASE_FEDRAMP_LABEL }} customer responsibility matrix whether SC-15 is inherited or shared; document customer-configured controls and verify Implementation Status] |
| **FedRAMP High Parameter Values**: `sc-15_odp` (exceptions where remote activation is to be allowed): no exceptions for computing devices<br>**FedRAMP Additional Guidance**: Requirement: The information system provides disablement (instead of physical disconnect) of collaborative computing devices in a manner that supports ease of use. |


### SC-16 Transmission of Security and Privacy Attributes

Associate [Assignment: organization-defined security and privacy attributes] with information exchanged between systems and between system components.


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure and FIPS 140-validated cryptographic backends. Where configured in the system's Terraform blueprints, the system provisions VPC Service Controls security perimeters, Cloud KMS CMEK encryption (AES-256), TLS 1.2+ transport security, Private Google Access, Cloud NAT, Cloud DNS, and regional Cloud Armor WAF protection. |


### SC-16(1) Transmission of Security and Privacy Attributes | Integrity Verification

Verify the integrity of transmitted security and privacy attributes.


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure and FIPS 140-validated cryptographic backends. Where configured in the system's Terraform blueprints, the system provisions VPC Service Controls security perimeters, Cloud KMS CMEK encryption (AES-256), TLS 1.2+ transport security, Private Google Access, Cloud NAT, Cloud DNS, and regional Cloud Armor WAF protection. |


### SC-16(2) Transmission of Security and Privacy Attributes | Anti-spoofing Mechanisms

Implement anti-spoofing mechanisms to prevent adversaries from falsifying the security attributes indicating the successful application of the security process.


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure and FIPS 140-validated cryptographic backends. Where configured in the system's Terraform blueprints, the system provisions VPC Service Controls security perimeters, Cloud KMS CMEK encryption (AES-256), TLS 1.2+ transport security, Private Google Access, Cloud NAT, Cloud DNS, and regional Cloud Armor WAF protection. |


### SC-16(3) Transmission of Security and Privacy Attributes | Cryptographic Binding

Implement [Assignment: organization-defined mechanisms or techniques] to bind security and privacy attributes to transmitted information.


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure and FIPS 140-validated cryptographic backends. Where configured in the system's Terraform blueprints, the system provisions VPC Service Controls security perimeters, Cloud KMS CMEK encryption (AES-256), TLS 1.2+ transport security, Private Google Access, Cloud NAT, Cloud DNS, and regional Cloud Armor WAF protection. |


### SC-17 Public Key Infrastructure Certificates


a. Issue public key certificates under an [Assignment: organization-defined certificate policy] or obtain public key certificates from an approved service provider; and


b. Include only approved trust anchors in trust stores or certificate stores managed by the organization.


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure and FIPS 140-validated cryptographic backends. Where configured in the system's Terraform blueprints, the system provisions VPC Service Controls security perimeters, Cloud KMS CMEK encryption (AES-256), TLS 1.2+ transport security, Private Google Access, Cloud NAT, Cloud DNS, and regional Cloud Armor WAF protection. |


### SC-18 Mobile Code


a. Define acceptable and unacceptable mobile code and mobile code technologies; and


b. Authorize, monitor, and control the use of mobile code within the system.


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure and FIPS 140-validated cryptographic backends. Where configured in the system's Terraform blueprints, the system provisions VPC Service Controls security perimeters, Cloud KMS CMEK encryption (AES-256), TLS 1.2+ transport security, Private Google Access, Cloud NAT, Cloud DNS, and regional Cloud Armor WAF protection. |


### SC-18(1) Mobile Code | Identify Unacceptable Code and Take Corrective Actions

Identify [Assignment: organization-defined unacceptable mobile code] and take [Assignment: organization-defined corrective actions].


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure and FIPS 140-validated cryptographic backends. Where configured in the system's Terraform blueprints, the system provisions VPC Service Controls security perimeters, Cloud KMS CMEK encryption (AES-256), TLS 1.2+ transport security, Private Google Access, Cloud NAT, Cloud DNS, and regional Cloud Armor WAF protection. |


### SC-18(2) Mobile Code | Acquisition, Development, and Use

Verify that the acquisition, development, and use of mobile code to be deployed in the system meets [Assignment: organization-defined mobile code requirements].


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure and FIPS 140-validated cryptographic backends. Where configured in the system's Terraform blueprints, the system provisions VPC Service Controls security perimeters, Cloud KMS CMEK encryption (AES-256), TLS 1.2+ transport security, Private Google Access, Cloud NAT, Cloud DNS, and regional Cloud Armor WAF protection. |


### SC-18(3) Mobile Code | Prevent Downloading and Execution

Prevent the download and execution of [Assignment: organization-defined unacceptable mobile code].


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure and FIPS 140-validated cryptographic backends. Where configured in the system's Terraform blueprints, the system provisions VPC Service Controls security perimeters, Cloud KMS CMEK encryption (AES-256), TLS 1.2+ transport security, Private Google Access, Cloud NAT, Cloud DNS, and regional Cloud Armor WAF protection. |


### SC-18(4) Mobile Code | Prevent Automatic Execution

Prevent the automatic execution of mobile code in [Assignment: organization-defined software applications] and enforce [Assignment: organization-defined actions] prior to executing the code.


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure and FIPS 140-validated cryptographic backends. Where configured in the system's Terraform blueprints, the system provisions VPC Service Controls security perimeters, Cloud KMS CMEK encryption (AES-256), TLS 1.2+ transport security, Private Google Access, Cloud NAT, Cloud DNS, and regional Cloud Armor WAF protection. |


### SC-20 Secure Name/Address Resolution Service (Authoritative Source)


a. Provide additional data origin authentication and integrity verification artifacts along with the authoritative name resolution data the system returns in response to external name/address resolution queries; and


b. Provide the means to indicate the security status of child zones and (if the child supports secure resolution services) to enable verification of a chain of trust among parent and child domains, when operating as part of a distributed, hierarchical namespace.


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for the Google-managed infrastructure that hosts the system. [CONFIG_REQUIRED: Confirm in the Google Cloud {{ DOD_IMPACT_LABEL }} / {{ BASE_FEDRAMP_LABEL }} customer responsibility matrix whether SC-20 is inherited or shared; document customer-configured controls and verify Implementation Status] |
| **FedRAMP Additional Guidance**: Requirement: Control Description should include how DNSSEC is implemented on authoritative DNS servers to supply valid responses to external DNSSEC requests. Requirement: Authoritative DNS servers must be geolocated in accordance with SA-9 (5). Guidance: SC-20 applies to use of external authoritative DNS to access a CSO from outside the boundary. Guidance: External authoritative DNS servers may be located outside an authorized environment. Positioning these servers inside an authorized boundary is encouraged. Guidance: CSPs are recommended to self-check DNSSEC configuration through one of many available analyzers such as Sandia National Labs (https://dnsviz.net) |


### SC-21 Secure Name/Address Resolution Service (Recursive or Caching Resolver)

Request and perform data origin authentication and data integrity verification on the name/address resolution responses the system receives from authoritative sources.


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for the Google-managed infrastructure that hosts the system. [CONFIG_REQUIRED: Confirm in the Google Cloud {{ DOD_IMPACT_LABEL }} / {{ BASE_FEDRAMP_LABEL }} customer responsibility matrix whether SC-21 is inherited or shared; document customer-configured controls and verify Implementation Status] |
| **FedRAMP Additional Guidance**: Requirement: Control description should include how DNSSEC is implemented on recursive DNS servers to make DNSSEC requests when resolving DNS requests from internal components to domains external to the CSO boundary. - If the reply is signed, and fails DNSSEC, do not use the reply - If the reply is unsigned: - CSP chooses the policy to apply Requirement: Internal recursive DNS servers must be located inside an authorized environment. It is typically within the boundary, or leveraged from an underlying IaaS/PaaS. Guidance: Accepting an unsigned reply is acceptable Guidance: SC-21 applies to use of internal recursive DNS to access a domain outside the boundary by a component inside the boundary. - DNSSEC resolution to access a component inside the boundary is excluded. |


### SC-22 Architecture and Provisioning for Name/Address Resolution Service

Ensure the systems that collectively provide name/address resolution service for an organization are fault-tolerant and implement internal and external role separation.


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for the Google-managed infrastructure that hosts the system. [CONFIG_REQUIRED: Confirm in the Google Cloud {{ DOD_IMPACT_LABEL }} / {{ BASE_FEDRAMP_LABEL }} customer responsibility matrix whether SC-22 is inherited or shared; document customer-configured controls and verify Implementation Status] |


### SC-23 Session Authenticity

Protect the authenticity of communications sessions.


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for the Google-managed infrastructure that hosts the system. [CONFIG_REQUIRED: Confirm in the Google Cloud {{ DOD_IMPACT_LABEL }} / {{ BASE_FEDRAMP_LABEL }} customer responsibility matrix whether SC-23 is inherited or shared; document customer-configured controls and verify Implementation Status] |


### SC-23(1) Session Authenticity | Invalidate Session Identifiers at Logout

Invalidate session identifiers upon user logout or other session termination.


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure and FIPS 140-validated cryptographic backends. Where configured in the system's Terraform blueprints, the system provisions VPC Service Controls security perimeters, Cloud KMS CMEK encryption (AES-256), TLS 1.2+ transport security, Private Google Access, Cloud NAT, Cloud DNS, and regional Cloud Armor WAF protection. |


### SC-23(3) Session Authenticity | Unique System-generated Session Identifiers

Generate a unique session identifier for each session with [Assignment: organization-defined randomness requirements] and recognize only session identifiers that are system-generated.


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure and FIPS 140-validated cryptographic backends. Where configured in the system's Terraform blueprints, the system provisions VPC Service Controls security perimeters, Cloud KMS CMEK encryption (AES-256), TLS 1.2+ transport security, Private Google Access, Cloud NAT, Cloud DNS, and regional Cloud Armor WAF protection. |


### SC-23(5) Session Authenticity | Allowed Certificate Authorities

Only allow the use of [Assignment: organization-defined certificate authorities] for verification of the establishment of protected sessions.


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure and FIPS 140-validated cryptographic backends. Where configured in the system's Terraform blueprints, the system provisions VPC Service Controls security perimeters, Cloud KMS CMEK encryption (AES-256), TLS 1.2+ transport security, Private Google Access, Cloud NAT, Cloud DNS, and regional Cloud Armor WAF protection. |


### SC-24 Fail in Known State

Fail to a [Assignment: organization-defined known system state] for the following failures on the indicated components while preserving [Assignment: organization-defined system state information] in failure: [Assignment: list of organization-defined types of system failures on organization-defined system components].


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for the Google-managed infrastructure that hosts the system. [CONFIG_REQUIRED: Confirm in the Google Cloud {{ DOD_IMPACT_LABEL }} / {{ BASE_FEDRAMP_LABEL }} customer responsibility matrix whether SC-24 is inherited or shared; document customer-configured controls and verify Implementation Status] |


### SC-28 Protection of Information at Rest

Protect the [Selection (one or more): confidentiality; integrity — FedRAMP High: confidentiality AND integrity] of the following information at rest: [Assignment: organization-defined information at rest].


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for default hardware-level AES-256 encryption across all physical persistent storage media. System persistent data repositories (Cloud Storage, persistent disks, databases) enforce cryptographic protection using FIPS 140-validated cryptographic modules with Customer-Managed Encryption Keys (CMEK) via Cloud KMS, automated key rotation, and separation of duties. |
| **FedRAMP High Parameter Values**: `sc-28_odp.01`: confidentiality AND integrity<br>**FedRAMP Additional Guidance**: Guidance: The organization supports the capability to use cryptographic mechanisms to protect information at rest. Guidance: When leveraging encryption from underlying IaaS/PaaS: While some IaaS/PaaS services provide encryption by default, many require encryption to be configured, and enabled by the customer. The CSP has the responsibility to verify encryption is properly configured. Guidance: Note that this enhancement requires the use of cryptography in accordance with SC-13. |


### SC-28(1) Protection of Information at Rest | Cryptographic Protection

Implement cryptographic mechanisms to prevent unauthorized disclosure and modification of the following information at rest on [Assignment: organization-defined system components or media — FedRAMP High: all information system components storing Federal data or system data that must be protected at the High or Moderate impact levels]: [Assignment: organization-defined information].


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for default hardware-level AES-256 encryption across all physical persistent storage media. System persistent data repositories (Cloud Storage, persistent disks, databases) enforce cryptographic protection using FIPS 140-validated cryptographic modules with Customer-Managed Encryption Keys (CMEK) via Cloud KMS, automated key rotation, and separation of duties. |
| **FedRAMP High Parameter Values**: `sc-28.01_odp.02` (system components or media): all information system components storing Federal data or system data that must be protected at the High or Moderate impact levels<br>**FedRAMP Additional Guidance**: Guidance: Organizations should select a mode of protection that is targeted towards the relevant threat scenarios. Examples: A. Organizations may apply full disk encryption (FDE) to a mobile device where the primary threat is loss of the device while storage is locked. B. For a database application housing data for a single customer, encryption at the file system level would often provide more protection than FDE against the more likely threat of an intruder on the operating system accessing the storage. C. For a database application housing data for multiple customers, encryption with unique keys for each customer at the database record level may be more appropriate. |


### SC-28(3) Protection of Information at Rest | Cryptographic Keys

Provide protected storage for cryptographic keys [Selection: [Assignment: organization-defined safeguards]; hardware-protected key store].


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for default hardware-level AES-256 encryption across all physical persistent storage media. System persistent data repositories (Cloud Storage, persistent disks, databases) enforce cryptographic protection using FIPS 140-validated cryptographic modules with Customer-Managed Encryption Keys (CMEK) via Cloud KMS, automated key rotation, and separation of duties. |


### SC-38 Operations Security

Employ the following operations security controls to protect key organizational information throughout the system development life cycle: [Assignment: organization-defined operations security controls].


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure and FIPS 140-validated cryptographic backends. Where configured in the system's Terraform blueprints, the system provisions VPC Service Controls security perimeters, Cloud KMS CMEK encryption (AES-256), TLS 1.2+ transport security, Private Google Access, Cloud NAT, Cloud DNS, and regional Cloud Armor WAF protection. |


### SC-39 Process Isolation

Maintain a separate execution domain for each executing system process.


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for the Google-managed infrastructure that hosts the system. [CONFIG_REQUIRED: Confirm in the Google Cloud {{ DOD_IMPACT_LABEL }} / {{ BASE_FEDRAMP_LABEL }} customer responsibility matrix whether SC-39 is inherited or shared; document customer-configured controls and verify Implementation Status] |


### SC-41 Port and I/O Device Access

[Selection: Physically; Logically] disable or remove [Assignment: organization-defined connection ports or input/output devices] on the following systems or system components: [Assignment: organization-defined systems or system components].


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure and FIPS 140-validated cryptographic backends. Where configured in the system's Terraform blueprints, the system provisions VPC Service Controls security perimeters, Cloud KMS CMEK encryption (AES-256), TLS 1.2+ transport security, Private Google Access, Cloud NAT, Cloud DNS, and regional Cloud Armor WAF protection. |


### SC-45 System Time Synchronization

Synchronize system clocks within and between systems and system components.


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure and FIPS 140-validated cryptographic backends. Where configured in the system's Terraform blueprints, the system provisions VPC Service Controls security perimeters, Cloud KMS CMEK encryption (AES-256), TLS 1.2+ transport security, Private Google Access, Cloud NAT, Cloud DNS, and regional Cloud Armor WAF protection. |


### SC-45(1) System Time Synchronization | Synchronization with Authoritative Time Source


(a) Compare the internal system clocks [Assignment: organization-defined frequency — FedRAMP High: At least hourly] with [Assignment: organization-defined authoritative time source — FedRAMP High: http://tf.nist.gov/tf-cgi/servers.cgi]; and


(b) Synchronize the internal system clocks to the authoritative time source when the time difference is greater than [Assignment: organization-defined time period — FedRAMP High: any difference].


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure and FIPS 140-validated cryptographic backends. Where configured in the system's Terraform blueprints, the system provisions VPC Service Controls security perimeters, Cloud KMS CMEK encryption (AES-256), TLS 1.2+ transport security, Private Google Access, Cloud NAT, Cloud DNS, and regional Cloud Armor WAF protection. |
| **FedRAMP High Parameter Values**: `sc-45.01_odp.01` (frequency): At least hourly; `sc-45.01_odp.02` (authoritative time source): http://tf.nist.gov/tf-cgi/servers.cgi; `sc-45.01_odp.03` (time period): any difference<br>**FedRAMP Additional Guidance**: Requirement: The service provider selects primary and secondary time servers used by the NIST Internet time service. The secondary server is selected from a different geographic region than the primary server. Requirement: The service provider synchronizes the system clocks of network computers that run operating systems other than Windows to the Windows Server Domain Controller emulator or to the same time source for that server. Guidance: Synchronization of system clocks improves the accuracy of log analysis. |


### SC-47 Alternate Communications Paths

Establish [Assignment: organization-defined alternate communications paths] for system operations organizational command and control.


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for Google Cloud common infrastructure and FIPS 140-validated cryptographic backends. Where configured in the system's Terraform blueprints, the system provisions VPC Service Controls security perimeters, Cloud KMS CMEK encryption (AES-256), TLS 1.2+ transport security, Private Google Access, Cloud NAT, Cloud DNS, and regional Cloud Armor WAF protection. |


## 2.19 System and Information Integrity


### SI-1 Policy and Procedures


a. Develop, document, and disseminate to [Assignment: organization-defined personnel or roles]:

  1. [Selection (one or more): Organization-level; Mission/business process-level; System-level] system and information integrity policy that:

    (a) Addresses purpose, scope, roles, responsibilities, management commitment, coordination among organizational entities, and compliance; and

    (b) Is consistent with applicable laws, executive orders, directives, regulations, policies, standards, and guidelines; and

  2. Procedures to facilitate the implementation of the system and information integrity policy and the associated system and information integrity controls;


b. Designate an [Assignment: organization-defined official] to manage the development, documentation, and dissemination of the system and information integrity policy and procedures; and


c. Review and update the current system and information integrity:

  1. Policy [Assignment: organization-defined frequency — FedRAMP High: at least annually] and following [Assignment: organization-defined events — FedRAMP High: significant changes]; and

  2. Procedures [Assignment: organization-defined frequency — FedRAMP High: at least annually] and following [Assignment: organization-defined events].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for hypervisor memory isolation, host malware protection, and automated binary integrity verification. Where configured in the system boundary, the system enforces DoD-accredited vulnerability scanning (such as ACAS and CI/CD pipeline scanners), threat detection through {{ THREAT_DETECTION_ENGINE }}, and immutable image rebuilds or configuration-managed OS patching within the accredited {{ DOD_IMPACT_LABEL }} boundary. |
| **FedRAMP High Parameter Values**: `si-01_odp.05` (frequency): at least annually; `si-01_odp.07` (frequency): at least annually; `si-01_odp.08` (events): significant changes |


### SI-2 Flaw Remediation


a. Identify, report, and correct system flaws;


b. Test software and firmware updates related to flaw remediation for effectiveness and potential side effects before installation;


c. Install security-relevant software and firmware updates within [Assignment: organization-defined time period — FedRAMP High: within thirty (30) days of release of updates] of the release of the updates; and


d. Incorporate flaw remediation into the organizational configuration management process.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for hypervisor memory isolation, host malware protection, and automated binary integrity verification. Where configured in the system boundary, the system enforces DoD-accredited vulnerability scanning (such as ACAS and CI/CD pipeline scanners), threat detection through {{ THREAT_DETECTION_ENGINE }}, and immutable image rebuilds or configuration-managed OS patching within the accredited {{ DOD_IMPACT_LABEL }} boundary. |
| **FedRAMP High Parameter Values**: `si-02_odp` (time period): within thirty (30) days of release of updates |


### SI-2(2) Flaw Remediation | Automated Flaw Remediation Status

Determine if system components have applicable security-relevant software and firmware updates installed using [Assignment: organization-defined automated mechanisms] [Assignment: organization-defined frequency — FedRAMP High: at least monthly].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for hypervisor memory isolation, host malware protection, and automated binary integrity verification. Where configured in the system boundary, the system enforces DoD-accredited vulnerability scanning (such as ACAS and CI/CD pipeline scanners), threat detection through {{ THREAT_DETECTION_ENGINE }}, and immutable image rebuilds or configuration-managed OS patching within the accredited {{ DOD_IMPACT_LABEL }} boundary. |
| **FedRAMP High Parameter Values**: `si-02.02_odp.02` (frequency): at least monthly |


### SI-2(3) Flaw Remediation | Time to Remediate Flaws and Benchmarks for Corrective Actions


(a) Measure the time between flaw identification and flaw remediation; and


(b) Establish the following benchmarks for taking corrective actions: [Assignment: organization-defined benchmarks].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for hypervisor memory isolation, host malware protection, and automated binary integrity verification. Where configured in the system boundary, the system enforces DoD-accredited vulnerability scanning (such as ACAS and CI/CD pipeline scanners), threat detection through {{ THREAT_DETECTION_ENGINE }}, and immutable image rebuilds or configuration-managed OS patching within the accredited {{ DOD_IMPACT_LABEL }} boundary. |


### SI-2(4) Flaw Remediation | Automated Patch Management Tools

Employ automated patch management tools to facilitate flaw remediation to the following system components: [Assignment: organization-defined system components].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for hypervisor memory isolation, host malware protection, and automated binary integrity verification. Where configured in the system boundary, the system enforces DoD-accredited vulnerability scanning (such as ACAS and CI/CD pipeline scanners), threat detection through {{ THREAT_DETECTION_ENGINE }}, and immutable image rebuilds or configuration-managed OS patching within the accredited {{ DOD_IMPACT_LABEL }} boundary. |


### SI-2(6) Flaw Remediation | Removal of Previous Versions of Software and Firmware

Remove previous versions of [Assignment: organization-defined software and firmware components] after updated versions have been installed.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for hypervisor memory isolation, host malware protection, and automated binary integrity verification. Where configured in the system boundary, the system enforces DoD-accredited vulnerability scanning (such as ACAS and CI/CD pipeline scanners), threat detection through {{ THREAT_DETECTION_ENGINE }}, and immutable image rebuilds or configuration-managed OS patching within the accredited {{ DOD_IMPACT_LABEL }} boundary. |


### SI-3 Malicious Code Protection


a. Implement [Selection (one or more): signature based; non-signature based] malicious code protection mechanisms at system entry and exit points to detect and eradicate malicious code;


b. Automatically update malicious code protection mechanisms as new releases are available in accordance with organizational configuration management policy and procedures;


c. Configure malicious code protection mechanisms to:

  1. Perform periodic scans of the system [Assignment: organization-defined frequency — FedRAMP High: at least weekly] and real-time scans of files from external sources at [Selection (one or more): endpoint; network entry and exit points — FedRAMP High: to include endpoints and network entry and exit points] as the files are downloaded, opened, or executed in accordance with organizational policy; and

  2. [Selection (one or more): block malicious code; quarantine malicious code; take [Assignment: organization-defined action — FedRAMP High: to include blocking and quarantining malicious code]]; and send alert to [Assignment: organization-defined personnel or roles — FedRAMP High: administrator or defined security personnel near-realtime] in response to malicious code detection; and


d. Address the receipt of false positives during malicious code detection and eradication and the resulting potential impact on the availability of the system.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for hypervisor memory isolation, host malware protection, and automated binary integrity verification. Where configured in the system boundary, the system enforces DoD-accredited vulnerability scanning (such as ACAS and CI/CD pipeline scanners), threat detection through {{ THREAT_DETECTION_ENGINE }}, and immutable image rebuilds or configuration-managed OS patching within the accredited {{ DOD_IMPACT_LABEL }} boundary. |
| **FedRAMP High Parameter Values**: `si-03_odp.01`: signature based and non-signature based; `si-03_odp.02` (frequency): at least weekly; `si-03_odp.03`: to include endpoints and network entry and exit points; `si-03_odp.04`: to include blocking and quarantining malicious code; `si-03_odp.06` (personnel or roles): administrator or defined security personnel near-realtime |


### SI-3(10) Malicious Code Protection | Malicious Code Analysis


(a) Employ the following tools and techniques to analyze the characteristics and behavior of malicious code: [Assignment: organization-defined tools and techniques]; and


(b) Incorporate the results from malicious code analysis into organizational incident response and flaw remediation processes.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for hypervisor memory isolation, host malware protection, and automated binary integrity verification. Where configured in the system boundary, the system enforces DoD-accredited vulnerability scanning (such as ACAS and CI/CD pipeline scanners), threat detection through {{ THREAT_DETECTION_ENGINE }}, and immutable image rebuilds or configuration-managed OS patching within the accredited {{ DOD_IMPACT_LABEL }} boundary. |


### SI-4 System Monitoring


a. Monitor the system to detect:

  1. Attacks and indicators of potential attacks in accordance with the following monitoring objectives: [Assignment: organization-defined monitoring objectives]; and

  2. Unauthorized local, network, and remote connections;


b. Identify unauthorized use of the system through the following techniques and methods: [Assignment: organization-defined techniques and methods];


c. Invoke internal monitoring capabilities or deploy monitoring devices:

  1. Strategically within the system to collect organization-determined essential information; and

  2. At ad hoc locations within the system to track specific types of transactions of interest to the organization;


d. Analyze detected events and anomalies;


e. Adjust the level of system monitoring activity when there is a change in risk to organizational operations and assets, individuals, other organizations, or the Nation;


f. Obtain legal opinion regarding system monitoring activities; and


g. Provide [Assignment: organization-defined system monitoring information] to [Assignment: organization-defined personnel or roles] [Selection (one or more): as needed; [Assignment: organization-defined frequency]].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for hypervisor memory isolation, host malware protection, and automated binary integrity verification. Where configured in the system boundary, the system enforces DoD-accredited vulnerability scanning (such as ACAS and CI/CD pipeline scanners), threat detection through {{ THREAT_DETECTION_ENGINE }}, and immutable image rebuilds or configuration-managed OS patching within the accredited {{ DOD_IMPACT_LABEL }} boundary. |
| **FedRAMP Additional Guidance**: Guidance: See US-CERT Incident Response Reporting Guidelines. |


### SI-4(1) System Monitoring | System-wide Intrusion Detection System

Connect and configure individual intrusion detection tools into a system-wide intrusion detection system.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for hypervisor memory isolation, host malware protection, and automated binary integrity verification. Where configured in the system boundary, the system enforces DoD-accredited vulnerability scanning (such as ACAS and CI/CD pipeline scanners), threat detection through {{ THREAT_DETECTION_ENGINE }}, and immutable image rebuilds or configuration-managed OS patching within the accredited {{ DOD_IMPACT_LABEL }} boundary. |


### SI-4(2) System Monitoring | Automated Tools and Mechanisms for Real-time Analysis

Employ automated tools and mechanisms to support near real-time analysis of events.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for hypervisor memory isolation, host malware protection, and automated binary integrity verification. Where configured in the system boundary, the system enforces DoD-accredited vulnerability scanning (such as ACAS and CI/CD pipeline scanners), threat detection through {{ THREAT_DETECTION_ENGINE }}, and immutable image rebuilds or configuration-managed OS patching within the accredited {{ DOD_IMPACT_LABEL }} boundary. |


### SI-4(4) System Monitoring | Inbound and Outbound Communications Traffic


(a) Determine criteria for unusual or unauthorized activities or conditions for inbound and outbound communications traffic;


(b) Monitor inbound and outbound communications traffic [Assignment: organization-defined frequency — FedRAMP High: continuously] for [Assignment: organization-defined unusual or unauthorized activities or conditions].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for hypervisor memory isolation, host malware protection, and automated binary integrity verification. Where configured in the system boundary, the system enforces DoD-accredited vulnerability scanning (such as ACAS and CI/CD pipeline scanners), threat detection through {{ THREAT_DETECTION_ENGINE }}, and immutable image rebuilds or configuration-managed OS patching within the accredited {{ DOD_IMPACT_LABEL }} boundary. |
| **FedRAMP High Parameter Values**: `si-04.04_odp.01` (frequency): continuously; `si-04.04_odp.03` (frequency): continuously |


### SI-4(5) System Monitoring | System-generated Alerts

Alert [Assignment: organization-defined personnel or roles] when the following system-generated indications of compromise or potential compromise occur: [Assignment: organization-defined compromise indicators].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for hypervisor memory isolation, host malware protection, and automated binary integrity verification. Where configured in the system boundary, the system enforces DoD-accredited vulnerability scanning (such as ACAS and CI/CD pipeline scanners), threat detection through {{ THREAT_DETECTION_ENGINE }}, and immutable image rebuilds or configuration-managed OS patching within the accredited {{ DOD_IMPACT_LABEL }} boundary. |
| **FedRAMP Additional Guidance**: Guidance: In accordance with the incident response plan. |


### SI-4(10) System Monitoring | Visibility of Encrypted Communications

Make provisions so that [Assignment: organization-defined encrypted communications traffic] is visible to [Assignment: organization-defined system monitoring tools and mechanisms].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for hypervisor memory isolation, host malware protection, and automated binary integrity verification. Where configured in the system boundary, the system enforces DoD-accredited vulnerability scanning (such as ACAS and CI/CD pipeline scanners), threat detection through {{ THREAT_DETECTION_ENGINE }}, and immutable image rebuilds or configuration-managed OS patching within the accredited {{ DOD_IMPACT_LABEL }} boundary. |
| **FedRAMP Additional Guidance**: Requirement: The service provider must support Agency requirements to comply with M-21-31 (https://www.whitehouse.gov/wp-content/uploads/2021/08/M-21-31-Improving-the-Federal-Governments-Investigative-and-Remediation-Capabilities-Related-to-Cybersecurity-Incidents.pdf) and M-22-09 (https://www.whitehouse.gov/wp-content/uploads/2022/01/M-22-09.pdf). |


### SI-4(11) System Monitoring | Analyze Communications Traffic Anomalies

Analyze outbound communications traffic at the external interfaces to the system and selected [Assignment: organization-defined interior points within the system] to discover anomalies.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for hypervisor memory isolation, host malware protection, and automated binary integrity verification. Where configured in the system boundary, the system enforces DoD-accredited vulnerability scanning (such as ACAS and CI/CD pipeline scanners), threat detection through {{ THREAT_DETECTION_ENGINE }}, and immutable image rebuilds or configuration-managed OS patching within the accredited {{ DOD_IMPACT_LABEL }} boundary. |


### SI-4(12) System Monitoring | Automated Organization-generated Alerts

Alert [Assignment: organization-defined personnel or roles] using [Assignment: organization-defined automated mechanisms] when the following indications of inappropriate or unusual activities with security or privacy implications occur: [Assignment: organization-defined activities that trigger alerts].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for hypervisor memory isolation, host malware protection, and automated binary integrity verification. Where configured in the system boundary, the system enforces DoD-accredited vulnerability scanning (such as ACAS and CI/CD pipeline scanners), threat detection through {{ THREAT_DETECTION_ENGINE }}, and immutable image rebuilds or configuration-managed OS patching within the accredited {{ DOD_IMPACT_LABEL }} boundary. |


### SI-4(14) System Monitoring | Wireless Intrusion Detection

Employ a wireless intrusion detection system to identify rogue wireless devices and to detect attack attempts and potential compromises or breaches to the system.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for hypervisor memory isolation, host malware protection, and automated binary integrity verification. Where configured in the system boundary, the system enforces DoD-accredited vulnerability scanning (such as ACAS and CI/CD pipeline scanners), threat detection through {{ THREAT_DETECTION_ENGINE }}, and immutable image rebuilds or configuration-managed OS patching within the accredited {{ DOD_IMPACT_LABEL }} boundary. |


### SI-4(15) System Monitoring | Wireless to Wireline Communications

Employ an intrusion detection system to monitor wireless communications traffic as the traffic passes from wireless to wireline networks.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for hypervisor memory isolation, host malware protection, and automated binary integrity verification. Where configured in the system boundary, the system enforces DoD-accredited vulnerability scanning (such as ACAS and CI/CD pipeline scanners), threat detection through {{ THREAT_DETECTION_ENGINE }}, and immutable image rebuilds or configuration-managed OS patching within the accredited {{ DOD_IMPACT_LABEL }} boundary. |


### SI-4(16) System Monitoring | Correlate Monitoring Information

Correlate information from monitoring tools and mechanisms employed throughout the system.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for hypervisor memory isolation, host malware protection, and automated binary integrity verification. Where configured in the system boundary, the system enforces DoD-accredited vulnerability scanning (such as ACAS and CI/CD pipeline scanners), threat detection through {{ THREAT_DETECTION_ENGINE }}, and immutable image rebuilds or configuration-managed OS patching within the accredited {{ DOD_IMPACT_LABEL }} boundary. |


### SI-4(18) System Monitoring | Analyze Traffic and Covert Exfiltration

Analyze outbound communications traffic at external interfaces to the system and at the following interior points to detect covert exfiltration of information: [Assignment: organization-defined interior points within the system].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for hypervisor memory isolation, host malware protection, and binary integrity verification in the underlying Google infrastructure. Where configured in the system boundary, the system uses container image vulnerability scanning, threat detection through {{ THREAT_DETECTION_ENGINE }}, and automated OS image rebuilds or configuration-managed patching within the accredited FedRAMP High boundary. |


### SI-4(19) System Monitoring | Risk for Individuals

Implement [Assignment: organization-defined additional monitoring] of individuals who have been identified by [Assignment: organization-defined sources] as posing an increased level of risk.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for hypervisor memory isolation, host malware protection, and automated binary integrity verification. Where configured in the system boundary, the system enforces DoD-accredited vulnerability scanning (such as ACAS and CI/CD pipeline scanners), threat detection through {{ THREAT_DETECTION_ENGINE }}, and immutable image rebuilds or configuration-managed OS patching within the accredited {{ DOD_IMPACT_LABEL }} boundary. |


### SI-4(20) System Monitoring | Privileged Users

Implement the following additional monitoring of privileged users: [Assignment: organization-defined additional monitoring].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for hypervisor memory isolation, host malware protection, and automated binary integrity verification. Where configured in the system boundary, the system enforces DoD-accredited vulnerability scanning (such as ACAS and CI/CD pipeline scanners), threat detection through {{ THREAT_DETECTION_ENGINE }}, and immutable image rebuilds or configuration-managed OS patching within the accredited {{ DOD_IMPACT_LABEL }} boundary. |


### SI-4(22) System Monitoring | Unauthorized Network Services


(a) Detect network services that have not been authorized or approved by [Assignment: organization-defined authorization or approval processes]; and

(b) [Selection (one or more): Audit; Alert [Assignment: organization-defined personnel or roles]] when detected.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for hypervisor memory isolation, host malware protection, and automated binary integrity verification. Where configured in the system boundary, the system enforces DoD-accredited vulnerability scanning (such as ACAS and CI/CD pipeline scanners), threat detection through {{ THREAT_DETECTION_ENGINE }}, and immutable image rebuilds or configuration-managed OS patching within the accredited {{ DOD_IMPACT_LABEL }} boundary. |


### SI-4(23) System Monitoring | Host-based Devices

Implement the following host-based monitoring mechanisms at [Assignment: organization-defined system components]: [Assignment: organization-defined host-based monitoring mechanisms].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for hypervisor memory isolation, host malware protection, and automated binary integrity verification. Where configured in the system boundary, the system enforces DoD-accredited vulnerability scanning (such as ACAS and CI/CD pipeline scanners), threat detection through {{ THREAT_DETECTION_ENGINE }}, and immutable image rebuilds or configuration-managed OS patching within the accredited {{ DOD_IMPACT_LABEL }} boundary. |


### SI-4(24) System Monitoring | Indicators of Compromise

Discover, collect, and distribute to [Assignment: organization-defined personnel or roles], indicators of compromise provided by [Assignment: organization-defined sources].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for hypervisor memory isolation, host malware protection, and automated binary integrity verification. Where configured in the system boundary, the system enforces DoD-accredited vulnerability scanning (such as ACAS and CI/CD pipeline scanners), threat detection through {{ THREAT_DETECTION_ENGINE }}, and immutable image rebuilds or configuration-managed OS patching within the accredited {{ DOD_IMPACT_LABEL }} boundary. |


### SI-4(25) System Monitoring | Optimize Network Traffic Analysis

Provide visibility into network traffic at external and key internal system interfaces to optimize the effectiveness of monitoring devices.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for hypervisor memory isolation, host malware protection, and automated binary integrity verification. Where configured in the system boundary, the system enforces DoD-accredited vulnerability scanning (such as ACAS and CI/CD pipeline scanners), threat detection through {{ THREAT_DETECTION_ENGINE }}, and immutable image rebuilds or configuration-managed OS patching within the accredited {{ DOD_IMPACT_LABEL }} boundary. |


### SI-5 Security Alerts, Advisories, and Directives


a. Receive system security alerts, advisories, and directives from [Assignment: organization-defined external organizations — FedRAMP High: to include US-CERT and Cybersecurity and Infrastructure Security Agency (CISA) Directives] on an ongoing basis;


b. Generate internal security alerts, advisories, and directives as deemed necessary;


c. Disseminate security alerts, advisories, and directives to: [Selection (one or more): [Assignment: organization-defined personnel or roles]; [Assignment: organization-defined elements within the organization]; [Assignment: organization-defined external organizations]]; and


d. Implement security directives in accordance with established time frames, or notify the issuing organization of the degree of noncompliance.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for hypervisor memory isolation, host malware protection, and automated binary integrity verification. Where configured in the system boundary, the system enforces DoD-accredited vulnerability scanning (such as ACAS and CI/CD pipeline scanners), threat detection through {{ THREAT_DETECTION_ENGINE }}, and immutable image rebuilds or configuration-managed OS patching within the accredited {{ DOD_IMPACT_LABEL }} boundary. |
| **FedRAMP High Parameter Values**: `si-05_odp.01` (external organizations): to include US-CERT and Cybersecurity and Infrastructure Security Agency (CISA) Directives; `si-05_odp.02`: to include system security personnel and administrators with configuration/patch-management responsibilities |


### SI-5(1) Security Alerts, Advisories, and Directives | Automated Alerts and Advisories

Broadcast security alert and advisory information throughout the organization using [Assignment: organization-defined automated mechanisms].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for hypervisor memory isolation, host malware protection, and automated binary integrity verification. Where configured in the system boundary, the system enforces DoD-accredited vulnerability scanning (such as ACAS and CI/CD pipeline scanners), threat detection through {{ THREAT_DETECTION_ENGINE }}, and immutable image rebuilds or configuration-managed OS patching within the accredited {{ DOD_IMPACT_LABEL }} boundary. |


### SI-6 Security and Privacy Function Verification


a. Verify the correct operation of [Assignment: organization-defined security and privacy functions];


b. Perform the verification of the functions specified in SI-6a [Selection (one or more): [Assignment: organization-defined system transitional states — FedRAMP High: to include upon system startup and/or restart]; upon command by user with appropriate privilege; [Assignment: organization-defined frequency — FedRAMP High: at least monthly]];


c. Alert [Assignment: organization-defined personnel or roles — FedRAMP High: to include system administrators and security personnel] to failed security and privacy verification tests; and

d. [Selection (one or more): Shut the system down; Restart the system; [Assignment: organization-defined alternative action(s)]] when anomalies are discovered.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for hypervisor memory isolation, host malware protection, and automated binary integrity verification. Where configured in the system boundary, the system enforces DoD-accredited vulnerability scanning (such as ACAS and CI/CD pipeline scanners), threat detection through {{ THREAT_DETECTION_ENGINE }}, and immutable image rebuilds or configuration-managed OS patching within the accredited {{ DOD_IMPACT_LABEL }} boundary. |
| **FedRAMP High Parameter Values**: `si-06_odp.04` (system transitional states): to include upon system startup and/or restart; `si-06_odp.05` (frequency): at least monthly; `si-06_odp.06` (personnel or roles): to include system administrators and security personnel |


### SI-6(3) Security and Privacy Function Verification | Report Verification Results

Report the results of security and privacy function verification to [Assignment: organization-defined personnel or roles].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for hypervisor memory isolation, host malware protection, and automated binary integrity verification. Where configured in the system boundary, the system enforces DoD-accredited vulnerability scanning (such as ACAS and CI/CD pipeline scanners), threat detection through {{ THREAT_DETECTION_ENGINE }}, and immutable image rebuilds or configuration-managed OS patching within the accredited {{ DOD_IMPACT_LABEL }} boundary. |


### SI-7 Software, Firmware, and Information Integrity


a. Employ integrity verification tools to detect unauthorized changes to the following software, firmware, and information: [Assignment: organization-defined software, firmware, and information]; and


b. Take the following actions when unauthorized changes to the software, firmware, and information are detected: [Assignment: organization-defined actions].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for hypervisor memory isolation, host malware protection, and automated binary integrity verification. Where configured in the system boundary, the system enforces DoD-accredited vulnerability scanning (such as ACAS and CI/CD pipeline scanners), threat detection through {{ THREAT_DETECTION_ENGINE }}, and immutable image rebuilds or configuration-managed OS patching within the accredited {{ DOD_IMPACT_LABEL }} boundary. |


### SI-7(1) Software, Firmware, and Information Integrity | Integrity Checks

Perform an integrity check of [Assignment: organization-defined software, firmware, and information] [Selection (one or more): at startup; at [Assignment: organization-defined transitional states or security-relevant events — FedRAMP High: selection to include security relevant event]; [Assignment: organization-defined frequency — FedRAMP High: at least monthly]].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for hypervisor memory isolation, host malware protection, and automated binary integrity verification. Where configured in the system boundary, the system enforces DoD-accredited vulnerability scanning (such as ACAS and CI/CD pipeline scanners), threat detection through {{ THREAT_DETECTION_ENGINE }}, and immutable image rebuilds or configuration-managed OS patching within the accredited {{ DOD_IMPACT_LABEL }} boundary. |
| **FedRAMP High Parameter Values**: `si-07.01_odp.03` (transitional states or security-relevant events): selection to include security relevant event; `si-07.01_odp.04` (frequency): at least monthly; `si-07.01_odp.07` (transitional states or security-relevant events): selection to include security relevant event; `si-07.01_odp.08` (frequency): at least monthly; `si-07.01_odp.11` (transitional states or security-relevant events): selection to include security relevant event; `si-07.01_odp.12` (frequency): at least monthly |


### SI-7(2) Software, Firmware, and Information Integrity | Automated Notifications of Integrity Violations

Employ automated tools that provide notification to [Assignment: organization-defined personnel or roles — FedRAMP High: to include the ISSO and/or similar role within the organization] upon discovering discrepancies during integrity verification.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for hypervisor memory isolation, host malware protection, and automated binary integrity verification. Where configured in the system boundary, the system enforces DoD-accredited vulnerability scanning (such as ACAS and CI/CD pipeline scanners), threat detection through {{ THREAT_DETECTION_ENGINE }}, and immutable image rebuilds or configuration-managed OS patching within the accredited {{ DOD_IMPACT_LABEL }} boundary. |
| **FedRAMP High Parameter Values**: `si-07.02_odp` (personnel or roles): to include the ISSO and/or similar role within the organization |


### SI-7(5) Software, Firmware, and Information Integrity | Automated Response to Integrity Violations

Automatically [Selection (one or more): shut the system down; restart the system; implement [Assignment: organization-defined controls]] when integrity violations are discovered.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for hypervisor memory isolation, host malware protection, and automated binary integrity verification. Where configured in the system boundary, the system enforces DoD-accredited vulnerability scanning (such as ACAS and CI/CD pipeline scanners), threat detection through {{ THREAT_DETECTION_ENGINE }}, and immutable image rebuilds or configuration-managed OS patching within the accredited {{ DOD_IMPACT_LABEL }} boundary. |


### SI-7(7) Software, Firmware, and Information Integrity | Integration of Detection and Response

Incorporate the detection of the following unauthorized changes into the organizational incident response capability: [Assignment: organization-defined security-relevant changes to the system].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for hypervisor memory isolation, host malware protection, and automated binary integrity verification. Where configured in the system boundary, the system enforces DoD-accredited vulnerability scanning (such as ACAS and CI/CD pipeline scanners), threat detection through {{ THREAT_DETECTION_ENGINE }}, and immutable image rebuilds or configuration-managed OS patching within the accredited {{ DOD_IMPACT_LABEL }} boundary. |


### SI-7(8) Software, Firmware, and Information Integrity | Auditing Capability for Significant Events

Upon detection of a potential integrity violation, provide the capability to audit the event and initiate the following actions: [Selection (one or more): generate an audit record; alert current user; alert [Assignment: organization-defined personnel or roles]; [Assignment: organization-defined other actions]].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for hypervisor memory isolation, host malware protection, and automated binary integrity verification. Where configured in the system boundary, the system enforces DoD-accredited vulnerability scanning (such as ACAS and CI/CD pipeline scanners), threat detection through {{ THREAT_DETECTION_ENGINE }}, and immutable image rebuilds or configuration-managed OS patching within the accredited {{ DOD_IMPACT_LABEL }} boundary. |


### SI-7(9) Software, Firmware, and Information Integrity | Verify Boot Process

Verify the integrity of the boot process of the following system components: [Assignment: organization-defined system components].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for hypervisor memory isolation, host malware protection, and automated binary integrity verification. Where configured in the system boundary, the system enforces DoD-accredited vulnerability scanning (such as ACAS and CI/CD pipeline scanners), threat detection through {{ THREAT_DETECTION_ENGINE }}, and immutable image rebuilds or configuration-managed OS patching within the accredited {{ DOD_IMPACT_LABEL }} boundary. |


### SI-7(10) Software, Firmware, and Information Integrity | Protection of Boot Firmware

Implement the following mechanisms to protect the integrity of boot firmware in [Assignment: organization-defined system components]: [Assignment: organization-defined mechanisms].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for hypervisor memory isolation, host malware protection, and automated binary integrity verification. Where configured in the system boundary, the system enforces DoD-accredited vulnerability scanning (such as ACAS and CI/CD pipeline scanners), threat detection through {{ THREAT_DETECTION_ENGINE }}, and immutable image rebuilds or configuration-managed OS patching within the accredited {{ DOD_IMPACT_LABEL }} boundary. |


### SI-7(15) Software, Firmware, and Information Integrity | Code Authentication

Implement cryptographic mechanisms to authenticate the following software or firmware components prior to installation: [Assignment: organization-defined software or firmware components — FedRAMP High: to include all software and firmware inside the boundary].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for hypervisor memory isolation, host malware protection, and automated binary integrity verification. Where configured in the system boundary, the system enforces DoD-accredited vulnerability scanning (such as ACAS and CI/CD pipeline scanners), threat detection through {{ THREAT_DETECTION_ENGINE }}, and immutable image rebuilds or configuration-managed OS patching within the accredited {{ DOD_IMPACT_LABEL }} boundary. |
| **FedRAMP High Parameter Values**: `si-07.15_odp` (software or firmware components): to include all software and firmware inside the boundary |


### SI-7(17) Software, Firmware, and Information Integrity | Runtime Application Self-protection

Implement [Assignment: organization-defined controls] for application self-protection at runtime.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for hypervisor memory isolation, host malware protection, and automated binary integrity verification. Where configured in the system boundary, the system enforces DoD-accredited vulnerability scanning (such as ACAS and CI/CD pipeline scanners), threat detection through {{ THREAT_DETECTION_ENGINE }}, and immutable image rebuilds or configuration-managed OS patching within the accredited {{ DOD_IMPACT_LABEL }} boundary. |


### SI-8 Spam Protection


a. Employ spam protection mechanisms at system entry and exit points to detect and act on unsolicited messages; and


b. Update spam protection mechanisms when new releases are available in accordance with organizational configuration management policy and procedures.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for hypervisor memory isolation, host malware protection, and automated binary integrity verification. Where configured in the system boundary, the system enforces DoD-accredited vulnerability scanning (such as ACAS and CI/CD pipeline scanners), threat detection through {{ THREAT_DETECTION_ENGINE }}, and immutable image rebuilds or configuration-managed OS patching within the accredited {{ DOD_IMPACT_LABEL }} boundary. |
| **FedRAMP Additional Guidance**: Guidance: When CSO sends email on behalf of the government as part of the business offering, Control Description should include implementation of Domain-based Message Authentication, Reporting \& Conformance (DMARC) on the sending domain for outgoing messages as described in DHS Binding Operational Directive (BOD) 18-01. https://cyber.dhs.gov/bod/18-01/ Guidance: CSPs should confirm DMARC configuration (where appropriate) to ensure that policy=reject and the rua parameter includes reports@dmarc.cyber.dhs.gov. DMARC compliance should be documented in the SI-08 control implementation solution description, and list the FROM: domain(s) that will be seen by email recipients. |


### SI-8(2) Spam Protection | Automatic Updates

Automatically update spam protection mechanisms [Assignment: organization-defined frequency].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for hypervisor memory isolation, host malware protection, and automated binary integrity verification. Where configured in the system boundary, the system enforces DoD-accredited vulnerability scanning (such as ACAS and CI/CD pipeline scanners), threat detection through {{ THREAT_DETECTION_ENGINE }}, and immutable image rebuilds or configuration-managed OS patching within the accredited {{ DOD_IMPACT_LABEL }} boundary. |


### SI-10 Information Input Validation

Check the validity of the following information inputs: [Assignment: organization-defined information inputs to the system].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for the Google-managed infrastructure that hosts the system. [CONFIG_REQUIRED: Confirm in the Google Cloud {{ DOD_IMPACT_LABEL }} / {{ BASE_FEDRAMP_LABEL }} customer responsibility matrix whether SI-10 is inherited or shared; document customer-configured controls and verify Implementation Status] |
| **FedRAMP Additional Guidance**: Requirement: Validate all information inputs and document any exceptions |


### SI-10(3) Information Input Validation | Predictable Behavior

Verify that the system behaves in a predictable and documented manner when invalid inputs are received.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for hypervisor memory isolation, host malware protection, and automated binary integrity verification. Where configured in the system boundary, the system enforces DoD-accredited vulnerability scanning (such as ACAS and CI/CD pipeline scanners), threat detection through {{ THREAT_DETECTION_ENGINE }}, and immutable image rebuilds or configuration-managed OS patching within the accredited {{ DOD_IMPACT_LABEL }} boundary. |


### SI-10(5) Information Input Validation | Restrict Inputs to Trusted Sources and Approved Formats

Restrict the use of information inputs to [Assignment: organization-defined trusted sources] and/or [Assignment: organization-defined formats].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for hypervisor memory isolation, host malware protection, and automated binary integrity verification. Where configured in the system boundary, the system enforces DoD-accredited vulnerability scanning (such as ACAS and CI/CD pipeline scanners), threat detection through {{ THREAT_DETECTION_ENGINE }}, and immutable image rebuilds or configuration-managed OS patching within the accredited {{ DOD_IMPACT_LABEL }} boundary. |


### SI-10(6) Information Input Validation | Injection Prevention

Prevent untrusted data injections.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for hypervisor memory isolation, host malware protection, and automated binary integrity verification. Where configured in the system boundary, the system enforces DoD-accredited vulnerability scanning (such as ACAS and CI/CD pipeline scanners), threat detection through {{ THREAT_DETECTION_ENGINE }}, and immutable image rebuilds or configuration-managed OS patching within the accredited {{ DOD_IMPACT_LABEL }} boundary. |


### SI-11 Error Handling


a. Generate error messages that provide information necessary for corrective actions without revealing information that could be exploited; and


b. Reveal error messages only to [Assignment: organization-defined personnel or roles — FedRAMP High: to include the ISSO and/or similar role within the organization].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for the Google-managed infrastructure that hosts the system. [CONFIG_REQUIRED: Confirm in the Google Cloud {{ DOD_IMPACT_LABEL }} / {{ BASE_FEDRAMP_LABEL }} customer responsibility matrix whether SI-11 is inherited or shared; document customer-configured controls and verify Implementation Status] |
| **FedRAMP High Parameter Values**: `si-11_odp` (personnel or roles): to include the ISSO and/or similar role within the organization |


### SI-12 Information Management and Retention

Manage and retain information within the system and information output from the system in accordance with applicable laws, executive orders, directives, regulations, policies, standards, guidelines and operational requirements.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for hypervisor memory isolation, host malware protection, and automated binary integrity verification. Where configured in the system boundary, the system enforces DoD-accredited vulnerability scanning (such as ACAS and CI/CD pipeline scanners), threat detection through {{ THREAT_DETECTION_ENGINE }}, and immutable image rebuilds or configuration-managed OS patching within the accredited {{ DOD_IMPACT_LABEL }} boundary. |


### SI-12(3) Information Management and Retention | Information Disposal

Use the following techniques to dispose of, destroy, or erase information following the retention period: [Assignment: organization-defined techniques].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for hypervisor memory isolation, host malware protection, and automated binary integrity verification. Where configured in the system boundary, the system enforces DoD-accredited vulnerability scanning (such as ACAS and CI/CD pipeline scanners), threat detection through {{ THREAT_DETECTION_ENGINE }}, and immutable image rebuilds or configuration-managed OS patching within the accredited {{ DOD_IMPACT_LABEL }} boundary. |


### SI-15 Information Output Filtering

Validate information output from the following software programs and/or applications to ensure that the information is consistent with the expected content: [Assignment: organization-defined software programs and/or applications].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for hypervisor memory isolation, host malware protection, and automated binary integrity verification. Where configured in the system boundary, the system enforces DoD-accredited vulnerability scanning (such as ACAS and CI/CD pipeline scanners), threat detection through {{ THREAT_DETECTION_ENGINE }}, and immutable image rebuilds or configuration-managed OS patching within the accredited {{ DOD_IMPACT_LABEL }} boundary. |


### SI-16 Memory Protection

Implement the following controls to protect the system memory from unauthorized code execution: [Assignment: organization-defined controls].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) and {{ DOD_PA_LABEL }} for the Google-managed infrastructure that hosts the system. [CONFIG_REQUIRED: Confirm in the Google Cloud {{ DOD_IMPACT_LABEL }} / {{ BASE_FEDRAMP_LABEL }} customer responsibility matrix whether SI-16 is inherited or shared; document customer-configured controls and verify Implementation Status] |


### SI-21 Information Refresh

Refresh [Assignment: organization-defined information] at [Assignment: organization-defined frequencies] or generate the information on demand and delete the information when no longer needed.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for hypervisor memory isolation, host malware protection, and automated binary integrity verification. Where configured in the system boundary, the system enforces DoD-accredited vulnerability scanning (such as ACAS and CI/CD pipeline scanners), threat detection through {{ THREAT_DETECTION_ENGINE }}, and immutable image rebuilds or configuration-managed OS patching within the accredited {{ DOD_IMPACT_LABEL }} boundary. |


## 2.20 Supply Chain Risk Management


### SR-1 Policy and Procedures


a. Develop, document, and disseminate to [Assignment: organization-defined personnel or roles — FedRAMP High: to include chief privacy and ISSO and/or similar role or designees]:

  1. [Selection (one or more): Organization-level; Mission/business process-level; System-level] supply chain risk management policy that:

    (a) Addresses purpose, scope, roles, responsibilities, management commitment, coordination among organizational entities, and compliance; and

    (b) Is consistent with applicable laws, executive orders, directives, regulations, policies, standards, and guidelines; and

  2. Procedures to facilitate the implementation of the supply chain risk management policy and the associated supply chain risk management controls;


b. Designate an [Assignment: organization-defined official] to manage the development, documentation, and dissemination of the supply chain risk management policy and procedures; and


c. Review and update the current supply chain risk management:

  1. Policy [Assignment: organization-defined frequency — FedRAMP High: at least annually] and following [Assignment: organization-defined events — FedRAMP High: significant changes]; and

  2. Procedures [Assignment: organization-defined frequency — FedRAMP High: at least annually] and following [Assignment: organization-defined events].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for hardware supply chain security, proprietary server manufacturing, and Titan security chip provenance. Where configured in the system boundary, container image digest pinning (`@sha256:`), CI/CD cryptographic signature verification, and Kubernetes admission controls ensure only verified container images run in production within the {{ DOD_IMPACT_LABEL }} boundary. |
| **FedRAMP High Parameter Values**: `sr-01_odp.01` (personnel or roles): to include chief privacy and ISSO and/or similar role or designees; `sr-01_odp.02` (personnel or roles): to include chief privacy and ISSO and/or similar role or designees; `sr-01_odp.05` (frequency): at least annually; `sr-01_odp.07` (frequency): at least annually; `sr-01_odp.08` (events): significant changes |


### SR-2 Supply Chain Risk Management Plan


a. Develop a plan for managing supply chain risks associated with the research and development, design, manufacturing, acquisition, delivery, integration, operations and maintenance, and disposal of the following systems, system components or system services: [Assignment: organization-defined systems, system components, or system services];


b. Review and update the supply chain risk management plan [Assignment: organization-defined frequency — FedRAMP High: at least annually] or as required, to address threat, organizational or environmental changes; and


c. Protect the supply chain risk management plan from unauthorized disclosure and modification.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for hardware supply chain security, proprietary server manufacturing, and Titan security chip provenance. Where configured in the system boundary, container image digest pinning (`@sha256:`), CI/CD cryptographic signature verification, and Kubernetes admission controls ensure only verified container images run in production within the {{ DOD_IMPACT_LABEL }} boundary. |
| **FedRAMP High Parameter Values**: `sr-02_odp.02` (frequency): at least annually |


### SR-2(1) Supply Chain Risk Management Plan | Establish SCRM Team

Establish a supply chain risk management team consisting of [Assignment: organization-defined personnel, roles, and responsibilities] to lead and support the following SCRM activities: [Assignment: organization-defined supply chain risk management activities].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for hardware supply chain security, proprietary server manufacturing, and Titan security chip provenance. Where configured in the system boundary, container image digest pinning (`@sha256:`), CI/CD cryptographic signature verification, and Kubernetes admission controls ensure only verified container images run in production within the {{ DOD_IMPACT_LABEL }} boundary. |


### SR-3 Supply Chain Controls and Processes


a. Establish a process or processes to identify and address weaknesses or deficiencies in the supply chain elements and processes of [Assignment: organization-defined system or system component] in coordination with [Assignment: organization-defined supply chain personnel];


b. Employ the following controls to protect against supply chain risks to the system, system component, or system service and to limit the harm or consequences from supply chain-related events: [Assignment: organization-defined supply chain controls]; and


c. Document the selected and implemented supply chain processes and controls in [Selection: security and privacy plans; supply chain risk management plan; [Assignment: organization-defined document]].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for hardware supply chain security, proprietary server manufacturing, and Titan security chip provenance. Where configured in the system boundary, container image digest pinning (`@sha256:`), CI/CD cryptographic signature verification, and Kubernetes admission controls ensure only verified container images run in production within the {{ DOD_IMPACT_LABEL }} boundary. |
| **FedRAMP Additional Guidance**: Requirement: CSO must document and maintain the supply chain custody, including replacement devices, to ensure the integrity of the devices before being introduced to the boundary. |


### SR-3(1) Supply Chain Controls and Processes | Diverse Supply Base

Employ a diverse set of sources for the following system components and services: [Assignment: organization-defined system components and services].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for hardware supply chain security, proprietary server manufacturing, and Titan security chip provenance. Where configured in the system boundary, container image digest pinning (`@sha256:`), CI/CD cryptographic signature verification, and Kubernetes admission controls ensure only verified container images run in production within the {{ DOD_IMPACT_LABEL }} boundary. |


### SR-3(2) Supply Chain Controls and Processes | Limitation of Harm

Employ the following controls to limit harm from potential adversaries identifying and targeting the organizational supply chain: [Assignment: organization-defined controls].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for hardware supply chain security, proprietary server manufacturing, and Titan security chip provenance. Where configured in the system boundary, container image digest pinning (`@sha256:`), CI/CD cryptographic signature verification, and Kubernetes admission controls ensure only verified container images run in production within the {{ DOD_IMPACT_LABEL }} boundary. |


### SR-3(3) Supply Chain Controls and Processes | Sub-tier Flow Down

Ensure that the controls included in the contracts of prime contractors are also included in the contracts of subcontractors.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for hardware supply chain security, proprietary server manufacturing, and Titan security chip provenance. Where configured in the system boundary, container image digest pinning (`@sha256:`), CI/CD cryptographic signature verification, and Kubernetes admission controls ensure only verified container images run in production within the {{ DOD_IMPACT_LABEL }} boundary. |


### SR-4 Provenance

Document, monitor, and maintain valid provenance of the following systems, system components, and associated data: [Assignment: organization-defined systems, system components, and associated data].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for hardware supply chain security, proprietary server manufacturing, and Titan security chip provenance. Where configured in the system boundary, container image digest pinning (`@sha256:`), CI/CD cryptographic signature verification, and Kubernetes admission controls ensure only verified container images run in production within the {{ DOD_IMPACT_LABEL }} boundary. |


### SR-5 Acquisition Strategies, Tools, and Methods

Employ the following acquisition strategies, contract tools, and procurement methods to protect against, identify, and mitigate supply chain risks: [Assignment: organization-defined acquisition strategies, contract tools, and procurement methods].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for hardware supply chain security, proprietary server manufacturing, and Titan security chip provenance. Where configured in the system boundary, container image digest pinning (`@sha256:`), CI/CD cryptographic signature verification, and Kubernetes admission controls ensure only verified container images run in production within the {{ DOD_IMPACT_LABEL }} boundary. |


### SR-5(1) Acquisition Strategies, Tools, and Methods | Adequate Supply

Employ the following controls to ensure an adequate supply of [Assignment: organization-defined critical system components]: [Assignment: organization-defined controls].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for hardware supply chain security, proprietary server manufacturing, and Titan security chip provenance. Where configured in the system boundary, container image digest pinning (`@sha256:`), CI/CD cryptographic signature verification, and Kubernetes admission controls ensure only verified container images run in production within the {{ DOD_IMPACT_LABEL }} boundary. |


### SR-5(2) Acquisition Strategies, Tools, and Methods | Assessments Prior to Selection, Acceptance, Modification, or Update

Assess the system, system component, or system service prior to selection, acceptance, modification, or update.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for hardware supply chain security, proprietary server manufacturing, and Titan security chip provenance. Where configured in the system boundary, container image digest pinning (`@sha256:`), CI/CD cryptographic signature verification, and Kubernetes admission controls ensure only verified container images run in production within the {{ DOD_IMPACT_LABEL }} boundary. |


### SR-6 Supplier Assessments and Reviews

Assess and review the supply chain-related risks associated with suppliers or contractors and the system, system component, or system service they provide [Assignment: organization-defined frequency — FedRAMP High: at least annually].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for hardware supply chain security, proprietary server manufacturing, and Titan security chip provenance. Where configured in the system boundary, container image digest pinning (`@sha256:`), CI/CD cryptographic signature verification, and Kubernetes admission controls ensure only verified container images run in production within the {{ DOD_IMPACT_LABEL }} boundary. |
| **FedRAMP High Parameter Values**: `sr-06_odp` (frequency): at least annually<br>**FedRAMP Additional Guidance**: Requirement: CSOs must ensure that their supply chain vendors build and test their systems in alignment with NIST SP 800-171 or a commensurate security and compliance framework. CSOs must ensure that vendors are compliant with physical facility access and logical access controls to supplied products. |


### SR-6(1) Supplier Assessments and Reviews | Testing and Analysis

Employ [Selection (one or more): organizational analysis; independent third-party analysis; organizational testing; independent third-party testing] of the following supply chain elements, processes, and actors associated with the system, system component, or system service: [Assignment: organization-defined supply chain elements, processes, and actors].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for hardware supply chain security, proprietary server manufacturing, and Titan security chip provenance. Where configured in the system boundary, container image digest pinning (`@sha256:`), CI/CD cryptographic signature verification, and Kubernetes admission controls ensure only verified container images run in production within the {{ DOD_IMPACT_LABEL }} boundary. |


### SR-7 Supply Chain Operations Security

Employ the following Operations Security (OPSEC) controls to protect supply chain-related information for the system, system component, or system service: [Assignment: organization-defined Operations Security (OPSEC) controls].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for hardware supply chain security, proprietary server manufacturing, and Titan security chip provenance. Where configured in the system boundary, container image digest pinning (`@sha256:`), CI/CD cryptographic signature verification, and Kubernetes admission controls ensure only verified container images run in production within the {{ DOD_IMPACT_LABEL }} boundary. |


### SR-8 Notification Agreements

Establish agreements and procedures with entities involved in the supply chain for the system, system component, or system service for the [Selection (one or more): notification of supply chain compromises; results of assessments or audits; [Assignment: organization-defined information — FedRAMP High: notification of supply chain compromises and results of assessment or audits]].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for hardware supply chain security, proprietary server manufacturing, and Titan security chip provenance. Where configured in the system boundary, container image digest pinning (`@sha256:`), CI/CD cryptographic signature verification, and Kubernetes admission controls ensure only verified container images run in production within the {{ DOD_IMPACT_LABEL }} boundary. |
| **FedRAMP High Parameter Values**: `sr-08_odp.01`: notification of supply chain compromises and results of assessment or audits<br>**FedRAMP Additional Guidance**: Requirement: CSOs must ensure and document how they receive notifications from their supply chain vendor of newly discovered vulnerabilities including zero-day vulnerabilities. |


### SR-9 Tamper Resistance and Detection

Implement a tamper protection program for the system, system component, or system service.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for hardware supply chain security, proprietary server manufacturing, and Titan security chip provenance. Where configured in the system boundary, container image digest pinning (`@sha256:`), CI/CD cryptographic signature verification, and Kubernetes admission controls ensure only verified container images run in production within the {{ DOD_IMPACT_LABEL }} boundary. |
| **FedRAMP Additional Guidance**: Requirement: CSOs must ensure vendors provide authenticity of software and patches supplied to the service provider including documenting the safeguards in place. |


### SR-9(1) Tamper Resistance and Detection | Multiple Stages of System Development Life Cycle

Employ anti-tamper technologies, tools, and techniques throughout the system development life cycle.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for hardware supply chain security, proprietary server manufacturing, and Titan security chip provenance. Where configured in the system boundary, container image digest pinning (`@sha256:`), CI/CD cryptographic signature verification, and Kubernetes admission controls ensure only verified container images run in production within the {{ DOD_IMPACT_LABEL }} boundary. |


### SR-10 Inspection of Systems or Components

Inspect the following systems or system components [Selection (one or more): at random; at [Assignment: organization-defined frequency], upon [Assignment: organization-defined indications of need for inspection]] to detect tampering: [Assignment: organization-defined systems or system components].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for hardware supply chain security, proprietary server manufacturing, and Titan security chip provenance. Where configured in the system boundary, container image digest pinning (`@sha256:`), CI/CD cryptographic signature verification, and Kubernetes admission controls ensure only verified container images run in production within the {{ DOD_IMPACT_LABEL }} boundary. |


### SR-11 Component Authenticity


a. Develop and implement anti-counterfeit policy and procedures that include the means to detect and prevent counterfeit components from entering the system; and


b. Report counterfeit system components to [Selection (one or more): source of counterfeit component; [Assignment: organization-defined external reporting organizations]; [Assignment: organization-defined personnel or roles]].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for hardware supply chain security, proprietary server manufacturing, and Titan security chip provenance. Where configured in the system boundary, container image digest pinning (`@sha256:`), CI/CD cryptographic signature verification, and Kubernetes admission controls ensure only verified container images run in production within the {{ DOD_IMPACT_LABEL }} boundary. |
| **FedRAMP Additional Guidance**: Requirement: CSOs must ensure that their supply chain vendors provide authenticity of software and patches and the vendor must have a plan to protect the development pipeline. |


### SR-11(1) Component Authenticity | Anti-counterfeit Training

Train [Assignment: organization-defined personnel or roles] to detect counterfeit system components (including hardware, software, and firmware).


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for hardware supply chain security, proprietary server manufacturing, and Titan security chip provenance. Where configured in the system boundary, container image digest pinning (`@sha256:`), CI/CD cryptographic signature verification, and Kubernetes admission controls ensure only verified container images run in production within the {{ DOD_IMPACT_LABEL }} boundary. |


### SR-11(2) Component Authenticity | Configuration Control for Component Service and Repair

Maintain configuration control over the following system components awaiting service or repair and serviced or repaired components awaiting return to service: [Assignment: organization-defined system components — FedRAMP High: all].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for hardware supply chain security, proprietary server manufacturing, and Titan security chip provenance. Where configured in the system boundary, container image digest pinning (`@sha256:`), CI/CD cryptographic signature verification, and Kubernetes admission controls ensure only verified container images run in production within the {{ DOD_IMPACT_LABEL }} boundary. |
| **FedRAMP High Parameter Values**: `sr-11.02_odp` (system components): all |


### SR-12 Component Disposal

Dispose of [Assignment: organization-defined data, documentation, tools, or system components] using the following techniques and methods: [Assignment: organization-defined techniques and methods].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from the Google Services {{ BASE_FEDRAMP_LABEL }} P-ATO and {{ DOD_PA_LABEL }} for hardware supply chain security, proprietary server manufacturing, and Titan security chip provenance. Where configured in the system boundary, container image digest pinning (`@sha256:`), CI/CD cryptographic signature verification, and Kubernetes admission controls ensure only verified container images run in production within the {{ DOD_IMPACT_LABEL }} boundary. |
