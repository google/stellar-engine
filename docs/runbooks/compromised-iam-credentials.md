# Incident Response Runbook: Compromised IAM Credentials

## Document Control
| Attribute | Detail |
| :--- | :--- |
| **Runbook ID** | IR-IAM-001 |
| **Last Updated** | YYYY-MM-DD |
| **Owner** | Security Operations / Cloud Platform Team |
| **Target SLA** | Triage: 15m \| Containment: 60m \| Eradication: 4h |

## 1. Objective
This runbook provides a structured, actionable process for Security Operators and Incident Responders to identify, contain, eradicate, and recover from incidents involving compromised Identity and Access Management (IAM) credentials within the Stellar architecture on Google Cloud Platform (GCP).

## 2. Target Audience & Prerequisites
**Audience:**
* Security Operations Center (SOC) Analysts (L1/L2/L3)
* Incident Responders
* Platform/Customer Security Teams

**Prerequisites for Responders:**
* `roles/logging.viewer` and `roles/securitycenter.admin` on the Stellar Organization.
* `roles/iam.securityAdmin` or a custom Break-Glass / Emergency Access role for containment actions.
* Google Workspace Super Admin or User Management Admin privileges (if responding to a human identity compromise).

## 3. Scope
This runbook applies to all environments deployed using the Stellar framework, including FedRAMP High, IL5, and standard landing zones. It covers the compromise of:
* **Google Workspace User Accounts:** Administrators, developers, and operators.
* **Google Cloud Service Accounts:** Especially highly privileged automation accounts used in FAST (Fabrication and Setup Tool) stages.
* **Workload Identity Federation (WIF) Identities:** Compromised external identities mapped to GCP roles.

---

## Phase 1: Identification & Triage

### 1.1 Detection Sources
Monitor for the following indicators of compromise (IoCs):
* **Security Command Center (SCC):** Look for `Leaked Credentials`, `Anomalous IAM Grants`, or `Unusual compute resource creation` finding classes.
* **Cloud Logging:** Spikes in API errors (e.g., `PERMISSION_DENIED`), or critical API calls from unexpected ASNs, IPs, or geographic locations.
* **VPC Service Controls (VPC-SC):** Deny events logged in `vpc-service-controls.googleapis.com` indicating a compromised identity attempting to extract data outside the trusted perimeter.
* **Billing Alerts:** Sudden, unexplained spikes in GCP spend.
* **External Notifications:** Threat Intel feeds, GitHub secret scanning alerts, or user reports.

### 1.2 Verification & Scoping
1.  **Analyze the Alert:** Determine the validity of the alert. Is it a known False Positive (e.g., scheduled pen-test, approved break-glass activity)?
2.  **Identify the Identity:** Document the exact principal (e.g., `jane.doe@example.com` or `fast-prod-sa@my-project.iam.gserviceaccount.com`).
3.  **Establish Blast Radius:**
    * Query Cloud Audit Logs (Admin Activity and Data Access) for the last 72 hours.
    * **Log Explorer Query Example:**
        ```text
        protoPayload.authenticationInfo.principalEmail="[COMPROMISED_IDENTITY_EMAIL]"
        AND logName:("cloudaudit.googleapis.com%2Factivity" OR "cloudaudit.googleapis.com%2Fdata_access")
        ```
4.  **Determine Severity:**
    * **SEV 1 (Critical):** High-privileged SA (e.g., FAST Bootstrap SA) or Org Admin compromised. Evidence of lateral movement or data exfiltration.
    * **SEV 2 (High):** Standard user or low-privileged SA compromised. Malicious resources created (e.g., crypto miners) but no exfiltration detected.
    * **SEV 3 (Medium):** Credential leaked (e.g., on GitHub) but no unauthorized access logs observed yet.

### 1.3 Escalation
* If SEV 1 or SEV 2, immediately declare an incident in the ticketing system and page the On-Call Incident Commander (IC).
* Open a dedicated incident communication channel (e.g., Slack `#inc-iam-compromise-123`).

---

## Phase 2: Containment

**Goal:** Stop the attacker from causing further damage, immediately severing their access.

### 2.1 Immediate Actions (User Accounts)
1.  **Suspend the User:** In Google Workspace Admin Console, suspend the account to prevent new logins.
2.  **Revoke Sessions & Tokens:** Force an immediate session termination.
    * Reset the user's sign-in cookies.
    * Revoke 3rd-party OAuth application access authorized by the user.
3.  **Reset Credentials:** Force a password reset and invalidate current MFA tokens (in case of a Man-in-the-Middle/AiTM attack).

### 2.2 Immediate Actions (Service Accounts)
1.  **Disable the Service Account:** This stops all new API authentications immediately without deleting the resource.
    ```bash
    gcloud iam service-accounts disable [SA_EMAIL] --project=[PROJECT_ID]
    ```
