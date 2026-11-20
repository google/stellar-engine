# Compromised IAM credentials runbook

Use this runbook to identify, contain, eradicate, and recover from compromised Identity and Access Management credentials in Stellar Engine environments on Google Cloud.

| Attribute | Detail |
| :--- | :--- |
| Runbook ID | IR-IAM-001 |
| Last updated | YYYY-MM-DD |
| Owner | Security Operations / Cloud Platform Team |
| Target SLA | Triage: 15m \| Containment: 60m \| Eradication: 4h |

## 1. Runbook objective

This runbook guides security operators and incident responders through identifying, containing, eradicating, and recovering from compromised IAM credentials across Stellar Engine landing zones on Google Cloud.

## 2. Audience and prerequisites

### 2.1 Target audience

- Tier 1, tier 2, and tier 3 Security Operations Center analysts
- Incident responders
- Platform and customer security teams

### 2.2 Responder prerequisites

- The `roles/logging.viewer` and `roles/securitycenter.admin` roles on the Stellar Engine organization.
- The `roles/iam.securityAdmin` role or a dedicated break-glass emergency access role for containment actions.
- Google Workspace Super Admin or User Management Admin privileges when responding to a compromised human identity.

## 3. Operational scope

This runbook applies to all Stellar Engine environments, including FedRAMP High, FedRAMP Moderate, IL4, IL5, and standard landing zones, across three identity types:

- Google Workspace user accounts belonging to administrators, developers, and operators.
- Google Cloud service accounts, especially privileged automation accounts provisioned for landing zone stages.
- External Workload Identity Federation identities mapped to Google Cloud IAM roles.

## 4. Identification and triage

### 4.1 Detection sources

Monitor these telemetry sources for indicators of credential compromise:

- Security Command Center findings in the `Leaked Credentials`, `Anomalous IAM Grants`, and `Unusual compute resource creation` classes.
- Cloud Logging spikes in `PERMISSION_DENIED` status codes or privileged API calls originating from unexpected autonomous system numbers, IP addresses, or geographic locations.
- VPC Service Controls deny events in `vpc-service-controls.googleapis.com` audit logs showing an identity attempting to move data outside a trusted perimeter.
- Cloud Billing alerts showing sudden, unexplained increases in Google Cloud spend.
- External threat intelligence feeds, source repository secret scanning alerts, and user reports.

### 4.2 Verification and scoping

1. Validate the alert to confirm that scheduled penetration testing or approved break-glass activity did not trigger a false positive.
2. Record the exact compromised principal, such as `admin@example.com` or `fast-prod-sa@my-project.iam.gserviceaccount.com`.
3. Query Admin Activity and Data Access audit logs across the preceding 72 hours in Logs Explorer to establish the blast radius:
   ```text
   protoPayload.authenticationInfo.principalEmail="[COMPROMISED_IDENTITY_EMAIL]"
   AND logName:("cloudaudit.googleapis.com%2Factivity" OR "cloudaudit.googleapis.com%2Fdata_access")
   ```
4. Assign incident severity based on principal privilege and observed activity:
   - Assign SEV 1 critical severity when a high-privilege service account, such as the Stage 0 bootstrap service account, or an organization administrator account is compromised, or when logs show lateral movement or data exfiltration.
   - Assign SEV 2 high severity when a standard user or low-privilege service account is compromised and unauthorized resources such as cryptominers exist without data exfiltration.
   - Assign SEV 3 medium severity when a credential leaks externally, such as in a source repository, without unauthorized access logs.

### 4.3 Incident escalation

- Declare an incident in the ticketing system immediately and page the on-call Incident Commander for any SEV 1 or SEV 2 event.
- Open a dedicated incident communication channel, such as `#inc-iam-compromise-123`.

## 5. Threat containment

Sever attacker access immediately to prevent privilege escalation, lateral movement, and data exfiltration.

### 5.1 User account actions

1. Suspend the compromised user account in the Google Workspace Admin Console to block new sign-ins.
2. Terminate active sessions immediately by resetting the user's sign-in cookies and revoking third-party OAuth application grants authorized by the account.
3. Force a password reset and invalidate active multifactor authentication tokens to mitigate adversary-in-the-middle session hijacking.

