# CA - Assessment Authorization and Monitoring Policy and Procedures

## Document Governance & Approval Baseline

| Governance Metric | Policy Standard & Specification |
| :--- | :--- |
| **Document Title** | Assessment Authorization and Monitoring Policy and Procedures |
| **NIST Control Family** | Assessment Authorization and Monitoring (CA) |
| **Primary NIST Benchmark** | NIST SP 800-37 Rev. 2 (RMF Framework), NIST SP 800-53A Rev. 5, NIST SP 800-137 |
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
> This document defines the enterprise security policy and implementation procedures for **Assessment Authorization and Monitoring** under **NIST SP 800-53 Rev. 5 (CA)**.
> Technical infrastructure controls are automatically provisioned and enforced via **{{ SYSTEM_NAME }}** Terraform blueprints.
> Operational rules or contact details requiring manual confirmation are highlighted with RMF Team Callouts.


## 1. Overview

This document establishes a common policy for the effective implementation of selected NIST SP 800-53rev5 “Security and Privacy Controls for Federal Information Systems and Organizations” controls and control enhancements in the Assessment, Authorization, and Monitoring (CA) family to be applied, as required. The risk management strategy is an important factor in establishing such policies and procedures, as they contribute to security and privacy assurance. These policies reflect applicable federal laws, Executive Orders, directives, regulations, policies, standards, and guidance. The Security Assessment, Authorization, and Monitoring control policies are high-level requirements that supplement the execution of cybersecurity assessments, authorizations, continuous monitoring, plans of actions and milestones and system interconnections. The purpose of this document is the establishment of a common policy for the implementation of security controls to protect the confidentiality, integrity, and availability of the applicable systems and its information, and to manage information security risk across {{ ORGANIZATION }}.

This policy covers all {{ ORGANIZATION }} information and information systems to include those used, managed, or operated by a contractor, or other organizations on behalf of {{ ORGANIZATION }}. This policy applies to all {{ ORGANIZATION }} employees, contractors, and all other users of {{ ORGANIZATION }} information and information systems that support the operation and assets of {{ ORGANIZATION }}.

> [!IMPORTANT]
> [WARNING: RMF TEAM ACTION REQUIRED: Verify and update operational contact/procedure details in this section.]
> The {{ ORGANIZATION }} ISSM shall ensure this policy is reviewed and updated annually, or as needed, and disseminated to {{ ORGANIZATION }} System Administrators, Information System Security Officers, Program Managers, and any relevant stakeholders.

This document complies with the following requirements from NIST Special Publication 800-53 Revision 5, "Security and Privacy Controls for Federal Information Systems and Organizations". A detailed compliance matrix can be found in Appendix A, “Detailed Compliance Matrix”.


### 1.1 Policy and Procedures

{{ ORGANIZATION }} security assessments will be performed to ensure that information security is built into {{ SYSTEM_NAME }}; identify weaknesses and deficiencies; provide essential information needed to make risk-based decisions as part of security authorization processes; and ensure compliance to vulnerability mitigation procedures. {{ ORGANIZATION }} assess security controls as part of:

- initial and ongoing security authorizations;

- annual security assessments;

- continuous monitoring; and

- system life cycle activities.

{{ ORGANIZATION }} security assessment will be conducted no less than annually on selected implemented security controls and enhancements, as documented in the System Security Plan.

The {{ ORGANIZATION }} Security Assessment Plan (SAP) will address assessment planning; procedures addressing control assessments; control assessment plan; control assessment report; system security plan; privacy plan and identify the security controls and those control enhancements under assessment. The SAP shall be approved by the AO prior to conducting an assessment.

The SAP will define the scope of the assessment, and the assessment environment, team, roles, and responsibilities.

> [!IMPORTANT]
> [WARNING: RMF TEAM ACTION REQUIRED: Verify and update operational contact/procedure details in this section.]
> The {{ ORGANIZATION }} Security Assessment Report (SAR) will identify the evaluation status of all security controls, including the extent to which the controls are implemented correctly, operating as intended, producing the desired outcome with respect to meeting established security requirement, compliance/non-compliance statuses of all controls, and specific deficiencies for all non-compliant controls identified. The SAR will be provided directly to the system ISSM/ISSO and will be stored in {{ RMF_GOVERNANCE_SYSTEM }} as an artifact.


### 1.2 Independent Assessors

