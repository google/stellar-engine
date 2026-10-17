# IA - Identification and Authentication Policy and Procedures

## Document Governance & Approval Baseline

| Governance Metric | Policy Standard & Specification |
| :--- | :--- |
| **Document Title** | Identification and Authentication Policy and Procedures |
| **NIST Control Family** | Identification and Authentication (IA) |
| **Primary NIST Benchmark** | NIST SP 800-63B (Authenticator Assurance Level 3 - AAL3 / FIDO2 / WebAuthn) |
| **Target System Name** | {{ SYSTEM_NAME }} ({{ SYSTEM_ABBREVIATION }}) |
| **Security Categorization** | {{ FIPS_199_CATEGORIZATION }} ({{ IMPACT_LEVEL }}) |
| **Governing Entity** | {{ ORGANIZATION }} |
| **Document Owner** | {{ ISSM_NAME }} ({{ ISSM_TITLE }}) |
| **Approval Authority** | {{ AO_NAME }} ({{ AO_TITLE }}) |
| **Review Frequency** | Annual (At least once every 365 days) and upon significant architectural changes |
| **Effective Date** | {{ DATE }} |
| **Policy Version** | {{ VERSION }} |

### Document Authorization Signatures

| Role / Authority | Designated Official | Signature & Date |
| :--- | :--- | :--- |
| **PREPARED BY:** | {{ PREPARED_BY }} | Signature: ______________________ Date: {{ DATE }} |
| **REVIEWED & RECOMMENDED BY:** | {{ ISSO_NAME }}<br>{{ ISSO_TITLE }}, {{ ORGANIZATION }} | Signature: ______________________ Date: {{ DATE }} |
| **REVIEWED & RECOMMENDED BY:** | {{ ISSM_NAME }}<br>{{ ISSM_TITLE }}, {{ ORGANIZATION }} | Signature: ______________________ Date: {{ DATE }} |
| **APPROVED BY:** | {{ SO_NAME }}<br>{{ SO_TITLE }}, {{ ORGANIZATION }} | Signature: ______________________ Date: {{ DATE }} |

### Document Change Record

| Date | Version | Author / Prepared By | Changes Made / Section(s) Description |
| :--- | :--- | :--- | :--- |
| {{ DATE }} | {{ VERSION }} | {{ PREPARED_BY }} | Initial formal baseline institutionalization under NIST SP 800-53 Rev. 5 / {{ COMPLIANCE_BASELINE }} governance. |

### Program Roles & Responsibilities Matrix

| Organizational Role | Assigned Authority | Primary Policy Enforcement & Compliance Responsibilities |
| :--- | :--- | :--- |
| **Authorizing Official (AO)** | {{ AO_NAME }} ({{ AO_TITLE }}) | Formally approves policy statements, risk tolerance thresholds, Exception-to-Policy (ETP) memorandums, and official ATO decisions. |
| **System Owner (SO)** | {{ SO_NAME }} ({{ SO_TITLE }}) | Ensures system operations align with policy requirements, manages operational resources, and approves operational change requests. |
| **ISSM** | {{ ISSM_NAME }} ({{ ISSM_TITLE }}) | Oversees enterprise cybersecurity policy enforcement, manages annual policy review cadences, and maintains compliance evidence. |
| **ISSO** | {{ ISSO_NAME }} ({{ ISSO_TITLE }}) | Conducts continuous security monitoring, audits system configurations, oversees technical countermeasures, and tracks POA&M remediation. |
| **DevSecOps Engineers** | Platform Engineering Team | Implements automated technical controls via Terraform Infrastructure as Code (IaC), CI/CD pipelines, and cloud platform configurations. |

> [!NOTE]
> **Policy Scope & Automation Level**
> This document defines the enterprise security policy and implementation procedures for **Identification and Authentication** under **NIST SP 800-53 Rev. 5 (IA)**.
> Technical infrastructure controls are automatically provisioned and enforced via **{{ SYSTEM_NAME }}** Terraform blueprints.
> Operational rules or contact details requiring manual confirmation are highlighted with RMF Team Callouts.


## 1. Overview

Federal agencies and organizations cannot protect the confidentiality, integrity, and availability of information in today's highly networked systems environment without ensuring that all people involved in using and managing IT:

1. Understand their roles and responsibilities related to the organizational mission;
2. Understand the organization's IT security policy, procedures, and practices; and
3. Have at least adequate knowledge of the various management, operational, and technical controls required and available to protect the IT resources for which they are responsible.

The purpose of this Identification and Authentication Policy is to establish the requirements for uniquely identifying and authenticating users, devices, and services before they access {{ SYSTEM_NAME }}, and for managing the identifiers and authenticators used to do so.

This policy addresses the Identification and Authentication (IA) family requirements of NIST Special Publication 800-53 Revision 5, "Security and Privacy Controls for Information Systems and Organizations." A detailed compliance matrix is provided in Appendix A, "Detailed Compliance Matrix."