### 5.2 Service account actions

1. Disable the service account to stop all new API authentications immediately without deleting the resource:
   ```bash
   gcloud iam service-accounts disable [SA_EMAIL] --project=[PROJECT_ID]
   ```
2. List and delete any exported user-managed service account keys, which Stellar Engine discourages:
   ```bash
   # List keys
   gcloud iam service-accounts keys list --iam-account=[SA_EMAIL] --project=[PROJECT_ID]
   # Delete the compromised key
   gcloud iam service-accounts keys delete [KEY_ID] --iam-account=[SA_EMAIL] --project=[PROJECT_ID]
   ```
3. Remove only the specific IAM bindings abused by the attacker as an emergency fallback when disabling the service account causes an unacceptable production outage.

### 5.3 Perimeter containment

- Tighten VPC Service Controls perimeters temporarily by removing ingress or egress rules that the attacker uses when active data exfiltration is underway.
- Consult the network lead before modifying VPC Service Controls perimeters during an incident because perimeter changes can disrupt dependent production services.

## 6. Threat eradication

Remove attacker access, eliminate persistence mechanisms, and remediate the initial entry vector.

### 6.1 Persistence removal

Audit affected projects and folders for backdoors that preserve access after credential revocation:

1. Query audit logs for `protoPayload.methodName="SetIamPolicy"` calls made by the compromised identity to detect unauthorized `roles/owner` or `roles/editor` grants to external accounts.
2. Query audit logs for `protoPayload.methodName="google.iam.admin.v1.CreateServiceAccount"` calls to identify rogue service accounts created by the attacker.
3. Inspect project metadata and individual Compute Engine instances for injected SSH keys or unauthorized OS Login profiles.
4. Audit the affected projects for newly generated API keys or unauthorized OAuth clients, and delete any unapproved credentials.

### 6.2 Resource and exfiltration audit

1. Inspect affected projects for unauthorized Compute Engine instances, Cloud Run services, and Cloud Functions used for cryptomining or command-and-control relays, and delete them.
2. Review Data Access audit logs for bulk read operations against Cloud Storage buckets, BigQuery tables, and Cloud SQL instances.
3. Verify that no permissive `0.0.0.0/0` firewall rules expose internal databases or workloads.

### 6.3 Terraform state enforcement

Reconcile live cloud configurations against the Stellar Engine GitOps repository:

1. Run `terraform plan` against the affected landing zone stages so unauthorized resources and manual IAM changes surface as state drift.
2. Run `terraform apply` from the trusted CI/CD pipeline to overwrite unauthorized drift and restore the last verified configuration.

## 7. Service recovery

Restore legitimate operations securely and verify workload health.

### 7.1 Access restoration

1. Confirm that the user's endpoint is free of malware, brief the user, unsuspend the Google Workspace account, enforce a new password, and require registration of a new FIDO2 or WebAuthn hardware security key.
2. Migrate affected workloads to Workload Identity Federation or provision replacement credentials where strictly required, update the CI/CD secret store, and re-enable the service account:
   ```bash
   gcloud iam service-accounts enable [SA_EMAIL] --project=[PROJECT_ID]
   ```

### 7.2 Integrity verification

1. Confirm that all dependent applications re-authenticate and operate normally.
2. Configure custom Cloud Logging metrics and alerts targeting the affected principals and projects for a 72-hour monitoring window.

## 8. Lessons learned

### 8.1 Post-incident review

1. Schedule a blameless post-incident review within 5 business days with security, operations, and the affected workload team.
2. Record the complete incident timeline across detection, containment, eradication, and recovery.

### 8.2 Root cause remediation

1. Identify how the attacker obtained the credentials, such as phishing, a secret committed to source control, missing multifactor authentication, or endpoint malware.
2. Apply targeted preventative controls based on the root cause:
   - Eliminate exported service account keys by migrating workloads to Workload Identity Federation or attaching service accounts directly to compute resources.
   - Enforce FIDO2 hardware security keys across all privileged Google Workspace accounts to prevent phishing.
   - Restrict API access from untrusted IP addresses using Access Context Manager access levels and VPC Service Controls perimeters.
3. Update this runbook with any additional log queries, tooling, or procedural improvements identified during the response.
