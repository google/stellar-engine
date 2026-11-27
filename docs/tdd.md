# Stellar Engine technical design document

| Field | Value |
| :--- | :--- |
| Date updated | November 2026 |
| Version | v7.0 |
| Recent changes | Aligned Stages 0 through 3, organization policies, IAM, module inventory, networking, and Assured Workloads documentation with Stellar Engine v7 |

This document serves as an illustrative technical working reference to guide project delivery. Its activities and design goals provide architectural detail and do not supersede any legal terms or conditions defined in the customer's written contract with Google.

<!-- BEGIN TOC -->
- [1. Purpose](#1-purpose)
- [2. Executive summary](#2-executive-summary)
  - [2.1 Overview](#21-overview)
  - [2.2 Project architecture](#22-project-architecture)
- [3. Cloud foundation](#3-cloud-foundation)
  - [3.1 Project organization](#31-project-organization)
    - [Network security and isolation](#network-security-and-isolation)
    - [Data security and compute hardening](#data-security-and-compute-hardening)
    - [IAM and service accounts](#iam-and-service-accounts)
    - [Serverless security](#serverless-security)
    - [Resource management and logging](#resource-management-and-logging)
    - [Optional guardrail policy packs](#optional-guardrail-policy-packs)
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
      - [Data platform folders](#data-platform-folders)
      - [GKE folders](#gke-folders)
      - [Networking folder](#networking-folder)
      - [Networking development folder](#networking-development-folder)
      - [Networking production folder](#networking-production-folder)
      - [Security folder](#security-folder)
      - [Teams and sandbox folders](#teams-and-sandbox-folders)
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
    - [OS and host vulnerability scanning](#os-and-host-vulnerability-scanning)
    - [Container and artifact scanning](#container-and-artifact-scanning)
    - [Security Command Center posture and threat findings](#security-command-center-posture-and-threat-findings)
    - [Regime scanning requirements](#regime-scanning-requirements)
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

The supplied directory structure and Terraform modules provide a starting foundation with pragmatic defaults that you can tailor to organizational requirements. Operators apply Stage `0-bootstrap` once during initial setup to create core administrative projects, Cloud Storage state buckets, Workload Identity Federation providers in `fast/stages-aw/0-bootstrap/workload-identity.tf`, and CI/CD automation resources in `fast/stages-aw/0-bootstrap/cicd.tf` with templates for GitHub Actions, GitLab CI/CD, and Cloud Build or Source Repositories. Subsequent stages execute either through those keyless CI/CD pipelines or via operator impersonation of stage service accounts.

Stage 0 creates the root Assured Workloads enclave folder `StellarEngine-<prefix>` via `google_assured_workloads_workload.primary`, defaulting to `IL5` in `US`, together with a `<RegimeCode> Common Services` folder for core administrative projects. Stage `1-resman` creates environment folders named `<RegimeCode> <Env>` under the root enclave folder to isolate non-production and production tenant folders inside the deployment's Assured Workloads boundary. Workloads requiring separate compliance regimes deploy into separate landing zone installations unless isolated at separate organization or folder boundaries outside Terraform.

### 2.1 Overview

Bootstrap scripts and staged Terraform configurations provision a baseline landing zone inside an Assured Workloads folder. Once the foundation is active, you can deploy individual Google Cloud and approved third-party workload blueprints based on tenant requirements, as detailed in section 3.4.

### 2.2 Project architecture

In the `example.com` reference architecture, Stage 0 provisions foundational projects inside the `<RegimeCode> Common Services` folder under `StellarEngine-<prefix>` to host shared automation, audit logging, and optional billing export telemetry:

| Project | Description |
| :--- | :--- |
| `<prefix>-prod-iac-core-0` | Hosts the Terraform state buckets, stage automation service accounts, and core KMS state encryption keys. Restrict access to this project tightly. |
| `<prefix>-prod-audit-logs-0` | Hosts centralized organization log sinks, KMS keys for logging, and 365-day Cloud Logging retention buckets. |
| `<prefix>-prod-billing-exp-0` | Optional project provisioned when `billing_account.is_org_level` is true to host a BigQuery dataset for organization [billing exports](https://cloud.google.com/billing/docs/how-to/export-data-bigquery). |

## 3. Cloud foundation

### 3.1 Project organization

Stage `0-bootstrap` enforces organization policies defined under `fast/stages-aw/0-bootstrap/data/org-policies/`, `data/custom-org-policies/`, and `data/custom-constraint-policies/`. By default, Terraform attaches policies at the organization node. When `deploy_org_resources.org_policies` is `false` for folder-scoped deployments, `module.root-folder-config[0]` applies eligible policies onto the `StellarEngine-<prefix>` root folder while excluding organization-only `resourcemanager.accessBoundaries`, custom constraints under `custom.*`, and the 12 baseline constraints listed in `aw_managed_policies` (`compute.disableGlobalCloudArmorPolicy`, `compute.disableGlobalLoadBalancing`, `compute.setNewProjectDefaultToZonalDNSOnly`, `compute.skipDefaultNetworkCreation`, `gcp.resourceLocations`, `gcp.restrictCmekCryptoKeyProjects`, `gcp.restrictNonCmekServices`, `gcp.restrictServiceUsage`, `gcp.restrictTLSVersion`, `iam.automaticIamGrantsForDefaultServiceAccounts`, `iam.disableServiceAccountKeyCreation`, and `storage.publicAccessPrevention`) so folder applies do not collide with Assured Workloads controls.

#### Network security and isolation

| Constraint | Enforcement |
| :--- | :--- |
| `compute.vmExternalIpAccess` | Denies all external IP addresses on Compute Engine VM instances. |
| `compute.skipDefaultNetworkCreation` | Skips creation of the `default` VPC network in newly created projects. |
| `compute.requireVpcFlowLogs` | Requires `COMPREHENSIVE` VPC Flow Logs across managed subnetworks. |
| `custom.restrictFirewallRanges` | Custom constraint denying ingress firewall rules that allow `0.0.0.0/0` or `::/0`. |
| `compute.restrictProtocolForwardingCreationForTypes` | Restricts forwarding rules to `INTERNAL` addresses; skipped when `regime` is `FEDRAMP_MODERATE`. |
| `compute.managed.restrictProtocolForwardingCreationForTypes` | Enforces Google-managed internal protocol forwarding; skipped when `regime` is `FEDRAMP_MODERATE`. |
| `compute.restrictLoadBalancerCreationForTypes` | Restricts load balancer creation to `INTERNAL` types; skipped when `regime` is `FEDRAMP_MODERATE`. |
| `compute.disableGlobalLoadBalancing` | Disables global load balancing resources; skipped when `regime` is `FEDRAMP_MODERATE`. |
| `compute.disableGlobalCloudArmorPolicy` | Disables global Cloud Armor policies; skipped when `regime` is `FEDRAMP_MODERATE`. |
| `compute.disableGlobalSelfManagedSslCertificate` | Disables global self-managed SSL certificates; skipped when `regime` is `FEDRAMP_MODERATE`. |
| `compute.restrictCloudNATUsage` | Restricts Cloud NAT gateways to `under:organizations/<org_id>`. |
| `compute.restrictDedicatedInterconnectUsage` | Restricts Dedicated Interconnect attachments to `under:organizations/<org_id>`. |
| `compute.restrictPartnerInterconnectUsage` | Restricts Partner Interconnect attachments to `under:organizations/<org_id>`. |
| `compute.restrictVpcPeering` | Restricts VPC Network Peering to `under:organizations/<org_id>` and configured `allowed_vpc_peering_producers`, defaulting to `under:folders/832634261155`. |
| `compute.setNewProjectDefaultToZonalDNSOnly` | Configures newly created projects to use zonal internal DNS by default. |
| `compute.disableAllIpv6` | Explicit baseline entry set to `enforce: false` to permit IPv6 configuration unless disabled by deployment policy. |
| `compute.disableHybridCloudIpv6` | Explicit baseline entry set to `enforce: false` for hybrid Cloud Router, Interconnect, and VPN IPv6 stacks. |
| `compute.disableInternetNetworkEndpointGroup` | Explicit baseline entry set to `enforce: false` for Internet Network Endpoint Groups. |
| `compute.disableVpcExternalIpv6` | Explicit baseline entry set to `enforce: false` for external IPv6 subnetworks. |
| `compute.disableVpcInternalIpv6` | Explicit baseline entry set to `enforce: false` for internal IPv6 subnetworks. |
| `iap.requireGlobalIapWebDisabled` | Explicit baseline entry set to `enforce: false` for global Identity-Aware Proxy web backends. |
| `iap.requireRegionalIapWebDisabled` | Explicit baseline entry set to `enforce: false` for regional Identity-Aware Proxy web backends. |
| `datastream.disablePublicConnectivity` | Disables public IP connectivity for Datastream connection profiles. |
| `sql.restrictAuthorizedNetworks` | Blocks unproxied authorized network ranges on Cloud SQL instances. |
| `sql.restrictPublicIp` | Blocks public IP addresses on Cloud SQL instances. |

#### Data security and compute hardening

| Constraint | Enforcement |
| :--- | :--- |
| `custom.kmsRotation` | Custom constraint requiring `SYMMETRIC_ENCRYPTION` Cloud KMS key rotation periods of 90 days (`7776000s`) or less. |
| `gcp.restrictNonCmekServices` | Denies `documentai.googleapis.com` by default unless configured with compliant CMEK settings. |
| `gcp.restrictTLSVersion` | Denies `TLS_VERSION_1` and `TLS_VERSION_1_1` across TLS endpoints. |
| `gcp.resourceLocations` | Enforces `in:us-locations` for `IL4`, `IL5`, and `FEDRAMP_HIGH`, and denies `in:asia-east2-locations` and `in:global` when `regime` is `FEDRAMP_MODERATE`. |
| `compute.requireShieldedVm` | Requires Shielded VM vTPM and integrity monitoring features on Compute Engine instances. |
| `compute.disableNestedVirtualization` | Disables nested virtualization on Compute Engine VM instances. |
| `compute.disableSerialPortAccess` | Disables interactive serial port access on Compute Engine VM instances. |
| `compute.disableGuestAttributesAccess` | Disables Compute Engine guest attributes metadata access. |
| `compute.disableSshInBrowser` | Explicit baseline entry set to `enforce: false` for Cloud Console SSH-in-browser. |
| `compute.trustedImageProjects` | Restricts instance boot images to 20 approved public and partner image projects including `paloaltonetworksgcp-public`. |
| `storage.uniformBucketLevelAccess` | Requires uniform bucket-level access across Cloud Storage buckets. |
| `storage.publicAccessPrevention` | Blocks public access on Cloud Storage buckets. |
| `storage.secureHttpTransport` | Requires HTTPS transport for Cloud Storage requests. |
| `appengine.disableCodeDownload` | Disables source code downloads from App Engine applications. |
| `bigquery.disableBQOmniAWS` | Disables BigQuery Omni cross-cloud connections to AWS. |
| `bigquery.disableBQOmniAzure` | Disables BigQuery Omni cross-cloud connections to Azure. |
| `firestore.requireP4SAforImportExport` | Explicit baseline entry set to `enforce: false` for Firestore P4SA import and export enforcement. |
| `clouddeploy.disableServiceLabelGeneration` | Explicit baseline entry set to `enforce: false` for Cloud Deploy service label generation. |

#### IAM and service accounts

| Constraint | Enforcement |
| :--- | :--- |
| `iam.disableServiceAccountKeyCreation` | Disables user-managed service account key creation. |
| `iam.managed.disableServiceAccountKeyCreation` | Managed constraint disabling user-managed service account key creation. |
| `iam.disableServiceAccountKeyUpload` | Disables uploading external public keys to service accounts. |
| `iam.managed.disableServiceAccountKeyUpload` | Managed constraint disabling external public key uploads to service accounts. |
| `iam.disableServiceAccountCreation` | Explicit baseline entry set to `enforce: false` so Terraform can create dedicated workload service accounts. |
| `iam.managed.preventPrivilegedBasicRolesForDefaultServiceAccounts` | Managed constraint blocking privileged basic roles on default service accounts. |
| `iam.automaticIamGrantsForDefaultServiceAccounts` | Prevents automatic Editor role grants on default service accounts. |
| `iam.serviceAccountKeyExposureResponse` | Sets `DISABLE_KEY` to disable exposed service account keys automatically. |
| `iam.allowedPolicyMemberDomains` | Restricts IAM policy principals to the customer ID and configured `allowed_domains`. |
| `compute.requireOsLogin` | Enforces OS Login across Compute Engine VMs; skipped when `regime` is `IL4` or `IL5`. |
| `essentialcontacts.managed.allowedContactDomains` | Managed constraint restricting Essential Contacts notifications to `@<domain_name>`. |
| `essentialcontacts.allowedContactDomains` | Restricts Essential Contacts addresses to `@<domain_name>`. |
| `essentialcontacts.disableProjectSecurityContacts` | Explicit baseline entry set to `enforce: false` so project security contacts remain configurable when needed. |

#### Serverless security

| Constraint | Enforcement |
| :--- | :--- |
| `cloudfunctions.allowedIngressSettings` | Sets `ALLOW_INTERNAL_AND_GCLB` to restrict Cloud Functions ingress. |
| `cloudfunctions.allowedVpcConnectorEgressSettings` | Sets `ALL_TRAFFIC` to route Cloud Functions VPC connector egress through the VPC. |
| `cloudfunctions.requireVPCConnector` | Explicit baseline entry set to `enforce: false` unless a deployment requires VPC connectors on all functions. |
| `run.allowedBinaryAuthorizationPolicies` | Restricts Cloud Run Binary Authorization policies to `default`. |
| `run.allowedIngress` | Sets `is:internal-and-cloud-load-balancing` to restrict Cloud Run ingress. |
| `run.allowedVPCEgress` | Sets `allow: all: true` so both `private-ranges-only` and `all-traffic` VPC egress modes remain permitted unless tightened. |
| `cloudbuild.allowedIntegrations` | Restricts Cloud Build external repository integrations to `github.com`. |
| `cloudscheduler.allowedTargetTypes` | Sets `allow: all: true` across supported Cloud Scheduler target types. |

#### Resource management and logging

| Constraint | Enforcement |
| :--- | :--- |
| `resourcemanager.allowedImportSources` | Restricts project imports to `under:organizations/<org_id>`. |
| `resourcemanager.allowedExportDestinations` | Restricts project exports to `under:organizations/<org_id>`. |
| `resourcemanager.accessBoundaries` | Organization-only constraint restricting Cloud Console visibility boundaries to `under:organizations/<org_id>`. |
| `gcp.detailedAuditLoggingMode` | Enables detailed Cloud Storage request and response audit logging. |
| `gcp.disableCloudLogging` | Explicit baseline entry set to `enforce: false` so Cloud Logging remains enabled for Healthcare API workloads. |

#### Optional guardrail policy packs

Additional opt-in organization policy bundles under `fast/assets/org-policy-packs/` provide `compute-data-managed`, `custom-constraints-dry-run`, and `gke-managed` rule packs for staged dry-run validation and stricter workload hardening. See the [Guardrails rubric and test plan](guardrails-rubric-and-test-plan.md) for adoption guidance.

#### Folder hierarchy

Stage `0-bootstrap` and Stage `1-resman` construct the landing zone folder hierarchy directly under the organization root:

- `StellarEngine-<prefix>` serves as the top-level Assured Workloads enclave folder provisioned in Stage `0-bootstrap`, with `module.no-compliance-folder` providing the same display name when `regime` is `COMPLIANCE_REGIME_UNSPECIFIED`.
- `<RegimeCode> Common Services` sits directly inside `StellarEngine-<prefix>` and contains Stage 0 core projects (`<prefix>-prod-iac-core-0`, `<prefix>-prod-audit-logs-0`, and optional `<prefix>-prod-billing-exp-0`) alongside two Stage `1-resman` child folders:
  - `Networking` hosts centralized Shared VPC host projects such as `<prefix>-net-hub-host` or `<prefix>-net-vdss-host` plus environment networking subfolders and projects.
  - `Security` hosts optional Stage 3 security core projects (`<prefix>-dev-sec-core-0` and `<prefix>-prod-sec-core-0`).
- Environment folders named `<RegimeCode> <Env>` such as `IL5 Prod` and `IL5 Dev` sit directly under the Assured Workloads root folder when configured through `1-resman/branch-envs.tf`.
- Tenant folders named `Project <tenant> <env>` sit inside each `<RegimeCode> <Env>` folder via `1-resman/branch-tenants.tf` and directly hold each tenant's self-service IaC project `<prefix>-<env>-<tenant>-iac-core-0` and workload projects without intermediate Core or Self child folders.
- Optional feature folders enabled via `fast_features` (`Data Platform`, `GKE`, `GCVE`, `Project Factory`, `Sandbox`, and `Teams`) also deploy under the root boundary when enabled.

#### Example organization layout

The hierarchy below illustrates an `IL5` organization layout produced by Stage 0 and Stage 1:

```text
Organization Root
└── StellarEngine-<prefix> (Assured Workloads root folder)
    ├── IL5 Common Services
    │   ├── <prefix>-prod-iac-core-0
    │   ├── <prefix>-prod-audit-logs-0
    │   ├── <prefix>-prod-billing-exp-0 (optional, when org billing mode applies)
    │   ├── Networking
    │   │   ├── <prefix>-net-vdss-host (or <prefix>-net-hub-host in Stage 2a)
    │   │   ├── Prod
    │   │   │   └── <prefix>-prod-net-host
    │   │   └── Dev
    │   │       └── <prefix>-dev-net-host
    │   └── Security
    │       ├── <prefix>-prod-sec-core-0
    │       └── <prefix>-dev-sec-core-0
    ├── IL5 Prod
    │   └── Project ten-1 prod
    │       ├── <prefix>-prod-ten-1-iac-core-0
    │       └── Workload Projects
    └── IL5 Dev
        └── Project ten-1 dev
            ├── <prefix>-dev-ten-1-iac-core-0
            └── Workload Projects
```

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
- Stage `0-bootstrap` maps `var.groups` to organization identity groups such as `gcp-organization-admins@example.com`, `gcp-security-admins@example.com`, `gcp-vpc-network-admins@example.com`, `gcp-billing-admins@example.com`, and `gcp-devops@example.com` (with `gcp-support` defaulting to `gcp-devops`), while Stage `1-resman` tenant entries bind per-tenant `admin_principal` groups.
- Your enterprise identity provider or Google Cloud Identity manages ongoing group membership lifecycle, while Terraform manages the IAM role bindings on folders and projects.

##### Initial role groups

The six group keys defined in `fast/stages-aw/0-bootstrap/variables.tf` receive the following organization-level roles in `0-bootstrap/organization-iam.tf` and `0-bootstrap/billing.tf` (`+` denotes additive bindings):

| Role group | Description | Assigned roles at organization level |
| :--- | :--- | :--- |
| `gcp-organization-admins` | Administers organization structure, Assured Workloads enclaves, and identity pools. | `roles/axt.admin`, `roles/cloudasset.owner`, `roles/cloudsupport.admin`, `roles/resourcemanager.folderAdmin`, `roles/resourcemanager.organizationAdmin`, `roles/resourcemanager.projectCreator`, `roles/resourcemanager.tagAdmin`, `roles/iam.workforcePoolAdmin`, `roles/assuredworkloads.admin`, `roles/orgpolicy.policyAdmin` `+`, `roles/iam.organizationRoleAdmin` `+`, and `roles/billing.admin` `+` when billing is organization-scoped |
| `gcp-billing-admins` | Administers Cloud Billing accounts and billing export visibility. | `roles/billing.admin` `+` when billing is organization-scoped, or billing-resource bindings in `0-bootstrap/billing.tf`; `roles/billing.creator` is explicitly removed via `iam_delete_roles` |
| `gcp-vpc-network-admins` | Creates and governs Shared VPC host projects, networks, firewalls, and connectivity. | `roles/cloudasset.owner`, `roles/cloudsupport.techSupportEditor`, `roles/compute.orgFirewallPolicyAdmin` `+`, and `roles/compute.xpnAdmin` `+` |
| `gcp-security-admins` | Establishes and audits security policies, logging, Security Command Center, and VPC-SC perimeters. | `roles/cloudasset.owner`, `roles/cloudsupport.techSupportEditor`, `roles/iam.securityReviewer`, `roles/logging.admin`, `roles/securitycenter.admin`, `roles/accesscontextmanager.policyAdmin` `+`, `roles/iam.organizationRoleAdmin` `+`, and `roles/orgpolicy.policyAdmin` `+` |
| `gcp-support` | Provides read-only observability and technical support escalation; defaults to `gcp-devops`. | `roles/cloudsupport.techSupportEditor`, `roles/logging.viewer`, and `roles/monitoring.viewer` |
| `gcp-devops` | Operates CI/CD automation and impersonates stage service accounts. | Inherits `gcp-support` organization roles by default, plus `roles/iam.serviceAccountAdmin` and `roles/iam.serviceAccountTokenCreator` on `<prefix>-prod-iac-core-0` |

##### Role group mappings

Stellar Engine also grants `domain:<organization_domain>` the `roles/browser` role at the organization level and supplements organization bindings with stage-specific folder and project access:

| Group | Scope and operational role |
| :--- | :--- |
| `gcp-organization-admins` | Organization administration, plus `roles/iam.serviceAccountTokenCreator` and `roles/iam.workloadIdentityPoolAdmin` on `<prefix>-prod-iac-core-0` and owner access on `<prefix>-prod-billing-exp-0`. |
| `gcp-billing-admins` | Billing administration across organization or linked billing accounts and billing export datasets in `<prefix>-prod-billing-exp-0`. |
| `gcp-vpc-network-admins` | Organization-wide network firewall policy and Shared VPC admin roles, plus `roles/editor` on the Stage `1-resman` `Networking` folder. |
| `gcp-security-admins` | Organization security audit, policy, Access Context Manager, and Security Command Center admin roles, plus `roles/editor` on the Stage `1-resman` `Security` folder. |
| `gcp-devops` | Technical support, logging viewer, and monitoring viewer across the organization via `gcp-support`, plus service account impersonation and administration inside `<prefix>-prod-iac-core-0`. |
| `gcp-support` | Dedicated read-only support and observability group when separated from `gcp-devops`. |

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

An administrator executes Stage 0 bootstrap using an individual Google Cloud user account in `gcp-organization-admins` or by impersonating a temporary bootstrap account before service account lockdown.

To run the bootstrap phase at the organization root, grant these roles outside Terraform beforehand:

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

Stage 0 and Stage 1 service account and group bindings follow the [Stage 0 IAM reference](../fast/stages-aw/0-bootstrap/IAM.md) and [Stage 1 IAM reference](../fast/stages-aw/1-resman/IAM.md). In Stage `1-resman`, additive bindings (`+`) and conditional bindings (`•`) keep automation privileges scoped to their target branches:

##### Organization node

| Member | Roles |
| :--- | :--- |
| `<prefix>-dev-resman-pf-0` (`serviceAccount`) | [roles/orgpolicy.policyAdmin](https://cloud.google.com/iam/docs/understanding-roles#orgpolicy.policyAdmin) `+` `•` |
| `<prefix>-prod-resman-net-0` (`serviceAccount`) | [roles/compute.orgFirewallPolicyAdmin](https://cloud.google.com/iam/docs/understanding-roles#compute.orgFirewallPolicyAdmin) `+`, [roles/compute.xpnAdmin](https://cloud.google.com/iam/docs/understanding-roles#compute.xpnAdmin) `+` |
| `<prefix>-prod-resman-pf-0` (`serviceAccount`) | [roles/orgpolicy.policyAdmin](https://cloud.google.com/iam/docs/understanding-roles#orgpolicy.policyAdmin) `+` `•` |
| `<prefix>-security-0` (`serviceAccount`) | [roles/accesscontextmanager.policyAdmin](https://cloud.google.com/iam/docs/understanding-roles#accesscontextmanager.policyAdmin) `+` |

##### Data platform folders

When `fast_features.data_platform` is enabled, `1-resman` creates `Data Platform/Development` and `Data Platform/Production` folders with `dev-resman-dp-0` and `prod-resman-dp-0` holding `organizations/<org_id>/roles/serviceProjectNetworkAdmin`, `roles/logging.admin`, `roles/owner`, `roles/resourcemanager.folderAdmin`, and `roles/resourcemanager.projectCreator`, while `dev-resman-dp-0r` and `prod-resman-dp-0r` receive `roles/resourcemanager.folderViewer` and `roles/viewer`.

##### GKE folders

When `fast_features.gke` is enabled, `1-resman` creates `GKE/Development` and `GKE/Production` folders with `dev-resman-gke-0` and `prod-resman-gke-0` holding `roles/compute.xpnAdmin`, `roles/logging.admin`, `roles/owner`, `roles/resourcemanager.folderAdmin`, and `roles/resourcemanager.projectCreator`, while `dev-resman-gke-0r` and `prod-resman-gke-0r` receive `roles/resourcemanager.folderViewer` and `roles/viewer`.

##### Networking folder

| Member | Roles |
| :--- | :--- |
| `gcp-vpc-network-admins` (`group`) | [roles/editor](https://cloud.google.com/iam/docs/understanding-roles#editor) |
| `<prefix>-prod-resman-net-0` (`serviceAccount`) | [roles/compute.xpnAdmin](https://cloud.google.com/iam/docs/understanding-roles#compute.xpnAdmin), [roles/logging.admin](https://cloud.google.com/iam/docs/understanding-roles#logging.admin), [roles/owner](https://cloud.google.com/iam/docs/understanding-roles#owner), [roles/resourcemanager.folderAdmin](https://cloud.google.com/iam/docs/understanding-roles#resourcemanager.folderAdmin), [roles/resourcemanager.projectCreator](https://cloud.google.com/iam/docs/understanding-roles#resourcemanager.projectCreator) |
| `<prefix>-prod-resman-net-0r` (`serviceAccount`) | [roles/resourcemanager.folderViewer](https://cloud.google.com/iam/docs/understanding-roles#resourcemanager.folderViewer), [roles/viewer](https://cloud.google.com/iam/docs/understanding-roles#viewer) |

##### Networking development folder

| Member | Roles |
| :--- | :--- |
| `<prefix>-dev-resman-dp-0` (`serviceAccount`) | `organizations/<org_id>/roles/serviceProjectNetworkAdmin` |
| `<prefix>-dev-resman-gke-0` (`serviceAccount`) | `organizations/<org_id>/roles/serviceProjectNetworkAdmin` |
| `<prefix>-dev-resman-pf-0` (`serviceAccount`) | `organizations/<org_id>/roles/serviceProjectNetworkAdmin` |
| `<prefix>-prod-resman-dp-0r` (`serviceAccount`) | [roles/compute.networkViewer](https://cloud.google.com/iam/docs/understanding-roles#compute.networkViewer) |
| `<prefix>-prod-resman-gke-0r` (`serviceAccount`) | [roles/compute.networkViewer](https://cloud.google.com/iam/docs/understanding-roles#compute.networkViewer) |
| `<prefix>-prod-resman-pf-0r` (`serviceAccount`) | [roles/compute.networkViewer](https://cloud.google.com/iam/docs/understanding-roles#compute.networkViewer) |

##### Networking production folder

| Member | Roles |
| :--- | :--- |
| `<prefix>-prod-resman-dp-0` (`serviceAccount`) | `organizations/<org_id>/roles/serviceProjectNetworkAdmin` |
| `<prefix>-prod-resman-dp-0r` (`serviceAccount`) | [roles/compute.networkViewer](https://cloud.google.com/iam/docs/understanding-roles#compute.networkViewer) |
| `<prefix>-prod-resman-gke-0` (`serviceAccount`) | `organizations/<org_id>/roles/serviceProjectNetworkAdmin` |
| `<prefix>-prod-resman-gke-0r` (`serviceAccount`) | [roles/compute.networkViewer](https://cloud.google.com/iam/docs/understanding-roles#compute.networkViewer) |
| `<prefix>-prod-resman-pf-0` (`serviceAccount`) | `organizations/<org_id>/roles/serviceProjectNetworkAdmin` |
| `<prefix>-prod-resman-pf-0r` (`serviceAccount`) | [roles/compute.networkViewer](https://cloud.google.com/iam/docs/understanding-roles#compute.networkViewer) |

##### Security folder

| Member | Roles |
| :--- | :--- |
| `gcp-security-admins` (`group`) | [roles/editor](https://cloud.google.com/iam/docs/understanding-roles#editor) |
| `<prefix>-security-0` (`serviceAccount`) | [roles/logging.admin](https://cloud.google.com/iam/docs/understanding-roles#logging.admin), [roles/owner](https://cloud.google.com/iam/docs/understanding-roles#owner), [roles/resourcemanager.folderAdmin](https://cloud.google.com/iam/docs/understanding-roles#resourcemanager.folderAdmin), [roles/resourcemanager.projectCreator](https://cloud.google.com/iam/docs/understanding-roles#resourcemanager.projectCreator) |
| `<prefix>-prod-resman-sec-0r` (`serviceAccount`) | [roles/resourcemanager.folderViewer](https://cloud.google.com/iam/docs/understanding-roles#resourcemanager.folderViewer), [roles/viewer](https://cloud.google.com/iam/docs/understanding-roles#viewer) |

##### Teams and sandbox folders

When enabled via `fast_features`, `dev-resman-sbox-0`, `prod-resman-teams-0`, `prod-teams-<name>-0`, and `dev-resman-pf-0` / `prod-resman-pf-0` hold folder-scoped `roles/logging.admin`, `roles/owner`, `roles/resourcemanager.folderAdmin`, and `roles/resourcemanager.projectCreator` on their respective branches, while tenant Stage 1 service accounts `tn-<env>-<tenant>-prod-0` govern `Project <tenant> <env>`. See the [Stage 1 IAM reference](../fast/stages-aw/1-resman/IAM.md) for the complete table.

##### Core automation project

On `<prefix>-prod-iac-core-0`, apply and read-only service accounts (`dev-resman-dp-0`/`0r`, `dev-resman-gke-0`/`0r`, `dev-resman-pf-0`/`0r`, `dev-resman-sbox-0`, `prod-resman-dp-0r`, `prod-resman-gke-0`/`0r`, `prod-resman-net-0`/`0r`, `prod-resman-pf-0`/`0r`, `prod-resman-sec-0r`, `prod-resman-teams-0`, `security-0`, and `tn-<env>-<tenant>-prod-0`) receive additive `roles/serviceusage.serviceUsageConsumer`, while CI/CD accounts (`prod-resman-net-1`/`1r` and `prod-resman-sec-1`/`1r`) receive additive `roles/logging.logWriter`. Stage-specific state bucket and token-creator permissions are generated alongside the [Stage 0 IAM reference](../fast/stages-aw/0-bootstrap/IAM.md) and [Stage 1 IAM reference](../fast/stages-aw/1-resman/IAM.md).

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

Foundational bootstrap and landing zone stages live under `fast/stages-aw`, optional organization policy guardrail bundles live under `fast/assets/org-policy-packs`, reusable service modules live under `modules` with 101 module subdirectories aligned to Cloud Foundation Fabric v60.0.0, and compliance-scoped workload compositions live under `blueprints`. Under `blueprints`, 15 shared workload blueprints reside canonically under `blueprints/il5/` alongside `bigquery`, while matching Git `120000` directory symlinks expose those 15 blueprints under `blueprints/fedramp-high/` alongside standalone FedRAMP High, Gemini Enterprise, stand-alone, and third-party blueprints:

```text
blueprints/
  fedramp-high/
    access-context-manager
    app-engine
    artifact-registry -> ../il5/artifact-registry
    bastion-pattern -> ../il5/bastion-pattern
    bcap -> ../il5/bcap
    beyondcorp
    bigtable
    bq-project -> ../il5/bq-project
    cloud-armor
    cloud-composer-environment
    cloud-functions
    cloud-ids
    cloud-run
    cloud-scheduler-job
    cloud-spanner
    cloud-translation
    cloud-workstations
    cnap
    compute-engine -> ../il5/compute-engine
    dataflow -> ../il5/dataflow
    datafusion
    dataproc-cluster
    datastore
    document-ai
    firestore
    gcs-project -> ../il5/gcs-project
    gitlab
    gke -> ../il5/gke
    gke-hardened -> ../il5/gke-hardened
    ha-vpn-multicloud -> ../il5/ha-vpn-multicloud
    kms-project -> ../il5/kms-project
    network-connectivity-center
    postgresql -> ../il5/postgresql
    private-service-connect -> ../il5/private-service-connect
    pub-sub-project -> ../il5/pub-sub-project
    secret-manager
    shielded-vm-project -> ../il5/shielded-vm-project
    vertex-mlops
    workflows
  gemini-enterprise/
    analytics
    deploy.sh
    gem4gov-cli
    gemini-stage-0
    gemini-stage-1
  il5/
    artifact-registry
    bastion-pattern
    bcap
    bigquery
    bq-project
    compute-engine
    dataflow
    gcs-project
    gke
    gke-hardened
    ha-vpn-multicloud
    kms-project
    postgresql
    private-service-connect
    pub-sub-project
    shielded-vm-project
  stand-alone/
    vpc-peering-project
  third-party-solutions/
    gitlab
fast/
  assets/
    org-policy-packs/
      compute-data-managed
      custom-constraints-dry-run
      gke-managed
  stages-aw/
    0-bootstrap
    1-resman
    2-networking-a-fedramp
    2-networking-b-il5-ngfw
    3-security
modules/
  access-context-manager      data-catalog-policy-tag     net-cloudnat
  alloydb                     data-catalog-tag            net-firewall-policy
  analytics-hub               data-catalog-tag-template   net-ipsec-over-interconnect
  api-gateway                 dataform-repository         net-lb-app-ext
  apigee                      datafusion                  net-lb-app-ext-regional
  app-engine                  datafusion-se               net-lb-app-int
  artifact-registry           dataplex                    net-lb-app-int-cross-region
  backup-dr                   dataplex-aspect-types       net-lb-ext
  beyondcorp                  dataplex-datascan           net-lb-int
  biglake-catalog             dataproc                    net-lb-proxy-int
  bigquery-connection         dns                         net-lb-proxy-int-cross-region
  bigquery-dataset            dns-response-policy         net-swp
  bigtable-instance           endpoints                   net-vlan-attachment
  billing-account             firestore                   net-vpc
  binauthz                    folder                      net-vpc-firewall
  certificate-authority-service  gcs                      net-vpc-peering
  certificate-manager         gcve-private-cloud          net-vpn-dynamic
  cis-log-alerts              geap-agent-gateway          net-vpn-ha
  cis-log-metrics             geap-agent-runtime          net-vpn-static
  cloud-build-v2-connection   geap-workbench              organization
  cloud-config-container      gke-cluster-autopilot       organization-se
  cloud-deploy                gke-cluster-standard        private-service-connect
  cloud-function-v1           gke-cluster-standard-se     project
  cloud-function-v2           gke-hub                     project-factory
  cloud-identity-group        gke-nodepool                projects-data-source
  cloud-run-v2                iam-service-account         pubsub
  cloud-scheduler             intrusion-detection-system  secops-rules
  cloudsql-instance           kms                         secret-manager
  compute-mig                 logging-bucket              secure-source-manager-instance
  compute-vm                  looker-core                 service-directory
  container-registry          managed-kafka               source-repository
  ncc-spoke-ra                net-address                 spanner-instance
  net-cloud-armor             spanner-instance-se         vpc-sc
  workflows                   workstation-cluster
```

### 3.5 Terraform design principles

#### Environment partitioning

Terraform configurations partition infrastructure into standalone, per-environment root modules, allowing additional customer tenants to onboard per environment. Keeping each tenant-and-environment configuration explicit and local-driven minimizes blast radius so changes in one tenant or environment do not affect another.

Example configuration from `fast/stages-aw/1-resman`:

```hcl
locals {
  tenant_envs = merge([for e, _ in var.envs_folders : {
    for t, v in var.tenants : "${e}-${t}" => {
      env         = e
      tenant      = t
      tenant_info = v
    }
  }]...)
}

module "branch-envs-folders" {
  source       = "../../../modules/folder"
  for_each     = var.envs_folders
  parent       = var.assured_workloads.folder
  name         = "${lookup(var.regime_mapping, var.assured_workloads.regime, var.assured_workloads.regime)} ${each.key}"
  iam          = local._envs_folder_iam
  tag_bindings = null
}

module "tenant-top-folders" {
  source   = "../../../modules/folder"
  for_each = local.tenant_envs
  parent   = module.branch-envs-folders[each.value.env].id
  name     = "Project ${each.value.tenant} ${each.value.env}"
}
```

### 3.6 Networking

See the [Google Cloud security foundations networking guide](https://cloud.google.com/architecture/security-foundations/networking) for foundational enterprise network patterns.

#### Shared VPC topology

Google Cloud connects Virtual Private Clouds privately across Google's backbone using Network Connectivity Center, VPC Network Peering, and [Shared VPC](https://cloud.google.com/vpc/docs/shared-vpc). Centralizing Shared VPC subnets, routes, and firewall policies in dedicated host projects simplifies network governance while allowing service project teams to deploy and manage workload resources independently.

Resources attached to Shared VPC networks communicate across project boundaries over internal IP addresses. Managing shared network constructs such as subnets, routes, and firewalls from central host projects enforces consistent network security policies across attached service projects.

In the Stage 2 reference topologies, each deployment uses a single unified Shared VPC tier per hub and environment rather than separate `base` and `restricted` Shared VPC tiers:

- Stage `2-networking-a-fedramp` provisions a central `hub-0` Shared VPC in `<prefix>-net-hub-host`, an optional `egress-0` Secure Web Proxy VPC, and environment `<env>-spoke-0` Shared VPCs in `<prefix>-<env>-net-host` projects connected via Network Connectivity Center `STAR` groups.
- Stage `2-networking-b-il5-ngfw` provisions a three-VPC Virtual Datacenter Security Stack (`Landing`, `DMZ`, and `Mgmt`) in `<prefix>-net-vdss-host` peered through inline VM-Series Next-Generation Firewalls to environment `<env>-spoke-0` Shared VPCs.
- When [VPC Service Controls](https://cloud.google.com/vpc-service-controls) is enabled in Stage `3-security`, perimeters protect designated projects and APIs across those Shared VPC environments without maintaining duplicate network tiers.

#### Virtual Private Clouds

A VPC provides an isolated virtual network for Google Cloud resources with customizable IP address ranges, regional subnets, and routing tables. Evaluate your organization's segmentation requirements before allocating VPC boundaries across tenants.

VPC Network Peering connects VPC networks within the same project or across separate projects over internal IP addresses without external gateways or public internet traversal, keeping inter-VPC traffic entirely on Google's private network backbone.

#### Subnet allocations

Subnet allocation divides a VPC primary CIDR block into regional IP segments for Compute Engine VMs, Google Kubernetes Engine clusters, and managed services. The reference subnet allocation scheme partitions a `/16` address space across up to eight `/19` blocks for tenants and up to eight `/23` project blocks per tenant.

The table below shows the four `/25` subnet allocations inside Project 1's `10.200.2.0/23` CIDR block, totaling 512 addresses:

| Subnet Address | Range of Addresses | Useable IPs | Hosts |
| :--- | :--- | :--- | :--- |
| `10.200.2.0/25` | `10.200.2.0 - 10.200.2.127` | `10.200.2.1 - 10.200.2.126` | 126 |
| `10.200.2.128/25` | `10.200.2.128 - 10.200.2.255` | `10.200.2.129 - 10.200.2.254` | 126 |
| `10.200.3.0/25` | `10.200.3.0 - 10.200.3.127` | `10.200.3.1 - 10.200.3.126` | 126 |
| `10.200.3.128/25` | `10.200.3.128 - 10.200.3.255` | `10.200.3.129 - 10.200.3.254` | 126 |

Subnets are logical partitions within a VPC that define IP address ranges for resources deployed in specific regions. Allocate separate subnets per application tier and configure Google Kubernetes Engine clusters with dedicated secondary ranges for pods and services. Define subnet CIDR ranges in the Stage 2 networking configuration as non-overlapping subsets of each VPC address block.

The table below shows an aligned CIDR allocation across the organization, tenant, and project tiers inside `10.200.0.0/16`:

| Component | CIDR | Notes |
| :--- | :--- | :--- |
| Organization (all tenants) | `10.200.0.0/16` | Eight `/19` blocks for tenants |
| Tenant 1 | `10.200.0.0/19` | Covers `10.200.0.0` through `10.200.31.255`; reserves `10.200.0.0/23` for shared hub/infra services |
| Project 1 | `10.200.2.0/23` | First workload `/23` block (`10.200.2.0 - 10.200.3.255`) |
| Project 2 | `10.200.4.0/23` | Second workload `/23` block (`10.200.4.0 - 10.200.5.255`) |
| Project 3 | `10.200.6.0/23` | Third workload `/23` block (`10.200.6.0 - 10.200.7.255`) |
| Project 4 | `10.200.8.0/23` | Fourth workload `/23` block (`10.200.8.0 - 10.200.9.255`) |
| Project 5 | `10.200.10.0/23` | Fifth workload `/23` block (`10.200.10.0 - 10.200.11.255`) |

Use the hierarchy above when allocating non-overlapping CIDRs for new projects within the `10.200.0.0/16` tenant range.

#### Private Google Access

Route traffic from VPC workloads to Google-managed APIs such as App Engine, Cloud SQL, and Cloud Functions over internal IP space using [Private Google Access](https://cloud.google.com/vpc/docs/private-google-access), which Stellar Engine enables across managed subnets. Route traffic from serverless Google-managed environments back into your VPC over internal IP space using [Serverless VPC Access](https://cloud.google.com/vpc/docs/serverless-vpc-access).

#### Inter-service communication

Route synchronous microservice-to-microservice traffic inside the VPC through [Internal Application Load Balancing](https://cloud.google.com/load-balancing/docs/l7-internal) or [Private Google Access](https://cloud.google.com/vpc/docs/private-google-access), and decouple asynchronous service messaging with [Cloud Pub/Sub](https://cloud.google.com/pubsub).

#### VPC firewall rules

By default, VPC networks deny all unsolicited ingress traffic and allow egress traffic unless overridden. Define firewall policies and rules in `fast/stages-aw/2-networking-a-fedramp` (which attaches the folder hierarchical firewall policy `<prefix>-net-default` and global network firewall policies such as `<prefix>-hub-fw-policy-0` and `<prefix>-<env>-fw-policy-0` with `BEFORE_CLASSIC_FIREWALL` precedence) or in `fast/stages-aw/2-networking-b-il5-ngfw`. Google Cloud firewall rules are stateful and evaluate in numeric priority order: the highest-priority rule matching source IP, destination IP, protocol, and port governs the flow, and lower-priority rules are skipped.

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

Google Cloud Assured Workloads enforces compliance guardrails across regulated folders. In `fast/stages-aw/0-bootstrap/variables.tf`, `var.assured_workloads` defaults to `regime = "IL5"` and `location = "US"` on the `StellarEngine-<prefix>` root folder so child folders and projects inherit the selected compliance constraints automatically. Supported `regime` values include `IL4`, `IL5`, `FEDRAMP_HIGH`, `FEDRAMP_MODERATE`, and `COMPLIANCE_REGIME_UNSPECIFIED` when deploying without an Assured Workloads enclave.

When you provision an Assured Workloads environment, Assured Workloads enforces baseline compliance controls and `constraints/gcp.resourceLocations` boundaries to keep data at rest within authorized regions.

Define tenant entries in the `1-resman` `terraform.tfvars` file under `var.tenants`. Tenant map keys must be strictly fewer than 7 characters, such as `ten-1`:

```hcl
tenants = {
  ten-1 = {
    admin_principal  = "group:gcp-ten-1-admins@example.com"
    descriptive_name = "ten-1"
    locations = {
      gcs = "us-east4"
      kms = "us-east4"
    }
  }
}
```

Although `var.tenants` includes an optional `compliance` attribute on the variable type in `fast/stages-aw/1-resman/variables.tf`, `fast/stages-aw/1-resman/branch-tenants.tf` does not provision per-tenant Assured Workloads folders from `tenants[*].compliance`. All tenant folders inherit the single Assured Workloads enclave created in `0-bootstrap`, so separate compliance regimes require separate landing zone deployments. See the [Terraform Assured Workloads documentation](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/assured_workloads_workload#compliance_regime) for supported compliance regimes.

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
- Enforce `constraints/storage.uniformBucketLevelAccess` (`true`) across all projects so Cloud IAM governs bucket and object permissions uniformly and legacy fine-grained object ACLs remain disabled.
- Enforce `constraints/storage.publicAccessPrevention` (`true`) and `constraints/iam.allowedPolicyMemberDomains` so buckets and objects never permit `allUsers` or `allAuthenticatedUsers` read or write access.
- Enforce `constraints/storage.secureHttpTransport` (`true`) to require HTTPS transport for every Cloud Storage request, and apply CMEK keys where mandated by the workload regime.
- Issue [signed URLs](https://cloud.google.com/storage/docs/access-control/signed-urls) with explicit read or write scope and short expiration windows only where approved temporary external access is required outside restricted buckets.

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

Stage `0-bootstrap` defines four organization log sinks (`audit-logs`, `vpc-sc`, `workspace-audit-logs`, and `empty-audit-logs`) in `var.log_sinks` that route audit and VPC Service Controls logs by default into dedicated Cloud Logging buckets inside `<prefix>-prod-audit-logs-0` (`logging_bucket_retention = 365` days) protected by CMEK. Where long-term archival beyond 365 days or external SIEM forwarding is required, configure additional sinks targeting Cloud Storage, BigQuery, or Pub/Sub via `var.log_sinks`.

When routing logs to a destination in another project, grant destination write permissions to the log sink writer identity service account, and authorize that writer identity in VPC Service Controls perimeters protecting the destination project (`fast-org-log-sinks` in `fast/stages-aw/3-security/vpc-sc.tf` provisions this automatically when `logging` is wired).

### 5.4 Monitoring

#### Host projects

Shared VPC monitoring metrics scopes and CIS security alerting span distinct host projects:

| Scope | Project | Purpose |
| :--- | :--- | :--- |
| Network metrics scope | `<prefix>-net-hub-host` or `<prefix>-net-vdss-host` | Receives `metric_scopes` bindings from Stage 2 environment network host projects (`<prefix>-<env>-net-host`) for unified network telemetry. |
| Security alerting | `<prefix>-dev-sec-core-0` and `<prefix>-prod-sec-core-0` | Hosts Stage `3-security` CIS log-based metrics (`modules/cis-log-metrics`) and alerting policies (`modules/cis-log-alerts`), complementing organization audit alerts in `<prefix>-prod-audit-logs-0`. |

#### Monitoring groups

Stage `0-bootstrap` configures the `gcp-support` role group (defaulting to `gcp-devops` in `var.groups`) with organization-level `roles/monitoring.viewer` and `roles/logging.viewer` visibility, while operations and security teams manage project-scoped alerting channels and dashboards.

#### Alerting policies

Configure Cloud Monitoring alerting policies on events and log-based metrics to specify trigger conditions and notification channels so operations teams detect and resolve service issues rapidly.

#### Dashboards

Cloud Monitoring installs default service dashboards automatically when you provision Google Cloud resources, and you can deploy custom dashboards to correlate metrics, alerting policies, and log entries from multiple services in a single view.

### 5.5 Security boundaries

In the reference boundary architecture, the authorization boundary encompasses the Assured Workloads folder hierarchy, shared networking and security host projects, and attached tenant service projects.

#### Organization policy inheritance

Child folders and projects inherit parent organization policies according to `inheritFromParent`. Setting `inheritFromParent = true` merges and reconciles the parent node's effective policy with local rules, whereas setting `inheritFromParent = false` reverts to the constraint's default behavior unless explicit allow or deny rules are defined on the child node.

#### Project layout and VPC Service Controls

Terraform manages cross-project IAM bindings declaratively across the folder and project hierarchy described in section 3.1. VPC Service Controls enforcement is opt-in through Stage `3-security` (`fast/stages-aw/3-security/vpc-sc.tf`) when `var.vpc_sc.perimeter_default` is configured, rather than provisioning an automatic perimeter on a separate restricted Shared VPC tier.

When enabled, `3-security/vpc-sc.tf` configures an Access Context Manager policy (`access_policy_create`), builds a default perimeter enclosing explicit `resources` plus optional automated project discovery (`resource_discovery`), restricts services listed in `data/vpc-sc/restricted-services.yaml`, attaches `fast-org-log-sinks` for centralized audit log ingestion, and supports validating rule updates via `dry_run_spec` alongside the enforced `status` block (`dry_run = true` clears `status = null`).

VPC Service Controls mitigates data exfiltration risks by wrapping protected Google Cloud services inside security perimeters that block unauthorized data egress even when an attacker holds valid user or service account credentials. Combine VPC Service Controls with Access Context Manager access levels and Context-Aware Access policies to enforce IP-range and device-trust checks on requests originating outside trusted corporate networks.

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
- Scans Cloud Storage buckets and logs for sensitive PII using Sensitive Data Protection (Cloud DLP); verify [Cloud DLP regional availability](https://cloud.google.com/dlp/docs/locations) and regulatory data residency requirements before scanning.
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

Each VPC network enforces a distributed, stateful virtual firewall at the host network layer across Compute Engine VMs and GKE clusters independently of guest operating systems, allowing return traffic automatically for permitted flows. In Stage `2-networking-a-fedramp`, Shared VPC networks set `network_firewall_policy_enforcement_order = "BEFORE_CLASSIC_FIREWALL"` so folder hierarchical firewall policy `<prefix>-net-default` on `Networking` and global network firewall policies (`<prefix>-hub-fw-policy-0`, `<prefix>-<env>-fw-policy-0`, and `<prefix>-egress-fw-policy-0`) created via `modules/net-firewall-policy` evaluate before classic VPC firewall rules. Stage `0-bootstrap` also enforces `custom.restrictFirewallRanges` to block ingress allow rules matching `0.0.0.0/0` or `::/0`.

Firewall policies and rules match traffic by protocol, port, direction, CIDR ranges, address groups, Secure Tags (`target_secure_tags`), or dedicated service accounts (`target_service_accounts`). Because firewall rules and policies carry deterministic Terraform identifiers, adopt a consistent naming convention before provisioning.

Every VPC network includes two built-in implied firewall rules at priority `65535`:

- The implied allow egress rule (`ALLOW`, destination `0.0.0.0/0`, priority `65535`) permits outbound traffic from any instance except traffic [blocked by Google Cloud](https://cloud.google.com/vpc/docs/firewalls#blockedtraffic), unless a higher-priority rule restricts egress.
- The implied deny ingress rule (`DENY`, source `0.0.0.0/0`, priority `65535`) blocks unsolicited inbound connections to all instances unless a higher-priority rule explicitly allows ingress.

You cannot delete the implied rules, so override them with explicit rules at higher priorities (`0` through `65534` for classic rules, or lower numeric priorities inside network firewall policies).

Enable Firewall Rules Logging individually on each allow or deny rule whose traffic you need to audit. When enabled, Google Cloud writes a connection record containing source and destination IP addresses, protocol, ports, timestamp, and matched rule reference to Cloud Logging for viewing or export; see [Using Firewall Rules Logging](https://cloud.google.com/vpc/docs/using-firewall-rules-logging) for details.

Alongside VPC-level firewall rules and network firewall policies, hierarchical firewall policies enforce consistent allow, deny, or `goto_next` delegation rules at the organization node or individual folders (`<prefix>-net-default` on `Networking`) so lower-level project rules cannot override organization-wide security controls. Evaluation starts at the organization node and proceeds down folder levels; for Shared VPC workloads, policy inheritance follows the Shared VPC host project's folder path rather than the service project's folder path, and `targetResources` can scope rules to specific VPC networks.

Apply these firewall governance recommendations across environments:

1. Scope rules by dedicated workload service accounts (`target_service_accounts`) or IAM-governed Secure Tags (`target_secure_tags`) rather than mutable classic network tags wherever possible, because service accounts are project-scoped and Secure Tags require explicit Resource Manager IAM tag bindings.
2. Restrict classic network tag-based firewall rules tightly because any user able to edit VM metadata can attach an arbitrary classic network tag, and ensure `BEFORE_CLASSIC_FIREWALL` policy evaluation accounts for higher-priority policy rules in Stage `2-networking-a-fedramp`.
3. Use specific subnet ranges or summarized CIDR blocks when broader network-level rules are required, relying on `custom.restrictFirewallRanges` to reject broad `0.0.0.0/0` and `::/0` ingress allow rules.
4. Create an explicit high-priority egress-deny rule ahead of the implied `65535` allow-egress rule so both ingress and egress traffic require explicit authorization.
5. Enforce a deterministic firewall naming convention and populate rule descriptions to preserve audit context.
6. Modify firewall rules managed automatically by Google Cloud service agents such as Google Kubernetes Engine only as documented by that service to avoid cluster disruptions or SLA invalidation.
7. Enable Firewall Rules Logging on security-relevant allow and deny rules for continuous verification.
8. Use Network Intelligence Center [Firewall Insights](https://cloud.google.com/network-intelligence-center/docs/firewall-insights/concepts/overview) to identify shadowed rules, overly permissive ranges, and unused rulesets.
9. Manage all custom firewall policies and rules centrally in [Terraform](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/compute_network_firewall_policy_rule) through peer-reviewed CI/CD pipelines for full audit traceability.
10. Use [hierarchical firewall policies](https://cloud.google.com/vpc/docs/firewall-policies) such as `<prefix>-net-default` to enforce organization-wide baseline rules above individual project administrators.

#### Data management

##### Sensitive data inspection

Use Sensitive Data Protection (Cloud Data Loss Prevention) to scan application logs and storage repositories on a recurring schedule where supported by regional residency rules, generating reports that identify inadvertently logged PII or sensitive tokens.

### 5.8 Vulnerability management

Google Cloud retired Rapid Vulnerability Detection on July 14, 2024. Stellar Engine environments combine active host, container, and platform posture capabilities across supported compliance boundaries alongside required DoD and federal assessment scanners.

#### OS and host vulnerability scanning

Use [VM Manager OS inventory and vulnerability management](https://cloud.google.com/compute/docs/os-inventory-management) together with Security Command Center [vulnerability findings](https://cloud.google.com/security-command-center/docs/concepts-vulnerabilities-findings) to detect missing OS patches and vulnerable packages on Compute Engine VMs running the OS Config agent. Automate recurring OS patch jobs for fleets rather than relying on manual host inspection.

#### Container and artifact scanning

Enable [Artifact Analysis on-demand and automated container scanning](https://cloud.google.com/artifact-analysis/docs/container-scanning-overview) on Artifact Registry repositories so container images built for GKE, Cloud Run, and Dataflow pipelines are scanned for known CVEs prior to deployment and monitored continuously as new advisories publish. Enforce Binary Authorization policies in `blueprints/il5/gke-hardened` and compatible workloads to block unattested or vulnerable images at admission time.

#### Security Command Center posture and threat findings

Where Security Command Center is enabled under your regime's authorization boundary (see the [Security Command Center deployment guide](./scc-deployment-guide.md)), use Security Health Analytics and Event Threat Detection to monitor misconfigurations, exposed services, and runtime threats, and export findings via Pub/Sub to your SIEM or query them through the [Security Command Center API](https://cloud.google.com/security-command-center/docs/how-to-api-list-findings#list_all_findings).

#### Regime scanning requirements

Security Command Center and certain managed Cloud DLP or Web Security Scanner features carry regional and regime approval constraints inside DoD IL5 enclaves. Regardless of managed Google Cloud add-ons, IL5 and FedRAMP High authorization boundaries require running Defense Information Systems Agency Security Technical Implementation Guides (STIG) checks and Assured Compliance Assessment Solution (ACAS) scans against hosts and containers as outlined in the [Path to authorization guide](./path-to-authorization.md).
