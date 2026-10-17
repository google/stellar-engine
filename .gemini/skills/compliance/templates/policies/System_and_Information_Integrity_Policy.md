# SI - System and Information Integrity Policy and Procedures

## Document Governance & Approval Baseline

| Governance Metric | Policy Standard & Specification |
| :--- | :--- |
| **Document Title** | System and Information Integrity Policy and Procedures |
| **NIST Control Family** | System and Information Integrity (SI) |
| **Primary NIST Benchmark** | NIST SP 800-40 Rev. 4 (Enterprise Patch Management), NIST SP 800-83 Rev. 1 (Malware Incident Prevention and Handling) |
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
> This document defines the enterprise security policy and implementation procedures for **System and Information Integrity** under **NIST SP 800-53 Rev. 5 (SI)**.
> Technical infrastructure controls are automatically provisioned and enforced via **{{ SYSTEM_NAME }}** Terraform blueprints.
> Operational rules or contact details requiring manual confirmation are highlighted with RMF Team Callouts.


## 1. Overview

Federal agencies and organizations cannot protect the confidentiality, integrity, and availability of information in today's highly networked systems environment without ensuring that all people involved in using and managing IT:

1. Understand their roles and responsibilities related to the organizational mission;
2. Understand the organization's IT security policy, procedures, and practices; and
3. Have at least adequate knowledge of the various management, operational, and technical controls required and available to protect the IT resources for which they are responsible.

The purpose of this System and Information Integrity Policy is to protect the integrity of {{ SYSTEM_NAME }} and its information by identifying and remediating flaws within established severity SLAs (Critical <= 15 days, High <= 30 days, Moderate <= 90 days), protecting against malicious code, monitoring the system for attacks and anomalies, and responding to security alerts and advisories.

This policy addresses the System and Information Integrity (SI) family requirements of NIST Special Publication 800-53 Revision 5, "Security and Privacy Controls for Information Systems and Organizations." A detailed compliance matrix is provided in Appendix A, "Detailed Compliance Matrix."

The System and Information Integrity Policy encompasses all {{ ORGANIZATION }} users who have access to {{ SYSTEM_NAME }}. This policy outlines the framework for establishing, implementing, and maintaining system and information integrity in alignment with applicable {{ GOVERNANCE_REGIME }} guidelines (NIST SP 800-53, FedRAMP, and applicable federal and state regulations), and is consistent with applicable laws, executive orders, directives, regulations, policies, standards, and guidelines. It applies to employees, contractors, and third-party users who handle sensitive information or operate within the {{ ORGANIZATION }} {{ SYSTEM_NAME }} information technology infrastructure.

{{ ORGANIZATION }} management is committed to the requirements of this policy and provides the resources needed to implement them. The ISSM ({{ ISSM_NAME }}) manages the development, documentation, and dissemination of this policy and its procedures, and coordinates their implementation with the Authorizing Official, System Owner, ISSO, and other organizational entities identified in the Program Roles & Responsibilities Matrix.

This policy and its procedures are reviewed and updated at least annually and following significant changes to {{ SYSTEM_NAME }} or its operating environment, security or privacy incidents, assessment or audit findings, or changes in applicable laws, executive orders, directives, regulations, policies, standards, or guidelines.


## 2. Flaw Remediation

The need to remediate system flaws applies to all types of software and firmware. Organizations identify systems affected by software flaws, including potential vulnerabilities resulting from those flaws, and report this information to designated organizational personnel with information security and privacy responsibilities.

{{ ORGANIZATION }} identifies, reports, and corrects all system flaws that are discovered through security assessments, continuous monitoring, incident response activities, or system error handling, using resources such as the Common Weakness Enumeration (CWE) and Common Vulnerabilities and Exposures (CVE) databases.

{{ ORGANIZATION }} tests software and firmware updates related to flaw remediation for effectiveness and potential side effects before installation.

{{ ORGANIZATION }} installs security-relevant software and firmware updates within 30 days of the release of the updates.

{{ ORGANIZATION }} incorporates flaw remediation into the configuration management process for {{ SYSTEM_NAME }}.


### 2.1 Automated Flaw Remediation Status & Continuous Threat Posture

{{ THREAT_DETECTION_IMPLEMENTATION }}


### 2.2 Flaw Remediation Benchmarks and Automated Patch Management

{{ VULNERABILITY_MANAGEMENT_IMPLEMENTATION }}


### 2.3 Removal of Previous Versions of Software and Firmware

{{ ORGANIZATION }} removes previous versions of software and firmware after updated versions have been installed.


### 2.4 Root Cause Analysis

{{ ORGANIZATION }} conducts a root cause analysis of [CONFIG_REQUIRED: issues and failures that require root cause analysis, e.g., security incidents and critical or recurring flaws], develops actions that address the root cause, implements those actions, and monitors their implementation for effectiveness. Corrective actions are tracked in the POA&M.


### 2.5 Google Cloud Platform (GCP) Inherited Controls & Shared Responsibility Boundary

- **Google Inherited Controls**: Google Cloud provides underlying infrastructure malware scanning (`SI-3`), hypervisor integrity monitoring (`SI-7`), and platform flaw remediation (`SI-2`).
- **Customer Implementation Responsibilities**: {{ ORGANIZATION }} is responsible for automated patch management (`SI-2`), continuous monitoring via {{ TELEMETRY_PIPELINE }} (`SI-4`), Binary Authorization container signature verification (`SI-7`), and Cloud Storage integrity checks (`SI-7`).

## 3. Malicious Code Protection

Malicious code includes viruses, worms, Trojan horses, and spyware. Malicious code can also be encoded in various formats contained within compressed or hidden files or hidden in files using techniques such as steganography. Malicious code can be inserted into systems in a variety of ways, including by electronic mail, the world-wide web, and portable storage devices. Malicious code insertions occur through the exploitation of system vulnerabilities. A variety of technologies and methods exist to limit or eliminate the effects of malicious code.

{{ ORGANIZATION }} implements signature-based and anomaly-based malicious code protection mechanisms at {{ SYSTEM_NAME }} entry and exit points to detect and eradicate malicious code.

In line with {{ ORGANIZATION }} configuration management policy for {{ SYSTEM_NAME }}, automated malicious code detection is integrated via {{ TELEMETRY_PIPELINE }} and {{ THREAT_DETECTION_ENGINE }}.

{{ ORGANIZATION }} will ensure the following configurations are implemented:

- Configure automated malicious code detection to perform periodic scans of {{ SYSTEM_NAME }} and real-time scans of files from external sources as the files are downloaded, opened, and executed.

