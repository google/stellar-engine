# Incident response runbook template

Use this template to author incident response runbooks for specific threat scenarios in Stellar Engine environments on Google Cloud.

| Attribute | Detail |
| :--- | :--- |
| Runbook ID | IR-[XYZ]-00[X] |
| Last updated | YYYY-MM-DD |
| Owner | [Team name or role] |
| Target SLA | Triage: [X]m \| Containment: [X]m \| Resolution: [X]h |

## 1. Runbook objective

[State the specific threat, vulnerability, or incident type that this runbook addresses and the target outcome of the response.]

## 2. Audience and prerequisites

### 2.1 Target audience

- [Tier 1, tier 2, and tier 3 Security Operations Center analysts]
- [Incident responders]
- [Cloud infrastructure and network security engineers]

### 2.2 Responder prerequisites

- [List the IAM roles required to execute this runbook, such as the `roles/logging.viewer` role.]
- [List the console or tool access required, such as Access Context Manager, Palo Alto Panorama, or Kubernetes RBAC permissions.]
- [Specify any emergency elevation or break-glass access procedures.]

## 3. Operational scope

[Define the environments, such as development, staging, and FedRAMP High or IL5 production landing zones, along with the cloud services, systems, and architectural components that this runbook covers.]

## 4. Identification and scoping

### 4.1 Detection sources

[List the primary telemetry sources, alerts, and logs that indicate this incident type.]

- [Document the Security Command Center finding class, alert ID, or detection rule name.]
- [Document the Cloud Logging log subtype, alert metric, or query indicator.]
- [Document third-party endpoint detection or SIEM alert signatures.]

### 4.2 Initial log assessment

[Describe the immediate steps to validate the alert and capture its core attributes.]

1. Navigate to the source alert or audit log in Logs Explorer and run the reusable query template:
   ```text
   [Insert reusable log query template here]
   ```
2. Extract and record the primary event attributes from the raw log payload:
   - Record the `principalEmail` or `identity` field to identify who initiated the action.
   - Record the `callerIp` field to capture the originating IP address, autonomous system number, and geographic location.
   - Record the `targetResource` field to identify the targeted project, instance, database, or bucket.
   - Record the `methodName` or `action` field to capture the exact API method executed.
3. Assign the preliminary incident severity based on operational and security impact:
   - Assign SEV 1 critical severity for production impact, active data exfiltration, or high-privilege account compromise requiring immediate escalation.
   - Assign SEV 2 high severity for non-production impact or isolated resource compromise without confirmed data loss.
   - Assign SEV 3 medium or low severity for operational drift, low-risk misconfigurations, or confirmed blocked attempts.

## 5. Triage and analysis

Verify the authenticity, scope, and impact of the incident to distinguish an active attack from an operational misconfiguration.

### 5.1 Attack versus misconfiguration

[Provide instructions for correlating historical events, change management records, and operational context.]

1. Check recent Terraform pipeline runs and approved emergency break-glass changes to verify whether an authorized deployment triggered the alert.
2. Compare the observed IP ranges, API calls, and operating hours against historical baselines for the principal and target resource.

### 5.2 Blast radius assessment

[Provide steps to determine how far the threat actor penetrated the architecture.]

1. Classify the threat directionality as inbound, outbound toward external command-and-control or exfiltration endpoints, or lateral across project perimeters.
2. Determine whether the affected resource can access regulated data, Cloud KMS cryptographic keys, Secret Manager secrets, or adjacent cloud infrastructure.

## 6. Threat containment

Stop active data exfiltration, block lateral movement, and sever threat actor access while preserving forensic evidence.

### 6.1 Immediate containment actions

[Provide explicit technical instructions and CLI commands to isolate the threat.]

1. Revoke active sessions, suspend compromised user accounts, or disable affected service accounts:
   ```bash
   [Insert emergency CLI command template, e.g., gcloud iam service-accounts disable ...]
   ```
2. Isolate affected network paths by binding a quarantine Secure Tag and adding top-priority deny rules to the global or hierarchical network firewall policy when `BEFORE_CLASSIC_FIREWALL` is active, or attach restrictive classic network tags where classic firewall evaluation applies:
   ```bash
   # Global network firewall policy (BEFORE_CLASSIC_FIREWALL, Stage 2a) or classic tag fallback (Stage 2b)
   # gcloud compute network-firewall-policies rules create 1 --firewall-policy=[FW_POLICY] --global-firewall-policy --project=[NETWORK_HOST_PROJECT_ID] --direction=INGRESS --action=deny --layer4-configs=all --src-ip-ranges=0.0.0.0/0 --target-secure-tags=[QUARANTINE_TAG_VALUE_ID]
   ```
3. Update VPC Service Controls perimeters or Cloud Armor security policies to enforce strict boundaries around the incident zone.

## 7. Eradication and recovery

Eliminate threat actor persistence, remediate the root vulnerability, and restore resources to a verified state.

### 7.1 Eradication and forensics

1. Preserve volatile memory, snapshot persistent disks, and export container logs before destroying compromised resources:
   ```bash
   [Insert snapshot or forensic export command template]
   ```
2. Audit and remove persistence mechanisms, including unauthorized `SetIamPolicy` grants, rogue service accounts, injected SSH keys, and unauthorized API keys.
3. Patch the entry point, such as vulnerable software dependencies or exposed firewall ports.

### 7.2 Recovery and IaC alignment

1. Run Terraform plans and applies from a clean CI/CD pipeline against the GitOps configuration to reconcile cloud state and overwrite manual attacker changes.
2. Re-enable legitimate access after enforcing password resets, re-registering multifactor authentication keys, and rotating service account credentials.
3. Monitor targeted log metrics, dashboards, and detection rules closely for 72 hours to verify that threat activity does not resume.

## 8. Lessons learned

### 8.1 Post-incident review

[Address these review items during the post-incident review with cross-functional teams.]

1. Document exact timestamps for detection, triage, containment, eradication, and recovery.
2. Evaluate how the incident surfaced and whether detection thresholds or audit log configurations can detect similar activity earlier.
3. Identify bottlenecks during containment and eradication that runbook automation can streamline.
4. Codify long-term preventative controls, such as organization policies, VPC Service Controls rules, and stricter network segmentation, in the base Terraform framework to eliminate this attack vector.
