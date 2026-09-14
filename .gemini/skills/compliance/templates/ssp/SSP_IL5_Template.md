# System Security Plan (SSP) - { SYSTEM_NAME }
## System Impact Level: { IMPACT_LEVEL }
## Compliance Baseline: { COMPLIANCE_BASELINE }

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

### Document Change Record
| Date | Version | Author | Changes Made / Section(s) |
|---|---|---|---|
| {{ DATE }} | {{ VERSION }} | {{ ORGANIZATION }} | Initial Automated Provisioning & SSP Baseline for {{ SYSTEM_NAME }} |

> [!NOTE]
> **System Architecture & Security Control Implementation**
> This System Security Plan details technical, operational, and management controls for **{{ SYSTEM_NAME }}**.
> Technical IaC controls (GCP IAM, VPC topology, Cloud KMS CMEK, SCC, Assured Workloads) are automatically provisioned.
> Operational fields requiring manual confirmation by the RMF team are highlighted with Action Callouts.


## 1.3 System Points of Contact & Other Designated POCs

> [!IMPORTANT]
> <mark style="background-color: #fff9c4; color: #b71c1c; font-weight: bold; padding: 2px 6px; border-radius: 4px;">⚠️ RMF TEAM ACTION REQUIRED: Verify and populate organizational contact details, secondary system points of contact (POCs), technical leads, and mission representatives in this section prior to formal ATO authorization submission.</mark>

| Role / Designation | Name | Title | Organization / Office | Work Phone | Email Address |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **System Owner (SO)** | {{ SO_NAME }} | {{ SO_TITLE }} | {{ SO_ORG }} | {{ SO_PHONE }} | {{ SO_EMAIL }} |
| **ISSM** | {{ ISSM_NAME }} | {{ ISSM_TITLE }} | {{ ISSM_ORG }} | {{ ISSM_PHONE }} | {{ ISSM_EMAIL }} |
| **ISSO** | {{ ISSO_NAME }} | {{ ISSO_TITLE }} | {{ ISSO_ORG }} | {{ ISSO_PHONE }} | {{ ISSO_EMAIL }} |
| **Authorizing Official (AO)** | {{ AO_NAME }} | {{ AO_TITLE }} | {{ AO_ORG }} | {{ AO_PHONE }} | {{ AO_EMAIL }} |
| **Technical / DevSecOps Lead** | `<mark style="background-color: #fff9c4; color: #b71c1c; font-weight: bold; padding: 1px 5px; border-radius: 3px;">⚠️ RMF TEAM ACTION REQUIRED: Technical POC Name</mark>` | DevSecOps Lead Engineer | `<mark style="background-color: #fff9c4; color: #b71c1c; font-weight: bold; padding: 1px 5px; border-radius: 3px;">⚠️ RMF TEAM ACTION REQUIRED: Office Address</mark>` | `<mark style="background-color: #fff9c4; color: #b71c1c; font-weight: bold; padding: 1px 5px; border-radius: 3px;">⚠️ RMF TEAM ACTION REQUIRED: Phone</mark>` | `<mark style="background-color: #fff9c4; color: #b71c1c; font-weight: bold; padding: 1px 5px; border-radius: 3px;">⚠️ RMF TEAM ACTION REQUIRED: Email</mark>` |
| **Other Designated POC (Operations)** | `<mark style="background-color: #e0f2fe; color: #0369a1; font-weight: bold; padding: 1px 5px; border-radius: 3px;">ℹ️ OPTIONAL CONFIG: Secondary Ops Contact</mark>` | Cloud Operations Lead | `<mark style="background-color: #e0f2fe; color: #0369a1; font-weight: bold; padding: 1px 5px; border-radius: 3px;">ℹ️ OPTIONAL CONFIG: Office Address</mark>` | `<mark style="background-color: #e0f2fe; color: #0369a1; font-weight: bold; padding: 1px 5px; border-radius: 3px;">ℹ️ OPTIONAL CONFIG: Phone</mark>` | `<mark style="background-color: #e0f2fe; color: #0369a1; font-weight: bold; padding: 1px 5px; border-radius: 3px;">ℹ️ OPTIONAL CONFIG: Email</mark>` |


## 1.4 Information System Operational Status


| System Status | Details |
| --- | --- |
| **Operational** | The system is operating and in production |
| **Under Development** | The system is being designed, developed, or implemented |
| **Major Modification** | The system is undergoing a major change, development, or transition |
|  |
|  |
|  |


## 1.5 Information System Type

{{ SYSTEM_NAME }} is considered a PaaS, IaaS, SaaS information system type.


## 1.6 General System Description

{{ SYSTEM_DESCRIPTION }}


## 1.7 Types of Users & Codebase IAM Architecture

> [!IMPORTANT]
> <mark style="background-color: #fff9c4; color: #b71c1c; font-weight: bold; padding: 2px 6px; border-radius: 4px;">⚠️ RMF TEAM ACTION REQUIRED: Confirm system access roles, administrative groups, and separation of duties boundaries match operational organizational policies.</mark>

The system enforces principle of least privilege and strict separation of duties across Google Cloud organizations, folders, and application projects. Architectural security identities, administrative role groups, and cloud service accounts are dynamically extracted directly from source code and Terraform blueprints:

{{ SEPARATION_OF_DUTIES_TABLE }}


## 1.8 System Environment, Connectivity & Technical Architecture

The technical environment, connectivity mechanisms, authentication architecture, and cryptographic protection standards are dynamically discovered from the system's infrastructure blueprints and Terraform configurations:

| Architecture Domain | Discovered Technical Implementation Standard | Source Verification |
| :--- | :--- | :--- |
| **Network & Perimeter Connectivity** | {{ CONNECTIVITY }} | Cloud Interconnect, VPC Peering, and NCC topology |
| **Identity & Authentication** | {{ AUTHENTICATION_MECHANISM }} | Cloud Identity, WIF, and IAM configuration |
| **Cryptographic Protection** | {{ ENCRYPTION_STANDARD }} | Cloud KMS CMEK and FIPS 140-3 cryptographic modules |


### 1.8.1 Logical Network Subnets & IP Allocation Boundaries

The system enforces logical network segregation across dedicated virtual subnets. Discovered IP ranges and boundaries extracted from infrastructure configurations include:

{{ SUBNET_BOUNDARY_TABLE }}


### 1.8.2 Workload Containers & Application Runtime Services

Containerized workload services, container base images, and runtime execution environments authorized within the boundary include:

{{ CONTAINER_WORKLOAD_TABLE }}


# 2. Minimum Security Controls


## 2.1 Access Control


### AC-1 Policy and Procedures


1. Develop, document, and disseminate to [Assignment: organization-defined personnel or roles]:

  a. [Selection (one-or-more): organization-level; mission/business process-level; system-level] access control policy that:

    - Addresses purpose, scope, roles, responsibilities, management commitment, coordination among organizational entities, and compliance; and

    - Is consistent with applicable laws, executive orders, directives, regulations, policies, standards, and guidelines; and

  b. Procedures to facilitate the implementation of the access control policy and the associated access controls;


2. Designate an [Assignment: organization-defined official] to manage the development, documentation, and dissemination of the access control policy and procedures; and


3. Review and update the current access control:

  c. Policy [Assignment: organization-defined frequency] and following [Assignment: organization-defined events]; and

  d. Procedures [Assignment: organization-defined frequency] and following [Assignment: organization-defined events].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) identity backends and hypervisor isolation. The system platform implements automated least-privilege IAM bindings, Identity-Aware Proxy (IAP) zero-trust tunnels, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### AC-2 Account Management


1. Define and document the types of accounts allowed and specifically prohibited for use within the system;


2. Assign account managers;


3. Require [Assignment: organization-defined prerequisites and criteria] for group and role membership;


4. Specify:

  a. Authorized users of the system;

  b. Group and role membership; and

  c. Access authorizations (i.e., privileges) and [Assignment: organization-defined attributes (as required)] for each account;


5. Require approvals by [Assignment: organization-defined personnel or roles] for requests to create accounts;


6. Create, enable, modify, disable, and remove accounts in accordance with [Assignment: organization-defined policy, procedures, prerequisites, and criteria];


7. Monitor the use of accounts;


8. Notify account managers and [Assignment: organization-defined personnel or roles] within:

  d. [Assignment: organization-defined time period] when accounts are no longer required;

  e. [Assignment: organization-defined time period] when users are terminated or transferred; and

  f. [Assignment: organization-defined time period] when system usage or need-to-know changes for an individual;


9. Authorize access to the system based on:

  g. A valid access authorization;

  h. Intended system usage; and

  i. [Assignment: organization-defined attributes (as required)];


10. Review accounts for compliance with account management requirements [Assignment: organization-defined frequency];


11. Establish and implement a process for changing shared or group account authenticators (if deployed) when individuals are removed from the group; and


12. Align account management processes with personnel termination and transfer processes.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) identity backends and hypervisor isolation. The system platform implements automated least-privilege IAM bindings, Identity-Aware Proxy (IAP) zero-trust tunnels, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### AC-2(1) Account Management | Automated System Account Management

Support the management of system accounts using [Assignment: organization-defined automated mechanisms].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) identity backends and hypervisor isolation. The system platform implements automated least-privilege IAM bindings, Identity-Aware Proxy (IAP) zero-trust tunnels, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### AC-2(2) Account Management | Automated Temporary and Emergency Account Management

Automatically [Selection: remove; disable] temporary and emergency accounts after [Assignment: organization-defined time period for each type of account].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) identity backends and hypervisor isolation. The system platform implements automated least-privilege IAM bindings, Identity-Aware Proxy (IAP) zero-trust tunnels, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### AC-2(3) Account Management | Disable Accounts

Disable accounts within [Assignment: organization-defined time period] when the accounts:


1. Have expired;


2. Are no longer associated with a user or individual;


3. Are in violation of organizational policy; or


4. Have been inactive for [Assignment: organization-defined time period].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) identity backends and hypervisor isolation. The system platform implements automated least-privilege IAM bindings, Identity-Aware Proxy (IAP) zero-trust tunnels, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### AC-2(4) Account Management | Automated Audit Actions

Automatically audit account creation, modification, enabling, disabling, and removal actions.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) identity backends and hypervisor isolation. The system platform implements automated least-privilege IAM bindings, Identity-Aware Proxy (IAP) zero-trust tunnels, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### AC-2(5) Account Management | Inactivity Logout

Require that users log out when [Assignment: organization-defined time period of expected inactivity or description of when to log out].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) identity backends and hypervisor isolation. The system platform implements automated least-privilege IAM bindings, Identity-Aware Proxy (IAP) zero-trust tunnels, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### AC-2(7) Account Management | Privileged User Accounts


1. Establish and administer privileged user accounts in accordance with [Selection: a role-based access scheme; an attribute-based access scheme];


2. Monitor privileged role or attribute assignments;


3. Monitor changes to roles or attributes; and


4. Revoke access when privileged role or attribute assignments are no longer appropriate.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) identity backends and hypervisor isolation. The system platform implements automated least-privilege IAM bindings, Identity-Aware Proxy (IAP) zero-trust tunnels, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### AC-2(9) Account Management | Restrictions on Use of Shared and Group Accounts

Only permit the use of shared and group accounts that meet [Assignment: organization-defined conditions for establishing shared and group accounts]


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) identity backends and hypervisor isolation. The system platform implements automated least-privilege IAM bindings, Identity-Aware Proxy (IAP) zero-trust tunnels, VPC Service Controls perimeters, and Google Organization Policy constraints. |
| Look to admin console output. |


### AC-2(11) Account Management | Usage Conditions

Enforce [Assignment: organization-defined circumstances and/or usage conditions] for [Assignment: organization-defined system accounts].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) identity backends and hypervisor isolation. The system platform implements automated least-privilege IAM bindings, Identity-Aware Proxy (IAP) zero-trust tunnels, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### AC-2(12) Account Management | Account Monitoring for Atypical Usage


1. Monitor system accounts for [Assignment: organization-defined atypical usage]; and


2. Report atypical usage of system accounts to [Assignment: organization-defined personnel or roles].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) identity backends and hypervisor isolation. The system platform implements automated least-privilege IAM bindings, Identity-Aware Proxy (IAP) zero-trust tunnels, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### AC-2(13) Account Management | Disable Accounts for High-risk Individuals

Disable accounts of individuals within [Assignment: organization-defined time period] of discovery of [Assignment: organization-defined significant risks].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) identity backends and hypervisor isolation. The system platform implements automated least-privilege IAM bindings, Identity-Aware Proxy (IAP) zero-trust tunnels, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### AC-3 Access Enforcement

Enforce approved authorizations for logical access to information and system resources in accordance with applicable access control policies.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) identity backends and hypervisor isolation. The system platform implements automated least-privilege IAM bindings, Identity-Aware Proxy (IAP) zero-trust tunnels, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### AC-3(4) Access Enforcement | Discretionary Access Control

Enforce [Assignment: organization-defined discretionary access control policy] over the set of covered subjects and objects specified in the policy, and where the policy specifies that a subject that has been granted access to information can do one or more of the following:


1. Pass the information to any other subjects or objects;


2. Grant its privileges to other subjects;


3. Change security attributes on subjects, objects, the system, or the system’s components;


4. Choose the security attributes to be associated with newly created or revised objects; or


5. Change the rules governing access control.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) identity backends and hypervisor isolation. The system platform implements automated least-privilege IAM bindings, Identity-Aware Proxy (IAP) zero-trust tunnels, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### AC-4 Information Flow Enforcement

Enforce approved authorizations for controlling the flow of information within the system and between connected systems based on [Assignment: organization-defined information flow control policies].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) identity backends and hypervisor isolation. The system platform implements automated least-privilege IAM bindings, Identity-Aware Proxy (IAP) zero-trust tunnels, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### AC-4(4) Information Flow Enforcement | Flow Control of Encrypted Information

Prevent encrypted information from bypassing [Assignment: organization-defined information flow control mechanisms] by [Selection (one or more): decrypting the information; blocking the flow of the encrypted information; terminating communications sessions attempting to pass encrypted information; [Assignment: organization-defined procedure or method]].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) identity backends and hypervisor isolation. The system platform implements automated least-privilege IAM bindings, Identity-Aware Proxy (IAP) zero-trust tunnels, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### AC-5 Separation of Duties


1. Identify and document [Assignment: organization-defined duties of individuals requiring separation]; and


2. Define system access authorizations to support separation of duties.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) identity backends and hypervisor isolation. The system platform implements automated least-privilege IAM bindings, Identity-Aware Proxy (IAP) zero-trust tunnels, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### AC-6 Least Privilege

Employ the principle of least privilege, allowing only authorized accesses for users (or processes acting on behalf of users) that are necessary to accomplish assigned organizational tasks.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) identity backends and hypervisor isolation. The system platform implements automated least-privilege IAM bindings, Identity-Aware Proxy (IAP) zero-trust tunnels, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### AC-6(1) Least Privilege | Authorize Access to Security Functions

Authorize access for [Assignment: organization-defined individuals or roles] to:

1. [Assignment: organization-defined security functions (deployed in hardware, software, and firmware)]; and

2. [Assignment: organization-defined security-relevant information].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) identity backends and hypervisor isolation. The system platform implements automated least-privilege IAM bindings, Identity-Aware Proxy (IAP) zero-trust tunnels, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### AC-6(2) Least Privilege | Non-privileged Access for Nonsecurity Functions

Require that users of system accounts (or roles) with access to [Assignment: organization-defined security functions or security-relevant information] use non-privileged accounts or roles, when accessing nonsecurity functions.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) identity backends and hypervisor isolation. The system platform implements automated least-privilege IAM bindings, Identity-Aware Proxy (IAP) zero-trust tunnels, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### AC-6(3) Least Privilege | Network Access to Privileged Commands

Authorize network access to [Assignment: organization-defined privileged commands] only for [Assignment: organization-defined compelling operational needs] and document the rationale for such access in the security plan for the system.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) identity backends and hypervisor isolation. The system platform implements automated least-privilege IAM bindings, Identity-Aware Proxy (IAP) zero-trust tunnels, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### AC-6(5) Least Privilege | Privileged Accounts

Restrict privileged accounts on the system to [Assignment: organization-defined personnel or roles].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) identity backends and hypervisor isolation. The system platform implements automated least-privilege IAM bindings, Identity-Aware Proxy (IAP) zero-trust tunnels, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### AC-6(7) Least Privilege | Review of User Privileges


1. Review [Assignment: organization-defined frequency] the privileges assigned to [Assignment: organization-defined roles or classes of users] to validate the need for such privileges; and


2. Reassign or remove privileges, if necessary, to correctly reflect organizational mission and business needs.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) identity backends and hypervisor isolation. The system platform implements automated least-privilege IAM bindings, Identity-Aware Proxy (IAP) zero-trust tunnels, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### AC-6(8) Least Privilege | Privilege Levels for Code Execution

Prevent the following software from executing at higher privilege levels than users executing the software: [Assignment: organization-defined software].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) identity backends and hypervisor isolation. The system platform implements automated least-privilege IAM bindings, Identity-Aware Proxy (IAP) zero-trust tunnels, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### AC-6(9) Least Privilege | Log Use of Privileged Functions

Log the execution of privileged functions.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) identity backends and hypervisor isolation. The system platform implements automated least-privilege IAM bindings, Identity-Aware Proxy (IAP) zero-trust tunnels, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### AC-6(10) Least Privilege | Prohibit Non-privileged Users from Executing Privileged Functions

Prevent non-privileged users from executing privileged functions.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) identity backends and hypervisor isolation. The system platform implements automated least-privilege IAM bindings, Identity-Aware Proxy (IAP) zero-trust tunnels, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### AC-7 Unsuccessful Logon Attempts


1. Enforce a limit of [Assignment: organization-defined number] consecutive invalid logon attempts by a user during a [Assignment: organization-defined time period]; and


2. Automatically [Selection (one or more): lock the account or node for an [Assignment: organization-defined time period]; lock the account or node until released by an administrator; delay next logon prompt per [Assignment: organization-defined delay algorithm]; notify system administrator; take other [Assignment: organization-defined action]] when the maximum number of unsuccessful attempts is exceeded.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). Google LLC manages underlying infrastructure, GCI backends, and physical environment controls for AC-7. |


### AC-8 System Use Notification


1. Display [Assignment: organization-defined system use notification message or banner] to users before granting access to the system that provides privacy and security notices consistent with applicable laws, executive orders, directives, regulations, policies, standards, and guidelines and state that:

  a. Users are accessing a U.S. Government system;

  b. System usage may be monitored, recorded, and subject to audit;

  c. Unauthorized use of the system is prohibited and subject to criminal and civil penalties; and

  d. Use of the system indicates consent to monitoring and recording;


2. Retain the notification message or banner on the screen until users acknowledge the usage conditions and take explicit actions to log on to or further access the system; and


3. For publicly accessible systems:

  e. Display system use information [Assignment: organization-defined conditions], before granting further access to the publicly accessible system;

  f. Display references, if any, to monitoring, recording, or auditing that are consistent with privacy accommodations for such systems that generally prohibit those activities; and

  g. Include a description of the authorized uses of the system.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) identity backends and hypervisor isolation. The system platform implements automated least-privilege IAM bindings, Identity-Aware Proxy (IAP) zero-trust tunnels, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### AC-10 Concurrent Session Control

Limit the number of concurrent sessions for each [Assignment: organization-defined account and/or account type] to [Assignment: organization-defined number].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). Google LLC manages underlying infrastructure, GCI backends, and physical environment controls for AC-10. |


### AC-11 Device Lock


1. Prevent further access to the system by [Selection (one or more): initiating a device lock after [Assignment: organization-defined time period] of inactivity; requiring the user to initiate a device lock before leaving the system unattended]; and


2. Retain the device lock until the user reestablishes access using established identification and authentication procedures.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). Google LLC manages underlying infrastructure, GCI backends, and physical environment controls for AC-11. |


### AC-11(1) Device Lock | Pattern-hiding Displays

Conceal, via the device lock, information previously visible on the display with a publicly viewable image.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). Google LLC manages underlying infrastructure, GCI backends, and physical environment controls for AC-11(1). |


### AC-12 Session Termination

Automatically terminate a user session after [Assignment: organization-defined conditions or trigger events requiring session disconnect].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). Google LLC manages underlying infrastructure, GCI backends, and physical environment controls for AC-12. |


### AC-12(1) Session Termination | User-initiated Logouts

Provide a logout capability for user-initiated communications sessions whenever authentication is used to gain access to [Assignment: organization-defined information resources].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) identity backends and hypervisor isolation. The system platform implements automated least-privilege IAM bindings, Identity-Aware Proxy (IAP) zero-trust tunnels, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### AC-12(2) Session Termination | Termination Message

Display an explicit logout message to users indicating the termination of authenticated communications sessions.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) identity backends and hypervisor isolation. The system platform implements automated least-privilege IAM bindings, Identity-Aware Proxy (IAP) zero-trust tunnels, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### AC-14 Permitted Actions Without Identification or Authentication


1. Identify [Assignment: organization-defined user actions] that can be performed on the system without identification or authentication consistent with organizational mission and business functions; and


2. Document and provide supporting rationale in the security plan for the system, user actions not requiring identification or authentication.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) identity backends and hypervisor isolation. The system platform implements automated least-privilege IAM bindings, Identity-Aware Proxy (IAP) zero-trust tunnels, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### AC-16 Security and Privacy Attributes


1. Provide the means to associate [Assignment: organization-defined types of security and privacy attributes] with [Assignment: organization-defined security and privacy attribute values] for information in storage, in process, and/or in transmission;


2. Ensure that the attribute associations are made and retained with the information;


3. Establish the following permitted security and privacy attributes from the attributes defined in AC-16a for [Assignment: organization-defined systems]: [Assignment: organization-defined security and privacy attributes];


4. Determine the following permitted attribute values or ranges for each of the established attributes: [Assignment: organization-defined attribute values or ranges for established attributes];


5. Audit changes to attributes; and


6. Review [Assignment: organization-defined security and privacy attributes] for applicability [Assignment: organization-defined frequency].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) identity backends and hypervisor isolation. The system platform implements automated least-privilege IAM bindings, Identity-Aware Proxy (IAP) zero-trust tunnels, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### AC-16(6) Security and Privacy Attributes | Maintenance of Attribute Association

Require personnel to associate and maintain the association of [Assignment: organization-defined security and privacy attributes] with [Assignment: organization-defined subjects and objects] in accordance with [Assignment: organization-defined security and privacy policies].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) identity backends and hypervisor isolation. The system platform implements automated least-privilege IAM bindings, Identity-Aware Proxy (IAP) zero-trust tunnels, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### AC-16(7) Security and Privacy Attributes | Consistent Attribute Interpretation

Provide a consistent interpretation of security and privacy attributes transmitted between distributed system components.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) identity backends and hypervisor isolation. The system platform implements automated least-privilege IAM bindings, Identity-Aware Proxy (IAP) zero-trust tunnels, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### AC-17 Remote Access


1. Establish and document usage restrictions, configuration/connection requirements, and implementation guidance for each type of remote access allowed; and


2. Authorize each type of remote access to the system prior to allowing such connections.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) identity backends and hypervisor isolation. The system platform implements automated least-privilege IAM bindings, Identity-Aware Proxy (IAP) zero-trust tunnels, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### AC-17(1) Remote Access | Monitoring and Control

Employ automated mechanisms to monitor and control remote access methods.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) identity backends and hypervisor isolation. The system platform implements automated least-privilege IAM bindings, Identity-Aware Proxy (IAP) zero-trust tunnels, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### AC-17(2) Remote Access | Protection of Confidentiality and Integrity Using Encryption

Implement cryptographic mechanisms to protect the confidentiality and integrity of remote access sessions.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) identity backends and hypervisor isolation. The system platform implements automated least-privilege IAM bindings, Identity-Aware Proxy (IAP) zero-trust tunnels, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### AC-17(3) Remote Access | Managed Access Control Points

Route remote accesses through authorized and managed network access control points.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) identity backends and hypervisor isolation. The system platform implements automated least-privilege IAM bindings, Identity-Aware Proxy (IAP) zero-trust tunnels, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### AC-17(4) Remote Access | Privileged Commands and Access


1. Authorize the execution of privileged commands and access to security-relevant information via remote access only in a format that provides assessable evidence and for the following needs: [Assignment: organization-defined needs]; and


2. Document the rationale for remote access in the security plan for the system.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) identity backends and hypervisor isolation. The system platform implements automated least-privilege IAM bindings, Identity-Aware Proxy (IAP) zero-trust tunnels, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### AC-17(6) Remote Access | Protection of Mechanism Information

Protect information about remote access mechanisms from unauthorized use and disclosure.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) identity backends and hypervisor isolation. The system platform implements automated least-privilege IAM bindings, Identity-Aware Proxy (IAP) zero-trust tunnels, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### AC-17(9) Remote Access | Disconnect or Disable Access

Provide the capability to disconnect or disable remote access to the system within [Assignment: organization-defined time period].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) identity backends and hypervisor isolation. The system platform implements automated least-privilege IAM bindings, Identity-Aware Proxy (IAP) zero-trust tunnels, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### AC-17(10) Remote Access | Authenticate Remote Commands

Implement [Assignment: organization-defined mechanisms] to authenticate [Assignment: organization-defined remote commands].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) identity backends and hypervisor isolation. The system platform implements automated least-privilege IAM bindings, Identity-Aware Proxy (IAP) zero-trust tunnels, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### AC-18 Wireless Access


1. Establish configuration requirements, connection requirements, and implementation guidance for each type of wireless access; and


2. Authorize each type of wireless access to the system prior to allowing such connections.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). Google LLC manages underlying infrastructure, GCI backends, and physical environment controls for AC-18. |


### AC-18(1) Wireless Access | Authentication and Encryption

Protect wireless access to the system using authentication of [Selection (one or more): users; devices] and encryption.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). Google LLC manages underlying infrastructure, GCI backends, and physical environment controls for AC-18(1). |


### AC-18(3) Wireless Access | Disable Wireless Networking

Disable, when not intended for use, wireless networking capabilities embedded within system components prior to issuance and deployment.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). Google LLC manages underlying infrastructure, GCI backends, and physical environment controls for AC-18(3). |


### AC-18(4) Wireless Access | Restrict Configurations by Users

Identify and explicitly authorize users allowed to independently configure wireless networking capabilities.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). Google LLC manages underlying infrastructure, GCI backends, and physical environment controls for AC-18(4). |


### AC-18(5) Wireless Access | Antennas and Transmission Power Levels

Select radio antennas and calibrate transmission power levels to reduce the probability that signals from wireless access points can be received outside of organization-controlled boundaries.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). Google LLC manages underlying infrastructure, GCI backends, and physical environment controls for AC-18(5). |


### AC-19 Access Control for Mobile Devices


1. Establish configuration requirements, connection requirements, and implementation guidance for organization-controlled mobile devices, to include when such devices are outside of controlled areas; and


2. Authorize the connection of mobile devices to organizational systems.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). Google LLC manages underlying infrastructure, GCI backends, and physical environment controls for AC-19. |


### AC-19(5) Access Control for Mobile Devices | Full Device or Container-based Encryption

Employ [Selection: full-device encryption; container-based encryption] to protect the confidentiality and integrity of information on [Assignment: organization-defined mobile devices].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). Google LLC manages underlying infrastructure, GCI backends, and physical environment controls for AC-19(5). |


### AC-20 Use of External Systems

1. [Selection (one or more): Establish [Assignment: organization-defined terms and conditions]; Identify [Assignment: organization-defined controls asserted to be implemented on external systems]], consistent with the trust relationships established with other organizations owning, operating, and/or maintaining external systems, allowing authorized individuals to:

  a. Access the system from external systems; and

  b. Process, store, or transmit organization-controlled information using external systems; or


2. Prohibit the use of [Assignment: organizationally-defined types of external systems].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) identity backends and hypervisor isolation. The system platform implements automated least-privilege IAM bindings, Identity-Aware Proxy (IAP) zero-trust tunnels, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### AC-20(1) Use of External Systems | Limits on Authorized Use

Permit authorized individuals to use an external system to access the system or to process, store, or transmit organization-controlled information only after:


1. Verification of the implementation of controls on the external system as specified in the organization’s security and privacy policies and security and privacy plans; or


2. Retention of approved system connection or processing agreements with the organizational entity hosting the external system.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) identity backends and hypervisor isolation. The system platform implements automated least-privilege IAM bindings, Identity-Aware Proxy (IAP) zero-trust tunnels, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### AC-20(2) Use of External Systems | Portable Storage Devices — Restricted Use

Restrict the use of organization-controlled portable storage devices by authorized individuals on external systems using [Assignment: organization-defined restrictions].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) identity backends and hypervisor isolation. The system platform implements automated least-privilege IAM bindings, Identity-Aware Proxy (IAP) zero-trust tunnels, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### AC-20(3) Use of External Systems | Non-organizationally Owned Systems — Restricted Use

Restrict the use of non-organizationally owned systems or system components to process, store, or transmit organizational information using [Assignment: organization-defined restrictions].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) identity backends and hypervisor isolation. The system platform implements automated least-privilege IAM bindings, Identity-Aware Proxy (IAP) zero-trust tunnels, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### AC-21 Information Sharing


1. Enable authorized users to determine whether access authorizations assigned to a sharing partner match the information’s access and use restrictions for [Assignment: organization-defined information sharing circumstances where user discretion is required]; and


2. Employ [Assignment: organization-defined automated mechanisms or manual processes] to assist users in making information sharing and collaboration decisions.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) identity backends and hypervisor isolation. The system platform implements automated least-privilege IAM bindings, Identity-Aware Proxy (IAP) zero-trust tunnels, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### AC-22 Publicly Accessible Content


1. Designate individuals authorized to make information publicly accessible;


2. Train authorized individuals to ensure that publicly accessible information does not contain nonpublic information;


3. Review the proposed content of information prior to posting onto the publicly accessible system to ensure that nonpublic information is not included; and


4. Review the content on the publicly accessible system for nonpublic information [Assignment: organization-defined frequency] and remove such information, if discovered.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) identity backends and hypervisor isolation. The system platform implements automated least-privilege IAM bindings, Identity-Aware Proxy (IAP) zero-trust tunnels, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### AC-23 Data Mining Protection

Employ [Assignment: organization-defined data mining prevention and detection techniques] for [Assignment: organization-defined data storage objects] to detect and protect against unauthorized data mining.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) identity backends and hypervisor isolation. The system platform implements automated least-privilege IAM bindings, Identity-Aware Proxy (IAP) zero-trust tunnels, VPC Service Controls perimeters, and Google Organization Policy constraints. |


## 2.2 Awareness and Training


### AT-1 Policy and Procedures


1. Develop, document, and disseminate to [Assignment: organization-defined personnel or roles]:

  a. [Selection (one or more): Organization-level; Mission/business process-level; System-level] awareness and training policy that:

    - Addresses purpose, scope, roles, responsibilities, management commitment, coordination among organizational entities, and compliance; and

    - Is consistent with applicable laws, executive orders, directives, regulations, policies, standards, and guidelines; and

  b. Procedures to facilitate the implementation of the awareness and training policy and the associated awareness and training controls;


2. Designate an [Assignment: organization-defined official] to manage the development, documentation, and dissemination of the awareness and training policy and procedures; and


3. Review and update the current awareness and training:

  c. Policy [Assignment: organization-defined frequency] and following [Assignment: organization-defined events]; and

  d. Procedures [Assignment: organization-defined frequency] and following [Assignment: organization-defined events].


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC provides mandatory security and privacy awareness training for all Google personnel supporting GCI and GCP (Inherited). {{ ORGANIZATION }} provides role-based RMF compliance and security training for system administrators and users. |


### AT-2 Literacy Training and Awareness


1. Provide security and privacy literacy training to system users (including managers, senior executives, and contractors):

  a. As part of initial training for new users and [Assignment: organization-defined frequency] thereafter; and

  b. When required by system changes or following [Assignment: organization-defined events];


2. Employ the following techniques to increase the security and privacy awareness of system users [Assignment: organization-defined awareness techniques];


3. Update literacy training and awareness content [Assignment: organization-defined frequency] and following [Assignment: organization-defined events]; and


4. Incorporate lessons learned from internal or external security incidents or breaches into literacy training and awareness techniques.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC provides mandatory security and privacy awareness training for all Google personnel supporting GCI and GCP (Inherited). {{ ORGANIZATION }} provides role-based RMF compliance and security training for system administrators and users. |


### AT-2(2) Literacy Training and Awareness | Insider Threat

Provide literacy training on recognizing and reporting potential indicators of insider threat.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC provides mandatory security and privacy awareness training for all Google personnel supporting GCI and GCP (Inherited). {{ ORGANIZATION }} provides role-based RMF compliance and security training for system administrators and users. |


### AT-2(3) Literacy Training and Awareness | Social Engineering and Mining

Provide literacy training on recognizing and reporting potential and actual instances of social engineering and social mining.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC provides mandatory security and privacy awareness training for all Google personnel supporting GCI and GCP (Inherited). {{ ORGANIZATION }} provides role-based RMF compliance and security training for system administrators and users. |


### AT-2(4) Literacy Training and Awareness | Suspicious Communications and Anomalous System Behavior

Provide literacy training on recognizing suspicious communications and anomalous behavior in organizational systems using [Assignment: organization-defined indicators of malicious code].


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC provides mandatory security and privacy awareness training for all Google personnel supporting GCI and GCP (Inherited). {{ ORGANIZATION }} provides role-based RMF compliance and security training for system administrators and users. |


### AT-2(5) Literacy Training and Awareness | Advanced Persistent Threat

Provide literacy training on the advanced persistent threat.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC provides mandatory security and privacy awareness training for all Google personnel supporting GCI and GCP (Inherited). {{ ORGANIZATION }} provides role-based RMF compliance and security training for system administrators and users. |


### AT-2(6) Literacy Training and Awareness | Cyber Threat Environment


1. Provide literacy training on the cyber threat environment; and


2. Reflect current cyber threat information in system operations.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC provides mandatory security and privacy awareness training for all Google personnel supporting GCI and GCP (Inherited). {{ ORGANIZATION }} provides role-based RMF compliance and security training for system administrators and users. |


### AT-3 Role-Based Training


1. Provide role-based security and privacy training to personnel with the following roles and responsibilities: [Assignment: organization-defined roles and responsibilities]:

  a. Before authorizing access to the system, information, or performing assigned duties, and [Assignment: organization-defined frequency] thereafter; and

  b. When required by system changes;


2. Update role-based training content [Assignment: organization-defined frequency] and following [Assignment: organization-defined events]; and


3. Incorporate lessons learned from internal or external security incidents or breaches into role-based training.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC provides mandatory security and privacy awareness training for all Google personnel supporting GCI and GCP (Inherited). {{ ORGANIZATION }} provides role-based RMF compliance and security training for system administrators and users. |


### AT-3(1) Role-Based Training | Environmental Controls

Provide [Assignment: organization-defined personnel or roles] with initial and [Assignment: organization-defined frequency] training in the employment and operation of environmental controls.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC provides mandatory security and privacy awareness training for all Google personnel supporting GCI and GCP (Inherited). {{ ORGANIZATION }} provides role-based RMF compliance and security training for system administrators and users. |


### AT-3(2) Role-based Training | Physical Security Controls

Provide [Assignment: organization-defined personnel or roles] with initial and [Assignment: organization-defined frequency] training in the employment and operation of physical security controls.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC provides mandatory security and privacy awareness training for all Google personnel supporting GCI and GCP (Inherited). {{ ORGANIZATION }} provides role-based RMF compliance and security training for system administrators and users. |


### AT-4 Training Records


1. Document and monitor information security and privacy training activities, including security and privacy awareness training and specific role-based security and privacy training; and


2. Retain individual training records for [Assignment: organization-defined time period].


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC provides mandatory security and privacy awareness training for all Google personnel supporting GCI and GCP (Inherited). {{ ORGANIZATION }} provides role-based RMF compliance and security training for system administrators and users. |


### AT-6 Training Feedback

Provide feedback on organizational training results to the following personnel [Assignment: organization-defined frequency]: [Assignment: organization-defined personnel].


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC provides mandatory security and privacy awareness training for all Google personnel supporting GCI and GCP (Inherited). {{ ORGANIZATION }} provides role-based RMF compliance and security training for system administrators and users. |


## 2.3 Audit and Accountability


### AU-1 Policy and Procedures


1. Develop, document, and disseminate to [Assignment: organization-defined personnel or roles]:

  a. [Selection (one or more): Organization-level; Mission/business process-level; System-level] audit and accountability policy that:

    - Addresses purpose, scope, roles, responsibilities, management commitment, coordination among organizational entities, and compliance; and

    - Is consistent with applicable laws, executive orders, directives, regulations, policies, standards, and guidelines; and

  b. Procedures to facilitate the implementation of the audit and accountability policy and the associated audit and accountability controls;


2. Designate an [Assignment: organization-defined official] to manage the development, documentation, and dissemination of the audit and accountability policy and procedures; and


