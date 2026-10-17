---
name: compliance-ppsm
description: Reference sub-skill specification for reviewing the Ports, Protocols, and Services Matrix (PPSM) in YAML and macro-enabled Excel (.xlsm) formats.
---
<!-- skip boilerplate check -->

# Review guide: Ports, Protocols, and Services Matrix (`ppsm_skill.md`)

> **Reference Sub-Skill:** This document is a component reference specification under `<SKILL_DIR>/subskills/` and is invoked through the parent `compliance` skill ([../SKILL.md](../SKILL.md)).

Use after the workflow in [../SKILL.md](../SKILL.md) has run. Outputs:

- `<TARGET_FOLDER>/ato_artifacts/PPSM/PPSM_Ports_Protocols_Services.xlsm` (from
  `<SKILL_DIR>/templates/ppsm/PPSMBoundariesInformationExport_Template.xlsm`; 20 columns, headers in row 8)
- `<TARGET_FOLDER>/ato_artifacts/PPSM/PPSM_Ports_Protocols_Services.yaml` (generated from
  canonical records in `src/compliance_engine/hardware_records.py`)

The generator writes one row per enabled Google API (HTTPS, port 443) and one row per Terraform
firewall rule, plus application ports found in container manifests. Several columns are filled
with fixed defaults, so check each row.

## 1. Firewall rules

- Every `google_compute_firewall` rule in the target folder has a row with the same protocol,
  ports, and direction.
- Source addresses are inferred: the IAP range `35.235.240.0/20` is used only when the rule name
  contains `iap`; other rules show the subnet CIDRs. Compare them with the rule's
  `source_ranges`.
- No row may allow `0.0.0.0/0` ingress to SSH (22), RDP (3389), or database ports. If the Terraform
  allows it, report a CAT I finding; do not hide it in the matrix.

## 2. Google API rows

- Each API in `google_project_service` has a row.
- The generator labels `199.36.153.4/30` as a Private Service Connect address. That range is the
  `restricted.googleapis.com` VIP (`private.googleapis.com` is `199.36.153.8/30`); a Private
  Service Connect endpoint uses an internal address you choose. Correct the row to match how the
  blueprint reaches Google APIs.

## 3. Boundary and tunnel columns

- The `Boundary`, `Connection Logical Source Point`, `Connection Logical Destination Point`, and
  `VPN Tunnel Type` values must come from the `Glossary` sheet.
- The generator uses fixed values: boundary `1. Ext to DoD GW (In)` for every API row and
  `11. Enclave GW to Enclave (In)` for every firewall row, and `Cloud Layer 3 VPN` as the tunnel
  type for API rows. Change each to the value that describes the real traffic path and direction.

## 4. Interconnections

- External connections that need an Interconnection Security Agreement or MOU (CA-3) are marked
  for ISSM review, with a `[WARNING: RMF TEAM ACTION REQUIRED: ...]` marker if the agreement is not
  yet recorded.

Edits to the generated files are overwritten by the next `generate` or `validate --fix` run.

## Example requests

- "Check that every firewall rule and API endpoint is in the PPSM."
- "Check the PPSM for any `0.0.0.0/0` ingress."
