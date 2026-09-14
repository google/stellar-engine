# PM - Program Management Policy and Procedures

## Document Governance & Approval Baseline

| Governance Metric | Policy Standard & Specification |
| :--- | :--- |
| **Document Title** | Program Management Policy and Procedures |
| **NIST Control Family** | Program Management (PM) |
| **Primary NIST Benchmark** | NIST SP 800-53 Rev. 5 (PM Family), OMB Circular A-130 |
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
> This document defines the enterprise security policy and implementation procedures for **Program Management** under **NIST SP 800-53 Rev. 5 (PM)**.
> Technical infrastructure controls are automatically provisioned and enforced via **{{ SYSTEM_NAME }}** Terraform blueprints.
> Operational rules or contact details requiring manual confirmation are highlighted with RMF Team Callouts.


## 1. Information Security Program Plan

An information security program plan is a formal document that provides an overview of the security requirements for an organization-wide information security program meeting those requirements. An information security program plan can be represented in a single document or compilations of documents. Privacy program plans and supply chain risk management plans are addressed separately in PM-18 and SR-2, respectively.

An information security program plan documents implementation details about program management and common controls. The plan provides sufficient information about the controls (including specification of parameters for assignment and selection operations, explicitly or by reference) to enable implementations that are unambiguously compliant with the intent of the plan and a determination of the risk to be incurred if the plan is implemented as intended. Updates to information security program plans include organizational changes and problems identified during plan implementation or control assessments.

Program management controls may be implemented at the organization level or the mission or business process level, and are essential for managing the organization’s information security program. Program management controls are distinct from common, system-specific, and hybrid controls because program management controls are independent of any particular system. Together, the individual system security plans and the organization-wide information security program plan provide complete coverage for the security controls employed within the organization.

Common controls available for inheritance by organizational systems are documented in an appendix to the organization’s information security program plan unless the controls are included in a separate security plan for a system. The organization-wide information security program plan indicates which separate security plans contain descriptions of common controls.

Events that may precipitate an update to the information security program plan include, but are not limited to, organization-wide assessment or audit findings, security incidents or breaches, or changes in laws, executive orders, directives, regulations, policies, standards, and guidelines.

This document complies with the following requirements from NIST Special Publication 800-53 Revision 5, "Security and Privacy Controls for Federal Information Systems and Organizations". A detailed compliance matrix can be found in Appendix A, “Detailed Compliance Matrix”.


## 2. Information Security and Privacy Resources

Organizations consider establishing champions for information security and privacy and, as part of including the necessary resources, assign specialized expertise and resources as needed. Organizations may designate and empower an Investment Review Board or similar group to manage and provide oversight for the information security and privacy aspects of the capital planning and investment control process.



### 2.1 Google Cloud Platform (GCP) Inherited Controls & Shared Responsibility Boundary

- **Google Inherited Controls**: Google Cloud maintains enterprise Risk Management Framework (RMF) program management (`PM-1`, `PM-2`), threat intelligence integration (`PM-16`), and CSP security leadership.
- **Customer Implementation Responsibilities**: {{ ORGANIZATION }} is responsible for appointing a qualified ISSM and ISSO (`PM-2`), establishing security capital planning (`PM-3`), and executing system-level security program management.

## 3. Plan of Actions and Milestones

The plan of action and milestones is a key organizational document and is subject to reporting requirements established by the Office of Management and Budget. Organizations develop plans of action and milestones with an organization-wide perspective, prioritizing risk response actions and ensuring consistency with the goals and objectives of the organization. Plan of action and milestones updates are based on findings from control assessments and continuous monitoring activities. There can be multiple plans of action and milestones corresponding to the information system level, mission/business process level, and organizational/governance level. While plans of action and milestones are required for federal organizations, other types of organizations can help reduce risk by documenting and tracking planned remediations. Specific guidance on plans of action and milestones at the system level is provided in CA-5.


## 4. System Inventory

OMB Circular A-130 (see Appendix B) provides guidance on developing systems inventories and associated reporting requirements. System inventory refers to an organization-wide inventory of systems, not system components as described in CM-8.


### 4.1 PII

An inventory of systems, applications, and projects that process personally identifiable information supports the mapping of data actions, providing individuals with privacy notices, maintaining accurate personally identifiable information, and limiting the processing of personally identifiable information when such information is not needed for operational purposes. Organizations may use this inventory to ensure that systems only process the personally identifiable information for authorized purposes and that this processing is still relevant and necessary for the purpose specified therein.


## 5. Measures of Performance

Measures of performance are outcome-based metrics used by an organization to measure the effectiveness or efficiency of the information security and privacy programs and the controls employed in support of the program. To facilitate security and privacy risk management, organizations consider aligning measures of performance with the organizational risk tolerance as defined in the risk management strategy.


