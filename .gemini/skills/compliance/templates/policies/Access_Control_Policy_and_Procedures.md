# AC - Access Control Policy and Procedures

## Document Governance & Approval Baseline

| Governance Metric | Policy Standard & Specification |
| :--- | :--- |
| **Document Title** | Access Control Policy and Procedures |
| **NIST Control Family** | Access Control (AC) |
| **Primary NIST Benchmark** | NIST SP 800-53 Rev. 5 (AC Family), NIST SP 800-63B (Digital Identity Guidelines) |
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
> This document defines the enterprise security policy and implementation procedures for **Access Control** under **NIST SP 800-53 Rev. 5 (AC)**.
> Technical infrastructure controls are automatically provisioned and enforced via **{{ SYSTEM_NAME }}** Terraform blueprints.
> Operational rules or contact details requiring manual confirmation are highlighted with RMF Team Callouts.


## 1. Overview

This document establishes a common policy for the effective implementation of selected NIST SP 800-53rev5 “Security and Privacy Controls for Federal Information Systems and Organizations” controls and control enhancements in the Access Control (AC) family to be applied, as required. The risk management strategy is an important factor in establishing such policies and procedures, as they contribute to security and privacy assurance. These policies reflect applicable federal laws, Executive Orders, directives, regulations, policies, standards, and guidance. The Access control policies are high-level requirements that specify how access is managed and who may access information under what circumstances.

The purpose of this document is the establishment of a common policy for the implementation of security controls to protect the confidentiality, integrity, and availability of the applicable systems and its information, and to manage information security risk across {{ ORGANIZATION }}.

This policy covers all {{ ORGANIZATION }} information and information systems to include those used, managed, or operated by a contractor, or other organizations on behalf of {{ ORGANIZATION }}. This policy applies to all {{ ORGANIZATION }} employees, contractors, and all other users of {{ ORGANIZATION }} information and information systems that support the operation and assets of {{ ORGANIZATION }}.

> [!IMPORTANT]
> <mark style="background-color: #fff9c4; color: #b71c1c; font-weight: bold; padding: 2px 6px; border-radius: 4px;">RMF TEAM ACTION REQUIRED: Verify and update operational contact/procedure details in this section.</mark>
> The {{ ORGANIZATION }} ISSM shall ensure this policy is reviewed and updated annually, or as needed, and disseminated to {{ ORGANIZATION }} System Administrators, Information System Security Officers, Program Managers, and any relevant stakeholders.

This document complies with the following requirements from NIST Special Publication 800-53 Revision 5, "Security and Privacy Controls for Federal Information Systems and Organizations". A detailed compliance matrix can be found in Appendix A, “Detailed Compliance Matrix”.


## 2. Account Management

The following sections details how {{ ORGANIZATION }} manages user and system accounts.  For specific procedures of how to complete tasks, please see the {{ SYSTEM_NAME }} User Management Operational Instruction.

{{ SYSTEM_NAME }} implements roles in Identity and Access Management (IAM) that logically separate accesses. {{ ORGANIZATION }} is responsible for providing identities and assigning users to groups; this ensures {{ ORGANIZATION }} is managing WHO gets what network access, not HOW they get network access.

{{ ORGANIZATION }} is responsible for managing all aspects of Access Control for {{ SYSTEM_NAME }} users.

{{ ORGANIZATION }} is responsible for assigning account managers for accounts used within {{ SYSTEM_NAME }}.


### 2.1 Automated System Account Management

Automated system account management includes using automated mechanisms to: create, enable, modify, disable, and remove accounts; notify account managers when an account is created, enabled, modified, disabled, or removed, or when users are terminated or transferred; monitor system account usage, and report atypical system account usage.

{{ IDENTITY_ACCESS_IMPLEMENTATION }}

Google Cloud Identity / SSO is utilized across {{ SYSTEM_NAME }} for the support of identity and credential verification and access management. Automated account management enables consistent and accurate user credential information across all information systems.


### 2.2 System Account Management

{{ SYSTEM_NAME }} will follow established accepted system account management practices utilizing the user access request form (<mark style="background-color: #fff9c4; color: #b71c1c; font-weight: bold; padding: 1px 5px; border-radius: 3px;">RMF TEAM ACTION REQUIRED: Identity Request Form / GRC Ticket</mark>).  user access request form (<mark style="background-color: #fff9c4; color: #b71c1c; font-weight: bold; padding: 1px 5px; border-radius: 3px;">RMF TEAM ACTION REQUIRED: Identity Request Form / GRC Ticket</mark>) must be completed per account on each security domain within a given {{ ORGANIZATION }} system.  {{ ORGANIZATION }} systems may customize the approved user access request form (<mark style="background-color: #fff9c4; color: #b71c1c; font-weight: bold; padding: 1px 5px; border-radius: 3px;">RMF TEAM ACTION REQUIRED: Identity Request Form / GRC Ticket</mark>) template to combine security domains and consolidate paperwork more efficiently.

At a minimum, each {{ ORGANIZATION }} system will identify the personnel responsible for the management of system accounts that hold the following roles:

- {{ SYSTEM_NAME }} Program Manager

- {{ SYSTEM_NAME }} Information System Security Officer

> [!IMPORTANT]
> <mark style="background-color: #fff9c4; color: #b71c1c; font-weight: bold; padding: 2px 6px; border-radius: 4px;">RMF TEAM ACTION REQUIRED: Verify and update operational contact/procedure details in this section.</mark>
> Given the position of these roles and the necessity of open communication with them for a wide variety of purposes, contact information for these roles will be well communicated amongst each of the {{ ORGANIZATION }} systems for the purpose of facilitating system accounts.


#### 2.2.1 Account Authorization

{{ ORGANIZATION }} will authorize the accounts that are on {{ SYSTEM_NAME }}.  Records of these authorizations will be kept throughout the duration of a user’s employment.  {{ ORGANIZATION }} will utilize the euser access request form (<mark style="background-color: #fff9c4; color: #b71c1c; font-weight: bold; padding: 1px 5px; border-radius: 3px;">RMF TEAM ACTION REQUIRED: Identity Request Form / GRC Ticket</mark>) to approve access to {{ SYSTEM_NAME }} based on intended usage and missions/business functions.


**System Account Authorization**

Account Authorization must be performed initially and maintained on an ongoing basis.


**Group Authorization**

Security and distribution groups belong to the Role Based Access Control (RBAC) strategy for securing access and privileges to resources in {{ SYSTEM_NAME }}.

All security and/or distribution groups present within {{ SYSTEM_NAME }} must be approved prior to being created or used. The group purpose shall be detailed providing:

- Who will be members of the group, generally identified;

- What resources the security group will allow/restrict access to;

- What system or subsystem will the group support, for example, a payroll system.

An inventory list of the groups will be maintained containing information about the authorized groups present on {{ SYSTEM_NAME }}.  At a minimum, the following information will be contained in this inventory list:

- Name of Group;

- Date Authorized;

- Summary purpose;

- System implemented (AD, KeyCloak, CSP)

> [!IMPORTANT]
> <mark style="background-color: #fff9c4; color: #b71c1c; font-weight: bold; padding: 2px 6px; border-radius: 4px;">RMF TEAM ACTION REQUIRED: Verify and update operational contact/procedure details in this section.</mark>
> Unauthorized groups that are identified will be escalated to the respective {{ SYSTEM_NAME }} ISSO for investigation and potential execution of Incident Response procedures.  See Incident Response Policy.

The list of Groups is compared against current authorizations of Groups on file for traceability.  All {{ SYSTEM_NAME }} users must be authorized to be members of a specific group as documented on their user access request form (<mark style="background-color: #fff9c4; color: #b71c1c; font-weight: bold; padding: 1px 5px; border-radius: 3px;">RMF TEAM ACTION REQUIRED: Identity Request Form / GRC Ticket</mark>).


**Role Authorization**

A system role is a collection of responsibilities and tasks that are carried out by authorized individuals that use technology to meet those obligations.  Examples of roles can be as specific or vaguely define a group of people such as in a RACI matrix.  A role may need to belong to several groups to be able to complete their tasks and responsibilities.  Potentially, roles can be easily translated into job descriptions and if the need is deemed critical enough, the role can be filled with a Full or Part-time employee. Despite this easy translation, roles are not synonymous with job positions as a job position may hold a single or many roles.

