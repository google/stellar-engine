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

Federal agencies and organizations cannot protect the confidentiality, integrity, and availability of information in today’s highly networked systems environment without ensuring that all people involved in using and managing IT:


1. Understand their roles and responsibilities related to the organizational mission;
2. Understand the organization’s IT security policy, procedures, and practices; and
3. Have at least adequate knowledge of the various management, operational, and technical controls required and available to protect the IT resources for which they are responsible.

The purpose of this System and Communications Protection Plan is to manage {{ ORGANIZATION }} aligned systems and communications security infrastructure, and to protect its information including the defense-in-depth approach for {{ ORGANIZATION }} Network Security.

This document complies with the following requirements from NIST Special Publication 800-53 Revision 5, "Security and Privacy Controls for Federal Information Systems and Organizations". A detailed compliance matrix can be found in Appendix A, “Detailed Compliance Matrix”.

The System and Communications Policy encompasses all {{ ORGANIZATION }} users who have access to {{ SYSTEM_NAME }}. This policy outlines the framework for establishing, implementing, and maintaining comprehensive system and communications instructions in alignment with applicable {{ GOVERNANCE_REGIME }} guidelines (NIST SP 800-53, FedRAMP, State/Federal regulations). It applies to employees, contractors, and third-party users who handle sensitive information or operate within {{ ORGANIZATION }} {{ SYSTEM_NAME }} information technology infrastructure.

The system and communications protection policy is required to be reviewed and updated as necessary, but at least annually.


## 2. Separation of System and User Functionality


#### 2.1.1 IAM Principles

These are the security design principles that guide the IAM settings.

- IAM Policy should be defined as Infrastructure-as-code (IaC) and enforced by code that’s reviewed and submitted using Terraform.

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


#### 2.1.2 Role Groups

Role Groups are created corresponding to the various development and administrative roles needed to build and maintain the application.

- Roles are identified by development and administrative teams.

- Groups are created for each role and administered by the IAM and Cloud Platform engineering teams. The bootstrap Terraform automation service account is an administrator of these groups to facilitate automated least-privilege role bindings.

- Group naming convention: `gcp-{environment}-{role}@{{ ORGANIZATION_DOMAIN }}` (e.g., `gcp-prod-security-admins@{{ ORGANIZATION_DOMAIN }}`).

- Initial role group memberships needed for system provisioning are checked into Terraform code and applied by the bootstrap Terraform service accounts. Ongoing role group membership management is integrated with {{ ORGANIZATION }} enterprise identity and IAM systems using Terraform IaC automation.



### 2.2 Cloud Service Provider Inherited Controls & Shared Responsibility Boundary

- **Cloud Provider Inherited Controls**: The underlying cloud platform provides physical network isolation, hypervisor and private SDN segmentation (`SC-7`), hardware FIPS 140-3 HSM crypto modules (`SC-12`, `SC-13`), and default WAN encryption in transit (`SC-8`).
- **Customer Implementation Responsibilities**: {{ ORGANIZATION }} is responsible for configuring VPC Firewall Rules / Security Groups (`SC-7`), boundary protection perimeters (`SC-7`), Cloud KMS CMEK key rotation (`SC-12`, `SC-28`), Private API Access (`SC-7`), and TLS 1.3 ingress encryption (`SC-8`).

## 3. Security Function Isolation


### 3.1 Security Analytics and Threat Monitoring

{{ THREAT_DETECTION_IMPLEMENTATION }}


#### 3.1.2 Firewall Rules

Each VPC network implements a distributed virtual firewall. Configure firewall rules that allow or deny traffic to and from the resources attached to the VPC, including Compute Engine VM instances and GKE clusters.

Firewall rules are applied at the VPC level, so they help provide effective protection and traffic control regardless of the operating system your instances use. The firewall is stateful, which means that for flows that are permitted, return traffic is automatically allowed.

Firewall rules are specific to a particular VPC network. The rules allow you to specify the type of traffic, such as ports and protocols, and the source or destination of the traffic, including IP addresses, subnets, tags, and service accounts. For example, you can create an ingress rule to allow any VM instance associated with a particular service account to accept TCP traffic on port 80 that originated from a specific source IP address or CIDR range. Once created firewall rules cannot be renamed so consider your naming convention to support operational needs.

Firewall rules assignment options

Each VPC automatically includes default and implied firewall rules:

- Implied egress rule: An egress rule whose action is ALLOW, destination is 0.0.0.0/0, and priority is the lowest possible (65535) lets any instance send traffic to any destination, except for traffic blocked by GCP.  Outbound access may be restricted by creating a higher priority firewall rule.

- Implied deny ingress rule: An ingress rule whose action is DENY, source is 0.0.0.0/0, and priority is the lowest possible (65535) protects all instances by blocking incoming traffic to them. Incoming access may be allowed by a higher priority rule.

The implied rules cannot be removed, but they have the lowest possible priorities. Rules you create can override them as long as your rules have higher priorities (less than 65535).

Firewall Rules Logging allows you to audit, verify, and analyze the effects of your firewall rules. For example, you can determine if a firewall rule designed to deny traffic is functioning as intended. Firewall Rules Logging is also useful if you need to determine how many connections are affected by a given firewall rule.

You enable Firewall Rules Logging individually for each firewall rule whose connections you need to log. Firewall Rules Logging is an option for any firewall rule, regardless of the action (allow or deny) or direction (ingress or egress) of the rule. Firewall Rules Logging is useful if you need to determine the effectiveness of a firewall rule and how many connections are affected by a given firewall rule.  For information about viewing logs, see Using Firewall Rules Logging.

When you enable logging for a firewall rule, Google Cloud creates an entry called a connection record each time the rule allows or denies traffic. Each connection record contains the source and destination IP addresses, the protocol and ports, date and time, and a reference to the firewall rule that applied to the traffic. You can view these records in Cloud Logging, and you can export logs to any destination that Cloud Logging export supports.

In addition to firewall rules per VPC there is also the ability to create Hierarchical firewall policies which let you create and enforce a consistent firewall policy across the organization. You can assign hierarchical firewall policies to the organization as a whole or to individual folders.

Hierarchical firewall policies are containers for firewall rules that can explicitly deny or allow connections. In addition, hierarchical firewall policy rules can delegate evaluation to lower-level policies or VPC network firewall rules if desired. Lower-level rules cannot override a rule from a higher place in the resource hierarchy. This lets organization-wide admins manage critical firewall rules in one place.

All rules associated with the organization node are evaluated, followed by those of the first level of folders, and so on. However with Shared VPC the evaluation follows the resource path of the Shared VPC host project, not the service project. Hierarchical firewall policy rules can be targeted to specific VPC networks and VMs by using target resources. This lets you create exceptions for groups of VMs.


#### 3.1.3 Firewall Policy Standards:

- Create firewall rules leveraging service accounts as the source or target wherever possible, as this allows for more  autonomy for applications teams to scale their resources without requiring additional firewall changes. In addition service accounts are specific to projects and can only be changed on VMs by stopping and starting.

- Limit the use of firewall rules using tags as they can be invoked by simply adding a network tag to a VM and are not specific to any project.

- Where more general firewall rules are required, using a specific subnet or a summarized IP CIDR range is recommended to reduce the complexity of the rules.

- To improve security posture it is recommended to create an egress-deny rule with a higher priority than the implied rules to ensure that both ingress and egress traffic is managed.

- Define a standard naming convention for firewall rules and make use of description metadata to allow those reviewing rules to better understand the intent or history of the rule.

- Firewall rules created by GCP service accounts for services running within {{ ORGANIZATION }} VPCs (e.g., Google Kubernetes Engine) are managed strictly according to verified service architecture and IaC templates.

- Enable Firewall Rules Logging to allow the audit, verification, and analysis the effects of your firewall rules.

- Leverage the Network Intelligence Firewall Insights service which provides visibility into firewall usage and detects firewall configuration issues. Related insights and metrics are also integrated into the Google Cloud Console for the Virtual Private Cloud (VPC) firewall.

- Manage custom firewall rules and configuration centrally, using Infrastructure as Code and Terraform. This provides development teams the ability to manage their rulesets which are approved as part of a CI/CD process by appropriate parties. In addition there is built in auditability and traceability in the process.

- Enforce Hierarchical Firewall Policies centrally across organization folders and environments using Terraform IaC, ensuring consistent baseline perimeter security across all tenant spoke projects.


#### 3.1.4 Data Loss Prevention

To validate and detect sensitive data exposure across containerized workloads and application logs, {{ ORGANIZATION }} enforces Cloud Sensitive Data Protection (Cloud DLP) inspection templates to regularly audit log streams and database stores, generating automated alerting on unintended PII/{{ SENSITIVITY_CLASSIFICATION }} disclosure.


## 4. Information in Shared System Resources


#### 4.1.1 Cloud Organization Policy

{{ ORGANIZATION }} enforces Organization Policy constraints across the resource hierarchy. Resource hierarchy nodes inherit baseline policies from the root organization node (`inheritFromParent = true`), ensuring mandatory enforcement of uniform security guardrails, CMEK restrictions, and external IP prohibitions across all folders and projects.


#### 4.1.2 Project Layout

All cross-project permission grants are controlled by Cloud IAM and defined in Terraform.

Details about the project layout are documented in the Cloud Project Organization section of this document. As a part of the hub and spoke network architecture, a default VPC service control perimeter is created around the project which hosts the restricted shared VPC.


#### 4.1.3 VPC Service Controls

VPC Service Controls secure and improve the ability to mitigate the risk of data exfiltration from GCP services by defining different controls. These controls include the creation of perimeters that protect resources and the data of services that are explicitly specified. We can enforce adaptive access control based on IP range or device trust (BeyondCorp) for GCP resource access from outside privileged networks.

A VPC Service Control makes sure that data in most GCP services cannot exit the perimeter to an un-recognized network IP, even if they have the appropriate IAM credentials such as a user account or service account.


## 5. Denial of Service Protection

{{ ORGANIZATION }} utilizes Google Cloud Armor WAF and Global Load Balancing to eliminate the effects of denial-of-service attacks:

- Volumetric - Also known as “floods,” the goal of this type of attack is to cause congestion and send so much traffic that it overwhelms the bandwidth of the site.

- TCP State-Exhaustion Attacks - This type of attack focuses on actual web servers, firewalls, and load balancers to disrupt connections, resulting in exhausting their finite number of concurrent connections the device can support

- Application Layer Attacks - Targets weaknesses in an application or server with the goal of establishing a connection and exhausting it by monopolizing processes and transactions

In the event {{ ORGANIZATION }} determines they are under a denial-of-service attack, the {{ ORGANIZATION }} Incident Response Plan (IRP) shall be initiated, and the following process executed. Some activities in the below process cannot be directly executed by {{ ORGANIZATION }}, therefore close coordination with {{ ORGANIZATION }} is mandatory.


#### 5.1.1 Identification


## 6. Detection and alerting:

  a. Search for traffic patterns to expose known attacks (signature detection)

  b. Compare parameters of the observed network traffic with normal traffic (anomaly detection)

  c. Contact USCYBERCOM for early warnings and indicator notices


## 7. Attack analysis:

  d. Identify the abused systems and services

  e. Understand if you are the target of the attack or a collateral victim

  f. Get a list of attacking IPs by tracing them onto the log files

  g. Define the attack’s profile by using network monitoring and traffic analysis tools



### 7.1 Cloud Service Provider Inherited Controls & Shared Responsibility Boundary

- **Cloud Provider Inherited Controls**: The underlying cloud platform provides physical network isolation, hypervisor and private SDN segmentation (`SC-7`), hardware FIPS 140-3 HSM crypto modules (`SC-12`, `SC-13`), and default WAN encryption in transit (`SC-8`).
- **Customer Implementation Responsibilities**: {{ ORGANIZATION }} is responsible for configuring VPC Firewall Rules / Security Groups (`SC-7`), boundary protection perimeters (`SC-7`), Cloud KMS CMEK key rotation (`SC-12`, `SC-28`), Private API Access (`SC-7`), and TLS 1.3 ingress encryption (`SC-8`).

## 8. Mitigation acquirement /refinement:

  h. Contact CNDSP to report the attack

  i. Ask for assessment and visibility into the attack


#### 8.1.1 Containment


## 9. Network modifications:

  a. Switch to alternative sites or networks using DNS or other mechanism

  b. Route traffic on scrubbing services and products


## 10. Content delivery control:

  c. Use Caching/Proxying

  d. Enable alternative communication channels (VPN)



### 10.1 Cloud Service Provider Inherited Controls & Shared Responsibility Boundary

- **Cloud Provider Inherited Controls**: The underlying cloud platform provides physical network isolation, hypervisor and private SDN segmentation (`SC-7`), hardware FIPS 140-3 HSM crypto modules (`SC-12`, `SC-13`), and default WAN encryption in transit (`SC-8`).
- **Customer Implementation Responsibilities**: {{ ORGANIZATION }} is responsible for configuring VPC Firewall Rules / Security Groups (`SC-7`), boundary protection perimeters (`SC-7`), Cloud KMS CMEK key rotation (`SC-12`, `SC-28`), Private API Access (`SC-7`), and TLS 1.3 ingress encryption (`SC-8`).

## 11. Traffic control:

  e. Terminate unwanted connections or processes on servers and routers

  f. Configure outbound filters for reducing DDoS response footprint

  g. Control content delivery based on user and session details


#### 11.1.1 Remediation


