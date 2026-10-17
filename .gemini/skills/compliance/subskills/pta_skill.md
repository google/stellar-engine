---
name: compliance-pta
description: Reference sub-skill specification for reviewing the Path to Authorization (PTA) Strategy, Master ATO Roadmap, and Execution Checklist (Path_to_Authorization.md and .docx).
---
<!-- skip boilerplate check -->

# Subskill: Path to Authorization (PTA) Strategy Review & Executive Roadmap (`pta_skill.md`)

> **Reference Sub-Skill:** This document is a component reference specification under `<SKILL_DIR>/subskills/` and is invoked through the parent `compliance` skill ([../SKILL.md](../SKILL.md)).

This subskill guides the AI agent to act as an **Executive RMF Strategist & Roadmap Reviewer** for the **Path to Authorization (PTA) Strategy, Master ATO Roadmap & Execution Checklist** hydrated from `<SKILL_DIR>/templates/pta/Path_to_Authorization_Template.md`:
- `<TARGET_FOLDER>/ato_artifacts/Path_to_Authorization.md`
- `<TARGET_FOLDER>/ato_artifacts/Path_to_Authorization.docx`

The Python generator (`<SKILL_DIR>/scripts/generate_compliance_artifacts.py`) and validator (`<SKILL_DIR>/scripts/validate_compliance_artifacts.py`) are the primary sources of truth that compile the foundational 6-phase master RMF roadmap, 7-step NIST SP 800-37 crosswalk, 10 operational evidence items, the engine's 12-control NIST SP 800-53 Rev. 5 ATC boundary review subset (informed by the DISA Cloud Connection Process Guide), and DISA STIG recommendations.

The AI agent uses this subskill to **review the executive roadmap, verify that Phase 3 deliverables match what was code-generated, ensure remaining human milestones (Phases 4-6) are actionable, and tailor the Authorizing Official (AO) engagement memo**.

---

## 4-Step Executive Review Methodology

### Step 1: Document Governance & Stakeholder Alignment
- Inspect the Document Governance block in `Path_to_Authorization.md`.
- Confirm that System Name, Organization, Compliance Baseline, Target Authorization Date, and stakeholder roles (ISSM, System Owner, Authorizing Official) match `compliance_config.yaml`.

### Step 2: Phase 3 Deliverables Verification
- Review the Phase 3 delivery section to ensure all delivered code-generated artifacts are correctly cataloged with clickable links:
  - System Security Plan (`SSP/`)
  - 20 Policy Manuals (`Policies_and_Procedures/`)
  - SCTM, PPSM, HW/SW Inventory, POA&M, FIPS Matrix, Incident Runbooks, and OSCAL packages.

### Step 3: ATC Connection Controls Review Subset & Operational Evidence Review
- Verify that the engine's 12-control Authorization to Connect (ATC) boundary review subset (`AC-17`, `AC-17(2)`, `IA-2(1)`, `IA-2(2)`, `IA-5(1)`, `IR-8`, `IR-9`, `RA-5`, `SC-7`, `SC-8`, `SC-28`, `SI-2`; informed by the DISA Cloud Connection Process Guide and mapped to NIST SP 800-53 Rev. 5, incorporating withdrawn Rev. 4 `IA-2(3)` and `IA-2(4)`) is complete and highlights zero residual High risks.
- Confirm the 10 Operational Evidence items (ACAS scans, STIG Viewer checklists, SAST/SBOM, PIA DD Form 2930, ISAs, CSSP SLA, SAAR DD 2875, TTX reports, AO Memo) provide clear operational guidance for the ISSM.

### Step 4: Executive Determination Request Memo Tailoring
- Inspect the sample Executive ATO Determination Request Memo.
- Tailor the business/mission impact justification and risk acceptance rationale to the specific public sector program.

---

## Trigger Commands

Prompt the AI agent at any time with:
- `"Review the Path to Authorization (PTA) roadmap to verify all delivered artifacts are cataloged"`
- `"Tailor the Authorizing Official (AO) executive submission memo"`