## 6. Enterprise Architecture

The integration of security and privacy requirements and controls into the enterprise architecture helps to ensure that security and privacy considerations are addressed throughout the system development life cycle and are explicitly related to the organization’s mission and business processes. The process of security and privacy requirements integration also embeds into the enterprise architecture and the organization’s security and privacy architectures consistent with the organizational risk management strategy. For PM-7, security and privacy architectures are developed at a system-of-systems level, representing all organizational systems. For PL-8, the security and privacy architectures are developed at a level that represents an individual system. The system-level architectures are consistent with the security and privacy architectures defined for the organization. Security and privacy requirements and control integration are most effectively accomplished through the rigorous application of the Risk Management Framework defined in NIST SP 800-37 and supporting security standards and guidelines.


## 7. Critical Infrastructure Plan

Protection strategies are based on the prioritization of critical assets and resources. The requirement and guidance for defining critical infrastructure and key resources and for preparing an associated critical infrastructure protection plan are found in applicable laws, executive orders, directives, policies, regulations, standards, and guidelines.


## 8. Risk Management Strategy

An organization-wide risk management strategy includes an expression of the security and privacy risk tolerance for the organization, security and privacy risk mitigation strategies, acceptable risk assessment methodologies, a process for evaluating security and privacy risk across the organization with respect to the organization’s risk tolerance, and approaches for monitoring risk over time. The senior accountable official for risk management (agency head or designated official) aligns information security management processes with strategic, operational, and budgetary planning processes. The risk executive function, led by the senior accountable official for risk management, can facilitate consistent application of the risk management strategy organization-wide. The risk management strategy can be informed by security and privacy risk-related inputs from other sources, both internal and external to the organization, to ensure that the strategy is broad-based and comprehensive. The supply chain risk management strategy described in PM-30 can also provide useful inputs to the organization-wide risk management strategy.


## 9. Authorization Process

> [!IMPORTANT]
> <mark style="background-color: #fff9c4; color: #b71c1c; font-weight: bold; padding: 2px 6px; border-radius: 4px;">⚠️ RMF TEAM ACTION REQUIRED: Verify and update operational contact/procedure details in this section.</mark>
> Authorization processes for organizational systems and environments of operation require the implementation of an organization-wide risk management process and associated security and privacy standards and guidelines. Specific roles for risk management processes include a risk executive (function) and designated authorizing officials for each organizational system and common control provider. The authorization processes for the organization are integrated with continuous monitoring processes to facilitate ongoing understanding and acceptance of security and privacy risks to organizational operations, organizational assets, individuals, other organizations, and the Nation.


## 10. Mission and Business Process Definition

Protection needs are technology-independent capabilities that are required to counter threats to organizations, individuals, systems, and the Nation through the compromise of information (i.e., loss of confidentiality, integrity, availability, or privacy). Information protection and personally identifiable information processing needs are derived from the mission and business needs defined by organizational stakeholders, the mission and business processes designed to meet those needs, and the organizational risk management strategy. Information protection and personally identifiable information processing needs determine the required controls for the organization and the systems. Inherent to defining protection and personally identifiable information processing needs is an understanding of the adverse impact that could result if a compromise or breach of information occurs. The categorization process is used to make such potential impact determinations. Privacy risks to individuals can arise from the compromise of personally identifiable information, but they can also arise as unintended consequences or a byproduct of the processing of personally identifiable information at any stage of the information life cycle. Privacy risk assessments are used to prioritize the risks that are created for individuals from system processing of personally identifiable information. These risk assessments enable the selection of the required privacy controls for the organization and systems. Mission and business process definitions and the associated protection requirements are documented in accordance with organizational policies and procedures.


## 11. Security and Privacy Workforce

> [!IMPORTANT]
> <mark style="background-color: #fff9c4; color: #b71c1c; font-weight: bold; padding: 2px 6px; border-radius: 4px;">⚠️ RMF TEAM ACTION REQUIRED: Verify and update operational contact/procedure details in this section.</mark>
> Security and privacy workforce development and improvement programs include defining the knowledge, skills, and abilities needed to perform security and privacy duties and tasks; developing role-based training programs for individuals assigned security and privacy roles and responsibilities; and providing standards and guidelines for measuring and building individual qualifications for incumbents and applicants for security- and privacy-related positions. Such workforce development and improvement programs can also include security and privacy career paths to encourage security and privacy professionals to advance in the field and fill positions with greater responsibility. The programs encourage organizations to fill security- and privacy-related positions with qualified personnel. Security and privacy workforce development and improvement programs are complementary to organizational security awareness and training programs and focus on developing and institutionalizing the core security and privacy capabilities of personnel needed to protect organizational operations, assets, and individuals.


