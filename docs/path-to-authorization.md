# Path to authorization

This guide outlines how to achieve an Authorization to Operate on Google Cloud using the NIST Risk Management Framework alongside Stellar Engine Infrastructure as Code and authorization package baselines for Impact Level 5 H-H-X and FedRAMP High, with landing zone support for FedRAMP Moderate.

| Field | Value |
| :--- | :--- |
| Google contact | stellar-engine@google.com |
| Version | 1.0 |

## 1. Background

The NIST Risk Management Framework provides a repeatable seven-step lifecycle for managing organizational information security and privacy risk. Completing all seven steps is essential to achieving and maintaining system authorization.

Stellar Engine accelerates Google Cloud deployments for public sector agencies and Independent Software Vendors by pairing reusable Terraform landing zone stages with pre-mapped cybersecurity documentation. Combining the Risk Management Framework with Stellar Engine reduces manual compliance engineering and shortens the timeline to an Authorization to Operate.

## 2. Risk Management Framework

Each step below highlights key Risk Management Framework activities, linked authorization submission artifacts, and Authorizing Official responsibilities.

### Step 0 prepare

Complete the [Prepare](https://csrc.nist.gov/Projects/risk-management/about-rmf/prepare-step) activities to ready your organization for managing security and privacy risks:

- Designate internal or external personnel responsible for executing the Risk Management Framework across the system lifecycle.
- Publish an organizational [risk management strategy](https://nvlpubs.nist.gov/nistpubs/Legacy/SP/nistspecialpublication800-39.pdf) that defines your risk tolerance:
  - Document operational assumptions, constraints, risk tolerances, priorities, and trade-offs.
  - Establish executive governance for cybersecurity and privacy risk decisions across different loss or compromise scenarios.
- Establish an organizational [continuous monitoring strategy](https://nvlpubs.nist.gov/nistpubs/legacy/sp/nistspecialpublication800-137.pdf) that specifies control monitoring methods and frequencies.
- Define the system authorization boundary to scope the resources protected, managed, and authorized for operation:
  - Request the [Impact Level 5 Authorization Boundary](https://forms.gle/zdv7Gip4opmdhBqk7) template.
  - Request the [FedRAMP High Authorization Boundary](https://forms.gle/zdv7Gip4opmdhBqk7) template, which provides the FedRAMP High baseline while the FedRAMP Moderate boundary template is planned.
- Assess security and privacy risks at both the organization and system levels and update risk assessment results continuously.

### Step 1 categorize

[Categorize](https://csrc.nist.gov/Projects/risk-management/about-rmf/categorize-step) the system and the information it processes, stores, and transmits based on an impact analysis:

- Determine the system security categorization under [NIST SP 800-60](https://csrc.nist.gov/pubs/sp/800/60/v1/r1/final) according to the organizational impact of a loss of confidentiality, integrity, or availability:
  - Review the [Categorization References](./artifacts/categorization-references/).
  - Request the [System Security Plan Templates](https://forms.gle/zdv7Gip4opmdhBqk7) for IL5 H-H-X and FedRAMP High baselines; the FedRAMP Moderate template is planned.

### Step 2 select

[Select](https://csrc.nist.gov/Projects/risk-management/about-rmf/select-step) the NIST SP 800-53 control baseline that protects the system according to your risk assessment:

- Choose a control baseline that satisfies your regulatory, contractual, and strategic security and privacy requirements:
  - Identify the specific security and privacy controls needed to mitigate organizational risk.
  - Decide whether to adopt a predefined control baseline or assemble a custom initial control set.
- Tailor the selected control baseline to match your organization's operational environment and risk posture.
- Define a system-level continuous monitoring strategy that specifies change monitoring, ongoing risk assessments, and reporting cadences:
  - Evaluate the effectiveness of implemented controls and set the monitoring frequency for each control family.
  - Request the [Security Control Traceability Matrix Templates](https://forms.gle/zdv7Gip4opmdhBqk7) for IL5 H-H-X and FedRAMP High baselines; the FedRAMP Moderate template is planned.
  - Request the [Policies and Procedures Templates](https://forms.gle/zdv7Gip4opmdhBqk7) for IL5 H-H-X and FedRAMP High baselines; the FedRAMP Moderate templates are planned.

### Step 3 implement

[Implement](https://csrc.nist.gov/Projects/risk-management/about-rmf/implement-step) the selected controls and document how each control operates in your environment:

- Deploy the selected security and privacy controls or establish a documented implementation plan for pending controls.
- Update your security and privacy plans to reflect the actual implementation details whenever operational constraints require deviations from the initial design.

### Step 4 assess

[Assess](https://csrc.nist.gov/Projects/risk-management/about-rmf/assess-step) the implemented controls to verify that they operate as intended and produce the required security outcomes:

- Assign an internal assessment team or engage an independent third-party assessor to evaluate control implementation.
- Develop, review, and approve security and privacy assessment plans before testing begins.
- Execute control assessments according to the approved assessment plans.
- Produce a Security Assessment Report documenting findings and remediation recommendations.
- Draft a Plan of Action and Milestones detailing remediation schedules and corrective actions for open findings.

### Step 5 authorize

Submit the completed package so a senior official can make a risk-based decision to [Authorize](https://csrc.nist.gov/Projects/risk-management/about-rmf/authorize-step) system operation. Authorizing Officials rely on their security teams to translate technical control implementations into mission and business risk terms.

- Assemble the complete authorization package, including inherited control documentation from external cloud service providers, and submit it to the Authorizing Official.
- Support the Authorizing Official during package review and organizational risk determination.
- Obtain the formal authorization decision granting or denying approval to operate the information system.

### Step 6 monitor

Continuously [Monitor](https://csrc.nist.gov/Projects/risk-management/about-rmf/monitor-step) control effectiveness and environmental changes across the system lifecycle:

- Track infrastructure, software, and operational changes that affect system security or privacy posture.
- Execute ongoing risk responses based on continuous monitoring metrics, updated risk assessments, and open Plan of Action and Milestones items.
- Report current security and privacy posture regularly to organizational leadership and the Authorizing Official.

## 3. Additional ATO artifacts

Include these supporting artifacts in your authorization package as required by your authorizing agency:

- [Privacy Impact Assessment](./artifacts/PIA-PCIL-SORN/)
- [PII Confidentiality Impact Level](./artifacts/PIA-PCIL-SORN/)
- [System of Records Notice](./artifacts/PIA-PCIL-SORN/)
- [Hardware List](./artifacts/hw-sw-list/)
- [Software List](./artifacts/hw-sw-list/)
- [Ports, Protocols, and Services Management](./artifacts/ppsms/)

## 4. Operational considerations

Account for personnel, scanning, maintenance, and reciprocity requirements early in your authorization timeline:

- Assign U.S. citizens to administrative and authorization team roles when required by your target compliance regime.
- Validate workload compliance against Defense Information Systems Agency Security Technical Implementation Guides and Assured Compliance Assessment Solution scans alongside package documentation.
- Maintain authorization artifacts continuously throughout the ATO period, which typically spans up to three years, so major architecture changes, updated security mandates, and vulnerability remediations do not accumulate into a disruptive reauthorization effort.
- Plan for agency-specific authorization boundaries. While an ATO issued by one agency does not transfer automatically to another program, Authorizing Officials within the same agency or across the Department of Defense frequently accept reciprocity for previously authorized components.

## 5. Work breakdown structure

Use this example Work Breakdown Structure to sequence key milestones across an Authorization to Operate engagement:

| WBS | Action |
| :--- | :--- |
| 1.0 | Conduct kick-off meetings with stakeholders, including the Authorizing Official and security engineering leads. |
| 1.1 | Establish the authorization roadmap, schedule, milestones, and team responsibilities. |
| 1.2 | Obtain access to required governance and compliance accounts such as networks and eMASS. |
| 1.3 | Build the core Authorization to Operate deliverables. |
| 1.3.1 | Draft initial boundary artifacts including the architecture diagram, hardware and software lists, and System Security Plan. |
| 1.3.2 | Determine the system security categorization under FIPS 199. |
| 1.3.3 | Select the security control baseline under NIST SP 800-53 Revision 4 or Revision 5. |
| 1.3.4 | Implement technical and procedural controls with the platform and application teams. |
| 1.3.5 | Author system policies and procedures covering configuration management, incident response, and continuous monitoring. |
| 1.3.6 | Perform a control self-assessment and draft the Plan of Action and Milestones. |
| 1.3.7 | Submit the authorization package to the Authorizing Official and resolve review questions. |
| 1.4 | Receive the formal Authorization to Operate decision from the Authorizing Official. |

## 6. References

- [NIST SP 800-37 Revision 2](https://csrc.nist.gov/pubs/sp/800/37/r2/final), *Risk Management Framework for Information Systems and Organizations: A System Life Cycle Approach for Security and Privacy*, defines the seven-step Risk Management Framework lifecycle.
- [FIPS 199](https://csrc.nist.gov/pubs/fips/199/final), *Standards for Security Categorization of Federal Information and Information Systems*, establishes confidentiality, integrity, and availability impact categories alongside NIST SP 800-60.
- [FIPS 200](https://csrc.nist.gov/pubs/fips/200/final), *Minimum Security Requirements for Federal Information and Information Systems*, specifies the risk-based process for selecting baseline security controls.
- NIST SP 800-53 [Revision 4](https://csrc.nist.gov/pubs/sp/800/53/r4/upd3/final) and [Revision 5](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final), *Security and Privacy Controls for Federal Information Systems and Organizations*, catalog federal security and privacy controls.
- [Stellar Engine Technical Design Document](tdd.md) documents the reference landing zone architecture.
