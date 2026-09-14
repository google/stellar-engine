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

Identification and authentication policies are high level requirements that contribute to security and privacy assurance within {{ ORGANIZATION }} {{ SYSTEM_NAME }}.

The purpose of this Identification and Authentication policy is to address the Identification and Authentication (IA) security controls of organizational entities supporting {{ ORGANIZATION }} {{ SYSTEM_NAME }}.  Identity and authentication is accomplished through the use of passwords, tokens, biometrics or, in the case of multifactor authentication, some combination thereof.

This document complies with the following requirements from NIST Special Publication 800-53 Revision 5, "Security and Privacy Controls for Federal Information Systems and Organizations". A detailed compliance matrix can be found in Appendix A, “Detailed Compliance Matrix”.


## 2. Policy and Procedures

Identification and authentication policies and procedures address the system-level controls in the IA family that are implemented within {{ ORGANIZATION }} {{ SYSTEM_NAME }}. This policy is to be disseminated to all {{ ORGANIZATION }} personnel and roles responsible for the development of {{ ORGANIZATION }} Identification, Authentication, Authorization, and privacy.

These policies and procedures will be reviewed, updated, and disseminated no less than annually by the {{ ORGANIZATION }} PMO. Updates will consider changes required due to updates to the enterprise architecture documentation; system security plan; privacy plan; records of system security and privacy plan reviews and updates; security and privacy architecture and design documentation; risk assessments; risk assessment results; control assessment documentation; and other relevant documents or records.

Federal Agencies and organizations cannot protect the confidentiality, integrity, and availability of information in today’s world without ensuring that all people involved in using and managing IT:

- Understand their roles and responsibilities related to the mission;

- Understand the IT security policy, procedures, and practices; and

- Have adequate knowledge of the various management, operational, and technical controls required and available to protect the IT resources for when they are responsible.



### 2.1 Google Cloud Platform (GCP) Inherited Controls & Shared Responsibility Boundary

- **Google Inherited Controls**: Google Cloud provides Titan Security Keys, hardware FIPS 140-3 HSM authentication infrastructure (`IA-7`), and Google Cloud Identity authentication gateways (`IA-2`).
- **Customer Implementation Responsibilities**: {{ ORGANIZATION }} is responsible for enforcing Multi-Factor Authentication (MFA) via FIDO2 WebAuthn / Security Keys (`IA-2`, `IA-8`), configuring SAML Single Sign-On (SSO) federation, and setting password complexity policies (`IA-5`).

## 3. Identification and Authentication (Organizational Users)

{{ ORGANIZATION }} {{ SYSTEM_NAME }} users include employees or individuals that organizations deem to have equivalent status of employees (e.g., contractors, guest researchers). All {{ ORGANIZATION }} {{ SYSTEM_NAME }} users must be uniquely identified.

{{ SYSTEM_NAME }} provides an RBAC schema for authorizing, accessing, and auditing all infrastructure components deployed. {{ ORGANIZATION }} {{ SYSTEM_NAME }} is responsible for managing group memberships of individual identities.


### 3.1 Google Cloud Platform (GCP) Inherited Controls & Shared Responsibility Boundary

- **Google Inherited Controls**: Google Cloud provides Titan Security Keys, hardware FIPS 140-3 HSM authentication infrastructure (`IA-7`), and Google Cloud Identity authentication gateways (`IA-2`).
- **Customer Implementation Responsibilities**: {{ ORGANIZATION }} is responsible for enforcing Multi-Factor Authentication (MFA) via FIDO2 WebAuthn / Security Keys (`IA-2`, `IA-8`), configuring SAML Single Sign-On (SSO) federation, and setting password complexity policies (`IA-5`).

## 4. Multi-Factor Authentication to Privileged and Non-Privileged Accounts

{{ IDENTITY_ACCESS_IMPLEMENTATION }}


#### 4.1.1 IAM Principles

