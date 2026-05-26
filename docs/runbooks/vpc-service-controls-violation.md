# Incident Response Runbook: VPC Service Controls (VPC-SC) Perimeter Violations

## Document Control
| Attribute | Detail |
| :--- | :--- |
| **Runbook ID** | IR-VPC-001 |
| **Last Updated** | YYYY-MM-DD |
| **Owner** | Security Operations / Cloud Platform Team |
| **Target SLA** | Triage: 15m \| Containment: 60m \| Resolution: 4h |

## 1. Objective
This runbook provides a structured process for Security Operators and Incident Responders to identify, triage, and respond to VPC Service Controls (VPC-SC) perimeter violations and potential data exfiltration incidents within the Stellar architecture on Google Cloud Platform (GCP).

## 2. Target Audience & Prerequisites
**Audience:**
* Security Operations Center (SOC) Analysts (L1/L2/L3)
* Incident Responders
* Cloud Network Security / Platform Teams

**Prerequisites for Responders:**
* `roles/logging.viewer` on the Stellar Organization to view audit logs.
* `roles/accesscontextmanager.policyViewer` to view perimeter and access level configurations.
* `roles/accesscontextmanager.policyAdmin` (via Break-Glass/Emergency Access) to modify perimeters if immediate containment is required.

## 3. Scope
This runbook applies to all environments deployed using the Stellar framework (including FedRAMP High and IL5 landing zones) where VPC-SC is used to protect sensitive data and mitigate data exfiltration risks.

---

## Phase 1: Identification & Scoping

### 1.1 Detection Sources
Monitor for the following indicators of compromise (IoCs):
* **Cloud Logging:** `cloudaudit.googleapis.com/policy` logs indicating a `VpcServiceControlsAuditMetadata` event.
* **Security Command Center (SCC):** Native alerts for VPC Service Controls violations.
* **SIEM/SOAR:** Automated alerts triggered by violation log metrics.
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
1. **Check Recent Changes:** Have there been recent Terraform/FAST deployments modifying Access Context Manager (ACM) policies, Access Levels, or adding new projects to perimeters?
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
Because Stellar operates on a strict GitOps model via the FAST framework:
1. **Identify the Missing Rule:** Determine if an Access Level needs a new IP range/identity, or if an Ingress/Egress rule is missing.
2. **Update IaC (Terraform):** Modify the corresponding Terraform definitions in your Stellar code repository (typically within the `access_context_manager` or `vpc-sc` modules).
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