During RMF Step 4, “Assess Security Controls”, an independent Assessor is required to perform testing and conduct control assessments. While the program office or individual systems may fund the Validator, the Validator will not report directly to the program manager.


### 1.3 Specialized Assessments

> [!IMPORTANT]
> [WARNING: RMF TEAM ACTION REQUIRED: Verify and update operational specialized assessment frequencies and execution teams under NIST SP 800-53 Control CA-2(2).]

{{ ORGANIZATION }} conducts specialized assessments, to include:

- **Automated Container & Application Vulnerability Assessments**: Continuous automated static code analysis (SAST), software composition analysis (SCA), and container image vulnerability scanning integrated into CI/CD build pipelines and Google Cloud Container Analysis (`RA-5`, `CA-2(2)`).

- **Independent Third-Party Penetration Testing**: Annual external web application, API, and cloud infrastructure grey-box penetration testing conducted by an independent assessment team (3PAO / SCA-R) (`CA-8`).

- **Real-Time Security Instrumentation & Anomaly Analytics**: Continuous cloud platform event threat detection, behavioral anomaly tracking, and misconfiguration auditing performed via {{ THREAT_DETECTION_ENGINE }} and {{ TELEMETRY_PIPELINE }} (`CA-7`).

- **Data Loss Prevention (DLP) & Sensitive Data Assessments**: Periodic automated inspection of cloud storage buckets and BigQuery analytical datasets using Google Cloud Sensitive Data Protection (Cloud DLP) to verify proper classification and handling of PII/CUI.

These assessments improve the readiness by exercising organizational capabilities and indicating current levels of performance as a means of focusing actions to improve the security and privacy of {{ SYSTEM_NAME }}.


## 2. Information Exchange

This section applies to dedicated connections between information systems (i.e., system interconnections) and does not apply to transitory, user-controlled connections such as email and website browsing.

> [!IMPORTANT]
> [WARNING: RMF TEAM ACTION REQUIRED: Verify and update operational contact/procedure details in this section.]
> {{ ORGANIZATION }} carefully considers the risks that may be introduced when information systems are connected to other systems with different security requirements and security controls, both within {{ ORGANIZATION }} and external to {{ ORGANIZATION }}. If {{ ORGANIZATION }} has an interconnection to another system with the same authorizing official, it is recommended that the {{ ORGANIZATION }} develop an Interconnection Security Agreement. Additionally, the {{ ORGANIZATION }} will describe the interface characteristics between those interconnecting systems in the System Security Plan (SSP). If {{ ORGANIZATION }} has an interconnection to another system with a different authorizing official, an Interconnection Security Agreement (ISA) is required.

All ISAs will be reviewed and updated at least annually.



### 2.1 Google Cloud Platform (GCP) Inherited Controls & Shared Responsibility Boundary

- **Google Inherited Controls**: Google Services maintains a FedRAMP High JAB Authorization to Operate (ATO) and FedRAMP High / DoD Impact Level 5 (IL5) Provisional Authorization (PA) (`CA-2`, `CA-3`). Google performs continuous monitoring of physical infrastructure, hypervisor security, and core CSP platform components (`CA-7`).
- **Customer Implementation Responsibilities**: {{ ORGANIZATION }} is responsible for maintaining the system's System Security Plan (SSP) (`CA-3`), conducting annual Security Control Traceability Matrix (SCTM) reviews, configuring {{ THREAT_DETECTION_ENGINE }} and continuous monitoring pipelines (`CA-7`), and tracking Plan of Action and Milestones (POA&M) remediation (`CA-5`).

## 3. Plan of Action and Milestones

The Plan of Action and Milestones (POA&M) is a key document in the {{ ORGANIZATION }} information security program and is subject to federal reporting requirements established by the Office of Management and Budget (OMB).

All {{ ORGANIZATION }} systems shall maintain a POA&M in {{ RMF_GOVERNANCE_SYSTEM }} which will be updated at a frequency of at least every 90 days.  All POA&M items should include realistic milestones for remediation to include a realistic closure date based on risk the vulnerability brings to the system.

With the increasing emphasis on organization-wide risk management across all three tiers in the risk management hierarchy (i.e., organization, mission/business process, and information system), organizations view POA&Ms from an organizational perspective, prioritizing risk response actions and ensuring consistency with the goals and objectives of the organization. POA&M updates are based on findings from security control assessments and continuous monitoring activities.