- IAM Policy should be defined as Infrastructure-as-code (IaC) and enforced by code that’s reviewed and submitted using Terraform.

  - Latitude will be given to development projects to accelerate the rate of development.

  - No human should have permissions to create or modify cloud resources in User Acceptance Test (UAT) or Quality Assurance (QA) environments that immediately precede production in the Continuous Integration / Continuous Development (CI/CD) pipeline.

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

  - Disable automatic role grants to default service accounts (iam.automaticIamGrantsForDefaultServiceAccounts ) should be enabled as organization policy , this will remove the editor role from the default service accounts.


#
### 4.2 Google Cloud Platform (GCP) Inherited Controls & Shared Responsibility Boundary

- **Google Inherited Controls**: Google Cloud provides Titan Security Keys, hardware FIPS 140-3 HSM authentication infrastructure (`IA-7`), and Google Cloud Identity authentication gateways (`IA-2`).
- **Customer Implementation Responsibilities**: {{ ORGANIZATION }} is responsible for enforcing Multi-Factor Authentication (MFA) via FIDO2 WebAuthn / Security Keys (`IA-2`, `IA-8`), configuring SAML Single Sign-On (SSO) federation, and setting password complexity policies (`IA-5`).

## 5. Access to Accounts

In order to reduce the likelihood of compromising authenticators or credentials that are stored on {{ SYSTEM_NAME }}, {{ ORGANIZATION }} require users to authenticate using a separate device from the system to which the user is attempting to access.

Access to {{ ORGANIZATION }} {{ SYSTEM_NAME }} accounts shall be resistant to replay attacks using replay resistant techniques including protocols that use cryptographic authenticators such as {{ MFA_MECHANISM }}.


## 6. Device Identification and Authentication

{{ ORGANIZATION }} utilizes Cloud Identity BeyondCorp Device Manager to implement the use of device identification and authentication.

Cloud Identity BeyondCorp Device Manager contains a list of authorized devices that are able to access {{ SYSTEM_NAME }}.

Approved devices will be identified before, during, and after an established connection to {{ SYSTEM_NAME }}.


### 6.1 Cryptographic Bidirectional Authentication

Devices within {{ ORGANIZATION }} {{ SYSTEM_NAME }} will undergo cryptographic bidirectional authentication to establish a secure connection. This provides stronger protection to validate the identity of other devices for connections that are of greater risk.


## 7. Identifier Management

Individual, group, role, and device identifiers are managed by the {{ ORGANIZATION }} Cloud Identity / Directory Service administrators within the {{ ORGANIZATION }} organization. Identifiers are assigned by receiving explicit, documented authorization from the {{ ORGANIZATION }} level or designate and are managed within the {{ ORGANIZATION }} Cloud Identity / Directory Service.

Identifiers are disabled, never deleted. As such, the reuse of identifiers for entities other than which they were originally assigned is prohibited. The {{ ORGANIZATION }} Cloud Identity / Directory Service will not permit the duplication of an identifier.


### 7.1 Identifier User Status

All {{ ORGANIZATION }} identifiers are required to be unique. Identifiers must also distinguish between contractor, government, and nationality. This is configured through the format of identifiers are described below:

- Contractor – must contain “.ctr” within the identifier

- Foreign Nationals – must contain country prefix, i.e. “UK” within the identifier

- Government – no extension. All accounts without an extension are considered Government employees

Note: Contractors who are also foreign nationals are identified as both, e.g., user.sample.ctr.uk@{{ ORGANIZATION_DOMAIN }}

> [!IMPORTANT]
> [WARNING: RMF TEAM ACTION REQUIRED: Verify and update operational contact/procedure details in this section.]
> Prior to an identifier being distributed to the end user, it must be authorized by at least the {{ ORGANIZATION }} {{ SYSTEM_NAME }} program manager and the ISSM.

{{ ORGANIZATION }} {{ SYSTEM_NAME }} is configured to disable identifiers after 35 days of inactivity through implementation of the appropriate STIG requirements.


### 7.2 Attribute Maintenance and Protection

{{ ORGANIZATION }} will maintain the attributes for each uniquely identified individual, device, or service; the attributes will be stored in Centralized Audit & Identity Store.


## 8. Authenticator Management

{{ ORGANIZATION }} does not use default authenticators.

Administrative procedures require that individuals are verified, trained, and sign acknowledgements that they will take specific controls to protect authenticators.

