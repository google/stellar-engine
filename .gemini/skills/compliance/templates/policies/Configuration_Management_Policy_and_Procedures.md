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
> This document defines the enterprise security policy and implementation procedures for **Configuration Management** under **NIST SP 800-53 Rev. 5 (CM)**.
> Technical infrastructure controls are automatically provisioned and enforced via **{{ SYSTEM_NAME }}** Terraform blueprints.
> Operational rules or contact details requiring manual confirmation are highlighted with RMF Team Callouts.


## 1. Overview

Federal agencies and organizations cannot protect the confidentiality, integrity, and availability of information in today's highly networked systems environment without ensuring that all people involved in using and managing IT:

1. Understand their roles and responsibilities related to the organizational mission;
2. Understand the organization's IT security policy, procedures, and practices; and
3. Have at least adequate knowledge of the various management, operational, and technical controls required and available to protect the IT resources for which they are responsible.

The purpose of this Configuration Management Policy is to establish and maintain secure baseline configurations and inventories of {{ SYSTEM_NAME }} components and to control changes to them throughout the system development life cycle.

This policy addresses the Configuration Management (CM) family requirements of NIST Special Publication 800-53 Revision 5, "Security and Privacy Controls for Information Systems and Organizations." A detailed compliance matrix is provided in Appendix A, "Detailed Compliance Matrix."

The Configuration Management Policy encompasses all {{ ORGANIZATION }} users who have access to {{ SYSTEM_NAME }}. This policy outlines the framework for establishing, implementing, and maintaining configuration management in alignment with applicable {{ GOVERNANCE_REGIME }} guidelines (NIST SP 800-53, FedRAMP, and applicable federal and state regulations), and is consistent with applicable laws, executive orders, directives, regulations, policies, standards, and guidelines. It applies to employees, contractors, and third-party users who handle sensitive information or operate within the {{ ORGANIZATION }} {{ SYSTEM_NAME }} information technology infrastructure.

{{ ORGANIZATION }} management is committed to the requirements of this policy and provides the resources needed to implement them. The ISSM ({{ ISSM_NAME }}) manages the development, documentation, and dissemination of this policy and its procedures, and coordinates their implementation with the Authorizing Official, System Owner, ISSO, and other organizational entities identified in the Program Roles & Responsibilities Matrix.

This policy and its procedures are reviewed and updated at least annually and following significant changes to {{ SYSTEM_NAME }} or its operating environment, security or privacy incidents, assessment or audit findings, or changes in applicable laws, executive orders, directives, regulations, policies, standards, or guidelines.

### 1.1 Background

Configuration management (CM) is the management and control of secure configurations for {{ SYSTEM_NAME }} to enable security and facilitate the management of risk. It is a collection of activities focused on establishing and maintaining the integrity of products and systems through control of the processes for initializing, changing, and monitoring their configurations throughout the system development life cycle. Configuration management is a minimum security requirement identified in Federal Information Processing Standards (FIPS) 200.


## 2. Policy and Procedures

The security-focused configuration management process is critical to maintaining a secure state under normal operations, contingency recovery operations, and reconstitution to normal operations.


### 2.1 Scope

The {{ ORGANIZATION }} {{ SYSTEM_NAME }} is in a constant state of change in response to new, enhanced, corrected, and updated capabilities, patches for correcting flaws and other errors to existing components, new security threats, and changing business functions. Implementing system changes almost always results in adjustments to system configurations. To ensure that these adjustments do not adversely affect the security posture of {{ ORGANIZATION }} or {{ SYSTEM_NAME }}, a well-defined configuration management process is necessary.


### 2.2 Review & Update

This policy, its procedures, and any {{ ORGANIZATION }} {{ SYSTEM_NAME }} specific configuration management procedures are reviewed and updated as described in Section 1. Reviews confirm that the documents reflect the process as it is executed and incorporate lessons learned, including security incident after-action reports that require changes to the review process for configuration changes.


### 2.3 Configuration Management Plan

{{ ORGANIZATION }} develops, documents, and implements a {{ SYSTEM_NAME }} Configuration Management Plan (CMP) that provides:

- Identification and recording of configurations that affect the security posture of {{ SYSTEM_NAME }};

- Consideration of security risks in approving the initial configuration;

- Analysis of the security implications of changes to the {{ SYSTEM_NAME }} configuration; and

- Documentation of approved and implemented changes.

The CMP documents the processes that maintain the secure configuration baseline and informs stakeholders of them. The AO, System Owner, and ISSM review and approve the CMP at least annually.

[CONFIG_REQUIRED: Configuration items placed under configuration management and the controls that protect the CMP from unauthorized disclosure and modification]


### 2.4 Google Cloud Platform (GCP) Inherited Controls & Shared Responsibility Boundary

- **Google Inherited Controls**: Google Cloud manages baseline configurations (`CM-2`), patch management (`CM-3`), and change control (`CM-4`) for all physical data centers, hypervisors, and core Google Cloud infrastructure services.
- **Customer Implementation Responsibilities**: {{ ORGANIZATION }} is responsible for managing GitOps Infrastructure-as-Code (Terraform) baselines (`CM-2`, `CM-3`), automated CI/CD pipeline code reviews, Cloud Workstations configuration, and maintaining software inventory (`CM-8`).

## 3. Baseline Configuration

Baseline configurations for systems include connectivity, operational, and communication aspects of systems. Baseline configurations are documented, formally reviewed, and agreed-upon specifications for systems or configuration items within those systems. A complete and accurate baseline for {{ SYSTEM_NAME }} is developed and documented and baselines are maintained under configuration control. The baseline configuration is used as a basis for future builds, releases, and/or changes.

Changes to the documented baseline will occur for any of the following items or events:

