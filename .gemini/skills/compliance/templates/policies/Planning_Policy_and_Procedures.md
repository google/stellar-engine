# PL - Planning Policy and Procedures

## Document Governance & Approval Baseline

| Governance Metric | Policy Standard & Specification |
| :--- | :--- |
| **Document Title** | Planning Policy and Procedures |
| **NIST Control Family** | Planning (PL) |
| **Primary NIST Benchmark** | NIST SP 800-18 Rev. 1 (Guide for Developing Security Plans for Federal Systems) |
| **Target System Name** | {{ SYSTEM_NAME }} ({{ SYSTEM_ABBREVIATION }}) |
| **Security Categorization** | {{ FIPS_199_CATEGORIZATION }} ({{ IMPACT_LEVEL }}) |
| **Governing Entity** | {{ ORGANIZATION }} |
| **Document Owner** | {{ ISSM_NAME }} ({{ ISSM_TITLE }}) |
| **Approval Authority** | {{ AO_NAME }} ({{ AO_TITLE }}) |
| **Review Frequency** | Annual (At least once every 365 days) and upon significant architectural changes |
| **Effective Date** | {{ DATE }} |
| **Policy Version** | {{ VERSION }} |

### Document Authorization Signatures

| Role / Authority | Designated Official | Signature & Date |
| :--- | :--- | :--- |
| **PREPARED BY:** | Google Public Sector LLC (GPS) RMF & Security Engineering Team | Signature: ______________________ Date: {{ DATE }} |
| **REVIEWED & RECOMMENDED BY:** | {{ ISSO_NAME }}<br>{{ ISSO_TITLE }}, {{ ORGANIZATION }} | Signature: ______________________ Date: {{ DATE }} |
| **REVIEWED & RECOMMENDED BY:** | {{ ISSM_NAME }}<br>{{ ISSM_TITLE }}, {{ ORGANIZATION }} | Signature: ______________________ Date: {{ DATE }} |
| **APPROVED BY:** | {{ SO_NAME }}<br>{{ SO_TITLE }}, {{ ORGANIZATION }} | Signature: ______________________ Date: {{ DATE }} |

### Document Change Record

| Date | Version | Author / Prepared By | Changes Made / Section(s) Description |
| :--- | :--- | :--- | :--- |
| {{ DATE }} | {{ VERSION }} | {{ ORGANIZATION }} / GPS RMF Team | Initial formal baseline institutionalization under NIST SP 800-53 Rev. 5 / {{ COMPLIANCE_BASELINE }} governance. |

### Program Roles & Responsibilities Matrix

| Organizational Role | Assigned Authority | Primary Policy Enforcement & Compliance Responsibilities |
| :--- | :--- | :--- |
| **Authorizing Official (AO)** | {{ AO_NAME }} ({{ AO_TITLE }}) | Formally approves policy statements, risk tolerance thresholds, Exception-to-Policy (ETP) memorandums, and official ATO decisions. |
| **System Owner (SO)** | {{ SO_NAME }} ({{ SO_TITLE }}) | Ensures system operations align with policy requirements, manages operational resources, and approves operational change requests. |
| **ISSM** | {{ ISSM_NAME }} ({{ ISSM_TITLE }}) | Oversees enterprise cybersecurity policy enforcement, manages annual policy review cadences, and maintains compliance evidence. |
| **ISSO** | {{ ISSO_NAME }} ({{ ISSO_TITLE }}) | Conducts continuous security monitoring, audits system configurations, oversees technical countermeasures, and tracks POA&M remediation. |
| **DevSecOps Engineers** | Platform Engineering Team | Implements automated technical controls via Terraform Infrastructure as Code (IaC), CI/CD pipelines, and cloud platform configurations. |

> [!NOTE]
> **Policy Scope & Automation Level**
> This document defines the enterprise security policy and implementation procedures for **Planning** under **NIST SP 800-53 Rev. 5 (PL)**.
> Technical infrastructure controls are automatically provisioned and enforced via **{{ SYSTEM_NAME }}** Terraform blueprints.
> Operational rules or contact details requiring manual confirmation are highlighted with RMF Team Callouts.


## 1. Overview

