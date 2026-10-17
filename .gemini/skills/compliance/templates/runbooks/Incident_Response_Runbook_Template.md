# Incident Response Runbook: [Threat Scenario Title]

## Document Control
| Attribute | Detail |
| :--- | :--- |
| **Runbook ID** | IR-CUSTOM-001 |
| **Last Updated** | {{ DATE }} |
| **Owner** | Incident Response Team (ISSO / SOC) |
| **Target SLA** | [CONFIG_REQUIRED: organization-defined triage, containment, and recovery targets, e.g., 15m / 30m / 4h] |


> [!NOTE]
> **SIEM & Threat Detection Tooling**:
> Threat monitoring depends on the services enabled in the environment configuration:
> - **Cloud-Native Posture & Threat Detection**: Where Security Command Center (SCC) or Google Cloud SecOps (Chronicle) is enabled, Event Threat Detection (ETD) and Security Health Analytics (SHA) findings are available. In <!-- IF DOD_IL5 -->DoD IL4 / DoD IL5<!-- ENDIF --><!-- IF DOD_IL4 -->DoD IL4<!-- ENDIF --><!-- IF DOD_IL2 -->DoD IL2<!-- ENDIF --><!-- IF DOD_IL6 -->DoD IL6<!-- ENDIF --><!-- IF NOT DOD_ENCLAVE -->{{ REGIME_DISPLAY_NAME }}<!-- ENDIF --> enclaves, SCC is not a telemetry source unless the Authorizing Official has approved an exception to policy.
> - **Centralized SIEM / CSSP Integration**: Audit logs route through Cloud Logging export sinks to the configured CSSP / SIEM (e.g., {{ CSSP_PROVIDER }}, {{ EXTERNAL_SIEM }}) for 24/7 monitoring.

> [!NOTE]
> **Lifecycle alignment**: NIST SP 800-61 Rev. 3 (April 2025) organizes incident response under the NIST CSF 2.0 Functions. The phases in this template map as follows: Phase 1 (Identification) to Detect (DE.AE) and Respond (RS.MA); Phase 2 (Triage and Analysis) to Respond (RS.AN); Phase 3 (Containment) and eradication to Respond (RS.MI); external reporting to Respond (RS.CO); recovery to Recover (RC.RP, RC.CO); Phase 5 (Lessons Learned) to Identify (ID.IM).

## 1. Objective
[State the threat, vulnerability, or incident type this runbook covers and the goal of the response.]

## 2. Target Audience & Prerequisites
**Audience:**
* [e.g., Security Operations Center (SOC) Analysts (L1/L2/L3)]
* [e.g., Incident Responders]
* [e.g., Cloud Infrastructure / Network Security Engineers]

**Prerequisites for Responders:**
* **Audit & Log Inspection:** [List roles, e.g., `roles/logging.viewer`, `roles/logging.privateLogViewer` on the {{ ORGANIZATION }} Organization]
* **Security & Posture Management (where SCC is enabled):** [List roles, e.g., `roles/securitycenter.adminViewer`, `roles/securitycenter.findingsViewer`, or `roles/securitycenter.admin`]
* [List containment / break-glass roles, e.g., `roles/compute.securityAdmin`, `roles/iam.securityAdmin`]
* Access to the configured CSSP / SIEM console (e.g., {{ CSSP_PROVIDER }} / {{ EXTERNAL_SIEM }}) that receives the audit logs.
* [List other tool or console access, e.g., Access Context Manager, Palo Alto Panorama, Kubernetes RBAC]

## 3. Scope
[Define the environments (e.g., Dev, Staging, {{ REGIME_DISPLAY_NAME }} production landing zones), systems, and components this runbook applies to.]

---

## Phase 1: Identification & Scoping

### 1.1 Detection Sources
[List the tools, alerts, and logs that indicate this incident type.]
* **[Source, e.g., Security Command Center (where enabled; not in <!-- IF DOD_IL5 -->DoD IL4 / DoD IL5<!-- ENDIF --><!-- IF DOD_IL4 -->DoD IL4<!-- ENDIF --><!-- IF DOD_IL2 -->DoD IL2<!-- ENDIF --><!-- IF DOD_IL6 -->DoD IL6<!-- ENDIF --><!-- IF NOT DOD_ENCLAVE -->{{ REGIME_DISPLAY_NAME }}<!-- ENDIF --> without an AO exception)]**: [Finding category or rule name].
* **[Source, e.g., CSSP / SIEM (where configured)]**: [Indicator from the Cloud Logging export sinks].
* **[Source, e.g., Cloud Logging]**: [Log name, query, or log-based alert metric].
* **[Source, e.g., third-party EDR]**: [Indicator].

