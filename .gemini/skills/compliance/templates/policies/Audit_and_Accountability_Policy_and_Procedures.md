# AU - Audit and Accountability Policy and Procedures

## Document Governance & Approval Baseline

| Governance Metric | Policy Standard & Specification |
| :--- | :--- |
| **Document Title** | Audit and Accountability Policy and Procedures |
| **NIST Control Family** | Audit and Accountability (AU) |
| **Primary NIST Benchmark** | NIST SP 800-92 (Computer Security Log Management), NIST SP 800-53 Rev. 5 (AU Family) |
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
> This document defines the enterprise security policy and implementation procedures for **Audit and Accountability** under **NIST SP 800-53 Rev. 5 (AU)**.
> Technical infrastructure controls are automatically provisioned and enforced via **{{ SYSTEM_NAME }}** Terraform blueprints.
> Operational rules or contact details requiring manual confirmation are highlighted with RMF Team Callouts.


## 1. Overview

Federal agencies and organizations cannot protect the confidentiality, integrity, and availability of information in today's highly networked systems environment without ensuring that all people involved in using and managing IT:

1. Understand their roles and responsibilities related to the organizational mission;
2. Understand the organization's IT security policy, procedures, and practices; and
3. Have at least adequate knowledge of the various management, operational, and technical controls required and available to protect the IT resources for which they are responsible.

The purpose of this Audit and Accountability Policy is to establish the requirements for generating, protecting, retaining, reviewing, and analyzing audit records for {{ SYSTEM_NAME }} so that system activity can be monitored and individual users can be held accountable for their actions.

This policy addresses the Audit and Accountability (AU) family requirements of NIST Special Publication 800-53 Revision 5, "Security and Privacy Controls for Information Systems and Organizations." A detailed compliance matrix is provided in Appendix A, "Detailed Compliance Matrix."

The Audit and Accountability Policy encompasses all {{ ORGANIZATION }} users who have access to {{ SYSTEM_NAME }}. This policy outlines the framework for establishing, implementing, and maintaining audit logging and accountability in alignment with applicable {{ GOVERNANCE_REGIME }} guidelines (NIST SP 800-53, FedRAMP, and applicable federal and state regulations), and is consistent with applicable laws, executive orders, directives, regulations, policies, standards, and guidelines. It applies to employees, contractors, and third-party users who handle sensitive information or operate within the {{ ORGANIZATION }} {{ SYSTEM_NAME }} information technology infrastructure.

{{ ORGANIZATION }} management is committed to the requirements of this policy and provides the resources needed to implement them. The ISSM ({{ ISSM_NAME }}) manages the development, documentation, and dissemination of this policy and its procedures, and coordinates their implementation with the Authorizing Official, System Owner, ISSO, and other organizational entities identified in the Program Roles & Responsibilities Matrix.

This policy and its procedures are reviewed and updated at least annually and following significant changes to {{ SYSTEM_NAME }} or its operating environment, security or privacy incidents, assessment or audit findings, or changes in applicable laws, executive orders, directives, regulations, policies, standards, or guidelines.


## 2. Event Logging

Google Cloud allows {{ ORGANIZATION }} developers to write code and manage cloud resources, including which audit logs are generated and how long they are retained. {{ ORGANIZATION }} is responsible for selecting the auditable events for {{ SYSTEM_NAME }} and ensuring that they are logged.

An event is any observable occurrence in an information system. The types of events that require logging are those events that are significant and relevant to the security of systems and the privacy of individuals. Event logging also supports specific monitoring and auditing needs. Event types include password changes, failed logons or failed accesses related to systems, security or privacy attribute changes, administrative privilege usage, PIV credential usage, data action changes, query parameters, or external credential usage.


**Audit Logs**

The following are all audit logs that are collected and stored within Google Cloud:

Admin Activity Logs - Admin Activity audit logs contain log entries for API calls or other actions that modify the configuration or metadata of resources. For example, these logs record when users create VM instances or change Identity and Access Management permissions.

Data Access Logs - Data Access audit logs contain API calls that read the configuration or metadata of resources, as well as user-driven API calls that create, modify, or read user-provided resource data.

System Event Logs - System Event audit logs contain log entries for Google Cloud actions that modify the configuration of resources. System Event audit logs are generated by Google systems; they aren't driven by direct user action.


**Other Logs**

VPC Flow Logs - VPC Flow Logs record a sample of network flows sent from and received by VM instances, including instances used as GKE nodes. These logs can be used for network monitoring, forensics, real-time security analysis, and expense optimization.

Firewall Rule Logs - Firewall Rules Logging lets you audit, verify, and analyze the effects of your firewall rules. For example, you can determine if a firewall rule designed to deny traffic is functioning as intended. Firewall Rules Logging is also useful if you need to determine how many connections are affected by a given firewall rule.

Access Transparency Logs - Access Transparency logs include data about Google staff activity, including:

- Actions by the Support team that you may have requested by phone

- Basic engineering investigations into your support requests

- Other investigations made for valid business purposes, such as recovering from an outage


**Log Destinations**

Log sinks route audit logs and other logs to the following destinations:

- BigQuery

- Cloud Storage

- Pub/Sub

When a log destination is in a different project, {{ ORGANIZATION }} grants the log sink's writer identity (service account) permission to write to that destination. If VPC Service Controls or other restrictions apply, {{ ORGANIZATION }} also grants the writer identity access through them.

{{ ORGANIZATION }} will enable the audit capability for the execution of privileged functions on {{ SYSTEM_NAME }}. {{ TELEMETRY_PIPELINE }} forwards audit records to {{ EXTERNAL_SIEM }} ({{ CSSP_PROVIDER }}) and centralized audit sinks via Pub/Sub.


