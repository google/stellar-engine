# MA - Maintenance Policy and Procedures

## Document Governance & Approval Baseline

| Governance Metric | Policy Standard & Specification |
| :--- | :--- |
| **Document Title** | Maintenance Policy and Procedures |
| **NIST Control Family** | Maintenance (MA) |
| **Primary NIST Benchmark** | NIST SP 800-53 Rev. 5 (MA Family), Google Services Customer Responsibility Matrix |
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
> This document defines the enterprise security policy and implementation procedures for **Maintenance** under **NIST SP 800-53 Rev. 5 (MA)**.
> Technical infrastructure controls are automatically provisioned and enforced via **{{ SYSTEM_NAME }}** Terraform blueprints.
> Operational rules or contact details requiring manual confirmation are highlighted with RMF Team Callouts.


## 1. Overview

Federal agencies and organizations cannot protect the confidentiality, integrity, and availability of information in today's highly networked systems environment without ensuring that all people involved in using and managing IT:

1. Understand their roles and responsibilities related to the organizational mission;
2. Understand the organization's IT security policy, procedures, and practices; and
3. Have at least adequate knowledge of the various management, operational, and technical controls required and available to protect the IT resources for which they are responsible.

The purpose of this Maintenance Policy is to establish the requirements for performing, controlling, and monitoring local and nonlocal maintenance of {{ SYSTEM_NAME }} components, including maintenance tools and maintenance personnel.

This policy addresses the Maintenance (MA) family requirements of NIST Special Publication 800-53 Revision 5, "Security and Privacy Controls for Information Systems and Organizations." A detailed compliance matrix is provided in Appendix A, "Detailed Compliance Matrix."

The Maintenance Policy encompasses all {{ ORGANIZATION }} users who have access to {{ SYSTEM_NAME }}. This policy outlines the framework for establishing, implementing, and maintaining system maintenance in alignment with applicable {{ GOVERNANCE_REGIME }} guidelines (NIST SP 800-53, FedRAMP, and applicable federal and state regulations), and is consistent with applicable laws, executive orders, directives, regulations, policies, standards, and guidelines. It applies to employees, contractors, and third-party users who handle sensitive information or operate within the {{ ORGANIZATION }} {{ SYSTEM_NAME }} information technology infrastructure.

{{ ORGANIZATION }} management is committed to the requirements of this policy and provides the resources needed to implement them. The ISSM ({{ ISSM_NAME }}) manages the development, documentation, and dissemination of this policy and its procedures, and coordinates their implementation with the Authorizing Official, System Owner, ISSO, and other organizational entities identified in the Program Roles & Responsibilities Matrix.

This policy and its procedures are reviewed and updated at least annually and following significant changes to {{ SYSTEM_NAME }} or its operating environment, security or privacy incidents, assessment or audit findings, or changes in applicable laws, executive orders, directives, regulations, policies, standards, or guidelines.


## 2. Controlled Maintenance

Google Cloud performs controlled maintenance, repair, and replacement of the physical infrastructure in its data centers, and {{ ORGANIZATION }} {{ SYSTEM_NAME }} inherits this control. {{ ORGANIZATION }} schedules maintenance of the components it manages, approves it through the Change Control Board (CCB), records it, and verifies after each maintenance action that the affected controls still function.

### 2.1 Google Cloud Platform (GCP) Inherited Controls & Shared Responsibility Boundary

- **Google Inherited Controls**: Google Cloud conducts physical server maintenance (`MA-2`), hardware replacement, and maintenance tool security (`MA-3`, `MA-5`) inside all Google data centers.
- **Customer Implementation Responsibilities**: {{ ORGANIZATION }} is responsible for scheduling maintenance windows for customer-managed GKE node pools, Cloud SQL instances, and application workloads (`MA-2`, `MA-4`).

## 3. Maintenance Tools

Google Cloud provides and secures the maintenance tools used in its data centers, and {{ ORGANIZATION }} {{ SYSTEM_NAME }} inherits this control. Tools that {{ ORGANIZATION }} administrators use to maintain {{ SYSTEM_NAME }}, such as CI/CD pipelines, Terraform, and container images, are:

- Approved by the CCB and reviewed at least annually;
- Restricted to authorized personnel, with use of tools that run with elevated privilege monitored through Cloud Audit Logs;
- Inspected for unauthorized modifications, and scanned for malicious code before use; and
- Kept current with the latest software updates and patches.

## 4. Nonlocal Maintenance

Nonlocal maintenance and diagnostic activities are those conducted by individuals communicating through a network, either an external network (e.g., the Internet) or an internal network. {{ ORGANIZATION }} does not authorize outside vendors to perform maintenance on {{ SYSTEM_NAME }}. Only authorized {{ ORGANIZATION }} administrators perform configuration changes and software updates, and their maintenance sessions:

- Are approved in advance and monitored in real time;
- Originate from compliant {{ ORGANIZATION }}-managed endpoints through an authorized virtual desktop or administrative bastion host;
- Use replay-resistant multi-factor authentication ({{ IDENTITY_PROVIDER }} with {{ MFA_MECHANISM }});
- Are encrypted and logically separated from other network sessions;
- Are logged to Cloud Logging and reviewed in {{ EXTERNAL_SIEM }} for anomalous behavior; and
- Are terminated after 15 minutes of inactivity or when maintenance is complete, and the termination is verified.

## 5. Maintenance Personnel

Google Cloud provides and supervises the maintenance personnel for its data centers, and {{ ORGANIZATION }} {{ SYSTEM_NAME }} inherits this control. {{ ORGANIZATION }} maintains the list of administrators authorized to maintain the components it manages in {{ IDENTITY_PROVIDER }} and Cloud IAM.

## 6. Timely Maintenance

Google Cloud provides maintenance support and spare parts for the infrastructure in its data centers, and {{ ORGANIZATION }} {{ SYSTEM_NAME }} inherits this control.


## Appendix A – Detailed Compliance Matrix

The following table provides detailed traceability between the policy implementation statements in this document, the authoritative NIST SP 800-53 Rev. 5 control requirements, DoD CCIs, and the technical/governance enforcement mechanisms active across {{ SYSTEM_NAME }}.