## 12. Bandwidth prioritization and blocking:

  a. Deny connections using geographic information

  b. Deny connections based on IP and traffic signatures

  c. Place limits on the amount of traffic, maximum burst size, traffic priority on individual packet types


## 13. Sinkholing:

  d. Attract DDoS traffic on the IP blocks advertised by the sinkhole to apply specialized analysis (Coordinate with CNDSP)


#### 13.1.1 Recovery


## 14. Normal state verification:

  a. Verify that traffic is nominal with no sharp increases. Let a period of time since last violation before the traffic flow is considered normal

  b. Ensure that the impacted services can be operational again

  c. Ensure that your infrastructure performance is back to your baseline

  d. Ensure that there are no collateral damages


## 15. Rollback:

  e. Initiate suspended services, applications, and modules

  f. Rollback the mitigation measures

  g. Announce the end of the incident

  h. Revert to your original network


#### 15.1.1 Aftermath


## 16. Incident review and information Disclosure:

  a. Evaluate the effectiveness of response

  b. Review the measures that could be taken to better address the incident response

  c. Review and refine attack-handling tools and procedures taken during the incident

  d. Create an incident review

  e. Measure the operational impact


### 16.1 Restrict Ability to Attack Other Systems

Restricting the ability of individuals to launch denial-of-service attacks requires the mechanisms commonly used for such attacks to be unavailable. Individuals of concern include hostile insiders or external adversaries who have breached or compromised the system and are using it to launch a denial-of-service attack.

{{ ORGANIZATION }} restricts individuals to connect and transmit arbitrary information on the transport medium and limits the ability of individuals to use excessive system resources.


### 16.2 Capacity, Bandwidth, and Redundancy

{{ ORGANIZATION }} manages the capacity, bandwidth, and other redundancy to limit the effects of information flooding denial-of-service attacks.


### 16.3 Detection and Monitoring


#### 16.3.1 Projects

To access Cloud Monitoring for each environment a host project has been created to hold the dashboards and alerts. The folders and monitoring host projects are listed in the table below.


| Folder | Monitoring Project |
| --- | --- |
| Security | <prefix>-dev-sec-core-0 |
| Security | <prefix>-prod-sec-core-0 |


#### 16.3.2 Groups

A group named gcp-monitoring-admins is created during the bootstrap process.


#### 16.3.3 Alerts

Alerts can be created based on events and log metrics. Alerting gives timely awareness to problems in your cloud applications so you can resolve the problems quickly. Within Cloud Monitoring, an alerting policy describes the circumstances under which you want to be alerted and how you want to be notified.


#### 16.3.4 Dashboards

Cloud Monitoring automatically installs a dashboard when you create a resource in a Google Cloud project. These dashboards display metrics and general information about a single Google Cloud service. Custom dashboards are dashboards that you create or install. Unlike dashboards for Google Cloud services and those for your supported integrations, custom dashboards let you view and analyze data from different sources in the same context. For example, you can create a dashboard that displays metric data, alerting policies, and log entries.


## 17. Boundary Protection


#### 17.1.1 Cloud Organization Policy

{{ ORGANIZATION }} enforces Organization Policy constraints across the resource hierarchy. Resource hierarchy nodes inherit baseline policies from the root organization node (`inheritFromParent = true`), ensuring mandatory enforcement of uniform security guardrails, CMEK restrictions, and external IP prohibitions across all folders and projects.


#### 17.1.2 Project Layout

All cross-project permission grants are controlled by Cloud IAM and defined in Terraform.

Details about the project layout are documented in the Cloud Project Organization section of this document. As a part of the hub and spoke network architecture, a default VPC service control perimeter is created around the project which hosts the restricted shared VPC.


#### 17.1.3 VPC Service Controls

VPC Service Controls secure and improve the ability to mitigate the risk of data exfiltration from GCP services by defining different controls. These controls include the creation of perimeters that protect resources and the data of services that are explicitly specified. We can enforce adaptive access control based on IP range or device trust (BeyondCorp) for GCP resource access from outside privileged networks.

A VPC Service Control makes sure that data in most GCP services cannot exit the perimeter to an un-recognized network IP, even if they have the appropriate IAM credentials such as a user account or service account.


#### 17.1.4 Network Control

Workload service projects are attached to the Shared VPC host network. Each service project is allocated dedicated subnets within regional environments. Service accounts are granted `compute.networkUser` permissions strictly on their assigned subnets, enforcing least-privilege IP allocation and network segregation.


#### 17.1.5 Firewall Rules

Hierarchical and VPC firewall rules are defined at the Shared VPC host level and managed strictly via Terraform IaC. By default, all ingress traffic is denied via an explicit default-deny rule. Ingress and egress policies are enforced with strict port, protocol, and CIDR constraints tailored to each landing zone environment (development, non-production, and production).


#### 17.1.6 DNS

{{ SYSTEM_NAME }} deploys private Google Cloud DNS zones with DNSSEC enabled across VPC environments. Forwarding rules and response policies are centrally managed, preventing unauthorized external DNS resolution and DNS tunneling.


#### 17.1.7 Org Policies

There are org policies set to apply additional security to the network:

- compute.vmExternalIpAccess is set to denyAll=true, meaning VMs cannot be created with an external IP address

- compute.skipDefaultNetworkCreation is set to true - Causes Google Cloud to skip the creation of the default network and related resources during Google Cloud project resource creation.

- compute.restrictProtocolForwardingCreationForTypes is set to internal - Causes new forwarding rule objects to be restricted to having target instances with internal IP addresses.

- compute.restrictXpnProjectLienRemoval is set to true - When true, restricts the set of users that can remove a Shared VPC project lien.

- compute.setNewProjectDefaultToZonalDNSOnly is set to true - Newly created projects will use Zonal DNS as default.

- sql.restrictAuthorizedNetworks is set to true - Prevents adding authorized networks for unproxied database access to Cloud SQL instances.

- sql.restrictPublicIp is set to true - Restricts public IP addresses on Cloud SQL instances.


### 17.2 Flow Diagram

Google Cloud Platform (GCP) offers a robust architecture for managing Virtual Private Clouds (VPCs) and facilitating communication among them using VPC Network Peering.  Shared VPC is a networking construct that significantly reduces the amount of complexity in network design. With Shared VPC, network policy and control for all networking resources are centralized and easier to manage. Service project departments can configure and manage non-network resources, enabling a clear separation of responsibilities for different teams in the organization.

Resources in Shared VPC networks can communicate with each other securely and efficiently across project boundaries using internal IP addresses. You can manage shared network resources—such as subnets, routes, and firewalls—from a central host project, so you can enforce consistent network policies across projects.

