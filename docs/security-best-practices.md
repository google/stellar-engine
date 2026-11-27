# Security best practices guide

This guide outlines operational hardening procedures to protect Google Cloud workloads, data, and foundational infrastructure deployed with Stellar Engine against privilege escalation, lateral movement, and data exfiltration.

| Field | Value |
| :--- | :--- |
| Created date | Nov 21, 2024 |
| Google contact | stellar-engine@google.com |
| Version | 1.0.2 |
| Recent changes | Updated formatting, table of contents, and `essentialcontacts.managed.allowedContactDomains` guidance |

Stellar Engine provisions compliant Google Cloud foundations inside Assured Workloads folders to support Department of Defense Impact Level 5 and FedRAMP High Authorization to Operate requirements. Using Terraform bootstrap stages, platform teams establish a standardized security baseline before deploying Google Cloud and approved third-party workload services.

To validate this baseline against real-world attacker tactics, techniques, and procedures, Mandiant conducted an authenticated penetration test from a Compute Engine instance across 18 Google Cloud resource types. The recommendations below address the resulting privilege escalation, lateral movement, and exfiltration findings so your organization can harden its deployment prior to authorization.

<!-- BEGIN TOC -->
- [1. Identity and access management](#1-identity-and-access-management)
  - [Human access](#human-access)
  - [Machine access](#machine-access)
  - [Application-specific groups](#application-specific-groups)
  - [User-specific IAM](#user-specific-iam)
  - [Group IAM](#group-iam)
  - [IAM references](#iam-references)
- [2. Group visibility restrictions](#2-group-visibility-restrictions)
- [3. Multi-factor authentication](#3-multi-factor-authentication)
  - [MFA references](#mfa-references)
- [4. Cloud Shell restrictions](#4-cloud-shell-restrictions)
  - [Cloud Shell references](#cloud-shell-references)
- [5. Logging and SIEM segmentation](#5-logging-and-siem-segmentation)
  - [Logging references](#logging-references)
- [6. Cloud Storage exfiltration controls](#6-cloud-storage-exfiltration-controls)
  - [Storage boundary references](#storage-boundary-references)
- [7. Essential Contacts](#7-essential-contacts)
  - [Domain restrictions](#domain-restrictions)
  - [Adding contacts](#adding-contacts)
  - [Managing contacts](#managing-contacts)
  - [Essential Contacts references](#essential-contacts-references)
- [8. Data security](#8-data-security)
  - [Encryption and data handling](#encryption-and-data-handling)
  - [Cloud KMS](#cloud-kms)
  - [Cloud Storage](#cloud-storage)
  - [Data residency](#data-residency)
<!-- END TOC -->

## 1. Identity and access management

Enforce least privilege across all principals and manage IAM bindings through Terraform rather than manual console edits. Restrict human permissions to create or modify resources to tightly controlled development projects, and execute `terraform apply` operations in higher environments exclusively through the dedicated Cloud Resource Manager automation service account in your CI/CD pipeline.

Configure role groups matching administrative and engineering functions in `fast/stages-aw/0-bootstrap` (`var.groups`, such as `gcp-organization-admins@example.com`, `gcp-security-admins@example.com`, `gcp-vpc-network-admins@example.com`, `gcp-billing-admins@example.com`, and `gcp-devops@example.com`) and per-tenant `admin_principal` groups in `1-resman`. Seed initial bindings in Terraform and manage ongoing membership through your enterprise identity provider or Terraform state.

Run the Stage 0 bootstrap phase using a tightly controlled individual administrator account belonging to the `gcp-organization-admins` group, and disable that account or revoke bootstrap privileges when bootstrap is not actively running. Bootstrap execution requires Organization Admin or Viewer, Organization Policy Admin, Billing Admin or User, Folder Creator, Access Context Manager Admin or User, Assured Workloads Admin, and Security Admin permissions. Independent Software Vendors must scope custom and predefined IAM roles strictly to system requirements.

### Human access

- Grant IAM roles to Google Cloud groups rather than individual user accounts.
- Scope group bindings to the minimum set of curated predefined roles required for each job function.

### Machine access

- Provision a dedicated service account for each microservice workload.
- Block downloadable service account keys and enforce the organization policy constraint that disables key creation.
- Grant each workload service account only the permissions required for its runtime function.
- Enforce the `iam.automaticIamGrantsForDefaultServiceAccounts` organization policy constraint to prevent default service accounts from receiving the primitive Editor role.

### Application-specific groups

Tenant platforms such as enterprise data warehouses often require workload-specific groups including Data Analyst, Data Engineer, Network Administrator, Security Administrator, and Security Analyst. Although you manage these application-level groups outside the core Stellar Engine stages, map their permissions carefully against foundational role groups to prevent unintended privilege overlap.

### User-specific IAM

When a development exception requires inspecting or granting principal-level access in the Google Cloud console, apply least-privilege roles:

1. Open <https://console.cloud.google.com> and select **IAM** from the search bar.
2. Select **Allow** and **View By Principals**, then click **Grant Access**.
3. Enter the principal address in the **New principals** field.
4. Select the minimum roles required under the principle of least privilege.
5. Click **Save**.

### Group IAM

Add users to Stellar Engine role groups or register new functional groups in the Google Cloud console:

1. Open <https://console.cloud.google.com> and select **Groups** from the search bar to view pre-configured Stellar Engine IAM groups.
2. Click the three-dot menu next to an existing group to add members, or click **Create** to define a new group with its name, email address, and description, then click **Save**.
3. Navigate to **IAM**, select **Allow** and **View By Principals**, and click **Grant Access**.
4. Enter the group email address in the **New principals** field and assign the minimum required roles.
5. Click **Save**.

### IAM references

- NIST SP 800-53 Revision 5 control SA-8(14), Security and Privacy Engineering Principles for Least Privilege.

## 2. Group visibility restrictions

Restrict group membership visibility in Google Workspace or Cloud Identity so non-administrative users such as application developers cannot enumerate privileged administrator groups:

1. Sign in to [Google Admin console](https://admin.google.com/ac/security/2sv) with a Super Admin account.
2. Navigate to **Directory** and select **Groups**.
3. Select the privileged group whose membership list you want to restrict.
4. Open **Access settings** and click the edit icon next to **Access type**.
5. Select **Restricted** to prevent general directory users from viewing group members.

## 3. Multi-factor authentication

Enforce multi-factor authentication for all privileged and non-privileged user accounts to meet IL5 and NIST authentication requirements. Stellar Engine cannot toggle Workspace-level authentication settings automatically during Terraform bootstrap, so Independent Software Vendors and organization administrators must enable multi-factor authentication when provisioning user accounts to block credential stuffing, phishing, and lateral movement:

1. Sign in to <https://admin.google.com/ac/security/2sv> with a Super Admin account.
2. Select **Allow users to turn on 2-Step Verification**.
3. Set **Enforcement** to **On**.
4. Configure the **New user enrollment period**, **Frequency**, and allowed **Methods** according to your compliance baseline.
5. Click **Save**.

### MFA references

- NIST SP 800-53 Revision 5 control IA-2(1), Multi-Factor Authentication for Privileged Accounts.
- NIST SP 800-53 Revision 5 control IA-2(2), Multi-Factor Authentication for Non-Privileged Accounts.
- NIST SP 800-63-3, Digital Identity Guidelines.

## 4. Cloud Shell restrictions

Disable Google Cloud Shell across IL2, IL4, and IL5 organizations because Cloud Shell is not an approved service for those regimes; check the [Assured Workloads supported products list](https://cloud.google.com/assured-workloads/docs/supported-products) for current regime coverage. Leaving Cloud Shell enabled gives an authenticated attacker a Google-hosted execution environment outside your customer-managed VPC perimeter that can proxy traffic and bypass host-level audit controls.

Independent Software Vendors and organization administrators must disable Cloud Shell in the Google Admin console:

1. Sign in to <https://admin.google.com/ac/appslist/additional> with a Super Admin account.
2. Select **Google Cloud Platform** and open **Cloud Shell Access Settings**.
3. Clear **Allow access to Cloud Shell**.
4. Click **Save**.

### Cloud Shell references

- [Disable or reset Cloud Shell](https://cloud.google.com/shell/docs/resetting-cloud-shell) in the Google Cloud documentation.

## 5. Logging and SIEM segmentation

Google Cloud generates audit, network, and provider access telemetry to support continuous monitoring and incident response:

- Admin Activity audit logs record API calls and administrative actions that modify resource configurations or IAM policies.
- Data Access audit logs record reads of resource configurations and metadata along with user-driven creation, modification, or reads of resource data.
- System Event audit logs record automated Google Cloud actions that modify resource configurations.
- VPC Flow Logs sample network flows to and from Compute Engine instances for traffic analysis and forensics.
- Firewall Rules Logging records rule matches and connection counts across VPC firewall rules.
- Access Transparency logs record actions taken by Google personnel when servicing support requests or maintaining platform availability.

Independent Software Vendors must deploy a dedicated Security Information and Event Management and Security Orchestration, Automation, and Response platform in a separate project and isolated VPC away from monitored tenant workloads. Isolating the SIEM instance preserves log integrity while delivering real-time alerting across infrastructure and application telemetry.

### Logging references

- NIST SP 800-53 Revision 5 control families for Audit and Accountability, Assessment, Authorization, and Monitoring, and System and Information Integrity.

## 6. Cloud Storage exfiltration controls

Enforce multi-factor authentication across all accounts as described in section 3 so compromised user credentials cannot read or exfiltrate sensitive objects from Cloud Storage.

Layer Access Context Manager access levels and VPC Service Controls perimeters (configured in Stage `fast/stages-aw/3-security/vpc-sc.tf`) around Cloud Storage buckets and sensitive APIs across supported IL5 and FedRAMP High environments. Check the [Assured Workloads supported products list](https://cloud.google.com/assured-workloads/docs/supported-products) for current service compliance scope before enabling Identity-Aware Proxy inside IL5 enclaves.

### Storage boundary references

- NIST SP 800-53 Revision 5 controls IA-2(1) and IA-2(2), and NIST SP 800-63-3.
- [Context-Aware Access setup guide](https://cloud.google.com/iap/docs/cloud-iap-context-aware-access-howto).
- [VPC Service Controls overview](https://cloud.google.com/vpc-service-controls/docs/overview#how-vpc-service-controls-works).

## 7. Essential Contacts

Configure Google Cloud Essential Contacts so designated security, billing, legal, and operations groups receive critical platform notifications without delay. Independent Software Vendors must register Essential Contacts across their organization hierarchy.

### Domain restrictions

Google Cloud enforces the `essentialcontacts.managed.allowedContactDomains` organization policy constraint to restrict notification recipients to approved email domains. Organizations created on or after June 26, 2025 automatically allow their primary organization domain, whereas older organizations or Terraform-managed policies may restrict or omit secondary partner domains and block contact registration.

Verify and update allowed contact domains through your Infrastructure as Code workflow:

1. Inspect the active [Essential Contacts](https://cloud.google.com/resource-manager/docs/managing-notification-contacts) `essentialcontacts.managed.allowedContactDomains` and `essentialcontacts.allowedContactDomains` policies configured in `fast/stages-aw/0-bootstrap/data/custom-org-policies/platform_policy.yaml`.
2. Set the primary organization domain without a leading `@` in Stage `0-bootstrap` `var.organization.domain`, such as `example.com`; `platform_policy.yaml` prepends `@` automatically when templating those policies.
3. Add any secondary or partner recipient domains prefixed with `@`, such as `@partner.example.com`, directly to `essentialcontacts.allowedContactDomains` and `essentialcontacts.managed.allowedContactDomains` in `fast/stages-aw/0-bootstrap/data/custom-org-policies/platform_policy.yaml`.
4. Commit these domain policy updates in Terraform rather than editing them manually in the Google Cloud console or `gcloud`, so subsequent pipeline runs do not overwrite your changes.

### Adding contacts

Configure notification recipients declaratively in `fast/stages-aw/0-bootstrap` using `var.essential_contacts`, which accepts either a single email string or a map of recipient emails to notification category lists (`SUSPENSION`, `SECURITY`, `TECHNICAL`, `BILLING`, `LEGAL`, `PRODUCT_UPDATES`, or `ALL`):

```hcl
essential_contacts = {
  "security@example.com" = ["ALL"]
  "billing@example.com"  = ["BILLING"]
}
```

Stage 0 passes `var.essential_contacts` to the organization (`module.organization`), core administrative projects, and folders so contact coverage inherits automatically across the landing zone.

### Managing contacts

Update or remove notification recipients by modifying `essential_contacts` in `fast/stages-aw/0-bootstrap/terraform.tfvars` and applying through your reviewed Terraform pipeline rather than making ad-hoc edits in the Google Cloud console, preventing Terraform state drift and organization policy conflicts.

### Essential Contacts references

- [Managing contacts for notifications](https://cloud.google.com/resource-manager/docs/managing-notification-contacts).

## 8. Data security

Securing data in Google Cloud follows a shared responsibility model in which Google secures the underlying physical infrastructure while you control transport configurations, encryption key lifecycles, bucket permissions, and regional placement.

### Encryption and data handling

Google encrypts inter-service platform traffic and data at rest across physical storage media automatically. Enforce TLS across all external and application-level channels, supply Customer-Managed Encryption Keys for Compute Engine persistent disks and Cloud Storage buckets where required, and add application-layer encryption for sensitive database fields to limit data exposure if workload credentials are compromised. When loading regulated data such as PII or PCI records into BigQuery, enforce dataset access controls and compliance governance before ingestion.

### Cloud KMS

Use Cloud Key Management Service to manage cryptographic keys and application-level encryption under your compliance boundary:

- Rotate encryption keys on an automated schedule through Terraform, `gcloud`, or the Google Cloud console to bound the volume of data protected by any single key version.
- Enforce separation of duties by hosting Cloud KMS in a dedicated security project without project-level Owner bindings. Restrict organization administrators to IAM policy administration so principals who manage key permissions cannot encrypt or decrypt workload ciphertext.
- Supply Additional Authenticated Data strings on Cloud KMS encrypt and decrypt API calls to bind ciphertext to its intended context and defend against confused deputy attacks.

### Cloud Storage

Because unauthenticated callers can probe Cloud Storage bucket and object existence through error responses, apply strict naming and access hygiene across all buckets:

- Include random suffixes in bucket names such as `stellar-engine-mybucket-gxl3` so external parties cannot guess or enumerate bucket names or infer stored contents.
- Enforce `constraints/storage.uniformBucketLevelAccess` (`true`) across all buckets so Cloud IAM governs access uniformly and legacy object ACLs remain disabled.
- Enforce `constraints/storage.publicAccessPrevention` (`true`) and `constraints/iam.allowedPolicyMemberDomains` so buckets and objects cannot grant `allUsers` or `allAuthenticatedUsers` read or write access.
- Enforce `constraints/storage.secureHttpTransport` (`true`) and configure CMEK encryption keys where mandated by the compliance regime.
- Issue time-bounded Signed URLs with explicit read or write scope only where temporary authenticated access by approved external parties is strictly required.

### Data residency

Enforce geographic data residency by combining Organization Policy constraints with least-privilege IAM:

- Identify the exact Google Cloud regions authorized by your compliance regime and customer contracts.
- Apply the `constraints/gcp.resourceLocations` organization policy constraint at the organization, folder, or project level to restrict newly created resources to approved regions.
- Restrict IAM permissions for regional and global services so operators cannot provision resources outside compliant boundaries.
- Audit deployed assets regularly to verify continuous compliance with regional residency policies.
- Account for existing resources separately during migrations, because `constraints/gcp.resourceLocations` evaluates new resource creation and does not relocate pre-existing resources.
