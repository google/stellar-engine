---
name: compliance
description: >-
  Automate NIST SP 800-53 Rev. 5, FedRAMP High/Moderate, DoD IL4/IL5/IL6, StateRAMP, CJIS, and FISMA Authorization to Operate (ATO) packages. Extracts facts from Terraform (.tf) and code, hydrating templates to generate dual-format (Markdown/DOCX, YAML/Excel) RMF deliverables: System Security Plan (SSP), 20 Policy Manuals, Security Control Traceability Matrix (SCTM), Ports Protocols & Services Matrix (PPSM), HW/SW Inventory, Plan of Action & Milestones (POA&M), FIPS 140-3 Matrix, NIST OSCAL schemas, IR Runbooks, and Path to Authorization (PTA) Strategy. Validates integrity, audits OpenXML, maps DISA STIGs, and verifies 14 ATC connection controls. Use when provisioning, auditing, or updating RMF/FedRAMP/DoD ATO packages, auditing controls against Terraform, or preparing Google Cloud compliance docs.
---

# Compliance & RMF Authorization Package Provisioning

Automate the generation, verification, and maintenance of formal Risk
Management Framework (RMF), FedRAMP (Moderate/High), DoD Cloud Computing SRG (IL4/IL5/IL6),
StateRAMP, and CJIS **Authorization to Operate (ATO) Packages** using the `compliance` automation engine.
Extract live architecture facts directly from Terraform blueprints and application
codebases, hydrate authoritative templates, and produce audit-ready deliverables
in both human-readable text (`.md`, `.yaml`) and executive binary (`.docx`, `.xlsm`)
formats inside `<TARGET_FOLDER>/ato_artifacts/`.

> [!IMPORTANT]
>
> **MANDATORY: Target Folder Context & Isolation**
> Unlike global or repository-wide tools, **Compliance & ATO generation operates
> strictly within a designated target folder** (`<TARGET_FOLDER>/`). All architecture
> blueprints, Terraform definitions (`terraform/`), design specifications (`spec.md`),
> and variables (`variables.yaml` or `compliance_config.yaml`) reside within this folder.
>
> **Guards against guessing**: If the user request does not specify a target folder
> and you cannot determine it from the active workspace or conversation context (i.e.,
> if `<TARGET_FOLDER>/spec.md` or `<TARGET_FOLDER>/variables.yaml` cannot be located),
> **you MUST STOP and ask the user for the correct target folder before running any commands.**
>
> You are **strictly forbidden** from guessing the target directory based on folder names
> in unrelated paths or generating `ato_artifacts/` loose directly into the repository root.
> If the target directory is undetermined, you must stop and ask. Do NOT attempt to run any
> compliance extraction, generation, or validation scripts without the target folder path.

> [!NOTE]
>
> **Operational Workflow vs. Framework Testing**:
> When provisioning or validating compliance deliverables for a target workspace (`<TARGET_FOLDER>`), execute the three operational scripts:
> 1. `extract_system_data.py <TARGET_FOLDER>`
> 2. `generate_compliance_artifacts.py <TARGET_FOLDER>`
> 3. `validate_compliance_artifacts.py <TARGET_FOLDER> --fix`
>
> The test suite (`run_tests.py` or `test_compliance_engine.py`) is reserved for framework developers modifying engine source code in `.gemini/skills/compliance/src/compliance_engine/`.

> [!TIP]
>
> **Multi-Regime Baseline Selection & Telemetry Routing**:
> The compliance engine dynamically adapts to any U.S. Public Sector accreditation
> baseline configured in `<TARGET_FOLDER>/compliance_config.yaml`:
>
> | Customer Sector | Target Impact Baselines | GRC Governance Portals | Identity & Credential Standards | Key Overlays & Telemetry Routing |
> | :--- | :--- | :--- | :--- | :--- |
> | **Department of Defense (DoD)** | DoD IL4, IL5, IL6 / FedRAMP High | eMASS / CRAMS | CAC / DoD PKI Authentication | DoD CC SRG, DISA STIGs, 14 ATC Controls, DISA / Service CSSP *(No native SCC in-boundary)* |
> | **Federal Civilian Agencies** | FedRAMP High / Moderate, FISMA High | CSAM / FedRAMP PMO Repository | PIV / FIPS 140-3 Hardware Token | FISMA, OMB Circular A-130, NIST SP 800-53 R5, TIC 3.0, Native SCC Enterprise |
> | **State, Local & Education (SLED)** | StateRAMP High/Mod, CJIS, HIPAA | ServiceNow GRC / Archer / GovCloud GRC | Enterprise MFA / FIPS 140-3 Token | StateRAMP, FBI CJIS Security Policy 5.9, IRS Pub 1075, Native SCC Enterprise |
> | **National Security & IC** | ICD 503 / Top Secret / Secret | Xacta 360 / Enterprise GRC | High-Assurance PKI / Hardware MFA | CNSSI 1253, ICD 503, FIPS 140-3 CMEK Encryption |
>
> **Critical Telemetry Rule for DoD IL4/IL5**: Native Google Security Command Center
> (SCC) is **NOT currently accredited for DoD IL4 or DoD IL5 production boundaries**.
> Never instruct users to enable SCC inside IL4/IL5 projects. Real-time audit logs and VPC
> flow logs MUST be exported via Cloud Logging sinks to an accredited external Cloud Cyber
> Security Service Provider (CSSP) (e.g. DISA, service CSSP) or external GovCloud SIEM. Native
> SCC is fully supported in FedRAMP High, commercial, and SLED environments.

