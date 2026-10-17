# IR - Incident Response Policy and Procedures

## Document Governance & Approval Baseline

| Governance Metric | Policy Standard & Specification |
| :--- | :--- |
| **Document Title** | Incident Response Policy and Procedures |
| **NIST Control Family** | Incident Response (IR) |
| **Primary NIST Benchmark** | NIST SP 800-61 Rev. 3 (Incident Response Recommendations and Considerations for Cybersecurity Risk Management: A CSF 2.0 Community Profile; April 2025, supersedes Rev. 2), CISA Federal Incident Notification Guidelines |
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
> This document defines the enterprise security policy and implementation procedures for **Incident Response** under **NIST SP 800-53 Rev. 5 (IR)**.
> Technical infrastructure controls are automatically provisioned and enforced via **{{ SYSTEM_NAME }}** Terraform blueprints.
> Operational rules or contact details requiring manual confirmation are highlighted with RMF Team Callouts.


## 1. Overview

Federal agencies and organizations cannot protect the confidentiality, integrity, and availability of information in today's highly networked systems environment without ensuring that all people involved in using and managing IT:

1. Understand their roles and responsibilities related to the organizational mission;
2. Understand the organization's IT security policy, procedures, and practices; and
3. Have at least adequate knowledge of the various management, operational, and technical controls required and available to protect the IT resources for which they are responsible.

The purpose of this Incident Response Policy is to establish an incident response capability for {{ SYSTEM_NAME }} that prepares for, detects, analyzes, contains, eradicates, and recovers from security and privacy incidents, and that reports incidents to the appropriate authorities.

This policy addresses the Incident Response (IR) family requirements of NIST Special Publication 800-53 Revision 5, "Security and Privacy Controls for Information Systems and Organizations." A detailed compliance matrix is provided in Appendix A, "Detailed Compliance Matrix."

The Incident Response Policy encompasses all {{ ORGANIZATION }} users who have access to {{ SYSTEM_NAME }}. This policy outlines the framework for establishing, implementing, and maintaining incident response in alignment with applicable {{ GOVERNANCE_REGIME }} guidelines (NIST SP 800-53, FedRAMP, and applicable federal and state regulations), and is consistent with applicable laws, executive orders, directives, regulations, policies, standards, and guidelines. It applies to employees, contractors, and third-party users who handle sensitive information or operate within the {{ ORGANIZATION }} {{ SYSTEM_NAME }} information technology infrastructure.

{{ ORGANIZATION }} management is committed to the requirements of this policy and provides the resources needed to implement them. The ISSM ({{ ISSM_NAME }}) manages the development, documentation, and dissemination of this policy and its procedures, and coordinates their implementation with the Authorizing Official, System Owner, ISSO, and other organizational entities identified in the Program Roles & Responsibilities Matrix.

This policy and its procedures are reviewed and updated at least annually and following significant changes to {{ SYSTEM_NAME }} or its operating environment, security or privacy incidents, assessment or audit findings, or changes in applicable laws, executive orders, directives, regulations, policies, standards, or guidelines.


### 1.1 Background

The incident handling procedures in Section 4 align with NIST SP 800-61 Revision 3 (April 2025), "Incident Response Recommendations and Considerations for Cybersecurity Risk Management: A CSF 2.0 Community Profile," which supersedes NIST SP 800-61 Revision 2 and maps the incident response life cycle onto the NIST CSF 2.0 Functions: Preparation to Govern (GV), Identify (ID), and Protect (PR); Detection and Analysis to Detect (`DE.AE`) and Respond (`RS.MA`, `RS.AN`); Containment, Eradication, and Recovery to Respond (`RS.MI`, `RS.CO`) and Recover (`RC.RP`, `RC.CO`); and Post-Incident Activity to Identify (`ID.IM`).

These incident response steps are complemented by the Google Cloud Security Incident Response Guide for incidents in the Google Cloud environment that hosts {{ ORGANIZATION }} {{ SYSTEM_NAME }}.


### 1.2 Roles and Responsibilities

{{ ORGANIZATION }} {{ SYSTEM_NAME }} has an incident response team assigned to handle incidents. The roles in the table below are required for {{ ORGANIZATION }} {{ SYSTEM_NAME }}.


| Role | Responsibility | Point of Contact |
| --- | --- | --- |
| Information System Owner (ISO) | Responsibilities include: - Protecting sensitive information on {{ SYSTEM_NAME }} and ensuring that its users know and follow Incident Response policies and procedures - Ensuring this policy is in direct alignment with regulatory requirements, applicable standards, and incident response procedures - Facilitating the involvement of law enforcement and ensuring legal action is taken appropriately towards the incident - Coordinating with relevant law enforcement, state fusion centers, or agency counterintelligence organizations as required | {{ SO_NAME }} {{ SO_EMAIL }} {{ SO_PHONE }} |
| Program Manager (PM) | Responsibilities include: - Coordinating the incident response among {{ ORGANIZATION }} stakeholders - Serving as the central point of communication across all teams within {{ ORGANIZATION }}, management, stakeholders, and any applicable third parties - Enforcing the incident response timelines and managing critical resources such as personnel and budgeting for incident response utilities and activities - Overseeing and approving the incident response documentation, reporting, evidence collection, incident analysis, and risk mitigation | [CONFIG_REQUIRED: Program Manager Point of Contact] |
| Information Systems Security Manager (ISSM) | Responsibilities include: - Serving as the primary cybersecurity advisor to the AO, ISO, and PM - Directing the development, documentation, approval, and dissemination of the Incident Response Plan, policies, and procedures - Ensuring all privileged users receive necessary technical training and that {{ SYSTEM_NAME }} users maintain proper clearances in accordance with applicable security regulations - Coordinating with the {{ SYSTEM_NAME }} ISSO/ISSE to ensure that {{ SYSTEM_NAME }} and applications are continuously monitored for security-relevant events and ready for incident response procedures - Assessing proposed configuration changes for potential impact to the cybersecurity posture - Ensuring that the incident response policies and procedures are reviewed and updated at least annually | {{ ISSM_NAME }} {{ ISSM_EMAIL }} {{ ISSM_PHONE }} |
| Cloud Service Provider (Google) | Responsibilities include: - Protecting incident information commensurate with the impact level of the cloud service - Maintaining a Risk Management Program for the cloud service in accordance with FedRAMP guidelines - Complying with IR guidance and requirements - Maintaining a list of all current customers and communication channels with all AOs and 3PAOs - Notifying affected customers of information security incidents - Notifying CISA of information security incidents within mandated FedRAMP/DoD reporting SLAs, providing the CISA tracking number to the FedRAMP PMO (`fedramp_security@gsa.gov` / `fedramp_security@fedramp.gov`) and all applicable stakeholders, and providing status updates thereafter - Requesting assistance from CISA when incident severity thresholds are met - Providing a final report to the FedRAMP PMO/Board and applicable stakeholders, including agency AOs or AO representatives, after completion of the Post-Incident activity phase of the incident response life cycle | [CONFIG_REQUIRED: Google Cloud Customer Care escalation contact and support channel] |


