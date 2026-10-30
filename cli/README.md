# Stellar Engine CLI

The `stellar` command turns the
[Detailed Deployment Guide](../docs/ddg.md) into a validated deployment. It
checks the prerequisites, records the answers of each deployment, renders
Terraform workspaces for the `0-bootstrap` and `1-resman` stages, and runs
the DDG steps of those stages with reviewed plans that a rerun resumes.

## 1 Install the CLI

The `cli/` project uses [uv](https://docs.astral.sh/uv/) to install the
Python version and the dependencies that `cli/pyproject.toml` declares, so you
do not install Python yourself.

- Install uv by following the
  [uv installation guide](https://docs.astral.sh/uv/getting-started/installation/).
- Run the command from the repository root with
  `uv run --project cli stellar --help`.
- Install the command on your `PATH` with `uv tool install ./cli` if you
  prefer to run `stellar` directly.
- The examples below call `stellar` directly, so prefix them with
  `uv run --project cli` when you skip the install.

## 2 Deploy Stage 0

The `stellar deploy` command runs the DDG steps of the prerequisites, Stage 0,
and Stage 1 in order, and each rerun resumes where the last run stopped. Run
the steps in this order.

### 2.1 Sign in

Terraform and preflight use your Application Default Credentials, and
preflight checks that the active gcloud account matches them.

```bash
gcloud auth login
gcloud auth application-default login
```

- Sign in as the user that holds the roles in the DDG prerequisites section.
- Terraform can also run as a service account that holds those roles.
- Point the `GOOGLE_APPLICATION_CREDENTIALS` variable at the credentials of
  that service account, and activate the same account in gcloud.
- Keep that gcloud session apart from your own by setting the
  `CLOUDSDK_CONFIG` variable to a dedicated folder.
- Stage 0 still grants a human user on the first apply, so name that user
  with the `bootstrap_user` answer or the `--bootstrap-user` flag.

### 2.2 Prepare the inputs

These commands write only to the home folder and never change Google Cloud.

```bash
export STELLAR_HOME=~/deployments/lab
stellar init
stellar preflight
stellar guide
```

- The `stellar init` command asks for the answers and saves them, as
  section 4 describes.
- The `stellar preflight` command checks the prerequisites against those
  answers, as section 6 describes.
- The `stellar guide` command explains each deploy step with the manual
  commands that do the same, without reading Google Cloud.
- Rerun preflight until it reports no failure that applies to your
  organization.

### 2.3 Apply Stage 0

The `stellar deploy` command prepares, plans, reviews, and applies Stage 0,
so you never run Terraform by hand.

```bash
stellar deploy --stage pre
stellar deploy --stage 0
stellar status
```

- The `--stage pre` run enables the bootstrap project APIs, grants the
  deployer the organization roles, and records the existing organization
  policies.
- The same run stops at a failed preflight check and asks you to confirm
  the prerequisites that no API shows.
- The `--stage 0` run renders the workspace, applies the Assured Workloads
  workload with a targeted plan, and allows BigQuery on the workload
  folder.
- The run then applies Stage 0 in the bootstrap phase, swaps in the remote
  providers file, and moves the state into the bootstrap bucket.
- The run finally sets the `stage0_phase` answer to `final` and runs the
  final apply, which imports the organization policies that the
  `pre.org_policies` step recorded.
- Each apply saves the plan under the `plans/` folder, prints the summary
  and the plan findings, and applies only that saved plan.
- Each apply that changes organization IAM waits for your review first, as
  section 11 describes.
- The deploy stops with exit status 4 when a step waits for you, such as a
  manual confirmation or a pre-created workload, and the next run resumes
  there.
- The `stellar status` command shows how far the deployment got and
  changes nothing.
- Section 13 lists the manual Terraform commands as a fallback.

### 2.4 Continue with Stage 1

The `stellar deploy --stage 1` command copies the Stage 0 outputs, renders
the Stage 1 workspace, and applies Stage 1.

```bash
stellar deploy --stage 1
```

- The `s1.outputs` step reads the Stage 0 outputs from the outputs bucket
  when the `fast-config/` folder of the environment lacks them, such as on
  another machine.
- The `s1.billing_grant` step grants the Stage 1 service account the
  `roles/billing.user` role on the billing account when the
  `billing.external_grant` answer asks for it.
- The `s1.precreate_tenants` step lists the tenant projects that an
  administrator creates when Stage 0 manages no billing IAM.
- A step that needs another identity, such as a billing administrator,
  stops with a handoff card that lists the commands for that person.
- Stages 2 and 3 still follow the DDG.

## 3 Choose a home

One home folder holds every file that a deployment owns, so you move or back
up a deployment by moving one folder.

- The `--home` flag selects the home for one command.
- The `STELLAR_HOME` environment variable selects the home when you omit the
  `--home` flag, for example `STELLAR_HOME=~/deployments/lab`.
- Without either setting, the command uses the `.stellar/` folder in the
  engine checkout, which the root `.gitignore` file excludes.
- Every command resolves the home the same way, and `stellar env show`
  prints the home and the setting that selected it.
- A home can live outside the checkout, because workspaces link to the
  engine code with absolute paths.
- One checkout can serve many homes, such as one home per organization.

Each environment lives in the `envs/<prefix>/` folder of the home.

- The `answers.yaml` file records the answers and keeps your comments
  across reruns.
- Only your user can read the `answers.yaml` file, because it names
  principals and billing accounts.
- The `fast/stages-aw/<stage>/` folders hold the stage workspaces.
- The `fast-config/` folder receives the provider and tfvars files that
  Stage 0 writes for later stages.
- The `generated/` folder stores a hash of each tfvars file that
  `stellar render` wrote, so the next render detects manual edits.
- The `.gitignore` file of the home lets Git track only the answers files,
  so you can turn the home into a private Git repository without committing
  state, logs, or plans.

## 4 Create an environment

The `stellar init` command validates every answer against the repository
before it saves the `answers.yaml` file, so mistakes surface before
Terraform runs.

```bash
stellar init
```

- The wizard offers the organizations and billing accounts that your
  credentials can see as defaults.
- The `--offline` flag skips those Google Cloud lookups.
- A rerun keeps the current answers as defaults, so you press Enter to keep
  each one.
- The `--section` flag asks only the named wizard section, such as
  `--section tenants`, and accepts repeats.
- The `--set KEY=VALUE` flag sets one answer and accepts repeats.
- Each `--set` value is YAML, so lists and maps work.
- The `--non-interactive` flag never prompts and exits with status 2 when an
  answer is missing or invalid.
- The `--from-config-env scripts/config.env` flag starts a new environment
  from an existing `scripts/deploy.sh` configuration file.
- A rerun never changes the prefix of an environment, so use the
  `--answers-from` flag to start a new environment from it.

```bash
stellar init --non-interactive --prefix abc \
  --set organization.id=123456789012 \
  --set organization.domain=example.com \
  --set organization.customer_id=C01234567 \
  --set billing.account_id=000000-AAAAAA-BBBBBB \
  --set bootstrap_project=my-bootstrap-project \
  --set region=us-east4 \
  --set compliance.regime=IL5 \
  --set alert_email=alerts@example.com \
  --set bootstrap_user=admin@example.com \
  --set 'resman.tenants.ten1={descriptive_name: tenant-1}'
```

### 4.1 Wizard sections

The wizard asks the sections in this order, and the `--section` flag accepts
each name.

| Section | Answers it sets |
| --- | --- |
| `prefix` | The resource prefix of every Stage 0 and Stage 1 name. |
| `organization` | The organization ID, domain, and directory customer ID. |
| `billing` | The billing account and how Stage 0 manages its IAM. |
| `bootstrap` | The bootstrap project, any pre-created Stage 0 projects, and whether a destroy keeps them. |
| `compliance` | The Assured Workloads regime. |
| `region` | The region from the regions that the regime supports, and the Assured Workloads location. |
| `kms` | The KMS protection level, which the answers keep only when it differs from the regime default. |
| `contacts` | The alert email, essential contacts, and bootstrap user. |
| `groups` | New names for the Stage 0 administrative groups. |
| `envs` | The Stage 1 environment folders and their admins. |
| `tenants` | The Stage 1 tenants, with each derived project ID and its remaining characters. |

- The wizard never asks for the log sink type, the log retention, the
  budget, the domain restricted sharing list, the billing override, the
  tenant locations, or the Stage 0 phase.
- Set those values with the `--set` flag or edit the `answers.yaml` file.

### 4.2 Answers file

The `answers.yaml` file starts with a `yaml-language-server` comment that
points at the `answers.schema.json` file of the home, so editors that read
that comment complete and check each key.

```yaml
# yaml-language-server: $schema=../../answers.schema.json
prefix: abc
organization:
  id: "123456789012"
  domain: example.com
  customer_id: C01234567
billing:
  account_id: 000000-AAAAAA-BBBBBB
  # The deployer cannot administer a shared billing account.
  no_iam: true
bootstrap_project: my-bootstrap-project
bootstrap_user: admin@example.com
region: us-east4
compliance:
  regime: IL5
alert_email: alerts@example.com
org_policies:
  allowed_policy_member_domains:
    - C0AAAAAAA
resman:
  tenants:
    ten1:
      descriptive_name: tenant-1
overrides:
  0-bootstrap:
    # Keep an existing grant on a role that Stage 0 manages.
    iam:
      roles/resourcemanager.projectCreator:
        - domain:example.com
```

- The command leaves out the values that it derives, such as the KMS
  protection level and the Assured Workloads location, so a regime change
  recomputes them.
- The `overrides` answer passes raw tfvars values per stage for variables
  that the answers do not model, such as the Stage 0 `iam` map.
- The command rejects an override of a variable that the stage does not
  declare or that the Stage 0 outputs provide.
- The command also rejects an override of a value that the CLI derives,
  such as the `prefix`, `outputs_location`, or `bootstrap_user` variable.
- Rerun `stellar init --non-interactive` after you edit the file, so the
  command validates the change before the next render.

### 4.3 Copy an environment

A new environment can start from the answers of another one, so most
prompts only need Enter.

- The `--answers-from` flag copies every answer from another environment
  prefix or an `answers.yaml` path, including the `overrides` answer.
- The copy never includes the prefix, the engine path, the imports, the
  existing organization policies, or the Stage 0 phase, because those
  belong to the source environment.
- The command lists the answers to review when the regime changes, such as
  an explicit `kms_protection_level` value.
- The `--new-prefix` flag suggests a fresh prefix with a random suffix, so
  the new project IDs avoid the IDs of a recently deleted deployment.

## 5 Manage environments

Each prefix in a home is one environment, and every command that omits the
`--prefix` flag works on the current environment.

- The `stellar env list` command shows each environment with its regime,
  region, and organization, and marks the current one.
- The `stellar env use PREFIX` command makes another environment current.
- The `stellar env show` command prints the home, the answers file, the
  workspaces, and the values that the CLI derives, such as the KMS
  protection level and the project IDs.
- The `stellar env show` command also lists the organization policies that
  Stage 0 imports and the deletion policy of each Stage 0 project.
- The `STELLAR_PREFIX` environment variable selects an environment the same
  way as the `--prefix` flag.
- The `render`, `env show`, and `imports scan` commands stop when the
  current environment no longer exists and point you to the
  `stellar env use PREFIX` command.
- Those commands and preflight also stop when the `prefix` answer differs
  from the name of the environment folder.

## 6 Run preflight

Preflight only reads from Google Cloud and never changes a resource, so you
can run it as often as you like.

```bash
stellar preflight
```

- Preflight reads its inputs from the answers of the current environment,
  or of the environment that the `--prefix` flag selects.
- Explicit flags override the answers.
- Each input flag such as `--org` also reads an environment variable such
  as `STELLAR_ORG_ID`.
- Without an environment, pass the inputs as flags instead.
- The `--config-env scripts/config.env` flag fills only the values that the
  flags and the answers leave unset.
- The `--group gcp-devops=platform-ops` flag checks a renamed Stage 0 group
  and accepts repeats.
- A check whose inputs you omit reports the `skip` status and names the
  flag that enables it.
- The `--json` flag prints machine-readable results for automation.
- The command exits with status 1 when a check fails, and the `--strict` flag
  also fails the run on warnings.

```bash
stellar preflight \
  --org 123456789012 \
  --billing-account 000000-AAAAAA-BBBBBB \
  --project my-bootstrap-project \
  --prefix abc \
  --regime IL5 \
  --region us-east4
```

### 6.1 Read the results

Each check reports one status, and most failures and warnings include a fix
and a link to the matching documentation.

| Status | Meaning |
| --- | --- |
| `pass` | Preflight verified the prerequisite. |
| `warn` | Review a risk that does not block Stage 0. |
| `fail` | Fix a missing prerequisite that blocks Stage 0. |
| `manual` | Confirm the prerequisite yourself. |
| `skip` | Pass the inputs that the check needs. |

### 6.2 Checks performed

Preflight catches each missing prerequisite before Stage 0 runs, in the
order of the DDG prerequisites section.

- Terraform meets the highest `required_version` floor that the modules under
  `modules/` declare.
- The workstation has the Google Cloud SDK and jq.
- The active gcloud account matches the Application Default Credentials
  identity that Terraform uses.
- A user account is available for the `bootstrap_user` variable, because
  Stage 0 grants it as a `user:` principal.
- The signed-in user serves as that account by default.
- The `--bootstrap-user` flag names another user when Terraform runs as a
  service account.
- The active gcloud project is the bootstrap project.
- The organization exists, and its domain and directory customer ID match the
  values you pass.
- The deploying identity holds every role that
  `fast/stages-aw/0-bootstrap/setIAM.yaml.sample` grants.
- The role check tests effective permissions with the
  `testIamPermissions` method, so it accepts direct, group, and inherited
  grants alike.
- The billing account is open, the deploying identity holds Billing Account
  Administrator on it, and the bootstrap project bills to it.
- The `--billing-no-iam` flag matches a Stage 0 `billing_account` input with
  `no_iam = true`, so Stage 0 never manages billing IAM.
- With that flag, preflight skips the Billing Account Administrator check
  and tests only the `billing.resourceAssociations.create` permission that
  links new projects to the billing account.
- The `billing.precreate` check lists each Stage 0 resource that needs
  billing access at creation, when the deploying identity lacks that access.
- These resources are the Stage 0 projects and the Assured Workloads
  workload, because the Assured Workloads API creates a workload only for a
  caller that can use the billing account.
- That check passes once the `imports.0-bootstrap` answer adopts every
  listed resource.
- The billing account, project linking, and Billing Account Administrator
  failures then become warnings.
- That check still fails when Stage 0 grants roles on the billing account
  itself or creates a budget from the `budget.amount` answer, because no
  pre-created resource replaces that access.
- That check also fails while the Stage 0 code leaves an input-only
  workload argument out of `lifecycle.ignore_changes`, because the import
  would then plan a replacement of the workload.
- That check also lists the Stage 1 tenant project IDs, because Stage 1
  links them to the billing account too.
- Stages 2 and 3 link their networking and security projects to the billing
  account as well, so the check points to the `billing_override` answer.
- A run without `answers.yaml` has no import blocks, so it lists every
  resource as missing.
- The bootstrap project is active and has every API that
  `fast/stages-aw/0-bootstrap/enableServices.sh` enables, plus the Cloud
  Monitoring API that the DDG requires.
- The Stage 0 administrative groups exist in Cloud Identity, and preflight
  resolves them from the `groups` variable the same way Stage 0 does.
- The region supports the compliance regime according to the
  [Assured Workloads locations](https://cloud.google.com/assured-workloads/docs/locations)
  page, and the regime appears in the Stage 0 `regime_mapping` variable.
- The prefix is valid, and no project, state bucket, or Assured Workloads
  folder that Stage 0 creates already exists with that prefix.
- An existing Assured Workloads folder passes the folder check when the
  `imports.0-bootstrap` answer adopts the workload that owns the folder.
- No soft-deleted project still holds a project ID that Stage 0 creates,
  because a deleted project keeps its ID for 30 days.
- The naming checks skip the billing export project unless the
  `billing.no_iam` answer is false and the `billing.is_org_level` answer is
  true, because Stage 0 creates it only then.
- The Stage 1 tenant project IDs from the answers are free and no
  soft-deleted project holds them.
- Organization-wide custom roles, custom constraints, and log sinks that
  Stage 0 creates do not exist yet.
- The `existing_org_policies` answer lists every existing organization
  policy that Stage 0 declares, so the final Stage 0 apply imports it.
- The organization IAM policy lists every existing grant that the first
  Stage 0 apply removes.
- For each role that `organization-iam.tf` manages authoritatively,
  preflight compares the current members with the members that Stage 0
  keeps on that role.
- Super Admin status, Access Transparency, and project quota appear as manual
  confirmations because no API exposes them to the deploying identity.

### 6.3 Required access

Preflight needs read access to the resources it checks, which the DDG roles
already include.

- Your Application Default Credentials need a quota project with the Cloud
  Resource Manager, IAM, Cloud Billing, Service Usage, Cloud Identity, Cloud
  Logging, and Organization Policy APIs enabled.
- A disabled API reports the exact `gcloud services enable` command to run.
- Terraform can run as a service account, because Stage 0 only needs a user
  account for the `bootstrap_user` variable.
- Pass that user's email with the `--bootstrap-user` flag, and set the same
  value as the `bootstrap_user` answer, which the render writes for the
  first Stage 0 apply.
- The `--redeploy` flag downgrades existing prefix resources to warnings when
  you rerun preflight against your own earlier deployment.
- The deploying identity needs Billing Account Administrator on the billing
  account, or Billing Account User when the `billing.no_iam` answer is true.
- Without that access, someone who has it pre-creates the resources that the
  `billing.precreate` check lists, and Stage 0 imports them.

## 7 Render the workspaces

The `stellar render` command turns the answers into one Terraform workspace
per stage, so Terraform runs with the `-chdir` option and never edits the
engine checkout. After it writes the files, the command points at the
`stellar deploy` run of the first stage it rendered.

```text
Next: stellar deploy --stage 0
stellar deploy runs the first apply in the bootstrap phase, moves the state to the bootstrap bucket, switches stage0_phase to final and runs the final apply. stellar guide --stage 0 lists the manual commands.
```

- The sample shows the bootstrap phase, which is the default. In the
  final phase the render prints only the first line.
- The `stellar deploy` command renders each stage itself, so a separate
  render is optional.
- Each workspace links the stage files of the engine and keeps the files
  that the environment owns, such as `terraform.tfvars` and the local state.
- The Stage 0 workspace receives a copy of the `providers.tf.tmp` file as
  `0-bootstrap-providers.tf`, as the DDG instructs.
- Later renders keep the `0-bootstrap-providers.tf` file, because the state
  migration step replaces it with the remote providers file.
- The `1-resman` workspace links the Stage 0 outputs from the `fast-config/`
  folder once Stage 0 writes them.
- The `--stage` flag renders one stage, such as `--stage 0`, and accepts
  repeats.
- The `--diff` flag prints the changes and writes nothing.
- The tfvars file never sets the `bootstrap_user` variable, because the
  `stage0_phase` answer decides whether Stage 0 runs with it.

### 7.1 Stage 0 phase

The `stage0_phase` answer picks the mode of the next Stage 0 apply, so a
plain `terraform apply` never runs in the wrong one.

- The `bootstrap` phase is the default, and the render writes the
  `0-bootstrap-phase.auto.tfvars` file with the `bootstrap_user` variable.
- Terraform reads that file on every run, so the first apply grants the
  bootstrap user and skips the organization policies without a `-var`
  option.
- The `bootstrap` phase requires the `bootstrap_user` answer, and the
  `stellar init` command reports a missing one.
- After the state migration, the `s0.phase_final` deploy step sets the
  answer to `final` and renders again, which removes the file, so the final
  apply manages the organization policies.
- By hand, the `stellar init --set stage0_phase=final` command and a render
  remove the file as well.
- The `stellar env show` command prints the phase.
- The render never replaces or removes a phase file that it did not write,
  and stops instead.
- The render warns when the `bootstrap` phase meets a workspace whose state
  already moved to the remote backend, because the next apply is then the
  final one.
- The `--answers-from` flag never copies the phase, so a new environment
  always starts in the `bootstrap` phase.
- Keep a deployed Stage 0 in the `final` phase, because a return to
  `bootstrap` plans to delete the organization policies that Stage 0
  manages.
- The `stellar init` command refuses that return once run-state records a
  final Stage 0 apply.
- A final-phase Stage 0 plan that changes nothing records that apply too,
  because it shows that the final phase already holds.

### 7.2 Manual edits

A render owns each tfvars file it writes, so put lasting changes in the
`answers.yaml` file instead of the tfvars file.

- A rerun replaces a tfvars file silently only when the file still matches
  the last render.
- The command asks before it replaces a tfvars file that holds manual edits,
  and exits with status 3 when it cannot ask.
- The `--force` flag replaces an edited file after it saves a
  `terraform.tfvars.backup.<timestamp>` copy.

## 8 Adopt existing resources

Terraform import blocks adopt Stage 0 projects and the Assured Workloads
workload that an administrator creates in advance, so a deployer without
billing access can still apply Stage 0.

```yaml
imports:
  0-bootstrap:
    module.automation-project.google_project.project[0]: abc-prod-iac-core-0
    module.log-export-project.google_project.project[0]: abc-prod-audit-logs-0
```

### 8.1 Import the projects

The bootstrap section of the wizard asks whether the Stage 0 projects exist
already and reads their addresses from the stage code.

- The `stellar render` command writes one `import` block per entry to the
  `0-bootstrap-imports.tf` file in the workspace.
- The command removes that file when the `imports` map and the
  `existing_org_policies` answer are both empty.
- Each Stage 0 import ID must equal the project ID that the prefix
  derives, because a different ID makes Terraform replace the imported
  project.
- The `module.billing-export-project[0]` address exists only when
  `billing.no_iam` is false and `billing.is_org_level` is true, so the
  command warns about an import into it otherwise.
- Preflight expects each project in the `imports` map to exist and be
  active, and reports it as a pass instead of a name collision.
- The `--set` flag accepts an address in double quotes, such as
  `--set 'imports.0-bootstrap."module.automation-project.google_project.project[0]"=abc-prod-iac-core-0'`.

### 8.2 Keep projects on destroy

The `keep_imported_projects` answer defaults to true, so a Stage 0 destroy
keeps the pre-created projects once the Stage 0 code declares the
`project_deletion_policies` variable.

- The wizard asks whether to keep these projects right after you confirm
  that the Stage 0 projects exist already.
- The `stellar render` command writes an `ABANDON` value to the
  `project_deletion_policies` variable for each imported project.
- The command sets this variable only when the Stage 0 code declares it.
- Until the Stage 0 code declares that variable, the command warns that a
  Stage 0 destroy deletes the imported projects.
- Once the Stage 0 code declares the variable, the CLI rejects a
  `project_deletion_policies` key in the `overrides.0-bootstrap` answer,
  because the `keep_imported_projects` answer controls it.
- You cannot set a `PREVENT` policy on a Stage 0 project through the
  `overrides` answer for that reason.
- The `--answers-from` flag carries the `keep_imported_projects` answer,
  because it records a preference rather than the state of an organization.

### 8.3 Pre-create the workload

The Assured Workloads API creates a workload only for a caller that can use
the billing account, so a deployer without billing access needs an
administrator to create the workload first.

```yaml
imports:
  0-bootstrap:
    google_assured_workloads_workload.primary[0]: organizations/123456789012/locations/us-east4/workloads/abc123
```

- The `billing.precreate` preflight check names the workload, its regime,
  and its location.
- Create the workload with the billing account, because the API requires
  one.
- Enable violation notifications on the workload, because the
  `organization.tf` file sets them.
- The API never returns the `resource_settings` argument, so the import
  plans a replacement unless the workload `lifecycle.ignore_changes` list
  in the `organization.tf` file names that argument.
- The `billing.precreate` check fails until the Stage 0 code ignores that
  argument.
- Review the Stage 0 plan before you apply it, and confirm that it imports
  the workload without a replacement.
- Give the workload and its consumer folder the display name that the
  check names.
- Add the workload name that the Assured Workloads API returns to the
  `imports.0-bootstrap` answer.
- The `s0.ready` deploy step prints this request when the deployer lacks
  billing access, and records the workload name that you enter.
- The import ID must name the organization from the `organization.id`
  answer and the location from the `compliance.location` answer, which
  defaults to the region.
- The `stellar init` and `stellar render` commands reject any other import
  ID, because Terraform would replace the imported workload.
- The `stellar render` command warns about a workload import when the
  `compliance.regime` answer is `COMPLIANCE_REGIME_UNSPECIFIED`, because
  Stage 0 creates no workload then.

## 9 Import organization policies

The `stellar imports scan` command records the organization policies that
exist before Stage 0, so the final Stage 0 apply adopts them instead of
failing to create them, and you no longer run the `import.sh` script. The
`pre.org_policies` deploy step runs the same scan.

```bash
stellar imports scan
stellar render --stage 0
```

### 9.1 Scan the organization

The scan only reads from Google Cloud and saves its result to the
`existing_org_policies` answer.

- The command keeps each constraint that a `*_policy.yaml` file declares in
  the `data/org-policies/` or `data/custom-org-policies/` folder of Stage 0.
- The command skips a constraint that the templates in the
  `data/custom-org-policies/` folder omit for the regime of the
  environment.
- The command skips the policies of the `custom.*` constraints that Stage 0
  declares, because Stage 0 creates those constraints in the same apply.
- The command also skips every other constraint, including custom
  constraints of the organization, because Stage 0 does not manage them.
- The command keeps the comments in the `answers.yaml` file when it saves.
- Rerun the scan before the final apply when someone changes the
  organization policies in the meantime.

### 9.2 Import timing

The `stellar render` command adds one `import` block for these policies to
the `0-bootstrap-imports.tf` file, and Stage 0 decides when it applies.

- The first Stage 0 apply runs in the `bootstrap` phase with the
  `bootstrap_user` variable, so Stage 0 manages no organization policies
  yet and imports none.
- The final Stage 0 apply runs in the `final` phase without the
  `bootstrap_user` variable and imports each listed policy that the regime
  templates still set.
- Terraform skips an import once the state holds the policy, so later
  applies keep working with the same file.

### 9.3 Related checks

Preflight and validation keep the scan result and the Stage 0 options
consistent.

- Preflight warns when a policy that Stage 0 declares exists but the
  `existing_org_policies` answer does not list it.
- Preflight only counts the existing policies when it runs without an
  `answers.yaml` file or with the `--redeploy` flag.
- The CLI rejects an `import_defaults` value of true in the
  `overrides.0-bootstrap.org_policies_config` answer while the
  `existing_org_policies` answer lists policies, because that option
  imports a fixed list of policies whether or not each one exists.
- The scan also finds the policies that the `import_defaults` option
  imports, so you can drop that option.

## 10 Run the deploy

The `stellar deploy` command walks an ordered catalog of steps, and each step
checks first whether it is done, so a rerun skips finished work and resumes
at the first open step.

```bash
stellar guide --stage 0
stellar deploy --stage 0
stellar status
```

### 10.1 Step catalog

Each step has an ID that run-state, the `--only` flag, and the `--from-step`
flag use.

| Step | Kind | What it does |
| --- | --- | --- |
| `pre.apis` | auto | Enables the bootstrap project APIs that the `enableServices.sh` script enables. |
| `pre.iam_roles` | auto | Grants the deployer the organization roles that preflight finds missing. |
| `pre.org_policies` | auto | Records the existing organization policies, as `stellar imports scan` does. |
| `pre.preflight` | check | Stops at a failed preflight check. |
| `pre.super_admin` | manual | Asks you to confirm the Super Admin role of the deployer. |
| `pre.access_transparency` | manual | Asks you to confirm Access Transparency. |
| `pre.project_quota` | manual | Asks you to confirm the project quota. |
| `s0.render` | auto | Renders the Stage 0 workspace. |
| `s0.ready` | auto | Checks the render warnings, the Terraform environment, and the workload billing access, and records a pre-created workload. |
| `s0.apply_workload` | auto | Applies the Assured Workloads workload, or the folder of a deployment without a regime, with a targeted plan. |
| `s0.allow_bq` | auto | Allows the BigQuery services on the workload folder through the Assured Workloads API. |
| `s0.apply_bootstrap` | auto | Runs the first Stage 0 apply in the bootstrap phase. |
| `s0.remote_providers` | auto | Copies the remote providers file into the workspace after a backup. |
| `s0.quota_project` | check | Checks the quota project of user credentials. |
| `s0.migrate_state` | auto | Moves the Stage 0 state into the bootstrap bucket. |
| `s0.phase_final` | auto | Sets the `stage0_phase` answer to `final` and renders again. |
| `s0.apply_final` | auto | Runs the final Stage 0 apply. |
| `s0.verify` | check | Checks the Stage 1 inputs and the remote Stage 0 state. |
| `s1.outputs` | auto | Copies the Stage 0 outputs from the outputs bucket. |
| `s1.render` | auto | Renders the Stage 1 workspace. |
| `s1.billing_grant` | manual | Grants the Stage 1 service account billing access. |
| `s1.precreate_tenants` | manual | Lists the tenant projects to pre-create and import. |
| `s1.apply` | auto | Applies Stage 1. |
| `s1.verify` | check | Checks the inputs of Stages 2 and 3. |

- An `auto` step runs on its own.
- A `manual` step waits for your confirmation.
- A `check` step only reports.
- The `stellar guide` command prints when each conditional step applies,
  such as the `s0.allow_bq` step, which applies only when the regime creates
  a workload.
- The `pre.iam_roles` step grants a role of the `setIAM.yaml.sample` file
  only when preflight finds it missing and the deployer holds no direct
  binding of it, so a role that a group grants stays with the group.
- The `pre.iam_roles` step never grants Billing Account Administrator.
- When the deployer lacks Billing Account Administrator on the billing
  account, the step stops with the `gcloud billing accounts
  add-iam-policy-binding` command for a billing account administrator.
- The `pre.iam_roles` step checks again every 15 seconds for up to 2
  minutes after a grant, and stops with exit status 4 when IAM has not
  applied the grant by then.
- When the deployer already holds each failing role directly, the step
  grants nothing, says so, and waits the same 2 minutes.
- A role that still fails after that wait stops the step with exit status
  4, because an earlier grant may still propagate or an IAM deny policy
  may withhold a permission of the role.
- The `pre.iam_roles` and `pre.preflight` steps and the manual confirmations
  apply only before the first Stage 0 apply, because Stage 0 then manages
  the organization roles.
- The remote providers file and the remote backend mark that first apply,
  so a remote state that the deploy cannot read never turns these steps
  back on.
- The `s0.apply_workload` step needs the `s0.ready` step, so the `--only`
  and `--from-step` flags never skip the workload billing check.
- The `s1.billing_grant` step grants Billing Account User, the least
  privilege that links projects, where the DDG names Billing Account
  Administrator.
- A manual step that the deployer can run, such as the `s1.billing_grant`
  step, offers to run it, and hands off to another identity otherwise.

### 10.2 Select steps

The selection flags pick the steps of one run, and the deploy keeps them in
catalog order.

- The `--stage` flag selects `pre`, `0`, or `1`, or a stage name such as
  `1-resman`, and accepts repeats.
- The `--only` flag selects single steps by ID and accepts repeats.
- The `--only` flag checks the prerequisites of each step but never runs
  them, so the run stops when one is not done.
- A prerequisite that run-state records as done counts only when its check
  cannot tell, so a later `stellar init` change still stops the run.
- The `--from-step` flag skips the selected steps before the named one.
- The `--yes` flag answers the routine questions, which apply a reviewed
  plan, grant the deployer the missing organization roles in the
  `pre.iam_roles` step, and allow the BigQuery services on the workload
  folder in the `s0.allow_bq` step.
- The `s0.allow_bq` step lists every service that Assured Workloads allows
  along with BigQuery, and the `--yes` flag answers it only when each one
  is a BigQuery service.
- Manual steps, plan findings that need a confirmation, and the
  organization IAM review always ask, even with the `--yes` flag.
- The `--non-interactive` flag never prompts, so the deploy stops with exit
  status 4 at the first question.
- The `--prefix`, `--home`, and `--repo` flags select the environment as for
  the other commands.

### 10.3 Exit codes

Every command shares these exit codes, and the deploy adds statuses 4 and 5.

| Status | Meaning |
| --- | --- |
| `0` | Every selected step is done. |
| `1` | A preflight check failed, or an `imports scan` or `iam` command could not reach Google Cloud. |
| `2` | A flag or an answer is invalid. |
| `3` | The render refused to replace a manually edited file. |
| `4` | The deploy stopped for you at a manual step, a handoff, a check that cannot tell, a declined question, a pending check, an engine or environment check, or a held lock. |
| `5` | A step failed after the bounded remedies, a plan guard refused the apply, or run-state is unreadable. |

- The `stellar status` command exits with status 4 while a selected step is
  not done.
- The `stellar iam restore` command exits with status 4 when you do not type
  the organization ID.

### 10.4 Resume a deploy

The `run-state.json` file of the environment records the outcome of each
step, so a rerun knows what the last run did.

- Each step checks first, so a rerun skips the steps that are done.
- An apply records the state lineage, serial, and remote generation that it
  left behind, and the hash of the stage inputs.
- An apply step stays done while the state and the inputs match that
  record.
- An apply that fails also records the state it left behind, so the rerun
  knows that the deploy wrote that state.
- A state whose lineage no run-state record holds, such as one applied by
  hand or kept after the `run-state.json` file went missing, leaves an
  apply step unknown.
- The `stellar status` command reports such a step as `manual`.
- The deploy asks before it plans such a step again, and the `--yes` flag
  never answers that question.
- A known failure, such as a missing service agent or a BigQuery
  restriction, runs its remedy and retries the step a bounded number of
  times.
- A remedy question that you decline, or that the `--non-interactive` flag
  forbids, uses no attempt, so the deploy stops with exit status 4 and the
  rerun asks again.
- The `s0.migrate_state` step stops with exit status 4 when the local and
  remote states disagree, and names both lineages and serials, so you keep
  the right one before the rerun.
- A Stage 0 workspace on the local backend without a state stops before
  its init when the bootstrap bucket holds a Stage 0 state, so a workspace
  that a render created again never applies against an empty state.
- The `s0.remote_providers` step resumes such a workspace, because it
  copies the remote providers file into it.
- Once an init configures the remote backend, `terraform init` ignores a
  non-empty local state, so the step moves that file to the `plans/`
  folder when the remote state already holds it, and stops otherwise.
- Any other failure stops with exit status 5 and prints the end of the
  Terraform output and the path of its log.
- A step that needs another identity stops with a handoff card that names
  the capability, the current identity, and the commands that resume the
  step.

### 10.5 Plans and logs

The deploy keeps every artifact with mode 0600 in folders that only your
user can read.

- The `plans/` folder holds each saved plan as a `.tfplan` file, its
  `terraform show -json` document, and its text.
- Each plan file name holds the stage, the step, and the time.
- The `plans/` folder also holds a copy of the local state before each
  apply, migration, import, or state push.
- The `plans/` folder also keeps the local providers file that the
  `s0.remote_providers` step replaces.
- The `plans/` folder also keeps each module manifest that a render moves
  away after an engine change.
- The `logs/` folder holds one log per Terraform command.
- Each log header lists the names of the environment variables that the
  deploy removed or kept, never their values.
- The deploy removes the impersonation variables, the `TF_VAR_` variables,
  and the other variables that change what Terraform reads, so the run
  matches the reviewed plan.
- Every Terraform command stops with exit status 4 when `CLOUDSDK_CONFIG`
  names a folder without application default credentials and
  `GOOGLE_APPLICATION_CREDENTIALS` is unset, because Terraform would then
  run as another identity than the one preflight checked.
- Logs and plans hold real identifiers and can echo sensitive values, so
  never attach them to issues or pull requests.

### 10.6 Deploy lock

The `deploy.lock` file of the environment keeps a second deploy from running
at the same time.

- A held lock stops the deploy with exit status 4 and names the command and
  the start time of the holder.
- The deploy never guesses whether a holder still runs, so delete the file
  once no deploy runs.
- The `stellar status` and `stellar guide` commands take no lock and write
  nothing.

### 10.7 Engine provenance

The deploy prints the commit of the engine checkout before the first step
and marks uncommitted changes as dirty.

- Run-state records the engine path and commit of the last init.
- Every init first checks that the workspace links point into this engine,
  and stops with exit status 4 otherwise, so the rerun of
  `stellar deploy --stage <n>` relinks the workspace in its render step.
- Terraform records the folder of each local module in the
  `.terraform/modules/modules.json` file, and a plain `terraform init`
  keeps those records.
- A render that relinks the workspace therefore moves that file to the
  `plans/` folder, so the next init uses the modules of the new engine.
- Every init also stops with exit status 4 while that file still records
  another engine.
- Another engine path, a different commit, or uncommitted changes ask for
  a confirmation before the next init.
- Each apply also records the engine commit and the provider lock file, so
  the plan guards blame an organization policy update on an outside change
  only while the inputs, the commit, and the provider versions match the
  last apply.

### 10.8 Deployment status

The `stellar status` command runs the check of every step against the files,
run-state, and Google Cloud, and writes nothing.

- The header shows the Stage 0 phase, the backend, and the local, backup,
  and remote states.
- The header also shows the engine, the last run, the last plan, the last
  organization IAM review, the pending manual steps, the lock, and the
  stage service accounts.
- One table lists every step with its status, detail, fix, and
  documentation link, in the layout of the preflight report.
- The title of each step names the step ID and its stage, so you can pass
  the ID to the `--only` and `--from-step` flags.
- The tables use the preflight statuses, so a done step is `pass`, a step
  that cannot tell is `manual`, a step that does not apply is `skip`, and
  any other step is `fail` with the deploy status leading the detail.
- The `--stage` flag limits the report to some stages.
- The `--json` flag prints the report as JSON, and each step carries the
  fields of a `stellar preflight --json` check.

## 11 Review organization IAM

Stage 0 binds organization roles authoritatively, so an apply removes the
grants that it does not declare, and the deploy reviews them before it
applies.

### 11.1 Review gate

Every apply whose plan changes organization IAM first saves the live policy
under the `iam-snapshots/` folder.

- A plan that removes no grant and replaces no owner of an imported
  project passes without a question.
- Otherwise the review lists each removed grant, each replaced audit log
  configuration, each rewritten conditional binding, and the owners of
  imported projects.
- A plan that manages no organization IAM, such as a Stage 1 plan, still
  asks before it replaces the owners of an imported project, and the
  `--yes` flag never answers that question.
- You keep the removed grants, confirm, skip the review, or abort.
- Keeping the grants adds them to the `overrides.0-bootstrap.iam` answer,
  renders again, and plans again.
- Confirming and skipping both need the organization ID typed, and
  run-state records the decision.
- The `--yes` flag never answers the review.
- The deploy reads the policy etag again before the apply, and reviews
  again when someone changed the policy in the meantime.
- A policy that changes three times during the review stops the deploy, so
  you can find out who edits it before you rerun the deploy.
- A role whose member list grows in the answers loses the comments inside
  that list, while new roles keep every comment.

### 11.2 IAM commands

The `stellar iam` commands save, compare, and restore the organization IAM
policy outside a deploy.

```bash
stellar iam snapshot --reason before-audit
stellar iam diff
stellar iam diff --plan plans/0-s0.apply_final-20261029T120000Z.json
stellar iam restore iam-snapshots/20261029T120000Z-gate.json
```

- The `stellar iam snapshot` command saves the live policy in the
  `gcloud organizations get-iam-policy --format=json` shape, with a
  metadata file beside it.
- The `stellar iam diff` command lists the grants that changed since the
  newest snapshot, or since the snapshot that the `--snapshot` flag names.
- The `--plan` flag of the `stellar iam diff` command lists the grants that
  applying a saved plan removes and adds instead.
- A relative path that the current folder lacks names a file of the
  environment, so the `plans/` and `iam-snapshots/` paths that the deploy
  prints work from any folder.
- The `stellar iam restore` command shows what the restore changes, asks
  for the organization ID, saves the live policy as a new snapshot, and
  writes the snapshot back.
- When someone changed the policy in the meantime, the restore reads and
  saves it again, asks for the organization ID again when the changes
  differ, and retries up to three times.
- The `--emit-overrides` flag adds the missing grants of the roles that
  Stage 0 manages to the `overrides.0-bootstrap.iam` answer instead, so the
  next Stage 0 apply grants them.
- The snapshot file leaves out the etag, which the metadata file keeps, so
  the `gcloud organizations set-iam-policy` command restores it by hand
  even after the policy changed.

## 12 Develop the CLI

The `cli/` project follows the
[Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
with the ruff settings in `cli/pyproject.toml`.

- Install the development environment with `uv sync` in the `cli/`
  directory.
- Run the tests with `uv run pytest`.
- Format and lint the code with `uv run ruff format` and `uv run ruff check`.
- Check types with `uv run pyright`.
- Unit tests replace Google Cloud with in-memory fakes, so they never touch
  the network.
- The `FakeCloud` class in the `cli/tests/conftest.py` file records every
  Google Cloud write, and the `FakeTerraform` class there returns scripted
  Terraform results.
- The `cli/tests/fixtures/plans/` folder holds hand-built
  `terraform show -json` documents with placeholder values for the plan and
  guard tests.
- Tests that carry the `terraform` marker run the real Terraform binary and
  skip when it is missing.
- Run only those tests with `uv run pytest -m terraform`.
- Snapshot tests keep their expected output in the
  `cli/tests/__snapshots__/` folder.
- Run `uv run pytest --snapshot-update` after an intended output change,
  and review the snapshot diff before you commit it.
- Sync tests in the `cli/tests/test_repo.py` and
  `cli/tests/test_deploy_catalog.py` files read the repository, the helper
  scripts, and the DDG, so they fail when the documentation and the code
  drift apart.

## 13 Manual fallback

Each deploy step names the manual commands that do the same, and the
`stellar guide` command prints them. These are the Terraform commands of the
manual flow for Stage 0.

```bash
ENV=$STELLAR_HOME/envs/abc
WS=$ENV/fast/stages-aw/0-bootstrap
terraform -chdir=$WS init -input=false
terraform -chdir=$WS plan -input=false -out=$ENV/plans/s0.tfplan
terraform -chdir=$WS apply -input=false $ENV/plans/s0.tfplan
```

- Save each plan in the `plans/` folder of the environment, never in the
  workspace, so a later apply never picks up a stale plan file.
- Review the saved plan before you apply it, because the first apply makes
  the organization IAM roles that Stage 0 manages authoritative.
- No command passes the `-var` option, because the
  `0-bootstrap-phase.auto.tfvars` file that the render writes sets the
  `bootstrap_user` variable for the first apply.
- After the first apply, set the gcloud project to the new
  `<prefix>-prod-iac-core-0` project.
- Copy the `fast-config/providers/0-bootstrap-providers.tf` file of the
  environment over the `0-bootstrap-providers.tf` file in the workspace.
- Run `terraform -chdir=$WS init -migrate-state` to move the state into the
  remote bucket.
- Run `stellar init --set stage0_phase=final` and then `stellar render`, so
  the render removes the phase file.
- Run the same `init`, `plan`, and `apply` commands again for the final
  apply, which runs without the `bootstrap_user` variable.
- That final apply manages the organization policies and imports the ones
  that the scan recorded, so you skip the `import.sh` script.
- Keep the `stage0_phase` answer at `final` from then on, because a return
  to `bootstrap` plans to delete the organization policies that Stage 0
  manages.
- For Stage 1, run `stellar render --stage 1` after the final Stage 0 apply,
  then run Terraform with the `-chdir` option in the Stage 1 workspace, as
  the DDG Stage 1 section describes.
