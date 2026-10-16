# Stellar Engine code review guide

## 1 Repository architecture

Stellar Engine provides Terraform landing zone stages under `fast/stages-aw/`, workload blueprints under `blueprints/`, reusable modules under `modules/`, and repository validation utilities under `tools/` for regulated Google Cloud environments across FedRAMP Moderate, FedRAMP High, IL4, and IL5.

### 1.1 Module composition

* Reuse existing modules from `modules/` and stage constructs from `fast/stages-aw/` instead of declaring raw `google_*` resources, creating wrapper modules, or provisioning overlapping service accounts.
* Keep modules lean, flat, and scoped to a single resource domain, encapsulating IAM bindings, logging, and organization policies alongside the primary resource rather than mixing unrelated resources outside `project-factory` and `net-vpc-factory`.
* Treat `blueprints/il5/*` as the canonical source for shared workload blueprints because matching subdirectories under `blueprints/fedramp-high/*` are Git `120000` directory symlinks pointing to `../il5/*`.
* Keep `blueprints/gemini-enterprise` compliance regimes scoped to `fedramp-moderate`, `fedramp-high`, `il4`, and `il5`, ordered adjacent by family in `deploy.sh` and `variables.tf`, and never reintroduce deprecated `us-regimes` or `experimental` values.
* Prefer Google-maintained container registries such as `gcr.io` and Artifact Registry over `mcr.microsoft.com/devcontainers` in devcontainer and CI workflow configurations.

### 1.2 Change scope

* Keep pull requests atomic, single-purpose, and independently testable so regressions can be isolated with `git bisect` and rolled back cleanly.
* Never mix structural refactoring with behavioral feature additions or bug fixes in the same pull request, and flag diffs that bundle unrelated stages, modules, or blueprints.
* Modify code, schemas, and documentation only to fix concrete functional defects or implement the requested capability.
* Reject unrequested default value bumps, cosmetic reformatting outside touched files, bulk `sensitive = true` or `0600` annotation churn, and changes that alter existing `for_each` resource key formats or force caller state migrations without an explicit `upgrade-note`.

## 2 Review signal

Evaluate diffs and static analysis findings from a skeptical maintainer perspective, prioritizing reproducible defects that affect runtime behavior, deployment reliability, or security posture:

* Focus on Terraform plan and apply correctness, least-privilege IAM, Customer-Managed Encryption Keys, network segmentation, backward compatibility, and Assured Workloads compliance across FedRAMP Moderate, FedRAMP High, IL4, and IL5.
* Inspect the full file context before flagging missing imports, undefined symbols, or uninitialized locals so unchanged definitions outside the diff hunk do not produce false positives.
* Reject defensive theater on local CLI utilities, linters, test runners, and maintainer scripts under `tools/` and `scripts/`, including SSRF or DNS resolution checks on local link checkers, `.is_relative_to()` path-traversal guards on local test runners, XML or SHA sanitizers on maintainer-triggered workflows, and pedantic regex or escaping churn when native library idioms suffice.
* Flag any committed files, examples, or pull request descriptions that contain real GCP project IDs, numeric project numbers, organization IDs, billing account IDs, personal or corporate email addresses, internal shortlinks, internal issue tracker IDs, or live sandbox resource names, and require generic placeholders such as `my-project`, `123456789012`, `user:admin@example.com`, and `test-bucket`.
* Verify that pull requests preserve the `.github/pull_request_template.md` checklist, link the resolved GitHub issue via `Fixes #<id>`, document empirical verification, and append a `Breaking Changes` section with an `upgrade-note` code fence whenever variable types, required inputs, or state keys change in a backward-incompatible way.
* Avoid purely stylistic or subjective comments when the code already conforms to `tools/lint.sh` and `tools/run_tests.sh`.

## 3 Terraform guidelines

### 3.1 Module interfaces

