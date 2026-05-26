# Incident Response Runbook: Customer Managed Encryption Keys (CMEK) Compromise or Loss

## Document Control
| Attribute | Detail |
| :--- | :--- |
| **Runbook ID** | IR-CMEK-001 |
| **Last Updated** | YYYY-MM-DD |
| **Owner** | Security Operations / Cloud Platform Team |
| **Target SLA** | Triage: 15m \| Containment: 30m \| Recovery: 4h - 24h (depending on re-encryption volume) |

## 1. Objective
This runbook provides a structured, actionable process for Security Operators and Incident Responders to identify, contain, and recover from incidents involving the compromise, accidental deletion, or loss of access to Customer Managed Encryption Keys (CMEK) managed via Cloud KMS within the Stellar architecture on Google Cloud Platform (GCP).

## 2. Target Audience & Prerequisites
**Audience:**
* Security Operations Center (SOC) Analysts
* Incident Responders
* Cloud Infrastructure/Platform Engineers

**Prerequisites for Responders:**
* `roles/logging.viewer` to analyze audit logs.
* `roles/cloudkms.viewer` to inspect key states and configurations.
* `roles/cloudkms.admin` (via Break-Glass/Emergency Access) to disable, restore, or rotate keys during containment.
* Familiarity with the Stellar framework's GitOps repository to revert unauthorized Infrastructure as Code (IaC) changes.

## 3. Scope
This runbook applies to all environments deployed using Stellar, including FedRAMP High and IL5 landing zones, where CMEK is mandated for data at rest. It covers:
* Compromise of Cloud KMS symmetric or asymmetric keys.
* Malicious or accidental scheduling of key destruction.
* Loss of access due to improper IAM bindings on keys or key rings.
* (Optional) External Key Manager (EKM) connectivity failures, if applicable to the Stellar deployment.

---

## Phase 4: Identification & Scoping

### 4.1 Detection Sources
Monitor for the following indicators of compromise or loss:
* **Cloud Logging:** Administrative actions on `cloudkms.googleapis.com`.
* **Security Command Center (SCC):** Alerts for anomalous KMS activity, excessive administrative actions, or policy violations.
* **Service Disruption (Availability Impact):** Automated alerts for widespread HTTP 500s, applications failing to start, or Cloud Storage/BigQuery returning `Permission Denied` or `FAILED_PRECONDITION` (Key Disabled) errors.
* **Key Access Justifications (KAJ):** For IL5/FedRAMP environments, unusual justification codes logged during key access.

### 4.2 Initial Assessment & Log Extraction
1. **Locate the Log Entry:** Find the specific KMS log entry causing the alert.
    * **Log Explorer Query Example (Destructive Actions):**
        ```text
        logName="organizations/[ORG_ID]/logs/cloudaudit.googleapis.com%2Factivity"
        AND resource.type="cloudkms_cryptokeyversion"
        AND protoPayload.methodName:("DestroyCryptoKeyVersion" OR "DisableCryptoKeyVersion" OR "UpdateCryptoKeyPrimaryVersion" OR "SetIamPolicy")
        ```
2. **Extract Key Details:** Identify the following from the logs:
    * `principalEmail`: The identity that performed the action.
    * `resourceName`: The full path to the affected key version (e.g., `projects/.../locations/.../keyRings/.../cryptoKeys/.../cryptoKeyVersions/1`).
    * `methodName`: The exact API call executed.
3. **Determine the Nature of the Incident (Severity):**
    * **SEV 1 (Key Destruction/Compromise):** A key in active use is scheduled for destruction or confirmed compromised. Immediate risk of permanent data loss or unauthorized data decryption.
    * **SEV 2 (Access Loss / Disabled):** A key is disabled or IAM policies were wiped, causing an immediate production outage, but the key material is intact.
    * **SEV 3 (Anomalous Admin Activity):** Unexpected key rotation or IAM changes with no immediate outage or proven compromise.

---

## Phase 5: Containment

**Goal:** Prevent further unauthorized decryption of data, stop rogue destruction of keys, and preserve the current state for recovery.

### 5.1 Immediate Actions (If Key is Compromised)
*Warning: Disabling a key version immediately breaks all GCP services actively relying on it for read/write operations. Coordinate with system owners if possible, but prioritize disabling if active data exfiltration is confirmed.*
1. **Disable the Compromised Key Version:** Prevent further unauthorized use.
    ```bash
    gcloud kms keys versions disable [VERSION] \
        --key=[KEY_NAME] \
        --keyring=[KEYRING_NAME] \
        --location=[LOCATION] \
        --project=[KMS_PROJECT_ID]
    ```