Authenticator change management includes protection from unauthorized disclosure, issuance, distribution, revocation, and updating or re-issuing authenticators when they expire, are compromised, are lost, are damaged, or are otherwise refreshed.


### 8.1 Password Based Authentication

Password based authentication used on {{ ORGANIZATION }} {{ SYSTEM_NAME }} applies to passwords regardless of whether they are used in single-factor or multi-factor authentication. Long passwords or passphrases are preferable with a minimum length of 12-character mix of uppercase letters, lowercase letters, numbers, and special characters including at least one of each for {{ ORGANIZATION }} {{ SYSTEM_NAME }}.  {{ ORGANIZATION }} {{ SYSTEM_NAME }} is configured to enforce password complexity by enforcing that at least 50% of the minimum password length is changed and validated through the use of STIG/SRG requirements.

Password changes will be required when they expire in accordance with {{ ORGANIZATION }} policy or when they are directly or indirectly compromised. During a password change, automated tools will be offered to assist the user in selecting strong password authenticators. Passwords will be rejected if they appear on the list of commonly used, expected, or compromised passwords that is updated no less than monthly.

Passwords will only be stored on an approved salted key derivation function, using a keyed hash.

Any application or service requiring transmission of passwords will ensure that passwords are transmitted over cryptographically protected channels.


### 8.2 Public Key-Based Authentication

{{ ORGANIZATION }} utilizes public key and hardware-token-based authentication ({{ MFA_MECHANISM }}), leveraging authoritative public key infrastructure ({{ PKI_TRUST_TYPE }}). The {{ ORGANIZATION }} {{ SYSTEM_NAME }} PKI authentication process maintains certificate validation and revocation checking (CRL/OCSP) to support path discovery and validation. Authenticated identities are mapped to the {{ ORGANIZATION }} {{ SYSTEM_NAME }} account of the individual or group for public key-based authentication.


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

When physical authenticators are utilized, {{ ORGANIZATION }} will issue them in-person or by a trusted external party.


## 9. Authentication Feedback

{{ ORGANIZATION }} {{ SYSTEM_NAME }} shall ensure authentication feedback is obscured when entering in password information. Obscuring the feedback of authentication information includes, for example, displaying asterisks when users type passwords into input devices, or displaying feedback for a very limited time before fully obscuring it.


## 10. Cryptographic Module Authentication

Authentication mechanisms may be required within a cryptographic module to authenticate an operator accessing the module and to verify that the operator is authorized to assume the requested role and perform services within that role.

{{ ORGANIZATION }} {{ SYSTEM_NAME }} is configured to implement mechanisms for authentication to a cryptographic module that meet the requirements of applicable federal laws, Executive Orders, directives, policies, regulations, standards, and guidance for such authentication through implementation of the appropriate STIG/SRG requirements.


## 11. Identification and Authentication (Non-Organizational Users)

{{ ORGANIZATION }} {{ SYSTEM_NAME }} is not a publicly accessible system. All users are screened and validated through {{ ORGANIZATION }} Access Control policy prior to accounts being established.


### 11.1 Acceptance of PIV Credentials from Other Agencies

External PKI PIV credentials allow trusted non-{{ ORGANIZATION }} users to access {{ ORGANIZATION }} as required and approved by {{ ORGANIZATION }}. PIV credentials are those credentials issued by federal agencies that conform to FIPS Publication 201 and supporting guidelines.  {{ ORGANIZATION }} shall be configured to accept and electronically verify approved external PKI credentials ({{ PKI_TRUST_TYPE }}) in accordance with federal and organizational directives.


### 11.2 Acceptance of External Authenticators

{{ ORGANIZATION }} shall accept only external authenticators that are NIST-compliant and document and maintain a list of accepted external authenticators authorized for use on {{ ORGANIZATION }} {{ SYSTEM_NAME }}. Acceptance of only NIST-compliant external authenticators applies to {{ ORGANIZATION }} {{ SYSTEM_NAME }} that are accessible to the public (e.g. public facing websites).  External authenticators are issued by nonfederal government entities and are compliant with SP 800-63B.

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


## 14. Re-Authentication

