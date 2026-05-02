Stellar Engine (SE) Security Best Practices Guide
Last Updated: May 2, 2026
Version: 1.1.0
Status: Managed/Secure
1. Purpose & Scope
This document outlines the security protocols for Stellar Engine (SE), a framework designed for rapid deployment within secure Google Cloud environments. It specifically addresses requirements for DoD Impact Level 5 (IL5) and FedRAMP High Authorization to Operate (ATO).
Stellar Engine leverages Infrastructure as Code (IaC) via Terraform to provision baseline environments within Assured Workloads. By following these best practices, organizations can proactively mitigate vulnerabilities identified during Mandiant penetration testing, specifically regarding privilege escalation and lateral movement.
2. Identity and Access Management (IAM)
Stellar Engine enforces the Principle of Least Privilege (PoLP). Human intervention is restricted to development environments, while production changes are strictly managed through CI/CD pipelines.
2.1 Human Access Control
Group-Based Access: Permissions must never be assigned to individual user accounts. Access is granted only to Google Groups.
Curated Roles: Use custom, minimalized roles instead of broad primitive roles (Owner/Editor).
Naming Convention: All role groups must follow the standard: gcp-X-${tenant}-${role}@X.gov.
2.2 Machine & Service Access
Microsegmentation: Every microservice must have a dedicated, unique Service Account.
Key Management: The creation of downloadable Service Account keys is strictly disabled via organizational policy to prevent credential leakage.
Default Account Hardening: Automatic role grants to default service accounts (iam.automaticIamGrantsForDefaultServiceAccounts) must be disabled to remove the default 'Editor' role.
2.3 Multi-Factor Authentication (MFA)
MFA is mandatory for all privileged and non-privileged accounts.
Enforcement: Navigate to admin.google.com/ac/security/2sv to enable 2-Step Verification.
Impact: Enforcing MFA is a critical requirement for IL5 compliance and protects against password spraying and social engineering attacks.
3. Detection, Alerting, and Logging (SIEM)
Stellar Engine utilizes comprehensive Google Cloud logging, but requires an external SIEM/SOAR solution for compliance.
Audit Logs: Monitor Admin Activity, Data Access, and System Events.
Network Logs: Enable VPC Flow Logs and Firewall Rule Logs for traffic analysis.
Segmentation: The SIEM system must be hosted in a separate project and VPC from the data source to ensure isolation and prevent tampering.
4. Essential Contacts & Governance
To ensure critical security and billing alerts reach the right personnel, Essential Contacts must be configured.
4.1 Domain Restrictions
For organizations created after June 2025, the essentialcontacts.managed.allowedContactDomains policy is enforced by default.
Pro Tip: When using Terraform to manage these policies, ensure all approved domains are prefixed with @ (e.g., @organization.com) within your .tf configuration to prevent manual overrides from being wiped during the next terraform apply.
5. Data Security & Encryption
Security is a Shared Responsibility. While Google secures the infrastructure, the user is responsible for data-layer security.
Transit: Ensure all data transmission is facilitated over TLS-encrypted channels.
At Rest: Utilize Cloud KMS (Key Management Service) for application-level encryption.
Key Rotation: Implement automated key rotation schedules to limit the blast radius of a potential key compromise.
Separation of Duties: Cloud KMS should reside in its own dedicated project. To maintain strict security, this project should not have an "Owner" at the project level; instead, permissions should be granted via specific KMS roles to prevent unauthorized key access by project administrators.