The following process is used by {{ ORGANIZATION }} to ensure compliance with POA&M requirements:

1.The POA&M is required and will be maintained in {{ RMF_GOVERNANCE_SYSTEM }};

2.The POA&M will be updated based on control assessment, independent audits, or continuous monitoring activities. At a minimum, the {{ RMF_GOVERNANCE_SYSTEM }} POA&M will be updated every 90 days;

3.All ongoing findings in the POA&M will contain an adequate risk mitigation;

4.POA&M reporting will be executed in accordance with higher-level guidance; and

5.All {{ ORGANIZATION }} stakeholders will review the POA&M annually to ensure consistency.


## 4. Authorization

> [!IMPORTANT]
> [WARNING: RMF TEAM ACTION REQUIRED: Verify and update operational contact/procedure details in this section.]
> Security authorizations are official management decisions, conveyed through authorization decision documents, by senior organizational officials or executives (i.e. Authorizing Official) to authorize operation of information systems and to explicitly accept the risk to organizational operations and assets, individuals, other organizations, and the Nation based on the implementation of agreed-upon security controls.

> [!IMPORTANT]
> [WARNING: RMF TEAM ACTION REQUIRED: Verify and update operational contact/procedure details in this section.]
> {{ ORGANIZATION }} will use the {{ AO_NAME }} ({{ AO_TITLE }})

{{ ORGANIZATION }} PMO will be the point of contact for all communication with the AO office.


## 5. Continuous Monitoring

Continuous monitoring at a system level facilitates ongoing awareness of the system security and privacy posture to support organizational risk management decisions. {{ ORGANIZATION }} will continuously assess and monitor controls and risks to support risk-based decisions.

All {{ ORGANIZATION }} systems are required to document a continuous monitoring plan and provide that strategy within {{ RMF_GOVERNANCE_SYSTEM }}.  The continuous monitoring plan allows {{ ORGANIZATION }} to maintain the authorization of {{ SYSTEM_NAME }} in a highly dynamic environment of operation with changing mission and business needs, threats, vulnerabilities, and technologies.


### 5.1 Independent Assessment

Organizations maximize the value of control assessments by requiring that assessments be conducted by assessors with appropriate levels of independence. The level of required independence is based on organizational continuous monitoring strategies. Assessor independence provides a degree of impartiality to the monitoring process. To achieve such impartiality, assessors do not create a mutual or conflicting interest with the organizations where the assessments are being conducted, assess their own work, act as management or employees of the organizations they are serving, or place themselves in advocacy positions for the organizations acquiring their services.


### 5.2 Trend Analysis

{{ ORGANIZATION }} is responsible for implementing trend analysis to determine if control implementations, the frequency of continuous monitoring activities, and the types of activities used in the continuous monitoring process need to be modified. {{ ORGANIZATION }} is responsible for staying up to date on current threat information that addresses the types of events that are trending in the Federal Government to ensure the {{ SYSTEM_NAME }} is properly protected.


### 5.3 Risk Monitoring

{{ ORGANIZATION }} will ensure risk monitoring is part of the continuous monitoring plan. Effectiveness monitoring will be used to determine the ongoing effectiveness of the risk response measures; compliance monitoring will verify that the risk response measures are implemented; and change monitoring identifies the changes made to {{ SYSTEM_NAME }} that may impact the security and privacy risk.


### 5.4 Consistency Analysis

When new privacy and security controls are added to the system, the {{ ORGANIZATION }} is responsible for ensuring that all policies are up-to-date, and the controls work together in a consistent or coordinated manner. {{ ORGANIZATION }} is responsible for ensuring the security and privacy controls compliment each other, and not compete against each other, and also ensure there are no unintended vulnerabilities to the system that could be exploited by adversaries.

It is important to validate through testing, monitoring, and analysis, to ensure all controls are operating in a consistent, coordinated, non-interfering manner.


### 5.5 Automation Support for Monitoring

{{ ORGANIZATION }} implements {{ THREAT_DETECTION_ENGINE }}, {{ SIEM_TOOL }}, Cloud Asset Inventory, and automated {{ IAC_TOOL }} posture scans to help maintain the accuracy, currency, and availability of monitoring information on {{ SYSTEM_NAME }}.


## 6. Penetration Testing