The objective of security planning is to improve protection of information system resources. The protection of a system must be documented in a system security plan.

DoD and NIST standards are used to categorize all information and information systems collected or maintained by or on behalf of each Department based on the objectives of providing appropriate levels of information security according to a range of risk level. For {{ ORGANIZATION }}, the potential impact values assigned to the respective security objectives (FIPS PUB 199 / NIST SP 800-60) are:

- **Confidentiality Impact Level**: `{{ CONFIDENTIALITY_IMPACT }}`
- **Integrity Impact Level**: `{{ INTEGRITY_IMPACT }}`
- **Availability Impact Level**: `{{ AVAILABILITY_IMPACT }}`

The Risk Management Framework (RMF) decision structure includes cybersecurity requirements managed through RMF consistent with the principles established in NIST SP 800-37 Rev. 2.

This plan ensures that {{ ORGANIZATION }} follows the established guidelines and requirements for security planning. The formal System Security Plan is documented separately. The purpose of this document is to consolidate information and provide traceability to security control requirements.

This document complies with {{ COMPLIANCE_BASELINE }} and is consistent with applicable laws, executive orders, directives, regulations, policies, standards, and guidelines. A detailed compliance matrix can be found in Appendix A, “Detailed Compliance Matrix”.


## 2. Policy and Procedures

Planning policy and procedures for the controls in the planning family are implemented within systems and organizations. Events that may precipitate an update to planning policy and procedures include, but are not limited to, assessment or audit findings, security incidents or breaches, or changes in laws, executive orders, directives, regulations, policies, standards, and guidelines.

{{ ORGANIZATION }} complies with applicable security planning policy mandates. Applicable regulations establish security planning policy for {{ GOVERNANCE_REGIME }}. Designated organizational personnel are assigned planning responsibilities or information security responsibilities.

The RMF has the following characteristics:

- Promotes the concept of near real-time risk management and ongoing information system authorization through the implementation of robust continuous monitoring processes;

- Encourages the use of automation to provide senior leaders the necessary information to make cost-effective, risk-based decisions with regard to the organizational information systems supporting their core missions and business functions;

- Integrates information security into the enterprise architecture and system development life cycle;

- Provides emphasis on the selection, implementation, assessment, and monitoring of security controls, and the authorization of information systems;

- Links risk management processes at the information system level to risk management processes at the organization level through a risk executive (function); and,

- Establishes responsibility and accountability for security controls deployed within organizational information systems and inherited by those systems (i.e., common controls).

The {{ ORGANIZATION }} Cybersecurity Team is responsible to develop and document this system-level Planning Policy and Procedures and to disseminate them to all {{ ORGANIZATION }} systems, with updates completed as necessary to account for changes in processes, requirements, and applicable training.

This document will be reviewed and updated no less than annually by the {{ ORGANIZATION }} Cybersecurity Team. Updates will consider changes required due to updates to the enterprise architecture documentation; system security plan; privacy plan; records of system security and privacy plan reviews and updates; security and privacy architecture and design documentation; risk assessments; risk assessment results; control assessment documentation; and other relevant documents or records.



### 2.1 Google Cloud Platform (GCP) Inherited Controls & Shared Responsibility Boundary

- **Google Inherited Controls**: Google Cloud maintains CSP System Security Plans, architectural baselines (`PL-2`), and security planning across all GCP cloud regions.
- **Customer Implementation Responsibilities**: {{ ORGANIZATION }} is responsible for developing the system's System Security Plan (SSP) (`PL-2`), Rules of Behavior (RoB) (`PL-4`), and updating architecture planning documentation annually.

## 3. System Security and Privacy Plans

The purpose of the System Security Plan (SSP) is to provide an overview of the security requirements of {{ ORGANIZATION }} {{ SYSTEM_NAME }} and describe the controls in place or planned for meeting those requirements. The SSP also delineates responsibilities and expected behavior of all individuals who access {{ ORGANIZATION }} systems.

The purpose of the Privacy Plan is to detail the privacy controls selected for an information system or environment of operation that are in place or planned for meeting applicable privacy requirements and managing privacy risks, including how the controls have been implemented, and describes the methodologies and metrics that will be used to assess the controls.