3. Review and update the current audit and accountability:

  c. Policy [Assignment: organization-defined frequency] and following [Assignment: organization-defined events]; and

  d. Procedures [Assignment: organization-defined frequency] and following [Assignment: organization-defined events].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google GCI audit infrastructure and Cloud Audit Logs backend. The system platform configures automated Cloud Logging audit sinks across all cloud projects, exporting immutable log records to Cloud Storage retention buckets and {{ SIEM_TOOL }} with real-time alerting via {{ TELEMETRY_PIPELINE }} and {{ THREAT_DETECTION_ENGINE }}. |


### AU-2 Event Logging


1. Identify the types of events that the system is capable of logging in support of the audit function: [Assignment: organization-defined event types that the system is capable of logging];


2. Coordinate the event logging function with other organizational entities requiring audit-related information to guide and inform the selection criteria for events to be logged;


3. Specify the following event types for logging within the system: [Assignment: organization-defined event types (subset of the event types defined in AU-2a.) along with the frequency of (or situation requiring) logging for each identified event type];


4. Provide a rationale for why the event types selected for logging are deemed to be adequate to support after-the-fact investigations of incidents; and


5. Review and update the event types selected for logging [Assignment: organization-defined frequency].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google GCI audit infrastructure and Cloud Audit Logs backend. The system platform configures automated Cloud Logging audit sinks across all cloud projects, exporting immutable log records to Cloud Storage retention buckets and {{ SIEM_TOOL }} with real-time alerting via {{ TELEMETRY_PIPELINE }} and {{ THREAT_DETECTION_ENGINE }}. |


### AU-3 Content of Audit Records

Ensure that audit records contain information that establishes the following:


1. What type of event occurred;


2. When the event occurred;


3. Where the event occurred;


4. Source of the event;


5. Outcome of the event; and


6. Identity of any individuals, subjects, or objects/entities associated with the event.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google GCI audit infrastructure and Cloud Audit Logs backend. The system platform configures automated Cloud Logging audit sinks across all cloud projects, exporting immutable log records to Cloud Storage retention buckets and {{ SIEM_TOOL }} with real-time alerting via {{ TELEMETRY_PIPELINE }} and {{ THREAT_DETECTION_ENGINE }}. |


### AU-3(1) Content of Audit Records | Additional Audit Information

Generate audit records containing the following additional information: [Assignment: organization-defined additional information].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google GCI audit infrastructure and Cloud Audit Logs backend. The system platform configures automated Cloud Logging audit sinks across all cloud projects, exporting immutable log records to Cloud Storage retention buckets and {{ SIEM_TOOL }} with real-time alerting via {{ TELEMETRY_PIPELINE }} and {{ THREAT_DETECTION_ENGINE }}. |


### AU-4 Audit Log Storage Capacity

Allocate audit log storage capacity to accommodate [Assignment: organization-defined audit log retention requirements].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google GCI audit infrastructure and Cloud Audit Logs backend. The system platform configures automated Cloud Logging audit sinks across all cloud projects, exporting immutable log records to Cloud Storage retention buckets and {{ SIEM_TOOL }} with real-time alerting via {{ TELEMETRY_PIPELINE }} and {{ THREAT_DETECTION_ENGINE }}. |


### AU-4(1) Audit Log Storage Capacity | Transfer to Alternate Storage

Transfer audit logs [Assignment: organization-defined frequency] to a different system, system component, or media other than the system or system component conducting the logging.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google GCI audit infrastructure and Cloud Audit Logs backend. The system platform configures automated Cloud Logging audit sinks across all cloud projects, exporting immutable log records to Cloud Storage retention buckets and {{ SIEM_TOOL }} with real-time alerting via {{ TELEMETRY_PIPELINE }} and {{ THREAT_DETECTION_ENGINE }}. |


### AU-5 Response to Audit Logging Process Failures


1. Alert [Assignment: organization-defined personnel or roles] within [Assignment: organization-defined time period] in the event of an audit logging process failure; and


2. Take the following additional actions: [Assignment: organization-defined additional actions].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google GCI audit infrastructure and Cloud Audit Logs backend. The system platform configures automated Cloud Logging audit sinks across all cloud projects, exporting immutable log records to Cloud Storage retention buckets and {{ SIEM_TOOL }} with real-time alerting via {{ TELEMETRY_PIPELINE }} and {{ THREAT_DETECTION_ENGINE }}. |


### AU-5(1) Response to Audit Logging Process Failures | Storage Capacity Warning

Provide a warning to [Assignment: organization-defined personnel, roles, and/or locations] within [Assignment: organization-defined time period] when allocated audit log storage volume reaches [Assignment: organization-defined percentage] of repository maximum audit log storage capacity.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google GCI audit infrastructure and Cloud Audit Logs backend. The system platform configures automated Cloud Logging audit sinks across all cloud projects, exporting immutable log records to Cloud Storage retention buckets and {{ SIEM_TOOL }} with real-time alerting via {{ TELEMETRY_PIPELINE }} and {{ THREAT_DETECTION_ENGINE }}. |


### AU-5(2) Response to Audit Logging Process Failures | Real-Time Alerts

Provide an alert within [Assignment: organization-defined real-time period] to [Assignment: organization-defined personnel, roles, and/or locations] when the following audit failure events occur: [Assignment: organization-defined audit logging failure events requiring real-time alerts].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google GCI audit infrastructure and Cloud Audit Logs backend. The system platform configures automated Cloud Logging audit sinks across all cloud projects, exporting immutable log records to Cloud Storage retention buckets and {{ SIEM_TOOL }} with real-time alerting via {{ TELEMETRY_PIPELINE }} and {{ THREAT_DETECTION_ENGINE }}. |


### AU-6 Audit Record Review, Analysis, and Reporting


1. Review and analyze system audit records [Assignment: organization-defined frequency] for indications of [Assignment: organization-defined inappropriate or unusual activity] and the potential impact of the inappropriate or unusual activity;


2. Report findings to [Assignment: organization-defined personnel or roles]; and


3. Adjust the level of audit record review, analysis, and reporting within the system when there is a change in risk based on law enforcement information, intelligence information, or other credible sources of information.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google GCI audit infrastructure and Cloud Audit Logs backend. The system platform configures automated Cloud Logging audit sinks across all cloud projects, exporting immutable log records to Cloud Storage retention buckets and {{ SIEM_TOOL }} with real-time alerting via {{ TELEMETRY_PIPELINE }} and {{ THREAT_DETECTION_ENGINE }}. |


### AU-6(1) Audit Record Review, Analysis, and Reporting | Automated Process Integration

Integrate audit record review, analysis, and reporting processes using [Assignment: organization-defined automated mechanisms].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google GCI audit infrastructure and Cloud Audit Logs backend. The system platform configures automated Cloud Logging audit sinks across all cloud projects, exporting immutable log records to Cloud Storage retention buckets and {{ SIEM_TOOL }} with real-time alerting via {{ TELEMETRY_PIPELINE }} and {{ THREAT_DETECTION_ENGINE }}. |


### AU-6(3) Audit Record Review, Analysis, and Reporting | Correlate Audit Record Repositories

Analyze and correlate audit records across different repositories to gain organization-wide situational awareness.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google GCI audit infrastructure and Cloud Audit Logs backend. The system platform configures automated Cloud Logging audit sinks across all cloud projects, exporting immutable log records to Cloud Storage retention buckets and {{ SIEM_TOOL }} with real-time alerting via {{ TELEMETRY_PIPELINE }} and {{ THREAT_DETECTION_ENGINE }}. |


### AU-6(4) Audit Record Review, Analysis, and Reporting | Central Review and Analysis

Provide and implement the capability to centrally review and analyze audit records from multiple components within the system.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google GCI audit infrastructure and Cloud Audit Logs backend. The system platform configures automated Cloud Logging audit sinks across all cloud projects, exporting immutable log records to Cloud Storage retention buckets and {{ SIEM_TOOL }} with real-time alerting via {{ TELEMETRY_PIPELINE }} and {{ THREAT_DETECTION_ENGINE }}. |


### AU-6(5) Audit Record Review, Analysis, and Reporting | Integrated Analysis of Audit Records

Integrate analysis of audit records with analysis of [Selection (one or more): vulnerability scanning information; performance data; system monitoring information; [Assignment: organization-defined data/information collected from other sources]] to further enhance the ability to identify inappropriate or unusual activity.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google GCI audit infrastructure and Cloud Audit Logs backend. The system platform configures automated Cloud Logging audit sinks across all cloud projects, exporting immutable log records to Cloud Storage retention buckets and {{ SIEM_TOOL }} with real-time alerting via {{ TELEMETRY_PIPELINE }} and {{ THREAT_DETECTION_ENGINE }}. |


### AU-6(6) Audit Record Review, Analysis, and Reporting | Correlation with Physical Monitoring

Correlate information from audit records with information obtained from monitoring physical access to further enhance the ability to identify suspicious, inappropriate, unusual, or malevolent activity.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google GCI audit infrastructure and Cloud Audit Logs backend. The system platform configures automated Cloud Logging audit sinks across all cloud projects, exporting immutable log records to Cloud Storage retention buckets and {{ SIEM_TOOL }} with real-time alerting via {{ TELEMETRY_PIPELINE }} and {{ THREAT_DETECTION_ENGINE }}. |


### AU-7 Audit Record Reduction and Report Generation

Provide and implement an audit record reduction and report generation capability that:


1. Supports on-demand audit record review, analysis, and reporting requirements and after-the-fact investigations of incidents; and


2. Does not alter the original content or time ordering of audit records.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). Google LLC manages underlying infrastructure, GCI backends, and physical environment controls for AU-7. |


### AU-7(1) Audit Record Reduction and Report Generation | Automatic Processing

Provide and implement the capability to process, sort, and search audit records for events of interest based on the following content: [Assignment: organization-defined fields within audit records].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google GCI audit infrastructure and Cloud Audit Logs backend. The system platform configures automated Cloud Logging audit sinks across all cloud projects, exporting immutable log records to Cloud Storage retention buckets and {{ SIEM_TOOL }} with real-time alerting via {{ TELEMETRY_PIPELINE }} and {{ THREAT_DETECTION_ENGINE }}. |


### AU-8 Time Stamps


1. Use internal system clocks to generate time stamps for audit records; and


2. Record time stamps for audit records that meet [Assignment: organization-defined granularity of time measurement] and that use Coordinated Universal Time, have a fixed local time offset from Coordinated Universal Time, or that include the local time offset as part of the time stamp.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). Google LLC manages underlying infrastructure, GCI backends, and physical environment controls for AU-8. |


### AU-9 Protection of Audit Information


1. Protect audit information and audit logging tools from unauthorized access, modification, and deletion; and


2. Alert [Assignment: organization-defined personnel or roles] upon detection of unauthorized access, modification, or deletion of audit information.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google GCI audit infrastructure and Cloud Audit Logs backend. The system platform configures automated Cloud Logging audit sinks across all cloud projects, exporting immutable log records to Cloud Storage retention buckets and {{ SIEM_TOOL }} with real-time alerting via {{ TELEMETRY_PIPELINE }} and {{ THREAT_DETECTION_ENGINE }}. |


### AU-9(2) Protection of Audit Information | Store on Separate Physical Systems or Components

Store audit records [Assignment: organization-defined frequency] in a repository that is part of a physically different system or system component than the system or component being audited.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google GCI audit infrastructure and Cloud Audit Logs backend. The system platform configures automated Cloud Logging audit sinks across all cloud projects, exporting immutable log records to Cloud Storage retention buckets and {{ SIEM_TOOL }} with real-time alerting via {{ TELEMETRY_PIPELINE }} and {{ THREAT_DETECTION_ENGINE }}. |


### AU-9(3) Protection of Audit Information | Cryptographic Protection

Implement cryptographic mechanisms to protect the integrity of audit information and audit tools.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google GCI audit infrastructure and Cloud Audit Logs backend. The system platform configures automated Cloud Logging audit sinks across all cloud projects, exporting immutable log records to Cloud Storage retention buckets and {{ SIEM_TOOL }} with real-time alerting via {{ TELEMETRY_PIPELINE }} and {{ THREAT_DETECTION_ENGINE }}. |


### AU-9(4) Protection of Audit Information | Access by Subset of Privileged Users

Authorize access to management of audit logging functionality to only [Assignment: organization-defined subset of privileged users or roles].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google GCI audit infrastructure and Cloud Audit Logs backend. The system platform configures automated Cloud Logging audit sinks across all cloud projects, exporting immutable log records to Cloud Storage retention buckets and {{ SIEM_TOOL }} with real-time alerting via {{ TELEMETRY_PIPELINE }} and {{ THREAT_DETECTION_ENGINE }}. |


### AU-9(5) Protection of Audit Information | Dual Authorization

Enforce dual authorization for [Selection (one or more): movement; deletion] of [Assignment: organization-defined audit information].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google GCI audit infrastructure and Cloud Audit Logs backend. The system platform configures automated Cloud Logging audit sinks across all cloud projects, exporting immutable log records to Cloud Storage retention buckets and {{ SIEM_TOOL }} with real-time alerting via {{ TELEMETRY_PIPELINE }} and {{ THREAT_DETECTION_ENGINE }}. |


### AU-9(6) Protection of Audit Information | Read-only Access

Authorize read-only access to audit information to [Assignment: organization-defined subset of privileged users or roles].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google GCI audit infrastructure and Cloud Audit Logs backend. The system platform configures automated Cloud Logging audit sinks across all cloud projects, exporting immutable log records to Cloud Storage retention buckets and {{ SIEM_TOOL }} with real-time alerting via {{ TELEMETRY_PIPELINE }} and {{ THREAT_DETECTION_ENGINE }}. |


### AU-10 Non-Repudiation

Provide irrefutable evidence that an individual (or process acting on behalf of an individual) has performed [Assignment: organization-defined actions to be covered by non-repudiation].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). Google LLC manages underlying infrastructure, GCI backends, and physical environment controls for AU-10. |


### AU-11 Audit Record Retention

Retain audit records for [Assignment: organization-defined time period consistent with records retention policy] to provide support for after-the-fact investigations of incidents and to meet regulatory and organizational information retention requirements.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google GCI audit infrastructure and Cloud Audit Logs backend. The system platform configures automated Cloud Logging audit sinks across all cloud projects, exporting immutable log records to Cloud Storage retention buckets and {{ SIEM_TOOL }} with real-time alerting via {{ TELEMETRY_PIPELINE }} and {{ THREAT_DETECTION_ENGINE }}. |


### AU-11(1) Audit Record Retention | Long-Term Retrieval Capability

Employ [Assignment: organization-defined measures] to ensure that long-term audit records generated by the system can be retrieved.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google GCI audit infrastructure and Cloud Audit Logs backend. The system platform configures automated Cloud Logging audit sinks across all cloud projects, exporting immutable log records to Cloud Storage retention buckets and {{ SIEM_TOOL }} with real-time alerting via {{ TELEMETRY_PIPELINE }} and {{ THREAT_DETECTION_ENGINE }}. |


### AU-12 Audit Record Generation


1. Provide audit record generation capability for the event types the system is capable of auditing as defined in AU-2a on [Assignment: organization-defined system components];


2. Allow [Assignment: organization-defined personnel or roles] to select the event types that are to be logged by specific components of the system; and


3. Generate audit records for the event types defined in AU-2c that include the audit record content defined in AU-3.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google GCI audit infrastructure and Cloud Audit Logs backend. The system platform configures automated Cloud Logging audit sinks across all cloud projects, exporting immutable log records to Cloud Storage retention buckets and {{ SIEM_TOOL }} with real-time alerting via {{ TELEMETRY_PIPELINE }} and {{ THREAT_DETECTION_ENGINE }}. |


### AU-12(1) Audit Record Generation | System-wide and Time-correlated Audit Trail

Compile audit records from [Assignment: organization-defined system components] into a system-wide (logical or physical) audit trail that is time-correlated to within [Assignment: organization-defined level of tolerance for the relationship between time stamps of individual records in the audit trail].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google GCI audit infrastructure and Cloud Audit Logs backend. The system platform configures automated Cloud Logging audit sinks across all cloud projects, exporting immutable log records to Cloud Storage retention buckets and {{ SIEM_TOOL }} with real-time alerting via {{ TELEMETRY_PIPELINE }} and {{ THREAT_DETECTION_ENGINE }}. |


### AU-12(3) Audit Record Generation | Changes by Authorized Individuals

Provide and implement the capability for [Assignment: organization-defined individuals or roles] to change the logging to be performed on [Assignment: organization-defined system components] based on [Assignment: organization-defined selectable event criteria] within [Assignment: organization-defined time thresholds].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google GCI audit infrastructure and Cloud Audit Logs backend. The system platform configures automated Cloud Logging audit sinks across all cloud projects, exporting immutable log records to Cloud Storage retention buckets and {{ SIEM_TOOL }} with real-time alerting via {{ TELEMETRY_PIPELINE }} and {{ THREAT_DETECTION_ENGINE }}. |


### AU-14 Session Audit


1. Provide and implement the capability for [Assignment: organization-defined users or roles] to [Selection (one or more): record; view; hear; log] the content of a user session under [Assignment: organization-defined circumstances]; and


2. Develop, integrate, and use session auditing activities in consultation with legal counsel and in accordance with applicable laws, executive orders, directives, regulations, policies, standards, and guidelines.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google GCI audit infrastructure and Cloud Audit Logs backend. The system platform configures automated Cloud Logging audit sinks across all cloud projects, exporting immutable log records to Cloud Storage retention buckets and {{ SIEM_TOOL }} with real-time alerting via {{ TELEMETRY_PIPELINE }} and {{ THREAT_DETECTION_ENGINE }}. |


### AU-14(1) Session Audit | System Start-Up

Initiate session audits automatically at system start-up.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google GCI audit infrastructure and Cloud Audit Logs backend. The system platform configures automated Cloud Logging audit sinks across all cloud projects, exporting immutable log records to Cloud Storage retention buckets and {{ SIEM_TOOL }} with real-time alerting via {{ TELEMETRY_PIPELINE }} and {{ THREAT_DETECTION_ENGINE }}. |


### AU-14(3) Session Audit | Remote Viewing and Listening

Provide and implement the capability for authorized users to remotely view and hear content related to an established user session in real time.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google GCI audit infrastructure and Cloud Audit Logs backend. The system platform configures automated Cloud Logging audit sinks across all cloud projects, exporting immutable log records to Cloud Storage retention buckets and {{ SIEM_TOOL }} with real-time alerting via {{ TELEMETRY_PIPELINE }} and {{ THREAT_DETECTION_ENGINE }}. |


## 2.4 Assessment, Authorization, and Monitoring


### CA-1 Policy and Procedures


1. Develop, document, and disseminate to [Assignment: organization-defined personnel or roles]:

  a. [Selection (one or more): Organization-level; Mission/business process-level; System-level] assessment, authorization, and monitoring policy that:

    - Addresses purpose, scope, roles, responsibilities, management commitment, coordination among organizational entities, and compliance; and

    - Is consistent with applicable laws, executive orders, directives, regulations, policies, standards, and guidelines; and

  b. Procedures to facilitate the implementation of the assessment, authorization, and monitoring policy and the associated assessment, authorization, and monitoring controls;


2. Designate an [Assignment: organization-defined official] to manage the development, documentation, and dissemination of the assessment, authorization, and monitoring policy and procedures; and


3. Review and update the current assessment, authorization, and monitoring:

  c. Policy [Assignment: organization-defined frequency] and following [Assignment: organization-defined events]; and

  d. Procedures [Assignment: organization-defined frequency] and following [Assignment: organization-defined events].


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Leverages Google Services FedRAMP High / IL5 provisional authorization to operate (P-ATO Package ID: {{ CSP_PATO_PACKAGE_ID }}). The system platform enforces continuous monitoring through {{ THREAT_DETECTION_ENGINE }}, {{ SIEM_TOOL }}, automated IaC drift analysis, and Gemini compliance verification tooling. Monitoring and control-effectiveness assessment are performed at the organization-defined frequency: {{ CONMON_REVIEW_FREQUENCY }}. Assessments are conducted as {{ CONMON_ASSESSMENT_TYPE }}, and security status, findings, and POA&M burndown are reported to the AO, ISSM, and ISSO through {{ GRC_TOOL_REFERENCE }}. |


### CA-2 Control Assessments


1. Select the appropriate assessor or assessment team for the type of assessment to be conducted;


2. Develop a control assessment plan that describes the scope of the assessment including:

  a. Controls and control enhancements under assessment;

  b. Assessment procedures to be used to determine control effectiveness; and

  c. Assessment environment, assessment team, and assessment roles and responsibilities;


3. Ensure the control assessment plan is reviewed and approved by the authorizing official or designated representative prior to conducting the assessment;


4. Assess the controls in the system and its environment of operation [Assignment: organization-defined frequency] to determine the extent to which the controls are implemented correctly, operating as intended, and producing the desired outcome with respect to meeting established security and privacy requirements;


5. Produce a control assessment report that document the results of the assessment; and


6. Provide the results of the control assessment to [Assignment: organization-defined individuals or roles].


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Leverages Google Services FedRAMP High / IL5 provisional authorization to operate (P-ATO Package ID: {{ CSP_PATO_PACKAGE_ID }}). The system platform enforces continuous monitoring through {{ THREAT_DETECTION_ENGINE }}, {{ SIEM_TOOL }}, automated IaC drift analysis, and Gemini compliance verification tooling. Monitoring and control-effectiveness assessment are performed at the organization-defined frequency: {{ CONMON_REVIEW_FREQUENCY }}. Assessments are conducted as {{ CONMON_ASSESSMENT_TYPE }}, and security status, findings, and POA&M burndown are reported to the AO, ISSM, and ISSO through {{ GRC_TOOL_REFERENCE }}. |


### CA-2(1) Control Assessments | Independent Assessors

Employ independent assessors or assessment teams to conduct control assessments.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Leverages Google Services FedRAMP High / IL5 provisional authorization to operate (P-ATO Package ID: {{ CSP_PATO_PACKAGE_ID }}). The system platform enforces continuous monitoring through {{ THREAT_DETECTION_ENGINE }}, {{ SIEM_TOOL }}, automated IaC drift analysis, and Gemini compliance verification tooling. Monitoring and control-effectiveness assessment are performed at the organization-defined frequency: {{ CONMON_REVIEW_FREQUENCY }}. Assessments are conducted as {{ CONMON_ASSESSMENT_TYPE }}, and security status, findings, and POA&M burndown are reported to the AO, ISSM, and ISSO through {{ GRC_TOOL_REFERENCE }}. |


### CA-2(2) Control Assessments | Specialized Assessments

Include as part of control assessments, [Assignment: organization-defined frequency], [Selection: announced; unannounced], [Selection (one or more): in-depth monitoring; security instrumentation; automated security test cases; vulnerability scanning; malicious user testing; insider threat assessment; performance and load testing; data leakage or data loss assessment; [Assignment: organization-defined other forms of assessment]].


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Leverages Google Services FedRAMP High / IL5 provisional authorization to operate (P-ATO Package ID: {{ CSP_PATO_PACKAGE_ID }}). The system platform enforces continuous monitoring through {{ THREAT_DETECTION_ENGINE }}, {{ SIEM_TOOL }}, automated IaC drift analysis, and Gemini compliance verification tooling. Monitoring and control-effectiveness assessment are performed at the organization-defined frequency: {{ CONMON_REVIEW_FREQUENCY }}. Assessments are conducted as {{ CONMON_ASSESSMENT_TYPE }}, and security status, findings, and POA&M burndown are reported to the AO, ISSM, and ISSO through {{ GRC_TOOL_REFERENCE }}. |


### CA-3 Information Exchange


1. Approve and manage the exchange of information between the system and other systems using [Selection (one or more): interconnection security agreements; information exchange security agreements; memoranda of understanding or agreement; service level agreements; user agreements; nondisclosure agreements; [Assignment: organization-defined type of agreement]];


2. Document, as part of each exchange agreement, the interface characteristics, security and privacy requirements, controls, and responsibilities for each system, and the impact level of the information communicated; and


3. Review and update the agreements [Assignment: organization-defined frequency].


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Leverages Google Services FedRAMP High / IL5 provisional authorization to operate (P-ATO Package ID: {{ CSP_PATO_PACKAGE_ID }}). The system platform enforces continuous monitoring through {{ THREAT_DETECTION_ENGINE }}, {{ SIEM_TOOL }}, automated IaC drift analysis, and Gemini compliance verification tooling. Monitoring and control-effectiveness assessment are performed at the organization-defined frequency: {{ CONMON_REVIEW_FREQUENCY }}. Assessments are conducted as {{ CONMON_ASSESSMENT_TYPE }}, and security status, findings, and POA&M burndown are reported to the AO, ISSM, and ISSO through {{ GRC_TOOL_REFERENCE }}. |


### CA-3(6) Information Exchange | Transfer Authorizations

Verify that individuals or systems transferring data between interconnecting systems have the requisite authorizations (i.e., write permissions or privileges) prior to accepting such data.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Leverages Google Services FedRAMP High / IL5 provisional authorization to operate (P-ATO Package ID: {{ CSP_PATO_PACKAGE_ID }}). The system platform enforces continuous monitoring through {{ THREAT_DETECTION_ENGINE }}, {{ SIEM_TOOL }}, automated IaC drift analysis, and Gemini compliance verification tooling. Monitoring and control-effectiveness assessment are performed at the organization-defined frequency: {{ CONMON_REVIEW_FREQUENCY }}. Assessments are conducted as {{ CONMON_ASSESSMENT_TYPE }}, and security status, findings, and POA&M burndown are reported to the AO, ISSM, and ISSO through {{ GRC_TOOL_REFERENCE }}. |


### CA-5 Plan of Action and Milestones


1. Develop a plan of action and milestones for the system to document the planned remediation actions of the organization to correct weaknesses or deficiencies noted during the assessment of the controls and to reduce or eliminate known vulnerabilities in the system; and


2. Update existing plan of action and milestones [Assignment: organization-defined frequency] based on the findings from control assessments, independent audits or reviews, and continuous monitoring activities.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Leverages Google Services FedRAMP High / IL5 provisional authorization to operate (P-ATO Package ID: {{ CSP_PATO_PACKAGE_ID }}). The system platform enforces continuous monitoring through {{ THREAT_DETECTION_ENGINE }}, {{ SIEM_TOOL }}, automated IaC drift analysis, and Gemini compliance verification tooling. Monitoring and control-effectiveness assessment are performed at the organization-defined frequency: {{ CONMON_REVIEW_FREQUENCY }}. Assessments are conducted as {{ CONMON_ASSESSMENT_TYPE }}, and security status, findings, and POA&M burndown are reported to the AO, ISSM, and ISSO through {{ GRC_TOOL_REFERENCE }}. |


### CA-6 Authorization


1. Assign a senior official as the authorizing official for the system;


2. Assign a senior official as the authorizing official for common controls available for inheritance by organizational systems;


3. Ensure that the authorizing official for the system, before commencing operations:

  a. Accepts the use of common controls inherited by the system; and

  b. Authorizes the system to operate;


4. Ensure that the authorizing official for common controls authorizes the use of those controls for inheritance by organizational systems;


5. Update the authorizations [Assignment: organization-defined frequency].


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Leverages Google Services FedRAMP High / IL5 provisional authorization to operate (P-ATO Package ID: {{ CSP_PATO_PACKAGE_ID }}). The system platform enforces continuous monitoring through {{ THREAT_DETECTION_ENGINE }}, {{ SIEM_TOOL }}, automated IaC drift analysis, and Gemini compliance verification tooling. Monitoring and control-effectiveness assessment are performed at the organization-defined frequency: {{ CONMON_REVIEW_FREQUENCY }}. Assessments are conducted as {{ CONMON_ASSESSMENT_TYPE }}, and security status, findings, and POA&M burndown are reported to the AO, ISSM, and ISSO through {{ GRC_TOOL_REFERENCE }}. |


### CA-7 Continuous Monitoring

Develop a system-level continuous monitoring strategy and implement continuous monitoring in accordance with the organization-level continuous monitoring strategy that includes:


1. Establishing the following system-level metrics to be monitored: [Assignment: organization-defined system-level metrics];


2. Establishing [Assignment: organization-defined frequencies] for monitoring and [Assignment: organization-defined frequencies] for assessment of control effectiveness;


3. Ongoing control assessments in accordance with the continuous monitoring strategy;


4. Ongoing monitoring of system and organization-defined metrics in accordance with the continuous monitoring strategy;


5. Correlation and analysis of information generated by control assessments and monitoring;


6. Response actions to address results of the analysis of control assessment and monitoring information; and


7. Reporting the security and privacy status of the system to [Assignment: organization-defined personnel or roles] [Assignment: organization-defined frequency].


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Leverages Google Services FedRAMP High / IL5 provisional authorization to operate (P-ATO Package ID: {{ CSP_PATO_PACKAGE_ID }}). The system platform enforces continuous monitoring through {{ THREAT_DETECTION_ENGINE }}, {{ SIEM_TOOL }}, automated IaC drift analysis, and Gemini compliance verification tooling. Monitoring and control-effectiveness assessment are performed at the organization-defined frequency: {{ CONMON_REVIEW_FREQUENCY }}. Assessments are conducted as {{ CONMON_ASSESSMENT_TYPE }}, and security status, findings, and POA&M burndown are reported to the AO, ISSM, and ISSO through {{ GRC_TOOL_REFERENCE }}. |


### CA-7(1) Continuous Monitoring | Independent Assessment

Employ independent assessors or assessment teams to monitor the controls in the system on an ongoing basis.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Leverages Google Services FedRAMP High / IL5 provisional authorization to operate (P-ATO Package ID: {{ CSP_PATO_PACKAGE_ID }}). The system platform enforces continuous monitoring through {{ THREAT_DETECTION_ENGINE }}, {{ SIEM_TOOL }}, automated IaC drift analysis, and Gemini compliance verification tooling. Monitoring and control-effectiveness assessment are performed at the organization-defined frequency: {{ CONMON_REVIEW_FREQUENCY }}. Assessments are conducted as {{ CONMON_ASSESSMENT_TYPE }}, and security status, findings, and POA&M burndown are reported to the AO, ISSM, and ISSO through {{ GRC_TOOL_REFERENCE }}. |


### CA-7(3) Continuous Monitoring | Trend Analysis

Employ trend analyses to determine if control implementations, the frequency of continuous monitoring activities, and the types of activities used in the continuous monitoring process need to be modified based on empirical data.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Leverages Google Services FedRAMP High / IL5 provisional authorization to operate (P-ATO Package ID: {{ CSP_PATO_PACKAGE_ID }}). The system platform enforces continuous monitoring through {{ THREAT_DETECTION_ENGINE }}, {{ SIEM_TOOL }}, automated IaC drift analysis, and Gemini compliance verification tooling. Monitoring and control-effectiveness assessment are performed at the organization-defined frequency: {{ CONMON_REVIEW_FREQUENCY }}. Assessments are conducted as {{ CONMON_ASSESSMENT_TYPE }}, and security status, findings, and POA&M burndown are reported to the AO, ISSM, and ISSO through {{ GRC_TOOL_REFERENCE }}. |


### CA-7(4) Continuous Monitoring | Risk Monitoring

Ensure risk monitoring is an integral part of the continuous monitoring strategy that includes the following:


1. Effectiveness monitoring;


2. Compliance monitoring; and


3. Change monitoring.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Leverages Google Services FedRAMP High / IL5 provisional authorization to operate (P-ATO Package ID: {{ CSP_PATO_PACKAGE_ID }}). The system platform enforces continuous monitoring through {{ THREAT_DETECTION_ENGINE }}, {{ SIEM_TOOL }}, automated IaC drift analysis, and Gemini compliance verification tooling. Monitoring and control-effectiveness assessment are performed at the organization-defined frequency: {{ CONMON_REVIEW_FREQUENCY }}. Assessments are conducted as {{ CONMON_ASSESSMENT_TYPE }}, and security status, findings, and POA&M burndown are reported to the AO, ISSM, and ISSO through {{ GRC_TOOL_REFERENCE }}. |


### CA-7(5) Continuous Monitoring | Consistency Analysis

Employ the following actions to validate that policies are established and implemented controls are operating in a consistent manner: [Assignment: organization-defined actions].


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Leverages Google Services FedRAMP High / IL5 provisional authorization to operate (P-ATO Package ID: {{ CSP_PATO_PACKAGE_ID }}). The system platform enforces continuous monitoring through {{ THREAT_DETECTION_ENGINE }}, {{ SIEM_TOOL }}, automated IaC drift analysis, and Gemini compliance verification tooling. Monitoring and control-effectiveness assessment are performed at the organization-defined frequency: {{ CONMON_REVIEW_FREQUENCY }}. Assessments are conducted as {{ CONMON_ASSESSMENT_TYPE }}, and security status, findings, and POA&M burndown are reported to the AO, ISSM, and ISSO through {{ GRC_TOOL_REFERENCE }}. |


### CA-7(6) Continuous Monitoring | Automation Support for Monitoring

Ensure the accuracy, currency, and availability of monitoring results for the system using [Assignment: organization-defined automated mechanisms].


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Leverages Google Services FedRAMP High / IL5 provisional authorization to operate (P-ATO Package ID: {{ CSP_PATO_PACKAGE_ID }}). The system platform enforces continuous monitoring through {{ THREAT_DETECTION_ENGINE }}, {{ SIEM_TOOL }}, automated IaC drift analysis, and Gemini compliance verification tooling. Monitoring and control-effectiveness assessment are performed at the organization-defined frequency: {{ CONMON_REVIEW_FREQUENCY }}. Assessments are conducted as {{ CONMON_ASSESSMENT_TYPE }}, and security status, findings, and POA&M burndown are reported to the AO, ISSM, and ISSO through {{ GRC_TOOL_REFERENCE }}. |


### CA-8 Penetration Testing

Conduct penetration testing [Assignment: organization-defined frequency] on [Assignment: organization-defined systems or system components].


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Leverages Google Services FedRAMP High / IL5 provisional authorization to operate (P-ATO Package ID: {{ CSP_PATO_PACKAGE_ID }}). The system platform enforces continuous monitoring through {{ THREAT_DETECTION_ENGINE }}, {{ SIEM_TOOL }}, automated IaC drift analysis, and Gemini compliance verification tooling. Monitoring and control-effectiveness assessment are performed at the organization-defined frequency: {{ CONMON_REVIEW_FREQUENCY }}. Assessments are conducted as {{ CONMON_ASSESSMENT_TYPE }}, and security status, findings, and POA&M burndown are reported to the AO, ISSM, and ISSO through {{ GRC_TOOL_REFERENCE }}. |


### CA-8(1) Penetration Testing | Independent Penetration Testing Agent or Team

Employ an independent penetration testing agent or team to perform penetration testing on the system or system components.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Leverages Google Services FedRAMP High / IL5 provisional authorization to operate (P-ATO Package ID: {{ CSP_PATO_PACKAGE_ID }}). The system platform enforces continuous monitoring through {{ THREAT_DETECTION_ENGINE }}, {{ SIEM_TOOL }}, automated IaC drift analysis, and Gemini compliance verification tooling. Monitoring and control-effectiveness assessment are performed at the organization-defined frequency: {{ CONMON_REVIEW_FREQUENCY }}. Assessments are conducted as {{ CONMON_ASSESSMENT_TYPE }}, and security status, findings, and POA&M burndown are reported to the AO, ISSM, and ISSO through {{ GRC_TOOL_REFERENCE }}. |


### CA-8(3) Penetration Testing | Facility Penetration Testing

> [!IMPORTANT]
> <mark style="background-color: #fff9c4; color: #b71c1c; font-weight: bold; padding: 2px 6px; border-radius: 4px;">⚠️ RMF TEAM ACTION REQUIRED: Verify and update operational procedure or contact details in this section.</mark>
> Employ a penetration testing process that includes [Assignment: organization-defined frequency] [Selection: announced; unannounced] attempts to bypass or circumvent controls associated with physical access points to the facility.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Leverages Google Services FedRAMP High / IL5 provisional authorization to operate (P-ATO Package ID: {{ CSP_PATO_PACKAGE_ID }}). The system platform enforces continuous monitoring through {{ THREAT_DETECTION_ENGINE }}, {{ SIEM_TOOL }}, automated IaC drift analysis, and Gemini compliance verification tooling. Monitoring and control-effectiveness assessment are performed at the organization-defined frequency: {{ CONMON_REVIEW_FREQUENCY }}. Assessments are conducted as {{ CONMON_ASSESSMENT_TYPE }}, and security status, findings, and POA&M burndown are reported to the AO, ISSM, and ISSO through {{ GRC_TOOL_REFERENCE }}. |


### CA-9 Internal System Connections


1. Authorize internal connections of [Assignment: organization-defined system components or classes of components] to the system;


2. Document, for each internal connection, the interface characteristics, security and privacy requirements, and the nature of the information communicated;


3. Terminate internal system connections after [Assignment: organization-defined conditions]; and


4. Review [Assignment: organization-defined frequency] the continued need for each internal connection.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Leverages Google Services FedRAMP High / IL5 provisional authorization to operate (P-ATO Package ID: {{ CSP_PATO_PACKAGE_ID }}). The system platform enforces continuous monitoring through {{ THREAT_DETECTION_ENGINE }}, {{ SIEM_TOOL }}, automated IaC drift analysis, and Gemini compliance verification tooling. Monitoring and control-effectiveness assessment are performed at the organization-defined frequency: {{ CONMON_REVIEW_FREQUENCY }}. Assessments are conducted as {{ CONMON_ASSESSMENT_TYPE }}, and security status, findings, and POA&M burndown are reported to the AO, ISSM, and ISSO through {{ GRC_TOOL_REFERENCE }}. |