* Keep Terraform and provider version constraints aligned with each directory's `versions.tf` file and the repository baseline with `required_version = ">= 1.10.2"` and provider `version = ">= 6.21.0, < 7.0.0"`.
* Never commit OpenTofu `versions.tofu` files or edit provider version constraints in individual modules out of sync with the repository baseline.
* Declare `provider = google-beta` explicitly on resources and attributes that require the beta provider under the active `versions.tf` constraints, including `google_cloud_run_v2_worker_pool`, `google_kms_autokey_config`, `google_folder_service_identity`, and `google_spanner_instance`.
* Prefer compact `object({...})` variables with `optional()` attributes over proliferating scalar variables, omitting explicit defaults on `optional()` when the underlying provider default should apply.
* Use `map(...)` collections rather than `list(...)` for multi-instance resources so `for_each` state keys remain stable across insertions and removals, and use deterministic `prefix` tokens rather than random string suffixes for resource naming.
* Include plan-time `validation` blocks on variables that mirror underlying provider ENUM values.
* Never hardcode project IDs, folder IDs, or regions in module or stage code, never set `project`, `region`, or `zone` on `provider "google"` or `provider "google-beta"` blocks, and never use `local-exec` or `remote-exec` provisioners when native Terraform resources or data sources exist.
* Preserve safe upstream defaults such as `deletion_protection = coalesce(each.value.deletion_protection, true)` on stateful resources.

### 3.2 Plan-time evaluation

* Never pass map or `yamldecode` object values into `coalesce(val, {})` because Terraform requires all `coalesce` arguments to share the exact same structural object type, causing non-empty decoded YAML objects to fail type unification against `object({})`.
* Convert decoded YAML mappings safely with `try({ for k, v in yamldecode(...) : k => v }, {})` and guard nullable map variables with explicit ternaries such as `val == null ? {} : val`.
* Use `try(obj.attr, null) != null` rather than `can(obj.attr) && obj.attr != null` when inspecting decoded YAML or JSON objects because Terraform does not short-circuit `&&` and fails at plan time when `attr` is absent.
* Ensure conditional YAML templates rendered with `templatefile` and decoded with `yamldecode` include `---` and an `%{ else ~}\n{}\n%{ endif ~}` fallback when all constraints are omitted for a compliance regime.
* Validate `type = any` map variables in `variables.tf` by checking element types explicitly, such as `can({ for k, v in tomap(var.essential_contacts) : k => tolist(v) })`, rather than bare `can(tomap(...))`.
* Coalesce optional string keys to `""` when indexing `for_each` resource maps with a default `""` key, such as `google_compute_forwarding_rule.default[coalesce(var.service_attachment.forwarding_rule, "")].id`.
* Support symbolic `$namespace:key` interpolation via the `context` variable using `ctx` and `ctx_p = "$"` locals in `main.tf`, excluding `condition_vars` from `local.ctx` flattening when IAM condition templates are used.
* Normalize resource prefixes on context fallbacks when the GCP API requires `projects/` or `folders/`, and reuse existing locals such as `local.folder_number` instead of repeating `replace(local.folder_id, "folders/", "")`.
* Keep resource blocks under 79 characters per line by moving complex `for` transformations and conditional strings into `locals`, using `_`-prefixed block-level locals for intermediate transformations, and wrapping multi-line ternary operators in parentheses with aligned `?` and `:` branches.
* Declare explicit `depends_on = [module.<project>]` on data sources such as `data.google_logging_project_settings` that read a `project_id` statically computed by a module in the same stage, and bind `for_each` `time_sleep` dependencies per instance via `time_sleep.peering_delay[each.key]` rather than across the entire resource map.

### 3.3 Security controls

* Store generated SSH private keys, TLS keys, and passwords in CMEK-encrypted Secret Manager secrets via `modules/secret-manager` with least-privilege `roles/secretmanager.secretAccessor` bindings rather than writing sensitive material to `local_file` resources, plaintext outputs, or Cloud Storage buckets.
* Provision dedicated service accounts via `modules/iam-service-account` with least-privilege roles instead of using default Compute Engine `-compute@developer.gserviceaccount.com` service accounts, static `google_service_account_key` resources, or broad Editor and Owner bindings.
* Enforce Customer-Managed Encryption Keys across supported storage, database, logging, and messaging resources, minimum TLS 1.2 via `constraints/gcp.restrictTLSVersion`, and regional data boundary constraints via `constraints/gcp.resourceLocations`.
* Scope `custom.kmsRotation` custom constraints to `method_types: ["CREATE"]` so `terraform destroy` can clear `rotationPeriod` via `UPDATE` prior to key destruction, and gate `compute.requireOsLogin` in `custom-org-policies/compute_policy.yaml` so enforcement is skipped on `IL4` and `IL5`.
* When evaluating or testing IAM conditional bindings against `resource.name`, use numeric GCP Project Numbers rather than project ID strings to match GCP IAM runtime evaluation.

