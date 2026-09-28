# Subskill: Security Control Traceability Matrix (SCTM) Review & Accuracy Checker (`sctm_skill.md`)

This subskill guides the AI agent to act as an **Assessor & Traceability Reviewer** for the **Security Control Traceability Matrix (SCTM)** deliverable:
- `<TARGET_FOLDER>/ato_artifacts/SCTM/SCTM_Burndown_Matrix.yaml`
- `<TARGET_FOLDER>/ato_artifacts/SCTM/SCTM_Burndown_Matrix.xlsm`

The Python generator (`generate_compliance_artifacts.py --data-format=both`) is the primary source of truth that loads the authoritative `ControlInfoExport_Template.xlsm`, preserves VBA macros and rows 7..5000+, matches controls in-place, and enforces dropdown validation from the `Data Validation` sheet.

The AI agent uses this subskill to **review the generated SCTM workbook, verify implementation statuses and narratives against live Terraform code, ensure no baseline controls were omitted, and refine technical implementation descriptions**.

---

## 4-Step SCTM Review Methodology

### Step 1: Excel Structure & Macro Integrity Check
- Verify that `SCTM_Burndown_Matrix.xlsm` preserves original VBA macros (`keep_vba=True`), embedded dropdown lists, and formula calculations.
- Confirm system metadata in Cell `A2` reflects the correct System Name and Organization.

### Step 2: Control Mapping & Status Verification
Inspect key control rows across all control families:
- Verify that `Implementation Status` (`Implemented`, `Inherited`, `Compensated`, `Planned`, `Not Applicable`) accurately reflects actual infrastructure state in `<TARGET_FOLDER>/terraform/`.
- Ensure common controls (e.g. Google Cloud physical datacenter controls for PE, physical media destruction for MP) are designated as `Inherited` or `Hybrid` with `Common Control Provider: Google Cloud`.
- Ensure system-specific controls (e.g. AC-17, IA-2, SC-7, SC-28, AU-2) are designated as `Implemented` or `Planned`.

### Step 3: Technical Narrative Depth & Evidence Review
- Inspect the implementation narrative column for core technical controls.
- Verify that the narrative details the actual Terraform resources (e.g. `google_kms_crypto_key` rotation for SC-28, Cloud IAP for AC-17, default-deny firewalls for SC-7).
- If the automated text is brief or generic, use the AI agent's security knowledge to enrich the statement with concrete architectural facts.

### Step 4: 14 ATC Connection Controls Verification
- Confirm that all 14 mandatory Authorization to Connect (ATC) controls have complete implementation narratives and valid test methods (`Test`, `Examine`, `Interview`).

---

## Trigger Commands

Prompt the AI agent at any time with:
- `"Review the SCTM workbook to verify control implementation statuses match my Terraform code"`
- `"Check the 14 ATC connection controls in the SCTM burndown matrix"`
- `"Ensure all Google Cloud inherited controls are properly mapped in the SCTM"`