Additionally, all {{ ORGANIZATION }} systems will develop these plans to be consistent with the systems architecture and will:

- Define system components, operational context, roles, and responsibilities.

- Identify information types processed, stored, and transmitted.

- Provide a security categorization of the system.

- Describe specific threats and vulnerabilities.

- Present the results of privacy risk assessments.

- Detail the operational environment and system dependencies.

- Outline security and privacy requirements and controls.

- Identify relevant control baselines and tailoring decisions.

- Include risk determinations for architectural and design decisions.

- Address coordination with relevant individuals and groups.

Copies of these plans will reside within each system’s {{ RMF_GOVERNANCE_SYSTEM }} package and will be provided to {{ ORGANIZATION }} PMO leadership upon request.


## 4. Rules of Behavior

Rules of behavior represent a type of access agreement for organizational users. {{ ORGANIZATION }} utilizes user access request form (`<mark style="background-color: #fff9c4; color: #b71c1c; font-weight: bold; padding: 1px 5px; border-radius: 3px;">⚠️ RMF TEAM ACTION REQUIRED: Rules of Behavior / Access Request Form</mark>`) as the methodology to request and grant access to {{ ORGANIZATION }} {{ SYSTEM_NAME }}.  {{ ORGANIZATION }} also utilizes an Acceptable Use Policy (AUP) which all users, both general and privileged, must sign.

The AUP has clearly defined and established rules describing {{ ORGANIZATION }} user responsibilities and expected behavior regarding information and information system usage for system users.

> [!IMPORTANT]
> <mark style="background-color: #fff9c4; color: #b71c1c; font-weight: bold; padding: 2px 6px; border-radius: 4px;">⚠️ RMF TEAM ACTION REQUIRED: Verify and update operational contact/procedure details in this section.</mark>
> user access request form (`<mark style="background-color: #fff9c4; color: #b71c1c; font-weight: bold; padding: 1px 5px; border-radius: 3px;">⚠️ RMF TEAM ACTION REQUIRED: Rules of Behavior / Access Request Form</mark>`) and AUPs are stored with the ISSM/ISSO and are reviewed on an annual basis. The user access request form (`<mark style="background-color: #fff9c4; color: #b71c1c; font-weight: bold; padding: 1px 5px; border-radius: 3px;">⚠️ RMF TEAM ACTION REQUIRED: Rules of Behavior / Access Request Form</mark>`) is shared with required parties via email.  In the event the user access request form (`<mark style="background-color: #fff9c4; color: #b71c1c; font-weight: bold; padding: 1px 5px; border-radius: 3px;">⚠️ RMF TEAM ACTION REQUIRED: Rules of Behavior / Access Request Form</mark>`) is revised, updated, or the type of access is changing, the end user must read and resign the form.

Furthermore, all {{ ORGANIZATION }} systems will require users with elevated or privileged access to sign the {{ ORGANIZATION }} Privileged Access Agreement (PAA).  The PAA outlines the acceptable use and training requirements to maintain privileged access.


### 4.1 Social Media and External Site/Application Usage Restrictions

The {{ ORGANIZATION }} AUP, which all users must sign, contains the following information in regard to social media and posting to public websites:

- Explicit restrictions on the use of social media/networking sites IAW DoDI 8550.01

- Explicit restrictions on posting organizational information on public websites and applications IAW DoDI 8550.01

Any sharing or posting of DoD data to social media or public websites will be subject to disciplinary action to include loss of clearance and termination.


## 5. Concept of Operations

{{ ORGANIZATION }} will maintain a Concept of Operations (CONOPS) for {{ SYSTEM_NAME }} describing how they intend to operate the system from a perspective of information security and privacy.

The CONOPS can be a stand alone document, or be included in various security or privacy plans for {{ SYSTEM_NAME }}; and it is intended to be a living document that is updated throughout the system development life cycle, and at least annually.

The CONOPS should contain information relating to the system architecture and the operational procedures. Changes to the CONOPS should be reflected in security and privacy plans, architectures, and other related documentation.


## 6. Security and Privacy Architectures