The {{ ORGANIZATION }} shall conduct a penetration test on the {{ SYSTEM_NAME }} annually (every 365 days prior to ATO expiration). The {{ ORGANIZATION }} is responsible for employing an independent penetration testing team to perform penetration testing on the {{ SYSTEM_NAME }}.


## 7. Internal System Connections

Per NIST 800-53 Rev 5, Internal System Connections refer to connections between organizational systems and separate constituent system components (i.e., connections between components that are part of the same system) including components used for system development. Intra-system connections include connections with mobile devices, notebook and desktop computers, tablets, printers, copiers, facsimile machines, scanners, sensors, and servers.

{{ ORGANIZATION }} PMO requires documentation of their internal connections.  Securing these connections include: network segmentation, secure communication protocols, access control, data protection and monitoring and logging of all assets. The {{ SYSTEM_NAME }} internal connections will be documented on the {{ SYSTEM_NAME }} network diagram and each asset will be noted on the {{ SYSTEM_NAME }} hardware list.

Before establishing a new internal connection, the assets that are being connected will have any relevant STIG, patching and vulnerability scan applied.  Connection approval will be granted by following the {{ ORGANIZATION }} CCB process.



## Appendix A – Detailed Compliance Matrix

The following table provides detailed traceability between the policy implementation statements in this document, the authoritative NIST SP 800-53 Rev. 5 control requirements, DoD CCIs, and the technical/governance enforcement mechanisms active across {{ SYSTEM_NAME }}.


| CTRL ID | CTRLTITLE | REQUIRED eMASS STANDARD | DOCREF | ENFORCEMENT MECHANISM |
| :--- | :--- | :--- | :--- | :--- |
| CA-01 | Policy and Procedures | Develop, document, disseminate to all personnel, and review/update annually (or upon eMASS updates, baseline changes, or major incidents) CA policy and procedures. (CCIs: 000238, 000239, 000240, 000241, 000242, 000243, 000244, 001578, 002061, 002062, 003849, 003850, 003851, 003852, 003853, 003854, 003855, 003856, 003857, 003858) | Section 1 | Formal annual review workflow by {{ ORGANIZATION }} ISSM/SO/AO; eMASS repository publishing; incident-triggered updates. |
| CA-02 | Control Assessments | Assess security and privacy controls continuously via automated telemetry and at least annually via formal SAP/SAR workflows; report to ISSO/ISSM. (CCIs: 000246, 000247, 000248, 000251, 000252, 000253, 000254, 002070, 002071, 003859, 003860, 003861) | Section 1.1 | NIST SP 800-53A assessment procedures; SAR artifact upload to eMASS; continuous automated control testing. |
| CA-02(01) | Independent Assessors | Employ independent assessors (SCA-R / 3PAO) to conduct security control assessments without organizational conflicts of interest. (CCIs: 000255) | Section 1.1 | Formal SCA-R appointment by AO; third-party assessment contract execution; independent assessment reporting. |
| CA-02(02) | Specialized Assessments | Conduct specialized assessments annually (and unannounced), including in-depth monitoring, automated IaC scans, vulnerability scans, and red teaming. (CCIs: 000256, 001582, 002065) | Section 1.1 | {{ THREAT_DETECTION_ENGINE }}; {{ VULNERABILITY_SCANNER }}; CI/CD security scanners (Semgrep, Checkov, tfsec, Gitleaks); Container Analysis. |
| CA-03 | Information Exchange | Establish, document, and review annually ISAs, MOUs, MOAs, and SLAs for all external system interconnections. (CCIs: 000258, 000259, 002083, 002084, 003862, 003863) | Section 2 | Formal ISA/MOA review workflows; SSP interface documentation; PPSM registry compliance under DoDI 8551.01. |
| CA-03(06) | Transfer Authorizations | Verify and enforce formal transfer authorizations and valid ATOs prior to permitting interconnecting information flows. (CCIs: 003864) | Section 2 | BGP peering authorization gating; Cross-Cloud Interconnect provisioning approval; ATO validation in eMASS. |
| CA-05 | Plan of Action and Milestones | Maintain and update the system POA&M in eMASS as findings occur and at least every 90 days; conduct annual comprehensive reviews. (CCIs: 000264, 000265, 000266) | Section 3 | eMASS POA&M module; quarterly ISSM review workflows; automated vulnerability remediation milestone tracking. |
| CA-06 | Authorization | Obtain formal ATO from the {{ ORGANIZATION }} AO prior to operations; reauthorize at least every 3 years or upon significant architectural changes/breaches. (CCIs: 000270, 000271, 000272, 000273, 003868, 003869, 003870) | Section 4 | AO authorization decision documents; eMASS RMF package management; continuous ongoing authorization workflows. |
| CA-07 | Continuous Monitoring | Execute continuous monitoring of system metrics (real-time automated, monthly manual); assess controls annually; report status quarterly to AO/ISSM. (CCIs: 000274, 000279, 000280, 000281, 002087, 002088, 002090, 002091, 002092, 003873, 003874, 003875, 003876, 003877, 003878, 003879, 003880) | Section 5 | {{ THREAT_DETECTION_ENGINE }} dashboards; {{ SIEM_TOOL }} real-time event correlation; quarterly RMF status reports. |
| CA-07(01) | Independent Assessment | Incorporate independent assessors into the continuous monitoring process to evaluate ongoing control effectiveness. (CCIs: 000282) | Section 5 | SCA-R independent continuous monitoring evaluations; periodic external 3PAO control reviews. |
| CA-07(03) | Trend Analysis | Perform trend analysis on vulnerability metrics, attack patterns, and audit logs to update monitoring frequencies and defensive posture. (CCIs: 002086) | Section 5 | BigQuery Log Analytics trend queries; SIEM threat trending dashboards; ARCYBER threat intelligence feeds. |
| CA-07(04) | Risk Monitoring | Conduct continuous risk monitoring spanning control effectiveness, baseline compliance, and infrastructure change monitoring. (CCIs: 003881, 003882, 003883) | Section 5 | Real-time Cloud Asset Inventory drift tracking; automated Terraform plan security policy checks. |
| CA-07(05) | Consistency Analysis | Ensure security policies and implemented controls operate consistently without conflict using Inquire, Review, Observe, Inspect, Re-validate. (CCIs: 003884, 003885, 003886) | Section 5 | Formal SME consistency reviews; multi-control integration testing; automated policy conflict analysis. |
| CA-07(06) | Automation Support for Monitoring | Deploy automated mechanisms ({{ THREAT_DETECTION_ENGINE }}, {{ VULNERABILITY_SCANNER }}, {{ EDR_SOLUTION }}, Cloud Asset Inventory) to ensure monitoring accuracy and currency. (CCIs: 003887, 003888) | Section 5 | {{ THREAT_DETECTION_ENGINE }}; {{ VULNERABILITY_SCANNER }}; automated CI/CD posture scanners. |
| CA-09 | Internal System Connections | Authorize all internal connections between components; verify STIG/patching compliance; review monthly; terminate upon mission end. (CCIs: 002101, 002102, 002103, 002104, 002105, 003891, 003892, 003893, 003894, 003895) | Section 7 | {{ ORGANIZATION }} CCB approval workflow; Terraform VPC peering/Shared VPC subnet grants; monthly connection audits. |



