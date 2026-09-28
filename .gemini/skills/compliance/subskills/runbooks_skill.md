# Subskill: Incident Response Runbooks Review & Customization (`runbooks_skill.md`)

This subskill guides the AI agent to act as an **Incident Response & SecOps Technical Reviewer** for the **5 Tactical Cloud Incident Response Runbooks** and the extensible scenario template under:
`<TARGET_FOLDER>/ato_artifacts/Incident_Response_Runbooks/`

The Python generator (`generate_compliance_artifacts.py`) is the primary source of truth that hydrates the runbooks from authoritative templates, injecting discovered project IDs, KMS key rings, and VPC configurations.

The AI agent uses this subskill to **review the generated runbooks against live infrastructure, verify step-by-step CLI commands and containment procedures, ensure regulatory reporting SLAs are correct, and author custom incident scenarios**.

---

## 5 Pre-Engineered Runbook Scenarios

1. `IR_IAM_Compromised_Credentials_Runbook.md` & `.docx` (IR-IAM-001)
2. `IR_Compute_Resource_Compromise_Runbook.md` & `.docx` (IR-COMP-001)
3. `IR_KMS_CMEK_Compromise_Runbook.md` & `.docx` (IR-CMEK-001)
4. `IR_Network_Intrusion_Runbook.md` & `.docx` (IR-NET-001)
5. `IR_VPC_Service_Controls_Violation_Runbook.md` & `.docx` (IR-VPC-001)
6. `Incident_Response_Runbook_Template.md` & `.docx` (IR-TPL-001)

---

## 4-Step SecOps Review Methodology

### Step 1: Verify Command Syntax & Resource Hydration
- Inspect containment and eradication CLI commands in Phase 2 of each runbook.
- Confirm that hydrated resource identifiers (project IDs, service account emails, KMS key rings, subnet names) match live resources discovered in `<TARGET_FOLDER>/system_inventory.json` and Terraform outputs.
- Verify that destructive commands (e.g. `gcloud kms keys versions destroy`) are guarded with required approval gates and blast-radius warnings.

### Step 2: Telemetry & Alert Ingestion Review
- **FedRAMP High / Commercial**: Confirm that native Google Security Command Center (SCC) Event Threat Detection (ETD) and Cloud Logging query signatures are referenced.
- **DoD IL4 / DoD IL5 Boundaries**: Confirm that the runbook strictly respects that **SCC is NOT accredited for DoD IL4/IL5 production enclaves**. Verify that detection signals are routed via Cloud Logging aggregated export sinks to an accredited external CSSP or external GovCloud SIEM.

### Step 3: Regulatory SLA Verification (Phase 4)
- Confirm that escalation tables enforce mandatory reporting windows:
  - **DoD Boundaries**: Mandatory 1-hour reporting to US-CERT / DoD Cyber Crime Center (DC3) per DoDI 8530.01.
  - **Federal Civilian**: Mandatory 1-hour reporting to CISA per OMB M-21-31.
  - **Internal Leadership**: Immediate notification to Authorizing Official (AO), ISSM, and System Owner.

### Step 4: Custom Scenario Authoring (When Needed)
- If the workload introduces unique mission architecture (e.g. multi-tenant database clusters, specialized GKE microservices, or custom API gateways), the agent uses `Incident_Response_Runbook_Template.md` to craft a bespoke runbook following the 4-phase NIST SP 800-61 Rev. 2 lifecycle.

---

## Trigger Commands

Prompt the AI agent at any time with:
- `"Review the incident response runbooks to ensure CLI commands match my GCP environment"`
- `"Verify incident reporting SLAs and CSSP telemetry routing in the runbooks"`
- `"Add a custom incident response runbook for database exfiltration or ransomware"`