- Quarantine malicious code and send an alert to the organizational ISSO and Security Operations Center (SOC) in response to malicious code detection.

{{ ORGANIZATION }} reviews malicious code detection alerts for false positives and addresses their potential impact on the availability of {{ SYSTEM_NAME }}.


### 3.1 Malicious Code Analysis

{{ ORGANIZATION }} implements automated malicious code analysis via {{ TELEMETRY_PIPELINE }} and {{ THREAT_DETECTION_ENGINE }} to analyze the characteristics and behavior of malicious code and to incorporate the results from malicious code analysis into incident response and flaw remediation processes.


## 4. System Monitoring

{{ ORGANIZATION }} implements continuous system monitoring for {{ SYSTEM_NAME }} across all Google Cloud project workloads. System monitoring capabilities include:

- **Real-time Threat Detection**: {{ TELEMETRY_PIPELINE }} and {{ THREAT_DETECTION_ENGINE }};
- **VPC Network Monitoring**: VPC Flow Logs, Firewall Rule Audit Logging, and Packet Mirroring to track network traffic patterns;
- **Workload Observability**: Cloud Monitoring metrics and alert policies triggering notifications for high CPU/memory utilization, error spikes, and unauthorized API calls;
- **Container & Host Security**: Artifact Registry vulnerability scanning and VM Manager OS patch tracking;
- **Centralized SIEM Ingestion**: Exporting audit logs and security findings via Cloud Pub/Sub to BigQuery and {{ EXTERNAL_SIEM }} for near real-time security analytics.


### 4.1 System-Wide Intrusion Detection System

{{ ORGANIZATION }} connects and configures {{ INTRUSION_DETECTION_SYSTEM }} and {{ TELEMETRY_PIPELINE }} into a system-wide intrusion detection system, with alerts and findings aggregated in {{ EXTERNAL_SIEM }}.


### 4.2 Automated Tools and Mechanisms for Real-Time Analysis

{{ ORGANIZATION }} employs Google BigQuery and {{ EXTERNAL_SIEM }} to support near real-time analysis of events.


### 4.3 Inbound and Outbound Communications Traffic

By default, all unsolicited inbound and outbound traffic is blocked. Ingress and egress firewall policies and security groups are centrally defined and managed via Infrastructure-as-Code modules. Cloud Virtual Private Cloud (VPC) firewall rules control traffic in priority order. Rules specify which protocols (TCP, UDP, ICMP, etc.) and ports (such as 443 for HTTPS) are permitted, with all unlisted traffic denied by default.

{{ ORGANIZATION }} defines criteria for unusual or unauthorized inbound and outbound communications traffic, such as traffic on unapproved protocols or ports or to unapproved destinations, and monitors inbound and outbound traffic against those criteria continuously using VPC Flow Logs and Firewall Rules Logging.


### 4.4 System Generated Alerts

Alerts may be generated from a variety of sources, including audit records or inputs from malicious code protection mechanisms, intrusion detection or prevention mechanisms, or boundary protection devices such as firewalls, gateways, and routers.

Alerts can be automated and may be transmitted telephonically, by electronic mail messages, or by text messaging.

> [!IMPORTANT]
> [WARNING: RMF TEAM ACTION REQUIRED: Verify and update operational contact/procedure details in this section.]
> {{ ORGANIZATION }} will alert system administrators, mission or business owners, system owners, information owners/stewards, senior agency information security officers, senior agency officials for privacy, system security officers, or privacy officers when the following system-generated indications of compromise or potential compromise occur:

- Unauthorized IAM privilege escalations or service account key creation

- Anomalous outbound data egress from VPC Service Controls perimeters

- Disabling of Cloud Audit Logging sinks or {{ THREAT_DETECTION_ENGINE }} policies


### 4.5 Visibility of Encrypted Communication

Organizations balance the need to encrypt communications traffic to protect data confidentiality with the need to maintain visibility into such traffic from a monitoring perspective.

{{ ORGANIZATION }} determines whether the visibility requirement applies to internal encrypted traffic, encrypted traffic intended for external destinations, or a subset of the traffic types.

{{ ORGANIZATION }} will make provisions so that identified encrypted communication traffic is visible to {{ INTRUSION_DETECTION_SYSTEM }} and {{ EXTERNAL_SIEM }}.


### 4.6 Analyze Communications Traffic Anomalies

{{ ORGANIZATION }} analyzes outbound communications traffic at the external interfaces of {{ SYSTEM_NAME }} and at internal network boundaries to discover anomalies. Network flow logs, firewall audit logs, and intrusion detection telemetry are continuously ingested into centralized SIEM and monitoring pipelines to identify unexpected traffic spikes, unauthorized cross-segment communications, and data exfiltration patterns.


### 4.7 Automated Organization-Generated Alerts

> [!IMPORTANT]
> [WARNING: RMF TEAM ACTION REQUIRED: Verify and update operational contact/procedure details in this section.]
> {{ ORGANIZATION }} personnel on the system alert notification list include system administrators, mission or business owners, system owners, senior agency information security officer, senior agency official for privacy, system security officers, or privacy officers.

{{ ORGANIZATION }} will alert personnel on the system alert notification list using Google Cloud Monitoring Alerting Policies when the following indications of inappropriate or unusual activities with security or privacy implications occur:

- Unusual root or organization admin access from non-CONUS IP ranges

- Multiple consecutive failed administrative authentication attempts

- Modification of firewall rules allowing public 0.0.0.0/0 ingress


### 4.8 Wireless Intrusion Detection

{{ ORGANIZATION }} employs Google data center infrastructure monitoring (inherited from Google Cloud) to identify rogue wireless devices and to detect attack attempts and potential compromises or breaches to {{ SYSTEM_NAME }}. Wireless access is prohibited within the {{ SYSTEM_NAME }} boundary.


### 4.9 Wireless to Wireline Communications

{{ ORGANIZATION }} employs Google data center infrastructure security controls (inherited from Google Cloud) to monitor wireless communications traffic as the traffic passes from wireless to wireline networks.


### 4.10 Correlate Monitoring Information

{{ ORGANIZATION }} uses {{ EXTERNAL_SIEM }} to correlate information from the monitoring tools and mechanisms employed throughout {{ SYSTEM_NAME }}.


### 4.11 Risk for Individuals

> [!IMPORTANT]
> [WARNING: RMF TEAM ACTION REQUIRED: Verify and update operational contact/procedure details in this section.]
> Indications of increased risk from individuals can be obtained from different sources, including personnel records, intelligence agencies, law enforcement organizations, and other sources. The monitoring of individuals is coordinated with the management, legal, security, privacy, and human resource officials who conduct such monitoring.