{{ ORGANIZATION }} will develop and maintain security and privacy architectures for {{ SYSTEM_NAME }} and {{ SYSTEM_NAME }}. This architecture will be used to show how {{ ORGANIZATION }} protects the confidentiality, integrity, and availability of data within {{ SYSTEM_NAME }} and {{ SYSTEM_NAME }}, as well as any internal or external connections to supporting systems. {{ ORGANIZATION }} utilizes a defense in depth approach to ensure adversaries have to defeat multiple controls before achieving their objective. Additionally, {{ ORGANIZATION }} ensures supplier diversity to manage the various strengths and weaknesses within various technologies.

System Security Plan Appendix A & Architecture Specification


## 7. Central Management

{{ ORGANIZATION }} will centrally manage the planning, implementing, assessing, authorizing, and monitoring processes. This ensures consistent processes throughout {{ ORGANIZATION }}, not only within {{ SYSTEM_NAME }} and {{ SYSTEM_NAME }}.


## 8. Baseline Selection

{{ ORGANIZATION }} will select a baseline set of controls based during the control selection phase of the RMF process.  The control baseline of each system will be dependent on system classification, information types and categorization level.  The baselines will be stored in {{ RMF_GOVERNANCE_SYSTEM }}.


## 9. Baseline Tailoring

{{ ORGANIZATION }} will conduct control tailoring during the control selection and implementation phases of the RMF process.  Tailored controls will be dependent on each system's information types, categorization levels, and classification.  Current control baselines for each system will be maintained within the system’s {{ RMF_GOVERNANCE_SYSTEM }} package.



## Appendix A – Detailed Compliance Matrix

The following table provides detailed traceability between the policy implementation statements in this document, the authoritative NIST SP 800-53 Rev. 5 control requirements, DoD CCIs, and the technical/governance enforcement mechanisms active across {{ SYSTEM_NAME }}.