Consistent with Zero Trust requirements, {{ ORGANIZATION }} requires re-authentication of individuals in certain situations, including when roles, authenticators, or credentials change, when the security posture of the {{ ORGANIZATION }} {{ SYSTEM_NAME }} changes, when security categories of systems change, when the execution of privileged functions occurs, after a fixed time, or periodically.


## 15. Identity Proofing

As part of the {{ ORGANIZATION }} {{ SYSTEM_NAME }} account provisioning process, users requiring {{ ORGANIZATION }} {{ SYSTEM_NAME }} access will be required to provide proof of identity as part of the Identity proofing process. {{ ORGANIZATION }} proof of identity will be waived for users possessing verified credentials ({{ MFA_MECHANISM }}) as it was performed during initial credential issuance.  Identity proofing is the process of collecting, validating, and verifying a user’s identity information for the purposes of establishing credentials for accessing {{ ORGANIZATION }} {{ SYSTEM_NAME }}.  Standards and guidelines specifying identity assurance levels for identity proofing include SP 800-63-3 and SP 800-63A.

Within {{ ORGANIZATION }} {{ SYSTEM_NAME }}, identities are resolved to a unique individual.


### 15.1 Supervisor Authorization

> [!IMPORTANT]
> [WARNING: RMF TEAM ACTION REQUIRED: Verify and update operational contact/procedure details in this section.]
> {{ ORGANIZATION }} requires System Owner / ISSO approval for new user registration.


### 15.2 Identity Evidence

Personnel requiring system access to {{ ORGANIZATION }} {{ SYSTEM_NAME }} will be required to present appropriate identification to the registration authority responsible for system access.  For authorized credential holders, this is accomplished through the certified identity issuance and registration process ({{ MFA_MECHANISM }}).


### 15.3 Identity Evidence Validation and Verification


Personnel requiring access to {{ ORGANIZATION }} {{ SYSTEM_NAME }} must submit two forms of valid identification as part of the process for acquiring credentials ({{ MFA_MECHANISM }}) which is required for access to certain {{ ORGANIZATION }} IT platforms. Acceptable forms of identification are specified in NIST SP 800-63A consistent with federal and organizational identity requirements.


### 15.4 In-Person Validation and Verification

> [!IMPORTANT]
> [WARNING: RMF TEAM ACTION REQUIRED: Verify and update operational contact/procedure details in this section.]
> The validation and verification of identity evidence must be conducted in-person before System Owner / ISSO.


### 15.5 Address Confirmation

{{ ORGANIZATION }} requires that a registration code or notice of proofing be delivered through an out-of-band channel to verify the physical or digital user address of record.



## Appendix A – Detailed Compliance Matrix

The following table provides detailed traceability between the policy implementation statements in this document, the authoritative NIST SP 800-53 Rev. 5 control requirements, DoD CCIs, and the technical/governance enforcement mechanisms active across {{ SYSTEM_NAME }}.


