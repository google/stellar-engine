# Security Command Center deployment guide

Follow these procedures to enable Google Cloud Security Command Center in a Stellar Engine organization.

## 1. Getting started

Review the Google Cloud Security Command Center documentation before activating the service at the organization level:

- [Security Command Center overview](https://cloud.google.com/security-command-center/docs/security-command-center-overview)
- [Organization-level activation overview](https://cloud.google.com/security-command-center/docs/activate-scc-overview#overview_of_organization-level_activation)
- [Activate Security Command Center for an organization](https://cloud.google.com/security-command-center/docs/activate-scc-for-an-organization)

## 2. Grant IAM permissions

Ensure the activating user belongs to the Stellar Engine organization groups provisioned in Stage `0-bootstrap` (`0-bootstrap/organization-iam.tf`) that hold the required Security Command Center activation and organization administration roles:

1. Open [IAM and Admin](https://console.cloud.google.com/iam-admin/iam) in the Google Cloud console or review `fast/stages-aw/0-bootstrap/organization-iam.tf`.
2. Select your organization in the **Project Selector**.
3. Confirm that your activating account belongs to both `gcp-security-admins@<domain>` (which holds `roles/securitycenter.admin`, `roles/iam.securityReviewer`, and `roles/logging.admin` at the organization level) and `gcp-organization-admins@<domain>` (which holds `roles/resourcemanager.organizationAdmin` and organization IAM administration permissions needed during initial activation), as documented in [Set Up Permissions](https://cloud.google.com/security-command-center/docs/activate-scc-for-an-organization#set_up_permissions).

## 3. Modify service usage policy

Apply this policy update only when evaluating Security Command Center in an IL5 environment where `gcp.restrictServiceUsage` blocks unapproved APIs, because Security Command Center is not yet approved for IL5 production workloads. Note that `gcp.restrictServiceUsage` on `StellarEngine-<prefix>` is managed by Assured Workloads (`aw_managed_policies` in `fast/stages-aw/0-bootstrap/organization.tf`); review the [Assured Workloads operations guide](./assured-workloads-operations.md) before modifying enclave-level policies.

Never choose **Replace** when editing `gcp.restrictServiceUsage` on a child folder, because replacing removes all inherited Assured Workloads baseline allowed services and breaks platform APIs across every project under the folder. Instead, manage the allowlist declaratively in `fast/stages-aw/0-bootstrap/data/org-policies/platform_policy.yaml` when organization-mode policy management applies, or merge with the inherited parent policy in the console:

1. Open [Restrict Resource Service Usage](https://console.cloud.google.com/iam-admin/orgpolicies/gcp-restrictServiceUsage) in the Google Cloud console.
2. Select the **StellarEngine-\<prefix\>** folder in the **Project Selector**.
3. Click **Manage Policy** and verify existing inherited allowed services first.
4. Select **Override Parent's Policy** with **Policy enforcement** set to **Merge with Parent** (never **Replace**) so inherited Assured Workloads services stay intact.
5. Scroll to the **Rules** section and expand the **Allow** list.
6. Click **Add Value** twice.
7. Enter these API service names into the two text fields:
   - `securitycenter.googleapis.com`
   - `securitycentermanagement.googleapis.com`
8. Click **Done**.
9. Click **Set Policy**, and record the approved exception in your compliance drift log per the [Assured Workloads operations guide](./assured-workloads-operations.md).

## 4. Activate Security Command Center

Activate Security Command Center for your organization and enforce data residency:

1. Open [Security Command Center](https://console.cloud.google.com/marketplace/product/google-cloud-platform/cloud-security-command-center-premium) in the Google Cloud console.
2. Select your organization in the **Project Selector**.
3. Click **Go to Security Command Center**.
4. Click **Get Security Command Center**.
5. Select your target tier, such as the **Premium** tier.
6. Click **Next**.
7. Keep all default services enabled and click **Next**.
8. Select **Enable Data Residency** under **Data Residency**, which is required for FedRAMP High compliance.
9. Select the **Grant Roles Automatically** radio button and click **Grant Roles**.
10. Click **Next** after Google Cloud finishes granting the roles.
11. Click **Finish** on the **Ready to Complete Setup** screen.
12. Open [Compliance](https://console.cloud.google.com/security/command-center/compliance) and select your organization in the **Project Selector**.
13. Wait approximately 24 hours for the initial scans to finish and generate compliance reports.

## 5. Reference documentation

- [Security Command Center overview](https://cloud.google.com/security-command-center/docs/security-command-center-overview)
- [Organization-level activation overview](https://cloud.google.com/security-command-center/docs/activate-scc-overview#overview_of_organization-level_activation)
- [Activate Security Command Center for an organization](https://cloud.google.com/security-command-center/docs/activate-scc-for-an-organization)
- [Set Up Permissions](https://cloud.google.com/security-command-center/docs/activate-scc-for-an-organization#set_up_permissions)
