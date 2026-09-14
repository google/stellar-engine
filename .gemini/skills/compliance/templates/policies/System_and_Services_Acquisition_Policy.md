# SA - System and Services Acquisition Policy and Procedures

## Document Governance & Approval Baseline

| Governance Metric | Policy Standard & Specification |
| :--- | :--- |
| **Document Title** | System and Services Acquisition Policy and Procedures |
| **NIST Control Family** | System and Services Acquisition (SA) |
| **Primary NIST Benchmark** | NIST SP 800-161 Rev. 1, NIST SP 800-64 Rev. 2 (Secure SDLC) |
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
> This document defines the enterprise security policy and implementation procedures for **System and Services Acquisition** under **NIST SP 800-53 Rev. 5 (SA)**.
> Technical infrastructure controls are automatically provisioned and enforced via **{{ SYSTEM_NAME }}** Terraform blueprints.
> Operational rules or contact details requiring manual confirmation are highlighted with RMF Team Callouts.


## 1. Overview

The purpose of this System and Services Acquisition Plan is to manage the design, development, maintenance, and disposal of {{ ORGANIZATION }} {{ SYSTEM_NAME }} throughout the security infrastructure and facilitate the implementation of the system and services acquisition policy and the associated system and services acquisition controls.

This document complies with the following requirements from NIST Special Publication 800-53 Revision 5, "Security and Privacy Controls for Federal Information Systems and Organizations". A detailed compliance matrix can be found in Appendix A, “Detailed Compliance Matrix”.


## 2. Policy and Procedures

System and services acquisition policy and procedures address the controls in the SA family that are implemented within systems and organizations. The risk management strategy is an important factor in establishing such policies and procedures. Therefore, it is important that security and privacy programs collaborate on the development of system and services acquisition policy and procedures.

This policy describes high-level requirements that specify how to manage the design, development, and maintenance of the security infrastructure, and to protect its information. This policy reflects DoD level policies, DoDD 5000.01, DoDI 5000.02, and DoDI 8580.1, which address system and services acquisition.

This policy is to be disseminated to all {{ ORGANIZATION }} personnel and associated roles to facilitate the implementation of the system and services acquisition policy and associated system and services acquisition controls.

{{ ORGANIZATION }} will review and update this policy, as necessary, but at least annually.



### 2.1 Google Cloud Platform (GCP) Inherited Controls & Shared Responsibility Boundary

- **Google Inherited Controls**: Google Cloud enforces Secure Software Development Lifecycle (SDLC) standards (`SA-8`, `SA-11`), static/dynamic code analysis, and supply chain security for all GCP platform software.
- **Customer Implementation Responsibilities**: {{ ORGANIZATION }} is responsible for defining DevSecOps acquisition policies (`SA-4`), executing automated CI/CD security checks (`SA-11`), and conducting developer security training (`SA-16`).

## 3. Allocation of Resources

Resource allocation for {{ ORGANIZATION }} {{ SYSTEM_NAME }} security includes funding for system and services acquisition, sustainment, and supply chain-related risks throughout the system development life cycle. {{ ORGANIZATION }} {{ SYSTEM_NAME }} must determine, document, and allocate the resources required to protect the system/service as part of its capital planning and investment control process and  establish line items for security and privacy in their programming and budgeting.

A System Categorization Document is completed for {{ ORGANIZATION }} {{ SYSTEM_NAME }} documenting the security requirements to be reviewed by the AO and SCA/Rs. Once approved, the {{ SYSTEM_NAME }} details and information, along with the system categorization, are entered into {{ RMF_GOVERNANCE_SYSTEM }} completing RMF Step 2 – Select Security Controls.


## 4. System Development Life Cycle

A well-defined System Development Life Cycle (SDLC) provides the foundation for the successful development, implementation, and operation of information systems. The integration of security and privacy considerations early in the SDLC is a foundational principle of systems security engineering and privacy engineering. To apply the required controls within the SDLC requires a basic understanding of information security and privacy, threats, vulnerabilities, adverse impacts, and risk to critical mission and business functions.

The effective integration of security and privacy requirements into enterprise architecture also helps to ensure that important security and privacy considerations are addressed throughout the SDLC and that those considerations are directly related to organizational mission and business processes.

{{ ORGANIZATION }} {{ SYSTEM_NAME }} documents the SDLC detailing the process of incorporating the implementation, testing and validation of the security requirements in alignment with the system development process. Evidence that the SDLC is adhered to during the development process is to be provided as part of the RMF package.

{{ ORGANIZATION }} identifies the following roles to implement and maintain cybersecurity requirements. Roles will be assigned in writing. The preferred method is in the form of an appointment letter by the Approving Official or designated authority.

The required roles are listed below:

- Program Manager

- System/Network Administrator

- Information System Security Manager (ISSM)

- Information System Security Officer (ISSO)

- Security Control Assessor/Representative (SCA/R)


### 4.1 Manage Preproduction Environment

The preproduction environment includes development, test, and integration environments.

{{ ORGANIZATION }} will maintain and manage the security and privacy of the preproduction environments for {{ SYSTEM_NAME }} and {{ SYSTEM_NAME }}, and the same impact and classification level as any live data that is used.


### 4.2 Use of Live or Operational Data