| CTRL ID | CTRLTITLE | REQUIRED eMASS STANDARD | DOCREF | ENFORCEMENT MECHANISM |
| :--- | :--- | :--- | :--- | :--- |
| IA-01 | Policy and Procedures | Develop, document, disseminate to all personnel, and review/update annually (or upon IdP migration/incidents) IA policy and procedures. (CCIs: 000757, 000758, 000759, 000762, 000763, 004031, 004032, 004033, 004034, 004035, 004036, 004037, 004038, 004039, 004040, 004041, 004042, 004043, 004044) | Section 2 | Formal annual review workflow by {{ ORGANIZATION }} ICAM Lead/ISSM/AO; published in eMASS; incident-driven update triggers. |
| IA-02 | Identification and Authentication (Organizational Users) | Uniquely identify and authenticate all organizational users before granting access; prohibit shared accounts and static passwords. (CCIs: 000764) | Section 3 | {{ IDENTITY_PROVIDER }} SAML 2.0 / OIDC federation to Cloud Identity; unique {{ USER_IDENTIFIER_TYPE }} assignment; no shared accounts. |
| IA-02(01) | Multi-Factor Authentication to Privileged Accounts | Enforce hardware-based Multi-Factor Authentication (MFA) for all privileged accounts accessing local, network, and remote sessions. (CCIs: 000765) | Section 4 | Mandatory {{ MFA_MECHANISM }} authentication; smart card / hardware security key enforcement in {{ IDENTITY_PROVIDER }}. |
| IA-02(02) | Multi-Factor Authentication to Non-Privileged Accounts | Enforce hardware-based Multi-Factor Authentication (MFA) for all non-privileged accounts accessing network and remote sessions. (CCIs: 000766) | Section 4 | Phishing-resistant MFA ({{ MFA_MECHANISM }}) enforced for all console, dashboard, and portal access; SMS/password OTP prohibited. |
| IA-02(05) | Individual Authentication with Group Accounts | Ensure individual identity is authenticated and audited when group/role access is utilized; maintain strict attribution. (CCIs: 004045) | Section 4 | {{ IDENTITY_PROVIDER }} individual user mapping to IAM groups (e.g. {{ SYSTEM_NAME }}-NetworkAdmins); Cloud Audit Log individual attribution. |
| IA-02(06) | Access to Accounts: Separate Device | Enforce authentication using a physically separate token ({{ MFA_MECHANISM }}) meeting FIPS 140-2/140-3 standards for all accounts. (CCIs: 004046, 004047, 004048) | Section 5 | FIPS-compliant hardware tokens / smart cards ({{ MFA_MECHANISM }}); hardware token reader requirements on all administrative endpoints. |
| IA-02(08) | Access to Accounts: Replay Resistant | Implement replay-resistant authentication mechanisms for all privileged and remote access transactions (CCIs: 001941) | Section 5 | TLS 1.3 with ephemeral Diffie-Hellman; FIPS 140-3 BoringCrypto (Cert #4407); signed SAML/OIDC nonces. |
| IA-02(12) | Acceptance of PIV Credentials | Accept {{ MFA_MECHANISM }} and Federal PIV credentials compliant with FIPS 201-3 and NIST SP 800-63B (AAL3) (CCIs: 001953, 001954) | Section 5 | {{ IDENTITY_PROVIDER }} certificate trust chain; {{ PKI_TRUST_TYPE }} certificate validation. |
| IA-03 | Device Identification and Authentication | Uniquely identify and authenticate all devices (routers, appliances, endpoints) before establishing network connections (CCIs: 000777, 000778, 001958) | Section 6 | Dedicated Cloud Router BGP ASNs, point-to-point interconnect IP allocations, and 802.1Q VLAN attachments. |
| IA-03(01) | Cryptographic Bidirectional Authentication | Enforce cryptographically based bidirectional mutual authentication on all local, network, and remote device connections (CCIs: 001959, 001967) | Section 6 | IEEE 802.1AE MACsec (gcm-aes-xpn-256); BGP MD5/SHA-256 peering authentication; IKEv2 IPsec VPN mutual auth. |
| IA-04 | Identifier Management | Authorize identifier assignment via ISSM/ISSO; prevent reuse of user identifiers indefinitely (at least 2 years) (CCIs: 001970, 001971, 001972, 001973, 001974, 001975) | Section 7 | System authorization gating; Enterprise Directory user provisioning; automated identifier reuse lockout. |
| IA-04(04) | Identify User Status | Uniquely identify user affiliation status (contractor vs. civilian/military) and nationality within identifier formats (CCIs: 000800, 000801) | Section 7 | Standardized identity email/UPN formatting (.civ@{{ ORGANIZATION_DOMAIN }}, .ctr@{{ ORGANIZATION_DOMAIN }}, .ctr.foreign@{{ ORGANIZATION_DOMAIN }}) synced via SCIM. |
| IA-04(09) | Attribute Maintenance and Protection | Manage and protect user, device, and service attributes in authoritative enterprise IdAM storage ({{ IDENTITY_PROVIDER }}) (CCIs: 004051, 004052) | Section 7 | SCIM protocol automated sync from {{ IDENTITY_PROVIDER }} to Cloud Identity Workforce Pool over encrypted TLS 1.3. |
| IA-05 | Authenticator Management | Manage authenticator lifecycle; refresh credentials every 3 years (1 yr ctr), passwords 60 days; rotate keys every 90 days (CCIs: 000176, 000182, 000183, 000184, 001544, 001610, 001980, 001981, 001984, 001985, 001988, 001990, 002042, 004053, 004054, 004055, 004056) | Section 8 | Enterprise PKI lifecycle; automated 90-day Cloud KMS key rotation; immediate revocation on compromise. |
| IA-05(01) | Password-Based Authentication | Enforce DoD password complexity rules (15+ chars, 4 character sets, 50% change) where passwords are exceptionally used (CCIs: 000197, 004057, 004058, 004059, 004060, 004061, 004062, 004063, 004064, 004065, 004066, 004067) | Section 8 | Linux PAM configuration on bastions; {{ IDENTITY_PROVIDER }} password protection against compromised/common password lists. |
| IA-05(02) | PKI-Based Authentication | Enforce PKI certificate validation, real-time CRL checking, and OCSP status verification for all authenticators (CCIs: 000185, 000186, 000187, 004068) | Section 8 | Real-time OCSP/CRL verification in {{ IDENTITY_PROVIDER }} and web proxies; rejection of expired/revoked {{ PKI_TRUST_TYPE }} certificates. |
| IA-05(06) | Protection of Authenticators | Protect authenticators and pre-shared keys against unauthorized disclosure using FIPS 140-3 Cloud KMS HSM CMEK (CCIs: 000201) | Section 8 | Google Cloud Secret Manager; Cloud KMS HSM encryption; least-privilege IAM secret access. |
| IA-05(07) | No Embedded Unencrypted Authenticators | Strictly prohibit hardcoded plaintext credentials, keys, or tokens in source code, Terraform scripts, and images (CCIs: 004069) | Section 8 | Automated CI/CD pre-commit secret scanning (Gitleaks); static analysis gates blocking unencrypted credentials. |
| IA-05(08) | Multiple System Accounts | Prohibit credential reuse across different security domains, classification levels, or between standard and admin roles (CCIs: 000204, 001621) | Section 8 | Segregation of standard accounts from dedicated admin-* accounts; training and policy enforcement against password reuse. |
| IA-05(13) | Expiration of Cached Authenticators | Invalidate and purge all cached authenticators and session tokens immediately upon user logoff or session termination (CCIs: 002006, 002007) | Section 8 | Automated token revocation in Cloud Identity / IAP upon logoff; immediate flush of cached credentials on bastions. |
| IA-05(14) | Managing Content of PKI Trust Stores | Authorize and manage the content of PKI trust stores, including root and intermediate certificates, under configuration control (CCIs: 002008) | Section 8 | CCB configuration control of {{ PKI_TRUST_TYPE }} trust bundles deployed to container images and Linux bastion operating systems. |
| IA-05(16) | In-Person Authenticator Issuance | Mandate that PKI hardware tokens ({{ MFA_MECHANISM }}) are issued in person by a certified Registration Authority (RA/TA) (CCIs: 004074, 004075, 004076, 004077) | Section 8 | Formal in-person identity proofing and biometric validation at certified issuance facilities. |
| IA-06 | Authentication Feedback | Obscure authentication feedback during credential entry to prevent shoulder surfing and credential harvesting (CCIs: 000206) | Section 9 | Masked input characters on console login portals; generic error messages on authentication failure. |
| IA-07 | Cryptographic Module Authentication | Employ NIST FIPS 140-2/140-3 validated cryptographic modules that authenticate operators before executing crypto functions (CCIs: 000803) | Section 10 | Google BoringCrypto (Cert #4407); Cloud HSM (Cert #4735); hardware-enforced cryptographic module boundaries. |
| IA-08 | Non-Organizational Users | Require non-organizational users to be sponsored, vetted, and uniquely authenticated using approved credentials (CCIs: 000804) | Section 11 | {{ ORGANIZATION }} sponsorship; Tier 3/5 background vetting; federated authentication via Federal PIV Trust Bridge. |
| IA-08(01) | Acceptance of PIV from Other Agencies | Accept Federal PIV credentials from other federal agencies via established trust bridges conforming to FIPS 201-3 (CCIs: 002009, 002010) | Section 11 | Cross-agency PKI trust mapping configured within {{ IDENTITY_PROVIDER }} federation profiles. |
| IA-08(02) | Acceptance of External Authenticators | Restrict acceptance of external authenticators to approved {{ MFA_MECHANISM }} tokens; prohibit commercial unverified MFA (CCIs: 004083, 004084) | Section 11 | {{ IDENTITY_PROVIDER }} Conditional Access policies restricting external authenticators strictly to {{ PKI_TRUST_TYPE }} tokens. |
| IA-08(04) | Use of Defined Profiles | Ensure external identity federation complies with the Federal / Public Sector Identity Federation Profile and NIST SP 800-63B standards (CCIs: 004085, 004086) | Section 11 | SAML 2.0 / OIDC federation configurations adhering to Federal Identity Federation Profile specifications. |
| IA-09 | Service Identification and Authentication | Uniquely identify and authenticate all automated services, CI/CD pipelines, and microservices using keyless WIF (CCIs: 002018, 002021, 002022) | Section 12 | Workload Identity Federation (WIF) OIDC token exchange; prohibition of static service account JSON keys. |
| IA-11 | Re-Authentication | Require full re-authentication ({{ MFA_MECHANISM }}) after 15-minute inactivity, prior to JIT privilege elevation, or when accessing {{ SENSITIVITY_CLASSIFICATION }} (CCIs: 002036, 002038) | Section 14 | 15-minute idle session disconnect; GCP Privileged Access Manager (PAM) re-authentication prompts; IAP timeout rules. |
| IA-12 | Identity Assertion Binding | Verify that all federated identity assertions (SAML/OIDC) are cryptographically bound to the authenticated subject (CCIs: 004092, 004093, 004094, 004095, 004096, 004097) | Section 15 | Cryptographic assertion signature validation; OIDC token signature verification using {{ IDENTITY_PROVIDER }} public keys. |
| IA-12(01) | Identity Assertion Binding: Accepted Identity Providers | Restrict acceptance of identity assertions strictly to authorized, vetted enterprise Identity Providers ({{ IDENTITY_PROVIDER }}) (CCIs: 004098) | Section 15 | Hardcoded IdP metadata bindings in GCP Workforce Identity Pool, rejecting untrusted identity assertion sources. |
| IA-12(02) | Identity Assertion Binding: Token Verification | Verify token validity, timestamps, audience restrictions, and cryptographic integrity before accepting assertions (CCIs: 004099) | Section 15 | Automated OIDC/SAML token validation engine verifying expiry, audience claims, and cryptographic nonces. |
| IA-12(03) | Identity Assertion Binding: Correlation and Validation | Real-time attribute validation against {{ IDENTITY_PROVIDER }} directory claims via SCIM during Workforce Pool token exchange (CCIs: 004100, 004101, 004102, 004103) | Section 15 | Real-time attribute validation against {{ IDENTITY_PROVIDER }} directory claims via SCIM during Workforce Pool token exchange. |



## Appendix B – Digital Identity & Authenticator Assurance Levels (Google Appendix E)

In accordance with NIST SP 800-63B and Google Services Appendix E (Digital Identity Worksheet), {{ ORGANIZATION }} enforces the following Digital Identity and Authenticator Assurance Levels across {{ SYSTEM_NAME }}:

| Identity & Authentication Category | Required Assurance Level | Technical Implementation Standard |
| :--- | :--- | :--- |
| **Identity Assurance Level (IAL)** | **IAL2** | Government PIV/CAC / Hardware Authenticator, Identity Verification, and Background Investigation (`PS-2`, `PS-3`). |
| **Authenticator Assurance Level (AAL)** | **AAL3** | Multi-Factor Authentication via FIDO2 / WebAuthn Hardware Security Keys (`IA-2`). |
| **Federated Assertion Level (FAL)** | **FAL3** | Cryptographically Signed SAML 2.0 / OpenID Connect (OIDC) Tokens via Google Workspace / Cloud Identity. |
| **Service Account Authentication** | **FAL3** | Short-Lived Workload Identity Federation (WIF) OAuth 2.0 Tokens (No long-lived JSON keys allowed). |
