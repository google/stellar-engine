# CM - Configuration Management Policy and Procedures

## Document Governance & Approval Baseline

| Governance Metric | Policy Standard & Specification |
| :--- | :--- |
| **Document Title** | Configuration Management Policy and Procedures |
| **NIST Control Family** | Configuration Management (CM) |
| **Primary NIST Benchmark** | NIST SP 800-128 (Security-Focused Configuration Management), NIST SP 800-70 |
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
> This document defines the enterprise security policy and implementation procedures for **Configuration Management** under **NIST SP 800-53 Rev. 5 (CM)**.
> Technical infrastructure controls are automatically provisioned and enforced via **{{ SYSTEM_NAME }}** Terraform blueprints.
> Operational rules or contact details requiring manual confirmation are highlighted with RMF Team Callouts.


## 1. Overview

Configuration Management (CM) is the management and control of secure configurations for an {{ SYSTEM_NAME }} to enable security and facilitate the management of risk.

Configuration Management is defined as a collection of activities focused on establishing and maintaining the integrity of products and systems, through control of the processes for initializing, changing, and monitoring the configurations of those products and systems throughout the system development lifecycle. Configuration management is a minimum security requirement identified in Federal Information Processing Standards (FIPS) 200.

This   document   complies   with   the   following   requirements   from   NIST   Special Publication 800-53 Revision 5, "Security and Privacy Controls for Federal Information Systems and Organizations” and is consistent with applicable laws, executive orders, directives, regulations, policies, standards, and guidelines. A detailed compliance matrix can be found in Appendix A, “Detailed Compliance Matrix”.


## 2. Policy and Procedures

The security-focused configuration management process is critical to maintaining a secure state under normal operations, contingency recovery operations, and reconstitution to normal operations. The {{ ORGANIZATION }} Configuration Management plan provides:

- Identification and recording of configurations that impact the security posture of {{ SYSTEM_NAME }};

- The consideration of security risks in approving the initial configuration;

- The analysis of security implications of changes to the {{ SYSTEM_NAME }} configuration; and

- Documentation of the approved/implemented changes.

The overall objective of the {{ ORGANIZATION }} {{ SYSTEM_NAME }} Configuration Management plan is to document and inform stakeholders of policies set forth to maintain a secure configuration management baseline and processes.


### 2.1 Scope

The {{ ORGANIZATION }} {{ SYSTEM_NAME }} is in a constant state of change in response to new, enhanced, corrected, and updated capabilities, patches for correcting flaws and other errors to existing components, new security threats, and changing business function. Implementing information system changes almost always results in adjustments to system configurations. To ensure that required adjustments do not adversely affect the security posture of {{ ORGANIZATION }} or {{ SYSTEM_NAME }}, a well-defined configuration management plan is necessary.


### 2.2 Review & Update

Reviews of policies and procedures are needed periodically to ensure that these documents accurately reflect the process as it is executed.  Additionally, this offers an opportunity to integrate lessons learned and necessary changes  that have been implemented to increase efficiency.

This policy, any supporting documents, procedures, and any {{ ORGANIZATION }} {{ SYSTEM_NAME }} specific configuration management policies/procedures will be reviewed for applicability and accuracy, at least, on an annual basis.  Upon review, these documents will be updated as is required to reflect necessary changes.

This configuration management policy and related procedures/documents will be reviewed for potential changes in preparation of or as a result of the following types of events:

- Security incident after-action report or lessons learned received requiring changes to the review process for configuration changes.

- Changes in orders, directives, laws or regulations affecting configuration management.



### 2.3 Google Cloud Platform (GCP) Inherited Controls & Shared Responsibility Boundary

- **Google Inherited Controls**: Google Cloud manages baseline configurations (`CM-2`), patch management (`CM-3`), and change control (`CM-4`) for all physical datacenters, hypervisors, and core GCP infrastructure services.
- **Customer Implementation Responsibilities**: {{ ORGANIZATION }} is responsible for managing GitOps Infrastructure-as-Code (Terraform) baselines (`CM-2`, `CM-3`), automated CI/CD pipeline code reviews, Cloud Workstations configuration, and maintaining software inventory (`CM-8`).

## 3. Baseline Configuration

Baseline configurations for systems include connectivity, operational, and communication aspects of systems. Baseline configurations are documented, formally reviewed, and agreed-upon specifications for systems or configuration items within those systems. A complete and accurate baseline for {{ SYSTEM_NAME }} is developed and documented and baselines are maintained under configuration control. The baseline configuration is used as a basis for future builds, releases, and/or changes.

Changes to the documented baseline will occur for any of the following items or events:

- To reflect system components that are being replaced due to vendor end of life of their product;

- To reflect major release updates to hardware or software; or

- To reflect any hardware/software mitigations put in place to limit risks.

{{ ORGANIZATION }} have the ability to use Google’s Cloud Deployment Manager to develop a repeatable process for creating and managing configuration baselines for {{ SYSTEM_NAME }}.


### 3.1 Automation Support for Accuracy and Currency

Automated mechanisms that help organizations maintain consistent baseline configurations for systems include configuration management tools, hardware, software, firmware inventory tools, and network management tools. Automated tools can be used at the organization level, mission and business process level, or system level on workstations, servers, notebook computers, network components, or mobile devices. These tools can be used to track version numbers on operating systems, applications, types of software installed, and current patch levels.

{{ ORGANIZATION }} {{ SYSTEM_NAME }} will maintain the currency and accuracy of the hardware and software that is authorized and present within their systems by leveraging a variety of automated means to include such things as:

- Environment and/or host scanning

- Anti-malware

- Automated Directory Services Management policies

