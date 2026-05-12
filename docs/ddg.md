# **Stellar Engine**

Cloud Foundation Fabric Detailed Deployment Guide

| <strong>Created:</strong>             | June 04, 2023 |
| :------------------------------------ | :------------ |
| <strong>Updated:</strong>             | May 11, 2026  |
| <strong>Version:</strong>             | v2.9.1        |
| <strong>Most recent changes:</strong> | Refresh to v2.9.1|

##

## Introduction

### Stellar Engine

Stellar Engine is a project aimed at providing Infrastructure as Code (IaC) for
Google Cloud Platform (GCP) customers who need to create a landing zone
environment with the Assured Workload overlays. The project has been confirmed
to work with (DISA) Impact Level 5 (IL5), Impact Level 4 (IL4), and FedRAMP
High, but will function as a starting point for any other Assured Workloads
overlay. In addition to the IaC, there is documentation available for both the
IL5 and FedRAMP High compliance regimes that provide a mapping of National
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
completion of a stage, the Terraform code will write out a **``<stage-name>`-tfvar.auto.tfvars.json`** file to the Google Cloud Storage
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

| <strong>VARIABLE</strong>             | <strong>TFVARS LOCATION</strong> | <strong>DESCRIPTION</strong>                                                                                                                                                                                                                                                                                   |
| :------------------------------------ | :------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| <strong>Billing Account</strong>      | `billing_account.id`             | The billing account to use for the deployment of the environments. <a href='https://console.cloud.google.com/billing'>Console Link</a>                                                                                                                                                                         |
| <strong>Bootstrap Project ID</strong> | `bootstrap_project`              | The bootstrap project id (created below)                                                                                                                                                                                                                                                                       |
| <strong>Compliance Regime</strong>    | `assured_workloads.regime`       | The <a href='https://assuredworkloads.googleapis.com/$discovery/rest?version=v1'>compliance regime</a> for this environment, (confirmed working in IL4, IL5, FEDRAMP_HIGH, and COMPLIANCE_REGIME_UNSPECIFIED)                                                                                                           |
| <strong>Customer ID</strong>          | `organization.customer_id`       | The Google Workspace Directory Customer ID. <br/>Run <strong>gcloud organizations list</strong> to view.                                                                                                                                                                                                       |
| <strong>Domain Name</strong>          | `organization.domain`            | The primary Fully Qualified Domain Name (FQDN). Run <strong>gcloud organizations list</strong> to view (make sure you have authorized as per prerequisites below)                                                                                                                                              |
| <strong>Alert Email</strong>          | `alert_email`                    | The email address used for logging alerts notifications.                                                                                                                                                                                                                                                       |
| <strong>Organization ID</strong>      | `organization.id`                | The Organization ID for the GCP Organization. Run <strong>gcloud organizations list</strong> to view.                                                                                                                                                                                                          |
| <strong>Prefix</strong>               | `prefix`                         | This is the prefix appended to the beginning of projects and resources deployed selected by your or your organization. <strong>Full project names must be globally unique and the prefix must use a maximum of 6 characters</strong>. A 409 error will occur if a globally unique project name is not created. |
| <strong>Region</strong>               | `assured_workloads.location`     | This is the (US) based region that we are deploying resources into (Dual regions like “NAM9” or continents are currently not supported)                                                                                                                                                                        |
| <strong>Tenant Name</strong>          | `tenants` (Stage 1)              | The name for the first tenant that will be deployed via this document. <strong>Full project names must be globally unique and the tenant-name must use a maximum of 6 characters</strong>.                                                                                                                     |

