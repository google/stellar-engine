# Guardrails review rubric and test plan

Use this guide to evaluate Google Cloud services before enabling them inside a regulated landing zone and to prove that every preventative guardrail blocks non-compliant requests while permitting approved workload patterns.

Applying a consistent five-layer review model prevents gaps where an API allowlist, VPC Service Controls perimeter, encryption mandate, organization policy, or IAM Deny rule leaves an unintended exfiltration or privilege-escalation path open.

## 1. Five-layer service review rubric

Evaluate every candidate Google Cloud service across all five control layers and record each control decision before adding the service to workload allowlists.

| Layer | Control plane | Primary objective | Verification focus |
| :--- | :--- | :--- | :--- |
| 1 | Assured Workloads allowlist | Restrict workload API usage via `gcp.restrictServiceUsage` to services approved for the target compliance regime | Confirm the API appears on the Assured Workloads regime allowlist and assess ungoverned APIs separately |
| 2 | VPC Service Controls | Prevent data exfiltration across project and perimeter boundaries | Confirm restricted service coverage, dry-run perimeter telemetry, and ingress or egress rule scoping |
| 3 | Customer-Managed Encryption Keys and Cloud HSM | Require hardware-backed customer encryption keys at rest | Verify `gcp.restrictNonCmekServices`, `cloudkms.allowedProtectionLevels`, and `gcp.restrictCmekCryptoKeyProjects` |
| 4 | Organization Policy and custom CEL constraints | Block unsafe service configurations at resource `CREATE` and `UPDATE` time | Prefer managed constraints first, write fail-closed `ALLOW` or targeted `DENY` custom CEL rules for gaps |
| 5 | IAM Deny and least-privilege RBAC | Protect platform-owned resources and block dangerous API methods regardless of IAM allow grants | Attach tag-scoped IAM Deny policies for platform resources and bound workload service account roles |

### Layer 1 allowlist constraints

Enforce `gcp.restrictServiceUsage` at the workload container folder so projects inherit a vetted subset of the Assured Workloads folder allowlist.

- Confirm every value in a child `gcp.restrictServiceUsage` policy also exists in the parent Assured Workloads allowlist because Assured Workloads flags any extra value as an organization policy violation.
- Account for services that `gcp.restrictServiceUsage` does not govern, including `iam.googleapis.com`, `sts.googleapis.com`, `iamcredentials.googleapis.com`, `logging.googleapis.com`, `monitoring.googleapis.com`, `cloudresourcemanager.googleapis.com`, `serviceusage.googleapis.com`, `cloudasset.googleapis.com`, `servicenetworking.googleapis.com`, `essentialcontacts.googleapis.com`, `billingbudgets.googleapis.com`, `cloudbilling.googleapis.com`, and `cloudquotas.googleapis.com`.
- Enumerate child folders and projects before setting `inherit_from_parent: false` on a parent folder policy because any child without its own policy switches immediately from the grandparent Assured Workloads list to the narrowed parent list.

### Layer 2 perimeter controls

Add each reviewed service to the VPC Service Controls restricted services list in dry-run mode before enforcing it on the live perimeter.

- Inspect dry-run perimeter telemetry in Cloud Audit Logs with `protoPayload.metadata.dryRun=true` to identify legitimate cross-project calls before promotion.
- Verify service-specific perimeter behaviors during review, such as Pub/Sub push subscriptions inside a perimeter accepting only Cloud Run default URLs or Workflows targets and Cloud Tasks HTTP targets accepting only authenticated calls to perimeter-compliant Cloud Run endpoints.
- Omit bundled sub-APIs that VPC Service Controls already covers under a parent service, such as `bigqueryconnection.googleapis.com` under `bigquery.googleapis.com`.

### Layer 3 encryption controls

Pair `gcp.restrictNonCmekServices` with `cloudkms.allowedProtectionLevels` allowing `is:HSM` and `gcp.restrictCmekCryptoKeyProjects` restricting key origin projects.

