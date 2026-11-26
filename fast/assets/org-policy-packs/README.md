# Opt-in organization policy guardrail packs

These curated YAML packs provide production-tested Google Cloud organization policy and custom constraint baselines that you can adopt incrementally without modifying default Stage 0 Terraform state or consuming organization custom constraint capacity until needed.

Keeping opt-in packs under `fast/assets/org-policy-packs/` rather than `fast/stages-aw/0-bootstrap/data/org-policies/` prevents unexpected drift on existing deployments and lets each platform team trial controls in dry-run mode before live enforcement.

## 1. Available packs

Select individual packs or individual YAML files based on the services enabled in your compliance boundary.

| Pack | Path | Contents | Default mode |
| :--- | :--- | :--- | :--- |
| GKE managed guardrails | [gke-managed/gke_managed_policy.yaml](./gke-managed/gke_managed_policy.yaml) | Twelve `container.managed.*` policies covering node service accounts, private nodes, Workload Identity Federation, Binary Authorization, Secrets encryption, kubelet read-only port, network policy, Cloud Logging, security bulletins, control-plane egress mode `NONE`, the `DenyServiceExternalIPs` admission controller blocking `spec.externalIPs`, and system RBAC bindings | Enforced, supports `dry_run:` prefix |
| Compute, Dataflow, and KMS guardrails | [compute-data-managed/managed_policy.yaml](./compute-data-managed/managed_policy.yaml) | Four managed constraints for FIPS machine types in Preview, container startup agent removal in Preview, private Dataflow workers, and IP forwarding, plus `cloudkms.allowedProtectionLevels` allowing `is:HSM` | Enforced, managed rules support `dry_run:` prefix |
| Custom CEL constraints and dry-run bindings | [custom-constraints-dry-run/constraints/](./custom-constraints-dry-run/constraints/) and [custom-constraints-dry-run/policies/custom_constraints_dry_run_policy.yaml](./custom-constraints-dry-run/policies/custom_constraints_dry_run_policy.yaml) | Ten custom constraint definitions across Artifact Registry, BigQuery, Cloud Build, Cloud Composer, Cloud DNS, Dataproc, GKE, IAM, and Pub/Sub, paired with matching `dry_run:custom.*` bindings | Dry-run audit only |

## 2. Adopting packs in Terraform

Each YAML file conforms to the JSON schemas enforced by `modules/organization-se` and `modules/folder`. Every policy YAML file uses the `*_policy.yaml` filename suffix and avoids existing `fast/stages-aw/0-bootstrap/data/org-policies/` filenames so copying packs into Stage 0 does not overwrite baseline files or drop silently.

### Using Stage 0 bootstrap factories

In `fast/stages-aw/0-bootstrap/organization.tf`, the `factories_config.org_policy` path loads every `*.yaml` file in the directory you specify before merging `data/org-policies/*_policy.yaml` and `data/custom-org-policies/*_policy.yaml`, while `factories_config.org_policy_custom_constraints` reads from `data/custom-constraint-policies/`.

1. Copy the desired `*_policy.yaml` files from `gke-managed/` or `compute-data-managed/` into a dedicated factory directory and point `factories_config.org_policy` at that directory in your `terraform.tfvars` file, or copy those files directly into `fast/stages-aw/0-bootstrap/data/org-policies/`.
2. Confirm that no duplicate constraint key exists in `fast/stages-aw/0-bootstrap/data/org-policies/` because files in `data/org-policies/` override keys with the same name loaded from `factories_config.org_policy`.
3. Copy only the custom constraint definition files you plan to use from `custom-constraints-dry-run/constraints/` into `fast/stages-aw/0-bootstrap/data/custom-constraint-policies/` so you do not consume unused custom constraint slots.
4. Copy `custom-constraints-dry-run/policies/custom_constraints_dry_run_policy.yaml` into your active policy factory directory or `fast/stages-aw/0-bootstrap/data/org-policies/`, keeping only the `dry_run:custom.*` bindings that match the constraint definitions you installed.

```hcl
factories_config = {
  org_policy = "../../assets/org-policy-packs/gke-managed"
}
```

### Using standalone organization or folder modules

When you manage guardrails in a separate policy repository or attach workload packs at the folder layer, pass pack paths directly to `modules/organization-se` or `modules/folder`.

