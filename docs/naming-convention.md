# Google Cloud Naming Convention

Google Cloud services and assets enforce strict naming constraints across character limits, casing, hyphens, underscores, and reserved prefixes. Several Google Cloud resources also require globally unique names to avoid cross-tenant collisions or keep deleted project identifiers reserved against immediate reuse.

Use this naming standard across Google Cloud resources, assets, and Terraform configurations to maintain compliance and prevent deployment failures.

Example names throughout this guide use the fictional organization `ACME` (`acme`).

# Table of Contents

<!-- BEGIN TOC -->
- [Table of Contents](#table-of-contents)
- [Google Cloud Org Domain](#google-cloud-org-domain)
- [Prefix](#prefix)
- [Google Cloud Folders](#google-cloud-folders)
- [Google Cloud Projects](#google-cloud-projects)
- [Google Cloud Networks](#google-cloud-networks)
- [Google Cloud Org Policy Custom Constraints](#google-cloud-org-policy-custom-constraints)
- [IAM Custom Roles](#iam-custom-roles)
- [GCS Buckets](#gcs-buckets)
- [GCE](#gce)
- [Terraform labels](#terraform-labels)
<!-- END TOC -->

## Google Cloud Org Domain
`acme.dev`

## Prefix

_acme_ (`ACME`) serves as the example prefix in this guide.

Choose a short `prefix` of 7 characters or fewer (`var.prefix`, enforced by `length(var.prefix) < 8` in `fast/stages-aw/*`) representing the organization or landing zone. Stages and blueprints prepend this `prefix` to globally unique resources such as projects, service accounts, and Cloud Storage buckets so identifiers remain unique without exceeding Google Cloud length limits.

Folder display names in `fast/stages-aw/0-bootstrap` (`StellarEngine-<prefix>`) include the prefix at the Assured Workloads root, while child administrative and tenant folders omit the prefix for readability.

## Google Cloud Folders

Stellar Engine Stage `0-bootstrap` and Stage `1-resman` generate a standardized folder hierarchy inside the Assured Workloads boundary:

- Root Assured Workloads folder: `StellarEngine-<prefix>`
- Common services folder: `<RegimeCode> Common Services` (containing `Networking` and `Security`)
- Environment folders: `<RegimeCode> <Env>` (such as `IL5 Prod` and `IL5 Dev`)
- Tenant folders: `Project <tenant> <env>` (such as `Project ten-1 prod`)

For custom workload subfolders created outside the core FAST stage naming pattern, prefer short descriptive display names (`1` to `30` characters, avoiding reserved control characters):

- Example stage folders: `StellarEngine-acme`, `IL5 Common Services`, `IL5 Prod`, `Project ten-1 prod`
- Example custom subfolder: `fh-logs-common`

[Google Cloud Folders Documentation](https://cloud.google.com/resource-manager/docs/creating-managing-folders#creating-folders)

Google Cloud Folder naming properties:

- Only viewable within the Google Cloud organization
- Not globally unique (unique only within the same parent folder or organization)
- Not permanently consumed on deletion
- Supports letters, digits, spaces, hyphens, and underscores up to 30 characters

## Google Cloud Projects

Stage `fast/stages-aw` core and tenant project IDs follow predictable prefix-based patterns (and blueprints append short suffixes within Google Cloud's 30-character maximum):

Spec:

- Stage projects: `<prefix>-<env>-<role>-<index>` or `<prefix>-net-<role>-host`
- Tenant projects: `<prefix>-<env>-<tenant>-<role>-<index>`
- Workload projects: `<prefix>-<regime>-<env>-<role>-<index>`

Examples:

- Stage 0 core IaC project: `acme-prod-iac-core-0`
- Stage 0 centralized audit logging project: `acme-prod-audit-logs-0`
- Stage 0 billing export project: `acme-prod-billing-exp-0`
- Stage 2 networking host projects: `acme-net-hub-host` (`2-networking-a-fedramp`) or `acme-net-vdss-host` (`2-networking-b-il5-ngfw`), and `acme-prod-net-host`
- Stage 3 security project: `acme-prod-sec-core-0`
- Stage 1 tenant self-service IaC project: `acme-prod-ten-1-iac-core-0`

[Google Cloud Projects Documentation](https://cloud.google.com/resource-manager/docs/creating-managing-projects)

Google Cloud Project ID rules:

- Lowercase letters, digits, and hyphens only (`^[a-z][a-z0-9-]{4,28}[a-z0-9]$`)
- No spaces or uppercase characters
- Globally unique across all Google Cloud customers
- Treat deleted project IDs as permanently consumed once created (unavailable after deletion)
- Must be 6 to 30 characters in length (enforced in `modules/project` preconditions)
- Must start with a lowercase letter and cannot end with a hyphen
- Cannot contain restricted substrings such as `google` or `ssl`

## Google Cloud Networks

VPC Network
  * spec: `{prefix}-{compliance regime}-{environment}-vpc-{region}`
  * example: `acme-il2-prod-vpc-uswest`

Subnet
  * spec: `{prefix}-{compliance regime}-{environment}-subnet-{region}-{app}`
  * example: `acme-il2-prod-subnet-uswest-gke`

Internal Firewall
  * spec: `{prefix}-{compliance regime}-{environment}-fw-{source}-{dest}-{protocal}-{port}-{action}`
  * example: `acme-il2-prod-fw-gke-lb-http-80-allow`

IP Route
  * spec: `{prefix}-{compliance regime}-{environment}-route-{source}-{nexthop}`
  * example `acme-il2-prod-route-gke-niprnet`

[Google Cloud VPCs Documentation](https://cloud.google.com/architecture/best-practices-vpc-design#naming)

Google Cloud Networks naming rules:

- Lowercase letters, digits, and hyphens only (`1` to `63` characters following RFC 1035 label syntax, starting with a lowercase letter and not ending with a hyphen)
- No spaces or uppercase letters
- Visible only inside the Google Cloud organization
- Not globally unique (unique per project for VPCs and per project/region for subnets)
- Not permanently consumed on deletion

## Google Cloud Org Policy Custom Constraints

Spec:

`custom.<camelCaseName>`

Examples from `fast/stages-aw/0-bootstrap/data/custom-constraint-policies/`:

- `custom.kmsRotation`
- `custom.restrictFirewallRanges`

[Google Cloud Organization Policy Custom Constraints Documentation](https://cloud.google.com/resource-manager/docs/organization-policy/creating-managing-custom-constraints#custom_constraints)

Google Cloud Organization Policy Custom Constraints naming rules:

- `custom.` prefix followed by alphanumeric camelCase characters starting with a lowercase letter (`custom.[a-z][a-zA-Z0-9]{0,61}`)
- No hyphens, underscores, or spaces
- Scoped to and viewable only inside the owning Google Cloud organization
- Unique only within the owning organization (not globally unique)
- Not permanently consumed on deletion

## IAM Custom Roles

Spec:

`<camelCaseRoleId>` or `<prefix>_<role>_<rw_ro>` (must match `^[a-zA-Z0-9_.]{3,64}$`; hyphens are not allowed by Google Cloud IAM)

Examples from `fast/stages-aw/0-bootstrap/data/custom-roles/`:

- `organizationAdminViewer`
- `tenantNetworkAdmin`
- `storageViewer`
- `acme_il5_ops_terraform_rw`

[Google Cloud IAM Custom Roles Documentation](https://cloud.google.com/iam/docs/creating-custom-roles#creating)

IAM Custom Role ID rules:

- Letters, digits, underscores, and periods only (`3` to `64` characters)
- No hyphens (`-`) or spaces
- Viewable only inside the owning Google Cloud organization or project
- Not globally unique
- Deleted role IDs remain unavailable for 37 days (7-day undelete grace period plus 30-day permanent deletion delay) before reuse

## GCS Buckets

Spec:

`<prefix>-<env>-<purpose>-<index>`

Examples matching `fast/stages-aw/0-bootstrap/automation.tf` and `fast/stages-aw/1-resman/branch-tenants.tf`:

- `acme-prod-iac-core-bootstrap-0`
- `acme-prod-iac-core-resman-0`
- `acme-prod-iac-core-outputs-0`
- `acme-tn-prod-ten-1-0`
- `acme-prod-ten-1-iac-0`
- `acme-prod-ten-1-iac-outputs-0`

[Google Cloud Storage Documentation](https://cloud.google.com/storage/docs/buckets)

GCS Bucket naming rules:

- Lowercase letters, digits, and hyphens only (`3` to `63` characters; avoid dots and underscores)
- No spaces or uppercase characters
- Stellar Engine enforces `storage.uniformBucketLevelAccess`, `storage.publicAccessPrevention`, and `iam.allowedPolicyMemberDomains`, keeping buckets private within the organization
- Globally unique across all Google Cloud customers
- Not permanently consumed on deletion (names become reusable after bucket deletion completes)

## GCE

Spec:

`<prefix>-<regime>-<env>-<role>-<000-999>`

Example:

`acme-fh-prod-app-001`

[Google Cloud GCE VM Documentation](https://cloud.google.com/compute/docs/naming-resources)

GCE instance naming rules:

- Lowercase letters, digits, and hyphens only (`1` to `63` characters following RFC 1035 syntax, starting with a lowercase letter and not ending with a hyphen)
- No spaces or uppercase characters
- Only viewable inside the owning Google Cloud project and organization
- Not globally unique (unique per project and zone)
- Not permanently consumed on deletion

## Terraform labels

Terraform block labels follow the upstream Cloud Foundation Fabric convention. The `terraform_naming_convention` rule in the `.tflint.hcl` file enforces it, and CI runs it through the `tools/tflint.sh` script.

- Resource, data source, variable and output labels use snake_case, such as `google_compute_firewall.allow_iap`.
- Module labels use kebab-case, such as `module.core-log-metrics`.
- Local value names use snake_case.
- A leading underscore marks a block-private intermediate local, such as `_cl_groups` in the `fast/stages-aw/0-bootstrap/checklist.tf` file.

The convention covers Terraform addresses only. The `name` argument that Google Cloud sees still follows the sections above, so a resource labeled `allow_iap` can create a firewall rule named `allow-iap`.

Labels form state addresses, so renaming a resource or a module changes its address. Add a `moved` block before every renamed resource or module block, so existing deployments move the state instead of destroying and recreating the resource:

```hcl
moved {
  from = google_compute_firewall.allow-iap
  to   = google_compute_firewall.allow_iap
}
```

Renaming a variable or an output changes the interface that callers and tfvars files use, so the pull request needs a Breaking Changes section with an `upgrade-note`.