- To reflect system components that are being replaced due to vendor end of life of their product;

- To reflect major release updates to hardware or software; or

- To reflect any hardware/software mitigations put in place to limit risks.

{{ ORGANIZATION }} uses Terraform infrastructure-as-code modules, stored in version-controlled Git repositories, as the repeatable process for creating and managing configuration baselines for {{ SYSTEM_NAME }}.


### 3.1 Automation Support for Accuracy and Currency

Automated mechanisms that help organizations maintain consistent baseline configurations for systems include configuration management tools, hardware, software, and firmware inventory tools, and network management tools. Automated tools can be used at the organization level, mission and business process level, or system level on workstations, servers, notebook computers, network components, or mobile devices. These tools can track version numbers of operating systems and applications, the types of software installed, and current patch levels.

{{ ORGANIZATION }} {{ SYSTEM_NAME }} maintains the currency and accuracy of the hardware and software that is authorized and present within its systems by using automated means, including:

- Environment and/or host scanning

- Anti-malware

- Automated Directory Services Management policies

- STIG compliance checking capability

- GRC tool for official reporting

{{ ORGANIZATION }} uses automated Terraform state management and Git repository version control to maintain up-to-date, complete, accurate, and readily available baseline configurations for {{ SYSTEM_NAME }}.


### 3.2 Retention of Previous Configurations

When a new baseline configuration for {{ ORGANIZATION }} {{ SYSTEM_NAME }} is established, all of the changes from the last baseline are considered approved. {{ ORGANIZATION }} retains at least two (2) previous versions of approved baseline configurations and makes them available for review and rollback.

The secure baseline is represented in the System Security Plan Hardware/Software List and Architecture Diagram. During assessment, the documented baseline is compared against the assessed baseline. This comparison is performed at least annually.


### 3.3 Configure Systems and Components for High-risk Areas

{{ ORGANIZATION }} does not issue {{ SYSTEM_NAME }} endpoints to individuals, so there are no endpoints to issue before travel or to inspect on return. {{ SYSTEM_NAME }} is a cloud-based system accessible throughout the continental United States (CONUS). Personnel who access {{ SYSTEM_NAME }} from high-risk locations do so only through managed virtual desktops or secure bastion hosts with {{ MFA_MECHANISM }}.


## 4. Configuration Change Control

Configuration change control involves the systematic proposal, justification, implementation, testing, review, and disposition of changes, to include upgrades and modifications.

A well-defined configuration change control process is fundamental to any configuration management program. Configuration change control is the process for ensuring that configuration changes to {{ SYSTEM_NAME }} are formally requested, evaluated for their security impact, tested for effectiveness, and approved before they are implemented.

{{ ORGANIZATION }} uses a Change Control Board (CCB), which has collective responsibility and authority to review and approve or disapprove change requests to {{ ORGANIZATION }} {{ SYSTEM_NAME }}.


### 4.1 Automated Documentation, Notification, and Prohibition of Changes

{{ ORGANIZATION }} uses automated CI/CD Cloud Build pull request checks, Git merge request logs, and automated notifications to ensure the following tasks are completed:

- Document proposed changes to {{ SYSTEM_NAME }};

- Notify approval authorities of proposed changes to {{ SYSTEM_NAME }} and request change approval;

- Highlight proposed changes to {{ SYSTEM_NAME }} that have not been approved or disapproved within 5 business days (`[INFORMATIONAL: OPTIONAL CONFIG: Institutional change window SLA]`).


### 4.2 Testing, Validation, and Documentation of Changes

{{ ORGANIZATION }} documents and implements a process to test and validate changes to the system before implementing them on the operational system. Changes to the system include modifications to hardware, software, or firmware components and configuration settings.

{{ ORGANIZATION }} {{ SYSTEM_NAME }} is designed so that testing does not interfere with system operations. The {{ ORGANIZATION }} {{ SYSTEM_NAME }} test/design baseline environment is the formal pre-production verification and validation environment.

The {{ ORGANIZATION }} Configuration Manager ensures that an audit trail of testing activity is maintained.


### 4.3 Security and Privacy Representatives

{{ ORGANIZATION }} security and privacy representatives serve as members of the Change Control Board (CCB).


| Role | Responsibility | Point of Contact |
| --- | --- | --- |
| DevSecOps Lead | Manages Terraform IaC baselines, Git PR approvals, and CI/CD pipelines | [CONFIG_REQUIRED: DevSecOps Lead Point of Contact] |
| Security Manager | Approves configuration change requests and security impact analyses | {{ ISSM_NAME }} ({{ ISSM_EMAIL }}) |
| Privacy Representative | Reviews changes that affect the processing of personally identifiable information | [CONFIG_REQUIRED: Privacy Representative Point of Contact] |
| System Owner | Final authorization for major system architecture modifications | {{ SO_NAME }} ({{ SO_EMAIL }}) |


### 4.4 Automated Security Response

To prevent unauthorized changes to {{ SYSTEM_NAME }}, {{ ORGANIZATION }} has implemented automated GitOps branch protection rules, Terraform Plan verification gates, and Google Cloud Organization Policy guardrails (`CM-3(5)`). Automated security responses include halting unauthorized deployment pipelines, blocking unauthorized cloud resource creation, and issuing immediate alert notifications via {{ TELEMETRY_PIPELINE }} (monitored via {{ THREAT_DETECTION_ENGINE }} and {{ EXTERNAL_SIEM }}) when a configuration item is modified without authorization.


### 4.5 Cryptography Management

{{ ORGANIZATION }} places the cryptographic mechanisms that protect {{ SYSTEM_NAME }} under configuration management. Cloud Key Management Service (Cloud KMS) customer-managed encryption key (CMEK) key rings, transport MACsec keys, and virtual appliance IPsec parameters are defined in Terraform and changed only through the configuration change control process. Cloud KMS CMEK keys protect data at rest using FIPS 140-3 validated cryptographic modules.


