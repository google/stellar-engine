# Incident Response Runbook: VPC Service Controls (VPC-SC) Perimeter Violations

## Document Control
| Attribute | Detail |
| :--- | :--- |
| **Runbook ID** | IR-VPC-001 |
| **Last Updated** | YYYY-MM-DD |
| **Owner** | Security Operations / Cloud Platform Team |
| **Target SLA** | Triage: 15m \| Containment: 60m \| Resolution: 4h |


> [!NOTE]
> **SIEM & Threat Detection Tooling**:
> Threat monitoring and security operations are driven by the services enabled in the environment configuration:
> - **Cloud-Native Posture & Threat Detection**: Where Security Command Center (SCC) or Google Cloud SecOps (Chronicle) is enabled, Event Threat Detection (ETD) and Security Health Analytics (SHA) provide native cloud threat alerts.
> - **Centralized SIEM / CSSP Integration**: Telemetry and audit trails route via Cloud Logging export sinks to the configured external CSSP / SIEM (e.g. {{ CSSP_PROVIDER }}, {{ EXTERNAL_SIEM }}) for centralized 24/7 security monitoring.

{{ DISCOVERED_ENVIRONMENT_CONTEXT }}

## 1. Objective
This runbook provides a structured process for Security Operators and Incident Responders to identify, triage, and respond to VPC Service Controls (VPC-SC) perimeter violations and potential data exfiltration incidents within the {{ SYSTEM_NAME }} cloud architecture on {{ CLOUD_PROVIDER }} ({{ CSP_ABBR }}).

## 2. Target Audience & Prerequisites
**Audience:**
* Security Operations Center (SOC) Analysts (L1/L2/L3)
* Incident Responders
* Cloud Network Security / Platform Teams

**Prerequisites for Responders:**
* **Audit & Log Inspection:** `roles/logging.viewer` and `roles/logging.privateLogViewer` on the {{ ORGANIZATION }} Organization to view audit logs and violation records.
* **Security & Posture Management (where SCC is enabled):** `roles/securitycenter.viewer` (or `roles/securitycenter.admin`) on the {{ ORGANIZATION }} Organization to view security findings and posture dashboards.
* `roles/accesscontextmanager.policyViewer` to view perimeter and access level configurations.
* `roles/accesscontextmanager.policyAdmin` (via Break-Glass/Emergency Access) to modify perimeters if immediate containment is required.
* Access to configured external CSOC / SIEM console (e.g. {{ CSSP_PROVIDER }} / {{ EXTERNAL_SIEM }}) where centralized audit telemetry streams.

## 3. Scope
This runbook applies to all environments deployed using the {{ SYSTEM_NAME }} foundation (including FedRAMP High, FedRAMP Moderate, and IL5 landing zones) where VPC-SC is used to protect sensitive data and mitigate data exfiltration risks.

---

## Phase 1: Identification & Scoping

### 1.1 Detection Sources
Monitor for the following indicators of compromise (IoCs):
* **Cloud Logging:** `cloudaudit.googleapis.com/policy` logs indicating a `VpcServiceControlsAuditMetadata` event.
* **Security Command Center (SCC) (where enabled):** Native alerts for VPC Service Controls violations.
* **External CSSP / SIEM (DoD IL4 / DoD IL5):** Automated alerts triggered by violation log metrics exported from Cloud Logging to external SIEM/SOAR platforms ({{ CSSP_PROVIDER }}, {{ EXTERNAL_SIEM }}).
* **Developer Reports:** Users reporting unexpected `HTTP 403 Forbidden` or `PERMISSION_DENIED` errors when accessing GCP services.

### 1.2 Initial Assessment & Log Extraction
1. **Locate the Violation Log:** Use Log Explorer to pinpoint the specific denial.
    * **Log Explorer Query Example:**
        ```text
        logName="organizations/[ORG_ID]/logs/cloudaudit.googleapis.com%2Fpolicy"
        AND protoPayload.metadata.@type="[type.googleapis.com/google.cloud.audit.VpcServiceControlsAuditMetadata](https://type.googleapis.com/google.cloud.audit.VpcServiceControlsAuditMetadata)"
        AND protoPayload.metadata.violationReason:*
        ```
2. **Extract Key Details:** Identify the following fields from the `protoPayload.metadata`:
    * `callerIp`: The IP address originating the request.
    * `principalEmail`: The IAM identity making the request.
    * `targetResource`: The resource being accessed (e.g., a specific Cloud Storage bucket).
    * `serviceName`: The GCP service API being targeted (e.g., `storage.googleapis.com`).
    * `violationReason`: The reason for the denial (e.g., `NO_MATCHING_ACCESS_LEVEL`, `NETWORK_NOT_IN_SAME_SERVICE_PERIMETER`).
    * `ingressViolations` / `egressViolations`: Determines the direction of the blocked traffic.

### 1.3 Escalation & Military Service Branch Reporting
* If violation indicates confirmed exfiltration attempt, immediately declare SEV 1 incident and notify On-Call Incident Commander.
* **Military Service Branch & DoD CSSP Escalation (CJCSM 6510.01B):**
  * **Army (USA):** Escalate to **Army RCERT** & **NETCOM** via Army C5ISR portal. Cat 1 (Exfiltration/Compromise): within **1 hour**.
  * **Air Force (USAF):** Escalate to **616th Operations Center (616 OC)** / 16th AF. Cat 1: within **1 hour**.
  * **Navy / Marines (USN / USMC):** Escalate to **NAVIFOR / NCDOC** or **MCCOG**. Cat 1: within **1 hour**.
  * **Space Force (USSF):** Escalate to **Space Delta 6 (Cyber Operations)**. Cat 1: within **1 hour**.
  * **Defense-Wide:** Escalate to **DISA / JFHQ-DODIN** via DICS. Cat 1: within **1 hour**; Cat 2: within **2 hours**.

