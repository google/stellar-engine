# PS - Personnel Security Policy and Procedures

## Document Governance & Approval Baseline

| Governance Metric | Policy Standard & Specification |
| :--- | :--- |
| **Document Title** | Personnel Security Policy and Procedures |
| **NIST Control Family** | Personnel Security (PS) |
| **Primary NIST Benchmark** | NIST SP 800-53 Rev. 5 (PS Family), OPM Federal Suitability Standards |
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
> This document defines the enterprise security policy and implementation procedures for **Personnel Security** under **NIST SP 800-53 Rev. 5 (PS)**.
> Technical infrastructure controls are automatically provisioned and enforced via **{{ SYSTEM_NAME }}** Terraform blueprints.
> Operational rules or contact details requiring manual confirmation are highlighted with RMF Team Callouts.


## 1. Overview

The {{ ORGANIZATION }} Personnel Security Program is to establish policies and procedures to ensure acceptance and retention of personnel. The acceptance and retention of members of {{ ORGANIZATION }}, DoD civilian employees, DoD contractors, and other affiliated persons' access to information are clearly consistent with the interests of national security.

This Personnel Security Plan ensures that {{ ORGANIZATION }} follows and implements the DoD Personnel Security Program.

The Personnel Security Policy objective is to authorize, initial and continued access to sensitive information and/or initial and continued assignment to sensitive duties to those persons whose loyalty, reliability, and trustworthiness are such that entrusting them with sensitive information or assigning them to sensitive duties is clearly consistent with the interest of national security.

Personnel Security Investigations is one of the tools used to gather information about a person.  It is used to evaluate access to sensitive information, assignment to sensitive duties, and suitability for civilian employment or military service.

Types of Personnel National Security Investigations

- Tier 1 – Governed by Executive Order 10450

- Tier 3 – Governed by Executive Order 10450 and Executive Order 12968

- Tier 5 – Governed by Executive 12968

This document complies with the following requirements from NIST Special Publication 800-53 Revision 5, "Security and Privacy Controls for Federal Information Systems and Organizations". A detailed compliance matrix can be found in Appendix A, “Detailed Compliance Matrix”.


## 2. Policies and Procedures

Policies and procedures contribute to security and privacy assurance, therefore, it is important that security and privacy programs collaborate on their development. Procedures can be established for security and privacy programs, for mission/business processes, and for systems, if needed. Procedures describe how the policies or controls are implemented and can be directed at the individual or role that is the object of the procedure. Procedures can be documented in system security and privacy plans or in one or more separate documents. Events that may precipitate an update to personnel security policy and procedures include, but are not limited to, assessment or audit findings, security incidents or breaches, or changes in applicable laws, executive orders, directives, regulations, policies, standards, and guidelines.

This document consists of the policy guidance that represents how personnel security will be implemented for {{ ORGANIZATION }} {{ SYSTEM_NAME }}.  All {{ ORGANIZATION }}  {{ SYSTEM_NAME }} users are required to comply with, at minimum, the statements of this policy.

This document will be reviewed, at minimum, on an annual basis by the {{ ORGANIZATION }} for any necessary updates.  This policy and any procedures derived from it will be aligned with overarching guidance related to existing DoD policy such as DoD 5200-R and DoDI 5200.02 in addition to any other laws, regulations, and/or executive orders.



### 2.1 Google Cloud Platform (GCP) Inherited Controls & Shared Responsibility Boundary

- **Google Inherited Controls**: Google Cloud performs background checks (`PS-3`), personnel screening (`PS-2`), and termination access revocation (`PS-4`, `PS-5`) for all Google employees and datacenter staff.
- **Customer Implementation Responsibilities**: {{ ORGANIZATION }} is responsible for background investigations (`PS-3`), security clearance verification, immediate IAM account revocation upon employee termination (`PS-4`), and executing non-disclosure agreements (`PS-6`).

## 3. Position Risk Designation