## 2.5 Configuration Management


### CM-1 Policy and Procedures


1. Develop, document, and disseminate to [Assignment: organization-defined personnel or roles]:

  a. [Selection (one or more): Organization-level; Mission/business process-level; System-level] configuration management policy that:

    - Addresses purpose, scope, roles, responsibilities, management commitment, coordination among organizational entities, and compliance; and

    - Is consistent with applicable laws, executive orders, directives, regulations, policies, standards, and guidelines; and

  b. Procedures to facilitate the implementation of the configuration management policy and the associated configuration management controls;


2. Designate an [Assignment: organization-defined official] to manage the development, documentation, and dissemination of the configuration management policy and procedures; and


3. Review and update the current configuration management:

  c. Policy [Assignment: organization-defined frequency] and following [Assignment: organization-defined events]; and

  d. Procedures [Assignment: organization-defined frequency] and following [Assignment: organization-defined events].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for underlying GCI host baselines and Borglet binary verifiers. The system platform maintains system configuration baselines as Infrastructure as Code (IaC) using modular Terraform blueprints, managed in Git version control with automated CI/CD validation via Cloud Build and continuous asset tracking through Cloud Asset Inventory. |


### CM-2 Baseline Configuration


1. Develop, document, and maintain under configuration control, a current baseline configuration of the system; and


2. Review and update the baseline configuration of the system:

  a. [Assignment: organization-defined frequency];

  b. When required due to [Assignment: organization-defined circumstances]; and

  c. When system components are installed or upgraded.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for underlying GCI host baselines and Borglet binary verifiers. The system platform maintains system configuration baselines as Infrastructure as Code (IaC) using modular Terraform blueprints, managed in Git version control with automated CI/CD validation via Cloud Build and continuous asset tracking through Cloud Asset Inventory. |


### CM-2(2) Baseline Configuration | Automation Support for Accuracy and Currency

Maintain the currency, completeness, accuracy, and availability of the baseline configuration of the system using [Assignment: organization-defined automated mechanisms].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for underlying GCI host baselines and Borglet binary verifiers. The system platform maintains system configuration baselines as Infrastructure as Code (IaC) using modular Terraform blueprints, managed in Git version control with automated CI/CD validation via Cloud Build and continuous asset tracking through Cloud Asset Inventory. |


### CM-2(3) Baseline Configuration | Retention of Previous Configurations

Retain [Assignment: organization-defined number] of previous versions of baseline configurations of the system to support rollback.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for underlying GCI host baselines and Borglet binary verifiers. The system platform maintains system configuration baselines as Infrastructure as Code (IaC) using modular Terraform blueprints, managed in Git version control with automated CI/CD validation via Cloud Build and continuous asset tracking through Cloud Asset Inventory. |


### CM-2(7) Baseline Configuration | Configure Systems and Components for High-risk Areas


1. Issue [Assignment: organization-defined systems or system components] with [Assignment: organization-defined configurations] to individuals traveling to locations that the organization deems to be of significant risk; and


2. Apply the following controls to the systems or components when the individuals return from travel: [Assignment: organization-defined controls].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for underlying GCI host baselines and Borglet binary verifiers. The system platform maintains system configuration baselines as Infrastructure as Code (IaC) using modular Terraform blueprints, managed in Git version control with automated CI/CD validation via Cloud Build and continuous asset tracking through Cloud Asset Inventory. |


### CM-3 Configuration Change Control


1. Determine and document the types of changes to the system that are configuration-controlled;


2. Review proposed configuration-controlled changes to the system and approve or disapprove such changes with explicit consideration for security and privacy impact analyses;


3. Document configuration change decisions associated with the system;


4. Implement approved configuration-controlled changes to the system;


5. Retain records of configuration-controlled changes to the system for [Assignment: organization-defined time period];


6. Monitor and review activities associated with configuration-controlled changes to the system; and


7. Coordinate and provide oversight for configuration change control activities through [Assignment: organization-defined configuration change control element] that convenes [Selection (one or more): [Assignment: organization-defined frequency]; when [Assignment: organization-defined configuration change conditions]].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for underlying GCI host baselines and Borglet binary verifiers. The system platform maintains system configuration baselines as Infrastructure as Code (IaC) using modular Terraform blueprints, managed in Git version control with automated CI/CD validation via Cloud Build and continuous asset tracking through Cloud Asset Inventory. |


### CM-3(1) Configuration Change Control | Automated Documentation, Notification, and Prohibition of Changes

Use [Assignment: organization-defined automated mechanisms] to:


1. Document proposed changes to the system;


2. Notify [Assignment: organization-defined approval authorities] of proposed changes to the system and request change approval;


3. Highlight proposed changes to the system that have not been approved or disapproved within [Assignment: organization-defined time period];


4. Prohibit changes to the system until designated approvals are received;


5. Document all changes to the system; and


6. Notify [Assignment: organization-defined personnel] when approved changes to the system are completed.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for underlying GCI host baselines and Borglet binary verifiers. The system platform maintains system configuration baselines as Infrastructure as Code (IaC) using modular Terraform blueprints, managed in Git version control with automated CI/CD validation via Cloud Build and continuous asset tracking through Cloud Asset Inventory. |


### CM-3(2) Configuration Change Control | Testing, Validation, and Documentation of Changes

Test, validate, and document changes to the system before finalizing the implementation of the changes.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for underlying GCI host baselines and Borglet binary verifiers. The system platform maintains system configuration baselines as Infrastructure as Code (IaC) using modular Terraform blueprints, managed in Git version control with automated CI/CD validation via Cloud Build and continuous asset tracking through Cloud Asset Inventory. |


### CM-3(4) Configuration Change Control | Security and Privacy Representatives

Require [Assignment: organization-defined security and privacy representatives] to be members of the [Assignment: organization-defined configuration change control element].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for underlying GCI host baselines and Borglet binary verifiers. The system platform maintains system configuration baselines as Infrastructure as Code (IaC) using modular Terraform blueprints, managed in Git version control with automated CI/CD validation via Cloud Build and continuous asset tracking through Cloud Asset Inventory. |


### CM-3(5) Configuration Change Control | Automated Security Response

Implement the following security responses automatically if baseline configurations are changed in an unauthorized manner: [Assignment: organization-defined security responses].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for underlying GCI host baselines and Borglet binary verifiers. The system platform maintains system configuration baselines as Infrastructure as Code (IaC) using modular Terraform blueprints, managed in Git version control with automated CI/CD validation via Cloud Build and continuous asset tracking through Cloud Asset Inventory. |


### CM-3(6) Configuration Change Control | Cryptography Management

Ensure that cryptographic mechanisms used to provide the following controls are under configuration management: [Assignment: organization-defined controls].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for underlying GCI host baselines and Borglet binary verifiers. The system platform maintains system configuration baselines as Infrastructure as Code (IaC) using modular Terraform blueprints, managed in Git version control with automated CI/CD validation via Cloud Build and continuous asset tracking through Cloud Asset Inventory. |


### CM-3(7) Configuration Change Control | Review System Changes

Review changes to the system [Assignment: organization-defined frequency] or when [Assignment: organization-defined circumstances] to determine whether unauthorized changes have occurred.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for underlying GCI host baselines and Borglet binary verifiers. The system platform maintains system configuration baselines as Infrastructure as Code (IaC) using modular Terraform blueprints, managed in Git version control with automated CI/CD validation via Cloud Build and continuous asset tracking through Cloud Asset Inventory. |


### CM-3(8) Configuration Change Control | Prevent or Restrict Configuration Changes

Prevent or restrict changes to the configuration of the system under the following circumstances: [Assignment: organization-defined circumstances].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for underlying GCI host baselines and Borglet binary verifiers. The system platform maintains system configuration baselines as Infrastructure as Code (IaC) using modular Terraform blueprints, managed in Git version control with automated CI/CD validation via Cloud Build and continuous asset tracking through Cloud Asset Inventory. |


### CM-4 Impact Analyses

Analyze changes to the system to determine potential security and privacy impacts prior to change implementation.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for underlying GCI host baselines and Borglet binary verifiers. The system platform maintains system configuration baselines as Infrastructure as Code (IaC) using modular Terraform blueprints, managed in Git version control with automated CI/CD validation via Cloud Build and continuous asset tracking through Cloud Asset Inventory. |


### CM-4(1) Impact Analyses | Separate Test Environments

Analyze changes to the system in a separate test environment before implementation in an operational environment, looking for security and privacy impacts due to flaws, weaknesses, incompatibility, or intentional malice.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for underlying GCI host baselines and Borglet binary verifiers. The system platform maintains system configuration baselines as Infrastructure as Code (IaC) using modular Terraform blueprints, managed in Git version control with automated CI/CD validation via Cloud Build and continuous asset tracking through Cloud Asset Inventory. |


### CM-4(2) Impact Analyses | Verification of Controls

After system changes, verify that the impacted controls are implemented correctly, operating as intended, and producing the desired outcome with regard to meeting the security and privacy requirements for the system.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for underlying GCI host baselines and Borglet binary verifiers. The system platform maintains system configuration baselines as Infrastructure as Code (IaC) using modular Terraform blueprints, managed in Git version control with automated CI/CD validation via Cloud Build and continuous asset tracking through Cloud Asset Inventory. |


### CM-5 Access Restrictions for Change

Define, document, approve, and enforce physical and logical access restrictions associated with changes to the system.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for underlying GCI host baselines and Borglet binary verifiers. The system platform maintains system configuration baselines as Infrastructure as Code (IaC) using modular Terraform blueprints, managed in Git version control with automated CI/CD validation via Cloud Build and continuous asset tracking through Cloud Asset Inventory. |


### CM-5(1) Access Restrictions for Change | Automated Access Enforcement and Audit Records


1. Enforce access restrictions using [Assignment: organization-defined automated mechanisms]; and


2. Automatically generate audit records of the enforcement actions.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for underlying GCI host baselines and Borglet binary verifiers. The system platform maintains system configuration baselines as Infrastructure as Code (IaC) using modular Terraform blueprints, managed in Git version control with automated CI/CD validation via Cloud Build and continuous asset tracking through Cloud Asset Inventory. |


### CM-5(5) Access Restrictions for Change | Privilege Limitation for Production and Operation


1. Limit privileges to change system components and system-related information within a production or operational environment; and


2. Review and reevaluate privileges [Assignment: organization-defined frequency].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for underlying GCI host baselines and Borglet binary verifiers. The system platform maintains system configuration baselines as Infrastructure as Code (IaC) using modular Terraform blueprints, managed in Git version control with automated CI/CD validation via Cloud Build and continuous asset tracking through Cloud Asset Inventory. |


### CM-5(6) Access Restrictions for Change | Limit Library Privileges

Limit privileges to change software resident within software libraries.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for underlying GCI host baselines and Borglet binary verifiers. The system platform maintains system configuration baselines as Infrastructure as Code (IaC) using modular Terraform blueprints, managed in Git version control with automated CI/CD validation via Cloud Build and continuous asset tracking through Cloud Asset Inventory. |


### CM-6 Configuration Settings


1. Establish and document configuration settings for components employed within the system that reflect the most restrictive mode consistent with operational requirements using [Assignment: organization-defined common secure configurations];


2. Implement the configuration settings;


3. Identify, document, and approve any deviations from established configuration settings for [Assignment: organization-defined system components] based on [Assignment: organization-defined operational requirements]; and


4. Monitor and control changes to the configuration settings in accordance with organizational policies and procedures.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for underlying GCI host baselines and Borglet binary verifiers. The system platform maintains system configuration baselines as Infrastructure as Code (IaC) using modular Terraform blueprints, managed in Git version control with automated CI/CD validation via Cloud Build and continuous asset tracking through Cloud Asset Inventory. |


### CM-6(1) Configuration Settings | Automated Management, Application, and Verification

Manage, apply, and verify configuration settings for [Assignment: organization-defined system components] using [Assignment: organization-defined automated mechanisms].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for underlying GCI host baselines and Borglet binary verifiers. The system platform maintains system configuration baselines as Infrastructure as Code (IaC) using modular Terraform blueprints, managed in Git version control with automated CI/CD validation via Cloud Build and continuous asset tracking through Cloud Asset Inventory. |


### CM-6(2) Configuration Settings | Respond to Unauthorized Changes

Take the following actions in response to unauthorized changes to [Assignment: organization-defined configuration settings]: [Assignment: organization-defined actions].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for underlying GCI host baselines and Borglet binary verifiers. The system platform maintains system configuration baselines as Infrastructure as Code (IaC) using modular Terraform blueprints, managed in Git version control with automated CI/CD validation via Cloud Build and continuous asset tracking through Cloud Asset Inventory. |


### CM-7 Least Functionality


1. Configure the system to provide only [Assignment: organization-defined mission essential capabilities]; and


2. Prohibit or restrict the use of the following functions, ports, protocols, software, and/or services: [Assignment: organization-defined prohibited or restricted functions, system ports, protocols, software, and/or services].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for underlying GCI host baselines and Borglet binary verifiers. The system platform maintains system configuration baselines as Infrastructure as Code (IaC) using modular Terraform blueprints, managed in Git version control with automated CI/CD validation via Cloud Build and continuous asset tracking through Cloud Asset Inventory. |


### CM-7(1) Least Functionality | Periodic Review


1. Review the system [Assignment: organization-defined frequency] to identify unnecessary and/or nonsecure functions, ports, protocols, software, and services; and


2. Disable or remove [Assignment: organization-defined functions, ports, protocols, software, and services within the system deemed to be unnecessary and/or nonsecure].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for underlying GCI host baselines and Borglet binary verifiers. The system platform maintains system configuration baselines as Infrastructure as Code (IaC) using modular Terraform blueprints, managed in Git version control with automated CI/CD validation via Cloud Build and continuous asset tracking through Cloud Asset Inventory. |


### CM-7(2) Least Functionality | Prevent Program Execution

Prevent program execution in accordance with [Selection (one or more): [Assignment: organization-defined policies, rules of behavior, and/or access agreements regarding software program usage and restrictions]; rules authorizing the terms and conditions of software program usage].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for underlying GCI host baselines and Borglet binary verifiers. The system platform maintains system configuration baselines as Infrastructure as Code (IaC) using modular Terraform blueprints, managed in Git version control with automated CI/CD validation via Cloud Build and continuous asset tracking through Cloud Asset Inventory. |


### CM-7(3) Least Functionality | Registration Compliance

Ensure compliance with [Assignment: organization-defined registration requirements for functions, ports, protocols, and services].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for underlying GCI host baselines and Borglet binary verifiers. The system platform maintains system configuration baselines as Infrastructure as Code (IaC) using modular Terraform blueprints, managed in Git version control with automated CI/CD validation via Cloud Build and continuous asset tracking through Cloud Asset Inventory. |


### CM-7(5) Least Functionality | Authorized Software — Allow-by-exception


1. Identify [Assignment: organization-defined software programs authorized to execute on the system];


2. Employ a deny-all, permit-by-exception policy to allow the execution of authorized software programs on the system; and


3. Review and update the list of authorized software programs [Assignment: organization-defined frequency].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for underlying GCI host baselines and Borglet binary verifiers. The system platform maintains system configuration baselines as Infrastructure as Code (IaC) using modular Terraform blueprints, managed in Git version control with automated CI/CD validation via Cloud Build and continuous asset tracking through Cloud Asset Inventory. |


### CM-7(8) Least Functionality | Binary or Machine Executable Code


1. Prohibit the use of binary or machine-executable code from sources with limited or no warranty or without the provision of source code; and


2. Allow exceptions only for compelling mission or operational requirements and with the approval of the authorizing official.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for underlying GCI host baselines and Borglet binary verifiers. The system platform maintains system configuration baselines as Infrastructure as Code (IaC) using modular Terraform blueprints, managed in Git version control with automated CI/CD validation via Cloud Build and continuous asset tracking through Cloud Asset Inventory. |


### CM-7(9) Least Functionality | Prohibiting The Use of Unauthorized Hardware


1. Identify [Assignment: organization-defined hardware components authorized for system use];


2. Prohibit the use or connection of unauthorized hardware components;


3. Review and update the list of authorized hardware components [Assignment: organization-defined frequency].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for underlying GCI host baselines and Borglet binary verifiers. The system platform maintains system configuration baselines as Infrastructure as Code (IaC) using modular Terraform blueprints, managed in Git version control with automated CI/CD validation via Cloud Build and continuous asset tracking through Cloud Asset Inventory. |


### CM-8 System Component Inventory


1. Develop and document an inventory of system components that:

  a. Accurately reflects the system;

  b. Includes all components within the system;

  c. Does not include duplicate accounting of components or components assigned to any other system;

  d. Is at the level of granularity deemed necessary for tracking and reporting; and

  e. Includes the following information to achieve system component accountability: [Assignment: organization-defined information deemed necessary to achieve effective system component accountability]; and


2. Review and update the system component inventory [Assignment: organization-defined frequency].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for underlying GCI host baselines and Borglet binary verifiers. The system platform maintains system configuration baselines as Infrastructure as Code (IaC) using modular Terraform blueprints, managed in Git version control with automated CI/CD validation via Cloud Build and continuous asset tracking through Cloud Asset Inventory. |


### CM-8(1) System Component Inventory | Updates During Installation and Removal

Update the inventory of system components as part of component installations, removals, and system updates.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for underlying GCI host baselines and Borglet binary verifiers. The system platform maintains system configuration baselines as Infrastructure as Code (IaC) using modular Terraform blueprints, managed in Git version control with automated CI/CD validation via Cloud Build and continuous asset tracking through Cloud Asset Inventory. |


### CM-8(2) System Component Inventory | Automated Maintenance

Maintain the currency, completeness, accuracy, and availability of the inventory of system components using [Assignment: organization-defined automated mechanisms].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for underlying GCI host baselines and Borglet binary verifiers. The system platform maintains system configuration baselines as Infrastructure as Code (IaC) using modular Terraform blueprints, managed in Git version control with automated CI/CD validation via Cloud Build and continuous asset tracking through Cloud Asset Inventory. |


### CM-8(3) System Component Inventory | Automated Unauthorized Component Detection


1. Detect the presence of unauthorized hardware, software, and firmware components within the system using [Assignment: organization-defined automated mechanisms] [Assignment: organization-defined frequency]; and


2. Take the following actions when unauthorized components are detected: [Selection (one or more): disable network access by such components; isolate the components; notify [Assignment: organization-defined personnel or roles]].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for underlying GCI host baselines and Borglet binary verifiers. The system platform maintains system configuration baselines as Infrastructure as Code (IaC) using modular Terraform blueprints, managed in Git version control with automated CI/CD validation via Cloud Build and continuous asset tracking through Cloud Asset Inventory. |


### CM-8(4) System Component Inventory | Accountability Information

Include in the system component inventory information, a means for identifying by [Selection (one or more): name; position; role], individuals responsible and accountable for administering those components.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for underlying GCI host baselines and Borglet binary verifiers. The system platform maintains system configuration baselines as Infrastructure as Code (IaC) using modular Terraform blueprints, managed in Git version control with automated CI/CD validation via Cloud Build and continuous asset tracking through Cloud Asset Inventory. |


### CM-9 Configuration Management Plan

Develop, document, and implement a configuration management plan for the system that:


1. Addresses roles, responsibilities, and configuration management processes and procedures;


2. Establishes a process for identifying configuration items throughout the system development life cycle and for managing the configuration of the configuration items;


3. Defines the configuration items for the system and places the configuration items under configuration management;


4. Is reviewed and approved by [Assignment: organization-defined personnel or roles]; and


5. Protects the configuration management plan from unauthorized disclosure and modification.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for underlying GCI host baselines and Borglet binary verifiers. The system platform maintains system configuration baselines as Infrastructure as Code (IaC) using modular Terraform blueprints, managed in Git version control with automated CI/CD validation via Cloud Build and continuous asset tracking through Cloud Asset Inventory. |


### CM-10 Software Usage Restrictions


1. Use software and associated documentation in accordance with contract agreements and copyright laws;


2. Track the use of software and associated documentation protected by quantity licenses to control copying and distribution; and


3. Control and document the use of peer-to-peer file sharing technology to ensure that this capability is not used for the unauthorized distribution, display, performance, or reproduction of copyrighted work.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for underlying GCI host baselines and Borglet binary verifiers. The system platform maintains system configuration baselines as Infrastructure as Code (IaC) using modular Terraform blueprints, managed in Git version control with automated CI/CD validation via Cloud Build and continuous asset tracking through Cloud Asset Inventory. |


### CM-10(1) Software Usage Restrictions | Open-source Software

Establish the following restrictions on the use of open-source software: [Assignment: organization-defined restrictions].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for underlying GCI host baselines and Borglet binary verifiers. The system platform maintains system configuration baselines as Infrastructure as Code (IaC) using modular Terraform blueprints, managed in Git version control with automated CI/CD validation via Cloud Build and continuous asset tracking through Cloud Asset Inventory. |


### CM-11 User-installed Software


1. Establish [Assignment: organization-defined policies] governing the installation of software by users;


2. Enforce software installation policies through the following methods: [Assignment: organization-defined methods]; and


3. Monitor policy compliance [Assignment: organization-defined frequency].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for underlying GCI host baselines and Borglet binary verifiers. The system platform maintains system configuration baselines as Infrastructure as Code (IaC) using modular Terraform blueprints, managed in Git version control with automated CI/CD validation via Cloud Build and continuous asset tracking through Cloud Asset Inventory. |


### CM-11(2) User-installed Software | Software Installation with Privileged Status

Allow user installation of software only with explicit privileged status.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for underlying GCI host baselines and Borglet binary verifiers. The system platform maintains system configuration baselines as Infrastructure as Code (IaC) using modular Terraform blueprints, managed in Git version control with automated CI/CD validation via Cloud Build and continuous asset tracking through Cloud Asset Inventory. |


### CM-12 Information Location


1. Identify and document the location of [Assignment: organization-defined information] and the specific system components on which the information is processed and stored;


2. Identify and document the users who have access to the system and system components where the information is processed and stored; and


3. Document changes to the location (i.e., system or system components) where the information is processed and stored.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for underlying GCI host baselines and Borglet binary verifiers. The system platform maintains system configuration baselines as Infrastructure as Code (IaC) using modular Terraform blueprints, managed in Git version control with automated CI/CD validation via Cloud Build and continuous asset tracking through Cloud Asset Inventory. |


### CM-12(1) Information Location | Automated Tools to Support Information Location

Use automated tools to identify [Assignment: organization-defined information by information type] on [Assignment: organization-defined system components] to ensure controls are in place to protect organizational information and individual privacy.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for underlying GCI host baselines and Borglet binary verifiers. The system platform maintains system configuration baselines as Infrastructure as Code (IaC) using modular Terraform blueprints, managed in Git version control with automated CI/CD validation via Cloud Build and continuous asset tracking through Cloud Asset Inventory. |


### CM-14 Signed Components

Prevent the installation of [Assignment: organization-defined software and firmware components] without verification that the component has been digitally signed using a certificate that is recognized and approved by the organization.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for underlying GCI host baselines and Borglet binary verifiers. The system platform maintains system configuration baselines as Infrastructure as Code (IaC) using modular Terraform blueprints, managed in Git version control with automated CI/CD validation via Cloud Build and continuous asset tracking through Cloud Asset Inventory. |


## 2.6 Contingency Plan


### CP-1 Policy and Procedures


1. Develop, document, and disseminate to [Assignment: organization-defined personnel or roles]:

  a. [Selection (one or more): Organization-level; Mission/business process-level; System-level] contingency planning policy that:

    - Addresses purpose, scope, roles, responsibilities, management commitment, coordination among organizational entities, and compliance; and

    - Is consistent with applicable laws, executive orders, directives, regulations, policies, standards, and guidelines; and

  b. Procedures to facilitate the implementation of the contingency planning policy and the associated contingency planning controls;


2. Designate an [Assignment: organization-defined official] to manage the development, documentation, and dissemination of the contingency planning policy and procedures; and


3. Review and update the current contingency planning:

  c. Policy [Assignment: organization-defined frequency] and following [Assignment: organization-defined events]; and

  d. Procedures [Assignment: organization-defined frequency] and following [Assignment: organization-defined events].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% for physical data center redundancy, multi-region power backup, GCI file system geo-replication, and automated live VM migration from Google Services P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). The system platform provisions dual-region Cloud Storage backup buckets, Cloud KMS geo-redundancy, and multi-zone GKE container clusters. |


### CP-2 Contingency Plan


1. Develop a contingency plan for the system that:

  a. Identifies essential mission and business functions and associated contingency requirements;

  b. Provides recovery objectives, restoration priorities, and metrics;

> [!IMPORTANT]
> <mark style="background-color: #fff9c4; color: #b71c1c; font-weight: bold; padding: 2px 6px; border-radius: 4px;">⚠️ RMF TEAM ACTION REQUIRED: Verify and update operational procedure or contact details in this section.</mark>
>   c. Addresses contingency roles, responsibilities, assigned individuals with contact information;

  d. Addresses maintaining essential mission and business functions despite a system disruption, compromise, or failure;

  e. Addresses eventual, full system restoration without deterioration of the controls originally planned and implemented;

  f. Addresses the sharing of contingency information; and

  g. Is reviewed and approved by [Assignment: organization-defined personnel or roles];


2. Distribute copies of the contingency plan to [Assignment: organization-defined key contingency personnel (identified by name and/or by role) and organizational elements];


3. Coordinate contingency planning activities with incident handling activities;


4. Review the contingency plan for the system [Assignment: organization-defined frequency];


5. Update the contingency plan to address changes to the organization, system, or environment of operation and problems encountered during contingency plan implementation, execution, or testing;


6. Communicate contingency plan changes to [Assignment: organization-defined key contingency personnel (identified by name and/or by role) and organizational elements];


7. Incorporate lessons learned from contingency plan testing, training, or actual contingency activities into contingency testing and training; and


8. Protect the contingency plan from unauthorized disclosure and modification.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% for physical data center redundancy, multi-region power backup, GCI file system geo-replication, and automated live VM migration from Google Services P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). The system platform provisions dual-region Cloud Storage backup buckets, Cloud KMS geo-redundancy, and multi-zone GKE container clusters. |


### CP-2(1) Contingency Plan | Coordinate with Related Plans

Coordinate contingency plan development with organizational elements responsible for related plans.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% for physical data center redundancy, multi-region power backup, GCI file system geo-replication, and automated live VM migration from Google Services P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). The system platform provisions dual-region Cloud Storage backup buckets, Cloud KMS geo-redundancy, and multi-zone GKE container clusters. |


### CP-2(2) Contingency Plan | Capacity Planning

Conduct capacity planning so that necessary capacity for information processing, telecommunications, and environmental support exists during contingency operations.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% for physical data center redundancy, multi-region power backup, GCI file system geo-replication, and automated live VM migration from Google Services P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). The system platform provisions dual-region Cloud Storage backup buckets, Cloud KMS geo-redundancy, and multi-zone GKE container clusters. |


### CP-2(3) Contingency Plan | Resume Mission and Business Functions

Plan for the resumption of [Selection: all; essential] mission and business functions within [Assignment: organization-defined time period] of contingency plan activation.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% for physical data center redundancy, multi-region power backup, GCI file system geo-replication, and automated live VM migration from Google Services P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). The system platform provisions dual-region Cloud Storage backup buckets, Cloud KMS geo-redundancy, and multi-zone GKE container clusters. |


### CP-2(8) Contingency Plan | Identify Critical Assets

Identify critical system assets supporting [Selection: all; essential] mission and business functions.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% for physical data center redundancy, multi-region power backup, GCI file system geo-replication, and automated live VM migration from Google Services P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). The system platform provisions dual-region Cloud Storage backup buckets, Cloud KMS geo-redundancy, and multi-zone GKE container clusters. |


### CP-3 Contingency Training


1. Provide contingency training to system users consistent with assigned roles and responsibilities:

  a. Within [Assignment: organization-defined time period] of assuming a contingency role or responsibility;

  b. When required by system changes; and

  c. [Assignment: organization-defined frequency] thereafter; and


2. Review and update contingency training content [Assignment: organization-defined frequency] and following [Assignment: organization-defined events].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% for physical data center redundancy, multi-region power backup, GCI file system geo-replication, and automated live VM migration from Google Services P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). The system platform provisions dual-region Cloud Storage backup buckets, Cloud KMS geo-redundancy, and multi-zone GKE container clusters. |


### CP-3(1) Contingency Training | Simulated Events

Incorporate simulated events into contingency training to facilitate effective response by personnel in crisis situations.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% for physical data center redundancy, multi-region power backup, GCI file system geo-replication, and automated live VM migration from Google Services P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). The system platform provisions dual-region Cloud Storage backup buckets, Cloud KMS geo-redundancy, and multi-zone GKE container clusters. |


### CP-4 Contingency Plan Testing


1. Test the contingency plan for the system [Assignment: organization-defined frequency] using the following tests to determine the effectiveness of the plan and the readiness to execute the plan: [Assignment: organization-defined tests].


2. Review the contingency plan test results; and


3. Initiate corrective actions, if needed.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% for physical data center redundancy, multi-region power backup, GCI file system geo-replication, and automated live VM migration from Google Services P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). The system platform provisions dual-region Cloud Storage backup buckets, Cloud KMS geo-redundancy, and multi-zone GKE container clusters. |


### CP-4(1) Contingency Plan Testing | Coordinate with Related Plans

Coordinate contingency plan testing with organizational elements responsible for related plans.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% for physical data center redundancy, multi-region power backup, GCI file system geo-replication, and automated live VM migration from Google Services P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). The system platform provisions dual-region Cloud Storage backup buckets, Cloud KMS geo-redundancy, and multi-zone GKE container clusters. |


### CP-4(2) Contingency Plan Testing | Alternate Processing Site

Test the contingency plan at the alternate processing site:


1. To familiarize contingency personnel with the facility and available resources; and


2. To evaluate the capabilities of the alternate processing site to support contingency operations.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% for physical data center redundancy, multi-region power backup, GCI file system geo-replication, and automated live VM migration from Google Services P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). The system platform provisions dual-region Cloud Storage backup buckets, Cloud KMS geo-redundancy, and multi-zone GKE container clusters. |


### CP-6 Alternate Storage Site


1. Establish an alternate storage site, including necessary agreements to permit the storage and retrieval of system backup information; and


2. Ensure that the alternate storage site provides controls equivalent to that of the primary site.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% for physical data center redundancy, multi-region power backup, GCI file system geo-replication, and automated live VM migration from Google Services P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). The system platform provisions dual-region Cloud Storage backup buckets, Cloud KMS geo-redundancy, and multi-zone GKE container clusters. |


### CP-6(1) Alternate Storage Site | Separation from Primary Site

Identify an alternate storage site that is sufficiently separated from the primary storage site to reduce susceptibility to the same threats.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% for physical data center redundancy, multi-region power backup, GCI file system geo-replication, and automated live VM migration from Google Services P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). The system platform provisions dual-region Cloud Storage backup buckets, Cloud KMS geo-redundancy, and multi-zone GKE container clusters. |


### CP-6(2) Alternate Storage Site | Recovery Time and Recovery Point Objectives

Configure the alternate storage site to facilitate recovery operations in accordance with recovery time objective (`{{ RECOVERY_TIME_OBJECTIVE }}`) and recovery point objective (`{{ RECOVERY_POINT_OBJECTIVE }}`).


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% for physical data center redundancy, multi-region power backup, GCI file system geo-replication, and automated live VM migration from Google Services P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). The system platform provisions dual-region Cloud Storage backup buckets, Cloud KMS geo-redundancy, and multi-zone GKE container clusters. |


### CP-6(3) Alternate Storage Site | Accessibility

Identify potential accessibility problems to the alternate storage site in the event of an area-wide disruption or disaster and outline explicit mitigation actions.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% for physical data center redundancy, multi-region power backup, GCI file system geo-replication, and automated live VM migration from Google Services P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). The system platform provisions dual-region Cloud Storage backup buckets, Cloud KMS geo-redundancy, and multi-zone GKE container clusters. |


### CP-7 Alternate Processing Site


1. Establish an alternate processing site, including necessary agreements to permit the transfer and resumption of [Assignment: organization-defined system operations] for essential mission and business functions within [Assignment: organization-defined time period consistent with recovery time objective (`{{ RECOVERY_TIME_OBJECTIVE }}`) and recovery point objective (`{{ RECOVERY_POINT_OBJECTIVE }}`)] when the primary processing capabilities are unavailable;


2. Make available at the alternate processing site, the equipment and supplies required to transfer and resume operations or put contracts in place to support delivery to the site within the organization-defined time period for transfer and resumption; and


3. Provide controls at the alternate processing site that are equivalent to those at the primary site.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% for physical data center redundancy, multi-region power backup, GCI file system geo-replication, and automated live VM migration from Google Services P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). The system platform provisions dual-region Cloud Storage backup buckets, Cloud KMS geo-redundancy, and multi-zone GKE container clusters. |


### CP-7(1) Alternate Processing Site | Separation from Primary Site

Identify an alternate processing site that is sufficiently separated from the primary processing site to reduce susceptibility to the same threats.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% for physical data center redundancy, multi-region power backup, GCI file system geo-replication, and automated live VM migration from Google Services P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). The system platform provisions dual-region Cloud Storage backup buckets, Cloud KMS geo-redundancy, and multi-zone GKE container clusters. |


### CP-7(2) Alternate Processing Site | Accessibility

Identify potential accessibility problems to alternate processing sites in the event of an area-wide disruption or disaster and outlines explicit mitigation actions.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% for physical data center redundancy, multi-region power backup, GCI file system geo-replication, and automated live VM migration from Google Services P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). The system platform provisions dual-region Cloud Storage backup buckets, Cloud KMS geo-redundancy, and multi-zone GKE container clusters. |


### CP-7(3) Alternate Processing Site | Priority of Service

Develop alternate processing site agreements that contain priority-of-service provisions in accordance with availability requirements (including recovery time objective (`{{ RECOVERY_TIME_OBJECTIVE }}`)).


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% for physical data center redundancy, multi-region power backup, GCI file system geo-replication, and automated live VM migration from Google Services P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). The system platform provisions dual-region Cloud Storage backup buckets, Cloud KMS geo-redundancy, and multi-zone GKE container clusters. |


### CP-7(4) Alternate Processing Site | Preparation for Use

Prepare the alternate processing site so that the site can serve as the operational site supporting essential mission and business functions.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% for physical data center redundancy, multi-region power backup, GCI file system geo-replication, and automated live VM migration from Google Services P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). The system platform provisions dual-region Cloud Storage backup buckets, Cloud KMS geo-redundancy, and multi-zone GKE container clusters. |


### CP-8 Telecommunication Services

Establish alternate telecommunications services, including necessary agreements to permit the resumption of [Assignment: organization-defined system operations] for essential mission and business functions within [Assignment: organization-defined time period] when the primary telecommunications capabilities are unavailable at either the primary or alternate processing or storage sites.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% for physical data center redundancy, multi-region power backup, GCI file system geo-replication, and automated live VM migration from Google Services P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). The system platform provisions dual-region Cloud Storage backup buckets, Cloud KMS geo-redundancy, and multi-zone GKE container clusters. |


### CP-8(1) Telecommunication Services | Priority of Service Provisions


1. Develop primary and alternate telecommunications service agreements that contain priority-of-service provisions in accordance with availability requirements (including recovery time objective (`{{ RECOVERY_TIME_OBJECTIVE }}`)); and


2. Request Telecommunications Service Priority for all telecommunications services used for national security emergency preparedness if the primary and/or alternate telecommunications services are provided by a common carrier.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% for physical data center redundancy, multi-region power backup, GCI file system geo-replication, and automated live VM migration from Google Services P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). The system platform provisions dual-region Cloud Storage backup buckets, Cloud KMS geo-redundancy, and multi-zone GKE container clusters. |


### CP-8(2) Telecommunication Services | Single Points of Failure

Obtain alternate telecommunications services to reduce the likelihood of sharing a single point of failure with primary telecommunications services.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% for physical data center redundancy, multi-region power backup, GCI file system geo-replication, and automated live VM migration from Google Services P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). The system platform provisions dual-region Cloud Storage backup buckets, Cloud KMS geo-redundancy, and multi-zone GKE container clusters. |


### CP-8(3) Telecommunication Services | Separation of Primary and Alternate Providers

Obtain alternate telecommunications services from providers that are separated from primary service providers to reduce susceptibility to the same threats.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% for physical data center redundancy, multi-region power backup, GCI file system geo-replication, and automated live VM migration from Google Services P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). The system platform provisions dual-region Cloud Storage backup buckets, Cloud KMS geo-redundancy, and multi-zone GKE container clusters. |


### CP-8(4) Telecommunication Services | Provider Contingency Plan


1. Require primary and alternate telecommunications service providers to have contingency plans;


2. Review provider contingency plans to ensure that the plans meet organizational contingency requirements; and


