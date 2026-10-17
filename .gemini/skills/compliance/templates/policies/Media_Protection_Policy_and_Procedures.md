# MP - Media Protection Policy and Procedures

## Document Governance & Approval Baseline

| Governance Metric | Policy Standard & Specification |
| :--- | :--- |
| **Document Title** | Media Protection Policy and Procedures |
| **NIST Control Family** | Media Protection (MP) |
| **Primary NIST Benchmark** | NIST SP 800-88 Rev. 2 (Guidelines for Media Sanitization), FIPS 140-3 |
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
> This document defines the enterprise security policy and implementation procedures for **Media Protection** under **NIST SP 800-53 Rev. 5 (MP)**.
> Technical infrastructure controls are automatically provisioned and enforced via **{{ SYSTEM_NAME }}** Terraform blueprints.
> Operational rules or contact details requiring manual confirmation are highlighted with RMF Team Callouts.


## 1. Overview

Federal agencies and organizations cannot protect the confidentiality, integrity, and availability of information in today's highly networked systems environment without ensuring that all people involved in using and managing IT:

1. Understand their roles and responsibilities related to the organizational mission;
2. Understand the organization's IT security policy, procedures, and practices; and
3. Have at least adequate knowledge of the various management, operational, and technical controls required and available to protect the IT resources for which they are responsible.

The purpose of this Media Protection Policy is to establish the requirements for protecting, marking, storing, transporting, sanitizing, and controlling the use of digital and non-digital media that contain {{ ORGANIZATION }} information.

This policy addresses the Media Protection (MP) family requirements of NIST Special Publication 800-53 Revision 5, "Security and Privacy Controls for Information Systems and Organizations." A detailed compliance matrix is provided in Appendix A, "Detailed Compliance Matrix."

The Media Protection Policy encompasses all {{ ORGANIZATION }} users who have access to {{ SYSTEM_NAME }}. This policy outlines the framework for establishing, implementing, and maintaining media protection in alignment with applicable {{ GOVERNANCE_REGIME }} guidelines (NIST SP 800-53, FedRAMP, and applicable federal and state regulations), and is consistent with applicable laws, executive orders, directives, regulations, policies, standards, and guidelines. It applies to employees, contractors, and third-party users who handle sensitive information or operate within the {{ ORGANIZATION }} {{ SYSTEM_NAME }} information technology infrastructure.

{{ ORGANIZATION }} management is committed to the requirements of this policy and provides the resources needed to implement them. The ISSM ({{ ISSM_NAME }}) manages the development, documentation, and dissemination of this policy and its procedures, and coordinates their implementation with the Authorizing Official, System Owner, ISSO, and other organizational entities identified in the Program Roles & Responsibilities Matrix.

This policy and its procedures are reviewed and updated at least annually and following significant changes to {{ SYSTEM_NAME }} or its operating environment, security or privacy incidents, assessment or audit findings, or changes in applicable laws, executive orders, directives, regulations, policies, standards, or guidelines.

### 1.1 Background

The security concern in media protection is the information recorded on the media, not the media itself. Information can be placed on media intentionally or unintentionally, so electronic media used on {{ SYSTEM_NAME }} are assumed to contain information at the confidentiality level of the system's security categorization. Improper handling or release of media can lead to unauthorized disclosure of that information.

This policy does not cover every type of media that {{ ORGANIZATION }} could use to store information, and it does not try to anticipate media types developed during the life of this policy. Users make protection decisions based on the security categorization of the information on the media and the regulations that govern media control, sanitization, and disposal.


## 2. Policy and Procedures

This policy sets the minimum standard for protecting and using media, including removable media, for {{ ORGANIZATION }} {{ SYSTEM_NAME }}. {{ ORGANIZATION }} {{ SYSTEM_NAME }} users are government employees, active-duty personnel, contractors, and vendors. Compliance with this policy is mandatory for all {{ ORGANIZATION }} {{ SYSTEM_NAME }} users and components.

This policy is available on request to any {{ SYSTEM_NAME }} user and is distributed initially through {{ RMF_GOVERNANCE_SYSTEM }} to all {{ ORGANIZATION }} {{ SYSTEM_NAME }} cybersecurity staff and system leadership.

