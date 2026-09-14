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
> This document defines the enterprise security policy and implementation procedures for **Physical and Environmental Protection** under **NIST SP 800-53 Rev. 5 (PE)**.
> Technical infrastructure controls are automatically provisioned and enforced via **{{ SYSTEM_NAME }}** Terraform blueprints.
> Operational rules or contact details requiring manual confirmation are highlighted with RMF Team Callouts.


## 1. Overview

The physical security program is that part of security concerned with active and passive measures designed to prevent unauthorized access to personnel, equipment, installations, information, and to safeguard them against espionage, sabotage, terrorism, damage, and criminal activity. Physical security is a primary command responsibility.

This plan ensures that {{ ORGANIZATION }} implements physical security to preserve the confidentiality, integrity, and availability of {{ ORGANIZATION }} information system resources.

This   document   complies   with   the   following   requirements   from   NIST   Special Publication 800-53 Revision 5, "Security and Privacy Controls for Federal Information Systems and Organizations” and is consistent with applicable laws, executive orders, directives, regulations, policies, standards, and guidelines. A detailed compliance matrix can be found in Appendix A, “Detailed Compliance Matrix”.


## 2. Policy and Procedures

The {{ ORGANIZATION }} Physical and Environmental Protection Policy includes a system-level physical and environmental protection policy that addresses physical and environmental protection’s purpose, scope, roles, responsibilities, management commitment, coordination among organizational entities, and compliance; and is consistent with applicable laws, executive orders, directives, regulations, policies, standards, and guidelines.

The {{ ORGANIZATION }} Physical and Environmental Protection Policy also includes procedures to facilitate the implementation of the physical and environmental protection policy, associated physical and environmental protection controls, and periodic review and update of Physical and environmental protection Policy and procedures.

> [!IMPORTANT]
> <mark style="background-color: #fff9c4; color: #b71c1c; font-weight: bold; padding: 2px 6px; border-radius: 4px;">⚠️ RMF TEAM ACTION REQUIRED: Verify and update operational contact/procedure details in this section.</mark>
> This plan has been disseminated to the {{ ORGANIZATION }} system team, ISSO and ISSM via {{ RMF_GOVERNANCE_SYSTEM }}.  This policy will be updated and/or reviewed, at minimum, on an annual basis



### 2.1 Google Cloud Platform (GCP) Inherited Controls & Shared Responsibility Boundary

- **Google Inherited Controls**: Google Cloud Platform provides 100% inherited physical security (`PE-2`, `PE-3`), biometric access control, 24x7 security guard patrols, fire suppression (`PE-13`), and climate control (`PE-14`, `PE-15`) across all GCP datacenters.
- **Customer Implementation Responsibilities**: {{ ORGANIZATION }} operates entirely within the cloud environment and inherits physical security controls from Google Services. {{ ORGANIZATION }} is responsible for securing physical access to customer-owned endpoint laptops and workstations used to access the cloud console.

## 3. Physical Access Authorizations

The development, issue, removal, approval, maintenance, review at a minimum of 90 days to physical access authorization requirements are fully inherited from Google Cloud.


## 4. Physical Access Control

Physical access control enforcement and verification of access authorizations and all control systems and monitoring of visitor activity are fully inherited from Google Cloud.


## 5. Access Control for Transmission

All security safeguards for the transmission medium used for physical access authorization requirements are fully inherited from Google Cloud.


## 6. Access Control for Output Devices

All additional access controls for output devices and determination for authorization are fully inherited from Google Cloud.


## 7. Monitoring Physical Access

All facilities are actively monitored with physical intrusion alarms and surveillance equipment and monitoring physical access is fully inherited from Google Cloud.


## 8. Visitor Access Records

All maintenance and review of visitor access records is fully inherited from Google Cloud.


## 9. Power Equipment and Cabling

Protection of power equipment and power cabling is fully inherited from Google Cloud.


## 10. Emergency Shutoff

All capability to shut off the power to facilities or areas within facilities containing {{ ORGANIZATION }} {{ SYSTEM_NAME }}  information system resources are fully inherited from Google Cloud.


## 11. Emergency Power

Emergency power capabilities and capacity is fully inherited from Google Cloud.


## 12. Emergency Lighting

Emergency lighting capabilities are fully inherited from Google Cloud


## 13. Fire Protection

Fire protection capabilities are fully inherited from Google Cloud.


## 14. Environmental Controls

All environmental controls are fully inherited from Google Cloud.


## 15. Water Damage Protection

All requirements to implement master shutoff valves for water sources are fully inherited from Google Cloud.


## 16. Delivery and Removal

Documentation and maintenance records for delivery and removal of components are fully inherited from Google Cloud.


## 17. Alternate Work Site

All physical security controls for alternate work sites are fully inherited from Google Cloud.


## 18. Location of System Components

All physical security controls for the location of system components are fully inherited from Google Cloud.



## Appendix A – Detailed Compliance Matrix

