# SR - Supply Chain Risk Management Policy and Procedures

## Document Governance & Approval Baseline

| Governance Metric | Policy Standard & Specification |
| :--- | :--- |
| **Document Title** | Supply Chain Risk Management Policy and Procedures |
| **NIST Control Family** | Supply Chain Risk Management (SR) |
| **Primary NIST Benchmark** | NIST SP 800-161 Rev. 1 (Cybersecurity Supply Chain Risk Management Practices) |
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
> This document defines the enterprise security policy and implementation procedures for **Supply Chain Risk Management** under **NIST SP 800-53 Rev. 5 (SR)**.
> Technical infrastructure controls are automatically provisioned and enforced via **{{ SYSTEM_NAME }}** Terraform blueprints.
> Operational rules or contact details requiring manual confirmation are highlighted with RMF Team Callouts.


## 1. Overview

The objective of supply chain risk management (SCRM) is to identify, assess, and mitigate risks to the integrity, trustworthiness, and authenticity of products and services within the supply chain.

This   document   complies   with   the   following   requirements   from   NIST   Special Publication 800-53 Revision 5, "Security and Privacy Controls for Federal Information Systems and Organizations” and is consistent with applicable laws, executive orders, directives, regulations, policies, standards, and guidelines. A detailed compliance matrix can be found in Appendix A, “Detailed Compliance Matrix”.


## 2. Supply Chain Risk Management Plan

The dependence on products, systems, and services from external providers, as well as the nature of the relationships with those providers, present an increasing level of risk to an organization. Threat actions that may increase security or privacy risks include unauthorized production, the insertion or use of counterfeits, tampering, theft, insertion of malicious software and hardware, and poor manufacturing and development practices in the supply chain. Supply chain risks can be endemic or systemic within a system element or component, a system, an organization, a sector, or the Nation. Managing supply chain risk is a complex, multifaceted undertaking that requires a coordinated effort across an organization to build trust relationships and communicate with internal and external stakeholders. SCRM activities include identifying and assessing risks, determining appropriate risk response actions, developing SCRM plans to document response actions, and monitoring performance against plans. The SCRM plan addresses managing, implementation, and monitoring of SCRM controls and the development/sustainment of systems across the system development life cycle (SDLC) to support mission and business functions.


### 2.1 Establish SCRM Team

The SCRM team consists of organizational personnel with diverse roles and responsibilities for leading and supporting SCRM activities, including risk executive, information technology, contracting, information security, privacy, mission or business, legal, supply chain and logistics, acquisition, business continuity, and other relevant functions.

Members of the SCRM team are involved in various aspects of the SDLC and, collectively, have an awareness of and provide expertise in acquisition processes, legal practices, vulnerabilities, threats, and attack vectors, as well as an understanding of the technical aspects and dependencies of systems.


| Role | Responsibility | Point of Contact |
| --- | --- | --- |
| Information System Owner (ISO) | The responsibilities of the ISO are listed, but not limited to the following: - Oversees system supply chain risk strategy and vendor approvals | {{ SO_NAME }} {{ SO_EMAIL }} {{ SO_PHONE }} |
| Program Manager (PM) | The responsibilities of the PM are listed, but not limited to the following: - Manages acquisition contracts and SCRM policy enforcement | {{ SO_NAME }} {{ SO_EMAIL }} {{ SO_PHONE }} |
| Information Systems Security Manager (ISSM) | The responsibilities of the ISSM are listed, but not limited to the following: - Verifies hardware/software provenance and Assured OSS compliance | {{ ISSM_NAME }} {{ ISSM_EMAIL }} {{ ISSM_PHONE }} |



### 2.2 Google Cloud Platform (GCP) Inherited Controls & Shared Responsibility Boundary

- **Google Inherited Controls**: Google Cloud maintains a rigorous Supply Chain Risk Management Program (`SR-3`, `SR-5`), vendor security assessments (`SR-6`), and hardware component provenance verification (`SR-11`).
- **Customer Implementation Responsibilities**: {{ ORGANIZATION }} is responsible for assessing third-party software dependencies (`SR-3`), verifying open-source Terraform module provenance (`SR-4`), and implementing Software Bill of Materials (SBOM) scanning (`SR-11`).

