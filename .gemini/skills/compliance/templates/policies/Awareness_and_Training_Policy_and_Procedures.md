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
> This document defines the enterprise security policy and implementation procedures for **Awareness and Training** under **NIST SP 800-53 Rev. 5 (AT)**.
> Technical infrastructure controls are automatically provisioned and enforced via **{{ SYSTEM_NAME }}** Terraform blueprints.
> Operational rules or contact details requiring manual confirmation are highlighted with RMF Team Callouts.


## 1. Overview

Awareness and Training policies and procedures for {{ ORGANIZATION }}, to include {{ SYSTEM_NAME }}, are built on the foundation of risk management. To secure {{ ORGANIZATION }} information technology (IT) systems, it is paramount that {{ SYSTEM_NAME }} users maintain literacy and awareness of the organization’s mission, their respective role in maintaining security and privacy, and the techniques in which to do so.

Federal agencies and organizations cannot protect the confidentiality, integrity, and availability of information in today’s highly networked systems environment without ensuring that all people involved in using and managing IT:


1. Understand their roles and responsibilities related to {{ ORGANIZATION }} mission;
2. Understand the {{ ORGANIZATION }} level awareness and training policies, procedures, and practices; and
3. Have at least adequate knowledge of the various management, operational, and technical controls required and available to protect the IT resources for which they are responsible.

As cited in audit reports, periodicals, and conference presentations, it is generally understood by the IT security professional community that people are one of the weakest links in attempts to secure systems and networks. The “people factor” - not technology - is key to providing an adequate and appropriate level of security. If people are the key, but are also a weak link, more and better attention must be paid to this “asset.”

{{ SYSTEM_NAME }} will adhere to this Awareness and Training plan, managed by {{ ORGANIZATION }}. Development, documentation and dissemination of the Awareness and Training policy and procedures will be completed with any updates included to account for changes in processes, requirements, and applicable training.

This plan does not claim to cover all possible means of awareness and training.

This document complies with the following requirements from NIST Special Publication 800-53 Revision 5, "Security and Privacy Controls for Federal Information Systems and Organizations” and is consistent with applicable laws, executive orders, directives, regulations, policies, standards, and guidelines. A detailed compliance matrix can be found in Appendix A, “Detailed Compliance Matrix”.


### 1.1 Applicability

This Awareness and Training Plan applies to the {{ ORGANIZATION }} {{ SYSTEM_NAME }}. All users must conduct required training at a minimum, on an annual basis, unless exceptions are in place.

All users must be able to provide a certificate of training to document completed training.

{{ ORGANIZATION }} {{ SYSTEM_NAME }} users can provide feedback on {{ ORGANIZATION }} training results to the {{ ORGANIZATION }} Cybersecurity Team.


## 2. Literacy Training and Awareness

Information technology has enabled {{ GOVERNANCE_REGIME }} organizations to transmit, communicate, collect, process, and store unprecedented amounts of information. Due to the increasing dependence on information systems, leadership has focused attention on the need to ensure that these assets, and the information they process, are protected from actions that would jeopardize the DoD’s ability to effectively function. Responsibility for securing the Department’s information and systems lies with the DoD Components. The trained, aware, and literate user is the first and most vital line of defense.

> [!IMPORTANT]
> <mark style="background-color: #fff9c4; color: #b71c1c; font-weight: bold; padding: 2px 6px; border-radius: 4px;">⚠️ RMF TEAM ACTION REQUIRED: Verify and update operational contact/procedure details in this section.</mark>
> Awareness is not training; awareness relies on reaching broad audiences with attractive techniques whereas training is formal with the goal of building knowledge and skills to facilitate job performance. In other words, awareness is used to reinforce the fact that security supports the mission of the organization by protecting valuable resources while the purpose of training is to teach the skills that will enable people to perform their jobs more securely. IT Security literacy then refers to an individual’s familiarity with – and ability to apply – a core knowledge set (i.e., “IT security basics”) needed to protect electronic information and systems. All individuals who use computer technology or its output products, regardless of their specific job responsibilities, must know IT security basics and be able to apply them.