Position risk designations reflect Office of Personnel Management (OPM) policy and guidance. Proper position designation is the foundation of an effective and consistent suitability and personnel security program. The Position Designation System (PDS) assesses the duties and responsibilities of a position to determine the degree of potential damage to the efficiency or integrity of the service due to misconduct of an incumbent of a position and establishes the risk level of that position. The PDS assessment also determines if the duties and responsibilities of the position present the potential for position incumbents to bring about a material adverse effect on national security and the degree of that potential effect, which establishes the sensitivity level of a position. The results of the assessment determine what level of investigation is conducted for a position. Risk designations can guide and inform the types of authorizations that individuals receive when accessing organizational information and information systems. Position screening criteria include explicit information security role appointment requirements. Parts 1400 and 731 of Title 5, Code of Federal Regulations, establish the applicability and suitability requirements for organizations to evaluate relevant covered positions for a position sensitivity and position risk designation commensurate with the duties and responsibilities of those positions.

{{ ORGANIZATION }} is required to assign risk designations to all positions supporting their respective system.  Additionally, {{ ORGANIZATION }} must establish the criteria for screening personnel who would fill the positions that they identify in support of their systems. The risk designations and screening criteria shall be included on the position descriptions of each system position designation.  These positions will be reviewed based on the organizational defined requirement for accuracy and updated as required to reflect the positions to be filled on the system.

Enclosure 1 lists the Position Designations and Record of Review, which must be performed annually.


## 4. Personnel Screening

> [!IMPORTANT]
> [WARNING: RMF TEAM ACTION REQUIRED: Verify and update operational contact/procedure details in this section.]
> Personnel screening and rescreening activities reflect applicable laws, executive orders, directives, regulations, policies, standards, guidelines, and specific criteria established for the risk designations of assigned positions. Examples of personnel screening include background investigations and agency checks. Organizations may define different rescreening conditions and frequencies for personnel accessing systems based on types of information processed, stored, or transmitted by the systems.

Personnel screening ensures all government and contract personnel meet the appropriate Automated Data Processing/Information Technology (ADP/IT) level designation requirements IAW DoD 5200.2-R in addition to DoDI 5200.02 guidance prior to authorizing access to the {{ ORGANIZATION }} {{ SYSTEM_NAME }}.

{{ ORGANIZATION }} {{ SYSTEM_NAME }} is an UNCLASSIFIED IL5 Environment that does not have individuals that require special access protections.

{{ ORGANIZATION }} must adhere to the following requirements in regard to Personnel Screening:

- All personnel must be screened prior to being approved for access to the system. Work with system ISSO’s and security staff to verify candidates hold a valid security clearance appropriate to the position that they will hold.

- Rescreen personnel based on the organizational defined requirements to ensure that staff maintain the appropriate clearance level to meet Position Designation requirements.  This includes working with any base or Program Security Office (PSO) to ensure that all requirements are met and in accordance with Defense Security Service (DSS) processes.

  - Rescreening actions are maintained as an audit trail

- Information System Owners (ISO) develop and document conditions requiring individuals who need to be rescreened to access {{ SYSTEM_NAME }}

- ISO define and document the required frequency of rescreening to maintain access to {{ SYSTEM_NAME }}

{{ ORGANIZATION }} requires users accessing {{ SYSTEM_NAME }} maintain U.S. Citizenship or verified background clearance (`[WARNING: RMF TEAM ACTION REQUIRED: Agency Citizenship / Clearance Rule]`).


## 5. Personnel Termination

When personnel separate from {{ ORGANIZATION }} and employment is terminated, immediate actions should be taken to protect {{ SYSTEM_NAME }}, its mission, data, and the individual who is leaving.  Reasons for termination vary and are facilitated through the Human Resources and Legal Departments.

It is the responsibility of the {{ ORGANIZATION }} {{ SYSTEM_NAME }} owner to ensure that the following tasks are completed:

- User access accounts have been disabled within 24 hours;

- Terminate/Revoke access to any authenticators/credentials associated with user;

- Conduct exit interviews that include the discussion of any non-disclosure agreements and requirements, and any additional legally-binding post-employment requirements;

  - Terminated individuals must sign an acknowledgement of post-employment requirements.

- Upon departure, ensure {{ ORGANIZATION }} retains access to the information and systems formerly controlled by the user.

- Inform appropriate stakeholders of individual termination; {{ ORGANIZATION }} shall use automated mechanisms to ensure such notification occurs within a timely manner.

Documentation of the system access termination should be retained to provide upon request by system leadership, auditors, and/or investigators.


## 6. Personnel Transfer

