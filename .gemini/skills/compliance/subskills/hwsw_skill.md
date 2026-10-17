---
name: compliance-hwsw
description: Reference sub-skill specification for reviewing the Hardware and Software Inventory in YAML and macro-enabled Excel (.xlsm) formats.
---
<!-- skip boilerplate check -->

# Review guide: hardware and software inventory (`hwsw_skill.md`)

> **Reference Sub-Skill:** This document is a component reference specification under `<SKILL_DIR>/subskills/` and is invoked through the parent `compliance` skill ([../SKILL.md](../SKILL.md)).

Use after the workflow in [../SKILL.md](../SKILL.md) has run. Outputs:

- `<TARGET_FOLDER>/ato_artifacts/HW_SW_Inventory/Hardware_Software_Inventory.xlsm` (from
  `<SKILL_DIR>/templates/hwsw/HWSWList_Template.xlsm`)
- `<TARGET_FOLDER>/ato_artifacts/HW_SW_Inventory/Hardware_Software_Inventory.yaml` (generated from
  canonical records in `src/compliance_engine/hardware_records.py`)

The workbook has a `Hardware` sheet and a `Software` sheet; headers are in row 7 and data starts at
row 8. Allowed component and software types come from the `(U) Lists` sheet.

## 1. Hardware sheet

- Each cloud component in `system_inventory.json` has a row: networks and subnets, Compute Engine
  instances, GKE clusters, databases, and Cloud KMS keys.
- `Public Facing` is `No` for private subnets, internal instances, and databases without public
  IP addresses, and `Yes` only where the Terraform exposes the asset.
- `Component Type` values are in the `(U) Lists` sheet. The validator reports rows whose type is
  not.
- Physical hardware belongs to the cloud provider. Mark any on-premises or edge hardware for human
  review rather than describing it from guesses.

## 2. Software sheet

- Every enabled Google Cloud API (`google_project_service`) is listed.
- Packages from application manifests (`package.json`, `requirements.txt`, `pyproject.toml`,
  `go.mod`, `pom.xml`) and container images are listed with their versions.
- `Software Type` values are in the `(U) Lists` sheet.

## 3. Reconcile with the inventory

- Row counts match the corresponding lists in `system_inventory.json`. The validator's
  "Architecture Reconciliation" line reports how many discovered assets it found in the
  deliverables.
- If the Terraform declares resources the inventory lacks (such as resources inside remote or unparsed
  modules outside the repository boundary), report them; rerunning the extractor on `terraform show -json`
  output picks them up.

Edits to the generated files are overwritten by the next `generate` or `validate --fix` run.

## Example requests

- "Check that the HW/SW inventory lists every Terraform resource."
- "Check the asset types and public-facing flags in the inventory."