## 3. Supply Chain Controls and Processes

Supply chain elements include organizations, entities, or tools employed for the research and development, design, manufacturing, acquisition, delivery, integration, operations and maintenance, and disposal of systems and system components.

{{ ORGANIZATION }} uses this SCRM plan to establish a process and identify and address weaknesses or deficiencies in the supply chain elements and processes of {{ SYSTEM_NAME }} in coordination with {{ ORGANIZATION }} supply chain personnel.

{{ ORGANIZATION }} works with supply chain personnel to employ controls to protect against supply chain risks to {{ SYSTEM_NAME }} to limit the harm and consequences from supply chain-relevant events.

{{ ORGANIZATION }} uses this SCRM plan to document the selected and implemented supply chain processes and controls.


### 3.1 Diverse Supply Base

Diversifying the supply of systems, system components, and services can reduce the probability that adversaries will successfully identify and target the supply chain and can reduce the impact of a supply chain event or compromise.

{{ ORGANIZATION }} employs a diverse set of sources for {{ SYSTEM_NAME }} components, including multi-zone Google Cloud infrastructure, diverse open-source software libraries verified via Google Assured OSS and DoD Iron Bank, independent multi-vendor DevSecOps scanning tooling (Semgrep, Checkov, Trivy), and redundant multi-supplier integrations.


### 3.2 Limitation of Harm

Controls that can be implemented to reduce the probability of adversaries successfully identifying and targeting the supply chain include avoiding the purchase of custom or non-standardized configurations, employing approved vendor lists with standing reputations in industry, following pre-agreed maintenance schedules and update and patch delivery mechanisms, maintaining a contingency plan in case of a supply chain event, using procurement carve-outs that provide exclusions to commitments or obligations, using diverse delivery routes, and minimizing the time between purchase decisions and delivery.

{{ ORGANIZATION }} implements controls to limit harm from potential adversaries identifying and targeting the organizational supply chain.


### 3.3 Sub-Tier Flow Down

To manage supply chain risk effectively and holistically, it is important that organizations ensure that supply chain risk management controls are included at all tiers in the supply chain. This includes ensuring that Tier 1 (prime) contractors have implemented processes to facilitate the “flow down” of supply chain risk management controls to sub-tier contractors.

{{ ORGANIZATION }} ensures that the implemented controls included in the contracts of prime contractors are also included in the contracts of subcontractors.


## 4. Provenance

Every system and system component has a point of origin and may be changed throughout its existence. Provenance is the chronology of the origin, development, ownership, location, and changes to a system or system component and associated data. It may also include personnel and processes used to interact with or make modifications to the system, component, or associated data.

{{ ORGANIZATION }} documents, monitors, and maintains valid provenance of {{ SYSTEM_NAME }}.


## 5. Acquisition Strategies, Tools, and Methods

{{ ORGANIZATION }} employs the following acquisition strategies, contract tools, and procurement methods to protect against, identify, and mitigate supply chain risks:

- Require vendors to provide Software Bill of Materials (SBOM) and SLSA compliance provenance

- Use verified Google Cloud Assured Open Source Software (Assured OSS) dependencies

- Enforce Binary Authorization container image signing policies prior to production deployment


### 5.1 Adequate Supply

Adversaries can attempt to impede organizational operations by disrupting the supply of critical system components or corrupting supplier operations.

{{ ORGANIZATION }} will ensure adequate supply and availability of critical system components by using multiple suppliers throughout the supply chain, leveraging diverse cloud regions, redundant compute and networking allocations, multi-vendor tooling, and identifying functionally equivalent components or pre-provisioned cloud infrastructure to ensure continuous operation during mission-critical times.


### 5.2 Assessments Prior to Selection, Acceptance, Modification, or Update

{{ ORGANIZATION }} will assess {{ SYSTEM_NAME }} components prior to selection, acceptance, modification, or update.


## 6. Supplier Assessments and Reviews

An assessment and review of supplier risk includes security and supply chain risk management processes, foreign ownership, control or influence (FOCI), and the ability of the supplier to effectively assess subordinate second-tier and third-tier suppliers and contractors.

