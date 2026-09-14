# RA - Risk Assessment Policy and Procedures

## Document Governance & Approval Baseline

| Governance Metric | Policy Standard & Specification |
| :--- | :--- |
| **Document Title** | Risk Assessment Policy and Procedures |
| **NIST Control Family** | Risk Assessment (RA) |
| **Primary NIST Benchmark** | NIST SP 800-30 Rev. 1 (Guide for Conducting Risk Assessments), NIST SP 800-39 |
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
> This document defines the enterprise security policy and implementation procedures for **Risk Assessment** under **NIST SP 800-53 Rev. 5 (RA)**.
> Technical infrastructure controls are automatically provisioned and enforced via **{{ SYSTEM_NAME }}** Terraform blueprints.
> Operational rules or contact details requiring manual confirmation are highlighted with RMF Team Callouts.


## 1. Overview

Federal agencies and organizations cannot protect the confidentiality, integrity, and availability of information in today’s highly networked systems without ensuring that all individuals involved in using and managing:

- Understand their roles and responsibilities related to the organizational mission;

- Understand the organization’s IT security policy, procedures, and practices; and

- Have at least adequate knowledge of the various management, operational, and technical controls required and available to protect IT resources for which they are responsible.

This Risk Assessment Plan follows the risk assessment procedures outlined in NIST SP 800-30 “Guide for Conducting Risk Assessments”, as pictured below:


### 1.1 Scope

The Risk Assessment Plan outlines the framework for risk assessments. This applies to employees, federal contractors, and third party users who handle sensitive information or operate within {{ SYSTEM_NAME }} information technology infrastructure.

The purpose of this Risk Assessment Plan is to establish a comprehensive framework for effectively managing security risks associated with utilizing GCP. While implementing this comprehensive risk assessment and vulnerability scanning controls, this policy safeguards the operations, assets, and data hosted on GCP {{ SYSTEM_NAME }} & {{ SYSTEM_NAME }}, mitigating the potential threats and vulnerabilities, ensuring compliance with any relevant security standards and regulations. By aligning with NIST SP 800-53 revision 5 and NIST 800-30, this policy ensures that {{ ORGANIZATION }} {{ SYSTEM_NAME }} maintains effectively robust risk assessment while maintaining the security posture.

This document complies with the following requirements from NIST Special Publication 800-53 Revision 5, "Security and Privacy Controls for Federal Information Systems and Organizations". A detailed compliance matrix can be found in Appendix A, “Detailed Compliance Matrix”.


### Roles & Responsibilities

The following sections describe the roles and responsibilities for the supporting implementation of this policy:


| Role | Responsibility | Point of Contact |
| --- | --- | --- |
| Information System Owner (ISO) | The responsibilities of the ISO are listed, but not limited to the following: - Defines the mission, objectives, and requirements of {{ SYSTEM_NAME }} - Allocate resources and budget for the implementation and maintenance of security controls and measures for {{ SYSTEM_NAME }} - Assesses all risks within {{ SYSTEM_NAME }} and protects sensitive information and is responsible for the security, functionality, and performance of {{ SYSTEM_NAME }} - Ensures that appropriate risk management practices are in compliance with relevant laws, regulations, policies, and standards, and are implemented and maintained throughout {{ SYSTEM_NAME }} - Ensure compliance with relevant risk assessment security policies, regulations, and contractual obligations governing the use of {{ SYSTEM_NAME }} - Review and approve security plans, risk assessments, and other security-related documentation for {{ SYSTEM_NAME }} | {{ SO_NAME }} {{ SO_EMAIL }} {{ SO_PHONE }} |
| Program Manager (PM) | The responsibilities of the PM are listed, but not limited to the following: - Serves as the central point of communication across all teams to share risk assessment results through {{ SYSTEM_NAME }}, management teams, applicable stakeholders, and other applicable third-parties - Enforcing risk assessment timelines and managing critical resources - Overseeing and approving risk assessment documentation, reporting, and risk mitigations | {{ SO_NAME }} {{ SO_EMAIL }} {{ SO_PHONE }} |
| Information Systems Security Manager (ISSM) | The responsibilities of the ISSM are listed, but not limited to the following: - Serves as the cybersecurity advisor to the AO, PM, and ISO - Directing the development, documentation, approval, and dissemination of the risk assessment plan, policies, and procedures - Coordinating with various ISSO/ISSEs to ensure that {{ SYSTEM_NAME }} is continuously monitored for security-related events and ready for risk assessment procedures - Assessing any proposed configuration changes for potential impact to the cybersecurity posture - Oversees and ensures that the risk assessment policies and procedures are reviewed and updated, as needed, but not less than annually - Provides direct strategic direction and support for risk assessment and vulnerability scanning initiatives within {{ SYSTEM_NAME }} | {{ ISSM_NAME }} {{ ISSM_EMAIL }} {{ ISSM_PHONE }} |
| RMF Team | The responsibilities of the RMF team are listed, but not limited to the following: - Conducting vulnerability scans in conjunction with applicable stakeholders - Maintaining, reporting, and monitoring vulnerabilities within {{ SYSTEM_NAME }} | {{ ISSO_NAME }} {{ ISSO_EMAIL }} {{ ISSO_PHONE }} |
| Authorizing Official | Senior official or executive with the authority to formally assume responsibility and accountability for operating a system; providing common controls inherited by organizational systems; or using a system, service, or application from an external provider. The authorizing official is the only organizational official who can accept the security and privacy risk to organizational operations, organizational assets, and individuals. | {{ AO_NAME }} {{ AO_EMAIL }} {{ AO_PHONE }} |
| Security Control Assessors (SCA) | Individual, group, or organization responsible for conducting a comprehensive assessment of implemented controls and control enhancements to determine the effectiveness of the controls (i.e., the extent to which the controls are implemented correctly, operating as intended, and producing the desired outcome with respect to meeting the security and privacy requirements for the system and the organization). | Designated 3PAO / SCA Assessment Team [CONFIG_REQUIRED: SCA Point of Contact] |


## 2. Policy and Procedures

Risk assessment policy and procedures address the controls in the Risk Assessment family that are required to be implemented within systems and their supporting organizations. The risk management strategy is an important factor in establishing such policies and procedures. Policies and procedures contribute to security and privacy assurance by establishing a baseline of guidance. Therefore, it is imperative that security and privacy stakeholders collaborate on the development of risk assessment policy and procedures. Security and privacy program policies and procedures at the organization level are preferable, in general, and may obviate the need for mission- or system-specific policies and procedures.

All {{ ORGANIZATION }} systems must adhere to the minimum requirements outlined in this policy and have the freedom to increase the standards, restrictions, or directed security controls, but never lessen these measures.



### 2.1 Google Cloud Platform (GCP) Inherited Controls & Shared Responsibility Boundary

- **Google Inherited Controls**: Google Cloud conducts continuous vulnerability assessments (`RA-5`) and risk evaluations across all physical datacenters, hypervisors, and core CSP infrastructure.
- **Customer Implementation Responsibilities**: {{ ORGANIZATION }} is responsible for conducting annual Risk Assessments (`RA-3`), automated container/VM vulnerability scanning via Artifact Registry / SCC (`RA-5`), and remediating identified risk findings (`RA-5`).

## 3. Security Categorization

Security categorization provides a structured way to determine the criticality of the information being processed, stored, and transmitted by a system. Through this process, the potential adverse impacts or negative consequences to organizational operations, organizational assets, and individuals can be defined. Security categorization is also a type of asset loss characterization in systems security engineering processes that is carried out throughout the system development life cycle to ensure that confidentiality, integrity, and availability are appropriately maintained.

When composing what the security categorization the {{ ORGANIZATION }} {{ SYSTEM_NAME }} system will be, {{ ORGANIZATION }} cybersecurity teams will involve the AO and ISO to ensure information types that are processed, traverse, or stored on the system are clearly identified and protected commensurately.  Information types will be documented on the most current template of the FIPS 199 Security Categorization Documentation’s office. Additionally, {{ ORGANIZATION }} will consult with and obtain concurrence with the {{ ORGANIZATION }} Cybersecurity Team on the information types and categorization document prior to submitting for approval.

{{ ORGANIZATION }} will support any meeting requests by {{ ORGANIZATION }} Cybersecurity Team, AO Office SCARs, SCAs, or AO that precede or follow the signature of the categorization form by the AO.