{{ ORGANIZATION }} shall identify and maintain a list of roles critical to fulfill the mission of {{ SYSTEM_NAME }}, the groups that they shall be members of, and the requirements of fulfilling that role.  The list of Roles is compared against current authorizations of users/groups within Roles on file for traceability.  All {{ SYSTEM_NAME }} system users must be authorized to hold a specific role(s) as documented on their user access request form (<mark style="background-color: #fff9c4; color: #b71c1c; font-weight: bold; padding: 1px 5px; border-radius: 3px;">RMF TEAM ACTION REQUIRED: Identity Request Form / GRC Ticket</mark>).


**Access Authorization**

> [!IMPORTANT]
> <mark style="background-color: #fff9c4; color: #b71c1c; font-weight: bold; padding: 2px 6px; border-radius: 4px;">RMF TEAM ACTION REQUIRED: Verify and update operational contact/procedure details in this section.</mark>
> {{ ORGANIZATION }} must authorize access for their own user accounts.  For non-privileged accounts, this will be reflected by the electronic signature of the respective system ISSO on the user’s user access request form (<mark style="background-color: #fff9c4; color: #b71c1c; font-weight: bold; padding: 1px 5px; border-radius: 3px;">RMF TEAM ACTION REQUIRED: Identity Request Form / GRC Ticket</mark>) form.  For privileged accounts, the respective system's ISSM signature must also be obtained on the user’s user access request form (<mark style="background-color: #fff9c4; color: #b71c1c; font-weight: bold; padding: 1px 5px; border-radius: 3px;">RMF TEAM ACTION REQUIRED: Identity Request Form / GRC Ticket</mark>) form.

Regular audits of access authorizations will be reviewed once {{ SYSTEM_NAME }} comes into full operation and then on a regular basis thereafter to ensure that the access granted is reflected in writing. The process for determining the level of access for user accounts is the responsibility of {{ ORGANIZATION }}.  Logs shall be kept to provide for audits to ensure the process is not only established, but implemented and followed.


#### 2.2.2 Account Approval/Creation

> [!IMPORTANT]
> <mark style="background-color: #fff9c4; color: #b71c1c; font-weight: bold; padding: 2px 6px; border-radius: 4px;">RMF TEAM ACTION REQUIRED: Verify and update operational contact/procedure details in this section.</mark>
> Approval of an account is represented by the finalizing signature of ISSO and/or ISSM.  {{ SYSTEM_NAME }} ISSO/ISSM shall not apply their signature until they are certain that the needed information is complete, accurate and all steps in the identified process have been completed.  System Administrators may only create accounts that have the required ISSO/ISSM signatures on a completed user access request form (<mark style="background-color: #fff9c4; color: #b71c1c; font-weight: bold; padding: 1px 5px; border-radius: 3px;">RMF TEAM ACTION REQUIRED: Identity Request Form / GRC Ticket</mark>) and for which they are notified to proceed by the system ISSO/ISSM.


#### 2.2.3 Account Maintenance

{{ SYSTEM_NAME }} utilizes the user access request form (<mark style="background-color: #fff9c4; color: #b71c1c; font-weight: bold; padding: 1px 5px; border-radius: 3px;">RMF TEAM ACTION REQUIRED: Identity Request Form / GRC Ticket</mark>) Process for creating, enabling, modifying, and tracking system accounts.

{{ SYSTEM_NAME }} follows the Personnel Termination process contained in the {{ SYSTEM_NAME }} Personnel Security Plan for disabling and removing system accounts.


#### 2.2.4 Account Removal

When an account is no longer needed for any reason, it shall be removed to reduce the potential of compromise.  {{ ORGANIZATION }} will implement the process for account removal:

- User’s supervisor will notify the respective {{ SYSTEM_NAME }} ISSO or ISSM immediately upon receiving notice of departure or termination;

- Remove user from all groups on date of departure;

- If applicable, remove attributes or entitlements on date of departure;

- If applicable, change user’s password and that of any approved group accounts the user may have been knowledgeable of; and

- Disable account and retain for one calendar year.


### 2.3 Automated Temporary and Emergency Account Management

Management of temporary and emergency accounts includes the removal or disabling of such accounts automatically after 24 hours following task completion. {{ SYSTEM_NAME }} will address these account types as described in the following sections.


#### 2.3.1 Temporary Accounts

> [!IMPORTANT]
> <mark style="background-color: #fff9c4; color: #b71c1c; font-weight: bold; padding: 2px 6px; border-radius: 4px;">RMF TEAM ACTION REQUIRED: Verify and update operational contact/procedure details in this section.</mark>
> In a case after {{ SYSTEM_NAME }} becomes operational, it may be necessary to create an account for testing a new functionality.  {{ SYSTEM_NAME }} authorizes the creation of temporary accounts for testing or to support mission needs with the approval of the {{ SYSTEM_NAME }} ISSM, and applicable stakeholders being informed. These accounts will be identified as temporary in status by meeting the following criteria:

- Adding the “.tmp” identifier to the end of the username at the time of creating the account.  For example, “TempUser.tmp”;

- Disabled Temporary accounts will be reviewed and removed, at minimum, on a quarterly basis; and

- Temporary Accounts will have a/an user access request form (<mark style="background-color: #fff9c4; color: #b71c1c; font-weight: bold; padding: 1px 5px; border-radius: 3px;">RMF TEAM ACTION REQUIRED: Identity Request Form / GRC Ticket</mark>) completed and kept on file that documents the purpose of the account and system ISSM approval.


#### 2.3.2 Emergency Accounts

{{ SYSTEM_NAME }} authorizes the use of emergency accounts to ensure access to the system in the event primary accounts are unavailable to accomplish privileged tasks; they must remain under restrictive control.  The emergency account must be clearly defined as an emergency account.

> [!IMPORTANT]
> <mark style="background-color: #fff9c4; color: #b71c1c; font-weight: bold; padding: 2px 6px; border-radius: 4px;">RMF TEAM ACTION REQUIRED: Verify and update operational contact/procedure details in this section.</mark>
> Passwords for emergency accounts must be regularly changed and exceed the minimum length requirements set for administrator/root passwords.  See the IA policy “Password Based Authentication” requirements. Passwords, once set, will be printed, double sealed in two envelopes (one inside the other) and stored in a GSA approved safe; emergency account passwords must never be saved or stored electronically. Access to these passwords stored in a GSA approved safe must be with the permission of the {{ SYSTEM_NAME }} ISSO, ISSM, or onsite commanding officer/manager only with the latter providing immediate notification to the former. An access log recording the name of the user, the reason for access, which emergency account was accessed, and the approver must be stored with the sealed passwords. Upon completing the task in which the emergency accounts were accessed, notification to the {{ SYSTEM_NAME }} ISSO and/or ISSM must be made. The account shall then be disabled, a new password set, sealed and placed in the safe.

Emergency Accounts must not be removed from the systems but remain in an enabled state until needed.


### 2.4 Disable Accounts

{{ SYSTEM_NAME }} administrators are authorized to disable user or system accounts under the following conditions to support least privilege and least functionality in an effort to reduce the attack surface area of the respective system:

- The account has expired, {{ SYSTEM_NAME }} Cloud Identity will automatically disable the account;

- The account is no longer associated with a user or individual;

- Are in violation of {{ SYSTEM_NAME }} policy such as training and/or certification requirements for IA/Cyber Workforce, policy review/acknowledgements, or DoD 8140 (Directive, Manual, or Instruction) requirements for the specific position;

- Have become inactive on the network, have not logged on in 35 days; or

- The account poses a significant risk to the system or exhibits atypical usage as identified in the previous sections.

All user and temporary accounts are required to remain disabled until they are needed and then, once again, disabled upon task completion or the account is no longer needed.  Emergency Accounts must remain enabled until they are used and then disabled upon task completion until the password can be reset.


### 2.5 Inactive Accounts

Inactive accounts are those accounts that have not been logged into for over 35 calendar days.  {{ ORGANIZATION }} must review inactive accounts regularly and either automatically or manually disable inactive accounts on {{ SYSTEM_NAME }}.  Examples of when an account may become inactive include:

- A user has transferred to another system

- A user has been terminated

- A user has changed job roles or functions within the same system

- A user has left on vacation, bereavement, FMLA or other time off associated leave without coordinating with the cyber team


### 2.6 Group Accounts

A Group Accounts is an account whereby the username and password for a given account is known by more than a single individual. Once logged on to the system, the actions taken by the user of the account are not attributable or traceable to that single individual because anyone who knows the username and password, has the token and knows the pin, etc. could have performed the actions.

