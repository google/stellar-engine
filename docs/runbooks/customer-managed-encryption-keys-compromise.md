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

This runbook applies to all Stellar Engine landing zones, including FedRAMP High, FedRAMP Moderate, IL4, and IL5 environments where CMEK protects data at rest, covering four scenarios:

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

1. Locate the triggering Cloud KMS administrative event in Logs Explorer:
   ```text
   logName="organizations/[ORG_ID]/logs/cloudaudit.googleapis.com%2Factivity"
   AND resource.type="cloudkms_cryptokeyversion"
   AND protoPayload.methodName:("DestroyCryptoKeyVersion" OR "DisableCryptoKeyVersion" OR "UpdateCryptoKeyPrimaryVersion" OR "SetIamPolicy")
   ```
2. Record the key attributes from the audit log entry:
   - Record the `principalEmail` field to identify the principal that executed the change.
   - Record the `resourceName` field for the full path to the affected key version, such as `projects/my-kms-project/locations/us-east4/keyRings/my-keyring/cryptoKeys/my-key/cryptoKeyVersions/1`.
   - Record the `methodName` field for the exact Cloud KMS API method invoked.
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

Destroying a Cloud KMS key version through the API or Google Cloud console places the version in a scheduled-for-destruction state with a default 24-hour soft-delete window before Google Cloud permanently erases the key material:

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

1. Create a new Cloud KMS key version and promote it to primary after confirming compromise of the previous primary version:
   ```bash
   gcloud kms keys versions create --key=[KEY_NAME] --keyring=[KEYRING_NAME] --location=[LOCATION] --project=[KMS_PROJECT_ID]
   # Set the new version as primary
   gcloud kms keys update [KEY_NAME] --keyring=[KEYRING_NAME] --location=[LOCATION] --project=[KMS_PROJECT_ID] --primary-version=[NEW_VERSION]
   ```

### 6.2 Data re-encryption

Rotating a Cloud KMS key encrypts new writes with the new primary key version, while existing data at rest remains encrypted under the previous version until rewritten:

1. Inventory all Cloud Storage buckets, BigQuery tables, and Compute Engine persistent disks protected by the compromised key version.
2. Rewrite existing data so Google Cloud re-encrypts every object, table, and disk under the new primary key version:
   - Rewrite Cloud Storage objects in place under the new key version. `gcloud storage objects update` rewrites each object when `--encryption-key` is set, so the command below re-encrypts every matching object under the key you name:
     ```bash
     gcloud storage objects update "gs://[BUCKET_NAME]/**" --all-versions --encryption-key=projects/[KMS_PROJECT_ID]/locations/[LOCATION]/keyRings/[KEYRING_NAME]/cryptoKeys/[KEY_NAME]
     ```
     - Keep `--all-versions` for buckets with Object Versioning enabled: without it only the live version is rewritten, and noncurrent versions stay encrypted under the compromised key version. Alternatively, delete the noncurrent versions that your retention policy allows you to remove.
     - Cloud Storage cannot decrypt objects while their key version is disabled. If the version was disabled in section 5.1, re-enable it for the rewrite window under strictly scoped IAM, then disable it again as soon as the rewrite finishes.
   - Copy BigQuery tables or write `SELECT *` query results into destination tables configured with the new key version.
   - Snapshot Compute Engine persistent disks using the new key version and recreate instances and disks from those snapshots.
3. Schedule the compromised key version for destruction only after verifying that all affected resources use the new key version.

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