### Robust Error Handling & Terminal Conditions

To avoid useless search loops and minimize turns, follow these strict rules when
resources or inputs are missing:

*   **Target Directory Not Found**: If the specified target directory does not exist or
    contains no infrastructure definitions (`.tf` files or `spec.md`), you **MUST STOP**
    immediately and report this to the user. Do **NOT** attempt to search other directories
    or invent mock infrastructure.
*   **Missing Configuration (`compliance_config.yaml`)**: If `<TARGET_FOLDER>/compliance_config.yaml`
    is missing, copy `config/compliance_config.yaml.example` to the target directory and prompt
    the user to verify key personnel and organizational metadata. If personnel names are not
    yet known, proceed with standard `[CONFIG_REQUIRED: ...]` tags—never invent fake personnel names.
*   **Missing Authoritative Template**: If an authoritative template in `.gemini/skills/compliance/templates/`
    is missing or corrupt, you **MUST STOP** immediately and report the missing file. Do **NOT**
    invent ad-hoc or unstructured compliance formats.
*   **Missing Python Dependencies**: Install the pinned dependency set rather than individual
    packages, so the version actually exercised by the test suite is the one deployed:
    ```bash
    python3 -m venv .gemini/skills/compliance/.venv && source .gemini/skills/compliance/.venv/bin/activate
    pip install -r .gemini/skills/compliance/requirements.txt
    ```
    Markdown generation requires zero pip dependencies. `PyYAML` is required for configuration
    parsing; `openpyxl` is required only for `.xlsm` hydration, and its absence degrades to
    YAML-only structured output with an explicit warning.
*   **Supply-Chain Warnings**: If the engine logs a `Supply-chain` warning at startup, it has
    located a required dependency inside an unrelated tool's virtualenv (commonly `checkov`'s)
    rather than in the active environment. The run will proceed, but the dependency is not
    under your control. Resolve it by installing `requirements.txt` as above. For accredited
    deployments set `COMPLIANCE_STRICT_DEPS=1` to disable all fallback discovery and fail
    closed instead of silently borrowing another tool's packages.
*   **Hardened Parser Facades**: XML is parsed exclusively through `src/compliance_engine/safe_xml.py` and
    HCL through `src/compliance_engine/hcl_parser.py`. Both prefer the genuine upstream libraries
    (`defusedxml`, `python-hcl2`) when installed and fall back to hardened in-repo
    implementations otherwise. Never import `xml.etree.ElementTree` or `hcl2` directly, and
    never add a module named after a PyPI distribution — such a module would shadow the real
    package everywhere.
*   **Application SAST Ruleset**: Semgrep runs using Semgrep's managed `auto` ruleset by default
    (`security_scanners.semgrep_config: "auto"`), pulling managed rulesets directly from the Semgrep registry.
    Operators can also supply a custom ruleset or registry reference, or use the curated offline baseline bundled at
    `config/semgrep_rules/public_sector_baseline.yaml`. Every rule routes through `map_cwe_to_nist()` into a POA&M item
    with the correct NIST SP 800-53 control. When running with `auto`, metrics restrictions are omitted so Semgrep can
    resolve its managed configuration. The compliance engine evaluates static code and infrastructure definitions (not
    application runtime data), and operates in standard connected environments alongside LLM integrations without requiring
    air-gap isolation. If a configured custom local ruleset path cannot be resolved, the engine fails closed and files
    a CA-2/RA-5 **assessment coverage gap** rather than reporting a clean codebase.
*   **Scanner Result Memoization**: A single `generate` derives POA&M findings three times (POA&M
    sheet, SCTM sheet, POA&M YAML). Only the **raw scanner output** is memoized, keyed on a
    fingerprint of the workspace tree; derivation still runs per caller because callers
    deliberately use different effective dates. The memo fails open — an unreliable fingerprint
    simply re-runs the scan. Set `COMPLIANCE_DISABLE_SCAN_CACHE=1` to disable it entirely.
