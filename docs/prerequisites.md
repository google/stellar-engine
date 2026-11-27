# Stellar Engine Deployment Prerequisites

This checklist centralizes the setup items required before running the Stellar
Engine deployment guide. The detailed deployment flow remains in the
[DDG](ddg.md); use this file as the prerequisite checklist before starting
Stage 0.

Run the `stellar preflight` command to verify most of this checklist
automatically. The [CLI README](../cli/README.md) lists its flags and every
check it performs.

## Local Workstation

- Use a POSIX-compliant shell environment: Linux, macOS, Google Cloud Shell, or WSL2 (Windows Subsystem for Linux) on Windows workstations.
  - Native Windows terminals (PowerShell, `cmd.exe`, Git Bash/`MINGW64`, or Cygwin) are not supported because stage linking (`fast/stage-links.sh`) and automation scripts (`scripts/*.sh`) rely on POSIX path resolution, `ln -s` symbolic links, and standard Unix utilities. Clone the repository and run all commands inside a WSL2 Linux filesystem (for example, `~/stellar-engine`) rather than a mounted Windows drive (`/mnt/c/...`) to avoid CRLF line-ending and symlink permission issues.
- Clone the Stellar Engine repository.
- Install the [Google Cloud SDK](https://cloud.google.com/sdk/docs/install).
- Install the Terraform version that the `required_version` constraints in
  the `modules/*/versions.tf` files require.
- Install [uv](https://docs.astral.sh/uv/getting-started/installation/) to
  run the `stellar` command from the `cli/` project.
- Install [jq](https://jqlang.github.io/jq/download/).
- Authenticate with Google Cloud:
  - `gcloud auth login`
  - `gcloud config set project <bootstrap_project_id>`
  - `gcloud auth application-default login`
- Verify the checklist with the following `stellar preflight` command, and
  fix every failed check before Stage 0.

  ```bash
  uv run --project cli stellar preflight --org <organization_id> \
    --billing-account <billing_account_id> --project <bootstrap_project_id> \
    --prefix <prefix> --regime <compliance_regime> --region <region>
  ```

## Google Cloud Organization

- Have a Google Cloud Organization available.
- If this is a new organization, sign in to `admin.google.com` at least once.
- Complete domain verification for the organization.
- Capture the organization values needed by
  `fast/stages-aw/0-bootstrap/terraform.tfvars`:
  - `organization.domain`
  - `organization.id`
  - `organization.customer_id`
- Ensure the deploying user is a Google Workspace Super Admin when required for
  the initial setup.

## Bootstrap Project

- Create a bootstrap Google Cloud project if one does not already exist.
- Enable billing on the bootstrap project.
- Set the active gcloud project to the bootstrap project before Stage 0.
- Capture the bootstrap variables used by
  `fast/stages-aw/0-bootstrap/terraform.tfvars`:
  - `billing_account.id`
  - `bootstrap_project`
  - `regions.primary`
  - `prefix`
  - `alert_email`
  - `assured_workloads.regime`
  - `assured_workloads.location`

## Required APIs

Enable the Stage 0 prerequisite APIs in the bootstrap project before running
Terraform.

> [!TIP]
> Run [`./fast/stages-aw/0-bootstrap/enableServices.sh`](../fast/stages-aw/0-bootstrap/enableServices.sh)
> from the repository root after setting the active `gcloud` project to enable
> all 12 prerequisite Stage 0 APIs automatically. Alternatively, enable each
> service listed below manually in the console or with the
> `gcloud services enable` command.

The `enableServices.sh` script enables these services:

- `iam.googleapis.com`
- `cloudkms.googleapis.com`
- `pubsub.googleapis.com`
- `serviceusage.googleapis.com`
- `cloudresourcemanager.googleapis.com`
- `bigquery.googleapis.com`
- `assuredworkloads.googleapis.com`
- `cloudbilling.googleapis.com`
- `logging.googleapis.com`
- `iamcredentials.googleapis.com`
- `orgpolicy.googleapis.com`
- `monitoring.googleapis.com`

## Initial IAM Grants

Grant the deploying user the organization-level roles required for the initial
bootstrap.

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
> billing account as well. Alternatively, grant each role below manually at the
> organization level.

The bootstrap checklist includes these roles:

- `roles/axt.admin`
- `roles/assuredworkloads.admin`
- `roles/billing.admin`
- `roles/logging.admin`
- `roles/resourcemanager.organizationAdmin`
- `roles/orgpolicy.policyAdmin`
- `roles/iam.organizationRoleAdmin`
- `roles/owner`
- `roles/resourcemanager.projectCreator`
- `roles/iam.serviceAccountAdmin`
- `roles/iam.serviceAccountTokenCreator`
- `roles/resourcemanager.tagAdmin`

A shared billing account whose IAM you cannot change still works with Stage 0.

- Set `no_iam = true` in the Stage 0 `billing_account` variable, so Stage 0
  skips every billing IAM binding.
- Grant `roles/billing.user` on the billing account instead of
  `roles/billing.admin`, because Stage 0 then only links new projects to it.
- Pass the `--billing-no-iam` flag to `stellar preflight` to test that
  permission.

## Administrative Groups

Create or confirm the required Stage 0 Google Cloud administrative groups
(`0-bootstrap/variables.tf`; `gcp-support` aliases to `gcp-devops` by default):

- `gcp-billing-admins@<domain>`
- `gcp-devops@<domain>`
- `gcp-organization-admins@<domain>`
- `gcp-vpc-network-admins@<domain>`
- `gcp-security-admins@<domain>`

## Organization Features And Quotas

- Enable Access Transparency for the organization.
- Confirm project quota before deployment. Budget at least
  `10 + 6 * <tenants>` new projects (`22` projects for the default
  3-environment, 2-tenant deployment).
- If an Assured Workloads deployment blocks `bigquery.googleapis.com`, review
  the available services in the Assured Workloads folder, allow the BigQuery
  family of APIs, wait for propagation, and rerun the failed Terraform step.

## Stage 0 Configuration Files

Before running Stage 0:

- Copy `fast/stages-aw/0-bootstrap/terraform.tfvars.sample` to
  `fast/stages-aw/0-bootstrap/terraform.tfvars`.
- Copy `fast/stages-aw/0-bootstrap/providers.tf.tmp` to
  `fast/stages-aw/0-bootstrap/0-bootstrap-providers.tf`.
- Fill in the values listed in this checklist and in the DDG Variables table.
- Export `FAST_PREFIX` from the Stage 0 `terraform.tfvars` if you want to reuse
  the DDG copy-and-paste commands.

## Related References

- [Detailed Deployment Guide](ddg.md)
- [Stage 0 bootstrap sample tfvars](../fast/stages-aw/0-bootstrap/terraform.tfvars.sample)
- [Stage 0 generated IAM reference](../fast/stages-aw/0-bootstrap/IAM.md)
- [FAST architecture notes](../fast/docs/README.md)