The Identification and Authentication Policy encompasses all {{ ORGANIZATION }} users who have access to {{ SYSTEM_NAME }}. This policy outlines the framework for establishing, implementing, and maintaining identification and authentication in alignment with applicable {{ GOVERNANCE_REGIME }} guidelines (NIST SP 800-53, FedRAMP, and applicable federal and state regulations), and is consistent with applicable laws, executive orders, directives, regulations, policies, standards, and guidelines. It applies to employees, contractors, and third-party users who handle sensitive information or operate within the {{ ORGANIZATION }} {{ SYSTEM_NAME }} information technology infrastructure.

{{ ORGANIZATION }} management is committed to the requirements of this policy and provides the resources needed to implement them. The ISSM ({{ ISSM_NAME }}) manages the development, documentation, and dissemination of this policy and its procedures, and coordinates their implementation with the Authorizing Official, System Owner, ISSO, and other organizational entities identified in the Program Roles & Responsibilities Matrix.

This policy and its procedures are reviewed and updated at least annually and following significant changes to {{ SYSTEM_NAME }} or its operating environment, security or privacy incidents, assessment or audit findings, or changes in applicable laws, executive orders, directives, regulations, policies, standards, or guidelines.


## 2. Policy and Procedures

This policy and its procedures address the system-level controls in the IA family that are implemented within {{ ORGANIZATION }} {{ SYSTEM_NAME }}. They are disseminated to all {{ ORGANIZATION }} personnel and roles responsible for developing the organization's identification, authentication, authorization, and privacy capabilities.

The {{ ORGANIZATION }} PMO reviews, updates, and redisseminates this policy and its procedures under the direction of the ISSM, at the frequency and following the events defined in Section 1. Each review considers changes to the enterprise architecture documentation; system security plan; privacy plan; records of system security and privacy plan reviews and updates; security and privacy architecture and design documentation; risk assessments and risk assessment results; control assessment documentation; and other relevant documents or records.



### 2.1 Google Cloud Inherited Controls & Shared Responsibility Boundary

- **Google Inherited Controls**: Google Cloud provides Titan Security Keys, hardware FIPS 140-2 Level 3 Cloud HSM authentication infrastructure (`IA-7`), and Google Cloud Identity authentication gateways (`IA-2`).
- **Customer Implementation Responsibilities**: {{ ORGANIZATION }} is responsible for enforcing Multi-Factor Authentication (MFA) via FIDO2 WebAuthn / Security Keys (`IA-2`, `IA-8`), configuring SAML Single Sign-On (SSO) federation, and setting password complexity policies (`IA-5`).

## 3. Identification and Authentication (Organizational Users)

{{ ORGANIZATION }} {{ SYSTEM_NAME }} users include employees or individuals that organizations deem to have equivalent status of employees (e.g., contractors, guest researchers). All {{ ORGANIZATION }} {{ SYSTEM_NAME }} users must be uniquely identified and authenticated before they are granted access.

{{ SYSTEM_NAME }} provides an RBAC schema for authorizing, accessing, and auditing all infrastructure components deployed. {{ ORGANIZATION }} {{ SYSTEM_NAME }} is responsible for managing group memberships of individual identities. When access is granted through a group or role, each user is individually authenticated before access to the group-held role or resource is granted.


## 4. Multi-Factor Authentication to Privileged and Non-Privileged Accounts

{{ IDENTITY_ACCESS_IMPLEMENTATION }}


### 4.1 IAM Principles

- IAM Policy should be defined as Infrastructure-as-code (IaC) and enforced by code that's reviewed and submitted using Terraform.

  - Latitude will be given to development projects to accelerate the rate of development.

  - No human should have permissions to create or modify cloud resources in User Acceptance Test (UAT) or Quality Assurance (QA) environments that immediately precede production in the Continuous Integration / Continuous Delivery (CI/CD) pipeline.

  - No human should have permissions to create or modify cloud resources in production.

  - The Cloud Resource Manager access required to execute Terraform code will be assigned to a unique service account.

    - This service account will only be used by the CI/CD pipeline for terraform apply actions.

- Human access

  - Access must be granted to groups, not individual users.

  - Access will be granted based on a minimalized set of curated roles.

- Machine access

  - Individual Service Accounts will be defined for each microservice.

  - Downloadable Service Account keys will not be used and their creation should be disabled by organization policy.

  - Access will be granted based on the principle of least privilege, with only necessary functionality granted for the microservice.

  - The organization policy constraint that disables automatic role grants to default service accounts (`iam.automaticIamGrantsForDefaultServiceAccounts`) should be enforced, so that default service accounts are not automatically granted the Editor role.


## 5. Access to Accounts

To reduce the likelihood of compromising authenticators or credentials that are stored on {{ SYSTEM_NAME }}, {{ ORGANIZATION }} requires users to authenticate using a device separate from the system that the user is attempting to access.

Access to {{ ORGANIZATION }} {{ SYSTEM_NAME }} accounts shall be resistant to replay attacks through replay-resistant techniques, including protocols that use cryptographic authenticators such as {{ MFA_MECHANISM }}.