{{ ORGANIZATION }} policy states that Group Accounts are not permitted, unless the following conditions are met:

- Documented operational necessity.

- {{ SYSTEM_NAME }} Owner approval

- {{ SYSTEM_NAME }} ISSM approval

- Notification, for situational awareness, to the {{ ORGANIZATION }} Cybersecurity Team to decide the level of monitoring required for the account.


### 2.7 Automated Audit Actions

{{ SYSTEM_NAME }} uses Google Cloud Logging to automatically handle all account actions (creation, modification, enabling, disabling, removal). {{ TELEMETRY_PIPELINE }} streams audit records via Pub/Sub to {{ SIEM_TOOL }} ({{ CSSP_PROVIDER }}) and centralized storage sinks.

{{ SIEM_TOOL }} shall have dashboards configured to review all account-related events.

{{ ORGANIZATION }} must monitor for the following account related events at a minimum:

- Account Creation

- Account Modification

- Account Enabling

- Account Disabling

- Account Removal


### 2.8 Inactivity Logout

{{ SYSTEM_NAME }} is configured to automatically logout users after an inactivity period of 15 minutes.

{{ SYSTEM_NAME }} users, at a minimum, shall logout of {{ SYSTEM_NAME }} upon completion of work on {{ SYSTEM_NAME }} or end of workday to prevent their session from being compromised and used in a manner inconsistent with the mission of {{ SYSTEM_NAME }}.


### 2.9 Disable Accounts for High-risk Individuals

{{ ORGANIZATION }} may identify users posing a significant risk through monitoring. These types of users may have a history of inappropriate behavior. In the event {{ ORGANIZATION }} identifies this user type, the following process will be followed at minimum:

- Have the account disabled immediately;

- Contact the System ISSO for incident response implementation;

- Ensure user does not have alternate accounts. If they exist, disable those accounts; and

- Notify {{ ORGANIZATION }} Cybersecurity Team for situational awareness.


### 2.10 Usage Conditions

Based on the separation of duty and the principle of the least privilege, multiple service accounts are used across the project.

Additional restrictions can be set to service accounts include:

- Disable automatic role grants to default service accounts*

- Disable service account creation

- Disable service account key creation*

- Disable service account key upload*

- Disable attachment of service accounts to resources in other projects

- Restrict removal of project liens when service accounts are used across projects

Note: Policies with (*) are recommended.


#### 2.10.1 Initial Service Account in Bootstrap Phase

A system administrator with an individual GCP account can run the bootstrap phase, or they can impersonate a service account to do so.

For the  individual account, it is recommended to be a member of the group gcp_org_admins as defined in the previous section, to ensure the required privileges are assigned.

To run the bootstrap phase using the service account, grant the following roles outside of Terraform:

- Organization Admin of the GCP Organization if the root node is the Organization itself.

- Organization Policy Admin of the GCP Organization, to manage organization policies.

- Billing Admin of the Billing Account, or at minimum the Billing User role, to create projects.

- Folder Creator, also to create folders and projects

- Access Context Manager Admin, to create VPC SC policies

- Assured Workloads Admin, to create assured workloads folders.

The minimum set of roles needed to run the bootstrap phase in a given assured workloads folder are:

- Organization Viewer, to query organization level resources.

- Organization Policy Admin, to manage organization policies.

- Billing User of the Billing Account, to create new projects.

- Folder Creator, also to create new folders and projects.

- Access Context Manager, to create VPC SC policies.

- Security Admin, to manage {{ THREAT_DETECTION_ENGINE }} and security events.


#### 2.10.2 IAM Roles

IAM bindings across {{ SYSTEM_NAME }} projects enforce the principle of least privilege and strict separation of duties; review the Technical Design Document and System Security Plan for the specific operational roles assigned.



### 2.11 Google Cloud Platform (GCP) Inherited Controls & Shared Responsibility Boundary

- **Google Inherited Controls**: Google Cloud Platform provides inherited physical access control (`PE-2`, `PE-3`), datacenter perimeter security, and underlying Borg container platform isolation (`AC-3`, `AC-4`). Google manages access control to physical servers, datacenter facilities, and cloud infrastructure control planes.
- **Customer Implementation Responsibilities**: {{ ORGANIZATION }} is responsible for configuring Identity and Access Management (IAM) policies (`AC-2`, `AC-6`), enforcing Principle of Least Privilege across service accounts, implementing Workforce Identity Federation / SAML SSO (`AC-2`), setting Access Context Manager VPC perimeters (`AC-3`), and performing quarterly IAM entitlement reviews.

## 3. Access Enforcement

{{ SYSTEM_NAME }} enforces approved authorizations for logical access to information and system resources in accordance with applicable access control policies through the following mechanisms:

- Identity and Access Management (IAM): Access is controlled via IAM policy, which is defined and enforced using Infrastructure-as-Code (IaC) and Google IAM. The IaC is reviewed and submitted using Terraform to ensure policy is properly implemented.

- Role-Based Access Control (RBAC): Security and distribution groups are utilized as part of the RBAC strategy to manage access and privileges to resources. All security and distribution groups are approved prior to creation or use.

- Least Privilege: Access is granted based on the principle of least privilege, ensuring users and services only have the minimum necessary access to perform their functions.

- Account Management Processes:

  - {{ ORGANIZATION }} is responsible for providing identities and assigning users to groups, managing who has access.

  - {{ SYSTEM_NAME }} account management follows established practices, including the use of user access request form (<mark style="background-color: #fff9c4; color: #b71c1c; font-weight: bold; padding: 1px 5px; border-radius: 3px;">RMF TEAM ACTION REQUIRED: Identity Request Form / GRC Ticket</mark>).

  - user access request form (<mark style="background-color: #fff9c4; color: #b71c1c; font-weight: bold; padding: 1px 5px; border-radius: 3px;">RMF TEAM ACTION REQUIRED: Identity Request Form / GRC Ticket</mark>) is used to authorize user access.

  - {{ SYSTEM_NAME }} uses automated mechanisms to manage accounts, including creation, modification, and removal.

  - Regular audits of access authorizations are conducted to ensure accuracy.

- Service Accounts:

  - Service accounts are defined for microservices and used by the CI/CD pipeline to execute Terraform code, adhering to the principle of least privilege.

  - Downloadable service account keys are disabled.

- Human Access Restrictions: Human access to cloud resources is restricted; direct human modification of resources is only permitted in tightly controlled development environments. Access is granted to groups, not individual users.


### 3.1 Logical Access Enforcement

For all {{ ORGANIZATION }}, access to logical resources shall be identified on the user access request form (<mark style="background-color: #fff9c4; color: #b71c1c; font-weight: bold; padding: 1px 5px; border-radius: 3px;">RMF TEAM ACTION REQUIRED: Identity Request Form / GRC Ticket</mark>).  Access to resources is enforced using Google Cloud IAM.

{{ SYSTEM_NAME }} must enforce approved authorizations for logical access to information and system resources in accordance with applicable access control policies.


### 3.2 Discretionary Access Control

{{ ORGANIZATION }} will define and document the discretionary access control the system is to enforce over subjects and objects before granting access to the system.


## 4. Information Flow Enforcement

{{ SYSTEM_NAME }} leverages Googles for encryption on all data communication channels that are used to transmit data between services.

Information flow control regulates where information travels within {{ SYSTEM_NAME }} without explicit regard to subsequent accesses to that information.  Information, once received by {{ SYSTEM_NAME }} will be viewed as internal information.  All information that crosses the authorization boundary to another entity is considered to be an external information flow.


### 4.1 Internal Information Flow

Internal to {{ SYSTEM_NAME }}, all information is permitted and authorized to flow freely under the following conditions:

- Information remains at the designated classification level;

- All users have a valid need to know, level of clearance;

  - If separation of users is required; information will be protected with access controls

- All information remains internal to {{ SYSTEM_NAME }}.

Approved authorizations are based on user access. If a user has a valid account on {{ SYSTEM_NAME }}, they are considered authorized to access the information required to perform their mission.


### 4.2 External Information Flow

External information flow leaves the authorization boundary of {{ SYSTEM_NAME }}.

External to {{ SYSTEM_NAME }}, all information is permitted and authorized to flow freely under the following conditions:

- Information remains at the same classification level;

- All users have the required level of clearance, a valid need to know;

  - if separation of users is required; information will be protected with access controls

- Ports, Protocols and Services must be identified in the architecture diagram

- Sensitive or classified information must be encrypted using NSA approved encryption prior to leaving the {{ SYSTEM_NAME }} boundary; and