- Prefix every `cloudkms.allowedProtectionLevels` value with `is:`, such as `is:HSM`, because the Organization Policy v2 API rejects bare protection-level names with `INVALID_ARGUMENT`.
- Supply `projects/<PROJECT_ID>` values rather than numeric project numbers in `gcp.restrictCmekCryptoKeyProjects` because policy writes accept project numbers without error while runtime CMEK enforcement matches project IDs and silently blocks creation.
- Verify regional key compatibility for each service because several managed services require single-region Cloud KMS keys rather than multi-region key rings.
- Grant `roles/cloudkms.cryptoKeyEncrypterDecrypter` to both the service-specific agent and the Compute Engine service agent when services such as Dataflow or Dataproc run worker VMs on CMEK-encrypted disks.

### Layer 4 organization policy and custom CEL

Adopt Google-managed constraints from the [opt-in guardrail packs](../fast/assets/org-policy-packs/README.md) before authoring custom constraints so you preserve the organization limit of 20 custom constraints per REST resource type.

- Use fail-closed `ALLOW` custom constraints when omitting an optional block defaults to an insecure setting, such as private GKE control-plane endpoints or Cloud Build worker pools without a network configuration.
- Split multi-field constraints when a service updates one configuration block per RPC, following the pattern of `custom.composerRequirePrivateIp` and `custom.composerRestrictWebServerAccess`.
- Verify every CEL field and helper function against the service's supported custom-constraint schema before rollout. Handle both short mode strings and REST enum names when they differ, as in `custom.artifactRegistryDisallowRemoteRepos`, and use `MemberTypeMatches` for `iam.googleapis.com/ServiceAccount` with legacy default service account suffixes on `iam.googleapis.com/AllowPolicy` rather than standard string operators so Google-managed service agents remain unaffected.

### Layer 5 IAM Deny and RBAC

Use IAM Deny policies for permissions that Organization Policy cannot govern, such as blocking non-platform principals from deleting platform-tagged log sinks, Pub/Sub topics, or Secret Manager secrets.

- Each attachment point supports up to 500 IAM Deny policies with up to 500 deny rules in total.
- Because the IAM v2 Policies API defaults to a low per-project request rate, request a quota increase before applying large batches of deny policies or limit Terraform concurrency with `-parallelism=1`.
- Exclude raw Workload Identity Federation `principalSet` tokens from deny exceptions when CI/CD pipelines impersonate dedicated automation service accounts.

## 2. Service onboarding and rollout workflow

Move every new guardrail through dry-run validation and explicit promotion so control changes never interrupt running workloads without evidence.

1. Confirm that no existing Terraform stage already manages the target constraint on the same organization or folder.
2. Deploy custom and managed constraints with the `dry_run:` prefix so Terraform writes only `dry_run_spec`.
3. Stage legacy constraints and IAM Deny policies that do not support dry-run mode as disabled until preflight inventories pass.
4. Execute both a block test case and an allow test case in a non-production workload project and archive the audit log entries.
5. Run Policy Simulator against non-production and production folders to identify pre-existing non-compliant resources.
6. Observe dry-run audit logs for at least two weeks covering at least one deployment cycle per active workload team.
7. Promote one guardrail per pull request so reviewers can validate blast radius and roll back cleanly if needed.

## 3. Preflight and dry-run log queries

Verify inheritance and inspect dry-run telemetry before promoting any constraint to live enforcement.

### Checking policy inheritance

Run `gcloud org-policies describe` without the `--effective` flag on child folders and projects; a not-found error confirms the resource inherits from its parent.

```bash
gcloud resource-manager folders list \
  --folder=987654321098 \
  --format='value(name,displayName)'

gcloud org-policies describe gcp.restrictServiceUsage \
  --folder=987654321098
```

Pass project IDs rather than numeric project numbers to `gcloud org-policies` and `gcloud logging read` commands because both commands reject project numbers.

### Reading dry-run audit logs

Organization Policy dry-run evaluations write `OrgPolicyDryRunAuditMetadata` entries to each project's `cloudaudit.googleapis.com/policy` log rather than the organization `_Default` bucket. Query a specific project directly or route policy logs from workload folders through an aggregated folder sink into a central log bucket or BigQuery dataset.

