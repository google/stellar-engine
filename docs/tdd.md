# Stellar Engine technical design document

| Field | Value |
| :--- | :--- |
| Date updated | December 5, 2025 |
| Version | v3.0 |
| Recent changes | Updates to reflect new architecture and administrative corrections |

This document serves as an illustrative technical working reference to guide project delivery. Its activities and design goals provide architectural detail and do not supersede any legal terms or conditions defined in the customer's written contract with Google.

<!-- BEGIN TOC -->
- [1. Purpose](#1-purpose)
- [2. Executive summary](#2-executive-summary)
  - [2.1 Overview](#21-overview)
  - [2.2 Project architecture](#22-project-architecture)
- [3. Cloud foundation](#3-cloud-foundation)
  - [3.1 Project organization](#31-project-organization)
    - [Network security and isolation](#network-security-and-isolation)
    - [Data security and encryption](#data-security-and-encryption)
    - [IAM and service accounts](#iam-and-service-accounts)
    - [Serverless security](#serverless-security)
    - [Resource management](#resource-management)
    - [Folder hierarchy](#folder-hierarchy)
    - [Example organization layout](#example-organization-layout)
  - [3.2 IAM](#32-iam)
    - [IAM principles](#iam-principles)
    - [Role groups](#role-groups)
      - [Initial role groups](#initial-role-groups)
      - [Role group mappings](#role-group-mappings)
      - [Application-specific groups](#application-specific-groups)
    - [Service accounts](#service-accounts)
      - [Bootstrap service account](#bootstrap-service-account)
    - [IAM roles](#iam-roles)
      - [Organization node](#organization-node)
      - [Data platform development folder](#data-platform-development-folder)
      - [Data platform production folder](#data-platform-production-folder)
      - [GKE development folder](#gke-development-folder)
      - [GKE production folder](#gke-production-folder)
      - [Networking folder](#networking-folder)
      - [Networking development folder](#networking-development-folder)
      - [Networking production folder](#networking-production-folder)
      - [Core automation project](#core-automation-project)
  - [3.3 Code control](#33-code-control)
    - [GitHub repositories](#github-repositories)
    - [Branching strategy](#branching-strategy)
    - [Pull request validation](#pull-request-validation)
  - [3.4 Infrastructure as Code](#34-infrastructure-as-code)
    - [Repository layout](#repository-layout)
  - [3.5 Terraform design principles](#35-terraform-design-principles)
    - [Environment partitioning](#environment-partitioning)
  - [3.6 Networking](#36-networking)
    - [Shared VPC topology](#shared-vpc-topology)
    - [Virtual Private Clouds](#virtual-private-clouds)
    - [Subnet allocations](#subnet-allocations)
    - [Private Google Access](#private-google-access)
    - [Inter-service communication](#inter-service-communication)
    - [VPC firewall rules](#vpc-firewall-rules)
    - [Hub-and-spoke topology](#hub-and-spoke-topology)
    - [Compliance regime overlays](#compliance-regime-overlays)
      - [FedRAMP High and Moderate pattern](#fedramp-high-and-moderate-pattern)
      - [IL5 pattern](#il5-pattern)
- [4. Assured Workloads](#4-assured-workloads)
- [5. Information security](#5-information-security)
  - [5.1 Access control](#51-access-control)
    - [Account types](#account-types)
    - [Identity providers](#identity-providers)
    - [Multi-factor authentication](#multi-factor-authentication)
    - [Role-based access control](#role-based-access-control)
  - [5.2 Data security](#52-data-security)
    - [Platform security](#platform-security)
    - [Data protection](#data-protection)
    - [Cloud KMS](#cloud-kms)
      - [Key management practices](#key-management-practices)
    - [Cloud Storage](#cloud-storage)
    - [Data residency](#data-residency)
    - [Encryption at rest](#encryption-at-rest)
    - [Encryption in transit](#encryption-in-transit)
    - [TLS version](#tls-version)
  - [5.3 Logging and auditing](#53-logging-and-auditing)
    - [Audit logs](#audit-logs)
    - [Network and access logs](#network-and-access-logs)
    - [Log destinations](#log-destinations)
  - [5.4 Monitoring](#54-monitoring)
    - [Host projects](#host-projects)
    - [Monitoring groups](#monitoring-groups)
    - [Alerting policies](#alerting-policies)
    - [Dashboards](#dashboards)
  - [5.5 Security boundaries](#55-security-boundaries)
    - [Organization policy inheritance](#organization-policy-inheritance)
    - [Project layout and VPC Service Controls](#project-layout-and-vpc-service-controls)
  - [5.6 Network security](#56-network-security)
    - [Shared VPC access control](#shared-vpc-access-control)
    - [Environment firewall rules](#environment-firewall-rules)
    - [Cloud DNS](#cloud-dns)
  - [5.7 Customer security practices](#57-customer-security-practices)
    - [Security Command Center](#security-command-center)
    - [VPC and hierarchical firewall governance](#vpc-and-hierarchical-firewall-governance)
    - [Data management](#data-management)
      - [Sensitive data inspection](#sensitive-data-inspection)
  - [5.8 Vulnerability management](#58-vulnerability-management)
    - [Rapid Vulnerability Detection](#rapid-vulnerability-detection)
    - [Supported scan targets](#supported-scan-targets)
    - [Managed scans](#managed-scans)
    - [Service enablement](#service-enablement)
      - [Testing](#testing)
      - [Reviewing findings](#reviewing-findings)
      - [Viewing findings](#viewing-findings)
<!-- END TOC -->

## 1. Purpose

Extending [Cloud Foundation Fabric](https://github.com/GoogleCloudPlatform/cloud-foundation-fabric), Stellar Engine provides compliant Google Cloud infrastructure and opinionated architecture patterns for supported [Assured Workloads](https://cloud.google.com/security/products/assured-workloads?hl=en) compliance regimes, paired with Google best practices and cybersecurity documentation to accelerate the federal Authorization to Operate process. Stellar Engine serves as an engineering accelerator for teams supporting Google Cloud customer and partner engagements:

- Automates the foundational Google Cloud landing zone phases of a Google Public Sector Professional Services engagement.
- Establishes a reusable baseline for Google Public Sector reference architectures and workload blueprints.
- Delivers an Impact Level 5 compliant Terraform Infrastructure as Code framework that customers can adopt and operate.
- Extends cleanly to additional federal compliance regimes across customer engagements.
- Simplifies Google Cloud and Terraform adoption for regulated public sector teams.

For post-deployment operational hardening procedures, see the [Security Best Practices Guide](security-best-practices.md).

## 2. Executive summary

The supplied directory structure and Terraform modules provide a starting foundation with pragmatic defaults that you can tailor to organizational requirements. Operators currently deploy the stages manually while evaluating IL5-compliant CI/CD automation options such as GitHub Actions, GitLab CI/CD, and Cloud Build.

Stage 0 creates a root folder at the top of the organization to hold foundational projects and policies. Under the root folder, you can provision tenant folders inside Assured Workloads boundaries configured for regimes such as FedRAMP Moderate, FedRAMP High, or IL5. Deployments typically validate workloads in non-production environments before promoting configurations to production.

### 2.1 Overview

Bootstrap scripts and staged Terraform configurations provision a baseline landing zone inside an Assured Workloads folder. Once the foundation is active, you can deploy individual Google Cloud and approved third-party workload blueprints based on tenant requirements, as detailed in section 3.4.

### 2.2 Project architecture

In the `example.com` reference architecture, foundational projects reside under the organization hierarchy to host shared automation, audit logging, and billing telemetry created by the deployment pipeline.

| Project | Description |
| :--- | :--- |
| `org-iac-core-0` | Hosts the Terraform state buckets and automation service accounts that build foundational organization components. Restrict access to this project tightly. |
| `org-audit-logs-0` | Hosts centralized log sinks, retention buckets, and detective security controls. |
| `org-billing-export-0` | Hosts an optional BigQuery dataset for organization [billing exports](https://cloud.google.com/billing/docs/how-to/export-data-bigquery). |

## 3. Cloud foundation

### 3.1 Project organization

Terraform enforces the following organization policies at the organization level using Google-managed constraints and custom constraints defined in YAML files under `data/org-policies/` and `data/custom-org-policies/`.

#### Network security and isolation

| Constraint | Enforcement |
| :--- | :--- |
| `compute.vmExternalIpAccess` | Denies all external IP addresses on Compute Engine VM instances. |
| `compute.skipDefaultNetworkCreation` | Skips creation of the `default` VPC network in newly created projects. |
| `compute.restrictProtocolForwardingCreationForTypes` | Restricts new forwarding rules to `INTERNAL` IP addresses. |
| `compute.restrictLoadBalancerCreationForTypes` | Restricts load balancer creation to `INTERNAL` types only. |
| `compute.disableGlobalLoadBalancing` | Disables global load balancing resources. |
| `compute.disableGlobalCloudArmorPolicy` | Disables global Cloud Armor security policies. |
| `compute.disableGlobalSelfManagedSslCertificate` | Disables global self-managed SSL certificates. |
| `compute.restrictCloudNATUsage` | Restricts Cloud NAT gateways to organization resources. |
| `compute.restrictDedicatedInterconnectUsage` | Restricts Dedicated Interconnect attachments to organization resources. |
| `compute.restrictPartnerInterconnectUsage` | Restricts Partner Interconnect attachments to organization resources. |
| `compute.restrictVpcPeering` | Restricts VPC Network Peering to organization resources and approved folders. |
| `compute.setNewProjectDefaultToZonalDNSOnly` | Configures newly created projects to use zonal internal DNS by default. |
| `sql.restrictAuthorizedNetworks` | Blocks unproxied authorized network ranges on Cloud SQL instances. |
| `sql.restrictPublicIp` | Blocks public IP addresses on Cloud SQL instances. |

#### Data security and encryption

| Constraint | Enforcement |
| :--- | :--- |
| `custom.kmsRotation` | Custom constraint enforcing the maximum rotation period on Cloud KMS keys. |
| `storage.uniformBucketLevelAccess` | Requires uniform bucket-level access across Cloud Storage buckets. |
| `storage.publicAccessPrevention` | Blocks public access on Cloud Storage buckets. |
| `storage.secureHttpTransport` | Requires HTTPS transport for Cloud Storage requests. |
| `appengine.disableCodeDownload` | Disables source code downloads from App Engine applications. |
| `bigquery.disableBQOmniAWS` | Disables BigQuery Omni cross-cloud connections to AWS. |
| `bigquery.disableBQOmniAzure` | Disables BigQuery Omni cross-cloud connections to Azure. |

#### IAM and service accounts

| Constraint | Enforcement |
| :--- | :--- |
| `iam.managed.disableServiceAccountKeyCreation` | Disables user-managed service account key creation. |
| `iam.managed.disableServiceAccountKeyUpload` | Disables uploading external public keys to service accounts. |
| `iam.managed.preventPrivilegedBasicRolesForDefaultServiceAccounts` | Blocks privileged basic roles on default service accounts. |
| `iam.automaticIamGrantsForDefaultServiceAccounts` | Prevents automatic Editor role grants on default service accounts. |
| `iam.serviceAccountKeyExposureResponse` | Sets `DISABLE_KEY` to disable exposed service account keys automatically. |
| `iam.allowedPolicyMemberDomains` | Restricts IAM policy principals to the customer ID and approved domains. |
| `essentialcontacts.managed.allowedContactDomains` | Restricts Essential Contacts notifications to approved domains. |
| `essentialcontacts.allowedContactDomains` | Restricts Essential Contacts addresses to the organization domain. |

#### Serverless security

| Constraint | Enforcement |
| :--- | :--- |
| `cloudfunctions.allowedIngressSettings` | Sets `ALLOW_INTERNAL_AND_GCLB` to restrict Cloud Functions ingress. |
| `cloudfunctions.allowedVpcConnectorEgressSettings` | Sets `ALL_TRAFFIC` to route all Cloud Functions egress through a VPC connector. |
| `run.allowedIngress` | Sets `internal-and-cloud-load-balancing` to restrict Cloud Run ingress. |
| `run.allowedVPCEgress` | Sets `all-traffic` to route all Cloud Run egress through VPC networking. |
| `cloudbuild.allowedIntegrations` | Restricts Cloud Build external repository integrations to `github.com`. |

#### Resource management

| Constraint | Enforcement |
| :--- | :--- |
| `resourcemanager.allowedImportSources` | Restricts project imports to the organization. |
| `resourcemanager.allowedExportDestinations` | Restricts project exports to the organization. |
| `resourcemanager.accessBoundaries` | Restricts Google Cloud console visibility boundaries to the organization. |

#### Folder hierarchy

Stage `1-resman` creates the folder hierarchy below, and you can customize folder display names in the `1-resman` configuration:

- Root-level folders represent the top-level organization or business unit boundary.
- First-level folders separate Common Services, Test, Integration, and Production environments.
- Second-level folders organize shared and tenant domains:
  - The Network folder sits under Common Services and hosts centralized networking projects.
  - The Security folder sits under Common Services and hosts centralized IaC Core, Audit Logs, and Billing Export projects.
  - Tenant folders sit under the Test, Integration, and Production environment folders.
- Third-level folders separate each tenant into a Tenant Core folder hosting the tenant IaC Core project and a Tenant Main folder hosting workload projects.

#### Example organization layout

The hierarchy below illustrates a nested multi-workstream organization layout:

- Organization Root Folder
  - Network-IL5
    - Production
      - `<prefix>-prod-net-landing-0`
      - `<prefix>-prod-net-spoke-0`
    - Development
      - `<prefix>-dev-net-landing-0`
      - `<prefix>-dev-net-spoke-0`
  - Security
    - `<prefix>-prod-security-core-0`
    - `<prefix>-dev-security-core-0`
  - Tenants
    - Workstream-A-IL5
      - Workstream Core
        - `<prefix>-workstream-a-iac-core-0`
      - Workstream Tenant
        - Project-A
        - Project-B
    - Workstream-B-IL4
      - Workstream Core
        - `<prefix>-workstream-b-iac-core-0`
      - Workstream Tenant
        - Project-C
        - Project-D

### 3.2 IAM

#### IAM principles

Cybersecurity least-privilege principles govern all IAM bindings in Stellar Engine:

- Manage IAM policies declaratively in Terraform and enforce them through Google Cloud IAM after peer code review:
  - Grant no human principal permissions to create or modify cloud resources outside tightly controlled development projects.
  - Assign the Cloud Resource Manager permissions required to execute Terraform exclusively to dedicated Stellar Engine automation service accounts used by CI/CD `terraform apply` pipelines.
  - Scope any broader development permissions strictly to development projects so elevated access never propagates to testing, staging, or production environments.
- Enforce group-based human access:
  - Bind IAM roles to Google Cloud groups rather than individual user principals.
  - Restrict bindings to a curated set of predefined least-privilege roles scoped to each operational function.
- Enforce isolated machine identities:
  - Provision a dedicated service account for each microservice workload.
  - Block downloadable service account keys through organization policy constraints.
  - Scope each workload service account strictly to its required runtime permissions.
  - Enforce `iam.automaticIamGrantsForDefaultServiceAccounts` through organization policy to strip default Editor grants from default service accounts.

Prefer Google Cloud predefined roles over custom IAM roles wherever possible to minimize custom permission maintenance overhead.

#### Role groups

Role groups align Google Cloud access with engineering, security, and platform operations teams:

- Development and administrative teams identify required job functions before bootstrap.
- Each role maps to a dedicated group following the `gcp-X-${tenant}-${role}@X.gov` naming convention, with the bootstrap Terraform service account retaining group ownership for automated provisioning.
- Bootstrap Terraform configurations seed initial group memberships, while ongoing membership lifecycle management runs through your enterprise identity provider or Terraform state.

##### Initial role groups

The initial role groups created during Google Cloud organization setup receive the following organization-level roles:

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

##### Role group mappings

Stellar Engine configures additional role groups and role bindings at the top-level organization or folder node and across project hierarchies:

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

##### Application-specific groups

Tenant workloads and specialized service platforms often define additional groups outside the core Stellar Engine stages. Accounting for those workload groups provides a complete view of role group governance across the organization.

For example, a secured data warehouse blueprint defines these workload groups:

- Data analyst group
- Data engineer group
- Network administrator group
- Security administrator group
- Security analyst group

You can map several of these functions to existing Stellar Engine groups while creating dedicated groups for specialized application roles.

#### Service accounts

Stellar Engine provisions dedicated, single-purpose service accounts across stages and workloads to enforce least privilege and prevent over-permissioned identities.

Apply these organization policy restrictions to harden service accounts, where items marked with `*` represent core baseline recommendations:

- Disable automatic role grants to default service accounts (`*`)
- Disable service account creation
- Disable service account key creation (`*`)
- Disable service account key upload (`*`)
- Disable cross-project service account attachment
- Restrict removal of project liens when service accounts operate across projects

##### Bootstrap service account

An administrator can execute Stage 0 bootstrap using an individual Google Cloud user account or by impersonating a bootstrap service account. Using a tightly controlled individual account assigned to the `gcp_org_admins` group is preferred, and you must disable that account when it is not actively executing bootstrap tasks.

To run the bootstrap phase through a service account at the organization root, grant these roles outside Terraform beforehand:

- Organization Admin on the Google Cloud organization when targeting the organization root node.
- Organization Policy Admin on the organization to manage organization policy constraints.
- Billing Account Administrator, or at minimum Billing Account User, to link newly created projects.
- Folder Creator to create foundational and environment folders.
- Access Context Manager Admin to configure VPC Service Controls policies.
- Assured Workloads Admin to provision Assured Workloads folders.

To run the bootstrap phase scoped to an existing Assured Workloads folder, grant these minimum roles:

- Organization Viewer to query organization-level metadata.
- Organization Policy Admin to manage folder-scoped organization policies.
- Billing Account User to link newly created projects to the billing account.
- Folder Creator to create nested folders and projects.
- Access Context Manager Admin to manage VPC Service Controls perimeters.
- Security Admin to configure Security Command Center and security telemetry.

#### IAM roles

Stellar Engine project and folder IAM bindings follow the Cloud Foundation Fabric design guidelines:

##### Organization node

| <strong>members</strong>                                               | <strong>roles</strong>                                                                                                                                                                                                                                            |
| :--------------------------------------------------------------------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| <strong>dev-resman-pf-0</strong><br/><strong>serviceAccount</strong>   | <a href='https://cloud.google.com/iam/docs/understanding-roles#orgpolicy.policyAdmin'>roles/orgpolicy.policyAdmin</a> +•                                                                                                                                          |
| <strong>prod-resman-net-0</strong><br/><strong>serviceAccount</strong> | <a href='https://cloud.google.com/iam/docs/understanding-roles#compute.orgFirewallPolicyAdmin'>roles/compute.orgFirewallPolicyAdmin</a> +<br/><a href='https://cloud.google.com/iam/docs/understanding-roles#compute.xpnAdmin'>roles/compute.xpnAdmin</a> +       |
| <strong>prod-resman-pf-0</strong><br/><strong>serviceAccount</strong>  | <a href='https://cloud.google.com/iam/docs/understanding-roles#orgpolicy.policyAdmin'>roles/orgpolicy.policyAdmin</a> +•                                                                                                                                          |
| <strong>prod-resman-sec-0</strong><br/><strong>serviceAccount</strong> | <a href='https://cloud.google.com/iam/docs/understanding-roles#cloudasset.viewer'>roles/cloudasset.viewer</a> +<br/><a href='https://cloud.google.com/iam/docs/understanding-roles#accesscontextmanager.policyAdmin'>roles/accesscontextmanager.policyAdmin</a> + |

##### Data platform development folder

| <strong>members</strong>                                              | <strong>roles</strong>                                                                                                                                                                                                          |
| :-------------------------------------------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| <strong>dev-resman-dp-0</strong><br/><strong>serviceAccount</strong>  | organizations/[organization #0]/roles/serviceProjectNetworkAdmin<br/>roles/logging.admin<br/>roles/owner<br/>roles/resourcemanager.folderAdmin<br/>roles/resourcemanager.projectCreator                                         |
| <strong>dev-resman-dp-0r</strong><br/><strong>serviceAccount</strong> | <a href='https://cloud.google.com/iam/docs/understanding-roles#resourcemanager.folderViewer'>roles/resourcemanager.folderViewer</a><br/><a href='https://cloud.google.com/iam/docs/understanding-roles#viewer'>roles/viewer</a> |

##### Data platform production folder

| <strong>members</strong>                                               | <strong>roles</strong>                                                                                                                                                                                                          |
| :--------------------------------------------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| <strong>prod-resman-dp-0</strong><br/><strong>serviceAccount</strong>  | organizations/[organization #0]/roles/serviceProjectNetworkAdmin<br/>roles/logging.admin<br/>roles/owner<br/>roles/resourcemanager.folderAdmin<br/>roles/resourcemanager.projectCreator                                         |
| <strong>prod-resman-dp-0r</strong><br/><strong>serviceAccount</strong> | <a href='https://cloud.google.com/iam/docs/understanding-roles#resourcemanager.folderViewer'>roles/resourcemanager.folderViewer</a><br/><a href='https://cloud.google.com/iam/docs/understanding-roles#viewer'>roles/viewer</a> |

##### GKE development folder

| <strong>members</strong>                                               | <strong>roles</strong>                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| :--------------------------------------------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| <strong>dev-resman-gke-0</strong><br/><strong>serviceAccount</strong>  | <a href='https://cloud.google.com/iam/docs/understanding-roles#compute.xpnAdmin'>roles/compute.xpnAdmin</a><br/><a href='https://cloud.google.com/iam/docs/understanding-roles#logging.admin'>roles/logging.admin</a><br/><a href='https://cloud.google.com/iam/docs/understanding-roles#owner'>roles/owner</a><br/><a href='https://cloud.google.com/iam/docs/understanding-roles#resourcemanager.folderAdmin'>roles/resourcemanager.folderAdmin</a><br/><a href='https://cloud.google.com/iam/docs/understanding-roles#resourcemanager.projectCreator'>roles/resourcemanager.projectCreator</a> |
| <strong>dev-resman-gke-0r</strong><br/><strong>serviceAccount</strong> | <a href='https://cloud.google.com/iam/docs/understanding-roles#resourcemanager.folderViewer'>roles/resourcemanager.folderViewer</a><br/><a href='https://cloud.google.com/iam/docs/understanding-roles#viewer'>roles/viewer</a>                                                                                                                                                                                                                                                                                                                                                                   |

##### GKE production folder

| <strong>members</strong>                                                | <strong>roles</strong>                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| :---------------------------------------------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| <strong>prod-resman-gke-0</strong><br/><strong>serviceAccount</strong>  | <a href='https://cloud.google.com/iam/docs/understanding-roles#compute.xpnAdmin'>roles/compute.xpnAdmin</a><br/><a href='https://cloud.google.com/iam/docs/understanding-roles#logging.admin'>roles/logging.admin</a><br/><a href='https://cloud.google.com/iam/docs/understanding-roles#owner'>roles/owner</a><br/><a href='https://cloud.google.com/iam/docs/understanding-roles#resourcemanager.folderAdmin'>roles/resourcemanager.folderAdmin</a><br/><a href='https://cloud.google.com/iam/docs/understanding-roles#resourcemanager.projectCreator'>roles/resourcemanager.projectCreator</a> |
| <strong>prod-resman-gke-0r</strong><br/><strong>serviceAccount</strong> | <a href='https://cloud.google.com/iam/docs/understanding-roles#resourcemanager.folderViewer'>roles/resourcemanager.folderViewer</a><br/><a href='https://cloud.google.com/iam/docs/understanding-roles#viewer'>roles/viewer</a>                                                                                                                                                                                                                                                                                                                                                                   |

##### Networking folder

| <strong>members</strong>                                                | <strong>roles</strong>                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| :---------------------------------------------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| <strong>gcp-network-admins</strong><br/><strong>group</strong>          | <a href='https://cloud.google.com/iam/docs/understanding-roles#editor'>roles/editor</a>                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| <strong>prod-resman-net-0</strong><br/><strong>serviceAccount</strong>  | <a href='https://cloud.google.com/iam/docs/understanding-roles#compute.xpnAdmin'>roles/compute.xpnAdmin</a><br/><a href='https://cloud.google.com/iam/docs/understanding-roles#logging.admin'>roles/logging.admin</a><br/><a href='https://cloud.google.com/iam/docs/understanding-roles#owner'>roles/owner</a><br/><a href='https://cloud.google.com/iam/docs/understanding-roles#resourcemanager.folderAdmin'>roles/resourcemanager.folderAdmin</a><br/><a href='https://cloud.google.com/iam/docs/understanding-roles#resourcemanager.projectCreator'>roles/resourcemanager.projectCreator</a> |
| <strong>prod-resman-net-0r</strong><br/><strong>serviceAccount</strong> | <a href='https://cloud.google.com/iam/docs/understanding-roles#resourcemanager.folderViewer'>roles/resourcemanager.folderViewer</a><br/><a href='https://cloud.google.com/iam/docs/understanding-roles#viewer'>roles/viewer</a>                                                                                                                                                                                                                                                                                                                                                                   |

##### Networking development folder

| <strong>members</strong>                                               | <strong>roles</strong>                                                                                                |
| :--------------------------------------------------------------------- | :-------------------------------------------------------------------------------------------------------------------- |
| <strong>dev-resman-dp-0</strong><br/><strong>serviceAccount</strong>   | organizations/[organization #0]/roles/serviceProjectNetworkAdmin                                                      |
| <strong>dev-resman-dp-0r</strong><br/><strong>serviceAccount</strong>  | <a href='https://cloud.google.com/iam/docs/understanding-roles#compute.networkViewer'>roles/compute.networkViewer</a> |
| <strong>dev-resman-gke-0</strong><br/><strong>serviceAccount</strong>  | organizations/[organization #0]/roles/serviceProjectNetworkAdmin                                                      |
| <strong>dev-resman-gke-0r</strong><br/><strong>serviceAccount</strong> | <a href='https://cloud.google.com/iam/docs/understanding-roles#compute.networkViewer'>roles/compute.networkViewer</a> |
| <strong>dev-resman-pf-0</strong><br/><strong>serviceAccount</strong>   | organizations/[organization #0]/roles/serviceProjectNetworkAdmin                                                      |
| <strong>dev-resman-pf-0r</strong><br/><strong>serviceAccount</strong>  | <a href='https://cloud.google.com/iam/docs/understanding-roles#compute.networkViewer'>roles/compute.networkViewer</a> |

##### Networking production folder

| <strong>members</strong>                                                | <strong>roles</strong>                                                                                                |
| :---------------------------------------------------------------------- | :-------------------------------------------------------------------------------------------------------------------- |
| <strong>prod-resman-dp-0</strong><br/><strong>serviceAccount</strong>   | organizations/[organization #0]/roles/serviceProjectNetworkAdmin                                                      |
| <strong>prod-resman-dp-0r</strong><br/><strong>serviceAccount</strong>  | <a href='https://cloud.google.com/iam/docs/understanding-roles#compute.networkViewer'>roles/compute.networkViewer</a> |
| <strong>prod-resman-gke-0</strong><br/><strong>serviceAccount</strong>  | organizations/[organization #0]/roles/serviceProjectNetworkAdmin                                                      |
| <strong>prod-resman-gke-0r</strong><br/><strong>serviceAccount</strong> | <a href='https://cloud.google.com/iam/docs/understanding-roles#compute.networkViewer'>roles/compute.networkViewer</a> |
| <strong>prod-resman-pf-0</strong><br/><strong>serviceAccount</strong>   | organizations/[organization #0]/roles/serviceProjectNetworkAdmin                                                      |
| <strong>prod-resman-pf-0r</strong><br/><strong>serviceAccount</strong>  | <a href='https://cloud.google.com/iam/docs/understanding-roles#compute.networkViewer'>roles/compute.networkViewer</a> |

##### Core automation project

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

Additive bindings use `+` and conditional bindings use `*`. These role definitions derive from the upstream [Cloud Foundation Fabric Stage 1 IAM reference](https://github.com/GoogleCloudPlatform/cloud-foundation-fabric/blob/master/fast/stages/1-resman/IAM.md).

### 3.3 Code control

#### GitHub repositories

Stellar Engine forks the open-source Cloud Foundation Fabric repository and maintains all stages, blueprints, and modules publicly on GitHub:

- [Cloud Foundation Fabric GitHub repository](https://github.com/GoogleCloudPlatform/cloud-foundation-fabric)
- [Google Public Sector Stellar Engine GitHub repository](https://github.com/google/stellar-engine)

#### Branching strategy

Contributors follow a trunk-based development model in which short-lived feature and bug-fix branches branch from `main` and merge back through reviewed pull requests; see [Trunk-Based Development](https://www.atlassian.com/continuous-delivery/continuous-integration/trunk-based-development) for workflow background. Aligning this branching strategy with upstream Cloud Foundation Fabric preserves clean upstream module synchronization.

#### Pull request validation

Open a [pull request](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/about-pull-requests) targeting `main` once feature or bug-fix changes pass local checks. Maintainers merge the branch into `main` after two reviewers complete code review and all review feedback is resolved.

### 3.4 Infrastructure as Code

Stellar Engine adopts the staged Terraform architecture from [Google Cloud Foundation Fabric](https://github.com/GoogleCloudPlatform/cloud-foundation-fabric). Operators execute stages 0 through 3 sequentially to establish the foundational landing zone before deploying tenant workloads, storing stage state files inside centralized Cloud Storage backend buckets:

- Store all Terraform configurations in a version-controlled infrastructure repository restricted to platform administrators.
- Gate every post-bootstrap configuration change through peer review in the infrastructure repository.

#### Repository layout

Foundational bootstrap and landing zone code lives under `fast/stages` and `fast/stages-aw`. Reusable service modules live under `modules`, while compliance-scoped workload compositions live under `blueprints` organized by target regime subfolder such as `il5` and `fedramp-high`:

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
  - **gemini-enterprise**
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
    - **2-networking-a-fedramp**
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

### 3.5 Terraform design principles

#### Environment partitioning

Terraform configurations partition infrastructure into standalone, per-environment root modules, allowing additional customer tenants to onboard per environment. Keeping each tenant-and-environment configuration explicit and local-driven minimizes blast radius so changes in one tenant or environment do not affect another.

Example configuration:

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

### 3.6 Networking

See the [Google Cloud security foundations networking guide](https://cloud.google.com/architecture/security-foundations/networking) for foundational enterprise network patterns.

#### Shared VPC topology

Google Cloud connects Virtual Private Clouds privately across Google's backbone using VPC Network Peering and [Shared VPC](https://cloud.google.com/vpc/docs/shared-vpc). Centralizing Shared VPC subnets, routes, and firewall policies in dedicated host projects simplifies network governance while allowing service project teams to deploy and manage workload resources independently.

Resources attached to Shared VPC networks communicate across project boundaries over internal IP addresses. Managing shared network constructs such as subnets, routes, and firewalls from a central host project enforces consistent network security policies across tenant projects.

In the `example.com` reference model, each environment separates workloads across two Shared VPC host projects: a `base` Shared VPC for workloads handling non-sensitive data and a `restricted` Shared VPC protected by [VPC Service Controls](https://cloud.google.com/vpc-service-controls) for workloads handling sensitive data.

Deploying this dual-Shared-VPC model independently across the common, development, non-production, and production environments provides strict network segmentation between lifecycle tiers.

In the hub-and-spoke variant, all environment spokes communicate with shared operational services in the common environment hub, such as CI/CD runners, directory services, and security tooling. A base Shared VPC hub connects the base spoke networks across development, non-production, and production, while a restricted Shared VPC hub connects the restricted spoke networks across those same environments. Select the restricted Shared VPC hub-and-spoke topology whenever workloads require VPC Service Controls data exfiltration protections.

#### Virtual Private Clouds

A VPC provides an isolated virtual network for Google Cloud resources with customizable IP address ranges, regional subnets, and routing tables. Evaluate your organization's segmentation requirements before allocating VPC boundaries across tenants.

VPC Network Peering connects VPC networks within the same project or across separate projects over internal IP addresses without external gateways or public internet traversal, keeping inter-VPC traffic entirely on Google's private network backbone.

#### Subnet allocations

Subnet allocation divides a VPC primary CIDR block into regional IP segments for Compute Engine VMs, Google Kubernetes Engine clusters, and managed services. The reference subnet allocation scheme supports up to eight organizations, eight tenants per organization, and eight projects per tenant, for a maximum of 512 projects.

The table below shows the four `/25` subnet allocations inside Project 1's `10.200.2.0/23` CIDR block (`512` total addresses):

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

Use the table above when allocating CIDRs for new projects within the `10.200.0.0/16` tenant range.

#### Private Google Access

Route traffic from VPC workloads to Google-managed APIs such as App Engine, Cloud SQL, and Cloud Functions over internal IP space using [Private Google Access](https://cloud.google.com/vpc/docs/private-google-access), which Stellar Engine enables across managed subnets. Route traffic from serverless Google-managed environments back into your VPC over internal IP space using [Serverless VPC Access](https://cloud.google.com/vpc/docs/serverless-vpc-access).

#### Inter-service communication

Route synchronous microservice-to-microservice traffic inside the VPC through [Internal Application Load Balancing](https://cloud.google.com/load-balancing/docs/l7-internal) or [Private Google Access](https://cloud.google.com/vpc/docs/private-google-access), and decouple asynchronous service messaging with [Cloud Pub/Sub](https://cloud.google.com/pubsub).

#### VPC firewall rules

By default, VPC networks deny all unsolicited ingress traffic and allow egress traffic unless overridden. Define ingress and egress firewall rules in `2-networking-a-peering` or your active Stage 2 networking configuration. Google Cloud VPC firewall rules are stateful and evaluate in numeric priority order: the highest-priority rule matching source IP, destination IP, protocol, and port governs the flow, and lower-priority rules are skipped.

#### Hub-and-spoke topology

Stellar Engine implements a hub-and-spoke network topology using either Network Connectivity Center with the `STAR` preset topology or VPC Network Peering depending on your target compliance regime. Centralized hub VPCs host shared DNS, Cloud VPN and Cloud Interconnect hybrid gateways, and perimeter inspection, while spoke VPCs isolate workload environments such as integration, testing, and production.

#### Compliance regime overlays

Stellar Engine provides two Stage 2 hub-and-spoke implementations tailored to FedRAMP Moderate, FedRAMP High, DoD IL2, IL4, and IL5 environments. Both stages use Shared VPC so network governance remains centralized in host projects while tenant teams deploy workloads into attached service projects:

- Stage `2-networking-a-fedramp` connects the central `hub-0` Shared VPC and optional `egress-0` Secure Web Proxy VPC in the Network Connectivity Center `center` group to environment `<env>-spoke-0` Shared VPCs in the `edge` group, enforcing spoke-to-spoke isolation without VPC peering scaling limits.
- Stage `2-networking-b-il5-ngfw` deploys a three-VPC Virtual Datacenter Security Stack comprising `Landing` trust, `DMZ` untrust, and `Mgmt` VPCs peered to environment spoke Shared VPCs through inline Palo Alto Networks VM-Series Next-Generation Firewalls.

##### FedRAMP High and Moderate pattern

Stage `2-networking-a-fedramp` implements the FedRAMP High, FedRAMP Moderate, and IL2 network architecture:

- The topology connects a central `hub-0` Shared VPC and an optional `egress-0` Secure Web Proxy internet egress spoke through a `STAR` Network Connectivity Center hub.
- Perimeter security combines folder-level hierarchical firewall policies with per-VPC global network firewall policies supporting Cloud NGFW Essentials, Standard, and Enterprise tiers, `center` and `edge` NCC group isolation, distributed Cloud NAT or centralized Secure Web Proxy next-hop internal load balancer egress, and per-VPC Private Service Connect endpoints for Google APIs.
- A central `<prefix>-net-hub-host` Shared VPC host project provides centralized Cloud DNS, inbound DNS forwarding, Private Service Connect `all-apis` or `vpc-sc` endpoints, and optional hybrid VPN or Interconnect transit across environment spokes attached to the `main` `STAR` hub.
- FedRAMP Moderate, FedRAMP High, and IL2 consolidate onto `2-networking-a-fedramp` for NIST SP 800-53 SC-7 and AC-4 network segmentation, while `kms_protection_level` differentiates cryptographic key protection (`SOFTWARE` for Moderate and IL2 versus `HSM` for High) under SC-12 and SC-13.
- Although the Stage 0 `FEDRAMP_MODERATE` organization policy template permits non-`asia-east2` locations at the organization policy layer, `2-networking-a-fedramp` is designed and validated for US regions (`in:us-locations`, defaulting to `us-east4` and `us-west1` or `us-central1`) to match Assured Workloads regional boundaries.
- DoD Impact Level 2 (`IL2`) workloads deploy on `2-networking-a-fedramp` paired with `kms_protection_level = "SOFTWARE"`, whereas `IL4` and `IL5` workloads deploy on `2-networking-b-il5-ngfw`.

##### IL5 pattern

Stage `2-networking-b-il5-ngfw` implements the DoD IL4 and IL5 Virtual Datacenter Security Stack architecture:

- The topology separates perimeter inspection across Landing and DMZ VPCs in a Virtual Datacenter Security Stack layout.
- Inline Next-Generation Firewalls enforce perimeter and inter-zone traffic inspection.
- A scalable cluster of Palo Alto Networks VM-Series firewalls provides Layer 7 inspection, intrusion prevention, and application-aware filtering required for IL5 accreditation.

## 4. Assured Workloads

Google Cloud Assured Workloads enforces compliance guardrails across regulated folders, enabling FedRAMP Moderate by default on the Assured Workloads root folder so child folders and projects inherit the selected compliance constraints automatically.

When you provision an Assured Workloads environment and select a compliance regime, Assured Workloads applies regional `constraints/gcp.resourceLocations` organization policies to keep data at rest within authorized geographic regions.

Define tenant folders and compliance settings in the `1-resman` `terraform.tfvars` file. The following configuration defines an example tenant with IL5 Assured Workloads settings:

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

Omitting the `compliance` block generates the tenant folder without an Assured Workloads configuration. See the [Terraform Assured Workloads documentation](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/assured_workloads_workload#compliance_regime) for supported compliance regimes.

## 5. Information security

The Stellar Engine information security strategy enforces controlled access to cloud resources and cryptographic protection of data at rest and in transit.

### 5.1 Access control

#### Account types

Manage human user identities through Google Identity Platform or Google Workspace, as described under Identity providers below.

Assign workloads and automated services to dedicated service accounts rather than human user accounts. Each service account uses a unique email address as its principal identifier. Google Cloud supports three categories of service accounts:

- Create and manage user-managed service accounts explicitly to serve as dedicated runtime identities for application and compute workloads.
- Manage or restrict default service accounts that Google Cloud creates automatically when you enable certain APIs.
- Allow Google-managed service accounts to execute background platform operations on your behalf.

Service account impersonation lets an authorized principal assume a service account's permissions temporarily to execute CLI commands or Terraform runs without exporting static keys, while blocking interactive Google Cloud console sign-in as the service account. Stellar Engine configures Terraform provider impersonation to provision projects and foundational resources.

#### Identity providers

Provide workforce and application identity through [Google Identity Platform](https://cloud.google.com/identity-platform) or [Cloud Identity](https://cloud.google.com/identity).

Google Identity Platform delivers customer identity and access management capabilities to protect application user accounts at scale on Google Cloud.

Cloud Identity provides Identity as a Service to manage workforce users and groups accessing Google Cloud and Google Workspace resources, and also acts as an identity provider for third-party SAML and LDAP applications.

#### Multi-factor authentication

Enforce multi-factor authentication across all user accounts to defend against phishing and credential compromise. Google corporate accounts require hardware-backed multi-factor authentication, and customers and partners should enforce equivalent multi-factor policies across all identities.

Stellar Engine cannot configure Workspace-level multi-factor authentication automatically during bootstrap, so you must enforce multi-factor authentication in your identity directory to meet IL5 compliance requirements.

#### Role-based access control

Role-based access control bindings and group hierarchies follow the design in section 3.2.

### 5.2 Data security

#### Platform security

Google provides [foundational infrastructure security](https://cloud.google.com/security/) across Google Cloud, while securing customer workloads and data remains a shared responsibility. Review and tailor the controls below to each workload that you deploy on Google Cloud.

#### Data protection

Google encrypts all inter-service platform communication channels automatically; enforce encrypted transport across all client and application-level network connections.

Google encrypts all data at rest across physical storage media to prevent unauthorized physical inspection, and you can supply Customer-Managed Encryption Keys for Compute Engine persistent disks and Cloud Storage buckets.

Database services encrypt stored data automatically at the storage layer; add application-level encryption for sensitive columns to prevent privileged users from reading raw records and to limit exposure during an intrusion.

When loading regulated datasets containing PII or PCI records into BigQuery, enforce applicable privacy and compliance controls and govern downstream query aggregation.

#### Cloud KMS

Use [Cloud Key Management Service](https://cloud.google.com/kms/) whenever workloads require application-layer encryption or customer-managed cryptographic keys to satisfy regulatory mandates.

##### Key management practices

- Rotate encryption keys regularly on an automated schedule through `gcloud`, Terraform, or the Google Cloud console to bound the data volume protected by each key version.
- Enforce separation of duties by running Cloud KMS in a dedicated project without project-level Owner bindings and managing access through an Organization Administrator. Separate Cloud KMS administration roles from `cryptoKeyEncrypterDecrypter` permissions so administrators who set IAM policies cannot decrypt workload data.
- Pass Additional Authenticated Data strings on Cloud KMS encrypt and decrypt API calls as an integrity check against [confused deputy attacks](https://en.wikipedia.org/wiki/Confused_deputy_problem). Cloud KMS refuses to decrypt ciphertext unless the caller supplies the exact Additional Authenticated Data string used during encryption, defaulting to an empty string when omitted.

#### Cloud Storage

Cloud Storage addresses buckets and objects by name, allowing external callers to infer bucket or object existence from error responses even when ACLs and IAM policies deny access. Apply these naming and access controls to protect bucket metadata and stored objects:

- Include random suffixes in bucket names such as `stellar-engine-mybucket-gxl3` so unauthorized parties cannot guess or enumerate bucket names.
- Configure [default object ACLs](https://cloud.google.com/storage/docs/access-control#default) or uniform bucket-level access before uploading objects to avoid retroactive per-object permission updates.
- Account for independent bucket and object ACLs when legacy fine-grained ACLs are enabled, because granting `GroupA` bucket listing permissions and `GroupB` object read permissions lets `GroupB` read a known object without listing the bucket.
- Segregate public assets into dedicated, clearly labeled buckets such as `stellar-engine-mybucket-public-3vxa` rather than mixing public and private objects.
- Verify access controls carefully before marking any object publicly readable, because internet-published objects can be copied immediately outside your control.
- Avoid granting public write permissions on Cloud Storage buckets, because publicly writable buckets invite abuse, malware distribution, and legal or financial liability for hosted content.
- Issue [signed URLs](https://cloud.google.com/storage/docs/access-control/signed-urls) with explicit read, write, or delete scope and short expiration windows whenever external users without Google accounts need temporary access to specific objects.

#### Data residency

Control physical data placement by applying [Organization Policy constraints](https://cloud.google.com/resource-manager/docs/organization-policy/overview) across your organization, folders, or projects. Combine the [resource locations constraint](https://cloud.google.com/resource-manager/docs/organization-policy/defining-locations) with least-privilege IAM service permissions so operators cannot provision resources in unauthorized regions.

Defining `constraints/gcp.resourceLocations` restricts newly created resources only; resources provisioned prior to policy enforcement remain active in their existing regions until migrated.

#### Encryption at rest

Google Cloud encrypts all stored data at rest using AES-256 with [Google-managed](https://cloud.google.com/storage/docs/encryption/default-keys) data encryption keys ([DEKs](https://cloud.google.com/security/encryption/default-encryption#key_management)) backed by Google's FIPS 140-2 validated cryptographic module, [BoringCrypto](https://csrc.nist.gov/projects/cryptographic-module-validation-program/Certificate/3318).

#### Encryption in transit

Microservices communicate primarily over [Cloud Pub/Sub](https://cloud.google.com/pubsub/docs/encryption) and HTTPS REST endpoints to maintain encryption in transit across project boundaries.

#### TLS version

Require TLS 1.2 or higher across all web services, disable the `TLS_ECDHE_RSA_WITH_AES_128_CBC_SHA` (`0xc013`) and `TLS_ECDHE_RSA_WITH_AES_256_CBC_SHA` (`0xc014`) cipher suites, and enforce minimum protocol versions with the `gcp.restrictTLSVersion` organization policy constraint.

### 5.3 Logging and auditing

#### Audit logs

Google Cloud collects three categories of [Cloud Audit Logs](https://cloud.google.com/logging/docs/audit):

- Admin Activity audit logs record API calls and administrative actions that modify resource configurations or metadata, such as creating VM instances or updating IAM bindings.
- Data Access audit logs record API calls that read resource configurations or metadata as well as user-driven calls that create, modify, or read user-provided resource data.
- System Event audit logs record automated Google Cloud actions that modify resource configurations independently of direct user requests.

#### Network and access logs

Enable network and provider access telemetry alongside Cloud Audit Logs:

- VPC Flow Logs sample network flows sent from and received by Compute Engine VM instances and Google Kubernetes Engine nodes to support network monitoring, forensics, security analysis, and traffic optimization.
- Firewall Rules Logging audits and verifies firewall rule behavior and tracks connection counts matching allow or deny rules.
- Access Transparency logs record Google personnel activity during phone-initiated support actions, engineering support investigations, and platform recovery operations.

#### Log destinations

Export audit and network logs without expiration to centralized retention sinks in BigQuery, Cloud Storage, or Pub/Sub.

When routing logs to a destination in another project, grant destination write permissions to the log sink writer identity service account, and authorize that writer identity in any VPC Service Controls perimeters or access policies protecting the destination project.

### 5.4 Monitoring

#### Host projects

Dedicated security core projects host Cloud Monitoring workspaces, dashboards, and alerting policies for each environment:

| Folder | Monitoring project |
| :--- | :--- |
| Security | `<prefix>`-dev-sec-core-0 |
| Security | `<prefix>`-prod-sec-core-0 |

#### Monitoring groups

Stage 0 bootstrap provisions the `gcp-monitoring-admins` group described in section 3.2 to administer monitoring configurations.

#### Alerting policies

Configure Cloud Monitoring alerting policies on events and log-based metrics to specify trigger conditions and notification channels so operations teams detect and resolve service issues rapidly.

#### Dashboards

Cloud Monitoring installs default service dashboards automatically when you provision Google Cloud resources, and you can deploy custom dashboards to correlate metrics, alerting policies, and log entries from multiple services in a single view.

### 5.5 Security boundaries

In the reference boundary architecture, the authorization boundary encompasses the Assured Workloads folder hierarchy, shared networking and security host projects, and attached tenant service projects.

#### Organization policy inheritance

Child folders and projects inherit parent organization policies according to `inheritFromParent`. Setting `inheritFromParent = true` merges and reconciles the parent node's effective policy with local rules, whereas setting `inheritFromParent = false` reverts to the constraint's default behavior unless explicit allow or deny rules are defined on the child node.

#### Project layout and VPC Service Controls

Terraform manages all cross-project IAM bindings declaratively across the folder and project hierarchy described in section 3.1. Within the hub-and-spoke network topology, a default VPC Service Controls perimeter surrounds the project hosting the restricted Shared VPC.

VPC Service Controls mitigate data exfiltration risks by wrapping specified Google Cloud services inside security perimeters that block data egress to unauthorized external IP addresses even when an attacker holds valid user or service account credentials. Combine VPC Service Controls with BeyondCorp Context-Aware Access policies to enforce IP-range and device-trust checks on requests originating outside privileged networks.

### 5.6 Network security

#### Shared VPC access control

Attach tenant service projects to centralized Shared VPC host networks and grant workload service accounts subnet-scoped [`compute.networkUser`](https://cloud.google.com/iam/docs/job-functions/networking) permissions so workloads can allocate internal IP addresses only in authorized subnets.

#### Environment firewall rules

Administer Shared VPC firewall rules centrally in the host project, enforcing default-deny ingress, managed egress, and environment-scoped policies across development, non-production, and production tiers.

#### Cloud DNS

Stellar Engine uses Google Cloud DNS to provide private and hybrid name resolution across Shared VPC networks.

### 5.7 Customer security practices

Separating workloads across isolated projects with least-privilege IAM boundaries minimizes blast radius and lets application teams ship on independent release schedules.

#### Security Command Center

Security Command Center remains on the IL5 authorization roadmap and is not yet approved for IL5 production workloads; manual deployment is required where supported. Follow the [Security Command Center deployment guide](./scc-deployment-guide.md) to activate the service.

[Security Command Center](https://cloud.google.com/security-command-center/) centralizes asset inventory, policy posture, and threat detection across Google Cloud:

- Discovers and tracks cloud resources through the Cloud Asset Inventory API.
- Scans Cloud Storage buckets for sensitive PII using Cloud Data Loss Prevention; verify [Cloud DLP regional availability](https://cloud.google.com/dlp/docs/locations) and regulatory data residency requirements before scanning.
- Scans web applications for cross-site scripting flaws and outdated libraries.
- Publishes Pub/Sub notifications when assets are created, modified, or deleted.

Activating the Security Command Center Premium tier enables built-in managed detection services:

- [Event Threat Detection](https://cloud.google.com/event-threat-detection/docs/)
- [Cloud Anomaly Detection](https://cloud.google.com/security-command-center/docs/how-to-view-vulnerabilities-threats#anomaly_detection)
- [Security Health Analytics](https://cloud.google.com/security-command-center/docs/how-to-manage-security-health-analytics), which holds [CIS Security Software Certification](https://www.cisecurity.org/partner/google-inc/) for the CIS Google Cloud Platform Foundation Benchmark v1.0.0 Levels 1 and 2.

[Security Health Analytics findings](https://cloud.google.com/security-command-center/docs/concepts-security-health-analytics-findings) also include reference mappings to OWASP Top Ten, NIST SP 800-53, and ISO 27001 controls; review each standard's primary guidance when validating compliance manually.

Apply these operational practices when running Security Command Center:

1. Review risk reports and posture findings regularly in the Security Command Center dashboard.
2. Automate asset scanning with the [Cloud Asset API](https://cloud.google.com/asset-inventory/docs/reference/rest) and publish custom analyzer results back into Security Command Center through the [Findings API](https://cloud.google.com/security-command-center/docs/how-to-api-create-manage-findings#creating_a_finding).
3. Configure Pub/Sub finding exports to stream alerts into your external SIEM platform.

#### VPC and hierarchical firewall governance

| Aspect | Specification |
| :--- | :--- |
| Requirements | Enforce default-deny ingress, manage all firewall rules through Terraform Infrastructure as Code, and target specific workload identities or node pools such as GKE node pools. |
| Design constraints | None. |
| Assumptions | None. |

Each VPC network enforces a distributed, stateful virtual firewall at the host network layer across Compute Engine VMs and GKE clusters independently of guest operating systems, allowing return traffic automatically for permitted flows.

VPC firewall rules match traffic by protocol, port, direction, and source or destination CIDRs, subnets, network tags, or service accounts. Because firewall rules cannot be renamed after creation, adopt a consistent naming convention before provisioning rules.

Every VPC network includes two built-in implied firewall rules at priority `65535`:

- The implied allow egress rule (`ALLOW`, destination `0.0.0.0/0`, priority `65535`) permits outbound traffic from any instance except traffic [blocked by Google Cloud](https://cloud.google.com/vpc/docs/firewalls#blockedtraffic), unless a higher-priority rule restricts egress.
- The implied deny ingress rule (`DENY`, source `0.0.0.0/0`, priority `65535`) blocks unsolicited inbound connections to all instances unless a higher-priority rule explicitly allows ingress.

You cannot delete the implied rules, so override them with explicit rules at higher priorities (`0` through `65534`).

Enable Firewall Rules Logging individually on each allow or deny rule whose traffic you need to audit. When enabled, Google Cloud writes a connection record containing source and destination IP addresses, protocol, ports, timestamp, and matched rule reference to Cloud Logging for viewing or export; see [Using Firewall Rules Logging](https://cloud.google.com/vpc/docs/using-firewall-rules-logging) for details.

Alongside VPC-level firewall rules, hierarchical firewall policies enforce consistent allow, deny, or `goto_next` delegation rules at the organization node or individual folders so lower-level VPC rules cannot override organization-wide security controls. Evaluation starts at the organization node and proceeds down folder levels; for Shared VPC workloads, policy inheritance follows the Shared VPC host project's folder path rather than the service project's folder path, and `targetResources` can scope rules to specific VPC networks.

Apply these firewall governance recommendations across environments:

1. Scope rules by dedicated workload service accounts rather than network tags wherever possible, because service accounts are project-specific and changing a VM's service account requires stopping and restarting the instance.
2. Restrict network tag-based firewall rules tightly because any user able to edit VM metadata can attach an arbitrary network tag across projects.
3. Use specific subnet ranges or summarized CIDR blocks when broader network-level rules are required.
4. Create an explicit high-priority egress-deny catch-all rule ahead of the implied `65535` allow-egress rule so both ingress and egress traffic require explicit authorization.
5. Enforce a deterministic firewall naming convention and populate rule descriptions to preserve audit context.
6. Modify firewall rules managed automatically by Google Cloud service agents such as Google Kubernetes Engine only as documented by that service to avoid cluster disruptions or SLA invalidation.
7. Enable Firewall Rules Logging on security-relevant allow and deny rules for continuous verification.
8. Use Network Intelligence Center [Firewall Insights](https://cloud.google.com/network-intelligence-center/docs/firewall-insights/concepts/overview) to identify shadowed rules, overly permissive ranges, and unused rulesets.
9. Manage all custom firewall rules centrally in [Terraform](https://www.terraform.io/docs/providers/google/r/compute_firewall.html) through peer-reviewed CI/CD pipelines for full audit traceability.
10. Use [hierarchical firewall policies](https://cloud.google.com/vpc/docs/firewall-policies) to enforce organization-wide baseline rules above individual project administrators.

#### Data management

##### Sensitive data inspection

Use Cloud Data Loss Prevention to scan application and Kubernetes container logs on a recurring schedule and generate reports identifying any inadvertently logged PII or sensitive tokens.

### 5.8 Vulnerability management

Vulnerability management tooling has limited service availability inside IL5 enclaves; this section documents the target architecture where Security Command Center scanning services are supported.

#### Rapid Vulnerability Detection

Security Command Center Premium includes [Rapid Vulnerability Detection](https://cloud.google.com/security-command-center/docs/concepts-rapid-vulnerability-detection-overview#overview) to identify critical exposures across public-facing endpoints.

#### Supported scan targets

- Compute Engine
- External Cloud Load Balancing
- Google Kubernetes Engine ingress
- Cloud Run
- App Engine

#### Managed scans

Rapid Vulnerability Detection runs automated weekly scans using [Cloud Asset Inventory](https://cloud.google.com/asset-inventory/docs/overview#features) discovery without requiring manual target URL lists to [detect](https://cloud.google.com/security-command-center/docs/concepts-rapid-vulnerability-detection-overview#scan_findings_and_remediations):

- Weak credentials
- Exposed network interfaces
- Incomplete software installations
- Known vulnerable software versions
- Exposed administrative user interfaces

#### Service enablement

Enable [Rapid Vulnerability Detection](https://cloud.google.com/security-command-center/docs/how-to-use-rapid-vulnerability-detection#enabling) on the Security Command Center Services page in the Google Cloud console. Initial scans run automatically within 24 hours of activation and repeat weekly thereafter.

##### Testing

Deploy the open-source [Tsunami Security Scanner Testbed](https://github.com/google/tsunami-security-scanner-testbed/tree/master/truepositives/secure) in a non-production sandbox to generate sample vulnerability findings and validate alerting pipelines.

##### Reviewing findings

Review project-level vulnerability findings in the Security Command Center console dashboard or query them programmatically through the [Security Command Center API](https://cloud.google.com/security-command-center/docs/how-to-api-list-findings#list_all_findings).

##### Viewing findings

Inspect Rapid Vulnerability Detection and integrated VM Manager [vulnerability findings](https://cloud.google.com/security-command-center/docs/concepts-vulnerabilities-findings) filtered by IP address or port in the Google Cloud console under [Findings](https://cloud.google.com/security-command-center/docs/how-to-use-rapid-vulnerability-detection#display-findings-for-port-or-ip) or through the [Security Command Center API](https://cloud.google.com/security-command-center/docs/how-to-api-list-findings#list_all_findings).
