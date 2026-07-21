# Shared Services CI/CD

Each shared service runs as an independent child pipeline triggered from `.gitlab-ci.yml`. Services use shared templates from `templates.yml` to reduce boilerplate.

## Templates Reference

Defined in `.gitlab/ci/shared-services/templates.yml`:

| Hidden Job | Purpose | What child jobs override |
|---|---|---|
| `.shared-service-init` | `before_script` preamble: `cd`, WIF auth, tf_dependencies, sets `$GCS_BUCKET` | N/A — referenced via `!reference`, not `extends` |
| `.shared-service-plan` | Sets `stage: plan`, `extends: .terraform_plan_template`, `GCP_SERVICE_ACCOUNT` | `variables` (TF_DIR, SERVICE_NAME), `before_script`, `rules` |
| `.shared-service-apply` | Sets `stage: apply`, `extends: .terraform_apply_template`, `GCP_SERVICE_ACCOUNT`, full `before_script` | `variables` (TF_DIR, SERVICE_NAME), `rules` |

## Adding a New Shared Service

### 1. Create the Terraform module

Add the module under `fast/stages-aw/shared-services/<service>/`. Include a `data/config.yml` if the service needs YAML-based configuration.

### 2. Create the CI pipeline file

Create `.gitlab/ci/shared-services/<service>.yml`. Use an existing service as a starting point (e.g., `ntp.yml` for standard services, `bcap.yml` for simpler ones).

Required structure:

```yaml
stages:
  - plan
  - apply

include:
 - local: '.gitlab/ci/templates/templates.yml'
 - local: '.gitlab/ci/shared-services/templates.yml'
 - local: '.gitlab/ci/templates/tf_dependencies_public.yml'
   rules:
    - if: $GCP_TF_REGISTRY_TYPE == "PUBLIC" || $GCP_TF_REGISTRY_TYPE == null || $GCP_TF_REGISTRY_TYPE == ""
 - local: '.gitlab/ci/templates/tf_dependencies_internal.yml'
   rules:
    - if: $GCP_TF_REGISTRY_TYPE == "PRIVATE_DW"

plan-<service>:
  extends: .shared-service-plan
  variables:
    TF_DIR: "fast/stages-aw/shared-services/<service>"
    SERVICE_NAME: "<service>"
  before_script:
    - !reference [.shared-service-init, before_script]
    # Download tfvars your service needs:
    # - gcloud storage cp ${GCS_BUCKET}/tfvars/1-assured-workload.auto.tfvars.json ./
    # - gcloud storage cp "${GCS_BUCKET}/tfvars/3-networking-shared-services.auto.tfvars.json" ./
    - gcloud storage cp "${GCS_BUCKET}/providers/shared-services-providers.tf" ./
    - yq '.' data/config.yml > <service>-config.auto.tfvars.json
    - |
      cat <<EOF ><service>-global.auto.tfvars
      prefix = "${PREFIX}"
      EOF
    - terraform init -backend-config=prefix=$SERVICE_NAME
  rules:
    - if: '$DEPLOY_STAGES =~ /\b(SERVICES|<UPPER_SERVICE>)\b/'
      when: on_success
    - if: '$PREFIX != null && $PREFIX != "" && ($CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH || $CI_PIPELINE_SOURCE == "merge_request_event")'
      when: on_success

apply-<service>:
  extends: .shared-service-apply
  variables:
    TF_DIR: "fast/stages-aw/shared-services/<service>"
    SERVICE_NAME: "<service>"
  rules:
    - if: '$DEPLOY_STAGES =~ /\b(SERVICES|<UPPER_SERVICE>)\b/'
      when: manual
    - if: '$PREFIX != null && $PREFIX != "" && $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH'
      when: manual
```

Replace `<service>` with the lowercase service name and `<UPPER_SERVICE>` with the uppercase name used in `DEPLOY_STAGES`.

### 3. Add the trigger in `.gitlab-ci.yml`

Add a trigger block under the `deploy-services` stage:

```yaml
pipeline-deploy-<service>:
  stage: deploy-services
  trigger:
    include:
      - local: .gitlab/ci/shared-services/<service>.yml
    forward:
      pipeline_variables: true
    strategy: depend
  rules:
    - if: '$DEPLOY_VALID != "true"'
      when: never
    - if: '$DEPLOY_STAGES && $DEPLOY_STAGES !~ /\b(SERVICES|<UPPER_SERVICE>)\b/'
      when: never
    - if: '$DEPLOY_STAGES && $DEPLOY_STAGES =~ /\b(SERVICES|<UPPER_SERVICE>)\b/'
      when: on_success
    - if: $CI_COMMIT_BRANCH == "main" || $CI_PIPELINE_SOURCE == "merge_request_event"
      changes:
        - fast/stages-aw/3-networking/**/*
        - fast/stages-aw/shared-services/<service>/**/*
      when: on_success
    - when: never
```

### 4. Update the deploy script

Add the service to `automation/shared-services-deploy.sh` following the existing pattern (GCS download, terraform init/plan/apply).

### 5. Triggering

- **Automatic**: pipelines trigger on changes to `fast/stages-aw/shared-services/<service>/**/*` or `fast/stages-aw/3-networking/**/*`
- **Manual**: set the `DEPLOY_STAGES` pipeline variable to include `<UPPER_SERVICE>` (e.g., `NTP`, `DNS,SMTP`) or `SERVICES` to trigger all shared services
