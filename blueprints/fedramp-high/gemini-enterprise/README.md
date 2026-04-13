# Gemini Enterprise for FedRAMP High - Comprehensive Documentation

**Version:** 1.2.0
**Compliance:** FedRAMP High / IL4+
**Scope:** Full System Documentation

---

## Table of Contents

1.  [Executive Overview](#1-executive-overview)
2.  [Architecture & Diagrams](#2-architecture--diagrams)
3.  [IAM Permissions & Prerequisites](#3-iam-permissions--prerequisites)
4.  [Stellar Engine Integration (Brownfield)](#4-stellar-engine-integration-brownfield)
5.  [Internal Ingress Deployment Guide](#5-internal-deployment-guide)
6.  [Stage 0: Infrastructure Foundation](#6-stage-0-infrastructure-foundation)
7.  [The gem4gov CLI Tool](#7-the-gem4gov-cli-tool)
8.  [Stage 1: Application Frontend](#8-stage-1-application-frontend)
9.  [Custom Brownfield Deployments (Non-Stellar Engine)](#9-custom-brownfield-deployments-non-stellar-engine)

---

## 1. Executive Overview

This blueprint deploys a secure and compliant environment for hosting Gemini Enterprise on Google Cloud Platform, specifically tailored for FedRAMP High requirements. It leverages the Vertex AI Search and Discovery Engine APIs. The deployment is divided into two main Terraform stages (`gemini-stage-0` and `gemini-stage-1`) and interacts with the `gem4gov` CLI tool.

**This blueprint supports both EXTERNAL and INTERNAL load balancer deployments, configurable via the `deployment_type` variable in `gemini-stage-0/terraform.tfvars`.**

It is designed to be **fully automated** via the `deploy.sh` script, which serves as the central management interface for the entire lifecycle of the application—from initial infrastructure provisioning to application updates and ongoing maintenance.

### Overall Goal

The primary goal is to provide a turnkey ("Push Button") solution for setting up Gemini Enterprise, enabling government customers and other regulated entities to utilize its AI-powered search and assistant capabilities while adhering to strict security and compliance mandates.

### Architecture Overview

The blueprint establishes a robust infrastructure including:

**1. Core Infrastructure (`gemini-stage-0`)**
- **Networking:**
  - **VPC & Subnets:** `google_compute_network` and `google_compute_subnetwork` for private and proxy-only subnets (Greenfield) or data source attachment to Shared VPC (Brownfield).
  - **IP Addressing:** `google_compute_address` for reserved internal/external Load Balancer IP.
  - **Network Endpoints:** `google_compute_region_network_endpoint_group` and `google_compute_region_network_endpoint` mapping to the Discovery Engine FQDN (`vertexaisearch.cloud.google.com`).
  - **HTTP Redirect (External LB):** `google_compute_region_url_map`, `google_compute_region_target_http_proxy`, and `google_compute_forwarding_rule` to ensure all HTTP traffic upgrades to HTTPS.
- **Security & Access Control:**
  - **Cloud Armor (WAF):** `google_compute_region_security_policy` with predefined OWASP rules and US-only geo-fencing.
  - **Access Context Manager:** `google_access_context_manager_access_level` defining conditions like Time of Day, IP Restrictions, Expiration Dates, and leniency tiers for Chrome Enterprise Premium device identity.
  - **IAM Bindings:** `google_project_iam_member` ensuring least privilege for Gemini Enterprise Admins, Gemini Enterprise End Users, and required Service Accounts.
- **Data Storage & Encryption:**
  - **KMS / CMEK:** `google_kms_key_ring`, `google_kms_crypto_key`, and `google_kms_crypto_key_iam_member` for encrypting Discovery Engine data stores.
  - **Discovery Engine Settings:** `google_discovery_engine_cmek_config` and `google_discovery_engine_acl_config`.
  - **Data Sources:** `google_storage_bucket` (GCS) and `google_bigquery_dataset` (BQ) acting as safe data hubs.

**2. Gemini Enterprise (`gem4gov-cli`):**
- **Gemini Application:** Creates and configures the core Search Engine resource.
- **Data Stores:** Configures and attaches Cloud Storage and BigQuery data stores to the Gemini Enterprise application.

**3. Application Frontend (`gemini-stage-1`)**
- **Gemini Application:** Creates the core Discovery Engine Application.
- **Data Stores:** Configures and attaches Cloud Storage and BigQuery data stores to the Gemini application.
- **Load Balancing:**
  - **Backend Service:** `google_compute_region_backend_service` pointing to the Stage 0 NEG.
  - **HTTPS Routing:** `google_compute_region_url_map` and `google_compute_region_target_https_proxy` (utilizing the managed/unmanaged SSL certificate).
  - **Forwarding Rule:** `google_compute_forwarding_rule` to accept external/internal HTTPS traffic.
- **Identity-Aware Proxy (IAP):**
  - **IAP Access Control:** `google_iap_web_region_backend_service_iam_member` binding the specific Admin/User Groups (or Workforce Identity Principals) to the Backend Service, enforcing the zero-trust boundary.

### Deployment Automation (`deploy.sh`)

The `deploy.sh` script is the recommended way to interact with this blueprint. It handles:

1.  **Interactive Configuration:** Guides you through every step, including authentication, project selection, prerequisite checking,and deployment topology selection (Greenfield vs. Brownfield).
2.  **Automated Discovery:**
    -   **Session Persistence:** Uses remote Terraform state to track resources that have been already deployed in a separate session
    -   **Resource Discovery:** Finds existing constraints, keys, networks, and subnets to prevent misconfiguration.
3.  **Variable Generation:** Auto-generates `terraform.tfvars` files for both stages, eliminating manual copy-pasting errors.
4.  **Lifecycle Management:** Contains a **"Helper Functions"** menu for post-deployment tasks:
    -   **Update App Compliance:** Ensure an existing Gemini Enterprise application meets the most recent compliance standards and includes any recently authorized features
    -   **Replace App / Routing:** Seamlessly swap the backend Gemini Enterprise application while maintaining the Load Balancer.
    -   **Import Documents:** Interactive utility to ingest data into GCS/BigQuery Data Stores.
    -   **Upload SSL Certificate:** Validates and uploads PEM certificates to GCP Certificate Manager.

#### 1. Intelligent Context Detection

- **Greenfield:** Prompts for a new `prefix` and creates a fresh environment with its own VPC, Subnets, and Keys.
- **Brownfield (Stellar Engine):** Automatically detects the environment context based on the Project ID.
  - **Prefix & Tenant Derivation:** Extracts `sedev`, `g4g`, etc., directly from the Project ID.
  - **State Bucket Reuse:** Identifies and reuses the existing Terraform state bucket provisioned by the Stellar Engine core pipeline.
  - **Key Inheritance:** Reuses the Tenant's existing `iac-core` KMS keyring for encryption, ensuring proper separation of duties while maintaining compliance.

#### 2. Network Integration

- **Greenfield:** Signals Terraform to create a new `gemini-enterprise-vpc`.
- **Brownfield:** Automatically discovers Shared VPC Host Projects, scans for usable subnets (Private and Proxy), and configures Stage 0 to attach to them.

---

## 2. Architecture & Diagrams

### Deployment Topologies: Greenfield vs. Brownfield

This diagram illustrates the difference between a standalone "Greenfield" deployment and a "Brownfield" deployment integrated with Stellar Engine (Shared VPC).

```text
+--------------------------------------------------+       +--------------------------------------------------+
| Greenfield Deployment (Standalone)               |       | Brownfield Deployment (Stellar Engine)           |
+--------------------------------------------------+       +--------------------------------------------------+
|                                                  |       |                                                  |
|   [ User / Terraform ]                           |       |   [ User / Terraform ]                           |
|           |                                      |       |           |                                      |
|           v                                      |       |           v                                      |
|   [ Creates New VPC ]                            |       |   [ Discovers Shared VPC Host Project ]          |
|           |                                      |       |           |                                      |
|           v                                      |       |           v                                      |
|   [ Deploys Gemini Resources ]                   |       |   [ Deploys Gemini Resources to Service Proj ]   |
|           |                                      |       |           |                                      |
|           v                                      |       |           v                                      |
|   [ Attached to New Subnets ]                    |       |   [ Attached to Shared Subnets ]                 |
|                                                  |       |                                                  |
+--------------------------------------------------+       +--------------------------------------------------+
```

### Network Access Patterns: External vs. Internal

This diagram contrasts the traffic flow for External (Internet-facing) vs. Internal (VPN/Interconnect) deployments.

```text
+--------------------------------------------------+       +--------------------------------------------------+
| External Deployment (Cloud Native Access Point)  |       | Internal Deployment (Hub & Spoke)                |
+--------------------------------------------------+       +--------------------------------------------------+
|                                                  |       |                                                  |
|   [ Internet User ]                              |       |   [ On-Prem User ]                               |
|           |                                      |       |           |                                      |
|           v (HTTPS)                              |       |           v (VPN / Interconnect)                 |
|   [ Cloud Native Access Point (CNAP) ]           |       |   [ Shared VPC Host Project (Hub) ]              |
|   [ Regional External ALB ]                      |       |   [ Cloud Router / VPN Gateway ]                 |
|           |                                      |       |           |                                      |
|           v                                      |       |           v (Shared VPC Peering)                 |
|   [ Cloud Armor (WAF) ]                          |       |   [ Gemini Service Project (Spoke) ]             |
|   [ DDoS Protection & Geo-Fencing ]              |       |   [ Regional Internal LB ]                       |
|           |                                      |       |           |                                      |
|           v                                      |       |           v                                      |
|   [ Identity-Aware Proxy (IAP) ]                 |       |   [ Identity-Aware Proxy (IAP) ]                 |
|   [ Zero Trust Policy Check ]                    |       |   [ Context-Aware Access ]                       |
|           |                                      |       |           |                                      |
|           v                                      |       |           v                                      |
|   [ Gemini Enterprise Application ]              |       |   [ Gemini Enterprise Application ]              |
|                                                  |       |                                                  |
+--------------------------------------------------+       +--------------------------------------------------+
```

### Ingress & Security Architecture

The blueprint supports two primary ingress patterns, applicable to both Greenfield and Brownfield deployments.

#### 1. Internal Ingress (Private Access)

Designed for access from on-premise networks or other VPCs via private IP.

- **Architecture:** Uses a **Regional Internal Application Load Balancer (L7)**.
- **Security:** Protected by **Identity-Aware Proxy (IAP)** to enforce zero-trust access.
- **Deployment Variants:**

  - **Brownfield (Stellar Engine):** Leverages the **Stellar Engine VDSS & Hub-Spoke** architecture.

    - **VDSS Layer (`net-vdss-host`):** Acts as the secure entry point. Traffic enters the **DMZ VPC** (`vdss-dmz-0`) and is routed via **Network Virtual Appliances (NVAs)** to the **Landing VPC** (`vdss-landing-0`).
      - **NVAs:** Managed Instance Groups fronted by Internal L3 Load Balancers (`nva-dmz-primary`, `nva-vdss-primary`) handle inspection and routing between DMZ and Landing zones.
    - **Net Host Layer (`*-net-host`):** The Landing VPC connects downstream to environment-specific Net Host projects (e.g., `*-test-net-host`, `*-int-net-host`, `*-prod-net-host`).
    - **Spoke Layer:** These Net Host projects host the Shared VPC networks (e.g., `test-spoke-0`, `int-spoke-0`, `prod-spoke-0`).
    - **Tenant Attachment:** The Tenant Project attaches as a **Service Project** to the target Net Host Shared VPC. The Internal Load Balancer consumes subnets from this shared network (e.g., `prod-spoke-0`).

    > **Note:** For **Stellar Engine (Brownfield)** deployments, the Cloud VPN or Cloud Interconnect is already established in the **Host Project**. You do not need to provision new connectivity; the Tenant Project inherits this access via the Shared VPC.

    **Traffic Flow:**
    `User -> VPN -> VDSS (DMZ -> NVA -> Landing) -> Net Host (Spoke) -> Tenant (ILB)`

  - **Greenfield:** The blueprint creates a **dedicated VPC** and subnets (`gemini-enterprise-vpc`). The ILB is deployed into this new network.

    > **Note:** You must establish your own VPN/Interconnect or Peering to this VPC for on-prem access. See the [Internal Ingress](#1-internal-ingress-private-access) section for details on how to configure this connectivity.

#### 2. External Ingress (Internet Access)

Designed for secure access from the public internet, following the **Cloud Native Access Point (CNAP)** model.

- **Architecture:** Uses a **Regional External Application Load Balancer (L7)**.
- **Security:**
  - **Cloud Armor (WAF):** Provides DDoS protection and Geo-blocking (default: US-only).
  - **Identity-Aware Proxy (IAP):** Authenticates users (Google Identity or Workforce Identity) and enforces context-aware access policies.
  - **Zero Trust:** Checks device state (with Chrome Enterprise Premium), location, and time.
- **Deployment Variants:**
  - **Brownfield:** The External LB is deployed in the Service Project. It uses the Shared VPC's proxy subnets (if applicable/shared) or project-local resources depending on configuration.
  - **Greenfield:** Deployed in the dedicated `gemini-enterprise-vpc`. The blueprint provisions all necessary public IPs and firewall rules.

> **Note:** External Ingress **does NOT** require a Cloud VPN or Cloud Interconnect connection. It is secure by design, following the [DOD Cloud Native Access Point Reference Design](https://dodcio.defense.gov/Portals/0/Documents/Library/CNAP_RefDesign_v1.0.pdf), which adheres to **FedRAMP High** compliance and aligns with the **DoD's mandate to implement a Zero Trust cybersecurity framework by fiscal year 2027** ([Target Level Zero Trust](https://dodcio.defense.gov/Portals/0/Documents/Library/DoD-ZTStrategy.pdf)).

---

## 3. IAM Permissions & Prerequisites

This section outlines the necessary Identity and Access Management (IAM) permissions required to successfully run the `deploy.sh` script and the associated Terraform configurations for the Gemini Enterprise Blueprint.

### Overview

The deployment process involves interacting with Google Cloud resources across multiple stages. The user running the deployment must have sufficient privileges to:

1.  **Run the Deployment Script:** Access Cloud Storage for state management and query project metadata.
2.  **Discover Shared VPC Resources:** List networks and subnets in the Shared VPC Host Project (if applicable).
3.  **Provision Infrastructure (Stage 0):** Create networking, load balancing, and security resources.
4.  **Deploy Application (Stage 1):** Deploy Cloud Run services, manage Service Accounts, and configure secrets.

### 1. Deployment Script Prerequisites (`deploy.sh`)

The script itself performs pre-flight checks (`check_dependencies`) and state management. It now automatically checks for critical Organization Policies (e.g., `compute.restrictLoadBalancerCreationForTypes`, `compute.disableInternetNetworkEndpointGroup`) to ensure deployment success.

**Required Tools (Checked by script):**

- `gcloud`
- `terraform`
- `pip3` / `python3`
- `jq` (essential for parsing JSON outputs)

**Required Roles:**

- `roles/storage.admin` (or `roles/storage.objectAdmin`) on the State Bucket.
- `roles/browser` (or `roles/viewer`) on the Target Project.
- `roles/orgpolicy.policyViewer` (Recommended: allows the script to validate policies).
- `roles/cloudkms.cryptoKeyEncrypterDecrypter` (or Admin) on the CMEK Key (if reusing existing encryption).

**Specific Permissions:**

- `storage.buckets.get`
- `storage.objects.get/create/delete`
- `resourcemanager.projects.get`
- `serviceusage.services.list`
- `orgpolicy.policies.list`

### 2. Shared VPC Discovery

If you are using a Shared VPC (Brownfield / Custom), the deployment user needs permissions to discover and use resources in the **Host Project**.

**Required Roles on Host Project:**

- `roles/compute.networkViewer` (Minimum for discovery)
- `roles/compute.networkUser` (Required for attaching resources to the subnets)

**Specific Permissions:**

- `compute.projects.get` (on Host Project)
- `compute.networks.list` (on Host Project)
- `compute.subnetworks.list` (on Host Project)
- `compute.subnetworks.listUsable` (on Host Project)
- `compute.subnetworks.use` (on the specific subnets)

> **Note:** The fallback discovery mechanism specifically relies on `compute.subnetworks.list` to query the Host Project directly if `list-usable` returns empty results.

### 3. Terraform Stage 0: Infrastructure

Stage 0 provisions the core networking and security infrastructure.

**Required Roles:**

**Organization Level:**

- `roles/accesscontextmanager.policyAdmin` (Manage Access Context Manager policies)
- `roles/orgpolicy.policyAdmin` (Set organization policies)
- `roles/assuredworkloads.reader` (Read Assured Workloads compliance status)
- `roles/iam.workforcePoolAdmin` (Manage Workforce Identity Pools - if using Third Party IdP)

**Project Level:**

- `roles/viewer` (Read-only access to project resources)
- `roles/aiplatform.admin` (Vertex AI management)
- `roles/compute.loadBalancerAdmin` (Load Balancer management)
- `roles/compute.networkAdmin` (VPC and Network management)
- `roles/compute.securityAdmin` (Cloud Armor security policies)
- `roles/cloudkms.admin` (KMS Key management)
- `roles/discoveryengine.admin` (Discovery Engine management)
- `roles/iap.admin` (IAP configuration)
- `roles/iap.settingsAdmin` (IAP settings for Third Party IdP)
- `roles/oauthconfig.editor` (OAuth consent screen configuration)
- `roles/resourcemanager.projectIamAdmin` (IAM policy management)
- `roles/serviceusage.serviceUsageAdmin` (API enablement)
- `roles/storage.admin` (GCS Bucket management)
- `roles/bigquery.admin` (BigQuery management)
- `roles/iam.serviceAccountCreator` (Service Account creation)
- `roles/dns.admin` (Cloud DNS management - if applicable)

**Specific Permissions (if using Custom Roles):**

- `accesscontextmanager.*`
- `orgpolicy.policies.*`
- `compute.networks.*`
- `compute.subnetworks.*`
- `compute.firewalls.*`
- `compute.routers.*`
- `compute.addresses.*`
- `compute.forwardingRules.*`
- `compute.regionBackendServices.*`
- `compute.regionHealthChecks.*`
- `compute.regionNetworkEndpointGroups.*`
- `compute.sslCertificates.*`
- `compute.targetHttpProxies.*`
- `compute.urlMaps.*`
- `compute.globalAddresses.*`
- `compute.securityPolicies.*`
- `iap.brands.*`
- `iap.identityAwareProxyClients.*`
- `resourcemanager.projects.setIamPolicy`
- `serviceusage.services.enable`
- `storage.buckets.*`
- `cloudkms.cryptoKeys.*`
- `discoveryengine.*`

### 4. Terraform Stage 1: Application

Stage 1 deploys the Gemini Enterprise application on Cloud Run.

**Required Roles on Target Project:**

- `roles/iam.serviceAccountAdmin` (Service Account creation)
- `roles/artifactregistry.admin` (If managing repositories)
- `roles/secretmanager.admin` (Secret management)
- `roles/serviceusage.serviceUsageAdmin` (Enabling APIs)

**Specific Permissions:**

- `run.services.*`
- `run.services.setIamPolicy`
- `iam.serviceAccounts.create`
- `iam.serviceAccounts.setIamPolicy`
- `iam.serviceAccounts.actAs`
- `artifactregistry.repositories.*`
- `secretmanager.secrets.*`
- `secretmanager.versions.add`
- `serviceusage.services.enable`

### Summary of Recommended Roles

For a smooth deployment experience, we recommend granting the following roles to the deployment user (or Service Account):

**On the Target Project:**

- `roles/owner` (Simplest, covers most requirements)
- OR
- `roles/editor`
- `roles/compute.networkAdmin`
- `roles/iap.admin`
- `roles/secretmanager.admin`
- `roles/resourcemanager.projectIamAdmin`

**On the Shared VPC Host Project (if applicable):**

- `roles/compute.networkUser`
- `roles/compute.networkViewer`

**On the Terraform State Bucket:**

- `roles/storage.admin`

---

## 4. Stellar Engine Integration (Brownfield)

This section details how the Gemini Enterprise deployment script (`deploy.sh`) integrates with an existing Stellar Engine "Brownfield" environment.

### Overview

When "Brownfield - Stellar Engine Integration" is selected, the script automates the configuration process by:

1.  **Prefix Extraction:** Derives the Stellar Engine prefix directly from the Project ID (e.g., extracts `sedev` from `sedev-test-nate-main-0`).
2.  **Tenant Context:** Identifies the Environment (`test`, `dev`, `prod`) and Tenant ID (`nate`, `g4g`) to locate the correct "IaC" project.
3.  **State Bucket Reuse:** Discovers the existing **Tenant IaC Core State Bucket** (`<prefix>-<env>-<tenant>-iac-0`) and reuses it for Gemini Enterprise state.
    -   *Crucial:* This ensures that Gemini Enterprise state lives alongside the rest of the tenant's infrastructure state.
4.  **CMEK Inheritance:**
    -   **State Key:** Discovers the key protecting the State Bucket.
    -   **Resource Key:** Scans the Tenant IaC Project for the `gcs` and `gemini-enterprise` (or `default`) keys in the `us` or `us-east4` keyrings.
    -   *Benefit:* No need to create new keys; leverages the tenant's existing crypto-boundary.

### Dynamic Discovery Logic

The `discover_infrastructure` function in `deploy.sh` performs the following:

1.  **Derive IaC Project:** `<prefix>-<env>-<tenant>-iac-core-0`
2.  **Locate State Bucket:** Checks `gs://${PREFIX}-${ENVIRONMENT}-${TENANT}-iac-0`.
3.  **Find Keys:**
    -   Checks US Multi-Region Keyring: `projects/.../locations/us/keyRings/${Environment}-${Tenant}-keyring`
    -   Checks Regional Keyring (fallback): `projects/.../locations/${REGION}/keyRings/${Environment}-${Tenant}-keyring`

### Network Integration (Shared VPC)

- **Automated:** If the Project ID indicates a Stellar Engine environment, the script assumes a Shared VPC architecture.
- **Discovery:** It queries the **Host Project** (typically `<prefix>-<env>-net-host`) for subnets shared with the Tenant Project.
- **Selection:**
    -   **Private Subnet:** Selects the first available PRIVATE subnet.
    -   **Proxy Subnet:** Selects the designated `REGIONAL_MANAGED_PROXY` subnet for the Internal Load Balancer.

**Result:** The script generates `gemini-stage-0/terraform.tfvars` with:
```hcl
use_shared_vpc = true
network_project_id = "sedev-test-net-host"
shared_vpc_network_name = "test-spoke-0"
shared_vpc_subnet_name = "test-spoke-0"
shared_vpc_proxy_subnet_name = "test-spoke-0-proxy"
```
#### Access Policy

**Command:** `gcloud access-context-manager policies list`

- **Purpose:** Auto-discovers the numeric Access Policy ID required for Chrome Enterprise Premium and VPC Service Controls.

### Generated Configuration

The script generates a `gemini-stage-0/terraform.tfvars` file populated with these discovered values, ensuring that the Gemini Enterprise deployment aligns perfectly with the existing Stellar Engine security and naming standards.

### Network Integration (Shared VPC)

The deployment logic now intelligently handles network configuration based on the environment type:

#### Brownfield (Shared VPC)

- **Logic:** If `use_shared_vpc` is set to `true` in Stage 0, Stage 1 automatically retrieves the Shared VPC details (`network_project_id`, `shared_vpc_network_name`, etc.) from the Stage 0 remote state.
- **Benefit:** Eliminates the need for manual input or hardcoded network names, ensuring seamless integration with the existing Stellar Engine Shared VPC.

#### Greenfield (Standalone VPC)

- **Logic:** If `use_shared_vpc` is `false` (default), Stage 1 defaults to using the `gemini-enterprise-vpc` created in Stage 0.
- **Benefit:** Preserves the standard behavior for standalone deployments while allowing for easy switching to Shared VPC if needed.

#### Stage 0 State Dependency

**Crucial:** The Shared VPC configuration is passed from Stage 0 to Stage 1 via Terraform outputs. If you modify the Shared VPC settings in `gemini-stage-0/terraform.tfvars`, you **must re-apply Stage 0** to update the state before deploying Stage 1.

---

## 5. Internal Ingress Deployment Guide

This section outlines the deployment of the Gemini Enterprise application on Google Cloud Platform, specifically for **internal-only access** from on-premise networks or other VPCs connected via Cloud VPN or Interconnect. This guide uses the main `gemini-stage-0` and `gemini-stage-1` directories, with specific variable settings.

### Deployment Overview

This deployment uses a Regional _Internal_ HTTP(S) Load Balancer (ILB) by setting `deployment_type = "internal"` in the `terraform.tfvars` file in `gemini-stage-0`. The application will NOT be accessible from the public internet.

**Key Components:**

- **VPC & Subnet:** Defined in `gemini-stage-0/network.tf`. The subnet range for the ILB can be set via `internal_lb_subnet_range` in `gemini-stage-0/terraform.tfvars`.
- **KMS Keys:** Defined in `gemini-stage-0/discovery-engine.tf`.
- **Discovery Engine:** Configured in `gemini-stage-0/discovery-engine.tf`.
- **Internal Load Balancer:** Configured in `gemini-stage-1/load_balancer.tf`, enabled by `deployment_type = "internal"`.
- **IAP:** Identity-Aware Proxy is used to secure access to the ILB.

### Prerequisites

1.  **Network Connectivity:** Ensure your on-premise network has a working connection to the GCP VPC where Gemini Enterprise will be deployed. This must be one of:

    - [Cloud VPN](https://cloud.google.com/network-connectivity/docs/vpn)
    - [Cloud Interconnect](https://cloud.google.com/network-connectivity/docs/interconnect)

2.  **Internal DNS Server:** You must have an internal DNS server (e.g., Windows DNS, BIND) on your on-premise network that your clients use for name resolution.

3.  **IP Address Space:** Ensure the VPC's IP range (defined by `internal_lb_subnet_range` in `gemini-stage-0/variables.tf`) does not conflict with your on-premise network ranges. See [Handling Overlapping IP Ranges](#handling-overlapping-ip-ranges).

4.  **Permissions:** Ensure the service account or user running Terraform has the necessary permissions to create all resources defined in `gemini-stage-0` and `gemini-stage-1`.

5.  **Organization Policy:** If deploying the **External** variant (not the primary focus of this doc, but relevant if reusing this blueprint), you must ensure the `compute.restrictLoadBalancerCreationForTypes` organization policy allows `EXTERNAL_MANAGED_HTTP_HTTPS` load balancers.

### Deployment Steps



1.  **Run `deploy.sh`:**
    -   Select **Option 1 (Deploy Stage 0)**.
    -   Select **Deployment Type:** "Brownfield" (if in Stellar) or "Greenfield".
    -   **When prompted for Usage Type:** Select **"2) Regional Internal (VPN / Interconnect)"**.
    -   **IP Ranges:** Enter the CIDR ranges of your on-premise network allowed to access the ILB.
    -   The script will generate the correct `terraform.tfvars` with `deployment_type = "internal"` and apply the changes.

2.  **Create App & Certificate:**
    -   Run `deploy.sh` -> **Helper Functions** -> **Upload SSL Certificate**.
        -   Upload your internal certificate (PEM format).
    -   Run `deploy.sh` -> **Step 2 (Create Gemini Enterprise App)**.
        -   Creates the engine and provides the `gemini_config_id`.

3.  **Deploy Stage 1:**
    -   Run `deploy.sh` -> **Step 3 (Deploy Stage 1)**.
    -   **Reuse Configuration:** Select **Yes**.
    -   Enter the `gemini_config_id` and the name of the certificate you uploaded.

4.  **Verification:**
    -   Configure your internal DNS (split-horizon) to point `gemini.yourdomain.internal` to the **Gemini Enterprise IP** (Output from Stage 0).
    -   Access the URL from your on-premise network.

### DNS Configuration (Split-Horizon DNS)

The goal is to configure your internal, on-premise DNS to resolve the domain name to the private IP address of the Google Cloud Internal Load Balancer.

**Core Concept:**

- **Public DNS:** Used by the internet.
- **Private DNS:** Used within your corporate network for internal resources.

You need to make your on-premise DNS server authoritative for resolving the internal service name (e.g., `gemini-internal.mycompany.com`) to the reserved internal IP in GCP (e.g., `10.10.10.5`).

**Steps:**

1.  **Identify Your Internal DNS Server:** Locate your corporate DNS server (e.g., Windows DNS, BIND).
2.  **Create a DNS 'A' Record:** On the internal DNS server, create a new 'A' record.
3.  **Configure the 'A' Record:**
    - **Name/Host:** The desired subdomain (e.g., `gemini-internal`).
    - **IP Address:** The reserved internal IP of the GCP load balancer (from Stage 0 output).
    - Example: `gemini-internal.mycompany.com -> 10.10.10.5`
4.  **Test from On-Premise:** Use `nslookup` or `ping` from an on-premise machine to verify resolution to the internal IP.
    ```bash
    ping gemini-internal.mycompany.com
    ```
    Flush DNS cache if needed (`ipconfig /flushdns` on Windows).

### SSL Certificate Provisioning for HTTPS

To enable HTTPS on the internal load balancer, an SSL certificate signed by your organization's internal Certificate Authority (CA) is required.

**Process:**

1.  **Private Key:** Secret file used by the load balancer for encryption.
2.  **Certificate Signing Request (CSR):** File generated from the private key, submitted to the internal CA.
3.  **Signed Certificate:** File provided by the internal CA after signing the CSR.

**Customer Action Plan:**

1.  **Generate the Private Key:** On a secure workstation, use OpenSSL:

    ```bash
    openssl genrsa -out gemini-internal.key 2048
    ```

    **Warning:** Protect `gemini-internal.key` as it is highly sensitive.

2.  **Create the Certificate Signing Request (CSR):**

    ```bash
    openssl req -new -key gemini-internal.key -out gemini-internal.csr
    ```

    Provide the requested information. The **Common Name** MUST match the internal domain name users will access (e.g., `gemini-internal.mycompany.gov`).

    | Field                          | Example Value                 | Description                                         |
    | :----------------------------- | :---------------------------- | :-------------------------------------------------- |
    | Country Name (2 letter code)   | US                            | Your country code.                                  |
    | State or Province Name         | Virginia                      | Your state or province.                             |
    | Locality Name (eg, city)       | Reston                        | Your city.                                          |
    | Organization Name              | Department of Example         | Your official organization name.                    |
    | Organizational Unit Name       | IT Security                   | Your specific department or unit.                   |
    | Common Name (e.g. server FQDN) | gemini-internal.mycompany.gov | **Crucial:** Exact internal domain name for access. |
    | Email Address                  | your-email@mycompany.gov      | An administrative contact email.                    |

3.  **Get the CSR Signed by Your Internal CA:** Submit `gemini-internal.csr` to your internal IT/Cybersecurity team for signature. They will return:

    - The Signed Certificate (e.g., `gemini-internal.crt`).
    - Intermediate/Chain Certificate (if applicable, e.g., `ca-chain.crt`).

4.  **Securely Provide Certificate Files to GCP Admin:** Transfer the following files securely to the administrator managing the GCP deployment:

    - `gemini-internal.key`
    - `gemini-internal.crt`
    - Intermediate/Chain Certificate (if provided).

5.  **Upload to GCP Certificate Manager:** The GCP administrator will upload these certificate files to Google Cloud Certificate Manager.

6.  **Update Load Balancer:** The Terraform configuration in `gemini-stage-1/load_balancer.tf` must be updated to reference the uploaded certificate in Certificate Manager, and `terraform apply` run again if needed.

7.  **Verification (Recommended):** After the certificate is deployed, verify from an on-premise machine:
    ```bash
    openssl s_client -connect <LOAD_BALANCER_INTERNAL_IP>:443 -servername <YOUR_INTERNAL_DOMAIN>
    ```
    Example:
    ```bash
    openssl s_client -connect 10.10.10.5:443 -servername gemini-internal.mycompany.gov
    ```
    Look for `Verify return code: 0 (ok)` and check that the certificate details match.

### Access Flow

1.  User on on-premise network opens `https://gemini-internal.mycompany.com`.
2.  Client queries the _internal_ DNS server.
3.  Internal DNS server responds with the ILB's private IP (e.g., `10.10.10.5`).
4.  Traffic is routed over the Cloud VPN/Interconnect to the GCP VPC.
5.  The ILB receives the request, IAP enforces access, and the request is forwarded to the Gemini Enterprise application.

### Handling Overlapping IP Ranges

**Note on IP Addressing:** The most straightforward way to ensure connectivity between your on-premise network and GCP is to use non-overlapping IP address ranges. The solutions below are for scenarios where re-addressing your GCP VPC or on-premise network is not feasible. Planning unique IP space allocation upfront is highly recommended to avoid this complexity.

Creating a new Google Cloud VPC with a conflicting (overlapping) internal IP address of an on-prem range is a major networking challenge that requires careful planning to resolve.
You cannot directly connect two networks that have the same or overlapping CIDR blocks via VPC Network Peering, Cloud VPN, or Cloud Interconnect.

Here are the standard architectural solutions to this problem:

**Solution 1: Re-IP the New VPC (The Best Practice for Greenfield Deployments)**
This is the cleanest and most architecturally sound solution.

- **How it Works:** Recreate the new VPC with a unique, non-overlapping IP address range before deploying significant resources.
- **Pros:** Eliminates all routing ambiguity, simplifies networking and security rules.
- **Cons:** Can be extremely disruptive if resources are already deployed.
- **Best For:** Greenfield deployments. Proactive IP Address Management (IPAM) is crucial.

**Solution 2: Use Network Address Translation (NAT) (The Standard Workaround for Brownfield Deployments)**
This is the most common solution when re-IPing is not an option.

- **How it Works:**
  1.  **Create a Hub/Transit VPC:** Set up a third VPC with a unique IP range (e.g., `10.255.255.0/24`) that does NOT overlap with the on-prem network.
  2.  **Deploy a NAT Device:** Inside the Hub VPC, deploy a Network Virtual Appliance (NVA) from the Marketplace (e.g., Palo Alto, Cisco, Fortinet) or a custom Linux router VM.
  3.  **Establish Connectivity:** Connect your on-prem network to this Hub VPC using Cloud VPN or Interconnect with Cloud Router.
  4.  **Peer Hub VPC with Gemini VPC:** Connect the Hub VPC to the Gemini VPC (with the overlapping IPs) using VPC Network Peering.
  5.  **Configure NAT Rules on the NVA:**
      - **Destination NAT (DNAT):** Allocate a non-conflicting "proxy" IP range (e.g., `10.200.0.0/16`). On-prem traffic destined for a proxy IP (e.g., `10.200.10.5`) is routed to the NVA. The NVA translates the destination to the real internal IP in the conflicting VPC (e.g., `10.10.10.5`).
      - **Source NAT (SNAT):** For return traffic, the NVA translates the source IP from the real IP back to the proxy IP before sending it to the on-prem network.
- **Pros:** Solves the overlapping IP problem without re-architecting existing networks.
- **Cons:** Adds complexity, cost, potential performance bottleneck (the NVA), and requires NAT rule management.

  **Implementation Details for NAT Solution:**

  - **On-Prem to Hub VPC Connection:** Use Cloud VPN or Cloud Interconnect. Cloud Router will manage dynamic routes between the on-premise network and the Hub VPC.
  - **Hub VPC to Gemini VPC Connection:** Use **VPC Network Peering**. Since the Hub VPC has a unique IP range, it can be peered with the Gemini VPC (which has the overlapping IP range). This allows the NVA in the Hub VPC to route traffic to/from the internal IPs in the Gemini VPC.
  - **NVA Configuration:** The NVA is the core of this solution. It needs to be configured with:
    - Network interfaces in appropriate subnets within the Hub VPC.
    - Routing rules to forward traffic between the VPN/Interconnect interface and the interface connected to the peered Gemini VPC network.
    - DNAT rules to translate destination IPs from the on-prem accessible "proxy" range to the actual Gemini VPC internal IPs.
    - SNAT rules to translate source IPs from the Gemini VPC internal IPs back to the "proxy" range for traffic returning to the on-premise network.
  - **Routing:**
    - On-premise routers need static routes for the "proxy" IP range, pointing towards the Cloud VPN/Interconnect to the Hub VPC.
    - The Hub VPC, through peering, will know how to reach the Gemini VPC's subnets.

**Solution 3: Isolate and Use Application-Level Proxies**
Suitable if only specific services need to be accessed.

- **How it Works:** Place a proxy in a non-conflicting network that can reach into the conflicting one. On-prem users connect to the proxy.
  - **Bastion Host:** For SSH/RDP access.
  - **Internal Application Load Balancer:** Expose web services via an ILB in a non-conflicting VPC with backends in the conflicting VPC.
- **Pros:** Often more secure, granular access control.
- **Cons:** Does not provide general IP-level connectivity; per-service configuration required.

**Summary and Recommendation**

| Solution                             | How it Works                                                                                             | Pros                                           | Cons                                               |
| :----------------------------------- | :------------------------------------------------------------------------------------------------------- | :--------------------------------------------- | :------------------------------------------------- |
| 1. Re-IP / Re-Architect              | Change the IP range of the new VPC to be unique.                                                         | Simple, clean, high performance.               | Highly disruptive; often not feasible.             |
| 2. Network Address Translation (NAT) | Use a router/NVA in a hub VPC to translate between a proxy IP range and the real (conflicting) IP range. | Solves the problem without re-IPing. Flexible. | Adds complexity, cost, and a potential bottleneck. |
| 3. Application Proxy                 | Use bastion hosts or application-level load balancers to broker access to specific services.             | Secure, granular access.                       | Does not provide general network connectivity.     |

**Recommendation:** For connecting an on-premise hosted domain to an internal Google Cloud resource where a VPC has a conflicting IP, the standard enterprise solution is **#2: Implement NAT using a Network Virtual Appliance (NVA) in a dedicated hub VPC**.

### Stellar Engine Network Architecture & NAT

Stellar Engine implements **Solution 2 (NAT)** through its **VDSS (Virtual Data Center Security Stack)** architecture, specifically designed to handle complex networking requirements like overlapping IP ranges.

**Components:**

- **VDSS Host Project (`net-vdss-host`):** Acts as the central hub for network security and connectivity.
- **DMZ VPC (`vdss-dmz-0`):** An "untrusted" network zone intended for external connectivity (e.g., Internet, On-Prem VPN).
- **Landing VPC (`vdss-landing-0`):** A "trusted" network zone where spoke projects (like the one hosting Gemini Enterprise) attach via Shared VPC or Peering.
- **Network Virtual Appliance (NVA):** A highly available cluster of VMs (e.g., `nva-template`, `nva-mig`) deployed in the VDSS project. These NVAs have network interfaces in both the DMZ and Landing VPCs.

**How it Works:**

1.  **Connectivity:** Your on-premise network connects to the **DMZ VPC** (via VPN/Interconnect).
2.  **NAT/Routing:** The **NVA** intercepts traffic. It performs NAT (Network Address Translation) to translate overlapping on-premise IPs to non-conflicting "proxy" IPs within the Google Cloud environment.
3.  **Forwarding:** The NVA forwards the translated traffic to the **Landing VPC**.
4.  **Spoke Access:** Resources in the Gemini Enterprise project (attached to the Landing VPC or peered) receive the traffic.

**Configuration:**

The Stellar Engine `2-networking-a-fedramp-high` stage automatically provisions these components (defined in `nva.tf` and `net-vdss.tf`). You simply need to configure the specific NAT rules and routes on the NVA to match your on-premise addressing requirements. This pre-built architecture ensures that you can deploy Gemini Enterprise into a Brownfield environment with overlapping IPs without needing to re-architect your entire network.

### Stellar Engine Spoke Architecture

In the Stellar Engine model, tenant projects (like the one hosting Gemini Enterprise) are deployed as **Service Projects** (Spokes) attached to the central **Host Project** (`net-vdss-host`).

**How Spokes Consume Network Resources:**

1.  **No Local VPC:** The Gemini Enterprise project does **not** have its own VPC network. Instead, it leverages the **Shared VPC** owned by the Host Project.
2.  **Subnet Sharing:**
    - The Host Project explicitly shares specific subnets (e.g., `default-us-east4`) with the Tenant Project.
    - This is achieved by granting the `roles/compute.networkUser` IAM role to the Tenant Project's Service Accounts (e.g., the Cloud Run Service Agent, the deployment user) on those specific subnets.
3.  **Resource Attachment:** When you deploy resources (like the Internal Load Balancer) in the Tenant project, you specify the **Host Project's VPC** and the **Shared Subnet**. The resource lives in the Tenant project but is network-attached to the Host Project's infrastructure.

**Communication Flow:**

- **Spoke-to-On-Prem:** Traffic originates from the Gemini ILB (in the Shared Subnet), flows through the Host Project's Landing VPC, is routed to the NVA (if NAT is used) or directly to the Cloud VPN/Interconnect, and reaches the on-premise network.
- **Spoke-to-Internet:** Traffic flows from the Gemini project through the Host Project's Cloud NAT (configured in `net-vdss.tf`) to reach the internet (e.g., for API calls to Google services).
- **Spoke-to-Spoke:** If multiple tenant projects are attached to the same Shared VPC, they can communicate with each other via internal IP addresses, subject to Firewall Rules defined in the Host Project.

---

## Resources Created / Necessary

### Stage 0: Core Infrastructure Resources

**Groups:**
Manual:

- gcp-gemini-enterprise-admins@<your-domain>
- gcp-gemini-enterprise-users@<your-domain>

**Network Configuration (network.tf)**
Manual:

- Cloud VPN / Cloud Interconnect
  - The customer needs a way to connect to GCP if the deployment is internal.
- Cloud Router
  - Cloud Router is needed to establish the from On-prem to GCP routes.
- Certificates
  - The customer needs a way to create a certificate, and upload it to google cloud to certificate manager
- DNS
  - The customer needs to point the DNS A record to the subdomain of their choosing.

Terraform:

- **VPC and Subnets:**
  - `google_compute_network "gemini_enterprise_vpc"`: Main VPC for deployment.
  - `google_compute_subnetwork "gemini_enterprise_vpc_subnet"`: Subnet for the VPC.
  - `google_compute_subnetwork "gemini_enterprise_vpc_proxy_subnet"`: Subnet for the regional managed proxy (ILB).
- **IP Addresses:**
  - `google_compute_address "gemini_enterprise_internal_ip"`: Reserved internal IP for internal load balancer.
- **Network Endpoints:**
  - `google_compute_region_network_endpoint_group "gemini_enterprise_neg"`: NEG for vertexaisearch.cloud.google.com FQDN.
  - `google_compute_region_network_endpoint "gemini_enterprise_endpoint"`: Network endpoint for the NEG.

**Access Control (cloudarmor.tf)**

- **WAF Policy:**
  - `google_compute_region_security_policy "gemini_enterprise_policy"`: WAF policy to permit US traffic and deny others. As well as the OWASP Top 10.

**Discovery Engine (discovery-engine.tf)**

- **Key Management:**
  - `google_kms_key_ring "cmek_key_ring"`: Key ring for CMEK.
  - `google_kms_crypto_key "cmek_crypto_key"`: CMEK key for encryption.
  - `google_kms_crypto_key_iam_member "discoveryengine_sa_kms_access"`: IAM binding for Discovery Engine SA access to CMEK.
  - `google_kms_crypto_key_iam_member "gcs_sa_kms_access"`: IAM binding for GCS SA access to CMEK.
  - `google_kms_crypto_key_iam_member "bq_sa_kms_access"`: IAM binding for BigQuery SA access to CMEK.
- **Discovery Engine Configuration:**
  - `google_discovery_engine_cmek_config "default"`: Configures default CMEK for Discovery Engine.
  - `google_storage_bucket "gemini_enterprise_data"`: GCS buckets as data sources.
  - `google_discovery_engine_data_store "gemini_enterprise_gcs_ds"`: Data stores for GCS buckets.
  - `google_bigquery_dataset "gemini_enterprise_bq_ds"`: BigQuery datasets for connectors.
  - `google_bigquery_table "gemini_enterprise_bq_table"`: BigQuery tables.
  - `google_discovery_engine_data_connector "gemini_enterprise_bq_connector"`: Connectors for BigQuery tables.
  - `time_sleep "wait_for_bq_datastore"`: Delay for data store creation.
  - `google_discovery_engine_acl_config "gemini_enterprise_acl_config"`: Configures ACLs for Discovery Engine.

### Stage 1: Load Balancer and Access Configuration Resources

**Load Balancer (load_balancer.tf)**

- **Backend and URL Maps:**
  - `google_compute_region_backend_service "gemini_enterprise_backend"`: Backend service for the ILB.
  - `google_compute_region_url_map "gemini_enterprise_https_url_map"`: URL map for HTTPS routing.
  - `google_compute_region_url_map "gemini_enterprise_http_redirect_url_map"`: URL map for HTTP to HTTPS redirection.
- **Proxies and Forwarding Rules:**
  - `google_compute_region_target_https_proxy "gemini_enterprise_https_proxy"`: Target HTTPS proxy using customer SSL certificate from Certificate Manager.
  - `google_compute_region_target_http_proxy "gemini_enterprise_http_proxy"`: Target HTTP proxy for redirection.
  - `google_compute_forwarding_rule "gemini_enterprise_https_forwarding_rule"`: Forwarding rule for HTTPS traffic.
  - `google_compute_forwarding_rule "gemini_enterprise_http_forwarding_rule"`: Forwarding rule for HTTP traffic.

**IAP Access (load_balancer.tf)**

- **IAM Members:**
  - `google_iap_web_region_backend_service_iam_member "iap_admin"`: Grants IAP access to admin group.
  - `google_iap_web_region_backend_service_iam_member "iap_user"`: Grants IAP access to user group.

---

## 6. Stage 0: Infrastructure Foundation

This blueprint deploys the necessary infrastructure to host a Gemini Enterprise application on Google Cloud Platform, adhering to FedRAMP High compliance standards. It provisions a secure environment with networking, load balancing, access controls, and data stores for Vertex AI Search.

### Prerequisites & Manual Steps Before Apply

Before applying this Terraform module, ensure the following manual steps and configurations are completed:

1.  **Organization Policy**: The `deploy.sh` script now automatically checks for critical Organization Policies (e.g., `compute.restrictLoadBalancerCreationForTypes`). If deploying the **External** variant, ensure your policy allows `EXTERNAL_MANAGED_HTTP_HTTPS` load balancers.

2.  **Group Creation for IAP / Gemini Enterprise Access :**
    - If identity provider is Cloud Identity...
      - In the [Google Workspace Admin Console](https://admin.google.com/), create the following groups:
        - `gcp-gemini-enterprise-admins@<your-domain>`
        - `gcp-gemini-enterprise-users@<your-domain>`
      - Add the necessary users to these groups who will need access to the Gemini Enterprise application through the Identity-Aware Proxy.
    - If identity provider is Third-Party Identity Provider (i.e. Microsoft Entra, Okta, etc.)...
      - [Setup Workforce Identity Federation](https://docs.cloud.google.com/iam/docs/configuring-workforce-identity-federation) at the GCP Organization-level
      - Ensure Group IDs are being passed to the Secure Token Service API and the attribute-mapping in the Workforce Identity Provider maps the list of Group IDs to `google.groups` (i.e. `google.groups=assertion.groups`)
        - [Microsoft Entra] (https://learn.microsoft.com/en-us/entra/identity-platform/optional-claims?tabs=appui#configure-groups-optional-claims)
        - [Okta](https://developer.okta.com/docs/guides/customize-tokens-groups-claim/main/)

3.  **OAuth Consent Screen:**

    - In the Google Cloud Console, navigate to "APIs & Services" > "OAuth consent screen".
    - Configure the OAuth consent screen. Select "Internal" user type if only for your organization. Provide an app name (e.g., "Gemini Enterprise IAP"), user support email, and developer contact information.

4.  **Chrome Enterprise Premium (Optional):**

    - Manually enable and configure Chrome Enterprise Premium within the Google Cloud Console for your organization. This is required for certain contextual awareness policies and endpoint configurations, adding to your zero-trust security posture. ([Learn how to purchase Chrome Enterprise Premium here](https://support.google.com/chrome/a/answer/15832585?hl=en))
    - **Note:** Chrome Enterprise Premium is required to enforce advanced policies such as mandated MFA, Endpoint protection, and Encryption status. However, basic Access Context Manager capabilities, such as setting IP Ranges and Geographic restrictions, are available at the Load Balancer / IAP level without a premium subscription.

5.  **CMEK Configuration:**
    - The `deploy.sh` script automatically handles the creation of a Customer-Managed Encryption Key (CMEK) for the Terraform state bucket and passes this key to Terraform for use with Discovery Engine resources.
    - **Greenfield:** The key is created with a **90-day rotation period** and **HSM protection level** to meet FedRAMP High requirements.
    - **Brownfield:** The script discovers and reuses the existing Tenant `iac-core` key.
    - Ensure your project has sufficient quota for Cloud KMS keys and HSM usage.

**IMPORTANT:** This blueprint is designed to be deployed in a **FedRAMP High GCP project**, to ensure a clean slate for meeting stringent FedRAMP High security and compliance requirements.

### IAM Permissions for Deployment

The user or service account applying this Terraform configuration needs the following IAM roles:

**Organization Level:**

- `roles/accesscontextmanager.policyAdmin`: To manage Access Context Manager policies and levels.
- `roles/orgpolicy.policyAdmin`: To set organization policies.
- `roles/assuredworkloads.reader`: To determine if project is within Assured Workloads FedRAMP High boundary
- `roles/iam.workforcePoolAdmin`: To create Workforce Identity Pools / Providers (if using Third-Party Identity Provider)

**Project Level:**

- `roles/viewer`: To grant read-only access to most project resources
- `roles/aiplatform.admin`: To disable implicit model data caching in the project
- `roles/compute.loadBalancerAdmin`: For all load balancer resources (frontends, backends, NEGs, etc.)
- `roles/compute.networkAdmin`: For all networking resources (VPC, subnets, firewalls, etc.)
- `roles/compute.securityAdmin`: For Cloud Armor security policies
- `roles/oauthconfig.editor`: To configure OAuth for IAP
- `roles/iap.admin`: To configure IAP on backend services
- `roles/iap.settingsAdmin`: To configure the IAP settings for third-party identity provider
- `roles/serviceusage.serviceUsageAdmin`: To enable required APIs
- `roles/resourcemanager.projectIamAdmin`: To manage project IAM bindings and service identities
- `roles/cloudkms.admin`: For KMS key rings, keys, and IAM permissions
- `roles/storage.admin`: For GCS buckets
- `roles/bigquery.admin`: For BigQuery datasets and tables
- `roles/discoveryengine.admin`: For all Discovery Engine resources
- `roles/iam.serviceAccountCreator`: To create Service Accounts in the project

### Achieving Stricter Least Privilege

The roles listed above provide the necessary permissions using standard Google Cloud predefined roles. For an even stricter adherence to the principle of least privilege, you can create **Custom IAM Roles**.

This involves identifying the minimum specific permissions required for each Terraform resource being deployed and creating custom roles containing only those permissions. For example, instead of `roles/compute.networkAdmin`, you would create a custom role with specific permissions like `compute.networks.create`, `compute.subnetworks.create`, etc.

**Steps to Implement Custom Roles:**

1.  **Analyze Permissions:** Carefully review the Terraform provider documentation for each resource used in this module to determine the exact IAM permissions needed for create, read, update, and delete operations.
2.  **Create Custom Role(s):** Define custom roles at the project or organization level, including only the permissions identified in step 1.
3.  **Grant Custom Role(s):** Assign the custom role(s) to the service account or user deploying the module.

**Considerations:**

- Creating and maintaining custom roles requires significant effort and ongoing maintenance as the infrastructure evolves.
- Using a dedicated Service Account with the predefined roles listed earlier is a balanced approach that provides good security separation.

Refer to the [Google Cloud IAM documentation on Custom Roles](https://cloud.google.com/iam/docs/creating-custom-roles) for more details.

### Overall Architecture

The blueprint sets up the following key components:

1.  **Networking:** A dedicated Virtual Private Cloud (VPC) with subnets

    - Private Google Access subnet
    - Regional Managed Proxy subnet (for the regional https load balancer)
    - Regional Network Endpoint Group (INTERNET_FQDN_PORT) pointing to `vertexaisearch.cloud.google.com`.

2.  **Load Balancing:**

    - **Stage 0 (This Blueprint):** Deploys a Regional External HTTP Load Balancer to direct all HTTP traffic to HTTPS.
    - **Stage 1 (gemini-stage-1):** After you upload a Google-managed certificate and launch the Gemini Enterprise application using the `gem4gov` CLI, the `gemini-stage-1` blueprint will configure the main Regional External HTTPS Load Balancer. This will include the frontend configuration, certificate attachment, and routing rules to the Gemini Enterprise application instance.

3.  **Security:**

    - **Identity-Aware Proxy (IAP):** Enabled on the backend service in `load_balancer.tf`. IAP is configured to use pre-defined Access Context Manager levels to enforce contextual awareness policies for the prerequisite Google Workspace groups:
      - `gcp-gemini-enterprise-admins@<your-domain>`: Requires the `strict_device` policy. This level enforces:
        - US-based access.
        - Access only during business hours (Mon-Fri, 9 AM - 5 PM ET).
        - Access expiring at the end of 2026.
        - Device must be Corp-owned, encrypted, have a screen lock, and be running macOS or Windows.
      - `gcp-gemini-enterprise-users@<your-domain>`: Requires the `moderate_device` policy. This level enforces:
        - US-based access.
        - Access only during business hours (Mon-Fri, 9 AM - 5 PM ET).
        - Access expiring at the end of 2026.
    - **Chrome Enterprise Premium (Recommended):** Enables "Strict" and "Moderate" device policies that check for:
      - **Device Encryption** (BitLocker/FileVault)
      - **OS Version** (Minimum requirements)
      - **Screen Lock**
      - **Corporate Ownership**
      - **Endpoint Verification** (via Chrome extension)
    - **Basic (No Premium):** Enables "Moderate" and "Lenient" policies based on:
      - **IP Address** (US Region)
      - **Time of Day** (7AM-9PM M-F)
      - **Expiration Date**
    - **Chrome Enterprise Premium & Managed Browsers:** To meet the device policy requirements (especially for `strict_device`), users will typically need to use Chrome browsers managed by your Google Workspace organization through Chrome Enterprise Premium. This allows your organization to enforce security settings, extensions, and report on browser status, which feeds into the Access Context Manager device policy evaluation. Configuration is done within the [Google Workspace Admin Console](https://admin.google.com/) under [Chrome Browser management](https://admin.google.com/ac/chrome/browsers).
      - To collect the necessary device information for Access Context Manager, ensure the **[Endpoint Verification](https://chromewebstore.google.com/detail/callobklhcbilhphinckomhgkigmfocg?utm_source=item-share-cb)** Chrome extension (ID: `callobklhcbilhphinckomhgkigmfocg`) is force-installed on managed browsers. This is extension is added to your users via the "[Apps & extensions](https://admin.google.com/ac/chrome/apps/user)" section within the Chrome Browser management section of the Google Workspace Admin Console.
    - **Cloud Armor:** Regional security policy to allow US traffic and deny others.
    - **Organization Policies:** Enforce security constraints.
    - **IAM policies and Service Accounts:** Follow the principle of least privilege.
    - **Access Context Manager:** Policies defined in `access_policy.tf` for geo-location, time, and device attributes are bound to IAP in `load_balancer.tf`.
      - **Customizable Business Hours:** The time-based access control (used in `moderate_device` and `strict_device` policies) can be customized using variables in your `terraform.tfvars` file:
        - `access_start_hour`: Start hour (0-23 ET, default: 9)
        - `access_end_hour`: End hour (0-23 ET, default: 17)
        - `access_start_day`: Start day (1=Mon, 7=Sun, default: 1)
        - `access_end_day`: End day (1=Mon, 7=Sun, default: 5)

4.  **Data Stores:** CMEK-encrypted GCS buckets and BigQuery datasets for Vertex AI Search, managed by the `discovery-engine` module.

### Deployment Steps

**Recommended:** Use the interactive `deploy.sh` script at the root of the repository.

1.  **Run `deploy.sh`**: Select **Option 1**.
2.  **Follow Prompts**:
    -   **Context:** Script detects Project/Tenant/Environment.
    -   **Access Policies:** Configure Time, Location, and Device trust levels.
    -   **Data Stores:** Interactively add GCS Buckets or BigQuery Datasets.
    -   **Compliance:** Select FedRAMP High (Default) or IL4.
3.  **Apply**: The script runs `terraform init` and `apply` automatically.

### Post-Deployment (Data Ingestion)

After Stage 0 completes, you must populate your created Data Stores.

1.  **Upload Data:** Upload your PDF/HTML/DOCX files to the created GCS buckets or populate your BigQuery tables.
2.  **Import Data:**
    -   Run `deploy.sh`.
    -   Select **Helper Functions (Option 4)**.
    -   Select **3. Import Documents to Gemini Enterprise Data Store**.
    -   Choose the Data Store from the list.
    -   The script will trigger the import job.

**Note:** For BigQuery Web Connectors, the sync is typically automatic based on the schedule, but the initial import can be triggered to speed up indexing.

3.  **Proceed to gemini-stage-1:** Once this stage is fully applied and manual steps are completed, you will run the `gem4gov` CLI to create the application engine, and then deploy the `gemini-stage-1` blueprint to configure the main load balancer frontend & routing rules to your customer instance.

### Outputs

This module provides outputs such as:

- `gcs_discovery_engine_data_stores`: A map of the created GCS-based Data Store names.
- `gcs_gemini_enterprise_data_buckets`: A map of the created GCS bucket names.
- `bq_discovery_engine_data_store_ids`: A map of the Data Store IDs managed by the BigQuery connectors.
- `gemini_enterprise_ip`: The reserved static IP for the load balancer.

These outputs are used by the "gem4gov" CLI tool and the `gemini-stage-1` blueprint.

---

## 7. The gem4gov CLI Tool

### Purpose of `gem4gov`

The `gem4gov` CLI tool is designed to automate and streamline the setup and configuration of Google Cloud components necessary for onboarding government customers to Gemini Enterprise, particularly within regulated environments like FedRAMP High and IL4/IL5.

After the foundational infrastructure is provisioned by the `gemini-stage-0` and `gemini-stage-1` Terraform modules, `gem4gov` takes over to perform the application-level setup within the Google Cloud project.

### How `gem4gov` Interacts After `gemini-stage-0` and `gemini-stage-1`

1.  **Environment Preparation:** `gemini-stage-0` and `gemini-stage-1` create the core resources like networking, service accounts, and the load balancer frontend.
2.  **CLI Execution:** The user runs `gem4gov onboard`.
3.  **Interactive Configuration:** The CLI guides the user through a series of prompts to:
    - **Authenticate:** Ensures the user is logged in with `gcloud` and has the necessary permissions.
    - **Validate Project & APIs:** Confirms the project is set up correctly and required APIs (Vertex AI, Discovery Engine, KMS, etc.) are enabled.
    - **Identity Provider:** Configures either Google Identity or a third-party IdP via Workforce Identity Federation for user access and ACLs.
    - **CMEK Setup:** Registers a Customer-Managed Encryption Key (KMS key in the 'us' multi-region) with Discovery Engine to protect data at rest.
    - **Data Store Creation/Selection:** Allows the user to connect existing Discovery Engine data stores or create new ones from GCS or BigQuery, including schema transformation for BigQuery.
    - **Engine Creation:** Provisions the Gemini Enterprise search engine, linking the selected data stores.
    - **Compliance Configuration:** Adjusts engine and assistant settings to disable features not yet authorized for the selected regulatory boundary (e.g., FedRAMP High), such as disabling certain grounding sources, analytics, and knowledge graph features.
4.  **Output:** Provides the user with essential IDs (Project, Data Store, Engine, Widget Config) and URLs to access the configured Gemini Enterprise instance.

### Key `gem4gov` Functions:

- **Authentication & Role Checks:** Verifies user credentials and IAM roles.
- **API Enablement:** Checks and enables required Google Cloud APIs.
- **Identity Provider Configuration:** Sets up `aclConfig` for Discovery Engine.
- **CMEK Configuration:** Updates `cmekConfig` for Discovery Engine.
- **Data Store Management:** Lists, validates, and creates Discovery Engine data stores (for GCS and BigQuery), including schema handling and data import initiation.
- **Engine Management:** Creates and configures the Discovery Engine (Search Engine).
- **FedRAMP/IL\* Configuration:** Patches Discovery Engine and Assistant resources to disable non-compliant features.

### Prerequisites

Before using this tool, you must have the following:

- **Python 3.6+**
- **Google Cloud SDK (`gcloud`)**: Installed and authenticated.
- **Google Cloud Project**: Created with billing enabled.
- **IAM Roles**: The user running the tool must have the following IAM roles on the project:
    - `roles/discoveryengine.admin`
    - `roles/aiplatform.admin`
    - `roles/serviceusage.serviceUsageAdmin`
    - `roles/storage.admin`
    - `roles/bigquery.admin`
    - `roles/cloudkms.admin` (Required for granting CMEK permissions)
    - `roles/resourcemanager.projectIamAdmin` (Recommended for general IAM management)

- **APIs**: The tool will check for and attempt to enable the following APIs:
    - `aiplatform.googleapis.com`
    - `discoveryengine.googleapis.com`
    - `cloudresourcemanager.googleapis.com`
    - `cloudkms.googleapis.com`
    - `iam.googleapis.com`
    - `serviceusage.googleapis.com`
    - `storage.googleapis.com`
    - `bigquery.googleapis.com`

### Installation

Follow these steps to install the `gem4gov` command-line tool.

#### 1. Install the Package

From the root of the project directory (`gemini-enterprise/gem4gov-cli`), install the package in editable mode:

```bash
pip3 install -e .
```

#### 2. Add to PATH

To run `gem4gov` from any directory, add the installation directory to your PATH.

Find the installation path:
```bash
which pip3
```
*Example output: `/Users/username/Library/Python/3.9/bin/pip3`*

Add the directory (e.g., `/Users/username/Library/Python/3.9/bin`) to your shell configuration (`~/.zshrc` or `~/.bash_profile`):

```bash
export PATH="<your_python_bin_directory>:$PATH"
```

Reload your shell:
```bash
source ~/.zshrc  # or ~/.bash_profile
```

#### 3. Verify Installation

```bash
gem4gov --help
```

### Commands

#### `gem4gov init`

Initializes the CLI and sets the active Google Cloud project.

```bash
gem4gov init
```
**Usage:**
1.  Clears existing project/billing configurations.
2.  Forces re-authentication.
3.  Prompts for the **GCP Project ID**.
4.  Sets the project as the default for `gcloud` and Application Default Credentials (ADC).

#### `gem4gov onboard`

Initiates the interactive onboarding process.

```bash
gem4gov onboard
```

**Step-by-Step Guide:**

1.  **Compliance Regime Selection**: Choose the regulatory boundary (`FedRAMP High`, `IL4`, or `None`).
2.  **Project Confirmation**: Confirm the GCP Project ID and ensure it resides in the appropriate Assured Workloads folder.
3.  **IAM Role Check**: Verifies required IAM roles.
4.  **API Check**: Verifies and enables required APIs.
5.  **Identity Provider Setup**:
    *   **Google Identity**: For Google Workspace users.
    *   **Third-Party (Workforce Identity)**: Requires `Workforce Pool ID` and `Provider ID`.
6.  **CMEK Configuration**:
    *   Checks for existing CMEK in `us` region.
    *   Options: Use existing key, create new key (instructions provided), or continue without CMEK (not recommended for production).
    *   **Note**: Grants `cloudkms.cryptoKeyEncrypterDecrypter` to Discovery Engine and Storage service accounts.
7.  **Application Type Selection**:
    *   **Default**: Chat only.
    *   **Search Engine**: Chat + 1 Data Store.
    *   **Blended Search**: Chat + 2+ Data Stores.
8.  **Data Store Configuration** (if applicable):
    *   **Existing**: Provide IDs of existing data stores.
    *   **New**: Create new **Cloud Storage** or **BigQuery** data stores.
        *   **GCS**: Requires Bucket Name and optional Path Prefix.
        *   **BigQuery**: Requires Dataset, Table, and Schema Mapping (Title, Description, etc.).
9.  **Engine Creation**: Creates the Gemini Enterprise application (Engine).
10. **Compliance Configuration**: Automatically disables features not authorized for the selected compliance regime (e.g., Image Gen, Personalization).
11. **Completion**: Outputs IDs and URLs for the created resources.

#### `gem4gov app create`

Creates a Gemini Enterprise application non-interactively (mostly).
**Note:** You can also trigger this command via the `deploy.sh` script (Option 4).

```bash
gem4gov app create --project-id <PROJECT_ID> [OPTIONS]
```

**Options:**
*   `--project-id`: (Required) GCP Project ID.
*   `--data-stores`: Comma-separated list of existing Data Store IDs.
*   `--workforce-pool-id`: Workforce Identity Pool ID (if using 3rd party IdP).
*   `--workforce-provider-id`: Workforce Identity Provider ID (if using 3rd party IdP).
*   `--compliance-regime`: `FEDRAMP_HIGH`, `IL4`, or `NONE`.

#### `gem4gov app update-compliance`

Updates an existing Gemini Enterprise application to comply with a specific regime.

```bash
gem4gov app update-compliance --project-id <PROJECT_ID> --engine-id <ENGINE_ID> --compliance-regime <REGIME>
```

**Options:**
*   `--project-id`: (Required) GCP Project ID.
*   `--engine-id`: (Required) The ID of the Gemini Enterprise Engine.
*   `--compliance-regime`: (Required) `FEDRAMP_HIGH` or `IL4`.

**Actions:**
*   Disables unauthorized features (e.g., Private Knowledge Graph, Location Context).
*   Updates the Default Search Widget to disable user event collection.
*   Disables Implicit Model Caching for the project.

Upon completion, it will output Project ID, Data Store ID, Engine ID, and the **Widget Config ID** (this is the `customer_id` needed for `gemini-stage-1`). It will also output the `Gemini Enterprise UI URL` that will take you directly to the authentication page of the Gemini Enterprise application. The end users will be redirected to this URL after making it through the security controls on the Load Balncer.

#### `gem4gov app update-idp`

Configures the Identity Provider for a Gemini Enterprise application widget.

```bash
gem4gov app update-idp --project-id <PROJECT_ID> --engine-id <ENGINE_ID> --workforce-pool-id <POOL_ID> --workforce-provider-id <PROVIDER_ID>
```

**Options:**
*   `--project-id`: (Required) GCP Project ID.
*   `--engine-id`: (Required) The ID of the Gemini Enterprise Engine.
*   `--workforce-pool-id`: (Required) Workforce Identity Pool ID.
*   `--workforce-provider-id`: (Required) Workforce Identity Provider ID.

#### `gem4gov datastore import`

Import documents into a Gemini Enterprise data store.

```bash
gem4gov datastore import --project-id <PROJECT_ID> --source-type <SOURCE_TYPE> [OPTIONS]
```

**Options:**
*   `--project-id`: (Required) GCP Project ID.
*   `--source-type`: (Required) Source of documents. Values: `gcs`, `bigquery`.
*   `--data-store-id`: (Optional) The ID of the data store. If not provided, you will be prompted to select one.

**Behavior:**
*   **GCS**: Prompts for the GCS URI (`gs://bucket/path`) and imports documents.
*   **BigQuery**: Not currently supported via this command (use `onboard`).

---

## 8. Stage 1: Application Frontend

This Terraform module (gemini-stage-1) provisions the network frontend components required to expose the Gemini Enterprise application created by the `gem4gov` CLI, building upon the foundation established in the `gemini-stage-0` module.

### Purpose of gemini-stage-1

- **Load Balancer Frontend:** Configures the Regional External Application Load Balancer frontend, including IP address and SSL certificate attachment.
- **Regional NEG Backend:** Defines a Regional Network Endpoint Group (NEG) of type `INTERNET_FQDN_PORT` to point to the Gemini Enterprise service endpoint.
- **Routing Rules with URL Rewrite:** Configures URL map rules for the load balancer. These rules will direct traffic to the NEG and, crucially, perform a **URL rewrite** to include the `gemini_config_id` (obtained from the `gem4gov` CLI output) in the path, like `/us/home/cid/{gemini_config_id}`.
- **Utilize gem4gov Output:** This stage consumes the `gemini_config_id` generated by the `gem4gov` tool as a key part of the URL rewrite configuration.

### Relationship with gemini-stage-0 and gem4gov

- **gemini-stage-0:** This initial stage laid the groundwork, provisioning core infrastructure via Terraform. This includes:

  - Networking foundations (VPC, Subnets).
  - Service Agents and IAM permissions.
  - CMEK keys and configuration.
  - Initial Data Store setup in Discovery Engine.
  - ACL configurations.
  - Reserving a static IP address for the load balancer.

- **gem4gov CLI:** While the `gem4gov` CLI _can_ perform many of the setup tasks covered in `gemini-stage-0` (like API enablement, IdP config, CMEK, Data Store creation), in this blueprint, its primary role _after_ `gemini-stage-0` is to create the Gemini Enterprise **Application (Engine)**. Running `gem4gov onboard` will guide you through this process, ultimately providing a **`config_id`** (referred to as `gemini_config_id` in the variables of this blueprint).

- **gemini-stage-1:** This stage takes the `gemini_config_id` from `gem4gov` and the name of your manually uploaded SSL certificate as inputs to configure the load balancer frontend.

### Prerequisites & Manual Steps Before Applying gemini-stage-1

1.  **Complete gemini-stage-0:** Ensure the `gemini-stage-0` Terraform module has been successfully applied.

2.  **Run `gem4gov onboard`:**

    - Install and run the `gem4gov` CLI tool (see instructions below).
    - Follow the prompts. Since `gemini-stage-0` handled most infrastructure, you will mainly be focused on the **Engine Creation** steps.
    - Note the **`Gemini Enterprise Widget Config ID`** provided in the output. This is your `gemini_config_id`.

3.  **Domain and SSL Certificate:**

    - **DNS Configuration:** You should have already pointed an 'A' record for your desired subdomain (e.g., `gemini.yourdomain.com`) to the static IP address (`gemini-enterprise-ip`) created in `gemini-stage-0`.
    - **Obtain/Upload SSL Certificate:**
      - Acquire an SSL certificate for your subdomain.
      - Upload the SSL certificate to Google Cloud Certificate Manager in the same project where `gemini-stage-0` was deployed. Regional Self-Managed SSL certificates (to be used with a regional load balancer) can **only** be uploaded via `gcloud` command. The certificate will be visible in Certificate Manager as a "Classic certificate".
        - Run the following command:
          ```bash
          gcloud compute ssl-certificates create YOUR_CERTIFICATE_NAME \
            --certificate=PATH_TO_YOUR_CERTIFICATE_FILE \
            --private-key=PATH_TO_YOUR_PRIVATE_KEY_FILE \
            --region=YOUR_REGION
          ```
          Replace `YOUR_CERTIFICATE_NAME`, `PATH_TO_YOUR_CERTIFICATE_FILE`, `PATH_TO_YOUR_PRIVATE_KEY_FILE`, and `YOUR_REGION` accordingly.
        - **Note:** The current Terraform configuration in `load_balancer.tf` uses the `google_compute_region_ssl_certificate` data source, which is compatible with certificates created via this `gcloud` command.
        - For more information on self-managed certificates, see the [Google Cloud documentation](https://docs.cloud.google.com/load-balancing/docs/ssl-certificates/self-managed-certs#createresource).
        - If you create a certificate directly through the Certificate Manager API (non-classic), you would need to adjust the data source in `load_balancer.tf` to `google_certificate_manager_certificates`.

4.  **Update `terraform.tfvars` for gemini-stage-1:**
    - **Recommended:** Run `./deploy.sh` and select **Option 2**. The script will:
      - Detect your Stage 0 configuration.
      - Automatically retrieve `project_id`, `region`, and `domain` from the Stage 0 remote state.
      - Prompt you only for the `gemini_config_id` and `ssl_certificate_name`.
      - Generate the `gemini-stage-1/terraform.tfvars` file for you.
    - **Manual:** Create or update the `terraform.tfvars` file in the `gemini-stage-1` directory with the following:
    ```hcl
    stage_0_state_bucket = "YOUR_STAGE_0_STATE_BUCKET" # From Stage 0 outputs
    gemini_enterprise_domain = "gemini.yourdomain.com"
    gemini_config_id = "OUTPUT_FROM_GEM4GOV_CLI" # Widget Config ID from gem4gov output
    ssl_certificate_name = "YOUR_CERTIFICATE_MANAGER_NAME" # Name of the uploaded cert
    ```

### Inputs

Refer to `variables.tf` for all required input variables. Key inputs from manual steps include `gemini_config_id` and `ssl_certificate_name`.

### Outputs

This module does not have explicit outputs. The Load Balancer IP address is the same as the one reserved in Stage 0 (`gemini_enterprise_ip`).

### Identity-Aware Proxy (IAP) Configuration

**Important:** Identity-Aware Proxy (IAP) is configured in this stage to protect the application. IAP a component that works in conjunction with the Google Cloud Load Balancer. The Load Balancer must be fully provisioned _before_ IAP can be enabled and its IAM policies applied. This is because IAP intercepts traffic handled by the Load Balancer to enforce access controls.

The `google_iap_web_backend_service_iam_member` resources are included in `load_balancer.tf` to ensure they are applied after the load balancer and backend service are created.

---

## 9. Custom Brownfield Deployments (Non-Stellar Engine)

The `deploy.sh` script includes a **Custom Brownfield** option (Option 3) designed for existing GCP environments that do not follow Stellar Engine naming conventions.

### Architectural Prerequisites

Although "Custom Brownfield" allows for flexible naming and discovery, your environment **MUST** still align with the blueprint's architectural expectations to ensure a successful deployment.

1.  **Existing Networking (Shared VPC Pattern):**
    *   The blueprint is designed to integrate into an **existing network**.
    *   You **MUST** set `use_shared_vpc = true` in your `terraform.tfvars`.
    *   You **MUST** provide the following existing resources:
        *   **Network Host Project ID** (`network_project_id`)
        *   **Network Name** (`shared_vpc_network_name`)
        *   **Subnet Name** (`shared_vpc_subnet_name`)
        *   **Proxy Subnet Name** (`shared_vpc_proxy_subnet_name`) - Required for the Internal Load Balancer.
    *   *Note:* If you are using a standalone VPC (not Shared VPC) but still want to reuse it, you can set `network_project_id` to your Service Project ID and provide the local network/subnet names.

2.  **Service Project Attachment:**
    *   Your Service Project (`main_project_id`) must be attached to the Host Project (if using actual Shared VPC).
    *   The subnets must be shared with the Service Project's Service Account (or the project itself).

### Workflow

1.  **Pre-populate `terraform.tfvars`:**
    Manually create and populate `gemini-stage-0/terraform.tfvars` and `gemini-stage-1/terraform.tfvars` with your specific values (e.g., `network_project_id`, `shared_vpc_network_name`, `kms_key_id`).

2.  **Run `deploy.sh` and Select Option 3:**
    ```bash
    ./deploy.sh
    # Select Option 3: Custom Brownfield (Manual Configuration)
    ```
### Configuration Guide: Mapping `tfvars` to Your Environment

To successfully deploy to a custom environment, you must map the variables in `terraform.tfvars` to your existing Google Cloud resources.

#### 1. Networking (Shared VPC or Standalone)
*   **`use_shared_vpc`**: Set to `true`.
*   **`network_project_id`**:
    *   *Shared VPC:* The Project ID of your Host Project.
    *   *Standalone VPC:* The Project ID of your Service Project (where the VPC lives).
*   **`shared_vpc_network_name`**: The name of your existing VPC network (e.g., `my-corp-network`).
*   **`shared_vpc_subnet_name`**: The name of the subnet where Gemini Enterprise resources (like the Load Balancer) will be deployed.
*   **`shared_vpc_proxy_subnet_name`**: The name of the **Regional Managed Proxy Subnet** required for Internal Load Balancers.
    *   *Requirement:* Must be `purpose = REGIONAL_MANAGED_PROXY`.
    *   *Requirement:* Must be in the same region as `region`.

#### 2. Security & Encryption
*   **`kms_key_id`**: The full Resource ID of your existing Customer-Managed Encryption Key (CMEK).
    *   *Format:* `projects/PROJECT/locations/LOCATION/keyRings/RING/cryptoKeys/KEY`
    *   *Usage:* Used to encrypt BigQuery datasets, Discovery Engine stores, and Storage Buckets.
    *   *Permission:* The Service Agents for BigQuery, Discovery Engine, and Storage must have `cloudkms.cryptoKeyEncrypterDecrypter` on this key.
*   **`create_resource_keys`**: (Optional) Set to `false` if you are providing an existing `kms_key_id` and do NOT want Terraform to attempt creating/managing it. Defaults to `true` for Custom Brownfield.
*   **`access_policy_number`**: The numeric ID of your Access Context Manager policy.
    *   *Find it:* Run `gcloud access-context-manager policies list --organization YOUR_ORG_ID`.

#### 3. Identity & Access
*   **`acl_idp_type`**:
    *   `GSUITE`: Use if you sync users to Cloud Identity/Workspace.
    *   `THIRD_PARTY`: Use if you use Workforce Identity Federation (e.g., Okta/Azure AD).
*   **`admin_group` / `user_group`**:
    *   *GSUITE:* The email address of your Google Group (e.g., `group:admins@example.com`).
    *   *THIRD_PARTY:* The Principal Set string (e.g., `principalSet://iam.googleapis.com/.../group/admins`).

#### 4. General Settings
*   **`main_project_id`**: The Project ID where Gemini Enterprise will be deployed.
*   **`region`**: The GCP region for resources (e.g., `us-east4`).
*   **`prefix`**: A short prefix for resource naming (e.g., `genai-`).
3.  **Provide State Bucket:**
    The script will check your `tfvars` for a `bucket` variable. If not found, it will prompt you to enter the name of your existing Terraform State Bucket.

    > [!IMPORTANT]
    > **Security Requirement:** Your State Bucket **MUST** be encrypted with a Customer-Managed Encryption Key (CMEK). The script will validate this and exit if the bucket is not properly encrypted.

4.  **Resource Key Creation:**
    The script will attempt to use the `kms_key_id` defined in your `tfvars`.
    -   If the key exists, it will be used.
    -   If the key does **not** exist (and you have permissions), the script will attempt to **create** the KeyRing and Key for you (similar to Greenfield deployment).
    -   If no key is specified, it defaults to using the same key as the State Bucket.

### Deploying Stage 1 (Load Balancer)

You can also use Option 3 to deploy Stage 1.

1.  **Pre-populate `gemini-stage-1/terraform.tfvars`:**
    Ensure you include the `stage_0_state_bucket` variable so Stage 1 can read the remote state.
    ```hcl
    stage_0_state_bucket     = "my-custom-state-bucket"
    gemini_enterprise_domain = "gemini.example.com"
    ssl_certificate_name     = "my-cert"
    gemini_config_id         = "..."
    ```

2.  **Run `deploy.sh`:**
    *   Select **Option 3** (Custom Brownfield).
    *   Select **Option 2** (Deploy Stage 1).
    *   Enter your State Bucket if prompted (or if not found in stage-0 tfvars).

### Key Differences from Stellar Brownfield
-   **No Auto-Discovery:** Does not attempt to infer Project IDs or scan for "iac-core-0" buckets.
-   **Flexible Networking:** Does not require a Shared VPC. You can specify any VPC/Subnet in your `tfvars`.
-   **Self-Healing Security:** Can auto-create missing CMEK keys for resources, ensuring your deployment meets security standards even in a custom environment.