| CTRL ID | CTRLTITLE | REQUIRED {{ GRC_STANDARD_LABEL }} STANDARD | DOCREF | ENFORCEMENT MECHANISM |
| :--- | :--- | :--- | :--- | :--- |
| MA-01 | Policy and Procedures | Develop, document, and disseminate the system maintenance policy and procedures; designate the ISSM to manage them; review and update them at least annually and following significant system changes, security or privacy incidents, assessment or audit findings, or changes in applicable laws, regulations, or guidance (CCI-000851, CCI-000852, CCI-000853, CCI-000854, CCI-000855, CCI-000856, CCI-000857, CCI-001628, CCI-002861, CCI-002862, CCI-004165, CCI-004166, CCI-004167, CCI-004168, CCI-004169, CCI-004170, CCI-004171, CCI-004172, CCI-004173) | Section 1 | Formal {{ ORGANIZATION }} policy approval, System Owner and ISSM governance, eMASS compliance repository, and annual CCB review tracking. |
| MA-02 | Controlled Maintenance | Schedule, authorize, monitor, log, and verify maintenance activities; sanitize equipment prior to removal (CCI-000860, CCI-000861, CCI-000862, CCI-002866, CCI-002868, CCI-002869, CCI-002870, CCI-002872, CCI-002873, CCI-002874, CCI-002875, CCI-002876, CCI-004174, CCI-004175, CCI-004176, CCI-004177, CCI-004178, CCI-004179, CCI-004180, CCI-004181) | Section 2 | {{ ORGANIZATION }} Change Control Board (CCB) change approvals, inherited Google Cloud data center maintenance, NIST SP 800-88 sanitization, and post-change automated reachability testing. |
| MA-02(02) | Automated Maintenance Activities | Employ automated mechanisms to schedule, conduct, and document maintenance and diagnostic activities, producing up-to-date, accurate, and complete records. (CCI-002864, CCI-002865, CCI-004182, CCI-004183, CCI-004184, CCI-004185) | Section 2 | Automated OS Patch Management (VM Manager), GKE maintenance windows, Terraform CI/CD change logs, and Cloud Audit Logs routed to {{ ITSM_SYSTEM }}. |
| MA-03 | Maintenance Tools | Approve, control, monitor, and conduct annual reviews of system maintenance tools (CCI-000865, CCI-000866, CCI-000867, CCI-004186, CCI-004187) | Section 3 | {{ ORGANIZATION }} CCB tool approval list, inherited Google Cloud maintenance tool controls, CI/CD pipeline gating, and annual ISSM tooling audits. |
| MA-03(01) | Inspect Tools | Inspect maintenance tools for improper or unauthorized modifications (CCI-000869) | Section 3 | Automated CI/CD cryptographic SHA-256 checksum verification, tfsec/Checkov static analysis, and out-of-band management VPN filtering. |
| MA-03(02) | Inspect Media | Check media containing diagnostic and test programs for malicious code prior to use (CCI-000870) | Section 3 | Inherited Google Cloud anti-malware controls, Trivy container image scans and Hadolint Dockerfile linting for Artifact Registry images, and ClamAV scanning of uploaded scripts. |
| MA-03(03) | Prevent Unauthorized Removal | Prevent unauthorized removal of maintenance equipment containing organizational information (CCI-000871, CCI-002882) | Section 3 | VPC Service Controls perimeters blocking unauthorized data exfiltration and inherited Google physical data center security perimeters. |
| MA-03(04) | Restricted Tool Use | Restrict the use of maintenance tools to authorized personnel only (CCI-002883) | Section 3 | {{ IDENTITY_PROVIDER }} with {{ MFA_MECHANISM }}, IAM custom roles (e.g., {{ SYSTEM_NAME }}-NetworkAdmins), and Resource Manager tag conditions. |
| MA-03(05) | Execution with Privilege | Monitor the use of maintenance tools that execute with increased privilege (CCI-004188) | Section 3 | Cloud Audit Logs (cloudaudit.googleapis.com/activity), Privileged Access Manager (PAM) just-in-time grants with audit logging, and BigQuery SIEM alerting on elevated service account execution. |
| MA-03(06) | Software Updates and Patches | Inspect maintenance tools to ensure the latest software updates and patches are installed (CCI-004189) | Section 3 | Automated CI/CD pipeline dependency updates, monthly container image rebuilds in Artifact Registry, and ACAS vulnerability scans. |
| MA-04 | Nonlocal Maintenance | Authorize, monitor, log, and terminate nonlocal maintenance sessions using strong authenticators (CCI-000873, CCI-000874, CCI-000876, CCI-000877, CCI-000878, CCI-004190, CCI-004191) | Section 4 | Strict prohibition of external vendor access, authorized virtual desktop and secure administrative bastion connectivity, 15-minute idle session timeouts, and real-time operations monitoring. |
| MA-04(01) | Logging and Review | Log audit events for nonlocal maintenance and review records for anomalous behavior (CCI-002884, CCI-002885, CCI-002886) | Section 4 | Cloud Logging sinks streaming maintenance API logs to {{ EXTERNAL_SIEM }} for automated behavioral analysis. |
| MA-04(03) | Comparable Security and Sanitization | Perform nonlocal maintenance from systems with comparable security; sanitize serviced components (CCI-000882, CCI-000883, CCI-001631) | Section 4 | Mandatory enterprise endpoint compliance, authorized secure bastion hosts, and NIST SP 800-88 media sanitization. |
| MA-04(04) | Authentication and Separation of Maintenance Sessions | Protect nonlocal maintenance with replay-resistant MFA and separate maintenance sessions from other traffic (CCI-000884, CCI-001632, CCI-002887, CCI-004192) | Section 4 | {{ IDENTITY_PROVIDER }} with {{ MFA_MECHANISM }}, dedicated management subnets, VPC-SC boundaries, and secure encrypted tunnel isolation. |
| MA-04(06) | Cryptographic Protection | Protect integrity and confidentiality of nonlocal maintenance communications using approved cryptography (CCI-002890, CCI-003123, CCI-004193) | Section 4 | Protocols TLS 1.2 minimum (TLS 1.3 where supported), Layer 2 MACsec (GCM-AES-XPN-256), and Layer 3 IPsec ESP (AES-256-GCM) using FIPS-validated cryptographic modules. |
| MA-04(07) | Disconnect Verification | Verify session and network connection termination after completion of nonlocal maintenance (CCI-002891) | Section 4 | Automated Cloud IAM session expirations, Privileged Access Manager (PAM) grant expiration, and HA VPN gateway idle-connection termination triggers. |
| MA-05 | Maintenance Personnel | Authorize, maintain roster, verify access authorizations, and supervise un-cleared maintenance personnel (CCI-000890, CCI-000891, CCI-002894, CCI-002895) | Section 5 | {{ IDENTITY_PROVIDER }} / Cloud IAM access rosters, inherited Google Cloud maintenance personnel controls, mandatory security background vetting, and physical/logical escort requirements. |
| MA-05(01) | Individuals Without Appropriate Access | Implement procedures for the use of maintenance personnel that lack appropriate security clearances or are not U.S. citizens, including escort and supervision by cleared personnel. (CCI-000893, CCI-000894, CCI-000895, CCI-004194, CCI-004195, CCI-004196) | Section 5 | Inherited from Google Cloud FedRAMP High / Assured Workloads US-person support controls; strict prohibition of unescorted uncleared maintenance access. |
| MA-05(02) | Security Clearances for Classified Systems | Verify that personnel performing maintenance and diagnostic activities on classified systems possess security clearances and formal access approvals for at least the highest classification level and compartments on the system. (CCI-000897) | Section 5 | [CONFIG_REQUIRED: Classified enclave security clearance verification via DISS/JPAS for all maintenance and diagnostic personnel per DISA CSP SRG V1R7 Table D-1 (IL6).] |
| MA-05(03) | Citizenship Requirements for Classified Systems | Verify that personnel performing maintenance and diagnostic activities on classified systems are U.S. citizens. (CCI-000898) | Section 5 | [CONFIG_REQUIRED: Mandatory U.S. citizenship verification for all classified enclave maintenance and diagnostic personnel per DISA CSP SRG V1R7 Table D-1 (IL6).] |
| MA-05(04) | Foreign Nationals | Ensure that cleared foreign nationals conduct maintenance on classified systems only on jointly owned/operated allied systems with approvals documented in Memoranda of Agreements. (CCI-000899, CCI-000900) | Section 5 | [CONFIG_REQUIRED: Prohibition of foreign national maintenance on classified systems absent an AO-approved joint allied Memorandum of Agreement per DISA CSP SRG V1R7 Table D-1 (IL6).] |
| MA-05(05) | Non-system Maintenance | Enforce non-system maintenance requirements across {{ SYSTEM_NAME }} in accordance with NIST SP 800-53 Rev. 5 MA-5(5). (CCI-002893) | Section 3 | Enforced via Google Cloud infrastructure controls, Terraform configuration baselines, and ISSM/ISSO governance verification. |
| MA-06 | Timely Maintenance | Obtain maintenance support and spare parts within defined timeframes: 24 hours for High, 3 days for Moderate, and 7 days for Low impact systems (CCI-000903, CCI-002896, CCI-002897) | Section 6 | Google Cloud Enterprise Support SLAs (15-minute P1 response), redundant multi-zone Cloud Interconnect and HA VPN, and automated IaC re-provisioning. |
| MA-06(01) | Preventive Maintenance | Perform preventive maintenance on defined components at scheduled intervals (CCI-002898, CCI-002899, CCI-002900) | Section 6 | Scheduled monthly container image refreshes, 90-day Cloud KMS CMEK key rotations, and semi-annual BGP/MACsec maintenance cadences. |