3. Obtain evidence of contingency testing and training by providers [Assignment: organization-defined frequency].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% for physical data center redundancy, multi-region power backup, GCI file system geo-replication, and automated live VM migration from Google Services P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). The system platform provisions dual-region Cloud Storage backup buckets, Cloud KMS geo-redundancy, and multi-zone GKE container clusters. |


### CP-8(5) Telecommunication Services | Alternate Telecommunication Service Testing

Test alternate telecommunication services [Assignment: organization-defined frequency].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% for physical data center redundancy, multi-region power backup, GCI file system geo-replication, and automated live VM migration from Google Services P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). The system platform provisions dual-region Cloud Storage backup buckets, Cloud KMS geo-redundancy, and multi-zone GKE container clusters. |


### CP-9 System Backup


1. Conduct backups of user-level information contained in [Assignment: organization-defined system components] [Assignment: organization-defined frequency consistent with recovery time objective (`{{ RECOVERY_TIME_OBJECTIVE }}`) and recovery point objective (`{{ RECOVERY_POINT_OBJECTIVE }}`)];


2. Conduct backups of system-level information contained in the system [Assignment: organization-defined frequency consistent with recovery time objective (`{{ RECOVERY_TIME_OBJECTIVE }}`) and recovery point objective (`{{ RECOVERY_POINT_OBJECTIVE }}`)];


3. Conduct backups of system documentation, including security- and privacy-related documentation [Assignment: organization-defined frequency consistent with recovery time objective (`{{ RECOVERY_TIME_OBJECTIVE }}`) and recovery point objective (`{{ RECOVERY_POINT_OBJECTIVE }}`)]; and


4. Protect the confidentiality, integrity, and availability of backup information.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% for physical data center redundancy, multi-region power backup, GCI file system geo-replication, and automated live VM migration from Google Services P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). The system platform provisions dual-region Cloud Storage backup buckets, Cloud KMS geo-redundancy, and multi-zone GKE container clusters. |


### CP-9(1) System Backup | Testing for Reliability and Integrity

Test backup information [Assignment: organization-defined frequency] to verify media reliability and information integrity.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% for physical data center redundancy, multi-region power backup, GCI file system geo-replication, and automated live VM migration from Google Services P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). The system platform provisions dual-region Cloud Storage backup buckets, Cloud KMS geo-redundancy, and multi-zone GKE container clusters. |


### CP-9(2) System Backup | Test Restoration Using Sampling

Use a sample of backup information in the restoration of selected system functions as part of contingency plan testing.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% for physical data center redundancy, multi-region power backup, GCI file system geo-replication, and automated live VM migration from Google Services P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). The system platform provisions dual-region Cloud Storage backup buckets, Cloud KMS geo-redundancy, and multi-zone GKE container clusters. |


### CP-9(3) System Backup | Separation Storage for Critical Information

> [!IMPORTANT]
> <mark style="background-color: #fff9c4; color: #b71c1c; font-weight: bold; padding: 2px 6px; border-radius: 4px;">⚠️ RMF TEAM ACTION REQUIRED: Verify and update operational procedure or contact details in this section.</mark>
> Store backup copies of [Assignment: organization-defined critical system software and other security-related information] in a separate facility or in a fire rated container that is not collocated with the operational system.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% for physical data center redundancy, multi-region power backup, GCI file system geo-replication, and automated live VM migration from Google Services P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). The system platform provisions dual-region Cloud Storage backup buckets, Cloud KMS geo-redundancy, and multi-zone GKE container clusters. |


### CP-9(5) System Backup | Transfer to Alternate Storage Site

Transfer system backup information to the alternate storage site [Assignment: organization-defined time period and transfer rate consistent with the recovery time objective (`{{ RECOVERY_TIME_OBJECTIVE }}`) and recovery point objective (`{{ RECOVERY_POINT_OBJECTIVE }}`)].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% for physical data center redundancy, multi-region power backup, GCI file system geo-replication, and automated live VM migration from Google Services P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). The system platform provisions dual-region Cloud Storage backup buckets, Cloud KMS geo-redundancy, and multi-zone GKE container clusters. |


### CP-9(8) System Backup | Cryptographic Protection

Implement cryptographic mechanisms to prevent unauthorized disclosure and modification of [Assignment: organization-defined backup information].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% for physical data center redundancy, multi-region power backup, GCI file system geo-replication, and automated live VM migration from Google Services P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). The system platform provisions dual-region Cloud Storage backup buckets, Cloud KMS geo-redundancy, and multi-zone GKE container clusters. |


### CP-10 System Recovery and Reconstitution

Provide for the recovery and reconstitution of the system to a known state within [Assignment: organization-defined time period consistent with recovery time objective (`{{ RECOVERY_TIME_OBJECTIVE }}`) and recovery point objective (`{{ RECOVERY_POINT_OBJECTIVE }}`)] after a disruption, compromise, or failure.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% for physical data center redundancy, multi-region power backup, GCI file system geo-replication, and automated live VM migration from Google Services P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). The system platform provisions dual-region Cloud Storage backup buckets, Cloud KMS geo-redundancy, and multi-zone GKE container clusters. |


### CP-10(2) System Recovery and Reconstitution | Transaction Recovery

Implement transaction recovery for systems that are transaction-based.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% for physical data center redundancy, multi-region power backup, GCI file system geo-replication, and automated live VM migration from Google Services P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). The system platform provisions dual-region Cloud Storage backup buckets, Cloud KMS geo-redundancy, and multi-zone GKE container clusters. |


### CP-10(4) System Recovery and Reconstitution | Restore Within Time Period

Provide the capability to restore system components within [Assignment: organization-defined restoration time periods] from configuration-controlled and integrity-protected information representing a known, operational state for the components.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% for physical data center redundancy, multi-region power backup, GCI file system geo-replication, and automated live VM migration from Google Services P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). The system platform provisions dual-region Cloud Storage backup buckets, Cloud KMS geo-redundancy, and multi-zone GKE container clusters. |


### CP-10(6) System Recovery and Reconstitution | Component Protection

Protect system components used for recovery and reconstitution.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% for physical data center redundancy, multi-region power backup, GCI file system geo-replication, and automated live VM migration from Google Services P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). The system platform provisions dual-region Cloud Storage backup buckets, Cloud KMS geo-redundancy, and multi-zone GKE container clusters. |


## 2.7 Identification and Authentication


### IA-1 Policy and Procedures


1. Develop, document, and disseminate to [Assignment: organization-defined personnel or roles]:

  a. [Selection (one or more): Organization-level; Mission/business process-level; System-level] identification and authentication policy that:

    - Addresses purpose, scope, roles, responsibilities, management commitment, coordination among organizational entities, and compliance; and

    - Is consistent with applicable laws, executive orders, directives, regulations, policies, standards, and guidelines; and

  b. Procedures to facilitate the implementation of the identification and authentication policy and the associated identification and authentication controls;


2. Designate an [Assignment: organization-defined official] to manage the development, documentation, and dissemination of the identification and authentication policy and procedures; and


3. Review and update the current identification and authentication:

  c. Policy [Assignment: organization-defined frequency] and following [Assignment: organization-defined events]; and

  d. Procedures [Assignment: organization-defined frequency] and following [Assignment: organization-defined events].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) identity backends and hypervisor isolation. The system platform implements automated least-privilege IAM bindings, Identity-Aware Proxy (IAP) zero-trust tunnels, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### IA-2 Identification and Authentication (Organizational Users)

Uniquely identify and authenticate organizational users and associate that unique identification with processes acting on behalf of those users.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) identity backends and hypervisor isolation. The system platform implements automated least-privilege IAM bindings, Identity-Aware Proxy (IAP) zero-trust tunnels, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### IA-2(1) Identification and Authentication (Organizational Users) | Multi-factor Authentication to Privileged Accounts

Implement multi-factor authentication for access to privileged accounts.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) identity backends and hypervisor isolation. The system platform implements automated least-privilege IAM bindings, Identity-Aware Proxy (IAP) zero-trust tunnels, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### IA-2(2) Identification and Authentication (Organizational Users) | Multi-factor Authentication to Non-privileged Accounts

Implement multi-factor authentication for access to non-privileged accounts.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) identity backends and hypervisor isolation. The system platform implements automated least-privilege IAM bindings, Identity-Aware Proxy (IAP) zero-trust tunnels, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### IA-2(5) Identification and Authentication (organizational Users) | Individual Authentication with Group Authentication

When shared accounts or authenticators are employed, require users to be individually authenticated before granting access to the shared accounts or resources.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) identity backends and hypervisor isolation. The system platform implements automated least-privilege IAM bindings, Identity-Aware Proxy (IAP) zero-trust tunnels, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### IA-2(6) Identification and Authentication (organizational Users) | Access to Accounts — Separate Device

Implement multi-factor authentication for [Selection (one or more): local; network; remote] access to [Selection (one or more): privileged accounts; non-privileged accounts] such that:


1. One of the factors is provided by a device separate from the system gaining access; and


2. The device meets [Assignment: organization-defined strength of mechanism requirements].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) identity backends and hypervisor isolation. The system platform implements automated least-privilege IAM bindings, Identity-Aware Proxy (IAP) zero-trust tunnels, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### IA-2(8) Identification and Authentication (Organizational Users) | Access to Accounts — Replay Resistant

Implement replay-resistant authentication mechanisms for access to [Selection (one or more): privileged accounts; non-privileged accounts].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) identity backends and hypervisor isolation. The system platform implements automated least-privilege IAM bindings, Identity-Aware Proxy (IAP) zero-trust tunnels, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### IA-2(12) Identification and Authentication (Organizational Users) | Acceptance of PIV Credentials

Accept and electronically verify Personal Identity Verification-compliant credentials.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) identity backends and hypervisor isolation. The system platform implements automated least-privilege IAM bindings, Identity-Aware Proxy (IAP) zero-trust tunnels, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### IA-3 Device Identification and Authentication

Uniquely identify and authenticate [Assignment: organization-defined devices and/or types of devices] before establishing a [Selection (one or more): local; remote; network] connection.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). Google LLC manages underlying infrastructure, GCI backends, and physical environment controls for IA-3. |


### IA-3(1) Device Identification and Authentication | Cryptographic Bidirectional Authentication

Authenticate [Assignment: organization-defined devices and/or types of devices] before establishing [Selection (one or more): local; remote; network] connection using bidirectional authentication that is cryptographically based.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) identity backends and hypervisor isolation. The system platform implements automated least-privilege IAM bindings, Identity-Aware Proxy (IAP) zero-trust tunnels, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### IA-4 Identifier Management

Manage system identifiers by:


1. Receiving authorization from [Assignment: organization-defined personnel or roles] to assign an individual, group, role, service, or device identifier;


2. Selecting an identifier that identifies an individual, group, role, service, or device;


3. Assigning the identifier to the intended individual, group, role, service, or device; and


4. Preventing reuse of identifiers for [Assignment: organization-defined time period].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) identity backends and hypervisor isolation. The system platform implements automated least-privilege IAM bindings, Identity-Aware Proxy (IAP) zero-trust tunnels, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### IA-4(4) Identifier Management | Identify User Status

Manage individual identifiers by uniquely identifying each individual as [Assignment: organization-defined characteristic identifying individual status].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) identity backends and hypervisor isolation. The system platform implements automated least-privilege IAM bindings, Identity-Aware Proxy (IAP) zero-trust tunnels, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### IA-4(9) Identifier Management | Attribute Maintenance and Protection

Maintain the attributes for each uniquely identified individual, device, or service in [Assignment: organization-defined protected central storage].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) identity backends and hypervisor isolation. The system platform implements automated least-privilege IAM bindings, Identity-Aware Proxy (IAP) zero-trust tunnels, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### IA-5 Authenticator Management

Manage system authenticators by:


1. Verifying, as part of the initial authenticator distribution, the identity of the individual, group, role, service, or device receiving the authenticator;


2. Establishing initial authenticator content for any authenticators issued by the organization;


3. Ensuring that authenticators have sufficient strength of mechanism for their intended use;


4. Establishing and implementing administrative procedures for initial authenticator distribution, for lost or compromised or damaged authenticators, and for revoking authenticators;


5. Changing default authenticators prior to first use;


6. Changing or refreshing authenticators [Assignment: organization-defined time period by authenticator type] or when [Assignment: organization-defined events] occur;


7. Protecting authenticator content from unauthorized disclosure and modification;


8. Requiring individuals to take, and having devices implement, specific controls to protect authenticators; and


9. Changing authenticators for group or role accounts when membership to those accounts changes.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) identity backends and hypervisor isolation. The system platform implements automated least-privilege IAM bindings, Identity-Aware Proxy (IAP) zero-trust tunnels, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### IA-5(1) Authenticator Management | Password-based Authentication

For password-based authentication:


1. Maintain a list of commonly-used, expected, or compromised passwords and update the list [Assignment: organization-defined frequency] and when organizational passwords are suspected to have been compromised directly or indirectly;


2. Verify, when users create or update passwords, that the passwords are not found on the list of commonly-used, expected, or compromised passwords in IA-5(1)(a);


3. Transmit passwords only over cryptographically-protected channels;


4. Store passwords using an approved salted key derivation function, preferably using a keyed hash;


5. Require immediate selection of a new password upon account recovery;


6. Allow user selection of long passwords and passphrases, including spaces and all printable characters;


7. Employ automated tools to assist the user in selecting strong password authenticators; and


8. Enforce the following composition and complexity rules: [Assignment: organization-defined composition and complexity rules].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) identity backends and hypervisor isolation. The system platform implements automated least-privilege IAM bindings, Identity-Aware Proxy (IAP) zero-trust tunnels, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### IA-5(2) Authenticator Management | Public Key-based Authentication


1. For public key-based authentication:

  a. Enforce authorized access to the corresponding private key; and

  b. Map the authenticated identity to the account of the individual or group; and


2. When public key infrastructure (PKI) is used:

  c. Validate certificates by constructing and verifying a certification path to an accepted trust anchor, including checking certificate status information; and

  d. Implement a local cache of revocation data to support path discovery and validation.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) identity backends and hypervisor isolation. The system platform implements automated least-privilege IAM bindings, Identity-Aware Proxy (IAP) zero-trust tunnels, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### IA-5(6) Authenticator Management | Protection of Authenticators

Protect authenticators commensurate with the security category of the information to which use of the authenticator permits access.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) identity backends and hypervisor isolation. The system platform implements automated least-privilege IAM bindings, Identity-Aware Proxy (IAP) zero-trust tunnels, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### IA-5(7) Authenticator Management | No Embedded Unencrypted Static Authenticators

Ensure that unencrypted static authenticators are not embedded in applications or other forms of static storage.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) identity backends and hypervisor isolation. The system platform implements automated least-privilege IAM bindings, Identity-Aware Proxy (IAP) zero-trust tunnels, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### IA-5(8) Authenticator Management | Multiple System Accounts

Implement [Assignment: organization-defined security controls] to manage the risk of compromise due to individuals having accounts on multiple systems.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) identity backends and hypervisor isolation. The system platform implements automated least-privilege IAM bindings, Identity-Aware Proxy (IAP) zero-trust tunnels, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### IA-5(13) Authenticator Management | Expiration of Cached Authenticators

Prohibit the use of cached authenticators after [Assignment: organization-defined time period].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) identity backends and hypervisor isolation. The system platform implements automated least-privilege IAM bindings, Identity-Aware Proxy (IAP) zero-trust tunnels, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### IA-5(14) Authenticator Management | Managing Content of PKI Trust Stores

For PKI-based authentication, employ an organization-wide methodology for managing the content of PKI trust stores installed across all platforms, including networks, operating systems, browsers, and applications.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) identity backends and hypervisor isolation. The system platform implements automated least-privilege IAM bindings, Identity-Aware Proxy (IAP) zero-trust tunnels, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### IA-5(16) Authenticator Management | In-person or Trusted External Party Authenticator Issuance

Require that the issuance of [Assignment: organization-defined types of and/or specific authenticators] be conducted [Selection: in person; by a trusted external party] before [Assignment: organization-defined registration authority] with authorization by [Assignment: organization-defined personnel or roles].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) identity backends and hypervisor isolation. The system platform implements automated least-privilege IAM bindings, Identity-Aware Proxy (IAP) zero-trust tunnels, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### IA-6 Authentication Feedback

Obscure feedback of authentication information during the authentication process to protect the information from possible exploitation and use by unauthorized individuals.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). Google LLC manages underlying infrastructure, GCI backends, and physical environment controls for IA-6. |


### IA-7 Cryptographic Module Authentication

Implement mechanisms for authentication to a cryptographic module that meet the requirements of applicable laws, executive orders, directives, policies, regulations, standards, and guidelines for such authentication.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). Google LLC manages underlying infrastructure, GCI backends, and physical environment controls for IA-7. |


### IA-8 Identification and Authentication (Non-Organizational Users)

Uniquely identify and authenticate non-organizational users or processes acting on behalf of non-organizational users.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). Google LLC manages underlying infrastructure, GCI backends, and physical environment controls for IA-8. |


### IA-8 (1) Identification and Authentication (Non-Organizational Users) | Acceptance of PIV Credentials from Other Agencies

Accept and electronically verify Personal Identity Verification-compliant credentials from other federal agencies.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). Google LLC manages underlying infrastructure, GCI backends, and physical environment controls for IA-8. |


### IA-8 (2) Identification and Authentication (Non-Organizational Users) | Acceptance of External Authenticators


1. Accept only external authenticators that are NIST-compliant; and


2. Document and maintain a list of accepted external authenticators.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). Google LLC manages underlying infrastructure, GCI backends, and physical environment controls for IA-8. |


### IA-8 (4) Identification and Authentication (Non-Organizational Users) | Use of Defined Profiles

Conform to the following profiles for identity management [Assignment: organization-defined identity management profiles].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). Google LLC manages underlying infrastructure, GCI backends, and physical environment controls for IA-8. |


### IA-9 Service Identification and Authentication

Uniquely identify and authenticate [Assignment: organization-defined system services and applications] before establishing communications with devices, users, or other services or applications.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) identity backends and hypervisor isolation. The system platform implements automated least-privilege IAM bindings, Identity-Aware Proxy (IAP) zero-trust tunnels, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### IA-10 Adaptive Authentication

Require individuals accessing the system to employ [Assignment: organization-defined supplemental authentication techniques or mechanisms] under specific [Assignment: organization-defined circumstances or situations].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) identity backends and hypervisor isolation. The system platform implements automated least-privilege IAM bindings, Identity-Aware Proxy (IAP) zero-trust tunnels, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### IA-11 Re-Authentication

Require users to re-authenticate when [Assignment: organization-defined circumstances or situations requiring re-authentication].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) identity backends and hypervisor isolation. The system platform implements automated least-privilege IAM bindings, Identity-Aware Proxy (IAP) zero-trust tunnels, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### IA-12 Identity Proofing


1. Identity proof users that require accounts for logical access to systems based on appropriate identity assurance level requirements as specified in applicable standards and guidelines;


2. Resolve user identities to a unique individual; and


3. Collect, validate, and verify identity evidence.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) identity backends and hypervisor isolation. The system platform implements automated least-privilege IAM bindings, Identity-Aware Proxy (IAP) zero-trust tunnels, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### IA-12(1) Identity Proofing | Supervisor Authorization

Require that the registration process to receive an account for logical access includes supervisor or sponsor authorization.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) identity backends and hypervisor isolation. The system platform implements automated least-privilege IAM bindings, Identity-Aware Proxy (IAP) zero-trust tunnels, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### IA-12(2) Identity Proofing | Identity Evidence

Require evidence of individual identification be presented to the registration authority.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) identity backends and hypervisor isolation. The system platform implements automated least-privilege IAM bindings, Identity-Aware Proxy (IAP) zero-trust tunnels, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### IA-12(3) Identity Proofing | Identity Evidence Validation and Verification

Require that the presented identity evidence be validated and verified through [Assignment: organizational defined methods of validation and verification].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) identity backends and hypervisor isolation. The system platform implements automated least-privilege IAM bindings, Identity-Aware Proxy (IAP) zero-trust tunnels, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### IA-12(4) Identify Proofing | In-Person Validation and Verification

Require that the validation and verification of identity evidence be conducted in person before a designated registration authority.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) identity backends and hypervisor isolation. The system platform implements automated least-privilege IAM bindings, Identity-Aware Proxy (IAP) zero-trust tunnels, VPC Service Controls perimeters, and Google Organization Policy constraints. |


### IA-12(5) Identity Proofing | Address Confirmation

Require that a [Selection: registration code; notice of proofing] be delivered through an out-of-band channel to verify the users address (physical or digital) of record.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) identity backends and hypervisor isolation. The system platform implements automated least-privilege IAM bindings, Identity-Aware Proxy (IAP) zero-trust tunnels, VPC Service Controls perimeters, and Google Organization Policy constraints. |


## 2.8 Incident Response


### IR-1  Policy and Procedures


1. Develop, document, and disseminate to [Assignment: organization-defined personnel or roles]:

  a. [Selection (one or more): Organization-level; Mission/business process-level; System-level] incident response policy that:

    - Addresses purpose, scope, roles, responsibilities, management commitment, coordination among organizational entities, and compliance; and

    - Is consistent with applicable laws, executive orders, directives, regulations, policies, standards, and guidelines; and

  b. Procedures to facilitate the implementation of the incident response policy and the associated incident response controls;


2. Designate an [Assignment: organization-defined official] to manage the development, documentation, and dissemination of the incident response policy and procedures; and


3. Review and update the current incident response:

  c. Policy [Assignment: organization-defined frequency] and following [Assignment: organization-defined events]; and

  d. Procedures [Assignment: organization-defined frequency] and following [Assignment: organization-defined events].


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Officer (ISSO) / IR Team & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC Incident Response team and Site Reliability Engineers (SREs) monitor and remediate infrastructure incidents (Inherited). System-level security events are detected via {{ THREAT_DETECTION_ENGINE }} Event Threat Detection, routed through Cloud Pub/Sub, and alerted to the organizational IR team and {{ CSSP_PROVIDER }}. |


### IR-2 Incident Response Training


1. Provide incident response training to system users consistent with assigned roles and responsibilities:

  a. Within [Assignment: organization-defined time period] of assuming an incident response role or responsibility or acquiring system access;

  b. When required by system changes; and

  c. [Assignment: organization-defined frequency] thereafter; and


2. Review and update incident response training content [Assignment: organization-defined frequency] and following [Assignment: organization-defined events].


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Officer (ISSO) / IR Team & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC Incident Response team and Site Reliability Engineers (SREs) monitor and remediate infrastructure incidents (Inherited). System-level security events are detected via {{ THREAT_DETECTION_ENGINE }} Event Threat Detection, routed through Cloud Pub/Sub, and alerted to the organizational IR team and {{ CSSP_PROVIDER }}. |


### IR-2(1) Incident Response Training | Simulated Events

Incorporate simulated events into incident response training to facilitate the required response by personnel in crisis situations.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Officer (ISSO) / IR Team & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC Incident Response team and Site Reliability Engineers (SREs) monitor and remediate infrastructure incidents (Inherited). System-level security events are detected via {{ THREAT_DETECTION_ENGINE }} Event Threat Detection, routed through Cloud Pub/Sub, and alerted to the organizational IR team and {{ CSSP_PROVIDER }}. |


### IR-2(2) Incident Response Training | Automated Training Environments

Provide an incident response training environment using [Assignment: organization-defined automated mechanisms].


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Officer (ISSO) / IR Team & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC Incident Response team and Site Reliability Engineers (SREs) monitor and remediate infrastructure incidents (Inherited). System-level security events are detected via {{ THREAT_DETECTION_ENGINE }} Event Threat Detection, routed through Cloud Pub/Sub, and alerted to the organizational IR team and {{ CSSP_PROVIDER }}. |


### IR-3  Incident Response Testing

Test the effectiveness of the incident response capability for the system [Assignment: organization-defined frequency] using the following tests: [Assignment: organization-defined tests].


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Officer (ISSO) / IR Team & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC Incident Response team and Site Reliability Engineers (SREs) monitor and remediate infrastructure incidents (Inherited). System-level security events are detected via {{ THREAT_DETECTION_ENGINE }} Event Threat Detection, routed through Cloud Pub/Sub, and alerted to the organizational IR team and {{ CSSP_PROVIDER }}. |


### IR-3(2) Incident Response Testing | Coordination with Related Plans

Coordinate incident response testing with organizational elements responsible for related plans.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Officer (ISSO) / IR Team & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC Incident Response team and Site Reliability Engineers (SREs) monitor and remediate infrastructure incidents (Inherited). System-level security events are detected via {{ THREAT_DETECTION_ENGINE }} Event Threat Detection, routed through Cloud Pub/Sub, and alerted to the organizational IR team and {{ CSSP_PROVIDER }}. |


### IR-4  Incident Handling


1. Implement an incident handling capability for incidents that is consistent with the incident response plan and includes preparation, detection and analysis, containment, eradication, and recovery;


2. Coordinate incident handling activities with contingency planning activities;


3. Incorporate lessons learned from ongoing incident handling activities into incident response procedures, training, and testing, and implement the resulting changes accordingly; and


4. Ensure the rigor, intensity, scope, and results of incident handling activities are comparable and predictable across the organization.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Officer (ISSO) / IR Team & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC Incident Response team and Site Reliability Engineers (SREs) monitor and remediate infrastructure incidents (Inherited). System-level security events are detected via {{ THREAT_DETECTION_ENGINE }} Event Threat Detection, routed through Cloud Pub/Sub, and alerted to the organizational IR team and {{ CSSP_PROVIDER }}. |


### IR-4(1) Incident Handling | Automated Incident Handling Processes

Support the incident handling process using [Assignment: organization-defined automated mechanisms].


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Officer (ISSO) / IR Team & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC Incident Response team and Site Reliability Engineers (SREs) monitor and remediate infrastructure incidents (Inherited). System-level security events are detected via {{ THREAT_DETECTION_ENGINE }} Event Threat Detection, routed through Cloud Pub/Sub, and alerted to the organizational IR team and {{ CSSP_PROVIDER }}. |


### IR-4(3) Incident Handling | Continuity of Operations

Identify [Assignment: organization-defined classes of incidents] and take the following actions in response to those incidents to ensure continuation of organizational mission and business functions: [Assignment: organization-defined actions to take in response to classes of incidents].


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Officer (ISSO) / IR Team & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC Incident Response team and Site Reliability Engineers (SREs) monitor and remediate infrastructure incidents (Inherited). System-level security events are detected via {{ THREAT_DETECTION_ENGINE }} Event Threat Detection, routed through Cloud Pub/Sub, and alerted to the organizational IR team and {{ CSSP_PROVIDER }}. |


### IR-4(4) Incident Handling | Information Correlation

Correlate incident information and individual incident responses to achieve an organization-wide perspective on incident awareness and response.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Officer (ISSO) / IR Team & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC Incident Response team and Site Reliability Engineers (SREs) monitor and remediate infrastructure incidents (Inherited). System-level security events are detected via {{ THREAT_DETECTION_ENGINE }} Event Threat Detection, routed through Cloud Pub/Sub, and alerted to the organizational IR team and {{ CSSP_PROVIDER }}. |


### IR-4(6) Incident Handling | Insider Threats

Implement an incident handling capability for incidents involving insider threats.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Officer (ISSO) / IR Team & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC Incident Response team and Site Reliability Engineers (SREs) monitor and remediate infrastructure incidents (Inherited). System-level security events are detected via {{ THREAT_DETECTION_ENGINE }} Event Threat Detection, routed through Cloud Pub/Sub, and alerted to the organizational IR team and {{ CSSP_PROVIDER }}. |


### IR-4(7) Incident Handling | Insider Threats — Intra-organization Coordination

Coordinate an incident handling capability for insider threats that includes the following organizational entities [Assignment: organization-defined entities].


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Officer (ISSO) / IR Team & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC Incident Response team and Site Reliability Engineers (SREs) monitor and remediate infrastructure incidents (Inherited). System-level security events are detected via {{ THREAT_DETECTION_ENGINE }} Event Threat Detection, routed through Cloud Pub/Sub, and alerted to the organizational IR team and {{ CSSP_PROVIDER }}. |


### IR-4(8) Incident Handling | Correlation with External Organizations

Coordinate with [Assignment: organization-defined external organizations] to correlate and share [Assignment: organization-defined incident information] to achieve a cross-organization perspective on incident awareness and more effective incident responses.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Officer (ISSO) / IR Team & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC Incident Response team and Site Reliability Engineers (SREs) monitor and remediate infrastructure incidents (Inherited). System-level security events are detected via {{ THREAT_DETECTION_ENGINE }} Event Threat Detection, routed through Cloud Pub/Sub, and alerted to the organizational IR team and {{ CSSP_PROVIDER }}. |


### IR-4(10) Incident Handling | Supply Chain Coordination

Coordinate incident handling activities involving supply chain events with other organizations involved in the supply chain.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Officer (ISSO) / IR Team & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC Incident Response team and Site Reliability Engineers (SREs) monitor and remediate infrastructure incidents (Inherited). System-level security events are detected via {{ THREAT_DETECTION_ENGINE }} Event Threat Detection, routed through Cloud Pub/Sub, and alerted to the organizational IR team and {{ CSSP_PROVIDER }}. |


### IR-4(11) Incident Handling | Integrated Incident Response Team

Establish and maintain an integrated incident response team that can be deployed to any location identified by the organization in [Assignment: organization-defined time period].


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Officer (ISSO) / IR Team & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC Incident Response team and Site Reliability Engineers (SREs) monitor and remediate infrastructure incidents (Inherited). System-level security events are detected via {{ THREAT_DETECTION_ENGINE }} Event Threat Detection, routed through Cloud Pub/Sub, and alerted to the organizational IR team and {{ CSSP_PROVIDER }}. |


### IR-4(12) Incident Handling | Malicious Code and Forensic Analysis

Analyze malicious code and/or other residual artifacts remaining in the system after the incident.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Officer (ISSO) / IR Team & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC Incident Response team and Site Reliability Engineers (SREs) monitor and remediate infrastructure incidents (Inherited). System-level security events are detected via {{ THREAT_DETECTION_ENGINE }} Event Threat Detection, routed through Cloud Pub/Sub, and alerted to the organizational IR team and {{ CSSP_PROVIDER }}. |


### IR-4(13) Incident Handling | Behavior Analysis

Analyze anomalous or suspected adversarial behavior in or related to [Assignment: organization-defined environments or resources].


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Officer (ISSO) / IR Team & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC Incident Response team and Site Reliability Engineers (SREs) monitor and remediate infrastructure incidents (Inherited). System-level security events are detected via {{ THREAT_DETECTION_ENGINE }} Event Threat Detection, routed through Cloud Pub/Sub, and alerted to the organizational IR team and {{ CSSP_PROVIDER }}. |


### IR-4(14) Incident Handling | Security Operations Center

Establish and maintain a security operations center.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Officer (ISSO) / IR Team & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC Incident Response team and Site Reliability Engineers (SREs) monitor and remediate infrastructure incidents (Inherited). System-level security events are detected via {{ THREAT_DETECTION_ENGINE }} Event Threat Detection, routed through Cloud Pub/Sub, and alerted to the organizational IR team and {{ CSSP_PROVIDER }}. |


### IR-5  Incident Monitoring

Track and document incidents.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Officer (ISSO) / IR Team & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC Incident Response team and Site Reliability Engineers (SREs) monitor and remediate infrastructure incidents (Inherited). System-level security events are detected via {{ THREAT_DETECTION_ENGINE }} Event Threat Detection, routed through Cloud Pub/Sub, and alerted to the organizational IR team and {{ CSSP_PROVIDER }}. |


### IR-5(1) Incident Monitoring | Automated Tracking, Data Collection, and Analysis

Track incidents and collect and analyze incident information using [Assignment: organization-defined automated mechanisms].


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Officer (ISSO) / IR Team & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC Incident Response team and Site Reliability Engineers (SREs) monitor and remediate infrastructure incidents (Inherited). System-level security events are detected via {{ THREAT_DETECTION_ENGINE }} Event Threat Detection, routed through Cloud Pub/Sub, and alerted to the organizational IR team and {{ CSSP_PROVIDER }}. |


### IR-6  Incident Reporting


1. Require personnel to report suspected incidents to the organizational incident response capability within [Assignment: organization-defined time period]; and


2. Report incident information to [Assignment: organization-defined authorities].


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Officer (ISSO) / IR Team & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC Incident Response team and Site Reliability Engineers (SREs) monitor and remediate infrastructure incidents (Inherited). System-level security events are detected via {{ THREAT_DETECTION_ENGINE }} Event Threat Detection, routed through Cloud Pub/Sub, and alerted to the organizational IR team and {{ CSSP_PROVIDER }}. |


### IR-6(1) Incident Reporting | Automated Reporting

Report incidents using [Assignment: organization-defined automated mechanisms].


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Officer (ISSO) / IR Team & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC Incident Response team and Site Reliability Engineers (SREs) monitor and remediate infrastructure incidents (Inherited). System-level security events are detected via {{ THREAT_DETECTION_ENGINE }} Event Threat Detection, routed through Cloud Pub/Sub, and alerted to the organizational IR team and {{ CSSP_PROVIDER }}. |


### IR-6(2) Incident Reporting | Vulnerabilities Related to Incidents

Report system vulnerabilities associated with reported incidents to [Assignment: organization-defined personnel or roles].


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Officer (ISSO) / IR Team & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC Incident Response team and Site Reliability Engineers (SREs) monitor and remediate infrastructure incidents (Inherited). System-level security events are detected via {{ THREAT_DETECTION_ENGINE }} Event Threat Detection, routed through Cloud Pub/Sub, and alerted to the organizational IR team and {{ CSSP_PROVIDER }}. |


### IR-6(3) Incident Reporting | Supply Chain Coordination

Provide incident information to the provider of the product or service and other organizations involved in the supply chain or supply chain governance for systems or system components related to the incident.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Officer (ISSO) / IR Team & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC Incident Response team and Site Reliability Engineers (SREs) monitor and remediate infrastructure incidents (Inherited). System-level security events are detected via {{ THREAT_DETECTION_ENGINE }} Event Threat Detection, routed through Cloud Pub/Sub, and alerted to the organizational IR team and {{ CSSP_PROVIDER }}. |


### IR-7  Incident Response Assistance

Provide an incident response support resource, integral to the organizational incident response capability, that offers advice and assistance to users of the system for the handling and reporting of incidents.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Officer (ISSO) / IR Team & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC Incident Response team and Site Reliability Engineers (SREs) monitor and remediate infrastructure incidents (Inherited). System-level security events are detected via {{ THREAT_DETECTION_ENGINE }} Event Threat Detection, routed through Cloud Pub/Sub, and alerted to the organizational IR team and {{ CSSP_PROVIDER }}. |


### IR-7(1) Incident Response Assistance | Automation Support for Availability of Information and Support

Increase the availability of incident response information and support using [Assignment: organization-defined automated mechanisms].


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Officer (ISSO) / IR Team & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC Incident Response team and Site Reliability Engineers (SREs) monitor and remediate infrastructure incidents (Inherited). System-level security events are detected via {{ THREAT_DETECTION_ENGINE }} Event Threat Detection, routed through Cloud Pub/Sub, and alerted to the organizational IR team and {{ CSSP_PROVIDER }}. |


### IR-7(2) Incident Response Assistance | Coordination with External Providers


1. Establish a direct, cooperative relationship between its incident response capability and external providers of system protection capability; and


2. Identify organizational incident response team members to the external providers.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Officer (ISSO) / IR Team & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC Incident Response team and Site Reliability Engineers (SREs) monitor and remediate infrastructure incidents (Inherited). System-level security events are detected via {{ THREAT_DETECTION_ENGINE }} Event Threat Detection, routed through Cloud Pub/Sub, and alerted to the organizational IR team and {{ CSSP_PROVIDER }}. |


### IR-8 Incident Response Plan


1. Develop an incident response plan that:

  a. Provides the organization with a roadmap for implementing its incident response capability;

  b. Describes the structure and organization of the incident response capability;

  c. Provides a high-level approach for how the incident response capability fits into the overall organization;

  d. Meets the unique requirements of the organization, which relate to mission, size, structure, and functions;

  e. Defines reportable incidents;

  f. Provides metrics for measuring the incident response capability within the organization;

  g. Defines the resources and management support needed to effectively maintain and mature an incident response capability;

  h. Addresses the sharing of incident information;

  i. Is reviewed and approved by [Assignment: organization-defined personnel or roles] [Assignment: organization-defined frequency]; and

  j. Explicitly designates responsibility for incident response to [Assignment: organization-defined entities, personnel, or roles].


2. Distribute copies of the incident response plan to [Assignment: organization-defined incident response personnel (identified by name and/or by role) and organizational elements];


3. Update the incident response plan to address system and organizational changes or problems encountered during plan implementation, execution, or testing;


4. Communicate incident response plan changes to [Assignment: organization-defined incident response personnel (identified by name and/or by role) and organizational elements]; and