- STIG compliance checking capability

- GRC tool for official reporting

{{ ORGANIZATION }} utilizes automated Terraform state management and Git repository version control to maintain up-to-date, complete, accurate, and readily available baseline configurations for {{ SYSTEM_NAME }}.


### 3.2 Retention of Previous Configurations

When a new baseline configuration for {{ ORGANIZATION }} {{ SYSTEM_NAME }} is established, the implication is that all of the changes from the last baseline have been approved. Older versions of approved baseline configurations are maintained for at least Code Retention Time and made available for review or rollback as needed.

The secure baseline is represented in the System Security Plan Hardware/Software List and Architecture Diagram. During assessment, the documented baseline is compared against the assessed baseline. This process is performed at least annually.


### 3.3 Configure Systems and Components for High-risk Areas

There are no {{ ORGANIZATION }} {{ SYSTEM_NAME }} endpoints to issue or return. This is a cloud based system which is accessible throughout the CONUS.

{{ ORGANIZATION }} acknowledges the importance of maintaining comprehensive security measures and will continue to monitor our systems to ensure that appropriate controls are in place to mitigate risks effectively.


## 4. Configuration Change Control

Configuration change control involves the systematic proposal, justification, implementation, testing, review, and disposition of changes, to include upgrades and modifications.

A well-defined configuration change control process is fundamental to any configuration management program. Configuration change control is the process for ensuring that configuration changes to {{ SYSTEM_NAME }} are formally requested, evaluated for their security impact, tested for effectiveness, and approved before they are implemented.

{{ ORGANIZATION }} utilizes Change Control Board (CCB). The Change Control Board (CCB) has a collective responsibility and authority to review and approve/disapprove change requests to {{ ORGANIZATION }} {{ SYSTEM_NAME }}.


### 4.1 Automated Documentation, Notification, and Prohibition of Changes

{{ ORGANIZATION }} uses automated CI/CD Cloud Build pull request checks, Git merge request logs, and automated notifications to ensure the following tasks are completed:

- Document proposed changes to {{ SYSTEM_NAME }};

- Notify approval authorities of proposed changes to {{ SYSTEM_NAME }} and request change approval;

- Highlight proposed changes to {{ SYSTEM_NAME }} that have not been approved or disapproved within 5 business days (`[INFORMATIONAL: OPTIONAL CONFIG: Institutional change window SLA]`)


### 4.2 Testing, Validation, and Documentation of Changes

{{ ORGANIZATION }} documents and implements a process to test and validate changes to the information system before implementing changes on the operational system. Changes to information systems include: modifications to hardware, software, or firmware components and configuration settings.

{{ ORGANIZATION }} {{ SYSTEM_NAME }} is designed to ensure that testing does not interfere with information system operations. {{ ORGANIZATION }} {{ SYSTEM_NAME }} test/design baseline environment functions as the formal pre-production verification and validation environment.

{{ ORGANIZATION }} Configuration Manager shall ensure that an audit trail of testing activity is maintained.


### 4.3 Security and Privacy Representatives

{{ ORGANIZATION }} security and privacy representatives serve as a member of the Change Control Board (CCB).


| Role | Responsibility | Point of Contact |
| --- | --- | --- |
| DevSecOps Lead | Manages Terraform IaC baselines, Git PR approvals, and CI/CD pipelines | {{ ISSO_NAME }} ({{ ISSO_EMAIL }}) |
| Security Manager | Approves configuration change requests and security impact analyses | {{ ISSM_NAME }} ({{ ISSM_EMAIL }}) |
| System Owner | Final authorization for major system architecture modifications | {{ SO_NAME }} ({{ SO_EMAIL }}) |


### 4.4 Automated Security Response

In order to prevent unauthorized changes to {{ SYSTEM_NAME }}, {{ ORGANIZATION }} has implemented automated GitOps branch protection rules, Terraform Plan verification gates, and Google Cloud Organization Policy guardrails (`CM-3(5)`). Automated security responses include: halting unauthorized deployment pipelines, blocking unauthorized cloud resource creation, and issuing immediate alert notifications via {{ TELEMETRY_PIPELINE }} (monitored via {{ THREAT_DETECTION_ENGINE }} and {{ SIEM_TOOL }}) when there is an unauthorized modification of a configuration item.


### 4.5 Cryptography Management

{{ ORGANIZATION }} {{ SYSTEM_NAME }} utilizes Google Cloud Key Management Service (Cloud KMS) Customer-Managed Encryption Keys (CMEK), which are FIPS 140-3 validated for encryption algorithms to protect data at rest and in transit.


### 4.6 Review System Changes

> [!IMPORTANT]
> [WARNING: RMF TEAM ACTION REQUIRED: Confirm institutional Change Control Board (CCB / CAB) review frequencies and operational triggers.]

{{ ORGANIZATION }} Change Control Board (CCB) and DevSecOps release managers review all infrastructure and security changes to {{ SYSTEM_NAME }} bi-weekly or upon major architecture events, including:

- Proposed modifications to foundational Terraform blueprints, IAM roles, or Organization Policy guardrails (`CM-3`).
- High or Critical security vulnerability alerts flagged by {{ VULNERABILITY_SCANNER }}, CI/CD scanners, external {{ CSSP_PROVIDER }}/{{ SIEM_TOOL }} feeds, or Container Analysis (`RA-5`, `SI-2`).
- Unscheduled emergency hotfix deployment requests or post-incident recovery configuration updates (`IR-4`, `CM-3`).
- `[INFORMATIONAL: OPTIONAL CONFIG: Additional agency-specific CCB meeting trigger]`


### 4.7 Prevent or Restrict Configuration Changes