## 4 Documentation style

### 4.1 Interface documentation

* Keep variable declarations in `variables.tf` and output declarations in `outputs.tf` sorted alphabetically to satisfy `FAIL_UNSORTED_VARS` and `FAIL_UNSORTED_OUTPUTS`, with every description ending in a period to satisfy `FAIL_VARIABLE_PERIOD` and `FAIL_OUTPUT_PERIOD`.
* Require updated `<!-- BEGIN TFDOC -->` tables generated via `tools/tfdoc.py` whenever `variables.tf` or `outputs.tf` files change so `tools/check_documentation.py` passes without `FAIL_STALE_README`.
* When modifying factory-backed modules or stages, require synchronized JSON schema updates under `schemas/`, regenerated `.schema.md` files via `tools/schema_docs.py`, and identical duplicate files verified via `tools/duplicate-diff.py`.

### 4.2 Prose conventions

* Write documentation, code comments, and review feedback in concise, objective engineering prose using active voice, present tense, and second-person address, explaining the rationale behind non-obvious design decisions rather than restating what the code does.
* State the outcome or user value first in section openings, prefer short single-idea bullets over dense paragraphs, and accompany flags, field names, and status codes with clarifying nouns.
* Use sentence case and concise 2-to-4-word numbered headings in guides and READMEs, and keep documentation version-agnostic by referencing `versions.tf` and upstream provider docs rather than hardcoding tool or runtime versions.
* Never use em-dashes, ampersands in prose or headings, unnecessary parentheses, first-person pronouns such as `I`, `we`, `my`, or `our` in documentation, validation openers such as `spot on`, `you're right`, or `great point`, AI cliches such as `delve`, `testament`, `tapestry`, or `underscore`, bolded lead-in labels or colon prefixes in bullet lists, backticks inside Markdown headings, or horizontal rules such as `---` as section dividers.

## 5 Scripting and testing

* Verify that Python files pass `pyflakes` and CodeQL `py/unused-local-variable` checks with no unused imports, unused local variables, or undefined names, format Python code with `yapf` using `.style.yapf`, and stay within the 79-character line limit.
* Execute modified code paths and unit tests via `bash tools/run_tests.sh`, `pytest`, `pyflakes`, and `shellcheck` rather than relying on syntax-only checks such as `py_compile` or `bash -n`.
* When resource attributes change in modules or stages covered by `tftest.yaml` or `README.md` `# tftest` directives, require updated YAML plan inventories and verify that every changed inventory line maps directly to the intended change.
* Guard empty collections before constructing `click.IntRange(1, len(items))` in interactive CLI prompts, and guard nullable dictionary fields such as `item.get("name")` before calling string methods such as `.split("/")`.
* On Container-Optimized OS `cloud-config.yaml` and startup scripts, guard file moves and `base64` decodes from `/tmp` with `[ ! -f /tmp/... ] ||` because `/tmp` is a `tmpfs` cleared across reboots while `/run` or persistent disks retain state, enforce `0770` or `0700` directory permissions and `0600` for private keys rather than `0777`, and bound network retry loops with exponential backoff.
* In repository shell scripts that invoke `find` such as `tools/lint.sh`, prune `.git`, `.terraform`, `.venv`, `venv`, `node_modules`, and `__pycache__` so local virtual environments and initialized Terraform caches do not cause false-positive failures.
* Require unit test coverage under `tests/` when adding or modifying CLI subcommands, stage validations, or repository tooling.
