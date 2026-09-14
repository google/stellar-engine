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
> This document defines the enterprise security policy and implementation procedures for **Audit and Accountability** under **NIST SP 800-53 Rev. 5 (AU)**.
> Technical infrastructure controls are automatically provisioned and enforced via **{{ SYSTEM_NAME }}** Terraform blueprints.
> Operational rules or contact details requiring manual confirmation are highlighted with RMF Team Callouts.


## 1. Overview

Audit and accountability policy and procedures ensure {{ ORGANIZATION }}, {{ SYSTEM_NAME }}, and {{ SYSTEM_NAME }} components or services are configured to audit, analyze and report events in accordance with DoD requirements. Policies and procedures contribute to security and privacy assurance. Therefore, it is important that security and privacy programs collaborate on the development of audit and accountability policy and procedures.

This document complies with the following requirements from NIST Special Publication 800-53 Revision 5, "Security and Privacy Controls for Federal Information Systems and Organizations". A detailed compliance matrix can be found in Appendix A, “Detailed Compliance Matrix”.

> [!IMPORTANT]
> [WARNING: RMF TEAM ACTION REQUIRED: Verify and update operational contact/procedure details in this section.]
> This {{ ORGANIZATION }} Audit and Accountability Policy is consistent with applicable federal laws, directives, policies, regulations, standards and guidance. This plan facilitates the implementation of the audit and accountability policy and the associated audit and accountability controls.  The {{ ORGANIZATION }} Cybersecurity Team’s office is responsible for the development of, update, annual review and dissemination of this Audit and Accountability Policy.  Dissemination of this policy and any associated procedures will occur initially to all {{ ORGANIZATION }} {{ SYSTEM_NAME }} level ISSMs and ISSOs, provided as an artifact in the Common Control Provider {{ RMF_GOVERNANCE_SYSTEM }} package for {{ SYSTEM_NAME }}, and is available upon request to the {{ ORGANIZATION }} Cybersecurity Team.  All reviews and updates will be tracked via the Change Record.

This policy is subject to change, upon review, in response to any event, After Action Report, to incorporate lessons learned, or as directed by higher commands and in accordance with any changes in applicable laws or directives.


## 2. Event Logging

{{ SYSTEM_NAME }} allows customer developers to write code and manage cloud resources to determine what audit logs are generated and how long they are retained. {{ ORGANIZATION }} is responsible for managing the audible events and ensuring appropriate events are logged.

An event is any observable occurrence in an information system. The types of events that require logging are those events that are significant and relevant to the security of systems and the privacy of individuals. Event logging also supports specific monitoring and auditing needs. Event types include password changes, failed logons or failed accesses related to systems, security or privacy attribute changes, administrative privilege usage, PIV credential usage, data action changes, query parameters, or external credential usage.


**Audit Logs**

The following are all audit logs that are collected and stored within Google Cloud:

Activity Logs - Admin Activity audit logs contain log entries for API calls or other actions that modify the configuration or metadata of resources. For example, these logs record when users create VM instances or change Identity and Access Management permissions.

Data Access Logs -Data Access audit logs contain API calls that read the configuration or metadata of resources, as well as user-driven API calls that create, modify, or read user-provided resource data.

System Event Logs - System Event audit logs contain log entries for Google Cloud actions that modify the configuration of resources. System Event audit logs are generated by Google systems; they aren't driven by direct user action.


**Other Logs**

VPC Flow Logs - VPC Flow Logs record a sample of network flows sent from and received by VM instances, including instances used as GKE nodes. These logs can be used for network monitoring, forensics, real-time security analysis, and expense optimization.

Firewall Rule Logs - Firewall Rules Logging lets you audit, verify, and analyze the effects of your firewall rules. For example, you can determine if a firewall rule designed to deny traffic is functioning as intended. Firewall Rules Logging is also useful if you need to determine how many connections are affected by a given firewall rule.

Access Transparency Logs - Access Transparency logs include data about Google staff activity, including:

- Actions by the Support team that you may have requested by phone

- Basic engineering investigations into your support requests

- Other investigations made for valid business purposes, such as recovering from an outage


**Log Destinations**

Audit logs and other logs do not expire and are sent to the following destinations:

- BigQuery

- Storage

- Pub/Sub

When the log destination is in a different project, we need to make sure the log writer identity service account of the log sink has the permission to write to the destination. If there is a VPC SC or other additional restrictions, we need to grant access to the log writer identity as well.