*   **No Polling/Retrying**: If a script exits with a non-zero exit code or terminal error, do not
    retry blindly with different flags unless you have a verified reason. Inspect the error log,
    correct the path or argument, and re-execute.

## Identifying metadata

Before executing compliance operations, verify the target environment context:

*   **Identify the target folder**: Look for `<TARGET_FOLDER>/variables.yaml`,
    `<TARGET_FOLDER>/spec.md`, and `<TARGET_FOLDER>/terraform/`.
*   **Identify the compliance configuration**: Inspect `<TARGET_FOLDER>/compliance_config.yaml`
    to read the target impact level (`IL5`, `FedRAMP-High`, `StateRAMP`), organization name,
    and assigned personnel roles (Authorizing Official, System Owner, ISSM, ISSO).
*   **Identify active infrastructure assets**: Inspect `<TARGET_FOLDER>/terraform/` or
    run `extract_system_data.py <TARGET_FOLDER>` to generate `<TARGET_FOLDER>/system_inventory.json`.
*   **Identify existing accreditation packages**: Check `<TARGET_FOLDER>/ato_artifacts/`
    to determine if artifacts already exist (for update/validation) or if initial provisioning is needed.

## Quick Start

Execute the complete end-to-end compliance workflow using the automated CLI scripts.
*(Note: These 3 operational steps are the ONLY commands executed for target workspaces. Do NOT run internal test scripts.)*

```bash
# Step 0: Initialize governance configuration (if not already present)
cp .gemini/skills/compliance/config/compliance_config.yaml.example <TARGET_FOLDER>/compliance_config.yaml

# Step 1: Extract live architecture and application facts into system_inventory.json
python3 .gemini/skills/compliance/scripts/extract_system_data.py <TARGET_FOLDER>

# Step 2: Generate full dual-format ATO package (Markdown, Word .docx, YAML, Excel .xlsm)
python3 .gemini/skills/compliance/scripts/generate_compliance_artifacts.py <TARGET_FOLDER> --policy-format=both --data-format=both

# Step 3: Audit deliverables, verify OpenXML integrity, analyze STIGs, and compile master PTA roadmap
python3 .gemini/skills/compliance/scripts/validate_compliance_artifacts.py <TARGET_FOLDER> --fix
```

---

## 4-Step Provisioning & Validation Methodology

### Step 1: Technical Discovery & Variable Extraction (`extract_system_data.py`)

Scan declarative Terraform code, YAML blueprints, and application runtime descriptors
to extract live system parameters into a unified `<TARGET_FOLDER>/system_inventory.json`:

```bash
python3 .gemini/skills/compliance/scripts/extract_system_data.py <TARGET_FOLDER>
```

#### What is Discovered
1. **Cloud Infrastructure Components**:
   - Active GCP APIs (`*.googleapis.com`), Assured Workloads compliance baselines.
   - VPC Networks, Subnet CIDRs, Firewall Rules, Private Service Connect endpoints.
   - GKE Clusters, Cloud SQL / AlloyDB Databases, BigQuery Datasets.
   - Cloud KMS CMEK Key Rings, Crypto Keys, and Automated Rotation Cycles.
   - Cloud Storage Buckets (CMEK status, retention policies), Compute Engine VMs.
   - Cloud IAM Custom Roles, Service Accounts, Separation-of-Duties Matrix.
   - Cloud Logging Sinks, Log Buckets, and Aggregated Export Filters.
2. **Application Services & Runtimes**:
   - Application descriptors: Node.js (`package.json`), Python (`requirements.txt`, `pyproject.toml`),
     Go (`go.mod`), and Java (`pom.xml`).
   - Software packages, frameworks, database connectors, and cloud client SDKs.
   - Container Base Images (`Dockerfile`, `docker-compose.yml`), exposed ingress ports,
     and Kubernetes service endpoints mapped directly to the PPSM.

> [!NOTE]
> `system_inventory.json` serves as the single source of technical truth for all downstream
> artifact hydration and validation scripts. Run this command whenever `.tf` infrastructure
> code or application dependencies change.

---

### Step 2: Full Package Provisioning & Dual-Format Hydration (`generate_compliance_artifacts.py`)

> [!CAUTION]
> This is a write action that publishes up to 67 compliance deliverables into
> `<TARGET_FOLDER>/ato_artifacts/`. Ensure that `<TARGET_FOLDER>/compliance_config.yaml`
> has been reviewed before running.

```bash
# Provision complete dual-format package (default)
python3 .gemini/skills/compliance/scripts/generate_compliance_artifacts.py <TARGET_FOLDER> --policy-format=both --data-format=both

# Provision lightweight text-only package (Markdown & YAML)
python3 .gemini/skills/compliance/scripts/generate_compliance_artifacts.py <TARGET_FOLDER> --policy-format=markdown --data-format=yaml

# Provision executive binary-only package (Word .docx & Excel .xlsm)
python3 .gemini/skills/compliance/scripts/generate_compliance_artifacts.py <TARGET_FOLDER> --policy-format=docx --data-format=excel
```