2. **Contain the Compromised Identity:** Immediately execute **IR-IAM-001 (Compromised IAM Credentials)** to suspend the user or disable the service account that leaked the key access.

### 5.2 Immediate Actions (If Key is Scheduled for Destruction)
*Crucial GCP Fact: When a key version is destroyed via API or console, it enters a "Scheduled for Destruction" state. By default, there is a 24-hour soft-delete window before the key material is permanently and irretrievably wiped.*
1. **Restore Key Version:** Cancel the destruction immediately.
    ```bash
    gcloud kms keys versions restore [VERSION] \
        --key=[KEY_NAME] \
        --keyring=[KEYRING_NAME] \
        --location=[LOCATION] \
        --project=[KMS_PROJECT_ID]
    ```

### 5.3 Immediate Actions (If Access Lost via IAM)
1. **Halt Automated Pipelines:** If a malformed Terraform deployment stripped KMS IAM roles, pause the CI/CD pipeline to prevent it from reapplying the bad state.
2. **Restore IAM Permissions:** Temporarily re-apply the `roles/cloudkms.cryptoKeyEncrypterDecrypter` role to the necessary service accounts directly via `gcloud` or the console to restore immediate service availability.

---

## Phase 6: Eradication and Recovery

**Goal:** Restore normal operations securely, re-encrypt affected data, and reconcile Infrastructure as Code (IaC).

### 6.1 Key Rotation
1. **Generate New Key Version:** If the primary key was compromised, manually rotate it to generate new cryptographic material.
    ```bash
    gcloud kms keys versions create --key=[KEY_NAME] --keyring=[KEYRING_NAME] --location=[LOCATION] --project=[KMS_PROJECT_ID]
    # Set the new version as primary
    gcloud kms keys update [KEY_NAME] --keyring=[KEYRING_NAME] --location=[LOCATION] --project=[KMS_PROJECT_ID] --primary-version=[NEW_VERSION]
    ```

### 6.2 Data Re-encryption (The Hard Part)
*Crucial GCP Fact: Rotating a CMEK key in GCP only ensures that **new** data is encrypted with the new key version. Existing data at rest remains encrypted with the compromised/old key version until it is rewritten.*
1. **Identify Affected Resources:** Determine which Cloud Storage buckets, BigQuery tables, or Persistent Disks are protected by the compromised key.
2. **Rewrite/Copy Data:**
    * **Cloud Storage:** Use the `rewrite` command to re-encrypt objects in place with the new primary key version.
      ```bash
      gcloud storage rewrite gs://[BUCKET_NAME]/** --encryption-key=[NEW_KEY_RESOURCE_PATH]
      ```
    * **BigQuery:** Run a `SELECT *` query and write the output to a new table encrypted with the new key, or use the BigQuery table copy function.
    * **Compute Engine:** Create a snapshot of the disk using the new key, and recreate the instance/disk from that snapshot.
3. **Destroy Old Material:** Once 100% of the data has been verified as successfully re-encrypted with the new key version, schedule the compromised key version for destruction.

### 6.3 Reconcile IaC State (Stellar GitOps)
1. **Update Terraform:** Ensure that the new KMS IAM bindings, key rotation schedules, or key states are accurately reflected in the Stellar FAST repositories.
2. **Apply State:** Run `terraform apply` through the trusted CI/CD pipeline to ensure the emergency manual changes are permanently codified and won't be overwritten on the next automated run.

---

## Phase 7: Lessons Learned

### 7.1 Post-Incident Review (PIR)
1. Conduct a PIR with Security, Platform, and Data owners within 5 business days.
2. **Identify Root Cause:** How did the compromise or accidental deletion occur? (e.g., compromised admin credentials, misconfigured Terraform module, lack of IAM guardrails).

### 7.2 Preventative Measures & Remediation
1. **Organization Policies:** Ensure GCP Organization Policies are in place to restrict KMS administration.
2. **Terraform Guardrails:** Implement Terraform `lifecycle { prevent_destroy = true }` blocks on all critical `google_kms_crypto_key` resources within the Stellar codebase.
3. **Separation of Duties:** Ensure the identities that *administer* keys (KMS Admins) are strictly separated from the identities that *use* keys (Encrypter/Decrypters).
4. **Alerting:** Tune SCC or SIEM alerts to immediately page the on-call engineer for any `DestroyCryptoKeyVersion` events in production projects.