{{ ORGANIZATION }} implements additional monitoring (keystroke logging, real-time command auditing, and session capture on administrative bastion hosts) of individuals identified by these sources as posing an increased level of risk, and conducts this monitoring in accordance with applicable laws, executive orders, directives, regulations, policies, standards, and guidelines.


### 4.12 Privileged Users

Privileged users have access to more sensitive information, including security-related information, than the general user population. Access to such information means that privileged users can potentially do greater damage to systems and organizations than non-privileged users.

{{ ORGANIZATION }} implements the following additional monitoring of privileged users: Cloud Audit Logs Admin Activity and Data Access logging of all privileged actions, exported to write-once log sinks and reviewed in {{ EXTERNAL_SIEM }}.


### 4.13 Unauthorized Network Services

{{ ORGANIZATION }} uses {{ THREAT_DETECTION_ENGINE }} findings and open-port discovery scans to detect network services that have not been authorized or approved through the {{ ORGANIZATION }} configuration management process, and audits the event and alerts the ISSO when such a service is detected.


### 4.14 Host-Based Devices

{{ ORGANIZATION }} implements {{ EDR_SOLUTION }}, Google Cloud Ops Agent, and Cloud Monitoring telemetry sinks on {{ SYSTEM_NAME }} components.


### 4.15 Indicators of Compromise

Indicators of compromise (IOC) are forensic artifacts from intrusions that are identified on organizational systems at the host or network level. IOCs provide valuable information on systems that have been compromised.

{{ ORGANIZATION }} discovers and collects IOCs from<!-- IF DOD_ENCLAVE --> USCYBERCOM and<!-- ENDIF --> {{ CSSP_PROVIDER }} and CISA threat intelligence feeds ingested into {{ EXTERNAL_SIEM }}, and distributes them to the ISSO, ISSM, and incident response personnel.


### 4.16 Optimize Network Traffic Analysis

{{ ORGANIZATION }} uses Packet Mirroring and VPC Flow Logs to provide visibility into network traffic at external and key internal {{ SYSTEM_NAME }} interfaces to optimize the effectiveness of monitoring devices.


## 5. Security Alerts, Advisories, and Directives

> [!IMPORTANT]
> [WARNING: RMF TEAM ACTION REQUIRED: Verify and update operational contact/procedure details in this section.]
> The Cybersecurity and Infrastructure Security Agency (CISA, formerly US-CERT) generates security alerts and advisories to maintain situational awareness across the federal government. Security directives are issued by OMB or other designated organizations with the responsibility and authority to issue such directives. Compliance with security directives is essential due to the critical nature of many of these directives and the potential immediate adverse effects on organizational operations and assets, individuals, other organizations, and the Nation should the directives not be implemented within the required time frames. External organizations include, for example, external mission/business partners, supply chain partners, external service providers, and other peer/supporting organizations.

> [!IMPORTANT]
> [WARNING: RMF TEAM ACTION REQUIRED: Verify and update operational contact/procedure details in this section.]
> The {{ ORGANIZATION }} ISSM will be registered to automatically receive notifications from<!-- IF DOD_ENCLAVE --> USCYBERCOM<!-- ENDIF --><!-- IF NOT DOD_ENCLAVE --> CISA<!-- ENDIF -->. The {{ ORGANIZATION }} ISSM will distribute the notifications to affected personnel, including the ISSO, system administrators, and other affected stakeholders.

{{ ORGANIZATION }} uses the DoD-approved vulnerability management system for compliance reporting to verify that security directives are implemented within established time frames, and notifies the issuing organization of the degree of noncompliance when they are not.


### 5.1 Automated Alerts and Advisories

{{ ORGANIZATION }} uses Cloud Monitoring and Pub/Sub notification channels to broadcast security alerts and advisory information throughout the organization.


## 6. Security and Privacy Function Verification

{{ ORGANIZATION }} lists the following functions as security and privacy functions for {{ SYSTEM_NAME }}:

- VPC Service Controls Perimeter Guardrails

- Cloud KMS Customer-Managed Encryption Key Rotation

- Cloud Audit Logs Ingestion & Immutable Storage

{{ ORGANIZATION }} verifies quarterly the correct operation of all listed security and privacy functions.

{{ ORGANIZATION }} {{ SYSTEM_NAME }} provides system notifications, such as hardware indicator lights, electronic alerts to system administrators, and messages to local computer consoles, when anomalies are discovered.


### 6.1 Report Verification Results

{{ ORGANIZATION }} reports the results of security and privacy function verification to systems security officers, senior agency information security officers, and senior agency officials for privacy.


## 7. Software, Firmware, and Information Integrity

Unauthorized changes to software, firmware, and information can occur due to errors or malicious activity. The {{ ORGANIZATION }} {{ SYSTEM_NAME }} software list documents the software and firmware subject to integrity verification. {{ ORGANIZATION }} employs container image signature verification (e.g., Binary Authorization where authorized in the accreditation boundary, or CI/CD cosign attestation) and Artifact Registry to verify container image signatures before deployment, and Shielded VM integrity monitoring (UEFI Secure Boot and vTPM) to verify virtual machine boot components.


### 7.1 Integrity Checks

Integrity checks of {{ ORGANIZATION }} {{ SYSTEM_NAME }} information, software, and firmware occur:

- During vulnerability scans;

- At the completion of the installation of new hardware, software, or firmware;

- On demand when there is a security-relevant event involving the hardware, software, or firmware; and

- Continuously or at least every 30 days for any additional internal scans.


### 7.2 Automated Notifications of Integrity Violations

{{ ORGANIZATION }} employs container image signature verification (e.g., Binary Authorization where authorized in the accreditation boundary, or CI/CD cosign attestation) to provide notification to identified stakeholders upon discovering discrepancies during integrity verification.


### 7.3 Automated Response to Integrity Violations

{{ ORGANIZATION }} employs container image signature verification (e.g., Binary Authorization where authorized in the accreditation boundary, or CI/CD cosign attestation) to block deployment and isolate the affected workload when integrity violations are discovered.


### 7.4 Integration of Detection and Response

{{ ORGANIZATION }} incorporates the detection of unauthorized security-relevant changes to {{ SYSTEM_NAME }} into the incident response process. The audit logs and other logs below support that detection.


#### 7.4.1 Audit Logs

The following are all audit logs that are collected and stored within Google Cloud:

- Admin Activity Logs - Admin Activity audit logs contain log entries for API calls or other actions that modify the configuration or metadata of resources. For example, these logs record when users create VM instances or change Identity and Access Management permissions.

- Data Access Logs - Data Access audit logs contain API calls that read the configuration or metadata of resources, as well as user-driven API calls that create, modify, or read user-provided resource data.

- System Event Logs - System Event audit logs contain log entries for Google Cloud actions that modify the configuration of resources. System Event audit logs are generated by Google systems; they aren't driven by direct user action.


#### 7.4.2 Other Logging

VPC Flow Logs - VPC Flow Logs record a sample of network flows sent from and received by VM instances, including instances used as GKE nodes. These logs can be used for network monitoring, forensics, real-time security analysis, and expense optimization.

Firewall Rule Logs - Firewall Rules Logging lets you audit, verify, and analyze the effects of your firewall rules. For example, you can determine if a firewall rule designed to deny traffic is functioning as intended. Firewall Rules Logging is also useful if you need to determine how many connections are affected by a given firewall rule.

Access Transparency Logs - Access Transparency logs include data about Google staff activity, including:

- Actions by the Support team that you may have requested by phone

- Basic engineering investigations into your support requests

- Other investigations made for valid business purposes, such as recovering from an outage


#### 7.4.3 Log Destinations

Audit logs and other logs are routed to the following destinations and retained as specified in Section 11:

- BigQuery

- Cloud Storage

- Pub/Sub

When a log destination is in a different project, the log sink's writer identity (service account) must be granted permission to write to the destination. If VPC Service Controls or other restrictions apply, the writer identity must also be granted access through them.


### 7.5 Auditing Capability for Significant Events

Upon detection of a potential integrity violation, {{ ORGANIZATION }} uses container image signature verification (e.g., Binary Authorization where authorized in the accreditation boundary, or CI/CD cosign attestation) to audit the event, generate an audit record, alert identified individuals, and alert the current user.


### 7.6 Verify Boot Process

Ensuring the integrity of boot processes is critical to starting system components in known, trustworthy states.

{{ ORGANIZATION }} employs Shielded VM Secure Boot, Measured Boot (vTPM), and integrity monitoring to verify the integrity of the boot process for {{ SYSTEM_NAME }} virtual machines.


### 7.7 Protection of Boot Firmware

Unauthorized modifications to boot firmware may indicate a sophisticated, targeted attack. These types of targeted attacks can result in a permanent denial of service or a persistent malicious code presence. These situations can occur if the firmware is corrupted or if the malicious code is embedded within the firmware.

{{ ORGANIZATION }} protects the integrity of boot firmware for {{ SYSTEM_NAME }} with the Google Titan security chip hardware root of trust (inherited from Google Cloud) and Shielded VM Secure Boot, which verifies the signatures of VM boot components.


### 7.8 Code Authentication

Cryptographic authentication includes verifying that software or firmware components have been digitally signed using certificates recognized and approved by organizations. Code signing is an effective method to protect against malicious code.

{{ ORGANIZATION }} implements container image signature verification (e.g., Binary Authorization where authorized in the accreditation boundary, or CI/CD cosign attestation) signed container policies to authenticate all software and firmware prior to installation.


### 7.9 Runtime Application Self-Protection

Runtime application self-protection employs runtime instrumentation to detect and block the exploitation of software vulnerabilities by taking advantage of information from the software in execution. Runtime exploit prevention differs from traditional perimeter-based protections such as guards and firewalls which can only detect and block attacks by using network information without contextual awareness. Runtime application self-protection technology can reduce the susceptibility of software to attacks by monitoring its inputs and blocking those inputs that could allow attacks.

{{ ORGANIZATION }} implements Google Cloud Armor WAF (where authorized in the accreditation boundary) and GKE Security Posture controls for application self-protection at runtime.


## 8. Spam Protection

Spam can be transported by different means, including email, email attachments, and web accesses.

{{ ORGANIZATION }} employs enterprise email gateway spam and phishing protection (via {{ IDENTITY_PROVIDER }} / organizational messaging gateways) at external entry and exit points to detect and act on unsolicited messages (`SI-8`). Spam protection mechanisms are updated automatically when new releases are available, in accordance with the {{ ORGANIZATION }} configuration management policy.


## 9. Information Input Validation

Checking the valid syntax and semantics of system inputs (including character set, length, numerical range, and acceptable values) verifies that inputs match specified definitions for format and content.

{{ ORGANIZATION }} ensures that all information input into {{ SYSTEM_NAME }} is valid and matches specified definitions for format and content.


### 9.1 Predictable Behavior

A common vulnerability in organizational systems is unpredictable behavior when invalid inputs are received. Verification of system predictability helps ensure that the system behaves as expected when invalid inputs are received.

{{ ORGANIZATION }} {{ SYSTEM_NAME }} behaves in a predictable and documented manner when invalid inputs are received.


### 9.2 Restrict Inputs to Trusted Sources and Approved Formats

Restricting the use of inputs to trusted sources and in trusted formats applies the concept of authorized or permitted software to information inputs. Specifying known trusted sources for information inputs and acceptable formats for such inputs can reduce the probability of malicious activity.

{{ ORGANIZATION }} only allows inputs from trusted sources and in predefined formats to reduce the probability of malicious activity.


### 9.3 Injection Prevention

{{ ORGANIZATION }} prevents untrusted data injections using parameterized queries, Semgrep static analysis in CI/CD pipelines, and Google Cloud Armor injection protection rules.


## 10. Error Handling

> [!IMPORTANT]
> [WARNING: RMF TEAM ACTION REQUIRED: Verify and update operational contact/procedure details in this section.]
> {{ ORGANIZATION }} {{ SYSTEM_NAME }} error handling procedures reveal error messages only to ISSO, ISSM, and SCA. {{ ORGANIZATION }} is responsible for ensuring applications built on Google Cloud generate error messages that provide information necessary for corrective actions.


## 11. Information Management and Retention

{{ ORGANIZATION }} handles and retains information within the system and information output from the system in accordance with applicable federal laws, Executive Orders, directives, policies, regulations, standards, and operational requirements. {{ ORGANIZATION }} {{ SYSTEM_NAME }} data retention and disposal adhere to agency records schedules and contract requirements. Upon contract expiration or decommissioning, Google Cloud returns {{ ORGANIZATION }} data and sanitizes the underlying storage media in accordance with NIST SP 800-88.


| Information Type | Handling Requirement | Retention Requirement |
| --- | --- | --- |
| Records | Need-to-know | System life |
| Classified | Cleared personnel | System life |
| Controlled Unclassified | Need-to-know | System life |
| Personally Identifiable Information | Need-to-know | System life |
| Audit Logs | Need-to-know. Only authorized personnel have access to logs. | 1 year |