### 1.2 Initial Assessment & Log Extraction
[Steps to validate the alert and capture its core attributes.]
1. **Locate the Primary Log Event:** [How to find the source log or alert. Provide a Logs Explorer query.]
    * **Logs Explorer Query Template:**
      ```text
      [Insert reusable log query here]
      ```
2. **Extract Key Details:** Record the following from the log entry:
    * `protoPayload.authenticationInfo.principalEmail`: [Who or what initiated the action]
    * `protoPayload.requestMetadata.callerIp`: [Originating IP address]
    * `protoPayload.resourceName`: [The resource targeted]
    * `protoPayload.methodName`: [The API method called]
3. **Determine Preliminary Severity:**
    * **SEV 1 (Critical):** [e.g., production impact, data exfiltration, privileged account compromise].
    * **SEV 2 (High):** [e.g., non-production impact, isolated resource compromise without data loss].
    * **SEV 3 (Medium/Low):** [e.g., configuration drift, low-risk misconfiguration, confirmed blocked attempt].

### 1.3 Escalation & External Reporting
* [Define internal escalation triggers and how to page the Incident Commander.]
* Report to external parties within the timelines that apply to this system:

| Reporting path | Applies to | Requirement | Contact and deadline for this system |
| :--- | :--- | :--- | :--- |
| CISA | Federal agencies | CISA Federal Incident Notification Guidelines: report within 1 hour of identification by the agency's top-level SOC, CSIRT, or IT department. US-CERT is now part of CISA. | [CONFIG_REQUIRED: agency reporting contact] |
| FedRAMP | Cloud services with a FedRAMP authorization | Notify affected agencies and FedRAMP per the FedRAMP incident communication rules. Under the FedRAMP Consolidated Rules for 2026 (Incident Evaluation and Communication), the Initial Incident Report deadline depends on the Potential Agency Impact (PAIN) rating and the certification class. | [CONFIG_REQUIRED: FedRAMP reporting procedure and deadline that apply] |
<!-- IF DOD_ENCLAVE -->
| DoD CSSP | <!-- IF DOD_IL5 -->DoD IL4 / DoD IL5<!-- ENDIF --><!-- IF DOD_IL4 -->DoD IL4<!-- ENDIF --><!-- IF DOD_IL2 -->DoD IL2<!-- ENDIF --><!-- IF DOD_IL6 -->DoD IL6<!-- ENDIF --><!-- IF NOT DOD_ENCLAVE -->{{ REGIME_DISPLAY_NAME }}<!-- ENDIF --> systems | Report through the system's Cybersecurity Service Provider (CSSP) into the Joint Incident Management System (JIMS) using the categories and impact-tiered timelines in CJCSM 6510.01B Table C-A-1. | [CONFIG_REQUIRED: CSSP contact and reporting timeline from the CSSP agreement] |
| DoD Cloud Service Provider | Cloud Service Offerings under DFARS 252.239-7010 / DISA CSP SRG V1R7 Section 6.2 | Submit initial incident report within 1 hour of triage via DIB Cyber Incident Collection Format (ICF) at https://dibnet.dod.mil (or `DCISE@DC3.mil` / 877-838-2174) for shared CSOs, or direct to USCYBERCOM / JFHQ-DODIN for dedicated DoD infrastructure. | [CONFIG_REQUIRED: CSP incident reporting POC] |
| DoD (DIBNet) | Defense contractors subject to DFARS 252.204-7012 | Report cyber incidents at https://dibnet.dod.mil within 72 hours of discovery; submit malicious software to the DoD Cyber Crime Center (DC3). | [CONFIG_REQUIRED: contract reporting POC] |
<!-- ENDIF -->