### 1.3 Assumptions

The following assumptions were used when developing this policy:

- {{ ORGANIZATION }} {{ SYSTEM_NAME }} is categorized as {{ FIPS_199_CATEGORIZATION }} in accordance with FIPS 199 and NIST SP 800-60 (see the {{ SYSTEM_NAME }} Categorization Form).

- Key {{ ORGANIZATION }} personnel have been identified and trained in their incident response and recovery roles and are available to activate the Incident Response Plan.

- The {{ ORGANIZATION }} Incident Response Plan does not apply to emergency evacuation of personnel.


## 2. Incident Response Training

All federal employees, contractors, and third-party vendors related to {{ ORGANIZATION }} {{ SYSTEM_NAME }} must receive incident response training on detection, reporting, and response procedures. All personnel involved with configuring, monitoring, handling, or overseeing {{ ORGANIZATION }} {{ SYSTEM_NAME }} will be required to review the Google Cloud Security Incident Response Guide.

- Specialized Training: Incident response team members shall receive specialized training on advanced incident analysis, containment techniques, and tool usage, in accordance with the NIST SP 800-53 Incident Response controls.

- Frequency of Training: Personnel receive incident response training consistent with their assigned roles within 30 days of assuming an incident response role or responsibility or acquiring system access, when required by system changes, and annually thereafter. Incident response training content is reviewed and updated at least annually and following significant system changes or lessons learned from incidents and exercises.

- Breach Training: Training covers how to identify and respond to a breach of personally identifiable information, including the {{ ORGANIZATION }} process for reporting a breach (see Section 7.1).

Users must be aware of policies and procedures regarding appropriate use of networks, systems, and applications. Applicable lessons learned from previous incidents are shared with users to see how actions could affect the organization. Improving user awareness regarding incidents should reduce the frequency of incidents. All applicable team members are trained to maintain their networks, systems, and applications in accordance with the organization's security standards.

{{ ORGANIZATION }} incorporates simulated events into the incident response training to facilitate effective response by their personnel in crisis situations. In addition to simulated events, automated mechanisms can provide a more thorough and realistic incident response training environment. {{ ORGANIZATION }} must ensure all personnel training is associated with their assigned roles and responsibilities to ensure that the appropriate content is included.


### 2.1 Google Cloud Inherited Controls & Shared Responsibility Boundary

- **Google Inherited Controls**: Google Cloud maintains 24x7 Incident Response Teams (`IR-4`, `IR-5`), physical security incident handling, and immediate notification to {{ ORGANIZATION }} for CSP infrastructure incidents (`IR-6`).
- **Customer Implementation Responsibilities**: {{ ORGANIZATION }} is responsible for maintaining the Incident Response Plan (`IR-8`), executing incident handling procedures (`IR-4`), reporting incidents to CISA (`https://www.cisa.gov/forms/report`)<!-- IF DOD_ENCLAVE --> and the contracted DoD CSSP / DISA<!-- ENDIF --> within the timelines in Section 5.1 (`IR-6`), and conducting annual Incident Response tabletop exercises (`IR-3`).

## 3. Incident Response Testing

{{ ORGANIZATION }} tests the effectiveness of the incident response capability at least annually, and every six months for systems with a High availability impact, to determine the overall incident response effectiveness, identify potential weaknesses or deficiencies in daily organizational operations, and record results in a Lessons Learned document. Incident Response Testing is done via the following "Test, Training, and Exercise Program" outlined in NIST SP 800-84.

{{ ORGANIZATION }} involves at least one of the following Incident Response Testing Methods from NIST SP 800-84:

- Incident Response Testing Checklist (NIST SP 800-84 / NIST SP 800-61 Rev. 3 CSF 2.0 profile)

- Functional or Tabletop Exercises

  - Functional: Personnel with operational responsibilities validate their IT plans and their operational readiness for emergencies in a simulated operational environment through exercising their roles and responsibilities of specific team members, procedures, and assets involved in one or more functional aspects of the Incident Response Plan.

  - Tabletop: All personnel with roles and responsibilities in the Incident Response Plan meet in a classroom setting or in a remote virtual conference to validate the Incident Response Plan contents through only discussion of their roles during emergencies and their responses to emergency situations. No deploying of equipment or any other resources are necessary.


### 3.1 Coordination with Related Plans

{{ ORGANIZATION }} coordinates incident response testing with the organizational elements responsible for related plans, including the {{ SYSTEM_NAME }} COOP/DR team, {{ ORGANIZATION }} NetOps, and the CSSP, and aligns testing with the Google Cloud Security Incident Response Guide.


## 4. Incident Handling

{{ ORGANIZATION }} implements an Incident Handling process for security incidents that follows the NIST SP 800-61 Revision 3 (CSF 2.0) incident response life cycle described in Section 4.1.


### 4.1 Incident Handling Life Cycle


#### 4.1.1 Preparation

{{ ORGANIZATION }} preparation involves enabling detective controls, verifying appropriate access to applicable tools and cloud services necessary, and preparing necessary playbooks (both manual and automated) to verify reliable and consistent responses.

Incident Handler Communications and Facilities:

- The {{ ORGANIZATION }} Incident Tracking System will triage incident information, timestamps, and overall incident status.

Incident Analysis Hardware and Software:

- {{ ORGANIZATION }} produces backup virtual assets through Google Cloud and preserves log files and other relevant data.

- Sandbox environments are in place for any form of testing, including static or dynamic malware analysis.

Incident Analysis Resources:

- {{ ORGANIZATION }} maintains current network diagrams, port listings, hardware and software lists, and security baseline configurations for the resources used within {{ SYSTEM_NAME }}.