> [!IMPORTANT]
> [WARNING: RMF TEAM ACTION REQUIRED: Verify and update operational contact/procedure details in this section.]
> The {{ ORGANIZATION }} {{ SYSTEM_NAME }} cybersecurity team supports the ISSM in the reviews described in Section 1. When this policy or its procedures are updated, the updated documents are distributed to each {{ ORGANIZATION }} {{ SYSTEM_NAME }} ISSM for dissemination to their systems and posted to {{ RMF_GOVERNANCE_SYSTEM }}, where {{ ORGANIZATION }} {{ SYSTEM_NAME }} cybersecurity teams can retrieve them.

### 2.1 Google Cloud Platform (GCP) Inherited Controls & Shared Responsibility Boundary

- **Google Inherited Controls**: Google Cloud enforces automated, physical media sanitization (`MP-6`) and NIST SP 800-88 compliant degaussing/shredding of decommissioned storage drives (`MP-4`, `MP-6`).
- **Customer Implementation Responsibilities**: {{ ORGANIZATION }} is responsible for logical media protection, enforcing Cloud Storage bucket CMEK encryption (`MP-5`), and restricting export of digital media outside cloud perimeters (`MP-7`).

## 3. Media Access

{{ ORGANIZATION }} {{ SYSTEM_NAME }} is hosted entirely in Google Cloud, and physical access to storage media in Google data centers is inherited from Google Cloud. {{ ORGANIZATION }} restricts access to digital media that contain {{ SENSITIVITY_CLASSIFICATION }} information or PII, such as Cloud Storage buckets and persistent disks, to authorized personnel with a need to know, using {{ IDENTITY_PROVIDER }} with {{ MFA_MECHANISM }}, IAM conditions, and VPC Service Controls perimeters.


## 4. Media Marking

Marking of physical media in Google data centers is inherited from Google Cloud. {{ ORGANIZATION }} marks digital resources with Terraform resource labels that record the data classification ({{ SENSITIVITY_CLASSIFICATION }}) and system identifier ({{ RMF_PACKAGE_ID }}).


## 5. Media Storage

Physical control and secure storage of media in Google data centers, until the media are sanitized or destroyed, is inherited from Google Cloud. {{ ORGANIZATION }} encrypts stored digital media with customer-managed encryption keys (CMEK) held in Cloud KMS hardware security modules and rotated every 90 days.


## 6. Media Transport

> [!IMPORTANT]
> [WARNING: RMF TEAM ACTION REQUIRED: Verify and update operational contact/procedure details in this section.]
> Transport of physical media is inherited from Google Cloud. {{ ORGANIZATION }} encrypts information that leaves controlled areas with FIPS-validated or NSA-approved cryptography (MACsec on {{ INTERCONNECT_TYPE }} and IPsec tunnels), and records these transfers in Cloud Audit Logs.


## 7. Media Sanitization

Sanitization and destruction of physical storage media in Google data centers, in accordance with NIST SP 800-88, is inherited from Google Cloud. {{ ORGANIZATION }} sanitizes digital media it controls by destroying the Cloud KMS keys that protect the data (cryptographic erase).


## 8. Media Use

Use of physical media in Google data centers is inherited from Google Cloud. {{ ORGANIZATION }} prohibits portable storage devices and removable media on {{ SYSTEM_NAME }} components. Enforcement includes removing USB controllers from virtual machine instances, blocking the usb-storage kernel module, and the {{ RULES_OF_BEHAVIOR }}.



## Appendix A – Detailed Compliance Matrix

The following table provides detailed traceability between the policy implementation statements in this document, the authoritative NIST SP 800-53 Rev. 5 control requirements, DoD CCIs, and the technical/governance enforcement mechanisms active across {{ SYSTEM_NAME }}.


