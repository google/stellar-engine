# PT - PII Processing and Transparency Policy and Procedures

## Document Governance & Approval Baseline

| Governance Metric | Policy Standard & Specification |
| :--- | :--- |
| **Document Title** | PII Processing and Transparency Policy and Procedures |
| **NIST Control Family** | PII Processing and Transparency (PT) |
| **Primary NIST Benchmark** | NIST Privacy Framework 1.0, OMB Circular A-130, NIST SP 800-53 Rev. 5 (PT) |
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
> This document defines the enterprise security policy and implementation procedures for **PII Processing and Transparency** under **NIST SP 800-53 Rev. 5 (PT)**.
> Technical infrastructure controls are automatically provisioned and enforced via **{{ SYSTEM_NAME }}** Terraform blueprints.
> Operational rules or contact details requiring manual confirmation are highlighted with RMF Team Callouts.


## 1. Overview

The objective of personally identifiable information (PII) processing and transparency is to ensure that privacy considerations are planned early and handled consistently in the project lifecycle.

{{ GOVERNANCE_REGIME }} organizations establish an integrated enterprise-wide decision structure for cybersecurity risk management, the Risk Management Framework (RMF). This structure identifies cybersecurity requirements for DoD information technologies to be managed through RMF, consistent with the principles established in National Institute of Standards and Technology (NIST) Special Publication (SP) 800-37.

This plan ensures that {{ ORGANIZATION }} {{ SYSTEM_NAME }} follows the established guidelines and requirements for PII processing and transparency.

This document complies with the following requirements from NIST Special Publication 800-53 Revision 5, "Security and Privacy Controls for Federal Information Systems and Organizations", and is consistent with applicable federal laws, Executive Orders, directives, policies, regulations, standards and guidance.

A detailed compliance matrix can be found in Appendix A, “Detailed Compliance Matrix”.


## 2. Policy and Procedures

PII processing, transparency policy, and procedures address the controls in the PII Processing and Transparency (PT) family that are implemented within {{ ORGANIZATION }} {{ SYSTEM_NAME }}.

> [!IMPORTANT]
> <mark style="background-color: #fff9c4; color: #b71c1c; font-weight: bold; padding: 2px 6px; border-radius: 4px;">⚠️ RMF TEAM ACTION REQUIRED: Verify and update operational contact/procedure details in this section.</mark>
> {{ ORGANIZATION }} is responsible for the development of, updates, annual reviews and dissemination of this PT Policy.  Dissemination of this policy and any associated procedures shall occur initially, and upon update(s), to all {{ ORGANIZATION }} {{ SYSTEM_NAME }} Information System Security Managers (ISSM) and Information System Security Officers (ISSO). All reviews and updates to this policy shall be tracked via the Review and Change Records at the beginning of this document.

This document shall be reviewed and updated no less than annually by {{ ORGANIZATION }}, with updates completed as necessary to account for changes in processes, requirements, and applicable training. Updates shall consider changes required due to modifications to the enterprise architecture documentation; system security plan; privacy plan; records of system security and privacy plan reviews and updates; security and privacy architecture and design documentation; risk assessments; risk assessment results; control assessment documentation; and other relevant documents or records. This policy is also subject to change in response to any event, After Action Report (AAR), to incorporate lessons learned, or as directed by higher commands and in accordance with any changes in applicable laws or directives.

{{ ORGANIZATION }} {{ SYSTEM_NAME }} users are directed to comply with the following tasks and requirements:

- All {{ ORGANIZATION }} systems must conduct a Privacy Impact Assessment (PIA) using DD Form 2930.

- {{ ORGANIZATION }} must complete a new Privacy Impact Assessment at that time to determine if there is a change to privacy information collected, stored or traversing their networks.

- Upon implementation of the {{ ORGANIZATION }} Identity, Credential, and Access Management (ICAM) solution, {{ ORGANIZATION }} shall conduct a new PIA to determine impact to privacy.

- As {{ ORGANIZATION }} Zero Trust Architecture (ZTA) solutions are implemented, {{ ORGANIZATION }} shall conduct a new PIA to determine impact to privacy.

