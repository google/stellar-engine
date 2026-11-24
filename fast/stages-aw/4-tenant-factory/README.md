# Tenant factory stage

This stage provisions multi-project tenant environments from declarative YAML manifests and optional HCL definitions without coupling tenant onboarding to core resource management state.

## Contents

<!-- BEGIN TOC -->
- [1 Architecture and guardrails](#1-architecture-and-guardrails)
- [2 Shared VPC service grants](#2-shared-vpc-service-grants)
- [3 Curated stage outputs](#3-curated-stage-outputs)
- [4 Billing linkage modes](#4-billing-linkage-modes)
- [5 Lifecycle and safe offboarding](#5-lifecycle-and-safe-offboarding)
- [6 VPC Service Controls enrollment](#6-vpc-service-controls-enrollment)
- [7 Manifest validation](#7-manifest-validation)
- [Variables](#variables)
- [Outputs](#outputs)
<!-- END TOC -->

## 1 Architecture and guardrails

This stage layers a strict tenant translation surface over the vendored [project-factory](../../../modules/project-factory/README.md), [project](../../../modules/project/README.md), and [iam-service-account](../../../modules/iam-service-account/README.md) modules without modifying anything under `modules/`.

* Environment-separated folders place every tenant under its matching parent in `var.environment_folders` using `<environment>/<tenant>` keys so the same tenant slug can coexist across `dev`, `test`, and `prod` without flattening environments into one folder.
* Least-privilege IAM enforcement rejects high-privilege roles including `roles/owner`, `roles/editor`, `roles/resourcemanager.organizationAdmin`, `roles/iam.securityAdmin`, `roles/resourcemanager.projectIamAdmin`, `roles/resourcemanager.folderIamAdmin`, `roles/orgpolicy.policyAdmin`, `roles/resourcemanager.lienModifier`, `roles/resourcemanager.folderAdmin`, `roles/iam.organizationRoleAdmin`, `roles/compute.xpnAdmin`, and `roles/iam.serviceAccountKeyAdmin` across JSON Schema validation, `variables.tf` checks, and `terraform_data.tenant_validation` preconditions.
* Shared VPC host-project service agent bindings in `shared_vpc_service_agent_iam` restrict members to `$service_agents:<alias>` references and allow only `roles/composer.sharedVpcAgent`, `roles/compute.networkUser`, `roles/container.hostServiceAgentUser`, and `roles/vpcaccess.user`.
* Project defaults apply `default_service_account = "deprivilege"` and disable automatic `roles/editor` grants for the Google APIs service agent on every tenant project.
* Per-tenant `org_policies` overrides are blocked so `constraints/gcp.restrictServiceUsage` stays enforced once on the Assured Workloads or environment parent folder without `inherit_from_parent = false` drift.
* Multi-subnet Shared VPC attachments map every `<region>/<subnet>` entry in `shared_vpc_subnets` through `network_subnet_users` and `service_agent_subnet_iam`, removing the single-subnet limit in Stage 2.
* Controlling-project automation creates isolated per-tenant Terraform state buckets and `rw` or `ro` service accounts scoped strictly to each tenant bucket, never granting Organization Admin, `roles/storage.admin` on the core automation project, or decrypt access to central landing zone state KMS keys.

## 2 Shared VPC service grants

Setting `shared_vpc_service_grants` delegates host-project IAM grants to the preset table in `modules/project/sharedvpc-agent-iam.yaml`. Entries must match `$service_agents:<api>.googleapis.com`.

Review the host-project roles granted by `modules/project` before enabling presets for Google Kubernetes Engine or Datastream:

* `$service_agents:container.googleapis.com` grants the GKE service agent `roles/compute.networkUser`, `roles/container.hostServiceAgentUser`, and `roles/compute.securityAdmin` on the host project, plus `roles/compute.networkUser` to the Google APIs service agent.
* `$service_agents:datastream.googleapis.com` grants the Datastream service agent `roles/compute.networkAdmin` on the host project.

Prefer `shared_vpc_subnets` with explicit `shared_vpc_service_agent_iam` entries when you need to avoid host-project-wide `roles/compute.securityAdmin` or `roles/compute.networkAdmin` grants.

## 3 Curated stage outputs

Consume upstream landing zone outputs either by copying curated `.auto.tfvars.json` files (`0-bootstrap.auto.tfvars.json` and `1-resman.auto.tfvars.json`) into this directory or by setting `read_stage_outputs_from_gcs = true` with `automation.outputs_bucket` populated.

Stage 1 exports environment folder IDs under `folder_ids.envs`, which this stage normalizes to lowercase keys and merges automatically when `environment_folders` is empty (with explicit `environment_folders` entries taking precedence). Stage 0 exports `automation.kms_keys.gcs`, which this stage uses as the default CMEK key for per-tenant `tf-state` buckets in Assured Workloads controlling projects unless `automation.bucket_kms_key` is set on the tenant.

When `read_stage_outputs_from_gcs` is enabled, this stage reads only `tfvars/1-resman.auto.tfvars.json` from `automation.outputs_bucket` through `data.google_storage_bucket_object_content.resman_outputs` and never touches core Stage 0 through Stage 3 Terraform state buckets.

## 4 Billing linkage modes

Set `billing_linkage_mode` to select how projects attach to a Cloud Billing account:

* Use `managed` when this stage links `billing_account.id` directly during project creation. Terraform rejects a null `billing_account.id` at plan time in this mode.
* Use `external_gate` when an external financial or governance workflow attaches billing accounts out of band. Terraform passes `billing_account = null` to `modules/project` so unlinked projects plan and apply cleanly.

## 5 Lifecycle and safe offboarding

Set `lifecycle_state` on every tenant manifest to prevent accidental project deletion when editing or removing YAML files:

* **Active protection (`lifecycle_state = "active"`)**: Terraform enables folder `deletion_protection`, sets project `deletion_policy` to `PREVENT`, and attaches a Resource Manager deletion lien regardless of `var.force_destroy`.
* **Production state-only archival (`lifecycle_state = "archived"`, `force_destroy = false`)**: Terraform switches project `deletion_policy` to `ABANDON`, disables folder `deletion_protection`, and removes the project lien in place without deleting the GCP project. After applying that transition, detach the tenant folder from state with `terraform state rm 'module.project-factory.module.folder-2["<env>/<tenant>"].google_folder.folder[0]'` (or move or delete the abandoned child projects in GCP first) before removing the YAML manifest so Cloud Resource Manager does not attempt to delete a non-empty folder.
* **Sandbox full teardown (`lifecycle_state = "archived"`, `force_destroy = true`)**: Setting `var.force_destroy = true` switches archived project `deletion_policy` to `DELETE` and sets `force_destroy = true` on per-tenant automation `tf-state` buckets. Apply `lifecycle_state = "archived"` with `-var="force_destroy=true"` first, then remove the manifest or run `terraform destroy -var="force_destroy=true"` to delete child projects, versioned state buckets, and the empty tenant folder cleanly.

## 6 VPC Service Controls enrollment

Set `vpc_sc_perimeter` on any project to manage additive perimeter membership via `google_access_context_manager_service_perimeter_resource` or `google_access_context_manager_service_perimeter_dry_run_resource`.

Set `ignore_resource_changes = true` on `perimeters.default` in `module.vpc-sc` inside [3-security](../3-security/README.md) (`3-security/vpc-sc.tf`) before enabling additive enrollment here so Stage 3 ignores external changes to `status.0.resources` and `spec.0.resources`. In brownfield environments where Stage 3 previously managed `google_access_context_manager_service_perimeter.regular["default"]` inline, add a `moved` block to `google_access_context_manager_service_perimeter.additive["default"]` in Stage 3 and import existing perimeter resource memberships before switching ownership to Stage 4.

## 7 Manifest validation

Validate tenant YAML files under `data/tenants/` against [tenant.schema.json](./schemas/tenant.schema.json) in CI before running Terraform plans. See [example-tenant.yaml](./data/tenants/example-tenant.yaml) for a multi-project manifest using multi-subnet Shared VPC and CMEK bindings.
<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [prefix](variables.tf#L127) | Lowercase prefix up to 10 characters for tenant resources. | <code>string</code> | ✓ |  |
| [automation](variables.tf#L19) | Optional Stage 0 outputs bucket, KMS keys, and project ID. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>&#123;&#125;</code> |
| [billing_account](variables.tf#L32) | Optional billing account used when billing mode is managed. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>null</code> |
| [billing_linkage_mode](variables.tf#L47) | Billing attachment mode: managed or external_gate. | <code>string</code> |  | <code>&#34;managed&#34;</code> |
| [environment_folders](variables.tf#L68) | Map of environment keys to folders/<id> parent folder IDs. | <code>map&#40;string&#41;</code> |  | <code>&#123;&#125;</code> |
| [factories_config](variables.tf#L83) | Paths to YAML tenant manifests and optional templates. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>&#123;&#125;</code> |
| [folder_ids](variables.tf#L93) | Optional Stage 1 folder IDs mapping with envs fallback. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>&#123;&#125;</code> |
| [force_destroy](variables.tf#L113) | Allow DELETE on archived projects and state bucket destroy. | <code>bool</code> |  | <code>false</code> |
| [kms_keys](variables.tf#L120) | Map of CMEK aliases to Cloud KMS crypto key resource IDs. | <code>map&#40;string&#41;</code> |  | <code>&#123;&#125;</code> |
| [read_stage_outputs_from_gcs](variables.tf#L143) | Read curated Stage 1 JSON outputs from automation bucket. | <code>bool</code> |  | <code>false</code> |
| [shared_vpc_host_projects](variables.tf#L157) | Map of environment keys to Shared VPC host project IDs. | <code>map&#40;string&#41;</code> |  | <code>&#123;&#125;</code> |
| [storage_location](variables.tf#L164) | Default GCS location for per-tenant automation buckets. | <code>string</code> |  | <code>&#34;us-east4&#34;</code> |
| [tenants](variables.tf#L171) | Optional HCL tenant definitions merged with YAML manifests. | <code>map&#40;object&#40;&#123;&#8230;&#125;&#41;&#41;</code> |  | <code>&#123;&#125;</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [tenant_folders](outputs.tf#L19) | Map of environment/tenant keys to tenant folder IDs. |  |
| [tenant_project_numbers](outputs.tf#L24) | Map of project keys to created tenant project numbers. |  |
| [tenant_projects](outputs.tf#L31) | Map of project keys to created tenant project IDs. |  |
| [tenant_service_accounts](outputs.tf#L38) | Map of tenant automation and workload service accounts. |  |
| [tenant_state_buckets](outputs.tf#L52) | Map of tenant automation state bucket keys to names. |  |
<!-- END TFDOC -->