### 5.1 Acceptance of PIV Credentials

{{ ORGANIZATION }} {{ SYSTEM_NAME }} accepts and electronically verifies Personal Identity Verification (PIV)-compliant credentials (FIPS 201) for organizational users. Certificates are validated against the {{ PKI_TRUST_TYPE }} trust chain configured in {{ IDENTITY_PROVIDER }}.


## 6. Device Identification and Authentication

{{ ORGANIZATION }} uses Cloud Identity BeyondCorp Device Manager to implement device identification and authentication.

Cloud Identity BeyondCorp Device Manager contains a list of authorized devices that are able to access {{ SYSTEM_NAME }}.

Approved devices will be identified before, during, and after an established connection to {{ SYSTEM_NAME }}.


### 6.1 Cryptographic Bidirectional Authentication

Devices within {{ ORGANIZATION }} {{ SYSTEM_NAME }} will undergo cryptographic bidirectional authentication to establish a secure connection. This provides stronger protection to validate the identity of other devices for connections that are of greater risk.


## 7. Identifier Management

Individual, group, role, and device identifiers are managed by the {{ ORGANIZATION }} Cloud Identity / Directory Service administrators within the {{ ORGANIZATION }} organization. Identifiers are assigned only after explicit, documented authorization from {{ ORGANIZATION }} or its designee (see Section 7.1) and are managed within the {{ ORGANIZATION }} Cloud Identity / Directory Service.

Identifiers are disabled, never deleted. As such, the reuse of identifiers for entities other than those to which they were originally assigned is prohibited. The {{ ORGANIZATION }} Cloud Identity / Directory Service will not permit the duplication of an identifier.


### 7.1 Identify User Status

All {{ ORGANIZATION }} identifiers are required to be unique. Identifiers must also distinguish contractors, government personnel, and foreign nationals, using the following identifier formats:

- Contractor: must contain ".ctr" within the identifier

- Foreign nationals: must contain a country code, e.g., "UK", within the identifier

- Government: no extension. All accounts without an extension are considered government employees

Note: Contractors who are also foreign nationals are identified as both, e.g., user.sample.ctr.uk@{{ ORGANIZATION_DOMAIN }}

> [!IMPORTANT]
> [WARNING: RMF TEAM ACTION REQUIRED: Verify and update operational contact/procedure details in this section.]
> Prior to an identifier being distributed to the end user, it must be authorized by at least the {{ ORGANIZATION }} {{ SYSTEM_NAME }} program manager and the ISSM.

{{ ORGANIZATION }} {{ SYSTEM_NAME }} is configured to disable identifiers after 35 days of inactivity through implementation of the applicable STIG requirements.


### 7.2 Attribute Maintenance and Protection

{{ ORGANIZATION }} will maintain the attributes for each uniquely identified individual, device, or service; the attributes will be stored in the Centralized Audit & Identity Store.


## 8. Authenticator Management

Authentication uses passwords, tokens, biometrics, or, for multi-factor authentication, a combination of these. {{ ORGANIZATION }} does not use default authenticators.

Administrative procedures require that individuals are verified, trained, and sign acknowledgements that they will take specific controls to protect authenticators.

Authenticator change management includes protection from unauthorized disclosure, issuance, distribution, revocation, and updating or re-issuing authenticators when they expire, are compromised, are lost, are damaged, or are otherwise refreshed.


### 8.1 Password-based Authentication

<!-- IF DOD_ENCLAVE -->
Password-based authentication requirements apply to passwords used on {{ ORGANIZATION }} {{ SYSTEM_NAME }}, regardless of whether they are used in single-factor or multi-factor authentication. Long passwords or passphrases are preferred, with a minimum length of 15 characters that mix uppercase letters, lowercase letters, numbers, and special characters, including at least one of each. {{ ORGANIZATION }} {{ SYSTEM_NAME }} enforces password complexity by requiring that at least 50% of the characters change when a password is changed, as configured through STIG/SRG requirements.
<!-- ENDIF -->
<!-- IF NOT DOD_ENCLAVE -->
Password-based authentication requirements apply to memorized secrets used on {{ ORGANIZATION }} {{ SYSTEM_NAME }}, regardless of whether they are used in single-factor or multi-factor authentication. In accordance with NIST SP 800-63B and FedRAMP IA-5(1) guidance, memorized secrets must be at least 12 characters (passphrases up to 64 characters supported), screened against commonly used or compromised password lists, and must not impose arbitrary character-composition rules or periodic rotation schedules in the absence of a known compromise.
<!-- ENDIF -->

Password changes will be required when passwords expire in accordance with {{ ORGANIZATION }} policy or when they are directly or indirectly compromised. During a password change, automated tools will be offered to assist the user in selecting strong password authenticators. Passwords will be rejected if they appear on the list of commonly used, expected, or compromised passwords, which is updated no less than monthly.

Passwords will be stored only using an approved salted key derivation function with a keyed hash.

Any application or service requiring transmission of passwords will ensure that passwords are transmitted over cryptographically protected channels.


