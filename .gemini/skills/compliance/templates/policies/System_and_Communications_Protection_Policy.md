# SC - System and Communications Protection Policy and Procedures

## Document Governance & Approval Baseline

| Governance Metric | Policy Standard & Specification |
| :--- | :--- |
| **Document Title** | System and Communications Protection Policy and Procedures |
| **NIST Control Family** | System and Communications Protection (SC) |
| **Primary NIST Benchmark** | NIST SP 800-52 Rev. 2 (TLS), NIST SP 800-77 (IPsec), FIPS 140-3 Cryptography |
| **Target System Name** | {{ SYSTEM_NAME }} ({{ SYSTEM_ABBREVIATION }}) |
| **Security Categorization** | {{ FIPS_199_CATEGORIZATION }} ({{ IMPACT_LEVEL }}) |
| **Governing Entity** | {{ ORGANIZATION }} |
| **Document Owner** | {{ ISSM_NAME }} ({{ ISSM_TITLE }}) |
| **Approval Authority** | {{ AO_NAME }} ({{ AO_TITLE }}) |
| **Review Frequency** | Annual (At least once every 365 days) and upon significant architectural changes |
| **Effective Date** | {{ DATE }} |
| **Policy Version** | {{ VERSION }} |

### Document Authorization Signatures

| Role / Authority | Designated Official | Signature & Date |
| :--- | :--- | :--- |
| **PREPARED BY:** | {{ PREPARED_BY }} | Signature: ______________________ Date: {{ DATE }} |
| **REVIEWED & RECOMMENDED BY:** | {{ ISSO_NAME }}<br>{{ ISSO_TITLE }}, {{ ORGANIZATION }} | Signature: ______________________ Date: {{ DATE }} |
| **REVIEWED & RECOMMENDED BY:** | {{ ISSM_NAME }}<br>{{ ISSM_TITLE }}, {{ ORGANIZATION }} | Signature: ______________________ Date: {{ DATE }} |
| **APPROVED BY:** | {{ SO_NAME }}<br>{{ SO_TITLE }}, {{ ORGANIZATION }} | Signature: ______________________ Date: {{ DATE }} |

### Document Change Record

| Date | Version | Author / Prepared By | Changes Made / Section(s) Description |
| :--- | :--- | :--- | :--- |
| {{ DATE }} | {{ VERSION }} | {{ PREPARED_BY }} | Initial formal baseline institutionalization under NIST SP 800-53 Rev. 5 / {{ COMPLIANCE_BASELINE }} governance. |

### Program Roles & Responsibilities Matrix

| Organizational Role | Assigned Authority | Primary Policy Enforcement & Compliance Responsibilities |
| :--- | :--- | :--- |
| **Authorizing Official (AO)** | {{ AO_NAME }} ({{ AO_TITLE }}) | Formally approves policy statements, risk tolerance thresholds, Exception-to-Policy (ETP) memorandums, and official ATO decisions. |
| **System Owner (SO)** | {{ SO_NAME }} ({{ SO_TITLE }}) | Ensures system operations align with policy requirements, manages operational resources, and approves operational change requests. |
| **ISSM** | {{ ISSM_NAME }} ({{ ISSM_TITLE }}) | Oversees enterprise cybersecurity policy enforcement, manages annual policy review cadences, and maintains compliance evidence. |
| **ISSO** | {{ ISSO_NAME }} ({{ ISSO_TITLE }}) | Conducts continuous security monitoring, audits system configurations, oversees technical countermeasures, and tracks POA&M remediation. |
| **DevSecOps Engineers** | Platform Engineering Team | Implements automated technical controls via Terraform Infrastructure as Code (IaC), CI/CD pipelines, and cloud platform configurations. |

> [!NOTE]
> **Policy Scope & Automation Level**
> This document defines the enterprise security policy and implementation procedures for **System and Communications Protection** under **NIST SP 800-53 Rev. 5 (SC)**.
> Technical infrastructure controls are automatically provisioned and enforced via **{{ SYSTEM_NAME }}** Terraform blueprints.
> Operational rules or contact details requiring manual confirmation are highlighted with RMF Team Callouts.


## 1. Overview

Federal agencies and organizations cannot protect the confidentiality, integrity, and availability of information in today's highly networked systems environment without ensuring that all people involved in using and managing IT:

1. Understand their roles and responsibilities related to the organizational mission;
2. Understand the organization's IT security policy, procedures, and practices; and
3. Have at least adequate knowledge of the various management, operational, and technical controls required and available to protect the IT resources for which they are responsible.

The purpose of this System and Communications Protection Policy is to manage {{ ORGANIZATION }} systems and communications security infrastructure and to protect its information through a defense-in-depth approach to {{ ORGANIZATION }} network security.

This policy addresses the System and Communications Protection (SC) family requirements of NIST Special Publication 800-53 Revision 5, "Security and Privacy Controls for Information Systems and Organizations." A detailed compliance matrix is provided in Appendix A, "Detailed Compliance Matrix."

The System and Communications Protection Policy encompasses all {{ ORGANIZATION }} users who have access to {{ SYSTEM_NAME }}. This policy outlines the framework for establishing, implementing, and maintaining system and communications protection in alignment with applicable {{ GOVERNANCE_REGIME }} guidelines (NIST SP 800-53, FedRAMP, and applicable federal and state regulations), and is consistent with applicable laws, executive orders, directives, regulations, policies, standards, and guidelines. It applies to employees, contractors, and third-party users who handle sensitive information or operate within the {{ ORGANIZATION }} {{ SYSTEM_NAME }} information technology infrastructure.

{{ ORGANIZATION }} management is committed to the requirements of this policy and provides the resources needed to implement them. The ISSM ({{ ISSM_NAME }}) manages the development, documentation, and dissemination of this policy and its procedures, and coordinates their implementation with the Authorizing Official, System Owner, ISSO, and other organizational entities identified in the Program Roles & Responsibilities Matrix.

This policy and its procedures are reviewed and updated at least annually and following significant changes to {{ SYSTEM_NAME }} or its operating environment, security or privacy incidents, assessment or audit findings, or changes in applicable laws, executive orders, directives, regulations, policies, standards, or guidelines.


## 2. Separation of System and User Functionality


### 2.1 IAM Principles

These are the security design principles that guide the IAM settings.

- IAM Policy should be defined as Infrastructure-as-code (IaC) and enforced by code that's reviewed and submitted using Terraform.

  - Latitude will be given to development projects to accelerate the rate of development.

  - No human should have permissions to create or modify cloud resources in User Acceptance Test (UAT) or Quality Assurance (QA) environments that immediately precede production in the Continuous Integration / Continuous Development (CI/CD) pipeline.

  - No human should have permissions to create or modify cloud resources in production.

  - The Cloud Resource Manager access required to execute Terraform code will be assigned to a unique service account.

    - This service account will only be used by the CI/CD pipeline for terraform apply actions.

- Human access

  - Access must be granted to groups, not individual users.

  - Access will be granted based on a minimalized set of curated roles.

- Machine access

  - Individual Service Accounts will be defined for each microservice.

  - Downloadable Service Account keys will not be used and their creation should be disabled by organization policy.

  - Access will be granted based on the principle of least privilege, with only necessary functionality granted for the microservice.

  - Disable automatic role grants to default service accounts (iam.automaticIamGrantsForDefaultServiceAccounts ) should be enabled as organization policy , this will remove the editor role from the default service accounts.

GCP Pre-Defined Roles will be used, custom roles are not recommended due to lifecycle management burdens.


### 2.2 Role Groups

Role Groups are created corresponding to the various development and administrative roles needed to build and maintain the application.

- Roles are identified by development and administrative teams.

- Groups are created for each role and administered by the IAM and Cloud Platform engineering teams. The bootstrap Terraform automation service account is an administrator of these groups to facilitate automated least-privilege role bindings.

- Group naming convention: `gcp-{environment}-{role}@{{ ORGANIZATION_DOMAIN }}` (e.g., `gcp-prod-security-admins@{{ ORGANIZATION_DOMAIN }}`).

- Initial role group memberships needed for system provisioning are checked into Terraform code and applied by the bootstrap Terraform service accounts. Ongoing role group membership management is integrated with {{ ORGANIZATION }} enterprise identity and IAM systems using Terraform IaC automation.