## Appendix B – Continuous Monitoring Operational Cadence (Google Appendix N)

In accordance with NIST SP 800-137 and Google Services Appendix N (Continuous Monitoring Plan), {{ ORGANIZATION }} maintains ongoing authorization for {{ SYSTEM_NAME }} through the following continuous monitoring schedule:

| Monitoring Activity | Frequency / Cadence | Target Tool & Evidence Output | Responsible Role |
| :--- | :--- | :--- | :--- |
| **Vulnerability Scanning (`RA-5`)** | Weekly | {{ VULNERABILITY_SCANNER }} / Container Analysis Logs | DevSecOps / ISSO |
| **Configuration Drift Auditing (`CM-3`)** | Continuous (Real-time) | Terraform Plan / Cloud Asset Inventory Export | DevSecOps |
| **Audit Log Review (`AU-6`)** | Daily (Automated) | Cloud Logging / BigQuery Log Analytics Sinks | ISSO |
| **Plan of Action & Milestones (`CA-5`)** | Monthly | {{ RMF_GOVERNANCE_SYSTEM }} / `Plan_of_Action_and_Milestones.yaml` | ISSM |
| **System Security Plan Update (`CA-6`)** | Annual / Post-Change | `SSP_System_Security_Plan.md` | ISSM / SO |
| **Penetration Testing (`CA-8`)** | Annual | Independent Third-Party Assessment Report | ISSM / AO |
