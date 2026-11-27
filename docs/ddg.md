# **Stellar Engine**

Cloud Foundation Fabric Detailed Deployment Guide

| **Created:**             | June 04, 2023 |
| :----------------------- | :------------ |
| **Updated:**             | November 10, 2026 |
| **Version:**             | v6.0.0        |
| **Most recent changes:** | [CHANGELOG.md](../CHANGELOG.md) |

##

## Introduction

### Stellar Engine

Stellar Engine is a project aimed at providing Infrastructure as Code (IaC) for
Google Cloud Platform (GCP) customers who need to create a landing zone
environment with the Assured Workload overlays. The project has been confirmed
to work with (DISA) Impact Level 5 (IL5), Impact Level 4 (IL4), and FedRAMP
High, but will function as a starting point for any other Assured Workloads
overlay. In addition to the IaC, there is documentation available for both the
IL5, FedRAMP High, and FedRAMP Moderate compliance regimes that provide a mapping of National
Institute of Standards and Technology (NIST) 800-53r5 controls to enable
projects that leverage the Stellar Engine codebase to accelerate the speed at
which an Authorization to Operate (ATO) can be attained. These responses are
provided purely as examples, and should be reviewed in depth after the Stellar
Engine deployment process. Many of the controls are handled via IaC, so any
deviations from the outlined systems should be cross-checked with the control
responses.

### Instructions

**_Note: Please make a copy of this deployment guide before filling out the
variable section below._**

After completing the **Variables** section below, you may proceed to each stage
and complete the steps listed in that section. After filling out these
variables, commands will be updated to reflect your specific environment making
it easy to copy and paste.

The deployment process is broken up into stages. During each stage, certain
variables are required to be added to the **`terraform.tfvars`** file. Upon
completion of a stage, the Terraform code will write out a **`<stage-name>.auto.tfvars.json`** file to the Google Cloud Storage
(GCS) bucket created in the initial **0-bootstrap stage**. Subsequent stages
will use the **gcloud** command line interface (CLI) to copy the files into the
new stage folder, as well as a provider file that impersonates a stage-specific
service account.

### Conventions

- Code to be executed in a bash-like environment has the following form:
  - **/bin/my-fun-command.sh –with arguments**

### Deployment Times

Depending on the number of tenants, current deployment of a clean environment
takes approximately 1 hour.

## Variables

To make using this deployment guide easier, the variables described below need to be populated into specific `terraform.tfvars` files in the repository.

**Most of these variables are configured in the Stage 0 Bootstrap `terraform.tfvars` file (a sample can be found at [`fast/stages-aw/0-bootstrap/terraform.tfvars.sample`](../fast/stages-aw/0-bootstrap/terraform.tfvars.sample)), except for the Tenant names, which are configured in Stage 1 (a sample can be found at [`fast/stages-aw/1-resman/terraform.tfvars.sample`](../fast/stages-aw/1-resman/terraform.tfvars.sample)).**