2.  **Rotate User-Managed Keys:** If the SA utilizes exported JSON keys (highly discouraged in Stellar, but possible), find and delete them.
    ```bash
    # List keys
    gcloud iam service-accounts keys list --iam-account=[SA_EMAIL] --project=[PROJECT_ID]
    # Delete the compromised key
    gcloud iam service-accounts keys delete [KEY_ID] --iam-account=[SA_EMAIL] --project=[PROJECT_ID]
    ```
3.  **Revoke IAM Bindings (Emergency Only):** If disabling the SA causes critical, unacceptable production outage, selectively remove the specific IAM bindings being abused by the attacker.

### 2.3 Network Containment (VPC-SC)
* If data exfiltration is ongoing, temporarily tighten VPC-SC perimeters by removing any ingress/egress rules that the attacker is leveraging.
* *(Caution: Modifying VPC-SC during an incident can cause wide-scale denial of service. Consult the network lead).*

---

## Phase 3: Eradication

**Goal:** Remove the threat actor's access, eliminate persistence mechanisms, and remediate the root cause.

### 3.1 Identify & Remove Persistence
Attackers often create backdoors to maintain access even after the initial credential is revoked. Investigate and revert:
1.  **Rogue IAM Grants:** Did the attacker grant `roles/owner` or `roles/editor` to a foreign Gmail account?
    * *Query:* `protoPayload.methodName="SetIamPolicy"` by the compromised identity.
2.  **New Service Accounts:** Did they spawn new SAs?
    * *Query:* `protoPayload.methodName="google.iam.admin.v1.CreateServiceAccount"`
3.  **SSH Keys / OS Login:** Did they inject SSH keys into project metadata or individual Compute Engine instances?
4.  **API Keys & OAuth Clients:** Check for newly generated API keys or malicious OAuth clients created in the GCP project.

### 3.2 Audit Resource Creation & Data Exfiltration
1.  **Compute/Serverless:** Check for newly created Compute Engine instances, Cloud Run services, or Cloud Functions (often used for crypto-mining or C2 nodes). Delete them.
2.  **Data Exfiltration:** Review Data Access logs for massive read operations on Cloud Storage buckets, BigQuery tables, or Cloud SQL instances.
3.  **Firewall Rules:** Ensure no "Allow All" (0.0.0.0/0) firewall rules were created to expose internal databases.

### 3.3 Enforce Infrastructure as Code (IaC) State
Because Stellar uses a GitOps model (FAST):
1.  **Compare State:** Run a `terraform plan` against the affected landing zones. Any malicious resources or IAM drift created by the attacker via ClickOps/CLI will show up as state drift.
2.  **Revert Drift:** If unauthorized drift is detected, carefully run `terraform apply` from the trusted CI/CD pipeline to revert the environment to the last known good configuration.

---

## Phase 4: Recovery

**Goal:** Restore normal operations securely and validate system integrity.

### 4.1 Restore Access
1.  **For Users:** Once the endpoint is confirmed clean (no malware) and the user has been briefed, un-suspend the account, enforce a new strong password, and require the registration of a new hardware security key (FIDO2/WebAuthn).
2.  **For Service Accounts:** Generate new keys (if strictly necessary) or migrate the workload to Workload Identity Federation. Update the CI/CD pipeline secrets manager with the new credentials. Re-enable the SA.
    ```bash
    gcloud iam service-accounts enable [SA_EMAIL] --project=[PROJECT_ID]
    ```

### 4.2 Verify Integrity
1.  Confirm all applications relying on the credentials have successfully re-authenticated and are functioning.
2.  Implement a "Hyper-Care" monitoring period. Set up custom Log Metrics and alerts targeting the affected identities and projects for the next 72 hours.

---

## Phase 5: Lessons Learned & Post-Incident

### 5.1 Blameless Post-Mortem
1.  Within 5 business days, schedule a blameless Post-Incident Review (PIR) with Security, Operations, and the affected team.
2.  Document the incident timeline (Detection, Containment, Resolution).

### 5.2 Root Cause Analysis (RCA) & Remediation
1.  **Identify the Root Cause:** How were the credentials stolen? (e.g., Phishing, hardcoded secret in GitHub, lack of MFA, endpoint malware).
2.  **Implement Preventative Measures:**
    * *If a key was leaked:* Can we eliminate the need for exported SA keys entirely by migrating to Workload Identity Federation or attaching the SA directly to the compute resource?
    * *If a user was phished:* Can we enforce FIDO2 Hardware Keys for all privileged Workspace accounts?
    * *VPC-SC:* Can we restrict API access from untrusted IPs using Access Context Manager?
3.  **Update Playbooks:** Incorporate any missing queries, tools, or process gaps discovered during the incident into this runbook.
