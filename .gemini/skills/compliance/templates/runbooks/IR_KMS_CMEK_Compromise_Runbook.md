# Incident Response Runbook: Customer-Managed Encryption Key (CMEK) Compromise or Loss

## Document Control
| Attribute | Detail |
| :--- | :--- |
| **Runbook ID** | IR-CMEK-001 |
| **Version** | {{ VERSION }} |
| **Last Updated** | {{ DATE }} |
| **Owner** | Security Operations / Cloud Platform Team |
| **Target SLA** | [CONFIG_REQUIRED: organization-defined triage, containment, and recovery targets, e.g., 15m / 30m / 4h-24h depending on re-encryption volume] |


> [!NOTE]
> **SIEM & Threat Detection Tooling**:
> Threat monitoring depends on the services enabled in the environment configuration:
> - **Cloud-Native Posture & Threat Detection**: Where Security Command Center (SCC) or Google Cloud SecOps (Chronicle) is enabled, Event Threat Detection (ETD) and Security Health Analytics (SHA) findings are available. In <!-- IF DOD_IL5 -->DoD IL4 / DoD IL5<!-- ENDIF --><!-- IF DOD_IL4 -->DoD IL4<!-- ENDIF --><!-- IF DOD_IL2 -->DoD IL2<!-- ENDIF --><!-- IF DOD_IL6 -->DoD IL6<!-- ENDIF --><!-- IF NOT DOD_ENCLAVE -->{{ REGIME_DISPLAY_NAME }}<!-- ENDIF --> enclaves, SCC is not a telemetry source unless the Authorizing Official has approved an exception to policy.
> - **Centralized SIEM / CSSP Integration**: Audit logs route through Cloud Logging export sinks to the configured CSSP / SIEM (e.g., {{ CSSP_PROVIDER }}, {{ EXTERNAL_SIEM }}) for 24/7 monitoring.

> [!NOTE]
> **Lifecycle alignment**: NIST SP 800-61 Rev. 3 (April 2025) organizes incident response under the NIST CSF 2.0 Functions. The phases in this runbook map as follows: Phase 1 (Identification & Scoping) to Detect (DE.AE) and Respond (RS.MA, RS.AN, RS.CO); Phase 2 (Containment) to Respond (RS.MI); Phase 3 (Eradication and Recovery) to Respond (RS.MI) and Recover (RC.RP, RC.CO); Phase 4 (Lessons Learned) to Identify (ID.IM).

{{ DISCOVERED_ENVIRONMENT_CONTEXT }}

## 1. Objective
This runbook gives Security Operators and Incident Responders the steps to identify, contain, and recover from the compromise, accidental deletion, or loss of access to Customer-Managed Encryption Keys (CMEK) in Cloud KMS within the {{ SYSTEM_NAME }} architecture on {{ CLOUD_PROVIDER }} ({{ CSP_ABBR }}).

## 2. Target Audience & Prerequisites
**Audience:**
* Security Operations Center (SOC) Analysts
* Incident Responders
* Cloud Infrastructure / Platform Engineers

**Prerequisites for Responders:**
* **Audit & Log Inspection:** `roles/logging.viewer` and `roles/logging.privateLogViewer` to analyze audit logs.
* **Security & Posture Management (where SCC is enabled):** `roles/securitycenter.adminViewer`, `roles/securitycenter.findingsViewer`, or `roles/securitycenter.admin` on the {{ ORGANIZATION }} Organization.
* **KMS Inspection:** `roles/cloudkms.viewer` to inspect key configurations.
* `roles/cloudkms.admin` (through break-glass / emergency access) to disable, restore, or rotate keys during containment.
* Access to the {{ SYSTEM_NAME }} GitOps repository to revert unauthorized Infrastructure as Code (IaC) changes.
* Access to the configured CSSP / SIEM console (e.g., {{ CSSP_PROVIDER }} / {{ EXTERNAL_SIEM }}) that receives the audit logs.

## 3. Scope
This runbook applies to {{ SYSTEM_NAME }} environments, including {{ REGIME_DISPLAY_NAME }} landing zones, where CMEK is required for data at rest. It covers:
* Compromise of Cloud KMS symmetric or asymmetric keys.
* Malicious or accidental scheduling of key version destruction.
* Loss of access caused by IAM changes on keys or key rings.
* Cloud External Key Manager (EKM) connectivity failures, if EKM is used in the {{ SYSTEM_NAME }} deployment.

---

## Phase 1: Identification & Scoping