## 12. Testing, Training, and Monitoring

A process for organization-wide security and privacy testing, training, and monitoring helps ensure that organizations provide oversight for testing, training, and monitoring activities and that those activities are coordinated. With the growing importance of continuous monitoring programs, the implementation of information security and privacy across the three levels of the risk management hierarchy and the widespread use of common controls, organizations coordinate and consolidate the testing and monitoring activities that are routinely conducted as part of ongoing assessments supporting a variety of controls. Security and privacy training activities, while focused on individual systems and specific roles, require coordination across all organizational elements. Testing, training, and monitoring plans and activities are informed by current threat and vulnerability assessments.


## 13. Protecting CUI on External Systems

Controlled unclassified information is defined by the National Archives and Records Administration along with the safeguarding and dissemination requirements for such information and is codified in 32 CFR Part 2002 and, specifically for systems external to the federal organization, 32 CFR 2002.14h. The policy prescribes the specific use and conditions to be implemented in accordance with organizational procedures, including via its contracting processes.


## 14. Privacy Program Plan

A privacy program plan is a formal document that provides an overview of an organization’s privacy program, including a description of the structure of the privacy program, the resources dedicated to the privacy program, the role of the senior agency official for privacy and other privacy officials and staff, the strategic goals and objectives of the privacy program, and the program management controls and common controls in place or planned for meeting applicable privacy requirements and managing privacy risks. Privacy program plans can be represented in single documents or compilations of documents.

The senior agency official for privacy is responsible for designating which privacy controls the organization will treat as program management, common, system-specific, and hybrid controls. Privacy program plans provide sufficient information about the privacy program management and common controls (including the specification of parameters and assignment and selection operations explicitly or by reference) to enable control implementations that are unambiguously compliant with the intent of the plans and a determination of the risk incurred if the plans are implemented as intended.

Program management controls are generally implemented at the organization level and are essential for managing the organization’s privacy program. Program management controls are distinct from common, system-specific, and hybrid controls because program management controls are independent of any particular information system. Together, the privacy plans for individual systems and the organization-wide privacy program plan provide complete coverage for the privacy controls employed within the organization.

Common controls are documented in an appendix to the organization’s privacy program plan unless the controls are included in a separate privacy plan for a system. The organization-wide privacy program plan indicates which separate privacy plans contain descriptions of privacy controls.


## 15. Privacy Program Leadership Role

The privacy officer is an organizational official. For federal agencies—as defined by applicable laws, executive orders, directives, regulations, policies, standards, and guidelines—this official is designated as the senior agency official for privacy. Organizations may also refer to this official as the chief privacy officer. The senior agency official for privacy also has roles on the data management board (see PM-23) and the data integrity board (see PM-24).


## 16. Dissemination of Privacy Program Information

> [!IMPORTANT]
> <mark style="background-color: #fff9c4; color: #b71c1c; font-weight: bold; padding: 2px 6px; border-radius: 4px;">⚠️ RMF TEAM ACTION REQUIRED: Verify and update operational contact/procedure details in this section.</mark>
> For federal agencies, the webpage is located at www.[agency].gov/privacy. Federal agencies include public privacy impact assessments, system of records notices, computer matching notices and agreements, Privacy Act (see Appendix B) exemption and implementation rules, privacy reports, privacy policies, instructions for individuals making an access or amendment request, email addresses for questions/complaints, blogs, and periodic publications.


### 16.1 Privacy Policies on Websites, Applications, and Digital Services

Organizations post privacy policies on all external-facing websites, mobile applications, and other digital services. Organizations post a link to the relevant privacy policy on any known, major entry points to the website, application, or digital service. In addition, organizations provide a link to the privacy policy on any webpage that collects personally identifiable information. Organizations may be subject to applicable laws, executive orders, directives, regulations, or policies that require the provision of specific information to the public. Organizational personnel consult with the senior agency official for privacy and legal counsel regarding such requirements.


## 17. PII Quality Management

Personally identifiable information quality management includes steps that organizations take to confirm the accuracy and relevance of personally identifiable information throughout the information life cycle. The information life cycle includes the creation, collection, use, processing, storage, maintenance, dissemination, disclosure, and disposition of personally identifiable information. Organizational policies and procedures for personally identifiable information quality management are important because inaccurate or outdated personally identifiable information maintained by organizations may cause problems for individuals. Organizations consider the quality of personally identifiable information involved in business functions where inaccurate information may result in adverse decisions or the denial of benefits and services, or the disclosure of the information may cause stigmatization. Correct information, in certain circumstances, can cause problems for individuals that outweigh the benefits of organizations maintaining the information. Organizations consider creating policies and procedures for the removal of such information.