#### CLI Options
- `target_dir`: Path to the target foundation directory (e.g., `my-foundation/`).
- `--policy-format`: Export format for the 20 policy manuals and SSP (`both`, `docx`, `markdown`). Defaults to `both`.
- `--data-format`: Export format for structured data matrices (`both`, `excel`, `yaml`). Defaults to `both`.

---

### Step 3: Detailed Deliverable Specifications & Inspection Guides

The compliance engine provisions and maintains 9 core accreditation deliverables:

#### 1. System Security Plan (SSP)
*Templates*: `templates/ssp/SSP_IL5_Template.md` *(DoD)* or `templates/ssp/SSP_FedRAMP_High_Template.md` *(Federal)*
*Outputs*:
- `<TARGET_FOLDER>/ato_artifacts/SSP/SSP_System_Security_Plan.md`
- `<TARGET_FOLDER>/ato_artifacts/SSP/SSP_System_Security_Plan.docx`
*Scope*: Comprehensive NIST SP 800-53 Rev. 5 system boundary, hardware/software specifications,
live role assignments, and dynamic IAM Separation-of-Duties table.

#### 1b. NIST OSCAL Machine-Readable Packages (SSP & Component Definitions)
*Engine*: `src/compliance_engine/oscal_generator.py`
*Outputs*:
- `<TARGET_FOLDER>/ato_artifacts/OSCAL_SSP/system_security_plan.oscal.json`
- `<TARGET_FOLDER>/ato_artifacts/OSCAL_SSP/system_security_plan.oscal.yaml`
- `<TARGET_FOLDER>/ato_artifacts/OSCAL_SSP/component_definition.oscal.json`
- `<TARGET_FOLDER>/ato_artifacts/OSCAL_SSP/component_definition.oscal.yaml`
*Scope*: Machine-readable NIST OSCAL System Security Plan (SSP) and Component Definitions conforming to
NIST OSCAL 1.2.3 (or 1.1.0) mapping live GCP cloud infrastructure and application components to NIST SP 800-53 Rev. 5 controls (AC, AU, CM, IA, MP, RA, SA, SC, SI)
with deterministic RFC 4122 UUIDv5 tracking, ready for direct FedRAMP automated validation and eMASS ingest.

#### 2. 20 NIST SP 800-53 Rev. 5 Policy & Procedure Manuals
*Templates*: `templates/policies/[Family]_Policy_and_Procedures.md`
*Outputs*:
- `<TARGET_FOLDER>/ato_artifacts/Policies_and_Procedures/[Family]_Policy_and_Procedures.md`
- `<TARGET_FOLDER>/ato_artifacts/Policies_and_Procedures/[Family]_Policy_and_Procedures.docx`
*Scope*: All 20 control families (AC, AT, AU, CA, CM, CP, IA, IR, MA, MP, PE, PL, PM, PS, PT, RA, SA, SC, SI, SR).
Features formatted executive document control blocks, defense-grade typography, styled tables,
and highlighted human action alerts.

#### 3. Security Control Traceability Matrix (SCTM)
*Templates*: `templates/sctm/ControlInfoExport_Template.xlsm`, `templates/sctm/SCTM_Template.yaml`
*Outputs*:
- `<TARGET_FOLDER>/ato_artifacts/SCTM/SCTM_Burndown_Matrix.yaml`
- `<TARGET_FOLDER>/ato_artifacts/SCTM/SCTM_Burndown_Matrix.xlsm`
*Scope*: In-place row matching across rows 7..5,000+ while preserving pre-existing control descriptions.
Populates implementation status, common control provider, test method, and technical narratives.
Strictly validates against embedded `Data Validation` lookup sheet.

#### 4. Ports, Protocols, and Services Matrix (PPSM)
*Templates*: `templates/ppsm/PPSMBoundariesInformationExport_Template.xlsm`, `templates/ppsm/PPSM_Template.yaml`
*Outputs*:
- `<TARGET_FOLDER>/ato_artifacts/PPSM/PPSM_Ports_Protocols_Services.yaml`
- `<TARGET_FOLDER>/ato_artifacts/PPSM/PPSM_Ports_Protocols_Services.xlsm`
*Scope*: 20-column DoD / FedRAMP network boundary registry detailing TCP/UDP ports, boundary
interfaces, API domains (`*.googleapis.com`), PSC endpoints (`199.36.153.4/30`), and ingress/egress rules.
Strictly validates against embedded `Glossary` sheet.