| **VARIABLE**             | **TFVARS LOCATION**          | **DESCRIPTION**                                                                                                                                                                                                                                                                             |
| :----------------------- | :--------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Billing Account**      | `billing_account.id`         | The billing account to use for the deployment of the environments. [Console Link](https://console.cloud.google.com/billing)                                                                                                                                                                 |
| **Bootstrap Project ID** | `bootstrap_project`          | The bootstrap project id (created below)                                                                                                                                                                                                                                                    |
| **Compliance Regime**    | `assured_workloads.regime`   | The [compliance regime](https://assuredworkloads.googleapis.com/$discovery/rest?version=v1) for this environment, (confirmed working in IL4, IL5, FEDRAMP_MODERATE, FEDRAMP_HIGH, and COMPLIANCE_REGIME_UNSPECIFIED)                                                                        |
| **Customer ID**          | `organization.customer_id`   | The Google Workspace Directory Customer ID. Run **gcloud organizations list** to view.                                                                                                                                                                                                      |
| **Domain Name**          | `organization.domain`        | The primary Fully Qualified Domain Name (FQDN). Run **gcloud organizations list** to view (make sure you have authorized as per prerequisites below)                                                                                                                                        |
| **Alert Email**          | `alert_email`                | The email address used for logging alerts notifications.                                                                                                                                                                                                                                    |
| **Organization ID**      | `organization.id`            | The Organization ID for the GCP Organization. Run **gcloud organizations list** to view.                                                                                                                                                                                                    |
| **Prefix**               | `prefix`                     | This is the prefix appended to the beginning of projects and resources deployed selected by your or your organization. **Full project names must be globally unique and the prefix must use a maximum of 7 characters**. A 409 error will occur if a globally unique project name is not created. |
| **Region**               | `assured_workloads.location` | This is the (US) based region that we are deploying resources into (Dual regions like “NAM9” or continents are currently not supported)                                                                                                                                                     |
| **Tenant Name**          | `tenants` (Stage 1)          | The name for the first tenant that will be deployed via this document. **Full project names must be globally unique and the tenant-name must use a maximum of 6 characters**.                                                                                                               |
| **KMS Protection Level** | `kms_protection_level`       | The Cloud KMS protection level for the keys the FAST stages create (`0-bootstrap`, `1-resman`, `2-networking-b-il5-ngfw`, `3-security`). Use `"HSM"` for FedRAMP High and IL5 compliance; `"SOFTWARE"` is permitted for FedRAMP Moderate.                                                      |


## Prerequisites

Before starting Stage 0, review the centralized
[deployment prerequisites checklist](prerequisites.md). It collects the local
tooling, bootstrap project, required APIs, IAM grants, administrative groups,
and quota checks that must be ready before the deployment steps below.

In a testing environment, it is possible that one user may have administrator
roles of all three types of resources. However, in a production environment, it
is more likely that we need to have multiple administrators involved during the
initial setup. **Note: If you have access issues either grant the roles for
yourself on the organization node or have your Administrator grant them for you.
A hard refresh of the cloud console may be required to be able to use the active
permissions.**

### Local Environment Setup:
- Clone [Stellar Engine Github](https://github.com/google/stellar-engine/)
- Install [Google Cloud SDK](https://cloud.google.com/sdk/docs/install)
- Install [Terraform](https://developer.hashicorp.com/terraform/tutorials/aws-get-started/install-cli) at the version that the `required_version` constraints in `modules/*/versions.tf` require
- Install [uv](https://docs.astral.sh/uv/getting-started/installation/) to run the `stellar` command from the `cli/` project
- Install [jq binary](https://jqlang.github.io/jq/download/)

### Google Cloud Setup:
- A Google Cloud Organization
  - If creating a new organization, see [Appendix](#appendices) below
  - Login into admin.google.com at least once
- [Create a bootstrap project manually in Google
  Cloud](https://console.cloud.google.com/projectcreate) if you do not already
  have one
  - Enable billing on the bootstrap project by going to [Account
    Management](https://console.cloud.google.com/billing/manage)
- Edit [Variables](#variables) Section above
- Authenticate and set the active project
  - **gcloud auth login**
  - **gcloud config set project `<bootstrap_project_id>`**
  - **gcloud auth application-default login**

> [!TIP]
> Run [`./fast/stages-aw/0-bootstrap/enableServices.sh`](../fast/stages-aw/0-bootstrap/enableServices.sh)
> from the repository root to enable all 12 prerequisite Stage 0 APIs in the
> active bootstrap project automatically. Alternatively, enable each API listed
> below manually in the console or with the `gcloud services enable` command.

- Enable the following Google Cloud APIs in the bootstrap project.
  - `assuredworkloads.googleapis.com`
  - `bigquery.googleapis.com`
  - `cloudbilling.googleapis.com`
  - `cloudkms.googleapis.com`
  - `cloudresourcemanager.googleapis.com`
  - `iam.googleapis.com`
  - `iamcredentials.googleapis.com`
  - `logging.googleapis.com`
  - `monitoring.googleapis.com` through `gcloud services enable monitoring.googleapis.com` or the [Cloud Monitoring API](https://console.developers.google.com/apis/api/monitoring.googleapis.com/overview) console page
  - `orgpolicy.googleapis.com`
  - `pubsub.googleapis.com`
  - `serviceusage.googleapis.com`

> [!TIP]
> Run [`./fast/stages-aw/0-bootstrap/setIAM.sh`](../fast/stages-aw/0-bootstrap/setIAM.sh)
> `<user_email> <organization_id>` from the repository root, such as
> `./fast/stages-aw/0-bootstrap/setIAM.sh admin@example.com 123456789012`, to
> grant the required organization-level roles from the
> [`setIAM.yaml.sample`](../fast/stages-aw/0-bootstrap/setIAM.yaml.sample)
> template automatically while preserving existing IAM bindings. That template
> also grants the `roles/resourcemanager.projectDeleter` role, so review it
> before applying the policy in production. If your billing account belongs to
> another organization, grant the `roles/billing.admin` role directly on the
> billing account as well. Alternatively, assign each role below manually at the
> organization level in [IAM and Admin](https://console.cloud.google.com/iam-admin/iam).

- Assign the following IAM roles to the deploying user at the organization level
  in [IAM and Admin](https://console.cloud.google.com/iam-admin/iam) rather than
  on an individual project.
  - Access Transparency Admin (roles/axt.admin)
  - Assured Workloads Administrator (roles/assuredworkloads.admin)
  - Billing Account Administrator (roles/billing.admin) on the organization or
    on the billing account
  - Logging Admin (roles/logging.admin)
  - Organization Administrator (roles/resourcemanager.organizationAdmin)
  - Organization Policy Admin (roles/orgpolicy.policyAdmin)
  - Organization Role Administrator (roles/iam.organizationRoleAdmin)
  - Owner (roles/owner)
  - Project Creator (roles/resourcemanager.projectCreator)
  - Service Account Admin (roles/iam.serviceAccountAdmin)
  - Service Account Token Creator (roles/iam.serviceAccountTokenCreator)
  - Tag Admin (roles/resourcemanager.tagAdmin)

- Navigate to the [Super Admin](https://admin.google.com/ac/roles) roles
  section in Google Workspace to ensure that the deploying user is a Super
  Admin
- Add the groups below, as described in Cloud Setup's [Users and
  groups](https://docs.cloud.google.com/docs/enterprise/advanced-production#checklist-section-2)
  task. The FAST stages bind these names (`0-bootstrap/variables.tf` through
  `3-security`). Cloud Setup recommends `gcp-network-admins` for the network
  group, so rename it to `gcp-vpc-network-admins` or override it in the
  `groups` variable of `0-bootstrap`.
  - If prompted, skip the IDP step for now
- Note: You do not have to complete subsequent steps but make sure you finish
  Step 2. Google may change their default group names. You can manually create
  the [group](https://console.cloud.google.com/iam-admin/groups) if it is not
  contained in the wizard.)

  **Required FAST Stage Groups:**
  - `gcp-billing-admins@<domain>`
  - `gcp-devops@<domain>` (`gcp-support` is aliased to `gcp-devops`)
  - `gcp-vpc-network-admins@<domain>`
  - `gcp-organization-admins@<domain>`
  - `gcp-security-admins@<domain>`
- [Enable Access
  Transparency](https://console.cloud.google.com/iam-admin/settings) for your
  organization
  - Note: If this is unavailable, make sure you have the Access Transparency
    Admin role and try again
- Request project quota of at least `10 + 6 * <tenants>` new projects (`22`
  projects for the default 3-environment, 2-tenant deployment) at
  <https://support.google.com/code/contact/billing_quota_increase> if your
  quota is below that threshold
  - [View and Manage
    Quotas](https://cloud.google.com/docs/quotas/view-manage)
- Verify the prerequisites with the `stellar preflight` command and fix every
  failed check before Stage 0, as the [CLI README](../cli/README.md) describes
  - `uv run --project cli stellar preflight --org <organization_id> --billing-account <billing_account_id> --project <bootstrap_project_id> --prefix <prefix> --regime <compliance_regime> --region <region>`

## Stage 0 - Bootstrap

### Description

This is the beginning stage where we align the existing parts of our network
with the Terraform state. It creates the initial IaC bootstrap service accounts
and projects. It is designed to transition from whatever project the user
initially has into a newly created “core” project and migrate the Terraform
state.

### Steps

- Enable [billing](https://console.cloud.google.com/billing/projects) for your
  bootstrap project if it is not enabled
- Change directory into **fast/stages-aw/0-bootstrap**
- Copy file **terraform.tfvars.sample** to **terraform.tfvars**
  - `cp terraform.tfvars.sample terraform.tfvars`
- Copy file **providers.tf.tmp** to **0-bootstrap-providers.tf**
  - `cp providers.tf.tmp 0-bootstrap-providers.tf`
- If your billing account belongs to a different organization, set `is_org_level = false` in `billing_account` (and ensure your deploying user holds `roles/billing.admin` on that billing account).
- If Stage 0 must not manage billing IAM (for example, a shared billing account), set `no_iam = true` in `billing_account` and grant `roles/billing.user` (`Billing Account User`) on the billing account instead of `roles/billing.admin`.
- If deploying into a shared organization without organization-level policy administration permissions, set `deploy_org_resources = { org_policies = false }` in `terraform.tfvars`. Stage 0 attaches non-Assured-Workloads baseline policies to the Assured Workloads folder (`module.root-folder-config[0]`) and skips organization-only custom constraints (`custom.kmsRotation`, `custom.restrictFirewallRanges`), `org_only_policies`, and the 12 Assured Workloads baseline policies.
- Update information in **terraform.tfvars** as follows below, the variables
  from the above sections are already included

**`fast/stages-aw/0-bootstrap/terraform.tfvars`**

```hcl
# use `gcloud beta billing accounts list`
billing_account = {
 id = "`<billing_account_id>`" # taken from Google Cloud Console Billing Accounts -> Manage Billing Account
}
# region configuration - this will automatically populate locations for GCS, BigQuery, KMS, and logging buckets
# Default to us-east4 for IL5/FedRAMP High/Moderate compliance - adjust as needed
regions = {
 primary = "`<region>`"
}
# KMS protection level for CMEK keys. Leave unset to get a regime-aware default:
# SOFTWARE for FEDRAMP_MODERATE, HSM for all other regimes (including FEDRAMP_HIGH and IL5).
# kms_protection_level = "HSM"
# use `gcloud organizations list`
organization = {
 domain = "`<domain>`" # DISPLAY_NAME
 id = "`<organization_id>`"
 customer_id = "`<customer_id>`"
}
outputs_location = "~/fast-config"
# use something unique and no longer than 7 characters
prefix = "`<prefix>`" # full project names must be globally unique
log_sinks = {
 audit-logs = {
 filter = "logName:\"/logs/cloudaudit.googleapis.com%2Factivity\" OR logName:\"/logs/cloudaudit.googleapis.com%2Fsystem_event\" OR protoPayload.metadata.@type=\"type.googleapis.com/google.cloud.audit.TransparencyLog\""
 type = "logging"
 }
 vpc-sc = {
 filter = "protoPayload.metadata.@type=\"type.googleapis.com/google.cloud.audit.VpcServiceControlAuditMetadata\""
 type = "logging"
 }
 workspace-audit-logs = {
 filter = "logName:\"/logs/cloudaudit.googleapis.com%2Fdata_access\" and protoPayload.serviceName:\"login.googleapis.com\""
 type = "logging"
 }
 # CIS Compliance Benchmark 2.2
 empty-audit-logs = {
 filter = ""
 type = "logging"
 }
}
org_policies_config = {
  import_defaults = false # No policies to import as of 27 SEP 2024
  constraints = {
    allowed_policy_member_domains = [] # Update with additional customer IDs if needed
    allowed_vpc_peering_producers = ["under:folders/832634261155"] # Google's Service Networking producer folder. Add other Google producers if needed
  }
}
fast_features = {
 envs = true
}

#regime must be in ALL CAPS
assured_workloads = {
 regime = "`<compliance_regime>`"  #"IL4, IL5, FEDRAMP_HIGH, etc... if you wish to not use assured_workloads, set this value to COMPLIANCE_REGIME_UNSPECIFIED"
 location = "`<region>`" # Uses the same region as other resources for consistency - change to match your regions.primary if different
}
bootstrap_project = "`<bootstrap_project_id>`"
alert_email = "`<alert_email>`"

```

- Export the prefix as an environment variable to simplify subsequent commands:
  - `export FAST_PREFIX=$(sed -n 's/^[[:space:]]*prefix[[:space:]]*=[[:space:]]*"\(.*\)"/\1/p' terraform.tfvars)`
  - **Note:** If you open a new terminal or change directories during the deployment, you can re-run this command from the repository root to restore the variable:
    - `export FAST_PREFIX=$(sed -n 's/^[[:space:]]*prefix[[:space:]]*=[[:space:]]*"\(.*\)"/\1/p' $(git rev-parse --show-toplevel)/fast/stages-aw/0-bootstrap/terraform.tfvars)`
- Run `terraform init`
- Run `terraform apply -var bootstrap_user=$(gcloud config list --format 'value(core.account)')`
  - Type `yes` when prompted
  - **Note:** You may receive a `403` error in this stage:
    `Request is disallowed by organization's constraints/gcp.restrictServiceUsage constraint ... attempting to use service 'bigquery.googleapis.com'`.
    - If you see this error, go to the [Assured Workloads
    ](https://console.cloud.google.com/compliance/assuredworkloads) page
    - Click the `StellarEngine-<prefix>` folder (and Networking folder, if applicable)
    - Click “Review Available Updates”, 
    - Go to “Allowed Services”
    - Click “Allow services” to bring in the BigQuery family of APIs. 
    - If prompted, say yes to the additional dialog confirming your choice. 
    - After making this change, you should wait \~2 minutes and then re-run:
      - `terraform apply -var bootstrap_user=$(gcloud config list --format 'value(core.account)')`
  - Type `yes` when prompted
  - **Note:** You may encounter a bug where your bootstrap project loses
    access to your billing account. If so [re-enable billing for your
    bootstrap project](https://console.cloud.google.com/billing/projects)
- Switch project to your new project
  - `gcloud config set project ${FAST_PREFIX}-prod-iac-core-0`
- Copy the new providers local
  - `gcloud storage cp gs://${FAST_PREFIX}-prod-iac-core-outputs-0/providers/0-bootstrap-providers.tf ./`
- Migrate the state from local to remote using
  - `terraform init --migrate-state`
  - Type `yes` when prompted
- Run `./import.sh <organization_id>` (passing the organization ID avoids failures when your account can view multiple GCP organizations; when `deploy_org_resources.org_policies = false`, `import.sh` detects folder mode and imports folder-level policies into `module.root-folder-config[0]` while skipping org-only constraints)
- Apply Terraform one more time before moving on to the next stage via
  `terraform apply`
  - Type `yes` when prompted

## Stage 1 - Resource Management

### Description

In this stage, we begin to build out the different folders, projects, and
service accounts that will be used at the organization level for subsequent
stages. In order to build out the environment, you will have to update the
**terraform.tfvars** file in **fast/stages-aw/1-resman** to include a tenants
variable as seen below.

### Steps

- **Note:** If you are using an environment variable for the prefix, make sure it is set:
  - `export FAST_PREFIX=$(sed -n 's/^[[:space:]]*prefix[[:space:]]*=[[:space:]]*"\(.*\)"/\1/p' $(git rev-parse --show-toplevel)/fast/stages-aw/0-bootstrap/terraform.tfvars)`
- If you are using an external billing account (`is_org_level = false`), Stage 0 grants `roles/billing.admin` on that billing account when `no_iam = false`. If `no_iam = true` (or if you manage billing IAM externally), grant Billing Account User (`roles/billing.user`) on the external billing account to:
  - `<prefix>-prod-resman-0@<prefix>-prod-iac-core-0.iam.gserviceaccount.com`

- If you are using an external billing account where the resman service account cannot be granted billing permissions,
you can use a **billing override** to run the project creation and billing links under your personal credentials.
To do this, define the `billing_override` variable in your **fast/stages-aw/1-resman/terraform.tfvars**:

  ```hcl
  billing_override = {
    project         = "<your-quota-project-id>"
    billing_project = "<your-quota-project-id>"
  }
  ```

  If you add the external billing account principal in the Google Cloud console instead:
  - Open **Billing** and then **Account management** for the external billing account.
  - Click **Add principal**.
  - Enter `<prefix>-prod-resman-0@<prefix>-prod-iac-core-0.iam.gserviceaccount.com` in the **New principals** field.
  - Select the **Billing Account User** (`roles/billing.user`) role.
  - Click **Save**.
- Change directory into **fast/stages-aw/1-resman**
- Copy file **terraform.tfvars.sample** to **terraform.tfvars**
  - `cp terraform.tfvars.sample terraform.tfvars`
- Update information in **terraform.tfvars** as follows
  - Note: Change “tenant_name(s)” below

**`fast/stages-aw/1-resman/terraform.tfvars`**

```hcl
tenants = {
ten-1 = { ## Change tenant_name here - 6 or less characters
  admin_principal = "group:gcp-devops@<domain>"
  descriptive_name = "tenant-1" ## Change descriptive_name here
  locations = {
    gcs = "<region>"
    kms = "<region>"
    }
  },
 ten-2 = { ## Change tenant_name-2 here - 6 or less characters
  admin_principal = "group:gcp-devops@<domain>"
  descriptive_name = "tenant-2" ## Change descriptive_name here
  locations = {
    gcs = "<region>"
    kms = "<region>"
    }
  }
## You can have “n” number of tenants; update subnets.<env>[*].tenant in Stage 2 terraform.tfvars to match these keys
}
fast_features = {
 envs = true
}
envs_folders = {
 Prod = {
  admin = "gcp-organization-admins@<domain>"
 },
 Int = {
  admin = "gcp-organization-admins@<domain>"
 },
 Test = {
  admin = "gcp-organization-admins@<domain>"
 }
}
```

- Copy the tfvars files from GCS
```
gcloud storage cp gs://${FAST_PREFIX}-prod-iac-core-outputs-0/providers/1-resman-providers.tf ./ &&
gcloud storage cp gs://${FAST_PREFIX}-prod-iac-core-outputs-0/tfvars/0-globals.auto.tfvars.json ./ &&
gcloud storage cp gs://${FAST_PREFIX}-prod-iac-core-outputs-0/tfvars/0-bootstrap.auto.tfvars.json ./
```
- Run `terraform init`
- Run `terraform apply`
  - Type `yes` when prompted

## Stage 2 - Network Creation

## FedRAMP High / Moderate / IL2 - Stage 2.1 Networking

### Steps

- **Note:** If you are using an environment variable for the prefix, make sure it is set:
  - `export FAST_PREFIX=$(sed -n 's/^[[:space:]]*prefix[[:space:]]*=[[:space:]]*"\(.*\)"/\1/p' $(git rev-parse --show-toplevel)/fast/stages-aw/0-bootstrap/terraform.tfvars)`
- If you are using an external billing account (`is_org_level = false` or `no_iam = true`), Stage 1 skips organization-level billing IAM grants. Grant Billing Account User (`roles/billing.user`) on the external billing account to:
  - `<prefix>-prod-resman-net-0@<prefix>-prod-iac-core-0.iam.gserviceaccount.com`

- If you are using an external billing account where the networking service account cannot be granted billing permissions,
you can use a **billing override** to run the project creation and billing links under your personal credentials.
To do this, define the `billing_override` variable in **fast/stages-aw/2-networking-a-fedramp/terraform.tfvars** file

  ```hcl
  billing_override = {
    project         = "<your-quota-project-id>"
    billing_project = "<your-quota-project-id>"
  }
  ```

  If you add the external billing account principal in the Google Cloud console instead:
  - Open **Billing** and then **Account management** for the external billing account.
  - Click **Add principal**.
  - Enter `<prefix>-prod-resman-net-0@<prefix>-prod-iac-core-0.iam.gserviceaccount.com` in the **New principals** field.
  - Select the **Billing Account User** (`roles/billing.user`) role.
  - Click **Save**.
- Change directory into **fast/stages-aw/2-networking-a-fedramp**
- Copy the provider and global tfvars files from the GCS buckets:
```bash
gcloud storage cp gs://${FAST_PREFIX}-prod-iac-core-outputs-0/providers/2-networking-providers.tf ./ && \
gcloud storage cp gs://${FAST_PREFIX}-prod-iac-core-outputs-0/tfvars/0-globals.auto.tfvars.json ./ && \
gcloud storage cp gs://${FAST_PREFIX}-prod-iac-core-outputs-0/tfvars/0-bootstrap.auto.tfvars.json ./ && \
gcloud storage cp gs://${FAST_PREFIX}-prod-iac-core-outputs-0/tfvars/1-resman.auto.tfvars.json ./
```
- Copy the sample `terraform.tfvars` file and configure your network settings:
  - `cp terraform.tfvars.sample terraform.tfvars`
- Update custom subnets, proxy subnets, global network firewall policy rules (`firewall_policy_rules`), named CIDRs (`cidrs`), Private Service Connect settings (`psc_google_apis`), optional Private Services Access ranges (`psa_ranges`) for workloads such as `blueprints/fedramp-high/postgresql` that need them, optional centralized Secure Web Proxy egress (`centralized_egress`), and optional hybrid NCC spokes (`ncc_hubs`) inside **`terraform.tfvars`** (built-in Google APIs DNS response policy rules load automatically from `data/dns-policy-rules.yaml`).
  - Whenever you rename, add, or remove `tenants` keys in Stage 1, update `subnets.<env>[*].tenant` in Stage 2 `terraform.tfvars` to match so `google_compute_subnetwork_iam_member.allow_admin_principals` grants `roles/compute.networkUser` to each tenant's `admin_principal` on its spoke subnet(s) (Stage 2 skips unmapped tenants with a plan warning rather than failing).
- Replace every `<region>` placeholder in **`terraform.tfvars`** with the `regions.primary` value from the Stage 0 **`terraform.tfvars`** file.
- Run `terraform init`
  - `terraform apply`
  - Type `yes` when prompted

## IL4/IL5 Stage 2.1 - Networking

### Description

This step deploys a pair of Palo Alto vm-series Next-Generation Firewalls
(NGFWs) into the network account. They use the Bring Your Own License (BYOL)
deployment image and will require you to use the Palo Alto web console to upload
a VM code and register them. For more instructions, see the README in the the
**2-networking-b-il5-ngfw** stage folder.

### Steps

- **Note:** If you are using an environment variable for the prefix, make sure it is set:
  - `export FAST_PREFIX=$(sed -n 's/^[[:space:]]*prefix[[:space:]]*=[[:space:]]*"\(.*\)"/\1/p' $(git rev-parse --show-toplevel)/fast/stages-aw/0-bootstrap/terraform.tfvars)`
- If you are using an external billing account (`is_org_level = false` or `no_iam = true`), Stage 1 skips organization-level billing IAM grants. Grant Billing Account User (`roles/billing.user`) on the external billing account to:
  - `<prefix>-prod-resman-net-0@<prefix>-prod-iac-core-0.iam.gserviceaccount.com`

- If you are using an external billing account where the networking service account cannot be granted billing permissions,
you can use a **billing override** to run the project creation and billing links under your personal credentials.
To do this, define the `billing_override` variable in **fast/stages-aw/2-networking-b-il5-ngfw/terraform.tfvars** file

  ```hcl
  billing_override = {
    project         = "<your-quota-project-id>"
    billing_project = "<your-quota-project-id>"
  }
  ```

  If you add the external billing account principal in the Google Cloud console instead:
  - Open **Billing** and then **Account management** for the external billing account.
  - Click **Add principal**.
  - Enter `<prefix>-prod-resman-net-0@<prefix>-prod-iac-core-0.iam.gserviceaccount.com` in the **New principals** field.
  - Select the **Billing Account User** (`roles/billing.user`) role.
  - Click **Save**.
- Change directory into **fast/stages-aw/2-networking-b-il5-ngfw**
- Copy the provider and global tfvars files from the GCS buckets:
```bash
gcloud storage cp gs://${FAST_PREFIX}-prod-iac-core-outputs-0/providers/2-networking-providers.tf ./ && \
gcloud storage cp gs://${FAST_PREFIX}-prod-iac-core-outputs-0/tfvars/0-globals.auto.tfvars.json ./ && \
gcloud storage cp gs://${FAST_PREFIX}-prod-iac-core-outputs-0/tfvars/0-bootstrap.auto.tfvars.json ./ && \
gcloud storage cp gs://${FAST_PREFIX}-prod-iac-core-outputs-0/tfvars/1-resman.auto.tfvars.json ./
```
- Copy the sample `terraform.tfvars` file and configure your network settings:
  - `cp terraform.tfvars.sample terraform.tfvars`
- Update custom subnets (including mgmt), proxy subnets, firewall rules, named CIDRs, and DNS response policy rules directly inside **`terraform.tfvars`**.
  - Whenever you rename, add, or remove `tenants` keys in Stage 1, update `subnets.<env>[*].tenant` in Stage 2 `terraform.tfvars` to match so `google_compute_subnetwork_iam_member.allow_admin_principals` grants `roles/compute.networkUser` to each tenant's `admin_principal` on its spoke subnet(s) (Stage 2 skips unmapped tenants with a plan warning rather than failing).
- Replace every `<region>` placeholder in **`terraform.tfvars`** with the `regions.primary` value from the Stage 0 **`terraform.tfvars`** file.
- Run `terraform init`
- Run `terraform apply`
  - Type `yes` when prompted
  - **Note:** If you receive an error relating to a service account and/or
    KMS not existing, please click “Settings” in the `<prefix>`-net-vdss-host
    storage account on the console, and it will generate the service account
    for you    

## Stage 3 - Security and Audit Account Configuration

### Description

This stage configures the security and audit projects. The security project
contains KMS services that support the CMEK requirements, it can also host
Secret Manager service. In IL5, CMEK is enabled by default for compute,
container, storage, and SQL server, the following organization policies related
to CMEK are enforced:

- `gcp.restrictNonCmekServices`:
  - `denied_values: "compute.googleapis.com"`
  - `denied_values: "container.googleapis.com"`
  - `denied_values: "storage.googleapis.com"`
  - `denied_values: "sqladmin.googleapis.com"`
- `gcp.restrictCmekCryptoKeyProjects` (commented out by default in `fast/stages-aw/0-bootstrap/data/org-policies/cloudkms_policy.yaml`): uncomment and list allowed CMEK key projects if you want to restrict which projects may host CMEK keys.

In this step, `<prefix>-prod-sec-core-0` and `<prefix>-dev-sec-core-0` projects are created to host centralized Cloud KMS keyrings and keys, optional Secret Manager secrets, and CIS log metric alerts and monitoring policies. A restricted admin role (can grant decrypt permissions to
other services) is granted to the KMS restricted admins. KMS key rings in
different locations are also provisioned. (KMS Key ring locations must match the
service locations, for example, a multi-regional keyring cannot be used in a
single region storage bucket, or vice versa).

Organization audit logging and the `<prefix>-prod-audit-logs-0` project are provisioned in Stage 0 (`0-bootstrap`). By default, Stage 0 routes organization audit logs to CMEK-encrypted Cloud Logging buckets within `<prefix>-prod-audit-logs-0` (`type = "logging"`), while Stage 3 adds CIS log metric alerts and monitoring policies on top of those audit logs.

#### Audit Log Retention
- The default retention for Cloud Logging buckets created in Stage 0 (`0-bootstrap`) is 365 days (1 year) to comply with regulatory standards (such as NIST 800-53 AU-9 requirements).
- To use a different retention period, configure the `logging_bucket_retention` variable in Stage 0. For long-term archival or external analytics, change the Stage 0 log sink routing type to `storage` (for GCS buckets) or `bigquery` (for BigQuery datasets).

#### Transitioning to Pub/Sub Routing (SIEM Integration)
To stream logs to an external SIEM or analytical platform, you can configure your log sinks to route to Pub/Sub (`type = "pubsub"`).
- **Important Retention Risk:** If you change the log sink type to `pubsub` without a connector or subscriber pipeline actively consuming and storing the messages, **logs will be lost** once they pass their short Pub/Sub retention period (default 7 days).
- **Configuration:** Ensure a consumer is configured and active for the Pub/Sub topics before switching the sink type to `pubsub`.

Security administrators are responsible for the security project, and auditors
are responsible for the audit project.

### Steps

- **Note:** If you are using an environment variable for the prefix, make sure it is set:
  - `export FAST_PREFIX=$(sed -n 's/^[[:space:]]*prefix[[:space:]]*=[[:space:]]*"\(.*\)"/\1/p' $(git rev-parse --show-toplevel)/fast/stages-aw/0-bootstrap/terraform.tfvars)`
- If you are using an external billing account (`is_org_level = false` or `no_iam = true`), Stage 1 skips organization-level billing IAM grants. Grant Billing Account User (`roles/billing.user`) on the external billing account to:
  - `<prefix>-security-0@<prefix>-prod-iac-core-0.iam.gserviceaccount.com`

- If you are using an external billing account where the security service account cannot be granted billing permissions,
you can use a **billing override** to run the project creation and billing links under your personal credentials.
To do this, define the `billing_override` variable in **fast/stages-aw/3-security/terraform.tfvars** file

  ```hcl
  billing_override = {
    project         = "<your-quota-project-id>"
    billing_project = "<your-quota-project-id>"
  }
  ```

  If you add the external billing account principal in the Google Cloud console instead:
  - Open **Billing** and then **Account management** for the external billing account.
  - Click **Add principal**.
  - Enter `<prefix>-security-0@<prefix>-prod-iac-core-0.iam.gserviceaccount.com` in the **New principals** field.
  - Select the **Billing Account User** (`roles/billing.user`) role.
  - Click **Save**.
- Change directory into **fast/stages-aw/3-security**
- Copy the **terraform.tfvars** files from the GCS buckets
```
gcloud storage cp gs://${FAST_PREFIX}-prod-iac-core-outputs-0/providers/3-security-providers.tf ./ &&
gcloud storage cp gs://${FAST_PREFIX}-prod-iac-core-outputs-0/tfvars/0-globals.auto.tfvars.json ./ &&
gcloud storage cp gs://${FAST_PREFIX}-prod-iac-core-outputs-0/tfvars/0-bootstrap.auto.tfvars.json ./ &&
gcloud storage cp gs://${FAST_PREFIX}-prod-iac-core-outputs-0/tfvars/1-resman.auto.tfvars.json ./
```
- Copy the sample `terraform.tfvars` file and configure centralized KMS keys:
  - `cp terraform.tfvars.sample terraform.tfvars`
  - Review `kms_keys` (including `locations`, matching your `regions.primary` and workload regions). Note that Stage 3 creates **no** KMS keyrings or keys if `kms_keys` is omitted or `{}` (`terraform.tfvars` is absent or empty), and leaving `version_template` commented out in `terraform.tfvars.sample` inherits `kms_protection_level` from Stage 0.
- Run `terraform init`
- Run `terraform apply`
  - Type `yes` when prompted
  - **Note:** Any issues with Service Accounts can be resolved by rerunning
    `terraform apply`
- Run `./sa_lockdown.sh` to disable the Stage 0 through Stage 3 automation service accounts used during deployment (apply accounts, read-only `-r` plan accounts, branch accounts, team accounts, and core tenant accounts)
  - You may be unable to deploy certain blueprints until the service accounts are re-enabled. If you are deploying additional services or blueprints into the Stellar Engine environment, do not run this script until deployments are complete.
- Run `./validation.sh --prefix "${FAST_PREFIX}"` to confirm that all Stage 0, Stage 1, Stage 2, and Stage 3 automation service accounts (including apply, read-only `-r` plan, branch, team, and core tenant accounts) are disabled
- Optionally delete the temporary initial bootstrap project after validation succeeds (do not delete `<prefix>-prod-iac-core-0`):
  - `./delete_gcp_project.sh --project-id=<bootstrap-project-id>`
  - Generated Stage 0 through Stage 3 `*-providers.tf` files use `<prefix>-prod-iac-core-0` as the Terraform billing and quota project, so deleting the temporary bootstrap project does not affect Day-2 runs.

**Congratulations, you have successfully deployed Stellar Engine\! For further
securing of the environment, please see the** [**Stellar Engine Security Best
Practices
Guide**](security-best-practices.md).

## Appendices

### Creating a new Google Cloud Org

1.  Create Basic Cloud Identity Account
    - <https://workspace.google.com/gcpidentity/signup?sku=identitybasic>
        - You must first log into the Google Admin console, and then cloud
            console, and wait approximately 2 minutes to provision the org
2.  Complete Domain Name verification
    -  This depends on your DNS provider
3.  Enable the account in GCP
    -  <https://console.cloud.google.com/>

### Billing Accounts

1.  Create a billing account
    - <https://console.cloud.google.com/billing/>

### Modifying Tenant Projects

Perform the following steps when adding or removing tenants projects for an existing Stellar Engine deployment.

#### Authenticate and Set Active Project
- `gcloud auth login `
- `gcloud config set project ${FAST_PREFIX}-prod-iac-core-0`
- `gcloud auth application-default login `

#### Enable FAST Stages Service Accounts
- Change directory into fast/stages-aw/3-security
- `./sa_lockdown.sh --enable`

#### Apply FAST Stage: 01-resman
- Change directory into fast/stages-aw/1-resman
- Update information in terraform.tfvars to your new requirements
- Run terraform init
- Run terraform apply
  - Type yes when prompted

#### Apply FAST Stage: 02-networking
- Change directory into appropriate network folder for your Stellar Engine deployment:
  - fast/stages-aw/2-networking-a-fedramp
  - fast/stages-aw/2-networking-b-il5-ngfw
- Copy the `1-resman` tfvars file from the GCS bucket:
  - `gcloud storage cp gs://${FAST_PREFIX}-prod-iac-core-outputs-0/tfvars/1-resman.auto.tfvars.json ./`
- Update `subnets.<env>[*].tenant` (and add or remove spoke subnets as needed) in Stage 2 `terraform.tfvars` so `tenant` matches the Stage 1 `tenants` keys and `allow_admin_principals` grants `roles/compute.networkUser` to each tenant's `admin_principal` on its spoke subnet(s)
- Run terraform init
- Run terraform apply
  - Type yes when prompted

#### Disable FAST Stages Service Accounts
- Change directory into fast/stages-aw/3-security
- `./sa_lockdown.sh`


### Cross-Stage IAM Impersonation and Troubleshooting 403 Errors

Each FAST deployment stage uses a dedicated least-privilege automation service account configured in its generated `*-providers.tf` file:

| Stage | Expected Service Account Pattern | Primary Scope |
| :--- | :--- | :--- |
| `0-bootstrap` | `${FAST_PREFIX}-prod-bootstrap-0@${FAST_PREFIX}-prod-iac-core-0.iam.gserviceaccount.com` | Organization IAM, Assured Workloads, Stage 0 projects |
| `1-resman` | `${FAST_PREFIX}-prod-resman-0@${FAST_PREFIX}-prod-iac-core-0.iam.gserviceaccount.com` | Stage folders, automation service accounts, CI/CD repositories |
| `2-networking` | `${FAST_PREFIX}-prod-resman-net-0@${FAST_PREFIX}-prod-iac-core-0.iam.gserviceaccount.com` | Shared VPCs, firewall policies, interconnect/VPN, DNS |
| `3-security` | `${FAST_PREFIX}-security-0@${FAST_PREFIX}-prod-iac-core-0.iam.gserviceaccount.com` | KMS keys, VPC Service Controls, security projects |

If you encounter `403 Forbidden` or `Permission 'iam.serviceAccounts.getAccessToken' denied` errors when transitioning between stages:

1. Clear any stale shell impersonation variables. If `GOOGLE_IMPERSONATE_SERVICE_ACCOUNT` or `CLOUDSDK_AUTH_IMPERSONATE_SERVICE_ACCOUNT` was exported while debugging a previous stage, it overrides the provider block in the current stage. Run `../../stage-links.sh <OUTPUTS_PATH>` (or `unset GOOGLE_IMPERSONATE_SERVICE_ACCOUNT CLOUDSDK_AUTH_IMPERSONATE_SERVICE_ACCOUNT`) so Terraform uses the stage's `*-providers.tf` configuration.
2. Verify that `./sa_lockdown.sh --enable` has been executed in `fast/stages-aw/3-security` if the deployment service accounts were previously disabled.
3. Confirm that your active `gcloud auth list` identity is a member of the organization admins or devops group granted `roles/iam.serviceAccountTokenCreator` on the target stage service account.

### Additional Notes

- When modifying synced `modules/` directories is necessary, prefer upstream-first fixes where possible, maintain local changes in-place across three-way merges via `tools/sync-from-cff.sh`, and record them in the [Upstream Sync Guide](upstream-sync.md) (instead of creating duplicate `modules/<module>-se` copies).
- If you receive KMS key errors during build, you may have to manually turn
  the keys back on in [KMS
  Management](https://console.cloud.google.com/security/kms/keyrings). If you
  receive these additional errors, please wait \~1 minute and rerun
  `terraform apply`
- On Windows, ensure Git symlinks are enabled (`git config core.symlinks true`) when working with shared blueprint symlinks under `blueprints/fedramp-high/` targeting `blueprints/il5/`.
- If you run into billing/quota issues, make sure your quota project is set. You can set it by running `gcloud auth application-default set-quota-project ${FAST_PREFIX}-prod-iac-core-0`, or change it to a project of your choice.

####