Cyber training must be current, engaging, and relevant to the target audience to enhance its effectiveness. It must incorporate internal and external security events, incidents and breaches into the literacy and awareness training with the primary purpose to educate and influence behavior based on lessons learned. The focus must be on education and awareness of all threats that include persistent threats, phishing and cloud vulnerabilities, so users do not perform actions that lead to or enable exploitations of {{ GOVERNANCE_REGIME }} and Enterprise Information Systems.  Authorized users must understand that they are a critical link in their organization’s overall Information Assurance (IA) success.


### 2.1 General User Training

Annual Cybersecurity Awareness Training (such as the DISA Cyber Awareness Challenge or Federal/SLED equivalent) serves as the baseline standard. It meets all applicable {{ GOVERNANCE_REGIME }} requirements for end user awareness training. DISA will ensure it provides distributive awareness content to address evolving requirements promulgated by Congress, the Office of Management and Budget (OMB) under the Information Systems Security Line of Business (ISS LoB) for Tier I, or the Office of the Secretary of Defense.

Organizational components are required to use approved Cyber Awareness Providers for their Cyber Awareness Provider. The DoD Cyber Awareness Challenge will be used to meet the initial and annual training mandated by applicable federal, state, and organizational regulations.

To ensure understanding of the critical importance of Cyber, all individuals with access to {{ GOVERNANCE_REGIME }} IT systems shall receive and complete initial Cyber awareness training before being granted access to the system(s) and annual Cyber awareness training to retain access. This training is required for all system users to include senior leadership, military, civilian and contractors.

All General User training shall be managed and tracked by {{ ORGANIZATION }} at the {{ SYSTEM_NAME }} level for one (1) year. Personnel must retain individual personal records.


### 2.2 Privileged User Training

A privileged user is a user that is authorized (and, therefore, trusted) to have elevated rights to perform security-relevant functions that ordinary users are not authorized to perform. A number of high-profile security incidents continue to prove that privileged users -- administrators, contractors, and others with system-level access to IT infrastructure -- are a critical element of {{ SYSTEM_NAME }} overall risk profile.