As shown in the architecture, {{ ORGANIZATION }} {{ SYSTEM_NAME }} deploys Shared VPC networks (base and restricted) as the foundational networking construct for each environment. Each Shared VPC network is contained within a single project. The base VPC network is used for deploying services that contain non-sensitive data, and the restricted VPC network uses VPC Service Controls to limit access to services that contain sensitive data.

You can implement the model described in the preceding section independently for each of the four environments (common, development, non-production, and production). This model provides the highest level of network segmentation between environments.

For the above  scenario, all environments can directly communicate with shared resources in the common environment hub. The common environment can host tooling that requires connectivity to other environments, like CI/CD infrastructure, directories, and security and configuration management tools. As with the previous independent Shared VPC model, the hub-and-spoke scenario is also composed of base and restricted VPC networks. A base Shared VPC hub connects the base Shared VPC network spokes in development, non-production, and production, while the restricted Shared VPC hub connects the restricted Shared VPC network spokes in these same environments. The choice between base and restricted Shared VPC networks also depends on whether VPC Service Controls are required. For workloads with strong data exfiltration mitigation requirements, the hub-and-spoke associated with the restricted Shared VPC networks is preferred.


#### 17.2.1 VPCs

A Virtual Private Cloud (VPC) provides complete network-level isolation for {{ ORGANIZATION }} cloud workloads. {{ ORGANIZATION }} mandates and enforces dedicated VPC networks with custom IP address ranges, non-overlapping subnets, and restricted routing tables to isolate production, staging, and shared management tiers.


#### 17.2.2 Google VPC Network Peering

Google Cloud Platform (GCP) offers a robust architecture for managing Virtual Private Clouds (VPCs) and facilitating communication among them using VPC Network Peering.  VPC Network Peering allows VPCs within the same project or across different projects to communicate securely and efficiently using internal IPs. Peering connections do not require any additional gateways or routers; traffic remains within Google's backbone network, ensuring low latency and high reliability. VPC Network Peering allows VPCs to exchange traffic securely and privately using internal IP addresses. It facilitates communication between resources deployed in different VPCs without needing to traverse the public internet.


#### 17.2.3 Subnet Allocations

Subnet allocation in Google Cloud Platform (GCP) divides the IP address range of Virtual Private Clouds (VPCs) into strictly segmented, non-overlapping subnetworks. Subnets are allocated across dedicated operational environments (Hub/Core Services, Spoke Workloads, and Ingress/Egress DMZs) and bound to specific geographic regions (e.g., {{ PRIMARY_LOCATION }}).

For {{ SYSTEM_NAME }}, active subnets are partitioned into tiered workload boundaries:
- **Tier 1 (Presentation / Ingress DMZ)**: Dedicated subnets for internal load balancers, Cloud IAP proxies, and managed ingress gateways.
- **Tier 2 (Application / Compute)**: Dedicated subnets for containerized services, GKE clusters, and VM instances.
- **Tier 3 (Data / Persistence)**: Dedicated subnets for Cloud SQL, Spanner PSC endpoints, and secure database services.

Subnet CIDR blocks are managed strictly through Terraform Infrastructure-as-Code and enforced via hierarchical firewall policies and VPC Service Controls. Active discovered subnets for the system boundary include: `{{ SUBNET_CIDRS }}`.

Subnets are logical partitions within a VPC that define IP address ranges for resources deployed in specific geographic locations (regions or availability zones). Each subnet is associated with a specific region and availability zone within that region. It is recommended to allocate a subnet for each application workload tier. For example, a Google Kubernetes Engine (GKE) cluster utilizes a dedicated node subnet and two secondary ranges (one for Pods and one for Services). These subnets are declared in the network architecture stage and referenced during workload deployment. Primary VPC IP ranges and subordinate subnet allocations ensure non-overlapping address spaces across interconnected environments.


#### 17.2.4 Google Private Access

Access to Google-managed services, (e.g. AppEngine, CloudSQL, CloudFunctions,) will be routed through internal network space using Google Private Access. Access from Google-managed services to the VPC will be routed through internal network space using Serverless VPC Access. Google Private Access is enabled for subnets.


#### 17.2.5 Interservice Communications

Direct network connections between microservices will be routed within the VPC using Internal Load-Balancing or Google Private Access for managed services. Interservice message quoting will utilize Cloud Pub/Sub for asynchronous delivery.


#### 17.2.6 VPC Firewall Rules

By default, all unsolicited ingress traffic is blocked. Ingress and egress firewall policies are centrally defined and managed via Infrastructure-as-Code modules. Cloud Virtual Private Cloud (VPC) firewall rules and security groups control traffic within the network. Firewall rules are applied in priority order. The first rule that matches the traffic criteria (source IP, destination IP, protocol, port, etc.) is applied, and subsequent rules are not evaluated. Rules specify which protocols (TCP, UDP, ICMP, etc.) and ports (such as 80 for HTTP or 443 for HTTPS) are allowed.


#### 17.2.7 Hub and Spoke architecture

Within Google Cloud Platform (GCP), VPC Network Peering is used to connect VPCs within or between projects in order to execute the Hub and Spoke architecture. A networking design pattern known as "Hub and Spoke" includes setting up Virtual Private Clouds (VPCs) in a centralized hub and outward spoke architecture. A centralized networking hub housing shared resources and services is provided by the hub VPC. Shared services that are accessed by several spoke VPCs, such logging, security, or monitoring tools, may also be hosted by the hub VPC.

The Spoke VPCs are separate VPC networks that are connected to the hub VPC. Each spoke VPC represents a distinct environment, such as development, testing, or production environments. Spoke VPCs contain the application-specific resources and workloads. They are isolated from each other and communicate with each other through the hub VPC


#### 17.2.8 Authorization Boundary

The below diagram demonstrates the network authorization boundary for the {{ SYSTEM_NAME }} environment.


## 18. Transmission Confidentiality and Integrity

{{ ORGANIZATION }} {{ SYSTEM_NAME }} provides confidentiality and integrity of information transmission through the use of IAP. All information entering the {{ ORGANIZATION }} enclave does so through the IAP encrypted tunnel.


### 18.1 Cryptographic Protection


#### 18.1.1 Encryption-at-Rest

All data stored in Google Cloud is encrypted at the storage level using AES256 using Google-managed data encryption keys (DEK). Google uses a common cryptographic library which incorporates a FIPS 140-2 validated module, BoringCrypto.


#### 18.1.2 Encryption-in-Transit

Microservices will primarily use Cloud Pub/Sub and REST transmission methods within the project system. Both of these protocols leverage HTTPS.


## 19. Network Disconnect

{{ ORGANIZATION }} ensures that network connections associated with a communications session are terminated at the end of the sessions.


## 20. Cryptographic Key Establishment and Management

{{ ORGANIZATION }} documents and implements Google Cloud Key Management Service (KMS) to establish cryptographic keys for required cryptography employed within the {{ ORGANIZATION }} {{ SYSTEM_NAME }}. Google Cloud KMS is used for compliant storage, access, destruction, generation, distribution, and access of all cryptographic keys.