### 4.6 Review System Changes

> [!IMPORTANT]
> [WARNING: RMF TEAM ACTION REQUIRED: Confirm institutional Change Control Board (CCB / CAB) review frequencies and operational triggers.]

{{ ORGANIZATION }} Change Control Board (CCB) and DevSecOps release managers review all infrastructure and security changes to {{ SYSTEM_NAME }} bi-weekly or upon major architecture events, including:

- Proposed modifications to foundational Terraform blueprints, IAM roles, or Organization Policy guardrails (`CM-3`).
- High or Critical security vulnerability alerts flagged by {{ VULNERABILITY_SCANNER }}, CI/CD scanners, external {{ CSSP_PROVIDER }}/{{ EXTERNAL_SIEM }} feeds, or Container Analysis (`RA-5`, `SI-2`).
- Unscheduled emergency hotfix deployment requests or post-incident recovery configuration updates (`IR-4`, `CM-3`).
- `[INFORMATIONAL: OPTIONAL CONFIG: Additional agency-specific CCB meeting trigger]`

At least quarterly, and after security incidents, the CCB also reviews deployed changes against CCB authorizations to determine whether unauthorized changes have occurred.


### 4.7 Prevent or Restrict Configuration Changes

Configuration changes can adversely affect critical system security and privacy functionality.

{{ ORGANIZATION }} uses automated CI/CD deployment pipelines ({{ CICD_PLATFORM }} / {{ IAC_TOOL }}), Git branch pull request protections, and Google Cloud Organization Policies to prevent and restrict unauthorized direct modifications to {{ SYSTEM_NAME }}.


## 5. Impact Analyses

Security impact analysis is the analysis conducted by qualified {{ ORGANIZATION }} staff to determine the extent to which changes to {{ ORGANIZATION }} {{ SYSTEM_NAME }} affect the security posture. Because {{ ORGANIZATION }} {{ SYSTEM_NAME }} is typically in a constant state of change, it is important to understand the impact of changes on the functionality of existing security controls and in the context of organizational risk tolerance. Security impact analysis is incorporated in the configuration change control process.

The security impact analysis of a change occurs when changes are analyzed and evaluated for adverse impact on security, preferably before they are approved and implemented, but also in the case of emergency/unscheduled changes. Once the changes are implemented and tested, a security impact analysis (and/or assessment) is performed to ensure that the changes have been implemented as approved, and to determine if there are any unanticipated effects of the change on existing security controls.

The process for a security impact analysis consists of the following steps:


## 6. Understand the Change

If the change is being proposed, develop a high-level architecture overview which shows how the change will be implemented. If the change has already occurred (unscheduled/unauthorized), request follow-up documentation/information and review it or use whatever information is available such as audit records or interview staff who made the change, to gain insight into the change.


## 7. Identify Vulnerabilities

If the change involves a hardware or software product, identify vulnerabilities. {{ ORGANIZATION }} uses this information to address known issues and remove or mitigate them before they become a concern. {{ ORGANIZATION }} {{ SYSTEM_NAME }} uses automated vulnerability scanning tools to search public vulnerability databases that apply to IT products. If the change involves custom development, a more in-depth analysis of the security impact is conducted.


## 8. Assess Risks

Once a vulnerability has been identified, a risk assessment is needed to identify the likelihood of a threat exercising the vulnerability and the impact of such an event. Although vulnerabilities may be identified in changes as they are proposed, built, and tested, the assessed risk may be low enough that the risk can be accepted without remediation. In other cases, the risk may be high enough that the change is not approved, or that safeguards and countermeasures are implemented to reduce the risk.


## 9. Assess Impact on Existing Security Controls

In addition to assessing the risk from the change, {{ ORGANIZATION }} analyzes whether and how a change will affect existing security controls. Determine whether the change may involve installation of software that alters the existing baseline configuration, or whether the change itself may cause or require changes to the existing baseline configuration. The change may also affect other systems or system components that depend on the function or component being changed, either temporarily or permanently.


## 10. Plan Safeguards and Countermeasures

Where identified risks are unacceptable, {{ ORGANIZATION }} uses the security impact analysis to revise the change or to plan safeguards and countermeasures to reduce the risk. If the security impact analysis shows that the proposed change modifies a common secure configuration setting, the change is reworked to function within the existing setting. If a change involves new elevated privileges for users, a plan to mitigate the additional risk is made.


### 10.1 Separate Test Environments

{{ ORGANIZATION }} uses a separate test environment to analyze changes to {{ SYSTEM_NAME }} before implementation in production.


### 10.2 Verification of Controls

Implementation in this context refers to installing changed code in the operational system that may have an impact on security or privacy controls. After {{ ORGANIZATION }} implements changes to {{ SYSTEM_NAME }}, impacted controls are verified to ensure they are implemented correctly, operating as intended, and producing the desired outcome.


## 11. Access Restrictions for Change

The {{ SYSTEM_NAME }} code base is written in Terraform and version-controlled in Git. All changes to the code base go through a merge/pull request review process, which prevents arbitrary modification of the core IaC. Code changes are not reflected in the infrastructure until the code is deployed through Terraform. After deployment, out-of-band changes (e.g., a privileged user modifying the infrastructure through the Google Cloud console) are technically possible but cause the deployed configuration to drift from the approved baseline. {{ ORGANIZATION }} requires that all changes to the infrastructure be made through the merge/pull request review process.

Physical access restrictions associated with changes to the Google Cloud infrastructure that hosts {{ SYSTEM_NAME }} are documented in the Google Services Configuration Management Plan and inherited by {{ ORGANIZATION }}.

