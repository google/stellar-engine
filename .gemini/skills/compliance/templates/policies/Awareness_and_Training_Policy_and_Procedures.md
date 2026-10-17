# AT - Awareness and Training Policy and Procedures

## Document Governance & Approval Baseline

| Governance Metric | Policy Standard & Specification |
| :--- | :--- |
| **Document Title** | Awareness and Training Policy and Procedures |
| **NIST Control Family** | Awareness and Training (AT) |
| **Primary NIST Benchmark** | NIST SP 800-50 (Building an Information Technology Security Awareness Program) |
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
> This document defines the enterprise security policy and implementation procedures for **Awareness and Training** under **NIST SP 800-53 Rev. 5 (AT)**.
> Technical infrastructure controls are automatically provisioned and enforced via **{{ SYSTEM_NAME }}** Terraform blueprints.
> Operational rules or contact details requiring manual confirmation are highlighted with RMF Team Callouts.


## 1. Overview

Federal agencies and organizations cannot protect the confidentiality, integrity, and availability of information in today's highly networked systems environment without ensuring that all people involved in using and managing IT:

1. Understand their roles and responsibilities related to the organizational mission;
2. Understand the organization's IT security policy, procedures, and practices; and
3. Have at least adequate knowledge of the various management, operational, and technical controls required and available to protect the IT resources for which they are responsible.

The purpose of this Awareness and Training Policy is to ensure that all personnel who use or manage {{ SYSTEM_NAME }} receive security and privacy literacy training and role-based training appropriate to their responsibilities, and that training completion is documented and tracked.

This policy addresses the Awareness and Training (AT) family requirements of NIST Special Publication 800-53 Revision 5, "Security and Privacy Controls for Information Systems and Organizations." A detailed compliance matrix is provided in Appendix A, "Detailed Compliance Matrix."

The Awareness and Training Policy encompasses all {{ ORGANIZATION }} users who have access to {{ SYSTEM_NAME }}. This policy outlines the framework for establishing, implementing, and maintaining security and privacy awareness and training in alignment with applicable {{ GOVERNANCE_REGIME }} guidelines (NIST SP 800-53, FedRAMP, and applicable federal and state regulations), and is consistent with applicable laws, executive orders, directives, regulations, policies, standards, and guidelines. It applies to employees, contractors, and third-party users who handle sensitive information or operate within the {{ ORGANIZATION }} {{ SYSTEM_NAME }} information technology infrastructure.

{{ ORGANIZATION }} management is committed to the requirements of this policy and provides the resources needed to implement them. The ISSM ({{ ISSM_NAME }}) manages the development, documentation, and dissemination of this policy and its procedures, and coordinates their implementation with the Authorizing Official, System Owner, ISSO, and other organizational entities identified in the Program Roles & Responsibilities Matrix.

This policy and its procedures are reviewed and updated at least annually and following significant changes to {{ SYSTEM_NAME }} or its operating environment, security or privacy incidents, assessment or audit findings, or changes in applicable laws, executive orders, directives, regulations, policies, standards, or guidelines.

### 1.1 Background

As audit reports, periodicals, and conference presentations have noted, the IT security community generally understands that people are one of the weakest links in attempts to secure systems and networks. The "people factor," not technology, is key to providing an adequate level of security. Because people are both the key and a weak link, they need sustained attention through awareness and training.

This policy does not cover every possible means of awareness and training.


### 1.2 Applicability

This policy applies to {{ ORGANIZATION }} {{ SYSTEM_NAME }}. All users must complete required training at least annually unless an approved Exception-to-Policy (ETP) is in place.

Users must be able to provide a training certificate as evidence of completed training. {{ ORGANIZATION }} documents and monitors each user's security and privacy training and retains individual training records for at least five (5) years.

{{ ORGANIZATION }} {{ SYSTEM_NAME }} users can give feedback on training to the {{ ORGANIZATION }} Cybersecurity Team. At least annually, and after incidents that reveal training gaps, the Cybersecurity Team reports organizational training results, such as completion rates and phishing simulation results, to supervisors and the ISSM.