### 20.1 Availability

{{ ORGANIZATION }} will ensure the availability of information on {{ SYSTEM_NAME }} is not compromised in the event of the loss of cryptographic keys by the users.


## 21. Cryptographic Protection

{{ ORGANIZATION }} encrypts all information on {{ SYSTEM_NAME }} within its boundary using FIPS approved algorithms in all encryption protocols.


## 22. Collaborative Computing Devices and Applications

{{ ORGANIZATION }} prohibits remote activation of collaborative computing devices.


## 23. Transmission of Security and Privacy Attributes

Security and privacy attributes are used to implement access control and information flow control policies; reflect special dissemination, management, or distribution instructions, including permitted uses of personally identifiable information; or support other aspects of the information security and privacy policies.

{{ ORGANIZATION }} associates all security and privacy attributes with information that is exchanged between {{ SYSTEM_NAME }} and {{ SYSTEM_NAME }} components.


### 23.1 Integrity Verification

Part of verifying the integrity of transmitted information is ensuring that security and privacy attributes that are associated with such information have not been modified in an unauthorized manner. Unauthorized modification of security or privacy attributes can result in a loss of integrity for transmitted information.

{{ ORGANIZATION }} employs Google Binary Authorization & Cloud Audit Logs to verify the integrity of transmitted security and privacy attributes.


### 23.2 Anti-Spoofing Mechanisms

{{ ORGANIZATION }} implements Google Access Context Manager & VPC Service Controls to prevent adversaries from falsifying security attributes.


### 23.3 Cryptographic Binding

Cryptographic mechanisms and techniques can provide strong security and privacy attribute binding to transmitted information to help ensure the integrity of such information.

{{ ORGANIZATION }} implements TLS 1.2+ / IPsec VPN encryption to bind security and privacy attributes to transmitted information.


## 24. Public Key Infrastructure Certificates

{{ ORGANIZATION }} {{ SYSTEM_NAME }} does not issue public key certificates but is permitted to obtain public key certificates from approved service providers.


## 25. Mobile Code

{{ ORGANIZATION }} {{ SYSTEM_NAME }} does not use mobile code, therefore, this control is not applicable.


## 26. Secure Name/Address Resolution Service (Authoritative Source)

This control is not applicable to the {{ ORGANIZATION }} {{ SYSTEM_NAME }}. {{ ORGANIZATION }} {{ SYSTEM_NAME }} does not own, manage, or operate any authoritative DNS servers. {{ ORGANIZATION }} {{ SYSTEM_NAME }} is not responsible for collecting artifacts, providing the means to indicate the security status of child zones, providing the means to enable verification of a chain of trust, or providing additional integrity verification artifacts related to DNS address resolution authoritative sources.


## 27. Secure Name/Address Resolution Service (Recursive or Caching Resolver)

This control is not applicable to the {{ ORGANIZATION }} {{ SYSTEM_NAME }}. {{ ORGANIZATION }} {{ SYSTEM_NAME }} does not own, manage, or operate any authoritative DNS servers. {{ ORGANIZATION }} is not responsible for requesting data origin authentication verification, requesting data integrity verification, performing data integrity verification, or performing data origin verification authentication on the name/address resolution responses related to DNS address resolution.


## 28. Architecture and Provisioning for Name/Address Resolution Service

This control is not applicable to the {{ ORGANIZATION }} {{ SYSTEM_NAME }}. {{ ORGANIZATION }} {{ SYSTEM_NAME }} does not own, manage, or operate any authoritative DNS servers. {{ ORGANIZATION }} is not responsible for identifying information systems that collectively provide name/address resolution or systems that implement internal/external role separation.


## 29. Session Authenticity

Protecting session authenticity addresses communications protection at the session level. Such protection establishes grounds for confidence at both ends of communications sessions in the ongoing identities of other parties and the validity of transmitted information.

Authenticity protection includes protecting against “man-in-the-middle” attacks, session hijacking, and the insertion of false information into sessions.

{{ ORGANIZATION }} {{ SYSTEM_NAME }} is configured to protect the authenticity of communications sessions through implementation of the IAP and NIST SP 800-53 Rev. 5 and FedRAMP approved cloud security configurations.


### 29.1 Invalidate Session Identifiers at Logout

{{ ORGANIZATION }} invalidates session identifiers at logout to curtail the ability of adversaries to capture and continue to employ previously valid session IDs.


### 29.2 Unique System-generated Session Identifiers

{{ ORGANIZATION }} generates unique session identifiers to curtail the ability of adversaries to reuse previously valid session IDs. {{ SYSTEM_NAME }} only recognizes session identifiers that are system-generated.


### 29.3 Allowed Certificate Authorities

{{ ORGANIZATION }} only allows the following certificate authorities for verification of the establishment of protected sessions:

- Google Cloud Certificate Authority Service (CAS)

- Federal / DoD Approved PKI Root CA

- Google Internal Production Machine CA


## 30. Fail in Known State

Failure in a known state addresses security concerns in accordance with the mission and business needs of organizations. Failure in a known state prevents the loss of confidentiality, integrity, or availability of information in the event of failures of organizational systems or system components.

{{ ORGANIZATION }} {{ SYSTEM_NAME }} fails to a known state to preserve the confidentiality, integrity, and availability of information and prevents injury or destruction of property; and facilitates {{ SYSTEM_NAME }} restart and return to the operational mode with less disruption of mission and business processes.


## 31. Protection of Information at Rest

Information at rest refers to the state of information when it is located on storage devices as specific components of information systems.

All information at rest on {{ SYSTEM_NAME }} is to be encrypted and protected.

All {{ ORGANIZATION }} {{ SYSTEM_NAME }} disks are encrypted at rest through the configurations of Google Cloud Compute Engine. Google Cloud Storage, in use, utilizes customer managed encryption keys.


### 31.1 Cryptographic Protection & Keys


#### 31.1.1 Encryption-at-Rest

All data stored in Google Cloud is encrypted at the storage level using AES256 using Google-managed data encryption keys (DEK). Google uses a common cryptographic library which incorporates a FIPS 140-2 validated module, BoringCrypto.


#### 31.1.2 Encryption-in-Transit

Microservices will primarily use Cloud Pub/Sub and REST transmission methods within the project system. Both of these protocols leverage HTTPS.


## 32. Operations Security

Operations security (OPSEC) is a systematic process by which potential adversaries can be denied information about the capabilities and intentions of organizations by identifying, controlling, and protecting generally unclassified information that specifically relates to the planning and execution of sensitive organizational activities. OPSEC controls protect the confidentiality of information, including limiting the sharing of information with suppliers, potential suppliers, and other non-organizational elements and individuals.