5. Protect the incident response plan from unauthorized disclosure and modification.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Officer (ISSO) / IR Team & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC Incident Response team and Site Reliability Engineers (SREs) monitor and remediate infrastructure incidents (Inherited). System-level security events are detected via {{ THREAT_DETECTION_ENGINE }} Event Threat Detection, routed through Cloud Pub/Sub, and alerted to the organizational IR team and {{ CSSP_PROVIDER }}. |


### IR-9 Information Spillage Response

Respond to information spills by:


1. Assigning [Assignment: organization-defined personnel or roles] with responsibility for responding to information spills;


2. Identifying the specific information involved in the system contamination;


3. Alerting [Assignment: organization-defined personnel or roles] of the information spill using a method of communication not associated with the spill;


4. Isolating the contaminated system or system component;


5. Eradicating the information from the contaminated system or component;


6. Identifying other systems or system components that may have been subsequently contaminated; and


7. Performing the following additional actions: [Assignment: organization-defined actions].


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Officer (ISSO) / IR Team & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC Incident Response team and Site Reliability Engineers (SREs) monitor and remediate infrastructure incidents (Inherited). System-level security events are detected via {{ THREAT_DETECTION_ENGINE }} Event Threat Detection, routed through Cloud Pub/Sub, and alerted to the organizational IR team and {{ CSSP_PROVIDER }}. |


### IR-9(2) Information Spillage Response | Training

Provide information spillage response training [Assignment: organization-defined frequency].


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Officer (ISSO) / IR Team & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC Incident Response team and Site Reliability Engineers (SREs) monitor and remediate infrastructure incidents (Inherited). System-level security events are detected via {{ THREAT_DETECTION_ENGINE }} Event Threat Detection, routed through Cloud Pub/Sub, and alerted to the organizational IR team and {{ CSSP_PROVIDER }}. |


### IR-9(3) Information Spillage Response | Exposure to Unauthorized Personnel

Implement the following procedures to ensure that organizational personnel impacted by information spills can continue to carry out assigned tasks while contaminated systems are undergoing corrective actions: [Assignment: organization-defined procedures].


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Officer (ISSO) / IR Team & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC Incident Response team and Site Reliability Engineers (SREs) monitor and remediate infrastructure incidents (Inherited). System-level security events are detected via {{ THREAT_DETECTION_ENGINE }} Event Threat Detection, routed through Cloud Pub/Sub, and alerted to the organizational IR team and {{ CSSP_PROVIDER }}. |


### IR-9(4) Information Spillage Response | Exposure to Unauthorized Personnel

Employ the following controls for personnel exposed to information not within assigned access authorizations: [Assignment: organization-defined controls].


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Officer (ISSO) / IR Team & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC Incident Response team and Site Reliability Engineers (SREs) monitor and remediate infrastructure incidents (Inherited). System-level security events are detected via {{ THREAT_DETECTION_ENGINE }} Event Threat Detection, routed through Cloud Pub/Sub, and alerted to the organizational IR team and {{ CSSP_PROVIDER }}. |


## 2.9 Maintenance


### MA-1 Policy and Procedures


1. Develop, document, and disseminate to [Assignment: organization-defined personnel or roles]:

  a. [Selection (one or more): Organization-level; Mission/business process-level; System-level] maintenance policy that:

    - Addresses purpose, scope, roles, responsibilities, management commitment, coordination among organizational entities, and compliance; and

    - Is consistent with applicable laws, executive orders, directives, regulations, policies, standards, and guidelines; and

  b. Procedures to facilitate the implementation of the maintenance policy and the associated maintenance controls;


2. Designate an [Assignment: organization-defined official] to manage the development, documentation, and dissemination of the maintenance policy and procedures; and


3. Review and update the current maintenance:

  c. Policy [Assignment: organization-defined frequency] and following [Assignment: organization-defined events]; and

  d. Procedures [Assignment: organization-defined frequency] and following [Assignment: organization-defined events].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). Google LLC manages underlying infrastructure, GCI backends, and physical environment controls for MA-1. |


### MA-2 Controlled Maintenance


1. Schedule, document, and review records of maintenance, repair, and replacement on system components in accordance with manufacturer or vendor specifications and/or organizational requirements;


2. Approve and monitor all maintenance activities, whether performed on site or remotely and whether the system or system components are serviced on site or removed to another location;


3. Require that [Assignment: organization-defined personnel or roles] explicitly approve the removal of the system or system components from organizational facilities for off-site maintenance, repair, or replacement;


4. Sanitize equipment to remove the following information from associated media prior to removal from organizational facilities for off-site maintenance, repair, or replacement: [Assignment: organization-defined information];


5. Check all potentially impacted controls to verify that the controls are still functioning properly following maintenance, repair, or replacement actions; and


6. Include the following information in organizational maintenance records: [Assignment: organization-defined information].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). Google LLC manages underlying infrastructure, GCI backends, and physical environment controls for MA-2. |


### MA-2(2) Controlled Maintenance | Automated Maintenance Activities


1. Schedule, conduct, and document maintenance, repair, and replacement actions for the system using [Assignment: organization-defined automated mechanisms]; and


2. Produce up-to date, accurate, and complete records of all maintenance, repair, and replacement actions requested, scheduled, in process, and completed.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). Google LLC manages underlying infrastructure, GCI backends, and physical environment controls for MA-2(2). |


### MA-3 Maintenance Tools


1. Approve, control, and monitor the use of system maintenance tools; and


2. Review previously approved system maintenance tools [Assignment: organization-defined frequency].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). Google LLC manages underlying infrastructure, GCI backends, and physical environment controls for MA-3. |


### MA-3(1) Maintenance Tools | Inspect Tools

Inspect the maintenance tools used by maintenance personnel for improper or unauthorized modifications.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). Google LLC manages underlying infrastructure, GCI backends, and physical environment controls for MA-3(1). |


### MA-3(2) Maintenance Tools | Inspect Media

Check media containing diagnostic and test programs for malicious code before the media are used in the system.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). Google LLC manages underlying infrastructure, GCI backends, and physical environment controls for MA-3(2). |


### MA-3(3) Maintenance Tools | Prevent Unauthorized Removal

Prevent the removal of maintenance equipment containing organizational information by:


1. Verifying that there is no organizational information contained on the equipment;


2. Sanitizing or destroying the equipment;


3. Retaining the equipment within the facility; or


4. Obtaining an exemption from [Assignment: organization-defined personnel or roles] explicitly authorizing removal of the equipment from the facility.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). Google LLC manages underlying infrastructure, GCI backends, and physical environment controls for MA-3(3). |


### MA-3(4) Maintenance Tools | Restricted Tool Use

Restrict the use of maintenance tools to authorized personnel only.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). Google LLC manages underlying infrastructure, GCI backends, and physical environment controls for MA-3(4). |


### MA-3(5) Maintenance Tools | Execution with Privilege

Monitor the use of maintenance tools that execute with increased privilege.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). Google LLC manages underlying infrastructure, GCI backends, and physical environment controls for MA-3(5). |


### MA-3(6) Maintenance Tools | Software Updates and Patches

Inspect maintenance tools to ensure the latest software updates and patches are installed.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). Google LLC manages underlying infrastructure, GCI backends, and physical environment controls for MA-3(6). |


### MA-4 Non-Local Maintenance


1. Approve and monitor nonlocal maintenance and diagnostic activities;


2. Allow the use of nonlocal maintenance and diagnostic tools only as consistent with organizational policy and documented in the security plan for the system;


3. Employ strong authentication in the establishment of nonlocal maintenance and diagnostic sessions;


4. Maintain records for nonlocal maintenance and diagnostic activities; and


5. Terminate session and network connections when nonlocal maintenance is completed.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). Google LLC manages underlying infrastructure, GCI backends, and physical environment controls for MA-4. |


### MA-4(1) Non-Local Maintenance | Logging and Review


1. Log [Assignment: organization-defined audit events] for nonlocal maintenance and diagnostic sessions; and


2. Review the audit records of the maintenance and diagnostic sessions to detect anomalous behavior.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). Google LLC manages underlying infrastructure, GCI backends, and physical environment controls for MA-4(1). |


### MA-4(3) Non-Local Maintenance | Comparable Security and Sanitization


1. Require that nonlocal maintenance and diagnostic services be performed from a system that implements a security capability comparable to the capability implemented on the system being serviced; or


2. Remove the component to be serviced from the system prior to nonlocal maintenance or diagnostic services; sanitize the component (for organizational information); and after the service is performed, inspect and sanitize the component (for potentially malicious software) before reconnecting the component to the system.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). Google LLC manages underlying infrastructure, GCI backends, and physical environment controls for MA-4(3). |


### MA-4(4) Non-Local Maintenance | Authentication and Separation of Maintenance Sessions

Protect nonlocal maintenance sessions by:


1. Employing [Assignment: organization-defined authenticators that are replay resistant]; and


2. Separating the maintenance sessions from other network sessions with the system by either:

  a. Physically separated communications paths; or

  b. Logically separated communications paths.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). Google LLC manages underlying infrastructure, GCI backends, and physical environment controls for MA-4(4). |


### MA-4(6) Non-Local Maintenance | Cryptographic Protection

Implement the following cryptographic mechanisms to protect the integrity and confidentiality of nonlocal maintenance and diagnostic communications: [Assignment: organization-defined cryptographic mechanisms].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). Google LLC manages underlying infrastructure, GCI backends, and physical environment controls for MA-4(6). |


### MA-4(7) Non-Local Maintenance | Disconnect Verification

Verify session and network connection termination after the completion of nonlocal maintenance and diagnostic sessions.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). Google LLC manages underlying infrastructure, GCI backends, and physical environment controls for MA-4(7). |


### MA-5 Maintenance Personnel


1. Establish a process for maintenance personnel authorization and maintain a list of authorized maintenance organizations or personnel;


2. Verify that non-escorted personnel performing maintenance on the system possess the required access authorizations; and


3. Designate organizational personnel with required access authorizations and technical competence to supervise the maintenance activities of personnel who do not possess the required access authorizations.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). Google LLC manages underlying infrastructure, GCI backends, and physical environment controls for MA-5. |


### MA-5(1) Maintenance Personnel | Individuals Without Appropriate Access


1. Implement procedures for the use of maintenance personnel that lack appropriate security clearances or are not U.S. citizens, that include the following requirements:

> [!IMPORTANT]
> <mark style="background-color: #fff9c4; color: #b71c1c; font-weight: bold; padding: 2px 6px; border-radius: 4px;">⚠️ RMF TEAM ACTION REQUIRED: Verify and update operational procedure or contact details in this section.</mark>
>   a. Maintenance personnel who do not have needed access authorizations, clearances, or formal access approvals are escorted and supervised during the performance of maintenance and diagnostic activities on the system by approved organizational personnel who are fully cleared, have appropriate access authorizations, and are technically qualified; and

  b. Prior to initiating maintenance or diagnostic activities by personnel who do not have needed access authorizations, clearances or formal access approvals, all volatile information storage components within the system are sanitized and all nonvolatile storage media are removed or physically disconnected from the system and secured; and


2. Develop and implement [Assignment: organization-defined alternate controls] in the event a system component cannot be sanitized, removed, or disconnected from the system.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). Google LLC manages underlying infrastructure, GCI backends, and physical environment controls for MA-5(1). |


### MA-6 Timely Maintenance

Obtain maintenance support and/or spare parts for [Assignment: organization-defined system components] within [Assignment: organization-defined time period] of failure.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). Google LLC manages underlying infrastructure, GCI backends, and physical environment controls for MA-6. |


### MA-6(1) Timely Maintenance | Preventative Maintenance

Perform preventive maintenance on [Assignment: organization-defined system components] at [Assignment: organization-defined time intervals].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). Google LLC manages underlying infrastructure, GCI backends, and physical environment controls for MA-6(1). |


## 2.10 Media Protection


### MP-1 Policy and Procedures


1. Develop, document, and disseminate to [Assignment: organization-defined personnel or roles]:

  a. [Selection (one or more): Organization-level; Mission/business process-level; System-level] media protection policy that:

    - Addresses purpose, scope, roles, responsibilities, management commitment, coordination among organizational entities, and compliance; and

    - Is consistent with applicable laws, executive orders, directives, regulations, policies, standards, and guidelines; and

  b. Procedures to facilitate the implementation of the media protection policy and the associated media protection controls;


2. Designate an [Assignment: organization-defined official] to manage the development, documentation, and dissemination of the media protection policy and procedures; and


3. Review and update the current media protection:

  c. Policy [Assignment: organization-defined frequency] and following [Assignment: organization-defined events]; and

  d. Procedures [Assignment: organization-defined frequency] and following [Assignment: organization-defined events].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for physical media sanitization and disk shredding in accordance with NIST SP 800-88 Rev. 1 Clear/Destroy guidelines. Digital media within customer VPCs is protected using FIPS 140-3 validated BoringCrypto modules and Cloud KMS Customer-Managed Encryption Keys (CMEK AES-256). |


### MP-2 Media Access

Restrict access to [Assignment: organization-defined types of digital and/or non-digital media] to [Assignment: organization-defined personnel or roles].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for physical media sanitization and disk shredding in accordance with NIST SP 800-88 Rev. 1 Clear/Destroy guidelines. Digital media within customer VPCs is protected using FIPS 140-3 validated BoringCrypto modules and Cloud KMS Customer-Managed Encryption Keys (CMEK AES-256). |


### MP-3 Media Marking


1. Mark system media indicating the distribution limitations, handling caveats, and applicable security markings (if any) of the information; and


2. Exempt [Assignment: organization-defined types of system media] from marking if the media remain within [Assignment: organization-defined controlled areas].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for physical media sanitization and disk shredding in accordance with NIST SP 800-88 Rev. 1 Clear/Destroy guidelines. Digital media within customer VPCs is protected using FIPS 140-3 validated BoringCrypto modules and Cloud KMS Customer-Managed Encryption Keys (CMEK AES-256). |


### MP-4 Media Storage


1. Physically control and securely store [Assignment: organization-defined types of digital and/or non-digital media] within [Assignment: organization-defined controlled areas]; and


2. Protect system media types defined in MP-4a until the media are destroyed or sanitized using approved equipment, techniques, and procedures.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for physical media sanitization and disk shredding in accordance with NIST SP 800-88 Rev. 1 Clear/Destroy guidelines. Digital media within customer VPCs is protected using FIPS 140-3 validated BoringCrypto modules and Cloud KMS Customer-Managed Encryption Keys (CMEK AES-256). |


### MP-5 Media Transport


1. Protect and control [Assignment: organization-defined types of system media] during transport outside of controlled areas using [Assignment: organization-defined controls];


2. Maintain accountability for system media during transport outside of controlled areas;


3. Document activities associated with the transport of system media; and


4. Restrict the activities associated with the transport of system media to authorized personnel.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for physical media sanitization and disk shredding in accordance with NIST SP 800-88 Rev. 1 Clear/Destroy guidelines. Digital media within customer VPCs is protected using FIPS 140-3 validated BoringCrypto modules and Cloud KMS Customer-Managed Encryption Keys (CMEK AES-256). |


### MP-6 Media Sanitization


1. Sanitize [Assignment: organization-defined system media] prior to disposal, release out of organizational control, or release for reuse using [Assignment: organization-defined sanitization techniques and procedures]; and


2. Employ sanitization mechanisms with the strength and integrity commensurate with the security category or classification of the information.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for physical media sanitization and disk shredding in accordance with NIST SP 800-88 Rev. 1 Clear/Destroy guidelines. Digital media within customer VPCs is protected using FIPS 140-3 validated BoringCrypto modules and Cloud KMS Customer-Managed Encryption Keys (CMEK AES-256). |


### MP-6(1) Media Sanitization | Review, Approve, Track, Document, and Verify

Review, approve, track, document, and verify media sanitization and disposal actions.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for physical media sanitization and disk shredding in accordance with NIST SP 800-88 Rev. 1 Clear/Destroy guidelines. Digital media within customer VPCs is protected using FIPS 140-3 validated BoringCrypto modules and Cloud KMS Customer-Managed Encryption Keys (CMEK AES-256). |


### MP-6(2) Media Sanitization | Equipment Testing

Test sanitization equipment and procedures [Assignment: organization-defined frequency] to ensure that the intended sanitization is being achieved.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for physical media sanitization and disk shredding in accordance with NIST SP 800-88 Rev. 1 Clear/Destroy guidelines. Digital media within customer VPCs is protected using FIPS 140-3 validated BoringCrypto modules and Cloud KMS Customer-Managed Encryption Keys (CMEK AES-256). |


### MP-6(3) Media Sanitization | Non-Destructive Techniques

Apply nondestructive sanitization techniques to portable storage devices prior to connecting such devices to the system under the following circumstances: [Assignment: organization-defined circumstances requiring sanitization of portable storage devices].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for physical media sanitization and disk shredding in accordance with NIST SP 800-88 Rev. 1 Clear/Destroy guidelines. Digital media within customer VPCs is protected using FIPS 140-3 validated BoringCrypto modules and Cloud KMS Customer-Managed Encryption Keys (CMEK AES-256). |


### MP-7 Media Use

1. [Selection: Restrict; Prohibit] the use of [Assignment: organization-defined types of system media] on [Assignment: organization-defined systems or system components] using [Assignment: organization-defined controls]; and


2. Prohibit the use of portable storage devices in organizational systems when such devices have no identifiable owner.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for physical media sanitization and disk shredding in accordance with NIST SP 800-88 Rev. 1 Clear/Destroy guidelines. Digital media within customer VPCs is protected using FIPS 140-3 validated BoringCrypto modules and Cloud KMS Customer-Managed Encryption Keys (CMEK AES-256). |


## 2.11 Physical and Environmental Protections


### PE-1 Policy and Procedures


1. Develop, document, and disseminate to [Assignment: organization-defined personnel or roles]:

  a. [Selection (one or more): Organization-level; Mission/business process-level; System-level] physical and environmental protection policy that:

    - Addresses purpose, scope, roles, responsibilities, management commitment, coordination among organizational entities, and compliance; and

    - Is consistent with applicable laws, executive orders, directives, regulations, policies, standards, and guidelines; and

  b. Procedures to facilitate the implementation of the physical and environmental protection policy and the associated physical and environmental protection controls;


2. Designate an [Assignment: organization-defined official] to manage the development, documentation, and dissemination of the physical and environmental protection policy and procedures; and


3. Review and update the current physical and environmental protection:

  c. Policy [Assignment: organization-defined frequency] and following [Assignment: organization-defined events]; and

  d. Procedures [Assignment: organization-defined frequency] and following [Assignment: organization-defined events].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). Google LLC manages underlying infrastructure, GCI backends, and physical environment controls for PE-1. |


### PE-2 Physical Access Authorizations


1. Develop, approve, and maintain a list of individuals with authorized access to the facility where the system resides;


2. Issue authorization credentials for facility access;


3. Review the access list detailing authorized facility access by individuals [Assignment: organization-defined frequency]; and


4. Remove individuals from the facility access list when access is no longer required.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). Google LLC manages underlying infrastructure, GCI backends, and physical environment controls for PE-2. |


### PE-3 Physical Access Control


1. Enforce physical access authorizations at [Assignment: organization-defined entry and exit points to the facility where the system resides] by:

> [!IMPORTANT]
> <mark style="background-color: #fff9c4; color: #b71c1c; font-weight: bold; padding: 2px 6px; border-radius: 4px;">⚠️ RMF TEAM ACTION REQUIRED: Verify and update operational procedure or contact details in this section.</mark>
>   a. Verifying individual access authorizations before granting access to the facility; and

> [!IMPORTANT]
> <mark style="background-color: #fff9c4; color: #b71c1c; font-weight: bold; padding: 2px 6px; border-radius: 4px;">⚠️ RMF TEAM ACTION REQUIRED: Verify and update operational procedure or contact details in this section.</mark>
>   b. Controlling ingress and egress to the facility using [Selection (one or more): [Assignment: organization-defined physical access control systems or devices]; guards];


2. Maintain physical access audit logs for [Assignment: organization-defined entry or exit points];


3. Control access to areas within the facility designated as publicly accessible by implementing the following controls: [Assignment: organization-defined physical access controls];


4. Escort visitors and control visitor activity [Assignment: organization-defined circumstances requiring visitor escorts and control of visitor activity];


5. Secure keys, combinations, and other physical access devices;


6. Inventory [Assignment: organization-defined physical access devices] every [Assignment: organization-defined frequency]; and


7. Change combinations and keys [Assignment: organization-defined frequency] and/or when keys are lost, combinations are compromised, or when individuals possessing the keys or combinations are transferred or terminated.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). Google LLC manages underlying infrastructure, GCI backends, and physical environment controls for PE-3. |


### PE-3(1) Physical Access Control | System Access

> [!IMPORTANT]
> <mark style="background-color: #fff9c4; color: #b71c1c; font-weight: bold; padding: 2px 6px; border-radius: 4px;">⚠️ RMF TEAM ACTION REQUIRED: Verify and update operational procedure or contact details in this section.</mark>
> Enforce physical access authorizations to the system in addition to the physical access controls for the facility at [Assignment: organization-defined physical spaces containing one or more components of the system].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). Google LLC manages underlying infrastructure, GCI backends, and physical environment controls for PE-3(1). |


### PE-4 Access Control for Transmission

Control physical access to [Assignment: organization-defined system distribution and transmission lines] within organizational facilities using [Assignment: organization-defined security controls].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). Google LLC manages underlying infrastructure, GCI backends, and physical environment controls for PE-4. |


### PE-5 Access Control for Output Devices

Control physical access to output from [Assignment: organization-defined output devices] to prevent unauthorized individuals from obtaining the output.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). Google LLC manages underlying infrastructure, GCI backends, and physical environment controls for PE-5. |


### PE-6 Monitoring Physical Access


1. Monitor physical access to the facility where the system resides to detect and respond to physical security incidents;


2. Review physical access logs [Assignment: organization-defined frequency] and upon occurrence of [Assignment: organization-defined events or potential indications of events]; and


3. Coordinate results of reviews and investigations with the organizational incident response capability.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). Google LLC manages underlying infrastructure, GCI backends, and physical environment controls for PE-6. |


### PE-6(1) Monitoring Physical Access | Intrusion Alarms and Surveillance Equipment

> [!IMPORTANT]
> <mark style="background-color: #fff9c4; color: #b71c1c; font-weight: bold; padding: 2px 6px; border-radius: 4px;">⚠️ RMF TEAM ACTION REQUIRED: Verify and update operational procedure or contact details in this section.</mark>
> Monitor physical access to the facility where the system resides using physical intrusion alarms and surveillance equipment.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). Google LLC manages underlying infrastructure, GCI backends, and physical environment controls for PE-6(1). |


### PE-6(4) Monitoring Physical Access | Monitoring Physical Access to Systems

> [!IMPORTANT]
> <mark style="background-color: #fff9c4; color: #b71c1c; font-weight: bold; padding: 2px 6px; border-radius: 4px;">⚠️ RMF TEAM ACTION REQUIRED: Verify and update operational procedure or contact details in this section.</mark>
> Monitor physical access to the system in addition to the physical access monitoring of the facility at [Assignment: organization-defined physical spaces containing one or more components of the system].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). Google LLC manages underlying infrastructure, GCI backends, and physical environment controls for PE-6(4). |


### PE-8 Visitor Access Records


1. Maintain visitor access records to the facility where the system resides for [Assignment: organization-defined time period];


2. Review visitor access records [Assignment: organization-defined frequency]; and


3. Report anomalies in visitor access records to [Assignment: organization-defined personnel].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). Google LLC manages underlying infrastructure, GCI backends, and physical environment controls for PE-8. |


### PE-8(1) Visitor Access Records | Automated Records Maintenance and Review

Maintain and review visitor access records using [Assignment: organization-defined automated mechanisms].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). Google LLC manages underlying infrastructure, GCI backends, and physical environment controls for PE-8(1). |


### PE-8(3) Visitor Access Records | Limit Personally Identifiable Information Elements

Limit personally identifiable information contained in visitor access records to the following elements identified in the privacy risk assessment: [Assignment: organization-defined elements].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). Google LLC manages underlying infrastructure, GCI backends, and physical environment controls for PE-8(3). |


### PE-9 Power Equipment and Cabling

Protect power equipment and power cabling for the system from damage and destruction.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). Google LLC manages underlying infrastructure, GCI backends, and physical environment controls for PE-9. |


### PE-10 Emergency Shutoff


1. Provide the capability of shutting off power to [Assignment: organization-defined system or individual system components] in emergency situations;


2. Place emergency shutoff switches or devices in [Assignment: organization-defined location by system or system component] to facilitate access for authorized personnel; and


3. Protect emergency power shutoff capability from unauthorized activation.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). Google LLC manages underlying infrastructure, GCI backends, and physical environment controls for PE-10. |


### PE-11 Emergency Power

Provide an uninterruptible power supply to facilitate [Selection (one or more): an orderly shutdown of the system; transition of the system to long-term alternate power] in the event of a primary power source loss.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). Google LLC manages underlying infrastructure, GCI backends, and physical environment controls for PE-11. |


### PE-11(1) Emergency Power | Alternate Power Supply - Minimal Operational Capability

Provide an alternate power supply for the system that is activated [Selection: manually; automatically] and that can maintain minimally required operational capability in the event of an extended loss of the primary power source.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). Google LLC manages underlying infrastructure, GCI backends, and physical environment controls for PE-11(1). |


### PE-12 Emergency Lighting

> [!IMPORTANT]
> <mark style="background-color: #fff9c4; color: #b71c1c; font-weight: bold; padding: 2px 6px; border-radius: 4px;">⚠️ RMF TEAM ACTION REQUIRED: Verify and update operational procedure or contact details in this section.</mark>
> Employ and maintain automatic emergency lighting for the system that activates in the event of a power outage or disruption and that covers emergency exits and evacuation routes within the facility.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). Google LLC manages underlying infrastructure, GCI backends, and physical environment controls for PE-12. |


### PE-13 Fire Protection

Employ and maintain fire detection and suppression systems that are supported by an independent energy source.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). Google LLC manages underlying infrastructure, GCI backends, and physical environment controls for PE-13. |


### PE-13(1) Fire Protection | Detection Systems - Automatic Activation and Notification

Employ fire detection systems that activate automatically and notify [Assignment: organization-defined personnel or roles] and [Assignment: organization-defined emergency responders] in the event of a fire.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). Google LLC manages underlying infrastructure, GCI backends, and physical environment controls for PE-13(1). |


### PE-13(2) Fire Protection | Suppression Systems - Automatic Activation and Notification


1. Employ fire suppression systems that activate automatically and notify [Assignment: organization-defined personnel or roles] and [Assignment: organization-defined emergency responders]; and


2. Employ an automatic fire suppression capability when the facility is not staffed on a continuous basis.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). Google LLC manages underlying infrastructure, GCI backends, and physical environment controls for PE-13(2). |


### PE-13(4) Fire Protection | Inspections

> [!IMPORTANT]
> <mark style="background-color: #fff9c4; color: #b71c1c; font-weight: bold; padding: 2px 6px; border-radius: 4px;">⚠️ RMF TEAM ACTION REQUIRED: Verify and update operational procedure or contact details in this section.</mark>
> Ensure that the facility undergoes [Assignment: organization-defined frequency] fire protection inspections by authorized and qualified inspectors and identified deficiencies are resolved within [Assignment: organization-defined time period].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). Google LLC manages underlying infrastructure, GCI backends, and physical environment controls for PE-13(4). |


### PE-14 Environmental Controls


1. Maintain [Selection (one or more): temperature; humidity; pressure; radiation; [Assignment: organization-defined environmental control]] levels within the facility where the system resides at [Assignment: organization-defined acceptable levels]; and


2. Monitor environmental control levels [Assignment: organization-defined frequency].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). Google LLC manages underlying infrastructure, GCI backends, and physical environment controls for PE-14. |


### PE-15 Water Damage Protection

Protect the system from damage resulting from water leakage by providing master shutoff or isolation valves that are accessible, working properly, and known to key personnel.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). Google LLC manages underlying infrastructure, GCI backends, and physical environment controls for PE-15. |


### PE-15(1) Water Damage Protection | Automation Support

Detect the presence of water near the system and alert [Assignment: organization-defined personnel or roles] using [Assignment: organization-defined automated mechanisms].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). Google LLC manages underlying infrastructure, GCI backends, and physical environment controls for PE-15(1). |


### PE-16 Delivery and Removal


1. Authorize and control [Assignment: organization-defined types of system components] entering and exiting the facility; and


2. Maintain records of the system components.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). Google LLC manages underlying infrastructure, GCI backends, and physical environment controls for PE-16. |


### PE-17 Alternate Work Site


1. Determine and document the [Assignment: organization-defined alternate work sites] allowed for use by employees;


2. Employ the following controls at alternate work sites: [Assignment: organization-defined controls];


3. Assess the effectiveness of controls at alternate work sites; and


4. Provide a means for employees to communicate with information security and privacy personnel in case of incidents.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). Google LLC manages underlying infrastructure, GCI backends, and physical environment controls for PE-17. |


### PE-18 Location of System Components

> [!IMPORTANT]
> <mark style="background-color: #fff9c4; color: #b71c1c; font-weight: bold; padding: 2px 6px; border-radius: 4px;">⚠️ RMF TEAM ACTION REQUIRED: Verify and update operational procedure or contact details in this section.</mark>
> Position system components within the facility to minimize potential damage from [Assignment: organization-defined physical and environmental hazards] and to minimize the opportunity for unauthorized access.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). Google LLC manages underlying infrastructure, GCI backends, and physical environment controls for PE-18. |


### PE-22 Component Marking

Mark [Assignment: organization-defined system hardware components] indicating the impact level or classification level of the information permitted to be processed, stored, or transmitted by the hardware component.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). Google LLC manages underlying infrastructure, GCI backends, and physical environment controls for PE-22. |


### PE-23 Facility Location


1. Plan the location or site of the facility where the system resides considering physical and environmental hazards; and


2. For existing facilities, consider the physical and environmental hazards in the organizational risk management strategy.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). Google LLC manages underlying infrastructure, GCI backends, and physical environment controls for PE-23. |


## 2.12 Planning


### PL-1 Policy and Procedures


1. Develop, document, and disseminate to [Assignment: organization-defined personnel or roles]:

  a. [Selection (one or more): Organization-level; Mission/business process-level; System-level] planning policy that:

    - Addresses purpose, scope, roles, responsibilities, management commitment, coordination among organizational entities, and compliance; and

    - Is consistent with applicable laws, executive orders, directives, regulations, policies, standards, and guidelines; and

  b. Procedures to facilitate the implementation of the planning policy and the associated planning controls;


2. Designate an [Assignment: organization-defined official] to manage the development, documentation, and dissemination of the planning policy and procedures; and


3. Review and update the current planning:

  c. Policy [Assignment: organization-defined frequency] and following [Assignment: organization-defined events]; and

  d. Procedures [Assignment: organization-defined frequency] and following [Assignment: organization-defined events].


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Owner & ISSO |
| **Implementation Status (check all that apply)**:<br>- [x] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [ ] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>The System Security Plan (SSP), System Architecture documentation, and NIST SP 800-53 control baselines are developed, maintained, and reviewed periodically by the System Owner and ISSO. |


### PL-2 System Security and Privacy Plans


1. Develop security and privacy plans for the system that:

  a. Are consistent with the organization’s enterprise architecture;

  b. Explicitly define the constituent system components;

  c. Describe the operational context of the system in terms of mission and business processes;

  d. Identify the individuals that fulfill system roles and responsibilities;

  e. Identify the information types processed, stored, and transmitted by the system;

  f. Provide the security categorization of the system, including supporting rationale;

  g. Describe any specific threats to the system that are of concern to the organization;

  h. Provide the results of a privacy risk assessment for systems processing personally identifiable information;

  i. Describe the operational environment for the system and any dependencies on or connections to other systems or system components;

  j. Provide an overview of the security and privacy requirements for the system;

  k. Identify any relevant control baselines or overlays, if applicable;

  l. Describe the controls in place or planned for meeting the security and privacy requirements, including a rationale for any tailoring decisions;

  m. Include risk determinations for security and privacy architecture and design decisions;

  n. Include security- and privacy-related activities affecting the system that require planning and coordination with [Assignment: organization-defined individuals or groups]; and

> [!IMPORTANT]
> <mark style="background-color: #fff9c4; color: #b71c1c; font-weight: bold; padding: 2px 6px; border-radius: 4px;">⚠️ RMF TEAM ACTION REQUIRED: Verify and update operational procedure or contact details in this section.</mark>
>   o. Are reviewed and approved by the authorizing official or designated representative prior to plan implementation.


2. Distribute copies of the plans and communicate subsequent changes to the plans to [Assignment: organization-defined personnel or roles];


3. Review the plans [Assignment: organization-defined frequency];


4. Update the plans to address changes to the system and environment of operation or problems identified during plan implementation or control assessments; and


5. Protect the plans from unauthorized disclosure and modification.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Owner & ISSO |
| **Implementation Status (check all that apply)**:<br>- [x] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [ ] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>The System Security Plan (SSP), System Architecture documentation, and NIST SP 800-53 control baselines are developed, maintained, and reviewed periodically by the System Owner and ISSO. |


### PL-4 Rules of Behavior


1. Establish and provide to individuals requiring access to the system, the rules that describe their responsibilities and expected behavior for information and system usage, security, and privacy;


2. Receive a documented acknowledgment from such individuals, indicating that they have read, understand, and agree to abide by the rules of behavior, before authorizing access to information and the system;


3. Review and update the rules of behavior [Assignment: organization-defined frequency]; and


4. Require individuals who have acknowledged a previous version of the rules of behavior to read and re-acknowledge [Selection (one or more): [Assignment: organization-defined frequency]; when the rules are revised or updated].


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Owner & ISSO |
| **Implementation Status (check all that apply)**:<br>- [x] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [ ] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>The System Security Plan (SSP), System Architecture documentation, and NIST SP 800-53 control baselines are developed, maintained, and reviewed periodically by the System Owner and ISSO. |


### PL-4(1) Rules of Behavior | Social Media and External Site/Application Usage Restrictions

Include in the rules of behavior, restrictions on:


1. Use of social media, social networking sites, and external sites/applications;


2. Posting organizational information on public websites; and


3. Use of organization-provided identifiers (e.g., email addresses) and authentication secrets (e.g., passwords) for creating accounts on external sites/applications.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Owner & ISSO |
| **Implementation Status (check all that apply)**:<br>- [x] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [ ] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>The System Security Plan (SSP), System Architecture documentation, and NIST SP 800-53 control baselines are developed, maintained, and reviewed periodically by the System Owner and ISSO. |


### PL-7 Concept of Operations


1. Develop a Concept of Operations (CONOPS) for the system describing how the organization intends to operate the system from the perspective of information security and privacy; and


2. Review and update the CONOPS [Assignment: organization-defined frequency].


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Owner & ISSO |
| **Implementation Status (check all that apply)**:<br>- [x] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [ ] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>The System Security Plan (SSP), System Architecture documentation, and NIST SP 800-53 control baselines are developed, maintained, and reviewed periodically by the System Owner and ISSO. |


### PL-8 Security and Privacy Architectures


1. Develop security and privacy architectures for the system that:

  a. Describe the requirements and approach to be taken for protecting the confidentiality, integrity, and availability of organizational information;

  b. Describe the requirements and approach to be taken for processing personally identifiable information to minimize privacy risk to individuals;

  c. Describe how the architectures are integrated into and support the enterprise architecture; and

  d. Describe any assumptions about, and dependencies on, external systems and services;


2. Review and update the architectures [Assignment: organization-defined frequency] to reflect changes in the enterprise architecture; and


3. Reflect planned architecture changes in security and privacy plans, Concept of Operations (CONOPS), criticality analysis, organizational procedures, and procurements and acquisitions.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Owner & ISSO |
| **Implementation Status (check all that apply)**:<br>- [x] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [ ] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>The System Security Plan (SSP), System Architecture documentation, and NIST SP 800-53 control baselines are developed, maintained, and reviewed periodically by the System Owner and ISSO. |


### PL-8(1) Security and Privacy Architectures | Defense in Depth

Design the security and privacy architectures for the system using a defense-in-depth approach that:


1. Allocates [Assignment: organization-defined controls] to [Assignment: organization-defined locations and architectural layers]; and


2. Ensures that the allocated controls operate in a coordinated and mutually reinforcing manner.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Owner & ISSO |
| **Implementation Status (check all that apply)**:<br>- [x] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [ ] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>The System Security Plan (SSP), System Architecture documentation, and NIST SP 800-53 control baselines are developed, maintained, and reviewed periodically by the System Owner and ISSO. |


### PL-8(2) Security and Privacy Architectures | Supplier Diversity

Require that [Assignment: organization-defined controls] allocated to [Assignment: organization-defined locations and architectural layers] are obtained from different suppliers.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Owner & ISSO |
| **Implementation Status (check all that apply)**:<br>- [x] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [ ] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>The System Security Plan (SSP), System Architecture documentation, and NIST SP 800-53 control baselines are developed, maintained, and reviewed periodically by the System Owner and ISSO. |


### PL-9 Central Management

Centrally manage [Assignment: organization-defined controls and related processes].


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Owner & ISSO |
| **Implementation Status (check all that apply)**:<br>- [x] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [ ] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>The System Security Plan (SSP), System Architecture documentation, and NIST SP 800-53 control baselines are developed, maintained, and reviewed periodically by the System Owner and ISSO. |