Configuration changes can adversely affect critical system security and privacy functionality.

{{ ORGANIZATION }} utilizes automated CI/CD deployment pipelines ({{ CICD_PLATFORM }} / {{ IAC_TOOL }}), Git branch pull request protections, and Google Cloud Organization Policies to prevent and restrict unauthorized direct modifications to {{ SYSTEM_NAME }}.


## 5. Impact Analyses

Security impact analysis is the analysis conducted by qualified {{ ORGANIZATION }} staff to determine the extent to which changes to {{ ORGANIZATION }} {{ SYSTEM_NAME }} affect the security posture. Because {{ ORGANIZATION }} {{ SYSTEM_NAME }} is typically in a constant state of change, it is important to understand the impact of changes on the functionality of existing security controls and in the context of organizational risk tolerance. Security impact analysis is incorporated in the configuration change control process.

The security impact analysis of a change occurs when changes are analyzed and evaluated for adverse impact on security, preferably before they are approved and implemented, but also in the case of emergency/unscheduled changes. Once the changes are implemented and tested, a security impact analysis (and/or assessment) is performed to ensure that the changes have been implemented as approved, and to determine if there are any unanticipated effects of the change on existing security controls.

The process for a security impact analysis consists of the following steps:


## 6. Understand the Change

If the change is being proposed, develop a high-level architecture overview which shows how the change will be implemented. If the change has already occurred (unscheduled/unauthorized), request follow-up documentation/information and review it or use whatever information is available such as audit records or interview staff who made the change, to gain insight into the change.


## 7. Identify Vulnerabilities

If the change involves a hardware or software product, identify vulnerabilities. {{ ORGANIZATION }} can leverage this information to address known issues and remove or mitigate them before they become a concern. {{ ORGANIZATION }} {{ SYSTEM_NAME }}  will use automated vulnerability scanning tools to search various public vulnerability databases that apply to IT products. If the change involves custom development, a more in-depth analysis of the security impact is conducted.



### 7.1 Google Cloud Platform (GCP) Inherited Controls & Shared Responsibility Boundary

- **Google Inherited Controls**: Google Cloud manages baseline configurations (`CM-2`), patch management (`CM-3`), and change control (`CM-4`) for all physical datacenters, hypervisors, and core GCP infrastructure services.
- **Customer Implementation Responsibilities**: {{ ORGANIZATION }} is responsible for managing GitOps Infrastructure-as-Code (Terraform) baselines (`CM-2`, `CM-3`), automated CI/CD pipeline code reviews, Cloud Workstations configuration, and maintaining software inventory (`CM-8`).

## 8. Assess Risks

Once a vulnerability has been identified, a risk assessment is needed to identify the likelihood of a threat exercising the vulnerability and the impact of such an event. Although vulnerabilities may be identified in changes as they are proposed, built, and tested, the assessed risk may be low enough that the risk can be accepted without remediation. In other cases, the risk may be high enough that the change is not approved, or that safeguards and countermeasures are implemented to reduce the risk.


## 9. Assess Impact on Existing Security Controls

In addition to assessing the risk from the change, {{ ORGANIZATION }} will analyze whether and how a change will impact existing security controls. Determine if the change may involve installation of software that alters the existing baseline configuration, or the change itself may cause or require changes to the existing baseline configuration. The change may also affect other systems or system components that depend on the function or component being changed, either temporarily or permanently.


## 10. Plan Safeguards and Countermeasures

In cases where risks have been identified and are unacceptable, {{ ORGANIZATION }} will use the security impact analysis to revise the change or to plan safeguards and countermeasures to reduce the risk. If the security impact analysis reveals that the proposed change causes a modification to a common secure configuration setting, plans to rework the change to function within the existing setting are initiated. If a change involves new elevated privileges for users, plans to mitigate the additional risk will need to be made.


### 10.1 Separate Test Environments

{{ ORGANIZATION }}  uses a separate test environment in order to analyze changes to {{ SYSTEM_NAME }} before implementation in production.


### 10.2 Verification of Controls

Implementation in this context refers to installing changed code in the operational system that may have an impact on security or privacy controls. After {{ ORGANIZATION }} implements changes to {{ SYSTEM_NAME }}, impacted controls will be verified to ensure they are implemented correctly, operating as intended, and producing the desired outcome.


## 11. Access Restrictions for Change

The {{ SYSTEM_NAME }} code base is built with terraform and controlled by GitHub. Any changes to the code base are handled via a merge/pull review process, preventing arbitrary modification to the core IaC. Changes to code are not reflected in the infrastructure until the code is actually deployed via terraform. Once the code is deployed, modification to the infrastructure via out-of-band changes (i.e., a privileged user modifying the infrastructure through the Google Cloud console), are possible, but would likely break inheritance. {{ ORGANIZATION }} will ensure a policy is enforced to require all changes to the infrastructure should be made via the merge/pull review process.

With the use of {{ SYSTEM_NAME }}, {{ SYSTEM_NAME }} configuration management of physical access restrictions to facilities associated with changes to {{ SYSTEM_NAME }} is documented in the Google Services Configuration Management plan.

{{ ORGANIZATION }} {{ SYSTEM_NAME }} is a cloud based system in which {{ ORGANIZATION }} personnel have no physical access restriction requirements.

{{ ORGANIZATION }} shall ensure logical access restrictions associated with changes to {{ SYSTEM_NAME }} are defined and documented. {{ ORGANIZATION }} {{ SYSTEM_NAME }} IT assets shall be restricted to authorized privileged users. Additionally, an audit trail of logical access to the information system is maintained.


### 11.1 Automated Access Enforcement and Audit Records