### 2.3 Cloud Service Provider Inherited Controls & Shared Responsibility Boundary

- **Cloud Provider Inherited Controls**: The underlying cloud platform provides physical network isolation, hypervisor and private SDN segmentation (`SC-7`), hardware FIPS 140-2 Level 3 Cloud HSM cryptographic modules (`SC-12`, `SC-13`), and default WAN encryption in transit (`SC-8`).
- **Customer Implementation Responsibilities**: {{ ORGANIZATION }} is responsible for configuring VPC Firewall Rules / Security Groups (`SC-7`), boundary protection perimeters (`SC-7`), Cloud KMS CMEK key rotation (`SC-12`, `SC-28`), Private API Access (`SC-7`), and TLS 1.2 minimum (TLS 1.3 where supported, per NIST SP 800-52 Rev. 2) ingress encryption (`SC-8`).

## 3. Security Function Isolation


### 3.1 Security Analytics and Threat Monitoring

{{ THREAT_DETECTION_IMPLEMENTATION }}


### 3.2 Firewall Rules

Each VPC network implements a distributed virtual firewall. Configure firewall rules that allow or deny traffic to and from the resources attached to the VPC, including Compute Engine VM instances and GKE clusters.

Firewall rules are applied at the VPC level, so they help provide effective protection and traffic control regardless of the operating system your instances use. The firewall is stateful, which means that for flows that are permitted, return traffic is automatically allowed.

Firewall rules are specific to a particular VPC network. The rules allow you to specify the type of traffic, such as ports and protocols, and the source or destination of the traffic, including IP addresses, subnets, tags, and service accounts. For example, you can create an ingress rule to allow any VM instance associated with a particular service account to accept TCP traffic on port 80 that originated from a specific source IP address or CIDR range. Once created firewall rules cannot be renamed so consider your naming convention to support operational needs.

Firewall rules assignment options

Each VPC automatically includes default and implied firewall rules:

- Implied egress rule: An egress rule whose action is ALLOW, destination is 0.0.0.0/0, and priority is the lowest possible (65535) lets any instance send traffic to any destination, except for traffic blocked by GCP. Outbound access may be restricted by creating a higher priority firewall rule.

- Implied deny ingress rule: An ingress rule whose action is DENY, source is 0.0.0.0/0, and priority is the lowest possible (65535) protects all instances by blocking incoming traffic to them. Incoming access may be allowed by a higher priority rule.

The implied rules cannot be removed, but they have the lowest possible priorities. Rules you create can override them as long as your rules have higher priorities (less than 65535).

Firewall Rules Logging allows you to audit, verify, and analyze the effects of your firewall rules. For example, you can determine if a firewall rule designed to deny traffic is functioning as intended. Firewall Rules Logging is also useful if you need to determine how many connections are affected by a given firewall rule.

You enable Firewall Rules Logging individually for each firewall rule whose connections you need to log. Firewall Rules Logging is an option for any firewall rule, regardless of the action (allow or deny) or direction (ingress or egress) of the rule. Firewall Rules Logging is useful if you need to determine the effectiveness of a firewall rule and how many connections are affected by a given firewall rule. For information about viewing logs, see Using Firewall Rules Logging.

When you enable logging for a firewall rule, Google Cloud creates an entry called a connection record each time the rule allows or denies traffic. Each connection record contains the source and destination IP addresses, the protocol and ports, date and time, and a reference to the firewall rule that applied to the traffic. You can view these records in Cloud Logging, and you can export logs to any destination that Cloud Logging export supports.

In addition to firewall rules per VPC there is also the ability to create Hierarchical firewall policies which let you create and enforce a consistent firewall policy across the organization. You can assign hierarchical firewall policies to the organization as a whole or to individual folders.

Hierarchical firewall policies are containers for firewall rules that can explicitly deny or allow connections. In addition, hierarchical firewall policy rules can delegate evaluation to lower-level policies or VPC network firewall rules if desired. Lower-level rules cannot override a rule from a higher place in the resource hierarchy. This lets organization-wide admins manage critical firewall rules in one place.

All rules associated with the organization node are evaluated, followed by those of the first level of folders, and so on. However with Shared VPC the evaluation follows the resource path of the Shared VPC host project, not the service project. Hierarchical firewall policy rules can be targeted to specific VPC networks and VMs by using target resources. This lets you create exceptions for groups of VMs.


### 3.3 Firewall Policy Standards

- Create firewall rules leveraging service accounts as the source or target wherever possible, as this allows for more autonomy for applications teams to scale their resources without requiring additional firewall changes. In addition service accounts are specific to projects and can only be changed on VMs by stopping and starting.

- Limit the use of firewall rules using tags as they can be invoked by simply adding a network tag to a VM and are not specific to any project.

- Where more general firewall rules are required, using a specific subnet or a summarized IP CIDR range is recommended to reduce the complexity of the rules.

- To improve security posture it is recommended to create an egress-deny rule with a higher priority than the implied rules to ensure that both ingress and egress traffic is managed.

- Define a standard naming convention for firewall rules and make use of description metadata to allow those reviewing rules to better understand the intent or history of the rule.

- Firewall rules created by GCP service accounts for services running within {{ ORGANIZATION }} VPCs (e.g., Google Kubernetes Engine) are managed strictly according to verified service architecture and IaC templates.

- Enable Firewall Rules Logging to allow the audit, verification, and analysis the effects of your firewall rules.

- Leverage the Network Intelligence Firewall Insights service which provides visibility into firewall usage and detects firewall configuration issues. Related insights and metrics are also integrated into the Google Cloud Console for the Virtual Private Cloud (VPC) firewall.

- Manage custom firewall rules and configuration centrally, using Infrastructure as Code and Terraform. This provides development teams the ability to manage their rulesets which are approved as part of a CI/CD process by appropriate parties. In addition there is built in auditability and traceability in the process.

- Enforce Hierarchical Firewall Policies centrally across organization folders and environments using Terraform IaC, ensuring consistent baseline perimeter security across all tenant spoke projects.


### 3.4 Data Loss Prevention

To validate and detect sensitive data exposure across containerized workloads and application logs, {{ ORGANIZATION }} enforces Cloud Sensitive Data Protection (Cloud DLP) inspection templates to regularly audit log streams and database stores, generating automated alerting on unintended PII/{{ SENSITIVITY_CLASSIFICATION }} disclosure.


## 4. Information in Shared System Resources

{{ ORGANIZATION }} prevents unauthorized and unintended information transfer via shared system resources across {{ SYSTEM_NAME }}.


### 4.1 Volatile Memory Clearing

Google Compute Engine and Google Kubernetes Engine hypervisors scrub and zeroize physical RAM pages before allocating memory to virtual machines, containers, or serverless execution environments, preventing residual memory inspection across tenants or workloads.


### 4.2 Persistent Disk and Storage Sanitization

Persistent Disk volumes, Cloud Storage objects, and managed database blocks are cryptographically erased and logically zeroized upon deallocation or deletion before underlying storage blocks are returned to the shared storage pool (`SC-4`).


### 4.3 Container and Process Storage Isolation

Ephemeral scratch volumes and volatile cryptographic buffers allocated to application containers are isolated per execution namespace and purged immediately upon pod or instance termination.


## 5. Denial of Service Protection

{{ ORGANIZATION }} utilizes Google Cloud Load Balancing, VPC firewall ingress filtering, and Google Cloud Armor WAF (where authorized within the target accreditation boundary) to mitigate the effects of denial-of-service (DoS/DDoS) attacks (`SC-5`):

- **Volumetric Attacks**: High-volume traffic floods intended to saturate network bandwidth.
- **TCP State-Exhaustion Attacks**: Connection floods targeting load balancers, firewalls, and web servers to exhaust state tables.
- **Application Layer Attacks**: Layer 7 request floods targeting application endpoints to exhaust compute and database resources.

In the event {{ ORGANIZATION }} determines that {{ SYSTEM_NAME }} is under a denial-of-service attack, the {{ ORGANIZATION }} Incident Response Plan (IRP) is initiated and the following five-stage workflow is executed in coordination with {{ CSSP_PROVIDER }} and Google Cloud Support:

### 5.1 Identification, Detection, and Attack Analysis

