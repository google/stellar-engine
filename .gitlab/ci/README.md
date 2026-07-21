# Terraform Landing Zone Automation Pipeline

## Overview
This repository contains the Continuous Deployment (CD) pipeline for our Terraform-based Landing Zone (LZ). The pipeline is designed to automate infrastructure provisioning, executing `terraform plan` and `terraform apply` whenever code is merged into the `main` branch. 

To maintain security, separation of duties, and modularity, the pipeline is divided into distinct stages and utilizes dynamic child pipelines to manage multi-tenant infrastructure efficiently.

---

## Architecture & Design

### Authentication
All authentication from the GitLab instance to Google Cloud is handled securely through **Workload Identity Federation (WIF)**. 
* GitLab authenticates via an OpenID Connect (OIDC) provider configured in Google Cloud.
* The WIF pool ID and prefix are passed as GitLab CI/CD variables to authorize the runner.
* This setup allows the pipeline to impersonate specific service accounts for each stage, ensuring strict separation of duties and least-privilege access.

### Pipeline Jobs & Stages
The pipeline is highly modular. Core infrastructural changes go through standard stages. 

| Job Name | Description |
| :--- | :--- |
| `compliance` | Runs immediately after the Stage 1 plan. Cross-checks the plan against allowed YAML configurations to ensure no services outside the compliance catalog (or compliance COA decisions) are utilized. |
| `<Stage_number>-plan` | Runs for Stages 0-4. Previews infrastructure changes on Merge Requests and `main`. Downloads tools, tfvars, and providers. Saves the plan as a GitLab artifact. |
| `<Stage_number>-apply` | Executes **only** on the `main` branch. Uses the saved plan artifact from the previous step to provision approved changes. |

### Execution Flow & Dependencies
Because of the modular design, the pipeline intelligently determines which stages need to run based on the files changed:

* **Changes in Stage 0:** Runs only Stage 0.
* **Changes in Stage 1:** Runs Stage 1, 2, 3, 4, and 5.
* **Changes in Stage 2:** Runs Stage 2, 3, 4, and 5.
* **Changes in Stage 3:** Runs Stage 3 and 5.
* **Changes in Stage 4:** Runs Stage only stage 4.
* **Changes in stage 5 or `tenants.yml`:** Runs only Stage 5.

*(Note: The pipeline automatically triggers the **Plan** stage, but will pause and wait for a **manual trigger** before executing the **Apply** stage).*

---

## Setup & Integration Guide

The following steps guide you through bootstrapping a new environment so that the automated CI/CD pipeline can take over subsequent deployments.

> **Best Practices**
> * Keep variable names exactly the same as documented.
> * Maintain the exact format for variable values.

### 1. Local Configuration

Authenticate your local `gcloud` environment:
```bash
gcloud auth login
gcloud auth application-default login
```

Create and set up your `config.env` file (use `config.env.sample` for reference). Be sure to include the Workload Identity Federation variables:
```env
# Workload Identity Federation via GitLab
CI_PROJECT_PATH=google-cloud/army-example-lz
# If deployment is for prod this should be main or the equivelent protected branch
CI_COMMIT_BRANCH=<Branch name you are testing on>
GITLAB_URL=[https://dev.darkwolf.io](https://dev.darkwolf.io)
```

Update the `tenants.yml` file located in the root directory to reflect the initial tenants you are deploying via `automation/tenant.sh`.

### 2. Initial Bootstrap (Stages 0 & 1)

To allow the CI/CD pipeline to assume control, you must manually deploy Stages 0 and 1 locally first. This establishes the Workload Identity Federation and impersonation service accounts.

**Run `./stellar-engine-deploy.sh`**
1. Go through all of stage 0
2. Run the through the first and second apply for stage one and update providers and migrate state, stop at the third apply without the bootstrap user.

🎉 **Success:** Workload Identity Federation should now be active. You can verify this by checking the `-il5-prod-iac` project in your GCP Console under **IAM > Workload Identity Federation**.

---

## GitLab Configuration

Now that WIF is set up in Google Cloud, you need to configure the connection variables in GitLab.

1. **Gather your WIF Provider Variable:**
   Run the following command from the `1-assured-workload` directory to extract the exact WIF path:
   ```bash
   cd fast/stages-aw/1-assured-workload
   terraform output -json workload_identity_pool | jq -r '.providers."gitlab-fed".audiences[1] | sub("[https://iam.googleapis.com/](https://iam.googleapis.com/)"; "")'
   ```
   *The output will look similar to: `projects/<project-ID>/locations/global/workloadIdentityPools/<WIF-pool-name>`*

2. **Set GitLab Variables:**
   * Navigate to **Settings > CI/CD** in your GitLab repository and expand the **Variables** section.
   * Edit the `PREFIX` variable and replace the value with your deployment's prefix.
   * Edit the `GCP_WORKLOAD_IDENTITY_PROVIDER` variable and paste the filepath outputted from the `jq` command above.
   * Click **Save Changes**.

---

## Usage

### Running the Pipeline
* Commits pushed to `fast/stages-aw` will trigger the pipeline automatically based on the dependency rules outlined in the Architecture section.
* To view a plan, click on the **logs** for the specific plan stage in the GitLab UI.
* To apply changes, click the **Play** button on the manual apply stage. 