Throughout the system development life cycle, {{ ORGANIZATION }} developers practice operations security to:  identify critical information, analyze threats, analyze vulnerabilities, assess risks, and apply appropriate countermeasures.


## 33. Process Isolation

{{ ORGANIZATION }} maintains a separate execution domain for each executing system process.


#### 33.1.1 Version Control Repositories

Source code and infrastructure blueprints for {{ SYSTEM_NAME }} are maintained in secured enterprise Git repositories enforcing branch protection rules, cryptographically verified commits, and mandatory peer code review workflows.


#### 33.1.2 Branching Strategy

Our development process follows a trunk-based branching strategy. This entails having a protected main branch, with engineers creating scoped feature/bugfix branches that are validated through automated CI/CD security gates before merging into the main branch.


#### 33.1.3 Validation

Currently, development happens on feature and bug fix branches. When complete, a pull request (PR), (also known as a  merge request (MR)), can be opened targeting the main branch. After two reviewers have submitted comments, and their recommendations have been adjudicated, (which can be an iterative process), the feature branch is merged into the main branch.


## 34. Port and I/O Device Access

{{ ORGANIZATION }} disables or removes connection ports and I/O devices to help prevent the exfiltration of information from {{ SYSTEM_NAME }} and the introduction of malicious code from those ports or devices.

Connection ports include Universal Serial Bus (USB), Thunderbolt, and Firewire (IEEE 1394). Input/output (I/O) devices include compact disc and digital versatile disc drives.


## 35. System Time Synchronization

{{ ORGANIZATION }} synchronizes {{ SYSTEM_NAME }} clocks within and between all {{ SYSTEM_NAME }} components.


### 35.1 Synchronization with Authoritative Time Source

{{ ORGANIZATION }} uses Google TrueTime NTP Servers as the authoritative time source for {{ SYSTEM_NAME }}. When the time difference between {{ SYSTEM_NAME }} and Google TrueTime NTP Servers is greater than 1 second, {{ ORGANIZATION }} must synchronize the internal system clocks.


## 36. Alternate Communications Path

An incident, whether adversarial- or non adversarial-based, can disrupt established communications paths used for system operations and organizational command and control. Alternate communications paths reduce the risk of all communications paths being affected by the same incident.

{{ ORGANIZATION }} uses Secondary Dedicated Cloud Interconnect / HA VPN Tunnel as an alternative communication path when the primary communication path is disrupted.



## Appendix A – Detailed Compliance Matrix

The following table provides detailed traceability between the policy implementation statements in this document, the authoritative NIST SP 800-53 Rev. 5 control requirements, DoD CCIs, and the technical/governance enforcement mechanisms active across {{ SYSTEM_NAME }}.


