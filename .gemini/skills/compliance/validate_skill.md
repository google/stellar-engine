---
name: compliance-validate
description: Reference package review guide for validating generated FedRAMP Low, FedRAMP Moderate, FedRAMP High, FISMA Low, FISMA Moderate, FISMA High, DoD IL2, DoD IL4, DoD IL5, DoD IL6, and CJIS ATO packages (GovRAMP / StateRAMP and FedRAMP Tailored / LI-SaaS fail closed).
---
<!-- skip boilerplate check -->

# Package review guide (`validate_skill.md`)

> **Reference Sub-Specification:** This guide is a reference specification under `<SKILL_DIR>/validate_skill.md` and is used alongside the parent `compliance` skill ([SKILL.md](SKILL.md)).

Use this guide after the three workflow scripts in [SKILL.md](SKILL.md) have run. It tells the
agent how to review the whole package as a security control assessor would: check that the
Terraform implements what was planned, that it is configured securely, and that the documents
describe what the Terraform actually does.

The scripts check structure and placeholders; they do not judge whether a narrative is true. That
judgment is the purpose of this review. Do not assign a pass percentage (`readiness_score` is `None`) or declare the system ready
for authorization: authorization is a risk decision made by the Authorizing Official (AO).

## Severity

Classify each finding:

- **CAT I**: exposes the system to compromise now. Examples: a plaintext secret in code,
  unencrypted sensitive data, or administrative ports open to `0.0.0.0/0`.
- **CAT II**: the documents and the implementation disagree, or a planned control is missing.
  Examples: the SSP claims dual-region failover but Terraform defines one region; logs are not
  exported to the CSSP or SIEM.
- **CAT III**: procedural or documentation gaps that do not affect the implemented controls.

## Phase 1: Plan versus code

1. **Intent.** If `<TARGET_FOLDER>/spec.md` exists, read it and list each planned capability
   (regions, networks, databases, service accounts, encryption). For each one, find the Terraform
   resource that implements it. A planned item with no resource is a CAT II finding.
2. **Scope creep.** List significant resources that the plan and the README do not mention (extra
   VPCs, instances, external IP addresses). Report them as CAT II findings.
3. **Inputs.** If the folder has a `variables.yaml`, or a `terraform.tfvars` / `*.auto.tfvars`
   file, check that its values (project IDs, CIDR ranges, domains) reach the resources through
   variables or locals rather than being replaced by hardcoded strings.
4. **Repository rules**:
   - No generated files (`ato_artifacts/`, `system_inventory.json`) at the repository root.
   - The blueprint, and any module it adds, has a `README.md` that explains its purpose, inputs,
     outputs, and dependencies.
   - Names follow `docs/naming-convention.md`.

## Phase 2: Secure configuration

Review every `.tf`, YAML, JSON, Dockerfile, and application file in the target folder.

1. **Secrets (IA-5, SC-28; CWE-798).** No API keys, passwords, private keys, service account key
   files, or tokens in code or variable defaults.
2. **Least privilege (AC-2, AC-6).** No `roles/owner`, `roles/editor`, or wildcard permissions.
   Each service account has a single purpose and only the roles it needs.
3. **Boundary (SC-7, AC-17).**
   - Ingress is denied by default.
   - No `0.0.0.0/0` ingress to 22, 3389, database ports, or admin consoles. Administrative access
     goes through Identity-Aware Proxy (source range `35.235.240.0/20`) or a bastion.
   - Google APIs are reached privately where required: Private Google Access, Private Service
     Connect, or the `restricted.googleapis.com` range `199.36.153.4/30`, and VPC Service Controls
     perimeters where the baseline calls for them.
4. **Encryption (SC-8, SC-12, SC-13, SC-28).**
   - Buckets, disks, datasets, and databases use customer-managed keys (CMEK) where the baseline
     requires them.
   - The key protection level (`version_template.protection_level`: `SOFTWARE` or `HSM`) is what
     the SSP claims.
   - The key `rotation_period` matches the organization's SC-12 parameter. The validator's linter
     flags rotation periods longer than 365 days.
   - TLS settings (for example `google_compute_ssl_policy.min_tls_version`) match what the SSP
     claims.