### 1.1 Detection Sources
Monitor for the following indicators of compromise or loss:
* **Cloud Logging:** Admin Activity audit logs for `cloudkms.googleapis.com`.
* **Security Command Center (SCC) (FedRAMP High / commercial, where enabled):** Findings for anomalous KMS activity or policy violations.
* **CSSP / SIEM (<!-- IF DOD_IL5 -->DoD IL4 / DoD IL5<!-- ENDIF --><!-- IF DOD_IL4 -->DoD IL4<!-- ENDIF --><!-- IF DOD_IL2 -->DoD IL2<!-- ENDIF --><!-- IF DOD_IL6 -->DoD IL6<!-- ENDIF --><!-- IF NOT DOD_ENCLAVE -->{{ REGIME_DISPLAY_NAME }}<!-- ENDIF -->):** KMS audit logs and alerts forwarded from Cloud Logging export sinks to the CSSP / SIEM.
* **Service Disruption (Availability Impact):** Alerts for widespread HTTP 500 errors, applications failing to start, or Cloud Storage / BigQuery returning `PERMISSION_DENIED` or `FAILED_PRECONDITION` errors after a key version was disabled.
* **Key Access Justifications (where configured):** Justification reasons that do not match expected access.

### 1.2 Initial Assessment & Log Extraction
1. **Locate the Log Entry:** Find the KMS audit log entry behind the alert. Cloud KMS writes its audit logs to the project that holds the key. Disabling a key version is logged as `UpdateCryptoKeyVersion`.
    * **Logs Explorer Query Example (Destructive Actions):**
        ```text
        logName="projects/[KMS_PROJECT_ID]/logs/cloudaudit.googleapis.com%2Factivity"
        AND protoPayload.serviceName="cloudkms.googleapis.com"
        AND protoPayload.methodName:("DestroyCryptoKeyVersion" OR "UpdateCryptoKeyVersion" OR "UpdateCryptoKeyPrimaryVersion" OR "SetIamPolicy")
        ```
    * **Logs Explorer Query Example (KMS roles granted at the organization level):** Review the policy delta in each result for `roles/cloudkms.*` bindings.
        ```text
        logName="organizations/[ORG_ID]/logs/cloudaudit.googleapis.com%2Factivity"
        AND protoPayload.methodName="SetIamPolicy"
        ```
2. **Extract Key Details:** Record the following from the log entry:
    * `protoPayload.authenticationInfo.principalEmail`: The identity that performed the action.
    * `protoPayload.resourceName`: The full path of the affected key or key version (e.g., `projects/.../locations/.../keyRings/.../cryptoKeys/.../cryptoKeyVersions/1`).
    * `protoPayload.methodName`: The API method called.
3. **Determine the Severity:**
    * **SEV 1 (Key Destruction/Compromise):** A key version in active use is scheduled for destruction or is confirmed compromised. Risk of permanent data loss or unauthorized decryption.
    * **SEV 2 (Access Loss / Disabled):** A key version is disabled or its IAM policy was removed, causing a production outage, but the key material is intact.
    * **SEV 3 (Anomalous Admin Activity):** Unexpected key rotation or IAM changes with no outage or confirmed compromise.

