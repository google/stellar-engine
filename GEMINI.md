# Stellar Engine AI assistant guidelines

## 1 Project overview

Stellar Engine is a fork of Google Cloud Foundation Fabric that provides
Terraform Infrastructure as Code to help Google Cloud customers deploy secure,
compliant landing zones. It targets environments that require Assured
Workloads overlays across FedRAMP Moderate, FedRAMP High, IL4, and IL5, and
includes documentation mapping NIST 800-53r5 controls to accelerate
Authorization to Operate processes.

## 2 Core principles

Follow these principles when you create or modify Terraform blueprints,
modules, and landing zone stages.

1. Reuse existing base configurations and modules instead of redefining common
   elements.
   * Inherit from and extend base variable definitions in each module or
     blueprint `variables.tf` file, such as `modules/net-vpc/variables.tf`,
     instead of hardcoding values.
   * Provision service accounts and IAM bindings through
     `modules/iam-service-account/` instead of creating overlapping custom
     service accounts.
   * Connect new blueprints to the VPCs, subnets, and firewall rules provided
     by `modules/net-vpc/` and `modules/net-vpc-firewall/` rather than
     creating parallel network structures.
2. Design blueprints to be modular and composable by building on the reusable
   modules under `modules/`.
3. Include a `README.md` file that documents the purpose, inputs, outputs, and
   dependencies of every module and blueprint that you add or modify.
4. Follow the naming conventions in `docs/naming-convention.md` so variables,
   resources, modules, and files stay consistent across the repository.
5. Apply GCP security best practices and least-privilege IAM across all
   configurations for the target compliance regime across FedRAMP Moderate,
   FedRAMP High, IL4, and IL5.

## 3 Key resources

Use these canonical directories and files when authoring or reviewing changes.

* Base variable definitions live in each module and blueprint `variables.tf`
  file, such as `modules/net-vpc/variables.tf` and
  `blueprints/il5/bigquery/variables.tf`.
* Core service account definitions live in `modules/iam-service-account/`.
* Base networking modules live under `modules/net-vpc/`,
  `modules/net-vpc-firewall/`, and the other `net-*` directories in
  `modules/`.
* Naming conventions live in `docs/naming-convention.md`.
* Shared workload blueprints live under `blueprints/il5/` such as
  `blueprints/il5/bigquery/` with matching Git `120000` directory symlinks
  under `blueprints/fedramp-high/`, while standalone FedRAMP High blueprints
  such as `blueprints/fedramp-high/cloud-run/` use regular directories.
* Organization landing zone stages live under `fast/stages-aw/`.

## 4 Assistant guidance

Follow these steps when you generate or modify code in this repository.

1. Apply the core principles and canonical paths from the previous sections.
2. Check whether an existing module in `modules/` or stage construct in
   `fast/stages-aw/` covers the requirement before declaring a new resource,
   especially for networking, service accounts, IAM, and common variables.
3. Follow `docs/naming-convention.md` for all resource, variable, and file
   names.
4. Ask the user why existing components do not fit before creating a new
   foundational resource such as a base VPC or privileged service account.
5. Read the `README.md` file of any module under `modules/` before calling it
   to verify its inputs, outputs, and version constraints.

## 6 Changelog and release notes

* Follow every top-level `* ` entry in `CHANGELOG.md`, release pull requests, GitHub Releases, and annotated Git tags with an indented `  * ...` sub-bullet sentence in plain English that summarizes what changed and how it affects deployments, rather than leaving bare one-line commit titles.
* When preparing a release pull request on `release-please--branches--main`, add the `  * ...` sub-bullets to `CHANGELOG.md` and the release pull request body (`RELEASES.md`).