The senior agency official for privacy ensures that practical means and mechanisms exist and are accessible for individuals or their authorized representatives to seek the correction or deletion of personally identifiable information. Processes for correcting or deleting data are clearly defined and publicly available. Organizations use discretion in determining whether data is to be deleted or corrected based on the scope of requests, the changes sought, and the impact of the changes. Additionally, processes include the provision of responses to individuals of decisions to deny requests for correction or deletion. The responses include the reasons for the decisions, a means to record individual objections to the decisions, and a means of requesting reviews of the initial determinations.

Organizations notify individuals or their designated representatives when their personally identifiable information is corrected or deleted to provide transparency and confirm the completed action. Due to the complexity of data flows and storage, other entities may need to be informed of the correction or deletion. Notice supports the consistent correction and deletion of personally identifiable information across the data ecosystem.


## 18. Data Governance Body

A Data Governance Body can help ensure that the organization has coherent policies and the ability to balance the utility of data with security and privacy requirements. The Data Governance Body establishes policies, procedures, and standards that facilitate data governance so that data, including personally identifiable information, is effectively managed and maintained in accordance with applicable laws, executive orders, directives, regulations, policies, standards, and guidance. Responsibilities can include developing and implementing guidelines that support data modeling, quality, integrity, and the de-identification needs of personally identifiable information across the information life cycle as well as reviewing and approving applications to release data outside of the organization, archiving the applications and the released data, and performing post-release monitoring to ensure that the assumptions made as part of the data release continue to be valid. Members include the chief information officer, senior agency information security officer, and senior agency official for privacy. Federal agencies are required to establish a Data Governance Body with specific roles and responsibilities in accordance with the Foundations for Evidence-Based Policymaking Act of 2018 and policies set forth under OMB Memorandum M-19-23 (both listed in Appendix B).


## 19. Data Integrity Board

> [!IMPORTANT]
> <mark style="background-color: #fff9c4; color: #b71c1c; font-weight: bold; padding: 2px 6px; border-radius: 4px;">⚠️ RMF TEAM ACTION REQUIRED: Verify and update operational contact/procedure details in this section.</mark>
> A Data Integrity Board is the board of senior officials designated by the head of a federal agency and is responsible for, among other things, reviewing the agency’s proposals to conduct or participate in a matching program and conducting an annual review of all matching programs in which the agency has participated. As a general matter, a matching program is a computerized comparison of records from two or more automated Privacy Act systems of records or an automated system of records and automated records maintained by a non-federal agency (or agent thereof). A matching program either pertains to Federal benefit programs or Federal personnel or payroll records. At a minimum, the Data Integrity Board includes the Inspector General of the agency, if any, and the senior agency official for privacy.


## 20. Minimization of PII Used in Testing, Training, and Research

The use of personally identifiable information in testing, research, and training increases the risk of unauthorized disclosure or misuse of such information. Organizations consult with the senior agency official for privacy and/or legal counsel to ensure that the use of personally identifiable information in testing, training, and research is compatible with the original purpose for which it was collected. When possible, organizations use placeholder data to avoid exposure of personally identifiable information when conducting testing, training, and research.


## 21. Complaint Management

> [!IMPORTANT]
> <mark style="background-color: #fff9c4; color: #b71c1c; font-weight: bold; padding: 2px 6px; border-radius: 4px;">⚠️ RMF TEAM ACTION REQUIRED: Verify and update operational contact/procedure details in this section.</mark>
> Complaints, concerns, and questions from individuals can serve as valuable sources of input to organizations and ultimately improve operational models, uses of technology, data collection practices, and controls. Mechanisms that can be used by the public include telephone hotline, email, or web-based forms. The information necessary for successfully filing complaints includes contact information for the senior agency official for privacy or other official designated to receive complaints. Privacy complaints may also include personally identifiable information which is handled in accordance with relevant policies and processes.


## 22. Privacy Reporting

Through internal and external reporting, organizations promote accountability and transparency in organizational privacy operations. Reporting can also help organizations to determine progress in meeting privacy compliance requirements and privacy controls, compare performance across the federal government, discover vulnerabilities, identify gaps in policy and implementation, and identify models for success. For federal agencies, privacy reports include annual senior agency official for privacy reports to OMB, reports to Congress required by Implementing Regulations of the 9/11 Commission Act, and other public reports required by law, regulation, or policy, including internal policies of organizations. The senior agency official for privacy consults with legal counsel, where appropriate, to ensure that organizations meet all applicable privacy reporting requirements.


## 23. Risk Framing

