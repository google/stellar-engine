# IR - Incident Response Policy and Procedures

## Document Governance & Approval Baseline

| Governance Metric | Policy Standard & Specification |
| :--- | :--- |
| **Document Title** | Incident Response Policy and Procedures |
| **NIST Control Family** | Incident Response (IR) |
| **Primary NIST Benchmark** | NIST SP 800-61 Rev. 2 (Computer Security Incident Handling Guide), US-CERT Guidelines |
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
> This document defines the enterprise security policy and implementation procedures for **Incident Response** under **NIST SP 800-53 Rev. 5 (IR)**.
> Technical infrastructure controls are automatically provisioned and enforced via **{{ SYSTEM_NAME }}** Terraform blueprints.
> Operational rules or contact details requiring manual confirmation are highlighted with RMF Team Callouts.


## 1. Overview

Federal agencies and organizations cannot protect the confidentiality, integrity, and availability of information in today’s highly networked systems environment without ensuring that all people involved in using and managing IT:


1. Understand their roles and responsibilities related to the organizational mission.
2. Understand the organization’s IT security policy, procedures, and practices.
3. Have at least adequate knowledge of the various management, operational, and technical controls required and available to protect the IT resources for which they are responsible.

The detailed procedures for {{ ORGANIZATION }} Incident Response Policy are the NIST SP 800-61 Rev 2 Incident Response Steps:

These Incident Response steps are complimented by the Google Cloud Incident Response Guide for accurate action for incidents in the Google Cloud {{ ORGANIZATION }} {{ SYSTEM_NAME }} environment. This document complies with requirements from NIST Special Publication 800-53 Revision 5, "Security and Privacy Controls for Federal Information Systems and Organizations". A detailed compliance matrix can be found in Appendix A, “Detailed Compliance Matrix”.


### 1.1 Purpose

The purpose of this {{ ORGANIZATION }} Incident Response Plan is to establish a comprehensive framework for identifying, analyzing, eradicating, and recovering from cybersecurity incidents within the {{ GOVERNANCE_REGIME }} Organization {{ ORGANIZATION }} {{ SYSTEM_NAME }}. By aligning with NIST SP 800-53 Revision 5 Incident Response controls, this policy aims to ultimately ensure that {{ ORGANIZATION }} maintains an Incident Response Policy that is effectively robust and addresses security incidents, minimizing organizational impact.

This policy aims to ensure that all {{ ORGANIZATION }} {{ SYSTEM_NAME }} users are equipped with the necessary knowledge and skills to understand and implement best practices regarding cybersecurity Incident Response. By providing a structured approach to awareness and training initiatives, this policy aims to enhance the organization's overall cybersecurity posture, reduce vulnerabilities, and promote a culture of continuous improvement in compliance with NIST SP 800-53 Rev. 5 and applicable {{ GOVERNANCE_REGIME }} standards. Through regular training sessions, communication strategies, and the dissemination of relevant materials, this policy seeks to empower {{ ORGANIZATION }} {{ SYSTEM_NAME }} users at all levels to contribute actively to the organization's commitment to maintaining the highest standards of information security and resilience.


### 1.2 Scope

The {{ ORGANIZATION }} Incident Response Plan encompasses all {{ ORGANIZATION }} {{ SYSTEM_NAME }} users who have access to {{ ORGANIZATION }} {{ SYSTEM_NAME }} information systems and data. This policy outlines the framework for preparing, identifying, analyzing, eradicating, and recovering from cybersecurity incidents in alignment with applicable {{ GOVERNANCE_REGIME }} guidelines (NIST SP 800-53, FedRAMP, State/Federal regulations). This applies to government employees, federal contractors, and third-party users who handle sensitive information or operate within {{ ORGANIZATION }} {{ SYSTEM_NAME }} information technology infrastructure.


### 1.3 Roles and Responsibilities

Each {{ ORGANIZATION }} {{ SYSTEM_NAME }} has an incident response team assigned to handle incidents. The roles listed in table below have been established as a requirement for the {{ ORGANIZATION }} {{ SYSTEM_NAME }}.


