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

Keep new code consistent, secure, and easy to maintain by following these
principles when you create or modify Terraform blueprints and modules.

1. Maximize reusability above all else by reusing existing base configurations
   and modules instead of redefining common elements.
   * Inherit from and extend the base variable definitions in the
     `variables.tf` file of each module and blueprint, such as the
     `modules/net-vpc/variables.tf` file, instead of hardcoding values.
   * Reuse the service account definitions and IAM policies in the
     `modules/iam-service-account/` module instead of creating service
     accounts with overlapping permissions.
   * Connect new blueprints to the VPCs, subnets, and firewall rules that the
     `modules/net-vpc/` and `modules/net-vpc-firewall/` modules provide
     rather than creating parallel or redundant network structures.
2. Design blueprints to be modular and composable by breaking complex
   deployments into smaller components that build on the existing modules in
   the `modules/` directory.
3. Include a `README.md` file that explains the purpose, inputs, outputs, and
   dependencies of every module and blueprint that you add or change.
4. Follow the naming conventions in the `docs/naming-convention.md` file so
   that variables, resources, modules, and files stay consistent.
5. Apply GCP security best practices and least privilege in all
   configurations to meet the target regime, such as FedRAMP Moderate,
   FedRAMP High, IL4, or IL5.

## 3 Key resources

Find the code and documentation to reuse in these locations.

* Base variable definitions live in the `variables.tf` file of each module and
  blueprint, such as the `modules/net-vpc/variables.tf` and
  `blueprints/il5/bigquery/variables.tf` files.
* Core service account definitions live in the
  `modules/iam-service-account/` module.
* The `modules/net-vpc/` module provides VPCs and subnets.
* The `modules/net-vpc-firewall/` module provides firewall rules.
* The other `net-` modules in the `modules/` directory provide the remaining
  networking components.
* The naming convention documentation lives in the
  `docs/naming-convention.md` file.
* The `blueprints/il5/bigquery/` blueprint is an example of a well-structured
  IL5 workload blueprint.
* The `blueprints/fedramp-high/cloud-run/` blueprint is an example of a
  well-structured FedRAMP High blueprint.
* The `blueprints/fedramp-high/cloud-run/` blueprint lives in a regular
  directory rather than a symlink because it has no `blueprints/il5/`
  counterpart.
* The `fast/stages-aw/` directory contains the landing zone stages for
  bootstrapping an organization.

## 4 Assistant guidance

Reuse existing components and pass review by following these steps when you
generate or modify code in this repository, especially new blueprints or
modules.

1. Apply the core principles and key resources from the previous sections.
2. Check whether an existing module in the `modules/` directory or stage
   construct in the `fast/stages-aw/` directory covers the need before you
   create any new resource, particularly for networking, service accounts and
   IAM, and common variable patterns.
3. Adhere strictly to the naming conventions in the
   `docs/naming-convention.md` file.
4. Ask the user why existing components do not fit before you create a new
   fundamental resource, such as a new base VPC or a highly privileged service
   account.
5. Read the `README.md` file of any module from the `modules/` directory that
   you use to understand its usage, inputs, and outputs.
