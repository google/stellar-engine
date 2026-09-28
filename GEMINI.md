# gemini.md - AI Assistant Guidelines for Stellar Engine

## Project Overview

Stellar Engine is a fork of the Google Cloud Foundation Fabric (CFF), providing Infrastructure as Code (IaC) to help Google Cloud Platform
(GCP) customers create secure and compliant landing zones. It has a strong focus on environments requiring Assured Workload overlays, such
as FedRAMP Moderate, FedRAMP High, IL4, and IL5, and includes documentation mapping NIST 800-53r5 controls to accelerate Authorization to Operate (ATO)
processes.

**Key Technologies:** Terraform, Google Cloud Platform (GCP)

## Core Principles & Guardrails for Blueprint Development

These principles MUST be followed when creating or modifying Terraform blueprints and modules in this repository.

1.  **Maximize Reusability (Critical):** This is the most important principle. DO NOT redefine common elements. ALWAYS REUSE existing base
configurations and modules.
    *   **Environment Variables:** Inherit from and extend base variable definitions found in `variables.tf` files within individual
modules and blueprints. Avoid hardcoding values. Common variables are typically defined within each module (e.g.,
`modules/net-vpc/variables.tf`).
    *   **Service Accounts:** Reuse existing service account definitions and IAM policies, primarily managed through the
`modules/iam-service-account/` module. Do not create new service accounts with overlapping permissions. Always adhere to the principle of
least privilege.
    *   **Networking:** Leverage the base networking infrastructure. New blueprints should connect to or build upon the VPCs, subnets, and
firewall rules defined in modules like `modules/net-vpc/`, `modules/net-vpc-firewall/`, etc. Do not create parallel or redundant network
structures.

2.  **Modularity:** Design blueprints to be modular and composable. Utilize the existing modules in the `modules/` directory. Break down
complex deployments into smaller, reusable components.

3.  **Documentation:** All new or modified modules and blueprints must include a `README.md` explaining their purpose, inputs (variables),
outputs, and any dependencies.

4.  **Naming Conventions:** Strictly follow the established naming conventions outlined in `documentation/naming-convention.md`.
Consistency in naming variables, resources, modules, and files is crucial.

5.  **Security:** Adhere to GCP security best practices and the principle of least privilege in all configurations. Ensure compliance with
the targeted regime (FedRAMP Moderate, FedRAMP High, IL5, etc.).

## Key Codebase Resources

*   **Base Environment Variable Configurations:** Defined within each module and blueprint's `variables.tf` file (e.g.,
`modules/net-vpc/variables.tf`, `blueprints/il5/bigquery/variables.tf`).
*   **Core Service Account Definitions:** `modules/iam-service-account/`
*   **Base Networking Modules:**
    *   VPC: `modules/net-vpc/`
    *   Firewall: `modules/net-vpc-firewall/`
    *   Subnets: Typically defined within the `modules/net-vpc/` module.
    *   Other networking components: See other modules starting with `net-` in the `modules/` directory.
*   **Naming Convention Documentation:** `documentation/naming-convention.md`
*   **Agent Skills:** `.gemini/skills/` (see **Agent Skills** below)
*   **Examples of Well-Structured Blueprints:**
    *   `blueprints/il5/bigquery/`
    *   `blueprints/fedramp-high/cloud-run/`
    *   The `fast/` directory contains staged blueprints for bootstrapping an organization.

## Agent Skills

Reusable agent skills are located in `.gemini/skills/<skill-name>/`, each defined by a `SKILL.md` with YAML
frontmatter (`name`, `description`). Skills are self-contained: they resolve their own root at runtime
and must not hardcode absolute paths or depend on a specific checkout location. Note that auto-discovery 
of repository-local skills varies by agent runtime environment; users may need to symlink them to their global 
`~/.gemini/config/skills/` directory if they are not automatically loaded.

### `compliance` — RMF / FedRAMP / DoD ATO Package Automation