1. **Detection and Alerting**:
   - Search for traffic patterns exposing known attack signatures (signature detection).
   - Compare observed network traffic parameters against baseline telemetry (anomaly detection).
   - Coordinate with CISA<!-- IF DOD_ENCLAVE --> and USCYBERCOM / {{ CSSP_PROVIDER }}<!-- ENDIF --> for early warnings and indicator notices.
2. **Attack Analysis**:
   - Identify targeted systems, subnets, and services.
   - Determine whether {{ SYSTEM_NAME }} is the primary target or a collateral victim.
   - Extract source IP ranges and Autonomous System Numbers (ASNs) from VPC Flow Logs and load balancer logs.
   - Profile the attack vector using Cloud Monitoring and network traffic analysis tools.
3. **Mitigation Coordination**:
   - Report the attack to {{ CSSP_PROVIDER }} / CISA and request upstream visibility and mitigation support.

### 5.2 Containment, Network Modifications, and Traffic Control

1. **Network Modifications**:
   - Shift traffic to alternate regions or networks using Cloud DNS / load balancer routing.
   - Route ingress traffic through upstream scrubbing and edge proxy services.
2. **Content Delivery and Traffic Control**:
   - Enable caching, proxying, and alternate encrypted communication channels (HA VPN / Dedicated Interconnect).
   - Terminate unauthorized connections and apply strict ingress/egress firewall filters to reduce the attack footprint.

### 5.3 Cloud Service Provider Inherited Controls & Shared Responsibility Boundary (SC-5)

- **Cloud Provider Inherited Controls**: Google Cloud provides global anycast edge absorption, upstream volumetric traffic scrubbing, and underlying Google Cloud Virtual Network software-defined networking (SDN) bandwidth capacity (`SC-5`).
- **Customer Implementation Responsibilities**: {{ ORGANIZATION }} is responsible for configuring VPC firewall ingress rules, load balancer backend capacity thresholds, Cloud Armor WAF rate-limiting policies (where authorized in the accreditation boundary), and alternate VPN/Interconnect failover routing (`SC-5`, `SC-7`).

### 5.4 Remediation, Bandwidth Prioritization, and Sinkholing

1. **Bandwidth Prioritization and Blocking**:
   - Deny connections based on unauthorized geographic origins, IP blocklists, and protocol signatures.
   - Enforce rate limits, maximum burst sizes, and connection throttling on ingress endpoints.
2. **Sinkholing**:
   - Coordinate with {{ CSSP_PROVIDER }} and upstream carriers to sinkhole malicious traffic targeting advertised IP blocks.

### 5.5 Recovery, Rollback, and Post-Incident Review

1. **Normal State Verification and Rollback**:
   - Verify that traffic volume and latency have returned to baseline with no collateral impact before rolling back temporary emergency blocks and restoring normal routing.
2. **Aftermath and Incident Review**:
   - Evaluate response effectiveness, measure operational impact, and update DDoS playbooks and firewall rules based on lessons learned.

### 5.6 Restrict Ability to Attack Other Systems

{{ ORGANIZATION }} restricts individuals and workloads from launching denial-of-service attacks against external systems (`SC-5(1)`) by enforcing default-deny outbound internet egress rules (`0.0.0.0/0` deny egress), VPC Service Controls perimeters, and compute resource quotas.

### 5.7 Capacity, Bandwidth, and Redundancy

{{ ORGANIZATION }} manages network capacity, bandwidth reservations, and multi-zone redundancy to limit the effects of information-flooding denial-of-service attacks (`SC-5(2)`).

### 5.8 Detection and Monitoring

#### 5.8.1 Projects

To access Cloud Monitoring for each environment, a dedicated security/monitoring host project holds centralized dashboards and alerting policies:

| Folder | Monitoring Project |
| :--- | :--- |
| Security | `<prefix>-dev-sec-core-0` |
| Security | `<prefix>-prod-sec-core-0` |

#### 5.8.2 Groups

A dedicated `gcp-monitoring-admins` group is provisioned during the bootstrap process to manage monitoring configurations under least privilege.

#### 5.8.3 Alerts

Alerting policies in Cloud Monitoring evaluate log-based metrics and infrastructure utilization thresholds in real time to notify responders of anomalous traffic spikes or resource exhaustion.

#### 5.8.4 Dashboards

Cloud Monitoring default and custom dashboards correlate network throughput, load balancer request rates, firewall hit counts, and compute utilization across {{ SYSTEM_NAME }}.


## 6. Boundary Protection

### 6.1 Boundary Protection Controls

#### 6.1.1 Cloud Organization Policy

{{ ORGANIZATION }} enforces Organization Policy constraints across the resource hierarchy. Resource hierarchy nodes inherit baseline policies from the root organization node (`inheritFromParent = true`), ensuring mandatory enforcement of uniform security guardrails, CMEK restrictions, and external IP prohibitions across all folders and projects.


#### 6.1.2 Project Layout

All cross-project permission grants are controlled by Cloud IAM and defined in Terraform.

Details about the project layout are documented in the Cloud Project Organization section of this document. As a part of the hub and spoke network architecture, a default VPC service control perimeter is created around the project which hosts the restricted shared VPC.


#### 6.1.3 VPC Service Controls

VPC Service Controls secure and improve the ability to mitigate the risk of data exfiltration from GCP services by defining different controls. These controls include the creation of perimeters that protect resources and the data of services that are explicitly specified. {{ ORGANIZATION }} enforces context-aware access controls (Access Context Manager IP range and device trust policies) for GCP resource access.

A VPC Service Control makes sure that data in most GCP services cannot exit the perimeter to an un-recognized network IP, even if they have the appropriate IAM credentials such as a user account or service account.


#### 6.1.4 Network Control

Workload service projects are attached to the Shared VPC host network. Each service project is allocated dedicated subnets within regional environments. Service accounts are granted `compute.networkUser` permissions strictly on their assigned subnets, enforcing least-privilege IP allocation and network segregation.


#### 6.1.5 Firewall Rules

Hierarchical and VPC firewall rules are defined at the Shared VPC host level and managed strictly via Terraform IaC. By default, all ingress traffic is denied via an explicit default-deny rule. Ingress and egress policies are enforced with strict port, protocol, and CIDR constraints tailored to each landing zone environment (development, non-production, and production).


#### 6.1.6 DNS

{{ SYSTEM_NAME }} deploys private Google Cloud DNS zones for authoritative internal name resolution within VPC boundaries (protected by Google Cloud control-plane integrity) and enables DNSSEC signing on public managed Cloud DNS zones where external resolution is required (`SC-20`, `SC-21`). Forwarding rules and response policies are centrally managed to prevent unauthorized external DNS resolution and DNS tunneling.


#### 6.1.7 Org Policies

There are org policies set to apply additional security to the network:

- compute.vmExternalIpAccess is set to denyAll=true, meaning VMs cannot be created with an external IP address

- compute.skipDefaultNetworkCreation is set to true - Causes Google Cloud to skip the creation of the default network and related resources during Google Cloud project resource creation.

- compute.restrictProtocolForwardingCreationForTypes is set to internal - Causes new forwarding rule objects to be restricted to having target instances with internal IP addresses.

- compute.restrictXpnProjectLienRemoval is set to true - When true, restricts the set of users that can remove a Shared VPC project lien.

- compute.setNewProjectDefaultToZonalDNSOnly is set to true - Newly created projects will use Zonal DNS as default.

- sql.restrictAuthorizedNetworks is set to true - Prevents adding authorized networks for unproxied database access to Cloud SQL instances.

- sql.restrictPublicIp is set to true - Restricts public IP addresses on Cloud SQL instances.


### 6.2 Flow Diagram

Google Cloud Platform (GCP) manages Virtual Private Clouds (VPCs) and inter-network communication using Shared VPC and VPC Network Peering. Shared VPC centralizes network policy and routing control across participating service projects. With Shared VPC, network policy and control for all networking resources are centralized and easier to manage. Service project departments can configure and manage non-network resources, enabling a clear separation of responsibilities for different teams in the organization.

Resources in Shared VPC networks can communicate with each other securely and efficiently across project boundaries using internal IP addresses. You can manage shared network resources—such as subnets, routes, and firewalls—from a central host project, so you can enforce consistent network policies across projects.

