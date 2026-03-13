## Introduction

Stellar Engine is a fork of the Google Cloud Foundation Fabric (CFF) repository, aimed at providing Infrastructure as Code (IaC) for Google Cloud Platform (GCP) customers who need to create a landing zone environment with the Assured Workload overlays. In addition to the IaC, there is documentation available for both the DISA FedRAMP High (FRH), DoD Impact Level 4 (IL4) and DoD Impact Level (IL5) compliance regimes that provide a mapping of National Institute of Standards and Technology (NIST) 800-53r5 controls to enable projects that leverage the Stellar Engine codebase to accelerate the speed at which an Authorization to Operate (ATO) can be attained.

## Getting Started

This repository provides **end-to-end blueprints** and a **suite of Terraform modules** for Google Cloud, which support different use cases:

- Google Cloud Organization [landing zone blueprint](fast/) used to bootstrap real-world cloud foundations
- reference [blueprints](./blueprints/) used to deep dive into network patterns or product features
- a comprehensive source of lean [modules](./modules/) that lend themselves well to changes

## Target Audience and Benefits

The target audience for Stellar Engine is organizations and teams that operate in regulated industries or require robust compliance and security frameworks. Below are a few examples of these such users:

<mark>Government Agencies:</mark> Agencies and contractors, such as those that work with FRH, IL4, and IL5 environments.  <br />
<mark>Regulated Industries:</mark> Regulated industries often face overlapping compliance and security requirements; Stellar Engine can simplify that.  <br />
<mark>Educational and Research Institutions:</mark> Universities and research organizations working on government-funded projects that require secure and compliant cloud environments.  <br />

## Benefits of Stellar Engine

Stellar Engine offers several significant benefits, particularly for organizations operating in regulated environments or requiring high levels of compliance and security. Here are the key advantages based on the summary:

<mark>Pre-Built Compliance Mappings:</mark> The inclusion of documentation mapping NIST 800-53r5 controls for FRH, IL4, and IL5 simplifies the process of achieving compliance. This allows organizations to fast-track their ATO processes by leveraging pre-validated configurations.  <br />
<mark>IaC for Compliance:</mark> By embedding compliance requirements into IaC, Stellar Engine ensures that key controls are implemented consistently and automatically.   <br />
<mark>Consistency and Scalability:</mark> Utilizing IaC enables repeatable and reliable deployment of landing zones, ensuring that infrastructure adheres to best practices and compliance standards.  <br />
<mark>Flexibility:</mark> While tailored for Assured Workload overlays, Stellar Engine serves as a foundation for other compliance regimes, making it adaptable to various regulatory requirements.  <br />
<mark>Efficiency:</mark> Automating infrastructure deployment reduces setup time and operational overhead, freeing up resources for other critical tasks and reducing manual effort and the risk of human error. <br />
<mark>Assured Workload Overlays:</mark> By integrating with Google Cloud’s Assured Workloads, Stellar Engine provides a robust framework for secure and compliant cloud environments, particularly for sensitive workloads in government and defense sectors.  <br />
<mark>Control Implementation:</mark> Many NIST controls are directly addressed via IaC, ensuring that security measures are embedded into the infrastructure from the start.  <br />
<mark>Comprehensive Documentation:</mark> The availability of detailed guidance helps teams navigate the complexities of compliance and understand the implementation of controls.  <br />

## Assured Workloads

Google Cloud Assured Workloads is a service designed to help organizations meet regulatory and compliance requirements when using cloud resources. It simplifies the process of creating and managing cloud environments that align with specific compliance frameworks, such as FedRAMP, HIPAA, CJIS, or GDPR. By leveraging GCP Assured Workloads, organizations can confidently deploy and manage workloads in the cloud while meeting strict compliance requirements, all without compromising on security or operational efficiency.


## FAST Stages - GCP Organization Blueprints