### 11.1 Information Disposal

Organizations can minimize both security and privacy risks by disposing of information when it is no longer needed. The disposal or destruction of information applies to originals as well as copies and archived records, including system logs that may contain personally identifiable information.

{{ ORGANIZATION }} disposes of information after its retention period by cryptographic erase (destruction of the Cloud KMS key versions that protect the data); Google Cloud sanitizes or destroys the underlying physical media in accordance with NIST SP 800-88 Rev. 2.


### 11.2 Limit Personally Identifiable Information Elements

{{ ORGANIZATION }} limits the personally identifiable information (PII) processed by {{ SYSTEM_NAME }} to the elements listed in the system Privacy Impact Assessment (PIA) and Privacy Threshold Analysis (PTA). Sensitive Data Protection (Cloud DLP) discovery scans identify PII elements that are not on that list.


### 11.3 Personally Identifiable Information Quality Operations

{{ ORGANIZATION }} checks the accuracy, relevance, timeliness, and completeness of PII in {{ SYSTEM_NAME }} at least annually and before disclosure, and corrects or deletes inaccurate or outdated PII. In addition, {{ ORGANIZATION }}:

- Collects PII directly from the individual to whom it pertains;

- Corrects or deletes PII upon request by the individual or the individual's designated representative;

- Propagates corrections and deletions to connected repositories through automated SCIM directory synchronization; and

- Notifies recipients of the PII and the affected individual when PII has been corrected or deleted.


## 12. Information Output Filtering

Certain types of attacks, including SQL injections, produce output results that are unexpected or inconsistent with the output results that would be expected from software programs or applications. Information output filtering focuses on detecting extraneous content, preventing such extraneous content from being displayed, and then alerting monitoring tools that anomalous behavior has been discovered.

{{ ORGANIZATION }} {{ SYSTEM_NAME }} validates information output from software programs and applications to ensure that the information is consistent with the expected content.


## 13. Memory Protection

Some adversaries launch attacks with the intent of executing code in non-executable regions of memory or in memory locations that are prohibited. {{ SYSTEM_NAME }} protects memory from unauthorized code execution by implementing the applicable STIG/SRG requirements, including data execution prevention (DEP) and address space layout randomization (ASLR).


## 14. Information Refresh

Retaining information for longer than it is needed makes it an increasingly valuable and enticing target for adversaries. Keeping information available for the minimum period of time needed to support organizational missions or business functions reduces the opportunity for adversaries to compromise, capture, and exfiltrate that information.

{{ ORGANIZATION }} {{ SYSTEM_NAME }} ensures that information is generated on demand, and deleted when no longer necessary to reduce the opportunity for adversaries to compromise, capture, and exfiltrate the information.



## Appendix A – Detailed Compliance Matrix

The following table provides detailed traceability between the policy implementation statements in this document, the authoritative NIST SP 800-53 Rev. 5 control requirements, DoD CCIs, and the technical/governance enforcement mechanisms active across {{ SYSTEM_NAME }}.