- {{ ORGANIZATION }} will use Google Cloud KMS for encryption of application activity.


#### 4.1.2 Detection and Analysis

{{ ORGANIZATION }} incident detection methods involve the {{ INTRUSION_DETECTION_SYSTEM }} to detect and analyze potential, dormant, or active anomalies within {{ ORGANIZATION }} {{ SYSTEM_NAME }}. Incidents in {{ ORGANIZATION }} {{ SYSTEM_NAME }} may also be detected manually via incidents reported by users.

- A precursor is an indication that an incident may occur in the future. Detecting precursors allow the opportunity to reinforce security practices and prevent an incident from altering the {{ ORGANIZATION }} {{ SYSTEM_NAME }} security posture. Precursors can include:

  - Threat notifications from external threat actors.

  - New exploits announced for {{ ORGANIZATION }} organization information systems, Google Cloud environment, etc.

- An indicator is an indication that an incident already occurred or is currently happening. Indicators can include:

  - Antivirus program announcing a host has been infected with malware.

  - IDS alerting unauthorized Log file changes.

{{ ORGANIZATION }} incident analysis methods involve the network and system behavioral analysis, Firewall log / IDPS system log reviews, and filtering out insignificant events, while also prioritizing incidents to handle the most critical ones first. The {{ ORGANIZATION }} Incident Response tracking system will ultimately ensure that reported incidents are prioritized, handled, tracked, and ultimately resolved promptly. The tracking system contains the following documented information for cross analysis:

- A detailed summary of the incident with all indicators related to the incident.

- Other incidents related to this incident.

- Actions taken by all incident handlers on this incident.

- Chain of custody (if applicable).

- Impact assessments related to the incident.

- Contact information for other involved parties (e.g., system owners, system administrators)

- A list of evidence gathered during the incident investigation.

- Comments from incident handlers, submitters, and all other applicable personnel.

- Next steps needed for an incident (e.g., rebuilding a host, upgrading an application, etc.).


#### 4.1.3 Containment, Eradication, and Recovery

Containment Strategy

Containment is critical for {{ ORGANIZATION }} {{ SYSTEM_NAME }} and must be conducted to decrease the risk of damage to other internal resources. If an incident requires containment, the following must be done to the affected information systems within {{ ORGANIZATION }} {{ SYSTEM_NAME }} as soon as possible (if applicable):

- Shutdown of services and system power.

- Isolation of network connectivity.

Evidence Gathering and Handling

{{ ORGANIZATION }} must gather evidence from incidents for legal proceedings (if applicable). This will involve clearly documenting details about the compromised systems and what was preserved in the environment, including the following:

- Identifying information (Incident location, serial number, model number, hostname, MAC addresses, and IP address)

- Name, title, and phone number of everyone who collected and handled the evidence during the investigation process.

- Time and date of each occurrence of evidence handling.

Eradication

Eradication within {{ ORGANIZATION }} {{ SYSTEM_NAME }} identifies all affected systems within the organization and performs remediation via elimination of affected systems.

Recovery

{{ ORGANIZATION }} recovery involves restoration of systems to normal operation, confirming normal functionality, and (if applicable) remediation of vulnerabilities to prevent future similar incidents.


#### 4.1.4 Post-incident Activity

Lessons Learned

{{ ORGANIZATION }} learns and improves from all incidents using "Lessons Learned" documentation and scheduled meetings with all parties involved from the incident to allow for direct closure with respect to the incident that occurred.

Post-incident review and continuous improvement questions (NIST SP 800-61 Revision 3 `ID.IM` / legacy Rev. 2) include:

- What happened and what time did the incident occur? Was information needed sooner?

- How well did staff and management perform in dealing with the incident? Were the documented procedures followed? Were they adequate?

- Were any steps or actions taken that might have inhibited the recovery?

- What would the staff and management do differently next time?

- How could information sharing with other organizations have been improved?

- What corrective actions can prevent similar incidents in the future?

- What precursors or indicators should be watched for in the future to detect similar incidents?


### 4.2 Automated Incident Handling Processes

{{ THREAT_DETECTION_IMPLEMENTATION }}


### 4.3 Continuity of Operations

{{ ORGANIZATION }} {{ SYSTEM_NAME }} is categorized as {{ FIPS_199_CATEGORIZATION }} in accordance with FIPS 199 and NIST SP 800-60 (see the {{ SYSTEM_NAME }} Categorization Form). {{ SYSTEM_NAME }} follows the actions provided by {{ ORGANIZATION }} in response to incidents to ensure continuation of mission and business functions. <!-- IF DOD_ENCLAVE -->Incident classes are the CJCSM 6510.01B categories listed in Section 7.<!-- ENDIF --><!-- IF NOT DOD_ENCLAVE -->Incident classes follow CISA Federal Incident Notification Guidelines and NIST SP 800-61 Rev. 3.<!-- ENDIF --> Continuity actions include multi-region route failover, redundant {{ INTERCONNECT_TYPE }} circuits, and HA Cloud VPN gateways.


### 4.4 Information Correlation

The following are all audit logs that are collected and stored within Google Cloud; {{ ORGANIZATION }} uses the logs to correlate incident information and individual incident responses to achieve an organization-wide perspective on incident awareness and response.

Admin Activity Logs - Admin Activity audit logs contain log entries for API calls or other actions that modify the configuration or metadata of resources. For example, these logs record when users create VM instances or change Identity and Access Management permissions.

Data Access Logs - Data Access audit logs contain API calls that read the configuration or metadata of resources, as well as user-driven API calls that create, modify, or read user-provided resource data.

System Event Logs - System Event audit logs contain log entries for Google Cloud actions that modify the configuration of resources. System Event audit logs are generated by Google systems; they aren't driven by direct user action.

VPC Flow Logs - VPC Flow Logs record a sample of network flows sent from and received by VM instances, including instances used as GKE nodes. These logs can be used for network monitoring, forensics, real-time security analysis, and expense optimization.

Firewall Rule Logs - Firewall Rules Logging lets you audit, verify, and analyze the effects of your firewall rules. For example, you can determine if a firewall rule designed to deny traffic is functioning as intended. Firewall Rules Logging is also useful if you need to determine how many connections are affected by a given firewall rule.

Access Transparency Logs - Access Transparency logs include data about Google staff activity, including:

- Actions by the Support team that you may have requested by phone

- Basic engineering investigations into your support requests

- Other investigations made for valid business purposes, such as recovering from an outage


### 4.5 Insider Threats

Insider threats pose various risks; {{ SYSTEM_NAME }} minimizes the risk by safeguarding privileged functions through the implementation of RBAC (IAM Privileges), principle of least privilege access, and log analysis of user activity to detect anomalies and potential threatening actions.

Refer to Section 4.2 for more information on {{ THREAT_DETECTION_ENGINE }} and how {{ SYSTEM_NAME }} implements RBAC, principle of least privilege access, and log analysis.


### 4.6 Insider Threats - Intra-Organization Coordination

{{ SYSTEM_NAME }} follows the actions provided by {{ ORGANIZATION }} to ensure intra-organizational coordination and communication is maintained throughout the lifecycle of an incident. Insider threat incident handling is coordinated with the Senior Agency Official for Privacy (SAOP), counterintelligence, the {{ ORGANIZATION }} Provost Marshal (or equivalent law enforcement office), and {{ CSSP_PROVIDER }} insider threat analysts.


### 4.7 Correlation with External Organizations

{{ SYSTEM_NAME }} follows the actions provided by {{ ORGANIZATION }} to ensure external organization coordination and communication is maintained throughout the lifecycle of an incident.

{{ ORGANIZATION }} {{ SYSTEM_NAME }} communicates incidents with the following external organizations:

- Cybersecurity and Infrastructure Security Agency (CISA, formerly US-CERT)

- Defense Information Systems Agency (DISA)

- Federal Risk and Authorization Management Program (FedRAMP PMO)

Information about significant threat detections and indicators of compromise is shared by the {{ SYSTEM_NAME }} ISO with the external organizations listed above via email, phone, or video call.


### 4.8 Supply Chain Coordination

{{ SYSTEM_NAME }} follows the actions provided by {{ ORGANIZATION }} to ensure external organization coordination and communication is maintained throughout the lifecycle of an incident, to include activities involving supply chain events with other organizations involved in the supply chain.


### 4.9 Integrated Incident Response Team

The Integrated Incident Response Team for {{ SYSTEM_NAME }} will be maintained by {{ ORGANIZATION }}.


### 4.10 Malicious Code and Forensic Analysis

The forensic analysis and analysis of malicious code and/or other residual artifacts remaining in the system after an incident is the responsibility of {{ ORGANIZATION }}.


### 4.11 Behavior Analysis

The analysis of behaviors in an environment targeted by adversaries is the responsibility of {{ ORGANIZATION }}.


### 4.12 Security Operations Center

Refer to Section 4.2 for more information on {{ THREAT_DETECTION_ENGINE }} and {{ EXTERNAL_SIEM }} maintained by {{ ORGANIZATION }}.


## 5. Incident Monitoring

Monitoring incidents includes maintaining records about each incident, the status of the incident, and other pertinent information necessary for forensics as well as evaluating incident details, trends, and handling. Incident information can be obtained from a variety of sources, including network monitoring, incident reports, incident response teams, user complaints, supply chain partners, audit monitoring, physical access monitoring, and user and administrator reports. Incident monitoring and documenting procedures will be included in the associated RMF package and aligned with the {{ ORGANIZATION }} program incident monitoring process.

{{ ORGANIZATION }} {{ SYSTEM_NAME }} uses {{ THREAT_DETECTION_ENGINE }} and {{ EXTERNAL_SIEM }} for automated tracking, data collection, and analysis. Refer to the {{ SYSTEM_NAME }} Technical Design Document and Section 4.2 for additional information.


### 5.1 Formal Incident Escalation & SLA Timelines (`IR-6`)

{{ INCIDENT_ESCALATION_IMPLEMENTATION }}


### 5.2 Automated Reporting

Automated incident reporting reduces delays in notifying stakeholders and reporting authorities.

{{ ORGANIZATION }} {{ SYSTEM_NAME }} implements the following automated reporting mechanisms:

#### 5.2.1 Automated Alerting & Incident Monitoring Integration (`IR-4`, `IR-6`)

{{ ORGANIZATION }} uses automated security monitoring and alerting tools in {{ SYSTEM_NAME }} to notify responders of security events in real time:

1. **Real-Time Threat & Finding Exports**: Automated security finding notifications from {{ THREAT_DETECTION_ENGINE }} are routed in real time via {{ TELEMETRY_PIPELINE }} and Pub/Sub to Cloud Functions / Eventarc triggers, creating high-priority tickets in {{ ITSM_SYSTEM }} (`IR-4`).
2. **SIEM / Log Sink Integration**: Critical security events (e.g., IAM permission changes, VPC firewall modifications, KMS key deletion attempts) trigger automated notifications in {{ EXTERNAL_SIEM }} and alerts to on-call DevSecOps personnel (`AU-6`, `IR-6`).
3. **Automated CISA / CSSP Incident Submission**: High-severity incident tickets generate structured JSON alerts formatted for rapid submission to federal reporting bodies in compliance with CISA Federal Incident Notification Guidelines<!-- IF DOD_ENCLAVE --> and DoD CJCSM 6510.01B<!-- ENDIF --> (`IR-6`).


### 5.3 Vulnerabilities Related to Incidents

Regular vulnerability assessments and vulnerability scans are conducted against {{ SYSTEM_NAME }} and its Google Cloud environment to identify, categorize, and remediate all relevant security vulnerabilities that are subject to exploitation during cybersecurity incidents. System vulnerabilities associated with reported incidents are reported to the ISSM and AO and tracked as POA&M entries.

Managing vulnerabilities related to incidents reduces the likelihood of exploitation and improves resilience to cybersecurity incidents in {{ SYSTEM_NAME }} and the Google Cloud environment.


### 5.4 Supply Chain Coordination

{{ ORGANIZATION }} will promptly report cybersecurity incidents to the provider of the product or service that is impacted. {{ ORGANIZATION }} follows the following process when coordinating with providers of products or services that are impacted by cybersecurity incidents:

#### 5.4.1 Third-Party & Cloud Provider Incident Coordination (`IR-6`, `SR-3`)

When a security incident originates from or impacts a third-party software component, open-source Terraform module, or Google Cloud infrastructure service:

1. **Google Support & Incident Escalation**: Security incidents involving underlying Google Cloud platform services (`google_compute_network`, `google_container_cluster`, `google_kms_crypto_key`) are reported immediately to Google Cloud Support via dedicated Premium Support ticket channels and Google Security Operations (`IR-6`).
2. **Software Vendor Notification**: Incidents involving third-party commercial software modules or containers are reported to vendor security contacts within **4 hours** of identification (`SR-3`).
3. **Supply Chain Exposure Analysis**: The ISSO evaluates all deployed Terraform modules (`{{ TERRAFORM_MODULES }}`) and container images in Artifact Registry to determine if secondary applications or environments share the vulnerable component (`SR-11`).


## 6. Incident Response Assistance

The {{ ORGANIZATION }} cyber team provides incident response support resources including help desks, assistance groups, automated ticketing systems to open and track incident response tickets, and access to forensics services, when required.

{{ ORGANIZATION }} maintains direct, cooperative relationships with external providers of system protection capability, including Google Cloud (through its Enterprise Support agreement) and {{ CSSP_PROVIDER }}, and identifies its incident response team members to these providers through designated ISSM and ISSO point-of-contact rosters.


## 7. Incident Response Methodology

> [!IMPORTANT]
> [WARNING: RMF TEAM ACTION REQUIRED: Verify and update operational contact/procedure details in this section.]
> {{ ORGANIZATION }} develops, disseminates, and maintains the Incident Response Plan that defines roles, responsibilities, and procedures for {{ ORGANIZATION }} incident detection, analysis, containment, eradication, recovery, and post-incident activities. The Incident Response Plan draws on the NIST SP 800-53 Incident Response (IR) control family, Google Cloud security guidance, and lessons learned from previous incidents and exercises. The ISSM oversees the development, documentation, implementation, approval, and dissemination of the {{ ORGANIZATION }} Cybersecurity Incident Response Plan.

The AO reviews and approves the Incident Response Plan at least annually. The ISSM distributes the plan to incident response personnel, updates it to address system and organizational changes and problems found during implementation, execution, or testing, and communicates plan changes to incident response personnel. The plan is protected from unauthorized disclosure and modification through {{ IDENTITY_PROVIDER }} with {{ MFA_MECHANISM }} access controls and Cloud KMS CMEK encryption.

<!-- IF DOD_ENCLAVE -->
Reportable incidents in {{ ORGANIZATION }} are identified in accordance with (adapted from) CJCSM 6510.01B Table B-A-2:
<!-- ENDIF -->
<!-- IF NOT DOD_ENCLAVE -->
Reportable incidents in {{ ORGANIZATION }} are classified in accordance with CISA Federal Incident Notification Guidelines and NIST SP 800-61 Rev. 3:
<!-- ENDIF -->


| Category | Category Description |
| --- | --- |
| 0 | Training and Exercises — Operations performed for training purposes and support to CC/S/A/FA exercises. |
| 1 | Root Level Intrusion (Incident) — Unauthorized privileged access to an IS. Privileged access, often referred to as administrative or root access, provides unrestricted access to the IS. This category includes unauthorized access to information or unauthorized access to account credentials that could be used to perform administrative functions (e.g., domain administrator). If the IS is compromised with malicious code that provides remote interactive control, it will be reported in this category. |
| 2 | User Level Intrusion (Incident) — Unauthorized non-privileged access to an IS. Non-privileged access, often referred to as user level access, provides restricted access to the IS based on the privileges granted to the user. This includes unauthorized access to information or unauthorized access to account credentials that could be used to perform user functions such as accessing Web applications, Web portals, or other similar information resources. If the IS is compromised with malicious code that provides remote interactive control, it will be reported in this category. |
| 3 | Unsuccessful Activity Attempt (Event) — Deliberate attempts to gain unauthorized access to an IS that are defeated by normal defensive mechanisms. Attacker fails to gain access to the IS (i.e., attacker attempts valid or potentially valid username and password combinations) and the activity cannot be characterized as exploratory scanning. Reporting of these events is critical for the gathering of useful effects-based metrics for commanders. Note the above CAT 3 explanation does not cover the "run-of-the-mill" virus that is defeated/deleted by AV software. "Run-of-the-mill" viruses that are defeated/deleted by AV software are not reportable events or incidents. |
| 4 | Denial of Service (Incident) — Activity that denies, degrades, or disrupts normal functionality of an IS or organization information network. |
| 5 | Non-Compliance Activity (Event) — Activity that potentially exposes ISs to increased risk as a result of the action or inaction of authorized users. This includes administrative and user actions such as failure to apply security patches, connections across security domains, installation of vulnerable applications, and other breaches of existing organizational security policy. Reporting of these events is critical for the gathering of useful effects-based metrics for commanders. |
| 6 | Reconnaissance (Event) — Activity that seeks to gather information used to characterize ISs, applications, organization information networks, and users that may be useful in formulating an attack. This includes activity such as mapping organization information networks, IS devices and applications, interconnectivity, and their users or reporting structure. This activity does not directly result in a compromise. |
| 7 | Malicious Logic (Incident) — Installation of software designed and/or deployed by adversaries with malicious intentions for the purpose of gaining access to resources or information without the consent or knowledge of the user. This only includes malicious code that does not provide remote interactive control of the compromised IS. Malicious code that has allowed interactive access should be categorized as Category 1 or Category 2 incidents, not Category 7. Interactive active access may include automated tools that establish an open channel of communications to and/or from an IS. |
| 8 | Investigating (Event) — Events that are potentially malicious or anomalous activity deemed suspicious and warrant, or are undergoing, further review. No event will be closed out as a Category 8. Category 8 will be recategorized to appropriate Category 1-7 or 9 prior to closure. |
| 9 | Explained Anomaly (Event) — Suspicious events that after further investigation are determined to be non-malicious activity and do not fit the criteria for any other categories. This includes events such as IS malfunctions and false alarms. When reporting these events, the reason for which it cannot be otherwise categorized must be clearly specified. |

Adherence to the {{ ORGANIZATION }} Incident Response Plan ensures a coordinated and consistent approach to incident response activities for the Google Cloud environment, enhancing the ability to mitigate, monitor, and manage the impact of cybersecurity incidents while maintaining continuity of operations.


### 7.1 Breaches Involving Personally Identifiable Information

For breaches involving personally identifiable information (PII), the Incident Response Plan includes:

1. A process, coordinated with the Senior Agency Official for Privacy (SAOP), to determine whether notice to affected individuals or other organizations, including oversight organizations, is needed;
2. An assessment process, following OMB M-17-12, to determine the extent of the harm, embarrassment, inconvenience, or unfairness to affected individuals and the mechanisms available to mitigate those harms; and
3. Identification of the privacy requirements that apply to the breach.


## 8. Information Spillage Response

{{ ORGANIZATION }} has the responsibility to report and escalate any form of spillage that is detected and reported. Spillages are not to be hidden or handled in secret in order to save organizational embarrassment.

All known or suspected instances of data spillages are to be reported and full cooperation is to be rendered during any investigation. [CONFIG_REQUIRED: Personnel or roles assigned responsibility for responding to information spills (for example, the ISSO and ISSM).]

> [!IMPORTANT]
> [WARNING: RMF TEAM ACTION REQUIRED: Verify and update operational contact/procedure details in this section.]
> Thorough investigations are to be conducted to determine the cause of any spillage incident. Depending on the level of data spillage, external communications to applicable federal, state, or local law enforcement agencies are done by the {{ ORGANIZATION }} {{ SYSTEM_NAME }} ISO for legal handling of that incident.

For any security incident, {{ SYSTEM_NAME }} is subject to isolation and will be processed according to the methods outlined in this policy, as well as any additional {{ ORGANIZATION }} Incident Response policies.


### 8.1 Training

{{ ORGANIZATION }} is responsible for ensuring all {{ SYSTEM_NAME }} users are trained on the reporting procedures for information spillage. Training must occur at least annually.


### 8.2 Post-Spill Operational Procedures & Remediation Workflow

In accordance with NIST SP 800-53 Rev. 5 (`IR-9`), CNSSI 1001, and NIST SP 800-61 Rev. 3 / CISA incident handling guidelines, {{ ORGANIZATION }} enforces the following 7-stage post-spill remediation protocol whenever higher-classification or unauthorized data is spilled into {{ SYSTEM_NAME }}:

1. **Immediate Resource Containment & Isolation (`IR-9`)**:
   - Immediately isolate affected Cloud Storage buckets, GKE pods, Persistent Disks, or Compute Engine VMs by applying strict VPC Service Control perimeters and revoking all IAM data access permissions.
   - Halt all automated backup jobs, cross-region storage replication (`CP-9`), and log export sinks (`AU-4`) associated with the spilled data path to prevent secondary contamination.

2. **Out-of-Band Incident Alerting (`IR-9`)**:
   - Notify the ISSO, ISSM, System Owner (`{{ SO_NAME }}`), and Authorizing Official (`{{ AO_NAME }}`) within **15 minutes** of spill confirmation.
   - All notifications must occur via secure out-of-band communication channels (e.g., dedicated secure voice line or out-of-band encrypted messaging) to ensure compromised system channels are not used.

3. **Forensic Identification & Spill Scope Analysis**:
   - Review Cloud Audit Logs (`AU-2`, `AU-3`) and Cloud Monitoring network flow logs (`AU-6`) to identify the exact timestamp, source IP, authenticated user ID, and full list of accessed objects/records involved in the spill.
   - Identify all downstream destinations, cache layers, or endpoint workstations that ingested or cached the spilled data.

4. **Cloud Media Sanitization & Cryptographic Destruction (`MP-6`, `SC-28`)**:
   - Perform logical sanitization and purge of contaminated Cloud Storage objects, SQL tables, and persistent disk sectors in strict compliance with NIST SP 800-88 Rev. 1 Guidelines for Media Sanitization.
   - If Customer-Managed Encryption Keys (CMEK) were used for the contaminated data store, execute immediate key destruction or rotation in Cloud KMS (`SC-12`, `SC-28`) to render any un-sanitized physical storage fragments permanently unreadable.

5. **Operational Continuity for Impacted Personnel (`IR-9(3)`)**:
   - Provide un-contaminated replacement endpoint hardware or isolated cloud workstations (`Cloud Workstations`) to impacted personnel to ensure mission-essential tasks continue while contaminated environments undergo remediation.

6. **Mandatory External Incident Escalation (`IR-6`)**:
   - Submit a formal Information Spillage Incident Summary Report to CISA, DISA/CSSP (for DoD deployments), FedRAMP PMO (when applicable), and the Authorizing Official within **24 hours** of incident verification, detailing the spill scope, data classification level, and containment actions taken.

7. **Root Cause Analysis (RCA) & POA&M Remediation (`CA-5`, `IR-8`)**:
   - Conduct a formal Post-Mortem Root Cause Analysis within **5 business days** of containment.
   - Document corrective actions, IAM policy updates, and automated VPC perimeter enhancements in the System Plan of Action and Milestones (POA&M) (`CA-5`) to permanently prevent recurrence of similar spillage incidents.


### 8.3 Exposure to Unauthorized Personnel

{{ SYSTEM_NAME }} implements access controls, encryption, and authentication mechanisms within Google Cloud to prevent unauthorized access to sensitive information. Personnel exposed to information not within their assigned access authorizations have the related access revoked immediately, receive a security debriefing, are reminded of their non-disclosure obligations, and may be subject to an administrative inquiry under DoDM 5200.01 Vol. 3.


## Appendix A – Detailed Compliance Matrix

The following table provides detailed traceability between the policy implementation statements in this document, the authoritative NIST SP 800-53 Rev. 5 control requirements, DoD CCIs, and the technical/governance enforcement mechanisms active across {{ SYSTEM_NAME }}.


