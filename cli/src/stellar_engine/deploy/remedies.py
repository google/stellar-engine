# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Known deploy failures, and how stellar fixes or explains each one.

Each remedy matches a failure by patterns over the end of its output, or
by the key of the plan guard finding that refused the apply. A remedy with
an action fixes the cause and the engine runs the step again, a bounded
number of times per step; a remedy without one explains the fix. Every
text names the manual fallback of the DDG or the helper scripts, and the
patterns come from errors that the DDG, `scripts/deploy.sh` and the lab
deployment recorded.
"""

from collections.abc import Callable, Sequence
import dataclasses
import re

from stellar_engine import naming
from stellar_engine.config import derive
from stellar_engine.deploy import cloud_ops
from stellar_engine.deploy import model
from stellar_engine.deploy import state_fix
from stellar_engine.preflight import checks
from stellar_engine.terraform import guards
from stellar_engine.terraform import plan as plan_lib
from stellar_engine.terraform import runner as runner_lib

# A remedy reads only this much of the output, where Terraform prints its
# errors.
TAIL_LINES = 200
_FLAGS = re.IGNORECASE | re.MULTILINE
_DDG_403 = (
    "docs/ddg.md#cross-stage-iam-impersonation-and-troubleshooting-403-errors"
)
_DDG_NOTES = "docs/ddg.md#additional-notes"
_DDG_BILLING = "docs/ddg.md#billing-accounts"
_DDG_VARIABLES = "docs/ddg.md#variables"
_DDG_IL5_NETWORKING = "docs/ddg.md#il4il5-stage-21---networking"

# Remedy keys; the import_replace_15725 key is also a plan guard key.
BQ_RESTRICT_SERVICE_USAGE = "bq_restrict_service_usage"
SA_PROPAGATION = "sa_propagation"
KMS_SERVICE_AGENT = "kms_service_agent"
IL5_GCS_SERVICE_AGENT = "il5_gcs_service_agent"
API_DISABLED = "api_disabled"
STATE_LOCK = "state_lock"
BACKEND_INIT_REQUIRED = "backend_init_required"
MIGRATE_REFUSED = "migrate_refused"
WORKLOAD_CREATE_FAILED = "workload_create_failed"
LOG_BUCKET_TIMEOUT = "log_bucket_timeout"
IMPORT_REPLACE_15725 = guards.IMPORT_REPLACE_15725
CMEK_FOLDER_SETTINGS = "cmek_folder_settings"
CUSTOM_ROLE_EXISTS = "custom_role_exists"
SINK_EXISTS = "sink_exists"
PROJECT_ID_TAKEN = "project_id_taken"
BILLING_UNLINKED = "billing_unlinked"
ADC_QUOTA_PROJECT = "adc_quota_project"

_KMS_AGENT_RE = re.compile(
    r"service-(\d+)@gcp-sa-cloudkms\.iam\.gserviceaccount\.com"
)
_GCS_AGENT_RE = re.compile(
    r"service-(\d+)@gs-project-accounts\.iam\.gserviceaccount\.com"
)
# The ErrorInfo details that Terraform prints for a disabled service, or
# the console link of the error message.
_CONSUMER_RE = re.compile(r'"consumer":\s*"projects/([\w-]+)"')
_SERVICE_RE = re.compile(r'"service":\s*"([\w.-]+\.googleapis\.com)"')
_CONSOLE_LINK_RE = re.compile(
    r"apis/api/([\w.-]+\.googleapis\.com)/\w+\?project=([\w-]+)"
)
_LOCK_ID_RE = re.compile(r"^\s*ID:\s+(\S+)", re.MULTILINE)
_KMS_SERVICE = "cloudkms.googleapis.com"
# The names of any deployment, as remedy texts name them.
_AUTOMATION_PROJECT = naming.automation_project_id("<prefix>")
_WORKLOAD_FOLDER = naming.workload_folder_name("<prefix>")
_ENABLE_ACCOUNT = cloud_ops.enable_accounts_command(
    _AUTOMATION_PROJECT, ["<email>"]
)


@dataclasses.dataclass(frozen=True)
class Failure:
    """A failed step run, as remedies see it.

    Attributes:
        step_id: The step.
        stage: Its catalog stage.
        command: What failed, such as `apply`.
        output: The output of the failure.
        plan: The parsed plan of the failed step, or None.
        findings: The keys of the plan guard findings that refused it.
    """

    step_id: str
    stage: str
    command: str
    output: str
    plan: plan_lib.Plan | None = None
    findings: tuple[str, ...] = ()

    @property
    def tail(self) -> str:
        """The last `TAIL_LINES` lines of the output."""
        return tail(self.output)


def tail(output: str, lines: int = TAIL_LINES) -> str:
    """Returns the last lines of an output, where Terraform prints errors.

    Args:
        output: The output.
        lines: How many lines to keep.
    """
    return "\n".join(output.strip().splitlines()[-lines:])


# Fixes the cause of a failure; returns whether the step may run again.
Action = Callable[[model.Context, Failure], bool]


@dataclasses.dataclass(frozen=True)
class Remedy:
    """A known failure and its fix.

    Attributes:
        key: The key that steps list and guard findings carry.
        title: What went wrong.
        patterns: Expressions that must all match the output tail,
            case-insensitively.
        action: Fixes the cause, or None when only a person can.
        max_attempts: How often the action may run per step until the
            step is done again.
        waits: Seconds to wait after each attempt; the last repeats.
        doc: Repository-relative link to the documentation.
        text: The fix, naming the manual fallback.
    """

    key: str
    title: str
    patterns: tuple[re.Pattern[str], ...]
    action: Action | None
    max_attempts: int
    waits: tuple[int, ...]
    doc: str
    text: str

    def matches(self, failure: Failure) -> bool:
        """Returns whether the remedy fits a failure.

        Args:
            failure: The failure.
        """
        if self.key in failure.findings:
            return True
        tail = failure.tail
        return bool(self.patterns) and all(
            pattern.search(tail) for pattern in self.patterns
        )

    def wait(self, attempt: int) -> int:
        """Returns the seconds to wait after an attempt, counted from 0."""
        if not self.waits:
            return 0
        return self.waits[min(attempt, len(self.waits) - 1)]


def match(failure: Failure, keys: Sequence[str]) -> Remedy | None:
    """Returns the first remedy among a step's keys that fits a failure.

    Args:
        failure: The failure.
        keys: The step's remedy keys, in the order to try them.

    Raises:
        KeyError: If a key names no remedy.
    """
    for key in keys:
        remedy = REMEDIES[key]
        if remedy.matches(failure):
            return remedy
    return None


def _patterns(*expressions: str) -> tuple[re.Pattern[str], ...]:
    """Compiles expressions that match case-insensitively per line."""
    return tuple(re.compile(expression, _FLAGS) for expression in expressions)


def _allow_bq(ctx: model.Context, failure: Failure) -> bool:
    """Allows the BigQuery services on the workload folder."""
    del failure  # The workload, not the error, says what to allow.
    return cloud_ops.allow_bq_run(ctx)


def _retry(ctx: model.Context, failure: Failure) -> bool:
    """Retries after the wait, for causes that time fixes."""
    del ctx, failure  # Waiting is the fix.
    return True


def _agent_action(
    pattern: re.Pattern[str],
    label: str,
    create: Callable[[model.Context, str], object],
) -> Action:
    """Returns an action that creates the service agents an error names.

    Args:
        pattern: Matches an agent email; its group is the project number.
        label: The service, such as `Cloud KMS`, for the progress line.
        create: Creates the agent of one project.
    """

    def action(ctx: model.Context, failure: Failure) -> bool:
        projects = sorted(set(pattern.findall(failure.tail)))
        for project in projects:
            ctx.say(f"Creating the {label} service agent of project {project}.")
            create(ctx, project)
        return bool(projects)

    return action


_kms_agent = _agent_action(
    _KMS_AGENT_RE,
    "Cloud KMS",
    lambda ctx, project: ctx.cloud.generate_service_identity(
        project, _KMS_SERVICE
    ),
)
_gcs_agent = _agent_action(
    _GCS_AGENT_RE,
    "Cloud Storage",
    lambda ctx, project: ctx.cloud.gcs_service_agent(project),
)


def disabled_api(output: str) -> tuple[str, str] | None:
    """Returns the disabled service and its project named in an error.

    Args:
        output: The error output.

    Returns:
        The service and the consumer project, or None.
    """
    consumer = _CONSUMER_RE.search(output)
    service = _SERVICE_RE.search(output)
    if consumer and service:
        return service.group(1), consumer.group(1)
    link = _CONSOLE_LINK_RE.search(output)
    return (link.group(1), link.group(2)) if link else None


def _enable_api(ctx: model.Context, failure: Failure) -> bool:
    """Enables the API that the error names in its project."""
    found = disabled_api(failure.tail)
    if found is None:
        return False
    service, project = found
    ctx.say(f"Enabling {service} on project {project}.")
    ctx.cloud.enable_services(project, [service])
    return True


def _force_unlock(ctx: model.Context, failure: Failure) -> bool:
    """Releases the state lock that the error names, after asking."""
    found = _LOCK_ID_RE.search(failure.tail)
    if found is None or failure.stage == model.PRE_STAGE:
        return False
    ctx.require_terraform_env()
    lock_id = found.group(1)
    workspace = ctx.workspace(failure.stage)
    question = (
        f"Release the state lock {lock_id}? Answer yes only when no other "
        "Terraform run uses this state."
    )
    if not ctx.confirm(question):
        raise model.StoppedError(
            f"The state of {workspace} is locked by {lock_id}.",
            remedy=runner_lib.manual(
                workspace, ("force-unlock",), (), [lock_id]
            ),
        )
    tf = ctx.terraform.for_step(failure.stage, failure.step_id)
    completed = tf.force_unlock(workspace, lock_id)
    model.succeeded(completed, "force-unlock", log=tf.last_log)
    return True


def _fix_buckets(ctx: model.Context, failure: Failure) -> bool:
    """Fixes the buckets the plan replaces, or every bucket after a timeout."""
    replaced = [
        change.address
        for change in (failure.plan.changes if failure.plan else ())
        if change.type == guards.LOG_BUCKET_TYPE and change.deletes
    ]
    sinks = state_fix.sinks_of(replaced) or None
    buckets = state_fix.log_buckets(ctx, sinks)
    return state_fix.fix_log_buckets(ctx, buckets, step_id=failure.step_id)


_REMEDIES = (
    Remedy(
        key=BQ_RESTRICT_SERVICE_USAGE,
        title="BigQuery is not an allowed service of the workload folder",
        patterns=_patterns(
            r"restrictServiceUsage", r"bigquery\.googleapis\.com"
        ),
        action=_allow_bq,
        max_attempts=2,
        waits=(120,),
        doc=checks.DDG_STAGE0,
        text=cloud_ops.allow_bq_card(_WORKLOAD_FOLDER),
    ),
    Remedy(
        key=SA_PROPAGATION,
        title="A stage service account cannot be used yet",
        patterns=_patterns(
            r"\b403\b",
            r"iam\.serviceAccounts\.getAccessToken|does not have permission",
            r"-prod-iac-core-0\.iam\.gserviceaccount\.com",
        ),
        action=_retry,
        max_attempts=3,
        waits=(10, 30, 60),
        doc=_DDG_403,
        text=(
            "A new service account takes minutes to propagate. If the "
            "error stays, check that your identity is a member of the "
            f"{derive.ORGANIZATION_ADMINS} group, which holds Service "
            "Account Token Creator on the stage service accounts, and that "
            f"the accounts are enabled: {_ENABLE_ACCOUNT}. Then rerun "
            "stellar deploy."
        ),
    ),
    Remedy(
        key=KMS_SERVICE_AGENT,
        title="The Cloud KMS service agent does not exist yet",
        patterns=_patterns(
            r"gcp-sa-cloudkms\.iam\.gserviceaccount\.com", r"does not exist"
        ),
        action=_kms_agent,
        max_attempts=2,
        waits=(30, 60),
        doc=_DDG_NOTES,
        text=(
            "Create the agent: gcloud beta services identity create "
            "--service=cloudkms.googleapis.com --project=<project>, or "
            "disable and enable cloudkms.googleapis.com in the project as "
            "scripts/deploy.sh does. Wait 30 seconds and rerun stellar "
            "deploy."
        ),
    ),
    Remedy(
        key=IL5_GCS_SERVICE_AGENT,
        title="The Cloud Storage service agent does not exist yet",
        patterns=_patterns(
            r"gs-project-accounts\.iam\.gserviceaccount\.com",
            r"does not exist",
        ),
        action=_gcs_agent,
        max_attempts=2,
        waits=(30,),
        doc=_DDG_IL5_NETWORKING,
        text=(
            "Open Cloud Storage Settings in the project named in the "
            "error, which creates the agent, or run gcloud storage "
            "service-agent --project=<project>. Then rerun stellar deploy."
        ),
    ),
    Remedy(
        key=API_DISABLED,
        title="A Google Cloud API is disabled",
        patterns=_patterns(r"SERVICE_DISABLED|has not been used in project"),
        action=_enable_api,
        max_attempts=1,
        waits=(30,),
        doc=checks.DOC_APIS,
        text=(
            "Enable the API named in the error in the project named there: "
            f"{checks.enable_command('<project>', ['<service>'])}. The "
            "bootstrap project needs the APIs of "
            "fast/stages-aw/0-bootstrap/enableServices.sh. Then rerun "
            "stellar deploy."
        ),
    ),
    Remedy(
        key=STATE_LOCK,
        title="The Terraform state is locked",
        patterns=_patterns(r"Error acquiring the state lock"),
        action=_force_unlock,
        max_attempts=1,
        waits=(),
        doc=_DDG_NOTES,
        text=(
            "Another Terraform run holds the state lock, or a crashed run "
            "left it. When no other run uses the state: terraform "
            "-chdir=<workspace> force-unlock <lock ID>, then rerun "
            "stellar deploy."
        ),
    ),
    Remedy(
        key=BACKEND_INIT_REQUIRED,
        title="The workspace backend is not initialized",
        patterns=_patterns(r"Backend initialization required"),
        action=None,
        max_attempts=0,
        waits=(),
        doc=checks.DDG_STAGE0,
        text=(
            "The remote providers file is in the workspace, but the "
            "backend was not initialized. Rerun stellar deploy, which "
            "initializes the workspace before every plan. Fallback: "
            "terraform -chdir=<workspace> init -migrate-state."
        ),
    ),
    Remedy(
        key=MIGRATE_REFUSED,
        title="Terraform asked to approve a state migration",
        patterns=_patterns(r"Can't ask approval for state migration"),
        action=None,
        max_attempts=0,
        waits=(),
        doc=checks.DDG_STAGE0,
        text=(
            "stellar ran a state migration without -force-copy, which is "
            "a stellar bug; please report it. Fallback: compare the local "
            "and remote states, then run terraform -chdir=<workspace> "
            "init -migrate-state and answer yes."
        ),
    ),
    Remedy(
        key=WORKLOAD_CREATE_FAILED,
        title="Assured Workloads could not create the workload",
        patterns=_patterns(
            r"Failed to create workload|ERROR_CODE_CREATE_WORKLOAD_FAILURE"
        ),
        action=None,
        max_attempts=0,
        waits=(),
        doc=_DDG_BILLING,
        text=(
            "Creating a workload needs an identity that can use the "
            "billing account. Ask an organization administrator with "
            f"billing access to create the {_WORKLOAD_FOLDER} workload "
            "as the s0.ready step describes, add its name to "
            "imports.0-bootstrap, and rerun stellar deploy. A failed "
            "create can leave soft-deleted folders, which expire after "
            "30 days."
        ),
    ),
    Remedy(
        key=LOG_BUCKET_TIMEOUT,
        title="Creating a log bucket timed out",
        patterns=_patterns(
            r"google_logging_project_bucket_config", r"timeout|Error waiting"
        ),
        action=_fix_buckets,
        max_attempts=1,
        waits=(),
        doc=checks.DDG_STAGE0,
        text=(
            "The buckets usually exist outside the state. "
            f"{state_fix.MANUAL_FIX}"
        ),
    ),
    Remedy(
        key=IMPORT_REPLACE_15725,
        title="An imported log bucket would be replaced",
        patterns=_patterns(
            r"google_logging_project_bucket_config",
            r"must be replaced",
            r"imported from",
        ),
        action=_fix_buckets,
        max_attempts=1,
        waits=(),
        doc=checks.DDG_STAGE0,
        text=(
            "terraform-provider-google stores the project of an imported "
            "log bucket as projects/<id>, which terraform-provider-google "
            f"issue 15725 tracks. {state_fix.MANUAL_FIX}"
        ),
    ),
    Remedy(
        key=CMEK_FOLDER_SETTINGS,
        title="Folder logging settings need a KMS key",
        patterns=_patterns(
            r"restrictNonCmekServices", r"logging\.googleapis\.com"
        ),
        action=None,
        max_attempts=0,
        waits=(),
        doc=checks.DDG_STAGE0,
        text=(
            "This engine version sets folder logging settings, which a "
            "CMEK organization policy refuses. Update the engine checkout "
            "to a release whose Stage 0 skips folder logging settings "
            "under CMEK, then rerun stellar deploy."
        ),
    ),
    Remedy(
        key=CUSTOM_ROLE_EXISTS,
        title="An organization custom role already exists",
        patterns=_patterns(r"already exists", r"roles/"),
        action=None,
        max_attempts=0,
        waits=(),
        doc=checks.DDG_STAGE0,
        text=(
            "A custom role of an earlier deployment exists, or was deleted "
            "less than about 37 days ago and still reserves its ID. "
            "Undelete it if needed with gcloud iam roles undelete <role ID> "
            "--organization=<org>, then add an imports.0-bootstrap entry "
            "for module.organization.google_organization_iam_custom_role."
            'roles["<name>"] with the ID organizations/<org>/roles/<role '
            "ID>, as scripts/deploy.sh imported them, and rerun stellar "
            "deploy."
        ),
    ),
    Remedy(
        key=SINK_EXISTS,
        title="An organization log sink already exists",
        patterns=_patterns(r"already exists", r"sinks/"),
        action=None,
        max_attempts=0,
        waits=(),
        doc=checks.DDG_STAGE0,
        text=(
            "Add an imports.0-bootstrap entry for module.organization."
            'google_logging_organization_sink.sink["<name>"] with the ID '
            "organizations/<org>/sinks/<name>, as scripts/deploy.sh "
            "imported them, or delete the old sink. Then rerun stellar "
            "deploy."
        ),
    ),
    Remedy(
        key=PROJECT_ID_TAKEN,
        title="A project ID is taken",
        patterns=_patterns(
            r"\b409\b",
            r"already exists|requested entity already exists",
            r"projects/",
        ),
        action=None,
        max_attempts=0,
        waits=(),
        doc=_DDG_VARIABLES,
        text=(
            "Project IDs are global, and a deleted project keeps its ID "
            "for about 30 days. Choose another prefix with stellar init "
            "--new-prefix, or import the existing project through "
            "imports, then rerun stellar deploy."
        ),
    ),
    Remedy(
        key=BILLING_UNLINKED,
        title="A project has no usable billing account",
        patterns=_patterns(
            r"billing account", r"disabled|not found|BILLING_DISABLED"
        ),
        action=None,
        max_attempts=0,
        waits=(),
        doc=checks.DDG_STAGE0,
        text=(
            "Link the project to the billing account again at "
            "https://console.cloud.google.com/billing/projects, or run "
            "gcloud billing projects link <project> --billing-account="
            "<account>, then rerun stellar deploy."
        ),
    ),
    Remedy(
        key=ADC_QUOTA_PROJECT,
        title="The credentials need a quota project",
        patterns=_patterns(r"USER_PROJECT_DENIED|quota project"),
        action=None,
        max_attempts=0,
        waits=(),
        doc=_DDG_NOTES,
        text=(
            "Set the quota project of your user credentials: "
            f"{cloud_ops.quota_command(_AUTOMATION_PROJECT)}, then rerun "
            "stellar deploy."
        ),
    ),
)
REMEDIES: dict[str, Remedy] = {remedy.key: remedy for remedy in _REMEDIES}