```bash
gcloud logging read \
  'protoPayload.metadata.dryRunResult="DENIED" AND protoPayload.metadata.liveResult="ALLOWED" AND protoPayload.metadata.constraint:"custom.dnsDisallowPublicZones"' \
  --project=acme-dev-workload \
  --freshness=14d \
  --limit=50 \
  --format='table(timestamp,protoPayload.metadata.constraint,protoPayload.metadata.checkedValue,protoPayload.methodName,protoPayload.authenticationInfo.principalEmail)'
```

For VPC Service Controls dry-run checks, filter the project `policy` log on the dry-run metadata field and service name.

```bash
gcloud logging read \
  'protoPayload.metadata.dryRun=true AND protoPayload.serviceName="cloudtasks.googleapis.com"' \
  --project=acme-dev-workload \
  --freshness=1d \
  --limit=50 \
  --format='table(timestamp,protoPayload.methodName,protoPayload.authenticationInfo.principalEmail)'
```

### Checking legacy guardrail prerequisites

Run resource inventories before enabling legacy constraints or IAM Deny policies that lack a dry-run mode.

```bash
# Verify Cloud Build runs use private worker pools before enforcing cloudbuild.allowedWorkerPools.
for REGION in us-east4 global; do
  gcloud builds list \
    --project=acme-dev-workload \
    --region="$REGION" \
    --filter='createTime>-P30D' \
    --limit=200 \
    --format='table(id,createTime,options.pool.name)'
done

# Inventory CMEK key projects before enforcing gcp.restrictCmekCryptoKeyProjects.
gcloud asset search-all-resources \
  --scope=folders/987654321098 \
  --query='kmsKeys:*' \
  --limit=500 \
  --format='table(name,kmsKeys)'

# Inventory custom Workload Identity Federation OIDC issuers, skipping GKE *.svc.id.goog pools.
gcloud iam workload-identity-pools list \
  --location=global \
  --project=acme-dev-workload \
  --format='value(name)'
```

## 4. Block and allow verification matrix

Run every block and allow pair in a non-production workload project (`acme-dev-workload`) using a non-exempt workload identity rather than a platform administrator account. Supply an approved Cloud HSM key (`KMS_KEY`) whenever CMEK is enforced so the request reaches the guardrail under test. Delete every test resource after recording the audit evidence.

While a constraint runs in dry-run mode, both commands succeed: the block case writes one `dryRunResult="DENIED"` entry in `cloudaudit.googleapis.com/policy`, and the allow case writes zero denied entries. Once enforced, the block case fails immediately and the allow case succeeds.

