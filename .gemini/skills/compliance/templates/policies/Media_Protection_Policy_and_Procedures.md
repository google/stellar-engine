# MP - Media Protection Policy and Procedures

## Document Governance & Approval Baseline

| Governance Metric | Policy Standard & Specification |
| :--- | :--- |
| **Document Title** | Media Protection Policy and Procedures |
| **NIST Control Family** | Media Protection (MP) |
| **Primary NIST Benchmark** | NIST SP 800-88 Rev. 1 (Guidelines for Media Sanitization), FIPS 140-3 |
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

The information security concerns regarding media protection reside not in the media itself, but in the recorded information. The issue of media protection is driven by the information placed intentionally or unintentionally on the media. Electronic media used on a system should be assumed to contain information commensurate with the security categorization of the system’s confidentiality. If not handled properly, release of these media could lead to an occurrence of unauthorized disclosure of information.

This plan does not claim to cover all possible media that {{ ORGANIZATION }} could use to store information, nor does it attempt to forecast the future media that may be developed during the effective life of this plan.

Users are expected to make protection decisions based on the security categorization of the information contained in the media and the overarching regulations that govern media disposal, sanitization and control.

This document complies with the following requirements from NIST Special Publication 800-53 Revision 5, "Security and Privacy Controls for Federal Information Systems and Organizations". A detailed compliance matrix can be found in Appendix A, “Detailed Compliance Matrix”.


## 2. Policy and Procedures

This policy defines how removable media will be properly handled for {{ ORGANIZATION }} {{ SYSTEM_NAME }}.  It establishes what is the minimum standard for media protection and usage for all {{ ORGANIZATION }} {{ SYSTEM_NAME }}. {{ ORGANIZATION }} {{ SYSTEM_NAME }} users are government employees, active-duty personnel, contractors, and/or vendors.  Compliance with this policy is mandatory for all {{ ORGANIZATION }}{{ ORGANIZATION }} {{ SYSTEM_NAME }} users, and components.  This policy is consistent with applicable laws, executive orders, directives, regulations, DOD policy, standards and guidelines.

This policy will be made available upon request to any {{ SYSTEM_NAME }} system or user and will be distributed initially through {{ RMF_GOVERNANCE_SYSTEM }} to all {{ ORGANIZATION }} {{ SYSTEM_NAME }} cybersecurity staff and system leadership.

> [!IMPORTANT]
> [WARNING: RMF TEAM ACTION REQUIRED: Verify and update operational contact/procedure details in this section.]
> The {{ ORGANIZATION }} {{ SYSTEM_NAME }} cybersecurity team is responsible for conducting annual reviews of this policy and making updates when applicable.  In the event updates are made to the policy or associated procedures, the documents will be distributed to each of the {{ ORGANIZATION }} {{ SYSTEM_NAME }} ISSMs for dissemination amongst their respective systems.  Additionally, the updated documents will be posted to {{ RMF_GOVERNANCE_SYSTEM }} where it can be retrieved by {{ ORGANIZATION }} {{ SYSTEM_NAME }} cybersecurity teams.



### 2.1 Google Cloud Platform (GCP) Inherited Controls & Shared Responsibility Boundary

- **Google Inherited Controls**: Google Cloud enforces automated, physical media sanitization (`MP-6`) and NIST SP 800-88 compliant degaussing/shredding of decommissioned storage drives (`MP-4`, `MP-6`).
- **Customer Implementation Responsibilities**: {{ ORGANIZATION }} is responsible for logical media protection, enforcing Cloud Storage bucket CMEK encryption (`MP-5`), and restricting export of digital media outside cloud perimeters (`MP-7`).

## 3. Media Access

Media access requirements are fully inherited from Google Cloud. The {{ ORGANIZATION }} {{ SYSTEM_NAME }} is fully hosted in Google Cloud.


## 4. Media Marking

Media marking requirements are fully inherited from Google Cloud. The {{ ORGANIZATION }} {{ SYSTEM_NAME }} is fully hosted in Google Cloud.


## 5. Media Storage

Media storage requirements are fully inherited from Google Cloud. The {{ SYSTEM_NAME }} is fully hosted in Google Cloud.


## 6. Media Transport

> [!IMPORTANT]
> [WARNING: RMF TEAM ACTION REQUIRED: Verify and update operational contact/procedure details in this section.]
> Media transport requirements are fully inherited from Google Cloud. The {{ ORGANIZATION }} {{ SYSTEM_NAME }} is fully hosted in Google Cloud.


## 7. Media Sanitization