{{ ORGANIZATION }} will enable the audit capability for the execution of privileged functions on {{ SYSTEM_NAME }}. {{ TELEMETRY_PIPELINE }} forwards audit records to {{ SIEM_TOOL }} ({{ CSSP_PROVIDER }}) and centralized audit sinks via Pub/Sub.



### 2.1 Google Cloud Platform (GCP) Inherited Controls & Shared Responsibility Boundary

- **Google Inherited Controls**: Google Cloud Platform provides underlying infrastructure log collection, physical server audit trails, and hardware-level audit logging for all CSP operations (`AU-2`, `AU-3`, `AU-12`).
- **Customer Implementation Responsibilities**: {{ ORGANIZATION }} is responsible for enabling Admin Activity and Data Access Audit Logs (`AU-2`, `AU-3`), configuring Cloud Logging log sinks to BigQuery / GCS buckets (`AU-4`, `AU-9`), enforcing 1-year (365-day) log retention (`AU-11`), and automated SIEM log review (`AU-6`).

## 3. Content of Audit Records

{{ SYSTEM_NAME }} empowers {{ ORGANIZATION }} developers and cloud engineers to manage cloud resources and define what audit records are generated across system boundaries. The {{ SYSTEM_NAME }} admin activity log produces audit records that contain sufficient information to, at a minimum, establish what type of event occurred, when (date and time) the event occurred, the source of the event, the outcome of the event, and the identity of any user/subject associated with the event. In the case of the admin activity log, “where the event occurred” is captured as occurring within {{ ORGANIZATION }} GCP projects, folders, and organizations. In addition to admin logs, application activity logs are captured in Cloud Logging, and application teams maintain the capability to define and customize application-level audit logging.

{{ AUDIT_AND_SIEM_IMPLEMENTATION }}


### 3.1 Additional Audit Information

GCP allows {{ ORGANIZATION }} developers to write code and manage cloud resources. {{ ORGANIZATION }} is able to determine what audit logs are generated and for how long they are retained. The GCP Admin Audit Logs and Data Access Logs include event start time, end time, request IP address/user agent, request payload, user identity and objects/resources being acted upon. It is {{ ORGANIZATION }} responsibility to ensure that {{ SYSTEM_NAME }} hosted on GCP through {{ SYSTEM_NAME }} and managed to include additional session specific information such as bytes transferred during a session that can be helpful during an investigation or inquiry.


## 4. Audit Log Storage Capacity

{{ ORGANIZATION }} manages cloud resources and log retention policies for {{ SYSTEM_NAME }}. Audit records generated by {{ SYSTEM_NAME }} and GCP services are maintained in storage systems with elastic audit record storage capacity. {{ ORGANIZATION }} allocates elastic audit log storage in Google Cloud Logging and continuous export sinks to prevent capacity exhaustion.

{{ SYSTEM_NAME }} uses the Google Cloud Logging System to store and manage all logs. The Google Cloud Logging System uses elastic storage to store nearly unlimited logs, retain them for a configurable period of time, and encrypt them with a {{ ORGANIZATION }} managed key.

Google Cloud Logging can export logs in a text format to Google Cloud Storage Bucket for long-term retention. These records can then be exported to an external system for archival storage.


## 5. Response to Audit Logging Process Failures

{{ ORGANIZATION }} is responsible for monitoring and remediating audit processing failures for {{ SYSTEM_NAME }}.


### 5.1 Storage Capacity Warning

Google Cloud Logging does not run out of storage in the traditional sense, but administrators have the ability to configure budgets in order to receive warnings before the costs of storing the logs in short-term accessible storage rise above the configured threshold.

{{ ORGANIZATION }} is responsible for providing a warning to essential stakeholders, or those individuals with identified roles and responsibilities, within 2 hours of budget warning events when allocated short-term storage costs or project log sink volume reaches 80% of repository capacity (`AU-5`).


### 5.2 Real-Time Alerts

> [!IMPORTANT]
> [WARNING: RMF TEAM ACTION REQUIRED: Verify and update operational audit log failure notification thresholds and incident response team contacts.]

{{ ORGANIZATION }} is responsible for providing immediate real-time automated alerts (within 15 minutes of detection via Cloud Monitoring alerting policies, {{ SIEM_TOOL }} channels, and {{ CSSP_PROVIDER }} alert feeds) when critical audit logging failure events occur, including:

- Storage bucket retention policy, write permission, or quota exhaustion failures preventing audit log ingestion (`AU-9`).
- Cloud KMS Customer-Managed Encryption Key (CMEK) revocation or key access failures affecting audit log encryption (`SC-13`).
- Network path disconnection or VPC egress firewall failures blocking audit log transmission to centralized log sinks (`SC-7`).