#### 5. Hardware & Software Asset Inventory (HW/SW)
*Templates*: `templates/hwsw/HWSWList_Template.xlsm`, `templates/hwsw/HWSW_Template.yaml`
*Outputs*:
- `<TARGET_FOLDER>/ato_artifacts/HW_SW_Inventory/Hardware_Software_Inventory.yaml`
- `<TARGET_FOLDER>/ato_artifacts/HW_SW_Inventory/Hardware_Software_Inventory.xlsm`
*Scope*: Two-sheet inventory (`Hardware` and `Software`). Tracks VMs, GKE clusters, Cloud SQL,
KMS HSM modules, VPCs, active GCP APIs, and application software packages. Validates against `(U) Lists` sheet.

#### 6. Plan of Action and Milestones (POA&M)
*Templates*: `templates/poam/POAM_Export_Template.xlsm`, `templates/poam/POAM_Template.yaml`
*Outputs*:
- `<TARGET_FOLDER>/ato_artifacts/POAM/Plan_of_Action_and_Milestones.yaml`
- `<TARGET_FOLDER>/ato_artifacts/POAM/Plan_of_Action_and_Milestones.xlsm`
*Scope*: 41-column continuous monitoring burndown matrix grounded strictly in real automated security scanners (Checkov for IaC misconfigurations, Semgrep for application SAST, Trivy for CVEs, and SARIF report ingestion), user-declared punch-lists, and live IaC architectural gap detection. Clean architectures report zero open items with no synthetic filler or mock milestones.

#### 7. FIPS 140-3 Cryptographic Validation Matrix
*Templates*: `templates/fips/FIPS_Cryptographic_Matrix_Template.yaml`, `templates/fips/FIPS_Cryptographic_Matrix_Template.md`
*Outputs*:
- `<TARGET_FOLDER>/ato_artifacts/FIPS_Cryptography/FIPS_Cryptographic_Matrix.yaml`
- `<TARGET_FOLDER>/ato_artifacts/FIPS_Cryptography/FIPS_Cryptographic_Matrix.md`
- `<TARGET_FOLDER>/ato_artifacts/FIPS_Cryptography/FIPS_Cryptographic_Matrix.docx`
*Scope*: Inventory of FIPS 140-3 validated Cloud KMS CMEK key rings, NIST CMVP certificate numbers,
TLS 1.3 cipher suites, and algorithm restrictions satisfying `SC-12` and `SC-13`.

#### 8. Tactical Cloud Incident Response Runbooks (5 Workflows + Template)
*Templates*: `templates/runbooks/IR_*_Runbook.md`, `templates/runbooks/Incident_Response_Runbook_Template.md`
*Outputs*:
- `<TARGET_FOLDER>/ato_artifacts/Incident_Response_Runbooks/IR_IAM_Compromised_Credentials_Runbook.md` & `.docx`
- `<TARGET_FOLDER>/ato_artifacts/Incident_Response_Runbooks/IR_Compute_Resource_Compromise_Runbook.md` & `.docx`
- `<TARGET_FOLDER>/ato_artifacts/Incident_Response_Runbooks/IR_KMS_CMEK_Compromise_Runbook.md` & `.docx`
- `<TARGET_FOLDER>/ato_artifacts/Incident_Response_Runbooks/IR_Network_Intrusion_Runbook.md` & `.docx`
- `<TARGET_FOLDER>/ato_artifacts/Incident_Response_Runbooks/IR_VPC_Service_Controls_Violation_Runbook.md` & `.docx`
- `<TARGET_FOLDER>/ato_artifacts/Incident_Response_Runbooks/Incident_Response_Runbook_Template.md` & `.docx`
*Scope*: Tactical cloud incident handling playbooks aligned with NIST SP 800-61 Rev. 2 and mandatory
reporting SLAs (DoD 1-hour to DC3/US-CERT, Federal 1-hour to CISA).

#### 9. Master Path to Authorization (PTA) Strategy & Executive Roadmap
*Templates*: `templates/pta/Path_to_Authorization_Template.md`
*Outputs*:
- `<TARGET_FOLDER>/ato_artifacts/Path_to_Authorization.md`
- `<TARGET_FOLDER>/ato_artifacts/Path_to_Authorization.docx`
*Scope*: Executive 6-Phase RMF execution roadmap, 14 ATC connection controls, dynamic DISA STIG mapping,
eMASS direct entry guide, sample determination memo, and Lead Assessor validation audit summary.

---

### Step 4: Package Validation, Mandatory AI Semantic Audit & DISA STIG Resolution

The compliance workflow enforces a strict separation of concerns between **Python Data Plumbing** and **AI Agent Semantic Reasoning**:

