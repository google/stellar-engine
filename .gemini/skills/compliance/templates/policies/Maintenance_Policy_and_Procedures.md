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


## 1. Controlled Maintenance

Controlled maintenance is performed by Google Cloud and is therefore inherited by {{ ORGANIZATION }} {{ SYSTEM_NAME }}. This document complies with requirements from NIST Special Publication 800-53 Revision 5, "Security and Privacy Controls for Federal Information Systems and Organizations". A detailed compliance matrix can be found in Appendix A, “Detailed Compliance Matrix”.



### 1.1 Google Cloud Platform (GCP) Inherited Controls & Shared Responsibility Boundary

- **Google Inherited Controls**: Google Cloud conducts physical server maintenance (`MA-2`), hardware replacement, and maintenance tool security (`MA-3`, `MA-5`) inside all Google datacenters.
- **Customer Implementation Responsibilities**: {{ ORGANIZATION }} is responsible for scheduling maintenance windows for customer-managed GKE node pools, Cloud SQL instances, and application workloads (`MA-2`, `MA-4`).

## 2. Maintenance Tools

Maintenance tools are provided by Google Cloud and are therefore inherited by {{ ORGANIZATION }} {{ SYSTEM_NAME }}.


## 3. Non-local Maintenance

Non-local maintenance and diagnostic activities are those activities conducted by individuals communicating through a network; either an external network (e.g., the Internet) or an internal network. {{ ORGANIZATION }} {{ SYSTEM_NAME }} does not authorize the use of non-local maintenance or diagnostic connections. {{ ORGANIZATION }} {{ SYSTEM_NAME }} will have admins performing configuration and software updates to the environment. There will not be any outside vendors performing maintenance activities to the environment.


## 4. Maintenance Personnel

Maintenance personnel are provided by Google through Google Cloud and this is therefore inherited by {{ ORGANIZATION }} {{ SYSTEM_NAME }}.


## 5. Timely Maintenance

Maintenance is provided by Google through Google Cloud and this is therefore inherited by {{ ORGANIZATION }} {{ SYSTEM_NAME }}.



## Appendix A – Detailed Compliance Matrix

The following table provides detailed traceability between the policy implementation statements in this document, the authoritative NIST SP 800-53 Rev. 5 control requirements, DoD CCIs, and the technical/governance enforcement mechanisms active across {{ SYSTEM_NAME }}.


