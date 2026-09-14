# Subskill: System Security Plan (SSP) Review & Narrative Accuracy Checker (`ssp_skill.md`)

This subskill guides the AI agent to act as an **Expert Technical Reviewer & Control Assessor** for the **System Security Plan (SSP)**.

The Python generator (`generate_compliance_artifacts.py`) is the primary source of truth that extracts Terraform AST facts, populates authoritative templates, and builds the baseline SSP under:
- `<TARGET_FOLDER>/ato_artifacts/SSP/SSP_System_Security_Plan.md`
- `<TARGET_FOLDER>/ato_artifacts/SSP/SSP_System_Security_Plan.docx`

The AI agent uses this subskill to **review the generated document for accuracy, ensure the Python engine didn't miss anything from the codebase, and enrich technical control narratives with human/cybersecurity expertise**.

---

## 4-Step Expert Review Methodology

### Step 1: Verify Python Extraction Fidelity
- Open `<TARGET_FOLDER>/ato_artifacts/SSP/SSP_System_Security_Plan.md`.
- Cross-reference against `<TARGET_FOLDER>/system_inventory.json` and `<TARGET_FOLDER>/terraform/` to verify:
  - System metadata: System Name, Organization, Billing ID, Primary GCP Region.
  - Component counts: Ensure all discovered GCS buckets, KMS key rings, subnets, firewalls, and IAM service accounts are accurately reflected.
  - Verify that no Terraform modules or components were omitted by the automated extractor.

### Step 2: Review Technical Control Implementation Statements
Inspect the implementation narratives across all 20 NIST SP 800-53 Rev. 5 control families, focusing on high-impact security controls:
- **AC-17 (Remote Access)**: Confirm that Identity-Aware Proxy (Cloud IAP), TCP forwarding tunnels, and mutual TLS 1.3 are documented, and that zero direct `0.0.0.0/0` SSH/RDP ingress exists in the code.
- **IA-2 (Identification & Authentication)**: Confirm that phishing-resistant MFA (FIDO2 / PIV-CAC), Workload Identity Federation (WIF), and Privileged Access Manager (PAM) are accurately described.
- **SC-7 (Boundary Defense)**: Confirm that perimeter firewalls, default-deny ingress, isolated private VPC subnets, and VPC Service Controls (VPC-SC) match live architecture.
- **SC-28 (Cryptographic Protection)**: Confirm that Customer-Managed Encryption Keys (CMEK) via Cloud KMS HSM modules (FIPS 140-3 Level 3 validated), automated key rotation <= 90 days, and AES-256-GCM are documented.
- **AU-2 / AU-6 (Audit & Accountability)**: Confirm that Cloud Logging sinks exporting audit and VPC flow logs to an accredited CSSP or external SIEM match live `.tf` sink definitions.
- **IR-4 / IR-6 (Incident Response)**: Confirm mandatory 1-hour reporting SLAs to DC3 / CISA and references to tactical runbooks.

### Step 3: Enrich and Tailor Nuanced Details
- If the Python generator produced a baseline narrative that lacks specific architectural context, use `replace_file_content` to enrich the narrative with concrete configuration details (e.g. exact crypto key paths, subnet CIDRs, or IAM role names).
- Eliminate any vague qualifiers (`"appropriate measures"`, `"as needed"`, `"reasonable precautions"`) by substituting exact operational parameters and SLAs.

### Step 4: Verify Human Action Callout Preservation
- Ensure all visual yellow action badges (`> [!IMPORTANT] ⚠️ **RMF TEAM / HUMAN ACTION REQUIRED**`) for site-specific physical security, facility suites, or executive signatures are preserved for human organizational review.

---

## Trigger Commands

Prompt the AI agent at any time with:
- `"Review the generated System Security Plan (SSP) for accuracy against my Terraform code"`
- `"Check that the SSP didn't miss any infrastructure components or encryption settings"`
- `"Enrich the SSP control implementation narratives with expert security details"`
