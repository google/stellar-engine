# Assured Workloads Day-2 operations guide

Use this runbook to triage Assured Workloads compliance violations, reconcile Google Cloud compliance updates with Terraform without drift, grant read-only Authorizing Official visibility, and govern Exception to Policy requests after initial landing zone deployment.

## 1. Violation inventory and triage

Query unresolved violations regularly so policy drift and resource compliance alerts are remediated before continuous monitoring audits.

Match the `--location` flag to the location where the Assured Workloads environment was created, such as `us` for multi-region U.S. workloads. Passing a Compute Engine region such as `us-east4` for a `us` workload returns an empty result set.

```bash
ORG_ID="123456789012"
AW_LOCATION="us"
WORKLOAD_ID="00-example-workload-id"

gcloud assured workloads violations list \
  --organization="$ORG_ID" \
  --location="$AW_LOCATION" \
  --workload="$WORKLOAD_ID" \
  --filter='state=UNRESOLVED' \
  --limit=200 \
  --format='table(name,category,orgPolicyConstraint,nonCompliantOrgPolicy,resourceName,beginTime)'
```

Inspect an individual violation with the full resource name returned by the list command to view its `associatedOrgPolicyViolationId` field, remediation guidance, and non-compliant policy values.

```bash
gcloud assured workloads violations describe \
  "organizations/${ORG_ID}/locations/${AW_LOCATION}/workloads/${WORKLOAD_ID}/violations/VIOLATION_ID"
```

Classify every violation before taking action.

- Organization policy violations arise when a folder or project policy adds a service outside the Assured Workloads allowlist or weakens a baseline control such as `gcp.restrictNonCmekServices`. Fix the governing Terraform configuration first so automated applies do not reintroduce the violation.
- Active resource violations arise when a workload creates a resource that violates an active compliance control. Remediate the resource configuration in Terraform before acknowledging or waiting for rescan resolution.
- Historical child resource violations carry an `associatedOrgPolicyViolationId` pointing to a parent organization policy violation that may already be resolved. Verify live resource compliance before acknowledging these records.

## 2. Regional updates API reconciliation

Assured Workloads publishes compliance baseline updates, such as changes to allowed services or CMEK-governed services, on the regional `/updates` REST endpoint. Always reconcile `AVAILABLE` updates with your Terraform repository before applying them so your next `terraform apply` does not revert the update.

The `gcloud assured workloads` command group does not expose a subcommand for listing or applying workload updates. Call the regional endpoint matching your workload location and pass the `X-Goog-User-Project` header set to a project with `assuredworkloads.googleapis.com` enabled. Omitting `X-Goog-User-Project` causes user-credential REST calls to fail with `403 SERVICE_DISABLED` against the default Cloud SDK quota project.

```bash
ORG_ID="123456789012"
AW_LOCATION="us"
WORKLOAD_ID="00-example-workload-id"
QUOTA_PROJECT="acme-platform-iac"

printf 'Authorization: Bearer %s\n' "$(gcloud auth print-access-token)" | \
  curl -sS -H @- -H "X-Goog-User-Project: ${QUOTA_PROJECT}" \
  "https://${AW_LOCATION}-assuredworkloads.googleapis.com/v1/organizations/${ORG_ID}/locations/${AW_LOCATION}/workloads/${WORKLOAD_ID}/updates"
```

Passing the bearer token to `curl` through standard input with `-H @-` keeps the token out of local process arguments.

Follow this reconciliation sequence for every `AVAILABLE` update.

1. Inspect `details.orgPolicyUpdate.suggestedPolicy` and `details.orgPolicyUpdate.appliedPolicy` in the JSON response to see the exact additions or removals Assured Workloads expects.
2. Mirror the update in your Terraform organization policy definitions first, then run `terraform plan` and `terraform apply`.
3. For allowed-services updates that call `restrictAllowedResources`, mirror the updated service list in Terraform before triggering the update because applying it resets the folder `gcp.restrictServiceUsage` policy to the regime list.
4. Apply the Assured Workloads update record via the regional `updates/{updateId}:apply` endpoint with body `{"action":"APPLY"}` or through the Google Cloud console, then run `terraform plan` again to verify zero drift.

## 3. Historical child violation triage

Assured Workloads Resource Monitoring attaches `associatedOrgPolicyViolationId` to resource violations recorded while a parent organization policy violation was open. After the parent organization policy violation resolves, historical child resource violations do not auto-resolve and must be verified and acknowledged.

### Verifying regional Secret Manager CMEK

Before rotating or replacing any Secret Manager secret flagged as a historical child violation of `gcp.restrictNonCmekServices`, inspect the live `ENABLED` secret versions to confirm whether they already use Cloud KMS encryption.

Regional `gcloud secrets` commands fail with `INVALID_ARGUMENT` unless you point the Secret Manager API override at the regional endpoint.

```bash
SECRET_REGION="us-east4"
SECRET_PROJECT="acme-shared-services"
SECRET_NAME="example-tls-cert"

CLOUDSDK_API_ENDPOINT_OVERRIDES_SECRETMANAGER="https://secretmanager.${SECRET_REGION}.rep.googleapis.com/" \
  gcloud secrets versions list "$SECRET_NAME" \
  --project="$SECRET_PROJECT" \
  --location="$SECRET_REGION" \
  --filter='state=ENABLED' \
  --format='table(name,state,customerManagedEncryption.kmsKeyVersionName)'
```