The use of operational data in preproduction (i.e., development, test, and integration) environments can result in significant risks to organizations. It is important for {{ ORGANIZATION }} to manage any additional risks that may result from the use of operational data. {{ ORGANIZATION }} can minimize such risks by using test or dummy data during the design, development, and testing of {{ SYSTEM_NAME }}, {{ SYSTEM_NAME }} components, and {{ SYSTEM_NAME }} services.

{{ ORGANIZATION }} will use risk assessment techniques to determine if the risk of using operational data is acceptable.


### 4.3 Technology Refresh

Technology refresh planning may encompass hardware, software, firmware, processes, personnel skill sets, suppliers, service providers, and facilities. The use of obsolete or nearing obsolete technology may increase the security and privacy risks associated with unsupported components, counterfeit or repurposed components, components unable to implement security or privacy requirements, slow or inoperable components, components from untrusted sources, inadvertent personnel error, or increased complexity. Technology refreshes typically occur during the operations and maintenance stage of the system development life cycle.

Throughout the SDLC, {{ ORGANIZATION }} will ensure technology refreshes are planned and executed to maintain the security posture of {{ SYSTEM_NAME }}.


## 5. Acquisition Process

The following requirements, descriptions, and criteria, explicitly or by reference, are to be included within the contract language in relation to the acquisition process for the {{ ORGANIZATION }} {{ SYSTEM_NAME }}, {{ SYSTEM_NAME }} component, or {{ SYSTEM_NAME }} service in accordance with applicable federal laws, Executive Orders, directives, policies, regulations, standards, guidelines, and organizational mission/business need:

- Security and privacy functional requirements;

- Strength of mechanism requirements;

- Security and privacy assurance requirements;

- Controls needed to satisfy the security and privacy requirements.

- Security and privacy documentation requirements;

- Requirements for protecting security and privacy documentation;

- Description of the system development environment and environment in which the system is intended to operate;

- Allocation of responsibility or identification of parties responsible for information security, privacy, and supply chain risk management; and

- Acceptance criteria.


### 5.1 Functional Properties of Controls

Functional properties of security and privacy controls describe the functionality (i.e., security or privacy capability, functions, or mechanisms) visible at the interfaces of the controls and specifically exclude functionality and data structures internal to the operation of the controls.

{{ ORGANIZATION }} developers provide description of the functional properties of the security controls that of {{ SYSTEM_NAME }}.


### 5.2 Design and Implementation Information

Developer of {{ ORGANIZATION }} {{ SYSTEM_NAME }}, {{ SYSTEM_NAME }} components, or {{ SYSTEM_NAME }} services provide design and implementation information detailing high and low-level design, external system interfaces, source code and hardware schematics. {{ ORGANIZATION }} cybersecurity and engineers work to configure security requirements into the design and document implementation related to applicable security controls. All system interfaces and IA-enabled IT products are required to be documented and approved through the RMF process. For {{ ORGANIZATION }} programs that have requirements for PKI tokens, National Information Assurance partnership (NIAP)-approved products, and Federal Information Processing Standards (FIPS)-validated products, all related design details and proof of implementation are to be provided for the RMF package.


### 5.3 Development Methods, Techniques, and Practices

Following a system development life cycle that includes state-of-the-practice software development methods, systems engineering methods, systems security and privacy engineering methods, and quality control processes helps to reduce the number and severity of latent errors within systems, system components, and system services. Reducing the number and severity of such errors reduces the number of vulnerabilities in those systems, components, and services. Transparency in the methods and techniques that developers select and implement for systems engineering, systems security and privacy engineering, software development, component and system assessments, and quality control processes provides an increased level of assurance in the trustworthiness of the system, system component, or system service being acquired.

{{ ORGANIZATION }} {{ SYSTEM_NAME }} developers must use SDLC process that includes:

- {{ SYSTEM_NAME }} Engineering Methods

- DevSecOps Infrastructure-as-Code (IaC)

- Agile DevSecOps CI/CD

- Automated Unit & IaC Security Verification

- Automated Code Review & Branch Protection


### 5.4 System, Component, and Service Configurations

{{ ORGANIZATION }} {{ SYSTEM_NAME }} developers use the following guidelines to implement security configurations:

- Center for Internet Security (CIS) Google Cloud Platform Foundation Benchmark
- NIST SP 800-53 Rev. 5 FedRAMP High / DoD IL5 Security Control Baselines
- DISA Security Technical Implementation Guides (STIGs) / Security Requirements Guides (SRGs)


### 5.5 NIAP-Approved Protection Profiles

{{ ORGANIZATION }} will limit the use of commercially provided information assurance and information assurance-enabled information technology products to those products that have been successfully evaluated against a National Information Assurance partnership (NIAP)-approved Protection Profile for a specific technology type, if such a profile exists; and require, if no NIAP-approved Protection Profile exists for a specific technology type but a commercially provided information technology product relies on cryptographic functionality to enforce its security policy, that the cryptographic module is FIPS-validated or NSA-approved.


### 5.6 Functions, Ports, Protocols, and Services in Use

By identifying the specific configurations within the system development life cycle of the {{ SYSTEM_NAME }}, {{ SYSTEM_NAME }} component, or {{ SYSTEM_NAME }} service, the developers can work with cybersecurity personnel to design and configure the system in a way that does not pose unnecessarily high risks and understand the trade-offs involved in blocking specific ports, protocols, or services.

