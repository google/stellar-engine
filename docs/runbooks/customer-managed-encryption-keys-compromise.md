# CMEK compromise response runbook

Use this runbook to identify, contain, and recover from the compromise, accidental destruction, or access loss of Customer-Managed Encryption Keys in Cloud KMS across Stellar Engine environments on Google Cloud.

| Attribute | Detail |
| :--- | :--- |
| Runbook ID | IR-CMEK-001 |
| Last updated | YYYY-MM-DD |
| Owner | Security Operations / Cloud Platform Team |
| Target SLA | Triage: 15m \| Containment: 30m \| Recovery: 4h to 24h based on re-encryption volume |

## 1. Runbook objective

This runbook guides security operators and incident responders through identifying, containing, and recovering from compromised, scheduled-for-destruction, or inaccessible Customer-Managed Encryption Keys managed in Cloud KMS across Stellar Engine landing zones on Google Cloud.

## 2. Audience and prerequisites

### 2.1 Target audience

- Security Operations Center analysts
- Incident responders
- Cloud infrastructure and platform engineers

### 2.2 Responder prerequisites

- The `roles/logging.viewer` role to inspect Cloud Audit Logs.
- The `roles/cloudkms.viewer` role to inspect key rings, key versions, and rotation settings.
- The `roles/cloudkms.admin` role via break-glass emergency access to disable, restore, or rotate keys during containment.
- Working access to the Stellar Engine GitOps repository to reconcile unauthorized Terraform changes.

## 3. Operational scope

This runbook applies to all Stellar Engine landing zones, including FedRAMP High, FedRAMP Moderate, IL4, and IL5 environments where CMEK protects data at rest. Key rings and keys live in centralized infrastructure projects such as `<prefix>-prod-iac-core-0`, `<prefix>-prod-audit-logs-0`, `<prefix>-<env>-<tenant>-iac-core-0`, `<prefix>-net-vdss-host`, and opt-in Stage 3 security projects `<prefix>-{dev,prod}-sec-core-0`, with symmetric key rotation constrained to 90 days (`7776000s`) or less by `custom.kmsRotation` and HSM protection used for FedRAMP High, IL4, and IL5. The procedures cover four scenarios:

- Compromise of symmetric or asymmetric Cloud KMS keys.
- Unauthorized or accidental scheduling of key version destruction.
- Loss of workload access caused by revoked IAM bindings on keys or key rings.
- External Key Manager connectivity failures in deployments that use external key custody.

## 4. Identification and scoping

### 4.1 Detection sources

Monitor these telemetry sources for indicators of CMEK compromise or loss:

- Cloud Logging administrative audit entries targeting the `cloudkms.googleapis.com` service.
- Security Command Center alerts reporting anomalous Cloud KMS activity, unexpected administrative calls, or policy violations.
- Availability alerts showing widespread HTTP 500 status codes, failed workload startups, or Cloud Storage and BigQuery `PERMISSION_DENIED` and `FAILED_PRECONDITION` errors caused by a disabled key.
- Key Access Justifications audit logs containing unexpected justification codes in FedRAMP High, FedRAMP Moderate, IL4, and IL5 environments.

### 4.2 Initial log assessment

1. Locate the triggering Cloud KMS administrative event in Logs Explorer scoped to the organization or the centralized `audit-logs` Cloud Logging bucket in `<prefix>-prod-audit-logs-0`:
   ```text
   log_id("cloudaudit.googleapis.com/activity")
   AND protoPayload.serviceName="cloudkms.googleapis.com"
   AND protoPayload.methodName:("DestroyCryptoKeyVersion" OR "DisableCryptoKeyVersion" OR "UpdateCryptoKeyPrimaryVersion" OR "SetIamPolicy")
   ```
   Also inspect `log_id("cloudaudit.googleapis.com/data_access")` filtered to `protoPayload.serviceName="cloudkms.googleapis.com"` when investigating unauthorized key use (`Encrypt`, `Decrypt`, `AsymmetricSign`, or `AsymmetricDecrypt`).
2. Record the key attributes from the audit log entry:
   - Record the `protoPayload.authenticationInfo.principalEmail` field to identify the principal that executed the change.
   - Record the `protoPayload.resourceName` field for the full path to the affected key or key version, such as `projects/my-kms-project/locations/us-east4/keyRings/my-keyring/cryptoKeys/my-key/cryptoKeyVersions/1`.
   - Record the `protoPayload.methodName` field for the exact Cloud KMS API method invoked.
3. Assign incident severity based on key state and data impact:
   - Assign SEV 1 critical severity when an active key version is compromised or scheduled for destruction, creating an immediate risk of unauthorized decryption or permanent data loss.
   - Assign SEV 2 high severity when a key version is disabled or required IAM bindings are removed, causing a production outage while the key material remains intact.
   - Assign SEV 3 medium severity for unexpected key rotation or administrative IAM changes with no outage or confirmed compromise.