## 6. Audit Record Review, Analysis, and Reporting

Within the GCP instance of {{ SYSTEM_NAME }}, Google retains online audit logs for thirty (30) days. It will then be the responsibility of {{ ORGANIZATION }} to offload those audit log records from the GCP console within that thirty (30) day window to an additional storage location. Once the audit logs are relocated, {{ ORGANIZATION }} is responsible for audit log review and any anomalous behavior within {{ SYSTEM_NAME }} and the GCP instance.


### 6.1 Automated Process Integration

{{ ORGANIZATION }} uses {{ TELEMETRY_PIPELINE }}, {{ SIEM_TOOL }}, Cloud Monitoring alerting, and BigQuery Log Analytics (monitored by {{ THREAT_DETECTION_ENGINE }}) to integrate audit review, analysis, and reporting processes to support {{ ORGANIZATION }} processes for investigation and response to suspicious activities.


### 6.2 Correlate Audit Record Repositories

{{ ORGANIZATION }} is responsible for analyzing and correlating audit records across the organization and various repositories to gain situational awareness throughout the entire organization. This includes audit logs and records from {{ SYSTEM_NAME }} and {{ SYSTEM_NAME }}.


### 6.3 Central Review and Analysis

> [!IMPORTANT]
> [WARNING: RMF TEAM ACTION REQUIRED: Confirm agency operational audit review cadence and analytical reporting recipients.]

{{ ORGANIZATION }} reviews system audit records at least weekly (and continuously 24x7 via automated {{ SIEM_TOOL }} / {{ CSSP_PROVIDER }} and {{ THREAT_DETECTION_ENGINE }}) for unusual or anomalous activities. All security findings will be reported to ISSO, ISSM, and enterprise SOC/CSSP stakeholders. {{ ORGANIZATION }} uses organization-level Cloud Logging aggregated log sinks exporting to immutable Cloud Storage buckets and BigQuery as the central repository for all organizational audit logs and records.


### 6.4 Integrated Analysis of Audit Records

{{ ORGANIZATION }} is responsible for integrating audit records with the analysis of vulnerability scanning information, performance data, and system monitoring information to further enhance the ability to identify inappropriate or unusual activity.


## 7. Audit Record Reduction and Report Generation

Audit reduction is the process that utilizes collected audit information and produces a summary of the data.

{{ ORGANIZATION }} implements {{ SIEM_TOOL }} (in coordination with {{ CSSP_PROVIDER }}) in order to collect, consolidate, and process event log/information and provide an on-demand audit review, analysis, and event report, that does not alter the original content or event times. Additionally, {{ SIEM_TOOL }} and BigQuery log analytics support after-the-fact investigations of security events/incidents.


### 7.1 Automatic Processing

{{ ORGANIZATION }} implements {{ SIEM_TOOL }} (supported by {{ CSSP_PROVIDER }}) and BigQuery Log Analytics that have the capability to process, sort, and search audit records for events of interest including, but not limited to: system resources involved, information objects accessed, identities of individuals, event types, event locations, event date and times, IP addresses involved, and event successes or failures.


## 8. Time Stamps

A time stamp is the time the event described by the log entry occurred. This time is used to compute the log entry's age and to enforce the logs retention period. If this field is omitted in a new log entry, then Logging assigns it the current time. Timestamps have nanosecond accuracy, but trailing zeros in the fractional seconds might be omitted when the timestamp is displayed.

Incoming log entries must have timestamps that don't exceed the logs retention period in the past, and that don't exceed 24 hours in the future. Log entries outside those time boundaries are rejected by Logging.

A timestamp in RFC3339 UTC "Zulu" format, with nanosecond resolution and up to nine fractional digits. Examples: "2014-10-02T15:01:23Z" and "2014-10-02T15:01:23.045123456Z".

GCP allows {{ ORGANIZATION }} developers to write code and manage cloud resources, to include, using the internal system clocks of Google Servers to generate timestamps for audit logs that are generated by {{ ORGANIZATION }} {{ SYSTEM_NAME }}.

{{ ORGANIZATION }} {{ SYSTEM_NAME }} will have the minimum granularity of time measurement for event logging configured to one millisecond (synchronized across all GCP infrastructure servers via Google TrueTime / Network Time Protocol UTC).


## 9. Protection of Audit Information


### 9.1 Storing, Viewing, and Managing Logs


**Log Buckets**

Cloud Logging uses log buckets as containers in your Google Cloud projects, billing accounts, folders, and organizations to store and organize your logs data. The logs that you store in Cloud Logging are indexed, optimized, and delivered to let you analyze your logs in real time. Cloud Logging buckets are different storage entities than the similarly named Cloud Storage buckets.

