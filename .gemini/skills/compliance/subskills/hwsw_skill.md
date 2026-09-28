# Subskill: Hardware & Software Inventory Review & Accuracy Checker (`hwsw_skill.md`)

This subskill guides the AI agent to act as an **Asset Management & CM-8 Reviewer** for the **Hardware and Software Asset Inventory (HW/SW Inventory)** deliverable:
- `<TARGET_FOLDER>/ato_artifacts/HW_SW_Inventory/Hardware_Software_Inventory.yaml`
- `<TARGET_FOLDER>/ato_artifacts/HW_SW_Inventory/Hardware_Software_Inventory.xlsm`

The Python generator (`generate_compliance_artifacts.py --data-format=both`) is the primary source of truth that extracts compute, network, storage, and API components from Terraform AST into the two-sheet (`Hardware` and `Software`) workbook.

The AI agent uses this subskill to **review the asset inventory against live Terraform definitions, verify component counts and public-facing flags, check dropdown compliance against the `(U) Lists` sheet, and ensure no deployed resources were missed**.

---

## 4-Step HW/SW Review Methodology

### Step 1: Hardware Sheet Verification (Row 8+)
- Inspect the `Hardware` sheet to verify all cloud infrastructure components are represented:
  - Cloud Provider Tenant / Organization Node.
  - Virtual Private Clouds (VPCs) and Subnets.
  - Compute Engine VMs, GKE Clusters, and Cloud SQL instances.
  - Cloud KMS HSM cryptographic modules.
- Verify that `Public Facing` is strictly set to `No` for private subnets, internal bastions, and isolated databases.
- Confirm that dropdown selections (`Component Type`, `Virtual Asset`, `Critical Asset`) match the allowable values in `(U) Lists`.

### Step 2: Software Sheet Verification (Row 8+)
- Inspect the `Software` sheet to verify all enabled Google Cloud APIs and application software are listed:
  - Enabled services discovered from `google_project_service` (e.g. Compute, KMS, Logging, IAM).
  - Terraform Infrastructure-as-Code engine and version (`1.5.7+`).
  - Application runtime packages discovered from package manifests (`package.json`, `requirements.txt`, `pom.xml`, `go.mod`).

### Step 3: Reconciliation Against `system_inventory.json`
- Verify that asset counts between the Excel workbook and `system_inventory.json` match with 100% parity.
- Ensure that no newly provisioned subnets or databases in `<TARGET_FOLDER>/terraform/` were missed by the automated run.

### Step 4: Physical Hardware Isolation Callout
- Confirm that physical datacenter equipment is designated as CSP-managed (`Google Cloud`), and any on-premises or tenant edge hardware is flagged with human audit callouts.

---

## Trigger Commands

Prompt the AI agent at any time with:
- `"Review the HW/SW inventory workbook to ensure all Terraform resources are captured"`
- `"Verify that asset types and public-facing flags in the inventory match my architecture"`