When selecting information types to support system categorization, {{ ORGANIZATION }} systems may refer to the following documents:

- NIST SP 800-60v2, for information type definitions

- CNSSI 1253, for information type definitions as they apply to National Security Systems (NSS)

- FIPS 199 & 200, for how to conduct categorizations.  Available from NIST

- {{ SYSTEM_NAME }} Categorization Form

All {{ ORGANIZATION }} systems, regardless of the security domain in which it is operated, are understood to process, transport, or store at a minimum, {{ SENSITIVITY_CLASSIFICATION }}.  It is, therefore, {{ ORGANIZATION }} policy that all systems, in compliance with reference iii, will have a security impact level of {{ FIPS_199_CATEGORIZATION }} for Confidentiality, Integrity, and Availability (CIA).


## 4. Risk Assessment

Risk Assessments are a multiple step process designed to examine a system's threats, vulnerabilities, and their associated impact.  At a high level, these steps include:

- Preparing for the assessment

  - Identify the purpose of the assessment;

  - Identify the scope of the assessment;

  - Identify the assumptions and constraints associated with the assessment;

  - Identify the sources of information to be used as inputs to the assessment; and

  - Identify the risk model and analytic approaches to be employed during the assessment.

- Conducting the assessment

  - Identify threat sources that are relevant to cloud organizations;

  - Identify threat events that could be produced by those sources;

  - Identify vulnerabilities within organizations that could be exploited by threat sources through specific threat events and the predisposing conditions that could affect successful exploitation;

  - Determine the likelihood that the identified threat sources would initiate specific threat events and the likelihood that the threat events would be successful;

  - Determine the adverse impacts to organizational operations and assets, individuals, other organizations, and the Nation resulting from the exploitation of vulnerabilities by threat sources (through specific threat events); and

  - Determine information security risks as a combination of likelihood of threat exploitation of vulnerabilities and the impact of such exploitation, including any uncertainties associated with the risk determinations.

- Communicating results

  - Communicate the risk assessment results; and

  - Share information developed in the execution of the risk assessment, to support other risk management activities.

- Periodic monitoring and reassessment

  - Monitor risk factors identified in the risk assessment on an ongoing basis and understand the subsequent changes to those factors; and

  - Update the components of risk assessments reflecting the monitoring activities carried out by organizations.

As implied by the listed steps, risk assessments are not static or permanent but, instead, worked continuously to actively manage the risks related to a system, or an organization while minimizing the overall impact.  When assessing risk, more than simply the threat or specific vulnerability are examined.  The threat source and the likelihood of exploitation must also be considered.  For {{ ORGANIZATION }}, threat sources may include:

- Insider threats (contractors, government civilians, active-duty personnel)

- Foreign nationals such as from Russia or China

- Activists

- Environmental

- Untrained users

- Opportunists

The likelihood of a vulnerability being exploited and having an impact on an {{ ORGANIZATION }} system(s) must also be considered when conducting a risk assessment.  The likelihood is a qualitative judgment of the potential a threat has to materialize.  Topics to consider when judging the likelihood may include such things as access to resources, funding levels, motivations, and existing mitigations that may be in place.

{{ ORGANIZATION }} Systems may conduct risk assessments at all three levels in the risk management hierarchy (i.e., organization level, mission/business process level, or information system level) and at any stage in the system development life cycle. Risk assessments will also be conducted at various steps in the Risk Management Framework, including preparation, categorization, control selection, control implementation, control assessment, authorization, and control monitoring. Risk assessment is an ongoing activity carried out throughout the system development life cycle.

Risk assessments can also address information related to the system, including system design, the intended use of the system, testing results, and supply chain-related information or artifacts. Risk assessments can play an important role in control selection processes, particularly during the application of tailoring guidance and in the earliest phases of capability determination.

{{ ORGANIZATION }} systems will create a Risk Assessment Report (RAR) that contains an executive summary; detailed risk assessment results; and supporting appendices.

{{ ORGANIZATION }} will remain updated on all-source intelligence in order to inform various stakeholders of identified risks, and help inform risk management decisions. The threat awareness information that is gathered from all-source intelligence, feeds into the organization's information security operations to help refine processes and procedures in response to the changing environment.


### 4.1 Supply Chain Risk Assessment

