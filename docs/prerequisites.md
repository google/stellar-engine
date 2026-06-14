# Stellar Engine Deployment Prerequisites

This checklist centralizes the setup items required before running the Stellar
Engine deployment guide. The detailed deployment flow remains in the
[DDG](ddg.md); use this file as the prerequisite checklist before starting
Stage 0.

## Local Workstation

- Clone the Stellar Engine repository.
- Install the [Google Cloud SDK](https://cloud.google.com/sdk/docs/install).
- Install Terraform version 1.8.1 or newer.
- Install [jq](https://jqlang.github.io/jq/download/).
- Authenticate with Google Cloud:
  - `gcloud auth login`
  - `gcloud config set project <bootstrap_project_id>`
  - `gcloud auth application-default login`

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
Terraform. The repository provides
`fast/stages-aw/0-bootstrap/enableServices.sh` for this step.

The script enables these services:

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

## Initial IAM Grants

Grant the deploying user the organization-level roles required for the initial
bootstrap. The DDG documents the manual console flow, and the repository
provides `fast/stages-aw/0-bootstrap/setIam.sh` plus
`fast/stages-aw/0-bootstrap/setIAM.yaml.sample` for the scripted flow.

The current bootstrap checklist includes:

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

`setIAM.yaml.sample` also grants `roles/resourcemanager.projectDeleter`; review
the generated policy before applying it in production.

## Administrative Groups

Create or confirm the initial Google Cloud administrative groups used by the
deployment:

- `gcp-billing-admins@<domain>`
- `gcp-developers@<domain>`
- `gcp-devops@<domain>`
- `gcp-hybrid-connectivity-admins@<domain>`
- `gcp-logging-monitoring-admins@<domain>`
- `gcp-logging-monitoring-viewers@<domain>`
- `gcp-organization-admins@<domain>`
- `gcp-vpc-network-admins@<domain>`
- `gcp-security-admins@<domain>`

## Organization Features And Quotas

- Enable Access Transparency for the organization.
- Confirm project quota before deployment. The DDG currently calls for a quota
  of at least 13 projects.
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
