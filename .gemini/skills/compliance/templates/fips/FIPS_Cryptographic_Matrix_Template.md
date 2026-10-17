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

## 1. Executive Cryptographic Summary & FIPS 140-2 / 140-3 Scope

This document serves as the formal **FIPS 140-2 / FIPS 140-3 Cryptographic Validation Matrix** required for federal authorization under NIST SP 800-53 Rev. 5 (controls **SC-12**, **SC-13**, **SC-28**, and **IA-7**), FedRAMP baselines, and DoD Cloud Computing Security Requirements Guide (CC SRG) Impact Levels 4 and 5.

Cryptographic modules utilized within {{ SYSTEM_NAME }} for data-at-rest encryption, data-in-transit protection, key generation, and administrative authentication are documented in Section 2 with their NIST Cryptographic Module Validation Program (CMVP) validation scope and any pending operator verification items (`[CONFIG_REQUIRED]`).

---

## 2. FIPS 140-2 / FIPS 140-3 Cryptographic Modules Inventory

| Module ID | Functional Area | Module Name | Vendor & NIST CMVP Cert # | Validation Level | Approved Cryptographic Algorithms | Implementation Scope & Enforcement | Validation Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **FIPS-01A** | Customer-Managed Key Management (Software) | Google Cloud KMS Software Module (Google BoringCrypto) | Google LLC (NIST CMVP Cert #4735, retrieved 2026-10-15) | **FIPS 140-3 Level 1** | AES-256-GCM, RSA-2048/3072/4096, ECDSA P-256/P-384, HMAC-SHA-256/SHA-384, SP 800-90A CTR-DRBG | Software-backed Customer-Managed Encryption Keys (`protection_level = SOFTWARE`) across Cloud Storage buckets, Cloud SQL databases, Persistent Disks, and Secret Manager. | Active on CMVP (#4735, retrieved 2026-10-15) |
| **FIPS-01B** | Customer-Managed Key Management (Hardware HSM) | Cloud HSM (Marvell [formerly Cavium] HSMs) | Marvell (formerly Cavium) `[CONFIG_REQUIRED: CMVP certificate number from the Google Cloud FedRAMP/DoD package cryptographic module inventory or the Cloud HSM key attestation certificate chain]` | **FIPS 140-2 Level 3** | AES-256-GCM, RSA-2048/3072/4096, ECDSA P-256/P-384, HMAC-SHA-256/SHA-384, SP 800-90A CTR-DRBG | Hardware-backed Customer-Managed Encryption Keys (`protection_level = HSM`) where configured in Terraform. | Per CSP documentation; verify CMVP certificate status before submission |
| **FIPS-02** | Data-in-Transit Encryption | Google BoringCrypto Module | Google LLC<br>(NIST CMVP Cert #5104, retrieved 2026-10-15) | **FIPS 140-3 Level 1** | TLS 1.2 / TLS 1.3 KDFs, AES-128/256-GCM, ECDHE-RSA / ECDHE-ECDSA, SHA-256 / SHA-384 | Transport Layer Security (TLS 1.2 minimum, TLS 1.3 where supported per NIST SP 800-52 Rev. 2) across Google Front Ends (GFE) and customer endpoints, plus Application Layer Transport Security (ALTS, AES-128-GCM by default) and PSP virtual network encryption. | Active on CMVP (#5104, retrieved 2026-10-15) |
| **FIPS-03** | Boundary & Perimeter Tunneling | Cloud VPN IPsec Module / Customer Virtual Network Appliance | [CONFIG_REQUIRED: CSP module certificate per Google Cloud FedRAMP/DoD authorization package and customer NGFW/appliance vendor & NIST CMVP Cert #] | **[CONFIG_REQUIRED: Cloud VPN & Customer Appliance FIPS Validation Level]** | IPsec IKEv2, AES-256-GCM, AES-256-CBC, HMAC-SHA-256/384, DH Group 14 (MODP-2048), ECDH Groups 19/20 (P-256/P-384) | Secure boundary tunneling connecting cloud VPCs to on-premises or boundary enclaves (customer must restrict Cloud VPN IKEv2 proposals to FIPS-approved cipher suites). | [CONFIG_REQUIRED: Verify NIST CMVP Certificate Status and applicable DISA STIG/SRG compliance for any customer-managed NGFW appliance] |
| **FIPS-04** | Identity & Access Authentication | High-Assurance PKI / Hardware Token Cryptographic Module | [CONFIG_REQUIRED: PIV / CAC / FIDO2 Token Vendor & NIST CMVP Cert #] | **FIPS 140-2 or FIPS 140-3 (Security Level 2 minimum for hardware authenticators per FIPS 201-3 / NIST SP 800-63B)** | PIV / CAC X.509v3 (FIPS 201-3), RSA-2048/3072, ECDSA P-256/P-384, FIDO2 WebAuthn | Phishing-resistant hardware multi-factor authentication (MFA) for privileged administrators and zero-trust access sessions via enterprise Identity Provider. | [CONFIG_REQUIRED: Verify Token CMVP Certificate Status] |

---

## 3. Customer-Managed Encryption Keys (CMEK) Inventory

| Key Ring / Key Resource | Protection Level | Rotation Cadence | Bound Workload Resources | Key Custodian / Management |
| :--- | :--- | :--- | :--- | :--- |
| `{{ KMS_KEYS }}` | **Cloud HSM (where `protection_level = HSM`): FIPS 140-2 Level 3 validated hardware security modules manufactured by Marvell (formerly Cavium); Cloud KMS software keys: FIPS 140-3 Level 1 (Google BoringCrypto #4735, retrieved 2026-10-15)** | [CONFIG_REQUIRED: Verify organization-defined cryptoperiod in Terraform per NIST SP 800-57 Part 1] | Storage Buckets, Database Volumes, Boot Disks, Secret Manager | Cloud Security Admin / Org KMS Service Account |

### Storage & Persistence CMEK Verification
{{ STORAGE_BUCKETS_LIST }}

---

## 4. Cryptographic Algorithm & Protocol Standards Summary

| Cryptographic Domain | Governing Standard | Minimum Key Length / Algorithm | Enforcement Mechanism |
| :--- | :--- | :--- | :--- |
| **Data-at-Rest** | NIST SP 800-111 / FIPS 197 | AES-256 bit encryption in GCM mode | Cloud KMS CMEK + Google Default Envelope Encryption (FIPS 140-validated Google BoringCrypto module per CSP authorization package) |
| **Data-in-Transit** | NIST SP 800-52 Rev. 2 / RFC 8446 | TLS 1.2 minimum, TLS 1.3 where supported with FIPS-approved cipher suites | Organization Policy `constraints/gcp.restrictTLSVersion` & `constraints/gcp.restrictTLSCipherSuites` (for Google API endpoints) and Load Balancer SSL Policies |
| **Key Generation & Derivation** | NIST SP 800-133 Rev. 2 / SP 800-90A | SP 800-90A CTR-DRBG (Google BoringCrypto #4735 for software keys; FIPS 140-2 Level 3 Cloud HSM for HSM keys) | Cloud KMS Software & Cloud HSM Key Rings |
| **Digital Signatures & PKI** | FIPS 186-5 / RFC 5280 | RSA >= 2048-bit (3072-bit recommended), ECDSA P-256 / P-384 | Certificate Manager & Google Cloud Certificate Authority Service (CAS) |
| **Password & Credential Hashing** | NIST SP 800-63B / SP 800-132 | PBKDF2-HMAC-SHA-256 / SHA-512 (per NIST SP 800-132 for FIPS-validated KDFs) | [CONFIG_REQUIRED: Enterprise Identity Provider / Credential Verifier] |

---

## 5. RMF Team Operational Verification & Action Items

> [!IMPORTANT]
> [WARNING: RMF TEAM / HUMAN ACTION REQUIRED]:
> 1. **NIST CMVP Certificate Validation**: Verify that the NIST CMVP certificate numbers listed in Section 2 remain in "Active" status on the NIST CSRC database (https://csrc.nist.gov/projects/cryptographic-module-validation-program/validated-modules) prior to formal SCA submission.
> 2. **Cryptoperiod & Key Rotation Audit**: Verify that Cloud KMS CMEK crypto keys enforce the organization-defined cryptoperiod (NIST SP 800-57 Part 1; FedRAMP SC-12 in accordance with Federal requirements) and confirm rotation events in Cloud Logging audit logs.
> 3. **eMASS Attachment**: Upload this signed FIPS Cryptographic Matrix document (`.docx` or `.pdf`) into the eMASS Artifacts repository under Control `SC-13`.
