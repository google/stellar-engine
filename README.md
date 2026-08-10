## Introduction

Stellar Engine is a fork of the Google Cloud Foundation Fabric (CFF) repository, aimed at providing Infrastructure as Code (IaC) for Google Cloud Platform (GCP) customers who need to create a landing zone environment with the Assured Workload overlays. In addition to the IaC, there is [documentation available](./docs/path-to-authorization.md) for FedRAMP High (FRH), FedRAMP Moderate (FRM), Department of Defense (DoD) Impact Level 4 (IL4) and DoD Impact Level (IL5) compliance regimes that provide a mapping of National Institute of Standards and Technology (NIST) 800-53r5 controls to enable projects that leverage the Stellar Engine codebase to accelerate the speed at which an Authorization to Operate (ATO) can be attained.

## Getting Started

This repository provides **end-to-end blueprints** and a **suite of Terraform modules** for Google Cloud, which support different use cases:

- Google Cloud Organization [landing zone blueprint](./fast/) used to bootstrap real-world cloud foundations
- Reference [blueprints](./blueprints/) used to securely deep dive into network patterns or product features
- Comprehensive source of lean [modules](./modules/) that lend themselves well to changes

## Target Audience and Benefits

The target audience for Stellar Engine is organizations and teams that operate in regulated industries or require robust compliance and security frameworks. Below are a few examples of these such users:

- **Government Agencies:** Agencies and contractors, such as those that work with FRH, IL4, and IL5 environments.  <br />
- **Regulated Industries:** Regulated industries often face overlapping compliance and security requirements; Stellar Engine can simplify that.  <br />
- **Educational and Research Institutions:** Universities and research organizations working on government-funded projects that require secure and compliant cloud environments.  <br />

## Benefits of Stellar Engine

Stellar Engine offers several significant benefits, particularly for organizations operating in regulated environments or requiring high levels of compliance and security. Here are the key advantages based on the summary:

- **Pre-Built Compliance Mappings:** The inclusion of documentation mapping NIST 800-53r5 controls for FRH, FRM, IL4, and IL5 simplifies the process of achieving compliance. This allows organizations to fast-track their ATO processes by leveraging pre-validated configurations.  <br />
IaC for Compliance: By embedding compliance requirements into IaC, Stellar Engine ensures that key controls are implemented consistently and automatically.   <br />
- **Consistency and Scalability:** Utilizing IaC enables repeatable and reliable deployment of landing zones, ensuring that infrastructure adheres to best practices and compliance standards.  <br />
- **Flexibility:** While tailored for Assured Workload overlays, Stellar Engine serves as a foundation for other compliance regimes, making it adaptable to various regulatory requirements.  <br />
- **Efficiency:** Automating infrastructure deployment reduces setup time and operational overhead, freeing up resources for other critical tasks and reducing manual effort and the risk of human error. <br />
- **Assured Workload Overlays:** By integrating with Google Cloud’s Assured Workloads, Stellar Engine provides a robust framework for secure and compliant cloud environments, particularly for sensitive workloads in government and defense sectors.  <br />
- **Control Implementation:** Many NIST controls are directly addressed via IaC, ensuring that security measures are embedded into the infrastructure from the start.  <br />
- **Comprehensive Documentation:** The availability of detailed guidance helps teams navigate the complexities of compliance and understand the implementation of controls.  <br />

## Assured Workloads

Google Cloud Assured Workloads is a service designed to help organizations meet regulatory and compliance requirements when using cloud resources. It simplifies the process of creating and managing cloud environments that align with specific compliance frameworks, such as FedRAMP, HIPAA, CJIS, or GDPR. By leveraging GCP Assured Workloads, organizations can confidently deploy and manage workloads in the cloud while meeting strict compliance requirements, all without compromising on security or operational efficiency.

## FAST Stages - GCP Organization Blueprints