The RMF package associated with {{ SYSTEM_NAME }} includes the documentation of functions, ports, protocols, and services. Internal and external connections are to be included in the documentation and accurately identified.


### 5.7 Use of PIV Products

FIPS 201-3 Personal Identity Verification (PIV) of Federal Employees and Contractors establishes a standard for a PIV system that meets the control and security objectives and is based on secure and reliable forms of identity credentials issued by the Federal Government to its employees and contractors. These credentials are used by mechanisms that authenticate individuals who require access to federally controlled facilities, information systems, and applications.

{{ ORGANIZATION }} implements information technology products on the FIPS 201-approved products list for PIV capability implemented within {{ ORGANIZATION }} {{ SYSTEM_NAME }}.


## 6. System Documentation

System documentation helps personnel understand the implementation and operation of controls. {{ ORGANIZATION }} has established specific measures to determine the quality and completeness of the content provided.

The {{ SYSTEM_NAME }} developers provide administrator documentation for {{ SYSTEM_NAME }} that describes secure installation, configuration, and operation. Maintenance procedures are documented and provided to identified and approved personnel performing maintenance tasks. User documentation describes user responsibilities in maintaining the security of the system, component, or service and is provided as required.

{{ ORGANIZATION }} is responsible for developing and maintaining administrative documentation for {{ SYSTEM_NAME }} that describes:

- Secure configuration, installation, and operation of {{ SYSTEM_NAME }};

- Effective use and maintenance of security and privacy functions and mechanisms; and

- known vulnerabilities regarding configuration and use of administrative or privileged functions.

{{ ORGANIZATION }} is responsible for developing and maintaining user documentation for {{ SYSTEM_NAME }} that describes:

- User accessible security and privacy functions and mechanisms and how to effectively use those functions and mechanisms;

- Methods for user interaction, which enables individuals to use {{ SYSTEM_NAME }}, in a more secure manner and protect individual privacy; and

- User responsibilities in maintaining the security of {{ SYSTEM_NAME }}.

{{ ORGANIZATION }} distributes the associated documentation to all applicable personnel.


## 7. Security and Privacy Engineering Principles

Systems security and privacy engineering principles are closely related to and implemented throughout the SDLC.

{{ ORGANIZATION }} documents {{ SYSTEM_NAME }} security and privacy engineering principles in the specification, design, development, implementation, and modification. The engineering principles required are derived from individual {{ ORGANIZATION }} {{ SYSTEM_NAME }} contracts and mission requirements.

{{ ORGANIZATION }} will implement the following security design principles:

- Clear Abstractions;

- Least Common Mechanisms;

- Modularity and Layering;

- Partially Ordered Dependencies;

- Efficiently Mediated Access;

- Minimized Sharing;

- Reduced Complexity;

- Secure Evolvability;

- Trusted Components;

- Hierarchical Trust;

- Inverse Modification Threshold;

- Hierarchical Protection;

- Minimized Security Elements;

- Least Privilege;

- Predicated Permission;

- Self-Reliant Trustworthiness;

- Secure Distributed Composition;

- Trusted Communications Channels;

- Continuous Protection;

- Secure Metadata Management;

- Self-Analysis;

- Accountability and Traceability;

- Secure Defaults;

- Secure Failure and Recovery;

- Economic Security;

- Performance Security;

- Human Factored Security;

- Acceptable Security;

- Repeatable and Documented Procedures;

- Procedural Rigor;

- Secure System Modification; and

- Sufficient Documentation.


## 8. External System Services

{{ ORGANIZATION }} {{ SYSTEM_NAME }}, system components or system services that have dependencies on external system services are required to provide evidence of security agreements between the external source and {{ ORGANIZATION }}. External system services documentation includes government, service providers, end user security roles and responsibilities, and service-level agreements. Service-level agreements define the expectations of performance for implemented controls, describe measurable outcomes, and identify remedies and response requirements for identified instances of noncompliance.

All relationships with external sources are to be continuously monitored.


### 8.1 Risk Assessments and Organizational Approvals

When external system services are utilized, {{ ORGANIZATION }} conducts an organizational assessment of risk prior to the acquisition or outsourcing of information security services. The acquisition or outsourcing of information security services can only be approved by the following roles:

- System Owner & ISSO


### 8.2 Identification of Functions, Ports, Protocols, and Services

{{ ORGANIZATION }} {{ SYSTEM_NAME }} requires providers of all system services external to {{ SYSTEM_NAME }}, to identify the functions, ports, protocols, and other services required for the use of such services. This information is to be included as part of all formal agreements between {{ ORGANIZATION }} and external providers for connection between the {{ SYSTEM_NAME }} and the external system service.


### 8.3 Establish and Maintain Trust Relationship with Providers

{{ ORGANIZATION }} will document, and maintain trust relationships with external service providers based on the following requirements, properties, factors, or conditions:

- FedRAMP High / DoD IL5 Trust Baseline


### 8.4 Processing and Storage Location - U.S. Jurisdiction

The geographic location of information processing and data storage can have a direct impact on the ability of organizations to successfully execute their mission and business functions.