- All {{ ORGANIZATION }} systems shall implement STIGs, or vendor best practice guides, to ensure all technology is hardened and lower the risk of both external and internal actions that could lead to a PII breach.

- All PII must be protected and marked appropriately. This includes using proper encryption for data at rest, and properly marking documents and data.



### 2.1 Google Cloud Platform (GCP) Inherited Controls & Shared Responsibility Boundary

- **Google Inherited Controls**: Google Cloud provides platform-level privacy controls (`PT-1`, `PT-3`) and data processing agreements ensuring customer data is never used for advertising or unauthorized processing.
- **Customer Implementation Responsibilities**: {{ ORGANIZATION }} is responsible for publishing Privacy Impact Assessments (PIA) (`PT-2`), managing PII inventory, and enforcing Data Loss Prevention (DLP) inspection policies (`PT-4`, `PT-7`).

## 3. Critical Definitions


#### 3.1.1 U.S. Department of Defense Privacy Principles


1. The privacy of an individual is directly affected by the collection, maintenance, use, and dissemination of personal information by Federal agencies;
2. The increasing use of computers and sophisticated information technology, while essential to the efficient operations of the Government, has greatly magnified the harm to individual privacy that can occur from any collection, maintenance, use, or dissemination of personal information.
3. The opportunities for an individual to secure employment, insurance, and credit, and his or her right to due process, and other legal protections are endangered by the misuse of certain information systems;
4. The right to privacy is a personal and fundamental right protected by the Constitution of the United States; and
5. In order to protect the privacy of individuals identified in information systems maintained by Federal agencies, it is necessary and proper for the Congress to regulate the collection, maintenance, use, and dissemination of information by such agencies.


#### 3.1.2 Personally Identifiable Information

1. “The term PII refers to information that can be used to distinguish or trace an individual’s identity, either alone or when combined with other information that is linked or linkable to a specific individual. PII may range from common data elements such as names, addresses, dates of birth, and places of employment, identity documents, Social Security numbers (SSN), other government-issued identity, precise location information, medical history, and biometrics. There are many different types of information that can be used to distinguish or trace an individual’s identity the term PII is necessarily broad…”

2. “The definition of PII is not anchored to any single category of information or technology. Rather, it demands a case-by-case assessment of the specific risk that an individual can be identified. In performing this assessment, it is important for an agency to recognize that non-PII can become PII whenever additional information is made publicly available – in any medium and from any source – that, when combined with other available information, could be used to identify an individual.”


## 4. Roles and Responsibilities

- Implement privacy safeguards, which includes completing PIAs and System of Record Notices (SORNs), if applicable;

- Determine early in the design phase of IT systems what type of PII shall be collected, used, processed, stored or disseminated;

- Formulate Privacy Act requirements in early stages of IT systems design, development, and data management to plan for and implement Information Assurance (IA) controls to safeguard PII.;

- Ensure records containing PII are safeguarded or removed as required from all IT systems prior to disposal, replacement, or reuse of IT hardware storage components (hard drives) in accordance with IA directives;

- Review applicable SORN(s) for information systems concurrently with the Federal Information Security Management Act (FISMA) annual review to validate whether changes to an existing SORN is required; and

- Review IT systems registered in the Information Technology Investment Portfolio Suite (ITIPS), addresses and updates responses to privacy questions.

- In the case of a PII breach, the ISSM shall follow the reporting procedures outlined in the {{ ORGANIZATION }} {{ SYSTEM_NAME }} Incident Response plan.

- The ISSM is designated as the individual responsible for ensuring this policy is updated, reviewed and disseminated on an annual basis.


#### 4.1.1 System Developers/Designers/Engineers

- Responsible for ensuring that the system design and specifications conform to privacy standards and requirements and that technical controls are in place for safeguarding personal information from unauthorized access.


#### 4.1.2 All Additional Personnel

- All users of {{ ORGANIZATION }} {{ SYSTEM_NAME }} are responsible for ensuring they protect the data they use within the system.