| Role | Responsibility | Point of Contact |
| --- | --- | --- |
| Information System Owner (ISO) | The responsibilities of the ISO are listed, but not limited to the following: - Protecting sensitive information on {{ SYSTEM_NAME }} and ensuring that {{ SYSTEM_NAME }} users know and follow Incident Response policies and procedures - Ensuring this policy is in direct alignment with regulatory requirements, industry standards, and incident response procedures - Facilitating the involvement of law enforcement and ensuring legal action is taken appropriately towards the incident - Coordinating with relevant law enforcement, state fusion centers, or agency counterintelligence organizations as required | {{ SO_NAME }} {{ SO_EMAIL }} {{ SO_PHONE }} |
| Program Manager (PM) | The responsibilities of the PM are listed, but not limited to the following: - Coordinates the incident response among the {{ ORGANIZATION }} Stakeholders - Serving as the central point of communication across all teams within {{ ORGANIZATION }}, management, stakeholders, and any applicable third parties - Enforcing the incident response timelines and managing critical resources such as personnel and budgeting for incident response utilities and activities - Overseeing and approving the incident response documentation, reporting, evidence collection, incident analyst, and risk mitigation. | {{ SO_NAME }} {{ SO_EMAIL }} {{ SO_PHONE }} |
| Information Systems Security Manager (ISSM) | The responsibilities of the ISSM are listed, but not limited to the following: - Serve as the primary cybersecurity advisor to the AO, ISO, and PM. - Directing the development, documentation, approval, dissemination of the Incident Response Plan, Policies, and Procedures - Ensuring all privileged users receive necessary technical training and that {{ SYSTEM_NAME }} users maintain proper clearances in accordance with applicable security regulations - Coordinating with {{ SYSTEM_NAME }} ISSO/ISSE to ensure that {{ SYSTEM_NAME }} and applications are continuously monitored for security-relevant events and ready for incident response procedures - Assessing proposed configuration changes for potential impact to the cybersecurity posture - Oversee and ensure that the incident response policies and procedures are reviewed and updated as needed, but not less than annually. | {{ ISSM_NAME }} {{ ISSM_EMAIL }} {{ ISSM_PHONE }} |
| Cloud Service Provider (Google) | The responsibilities of Google are listed, but not limited to the following: - Protects incident information commensurate with the impact-level of the cloud service - Maintains a satisfactory Risk Management Program for the cloud service in accordance with FedRAMP guidelines - Complies with IR guidance and requirements - Maintains a list of all current customer and proper communication channels with all AOs and 3PAOs - Notifies affected customers of information security incidents - Notifies US-CERT of information security incidents, as needed and provides the US-CERT tracking number to FedRAMP PMO as well as all applicable stakeholders of information security incidents, and provides status updates thereafter - Requests assistance from US-CERT, as needed - Provides a final report to FedRAMP PMO as well as applicable stakeholders to include agency AOs and JAB representatives after  completion of the Post-Incident activity phase of the incident response life cycle | Google Cloud Support Leadsupport-escalation@google.comGoogle Cloud Enterprise Support Portal|


### 1.4 Reviews and Updates

The {{ ORGANIZATION }} Cybersecurity Team will review the Incident Response policy and procedures at least annually. All changes and updates to this Incident Response Policy and procedure must be recorded in the Version History of this document.


### 1.5 Assumptions

The following assumptions were used when developing this Incident Response Plan:

- {{ ORGANIZATION }} {{ SYSTEM_NAME }} has  been established as a High Availability impact system in accordance with FIPS 199 / NIST SP 800-60,{{ SYSTEM_NAME }} Categorization Form

- Key {{ ORGANIZATION }} personnel have been identified and trained in their incident response and recovery roles and are available to active the Incident Response plan.

- The {{ ORGANIZATION }} Incident Response plan does not apply to emergency evacuation of personnel.


## 2. Incident Response Training

All federal employees, contractors, and third-party vendors related to {{ ORGANIZATION }} {{ SYSTEM_NAME }} must receive regular training on incident response detection, reporting, and procedures per NIST 800-61 Revision 2. All personnel involved with configuring, monitoring, handling, or overseeing the {{ ORGANIZATION }} {{ SYSTEM_NAME }} will be required to review the Google Cloud Security Incident Response Guide.

Directly from NIST SP 800-61 Revision 2:

- Specialized Training: Incident response team members shall receive specialized training on advanced incident analysis, containment techniques, and tool usage, in accordance with the requirements of NIST SP 800-53 Incident Response controls.

- Frequency of Training: Training sessions shall be conducted periodically, with refresher courses provided as needed.

  - The DoD has defined incident response training to be every 30 working days.

  - The DoD has defined refresher training to be annual.

Per NIST 800-61 Revision 2, users must be aware of policies and procedures regarding appropriate use of networks, systems, and applications. Applicable lessons learned from previous incidents are shared with users to see how actions could affect the organization. Improving user awareness regarding incidents should reduce the frequency of incidents. All applicable team members are trained to maintain their networks, systems, and applications in accordance with the organization’s security standards.

{{ ORGANIZATION }} incorporates simulated events into the incident response training in order to facilitate effective response by their personnel in crisis situations. In addition to simulated events, automated mechanisms can provide a more thorough and realistic incident response training environment. {{ ORGANIZATION }} must ensure all personnel training is associated with their assigned roles and responsibilities to ensure that the appropriate content is included.



### 2.1 Google Cloud Platform (GCP) Inherited Controls & Shared Responsibility Boundary

- **Google Inherited Controls**: Google Cloud maintains 24x7 Incident Response Teams (`IR-4`, `IR-5`), physical security incident handling, and immediate notification to {{ ORGANIZATION }} for CSP infrastructure incidents (`IR-6`).
- **Customer Implementation Responsibilities**: {{ ORGANIZATION }} is responsible for maintaining the Incident Response Plan (`IR-8`), executing incident handling procedures (`IR-4`), reporting incidents to US-CERT / DISA within 1 hour (`IR-6`), and conducting annual Incident Response tabletop exercises (`IR-3`).