1. **Python Data Plumbing Layer (`validate_compliance_artifacts.py`)**:
   Runs fast, deterministic pre-flight checks: unzips OpenXML packages (`.docx`, `.xlsm`) to verify XML schemas and macro preservation, checks ZIP bomb protections, validates JSON schemas and AST structures, resolves dynamic DISA STIG benchmarks, and applies AST pre-filtering.
   ```bash
   # Run pre-flight structural validation, STIG discovery, and drift sync
   python3 .gemini/skills/compliance/scripts/validate_compliance_artifacts.py <TARGET_FOLDER> --fix

   # Audit package and dynamically pull active STIG versions from remote feeds/catalog:
   python3 .gemini/skills/compliance/scripts/validate_compliance_artifacts.py <TARGET_FOLDER> --fix --update-stigs

   # Audit package with custom STIG catalog source or explicit air-gap mode:
   python3 .gemini/skills/compliance/scripts/validate_compliance_artifacts.py <TARGET_FOLDER> --stigs-mode=auto --stigs-catalog=path/or/url

   # Audit package with AI-generated contextual sample data in remaining action boxes:
   python3 .gemini/skills/compliance/scripts/validate_compliance_artifacts.py <TARGET_FOLDER> --fix --fill-example-data

   # Audit package strictly retaining raw human action callouts (no sample text):
   python3 .gemini/skills/compliance/scripts/validate_compliance_artifacts.py <TARGET_FOLDER> --fix --no-fill-example-data
   ```

2. **AI Agent Semantic Reasoning Layer (`validate_skill.md`)**:
   The AI agent operationalizes the **Senior Security Control Assessor (SCA) & Public Sector Security Engineer ("Trust But Verify")** persona:
   - **Semantic Control Assessment**: Evaluates all deliverables (SSP, POA&M, 20 Policy Manuals, SCTM, PPSM) against target public sector baselines (NIST SP 800-53 Rev. 5, FedRAMP Moderate/High, DoD CC SRG IL4/IL5/IL6).
   - **Architectural Drift Detection**: Cross-references narrative claims directly against live Terraform code (`<TARGET_FOLDER>/terraform/`) and AST inventory (`system_inventory.json`):
     - Flag CAT I drift if an artifact claims CMEK encryption but Terraform lacks KMS keys or uses default Google keys.
     - Flag CAT I drift if an artifact claims zero-trust/private access but Terraform firewalls allow `0.0.0.0/0` ingress to administrative ports (22, 3389, DB).
     - Flag CAT II drift if an artifact claims dual-region failover but Terraform defines single-region resources.
     - Flag CAT II drift if an artifact claims centralized SIEM ingestion but Terraform lacks logging export sinks.
   - **Zero Tolerance for Vague Boilerplate**: Explicitly rejects ambiguous phrases lacking prescriptive technical parameters (e.g. "appropriate security measures", "as needed", "reasonable precautions", "industry standards", "strong passwords", "regularly reviewed").
   - **Zero Untailored Placeholders**: Rejects unresolved template brackets (`[assignment: ...]`, `[selection: ...]`, `{{ ... }}`, `[CONFIG_REQUIRED: ...]`).
   - **Auto-Repair & Executive Synthesis**: Auto-repairs fixable naming/protocol gaps and compiles the authoritative Lead Assessor Executive Audit & Remediation Playbook in `<TARGET_FOLDER>/ato_artifacts/Path_to_Authorization.md` and `.docx`.

3. **Specialized AI Reviewer Subskills (`subskills/*.md`)**:
   Targeted subskills in `subskills/` allow the AI agent to review Python-generated deliverables, verify fidelity against live Terraform definitions, ensure the generator didn't miss anything, and tailor domain-specific procedures with public sector expertise:
   - [`subskills/ssp_skill.md`](subskills/ssp_skill.md): Review Python-generated SSP, verify all discovered infrastructure is captured, and deepen NIST SP 800-53 control narratives.
   - [`subskills/policies_skill.md`](subskills/policies_skill.md): Review 20 policy manuals, verify mandatory NIST -1 sections, and tailor agency-specific procedures.
   - [`subskills/runbooks_skill.md`](subskills/runbooks_skill.md): Review 5 incident runbooks, verify containment CLI commands, and ensure telemetry routing (e.g. no SCC in DoD IL4/IL5).
   - [`subskills/sctm_skill.md`](subskills/sctm_skill.md): Review SCTM workbook row matching, dropdown data validation, and 14 ATC connection controls.
   - [`subskills/poam_skill.md`](subskills/poam_skill.md): Review POA&M matrix, verify grounding in real scanner findings, and check remediation timeline SLAs.
   - [`subskills/hwsw_skill.md`](subskills/hwsw_skill.md): Review hardware/software inventory sheets and verify virtual/critical asset classification.
   - [`subskills/ppsm_skill.md`](subskills/ppsm_skill.md): Review network boundary matrix, verify ingress/egress firewall rules, and check API endpoints.
   - [`subskills/pta_skill.md`](subskills/pta_skill.md): Review Path to Authorization roadmap, verify catalog of delivered artifacts, and tailor executive memos.