Setting up a production-ready GCP Organization is often a time-consuming process. Stellar Engine's [FAST](fast/) stages aim to speed up this process via two complementary goals. On the one hand, FAST provides a design of a GCP Organization that includes the typical elements required by enterprise customers. Secondly, we provide a reference implementation of the FAST design using Terraform. For pricing and other information about Assured Workloads, please see Google's documentation [here](https://cloud.google.com/security/products/assured-workloads?hl=en).

## Modules

The suite of modules in this repository is designed for rapid composition and reuse, and to be reasonably simple and readable so that they can be forked and changed where the use of third-party code and sources is not allowed. Modules that end with "se" have been modified from the original CFF versions to allow for use cases specific to Stellar Engine, while still allowing for upstream updates from CFF. Modifications to modules should continue to follow this paradigm.

All modules share a similar interface where each module tries to stay close to the underlying provider resources, support IAM together with resource creation and modification, offer the option of creating multiple resources where it makes sense (e.g. not for projects), and be completely free of side-effects (e.g. no external commands).

A well-defined naming standard is used across Stellar Engine to ensure adherence to Google Cloud's best practices, naming requirements, and naming collision avoidance for global resources. The Google Cloud naming standard documentation is [here](documentation/naming-convention.md) and will be used before the Stellar Engine deployment begins by choosing a naming standard that will flow through the Google Cloud infrastructure state.

The current modules support most of the core foundational and networking components used to design end-to-end infrastructure, with more modules in active development for specialized compute, security, and data scenarios.

For more information and usage examples see each module's README file, as well as any associated blueprints.

## End-to-End Blueprints

Stellar Engine currently offers blueprints that are compliant with [FRH](https://github.com/google/stellar-engine/tree/main/blueprints/fedramp-high) and [IL5](https://github.com/google/stellar-engine/tree/main/blueprints/il5) baselines. </br>
These blueprints range from full end-to-end services like a Cloud Native Access Point (CNAP), to ad-hoc services that are designed to be molded to users' individual use cases.

For more information, please look at each blueprint's README file.

## Cybersecurity Documentation

In addition to the IaC, Stellar Engine provides supporting documentation that maps NIST 800-53r5 controls for users leveraging the IaC. This documentation is designed to streamline achieving ATO by providing generalized templates. All documentation is provided [here](https://drive.google.com/drive/folders/1NeWZcOuxysi7kUNRCFDd8CeHnxF14ywp). For how to utilize these documents, please see the following [Path to Authorization](docs/path-to-authorization.md) guide.

## Detailed Deployment Guide

The Stellar Engine Cloud Foundation Fabric Detailed Deployment Guide (DDG) outlines a structured process for deploying a secure, compliant infrastructure on GCP using IaC. Designed to support compliance with standards such as FRH, IL4, and IL5, the guide enables organizations to create a foundational "landing zone" with Assured Workload overlays. It includes mappings of NIST 800-53r5 controls to streamline achieving ATO. The deployment process is divided into stages, each focusing on specific components like resource management, networking, and security configuration.

Key stages include Stage 0 (Bootstrap), which initializes the infrastructure, creates core Google Cloud Projects, and sets up service accounts; Stage 1 (Resource Management), which organizes Google Cloud Folders and Google Cloud Projects for tenants; and Stage 2 (Network Creation), which configures networking, including advanced setups like Palo Alto NGFWs for IL5 environments. The final stage, Stage 3 (Security and Audit Account Configuration), establishes security protocols, including Customer Managed Encryption Keys (CMEK) requirements and logging for audit purposes. Each stage requires detailed configuration of Terraform variables and adherence to prerequisites like IAM roles, service account setups, and enabling Google Cloud services.

The guide emphasizes the importance of compliance, providing instructions for enabling Access Transparency and managing IAM roles effectively. Appendices include steps for creating new GCP Organizations and troubleshooting common issues like KMS key errors. Overall, the document serves as a comprehensive manual for deploying compliant, scalable, and secure cloud environments tailored to government and regulated industry requirements.

For more information, please look at the [DDG](docs/ddg.md).

## Technical Design Document

The Stellar Engine Technical Design Document (TDD) outlines a comprehensive framework for deploying secure, compliant, and scalable GCP infrastructure, particularly tailored for Federal ATO processes. This document highlights a structured approach to building a cloud foundation using IaC principles.

The document delves into key aspects such as Identity and Access Management (IAM), Google Cloud Organization configuration, Google Cloud Project hierarchy, networking, and security. It emphasizes principles like least privilege for IAM, structured role group management, and secure service account configurations. The networking section introduces a hub-and-spoke VPC architecture, leveraging shared VPCs and service controls to ensure isolation and secure interservice communications. Additionally, it provides guidelines for implementing encryption at rest and in transit, logging and monitoring strategies, and robust access control mechanisms to meet compliance needs. This document is a vital resource for teams aiming to adopt GCP with a focus on security, compliance, and scalability. The TDD is used in conjunction with the Security Best Practices Guide for hardening the deployment against real-world cyber threats and attacks.

For more information, please look at the [TDD](docs/tdd.md).

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


## Google’s Open Source Software Vulnerability Rewards Program (OSS VRP)

This is not an officially supported Google product. This project is not eligible for the [Google Open Source Software Vulnerability Rewards Program](https://bughunters.google.com/open-source-security).