## 3. Incident Response Testing

Every 365 days (annually){{ ORGANIZATION }} conducts incident response testing to determine the overall incident response effectiveness, identify potential weaknesses or deficiencies in daily organizational operations, and record  results in a Lessons Learned document. Incident Response Testing is done via the following “Test, Training, and Exercise Program” outlined in NIST SP 800-84.

{{ ORGANIZATION }} involves at least one of the following Incident Response Testing Methods from NIST SP 800-84:

- Incident Response Testing Checklist from NIST 800-61 Revision 2

- Functional or Tabletop Exercises

  - Functional: Personnel with operational responsibilities validate their IT plans and their operational readiness for emergencies in a simulated operational environment through exercising their roles and responsibilities of specific team members, procedures, and assets involved in one or more functional aspects of the Incident Response Plan.

  - Tabletop: All personnel with roles and responsibilities in the Incident Response Plan meet in a classroom setting or in a remote virtual conference to validate the Incident Response Plan contents through only discussion of their roles during emergencies and their responses to emergency situations. No deploying of equipment or any other resources are necessary.


### 3.1 Coordination with Related Plans

The {{ ORGANIZATION }} Incident Response Testing is implemented in coordination with the Google Cloud Security Incident Response Guide and any additional organizational Incident Response plans.


## 4. Incident Handling

{{ ORGANIZATION }} implements an Incident Handling process per NIST SP 800-61 Revision 2 for security incidents using the following steps:


#### 4.1.1 Preparation

{{ ORGANIZATION }} preparation involves enabling detective controls, verifying appropriate access to applicable tools and cloud services necessary, and preparing necessary playbooks (both manual and automated) to verify reliable and consistent responses.

Incident Handler Communications and Facilities:

- The {{ ORGANIZATION }} Incident Tracking System will triage incident information, timestamps, and overall incident status.

Incident Analysis Hardware and Software:

- {{ ORGANIZATION }} produces backup virtual assets through Google Cloud and preserves log files and other relevant data.

- Sandbox environments are in place for any form of testing, including static or dynamic malware analysis.

Incident Analysis Resources:

- {{ ORGANIZATION }} possesses updated network diagrams, port listings, hardware and software list, and security baseline configurations for the resources used within {{ ORGANIZATION }} {{ SYSTEM_NAME }}.

- {{ ORGANIZATION }} will use Google Cloud KMS for encryption of application activity.


#### 4.1.2 Detection and Analysis

{{ ORGANIZATION }} incident detection methods involve the {{ INTRUSION_DETECTION_SYSTEM }} to detect and analyze potential, dormant, or active anomalies within {{ ORGANIZATION }} {{ SYSTEM_NAME }}. Incidents in {{ ORGANIZATION }} {{ SYSTEM_NAME }}  may also be detected manually via incidents reported by users.

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

{{ ORGANIZATION }} learns and improves from all incidents using “Lessons Learned” documentation and scheduled meetings with all parties involved from the incident to allow for direct closure with respect to the incident that occurred.

Lessons learned questions from NIST SP 800-61 Revision 2 include:

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

{{ ORGANIZATION }} {{ SYSTEM_NAME }} has been established as a High Availability impact system in accordance with FIPS 199 / NIST SP 800-60,{{ SYSTEM_NAME }} Categorization Form. {{ SYSTEM_NAME }} follows the actions provided by {{ ORGANIZATION }} in response to incidents to ensure continuation of mission and business functions.


### 4.4 Information Correlation

The following are all audit logs that are collected and stored within Google Cloud; {{ ORGANIZATION }} utilizes the logs to correlate the incident information and incident response to achieve perspective on the incident awareness and response.

Activity Logs - Admin Activity audit logs contain log entries for API calls or other actions that modify the configuration or metadata of resources. For example, these logs record when users create VM instances or change Identity and Access Management permissions.

Data Access Logs -Data Access audit logs contain API calls that read the configuration or metadata of resources, as well as user-driven API calls that create, modify, or read user-provided resource data.

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

{{ SYSTEM_NAME }} follows the actions provided by {{ ORGANIZATION }} to ensure intra-organizational coordination and communication is maintained throughout the lifecycle of an incident.


### 4.7 Correlation with External Organizations

{{ SYSTEM_NAME }} follows the actions provided by {{ ORGANIZATION }} to ensure external organization coordination and communication is maintained throughout the lifecycle of an incident.

{{ ORGANIZATION }} {{ SYSTEM_NAME }} communicates incidents with the following external organizations:

- Defense Information Systems Agency (DISA)

- Federal Risk and Authorization Management Program (FedRAMP PMO)

Information of significant threat detections and incidents of compromise are shared by the {{ SYSTEM_NAME }} ISO to the above defined external organizations via email, phone, or video call.

Effective collaboration with external organizations enhances the incident response capabilities and strengthens cybersecurity defenses in the {{ SYSTEM_NAME }} and {{ SYSTEM_NAME }} environments. Failure to comply diminishes the efforts of communication to promptly address incidents that occur within {{ SYSTEM_NAME }}.


