# Stellar Engine

Stellar Engine is a fork of the Google Cloud Foundation Fabric repository that provides Terraform Infrastructure as Code for regulated Google Cloud landing zones with Assured Workloads overlays. Alongside the Terraform codebase, Stellar Engine includes [authorization documentation](/docs/path-to-authorization.md) for FedRAMP Moderate, FedRAMP High, DoD Impact Level 4, and DoD Impact Level 5 regimes, mapping NIST SP 800-53r5 controls to accelerate your Authorization to Operate process.

## 1. Getting started

This repository provides end-to-end blueprints and reusable Terraform modules for regulated Google Cloud environments:

- Bootstrap a production Google Cloud organization foundation with the [landing zone stages](./fast/).
- Deploy compliant workload architectures and network patterns from the reference [blueprints](./blueprints/).
- Compose custom infrastructure from lean, single-purpose Terraform [modules](./modules/).

Deployment and stage-linking scripts (`scripts/*.sh` and `fast/stage-links.sh`) require a POSIX-compliant shell environment such as Linux, macOS, Google Cloud Shell, or WSL2 on Windows. Native Windows shells, including PowerShell, Command Prompt, Git Bash, `MINGW64`, and Cygwin, are not supported due to POSIX path, symbolic link (`ln -s`), and line-ending requirements. See the [Deployment Prerequisites](./docs/prerequisites.md) and [Scripts README](./scripts/README.md) for setup details.

## 2. Target audience

Stellar Engine supports organizations and engineering teams that operate in regulated sectors with strict security and compliance mandates:

- Government agencies and defense contractors operating FedRAMP Moderate, FedRAMP High, IL4, and IL5 environments.
- Regulated commercial organizations managing overlapping federal and industry security frameworks.
- Universities and research institutions hosting government-funded workloads that require compliant cloud boundaries.

## 3. Key benefits

Deploying a landing zone with Stellar Engine accelerates compliance readiness and standardizes cloud operations:

- Pre-built NIST SP 800-53r5 control mappings for FedRAMP Moderate, FedRAMP High, IL4, and IL5 fast-track the Authorization to Operate process with pre-validated configurations.
- Infrastructure as Code embeds security and compliance controls directly into Terraform so requirements apply consistently across deployments.
- Repeatable landing zone stages enforce architectural standards across development, testing, integration, and production environments.
- Modular configurations tailored for Assured Workloads adapt cleanly to adjacent regulatory frameworks.
- Automated provisioning reduces setup time, operational overhead, and manual configuration drift.
- Native integration with Google Cloud Assured Workloads enforces data residency, personnel access controls, and encryption guardrails for government and defense workloads.
- Built-in organization policies, KMS configurations, and audit logging implement foundational NIST controls from initial deployment.
- Reference guides walk platform and security teams through architecture, deployment, and control inheritance.

## 4. Assured Workloads

