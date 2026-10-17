# PE - Physical and Environmental Protection Policy and Procedures

## Document Governance & Approval Baseline

| Governance Metric | Policy Standard & Specification |
| :--- | :--- |
| **Document Title** | Physical and Environmental Protection Policy and Procedures |
| **NIST Control Family** | Physical and Environmental Protection (PE) |
| **Primary NIST Benchmark** | NIST SP 800-53 Rev. 5 (PE Family), Google Datacenter Physical Security Standards |
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
> This document defines the enterprise security policy and implementation procedures for **Physical and Environmental Protection** under **NIST SP 800-53 Rev. 5 (PE)**.
> Technical infrastructure controls are automatically provisioned and enforced via **{{ SYSTEM_NAME }}** Terraform blueprints.
> Operational rules or contact details requiring manual confirmation are highlighted with RMF Team Callouts.


## 1. Overview

Federal agencies and organizations cannot protect the confidentiality, integrity, and availability of information in today's highly networked systems environment without ensuring that all people involved in using and managing IT:

1. Understand their roles and responsibilities related to the organizational mission;
2. Understand the organization's IT security policy, procedures, and practices; and
3. Have at least adequate knowledge of the various management, operational, and technical controls required and available to protect the IT resources for which they are responsible.

The purpose of this Physical and Environmental Protection Policy is to establish the requirements for controlling physical access to the facilities that house {{ SYSTEM_NAME }} and for protecting those facilities and system components from environmental hazards.

This policy addresses the Physical and Environmental Protection (PE) family requirements of NIST Special Publication 800-53 Revision 5, "Security and Privacy Controls for Information Systems and Organizations." A detailed compliance matrix is provided in Appendix A, "Detailed Compliance Matrix."

The Physical and Environmental Protection Policy encompasses all {{ ORGANIZATION }} users who have access to {{ SYSTEM_NAME }}. This policy outlines the framework for establishing, implementing, and maintaining physical and environmental protection in alignment with applicable {{ GOVERNANCE_REGIME }} guidelines (NIST SP 800-53, FedRAMP, and applicable federal and state regulations), and is consistent with applicable laws, executive orders, directives, regulations, policies, standards, and guidelines. It applies to employees, contractors, and third-party users who handle sensitive information or operate within the {{ ORGANIZATION }} {{ SYSTEM_NAME }} information technology infrastructure.

{{ ORGANIZATION }} management is committed to the requirements of this policy and provides the resources needed to implement them. The ISSM ({{ ISSM_NAME }}) manages the development, documentation, and dissemination of this policy and its procedures, and coordinates their implementation with the Authorizing Official, System Owner, ISSO, and other organizational entities identified in the Program Roles & Responsibilities Matrix.

This policy and its procedures are reviewed and updated at least annually and following significant changes to {{ SYSTEM_NAME }} or its operating environment, security or privacy incidents, assessment or audit findings, or changes in applicable laws, executive orders, directives, regulations, policies, standards, or guidelines.

### 1.1 Background

The physical security program is the part of security concerned with active and passive measures that prevent unauthorized access to personnel, equipment, installations, and information, and that safeguard them against espionage, sabotage, terrorism, damage, and criminal activity. Physical security is a primary command responsibility.


## 2. Policy and Procedures

This is a system-level physical and environmental protection policy. It includes procedures to implement the policy and the associated physical and environmental protection controls.

> [!IMPORTANT]
> [WARNING: RMF TEAM ACTION REQUIRED: Verify and update operational contact/procedure details in this section.]
> This policy has been disseminated to the {{ ORGANIZATION }} system team, ISSO, and ISSM via {{ RMF_GOVERNANCE_SYSTEM }}. It is reviewed and updated as described in Section 1.

### 2.1 Google Cloud Platform (GCP) Inherited Controls & Shared Responsibility Boundary

- **Google Inherited Controls**: Google Cloud provides inherited physical security (`PE-2`, `PE-3`), biometric access control, 24x7 security guard patrols, fire suppression (`PE-13`), climate control (`PE-14`), and water damage protection (`PE-15`) across all Google data centers.
- **Customer Implementation Responsibilities**: {{ ORGANIZATION }} operates entirely within the cloud environment and inherits physical security controls from Google Cloud. {{ ORGANIZATION }} is responsible for securing physical access to customer-owned endpoint laptops and workstations used to access the cloud console.

## 3. Physical Access Authorizations