{{ ORGANIZATION }} uses Google Cloud Logging aggregated organization sinks exporting to immutable Cloud Storage buckets and BigQuery Log Sinks as the central repository for all organizational audit logs and configuration change audit trails.

{{ ORGANIZATION }} will ensure log system accesses associated with applying configuration changes to ensure that configuration change control is implemented and to support after-the-fact actions should unauthorized changes be discovered.


### 11.2 Privilege Limitation for Production and Operation

Access control policies control access between active entities or subjects and passive entities or objects in {{ ORGANIZATION }} {{ SYSTEM_NAME }}.

{{ ORGANIZATION }} is responsible for adding users to the provided {{ SYSTEM_NAME }} roles for access.

{{ ORGANIZATION }} is responsible for managing all aspects of access control users of {{ SYSTEM_NAME }}.

For all {{ ORGANIZATION }}, access to logical resources shall be documented via user access request workflow (`[WARNING: RMF TEAM ACTION REQUIRED: Account Creation Request Form / GRC Ticket]`). Access to resources is enforced using Google Cloud Identity and Google Cloud IAM.

{{ SYSTEM_NAME }} must enforce approved authorizations for logical access to information and system resources in accordance with applicable access control policies.


### 11.3 Limit Library Privileges

{{ ORGANIZATION }} will limit privileges to change software resident within software libraries.


## 12. Configuration Settings

Configuration settings are the parameters that can be changed in the hardware, software, or firmware components of the system that affect the security and privacy posture or functionality of the system. Information technology products for which configuration settings can be defined include mainframe computers, servers, workstations, operating systems, mobile devices, input/output devices, protocols, and applications. Parameters that impact the security posture of systems include registry settings; account, file, or directory permission settings; and settings for functions, protocols, ports, services, and remote connections.

Privacy parameters are parameters impacting the privacy posture of systems, including the parameters required to satisfy other privacy controls. Privacy parameters include settings for access controls, data processing preferences, and processing and retention permissions.

The established configuration settings become part of the configuration baseline for the system.

{{ SYSTEM_NAME }} infrastructure configuration follows a structured, multi-stage Infrastructure as Code (IaC) deployment model. Pipeline stages deploy foundational resource management, networking, and application workloads in verified sequence. The system's state is managed using secure cloud remote backends enforcing state locking, encryption at rest, and audit tracking.

- Terraform configuration is stored in an infrastructure code repository. Repository access is limited to infrastructure administrators.

- Once the initial bootstrap environment is created by infrastructure admins, all configuration changes are gated by a code review in the infrastructure repository.

Terraform configuration is partitioned into stand-alone per-environment configuration modules. Additional customer tenants can be configured per-environment. To facilitate rapid iteration and collaboration across tenants, configuration is relatively static. Each combination of tenant and environment has a dedicated configuration module. Each configuration module relies on Terraform locals that reside in the same file.

This approach leads to a lot of repetition but minimizes the opportunity for changes in one tenant or environment to impact any other.

{{ ORGANIZATION }} uses applicable STIGs and SRGs as guidance on which configurations are required to be applied to {{ SYSTEM_NAME }}. If appropriate STIGs are not available, the following will be used (in order) for configuration / implementation guidance:

- SRG

- CIS Benchmarks

- Industry Best Practices

Configuration settings will be treated as changes to {{ SYSTEM_NAME }} and follow all guidance from Change Control Board (CCB).


### 12.1 Automated Management, Application, and Verification

{{ ORGANIZATION }} utilizes automated Terraform plan/apply CI/CD pipelines, Google Cloud Policy Intelligence, and Google Cloud Asset Inventory to automate the management, application, and continuous verification of baseline configuration settings in {{ SYSTEM_NAME }}.


### 12.2 Respond to Unauthorized Changes

Response to unauthorized changes to configuration settings include alerting designated personnel, restoring established configuration settings, or halting affected system processing.

If {{ ORGANIZATION }} determines that an unauthorized change has been made to {{ SYSTEM_NAME }}, the following steps will take place:

- Automated rollback of IaC state via Terraform apply

- Quarantine or isolate affected GCP resource/VPC network

- Trigger immediate high-priority alert via {{ TELEMETRY_PIPELINE }} to {{ SIEM_TOOL }} / {{ CSSP_PROVIDER }} incident dispatch queues

- Initiate root-cause security investigation and incident report


## 13. Least Functionality

All {{ ORGANIZATION }} {{ SYSTEM_NAME }} are configured to the least functionality possible. Cloud IAM authorizes a user with only necessary capabilities to perform functions that meet the requirements of a specific assigned role. {{ ORGANIZATION }} shall document the essential capabilities which the system must provide and prohibited or restricted functions, ports, protocols, and/or services in accordance with the United States Government Configuration Baseline (USGCB).

{{ ORGANIZATION }} utilizes: Google Cloud Asset Inventory, {{ TELEMETRY_PIPELINE }} and {{ THREAT_DETECTION_ENGINE }} to scan networks, {{ INTRUSION_DETECTION_SYSTEM }} for intrusion detection and prevention, and {{ EDR_SOLUTION }} for endpoint protection


### 13.1 Periodic Review

{{ ORGANIZATION }} will review functions, ports, protocols, and services on {{ SYSTEM_NAME }} quarterly review period for functions, ports, protocols, and services. {{ ORGANIZATION }} will disable or remove the identified functions, ports, protocols, or services within 30 calendar days.


### 13.2 Prevent Program Execution

Prevention of program execution addresses {{ ORGANIZATION }} policies, rules of behavior, and/or access agreements that restrict software usage and the terms and conditions imposed by the developer or manufacturer, including software licensing and copyrights. Restrictions include prohibiting auto-execute features, restricting roles allowed to approve program execution, permitting or prohibiting specific software programs, or restricting the number of program instances executed at the same time.

