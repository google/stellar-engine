# Subskill: NIST SP 800-53 Policy Manuals Review & Tailoring (`policies_skill.md`)

This subskill guides the AI agent to act as an **Expert Governance & Compliance Policy Reviewer** for the **20 Enterprise Policy and Procedure Manuals** matching all 20 NIST SP 800-53 Rev. 5 control families.

The Python generator (`generate_compliance_artifacts.py --policy-format=both`) is the primary source of truth that deterministically hydrates authoritative Markdown templates and generates styled OpenXML Word documents (`.docx`) under:
`<TARGET_FOLDER>/ato_artifacts/Policies_and_Procedures/`

The AI agent uses this subskill to **review the generated policy manuals, verify they correctly reflect the system architecture and organizational parameters, ensure nothing was missed, and tailor domain-specific procedures with public sector expertise**.

---

## 4-Step Policy Review Methodology

### Step 1: Structural & Completeness Verification
Inspect the generated policy manuals to verify that each of the 20 control families has both `.md` and `.docx` deliverables present:
- AC, AT, AU, CA, CM, CP, IA, IR, MA, MP, PE, PL, PM, PS, PT, RA, SA, SC, SI, SR.
- Verify that every manual contains the mandatory NIST -1 structural sections:
  1. `## 1. Purpose` (Statutory / regulatory authority: FISMA, OMB A-130, NIST SP 800-53 R5).
  2. `## 2. Scope` (System authorization boundary applicability).
  3. `## 3. Roles and Responsibilities` (Concrete accountabilities: ISSM, ISSO, System Owner, Admins).
  4. `## 4. Policy Statements` (Prescriptive technical mandates).
  5. `## 5. Compliance & Enforcement` (Continuous audit authority and violation penalties).

### Step 2: Code Parity & Architectural Alignment Check
Cross-reference policy statements against live Terraform code in `<TARGET_FOLDER>/terraform/`:
- **Access Control (AC)**: Verify that remote access policies align with Cloud IAP and zero-trust proxies defined in Terraform; ensure passwordless/MFA requirements match identity configuration.
- **Audit & Accountability (AU)**: Verify that audit log retention policies (minimum 365 days) align with Cloud Storage retention policies or external SIEM sinks.
- **Identification & Authentication (IA)**: Verify that identity federation, hardware MFA, and Privileged Access Management (PAM) policies reflect live Google Cloud Identity settings.
- **System & Communications Protection (SC)**: Verify that encryption policies mandate CMEK key rotation <= 90 days and TLS 1.3, matching Terraform `google_kms_crypto_key` definitions.
- **Incident Response (IR)**: Verify that reporting escalation matrices mandate 1-hour reporting to CISA (Federal Civilian) or DC3 (DoD).

### Step 3: Eliminate Ambiguity & Inject Concrete Parameters
- Review the text to ensure the automated generator did not leave generic boilerplate or vague qualifiers.
- Replace any remaining ambiguous phrases (`"appropriate controls"`, `"as needed"`, `"regularly reviewed"`) with precise operational frequencies (e.g. quarterly account recertification, annual policy reviews, 24-hour account deactivation upon termination).

### Step 4: Preserve Human Governance Callouts
- Ensure all organizational action callouts (`> [!IMPORTANT] ⚠️ **RMF TEAM / HUMAN ACTION REQUIRED**`) for agency escalation phone numbers, local training LMS links, or executive signatures remain intact for human administrative sign-off.

---

## Trigger Commands

Prompt the AI agent at any time with:
- `"Review the 20 generated policy manuals to verify they match my cloud infrastructure"`
- `"Check that the policies didn't miss any NIST SP 800-53 Rev. 5 mandatory sections"`
- `"Tailor the access control and incident response policies with agency-specific parameters"`