Based on the classification of the data stored and processed on {{ SYSTEM_NAME }}, {{ ORGANIZATION }} restricts the geographic location of information processing and data storage to facilities located in the legal jurisdictional boundary of the United States.


## 9. Developer Configuration Management

Organizations consider the quality and completeness of configuration management activities conducted by developers as direct evidence of applying effective security controls. The quality and completeness of the configuration management activities conducted by developers as evidence of applying effective security safeguards is considered.

{{ ORGANIZATION }} {{ SYSTEM_NAME }} developers are required to perform configuration management during the design, development, implementation, operation, and disposal phases of SDLC; document, manage, and control the integrity of changes to {{ SYSTEM_NAME }}; implement approved changes to {{ SYSTEM_NAME }}; document approved changes to {{ SYSTEM_NAME }}; and track security flaws and flaw resolution within {{ SYSTEM_NAME }}.


### 9.1 Software and Firmware Integrity Verification

Software and firmware integrity verification allows organizations to detect unauthorized changes to software and firmware components using developer-provided tools, techniques, and mechanisms.

{{ ORGANIZATION }} developers enable integrity verification of software and firmware components.


### 9.2 Hardware Integrity Verification

Hardware integrity verification allows organizations to detect unauthorized changes to hardware components using developer-provided tools, techniques, methods, and mechanisms.

{{ ORGANIZATION }} inherits hardware root-of-trust and physical component verification from the Google Cloud Services FedRAMP High / DoD IL5 Provisional Authorization to Operate (P-ATO). At the IaaS/PaaS tier, {{ ORGANIZATION }} enforces hardware integrity via Google Titan security chips, server firmware cryptographic attestation, and Shielded VM virtual Trusted Platform Module (vTPM) with UEFI Secure Boot measurement validation.


### 9.3 Security and Privacy Representatives

{{ ORGANIZATION }} includes security and privacy representatives as part of the Change Control Board (CCB).


## 10. Developer Testing and Evaluation

Developmental testing and evaluation confirm that the required controls are implemented correctly, operating as intended, enforcing the desired security and privacy policies, and meeting established security and privacy requirements.

{{ ORGANIZATION }} developers develop and implement a plan for ongoing security and privacy control assessment; perform unit, integration, system, and regression testing every Annual at Full System Coverage; produce evidence of the execution of the assessment plan and the results of the testing and evaluation event; implement a flaw remediation process; and correct flaws identified during testing and evaluation events.


### 10.1 Static Code Analysis

{{ ORGANIZATION }} developers use CI/CD static security scanners (Semgrep, Checkov, tfsec) and IaC scanners (along with {{ THREAT_DETECTION_ENGINE }} and {{ VULNERABILITY_SCANNER }}) to identify common flaws and document the results of the analysis.


### 10.2 Threat Modeling and Vulnerability Analyses

{{ ORGANIZATION }} developers perform threat modeling and vulnerability analyses during SDLC and the subsequent testing and evaluation events.


## 11. Development Process, Standards, and Tools

Development tools include programming languages and computer-aided design systems. Reviews of development processes can include the use of maturity models to determine the potential effectiveness of such processes. Maintaining the integrity of changes to tools and processes enables accurate supply chain risk assessment and mitigation and requires robust configuration control throughout the life cycle (including design, development, transport, delivery, integration, and maintenance) to track authorized changes and prevent unauthorized changes.

{{ ORGANIZATION }} developers follow a documented process that explicitly addresses security and privacy requirements; identifies the standards and tools in the development process; documents the specific tool options and tool configurations used in the development process; and documents, manages, and ensures the integrity of changes to the processes and/or tools used in development.

{{ ORGANIZATION }} reviews this process as necessary, but at least annually.


### 11.1 Criticality Analysis

Criticality analysis performed by the developer provides input to the criticality analysis performed by organizations. Developer input is essential to organizational criticality analysis because organizations may not have access to detailed design documentation for system components that are developed as commercial off-the-shelf products.

{{ ORGANIZATION }} developers perform a criticality analysis at the following decision points of the SDLC:

- System Concept & Architecture Review Phase
- Component Acquisition & Integration Phase
- Pre-Production Testing & Deployment Phase


## 12. Developer-Provided Training

All {{ ORGANIZATION }} developers are required to take the following training courses to ensure the correct use and operation of implemented security and privacy functions, controls, and mechanisms:

- Secure Software Development & OWASP Top 10 Security Training
- DevSecOps Infrastructure as Code (IaC) & Cloud Security Training
- Supply Chain Risk Management & Container Vulnerability Scanning Training


## 13. Developer Security and Privacy Architecture and Design

{{ ORGANIZATION }} developers produce a security and privacy architecture that is consistent with {{ ORGANIZATION }} enterprise architecture; accurately and completely describes the required security and privacy functionality, and the allocation of controls among physical and logical components; and expresses how individual security and privacy functions, mechanisms, and services work together to provide required security and privacy capabilities and a unified approach to protection.


## 14. Developer Screening

{{ ORGANIZATION }} will ensure all external developers are properly screened and authorized in accordance with applicable federal laws, Executive Orders, directives, policies, regulations, standards, guidelines, and organizational mission/business need.


## 15. Unsupported System Components

Support for system components includes software patches, firmware updates, replacement parts, and maintenance contracts.