## Prerequisites

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
- Update local [Terraform](https://developer.hashicorp.com/terraform/tutorials/aws-get-started/install-cli) to version >= 1.8.1
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
  - [Enable The Cloud Monitoring
    API](https://console.developers.google.com/apis/api/monitoring.googleapis.com/overview)
    in the bootstrap project
- Edit [Variables](#variables) Section above
- Authenticate and set the active project
  - **gcloud auth login**
  - **gcloud config set project `<bootstrap_project_id>`**
  - **gcloud auth application-default login**
- Navigate to [IAM & Admin](https://console.cloud.google.com/iam-admin/iam) at
  the Organization level **_(not project-specific)_** in the GCP Console and
  assign the following IAM roles for the deploying user. See the note at the
  bottom of this list for a script to automatically assign these permissions.
  - Access Transparency Admin (roles/axt.admin)
  - Assured Workloads Administrator (roles/assuredworkloads.admin)
  - Billing Account Administrator (roles/billing.admin) either on the
    organization or the billing account (see the following section for
    details)
  - Logging Admin (roles/logging.admin)
  - Organization Administrator (roles/resourcemanager.organizationAdmin)
  - Organization Policy Admin (roles/orgpolicy.policyAdmin)
  - Organization Role Administrator (roles/iam.organizationRoleAdmin)
  - Owner (roles/owner)
  - Project Creator (roles/resourcemanager.projectCreator)
  - Service Account Admin (roles/iam.serviceAccountAdmin)
  - Service Account Token Creator (roles/iam.serviceAccountTokenCreator)
  - Tag Admin (roles/resourcemanager.tagAdmin)
    - Note: If you are starting with a brand new organization, the above
      permissions (excluding billing account admin and super admin) can be
      automated by running the following script:
      - **Warning: You will lose all current permissions for your user
        besides Super User**
      - **./setIam.sh \<your-email-address\> `<customer_id>`** from within the fast/stages-aw/0-bootstrap folder

- Navigate to the [Super Admin](https://admin.google.com/ac/roles) roles
  section in Google Workspace to ensure that the deploying user is a Super
  Admin
- Follow the [Initial Groups and Administrative Access in Cloud Setup Steps 2
  and 3](https://console.cloud.google.com/cloud-setup/overview) instructions
  adding all the below groups.
  - If prompted, skip the IDP step for now
- Note: You do not have to complete subsequent steps but make sure you finish
  Step 2. Google may change their default group names. You can manually create
  the [group](https://console.cloud.google.com/iam-admin/groups) if it is not
  contained in the wizard.)
  - gcp-billing-admins@`<domain>`
  - gcp-developers@`<domain>`
  - gcp-devops@`<domain>`
  - gcp-hybrid-connectivity-admins@`<domain>`
  - gcp-logging-monitoring-admins@`<domain>`
  - gcp-logging-monitoring-viewers@`<domain>`
  - gcp-organization-admins@`<domain>`
  - gcp-vpc-network-admins@`<domain>`
  - gcp-security-admins@`<domain>`
- We need to enable these Google Cloud Services by running the following
  script:
    - fast/stages-aw/0-bootstrap/enable_services.sh
      - If you run into issues with the above command, you can simply run the following deprecated command (on MacOS, works on other *nix variants)
        - `echo "iam cloudkms pubsub serviceusage cloudresourcemanager bigquery assuredworkloads cloudbilling logging iamcredentials orgpolicy" | xargs -n1 -I {} gcloud services enable "{}.googleapis.com”`
- [Enable Access
  Transparency](https://console.cloud.google.com/iam-admin/settings) for your
  organization
  - Note: If this is unavailable, make sure you have the Access Transparency
    Admin role and try again
- Request “13 projects” here
  <https://support.google.com/code/contact/billing_quota_increase> if your
  quota is below 13
  - [View and Manage
    Quotas](https://cloud.google.com/docs/quotas/view-manage)

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
  - **cp terraform.tfvars.sample terraform.tfvars**
- Copy file **providers.tf.tmp** to **0-bootstrap-providers.tf**
  - **cp providers.tf.tmp 0-bootstrap-providers.tf**
- Update information in **terraform.tfvars** as follows below, the variables
  from the above sections are already included

**`fast/stages-aw/0-bootstrap/terraform.tfvars`**

```hcl
# use `gcloud beta billing accounts list`
billing_account = {
 id = "`<billing_account_id>`" # taken from Google Cloud Console Billing Accounts -> Manage Billing Account
}
# locations for GCS, BigQuery, and logging buckets created here
locations = {
 bq = "`<region>`"
 gcs = "`<region>`"
 logging = "`<region>`"
 pubsub = "`<region>`"
 kms = "`<region>`"
}
# use `gcloud organizations list`
organization = {
 domain = "`<domain>`" # DISPLAY_NAME
 id = "`<organization_id>`"
 customer_id = "`<organization_id>`"
}
outputs_location = "~/fast-config"
# use something unique and no longer than 6 characters
prefix = "`<prefix>`" # full project names must be globally unique
log_sinks = {
 audit-logs = {
 filter = "logName:\"/logs/cloudaudit.googleapis.com%2Factivity\" OR logName:\"/logs/cloudaudit.googleapis.com%2Fsystem_event\" OR protoPayload.metadata.@type=\"type.googleapis.com/google.cloud.audit.TransparencyLog\""
 type = "pubsub"
 }
 vpc-sc = {
 filter = "protoPayload.metadata.@type=\"type.googleapis.com/google.cloud.audit.VpcServiceControlAuditMetadata\""
 type = "pubsub"
 }
 workspace-audit-logs = {
 filter = "logName:\"/logs/cloudaudit.googleapis.com%2Fdata_access\" and protoPayload.serviceName:\"login.googleapis.com\""
 type = "pubsub"
 }
 empty-audit-logs = {
 filter = ""
 type = "pubsub"
 }
}
org_policies_config = {
  constraints = {
    allowed_policy_member_domains = [] #Update with additional customer IDs if needed
    }
  }
fast_features = {
 envs = true
}
assured_workloads = {
 regime = "`<compliance_regime>`"
 location = "`<region>`"
}
bootstrap_project = "`<bootstrap_project_id>`"
alert_email = "`<alert_email>`"
```

- Run **terraform init**
- Run **terraform apply -var bootstrap_user=$(gcloud config list --format
  'value(core.account)')**
  - Type **yes** when prompted
  - **Note:** You may receive an error in this stage where it reports that
    ‘bigquery.googleapis.com\` is not usable in the Assured Workloads. 
    - If you see this error, go to the [Assured Workloads
    ](https://console.cloud.google.com/compliance/assuredworkload)page
    - Click the  StellarEngine-`<compliance_regime>` folder (and Networking folder, if applicable)
    - Click “Review Available Updates”, 
    - Go to “Allowed Services”
    - Click “Allow services” to bring in the BigQuery family of APIs. 
    - If prompted, say yes to the additional dialog confirming your choice. 
    - After making this change, you should wait \~2 minutes and then re-run:
      - **terraform apply -var bootstrap_user=$(gcloud config list --format
    'value(core.account)')**
  - Type **yes** when prompted
  - **Note:** You may encounter a bug where your bootstrap project loses
    access to your billing account. If so [re-enable billing for your
    bootstrap project](https://console.cloud.google.com/billing/projects)
- Switch project to your new project
  - **gcloud config set project `<prefix>`-prod-iac-core-0**
- Copy the new providers local
  - **gcloud alpha storage cp
    gs://`<prefix>`-prod-iac-core-outputs-0/providers/0-bootstrap-providers.tf
    ./**
- Migrate the state from local to remote using
  - **terraform init --migrate-state**
  - Type **yes** when prompted
- Run ./**import.sh**
- Apply Terraform one more time before moving on to the next stage via
  **terraform apply**
  - Type **yes** when prompted

## Stage 1 - Resource Management

### Description

In this stage, we begin to build out the different folders, projects, and
service accounts that will be used at the organization level for subsequent
stages. In order to build out the environment, you will have to update the
**terraform.tfvars** file in **fast/stages-aw/1-resman** to include a tenants
variable as seen below.

### Steps

- **Note:** If you are using an external billing account, you have to add the
  Billing Account Administrator for the following service account to the external billing account:
  - **`<prefix>`-prod-resman-0@`<prefix>`-prod-iac-core-0.iam.gserviceaccount.com**

  **Steps to add the external billing account (if applicable):**
  - In the Google Cloud console (External billing Account), go to the
    Account management page for the Cloud Billing account, select the
    Organization level and Go to Account management in Cloud Billing
  - At the prompt, choose the Cloud Billing account you want to view.
  - In the Permissions panel, To add new principals and assign permissions,
    do the following:
  - Click Add principal.
  - In the New principals field, enter the email address for the principals
    you want to add for example:
    - `<prefix>`-prod-resman-0@`<prefix>`-prod-iac-core-0.iam.gserviceaccount.com
  - Select a permission for the principal(s) from Select a role as “Billing
    Account Administrator”.
  - When done, click Save.
- Change directory into **fast/stages-aw/1-resman**
- Copy file **terraform.tfvars.sample** to **terraform.tfvars **
  - **cp terraform.tfvars.sample terraform.tfvars**
- Update information in **terraform.tfvars** as follows
  - Note: Change “tenant_name(s)” below

**`fast/stages-aw/1-resman/terraform.tfvars`**

```hcl
tenants = {
`<tenant_name>` = { ## Change tenant_name here - 6 or less characters
  admin_principal = "group:gcp-devops@`<domain>`"
  descriptive_name = `<tenant_name>` ## Change descriptive_name here
  locations = {
    gcs = `<region>`
    kms = `<region>`
    }
 },
 tenant_name-2 = { ## Change tenant_name-2 here - 6 or less characters
  admin_principal = "group:gcp-devops@`<domain>`"
  descriptive_name = "tenant-name-2" ## Change descriptive_name here
  locations = {
    gcs = `<region>`
    kms = `<region>`
    }
 }
## You can have “n” number of tenants
}
fast_features = {
 envs = true
}
envs_folders = {
 Prod = {
  admin = "gcp-organization-admins@`<domain>`"
 },
 Int = {
  admin = "gcp-organization-admins@`<domain>`"
 },
 Test = {
  admin = "gcp-organization-admins@`<domain>`"
 }
}
```

- Copy the tfvars files from GCS
  - **gcloud storage cp
    gs://`<prefix>`-prod-iac-core-outputs-0/providers/1-resman-providers.tf ./**
  - **gcloud storage cp
    gs://`<prefix>`-prod-iac-core-outputs-0/tfvars/0-globals.auto.tfvars.json
    ./**
  - **gcloud storage cp
    gs://`<prefix>`-prod-iac-core-outputs-0/tfvars/0-bootstrap.auto.tfvars.json
    ./**
- Run **terraform init**
- Run **terraform apply**
  - Type **yes** when prompted

## Stage 2 - Network Creation

## FedRAMP High - Stage 2.1 Networking

### Steps

**Note:** If you are using an external billing account, you have to add the
  Billing Account Administrator for the following service account to the external billing account:
  - **`<prefix>`-prod-resman-net-0@`<prefix>`-prod-iac-core-0.iam.gserviceaccount.com**

  **Steps to add the external billing account (if applicable):**
  - In the Google Cloud console (External billing Account), go to the
    Account management page for the Cloud Billing account, select the
    Organization level and Go to Account management in Cloud Billing
  - At the prompt, choose the Cloud Billing account you want to view.
  - In the Permissions panel, To add new principals and assign permissions,
    do the following:
  - Click Add principal.
  - In the New principals field, enter the email address for the principals
    you want to add for example:
    - `<prefix>`-prod-resman-net-0@`<prefix>`-prod-iac-core-0.iam.gserviceaccount.com
  - Select a permission for the principal(s) from Select a role as “Billing
    Account Administrator”.
  - When done, click Save.
- Change directory into **fast/stages-aw/2-networking-a-fedramp-high**
- Copy the **terraform.tfvars.tf** files from the GCS buckets
  - **gcloud storage cp
    gs://`<prefix>`-prod-iac-core-outputs-0/providers/2-networking-providers.tf
    ./**
  - **gcloud storage cp
    gs://`<prefix>`-prod-iac-core-outputs-0/tfvars/0-globals.auto.tfvars.json
    ./**
  - **gcloud storage cp
    gs://`<prefix>`-prod-iac-core-outputs-0/tfvars/0-bootstrap.auto.tfvars.json
    ./**
  - **gcloud storage cp
    gs://`<prefix>`-prod-iac-core-outputs-0/tfvars/1-resman.auto.tfvars.json
    ./**
- Run **terraform init**
- **terraform apply**
  - Type **yes** when prompted

## IL4/IL5 Stage 2.1 - Networking

### Description

This step deploys a pair of Palo Alto vm-series Next-Generation Firewalls
(NGFWs) into the network account. They use the Bring Your Own License (BYOL)
deployment image and will require you to use the Palo Alto web console to upload
a VM code and register them. For more instructions, see the README in the the
**2-networking-b-il5-ngfw **stage folder.

### Steps

**Note:** If you are using an external billing account, you have to add the
  Billing Account Administrator for the following service account to the external billing account:
  - **`<prefix>`-prod-resman-net-0@`<prefix>`-prod-iac-core-0.iam.gserviceaccount.com**

  **Steps to add the external billing account (if applicable):**
  - In the Google Cloud console (External billing Account), go to the
    Account management page for the Cloud Billing account, select the
    Organization level and Go to Account management in Cloud Billing
  - At the prompt, choose the Cloud Billing account you want to view.
  - In the Permissions panel, To add new principals and assign permissions,
    do the following:
  - Click Add principal.
  - In the New principals field, enter the email address for the principals
    you want to add for example:
    - `<prefix>`-prod-resman-net-0@`<prefix>`-prod-iac-core-0.iam.gserviceaccount.com
  - Select a permission for the principal(s) from Select a role as “Billing
    Account Administrator”.
  - When done, click Save.
- Change directory into **fast/stages-aw/2-networking-b-il5-ngfw**
- Copy the **terraform.tfvars.tf** files from the GCS buckets
  - **gcloud storage cp
    gs://`<prefix>`-prod-iac-core-outputs-0/providers/2-networking-providers.tf
    ./**
  - **gcloud storage cp
    gs://`<prefix>`-prod-iac-core-outputs-0/tfvars/0-globals.auto.tfvars.json
    ./**
  - **gcloud storage cp
    gs://`<prefix>`-prod-iac-core-outputs-0/tfvars/0-bootstrap.auto.tfvars.json
    ./**
  - **gcloud storage cp
    gs://`<prefix>`-prod-iac-core-outputs-0/tfvars/1-resman.auto.tfvars.json
    ./**
- Run **terraform init**
- Run **terraform apply -target google_project_iam_custom_role.ngfw-custom-role**
  - Type **yes** when prompted
  - **Note: **If you receive an error relating to a service account and/or
    KMS not existing, please click “Settings” in the `<prefix>`-net-vdss-host
    storage account on the console, and it will generate the service account
    for you

## IL2/FedRAMP Mod Stage 2.1 - Networking

### Steps

**Note:** If you are using an external billing account, you have to add the
  Billing Account Administrator for the following service account to the external billing account:
  - **`<prefix>`-prod-resman-net-0@`<prefix>`-prod-iac-core-0.iam.gserviceaccount.com**

  **Steps to add the external billing account (if applicable):**
  - In the Google Cloud console (External billing Account), go to the
    Account management page for the Cloud Billing account, select the
    Organization level and Go to Account management in Cloud Billing
  - At the prompt, choose the Cloud Billing account you want to view.
  - In the Permissions panel, To add new principals and assign permissions,
    do the following:
  - Click Add principal.
  - In the New principals field, enter the email address for the principals
    you want to add for example:
    - `<prefix>`-prod-resman-net-0@`<prefix>`-prod-iac-core-0.iam.gserviceaccount.com
  - Select a permission for the principal(s) from Select a role as “Billing
    Account Administrator”.
  - When done, click Save.

- Change directory into **fast/stages-aw/2-networking-c-fedramp-mod**
- Copy file terraform.tfvars.sample to terraform.tfvars 
  - `cp terraform.tfvars.sample terraform.tfvars`
- Update information in terraform.tfvars as follows
  - The `ngfw` variable determines whether or not firewall endpoints will be created for your network.
  - Available options for `min_tls_version`: TLS_VERSION_UNSPECIFIED, TLS_1_0, TLS_1_1, TLS_1_2, TLS_1_3.
  - Available options for `tls_feature_profile`: PROFILE_UNSPECIFIED, PROFILE_COMPATIBLE, PROFILE_MODERN, PROFILE_RESTRICTED, PROFILE_CUSTOM.
  - You may also delete the `tls` variable if you wish to have no TLS  inspection policy associated with your firewall endpoints.

**`fast/stages-aw/2-networking-c-fedramp-mod/terraform.tfvars`**
```hcl
ngfw = true
tls = {
  min_tls_version = "TLS_1_2",
  tls_feature_profile = "PROFILE_MODERN"
}
```

- Copy the **terraform.tfvars.tf** files from the GCS buckets
  - **gcloud storage cp
    gs://`<prefix>`-prod-iac-core-outputs-0/providers/2-networking-providers.tf
    ./**
  - **gcloud storage cp
    gs://`<prefix>`-prod-iac-core-outputs-0/tfvars/0-globals.auto.tfvars.json
    ./**
  - **gcloud storage cp
    gs://`<prefix>`-prod-iac-core-outputs-0/tfvars/0-bootstrap.auto.tfvars.json
    ./**
  - **gcloud storage cp
    gs://`<prefix>`-prod-iac-core-outputs-0/tfvars/1-resman.auto.tfvars.json
    ./**
- Run **terraform init**
- Run **terraform apply -target google_project_iam_custom_role.ngfw-custom-role**
  - Type **yes** when prompted
  - **Note: **If you receive an error relating to a service account and/or
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
- `gcp.restrictCmekCryptoKeyProjects`: list CMEK key projects allowed to be used.

In this step, prod-sec-core-0 project is created to host KMS and Secret Manager
(optional) services. A restricted admin role (can grant decrypt permissions to
other services) is granted to the KMS restricted admins. KMS key rings in
different locations are also provisioned. (KMS Key ring locations must match the
service locations, for example, a multi-regional keyring cannot be used in a
single region storage bucket, or vice versa).

TBA: The audit project contains a logging bucket for audit logs.

Security administrators are responsible for the security project, and auditors
are responsible for the audit project.

### Steps

- **Note: If you are using an external billing account, you have to add the
  Billing Account Administrator for the following service account to the external billing account:**
  - `<prefix>`-security-0@`<prefix>`-prod-iac-core-0.iam.gserviceaccount.com
  
  **Steps to add the external billing account:**
  - In the Google Cloud console (External billing Account), go to the
    Account management page for the Cloud Billing account, select the
    Organization level and Go to Account management in Cloud Billing
  - At the prompt, choose the Cloud Billing account you want to view.
  - In the Permissions panel, To add new principals and assign permissions,
    do the following:
  - Click Add principal.
  - In the New principals field, enter the email address for the principals
    you want to add for example:
    - `<prefix>`-security-0@`<prefix>`-prod-iac-core-0.iam.gserviceaccount.com
  - Select a permission for the principal(s) from Select a role as “Billing
    Account Administrator”.
  - When done, click Save.
- Change directory into **fast/stages-aw/3-security**
- Copy the **terraform.tfvars** files from the GCS buckets
  - **gcloud storage cp
    gs://`<prefix>`-prod-iac-core-outputs-0/providers/3-security-providers.tf
    ./**
  - **gcloud storage cp
    gs://`<prefix>`-prod-iac-core-outputs-0/tfvars/0-globals.auto.tfvars.json
    ./**
  - **gcloud storage cp
    gs://`<prefix>`-prod-iac-core-outputs-0/tfvars/0-bootstrap.auto.tfvars.json
    ./**
  - **gcloud storage cp
    gs://`<prefix>`-prod-iac-core-outputs-0/tfvars/1-resman.auto.tfvars.json
    ./**
- Run **terraform init**
- Run **terraform apply**
  - Type **yes** when prompted
  - **Note:** Any issues with Service Accounts can be resolved by rerunning
    **terraform apply**
- Run **./sa_lockdown.sh** to disable the Service Accounts used during the
  deployment
  - **Note:** You may be unable to deploy certain blueprints until the Service Accounts are re-enabled. If you are deploying additional services/blueprints into the Stellar Engine environment, do not run this script until deployments are complete.

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
- `gcloud config set project xxx-prod-iac-core-0`
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
  - fast/stages-aw/2-networking-a-fedramp-high
  - fast/stages-aw/2-networking-b-il5-ngfw
  - fast/stages-aw/2-networking-c-fedramp-mod
- Copy the 1-resman 1-resman tfvars file from the GCS bucket
  - `gcloud storage cp gs://xxx-prod-iac-core-outputs-0/tfvars/1-resman.auto.tfvars.json ./`
- Run terraform init
- Run terraform apply
  - Type yes when prompted

#### Disable FAST Stages Service Accounts
- Change directory into fast/stages-aw/3-security
- `./sa_lockdown.sh`


### Additional Notes

- When modifying modules is necessary, please copy the entire module over, and
  use the naming convention \<module-se\> to avoid merge conflicts when
  periodic updates are pulled in from the CFF
- If you receive KMS key errors during build, you may have to manually turn
  the keys back on in [KMS
  Management](https://console.cloud.google.com/security/kms/keyrings). If you
  receive these additional errors, please wait \~1 minute and rerun
  **terraform apply**
- On a Windows Machine, symlinks may not work, and specific files may need to be copied over manually, specifically psc.tf and log-metric-alerts.tf during the “2-network” stages
- If you run into billing/quota issues, make sure your quota project is set. You can set it by running `gcloud auth application-default set-quota-project xxx-prod-iac-core-0`, or change it to a project of your choice.

####
