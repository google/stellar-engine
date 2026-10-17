---
name: compliance-policies
description: Reference sub-skill specification for reviewing the 20 NIST SP 800-53 Rev. 5 policy and procedure manuals in Markdown and Word (.docx) formats.
---
<!-- skip boilerplate check -->

# Review guide: policy and procedure documents (`policies_skill.md`)

> **Reference Sub-Skill:** This document is a component reference specification under `<SKILL_DIR>/subskills/` and is invoked through the parent `compliance` skill ([../SKILL.md](../SKILL.md)).

Use after the workflow in [../SKILL.md](../SKILL.md) has run. The generator fills the 20 templates
in `<SKILL_DIR>/templates/policies/`, one per NIST SP 800-53 Rev. 5 control family, and writes them to
`<TARGET_FOLDER>/ato_artifacts/Policies_and_Procedures/` as `.md` and/or `.docx`, depending on
`--policy-format`.

Families: AC, AT, AU, CA, CM, CP, IA, IR, MA, MP, PE, PL, PM, PS, PT, RA, SA, SC, SI, SR.

## 1. Check that the set is complete

- Each of the 20 templates has an output with the same base name (some end in
  `_Policy_and_Procedures`, others in `_Policy`), in every format that was requested.
- Each document has the document governance block, an overview, one section per control in the
  family, and Appendix A (compliance matrix).
- The XX-1 control of each family requires the policy to address purpose, scope, roles,
  responsibilities, management commitment, coordination among organizational entities, and
  compliance. Check that the overview and roles text cover these.

## 2. Check agreement with the Terraform and the other deliverables

- **AC:** remote access and MFA statements match the access path in Terraform (for example, IAP)
  and the identity provider in `compliance_config.yaml`.
- **AU:** the retention period stated for AU-11 matches the log bucket or sink retention in
  Terraform, and log destinations match the SSP.
- **IA:** identity federation, MFA, and service account key handling match the configuration.
- **SC:** key rotation and encryption statements match `google_kms_crypto_key` settings
  (`rotation_period`, protection level) and the SSP.
- **IR:** escalation contacts and reporting timelines match the incident response runbooks (see
  [runbooks_skill.md](runbooks_skill.md)).

## 3. Replace vague wording

- Replace phrases such as "appropriate controls", "as needed", and "regularly reviewed" with the
  actual frequency or parameter (for example, "reviewed every 90 days").
- If the value is an organizational decision that is not recorded anywhere, insert a
  `[CONFIG_REQUIRED: ...]` placeholder instead of choosing one.
- Edits are overwritten by the next `generate` or `validate --fix` run; record them or propose the
  change in the template.

## 4. Keep human-action markers

Leave every `[WARNING: RMF TEAM ACTION REQUIRED: ...]` marker and `> [!IMPORTANT]` callout in place
(escalation phone numbers, training systems, signatures, and similar organizational details).

## Example requests

- "Review the 20 policy documents against my Terraform."
- "Check that each policy covers the XX-1 requirements."
- "Make the access control and incident response policies specific to our organization."