| CTRL ID | CTRLTITLE | REQUIRED {{ GRC_STANDARD_LABEL }} STANDARD | DOCREF | ENFORCEMENT MECHANISM |
| :--- | :--- | :--- | :--- | :--- |
| MP-01 | Policy and Procedures | Develops, documents, and disseminates MP policy and procedures to cybersecurity staff and system leadership; designates the ISSM to manage them; reviews and updates them at least annually and following significant system changes, security or privacy incidents, assessment or audit findings, or changes in applicable laws, regulations, or guidance. (CCI-000995, CCI-000996, CCI-000997, CCI-000998, CCI-000999, CCI-001000, CCI-001001, CCI-001002, CCI-002566, CCI-004201, CCI-004202, CCI-004203, CCI-004204, CCI-004205, CCI-004206, CCI-004207, CCI-004208, CCI-004209, CCI-004210) | Section 1 & 2 | Formal policy workflow published via eMASS (System ID: {{ RMF_PACKAGE_ID }}); annual review cadence managed by the {{ ORGANIZATION }} ISSM with ISSO support; incident triggers aligned with<!-- IF DOD_ENCLAVE --> CJCSM 6510.01B<!-- ENDIF --><!-- IF NOT DOD_ENCLAVE --> NIST SP 800-61 Rev. 2<!-- ENDIF -->. |
| MP-02 | Media Access | Restricts access to digital/non-digital media containing sensitive information, {{ SENSITIVITY_CLASSIFICATION }}, and PII to authorized personnel with a valid need-to-know and clearance. (CCI-001003, CCI-001004, CCI-001005) | Section 3 | {{ IDENTITY_PROVIDER }} with {{ MFA_MECHANISM }}, SCIM synchronization to Cloud Identity, granular IAM conditions on Resource Manager tags, and VPC-SC perimeter controls. |
| MP-03 | Media Marking | Marks digital media indicating distribution limitations and caveats; exempts physical media inside certified controlled data centers. (CCI-001010, CCI-001011, CCI-001012, CCI-001013) | Section 4 | Automated Terraform IaC tagging and resource labeling (classification: {{ SENSITIVITY_CLASSIFICATION }}, system-id: {{ RMF_PACKAGE_ID }}); physical data center markings inherited from Google FedRAMP High boundary. |
| MP-04 | Media Storage | Physically controls and securely stores digital media containing {{ SENSITIVITY_CLASSIFICATION }}/PII within approved controlled areas until sanitized or destroyed. (CCI-001015, CCI-001016, CCI-004211, CCI-004212, CCI-004213, CCI-004214, CCI-004215) | Section 5 | Cloud KMS FIPS 140-2 Level 3 Cloud HSM CMEK at-rest encryption (key-compute, key-storage), organization-defined key rotation, isolated seed project remote state storage, and Google physical data center security. |
| MP-05 | Media Transport | Protects, controls, and maintains accountability for digital media during transport outside controlled areas using NSA/FIPS-validated encryption. (CCI-001021, CCI-001022, CCI-001023, CCI-001024, CCI-001025, CCI-004217, CCI-004218) | Section 6 | Hardware-enforced Layer 2 MACsec on {{ INTERCONNECT_TYPE }}, Layer 3 IPsec encapsulation, isolated management subnets, and Cloud Audit Logging to {{ ORGANIZATION }} NetOps/SOC. |
| MP-06 | Media Sanitization | Sanitizes all digital and physical media prior to disposal, release, or reuse IAW NIST SP 800-88 using strength commensurate with classification. (CCI-001028, CCI-002578, CCI-002579, CCI-002580) | Section 7 | Cloud KMS cryptographic key revocation/destruction (crypto-shredding), automated zero-overwriting on persistent disk deletion, and inherited physical degaussing/shredding in Google data centers. |
| MP-06(01) | Review, Approve, Track, Document, and Verify | Review, approve, track, document, and verify media sanitization and disposal actions across the system lifecycle. (CCI-002567, CCI-002568, CCI-002569, CCI-002570, CCI-002571, CCI-002572) | Section 7 | Inherited Google Cloud NIST SP 800-88 physical media destruction tracking and customer Cloud Audit Logs verifying KMS key destruction (crypto-erase) events. |
| MP-06(02) | Equipment Testing | Test sanitization equipment and procedures at least annually to verify that the intended sanitization is being achieved. (CCI-001031, CCI-004219, CCI-004220) | Section 7 | Inherited Google Cloud data center sanitization equipment validation (3PAO audited) and annual customer verification of cryptographic erasure workflows. |
| MP-06(03) | Nondestructive Techniques | Apply nondestructive sanitization (cryptographic erase and logical zeroization) to portable storage devices before connecting such devices to {{ SYSTEM_NAME }}. (CCI-001032, CCI-001033) | Section 7 | Strict prohibition of removable media (`MP-7`) combined with mandatory NIST SP 800-88 Purge/Clear and malware scanning prior to any authorized media use. |
| MP-07 | Media Use | Prohibits the use of all portable storage devices and unidentifiable removable media across all system components and networks. (CCI-002581, CCI-002582, CCI-002583, CCI-002584, CCI-002585) | Section 8 | Virtual instance USB controller removal, OS kernel-level usb-storage module blocking, DevSecOps CI/CD scanner enforcement (Hadolint, Checkov), and mandatory {{ RULES_OF_BEHAVIOR }}. |