{{ ORGANIZATION }} will ensure adequate assessments and reviews for supply chain-related risks associated with suppliers or contractors are completed annual supply chain risk assessment review period.


### 6.1 Testing and Analysis

{{ ORGANIZATION }} performs testing and analysis on the supply chain elements, processes, and actors associated with {{ SYSTEM_NAME }}.


## 7. Supply Chain Operations Security

Supply chain OPSEC expands the scope of OPSEC to include suppliers and potential suppliers. OPSEC is a process that includes identifying critical information, analyzing friendly actions related to operations and other activities to identify actions that can be observed by potential adversaries, determining indicators that potential adversaries might obtain that could be interpreted or pieced together to derive information in sufficient time to cause harm to organizations, implementing safeguards or countermeasures to eliminate or reduce exploitable vulnerabilities and risk to an acceptable level, and considering how aggregated information may expose users or specific uses of the supply chain.

{{ ORGANIZATION }} implements OPSEC controls to protect supply chain-related information for {{ SYSTEM_NAME }}.


## 8. Notification Agreements

The establishment of agreements and procedures facilitates communications among supply chain entities. Early notification of compromises and potential compromises in the supply chain that can potentially adversely affect or have adversely affected organizational systems or system components is essential for organizations to effectively respond to such incidents. The results of assessments or audits may include open-source information that contributed to a decision or result and could be used to help the supply chain entity resolve a concern or improve its processes.

{{ ORGANIZATION }} establishes agreements and procedures with entities involved in the supply chain for {{ SYSTEM_NAME }}.


## 9. Tamper Resistance and Detection

Anti-tamper technologies, tools, and techniques provide a level of protection for {{ SYSTEM_NAME }} against many threats, including reverse engineering, modification, and substitution. Strong identification combined with tamper resistance and/or tamper detection is essential to protecting systems and components during distribution and when in use.

{{ ORGANIZATION }} implements a tamper protection program for {{ SYSTEM_NAME }} throughout the entire SDLC.


## 10. Inspection of Systems or Components

The inspection of {{ SYSTEM_NAME }} components for tamper resistance and detection addresses physical and logical tampering and is applied to {{ SYSTEM_NAME }} components removed from organization-controlled areas. Indications of a need for inspection include changes in packaging, specifications, factory location, or entity in which the part is purchased, and when individuals return from travel to high-risk locations.

{{ ORGANIZATION }} inspects {{ SYSTEM_NAME }} components quarterly to detect any instances of tampering.


## 11. Component Authenticity

Sources of counterfeit components include manufacturers, developers, vendors, and contractors. Anti-counterfeiting policies and procedures support tamper resistance and provide a level of protection against the introduction of malicious code.

{{ ORGANIZATION }} implements an anti-counterfeit policy and procedure that includes the means to detect and prevent counterfeit components from entering {{ SYSTEM_NAME }}.


### 11.1 Anti-Counterfeit Training

{{ ORGANIZATION }} will train identified personnel to detect counterfeit system components, to include hardware, software, and firmware.


### 11.2 Configuration Control for Component Service and Repair

{{ ORGANIZATION }} maintains configuration control for components awaiting service and repair or repaired components awaiting return to service.


## 12. Component Disposal

Data, documentation, tools, or system components can be disposed of at any time during the system development life cycle. Proper disposal of system components helps to prevent such components from entering the gray market.

{{ ORGANIZATION }} will dispose of data, documentation, tools, and {{ SYSTEM_NAME }} components using the following techniques and methods:

- Logically wipe and degauss electronic media per NIST SP 800-88

- Physically shred retired storage drives in secure Google facility

- Maintain serial-number-tracked sanitization certificates



## Appendix A – Detailed Compliance Matrix

The following table provides detailed traceability between the policy implementation statements in this document, the authoritative NIST SP 800-53 Rev. 5 control requirements, DoD CCIs, and the technical/governance enforcement mechanisms active across {{ SYSTEM_NAME }}.