### 2.1 Google Cloud Inherited Controls & Shared Responsibility Boundary

- **Google Inherited Controls**: Google Cloud provides underlying infrastructure log collection, physical server audit trails, and hardware-level audit logging for all CSP operations (`AU-2`, `AU-3`, `AU-12`).
- **Customer Implementation Responsibilities**: {{ ORGANIZATION }} is responsible for enabling Admin Activity and Data Access Audit Logs (`AU-2`, `AU-3`), configuring Cloud Logging log sinks to BigQuery / GCS buckets (`AU-4`, `AU-9`), enforcing at least 90 days online (hot) retention and NARA-compliant offline archival per FedRAMP `AU-11` (or at least 12 months active storage plus 18 months cold storage [30 months total] for federal civilian agencies subject to OMB M-21-31), and automated SIEM log review (`AU-6`).

## 3. Content of Audit Records

Google Cloud allows {{ ORGANIZATION }} developers and cloud engineers to manage cloud resources and define what audit records are generated across system boundaries. The {{ SYSTEM_NAME }} admin activity log produces audit records that contain sufficient information to, at a minimum, establish what type of event occurred, when (date and time) the event occurred, the source of the event, the outcome of the event, and the identity of any user/subject associated with the event. In the case of the admin activity log, "where the event occurred" is captured as occurring within {{ ORGANIZATION }} Google Cloud projects, folders, and organizations. In addition to admin logs, application activity logs are captured in Cloud Logging, and application teams maintain the capability to define and customize application-level audit logging.

{{ AUDIT_AND_SIEM_IMPLEMENTATION }}


### 3.1 Additional Audit Information

Google Cloud allows {{ ORGANIZATION }} to determine which audit logs are generated and how long they are retained. Admin Activity and Data Access audit logs include the event start time, end time, request IP address and user agent, request payload, user identity, and the objects or resources being acted upon. {{ ORGANIZATION }} is responsible for configuring {{ SYSTEM_NAME }} to also record additional session-specific information, such as bytes transferred during a session, that can help during an investigation or inquiry.


### 3.2 Limit Personally Identifiable Information Elements

{{ ORGANIZATION }} limits personally identifiable information (PII) in audit records to the elements identified in the privacy risk assessment (Privacy Impact Assessment): user ID, {{ USER_IDENTIFIER_TYPE }}, and terminal ID. Cloud DLP inspection templates, PII redaction filters, and payload exclusion filters keep other PII out of audit records.


## 4. Audit Log Storage Capacity

{{ ORGANIZATION }} manages cloud resources and log retention policies for {{ SYSTEM_NAME }}. Audit records generated by {{ SYSTEM_NAME }} and Google Cloud services are maintained in storage systems with elastic audit record storage capacity. {{ ORGANIZATION }} allocates elastic audit log storage in Google Cloud Logging and continuous export sinks to prevent capacity exhaustion. Storage is allocated to keep audit records online for at least 90 days and archived for at least 365 days (see Section 11).

{{ SYSTEM_NAME }} uses Google Cloud Logging to store and manage all logs. Cloud Logging storage scales with log volume, retains logs for a configurable period, and encrypts them with a {{ ORGANIZATION }}-managed key.

Aggregated organization log sinks transfer audit records in real time from the components that generate them to central storage in a separate audit project (see Section 9.3). Cloud Logging can export logs to Cloud Storage buckets for long-term retention, and these records can then be exported to an external system for archival storage.


## 5. Response to Audit Logging Process Failures

{{ ORGANIZATION }} is responsible for monitoring and remediating audit processing failures for {{ SYSTEM_NAME }}. When an audit logging process failure occurs, Cloud Monitoring alerting policies notify the ISSM and ISSO within 15 minutes, Pub/Sub dead-letter queues hold undelivered records to minimize data loss, and fail-secure administrative access restrictions are applied.


### 5.1 Storage Capacity Warning

Google Cloud Logging does not run out of storage in the traditional sense, but administrators can configure budgets to receive warnings before the costs of storing the logs in short-term accessible storage rise above the configured threshold.

{{ ORGANIZATION }} is responsible for providing a warning to the ISSM, the ISSO, and other personnel with assigned audit responsibilities within 2 hours of budget warning events when allocated short-term storage costs or project log sink volume reaches 75% of repository capacity (`AU-5(1)`).


### 5.2 Real-Time Alerts

> [!IMPORTANT]
> [WARNING: RMF TEAM ACTION REQUIRED: Verify and update operational audit log failure notification thresholds and incident response team contacts.]

{{ ORGANIZATION }} is responsible for providing immediate real-time automated alerts (within 15 minutes of detection via Cloud Monitoring alerting policies, {{ EXTERNAL_SIEM }} channels, and {{ CSSP_PROVIDER }} alert feeds) when critical audit logging failure events occur, including:

- Storage bucket retention policy, write permission, or quota exhaustion failures preventing audit log ingestion (`AU-9`).
- Cloud KMS Customer-Managed Encryption Key (CMEK) revocation or key access failures affecting audit log encryption (`SC-13`).
- Network path disconnection or VPC egress firewall failures blocking audit log transmission to centralized log sinks (`SC-7`).


## 6. Audit Record Review, Analysis, and Reporting

Cloud Logging keeps Data Access audit logs in the _Default bucket for 30 days unless custom retention is configured (see Section 9.1). Before that period ends, {{ ORGANIZATION }} routes audit logs through log sinks to storage that it controls, and it is responsible for reviewing them for anomalous activity within {{ SYSTEM_NAME }} and its Google Cloud environment.


### 6.1 Automated Process Integration

