---
name: compliance-ssp
description: Reference sub-skill specification for reviewing the System Security Plan (SSP) in Markdown and Word (.docx) formats.
---
<!-- skip boilerplate check -->

# Review guide: System Security Plan (`ssp_skill.md`)

> **Reference Sub-Skill:** This document is a component reference specification under `<SKILL_DIR>/subskills/` and is invoked through the parent `compliance` skill ([../SKILL.md](../SKILL.md)).

Use after the workflow in [../SKILL.md](../SKILL.md) has run. The generator fills the SSP template
from `system_inventory.json` and `compliance_config.yaml`:

- `<SKILL_DIR>/templates/ssp/SSP_IL5_Template.md` for `DoD IL2` (filtered to 323 controls), `DoD IL4`
  (334 controls), `DoD IL5` (624 controls), and `DoD IL6` (627 controls); `<SKILL_DIR>/templates/ssp/SSP_FedRAMP_High_Template.md` for
  `FedRAMP Low` (156), `FedRAMP Moderate` (323), `FedRAMP High` (410), `FISMA Low` (149),
  `FISMA Moderate` (287), `FISMA High` (370), and `CJIS` (323). (`GovRAMP` / `StateRAMP` and `FedRAMP Tailored / LI-SaaS` fail closed.)
- Output: `<TARGET_FOLDER>/ato_artifacts/SSP/SSP_System_Security_Plan.md` and `.docx`.

Your job is to check the SSP against the Terraform, add facts the generator missed, and leave
organizational decisions to people.

## 1. Check what was extracted

Compare the SSP with `system_inventory.json` and the `.tf` files in the target folder:

- System name, organization, billing account, and primary region match `compliance_config.yaml`
  or the Terraform.
- Every bucket, key ring and key, network and subnet, firewall rule, and service account in the
  Terraform appears in the SSP.
- Resources declared in local child modules within the git work tree boundary are discovered and
  extracted by the HCL parser. For remote registry modules or unparsed modules outside the work tree
  boundary, run the extractor on `terraform show -json` output (`terraform_plan_path` or
  `terraform_state_path`).
- Values shown as `[NOT DETERMINED FROM SOURCE]` could not be found in the code. Confirm that they
  are really absent rather than missed.

## 2. Check the control statements

Each statement must describe the mechanism the Terraform implements, not a generic one:

- **AC-17 (Remote Access):** how administrators reach the system (for example, IAP TCP forwarding
  from `35.235.240.0/20`), and that no firewall rule allows `0.0.0.0/0` to SSH or RDP.
- **IA-2 (Identification and Authentication):** the identity provider and MFA method from
  `compliance_config.yaml` (`external_systems`), and workload identity for service accounts.
- **SC-7 (Boundary Protection):** firewall rules, private subnets, and VPC Service Controls
  perimeters as declared.
- **SC-28 (Protection of Information at Rest):** which resources use CMEK, the key names, the
  protection level, and the rotation period.
- **AU-2 / AU-6 (Event Logging / Audit Record Review):** the log sinks and their destination (the
  CSSP or SIEM). In DoD IL4/IL5 systems, do not rely on Security Command Center inside the
  boundary.
- **IR-4 / IR-6 (Incident Handling / Incident Reporting):** points to the runbooks, and reporting
  recipients and timelines agree with them (see [runbooks_skill.md](runbooks_skill.md)).

## 3. Improve the narratives

- Where a statement is generic, add concrete details from the code: key paths, subnet CIDRs, role
  names, sink destinations.
- Replace vague wording ("appropriate measures", "as needed", "regularly") with the actual
  parameter, or with a `[CONFIG_REQUIRED: ...]` placeholder if the value is an organizational
  decision. Do not invent values.
- Edits to the Markdown are overwritten by the next `generate` or `validate --fix` run. Record
  them so they can be repeated, or propose the change in the template.

## 4. Keep human-action markers

Leave every `[WARNING: RMF TEAM ACTION REQUIRED: ...]` marker and `> [!IMPORTANT]` callout in place.
They cover facility details, contacts, signatures, and other decisions that code cannot make.

## Example requests

- "Review the generated SSP against my Terraform."
- "Check that the SSP covers every bucket, key, and firewall rule."
- "Make the SSP control statements specific to this blueprint."