`.gemini/skills/compliance/` automates NIST SP 800-53 Rev. 5, FedRAMP Moderate/High, DoD CC SRG
(IL4/IL5/IL6), StateRAMP, CJIS, and FISMA Authorization to Operate (ATO) packages. It extracts live
architecture facts from Terraform blueprints and application code, hydrates authoritative templates,
and emits deliverables as Markdown, Word (`.docx`), YAML, and macro-enabled Excel (`.xlsm`):
SSP, 20 policy manuals, SCTM, PPSM, HW/SW inventory, POA&M, FIPS 140-3 matrix, IR runbooks,
NIST OSCAL packages, and the master Path to Authorization roadmap.

**Setup** (pinned dependencies, isolated virtualenv — `.venv/` is gitignored):

```bash
python3 -m venv .gemini/skills/compliance/.venv
.gemini/skills/compliance/.venv/bin/python -m pip install --require-virtualenv \
  -r .gemini/skills/compliance/requirements.txt
```

**Operational workflow** — the only three commands run against a target folder:

```bash
PY=.gemini/skills/compliance/.venv/bin/python
$PY .gemini/skills/compliance/scripts/extract_system_data.py <TARGET_FOLDER>
$PY .gemini/skills/compliance/scripts/generate_compliance_artifacts.py <TARGET_FOLDER> \
  --policy-format=both \
  --data-format=both \
  --oscal-format=both
$PY .gemini/skills/compliance/scripts/validate_compliance_artifacts.py <TARGET_FOLDER> --fix
```

Here `<TARGET_FOLDER>` is a single blueprint directory (e.g. `blueprints/il5/bigquery/`), **not** the
repository root. Artifacts are written to `<TARGET_FOLDER>/ato_artifacts/`.

> **Target folder isolation:** the skill operates strictly within one designated target folder. If the
> target folder is not specified and cannot be determined from context, STOP and ask the user. Never
> guess a blueprint directory and never generate `ato_artifacts/` into the repository root.

**Engine test suite** (framework developers modifying `src/compliance_engine/` only — never during a
normal compliance run):

```bash
.gemini/skills/compliance/.venv/bin/python .gemini/skills/compliance/scripts/run_tests.py
```

`python-hcl2==7.3.1` is a required pin, not an optional extra: it determines how much Terraform lands
inside the assessed accreditation boundary (the in-repo fallback parser historically covers significantly less of a complex estate).
Always install into the skill's own virtualenv. Running the engine on a bare system interpreter can
cause it to borrow an unrelated tool's packages (e.g. checkov's incompatible `bc-python-hcl2` fork),
which is refused by a shape canary and silently degrades Terraform coverage.

## Guidance for AI Assistants

When generating or modifying code within the Stellar Engine repository, especially for new blueprints or modules:

1.  **ALWAYS** refer to the **Core Principles & Guardrails** and **Key Codebase Resources** outlined above.
2.  **PRIORITIZE REUSE:** Before creating any new resource, thoroughly check if an existing module or configuration in `modules/` or
`fast/` can be leveraged, particularly for:
    *   Networking (VPCs, subnets, firewalls)
    *   Service Accounts and IAM
    *   Common variable patterns
3.  **Follow Naming Conventions:** Adhere strictly to `documentation/naming-convention.md`.
4.  **Ask for Clarification:** If a request seems to require creating a new fundamental resource (e.g., a new base VPC, a new highly
privileged service account), ask the user to confirm if this is truly necessary and why existing components cannot be used.
5.  **Consult Module READMEs:** When using a module from `modules/`, always read its `README.md` to understand its usage, inputs, and
outputs.
6.  **Use the `compliance` Skill for ATO Work:** For any RMF, FedRAMP, DoD IL, StateRAMP, or CJIS accreditation
request, use `.gemini/skills/compliance/` (see **Agent Skills** above) rather than drafting compliance
documents by hand. Read its `SKILL.md` first, and confirm the target blueprint folder before running it.