### 4.8 Supply Chain Coordination

{{ SYSTEM_NAME }} follows the actions provided by {{ ORGANIZATION }} to ensure external organization coordination and communication is maintained throughout the lifecycle of an incident, to include activities involving supply chain events with other organizations involved in the supply chain.


### 4.9 Integrated Incident Response Team

The Integrated Incident Response Team for {{ SYSTEM_NAME }} will be maintained by {{ ORGANIZATION }}.


### 4.10 Malicious Code and Forensic Analysis

The forensic analysis and analysis of malicious code and/or other residual artifacts remaining in the system after an incident is the responsibility of  {{ ORGANIZATION }}.


### 4.11 Behavior Analysis

The analysis of behaviors in an environment targeted by adversaries is the responsibility of {{ ORGANIZATION }}.


### 4.12 Security Operations Center

Refer to Section 4.2 for more information on {{ THREAT_DETECTION_ENGINE }} and {{ SIEM_TOOL }} maintained by {{ ORGANIZATION }}.


## 5. Incident Monitoring

Monitoring incidents includes maintaining records about each incident, the status of the incident, and other pertinent information necessary for forensics as well as evaluating incident details, trends, and handling. Incident information can be obtained from a variety of sources, including network monitoring, incident reports, incident response teams, user complaints, supply chain partners, audit monitoring, physical access monitoring, and user and administrator reports. Incident monitoring and documenting procedures will be included in the associated in the RMF package and aligned with the {{ ORGANIZATION }} program incident monitoring process.

{{ ORGANIZATION }} {{ SYSTEM_NAME }} utilizes {{ THREAT_DETECTION_ENGINE }} and {{ SIEM_TOOL }} for automated tracking, data collection, and analysis. Refer to the {{ SYSTEM_NAME }} Technical Design Document and Section 4.2 for additional information.


#### 5.1.1 Formal Incident Escalation & SLA Timelines (`IR-6`)

{{ INCIDENT_ESCALATION_IMPLEMENTATION }}


### 5.2 Automated Reporting

The automation of incident reporting processes streamlines response efforts to ensure compliance with automated reporting requirements. Failure to comply with automotive incident monitoring diminishes the efforts to promptly address incidents that occur, delaying communication to relevant stakeholders.

{{ ORGANIZATION }} {{ SYSTEM_NAME }} implements the following automated reporting mechanisms:

#### 5.2.1 Automated Alerting & Incident Monitoring Integration (`IR-4`, `IR-6`)

{{ ORGANIZATION }} leverages automated security monitoring and alerting tools in {{ SYSTEM_NAME }} to ensure instant notification of security events:

1. **Real-Time Threat & Finding Exports**: Automated security finding notifications from {{ THREAT_DETECTION_ENGINE }} are routed in real time via {{ TELEMETRY_PIPELINE }} and Pub/Sub to Cloud Functions / Eventarc triggers, creating high-priority tickets in {{ ITSM_SYSTEM }} (`IR-4`).
2. **SIEM / Log Sink Integration**: Critical security events (e.g., IAM permission changes, VPC firewall modifications, KMS key deletion attempts) trigger automated notifications in {{ SIEM_TOOL }} and alerts to on-call DevSecOps personnel (`AU-6`, `IR-6`).
3. **Automated US-CERT API Submission**: High-severity incident tickets generate structured JSON alerts formatted for rapid submission to federal reporting bodies in compliance with US-CERT Guidelines (`IR-6`).


### 5.3 Vulnerabilities Related to Incidents

Regular vulnerability assessments and vulnerability scans are conducted against {{ SYSTEM_NAME }} and {{ SYSTEM_NAME }} to appropriately identify, categorize, and remediate all relevant security vulnerabilities that are subject to exploitation during cybersecurity incidents.

Managing vulnerabilities related to incidentes reduces the likelihood of exploitation and resilience to cybersecurity incidents in {{ SYSTEM_NAME }} and the Google Cloud environment.

Failure to comply with reporting and remediation of the identified vulnerabilities diminishes the efforts to promptly address security incidents that may occur, delaying communication to relevant stakeholders.


### 5.4 Supply Chain Coordination

{{ ORGANIZATION }} will promptly report cybersecurity incidents to the provider of the product or service that is impacted. {{ ORGANIZATION }} follows the following process when coordinating with providers of products or services that are impacted by cybersecurity incidents:

#### 5.4.1 Third-Party & Cloud Provider Incident Coordination (`IR-6`, `SR-3`)

When a security incident originates from or impacts a third-party software component, open-source Terraform module, or Google Cloud infrastructure service:

1. **Google Support & Incident Escalation**: Security incidents involving underlying GCP platform services (`google_compute_network`, `google_container_cluster`, `google_kms_crypto_key`) are reported immediately to Google Cloud Support via dedicated Premier Support ticket channels and Google Security Operations (`IR-6`).
2. **Software Vendor Notification**: Incidents involving third-party commercial software modules or containers are reported to vendor security contacts within **4 hours** of identification (`SR-3`).
3. **Supply Chain Exposure Analysis**: The ISSO evaluates all deployed Terraform modules (`{{ TERRAFORM_MODULES }}`) and container images in Artifact Registry to determine if secondary applications or environments share the vulnerable component (`SR-11`).