```hcl
module "organization_guardrails" {
  source          = "./modules/organization-se"
  organization_id = "organizations/123456789012"
  prefix          = ""
  factories_config = {
    org_policy_custom_constraints = "./fast/assets/org-policy-packs/custom-constraints-dry-run/constraints"
    org_policies                  = "./fast/assets/org-policy-packs/custom-constraints-dry-run/policies"
  }
}
```

Check how the `prefix` variable affects `custom.*` names before splitting constraint definitions and folder policy attachments across modules.

- `modules/organization-se` appends the alphanumeric characters of a non-empty `prefix` value to both `google_org_policy_custom_constraint` names and `google_org_policy_policy` names that start with `custom.`.
- `modules/folder` passes policy keys directly to `google_org_policy_policy` without appending a `prefix` suffix, so set `prefix = ""` on the organization module or include the exact suffixed constraint name in folder-level YAML files.
- Never manage the same constraint on the same organization or folder from two separate Terraform states because each `terraform apply` overwrites the other.

## 3. Dry-run and enforcement lifecycle

Dry-run mode populates the `dry_run_spec` block on `google_org_policy_policy`, logging violations to `cloudaudit.googleapis.com/policy` without blocking requests.

1. Prefix any supported constraint key with `dry_run:` in YAML to write a dry-run policy only.
2. You can supply both `constraint.name` and `dry_run:constraint.name` in the same factory directory to enforce a current baseline in `spec` while auditing a stricter proposal in `dry_run_spec`.
3. Run Policy Simulator before enforcement to discover existing non-compliant resources because dry-run audit logs record only new `CREATE` and `UPDATE` API calls.
4. Observe dry-run logs across at least two weeks and at least one deployment cycle per active workload team.
5. Promote one constraint per pull request by removing the `dry_run:` prefix so any regression isolates cleanly and rolls back in a single revert.

Verify dry-run eligibility before adding a `dry_run:` prefix because the Organization Policy API rejects unsupported constraints with an error.

- Custom constraints starting with `custom.` support dry-run mode.
- Managed constraints containing `.managed.` support dry-run mode.
- Among legacy constraints, only `gcp.restrictServiceUsage`, `gcp.restrictEndpointUsage`, `gcp.restrictTLSVersion`, and `gcp.restrictTLSCipherSuites` support dry-run mode.
- Legacy `cloudkms.allowedProtectionLevels` in `compute-data-managed/managed_policy.yaml` does not support dry-run mode; validate existing KMS key protection levels and rotation schedules before applying it.

## 4. Quotas and system limits

Plan custom constraint adoption against Google Cloud Organization Policy system limits, which cannot be increased through quota requests.

- Google Cloud enforces a system limit of 20 custom constraints per REST resource type across an organization.
- Individual organization policy documents are limited to 32 KB.
- Creating a custom constraint definition at the organization level does not enforce the rule until a policy binding attaches that constraint to an organization, folder, or project.
- Keep `custom.composerRequirePrivateIp` and `custom.composerRestrictWebServerAccess` as separate single-field constraints because Cloud Composer `UPDATE` RPCs modify one configuration block at a time and combining both checks in a single `ALLOW` rule deadlocks remediation on existing environments.
- Scope `custom.preventServiceAccountPrivilegeEscalation` to workload folders or projects rather than the organization root so platform bootstrap and CI/CD automation service accounts retain required administrative bindings. Its CEL rule uses `MemberTypeMatches` for `iam.googleapis.com/ServiceAccount` plus legacy default service account suffixes, which protects Google-managed service agents (`iam.googleapis.com/ServiceAgent`) from accidental denial.
- Validate `compute.managed.disableNonFIPSMachineTypes` and `compute.managed.disableVmsWithContainerStartupAgent` in dry-run mode before live enforcement because both constraints are in Google Cloud Preview.
- Exempt dedicated network firewall, NAT, or proxy appliance folders or VMs from `compute.managed.vmCanIpForward` before enforcing it at a parent folder.

## 5. Related guides

- Read the [Guardrails rubric and test plan](../../../docs/guardrails-rubric-and-test-plan.md) for the five-layer service review model, dry-run audit queries, Policy Simulator commands, and block and allow test cases.
- Read the [Assured Workloads Day-2 operations guide](../../../docs/assured-workloads-operations.md) for regional updates API reconciliation, child violation triage, and Exception to Policy governance.
- Review the [organization module documentation](../../../modules/organization-se/README.md) and [folder module documentation](../../../modules/folder/README.md) for complete factory variable specifications.
