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
| **PREPARED BY:** | {{ PREPARED_BY }} | Signature: ______________________ Date: {{ DATE }} |
| **REVIEWED & RECOMMENDED BY:** | {{ ISSO_NAME }}<br>{{ ISSO_TITLE }}, {{ ORGANIZATION }} | Signature: ______________________ Date: {{ DATE }} |
| **REVIEWED & RECOMMENDED BY:** | {{ ISSM_NAME }}<br>{{ ISSM_TITLE }}, {{ ORGANIZATION }} | Signature: ______________________ Date: {{ DATE }} |
| **APPROVED BY:** | {{ SO_NAME }}<br>{{ SO_TITLE }}, {{ ORGANIZATION }} | Signature: ______________________ Date: {{ DATE }} |

### Document Change Record

| Date | Version | Author / Prepared By | Changes Made / Section(s) Description |
| :--- | :--- | :--- | :--- |
| {{ DATE }} | {{ VERSION }} | {{ PREPARED_BY }} | Initial formal baseline institutionalization under NIST SP 800-53 Rev. 5 / {{ COMPLIANCE_BASELINE }} governance. |

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

Federal agencies and organizations cannot protect the confidentiality, integrity, and availability of information in today's highly networked systems environment without ensuring that all people involved in using and managing IT:

1. Understand their roles and responsibilities related to the organizational mission;
2. Understand the organization's IT security policy, procedures, and practices; and
3. Have at least adequate knowledge of the various management, operational, and technical controls required and available to protect the IT resources for which they are responsible.

The purpose of this Planning Policy is to establish the requirements for developing and maintaining the system security and privacy plans, rules of behavior, and security and privacy architectures that govern {{ SYSTEM_NAME }}.

This policy addresses the Planning (PL) family requirements of NIST Special Publication 800-53 Revision 5, "Security and Privacy Controls for Information Systems and Organizations." A detailed compliance matrix is provided in Appendix A, "Detailed Compliance Matrix."

The Planning Policy encompasses all {{ ORGANIZATION }} users who have access to {{ SYSTEM_NAME }}. This policy outlines the framework for establishing, implementing, and maintaining security and privacy planning in alignment with applicable {{ GOVERNANCE_REGIME }} guidelines (NIST SP 800-53, FedRAMP, and applicable federal and state regulations), and is consistent with applicable laws, executive orders, directives, regulations, policies, standards, and guidelines. It applies to employees, contractors, and third-party users who handle sensitive information or operate within the {{ ORGANIZATION }} {{ SYSTEM_NAME }} information technology infrastructure.

{{ ORGANIZATION }} management is committed to the requirements of this policy and provides the resources needed to implement them. The ISSM ({{ ISSM_NAME }}) manages the development, documentation, and dissemination of this policy and its procedures, and coordinates their implementation with the Authorizing Official, System Owner, ISSO, and other organizational entities identified in the Program Roles & Responsibilities Matrix.

This policy and its procedures are reviewed and updated at least annually and following significant changes to {{ SYSTEM_NAME }} or its operating environment, security or privacy incidents, assessment or audit findings, or changes in applicable laws, executive orders, directives, regulations, policies, standards, or guidelines.

### 1.1 Background

The objective of security planning is to improve the protection of information system resources. The protection of a system must be documented in a system security plan. The System Security Plan for {{ SYSTEM_NAME }} is a separate document (see Section 3).

DoD and NIST standards are used to categorize all information and information systems collected or maintained by or on behalf of {{ ORGANIZATION }}, so that each system receives a level of information security that matches its risk. For {{ SYSTEM_NAME }}, the potential impact values assigned to the respective security objectives (FIPS PUB 199 / NIST SP 800-60) are:

- **Confidentiality Impact Level**: `{{ CONFIDENTIALITY_IMPACT }}`
- **Integrity Impact Level**: `{{ INTEGRITY_IMPACT }}`
- **Availability Impact Level**: `{{ AVAILABILITY_IMPACT }}`

Cybersecurity requirements for {{ SYSTEM_NAME }} are managed through the Risk Management Framework (RMF), consistent with the principles established in NIST SP 800-37 Rev. 2.


## 2. Policy and Procedures

The {{ ORGANIZATION }} Cybersecurity Team develops, documents, and reviews this system-level Planning Policy and Procedures under the direction of the ISSM, and disseminates them to {{ ORGANIZATION }} personnel with planning or information security responsibilities. Section 1 defines the review frequency and the events that trigger an update.

Each review considers changes in processes, requirements, and training, and changes to the enterprise architecture documentation; system security plan; privacy plan; records of system security and privacy plan reviews and updates; security and privacy architecture and design documentation; risk assessments and risk assessment results; control assessment documentation; and other relevant documents or records.