- Any information containing credentials must be encrypted

Approved authorizations are based on user or system access. If a user has a valid account on {{ SYSTEM_NAME }}, they are considered authorized to access the information. If {{ SYSTEM_NAME }} interconnects with another trusted system, it is considered authorized.


## 5. Separation of Duties

Separation of duties addresses the potential for abuse of authorized privileges and helps to reduce the risk of malevolent activity without collusion. Separation of duties includes:

- Dividing mission functions and information system support functions among different individuals and/or roles;
- Conducting information system support functions with different individuals (e.g., system management, programming, configuration management, quality assurance and testing, and network security); and
- Ensuring security personnel administering access control functions do not also administer audit functions (`AC-6`).

{{ ORGANIZATION }} enforces the following Separation of Duties (SoD) role group matrix for {{ SYSTEM_NAME }}, dynamically provisioned based on deployed IAM structures and service account configurations:

{{ SEPARATION_OF_DUTIES_TABLE }}

{{ SYSTEM_NAME }} utilizes electronic account authorization forms for user account creation, designating the specific IAM group and role assigned to each user.

## 6. Least Privilege

{{ ORGANIZATION }} the user access request form (<mark style="background-color: #fff9c4; color: #b71c1c; font-weight: bold; padding: 1px 5px; border-radius: 3px;">RMF TEAM ACTION REQUIRED: Identity Request Form / GRC Ticket</mark>) and implements the concept of least privilege, allowing only authorized accesses for users (and processes acting on behalf of users) which are necessary to accomplish assigned tasks in accordance with mission and business functions.


### 6.1 Authorize Access to Security Functions

All privileged accounts will be strictly role based and will follow the user access request form (<mark style="background-color: #fff9c4; color: #b71c1c; font-weight: bold; padding: 1px 5px; border-radius: 3px;">RMF TEAM ACTION REQUIRED: Identity Request Form / GRC Ticket</mark>) process.  A user must prove that they meet the requirements necessary to support their position before an account can be authorized to be created on an {{ SYSTEM_NAME }}.

To include:

- Completed user access request form (<mark style="background-color: #fff9c4; color: #b71c1c; font-weight: bold; padding: 1px 5px; border-radius: 3px;">RMF TEAM ACTION REQUIRED: Identity Request Form / GRC Ticket</mark>)

- Comply with DoDI 8140.01 and DoDM 8570.01 certification requirements

- Complete annual DoD Cybersecurity Awareness Training

- Complete {{ ORGANIZATION }} Cybersecurity Training


### 6.2 Non-privileged Access for Non-security Functions

{{ ORGANIZATION }} requires that aligned systems enforce that all privileged users utilize non-privileged accounts, or roles, when accessing non-security functions.


#### 6.2.1 Prohibit non-privileged Users from Executing Privileged Functions

{{ SYSTEM_NAME }} must prevent non-privileged users from executing privileged functions to include disabling, circumventing, or altering implemented security safeguards/countermeasures. This will include requiring the use of non-privileged accounts when accessing non-security functions.

Privileged accounts are roles assigned to individuals that are responsible for performing certain security-relevant functions that ordinary users are not authorized to perform.  Privileged Accounts are necessary to maintain {{ SYSTEM_NAME }} and keep it in an operational condition. All privileged accounts shall follow the principle of least privilege in that administrator rights are only granted to the account for {{ SYSTEM_NAME }}. It shall only be used to accomplish the immediate task and nothing more.


#### 6.2.2 Privileged Access Control & Just-In-Time Elevation Procedures (`AC-6`, `AC-17`)

In accordance with NIST SP 800-53 Rev. 5 (`AC-6`, `AC-17`) and DISA STIG guidelines, {{ ORGANIZATION }} enforces strict privileged access control procedures across {{ SYSTEM_NAME }}:

1. **Dedicated Privileged Accounts**: Administrative tasks must never be performed using standard user accounts. Privileged users must use dedicated administrative accounts (e.g., `admin-username@{{ ORGANIZATION }}.com`) bound to Multi-Factor Authentication (MFA) via FIDO2 WebAuthn security keys (`IA-2`).
2. **Just-In-Time (JIT) Privileged Elevation**: Privileged access elevation for production GCP projects is granted on a temporary, Just-In-Time basis using GCP Access Approval and Privileged Access Manager (PAM). Access automatically expires after a maximum duration of **4 hours**.
3. **Command Logging & Session Auditing**: All privileged console actions, gcloud CLI commands, and IAM role modifications are logged in Cloud Audit Logs (`AU-2`) and routed to an immutable Cloud Logging sink (`AU-9`).
4. **Prohibition of Direct Root/Owner Access**: Direct use of Primitive Roles (e.g., `roles/owner`, `roles/editor`) is strictly prohibited in production. All administrative permissions must use fine-grained Custom IAM Roles enforcing Principle of Least Privilege (`AC-6`).


### 6.3 Privileged Accounts

{{ ORGANIZATION }} implements the concept of least privilege, allowing only authorized accesses for users which are necessary to accomplish assigned tasks in accordance with mission and business functions.

{{ ORGANIZATION }} restricts privileged accounts on {{ SYSTEM_NAME }} to those that are necessary and in line with least privilege.


### 6.4 Review of User Privileges

{{ ORGANIZATION }} documents the personnel or roles to whom privileged accounts are to be restricted.

In accordance with DoD Directive 8140.01 (and related DoDI 8140.02/DODM 8140.03) regarding the DoD Cyberspace Workforce Framework, all {{ ORGANIZATION }} systems will conduct regular review/auditing of privileged user accounts to ensure that the user in which the privileged account is associated with maintains the requirements on an annual basis.  Should a user fail to comply with any one of the requirements, their account will be disabled until the requirements are met. It is the user’s responsibility to maintain certifications and annual training requirements and provide the required copies of certificates of completion to {{ ORGANIZATION }} cybersecurity staff.

The audit must include a review of privileges the user has reconciled to what has been authorized by the user’s most recent user access request form (<mark style="background-color: #fff9c4; color: #b71c1c; font-weight: bold; padding: 1px 5px; border-radius: 3px;">RMF TEAM ACTION REQUIRED: Identity Request Form / GRC Ticket</mark>).  Deviations must be documented and corrected.

Audits must be completed on no less than a quarterly basis with records kept to meet authorization security controls.

In the event a review identifies incorrect privileges are assigned, the following process will be executed:

- Determine if privilege found was previously documented and authorized. If not, this may be an indication of unauthorized access and will immediately be reported to the ISSO.

- Review the assigned privilege and determine if it is still active. If not, disable.

- Ensure the end user or service with the current privilege still has a valid mission need for that privilege. If not, remove the privilege if there is not a valid mission need.


### 6.5 Privilege Levels for Code Execution

IAM Policy should be defined as Infrastructure-as-code (IaC) and enforced by code that’s reviewed and submitted using Terraform.

- Latitude will be given to development projects to accelerate the rate of development.

- No human should have permissions to create or modify cloud resources in User Acceptance Test (UAT) or Quality Assurance (QA) environments that immediately precede production in the Continuous Integration / Continuous Development (CI/CD) pipeline.

- No human should have permissions to create or modify cloud resources in production.

- The Cloud Resource Manager access required to execute Terraform code will be assigned to a unique service account.

  - This service account will only be used by the CI/CD pipeline for terraform apply actions.


### 6.6 Human access

- Access must be granted to groups, not individual users.

- Access will be granted based on a minimalized set of curated roles.


### 6.7 Machine access

- Individual Service Accounts will be defined for each microservice.

- Downloadable Service Account keys will not be used and their creation should be disabled by organization policy.

- Access will be granted based on the principle of least privilege, with only necessary functionality granted for the microservice.

- Disable automatic role grants to default service accounts (iam.automaticIamGrantsForDefaultServiceAccounts ) should be enabled as organization policy , this will remove the editor role from the default service accounts.


### 6.8 Log Use of Privileged Functions


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

{{ ORGANIZATION }} will enable the audit capability for the execution of privileged functions on {{ SYSTEM_NAME }}. {{ SIEM_TOOL }} ({{ CSSP_PROVIDER }}) will ingest audit records via {{ TELEMETRY_PIPELINE }} and Pub/Sub.


## 7. Unsuccessful Logon Attempts