The following table provides detailed traceability between the policy implementation statements in this document, the authoritative NIST SP 800-53 Rev. 5 control requirements, DoD CCIs, and the technical/governance enforcement mechanisms active across {{ SYSTEM_NAME }}.


| CTRL ID | CTRLTITLE | REQUIRED eMASS STANDARD | DOCREF | ENFORCEMENT MECHANISM |
| :--- | :--- | :--- | :--- | :--- |
| PE-01 | Policy and Procedures | Develops, documents, and disseminates PE policy/procedures to personnel with PE responsibilities; designates Physical Security Officer; reviews annually and upon audit findings, incidents, or policy changes. (CCI-000904, CCI-000905, CCI-000906, CCI-000907, CCI-000908, CCI-000909, CCI-000910, CCI-000911, CCI-002908, CCI-002909, CCI-004229, CCI-004230, CCI-004231, CCI-004232, CCI-004233, CCI-004234, CCI-004235, CCI-004236, CCI-004237, CCI-004238, CCI-004239) | Section 2 | Formal policy workflow published via eMASS (System ID: {{ RMF_PACKAGE_ID }}); annual governance cadence overseen by {{ ORGANIZATION }} Physical Security Officer, ISSM, and ISSO; incident triggers aligned with DoDM 5200.08 and federal facility security standards. |
| PE-02 | Physical Access Authorizations | Develops, approves, and maintains authorized facility access list; issues credentials; reviews access lists at least every 90 days; removes access upon termination. (CCI-000912, CCI-000913, CCI-000914, CCI-000915, CCI-001635, CCI-002910, CCI-002911) | Section 3 | Fully inherited from Google Services IL5 (eMASS ID: U:CLOUD:184) for cloud data centers; physical facility access lists managed in accordance with federal and DoD facility security directives with mandatory 90-day review cadence and automated offboarding. |
| PE-03 | Physical Access Control | Enforces physical access control at facility entry/exit points via guards/biometrics; maintains audit logs; controls publicly accessible areas; escorts/monitors visitors; secures keys; inventories access devices annually; changes combinations/keys upon events. (CCI-000920, CCI-000923, CCI-000924, CCI-000925, CCI-000926, CCI-000927, CCI-002915, CCI-002916, CCI-002917, CCI-002918, CCI-002919, CCI-002920, CCI-002921, CCI-002922, CCI-002923, CCI-002924, CCI-002925, CCI-004240, CCI-004241, CCI-004242, CCI-004243) | Section 4 | Google IL5 data center biometric mantraps, 24x7 armed guards, automated electronic badging, and annual physical access device inventories; on-premises server room keycard controls. |
| PE-03(01) | Physical Access Control: System Access | Enforces physical access authorizations to the system in addition to facility-level access controls at physical spaces containing system components. (CCI-000928, CCI-002926) | Section 4 | Individually locked server racks, cage partitions with electronic badges in colocation PoPs, and segregated Assured Workloads data halls inherited from Google IL5. |
| PE-04 | Access Control for Transmission | Controls physical access to system distribution and transmission lines within facilities using security controls and conduit. (CCI-000936, CCI-002930, CCI-002931) | Section 5 | Locked overhead fiber raceways in Google data centers; hardware Layer 2 MACsec encryption on {{ INTERCONNECT_TYPE }} and Layer 3 IPsec encapsulation for all external transit circuits. |
| PE-05 | Access Control for Output Devices | Controls physical access to output from system output devices to prevent unauthorized access. (CCI-000937) | Section 6 | Prohibition of physical output devices in cloud VPCs; serverless Grafana telemetry dashboards protected by {{ IDENTITY_PROVIDER }} with {{ MFA_MECHANISM }} and IAM role restrictions. |
| PE-06 | Monitoring Physical Access | Monitors physical access to facilities to detect/respond to incidents; reviews physical access logs at least every 90 days and upon security events; coordinates with incident response. (CCI-002939, CCI-000939, CCI-000940, CCI-002940, CCI-002941, CCI-000941) | Section 7 | Google GSOC 24x7 monitoring, automated access logging, 90-day log review cadence, and integration with {{ ORGANIZATION }} NetOps / DISA CSSP per CJCSM 6510.01B and DoDI 8530.01. |
| PE-06(01) | Monitoring Physical Access: Intrusion Alarms and Surveillance Equipment | Monitors physical access to the facility using physical intrusion alarms and surveillance equipment. (CCI-000942) | Section 7 | Inherited Google IL5 CCTV coverage, laser perimeter sensors, and automated physical intrusion detection systems (PIDS) with continuous recording. |
| PE-08 | Visitor Access Records | Maintains visitor access records for at least one year IAW NARA GRS; reviews records at least every 90 days; reports anomalies to security personnel. (CCI-000947, CCI-000948, CCI-000949, CCI-002952, CCI-004251, CCI-004252) | Section 8 | Automated visitor logging systems with 1-year retention, quarterly 90-day reviews, and automated anomaly alerting to {{ ORGANIZATION }} ISSO / facility security officers. |
| PE-08(03) | Visitor Access Records: Limit Personally Identifiable Information Elements | Limits PII elements in visitor access records to the minimum required for identity verification and operational purposes per the PIA. (CCI-004254, CCI-004255) | Section 8 | Mandatory PIA data minimization standards enforcing capture of name, DoD affiliation, badge number, and timestamp only; SSN collection strictly prohibited. |
| PE-09 | Power Equipment and Cabling | Protects power equipment and power cabling from damage, tampering, and physical destruction. (CCI-000952) | Section 9 | Inherited Google IL5 physical electrical infrastructure, subterranean reinforced power routing, armored conduits, and secured electrical utility rooms. |
| PE-10 | Emergency Shutoff | Provides capability of shutting off power in emergency situations; places labeled shutoff switches near more than one IT area egress point; protects from unauthorized activation. (CCI-000956, CCI-000957, CCI-000958, CCI-000959, CCI-004256) | Section 10 | Dual-action Emergency Power Off (EPO) switches installed at multiple egress points, fitted with protective safety shields and anti-tamper alarm monitoring. |
| PE-11 | Emergency Power | Provides uninterruptible power supply (UPS) and long-term alternate power for orderly shutdown or sustained transition. (CCI-002955) | Section 11 | N+1 redundant UPS battery banks and on-site diesel emergency backup generators with 72+ hours of dedicated fuel reserves inherited from Google IL5 data centers. |
| PE-12 | Emergency Lighting | Employs and maintains automatic emergency lighting that activates during power loss, illuminating exits and evacuation routes. (CCI-000963) | Section 12 | Automated emergency lighting grid backed by independent battery packs and generator backup circuits covering all egress pathways and data halls. |
| PE-13 | Fire Protection | Employs and maintains fire detection and suppression systems supported by an independent energy source. (CCI-000965) | Section 13 | Google IL5 fire protection infrastructure powered by independent emergency circuits and generator backups. |
| PE-13(01) | Fire Protection: Detection Systems | Employs automatic fire detection systems that notify designated personnel and emergency responders in the event of a fire. (CCI-002961, CCI-002962, CCI-002963, CCI-002964) | Section 13 | VESDA air-aspirating smoke detection and thermal sensors with automated dispatch to 24x7 GSOC and local municipal fire departments. |
| PE-13(02) | Fire Protection: Suppression Systems | Employs automatic fire suppression systems that notify personnel/responders and operate continuously even when facilities are not staffed. (CCI-000968, CCI-002965, CCI-002966, CCI-002967) | Section 13 | Automated clean-agent gaseous fire suppression (FM-200/NOVEC 1230) and pre-action dry-pipe sprinklers with 24x7 autonomous activation and responder notification. |
| PE-14 | Environmental Controls | Maintains and continuously monitors temperature and humidity levels within manufacturer specifications. (CCI-000971, CCI-000972, CCI-000973, CCI-000974) | Section 14 | Automated Building Management Systems (BMS) continuously monitoring and regulating HVAC/CRAH temperature and humidity to ASHRAE standards. |
| PE-15 | Water Damage Protection | Protects system from water leakage damage; provides accessible, working master shutoff valves; ensures key personnel have knowledge of valves. (CCI-000977, CCI-000978, CCI-000979) | Section 15 | Raised computer room flooring, under-floor moisture detection sensors, accessible and tested master shutoff valves, and personnel emergency training. |
| PE-16 | Delivery and Removal | Authorizes and controls all system components entering/exiting facility; maintains inventory records of components. (CCI-000981, CCI-000983, CCI-000984, CCI-002974) | Section 16 | Secure loading dock inspections, strict bill of lading verification, serial number tracking, and NIST SP 800-88 Rev. 1 certified hardware destruction records. |
| PE-17 | Alternate Work Site | Determines and documents allowed alternate work sites per COOP; employs security controls and building codes; provides incident communication channels. (CCI-000985, CCI-000987, CCI-000988, CCI-002975, CCI-004262, CCI-004263) | Section 17 | Formal {{ ORGANIZATION }} COOP plan authorization, GFE mandates, {{ IDENTITY_PROVIDER }} with {{ MFA_MECHANISM }}, VPC-SC context-aware perimeter restrictions, and security operations communication channels. |
| PE-22 | Component Marking | Marks hardware processing/output components indicating impact/classification level ({{ IMPACT_LEVEL }} / {{ SENSITIVITY_CLASSIFICATION }}). (CCI-004269, CCI-004270) | Section 16 | Physical classification labels on on-premises/colocation network racks and automated Terraform IaC tagging (classification: {{ SENSITIVITY_CLASSIFICATION }}) on all cloud resources. |
| PE-23 | Facility Location | Plans facility site location considering physical/environmental hazards; incorporates hazard analysis into risk strategy. (CCI-004271, CCI-004272) | Section 18 | Multi-region deployment (us-east4 / us-central1), geographic disaster hazard vetting by Google/{{ ORGANIZATION }}, and automated BGP ECMP cross-region failover. |