The RMF that governs {{ SYSTEM_NAME }} has the following characteristics:

- Promotes near real-time risk management and ongoing information system authorization through continuous monitoring processes;

- Encourages the use of automation to give senior leaders the information they need to make cost-effective, risk-based decisions about the organizational information systems that support their core missions and business functions;

- Integrates information security into the enterprise architecture and system development life cycle;

- Emphasizes the selection, implementation, assessment, and monitoring of security controls, and the authorization of information systems;

- Links risk management processes at the information system level to risk management processes at the organization level through a risk executive (function); and

- Establishes responsibility and accountability for security controls deployed within organizational information systems and inherited by those systems (i.e., common controls).


### 2.1 Google Cloud Inherited Controls & Shared Responsibility Boundary

- **Google Inherited Controls**: Google Cloud maintains CSP System Security Plans, architectural baselines (`PL-2`), and security planning across all Google Cloud regions.
- **Customer Implementation Responsibilities**: {{ ORGANIZATION }} is responsible for developing the system's System Security Plan (SSP) (`PL-2`), Rules of Behavior (RoB) (`PL-4`), and updating architecture planning documentation annually.

## 3. System Security and Privacy Plans

The purpose of the System Security Plan (SSP) is to provide an overview of the security requirements of {{ ORGANIZATION }} {{ SYSTEM_NAME }} and describe the controls in place or planned for meeting those requirements. The SSP also delineates the responsibilities and expected behavior of all individuals who access {{ ORGANIZATION }} systems.

The purpose of the Privacy Plan is to detail the privacy controls selected for an information system or environment of operation that are in place or planned for meeting applicable privacy requirements and managing privacy risks, including how the controls have been implemented, and to describe the methodologies and metrics that will be used to assess the controls.

All {{ ORGANIZATION }} systems will develop these plans consistent with the organization's enterprise architecture. The plans will:

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

Copies of these plans will reside within each system's {{ RMF_GOVERNANCE_SYSTEM }} package and will be provided to {{ ORGANIZATION }} PMO leadership upon request.


## 4. Rules of Behavior

Rules of behavior are a type of access agreement for organizational users. {{ ORGANIZATION }} uses a user access request form (`[WARNING: RMF TEAM ACTION REQUIRED: Rules of Behavior / Access Request Form]`) to request and grant access to {{ ORGANIZATION }} {{ SYSTEM_NAME }}. {{ ORGANIZATION }} also uses an Acceptable Use Policy (AUP) that all users, both general and privileged, must sign.

The AUP defines {{ ORGANIZATION }} user responsibilities and expected behavior for information and system usage, security, and privacy.

> [!IMPORTANT]
> [WARNING: RMF TEAM ACTION REQUIRED: Verify and update operational contact/procedure details in this section.]
> The user access request form (`[WARNING: RMF TEAM ACTION REQUIRED: Rules of Behavior / Access Request Form]`) and AUPs are stored with the ISSM/ISSO and are reviewed annually. The user access request form (`[WARNING: RMF TEAM ACTION REQUIRED: Rules of Behavior / Access Request Form]`) is shared with required parties via email. If the user access request form (`[WARNING: RMF TEAM ACTION REQUIRED: Rules of Behavior / Access Request Form]`) is revised or updated, or the type of access changes, the end user must read and re-sign the form.

All {{ ORGANIZATION }} systems will also require users with elevated or privileged access to sign the Privileged Access Agreement (PAA). The PAA defines the acceptable use and training requirements for maintaining privileged access.


### 4.1 Social Media and External Site/Application Usage Restrictions

The {{ ORGANIZATION }} AUP, which all users must sign, contains the following restrictions on social media, public websites, and external sites and applications:

- Explicit restrictions on the use of social media and networking sites IAW DoDI 8550.01

- Explicit restrictions on posting organizational information on public websites and applications IAW DoDI 8550.01

- Explicit restrictions on using organization-provided identifiers (e.g., email addresses) and authentication secrets (e.g., passwords) to create accounts on external sites and applications

Any sharing or posting of DoD data to social media or public websites will be subject to disciplinary action, including loss of clearance and termination.


## 5. Concept of Operations

{{ ORGANIZATION }} will maintain a Concept of Operations (CONOPS) for {{ SYSTEM_NAME }} that describes how {{ ORGANIZATION }} intends to operate the system from the perspective of information security and privacy.

The CONOPS can be a standalone document or be included in the security or privacy plans for {{ SYSTEM_NAME }}. It is a living document that is updated throughout the system development life cycle and at least annually.