## 6. Incident Response Assistance

The {{ ORGANIZATION }} cyber team provides incident response support resources including help desks, assistance groups, automated ticketing systems to open and track incident response tickets, and access to forensics services, when required.

{{ ORGANIZATION }} works closely with external providers including the federal/state regulatory authorities, Google, and key public sector partners to ultimately develop and implement security measures aligned with business objectives and regulatory requirements regarding {{ ORGANIZATION }} Incident Response to leverage many external expertise and resources. The exchange of information established through regular communication channels are to stay abreast of security threats and maintain proper coordination of response efforts. Strong partnerships enable proactive identification and resolution of security issues while promoting organizational resilience.


## 7. Incident Response Methodology

> [!IMPORTANT]
> <mark style="background-color: #fff9c4; color: #b71c1c; font-weight: bold; padding: 2px 6px; border-radius: 4px;">RMF TEAM ACTION REQUIRED: Verify and update operational contact/procedure details in this section.</mark>
> {{ ORGANIZATION }} develops, disseminates, and maintains the Incident Response Plan that ultimately defines roles, responsibilities, and procedures for {{ ORGANIZATION }} incident response procedures of detection, analysis, containment, eradication, recovery, and post-incident activities. This Incident Response Plan compiles the usage of NIST SP 800-53 Incident Response (IR) Security Control family, Google best security practices, industry standards, and lessons learned from previous incidents and exercises. The ISSM oversees the development, documentation, implementation, approval, and dissemination of the {{ ORGANIZATION }} Cybersecurity Incident Response Plan.

Reportable incidents in {{ ORGANIZATION }} are identified as (but not limited to) the following CJCSM 6510.01B Table B-A-2:


| Category | Category  Description |
| --- | --- |
| 0 | Training and Exercises — Operations performed for training purposes |
| 1 | Root Level Intrusion (Incident) — Unauthorized privileged access to an IS.  Privileged access, often referred to as administrative or root access, provides unrestricted access to the IS.  This category includes unauthorized access to information or unauthorized access to account credentials that could be used to perform administrative functions (e.g., domain administrator).  If the IS is compromised with malicious code that provides remote interactive control, it will be reported in this category. |
| 2 | User Level Intrusion (Incident) — Unauthorized non-privileged access to an IS.  Non-privileged access, often referred to as user level access, provides restricted access to the IS based on the privileges granted to the user.  This includes unauthorized access to information or unauthorized access to account credentials that could be used to perform user functions such as accessing Web applications, Web portals, or other similar information resources.  If the IS is compromised with malicious code that provides remote interactive control, it will be reported in this category. |
| 3 | Unsuccessful Activity Attempt (Event) — Deliberate attempts to gain unauthorized access to an IS that are defeated by normal defensive mechanisms.  Attacker fails to gain access to the IS (i.e., attacker attempts valid or potentially valid username and password combinations) and the activity cannot be characterized as exploratory scanning.  Reporting of these events is critical for the gathering of useful effects-based metrics for commanders.  Note the above CAT 3 explanation does not cover the “run-of-themill” virus that is defeated/deleted by AV software.  “Run-of-themill” viruses that are defeated/deleted by AV software are not reportable events or incidents. |
| 4 | Denial of Service (Incident) — Activity that denies, degrades, or disrupts normal functionality of an IS or organization network infrastructure. |
| 5 | Non-Compliance Activity (Event) — Activity that potentially exposes ISs to increased risk as a result of the action or inaction of authorized users.  This includes administrative and user actions such as failure to apply security patches, connections across |
| 6 | Reconnaissance (Event) — Activity that seeks to gather information used to characterize ISs, applications, organization network infrastructures, and users that may be useful in formulating an attack.  This includes activity such as mapping organization network infrastructures, IS devices and applications, interconnectivity, and their users or reporting structure.  This activity does not directly result in a compromise. |
| 7 | Malicious Logic (Incident) — Installation of software designed and/or deployed by adversaries with malicious intentions for the purpose of gaining access to resources or information without the consent or knowledge of the user.  This only includes malicious code that does not provide remote interactive control of the compromised IS.  Malicious code that has allowed interactive access should be categorized as Category 1 or Category 2 incidents, not Category 7.  Interactive active access may include automated tools that establish an open channel of communications to and/or from an IS. |
| 8 | Investigating (Event) — Events that are potentially malicious or anomalous activity deemed suspicious and warrant, or are undergoing, further review.  No event will be closed out as a Category 8.  Category 8 will be recategorized to appropriate Category 1-7 or 9 prior to closure. |
| 9 | Explained Anomaly (Event) — Suspicious events that after further investigation are determined to be non-malicious activity and do not fit the criteria for any other categories.  This includes events such as IS malfunctions and false alarms.  When reporting these events, the reason for which it cannot be otherwise categorized must be clearly specified. |