{{ ORGANIZATION }} {{ SYSTEM_NAME }} is a cloud-based system in which {{ ORGANIZATION }} personnel have no physical access restriction requirements.

{{ ORGANIZATION }} defines and documents the logical access restrictions associated with changes to {{ SYSTEM_NAME }}. {{ ORGANIZATION }} {{ SYSTEM_NAME }} IT assets are restricted to authorized privileged users, and an audit trail of logical access to the system is maintained.


### 11.1 Automated Access Enforcement and Audit Records

{{ ORGANIZATION }} uses Google Cloud Logging aggregated organization sinks exporting to immutable Cloud Storage buckets and BigQuery Log Sinks as the central repository for all organizational audit logs and configuration change audit trails.

{{ ORGANIZATION }} logs system access associated with applying configuration changes, to verify that configuration change control is followed and to support after-the-fact actions if unauthorized changes are discovered.


### 11.2 Privilege Limitation for Production and Operation

Access control policies control access between active entities or subjects and passive entities or objects in {{ ORGANIZATION }} {{ SYSTEM_NAME }}.

{{ ORGANIZATION }} is responsible for adding users to the provided {{ SYSTEM_NAME }} roles for access.

{{ ORGANIZATION }} is responsible for all aspects of access control for {{ SYSTEM_NAME }} users.

For all {{ ORGANIZATION }} users, access to logical resources is documented through the user access request workflow (`[WARNING: RMF TEAM ACTION REQUIRED: Account Creation Request Form / GRC Ticket]`). Access to resources is enforced using Google Cloud Identity and Google Cloud IAM.

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

{{ ORGANIZATION }} uses automated Terraform plan/apply CI/CD pipelines, Google Cloud Policy Intelligence, and Google Cloud Asset Inventory to automate the management, application, and continuous verification of baseline configuration settings in {{ SYSTEM_NAME }}.


### 12.2 Respond to Unauthorized Changes

Responses to unauthorized changes to configuration settings include alerting designated personnel, restoring established configuration settings, or halting affected system processing.

If {{ ORGANIZATION }} determines that an unauthorized change has been made to {{ SYSTEM_NAME }}, the following steps take place:

- Automated rollback of IaC state via Terraform apply

- Quarantine or isolation of the affected Google Cloud resource or VPC network

- Immediate high-priority alert via {{ TELEMETRY_PIPELINE }} to {{ EXTERNAL_SIEM }} / {{ CSSP_PROVIDER }} incident dispatch queues

- Root-cause security investigation and incident report


## 13. Least Functionality

All {{ ORGANIZATION }} {{ SYSTEM_NAME }} components are configured to provide the least functionality possible. Cloud IAM grants each user only the capabilities needed to perform the functions of an assigned role. {{ ORGANIZATION }} documents the essential capabilities that the system must provide and the prohibited or restricted functions, ports, protocols, and services, in accordance with the configuration guidance in Section 12.

{{ ORGANIZATION }} uses Google Cloud Asset Inventory, {{ TELEMETRY_PIPELINE }}, and {{ THREAT_DETECTION_ENGINE }} to scan networks, {{ INTRUSION_DETECTION_SYSTEM }} for intrusion detection and prevention, and {{ EDR_SOLUTION }} for endpoint protection.


### 13.1 Periodic Review

{{ ORGANIZATION }} reviews the functions, ports, protocols, and services on {{ SYSTEM_NAME }} at least annually through a Ports, Protocols, and Services Management (PPSM) audit, and checks open ports quarterly through vulnerability scan port reviews. {{ ORGANIZATION }} disables or removes functions, ports, protocols, and services identified as unnecessary or nonsecure within 30 calendar days.


### 13.2 Prevent Program Execution

Prevention of program execution addresses {{ ORGANIZATION }} policies, rules of behavior, and/or access agreements that restrict software usage and the terms and conditions imposed by the developer or manufacturer, including software licensing and copyrights. Restrictions include prohibiting auto-execute features, restricting roles allowed to approve program execution, permitting or prohibiting specific software programs, or restricting the number of program instances executed at the same time.

All program execution within {{ SYSTEM_NAME }} occurs through managed services. Each service has IAM profiles and policies that strictly control the execution rights and privileges assigned to it.


### 13.3 Registration Compliance

{{ ORGANIZATION }} registers the ports, protocols, and services used by {{ SYSTEM_NAME }} in the DoD PPSM Central Registry in accordance with DoD Instruction 8551.01, "Ports, Protocols, and Services Management (PPSM)."


### 13.4 Authorized Software - Allow-by-Exception

{{ ORGANIZATION }} employs an allow-by-exception policy for {{ SYSTEM_NAME }}. The list of authorized software is reviewed and updated at least quarterly and when there is a change.


### 13.5 Binary or Machine Executable Code

> [!IMPORTANT]
> [WARNING: RMF TEAM ACTION REQUIRED: Verify and update operational contact/procedure details in this section.]
> Binary or machine executable code applies to all sources of binary or machine-executable code, including commercial software and firmware and open-source software. {{ ORGANIZATION }} prohibits the use of binary or machine-executable code from sources with limited or no warranty or without the provision of source code. {{ ORGANIZATION }} allows exceptions only for compelling mission or operational requirements with the approval of the authorizing official.


### 13.6 Prohibiting the Use of Unauthorized Hardware

Hardware components provide the foundation for the systems and the platform for the execution of authorized software programs. {{ ORGANIZATION }} manages the inventory of hardware components and controls which hardware components are permitted to be installed in or connected to {{ SYSTEM_NAME }}.

{{ ORGANIZATION }} prohibits the use or connection of unauthorized hardware components, and reviews and updates the list of authorized hardware components at least annually.