Setting up a production-ready GCP Organization is often a time-consuming process. Stellar Engine's [FAST](./fast/) stages aim to speed up this process via two complementary goals. On the one hand, FAST provides a design of a GCP Organization that includes the typical elements required by enterprise customers. Secondly, we provide a reference implementation of the FAST design using Terraform. For pricing and other information about Assured Workloads, please see Google's documentation [here](https://cloud.google.com/security/products/assured-workloads?hl=en).

## Modules

The suite of modules in this repository is designed for rapid composition and reuse, and to be reasonably simple and readable so that they can be forked and changed where the use of third-party code and sources is not allowed. Modules that end with "se" have been modified from the original CFF versions to allow for use cases specific to Stellar Engine, while still allowing for upstream updates from CFF. Modifications to modules should continue to follow this paradigm.

All modules share a similar interface where each module tries to stay close to the underlying provider resources, support IAM together with resource creation and modification, offer the option of creating multiple resources where it makes sense (e.g. not for projects), and be completely free of side-effects (e.g. no external commands).

A well-defined naming standard is used across Stellar Engine to ensure adherence to Google Cloud's best practices, naming requirements, and naming collision avoidance for global resources. The Google Cloud naming standard documentation is here and will be used before the Stellar Engine deployment begins by choosing a naming standard that will flow through the Google Cloud infrastructure state.

The current modules support most of the core foundational and networking components used to design end-to-end infrastructure, with more modules in active development for specialized compute, security, and data scenarios.

For more information and usage examples see each module's README file, as well as any associated blueprints.

## End-to-End Blueprints

Stellar Engine currently offers blueprints that are compliant with [FRH](https://github.com/google/stellar-engine/tree/main/blueprints/fedramp-high) and [IL5](https://github.com/google/stellar-engine/tree/main/blueprints/il5) baselines. </br>
These blueprints range from full end-to-end services like a Cloud Native Access Point (CNAP), to ad-hoc services that are designed to be molded to users' individual use cases.

For more information, please look at each blueprint's README file.

## Cybersecurity Documentation

In addition to the IaC, Stellar Engine provides supporting documentation that maps NIST 800-53r5 controls for users leveraging the IaC. This documentation is designed to streamline achieving ATO by providing generalized templates. All documentation can be requested [here](https://forms.gle/zdv7Gip4opmdhBqk7). For how to utilize these documents, please see the following [Path to Authorization](./docs/path-to-authorization.md) guide.

## Detailed Deployment Guide

The Stellar Engine Cloud Foundation Fabric Detailed Deployment Guide (DDG) outlines a structured process for deploying a secure, compliant infrastructure on GCP using IaC. Designed to support compliance with standards such as FRH, IL4, and IL5, the guide enables organizations to create a foundational "landing zone" with Assured Workload overlays. It includes mappings of NIST 800-53r5 controls to streamline achieving ATO. The deployment process is divided into stages, each focusing on specific components like resource management, networking, and security configuration.

Key stages include Stage 0 (Bootstrap), which initializes the infrastructure, creates core Google Cloud Projects, and sets up service accounts; Stage 1 (Resource Management), which organizes Google Cloud Folders and Google Cloud Projects for tenants; and Stage 2 (Network Creation), which configures networking, including advanced setups like Palo Alto NGFWs for IL5 environments. The final stage, Stage 3 (Security and Audit Account Configuration), establishes security protocols, including Customer Managed Encryption Keys (CMEK) requirements and logging for audit purposes. Each stage requires detailed configuration of Terraform variables and adherence to prerequisites like IAM roles, service account setups, and enabling Google Cloud services.

The guide emphasizes the importance of compliance, providing instructions for enabling Access Transparency and managing IAM roles effectively. Appendices include steps for creating new GCP Organizations and troubleshooting common issues like KMS key errors. Overall, the document serves as a comprehensive manual for deploying compliant, scalable, and secure cloud environments tailored to government and regulated industry requirements.

For more information, please look at the [DDG](./docs/ddg.md).

## Technical Design Document

The Stellar Engine Technical Design Document (TDD) outlines a comprehensive framework for deploying secure, compliant, and scalable GCP infrastructure, particularly tailored for Federal ATO processes. This document highlights a structured approach to building a cloud foundation using IaC principles.

The document delves into key aspects such as Identity and Access Management (IAM), Google Cloud Organization configuration, Google Cloud Project hierarchy, networking, and security. It emphasizes principles like least privilege for IAM, structured role group management, and secure service account configurations. The networking section introduces a hub-and-spoke VPC architecture, leveraging shared VPCs and service controls to ensure isolation and secure interservice communications. Additionally, it provides guidelines for implementing encryption at rest and in transit, logging and monitoring strategies, and robust access control mechanisms to meet compliance needs. This document is a vital resource for teams aiming to adopt GCP with a focus on security, compliance, and scalability. The TDD is used in conjunction with the Security Best Practices Guide for hardening the deployment against real-world cyber threats and attacks.

For more information, please look at the [TDD](./docs/tdd.md).

## Security Best Practices Guide

The Stellar Engine Security Best Practices Guide (SBPG) outlines a robust framework for deploying secure and compliant GCP infrastructure. Designed for organizations requiring adherence to FRH and IL5 standards, it employs IaC principles via Terraform. The Stellar Engine facilitates the automated creation of a baseline GCP environment, supporting modular deployment of both Google and approved third-party services. Its hierarchical architecture ensures effective organization, leveraging role-based access control (RBAC), strict IAM policies, and a hub-and-spoke VPC networking design for isolation and scalability.

The document emphasizes best practices in identity and access management, security monitoring, and compliance. IAM configurations focus on the principle of least privilege, with automation enabling minimal human interaction during setup. Security features include encryption-at-rest, TLS enforcement, and centralized logging and monitoring through audit logs, VPC flow logs, and other diagnostics. The system supports Assured Workloads, providing region-specific data residency and compliance settings to meet regulatory requirements.

Accompanied by the SBPG, the document incorporates recommendations from penetration testing conducted by Mandiant, aimed at hardening the system against real-world cyber threats. The guide advocates for enforcing multi-factor authentication (MFA), segmenting security monitoring tools, and integrating Security Information Event Management (SIEM) solutions for proactive threat detection. Together, these resources enable secure, scalable, and compliant cloud operations for high-security use cases.

For more information, please look at the [Security Best Practices Guide](https://docs.google.com/document/d/1uv62Fqg73r9oJNP-NPZebpzoBom8rOgLoHkiMZPutbo/edit?usp=sharing). NOTE: you will need to request permissions for it.

## Contributing

We welcome contributions to Stellar Engine! Since this is an open-source project, you can contribute by forking the repository, making your changes, and submitting a pull request. 

Please ensure your code adheres to our formatting and security standards. 

## Issue Reporting

If you encounter any bugs, have feature requests, or run into deployment issues, please [create an issue](https://github.com/google/stellar-engine/issues) on our GitHub repository. Keep the issue description clear and provide steps to reproduce if applicable.

## Frequently Asked Questions 

Whether you are aiming to clear federal compliance hurdles, unblock a customer deployment, or contribute code, this document covers the essential technical details of the Stellar Engine framework.

### When and how did Stellar Engine get started? 

The project launched in the summer of 2022 when the Technical Delivery team within Google grew tired of repeatedly manual-building secure, compliant landing zones for federal customers. To establish a repeatable baseline, we built a specialized compliance-focused fork of Cloud Foundation Fabric. In March 2024, a comprehensive gap analysis shifted the project's strategic focus toward generating actual ATO documentation, transforming it into the accelerator it is today.

### What are the core features? 

The framework includes hierarchical staged orchestration divided into bootstrap, resource management, networking, and security stages. It supports FedRAMP Moderate, FedRAMP High, and DoD Impact Level 5 compliance configurations by default. Additionally, it provides pre-packaged templates for System Security Plans, Technical Design Documents, and Security Controls Traceability Matrices mapped to NIST SP 800-53r5 controls, alongside pre-integrated security partner configurations like Palo Alto Networks firewalls.

### What are the primary use cases? 

The main use cases are bootstrapping secure, tenant-isolated landing zones in hours instead of months, fast-tracking authorizations to operate by mapping infrastructure to NIST security controls, deploying boundary traffic inspection, and providing a standardized, repeatable baseline for professional services and partner deliveries to minimize deployment risk.

### How does Stellar Engine differ from Cloud Foundation Fabric, and why wasn't it just merged directly? 

Cloud Foundation Fabric (CFF) is a general-purpose, global set of HashiCorp Terraform Infrastructure as Code (IAC) optimized for typical commercial environments. CFF is internally supported by commercial professional services (PSO). 

Stellar Engine is a specialized, tactical framework built specifically for highly regulated public sector environments. Stellar Engine is maintained by Google Public Sector (GPS). 

While merging massive NIST-mapped documentation generation and aggressive security constraints into the core of Cloud Foundation Fabric would overcomplicate it for the average commercial user, we are actively working on building a relationship to understand where there are opportunities for supporting one another.

### Which customers should use Cloud Foundation Fabric instead of Stellar Engine?

Standard Cloud Foundation Fabric is ideal for customers who do not have rigorous compliance benchmarks like FedRAMP or IL5, or for highly mature organizations that already possess massive, custom Infrastructure as Code codebases, large internal platform teams, and their own compliance pipelines. If they do not fall into those rare categories, Stellar Engine is the recommended path.

### Where are the Stellar Engine roadmap and backlog located? 

The roadmap is hosted on [GitHub](https://github.com/orgs/google/projects/171) along with the [backlog](https://github.com/orgs/google/projects/171/views/1).

### Is Stellar Scanner still supported? 

Stellar Scanner is no longer supported. The team is currently evaluating modern internal and external security scanners to eventually integrate automated checks directly into the modern Stellar Engine framework and development lifecycle.

### What does support look like across the past, present, and future? 

In the past, the project had multiple restarts due to resource constraints before being modernized in early 2024. Currently, it is maintained as an open-source repository on GitHub with ad-hoc community support. In the future, the team aims to establish structured sprint rollouts, automated security checks for pull requests, a public documentation library, and a formalized Turbo Launch process to publish guides on official Cloud Docs.

### Do customers have a path to SLA-based support? 

No official SLA-based support exists. Stellar Engine operates on a collaborative open-source model. However, the project is moving away from historical fork-and-forget delivery methods. The team is fostering a community framework where customers can regularly pull upstream updates, security patches, and compliance improvements back into their active deployments.

### What guarantees do customers have that Google will not deprecate the project? 

As with any open-source software, there are no commercial guarantees. However, Stellar Engine is best viewed as a high-velocity launchpad. Even if the upstream project evolves, it accelerates your initial accreditation and leaves you with a fully documented, robust, and highly secure codebase that your organization owns and controls completely.

### What is the appropriate messaging for interested parties? 

Google's Field teams should actively encourage its use as the best established way to deploy foundational, compliant landing zones on Google Cloud. However, they must clearly communicate that it is an open-source solution accelerator, not a commercially licensed Google product. The customer or their system integrator ultimately owns and manages the deployed environment.

### How should issues or feature requests be shared with the maintainers? 

Interested parties are encouraged to open [GitHub issues](https://github.com/google/stellar-engine/issues) for bug reports or feature requests. If they have development resources, they can submit pull requests directly. They can also engage with maintainers in the [Google Chat space](https://chat.google.com/room/AAQAWBaZDBE). 

### How should interested parties engage for technical feedback or roadmap questions? 

Interested parties should join the [Google Chat space](https://chat.google.com/room/AAQAWBaZDBE). While the project is maintained on a 20 percent basis by many contributors, the team is dedicated to reviewing feedback and unblocking customer deployments.

## Google’s Open Source Software Vulnerability Rewards Program (OSS VRP)

This is not an officially supported Google solution. This project is not eligible for the [Google Open Source Software Vulnerability Rewards Program](https://bughunters.google.com/open-source-security).
