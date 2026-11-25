# ADR-0000: Short descriptive title

Use this template to record durable architecture decisions, security boundary changes, and time-bounded Exception to Policy justifications across your landing zone. Store accepted records alongside your infrastructure repository so reviewers and Authorizing Officials can trace every deviation back to its technical rationale.

| Field | Value |
| :--- | :--- |
| Status | `DRAFT` \| `UNDER REVIEW` \| `APPROVED` \| `APPROVED WITH CONDITIONS` \| `REJECTED` \| `SUPERSEDED` |
| Date | `YYYY-MM-DD` |
| Author | `<name-and-role>` |
| Reviewers | `<architect-and-security-reviewers>` |
| Related issue | `ISSUE-0000` |
| Expiration date | `N/A` or `YYYY-MM-DD` for time-bounded exceptions |
| Supersedes | `N/A` or `ADR-XXXX` |
| Superseded by | `N/A` or `ADR-YYYY` |

## 1. Context and problem

Describe the operational requirement, compliance mandate, or environmental drift that prompts this decision in two to four concise sentences.

- Summarize the exact problem statement and affected landing zone stages, folders, or workload projects.
- List hard technical, regulatory, cost, or schedule constraints such as FedRAMP High or Impact Level 5 control requirements, regional data boundaries, or service quota ceilings.
- Link relevant guardrail reviews from the [Guardrails review rubric and test plan](../guardrails-rubric-and-test-plan.md) or authorization steps from the [Path to authorization](../path-to-authorization.md).

## 2. Proposed architecture delta

Contrast the current baseline with the proposed target state so reviewers can inspect the exact blast radius.

### Current baseline

- Describe the existing resource topology, IAM boundary, encryption posture, and network egress path.
- Reference the authoritative Terraform stage, module, or diagram file path.

### Target state

- Describe every resource, organization policy, IAM Deny rule, VPC Service Controls entry, or routing path added, modified, or removed.
- Identify whether existing resources require recreation, state moves, or in-place updates.

## 3. Options considered

Evaluate at least two viable implementation options alongside the status quo so the decision record demonstrates objective trade-off analysis.

### Option 1 proposed solution

Summarize the recommended architecture in one short paragraph.

- Advantages include measurable security, reliability, or operational gains.
- Trade-offs include implementation effort, service limits, or temporary operational overhead.

### Option 2 alternative approach

Summarize the primary alternative considered and why reviewers ruled it out.

- Advantages include any lower cost or simpler migration path.
- Trade-offs include compliance gaps, maintenance burden, or scalability limits.

### Option 3 status quo

State the concrete risk or mission impact of making no change.

## 4. Well-architected evaluation

Assess cross-cutting impacts and compensating controls across the five Google Cloud Architecture Framework pillars.

| Pillar | Impact and risk analysis | Compensating controls and guardrails |
| :--- | :--- | :--- |
| Security and compliance | Identity scope, VPC Service Controls impact, CMEK or Cloud HSM posture, NIST SP 800-53 control delta | Least-privilege IAM, custom constraints, IAM Deny policies, audit log alerts |
| Reliability | Failure domains, regional redundancy, Recovery Time Objective and Recovery Point Objective impact | Multi-zone deployment, automated backups, rollback sequence |
| Cost optimization | Estimated monthly spend change and licensing impact | Budgets, autoscaling bounds, storage lifecycle policies |
| Operational excellence | Terraform state ownership, CI/CD workflow changes, Day-2 runbook impact | Automated validation, dry-run telemetry, documented rollback steps |
| Performance efficiency | Latency, throughput, and Google Cloud quota consumption | Quota pre-checks, sizing tiers, regional colocation |

## 5. Decision and rationale

Populate this section during or immediately after Architecture Review Board or Authorizing Official review.

| Decision field | Value |
| :--- | :--- |
| Outcome | `APPROVED` \| `APPROVED WITH CONDITIONS` \| `REJECTED` \| `DEFERRED` |
| Decision date | `YYYY-MM-DD` |
| Approver role | `<board-or-authorizing-official-role>` |

Summarize why reviewers selected this option over the alternatives, including any risk acceptance scope or mandatory sunset trigger.

## 6. Follow-up actions

Track conditional requirements, compensating control implementations, and exception expiration milestones to closure.

| Item | Action or condition | Owner | Target date | Status |
| :--- | :--- | :--- | :--- | :--- |
| 1 | Validate dry-run audit logs and Policy Simulator output in non-production | `<owner-role>` | `YYYY-MM-DD` | `OPEN` |
| 2 | Update Terraform modules, tests, and Plan of Action and Milestones entries | `<owner-role>` | `YYYY-MM-DD` | `OPEN` |