### 8.2 Public Key-based Authentication

{{ ORGANIZATION }} uses public key and hardware-token-based authentication ({{ MFA_MECHANISM }}) with an authoritative public key infrastructure ({{ PKI_TRUST_TYPE }}). The {{ ORGANIZATION }} {{ SYSTEM_NAME }} PKI authentication process maintains certificate validation and revocation checking (CRL/OCSP) to support path discovery and validation. Authenticated identities are mapped to the {{ ORGANIZATION }} {{ SYSTEM_NAME }} account of the individual or group for public key-based authentication.


### 8.3 Protection of Authenticators

Authenticators used in support of {{ ORGANIZATION }} {{ SYSTEM_NAME }} are protected by both the individual and the system in which the authenticator resides. For systems that contain multiple security categories of information without reliable physical or logical separation between categories, authenticators used to grant access to {{ ORGANIZATION }} {{ SYSTEM_NAME }} are protected commensurate with the highest security category of information processed on the systems.


### 8.4 No Embedded Unencrypted Static Authenticators

{{ ORGANIZATION }} will ensure that unencrypted static authenticators are not embedded in applications or other forms of static storage.


### 8.5 Multiple System Accounts

{{ ORGANIZATION }} will train individuals to know the importance of having different authenticators for different systems. When individuals have accounts on multiple systems and use the same authenticators, there is a risk that a compromise of one account may lead to the compromise of other accounts. {{ ORGANIZATION }} will update the Rules of Behavior and Access Agreements to mitigate the risk of multiple system accounts with shared authenticators.


### 8.6 Expiration of Cached Authenticators

{{ ORGANIZATION }} shall prohibit the use of cached authenticators after 12 hours (or per organization policy).


### 8.7 Managing Content of PKI Trust Stores

{{ ORGANIZATION }} uses Centralized Certificate Authority / Cloud KMS PKI Store to manage the content of PKI trust stores installed across {{ SYSTEM_NAME }}.


### 8.8 In-person or Trusted External Party Authenticator Issuance

When physical authenticators are used, {{ ORGANIZATION }} will issue them in person or through a trusted external party.


## 9. Authentication Feedback

{{ ORGANIZATION }} {{ SYSTEM_NAME }} shall ensure authentication feedback is obscured when entering in password information. Obscuring the feedback of authentication information includes, for example, displaying asterisks when users type passwords into input devices, or displaying feedback for a very limited time before fully obscuring it.


## 10. Cryptographic Module Authentication

Authentication mechanisms may be required within a cryptographic module to authenticate an operator accessing the module and to verify that the operator is authorized to assume the requested role and perform services within that role.

{{ ORGANIZATION }} {{ SYSTEM_NAME }} is configured to implement mechanisms for authentication to a cryptographic module that meet the requirements of applicable federal laws, Executive Orders, directives, policies, regulations, standards, and guidance for such authentication through implementation of the applicable STIG/SRG requirements.


## 11. Identification and Authentication (Non-organizational Users)

{{ ORGANIZATION }} {{ SYSTEM_NAME }} is not a publicly accessible system. All users are screened and validated through {{ ORGANIZATION }} Access Control policy prior to accounts being established.


### 11.1 Acceptance of PIV Credentials from Other Agencies

External PKI PIV credentials allow trusted non-{{ ORGANIZATION }} users to access {{ ORGANIZATION }} as required and approved by {{ ORGANIZATION }}. PIV credentials are those credentials issued by federal agencies that conform to FIPS Publication 201 and supporting guidelines. {{ ORGANIZATION }} shall be configured to accept and electronically verify approved external PKI credentials ({{ PKI_TRUST_TYPE }}) in accordance with federal and organizational directives.


### 11.2 Acceptance of External Authenticators

{{ ORGANIZATION }} shall accept only external authenticators that are NIST-compliant and shall document and maintain a list of accepted external authenticators authorized for use on {{ ORGANIZATION }} {{ SYSTEM_NAME }}. Acceptance of only NIST-compliant external authenticators applies to {{ ORGANIZATION }} {{ SYSTEM_NAME }} components that are accessible to the public (e.g., public-facing websites). External authenticators are issued by nonfederal government entities and are compliant with SP 800-63B.

> [!IMPORTANT]
> [WARNING: RMF TEAM ACTION REQUIRED: Verify and update the list of accepted external authenticators for your organization.]

Below is the list of accepted external authenticators authorized for use on {{ ORGANIZATION }} {{ SYSTEM_NAME }}:

- Federal PIV/CAC / FIDO2 Credential ({{ PKI_TRUST_TYPE }})
- FIPS 140-2/3 Validated Hardware Security Key (FIDO2 / WebAuthn / Security Key)
- NIST SP 800-63B Compliant Federated Identity Provider (SAML 2.0 / OpenID Connect)


### 11.3 Use of Defined Profiles

{{ ORGANIZATION }} defines profiles for identity management based on open identity management standards consistent with NIST SP 800-63-4, Digital Identity Guidelines.


## 12. Service Identification and Authentication