> [!IMPORTANT]
> [WARNING: RMF TEAM ACTION REQUIRED: Verify and update operational contact/procedure details in this section.]
> Personnel transfer applies when reassignments or transfers of individuals are permanent or of such extended duration as to make the actions warranted. {{ ORGANIZATION }} define actions appropriate for the types of reassignments or transfers, whether permanent or extended. Actions that may be required for personnel transfers or reassignments to other positions within organizations include returning old and issuing new keys, identification cards, and building passes; closing system accounts and establishing new accounts; changing system access authorizations (i.e., privileges); and providing for access to official records to which individuals had access at previous work locations and in previous system accounts.

A permanent transfer from one {{ ORGANIZATION }} system to another rarely will require a person to retain their level of access prior to the transfer. Any individual filling a position on an {{ ORGANIZATION }} system must have documentation that requests and authorizes the level of access they will need. Transfers or reassignment of personnel on {{ ORGANIZATION }} systems will be:

- Treated as a new user to be screened and onboarded on the destination system that the transferee is moving to support; and

- Treated as a departing employee and followed Personnel Termination from the viewpoint of the source system.

The only exception to this process will be that the transferring employee will retain their authenticator token ({{ MFA_MECHANISM }}) as the sponsorship will remain to be held by {{ ORGANIZATION }}.

Access and authorizations for newly assigned systems will follow the user access request form ([WARNING: RMF TEAM ACTION REQUIRED: Access Request Form]) process.


## 7. Access Agreements

Access agreements include nondisclosure agreements, acceptable use agreements, rules of behavior, and conflict-of-interest agreements. Signed access agreements include an acknowledgement that individuals have read, understand, and agree to abide by the constraints associated with organizational systems to which access is authorized. Organizations can use electronic signatures to acknowledge access agreements unless specifically prohibited by organizational policy.

{{ ORGANIZATION }} utilizes user access request form ([WARNING: RMF TEAM ACTION REQUIRED: Access Request Form]) as the method to request and grant access to {{ SYSTEM_NAME }}.

{{ ORGANIZATION }} will review, and update as required, access agreements, as mandated by security controls or no more than an annual basis. At which time upon making updated versions available to systems, all {{ ORGANIZATION }} {{ SYSTEM_NAME }} users are required to resign the document and have it added to their personnel record. If no changes are deemed necessary, signature by users is not required. Any user who fails to digitally sign an updated access agreement, regardless of having signed prior versions may be subject to have their access revoked to {{ SYSTEM_NAME }} until the document is signed or employment is terminated.  Discretion of the {{ ORGANIZATION }} may be exercised in certain circumstances and considered on a per instance basis.

Finally, {{ ORGANIZATION }} must ensure that all access agreements including those listed above must be digitally signed by the user via the user’s appropriate digital certificates prior to having their access request authorized. All access agreements must be resigned if their level of access changes.


## 8. External Personnel Security

External provider refers to organizations other than the organization operating or acquiring the system. External providers include service bureaus, contractors, and other organizations that provide system development, information technology services, testing or assessment services, outsourced applications, and network/security management. Organizations explicitly include personnel security requirements in acquisition-related documents. External providers may have personnel working at organizational facilities with credentials, badges, or system privileges issued by organizations. Notifications of external personnel changes ensure the appropriate termination of privileges and credentials. Any changes in transfers and terminations are deemed reportable by security-related characteristics that include functions, roles, and the nature of credentials or privileges associated with transferred or terminated individuals.

All third parties providing support to {{ ORGANIZATION }} {{ SYSTEM_NAME }} must meet all applicable DoD guidance to include:

- DoD 5220.22-M,

- DoD 5220.22-R,

- DoD 5200.2-R,

- DOD 8140 series/DoD 8570.01-M

- DoDI 3020.41

- Any {{ ORGANIZATION }} PMO/System policies for personnel security.

External vendors who are contracted to support {{ ORGANIZATION }} {{ SYSTEM_NAME }} must have roles and responsibilities explicitly defined in any contract authorizing their work to be performed.  {{ ORGANIZATION }} may define the roles and responsibilities to suit their support requirements.

> [!IMPORTANT]
> [WARNING: RMF TEAM ACTION REQUIRED: Verify and update operational contact/procedure details in this section.]
> In addition to any existing contract requirements, third-party providers are required to notify at a minimum, the system ISSO and responsible personnel for transferring credentials of any personnel transfers or terminations of third-party personnel who possess organizational credentials and/or badges, or who have information system privileges immediately.


## 9. Personnel Sanctions

In the event personnel fail to comply with established information security policies and procedures for {{ SYSTEM_NAME }}, formal sanctions will be employed.