As shown in the architecture, {{ ORGANIZATION }} {{ SYSTEM_NAME }} deploys Shared VPC networks (base and restricted) as the foundational networking construct for each environment. Each Shared VPC network is contained within a single project. The base VPC network is used for deploying services that contain non-sensitive data, and the restricted VPC network uses VPC Service Controls to limit access to services that contain sensitive data.

You can implement the model described in the preceding section independently for each of the four environments (common, development, non-production, and production). This model provides the highest level of network segmentation between environments.

For the above scenario, all environments can directly communicate with shared resources in the common environment hub. The common environment can host tooling that requires connectivity to other environments, like CI/CD infrastructure, directories, and security and configuration management tools. As with the previous independent Shared VPC model, the hub-and-spoke scenario is also composed of base and restricted VPC networks. A base Shared VPC hub connects the base Shared VPC network spokes in development, non-production, and production, while the restricted Shared VPC hub connects the restricted Shared VPC network spokes in these same environments. The choice between base and restricted Shared VPC networks also depends on whether VPC Service Controls are required. For workloads with strong data exfiltration mitigation requirements, the hub-and-spoke associated with the restricted Shared VPC networks is preferred.


#### 6.2.1 VPCs

A Virtual Private Cloud (VPC) provides complete network-level isolation for {{ ORGANIZATION }} cloud workloads. {{ ORGANIZATION }} mandates and enforces dedicated VPC networks with custom IP address ranges, non-overlapping subnets, and restricted routing tables to isolate production, staging, and shared management tiers.


#### 6.2.2 Google VPC Network Peering

Google VPC Network Peering connects Virtual Private Clouds (VPCs) within the same project or across separate projects using internal IP addresses without traversing the public internet. Peering traffic remains entirely within Google Cloud's encrypted backbone network without requiring external gateways, providing low-latency, private inter-VPC communication.


#### 6.2.3 Subnet Allocations

Subnet allocation in Google Cloud Platform (GCP) divides the IP address range of Virtual Private Clouds (VPCs) into strictly segmented, non-overlapping subnetworks. Subnets are allocated across dedicated operational environments (Hub/Core Services, Spoke Workloads, and Ingress/Egress DMZs) and bound to specific geographic regions (e.g., {{ PRIMARY_LOCATION }}).

For {{ SYSTEM_NAME }}, active subnets are partitioned into tiered workload boundaries:
- **Tier 1 (Presentation / Ingress DMZ)**: Dedicated subnets for internal load balancers, Cloud IAP proxies, and managed ingress gateways.
- **Tier 2 (Application / Compute)**: Dedicated subnets for containerized services, GKE clusters, and VM instances.
- **Tier 3 (Data / Persistence)**: Dedicated subnets for Cloud SQL, Spanner PSC endpoints, and secure database services.

Subnet CIDR blocks are managed strictly through Terraform Infrastructure-as-Code and enforced via hierarchical firewall policies and VPC Service Controls. Active discovered subnets for the system boundary include: `{{ SUBNET_CIDRS }}`.

Subnets are logical partitions within a VPC that define IP address ranges for resources deployed in specific geographic locations (regions or availability zones). Each subnet is associated with a specific region and availability zone within that region. It is recommended to allocate a subnet for each application workload tier. For example, a Google Kubernetes Engine (GKE) cluster utilizes a dedicated node subnet and two secondary ranges (one for Pods and one for Services). These subnets are declared in the network architecture stage and referenced during workload deployment. Primary VPC IP ranges and subordinate subnet allocations ensure non-overlapping address spaces across interconnected environments.


#### 6.2.4 Google Private Access

Access to Google-managed services, (e.g. AppEngine, CloudSQL, CloudFunctions,) will be routed through internal network space using Google Private Access. Access from Google-managed services to the VPC will be routed through internal network space using Serverless VPC Access. Google Private Access is enabled for subnets.


#### 6.2.5 Interservice Communications

Direct network connections between microservices will be routed within the VPC using Internal Load-Balancing or Google Private Access for managed services. Interservice message quoting will utilize Cloud Pub/Sub for asynchronous delivery.


#### 6.2.6 VPC Firewall Rules

By default, all unsolicited ingress traffic is blocked. Ingress and egress firewall policies are centrally defined and managed via Infrastructure-as-Code modules. Cloud Virtual Private Cloud (VPC) firewall rules and security groups control traffic within the network. Firewall rules are applied in priority order. The first rule that matches the traffic criteria (source IP, destination IP, protocol, port, etc.) is applied, and subsequent rules are not evaluated. Rules specify which protocols (TCP, UDP, ICMP, etc.) and ports (such as 80 for HTTP or 443 for HTTPS) are allowed.


#### 6.2.7 Hub and Spoke architecture

Within Google Cloud Platform (GCP), VPC Network Peering is used to connect VPCs within or between projects in order to execute the Hub and Spoke architecture. A networking design pattern known as "Hub and Spoke" includes setting up Virtual Private Clouds (VPCs) in a centralized hub and outward spoke architecture. A centralized networking hub housing shared resources and services is provided by the hub VPC. Shared services that are accessed by several spoke VPCs, such as logging, security, or monitoring tools, may also be hosted by the hub VPC.

The Spoke VPCs are separate VPC networks that are connected to the hub VPC. Each spoke VPC represents a distinct environment, such as development, testing, or production environments. Spoke VPCs contain the application-specific resources and workloads. They are isolated from each other and communicate with each other through the hub VPC.


#### 6.2.8 Authorization Boundary

The below diagram demonstrates the network authorization boundary for the {{ SYSTEM_NAME }} environment.


## 7. Transmission Confidentiality and Integrity

{{ ORGANIZATION }} {{ SYSTEM_NAME }} provides confidentiality and integrity of information transmission through the use of IAP. All information entering the {{ ORGANIZATION }} enclave does so through the IAP encrypted tunnel.


### 7.1 Cryptographic Protection


#### 7.1.1 Transport Layer Cryptographic Modules

VM-to-VM traffic within Google Cloud Virtual Network infrastructure is encrypted at the network layer using session keys established over Application Layer Transport Security (ALTS, AES-128-GCM by default, using FIPS 140-2 / FIPS 140-3 Level 1 validated cryptographic primitives). Customer-configured service endpoints enforce TLS 1.2 minimum and TLS 1.3 where supported (NIST SP 800-52 Rev. 2), governed by `constraints/gcp.restrictTLSVersion` and load balancer SSL policies where configured in Terraform (`SC-8`, `SC-8(1)`).


#### 7.1.2 Encryption-in-Transit

Microservices will primarily use Cloud Pub/Sub and REST transmission methods within the project system. Both of these protocols leverage HTTPS.


## 8. Network Disconnect

{{ ORGANIZATION }} ensures that network connections associated with a communications session are terminated at the end of the sessions.


## 9. Cryptographic Key Establishment and Management

{{ ORGANIZATION }} documents and implements Google Cloud Key Management Service (KMS) to establish cryptographic keys for required cryptography employed within the {{ ORGANIZATION }} {{ SYSTEM_NAME }}. Google Cloud KMS is used for compliant storage, access, destruction, generation, distribution, and access of all cryptographic keys.


### 9.1 Availability

{{ ORGANIZATION }} will ensure the availability of information on {{ SYSTEM_NAME }} is not compromised in the event of the loss of cryptographic keys by the users.


## 10. Cryptographic Protection

{{ ORGANIZATION }} encrypts all information on {{ SYSTEM_NAME }} within its boundary using FIPS approved algorithms in all encryption protocols.


## 11. Collaborative Computing Devices and Applications

{{ ORGANIZATION }} prohibits remote activation of collaborative computing devices.


## 12. Transmission of Security and Privacy Attributes

Security and privacy attributes are used to implement access control and information flow control policies; reflect special dissemination, management, or distribution instructions, including permitted uses of personally identifiable information; or support other aspects of the information security and privacy policies.

{{ ORGANIZATION }} associates all security and privacy attributes with information that is exchanged between {{ SYSTEM_NAME }} and its system components.


### 12.1 Integrity Verification

Part of verifying the integrity of transmitted information is ensuring that security and privacy attributes that are associated with such information have not been modified in an unauthorized manner. Unauthorized modification of security or privacy attributes can result in a loss of integrity for transmitted information.

{{ ORGANIZATION }} employs Google Binary Authorization & Cloud Audit Logs to verify the integrity of transmitted security and privacy attributes.