---

## Phase 2: Triage and Analysis

**Goal:** Determine if the violation is a misconfiguration/False Positive (legitimate traffic blocked) or an attack/True Positive (attempted data exfiltration or unauthorized access).

### 2.1 Use the VPC-SC Troubleshooter
Leverage the GCP Console's built-in tool for rapid analysis:
1. Navigate to **Security** -> **VPC Service Controls** -> **Troubleshooter**.
2. Input the `uniqueId` from the VPC-SC violation log.
3. Review the API assessment to understand exactly which Access Level, Ingress Rule, or Egress Rule failed.

### 2.2 Misconfiguration Analysis (False Positive)
Check if the violation correlates with legitimate administrative or developer activity:
1. **Check Recent Changes:** Have there been recent Terraform / Infrastructure as Code deployments modifying Access Context Manager (ACM) policies, Access Levels, or adding new projects to perimeters?
2. **Verify Identity:** Is `principalEmail` a known CI/CD service account, developer, or automated pipeline performing an expected task?
3. **Context Check:** Is the `callerIp` from a known corporate VPN, an authorized egress NAT gateway, or an internal subnetwork?
4. **Dry-Run Analysis:** Was the project recently moved from a `dry-run` perimeter to an enforced perimeter without updating necessary ingress/egress rules?

### 2.3 Attack Analysis (Potential Exfiltration / True Positive)
If the activity cannot be linked to authorized operations, treat it as a potential attack:
1. **Unknown Identity:** Is the request coming from an external identity or a highly privileged service account acting anomalously?
2. **Unexpected Location:** Does the `callerIp` belong to an unknown ASN, Tor exit node, or unexpected geographic location?
3. **High Volume/Scanning:** Are there rapid, repeated violations targeting multiple distinct `targetResource` paths?
4. **Sensitive Target:** Is the target a critical database or bucket (e.g., customer PII, tfstate buckets, secrets)?

---

## Phase 3: Containment

**Goal:** Ensure the perimeter holds, stop potential data exfiltration, and isolate compromised components.

### 3.1 Immediate Actions (If True Positive Attack)
*Note: If VPC-SC blocked the request, the exfiltration was successfully prevented. However, the actor still has access to the credential or network.*
1. **Isolate the Identity:** If the log shows a compromised internal identity (`principalEmail`), immediately trigger the **IR-IAM-001 (Compromised IAM Credentials)** runbook to suspend the user or disable the service account.
2. **Isolate Compute Resources:** If the `callerIp` originates from an internal Compute Engine instance or GKE node, snapshot the instance for forensics, then isolate it from the network via strict VPC Firewall rules.
3. **Block External Threat Actors:** If the `callerIp` is external and malicious, update Access Levels to explicitly deny the IP block, or update Cloud Armor policies if applicable.

### 3.2 Do NOT Loosen Perimeters During Active Incidents
Under no circumstances should the VPC-SC perimeter be loosened or disabled to "see what the attacker is doing." Maintain the integrity of the boundary.

---

## Phase 4: Eradication and Recovery

**Goal:** Fix the root cause and restore normal operations via Infrastructure as Code (IaC).

### 4.1 Resolving Misconfigurations (False Positives)
Because {{ SYSTEM_NAME }} operates on a strict declarative GitOps model:
1. **Identify the Missing Rule:** Determine if an Access Level needs a new IP range/identity, or if an Ingress/Egress rule is missing.
2. **Update IaC (Terraform):** Modify the corresponding Terraform definitions in your {{ SYSTEM_NAME }} Infrastructure as Code repository (typically within the `access_context_manager` or `vpc-sc` modules).
3. **Test in Dry-Run:** If possible, apply the new rules to a dry-run perimeter first to ensure they resolve the violation without opening unintended gaps.
4. **Deploy:** Merge the Pull Request and allow the CI/CD pipeline to apply the changes.
5. **Verify Fix:** Confirm with the user/system owner that legitimate traffic now passes without generating `violationReason` logs.

### 4.2 Recovering from Attacks (True Positives)
1. **Verify Eradication:** Ensure all compromised credentials have been rotated and malicious internal workloads have been destroyed.
2. **Verify Perimeter Integrity:** Review recent Terraform state changes to ensure the threat actor did not successfully modify VPC-SC configurations to create a backdoor before being contained.

---

## Phase 5: Lessons Learned

### 5.1 Post-Incident Review
1. Conduct a post-incident review (PIR) with Security, Network, and the affected service teams within 5 business days.
2. **For False Positives:** Identify why the required access was missed during the initial VPC-SC design phase. Improve developer training on requesting VPC-SC exceptions via IaC.
3. **For True Positives:** Analyze how the attacker gained the initial credentials or network foothold. 
4. **Tune Alerts:** Adjust SIEM/SCC alerting thresholds to reduce alert fatigue for known noisy (but benign) VPC-SC violations.
5. **Update Runbook:** Incorporate any new troubleshooting steps, `gcloud` commands, or queries discovered during the incident.