Development, approval, and maintenance of the facility access list, issuance of access credentials, review of the access list ({{ ODP_PE_2_REVIEW_FREQ }}), and removal of individuals who no longer need access are fully inherited from Google Cloud.


## 4. Physical Access Control

Enforcement of physical access authorizations at facility entry and exit points, physical access control systems, and visitor escort and monitoring are fully inherited from Google Cloud.


## 5. Access Control for Transmission

Physical protection of system distribution and transmission lines within Google data centers is fully inherited from Google Cloud.


## 6. Access Control for Output Devices

Physical access control for output devices in Google data centers is fully inherited from Google Cloud. {{ SYSTEM_NAME }} has no physical output devices in its cloud environment.


## 7. Monitoring Physical Access

Monitoring of physical access to Google data centers, including physical intrusion alarms and surveillance equipment, is fully inherited from Google Cloud.


## 8. Visitor Access Records

Maintenance and review of visitor access records for Google data centers are fully inherited from Google Cloud. Where {{ ORGANIZATION }} keeps visitor access records for its own facilities, the records contain only the personally identifiable information (PII) elements identified in the privacy risk assessment.


## 9. Power Equipment and Cabling

Protection of power equipment and power cabling is fully inherited from Google Cloud.


## 10. Emergency Shutoff

The capability to shut off power to {{ ORGANIZATION }} {{ SYSTEM_NAME }} components in an emergency is fully inherited from Google Cloud.


## 11. Emergency Power

Emergency power capabilities and capacity are fully inherited from Google Cloud.


## 12. Emergency Lighting

Emergency lighting capabilities are fully inherited from Google Cloud.


## 13. Fire Protection

Fire detection and suppression systems, including their automatic activation and notification, are fully inherited from Google Cloud.


## 14. Environmental Controls

All environmental controls are fully inherited from Google Cloud.


## 15. Water Damage Protection

Water damage protection, including accessible and working master shutoff or isolation valves, is fully inherited from Google Cloud.


## 16. Delivery and Removal

Authorization and control of system components entering and exiting Google data centers, and the records of those components, are fully inherited from Google Cloud.


## 17. Alternate Work Site

Alternate work sites are not inherited from Google Cloud. {{ ORGANIZATION }} determines and documents in its COOP plan the alternate work sites, such as telework locations, that its personnel may use. Personnel at alternate work sites use government-furnished equipment (GFE) and connect through {{ IDENTITY_PROVIDER }} with {{ MFA_MECHANISM }} and context-aware access restrictions, and they report incidents to security and privacy staff through the {{ ORGANIZATION }} security operations communication channels.

[CONFIG_REQUIRED: Method and frequency for assessing the effectiveness of controls at alternate work sites]


## 18. Facility Location and Location of System Components

Selection of facility sites, and positioning of system components within facilities to minimize damage from physical and environmental hazards and the opportunity for unauthorized access, are fully inherited from Google Cloud. {{ ORGANIZATION }} considers physical and environmental hazards when selecting the Google Cloud regions that host {{ SYSTEM_NAME }}.


## 19. Component Marking

Marking of hardware components in Google data centers is inherited from Google Cloud. Where {{ ORGANIZATION }} operates on-premises or colocation equipment for {{ SYSTEM_NAME }}, such as {{ INTERCONNECT_TYPE }} network racks, it marks that equipment with the impact level ({{ IMPACT_LEVEL }}). {{ ORGANIZATION }} labels cloud resources with the data classification ({{ SENSITIVITY_CLASSIFICATION }}) through Terraform.



## Appendix A – Detailed Compliance Matrix

The following table provides detailed traceability between the policy implementation statements in this document, the authoritative NIST SP 800-53 Rev. 5 control requirements, DoD CCIs, and the technical/governance enforcement mechanisms active across {{ SYSTEM_NAME }}.