### 12.2 Anti-Spoofing Mechanisms

{{ ORGANIZATION }} implements Google Access Context Manager & VPC Service Controls to prevent adversaries from falsifying security attributes.


### 12.3 Cryptographic Binding

Cryptographic mechanisms and techniques can provide strong security and privacy attribute binding to transmitted information to help ensure the integrity of such information.

{{ ORGANIZATION }} implements TLS 1.2+ / IPsec VPN encryption to bind security and privacy attributes to transmitted information.


## 13. Public Key Infrastructure Certificates

{{ ORGANIZATION }} {{ SYSTEM_NAME }} does not issue public key certificates but is permitted to obtain public key certificates from approved service providers.


## 14. Mobile Code

{{ ORGANIZATION }} {{ SYSTEM_NAME }} does not use mobile code, therefore, this control is not applicable.


## 15. Secure Name/Address Resolution Service (Authoritative Source)

For authoritative name resolution (`SC-20`), {{ SYSTEM_NAME }} leverages Google Cloud DNS. Where public managed DNS zones are deployed, DNSSEC signing (with automated Key-Signing Key and Zone-Signing Key management) is enabled to provide data origin authentication and integrity verification artifacts and to establish a cryptographic chain of trust for child zones. Internal VPC name resolution uses private Cloud DNS zones isolated within the Google Cloud control plane.


## 16. Secure Name/Address Resolution Service (Recursive or Caching Resolver)

For recursive and caching name resolution (`SC-21`), {{ SYSTEM_NAME }} uses Google Cloud DNS VPC resolvers, which automatically request and perform DNSSEC data origin authentication and integrity validation on responses received from signed authoritative DNS servers.


## 17. Architecture and Provisioning for Name/Address Resolution Service

The name/address resolution architecture for {{ SYSTEM_NAME }} (`SC-22`) is provisioned on Google Cloud DNS, which operates a globally distributed, anycast fault-tolerant infrastructure. Internal/external role separation is enforced by isolating internal workload records within VPC-scoped private Cloud DNS zones that are unreachable from external networks, while external resolution (where authorized) is served from separate public managed zones.


## 18. Session Authenticity

Protecting session authenticity addresses communications protection at the session level. Such protection establishes grounds for confidence at both ends of communications sessions in the ongoing identities of other parties and the validity of transmitted information.

Authenticity protection includes protecting against "man-in-the-middle" attacks, session hijacking, and the insertion of false information into sessions.

{{ ORGANIZATION }} {{ SYSTEM_NAME }} is configured to protect the authenticity of communications sessions through implementation of the IAP and NIST SP 800-53 Rev. 5 and FedRAMP approved cloud security configurations.


### 18.1 Invalidate Session Identifiers at Logout

{{ ORGANIZATION }} invalidates session identifiers at logout to curtail the ability of adversaries to capture and continue to employ previously valid session IDs.


### 18.2 Unique System-generated Session Identifiers

{{ ORGANIZATION }} generates unique session identifiers to curtail the ability of adversaries to reuse previously valid session IDs. {{ SYSTEM_NAME }} only recognizes session identifiers that are system-generated.


### 18.3 Allowed Certificate Authorities

{{ ORGANIZATION }} only allows the following certificate authorities for verification of the establishment of protected sessions:

- Google Cloud Certificate Authority Service (CAS)

- Federal / DoD Approved PKI Root CA

- Google Trust Services (GTS) / Organization-Approved Enterprise PKI CA


## 19. Fail in Known State

Failure in a known state addresses security concerns in accordance with the mission and business needs of organizations. Failure in a known state prevents the loss of confidentiality, integrity, or availability of information in the event of failures of organizational systems or system components.

{{ ORGANIZATION }} {{ SYSTEM_NAME }} fails to a known state to preserve the confidentiality, integrity, and availability of information and prevents injury or destruction of property; and facilitates {{ SYSTEM_NAME }} restart and return to the operational mode with less disruption of mission and business processes.


## 20. Protection of Information at Rest

Information at rest refers to the state of information when it is located on storage devices as specific components of information systems.

All information at rest on {{ SYSTEM_NAME }} is to be encrypted and protected.

All {{ ORGANIZATION }} {{ SYSTEM_NAME }} disks are encrypted at rest through the configurations of Google Cloud Compute Engine. Google Cloud Storage, in use, utilizes customer managed encryption keys.


### 20.1 Cryptographic Protection & Keys


#### 20.1.1 Encryption-at-Rest

All data stored in Google Cloud is encrypted at the storage level using AES-256 with Google-managed data encryption keys (DEK). Google Cloud uses its common cryptographic library incorporating a FIPS 140-validated Google BoringCrypto module (see CSP authorization package cryptographic module inventory).


#### 20.1.2 Customer-Managed Encryption Keys (CMEK)

Where required by the system security categorization, {{ SYSTEM_NAME }} wraps data encryption keys with Customer-Managed Encryption Keys (CMEK) managed in Google Cloud Key Management Service (Cloud KMS) backed by FIPS 140-2 Level 3 validated Hardware Security Modules (Cloud HSM manufactured by Marvell [formerly Cavium]; `[CONFIG_REQUIRED: CMVP certificate number from the Google Cloud FedRAMP/DoD package cryptographic module inventory or the Cloud HSM key attestation certificate chain]`).


## 21. Operations Security

Operations security (OPSEC) is a systematic process by which potential adversaries can be denied information about the capabilities and intentions of organizations by identifying, controlling, and protecting generally unclassified information that specifically relates to the planning and execution of sensitive organizational activities. OPSEC controls protect the confidentiality of information, including limiting the sharing of information with suppliers, potential suppliers, and other non-organizational elements and individuals.

Throughout the system development life cycle, {{ ORGANIZATION }} developers practice operations security to: identify critical information, analyze threats, analyze vulnerabilities, assess risks, and apply appropriate countermeasures.


## 22. Process Isolation

{{ ORGANIZATION }} maintains a separate execution domain for each executing system process.

### 22.1 Source Code and Execution Domain Isolation

#### 22.1.1 Version Control Repositories

Source code and infrastructure blueprints for {{ SYSTEM_NAME }} are maintained in secured enterprise Git repositories enforcing branch protection rules, cryptographically verified commits, and mandatory peer code review workflows.


#### 22.1.2 Branching Strategy

Our development process follows a trunk-based branching strategy. This entails having a protected main branch, with engineers creating scoped feature/bugfix branches that are validated through automated CI/CD security gates before merging into the main branch.


#### 22.1.3 Validation

Currently, development happens on feature and bug fix branches. When complete, a pull request (PR), (also known as a merge request (MR)), can be opened targeting the main branch. After two reviewers have submitted comments, and their recommendations have been adjudicated, (which can be an iterative process), the feature branch is merged into the main branch.


## 23. Port and I/O Device Access

{{ ORGANIZATION }} disables or removes connection ports and I/O devices to help prevent the exfiltration of information from {{ SYSTEM_NAME }} and the introduction of malicious code from those ports or devices.

Connection ports include Universal Serial Bus (USB), Thunderbolt, and Firewire (IEEE 1394). Input/output (I/O) devices include compact disc and digital versatile disc drives.


## 24. System Time Synchronization

{{ ORGANIZATION }} synchronizes {{ SYSTEM_NAME }} clocks within and between all {{ SYSTEM_NAME }} components.


### 24.1 Synchronization with Authoritative Time Source

{{ ORGANIZATION }} uses Google TrueTime NTP Servers as the authoritative time source for {{ SYSTEM_NAME }}. When the time difference between {{ SYSTEM_NAME }} and Google TrueTime NTP Servers is greater than 1 second, {{ ORGANIZATION }} must synchronize the internal system clocks.


## 25. Alternate Communications Path

An incident, whether adversarial- or non adversarial-based, can disrupt established communications paths used for system operations and organizational command and control. Alternate communications paths reduce the risk of all communications paths being affected by the same incident.

{{ ORGANIZATION }} uses Secondary Dedicated Cloud Interconnect / HA VPN Tunnel as an alternative communication path when the primary communication path is disrupted.



## Appendix A – Detailed Compliance Matrix