Google Cloud Assured Workloads helps regulated organizations enforce compliance boundaries across cloud resources. You can provision folders aligned with frameworks such as FedRAMP, DoD Impact Levels, HIPAA, CJIS, and GDPR without sacrificing operational velocity. See the [Assured Workloads documentation](https://cloud.google.com/security/products/assured-workloads?hl=en) for supported regimes and pricing details.

## 5. FAST organization stages

Setting up a production-ready Google Cloud organization requires coordinated identity, resource hierarchy, networking, and security controls. Stellar Engine's [FAST](./fast/) stages provide both an enterprise organization design and a Terraform reference implementation tailored for Assured Workloads.

## 6. Terraform modules

The modules under `modules/` support rapid composition and remain simple enough to fork and audit in environments that restrict third-party dependencies. Upstream Cloud Foundation Fabric modules are synced in place via three-way merge as documented in the [upstream sync guide](./docs/upstream-sync.md); legacy `-se` copies remain only where listed there rather than creating new `-se` module copies.

Every module stays close to the underlying provider resources, manages IAM bindings alongside resource creation, supports multi-resource instantiation where appropriate, and avoids external command side effects.

Select a consistent resource prefix before starting deployment so global resource names follow Google Cloud best practices and avoid naming collisions. See the [naming convention guide](/docs/naming-convention.md) for prefix and identifier rules.

The module catalog covers foundational identity, resource hierarchy, networking, encryption, and workload services. See each module's `README.md` file and matching blueprints for usage examples.

## 7. Workload blueprints

Stellar Engine provides workload blueprints aligned with [FRM](https://github.com/google/stellar-engine/tree/main/blueprints/fedramp-moderate), [FRH](https://github.com/google/stellar-engine/tree/main/blueprints/fedramp-high), and [IL5](https://github.com/google/stellar-engine/tree/main/blueprints/il5) baselines. These blueprints range from full boundary architectures such as Cloud Native Access Point to focused service deployments that you can adapt to tenant workloads.

See each blueprint's `README.md` file for prerequisites, inputs, and deployment steps.

## 8. Cybersecurity documentation

Stellar Engine provides generalized authorization templates that map NIST SP 800-53r5 controls to the deployed Terraform architecture. Request the authorization package templates through the [artifact request form](https://forms.gle/zdv7Gip4opmdhBqk7), and review the [Path to Authorization](/docs/path-to-authorization.md) guide before tailoring them to your system boundary.

## 9. Detailed deployment guide

The Detailed Deployment Guide walks you through deploying a compliant Google Cloud landing zone across FedRAMP Moderate, FedRAMP High, IL4, and IL5 environments. Deployment runs across four sequential stages:

- Stage 0 initializes bootstrap automation projects, state buckets, organization policies, and stage service accounts.
- Stage 1 builds the folder hierarchy and tenant project structure for resource management.
- Stage 2 provisions hub-and-spoke Shared VPC networking, including Network Connectivity Center topologies for FedRAMP and Palo Alto Networks Next-Generation Firewalls for IL5.
- Stage 3 configures centralized security controls, Customer-Managed Encryption Keys, VPC Service Controls, and audit logging.

The guide also covers Access Transparency prerequisites, IAM group setup, organization onboarding, and KMS troubleshooting. Read the [Detailed Deployment Guide](./docs/ddg.md) for step-by-step instructions.

## 10. Technical design document

The Technical Design Document defines the reference architecture for deploying secure, compliant Google Cloud foundations designed for federal Authorization to Operate assessments.

The document covers IAM least-privilege role groups, service account isolation, folder and project hierarchy, hub-and-spoke Shared VPC networking, VPC Service Controls, encryption at rest and in transit, and centralized audit logging and monitoring. Pair the [Technical Design Document](./docs/tdd.md) with the Security Best Practices Guide to harden your deployment against operational threats.

## 11. Security best practices

The Security Best Practices Guide details operational hardening steps for FedRAMP Moderate, FedRAMP High, and IL5 deployments on Google Cloud. It covers least-privilege IAM administration, group visibility restrictions, multi-factor authentication enforcement, Cloud Shell restrictions, segmented SIEM logging, Customer-Managed Encryption Keys, Cloud Storage access hygiene, and regional data residency controls.

The guide incorporates findings from Mandiant penetration testing to help you mitigate privilege escalation, lateral movement, and data exfiltration risks. Read the [Security Best Practices Guide](docs/security-best-practices.md) for post-deployment hardening procedures.

## 12. Contributing

You can contribute to Stellar Engine by forking the repository, making your changes on a feature branch, and submitting a pull request that follows the repository formatting and security standards.

Run the repository checks before you open a pull request. The `pyproject.toml` and `uv.lock` files at the repository root pin the Python version and packages for the `tools/` scripts and the `tests/` suite, so [uv](https://docs.astral.sh/uv/getting-started/installation/) is the only Python tool you install:

- Run `uv run pytest` to execute the Python unit tests.
- Run `bash tools/run_tests.sh` to execute the Python unit tests, shell script tests, and Python syntax checks.
- Run `bash tools/lint.sh` to validate license headers, documentation tables, links, naming conventions, formatting, and blueprint metadata.

Ensure the `terraform` and `tflint` binaries are available on your `PATH` before running `tools/lint.sh`.

## 13. Issue reporting

Report bugs, request features, or document deployment issues by [creating an issue](https://github.com/google/stellar-engine/issues) in the GitHub repository with clear reproduction steps.

## 14. Frequently asked questions

This section answers common technical and operational questions about adopting, supporting, and contributing to Stellar Engine.

### Project history

Google's Technical Delivery team launched Stellar Engine in summer 2022 as a compliance-focused fork of Cloud Foundation Fabric to replace repetitive manual builds of federal landing zones. In March 2024, a gap analysis expanded the project scope to include NIST-mapped Authorization to Operate documentation alongside the Terraform foundation.

### Core features

Stellar Engine orchestrates bootstrap, resource management, networking, and security landing zone stages supporting FedRAMP Moderate, FedRAMP High, and DoD Impact Level 5 baselines. It pairs these Terraform stages with pre-integrated partner firewall patterns such as Palo Alto Networks VM-Series and generalized templates for System Security Plans, Technical Design Documents, and Security Control Traceability Matrices mapped to NIST SP 800-53r5.

### Primary use cases

Teams use Stellar Engine to bootstrap tenant-isolated landing zones rapidly, accelerate Authorization to Operate packages through pre-mapped NIST security controls, deploy boundary traffic inspection, and standardize delivery across professional services and system integrator engagements.

### Cloud Foundation Fabric differences

Cloud Foundation Fabric is a general-purpose Terraform library optimized for commercial environments and maintained by Google Cloud commercial Professional Services. Stellar Engine is a specialized framework built for regulated public sector environments and maintained by Google Public Sector. Keeping NIST documentation packages and strict Assured Workloads constraints in Stellar Engine avoids adding regulatory complexity to commercial Cloud Foundation Fabric deployments while allowing both teams to share upstream module improvements.

### Choosing Cloud Foundation Fabric

Choose upstream Cloud Foundation Fabric when your workloads do not require federal compliance baselines such as FedRAMP or IL5, or when your organization already operates a mature custom Terraform platform with dedicated compliance engineering pipelines. Otherwise, start with Stellar Engine for regulated public sector landing zones.

### Roadmap and backlog

Track upcoming features on the [GitHub roadmap](https://github.com/orgs/google/projects/171) and review active work items in the [project backlog](https://github.com/orgs/google/projects/171/views/1).

### Stellar Scanner status

Stellar Scanner is no longer supported. Maintainers are evaluating modern security scanners to integrate automated policy and vulnerability checks directly into the Stellar Engine development workflow.

### Support model evolution

After early iterations and a 2024 modernization effort, Stellar Engine operates as an open-source GitHub repository with community-driven support. Planned improvements include structured sprint releases, automated pull request security checks, and expanded public documentation.

### SLA support model

Stellar Engine has no commercial SLA-backed support and operates under a collaborative open-source model. Rather than encouraging one-off fork-and-forget deliveries, the project enables organizations to pull upstream module updates, security patches, and compliance improvements into active deployments.

### Project longevity

As open-source software, Stellar Engine carries no commercial lifecycle guarantees, but it leaves your organization in full ownership of a documented, auditable Terraform codebase and compliance baseline even as upstream projects evolve.

### Customer expectations

Position Stellar Engine as an open-source solution accelerator for deploying compliant Google Cloud landing zones rather than a commercially licensed Google product. Your organization or system integrator owns and operates the deployed infrastructure.

### Sharing issues and requests

Open [GitHub issues](https://github.com/google/stellar-engine/issues) for bug reports and feature requests, submit pull requests directly when contributing fixes, or connect with maintainers in the [Google Chat space](https://chat.google.com/room/AAQAWBaZDBE).

### Technical feedback channels

Join the [Google Chat space](https://chat.google.com/room/AAQAWBaZDBE) to share deployment feedback or ask roadmap questions. Contributors actively review community feedback to help unblock customer deployments.

## 15. Vulnerability rewards program

Stellar Engine is not an officially supported Google product and is not eligible for the [Google Open Source Software Vulnerability Rewards Program](https://bughunters.google.com/open-source-security).
