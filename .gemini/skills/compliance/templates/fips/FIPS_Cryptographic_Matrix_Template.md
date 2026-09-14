# FIPS 140-2 / FIPS 140-3 Cryptographic Module Validation Matrix

## Document Control & System Metadata

| Parameter | Configuration Value |
| :--- | :--- |
| **System Name** | {{ SYSTEM_NAME }} ({{ SYSTEM_ABBREVIATION }}) |
| **Impact Level** | {{ IMPACT_LEVEL }} |
| **Compliance Baseline** | {{ COMPLIANCE_BASELINE }} |
| **Governing Organization** | {{ ORGANIZATION }} |
| **Effective Date** | {{ DATE }} |
| **Document Version** | {{ VERSION }} |
| **System Owner** | {{ SO_NAME }} ({{ SO_TITLE }}) |
| **ISSM** | {{ ISSM_NAME }} ({{ ISSM_TITLE }}) |
| **Authorizing Official** | {{ AO_NAME }} ({{ AO_TITLE }}) |

---

## 1. Executive Cryptographic Summary & FIPS 140-3 Mandate

This document serves as the formal **FIPS 140-2 / FIPS 140-3 Cryptographic Validation Matrix** required for federal authorization under NIST SP 800-53 Rev. 5 (controls **SC-12**, **SC-13**, **SC-28**, and **IA-7**), FedRAMP High baseline, and DoD Cloud Computing Security Requirements Guide (CC SRG) Impact Levels 4 and 5.

All cryptographic modules utilized within {{ SYSTEM_NAME }} for data-at-rest encryption, data-in-transit protection, key generation, and administrative authentication are validated under the NIST Cryptographic Module Validation Program (CMVP) and Cryptographic Algorithm Validation Program (CAVP).

---

## 2. FIPS 140-3 Cryptographic Modules Inventory

| Module ID | Functional Area | Module Name | Vendor & NIST CMVP Cert # | Validation Level | Approved Cryptographic Algorithms | Implementation Scope & Enforcement | Validation Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **FIPS-01** | Data-at-Rest Encryption | Google Cloud KMS HSM (FIPS 140-3 Level 3 Hardware Security Module) | Google Cloud / Marvell<br>(NIST CMVP Cert #4282 / #3318) | **FIPS 140-3 Level 3** | AES-256 GCM, RSA-4096, ECDSA P-384, HMAC-SHA384, DRBG SP 800-90A | Customer-Managed Encryption Keys (CMEK) enforcing envelope encryption across Cloud Storage buckets, Cloud SQL databases, Persistent Disks, and Secret Manager. | Active / Validated CMVP |
| **FIPS-02** | Data-in-Transit Encryption | Google BoringCrypto Module | Google Cloud Platform<br>(NIST CMVP Cert #4407 / #3318) | **FIPS 140-3 Level 1** | TLS 1.3, AES-256-GCM, ECDHE-ECDSA, SHA-256 / SHA-384 | Mutual TLS 1.3 / HTTPS encryption across all Google Front Ends (GFE), Private Service Connect (PSC), and inter-VPC peering endpoints. | Active / Validated CMVP |
| **FIPS-03** | Boundary & Perimeter Tunneling | FIPS 140-3 Validated Virtual Appliance / Cloud VPN IPSec Gateway | Google Cloud / Enterprise NGFW Vendor<br>(NIST CMVP Cert #4123) | **FIPS 140-2 / 140-3 Level 2** | IPsec IKEv2, AES-256-GCM, AES-256-CBC, HMAC-SHA256, Diffie-Hellman Group 14/19/20 | Secure boundary tunneling connecting cloud VPCs to DoD DISA Boundary Cloud Access Point (BCAP) and on-premises enclaves. | Active / Validated CMVP |
| **FIPS-04** | Identity & Access Authentication | High-Assurance PKI / Hardware Token Authenticator | Google Cloud Identity / Federal PKI<br>(FIPS 201-3 / NIST CMVP #3842) | **FIPS 140-3 Level 3** | PIV / CAC X.509v3, RSA-2048/4096, ECDSA P-256/P-384, FIDO2 WebAuthn | Hardware MFA authentication for privileged administrators and zero-trust Identity-Aware Proxy (IAP) access sessions. | Active / Validated CMVP |

---

## 3. Customer-Managed Encryption Keys (CMEK) Inventory

| Key Ring / Key Resource | Protection Level | Rotation Cadence | Bound Workload Resources | Key Custodian / Management |
| :--- | :--- | :--- | :--- | :--- |
| `{{ KMS_KEYS }}` | **Hardware (HSM) FIPS 140-3 Level 3** | Automated 90-Day Rotation | Storage Buckets, Database Volumes, Boot Disks, Secret Manager | Cloud Security Admin / Org KMS Service Account |

### Storage & Persistence CMEK Verification
{{ STORAGE_BUCKETS_LIST }}

---

## 4. Cryptographic Algorithm & Protocol Standards Summary

| Cryptographic Domain | Governing Standard | Minimum Key Length / Algorithm | Enforcement Mechanism |
| :--- | :--- | :--- | :--- |
| **Data-at-Rest** | NIST SP 800-111 / FIPS 197 | AES-256 bit encryption in GCM mode | Cloud KMS CMEK + Google Default Envelope Encryption |
| **Data-in-Transit** | NIST SP 800-52 Rev. 2 / RFC 8446 | TLS 1.3 (with TLS 1.2 restricted ciphers) | Organization Policy `constraints/compute.restrictTlsVersions` |
| **Key Generation & Derivation** | NIST SP 800-133 Rev. 2 / SP 800-90A | FIPS 140-3 Level 3 HSM hardware entropy source | Cloud KMS Cloud HSM Key Rings |
| **Digital Signatures & PKI** | FIPS 186-5 / RFC 5280 | RSA >= 2048-bit, ECDSA P-384 | Certificate Manager & Google Cloud Certificate Authority Service (CAS) |
| **Password & Credential Hashing** | NIST SP 800-63B / SP 800-132 | Argon2id / PBKDF2 with SHA-256+ | Secret Manager + Cloud Identity Workload Identity Federation |

---

## 5. RMF Team Operational Verification & Action Items

> [!IMPORTANT]
> <mark style="background-color: #fff9c4; color: #b71c1c; font-weight: bold; padding: 2px 6px; border-radius: 4px;">**RMF TEAM / HUMAN ACTION REQUIRED**</mark>:
> 1. **NIST CMVP Certificate Validation**: Verify that the NIST CMVP certificate numbers listed in Section 2 remain in "Active" status on the NIST CSRC database (https://csrc.nist.gov/projects/cryptographic-module-validation-program/validated-modules) prior to formal SCA submission.
> 2. **Annual Crypto Period Audit**: Ensure all Cloud KMS CMEK crypto keys have active automated 90-day rotation schedules verified in Cloud Logging audit logs.
> 3. **eMASS Attachment**: Upload this signed FIPS Cryptographic Matrix document (`.docx` or `.pdf`) into the eMASS Artifacts repository under Control `SC-13`.
