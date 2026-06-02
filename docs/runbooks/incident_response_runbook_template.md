# Incident Response Runbook: [Threat Scenario Title]

## Document Control
| Attribute | Detail |
| :--- | :--- |
| **Runbook ID** | IR-[XYZ]-00[X] |
| **Last Updated** | YYYY-MM-DD |
| **Owner** | [Team Name / Role] |
| **Target SLA** | Triage: [X]m \| Containment: [X]m \| Resolution: [X]h |

## 1. Objective
[Provide a brief, clear statement of the runbook's objective. What specific threat, vulnerability, or incident type does this address, and what is the ultimate goal of the response?]

## 2. Target Audience & Prerequisites
**Audience:**
* [e.g., Security Operations Center (SOC) Analysts (L1/L2/L3)]
* [e.g., Incident Responders]
* [e.g., Cloud Infrastructure / Network Security Engineers]

**Prerequisites for Responders:**
* [List specific IAM Roles required to execute this runbook, e.g., `roles/logging.viewer`]
* [List specific tool or console access required, e.g., Access Context Manager, Palo Alto Panorama, Kubernetes RBAC access]
* [Specify any specialized procedures, such as Break-Glass / Emergency Elevation protocols]

## 3. Scope
[Define the exact scope of this runbook. Specify which environments (e.g., Dev, Staging, FedRAMP High/IL5 Prod landing zones), cloud providers, systems, or architectural components it applies to.]

---

## Phase 1: Identification & Scoping

### 1.1 Detection Sources
[List the primary tools, telemetry, alerts, and logs that indicate this specific type of incident has occurred.]
* **[Source/Tool Name, e.g., Security Command Center]**: [Description of the specific finding class, alert ID, or rule name].
* **[Source/Tool Name, e.g., Cloud Logging]**: [Description of the indicator, specific log sub-type, or automated alert metric].
* **[Source/Tool Name, e.g., Third-Party EDR/SIEM]**: [Description of indicator].

### 1.2 Initial Assessment & Log Extraction
[Describe the immediate steps to perform an initial validation and capture the core attributes of the alert.]
1. **Locate the Primary Log Event:** [Instructions on how to navigate to the source log or alert. Provide a template Log Explorer query if applicable.]
    * **Log Explorer Query Template:**
      ```text
      [Insert reusable log query template here]
      ```
2. **Extract Key Details:** Identify and document the following attributes from the raw event payload:
    * `principalEmail` / `identity`: [Who or what initiated the action]
    * `callerIp`: [The originating IP address, ASN, or geographic location]
    * `targetResource`: [The specific resource, asset, database, or bucket targeted]
    * `methodName` / `action`: [The exact API call or action executed]
3. **Determine Preliminary Severity:**
    * **SEV 1 (Critical):** [Define conditions for maximum escalation, e.g., Production impact, data exfiltration, highly privileged account compromise].
    * **SEV 2 (High):** [Define conditions for high escalation, e.g., Non-prod impact, isolated resource compromise without data loss].
    * **SEV 3 (Medium/Low):** [Define conditions for standard tracking, e.g., Operational drift, low-risk misconfiguration, confirmed blocked attempt].

---

## Phase 2: Triage and Analysis

**Goal:** Thoroughly verify the extent, impact, and authenticity of the incident to distinguish a true attack from operational misconfiguration.

### 2.1 Attack vs. Misconfiguration Analysis
[Detailed instructions for correlating historical events, recent change management, or operational context.]
1. **Check Change Management & IaC Pipelines:** [Instructions to verify if recent automated deployments or approved manual "break-glass" changes caused the alert.]
2. **Identity & Behavior Correlation:** [Instructions for evaluating if the observed behavior is normal or anomalous for the identity/resource involved (e.g., comparing historical IP ranges, times of operation).]

### 2.2 Impact & Blast Radius Assessment
[Steps to determine how far the threat actor has penetrated the architecture.]
1. **Determine Directionality & Scope:** [Instructions to determine if the threat is inbound, outbound (data exfiltration/C2), or lateral (moving between project perimeters).]
2. **Identify Sensitive Dependencies:** [How to quickly determine if the compromised resource has access to highly sensitive data, cryptographic keys, secrets, or adjacent cloud infrastructure.]

---

## Phase 3: Containment

**Goal:** Stop active data exfiltration, eliminate lateral movement, and sever threat actor access while preserving evidence.

### 3.1 Immediate Containment Actions
[Provide explicit step-by-step technical instructions or CLI commands to isolate the threat.]
1. **Isolate the Identity:** [Instructions or commands to revoke active sessions, suspend user accounts, or disable service accounts.]
    ```bash
    [Insert emergency CLI command template, e.g., gcloud iam service-accounts disable ...]
    ```
2. **Isolate the Infrastructure/Network:** [Instructions or commands to isolate network traffic, apply emergency quarantine firewall rules, or add restrictive network tags.]
    ```bash
    [Insert emergency CLI command template, e.g., gcloud compute instances add-tags ...]
    ```
3. **Perimeter Controls:** [Instructions for leveraging VPC Service Controls or Cloud Armor to enforce hard borders around the incident zone.]

---

## Phase 4: Eradication and Recovery

**Goal:** Completely eliminate the threat actor's presence, patch the root vulnerability, and securely restore resources to a known good state.

### 4.1 Eradication & Forensic Capture
1. **Capture Forensic Evidence:** [Instructions for preserving volatile memory, snapshotting persistent disks, or saving container logs before destruction.]
    ```bash
    [Insert snapshot or forensic export command template]
    ```
2. **Eliminate Persistence Mechanisms:** [Steps to audit and remove backdoors, such as unauthorized IAM policy grants (`SetIamPolicy`), newly created service accounts, rogue SSH keys, or rogue API keys.]
3. **Remediate the Root Vulnerability:** [Instructions for identifying and patching the entry point (e.g., updating software dependencies, closing open firewall ports).]

### 4.2 Recovery & IaC Alignment
1. **Reconcile Infrastructure as Code (IaC State):** [Instructions for verifying the cloud state against GitOps/Terraform configurations. Explain how to securely run plans/applies from a clean CI/CD pipeline to wipe away manual attacker modifications.]
2. **Restore Access & Verification:** [Steps to re-enable legitimate access securely (e.g., enforcing new passwords, resetting MFA keys, rotating service account keys).]
3. **Hyper-Care Monitoring:** [Identify the exact log metrics, dashboards, or security rules to monitor heavily for the next 72 hours to ensure the threat actor does not return.]

---

## Phase 5: Lessons Learned

### 5.1 Post-Incident Review (PIR)
[Questions and action items to address during the post-mortem with cross-functional teams.]
1. **Timeline Reconstruction:** Document exact timestamps for Detection, Triage, Containment, Eradication, and Recovery.
2. **Detection Optimization:** How was the incident detected? Could detection thresholds or logging configurations be improved to catch it earlier?
3. **Response Optimization:** Which parts of the containment and eradication process were bottlenecked? How can the automation of this runbook be improved?
4. **Architecture Architecture & Hardening:** What long-term preventative controls (e.g., Organization Policies, Service Control Policies, stricter network architecture) should be codified in the base framework to completely eliminate this attack vector?