> [!IMPORTANT]
> <mark style="background-color: #fff9c4; color: #b71c1c; font-weight: bold; padding: 2px 6px; border-radius: 4px;">⚠️ RMF TEAM ACTION REQUIRED: Verify and update operational contact/procedure details in this section.</mark>
> Risk framing is most effective when conducted at the organization level and in consultation with stakeholders throughout the organization including mission, business, and system owners. The assumptions, constraints, risk tolerance, priorities, and trade-offs identified as part of the risk framing process inform the risk management strategy, which in turn informs the conduct of risk assessment, risk response, and risk monitoring activities. Risk framing results are shared with organizational personnel, including mission and business owners, information owners or stewards, system owners, authorizing officials, senior agency information security officer, senior agency official for privacy, and senior accountable official for risk management.


## 24. Risk Management Program Leadership Roles

The senior accountable official for risk management leads the risk executive (function) in organization-wide risk management activities.


## 25. Supply Chain Risk Management Strategy

An organization-wide supply chain risk management strategy includes an unambiguous expression of the supply chain risk appetite and tolerance for the organization, acceptable supply chain risk mitigation strategies or controls, a process for consistently evaluating and monitoring supply chain risk, approaches for implementing and communicating the supply chain risk management strategy, and the associated roles and responsibilities. Supply chain risk management includes considerations of the security and privacy risks associated with the development, acquisition, maintenance, and disposal of systems, system components, and system services. The supply chain risk management strategy can be incorporated into the organization’s overarching risk management strategy and can guide and inform supply chain policies and system-level supply chain risk management plans. In addition, the use of a risk executive function can facilitate a consistent, organization-wide application of the supply chain risk management strategy. The supply chain risk management strategy is implemented at the organization and mission/business levels, whereas the supply chain risk management plan (see SR-2) is implemented at the system level.


## 26. Continuous Monitoring Strategy

Continuous monitoring at the organization level facilitates ongoing awareness of the security and privacy posture across the organization to support organizational risk management decisions. The terms “continuous” and “ongoing” imply that organizations assess and monitor their controls and risks at a frequency sufficient to support risk-based decisions. Different types of controls may require different monitoring frequencies. The results of continuous monitoring guide and inform risk response actions by organizations. Continuous monitoring programs allow organizations to maintain the authorizations of systems and common controls in highly dynamic environments of operation with changing mission and business needs, threats, vulnerabilities, and technologies. Having access to security- and privacy-related information on a continuing basis through reports and dashboards gives organizational officials the capability to make effective, timely, and informed risk management decisions, including ongoing authorization decisions. To further facilitate security and privacy risk management, organizations consider aligning organization-defined monitoring metrics with organizational risk tolerance as defined in the risk management strategy. Monitoring requirements, including the need for monitoring, may be referenced in other controls and control enhancements such as, AC-2g, AC-2(7), AC-2(12)(a), AC-2(7)(b), AC-2(7)(c), AC-17(1), AT-4a, AU-13, AU-13(1), AU-13(2), CA-7, CM-3f, CM-6d, CM-11c, IR-5, MA-2b, MA-3a, MA-4a, PE-3d, PE-6, PE-14b, PE-16, PE-20, PM-6, PM-23, PS-7e, SA-9c, SC-5(3)(b), SC-7a, SC-7(24)(b), SC-18b, SC-43b, SI-4.



## Appendix A – Detailed Compliance Matrix

The following table provides detailed traceability between the policy implementation statements in this document, the authoritative NIST SP 800-53 Rev. 5 control requirements, DoD CCIs, and the technical/governance enforcement mechanisms active across {{ SYSTEM_NAME }}.