The following table provides detailed traceability between the policy implementation statements in this document, the authoritative NIST SP 800-53 Rev. 5 control requirements, DoD CCIs, and the technical/governance enforcement mechanisms active across {{ SYSTEM_NAME }}.


| CTRL ID | CTRLTITLE | REQUIRED {{ GRC_STANDARD_LABEL }} STANDARD | DOCREF | ENFORCEMENT MECHANISM |
| :--- | :--- | :--- | :--- | :--- |
| SC-01 | Policy and Procedures | Develops, documents, and disseminates SC policy/procedures to ISSO/ISSM; designates ISO/PM; reviews annually and upon system changes, new threats, breaches, or policy updates. (CCI-001075, CCI-001076, CCI-001077, CCI-001079, CCI-001080, CCI-001081, CCI-002378, CCI-002380, CCI-004852, CCI-004853, CCI-004854, CCI-004855, CCI-004856, CCI-004857, CCI-004858, CCI-004859, CCI-004860, CCI-004861, CCI-004862, CCI-004863, CCI-004864) | Section 1 | eMASS governance publication (System ID: {{ RMF_PACKAGE_ID }}); annual review cadence managed by ISO/PM, ISSM, and ISSO; trigger alignment with DoDI 8510.01 and DoDI 8500.01. |
| SC-02 | Separation of System and User Functionality | Separates user functionality from system administrative and security management functions. (CCI-001082) | Section 2 | {{ IDENTITY_PROVIDER }} with {{ MFA_MECHANISM }}, project boundary isolation across network transport and telemetry logging, and role-based access control. |
| SC-03 | Security Function Isolation | Isolates security functions from non-security functions to maintain system integrity. (CCI-001084) | Section 3 | Multi-project landing zone topology, centralized machine identity management, and IAM conditions on Resource Manager Tags. |
| SC-04 | Information in Shared System Resources | Prevents unauthorized residual information transfer across shared system resources (RAM, persistent disks). (CCI-001090) | Section 4 | Google Compute Engine automated memory clearing, persistent disk zero-overwriting, and volatile cryptographic buffer flushing. |
| SC-05 | Denial-of-service Protection | Protects against/limits effects of network and application DoS/DDoS attacks via ingress/egress filtering, rate limiting, and anomaly detection. (CCI-001093, CCI-002385, CCI-004866, CCI-004867) | Section 5 | Google Cloud Armor WAF, Cloud Load Balancing, stateful VPC firewall rules, and automated traffic scrubbing. |
| SC-05(01) | Restrict Ability to Attack Other Systems | Restricts individuals from launching DoS/DDoS attacks against other systems. (CCI-001094, CCI-002387) | Section 5 | Outbound internet deny rules (0.0.0.0/0 deny egress) and VPC Service Controls egress restrictions per DoDI 8500.01. |
| SC-05(02) | Capacity, Bandwidth, and Redundancy | Manages capacity, bandwidth, and redundancy to limit effects of information flooding attacks. (CCI-001095) | Section 5 | Dual {{ INTERCONNECT_TYPE }} circuits, dynamic BGP ECMP routing, and auto-scaling telemetry collectors. |
| SC-05(03) | Detection and Monitoring | Monitors CPU, memory, bandwidth, and sessions using IDS/IPS and SIEM to detect DoS indicators. (CCI-002388, CCI-002389, CCI-002390, CCI-002391) | Section 5 | Real-time Cloud Monitoring alerting, {{ ORGANIZATION }} NetOps telemetry analysis, and {{ CSSP_PROVIDER }} 24x7 CSSP sensor monitoring per DoDI 8530.01. |
| SC-07 | Boundary Protection | Logically monitors and controls communications at external and key internal boundaries. (CCI-001097, CCI-001098, CCI-002395, CCI-004868) | Section 17 | NCC Global Hub, Central Transit VPC Cloud Routers, virtual network security appliances, and multi-NIC VDSS inspection boundaries (ETP-{{ SYSTEM_NAME }}-01/02). |
| SC-07(03) | Access Points | Limits number of external network connections and access points. (CCI-001101) | Section 17 | Consolidated transit VPC architecture aggregating 7 initial spokes through centralized Cloud Routers. |
| SC-07(04) | External Telecommunications Services | Governs external telecom connections; reviews traffic flow exceptions at least weekly. (CCI-001102, CCI-001103, CCI-001105, CCI-001106, CCI-001107, CCI-001108, CCI-002396, CCI-004869, CCI-004870, CCI-004871) | Section 17 | Weekly ISSO firewall exception review cadence; Cross-Cloud Interconnect SLAs with AWS and Azure. |
| SC-07(05) | Deny by Default — Allow by Exception | Denies network traffic by default and allows traffic by exception at managed interfaces for all systems. (CCI-001109, CCI-004872) | Section 17 | Default VPC implied deny ingress rules (priority 65535) overridden only by explicit, documented firewall allows. |
| SC-07(07) | Split Tunneling for Remote Devices | Prevents split tunneling for remote devices; routes all traffic through DoDIN connection. (CCI-002397, CCI-004873) | Section 17 | Mandatory authorized Virtual Desktop (AVD) / enterprise VPN gateway routing per DoDI 8100.04; full tunnel enforcement. |
| SC-07(08) | Route Traffic to Authenticated Proxy Servers | Routes internal web traffic to external networks through authenticated proxy servers. (CCI-001112, CCI-001113, CCI-001114) | Section 17 | Authenticated egress proxies and Identity-Aware Proxy (IAP) integration at managed boundary gateways. |
| SC-07(09) | Restrict Threatening Outgoing Communications Traffic | Restricts outgoing communications traffic containing potential threats. (CCI-002398, CCI-002399, CCI-002400) | Section 17 | Virtual network appliance deep packet inspection and VDSS traffic filtering. |
| SC-07(10) | Prevent Exfiltration | Prevents data exfiltration; conducts exfiltration tests at least annually. (CCI-001116, CCI-004874, CCI-004875) | Section 17 | VPC Service Controls perimeters blocking external data movement; annual exfiltration penetration testing per DoDI 8500.01. |
| SC-07(11) | Restrict Incoming Communications Traffic | Restricts incoming traffic to explicitly defined IP ranges and internal destinations documented in PPSM. (CCI-002401, CCI-002402, CCI-002403) | Section 17 | Strict VPC firewall ingress rules matching the authorized PPSM registry; public ICMP blocking. |
| SC-07(12) | Host-based Protection | Implements host-based boundary protection on all capable components. (CCI-002404, CCI-002405, CCI-002406) | Section 17 | DoD-approved endpoint protection software, OS firewalls, and GCP VM Manager policy enforcement. |
| SC-07(13) | Isolation of Security Tools, Mechanisms, and Support Components | Isolates security tools (PKI, CSSP sensors, logging) on separate subnetworks with managed interfaces. (CCI-001119, CCI-001120) | Section 17 | Dedicated security and telemetry VPC subnets isolated from transit payload routing. |
| SC-07(14) | Protect Against Unauthorized Physical Connections | Protects managed interfaces crossing security domains from unauthorized physical connections. (CCI-001121, CCI-002407) | Section 17 | Inherited Google IL5 datacenter physical security; locked enterprise colocation cages with MACsec encryption. |
| SC-07(15) | Networked Privileged Accesses | Restricts network privileged access to authorized administrators. (CCI-001123) | Section 17 | {{ IDENTITY_PROVIDER }} with {{ MFA_MECHANISM }}, GCP PAM, and custom role blueprints (e.g. {{ SYSTEM_NAME }}-NetworkAdmins). |
| SC-07(18) | Fail Secure | Prevent the system from entering an unsecure state in the event of an operational failure of a boundary protection device (fail-secure). (CCI-001126) | Section 6 | Stateful VPC firewall default-deny rules, VPC Service Controls fail-closed perimeter evaluation, and HA boundary appliance failover. |
| SC-07(20) | Dynamic Isolation and Segregation | Provide the capability to dynamically isolate system components from other components when compromises or anomalies are detected. (CCI-002410, CCI-002411) | Section 6 | Automated and runbook-driven VPC firewall tag/service-account quarantine rules, GKE NetworkPolicy isolation, and VPC Service Controls perimeter updates. |
| SC-07(21) | Isolation of System Components | Employ boundary protection mechanisms to isolate system components supporting different missions or business functions. (CCI-002413, CCI-002414, CCI-002415) | Section 6 | Environment- and tier-segregated Shared VPC projects, dedicated subnets ({{ SUBNET_CIDRS }}), and VPC Service Controls perimeters isolating mission workloads. |
| SC-07(25) | Unclassified National Security System Connections | Prohibits unclassified NSS from connecting to external networks without a DoDIN-approved boundary security system (VDSS). (CCI-004881, CCI-004882, CCI-004883) | Section 17 | Mandatory VDSS boundary traffic inspection under approved Exception-to-Policy (ETP-{{ SYSTEM_NAME }}-01). |
| SC-07(28) | Connections to Public Networks | Prohibits direct connection of all system components to public networks. (CCI-004889, CCI-004890) | Section 17 | compute.vmExternalIpAccess = denyAll organization policy; zero public IP assignments on VPC instances. |
| SC-07(29) | Separate Subnets to Isolate Functions | Implements logical subnetworks to isolate critical functions (server enclaves, databases). (CCI-004891, CCI-004892) | Section 17 | Structured VPC subnetworks and dedicated transit/workload subnets ({{ SUBNET_CIDRS }}). |
| SC-08 | Transmission Confidentiality and Integrity | Protects confidentiality and integrity of information in transit across internal and external networks. (CCI-002418) | Section 7 | Layer 2 MACsec on {{ INTERCONNECT_TYPE }}, Layer 3 IPsec VPN encapsulation, ALTS network-layer encryption within the VPC, and TLS 1.2 minimum (TLS 1.3 where supported, per NIST SP 800-52 Rev. 2) across external transit streams. |
| SC-08(01) | Cryptographic Protection | Implements cryptographic protection to prevent unauthorized disclosure and detect changes in transit. (CCI-002421) | Section 7 | Hardware MACsec (gcm-aes-xpn-256), virtual appliance IPsec (AES-256-GCM), and Google BoringCrypto TLS 1.2/1.3 (CMVP FIPS 140-3 Cert #5104, Security Level 1, retrieved 2026-10-15). |
| SC-08(02) | Pre- and Post-transmission Handling | Maintains confidentiality and integrity of information during pre- and post-transmission handling. (CCI-002420, CCI-002422) | Section 7 | End-to-end payload encapsulation and volatile memory encryption buffers within virtual network security appliances. |
| SC-10 | Network Disconnect | Terminates network connection at session end or after {{ ODP_SC_10_INACTIVITY_TIMEOUT }} of inactivity. (CCI-001133, CCI-001134) | Section 8 | Automated 15-minute idle session disconnect enforced across GCP console, SSH, and IAP sessions. |
| SC-11 | Trusted Path | Establishes logical trusted path for authentication, password changes, and enrollment per DoDI 8520.03. (CCI-001135, CCI-001661, CCI-004895) | Section 8 | IAP-encrypted administrative tunnels and {{ IDENTITY_PROVIDER }} with {{ MFA_MECHANISM }}. |
| SC-12 | Cryptographic Key Establishment and Management | Adheres to NIST FIPS/NSA requirements for key generation, distribution, storage, access, and destruction. (CCI-002428, CCI-002429, CCI-002430, CCI-002431, CCI-002432, CCI-002433, CCI-002434, CCI-002435, CCI-002436, CCI-002437, CCI-002438, CCI-002439, CCI-002440, CCI-002441, CCI-002442) | Section 9 | Google Cloud KMS FIPS 140-2 Level 3 Cloud HSM key rings where hardware protection is configured (software-backed Cloud KMS keys use Google BoringCrypto FIPS 140-3 Level 1 primitives), organization-defined key rotation, and secure key transfers. |
| SC-12(01) | Availability | Ensures availability of information in the event of cryptographic key loss. (CCI-001139) | Section 9 | Multi-region Cloud KMS HSM replication across {{ PRIMARY_LOCATION }} and {{ SECONDARY_LOCATION }}. |
| SC-12(06) | Physical Control of Keys | Enforce physical control of keys requirements across {{ SYSTEM_NAME }} in accordance with NIST SP 800-53 Rev. 5 SC-12(6). (CCI-004899) | Section 3 | Enforced via Google Cloud infrastructure controls, Terraform configuration baselines, and ISSM/ISSO governance verification. |
| SC-13 | Cryptographic Protection | Employs NSA-approved / FIPS-validated cryptography for authentication, encryption, and non-repudiation. (CCI-002449, CCI-002450, CCI-004900) | Section 10 | FIPS-validated cryptographic modules: Cloud HSM (FIPS 140-2 Level 3 validated hardware security modules manufactured by Marvell [formerly Cavium], `[CONFIG_REQUIRED: CMVP certificate number from CSP package or key attestation chain]`) where hardware protection is configured; software-backed cryptographic primitives use Google BoringCrypto (CMVP FIPS 140-3 Cert #4735, Level 1, retrieved 2026-10-15). |
| SC-15 | Collaborative Computing Devices and Applications | Prohibits remote activation of collaborative computing devices (cameras, microphones). (CCI-001150, CCI-001151, CCI-001152) | Section 11 | Hardware absence on cloud virtual machines and network switches; isolated physical VTC suites. |
| SC-16 | Transmission of Security and Privacy Attributes | Associates security/privacy attributes ({{ SENSITIVITY_CLASSIFICATION }} markings, {{ IMPACT_LEVEL }}) with information exchanged across interfaces. (CCI-001157, CCI-002454, CCI-002455, CCI-004901, CCI-004902, CCI-004903) | Section 12 | Automated Terraform IaC tagging, packet encapsulation metadata, and BigQuery table labels. |
| SC-16(01) | Integrity Verification | Verifies integrity of transmitted security and privacy attributes. (CCI-001158, CCI-004904) | Section 12 | Google Binary Authorization, Cloud Audit Logging, and HMAC integrity hashing. |
| SC-16(02) | Anti-spoofing Mechanisms | Implements anti-spoofing mechanisms to prevent adversaries from falsifying security attributes. (CCI-004905) | Section 12 | Access Context Manager and VPC Service Controls ingress condition enforcement. |
| SC-16(03) | Cryptographic Binding | Enforce cryptographic binding requirements across {{ SYSTEM_NAME }} in accordance with NIST SP 800-53 Rev. 5 SC-16(3). (CCI-004906, CCI-004907, CCI-004908) | Section 3 | Enforced via Google Cloud infrastructure controls, Terraform configuration baselines, and ISSM/ISSO governance verification. |
| SC-17 | Public Key Infrastructure Certificates | Issues public key certificates under DoDI 8520.02 via approved PKI CAs. (CCI-001159, CCI-002456, CCI-004909) | Section 13 | {{ PKI_TRUST_TYPE }}, Federal Bridge CA, and Google Cloud Certificate Authority Service (CAS). |
| SC-18 | Mobile Code | Prohibits unacceptable mobile code; blocks automatic execution in scriptable applications. (CCI-001160, CCI-001163, CCI-001164, CCI-001165) | Section 14 | Mobile code execution disabled on virtual hosts; user authorization required for scripts per DoDI 8500.01. |
| SC-18(01) | Identify Unacceptable Code and Take Corrective Actions | Enforce identify unacceptable code and take corrective actions requirements across {{ SYSTEM_NAME }} in accordance with NIST SP 800-53 Rev. 5 SC-18(1). (CCI-001166, CCI-001662, CCI-002457, CCI-002458) | Section 3 | Enforced via Google Cloud infrastructure controls, Terraform configuration baselines, and ISSM/ISSO governance verification. |
| SC-18(02) | Acquisition, Development, and Use | Enforce acquisition, development, and use requirements across {{ SYSTEM_NAME }} in accordance with NIST SP 800-53 Rev. 5 SC-18(2). (CCI-001167, CCI-001168, CCI-001687, CCI-001688) | Section 3 | Enforced via Google Cloud infrastructure controls, Terraform configuration baselines, and ISSM/ISSO governance verification. |
| SC-18(03) | Prevent Downloading and Execution | Enforce prevent downloading and execution requirements across {{ SYSTEM_NAME }} in accordance with NIST SP 800-53 Rev. 5 SC-18(3). (CCI-001169, CCI-001695, CCI-002459) | Section 3 | Enforced via Google Cloud infrastructure controls, Terraform configuration baselines, and ISSM/ISSO governance verification. |
| SC-18(04) | Prevent Automatic Execution | Enforce prevent automatic execution requirements across {{ SYSTEM_NAME }} in accordance with NIST SP 800-53 Rev. 5 SC-18(4). (CCI-001170, CCI-001171, CCI-001172, CCI-002460) | Section 3 | Enforced via Google Cloud infrastructure controls, Terraform configuration baselines, and ISSM/ISSO governance verification. |
| SC-20 | Secure Name/Address Resolution Service (Authoritative Source) | Provide additional data origin authentication and integrity verification artifacts along with authoritative name resolution data, and provide the means to indicate the security status of child zones. (CCI-001178, CCI-001179, CCI-001663, CCI-002462) | Section 15 | Google Cloud DNS managed public zones with DNSSEC signing (KSK/ZSK) enabled and VPC-scoped private Cloud DNS zones protected within the Google Cloud control plane. |
| SC-21 | Secure Name/Address Resolution Service (Recursive or Caching Resolver) | Request and perform data origin authentication and data integrity verification on the name/address resolution responses the system receives from authoritative sources. (CCI-002465, CCI-002466, CCI-002467, CCI-002468) | Section 16 | Google Cloud DNS recursive resolvers performing automatic DNSSEC validation on responses from signed external zones. |
| SC-22 | Architecture and Provisioning for Name/Address Resolution Service | Ensure the systems that collectively provide name/address resolution service for the organization are fault-tolerant and implement internal and external role separation. (CCI-001182, CCI-001183) | Section 17 | Anycast, multi-region fault-tolerant Google Cloud DNS infrastructure with strict separation between internal private VPC DNS zones and external public DNS resolution. |
| SC-23 | Session Authenticity | Protects session authenticity using FIPS 140-validated random session IDs, invalidates at logout, trusts DoD CAs. (CCI-001184) | Section 18 | IAP session tokens generated with FIPS randomness, immediate token invalidation on logout, and {{ PKI_TRUST_TYPE }} trust anchors. |
| SC-23(01) | Invalidate Session Identifiers at Logout | Enforce invalidate session identifiers at logout requirements across {{ SYSTEM_NAME }} in accordance with NIST SP 800-53 Rev. 5 SC-23(1). (CCI-001185) | Section 3 | Enforced via Google Cloud infrastructure controls, Terraform configuration baselines, and ISSM/ISSO governance verification. |
| SC-23(03) | Unique System-generated Session Identifiers | Enforce unique system-generated session identifiers requirements across {{ SYSTEM_NAME }} in accordance with NIST SP 800-53 Rev. 5 SC-23(3). (CCI-001188, CCI-001189, CCI-001664) | Section 3 | Enforced via Google Cloud infrastructure controls, Terraform configuration baselines, and ISSM/ISSO governance verification. |
| SC-23(05) | Allowed Certificate Authorities | Enforce allowed certificate authorities requirements across {{ SYSTEM_NAME }} in accordance with NIST SP 800-53 Rev. 5 SC-23(5). (CCI-002469, CCI-002470) | Section 3 | Enforced via Google Cloud infrastructure controls, Terraform configuration baselines, and ISSM/ISSO governance verification. |
| SC-24 | Fail in Known State | Fails to a known secure state across all failure types on all system components, preserving state info. (CCI-001190, CCI-001191, CCI-001192, CCI-001193, CCI-001665) | Section 19 | Fail-closed stateful firewall filtering, BGP sub-second BFD reconvergence, and persistent error logging. |
| SC-28 | Protection of Information at Rest | Protects confidentiality and integrity of all info at rest across components/media using FIPS cryptography. (CCI-001199, CCI-002472) | Section 20 | Mandatory AES-256 Cloud KMS CMEK encryption on Compute disks, GCS buckets, Cloud SQL, and BigQuery. |
| SC-28(01) | Cryptographic Protection | Implements FIPS-validated cryptographic mechanisms to prevent unauthorized disclosure and modification of information at rest on all system components and media that store system or customer data. (CCI-002473, CCI-002474, CCI-002475, CCI-002476) | Section 20 | AES-256 Cloud KMS customer-managed encryption keys (CMEK) on Compute Engine disks, Cloud Storage buckets, Cloud SQL, and BigQuery datasets. |
| SC-28(02) | Offline Storage | Moves backups, old logs, and inactive keys to secure offline storage. (CCI-002477, CCI-002478, CCI-002479) | Section 20 | Cloud Storage Archive tier with Object Retention Lock for long-term audit and backup archives per DoDI 8510.01. |
| SC-28(03) | Cryptographic Keys | Protects cryptographic keys in hardware key stores backed by FIPS 140-validated cryptographic modules. (CCI-004910, CCI-004911) | Section 20 | Where Cloud HSM is configured, cryptographic keys are protected in FIPS 140-2 Level 3 validated hardware security modules manufactured by Marvell (formerly Cavium) per NIST SP 800-53 Rev. 5 SC-12 and SC-28(3); software-backed Cloud KMS keys use Google BoringCrypto (FIPS 140-3 Level 1, CMVP Cert #4735). |
| SC-38 | Operations Security | Employs OPSEC controls (access controls, marking, need-to-know) across SDLC per DoDD 5205.02E. (CCI-002528, CCI-002529) | Section 21 | Role-based access control, {{ SENSITIVITY_CLASSIFICATION }} metadata tagging, and restriction of network schematics. |
| SC-39 | Process Isolation | Maintains separate execution domains for each executing system process. (CCI-002530) | Section 22 | Operating system address space isolation, unprivileged container namespaces, and gVisor isolation. |
| SC-41 | Port and I/O Device Access | Logically disables unused connection ports and I/O devices (USB, serial) not needed for mission. (CCI-002544, CCI-002545, CCI-002546) | Section 23 | Provisioning virtual instances without USB emulation; kernel-level disabling of unneeded peripheral interfaces per DoDI 8500.01. |
| SC-45 | System Time Synchronization | Synchronizes system clocks within and between systems and system components. (CCI-004922) | Section 24 | Google TrueTime NTP infrastructure traceable to US Naval Observatory (USNO) with automated synchronization per DoDI 8320.02. |
| SC-45(01) | Synchronization with Authoritative Time Source | Compares and synchronizes system clocks ({{ ODP_SC_45_1_SYNC_FREQ }}). (CCI-004923, CCI-004924, CCI-004925, CCI-004926, CCI-004927) | Section 24 | Google TrueTime NTP infrastructure traceable to US Naval Observatory (USNO) with automated synchronization per DoDI 8320.02. |
| SC-47 | Alternate Communications Paths | Establishes alternate communications paths not relying on primary infrastructure for C2. (CCI-004931) | Section 25 | Secondary Dedicated Interconnects, HA Cloud VPN failover circuits, and out-of-band cellular/satellite links per DoDI 8500.01. |



## Appendix B – FIPS 140-2 / FIPS 140-3 Cryptographic Module Architecture (Google Appendix Q)

In accordance with FIPS PUB 140-2 / 140-3, NIST SP 800-52 Rev. 2, and Google Services Appendix Q, {{ ORGANIZATION }} enforces validated cryptographic modules for all data at rest and data in transit across {{ SYSTEM_NAME }}:

| Protection Layer | Validated Cryptographic Module | FIPS Certificate # | Technical Enforcement Mechanism |
| :--- | :--- | :--- | :--- |
| **Hardware Key Security (`SC-12`)** | Cloud HSM (Marvell [formerly Cavium] HSMs) | FIPS 140-2 Level 3 (`[CONFIG_REQUIRED: CMVP certificate number from CSP package or key attestation chain]`) | Cloud KMS HSM-Backed Customer-Managed Encryption Keys (CMEK) |
| **Transport Encryption (`SC-8`)** | Google BoringCrypto | FIPS 140-3 Cert #5104 (Level 1, retrieved 2026-10-15) | TLS 1.2 minimum (TLS 1.3 where supported) across external endpoints and ALTS across Cloud Virtual Network SDN |
| **Storage Encryption (`SC-28`)** | Google BoringCrypto (AES-256-GCM) | FIPS 140-validated BoringCrypto (per CSP authorization package) | Automated Bucket, Persistent Disk, & Database Volume Encryption wrapped with Cloud KMS CMEK |