This control requires a limit of three consecutive invalid logon attempts by a user within 15 minutes. The Google Security Team limits invalid logon attempts to 30 attempts during a 3 hour period for single-factor authentication. In order to access the production environment a user must authenticate using the Single Sign-On service. Single Sign-On requires a username, password, and second factor authenticator. Single Sign-On will lock an account after 30 attempts during a 3 hour period. Users are locked out for 24 hours, until unlocked by TechStop or until they unlock using a self-service option which requires multi-factor authentication.

The main focus of this control is to prevent brute force attacks against accounts authenticated using usernames and passwords. Google has implemented stronger authentication mechanisms including username, passwords, and the required use of a second factor authenticator throughout the Google infrastructure. Google considers the risk between three consecutive logon attempts within 15 minutes (maximum 12 per hour) and 30 consecutive attempts within 3 hours (maximum 10 per hour) to be minimal and mitigated by the longer timeout period. Additionally, Google recognizes account lockouts after three failed logon attempts as an increased risk to the availability of the system, as an engineer may be locked out of their account and unable to perform their job function until their account is unlocked.

The second factor authenticator provides an additional layer of protection in case the user’s regular password is compromised. An adversary would need to compromise both the regular password and the second factor authenticator.

{{ SYSTEM_NAME }} will limit the number of failed logon attempts to 3 consecutive failed attempts within a 15-minute window.{{ SYSTEM_NAME }} must automatically lock the account or node until the locked account is released by an administrator.


## 8. System Use Notification

{{ ORGANIZATION }} will provide the User Agreement before granting access to the system.


## 9. Concurrent Session Control

{{ ORGANIZATION }} limits the number of concurrent sessions for users according to the account types listed below.

- Users - Users are created and managed through Google Identity Platform or Google Workspace.

- Service Accounts - A service account is a special kind of account typically used by an application or compute workload rather than a human. Its email address, which is unique to the account, identifies a service account.

In {{ SYSTEM_NAME }}, there are several different types of service accounts:

- User-managed service accounts: Service accounts that {{ ORGANIZATION }} creates and manages. These service accounts are often used as identities for workloads.

- Default service accounts: User-managed service accounts that are created automatically when you enable certain Google Cloud services. {{ ORGANIZATION }} is responsible for managing these service accounts.

- Google-managed service accounts: Google-created and Google-managed service accounts that enable services to access resources on your behalf.


## 10. Device Lock and/or Session Lock

{{ ORGANIZATION }} prevents further access to {{ SYSTEM_NAME }} by initiating a session lock after 15 minutes of inactivity or upon receiving a request from a user. The session lock is retained until the user reestablishes access using IAM procedures.

{{ ORGANIZATION }} ensures that when sessions locks are initiated on {{ SYSTEM_NAME }}, a screensaver is displayed until a user signs back into the session. The screensaver is used to conceal the information previously visible on the display within a publicly viewable image.


## 11. Session Termination

{{ SYSTEM_NAME }} will provide a logout capability for user-initiated communications sessions whenever authentication is used to gain access to information resources regardless of system type.  Upon successful logout from a system, an explicit logout message to users indicating the reliable termination of authenticated communications sessions will be displayed.

{{ SYSTEM_NAME }} has defined the following conditions or trigger events requiring session disconnect to be employed by the information system when automatically terminating a user session:

- Inactivity timeout

- User logoff

- System shutdown


## 12. Permitted Actions Without Identification or Authentication

{{ SYSTEM_NAME }} does not permit any actions to be performed without identification and authentication.

{{ SYSTEM_NAME }} uses Google IAM to manage access to Google Cloud. User access permissions are controlled at the group level through Role Based Access Control, and using the principle of least privilege, users are given the least number of privileges necessary to perform their specific job function. These groups can be mapped to federate access based on an external identity provider (IdP).

The following breakdown of the various job functions that are considered for the baseline.

- Job Function: the specific type of work to be performed in the baseline

- IAM Role: the set of permissions associated with the job function

- IAM Policy: the document that defines the permissions

- IAM Group: a set of users who share a similar role

- Description: describes what permissions are associated with the specific job function

{{ ORGANIZATION }} permits / does not permit any actions to be performed without identification and authentication.


## 13. Security and Privacy Attributes

Information is represented internally within systems using abstractions known as data structures. Internal data structures can represent different types of entities, both active and passive. Active entities, also known as subjects, are typically associated with individuals, devices, or processes acting on behalf of individuals. Passive entities, also known as objects, are typically associated with data structures, such as records, buffers, tables, files, inter-process pipes, and communications ports. Security attributes, a form of metadata, are abstractions that represent the basic properties or characteristics of active and passive entities with respect to safeguarding information. Privacy attributes, which may be used independently or in conjunction with security attributes, represent the basic properties or characteristics of active or passive entities with respect to the management of personally identifiable information.

{{ ORGANIZATION }} determines how security and privacy attributes are associated with information in storage, in process, and in transmission.

{{ ORGANIZATION }} audits the changes made to any attributes, and reviews them as necessary, but at least annually, for applicability.


## 14. Remote Access

The introduction of cloud-based systems has expanded the boundary to include non-traditional methods of access.  {{ ORGANIZATION }} will manage their own remote access solutions as not all will need remote access solutions in place.  {{ ORGANIZATION }} will consider at a minimum the following items:

- Cloud provider console access must protect data in transit to include usernames and passwords, pin numbers, or other credentials; and

- Any external interfaces used to manage system resources must protect data in transit.

{{ ORGANIZATION }} must configure to route all remote access traffic through managed access control points.


### 14.1 Remote Access Monitoring & Control

The following audit logs are published to pub/sub. {{ SIEM_TOOL }} ({{ CSSP_PROVIDER }}) will subscribe to pub/sub via {{ TELEMETRY_PIPELINE }} to ingest the listed audit logs.

- Activity Logs - Admin Activity audit logs contain log entries for API calls or other actions that modify the configuration or metadata of resources. For example, these logs record when users create VM instances or change Identity and Access Management permissions.

- Data Access Logs -Data Access audit logs contain API calls that read the configuration or metadata of resources, as well as user-driven API calls that create, modify, or read user-provided resource data.

- System Event Logs - System Event audit logs contain log entries for Google Cloud actions that modify the configuration of resources. System Event audit logs are generated by Google systems; they aren't driven by direct user action.

{{ ORGANIZATION }} will monitor all remote access sessions.

Remote access to {{ SYSTEM_NAME }} can be immediately revoked via Google Cloud IAM.


### 14.2 Protection of Confidentiality and Integrity Using Encryption

Encryption can be used to protect data in three states:

- Encryption at rest: protects your data from a system compromise or data exfiltration by encrypting data while stored. The Advanced Encryption Standard (AES) is often used to encrypt data at rest.

- Encryption in transit: protects your data if communications are intercepted while data moves between your site and the cloud provider or between two services. This protection is achieved by encrypting the data before transmission; authenticating the endpoints; and, on arrival, decrypting and verifying that the data was not modified. For example, Transport Layer Security (TLS) is often used to encrypt data in transit for transport security, and Secure/Multipurpose Internet Mail Extensions (S/MIME) is used often for email message encryption.

- Encryption in use: protects your data in memory from compromise or data exfiltration by encrypting data while being processed.


**Encryption-at-Rest**

Google encrypts all content stored at rest, without any further action, using one or more encryption mechanisms.

All data stored in Google Cloud is encrypted at the storage level using AES256 using Google-managed data encryption keys (DEK). Google uses a common cryptographic library which incorporates a FIPS 140-2 validated module, BoringCrypto.


**Encryption-in-Transit**

Google employs several security measures to help ensure the authenticity, integrity, and privacy of data-in-transit.

- Authentication: verify the data source, either a human or a process, and destination.

- Integrity: make sure data you send arrives at its destination unaltered.

- Encryption: make your data unreadable while in transit to keep it private. Encryption is the process through which legible data (plaintext) is made illegible (ciphertext) with the goal of ensuring the plaintext is only accessible by parties authorized by the owner of the data. The algorithms used in the encryption process are public, but the key required for decrypting the ciphertext is private. Encryption in transit often uses asymmetric key exchange, such as elliptic-curve-based Diffie-Hellman, to establish a shared symmetric key that is used for data encryption.

Microservices will primarily use Cloud Pub/Sub and REST transmission methods within the project system. Both of these protocols leverage HTTPS.


## 15. Privileged Commands and Access

Google Cloud IAM roles and groups are designed as a starting point to provide administrative access into {{ SYSTEM_NAME }}. The managed roles and groups are based on job function criteria that can fit a wide range of operational requirements. When assigning any user to a group or role, it is imperative to follow the principle of least privilege. User access permissions should be controlled at the group level through RBAC, and users should be given the least number of privileges necessary to perform their specific job function.

