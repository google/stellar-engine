---
name: compliance
description: >-
  Generates draft Authorization to Operate (ATO) documents for one Stellar Engine blueprint folder from its Terraform: System Security Plan (SSP), 20 policy and procedure documents, SCTM, PPSM, HW/SW inventory, POA&M, FIPS 140-3 matrix, incident response runbooks, NIST OSCAL SSP and component definition, and a Path to Authorization report, as Markdown/Word and YAML/Excel. Checks the generated package and lists applicable DISA STIGs. Supports 11 NIST SP 800-53 Rev. 5 regimes (FedRAMP Low/Moderate/High, FISMA Low/Moderate/High, DoD IL2/IL4/IL5/IL6, CJIS); GovRAMP / StateRAMP and FedRAMP Tailored / LI-SaaS fail closed.
---
<!-- skip boilerplate check -->

# Compliance: ATO package generation

This skill drafts Risk Management Framework (RMF) authorization documents for one blueprint
folder. It reads the folder's Terraform (and any application manifests), fills the templates in
`templates/`, and writes the results to `<TARGET_FOLDER>/ato_artifacts/`. The output is a draft:
it contains `[CONFIG_REQUIRED: ...]` placeholders and human-action banners that people must
resolve before anything is submitted.

See [README.md](README.md) for the package layout and module list.

## Rules

> [!IMPORTANT]
> **Target folder.** Run the skill against exactly one target folder: a blueprint directory that
> contains Terraform (`.tf`) files, such as `blueprints/il5/bigquery/`. If the user did not name
> the folder and you cannot determine it from the conversation, stop and ask. Never guess, and
> never run the scripts against the repository root (that would write `ato_artifacts/` there).

