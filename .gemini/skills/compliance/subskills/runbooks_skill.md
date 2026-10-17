---
name: compliance-runbooks
description: Reference sub-skill specification for reviewing tactical cloud incident response runbooks in Markdown and Word (.docx) formats.
---
<!-- skip boilerplate check -->

# Review guide: incident response runbooks (`runbooks_skill.md`)

> **Reference Sub-Skill:** This document is a component reference specification under `<SKILL_DIR>/subskills/` and is invoked through the parent `compliance` skill ([../SKILL.md](../SKILL.md)).

Use after the workflow in [../SKILL.md](../SKILL.md) has run. The generator fills each template in
`<SKILL_DIR>/templates/runbooks/` with project IDs, key names, and other values from the inventory and writes
it to `<TARGET_FOLDER>/ato_artifacts/Incident_Response_Runbooks/` as `.md` and/or `.docx`. Values
it cannot find render as `[NOT DETERMINED FROM SOURCE]`.

| File | ID |
| :--- | :--- |
| `IR_IAM_Compromised_Credentials_Runbook` | IR-IAM-001 |
| `IR_Compute_Resource_Compromise_Runbook` | IR-COMP-001 |
| `IR_KMS_CMEK_Compromise_Runbook` | IR-CMEK-001 |
| `IR_Network_Intrusion_Runbook` | IR-NET-001 |
| `IR_VPC_Service_Controls_Violation_Runbook` | IR-VPC-001 |
| `Incident_Response_Runbook_Template` (blank, for new scenarios) | IR-CUSTOM-001 |

## 1. Check commands and resource names

- In the containment and eradication sections, every `gcloud` command must use subcommands and
  flags that exist. Check with `gcloud <command> --help` or the Cloud SDK reference.
- Project IDs, service account emails, key rings, keys, buckets, and subnets must match
  `system_inventory.json` and the Terraform. Replace `[NOT DETERMINED FROM SOURCE]` only with values
  found in the code or supplied by the user.
- Destructive steps (for example, `gcloud kms keys versions destroy`) must state who approves
  them and what they affect.

## 2. Check detection sources

- FedRAMP, state and local, and commercial systems may use Security Command Center findings and
  Cloud Logging queries as detection sources.
- DoD IL4/IL5 systems: detection must not depend on Security Command Center inside the boundary.
  Signals should come from Cloud Logging sinks that export to the accredited CSSP or an external
  SIEM, unless `security_operations.allow_unaccredited_scc_in_il5` records an AO exception.

## 3. Check reporting timelines and recipients

The escalation sections list reporting timelines by organization. Verify each one against the
authority that applies to the system, and correct or flag any that you cannot confirm:

- DoD components: CJCSM 6510.01B and the procedures of the component's CSSP.
- Federal civilian agencies: CISA's Federal Incident Notification Guidelines.
- Defense contractors: DFARS 252.204-7012 (reports go to DoD through the DIBNet portal).
- The agency's own incident response policy and the IR policy document in this package.

US-CERT's functions are now part of CISA; do not list US-CERT as a separate recipient. Internal
notification of the Authorizing Official, ISSM, and System Owner belongs in every runbook.

## 4. Writing a new runbook

Copy `Incident_Response_Runbook_Template.md` for scenarios the five runbooks do not cover (for
example, database exfiltration or ransomware). NIST SP 800-61 Rev. 3 (April 2025) replaced Rev. 2;
it organizes incident response around the NIST Cybersecurity Framework 2.0 functions rather than
Rev. 2's four-phase lifecycle. Cite Rev. 3 in new runbooks.

## Example requests

- "Check that the runbook commands match my Google Cloud resources."
- "Verify the incident reporting timelines and CSSP routing in the runbooks."
- "Add a runbook for database exfiltration."