- All users should properly mark, encrypt, and store data per {{ ORGANIZATION }} requirements.  Any breach or incident involving PII should be immediately reported to the {{ SYSTEM_NAME }} ISSM/ISSO.


## 5. Authority to Process PII and Consent

> [!IMPORTANT]
> <mark style="background-color: #fff9c4; color: #b71c1c; font-weight: bold; padding: 2px 6px; border-radius: 4px;">⚠️ RMF TEAM ACTION REQUIRED: Verify and update operational contact/procedure details in this section.</mark>
> The {{ ORGANIZATION }} has implemented rigorous standards to protect data-at-rest and data-in-transit utilizing established public key infrastructure ({{ PKI_TRUST_TYPE }}) leveraging certificates stored on hardware tokens ({{ MFA_MECHANISM }}). Personnel and contractors assigned to support {{ ORGANIZATION }} {{ SYSTEM_NAME }} provide explicit consent through the user access agreement form ({{ ACCESS_AGREEMENT_TYPE }}) maintained with the ISSO/ISSM granting authorized access. {{ ORGANIZATION }} reserves the authority to associate unique enterprise identifiers ({{ USER_IDENTIFIER_TYPE }}) with username, first, and last name in support of hardware token-based authentication.

> [!IMPORTANT]
> <mark style="background-color: #fff9c4; color: #b71c1c; font-weight: bold; padding: 2px 6px; border-radius: 4px;">⚠️ RMF TEAM ACTION REQUIRED: Verify and update operational contact/procedure details in this section.</mark>
> At the conclusion of the RMF process, the {{ ORGANIZATION }} Authorizing Official (AO) shall determine whether the overall risk posture of the system is acceptable to issue an “Authorization-to-Operate” (ATO). This provides the system with the ability to process information, to include PII.



## Appendix A – Detailed Compliance Matrix

The following table provides detailed traceability between the policy implementation statements in this document, the authoritative NIST SP 800-53 Rev. 5 control requirements, DoD CCIs, and the technical/governance enforcement mechanisms active across {{ SYSTEM_NAME }}.