| CTRL ID | CTRLTITLE | REQUIRED eMASS STANDARD | DOCREF | ENFORCEMENT MECHANISM |
| :--- | :--- | :--- | :--- | :--- |
| SC-01 | Policy and Procedures | Develops, documents, and disseminates SC policy/procedures to ISSO/ISSM; designates ISO/PM; reviews annually and upon system changes, new threats, breaches, or policy updates. (CCI-001075, CCI-001076, CCI-001077, CCI-001079, CCI-001080, CCI-001081, CCI-002378, CCI-002380, CCI-004852, CCI-004853, CCI-004854, CCI-004855, CCI-004856, CCI-004857, CCI-004858, CCI-004859, CCI-004860, CCI-004861, CCI-004862, CCI-004863, CCI-004864) | Section 1 | eMASS governance publication (System ID: {{ RMF_PACKAGE_ID }}); annual review cadence managed by ISO/PM, ISSM, and ISSO; trigger alignment with DoDI 8510.01 and DoDI 8500.01. |
| SC-02 | Separation of System and User Functionality | Separates user functionality from system administrative and security management functions. (CCI-001082) | Section 2 | {{ IDENTITY_PROVIDER }} with {{ MFA_MECHANISM }}, project boundary isolation across network transport and telemetry logging, and role-based access control. |
| SC-03 | Security Function Isolation | Isolates security functions from non-security functions to maintain system integrity. (CCI-001084) | Section 3 | Multi-project landing zone topology, centralized machine identity management, and IAM conditions on Resource Manager Tags. |
| SC-04 | Information in Shared System Resources | Prevents unauthorized residual information transfer across shared system resources (RAM, persistent disks). (CCI-001090) | Section 4 | Google Compute Engine automated memory clearing, persistent disk zero-overwriting, and volatile cryptographic buffer flushing. |
| SC-05 | Denial-of-Service Protection | Protects against/limits effects of network and application DoS/DDoS attacks via ingress/egress filtering, rate limiting, and anomaly detection. (CCI-001093, CCI-002385, CCI-004866, CCI-004867) | Section 5 | Google Cloud Armor WAF, Cloud Load Balancing, stateful VPC firewall rules, and automated traffic scrubbing. |
| SC-05(01) | Denial-of-Service Protection: Restrict Ability to Attack Other Systems | Restricts individuals from launching DoS/DDoS attacks against other systems. (CCI-001094, CCI-002387) | Section 5 | Outbound internet deny rules (0.0.0.0/0 deny egress) and VPC Service Controls egress restrictions per DoDI 8500.01. |
| SC-05(02) | Denial-of-Service Protection: Capacity, Bandwidth, and Redundancy | Manages capacity, bandwidth, and redundancy to limit effects of information flooding attacks. (CCI-001095) | Section 5 | Dual {{ INTERCONNECT_TYPE }} circuits, dynamic BGP ECMP routing, and auto-scaling telemetry collectors. |
| SC-05(03) | Denial-of-Service Protection: Detection and Monitoring | Monitors CPU, memory, bandwidth, and sessions using IDS/IPS and SIEM to detect DoS indicators. (CCI-002388, CCI-002389, CCI-002390, CCI-002391) | Section 5 | Real-time Cloud Monitoring alerting, {{ ORGANIZATION }} NetOps telemetry analysis, and {{ CSSP_PROVIDER }} 24x7 CSSP sensor monitoring per DoDI 8530.01. |
| SC-07 | Boundary Protection | Logically monitors and controls communications at external and key internal boundaries. (CCI-001097, CCI-001098, CCI-002395, CCI-004868) | Section 17 | NCC Global Hub, Central Transit VPC Cloud Routers, virtual network security appliances, and multi-NIC VDSS inspection boundaries (ETP-{{ SYSTEM_NAME }}-01/02). |
| SC-07(03) | Boundary Protection: Access Points | Limits number of external network connections and access points. (CCI-001101) | Section 17 | Consolidated transit VPC architecture aggregating 7 initial spokes through centralized Cloud Routers. |
| SC-07(04) | Boundary Protection: External Telecommunications Services | Governs external telecom connections; reviews traffic flow exceptions at least weekly. (CCI-001102, CCI-001103, CCI-001105, CCI-001106, CCI-001107, CCI-001108, CCI-002396, CCI-004869, CCI-004870, CCI-004871) | Section 17 | Weekly ISSO firewall exception review cadence; Cross-Cloud Interconnect SLAs with AWS and Azure. |
| SC-07(05) | Boundary Protection: Deny by Default: Allow by Exception | Denies network traffic by default and allows traffic by exception at managed interfaces for all systems. (CCI-001109, CCI-004872) | Section 17 | Default VPC implied deny ingress rules (priority 65535) overridden only by explicit, documented firewall allows. |
| SC-07(07) | Boundary Protection: Split Tunneling for Remote Devices | Prevents split tunneling for remote devices; routes all traffic through DoDIN connection. (CCI-002397, CCI-004873) | Section 17 | Mandatory authorized Virtual Desktop (AVD) / enterprise VPN gateway routing per DoDI 8100.04; full tunnel enforcement. |
| SC-07(08) | Boundary Protection: Route Traffic to Authenticated Proxy Servers | Routes internal web traffic to external networks through authenticated proxy servers. (CCI-001112, CCI-001113, CCI-001114) | Section 17 | Authenticated egress proxies and Identity-Aware Proxy (IAP) integration at managed boundary gateways. |
| SC-07(09) | Boundary Protection: Restrict Threatening Outgoing Traffic | Restricts outgoing communications traffic containing potential threats. (CCI-002398, CCI-002399, CCI-002400) | Section 17 | Virtual network appliance deep packet inspection and VDSS traffic filtering. |
| SC-07(10) | Boundary Protection: Prevent Exfiltration | Prevents data exfiltration; conducts exfiltration tests at least annually. (CCI-001116, CCI-004874, CCI-004875) | Section 17 | VPC Service Controls perimeters blocking external data movement; annual exfiltration penetration testing per DoDI 8500.01. |
| SC-07(11) | Boundary Protection: Restrict Incoming Communications Traffic | Restricts incoming traffic to explicitly defined IP ranges and internal destinations documented in PPSM. (CCI-002401, CCI-002402, CCI-002403) | Section 17 | Strict VPC firewall ingress rules matching the authorized PPSM registry; public ICMP blocking. |
| SC-07(12) | Boundary Protection: Host-Based Protection | Implements host-based boundary protection on all capable components. (CCI-002404, CCI-002405, CCI-002406) | Section 17 | DoD-approved endpoint protection software, OS firewalls, and GCP VM Manager policy enforcement. |
| SC-07(13) | Boundary Protection: Isolation of Security Tools | Isolates security tools (PKI, CSSP sensors, logging) on separate subnetworks with managed interfaces. (CCI-001119, CCI-001120) | Section 17 | Dedicated security and telemetry VPC subnets isolated from transit payload routing. |
| SC-07(14) | Boundary Protection: Protect Against Unauthorized Physical Connections | Protects managed interfaces crossing security domains from unauthorized physical connections. (CCI-001121, CCI-002407) | Section 17 | Inherited Google IL5 datacenter physical security; locked enterprise colocation cages with MACsec encryption. |
| SC-07(15) | Boundary Protection: Network Privileged Accesses | Restricts network privileged access to authorized administrators. (CCI-001123) | Section 17 | {{ IDENTITY_PROVIDER }} with {{ MFA_MECHANISM }}, GCP PAM, and custom role blueprints (e.g. {{ SYSTEM_NAME }}-NetworkAdmins). |
| SC-07(25) | Boundary Protection: Unclassified National Security System Connections | Prohibits unclassified NSS from connecting to external networks without a DoDIN-approved boundary security system (VDSS). (CCI-004881, CCI-004882, CCI-004883) | Section 17 | Mandatory VDSS boundary traffic inspection under approved Exception-to-Policy (ETP-{{ SYSTEM_NAME }}-01). |
| SC-07(28) | Boundary Protection: Connections to Public Networks | Prohibits direct connection of all system components to public networks. (CCI-004889, CCI-004890) | Section 17 | compute.vmExternalIpAccess = denyAll organization policy; zero public IP assignments on VPC instances. |
| SC-07(29) | Boundary Protection: Separate Subnets to Isolate Functions | Implements logical subnetworks to isolate critical functions (server enclaves, databases). (CCI-004891, CCI-004892) | Section 17 | Structured VPC subnetworks and dedicated transit/workload subnets ({{ SUBNET_CIDRS }}). |
| SC-08 | Transmission Confidentiality and Integrity | Protects confidentiality and integrity of information in transit across internal and external networks. (CCI-002418) | Section 18 | Layer 2 MACsec on {{ INTERCONNECT_TYPE }}, Layer 3 IPsec VPN encapsulation, and TLS 1.3 across all transit streams. |
| SC-08(01) | Transmission Confidentiality and Integrity: Cryptographic Protection | Implements cryptographic protection to prevent unauthorized disclosure and detect changes in transit. (CCI-002421) | Section 18 | Hardware MACsec (gcm-aes-xpn-256), virtual appliance IPsec (AES-256-GCM), and BoringCrypto TLS 1.3 (FIPS 140-3 Cert #4407). |
| SC-08(02) | Transmission Confidentiality and Integrity: Pre- and Post-Transmission Handling | Maintains confidentiality and integrity of information during pre- and post-transmission handling. (CCI-002420, CCI-002422) | Section 18 | End-to-end payload encapsulation and volatile memory encryption buffers within virtual network security appliances. |
| SC-10 | Network Disconnect | Terminates network connection at session end or after no more than 15 minutes of inactivity. (CCI-001133, CCI-001134) | Section 19 | Automated 15-minute idle session disconnect enforced across GCP console, SSH, and IAP sessions. |
| SC-11 | Trusted Path | Establishes logical trusted path for authentication, password changes, and enrollment per DoDI 8520.03. (CCI-001135, CCI-001661, CCI-004895) | Section 19 | IAP-encrypted administrative tunnels and {{ IDENTITY_PROVIDER }} with {{ MFA_MECHANISM }}. |
| SC-12 | Cryptographic Key Establishment and Management | Adheres to NIST FIPS/NSA requirements for key generation, distribution, storage, access, and destruction. (CCI-002428 through CCI-002442) | Section 20 | Google Cloud KMS HSM FIPS 140-3 key rings, automated 90-day rotation, and DoD SAFE key transfers. |
| SC-12(01) | Cryptographic Key Establishment and Management: Availability | Ensures availability of information in the event of cryptographic key loss. (CCI-002434) | Section 20 | Multi-region Cloud KMS HSM replication across us-east4 and us-central1. |
| SC-13 | Cryptographic Protection | Employs NSA-approved / FIPS-validated cryptography for authentication, encryption, and non-repudiation. (CCI-002450, CCI-004900) | Section 21 | FIPS 140-3 validated cryptographic modules: Cloud KMS CMEK (Cert #4735), BoringCrypto (Cert #4407), and Titan HSM. |
| SC-15 | Collaborative Computing Devices | Prohibits remote activation of collaborative computing devices (cameras, microphones). (CCI-001150, CCI-001151, CCI-001152) | Section 22 | Hardware absence on cloud virtual machines and network switches; isolated physical VTC suites. |
| SC-16 | Transmission of Security and Privacy Attributes | Associates security/privacy attributes ({{ SENSITIVITY_CLASSIFICATION }} markings, {{ IMPACT_LEVEL }}) with information exchanged across interfaces. (CCI-001157, CCI-002454, CCI-002455, CCI-004901, CCI-004902, CCI-004903) | Section 23 | Automated Terraform IaC tagging, packet encapsulation metadata, and BigQuery table labels. |
| SC-16(01) | Transmission of Security Attributes: Integrity Verification | Verifies integrity of transmitted security and privacy attributes. (CCI-001158, CCI-004904) | Section 23 | Google Binary Authorization, Cloud Audit Logging, and HMAC integrity hashing. |
| SC-16(02) | Transmission of Security Attributes: Anti-Spoofing | Implements anti-spoofing mechanisms to prevent adversaries from falsifying security attributes. (CCI-004905) | Section 23 | Access Context Manager and VPC Service Controls ingress condition enforcement. |
| SC-17 | Public Key Infrastructure Certificates | Issues public key certificates under DoDI 8520.02 via approved PKI CAs. (CCI-001159, CCI-002456, CCI-004909) | Section 24 | {{ PKI_TRUST_TYPE }}, Federal Bridge CA, and Google Cloud Certificate Authority Service (CAS). |
| SC-18 | Mobile Code | Prohibits unacceptable mobile code; blocks automatic execution in scriptable applications. (CCI-001160, CCI-001163, CCI-001164, CCI-001165, CCI-001166, CCI-001167, CCI-001168, CCI-001169, CCI-001170, CCI-001171, CCI-001172, CCI-001662, CCI-001687, CCI-001688, CCI-001695, CCI-002457, CCI-002458, CCI-002459, CCI-002460) | Section 25 | Mobile code execution disabled on virtual hosts; user authorization required for scripts per DoDI 8500.01. |
| SC-23 | Session Authenticity | Protects session authenticity using FIPS 140-validated random session IDs, invalidates at logout, trusts DoD CAs. (CCI-001184, CCI-001185, CCI-001188, CCI-001189, CCI-001664, CCI-002469, CCI-002470) | Section 29 | IAP session tokens generated with FIPS randomness, immediate token invalidation on logout, and {{ PKI_TRUST_TYPE }} trust anchors. |
| SC-24 | Fail in Known State | Fails to a known secure state across all failure types on all system components, preserving state info. (CCI-001190, CCI-001191, CCI-001192, CCI-001193, CCI-001665) | Section 30 | Fail-closed stateful firewall filtering, BGP sub-second BFD reconvergence, and persistent error logging. |
| SC-28 | Protection of Information at Rest | Protects confidentiality and integrity of all info at rest across components/media using FIPS cryptography. (CCI-001199, CCI-002472, CCI-002473, CCI-002474, CCI-002475, CCI-002476, CCI-002477, CCI-002478, CCI-002479, CCI-004910, CCI-004911) | Section 31 | Mandatory AES-256 Cloud KMS CMEK encryption on Compute disks, GCS buckets, Cloud SQL, and BigQuery. |
| SC-28(02) | Protection of Information at Rest: Offline Storage | Moves backups, old logs, and inactive keys to secure offline storage. (CCI-002477, CCI-002478, CCI-002479) | Section 31 | Cloud Storage Archive tier with Object Retention Lock for long-term audit and backup archives per DoDI 8510.01. |
| SC-28(03) | Protection of Information at Rest: Cryptographic Keys | Protects cryptographic keys in hardware key stores backed by FIPS 140-validated cryptographic modules. (CCI-004910, CCI-004911) | Section 31 | Google Cloud KMS HSM FIPS 140-3 Level 3 hardware key storage per CNSSI 4005. |
| SC-38 | Operations Security | Employs OPSEC controls (access controls, marking, need-to-know) across SDLC per DoDD 5205.02E. (CCI-002528, CCI-002529) | Section 32 | Role-based access control, {{ SENSITIVITY_CLASSIFICATION }} metadata tagging, and restriction of network schematics. |
| SC-39 | Process Isolation | Maintains separate execution domains for each executing system process. (CCI-002530) | Section 33 | Operating system address space isolation, unprivileged container namespaces, and gVisor isolation. |
| SC-41 | Port and I/O Device Access | Logically disables unused connection ports and I/O devices (USB, serial) not needed for mission. (CCI-002544, CCI-002545, CCI-002546) | Section 34 | Provisioning virtual instances without USB emulation; kernel-level disabling of unneeded peripheral interfaces per DoDI 8500.01. |
| SC-45 | System Time Synchronization | Synchronizes system clocks to authoritative time source (USNO) every 24 hours when drift exceeds 1 second. (CCI-004922, CCI-004923, CCI-004924, CCI-004925, CCI-004926, CCI-004927, CCI-004928, CCI-004929) | Section 35 | Google TrueTime NTP infrastructure traceable to US Naval Observatory (USNO) with automated synchronization per DoDI 8320.02. |
| SC-47 | Alternate Communications Paths | Establishes alternate communications paths not relying on primary infrastructure for C2. (CCI-004931) | Section 36 | Secondary Dedicated Interconnects, HA Cloud VPN failover circuits, and out-of-band cellular/satellite links per DoDI 8500.01. |



## Appendix B – FIPS 140-3 Cryptographic Module Architecture (Google Appendix Q)

In accordance with FIPS PUB 140-3, NIST SP 800-52 Rev. 2, and Google Services Appendix Q, {{ ORGANIZATION }} enforces validated cryptographic modules for all data at rest and data in transit across {{ SYSTEM_NAME }}:

| Protection Layer | Validated Cryptographic Module | FIPS Certificate # | Technical Enforcement Mechanism |
| :--- | :--- | :--- | :--- |
| **Hardware Key Security (`SC-12`)** | Hardware Security Module (HSM) / Titan HSM | FIPS 140-2/3 Level 3 | Cloud KMS Customer-Managed Encryption Keys (CMEK) |
| **Transport Encryption (`SC-8`)** | FIPS 140-3 Validated Crypto Module / BoringCrypto | FIPS 140-3 Cert #4407 | TLS 1.3 / IPsec Tunneling across Cloud Virtual Network SDN |
| **Storage Encryption (`SC-28`)** | AES-256 Cloud KMS CMEK Module | FIPS 140-3 Cert #4735 | Automated Bucket & Database Volume Encryption |