The CONOPS should contain information on the system architecture and the operational procedures. Changes to the CONOPS should be reflected in security and privacy plans, architectures, and other related documentation.


## 6. Security and Privacy Architectures

{{ ORGANIZATION }} will develop and maintain security and privacy architectures for {{ SYSTEM_NAME }}. The architectures show how {{ ORGANIZATION }} protects the confidentiality, integrity, and availability of data within {{ SYSTEM_NAME }}, as well as any internal or external connections to supporting systems. {{ ORGANIZATION }} uses a defense-in-depth approach so that adversaries have to defeat multiple controls before achieving their objective. {{ ORGANIZATION }} also uses supplier diversity to offset the strengths and weaknesses of individual technologies.

The architectures are documented in the {{ SYSTEM_NAME }} System Security Plan and architecture specification.


## 7. Central Management

{{ ORGANIZATION }} will centrally manage the planning, implementing, assessing, authorizing, and monitoring processes. This keeps processes consistent across {{ ORGANIZATION }}, not only within {{ SYSTEM_NAME }}. Flaw remediation, malicious code protection, and spam protection are also managed centrally through the mechanisms listed for PL-09 in Appendix A.


## 8. Baseline Selection

{{ ORGANIZATION }} will select a control baseline for each system during the control selection step of the RMF process. The control baseline of each system depends on the system classification, information types, and categorization level. The baselines will be stored in {{ RMF_GOVERNANCE_SYSTEM }}.


## 9. Baseline Tailoring

{{ ORGANIZATION }} will tailor controls during the control selection and implementation steps of the RMF process. Tailored controls depend on each system's information types, categorization levels, and classification. Current control baselines for each system will be maintained within the system's {{ RMF_GOVERNANCE_SYSTEM }} package.



## Appendix A – Detailed Compliance Matrix

The following table provides detailed traceability between the policy implementation statements in this document, the authoritative NIST SP 800-53 Rev. 5 control requirements, DoD CCIs, and the technical/governance enforcement mechanisms active across {{ SYSTEM_NAME }}.