Media sanitization requirements are fully inherited from Google Cloud. The {{ ORGANIZATION }} {{ SYSTEM_NAME }} is fully hosted in Google Cloud.


## 8. Media Use

Media use requirements are fully inherited from Google Cloud. The {{ ORGANIZATION }} {{ SYSTEM_NAME }} is fully hosted in Google Cloud.



## Appendix A – Detailed Compliance Matrix

The following table provides detailed traceability between the policy implementation statements in this document, the authoritative NIST SP 800-53 Rev. 5 control requirements, DoD CCIs, and the technical/governance enforcement mechanisms active across {{ SYSTEM_NAME }}.


| CTRL ID | CTRLTITLE | REQUIRED eMASS STANDARD | DOCREF | ENFORCEMENT MECHANISM |
| :--- | :--- | :--- | :--- | :--- |
| MP-01 | Policy and Procedures | Develops, documents, and disseminates MP policy/procedures to all personnel; designates ISSM/ISSO; reviews at least annually and upon significant change or security incidents. (CCI-000995, CCI-000996, CCI-000997, CCI-000998, CCI-000999, CCI-001000, CCI-001001, CCI-001002, CCI-002566, CCI-004201, CCI-004202, CCI-004203, CCI-004204, CCI-004205, CCI-004206, CCI-004207, CCI-004208, CCI-004209, CCI-004210) | Section 2 | Formal policy workflow published via eMASS (System ID: {{ RMF_PACKAGE_ID }}); annual governance cadence managed by {{ ORGANIZATION }} ISSM/ISSO; incident triggers aligned with CJCSM 6510.01B. |
| MP-02 | Media Access | Restricts access to digital/non-digital media containing sensitive info, {{ SENSITIVITY_CLASSIFICATION }}, and PII to authorized personnel with a valid need-to-know and clearance. (CCI-001003, CCI-001004, CCI-001005) | Section 3 | {{ IDENTITY_PROVIDER }} with {{ MFA_MECHANISM }}, SCIM synchronization to Cloud Identity, granular IAM conditions on Resource Manager tags, and VPC-SC perimeter controls. |
| MP-03 | Media Marking | Marks digital media indicating distribution limitations and caveats; exempts physical media inside certified controlled data centers. (CCI-001010, CCI-001011, CCI-001012, CCI-001013) | Section 4 | Automated Terraform IaC tagging and resource labeling (classification: {{ SENSITIVITY_CLASSIFICATION }}, system-id: {{ RMF_PACKAGE_ID }}); physical data center markings inherited from Google FedRAMP High boundary. |
| MP-04 | Media Storage | Physically controls and securely stores digital media containing {{ SENSITIVITY_CLASSIFICATION }}/PII within approved controlled areas until sanitized or destroyed. (CCI-001015, CCI-001016, CCI-004211, CCI-004212, CCI-004213, CCI-004214, CCI-004215) | Section 5 | Cloud KMS FIPS 140-3 HSM CMEK at-rest encryption (key-compute, key-storage), 90-day key rotation, isolated seed project remote state storage, and Google physical data center security. |
| MP-05 | Media Transport | Protects, controls, and maintains accountability for digital media during transport outside controlled areas using NSA/FIPS-validated encryption. (CCI-001021, CCI-001022, CCI-001023, CCI-001024, CCI-001025, CCI-004217, CCI-004218) | Section 6 | Hardware-enforced Layer 2 MACsec on {{ INTERCONNECT_TYPE }}, Layer 3 IPsec encapsulation, isolated management subnets, and Cloud Audit Logging to {{ ORGANIZATION }} NetOps/SOC. |
| MP-06 | Media Sanitization | Sanitizes all digital and physical media prior to disposal, release, or reuse IAW NIST SP 800-88 Rev. 1 using strength commensurate with classification. (CCI-001028, CCI-002578, CCI-002579, CCI-002580) | Section 7 | Cloud KMS cryptographic key revocation/destruction (crypto-shredding), automated zero-overwriting on persistent disk deletion, and inherited physical degaussing/shredding in Google data centers. |
| MP-07 | Media Use | Prohibits the use of all portable storage devices and unidentifiable removable media across all system components and networks. (CCI-002581, CCI-002582, CCI-002583, CCI-002584, CCI-002585) | Section 8 | Virtual instance USB controller removal, OS kernel-level usb-storage module blacklisting, DevSecOps CI/CD scanner enforcement (Hadolint, Checkov), and mandatory {{ RULES_OF_BEHAVIOR }}. |