| Guardrail | Block test case | Allow test case |
| :--- | :--- | :--- |
| `custom.dnsDisallowPublicZones` | `gcloud dns managed-zones create test-public --dns-name=test.example.com. --description="guardrail test" --visibility=public --project=acme-dev-workload` | Same command with `--visibility=private --networks=acme-dev-vpc` |
| `custom.artifactRegistryDisallowRemoteRepos` | `gcloud artifacts repositories create test-remote --repository-format=docker --location=us-east4 --mode=remote-repository --remote-docker-repo=docker-hub --kms-key="$KMS_KEY" --project=acme-dev-workload` | Same command with `--mode=standard-repository` and without `--remote-docker-repo` |
| `custom.pubsubDisallowPushSubscriptions` | `gcloud pubsub subscriptions create test-push --topic=test-topic --push-endpoint=https://app.example.com/hook --push-auth-service-account=sa-push@acme-dev-workload.iam.gserviceaccount.com --project=acme-dev-workload` | Same command without `--push-endpoint` and `--push-auth-service-account` |
| `custom.cloudBuildWorkerPoolNoPublicEgress` | `gcloud builds worker-pools create test-egress --region=us-east4 --peered-network=projects/acme-net-host/global/networks/acme-dev-vpc --project=acme-dev-workload` | Same command with `--no-public-egress` |
| `custom.dataprocRequireInternalIp` | Create a Dataproc cluster without `--no-address` so `internalIpOnly` is false or omitted | Create the same Dataproc cluster with `--no-address` so `internalIpOnly` is true |
| `custom.gkeRequirePrivateControlPlane` | Provision a GKE cluster with `privateClusterConfig.enablePrivateEndpoint: false` or external DNS traffic enabled | Provision the same cluster with `enablePrivateEndpoint: true` and `allowExternalTraffic: false` |
| `custom.composerRequirePrivateIp` | Create a Cloud Composer environment without Private IP networking | Create a Cloud Composer environment with `enablePrivateEnvironment: true` or `networkingType: PRIVATE` |
| `custom.composerRestrictWebServerAccess` | Create a Cloud Composer environment omitting `webServerNetworkAccessControl` or allowing `0.0.0.0/0` | Create the environment with only internal RFC 1918 or approved management CIDRs such as `192.0.2.0/24` |
| `custom.bigqueryDisallowExternalDatasets` | Create a BigQuery dataset referencing `externalDatasetReference` or `externalCatalogDatasetOptions` | Create a native BigQuery dataset in an approved region |
| `custom.preventServiceAccountPrivilegeEscalation` | Bind `roles/editor` to `serviceAccount:sa-app@acme-dev-workload.iam.gserviceaccount.com` or a legacy default service account on `acme-dev-workload` | Bind a least-privilege role such as `roles/storage.objectViewer` to the same service account, or bind a required role to a Google-managed service agent |
| `gcp.restrictServiceUsage` | Call an enabled API excluded from the workload allowlist | Call an allowed API such as `gcloud pubsub topics list --project=acme-dev-workload --limit=5` |
| `cloudkms.allowedProtectionLevels` | Create a `SOFTWARE` protection-level CryptoKey in `acme-dev-workload` while `is:HSM` is enforced | Create an `HSM` protection-level CryptoKey in `acme-dev-workload` |

## 5. Policy Simulator and Policy Troubleshooter

Dry-run logs evaluate only new write requests. Pair Policy Simulator and Policy Troubleshooter with live test cases to audit pre-existing resources and IAM Deny interactions without mutating infrastructure.

### Simulating organization policy changes

Policy Simulator for Organization Policy evaluates existing resources against custom and managed constraints. Legacy constraints are not supported by Policy Simulator.

Write a proposed policy file such as `proposed_policy.yaml`:

```yaml
name: folders/987654321098/policies/custom.dnsDisallowPublicZones
spec:
  rules:
    - enforce: true
```

Run the simulation against your organization and pass `--custom-constraints` when testing a constraint definition that does not yet exist in the organization.

```bash
gcloud policy-intelligence simulate orgpolicy \
  --organization=123456789012 \
  --policies=proposed_policy.yaml
```

Run Policy Simulator on non-production folders first, remediate or document exceptions for any non-compliant existing assets, then repeat on production folders prior to promotion.

### Troubleshooting IAM Allow and Deny policies

Policy Troubleshooter evaluates effective IAM Allow and IAM Deny bindings together without creating or deleting resources. Test both a denied workload identity and an exempted platform identity before enabling any deny policy.

```bash
# Block case: non-exempt workload identity on a platform-tagged resource.
gcloud policy-intelligence troubleshoot-policy iam \
  //pubsub.googleapis.com/projects/acme-platform-logging/topics/audit-events \
  --principal-email=sa-app@acme-dev-workload.iam.gserviceaccount.com \
  --permission=pubsub.googleapis.com/topics.delete

# Allow case: exempted platform automation service account.
gcloud policy-intelligence troubleshoot-policy iam \
  //pubsub.googleapis.com/projects/acme-platform-logging/topics/audit-events \
  --principal-email=sa-platform-ops@acme-platform-iac.iam.gserviceaccount.com \
  --permission=pubsub.googleapis.com/topics.delete
```

## 6. Related documentation

- Review the [opt-in organization policy guardrail packs](../fast/assets/org-policy-packs/README.md) for reusable managed and custom constraint YAML baselines.
- Follow the [Assured Workloads Day-2 operations guide](./assured-workloads-operations.md) for violation triage, regional updates API checks, and Exception to Policy procedures.
- Record formal guardrail exceptions and architectural trade-offs using the [Architecture Decision Record template](./adr/template.md).