Only roles that have proper permissions applied can conduct the execution of privileged commands via remote access, and only for pre-defined needs.

{{ ORGANIZATION }} is responsible for determining who needs privileged access.

Google leverages integrated IAM for authentication for all interaction with the environment.


## 16. Wireless Access

Wireless access is not permitted for privileged access to {{ SYSTEM_NAME }} or {{ SYSTEM_NAME }}.


## 17. Access Control for Mobile Devices

Mobile devices are not permitted for privileged access to {{ SYSTEM_NAME }} or {{ SYSTEM_NAME }}.


## 18. Use of External Systems

External systems are not authorized to access {{ SYSTEM_NAME }} or {{ SYSTEM_NAME }}.


## 19. Information Sharing

Under the Cloud Shared Responsibility Model, {{ ORGANIZATION }} is responsible for securing application workloads and data transmission.

Google encrypts all underlying infrastructure data communication channels. {{ ORGANIZATION }} mandates and enforces that all transmission of data across system endpoints is facilitated over encrypted channels (TLS 1.3/IPsec).

Google encrypts all data on storage devices to prevent anyone with physical access to physical devices from being able to inspect the data contained on those devices. {{ ORGANIZATION }} can provide their own encryption keys for the encryption of Google Compute Engine Persistent Disks and Google Cloud Storage buckets.

Data stored within databases are all encrypted at the storage level, however additional encryption is advisable at the application level to prevent {{ ORGANIZATION }} users from accessing content and limiting spillage in the event of intrusion.

{{ ORGANIZATION }} may load data which may include PII and PCI into BigQuery for analysis. {{ ORGANIZATION }} are responsible for being aware of and abiding by any regulations regarding the use and storage of this data and are responsible for developing their own aggregation capabilities.


## 20. Publicly Accessible Content

In accordance with federal laws, Executive Orders, directives, policies, regulations, standards, and/or guidance, the general public is not authorized access to nonpublic information (e.g., information protected under the Privacy Act and proprietary information).


## 21. Data Mining Protection

{{ ORGANIZATION }} deploys Google Cloud Sensitive Data Protection (Cloud DLP) inspection templates and BigQuery audit anomaly detectors to detect and protect against unauthorized bulk data retrieval.



## Appendix A – Detailed Compliance Matrix

The following table provides detailed traceability between the policy implementation statements in this document, the authoritative NIST SP 800-53 Rev. 5 control requirements, DoD CCIs, and the technical/governance enforcement mechanisms active across {{ SYSTEM_NAME }}.