<!-- IF DOD_ENCLAVE -->
* **CJCSM 6510.01B categories & Table C-A-1 timelines:** [List the categories that apply to this scenario, e.g., CAT 1 Root Level Intrusion, CAT 2 User Level Intrusion, CAT 4 Denial of Service, CAT 7 Malicious Logic. Per CJCSM 6510.01B Table C-A-1: High impact CAT 1/2/4/7 notify next tier within 15 minutes / initial report within 4 hours / JIMS submission within 6 hours; Moderate impact CAT 1/2/7 notify within 2 hours / report within 8 hours / JIMS within 12 hours, and CAT 4 notify within 15 minutes / report within 4 hours / JIMS within 6 hours; `[CONFIG_REQUIRED: CSSP agreement timeline]`.]
* **Authorized DoD Component CSSP escalation points (DoDM 8530.01 / GAO-25-107121; confirm against the system's CSSP agreement):**
  * Army: U.S. Army Cyber Command (ARCYBER) CSSP (executed via Army Network Enterprise Technology Command Regional Cyber Centers [RCCs]) and U.S. Army C5ISR Center CSSP.
  * Air Force: 16th Air Force (AFCYBER / AFIN CSSP, 616th Operations Center) and U.S. Air Forces Central (AFCENT) CSSP.
  * Navy: Navy Cyber Defense Operations Command (NCDOC) and NIWC Atlantic CSSP.
  * Marine Corps: Marine Corps Forces Cyberspace Command (MARFORCYBER / Marine Corps Cyberspace Operations Group [MCCOG]).
  * Space Force: U.S. Space Force CSSP (Space Delta 6 / Mission Delta 6).
  * Defense Agencies: DISA CSSP (or component-specific CSSP such as DIA, DLA, DTRA, MDA, NGA, NRO, NSA), which reports upstream to USCYBERCOM / JFHQ-DODIN (DoD Cyber Defense Command) via JIMS.
<!-- ENDIF -->

---

## Phase 2: Triage and Analysis

**Goal:** Confirm the scope, impact, and cause of the incident and distinguish an attack from a misconfiguration.

### 2.1 Attack vs. Misconfiguration Analysis
[Steps for correlating recent changes and operational context.]
1. **Check Change Management & IaC Pipelines:** [How to check whether a recent deployment or an approved break-glass change caused the alert.]
2. **Identity & Behavior Correlation:** [How to decide whether the behavior is normal for the identity or resource, e.g., by comparing source IP ranges and times of activity.]

### 2.2 Impact & Blast Radius Assessment
[Steps to determine how far the threat actor reached.]
1. **Determine Direction & Scope:** [How to tell whether activity is inbound, outbound (exfiltration / C2), or lateral (between projects or perimeters).]
2. **Identify Sensitive Dependencies:** [How to determine whether the affected resource can reach sensitive data, keys, secrets, or adjacent infrastructure.]

---

## Phase 3: Containment

**Goal:** Stop exfiltration and lateral movement and cut off the threat actor's access while preserving evidence.

### 3.1 Immediate Containment Actions
[Step-by-step instructions or CLI commands to isolate the threat.]
1. **Isolate the Identity:** [Commands to revoke sessions, suspend user accounts, or disable service accounts.]
    ```bash
    [Insert command, e.g., gcloud iam service-accounts disable ...]
    ```
2. **Isolate the Infrastructure/Network:** [Commands to apply quarantine firewall rules or network tags.]
    ```bash
    [Insert command, e.g., gcloud compute instances add-tags ...]
    ```
3. **Perimeter Controls:** [How to use VPC Service Controls or Cloud Armor to restrict access around the affected resources.]

---

## Phase 4: Eradication and Recovery

**Goal:** Remove the threat actor's presence, fix the root cause, and restore resources to a known good state.

### 4.1 Eradication & Forensic Capture
1. **Capture Forensic Evidence:** [How to preserve memory, snapshot persistent disks, or save container logs before deleting anything.]
    ```bash
    [Insert snapshot or forensic export command]
    ```
2. **Eliminate Persistence Mechanisms:** [How to find and remove unauthorized IAM grants (`SetIamPolicy`), new service accounts, SSH keys, or API keys.]
3. **Remediate the Root Vulnerability:** [How to fix the entry point, e.g., update dependencies or close firewall ports.]

### 4.2 Recovery & IaC Alignment
1. **Reconcile Infrastructure as Code (IaC State):** [How to compare the cloud state with the Terraform configuration and run plan/apply from the trusted CI/CD pipeline to remove manual changes made by the attacker.]
2. **Restore Access & Verification:** [How to re-enable legitimate access, e.g., new passwords, re-registered MFA keys, rotated service account keys.]
3. **Heightened Monitoring:** [List the log metrics, dashboards, or alert rules to watch for the next [CONFIG_REQUIRED: monitoring period, e.g., 72 hours].]

---

## Phase 5: Lessons Learned

### 5.1 Post-Incident Review (PIR)
[Questions and action items for the post-incident review.]
1. **Timeline Reconstruction:** Record the timestamps for detection, triage, containment, eradication, and recovery.
2. **Detection Improvements:** How was the incident detected? Could thresholds or logging have detected it earlier?
3. **Response Improvements:** Which containment or eradication steps were slow? Which steps of this runbook can be automated?
4. **Architecture & Hardening:** Which preventive controls (e.g., Organization Policy constraints, network architecture changes) should be added to the base configuration to remove this attack vector?