4. **Final Comprehensive Quality Gate (`validate_skill.md`)**:
   After artifacts are generated and reviewed, the AI agent executes [`validate_skill.md`](validate_skill.md) to **check everything together across any IaC or application stack**:
   - **Contractual Intent & Delivery Audit**: Reconciles `<TARGET_FOLDER>/spec.md` and `variables.yaml` against live code in `terraform/` and `app/` to ensure the team actually built what was promised (zero phantom omissions, zero unapproved scope creep).
   - **Deep IaC & Workload Security Gate**: Audits secret sprawl (CWE-798), least-privilege IAM, default-deny boundaries, FIPS 140-3 CMEK encryption, centralized SIEM logging, and container image/runtime hardening.
   - **Automated Data Plumbing Pre-Flight**: Runs pre-flight structural verification and STIG resolution (`validate_compliance_artifacts.py <TARGET_FOLDER> --fix`).
   - **Live Architecture Truth Reconciliation**: Conducts whole-package semantic audit, detecting cross-system architectural drift between live Terraform code and all documentation.
   - **Auto-Repair & Executive Playbook Synthesis**: Safely auto-repairs fixable documentation drift and compiles the authoritative Lead Assessor Executive Audit & Remediation Playbook in `<TARGET_FOLDER>/ato_artifacts/Path_to_Authorization.md` and `.docx`.