All program execution within {{ SYSTEM_NAME }} occurs via managed services. Each service has IAM profiles and policies associated with them that strictly control the execution rights and privileges assigned to them.


### 13.3 Registration Compliance

{{ ORGANIZATION }} ensures the registration requirements for functions, ports, protocols, and services are implemented in accordance with Google Cloud Identity Registration & Compliance SOP


### 13.4 Authorized Software - Allow-by-Exception

{{ ORGANIZATION }} employs an allow-by-exception policy for {{ SYSTEM_NAME }}. The list of services is reviewed and updated, as necessary, but at least annually.


### 13.5 Binary or Machine Executable Code

> [!IMPORTANT]
> [WARNING: RMF TEAM ACTION REQUIRED: Verify and update operational contact/procedure details in this section.]
> Binary or machine executable code applies to all sources of binary or machine-executable code, including commercial software and firmware and open-source software. {{ ORGANIZATION }} prohibits the use of binary or machine-executable code from sources with limited or no warranty or without the provision of source code. {{ ORGANIZATION }} allows for exceptions only for compelling mission or requirements with the approval of the authorizing official.


### 13.6 Prohibiting the Use of Unauthorized Hardware

Hardware components provide the foundation for the systems and platform for the execution of authorized software programs. {{ ORGANIZATION }} manages the inventory of hardware components and controlling which hardware components are permitted to be installed or connected to {{ SYSTEM_NAME }}.

{{ ORGANIZATION }} will prohibit the use or connection of unauthorized hardware components. {{ ORGANIZATION }} will review and update the list of authorized hardware components, as necessary, but at least annually.


## 14. System Component Inventory

System components are discrete, identifiable information technology assets that include hardware, software, and firmware. {{ ORGANIZATION }} uses dynamic build extraction tooling (`extract_system_data.py`), `system_inventory.json`, and Google Cloud Asset Inventory exports as a centralized location for component inventory for {{ SYSTEM_NAME }}. In addition to Cloud Asset Inventory, the automated `Hardware_Software_Inventory.yaml` list and authorization boundary diagram provide an active overview of system components.

{{ ORGANIZATION }} reviews and updates `system_inventory.json`, the `Hardware_Software_Inventory.yaml` list, and authorization boundary diagrams continuously upon build release, and at least annually.


### 14.1 Updates During Installation and Removal

{{ ORGANIZATION }} shall maintain the accuracy, completeness, and consistency of system component inventories. Inventories shall be updated as part of component installations or removals or during general system updates.


### 14.2 Automated Maintenance

{{ ORGANIZATION }} utilizes automated build extraction scripts (`extract_system_data.py`) and Google Cloud Asset Inventory exports to maintain an up-to-date, complete, accurate, and readily available inventory of system components.


### 14.3 Automated Unauthorized Component Detection

{{ ORGANIZATION }} utilizes Google Cloud Asset Inventory continuous feed alerts, {{ TELEMETRY_PIPELINE }} into {{ SIEM_TOOL }}, and Terraform Plan checks to detect unauthorized components or drift on {{ SYSTEM_NAME }}.


### 14.4 Accountability Information

Identifying individuals who are responsible and accountable for administering {{ SYSTEM_NAME }} components ensures that the assigned components are properly administered and that {{ ORGANIZATION }} can contact those individuals if some action is required.

{{ ORGANIZATION }} utilizes code-repository CODEOWNERS mappings and `compliance_config.yaml` role assignments as a means for identifying individuals responsible and accountable for {{ SYSTEM_NAME }} components.


## 15. Software Usage Restrictions

All software contained within {{ ORGANIZATION }} Systems must be correctly licensed. {{ ORGANIZATION }} authorizes the use of Commercial Off-the-shelf (COTS), Government Off-the-shelf (GOTS), and where applicable, vetted and approved, Open-Source Software (OSS).  {{ ORGANIZATION }} {{ SYSTEM_NAME }} is encouraged to leverage enterprise licensing where available.


### 15.1 Open-Source Software

Open-source software refers to software that is available in source code form. Certain software rights normally reserved for copyright holders are routinely provided under software license agreements that permit individuals to study, change, and improve the software. From a security perspective, the major advantage of open-source software is that it provides {{ ORGANIZATION }} with the ability to examine the source code. Remediate vulnerabilities in open-source software may be problematic.

{{ ORGANIZATION }} has established the following restrictions when using open-source software:

- Open-source software (OSS) must be sieved exclusively from verified upstream Google Cloud Platform open-source templates or curated enterprise artifact registries (`SA-4`).
- All open-source container images and software dependencies must pass automated vulnerability scanning (Container Analysis / Software Composition Analysis) with zero unresolved Critical or High CVEs (`RA-5`, `SI-2`).
- Open-source software licenses must comply with agency legal counsel licensing terms (permissible Apache 2.0/MIT/BSD vs restricted AGPL) (`SA-4`).


## 16. User-installed Software

Only privileged users have the ability to install software on {{ SYSTEM_NAME }}.

The following user types are authorized to install software on {{ SYSTEM_NAME }}:


| User Type | Privilege Level | Notes |
| --- | --- | --- |
| Org Administrator | High (Privileged) | Restricted access via {{ MFA_MECHANISM }} & {{ IDENTITY_PROVIDER }} |
| Security Administrator | High (Privileged) | {{ THREAT_DETECTION_ENGINE }} & Org Policy management |
| Developer / DevOps | Medium (Non-Privileged) | Read-only in prod; PR submission for changes |
| Service Account | System (Keyless WIF) | CI/CD pipeline deployment via {{ CICD_PLATFORM }} |