## 14. System Component Inventory

System components are discrete, identifiable information technology assets that include hardware, software, and firmware. {{ ORGANIZATION }} uses dynamic build extraction tooling (`extract_system_data.py`), `system_inventory.json`, and Google Cloud Asset Inventory exports as a centralized location for component inventory for {{ SYSTEM_NAME }}. In addition to Cloud Asset Inventory, the automated `Hardware_Software_Inventory.yaml` list and authorization boundary diagram provide an active overview of system components.

{{ ORGANIZATION }} reviews and updates `system_inventory.json`, the `Hardware_Software_Inventory.yaml` list, and authorization boundary diagrams continuously upon build release, and at least annually.


### 14.1 Updates During Installation and Removal

{{ ORGANIZATION }} shall maintain the accuracy, completeness, and consistency of system component inventories. Inventories shall be updated as part of component installations or removals or during general system updates.


### 14.2 Automated Maintenance

{{ ORGANIZATION }} uses automated build extraction scripts (`extract_system_data.py`) and Google Cloud Asset Inventory exports to maintain an up-to-date, complete, accurate, and readily available inventory of system components.


### 14.3 Automated Unauthorized Component Detection

{{ ORGANIZATION }} uses Google Cloud Asset Inventory continuous feed alerts, {{ TELEMETRY_PIPELINE }} into {{ EXTERNAL_SIEM }}, and Terraform Plan checks to detect unauthorized components or drift on {{ SYSTEM_NAME }}.


### 14.4 Accountability Information

Identifying individuals who are responsible and accountable for administering {{ SYSTEM_NAME }} components ensures that the assigned components are properly administered and that {{ ORGANIZATION }} can contact those individuals if action is required.

{{ ORGANIZATION }} uses code-repository CODEOWNERS mappings and `compliance_config.yaml` role assignments to identify individuals responsible and accountable for {{ SYSTEM_NAME }} components.


## 15. Software Usage Restrictions

All software contained within {{ ORGANIZATION }} systems must be correctly licensed. {{ ORGANIZATION }} authorizes the use of Commercial Off-the-shelf (COTS) software, Government Off-the-shelf (GOTS) software, and vetted and approved Open-Source Software (OSS). {{ ORGANIZATION }} {{ SYSTEM_NAME }} uses enterprise licensing where available.


### 15.1 Open-Source Software

Open-source software refers to software that is available in source code form. Certain software rights normally reserved for copyright holders are routinely provided under software license agreements that permit individuals to study, change, and improve the software. From a security perspective, the major advantage of open-source software is that it lets {{ ORGANIZATION }} examine the source code. Remediating vulnerabilities in open-source software can be difficult.

{{ ORGANIZATION }} has established the following restrictions when using open-source software:

- Open-source software (OSS) must be sourced only from verified upstream Google Cloud open-source templates or curated enterprise artifact registries (`SA-4`).
- All open-source container images and software dependencies must pass automated vulnerability scanning (Container Analysis / Software Composition Analysis) with zero unresolved Critical or High CVEs (`RA-5`, `SI-2`).
- Open-source software licenses must comply with agency legal counsel licensing terms (permissible Apache 2.0/MIT/BSD vs restricted AGPL) (`SA-4`).


## 16. User-installed Software

Only privileged users and the CI/CD deployment service account can install software on {{ SYSTEM_NAME }}. Developers cannot install software directly; they propose software changes through pull requests, which the CI/CD pipeline deploys after approval.

The following user types can install software on {{ SYSTEM_NAME }} or propose its installation:


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

- Identify and document the users who have access to {{ SYSTEM_NAME }} and its system components where the information is processed and stored; and

- Document changes to the location where the information is processed and stored.


### 17.1 Automated Tools to Support Information Location

The use of automated tools helps to increase the effectiveness and efficiency of the information location capability implemented within {{ SYSTEM_NAME }}. The output of automated information location tools can be used to guide and inform system architecture and design decisions.

{{ ORGANIZATION }} uses Google Cloud Asset Inventory metadata, Cloud KMS resource region constraints, and Google Cloud Sensitive Data Protection (Cloud DLP) automated inspection jobs to ensure controls are in place to protect {{ ORGANIZATION }} information and individual privacy.


## 18. Signed Components

Software and firmware components prevented from installation unless signed with recognized and approved certificates include software and firmware version updates, patches, service packs, device drivers, and basic input/output system updates.

{{ ORGANIZATION }} prevents the installation of software and firmware without verification that the component has been digitally signed using a certificate that is recognized and approved by {{ ORGANIZATION }}.


## 19. Data Action Mapping

Data actions are system operations that process personally identifiable information (PII) across the information life cycle, including collection, generation, transformation, use, disclosure, retention, and disposal. {{ ORGANIZATION }} develops and documents a map of the data actions that {{ SYSTEM_NAME }} performs on PII and maintains it with the System Security Plan data flow and data mapping documentation. Changes that alter how {{ SYSTEM_NAME }} processes PII go through the CCB, which includes privacy representatives (Section 4.3), and the map is updated with the change.

[CONFIG_REQUIRED: Location and owner of the {{ SYSTEM_NAME }} data action map]



## Appendix A – Detailed Compliance Matrix

The following table provides detailed traceability between the policy implementation statements in this document, the authoritative NIST SP 800-53 Rev. 5 control requirements, DoD CCIs, and the technical/governance enforcement mechanisms active across {{ SYSTEM_NAME }}.