Supply chains provide systems with critical resources required to complete their missions.  This can be in the form of hardware, software, or other resources making them ideal targets for threat actors.  Supply chain-related events include disruption, use of defective components, insertion of counterfeits, theft, malicious development practices, improper delivery practices, and insertion of malicious code. These events can have a significant impact on the confidentiality, integrity, or availability of a system and its information and, therefore, can also adversely impact organizational operations (including mission, functions, image, or reputation), organizational assets, individuals, other organizations, and the Nation. Supply chain-related events may be unintentional or malicious and can occur at any point during the system life cycle. An analysis of supply chain risk can help an organization identify systems or components for which additional supply chain risk mitigations are required.

> [!IMPORTANT]
> <mark style="background-color: #fff9c4; color: #b71c1c; font-weight: bold; padding: 2px 6px; border-radius: 4px;">RMF TEAM ACTION REQUIRED: Verify and update operational contact/procedure details in this section.</mark>
> {{ ORGANIZATION }} systems are required to identify any supply chain related risks that could be present in the system. To assist in limiting the potential risk, only hardware and or software that has been approved by DISA or authorized for use by an Authorizing Official via a risk assessment, Security Impact Assessment (SIA).  Monitoring of the supply chain and updates to the supply chain risk assessment will take place at regular intervals based on:

- Significant changes to the supply chain;

- Changes to the system, environments in which they operate;

- Or other changes/conditions necessitate changes in the supply chain.


### 4.2 Use of All-Source Intelligence & Dynamic Threat Awareness

{{ ORGANIZATION }} will remain updated on all-source intelligence in order to inform various stakeholders of identified risks, and help inform risk management decisions. The threat awareness information that is gathered from all-source intelligence feeds into the organization's information security operations to help refine processes and procedures in response to the changing environment.


## 5. Vulnerability Monitoring & Scanning

{{ ORGANIZATION }} will conduct regular vulnerability scans of {{ SYSTEM_NAME }} and {{ SYSTEM_NAME }} at least Weekly automated scans.

{{ ORGANIZATION }} uses {{ VULNERABILITY_SCANNER }} and CI/CD automated vulnerability scanners (along with {{ SCC_STATUS }} where deployed) to automatically scan for vulnerabilities.

The vulnerability scan results are promptly analyzed to identify vulnerabilities and prioritize remediation efforts based on severity ratings. Scan results and any residual risks / findings are stored  and reviewed, as needed, for vulnerability comparisons.

{{ VULNERABILITY_MANAGEMENT_IMPLEMENTATION }}


### 5.1 Update Vulnerabilities to be Scanned

Using automated vulnerability feeds from {{ VULNERABILITY_SCANNER }} and CI/CD scanners, {{ ORGANIZATION }} remains updated on new vulnerabilities.


### 5.2 Discoverable Information

In supported enclaves, {{ THREAT_DETECTION_ENGINE }} ({{ SCC_STATUS }}) is configured to collect comprehensive vulnerability information about GCP resources.

Security scanners discover information to help promptly identify potential and current security flaws, vulnerabilities, and security misconfigurations.


### 5.3 Privileged Access

Vulnerability Scanning can be conducted in one of two methods – credentialed and uncredentialed.  Each has value in determining the cybersecurity posture of a given system or application.  Credentialed, or credentialed, vulnerability scans are intrusive to some systems but necessary to access system registries, indexes, installed software versioning and patch levels, ports, protocols, and installed services.  Without privileged access, the scan job is “uncredentialed” and does not contain the complete picture of potential vulnerability that exists on a given system.  Uncredentialed scans do have value in that they can depict what a threat actor may have access to when trying to compromise systems.  With rapidly advancing attack methods being used by threat actors, it is commonly recognized that this value is fleeting at best.

{{ ORGANIZATION }}, where the capability exists, will conduct “credentialed” privileged access vulnerability scans.  To facilitate this, FIPS 199 Security Categorization Documentation agents will be deployed to physical and virtual hosts that support its installation to allow scans to operate as a service in the background. Network based hosts that use privilege escalation will have their scans conducted with the escalating password as necessary.  For example, to gain the necessary privileged access on network appliances or routers, privileged administrative credentials must be used with an authorized account to successfully complete the scan job.