| CTRL ID | CTRLTITLE | REQUIRED {{ GRC_STANDARD_LABEL }} STANDARD | DOCREF | ENFORCEMENT MECHANISM |
| :--- | :--- | :--- | :--- | :--- |
| IR-01 | Policy and Procedures | Develop, document, and disseminate to all personnel an incident response policy and procedures; designate the ISSM to manage them; review and update both at least annually and following significant system changes, security or privacy incidents, assessment or audit findings, or changes in applicable laws, regulations, or policies (CCI-000805, CCI-000806, CCI-000807, CCI-000808, CCI-000809, CCI-000810, CCI-000811, CCI-000812, CCI-002776, CCI-002777, CCI-004109, CCI-004110, CCI-004111, CCI-004112, CCI-004113, CCI-004114, CCI-004115, CCI-004116) | Section 1 | ISSM-managed annual and event-driven review; AO approval; changes recorded in the Document Change Record; eMASS artifact repositories. |
| IR-02 | Incident Response Training | Provide role-based incident response training to system users within {{ ODP_IR_2_TRAINING_WINDOW }} of role assumption and at least annually thereafter (CCI-000813, CCI-000814, CCI-000815, CCI-002778, CCI-002779, CCI-005151, CCI-005152, CCI-005153) | Section 2 | Automated LMS tracking, role-based training modules on Google Cloud and DoD incident handling, and ISSM annual curriculum audits. |
| IR-02(01) | Simulated Events | Incorporate simulated events into incident response training to facilitate effective response by personnel in crisis situations. (CCI-000816) | Section 2 | Annual simulated cyber incident exercises (tabletop and red/blue team drills) covering cloud credential, compute, and boundary compromise scenarios. |
| IR-02(02) | Automated Training Environments | Employ automated mechanisms to provide a more thorough and realistic incident response training environment. (CCI-000817, CCI-004117) | Section 2 | Automated LMS cyber range simulations and sandbox GCP incident drill environments. |
| IR-02(03) | Breach | Provide incident response training on how to identify and respond to a breach, including the organization's process for reporting a breach (CCI-004118) | Section 2 | Mandatory PII/CUI breach identification, response, and reporting training tracked in the {{ ORGANIZATION }} Learning Management System; DoD Cyber Awareness Challenge. |
| IR-03 | Incident Response Testing | Test the effectiveness of the incident response capability at least annually, and every 6 months for systems with a High availability impact, using checklist, functional, and tabletop tests (CCI-000818, CCI-000819, CCI-000820) | Section 3 | Semiannual tabletop exercises (TTX) and live functional failover simulations in sandboxed test projects. |
| IR-03(02) | Coordination with Related Plans | Coordinate incident response testing with organizational elements responsible for related plans (CCI-002780) | Section 3.1 | Cross-functional exercise coordination with cyber operations commands, {{ ORGANIZATION }} NetOps, DISA CSSP, {{ SYSTEM_NAME }} COOP/DR teams, and {{ CLOUD_PROVIDER }} incident support. |
| IR-04 | Incident Handling | Implement an incident handling capability for incidents consistent with the IRP, CP coordination, and lessons learned (CCI-000822, CCI-000823, CCI-001625, CCI-004130, CCI-004131, CCI-004132, CCI-004133, CCI-004134, CCI-004135, CCI-004136) | Section 4 | NIST SP 800-61 Rev. 3 (CSF 2.0) incident response life cycle, automated Google Cloud Logging sinks, BigQuery analytics, and Terraform IaC rollback playbooks. |
| IR-04(01) | Automated Incident Handling Processes | Support incident handling using automated mechanisms including SIEM, SOAR, EDR, and NAC (CCI-000825, CCI-004137) | Section 4.2 | Cloud Logging sinks routing to Pub/Sub, BigQuery, SOAR playbooks, IAM credential revocation, and automated VPC-SC firewall rules. |
| IR-04(02) | Dynamic Reconfiguration | Include dynamic reconfiguration of {{ SYSTEM_NAME }} components (such as router rules, firewall policies, and IAM bindings) as part of the incident handling capability. (CCI-000826, CCI-002781, CCI-004138) | Section 4 | Automated and runbook-driven dynamic updates to VPC firewall rules, Cloud Armor policies, VPC Service Controls perimeters, and Cloud IAM bindings during containment. |
| IR-04(03) | Continuity of Operations | Identify incident classes<!-- IF DOD_ENCLAVE --> (CJCSM 6510.01B)<!-- ENDIF --> and execute actions ensuring mission continuity (CCI-000827, CCI-000828, CCI-004139, CCI-004140) | Section 4.3 | Dynamic BGP multi-region route failover, redundant {{ INTERCONNECT_TYPE }} circuits, and HA Cloud VPN gateways. |
| IR-04(04) | Information Correlation | Correlate incident information and responses to achieve an organization-wide perspective (CCI-000829) | Section 4.4 | BigQuery SQL analytical views aggregating VPC Flow Logs, boundary firewall logs, and {{ CSSP_PROVIDER }} centralized correlation. |
| IR-04(06) | Insider Threats | Implement incident handling capability for insider threats (CCI-002782) | Section 4.5 | Google Cloud Privileged Access Manager (PAM) just-in-time access, intra-project separation of duties via Resource Manager Tags, and immutable Cloud Audit Logs. |
| IR-04(07) | Insider Threats — Intra-organization Coordination | Coordinate insider threat incident handling with SAOP and key cybersecurity personnel (CCI-004141, CCI-004142) | Section 4.6 | Integrated escalation workflows with {{ ORGANIZATION }} Provost Marshal, Counterintelligence (CI), SAOP, and {{ CSSP_PROVIDER }} insider threat analysts. |
| IR-04(08) | Correlation with External Organizations | Coordinate with external organizations (CISA, DoD CSSP, DISA, FedRAMP PMO) to correlate and share compromise data (CCI-002785, CCI-002786, CCI-002787) | Section 4.7 | Out-of-band communications, automated CISA / CSSP incident reporting gateways, and DISA/FedRAMP PMO coordination channels. |
| IR-04(10) | Supply Chain Coordination | Enforce supply chain coordination requirements across {{ SYSTEM_NAME }} in accordance with NIST SP 800-53 Rev. 5 IR-4(10). (CCI-002790) | Section 3 | Enforced via Google Cloud infrastructure controls, Terraform configuration baselines, and ISSM/ISSO governance verification. |
| IR-04(11) | Integrated Incident Response Team | Establish and maintain an integrated incident response team that can be deployed to any location identified by the organization within 24 hours. (CCI-004143, CCI-004144) | Section 4.9 | Cross-functional incident response team (ISSO, ISSM, DevSecOps, SOC/CSSP analysts, and cloud forensics specialists) with 24x7 remote and on-site mobilization capability. |
| IR-04(12) | Malicious Code and Forensic Analysis | Analyze malicious code and residual artifacts remaining in the system after an incident (CCI-004145) | Section 4.10 | Isolated forensic analysis sandboxes in dedicated staging projects, GCS disk snapshot acquisitions, and volatile memory inspection tooling. |
| IR-04(13) | Behavior Analysis | Analyze anomalous or suspected adversarial behavior across network traffic, process logs, and auth logs (CCI-004146, CCI-004147) | Section 4.11 | Continuous behavioral inspection using BigQuery streaming analytics, network telemetry, and {{ IDENTITY_PROVIDER }} sign-in log analysis. |
| IR-04(14) | Security Operations Center | Establish and maintain a security operations center (CCI-004148) | Section 4.12 | 24x7x365 {{ ORGANIZATION }} NetOps and accredited CSSP Security Operations Center monitoring per DoDI 8530.01. |
| IR-05 | Incident Monitoring | Track and document incidents across the system lifecycle (CCI-000832) | Section 5 | Immutable incident logging in {{ ITSM_SYSTEM }}, BigQuery audit data warehouse, and eMASS POA&M tracking. |
| IR-05(01) | Automated Tracking, Data Collection, and Analysis | Track incidents and collect/analyze incident data using SIEM and automated ticketing (CCI-004151, CCI-004152, CCI-004153, CCI-004154) | Section 5 | Automated Cloud Monitoring alert policies, Pub/Sub event ingestion, and {{ EXTERNAL_SIEM }} ticket auto-generation. |
| IR-06 | Incident Reporting | Report suspected incidents to designated authorities (CISA within 1 hour for Federal agencies<!-- IF DOD_ENCLAVE -->; DoD CSSP/USCYBERCOM within CJCSM 6510.01B Table C-A-1 impact-tiered timelines<!-- ENDIF -->; AO/ISSM) (CCI-000834, CCI-000835, CCI-000836, CCI-002791) | Section 5.1 | Formal multi-tiered SLA matrix (1-hr CISA<!-- IF DOD_ENCLAVE -->; CJCSM 6510.01B Table C-A-1 impact-tiered timelines: High impact CAT 1/2/4/7 notify next tier within 15 min / initial report within 4h / JIMS within 6h; Moderate impact CAT 1/2/7 within 2h / 8h / 12h and CAT 4 within 15 min / 4h / 6h<!-- ENDIF -->), automated alerting, and out-of-band command notifications. |
| IR-06(01) | Automated Reporting | Report incidents using automated SOAR and ITSM integration (CCI-000837, CCI-004155) | Section 5.2 | SOAR pipeline integration with {{ ITSM_SYSTEM }} for automated notification dispatch and JSON report creation. |
| IR-06(02) | Vulnerabilities Related to Incidents | Report system vulnerabilities associated with incidents to the ISSM and AO (CCI-000838, CCI-002792) | Section 5.3 | Automated CI/CD scan findings (Semgrep, Checkov, tfsec) and ACAS vulnerability mapping to eMASS POA&M entries. |
| IR-06(03) | Supply Chain Coordination | Provide incident information to the provider of the affected product or service, including the CSP, and to other organizations involved in the supply chain or supply chain governance (CCI-002793, CCI-004156) | Section 5.4 | Automated escalation tickets to Google Cloud Premium Support and hardware/software vendor security response centers. |
| IR-07 | Incident Response Assistance | Provide integral incident response support resources including help desks and forensics (CCI-000839) | Section 6 | 24x7 NetOps operational help desk, automated service portal, and dedicated forensic engineering support teams. |
| IR-07(01) | Automation Support for Availability of Information and Support | Increase the availability of incident response information and support using automated mechanisms (self-service knowledge portal and automated ticketing) (CCI-005154) | Section 6 | Centralized knowledge portal, automated {{ ITSM_SYSTEM }} runbooks, and Google Cloud documentation repositories. |
| IR-07(02) | Coordination with External Providers | Establish direct relationships with external providers and identify IR team members (CCI-000841, CCI-000842) | Section 6 | Established Enterprise Support agreements with Google Cloud, colocation facility providers, and carriers, with designated ISSM/ISSO POC rosters. |
| IR-08 | Incident Response Plan | Develop, review, approve, update, and protect the Incident Response Plan (CCI-000844, CCI-000845, CCI-000846, CCI-000849, CCI-000850, CCI-002794, CCI-002795, CCI-002796, CCI-002797, CCI-002798, CCI-002799, CCI-002800, CCI-002801, CCI-002802, CCI-002803, CCI-002804, CCI-004157, CCI-004158, CCI-004159) | Section 7 | Formally approved {{ SYSTEM_NAME }} IRP document, annual AO approval, {{ IDENTITY_PROVIDER }} with {{ MFA_MECHANISM }} access controls, and Cloud KMS CMEK storage encryption. |
| IR-08(01) | Breaches | Include in the Incident Response Plan, for breaches involving PII, a process to determine whether notice to individuals or other organizations (including oversight organizations) is needed, an assessment of the extent of harm to affected individuals and how to mitigate it, and identification of applicable privacy requirements (CCI-004160, CCI-004161, CCI-004162) | Section 7.1 | OMB M-17-12 harm assessment framework, SAOP coordination protocols, and automated affected-party notification workflows. |
| IR-09 | Information Spillage Response | Respond to information spills by assigning responders, identifying the spilled information, alerting personnel out-of-band, isolating and eradicating the information, identifying other contaminated components, and performing the additional actions in the 7-stage workflow (CCI-002805, CCI-002806, CCI-002807, CCI-002808, CCI-002809, CCI-002810, CCI-002811, CCI-002812, CCI-004163, CCI-004164) | Section 8 | Out-of-band notification, VPC Service Control boundary enforcement, NIST SP 800-88 Rev. 1 media sanitization, and Cloud KMS key destruction. |
| IR-09(02) | Training | Provide information spillage response training annually consistent with IR-02 (CCI-002816, CCI-002817) | Section 8.1 | Annual mandatory spillage awareness training integrated into the {{ ORGANIZATION }} Learning Management System. |
| IR-09(03) | Post-spill Operations | Implement COOP procedures to ensure personnel carry out tasks during spill cleanup (CCI-002818, CCI-002819) | Section 8.2 | Invocation of {{ SYSTEM_NAME }} COOP plan, deployment of clean Google Cloud Workstations, and traffic redirection to secondary regions. |
| IR-09(04) | Exposure to Unauthorized Personnel | Employ controls for personnel exposed to unauthorized spilled information (CCI-002820, CCI-002821) | Section 8.3 | Immediate access revocation, NDA reinforcement, security debriefings, and administrative inquiry under DoDM 5200.01 Vol. 3. |
