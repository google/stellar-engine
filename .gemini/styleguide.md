# Stellar Engine code review guide

## 1 Repository architecture

Stellar Engine provides Terraform landing zone stages under `fast/stages-aw/`, workload blueprints under `blueprints/`, reusable modules under `modules/`, and repository validation utilities under `tools/` for regulated Google Cloud environments across FedRAMP Moderate, FedRAMP High, IL4, and IL5.

Follow these structural conventions during code review:

* Reuse existing modules from `modules/` and stage constructs from `fast/stages-aw/` instead of duplicating raw resources or creating overlapping service accounts.
* Treat `blueprints/il5/*` as the canonical source for shared workload blueprints because matching subdirectories under `blueprints/fedramp-high/*` are Git `120000` directory symlinks pointing to `../il5/*`.
* Keep `blueprints/gemini-enterprise` compliance regimes scoped to `fedramp-moderate`, `fedramp-high`, `il4`, and `il5`, ordered adjacent by family in `deploy.sh` and `variables.tf`, and never reintroduce deprecated `us-regimes` or `experimental` values.

## 2 Review scope and signal

Prioritize actionable defects that affect runtime behavior, deployment reliability, or security posture:

* Focus on Terraform plan and apply correctness, least-privilege IAM, Customer-Managed Encryption Keys, network segmentation, and Assured Workloads compliance across FedRAMP Moderate, FedRAMP High, IL4, and IL5.
* Inspect the full file context before flagging missing imports or undefined symbols so unchanged imports outside the diff hunk do not produce false positives.
* Do not suggest defensive theater on local CLI utilities, linters, or maintainer scripts under `tools/`, such as SSRF or DNS checks on local link checkers, path-traversal guards on local test runners, XML or SHA sanitizers on internal CI helpers, or pedantic regex churn.
* Avoid purely stylistic or subjective comments when the code already conforms to `tools/lint.sh` and `tools/run_tests.sh`.

## 3 Terraform guidelines

### 3.1 Module and provider contracts

Enforce consistent module and provider boundaries across stages, modules, and blueprints:

* Keep Terraform and provider version constraints aligned with each directory's `versions.tf` file and the repository baseline.
* Never commit OpenTofu `versions.tofu` files or introduce conflicting provider constraints across individual modules.
* Declare `provider = google-beta` explicitly on resources and attributes that require the beta provider under the active `versions.tf` constraints, including `google_cloud_run_v2_worker_pool`, `google_kms_autokey_config`, `google_folder_service_identity`, and `google_spanner_instance`.
* Preserve safe upstream defaults such as `deletion_protection = coalesce(each.value.deletion_protection, true)` on stateful resources and preserve existing `for_each` resource key formats so callers do not face destructive state migrations.

### 3.2 Plan-time and type evaluation

Check for HCL type-system and plan-time evaluation pitfalls across stages, modules, and blueprints:

* Never pass map or `yamldecode` object values into `coalesce(val, {})` because Terraform requires all `coalesce` arguments to share the exact same structural object type, causing non-empty decoded YAML objects to fail type unification against `object({})`.
* Convert decoded YAML mappings safely with `try({ for k, v in yamldecode(...) : k => v }, {})` and guard nullable map variables with explicit ternaries such as `val == null ? {} : val`.
* Use `try(obj.attr, null) != null` rather than `can(obj.attr) && obj.attr != null` when inspecting decoded YAML or JSON objects because Terraform does not short-circuit `&&` and fails at plan time when `attr` is absent.
* Ensure conditional YAML templates rendered with `templatefile` and decoded with `yamldecode` include `---` and an `%{ else ~}\n{}\n%{ endif ~}` fallback when all constraints are omitted for a compliance regime.
* Validate `type = any` map variables in `variables.tf` by checking element types explicitly, such as `can({ for k, v in tomap(var.essential_contacts) : k => tolist(v) })`, rather than bare `can(tomap(...))`.
* Coalesce optional string keys to `""` when indexing `for_each` resource maps with a default `""` key, such as `google_compute_forwarding_rule.default[coalesce(var.service_attachment.forwarding_rule, "")].id`.
* Normalize resource prefixes on context fallbacks when the GCP API requires `projects/` or `folders/`, and reuse existing locals such as `local.folder_number` instead of repeating `replace(local.folder_id, "folders/", "")`.
* Declare explicit `depends_on = [module.<project>]` on data sources such as `data.google_logging_project_settings` that read a `project_id` statically computed by a module in the same stage, and bind `for_each` `time_sleep` dependencies per instance via `time_sleep.peering_delay[each.key]` rather than across the entire resource map.

### 3.3 Security and compliance controls

Verify that infrastructure changes preserve Assured Workloads security controls:

* Store generated SSH private keys, TLS keys, and passwords in CMEK-encrypted Secret Manager secrets via `modules/secret-manager` with least-privilege `roles/secretmanager.secretAccessor` bindings rather than writing sensitive material to `local_file` resources, plaintext outputs, or GCS buckets.
* Provision dedicated service accounts via `modules/iam-service-account` instead of using default Compute Engine `-compute@developer.gserviceaccount.com` service accounts or `google_service_account_key` resources.
* Scope `custom.kmsRotation` custom constraints to `method_types: ["CREATE"]` so `terraform destroy` can clear `rotationPeriod` via `UPDATE` prior to key destruction, and gate `compute.requireOsLogin` in `custom-org-policies/compute_policy.yaml` so enforcement is skipped on `IL4` and `IL5`.

### 3.4 Documentation synchronization

Verify that Terraform interface documentation stays synchronized with code changes:

* Keep variable declarations in `variables.tf` and output declarations in `outputs.tf` sorted alphabetically to satisfy `FAIL_UNSORTED_VARS` and `FAIL_UNSORTED_OUTPUTS`, with every description ending in a period to satisfy `FAIL_VARIABLE_PERIOD` and `FAIL_OUTPUT_PERIOD`.
* Require updated `<!-- BEGIN TFDOC -->` tables generated via `tools/tfdoc.py` whenever `variables.tf` or `outputs.tf` files change so `tools/check_documentation.py` passes without `FAIL_STALE_README`.

## 4 Python and shell guidelines

Apply these verification rules to CLI tools, startup scripts, and tests:

* Verify that Python files pass `pyflakes` and CodeQL `py/unused-local-variable` checks with no unused imports, unused local variables, or undefined names, and stay within repository line-length limits.
* Guard empty collections before constructing `click.IntRange(1, len(items))` in interactive CLI prompts, and guard nullable dictionary fields such as `item.get("name")` before calling string methods such as `.split("/")`.
* On Container-Optimized OS `cloud-config.yaml` and startup scripts, guard file moves and `base64` decodes from `/tmp` with `[ ! -f /tmp/... ] ||` because `/tmp` is a `tmpfs` cleared across reboots while `/run` or persistent disks retain state, and enforce `0770` or `0700` directory permissions and `0600` for private keys rather than `0777`.
* In repository shell scripts that invoke `find` such as `tools/lint.sh`, prune `.git`, `.terraform`, `.venv`, `venv`, `node_modules`, and `__pycache__` so local virtual environments and initialized Terraform caches do not cause false-positive failures.
* Require unit test coverage under `tests/` when adding or modifying CLI subcommands, stage validations, or repository tooling.