| CTRL ID | CTRLTITLE | REQUIRED eMASS STANDARD | DOCREF | ENFORCEMENT MECHANISM |
| :--- | :--- | :--- | :--- | :--- |
| SR-01 | Policy and Procedures | Develops, documents, and disseminates SCRM policy/procedures to PM, SAOP, and key security personnel; designates PM/SO; reviews annually and upon regulation changes or supply chain incidents. (CCI-005056, CCI-005057, CCI-005058, CCI-005059, CCI-005060, CCI-005061, CCI-005062, CCI-005063, CCI-005064, CCI-005065, CCI-005066, CCI-005067, CCI-005068, CCI-005069, CCI-005070, CCI-005071) | Section 1 | Formal eMASS governance publication (System ID: {{ RMF_PACKAGE_ID }}); annual review cadence managed by PM/SO, ISSM, and ISSO; trigger alignment with DoDI 5200.44 and NIST SP 800-161. |
| SR-02 | Supply Chain Risk Management Plan | Develops, documents, and updates SCRM plan annually for all systems and system components across the entire lifecycle. (CCI-005072, CCI-005073, CCI-005074, CCI-005075, CCI-005076) | Section 2 | Formal {{ SYSTEM_NAME }} SCRM Plan embedded in the Program Protection Plan (PPP) and eMASS ATO artifact repository. |
| SR-02(01) | Supply Chain Risk Management Plan: Establish SCRM Team | Establishes multidisciplinary SCRM team (PM, Engineering, Cybersecurity, Intel, Acquisition, Legal) to identify critical components, assess risks, and implement PPP. (CCI-005077, CCI-005078, CCI-005079) | Section 2 | {{ ORGANIZATION }} SCRM Team Charter appointing PM, ISSM, ISSO, and engineering leads per DoDI 5200.44. |
| SR-03 | Supply Chain Controls and Processes | Establishes processes to address supply chain weaknesses; creates/obtains SBOM and hardware inventory for all systems/components. (CCI-005080, CCI-005081, CCI-005082, CCI-005083, CCI-005084, CCI-005085, CCI-005086, CCI-005087, CCI-005088, CCI-005089, CCI-005090) | Section 3 | Automated CI/CD SBOM generation (Syft/Trivy), hardware CMDB tracking, and supply chain vulnerability analysis. |
| SR-03(01) | Supply Chain Controls and Processes: Diverse Supply Base | Employs a diverse set of sources for system components to reduce adversary targeting impact. (CCI-005086) | Section 3 | Cloud-native multi-vendor supply chain diversity: multi-zone GCP topology, DoD Iron Bank container provenance, Google Assured OSS, and multi-vendor DevSecOps scanners. |
| SR-03(02) | Supply Chain Controls and Processes: Limitation of Harm | Implements controls to limit harm from adversaries targeting the supply chain (DISA APL vendors, dual-region redundancy). (CCI-005087) | Section 3 | DISA APL product mandates and active dual-region cloud failover (us-east4 / us-central1). |
| SR-03(03) | Supply Chain Controls and Processes: Sub-Tier Flow Down | Ensures prime contractors flow down all SCRM controls, DFARS clauses, and reporting requirements to subcontractors. (CCI-005095) | Section 3 | Mandatory DFARS flow-down contract clauses incorporated in all {{ SYSTEM_NAME }} prime acquisition agreements. |
| SR-04 | Provenance | Documents, monitors, and maintains valid provenance for all systems, components, and associated data across the lifecycle. (CCI-005096, CCI-005097, CCI-005098, CCI-005099) | Section 4 | Immutable git commit histories, signed release tags, and container provenance metadata stored in Google Artifact Registry. |
| SR-04(03) | Provenance: Validate as Genuine and Not Altered | Validates components as genuine and unaltered using digital signatures, packaging inspection, and anti-counterfeit controls per DoDI 5200.44. (CCI-005104, CCI-005105, CCI-005106, CCI-005107) | Section 4 | Google Binary Authorization cryptographic signature attestation, Artifact Registry provenance, and Google Cloud Services P-ATO physical data center chain of custody. |
| SR-04(04) | Provenance: Supply Chain Integrity: Pedigree | Validates internal composition and pedigree of critical components using chain of custody, trusted supplier network, and SBOM analysis. (CCI-005110, CCI-005111) | Section 4 | Trusted supplier networks, audited chains of custody, and automated SBOM dependency vulnerability analysis. |
| SR-05 | Acquisition Strategies, Tools, and Methods | Employs acquisition strategies and contract tools, including pedigree analysis, SBOM, and SLSA compliance. (CCI-005112, CCI-005113) | Section 5 | Mandatory SLSA Level 3 build pipelines, Google Assured OSS integration, and DoD Iron Bank base container images. |
| SR-05(01) | Acquisition Strategies, Tools, and Methods: Adequate Supply | Ensures adequate supply of critical components by identifying alternative parts and maintaining spare inventory. (CCI-005112) | Section 5 | Pre-provisioned multi-region cloud routing infrastructure, diverse cloud vendor allocations, and automated infrastructure redundancy. |
| SR-05(02) | Acquisition Strategies, Tools, and Methods: Assessments Prior to Selection | Assesses components prior to selection, acceptance, modification, or update. (CCI-005117) | Section 5 | Pre-deployment staging evaluations and CI/CD security scanner gating in preproduction environments. |
| SR-06 | Supplier Assessments and Reviews | Assesses and reviews supply chain risks associated with suppliers at least annually or upon threat intelligence events. (CCI-005118, CCI-005119) | Section 6 | Annual supplier security evaluations, FOCI reviews, and supply chain illumination audits. |
| SR-06(01) | Supplier Assessments and Reviews: Testing and Analysis | Performs testing and analysis on third-party software and configuration templates. (CCI-005119) | Section 6 | Automated SAST (Semgrep) and IaC (Checkov/tfsec) scanning of all external software deliverables. |
| SR-07 | Supply Chain Operations Security | Employs OPSEC controls to protect supply chain information per DoDD 5205.02E. (CCI-005124) | Section 7 | OPSEC handling procedures protecting procurement manifests, infrastructure IaC blueprints, and cloud network topologies. |
| SR-08 | Notification Agreements | Establishes agreements requiring suppliers to notify {{ ORGANIZATION }} immediately (within 24 hrs) of supply chain compromises. (CCI-005124, CCI-005125) | Section 8 | Contractual incident notification clauses requiring 24-hour breach disclosures to the ISSO and Contracting Officer. |
| SR-09 | Tamper Resistance and Detection | Implements tamper protection program across all SDLC stages using anti-tamper tech and physical seals. (CCI-005126) | Section 9 | Google Titan chip hardware attestation, UEFI Secure Boot, and Shielded VM vTPM integrity measurements. |
| SR-09(01) | Tamper Resistance and Detection: Multiple Stages of SDLC | Implements tamper protection controls across multiple stages of the system development life cycle. (CCI-005126) | Section 9 | Multi-stage tamper verification spanning manufacturing receipt, staging, and operational runtime. |
| SR-10 | Inspection of Systems or Components | Inspects components upon receipt, prior to installation, annually, and at random for critical components per PPP. (CCI-005128, CCI-005129, CCI-005130, CCI-005131) | Section 10 | Mandatory receiving dock physical inspections, serial number validation, and cryptographic hash verification. |
| SR-11 | Component Authenticity | Implements anti-counterfeit policies/procedures; restricts procurement to OEMs and authorized distributors. (CCI-005132, CCI-005133, CCI-005134, CCI-005135, CCI-005136) | Section 11 | Authorized distributor sourcing mandates and manufacturer serial database validation. |
| SR-11(01) | Component Authenticity: Anti-Counterfeit Training | Trains personnel to detect counterfeit hardware, software, and firmware. (CCI-005137, CCI-005138) | Section 11 | Annual anti-counterfeiting training for {{ ORGANIZATION }} logistics, procurement, and hardware engineering personnel. |
| SR-11(02) | Component Authenticity: Configuration Control for Service and Repair | Maintains configuration control over all components awaiting service/repair or return to service. (CCI-005139, CCI-005140, CCI-005141) | Section 11 | Strict repair chain of custody, baseline re-STIGging, and firmware signature re-verification upon return to service. |
| SR-12 | Component Disposal | Disposes of data, tools, and components IAW NIST SP 800-88 Rev. 1 media sanitization and NSA guidelines. (CCI-005144, CCI-005145, CCI-005146) | Section 12 | Serial-number-tracked degaussing/shredding in Google IL5 facilities and Cloud KMS cryptographic erasure. |