| CTRL ID | CTRLTITLE | REQUIRED eMASS STANDARD | DOCREF | ENFORCEMENT MECHANISM |
| :--- | :--- | :--- | :--- | :--- |
| PM-01 | Information Security Program Plan | Develops, approves, disseminates, and protects organization-wide program plan; reviews annually and upon significant threat/technology changes or major incidents. (CCI-000073, CCI-000074, CCI-000075, CCI-000076, CCI-001680, CCI-002984, CCI-002985, CCI-002986, CCI-002987, CCI-002988, CCI-002989, CCI-002990, CCI-004312, CCI-004313) | Section 1 | Formal AO approval workflow; eMASS System ID {{ RMF_PACKAGE_ID }} governance publication; RBAC and {{ IDENTITY_PROVIDER }} with {{ MFA_MECHANISM }} access controls; Cloud KMS FIPS 140-3 CMEK plan encryption. |
| PM-02 | Information Security Program Leadership | Appoints a Senior Information Security Officer / ISSM with authority and resources to coordinate and maintain the security program. (CCI-000078) | Section 1 | Official {{ ORGANIZATION }} appointment memorandum designating {{ ISSM_NAME }} as ISSM; governance integration with AO, CTO, SO, and ISSO. |
| PM-03 | Information Security and Privacy Resources | Includes security and privacy resources in capital planning / POM budget requests; prepares required documentation; makes funds available for expenditure. (CCI-000080, CCI-000141, CCI-004314, CCI-004315, CCI-004316, CCI-004317, CCI-004318) | Section 2 | Formal {{ ORGANIZATION }} capital planning budget submissions funding {{ INTERCONNECT_TYPE }}, Cloud KMS HSM, Secret Manager, VPC-SC, DevSecOps pipelines, and security operations support. |
| PM-04 | Plan of Action and Milestones Process | Implements process to develop, maintain, review, and report security, privacy, and SCRM POA&Ms; ensures consistency with risk strategy. (CCI-000142, CCI-000170, CCI-002991, CCI-002993, CCI-004319, CCI-004320, CCI-004321, CCI-004322, CCI-004323, CCI-004324, CCI-004325, CCI-004326, CCI-004327) | Section 3 | Centralized eMASS POA&M tracking; quarterly review cadence with ISSM/SO; automated ingestion of vulnerability and static code scan findings. |
| PM-05 | System Inventory | Develops and maintains inventory of organizational systems; updates at least annually or when systems are added/removed. (CCI-004328, CCI-004329, CCI-004330) | Section 4 | eMASS System ID {{ RMF_PACKAGE_ID }} tracking all organizational cloud projects, landing zones, and external network spoke connections. |
| PM-05(01) | System Inventory: Inventory of Personally Identifiable Information | Establishes and maintains inventory of systems processing PII; updates continuously. (CCI-004331, CCI-004332, CCI-004333, CCI-004334) | Section 4 | Automated SCIM identity directory synchronization, Privacy Impact Assessments (PIAs), and continuous tracking of administrative access logs in BigQuery. |
| PM-06 | Measures of Performance | Develops, monitors, and reports outcome-based security and privacy measures of performance. (CCI-000209, CCI-000210, CCI-000211, CCI-004335, CCI-004336, CCI-004337) | Section 5 | Real-time Cloud Run telemetry streaming to BigQuery and executive Grafana dashboards tracking SLA availability (≥99.99%), BGP convergence, and encryption status. |
| PM-07 | Enterprise Architecture | Develops and maintains enterprise architecture integrating security and privacy requirements. (CCI-000212, CCI-004338, CCI-004339, CCI-004340) | Section 6 | Enterprise cloud landing zone integration; multi-project topology decoupling networking, compute workloads, telemetry pipelines, and machine identities. |
| PM-07(01) | Enterprise Architecture: Offloading | Offloads non-essential functions and services not directly related to mission-critical transport (office automation, email). (CCI-004341, CCI-004342) | Section 6 | Offloading non-essential services to enterprise cloud providers; restricting {{ SYSTEM_NAME }} VPCs to authorized workload pipelines via Organization Policies. |
| PM-08 | Critical Infrastructure Plan | Addresses security and privacy issues in critical infrastructure and key resources protection plans. (CCI-000216, CCI-001640, CCI-004343, CCI-004344) | Section 7 | {{ SYSTEM_NAME }} Critical Infrastructure Protection Plan; physical path redundancy across geographically distributed enterprise colocation and cloud edge facilities. |
| PM-09 | Risk Management Strategy | Develops, implements, and reviews risk management strategy at least annually (updated at least within 10 years). (CCI-000227, CCI-000228, CCI-002994, CCI-002995, CCI-004345) | Section 8 | Enterprise RMF strategy governed by {{ ORGANIZATION }} and eMASS workflows; annual strategy review cadence. |
| PM-10 | Authorization Process | Manages security/privacy state via RMF authorization processes integrated into enterprise risk management. (CCI-000233, CCI-000234, CCI-004346, CCI-004347) | Section 9 | Integrated eMASS authorization workflows, AO approval gates, and continuous monitoring feeds per DoDI 8510.01. |
| PM-11 | Mission and Business Process Definition | Defines mission/business processes considering security/privacy; reviews and revises at least annually. (CCI-000235, CCI-000236, CCI-004348, CCI-004349, CCI-004350, CCI-004351) | Section 10 | {{ SYSTEM_NAME }} NaaS operational architecture specifications; annual review cadence by {{ ORGANIZATION }} System Owner and engineering leads. |
| PM-12 | Insider Threat Program | Implements insider threat program with cross-discipline incident handling team. (CCI-002996) | Section 10 | Integration with {{ ORGANIZATION }} Insider Threat Program; centralized Cloud Audit Log routing to BigQuery and DISA CSSP for behavioral anomaly detection. |
| PM-13 | Security and Privacy Workforce | Establishes security and privacy workforce development and improvement program. (CCI-002997, CCI-004352) | Section 11 | DoD 8140 / 8570.01-M baseline certification tracking (Security+, CISSP) and mandatory annual role-based training for all {{ SYSTEM_NAME }} engineers. |
| PM-14 | Testing, Training, and Monitoring | Develops, maintains, executes, and reviews testing, training, and monitoring plans for consistency with risk strategy. (CCI-002998 through CCI-003009, CCI-004353 through CCI-004361) | Section 12 | Automated CI/CD DevSecOps scanner suite (Semgrep, Checkov, tfsec), annual SCA assessments, and continuous telemetry monitoring reviewed annually. |
| PM-15 | Contacts with Selected Groups and Associations | Establishes and institutionalizes contact with security/privacy groups to maintain currency and share threat information. (CCI-003010, CCI-003011, CCI-003012, CCI-004362, CCI-004363, CCI-004364) | Section 12 | Institutionalized liaison with DoD Cybersecurity Forum, DISA, USCYBERCOM, NSA, and NIST. |
| PM-16 | Threat Awareness Program | Implements threat awareness program with cross-organization information sharing. (CCI-003013) | Section 12 | Automated threat data feeds from {{ CSSP_PROVIDER }} CSSP, {{ THREAT_DETECTION_ENGINE }}, and USCYBERCOM alerts. |
| PM-16(01) | Threat Awareness Program: Automated Threat Intelligence Sharing | Employs automated means to share threat intelligence information. (CCI-004365) | Section 12 | Automated API-driven threat intelligence ingestion and dynamic firewall rule deployment via {{ THREAT_DETECTION_ENGINE }} and {{ TELEMETRY_PIPELINE }}. |
| PM-17 | Protecting CUI on External Systems | Establishes and reviews annually policy/procedures for protecting CUI on external systems. (CCI-004366, CCI-004367, CCI-004368, CCI-004369, CCI-004370, CCI-004371) | Section 13 | Mandated FIPS 140-3 encryption (Layer 2/3 transport encryption) on all external transit links; annual policy review cadence. |
| PM-18 | Privacy Program Plan | Develops, approves, disseminates, and updates privacy program plan at least annually. (CCI-004372 through CCI-004389) | Section 14 | Formal {{ ORGANIZATION }} Privacy Program Plan overseen by SAOP; annual review cadence published via eMASS. |
| PM-19 | Privacy Program Leadership Role | Appoints Senior Agency Official for Privacy (SAOP) with authority and resources to manage privacy risks. (CCI-004390, CCI-004391, CCI-004392, CCI-004393) | Section 15 | {{ ORGANIZATION }} SAOP formal appointment memorandum with executive oversight across enterprise data systems. |
| PM-20 | Dissemination of Privacy Program Information | Maintains central resource webpage with public privacy information and communication mechanisms. (CCI-004394, CCI-004395, CCI-004396, CCI-004397, CCI-004398) | Section 16 | Publicly accessible {{ ORGANIZATION }} privacy portal hosting PIAs, SORNs, and SAOP feedback channels. |
| PM-20(01) | Dissemination of Privacy Program Information: Privacy Policies on Websites | Posts clear, date-stamped privacy policies on public digital services. (CCI-004399 through CCI-004403) | Section 16 | Published plain-language digital privacy statements on public interfaces with automated timestamping. |
| PM-21 | Accounting of Disclosures | Maintains accurate accounting of PII disclosures; retains for at least 5 years or life of record. (CCI-004404 through CCI-004411) | Section 16 | GCP Cloud Audit Log immutable retention in BigQuery datasets for at least 5 years with individual disclosure access. |
| PM-22 | Personally Identifiable Information Quality Management | Establishes policies/procedures to review, correct, or delete inaccurate PII throughout life cycle. (CCI-004412 through CCI-004419) | Section 17 | Standardized PII correction/appeal workflows managed by the Privacy Officer and SAOP. |
| PM-23 | Data Governance Body | Establishes Data Governance Body (minimally SAISO and SAOP) to enforce policies for data management and protection per NIST SP 800-193. (CCI-004420, CCI-004421, CCI-004422) | Section 18 | {{ ORGANIZATION }} Data Governance Board charters enforcing data lifecycle, BigQuery dataset permissions, and schema validations. |
| PM-24 | Data Integrity Board | Establishes Data Integrity Board to conduct annual reviews of matching programs. (CCI-004423, CCI-004424) | Section 19 | Enterprise Data Integrity Board annual matching program review compliance. |
| PM-25 | Minimization of PII in Testing, Training, and Research | Prohibits live PII in testing/training; authorizes exceptions; reviews policies at least annually. (CCI-004425 through CCI-004434) | Section 20 | Multi-environment project segregation (development, test, and production); synthetic test data pipelines; annual policy review cadence. |
| PM-26 | Complaint Management | Implements process for security/privacy complaints; acknowledges within 10 business days; resolves within 30 business days. (CCI-004435 through CCI-004445) | Section 21 | Formal incident/complaint portal with automated tracking ensuring 10-day acknowledgment and 30-day resolution per CJCSM 6510.01B. |
| PM-27 | Privacy Reporting | Develops annual FISMA privacy reports; disseminates to SAOP, CIO, AO, OMB, and DoD CIO; reviews annually. (CCI-004446 through CCI-004453) | Section 22 | Automated FISMA privacy reporting workflows submitted annually to oversight authorities. |
| PM-28 | Risk Framing | Documents assumptions, constraints, risk tolerance, and priorities; distributes to risk leadership; reviews at least annually. (CCI-004454 through CCI-004461) | Section 23 | {{ SYSTEM_NAME }} Risk Framing document; annual review cadence; distribution to AO, SO, ISSM, and ISSO per DoDI 8510.01. |
| PM-29 | Risk Management Program Leadership Roles | Appoints Senior Accountable Official for Risk Management; establishes enterprise Risk Executive function. (CCI-004462 through CCI-004465) | Section 24 | {{ ORGANIZATION }} Risk Executive (function) integration ensuring consistent risk posture across DoD Cloud / GCP cloud enclaves. |
| PM-30 | Supply Chain Risk Management Strategy | Develops, implements, and reviews SCRM strategy across system lifecycle at least annually. (CCI-004466 through CCI-004472) | Section 25 | Enterprise SCRM policy; annual review cadence; mandatory vendor vetting against NDAA Section 889. |
| PM-30(01) | Supply Chain Risk Management Strategy: Supplier Reviews | Identifies, prioritizes, and assesses suppliers of critical or mission-essential technologies. (CCI-005150) | Section 25 | Formal supplier vetting for hardware, cloud infrastructure, and network appliance providers; automated CI/CD SBOM generation and dependency scanning. |
| PM-31 | Continuous Monitoring Strategy | Develops and implements ISCM strategy; monitors metrics in near real-time; assesses controls annually; reports quarterly to CIO, SAOP, and risk leadership. (CCI-004473 through CCI-004495) | Section 26 | Real-time Cloud Run / BigQuery / Grafana telemetry monitoring; annual SCA control assessments; quarterly executive reporting to {{ ORGANIZATION }} CIO, SAOP, and executive leadership. |
| PM-32 | Purposing | Analyzes all mission-essential systems and components to ensure usage consistent with intended purpose. (CCI-004496, CCI-004497) | Section 26 | Routine analysis of all {{ SYSTEM_NAME }} transport nodes and telemetry pipelines; GCP Organization Policies (gcp.restrictServiceUsage) and VPC-SC perimeter enforcement. |