{{ ORGANIZATION }} will replace {{ SYSTEM_NAME }} components when the support for the components is no longer available from the developer, vendor, or manufacturer.



## Appendix A – Detailed Compliance Matrix

The following table provides detailed traceability between the policy implementation statements in this document, the authoritative NIST SP 800-53 Rev. 5 control requirements, DoD CCIs, and the technical/governance enforcement mechanisms active across {{ SYSTEM_NAME }}.


| CTRL ID | CTRLTITLE | REQUIRED eMASS STANDARD | DOCREF | ENFORCEMENT MECHANISM |
| :--- | :--- | :--- | :--- | :--- |
| SA-01 | Policy and Procedures | Develops, documents, and disseminates SA policy/procedures to all personnel; designates PM/acquisition authority; reviews annually and upon acquisition pathway/regulation changes or audit gaps. (CCI-000601, CCI-000602, CCI-000603, CCI-000604, CCI-000605, CCI-000606, CCI-000607, CCI-001646, CCI-003089, CCI-003090, CCI-004655, CCI-004656, CCI-004657, CCI-004658, CCI-004659, CCI-004660, CCI-004661, CCI-004662, CCI-004663, CCI-004664, CCI-004665) | Section 2 | Formal eMASS governance publication (System ID: {{ RMF_PACKAGE_ID }}); annual review cadence managed by PM, ISSM, and ISSO; trigger alignment with DoDI 5000.02 and Adaptive Acquisition Framework. |
| SA-02 | Allocation of Resources | Determines security/privacy requirements in planning; allocates resources in CPIC; establishes discrete budget line items for security and privacy. (CCI-000610, CCI-000611, CCI-000612, CCI-000613, CCI-000614, CCI-003091, CCI-004666, CCI-004667, CCI-004668) | Section 3 | Formal {{ ORGANIZATION }} CPIC and POM budget submissions with discrete security line items funding {{ INTERCONNECT_TYPE }} circuits, Cloud KMS HSM, CI/CD security scanners, and security monitoring oversight. |
| SA-03 | System Development Life Cycle | Manages/acquires system using DoD Adaptive Acquisition Framework (Software Acquisition pathway); defines roles; integrates RMF into SDLC. (CCI-000615, CCI-000616, CCI-000618, CCI-003092, CCI-003093, CCI-004669, CCI-004670, CCI-004671, CCI-004672, CCI-004673, CCI-004674, CCI-004675, CCI-004676, CCI-004677, CCI-004678) | Section 4 | AAF Software Acquisition Framework; formal role assignment letters; continuous RMF integration documented in eMASS. |
| SA-03(01) | System Development Life Cycle: Manage Preproduction Environment | Protects preproduction environments commensurate with risk throughout the SDLC. (CCI-004679) | Section 4 | Dedicated lower environment staging and test projects enforcing identical VPC-SC perimeters, IAM conditions, and CMEK encryption. |
| SA-03(02) | System Development Life Cycle: Use of Live or Operational Data | Controls and approves use of live data in preproduction; protects preproduction at same classification/impact level ({{ IMPACT_LEVEL }}) as live data. (CCI-004680, CCI-004681, CCI-004682, CCI-004683) | Section 4 | Synthetic test data pipelines by default; formal ISO/ISSO approval workflow and {{ IMPACT_LEVEL }} security baseline enforcement if operational data is utilized. |
| SA-03(03) | System Development Life Cycle: Technology Refresh | Plans and implements technology refresh schedules throughout SDLC to prevent obsolescence. (CCI-004684, CCI-004685) | Section 4 | Lifecycle refresh schedule for physical edge hardware, virtual security appliances, and container base images managed via Terraform IaC. |
| SA-04 | Acquisition Process | Includes functional, assurance, documentation, SCRM, and acceptance requirements using standardized contract language and FAR/DFARS clauses. (CCI-003094, CCI-003095, CCI-003096, CCI-003097, CCI-003098, CCI-003099, CCI-003100, CCI-004687, CCI-004688, CCI-004689, CCI-004690, CCI-004691, CCI-004692, CCI-004693, CCI-004694, CCI-004695, CCI-004696) | Section 5 | Standardized DoD FAR/DFARS contract clauses, Statements of Work (SOW), and Program Protection Plans (PPP) enforcing cybersecurity baselines. |
| SA-04(01) | Acquisition Process: Functional Properties of Controls | Requires developer to provide description of functional properties of controls to be implemented. (CCI-000623) | Section 5 | Developer functional specifications and security control capability matrices reviewed during RMF Step 2/3. |
| SA-04(02) | Acquisition Process: Design and Implementation Information | Requires developer to provide design info (interfaces, high/low designs, source code, hardware schematics, PPP) sufficient for security reviews. (CCI-003101, CCI-003102, CCI-003103, CCI-003104, CCI-003105, CCI-003106) | Section 5 | {{ SYSTEM_NAME }} Technical Design Document (TDD), Program Protection Plan (PPP), and architecture schematics submitted for SCA review per DoDI 5000.82. |
| SA-04(05) | Acquisition Process: System, Component, and Service Configurations | Requires developer to deliver systems with DoDI 8510.01 / STIGs / CIS GCP Benchmark configurations implemented as defaults. (CCI-003109, CCI-003110, CCI-003111) | Section 5 | Immutable Terraform IaC baseline modules hardcoded with CIS GCP Foundation Benchmark and DISA STIG parameters. |
| SA-04(06) | Acquisition Process: Government Off-the-Shelf / Commercial Solutions | Employs only GOTS/COTS products composing NSA-approved solutions evaluated/validated by NSA. (CCI-000631, CCI-000633) | Section 5 | Deployment of NSA-approved cryptographic algorithms and DISA APL vetted appliances for defense transport. |
| SA-04(07) | Acquisition Process: NIAP-Approved Protection Profiles | Limits commercial IA products to NIAP Protection Profile evaluated products or FIPS 140-3 validated cryptographic modules. (CCI-000634, CCI-000635) | Section 5 | FIPS 140-3 validated Cloud KMS HSM, hardware MACsec engines, and virtual appliance IPsec cryptographic modules. |
| SA-04(09) | Acquisition Process: Functions, Ports, Protocols, and Services in Use | Requires developer to identify all PPS intended for organizational use. (CCI-003114) | Section 5 | Formal {{ SYSTEM_NAME }} PPSM baseline registry tracking all BGP, IPsec, SNMPv3, and telemetry port allocations. |
| SA-04(10) | Acquisition Process: Use of Approved PIV Products | Employs only products on FIPS 201-approved products list for PIV/CAC capabilities. (CCI-003116) | Section 5 | {{ IDENTITY_PROVIDER }} with {{ MFA_MECHANISM }} utilizing certified authenticators and middleware. |
| SA-04(11) | Acquisition Process: System of Records | Includes FAR/DFARS Privacy Act clauses in contracts for operation of a system of records. (CCI-004703, CCI-004704) | Section 5 | Mandatory DFARS Privacy Act clauses incorporated into all {{ SYSTEM_NAME }} vendor procurement agreements per DoDI 5000.82. |
| SA-04(12) | Acquisition Process: Data Ownership | Mandates organizational data ownership and requires all data to be removed and returned by the end of the contract. (CCI-004705, CCI-004706, CCI-004707) | Section 5 | Contractual data ownership clauses enforcing complete data return and verified zero-sanitization upon contract completion. |
| SA-05 | System Documentation | Obtains/develops administrator and user documentation describing secure config, operation, privacy mechanisms, and known vulnerabilities; distributes to ISSO/ISSM. (CCI-000642, CCI-003124, CCI-003125, CCI-003126, CCI-003127, CCI-003128, CCI-003129, CCI-003130, CCI-003131, CCI-003132, CCI-003133, CCI-003135, CCI-003136, CCI-004708, CCI-004709, CCI-004710, CCI-004711) | Section 6 | Comprehensive {{ SYSTEM_NAME }} Administrative Setup Guides, User Manuals, and SOPs published in eMASS and distributed to ISSO/ISSM. |
| SA-08 | Security and Privacy Engineering Principles | Applies systems security and privacy engineering principles (DoD Zero Trust Principles/Tenets) across specification, design, development, implementation, and modification. (CCI-000664, CCI-000665, CCI-000666, CCI-000667, CCI-000668, CCI-004712, CCI-004713, CCI-004714, CCI-004715, CCI-004716) | Section 7 | Systems security engineering documented in the Cybersecurity Strategy (CSS) adhering to NIST SP 800-160 Vol. 1 and DoD Zero Trust Architecture. |
| SA-08(03) | Security and Privacy Engineering Principles: Modularity and Layering | Implements modularity and layering design principles across system components. (CCI-004720, CCI-004721) | Section 7 | Multi-project landing zone topology separating network transport, virtual security inspection, telemetry logging, and automation identities. |
| SA-08(14) | Security and Privacy Engineering Principles: Least Privilege | Implements least privilege across all systems and components. (CCI-004742, CCI-004743) | Section 7 | Granular IAM conditions on Resource Manager tags and labels (e.g. environment: prod, tier: backend), custom roles, and service account actAs restrictions. |
| SA-08(22) | Security and Privacy Engineering Principles: Accountability and Traceability | Implements accountability and traceability across all system components. (CCI-004758, CCI-004759) | Section 7 | GCP Cloud Audit Logs, VPC Flow Logs, and BigQuery Storage Write API logs exported to {{ ORGANIZATION }} NetOps and DISA CSSP. |
| SA-08(23) | Security and Privacy Engineering Principles: Secure Defaults | Implements secure defaults across all system components. (CCI-004760, CCI-004761) | Section 7 | Hardcoded Terraform defaults: private IP addressing, disabled public ingress, Private Google Access, and mandatory CMEK encryption. |
| SA-08(28) | Security and Privacy Engineering Principles: Acceptable Security | Implements acceptable security design principles across all system components. (CCI-004770, CCI-004771) | Section 7 | Balancing multi-cloud routing performance (>99.99% availability) with line-rate MACsec Layer 2 and IPsec Layer 3 encryption. |
| SA-08(33) | Security and Privacy Engineering Principles: Minimization | Implements privacy minimization across all systems collecting/processing PII. (CCI-004780, CCI-004781) | Section 7 | Automated restriction of {{ SYSTEM_NAME }} telemetry data ingestion to network headers and hardware MIBs, excluding end-user PII. |
| SA-09 | External System Services | Requires external service providers to comply with CNSSI 1253 controls; defines oversight and user roles; monitors compliance. (CCI-000669, CCI-003138, CCI-003139, CCI-004782, CCI-004783, CCI-004784, CCI-004785, CCI-004786) | Section 8 | FedRAMP High / DoD IL5 contractual SLAs with Google Cloud; continuous continuous monitoring via NetOps and CSSP. |
| SA-09(01) | External System Services: Risk Assessments and Approvals | Conducts risk assessment; requires DoD Component CIO approval for acquisition of external security services. (CCI-003140, CCI-003141, CCI-003142) | Section 8 | Formal {{ ORGANIZATION }} CIO acquisition approval package based on comprehensive RMF risk assessment. |
| SA-09(02) | External System Services: Functions, Ports, Protocols, and Services | Requires external providers to identify all PPS required for service use. (CCI-003143, CCI-003144) | Section 8 | External provider PPS declarations integrated into the DoD PPSM tracking registry. |
| SA-09(03) | External System Services: Establish and Maintain Trust Relationship | Establishes and maintains trust relationships based on FedRAMP High / DoD IL5 authorization baselines. (CCI-003145, CCI-003146, CCI-003147, CCI-003148, CCI-004787, CCI-004788, CCI-004789, CCI-004790) | Section 8 | Verification of active FedRAMP High / DoD IL5 Provisional Authorization (PA) and DoD ATO for Google Services IL5 (eMASS ID: U:CLOUD:184). |
| SA-09(06) | External System Services: Cryptographic Key Control | Maintains exclusive organizational control of cryptographic keys for encrypted data on external systems. (CCI-004791) | Section 8 | Customer-Managed Encryption Keys (CMEK) generated and stored in dedicated FIPS 140-3 Cloud KMS HSM instances. |
| SA-09(08) | External System Services: Processing and Storage Location | Restricts geographic location of data processing and storage to facilities within U.S. legal jurisdiction. (CCI-004793) | Section 8 | Google Cloud Assured Workloads {{ IMPACT_LEVEL }} organizational policy constraints restricting resource deployment to approved regions. |
| SA-10 | Developer Configuration Management | Performs CM across all SDLC phases for all items in CM plan; manages/controls changes; tracks/reports security flaws to ISSO/ISSM. (CCI-000692, CCI-000694, CCI-003155, CCI-003156, CCI-003157, CCI-003158, CCI-003159, CCI-003160, CCI-003161, CCI-003162, CCI-003163, CCI-003164, CCI-004794) | Section 9 | GitLab version control repositories, automated Terraform pull request change controls, and automated flaw reporting to ISSO/ISSM. |
| SA-10(01) | Developer Configuration Management: Software/Firmware Integrity | Enables integrity verification of software and firmware components. (CCI-000698) | Section 9 | Cryptographic hash verification (SHA-256) and signed container image provenance in Artifact Registry. |
| SA-10(03) | Developer Configuration Management: Hardware Integrity | Enables integrity verification of hardware components. (CCI-003165) | Section 9 | Inherited from Google Cloud Services P-ATO hardware root-of-trust (Titan security chips) and Shielded VM vTPM cryptographic integrity validation. |
| SA-10(06) | Developer Configuration Management: Specifying Master Copies | Executes procedures ensuring distributed updates match master copies exactly. (CCI-003170) | Section 9 | Cryptographically signed release tags and checksum validation pipelines within GitLab CI/CD. |
| SA-10(07) | Developer Configuration Management: Security/Privacy Representatives | Includes ISSM and Privacy Officer on the Configuration Control Board (CCB). (CCI-004795, CCI-004796, CCI-004797) | Section 9 | Formal {{ ORGANIZATION }} CCB charter appointing ISSM and Privacy Officer as mandatory voting members for all baseline changes. |
| SA-11 | Developer Testing and Evaluation | Executes testing plan continuously during builds and prior to production release (unit, integration, system, regression); validates TEMP requirements; remediates flaws. (CCI-003171, CCI-003172, CCI-003173, CCI-003174, CCI-003175, CCI-003176, CCI-003177, CCI-003178, CCI-004798, CCI-004799, CCI-004800) | Section 10 | Automated CI/CD testing pipelines executing unit/integration test suites and TEMP compliance validation before production deployment. |
| SA-11(01) | Developer Testing and Evaluation: Static Code Analysis | Employs static code analysis tools to identify flaws; documents results. (CCI-003179, CCI-003180) | Section 10 | Automated Semgrep, Checkov, and tfsec static analysis embedded in .gitlab-ci-security.yml and cloudbuild-security.yaml. |
| SA-11(02) | Developer Testing and Evaluation: Threat Modeling | Performs threat modeling and vulnerability analyses during development and testing using TEMP methods and threat intel. (CCI-003181, CCI-003182, CCI-004801, CCI-004802, CCI-004803, CCI-004804, CCI-004805, CCI-004806, CCI-004807, CCI-004808) | Section 10 | Formal threat modeling artifacts integrated into the Program Protection Plan (PPP) and TEMP per DoDI 5200.44. |
| SA-11(04) | Developer Testing and Evaluation: Manual Code Reviews | Performs manual code reviews for all critical security functions and cross-classification components per TEMP/CSS. (CCI-003187, CCI-003188, CCI-003189) | Section 10 | Mandatory two-person peer review and approval on all merge requests touching security, IAM, or cryptographic modules. |
| SA-11(05) | Developer Testing and Evaluation: Penetration Testing | Performs penetration testing at breadth/depth and under RoE documented in the approved TEMP. (CCI-003191, CCI-003192, CCI-004812, CCI-004813) | Section 10 | Annual independent penetration testing conducted by certified assessors under formal DoD Rules of Engagement. |
| SA-11(07) | Developer Testing and Evaluation: Verify Scope of Testing | Verifies testing scope provides complete coverage of required controls at rigor defined in TEMP. (CCI-003194, CCI-003195) | Section 10 | Formal Test and Evaluation Master Plan (TEMP) requirement traceability matrices. |
| SA-11(08) | Developer Testing and Evaluation: Dynamic Code Analysis | Employs dynamic code analysis tools to identify common flaws; documents results. (CCI-003196, CCI-003197) | Section 10 | DAST scanning and automated runtime testing of Cloud Run container endpoints. |
| SA-15 | Development Process, Standards, and Tools | Follows documented development process meeting CNSSI 1253; reviews tool options/configurations continuously. (CCI-003234, CCI-003235, CCI-003236, CCI-003237, CCI-003238, CCI-003239, CCI-003240, CCI-003241, CCI-003242, CCI-003243, CCI-003244, CCI-003245, CCI-003246, CCI-004816, CCI-004817, CCI-004818, CCI-004819, CCI-004820, CCI-004821, CCI-004822) | Section 11 | Version-controlled DevSecOps tooling configurations, continuous tool auditing, and CNSSI 1253 security baseline enforcement. |
| SA-15(01) | Development Process, Standards, and Tools: Quality Metrics | Defines quality metrics; provides evidence of meeting metrics upon delivery and at major milestones (PDR/CDR). (CCI-003247, CCI-003248, CCI-003249, CCI-003250) | Section 11 | Formal quality gates and milestone review deliverables tracked in the Defense Acquisition Management System. |
| SA-15(03) | Development Process, Standards, and Tools: Criticality Analysis | Performs criticality analysis during requirements definition and prior to CDR to identify CPI per PPP. (CCI-003254, CCI-003255, CCI-004825, CCI-004826) | Section 11 | Component criticality analysis embedded in the Program Protection Plan (PPP) identifying mission-critical routing and crypto elements. |
| SA-15(05) | Development Process, Standards, and Tools: Attack Surface Reduction | Reduces attack surfaces to the minimum necessary to support mission-essential functions per PPP. (CCI-003272, CCI-003273) | Section 11 | Automated minimization of open ports, disabled public IPs, and strict VPC Service Controls perimeter policies. |
| SA-15(07) | Development Process, Standards, and Tools: Automated Vulnerability Analysis | Executes automated vulnerability analysis continuously using ACAS/scanners; delivers outputs to ISSO/ISSM/PM. (CCI-003275, CCI-003276, CCI-003277, CCI-003278, CCI-003279, CCI-003280, CCI-004827, CCI-004828, CCI-004829, CCI-004830) | Section 11 | Continuous ACAS and CI/CD vulnerability scanning pipelines delivering automated reports to ISSO, ISSM, and PM. |
| SA-15(10) | Development Process, Standards, and Tools: Incident Response Plan | Provides, implements, and tests an incident response plan. (CCI-003289, CCI-004831, CCI-004832) | Section 11 | Developer incident response plan integrated with {{ ORGANIZATION }} NetOps and DISA CSSP continuous monitoring workflows. |
| SA-15(11) | Development Process, Standards, and Tools: Archive System | Archives released system/component together with evidence supporting final security/privacy reviews. (CCI-003290, CCI-004833) | Section 11 | Immutable code and release artifact archiving in Google Cloud Artifact Registry and secure git repositories. |
| SA-15(13) | Development Process, Standards, and Tools: Logging Syntax | Uses secure logging formats (JSON, Syslog RFC 5424, CEF) to log AU-2 events with timestamp, event type, source IP, user ID, and outcome. (CCI-005170) | Section 11 | Automated JSON-formatted structured logging across Cloud Logging, Cloud Run, and BigQuery telemetry sinks. |
| SA-21 | Developer Screening | Requires developers of mission-critical systems with duties requiring classified/CUI access to satisfy additional screening for foreign influence/risks per PPP. (CCI-003381, CCI-003382, CCI-003383, CCI-003385) | Section 14 | Tier 3 / Tier 5 security clearance validation in DISS and contractor personnel vetting against DoD 5000.83 standards. |
| SA-22 | Unsupported System Components | Replaces unsupported components; provides in-house support and isolation when replacement is unavailable. (CCI-003372, CCI-003373, CCI-003376) | Section 15 | Component lifecycle tracking in CMDB; automated container patching; AO-approved ETP isolation for legacy modules. |
| SA-24 | Design for Cyber Resiliency | Designs system to achieve cyber resiliency addressing NIST SP 800-160 Vol. 2 goals, objectives, techniques, approaches, and design principles. (CCI-005176, CCI-005182) | Section 7 | High-availability dynamic BGP ECMP routing, multi-region redundancy (us-east4 / us-central1), automated failover, and decoupled telemetry architecture. |