{{ ORGANIZATION }} uses {{ TELEMETRY_PIPELINE }}, {{ EXTERNAL_SIEM }}, Cloud Monitoring alerting, and BigQuery Log Analytics (monitored by {{ THREAT_DETECTION_ENGINE }}) to integrate audit review, analysis, and reporting processes to support {{ ORGANIZATION }} processes for investigation and response to suspicious activities.


### 6.2 Correlate Audit Record Repositories

{{ ORGANIZATION }} is responsible for analyzing and correlating audit records across the organization and various repositories to gain situational awareness throughout the entire organization. This includes audit records from {{ SYSTEM_NAME }} and its Google Cloud environment.


### 6.3 Central Review and Analysis

> [!IMPORTANT]
> [WARNING: RMF TEAM ACTION REQUIRED: Confirm agency operational audit review cadence and analytical reporting recipients.]

{{ ORGANIZATION }} reviews system audit records at least weekly (and continuously 24x7 via automated {{ EXTERNAL_SIEM }} / {{ CSSP_PROVIDER }} and {{ THREAT_DETECTION_ENGINE }}) for unusual or anomalous activities. All security findings will be reported to ISSO, ISSM, and enterprise SOC/CSSP stakeholders. {{ ORGANIZATION }} uses organization-level Cloud Logging aggregated log sinks exporting to immutable Cloud Storage buckets and BigQuery as the central repository for all organizational audit logs and records.


### 6.4 Integrated Analysis of Audit Records

{{ ORGANIZATION }} is responsible for integrating audit records with the analysis of vulnerability scanning information, performance data, and system monitoring information to further enhance the ability to identify inappropriate or unusual activity.


### 6.5 Correlation with Physical Monitoring

Physical access monitoring for the data centers that host {{ SYSTEM_NAME }} is inherited from Google Cloud. {{ ORGANIZATION }} correlates audit records in {{ EXTERNAL_SIEM }} with physical access monitoring information to identify suspicious, inappropriate, unusual, or malevolent activity. [CONFIG_REQUIRED: Physical access monitoring sources correlated with audit records (for example, badge access logs for {{ ORGANIZATION }} facilities with administrative access to {{ SYSTEM_NAME }}).]


## 7. Audit Record Reduction and Report Generation

Audit reduction is the process that uses collected audit information and produces a summary of the data.

{{ ORGANIZATION }} implements {{ EXTERNAL_SIEM }} (in coordination with {{ CSSP_PROVIDER }}) to collect, consolidate, and process event log information and provide an on-demand audit review, analysis, and event report that does not alter the original content or event times. Additionally, {{ EXTERNAL_SIEM }} and BigQuery log analytics support after-the-fact investigations of security events/incidents.


### 7.1 Automatic Processing

{{ ORGANIZATION }} implements {{ EXTERNAL_SIEM }} (supported by {{ CSSP_PROVIDER }}) and BigQuery Log Analytics that have the capability to process, sort, and search audit records for events of interest including, but not limited to: system resources involved, information objects accessed, identities of individuals, event types, event locations, event date and times, IP addresses involved, and event successes or failures.


## 8. Time Stamps

A time stamp is the time the event described by the log entry occurred. This time is used to compute the log entry's age and to enforce the log retention period. If this field is omitted in a new log entry, then Logging assigns it the current time. Timestamps have nanosecond accuracy, but trailing zeros in the fractional seconds might be omitted when the timestamp is displayed.

Incoming log entries must have timestamps that don't exceed the log retention period in the past, and that don't exceed 24 hours in the future. Log entries outside those time boundaries are rejected by Logging.

Timestamps use RFC 3339 UTC "Zulu" format, with nanosecond resolution and up to nine fractional digits. Examples: "2014-10-02T15:01:23Z" and "2014-10-02T15:01:23.045123456Z".

Audit logs generated by {{ ORGANIZATION }} {{ SYSTEM_NAME }} receive time stamps from the internal system clocks of Google servers.

{{ ORGANIZATION }} {{ SYSTEM_NAME }} will have the minimum granularity of time measurement for event logging configured to one millisecond (synchronized across all Google Cloud infrastructure servers via Google TrueTime / Network Time Protocol UTC).


## 9. Protection of Audit Information

{{ ORGANIZATION }} protects audit information and audit logging tools from unauthorized access, modification, and deletion. This section focuses on technical protection of audit information. Physical protection of audit information is addressed by media protection controls and physical and environmental protection controls.

Regardless of the source of the discovery, coordination through the {{ ORGANIZATION }} Cybersecurity Team will occur upon the discovery of unauthorized access to, modification of, or deletion of audit logs or the capability. This is to ensure the proper Incident Response is conducted and communicated up the proper chain of command. Cloud Monitoring alerts the ISSM and ISSO in real time when deletion of audit logs, log buckets, or log sinks is attempted.


### 9.1 Storing, Viewing, and Managing Logs


**Log Buckets**

Cloud Logging uses log buckets as containers in your Google Cloud projects, billing accounts, folders, and organizations to store and organize your logs data. The logs that you store in Cloud Logging are indexed, optimized, and delivered to let you analyze your logs in real time. Cloud Logging buckets are different storage entities than the similarly named Cloud Storage buckets.

For each Google Cloud project, billing account, folder, and organization, Logging automatically creates two log buckets: _Required and _Default. Logging automatically creates sinks named _Required and _Default that, in the default configuration, route logs to the correspondingly named buckets.

You can disable the _Default sink, which routes logs to the _Default log bucket. You can change the behavior of the _Default sinks created for any new Google Cloud projects or folders.

You can't change routing rules for the _Required bucket.

Additionally, you can create user-defined buckets for any Google Cloud project.