### 1.3 Escalation & External Reporting
* For SEV 1 or SEV 2, declare an incident and page the on-call Incident Commander.
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
* **CJCSM 6510.01B categories & Table C-A-1 timelines:** a compromised KMS administrator account or key is usually CAT 1 (Root Level Intrusion) or CAT 2 (User Level Intrusion), while a key-destruction denial of service is CAT 4 (Denial of Service). Per CJCSM 6510.01B Table C-A-1: High impact CAT 1/2/4 notify next tier within 15 minutes / initial report within 4 hours / JIMS submission within 6 hours; Moderate impact CAT 1/2 notify within 2 hours / report within 8 hours / JIMS within 12 hours, and CAT 4 notify within 15 minutes / report within 4 hours / JIMS within 6 hours; confirm the category and `[CONFIG_REQUIRED: CSSP agreement timeline]` with the CSSP.
* **Authorized DoD Component CSSP escalation points (DoDM 8530.01 / GAO-25-107121; confirm against the system's CSSP agreement):**
  * Army: U.S. Army Cyber Command (ARCYBER) CSSP (executed via Army Network Enterprise Technology Command Regional Cyber Centers [RCCs]) and U.S. Army C5ISR Center CSSP.
  * Air Force: 16th Air Force (AFCYBER / AFIN CSSP, 616th Operations Center) and U.S. Air Forces Central (AFCENT) CSSP.
  * Navy: Navy Cyber Defense Operations Command (NCDOC) and NIWC Atlantic CSSP.
  * Marine Corps: Marine Corps Forces Cyberspace Command (MARFORCYBER / Marine Corps Cyberspace Operations Group [MCCOG]).
  * Space Force: U.S. Space Force CSSP (Space Delta 6 / Mission Delta 6).
  * Defense Agencies: DISA CSSP (or component-specific CSSP such as DIA, DLA, DTRA, MDA, NGA, NRO, NSA), which reports upstream to USCYBERCOM / JFHQ-DODIN (DoD Cyber Defense Command) via JIMS.
<!-- ENDIF -->

---

## Phase 2: Containment

**Goal:** Prevent further unauthorized decryption, stop destruction of keys, and preserve the current state for recovery.

### 2.1 Immediate Actions (If a Key Is Compromised)
*Warning: Disabling a key version breaks every service that uses it for reads and writes. Coordinate with system owners when possible, but disable the version if active data exfiltration is confirmed.*
1. **Disable the Compromised Key Version:**
    ```bash
    gcloud kms keys versions disable [VERSION] \
        --key=[KEY_NAME] \
        --keyring=[KEYRING_NAME] \
        --location=[LOCATION] \
        --project=[KMS_PROJECT_ID]
    ```
2. **Contain the Compromised Identity:** Run **IR-IAM-001 (Compromised IAM Credentials)** to suspend the user or disable the service account that used the key.

### 2.2 Immediate Actions (If a Key Version Is Scheduled for Destruction)
*Note: A destroyed key version first enters the "scheduled for destruction" state. The default duration of that state is 30 days; it can be set per key at creation, and an organization policy can enforce a minimum. Restore the version before the period ends, after which the key material is permanently deleted.*
1. **Restore the Key Version:**
    ```bash
    gcloud kms keys versions restore [VERSION] \
        --key=[KEY_NAME] \
        --keyring=[KEYRING_NAME] \
        --location=[LOCATION] \
        --project=[KMS_PROJECT_ID]
    ```
    A restored version returns in the disabled state; enable it with `gcloud kms keys versions enable` once the incident commander approves.

### 2.3 Immediate Actions (If Access Was Lost Through IAM)
1. **Halt Automated Pipelines:** If a faulty Terraform deployment removed KMS IAM roles, pause the CI/CD pipeline so it does not reapply the bad state.
2. **Restore IAM Permissions:** Re-grant `roles/cloudkms.cryptoKeyEncrypterDecrypter` to the affected service agents with `gcloud` or the console to restore service, then codify the change (Phase 3.3).

---

## Phase 3: Eradication and Recovery

**Goal:** Restore normal operations, re-encrypt affected data, and reconcile Infrastructure as Code (IaC).

### 3.1 Key Rotation
1. **Create a New Key Version:** If the primary version was compromised, rotate the key manually.
    ```bash
    gcloud kms keys versions create --key=[KEY_NAME] --keyring=[KEYRING_NAME] --location=[LOCATION] --project=[KMS_PROJECT_ID]
    # Set the new version as primary
    gcloud kms keys update [KEY_NAME] --keyring=[KEYRING_NAME] --location=[LOCATION] --project=[KMS_PROJECT_ID] --primary-version=[NEW_VERSION]
    ```

### 3.2 Data Re-encryption
*Note: Rotating a key does not re-encrypt existing data. Data stays encrypted with the old key version until it is rewritten.*
1. **Identify Affected Resources:** List the Cloud Storage buckets, BigQuery tables, and Persistent Disks protected by the compromised key version.
2. **Rewrite or Copy Data:**
    * **Cloud Storage:** Rewrite all current and noncurrent object versions with the key's current primary version (`--all-versions`). Note: buckets protected by an active Bucket Lock retention policy or object holds (`retentionPolicyNotMet`) cannot rewrite objects in place before the retention period expires; for retention-locked buckets, copy objects to a compliant replacement bucket encrypted with the new key version while preserving retention governance.
      ```bash
      gcloud storage objects update gs://[BUCKET_NAME]/** \
          --all-versions \
          --encryption-key=projects/[KMS_PROJECT_ID]/locations/[LOCATION]/keyRings/[KEYRING_NAME]/cryptoKeys/[KEY_NAME]
      ```
    * **BigQuery:** Copy each affected table to a new table encrypted with the key (for example, `bq cp --destination_kms_key=...`), verify the copy, then replace the original.
    * **Compute Engine:** Snapshot the disk, create a new disk from the snapshot encrypted with the key's current primary version, and recreate the instance from it.
3. **Destroy Old Material:** After all data is confirmed re-encrypted with the new version, schedule the compromised key version for destruction.

### 3.3 Reconcile IaC State ({{ SYSTEM_NAME }} GitOps)
1. **Update Terraform:** Record the new KMS IAM bindings, rotation schedules, and key states in the {{ SYSTEM_NAME }} Terraform repository.
2. **Apply State:** Run `terraform apply` from the trusted CI/CD pipeline so the emergency changes are codified and not overwritten by the next run.

---

## Phase 4: Lessons Learned

### 4.1 Post-Incident Review (PIR)
1. Hold a PIR with Security, Platform, and Data owners within [CONFIG_REQUIRED: review deadline, e.g., 5 business days].
2. **Identify Root Cause:** How did the compromise or deletion happen (e.g., compromised admin credentials, misconfigured Terraform module, missing IAM guardrails)?

### 4.2 Preventive Measures & Remediation
1. **Organization Policies:** Set the "Minimum destroy scheduled duration per key" organization policy constraint and restrict who holds KMS administration roles.
2. **Terraform Guardrails:** Add `lifecycle { prevent_destroy = true }` to critical `google_kms_crypto_key` resources in the {{ SYSTEM_NAME }} codebase.
3. **Separation of Duties:** Keep identities that administer keys (KMS Admins) separate from identities that use keys (Encrypter/Decrypters).
4. **Alerting:** Configure the SIEM / CSSP (or SCC where permitted) to page the on-call engineer for any `DestroyCryptoKeyVersion` event in production projects.