### PL-10 Baseline Selection

Select a control baseline for the system.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Owner & ISSO |
| **Implementation Status (check all that apply)**:<br>- [x] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [ ] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>The System Security Plan (SSP), System Architecture documentation, and NIST SP 800-53 control baselines are developed, maintained, and reviewed periodically by the System Owner and ISSO. |


### PL-11 Baseline Tailoring

Tailor the selected control baseline by applying specified tailoring actions.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Owner & ISSO |
| **Implementation Status (check all that apply)**:<br>- [x] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [ ] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>The System Security Plan (SSP), System Architecture documentation, and NIST SP 800-53 control baselines are developed, maintained, and reviewed periodically by the System Owner and ISSO. |


## 2.13 Program Management


### PM-1 Information Security Program Plan


1. Develop and disseminate an organization-wide information security program plan that:

  a. Provides an overview of the requirements for the security program and a description of the security program management controls and common controls in place or planned for meeting those requirements;

  b. Includes the identification and assignment of roles, responsibilities, management commitment, coordination among organizational entities, and compliance;

  c. Reflects the coordination among organizational entities responsible for information security; and

  d. Is approved by a senior official with responsibility and accountability for the risk being incurred to organizational operations (including mission, functions, image, and reputation), organizational assets, individuals, other organizations, and the Nation;


2. Review and update the organization-wide information security program plan [Assignment: organization-defined frequency] and following [Assignment: organization-defined events]; and


3. Protect the information security program plan from unauthorized disclosure and modification.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) |
| **Implementation Status (check all that apply)**:<br>- [x] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [ ] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Organization-wide cybersecurity program management and risk governance. |


### PM-3 Information Security and Privacy Resources


1. Include the resources needed to implement the information security and privacy programs in capital planning and investment requests and document all exceptions to this requirement;


2. Prepare documentation required for addressing information security and privacy programs in capital planning and investment requests in accordance with applicable laws, executive orders, directives, policies, regulations, standards; and


3. Make available for expenditure, the planned information security and privacy resources.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) |
| **Implementation Status (check all that apply)**:<br>- [x] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [ ] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Organization-wide cybersecurity program management and risk governance. |


### PM-4 Plan of Action and Milestones Process


1. Implement a process to ensure that plans of action and milestones for the information security, privacy, and supply chain risk management programs and associated organizational systems:

  a. Are developed and maintained;

  b. Document the remedial information security, privacy, and supply chain risk management actions to adequately respond to risk to organizational operations and assets, individuals, other organizations, and the Nation; and

  c. Are reported in accordance with established reporting requirements.


2. Review plans of action and milestones for consistency with the organizational risk management strategy and organization-wide priorities for risk response actions.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) |
| **Implementation Status (check all that apply)**:<br>- [x] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [ ] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Organization-wide cybersecurity program management and risk governance. |


### PM-5 System Inventory

Develop and update [Assignment: organization-defined frequency] an inventory of organizational systems.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) |
| **Implementation Status (check all that apply)**:<br>- [x] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [ ] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Organization-wide cybersecurity program management and risk governance. |


### PM-5(1) System Inventory | Inventory of Personally Identifiable Information

Establish, maintain, and update [Assignment: organization-defined frequency] an inventory of all systems, applications, and projects that process personally identifiable information.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) |
| **Implementation Status (check all that apply)**:<br>- [x] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [ ] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Organization-wide cybersecurity program management and risk governance. |


### PM-6 Measures of Performance

Develop, monitor, and report on the results of information security and privacy measures of performance.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) |
| **Implementation Status (check all that apply)**:<br>- [x] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [ ] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Organization-wide cybersecurity program management and risk governance. |


### PM-7 Enterprise Architecture

Develop and maintain an enterprise architecture with consideration for information security, privacy, and the resulting risk to organizational operations and assets, individuals, other organizations, and the Nation.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) |
| **Implementation Status (check all that apply)**:<br>- [x] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [ ] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Organization-wide cybersecurity program management and risk governance. |


### PM-8 Critical Infrastructure Plan

Address information security and privacy issues in the development, documentation, and updating of a critical infrastructure and key resources protection plan.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) |
| **Implementation Status (check all that apply)**:<br>- [x] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [ ] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Organization-wide cybersecurity program management and risk governance. |


### PM-9 Risk Management Strategy


1. Develops a comprehensive strategy to manage:

  a. Security risk to organizational operations and assets, individuals, other organizations, and the Nation associated with the operation and use of organizational systems; and

  b. Privacy risk to individuals resulting from the authorized processing of personally identifiable information;


2. Implement the risk management strategy consistently across the organization; and


3. Review and update the risk management strategy [Assignment: organization-defined frequency] or as required, to address organizational changes.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) |
| **Implementation Status (check all that apply)**:<br>- [x] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [ ] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Organization-wide cybersecurity program management and risk governance. |


### PM-10 Authorization Process


1. Manage the security and privacy state of organizational systems and the environments in which those systems operate through authorization processes;


2. Designate individuals to fulfill specific roles and responsibilities within the organizational risk management process; and


3. Integrate the authorization processes into an organization-wide risk management program.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) |
| **Implementation Status (check all that apply)**:<br>- [x] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [ ] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Organization-wide cybersecurity program management and risk governance. |


### PM-11 Mission and Business Process Definition


1. Define organizational mission and business processes with consideration for information security and privacy and the resulting risk to organizational operations, organizational assets, individuals, other organizations, and the Nation; and


2. Determine information protection and personally identifiable information processing needs arising from the defined mission and business processes; and


3. Review and revise the mission and business processes [Assignment: organization-defined frequency].


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) |
| **Implementation Status (check all that apply)**:<br>- [x] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [ ] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Organization-wide cybersecurity program management and risk governance. |


### PM-13 Security and Privacy Workforce

Establish a security and privacy workforce development and improvement program.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) |
| **Implementation Status (check all that apply)**:<br>- [x] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [ ] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Organization-wide cybersecurity program management and risk governance. |


### PM-14 Testing, Training, and Monitoring


1. Implement a process for ensuring that organizational plans for conducting security and privacy testing, training, and monitoring activities associated with organizational systems:

  a. Are developed and maintained; and

  b. Continue to be executed; and


2. Review testing, training, and monitoring plans for consistency with the organizational risk management strategy and organization-wide priorities for risk response actions.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) |
| **Implementation Status (check all that apply)**:<br>- [x] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [ ] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Organization-wide cybersecurity program management and risk governance. |


### PM-17 Protecting Controlled Unclassified Information on External Systems


1. Establish policy and procedures to ensure that requirements for the protection of controlled unclassified information that is processed, stored or transmitted on external systems, are implemented in accordance with applicable laws, executive orders, directives, policies, regulations, and standards; and


2. Review and update the policy and procedures [Assignment: organization-defined frequency].


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) |
| **Implementation Status (check all that apply)**:<br>- [x] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [ ] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Organization-wide cybersecurity program management and risk governance. |


### PM-18 Privacy Program Plan


1. Develop and disseminate an organization-wide privacy program plan that provides an overview of the agency’s privacy program, and:

  a. Includes a description of the structure of the privacy program and the resources dedicated to the privacy program;

  b. Provides an overview of the requirements for the privacy program and a description of the privacy program management controls and common controls in place or planned for meeting those requirements;

  c. Includes the role of the senior agency official for privacy and the identification and assignment of roles of other privacy officials and staff and their responsibilities;

  d. Describes management commitment, compliance, and the strategic goals and objectives of the privacy program;

  e. Reflects coordination among organizational entities responsible for the different aspects of privacy; and

  f. Is approved by a senior official with responsibility and accountability for the privacy risk being incurred to organizational operations (including mission, functions, image, and reputation), organizational assets, individuals, other organizations, and the Nation; and


2. Update the plan [Assignment: organization-defined frequency] and to address changes in federal privacy laws and policy and organizational changes and problems identified during plan implementation or privacy control assessments.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) |
| **Implementation Status (check all that apply)**:<br>- [x] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [ ] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Organization-wide cybersecurity program management and risk governance. |


### PM-19 Privacy Program Leadership Role

Appoint a senior agency official for privacy with the authority, mission, accountability, and resources to coordinate, develop, and implement, applicable privacy requirements and manage privacy risks through the organization-wide privacy program.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) |
| **Implementation Status (check all that apply)**:<br>- [x] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [ ] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Organization-wide cybersecurity program management and risk governance. |


### PM-20 Dissemination of Privacy Program Information

Maintain a central resource webpage on the organization’s principal public website that serves as a central source of information about the organization’s privacy program and that:


1. Ensures that the public has access to information about organizational privacy activities and can communicate with its senior agency official for privacy;


2. Ensures that organizational privacy practices and reports are publicly available; and


3. Employs publicly facing email addresses and/or phone lines to enable the public to provide feedback and/or direct questions to privacy offices regarding privacy practices.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) |
| **Implementation Status (check all that apply)**:<br>- [x] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [ ] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Organization-wide cybersecurity program management and risk governance. |


### PM-20(1) Dissemination of Privacy Program Information | Privacy Policies on Websites, Applications, and Digital Services

Develop and post privacy policies on all external-facing websites, mobile applications, and other digital services, that:


1. Are written in plain language and organized in a way that is easy to understand and navigate;


2. Provide information needed by the public to make an informed decision about whether and how to interact with the organization; and


3. Are updated whenever the organization makes a substantive change to the practices it describes and includes a time/date stamp to inform the public of the date of the most recent changes.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) |
| **Implementation Status (check all that apply)**:<br>- [x] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [ ] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Organization-wide cybersecurity program management and risk governance. |


### PM-22 Personally Identifiable Information Quality Management

Develop and document organization-wide policies and procedures for:


1. Reviewing for the accuracy, relevance, timeliness, and completeness of personally identifiable information across the information life cycle;


2. Correcting or deleting inaccurate or outdated personally identifiable information;


3. Disseminating notice of corrected or deleted personally identifiable information to individuals or other appropriate entities; and


4. Appeals of adverse decisions on correction or deletion requests.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) |
| **Implementation Status (check all that apply)**:<br>- [x] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [ ] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Organization-wide cybersecurity program management and risk governance. |


### PM-23 Data Governance Body

Establish a Data Governance Body consisting of [Assignment: organization-defined roles] with [Assignment: organization-defined responsibilities].


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) |
| **Implementation Status (check all that apply)**:<br>- [x] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [ ] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Organization-wide cybersecurity program management and risk governance. |


### PM-24 Data Integrity Board

Establish a Data Integrity Board to:


1. Review proposals to conduct or participate in a matching program; and


2. Conduct an annual review of all matching programs in which the agency has participated.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) |
| **Implementation Status (check all that apply)**:<br>- [x] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [ ] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Organization-wide cybersecurity program management and risk governance. |


### PM-25 Minimization of Personally Identifiable Information Used in Testing, Training, and Research


1. Develop, document, and implement policies and procedures that address the use of personally identifiable information for internal testing, training, and research;


2. Limit or minimize the amount of personally identifiable information used for internal testing, training, and research purposes;


3. Authorize the use of personally identifiable information when such information is required for internal testing, training, and research; and


4. Review and update policies and procedures [Assignment: organization-defined frequency].


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) |
| **Implementation Status (check all that apply)**:<br>- [x] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [ ] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Organization-wide cybersecurity program management and risk governance. |


### PM-26 Complaint Management

Implement a process for receiving and responding to complaints, concerns, or questions from individuals about the organizational security and privacy practices that includes:


1. Mechanisms that are easy to use and readily accessible by the public;


2. All information necessary for successfully filing complaints;


3. Tracking mechanisms to ensure all complaints received are reviewed and addressed within [Assignment: organization-defined time period];


4. Acknowledgement of receipt of complaints, concerns, or questions from individuals within [Assignment: organization-defined time period]; and


5. Response to complaints, concerns, or questions from individuals within [Assignment: organization-defined time period].


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) |
| **Implementation Status (check all that apply)**:<br>- [x] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [ ] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Organization-wide cybersecurity program management and risk governance. |


### PM-27 Privacy Reporting


1. Develop [Assignment: organization-defined privacy reports] and disseminate to:

  a. [Assignment: organization-defined oversight bodies] to demonstrate accountability with statutory, regulatory, and policy privacy mandates; and

  b. [Assignment: organization-defined officials] and other personnel with responsibility for monitoring privacy program compliance; and


2. Review and update privacy reports [Assignment: organization-defined frequency].


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) |
| **Implementation Status (check all that apply)**:<br>- [x] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [ ] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Organization-wide cybersecurity program management and risk governance. |


### PM-28 Risk Framing


1. Identify and document:

  a. Assumptions affecting risk assessments, risk responses, and risk monitoring;

  b. Constraints affecting risk assessments, risk responses, and risk monitoring;

  c. Priorities and trade-offs considered by the organization for managing risk; and

  d. Organizational risk tolerance;


2. Distribute the results of risk framing activities to [Assignment: organization-defined personnel]; and


3. Review and update risk framing considerations [Assignment: organization-defined frequency].


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) |
| **Implementation Status (check all that apply)**:<br>- [x] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [ ] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Organization-wide cybersecurity program management and risk governance. |


### PM-29 Risk Management Program Leadership Roles


1. Appoint a Senior Accountable Official for Risk Management to align organizational information security and privacy management processes with strategic, operational, and budgetary planning processes; and


2. Establish a Risk Executive (function) to view and analyze risk from an organization-wide perspective and ensure management of risk is consistent across the organization.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) |
| **Implementation Status (check all that apply)**:<br>- [x] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [ ] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Organization-wide cybersecurity program management and risk governance. |


### PM-30 Supply Chain Risk Management Strategy


1. Develop an organization-wide strategy for managing supply chain risks associated with the development, acquisition, maintenance, and disposal of systems, system components, and system services;


2. Implement the supply chain risk management strategy consistently across the organization; and


3. Review and update the supply chain risk management strategy on [Assignment: organization-defined frequency] or as required, to address organizational changes.


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) |
| **Implementation Status (check all that apply)**:<br>- [x] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [ ] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Organization-wide cybersecurity program management and risk governance. |


### PM-31 Continuous Monitoring Strategy

Develop an organization-wide continuous monitoring strategy and implement continuous monitoring programs that include:


1. Establishing the following organization-wide metrics to be monitored: [Assignment: organization-defined metrics];


2. Establishing [Assignment: organization-defined frequencies] for monitoring and [Assignment: organization-defined frequencies] for assessment of control effectiveness;


3. Ongoing monitoring of organizationally-defined metrics in accordance with the continuous monitoring strategy;


4. Correlation and analysis of information generated by control assessments and monitoring;


5. Response actions to address results of the analysis of control assessment and monitoring information; and


6. Reporting the security and privacy status of organizational systems to [Assignment: organization-defined personnel or roles] [Assignment: organization-defined frequency].


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Security Manager (ISSM) |
| **Implementation Status (check all that apply)**:<br>- [x] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [ ] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Organization-wide cybersecurity program management and risk governance. |


## 2.14 Personnel Security


### PS-1 Policy and Procedures


1. Develop, document, and disseminate to [Assignment: organization-defined personnel or roles]:

  a. [Selection (one or more): Organization-level; Mission/business process-level; System-level] personnel security policy that:

    - Addresses purpose, scope, roles, responsibilities, management commitment, coordination among organizational entities, and compliance; and

    - Is consistent with applicable laws, executive orders, directives, regulations, policies, standards, and guidelines; and

  b. Procedures to facilitate the implementation of the personnel security policy and the associated personnel security controls;


2. Designate an [Assignment: organization-defined official] to manage the development, documentation, and dissemination of the personnel security policy and procedures; and


3. Review and update the current personnel security:

  c. Policy [Assignment: organization-defined frequency] and following [Assignment: organization-defined events]; and

  d. Procedures [Assignment: organization-defined frequency] and following [Assignment: organization-defined events].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & ISSM |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC background screening and clearance procedures for all Googlers with administrative access to Google Common Infrastructure (GCI) are Inherited. {{ ORGANIZATION }} conducts background screening for system administrators prior to granting GCP IAM access. |


### PS-2 Position Risk Designation


1. Assign a risk designation to all organizational positions;


2. Establish screening criteria for individuals filling those positions; and


3. Review and update position risk designations [Assignment: organization-defined frequency].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & ISSM |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC background screening and clearance procedures for all Googlers with administrative access to Google Common Infrastructure (GCI) are Inherited. {{ ORGANIZATION }} conducts background screening for system administrators prior to granting GCP IAM access. |


### PS-3 Personnel Screening


1. Screen individuals prior to authorizing access to the system; and


2. Rescreen individuals in accordance with [Assignment: organization-defined conditions requiring rescreening and, where rescreening is so indicated, the frequency of rescreening].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & ISSM |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC background screening and clearance procedures for all Googlers with administrative access to Google Common Infrastructure (GCI) are Inherited. {{ ORGANIZATION }} conducts background screening for system administrators prior to granting GCP IAM access. |


### PS-3(4) Personnel Screening | Citizenship Requirements

Verify that individuals accessing a system processing, storing, or transmitting [Assignment: organization-defined information types] meet [Assignment: organization-defined citizenship requirements].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & ISSM |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC background screening and clearance procedures for all Googlers with administrative access to Google Common Infrastructure (GCI) are Inherited. {{ ORGANIZATION }} conducts background screening for system administrators prior to granting GCP IAM access. |


### PS-4 Personnel Termination

Upon termination of individual employment:


1. Disable system access within [Assignment: organization-defined time period];


2. Terminate or revoke any authenticators and credentials associated with the individual;


3. Conduct exit interviews that include a discussion of [Assignment: organization-defined information security topics];


4. Retrieve all security-related organizational system-related property; and


5. Retain access to organizational information and systems formerly controlled by terminated individual.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & ISSM |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC background screening and clearance procedures for all Googlers with administrative access to Google Common Infrastructure (GCI) are Inherited. {{ ORGANIZATION }} conducts background screening for system administrators prior to granting GCP IAM access. |


### PS-4(1) Personnel Termination | Post-employment Requirements


1. Notify terminated individuals of applicable, legally binding post-employment requirements for the protection of organizational information; and


2. Require terminated individuals to sign an acknowledgment of post-employment requirements as part of the organizational termination process.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & ISSM |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC background screening and clearance procedures for all Googlers with administrative access to Google Common Infrastructure (GCI) are Inherited. {{ ORGANIZATION }} conducts background screening for system administrators prior to granting GCP IAM access. |


### PS-4(2) Personnel Termination | Automated Actions

Use [Assignment: organization-defined automated mechanisms] to [Selection (one or more): notify [Assignment: organization-defined personnel or roles] of individual termination actions; disable access to system resources].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & ISSM |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC background screening and clearance procedures for all Googlers with administrative access to Google Common Infrastructure (GCI) are Inherited. {{ ORGANIZATION }} conducts background screening for system administrators prior to granting GCP IAM access. |


### PS-5 Personnel Transfer


1. Review and confirm ongoing operational need for current logical and physical access authorizations to systems and facilities when individuals are reassigned or transferred to other positions within the organization;


2. Initiate [Assignment: organization-defined transfer or reassignment actions] within [Assignment: organization-defined time period following the formal transfer action];


3. Modify access authorization as needed to correspond with any changes in operational need due to reassignment or transfer; and


4. Notify [Assignment: organization-defined personnel or roles] within [Assignment: organization-defined time period].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & ISSM |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC background screening and clearance procedures for all Googlers with administrative access to Google Common Infrastructure (GCI) are Inherited. {{ ORGANIZATION }} conducts background screening for system administrators prior to granting GCP IAM access. |


### PS-6 Access Agreements


1. Develop and document access agreements for organizational systems;


2. Review and update the access agreements [Assignment: organization-defined frequency]; and


3. Verify that individuals requiring access to organizational information and systems:

  a. Sign appropriate access agreements prior to being granted access; and

  b. Re-sign access agreements to maintain access to organizational systems when access agreements have been updated or [Assignment: organization-defined frequency].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & ISSM |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC background screening and clearance procedures for all Googlers with administrative access to Google Common Infrastructure (GCI) are Inherited. {{ ORGANIZATION }} conducts background screening for system administrators prior to granting GCP IAM access. |


### PS-6(3) Access Agreements | Post-employment Requirements


1. Notify individuals of applicable, legally binding post-employment requirements for protection of organizational information; and


2. Require individuals to sign an acknowledgment of these requirements, if applicable, as part of granting initial access to covered information.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & ISSM |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC background screening and clearance procedures for all Googlers with administrative access to Google Common Infrastructure (GCI) are Inherited. {{ ORGANIZATION }} conducts background screening for system administrators prior to granting GCP IAM access. |


### PS-7 External Personnel Security


1. Establish personnel security requirements, including security roles and responsibilities for external providers;


2. Require external providers to comply with personnel security policies and procedures established by the organization;


3. Document personnel security requirements;


4. Require external providers to notify [Assignment: organization-defined personnel or roles] of any personnel transfers or terminations of external personnel who possess organizational credentials and/or badges, or who have system privileges within [Assignment: organization-defined time period]; and


5. Monitor provider compliance with personnel security requirements.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & ISSM |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC background screening and clearance procedures for all Googlers with administrative access to Google Common Infrastructure (GCI) are Inherited. {{ ORGANIZATION }} conducts background screening for system administrators prior to granting GCP IAM access. |


### PS-8 Personnel Sanctions


1. Employ a formal sanctions process for individuals failing to comply with established information security and privacy policies and procedures; and


2. Notify [Assignment: organization-defined personnel or roles] within [Assignment: organization-defined time period] when a formal employee sanctions process is initiated, identifying the individual sanctioned and the reason for the sanction.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & ISSM |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC background screening and clearance procedures for all Googlers with administrative access to Google Common Infrastructure (GCI) are Inherited. {{ ORGANIZATION }} conducts background screening for system administrators prior to granting GCP IAM access. |


### PS-9 Position Descriptions

Incorporate security and privacy roles and responsibilities into organizational position descriptions.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & ISSM |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC background screening and clearance procedures for all Googlers with administrative access to Google Common Infrastructure (GCI) are Inherited. {{ ORGANIZATION }} conducts background screening for system administrators prior to granting GCP IAM access. |


## 2.15 PII Processing and Transparency


### PT-1 Policy and Procedures


1. Develop, document, and disseminate to [Assignment: organization-defined personnel or roles]:

  a. [Selection (one or more): Organization-level; Mission/business process-level; System-level] personally identifiable information processing and transparency policy that:

    - Addresses purpose, scope, roles, responsibilities, management commitment, coordination among organizational entities, and compliance; and

    - Is consistent with applicable laws, executive orders, directives, regulations, policies, standards, and guidelines; and

  b. Procedures to facilitate the implementation of the personally identifiable information processing and transparency policy and the associated personally identifiable information processing and transparency controls;


2. Designate an [Assignment: organization-defined official] to manage the development, documentation, and dissemination of the personally identifiable information processing and transparency policy and procedures; and


3. Review and update the current personally identifiable information processing and transparency:

  c. Policy [Assignment: organization-defined frequency] and following [Assignment: organization-defined events]; and

  d. Procedures [Assignment: organization-defined frequency] and following [Assignment: organization-defined events].


| Control Summary Information |
| :--- |
| **Responsible Role**: Information System Owner & Privacy Official |
| **Implementation Status (check all that apply)**:<br>- [x] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [ ] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>System privacy policies and PII processing procedures are established and reviewed in accordance with federal privacy regulations. |


## 2.16 Risk Assessment


### RA-1 Policy and Procedures


1. Develop, document, and disseminate to [Assignment: organization-defined personnel or roles]:

  a. [Selection (one or more): Organization-level; Mission/business process-level; System-level] risk assessment policy that:

  b. Addresses purpose, scope, roles, responsibilities, management commitment, coordination among organizational entities, and compliance; and

  c. Is consistent with applicable laws, executive orders, directives, regulations, policies, standards, and guidelines; and

  d. Procedures to facilitate the implementation of the risk assessment policy and the associated risk assessment controls;


2. Designate an [Assignment: organization-defined official] to manage the development, documentation, and dissemination of the risk assessment policy and procedures; and


3. Review and update the current risk assessment:

  e. Policy [Assignment: organization-defined frequency] and following [Assignment: organization-defined events]; and

  f. Procedures [Assignment: organization-defined frequency] and following [Assignment: organization-defined events].


| Control Summary Information |
| :--- |
| **Responsible Role**: ISSO / DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC conducts platform-level threat modeling and vulnerability assessments for GCI (Inherited). The system platform performs automated container image vulnerability scanning via Artifact Registry and continuous posture monitoring via {{ THREAT_DETECTION_ENGINE }}. |


### RA-2 Security Categorization


1. Categorize the system and information it processes, stores, and transmits;


2. Document the security categorization results, including supporting rationale, in the security plan for the system; and


3. Verify that the authorizing official or authorizing official designated representative reviews and approves the security categorization decision.


| Control Summary Information |
| :--- |
| **Responsible Role**: ISSO / DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC conducts platform-level threat modeling and vulnerability assessments for GCI (Inherited). The system platform performs automated container image vulnerability scanning via Artifact Registry and continuous posture monitoring via {{ THREAT_DETECTION_ENGINE }}. |


### RA-3 Risk Assessment


1. Conduct a risk assessment, including:

  a. Identifying threats to and vulnerabilities in the system;

  b. Determining the likelihood and magnitude of harm from unauthorized access, use, disclosure, disruption, modification, or destruction of the system, the information it processes, stores, or transmits, and any related information; and

  c. Determining the likelihood and impact of adverse effects on individuals arising from the processing of personally identifiable information;


2. Integrate risk assessment results and risk management decisions from the organization and mission or business process perspectives with system-level risk assessments;


3. Document risk assessment results in [Selection: security and privacy plans; risk assessment report; [Assignment: organization-defined document]];


4. Review risk assessment results [Assignment: organization-defined frequency];


5. Disseminate risk assessment results to [Assignment: organization-defined personnel or roles]; and


6. Update the risk assessment [Assignment: organization-defined frequency] or when there are significant changes to the system, its environment of operation, or other conditions that may impact the security or privacy state of the system.


| Control Summary Information |
| :--- |
| **Responsible Role**: ISSO / DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC conducts platform-level threat modeling and vulnerability assessments for GCI (Inherited). The system platform performs automated container image vulnerability scanning via Artifact Registry and continuous posture monitoring via {{ THREAT_DETECTION_ENGINE }}. |


### RA-3(1) Risk Assessment | Supply Chain Risk Assessment


1. Assess supply chain risks associated with [Assignment: organization-defined systems, system components, and system services]; and


2. Update the supply chain risk assessment [Assignment: organization-defined frequency], when there are significant changes to the relevant supply chain, or when changes to the system, environments of operation, or other conditions may necessitate a change in the supply chain.


| Control Summary Information |
| :--- |
| **Responsible Role**: ISSO / DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC conducts platform-level threat modeling and vulnerability assessments for GCI (Inherited). The system platform performs automated container image vulnerability scanning via Artifact Registry and continuous posture monitoring via {{ THREAT_DETECTION_ENGINE }}. |


### RA-3(2) Risk Assessment | Use of All-source Intelligence

Use all-source intelligence to assist in the analysis of risk.


| Control Summary Information |
| :--- |
| **Responsible Role**: ISSO / DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC conducts platform-level threat modeling and vulnerability assessments for GCI (Inherited). The system platform performs automated container image vulnerability scanning via Artifact Registry and continuous posture monitoring via {{ THREAT_DETECTION_ENGINE }}. |


### RA-3(3) Risk Assessment | Dynamic Threat Awareness

Determine the current cyber threat environment on an ongoing basis using [Assignment: organization-defined means].


| Control Summary Information |
| :--- |
| **Responsible Role**: ISSO / DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC conducts platform-level threat modeling and vulnerability assessments for GCI (Inherited). The system platform performs automated container image vulnerability scanning via Artifact Registry and continuous posture monitoring via {{ THREAT_DETECTION_ENGINE }}. |


### RA-5 Vulnerability Monitoring and Scanning


1. Monitor and scan for vulnerabilities in the system and hosted applications [Assignment: organization-defined frequency and/or randomly in accordance with organization-defined process] and when new vulnerabilities potentially affecting the system are identified and reported;


2. Employ vulnerability monitoring tools and techniques that facilitate interoperability among tools and automate parts of the vulnerability management process by using standards for:

  a. Enumerating platforms, software flaws, and improper configurations;

  b. Formatting checklists and test procedures; and

  c. Measuring vulnerability impact;


3. Analyze vulnerability scan reports and results from vulnerability monitoring;


4. Remediate legitimate vulnerabilities [Assignment: organization-defined response times] in accordance with an organizational assessment of risk;


5. Share information obtained from the vulnerability monitoring process and control assessments with [Assignment: organization-defined personnel or roles] to help eliminate similar vulnerabilities in other systems; and


6. Employ vulnerability monitoring tools that include the capability to readily update the vulnerabilities to be scanned.


| Control Summary Information |
| :--- |
| **Responsible Role**: ISSO / DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC conducts platform-level threat modeling and vulnerability assessments for GCI (Inherited). The system platform performs automated container image vulnerability scanning via Artifact Registry and continuous posture monitoring via {{ THREAT_DETECTION_ENGINE }}. |


### RA-5(2) Vulnerability Monitoring and Scanning | Update Vulnerabilities to Be Scanned

Update the system vulnerabilities to be scanned [Selection (one or more): [Assignment: organization-defined frequency]; prior to a new scan; when new vulnerabilities are identified and reported].


| Control Summary Information |
| :--- |
| **Responsible Role**: ISSO / DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC conducts platform-level threat modeling and vulnerability assessments for GCI (Inherited). The system platform performs automated container image vulnerability scanning via Artifact Registry and continuous posture monitoring via {{ THREAT_DETECTION_ENGINE }}. |


### RA-5(4) Vulnerability Monitoring and Scanning | Discoverable Information

Determine information about the system that is discoverable and take [Assignment: organization-defined corrective actions].


| Control Summary Information |
| :--- |
| **Responsible Role**: ISSO / DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC conducts platform-level threat modeling and vulnerability assessments for GCI (Inherited). The system platform performs automated container image vulnerability scanning via Artifact Registry and continuous posture monitoring via {{ THREAT_DETECTION_ENGINE }}. |


### RA-5(5) Vulnerability Monitoring and Scanning | Privileged Access

Implement privileged access authorization to [Assignment: organization-defined system components] for [Assignment: organization-defined vulnerability scanning activities].


| Control Summary Information |
| :--- |
| **Responsible Role**: ISSO / DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC conducts platform-level threat modeling and vulnerability assessments for GCI (Inherited). The system platform performs automated container image vulnerability scanning via Artifact Registry and continuous posture monitoring via {{ THREAT_DETECTION_ENGINE }}. |


### RA-5(10) Vulnerability Monitoring and Scanning | Correlate Scanning Information

Correlate the output from vulnerability scanning tools to determine the presence of multi-vulnerability and multi-hop attack vectors.


| Control Summary Information |
| :--- |
| **Responsible Role**: ISSO / DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC conducts platform-level threat modeling and vulnerability assessments for GCI (Inherited). The system platform performs automated container image vulnerability scanning via Artifact Registry and continuous posture monitoring via {{ THREAT_DETECTION_ENGINE }}. |


### RA-5(11) Vulnerability Monitoring and Scanning | Public Disclosure Program

Establish a public reporting channel for receiving reports of vulnerabilities in organizational systems and system components.


| Control Summary Information |
| :--- |
| **Responsible Role**: ISSO / DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC conducts platform-level threat modeling and vulnerability assessments for GCI (Inherited). The system platform performs automated container image vulnerability scanning via Artifact Registry and continuous posture monitoring via {{ THREAT_DETECTION_ENGINE }}. |


### RA-7 Risk Response

Respond to findings from security and privacy assessments, monitoring, and audits in accordance with organizational risk tolerance.


| Control Summary Information |
| :--- |
| **Responsible Role**: ISSO / DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC conducts platform-level threat modeling and vulnerability assessments for GCI (Inherited). The system platform performs automated container image vulnerability scanning via Artifact Registry and continuous posture monitoring via {{ THREAT_DETECTION_ENGINE }}. |


### RA-9 Criticality Analysis

Identify critical system components and functions by performing a criticality analysis for [Assignment: organization-defined systems, system components, or system services] at [Assignment: organization-defined decision points in the system development life cycle].


| Control Summary Information |
| :--- |
| **Responsible Role**: ISSO / DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC conducts platform-level threat modeling and vulnerability assessments for GCI (Inherited). The system platform performs automated container image vulnerability scanning via Artifact Registry and continuous posture monitoring via {{ THREAT_DETECTION_ENGINE }}. |


### RA-10 Threat Hunting


1. Establish and maintain a cyber threat hunting capability to:

  a. Search for indicators of compromise in organizational systems; and

  b. Detect, track, and disrupt threats that evade existing controls; and


2. Employ the threat hunting capability [Assignment: organization-defined frequency].


| Control Summary Information |
| :--- |
| **Responsible Role**: ISSO / DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Google LLC conducts platform-level threat modeling and vulnerability assessments for GCI (Inherited). The system platform performs automated container image vulnerability scanning via Artifact Registry and continuous posture monitoring via {{ THREAT_DETECTION_ENGINE }}. |


## 2.17 System and Services Acquisition


### SA-1 Policy and Procedures


1. Develop, document, and disseminate to [Assignment: organization-defined personnel or roles]:

  a. [Selection (one or more): Organization-level; Mission/business process-level; System-level] system and services acquisition policy that:

    - Addresses purpose, scope, roles, responsibilities, management commitment, coordination among organizational entities, and compliance; and

    - Is consistent with applicable laws, executive orders, directives, regulations, policies, standards, and guidelines; and

  b. Procedures to facilitate the implementation of the system and services acquisition policy and the associated system and services acquisition controls;


2. Designate an [Assignment: organization-defined official] to manage the development, documentation, and dissemination of the system and services acquisition policy and procedures; and


3. Review and update the current system and services acquisition:

  c. Policy [Assignment: organization-defined frequency] and following [Assignment: organization-defined events]; and

  d. Procedures [Assignment: organization-defined frequency] and following [Assignment: organization-defined events].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-2 Allocation of Resources


1. Determine the high-level information security and privacy requirements for the system or system service in mission and business process planning;


2. Determine, document, and allocate the resources required to protect the system or system service as part of the organizational capital planning and investment control process; and


3. Establish a discrete line item for information security and privacy in organizational programming and budgeting documentation.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-3 System Development Life Cycle


1. Acquire, develop, and manage the system using [Assignment: organization-defined system development life cycle] that incorporates information security and privacy considerations;


2. Define and document information security and privacy roles and responsibilities throughout the system development life cycle;


3. Identify individuals having information security and privacy roles and responsibilities; and


4. Integrate the organizational information security and privacy risk management process into system development life cycle activities.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-3(1) System Development Life Cycle | Manage Preproduction Environment

Protect system preproduction environments commensurate with risk throughout the system development life cycle for the system, system component, or system service.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-3(2) System Development Life Cycle | Use of Live or Operational Data


1. Approve, document, and control the use of live data in preproduction environments for the system, system component, or system service; and


2. Protect preproduction environments for the system, system component, or system service at the same impact or classification level as any live data in use within the preproduction environments.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-3(3) System Development Life Cycle | Technology Refresh

Plan for and implement a technology refresh schedule for the system throughout the system development life cycle.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-4 Acquisition Process


1. Security and privacy functional requirements;


2. Strength of mechanism requirements;


3. Security and privacy assurance requirements;


4. Controls needed to satisfy the security and privacy requirements.


5. Security and privacy documentation requirements;


6. Requirements for protecting security and privacy documentation;


7. Description of the system development environment and environment in which the system is intended to operate;


8. Allocation of responsibility or identification of parties responsible for information security, privacy, and supply chain risk management; and


9. Acceptance criteria.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-4(1) Acquisition Process | Functional Properties of Controls

Require the developer of the system, system component, or system service to provide a description of the functional properties of the controls to be implemented.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-4(2) Acquisition Process | Design and Implementation for Controls

Require the developer of the system, system component, or system service to provide design and implementation information for the controls that includes: [Selection (one or more): security-relevant external system interfaces; high-level design; low-level design; source code or hardware schematics; [Assignment: organization-defined design and implementation information]] at [Assignment: organization-defined level of detail].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-4(3) Acquisition Process | Development Methods, Techniques, and Practices

Require the developer of the system, system component, or system service to demonstrate the use of a system development life cycle process that includes:

1. [Assignment: organization-defined systems engineering methods];

2. [Assignment: organization-defined [Selection (one or more): systems security; privacy] engineering methods]; and

3. [Assignment: organization-defined software development methods; testing, evaluation, assessment, verification, and validation methods; and quality control processes].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-4(5) Acquisition Process | System, Component, and Service Configurations

Require the developer of the system, system component, or system service to:


1. Deliver the system, component, or service with [Assignment: organization-defined security configurations] implemented; and


2. Use the configurations as the default for any subsequent system, component, or service reinstallation or upgrade.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-4(7) Acquisition Process | NIAP-approved Protection Profiles