## 17. Information Location

Information location addresses the need to understand where information is being processed and stored. Information location includes identifying where specific information types and information reside in {{ SYSTEM_NAME }} components and how information is being processed so that information flow can be understood, and adequate protection and policy management provided for such information and {{ SYSTEM_NAME }} components. The security category of the information is also a factor in determining the controls necessary to protect the information and the system component where the information resides (see FIPS 199). The location of the information and system components is also a factor in the architecture and design of the system.

{{ ORGANIZATION }} shall:

- Identify and document the location of the specific {{ SYSTEM_NAME }} components on which the information is processed and stored;

- Identify and document the users who have access to {{ SYSTEM_NAME }} and {{ SYSTEM_NAME }} components where the information is processed and stored; and,

- Document changes to the location where the information is processed and stored.


### 17.1 Automated Tools to Support Information Location

The use of automated tools helps to increase the effectiveness and efficiency of the information location capability implemented within {{ SYSTEM_NAME }}. The output of automated information location tools can be used to guide and inform system architecture and design decisions.

{{ ORGANIZATION }} uses Google Cloud Asset Inventory metadata, Cloud KMS resource region constraints, and Google Cloud Sensitive Data Protection (Cloud DLP) automated inspection jobs to ensure controls are in place to protect {{ ORGANIZATION }} information and individual privacy.


## 18. Signed Components

Software and firmware components prevented from installation unless signed with recognized and approved certificates include software and firmware version updates, patches, service packs, device drivers, and basic input/output system updates.

{{ ORGANIZATION }} prevents the installation of software and firmware without verification that the component has been digitally signed using a certificate that is recognized and approved by {{ ORGANIZATION }}.



## Appendix A – Detailed Compliance Matrix

The following table provides detailed traceability between the policy implementation statements in this document, the authoritative NIST SP 800-53 Rev. 5 control requirements, DoD CCIs, and the technical/governance enforcement mechanisms active across {{ SYSTEM_NAME }}.