For each Google Cloud project, billing account, folder, and organization, Logging automatically creates two log buckets: _Required and _Default. Logging automatically creates sinks named _Required and _Default that, in the default configuration, route logs to the correspondingly named buckets.

You can disable the _Default sink, which routes logs to the _Default log bucket. You can change the behavior of the _Default sinks created for any new Google Cloud projects or folders. For more information, see Configure default settings for organizations and folders.

You can't change routing rules for the _Required bucket.

Additionally, you can create user-defined buckets for any Google Cloud project.

You create sinks to route all, or just a subset, of your logs to any log bucket. This flexibility allows you to choose the Google Cloud project in which your logs are stored and what other logs are stored with them.


**_Required log bucket**

Cloud Logging automatically routes the following types of logs to the _Required bucket:

- Admin Activity audit logs

- System Event audit logs

- Google Workspace Admin Audit logs

- Enterprise Groups Audit logs

- Login Audit logs

- Access Transparency logs. For information about enabling Access Transparency logs, see the Access Transparency logs documentation.

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


### 9.2 Logging Roles

IAM provides predefined roles to grant granular access to specific Google Cloud resources and prevent unwanted access to other resources. Google Cloud creates and maintains these roles and automatically updates their permissions as necessary, such as when Logging adds new features.

The following list is the predefined roles for Logging:

- Logging Admin

- Logs Bucket Writer

- Logs Configuration Writer

- Log Field Accessor

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

To let a user read logs by using a log view on a log bucket, grant the Logs View Accessor (roles/logging.viewAccessor) role. You can restrict authorization to a specific log view on a specific log bucket. For information about creating log views and granting access, see Configure log views on a log bucket.

To give a user access to restricted LogEntry fields, if any, in a given bucket, grant the Logs Field Accessor (roles/logging.fieldAccessor) role. For more information, see Configure field-level access.

To let a user write logs by using the Logging API, grant the Logs Writer (roles/logging.logWriter) role. This role doesn't grant viewing permissions.

To let the service account of a sink route logs to a bucket in a different Google Cloud project, grant the service account the Logs Bucket Writer (roles/logging.bucketWriter) role.

This section focuses on technical protection of audit information. Physical protection of audit information is addressed by media protection controls and physical and environmental protection controls.

Regardless of the source of the discovery, coordination through the {{ ORGANIZATION }} Cybersecurity Team will occur upon the discovery of unauthorized access to, modification of, or deletion of audit logs or the capability.  This is to ensure the proper Incident Response is conducted and communicated up the proper chain of command.

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


### 9.3 Store on Separate Physical Systems or Components

{{ ORGANIZATION }} routes and stores audit records in a dedicated, isolated Log Archive repository (Google Cloud Logging aggregated organization sinks exporting to WORM-locked Cloud Storage buckets and BigQuery Log Sinks in a distinct audit project separate from {{ SYSTEM_NAME }}); this helps ensure that a compromise of {{ SYSTEM_NAME }} does not also result in a compromise of the audit records.


### 9.4 Cryptographic Protection

{{ ORGANIZATION }} uses Cloud KMS CMEK encryption and GCS bucket retention locks to protect the integrity of audit information.


### 9.5 Access by Subset of Privileged Users

GCP allows {{ ORGANIZATION }} developers to write code and manage cloud resources. Many of GCP services generate audit logs for {{ SYSTEM_NAME }}. {{ ORGANIZATION }} audit logs can only be viewed by users/groups with specific Identity and Access management roles. {{ ORGANIZATION }} can configure who can view and export audit logs within {{ SYSTEM_NAME }} and the GCP Project.


### 9.6 Dual Authorization

Dual Authorization Mechanisms, also known as two person control, require the approval of two authorized individuals to execute audit functions. To reduce the risk of collusion, {{ ORGANIZATION }} must consider rotating dual authorization duties to other individuals. Dual authorization mechanisms should not be required when immediate responses are necessary, to ensure public and environmental safety.

{{ ORGANIZATION }} enforces dual authorization for the movement or deletion of audit records.


### 9.7 Read-Only Access

Restricting privileged user or role authorizations to read-only helps to limit the potential damage to {{ ORGANIZATION }} that could be initiated by such users or roles, such as deleting audit records to cover up malicious activity.

{{ ORGANIZATION }} will restrict privileged users or specified roles to read-only access for audit records.


## 10. Non-Repudiation

Activities covered by non-repudiation include read, write, modify, and deletion of audit information. For auditing tools, non-repudiation includes installation, configuration, modification, and uninstalling tools.