## Appendix B – Statutory Authorities, Laws, and Regulations (Google Appendix L)

{{ ORGANIZATION }} operates {{ SYSTEM_NAME }} in strict compliance with applicable federal statutes, executive directives, and DoD regulations documented in Google Services Appendix L:

| Regulatory Instrument | Title / Description | Governing Compliance Baseline |
| :--- | :--- | :--- |
| **Public Law 107-347** | Federal Information Security Modernization Act (FISMA 2014) | Mandatory Information Security Management |
| **Public Law 93-579** | Privacy Act of 1974 | Federal Privacy Protection, Systems of Records, and Matching Programs |
| **Public Law 115-435** | Foundations for Evidence-Based Policymaking Act of 2018 | Federal Data Governance Body and Data Management |
| **OMB Circular A-130** | Managing Information as a Strategic Resource | Federal Risk Management & Privacy Guidelines |
| **OMB Memorandum M-19-23** | Phase 1 Implementation of the Foundations for Evidence-Based Policymaking Act of 2018: Learning Agendas, Personnel, and Planning Guidance | Federal Data Governance Body Roles and Responsibilities |
| **Executive Order 14028** | Improving the Nation's Cybersecurity | Zero Trust Architecture, Software Supply Chain Security |
| **DoDI 8510.01** | Risk Management Framework (RMF) for DoD Information Technology | DoD IL5 System Authorization Framework |
| **DoD Cloud SRG** | DoD Cloud Computing Security Requirements Guide (IL5) | Defense Information Systems Agency (DISA) STIGs |
| **FIPS PUB 199 / 200** | Standards for Security Categorization & Minimum Security Requirements | {{ FIPS_199_CATEGORIZATION }} Baseline |