| CTRL ID | CTRLTITLE | REQUIRED eMASS STANDARD | DOCREF | ENFORCEMENT MECHANISM |
| :--- | :--- | :--- | :--- | :--- |
| PL-01 | Policy and Procedures | Develops, documents, and disseminates PL policy/procedures to personnel with planning/security duties; designates PM/SO; reviews annually and upon significant changes or published guidance. (CCI-000563, CCI-000564, CCI-000566, CCI-000567, CCI-000568, CCI-001636, CCI-001637, CCI-001638, CCI-003047, CCI-003048, CCI-004273, CCI-004274, CCI-004275, CCI-004276, CCI-004277) | Section 2 | eMASS governance publication (System ID: {{ RMF_PACKAGE_ID }}); annual review cadence managed by {{ ORGANIZATION }} PM/SO, ISSM, and ISSO; trigger alignment with DoDI 8510.01 and NIST SP 800-137. |
| PL-02 | System Security and Privacy Plans | Develops, reviews, approves, distributes, and protects SSP/Privacy Plan defining boundary, mission context, roles, info types ({{ IMPACT_LEVEL }}), operational environment, baselines, and controls; reviews annually; coordinates with Privacy Officer/ISSM/ISSO. (CCI-000571, CCI-000572, CCI-000573, CCI-000574, CCI-003050, CCI-003051, CCI-003052, CCI-003053, CCI-003054, CCI-003055, CCI-003056, CCI-003057, CCI-003059, CCI-003060, CCI-003061, CCI-003062, CCI-003063, CCI-003064, CCI-004278, CCI-004279, CCI-004280, CCI-004281, CCI-004282, CCI-004283) | Section 3 | Formal AO approval workflow; eMASS System Security Plan repository; RBAC and {{ IDENTITY_PROVIDER }} with {{ MFA_MECHANISM }} access controls; Cloud KMS FIPS 140-3 CMEK plan encryption. |
| PL-04 | Rules of Behavior | Establishes rules of behavior for system/security/privacy usage; requires documented acknowledgment prior to access; reviews annually; requires annual user re-acknowledgment. (CCI-000592, CCI-000593, CCI-003068, CCI-003069, CCI-003070, CCI-004284, CCI-004285, CCI-004286, CCI-004287, CCI-004288, CCI-004289) | Section 4 | Automated onboarding/annual acknowledgment portal; {{ IDENTITY_PROVIDER }} conditional access policy requiring signed RoB compliance prior to {{ CSP_ABBR }} console session initiation. |
| PL-04(01) | Rules of Behavior: Social Media and External Networking Restrictions | Restricts social media and external application access; prohibits posting system info to public websites; prohibits using DoD identifiers/passwords on external sites. (CCI-000594, CCI-000595, CCI-004290) | Section 4 | Mandatory {{ RULES_OF_BEHAVIOR }}; VPC Service Controls blocking unapproved external web traffic; secure coding pipelines preventing public repository commits. |
| PL-07 | Concept of Operations | Develops, documents, and maintains security and privacy CONOPS; reviews and updates at least annually. (CCI-000577, CCI-000578, CCI-003071, CCI-004291) | Section 5 | Formal {{ ORGANIZATION }} {{ SYSTEM_NAME }} CONOPS document integrated with {{ ORGANIZATION }} NetOps / CSSP continuous monitoring workflows per DoDI 8530.01. |
| PL-08 | Security and Privacy Architectures | Develops, documents, and maintains system security/privacy architecture integrated into enterprise architecture; defines dependencies; reviews annually; reflects planned changes in SSP/CONOPS/acquisitions. (CCI-003073, CCI-003074, CCI-003075, CCI-003076, CCI-003077, CCI-003078, CCI-003080, CCI-004293, CCI-004294, CCI-004295, CCI-004296, CCI-004297, CCI-004298, CCI-004299, CCI-004300) | Section 6 | {{ SYSTEM_NAME }} Technical Design Document (TDD) architecture baselines; Terraform IaC infrastructure manifests; annual RMF review cycle integrated with enterprise landing zone standards. |
| PL-08(01) | Security and Privacy Architectures: Defense in Depth | Allocates coordinated, mutually reinforcing controls across all critical locations and architectural layers (physical, transit, compute platform, perimeter, IAM, encryption, telemetry). (CCI-003081, CCI-003082, CCI-003083, CCI-003084, CCI-003085, CCI-003086, CCI-003087, CCI-004301, CCI-004302, CCI-004303, CCI-004304, CCI-004305, CCI-004306, CCI-004307) | Section 6 | Layer 2/3 transport encryption, VPC-SC perimeters, MFA authentication, Cloud KMS HSM CMEK, isolated project enclaves, and automated CI/CD security gateways. |
| PL-08(02) | Security and Privacy Architectures: Supplier Diversity | Mandates that controls allocated to critical locations and architectural layers be obtained from different suppliers to mitigate supply chain risk. (CCI-003088, CCI-004308, CCI-004309) | Section 6 | Multi-supplier architecture across cloud networking, cloud transit, perimeter security, identity management, and diverse DevSecOps scanners (Semgrep, Checkov, tfsec, Gitleaks, Hadolint). |
| PL-09 | Central Management | Centrally manages flaw remediation, malicious code protection, and spam protection across the enterprise. (CCI-003117, CCI-003118) | Section 7 | Centrally managed via {{ ORGANIZATION }} DevSecOps CI/CD pipelines ({{ CICD_PLATFORM }}), {{ SIEM_TOOL }} ({{ CSSP_PROVIDER }}) integration via {{ TELEMETRY_PIPELINE }}, {{ VULNERABILITY_SCANNER }}, and {{ RMF_GOVERNANCE_SYSTEM }} POA&M tracking. |
| PL-10 | Baseline Selection | Selects and documents the security control baseline for the system. (CCI-004310) | Section 8 | Selection of NIST SP 800-53 Rev. 5 / DoD IL5 / FedRAMP High baseline, inherited from Google Services IL5 (eMASS ID: U:CLOUD:184). |
| PL-11 | Baseline Tailoring | Tailors the selected control baseline applying specified tailoring actions and compensating security controls. (CCI-004311) | Section 9 | Formal AO tailoring authorization; approved Exceptions-to-Policy (ETP-{{ SYSTEM_NAME }}-01 for VDSS inspection, ETP-{{ SYSTEM_NAME }}-02 for IPsec transit encapsulation). |