{{ ORGANIZATION }} {{ SYSTEM_NAME }} must ensure that services are uniquely identified and authenticated before establishing communications with devices, users, or other services or applications.


## 13. Adaptive Authentication

{{ ORGANIZATION }} requires individuals accessing {{ SYSTEM_NAME }} to adjust their authentication method under the following situations or circumstances:

- Access attempts originating from atypical geographic locations or unrecognized IP addresses;
- Anomalous logon behavior, such as off-hours access or high-frequency login failures;
- Requests for elevated privileges or access to high-sensitivity security resources.


## 14. Re-authentication

Consistent with Zero Trust requirements, {{ ORGANIZATION }} requires re-authentication of individuals in certain situations, including when roles, authenticators, or credentials change, when the security posture of the {{ ORGANIZATION }} {{ SYSTEM_NAME }} changes, when security categories of systems change, when the execution of privileged functions occurs, after a fixed time, or periodically.


## 15. Identity Proofing

As part of the {{ ORGANIZATION }} {{ SYSTEM_NAME }} account provisioning process, users requiring {{ ORGANIZATION }} {{ SYSTEM_NAME }} access will be required to provide proof of identity as part of the identity proofing process. {{ ORGANIZATION }} proof of identity will be waived for users possessing verified credentials ({{ MFA_MECHANISM }}) because proofing was performed during initial credential issuance. Identity proofing is the process of collecting, validating, and verifying a user's identity information for the purposes of establishing credentials for accessing {{ ORGANIZATION }} {{ SYSTEM_NAME }}. Standards and guidelines specifying identity assurance levels for identity proofing include NIST SP 800-63-4 and SP 800-63A-4.

Within {{ ORGANIZATION }} {{ SYSTEM_NAME }}, identities are resolved to a unique individual.


### 15.1 Supervisor Authorization

> [!IMPORTANT]
> [WARNING: RMF TEAM ACTION REQUIRED: Verify and update operational contact/procedure details in this section.]
> {{ ORGANIZATION }} requires System Owner / ISSO approval for new user registration.


### 15.2 Identity Evidence

Personnel requiring system access to {{ ORGANIZATION }} {{ SYSTEM_NAME }} will be required to present appropriate identification to the registration authority responsible for system access. For authorized credential holders, this is accomplished through the certified identity issuance and registration process ({{ MFA_MECHANISM }}).


### 15.3 Identity Evidence Validation and Verification

Personnel requiring access to {{ ORGANIZATION }} {{ SYSTEM_NAME }} must submit two forms of valid identification as part of the process for acquiring credentials ({{ MFA_MECHANISM }}) which is required for access to certain {{ ORGANIZATION }} IT platforms. Acceptable forms of identification are specified in NIST SP 800-63A-4 consistent with federal and organizational identity requirements.


### 15.4 In-person Validation and Verification

> [!IMPORTANT]
> [WARNING: RMF TEAM ACTION REQUIRED: Verify and update operational contact/procedure details in this section.]
> The validation and verification of identity evidence must be conducted in person before System Owner / ISSO.


### 15.5 Address Confirmation

{{ ORGANIZATION }} requires that a registration code or notice of proofing be delivered through an out-of-band channel to verify the physical or digital user address of record.



## Appendix A – Detailed Compliance Matrix

The following table provides detailed traceability between the policy implementation statements in this document, the authoritative NIST SP 800-53 Rev. 5 control requirements, DoD CCIs, and the technical/governance enforcement mechanisms active across {{ SYSTEM_NAME }}.