## 2. Literacy Training and Awareness

Information technology lets {{ GOVERNANCE_REGIME }} organizations transmit, collect, process, and store large amounts of information. Because of this dependence on information systems, leadership must ensure that these systems, and the information they process, are protected from actions that would jeopardize {{ ORGANIZATION }}'s ability to function. The trained, aware, and literate user is the first line of defense.

> [!IMPORTANT]
> [WARNING: RMF TEAM ACTION REQUIRED: Verify and update operational contact/procedure details in this section.]
> Awareness is not training. Awareness reaches broad audiences with attention-getting techniques, whereas training is formal and builds the knowledge and skills needed for job performance. Awareness reinforces that security supports the organization's mission by protecting valuable resources; training teaches the skills people need to do their jobs more securely. IT security literacy is an individual's familiarity with, and ability to apply, a core knowledge set (i.e., "IT security basics") needed to protect electronic information and systems. All individuals who use computer technology or its output products, regardless of their job responsibilities, must know IT security basics and be able to apply them.

Cyber training must be current and relevant to the target audience. It incorporates lessons learned from internal and external security events, incidents, and breaches, with the goal of educating users and influencing their behavior. It covers current threats, including persistent threats, phishing, and cloud vulnerabilities, so that users do not take actions that lead to or enable exploitation of {{ GOVERNANCE_REGIME }} and enterprise information systems. Literacy training teaches users to recognize and report suspicious communications, such as phishing messages and malicious attachments, and anomalous system behavior that can indicate malicious code. Authorized users must understand that they are a critical link in their organization's information assurance (IA) program.


### 2.1 General User Training

Annual cybersecurity awareness training, such as the DISA Cyber Awareness Challenge or a federal or SLED equivalent, is the baseline standard and meets the applicable {{ GOVERNANCE_REGIME }} requirements for end user awareness training. DISA updates the Cyber Awareness Challenge content to address requirements issued by Congress, the Office of Management and Budget (OMB) under the Information Systems Security Line of Business (ISS LoB) for Tier I, or the Office of the Secretary of Defense.

Organizational components must use an approved cyber awareness training provider. The DoD Cyber Awareness Challenge, or an approved federal or SLED equivalent, meets the initial and annual training requirement set by applicable federal, state, and organizational regulations.

All individuals with access to {{ SYSTEM_NAME }} must complete initial cyber awareness training before they are granted access, and annual cyber awareness training to keep access. This requirement applies to all system users, including senior leadership, military, civilian, and contractor personnel.

{{ ORGANIZATION }} tracks general user training at the {{ SYSTEM_NAME }} level and retains the records for at least five (5) years. Personnel must also keep their own training records.


### 2.2 Privileged User Training

A privileged user is a user who is authorized (and therefore trusted) to have elevated rights to perform security-relevant functions that ordinary users are not authorized to perform. High-profile security incidents continue to show that privileged users, such as administrators, contractors, and others with system-level access to IT infrastructure, are a critical element of the {{ SYSTEM_NAME }} risk profile.