Adherence to the {{ ORGANIZATION }} Incident Response Plan ensures a coordinated and consistent approach to incident response activities for the Google Cloud environment, enhancing the ability to mitigate, monitor, and manage the impact of cybersecurity incidents while maintaining continuity of operations.


## 8. Information Spillage Response

{{ ORGANIZATION }} has the responsibility to report and escalate any form of spillage that is detected and reported. Spillages are not to be hidden or handled in secret in order to save organizational embarrassment.

All known or suspected instances of data spillages are to be reported and full cooperation is to be rendered during any investigation.

> [!IMPORTANT]
> <mark style="background-color: #fff9c4; color: #b71c1c; font-weight: bold; padding: 2px 6px; border-radius: 4px;">RMF TEAM ACTION REQUIRED: Verify and update operational contact/procedure details in this section.</mark>
> Thorough investigations are to be conducted to determine the cause of any spillage incident. Depending on the level of data spillage, external communications to applicable federal, state, or local law enforcement agencies are done by the {{ ORGANIZATION }} {{ SYSTEM_NAME }} ISO for legal handling of that incident.

For any security incident, {{ SYSTEM_NAME }} is subject to isolation and will be processed according through the methods outlined in this policy, as well as any additional {{ ORGANIZATION }} Incident Response policies.


### 8.1 Training

{{ ORGANIZATION }} is responsible for ensuring all {{ SYSTEM_NAME }} users are trained on the reporting procedures for information spillage. Training must occur at least annually.


#### 8.1.1 Post-Spill Operational Procedures & Remediation Workflow

In accordance with NIST SP 800-53 Rev. 5 (`IR-9`), CNSSI 1001, and NIST SP 800-61 / US-CERT / CISA incident handling guidelines, {{ ORGANIZATION }} enforces the following 7-stage post-spill remediation protocol whenever higher-classification or unauthorized data is spilled into {{ SYSTEM_NAME }}:

1. **Immediate Resource Containment & Isolation (`IR-9(1)`)**:
   - Immediately isolate affected GCP Cloud Storage buckets, GKE pods, Persistent Disks, or Compute Engine VMs by applying strict VPC Service Control perimeters and revoking all IAM data access permissions.
   - Halt all automated backup jobs, cross-region storage replication (`CP-9`), and log export sinks (`AU-4`) associated with the spilled data path to prevent secondary contamination.

2. **Out-of-Band Incident Alerting (`IR-9(3)`)**:
   - Notify the ISSO, ISSM, System Owner (`{{ SO_NAME }}`), and Authorizing Official (`{{ AO_NAME }}`) within **15 minutes** of spill confirmation.
   - All notifications must occur via secure out-of-band communication channels (e.g., dedicated secure voice line or out-of-band encrypted messaging) to ensure compromised system channels are not utilized.

3. **Forensic Identification & Spill Scope Analysis**:
   - Review Cloud Audit Logs (`AU-2`, `AU-3`) and Cloud Monitoring network flow logs (`AU-6`) to identify the exact timestamp, source IP, authenticated user ID, and full list of accessed objects/records involved in the spill.
   - Identify all downstream destinations, cache layers, or endpoint workstations that ingested or cached the spilled data.

4. **Cloud Media Sanitization & Cryptographic Destruction (`MP-6`, `SC-28`)**:
   - Perform logical sanitization and purge of contaminated Cloud Storage objects, SQL tables, and persistent disk sectors in strict compliance with NIST SP 800-88 Rev. 1 Guidelines for Media Sanitization.
   - If Customer-Managed Encryption Keys (CMEK) were utilized for the contaminated data store, execute immediate key destruction or rotation in Cloud KMS (`SC-12`, `SC-28`) to render any un-sanitized physical storage fragments permanently unreadable.

5. **Operational Continuity for Impacted Personnel (`IR-9(3)`)**:
   - Provide un-contaminated replacement endpoint hardware or isolated cloud workstations (`Cloud Workstations`) to impacted personnel to ensure mission-essential tasks continue while contaminated environments undergo remediation.

6. **Mandatory External Incident Escalation (`IR-6`)**:
   - Submit a formal Information Spillage Incident Summary Report to US-CERT, DISA, and the Authorizing Official within **24 hours** of incident verification, detailing the spill scope, data classification level, and containment actions taken.

7. **Root Cause Analysis (RCA) & POA&M Remediation (`CA-5`, `IR-8`)**:
   - Conduct a formal Post-Mortem Root Cause Analysis within **5 business days** of containment.
   - Document corrective actions, IAM policy updates, and automated VPC perimeter enhancements in the System Plan of Action and Milestones (POA&M) (`CA-5`) to permanently prevent recurrence of similar spillage incidents.


### 8.2 Exposure to Unauthorized Personnel

{{ SYSTEM_NAME }} and {{ SYSTEM_NAME }} implement access controls, encryption, and authentication mechanisms within GCP to prevent unauthorized access to sensitive information.



## Appendix A – Detailed Compliance Matrix

The following table provides detailed traceability between the policy implementation statements in this document, the authoritative NIST SP 800-53 Rev. 5 control requirements, DoD CCIs, and the technical/governance enforcement mechanisms active across {{ SYSTEM_NAME }}.