> [!IMPORTANT]
> [WARNING: RMF TEAM ACTION REQUIRED: Verify and update operational contact/procedure details in this section.]
> The {{ SYSTEM_NAME }} ISSO will be immediately notified when the formal employee sanctions process is initiated, identifying the individual sanctioned and the reason for the sanction. The {{ SYSTEM_NAME }} ISSO will provide situational awareness to the {{ ORGANIZATION }} leadership within 24 hours of the sanctions process being initiated.

Formal Sanctions are part of the general personnel policies and procedures for the {{ SYSTEM_NAME }}. The process addresses the following:

- Informal corrective actions;

- Formal disciplinary actions;

- Severe disciplinary actions;

- Removal of system access; and

- Possible criminal and/or civil penalties.

NOTE: Any person who improperly discloses classified or sensitive information is subject to criminal and civil penalties and sanctions.


## 10. Position Descriptions

{{ ORGANIZATION }} will include specifications of security and privacy roles in individual position descriptions to facilitate clarity in understanding the security and/or privacy responsibilities associated with the roles. Additionally, {{ ORGANIZATION }} will provide any role-based security and privacy training requirements for the defined roles.



## Appendix A – Detailed Compliance Matrix

The following table provides detailed traceability between the policy implementation statements in this document, the authoritative NIST SP 800-53 Rev. 5 control requirements, DoD CCIs, and the technical/governance enforcement mechanisms active across {{ SYSTEM_NAME }}.


