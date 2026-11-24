# Upgrade to v7.0.0

Use this guide to deploy Stellar Engine v7.0.0 from scratch or upgrade an existing v6.0.0 deployment while preserving stateful Google Cloud resources. Review [CHANGELOG.md](CHANGELOG.md) and release pull request [#415](https://github.com/google/stellar-engine/pull/415) alongside these steps before running Terraform.

<!-- BEGIN TOC -->
- [1 Deploy from scratch](#1-deploy-from-scratch)
  - [1.1 Required tooling](#11-required-tooling)
  - [1.2 Deployment workflow changes](#12-deployment-workflow-changes)
  - [1.3 Retired classroom workarounds](#13-retired-classroom-workarounds)
  - [1.4 Known open issues](#14-known-open-issues)
- [2 Upgrade from v6.0.0](#2-upgrade-from-v600)
  - [2.1 AI-assisted upgrade workflow](#21-ai-assisted-upgrade-workflow)
  - [2.2 Manual state migrations](#22-manual-state-migrations)
  - [2.3 Outages and maintenance windows](#23-outages-and-maintenance-windows)
  - [2.4 Multi-pass Terraform applies](#24-multi-pass-terraform-applies)
<!-- END TOC -->

## 1 Deploy from scratch

Follow the [Detailed Deployment Guide](docs/ddg.md) and [Prerequisites](docs/prerequisites.md) while applying the tooling requirements, workflow changes, retired workarounds, and open issue mitigations below. Operators trained on v5.x or v6.0.0 classroom deployments should check each stage delta before running `terraform apply`.

### 1.1 Required tooling

Verify that your workstation provides the tools and local provider binaries listed in [docs/prerequisites.md](docs/prerequisites.md) and [default-versions.tf](default-versions.tf) before starting Stage 0.

- A POSIX shell on Linux, macOS, Google Cloud Shell, or a native WSL2 Linux filesystem
- `git`
- Google Cloud SDK and `gcloud` CLI
- `terraform` matching the constraints in [default-versions.tf](default-versions.tf) and per-directory `versions.tf` or `provider.tf` files
- `jq`
- Air-gapped provider mirrors containing `hashicorp/google`, `hashicorp/google-beta`, `hashicorp/time`, `hashicorp/tls`, `hashicorp/random`, `hashicorp/null`, `hashicorp/local`, `hashicorp/external`, and `hashicorp/archive`

### 1.2 Deployment workflow changes

Review these updates to [docs/ddg.md](docs/ddg.md) across Stages 0 through 3, networking topologies, and default blueprint permissions before deploying.

- Run `./fast/stages-aw/0-bootstrap/enableServices.sh`, `gcloud services enable monitoring.googleapis.com`, and `./fast/stages-aw/0-bootstrap/setIAM.sh <user_email> <organization_id>` from the repository root before Stage 0; review `setIAM.yaml.sample` before production use because it includes `roles/resourcemanager.projectDeleter`, grant `roles/billing.admin` directly on external billing accounts, and verify `gcp-vpc-network-admins@example.com` exists rather than Google Cloud Setup's `gcp-network-admins@example.com` default or override `var.groups`.
- Setting `deploy_org_resources = { org_policies = false }` in `fast/stages-aw/0-bootstrap` now attaches baseline Stage 0 policies to the Assured Workloads enclave folder via `module.root-folder-config[0]`, and `custom.restrictFirewallRanges` blocks classic VPC ingress allow rules containing `0.0.0.0/0` alongside narrower CIDRs or `::/0`.
- Stage 1 resolves per-tenant KMS and Cloud Storage regions from `tenants[*].locations` instead of `var.regions.primary`, consolidates tenant folder IAM into `module.tenant-top-folders-iam`, and outputs `team_cicd_repositories[*].service_account` as an `{ apply, plan }` map.
- Operators returning from v5.x training should note that [fast/stages-aw/2-networking-a-fedramp](fast/stages-aw/2-networking-a-fedramp/README.md) now deploys `<prefix>-net-hub-host`, a `STAR` Network Connectivity Center hub, `BEFORE_CLASSIC_FIREWALL` Cloud NGFW policies under `var.firewall_policy_rules`, PSC Google APIs endpoints, Cloud NAT or `var.centralized_egress` Secure Web Proxy, object-typed `secondary_ip_ranges`, and opt-in `var.psa_ranges`; on FedRAMP Moderate, FedRAMP High, and IL2 it leaves `enable-oslogin` metadata to `compute.requireOsLogin`.
- [fast/stages-aw/2-networking-b-il5-ngfw](fast/stages-aw/2-networking-b-il5-ngfw/README.md) emits lowercase `{ <env> = "<project-id>" }` strings in `output.host_project_ids`, skips `default-peering` PSA creation when `var.psa_ranges` covers an environment, writes NGFW return routes for all spoke primary, secondary, and proxy-only CIDRs, and enforces Suite-B-GCM-256 default IPsec profiles.
- Stage 3 `sa_lockdown.sh` and fail-closed `validation.sh`, which accepts the `--prefix` and `--project` flags, cover all 27 static `VALID_NAMES` accounts including `<prefix>-prod-resman-envs-0` plus `team-<name>` accounts, while `vpc_sc.perimeter_default.dry_run_spec` trials perimeter edits without dropping active enforcement.
- `cloud-run`, `cnap`, `pub-sub-project`, `vertex-mlops`, `cloud-workstations`, `cloud-functions`, and `cloud-composer-environment` bind IAM roles to individual resources rather than entire projects; populate `var.subscriptions` in `pub-sub-project` to grant subscriber access and `var.image_repository` in `cloud-workstations` when pulling private images.
- `postgresql` drops its untargeted host-project firewall rule and adds opt-in `var.psc_config` Private Service Connect; `cnap` via `var.cloud_armor_request_body_limit` plus `cloud-armor` in `rules.yaml` block HTTP bodies over 8 KB; `gemini-enterprise` adds the same 8 KB limit at priority 90 in preview mode until a rule in `cloudarmor.yaml` disables `preview`; `il5/gke` and `fedramp-high/gke` enforce `access_config.private_nodes = true`; `fedramp-high/gitlab` runs GKE nodes on a dedicated node account; `beyondcorp` requires encrypted Endpoint Verification devices; and `cloud-spanner` plus `cloud-composer-environment` add optional `var.kms_key_name` CMEK inputs.

### 1.3 Retired classroom workarounds

Stop applying the legacy v5.x and v6.0.0 workarounds below because v7.0.0 resolves each defect directly in code.

| Component | Workaround no longer needed |
| --- | --- |
| `0-bootstrap`, `docs/ddg.md` | Attaching enclave folder policies manually when `org_policies` is `false`, or correcting `./setIam.sh` casing |
| `1-resman` | Re-applying Stage 1 to repair overwritten tenant folder IAM bindings |
| `2-networking-a-fedramp` | Importing `enable-oslogin` metadata after duplicate-key errors, or fixing overlapping `psa_ranges` sample CIDRs |
| `2-networking-b-il5-ngfw` | Adding static PAN-OS return routes for secondary or proxy-only subnets, or resolving duplicate PSA peerings on new deployments |
| `3-security` | Manually disabling `-0r` plan, Stage 3 branch, `prod-resman-envs-0`, or `team-<name>` SAs after `sa_lockdown.sh`, or setting `dry_run = true` to trial VPC-SC edits |
| `cloud-spanner`, `dataflow`, `gitlab`, `postgresql`, `pub-sub-project` | Running `terraform apply` twice, pre-creating service agents, or targeting publisher and subscriber SAs before CMEK grants |
| `fedramp-high/gitlab`, `dataflow` | Passing a bare region to `gitlab` `var.zone`, overriding region-valued `dataflow` `var.zone`, or clearing `network` on Shared VPC jobs |
| `gke`, `gke-hardened`, `dataflow`, `kms-project` | Shortening cluster or project names under 30 characters, or applying `var.existing_kms_keys[*].iam_members` out of band |

### 1.4 Known open issues

Apply the active workarounds below when open GitHub issues affect fresh v7.0.0 deployments or Day-2 operations.

> [!WARNING]
> Stage 2b in [fast/stages-aw/2-networking-b-il5-ngfw](fast/stages-aw/2-networking-b-il5-ngfw/README.md) currently fails every `terraform plan` run due to [#512](https://github.com/google/stellar-engine/issues/512) and [#513](https://github.com/google/stellar-engine/issues/513) until you update `bastion.tf` and `variables.tf` locally.

Before planning `fast/stages-aw/2-networking-b-il5-ngfw`, replace `data` and `data_config` on both `ngfw-ssh-private-key` and `ngfw-ssh-public-key` in `bastion.tf` and change `secondary_ip_ranges` on line 324 of `variables.tf` to an object map:

```hcl
# fast/stages-aw/2-networking-b-il5-ngfw/bastion.tf
ngfw-ssh-private-key = {
  # Keep existing global_replica_locations and iam blocks.
  versions = {
    latest = {
      enabled = true
      data = {
        value      = tls_private_key.ngfw_ssh.private_key_openssh
        wo_version = 1
      }
    }
  }
}

ngfw-ssh-public-key = {
  # Keep existing global_replica_locations and iam blocks.
  versions = {
    latest = {
      enabled = true
      data = {
        value      = tls_private_key.ngfw_ssh.public_key_openssh
        wo_version = 1
      }
    }
  }
}

# fast/stages-aw/2-networking-b-il5-ngfw/variables.tf line 324
secondary_ip_ranges = optional(map(object({
  ip_cidr_range           = optional(string)
  reserved_internal_range = optional(string)
})))
```

| Issue | Component | Symptom and workaround |
| --- | --- | --- |
| [#515](https://github.com/google/stellar-engine/issues/515), [#516](https://github.com/google/stellar-engine/issues/516) | `0-bootstrap`, `docs/ddg.md` | Commented `kms_protection_level` fails with the `-input=false` flag and DDG blocks contain inner backticks; copy `terraform.tfvars.sample`, set `kms_protection_level` explicitly to `null`, `"SOFTWARE"`, or `"HSM"`, and omit it from `1-resman` |
| [#519](https://github.com/google/stellar-engine/issues/519) | `0-bootstrap` | `import.sh` fails on macOS `mapfile` and generates org-level imports when `org_policies` is `false`; pass an explicit org ID like `./import.sh 123456789012`, and skip `import.sh` when `org_policies` is `false` |
| [#522](https://github.com/google/stellar-engine/issues/522), [#525](https://github.com/google/stellar-engine/issues/525) | `docs/ddg.md`, `docs/prerequisites.md`, `0-bootstrap`, `1-resman` | Quota of 13 understates `10 + 6 * <tenants>`, `enableServices.sh` omits `monitoring.googleapis.com`, `docs/prerequisites.md` lists 3 invalid groups, and `prefix` length limits vary; request at least 16 projects for 1 tenant or 22 for 2 tenants plus workloads, enable monitoring, keep `prefix` to 7 characters or fewer, and set `is_org_level = false` for external billing |
| [#518](https://github.com/google/stellar-engine/issues/518), [#523](https://github.com/google/stellar-engine/issues/523) | `1-resman`, `2-networking-*` | Custom tenant keys crash Stage 2 `one(...)` subnet lookups and `envs_folders[*].admin` is unread; keep tenant keys to 6 characters or fewer, map one subnet with `tenant = "<tenant>"` per environment in `var.subnets`, and grant folder IAM via `var.folder_iam.envs` |
| [#524](https://github.com/google/stellar-engine/issues/524), [#442](https://github.com/google/stellar-engine/issues/442) | `2-networking-*`, `scripts/` | Stage 2b `var.psa_ranges` drops `int` and `test`, `ngfw.tf` hardcodes `HSM` on `vdss-keyring`, `scripts/restore.sh` crashes on `promptUser`, and folder firewall policies ignore `var.firewall_policy_rules`; add optional `int` and `test` attributes to `var.psa_ranges` in `2-networking-b-il5-ngfw/variables.tf` or update `branch-net-envs.tf` and `psc.tf` to `try(var.psa_ranges[lower(...)], var.psa_ranges["dev"], [])` alongside `map(list(object(...)))`, update `ngfw.tf` line 405 to `coalesce(var.kms_protection_level, "HSM")`, place folder rules in `data/hierarchical-ingress-rules.yaml` and `data/cidrs.yaml`, and avoid direct `scripts/restore.sh` runs |
| [#517](https://github.com/google/stellar-engine/issues/517) | `3-security` | Omitting `3-security/terraform.tfvars` deploys zero KMS keys while `terraform.tfvars.sample` forces `HSM`; copy `terraform.tfvars.sample`, adjust `locations`, and remove `version_template` on FedRAMP Moderate |
| [#508](https://github.com/google/stellar-engine/issues/508), [#520](https://github.com/google/stellar-engine/issues/520) | `0-bootstrap`, `1-resman`, `3-security` | `sa_lockdown.sh` misses `<prefix>-tn-<env>-<tenant>-prod-0` `roles/owner` SAs and deleting the bootstrap project breaks Day-2 Stage 0 and 1 runs; disable `*-tn-*-prod-0` manually via `gcloud`, and set `billing_project` to `<prefix>-prod-iac-core-0` in Stage 0 and 1 providers before deleting the bootstrap project |
| [#521](https://github.com/google/stellar-engine/issues/521), [#433](https://github.com/google/stellar-engine/issues/433) | `0-bootstrap`, `1-resman`, `fast/` | WIF crashes `cicd.tf`, workflows pin `TF_VERSION: 1.7.4`, `stage-links.sh` prints `gcloud alpha storage cp`, and PR triggers bind apply SAs; merge `local.workload_identity_providers_defs`, bump workflow `TF_VERSION` to match `default-versions.tf`, use `gcloud storage cp`, and bind PR jobs only to `-0r` plan accounts |
| [#535](https://github.com/google/stellar-engine/issues/535), [#434](https://github.com/google/stellar-engine/issues/434) | `fedramp-high/cnap`, `cloud-armor` | `cnap` deletes Stage 3 ACM levels, pins `network_project_id` in `provider.tf`, uses a 2025 timestamp, and omits `sqli-v33-stable`; `cloud-armor` `throttle` rules shadow `Default Deny Rule` and `nodejs-v33-stable`; switch `cnap` to additive levels, `main_project_id`, and `sqli-v33-stable` before applying, and scope `cloud-armor` `throttle` rules by source range ahead of `deny(403)` rules |
| [#434](https://github.com/google/stellar-engine/issues/434), [#435](https://github.com/google/stellar-engine/issues/435), [#543](https://github.com/google/stellar-engine/issues/543), [#401](https://github.com/google/stellar-engine/issues/401), [#544](https://github.com/google/stellar-engine/issues/544), [#548](https://github.com/google/stellar-engine/issues/548) | `gemini-enterprise` | WAF rules and priority-90 `cloudarmor.tf` stay `preview = true`; rule `2000` bypasses `allowed_ip_ranges`; bucket import attaches a 30-day `Delete` rule; `enable_analytics = true` fails; `deploy.sh` hits `IMPORT_GCS=N` and `sed` bugs; `access_end_hour` is inclusive; docs claim `IL2`; set `preview = false` in `data/cloudarmor.yaml` and `gemini-stage-0/cloudarmor.tf`, tighten rule `2000`, strip `lifecycle_rule` in `discovery-engine.tf`, keep `enable_analytics = false`, enable `lenient_device` and `moderate_device`, subtract 1 from `access_end_hour`, use regional Compute Engine SSL certs, destroy `gemini-stage-1` first, and ignore `IL2` claims |
| [#445](https://github.com/google/stellar-engine/issues/445), [#402](https://github.com/google/stellar-engine/issues/402), [#543](https://github.com/google/stellar-engine/issues/543) | `gem4gov` | `license assign` fails on bare IDs and `update-compliance` enables agent sharing while leaving Private Knowledge Graph active; pass `projects/<project_number>/locations/us/licenseConfigs/<id>` with `--location us`, set `disable-agent-sharing: "FEATURE_STATE_ON"` in `engine_features.yaml`, and disable `knowledgeGraphConfig` via REST `PATCH` |
| [#536](https://github.com/google/stellar-engine/issues/536) | `shielded-vm-project`, `gke-hardened` | `e2-micro` rejects `SEV`; `gke-hardened` defaults `kms_key_names` to `"key-gke"` while `main.tf` reads `keys.default.id`, omits GKE and Fleet APIs, and hardcodes `us-east4-a` plus an EOL COS image; set `instance_type = "n2d-standard-2"` on `shielded-vm-project`, copy the `kms_key_names["key-gke"]` object under key `"default"` in `terraform.tfvars`, and pre-enable GKE and Fleet APIs |
| [#538](https://github.com/google/stellar-engine/issues/538), [#539](https://github.com/google/stellar-engine/issues/539) | `document-ai`, `cloud-translation`, `vertex-mlops`, `access-context-manager`, `beyondcorp` | `document-ai` shares one key across `us` and regional resources; `cloud-translation` hardcodes `us-central1`; `vertex-mlops` creates a duplicate project and sets `us-central`; `access-context-manager` sample has broken HCL; `beyondcorp` omits `compute.googleapis.com`; split `us` and regional KMS keys in `document-ai`, deploy `cloud-translation` in `us-central1`, target a net-new project and `us-east4` in `vertex-mlops`, fix HCL with `regions = ["US"]`, and pre-enable Compute Engine API |
| [#534](https://github.com/google/stellar-engine/issues/534), [#545](https://github.com/google/stellar-engine/issues/545) | Short-name inputs, `private-service-connect`, `datastore` | 11 blueprints describe short-name `kms_key_name`, `network_name`, or `subnetwork_name` inputs as full paths; `private-service-connect` needs a `projects/<project>/global/networks/<vpc>` self-link in `var.network_name` and pins `google < 7.0.0`; `datastore` pins `google < 6`; pass short names to `artifact-registry`, `bastion-pattern`, `bigquery`, `cloud-composer-environment`, `cloud-run`, `compute-engine`, `dataflow`, `datafusion`, `gcs-project`, `pub-sub-project`, and `shielded-vm-project`, pass a full self-link to `var.network_name`, mirror Google `6.x` or bump `provider.tf` locally for `private-service-connect`, and use `firestore` instead of `datastore` |
| [#540](https://github.com/google/stellar-engine/issues/540) | `cloud-workstations`, `firestore`, `cloud-functions`, `datafusion` | `cloud-workstations` and `firestore` miss service agent KMS grants; `cloud-functions` ignores 6 variables in `null_resource.cloud_function_deploy`, cites nonexistent `enable-apis.sh`, and leaks functions on destroy; `datafusion` defaults `kms_key_name = null` and outputs SA email in `service_endpoint`; pre-grant `compute-system` and `gcp-sa-firestore` KMS access, edit `cloud-functions/main.tf` flags and delete functions manually after `destroy`, set non-null `kms_key_name` plus PSA IPs on `datafusion`, and read `module.datafusion.resource.service_endpoint` via `output "resource"` |
| [#477](https://github.com/google/stellar-engine/issues/477), [#541](https://github.com/google/stellar-engine/issues/541) | `gitlab`, `cloud-scheduler-job` | `fedramp-high/gitlab` hardcodes `protocol = "HTTP"` and port `80` health checks plus `10.1.3.0/24` and `10.203.0.0/16` `Test` CIDRs; `third-party-solutions/gitlab` defaults `location = "EU"`; `cloud-scheduler-job` double-encodes `var.data` and omits publisher IAM; update `application-lb`, port `80` health check, `gitlab.rb` proxy settings, and `main.tf` CIDRs on `fedramp-high/gitlab`, set US `gcs_config.location`, pass plain text in `var.data`, and grant `roles/pubsub.publisher` to Cloud Scheduler |
| [#530](https://github.com/google/stellar-engine/issues/530), [#529](https://github.com/google/stellar-engine/issues/529), [#528](https://github.com/google/stellar-engine/issues/528) | [compute-resource-compromise.md](docs/runbooks/compute-resource-compromise.md), [customer-managed-encryption-keys-compromise.md](docs/runbooks/customer-managed-encryption-keys-compromise.md), [vpc-service-controls-violation.md](docs/runbooks/vpc-service-controls-violation.md) | `BEFORE_CLASSIC_FIREWALL` bypasses `ir-quarantine` tags, `gcloud storage rewrite` is invalid, and plural `VpcServiceControlsAuditMetadata` matches nothing; quarantine VMs with a top-priority `deny` rule in `<prefix>-<env>-fw-policy-0`, re-encrypt with `gcloud storage objects update`, and query singular `VpcServiceControlAuditMetadata` |

Also note documentation caveats in [docs/tdd.md](docs/tdd.md) regarding 365-day log retention tracked in [#532](https://github.com/google/stellar-engine/issues/532) and [#533](https://github.com/google/stellar-engine/issues/533), and in [docs/naming-convention.md](docs/naming-convention.md) regarding disallowed hyphens in custom IAM role IDs tracked in [#527](https://github.com/google/stellar-engine/issues/527).

## 2 Upgrade from v6.0.0

Upgrade existing v6.0.0 deployments sequentially from `0-bootstrap` through workload blueprints using saved Terraform plans so stateful Assured Workloads resources remain intact.

### 2.1 AI-assisted upgrade workflow

Hand this section and your `terraform.tfvars` files to an AI coding assistant so it prepares plans safely and pauses for operator approval before mutating cloud infrastructure.

- Never execute `scripts/deploy.sh`, `scripts/destroy.sh`, `scripts/clean.sh`, `scripts/restore.sh`, `fast/stages-aw/0-bootstrap/import.sh`, `terraform destroy`, or `terraform apply -auto-approve`.
- Never run imperative `terraform state mv`, `terraform state rm`, or `terraform import` commands without human approval; write `moved`, `removed` with `lifecycle { destroy = false }`, and `import` blocks in a temporary untracked `migrations.tf` file while leaving built-in `.tf` `moved` and `removed` blocks untouched.
- Verify Cloud Storage state bucket object versioning is enabled on `<prefix>-prod-iac-core-bootstrap-0`, `<prefix>-prod-iac-core-resman-0`, `<prefix>-prod-resman-net-0`, and `<prefix>-prod-resman-sec-0` before upgrading.
- Unset `GOOGLE_IMPERSONATE_SERVICE_ACCOUNT` and `CLOUDSDK_AUTH_IMPERSONATE_SERVICE_ACCOUNT` before switching stages so `<stage>-providers.tf` governs impersonation, and set your quota project to `<prefix>-prod-iac-core-0`.
- Save every plan with `terraform plan -out=upgrade.tfplan`, inspect `terraform show -no-color upgrade.tfplan`, and require explicit human approval whenever `destroy` or `forces replacement` appears on stateful resources.

```bash
unset GOOGLE_IMPERSONATE_SERVICE_ACCOUNT CLOUDSDK_AUTH_IMPERSONATE_SERVICE_ACCOUNT
gcloud config set project acme-prod-iac-core-0
gcloud auth application-default set-quota-project acme-prod-iac-core-0
```

Execute each stage in strict dependency order:

1. Verify a clean `terraform plan` on v6.0.0, unlock stage accounts from `fast/stages-aw/3-security` with `./sa_lockdown.sh --enable`, and check out v7.0.0.
2. Upgrade `0-bootstrap`, `1-resman`, `2-networking-a-fedramp` or `2-networking-b-il5-ngfw`, `3-security`, optional Stage 3 branches, and `blueprints/` in order.
3. In each downstream stage, run `bash ../../stage-links.sh gs://<prefix>-prod-iac-core-outputs-0` or pass an absolute `var.outputs_location` path because relative paths break symlinks, apply the printed copy or symlink commands using `gcloud storage cp` if needed, and run `terraform init -upgrade`.
4. Add temporary `migrations.tf` blocks from Section 2.2, review `upgrade.tfplan` with the operator, run `terraform apply upgrade.tfplan` after approval, remove `upgrade.tfplan` and temporary `migrations.tf`, and re-run `terraform plan` to confirm zero drift.
5. Re-lock and verify all automation accounts from `fast/stages-aw/3-security` via `./sa_lockdown.sh` and `./validation.sh --prefix acme`.

### 2.2 Manual state migrations

Stage `1-resman` automatically releases `module.tenant-core-folders-iam` and `module.tenant-self-folders-iam` via built-in `removed` blocks in `branch-tenants.tf`, and Stage `2-networking-a-fedramp` automatically releases `enable-oslogin` state addresses for `hub`, `Prod`, `Int`, and `Test` across all regimes via `oslogin.tf`. Apply the remaining manual migrations below before `terraform apply`.

- In `0-bootstrap` when `deploy_org_resources.org_policies = false`, list policies on your Assured Workloads folder via `gcloud org-policies list --folder=123456789012 --format="value(constraint)"` and import matching constraints into `module.root-folder-config[0].google_org_policy_policy.default["<constraint>"]` in `migrations.tf`:

  ```hcl
  # fast/stages-aw/0-bootstrap/migrations.tf
  import {
    to = module.root-folder-config[0].google_org_policy_policy.default["compute.requireOsLogin"]
    id = "folders/123456789012/policies/compute.requireOsLogin"
  }
  ```

- In `1-resman`, pin `tenants[*].locations.kms` to `var.regions.primary` or `null` if an existing tenant specifies a non-primary KMS region because Cloud KMS keyrings cannot be deleted and mismatching keyring vs bucket regions fail with HTTP 400 errors; update external callers of `output.team_cicd_repositories[*].service_account` to read `.apply` or `.plan`.
- In `2-networking-a-fedramp`, delete prior `enable-oslogin` workaround `import` blocks, move custom `var.envs_folders` keys outside `Prod`, `Int`, and `Test` into `oslogin_released`, and add one `import` block per host project covering `hub` and every spoke when `assured_workloads.regime` is `IL4`, `IL5`, unset, or `manage_oslogin_metadata = true`:

  ```hcl
  # fast/stages-aw/2-networking-a-fedramp/migrations.tf
  moved {
    from = module.env-spoke-projects["Dev"].google_compute_project_metadata_item.default["enable-oslogin"]
    to   = google_compute_project_metadata_item.oslogin_released["dev"]
  }

  import {
    to = google_compute_project_metadata_item.oslogin["hub"]
    id = "projects/acme-net-hub-host/meta-data/enable-oslogin"
  }

  import {
    to = google_compute_project_metadata_item.oslogin["prod"]
    id = "projects/acme-prod-net-host/meta-data/enable-oslogin"
  }
  ```

- In `2-networking-b-il5-ngfw`, apply the Section 1.4 HCL fixes first, update external consumers of `host_project_ids["<Env>"].project_id` to lowercase `host_project_ids["<env>"]`, and check `terraform state list` for `google_service_networking_connection.default["<Env>"]`; for every environment covered by `var.psa_ranges` including the `var.psa_ranges.dev` fallback across non-`Prod` environments, detach the duplicate connection in `migrations.tf` and detach `google_compute_global_address.private_service_connect_ip["<Env>"]` if producer services already use `default-peering`:

  ```hcl
  # fast/stages-aw/2-networking-b-il5-ngfw/migrations.tf
  moved {
    from = google_service_networking_connection.default["Dev"]
    to   = google_service_networking_connection.default_released["Dev"]
  }

  removed {
    from = google_service_networking_connection.default_released

    lifecycle {
      destroy = false
    }
  }

  # Include both blocks below when producer services already use default-peering.
  moved {
    from = google_compute_global_address.private_service_connect_ip["Dev"]
    to   = google_compute_global_address.private_service_connect_ip_released["Dev"]
  }

  removed {
    from = google_compute_global_address.private_service_connect_ip_released

    lifecycle {
      destroy = false
    }
  }
  ```

- For standalone `2-networking-b-il5-ngfw` or `3-security` deployments where `var.folder_ids` is `null`, ensure the deployer holds `resourcemanager.folders.move` so `module.folder.google_folder.folder[0]` can move under `common_services_folder` or `assured_workloads.folder`.
- Custom callers of `modules/access-context-manager` and `modules/beyondcorp` must drop the `project_id` and `region` inputs or the `region` input respectively, declare root `google` and `google-beta` providers, mark outputs referencing `oauth_client_secret` as `sensitive = true`, and read the `endpoint_name` output as a string.
- Existing `fedramp-high/gitlab` deployments holding a bare region in `var.zone` such as `us-east4` must append `-a` to form `us-east4-a` and run `terraform init -upgrade` for `hashicorp/time` before planning to prevent VM and UMIG replacement.
- Existing `pub-sub-project` deployments must import existing subscriptions into `module.pubsub.google_pubsub_subscription.default["<sub_name>"]` and define `var.subscriptions` or grant external subscription IAM because empty `var.subscriptions` removes `roles/pubsub.subscriber`.
- Existing `cloud-workstations` deployments using a private `var.image` must set `var.image_repository` as `{ location, name, project_id }` and grant the Terraform deployer `roles/iam.serviceAccountUser` on `var.main_project_id` or the created `workstation-vm` service account before upgrading so workstations keep Artifact Registry access.
- Deployers upgrading `cloud-run`, `cnap`, `pub-sub-project`, `vertex-mlops`, `cloud-workstations`, `cloud-functions`, and `cloud-composer-environment` require `resourcemanager.projects.setIamPolicy` plus resource-level `setIamPolicy` on target Cloud Run services and jobs, Artifact Registry repositories, Shared VPC subnetworks, buckets, BigQuery datasets, Pub/Sub topics and subscriptions, and service accounts; pre-grant IAM for any external resources, update `vertex-mlops` `model_garden_pytorch_flux.ipynb` copies to use `notebook-sa`, and pass `sa-mlops` explicitly on Dataflow jobs launched by `sa-mlops`.
- Deployers upgrading `postgresql` need `compute.firewalls.delete` on `var.network_project_id` once and should remove deprecated `firewall_name`, `firewall_source_range`, and `allowed_firewall_ports` variables from `terraform.tfvars`.

### 2.3 Outages and maintenance windows

Schedule maintenance windows for the changes below because each triggers instance replacements, restarts, traffic restrictions, or brief IAM cutovers.

- Stage 2b rolling NGFW replacement resets open sessions, disables serial port access, overwrites uncommitted PAN-OS edits unless saved in `templates/bootstrap.xml.tpl`, and requires Suite-B-GCM-256 ciphers on IPsec peers using the `default` profile.
- Enforcing `access_config.private_nodes = true` in `il5/gke` and `fedramp-high/gke` when `gke_cluster_enable_private_endpoint = false` requires Cloud NAT plus Private Google Access beforehand and can force GKE cluster replacement.
- Hardening `fedramp-high/gitlab` restarts the GitLab VM in place for Shielded VM plus OS Login and replaces the `"nodes"` GKE node pool onto `module.gke-node-sa`.
- Upgrading `dataflow` can update or replace tracked `google_dataflow_job.job` instances, while opting an existing `cloud-spanner` database or `cloud-composer-environment` into `var.kms_key_name` forces replacement; `blueprints/fedramp-high/cloud-spanner` omits `deletion_protection` so `modules/spanner-instance-se` defaults it to `true` via `coalesce`, blocking CMEK database replacement until you temporarily set `deletion_protection = false` in `blueprints/fedramp-high/cloud-spanner/main.tf` and apply that change first.
- Deleting `google_compute_firewall.postgres` in `postgresql` and scoping `google_compute_firewall.default` in `bastion-pattern` removes ingress for unrelated Shared VPC VMs unless targeted rules are created first.
- Enforcing 8 KB request-body blocks in `cloud-armor` and `cnap`, encrypted Endpoint Verification with `iap_user` replacement in `beyondcorp`, and all `conditions` via `AND` in `access-context-manager` rejects oversized payloads or non-compliant devices immediately.
- Running `sa_lockdown.sh` without the `--sa` flag disables `-0r` plan, Stage 3 branch, and `envs` accounts, halting CI/CD `plan` pipelines until re-enabled with comma-separated names like `./sa_lockdown.sh --enable --sa "bootstrap-r,resman-r,networking-r,security-r"`.
- Using `vpc_sc.perimeter_default.dry_run_spec` in `3-security` shares `access_levels`, `ingress_policies`, `egress_policies`, and `resource_discovery` with enforced `status`, so define trial rules under distinct keys and list trial projects in `resource_discovery.ignore_projects`.

### 2.4 Multi-pass Terraform applies

Plan for multiple `terraform apply` passes or targeted runs across these v7.0.0 upgrade scenarios.

1. Run stages sequentially with `fast/stage-links.sh` refreshes so `0-bootstrap` exports `automation.kms_keys.gcs` to `1-resman`, `1-resman` exports `service_accounts.envs` and GKE or GCVE accounts to `3-security`, and `2-networking-*` creates spoke projects and `host_project_ids` for `3-security` and Stage 3 branches.
2. Apply resource-scoped IAM bindings using the `-target` flag before running a full `terraform apply` that deletes legacy project bindings when minimizing authorization gaps:

   | Blueprint | Pre-apply target addresses and prerequisite |
   | --- | --- |
   | `cloud-run` | Target `google_cloud_run_v2_service_iam_member.cloud_run_invoker` or `google_cloud_run_v2_job_iam_member.cloud_run_invoker` |
   | `cnap` | Target `google_cloud_run_v2_service_iam_member.iap_sa_cloudrun_invoker` |
   | `pub-sub-project` | Populate `var.subscriptions` and stage `module.pubsub.google_pubsub_subscription.default["<sub_name>"]` imports first, then target `module.pubsub` |
   | `vertex-mlops` | Target `module.gcs-bucket`, `module.gcs-bucket-cloudbuild`, `module.bq-dataset`, and `google_service_account_iam_member.service_account_user` first; `module.project` swaps `shared_vpc_service_config` subnet IAM during full apply |
   | `cloud-workstations` | Set `var.image_repository` if using a private image, then target `google_compute_subnetwork_iam_member.network_user` and `google_artifact_registry_repository_iam_member.artifact_registry_reader` |
   | `cloud-functions` | Target `google_cloud_run_v2_service_iam_member.cloud_invoker` and `module.registry-docker.google_artifact_registry_repository_iam_member.members["artifactregistry-writer-runner"]` first, noting `cloud_invoker` triggers `null_resource.cloud_function_deploy` if changed |
   | `cloud-composer-environment` | Target `google_compute_subnetwork_iam_member.composer_network_user` |

3. Re-run `terraform apply` once in `2-networking-b-il5-ngfw` if deleting an unused `google_compute_global_address.private_service_connect_ip["<Env>"]` races `psa_connection` updating `reserved_peering_ranges`.
4. Run a two-pass GKE rebuild when setting variable `gke_cluster_enable_private_endpoint = false` forces cluster replacement while variable `enable_deletion_protection = true` is active: apply `enable_deletion_protection = false` on v6.0.0 first, then upgrade to v7.0.0.
5. Apply custom `modules/access-context-manager` or `modules/beyondcorp` upgrades once before removing a `module` block in a second apply, and re-run `1-resman` once if custom `roles/browser` tenant folder bindings hit a delete-after-create race.