| CTRL ID | CTRLTITLE | REQUIRED eMASS STANDARD | DOCREF | ENFORCEMENT MECHANISM |
| :--- | :--- | :--- | :--- | :--- |
| IR-01 | Policy and Procedures | Develop, document, disseminate, review, and update incident response policy and operational procedures (CCIs: 000805, 000806, 000807, 000808, 000809, 000810, 000811, 000812, 002776, 002777, 004109, 004110, 004111, 004112, 004113, 004114, 004115, 004116) | Section 2.1 | Formal {{ ORGANIZATION }} policy issuance, ISSM governance workflows, eMASS artifact repositories, and annual review tracking via NetOps. |
| IR-02 | Incident Response Training | Provide role-based incident response training to system users within 30 days of role assumption and at least annually thereafter (CCIs: 000813, 000814, 000815, 002778, 002779, 005151, 005152, 005153) | Section 2.2 | Automated LMS tracking, role-based training modules on Google Cloud and DoD incident handling, and ISSM annual curriculum audits. |
| IR-02(03) | Breach Identification | Train system personnel to identify and respond to data breaches and unauthorized disclosures of sensitive data/PII (CCI: 004118) | Section 2.2 | DoD Cyber Awareness Challenge, specialized GCP audit log inspection curricula, and mandatory PII/CUI breach response training. |
| IR-03 | Incident Response Testing | Test incident response capability effectiveness every 6 months for HA components and annually using defined tests (CCIs: 000818, 000819, 000820) | Section 2.3 | Bi-annual tabletop exercises (TTX) and live functional failover simulations in sandboxed test projects. |
| IR-03(02) | Coordination with Related Plans | Coordinate incident response testing with organizational elements responsible for related plans (CCI: 002780) | Section 2.3 | Cross-functional exercise coordination with cyber operations commands, {{ ORGANIZATION }} NetOps, DISA CSSP, {{ SYSTEM_NAME }} COOP/DR teams, and Google Public Sector. |
| IR-04 | Incident Handling | Implement an incident handling capability for incidents consistent with the IRP, CP coordination, and lessons learned (CCIs: 000822, 000823, 001625, 004130, 004131, 004132, 004133, 004134, 004135, 004136) | Section 2.4 | 6-Phase NIST SP 800-61 Rev. 2 lifecycle, automated GCP Cloud Logging sinks, BigQuery analytics, and Terraform IaC rollback playbooks. |
| IR-04(01) | Automated Incident Handling Processes | Support incident handling using automated mechanisms including SIEM, SOAR, EDR, and NAC (CCIs: 000825, 004137) | Section 2.4 | Cloud Logging sinks routing to Pub/Sub, BigQuery, SOAR playbooks, IAM credential revocation, and automated VPC-SC firewall rules. |
| IR-04(03) | Continuity of Operations | Identify incident classes (CJCSM 6510.01B) and execute actions ensuring mission continuity (CCIs: 000827, 000828, 004139, 004140) | Section 2.4 | Dynamic BGP multi-region route failover, redundant {{ INTERCONNECT_TYPE }} circuits, and HA Cloud VPN gateways. |
| IR-04(04) | Information Correlation | Correlate incident information and responses to achieve an organization-wide perspective (CCI: 000829) | Section 2.4 | BigQuery SQL analytical views aggregating VPC Flow Logs, boundary firewall logs, and {{ CSSP_PROVIDER }} centralized correlation. |
| IR-04(06) | Insider Threats | Implement incident handling capability for insider threats (CCI: 002782) | Section 2.4 | GCP PAM Just-In-Time access, intra-project separation of duties via Resource Manager Tags, and immutable Cloud Audit Logs. |
| IR-04(07) | Insider Threats: Intra-Organization Coordination | Coordinate insider threat incident handling with SAOP and key cybersecurity personnel (CCIs: 004141, 004142) | Section 2.4 | Integrated escalation workflows with {{ ORGANIZATION }} Provost Marshal, Counterintelligence (CI), SAOP, and {{ CSSP_PROVIDER }} insider threat analysts. |
| IR-04(08) | Correlation with External Organizations | Coordinate with external organizations (US-CERT, DoD CERT, DISA) to correlate and share compromise data (CCIs: 002785, 002786, 002787) | Section 2.4 | Out-of-band communications, automated US-CERT JSON reporting gateways, and DISA/FedRAMP PMO coordination channels. |
| IR-04(12) | Malicious Code and Forensic Analysis | Analyze malicious code and residual artifacts remaining in the system after an incident (CCI: 004145) | Section 2.4 | Isolated forensic analysis sandboxes in dedicated staging projects, GCS disk snapshot acquisitions, and volatile memory inspection tooling. |
| IR-04(13) | Behavior Analysis | Analyze anomalous or suspected adversarial behavior across network traffic, process logs, and auth logs (CCIs: 004146, 004147) | Section 2.4 | Continuous behavioral inspection using BigQuery streaming analytics, network telemetry, and {{ IDENTITY_PROVIDER }} sign-in log analysis. |
| IR-04(14) | Security Operations Center | Establish and maintain a security operations center (CCI: 004148) | Section 2.4 | 24x7x365 {{ ORGANIZATION }} NetOps and accredited CSSP Security Operations Center monitoring per DoDI 8530.01. |
| IR-05 | Incident Monitoring | Track and document incidents across the system lifecycle (CCI: 000832) | Section 2.5 | Immutable incident logging in {{ ITSM_SYSTEM }}, BigQuery audit data warehouse, and eMASS POA&M tracking. |
| IR-05(01) | Automated Tracking, Data Collection, and Analysis | Track incidents and collect/analyze incident data using SIEM and automated ticketing (CCIs: 004151, 004152, 004153, 004154) | Section 2.5 | Automated Cloud Monitoring alert policies, Pub/Sub event ingestion, and {{ SIEM_TOOL }} ticket auto-generation. |
| IR-06 | Incident Reporting | Report suspected incidents within 2 hours to designated authorities (US-CERT, DISA, AO) (CCIs: 000834, 000835, 000836, 002791) | Section 2.6 | Formal multi-tiered SLA matrix (1-hr CAT 1, 2-hr CAT 2), automated alerting, and out-of-band command notifications. |
| IR-06(01) | Automated Reporting | Report incidents using automated SOAR and ITSM integration (CCIs: 000837, 004155) | Section 2.6 | SOAR pipeline integration with {{ ITSM_SYSTEM }} for automated notification dispatch and JSON report creation. |
| IR-06(02) | Vulnerabilities Related to Incidents | Report system vulnerabilities associated with incidents to the ISSM and AO (CCIs: 000838, 002792) | Section 2.6 | Automated CI/CD scan findings (Semgrep, Checkov, tfsec) and ACAS vulnerability mapping to eMASS POA&M entries. |
| IR-06(03) | Supply Chain Coordination | Provide incident information to supply chain organizations and CSP providers (CCIs: 002793, 004156) | Section 2.6 | Automated escalation tickets to Google Cloud Premier Support and hardware/software vendor security response centers. |
| IR-07 | Incident Response Assistance | Provide integral incident response support resources including help desks and forensics (CCI: 000839) | Section 2.7 | 24x7 NetOps operational help desk, automated service portal, and dedicated forensic engineering support teams. |
| IR-07(01) | Automation Support for Information Availability | Increase availability of incident info and support using automated portals and ticketing (CCI: 005154) | Section 2.7 | Centralized knowledge portal, automated Jira/ServiceNow runbooks, and Google Cloud documentation repositories. |
| IR-07(02) | Coordination with External Providers | Establish direct relationships with external providers and identify IR team members (CCIs: 000841, 000842) | Section 2.7 | Established Enterprise Support agreements with Google Cloud, colocation facility providers, and carriers, with designated ISSM/ISSO POC rosters. |
| IR-08 | Incident Response Plan | Develop, review, approve, update, and protect the Incident Response Plan (CCIs: 000844, 000845, 000846, 000849, 000850, 002795, 002796, 002797, 002798, 002799, 002800, 002801, 002802, 002803, 002804, 004157, 004158, 004159) | Section 2.8 | Formally approved {{ SYSTEM_NAME }} IRP document, annual AO approval, {{ IDENTITY_PROVIDER }} with {{ MFA_MECHANISM }} access controls, and Cloud KMS CMEK storage encryption. |
| IR-08(01) | Breaches Involving PII | Include processes for breach assessment, harm determination, and privacy oversight notification (CCIs: 004160, 004161, 004162) | Section 2.8 | OMB M-17-12 harm assessment framework, SAOP coordination protocols, and automated affected-party notification workflows. |
| IR-09 | Information Spillage Response | Implement 7-stage spillage workflow: assign roles, identify data, alert out-of-band, isolate, eradicate, and damage assessment (CCIs: 002805, 002806, 002807, 002808, 002809, 002810, 002811, 002812, 004163, 004164) | Section 2.9 | Out-of-band notification, VPC Service Control boundary enforcement, NIST SP 800-88 Rev. 1 media sanitization, and Cloud KMS key destruction. |
| IR-09(02) | Training | Provide information spillage response training annually consistent with IR-02 (CCIs: 002816, 002817) | Section 2.9 | Annual mandatory spillage awareness training integrated into the {{ ORGANIZATION }} Learning Management System. |
| IR-09(03) | Post-Spill Operations | Implement COOP procedures to ensure personnel carry out tasks during spill cleanup (CCIs: 002818, 002819) | Section 2.9 | Invocation of {{ SYSTEM_NAME }} COOP plan, deployment of clean Google Cloud Workstations, and traffic redirection to secondary regions. |
| IR-09(04) | Exposure to Unauthorized Personnel | Employ controls for personnel exposed to unauthorized spilled information (CCIs: 002820, 002821) | Section 2.9 | Immediate access revocation, NDA reinforcement, security debriefings, and administrative inquiry under DoDM 5200.01 Vol. 3. |
