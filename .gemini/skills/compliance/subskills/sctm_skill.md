---
name: compliance-sctm
description: Reference sub-skill specification for reviewing the Security Control Traceability Matrix (SCTM) in YAML and macro-enabled Excel (.xlsm) formats.
---
<!-- skip boilerplate check -->

# Review guide: Security Control Traceability Matrix (`sctm_skill.md`)

> **Reference Sub-Skill:** This document is a component reference specification under `<SKILL_DIR>/subskills/` and is invoked through the parent `compliance` skill ([../SKILL.md](../SKILL.md)).

Use after the workflow in [../SKILL.md](../SKILL.md) has run. Outputs:

- `<TARGET_FOLDER>/ato_artifacts/SCTM/SCTM_Burndown_Matrix.xlsm` (from
  `<SKILL_DIR>/templates/sctm/ControlInfoExport_Template.xlsm`)
- `<TARGET_FOLDER>/ato_artifacts/SCTM/SCTM_Burndown_Matrix.yaml` (from
  `<SKILL_DIR>/templates/sctm/SCTM_Template.yaml`)

The generator opens the workbook with `keep_vba=True`, writes the system name and organization to
cell `A2` of the `Template` sheet, and fills each control row (row 7 onward) in place. For each
control it sets the implementation status, designation, common control provider, test method,
narrative, and monitoring fields:

- controls outside the selected baseline (`config/baselines/<regime>.json` across the 11 supported regimes: `FedRAMP Low/Moderate/High`, `FISMA Low/Moderate/High`, `DoD IL2/IL4/IL5/IL6`, and `CJIS`) are marked `Not Applicable` with a Column I justification and blank Column J completion date;
- from `SCTM_Template.yaml` when that file lists an active baseline control;
- otherwise from fixed defaults per control family (for example, PE and PS rows become
  `Inherited` with provider `DoD`, PL and PM rows `Planned`, and AC, IA, and SC rows `Implemented`
  with a generic narrative);
- with the risk fields (severity, likelihood, impact, residual risk) taken from a POA&M item
  that maps to the control, if there is one.

These values are not derived control by control from the Terraform, so every row needs review.

## 1. Check the workbook

- The macros are preserved: open the file in Excel, or confirm that `xl/vbaProject.bin` is in the
  archive (`unzip -l SCTM_Burndown_Matrix.xlsm`).
- Cell `A2` shows the correct system name and organization.
- The validator reports SCTM rows with a missing estimated completion date, missing responsible
  entities, missing SLCM comments, or dates that contradict the status. Resolve those first.

## 2. Check status and inheritance

- `Implemented` only where the Terraform or a documented process actually implements the control.
  Use `Planned` (with a date) or `Not Applicable` (with a justification in column I) otherwise.
- Inherited controls name the real provider. For a system on Google Cloud, physical and
  environmental (PE) controls are typically inherited from Google's provisional authorization;
  the default provider `DoD` is often wrong.
- System-specific controls such as AC-17, IA-2, SC-7, SC-28, and AU-2 cite the resources that
  implement them.

## 3. Check the narratives

- Replace generic family narratives with the actual mechanism: for example, `google_kms_crypto_key`
  settings for SC-28, the IAP access path for AC-17, and the firewall rules for SC-7.
- Test methods use the assessment methods `Examine`, `Interview`, and `Test`.

## 4. Check the ATC controls

The validator checks a list of Authorization to Connect (ATC) controls defined in
`src/compliance_engine/validate_compliance_artifacts.py` and reports any that have no
implementation statement in the SCTM or SSP. Each of those controls needs a complete narrative and
a test method. The list is the engine's own checklist, not a published DISA list; confirm with the
AO or the connection approval authority which controls they require.

Edits to the generated files are overwritten by the next `generate` or `validate --fix` run.

## Example requests

- "Review the SCTM statuses against my Terraform."
- "Check the ATC controls in the SCTM."
- "Check which controls in the SCTM are inherited and from whom."