| CTRL ID | CTRLTITLE | REQUIRED {{ GRC_STANDARD_LABEL }} STANDARD | DOCREF | ENFORCEMENT MECHANISM |
| :--- | :--- | :--- | :--- | :--- |
| CM-01 | Policy and Procedures | Develop, document, and disseminate to all stakeholders the CM policy and procedures; designate the ISSM to manage them; review and update them at least annually and following significant system changes, security or privacy incidents, assessment or audit findings, or changes in applicable laws, regulations, or guidance. (CCI-000286, CCI-000287, CCI-000289, CCI-000290, CCI-000292, CCI-001584, CCI-001821, CCI-001822, CCI-001824, CCI-001825, CCI-003897, CCI-003898, CCI-003899, CCI-003900, CCI-003901, CCI-003902, CCI-003903, CCI-003904, CCI-003905, CCI-003906, CCI-003907, CCI-003908) | Section 1 & 2 | Formal annual review workflow managed by the {{ ORGANIZATION }} ISSM with CCB and SO input; published in governance repository; event-driven triggers. |
| CM-02 | Baseline Configuration | Develop, document, and maintain under configuration control a baseline configuration; review annually, after major updates, and upon STIG releases. (CCI-000295, CCI-000296, CCI-000297, CCI-001497, CCI-001585, CCI-003909, CCI-003910) | Section 3 | Git repository version-controlled Terraform code; System Security Plan architecture models; annual baseline audits. |
| CM-02(02) | Automation Support for Accuracy and Currency | Employ automated mechanisms (SCAP, HBSS, Terraform, Cloud Asset Inventory) to maintain currency and accuracy of baseline configurations. (CCI-000300, CCI-000301, CCI-000302, CCI-000303, CCI-003911) | Section 3.1 | Automated Terraform state in GCS; Cloud Asset Inventory continuous discovery feeds; SCAP/Checkov compliance scans. |
| CM-02(03) | Retention of Previous Configurations | Retain at least two (2) previous versions of approved baseline configurations to support immediate operational rollback. (CCI-000304, CCI-001736) | Section 3.2 | Git version control tag history; GCS bucket object versioning on Terraform state files; container image registry tags. |
| CM-02(07) | Configure Systems and Components for High-risk Areas | Enforce hardened configuration, inspection, and zero-trust controls for endpoints accessing the system from high-risk environments. (CCI-001737, CCI-001738, CCI-001739, CCI-001815, CCI-001816) | Section 3.3 | Managed virtual desktops / secure bastion hosts; {{ MFA_MECHANISM }}; boundary traffic inspection gateways. |
| CM-03 | Configuration Change Control | Formally request, evaluate, test, and approve all configuration changes; convene CCB at least monthly; retain records for 1 year / 2 cycles. (CCI-000313, CCI-000314, CCI-000316, CCI-000318, CCI-000319, CCI-000320, CCI-000321, CCI-001586, CCI-001740, CCI-001741, CCI-001819, CCI-002056, CCI-003912) | Section 4 | {{ ORGANIZATION }} CCB charter; monthly CCB review meetings; version-control pull request change logs and approval histories. |
| CM-03(01) | Automated Documentation, Notification, and Prohibition of Changes | Use automated mechanisms to document, notify, approve, implement, and audit configuration changes to {{ SYSTEM_NAME }} components. (CCI-000322, CCI-000323, CCI-000324, CCI-000325, CCI-000326, CCI-001498, CCI-001742, CCI-002057, CCI-002058, CCI-003913, CCI-003914, CCI-003915, CCI-003916, CCI-003917, CCI-003918) | Section 3 | GitOps pull-request workflows, automated CI/CD Terraform plan/apply gates, mandatory peer/CCB approvals, and immutable audit trails. |
| CM-03(02) | Testing, Validation, and Documentation of Changes | Test and validate all changes in separate staging environments prior to production; maintain audit trails of test execution. (CCI-000327, CCI-000328, CCI-000329) | Section 4.2 | Automated CI/CD pipeline tests; deployment validation in dedicated development and test staging projects. |
| CM-03(04) | Security and Privacy Representatives | Mandate cybersecurity and privacy representatives as formal voting members of the Configuration Control Board (CCB). (CCI-000332, CCI-003921, CCI-003922, CCI-003923, CCI-003924) | Section 4.3 | CCB formal charter; voting sign-offs by the ISSM ({{ ISSM_NAME }}), the privacy representative, and the DevSecOps Lead. |
| CM-03(05) | Automated Security Response | Enforce automated security response requirements across {{ SYSTEM_NAME }} in accordance with NIST SP 800-53 Rev. 5 CM-3(5). (CCI-001743, CCI-001744) | Section 3 | Enforced via Google Cloud infrastructure controls, Terraform configuration baselines, and ISSM/ISSO governance verification. |
| CM-03(06) | Cryptography Management | Subject all controls and system components relying on cryptography to formal configuration management. (CCI-001745, CCI-001746) | Section 4.5 | Configuration control of Cloud KMS CMEK keyrings, transport MACsec keys, and virtual appliance IPsec parameters. |
| CM-03(07) | Review System Changes | Review system changes quarterly (for Moderate Integrity) and immediately post-incident to verify compliance with CCB authorizations. (CCI-003925, CCI-003926, CCI-003927) | Section 4.6 | Quarterly CCB audit reviews; automated CI/CD deployment log audits; post-incident configuration reconciliation. |
| CM-03(08) | Prevent or Restrict Configuration Changes | Prevent and restrict unauthorized direct modifications to production cloud infrastructure and configuration baselines. (CCI-003928, CCI-003929) | Section 4.7 | Git branch protections; Organization Policies; prohibition of manual Google Cloud Console edits in production. |
| CM-04 | Impact Analyses | Conduct Security Impact Analysis (SIA) before implementing changes to evaluate security posture and control effects. (CCI-000333, CCI-003930) | Section 5 - 10 | Formal 5-step SIA methodology; pre-merge automated security scans; ISSM security risk evaluation sign-offs. |
| CM-04(01) | Separate Test Environments | Maintain separate test/development environments physically and logically isolated from the operational production system. (CCI-001817, CCI-001818, CCI-003931) | Section 10.1 | Hard project boundaries for Dev (*-d) and Test (*-t) environments; separate KMS encryption keys and state buckets. |
| CM-04(02) | Verification of Controls | Verify that all impacted security and privacy controls operate effectively and as intended following production implementation. (CCI-000335, CCI-000336, CCI-000337, CCI-003932, CCI-003933, CCI-003934) | Section 10.2 | Post-deployment automated CI/CD validation test suites; ISSO operational security control verification audits. |
| CM-05 | Access Restrictions for Change | Define and enforce logical access restrictions governing authorization to propose, approve, and execute system changes. (CCI-000340, CCI-000341, CCI-000344, CCI-000345, CCI-003935, CCI-003936) | Section 11 | Git repository branch protections; CODEOWNERS approval gating; prohibition of manual out-of-band console changes. |
| CM-05(01) | Automated Access Enforcement and Audit Records | Enforce access restrictions via automated GitOps mechanisms and maintain complete audit trails of all configuration change events. (CCI-001813, CCI-003937, CCI-003938) | Section 11.1 | Version-control ACLs; Cloud Audit Logs capturing all deployment API calls; real-time Pub/Sub streaming to SIEM. |
| CM-05(05) | Privilege Limitation for Production and Operation | Deny human production change rights; execute deployments via keyless WIF service accounts; review privileges at least annually. (CCI-001753, CCI-001754, CCI-003939, CCI-003940) | Section 11.2 | Automated CI/CD deployment service accounts executing via WIF OIDC; annual CCB privilege re-evaluation audits. |
| CM-05(06) | Limit Library Privileges | Restrict privileges to modify shared software libraries, Terraform modules, and container registries to authorized DevSecOps leads. (CCI-001499) | Section 11.3 | Google Artifact Registry IAM permissions; protected Terraform module repositories with restricted write access. |
| CM-06 | Configuration Settings | Establish and enforce mandatory configuration settings based on DISA STIGs/SRGs, CIS Benchmarks; require AO approval for deviations. (CCI-000366, CCI-000367, CCI-000368, CCI-000369, CCI-001755, CCI-001756, CCI-003941, CCI-003942, CCI-003943, CCI-003944, CCI-003945, CCI-003946) | Section 12 | DISA STIG compliance baselines; Google Cloud Organization Policies; formal AO Exception to Policy (ETP) workflows. |
| CM-06(01) | Automated Management, Application, and Verification | Manage, apply, and verify configuration settings across all components using automated tools (HBSS, GPO, Terraform, Org Policies). (CCI-000370, CCI-000371, CCI-000372, CCI-002059, CCI-003947) | Section 12.1 | Organization Policy constraints (vmExternalIpAccess, publicAccessPrevention); Terraform CI/CD posture enforcement. |
| CM-06(02) | Respond to Unauthorized Changes | Respond to unauthorized configuration changes by alerting personnel, isolating resources, and rolling back to approved baselines. (CCI-001757, CCI-001758, CCI-001759) | Section 12.2 | Real-time alerts via Cloud Logging export sinks to external accredited CSSP/SIEM and Cloud Monitoring (or SCC Event Threat alerts in FedRAMP High / Commercial enclaves); automated Terraform apply rollback triggers; VPC quarantine rules. |
| CM-07 | Least Functionality | Configure system to provide only mission-essential capabilities; prohibit unnecessary ports, protocols, functions, and services. (CCI-000380, CCI-000381, CCI-000382, CCI-003948) | Section 13 | Removal of unused OS packages; strict VPC firewall ingress/egress rules; least functionality IAM permissions. |
| CM-07(01) | Periodic Review | Review system functions, ports, protocols, and services at least annually, with quarterly port reviews; disable or remove unnecessary or nonsecure items within 30 days. (CCI-000384, CCI-001760, CCI-001761, CCI-001762) | Section 13.1 | Annual PPSM audits; quarterly vulnerability scan port reviews; automated disablement of unapproved services. |
| CM-07(02) | Prevent Program Execution | Prevent unauthorized program execution adhering to software usage rules, licensing terms, and application execution controls. (CCI-001592, CCI-001763, CCI-001764) | Section 13.2 | AppLocker / Linux STIG application allowlisting; Google Cloud Binary Authorization on serverless containers. |
| CM-07(03) | Registration Compliance | Ensure all network ports, protocols, and services comply with and are registered under DoDI 8551.01 (PPSM). (CCI-000387, CCI-000388) | Section 13.3 | Formal registration in DoD PPSM Central Registry; automated verification against registered PPSM category codes. |
| CM-07(05) | Authorized Software — Allow-by-exception | Enforce an allow-by-exception software policy; review and update the Authorized Software List at least quarterly. (CCI-001772, CCI-001773, CCI-001774, CCI-001775, CCI-001777) | Section 13.4 | CCB-approved Authorized Software List; Google Artifact Registry curated base images; quarterly software reviews. |
| CM-07(08) | Binary or Machine Executable Code | Prohibit the use of unverified binary/executable code lacking source code transparency or warranty; require AO approval for exceptions. (CCI-003955, CCI-003956) | Section 13.5 | Pre-merge source code verification; container provenance scanning; ban on unverified third-party binaries. |
| CM-07(09) | Prohibiting The Use of Unauthorized Hardware | Prohibit unauthorized hardware; permit only evaluated, approved hardware components; review hardware list annually. (CCI-003957, CCI-003958, CCI-003959, CCI-003960, CCI-003961) | Section 13.6 | Google Cloud Services P-ATO data center physical security; Google Titan chip hardware attestation; annual CCB hardware reviews. |
| CM-08 | System Component Inventory | Maintain a complete inventory of all system components (hardware, software, cloud resources); review/update continuously. (CCI-000398, CCI-001779, CCI-001780, CCI-003962, CCI-003963, CCI-003964, CCI-003965, CCI-003966, CCI-003967) | Section 14 | Centralized system_inventory.json and Hardware_Software_Inventory.yaml artifacts; annual SSP inventory reconciliation. |
| CM-08(01) | Updates During Installation and Removal | Update system component inventories automatically as part of component installation, modification, or removal. (CCI-000408, CCI-000409, CCI-000410) | Section 14.1 | Automated CI/CD build extraction scripts (extract_system_data.py); dynamic Cloud Asset Inventory sync. |
| CM-08(02) | Automated Maintenance | Employ automated mechanisms (ACAS, HBSS, Cloud Asset Inventory) to maintain inventory currency, accuracy, and completeness. (CCI-000411, CCI-000412, CCI-000413, CCI-000414, CCI-003968) | Section 14.2 | Google Cloud Asset Inventory continuous discovery feeds; ACAS network asset scans; CMDB aggregation. |
| CM-08(03) | Automated Unauthorized Component Detection | Continuously detect unauthorized components via automated tools; isolate components and notify ISSM/ISSO via {{ ODP_CM_8_3_DETECTION_DELAY }}. (CCI-000415, CCI-000416, CCI-001783, CCI-001784, CCI-003969) | Section 14.3 | Real-time Cloud Asset Inventory drift feeds; Cloud Logging Log Router alerts to external CSSP/SIEM (or SCC alerts in FedRAMP High / Commercial enclaves); automated network quarantine rules. |
| CM-08(04) | Accountability Information | Include in the system component inventory the organizational position or role responsible for administering and maintaining each component. (CCI-000418) | Section 8 | Mandatory Terraform resource labels (owner, admin-role, cost-center, system-id) and Cloud Asset Inventory accountability mappings. |
| CM-08(07) | Centralized Repository | Maintain a centralized, integrated repository for all component inventory and configuration baseline records. (CCI-001785) | Section 14 | Centralized Git repository linked with eMASS and CMDB; integrated configuration traceability databases. |
| CM-09 | Configuration Management Plan | Develop, document, and implement a Configuration Management Plan; review and approve by AO, SO, and ISSM at least annually. (CCI-000423, CCI-000426, CCI-001792, CCI-001795, CCI-001798, CCI-001799, CCI-001801, CCI-003971, CCI-003972, CCI-003973, CCI-003974, CCI-003975, CCI-003976, CCI-003977, CCI-003978, CCI-003979) | Section 2.3 | Formally approved {{ SYSTEM_NAME }} Configuration Management Plan (CMP); annual AO/SO/ISSM re-certification workflows. |
| CM-10 | Software Usage Restrictions | Enforce compliance with software licenses, copyright agreements, and usage restrictions across all system components. (CCI-001726, CCI-001727, CCI-001728, CCI-001729, CCI-001730, CCI-001731, CCI-001732, CCI-001733, CCI-001802, CCI-001803) | Section 15 | Enterprise software license tracking; automated container dependency auditing in CI/CD pipelines. |
| CM-10(01) | Open-source Software | Govern open-source software usage per DoD 2022 Memo; mandate Software Bill of Materials (SBOM) and vulnerability vetting. (CCI-001734, CCI-001735) | Section 15.1 | Automated SBOM generation (Syft/Trivy); Container Analysis vulnerability screening; Artifact Registry curation. |
| CM-11 | User-installed Software | Strictly prohibit user-installed software; enforce via removal of admin rights, application allowlisting, and continuous monitoring. (CCI-001804, CCI-001805, CCI-001806, CCI-001807, CCI-001808, CCI-001809) | Section 16 | Non-root container runtime execution; removal of administrative rights on bastions; Endpoint Security monitoring. |
| CM-11(02) | Software Installation with Privileged Status | Restrict software installation privileges strictly to authorized system administrators executing CCB-approved changes. (CCI-003980) | Section 16 | Dedicated administrative role bindings; mandatory CCB change authorization gating for software deployment. |
| CM-12 | Information Location | Identify and document exact geographic and logical locations of {{ SENSITIVITY_CLASSIFICATION }}, {{ IMPACT_LEVEL }} data, and system components; document all location changes. (CCI-003982, CCI-003983, CCI-003984, CCI-003985, CCI-003986, CCI-003987) | Section 17 | Cloud KMS US-only region constraints; VPC subnet location documentation; System Security Plan data mapping. |
| CM-12(01) | Automated Tools to Support Information Location | Deploy automated tools (Cloud DLP, Cloud Asset Inventory) to identify and track {{ SENSITIVITY_CLASSIFICATION }}, PII, and mission data across components. (CCI-003988, CCI-003989, CCI-003990) | Section 17.1 | Google Cloud Sensitive Data Protection automated discovery jobs; BigQuery column-level metadata tagging. |
| CM-13 | Data Action Mapping | Develop and document a map of system data actions to track how personally identifiable information and mission data are collected, processed, stored, and transmitted across system components. (CCI-003991) | Section 19 | Data flow diagrams and data action mapping in the SSP, PIA, and `system_inventory.json`. |
| CM-14 | Signed Components | Prevent the installation of software, container images, patches, or firmware unless digitally signed using approved {{ PKI_TRUST_TYPE }} certificates. (CCI-003992, CCI-003993) | Section 18 | Google Cloud Binary Authorization; cryptographic container image signature validation (cosign); PKI driver checks. |