5. **Storage (SC-28, CP-9).** `public_access_prevention = "enforced"` and uniform bucket-level
   access on buckets; versioning and retention where the SSP claims them.
6. **Logging (AU-2, AU-6, AU-12).** Log sinks export Admin Activity, Data Access, and VPC flow logs
   to the CSSP or SIEM named in `compliance_config.yaml`. In DoD IL4/IL5 boundaries, detection must
   not depend on Security Command Center inside the boundary (see the rules in SKILL.md).
7. **Containers and applications** (if the folder has them). Base images pinned by digest or exact
   version (no `:latest`); a non-root `USER`; minimal base images; dependency lockfiles present.

## Phase 3: Script results

Run the validator using the skill's isolated virtual environment:

```bash
<SKILL_DIR>/.venv/bin/python <SKILL_DIR>/scripts/validate_compliance_artifacts.py <TARGET_FOLDER> --fix
```

Supported CLI options for `validate_compliance_artifacts.py`:
- `--fix`: Re-runs `generate_compliance_artifacts.py` to synchronize drift before auditing. Backs up existing artifacts to `ato_artifacts_backup_<timestamp>/`.
- `--fill-example-data`: Relabels `[CONFIG_REQUIRED: ...]` placeholders as `[EXAMPLE_DATA_REQUIRED: ...]` for an AI agent or reviewer to fill.
- `--no-fill-example-data`: Leaves placeholders as `[CONFIG_REQUIRED: ...]` (default in non-interactive sessions).
- `--policy-format={both,docx,markdown}`: With `--fix`: overrides policy export format.
- `--data-format={both,excel,yaml}`: With `--fix`: overrides structured data format.
- `--oscal-format={both,json,yaml,none}`: With `--fix`: overrides OSCAL export format.
- `--oscal-version=<VERSION>`: With `--fix`: target OSCAL specification version (e.g. `1.2.3` or `1.1.0`).
- `--run-scanners`: With `--fix`: runs live security scanners (Checkov, Semgrep) on a sanitized private copy of target.
- `--update-stigs`: Pulls updated DISA STIG/SRG benchmark versions from the configured catalog source.
- `--stigs-mode={auto,online,offline}`: Overrides `disa_stigs.update_mode` (`auto`, `online`, or `offline`).
- `--stigs-catalog=<URL_OR_PATH>`: Overrides `disa_stigs.catalog_source` with a custom HTTPS URL or local JSON catalog path.
- `--no-linter`: Disables deterministic semantic linter evaluation.
- `--no-linter-strict`: Does not fail validation on CAT I semantic linter findings (structural and assessor CAT I failures still fail closed).

Read its summary:

- **Unresolved tokens.** Any `{{ TOKEN }}` left in the output is a generation defect.
- **Placeholders.** `[CONFIG_REQUIRED: ...]` and `[EXAMPLE_DATA_REQUIRED: ...]` mark values
  that people must supply. List them; do not fill them with invented values.
- **Word and Excel.** Any `.docx` or `.xlsm` reported as `FAIL` or `UNVERIFIED` must be
  regenerated or fixed before review continues.
- **OSCAL.** The validator checks only the root element, the version string, and counts. Schema
  validation needs NIST's OSCAL tooling.
- **STIGs.** The list of applicable DISA STIG/SRG benchmarks tells the team which `.ckl`
  checklists to complete in STIG Viewer. The scripts do not complete them.