1. Limit the use of commercially provided information assurance and information assurance-enabled information technology products to those products that have been successfully evaluated against a National Information Assurance partnership (NIAP)-approved Protection Profile for a specific technology type, if such a profile exists; and


2. Require, if no NIAP-approved Protection Profile exists for a specific technology type but a commercially provided information technology product relies on cryptographic functionality to enforce its security policy, that the cryptographic module is FIPS-validated or NSA-approved.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-4(9) Acquisition Process | Functions, Ports, Protocols, and Services in Use

Require the developer of the system, system component, or system service to identify the functions, ports, protocols, and services intended for organizational use.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-4(10) Acquisition Process | Use of Approved PIV Products

Employ only information technology products on the FIPS 201-approved products list for Personal Identity Verification (PIV) capability implemented within organizational systems.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-5 System Documentation


1. Obtain or develop administrator documentation for the system, system component, or system service that describes:

  a. Secure configuration, installation, and operation of the system, component, or service;

  b. Effective use and maintenance of security and privacy functions and mechanisms; and

  c. Known vulnerabilities regarding configuration and use of administrative or privileged functions;


2. Obtain or develop user documentation for the system, system component, or system service that describes:

  d. User-accessible security and privacy functions and mechanisms and how to effectively use those functions and mechanisms;

  e. Methods for user interaction, which enables individuals to use the system, component, or service in a more secure manner and protect individual privacy; and

  f. User responsibilities in maintaining the security of the system, component, or service and privacy of individuals;


3. Document attempts to obtain system, system component, or system service documentation when such documentation is either unavailable or nonexistent and take [Assignment: organization-defined actions] in response; and


4. Distribute documentation to [Assignment: organization-defined personnel or roles].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-8 Security and Privacy Engineering Principles

Apply the following systems security and privacy engineering principles in the specification, design, development, implementation, and modification of the system and system components: [Assignment: organization-defined systems security and privacy engineering principles].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-8(1) Security and Privacy Engineering Principles | Clear Abstractions

Implement the security design principle of clear abstractions.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-8(2) Security and Privacy Engineering Principles | Least Common Mechanism

Implement the security design principle of least common mechanism in [Assignment: organization-defined systems or system components].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-8(3) Security and Privacy Engineering Principles | Modularity and Layering

Implement the security design principles of modularity and layering in [Assignment: organization-defined systems or system components].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-8(4) Security and Privacy Engineering Principles | Partially Ordered Dependencies

Implement the security design principle of partially ordered dependencies in [Assignment: organization-defined systems or system components].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-8(5) Security and Privacy Engineering Principles | Efficiently Mediated Access

Implement the security design principle of efficiently mediated access in [Assignment: organization-defined systems or system components].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-8(6) Security and Privacy Engineering Principles | Minimized Sharing

Implement the security design principle of minimized sharing in [Assignment: organization-defined systems or system components].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-8(7) Security and Privacy Engineering Principles | Reduced Complexity

Implement the security design principle of reduced complexity in [Assignment: organization-defined systems or system components].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-8(8) Security and Privacy Engineering Principles | Secure Evolvability

Implement the security design principle of secure evolvability in [Assignment: organization-defined systems or system components].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-8(9) Security and Privacy Engineering Principles | Trusted Components

Implement the security design principle of trusted components in [Assignment: organization-defined systems or system components].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-8(10) Security and Privacy Engineering Principles | Hierarchical Trust

Implement the security design principle of hierarchical trust in [Assignment: organization-defined systems or system components].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-8(11) Security and Privacy Engineering Principles | Inverse Modification Threshold

Implement the security design principle of inverse modification threshold in [Assignment: organization-defined systems or system components].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-8(12) Security and Privacy Engineering Principles | Hierarchical Protection

Implement the security design principle of hierarchical protection in [Assignment: organization-defined systems or system components].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-8(13) Security and Privacy Engineering Principles | Minimized Security Elements

Implement the security design principle of minimized security elements in [Assignment: organization-defined systems or system components].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-8(14) Security and Privacy Engineering Principles | Least Privilege

Implement the security design principle of least privilege in [Assignment: organization-defined systems or system components].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-8(15) Security and Privacy Engineering Principles | Predicate Permission

Implement the security design principle of predicate permission in [Assignment: organization-defined systems or system components].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-8(16) Security and Privacy Engineering Principles | Self-reliant Trustworthiness

Implement the security design principle of self-reliant trustworthiness in [Assignment: organization-defined systems or system components].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-8(17) Security and Privacy Engineering Principles | Secure Distributed Composition

Implement the security design principle of secure distributed composition in [Assignment: organization-defined systems or system components].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-8(18) Security and Privacy Engineering Principles | Trusted Communications Channels

Implement the security design principle of trusted communications channels in [Assignment: organization-defined systems or system components].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-8(19) Security and Privacy Engineering Principles | Continuous Protection

Implement the security design principle of continuous protection in [Assignment: organization-defined systems or system components].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-8(20) Security and Privacy Engineering Principles | Secure Metadata Management

Implement the security design principle of secure metadata management in [Assignment: organization-defined systems or system components].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-8(21) Security and Privacy Engineering Principles | Self-analysis

Implement the security design principle of self-analysis in [Assignment: organization-defined systems or system components].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-8(22) Security and Privacy Engineering Principles | Accountability and Traceability

Implement the security design principle of accountability and traceability in [Assignment: organization-defined systems or system components].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-8(23) Security and Privacy Engineering Principles | Secure Defaults

Implement the security design principle of secure defaults in [Assignment: organization-defined systems or system components].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-8(24) Security and Privacy Engineering Principles | Secure Failure and Recovery

Implement the security design principle of secure failure and recovery in [Assignment: organization-defined systems or system components].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-8(25) Security and Privacy Engineering Principles | Economic Security

Implement the security design principle of economic security in [Assignment: organization-defined systems or system components].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-8(26) Security and Privacy Engineering Principles | Performance Security

Implement the security design principle of performance security in [Assignment: organization-defined systems or system components].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-8(27) Security and Privacy Engineering Principles | Human Factored Security

Implement the security design principle of human factored security in [Assignment: organization-defined systems or system components].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-8(28) Security and Privacy Engineering Principles | Acceptable Security

Implement the security design principle of acceptable security in [Assignment: organization-defined systems or system components].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-8(29) Security and Privacy Engineering Principles | Repeatable and Documented Procedures

Implement the security design principle of repeatable and documented procedures in [Assignment: organization-defined systems or system components].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-8(30) Security and Privacy Engineering Principles | Procedural Rigor

Implement the security design principle of procedural rigor in [Assignment: organization-defined systems or system components].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-8(31) Security and Privacy Engineering Principles | Secure System Modification

Implement the security design principle of secure system modification in [Assignment: organization-defined systems or system components].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-8(32) Security and Privacy Engineering Principles | Sufficient Documentation

Implement the security design principle of sufficient documentation in [Assignment: organization-defined systems or system components].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-9 External System Services


1. Require that providers of external system services comply with organizational security and privacy requirements and employ the following controls: [Assignment: organization-defined controls];


2. Define and document organizational oversight and user roles and responsibilities with regard to external system services; and


3. Employ the following processes, methods, and techniques to monitor control compliance by external service providers on an ongoing basis: [Assignment: organization-defined processes, methods, and techniques].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-9(1) External System Services | Risk Assessments and Organizational Approvals


1. Conduct an organizational assessment of risk prior to the acquisition or outsourcing of information security services; and


2. Verify that the acquisition or outsourcing of dedicated information security services is approved by [Assignment: organization-defined personnel or roles].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-9 (2) External System Services | Identification of Functions, Ports, Protocols, and Services

Require providers of the following external system services to identify the functions, ports, protocols, and other services required for the use of such services: [Assignment: organization-defined external system services].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-9(3) External System Services | Establish and Maintain Trust Relationship with Providers

Establish, document, and maintain trust relationships with external service providers based on the following requirements, properties, factors, or conditions: [Assignment: organization-defined security and privacy requirements, properties, factors, or conditions defining acceptable trust relationships].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-9(8) External System Services | Processing and Storage Location — U.S. Jurisdiction

Restrict the geographic location of information processing and data storage to facilities located within in the legal jurisdictional boundary of the United States.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-10 Developer Configuration Management

Require the developer of the system, system component, or system service to:


1. Perform configuration management during system, component, or service [Selection (one or more): design; development; implementation; operation; disposal];


2. Document, manage, and control the integrity of changes to [Assignment: organization-defined configuration items under configuration management];


3. Implement only organization-approved changes to the system, component, or service;


4. Document approved changes to the system, component, or service and the potential security and privacy impacts of such changes; and


5. Track security flaws and flaw resolution within the system, component, or service and report findings to [Assignment: organization-defined personnel].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-10(1) Developer Configuration Management | Software and Firmware Integrity Verification

Require the developer of the system, system component, or system service to enable integrity verification of software and firmware components.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-10(3) Developer Configuration Management | Hardware Integrity Verification

Require the developer of the system, system component, or system service to enable integrity verification of hardware components.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-10(7) Developer Configuration Management | Security and Privacy Representatives

Require [Assignment: organization-defined security and privacy representatives] to be included in the [Assignment: organization-defined configuration change management and control process].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-11 Developer Testing and Evaluation

Require the developer of the system, system component, or system service, at all post-design stages of the system development life cycle, to:


1. Develop and implement a plan for ongoing security and privacy control assessments;


2. Perform [Selection (one or more): unit; integration; system; regression] testing/evaluation [Assignment: organization-defined frequency] at [Assignment: organization-defined depth and coverage];


3. Produce evidence of the execution of the assessment plan and the results of the testing and evaluation;


4. Implement a verifiable flaw remediation process; and


5. Correct flaws identified during testing and evaluation.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-11(1) Developer Testing and Evaluation | Static Code Analysis

Require the developer of the system, system component, or system service to employ static code analysis tools to identify common flaws and document the results of the analysis.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-11(2) Developer Testing and Evaluation | Threat Modeling and Vulnerability Analyses

Require the developer of the system, system component, or system service to perform threat modeling and vulnerability analyses during development and the subsequent testing and evaluation of the system, component, or service that:


1. Uses the following contextual information: [Assignment: organization-defined information concerning impact, environment of operations, known or assumed threats, and acceptable risk levels];


2. Employs the following tools and methods: [Assignment: organization-defined tools and methods];


3. Conducts the modeling and analyses at the following level of rigor: [Assignment: organization-defined breadth and depth of modeling and analyses]; and


4. Produces evidence that meets the following acceptance criteria: [Assignment: organization-defined acceptance criteria].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-15 Development Process, Standards, and Tools


1. Require the developer of the system, system component, or system service to follow a documented development process that:

  a. Explicitly addresses security and privacy requirements;

  b. Identifies the standards and tools used in the development process;

  c. Documents the specific tool options and tool configurations used in the development process; and

  d. Documents, manages, and ensures the integrity of changes to the process and/or tools used in development; and


2. Review the development process, standards, tools, tool options, and tool configurations [Assignment: organization-defined frequency] to determine if the process, standards, tools, tool options and tool configurations selected and employed can satisfy the following security and privacy requirements: [Assignment: organization-defined security and privacy requirements].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-15(3) Development Process, Standards, and Tools | Criticality Analysis

Require the developer of the system, system component, or system service to perform a criticality analysis:


1. At the following decision points in the system development life cycle: [Assignment: organization-defined decision points in the system development life cycle]; and


2. At the following level of rigor: [Assignment: organization-defined breadth and depth of criticality analysis].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-16 Developer-Provided Training

Require the developer of the system, system component, or system service to provide the following training on the correct use and operation of the implemented security and privacy functions, controls, and/or mechanisms: [Assignment: organization-defined training].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-17 Developer Security and Privacy Architecture and Design

Require the developer of the system, system component, or system service to produce a design specification and security and privacy architecture that:


1. Is consistent with the organization’s security and privacy architecture that is an integral part the organization’s enterprise architecture;


2. Accurately and completely describes the required security and privacy functionality, and the allocation of controls among physical and logical components; and


3. Expresses how individual security and privacy functions, mechanisms, and services work together to provide required security and privacy capabilities and a unified approach to protection.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-21 Developer Screening

Require that the developer of [Assignment: organization-defined system, system component, or system service]:


1. Has appropriate access authorizations as determined by assigned [Assignment: organization-defined official government duties]; and


2. Satisfies the following additional personnel screening criteria: [Assignment: organization-defined additional personnel screening criteria].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


### SA-22 Unsupported System Components


1. Replace system components when support for the components is no longer available from the developer, vendor, or manufacturer; or


2. Provide the following options for alternative sources for continued support for unsupported components [Selection (one or more): in-house support; [Assignment: organization-defined support from external providers]].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for Google hardware procurement and Titan security chip acquisition. The system platform uses peer-reviewed, security-hardened Terraform modules following secure SDLC principles. |


## 2.18 System and Communications Protection


### SC-1 Policies and Procedures


1. Develop, document, and disseminate to [Assignment: organization-defined personnel or roles]:

  a. [Selection (one or more): Organization-level; Mission/business process-level; System-level] system and communications protection policy that:

    - Addresses purpose, scope, roles, responsibilities, management commitment, coordination among organizational entities, and compliance; and

    - Is consistent with applicable laws, executive orders, directives, regulations, policies, standards, and guidelines; and

  b. Procedures to facilitate the implementation of the system and communications protection policy and the associated system and communications protection controls;


2. Designate an [Assignment: organization-defined official] to manage the development, documentation, and dissemination of the system and communications protection policy and procedures; and


3. Review and update the current system and communications protection:

  c. Policy [Assignment: organization-defined frequency] and following [Assignment: organization-defined events]; and

  d. Procedures [Assignment: organization-defined frequency] and following [Assignment: organization-defined events].


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) and FIPS 140-validated cryptographic backends. The system platform provisions VPC Service Controls security perimeters, Cloud Armor WAF protection, Cloud KMS CMEK encryption (AES-256), TLS 1.2+ transport security, Private Google Access, Cloud NAT, and Cloud DNS. |


### SC-2 Separation of System and User Functionality

Separate user functionality, including user interface services, from system management functionality.


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). Google LLC manages underlying infrastructure, GCI backends, and physical environment controls for SC-2. |


### SC-3 Security Function Isolation

Isolate security functions from nonsecurity functions.


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). Google LLC manages underlying infrastructure, GCI backends, and physical environment controls for SC-3. |


### SC-4 Information in Shared System Resources

Prevent unauthorized and unintended information transfer via shared system resources.


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). Google LLC manages underlying infrastructure, GCI backends, and physical environment controls for SC-4. |


### SC-5 Denial-of-Service Protection

1. [Selection: Protect against; Limit] the effects of the following types of denial-of-service events: [Assignment: organization-defined types of denial-of-service events]; and


2. Employ the following controls to achieve the denial-of-service objective: [Assignment: organization-defined controls by type of denial-of-service event].


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) and FIPS 140-validated cryptographic backends. The system platform provisions VPC Service Controls security perimeters, Cloud Armor WAF protection, Cloud KMS CMEK encryption (AES-256), TLS 1.2+ transport security, Private Google Access, Cloud NAT, and Cloud DNS. |


### SC-5(1) Denial-of-service Protection | Restrict Ability to Attack Other Systems

Restrict the ability of individuals to launch the following denial-of-service attacks against other systems: [Assignment: organization-defined denial-of-service attacks].


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) and FIPS 140-validated cryptographic backends. The system platform provisions VPC Service Controls security perimeters, Cloud Armor WAF protection, Cloud KMS CMEK encryption (AES-256), TLS 1.2+ transport security, Private Google Access, Cloud NAT, and Cloud DNS. |


### SC-5(2) Denial-of-Service Protection | Capacity, Bandwidth, and Redundancy

Manage capacity, bandwidth, or other redundancy to limit the effects of information flooding denial-of-service attacks.


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) and FIPS 140-validated cryptographic backends. The system platform provisions VPC Service Controls security perimeters, Cloud Armor WAF protection, Cloud KMS CMEK encryption (AES-256), TLS 1.2+ transport security, Private Google Access, Cloud NAT, and Cloud DNS. |


### SC-5(3) Denial-of-Service Protection | Detection and Monitoring


1. Employ the following monitoring tools to detect indicators of denial-of-service attacks against, or launched from, the system: [Assignment: organization-defined monitoring tools]; and


2. Monitor the following system resources to determine if sufficient resources exist to prevent effective denial-of-service attacks: [Assignment: organization-defined system resources].


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) and FIPS 140-validated cryptographic backends. The system platform provisions VPC Service Controls security perimeters, Cloud Armor WAF protection, Cloud KMS CMEK encryption (AES-256), TLS 1.2+ transport security, Private Google Access, Cloud NAT, and Cloud DNS. |


### SC-7 Boundary Protection


1. Monitor and control communications at the external managed interfaces to the system and at key internal managed interfaces within the system;


2. Implement subnetworks for publicly accessible system components that are [Selection: physically; logically] separated from internal organizational networks; and


3. Connect to external networks or systems only through managed interfaces consisting of boundary protection devices arranged in accordance with an organizational security and privacy architecture.


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for physical datacenter boundary isolation and Google Common Infrastructure (GCI) edge routing. Logical network perimeters are enforced through VPC ingress/egress firewall rules, isolated multi-tier subnet topologies, VPC Service Controls security perimeters, Cloud Armor web application filtering, and Private Google Access, denying unauthorized cross-boundary communications. |


### SC-7(3) Boundary Protection | Access Points

Limit the number of external network connections to the system.


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for physical datacenter boundary isolation and Google Common Infrastructure (GCI) edge routing. Logical network perimeters are enforced through VPC ingress/egress firewall rules, isolated multi-tier subnet topologies, VPC Service Controls security perimeters, Cloud Armor web application filtering, and Private Google Access, denying unauthorized cross-boundary communications. |


### SC-7(4) Boundary Protection | External Telecommunications Services


1. Implement a managed interface for each external telecommunication service;


2. Establish a traffic flow policy for each managed interface;


3. Protect the confidentiality and integrity of the information being transmitted across each interface;


4. Document each exception to the traffic flow policy with a supporting mission or business need and duration of that need;


5. Review exceptions to the traffic flow policy [Assignment: organization-defined frequency] and remove exceptions that are no longer supported by an explicit mission or business need;


6. Prevent unauthorized exchange of control plane traffic with external networks;


7. Publish information to enable remote networks to detect unauthorized control plane traffic from internal networks; and


8. Filter unauthorized control plane traffic from external networks.


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for physical datacenter boundary isolation and Google Common Infrastructure (GCI) edge routing. Logical network perimeters are enforced through VPC ingress/egress firewall rules, isolated multi-tier subnet topologies, VPC Service Controls security perimeters, Cloud Armor web application filtering, and Private Google Access, denying unauthorized cross-boundary communications. |


### SC-7(5) Boundary Protection | Deny by Default — Allow by Exception

Deny network communications traffic by default and allow network communications traffic by exception [Selection (one or more): at managed interfaces; for [Assignment: organization-defined systems]].


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for physical datacenter boundary isolation and Google Common Infrastructure (GCI) edge routing. Logical network perimeters are enforced through VPC ingress/egress firewall rules, isolated multi-tier subnet topologies, VPC Service Controls security perimeters, Cloud Armor web application filtering, and Private Google Access, denying unauthorized cross-boundary communications. |


### SC-7(7) Boundary Protection | Split Tunneling for Remote Devices

Prevent split tunneling for remote devices connecting to organizational systems unless the split tunnel is securely provisioned using [Assignment: organization-defined safeguards].


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for physical datacenter boundary isolation and Google Common Infrastructure (GCI) edge routing. Logical network perimeters are enforced through VPC ingress/egress firewall rules, isolated multi-tier subnet topologies, VPC Service Controls security perimeters, Cloud Armor web application filtering, and Private Google Access, denying unauthorized cross-boundary communications. |


### SC-7(8) Boundary Protection | Route Traffic to Authenticated Proxy Servers

Route [Assignment: organization-defined internal communications traffic] to [Assignment: organization-defined external networks] through authenticated proxy servers at managed interfaces.


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for physical datacenter boundary isolation and Google Common Infrastructure (GCI) edge routing. Logical network perimeters are enforced through VPC ingress/egress firewall rules, isolated multi-tier subnet topologies, VPC Service Controls security perimeters, Cloud Armor web application filtering, and Private Google Access, denying unauthorized cross-boundary communications. |


### SC-7(9) Boundary Protection | Route Traffic to Authenticated Proxy Servers


1. Detect and deny outgoing communications traffic posing a threat to external systems; and


2. Audit the identity of internal users associated with denied communications.


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for physical datacenter boundary isolation and Google Common Infrastructure (GCI) edge routing. Logical network perimeters are enforced through VPC ingress/egress firewall rules, isolated multi-tier subnet topologies, VPC Service Controls security perimeters, Cloud Armor web application filtering, and Private Google Access, denying unauthorized cross-boundary communications. |


### SC-7(10) Boundary Protection | Prevent Exfiltration


1. Prevent the exfiltration of information; and


2. Conduct exfiltration tests [Assignment: organization-defined frequency].


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for physical datacenter boundary isolation and Google Common Infrastructure (GCI) edge routing. Logical network perimeters are enforced through VPC ingress/egress firewall rules, isolated multi-tier subnet topologies, VPC Service Controls security perimeters, Cloud Armor web application filtering, and Private Google Access, denying unauthorized cross-boundary communications. |


### SC-7(11) Boundary Protection | Restrict Incoming Communications Traffic

Only allow incoming communications from [Assignment: organization-defined authorized sources] to be routed to [Assignment: organization-defined authorized destinations].


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for physical datacenter boundary isolation and Google Common Infrastructure (GCI) edge routing. Logical network perimeters are enforced through VPC ingress/egress firewall rules, isolated multi-tier subnet topologies, VPC Service Controls security perimeters, Cloud Armor web application filtering, and Private Google Access, denying unauthorized cross-boundary communications. |


### SC-7(12) Boundary Protection | Host-based Protection

Implement [Assignment: organization-defined host-based boundary protection mechanisms] at [Assignment: organization-defined system components].


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for physical datacenter boundary isolation and Google Common Infrastructure (GCI) edge routing. Logical network perimeters are enforced through VPC ingress/egress firewall rules, isolated multi-tier subnet topologies, VPC Service Controls security perimeters, Cloud Armor web application filtering, and Private Google Access, denying unauthorized cross-boundary communications. |


### SC-7(13) Boundary Protection | Isolation of Security Tools, Mechanisms, and Support Components

Isolate [Assignment: organization-defined information security tools, mechanisms, and support components] from other internal system components by implementing physically separate subnetworks with managed interfaces to other components of the system.


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for physical datacenter boundary isolation and Google Common Infrastructure (GCI) edge routing. Logical network perimeters are enforced through VPC ingress/egress firewall rules, isolated multi-tier subnet topologies, VPC Service Controls security perimeters, Cloud Armor web application filtering, and Private Google Access, denying unauthorized cross-boundary communications. |


### SC-7(14) Boundary Protection | Protect Against Unauthorized Physical Connections

Protect against unauthorized physical connections at [Assignment: organization-defined managed interfaces].


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for physical datacenter boundary isolation and Google Common Infrastructure (GCI) edge routing. Logical network perimeters are enforced through VPC ingress/egress firewall rules, isolated multi-tier subnet topologies, VPC Service Controls security perimeters, Cloud Armor web application filtering, and Private Google Access, denying unauthorized cross-boundary communications. |


### SC-7(15) Boundary Protection | Network Privileged Accesses

Route networked, privileged accesses through a dedicated, managed interface for purposes of access control and auditing.


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for physical datacenter boundary isolation and Google Common Infrastructure (GCI) edge routing. Logical network perimeters are enforced through VPC ingress/egress firewall rules, isolated multi-tier subnet topologies, VPC Service Controls security perimeters, Cloud Armor web application filtering, and Private Google Access, denying unauthorized cross-boundary communications. |


### SC-7(18) Boundary Protection | Fail Secure

Prevent systems from entering unsecure states in the event of an operational failure of a boundary protection device.


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for physical datacenter boundary isolation and Google Common Infrastructure (GCI) edge routing. Logical network perimeters are enforced through VPC ingress/egress firewall rules, isolated multi-tier subnet topologies, VPC Service Controls security perimeters, Cloud Armor web application filtering, and Private Google Access, denying unauthorized cross-boundary communications. |


### SC-7(21) Boundary Protection | Isolation of System Components

Employ boundary protection mechanisms to isolate [Assignment: organization-defined system components] supporting [Assignment: organization-defined missions and/or business functions].


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for physical datacenter boundary isolation and Google Common Infrastructure (GCI) edge routing. Logical network perimeters are enforced through VPC ingress/egress firewall rules, isolated multi-tier subnet topologies, VPC Service Controls security perimeters, Cloud Armor web application filtering, and Private Google Access, denying unauthorized cross-boundary communications. |


### SC-7(25) Boundary Protection | Unclassified National Security System Connections

Prohibit the direct connection of [Assignment: organization-defined unclassified national security system] to an external network without the use of [Assignment: organization-defined boundary protection device].


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for physical datacenter boundary isolation and Google Common Infrastructure (GCI) edge routing. Logical network perimeters are enforced through VPC ingress/egress firewall rules, isolated multi-tier subnet topologies, VPC Service Controls security perimeters, Cloud Armor web application filtering, and Private Google Access, denying unauthorized cross-boundary communications. |


### SC-7(28) Boundary Protection | Connections to Public Networks

Prohibit the direct connection of [Assignment: organization-defined system] to a public network.


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for physical datacenter boundary isolation and Google Common Infrastructure (GCI) edge routing. Logical network perimeters are enforced through VPC ingress/egress firewall rules, isolated multi-tier subnet topologies, VPC Service Controls security perimeters, Cloud Armor web application filtering, and Private Google Access, denying unauthorized cross-boundary communications. |


### SC-7(29) Boundary Protection | Separate Subnets to Isolate Functions

Implement [Selection: physically; logically] separate subnetworks to isolate the following critical system components and functions: [Assignment: organization-defined critical system components and functions].


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for physical datacenter boundary isolation and Google Common Infrastructure (GCI) edge routing. Logical network perimeters are enforced through VPC ingress/egress firewall rules, isolated multi-tier subnet topologies, VPC Service Controls security perimeters, Cloud Armor web application filtering, and Private Google Access, denying unauthorized cross-boundary communications. |


### SC-8 Transmission Confidentiality and Integrity

Protect the [Selection (one or more): confidentiality; integrity] of transmitted information.


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for physical inter-datacenter backbone MACsec encryption and internal RPC mTLS. All system communications across internal and external network interfaces enforce FIPS 140-validated TLS 1.2+ encryption for data in transit, disabling legacy cipher suites and unencrypted plaintext protocols across all public and internal service endpoints. |


### SC-8(1) Transmission Confidentiality and Integrity | Cryptographic Protection

Implement cryptographic mechanisms to [Selection (one or more): prevent unauthorized disclosure of information; detect changes to information] during transmission.


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for physical inter-datacenter backbone MACsec encryption and internal RPC mTLS. All system communications across internal and external network interfaces enforce FIPS 140-validated TLS 1.2+ encryption for data in transit, disabling legacy cipher suites and unencrypted plaintext protocols across all public and internal service endpoints. |


### SC-8(2) Transmission Confidentiality and Integrity | Pre- and Post-transmission Handling

Maintain the [Selection (one or more): confidentiality; integrity] of information during preparation for transmission and during reception.


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for physical inter-datacenter backbone MACsec encryption and internal RPC mTLS. All system communications across internal and external network interfaces enforce FIPS 140-validated TLS 1.2+ encryption for data in transit, disabling legacy cipher suites and unencrypted plaintext protocols across all public and internal service endpoints. |


### SC-10 Network Disconnect

Terminate the network connection associated with a communications session at the end of the session or after [Assignment: organization-defined time period] of inactivity.


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) and FIPS 140-validated cryptographic backends. The system platform provisions VPC Service Controls security perimeters, Cloud Armor WAF protection, Cloud KMS CMEK encryption (AES-256), TLS 1.2+ transport security, Private Google Access, Cloud NAT, and Cloud DNS. |


### SC-12 Cryptographic Key Establishment and Management

Establish and manage cryptographic keys when cryptography is employed within the system in accordance with the following key management requirements: [Assignment: organization-defined requirements for key generation, distribution, storage, access, and destruction].


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) and FIPS 140-validated cryptographic backends. The system platform provisions VPC Service Controls security perimeters, Cloud Armor WAF protection, Cloud KMS CMEK encryption (AES-256), TLS 1.2+ transport security, Private Google Access, Cloud NAT, and Cloud DNS. |


### SC-12(1) Cryptographic Key Establishment and Management | Availability

Maintain availability of information in the event of the loss of cryptographic keys by users.


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) and FIPS 140-validated cryptographic backends. The system platform provisions VPC Service Controls security perimeters, Cloud Armor WAF protection, Cloud KMS CMEK encryption (AES-256), TLS 1.2+ transport security, Private Google Access, Cloud NAT, and Cloud DNS. |


### SC-13 Cryptographic Protection


1. Determine the [Assignment: organization-defined cryptographic uses]; and


2. Implement the following types of cryptography required for each specified cryptographic use: [Assignment: organization-defined types of cryptography for each specified cryptographic use].


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) and FIPS 140-validated cryptographic backends. The system platform provisions VPC Service Controls security perimeters, Cloud Armor WAF protection, Cloud KMS CMEK encryption (AES-256), TLS 1.2+ transport security, Private Google Access, Cloud NAT, and Cloud DNS. |


### SC-15 Collaborative Computing Devices and Applications


1. Prohibit remote activation of collaborative computing devices and applications with the following exceptions: [Assignment: organization-defined exceptions where remote activation is to be allowed]; and


2. Provide an explicit indication of use to users physically present at the devices.


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). Google LLC manages underlying infrastructure, GCI backends, and physical environment controls for SC-15. |


### SC-16 Transmission of Security and Privacy Attributes

Associate [Assignment: organization-defined security and privacy attributes] with information exchanged between systems and between system components.


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) and FIPS 140-validated cryptographic backends. The system platform provisions VPC Service Controls security perimeters, Cloud Armor WAF protection, Cloud KMS CMEK encryption (AES-256), TLS 1.2+ transport security, Private Google Access, Cloud NAT, and Cloud DNS. |


### SC-16(1) Transmission of Security and Privacy Attributes | Integrity Verification

Verify the integrity of transmitted security and privacy attributes.


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) and FIPS 140-validated cryptographic backends. The system platform provisions VPC Service Controls security perimeters, Cloud Armor WAF protection, Cloud KMS CMEK encryption (AES-256), TLS 1.2+ transport security, Private Google Access, Cloud NAT, and Cloud DNS. |


### SC-16(2) Transmission of Security and Privacy Attributes | Anti-spoofing Mechanisms

Implement anti-spoofing mechanisms to prevent adversaries from falsifying the security attributes indicating the successful application of the security process.


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) and FIPS 140-validated cryptographic backends. The system platform provisions VPC Service Controls security perimeters, Cloud Armor WAF protection, Cloud KMS CMEK encryption (AES-256), TLS 1.2+ transport security, Private Google Access, Cloud NAT, and Cloud DNS. |


### SC-16(3) Transmission of Security and Privacy Attributes | Cryptographic Binding

Implement [Assignment: organization-defined mechanisms or techniques] to bind security and privacy attributes to transmitted information.


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) and FIPS 140-validated cryptographic backends. The system platform provisions VPC Service Controls security perimeters, Cloud Armor WAF protection, Cloud KMS CMEK encryption (AES-256), TLS 1.2+ transport security, Private Google Access, Cloud NAT, and Cloud DNS. |


### SC-17 Public Key Infrastructure Certificates


1. Issue public key certificates under an [Assignment: organization-defined certificate policy] or obtain public key certificates from an approved service provider; and


2. Include only approved trust anchors in trust stores or certificate stores managed by the organization.


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) and FIPS 140-validated cryptographic backends. The system platform provisions VPC Service Controls security perimeters, Cloud Armor WAF protection, Cloud KMS CMEK encryption (AES-256), TLS 1.2+ transport security, Private Google Access, Cloud NAT, and Cloud DNS. |


### SC-18 Mobile Code


1. Define acceptable and unacceptable mobile code and mobile code technologies; and


2. Authorize, monitor, and control the use of mobile code within the system.


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) and FIPS 140-validated cryptographic backends. The system platform provisions VPC Service Controls security perimeters, Cloud Armor WAF protection, Cloud KMS CMEK encryption (AES-256), TLS 1.2+ transport security, Private Google Access, Cloud NAT, and Cloud DNS. |


### SC-18(1) Mobile Code | Identify Unacceptable Code and Take Corrective Actions

Identify [Assignment: organization-defined unacceptable mobile code] and take [Assignment: organization-defined corrective actions].


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) and FIPS 140-validated cryptographic backends. The system platform provisions VPC Service Controls security perimeters, Cloud Armor WAF protection, Cloud KMS CMEK encryption (AES-256), TLS 1.2+ transport security, Private Google Access, Cloud NAT, and Cloud DNS. |


### SC-18(2) Mobile Code | Acquisition, Development, and Use

Verify that the acquisition, development, and use of mobile code to be deployed in the system meets [Assignment: organization-defined mobile code requirements].


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) and FIPS 140-validated cryptographic backends. The system platform provisions VPC Service Controls security perimeters, Cloud Armor WAF protection, Cloud KMS CMEK encryption (AES-256), TLS 1.2+ transport security, Private Google Access, Cloud NAT, and Cloud DNS. |


### SC-18(3) Mobile Code | Prevent Downloading and Execution

Prevent the download and execution of [Assignment: organization-defined unacceptable mobile code].


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) and FIPS 140-validated cryptographic backends. The system platform provisions VPC Service Controls security perimeters, Cloud Armor WAF protection, Cloud KMS CMEK encryption (AES-256), TLS 1.2+ transport security, Private Google Access, Cloud NAT, and Cloud DNS. |


### SC-18(4) Mobile Code | Prevent Automatic Execution

Prevent the automatic execution of mobile code in [Assignment: organization-defined software applications] and enforce [Assignment: organization-defined actions] prior to executing the code.


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) and FIPS 140-validated cryptographic backends. The system platform provisions VPC Service Controls security perimeters, Cloud Armor WAF protection, Cloud KMS CMEK encryption (AES-256), TLS 1.2+ transport security, Private Google Access, Cloud NAT, and Cloud DNS. |


### SC-20 Secure Name/Address Resolution Service (Authoritative Source)


1. Provide additional data origin authentication and integrity verification artifacts along with the authoritative name resolution data the system returns in response to external name/address resolution queries; and


2. Provide the means to indicate the security status of child zones and (if the child supports secure resolution services) to enable verification of a chain of trust among parent and child domains, when operating as part of a distributed, hierarchical namespace.


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). Google LLC manages underlying infrastructure, GCI backends, and physical environment controls for SC-20. |


### SC-21 Secure Name/Address Resolution Service (Recursive or Caching Resolver)

Request and perform data origin authentication and data integrity verification on the name/address resolution responses the system receives from authoritative sources.


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). Google LLC manages underlying infrastructure, GCI backends, and physical environment controls for SC-21. |


### SC-22 Architecture and Provisioning for Name/Address Resolution Service

Ensure the systems that collectively provide name/address resolution service for an organization are fault-tolerant and implement internal and external role separation.


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). Google LLC manages underlying infrastructure, GCI backends, and physical environment controls for SC-22. |


### SC-23 Session Authenticity

Protect the authenticity of communications sessions.


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). Google LLC manages underlying infrastructure, GCI backends, and physical environment controls for SC-23. |


### SC-23(1) Session Authenticity | Invalidate Session Identifiers at Logout

Invalidate session identifiers upon user logout or other session termination.


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) and FIPS 140-validated cryptographic backends. The system platform provisions VPC Service Controls security perimeters, Cloud Armor WAF protection, Cloud KMS CMEK encryption (AES-256), TLS 1.2+ transport security, Private Google Access, Cloud NAT, and Cloud DNS. |


### SC-23(3) Session Authenticity | Unique System-generated Session Identifiers

Generate a unique session identifier for each session with [Assignment: organization-defined randomness requirements] and recognize only session identifiers that are system-generated.


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) and FIPS 140-validated cryptographic backends. The system platform provisions VPC Service Controls security perimeters, Cloud Armor WAF protection, Cloud KMS CMEK encryption (AES-256), TLS 1.2+ transport security, Private Google Access, Cloud NAT, and Cloud DNS. |


### SC-23(5) Session Authenticity | Allowed Certificate Authorities

Only allow the use of [Assignment: organization-defined certificate authorities] for verification of the establishment of protected sessions.


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) and FIPS 140-validated cryptographic backends. The system platform provisions VPC Service Controls security perimeters, Cloud Armor WAF protection, Cloud KMS CMEK encryption (AES-256), TLS 1.2+ transport security, Private Google Access, Cloud NAT, and Cloud DNS. |


### SC-24 Fail in Known State

Fail to a [Assignment: organization-defined known system state] for the following failures on the indicated components while preserving [Assignment: organization-defined system state information] in failure: [Assignment: list of organization-defined types of system failures on organization-defined system components].


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). Google LLC manages underlying infrastructure, GCI backends, and physical environment controls for SC-24. |