| CTRL ID | CTRLTITLE | REQUIRED {{ GRC_STANDARD_LABEL }} STANDARD | DOCREF | ENFORCEMENT MECHANISM |
| :--- | :--- | :--- | :--- | :--- |
| IA-01 | Policy and Procedures | Develop, document, and disseminate the IA policy and procedures to personnel with identification, authentication, authorization, and privacy responsibilities; designate the ISSM to manage them; review and update them at least annually and following significant system changes (including IdP migration), security or privacy incidents, assessment or audit findings, or changes in applicable laws, regulations, or guidance. (CCI-000757, CCI-000758, CCI-000759, CCI-000762, CCI-000763, CCI-004031, CCI-004032, CCI-004033, CCI-004034, CCI-004035, CCI-004036, CCI-004037, CCI-004038, CCI-004039, CCI-004040, CCI-004041, CCI-004042, CCI-004043, CCI-004044) | Section 1 & 2 | Formal annual review workflow managed by the ISSM with the {{ ORGANIZATION }} ICAM Lead and AO; published in {{ RMF_GOVERNANCE_SYSTEM }}; incident-driven update triggers. |
| IA-02 | Identification and Authentication (Organizational Users) | Uniquely identify and authenticate all organizational users before granting access; prohibit shared accounts and static passwords. (CCI-000764) | Section 3 | {{ IDENTITY_PROVIDER }} SAML 2.0 / OIDC federation to Cloud Identity; unique {{ USER_IDENTIFIER_TYPE }} assignment; no shared accounts. |
| IA-02(01) | Multi-factor Authentication to Privileged Accounts | Enforce hardware-based Multi-Factor Authentication (MFA) for all privileged accounts accessing local, network, and remote sessions. (CCI-000765) | Section 4 | Mandatory {{ MFA_MECHANISM }} authentication; smart card / hardware security key enforcement in {{ IDENTITY_PROVIDER }}. |
| IA-02(02) | Multi-factor Authentication to Non-privileged Accounts | Enforce hardware-based Multi-Factor Authentication (MFA) for all non-privileged accounts accessing network and remote sessions. (CCI-000766) | Section 4 | Phishing-resistant MFA ({{ MFA_MECHANISM }}) enforced for all console, dashboard, and portal access; SMS/password OTP prohibited. |
| IA-02(05) | Individual Authentication with Group Authentication | Require users to be individually authenticated before granting access to shared accounts or resources when shared accounts or authenticators are employed. (CCI-004045) | Section 3 | No shared accounts are issued; access to group-held roles (e.g., {{ SYSTEM_NAME }}-NetworkAdmins) requires individual {{ IDENTITY_PROVIDER }} authentication; Cloud Audit Logs attribute each action to the individual user. |
| IA-02(06) | Access to Accounts —separate Device | Enforce authentication using a physically separate token ({{ MFA_MECHANISM }}) meeting FIPS 140-2/140-3 standards for all accounts. (CCI-004046, CCI-004047, CCI-004048) | Section 5 | FIPS-compliant hardware tokens / smart cards ({{ MFA_MECHANISM }}); hardware token reader requirements on all administrative endpoints. |
| IA-02(08) | Access to Accounts — Replay Resistant | Implement replay-resistant authentication mechanisms for all privileged and remote access transactions. (CCI-001941) | Section 5 | TLS 1.2 minimum / TLS 1.3 with ephemeral Diffie-Hellman; FIPS 140-3 BoringCrypto (CMVP Cert #5104, retrieved 2026-10-15); signed SAML/OIDC nonces. |
| IA-02(12) | Acceptance of PIV Credentials | Accept {{ MFA_MECHANISM }} and Federal PIV credentials compliant with FIPS 201-3 and NIST SP 800-63B (AAL3). (CCI-001953, CCI-001954) | Section 5.1 | {{ IDENTITY_PROVIDER }} certificate trust chain; {{ PKI_TRUST_TYPE }} certificate validation. |
| IA-03 | Device Identification and Authentication | Uniquely identify and authenticate all devices (routers, appliances, endpoints) before establishing network connections. (CCI-000777, CCI-000778, CCI-001958) | Section 6 | Cloud Identity BeyondCorp Device Manager authorized-device list for endpoints; dedicated Cloud Router BGP ASNs, point-to-point interconnect IP allocations, and 802.1Q VLAN attachments. |
| IA-03(01) | Cryptographic Bidirectional Authentication | Enforce cryptographically based bidirectional mutual authentication on all local, network, and remote device connections. (CCI-001959, CCI-001967) | Section 6.1 | IEEE 802.1AE MACsec (gcm-aes-xpn-256) and IKEv2 IPsec VPN mutual certificate/pre-shared key authentication. |
| IA-04 | Identifier Management | Authorize identifier assignment via ISSM/ISSO; prevent reuse of user identifiers indefinitely (at least 2 years). (CCI-001970, CCI-001971, CCI-001972, CCI-001973, CCI-001974, CCI-001975) | Section 7 | System authorization gating; Enterprise Directory user provisioning; automated identifier reuse lockout. |
| IA-04(04) | Identify User Status | Uniquely identify user affiliation status (contractor vs. civilian/military) and nationality within identifier formats. (CCI-000800, CCI-000801) | Section 7.1 | Standardized identifier formats synced via SCIM: contractor (.ctr), foreign national (country code, e.g., .uk), and government (no extension), e.g., user.sample.ctr.uk@{{ ORGANIZATION_DOMAIN }}. |
| IA-04(09) | Attribute Maintenance and Protection | Manage and protect user, device, and service attributes in authoritative enterprise IdAM storage ({{ IDENTITY_PROVIDER }}). (CCI-004051, CCI-004052) | Section 7.2 | SCIM protocol automated sync from {{ IDENTITY_PROVIDER }} to Cloud Identity Workforce Pool over encrypted TLS 1.2 minimum (TLS 1.3 where supported). |
| IA-05 | Authenticator Management | Manage authenticator lifecycle; refresh credentials every 3 years (1 yr ctr)<!-- IF DOD_ENCLAVE -->, passwords 60 days<!-- ENDIF -->; rotate keys every 90 days. (CCI-000176, CCI-000182, CCI-000183, CCI-000184, CCI-001544, CCI-001610, CCI-001980, CCI-001981, CCI-001984, CCI-001985, CCI-001988, CCI-001990, CCI-002042, CCI-004053, CCI-004054, CCI-004055, CCI-004056) | Section 8 | Enterprise PKI lifecycle; automated 90-day Cloud KMS key rotation; immediate revocation on compromise. |
| IA-05(01) | Password-based Authentication | <!-- IF DOD_ENCLAVE -->Enforce DoD password complexity rules (15+ chars, 4 character sets, 50% change) where passwords are used by exception.<!-- ENDIF --><!-- IF NOT DOD_ENCLAVE -->Enforce NIST SP 800-63B memorized-secret standards (minimum 12 characters, compromised-password screening, no arbitrary composition or periodic rotation rules) where passwords are used.<!-- ENDIF --> (CCI-000197, CCI-004057, CCI-004058, CCI-004059, CCI-004060, CCI-004061, CCI-004062, CCI-004063, CCI-004064, CCI-004065, CCI-004066, CCI-004067) | Section 8.1 | Linux PAM configuration on bastions; {{ IDENTITY_PROVIDER }} password protection against compromised/common password lists. |
| IA-05(02) | Public Key-based Authentication | For public key-based authentication, enforce authorized access to the private key and map the authenticated identity to the individual or group account; when PKI is used, validate certificates by building and verifying a certification path to an accepted trust anchor, including certificate status checking, and keep a local cache of revocation data. (CCI-000185, CCI-000186, CCI-000187, CCI-004068) | Section 8.2 | Private keys held on {{ MFA_MECHANISM }} hardware tokens; certificate path validation with real-time OCSP/CRL verification in {{ IDENTITY_PROVIDER }} and web proxies; authenticated identities mapped to individual or group accounts; rejection of expired/revoked {{ PKI_TRUST_TYPE }} certificates. |
| IA-05(06) | Protection of Authenticators | Protect authenticators and pre-shared keys against unauthorized disclosure using FIPS 140-2 Level 3 Cloud KMS HSM CMEK. (CCI-000201) | Section 8.3 | Google Cloud Secret Manager; Cloud KMS HSM encryption; least-privilege IAM secret access. |
| IA-05(07) | No Embedded Unencrypted Static Authenticators | Prohibit hardcoded plaintext credentials, keys, or tokens in source code, Terraform scripts, and images. (CCI-004069) | Section 8.4 | Automated CI/CD pre-commit secret scanning (Gitleaks); static analysis gates blocking unencrypted credentials. |
| IA-05(08) | Multiple System Accounts | Prohibit credential reuse across different security domains, classification levels, or between standard and admin roles. (CCI-000204, CCI-001621) | Section 8.5 | Segregation of standard accounts from dedicated admin-* accounts; training and policy enforcement against password reuse. |
| IA-05(13) | Expiration of Cached Authenticators | Invalidate and purge all cached authenticators and session tokens immediately upon user logoff or session termination. (CCI-002006, CCI-002007) | Section 8.6 | Automated token revocation in Cloud Identity / IAP upon logoff; immediate flush of cached credentials on bastions. |
| IA-05(14) | Managing Content of PKI Trust Stores | Authorize and manage the content of PKI trust stores, including root and intermediate certificates, under configuration control. (CCI-002008) | Section 8.7 | CCB configuration control of {{ PKI_TRUST_TYPE }} trust bundles deployed to container images and Linux bastion operating systems. |
| IA-05(16) | In-person or Trusted External Party Authenticator Issuance | Require that PKI hardware tokens ({{ MFA_MECHANISM }}) be issued in person or by a trusted external party before a certified Registration Authority (RA/TA), with authorization by [CONFIG_REQUIRED: personnel or roles who authorize authenticator issuance]. (CCI-004074, CCI-004075, CCI-004076, CCI-004077) | Section 8.8 | Formal in-person identity proofing and biometric validation at certified issuance facilities. |
| IA-06 | Authentication Feedback | Obscure authentication feedback during credential entry to prevent shoulder surfing and credential harvesting. (CCI-000206) | Section 9 | Masked input characters on console login portals; generic error messages on authentication failure. |
| IA-07 | Cryptographic Module Authentication | Employ NIST FIPS 140-2/140-3 validated cryptographic modules that authenticate operators before executing crypto functions. (CCI-000803) | Section 10 | Google BoringCrypto (FIPS 140-3 Level 1, CMVP Cert #4735) for software cryptographic primitives; hardware-enforced FIPS 140-2 Level 3 Cloud HSM module boundaries. |
| IA-08 | Identification and Authentication (Non-organizational Users) | Uniquely identify and authenticate non-organizational users, and processes acting on their behalf, after sponsorship and vetting. (CCI-000804) | Section 11 | {{ ORGANIZATION }} sponsorship; Tier 3/5 background vetting; federated authentication via Federal PIV Trust Bridge. |
| IA-08(01) | Acceptance of PIV Credentials from Other Agencies | Accept and electronically verify PIV-compliant credentials from other federal agencies through established trust bridges conforming to FIPS 201-3. (CCI-002009, CCI-002010) | Section 11.1 | Cross-agency PKI trust mapping configured within {{ IDENTITY_PROVIDER }} federation profiles. |
| IA-08(02) | Acceptance of External Authenticators | Accept only NIST-compliant external authenticators ({{ MFA_MECHANISM }} tokens); document and maintain the list of accepted external authenticators; prohibit unverified commercial MFA. (CCI-004083, CCI-004084) | Section 11.2 | {{ IDENTITY_PROVIDER }} Conditional Access policies restricting external authenticators strictly to {{ PKI_TRUST_TYPE }} tokens. |
| IA-08(04) | Use of Defined Profiles | Ensure external identity federation complies with the Federal / Public Sector Identity Federation Profile and NIST SP 800-63B standards. (CCI-004085, CCI-004086) | Section 11.3 | SAML 2.0 / OIDC federation configurations adhering to Federal Identity Federation Profile specifications. |
| IA-09 | Service Identification and Authentication | Uniquely identify and authenticate all automated services, CI/CD pipelines, and microservices using keyless WIF. (CCI-002018, CCI-002021, CCI-002022) | Section 12 | Workload Identity Federation (WIF) OIDC token exchange; prohibition of static service account JSON keys. |
| IA-10 | Adaptive Authentication | Enforce adaptive authentication requirements across {{ SYSTEM_NAME }} in accordance with NIST SP 800-53 Rev. 5 IA-10. (CCI-002033, CCI-002034, CCI-002035) | Section 3 | Enforced via Google Cloud infrastructure controls, Terraform configuration baselines, and ISSM/ISSO governance verification. |
| IA-11 | Re-authentication | Require full re-authentication ({{ MFA_MECHANISM }}) after 15-minute inactivity, prior to JIT privilege elevation, or when accessing {{ SENSITIVITY_CLASSIFICATION }}. (CCI-002036, CCI-002038) | Section 14 | 15-minute idle session disconnect; Google Cloud Privileged Access Manager (PAM) re-authentication prompts; IAP timeout rules. |
| IA-12 | Identity Proofing | Identity proof users who require accounts for logical access at the identity assurance level required by NIST SP 800-63A; resolve each identity to a unique individual; collect, validate, and verify identity evidence. (CCI-004092, CCI-004093, CCI-004094, CCI-004095, CCI-004096, CCI-004097) | Section 15 | Identity proofing during {{ SYSTEM_NAME }} account provisioning (IAL2, Appendix B); reliance on proofing performed at {{ MFA_MECHANISM }} credential issuance; unique-individual identity resolution in {{ IDENTITY_PROVIDER }}. |
| IA-12(01) | Supervisor Authorization | Require supervisor or sponsor authorization in the registration process for an account with logical access. (CCI-004098) | Section 15.1 | Documented System Owner / ISSO approval of each new user registration before account creation. |
| IA-12(02) | Identity Evidence | Require evidence of individual identification to be presented to the registration authority. (CCI-004099) | Section 15.2 | Identity evidence presented to the registration authority during the certified {{ MFA_MECHANISM }} issuance and registration process. |
| IA-12(03) | Identity Evidence Validation and Verification | Require presented identity evidence to be validated and verified through the methods specified in NIST SP 800-63A, including two forms of valid identification. (CCI-004100, CCI-004101, CCI-004102, CCI-004103) | Section 15.3 | Validation and verification of two forms of identification per NIST SP 800-63A during {{ MFA_MECHANISM }} credential issuance. |
| IA-12(04) | In-person Validation and Verification | Require that the validation and verification of identity be performed in person before a designated registration authority for high-assurance credential issuance. (CCI-004104, CCI-004105) | Section 12 | In-person identity proofing before an authorized Registration Authority (RA) prior to issuing PIV/CAC or hardware FIDO2/WebAuthn authenticators ({{ MFA_MECHANISM }}). |
| IA-12(05) | Address Confirmation | Provide an addressee of record with a notification of registration via an out-of-band channel to verify intent and detect fraudulent enrollment. (CCI-004106) | Section 12 | Out-of-band enrollment confirmation notices sent to verified organizational contact addresses upon credential issuance or registration changes. |



## Appendix B – Digital Identity & Authenticator Assurance Levels

In accordance with NIST SP 800-63B, {{ ORGANIZATION }} enforces the following Digital Identity and Authenticator Assurance Levels across {{ SYSTEM_NAME }}:

| Identity & Authentication Category | Required Assurance Level | Technical Implementation Standard |
| :--- | :--- | :--- |
| **Identity Assurance Level (IAL)** | **IAL2** | Government PIV/CAC / Hardware Authenticator, Identity Verification, and Background Investigation (`PS-2`, `PS-3`). |
| **Authenticator Assurance Level (AAL)** | **AAL3** | Multi-Factor Authentication via FIDO2 / WebAuthn Hardware Security Keys (`IA-2`). |
| **Federated Assertion Level (FAL)** | **FAL3** | Cryptographically Signed SAML 2.0 / OpenID Connect (OIDC) Tokens via Google Workspace / Cloud Identity. |
| **Service Account Authentication** | **FAL3** | Short-Lived Workload Identity Federation (WIF) OAuth 2.0 Tokens (No long-lived JSON keys allowed). |