| CTRL ID | CTRLTITLE | REQUIRED {{ GRC_STANDARD_LABEL }} STANDARD | DOCREF | ENFORCEMENT MECHANISM |
| :--- | :--- | :--- | :--- | :--- |
| SI-01 | Policy and Procedures | Develop, document, and disseminate the SI policy and procedures to the roles in the Program Roles & Responsibilities Matrix; designate the ISSM to manage them; review and update both at least annually and following significant changes, incidents, assessment findings, or changes in applicable requirements (CCI-001217, CCI-001218, CCI-001219, CCI-001220, CCI-001221, CCI-001222, CCI-001223, CCI-001224, CCI-002601, CCI-004944, CCI-004945, CCI-004946, CCI-004947, CCI-004948, CCI-004949, CCI-004950, CCI-004951, CCI-004952, CCI-004953, CCI-004954) | Section 1 | Formal organizational approval by {{ ORGANIZATION }} ISSM/SO/AO; published in central compliance portal; event-driven RMF update triggers. |
| SI-02 | Flaw Remediation | Identify, report, and correct system flaws across all components; install security-relevant updates within 30 days (CCI-001225, CCI-001226, CCI-001227, CCI-001228, CCI-001229, CCI-001230, CCI-002602, CCI-002603, CCI-002604, CCI-002605, CCI-002606, CCI-002607) | Section 2 | {{ CSSP_PROVIDER }} and {{ VULNERABILITY_SCANNER }} vulnerability reports, automated preproduction pipeline gating, and mandatory 30-day IAVM/patching cycles. |
| SI-02(02) | Automated Flaw Remediation Status | Employ automated mechanisms (ACAS, HBSS) to continuously monitor and verify update installation across components (CCI-004955, CCI-004956, CCI-004957, CCI-004958, CCI-004959, CCI-004960) | Section 2 | Automated compliance monitoring via Google Cloud VM Manager patch execution and agent-based policy auditing. |
| SI-02(03) | Time to Remediate Flaws and Benchmarks for Corrective Actions | Measure the time between flaw identification and flaw remediation against corrective action benchmarks: 15 days for IAVA/critical flaws and 30 days for IAVB/high flaws (CCI-001235, CCI-001236, CCI-002608) | Section 2 | Time from identification to remediation tracked per finding in the POA&M; IAVM/CTO directive benchmarks (Critical: 15 days, High: 30 days) enforced. |
| SI-02(04) | Automated Patch Management Tools | Employ Google Cloud VM Manager and Artifact Registry container scanning as automated patch management tools across all capable components (CCI-004961, CCI-004962) | Section 2 | Google Cloud VM Manager patch orchestrations, Artifact Registry automated scanning, and CI/CD pre-commit security gating. |
| SI-02(06) | Removal of Previous Versions of Software and Firmware | Automatically remove and purge upgraded or replaced software and firmware components no longer required for system operations (CCI-002615, CCI-002616, CCI-002617, CCI-002618) | Section 2 | Automated deployment clean-up tasks within {{ CICD_PLATFORM }} runner pipelines, removing legacy builds and unneeded packages. |
| SI-03 | Malicious Code Protection | Implement signature-based and heuristic/behavioral malicious code protection at all endpoints and gateways; update and scan daily (CCI-001241, CCI-001243, CCI-001244, CCI-001245, CCI-002623, CCI-002624, CCI-004963, CCI-004964, CCI-004965, CCI-004966) | Section 3 | Google Cloud Armor WAF (where authorized in the accreditation boundary) integration, host-level antivirus engines, and daily automated definition sync pipelines. |
| SI-03(10) | Malicious Code Analysis | Employ malware analysis tools and techniques directed by {{ CSSP_PROVIDER }} CSSP to analyze the characteristics and behavior of malicious code; incorporate the results into incident response and flaw remediation processes (CCI-002634, CCI-002635, CCI-002636, CCI-002638, CCI-002639, CCI-002640) | Section 3 | Ingestion of {{ CSSP_PROVIDER }} threat advisories; malware detonation sandboxes in isolated staging projects. |
| SI-04 | System Monitoring | Monitor {{ SYSTEM_NAME }} continuously to detect malicious and suspicious activity; generate and deliver security status reports at least monthly to ISSO/ISSM (CCI-001253, CCI-001255, CCI-001256, CCI-001257, CCI-001258, CCI-002641, CCI-002642, CCI-002643, CCI-002644, CCI-002645, CCI-002646, CCI-002650, CCI-002651, CCI-002652, CCI-002654, CCI-004967) | Section 4 | {{ EXTERNAL_SIEM }} real-time event analytics; Google Cloud Operations Suite; automated log routing via Pub/Sub sinks to BigQuery. |
| SI-04(01) | System-wide Intrusion Detection System | Connect and configure individual intrusion detection tools into a system-wide intrusion detection system (CCI-002655, CCI-002656) | Section 4 | {{ INTRUSION_DETECTION_SYSTEM }} alerts and {{ THREAT_DETECTION_ENGINE }} findings aggregated in {{ EXTERNAL_SIEM }} through Pub/Sub log sinks. |
| SI-04(02) | Automated Tools and Mechanisms for Real-time Analysis | Employ automated tools and mechanisms to support near real-time analysis of events (CCI-001260, CCI-004968) | Section 4 | {{ EXTERNAL_SIEM }} and BigQuery analysis of Cloud Logging, VPC Flow Logs, and container audit events; real-time alert rules in Cloud Monitoring. |
| SI-04(04) | Inbound and Outbound Communications Traffic | Define criteria for unusual or unauthorized inbound and outbound communications traffic; monitor inbound and outbound traffic continuously against those criteria (CCI-002659, CCI-002660, CCI-002661, CCI-002662, CCI-004971, CCI-004972, CCI-004973, CCI-004974) | Section 4 | Ingress and egress logging at {{ PERIMETER_GATEWAY }} and VPC firewall rules; VPC Flow Logs analyzed continuously in {{ EXTERNAL_SIEM }} against the defined criteria. |
| SI-04(05) | System-generated Alerts | Dispatch automated alerts to ISSO/ISSM and Incident Response Team immediately upon compromise indicator detection (CCI-001264, CCI-002663, CCI-002664) | Section 4 | Pub/Sub notification integrations routing high-priority alerts directly to PagerDuty and the NetOps incident queue. |
| SI-04(10) | Visibility of Encrypted Communications | Establish visibility into encrypted traffic sessions at approved decryption boundaries (VDSS/VPN) (CCI-002665, CCI-002666, CCI-002667, CCI-004977, CCI-004978, CCI-004979) | Section 4 | Approved SSL/TLS decryption boundaries at VDSS firewalls and HA Cloud VPN gateways. |
| SI-04(11) | Analyze Communications Traffic Anomalies | Analyze outbound communications traffic at external interfaces and at selected interior points to discover anomalies (CCI-001273, CCI-001671, CCI-002668) | Section 4 | BigQuery analytical views of outbound VPC Flow Logs from external interfaces and internal subnet boundaries; continuous {{ ORGANIZATION }} NetOps anomaly detection. |
| SI-04(12) | Automated Organization-generated Alerts | Alert personnel on the system alert notification list using automated mechanisms when defined inappropriate or unusual activities with security or privacy implications occur (CCI-001274, CCI-001275, CCI-004980) | Section 4 | Cloud Monitoring alerting policies for non-CONUS administrator access, repeated failed administrative authentication, and firewall rules that allow 0.0.0.0/0 ingress. |
| SI-04(14) | Wireless Intrusion Detection | Employ a wireless intrusion detection system to identify rogue wireless devices and detect attack attempts and potential compromises or breaches (CCI-001673) | Section 4 | Inherited Google data center infrastructure monitoring for rogue wireless devices; wireless access is prohibited within the {{ SYSTEM_NAME }} boundary. |
| SI-04(15) | Wireless to Wireline Communications | Employ an intrusion detection system to monitor wireless communications traffic as it passes from wireless to wireline networks (CCI-001282) | Section 4 | Inherited Google data center infrastructure security controls; wireless access is prohibited within the {{ SYSTEM_NAME }} boundary. |
| SI-04(16) | Correlate Monitoring Information | Correlate information from monitoring tools and mechanisms employed throughout {{ SYSTEM_NAME }} (CCI-001283, CCI-004981) | Section 4 | {{ EXTERNAL_SIEM }} correlation of Cloud Audit Logs, VPC Flow Logs, {{ INTRUSION_DETECTION_SYSTEM }} alerts, and {{ THREAT_DETECTION_ENGINE }} findings. |
| SI-04(18) | Analyze Traffic and Covert Exfiltration | Analyze outbound communications traffic at the external boundary of the system and selected interior points to detect covert exfiltration of information. (CCI-002670, CCI-002671, CCI-002672) | Section 4 | VPC Flow Logs, Cloud DNS query logging, Cloud NAT/proxy egress logs, and {{ INTRUSION_DETECTION_SYSTEM }} / {{ EXTERNAL_SIEM }} anomaly analytics. |
| SI-04(19) | Risk for Individuals | Implement additional monitoring (keystroke logging, real-time command auditing, and session capture) of individuals identified by personnel records, intelligence agencies, or law enforcement organizations as posing an increased level of risk (CCI-002673, CCI-002674, CCI-002675) | Section 4 | Keystroke logging, real-time command auditing, and session capture on administrative bastion hosts for individuals identified as high risk. |
| SI-04(20) | Privileged Users | Implement additional monitoring of privileged users: Admin Activity and Data Access audit logging of all privileged actions, reviewed in {{ EXTERNAL_SIEM }} (CCI-002676, CCI-002677) | Section 4 | Cloud Audit Logs (Admin Activity and Data Access); write-once aggregated log sinks locked with bucket retention policies. |
| SI-04(22) | Unauthorized Network Services | Detect network services not authorized or approved through the {{ ORGANIZATION }} configuration management process; audit the event and alert the ISSO when detected (CCI-002681, CCI-002682, CCI-002683, CCI-002684) | Section 4 | {{ THREAT_DETECTION_ENGINE }} findings and NetOps open-port discovery scans compared against approved services; alerts routed to the ISSO. |
| SI-04(23) | Host-based Devices | Implement host-based monitoring mechanisms ({{ EDR_SOLUTION }} and Google Cloud Ops Agent) on {{ SYSTEM_NAME }} components (CCI-002685, CCI-002686, CCI-002687) | Section 4 | {{ EDR_SOLUTION }} and Ops Agent telemetry from VM instances and container hosts sent to Cloud Monitoring and {{ EXTERNAL_SIEM }}. |
| SI-04(24) | Indicators of Compromise | Discover, collect, and distribute indicators of compromise provided by<!-- IF DOD_ENCLAVE --> USCYBERCOM and<!-- ENDIF --> {{ CSSP_PROVIDER }} and CISA to the ISSO, ISSM, and incident response personnel (CCI-002688, CCI-002689, CCI-002690) | Section 4 | Automated ingestion of <!-- IF DOD_ENCLAVE -->USCYBERCOM and <!-- ENDIF -->{{ CSSP_PROVIDER }} threat intelligence feeds into {{ EXTERNAL_SIEM }}; SIEM incident dispatch; standardized threat format sharing (STIX/TAXII) <!-- IF DOD_ENCLAVE -->with USCYBERCOM/DISA<!-- ENDIF --><!-- IF NOT DOD_ENCLAVE -->with CISA<!-- ENDIF -->. |
| SI-04(25) | Optimize Network Traffic Analysis | Enforce optimize network traffic analysis requirements across {{ SYSTEM_NAME }} in accordance with NIST SP 800-53 Rev. 5 SI-4(25). (CCI-004982) | Section 3 | Enforced via Google Cloud infrastructure controls, Terraform configuration baselines, and ISSM/ISSO governance verification. |
| SI-05 | Security Alerts, Advisories, and Directives | Receive system security alerts, advisories, and directives from<!-- IF DOD_ENCLAVE --> CSSP, USCYBERCOM, and DISA<!-- ENDIF --><!-- IF NOT DOD_ENCLAVE --> CISA and NIST<!-- ENDIF -->; disseminate to ISSO/ISSM (CCI-001285, CCI-001286, CCI-001287, CCI-001288, CCI-001289, CCI-002692, CCI-002693, CCI-002694) | Section 5 | Ongoing monitoring of IAVM/CIRT channels; rapid dissemination to {{ ORGANIZATION }} ISSO/ISSM; formal POA&M scheduling. |
| SI-05(01) | Automated Alerts and Advisories | Broadcast security alert and advisory information throughout the organization using automated mechanisms. (CCI-001290, CCI-004983) | Section 5 | Automated CISA / vendor advisory ingestion, Cloud Monitoring / {{ EXTERNAL_SIEM }} alert broadcasts, and automated ticket creation in {{ ITSM_SYSTEM }}. |
| SI-06 | Security and Privacy Function Verification | Verify correct operation of security and privacy functions (VPC-SC, KMS) at startup, upon command, and {{ ODP_SI_6_VERIFY_FREQ }} (CCI-001294, CCI-002695, CCI-002696, CCI-002697, CCI-002698, CCI-002699, CCI-002700, CCI-002701, CCI-002702, CCI-004984, CCI-004985, CCI-004986, CCI-004987, CCI-004988, CCI-004989, CCI-004990, CCI-004991, CCI-004992) | Section 6 | Automated startup sanity scripts; scheduled quarterly RMF verification tests managed by ISSM/ISSO. |
| SI-06(03) | Report Verification Results | Enforce report verification results requirements across {{ SYSTEM_NAME }} in accordance with NIST SP 800-53 Rev. 5 SI-6(3). (CCI-001296, CCI-001675, CCI-004994, CCI-004995) | Section 3 | Enforced via Google Cloud infrastructure controls, Terraform configuration baselines, and ISSM/ISSO governance verification. |
| SI-07 | Software, Firmware, and Information Integrity | Employ automated integrity verification tools to detect unauthorized changes to all software, firmware, and information (CCI-002703, CCI-002704, CCI-004996, CCI-004997) | Section 7 | UEFI Secure Boot, Shielded VM integrity verifications, and automated container image signature checking. |
| SI-07(01) | Integrity Checks | Perform integrity checks on OS files, libraries, and executables at boot, post-update, post-admin logoff, and monthly (CCI-002705, CCI-002706, CCI-002707, CCI-002708, CCI-002709, CCI-002710, CCI-002711, CCI-002712) | Section 7 | Cryptographic boot measurements (vTPM), automated post-patch file integrity scans, and monthly SCAP audits. |
| SI-07(02) | Automated Notifications of Integrity Violations | Employ automated tools that provide notification to designated individuals upon discovering discrepancies during integrity verification. (CCI-001300, CCI-002713) | Section 7 | Shielded VM integrity monitoring alerts, container image digest verification in CI/CD, and Cloud Monitoring real-time integrity alerts to the ISSO/SOC. |
| SI-07(05) | Automated Response to Integrity Violations | Automatically halt system or component execution, isolate the affected workload, or roll back to a known-good state when integrity violations are discovered. (CCI-002714, CCI-002715) | Section 7 | Shielded VM Secure Boot halt-on-failure, GKE admission control digest enforcement, and automated instance replacement from verified images. |
| SI-07(07) | Integration of Detection and Response | Incorporate automated detection of security-relevant system changes into the organizational incident response process (CCI-002719, CCI-002720) | Section 7 | Incident response playbooks triggered immediately upon detection of unauthorized system configuration changes. |
| SI-07(08) | Auditing Capability for Significant Events | Generate audit logs, alert user and ISSO, and isolate/quarantine affected components upon detecting integrity violations (CCI-002721, CCI-002722, CCI-002723, CCI-002724) | Section 7 | Automated instance shutdown/quarantine triggered by integrity failures; immediate audit record generation and alerts. |
| SI-07(09) | Verify Boot Process | Verify boot process integrity across all virtual instances using UEFI Secure Boot and vTPM (CCI-002725, CCI-002726) | Section 7 | Google Shielded VM vTPM measurements and secure boot UEFI configurations validating hypervisor and OS boot code. |
| SI-07(10) | Protection of Boot Firmware | Protect boot firmware integrity using cryptographic signatures backed by a hardware root of trust (TPM 2.0) (CCI-002727, CCI-002728, CCI-002729) | Section 7 | Hardware-anchored boot firmware protection (Titan security chip / TPM 2.0) preventing firmware modifications. |
| SI-07(12) | Integrity Verification | Verify integrity of all software, container images, and updates using digital signatures prior to execution (CCI-002732, CCI-002733) | Section 7 | container image signature verification (e.g., Binary Authorization where authorized in the accreditation boundary, or CI/CD cosign attestation) enforcing cryptographic container signatures (cosign) across all deployed workloads. |
| SI-07(15) | Code Authentication | Implement cryptographic mechanisms to authenticate software and firmware components prior to installation and execution. (CCI-002739, CCI-002740) | Section 7 | Cryptographic signature verification of OS packages (GPG/RPM/APT), container image cosign/attestation checks, and Shielded VM UEFI Secure Boot. |
| SI-07(17) | Runtime Application Self-protection | Enforce runtime application self-protection requirements across {{ SYSTEM_NAME }} in accordance with NIST SP 800-53 Rev. 5 SI-7(17). (CCI-004998, CCI-004999) | Section 3 | Enforced via Google Cloud infrastructure controls, Terraform configuration baselines, and ISSM/ISSO governance verification. |
| SI-08 | Spam Protection | Deploy enterprise spam and phishing protections at all external messaging gateways; update signatures at least weekly (CCI-002741, CCI-002742, CCI-005000, CCI-005001) | Section 8 | DoD Enterprise Email spam protection; Google Workspace spam filters; automated threat classification. |
| SI-08(02) | Automatic Updates | Configure spam protection mechanisms to automatically update signature definitions at least weekly (CCI-001308, CCI-005002) | Section 8 | Automated weekly signature updates and cloud threat intelligence synchronization at the email gateway. |
| SI-10 | Information Input Validation | Check the validity of all information inputs (character set, string length, CIDR notation) across APIs and interfaces (CCI-001310, CCI-002744) | Section 9 | JSON schema validations; regex pattern checking; API gateway input filtering restricting character sets and sizes. |
| SI-10(03) | Predictable Behavior | Ensure {{ SYSTEM_NAME }} behaves in a predictable, documented manner when invalid inputs are received without leaking stack traces (CCI-002754) | Section 9 | Standardized error return configurations; stack trace suppression on all production-facing interfaces. |
| SI-10(05) | Restrict Inputs to Trusted Sources and Approved Formats | Enforce restrict inputs to trusted sources and approved formats requirements across {{ SYSTEM_NAME }} in accordance with NIST SP 800-53 Rev. 5 SI-10(5). (CCI-002756, CCI-002757, CCI-002758) | Section 3 | Enforced via Google Cloud infrastructure controls, Terraform configuration baselines, and ISSM/ISSO governance verification. |
| SI-10(06) | Injection Prevention | Prevent injection attacks (SQL, command, XSS) using parameterized queries, static analysis, and Cloud Armor WAF (CCI-005003) | Section 9 | Parameterized BigQuery/SQL queries; Semgrep SAST scanning; Google Cloud Armor injection protection rules. |
| SI-11 | Error Handling | Generate secure error messages providing only necessary info; restrict detailed debug messages to ISSM/ISSO/admins (CCI-001312, CCI-001314, CCI-002759) | Section 10 | Detailed error logging restricted to private sinks; generic user-facing error messages omitting system details. |
| SI-12 | Information Management and Retention | Manage and retain system information and audit logs online for 1 year and archive for 5 years in secure storage (CCI-001315, CCI-001678) | Section 11 | BigQuery table partitioning; long-term Cloud Storage Coldline buckets locked via Object Retention policies. |
| SI-12(01) | Limit Personally Identifiable Information Elements | Limit Personally Identifiable Information (PII) processed in {{ SYSTEM_NAME }} strictly to elements listed in the system PIA/PTA (CCI-005004, CCI-005005) | Section 11 | Sensitive Data Protection (Cloud DLP) discovery templates; strict administrative authentication data limitations. |
| SI-12(03) | Information Disposal | Sanitize and dispose of digital information following retention expiration using cryptographic erasure (crypto-shredding) (CCI-005008) | Section 11 | Cloud KMS key version destruction (crypto-shredding) and secure multitenant physical drive destruction at retired nodes. |
| SI-15 | Information Output Filtering | Validate software output to ensure consistency with expected content and sanitize unexpected or extraneous data (CCI-002770, CCI-002771) | Section 12 | Data egress schema checking; automated data sanitization scripts; BigQuery view output validations. |
| SI-16 | Memory Protection | Enforce hardware and OS memory protections (DEP, ASLR, CFI) to protect system memory from unauthorized code execution (CCI-002823, CCI-002824) | Section 13 | Guest operating system memory protections (DEP/ASLR/CFI) enforced on all container hosts through STIG hardening. |
| SI-18 | Personally Identifiable Information Quality Operations | Check the accuracy, relevance, timeliness, and completeness of administrative PII at least annually and before disclosure; correct or delete inaccurate or outdated PII (CCI-005018, CCI-005019, CCI-005020) | Section 11 | Annual administrative identity attribute reviews; manual correction workflows managed by the Privacy Officer. |
| SI-18(01) | Automation Support | Employ automated SCIM directory synchronization to correct or delete inaccurate or outdated PII across repositories (CCI-005021, CCI-005022) | Section 11 | SCIM dynamic synchronization; automated directory deletions propagating immediately to Google Cloud Workforce Identity Federation pools. |
| SI-18(03) | Collection | Collect PII directly from the individual to whom it pertains (CCI-005024) | Section 11 | Identity attributes collected from the individual during in-person identity proofing and credential issuance at DoD DEERS card issuance facilities. |
| SI-18(04) | Individual Requests | Correct or delete PII upon request by the individual or the individual's designated representative (CCI-005025) | Section 11 | Privacy Officer correction and deletion workflow for individual requests; changes propagated to connected repositories through SCIM directory synchronization. |
| SI-18(05) | Notice of Correction or Deletion | Notify recipients of the PII and the affected individual when PII has been corrected or deleted (CCI-005026, CCI-005027, CCI-005028) | Section 11 | SCIM directory correction feeds notify downstream connected applications; the Privacy Officer notifies the individual when the correction or deletion is complete. |
| SI-21 | Information Refresh | Enforce information refresh requirements across {{ SYSTEM_NAME }} in accordance with NIST SP 800-53 Rev. 5 SI-21. (CCI-005043, CCI-005044, CCI-005045) | Section 3 | Enforced via Google Cloud infrastructure controls, Terraform configuration baselines, and ISSM/ISSO governance verification. |