You create sinks to route all, or just a subset, of your logs to any log bucket. This flexibility allows you to choose the Google Cloud project in which your logs are stored and what other logs are stored with them.


**_Required log bucket**

Cloud Logging automatically routes the following types of logs to the _Required bucket:

- Admin Activity audit logs

- System Event audit logs

- Cloud Identity / Google Workspace Admin Audit logs (when applicable)

- Enterprise Groups Audit logs

- Login Audit logs

- Access Transparency logs

Cloud Logging retains the logs in the _Required bucket for 400 days; you can't change this retention period.

You can't modify or delete the _Required bucket. You can't disable the _Required sink, which routes logs to the _Required bucket.


**_Default log bucket**

Any log entry that isn't stored in the _Required bucket is routed by the _Default sink to the _Default bucket, unless you disable or otherwise edit the _Default sink.

For example, Cloud Logging automatically routes the following types of logs to the _Default bucket:

- Data Access audit logs

- Policy Denied audit logs

Cloud Logging retains the logs in the _Default bucket for 30 days, unless you configure custom retention for the bucket.

You can't delete the _Default bucket.


**User-defined log buckets**

You can also create user-defined log buckets in any Google Cloud project. By applying sinks to your user-defined log buckets, you can route any subset of your logs to any log bucket, letting you choose which Google Cloud project your logs are stored in and which other logs are stored with them.

For example, for any log generated in Project-A, you can configure a sink to route that log to user-defined buckets in Project-A or Project-B.

You can configure custom retention for the bucket.


**Log Sinks**

Sinks control how Cloud Logging routes logs. Using sinks, you can route some or all of your logs to supported destinations. Some of the reasons that you might want to control how your logs are routed include the following:

- To store logs that are unlikely to be read but that must be retained for compliance purposes.

- To organize your logs in buckets in a format that is useful to you.

- To use big-data analysis tools on your logs.

- To stream your logs to other applications, other repositories, or third parties. For example, if you want to export your logs from Google Cloud so that you can view them on a third-party platform, then configure a sink to route your log entries to Pub/Sub.

Sinks belong to a given Google Cloud resource: Google Cloud projects, billing accounts, folders, and organizations. When the resource receives a log entry, it routes the log entry according to the sinks contained by that resource and any ancestral sinks configured across the resource hierarchy. The log entry is sent to the destination associated with each matching sink.

Cloud Logging provides two predefined sinks for each Google Cloud project, billing account, folder, and organization: _Required and _Default. All logs that are generated in a resource are automatically processed through these two sinks and then are stored either in the correspondingly named _Required or _Default buckets.

Sinks act independently of each other. Regardless of how the predefined sinks process your log entries, you can create your own sinks to route some or all of your logs to various supported destinations or to exclude them from being stored by Cloud Logging.

The routing behavior for each sink is controlled by configuring the inclusion filter and exclusion filters for that sink. Depending on the sink's configuration, every log entry received by Cloud Logging falls into one or more of these categories:

- Stored in Cloud Logging and not routed elsewhere.

- Stored in Cloud Logging and routed to a supported destination.

- Not stored in Cloud Logging but routed to a supported destination.

- Neither stored in Cloud Logging nor routed elsewhere.


### 9.2 Logging Roles

IAM provides predefined roles to grant granular access to specific Google Cloud resources and prevent unwanted access to other resources. Google Cloud creates and maintains these roles and automatically updates their permissions when Cloud Logging adds new features or APIs.

The following are the predefined roles for Logging:

- Logging Admin

- Logs Bucket Writer

- Logs Configuration Writer

- Logs Field Accessor

- Log Link Accessor

- Logs Writer

- Private Logs Viewer

- Logs View Accessor

- Logs Viewer

To let a user perform all actions in Logging, grant the Logging Admin (roles/logging.admin) role.

To let a user create and modify logging configurations, such as sinks, buckets, views, links, log-based metrics, or exclusions, grant the Logs Configuration Writer (roles/logging.configWriter) role.

To let a user read logs in the _Required and _Default buckets, use the Logs Explorer, and use the Log Analytics page, grant one of the following roles:

- For access to all logs in the _Required bucket, and access to the _Default view on the _Default bucket, grant the Logs Viewer (roles/logging.viewer) role.

- For access to all logs in the _Required and _Default buckets, including data access logs, grant the Private Logs Viewer (roles/logging.privateLogViewer) role.

To let a user read logs by using a log view on a log bucket, grant the Logs View Accessor (roles/logging.viewAccessor) role. You can restrict authorization to a specific log view on a specific log bucket.

To give a user access to restricted LogEntry fields, if any, in a given bucket, grant the Logs Field Accessor (roles/logging.fieldAccessor) role.

To let a user write logs by using the Logging API, grant the Logs Writer (roles/logging.logWriter) role. This role doesn't grant viewing permissions.

To let the service account of a sink route logs to a bucket in a different Google Cloud project, grant the service account the Logs Bucket Writer (roles/logging.bucketWriter) role.


### 9.3 Store on Separate Physical Systems or Components

{{ ORGANIZATION }} routes and stores audit records in a dedicated, isolated Log Archive repository (Google Cloud Logging aggregated organization sinks exporting to WORM-locked Cloud Storage buckets and BigQuery Log Sinks in a distinct audit project separate from {{ SYSTEM_NAME }}); this helps ensure that a compromise of {{ SYSTEM_NAME }} does not also result in a compromise of the audit records.


### 9.4 Cryptographic Protection

{{ ORGANIZATION }} uses Cloud KMS CMEK encryption and GCS bucket retention locks to protect the integrity of audit information.


### 9.5 Access by Subset of Privileged Users