### SC-28 Protection of Information at Rest

Protect the [Selection (one or more): confidentiality; integrity] of the following information at rest: [Assignment: organization-defined information at rest].


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for default hardware-level AES-256 encryption across all physical persistent storage media. System persistent data repositories (Cloud Storage, persistent disks, databases) enforce cryptographic protection using FIPS 140-validated cryptographic modules with Customer-Managed Encryption Keys (CMEK) via Cloud KMS, automated key rotation, and separation of duties. |


### SC-28(1) Protection of Information at Rest | Cryptographic Protection

Implement cryptographic mechanisms to prevent unauthorized disclosure and modification of the following information at rest on [Assignment: organization-defined system components or media]: [Assignment: organization-defined information].


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for default hardware-level AES-256 encryption across all physical persistent storage media. System persistent data repositories (Cloud Storage, persistent disks, databases) enforce cryptographic protection using FIPS 140-validated cryptographic modules with Customer-Managed Encryption Keys (CMEK) via Cloud KMS, automated key rotation, and separation of duties. |


### SC-28(3) Protection of Information at Rest | Cryptographic Keys

Provide protected storage for cryptographic keys [Selection: [Assignment: organization-defined safeguards]; hardware-protected key store].


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for default hardware-level AES-256 encryption across all physical persistent storage media. System persistent data repositories (Cloud Storage, persistent disks, databases) enforce cryptographic protection using FIPS 140-validated cryptographic modules with Customer-Managed Encryption Keys (CMEK) via Cloud KMS, automated key rotation, and separation of duties. |


### SC-38 Operations Security

Employ the following operations security controls to protect key organizational information throughout the system development life cycle: [Assignment: organization-defined operations security controls].


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) and FIPS 140-validated cryptographic backends. The system platform provisions VPC Service Controls security perimeters, Cloud Armor WAF protection, Cloud KMS CMEK encryption (AES-256), TLS 1.2+ transport security, Private Google Access, Cloud NAT, and Cloud DNS. |


### SC-39 Process Isolation

Maintain a separate execution domain for each executing system process.


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). Google LLC manages underlying infrastructure, GCI backends, and physical environment controls for SC-39. |


### SC-41 Port and I/O Device Access

[Selection: Physically; Logically] disable or remove [Assignment: organization-defined connection ports or input/output devices] on the following systems or system components: [Assignment: organization-defined systems or system components].


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) and FIPS 140-validated cryptographic backends. The system platform provisions VPC Service Controls security perimeters, Cloud Armor WAF protection, Cloud KMS CMEK encryption (AES-256), TLS 1.2+ transport security, Private Google Access, Cloud NAT, and Cloud DNS. |


### SC-45 System Time Synchronization

Synchronize system clocks within and between systems and system components.


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) and FIPS 140-validated cryptographic backends. The system platform provisions VPC Service Controls security perimeters, Cloud Armor WAF protection, Cloud KMS CMEK encryption (AES-256), TLS 1.2+ transport security, Private Google Access, Cloud NAT, and Cloud DNS. |


### SC-45(1) System Time Synchronization | Synchronization with Authoritative Time Source


1. Compare the internal system clocks [Assignment: organization-defined frequency] with [Assignment: organization-defined authoritative time source]; and


2. Synchronize the internal system clocks to the authoritative time source when the time difference is greater than [Assignment: organization-defined time period].


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) and FIPS 140-validated cryptographic backends. The system platform provisions VPC Service Controls security perimeters, Cloud Armor WAF protection, Cloud KMS CMEK encryption (AES-256), TLS 1.2+ transport security, Private Google Access, Cloud NAT, and Cloud DNS. |


### SC-47 Alternate Communications Paths

Establish [Assignment: organization-defined alternate communications paths] for system operations organizational command and control.


| Control Summary Information |
| :--- |
| **Responsible Role**: Network Engineer & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}) for Google Common Infrastructure (GCI) and FIPS 140-validated cryptographic backends. The system platform provisions VPC Service Controls security perimeters, Cloud Armor WAF protection, Cloud KMS CMEK encryption (AES-256), TLS 1.2+ transport security, Private Google Access, Cloud NAT, and Cloud DNS. |


## 2.19 System and Information Integrity


### SI-1 Policy and Procedures


1. Develop, document, and disseminate to [Assignment: organization-defined personnel or roles]:

  a. [Selection (one or more): Organization-level; Mission/business process-level; System-level] system and information integrity policy that:

    - Addresses purpose, scope, roles, responsibilities, management commitment, coordination among organizational entities, and compliance; and

    - Is consistent with applicable laws, executive orders, directives, regulations, policies, standards, and guidelines; and

  b. Procedures to facilitate the implementation of the system and information integrity policy and the associated system and information integrity controls;


2. Designate an [Assignment: organization-defined official] to manage the development, documentation, and dissemination of the system and information integrity policy and procedures; and


3. Review and update the current system and information integrity:

  c. Policy [Assignment: organization-defined frequency] and following [Assignment: organization-defined events]; and

  d. Procedures [Assignment: organization-defined frequency] and following [Assignment: organization-defined events].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for hypervisor memory isolation, host malware protection, and automated binary integrity verification. The system platform enforces container image vulnerability scanning in Artifact Registry, real-time threat detection in SCC, and automated OS patch management via VM Manager. |


### SI-2 Flaw Remediation


1. Identify, report, and correct system flaws;


2. Test software and firmware updates related to flaw remediation for effectiveness and potential side effects before installation;


3. Install security-relevant software and firmware updates within [Assignment: organization-defined time period] of the release of the updates; and


4. Incorporate flaw remediation into the organizational configuration management process.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for hypervisor memory isolation, host malware protection, and automated binary integrity verification. The system platform enforces container image vulnerability scanning in Artifact Registry, real-time threat detection in SCC, and automated OS patch management via VM Manager. |


### SI-2(2) Flaw Remediation | Automated Flaw Remediation Status

Determine if system components have applicable security-relevant software and firmware updates installed using [Assignment: organization-defined automated mechanisms] [Assignment: organization-defined frequency].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for hypervisor memory isolation, host malware protection, and automated binary integrity verification. The system platform enforces container image vulnerability scanning in Artifact Registry, real-time threat detection in SCC, and automated OS patch management via VM Manager. |


### SI-2(3) Flaw Remediation | Time to Remediate Flaws and Benchmarks for Corrective Actions


1. Measure the time between flaw identification and flaw remediation; and


2. Establish the following benchmarks for taking corrective actions: [Assignment: organization-defined benchmarks].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for hypervisor memory isolation, host malware protection, and automated binary integrity verification. The system platform enforces container image vulnerability scanning in Artifact Registry, real-time threat detection in SCC, and automated OS patch management via VM Manager. |


### SI-2(4) Flaw Remediation | Automated Patch Management Tools

Employ automated patch management tools to facilitate flaw remediation to the following system components: [Assignment: organization-defined system components].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for hypervisor memory isolation, host malware protection, and automated binary integrity verification. The system platform enforces container image vulnerability scanning in Artifact Registry, real-time threat detection in SCC, and automated OS patch management via VM Manager. |


### SI-2(6) Flaw Remediation | Removal of Previous Versions of Software and Firmware

Remove previous versions of [Assignment: organization-defined software and firmware components] after updated versions have been installed.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for hypervisor memory isolation, host malware protection, and automated binary integrity verification. The system platform enforces container image vulnerability scanning in Artifact Registry, real-time threat detection in SCC, and automated OS patch management via VM Manager. |


### SI-3 Malicious Code Protection


1. Implement [Selection (one or more): signature based; non-signature based] malicious code protection mechanisms at system entry and exit points to detect and eradicate malicious code;


2. Automatically update malicious code protection mechanisms as new releases are available in accordance with organizational configuration management policy and procedures;


3. Configure malicious code protection mechanisms to:

  a. Perform periodic scans of the system [Assignment: organization-defined frequency] and real-time scans of files from external sources at [Selection (one or more): endpoint; network entry and exit points] as the files are downloaded, opened, or executed in accordance with organizational policy; and

  b. [Selection (one or more): block malicious code; quarantine malicious code; take [Assignment: organization-defined action]]; and send alert to [Assignment: organization-defined personnel or roles] in response to malicious code detection; and


4. Address the receipt of false positives during malicious code detection and eradication and the resulting potential impact on the availability of the system.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for hypervisor memory isolation, host malware protection, and automated binary integrity verification. The system platform enforces container image vulnerability scanning in Artifact Registry, real-time threat detection in SCC, and automated OS patch management via VM Manager. |


### SI-3(10) Malicious Code Protection | Malicious Code Analysis


1. Employ the following tools and techniques to analyze the characteristics and behavior of malicious code: [Assignment: organization-defined tools and techniques]; and


2. Incorporate the results from malicious code analysis into organizational incident response and flaw remediation processes.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for hypervisor memory isolation, host malware protection, and automated binary integrity verification. The system platform enforces container image vulnerability scanning in Artifact Registry, real-time threat detection in SCC, and automated OS patch management via VM Manager. |


### SI-4 System Monitoring


1. Monitor the system to detect:

  a. Attacks and indicators of potential attacks in accordance with the following monitoring objectives: [Assignment: organization-defined monitoring objectives]; and

  b. Unauthorized local, network, and remote connections;


2. Identify unauthorized use of the system through the following techniques and methods: [Assignment: organization-defined techniques and methods];


3. Invoke internal monitoring capabilities or deploy monitoring devices:

  c. Strategically within the system to collect organization-determined essential information; and

  d. At ad hoc locations within the system to track specific types of transactions of interest to the organization;


4. Analyze detected events and anomalies;


5. Adjust the level of system monitoring activity when there is a change in risk to organizational operations and assets, individuals, other organizations, or the Nation;


6. Obtain legal opinion regarding system monitoring activities; and


7. Provide [Assignment: organization-defined system monitoring information] to [Assignment: organization-defined personnel or roles] [Selection (one or more): as needed; [Assignment: organization-defined frequency]].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for hypervisor memory isolation, host malware protection, and automated binary integrity verification. The system platform enforces container image vulnerability scanning in Artifact Registry, real-time threat detection in SCC, and automated OS patch management via VM Manager. |


### SI-4(1) System Monitoring | System-wide Intrusion Detection System

Connect and configure individual intrusion detection tools into a system-wide intrusion detection system.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for hypervisor memory isolation, host malware protection, and automated binary integrity verification. The system platform enforces container image vulnerability scanning in Artifact Registry, real-time threat detection in SCC, and automated OS patch management via VM Manager. |


### SI-4(2) System Monitoring | Automated Tools and Mechanisms for Real-time Analysis

Employ automated tools and mechanisms to support near real-time analysis of events.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for hypervisor memory isolation, host malware protection, and automated binary integrity verification. The system platform enforces container image vulnerability scanning in Artifact Registry, real-time threat detection in SCC, and automated OS patch management via VM Manager. |


### SI-4(4) System Monitoring | Inbound and Outbound Communications Traffic


1. Determine criteria for unusual or unauthorized activities or conditions for inbound and outbound communications traffic;


2. Monitor inbound and outbound communications traffic [Assignment: organization-defined frequency] for [Assignment: organization-defined unusual or unauthorized activities or conditions].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for hypervisor memory isolation, host malware protection, and automated binary integrity verification. The system platform enforces container image vulnerability scanning in Artifact Registry, real-time threat detection in SCC, and automated OS patch management via VM Manager. |


### SI-4(5) System Monitoring | System-generated Alerts

Alert [Assignment: organization-defined personnel or roles] when the following system-generated indications of compromise or potential compromise occur: [Assignment: organization-defined compromise indicators].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for hypervisor memory isolation, host malware protection, and automated binary integrity verification. The system platform enforces container image vulnerability scanning in Artifact Registry, real-time threat detection in SCC, and automated OS patch management via VM Manager. |


### SI-4(10) System Monitoring | Visibility of Encrypted Communications

Make provisions so that [Assignment: organization-defined encrypted communications traffic] is visible to [Assignment: organization-defined system monitoring tools and mechanisms].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for hypervisor memory isolation, host malware protection, and automated binary integrity verification. The system platform enforces container image vulnerability scanning in Artifact Registry, real-time threat detection in SCC, and automated OS patch management via VM Manager. |


### SI-4(11) System Monitoring | Analyze Communications Traffic Anomalies

Analyze outbound communications traffic at the external interfaces to the system and selected [Assignment: organization-defined interior points within the system] to discover anomalies.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for hypervisor memory isolation, host malware protection, and automated binary integrity verification. The system platform enforces container image vulnerability scanning in Artifact Registry, real-time threat detection in SCC, and automated OS patch management via VM Manager. |


### SI-4(12) System Monitoring | Automated Organization-generated Alerts

Alert [Assignment: organization-defined personnel or roles] using [Assignment: organization-defined automated mechanisms] when the following indications of inappropriate or unusual activities with security or privacy implications occur: [Assignment: organization-defined activities that trigger alerts].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for hypervisor memory isolation, host malware protection, and automated binary integrity verification. The system platform enforces container image vulnerability scanning in Artifact Registry, real-time threat detection in SCC, and automated OS patch management via VM Manager. |


### SI-4(14) System Monitoring | Wireless Intrusion Detection

Employ a wireless intrusion detection system to identify rogue wireless devices and to detect attack attempts and potential compromises or breaches to the system.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for hypervisor memory isolation, host malware protection, and automated binary integrity verification. The system platform enforces container image vulnerability scanning in Artifact Registry, real-time threat detection in SCC, and automated OS patch management via VM Manager. |


### SI-4(15) System Monitoring | Wireless to Wireline Communications

Employ an intrusion detection system to monitor wireless communications traffic as the traffic passes from wireless to wireline networks.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for hypervisor memory isolation, host malware protection, and automated binary integrity verification. The system platform enforces container image vulnerability scanning in Artifact Registry, real-time threat detection in SCC, and automated OS patch management via VM Manager. |


### SI-4(16) System Monitoring | Correlate Monitoring Information

Correlate information from monitoring tools and mechanisms employed throughout the system.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for hypervisor memory isolation, host malware protection, and automated binary integrity verification. The system platform enforces container image vulnerability scanning in Artifact Registry, real-time threat detection in SCC, and automated OS patch management via VM Manager. |


### SI-4(19) System Monitoring | Risk for Individuals

Implement [Assignment: organization-defined additional monitoring] of individuals who have been identified by [Assignment: organization-defined sources] as posing an increased level of risk.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for hypervisor memory isolation, host malware protection, and automated binary integrity verification. The system platform enforces container image vulnerability scanning in Artifact Registry, real-time threat detection in SCC, and automated OS patch management via VM Manager. |


### SI-4(20) System Monitoring | Privileged Users

Implement the following additional monitoring of privileged users: [Assignment: organization-defined additional monitoring].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for hypervisor memory isolation, host malware protection, and automated binary integrity verification. The system platform enforces container image vulnerability scanning in Artifact Registry, real-time threat detection in SCC, and automated OS patch management via VM Manager. |


### SI-4(22) System Monitoring | Unauthorized Network Services


1. Detect network services that have not been authorized or approved by [Assignment: organization-defined authorization or approval processes]; and

2. [Selection (one or more): Audit; Alert [Assignment: organization-defined personnel or roles]] when detected.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for hypervisor memory isolation, host malware protection, and automated binary integrity verification. The system platform enforces container image vulnerability scanning in Artifact Registry, real-time threat detection in SCC, and automated OS patch management via VM Manager. |


### SI-4(23) System Monitoring | Host-based Devices

Implement the following host-based monitoring mechanisms at [Assignment: organization-defined system components]: [Assignment: organization-defined host-based monitoring mechanisms].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for hypervisor memory isolation, host malware protection, and automated binary integrity verification. The system platform enforces container image vulnerability scanning in Artifact Registry, real-time threat detection in SCC, and automated OS patch management via VM Manager. |


### SI-4(24) System Monitoring | Indicators of Compromise

Discover, collect, and distribute to [Assignment: organization-defined personnel or roles], indicators of compromise provided by [Assignment: organization-defined sources].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for hypervisor memory isolation, host malware protection, and automated binary integrity verification. The system platform enforces container image vulnerability scanning in Artifact Registry, real-time threat detection in SCC, and automated OS patch management via VM Manager. |


### SI-4(25) System Monitoring | Optimize Network Traffic Analysis

Provide visibility into network traffic at external and key internal system interfaces to optimize the effectiveness of monitoring devices.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for hypervisor memory isolation, host malware protection, and automated binary integrity verification. The system platform enforces container image vulnerability scanning in Artifact Registry, real-time threat detection in SCC, and automated OS patch management via VM Manager. |


### SI-5 Security Alerts, Advisories, and Directives


1. Receive system security alerts, advisories, and directives from [Assignment: organization-defined external organizations] on an ongoing basis;


2. Generate internal security alerts, advisories, and directives as deemed necessary;


3. Disseminate security alerts, advisories, and directives to: [Selection (one or more): [Assignment: organization-defined personnel or roles]; [Assignment: organization-defined elements within the organization]; [Assignment: organization-defined external organizations]]; and


4. Implement security directives in accordance with established time frames, or notify the issuing organization of the degree of noncompliance.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for hypervisor memory isolation, host malware protection, and automated binary integrity verification. The system platform enforces container image vulnerability scanning in Artifact Registry, real-time threat detection in SCC, and automated OS patch management via VM Manager. |


### SI-5(1) Security Alerts, Advisories, and Directives | Automated Alerts and Advisories

Broadcast security alert and advisory information throughout the organization using [Assignment: organization-defined automated mechanisms].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for hypervisor memory isolation, host malware protection, and automated binary integrity verification. The system platform enforces container image vulnerability scanning in Artifact Registry, real-time threat detection in SCC, and automated OS patch management via VM Manager. |


### SI-6 Security and Privacy Function Verification


1. Verify the correct operation of [Assignment: organization-defined security and privacy functions];


2. Perform the verification of the functions specified in SI-6a [Selection (one or more): [Assignment: organization-defined system transitional states]; upon command by user with appropriate privilege; [Assignment: organization-defined frequency]];


3. Alert [Assignment: organization-defined personnel or roles] to failed security and privacy verification tests; and

4. [Selection (one or more): Shut the system down; Restart the system; [Assignment: organization-defined alternative action(s)]] when anomalies are discovered.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for hypervisor memory isolation, host malware protection, and automated binary integrity verification. The system platform enforces container image vulnerability scanning in Artifact Registry, real-time threat detection in SCC, and automated OS patch management via VM Manager. |


### SI-6(3) Security and Privacy Function Verification | Report Verification Results

Report the results of security and privacy function verification to [Assignment: organization-defined personnel or roles].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for hypervisor memory isolation, host malware protection, and automated binary integrity verification. The system platform enforces container image vulnerability scanning in Artifact Registry, real-time threat detection in SCC, and automated OS patch management via VM Manager. |


### SI-7 Software, Firmware, and Information Integrity


1. Employ integrity verification tools to detect unauthorized changes to the following software, firmware, and information: [Assignment: organization-defined software, firmware, and information]; and


2. Take the following actions when unauthorized changes to the software, firmware, and information are detected: [Assignment: organization-defined actions].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for hypervisor memory isolation, host malware protection, and automated binary integrity verification. The system platform enforces container image vulnerability scanning in Artifact Registry, real-time threat detection in SCC, and automated OS patch management via VM Manager. |


### SI-7(1) Software, Firmware, and Information Integrity | Integrity Checks

Perform an integrity check of [Assignment: organization-defined software, firmware, and information] [Selection (one or more): at startup; at [Assignment: organization-defined transitional states or security-relevant events]; [Assignment: organization-defined frequency]].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for hypervisor memory isolation, host malware protection, and automated binary integrity verification. The system platform enforces container image vulnerability scanning in Artifact Registry, real-time threat detection in SCC, and automated OS patch management via VM Manager. |


### SI-7(2) Software, Firmware, and Information Integrity | Automated Notifications of Integrity Violations

Employ automated tools that provide notification to [Assignment: organization-defined personnel or roles] upon discovering discrepancies during integrity verification.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for hypervisor memory isolation, host malware protection, and automated binary integrity verification. The system platform enforces container image vulnerability scanning in Artifact Registry, real-time threat detection in SCC, and automated OS patch management via VM Manager. |


### SI-7(5) Software, Firmware, and Information Integrity | Automated Response to Integrity Violations

Automatically [Selection (one or more): shut the system down; restart the system; implement [Assignment: organization-defined controls]] when integrity violations are discovered.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for hypervisor memory isolation, host malware protection, and automated binary integrity verification. The system platform enforces container image vulnerability scanning in Artifact Registry, real-time threat detection in SCC, and automated OS patch management via VM Manager. |


### SI-7(7) Software, Firmware, and Information Integrity | Integration of Detection and Response

Incorporate the detection of the following unauthorized changes into the organizational incident response capability: [Assignment: organization-defined security-relevant changes to the system].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for hypervisor memory isolation, host malware protection, and automated binary integrity verification. The system platform enforces container image vulnerability scanning in Artifact Registry, real-time threat detection in SCC, and automated OS patch management via VM Manager. |


### SI-7(8) Software, Firmware, and Information Integrity | Auditing Capability for Significant Events

Upon detection of a potential integrity violation, provide the capability to audit the event and initiate the following actions: [Selection (one or more): generate an audit record; alert current user; alert [Assignment: organization-defined personnel or roles]; [Assignment: organization-defined other actions]].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for hypervisor memory isolation, host malware protection, and automated binary integrity verification. The system platform enforces container image vulnerability scanning in Artifact Registry, real-time threat detection in SCC, and automated OS patch management via VM Manager. |


### SI-7(9) Software, Firmware, and Information Integrity | Verify Boot Process

Verify the integrity of the boot process of the following system components: [Assignment: organization-defined system components].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for hypervisor memory isolation, host malware protection, and automated binary integrity verification. The system platform enforces container image vulnerability scanning in Artifact Registry, real-time threat detection in SCC, and automated OS patch management via VM Manager. |


### SI-7(10) Software, Firmware, and Information Integrity | Protection of Boot Firmware

Implement the following mechanisms to protect the integrity of boot firmware in [Assignment: organization-defined system components]: [Assignment: organization-defined mechanisms].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for hypervisor memory isolation, host malware protection, and automated binary integrity verification. The system platform enforces container image vulnerability scanning in Artifact Registry, real-time threat detection in SCC, and automated OS patch management via VM Manager. |


### SI-7(15) Software, Firmware, and Information Integrity | Code Authentication

Implement cryptographic mechanisms to authenticate the following software or firmware components prior to installation: [Assignment: organization-defined software or firmware components].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for hypervisor memory isolation, host malware protection, and automated binary integrity verification. The system platform enforces container image vulnerability scanning in Artifact Registry, real-time threat detection in SCC, and automated OS patch management via VM Manager. |


### SI-7(17) Software, Firmware, and Information Integrity | Runtime Application Self-Protection

Implement [Assignment: organization-defined controls] for application self-protection at runtime.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for hypervisor memory isolation, host malware protection, and automated binary integrity verification. The system platform enforces container image vulnerability scanning in Artifact Registry, real-time threat detection in SCC, and automated OS patch management via VM Manager. |


### SI-8 Spam Protection


1. Employ spam protection mechanisms at system entry and exit points to detect and act on unsolicited messages; and


2. Update spam protection mechanisms when new releases are available in accordance with organizational configuration management policy and procedures.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for hypervisor memory isolation, host malware protection, and automated binary integrity verification. The system platform enforces container image vulnerability scanning in Artifact Registry, real-time threat detection in SCC, and automated OS patch management via VM Manager. |


### SI-8(2) Spam Protection | Automatic Updates

Automatically update spam protection mechanisms [Assignment: organization-defined frequency].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for hypervisor memory isolation, host malware protection, and automated binary integrity verification. The system platform enforces container image vulnerability scanning in Artifact Registry, real-time threat detection in SCC, and automated OS patch management via VM Manager. |


### SI-10 Information Input Validation

Check the validity of the following information inputs: [Assignment: organization-defined information inputs to the system].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). Google LLC manages underlying infrastructure, GCI backends, and physical environment controls for SI-10. |


### SI-10(3) Information Input Validation | Predictable Behavior

Verify that the system behaves in a predictable and documented manner when invalid inputs are received.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for hypervisor memory isolation, host malware protection, and automated binary integrity verification. The system platform enforces container image vulnerability scanning in Artifact Registry, real-time threat detection in SCC, and automated OS patch management via VM Manager. |


### SI-10(5) Information Input Validation | Restrict Inputs to Trusted Sources and Approved Formats

Restrict the use of information inputs to [Assignment: organization-defined trusted sources] and/or [Assignment: organization-defined formats].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for hypervisor memory isolation, host malware protection, and automated binary integrity verification. The system platform enforces container image vulnerability scanning in Artifact Registry, real-time threat detection in SCC, and automated OS patch management via VM Manager. |


### SI-10(6) Information Input Validation | Injection Prevention

Prevent untrusted data injections.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for hypervisor memory isolation, host malware protection, and automated binary integrity verification. The system platform enforces container image vulnerability scanning in Artifact Registry, real-time threat detection in SCC, and automated OS patch management via VM Manager. |


### SI-11 Error Handling


1. Generate error messages that provide information necessary for corrective actions without revealing information that could be exploited; and


2. Reveal error messages only to [Assignment: organization-defined personnel or roles].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). Google LLC manages underlying infrastructure, GCI backends, and physical environment controls for SI-11. |


### SI-12 Information Management and Retention

Manage and retain information within the system and information output from the system in accordance with applicable laws, executive orders, directives, regulations, policies, standards, guidelines and operational requirements.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for hypervisor memory isolation, host malware protection, and automated binary integrity verification. The system platform enforces container image vulnerability scanning in Artifact Registry, real-time threat detection in SCC, and automated OS patch management via VM Manager. |


### SI-12(3) Information Management and Retention | Information Disposal

Use the following techniques to dispose of, destroy, or erase information following the retention period: [Assignment: organization-defined techniques].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for hypervisor memory isolation, host malware protection, and automated binary integrity verification. The system platform enforces container image vulnerability scanning in Artifact Registry, real-time threat detection in SCC, and automated OS patch management via VM Manager. |


### SI-15 Information Output Filtering

Validate information output from the following software programs and/or applications to ensure that the information is consistent with the expected content: [Assignment: organization-defined software programs and/or applications].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for hypervisor memory isolation, host malware protection, and automated binary integrity verification. The system platform enforces container image vulnerability scanning in Artifact Registry, real-time threat detection in SCC, and automated OS patch management via VM Manager. |


### SI-16 Memory Protection

Implement the following controls to protect the system memory from unauthorized code execution: [Assignment: organization-defined controls].


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [ ] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited 100% from Google Services FedRAMP High / IL5 P-ATO (Package ID: {{ CSP_PATO_PACKAGE_ID }}). Google LLC manages underlying infrastructure, GCI backends, and physical environment controls for SI-16. |


### SI-21 Information Refresh

Refresh [Assignment: organization-defined information] at [Assignment: organization-defined frequencies] or generate the information on demand and delete the information when no longer needed.


| Control Summary Information |
| :--- |
| **Responsible Role**: DevSecOps Lead & Cloud Service Provider (Google LLC) |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for hypervisor memory isolation, host malware protection, and automated binary integrity verification. The system platform enforces container image vulnerability scanning in Artifact Registry, real-time threat detection in SCC, and automated OS patch management via VM Manager. |


## 2.20 Supply Chain Risk Management


### SR-1 Policy and Procedures


1. Develop, document, and disseminate to [Assignment: organization-defined personnel or roles]:

  a. [Selection (one or more): Organization-level; Mission/business process-level; System-level] supply chain risk management policy that:

    - Addresses purpose, scope, roles, responsibilities, management commitment, coordination among organizational entities, and compliance; and

    - Is consistent with applicable laws, executive orders, directives, regulations, policies, standards, and guidelines; and

  b. Procedures to facilitate the implementation of the supply chain risk management policy and the associated supply chain risk management controls;


2. Designate an [Assignment: organization-defined official] to manage the development, documentation, and dissemination of the supply chain risk management policy and procedures; and


3. Review and update the current supply chain risk management:

  c. Policy [Assignment: organization-defined frequency] and following [Assignment: organization-defined events]; and

  d. Procedures [Assignment: organization-defined frequency] and following [Assignment: organization-defined events].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for hardware supply chain security, proprietary server manufacturing, and Titan security chip provenance. The system platform implements Binary Authorization policies to ensure only signed, verified container images run in production. |


### SR-2 Supply Chain Risk Management Plan


1. Develop a plan for managing supply chain risks associated with the research and development, design, manufacturing, acquisition, delivery, integration, operations and maintenance, and disposal of the following systems, system components or system services: [Assignment: organization-defined systems, system components, or system services];


2. Review and update the supply chain risk management plan [Assignment: organization-defined frequency] or as required, to address threat, organizational or environmental changes; and


3. Protect the supply chain risk management plan from unauthorized disclosure and modification.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for hardware supply chain security, proprietary server manufacturing, and Titan security chip provenance. The system platform implements Binary Authorization policies to ensure only signed, verified container images run in production. |


### SR-2(1) Supply Chain Risk Management Plan | Establish SCRM Team

Establish a supply chain risk management team consisting of [Assignment: organization-defined personnel, roles, and responsibilities] to lead and support the following SCRM activities: [Assignment: organization-defined supply chain risk management activities].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for hardware supply chain security, proprietary server manufacturing, and Titan security chip provenance. The system platform implements Binary Authorization policies to ensure only signed, verified container images run in production. |


### SR-3 Supply Chain Controls and Processes


1. Establish a process or processes to identify and address weaknesses or deficiencies in the supply chain elements and processes of [Assignment: organization-defined system or system component] in coordination with [Assignment: organization-defined supply chain personnel];


2. Employ the following controls to protect against supply chain risks to the system, system component, or system service and to limit the harm or consequences from supply chain-related events: [Assignment: organization-defined supply chain controls]; and


3. Document the selected and implemented supply chain processes and controls in [Selection: security and privacy plans; supply chain risk management plan; [Assignment: organization-defined document]].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for hardware supply chain security, proprietary server manufacturing, and Titan security chip provenance. The system platform implements Binary Authorization policies to ensure only signed, verified container images run in production. |


### SR-3(1) Supply Chain Controls and Processes | Diverse Supply Base

Employ a diverse set of sources for the following system components and services: [Assignment: organization-defined system components and services].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for hardware supply chain security, proprietary server manufacturing, and Titan security chip provenance. The system platform implements Binary Authorization policies to ensure only signed, verified container images run in production. |


### SR-3(2) Supply Chain Controls and Processes | Limitation of Harm

Employ the following controls to limit harm from potential adversaries identifying and targeting the organizational supply chain: [Assignment: organization-defined controls].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for hardware supply chain security, proprietary server manufacturing, and Titan security chip provenance. The system platform implements Binary Authorization policies to ensure only signed, verified container images run in production. |


### SR-3(3) Supply Chain Controls and Processes | Sub-tier Flow Down

Ensure that the controls included in the contracts of prime contractors are also included in the contracts of subcontractors.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for hardware supply chain security, proprietary server manufacturing, and Titan security chip provenance. The system platform implements Binary Authorization policies to ensure only signed, verified container images run in production. |


### SR-4 Provenance

Document, monitor, and maintain valid provenance of the following systems, system components, and associated data: [Assignment: organization-defined systems, system components, and associated data].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for hardware supply chain security, proprietary server manufacturing, and Titan security chip provenance. The system platform implements Binary Authorization policies to ensure only signed, verified container images run in production. |


### SR-5 Acquisition Strategies, Tools, and Methods

Employ the following acquisition strategies, contract tools, and procurement methods to protect against, identify, and mitigate supply chain risks: [Assignment: organization-defined acquisition strategies, contract tools, and procurement methods].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for hardware supply chain security, proprietary server manufacturing, and Titan security chip provenance. The system platform implements Binary Authorization policies to ensure only signed, verified container images run in production. |


### SR-5(1) Acquisition Strategies, Tools, and Methods | Adequate Supply

Employ the following controls to ensure an adequate supply of [Assignment: organization-defined critical system components]: [Assignment: organization-defined controls].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for hardware supply chain security, proprietary server manufacturing, and Titan security chip provenance. The system platform implements Binary Authorization policies to ensure only signed, verified container images run in production. |


### SR-5(2) Acquisition Strategies, Tools, and Methods | Assessments Prior to Selection, Acceptance, Modification, or Update

Assess the system, system component, or system service prior to selection, acceptance, modification, or update.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for hardware supply chain security, proprietary server manufacturing, and Titan security chip provenance. The system platform implements Binary Authorization policies to ensure only signed, verified container images run in production. |


### SR-6 Supplier Assessments and Reviews

Assess and review the supply chain-related risks associated with suppliers or contractors and the system, system component, or system service they provide [Assignment: organization-defined frequency].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for hardware supply chain security, proprietary server manufacturing, and Titan security chip provenance. The system platform implements Binary Authorization policies to ensure only signed, verified container images run in production. |


### SR-6(1) Supplier Assessments and Reviews | Testing and Analysis

Employ [Selection (one or more): organizational analysis; independent third-party analysis; organizational testing; independent third-party testing] of the following supply chain elements, processes, and actors associated with the system, system component, or system service: [Assignment: organization-defined supply chain elements, processes, and actors].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for hardware supply chain security, proprietary server manufacturing, and Titan security chip provenance. The system platform implements Binary Authorization policies to ensure only signed, verified container images run in production. |


### SR-7 Supply Chain Operations Security

Employ the following Operations Security (OPSEC) controls to protect supply chain-related information for the system, system component, or system service: [Assignment: organization-defined Operations Security (OPSEC) controls].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for hardware supply chain security, proprietary server manufacturing, and Titan security chip provenance. The system platform implements Binary Authorization policies to ensure only signed, verified container images run in production. |


### SR-8 Notification Agreements

Establish agreements and procedures with entities involved in the supply chain for the system, system component, or system service for the [Selection (one or more): notification of supply chain compromises; results of assessments or audits; [Assignment: organization-defined information]].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for hardware supply chain security, proprietary server manufacturing, and Titan security chip provenance. The system platform implements Binary Authorization policies to ensure only signed, verified container images run in production. |


### SR-9 Tamper Resistance and Detection

Implement a tamper protection program for the system, system component, or system service.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for hardware supply chain security, proprietary server manufacturing, and Titan security chip provenance. The system platform implements Binary Authorization policies to ensure only signed, verified container images run in production. |


### SR-9(1) Tamper Resistance and Detection | Multiple Stages of System Development Life Cycle

Employ anti-tamper technologies, tools, and techniques throughout the system development life cycle.


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for hardware supply chain security, proprietary server manufacturing, and Titan security chip provenance. The system platform implements Binary Authorization policies to ensure only signed, verified container images run in production. |


### SR-10 Inspection of Systems or Components

Inspect the following systems or system components [Selection (one or more): at random; at [Assignment: organization-defined frequency], upon [Assignment: organization-defined indications of need for inspection]] to detect tampering: [Assignment: organization-defined systems or system components].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for hardware supply chain security, proprietary server manufacturing, and Titan security chip provenance. The system platform implements Binary Authorization policies to ensure only signed, verified container images run in production. |


### SR-11 Component Authenticity


1. Develop and implement anti-counterfeit policy and procedures that include the means to detect and prevent counterfeit components from entering the system; and


2. Report counterfeit system components to [Selection (one or more): source of counterfeit component; [Assignment: organization-defined external reporting organizations]; [Assignment: organization-defined personnel or roles]].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for hardware supply chain security, proprietary server manufacturing, and Titan security chip provenance. The system platform implements Binary Authorization policies to ensure only signed, verified container images run in production. |


### SR-11(1) Component Authenticity | Anti-counterfeit Training

Train [Assignment: organization-defined personnel or roles] to detect counterfeit system components (including hardware, software, and firmware).


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for hardware supply chain security, proprietary server manufacturing, and Titan security chip provenance. The system platform implements Binary Authorization policies to ensure only signed, verified container images run in production. |


### SR-11(2) Component Authenticity | Configuration Control for Component Service and Repair

Maintain configuration control over the following system components awaiting service or repair and serviced or repaired components awaiting return to service: [Assignment: organization-defined system components].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for hardware supply chain security, proprietary server manufacturing, and Titan security chip provenance. The system platform implements Binary Authorization policies to ensure only signed, verified container images run in production. |


### SR-12 Component Disposal

Dispose of [Assignment: organization-defined data, documentation, tools, or system components] using the following techniques and methods: [Assignment: organization-defined techniques and methods].


| Control Summary Information |
| :--- |
| **Responsible Role**: Cloud Service Provider (Google LLC) & DevSecOps Lead |
| **Implementation Status (check all that apply)**:<br>- [ ] Implemented<br>- [x] Partially Implemented (Hybrid)<br>- [ ] Planned<br>- [x] Inherited<br>- [ ] Not Applicable |
| **Control Implementation Statement**:<br>Inherited from Google Services P-ATO for hardware supply chain security, proprietary server manufacturing, and Titan security chip provenance. The system platform implements Binary Authorization policies to ensure only signed, verified container images run in production. |
