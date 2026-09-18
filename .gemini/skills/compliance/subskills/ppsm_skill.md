# Subskill: Ports, Protocols, and Services Matrix (PPSM) Review & Accuracy Checker (`ppsm_skill.md`)

This subskill guides the AI agent to act as a **Network Boundary & Protocol Reviewer** for the **Ports, Protocols, and Services Matrix (PPSM)** deliverable:
- `<TARGET_FOLDER>/ato_artifacts/PPSM/PPSM_Ports_Protocols_Services.yaml`
- `<TARGET_FOLDER>/ato_artifacts/PPSM/PPSM_Ports_Protocols_Services.xlsm`

The Python generator (`generate_compliance_artifacts.py --data-format=both`) is the primary source of truth that extracts firewall rules, network interfaces, Private Service Connect endpoints, and API services into the 20-column DoD / FedRAMP boundary matrix.

The AI agent uses this subskill to **review the PPSM against live Terraform firewall definitions, verify that all ingress ports and APIs are documented, check boundary designations against the `Glossary` sheet, and ensure no unapproved ports or protocols are exposed**.

---

## 4-Step PPSM Review Methodology

### Step 1: Firewall Ingress & Protocol Parity Check
- Cross-reference the PPSM rows against all `google_compute_firewall` resources in `<TARGET_FOLDER>/terraform/`.
- Verify that every allowed ingress port (e.g. TCP 443 for HTTPS, TCP 22 via Cloud IAP netblock `35.235.240.0/20`) has an authorized stream record.
- **Strict Check**: Ensure that NO entry permits direct unauthenticated `0.0.0.0/0` ingress to SSH (22), RDP (3389), or database listener ports.

### Step 2: Cloud API & Private Service Connect (PSC) Endpoint Check
- Verify that all active Google API service domains (`*.googleapis.com`) and Private Google Access / PSC VIP ranges (`199.36.153.4/30`) are documented.
- Confirm protocol definitions state TLS 1.3 / mTLS with FIPS-validated cryptographic suites.

### Step 3: Boundary Type & Excel Dropdown Validation
- Verify that the `Boundary Type` column strictly uses allowable glossary values (`External Cloud Boundary`, `VPC Boundary`, `Inter-VPC Peering Boundary`).
- Confirm that entries conform to the embedded data validation rules in the `PPSMBoundariesInformationExport_Template.xlsm` workbook.

### Step 4: Interconnection Approval Badges
- Confirm that external boundary interconnections requiring formal Interconnection Security Agreements (ISAs/MOUs) are tagged with required human review badges (`RMF Team & ISSM Sign-Off Required`).

---

## Trigger Commands

Prompt the AI agent at any time with:
- `"Review the PPSM workbook to verify all firewall rules and API endpoints are mapped"`
- `"Check that no unapproved or public 0.0.0.0/0 ingress rules exist in the PPSM"`