Non-repudiation protects against claims by authors of not having authored certain documents, senders of not having transmitted messages, receivers of not having received messages, and signatories of not having signed documents.

Non-repudiation services can be used to determine if information originated from an individual or if an individual took specific actions.

{{ ORGANIZATION }} {{ SYSTEM_NAME }} enforces non-repudiation through Google Cloud Audit Logs cryptographically bound to immutable service account identities and hardware-backed Cloud Identity FIDO2/WebAuthn user credentials (`AU-10`).


## 11. Audit Record Retention

GCP allows {{ ORGANIZATION }} developers to write code and manage cloud resources. GCP retains Google-generated audit logs for at least 7 days for free tiered services and no longer than 30 days for premium tiers. It is {{ ORGANIZATION }} responsibility to offload these audit log records from the GCP Cloud Console and manage the retention of logs. {{ ORGANIZATION }} exports logs to dedicated Google Cloud Storage WORM log buckets and BigQuery analytical sinks to ensure proper compliance retention (`AU-11`).

{{ ORGANIZATION }} is responsible for the retention of audit records for customer applications within GCP. These end-user logs ("online logs") are retained by Google for at least 90 days. Google provides end-user domain administrators with controls over the retention of end-user application audit logs. End-user domain administrators are responsible for preserving audit records offline for a period that is in accordance with NARA.


### 11.1 Long-Term Retrieval Capability

{{ ORGANIZATION }} has a need to access and read audit records, requiring long-term storage. Measures employed to help facilitate the retrieval of audit records include converting records to newer formats, retaining equipment capable of reading the records, and retaining the necessary documentation to help personnel understand how to interpret the audit records.

{{ ORGANIZATION }} uses Google Cloud Storage dual-region buckets with Bucket Lock retention holds and BigQuery long-term table partitioning for long-term storage and high-speed analytical retrieval of audit records (`AU-11`).


## 12. Audit Record Generation

{{ ORGANIZATION }} {{ SYSTEM_NAME }}, all physical and logical components, must produce audit records. {{ ORGANIZATION }} must ensure each {{ SYSTEM_NAME }} component must be configured to collect audit records for the following security and operational events (`AU-12`):

- Admin Activity Audit Logs (recording all resource creation, IAM role assignments, and VPC security boundary modifications).
- System Event Audit Logs (recording automated platform actions, OS updates, and host live migration events).
- Data Access & Policy Intelligence Audit Logs (recording authentication attempts, BigQuery table reads, and GCS storage accesses).


### 12.1 System-Wide and Time-Correlated Audit Trail

A time stamp is the time the event described by the log entry occurred. This time is used to compute the log entry's age and to enforce the logs retention period. If this field is omitted in a new log entry, then Logging assigns it the current time. Timestamps have nanosecond accuracy, but trailing zeros in the fractional seconds might be omitted when the timestamp is displayed.

Incoming log entries must have timestamps that don't exceed the logs retention period in the past, and that don't exceed 24 hours in the future. Log entries outside those time boundaries are rejected by Logging.

A timestamp in RFC3339 UTC "Zulu" format, with nanosecond resolution and up to nine fractional digits. Examples: "2014-10-02T15:01:23Z" and "2014-10-02T15:01:23.045123456Z".

GCP allows {{ ORGANIZATION }} developers to write code and manage cloud resources, to include, using the internal system clocks of Google Servers to generate timestamps for audit logs that are generated by {{ ORGANIZATION }} {{ SYSTEM_NAME }}.

{{ ORGANIZATION }} {{ SYSTEM_NAME }} will have the minimum granularity of time measurement for event logging configured to one millisecond (synchronized across all GCP infrastructure servers via Google TrueTime / Network Time Protocol UTC).


### 12.2 Changes by Authorized Individuals

Permitting authorized individuals to make changes to system logging enabled {{ ORGANIZATION }} to extend or limit logging as necessary to meet organizational requirements. Logging that is limited to conserve {{ SYSTEM_NAME }} resources may be extended to address certain threat situations. In addition, logging may be limited to a specific set of event types to facilitate audit reduction, analysis, and reporting. {{ ORGANIZATION }} established threshold of System security incident or elevated risk status.


## 13. Session Audit

Session Audits can include monitoring keystrokes, tracking websites visited, and recording information and/or file transfers. Session audit capability is implemented in addition to event logging and may involve implementation of specialized session capture technology.

{{ ORGANIZATION }} provides and implements Google Access Transparency & Cloud Audit Logs to audit administrative user session activities.