To achieve this task, {{ ORGANIZATION }} will conduct proper coordination to ensure that the proper administrative level permissions are made available for {{ VULNERABILITY_SCANNER }}, CI/CD pipelines, and Artifact Registry Scanner (and {{ SCC_STATUS }} where deployed). Results of these scans will be treated at the same classification level as the system

### 5.4 Correlate Scanning Information

{{ ORGANIZATION }} can use attack trees to show how hostile activities by adversaries interact and combine to produce adverse impacts or negative consequences to {{ SYSTEM_NAME }}. This information, together with correlated threat intelligence data provides greater clarity regarding multi-vulnerability and multi-hop attack vectors.

It is extremely important to use correlated information when transitioning from older to newer technologies.


### 5.5 Public Disclosure Program

The [Public Vulnerability Disclosure Channel](https://cloud.google.com/security/vulnerability-reporting) is publicly discoverable and contains clear language authorizing good-faith security research.

> [!IMPORTANT]
> <mark style="background-color: #fff9c4; color: #b71c1c; font-weight: bold; padding: 2px 6px; border-radius: 4px;">RMF TEAM ACTION REQUIRED: Verify and update operational contact/procedure details in this section.</mark>
> {{ ORGANIZATION }} Cybersecurity Team will establish a distribution email group to be used for the disclosure/submittal of new vulnerabilities that have been identified on {{ ORGANIZATION }} {{ SYSTEM_NAME }}.  The {{ ORGANIZATION }} Cybersecurity team will then work with the affected system to verify the vulnerability is present.  Upon successful verification the {{ ORGANIZATION }} Cybersecurity Team will work with the cybersecurity team ISSO or ISSM of the affected system to:

- Ensure that a POA&M is created for tracking all actions related to the vulnerability if it cannot be immediately resolved.

- Ensure proper mitigations that address the vulnerability are put into place.

- Review actions tracking the vulnerability.

- Work to verify the vulnerability has been resolved once the system believes it to be so.


## 6. Risk Response

Organizations have many options for responding to risk including any of the following:

- Mitigating risk by implementing new controls or strengthening existing controls,

- Accepting risk with appropriate justification or rationale,

- Sharing and/or transferring risk, or

- Avoiding/rejecting risk.

The risk tolerance of {{ ORGANIZATION }} influences risk response decisions and actions. Risk response addresses the need to determine an appropriate response to risk before generating a plan of action and milestones entry. For example, the response may be to accept risk or reject risk, or it may be possible to mitigate the risk immediately so that a plan of action and milestones entry is not needed. However, if the risk response is to mitigate the risk, and the mitigation cannot be completed immediately, a plan of action and milestones entry is generated.

{{ ORGANIZATION }} will respond to risk(s) that have been identified by assessments (security and/or privacy), disclosure through the {{ ORGANIZATION }} public disclosure program, vulnerability scans, SCAP scans, and/or other systems.  Risks that cannot immediately be remediated, mitigated, or are only partially mitigated will be tracked via a Plan of Action and Milestones (POA&M) and recorded in {{ RMF_GOVERNANCE_SYSTEM }}. This tracking will be performed until the risk is mitigated to an acceptable level of risk or fully remediated.


## 7. Criticality Analysis

Not all system components, functions, or services necessarily require significant protections. Systems engineers conduct a functional decomposition of a system to identify mission-critical functions and components. The functional decomposition includes the identification of organizational missions supported by the system, decomposition into the specific functions to perform those missions, and traceability to the hardware, software, and firmware components that implement those functions, including when the functions are shared by many components within and external to the system.

The operational environment of a system or a system component may impact the criticality, including the connections to and dependencies on cyber-physical systems, devices, system-of-systems, and outsourced IT services. System components that allow unmediated access to critical system components or functions are considered critical due to the inherent vulnerabilities that such components create. Component and function criticality are assessed in terms of the impact of a component or function failure on the organizational missions that are supported by the system that contains the components and functions.

For {{ ORGANIZATION }} {{ SYSTEM_NAME }}, initial criticality analysis is conducted and recorded on the FIPS 199 Security Categorization Documentation in terms of the information types and impacts to confidentiality, integrity, and availability as it traverses, is processed, or is stored on {{ ORGANIZATION }} {{ SYSTEM_NAME }}.  As a part of the initial analysis and in addition to the FIPS 199 Security Categorization Documentation, critical systems, components, and functions will be captured and documented in the following documents:

- Hardware/Software List

- Architecture diagrams

- Ports, Protocols, and Services

This analysis continues as the systems are further designed and implemented. Once a system is fully developed and implemented, {{ ORGANIZATION }} will continue to perform criticality analysis whenever an architecture or design is being developed, modified, or upgraded throughout the System Development Life Cycle (SDLC).


## 8. Threat Hunting

Threat hunting is an active means of cyber defense in contrast to traditional protection measures, such as firewalls, intrusion detection and prevention systems, quarantining malicious code in sandboxes, and Security Information and Event Management technologies and systems. {{ ORGANIZATION }} should maintain a proactive approach searching {{ SYSTEM_NAME }} in order to track and disrupt cyber adversaries as early as possible in the attack sequence, and to measurably improve the speed and accuracy of response.



## Appendix A – Detailed Compliance Matrix

The following table provides detailed traceability between the policy implementation statements in this document, the authoritative NIST SP 800-53 Rev. 5 control requirements, DoD CCIs, and the technical/governance enforcement mechanisms active across {{ SYSTEM_NAME }}.


| CTRL ID | CTRLTITLE | REQUIRED eMASS STANDARD | DOCREF | ENFORCEMENT MECHANISM |
| :--- | :--- | :--- | :--- | :--- |
| RA-01 | Policy and Procedures | Develops, documents, and disseminates RA policy/procedures to ISSO/ISSM/security staff; designates Senior RMF Official; reviews annually and upon policy changes, tool adoption, or audit findings. (CCI-001037, CCI-001038, CCI-001039, CCI-001040, CCI-001041, CCI-001042, CCI-001043, CCI-001044, CCI-002368, CCI-002369, CCI-004603, CCI-004604, CCI-004605, CCI-004606, CCI-004607, CCI-004608, CCI-004609, CCI-004610, CCI-004611, CCI-004612, CCI-004613) | Section 2 | Formal policy publication in eMASS (System ID: {{ RMF_PACKAGE_ID }}); annual review cadence managed by Senior RMF Official, ISSM, and ISSO; trigger alignment with NIST SP 800-30 and DoDI 8510.01. |
| RA-02 | Security Categorization | Categorizes system and information ({{ FIPS_199_CATEGORIZATION }}: {{ IMPACT_LEVEL }}); documents results and rationale in SSP; obtains AO review and approval. (CCI-001046, CCI-001047, CCI-004614, CCI-004615, CCI-004616) | Section 3 | Formal FIPS 199 Security Categorization Form signed by AO ({{ AO_NAME }}); documentation embedded in eMASS SSP baseline. |
| RA-03 | Risk Assessment | Conducts risk assessments identifying threats/vulnerabilities and harm; documents in RAR, SSP, and POA&M; reviews results as received; disseminates to ISSM/ISSO/AO/PM; updates annually. (CCI-001048, CCI-001049, CCI-001050, CCI-001051, CCI-001052, CCI-001053, CCI-001642, CCI-002370, CCI-002371, CCI-004618, CCI-004619, CCI-004620, CCI-004621, CCI-004622, CCI-004623) | Section 4 | NIST SP 800-30 Risk Assessment Report (RAR) workflows; automated POA&M tracking in eMASS; quarterly risk briefing to AO and PM. |
| RA-03(01) | Risk Assessment: Supply Chain Risk Assessment | Assesses supply chain risks for all systems, components, and services; updates at least annually and upon supply chain changes. (CCI-004624, CCI-004625, CCI-004626, CCI-004627) | Section 4.1 | DISA APL hardware and appliance vetting; NDAA Section 889 compliance verification; CI/CD SBOM and dependency scanning. |
| RA-03(02) | Risk Assessment: Use of All-Source Intelligence | Integrates all-source intelligence to assist in risk analysis. (CCI-004628) | Section 4.2 | Integration of cyber threat intelligence feeds from USCYBERCOM, DIA, NSA, and {{ CSSP_PROVIDER }} into threat models. |
| RA-03(03) | Risk Assessment: Dynamic Threat Awareness | Determines cyber threat environment on an ongoing basis using vulnerability assessments, malware protection, continuous monitoring, incident handling, UAM, and AS&W per DoDI 8530.01. (CCI-004629, CCI-004630) | Section 4.2 | 24x7 NetOps continuous monitoring, {{ CSSP_PROVIDER }} sensor feeds, automated attack sensing and warning (and {{ THREAT_DETECTION_ENGINE }} alerts). |
| RA-05 | Vulnerability Monitoring and Scanning | Monitors and scans for vulnerabilities continuously and as frequently as practical; uses SCAP standards; analyzes reports; remediates IAW DoD timelines (Critical: 15 days, High: 30 days); shares data with ISSO/ISSM. (CCI-001054, CCI-001055, CCI-001056, CCI-001057, CCI-001058, CCI-001059, CCI-001060, CCI-001061, CCI-001641, CCI-001643, CCI-002376, CCI-004634, CCI-004635, CCI-004636) | Section 5 | Automated CI/CD DevSecOps scanner suite (Semgrep, Checkov, tfsec, Gitleaks, Hadolint), {{ VULNERABILITY_SCANNER }} credentialed scans, and automated POA&M logging. |
| RA-05(02) | Vulnerability Monitoring and Scanning: Update Vulnerabilities to Be Scanned | Updates scanned vulnerabilities at least daily (within 24 hours prior to scans) and upon new threat disclosures. (CCI-001063, CCI-001064) | Section 5.1 | Automated daily {{ VULNERABILITY_SCANNER }} plugin updates and CI/CD security scanner definition synchronization. |
| RA-05(04) | Vulnerability Monitoring and Scanning: Discoverable Information | Determines discoverable system information; takes corrective actions to remove, mask, or encrypt sensitive information and limit exposure per DoDD 5205.02E. (CCI-001066, CCI-002374, CCI-002375) | Section 5.2 | Periodic discovery audits, public IP elimination on Cloud SQL/VPCs, Private Google Access enforcement, and VPC Service Controls perimeters. |
| RA-05(05) | Vulnerability Monitoring and Scanning: Privileged Access | Implements privileged access authorizations across all system components for active vulnerability scanning activities. (CCI-001067, CCI-001645, CCI-002906) | Section 5.3 | Dedicated {{ VULNERABILITY_SCANNER }} credentialed service accounts and administrative SSH/enable keys secured via GCP Secret Manager and PAM. |
| RA-05(11) | Vulnerability Monitoring and Scanning: Public Disclosure Program | Establishes public reporting channel for receiving vulnerability reports from security researchers. (CCI-004640) | Section 5.5 | Integration with DoD Vulnerability Disclosure Program (DC3) and Google Public Vulnerability Disclosure channel. |
| RA-07 | Risk Response | Responds to findings from security/privacy assessments, continuous monitoring, and audits in accordance with risk tolerance. (CCI-004641, CCI-004642, CCI-004643, CCI-004644) | Section 6 | Automated Terraform IaC remediation pipelines, compensating security controls (ETP-{{ SYSTEM_NAME }}-01/02), and formal eMASS POA&M resolution. |
| RA-08 | Privacy Impact Assessments | Conducts PIAs prior to developing/procuring IT or initiating new collections of PII. (CCI-004645, CCI-004646, CCI-004647) | Section 4 | Formal DD Form 2930 Privacy Impact Assessment confirming zero end-user PII processing within {{ SYSTEM_NAME }}. |
| RA-09 | Criticality Analysis | Performs criticality analysis for all systems, components, and services at major milestone decision points across the SDLC. (CCI-004648, CCI-004649, CCI-004650) | Section 7 | Functional decomposition in {{ SYSTEM_NAME }} TDD architecture; component criticality analysis identifying Cloud Routers, virtual network appliances, and KMS HSM as mission-essential. |
| RA-10 | Threat Hunting | Establishes and maintains a continuous (24x7x365) threat hunting capability to search for IoCs and disrupt threats that evade controls. (CCI-004651, CCI-004652, CCI-004653, CCI-004654) | Section 8 | Real-time telemetry streaming to BigQuery, {{ ORGANIZATION }} NetOps behavioral analytics, and accredited 24x7 CSSP continuous threat hunting per DoDI 8530.01. |
