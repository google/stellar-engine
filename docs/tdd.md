# **Stellar Engine**

Technical Design Document

Date updated: December 5, 2025

| <strong>Created:</strong>             |                                                                 |
| :------------------------------------ | :-------------------------------------------------------------- |
| <strong>Updated:</strong>             |                                                                 |
| <strong>Version:</strong>             | v3.0                                                            |
| <strong>Most recent changes:</strong> | Updates to reflect new architecture; Administrative corrections |

Contents

_This document is intended to be a technical working document to help manage the
delivery of a project and is provided for illustrative purposes only. The
activities and goals serve as guidelines and additional detail, and do not
supersede any legal terms or conditions as defined in the customer’s written
contract with Google. _

# 1.0 Purpose

Extending [Cloud Foundation
Fabric](https://github.com/GoogleCloudPlatform/cloud-foundation-fabric), Stellar
Engine provides compliant Google Cloud infrastructure and opinionated
architecture patterns for supported [Assured
Workloads](https://cloud.google.com/security/products/assured-workloads?hl=en)
compliance regimes, including Google best practices and cybersecurity
documentation to aid in the Federal Authorization to Operate (ATO) process.
Stellar Engine is designed as an accelerator for technology teams supporting
Google Cloud customer and partner engagements.

Specifically, Stellar Engine:

- Templatizes and automates the initial GCP foundations phases of a GPS
  Professional Services Organization (PSO) customer engagement
- Provides a common base on which to build GPS reference architectures and
  solutions
- Supports PSO customers with an Impact Level 5 (IL5) compliant Infrastructure
  as Code (IaC) framework that they can adopt
- Provides PSO the ability to extend the codebase to be compliant with other
  Federal Government programs in future engagements
- Eases the use of GCP and Terraform for GPS customers

This document is not intended to inform users on Security Best Practices. For
information on post deployment recommendations, please see the [Security Best
Practices Guide
(SBPG)](https://docs.google.com/document/d/1uv62Fqg73r9oJNP-NPZebpzoBom8rOgLoHkiMZPutbo/edit?tab=t.0#heading=h.gjdgxs).

# 2.0 Executive Summary

The supplied structure and code is intended to form a starting point for
building your own foundation with pragmatic defaults that you can customize to
meet your own requirements. Currently, all code is deployed manually as we
determine a path forward that embraces automation – such as Github Actions,
GitLab CI/CD, or Cloud Build – and is compliant with established IL5
regulations.

A root folder is created at the top of the organization to hold all projects and
resources. From the root folder, tenants can be created in either an Assured
Workloads folder with configurable compliance regime, such as FedRAMP High or
IL5, based on the needs of the user. Each deployment initially creates a
development environment with the intention of users migrating to a production
environment after the development environment has been fully built and tested.

## 2.1 Overview

Stellar Engine is provisioned through a series of bootstrap scripts to create a
baseline environment within an Assured Workloads folder. Once the environment is
provisioned, users can pick and choose what services to deploy based on their
specific use case (see Section 3.4 for more details). In addition to Google
Cloud services, the IaC provides users the flexibility to provision third-party
offerings to operate within the Stellar Engine environment.

## 2.2 Project Architecture

In the _example.com_ architecture, a series of projects reside under the
organization node, which contains resources that are used across the
_example.com_ organization. These projects, detailed in the table below, provide
various enterprise functions and are created through the infrastructure
deployment pipeline.

| Project              | Description                                                                                                                                                         |     |
| :------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------ | :-- |
| org-iac-core-0       | Contains the deployment pipeline that's used to build out the foundation components of the organization. <strong>This project should be highly restricted</strong>. |     |
| org-audit-logs-0     | Provides a destination for log sinks and detective controls.                                                                                                        |     |
| org-billing-export-0 | Contains a BigQuery dataset with the organization's <a href='https://cloud.google.com/billing/docs/how-to/export-data-bigquery'>billing exports</a>. (optional)     |     |

# 3.0 Cloud Foundation

## 3.1 Project Organization

.The following policies are implemented at the organization level via Terraform.
They are applied using a combination of Google-managed defaults and custom
constraints defined in YAML files (data/org-policies/ and
data/custom-org-policies/).

### Network Security & Isolation:

- compute.vmExternalIpAccess: Deny All. VMs cannot be created with external IP
  addresses.
- compute.skipDefaultNetworkCreation: Enforced. Skips creation of the default
  network in new projects.
- compute.restrictProtocolForwardingCreationForTypes: Restricted to INTERNAL.
  New forwarding rules must use internal IP addresses.
- compute.restrictLoadBalancerCreationForTypes: Restricted to INTERNAL. Only
  internal load balancers are allowed.
- compute.disableGlobalLoadBalancing: Enforced. Global load balancing is
  disabled.
- compute.disableGlobalCloudArmorPolicy: Enforced. Global Cloud Armor policies
  are disabled.
- compute.disableGlobalSelfManagedSslCertificate: Enforced. Global
  self-managed SSL certificates are disabled.
- compute.restrictCloudNATUsage: Restricted to organization resources.
- compute.restrictDedicatedInterconnectUsage: Restricted to organization
  resources.
- compute.restrictPartnerInterconnectUsage: Restricted to organization
  resources.
- compute.restrictVpcPeering: Restricted to organization resources and
  specific allowed folders.
- compute.setNewProjectDefaultToZonalDNSOnly: Enforced. Newly created projects
  use Zonal DNS by default.
- sql.restrictAuthorizedNetworks: Enforced. Prevents adding authorized
  networks for unproxied Cloud SQL access.
- sql.restrictPublicIp: Enforced. Restricts public IP addresses on Cloud SQL
  instances.

### Data Security & Encryption:

- custom.kmsRotation: Enforced. Requires proper rotation period for KMS keys
  (Custom Constraint).
- storage.uniformBucketLevelAccess: Enforced. Buckets must use uniform
  bucket-level access.
- storage.publicAccessPrevention: Enforced. Prevents public access to Cloud
  Storage buckets.
- storage.secureHttpTransport: Enforced. Requires HTTPS for Cloud Storage.
- appengine.disableCodeDownload: Enforced. Disables downloading source code
  from App Engine.
- bigquery.disableBQOmniAWS: Enforced. Disables BigQuery Omni for AWS.
- bigquery.disableBQOmniAzure: Enforced. Disables BigQuery Omni for Azure.

### IAM & Service Accounts:

- iam.managed.disableServiceAccountKeyCreation: Enforced.
- iam.managed.disableServiceAccountKeyUpload: Enforced.
- iam.managed.preventPrivilegedBasicRolesForDefaultServiceAccounts: Enforced.
- iam.automaticIamGrantsForDefaultServiceAccounts: Enforced. Prevents
  automatic role grants for default service accounts.
- iam.serviceAccountKeyExposureResponse: DISABLE_KEY. Automatically disables
  exposed keys.
- iam.allowedPolicyMemberDomains: Restricted to the customer ID and allowed
  domains.
- essentialcontacts.managed.allowedContactDomains: Restricted to allowed
  domains.
- essentialcontacts.allowedContactDomains: Restricted to the organization's
  domain.

### Serverless Security (Cloud Run & Functions):

- cloudfunctions.allowedIngressSettings: ALLOW_INTERNAL_AND_GCLB. Restricts
  function ingress.
- cloudfunctions.allowedVpcConnectorEgressSettings: ALL_TRAFFIC. Forces all
  traffic through VPC connector.
- run.allowedIngress: internal-and-cloud-load-balancing. Restricts Cloud Run
  ingress.
- run.allowedVPCEgress: all-traffic. Forces all Cloud Run traffic through VPC
  connector.
- cloudbuild.allowedIntegrations: Restricted to github.com.

### Resource Management:

- resourcemanager.allowedImportSources: Restricted to the organization.
- resourcemanager.allowedExportDestinations: Restricted to the organization.
- resourcemanager.accessBoundaries: Restricted to the organization (Cloud
  Console visibility).

The purpose of this step is to create the below resources. The names of the
folders can be modified in 1-resman folders.

**Folders:**

- Root level folders
  - Folder representing an organization root - Eg: Organization Business
    Unit
- First level folders
  - Common Services
  - Test
  - Integration
  - Production
- Second level folders
  - Network - Downstream of Common Services. Network hub folder, contains
    all the networking projects.
  - Security - Downstream of Common Services. Centralized security services
    folder. Contains IAC Core, Audit Logs, and Billing Export projects.
  - Tenant - Downstream of Test/Integration/Prod folders.
- Third Level Folders
  - Tenant Core - Contains Tenant IAC Core project
  - Tenant Main - Contains Tenant Main Project

The structure below is an example of a nested layout conforming to the proposed
cloud project organization.

Example Organization

- Organization Root Folder
  - Network-IL5
    - Production
      - \<prefix\>-prod-net-landing-0
      - \<prefix\>-prod-net-spoke-0
    - Development
      - \<prefix\>-dev-net-landing-0
      - \<prefix\>-dev-net-spoke-0
  - Security
    - \<prefix\>-prod-security-core-0
    - \<prefix-dev-security-core-0
  - Tenants
    - Workstream-A-IL5
      - Workstream Core
        - \<prefix\>-workstream-a-iac-core-0
      - Workstream Tenant
        - Project-A
        - Project-B
    - Workstream-B-IL4
      - Workstream Core
        - \<prefix\>-workstream-b-iac-core-0
      - Workstream Tenant
        - Project-C
        - Project-D

## 3.2 IAM

### IAM Principles

These are the cybersecurity design principles that guide the IAM settings.

- IAM Policy is defined by Infrastructure-as-code (IaC) and enforced by Google
  IAM. The IaC used to define this policy is reviewed and submitted using
  Terraform. Using this code:
  - No human should have permissions to create or modify cloud resources in
    any environment other than a development environment. Even in a
    development environment, these permissions should be tightly controlled.
  - The Cloud Resource Manager access required to execute Terraform code
    will be assigned to a unique service account defined by Stellar Engine.
    - This service account will only be used by the CI/CD pipeline for
      terraform apply actions.
  - **Note:** Broader permissions may be given to development projects to
    accelerate the rate of development. This should only be done under
    extreme caution, and permissions should not propagate to any environment
    other than the development environment (e.g., testing, staging, or
    production).
- Human access
  - Access must be granted to groups, not individual users.
  - Access will be granted based on a minimalized set of curated roles.
  - Access is granted based on the principle of least privilege, with only
    the minimum amount of access granted to perform a function.
- Machine access
  - Individual Service Accounts will be defined for each microservice.&#9;
  - Downloadable Service Account keys will not be used and their creation
    should be disabled by organization policy.
  - Access will be granted based on the principle of least privilege, with
    only necessary functionality granted for the microservice.
  - Disable automatic role grants to default service accounts
    (*iam.automaticIamGrantsForDefaultServiceAccounts ) *should be enabled
    as organization policy , this will remove the editor role from the
    default service accounts.

The IAM model used in GCP is illustrated in the diagram below:

GCP Pre-Defined Roles will be used, custom roles are not recommended due to
lifecycle management burdens.

### Role Groups

Role Groups are created corresponding to the various development and
administrative roles needed to build and maintain the application.

- Roles are identified by development and administrative teams.
- Groups are created for each role and owned by X. The bootstrap Terraform
  service account is an owner of each of these groups.
  - Group naming convention: **gcp-X-${tenant}-${role}@X.gov**
- Initial role group memberships needed for system provisioning are checked
  into Terraform code and applied by the bootstrap Terraform service accounts.
  Ongoing role group membership management should be implemented with
  customers existing IAM systems, or should continue to use the Terraform IaC
  method.

#### GCP Initial Role Groups

The initial _role groups_ created during the GCP organization set up and their
assigned _roles_ at the _organization level_ are:

| Role Group              | Description                                                                                                                          | Assigned Roles @ Org Level                                                                                                                                                                                                                                  |
| :---------------------- | :----------------------------------------------------------------------------------------------------------------------------------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| gcp-organization-admins | Org admins have access to administer all resources belong to the organization                                                        | - Billing Account User<br/>- Support Account Admin<br/>- Organization Role Admin<br/>- Organization Policy Admin<br/>- Folder Admin<br/>- Organization Admin                                                                                                |
| gcp-billing-admins      | set up billing accounts and monitoring their usage                                                                                   | - Billing Account Administrator<br/>- Billing Account Creator<br/>- Organization Viewer                                                                                                                                                                     |
| gcp-vpc-network-admins  | creating networks, subnets, firewall rules, and network devices such as router, vpn, and load balancers                              | - Compute Network Admin<br/>- Compute Security Admin<br/>- Compute Shared VPC Admin<br/>- Folder Viewer                                                                                                                                                     |
| gcp-logging-admins      | have access to all features of logging                                                                                               | -Logging Admin                                                                                                                                                                                                                                              |
| gcp-logging-viewers     | have read-only access to a specific subsets of logs ingested into logging                                                            | - Logging Viewer                                                                                                                                                                                                                                            |
| gcp-monitoring-admins   | have access to use and configure all features of Cloud Monitoring                                                                    | - Monitoring Admin                                                                                                                                                                                                                                          |
| gcp-security-admins     | establish and manage security policies for the entire organization, including access management and organization constraint policies | - Compute Viewer<br/>- Kubernetes Engine Viewer<br/>- Organization Role Viewer<br/>- Security Reviewer<br/>- Logs Configuration Writer<br/>- Private Logs Viewer<br/>- Organization Policy Administrator<br/>- Folder IAM Admin<br/>- Security Center Admin |
| gcp-developers          | design, develop and test applications                                                                                                | No default roles at the organization level.                                                                                                                                                                                                                 |
| gcp-devops              | create or manage end-to-end pipelines that support CICD, monitoring, and system provisioning                                         | - Folder Viewer<br/>- Organization Viewer*<br/>- Organization Policy Viewer*<br/>- Logging Viewer\*                                                                                                                                                         |

Not all above role groups are mandatory, and one GCP group can be mapped to
multiple role groups.

#### Additional Role Groups to Role Mapping

Stellar Engine adds additional role groups and role mappings at the top node
level (could be Organization or a Folder, depending on customer environment) and
projects levels for custom groups.

| Group                   | Description                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| :---------------------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| gcp-organization-admins | Administer all organization resources. Assign this role only to your most trusted users.                                                                                                                                                                                                                                                                                                                                                                         |
| gcp-billing-admins      | Set up billing accounts and monitor usage.                                                                                                                                                                                                                                                                                                                                                                                                                       |
| gcp-vpc-network-admins  | Create networks, subnets, firewall rules, and network devices such as Cloud Router, Cloud VPN, and load balancers.                                                                                                                                                                                                                                                                                                                                               |
| gcp-logging-admins      | Use all Cloud Logging features.                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| gcp-logging-viewers     | Read-only access to a subset of logs.                                                                                                                                                                                                                                                                                                                                                                                                                            |
| gcp-monitoring-admins   | Establishing and managing security policies for the entire organization, including access management and <a href='https://cloud.google.com/resource-manager/docs/organization-policy/org-policy-constraints'>organization constraint policies</a>. See the <a href='https://cloud.google.com/architecture/security-foundations'>Google Cloud enterprise foundations blueprint</a> for more information about planning your Google Cloud security infrastructure. |
| gcp-security-admins     | Establish and manage security policies for the entire organization, including access management and organization constraint policies.                                                                                                                                                                                                                                                                                                                            |
| gcp-developers          | Design, code, and test applications.                                                                                                                                                                                                                                                                                                                                                                                                                             |
| gcp-devops              | Create or manage end-to-end pipelines that support continuous integration and delivery, monitoring, and system provisioning.                                                                                                                                                                                                                                                                                                                                     |

#### Application Specific Groups

There could be additional groups with role bindings for each tenant and/or
service platforms. This is beyond the scope of Stellar Engine but worth
mentioning here so that we can have a complete picture of the role group
management.

For example, a secured data warehouse blueprint defines the following groups:

- Data analyst group
- Data engineer group
- Network administrator group
- Security administrator group
- Security analyst group

Some above groups can be mapped to existing groups which Stellar Engine defines,
but some new groups need to be created and managed.

### Service Accounts

Multiple service accounts are used across Stellar Engine. This is to maintain
principles of least privilege and ensure service accounts are used for a
singular purpose, so as not to make them overly permissive.

Additional restrictions can be set to service accounts, including:

- Disable automatic role grants to default service accounts\*
- Disable service account creation
- Disable service account key creation\*
- Disable service account key upload\*
- Disable attachment of service accounts to resources in other projects
- Restrict removal of project liens when service accounts are used across
  projects

####

Policies with (\*) are recommended.

#### Initial Service Account in bootstrap phase

A system administrator with an individual GCP account can run the bootstrap
phase, or they can impersonate a service account to do so. The preferred and
suggested method is to use an individual account with the gcp_org_admins group
membership assigned to ensure the required privileges are assigned. This account
should be tightly controlled and disabled when not in use.

To run the bootstrap phase using the service account, grant the following roles
outside of Terraform:

- Organization Admin of the GCP Organization if the root node is the
  Organization itself.
- Organization Policy Admin of the GCP Organization, to manage organization
  policies.
- Billing Admin of the Billing Account, or at minimum the Billing User role,
  to create projects.
- Folder Creator, also to create folders and projects.
- Access Context Manager Admin, to create VPC SC policies.
- Assured Workloads Admin, to create assured workloads folders.

The minimum set of roles needed to run the bootstrap phase in a given assured
workloads folder are:

- Organization Viewer, to query organization level resources.
- Organization Policy Admin, to manage organization policies.
- Billing User of the Billing Account, to create new projects.
- Folder Creator, also to create new folders and projects.
- Access Context Manager, to create VPC SC policies.
- Security Admin, to manage security command center and security events.

### IAM roles

Our IAM bindings for the Stellar Engine projects are taken from the Cloud
Foundations Fabric guidelines. They are as follows:

#### Organization _\[organization \#0\]_

| <strong>members</strong>                                               | <strong>roles</strong>                                                                                                                                                                                                                                            |
| :--------------------------------------------------------------------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| <strong>dev-resman-pf-0</strong><br/><strong>serviceAccount</strong>   | <a href='https://cloud.google.com/iam/docs/understanding-roles#orgpolicy.policyAdmin'>roles/orgpolicy.policyAdmin</a> +•                                                                                                                                          |
| <strong>prod-resman-net-0</strong><br/><strong>serviceAccount</strong> | <a href='https://cloud.google.com/iam/docs/understanding-roles#compute.orgFirewallPolicyAdmin'>roles/compute.orgFirewallPolicyAdmin</a> +<br/><a href='https://cloud.google.com/iam/docs/understanding-roles#compute.xpnAdmin'>roles/compute.xpnAdmin</a> +       |
| <strong>prod-resman-pf-0</strong><br/><strong>serviceAccount</strong>  | <a href='https://cloud.google.com/iam/docs/understanding-roles#orgpolicy.policyAdmin'>roles/orgpolicy.policyAdmin</a> +•                                                                                                                                          |
| <strong>prod-resman-sec-0</strong><br/><strong>serviceAccount</strong> | <a href='https://cloud.google.com/iam/docs/understanding-roles#cloudasset.viewer'>roles/cloudasset.viewer</a> +<br/><a href='https://cloud.google.com/iam/docs/understanding-roles#accesscontextmanager.policyAdmin'>roles/accesscontextmanager.policyAdmin</a> + |

#### Folder _data platform/development_

| <strong>members</strong>                                              | <strong>roles</strong>                                                                                                                                                                                                          |
| :-------------------------------------------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| <strong>dev-resman-dp-0</strong><br/><strong>serviceAccount</strong>  | organizations/[organization #0]/roles/serviceProjectNetworkAdmin<br/>roles/logging.admin<br/>roles/owner<br/>roles/resourcemanager.folderAdmin<br/>roles/resourcemanager.projectCreator                                         |
| <strong>dev-resman-dp-0r</strong><br/><strong>serviceAccount</strong> | <a href='https://cloud.google.com/iam/docs/understanding-roles#resourcemanager.folderViewer'>roles/resourcemanager.folderViewer</a><br/><a href='https://cloud.google.com/iam/docs/understanding-roles#viewer'>roles/viewer</a> |

#### Folder _data platform/production_

| <strong>members</strong>                                               | <strong>roles</strong>                                                                                                                                                                                                          |
| :--------------------------------------------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| <strong>prod-resman-dp-0</strong><br/><strong>serviceAccount</strong>  | organizations/[organization #0]/roles/serviceProjectNetworkAdmin<br/>roles/logging.admin<br/>roles/owner<br/>roles/resourcemanager.folderAdmin<br/>roles/resourcemanager.projectCreator                                         |
| <strong>prod-resman-dp-0r</strong><br/><strong>serviceAccount</strong> | <a href='https://cloud.google.com/iam/docs/understanding-roles#resourcemanager.folderViewer'>roles/resourcemanager.folderViewer</a><br/><a href='https://cloud.google.com/iam/docs/understanding-roles#viewer'>roles/viewer</a> |

#### Folder _gke/development_

| <strong>members</strong>                                               | <strong>roles</strong>                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| :--------------------------------------------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| <strong>dev-resman-gke-0</strong><br/><strong>serviceAccount</strong>  | <a href='https://cloud.google.com/iam/docs/understanding-roles#compute.xpnAdmin'>roles/compute.xpnAdmin</a><br/><a href='https://cloud.google.com/iam/docs/understanding-roles#logging.admin'>roles/logging.admin</a><br/><a href='https://cloud.google.com/iam/docs/understanding-roles#owner'>roles/owner</a><br/><a href='https://cloud.google.com/iam/docs/understanding-roles#resourcemanager.folderAdmin'>roles/resourcemanager.folderAdmin</a><br/><a href='https://cloud.google.com/iam/docs/understanding-roles#resourcemanager.projectCreator'>roles/resourcemanager.projectCreator</a> |
| <strong>dev-resman-gke-0r</strong><br/><strong>serviceAccount</strong> | <a href='https://cloud.google.com/iam/docs/understanding-roles#resourcemanager.folderViewer'>roles/resourcemanager.folderViewer</a><br/><a href='https://cloud.google.com/iam/docs/understanding-roles#viewer'>roles/viewer</a>                                                                                                                                                                                                                                                                                                                                                                   |

#### Folder _gke/production_

| <strong>members</strong>                                                | <strong>roles</strong>                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| :---------------------------------------------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| <strong>prod-resman-gke-0</strong><br/><strong>serviceAccount</strong>  | <a href='https://cloud.google.com/iam/docs/understanding-roles#compute.xpnAdmin'>roles/compute.xpnAdmin</a><br/><a href='https://cloud.google.com/iam/docs/understanding-roles#logging.admin'>roles/logging.admin</a><br/><a href='https://cloud.google.com/iam/docs/understanding-roles#owner'>roles/owner</a><br/><a href='https://cloud.google.com/iam/docs/understanding-roles#resourcemanager.folderAdmin'>roles/resourcemanager.folderAdmin</a><br/><a href='https://cloud.google.com/iam/docs/understanding-roles#resourcemanager.projectCreator'>roles/resourcemanager.projectCreator</a> |
| <strong>prod-resman-gke-0r</strong><br/><strong>serviceAccount</strong> | <a href='https://cloud.google.com/iam/docs/understanding-roles#resourcemanager.folderViewer'>roles/resourcemanager.folderViewer</a><br/><a href='https://cloud.google.com/iam/docs/understanding-roles#viewer'>roles/viewer</a>                                                                                                                                                                                                                                                                                                                                                                   |

#### Folder _networking_

| <strong>members</strong>                                                | <strong>roles</strong>                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| :---------------------------------------------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| <strong>gcp-network-admins</strong><br/><strong>group</strong>          | <a href='https://cloud.google.com/iam/docs/understanding-roles#editor'>roles/editor</a>                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| <strong>prod-resman-net-0</strong><br/><strong>serviceAccount</strong>  | <a href='https://cloud.google.com/iam/docs/understanding-roles#compute.xpnAdmin'>roles/compute.xpnAdmin</a><br/><a href='https://cloud.google.com/iam/docs/understanding-roles#logging.admin'>roles/logging.admin</a><br/><a href='https://cloud.google.com/iam/docs/understanding-roles#owner'>roles/owner</a><br/><a href='https://cloud.google.com/iam/docs/understanding-roles#resourcemanager.folderAdmin'>roles/resourcemanager.folderAdmin</a><br/><a href='https://cloud.google.com/iam/docs/understanding-roles#resourcemanager.projectCreator'>roles/resourcemanager.projectCreator</a> |
| <strong>prod-resman-net-0r</strong><br/><strong>serviceAccount</strong> | <a href='https://cloud.google.com/iam/docs/understanding-roles#resourcemanager.folderViewer'>roles/resourcemanager.folderViewer</a><br/><a href='https://cloud.google.com/iam/docs/understanding-roles#viewer'>roles/viewer</a>                                                                                                                                                                                                                                                                                                                                                                   |

#### Folder _networking/development_

| <strong>members</strong>                                               | <strong>roles</strong>                                                                                                |
| :--------------------------------------------------------------------- | :-------------------------------------------------------------------------------------------------------------------- |
| <strong>dev-resman-dp-0</strong><br/><strong>serviceAccount</strong>   | organizations/[organization #0]/roles/serviceProjectNetworkAdmin                                                      |
| <strong>dev-resman-dp-0r</strong><br/><strong>serviceAccount</strong>  | <a href='https://cloud.google.com/iam/docs/understanding-roles#compute.networkViewer'>roles/compute.networkViewer</a> |
| <strong>dev-resman-gke-0</strong><br/><strong>serviceAccount</strong>  | organizations/[organization #0]/roles/serviceProjectNetworkAdmin                                                      |
| <strong>dev-resman-gke-0r</strong><br/><strong>serviceAccount</strong> | <a href='https://cloud.google.com/iam/docs/understanding-roles#compute.networkViewer'>roles/compute.networkViewer</a> |
| <strong>dev-resman-pf-0</strong><br/><strong>serviceAccount</strong>   | organizations/[organization #0]/roles/serviceProjectNetworkAdmin                                                      |
| <strong>dev-resman-pf-0r</strong><br/><strong>serviceAccount</strong>  | <a href='https://cloud.google.com/iam/docs/understanding-roles#compute.networkViewer'>roles/compute.networkViewer</a> |

#### Folder _networking/production_

| <strong>members</strong>                                                | <strong>roles</strong>                                                                                                |
| :---------------------------------------------------------------------- | :-------------------------------------------------------------------------------------------------------------------- |
| <strong>prod-resman-dp-0</strong><br/><strong>serviceAccount</strong>   | organizations/[organization #0]/roles/serviceProjectNetworkAdmin                                                      |
| <strong>prod-resman-dp-0r</strong><br/><strong>serviceAccount</strong>  | <a href='https://cloud.google.com/iam/docs/understanding-roles#compute.networkViewer'>roles/compute.networkViewer</a> |
| <strong>prod-resman-gke-0</strong><br/><strong>serviceAccount</strong>  | organizations/[organization #0]/roles/serviceProjectNetworkAdmin                                                      |
| <strong>prod-resman-gke-0r</strong><br/><strong>serviceAccount</strong> | <a href='https://cloud.google.com/iam/docs/understanding-roles#compute.networkViewer'>roles/compute.networkViewer</a> |
| <strong>prod-resman-pf-0</strong><br/><strong>serviceAccount</strong>   | organizations/[organization #0]/roles/serviceProjectNetworkAdmin                                                      |
| <strong>prod-resman-pf-0r</strong><br/><strong>serviceAccount</strong>  | <a href='https://cloud.google.com/iam/docs/understanding-roles#compute.networkViewer'>roles/compute.networkViewer</a> |

#### Project _prod-iac-core-0_

| <strong>members</strong>                                                  | <strong>roles</strong>                                                                                                                          |
| :------------------------------------------------------------------------ | :---------------------------------------------------------------------------------------------------------------------------------------------- |
| <strong>dev-resman-dp-0</strong><br/><strong>serviceAccount</strong>      | <a href='https://cloud.google.com/iam/docs/understanding-roles#serviceusage.serviceUsageConsumer'>roles/serviceusage.serviceUsageConsumer</a> + |
| <strong>dev-resman-dp-0r</strong><br/><strong>serviceAccount</strong>     | <a href='https://cloud.google.com/iam/docs/understanding-roles#serviceusage.serviceUsageConsumer'>roles/serviceusage.serviceUsageConsumer</a> + |
| <strong>dev-resman-gke-0</strong><br/><strong>serviceAccount</strong>     | <a href='https://cloud.google.com/iam/docs/understanding-roles#serviceusage.serviceUsageConsumer'>roles/serviceusage.serviceUsageConsumer</a> + |
| <strong>dev-resman-gke-0r</strong><br/><strong>serviceAccount</strong>    | <a href='https://cloud.google.com/iam/docs/understanding-roles#serviceusage.serviceUsageConsumer'>roles/serviceusage.serviceUsageConsumer</a> + |
| <strong>dev-resman-pf-0</strong><br/><strong>serviceAccount</strong>      | <a href='https://cloud.google.com/iam/docs/understanding-roles#serviceusage.serviceUsageConsumer'>roles/serviceusage.serviceUsageConsumer</a> + |
| <strong>dev-resman-pf-0r</strong><br/><strong>serviceAccount</strong>     | <a href='https://cloud.google.com/iam/docs/understanding-roles#serviceusage.serviceUsageConsumer'>roles/serviceusage.serviceUsageConsumer</a> + |
| <strong>dev-resman-sbox-0</strong><br/><strong>serviceAccount</strong>    | <a href='https://cloud.google.com/iam/docs/understanding-roles#serviceusage.serviceUsageConsumer'>roles/serviceusage.serviceUsageConsumer</a> + |
| <strong>prod-resman-dp-0r</strong><br/><strong>serviceAccount</strong>    | <a href='https://cloud.google.com/iam/docs/understanding-roles#serviceusage.serviceUsageConsumer'>roles/serviceusage.serviceUsageConsumer</a> + |
| <strong>prod-resman-gke-0</strong><br/><strong>serviceAccount</strong>    | <a href='https://cloud.google.com/iam/docs/understanding-roles#serviceusage.serviceUsageConsumer'>roles/serviceusage.serviceUsageConsumer</a> + |
| <strong>prod-resman-gke-0r</strong><br/><strong>serviceAccount</strong>   | <a href='https://cloud.google.com/iam/docs/understanding-roles#serviceusage.serviceUsageConsumer'>roles/serviceusage.serviceUsageConsumer</a> + |
| <strong>prod-resman-net-0</strong><br/><strong>serviceAccount</strong>    | <a href='https://cloud.google.com/iam/docs/understanding-roles#serviceusage.serviceUsageConsumer'>roles/serviceusage.serviceUsageConsumer</a> + |
| <strong>prod-resman-net-0r</strong><br/><strong>serviceAccount</strong>   | <a href='https://cloud.google.com/iam/docs/understanding-roles#serviceusage.serviceUsageConsumer'>roles/serviceusage.serviceUsageConsumer</a> + |
| <strong>prod-resman-net-1</strong><br/><strong>serviceAccount</strong>    | <a href='https://cloud.google.com/iam/docs/understanding-roles#logging.logWriter'>roles/logging.logWriter</a> +                                 |
| <strong>prod-resman-net-1r</strong><br/><strong>serviceAccount</strong>   | <a href='https://cloud.google.com/iam/docs/understanding-roles#logging.logWriter'>roles/logging.logWriter</a> +                                 |
| <strong>prod-resman-pf-0</strong><br/><strong>serviceAccount</strong>     | <a href='https://cloud.google.com/iam/docs/understanding-roles#serviceusage.serviceUsageConsumer'>roles/serviceusage.serviceUsageConsumer</a> + |
| <strong>prod-resman-pf-0r</strong><br/><strong>serviceAccount</strong>    | <a href='https://cloud.google.com/iam/docs/understanding-roles#serviceusage.serviceUsageConsumer'>roles/serviceusage.serviceUsageConsumer</a> + |
| <strong>prod-resman-sec-0</strong><br/><strong>serviceAccount</strong>    | <a href='https://cloud.google.com/iam/docs/understanding-roles#serviceusage.serviceUsageConsumer'>roles/serviceusage.serviceUsageConsumer</a> + |
| <strong>prod-resman-sec-0r</strong><br/><strong>serviceAccount</strong>   | <a href='https://cloud.google.com/iam/docs/understanding-roles#serviceusage.serviceUsageConsumer'>roles/serviceusage.serviceUsageConsumer</a> + |
| <strong>prod-resman-sec-1</strong><br/><strong>serviceAccount</strong>    | <a href='https://cloud.google.com/iam/docs/understanding-roles#logging.logWriter'>roles/logging.logWriter</a> +                                 |
| <strong>prod-resman-sec-1r</strong><br/><strong>serviceAccount</strong>   | <a href='https://cloud.google.com/iam/docs/understanding-roles#logging.logWriter'>roles/logging.logWriter</a> +                                 |
| <strong>prod-resman-teams-0</strong><br/><strong>serviceAccount</strong>  | <a href='https://cloud.google.com/iam/docs/understanding-roles#serviceusage.serviceUsageConsumer'>roles/serviceusage.serviceUsageConsumer</a> + |
| <strong>prod-resman-test-3-0</strong><br/><strong>serviceAccount</strong> | <a href='https://cloud.google.com/iam/docs/understanding-roles#serviceusage.serviceUsageConsumer'>roles/serviceusage.serviceUsageConsumer</a> + |

**Legend: + additive, \* conditional**

IAM roles have been taken from the following Cloud Foundations Fabric document -
<https://github.com/GoogleCloudPlatform/cloud-foundation-fabric/blob/master/fast/stages/1-resman/IAM.md>.

## 3.3 Code Control

### GitHub Projects

Code has been forked off of the open-source Cloud Foundations Fabric (CFF)
GitHub repository.
The Stellar Engine project is fully open source and is maintained on GitHub.

[Cloud Foundations Fabric
GitHub](https://github.com/GoogleCloudPlatform/cloud-foundation-fabric)

[Google Public Sector Stellar Engine
GitHub](https://github.com/google/stellar-engine)

### Branches

Our development process follows a trunk-based branching strategy. This entails
having one main branch, with developers creating their own feature branches,
which are then merged back into the main branch upon completion. For more
information on trunk based branching, please see [Trunk Based
Branching](https://www.atlassian.com/continuous-delivery/continuous-integration/trunk-based-development).
Our branching strategy will follow Cloud Foundations Fabric’s branching strategy
upon reintroduction of our project’s repository into the larger repository.

### Validation

Currently, development happens on feature and bug fix branches. When complete, a
[pull request
(PR)](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/about-pull-requests) can be opened
targeting the main branch. After two reviewers have submitted comments, and
their recommendations have been adjudicated (which can be an iterative process)
the feature branch is merged into the main branch.

## 3.4 Infrastructure-as-Code

Stellar Engine Terraform configuration is based on the deployment process from
[Google Cloud Foundation
Fabric](https://github.com/GoogleCloudPlatform/cloud-foundation-fabric).
Successful deployment requires prerequisite steps, labeled 0 through 3, to be
completed before the deployment is ready for further development. The project’s
state is managed by a single backend, but can use multiple state files within
this backend.

- Terraform configuration is stored in an infrastructure code repository.
  Repository access is limited to infrastructure administrators.
- Once the initial bootstrap environment is created by infrastructure admins,
  all configuration changes are gated by a code review in the infrastructure
  repository.

### File Structure

Initial deployment/bootstrapping is achieved via the code in the
**fast/stages** or **fast/stages-aw** folders. The **modules** folder contains a series of
portable Terraform code designed to fast track the deployment of individual GCP
services. The **blueprints** folder contains use cases of these modules, with
the use case represented by the name of the corresponding subfolder, (for
example, the **il5** folder is designed for deployments within an IL5
environment.) A subset of the file structure containing IaC is listed below.

- **blueprints**
  - **fedramp-high**
    - **access-context-manager**
    - **app-engine**
    - **artifact-registry**
    - **bastion-pattern**
    - **bcap**
    - **beyondcorp**
    - **bigtable**
    - **bq-project**
    - **cloud-armor**
    - **cloud-composer-environment**
    - **cloud-functions**
    - **cloud-ids**
    - **cloud-run**
    - **cloud-scheduler-job**
    - **cloud-spanner**
    - **cloud-translation**
    - **cloud-workstations**
    - **cnap**
    - **compute-engine**
    - **dataflow**
    - **datafusion**
    - **dataproc-cluster**
    - **datastore**
    - **document-ai**
    - **firestore**
    - **gcs-project**
    - **gemini-enterprise**
    - **gitlab**
    - **gke**
    - **gke-hardened**
    - **kms-project**
    - **network-connectivity-center**
    - **postgresql**
    - **private-service-connect**
    - **pub-sub-project**
    - **secret-manager**
    - **shielded-vm-project**
    - **vertex-mlops**
    - **workflows**
  - **il5**
    - **artifact-registry**
    - **bastion-pattern**
    - **bcap**
    - **bigquery**
    - **bq-project**
    - **compute-engine**
    - **dataflow**
    - **gcs-project**
    - **gke**
    - **gke-hardened**
    - **kms-project**
    - **postgresql**
    - **private-service-connect**
    - **pub-sub-project**
    - **shielded-vm-project**
- **fast**
  - **stages-aw**
    - **0-bootstrap**
    - **1-resman**
    - **2-networking-a-fedramp-high**
    - **2-networking-b-il5-ngfw**
    - **3-security**
- **modules**
  - **access-context-manager**
  - **alloydb**
  - **analytics-hub**
  - **api-gateway**
  - **apigee**
  - **app-engine**
  - **artifact-registry**
  - **beyondcorp**
  - **biglake-catalog**
  - **bigquery-dataset**
  - **bigtable-instance**
  - **billing-account**
  - **binauthz**
  - **certificate-authority-service**
  - **certificate-manager**
  - **cis-log-alerts**
  - **cis-log-metrics**
  - **cloud-config-container**
  - **cloud-function-v1**
  - **cloud-function-v2**
  - **cloud-identity-group**
  - **cloud-run**
  - **cloud-run-v2**
  - **cloud-run-v2-se**
  - **cloud-scheduler**
  - **cloudsql-instance**
  - **compute-mig**
  - **compute-vm**
  - **container-registry**
  - **data-catalog-policy-tag**
  - **data-catalog-tag**
  - **data-catalog-tag-template**
  - **dataform-repository**
  - **datafusion**
  - **datafusion-se**
  - **dataplex**
  - **dataplex-datascan**
  - **dataproc**
  - **dns**
  - **dns-response-policy**
  - **endpoints**
  - **firestore**
  - **folder**
  - **gcs**
  - **gcve-private-cloud**
  - **gke-cluster-autopilot**
  - **gke-cluster-standard**
  - **gke-cluster-standard-se**
  - **gke-hub**
  - **gke-nodepool**
  - **iam-service-account**
  - **intrusion-detection-system**
  - **kms**
  - **logging-bucket**
  - **looker-core**
  - **ncc-spoke-ra**
  - **net-address**
  - **net-cloudnat**
  - **net-firewall-policy**
  - **net-ipsec-over-interconnect**
  - **net-lb-app-ext**
  - **net-lb-app-ext-regional**
  - **net-lb-app-int**
  - **net-lb-app-int-cross-region**
  - **net-lb-ext**
  - **net-lb-int**
  - **net-lb-proxy-int**
  - **net-swp**
  - **net-vlan-attachment**
  - **net-vpc**
  - **net-vpc-firewall**
  - **net-vpc-peering**
  - **net-vpn-dynamic**
  - **net-vpn-ha**
  - **net-vpn-static**
  - **organization**
  - **organization-se**
  - **private-service-connect**
  - **project**
  - **project-factory**
  - **projects-data-source**
  - **pubsub**
  - **secret-manager**
  - **secure-source-manager-instance**
  - **service-directory**
  - **source-repository**
  - **spanner-instance**
  - **spanner-instance-se**
  - **vpc-sc**
  - **workflows**
  - **workstation-cluster**

## 3.5 Infrastructure-as-Code Principles

### Terraform Configuration

Terraform configuration is partitioned into stand-alone, per-environment
configuration modules. Additional customer tenants can be configured
per-environment. To facilitate rapid iteration and collaboration across tenants,
configuration is relatively static. Each combination of tenant and environment
has a dedicated configuration module. Each configuration module relies on
Terraform locals that reside in the same file.

This approach leads to a lot of repetition but minimizes the opportunity for
changes in one tenant or environment to impact any other.

Example:

```hcl
# project-specific locals
locals {
  step_terraform_sa = [
    "serviceAccount:${google_service_account.terraform-env-sa["bootstrap"].email}",
    "serviceAccount:${google_service_account.terraform-env-sa["org"].email}",
    "serviceAccount:${google_service_account.terraform-env-sa["env"].email}",
    "serviceAccount:${google_service_account.terraform-env-sa["net"].email}",
    "serviceAccount:${google_service_account.terraform-env-sa["proj"].email}",
  ]
  org_project_creators           = distinct(concat(var.org_project_creators, local.step_terraform_sa))
  parent                         = var.parent_folder != "" ? "folders/${var.parent_folder}" : "organizations/${var.org_id}"
  org_admins_org_iam_permissions = var.org_policy_admin_role == true ? [
    "roles/orgpolicy.policyAdmin", "roles/resourcemanager.organizationAdmin", "roles/billing.user"
  ] : ["roles/resourcemanager.organizationAdmin", "roles/billing.user"]
  group_org_admins     = var.groups.create_groups ? var.groups.required_groups.group_org_admins : var.group_org_admins
  group_billing_admins = var.groups.create_groups ? var.groups.required_groups.group_billing_admins : var.group_billing_admins
}

resource "google_folder" "bootstrap" {
  display_name = "${var.folder_prefix}-bootstrap"
  parent       = local.parent
}
```

## 3.6 Networking

### References:

### <https://cloud.google.com/architecture/security-foundations/networking>

### Flow Diagram

Google Cloud offers a robust architecture for managing Virtual Private Clouds
(VPCs) and facilitating communication among them using VPC Network Peering.
[Shared VPC](https://cloud.google.com/vpc/docs/shared-vpc) is a networking
construct that significantly reduces the amount of complexity in network design.
With Shared VPC, network policy and control for all networking resources are
centralized and easier to manage. Service project departments can configure and
manage non-network resources, enabling a clear separation of responsibilities
for different teams in the organization.

Resources in Shared VPC networks can communicate with each other securely and
efficiently across project boundaries using internal IP addresses. You can
manage shared network resources—such as subnets, routes, and firewalls—from a
central host project, so you can enforce consistent network policies across
projects.

As shown in the diagram below, the example.com architecture uses two Shared VPC
networks, base and restricted, as the default networking construct for each
environment. Each Shared VPC network is contained within a single project. The
base VPC network is used for deploying services that contain non-sensitive data,
and the restricted VPC network uses [VPC Service
Controls](https://cloud.google.com/vpc-service-controls) to limit access to
services that contain sensitive data.

You can implement the model described in the preceding section independently for
each of the four environments (common, development, non-production, and
production). This model provides the highest level of network segmentation
between environments.

For the above scenario, all environments can directly communicate with shared
resources in the common environment hub. The common environment can host tooling
that requires connectivity to other environments, like CI/CD infrastructure,
directories, and security and configuration management tools. As with the
previous independent Shared VPC model, the hub-and-spoke scenario is also
composed of base and restricted VPC networks. A base Shared VPC hub connects the
base Shared VPC network spokes in development, non-production, and production,
while the restricted Shared VPC hub connects the restricted Shared VPC network
spokes in these same environments. The choice between base and restricted Shared
VPC networks also depends on whether VPC Service Controls are required. For
workloads with strong data exfiltration mitigation requirements, the
hub-and-spoke associated with the restricted Shared VPC networks is preferred.

###

### VPCs

A VPC is a virtual network dedicated to a user's Google Cloud resources. It
provides isolation from other networks and allows customization of IP address
ranges, subnets, and routing tables. Consider if using a VPC to control traffic
and access is appropriate within the customers GCP organization.

Google VPC Network Peering

Google Cloud offers a robust architecture for managing Virtual Private Clouds
(VPCs) and facilitating communication among them using VPC Network Peering. VPC
Network Peering allows VPCs within the same project or across different projects
to communicate securely and efficiently using internal IPs. Peering connections
do not require any additional gateways or routers; traffic remains within
Google's backbone network, ensuring low latency and high reliability. VPC
Network Peering allows VPCs to exchange traffic securely and privately using
internal IP addresses. It facilitates communication between resources deployed
in different VPCs without needing to traverse the public internet.

###

### Subnet Allocations

Subnet allocation in Google Cloud involves the process of dividing the IP
address range of a Virtual Private Cloud (VPC) into smaller segments called
subnets. These subnets are then assigned to specific regions within GCP where
resources such as virtual machine (VM) instances, Kubernetes clusters, and other
services can be deployed. Our subnet allocation paradigm provides users the
ability to host eight organizations, with eight tenants per organization, with
eight projects per organization, for a maximum of 512 total projects.

The Table below displays the four Subnets allocation for Project 1 with
CIDR 10.200.2.0/23 having 512 IPs.

| <strong>Subnet Address</strong> | <strong>Range of Addresses</strong> | <strong>Useable IPs</strong> | <strong>Hosts</strong> |
| :------------------------------ | :---------------------------------- | :--------------------------- | :--------------------- |
| 10.200.2.0/25                   | 10.200.2.0 - 10.200.2.127           | 10.200.2.1 - 10.200.2.126    | 126                    |
| 10.200.2.128/25                 | 10.200.2.128 - 10.200.2.255         | 10.200.2.129 - 10.200.2.254  | 126                    |
| 10.200.3.0/25                   | 10.200.3.0 - 10.200.3.127           | 10.200.3.1 - 10.200.3.126    | 126                    |
| 10.200.3.128/25                 | 10.200.3.128 - 10.200.3.255         | 10.200.3.129 - 10.200.3.254  | 126                    |

Subnets are logical partitions within a VPC that define IP address ranges for
resources deployed in specific geographic locations (regions or availability
zones). Each subnet is associated with a specific region and availability zone
within that region. It is recommended to allocate a subnet for each application.
For example, a Google Kubernetes Engine (GKE) cluster would require a subnet and
two secondary ranges (one for pods and one for services). You can add the subnet
in the environments section in the Terraform networks stage, and reference the
subnet when configuring your cluster. When creating a VPC, you define a primary
IP address range (CIDR block) in IPv4 format (e.g., 10.200.2.0/23). This range
determines the total number of IP addresses available for allocation across all
subnets within the VPC.

When creating subnets within a VPC, you specify a subnet IP address range that
is a subset of the VPC's primary IP range. For example, if your VPC has the
range 10.200.2.0/23, you might create subnets with ranges
like 10.200.2.0/25, 10.200.2.128/25, 10.200.3.0/25 and 10.200.3.128/25 so on.

The Distribution of the CIDR as per Organization, Tenants and Projects

| <strong>Component</strong> | <strong>CIDR</strong> | <strong>Notes</strong>     |
| :------------------------- | :-------------------- | :------------------------- |
| Organization (All Tenants) | 10.200.0.0/16         | 8 Tenants per Organization |
| Tenants 1                  | 10.200.3.0/19         | 8 projects per tenant      |
| Project 1                  | 10.200.2.0/23         |                            |
| Project 2                  | 10.200.4.0/23         |                            |
| Project 3                  | 10.200.6.0/23         |                            |
| Project 4                  | 10.200.8.0/23         |                            |
| Project 5                  | 10.200.10.0/23        |                            |

Utilize the above table to create new projects with CIDRs. The 10.200.0.0/16 is
a tenant subnet.

### Google Private Access

Access to Google-managed services, (e.g. AppEngine, CloudSQL, CloudFunctions,)
will be routed through internal network space using [Google Private
Access](https://cloud.google.com/vpc/docs/private-google-access). Access from
Google-managed services to the VPC will be routed through internal network space
using [Serverless VPC
Access](https://cloud.google.com/vpc/docs/serverless-vpc-access). Google Private
Access is enabled for subnets.

### Interservice Communications

Direct network connections between microservices will be routed within the VPC
using [Internal
Load-Balancing](https://cloud.google.com/load-balancing/docs/l7-internal) or
[Google Private Access](https://cloud.google.com/vpc/docs/private-google-access)
for managed services. Interservice message quoting will utilize [Cloud
Pub/Sub](https://cloud.google.com/pubsub) for asynchronous delivery.

### VPC Firewall Rules

By default, no ingress traffic is allowed. By default, all egress traffic is
allowed. Ingress/egress firewall policies can be defined
in 2-networking-a-peering.The Google Cloud VPC (Virtual Private Cloud) firewall
rules are used to control traffic in a VPC network. The Firewall rules in Google
Cloud are defined at the network level (VPC network) and are stateful. Firewall
rules are applied in priority order. The first rule that matches the traffic
criteria (source IP, destination IP, protocol, port, etc.) is applied, and
subsequent rules are not evaluated. Rules can specify which protocols (TCP, UDP,
ICMP, etc.) and ports (such as 80 for HTTP or 443 for HTTPS) are allowed.

### Hub and Spoke architecture

Within Google Cloud, VPC Network Peering is used to connect VPCs within or
between projects in order to execute the Hub and Spoke architecture. A
networking design pattern known as "Hub and Spoke" includes setting up Virtual
Private Clouds (VPCs) in a centralized hub and outward spoke architecture. A
centralized networking hub housing shared resources and services is provided by
the hub VPC. Shared services that are accessed by several spoke VPCs, such
logging, security, or monitoring tools, may also be hosted by the hub VPC.

The Spoke VPCs are separate VPC networks that are connected to the hub VPC. Each
spoke VPC represents a distinct environment, such as development, testing, or
production environments. Spoke VPCs contain the application-specific resources
and workloads. They are isolated from each other and communicate with each other
through the hub VPCHub and Spoke Architecture with Compliance Overlays

Stellar Engine implements a robust Hub and Spoke network architecture,
specifically tailored to meet rigorous compliance requirements (FedRAMP High and
IL5). In this model, centralized Hub VPCs host shared networking resources,
connectivity gateways (Cloud VPN, Interconnect), and security appliances, while
Spoke VPCs host isolated workload environments (e.g., Development, Production).

Connectivity between the Hub and Spokes is established using VPC Network
Peering, ensuring low-latency, high-bandwidth communication. Shared VPC is
utilized throughout to centralize network administration within the Hub project
while allowing workload owners to consume network resources in their respective
Spoke projects.

Both supported patterns implement a Virtual Datacenter Security Stack (VDSS)
topology with distinct security appliance strategies:

- Landing VPC (Trust): The internal hub that connects to Spoke VPCs and
  on-premises networks.
- DMZ VPC (Untrust): The external-facing hub that handles Internet
  ingress/egress.

Supported Implementations:

#### FedRAMP High Pattern (2-networking-a-fedramp-high):

- Topology: VDSS (Landing + DMZ).
- Perimeter Security: Uses Network Virtual Appliances (NVAs).
- Implementation: Deploys a generic NVA cluster (based on simple-nva) to
  handle routing and basic traffic filtering between Trust and Untrust zones.

#### IL5 Pattern (2-networking-b-il5-ngfw):

- Topology: VDSS (Landing + DMZ).
- Perimeter Security: Uses Next-Generation Firewalls (NGFWs).
- Implementation: Deploys a scalable cluster of Palo Alto Networks VM-Series
  firewalls to provide advanced Layer 7 inspection, intrusion prevention
  (IPS), and granular application-aware filtering required for IL5 compliance.

# 4.0 Assured Workloads

Assured workloads in GCP are a set of features that help you ensure the
performance, availability, and security of your applications. Assured Workloads,
using FedRAMP Moderate by default, is enabled on the Assured Workloads folder.
All sub folders below the Assured Workloads folder will inherit policies and
constraints according to the compliance program selected.

To support compliance with data residency requirements, Google Cloud provides
you the ability to restrict the regions where data at rest can be stored.

During the Assured Workloads setup, you create an environment and select your
compliance regime. When you create resources in the environment, Assured
Workloads restricts the regions you can select for those resources based on the
compliance program chosen, using Organization Policies.

Projects in Stellar Engine are described via the terraform.tfvars file in
the 1-resman stage. In order to create a new tenant folder with Assured
Workloads configured. An example configuration for a tenant folder with an IL5
Assured Workloads is as follows:

```hcl
tenants = {
  dino-runner = {
    admin_principal  = "group:gcp-devops@dino-runner.cloud"
    descriptive_name = "dino-runner"
    compliance = {
      regime   = "IL5"
      location = "us"
    }
    locations = {
      gcs = "us-east4"
      kms = "us-east4"
    }
  }
}
```

**Note: If the compliance field is not set, the tenant folder will be generated
without an Assured Workloads configuration**. For a complete list of available
compliance regimes, please refer to the [Terraform
documentation](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/assured_workloads_workload#compliance_regime)

# 5.0 Information Security

The Stellar Engine information security strategy relies primarily on controlled
access to resources and securing data.

##

## 5.1 Access Control

### Account Types

**Users - ** Users are created and managed through Google Identity Platform or
Google Workspace. See the Identity Providers section below for more information.

**Service Accounts -** A service account is a special kind of account typically
used by an application or compute workload rather than a human. Its email
address, which is unique to the account, identifies a service account.

In Google Cloud, there are several different types of service accounts:

- **User-managed service accounts:** Service accounts that you create and
  manage. These service accounts are often used as identities for workloads.
- **Default service accounts:** User-managed service accounts that are created
  automatically when you enable certain Google Cloud services. You are
  responsible for managing these service accounts.
- **Google-managed service accounts:** Google-created and Google-managed
  service accounts that enable services to access resources on your behalf.

Impersonation is typically used to temporarily grant a user elevated access,
because it allows users to assume the roles and permissions that the service
account is assigned. A principal can use service account impersonation to run
commands as a service account. However, a principal can't use service account
impersonation to access the Google Cloud console. Within Stellar Engine,
impersonation is set via Terraform and used to create projects and resources.

### Identity Providers

Identity can be provided through [Google Identity
Platform](https://cloud.google.com/identity-platform) or [Cloud
Identity](https://cloud.google.com/identity).

Google Identity Platform is a customer identity and access management (CIAM)
platform. It helps organizations add identity and access management
functionality to their applications, protect user accounts, and scale with
confidence on Google Cloud.

Cloud Identity is an Identity as a Service (IDaaS) solution that allows you to
centrally manage users and groups who can access Google Cloud and Google
Workspace resources. It is the same identity service that powers Google
Workspace and can also be used as IdP for third-party applications (supports
SAML and LDAP applications).

### Multi-Factor Authentication (MFA)

MFA enforcement is a best practice when administering users. Google.com accounts
always require hardware-based multi-factor authentication. Google believes
enabling MFA is the best way to protect accounts from phishing and recommends
partners and customers always enable it.

**Note:** By default, Stellar Engine does not enforce MFA for logistical
reasons; however, in order to be fully compliant with IL5, the user _must_
enforce MFA in their environment.

### RBAC

Role-based Access Control is defined in the IAM Section of this document.

## 5.2 Data Security

### GCP Platform security

Google provides [many protections](https://cloud.google.com/security/) to GCP
customers, however security of workloads running in GCP is a shared
responsibility. All of the decisions reflected in this section are recommended
to the Customer to implement.

Customers are responsible for the following aspects of their applications'
security. It should be noted that the following list is not intended to be
exhaustive and care should be exercised on a case by case basis when deploying
and configuring resources in GCP.

### Data

Google encrypts all data communication channels that it uses to transmit data
between services. Customers are responsible for ensuring that the transmission
of data is facilitated over an encrypted channel.

Google encrypts all data on storage devices to prevent anyone with physical
access to physical devices from being able to inspect the data contained on
those devices. Customers can provide their own encryption keys for the
encryption of Google Compute Engine Persistent Disks and Google Cloud Storage
buckets.

Data stored within databases are all encrypted at the storage level, however
additional encryption is advisable at the application level to prevent customer
users from accessing content and limiting spillage in the event of intrusion.

A customer may load data which may include PII and PCI into BigQuery for
analysis. Customers are responsible for being aware of and abiding by any
regulations regarding the use and storage of this data and are responsible for
developing their own aggregation capabilities.

### Cloud KMS

If a customer needs to encrypt data at the application level or manage their own
encryption keys for compliance or regulatory reasons, they should consider at
[Cloud Key Management Service (KMS)](https://cloud.google.com/kms/). Cloud KMS
is a global cloud-hosted key management service that lets you manage encryption
for your cloud services the same way you do on-premises.

#### Best Practices

- Key rotation - Regular rotation of the encryption key is encouraged. This
  limits the amount of data protected by a single key. Automatic rotation can
  be configured on a user defined schedule by using _gcloud_ or the GCP
  Console.
- Separation of duties - Cloud KMS should be run in its own project without an
  owner at the project-level and instead being managed by an Org Admin. The
  Org Admin is not able to manage or use keys, but they are able to set IAM
  policies to restrict who has permissions for key management and usage.
  Additionally, the ability to manage Cloud

KMS should have role separation from the ability to perform encryption and
decryption operations. Any user with management access should not be able to
decrypt data.

- Additional authenticated data (AAD) - We recommend AAD as an additional
  integrity check as it can help protect your data from a [confused deputy
  attack](https://en.wikipedia.org/wiki/Confused_deputy_problem). Additional
  authenticated data is a string that you pass to Cloud KMS as part of an
  encrypt or decrypt API call. Cloud KMS cannot decrypt ciphertext unless the
  same AAD value is used for both encryption and decryption. By default an
  empty string is used for the AAD value.

### Google Cloud Storage

Cloud Storage requests refer to buckets and objects by their names. As a result,
even though ACLs will prevent unauthorized third parties from operating on
buckets or objects, a third party can attempt requests with bucket or object
names and determine their existence by observing the error responses. From the
bucket name it might be possible to infer information present within the bucket
itself, which might lead to leaks. If you are concerned about the privacy of
your bucket or object names, you should take appropriate precautions, such as:

- Choosing bucket and object names that are difficult to guess. For example, a
  bucket named stellar-engine-mybucket-gxl3 is random enough that unauthorized
  third parties cannot feasibly guess it or enumerate other bucket names from
  it.
- Before adding objects to a bucket, check that the [default object
  ACLs](https://cloud.google.com/storage/docs/access-control#default) are set
  to your requirements first. This could save you a lot of time updating ACLs
  for individual objects.
- Bucket and object ACLs are independent of each other, which means that the
  ACLs on a bucket do not affect the ACLs on objects inside that bucket. It is
  possible for a user without permissions for a bucket to have permissions for
  an object inside the bucket. For example, you can create a bucket such that
  only GroupA is granted permission to list the objects in the bucket, but
  then upload an object into that bucket that allows GroupB READ access to the
  object. GroupB will be able to read the object, but will not be able to view
  the contents of the bucket or perform bucket-related tasks.
- A simple yet effective approach is to keep private and public data separate
  in different buckets and to label public buckets clearly, such as
  stellar-engine-mybucket-public-3vxa.
- The Cloud Storage access control system includes the ability to specify that
  objects are publicly readable. Make sure you intend for any objects you
  write with this permission to be public. Once "published", data on the
  Internet can be copied to many places, so it's effectively impossible to
  regain read control over an object written with this permission.
- The Cloud Storage access control system includes the ability to specify that
  buckets are publicly writable. While configuring a bucket this way can be
  convenient for various purposes, we recommend against using this permission
  - it can be abused for distributing illegal content, viruses, and other
    malware, and the bucket owner is legally and financially responsible for the
    content stored in their buckets.
- If you need to make content available securely to users who don't have
  Google accounts, we recommend you use [signed
  URLs](https://cloud.google.com/storage/docs/access-control/signed-urls). For
  example, with signed URLs you can provide a link to an object and your
  application's customers do not need to authenticate with Cloud Storage to
  access the object. When you create a signed URL you control the type (read,
  write, delete) and duration of access.

### Data Residency

Google Cloud offers you the ability to control where your data is stored. When a
Customer chooses to configure resources in any location, Google may store that
Data at rest only in the selected Region. For that purpose we recommend using
[Organization Policy
constraints](https://docs.google.com/document/d/1AZijm5PTlfWeXUy1Jm6zjsC6ecyihberM5SVhbB_LgY/edit?resourcekey=0-4Mu_okWoVrjK9Du9hiZcgw#heading=h.de1wyjzdkh1h)
which can be applied at the organization, folder, or project level. Customers
can limit the physical location of a new resource with the Organization Policy
Service [resource locations
constraint](https://cloud.google.com/resource-manager/docs/organization-policy/defining-locations).
When coupled with Cloud IAM configuration to enable or disable services for sets
of users, you can prevent your employees from accidentally storing data in the
wrong Google Cloud region.

After you define resource locations, this limitation will apply only to
newly-created resources. Resources you created before setting the resource
locations constraint will continue to exist and perform their function.

### Encryption-at-Rest

All data stored in Google Cloud is encrypted at the storage level using AES256
using
[Google-managed](https://cloud.google.com/storage/docs/encryption/default-keys)
data encryption keys
([DEK](https://cloud.google.com/security/encryption/default-encryption#key_management)).
Google uses a common cryptographic library which incorporates a FIPS 140-2
validated module,
[BoringCrypto](https://csrc.nist.gov/projects/cryptographic-module-validation-program/Certificate/3318).

### Encryption-in-Transit

Microservices will primarily use [Cloud
Pub/Sub](https://cloud.google.com/pubsub/docs/encryption) and REST transmission
methods within the project system. Both of these protocols leverage HTTPS.

### TLS Version

All web services utilizing Transport Layer Security are required to support
version 1.2 or higher.

The following two ciphers are disabled when using TLS.

- TLS_ECDHE_RSA_WITH_AES_128_CBC_SHA (0xc013)
- TLS_ECDHE_RSA_WITH_AES_256_CBC_SHA (0xc014)

Organization policy gcp.restrictTLSVersion can be used to restrict the TLS
versions.

## 5.3 Logging & Auditing

### Audit Logs

The following are all [audit logs](https://cloud.google.com/logging/docs/audit)
that are collected and stored within Google Cloud:

**Activity Logs** - Admin Activity audit logs contain log entries for API calls
or other actions that modify the configuration or metadata of resources. For
example, these logs record when users create VM instances or change Identity and
Access Management permissions.

**Data Access Logs** -Data Access audit logs contain API calls that read the
configuration or metadata of resources, as well as user-driven API calls that
create, modify, or read user-provided resource data.

**System Event Logs** - System Event audit logs contain log entries for Google
Cloud actions that modify the configuration of resources. System Event audit
logs are generated by Google systems; they aren't driven by direct user action.

### Other Logging

**VPC Flow Logs** - VPC Flow Logs record a sample of network flows sent from and
received by VM instances, including instances used as GKE nodes. These logs can
be used for network monitoring, forensics, real-time security analysis, and
expense optimization.

**Firewall Rule Logs** - Firewall Rules Logging lets you audit, verify, and
analyze the effects of your firewall rules. For example, you can determine if a
firewall rule designed to deny traffic is functioning as intended. Firewall
Rules Logging is also useful if you need to determine how many connections are
affected by a given firewall rule.

**Access Transparency Logs** - Access Transparency logs include data about
Google staff activity, including:

- Actions by the Support team that you may have requested by phone
- Basic engineering investigations into your support requests
- Other investigations made for valid business purposes, such as recovering
  from an outage

### Log Destinations

Audit logs and other logs do not expire and are sent to the following
destinations:

- BigQuery
- Storage
- Pub/Sub

When the log destination is in a different project, we need to make sure the log
writer identity service account of the log sink has the permission to write to
the destination. If there is a VPC SC or other additional restrictions, we need
to grant access to the log writer identity as well.

## 5.4 Monitoring

### Projects

To access Cloud Monitoring for each environment a host project has been created
to hold the dashboards and alerts. The folders and monitoring host projects are
listed in the table below.

| Folder   | Monitoring Project       |
| :------- | :----------------------- |
| Security | `<prefix>`-dev-sec-core-0  |
| Security | `<prefix>`-prod-sec-core-0 |

### Groups

A group named gcp-monitoring-admins is created during the bootstrap process (See
3.2 IAM).

### Alerts

Alerts can be created based on events and log metrics. Alerting gives timely
awareness to problems in your cloud applications so you can resolve the problems
quickly. Within Cloud Monitoring, an alerting policy describes the circumstances
under which you want to be alerted and how you want to be notified.

### Dashboards

Cloud Monitoring automatically installs a dashboard when you create a resource
in a Google Cloud project. These dashboards display metrics and general
information about a single Google Cloud service. Custom dashboards are
dashboards that you create or install. Unlike dashboards for Google Cloud
services and those for your supported integrations, custom dashboards let you
view and analyze data from different sources in the same context. For example,
you can create a dashboard that displays metric data, alerting policies, and log
entries.

###

## 5.5 Security Boundaries

In the above diagram, the dotted red line represents the intended Authorization
Boundary of a Stellar Engine deployment.

### Cloud Organization Policy

The customer’s GCP Cloud Organization may inherit its organizational policy
restrictions. If a resource node has set inheritFromParent = true, then the
effective Policy of the parent resource is inherited, merged, and reconciled to
evaluate the resulting effective policy. If a resource hierarchy node has a
policy that includes inheritFromParent = false, it doesn't inherit the
organization policy from its parent. Instead, the node inherits the constraint's
default behavior unless you set a policy with allowed or denied values.

### Project Layout

All cross-project permission grants are controlled by Cloud IAM and defined in
Terraform.

Details about the project layout are documented in the Cloud Project
Organization section of this document. As a part of the hub and spoke network
architecture, a default VPC service control perimeter is created around the
project which hosts the restricted shared VPC.

VPC Service Controls

VPC Service Controls secure and improve the ability to mitigate the risk of data
exfiltration from GCP services by defining controls. These controls include the
creation of perimeters that protect resources and the data of services that are
explicitly specified. We can enforce adaptive access control based on IP range
or device trust (BeyondCorp) for GCP resource access from outside privileged
networks.

A VPC Service Control makes sure that data in most GCP services cannot exit the
perimeter to an un-recognized network IP, even if they have the appropriate IAM
credentials such as a user account or service account.

## 5.6 Network Security

### Network Control

The customer project may be managed by the SharedVPC network. Each service
project may have one or more subnets provisioned for its use by the customer.
Service accounts can be granted
[compute.networkUser](https://cloud.google.com/iam/docs/job-functions/networking)
permissions within the specific subnet for each project to allow IP addresses to
be created.

### Firewall Rules

Firewall rules are set at the SharedVPC level and may be administered by the
customer or personnel. By default, no ingress traffic is allowed. By default,
all egress traffic is allowed. Ingress/egress policies can be defined at the
environment (development, non-production and production) level.

### DNS

For DNS, Stellar Engine uses Google Cloud DNS, a recently provisionally approved
first party service.

## 5.7 Customer Security Practices

The structure of the cloud projects, and method by which the application is
developed and maintained, minimizes risk and allows for disparate teams to work
using independent release schedules. Security is enforced through a separation
of projects and IAM controls.

### Security Command Center

**Note: SCC is currently in the roadmap for IL5 but is not approved at this
time.**

Status: Manual Deployment Required

Deployment Guide: [Stellar Engine - SCC Deployment Guide](./scc-deployment-guide.md)

[Security Command Center
(SCC](https://cloud.google.com/security-command-center/)) is a security and data
risk database for GCP. It unifies assets, resources, policies, IAM,
recommendations, and security/risk specific annotations in one place. These
include:

- Asset discovery and inventory with Cloud Inventory API
- Sensitive data scanning for PII: GCS Buckets (note the
  [regions](https://cloud.google.com/dlp/docs/locations) of Cloud DLP
  deployment and possible regulatory declarations for offshore data analysis
  needed)
- Web app vulnerability scanning - XSS, insecure libraries
- Notifications: Pub/Sub events on new/deleted/modified assets discovered

Customers can optionally use Security Command Center with a Premium level
license for all organizations which will leverage built-in security sources
including:

- [Event Threat
  Detection](https://cloud.google.com/event-threat-detection/docs/)
- [Cloud Anomaly
  Detection](https://cloud.google.com/security-command-center/docs/how-to-view-vulnerabilities-threats#anomaly_detection)
- [Security Health
  Analytics](https://cloud.google.com/security-command-center/docs/how-to-manage-security-health-analytics)
  - CIS Security Software
    [Certified](https://www.cisecurity.org/partner/google-inc/) for the
    following Benchmarks: CIS Benchmark for Google Cloud Platform Foundation
    Benchmark, v1.0.0, Level 1 & 2.

Additional compliance mappings are included for reference in [Security Health
Analytics
findings](https://cloud.google.com/security-command-center/docs/concepts-security-health-analytics-findings)
but are neither provided or reviewed by the OWASP Foundation. Customers should
review the guiding documentation of OWASP Top Ten, National Institute of
Standards and Technology 800-53 (NIST 800-53), and International Organization
for Standardization 27001 (ISO 27001) for how to check violations manually.

Google also recommends using the list as a reference for Google Cloud security
controls.

| <strong>Google Recommendation</strong>:<br/><ol><li>Continuous Review: Regularly review risk reports and insights presented in the SCC dashboard.</li><li>Automation: Automate risk scanning using <a href='https://cloud.google.com/asset-inventory/docs/reference/rest'>Cloud Asset API</a> and implement custom detection logic (e.g., via Cloud Functions). Integrate outcomes of custom security analysis using results back into SCC through <a href='https://cloud.google.com/security-command-center/docs/how-to-api-create-manage-findings#creating_a_finding'>Findings API</a>.</li><li>SIEM Integration: Configure Pub/Sub exports for finding notifications to integrate with external SIEM systems.</li></ol> |
| :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

### Firewall Rules

| <strong>Requirements:</strong><br/><ul><li>Default deny for ingress</li><li>Firewall rules to be managed using IAC</li><li>Need to be able to target specific resources, e.g. node pool within GKE cluster</li></ul> |
| :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| <strong>Design Constraints:</strong><br/><ul><li>None</li></ul>                                                                                                                                                      |
| <strong>Assumptions:</strong><br/><ul><li>None</li></ul>                                                                                                                                                             |

Each VPC network implements a distributed virtual firewall. Configure firewall
rules that allow or deny traffic to and from the resources attached to the VPC,
including Compute Engine VM instances and GKE clusters.

Firewall rules are applied at the VPC level, so they help provide effective
protection and traffic control regardless of the operating system your instances
use. The firewall is stateful, which means that for flows that are permitted,
return traffic is automatically allowed.

Firewall rules are specific to a particular VPC network. The rules allow you to
specify the type of traffic, such as ports and protocols, and the source or
destination of the traffic, including IP addresses, subnets, tags, and service
accounts. For example, you can create an ingress rule to allow any VM instance
associated with a particular service account to accept TCP traffic on port 80
that originated from a specific source IP address or CIDR range. Once created
firewall rules cannot be renamed so consider your naming convention to support
operational needs.

**Figure:** Firewall rules assignment options

Each VPC automatically includes default and implied firewall rules:

- **Implied egress rule:** An egress rule whose action is ALLOW, destination
  is 0.0.0.0/0, and priority is the lowest possible (65535) lets any instance
  send traffic to any destination, except for traffic
  [blocked](https://cloud.google.com/vpc/docs/firewalls#blockedtraffic) by
  GCP. Outbound access may be restricted by creating a higher priority
  firewall rule.
- **Implied deny ingress rule:** An ingress rule whose action is DENY, source
  is 0.0.0.0/0, and priority is the lowest possible (65535) protects all
  instances by blocking incoming traffic to them. Incoming access may be
  allowed by a higher priority rule.

The implied rules cannot be removed, but they have the lowest possible
priorities. Rules you create can override them as long as your rules have higher
priorities (less than 65535).

Firewall Rules Logging allows you to audit, verify, and analyze the effects of
your firewall rules. For example, you can determine if a firewall rule designed
to deny traffic is functioning as intended. Firewall Rules Logging is also
useful if you need to determine how many connections are affected by a given
firewall rule.

You enable Firewall Rules Logging individually for each firewall rule whose
connections you need to log. FirewaThe implied rules cannot be removed, but they
have the lowest possible priorities. Rules you create can override them as long
as your rules have higher priorities (less than 65535).

Firewall Rules Logging allows you to audit, verify, and analyze the effects of
your firewall rules. For example, you can determine if a firewall rule designed
to deny traffic is functioning as intended. Firewall Rules Logging is also
useful if you need to determine how many connections are affected by a given
firewall rule.

You enable Firewall Rules Logging individually for each firewall rule whose
connections you need to log. Firewall Rules Logging is an option for any
firewall rule, regardless of the action (allow or deny) or direction (ingress or
egress) of the rule. Firewall Rules Logging is useful if you need to determine
the effectiveness of a firewall rule and how many connections are affected by a
given firewall rule. For information about viewing logs, see [Using Firewall
Rules Logging](https://cloud.google.com/vpc/docs/using-firewall-rules-logging).

When you enable logging for a firewall rule, Google Cloud creates an entry
called a connection record each time the rule allows or denies traffic. Each
connection record contains the source and destination IP addresses, the protocol
and ports, date and time, and a reference to the firewall rule that applied to
the traffic. You can view these records in Cloud Logging, and you can export
logs to any destination that Cloud Logging export supports.

In addition to firewall rules per VPC there is also the ability to create
Hierarchical firewall policies which let you create and enforce a consistent
firewall policy across the organization. You can assign hierarchical firewall
policies to the organization as a whole or to individual folders.

Hierarchical firewall policies are containers for firewall rules that can
explicitly deny or allow connections. In addition, hierarchical firewall policy
rules can delegate evaluation to lower-level policies or VPC network firewall
rules if desired. Lower-level rules cannot override a rule from a higher place
in the resource hierarchy. This lets organization-wide admins manage critical
firewall rules in one place.

All rules associated with the organization node are evaluated, followed by those
of the first level of folders, and so on. However with Shared VPC the evaluation
follows the resource path of the Shared VPC host project, not the service
project. Hierarchical firewall policy rules can be targeted to specific VPC
networks and VMs by using target resources. This lets you create exceptions for
groups of VMs.ll Rules Logging is an option for any firewall rule, regardless of
the action (allow or deny) or direction (ingress or egress[^1]) of the rule.
Firewall Rules Logging is useful if you need to determine the effectiveness of a
firewall rule and how many connections are affected by a given firewall rule.
For information about viewing logs, see [Using Firewall Rules
Logging](https://cloud.google.com/vpc/docs/using-firewall-rules-logging).

When you enable logging for a firewall rule, Google Cloud creates an entry
called a connection record each time the rule allows or denies traffic. Each
connection record contains the source and destination IP addresses, the protocol
and ports, date and time, and a reference to the firewall rule that applied to
the traffic. You can view these records in Cloud Logging, and you can export
logs to any destination that Cloud Logging export supports.

In addition to firewall rules per VPC there is also the ability to create
Hierarchical firewall policies which let you create and enforce a consistent
firewall policy across the organization. You can assign hierarchical firewall
policies to the organization as a whole or to individual folders.

Hierarchical firewall policies are containers for firewall rules that can
explicitly deny or allow connections. In addition, hierarchical firewall policy
rules can delegate evaluation to lower-level policies or VPC network firewall
rules if desired. Lower-level rules cannot override a rule from a higher place
in the resource hierarchy. This lets organization-wide admins manage critical
firewall rules in one place.

All rules associated with the organization node are evaluated, followed by those
of the first level of folders, and so on. However with Shared VPC the evaluation
follows the resource path of the Shared VPC host project, not the service
project. Hierarchical firewall policy rules can be targeted to specific VPC
networks and VMs by using target resources. This lets you create exceptions for
groups of VMs.

| <strong>Google Recommendation:</strong><br/><ol><li>Create firewall rules leveraging service accounts as the source or target wherever possible, as this allows for more autonomy for applications teams to scale their resources without requiring additional firewall changes. In addition service accounts are specific to projects and can only be changed on VMs by stopping and starting. </li><li>Limit the use of firewall rules using tags as they can be invoked by simply adding a network tag to a VM and are not specific to any project. </li><li>Where more general firewall rules are required, using a specific subnet or a summarized IP CIDR range is recommended to reduce the complexity of the rules.</li><li>To improve security posture it is recommended to create an egress-deny rule with a higher priority than the implied rules to ensure that both ingress and egress traffic is managed. </li><li>Define a standard naming convention for firewall rules and make use of description metadata to allow those reviewing rules to better understand the intent or history of the rule. </li><li>Firewall rules created by GCP service accounts for the purpose of running services inside customers VPCs, e.g. Google Kubernetes Engine, should only be changed in accordance with the documentation for the service. Any changes outside of this may result in service failure and/or invalidation of SLAs.</li><li>Enable Firewall Rules Logging to allow the audit, verification, and analysis the effects of your firewall rules. </li><li>Leverage the Network Intelligence <a href='https://cloud.google.com/network-intelligence-center/docs/firewall-insights/concepts/overview'>Firewall Insights service</a> which provides visibility into firewall usage and detects firewall configuration issues. Related insights and metrics are also integrated into the Google Cloud Console for the Virtual Private Cloud (VPC) firewall.</li><li>Manage custom firewall rules and configuration centrally, using Infrastructure as Code and <a href='https://www.terraform.io/docs/providers/google/r/compute_firewall.html'>Terraform</a>. This provides development teams the ability to manage their rulesets which are approved as part of a CI/CD process by appropriate parties. In addition there is built in auditability and traceability in the process.</li><li>Investigate <a href='https://cloud.google.com/vpc/docs/firewall-policies'>Hierarchical firewall policies</a> to centralize general firewall rules across the organization and/or environments. At the time of writing this feature is in preview.</li></ol> |
| :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

### Data Management

#### Data Loss Prevention (DLP)

To validate and understand where applications in Kubernetes might be logging
PII, Google recommends the customer utilize DLP to regularly scan logs and
create a report that details the presence of potentially sensitive data.

## 5.8 Vulnerability Management

Vulnerability management is currently a work in progress, as availability is
limited in the IL5 enclave. The below section details our end-state goal for
vulnerability management.

### Security Command Center

Security Command Center’s Premium offering has [Rapid Vulnerability
Detection](https://cloud.google.com/security-command-center/docs/concepts-rapid-vulnerability-detection-overview#overview),
a built-in service that finds critical vulnerabilities in several different scan
targets.

### Supported Scan Targets

- Compute Engine
- Cloud Load Balancing (External)
- Google Kubernetes Engine ingress
- Cloud Run
- App Engine

### Scans

Rapid Vulnerability Detection runs managed scans that
[detect](https://cloud.google.com/security-command-center/docs/concepts-rapid-vulnerability-detection-overview#scan_findings_and_remediations):

- Weak credentials
- Exposed interface findings
- Incomplete software installations
- Vulnerable software findings
- Exposed administrator user interfaces

When enabled, Security Command Center automatically configures and manages the
service scans without a need to provide target URLs or manually start scans.
Rapid Vulnerability Detection uses [Cloud Asset
Inventory](https://cloud.google.com/asset-inventory/docs/overview#features) to
retrieve information about new VMs and applications in projects and runs scans
once a week to find public endpoints and detect vulnerabilities.

### Enablement

[Rapid Vulnerability
Detection](https://cloud.google.com/security-command-center/docs/how-to-use-rapid-vulnerability-detection#enabling)
can be enabled via Google Cloud Console on the Services page.

The scans start automatically within 24 hours after first enabling Rapid
Vulnerability Detection. After the first scan, Rapid Vulnerability Detection
runs managed scans weekly.

#### Test

For testing, open source [Testbed for Tsunami
Security](https://github.com/google/tsunami-security-scanner-testbed/tree/master/truepositives/secure)
can be used. This is available on GitHub to generate findings for
vulnerabilities.

#### Review

Findings contain detected vulnerabilities and information about affected
projects. Vulnerabilities are reported for projects, not specific scan targets
(endpoints and application software) or VMs contained within projects.

Findings can be viewed in the Security Command Center dashboard or by using
[Security Command Center
API.](https://cloud.google.com/security-command-center/docs/how-to-api-list-findings#list_all_findings)

#### Display

Rapid Vulnerability Detection generates [vulnerability
findings](https://cloud.google.com/security-command-center/docs/concepts-vulnerabilities-findings)
that are available in the Security Command Center. When they are enabled in the
Security Command Center, integrated services, like VM Manager, also generate
vulnerability findings.

Displaying all findings for a port or IP address can be done via Google Cloud
Console under
[Findings](https://cloud.google.com/security-command-center/docs/how-to-use-rapid-vulnerability-detection#display-findings-for-port-or-ip)
and via [Security Command Center
API](https://cloud.google.com/security-command-center/docs/how-to-api-list-findings#list_all_findings).