- **12 ATC controls (engine review subset).** Evaluates the engine's 12-control Authorization to Connect (ATC) boundary review subset (`AC-17`, `AC-17(2)`, `IA-2(1)`, `IA-2(2)`, `IA-5(1)`, `IR-8`, `IR-9`, `RA-5`, `SC-7`, `SC-8`, `SC-28`, `SI-2`; informed by the DISA Cloud Connection Process Guide and mapped to NIST SP 800-53 Rev. 5, where Rev. 4 `IA-2(3)` and `IA-2(4)` were incorporated into `IA-2(1)` and `IA-2(2)`) and flags any with no implementation statement in the SCTM or SSP.
- **Semantic linter.** Findings in `ato_artifacts/semantic_linter_report.json`, such as vague
  wording ("as needed", "appropriate measures") and documents that contradict the inventory.

## Phase 4: Documents versus code

Compare `system_inventory.json` and the Terraform with each deliverable in `ato_artifacts/`:

1. **SSP** (`SSP/SSP_System_Security_Plan.md`): every bucket, key, subnet, firewall rule, and
   service account in the inventory appears. Statements for AC-17, IA-2, SC-7, SC-8, SC-28, AU-2,
   AU-6, IR-4, RA-5, and SI-2 name the actual mechanism and configuration.
2. **PPSM** (`PPSM/`): every port and protocol allowed by a firewall rule, load balancer, or
   container manifest has a row. An open port with no row is a CAT I finding.
3. **HW/SW inventory** (`HW_SW_Inventory/`): every instance, cluster, database, container image,
   and software package in the inventory is listed.
4. **POA&M** (`POAM/`): every item traces to a scanner finding, a `poam_items` entry in the config,
   an unparsed Terraform file, or an inventory rule. Planned milestones are specific and dated.
   Scanner outages are not security findings (see SKILL.md, Scanners).
5. **SCTM** (`SCTM/`): statuses and narratives are family defaults unless `SCTM_Template.yaml`
   lists the control; check them against the Terraform (see
   [subskills/sctm_skill.md](subskills/sctm_skill.md)).
6. **Policies** (`Policies_and_Procedures/`): roles and frequencies are concrete, and the
   documents agree with the SSP and the runbooks.
7. **Runbooks** (`Incident_Response_Runbooks/`): commands reference real resource names and log
   sinks; reporting timelines are verified (see [subskills/runbooks_skill.md](subskills/runbooks_skill.md)).

The per-deliverable guides in `subskills/` give more detail.

## Phase 5: Corrections and report

1. **Corrections.** Where a document disagrees with the code (a wrong key path, a missing PPSM row,
   a broken link), edit the Markdown or YAML deliverable to match the code. Do not change
   Terraform without the user's approval. Note that `generate` and `validate --fix` overwrite the
   deliverables, so hand edits are lost on the next run (the validator keeps a backup in
   `ato_artifacts_backup_<timestamp>/`). Record each correction in the report so it can be made
   again, or fixed in the template.
2. **Report.** Add a review section to `ato_artifacts/Path_to_Authorization.md`. The validator
   rewrites this file and its `.docx` on every run, so add the section after the last validator
   run. The `.docx` is not updated from hand edits.

Report layout (replace the bracketed values):

```markdown
## Assessor Review

| Item | Result |
| :--- | :--- |
| Baseline reviewed | [baseline from compliance_config.yaml] |
| CAT I findings | [count] |
| CAT II findings | [count] |
| CAT III findings | [count] |
| Plan items not implemented | [count, or "no spec.md"] |
| Applicable STIG benchmarks | [count from the validator] |

### Plan, code, and documentation

| Capability | Planned in | Implemented in | Documented in | Status |
| :--- | :--- | :--- | :--- | :--- |
| [capability] | [spec.md section] | [file.tf:resource] | [SSP control] | [ALIGNED / GAP] |

### Findings

| ID | Control | Severity | Owner role | File and line | Finding | Proposed fix |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| [ID] | [control] | [CAT] | [role] | [path:line] | [what is wrong] | [change to make] |

### Corrections made

| Date | File | Problem | Change |
| :--- | :--- | :--- | :--- |
```

## Example requests

- "Check that what we built matches spec.md."
- "Review the ATO package in `<TARGET_FOLDER>` and list the applicable DISA STIGs."
- "Compare the generated SSP and PPSM with the Terraform and report any drift."
