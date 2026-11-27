# Tenant factory stage

This stage provisions multi-project tenant environments from declarative YAML manifests and optional HCL definitions without coupling tenant onboarding to core resource management state.

## Contents

<!-- BEGIN TOC -->
- [1 Architecture and guardrails](#1-architecture-and-guardrails)
- [2 Tenant IAM guardrails](#2-tenant-iam-guardrails)
- [3 Shared VPC isolation and service grants](#3-shared-vpc-isolation-and-service-grants)
- [4 Curated stage outputs](#4-curated-stage-outputs)
- [5 Billing linkage modes](#5-billing-linkage-modes)
- [6 Lifecycle and safe offboarding](#6-lifecycle-and-safe-offboarding)
- [7 VPC Service Controls enrollment](#7-vpc-service-controls-enrollment)
- [8 Project templates](#8-project-templates)
- [9 Stage runner permissions](#9-stage-runner-permissions)
- [10 Manifest validation](#10-manifest-validation)
- [Variables](#variables)
- [Outputs](#outputs)
<!-- END TOC -->

## 1 Architecture and guardrails

This stage layers a strict tenant translation surface over the vendored [project-factory](../../../modules/project-factory/README.md), [project](../../../modules/project/README.md), and [iam-service-account](../../../modules/iam-service-account/README.md) modules without modifying anything under `modules/`.

* Environment-separated folders place every tenant under its matching parent in `var.environment_folders` using `<environment>/<tenant>` keys so the same tenant slug can coexist across `dev`, `test`, and `prod` without flattening environments into one folder.
* Tenant IAM guardrails reject privilege escalation roles, service agent roles, and unapproved custom roles across JSON Schema validation, `variables.tf` checks, and `terraform_data.tenant_validation` preconditions, as described in [Tenant IAM guardrails](#2-tenant-iam-guardrails).
* Shared VPC attachments always use the host project that the stage maps to the tenant environment, grant `roles/compute.networkUser` only on listed subnets, and gate privileged service presets, as described in [Shared VPC isolation and service grants](#3-shared-vpc-isolation-and-service-grants).
* Project defaults apply `default_service_account = "deprivilege"` and disable automatic `roles/editor` grants for the Google APIs service agent on every tenant project.
* Per-tenant `org_policies` overrides are blocked so `constraints/gcp.restrictServiceUsage` stays enforced once on the Assured Workloads or environment parent folder without `inherit_from_parent = false` drift.
* Controlling-project automation creates isolated per-tenant Terraform state buckets and `rw` or `ro` service accounts scoped strictly to each tenant bucket, never granting Organization Admin, `roles/storage.admin` on the core automation project, or decrypt access to central landing zone state KMS keys.
* Malformed YAML aborts the plan: syntax errors stop `yamldecode`, and empty, comment-only, or non-mapping tenant manifests and project templates fail `tenant_validation` instead of silently removing a tenant or template attributes.

## 2 Tenant IAM guardrails

The JSON Schema, `variables.tf`, and `terraform_data.tenant_validation` apply the same role rules, and the Terraform layers trim whitespace and ignore case when they match denylisted and service agent roles. `variables.tf` reuses the role and pattern locals in `main.tf`, and `tests/test_tenant_factory_schema.py` checks that the schema matches them.

Tenant folder and project IAM inputs (`iam`, `iam_by_principals`, `iam_bindings_additive`) and `service_accounts.<name>.iam_self_roles` reject these roles:

* Ownership and hierarchy administration: `roles/owner`, `roles/editor`, `roles/resourcemanager.organizationAdmin`, `roles/resourcemanager.folderAdmin`, `roles/resourcemanager.folderIamAdmin`, `roles/resourcemanager.projectIamAdmin`, and `roles/resourcemanager.lienModifier`.
* IAM, service account, and Workload Identity administration: `roles/iam.securityAdmin`, `roles/iam.roleAdmin`, `roles/iam.organizationRoleAdmin`, `roles/iam.denyAdmin`, `roles/iam.serviceAccountAdmin`, `roles/iam.serviceAccountKeyAdmin`, `roles/iam.serviceAccountTokenCreator`, `roles/iam.serviceAccountUser`, `roles/iam.workloadIdentityUser`, and `roles/iam.workloadIdentityPoolAdmin`.
* Policy, tag, audit, service, and key administration: `roles/orgpolicy.policyAdmin`, `roles/resourcemanager.tagAdmin`, `roles/resourcemanager.tagUser`, `roles/logging.admin`, `roles/logging.configWriter`, `roles/serviceusage.serviceUsageAdmin`, and `roles/cloudkms.admin`.
* Network administration: `roles/compute.networkAdmin`, `roles/compute.securityAdmin`, `roles/compute.xpnAdmin`, and `roles/dns.admin`.

The remaining rules split by scope and role type:

* `service_accounts.<name>.iam` binds roles on that workload service account only. It allows `roles/iam.serviceAccountUser`, `roles/iam.serviceAccountTokenCreator`, and `roles/iam.workloadIdentityUser` so deployers can act as one runtime identity and Kubernetes service accounts can use Workload Identity, and it rejects every other denylisted role.
* `iam` and `iam_by_principals` are authoritative per role: listing a role replaces every member of that role on the folder or project. Roles whose name contains `serviceAgent` in any case are rejected in every IAM input, because authoritative grants would remove the service agent bindings that `modules/project` manages and service agent roles are meant only for Google-managed service agents. Use `iam_bindings_additive` for roles that other systems also grant.
* Custom role IDs (`organizations/<id>/roles/<name>` or `projects/<id>/roles/<name>`) plan only when listed in `allowed_custom_roles`. Stage 0 `$custom_roles:<key>` references resolve through `custom_roles` and also need an `allowed_custom_roles` entry, either the reference or its resolved ID, because Stage 0 exports administrative roles such as `organization_iam_admin` and `service_project_network_admin`.
* `allowed_privileged_roles` is a deliberate escape hatch that exempts specific denylisted or service agent roles for every tenant, so review each entry as a security exception. The JSON Schema cannot read stage variables and keeps the full denylist, so grant exempted roles through operator-owned HCL `tenants` entries rather than tenant-authored YAML.

## 3 Shared VPC isolation and service grants

The stage resolves each environment host project from `shared_vpc_host_projects`, then falls back to the Stage 2 `host_project_ids` output for environments without an explicit entry. The Stage 2 `hub` host project is never a fallback target.

* `shared_vpc_host_project` on a project is an assertion only. It must equal the resolved host project for the tenant environment, so a `dev` tenant cannot attach to a `prod` or hub host project.
* `shared_vpc_network_users` requires `shared_vpc_subnets`. The stage grants `roles/compute.networkUser` on each listed `<region>/<subnet>` and never on the whole host project.
* `shared_vpc_service_agent_iam` grants allowlisted roles (`roles/composer.sharedVpcAgent`, `roles/compute.networkUser`, `roles/container.hostServiceAgentUser`, and `roles/vpcaccess.user`) to `$service_agents:<alias>` members at the host project level, not per subnet.
* Set `shared_vpc_subnet_allowlist` to map each `<env>/<tenant>` key to the subnets that Stage 2 allocated to that tenant. Every `shared_vpc_subnets` entry must then appear in the tenant list, and tenants missing from the map cannot attach subnets. The default `null` value disables the check.

```hcl
shared_vpc_subnet_allowlist = {
  "dev/acme" = ["us-east4/dev-acme-app", "us-east4/dev-acme-data"]
}
```

`shared_vpc_service_grants` entries, set on a project or inherited from its template, must match `$service_agents:<api>.googleapis.com` and name a preset in [sharedvpc-agent-iam.yaml](../../../modules/project/sharedvpc-agent-iam.yaml). The stage resolves the host project roles of each preset and fails the plan when any role falls outside the agent role allowlist, unless the API is listed in `privileged_shared_vpc_service_grants`:

* `container.googleapis.com` (GKE) grants the GKE service agent `roles/compute.securityAdmin` to manage firewall rules, plus `roles/compute.networkUser` and `roles/container.hostServiceAgentUser`, and grants `roles/compute.networkUser` to the Google APIs service agent.
* `datastream.googleapis.com` (Datastream) grants the Datastream service agent `roles/compute.networkAdmin`.

These roles apply to the whole environment host project, so an opted-in tenant service agent can change firewall rules or network resources that other tenants on the same host project rely on. Opt in only for host projects whose tenants share that trust level.

## 4 Curated stage outputs

Consume upstream landing zone outputs either by copying curated `.auto.tfvars.json` files into this directory or by setting `read_stage_outputs_from_gcs = true` with `automation.outputs_bucket` populated.

* Stage 0 (`0-bootstrap.auto.tfvars.json`) exports `automation` (outputs bucket, project ID, and `kms_keys.gcs`) and `custom_roles`. Stage 0 sets `custom_roles` to `null` when it skips custom roles, which this stage treats as an empty map. This stage forwards `custom_roles` into the folder, project, and service account IAM contexts so allowlisted `$custom_roles:<key>` references resolve.
* Stage 1 (`1-resman.auto.tfvars.json`) exports environment folder IDs under `folder_ids.envs`, which this stage normalizes to lowercase keys and merges when `environment_folders` lacks an entry, with explicit `environment_folders` entries taking precedence.
* Stage 2 (`2-networking.auto.tfvars.json`) exports `host_project_ids` keyed by lowercase environment from both [2-networking-a-fedramp](../2-networking-a-fedramp/README.md) and [2-networking-b-il5-ngfw](../2-networking-b-il5-ngfw/README.md). This stage uses it as the per-environment fallback for `shared_vpc_host_projects`.

When `read_stage_outputs_from_gcs` is enabled, this stage reads only `tfvars/1-resman.auto.tfvars.json` from `automation.outputs_bucket` through `data.google_storage_bucket_object_content.resman_outputs` and never touches core Stage 0 through Stage 3 Terraform state buckets.

Per-tenant `tf-state` buckets fall back to the Stage 0 `automation.kms_keys.gcs` key only when the tenant `automation.project_id` equals the Stage 0 automation project, because Stage 0 grants `roles/cloudkms.cryptoKeyEncrypterDecrypter` on that key only to the Cloud Storage service agent of its own automation project. Any other automation project requires `automation.bucket_kms_key`, and the operator must grant that project's Cloud Storage service agent access to the key. Every tenant on the fallback shares the central Stage 0 GCS key, so rotating, disabling, or destroying that key affects all of them and any landing zone buckets that use it. Prefer a per-tenant key to rotate, revoke, or crypto-shred one tenant's state at offboarding.

Every `kms_services` reference and `automation.bucket_kms_key` must be a `kms_keys` alias or a full `projects/<project>/locations/<location>/keyRings/<ring>/cryptoKeys/<key>` ID, and `kms_services` keys must be `<api>.googleapis.com` names.

## 5 Billing linkage modes

Set `billing_linkage_mode` to select how projects attach to a Cloud Billing account:

* Use `managed` when this stage links `billing_account.id` directly during project creation. Terraform rejects a null `billing_account.id` at plan time in this mode.
* Use `external_gate` when an external financial or governance workflow attaches billing accounts out of band. Terraform passes `billing_account = null` to `modules/project` so unlinked projects plan and apply cleanly.

## 6 Lifecycle and safe offboarding

Set `lifecycle_state` on every tenant manifest to prevent accidental project deletion when editing or removing YAML files. Active tenants keep folder `deletion_protection`, project `deletion_policy = "PREVENT"`, a Resource Manager deletion lien, and `force_destroy = false` on their `tf-state` bucket regardless of `var.force_destroy`.

To archive a production tenant while keeping its projects and state in Google Cloud:

1. Set `lifecycle_state: archived` and apply with `force_destroy = false`. Terraform switches project `deletion_policy` to `ABANDON` and removes the project liens and folder deletion protection, while the tenant `tf-state` bucket keeps `force_destroy = false`.
2. Remove the tenant folder and the non-empty state bucket from Terraform state, using the `module.project-factory.module.folder-2["<env>/<tenant>"].google_folder.folder[0]` and `module.project-factory.module.automation-bucket["<env>/<tenant>/automation/tf-state"].google_storage_bucket.bucket[0]` addresses with `terraform state rm`. To keep the abandoned projects fully working, also remove each `module.tenant-projects["<env>/<tenant>/<project>"]` and `module.tenant-service-accounts["<env>/<tenant>/<project>/<sa>"]` instance, or the next apply revokes their IAM, CMEK grants, and Shared VPC attachments.
3. Delete the tenant manifest and apply. Terraform removes only the tenant objects left in state, such as folder IAM bindings, automation service accounts, and state bucket IAM.

To tear down a sandbox tenant completely:

1. Set `lifecycle_state: archived` and apply with `-var="force_destroy=true"`. Only archived tenants switch projects to `deletion_policy = "DELETE"` and arm `force_destroy` on their `tf-state` bucket.
2. Delete only that tenant manifest and run `terraform apply -var="force_destroy=true"`. Terraform deletes the tenant projects, versioned state bucket, and folder, and leaves every other tenant unchanged.

Never run `terraform destroy` to offboard one tenant. It plans the removal of every tenant in this stage, so it can delete active tenants' IAM bindings, service accounts, Shared VPC attachments, and empty state buckets before it fails on projects protected by `PREVENT`.

## 7 VPC Service Controls enrollment

Set `vpc_sc_perimeter` on any project to manage additive perimeter membership via `google_access_context_manager_service_perimeter_resource` or `google_access_context_manager_service_perimeter_dry_run_resource`.

Set `ignore_resource_changes = true` on `perimeters.default` in `module.vpc-sc` inside [3-security](../3-security/README.md) (`3-security/vpc-sc.tf`) before enabling additive enrollment here so Stage 3 ignores external changes to `status.0.resources` and `spec.0.resources`. In brownfield environments where Stage 3 previously managed `google_access_context_manager_service_perimeter.regular["default"]` inline, add a `moved` block to `google_access_context_manager_service_perimeter.additive["default"]` in Stage 3 and import existing perimeter resource memberships before switching ownership to Stage 4.

## 8 Project templates

Set `factories_config.project_templates_path` to a directory of `**/*.yaml` templates and reference each template from a project by its relative path without the `.yaml` suffix. A template may set only the keys below, and any other key fails the plan:

| key | merge behavior |
|---|---|
| `contacts` | Merged as a map, with tenant and then project entries taking precedence. |
| `kms_services` | Merged per API, with project lists replacing template lists for the same API. |
| `labels` | Merged as a map, with tenant and then project labels taking precedence and the stage `environment`, `lifecycle_state`, and `tenant` labels always applied. |
| `metric_scopes` | Combined with project entries. |
| `services` | Combined with project entries. |
| `shared_vpc_service_grants` | Combined with project entries. Inherited grants attach the project to the environment host project and pass the same preset checks. |

Templates never carry IAM, subnets, or network users, so every IAM and network grant stays in the tenant manifest where the guardrails apply.

## 9 Stage runner permissions

The tenant guardrails restrict what manifests grant, not the identity that runs this stage. Grant the Stage 4 service account these permissions, preferring IAM conditions that limit delegated grants where noted:

| scope | purpose | example roles |
|---|---|---|
| Each `environment_folders` parent | Tenant folders, projects, project IAM, liens, services, workload service accounts, and essential contacts | `roles/resourcemanager.folderAdmin`, `roles/resourcemanager.projectCreator`, and `roles/owner` or the narrower `roles/resourcemanager.projectIamAdmin`, `roles/serviceusage.serviceUsageAdmin`, `roles/iam.serviceAccountAdmin`, `roles/resourcemanager.lienModifier`, and `roles/essentialcontacts.admin` set, plus `roles/resourcemanager.projectDeleter` only for sandbox teardown |
| Billing account | Project billing links in `managed` mode | `roles/billing.user` |
| Shared VPC host projects and their parent folder or organization | Service project attachment plus host project and subnet IAM | `roles/compute.xpnAdmin`, the Stage 0 `service_project_network_admin` custom role, and `roles/resourcemanager.projectIamAdmin` conditioned on the agent role allowlist plus any opted-in preset roles |
| Tenant automation projects | Automation service accounts, state buckets, and `roles/serviceusage.serviceUsageConsumer` grants | `roles/iam.serviceAccountAdmin`, `roles/storage.admin`, and `roles/resourcemanager.projectIamAdmin` conditioned on `roles/serviceusage.serviceUsageConsumer` |
| Referenced Cloud KMS keys | Service agent CMEK grants | `roles/cloudkms.admin` on tenant key rings, or a custom role with `cloudkms.cryptoKeys.getIamPolicy` and `cloudkms.cryptoKeys.setIamPolicy` |
| VPC Service Controls access policy | Additive perimeter membership | `roles/accesscontextmanager.policyEditor` |
| Tag values | Folder and project tag bindings | `roles/resourcemanager.tagUser` |
| Stage 0 outputs bucket | `read_stage_outputs_from_gcs` reads | `roles/storage.objectViewer` |

## 10 Manifest validation

Copy [example-tenant.yaml.sample](./data/tenants/example-tenant.yaml.sample) to `data/tenants/<tenant>.yaml` to onboard a tenant. The stage loads only `*.yaml` files under `tenants_data_path`, so the sample never deploys, and the Terraform tests read manifests from `tests/fixtures/` instead.

Validate tenant YAML files against [tenant.schema.json](./schemas/tenant.schema.json) in CI before running Terraform plans. The schema enforces the static rules of each manifest, while cross-manifest checks such as unique computed project IDs, template checks, and rules that depend on stage variables run only at plan time: host project matching, `shared_vpc_subnet_allowlist`, `kms_keys` alias resolution, `allowed_custom_roles`, `allowed_privileged_roles`, Shared VPC preset resolution, and the automation bucket KMS requirement.
<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [prefix](variables.tf#L199) | Lowercase prefix up to 10 characters for tenant resources. | <code>string</code> | ✓ |  |
| [allowed_custom_roles](variables.tf#L23) | Custom role IDs or $custom_roles refs tenant IAM may grant. | <code>list&#40;string&#41;</code> |  | <code>&#91;&#93;</code> |
| [allowed_privileged_roles](variables.tf#L39) | Denylisted or service agent roles deliberately exempted. | <code>list&#40;string&#41;</code> |  | <code>&#91;&#93;</code> |
| [automation](variables.tf#L54) | Optional Stage 0 outputs bucket, KMS keys, and project ID. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>&#123;&#125;</code> |
| [billing_account](variables.tf#L67) | Optional billing account used when billing mode is managed. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>null</code> |
| [billing_linkage_mode](variables.tf#L82) | Billing attachment mode: managed or external_gate. | <code>string</code> |  | <code>&#34;managed&#34;</code> |
| [custom_roles](variables.tf#L103) | Optional Stage 0 custom role IDs keyed by role name. | <code>map&#40;string&#41;</code> |  | <code>&#123;&#125;</code> |
| [environment_folders](variables.tf#L119) | Map of environment keys to folders/<id> parent folder IDs. | <code>map&#40;string&#41;</code> |  | <code>&#123;&#125;</code> |
| [factories_config](variables.tf#L134) | Paths to YAML tenant manifests and optional templates. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>&#123;&#125;</code> |
| [folder_ids](variables.tf#L144) | Optional Stage 1 folder IDs mapping with envs fallback. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>&#123;&#125;</code> |
| [force_destroy](variables.tf#L164) | Allow DELETE and state bucket destroy for archived tenants. | <code>bool</code> |  | <code>false</code> |
| [host_project_ids](variables.tf#L171) | Optional Stage 2 host project IDs keyed by environment. | <code>map&#40;string&#41;</code> |  | <code>&#123;&#125;</code> |
| [kms_keys](variables.tf#L186) | Map of CMEK aliases to Cloud KMS crypto key resource IDs. | <code>map&#40;string&#41;</code> |  | <code>&#123;&#125;</code> |
| [privileged_shared_vpc_service_grants](variables.tf#L215) | APIs allowed to use privileged Shared VPC service presets. | <code>list&#40;string&#41;</code> |  | <code>&#91;&#93;</code> |
| [read_stage_outputs_from_gcs](variables.tf#L229) | Read curated Stage 1 JSON outputs from automation bucket. | <code>bool</code> |  | <code>false</code> |
| [shared_vpc_host_projects](variables.tf#L243) | Map of environment keys to Shared VPC host project IDs. | <code>map&#40;string&#41;</code> |  | <code>&#123;&#125;</code> |
| [shared_vpc_subnet_allowlist](variables.tf#L258) | Optional <env>/<tenant> map of allocated Shared VPC subnets. | <code>map&#40;list&#40;string&#41;&#41;</code> |  | <code>null</code> |
| [storage_location](variables.tf#L275) | Default GCS location for per-tenant automation buckets. | <code>string</code> |  | <code>&#34;us-east4&#34;</code> |
| [tenants](variables.tf#L282) | Optional HCL tenant definitions merged with YAML manifests. | <code>map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> |  | <code>&#123;&#125;</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [tenant_folders](outputs.tf#L19) | Map of environment/tenant keys to tenant folder IDs. |  |
| [tenant_project_numbers](outputs.tf#L24) | Map of project keys to created tenant project numbers. |  |
| [tenant_projects](outputs.tf#L31) | Map of project keys to created tenant project IDs. |  |
| [tenant_service_accounts](outputs.tf#L38) | Map of tenant automation and workload service accounts. |  |
| [tenant_state_buckets](outputs.tf#L52) | Map of tenant automation state bucket keys to names. |  |
<!-- END TFDOC -->
