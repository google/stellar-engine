# VPC-SC perimeter violation runbook

Use this runbook to identify, triage, contain, and resolve VPC Service Controls perimeter violations and attempted data exfiltration in Stellar Engine environments on Google Cloud.

| Attribute | Detail |
| :--- | :--- |
| Runbook ID | IR-VPC-001 |
| Last updated | YYYY-MM-DD |
| Owner | Security Operations / Cloud Platform Team |
| Target SLA | Triage: 15m \| Containment: 60m \| Resolution: 4h |

## 1. Runbook objective

This runbook guides security operators and incident responders through identifying, triaging, and resolving VPC Service Controls perimeter violations and attempted data exfiltration across Stellar Engine landing zones on Google Cloud.

## 2. Audience and prerequisites

### 2.1 Target audience

- Tier 1, tier 2, and tier 3 Security Operations Center analysts
- Incident responders
- Cloud network security and platform teams

### 2.2 Responder prerequisites

- The `roles/logging.viewer` role on the Stellar Engine organization to inspect Policy Denied audit logs.
- The `roles/accesscontextmanager.policyViewer` role to inspect service perimeters and access level definitions.
- The `roles/accesscontextmanager.policyAdmin` role via break-glass emergency access when emergency perimeter containment is required.

## 3. Operational scope

This runbook applies to all Stellar Engine landing zones, including FedRAMP High, FedRAMP Moderate, IL4, and IL5 environments that enforce VPC Service Controls perimeters to prevent unauthorized data movement.

## 4. Identification and scoping

### 4.1 Detection sources

Monitor these telemetry sources for VPC Service Controls violations:

- Cloud Logging entries in the `cloudaudit.googleapis.com/policy` log stream containing a `VpcServiceControlAuditMetadata` payload, centralized in the `vpc-sc` Cloud Logging bucket in `<prefix>-prod-audit-logs-0`.
- Security Command Center findings reporting VPC Service Controls perimeter denials.
- SIEM and SOAR alerts triggered by log-based violation metrics.
- Operator or developer reports of unexpected HTTP 403 Forbidden status codes or `PERMISSION_DENIED` errors when calling Google Cloud APIs.

### 4.2 Initial log assessment

1. Query Policy Denied audit logs in Logs Explorer scoped to the organization or the `vpc-sc` Cloud Logging bucket in `<prefix>-prod-audit-logs-0`:
   ```text
   log_id("cloudaudit.googleapis.com/policy")
   AND protoPayload.metadata.@type="type.googleapis.com/google.cloud.audit.VpcServiceControlAuditMetadata"
   AND protoPayload.metadata.violationReason:*
   ```
2. Record the violation attributes from the `protoPayload` audit log entry:
   - Record the `protoPayload.requestMetadata.callerIp` field for the originating client IP address.
   - Record the `protoPayload.authenticationInfo.principalEmail` field for the IAM principal that issued the request.
   - Record the `protoPayload.resourceName` and `protoPayload.metadata.resourceNames` fields for the protected resource, such as a Cloud Storage bucket or BigQuery dataset.
   - Record the `protoPayload.serviceName` field for the targeted Google Cloud service API, such as `storage.googleapis.com`.
   - Record the `protoPayload.metadata.violationReason` field, such as `NO_MATCHING_ACCESS_LEVEL` or `NETWORK_NOT_IN_SAME_SERVICE_PERIMETER`.
   - Record the `protoPayload.metadata.ingressViolations` and `protoPayload.metadata.egressViolations` fields to determine the direction of the blocked call.
   - Record the `protoPayload.metadata.vpcServiceControlsUniqueId` field for the VPC Service Controls troubleshooter lookup.

## 5. Triage and analysis

Determine whether the violation stems from an operational misconfiguration blocking legitimate traffic or an unauthorized attempt to access or exfiltrate protected data.

### 5.1 VPC-SC Troubleshooter analysis

Inspect the denial details in the Google Cloud console:

1. Open Security, select VPC Service Controls, and open Troubleshooter in the Google Cloud console.
2. Enter the `protoPayload.metadata.vpcServiceControlsUniqueId` value from the VPC Service Controls audit log entry.
3. Review the Troubleshooter evaluation to identify which access level, ingress rule, or egress rule denied the request.

### 5.2 Misconfiguration analysis

Correlate the violation with authorized platform or developer activity:

1. Check recent Terraform deployments that modified Access Context Manager policies, access levels, or perimeter project memberships.
2. Verify whether the `protoPayload.authenticationInfo.principalEmail` field belongs to a known CI/CD service account, developer, or platform automation job running an expected workflow.
3. Confirm whether the `protoPayload.requestMetadata.callerIp` address belongs to an approved corporate VPN range, authorized Cloud NAT gateway, or internal spoke subnet.
4. Check whether the project recently moved into an enforced `status` perimeter in `fast/stages-aw/3-security/vpc-sc.tf` or whether a recent `dry_run_spec` promotion lacked corresponding ingress or egress rules.

### 5.3 Attack analysis

Treat the event as a potential attack whenever the request does not match authorized operational activity:

1. Check whether the `protoPayload.authenticationInfo.principalEmail` identity is external to the organization or a privileged service account acting outside its normal pattern.
2. Check whether the `protoPayload.requestMetadata.callerIp` address resolves to an unrecognized autonomous system number, anonymizing proxy, or unexpected geographic region.
3. Check for rapid, repeated denials scanning multiple `protoPayload.resourceName` or `protoPayload.metadata.resourceNames` paths.
4. Check whether the targeted resource stores regulated data, Terraform state buckets, or Secret Manager secrets.

## 6. Threat containment

Preserve perimeter enforcement, block unauthorized data movement, and isolate compromised credentials or hosts.

### 6.1 Confirmed attack actions

A VPC Service Controls denial confirms that the perimeter blocked the immediate API request, while the threat actor still holds access to the originating credential or network path:

1. Execute the [IR-IAM-001](compromised-iam-credentials.md) runbook immediately to suspend the user or disable the service account when the violation involves a compromised internal `principalEmail` identity.
2. Snapshot the instance for forensic analysis and quarantine it via the [IR-COMP-001](compute-resource-compromise.md) runbook when the `protoPayload.requestMetadata.callerIp` address belongs to an internal Compute Engine virtual machine or GKE node.
3. Inspect Access Context Manager access levels to verify that no overly broad CIDR range or identity condition admits the malicious `protoPayload.requestMetadata.callerIp` address, because access levels act as allowlists rather than blocklists. Remove any untrusted CIDR or identity entry from the access level allowlist or tighten its custom CEL condition, and add a Cloud Armor security policy deny rule if malicious external requests also target workloads behind an external Application Load Balancer. Cloud Armor applies only to load-balanced HTTP and HTTPS traffic, while the VPC Service Controls perimeter blocks unauthorized Google Cloud API calls directly.

### 6.2 Perimeter boundary preservation

Never loosen an enforced perimeter, remove protected projects or restricted services, or set `dry_run = true` in `fast/stages-aw/3-security/vpc-sc.tf` during an active security incident, because setting `dry_run = true` clears the enforced `status` block to `status = null`. Keep the enforced `status` boundary intact throughout investigation and containment.

## 7. Eradication and recovery

Remediate the root cause and restore legitimate API access through Terraform.

### 7.1 Misconfiguration resolution

Resolve confirmed false positives through the Stellar Engine GitOps workflow:

1. Identify the specific access level IP range, principal entry, ingress rule, or egress rule needed for the legitimate workflow.
2. Update the Access Context Manager and VPC Service Controls Terraform configurations in the Stellar Engine repository.
3. Validate proposed rule changes using `dry_run_spec` alongside the enforced `status` perimeter in `fast/stages-aw/3-security/vpc-sc.tf`, verify in `cloudaudit.googleapis.com/policy` logs with `protoPayload.metadata.dryRun=true` that the change clears the denial without over-broadening access, and then promote the validated rules into `status`.
4. Merge the pull request so the trusted CI/CD pipeline applies the perimeter update.
5. Confirm with the workload owner that legitimate requests succeed without generating new `protoPayload.metadata.violationReason` log entries.

### 7.2 Attack recovery

1. Confirm that all compromised credentials are rotated and any unauthorized internal compute instances are destroyed.
2. Audit recent Terraform state history and Access Context Manager audit logs to verify that the attacker did not add unauthorized perimeter bridges, access levels, or egress rules before containment.

## 8. Lessons learned

### 8.1 Post-incident review

1. Conduct a post-incident review within 5 business days with security, network, and affected workload teams.
2. Review perimeter design intake procedures after false positives so teams declare required VPC Service Controls ingress and egress paths in Terraform before enforcement.
3. Document how the attacker obtained initial credentials or network access after confirmed attacks, and codify preventative controls.
4. Tune SIEM and Security Command Center alert thresholds to reduce noise from benign, expected perimeter denials while preserving high-signal exfiltration alerts.
5. Update this runbook with any new troubleshooting steps, `gcloud` commands, or log queries identified during the response.