| CTRL ID | CTRLTITLE | REQUIRED eMASS STANDARD | DOCREF | ENFORCEMENT MECHANISM |
| :--- | :--- | :--- | :--- | :--- |
| AC-01 | Policy and Procedures | Develop, document, disseminate to all personnel, and review/update annually (or upon significant threat/architecture changes) access control policy and procedures. (CCIs: 000002, 000003, 000005, 000006, 001545, 001546, 002107, 002108, 003601, 003602, 003603, 003604, 003605, 003606, 003607, 003608, 003609, 003610, 003611) | Section 2.1 | Formal annual review workflow by {{ ORGANIZATION }} ISSM/AO; published in central governance repository; triggered on architecture/incident events. |
| AC-02 | Account Management | Define account types, prerequisites, operational need-to-know, clearance levels, approvals (ISSO/ISSM), notifications within 4h/24h, and quarterly account reviews. (CCIs: 000010, 000011, 000012, 001547, 002112, 002115, 002116, 002117, 002118, 002119, 002120, 002121, 002122, 002123, 002124, 002125, 002126, 002127, 002128, 002129, 003612, 003613, 003614, 003615, 003616, 003617, 003618, 003619, 003620, 003621, 003622, 003625, 003626) | Section 2.2 | {{ ACCESS_AGREEMENT_TYPE }} electronic workflow; {{ IDENTITY_PROVIDER }} identity lifecycle; quarterly IAM audits; automated role group assignments. |
| AC-02(01) | Automated System Account Management | Employ automated mechanisms to create, enable, modify, disable, and remove accounts across the system. (CCIs: 000015) | Section 2.2 | SCIM protocol sync from {{ IDENTITY_PROVIDER }} to Cloud Identity Workforce Pool; automated IAM group membership updates. |
| AC-02(02) | Automated Temporary and Emergency Account Management | Automatically disable temporary accounts (.tmp) and emergency break-glass accounts after 72 hours (or 24 hours post-task). (CCIs: 000016, 001361, 001365, 001682) | Section 2.2 | Cloud Identity automated account expiration triggers; sealed Class 6 safe break-glass credentials; physical register logs. |
| AC-02(03) | Disable Accounts | Disable accounts within 72 hours of termination/transfer, and disable inactive accounts after 35 days of inactivity. (CCIs: 000017, 003627, 003628, 003629) | Section 2.2 | Automated 35-day inactivity disablement policy in {{ IDENTITY_PROVIDER }} / Cloud Identity; immediate administrative revocation workflows. |
| AC-02(04) | Automated Audit Actions | Automatically audit all account management actions (creation, modification, disablement, deletion) and alert administrators. (CCIs: 000018, 001403, 001404, 001405, 002130) | Section 2.2 | GCP Cloud Audit Logs (Admin Activity); real-time Pub/Sub log sinks; external CSSP/SIEM and Cloud Monitoring (or SCC dashboards in FedRAMP High / Commercial enclaves). |
| AC-02(05) | Inactivity Logout | Require users to log out at the end of their work period and enforce automated inactivity logout after 15 minutes. (CCIs: 000019, 001406, 002133) | Section 2.2 | Automated 15-minute idle session timeout policy across Google Cloud Console, IAP, and management portals. |
| AC-02(07) | Privileged User Accounts | Enforce role-based and attribute-based access schemes for privileged accounts, restricting them to DCWF qualified personnel. (CCIs: 001358, 001360, 001407, 002137, 003630) | Section 2.3 | Dedicated administrative accounts (admin-*); {{ MFA_MECHANISM }}; fine-grained Custom IAM Roles with Resource Manager tags. |
| AC-02(09) | Restrictions on Use of Shared and Group Accounts | Prohibit shared/group accounts unless operational necessity is documented, AO approves, and deterministic individual auditability exists. (CCIs: 002140, 002141) | Section 2.3 | Cloud IAM individual identity enforcement; prohibition of static shared credentials; individual proxy session logging. |
| AC-02(12) | Account Monitoring for Atypical Usage | Monitor accounts for atypical usage (unusual times, locations, access patterns) and alert ISSM, ISSO, and SO. (CCIs: 002146, 002147, 002148, 002149) | Section 2.2 | Cloud Logging Log Router sinks streaming to external accredited CSSP/SIEM; Cloud Monitoring anomaly alerting (or SCC anomaly detection in FedRAMP High / Commercial enclaves); automated UBA alert pipelines. |
| AC-02(13) | Disable Accounts for High-risk Individuals | Immediately disable accounts for individuals posing significant risk, credential compromise, or insider threat indicators. (CCIs: 002150, 002151, 003637) | Section 2.2 | Automated identity revocation; programmatic API token revocation; 15-minute ISSO incident response trigger. |
| AC-03 | Access Enforcement | Enforce approved authorizations for logical access to information and resources based on applicable access control policies. (CCIs: 000213) | Section 2.4 | Google Cloud IAM policy evaluation; VPC Service Controls perimeters; Identity-Aware Proxy (IAP) Zero Trust tunnels. |
| AC-03(04) | Discretionary Access Control | Enforce discretionary access control policies adhering to least privilege across subjects and objects. (CCIs: 002163, 002164, 002165, 003638, 003639, 003640, 003641, 003642) | Section 2.4 | IaC Terraform resource-level IAM bindings; GCS bucket IAM policies; BigQuery dataset access control lists. |
| AC-03(09) | Controlled Release | Adhere to security controls and obtain Information Owner authorization prior to releasing information across boundaries. (CCIs: 002180, 002181, 002182, 002183, 002184) | Section 2.4 | Pub/Sub schema validation; BigQuery row-level security filters; DoDI 8540.01 cross-domain authorization policies. |
| AC-03(14) | Individual Access | Provide mechanisms for individuals to access and review their PII in accordance with The Privacy Act of 1974. (CCIs: 003654, 003655, 003656) | Section 2.4 | Formal Data Subject Access Request (DSAR) workflow administered by Enterprise Privacy Officer; audited log extraction. |
| AC-04 | Information Flow Enforcement | Enforce information flow control policies based on classification, need-to-know, and PPSM deny-all baseline. (CCIs: 001368, 001414, 001548, 001549) | Section 2.5 | GCP Cloud Firewall rules; Cloud Router routing policies; VPC route tables; NCC spoke-to-spoke transit rules. |
| AC-04(01) | Object Security and Privacy Attributes | Associate security attributes (classification, sensitivity) with information, source, and destination objects in flow decisions. (CCIs: 002187, 002188, 002189, 002190, 003661) | Section 2.5 | GCP Resource Manager Tags (environment: prod, tier: backend); packet encapsulation headers; subnet tags. |
| AC-04(08) | Security and Privacy Policy Filters | Deploy security/privacy filters and enforce fail-safe blocking and quarantining of information flows upon filter failure. (CCIs: 000032, 001417, 002195, 003663, 003664, 003665) | Section 2.5 | Cloud Armor policies; Cloud DLP inspection engines; virtual firewall appliances; automated fail-safe drop rules. |
| AC-04(17) | Domain Authentication | Authenticate communicating organizations, systems, applications, and services prior to information transfer. (CCIs: 002205, 002207) | Section 2.5 | BGP MD5 authentication; BFD sub-second link verification; SNMPv3 AuthPriv encryption with dynamic Secret Manager keys. |
| AC-04(19) | Validation of Metadata | Validate that metadata, tags, and markings accurately reflect security classification ({{ SENSITIVITY_CLASSIFICATION }} / {{ IMPACT_LEVEL }}) before routing data. (CCIs: 002211, 003666) | Section 2.5 | Automated CI/CD metadata validation; Resource Manager Tag enforcement; Cloud Build static policy gates. |
| AC-05 | Separation of Duties | Separate duties across administration, security auditing, software development, and network vs. compute platform engineering. (CCIs: 002219, 002220, 003684) | Section 2.6 | Multi-project landing zone topology; separate CI/CD service accounts; mutual exclusivity IAM rules. |
| AC-06 | Least Privilege | Enforce least privilege, allowing only authorized accesses necessary to accomplish assigned mission functions. (CCIs: 000225) | Section 2.7 | Elimination of primitive IAM roles; fine-grained Custom IAM Roles; subnet-level access control on Shared VPCs. |
| AC-06(01) | Authorize Access to Security Functions | Authorize privileged users access to security functions and security-relevant information based on DCWF position roles. (CCIs: 001558, 002221, 002222, 002223, 003685, 003686) | Section 2.7 | Custom IAM roles for {{ SYSTEM_NAME }} Network Administrators and Compute Infrastructure Administrators; signed {{ ACCESS_AGREEMENT_TYPE }} verification. |
| AC-06(02) | Non-privileged Access for Nonsecurity Functions | Require privileged users to use non-privileged accounts or roles when accessing non-security functions. (CCIs: 000039, 001419) | Section 2.7 | Separation of admin accounts (admin-*) from standard user accounts; policy prohibition of dual-purpose sessions. |
| AC-06(04) | Separate Processing Domains | Maintain separate execution and processing domains for different security and operational environments. (CCIs: 002225) | Section 2.7 | Hard project boundaries between Dev (*-d), Test (*-t), and Prod (*-p); separate GCS Terraform state buckets. |
| AC-06(05) | Privileged Accounts | Restrict privileged account creation exclusively to personnel requiring privileged access under DCWF standards. (CCIs: 002226, 002227) | Section 2.7 | Strict ISSM/ISSO approval gating; DCWF certification mapping; annual workforce compliance audits. |
| AC-06(07) | Review of User Privileges | Review privileges assigned to all users at least quarterly (and annually) to ensure adherence to least privilege. (CCIs: 002228, 002229, 002230, 002231) | Section 2.7 | Quarterly IAM entitlement review against {{ ACCESS_AGREEMENT_TYPE }} authorizations; automated privilege revocation on discrepancies. |
| AC-06(08) | Privilege Levels for Code Execution | Prevent software and pipelines from executing with higher privileges than authorized; restrict CI/CD service accounts. (CCIs: 002232, 002233) | Section 2.7 | Workload Identity Federation (WIF) OIDC impersonation; no downloadable JSON keys; transit-network-sa scoped roles. |
| AC-06(09) | Log Use of Privileged Functions | Enable audit logging for all executions of privileged functions, API calls, and administrative operations. (CCIs: 002234) | Section 2.7 | GCP Cloud Audit Logs (Admin Activity & Data Access); immutable log sinks; Pub/Sub routing to BigQuery and SIEM. |
| AC-06(10) | Prohibit Non-privileged Users from Executing Privileged Functions | Prevent non-privileged users from executing privileged commands or altering security countermeasures. (CCIs: 002235) | Section 2.7 | GCP Cloud IAM explicit permission denial; separation of IAM Admin permissions; Cloud Resource Manager protections. |
| AC-07 | Unsuccessful Logon Attempts | Limit consecutive invalid logon attempts to 3 within 15 minutes, automatically locking the account for 15 minutes. (CCIs: 000043, 000044, 001423, 002236, 002237, 002238) | Section 2.8 | {{ IDENTITY_PROVIDER }} lockout policy (3 attempts / 15-min lockout); automated SOC alert on lockout events. |
| AC-08 | System Use Notification | Display approved {{ WARNING_BANNER_TYPE }} before granting access, requiring explicit user consent. (CCIs: 000048, 000050, 001384, 001385, 001386, 001387, 001388, 002243, 002244, 002245, 002246, 002247, 002248) | Section 2.8 | Pre-login banners on Google Cloud Console SSO, bastion SSH legal banners, and IAP gateway consent screens. |
| AC-09 | Previous Logon Notification | Notify users upon successful logon of the date, time, and source IP of their previous successful and failed attempts. (CCIs: 000052) | Section 2.8 | Linux bastion PAM login notifications; {{ IDENTITY_PROVIDER }} authentication history displays and audit logs. |
| AC-10 | Concurrent Session Control | Limit concurrent active sessions to a maximum of 3 sessions for all user accounts across the system. (CCIs: 000054, 000055, 002252) | Section 2.9 | {{ IDENTITY_PROVIDER }} conditional access session controls; Cloud Identity concurrent session limiting policies. |
| AC-11 | Device Lock | Prevent unauthorized access by initiating a session lock after 15 minutes of inactivity or upon user request. (CCIs: 000056, 000057, 000059) | Section 2.9 | Automated 15-minute screensaver lock policy on authorized virtual desktops and management workstations; {{ MFA_MECHANISM }} re-authentication. |
| AC-11(01) | Pattern-hiding Displays | Conceal previously visible information on display screens during device lock using pattern-hiding displays. (CCIs: 000060) | Section 2.9 | Blank screen / generic DoD screensaver enforcement via Group Policy Objects (GPO) and endpoint configuration. |
| AC-12 | Session Termination | Automatically terminate user sessions after 15 minutes of inactivity, user logoff, or reaching maximum duration (24h/4h). (CCIs: 002360, 002361) | Section 2.9 | Cloud Console session lifetime policies; PAM 4-hour elevation timeout; IAP TCP tunnel disconnect triggers. |
| AC-12(01) | User-initiated Logouts | Provide explicit user-initiated logout capability across all system communications and management sessions. (CCIs: 002362, 002363) | Section 2.9 | Web application explicit logout buttons; SAML single-logout (SLO) endpoint integration; SSH session termination. |
| AC-12(02) | Termination Message | Display an explicit logout message confirming reliable termination of authenticated communications sessions. (CCIs: 002364) | Section 2.9 | SSO post-logout confirmation page; session token invalidation confirmation notices. |
| AC-14 | Permitted Actions Without Identification or Authentication | Prohibit all unauthenticated user actions across {{ SYSTEM_NAME }} infrastructure; mandate identification and authentication. (CCIs: 000061, 000232, 003695) | Section 2.10 | GCP IAM default deny; compute.vmExternalIpAccess organization policy; zero-trust network ingress architecture. |
| AC-16 | Security and Privacy Attributes | Establish, associate, and review (every 90 days) security and privacy attributes across storage, processing, and transit. (CCIs: 002256, 002257, 002258, 002259, 002260, 002261, 002262, 002263, 002264, 002265, 002266, 002267, 002268, 002269, 002270, 002271, 003696, 003697, 003698, 003699, 003700, 003701, 003702, 003703, 003704, 003705, 003706, 003707, 003708, 003709, 003710, 003711) | Section 2.10 | GCP Resource Manager Tags (data-sensitivity, environment); BigQuery column policy tags; quarterly attribute reviews. |
| AC-16(01) | Dynamic Attribute Association | Dynamically associate security and privacy attributes with subjects and objects based on operational context. (CCIs: 001424, 002272, 002273, 002274, 002275, 003712, 003713, 003714) | Section 2.10 | {{ IDENTITY_PROVIDER }} dynamic security groups; SCIM attribute mapping; IAM Conditional bindings based on resource tags. |
| AC-16(03) | Maintenance of Attribute Associations by System | Ensure the system maintains the integrity and association of security attributes across data lifecycles. (CCIs: 002278, 002279, 002280, 002281, 002282, 002283, 002284, 003717, 003718, 003719, 003720, 003721) | Section 2.10 | Cloud KMS encryption context bindings; Pub/Sub message attribute preservation; BigQuery schema enforcement. |
| AC-16(06) | Maintenance of Attribute Association by Personnel | Require personnel to correctly associate and maintain security markings and metadata on all managed resources. (CCIs: 002291, 002292, 002293, 002294, 002295, 002296, 002297, 002298, 003730, 003731, 003732, 003733, 003734, 003735, 003736, 003737) | Section 2.10 | Mandatory Terraform tagging modules; pre-commit linting (checkov, tfsec) validating required tag definitions. |
| AC-16(07) | Consistent Attribute Interpretation | Ensure consistent interpretation of security attributes across interconnected government cloud enclaves and tenant spoke projects. (CCIs: 002299, 003738) | Section 2.10 | Standardized {{ SENSITIVITY_CLASSIFICATION }} taxonomy across Google Cloud Assured Workloads and tenant landing zones. |
| AC-17 | Remote Access | Authorize and control all remote access to the system via managed access control points and secure protocols. (CCIs: 000065, 002310, 002311, 002312) | Section 2.11 | DoD SCCA / VDSS boundary firewalls; GCP Identity-Aware Proxy (IAP) Zero Trust tunnels; no public internet ingress. |
| AC-17(01) | Monitoring and Control | Monitor and control all remote access sessions in real time, routing audit telemetry to central security hubs. (CCIs: 000067, 002314) | Section 2.11 | Cloud Audit Logging; VPC Flow Logs on transit subnets; real-time Pub/Sub streaming to {{ SIEM_TOOL }} / {{ CSSP_PROVIDER }} SOC. |
| AC-17(02) | Protection of Confidentiality and Integrity Using Encryption | Protect confidentiality and integrity of remote access sessions using FIPS 140-2/140-3 NSA-approved cryptography. (CCIs: 000068, 001453) | Section 2.11 | Physical Layer 2 MACsec (gcm-aes-xpn-256); Layer 3 IPsec (AES-256-GCM); Cloud KMS HSM CMEK (AES-256). |
| AC-17(03) | Managed Access Control Points | Route all remote access traffic through designated managed access control points (SCCA/VDSS/IAP). (CCIs: 000069) | Section 2.11 | Shared VPC host architecture; dedicated interconnect transit VPC routing. |
| AC-17(04) | Privileged Commands and Access | Restrict remote execution of privileged commands to compelling operational needs, requiring PAM JIT authorization. (CCIs: 000070, 002316, 002317, 002318, 002319, 002320) | Section 2.11 | GCP Privileged Access Manager (PAM) JIT elevation (max 4 hours); Access Approval workflows; command-line auditing. |
| AC-17(06) | Protection of Mechanism Information | Protect remote access mechanism implementation details and key material against unauthorized disclosure. (CCIs: 000072) | Section 2.11 | GCP Secret Manager storage for credentials; VPC Service Controls perimeters; DoD SAFE key transfer protocols. |
| AC-17(09) | Disconnect or Disable Access | Maintain the capability to immediately disconnect or disable remote access sessions upon detected security risks. (CCIs: 002321, 002322) | Section 2.11 | Programmatic IAM session revocation APIs; Cloud Identity immediate account suspension; IAP tunnel kill switches. |
| AC-18 | Wireless Access | Prohibit wireless access for privileged administration and disable wireless interfaces on all infrastructure devices. (CCIs: 001439, 001441, 002323) | Section 2.12 | Disablement of wireless drivers/interfaces on compute VMs; network policy blocking wireless management ingress. |
| AC-18(01) | Authentication and Encryption | Enforce strong mutual authentication and encryption if wireless is ever authorized by exception ({{ MFA_MECHANISM }}). (CCIs: 001443, 001444) | Section 2.12 | WPA3-Enterprise / 802.1X EAP-TLS requirements for base-level wireless transport connecting to VPN overlays. |
| AC-18(03) | Disable Wireless Networking | Disable internal wireless networking capabilities across all cloud instances and transit routing components. (CCIs: 001449) | Section 2.12 | Baseline OS hardening images (DISA STIG); Terraform compute instance configurations omitting wireless hardware. |
| AC-18(04) | Restrict Configurations by Users | Restrict users from configuring or enabling wireless networking capabilities on any {{ SYSTEM_NAME }} system component. (CCIs: 002324) | Section 2.12 | IAM policy restricting system configuration privileges; GPO / Linux STIG disabling user network reconfiguration. |
| AC-19 | Access Control for Mobile Devices | Prohibit commercial mobile devices from directly accessing or administering {{ SYSTEM_NAME }} infrastructure. (CCIs: 000083, 000084, 002325, 002326) | Section 2.12 | {{ IDENTITY_PROVIDER }} Conditional Access blocking non-compliant mobile OS; IAP device context verification rules. |
| AC-19(05) | Full Device or Container-based Encryption | Mandate full-device encryption for any authorized mobile devices processing organizational data. (CCIs: 002329, 002330, 002331) | Section 2.12 | DoD MDM / Intune compliance policies enforcing FIPS 140-2 BitLocker / FileVault full-disk encryption. |
| AC-20 | Use of External Systems | Prohibit unauthorized external systems; require ATO, ISA/MOA, and approved security controls for interconnections. (CCIs: 000093, 002332, 003750, 003751, 003752, 003753, 003754, 003755) | Section 2.12 | Formal Interconnection Security Agreements (ISAs); cross-cloud BGP peering validation; VPC Service Controls. |
| AC-20(01) | Limits on Authorized Use | Limit authorized use of external systems to approved DoD IL5 accredited enclaves and interconnected mission partner systems. (CCIs: 002337, 003756, 003757) | Section 2.12 | BGP prefix filtering on Cloud Routers; Dedicated Interconnect VLAN attachment access control lists. |
| AC-20(02) | Portable Storage Devices: Restricted Use | Prohibit and technically restrict the use of portable storage devices on all management workstations and bastions. (CCIs: 000097, 003758) | Section 2.12 | Endpoint GPO disabling USB mass storage; virtual bastion instances configured without removable media mounts. |
| AC-20(03) | Non-organizationally Owned Systems: Restricted Use | Restrict non-organizationally owned systems from processing organizational data; mandate DoD-approved authentication. (CCIs: 002338) | Section 2.12 | {{ IDENTITY_PROVIDER }} device compliance policies; mandatory {{ MFA_MECHANISM }} mutual TLS authentication; boundary gateway proxying. |
| AC-21 | Information Sharing | Govern ad-hoc information sharing with external partners, validating access authorizations and need-to-know. (CCIs: 000098, 001470, 001471, 001472) | Section 2.13 | Automated Cloud DLP inspection templates; BigQuery authorized views; ISSO manual {{ SENSITIVITY_CLASSIFICATION }} verification procedures. |
| AC-22 | Publicly Accessible Content | Prohibit hosting non-public content on publicly accessible endpoints; audit public exposure quarterly. (CCIs: 001473, 001474, 001475, 001476, 001477, 001478) | Section 2.13 | compute.vmExternalIpAccess and storage.publicAccessPrevention org policies; quarterly public asset audit scans. |
| AC-23 | Data Mining Protection | Deploy anomaly detection and user behavior analytics to protect databases and storage objects from data mining/exfiltration. (CCIs: 002343, 002344, 002345, 002346, 002347) | Section 2.13 | VPC Service Controls perimeter blocking data export; BigQuery audit anomaly detectors; Cloud Logging export sinks to external CSSP/SIEM (or SCC threat monitoring in FedRAMP High / Commercial enclaves). |