- **Commands.** A compliance run uses only the three scripts under [Workflow](#workflow). The test
  suite is for engine developers; do not run it during a compliance run.
- **Missing target.** If the target folder does not exist or contains no `.tf` files, stop and tell
  the user. Do not search other directories or create placeholder infrastructure.
- **Configuration.** If `<TARGET_FOLDER>/compliance_config.yaml` does not exist, copy
  `config/compliance_config.yaml.example` there and ask the user to fill in the organization and
  personnel fields. Until they do, leave the `[CONFIG_REQUIRED: ...]` placeholders in place. Never
  invent names, contact details, or other organizational facts.
- **Templates.** If a file under `templates/` is missing or unreadable, stop and report it. Do not
  improvise a replacement format.
- **Errors.** If a script exits non-zero, read the error, fix the path or argument, and rerun. Do
  not retry with different flags without a reason.
- **Human-action banners.** Keep every `> [!IMPORTANT]` /
  `[WARNING: RMF TEAM / HUMAN ACTION REQUIRED]` banner in the Markdown and Word outputs. They mark
  decisions that code cannot make, such as signatures, facility details, and local procedures. If
  you add sample text (see `--fill-example-data`), prefix it with
  `[WARNING: AI-GENERATED EXAMPLE DATA - DO NOT SUBMIT AS FINAL EVIDENCE]:`.
- **No Security Command Center (SCC) inside DoD IL4/IL5 boundaries.** Do not tell users to enable
  SCC in IL4 or IL5 projects. Route audit logs and VPC flow logs through Cloud Logging sinks to the
  accredited Cybersecurity Service Provider (CSSP) or an external SIEM. The engine describes SCC
  inside an IL4/IL5 boundary only when `security_operations.allow_unaccredited_scc_in_il5` is
  `true`, which records an Authorizing Official (AO) exception. SCC is acceptable for FedRAMP,
  state and local, and commercial systems.

## Setup

Run from the repository root. Always use the skill's own virtualenv; the system `python3`
usually lacks the pinned dependencies (the scripts then fail with
`ImportError: PyYAML is a required dependency`).

```bash
python3 -m venv .gemini/skills/compliance/.venv
.gemini/skills/compliance/.venv/bin/python -m pip install --require-virtualenv \
  -r .gemini/skills/compliance/requirements.txt
```

The test suite runs on Python 3.11 in CI and has also been run on Python 3.14. `requirements.txt`
pins PyYAML, openpyxl, and python-hcl2; see its comments for why the python-hcl2 version matters.

## Workflow

```bash
PY=.gemini/skills/compliance/.venv/bin/python
$PY .gemini/skills/compliance/scripts/extract_system_data.py <TARGET_FOLDER>
$PY .gemini/skills/compliance/scripts/generate_compliance_artifacts.py <TARGET_FOLDER> \
  --policy-format=both \
  --data-format=both \
  --oscal-format=both
$PY .gemini/skills/compliance/scripts/validate_compliance_artifacts.py <TARGET_FOLDER> --fix
```

`<TARGET_FOLDER>` is required by all three scripts. It must be a real directory: a path that is or
passes through a symbolic link (for example the `blueprints/fedramp-high/*` links into
`blueprints/il5/`) is refused so outputs never land in the link destination; copy the blueprint
instead. A repository root (a folder containing `.git`) is refused too. The scripts exit 1 with a
one-line `[ERROR]` message on these and other input errors.

### 1. Extract: `extract_system_data.py`

Writes `<TARGET_FOLDER>/system_inventory.json` (the previous file, if any, is kept as
`system_inventory.json.bak`). Inputs:

- Terraform. If a plan or state JSON exists (`terraform_plan_path` / `terraform_state_path` in
  `compliance_config.yaml`, or a `tfplan.json` / `terraform.tfstate` file in the folder), the
  extractor reads it. Otherwise it parses the `.tf` files with python-hcl2 and recursively walks
  local child modules (`source = "./..."` or `"../../modules/x"`) within the enclosing git work tree
  (or `--module-root`). Remote registry modules or unparsed modules outside the work tree require
  pointing the config at `terraform show -json` output.
- Configuration: `compliance_config.yaml` and other YAML files in the folder.
- Application manifests, if present: `package.json`, `requirements.txt`, `pyproject.toml`,
  `go.mod`, `pom.xml`, `Dockerfile`, `docker-compose.yml`.
- `README.md`, `spec.md`, or `tdd.md` for the system description. None of these are required.
- Local child modules (`source = "../../modules/x"`) are read only inside the enclosing git work
  tree (or the folder given with `--module-root`, which must contain the target); symlinked
  module paths are skipped. Every module file read outside the target is listed in
  `provenance.external_module_files` of the inventory.

The extractor exits 1 when the folder has no Terraform, plan/state or application inputs, or
when none of its Terraform files can be read or parsed.

| Option | Values | Default |
| :--- | :--- | :--- |
| `target_dir` (positional) | Target blueprint folder | required |
| `--allow-terraform-plan` | Flag | disabled |
| `--allow-scanners` | Flag | disabled |
| `--module-root` | Path to module boundary directory | enclosing git work tree |

> [!WARNING]
> **Trusted Inputs Only for `--allow-terraform-plan`:** Passing `--allow-terraform-plan` permits running
> `terraform plan` or `terraform show -json`. Running `terraform plan` executes target provider plugins
> and arbitrary target Terraform code. Never pass `--allow-terraform-plan` on untrusted inputs.

By default, the extractor performs static AST extraction and does not execute `terraform plan`, Syft, or
Trivy unless explicitly enabled via `--allow-terraform-plan` and `--allow-scanners`.
Rerun the extractor after every Terraform change: the other two scripts read the saved inventory.

### 2. Generate: `generate_compliance_artifacts.py`

Writes the deliverables listed below into `<TARGET_FOLDER>/ato_artifacts/`, overwriting files
from earlier runs. Review `compliance_config.yaml` first.

| Option | Values | Default |
| :--- | :--- | :--- |
| `target_dir` (positional) | Target folder | required |
| `--policy-format` | `both`, `markdown`, `docx` | `export_preferences.policy_formats` in the config, else `both` |
| `--data-format` | `both`, `yaml`, `excel` | `export_preferences.structured_data_formats`, else `both` |
| `--oscal-format` | `both`, `json`, `yaml`, `none` | `export_preferences.oscal_formats`, else `both` |
| `--oscal-version` | An OSCAL release, such as `1.2.3` or `1.1.0` | `1.2.3` |
| `--run-scanners` | Flag | disabled |
| `--scanners` | Comma-separated scanner list (`checkov,semgrep,trivy`) | `checkov,semgrep` |
| `--semgrep-config` | Local path or `p/...` / `r/...` registry reference | Bundled offline ruleset |

The number of files depends on the format flags:

- `--policy-format` applies to 28 documents (SSP, Path to Authorization, 5 scenario runbooks, FIPS matrix,
  20 policies): 28 files for `markdown` or `docx`, 56 for `both`.
- `--data-format`: `yaml` writes 5 files (HW/SW, PPSM, POA&M, SCTM, FIPS), `excel` writes 4
  workbooks (HW/SW, PPSM, POA&M, SCTM), `both` writes 9.
- `--oscal-format`: `both` writes 4 files, `json` or `yaml` 2, `none` 0.

All three set to `both` gives 69 compliance deliverables (plus 1 auxiliary `compliance_engine_audit.jsonl`
audit log emitted during generation, and 1 auxiliary `semantic_linter_report.json` emitted during
validation, yielding 71 total files under `<TARGET_FOLDER>/ato_artifacts/`). The validator's placeholder
checks read the Markdown and YAML files, so keep `markdown` or `both` if you plan to validate.

The generator ingests `*.sarif` files found in the target folder. With `--run-scanners` it also
runs Checkov and Semgrep on a private copy of the target to build POA&M items. See
[Scanners](#scanners).

### 3. Validate: `validate_compliance_artifacts.py`

Checks the package in `<TARGET_FOLDER>/ato_artifacts/` and then rewrites
`Path_to_Authorization.md` and `.docx` with its own report. The checks:

- Counts unresolved `{{ TOKEN }}` placeholders and lists `[CONFIG_REQUIRED: ...]` placeholders and
  human-action items in the Markdown and YAML files.
- Parses every YAML file.
- Opens each `.docx` and checks `word/document.xml` and its hyperlink relationships.
- Opens each workbook with openpyxl: required sheets, HW/SW component types against the
  `(U) Lists` sheet, POA&M scheduled dates, and SCTM row completeness and status/date consistency.
- Checks the OSCAL JSON files for the root element, a known `oscal-version`, and component and
  requirement counts. It does not validate against the NIST OSCAL schemas.
- Lists the DISA STIG and SRG benchmarks that apply to the discovered technologies (see
  [STIG resolution](#stig-resolution)). It does not produce `.ckl` checklists; completing them in
  STIG Viewer is a manual step.
- Compares discovered assets with the deliverables, looks for implementation statements for the 12
  NIST SP 800-53 Rev. 5 Authorization to Connect (ATC) controls in the SCTM and SSP (incorporating
  withdrawn Rev. 4 `IA-2(3)` and `IA-2(4)` into `IA-2(1)` and `IA-2(2)`), computes a qualitative
  readiness verdict (`readiness_score` is `None`), and runs a deterministic (pattern-based)
  semantic linter. The linter report is saved as `semantic_linter_report.json`.

Read the summary it prints and the rewritten `Path_to_Authorization.md`; they list the findings.

| Option | Effect |
| :--- | :--- |
| `--fix` | Copies `ato_artifacts/` to `ato_artifacts_backup_<timestamp>/`, then reruns the generator from the existing `system_inventory.json`. This overwrites manual edits in the deliverables. It does not rerun the extractor. |
| `--policy-format=`, `--data-format=`, `--oscal-format=`, `--oscal-version=` | Formats passed to the generator by `--fix`. Without them it uses the config's `export_preferences`, else `both`. |
| `--run-scanners` | With `--fix`: runs live security scanners (Checkov, Semgrep) on a sanitized private copy of target. |
| `--fill-example-data` | Relabels each remaining `[CONFIG_REQUIRED: ...]` in the Markdown and YAML files as `[EXAMPLE_DATA_REQUIRED: ...]` for an agent to fill with labeled sample text. It writes no sample values and does not change `.docx` or `.xlsm` files. |
| `--no-fill-example-data` | Leaves placeholders as they are (the default). Without either flag the validator asks only in an interactive terminal; agent shells and CI proceed without example data. |
| `--update-stigs` | Pulls STIG versions from the configured catalog source. Without a catalog source it changes nothing. |
| `--stigs-mode=auto\|online\|offline` | `offline` never contacts a catalog source; `online` pulls on every run; `auto` (default) pulls only with `--update-stigs`. |
| `--stigs-catalog=SOURCE` | Catalog source: an `https://` URL on `cyber.mil`, `disa.mil`, `defense.gov`, or `nist.gov`, or a JSON/YAML file inside the target folder. Used only when a pull happens. |
| `--no-linter`, `--no-linter-strict` | Skip the semantic linter, or run it in non-strict mode. |

Examples (append to the `$PY .../validate_compliance_artifacts.py <TARGET_FOLDER>` command):

```bash
--fix --no-fill-example-data                          # regenerate and audit, no prompt
--fix --update-stigs --stigs-catalog=<SOURCE>         # also refresh STIG versions
--stigs-mode=offline                                  # audit only, never contact a catalog
```

### STIG resolution

Each applicable benchmark's version comes from the first of:

1. `disa_stigs.version_overrides` in `compliance_config.yaml`.
2. `<TARGET_FOLDER>/ato_artifacts/.stig_cache.json`, written when a catalog pull succeeds.
3. `config/stig_catalog.json`, shipped with the skill.

`disa_stigs.custom_checklists` adds benchmarks to the list. Remote catalog fetches use HTTPS only,
refuse redirects, retry up to 3 times with short timeouts, and fall back to the local catalog on
failure. The report links each benchmark to STIG Viewer (https://www.stigviewer.com/stigs) and the
DoD Cyber Exchange.

## Deliverables

Paths are relative to `<TARGET_FOLDER>/ato_artifacts/`. Which renditions appear depends on the
format flags.

| Deliverable | Template | Output |
| :--- | :--- | :--- |
| System Security Plan | `templates/ssp/SSP_IL5_Template.md` for `DoD IL2`, `DoD IL4`, `DoD IL5`, and `DoD IL6`; `templates/ssp/SSP_FedRAMP_High_Template.md` for `FedRAMP Low`, `FedRAMP Moderate`, `FedRAMP High`, `FISMA Low`, `FISMA Moderate`, `FISMA High`, and `CJIS` (filtered to the selected baseline in `config/baselines/`) | `SSP/SSP_System_Security_Plan.md`, `.docx` |
| OSCAL SSP and component definition | Built by `src/compliance_engine/oscal_generator.py` | `OSCAL_SSP/system_security_plan.oscal.json`, `.yaml`; `OSCAL_SSP/component_definition.oscal.json`, `.yaml` |
| 20 policy and procedure documents (AC, AT, AU, CA, CM, CP, IA, IR, MA, MP, PE, PL, PM, PS, PT, RA, SA, SC, SI, SR) | `templates/policies/*.md` | `Policies_and_Procedures/<template name>.md`, `.docx` |
| Security Control Traceability Matrix (SCTM) | `templates/sctm/ControlInfoExport_Template.xlsm`, `SCTM_Template.yaml` | `SCTM/SCTM_Burndown_Matrix.xlsm`, `.yaml` |
| Ports, Protocols, and Services Matrix (PPSM) | `templates/ppsm/PPSMBoundariesInformationExport_Template.xlsm` (YAML built directly by `hardware_records.py`) | `PPSM/PPSM_Ports_Protocols_Services.xlsm`, `.yaml` |
| Hardware/software inventory | `templates/hwsw/HWSWList_Template.xlsm` (YAML built directly by `hardware_records.py`) | `HW_SW_Inventory/Hardware_Software_Inventory.xlsm`, `.yaml` |
| Plan of Action and Milestones (POA&M) | `templates/poam/POAM_Export_Template.xlsm` (YAML built directly by `generate_compliance_artifacts.py`) | `POAM/Plan_of_Action_and_Milestones.xlsm`, `.yaml` |
| FIPS 140-3 cryptographic matrix | `templates/fips/FIPS_Cryptographic_Matrix_Template.md`, `.yaml` | `FIPS_Cryptography/FIPS_Cryptographic_Matrix.md`, `.docx`, `.yaml` |
| Incident response runbooks (5 scenario runbooks; `Incident_Response_Runbook_Template.md` is reference-only) | `templates/runbooks/IR_*.md` | `Incident_Response_Runbooks/<template name>.md`, `.docx` |
| Path to Authorization | `templates/pta/Path_to_Authorization_Template.md` (the validator replaces it with its report) | `Path_to_Authorization.md`, `.docx` |

Notes:

- Supported regimes (from vendored normalized baselines in `config/baselines/`): `FedRAMP Low` (156 controls), `FedRAMP Moderate` (323), `FedRAMP High` (410), `FISMA Low` (149), `FISMA Moderate` (287), `FISMA High` (370), `DoD IL2` (323 = FedRAMP Moderate + 0 Table D-1 additions), `DoD IL4` (334 = FedRAMP Moderate + 11 DISA CSP SRG V1R7 Table D-1 additions), `DoD IL5` (624 = FedRAMP High + DISA CSP SRG V1R7 Table D-1 IL5 + CNSSI 1253 HHx/Privacy), `DoD IL6` (627 = DoD IL5 + DISA CSP SRG V1R7 Table D-1 IL6 classified additions `MA-5(2..4)` with classified enclave `[CONFIG_REQUIRED]` inheritance markers), and `CJIS` (323 = NIST SP 800-53B / FedRAMP Moderate harmonized baseline + FBI CJIS Security Policy v5.9.4 / v6.0 parameter overrides).
- Unsupported regimes (`GovRAMP` / `StateRAMP` and `FedRAMP Tailored / LI-SaaS`, plus bare/unconfigured strings) fail closed (`exit 1`) before writing any files.
- SCTM: the generator fills each control row of the `Template` sheet (row 7 onward) in place. The
  status, designation, test method, and narrative come from `SCTM_Template.yaml` when it lists the
  control, and otherwise from defaults per control family. They are not derived control by
  control from Terraform, so review every row.
- PPSM: one row per enabled Google API and per Terraform firewall rule, in the template's
  20-column layout.
- POA&M: 41 columns per item. Items come from `poam_items` in the config, Checkov and Semgrep
  results (with `--run-scanners`), SARIF files in the target folder, Terraform files the parser could not read, and rules that test the
  inventory (for example, an instance with a public IP). With none of these, the POA&M is empty.
- OSCAL: `metadata.oscal-version` is `1.2.3` unless `--oscal-version` says otherwise; the document
  structure does not change with the version. UUIDs are derived from SHA-256 of stable names, so
  they do not change between runs. Implemented requirements cover a fixed set of controls in the
  AC, AU, CM, IA, MP, RA, SA, SC, and SI families. Validate with NIST's OSCAL tooling before
  submitting.
- Runbooks follow NIST SP 800-61 (Rev. 3, April 2025, replaced Rev. 2). Check the reporting
  timelines and recipients in each runbook against the authority that applies to the system.
- Other files: `compliance_engine_audit.jsonl` (an audit log with a SHA-256 hash chain) and, after
  validation, `semantic_linter_report.json`.

## Reviewing the output

After the scripts run, review the drafts with these guides. Each one says what the generator
produces and what to check against the Terraform and `system_inventory.json`.

- [validate_skill.md](validate_skill.md): whole-package review across intent (`spec.md`, if
  present), code, and documentation.
- [subskills/ssp_skill.md](subskills/ssp_skill.md): SSP.
- [subskills/policies_skill.md](subskills/policies_skill.md): the 20 policy documents.
- [subskills/runbooks_skill.md](subskills/runbooks_skill.md): incident response runbooks.
- [subskills/sctm_skill.md](subskills/sctm_skill.md): SCTM.
- [subskills/poam_skill.md](subskills/poam_skill.md): POA&M.
- [subskills/hwsw_skill.md](subskills/hwsw_skill.md): HW/SW inventory.
- [subskills/ppsm_skill.md](subskills/ppsm_skill.md): PPSM.
- [subskills/pta_skill.md](subskills/pta_skill.md): Path to Authorization report.

When you correct a deliverable by hand, remember that `validate --fix` and every later `generate`
run overwrite it (the validator keeps a backup copy).

## Scanners

- **Live scanners are off by default.** Pass `--run-scanners` to `generate_compliance_artifacts.py`
  (or `validate_compliance_artifacts.py --fix --run-scanners`) to run Checkov and Semgrep;
  `--scanners checkov,semgrep,trivy` picks a subset. `COMPLIANCE_DISABLE_LIVE_SCANNERS=1` (or
  `true`/`yes`/`on`) always disables them. The target's `compliance_config.yaml` and
  `system_inventory.json` cannot enable scanners or choose what is scanned: their
  `security_scanners.enabled` / `run_*` keys and `workspace_path` are ignored.
- **Isolation.** Scanners never see the target folder itself. They run on a private temporary
  copy that contains only Terraform/HCL, YAML/JSON manifests, Dockerfiles and source files; dotfiles
  and dot-directories (`.checkov.yaml`, `.semgrepignore`, `.git`), auto-discovered scanner
  configuration files (`checkov.yaml`, `trivy.yaml`, `semgrep.yml`) and symlinks are left out.
  Each scanner runs with an empty `HOME` and working directory; Checkov gets an explicit
  operator config file. Finding paths are reported relative to the target.
- **Semgrep ruleset.** By default, Semgrep uses the bundled offline ruleset
  `config/semgrep_rules/public_sector_baseline.yaml` and always runs with `--metrics=off`.
  The operator can specify an alternative ruleset with `--semgrep-config <path-or-ref>` or the
  `COMPLIANCE_SEMGREP_CONFIG` environment variable. `--semgrep-config` accepts local in-boundary paths
  within the target directory or bundled rules directory, or registry references (`p/...`, `r/...`)
  when online. Remote URLs (`http://`, `https://`, `file://`) are strictly rejected.
  Findings map to NIST SP 800-53 controls through `map_cwe_to_nist()`.
- **Scanner failures.** If a configured local ruleset does not exist or a scanner fails, the scan
  is recorded as a CA-2/RA-5 coverage gap. These records stay out of the POA&M unless
  `security_scanners.include_scanner_failures_in_poam` is `true`; check the log for
  `Scanner outage detected`.
- **Caching.** Within one process, raw scanner output is reused while the target folder is
  unchanged. `COMPLIANCE_DISABLE_SCAN_CACHE=1` turns this off.

## Environment variables

The engine recognizes the following environment variables for operator configuration, security isolation, and resource budgeting:

| Environment Variable | Description |
| :--- | :--- |
| `COMPLIANCE_OFFLINE` | When set (`1`, `true`, `yes`), forces strict offline operation, disabling remote STIG catalog updates and remote network calls. |
| `SEMGREP_OFFLINE` | When set (`1`, `true`, `yes`), disables Semgrep online registry lookups. |
| `COMPLIANCE_DISABLE_LIVE_SCANNERS` | Master kill switch (`1`, `true`, `yes`, `on`) that unconditionally disables all live security scanners (Checkov, Semgrep, Trivy). |
| `COMPLIANCE_ALLOW_LIVE_CLOUD_TELEMETRY` | When set (`1`, `true`, `yes`), permits querying live Google Cloud Security Command Center (SCC) findings. |
| `COMPLIANCE_AUDIT_HMAC_KEY` | Optional secret key used for HMAC SHA-256 tamper-evident signing of audit log entries in `compliance_engine_audit.jsonl`. |
| `COMPLIANCE_SEMGREP_CONFIG` | Operator-side ruleset override for Semgrep SAST scans (local path or `p/...`, `r/...` registry reference; URLs rejected). |
| `COMPLIANCE_DISABLE_SCAN_CACHE` | When set (`1`, `true`, `yes`), disables in-process caching of scanner outputs. |
| `COMPLIANCE_STRICT_DEPS` | When set (`1`, `true`, `yes`), enforces strict supply chain isolation: never extends `sys.path` with foreign or borrowed virtualenv packages. |
| `COMPLIANCE_ALLOW_BORROWED_DEPS` | When set (`1`), allows fallback searching of external virtualenvs if PyYAML is missing. |
| `COMPLIANCE_SITE_PACKAGES` | Colon-separated list of additional site-packages directory paths to load. |
| `COMPLIANCE_MAX_HCL_BYTES` | Maximum byte size limit for individual Terraform HCL files (default: 10 MB). |
| `COMPLIANCE_MAX_HCL_DEPTH` | Maximum AST recursion depth for HCL parsing (default: 100). |
| `COMPLIANCE_MAX_HCL_TOKENS` | Maximum token count limit for HCL lexing (default: 500,000). |
| `COMPLIANCE_MAX_XML_BYTES` | Maximum byte size limit for XML parsing (default: 20 MB). |
| `COMPLIANCE_MAX_XML_DEPTH` | Maximum element nesting depth for XML parsing (default: 50). |
| `COMPLIANCE_MAX_XML_ELEMENTS` | Maximum element count limit for XML parsing (default: 100,000). |
| `{TOOL}_PATH` / `{TOOL}_BIN` / `{TOOL}_BINARY` | Overrides binary path for tools (where `{TOOL}` is `CHECKOV`, `SEMGREP`, `TRIVY`, `SYFT`, `TERRAFORM`). |

## Dependencies and parsers

- The engine imports only from the active interpreter (plus any directories listed in
  `COMPLIANCE_SITE_PACKAGES`). It does not borrow packages from other tools' virtualenvs unless
  `COMPLIANCE_ALLOW_BORROWED_DEPS=1` is set and PyYAML is missing; when it does, it logs a
  `Supply-chain notice` warning. Setting `COMPLIANCE_STRICT_DEPS=1` disables both
  `COMPLIANCE_SITE_PACKAGES` and `COMPLIANCE_ALLOW_BORROWED_DEPS` so the engine fails closed if any
  required dependency is missing from the active interpreter.
- XML is parsed only through `src/compliance_engine/safe_xml.py` and HCL only through
  `src/compliance_engine/hcl_parser.py`. Each uses the upstream library (`defusedxml`,
  `python-hcl2`) when installed and an in-repo parser otherwise. `hcl_parser.py` accepts a
  python-hcl2 backend only if a canary document parses to the expected shape; it rejects
  python-hcl2 8.x and checkov's `bc-python-hcl2` fork with a warning. Do not import
  `xml.etree.ElementTree` or `hcl2` directly, and do not add a module named after a PyPI
  distribution (it would shadow the real package).
- openpyxl is needed only for the `.xlsm` workbooks; without it the generator logs a warning and
  skips them.

## Engine development

> [!CAUTION]
> For developers changing the engine (`src/compliance_engine/`), not for compliance runs.

```bash
.gemini/skills/compliance/.venv/bin/python .gemini/skills/compliance/scripts/run_tests.py
```

`run_tests.py` CLI options:
- `-v`, `--verbose`: Run tests with verbose output (default: verbose).
- `-q`, `--quiet`: Run tests with quiet output.
- `-f`, `--failfast`: Stop on first failure or error.
- `-k PATTERN`: Run only tests matching `PATTERN` substring.
- `tests` (positional): Optional test module, class, or method selectors (e.g. `tests.test_compliance_engine`, `tests/test_regime_baselines.py`).
- `-h`, `--help`: Show CLI help and options.

`run_tests.py` discovers every `tests/test_*.py` module and runs them locally (supported on
Python 3.11 and 3.13). When changing the engine:

1. Keep the suite passing and add a test for each bug fix.
2. In `src/compliance_engine/excel_hydrator.py`, keep `keep_vba=True` and the workbooks' lookup
   sheets.
3. After changing `src/compliance_engine/docx_generator.py`, open a generated `.docx` and rerun the
   validator's DOCX checks.

## Reference

| Item | Path |
| :--- | :--- |
| Example configuration | [config/compliance_config.yaml.example](config/compliance_config.yaml.example) |
| GCP service catalog (service to control family mappings) | [config/gcp_service_catalog.yaml](config/gcp_service_catalog.yaml) |
| STIG catalog | [config/stig_catalog.json](config/stig_catalog.json) |
| Bundled Semgrep rules | [config/semgrep_rules/public_sector_baseline.yaml](config/semgrep_rules/public_sector_baseline.yaml) |
| Workbook template provenance | [templates/PROVENANCE.md](templates/PROVENANCE.md) |
| Engine package | `src/compliance_engine/` |
| CLI entry points | `scripts/extract_system_data.py`, `scripts/generate_compliance_artifacts.py`, `scripts/validate_compliance_artifacts.py` |
| Test runner | `scripts/run_tests.py` |

Report problems with this skill in the repository issue tracker.