Updating a secret's CMEK key applies only to newly added versions and never re-encrypts older versions. If every `ENABLED` version already reports a valid `kmsKeyVersionName`, do not rotate or destroy working credentials; acknowledge the historical violation with the verified key version evidence.

### Handling maintenance child violations

Resource Monitoring can record `maintenance.googleapis.com/ResourceMaintenance` child violations whenever a parent folder holds an unresolved `gcp.restrictServiceUsage` violation, even if `maintenance.googleapis.com` is already disabled in the affected projects.

1. Confirm the parent organization policy violation referenced by `associatedOrgPolicyViolationId` is in the `RESOLVED` state after applying the corrected folder allowlist in Terraform.
2. Verify with `gcloud services list --enabled --project=acme-workload-prod` that no disallowed API remains active in the affected project.
3. Acknowledge the remaining historical child violations with a concise audit justification referencing the resolved parent violation ID and verification date.

### Acknowledging verified violations

Use `gcloud assured workloads violations acknowledge` after confirming that live compliance holds or after recording an approved Exception to Policy. Pass `--acknowledge-type=SINGLE_VIOLATION` for individual historical resource records, or `--acknowledge-type=EXISTING_CHILD_RESOURCE_VIOLATIONS` when acknowledging an organization policy violation together with its existing child records.

```bash
gcloud assured workloads violations acknowledge \
  "organizations/${ORG_ID}/locations/${AW_LOCATION}/workloads/${WORKLOAD_ID}/violations/VIOLATION_ID" \
  --acknowledge-type=SINGLE_VIOLATION \
  --comment="Verified live CMEK kmsKeyVersionName on all ENABLED versions after parent org policy violation resolved on 2026-11-24."
```

Assured Workloads rescans asynchronously after Terraform policy changes, so newly remediated organization policy violations can take several minutes to transition to `RESOLVED`.

## 4. Authorizing Official read-only access

Grant Authorizing Officials, Security Control Assessors, and compliance auditors dedicated read-only visibility across Assured Workloads, Organization Policy, Security Command Center, VPC Service Controls, Cloud Asset Inventory, and Cloud Audit Logs without granting write permissions.

Bind the following predefined roles to a dedicated auditor group such as `gcp-ao-reviewers@example.com` at the organization or Assured Workloads folder level depending on authorization boundary scope.

| Role | Scope | Audit capability |
| :--- | :--- | :--- |
| `roles/assuredworkloads.reader` | Organization or Assured Workloads folder | Inspect Assured Workloads environments, compliance controls, and violation records |
| `roles/orgpolicy.policyViewer` | Organization or Assured Workloads folder | Inspect active and dry-run organization policies and custom constraints |
| `roles/securitycenter.adminViewer` | Organization or folder | Inspect Security Command Center posture, sources, and security findings |
| `roles/accesscontextmanager.policyReader` | Organization | Inspect Access Context Manager access levels and VPC Service Controls perimeters |
| `roles/cloudasset.viewer` | Organization or folder | Query Cloud Asset Inventory resource and IAM policy snapshots |
| `roles/logging.viewer` | Logging project or folder | Inspect Cloud Audit Logs, policy dry-run entries, and Access Transparency logs |
| `roles/resourcemanager.folderViewer` | Assured Workloads folder | Traverse the folder hierarchy inside the authorization boundary |
| `roles/browser` | Organization or folder | Browse resource hierarchy metadata in the Google Cloud console |

Follow strict separation of duties when provisioning auditor access.

- Assign auditor permissions exclusively to a managed identity group backed by phishing-resistant multi-factor authentication rather than individual accounts.
- Substitute `roles/securitycenter.findingsViewer` for `roles/securitycenter.adminViewer` when reviewers need findings access without Security Command Center configuration metadata.
- Omit `roles/assuredworkloads.editor`, `roles/assuredworkloads.admin`, `roles/orgpolicy.policyAdmin`, and `roles/secretmanager.secretAccessor` from reviewer bundles so auditors cannot modify policies, acknowledge violations unilaterally, or read workload secret payloads.

## 5. Exception to Policy workflow

When a mission workload cannot satisfy a landing zone guardrail immediately, govern the temporary deviation through a documented Exception to Policy workflow rather than relaxing organization-wide defaults.

1. Scope the request to the narrowest possible folder, project, or tagged resource rather than widening the organization or top-level Assured Workloads folder.
2. Document the architectural context, risk analysis, compensating controls, and expiration date using the [Architecture Decision Record template](./adr/template.md) and submit the package to the Authorizing Official for a risk acceptance decision.
3. Implement list-policy exceptions by merging the approved values into an explicit allowlist rule conditioned on an organization-scoped Resource Manager tag key rather than granting conditional `allow_all`, which disables the entire constraint on tagged resources.
4. Implement IAM Deny exceptions using explicit least-privilege service accounts or admin groups rather than broad wildcard or raw federation pool principals.
5. Record the approved Exception to Policy identifier, Authorizing Official approval date, and expiration date in the Terraform change description, the Plan of Action and Milestones, and any required Assured Workloads violation acknowledgement comment.
6. Review active exceptions on a recurring continuous monitoring cadence, renewing only with fresh Authorizing Official sign-off and removing expired exceptions through Terraform once the workload adopts the compliant pattern.

## 6. Related documentation

- Follow the [Path to authorization](./path-to-authorization.md) for Risk Management Framework phases and authorization package artifacts.
- Use the [Guardrails review rubric and test plan](./guardrails-rubric-and-test-plan.md) to test preventative controls before enforcement.
- Record exception decisions and architecture deltas with the [Architecture Decision Record template](./adr/template.md).
