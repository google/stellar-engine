# Stellar Engine: Security Command Center (SCC) Deployment Guide

Procedures to deploy Security Command Center into a Stellar Engine deployment

## 1.0 - Getting Started

This document follows the information and steps as outlined in the following Google Cloud Security Command Center articles to enable SCC for a Stellar Engine Deployment.

- [Security Command Center Overview](https://cloud.google.com/security-command-center/docs/security-command-center-overview)
- [Overview of Organization-Level Activation](https://cloud.google.com/security-command-center/docs/activate-scc-overview#overview_of_organization-level_activation)
- [Activate the Security Command Center Standard/Premium Tier for an Organization](https://cloud.google.com/security-command-center/docs/activate-scc-for-an-organization)

## 2.0 - Grant IAM Permissions

Grant the appropriate IAM roles to set up the Security Command Center service.

1. Navigate to [IAM & Admin](https://console.cloud.google.com/iam-admin/iam)
2. In the **Project Selector**, select your organization
3. If not already added, add your user to the following GCP groups that have the appropriate IAM roles already assigned:

**Resources**
- [Set Up Permissions](https://cloud.google.com/security-command-center/docs/activate-scc-for-an-organization#set_up_permissions)

## 3.0 - Modify Resource Service Usage Policy

**Note**: This step is for evaluating SCC within an IL5 environment since SCC is not yet approved for the IL5 compliance regime.

Enable the Security Command Center APIs for the **StellarEngine-<prefix>** folder under the Restrict Resource Service Usage Organizational Policy.

1. Navigate to [Organizational Policies - Restrict Resource Service Usage](https://console.cloud.google.com/iam-admin/orgpolicies/gcp-restrictServiceUsage)
2. In the **Project Selector**, select the **StellarEngine-<prefix>** folder
3. Click **Manage Policy**
4. Ensure not to modify the radio buttons as the following should already be selected:
    - **Policy Source**: Override Parent’s Policy
    - **Policy Enforcement**: Replace

**IMPORTANT**: Ensure that **Replace** is selected instead of **Merge with Parent**

5. Scroll down to the **Rules** section and expand the **Allow** list
6. Scroll down to the bottom and click **Add Value** twice (x2)
7. Copy and paste the following APIs into each of the text fields:
    - `securitycenter.googleapis.com`
    - `securitycentermanagement.googleapis.com`
8. Click **Done**
9. Click **Set Policy**

## 4.0 - Activate Security Command Center

1. Navigate to [Security Command Center](https://console.cloud.google.com/marketplace/product/google-cloud-platform/cloud-security-command-center-premium)
2. In the **Project Selector**, select your organization
3. Click **Go to Security Command Center**
4. Click **Get Security Command Center**
5. Select a tier
    - We have been evaluating the Premium tier
6. Click **Next**
7. Accept the default services. All services are enabled by default.
8. Click **Next**
9. Under Data Residency, select **Enable Data Residency**
    - **IMPORTANT: Data Residency is required for FedRAMP High compliance**
10. Select the **Grant Roles Automatically** radio button
11. Click **Grant Roles**
12. Click **Next** once the roles have successfully been granted.
13. Click **Finish** once you have reached the **Ready to Complete Setup** screen
14. Navigate to [Compliance Center](https://console.cloud.google.com/security/command-center/compliance)
15. In the **Project Selector**, select your organization
16. Wait about **24 hours** for the scans to complete and for the reports to be generated

## Appendix

### Resources
- [Security Command Center Overview](https://cloud.google.com/security-command-center/docs/security-command-center-overview)
- [Overview of Organization-Level Activation](https://cloud.google.com/security-command-center/docs/activate-scc-overview#overview_of_organization-level_activation)
- [Activate the Security Command Center Standard/Premium Tier for an Organization](https://cloud.google.com/security-command-center/docs/activate-scc-for-an-organization)
- [Set Up Permissions](https://cloud.google.com/security-command-center/docs/activate-scc-for-an-organization#set_up_permissions)