### 13.1 System Start-Up

{{ ORGANIZATION }} configures Cloud Audit Logs to initiate session audits automatically at {{ SYSTEM_NAME }} startup.


### 13.2 Remote View and Listening

{{ ORGANIZATION }} configures Cloud Logging & IAP Session Auditing to provide session audit visibility.



## Appendix A – Detailed Compliance Matrix

The following table provides detailed traceability between the policy implementation statements in this document, the authoritative NIST SP 800-53 Rev. 5 control requirements, DoD CCIs, and the technical/governance enforcement mechanisms active across {{ SYSTEM_NAME }}.


| CTRL ID | CTRLTITLE | REQUIRED eMASS STANDARD | DOCREF | ENFORCEMENT MECHANISM |
| :--- | :--- | :--- | :--- | :--- |
| AU-01 | Policy and Procedures | Develop, document, disseminate to all personnel, and review/update annually (or upon SIEM upgrades, OS schema changes, or security incidents) audit policy and procedures. (CCIs: 000117, 000119, 000120, 000122, 001569, 001570, 001832, 001834, 001930, 001931, 003799, 003800, 003801, 003802, 003803, 003804, 003805, 003806, 003807, 003808, 003809) | Section 2.1 | Formal annual review workflow by {{ ORGANIZATION }} ISSM/SO/AO; publishing to eMASS repository; incident-driven update triggers. |
| AU-02 | Event Logging | Identify and log successful and unsuccessful attempts for all auditable events per CNSSI 1015; review event types at least annually. (CCIs: 000123, 000124, 000125, 000126, 001484, 001485, 001571, 003810, 003811) | Section 2.2 | Google Cloud Audit Logs (Admin Activity & Data Access); VPC Flow Logs; annual logging taxonomy reviews. |
| AU-03 | Content of Audit Records | Ensure audit records capture what, when, where, source, outcome, and user identity across all system events. (CCIs: 000130, 000131, 000132, 000133, 000134, 001487) | Section 2.2 | Cloud Logging structured JSON schema containing caller IP, principal email, method name, timestamp, and status. |
| AU-03(01) | Additional Audit Information | Collect additional audit details including full-text privileged command execution and individual identities. (CCIs: 000135, 001488) | Section 2.2 | Full-text gcloud CLI logging; Cloud Audit request/response payload capture; IAP session identity binding. |
| AU-03(03) | Limit Personally Identifiable Information Elements | Limit PII contained in audit records to User ID, {{ USER_IDENTIFIER_TYPE }}, and terminal ID as authorized by the Privacy Impact Assessment. (CCIs: 003812, 003813) | Section 2.2 | Cloud DLP inspection templates; automated PII redaction filters; strict payload exclusion policies. |
| AU-04 | Audit Log Storage Capacity | Allocate elastic audit log storage capacity ensuring at least 90 days online and 365 days archived storage per OMB M-21-31. (CCIs: 001848, 001849) | Section 2.3 | Elastic Cloud Logging buckets; BigQuery 90-day active partitioning; dual-region Cloud Storage long-term archive. |
| AU-04(01) | Transfer to Alternate Storage | Transfer audit records from logging components to central storage repositories in real time for interconnected systems. (CCIs: 001850, 001851) | Section 2.3 | Aggregated organization log sinks streaming via Pub/Sub topics to BigQuery and Enterprise SIEM in real time. |
| AU-05 | Response to Audit Logging Process Failures | Take automated action to minimize data loss, alert ISSM/ISSO in near real time (15 mins), and enforce fail-secure posture. (CCIs: 000139, 000140, 001490, 001572, 003814) | Section 2.3 | Cloud Monitoring automated alert policies; Pub/Sub dead-letter queues; fail-secure administrative access restrictions. |
| AU-05(01) | Storage Capacity Warning | Provide automated warnings to ISSM/ISSO in near real time when allocated audit storage reaches 75% capacity. (CCIs: 001852, 001853, 001854, 001855) | Section 2.3 | Cloud Monitoring metric alerts and billing threshold alerts configured at 75% log volume capacity. |
| AU-05(02) | Real-Time Alerts | Provide near real-time automated alerts upon detection of critical logging failure events (CMEK failure, bucket lock failure). (CCIs: 000147, 001856, 001857, 001858) | Section 2.3 | Real-time Cloud Monitoring alerting policies dispatched to ISSO/ISSM and SOC via automated webhook/email channels. |
| AU-06 | Audit Record Review, Analysis, and Reporting | Review and analyze audit records at least every 7 days (and continuously via automation) for anomalous activity; report to ISSO/ISSM. (CCIs: 000148, 000149, 000151, 001862, 001863, 003817, 003818, 003819) | Section 2.4 | {{ TELEMETRY_PIPELINE }}; {{ THREAT_DETECTION_ENGINE }}; weekly manual ISSO audit reviews and {{ SIEM_TOOL }} correlation. |
| AU-06(01) | Automated Process Integration | Integrate audit review, analysis, and reporting using a centralized SIEM and SOAR platform for automated incident response. (CCIs: 001864, 001865, 003820) | Section 2.4 | Enterprise {{ SIEM_TOOL }} ({{ CSSP_PROVIDER }}) ingestion via {{ TELEMETRY_PIPELINE }} and Pub/Sub; automated containment playbooks. |
| AU-06(03) | Correlate Audit Record Repositories | Correlate audit records across disparate repositories, cloud spokes, and VPC network perimeters to gain global situational awareness. (CCIs: 000153) | Section 2.4 | Centralized SIEM cross-cloud log correlation; analytics views spanning all authorized system projects and accounts. |
| AU-06(04) | Central Review and Analysis | Establish centralized repository for organization audit logs and conduct centralized security review and analysis. (CCIs: 000154, 003821) | Section 2.4 | Aggregated organization-level Cloud Logging sinks exporting to central telemetry BigQuery master warehouse. |
| AU-06(05) | Integrated Analysis of Audit Records | Integrate audit log analysis with vulnerability scan results, network performance metrics, and system monitoring data. | Section 2.4 | SIEM multi-source data ingestion linking Semgrep/Checkov scan reports, system telemetry, and audit trails. |
| AU-06(06) | Correlation with Physical Monitoring | Correlate physical facility access records with logical audit logs to identify anomalous cross-domain activities. | Section 2.4 | Inherited from Google Cloud Services P-ATO data center physical access controls; logical access logs correlated via Cloud Logging and enterprise SIEM. |
| AU-07 | Audit Record Reduction and Report Generation | Provide on-demand audit reduction and report generation capabilities without altering original event records or timestamps. (CCIs: 001875, 001876, 001877, 001878, 001879, 001880, 001881, 001882, 003822, 003823, 003824, 003825, 003826, 003827, 003828, 003829) | Section 2.4 | BigQuery analytical views and SIEM reporting engines generating immutable summary reports. |
| AU-07(01) | Automatic Processing | Provide automatic processing to sort, filter, and search audit records by timestamp, user, IP, event type, and outcome. (CCIs: 000158, 001883, 003830) | Section 2.4 | BigQuery SQL indexing and SIEM indexed search filters across all standardized audit record metadata fields. |
| AU-08 | Time Stamps | Synchronize system clocks to authoritative Stratum-1 sources and record audit timestamps in RFC 3339 UTC with 1ms granularity. (CCIs: 000159, 001888, 001889, 001890) | Section 2.5 | Google TrueTime and DoD NTP synchronization; nanosecond RFC 3339 UTC timestamping in Cloud Logging. |
| AU-09 | Protection of Audit Information | Protect audit records against unauthorized access, modification, and deletion; alert ISSM/ISSO on tampering attempts. (CCIs: 000162, 000163, 000164, 001493, 001494, 001495, 003831, 003832) | Section 2.6 | Cloud IAM permission boundaries; immutable log sink architectures; real-time alerting on log deletion attempts. |
| AU-09(02) | Store on Separate Physical Systems or Components | Store audit records in a dedicated repository physically and logically separated from the system being audited every 7 days (real time). (CCIs: 001348, 001349) | Section 2.6 | Isolated central telemetry logging project and landing zone audit vaults distinct from transit projects. |
| AU-09(03) | Cryptographic Protection | Protect audit record integrity using Cloud KMS CMEK encryption and GCS Bucket Lock WORM retention policies. (CCIs: 001350, 001496) | Section 2.6 | FIPS 140-3 Cloud KMS HSM keys; GCS Object Retention Lock (SEC Rule 17a-4 compliant). |
| AU-09(04) | Access by Subset of Privileged Users | Restrict management of audit logging functionality strictly to an authorized subset of privileged security administrators. (CCIs: 001351, 001894) | Section 2.6 | Fine-grained IAM roles (roles/logging.admin, roles/logging.configWriter) restricted to ISSM/ISSO personnel. |
| AU-09(06) | Read-Only Access | Restrict privileged audit access for auditors and CSSP personnel to read-only permissions. (CCIs: 001897, 001898) | Section 2.6 | IAM read-only roles (roles/logging.viewer, roles/logging.privateLogViewer, roles/bigquery.dataViewer). |
| AU-10 | Non-Repudiation | Enforce non-repudiation for all administrative actions and resource modifications in accordance with DoDI 8520.02. (CCIs: 000166, 001899) | Section 2.7 | Cryptographic binding to {{ IDENTITY_PROVIDER }} with {{ MFA_MECHANISM }} credentials and Workload Identity Federation (WIF) OIDC claims. |
| AU-10(01) | Association of Identities | Bind the identity of the information producer with the information at an assurance level commensurate with {{ IMPACT_LEVEL }} data. (CCIs: 001900, 001901, 001902) | Section 2.7 | Immutable digital identity logging in Cloud Audit Logs; signed OIDC token validation; hardware token assertions ({{ MFA_MECHANISM }}). |
| AU-11 | Audit Record Retention | Retain audit records for a minimum of 365 calendar days (1 year) in compliance with CNSSI 1015 and OMB M-21-31. (CCIs: 000167, 000168) | Section 2.8 | GCS bucket retention policies set to 365 days; BigQuery long-term table partition retention management. |
| AU-11(01) | Long-Term Retrieval Capability | Ensure long-term audit records remain retrievable and queryable in standardized non-proprietary formats. (CCIs: 002044, 002045) | Section 2.8 | Standardized JSON/Parquet storage formats in GCS; BigQuery federated queries across long-term partitions. |
| AU-12 | Audit Record Generation | Ensure audit generation capabilities are enabled across all system components and managed by ISSM/ISSO. (CCIs: 000169, 000171, 000172, 001459, 001910) | Section 2.9 | Universal Cloud Logging enablement via organization policy; Terraform baseline audit module deployment. |
| AU-12(01) | System-Wide and Time-Correlated Audit Trail | Compile audit records from all components into a system-wide audit trail time-correlated within 1 millisecond. (CCIs: 000173, 000174, 001577) | Section 2.9 | Aggregated organization log sinks; TrueTime synchronization ensuring sub-millisecond correlation across all spokes. |
| AU-12(03) | Changes by Authorized Individuals | Enable authorized administrators to dynamically modify logging parameters within 4 hours based on operational needs. (CCIs: 001911, 001912, 001913, 001914, 002047, 003834) | Section 2.9 | Terraform IaC pipeline triggers and Cloud Logging API dynamic filter updates executed within 4 hours. |
| AU-13 | Monitoring for Information Disclosure | Continuously monitor open-source repositories and public sites for unauthorized disclosure of system data. (CCIs: 001460, 001461, 001915, 003837, 003838, 003839, 003840) | Section 2.10 | Automated CI/CD secret scanning (Gitleaks); public repository monitoring; immediate {{ CSSP_PROVIDER }} escalation workflows. |
| AU-14 | Session Audit | Provide capability to log, record, view, and analyze administrative session content during incident investigations. (CCIs: 001919, 003844, 003845, 003846, 003847) | Section 2.10 | Google Access Transparency; Cloud Audit Logs; Identity-Aware Proxy (IAP) TCP session stream logging. |
| AU-14(01) | System Start-Up | Automatically initiate session auditing capabilities at system startup across all transit components. (CCIs: 001464) | Section 2.10 | Default Cloud Logging startup daemon configuration; automated IAP session capture initiation. |
| AU-14(03) | Remote Viewing and Listening | Provide authorized incident responders remote session auditing visibility during active security investigations. (CCIs: 001920, 003848) | Section 2.10 | Role-based IAP tunnel auditing; Cloud Audit Log live stream inspection for certified forensic analysts. |
| AU-16 | Cross-Organizational Audit Logging | Coordinate and standardize audit logging when information is transmitted across organizational boundaries. (CCIs: 001923, 001924, 001925) | Section 2.10 | Automated STIX/TAXII threat sharing; standardized RFC 5424 Syslog forwarding to central logging and {{ CSSP_PROVIDER }} boundaries. |
| AU-16(01) | Automated Integration of Cross-Organizational Audit Logging | Integrate cross-organizational audit logs automatically using standardized schemas across connected systems. (CCIs: 001926) | Section 2.10 | Automated Pub/Sub cross-project subscriptions; normalized JSON security feeds to {{ SIEM_TOOL }}. |
| AU-16(02) | Sharing of Audit Information | Provide cross-organizational audit information to USCYBERCOM, JFHQ-DODIN, and CSSPs under binding SLAs. (CCIs: 001927, 001928, 001929) | Section 2.10 | Automated SIEM peering feeds; secure API log export to CSSP analysis platforms under DoD sharing agreements. |