Google Cloud allows {{ ORGANIZATION }} developers to write code and manage cloud resources. Many Google Cloud services generate audit logs for {{ SYSTEM_NAME }}. {{ ORGANIZATION }} audit logs can only be viewed by users and groups with specific Identity and Access Management roles. {{ ORGANIZATION }} can configure who can view and export audit logs within {{ SYSTEM_NAME }} and its Google Cloud projects. Management of audit logging functionality (the Logging Admin and Logs Configuration Writer roles) is limited to personnel designated by the ISSM and ISSO.


### 9.6 Dual Authorization

Dual authorization mechanisms, also known as two-person control, require the approval of two authorized individuals to execute audit functions. To reduce the risk of collusion, {{ ORGANIZATION }} must consider rotating dual authorization duties to other individuals. Dual authorization mechanisms should not be required when immediate responses are necessary, to ensure public and environmental safety.

{{ ORGANIZATION }} enforces dual authorization for the movement or deletion of audit records.


### 9.7 Read-Only Access

Restricting privileged user or role authorizations to read-only helps to limit the potential damage to {{ ORGANIZATION }} that could be initiated by such users or roles, such as deleting audit records to cover up malicious activity.

{{ ORGANIZATION }} will restrict privileged users or specified roles to read-only access for audit records.


## 10. Non-Repudiation

Activities covered by non-repudiation include read, write, modify, and deletion of audit information. For auditing tools, non-repudiation includes installation, configuration, modification, and uninstalling tools.

Non-repudiation protects against claims by authors of not having authored certain documents, senders of not having transmitted messages, receivers of not having received messages, and signatories of not having signed documents.

Non-repudiation services can be used to determine if information originated from an individual or if an individual took specific actions.

{{ ORGANIZATION }} {{ SYSTEM_NAME }} enforces non-repudiation through Google Cloud Audit Logs cryptographically bound to immutable service account identities and hardware-backed Cloud Identity FIDO2/WebAuthn user credentials (`AU-10`). Each audit record binds the action to the authenticated identity that performed it, so authorized reviewers can determine the identity of the producer of the information (`AU-10(1)`).


## 11. Audit Record Retention

Cloud Logging retains logs in the _Required bucket for 400 days and in the _Default bucket for 30 days unless custom retention is configured (see Section 9.1). It is {{ ORGANIZATION }}'s responsibility to route audit log records out of these default buckets and manage their retention. {{ ORGANIZATION }} exports logs to dedicated Google Cloud Storage WORM log buckets and BigQuery analytical sinks to meet retention requirements (`AU-11`).

{{ ORGANIZATION }} is responsible for the retention of audit records for customer applications within Google Cloud. {{ ORGANIZATION }} keeps audit records online for at least 90 days, retains them for at least 365 days, and preserves them offline for any longer period required by NARA records schedules.


### 11.1 Long-Term Retrieval Capability

{{ ORGANIZATION }} needs to access and read audit records that are kept in long-term storage. Measures employed to help facilitate the retrieval of audit records include converting records to newer formats, retaining equipment capable of reading the records, and retaining the necessary documentation to help personnel understand how to interpret the audit records.

{{ ORGANIZATION }} uses Google Cloud Storage dual-region buckets with Bucket Lock retention holds and BigQuery long-term table partitioning for long-term storage and high-speed analytical retrieval of audit records (`AU-11(1)`).


## 12. Audit Record Generation

All physical and logical components of {{ ORGANIZATION }} {{ SYSTEM_NAME }} must produce audit records. {{ ORGANIZATION }} must ensure that each {{ SYSTEM_NAME }} component is configured to collect audit records for the following security and operational events (`AU-12`):

- Admin Activity Audit Logs (recording all resource creation, IAM role assignments, and VPC security boundary modifications).
- System Event Audit Logs (recording automated platform actions, OS updates, and host live migration events).
- Data Access & Policy Intelligence Audit Logs (recording authentication attempts, BigQuery table reads, and GCS storage accesses).

Audit record generation is managed by the ISSM and ISSO, who select the event types to be logged by specific components.


### 12.1 System-Wide and Time-Correlated Audit Trail

{{ ORGANIZATION }} compiles audit records from all {{ SYSTEM_NAME }} components into a system-wide audit trail using aggregated organization-level log sinks (see Section 6.3). Time stamps are generated from synchronized Google system clocks (see Section 8), so records in the audit trail are time-correlated to within one millisecond.


### 12.2 Changes by Authorized Individuals

Permitting authorized individuals to make changes to system logging enables {{ ORGANIZATION }} to extend or limit logging in response to elevated threat conditions or defined operational requirements. Logging that is limited to conserve {{ SYSTEM_NAME }} resources may be extended to address certain threat situations. In addition, logging may be limited to a specific set of event types to facilitate audit reduction, analysis, and reporting. Authorized administrators can change the logging performed on {{ SYSTEM_NAME }} components within 4 hours when a system security incident occurs or the risk status is elevated.


## 13. Monitoring for Information Disclosure

{{ ORGANIZATION }} continuously monitors public code repositories and other open-source information sites for evidence of unauthorized disclosure of {{ SYSTEM_NAME }} information, such as credentials, keys, and configuration data. CI/CD pipelines run automated secret scanning (Gitleaks). When a disclosure is discovered, {{ ORGANIZATION }} notifies the ISSO and ISSM, escalates to {{ CSSP_PROVIDER }}, and handles the event under the Incident Response Policy. [CONFIG_REQUIRED: List the open-source information sites and public repositories that are monitored.]


## 14. Session Audit

Session Audits can include monitoring keystrokes, tracking websites visited, and recording information and/or file transfers. Session audit capability is implemented in addition to event logging and may involve implementation of specialized session capture technology.