| CTRL ID | CTRLTITLE | REQUIRED eMASS STANDARD | DOCREF | ENFORCEMENT MECHANISM |
| :--- | :--- | :--- | :--- | :--- |
| PT-01 | Policy and Procedures | Develops, documents, and disseminates PT policy/procedures to stakeholders (privacy/security officials, SO, PM); designates ISSO/ISSM; reviews annually and upon findings/breaches. (CCI-004525, CCI-004526, CCI-004527, CCI-004528, CCI-004529, CCI-004530, CCI-004531, CCI-004532, CCI-004533, CCI-004534, CCI-004535, CCI-004536, CCI-004537, CCI-004538) | Section 2.1 | Formal eMASS governance publication (System ID: {{ RMF_PACKAGE_ID }}); annual review cadence managed by ISSM/ISSO in coordination with {{ ORGANIZATION }} SAOP; trigger alignment with DoDI 5400.16. |
| PT-02 | Authority to Process Personally Identifiable Information | Determines and documents legal authority (statute/E.O./SORN) permitting PII processing; restricts processing to authorized administrative functions. (CCI-004539, CCI-004540, CCI-004541, CCI-004542, CCI-004543) | Section 2.2 | Documented legal authority under federal statute and published agency SORN; technical restriction to administrative authentication via {{ IDENTITY_PROVIDER }}. |
| PT-03 | Personally Identifiable Information Processing Purposes | Documents authorized purposes for PII processing; describes in notices; restricts processing to compatible use/disclosure; monitors changes via CCB and PIA updates. (CCI-004549, CCI-004550, CCI-004551, CCI-004552, CCI-004553, CCI-004554, CCI-004555, CCI-004556, CCI-004557) | Section 2.2 | Formal Privacy Impact Assessment (PIA); {{ ORGANIZATION }} CCB approval workflows for system baseline changes; IAM role condition enforcement on administrative data. |
| PT-04 | Consent | Implements electronic/paper mechanisms for individuals to provide informed consent prior to PII collection. (CCI-004561, CCI-004562) | Section 2.3 | Digitally signed {{ ACCESS_AGREEMENT_TYPE }} onboarding workflow and mandatory interactive {{ WARNING_BANNER_TYPE }} acknowledgment. |
| PT-05 | Privacy Notice | Provides clear, plain-language privacy notice upon initial interaction and upon changes in collection/use; identifies authority, purpose, SORN link, and routine uses. (CCI-004571, CCI-004572, CCI-004573, CCI-004574, CCI-004575, CCI-004576, CCI-004577) | Section 2.3 | Standardized Privacy Act notices integrated into the user registration portal and electronic system login splash pages. |
| PT-05(01) | Privacy Notice: Just-in-Time Notice | Presents just-in-time notice of PII processing at the point of collection. (CCI-004578, CCI-004579) | Section 2.3 | Dynamic point-of-collection privacy banners rendered on administrative credential input and {{ ACCESS_AGREEMENT_TYPE }} onboarding web forms. |
| PT-05(02) | Privacy Notice: Privacy Act Statements | Includes formal Privacy Act statements on forms collecting information maintained in a system of records. (CCI-004580) | Section 2.3 | Mandatory Privacy Act Statement (5 U.S.C. § 552a(e)(3)) embedded directly on {{ ACCESS_AGREEMENT_TYPE }} and user account request portals. |
| PT-06 | System of Records Notice | Drafts SORNs per OMB guidance; submits for advance review; publishes in Federal Register; keeps SORNs accurate and updated. (CCI-004581, CCI-004582, CCI-004583, CCI-004584) | Section 2.4 | Enterprise SORN publication workflows managed by the {{ ORGANIZATION }} Privacy Office under OMB Circular A-108 governance. |
| PT-06(01) | System of Records Notice: Routine Uses | Reviews all routine uses upon system changes requiring PIA update, significant SORN modification under OMB A-108, or as directed by Privacy Officer. (CCI-004585, CCI-004586, CCI-004587) | Section 2.4 | Synchronized SORN routine-use review triggers integrated into the annual FISMA and PIA review cycle. |
| PT-06(02) | System of Records Notice: Exemption Rules | Reviews all Privacy Act exemptions claimed upon system changes requiring PIA update or SORN modification under OMB A-108. (CCI-004588, CCI-004589, CCI-004590, CCI-004591) | Section 2.4 | Formal legal and privacy review of claimed Privacy Act exemptions conducted concurrently with RMF continuous monitoring updates. |
| PT-07 | Specific Categories of Personally Identifiable Information | Applies processing conditions for specific PII categories IAW DoD regulations, statutory Privacy Act requirements, and federal laws across information lifecycle. (CCI-004592, CCI-004593) | Section 2.5 | Cryptographic enforcement (FIPS 140-3 Cloud KMS CMEK) and strict prohibition of PHI/biometric data in {{ SYSTEM_NAME }} transport/telemetry pipelines. |
| PT-07(01) | Specific Categories of PII: Social Security Numbers | Eliminates unnecessary collection of SSNs; explores alternatives; uses DoD EDIPI / enterprise identifiers; prohibits denying rights for refusal to disclose SSN. (CCI-004594, CCI-004595, CCI-004596) | Section 2.5 | Mandatory replacement of SSN with {{ USER_IDENTIFIER_TYPE }} across {{ IDENTITY_PROVIDER }}, SCIM sync, and IAM bindings. |
| PT-07(02) | Specific Categories of PII: First Amendment Information | Prohibits processing information describing how individuals exercise First Amendment rights unless expressly authorized by statute. (CCI-004597) | Section 2.5 | Scope restriction to network routing headers and telemetry MIBs; absolute prohibition on payload inspection or storage of First Amendment data. |
| PT-08 | Computer Matching Agreements | Obtains Data Integrity Board approval, executes CMA, publishes Federal Register notice, verifies data, and provides notice before adverse action. (CCI-004598, CCI-004599, CCI-004600, CCI-004601, CCI-004602) | Section 2.6 | Formal DoD Data Integrity Board review and Computer Matching Agreement procedures per 5 U.S.C. § 552a(o). |