| CTRL ID | CTRLTITLE | REQUIRED {{ GRC_STANDARD_LABEL }} STANDARD | DOCREF | ENFORCEMENT MECHANISM |
| :--- | :--- | :--- | :--- | :--- |
| PL-01 | Policy and Procedures | Develops, documents, and disseminates PL policy and procedures to personnel with planning and security duties; designates the ISSM to manage them; reviews and updates them at least annually and following significant system changes, security or privacy incidents, assessment or audit findings, or changes in applicable laws, regulations, or guidance. (CCI-000563, CCI-000564, CCI-000566, CCI-000567, CCI-000568, CCI-001636, CCI-001637, CCI-001638, CCI-003047, CCI-003048, CCI-004273, CCI-004274, CCI-004275, CCI-004276, CCI-004277) | Section 1 & 2 | eMASS governance publication (System ID: {{ RMF_PACKAGE_ID }}); annual review cadence managed by the ISSM with the SO and ISSO; trigger alignment with DoDI 8510.01 and NIST SP 800-137. |
| PL-02 | System Security and Privacy Plans | Develops, reviews, approves, distributes, and protects SSP/Privacy Plan defining boundary, mission context, roles, info types ({{ IMPACT_LEVEL }}), operational environment, baselines, and controls; reviews annually; coordinates with Privacy Officer/ISSM/ISSO. (CCI-000571, CCI-000572, CCI-000573, CCI-000574, CCI-003049, CCI-003050, CCI-003051, CCI-003052, CCI-003053, CCI-003054, CCI-003055, CCI-003056, CCI-003057, CCI-003059, CCI-003060, CCI-003061, CCI-003062, CCI-003063, CCI-003064, CCI-004278, CCI-004279, CCI-004280, CCI-004281, CCI-004282, CCI-004283) | Section 3 | Formal AO approval workflow; eMASS System Security Plan repository; RBAC and {{ IDENTITY_PROVIDER }} with {{ MFA_MECHANISM }} access controls; Cloud KMS FIPS 140-3 CMEK plan encryption. |
| PL-04 | Rules of Behavior | Establishes rules of behavior for system/security/privacy usage; requires documented acknowledgment prior to access; reviews annually; requires users to re-acknowledge annually and when the rules are revised. (CCI-000592, CCI-000593, CCI-003068, CCI-003069, CCI-003070, CCI-004284, CCI-004285, CCI-004286, CCI-004287, CCI-004288, CCI-004289) | Section 4 | Automated onboarding/annual acknowledgment portal; {{ IDENTITY_PROVIDER }} conditional access policy requiring signed RoB compliance prior to {{ CSP_ABBR }} console session initiation. |
| PL-04(01) | Social Media and External Site/Application Usage Restrictions | Includes in the rules of behavior restrictions on the use of social media, social networking sites, and external sites/applications; on posting organizational information on public websites; and on using organization-provided identifiers (e.g., email addresses) and passwords to create accounts on external sites/applications. (CCI-000594, CCI-000595, CCI-004290) | Section 4.1 | Mandatory {{ RULES_OF_BEHAVIOR }} acknowledgment; VPC Service Controls perimeters blocking data movement from protected Google Cloud services to external destinations; secure coding pipelines preventing public repository commits. |
| PL-07 | Concept of Operations | Develops, documents, and maintains security and privacy CONOPS; reviews and updates at least annually. (CCI-000577, CCI-000578, CCI-003071, CCI-004291) | Section 5 | Formal {{ ORGANIZATION }} {{ SYSTEM_NAME }} CONOPS document integrated with {{ ORGANIZATION }} NetOps / CSSP continuous monitoring workflows per DoDI 8530.01. |
| PL-08 | Security and Privacy Architectures | Develops, documents, and maintains system security/privacy architecture integrated into enterprise architecture; defines dependencies; reviews annually; reflects planned changes in SSP/CONOPS/acquisitions. (CCI-003072, CCI-003073, CCI-003074, CCI-003075, CCI-003076, CCI-003077, CCI-003078, CCI-003079, CCI-003080, CCI-004292, CCI-004293, CCI-004294, CCI-004295, CCI-004296, CCI-004297, CCI-004298, CCI-004299, CCI-004300) | Section 6 | {{ SYSTEM_NAME }} Technical Design Document (TDD) architecture baselines; Terraform IaC infrastructure manifests; annual RMF review cycle integrated with enterprise landing zone standards. |
| PL-08(01) | Defense in Depth | Allocates coordinated, mutually reinforcing controls across all critical locations and architectural layers (physical, transit, compute platform, perimeter, IAM, encryption, telemetry). (CCI-003081, CCI-003082, CCI-003083, CCI-003084, CCI-003085, CCI-003086, CCI-003087, CCI-004301, CCI-004302, CCI-004303, CCI-004304, CCI-004305, CCI-004306, CCI-004307) | Section 6 | Layer 2/3 transport encryption, VPC-SC perimeters, MFA authentication, Cloud KMS HSM CMEK, isolated project enclaves, and automated CI/CD security gateways. |
| PL-08(02) | Supplier Diversity | Mandates that controls allocated to critical locations and architectural layers be obtained from different suppliers to mitigate supply chain risk. (CCI-003088, CCI-004308, CCI-004309) | Section 6 | Multi-supplier architecture across cloud networking, cloud transit, perimeter security, identity management, and diverse DevSecOps scanners (Semgrep, Checkov, tfsec, Gitleaks, Hadolint). |
| PL-09 | Central Management | Centrally manages flaw remediation, malicious code protection, and spam protection across the enterprise. (CCI-003117, CCI-003118) | Section 7 | Centrally managed via {{ ORGANIZATION }} DevSecOps CI/CD pipelines ({{ CICD_PLATFORM }}), {{ EXTERNAL_SIEM }} ({{ CSSP_PROVIDER }}) integration via {{ TELEMETRY_PIPELINE }}, {{ VULNERABILITY_SCANNER }}, and {{ RMF_GOVERNANCE_SYSTEM }} POA&M tracking. |
| PL-10 | Baseline Selection | Selects and documents the security control baseline for the system. (CCI-004310) | Section 8 | Selection of NIST SP 800-53 Rev. 5 / {{ REGIME_DISPLAY_NAME }} baseline<!-- IF DOD_IL6 --> ({{ CSP_INHERITANCE_HEADER }})<!-- ENDIF --><!-- IF NOT DOD_IL6 --><!-- IF DOD_ENCLAVE -->, inherited from Google Services {{ DOD_IMPACT_SHORT }} (eMASS ID: U:CLOUD:184)<!-- ENDIF --><!-- IF NOT DOD_ENCLAVE -->, leveraging the {{ CSP_INHERITANCE_AUTHORIZATION }}<!-- ENDIF --><!-- ENDIF -->. |
| PL-11 | Baseline Tailoring | Tailors the selected control baseline applying specified tailoring actions and compensating security controls. (CCI-004311) | Section 9 | Formal AO tailoring authorization; approved Exceptions-to-Policy (ETP-{{ SYSTEM_NAME }}-01 for VDSS inspection, ETP-{{ SYSTEM_NAME }}-02 for IPsec transit encapsulation). |