## 5. Threat containment

Stop unauthorized data decryption, cancel destructive key operations, and preserve key state for recovery.

### 5.1 Compromised key containment

Disabling a key version immediately interrupts read and write operations on every Google Cloud service encrypted with that version. Coordinate with workload owners when possible, and disable the version immediately if active data exfiltration is confirmed:

1. Disable the compromised Cloud KMS key version to block further decryption calls:
   ```bash
   gcloud kms keys versions disable [VERSION] \
       --key=[KEY_NAME] \
       --keyring=[KEYRING_NAME] \
       --location=[LOCATION] \
       --project=[KMS_PROJECT_ID]
   ```
2. Execute the [IR-IAM-001](compromised-iam-credentials.md) runbook immediately to suspend the user or disable the service account that exposed key access.

### 5.2 Scheduled destruction recovery

Destroying a Cloud KMS key version through the API or Google Cloud console places the version in a scheduled-for-destruction state with a default 30-day soft-delete window, configurable down to a 24-hour minimum, before Google Cloud permanently erases the key material:

1. Restore the scheduled key version immediately before the destruction window expires:
   ```bash
   gcloud kms keys versions restore [VERSION] \
       --key=[KEY_NAME] \
       --keyring=[KEYRING_NAME] \
       --location=[LOCATION] \
       --project=[KMS_PROJECT_ID]
   ```

### 5.3 IAM access restoration

1. Pause automated Terraform CI/CD pipelines when a misconfigured deployment strips Cloud KMS IAM bindings so the pipeline does not reapply the broken state.
2. Re-grant the `roles/cloudkms.cryptoKeyEncrypterDecrypter` role to the affected service agents and workload service accounts through `gcloud` or the Google Cloud console to restore immediate service availability.

## 6. Eradication and recovery

Generate clean cryptographic material, re-encrypt affected data at rest, and align Terraform state.

### 6.1 Key rotation

1. Create a new Cloud KMS key version and promote it to primary for symmetric keys after confirming compromise of the previous primary version, or update workload references directly when rotating an asymmetric key because asymmetric keys do not use a primary version:
   ```bash
   gcloud kms keys versions create --key=[KEY_NAME] --keyring=[KEYRING_NAME] --location=[LOCATION] --project=[KMS_PROJECT_ID] --primary
   # Or update the primary version explicitly when the key version already exists
   gcloud kms keys update [KEY_NAME] --keyring=[KEYRING_NAME] --location=[LOCATION] --project=[KMS_PROJECT_ID] --primary-version=[NEW_VERSION]
   ```

### 6.2 Data re-encryption

Rotating a Cloud KMS key encrypts new writes with the new primary key version, while existing data at rest remains encrypted under the previous version until rewritten:

1. Inventory all Cloud Storage buckets, BigQuery tables, and Compute Engine persistent disks protected by the compromised key version.
2. Rewrite existing data so Google Cloud re-encrypts every object, table, and disk under the new primary key version:
   - Rewrite Cloud Storage objects in place under the new key version:
     ```bash
     gcloud storage rewrite gs://[BUCKET_NAME]/** --encryption-key=[NEW_KEY_RESOURCE_PATH]
     ```
   - Copy BigQuery tables or write `SELECT *` query results into destination tables configured with the new key version.
   - Snapshot Compute Engine persistent disks using the new key version and recreate instances and disks from those snapshots.
3. Schedule the compromised key version for destruction only after verifying that all affected resources use the new key version:
   ```bash
   gcloud kms keys versions destroy [OLD_VERSION] --key=[KEY_NAME] --keyring=[KEYRING_NAME] --location=[LOCATION] --project=[KMS_PROJECT_ID]
   ```

### 6.3 Terraform state reconciliation

1. Update the KMS IAM bindings, rotation periods, and key configurations in the Stellar Engine landing zone repositories.
2. Run `terraform apply` from the trusted CI/CD pipeline so emergency manual changes are codified and preserved on subsequent pipeline runs.

## 7. Lessons learned

### 7.1 Post-incident review

1. Conduct a post-incident review within 5 business days with security, platform, and data owners.
2. Identify the root cause of the compromise or outage, such as compromised administrator credentials, a misconfigured Terraform change, or missing IAM guardrails.

### 7.2 Preventative controls

1. Enforce Google Cloud organization policies that restrict Cloud KMS administration and enforce key rotation intervals.
2. Configure Terraform `lifecycle { prevent_destroy = true }` blocks on critical `google_kms_crypto_key` resources.
3. Separate Cloud KMS administrative principals strictly from principals granted encrypter and decrypter roles.
4. Configure Security Command Center and SIEM alerts to page the on-call responder immediately on any `DestroyCryptoKeyVersion` event in production projects.
