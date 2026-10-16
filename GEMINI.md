# Stellar Engine AI assistant guidelines

## 1 Project overview

Stellar Engine is a fork of the Google Cloud Foundation Fabric that provides
Infrastructure as Code to help Google Cloud Platform customers create
secure and compliant landing zones. It focuses on environments that require
Assured Workloads overlays, such as FedRAMP Moderate, FedRAMP High, IL4, and
IL5, and includes documentation that maps NIST 800-53r5 controls to accelerate
Authorization to Operate processes.

The key technologies are Terraform and GCP.

## 2 Core principles

Follow these principles when you create or modify Terraform blueprints and
modules in this repository.

1. Maximize reusability above all else by reusing existing base configurations
   and modules instead of redefining common elements.
   * Inherit from and extend the base variable definitions in the
     `variables.tf` file of each module and blueprint, such as
     `modules/net-vpc/variables.tf`, instead of hardcoding values.
   * Reuse the existing service account definitions and IAM policies in
     `modules/iam-service-account/`, avoid new service accounts with
     overlapping permissions, and always apply least privilege.
   * Connect new blueprints to the VPCs, subnets, and firewall rules that
     modules such as `modules/net-vpc/` and `modules/net-vpc-firewall/`
     provide rather than creating parallel or redundant network structures.
2. Design blueprints to be modular and composable by building on the existing
   modules in `modules/` and breaking complex deployments into smaller,
   reusable components.
3. Include a `README.md` with every new or modified module and blueprint that
   explains its purpose, inputs, outputs, and dependencies.
4. Follow the naming conventions in `docs/naming-convention.md` so that
   variables, resources, modules, and files stay consistent.
5. Apply GCP security best practices and least privilege in all
   configurations, and ensure compliance with the targeted regime, such as
   FedRAMP Moderate, FedRAMP High, IL4, or IL5.

## 3 Key resources

* Base variable definitions live in the `variables.tf` file of each module and
  blueprint, such as `modules/net-vpc/variables.tf` and
  `blueprints/il5/bigquery/variables.tf`.
* Core service account definitions live in `modules/iam-service-account/`.
* The base networking modules are `modules/net-vpc/` for VPCs and subnets and
  `modules/net-vpc-firewall/` for firewall rules, and the other `net-` modules
  in `modules/` provide the remaining networking components.
* The naming convention documentation lives at `docs/naming-convention.md`.
* `blueprints/il5/bigquery/` and `blueprints/fedramp-high/cloud-run/` are
  examples of well-structured blueprints, and `fast/stages-aw/` contains the
  landing zone stages for bootstrapping an organization.

## 4 Assistant guidance

Follow these steps when you generate or modify code in this repository,
especially new blueprints or modules.

1. Apply the core principles and key resources from the previous sections.
2. Check whether an existing module in `modules/` or stage construct in
   `fast/stages-aw/` covers the need before you create any new resource,
   particularly for networking, service accounts and IAM, and common variable
   patterns.
3. Adhere strictly to the naming conventions in `docs/naming-convention.md`.
4. Ask the user to confirm that a new fundamental resource, such as a new base
   VPC or a highly privileged service account, is necessary and why existing
   components do not fit.
5. Read the `README.md` of any module from `modules/` that you use to
   understand its usage, inputs, and outputs.