| CTRL ID | CTRLTITLE | REQUIRED eMASS STANDARD | DOCREF | ENFORCEMENT MECHANISM |
| :--- | :--- | :--- | :--- | :--- |
| PS-01 | Policy and Procedures | Develops, documents, and disseminates PS policy/procedures to personnel with access control duties; designates Senior Security Manager; reviews annually and upon regulation changes or insider incidents. (CCI-001504, CCI-001505, CCI-001506, CCI-001507, CCI-001508, CCI-001509, CCI-001510, CCI-001511, CCI-003017, CCI-003018, CCI-004498, CCI-004499, CCI-004500, CCI-004501, CCI-004502, CCI-004503, CCI-004504, CCI-004505, CCI-004506, CCI-004507, CCI-004508) | Section 2 | Formal policy publication in eMASS (System ID: {{ RMF_PACKAGE_ID }}); annual review cadence managed by Senior Security Manager, ISSM, and ISSO; trigger alignment with DoDM 5200.02 and CJCSM 6510.01B. |
| PS-02 | Position Risk Designation | Assigns risk designations to all positions (ADP-IT-I/II/III); establishes screening criteria; reviews annually, upon PD updates, or when vacated. (CCI-001512, CCI-001513, CCI-001514, CCI-001515) | Section 3 | {{ ORGANIZATION }} Position Designation System (PDS) assessments; formal position descriptions defining sensitivity levels and mandatory DoD 8140 baseline certifications. |
| PS-03 | Personnel Screening | Screens personnel prior to access; rescreens based on continuous vetting (DCSA) and immediately upon derogatory information. (CCI-001516, CCI-001517, CCI-001518, CCI-001519) | Section 4 | Defense Information System for Security (DISS) clearance verification; continuous vetting enrollment; PSO pre-access screening workflows. |
| PS-03(04) | Personnel Screening: Citizenship Requirements | Verifies individuals accessing classified info and {{ SENSITIVITY_CLASSIFICATION }} / {{ IMPACT_LEVEL }} meet United States citizenship requirements. (CCI-004509, CCI-004510, CCI-004511) | Section 4 | Mandatory U.S. citizenship validation recorded in DISS and personnel files; foreign national access blocked across all {{ SYSTEM_NAME }} projects. |
| PS-04 | Personnel Termination | Disables system access immediately (within 24 hours); revokes authenticators/credentials; conducts exit interviews on continuing {{ SENSITIVITY_CLASSIFICATION }} protection; retains access to data. (CCI-001522, CCI-001523, CCI-001524, CCI-001525, CCI-001526, CCI-003022, CCI-003023, CCI-003024) | Section 5 | Automated {{ IDENTITY_PROVIDER }} account disablement, SCIM sync to Cloud Identity, OAuth token revocation, physical GFE retrieval, and signed outprocessing debriefs. |
| PS-04(01) | Personnel Termination: Post-Employment Requirements | Notifies terminated individuals of legally binding post-employment {{ SENSITIVITY_CLASSIFICATION }} protection requirements; requires signed acknowledgment. (CCI-003027, CCI-003028) | Section 5 | Formal {{ ORGANIZATION }} exit interview debriefing; signed Acknowledgment of Post-Employment Requirements under 18 U.S.C. § 793 / § 1905 archived in security files. |
| PS-05 | Personnel Transfer | Reviews need-to-know on transfer; initiates transfer/reassignment actions immediately; modifies access; notifies ISSO and credential personnel within 24 hours. (CCI-001527, CCI-001528, CCI-001529, CCI-001530, CCI-003031, CCI-003032, CCI-003033, CCI-003034) | Section 6 | Automated transfer notification workflows within 24 hours; immediate removal of unneeded GCP IAM bindings; mandatory new {{ ACCESS_AGREEMENT_TYPE }} submission for new duties. |
| PS-06 | Access Agreements | Develops, reviews annually, and requires signed access agreements ({{ ACCESS_AGREEMENT_TYPE }}, NDAs, {{ RULES_OF_BEHAVIOR }}) prior to access; re-signs at least annually. (CCI-001532, CCI-001533, CCI-003035, CCI-004513, CCI-004514, CCI-004515, CCI-004516, CCI-004517, CCI-004518) | Section 7 | Digitally signed {{ ACCESS_AGREEMENT_TYPE }}, annual {{ RULES_OF_BEHAVIOR }} re-certification portal, and automated IAM access suspension upon expired agreements. |
| PS-06(03) | Access Agreements: Post-Employment Requirements | Notifies and requires signed acknowledgment of legally binding post-employment requirements as part of initial access authorization. (CCI-003038, CCI-003039) | Section 7 | Mandatory pre-access NDA and post-employment legal terms embedded in initial onboarding packages and {{ ACCESS_AGREEMENT_TYPE }} approvals. |
| PS-07 | External Personnel Security | Establishes personnel security requirements for external providers; requires compliance with DoD policies; requires notification of transfers/terminations within 1 working day; monitors compliance. (CCI-001539, CCI-001540, CCI-001541, CCI-003041, CCI-003042, CCI-003043, CCI-004519, CCI-004520) | Section 8 | Contractual SOW clauses enforcing NISPOM / DoDI 5200.02; mandatory 24-hour vendor termination notification to ISSO; semi-annual contractor clearance audits. |
| PS-08 | Personnel Sanctions | Employs formal sanctions process for security policy violations; notifies ISSO/ISSM within 24 hours of initiation. (CCI-003044, CCI-003045, CCI-003046, CCI-004521, CCI-004522) | Section 9 | Progressive disciplinary framework (Levels 1–4); automated incident ticketing; mandatory 24-hour notification to ISSO/ISSM and AO briefing. |
| PS-09 | Position Descriptions | Incorporates security and privacy roles, responsibilities, and training requirements into formal position descriptions. (CCI-004523, CCI-004524) | Section 10 | Formal military duty descriptions and civilian PDs detailing transport engineering, IAM, and ISSO continuous monitoring duties per DoD 8140 standards. |



## Appendix B – Rules of Behavior & User Directives (Google Appendix F)

In accordance with OMB Circular A-130 and Google Services Appendix F (Rules of Behavior), all {{ ORGANIZATION }} system users and administrators must sign and adhere to the following Rules of Behavior before accessing {{ SYSTEM_NAME }}:

1. **Acceptable Use**: System access is granted exclusively for official authorized government duties. Personal use, unauthorized software installation, or bypass of security controls (`AC-6`) is strictly prohibited.
2. **Authenticator Protection**: Users must protect MFA hardware keys and credentials (`IA-2`). Passwords/PINs must never be shared, stored in cleartext, or written down.
3. **Data Handling & Spillage Prevention**: Sensitive data ({{ SENSITIVITY_CLASSIFICATION }} / {{ IMPACT_LEVEL }}) must only be processed within approved GCP storage perimeters (`SC-7`, `MP-6`). Any suspected data spillage must be reported immediately (`IR-9`).
4. **Session Security**: Users must lock unattended workstations and terminate active administrative console sessions (`AC-11`, `AC-12`).
5. **Annual Re-Certification**: Rules of Behavior acknowledgement must be renewed annually by all users during mandatory Security Awareness Training (`AT-2`).