In addition to signing a Privileged Access Agreement prior to account creation, individuals will take the [Privileged User Training](https://www.cdse.edu/Training/eLearning/DS-IA112) created by DISA.

All Privileged User training records are tracked by {{ ORGANIZATION }} at the {{ SYSTEM_NAME }} level for one (1) year. Personnel must retain individual Privileged User Training records.


### 2.3 Role-Based Training

The DoD leverages the National Initiative for Cybersecurity Education (NICE) Cybersecurity Workforce Framework (NCWF) and the Joint Cyberspace Training and Certification Standards to develop the DoD Cyber Workforce Framework (DCWF) or NIST NICE Framework. “The DCWF describes the work performed by the full spectrum of the cyber workforces as defined in DoD Directive (DoDD) 8140.01 / NIST NICE Framework “.

The {{ ORGANIZATION }} Cybersecurity Team ensures users have received role-based security and privacy training for duties assigned as a new user and for changes to job functions, initially, and annually thereafter based on continued duties in the assigned role.


### 2.4 Cyber Threat Environment

{{ ORGANIZATION }} is responsible for providing literacy training on the cyber threat environment that reflects the current cyber threat information in the system operations. Since threats continue to change over time, threat literacy training by the organization is dynamic. Moreover, threat literacy training is not performed in isolation from the system operations that support organizational mission and business functions.



### 2.5 Google Cloud Platform (GCP) Inherited Controls & Shared Responsibility Boundary

- **Google Inherited Controls**: Google Services enforces mandatory security awareness training (`AT-2`) and specialized role-based training (`AT-3`) for all Google personnel, data center engineers, and cloud infrastructure developers.
- **Customer Implementation Responsibilities**: {{ ORGANIZATION }} is responsible for administering annual Security Awareness Training (`AT-2`), role-based DevSecOps training (`AT-3`), and maintaining training completion logs for all {{ ORGANIZATION }} system administrators and personnel (`AT-4`).

## 3. Physical Security Training

Physical security training shall be handled by {{ ORGANIZATION }} or at the organization level. Local personnel shall reference the Security SOP as their reference for meeting training requirements.


#
### 3.1 Google Cloud Platform (GCP) Inherited Controls & Shared Responsibility Boundary

- **Google Inherited Controls**: Google Services enforces mandatory security awareness training (`AT-2`) and specialized role-based training (`AT-3`) for all Google personnel, data center engineers, and cloud infrastructure developers.
- **Customer Implementation Responsibilities**: {{ ORGANIZATION }} is responsible for administering annual Security Awareness Training (`AT-2`), role-based DevSecOps training (`AT-3`), and maintaining training completion logs for all {{ ORGANIZATION }} system administrators and personnel (`AT-4`).

## 4. Applicable Security Controls

The following physical access controls have been documented as requiring training:


| Number | Control | Control Text | Training Resource |
| --- | --- | --- | --- |
| PE-1 | Policy and Procedures | This control addresses the establishment of policy and procedures for the effective implementation of selected security controls and control enhancements in the PE family. Policy and procedures reflect applicable federal laws, Executive Orders, directives, regulations, policies, standards, and guidance | [Introduction to Physical Security](https://www.cdse.edu/Training/eLearning/PY011) |
| PE-2 | Physical Access Authorizations | This control applies to organizational employees and visitors. Individuals (e.g., employees, contractors, and others) with permanent physical access authorization credentials are not considered visitors. Authorization credentials include, for example, badges, identification cards, and smart cards | [Physical Security Planning and Implementation](https://www.cdse.edu/Training/eLearning/PY106) |
| PE-3 | Physical Access Control | This control applies to organizational employees and visitors. Individuals (e.g., employees, contractors, and others) with permanent physical access authorization credentials are not considered visitors. Physical access devices include, for example, keys, locks, combinations, biometric readers, and card readers. | [Lock and Key Systems](https://www.cdse.edu/Training/eLearning/PY104) |
| PE-6 | Monitoring Physical Access | Organizational incident response capabilities include investigations of and responses to detected physical security incidents. Security incidents include, for example, apparent security violations or suspicious physical access activities | [Physical Security Measures](https://www.cdse.edu/Training/eLearning/PY103) |


### 4.1 Google Cloud Platform (GCP) Inherited Controls & Shared Responsibility Boundary

- **Google Inherited Controls**: Google Services enforces mandatory security awareness training (`AT-2`) and specialized role-based training (`AT-3`) for all Google personnel, data center engineers, and cloud infrastructure developers.
- **Customer Implementation Responsibilities**: {{ ORGANIZATION }} is responsible for administering annual Security Awareness Training (`AT-2`), role-based DevSecOps training (`AT-3`), and maintaining training completion logs for all {{ ORGANIZATION }} system administrators and personnel (`AT-4`).

## 5. Personnel and Roles

All {{ ORGANIZATION }} {{ SYSTEM_NAME }} users will be required to identify specific individuals or groups to fulfill physical security roles. The roles should be clearly defined, with personnel assigned to and aware of their physical security roles, with training requirements completed.

The following roles have been identified as requiring physical security training:


> [!IMPORTANT]
> <mark style="background-color: #fff9c4; color: #b71c1c; font-weight: bold; padding: 2px 6px; border-radius: 4px;">⚠️ RMF TEAM ACTION REQUIRED: Identify assigned personnel and confirm physical security training completion dates in this table.</mark>

| Role | Assigned Personnel | Training Completed? |
| --- | --- | --- |
| Security Manager | <mark style="background-color: #fff9c4; color: #b71c1c; font-weight: bold; padding: 1px 5px; border-radius: 3px;">⚠️ RMF TEAM ACTION REQUIRED: Assign Personnel</mark> | <mark style="background-color: #fff9c4; color: #b71c1c; font-weight: bold; padding: 1px 5px; border-radius: 3px;">⚠️ RMF TEAM ACTION REQUIRED: Confirm Status</mark> |
| Physical Security Manager | <mark style="background-color: #fff9c4; color: #b71c1c; font-weight: bold; padding: 1px 5px; border-radius: 3px;">⚠️ RMF TEAM ACTION REQUIRED: Assign Personnel</mark> | <mark style="background-color: #fff9c4; color: #b71c1c; font-weight: bold; padding: 1px 5px; border-radius: 3px;">⚠️ RMF TEAM ACTION REQUIRED: Confirm Status</mark> |
| Base Security | <mark style="background-color: #fff9c4; color: #b71c1c; font-weight: bold; padding: 1px 5px; border-radius: 3px;">⚠️ RMF TEAM ACTION REQUIRED: Assign Personnel</mark> | <mark style="background-color: #fff9c4; color: #b71c1c; font-weight: bold; padding: 1px 5px; border-radius: 3px;">⚠️ RMF TEAM ACTION REQUIRED: Confirm Status</mark> |


## 6. {{ SYSTEM_NAME }} Non-Access or Role-Based Training


### 6.1 Insider Threat Training

Insider Threat Awareness is an essential component of a comprehensive security program. Its’ purpose is to deter, detect, and mitigate actions by insiders who represent a threat to national security.

Potential indicators and possible precursors of insider threat can include behaviors such as inordinate, long-term job dissatisfaction; attempts to gain access to information not required for job performance; unexplained access to financial resources; bullying or harassment of fellow employees; workplace violence; and other serious violations of policies, procedures, directives, regulations, rules, or practices.

{{ ORGANIZATION }} {{ SYSTEM_NAME }} users will be required to complete Insider Threat Awareness Training offered by The Center for Development of Security Excellence (CDSE).


### 6.2 Social Engineering and Mining Training

Users must be trained to recognize indicators to identify when they are targeted by social engineers. There are various types of social engineering, including phishing, spear phishing, whaling, smishing, and vishing. Users are the best line of defense; attempts can be internal to the organization and external.

Social engineering is an attempt to trick an individual into revealing information or taking an action that can be used to breach, compromise, or otherwise adversely impact a system. Social engineering includes phishing, pretexting, impersonation, baiting, quid pro quo, thread-jacking, social media exploitation, and tailgating. Social mining is an attempt to gather information about the organization that may be used to support future attacks.

{{ ORGANIZATION }} {{ SYSTEM_NAME }} users will be required to complete Phishing and Social Engineering: Virtual Communication Awareness Training offered by The Center for Development of Security Excellence (CDSE).



## Appendix A – Detailed Compliance Matrix

The following table provides detailed traceability between the policy implementation statements in this document, the authoritative NIST SP 800-53 Rev. 5 control requirements, DoD CCIs, and the technical/governance enforcement mechanisms active across {{ SYSTEM_NAME }}.


| CTRL ID | CTRLTITLE | REQUIRED eMASS STANDARD | DOCREF | ENFORCEMENT MECHANISM |
| :--- | :--- | :--- | :--- | :--- |
| AT-01 | Policy and Procedures | Develop, document, disseminate to all personnel, and review/update annually (or upon significant security incidents, threat intelligence changes, or architectural shifts) awareness and training policy and procedures. (CCIs: 000100, 000101, 000102, 000103, 000104, 000105, 001564, 001565, 002048, 002049, 003761, 003762, 003763, 003764, 003765) | Section 1 | Formal annual review workflow by {{ ORGANIZATION }} ISSM/SO/AO; publishing to central {{ ORGANIZATION }} governance portals; event-driven RMF update triggers. |
| AT-02 | Literacy Training and Awareness | Provide basic cybersecurity and privacy literacy training to all users initially and at least annually (every 365 days); update content based on trending threats, policy changes, and incident lessons learned. (CCIs: 000106, 000112, 003766, 003767, 003768, 003769, 003770, 003771, 003772, 003773, 003774, 005147) | Section 2 | Cyber awareness training integration; compliance tracking; {{ IDENTITY_PROVIDER }} conditional access account suspension on training lapse. |
| AT-02(02) | Insider Threat | Provide literacy training on recognizing and reporting insider threat indicators, precursors, and anomalous behavior. (CCIs: 002055) | Section 2 | CDSE Insider Threat Awareness course integration; mandatory initial and annual completion validation by ISSO. |
| AT-02(03) | Social Engineering and Mining | Provide literacy training on recognizing social engineering, phishing, spear phishing, smishing, vishing, and open-source social mining. (CCIs: 003775, 003776) | Section 2 | CDSE Phishing and Social Engineering training; command-sponsored automated phishing simulation platforms. |
| AT-02(04) | Suspicious Communications and Anomalous System Behavior | Train users to recognize suspicious communications, anomalous system behavior, phishing attempts, malicious attachments, and physical attacks. (CCIs: 003777, 003778) | Section 2 | Targeted {{ SYSTEM_NAME }} threat awareness curriculum; automated SIEM anomaly reporting workflows; operational cybersecurity incident escalation paths. |
| AT-02(05) | Advanced Persistent Threat | Provide awareness training on the capabilities, tradecraft, and tactics, techniques, and procedures (TTPs) of Advanced Persistent Threats (APTs). (CCIs: 003779) | Section 2 | Specialized cyber operations and DISA threat intelligence briefing modules; zero-trust cloud attack surface training. |
| AT-03 | Role-Based Training | Provide comprehensive role-based cybersecurity and privacy training to privileged users, network admins, DevSecOps engineers, and ISSMs/ISSOs initially and at least annually. (CCIs: 000108, 000109, 003782, 003783, 003784, 003785, 003786, 003787, 003788, 003789) | Section 3 & 6 | DCWF / DoDD 8140.01 certification enforcement (CISSP, CASP+, Google Cloud Professional); ATCTS credential verification. |
| AT-03(01) | Environmental Controls | Train authorized and privileged personnel in the employment, operation, and emergency procedures for environmental controls at least annually. (CCIs: 001481, 001482, 001483, 002050) | Section 3 | Physical colocation facility SOP training (HVAC, UPS, PDU, fire suppression); inherited GCP data center IL5 P-ATO controls. |
| AT-03(02) | Physical Security Controls | Provide annual physical security controls training to all physical security personnel, facility managers, and network field technicians. (CCIs: 001566, 001567, 001568, 002051) | Section 4 & 5 | CDSE Physical Security curriculum (PY011, PY106, PY104, PY103); physical security qualification records and DoDM 5200.08 logs. |
| AT-03(03) | Practical Exercises | Include practical training exercises and simulated emergency scenarios in role-based training programs at least annually. (CCIs: 002052, 003790) | Section 6 | Annual multi-cloud failover drills; BGP hijacking tabletop simulations; automated CI/CD compromised pipeline recovery exercises. |
| AT-03(05) | Processing Personally Identifiable Information | Provide annual role-based training on PII processing, transparency controls, and Privacy Act compliance to all personnel accessing systems. (CCIs: 003791, 003792, 003793) | Section 6 | Annual DoD Privacy and Civil Liberties training; Cloud DLP inspection and redaction operational training. |
| AT-04 | Training Records | Document, centrally track, and retain individual training records, completion certificates, and qualifications for at least 5 years. (CCIs: 000113, 000114, 001336, 001337, 003794, 003795) | Section 1.1 | Centralized ATCTS database tracking; quarterly ISSO compliance audits; automated 15-day grace period disablement scripts. |
| AT-06 | Training Feedback | Provide formal feedback on organizational training results and metrics to supervisors and cybersecurity officials at least annually or post-incident. (CCIs: 003796, 003797, 003798) | Section 1.1 | Annual executive training metrics reports; phishing simulation analysis dashboards; post-incident training gap reviews. |