| CTRL ID | CTRLTITLE | REQUIRED {{ GRC_STANDARD_LABEL }} STANDARD | DOCREF | ENFORCEMENT MECHANISM |
| :--- | :--- | :--- | :--- | :--- |
| PE-01 | Policy and Procedures | Develops, documents, and disseminates PE policy and procedures to the system team, ISSO, and ISSM; designates the ISSM to manage them; reviews and updates them at least annually and following significant system changes, security or privacy incidents, assessment or audit findings, or changes in applicable laws, regulations, or guidance. (CCI-000904, CCI-000905, CCI-000906, CCI-000907, CCI-000908, CCI-000909, CCI-000910, CCI-000911, CCI-002908, CCI-002909, CCI-004229, CCI-004230, CCI-004231, CCI-004232, CCI-004233, CCI-004234, CCI-004235, CCI-004236, CCI-004237, CCI-004238, CCI-004239) | Section 1 & 2 | Formal policy workflow published via eMASS (System ID: {{ RMF_PACKAGE_ID }}); annual review cadence managed by the {{ ORGANIZATION }} ISSM with ISSO support; incident triggers aligned with DoDM 5200.08 and federal facility security standards. |
| PE-02 | Physical Access Authorizations | Develops, approves, and maintains authorized facility access list; issues credentials; reviews access lists ({{ ODP_PE_2_REVIEW_FREQ }}); removes access upon termination. (CCI-000912, CCI-000913, CCI-000914, CCI-000915, CCI-001635, CCI-002910, CCI-002911) | Section 3 | Fully inherited from <!-- IF DOD_IL6 -->{{ CSP_INHERITANCE_HEADER }}<!-- ENDIF --><!-- IF NOT DOD_IL6 --><!-- IF DOD_ENCLAVE -->Google Services {{ DOD_IMPACT_SHORT }} (eMASS ID: U:CLOUD:184)<!-- ENDIF --><!-- IF NOT DOD_ENCLAVE -->{{ CSP_INHERITANCE_AUTHORIZATION }}<!-- ENDIF --><!-- ENDIF --> for cloud data centers; physical facility access lists managed in accordance with federal and DoD facility security directives with mandatory 90-day review cadence and automated offboarding. |
| PE-03 | Physical Access Control | Enforces physical access control at facility entry/exit points via guards/biometrics; maintains audit logs; controls publicly accessible areas; escorts/monitors visitors; secures keys; inventories access devices annually; changes combinations/keys upon events. (CCI-000920, CCI-000923, CCI-000924, CCI-000925, CCI-000926, CCI-000927, CCI-002915, CCI-002916, CCI-002917, CCI-002918, CCI-002919, CCI-002920, CCI-002921, CCI-002922, CCI-002923, CCI-002924, CCI-002925, CCI-004240, CCI-004241, CCI-004242, CCI-004243) | Section 4 | Google<!-- IF DOD_ENCLAVE --> {{ DOD_IMPACT_SHORT }}<!-- ENDIF --> data center biometric mantraps, 24x7 armed guards, automated electronic badging, and annual physical access device inventories; on-premises server room keycard controls. |
| PE-03(01) | System Access | Enforces physical access authorizations to the system in addition to facility-level access controls at physical spaces containing system components. (CCI-000928, CCI-002926) | Section 4 | Individually locked server racks, cage partitions with electronic badges in colocation PoPs, and segregated Assured Workloads data halls inherited from Google<!-- IF DOD_ENCLAVE --> {{ DOD_IMPACT_SHORT }}<!-- ENDIF -->. |
| PE-04 | Access Control for Transmission | Controls physical access to system distribution and transmission lines within facilities using security controls and conduit. (CCI-000936, CCI-002930, CCI-002931) | Section 5 | Locked overhead fiber raceways in Google data centers; hardware Layer 2 MACsec encryption on {{ INTERCONNECT_TYPE }} and Layer 3 IPsec encapsulation for all external transit circuits. |
| PE-05 | Access Control for Output Devices | Controls physical access to output from system output devices to prevent unauthorized access. (CCI-000937) | Section 6 | Prohibition of physical output devices in cloud VPCs; serverless Grafana telemetry dashboards protected by {{ IDENTITY_PROVIDER }} with {{ MFA_MECHANISM }} and IAM role restrictions. |
| PE-06 | Monitoring Physical Access | Monitors physical access to facilities to detect/respond to incidents; reviews physical access logs ({{ ODP_PE_6_REVIEW_FREQ }}) and upon security events; coordinates with incident response. (CCI-000939, CCI-000940, CCI-000941, CCI-002939, CCI-002940, CCI-002941) | Section 7 | Google GSOC 24x7 monitoring, automated access logging, 90-day log review cadence, and integration with {{ ORGANIZATION }} NetOps / DISA CSSP <!-- IF DOD_ENCLAVE -->per CJCSM 6510.01B and DoDI 8530.01<!-- ENDIF --><!-- IF NOT DOD_ENCLAVE -->per organizational incident response procedures<!-- ENDIF -->. |
| PE-06(01) | Intrusion Alarms and Surveillance Equipment | Monitors physical access to the facility using physical intrusion alarms and surveillance equipment. (CCI-000942) | Section 7 | Inherited Google<!-- IF DOD_ENCLAVE --> {{ DOD_IMPACT_SHORT }}<!-- ENDIF --> CCTV coverage, laser perimeter sensors, and automated physical intrusion detection systems (PIDS) with continuous recording. |
| PE-06(04) | Monitoring Physical Access to Systems | Monitor physical access to the system in addition to the physical access monitoring of the facility where the system resides. (CCI-002950, CCI-002951) | Section 6 | Inherited from Google Cloud data center multi-layer server floor CCTV, biometric access logs, and rack-level monitoring under the CSP P-ATO. |
| PE-08 | Visitor Access Records | Maintains visitor access records for at least one year IAW NARA GRS; reviews records ({{ ODP_PE_8_REVIEW_FREQ }}); reports anomalies to security personnel. (CCI-000947, CCI-000948, CCI-000949, CCI-002952, CCI-004251, CCI-004252) | Section 8 | Automated visitor logging systems with 1-year retention, quarterly 90-day reviews, and automated anomaly alerting to {{ ORGANIZATION }} ISSO / facility security officers. |
| PE-08(01) | Automated Records Maintenance and Review | Maintain and review visitor access records using automated mechanisms. (CCI-000950, CCI-004253) | Section 8 | Inherited from Google Cloud automated data center visitor management systems and organizational electronic badge/visitor logging systems. |
| PE-08(03) | Limit Personally Identifiable Information Elements | Limits PII elements in visitor access records to the minimum required for identity verification and operational purposes per the PIA. (CCI-004254, CCI-004255) | Section 8 | Mandatory PIA data minimization standards enforcing capture of name, DoD affiliation, badge number, and timestamp only; SSN collection strictly prohibited. |
| PE-09 | Power Equipment and Cabling | Protects power equipment and power cabling from damage, tampering, and physical destruction. (CCI-000952) | Section 9 | Inherited Google<!-- IF DOD_ENCLAVE --> {{ DOD_IMPACT_SHORT }}<!-- ENDIF --> physical electrical infrastructure, subterranean reinforced power routing, armored conduits, and secured electrical utility rooms. |
| PE-10 | Emergency Shutoff | Provides capability of shutting off power in emergency situations; places labeled shutoff switches near more than one IT area egress point; protects from unauthorized activation. (CCI-000956, CCI-000957, CCI-000958, CCI-000959, CCI-004256) | Section 10 | Dual-action Emergency Power Off (EPO) switches installed at multiple egress points, fitted with protective safety shields and anti-tamper alarm monitoring. |
| PE-11 | Emergency Power | Provides uninterruptible power supply (UPS) and long-term alternate power for orderly shutdown or sustained transition. (CCI-002955) | Section 11 | N+1 redundant UPS battery banks and on-site diesel emergency backup generators with 72+ hours of dedicated fuel reserves inherited from Google<!-- IF DOD_ENCLAVE --> {{ DOD_IMPACT_SHORT }}<!-- ENDIF --> data centers. |
| PE-11(01) | Alternate Power Supply — Minimal Operational Capability | Provide an alternate power supply for the system that is activated manually or automatically and can maintain minimally required operational capability in the event of an extended loss of primary power. (CCI-000961) | Section 11 | Inherited from Google Cloud data center N+1/2N redundant utility feeds, UPS battery banks, and on-site diesel generators with multi-day fuel reserves. |
| PE-12 | Emergency Lighting | Employs and maintains automatic emergency lighting that activates during power loss, illuminating exits and evacuation routes. (CCI-000963) | Section 12 | Automated emergency lighting grid backed by independent battery packs and generator backup circuits covering all egress pathways and data halls. |
| PE-13 | Fire Protection | Employs and maintains fire detection and suppression systems supported by an independent energy source. (CCI-000965) | Section 13 | Google<!-- IF DOD_ENCLAVE --> {{ DOD_IMPACT_SHORT }}<!-- ENDIF --> fire protection infrastructure powered by independent emergency circuits and generator backups. |
| PE-13(01) | Detection Systems — Automatic Activation and Notification | Employs automatic fire detection systems that notify designated personnel and emergency responders in the event of a fire. (CCI-002961, CCI-002962, CCI-002963, CCI-002964) | Section 13 | VESDA air-aspirating smoke detection and thermal sensors with automated dispatch to 24x7 GSOC and local municipal fire departments. |
| PE-13(02) | Suppression Systems — Automatic Activation and Notification | Employs automatic fire suppression systems that notify personnel/responders and operate continuously even when facilities are not staffed. (CCI-000968, CCI-002965, CCI-002966, CCI-002967) | Section 13 | Automated clean-agent gaseous fire suppression (FM-200/NOVEC 1230) and pre-action dry-pipe sprinklers with 24x7 autonomous activation and responder notification. |
| PE-13(04) | Inspections | Enforce inspections requirements across {{ SYSTEM_NAME }} in accordance with NIST SP 800-53 Rev. 5 PE-13(4). (CCI-002968, CCI-002969, CCI-002970, CCI-002971) | Section 3 | Enforced via Google Cloud infrastructure controls, Terraform configuration baselines, and ISSM/ISSO governance verification. |
| PE-14 | Environmental Controls | Maintains and continuously monitors temperature and humidity levels within manufacturer specifications. (CCI-000971, CCI-000972, CCI-000973, CCI-000974) | Section 14 | Automated Building Management Systems (BMS) continuously monitoring and regulating HVAC/CRAH temperature and humidity to ASHRAE standards. |
| PE-14(02) | Monitoring with Alarms and Notifications | Maintain environmental monitoring logs that record temperature and humidity levels within facilities housing the system. (CCI-000976, CCI-004258) | Section 14 | Inherited from Google Cloud continuous automated building management system (BMS) environmental telemetry logs audited under the CSP P-ATO. |
| PE-15 | Water Damage Protection | Protects system from water leakage damage; provides accessible, working master shutoff valves; ensures key personnel have knowledge of valves. (CCI-000977, CCI-000978, CCI-000979) | Section 15 | Raised computer room flooring, under-floor moisture detection sensors, accessible and tested master shutoff valves, and personnel emergency training. |
| PE-15(01) | Automation Support | Detect the presence of water in the vicinity of the system and alert designated organizational personnel using automated mechanisms. (CCI-002973, CCI-004259, CCI-004260, CCI-004261) | Section 15 | Inherited from Google Cloud data center automated under-floor/plenum leak-detection sensors and 24x7 facility operations alerting. |
| PE-16 | Delivery and Removal | Authorizes and controls all system components entering/exiting facility; maintains inventory records of components. (CCI-000981, CCI-000983, CCI-000984, CCI-002974) | Section 16 | Secure loading dock inspections, strict bill of lading verification, serial number tracking, and NIST SP 800-88 certified hardware destruction records. |
| PE-17 | Alternate Work Site | Determines and documents allowed alternate work sites per COOP; employs defined security controls at those sites and assesses their effectiveness; provides a means to communicate with security and privacy personnel about incidents. (CCI-000985, CCI-000987, CCI-000988, CCI-002975, CCI-004262, CCI-004263) | Section 17 | Formal {{ ORGANIZATION }} COOP plan authorization, GFE mandates, {{ IDENTITY_PROVIDER }} with {{ MFA_MECHANISM }}, VPC-SC context-aware perimeter restrictions, and security operations communication channels. |
| PE-18 | Location of System Components | Position system components within the facility to minimize potential damage from physical and environmental hazards and to minimize the opportunity for unauthorized access. (CCI-000989, CCI-000991, CCI-002976) | Section 2 | Inherited from Google Cloud secure data center site selection, setback perimeters, and windowless interior server hall placement. |
| PE-22 | Component Marking | Marks hardware processing/output components indicating impact/classification level ({{ IMPACT_LEVEL }} / {{ SENSITIVITY_CLASSIFICATION }}). (CCI-004269, CCI-004270) | Section 19 | Physical classification labels on on-premises/colocation network racks and automated Terraform IaC tagging (classification: {{ SENSITIVITY_CLASSIFICATION }}) on all cloud resources. |
| PE-23 | Facility Location | Plans facility site location considering physical/environmental hazards; incorporates hazard analysis into risk strategy. (CCI-004271, CCI-004272) | Section 18 | Multi-region deployment ({{ PRIMARY_LOCATION }} / {{ SECONDARY_LOCATION }}), geographic disaster hazard vetting by Google/{{ ORGANIZATION }}, and automated BGP ECMP cross-region failover. |