| CTRL ID | CTRLTITLE | REQUIRED eMASS STANDARD | DOCREF | ENFORCEMENT MECHANISM |
| :--- | :--- | :--- | :--- | :--- |
| CM-01 | Policy and Procedures | Develop, document, disseminate to all stakeholders, and review/update annually (or upon major change tool upgrades/incidents) CM policy and procedures. (CCIs: 000286, 000287, 000289, 000290, 000292, 001584, 001821, 001822, 001824, 001825, 003897, 003898, 003899, 003900, 003901, 003902, 003903, 003904, 003905, 003906, 003907, 003908) | Section 2.1 | Formal annual review workflow by {{ ORGANIZATION }} CCB/SO/ISSM; published in governance repository; event-driven triggers. |
| CM-02 | Baseline Configuration | Develop, document, and maintain under configuration control a baseline configuration; review annually, after major updates, and upon STIG releases. (CCIs: 000295, 000296, 000297, 001497, 001585, 003909, 003910) | Section 2.2 | Git repository version-controlled Terraform code; System Security Plan architecture models; annual baseline audits. |
| CM-02(02) | Automation Support for Accuracy and Currency | Employ automated mechanisms (SCAP, HBSS, Terraform, Cloud Asset Inventory) to maintain currency and accuracy of baseline configurations. (CCIs: 000300, 000301, 000302, 000303, 003911) | Section 2.2 | Automated Terraform state in GCS; Cloud Asset Inventory continuous discovery feeds; SCAP/Checkov compliance scans. |
| CM-02(03) | Retention of Previous Configurations | Retain at least two (2) previous versions of approved baseline configurations to support immediate operational rollback. (CCIs: 000304, 001736) | Section 2.2 | Git version control tag history; GCS bucket object versioning on Terraform state files; container image registry tags. |
| CM-02(07) | Configure Systems and Components for High-risk Areas | Enforce hardened configuration, inspection, and zero-trust controls for endpoints accessing the system from high-risk environments. (CCIs: 001737, 001738, 001739, 001815, 001816) | Section 2.2 | Managed virtual desktops / secure bastion hosts; {{ MFA_MECHANISM }}; boundary traffic inspection gateways. |
| CM-03 | Configuration Change Control | Formally request, evaluate, test, and approve all configuration changes; convene CCB at least monthly; retain records for 1 year / 2 cycles. (CCIs: 000313, 000314, 000316, 000318, 000319, 000320, 000321, 001586, 001740, 001741, 001819, 002056, 003912) | Section 2.3 | {{ ORGANIZATION }} CCB charter; monthly CCB review meetings; GitLab/GitHub pull request change logs and approval histories. |
| CM-03(02) | Testing, Validation, and Documentation of Changes | Test and validate all changes in separate staging environments prior to production; maintain audit trails of test execution. (CCIs: 000327, 000328, 000329) | Section 2.3 | Automated CI/CD pipeline tests; deployment validation in dedicated development and test staging projects. |
| CM-03(04) | Security and Privacy Representatives | Mandate cybersecurity and privacy representatives as formal voting members of the Configuration Control Board (CCB). (CCIs: 000332, 003921, 003922, 003923, 003924) | Section 2.3 | CCB formal charter; voting sign-offs by ISSM ({{ ISSM_NAME }}) and DevSecOps Lead ({{ ISSO_NAME }}). |
| CM-03(06) | Cryptography Management | Subject all controls and system components relying on cryptography to formal configuration management. (CCIs: 001745, 001746) | Section 2.3 | Configuration control of Cloud KMS CMEK keyrings, transport MACsec keys, and virtual appliance IPsec parameters. |
| CM-03(07) | Review System Changes | Review system changes quarterly (for Moderate Integrity) and immediately post-incident to verify compliance with CCB authorizations. (CCIs: 003925, 003926, 003927) | Section 2.3 | Quarterly CCB audit reviews; automated CI/CD deployment log audits; post-incident configuration reconciliation. |
| CM-03(08) | Prevent or Restrict Configuration Changes | Prevent and restrict unauthorized direct modifications to production cloud infrastructure and configuration baselines. (CCIs: None - Out of Scope for Package) | Section 2.3 | Git branch protections; Organization Policies; prohibition of manual Google Cloud Console edits in production. |
| CM-04 | Impact Analyses | Conduct Security Impact Analysis (SIA) before implementing changes to evaluate security posture and control effects. (CCIs: 000333, 003930) | Section 2.4 | Formal 5-step SIA methodology; pre-merge automated security scans; ISSM security risk evaluation sign-offs. |
| CM-04(01) | Separate Test Environments | Maintain separate test/development environments physically and logically isolated from the operational production system. (CCIs: 001817, 001818, 003931) | Section 2.4 | Hard project boundaries for Dev (*-d) and Test (*-t) environments; separate KMS encryption keys and state buckets. |
| CM-04(02) | Verification of Controls | Verify that all impacted security and privacy controls operate effectively and as intended following production implementation. (CCIs: 000335, 000336, 000337, 003932, 003933, 003934) | Section 2.4 | Post-deployment automated CI/CD validation test suites; ISSO operational security control verification audits. |
| CM-05 | Access Restrictions for Change | Define and enforce logical access restrictions governing authorization to propose, approve, and execute system changes. (CCIs: 000340, 000341, 000344, 000345, 003935, 003936) | Section 2.5 | Git repository branch protections; CODEOWNERS approval gating; prohibition of manual out-of-band console changes. |
| CM-05(01) | Automated Access Enforcement and Audit Records | Enforce access restrictions via automated GitOps mechanisms and maintain complete audit trails of all configuration change events. (CCIs: 001813, 003937, 003938) | Section 2.5 | GitHub/GitLab ACLs; Cloud Audit Logs capturing all deployment API calls; real-time Pub/Sub streaming to SIEM. |
| CM-05(05) | Privilege Limitation for Production and Operation | Deny human production change rights; execute deployments via keyless WIF service accounts; review privileges at least annually. (CCIs: 001753, 001754, 003939, 003940) | Section 2.5 | Automated CI/CD deployment service accounts executing via WIF OIDC; annual CCB privilege re-evaluation audits. |
| CM-05(06) | Limit Library Privileges | Restrict privileges to modify shared software libraries, Terraform modules, and container registries to authorized DevSecOps leads. (CCIs: 001499) | Section 2.5 | Google Artifact Registry IAM permissions; protected Terraform module repositories with restricted write access. |
| CM-06 | Configuration Settings | Establish and enforce mandatory configuration settings based on DISA STIGs/SRGs, CIS Benchmarks; require AO approval for deviations. (CCIs: 000366, 000367, 000368, 000369, 001755, 001756, 003941, 003942, 003943, 003944, 003945, 003946) | Section 2.6 | DISA STIG compliance baselines; Google Cloud Organization Policies; formal AO Exception to Policy (ETP) workflows. |
| CM-06(01) | Automated Management, Application, and Verification | Manage, apply, and verify configuration settings across all components using automated tools (HBSS, GPO, Terraform, Org Policies). (CCIs: 000370, 000371, 000372, 002059, 003947) | Section 2.6 | Organization Policy constraints (vmExternalIpAccess, publicAccessPrevention); Terraform CI/CD posture enforcement. |
| CM-06(02) | Respond to Unauthorized Changes | Respond to unauthorized configuration changes by alerting personnel, isolating resources, and rolling back to approved baselines. (CCIs: None - Out of Scope for Package) | Section 2.6 | Real-time alerts via Cloud Logging export sinks to external accredited CSSP/SIEM and Cloud Monitoring (or SCC Event Threat alerts in FedRAMP High / Commercial enclaves); automated Terraform apply rollback triggers; VPC quarantine rules. |
| CM-07 | Least Functionality | Configure system to provide only mission-essential capabilities; prohibit unnecessary ports, protocols, functions, and services. (CCIs: 000380, 000381, 000382, 003948) | Section 2.7 | Removal of unused OS packages; strict VPC firewall ingress/egress rules; least functionality IAM permissions. |
| CM-07(01) | Periodic Review | Review system ports, protocols, and services at least annually; disable or remove unnecessary services within 30 days. (CCIs: 000384, 001760, 001761, 001762) | Section 2.7 | Annual PPSM audits; quarterly vulnerability scan port reviews; automated disablement of unapproved services. |
| CM-07(02) | Prevent Program Execution | Prevent unauthorized program execution adhering to software usage rules, licensing terms, and application execution controls. (CCIs: 001592, 001763, 001764) | Section 2.7 | AppLocker / Linux STIG application whitelisting; Google Cloud Binary Authorization on serverless containers. |
| CM-07(03) | Registration Compliance | Ensure all network ports, protocols, and services comply with and are registered under DoDI 8551.01 (PPSM). (CCIs: 000387, 000388) | Section 2.7 | Formal registration in DoD PPSM Central Registry; automated verification against registered PPSM category codes. |
| CM-07(05) | Authorized Software: Allow-by-exception | Enforce an allow-by-exception software policy; review and update the Authorized Software List at least quarterly. (CCIs: 001772, 001773, 001774, 001775, 001777) | Section 2.7 | CCB-approved Authorized Software List; Google Artifact Registry curated base images; quarterly software reviews. |
| CM-07(08) | Binary or Machine Executable Code | Prohibit the use of unverified binary/executable code lacking source code transparency or warranty; require AO approval for exceptions. (CCIs: 003955, 003956) | Section 2.7 | Pre-merge source code verification; container provenance scanning; ban on unverified third-party binaries. |
| CM-07(09) | Prohibiting The Use of Unauthorized Hardware | Prohibit unauthorized hardware; permit only evaluated, approved hardware components; review hardware list annually. (CCIs: 003957, 003958, 003959, 003960, 003961) | Section 2.7 | Google Cloud Services P-ATO data center physical security; Google Titan chip hardware attestation; annual CCB hardware reviews. |
| CM-08 | System Component Inventory | Maintain a comprehensive inventory of all system components (hardware, software, cloud resources); review/update continuously. (CCIs: 000398, 001779, 001780, 003962, 003963, 003964, 003965, 003966, 003967) | Section 2.8 | Centralized system_inventory.json and Hardware_Software_Inventory.yaml artifacts; annual SSP inventory reconciliation. |
| CM-08(01) | Updates During Installation and Removal | Update system component inventories automatically as part of component installation, modification, or removal. (CCIs: 000408, 000409, 000410) | Section 2.8 | Automated CI/CD build extraction scripts (extract_system_data.py); dynamic Cloud Asset Inventory sync. |
| CM-08(02) | Automated Maintenance | Employ automated mechanisms (ACAS, HBSS, Cloud Asset Inventory) to maintain inventory currency, accuracy, and completeness. (CCIs: 000411, 000412, 000413, 000414, 003968) | Section 2.8 | Google Cloud Asset Inventory continuous discovery feeds; ACAS network asset scans; CMDB aggregation. |
| CM-08(03) | Automated Unauthorized Component Detection | Continuously detect unauthorized components via automated tools; isolate components and notify ISSM/ISSO in real time (15 mins). (CCIs: 000415, 000416, 001783, 001784, 003969) | Section 2.8 | Real-time Cloud Asset Inventory drift feeds; Cloud Logging Log Router alerts to external CSSP/SIEM (or SCC alerts in FedRAMP High / Commercial enclaves); automated network quarantine rules. |
| CM-08(07) | Centralized Configuration Management Repository | Maintain a centralized, integrated repository for all component inventory and configuration baseline records. (CCIs: 001785) | Section 2.8 | Centralized Git repository linked with eMASS and CMDB; integrated configuration traceability databases. |
| CM-09 | Configuration Management Plan | Develop, document, and implement a Configuration Management Plan; review and approve by AO, SO, and ISSM at least annually. (CCIs: 000423, 000426, 001792, 001795, 001798, 001799, 001801, 003971, 003972, 003973, 003974, 003975, 003976, 003977, 003978, 003979) | Section 2.9 | Formally approved {{ SYSTEM_NAME }} Configuration Management Plan (CMP); annual AO/SO/ISSM re-certification workflows. |
| CM-10 | Software Usage Restrictions | Enforce compliance with software licenses, copyright agreements, and usage restrictions across all system components. (CCIs: 001726, 001727, 001728, 001729, 001730, 001731, 001802, 001803) | Section 2.10 | Enterprise software license tracking; automated container dependency auditing in CI/CD pipelines. |
| CM-10(01) | Open-source Software | Govern open-source software usage per DoD 2022 Memo; mandate Software Bill of Materials (SBOM) and vulnerability vetting. (CCIs: 001734, 001735) | Section 2.10 | Automated SBOM generation (Syft/Trivy); Container Analysis vulnerability screening; Artifact Registry curation. |
| CM-11 | User-installed Software | Strictly prohibit user-installed software; enforce via removal of admin rights, application allowlisting, and continuous monitoring. (CCIs: 001804, 001805, 001806, 001807, 001808, 001809) | Section 2.10 | Non-root container runtime execution; removal of administrative rights on bastions; Endpoint Security monitoring. |
| CM-11(02) | Software Installation with Privileged Status | Restrict software installation privileges strictly to authorized system administrators executing CCB-approved changes. (CCIs: 003980) | Section 2.10 | Dedicated administrative role bindings; mandatory CCB change authorization gating for software deployment. |
| CM-12 | Information Location | Identify and document exact geographic and logical locations of {{ SENSITIVITY_CLASSIFICATION }}, {{ IMPACT_LEVEL }} data, and system components; document all location changes. (CCIs: 003982, 003983, 003984, 003985, 003986, 003987) | Section 2.10 | Cloud KMS US-only region constraints; VPC subnet location documentation; System Security Plan data mapping. |
| CM-12(01) | Automated Tools to Support Information Location | Deploy automated tools (Cloud DLP, Cloud Asset Inventory) to identify and track {{ SENSITIVITY_CLASSIFICATION }}, PII, and mission data across components. (CCIs: 003988, 003989, 003990) | Section 2.10 | Google Cloud Sensitive Data Protection automated discovery jobs; BigQuery column-level metadata tagging. |
| CM-13 | Data Action Restrictions | Enforce least-privilege data action restrictions across system datasets and data repositories. (CCIs: 003991) | Section 2.10 | Cloud IAM fine-grained dataset permissions; BigQuery row/column security; Cloud Storage IAM restrictions. |
| CM-14 | Signed Components | Prevent the installation of software, container images, patches, or firmware unless digitally signed using approved {{ PKI_TRUST_TYPE }} certificates. (CCIs: 003992, 003993) | Section 2.10 | Google Cloud Binary Authorization; cryptographic container image signature validation (cosign); PKI driver checks. |
