# Subskill: Plan of Action and Milestones (POA&M) Review & Accuracy Checker (`poam_skill.md`)

This subskill guides the AI agent to act as a **Remediation & Continuous Monitoring Reviewer** for the **Plan of Action and Milestones (POA&M)** deliverable:
- `<TARGET_FOLDER>/ato_artifacts/POAM/Plan_of_Action_and_Milestones.yaml`
- `<TARGET_FOLDER>/ato_artifacts/POAM/Plan_of_Action_and_Milestones.xlsm`

The Python generator (`generate_compliance_artifacts.py --data-format=both`) is the primary source of truth that evaluates automated scanner findings (Checkov, Semgrep, Trivy, SARIF), user-declared punch-lists, and IaC gaps into the 41-column eMASS-compliant schema.

The AI agent uses this subskill to **review the POA&M workbook against live security scans, verify planned mitigations are technically concrete, ensure realistic milestone completion dates, and confirm no artificial placeholder findings were hallucinated**.

---

## 4-Step POA&M Review Methodology

### Step 1: Scanner Ingestion & Finding Grounding Check
- Verify that every weakness entry in the POA&M stems from a real, verifiable source:
  1. Real scanner findings from Checkov (IaC misconfigurations), Semgrep (SAST), or Trivy (container CVEs).
  2. Declared punch-list items in `compliance_config.yaml`.
  3. Real architectural gaps detected in live Terraform state (e.g. unencrypted bucket or overly permissive firewall rule).
- **Zero Hallucinated Fillers**: If the deployed architecture is 100% compliant and scanners report clean passes, verify that the POA&M contains zero open items. Reject synthetic or mock operational milestones (such as unperformed penetration tests or fake tabletop exercises).

### Step 2: Milestone Schedule & SLA Compliance Check
- Inspect `Scheduled Completion Date` across all open items.
- Ensure completion dates conform to federal/DoD flaw remediation SLAs:
  - **CAT I / Critical**: Remediation mandated within 30 days of discovery.
  - **CAT II / Medium**: Remediation mandated within 90 days.
  - **CAT III / Low**: Remediation within 180 days or next release cycle.
- Flag and correct any placeholder dates (`YYYY-MM-DD`, `null`, `None`).

### Step 3: Mitigation Specificity & Terraform Alignment
- Inspect the `Planned Mitigation` field for each item.
- Ensure each mitigation provides actionable, technically specific remediation steps (e.g. referencing exact Terraform resource blocks, CLI commands, or configuration flags) rather than vague promises (`"will fix later"`).

### Step 4: Dropdown Validation & eMASS Schema Conformance
- Verify that severity, status (`Open`, `Ongoing`, `Completed`, `Risk Accepted`), and risk assessment columns conform strictly to the embedded Excel validation rules.

---

## Trigger Commands

Prompt the AI agent at any time with:
- `"Review the POA&M workbook to verify findings match my security scan outputs"`
- `"Check that all POA&M remediation timelines satisfy DoD / FedRAMP flaw remediation SLAs"`
- `"Ensure the POA&M does not contain synthetic or fabricated findings"`