#### What the Validator Performs
1. **OpenXML Structural Integrity Audit**: Unzips and validates XML structure for all `.docx` and `.xlsm` deliverables.
2. **Code Drift & Parity Synchronization**: Verifies that discovered Terraform resources match entries across Markdown and Excel workbooks.
3. **Dynamic DISA STIG / SRG Version Resolver & Lifecycle Engine (`src/compliance_engine/stig_resolver.py`)**:
   - Evaluates foundational cloud mission owner baselines: DoD Cloud Computing SRG (`cloud_computing_srg`),
     IAM STIG (`identity_and_access_management_iam_srg`), KMS STIG (`key_and_certificate_management_srg`).
   - Dynamically evaluates discovered workload technologies (Ubuntu/RHEL host OS, Kubernetes GKE,
     Cloud SQL PostgreSQL/MySQL, perimeter firewalls, WAF, serverless, messaging) and lists exact DISA STIG benchmarks.
   - **Dynamic Versioning & Active Pulling**: Resolves active versions across multi-tiered channels:
     1. User overrides in `compliance_config.yaml` (`disa_stigs.version_overrides`).
     2. Custom checklists injected via `compliance_config.yaml` (`disa_stigs.custom_checklists`).
     3. Active versions pulled from remote feeds or custom catalog endpoints (`--update-stigs`).
     4. Local target cache (`<TARGET_FOLDER>/.stig_cache.json`).
     5. Centralized authoritative baseline catalog (`config/stig_catalog.json`).
   - **Air-Gap Resilient**: Strict network timeouts and safe exception handling ensure offline execution never blocks or crashes.
   - Provides direct links to [STIG Viewer](https://www.stigviewer.com/stigs) and official DoD Cyber Exchange download instructions.
4. **Complete DoD ISSM ATO Submission Checklist (10 Operational Evidence Items)**:
   - ACAS/Nessus credentialed scans (`RA-5`), DISA STIG Viewer checklists (`CM-6`), SAST/DAST/SBOM (`SA-11`),
     14 ATC Controls (`AC-17`, `IA-2`, `SC-7`), PIA DD Form 2930 (`PT-2`), Interconnection ISAs (`CA-3`),
     CSSP SLA (`CA-9`), User SAAR DD Form 2875 (`AC-2`), Tabletop TTX Reports (`CP-4`, `IR-4`),
     and Executive ATO Determination Memo (`CA-6`).
5. **14 ATC (Authorization to Connect) Critical Controls Audit**: Verifies complete implementation statements
   and zero unmitigated High/Very High residual risks for connection controls.
6. **Compiles Master Executive PTA Report**: Refreshes `<TARGET_FOLDER>/ato_artifacts/Path_to_Authorization.md`
   and `.docx` with audit metrics and role-grouped remediation cards.

---

## Retaining Human Administrative Intervention Callouts

> [!IMPORTANT]
> **MANDATORY PRESERVATION OF HUMAN ACTION BANNERS**:
> Code inspection cannot answer institutional, legal, physical facility, or executive signature decisions.
> The AI agent **MUST retain and preserve explicit callout banners** in both Markdown and Word DOCX outputs:
>
> `> [!IMPORTANT]`
> `> <mark style="background-color: #fff9c4; color: #b71c1c; font-weight: bold; padding: 2px 6px; border-radius: 4px;">⚠️ **RMF TEAM / HUMAN ACTION REQUIRED**</mark>: [Exact administrative SOP, physical building office suite number, local training tool URL, or human approval signature required]`
>
> When `--fill-example-data` is requested, wrap sample data with high-contrast disclaimer borders:
> ```html
> <mark style="background-color: #fef08a; border: 2px dashed #ca8a04; color: #854d0e; font-weight: bold; padding: 3px 8px; border-radius: 4px;">⚠️ [AI-GENERATED EXAMPLE DATA — DO NOT SUBMIT AS FINAL EVIDENCE]: Agency Service Desk Portal (Ticket #REQ-2026-991)</mark>
> ```

---

## Internal Engine Development Testing (INTERNAL DEVELOPERS ONLY)

> [!CAUTION]
> **FOR CORE COMPLIANCE ENGINE DEVELOPERS ONLY — DO NOT RUN DURING WORKSPACE COMPLIANCE RUNS**
>
> The command below runs the comprehensive automated test suite covering unit, integration, and security boundaries.
> **DO NOT run these commands when provisioning, validating, or maintaining compliance artifacts for an active user workspace.**
> There is **zero reason** for the test suite to run when someone is using the skill as intended.
> This test suite should ONLY be executed by framework developers when modifying the Python source code of the compliance engine itself (`.gemini/skills/compliance/src/compliance_engine/`).

When making changes to the compliance engine source code itself:
```bash
# Run the complete test suite via the dedicated runner
python3 .gemini/skills/compliance/scripts/run_tests.py
```

---

## Reference Material

| Reference Component | Path | Focus Area |
| :--- | :--- | :--- |
| **Governance Configuration** | [compliance_config.yaml.example](config/compliance_config.yaml.example) | Governance, personnel roles, format flags, and scanner settings |
| **GCP Service Catalog** | [gcp_service_catalog.yaml](config/gcp_service_catalog.yaml) | Cloud service classifications, NIST families, and control mappings |
| **Core Compliance Engine** | `src/compliance_engine/` | Modular package exposing public API, models, generators, and validators |
| **System Security Plan (SSP)** | `templates/ssp/` | FedRAMP High & DoD IL5 SSP starting templates (`.md`) |
| **20 Policy Manuals** | `templates/policies/` | 20 NIST SP 800-53 Rev. 5 Policy & Procedure starting templates (`.md`) |
| **SCTM Burndown Matrix** | `templates/sctm/` | SCTM template workbook (`.xlsm`) and structured YAML (`.yaml`) |
| **PPSM Boundaries Registry** | `templates/ppsm/` | PPSM template workbook (`.xlsm`) and structured YAML (`.yaml`) |
| **HW/SW Asset Inventory** | `templates/hwsw/` | Asset inventory workbook (`.xlsm`) and structured YAML (`.yaml`) |
| **POA&M Tracking Matrix** | `templates/poam/` | Continuous monitoring burndown workbook (`.xlsm`) and structured YAML |
| **Incident Response Runbooks** | `templates/runbooks/` | 5 tactical cloud IR playbooks + extensible starting template (`.md`) |
| **Path to Authorization (PTA)** | `templates/pta/` | Executive master roadmap and Authorizing Official memo template (`.md`) |
| **Discovery Entry Point** | `scripts/extract_system_data.py` | CLI entrypoint delegating to `compliance_engine.extract_system_data` |
| **Provisioning Entry Point** | `scripts/generate_compliance_artifacts.py` | CLI entrypoint delegating to `compliance_engine.generate_compliance_artifacts` |
| **Validation Entry Point** | `scripts/validate_compliance_artifacts.py` | CLI entrypoint delegating to `compliance_engine.validate_compliance_artifacts` |
| **Test Suite Runner** | `scripts/run_tests.py` | Test discovery runner executing automated tests across `tests/` |

---

## Contributions

To contribute or modify this skill or its templates:
1. Ensure all new templates adhere to the official DoD / NIST SP 800-53 Rev. 5 schemas.
2. When modifying `src/compliance_engine/excel_hydrator.py`, ensure `keep_vba=True` is maintained and embedded lookup sheets are preserved.
3. When modifying `src/compliance_engine/docx_generator.py`, test with OpenXML validation to avoid XML namespace corruption.
4. When making changes to the compliance engine source code itself, run `python3 .gemini/skills/compliance/scripts/run_tests.py` before submitting changes (engine code modifications only, never during standard workspace usage).

---

## Reporting Issues

Report bugs or feature improvements for this skill in the project repository tracker or
following the workspace issue management process.
