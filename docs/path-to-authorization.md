[//]: # Tab Start: Tab 1

# Path to Authorization

_Impact Level 5 (H-H-X) & FedRAMP High_

**Created Date:**

**Last Modified: **

**Google POC(s):** stellar-engine@google.com

**Version:** 1.0

**Purpose:** The purpose of this document is to discuss the path to
authorization through the use of the Risk Management Framework along with
Stellar Engine and ATO-Ready Deployment Blueprints.

**Background:** The Risk Management Framework (RMF) provides a comprehensive,
flexible, and repeatable seven-step process designed to help organizations
manage their specific information security and privacy risks. All seven steps
are essential for the successful implementation of the RMF.

Stellar Engine accelerates Google Cloud deployments for Public Sector customers
by providing reusable Infrastructure as Code (IaC) and cybersecurity
documentation. This enables both customers and Independent Software Vendors
(ISVs) to deploy solutions more quickly and achieve Authorization to Operate
(ATO) on Google Cloud with greater efficiency.

By leveraging the RMF alongside Stellar Engine’s tools, organizations can
streamline their security and compliance efforts, ensuring faster, more secure
deployments in the cloud.

**RMF & Stellar Engine**:

_Red Text indicates MAJOR ARTIFACTS for ATO submission; Blue Text indicates
AO ACTIONS_

[**Step 0;
Prepare**](https://csrc.nist.gov/Projects/risk-management/about-rmf/prepare-step)**:**
Essential activities to **prepare** the organization to manage security and
privacy risks

- Designate an individual, or individuals, who will be assigned the task of
  executing the Risk Management Framework.
  - Roles and responsibilities may be assigned to personnel internal or
    external to your organization.
- Create a [risk management
  strategy](https://nvlpubs.nist.gov/nistpubs/Legacy/SP/nistspecialpublication800-39.pdf)
  for the organization that articulates your organizational risk tolerance.
  - Understand and document specific assumptions, constraints, risk
    tolerances, priorities, and trade-offs.
  - Make strategic-level decisions on how to manage cybersecurity and
    privacy risk.
  - There is no “correct level” of risk tolerance. The degree of risk
    tolerance is generally based on organizational culture, could be
    different for different types of losses or compromises, and can be
    influenced by risk tolerance of executives.
- Implement a [continuous monitoring
  strategy](https://nvlpubs.nist.gov/nistpubs/legacy/sp/nistspecialpublication800-137.pdf)
  for your organization to monitor security and privacy risk posture.
  - The strategy articulates frequency of control monitoring and how
    monitoring is to be conducted.
- Determine the scope of protection for the system and what falls into that
  scope.
  - Authorization boundaries establish the scope of systems to be protected,
    managed, and authorized for operation or use.
  - [Impact Level 5 Authorization
    Boundary](https://drive.google.com/drive/folders/1BLtoC59BMUueC9uwtWjBymJuQg2ku2m3)
  - [FedRAMP High Authorization
    Boundary](https://drive.google.com/drive/folders/16zsUdmzq_fK1BRFCrjgxsFRM23YVhjBa)
- Regularly assess the security and privacy risks at the organization level
  and system level. Update risk assessment results on an on-going basis.

[**Step 1;
Categorize**](https://csrc.nist.gov/Projects/risk-management/about-rmf/categorize-step):
**Categorize** the system and information processed, stored, and transmitted
based on the impact analysis

- [Categorize](https://csrc.nist.gov/pubs/sp/800/60/v1/r1/final) each system
  based on the impact to the organization if the confidentiality,
  availability, or integrity were to become compromised.
  - [FIPS 199](https://drive.google.com/drive/u/0/folders/1CMLkSzmdJTtld5-R7Ttks2uSGvv79Ikr)
  - [System Security Plan
    Templates](https://drive.google.com/drive/u/0/folders/1qV0Pu9EDnCEJpk0iKDodU_69BN96hEVr)

[**Step 2;
Select**](https://csrc.nist.gov/Projects/risk-management/about-rmf/select-step):
**Select** the set of NIST SP 800-53 controls to protect the system based on
risk assessment(s)

- Now that you have categorized the systems and assets, select the appropriate
  controls needed for protection.
  - The control baseline is a set of controls you can implement to meet
    strategic, legal, regulatory, or contractual security and privacy
    requirements and manage risk.
  - What security and privacy controls are needed to satisfy the
    organization’s security and privacy requirements and to adequately
    manage risk?
  - For our initial selection of controls, should we use a baseline
    (pre-defined) control selection approach, or should we select our own
    controls?
- After selecting an appropriate control baseline, tailor the controls to
  address the specific security and privacy requirements for the organization.
- Develop and implement a system-level strategy for monitoring control
  effectiveness.
  - This strategy defines how changes to the system and environment of
    operation are to be monitored, how risk assessments are conducted, and
    the reporting requirements.
  - How effective are the controls we have implemented? What is the
    frequency in which the controls are monitored?
  - [Security Control Traceability Matrix (SCTM)
    Templates](https://drive.google.com/drive/u/0/folders/13SahM7cIrE_jeA2G103yhGfpeXlBaZIq)
    (IL5 H-H-X and FedRAMP High Baselines)
  - [Policies and Procedures
    Templates](https://drive.google.com/drive/u/0/folders/1qnZ0N2BrRd8fF5u4h06H2Bbd4TxvLJvl)
    (IL5 HHX and FedRAMP High Baselines)

[**Step 3;
Implement**](https://csrc.nist.gov/Projects/risk-management/about-rmf/implement-step):
**Implement **the controls and document how controls are deployed

- Now that you have categorized systems by their risks and have selected
  appropriate controls, now is the time to implement the controls.
  - Have the security and privacy controls been implemented or is there an
    implementation plan in place?
- Update security and privacy plans to document necessary changes.
  - It’s not always feasible to implement controls as planned. Document
    necessary revisions that reflect how the control is implemented.

[**Step 4;
Assess**](https://csrc.nist.gov/Projects/risk-management/about-rmf/assess-step):
**Assess** to determine if the controls are in place, operating as intended, and
producing the desired results

- Select an individual or team responsible for conducting a control
  assessment.
  - Organizations can conduct self-assessments of controls or obtain the
    services of an independent assessor.
- Develop, review, and approve plans to assess implemented controls.
- Once plans are approved, conduct control assessments using the assessment
  plans.
- Prepare an assessment report documenting the findings and recommendations,
  such as plans for correcting deficiencies.
- Prepare the plan of action and milestones, which details remediation plans
  based on the findings and recommendations of the assessment report.

[**Step 5;
Authorize**](https://csrc.nist.gov/Projects/risk-management/about-rmf/authorize-step):
Senior official makes a risk-based decision to **authorize** the system (to
operate). Authorizing Officials (AOs) are executive-level leaders with demanding
schedules, which is why they typically rely on a team for information system
security. Each AO has a unique perspective on risk tolerance and while they are
not always technical subject matter experts, they are experts in the business or
mission area. To engage effectively, it’s important to translate security
controls in a way that aligns with and supports the success of their mission.

- Assemble the authorization package and submit it to the authorizing official
  for an authorization decision.
  - If security and privacy controls are being implemented by an external
    provider, ensure the provider makes available the information needed for
    your organization to make risk-based decisions.
- The authorizing official analyzes the information in the authorization
  package and finalizes the determination of risk to the organization.
- The authorizing official issues an authorization decision for the
  information system, indicating whether the system is authorized to operate
  or not.

[**Step 6;
Monitor**](https://csrc.nist.gov/Projects/risk-management/about-rmf/monitor-step):
Continuously **monitor** control implementation and risks to the system

- Monitor the system and environment of operation for changes that impact
  security and privacy.
- Using the results of the ongoing monitoring activities, risk assessments,
  and outstanding items in plans of action and milestones, determine the
  appropriate risk response and implement.
- Maintain ongoing communication with organizational leadership to convey the
  current security and privacy posture of the organization.

**Additional Artifacts for an ATO:**

- [Privacy Impact Assessment
  (PIA)](https://drive.google.com/drive/u/0/folders/18N1nBCZOaV2peJI4cEDJ0KSNyTo3s32o)
- [PII Confidentiality Impact Level
  (PCIL)](https://drive.google.com/drive/u/0/folders/18N1nBCZOaV2peJI4cEDJ0KSNyTo3s32o)
- [System of Records Notice
  (SORN)](https://drive.google.com/drive/u/0/folders/18N1nBCZOaV2peJI4cEDJ0KSNyTo3s32o)
- [Hardware
  List](https://drive.google.com/drive/u/0/folders/1fH-PDmfeJxf7b8BNkJVW39EHtUhYImUm)
- [Software
  List](https://drive.google.com/drive/u/0/folders/1fH-PDmfeJxf7b8BNkJVW39EHtUhYImUm)
- [Ports, Protocols, and Services Management
  (PPSM)](https://drive.google.com/drive/u/0/folders/1cvnyqHlwMINoxU2sZ61OQRWOKetSauuF)

**Things to Consider:**

- Team members should be U.S. Citizens.
- In addition to documentation, you may be required to ensure compliance with
  STIGs and ACAS scans.
- ATOs are for a set time frame with a max of 3 years, but that does not mean
  the work stops; packages will need to be maintained throughout the lifecycle
  of the ATO. Without continuous updates, there will be a herculean effort to
  make updates to address major changes, security requirement updates, or
  CVEs.
- An ATO with one agency/program does not necessarily transfer to another
  agency program. ATOs are agency specific, however, there is potential for
  reciprocity. Many AOs will accept reciprocity if the application, system, or
  component of the system was authorized by another government official,
  especially within the same agency or within DoD.

**Example Work Breakdown Structure (WBS) for ATO:**

| <strong>WBS #:</strong> | <strong>Action:</strong>                                                                                               |
| :---------------------- | :--------------------------------------------------------------------------------------------------------------------- |
| <strong>1.0</strong>    | Conduct kick-off meetings with stakeholders, including the Authorizing Official and their team.                        |
| <strong>1.1</strong>    | Roadmap with schedule , milestones, and responsibilities for the process                                               |
| <strong>1.2</strong>    | Obtain access to system accounts (networks, eMASS, etc.).                                                              |
| <strong>1.3</strong>    | Build ATO Deliverables                                                                                                 |
| <strong>1.3.1</strong>  | Build Initial Artifacts: Architecture Diagram; HW/SW List; System Security Plan                                        |
| <strong>1.3.2</strong>  | Determine categorization per FIPS 199                                                                                  |
| <strong>1.3.3</strong>  | Select controls based upon NIST SP 800-53 rev 4 or rev 5                                                               |
| <strong>1.3.4</strong>  | Assist team with implementation of controls                                                                            |
| <strong>1.3.5</strong>  | Write policies and procedures (Configuration Management, Incident Response Plan, Continuous Monitoring Strategy, etc.) |
| <strong>1.3.6</strong>  | Perform self-assessment, draft POA&M                                                                                   |
| <strong>1.3.7</strong>  | Submit package to AO, answer questions, and provide support as needed                                                  |
| <strong>1.4</strong>    | AO awards ATO                                                                                                          |

**References**

- [NIST SP 800-37 rev 2](https://csrc.nist.gov/pubs/sp/800/37/r2/final), _Risk
  Management Framework for Information Systems and Organizations: A System
  Life Cycle Approach for Security and Privacy_
  - Describes the RMF and provides guidelines for apply the RMF to
    information systems and organizations
- [Federal Information Processing Standards
  (FIPS) 199](https://csrc.nist.gov/pubs/fips/199/final), _Standards for
  Security Categorization of Federal Information and Information Systems_
  - Standard for categorizing information systems according to concerns for
    confidentiality, integrity, and availability. Used with SP 800-60, Guide
    for Mapping Types of Information and Information Systems to Security
    Categories
- [FIPS 200](https://csrc.nist.gov/pubs/fips/200/final), _Minimum Security
  Requirements for Federal Information and Information Systems_
  - Provides a risk-based process for selecting the security controls
    necessary to satisfy the minimum requirements for information and an
    information system
- NIST SP 800-53 [rev 4](https://csrc.nist.gov/pubs/sp/800/53/r4/upd3/final)
  and [rev 5](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final), _Security
  and Privacy Controls for Federal Information Systems and Organizations_
  - Catalog of security and privacy controls for information systems and
    organizations to protect against a diverse set of threats and risks.
- [Stellar Engine Technical Design
  Document](https://docs.google.com/document/d/15WMwslyCrkmuI7EutGBd7YXH3K8P3KrwzLOGcv-W4t8/edit?resourcekey=0-mjoA_PGM2MkIMPpr75SQbQ&tab=t.0)

[//]: # Tab End: Tab 1