{{ ORGANIZATION }} provides and implements Google Access Transparency & Cloud Audit Logs to audit administrative user session activities.


### 14.1 System Start-up

{{ ORGANIZATION }} configures Cloud Audit Logs to initiate session audits automatically at {{ SYSTEM_NAME }} startup.


### 14.2 Remote Viewing and Listening

{{ ORGANIZATION }} configures Cloud Logging and IAP session auditing so that authorized incident responders can view the content of established user sessions remotely in real time during active security investigations.


## 15. Cross-Organizational Audit Logging

{{ ORGANIZATION }} coordinates audit information with external organizations, including {{ CSSP_PROVIDER }}, when audit information is transmitted across organizational boundaries. Audit records are forwarded in standardized formats (RFC 5424 Syslog and normalized JSON) through {{ TELEMETRY_PIPELINE }} and Pub/Sub to central logging and {{ EXTERNAL_SIEM }}.


### 15.1 Identity Preservation

Cross-organizational audit trails preserve the identity of the individual who performed each action. Cloud Audit Logs record the authenticated principal for each action, and that identity is kept unchanged when records are forwarded to {{ EXTERNAL_SIEM }} and {{ CSSP_PROVIDER }}.


### 15.2 Sharing of Audit Information

{{ ORGANIZATION }} provides cross-organizational audit information to {{ CSSP_PROVIDER }} <!-- IF DOD_ENCLAVE -->and to USCYBERCOM and JFHQ-DODIN<!-- ENDIF -->, under documented sharing agreements. [CONFIG_REQUIRED: List the organizations that receive cross-organizational audit information and the sharing agreements that govern it.]


## Appendix A – Detailed Compliance Matrix

The following table provides detailed traceability between the policy implementation statements in this document, the authoritative NIST SP 800-53 Rev. 5 control requirements, DoD CCIs, and the technical/governance enforcement mechanisms active across {{ SYSTEM_NAME }}.