| CTRL ID | CTRLTITLE | REQUIRED eMASS STANDARD | DOCREF | ENFORCEMENT MECHANISM |
| :--- | :--- | :--- | :--- | :--- |
| MA-01 | Policy and Procedures | Develop, document, disseminate, review, and update system maintenance policy and operational procedures (CCIs: 000851, 000852, 000853, 000854, 000855, 000856, 000857, 001628, 002861, 002862, 004165, 004166, 004167, 004168, 004169, 004170, 004171, 004172, 004173) | Section 1 | Formal {{ ORGANIZATION }} policy approval, ISO/PM and ISSM governance, eMASS compliance repository, and annual CCB review tracking. |
| MA-02 | Controlled Maintenance | Schedule, authorize, monitor, log, and verify maintenance activities; sanitize equipment prior to removal (CCIs: 000860, 000861, 000862, 002866, 002868, 002869, 002870, 002872, 002873, 002874, 002875, 002876, 004174, 004175, 004176, 004177, 004178, 004179, 004180, 004181) | Section 1 | {{ ORGANIZATION }} Change Control Board (CCB) change approvals, inherited Google Cloud datacenter maintenance, NIST SP 800-88 sanitization, and post-change automated reachability testing. |
| MA-03 | Maintenance Tools | Approve, control, monitor, and conduct annual reviews of system maintenance tools (CCIs: 000865, 000866, 000867, 004186, 004187) | Section 2 | {{ ORGANIZATION }} CCB tool approval list, Google Tool Shed governance, CI/CD pipeline gating, and annual ISSM tooling audits. |
| MA-03(01) | Inspect Tools | Inspect maintenance tools for improper or unauthorized modifications (CCI: 000869) | Section 2 | Automated CI/CD cryptographic SHA-256 checksum verification, tfsec/Checkov static analysis, and out-of-band management VPN filtering. |
| MA-03(02) | Inspect Media | Check media containing diagnostic and test programs for malicious code prior to use (CCI: 000870) | Section 2 | Google Services anti-malware pipeline, container vulnerability scans (Trivy/Hadolint) in Artifact Registry, and ClamAV scanning of uploaded scripts. |
| MA-03(03) | Prevent Unauthorized Removal | Prevent unauthorized removal of maintenance equipment containing organizational information (CCIs: 000871, 002882) | Section 2 | VPC Service Control perimeters blocking unauthorized data exfiltration and inherited Google physical datacenter security perimeters. |
| MA-03(04) | Restricted Tool Use | Restrict the use of maintenance tools to authorized personnel only (CCI: 002883) | Section 2 | {{ IDENTITY_PROVIDER }} with {{ MFA_MECHANISM }}, IAM custom roles (e.g. {{ SYSTEM_NAME }}-NetworkAdmins), and Resource Manager tag conditions. |
| MA-03(05) | Execution with Privilege | Monitor the use of maintenance tools that execute with increased privilege (CCI: 004188) | Section 2 | GCP Cloud Audit Logs (cloudaudit.googleapis.com/activity), GCP PAM session recording, and BigQuery SIEM alerting on elevated Service Account execution. |
| MA-03(06) | Software Updates and Patches | Inspect maintenance tools to ensure the latest software updates and patches are installed (CCI: 004189) | Section 2 | Automated CI/CD pipeline dependency updates, monthly container image rebuilds in Artifact Registry, and ACAS vulnerability scans. |
| MA-04 | Non-Local Maintenance | Authorize, monitor, log, and terminate nonlocal maintenance sessions using strong authenticators (CCIs: 000873, 000874, 000876, 000877, 000878, 004190, 004191) | Section 3 | Strict prohibition of external vendor access, authorized virtual desktop and secure administrative bastion connectivity, 15-minute idle session timeouts, and real-time operations monitoring. |
| MA-04(01) | Logging and Review | Log audit events for nonlocal maintenance and review records for anomalous behavior (CCIs: 002884, 002885, 002886) | Section 3 | Cloud Logging sinks streaming maintenance API logs to {{ SIEM_TOOL }} for automated behavioral analysis. |
| MA-04(03) | Comparable Security and Sanitization | Perform nonlocal maintenance from systems with comparable security; sanitize serviced components (CCIs: 000882, 000883, 001631) | Section 3 | Mandatory enterprise endpoint compliance, authorized secure bastion hosts, and NIST SP 800-88 Rev. 1 media sanitization. |
| MA-04(04) | Authentication and Session Separation | Protect nonlocal maintenance with replay-resistant MFA and separate maintenance sessions from other traffic (CCIs: 000884, 001632, 002887, 004192) | Section 3 | {{ IDENTITY_PROVIDER }} with {{ MFA_MECHANISM }}, dedicated management subnets, VPC-SC boundaries, and secure encrypted tunnel isolation. |
| MA-04(06) | Cryptographic Protection | Protect integrity and confidentiality of nonlocal maintenance communications using approved cryptography (CCIs: 002890, 003123, 004193) | Section 3 | CNSSP 15 Annex B cryptographic algorithms: TLS 1.3, Layer 2 MACsec (GCM-AES-XPN-256), and Layer 3 IPsec ESP (AES-256-GCM). |
| MA-04(07) | Disconnect Verification | Verify session and network connection termination after completion of nonlocal maintenance (CCI: 002891) | Section 3 | Automated Cloud IAM session expirations, GCP PAM access revoking, and HA VPN gateway idle-connection termination triggers. |
| MA-05 | Maintenance Personnel | Authorize, maintain roster, verify access authorizations, and supervise un-cleared maintenance personnel (CCIs: 000890, 000891, 002894, 002895) | Section 4 | {{ IDENTITY_PROVIDER }} / Cloud IAM access rosters, Google Machine ACLs, mandatory security background vetting, and physical/logical escort requirements. |
| MA-06 | Timely Maintenance | Obtain maintenance support and spare parts within defined timeframes (24 hrs for HA, 3 days for Mod, 7 days for Low) (CCIs: 000903, 002896, 002897) | Section 5 | Google Cloud Enterprise Support SLAs (15-minute P1 response), redundant multi-zone Cloud Interconnect and HA VPN, and automated IaC re-provisioning. |
| MA-06(01) | Preventive Maintenance | Perform preventive maintenance on defined components at scheduled intervals (CCIs: 002898, 002899, 002900) | Section 5 | Scheduled monthly container image refreshes, 90-day Cloud KMS CMEK key rotations, and semi-annual BGP/MACsec maintenance cadences. |
