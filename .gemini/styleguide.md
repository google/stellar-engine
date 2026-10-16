# Stellar Engine code review guide

## 1 Repository architecture

Stellar Engine provides Terraform landing zone stages under `fast/stages-aw/`, workload blueprints under `blueprints/`, reusable modules under `modules/`, and repository validation utilities under `tools/` for regulated Google Cloud environments across FedRAMP Moderate, FedRAMP High, IL4, and IL5.

Follow these structural conventions during code review:

* Reuse existing modules from `modules/` and stage constructs from `fast/stages-aw/` instead of duplicating raw resources or overlapping service accounts.
* Treat `blueprints/il5/*` as the canonical source for shared workload blueprints because matching subdirectories under `blueprints/fedramp-high/*` are Git directory symlinks to `../il5/*`.
* Align variable, resource, and output names with existing module contracts and `GEMINI.md`.

## 2 Review scope and signal

Prioritize actionable defects that affect runtime behavior, deployment reliability, or security posture:

* Focus on Terraform plan and apply correctness, least-privilege IAM, Customer-Managed Encryption Keys, network segmentation, and Assured Workloads compliance across FedRAMP Moderate, FedRAMP High, IL4, and IL5.
* Flag concrete bugs, unguarded reboot or state-transition failures, undefined symbols, and breaking changes to variable or output contracts.
* Do not suggest defensive theater on local CLI utilities, linters, or maintainer scripts under `tools/`, such as SSRF or DNS checks on local link checkers, path-traversal guards on local test runners, or XML and SHA sanitizers on internal CI helpers.
* Avoid purely stylistic or subjective comments when the code already conforms to `tools/lint.sh` and `tools/run_tests.sh`.

## 3 Terraform guidelines

### 3.1 Module and provider contracts

Enforce consistent module and provider boundaries across stages and blueprints:

* Keep Terraform and provider version constraints aligned with each directory's `versions.tf` file.
* Preserve existing `for_each` resource key formats so callers do not experience state migration churn.
* Validate complex input variables in `variables.tf` with explicit `validation` blocks that verify nested collection types.

### 3.2 Plan-time evaluation

Check for common HCL evaluation pitfalls in stages and blueprints:

* Use `try(obj.attr, null) != null` rather than `can(obj.attr) && obj.attr != null` when inspecting decoded YAML or JSON objects so Terraform does not fail on missing attributes during plan evaluation.
* Declare explicit `depends_on` references when a data source reads a project identifier computed by a module in the same stage.
* Ensure conditional YAML templates decoded with `yamldecode` emit a valid empty mapping when all constraints are omitted for a given compliance regime.

### 3.3 Documentation synchronization

Verify that Terraform interface documentation stays synchronized with code changes:

* Keep variable declarations in `variables.tf` and output declarations in `outputs.tf` sorted alphabetically, with every description ending in a period.
* Require updated `<!-- BEGIN TFDOC -->` tables generated via `tools/tfdoc.py` whenever `variables.tf` or `outputs.tf` files change.

## 4 Python and shell guidelines

Apply these verification rules to CLI tools, startup scripts, and tests:

* Verify that Python files have no unused imports or undefined names and stay formatted within repository line-length limits.
* Ensure shell scripts and cloud-init unit commands quote variable expansions and guard operations on ephemeral `/tmp` files so services remain idempotent across instance reboots.
* Require unit test coverage under `tests/` when adding or modifying CLI subcommands, stage validations, or repository tooling.