| CTRL ID | CTRLTITLE | REQUIRED {{ GRC_STANDARD_LABEL }} STANDARD | DOCREF | ENFORCEMENT MECHANISM |
| :--- | :--- | :--- | :--- | :--- |
| AU-01 | Policy and Procedures | Develop, document, and disseminate to all personnel an audit and accountability policy and procedures; designate the ISSM to manage them; review and update both at least annually and following significant system changes (including SIEM upgrades or log schema changes), security or privacy incidents, assessment or audit findings, or changes in applicable laws, regulations, or policies. (CCI-000117, CCI-000119, CCI-000120, CCI-000122, CCI-001569, CCI-001570, CCI-001832, CCI-001834, CCI-001930, CCI-001931, CCI-003799, CCI-003800, CCI-003801, CCI-003802, CCI-003803, CCI-003804, CCI-003805, CCI-003806, CCI-003807, CCI-003808, CCI-003809) | Section 1 | ISSM-managed annual and event-driven review; AO approval; changes recorded in the Document Change Record; publication to the eMASS repository. |
| AU-02 | Event Logging | Identify and log successful and unsuccessful attempts for all auditable events per CNSSI 1015; review event types at least annually. (CCI-000123, CCI-000124, CCI-000125, CCI-000126, CCI-001484, CCI-001485, CCI-001571, CCI-003810, CCI-003811) | Section 2 | Google Cloud Audit Logs (Admin Activity & Data Access); VPC Flow Logs; annual logging taxonomy reviews. |
| AU-03 | Content of Audit Records | Ensure audit records capture what, when, where, source, outcome, and user identity across all system events. (CCI-000130, CCI-000131, CCI-000132, CCI-000133, CCI-000134, CCI-001487) | Section 3 | Cloud Logging structured JSON schema containing caller IP, principal email, method name, timestamp, and status. |
| AU-03(01) | Additional Audit Information | Collect additional audit details including full-text privileged command execution and individual identities. (CCI-000135, CCI-001488) | Section 3.1 | Full-text gcloud CLI logging; Cloud Audit request/response payload capture; IAP session identity binding. |
| AU-03(03) | Limit Personally Identifiable Information Elements | Limit PII contained in audit records to User ID, {{ USER_IDENTIFIER_TYPE }}, and terminal ID as authorized by the Privacy Impact Assessment. (CCI-003812, CCI-003813) | Section 3.2 | Cloud DLP inspection templates; automated PII redaction filters; strict payload exclusion policies. |
| AU-04 | Audit Log Storage Capacity | Allocate elastic audit log storage capacity ensuring at least 90 days online retention and NARA-compliant offline archival (and supporting 12 months active + 18 months cold storage [30 months total] where OMB M-21-31 applies). (CCI-001848, CCI-001849) | Section 4 | Elastic Cloud Logging buckets; BigQuery 90-day active partitioning; dual-region Cloud Storage long-term archive. |
| AU-04(01) | Transfer to Alternate Storage | Transfer audit records from logging components to central storage repositories in real time for interconnected systems. (CCI-001850, CCI-001851) | Section 4 | Aggregated organization log sinks streaming via Pub/Sub topics to BigQuery and Enterprise SIEM in real time. |
| AU-05 | Response to Audit Logging Process Failures | Take automated action to minimize data loss, alert ISSM/ISSO in near real time (15 mins), and enforce fail-secure posture. (CCI-000139, CCI-000140, CCI-001490, CCI-001572, CCI-003814) | Section 5 | Cloud Monitoring automated alert policies; Pub/Sub dead-letter queues; fail-secure administrative access restrictions. |
| AU-05(01) | Storage Capacity Warning | Provide automated warnings to ISSM/ISSO within 2 hours when allocated audit storage reaches 75% capacity. (CCI-001852, CCI-001853, CCI-001854, CCI-001855) | Section 5.1 | Cloud Monitoring metric alerts and billing threshold alerts configured at 75% log volume capacity. |
| AU-05(02) | Real-time Alerts | Provide near real-time automated alerts upon detection of critical logging failure events (CMEK failure, bucket lock failure). (CCI-000147, CCI-001856, CCI-001857, CCI-001858) | Section 5.2 | Real-time Cloud Monitoring alerting policies dispatched to ISSO/ISSM and SOC via automated webhook/email channels. |
| AU-06 | Audit Record Review, Analysis, and Reporting | Review and analyze audit records at least every 7 days (and continuously via automation) for anomalous activity; report to ISSO/ISSM. (CCI-000148, CCI-000149, CCI-000151, CCI-001862, CCI-001863, CCI-003817, CCI-003818, CCI-003819) | Section 6 | {{ TELEMETRY_PIPELINE }}; {{ THREAT_DETECTION_ENGINE }}; weekly manual ISSO audit reviews and {{ EXTERNAL_SIEM }} correlation. |
| AU-06(01) | Automated Process Integration | Integrate audit review, analysis, and reporting using a centralized SIEM and SOAR platform for automated incident response. (CCI-001864, CCI-001865, CCI-003820) | Section 6.1 | Enterprise {{ EXTERNAL_SIEM }} ({{ CSSP_PROVIDER }}) ingestion via {{ TELEMETRY_PIPELINE }} and Pub/Sub; automated containment playbooks. |
| AU-06(03) | Correlate Audit Record Repositories | Correlate audit records across disparate repositories, cloud spokes, and VPC network perimeters to gain global situational awareness. (CCI-000153) | Section 6.2 | Centralized SIEM cross-cloud log correlation; analytics views spanning all authorized system projects and accounts. |
| AU-06(04) | Central Review and Analysis | Establish centralized repository for organization audit logs and conduct centralized security review and analysis. (CCI-000154, CCI-003821) | Section 6.3 | Aggregated organization-level Cloud Logging sinks exporting to central telemetry BigQuery master warehouse. |
| AU-06(05) | Integrated Analysis of Audit Records | Integrate audit log analysis with vulnerability scan results, network performance metrics, and system monitoring data. (CCI-001866, CCI-001867) | Section 6.4 | SIEM multi-source data ingestion linking Semgrep/Checkov scan reports, system telemetry, and audit trails. |
| AU-06(06) | Correlation with Physical Monitoring | Correlate physical facility access records with logical audit logs to identify anomalous cross-domain activities. (CCI-001491) | Section 6.5 | Inherited from Google Cloud Services P-ATO data center physical access controls; logical access logs correlated via Cloud Logging and enterprise SIEM. |
| AU-06(07) | Permitted Actions | Specify the permitted actions for each role or user associated with the review, analysis, and reporting of audit information. (CCI-001868, CCI-001869) | Section 6 | Granular Cloud IAM roles (roles/logging.privateLogViewer, roles/bigquery.dataViewer) and SIEM RBAC profiles restricting audit reviewers to read-only analytical actions. |
| AU-07 | Audit Record Reduction and Report Generation | Provide on-demand audit reduction and report generation capabilities without altering original event records or timestamps. (CCI-001875, CCI-001876, CCI-001877, CCI-001878, CCI-001879, CCI-001880, CCI-001881, CCI-001882, CCI-003822, CCI-003823, CCI-003824, CCI-003825, CCI-003826, CCI-003827, CCI-003828, CCI-003829) | Section 7 | BigQuery analytical views and SIEM reporting engines generating immutable summary reports. |
| AU-07(01) | Automatic Processing | Provide automatic processing to sort, filter, and search audit records by timestamp, user, IP, event type, and outcome. (CCI-000158, CCI-001883, CCI-003830) | Section 7.1 | BigQuery SQL indexing and SIEM indexed search filters across all standardized audit record metadata fields. |
| AU-08 | Time Stamps | Synchronize system clocks to authoritative Stratum-1 sources and record audit timestamps in RFC 3339 UTC with 1ms granularity. (CCI-000159, CCI-001888, CCI-001889, CCI-001890) | Section 8 | Google TrueTime and DoD NTP synchronization; nanosecond RFC 3339 UTC timestamping in Cloud Logging. |
| AU-09 | Protection of Audit Information | Protect audit records against unauthorized access, modification, and deletion; alert ISSM/ISSO on tampering attempts. (CCI-000162, CCI-000163, CCI-000164, CCI-001493, CCI-001494, CCI-001495, CCI-003831, CCI-003832) | Section 9 | Cloud IAM permission boundaries; immutable log sink architectures; real-time alerting on log deletion attempts. |
| AU-09(02) | Store on Separate Physical Systems or Components | Store audit records, in real time and no less than weekly, in a dedicated repository physically and logically separated from the system being audited. (CCI-001348, CCI-001349) | Section 9.3 | Isolated central telemetry logging project and landing zone audit vaults distinct from transit projects. |
| AU-09(03) | Cryptographic Protection | Protect audit record integrity using Cloud KMS CMEK encryption and GCS Bucket Lock WORM retention policies. (CCI-001350, CCI-001496) | Section 9.4 | FIPS 140-2 Level 3 Cloud KMS HSM keys; GCS Object Retention Lock (SEC Rule 17a-4 compliant). |
| AU-09(04) | Access by Subset of Privileged Users | Restrict management of audit logging functionality strictly to an authorized subset of privileged security administrators. (CCI-001351, CCI-001894) | Section 9.5 | Fine-grained IAM roles (roles/logging.admin, roles/logging.configWriter) restricted to ISSM/ISSO personnel. |
| AU-09(05) | Dual Authorization | Enforce dual authorization requirements across {{ SYSTEM_NAME }} in accordance with NIST SP 800-53 Rev. 5 AU-9(5). (CCI-001895, CCI-001896) | Section 3 | Enforced via Google Cloud infrastructure controls, Terraform configuration baselines, and ISSM/ISSO governance verification. |
| AU-09(06) | Read-only Access | Restrict privileged audit access for auditors and CSSP personnel to read-only permissions. (CCI-001897, CCI-001898) | Section 9.7 | IAM read-only roles (roles/logging.viewer, roles/logging.privateLogViewer, roles/bigquery.dataViewer). |
| AU-10 | Non-repudiation | Enforce non-repudiation for all administrative actions and resource modifications in accordance with DoDI 8520.02. (CCI-000166, CCI-001899) | Section 10 | Cryptographic binding to {{ IDENTITY_PROVIDER }} with {{ MFA_MECHANISM }} credentials and Workload Identity Federation (WIF) OIDC claims. |
| AU-10(01) | Association of Identities | Bind the identity of the information producer with the information at an assurance level commensurate with {{ IMPACT_LEVEL }} data. (CCI-001900, CCI-001901, CCI-001902) | Section 10 | Immutable digital identity logging in Cloud Audit Logs; signed OIDC token validation; hardware token assertions ({{ MFA_MECHANISM }}). |
| AU-11 | Audit Record Retention | Retain audit records online for at least 90 days and preserve offline in accordance with NARA requirements (and CNSSI 1015 where applicable; federal civilian agencies subject to OMB M-21-31 require at least 12 months active storage plus 18 months cold storage [30 months total]). (CCI-000167, CCI-000168) | Section 11 | GCS bucket retention policies (minimum 90 days online / NARA schedule; or 12 months active + 18 months cold [30 months total] where OMB M-21-31 applies); BigQuery long-term table partition retention management. |
| AU-11(01) | Long-term Retrieval Capability | Ensure long-term audit records remain retrievable and queryable in standardized non-proprietary formats. (CCI-002044, CCI-002045) | Section 11.1 | Standardized JSON/Parquet storage formats in GCS; BigQuery federated queries across long-term partitions. |
| AU-12 | Audit Record Generation | Ensure audit generation capabilities are enabled across all system components and managed by ISSM/ISSO. (CCI-000169, CCI-000171, CCI-000172, CCI-001459, CCI-001910) | Section 12 | Universal Cloud Logging enablement via organization policy; Terraform baseline audit module deployment. |
| AU-12(01) | System-wide and Time-correlated Audit Trail | Compile audit records from all components into a system-wide audit trail time-correlated within 1 millisecond. (CCI-000173, CCI-000174, CCI-001577) | Section 12.1 | Aggregated organization log sinks; TrueTime synchronization ensuring sub-millisecond correlation across all spokes. |
| AU-12(03) | Changes by Authorized Individuals | Enable authorized administrators to dynamically modify logging parameters within 4 hours based on operational needs. (CCI-001911, CCI-001912, CCI-001913, CCI-001914, CCI-002047, CCI-003834) | Section 12.2 | Terraform IaC pipeline triggers and Cloud Logging API dynamic filter updates executed within 4 hours. |
| AU-13 | Monitoring for Information Disclosure | Continuously monitor open-source repositories and public sites for unauthorized disclosure of system data. (CCI-001460, CCI-001461, CCI-001915, CCI-003837, CCI-003838, CCI-003839, CCI-003840) | Section 13 | Automated CI/CD secret scanning (Gitleaks); public repository monitoring; immediate {{ CSSP_PROVIDER }} escalation workflows. |
| AU-14 | Session Audit | Provide capability to log, record, view, and analyze administrative session content during incident investigations. (CCI-001919, CCI-003844, CCI-003845, CCI-003846, CCI-003847) | Section 14 | Google Access Transparency; Cloud Audit Logs; Identity-Aware Proxy (IAP) TCP session stream logging. |
| AU-14(01) | System Start-up | Automatically initiate session auditing capabilities at system startup across all transit components. (CCI-001464) | Section 14.1 | Default Cloud Logging startup daemon configuration; automated IAP session capture initiation. |
| AU-14(03) | Remote Viewing and Listening | Provide authorized incident responders remote session auditing visibility during active security investigations. (CCI-001920, CCI-003848) | Section 14.2 | Role-based IAP tunnel auditing; Cloud Audit Log live stream inspection for certified forensic analysts. |
| AU-16 | Cross-organizational Audit Logging | Coordinate and standardize audit logging when information is transmitted across organizational boundaries. (CCI-001923, CCI-001924, CCI-001925) | Section 15 | Automated STIX/TAXII threat sharing; standardized RFC 5424 Syslog forwarding to central logging and {{ CSSP_PROVIDER }} boundaries. |
| AU-16(01) | Identity Preservation | Preserve the identity of individuals in cross-organizational audit trails so that each action remains attributable to the individual who performed it. (CCI-001926) | Section 15.1 | Authenticated principal recorded in each Cloud Audit Log entry; identity fields forwarded unchanged to {{ EXTERNAL_SIEM }} and {{ CSSP_PROVIDER }}. |
| AU-16(02) | Sharing of Audit Information | Provide cross-organizational audit information to USCYBERCOM, JFHQ-DODIN, and CSSPs under binding SLAs. (CCI-001927, CCI-001928, CCI-001929) | Section 15.2 | Automated SIEM peering feeds; secure API log export to CSSP analysis platforms under DoD sharing agreements. |