In addition to signing a Privileged Access Agreement before account creation, individuals must complete the [Privileged User Training](https://www.cdse.edu/Training/eLearning/DS-IA112) created by DISA.

{{ ORGANIZATION }} tracks privileged user training at the {{ SYSTEM_NAME }} level and retains the records for at least five (5) years. Personnel must also keep their own privileged user training records.


### 2.3 Role-Based Training

The DoD used the National Initiative for Cybersecurity Education (NICE) Cybersecurity Workforce Framework and the Joint Cyberspace Training and Certification Standards to develop the DoD Cyber Workforce Framework (DCWF), which describes the work performed by the cyber workforce as defined in DoD Directive (DoDD) 8140.01. Organizations outside the DoD can use the NIST NICE Framework for the same purpose.

The {{ ORGANIZATION }} Cybersecurity Team ensures that personnel receive role-based security and privacy training before they are authorized to access the system or perform assigned duties, when their job functions or the system change, and at least annually thereafter. Role-based training includes practical exercises, such as tabletop simulations and failover drills, that reinforce training objectives. All personnel who access {{ SYSTEM_NAME }} receive initial and annual training on personally identifiable information (PII) processing and transparency controls, including Privacy Act requirements.


### 2.4 Cyber Threat Environment

{{ ORGANIZATION }} provides literacy training on the cyber threat environment that reflects current cyber threat information for system operations. Because threats change over time, threat literacy training is updated as the threat environment changes, and it is tied to the system operations that support organizational mission and business functions. Threat literacy training covers the advanced persistent threat (APT), including the tactics, techniques, and procedures used by APT actors.


### 2.5 Google Cloud Platform (GCP) Inherited Controls & Shared Responsibility Boundary

- **Google Inherited Controls**: Google enforces mandatory security awareness training (`AT-2`) and specialized role-based training (`AT-3`) for all Google personnel, data center engineers, and cloud infrastructure developers.
- **Customer Implementation Responsibilities**: {{ ORGANIZATION }} is responsible for administering annual Security Awareness Training (`AT-2`), role-based DevSecOps training (`AT-3`), and maintaining training completion logs for all {{ ORGANIZATION }} system administrators and personnel (`AT-4`).

## 3. Physical Security Training

{{ ORGANIZATION }} provides physical security training at the organization level. Personnel in the roles listed in Section 5 receive initial and annual training in the employment and operation of physical security controls, using the courses listed in Section 4 and the local Security SOP.

Personnel who operate environmental controls at {{ ORGANIZATION }} facilities, such as HVAC, uninterruptible power supply, power distribution, and fire suppression systems, receive initial and annual training in their employment and operation under the same SOP. Environmental control training for Google data center personnel is inherited from Google Cloud.

## 4. Applicable Security Controls and Role-Based Curriculum

This policy implements the Awareness and Training (`AT`) control family (`AT-1` Policy and Procedures, `AT-2` Literacy Training and Awareness, `AT-3` Role-Based Training, `AT-4` Training Records, and `AT-6` Training Feedback; note that `AT-5` was withdrawn in NIST SP 800-53 Rev. 5 and incorporated into `PM-15`), as mapped in Appendix A.

For personnel assigned physical security responsibilities under `AT-3(2)` (see Section 3 and Section 5), the following Center for Development of Security Excellence (CDSE) curriculum supports physical security control operation:

- **Physical Security Policy and Procedures (`PE-1` context)**: [Introduction to Physical Security](https://www.cdse.edu/Training/eLearning/PY011) — establishes foundational policy and procedural training for physical security controls.
- **Physical Access Authorizations (`PE-2` context)**: [Physical Security Planning and Implementation](https://www.cdse.edu/Training/eLearning/PY106) — covers authorization credentials (badges, identification cards, and smart cards) for employees and visitors.
- **Physical Access Control (`PE-3` context)**: [Lock and Key Systems](https://www.cdse.edu/Training/eLearning/PY104) — covers operation and maintenance of physical access devices (keys, locks, combinations, biometric readers, and card readers).
- **Monitoring Physical Access (`PE-6` context)**: [Physical Security Measures](https://www.cdse.edu/Training/eLearning/PY103) — covers physical access monitoring and response to suspicious physical access activities.

## 5. Personnel and Roles

{{ ORGANIZATION }} identifies the individuals or groups that fill physical security roles for {{ ORGANIZATION }} {{ SYSTEM_NAME }}. Each role is defined, and the assigned personnel know their physical security responsibilities and complete the required training.

The following roles have been identified as requiring physical security training:


> [!IMPORTANT]
> [WARNING: RMF TEAM ACTION REQUIRED: Identify assigned personnel and confirm physical security training completion dates in this table.]

| Role | Assigned Personnel | Training Completed? |
| --- | --- | --- |
| Security Manager | [WARNING: RMF TEAM ACTION REQUIRED: Assign Personnel] | [WARNING: RMF TEAM ACTION REQUIRED: Confirm Status] |
| Physical Security Manager | [WARNING: RMF TEAM ACTION REQUIRED: Assign Personnel] | [WARNING: RMF TEAM ACTION REQUIRED: Confirm Status] |
| Base Security | [WARNING: RMF TEAM ACTION REQUIRED: Assign Personnel] | [WARNING: RMF TEAM ACTION REQUIRED: Confirm Status] |


## 6. Additional Literacy Training Topics


### 6.1 Insider Threat Training

Insider threat awareness is an essential part of a security program. Its purpose is to deter, detect, and mitigate actions by insiders who represent a threat to national security.

Potential indicators and possible precursors of insider threat can include behaviors such as inordinate, long-term job dissatisfaction; attempts to gain access to information not required for job performance; unexplained access to financial resources; bullying or harassment of fellow employees; workplace violence; and other serious violations of policies, procedures, directives, regulations, rules, or practices.

{{ ORGANIZATION }} {{ SYSTEM_NAME }} users must complete the Insider Threat Awareness training offered by the Center for Development of Security Excellence (CDSE), initially and annually. The training covers how to recognize and report potential indicators of insider threat.


### 6.2 Social Engineering and Mining Training

Users are trained to recognize when they are targeted by social engineers and to report potential and actual social engineering and social mining attempts. Users are the best line of defense, and attempts can come from inside or outside the organization.

Social engineering is an attempt to trick an individual into revealing information or taking an action that can be used to breach, compromise, or otherwise adversely impact a system. Social engineering includes phishing, spear phishing, whaling, smishing, vishing, pretexting, impersonation, baiting, quid pro quo, thread-jacking, social media exploitation, and tailgating. Social mining is an attempt to gather information about the organization that may be used to support future attacks.

{{ ORGANIZATION }} {{ SYSTEM_NAME }} users must complete the Phishing and Social Engineering: Virtual Communication Awareness training offered by the Center for Development of Security Excellence (CDSE).



## Appendix A – Detailed Compliance Matrix

The following table provides detailed traceability between the policy implementation statements in this document, the authoritative NIST SP 800-53 Rev. 5 control requirements, DoD CCIs, and the technical/governance enforcement mechanisms active across {{ SYSTEM_NAME }}.


| CTRL ID | CTRLTITLE | REQUIRED {{ GRC_STANDARD_LABEL }} STANDARD | DOCREF | ENFORCEMENT MECHANISM |
| :--- | :--- | :--- | :--- | :--- |
| AT-01 | Policy and Procedures | Develop, document, and disseminate to all personnel the awareness and training policy and procedures; designate the ISSM to manage them; review and update them at least annually and following significant system changes, security or privacy incidents, assessment or audit findings, or changes in applicable laws, regulations, or guidance. (CCI-000100, CCI-000101, CCI-000102, CCI-000103, CCI-000104, CCI-000105, CCI-001564, CCI-001565, CCI-002048, CCI-002049, CCI-003761, CCI-003762, CCI-003763, CCI-003764, CCI-003765) | Section 1 | Formal annual review workflow managed by the {{ ORGANIZATION }} ISSM with SO and AO approval; publishing to central {{ ORGANIZATION }} governance portals; event-driven RMF update triggers. |
| AT-02 | Literacy Training and Awareness | Provide basic cybersecurity and privacy literacy training to all users initially and at least annually (every 365 days); update content based on trending threats, policy changes, and incident lessons learned. (CCI-000106, CCI-000112, CCI-003766, CCI-003767, CCI-003768, CCI-003769, CCI-003770, CCI-003771, CCI-003772, CCI-003773, CCI-003774, CCI-005147) | Section 2 | Cyber awareness training integration; compliance tracking; {{ IDENTITY_PROVIDER }} conditional access account suspension on training lapse. |
| AT-02(02) | Insider Threat | Provide literacy training on recognizing and reporting insider threat indicators, precursors, and anomalous behavior. (CCI-002055) | Section 6.1 | CDSE Insider Threat Awareness course integration; mandatory initial and annual completion validation by ISSO. |
| AT-02(03) | Social Engineering and Mining | Provide literacy training on recognizing social engineering, phishing, spear phishing, smishing, vishing, and open-source social mining. (CCI-003775, CCI-003776) | Section 6.2 | CDSE Phishing and Social Engineering training; command-sponsored automated phishing simulation platforms. |
| AT-02(04) | Suspicious Communications and Anomalous System Behavior | Train users to recognize suspicious communications, anomalous system behavior, phishing attempts, malicious attachments, and physical attacks. (CCI-003777, CCI-003778) | Section 2 | Targeted {{ SYSTEM_NAME }} threat awareness curriculum; automated SIEM anomaly reporting workflows; operational cybersecurity incident escalation paths. |
| AT-02(05) | Advanced Persistent Threat | Provide awareness training on the capabilities, tradecraft, and tactics, techniques, and procedures (TTPs) of Advanced Persistent Threats (APTs). (CCI-003779) | Section 2.4 | Specialized cyber operations and DISA threat intelligence briefing modules; zero-trust cloud attack surface training. |
| AT-02(06) | Cyber Threat Environment | Enforce cyber threat environment requirements across {{ SYSTEM_NAME }} in accordance with NIST SP 800-53 Rev. 5 AT-2(6). (CCI-003780, CCI-003781) | Section 3 | Enforced via Google Cloud infrastructure controls, Terraform configuration baselines, and ISSM/ISSO governance verification. |
| AT-03 | Role-based Training | Provide role-based cybersecurity and privacy training to privileged users, network admins, DevSecOps engineers, and ISSMs/ISSOs initially and at least annually. (CCI-000108, CCI-000109, CCI-003782, CCI-003783, CCI-003784, CCI-003785, CCI-003786, CCI-003787, CCI-003788, CCI-003789) | Section 2.2 & 2.3 | DCWF / DoDD 8140.01 certification enforcement (CISSP, CompTIA SecurityX (formerly CASP+), Google Cloud Professional certifications); ATCTS credential verification. |
| AT-03(01) | Environmental Controls | Train authorized and privileged personnel in the employment, operation, and emergency procedures for environmental controls initially and at least annually. (CCI-001481, CCI-001482, CCI-001483, CCI-002050) | Section 3 | Physical colocation facility SOP training (HVAC, UPS, PDU, fire suppression); inherited Google Cloud data center IL5 P-ATO controls. |
| AT-03(02) | Physical Security Controls | Provide initial and annual physical security controls training to all physical security personnel, facility managers, and network field technicians. (CCI-001566, CCI-001567, CCI-001568, CCI-002051) | Section 3, 4 & 5 | CDSE Physical Security curriculum (PY011, PY106, PY104, PY103); physical security qualification records and DoDM 5200.08 logs. |
| AT-03(03) | Practical Exercises | Include practical training exercises and simulated emergency scenarios in role-based training programs at least annually. (CCI-002052, CCI-003790) | Section 2.3 | Annual multi-cloud failover drills; BGP hijacking tabletop simulations; automated CI/CD compromised pipeline recovery exercises. |
| AT-03(05) | Processing Personally Identifiable Information | Provide initial and annual role-based training on PII processing, transparency controls, and Privacy Act compliance to all personnel who access the system. (CCI-003791, CCI-003792, CCI-003793) | Section 2.3 | Annual DoD Privacy and Civil Liberties training; Cloud DLP inspection and redaction operational training. |
| AT-04 | Training Records | Document, centrally track, and retain individual training records, completion certificates, and qualifications for at least 5 years. (CCI-000113, CCI-000114, CCI-001336, CCI-001337, CCI-003794, CCI-003795) | Section 1.2 | Centralized ATCTS database tracking; quarterly ISSO compliance audits; automated 15-day grace period disablement scripts. |
| AT-06 | Training Feedback | Provide formal feedback on organizational training results and metrics to supervisors and cybersecurity officials at least annually or post-incident. (CCI-003796, CCI-003797, CCI-003798) | Section 1.2 | Annual executive training metrics reports; phishing simulation analysis dashboards; post-incident training gap reviews. |
