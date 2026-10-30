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

"""Reads how far Stage 0 got, and decides how to initialize its backend.

Stage 0 starts on the local backend, copies the remote providers file into
its workspace after the first apply, then moves its state into the bootstrap
bucket. No single file shows where it stands: the providers file turns
remote before the migration runs, and Terraform empties the local state
only after it copied it. `probe` reads every signal from files and from the
remote state object, never through Terraform, so `stellar status` works in
any window of that sequence.

`migrate_decision` turns a probe into one init. Terraform's
`init -migrate-state -force-copy` copies a non-empty local state over the
remote one without comparing lineage or serial, so the decision copies
only when the remote state is absent or older in the same lineage, and
refuses when it cannot tell.
"""

from collections.abc import Iterator, Mapping
import dataclasses
import enum
import json
import pathlib
from typing import Any, Protocol

from stellar_engine import fsutil
from stellar_engine import naming
from stellar_engine import paths
from stellar_engine import repo as repo_lib
from stellar_engine import workspace as workspace_lib
from stellar_engine.config import models
from stellar_engine.deploy import run_state as run_state_lib
from stellar_engine.gcp import api
from stellar_engine.render import phase as phase_lib

STATE_FILE = "terraform.tfstate"
BACKUP_FILE = "terraform.tfstate.backup"
# Where `terraform init` records the configured backend of a workspace.
CACHED_BACKEND = pathlib.PurePosixPath(".terraform/terraform.tfstate")
# The state object of a stage whose providers file sets no backend prefix.
REMOTE_OBJECT = "default.tfstate"
GCS = "gcs"
_CONSUMER_FOLDER = "CONSUMER_FOLDER"
# The state bucket name and the automation service account of each catalog
# stage, from `0-bootstrap/automation.tf`.
_BACKENDS = {"0": ("bootstrap", "bootstrap-0"), "1": ("resman", "resman-0")}
_REMOTE_PROVIDERS = workspace_lib.REMOTE_BOOTSTRAP_PROVIDERS


class Source(Protocol):
    """What `probe` reads; `model.Context` provides it."""

    @property
    def env(self) -> paths.EnvPaths:
        """The environment."""
        ...

    @property
    def answers(self) -> models.Answers:
        """The environment answers."""
        ...

    @property
    def cloud(self) -> api.CloudApi:
        """Reads the remote state object."""
        ...


@dataclasses.dataclass(frozen=True)
class Backend:
    """The remote state of a stage.

    Attributes:
        bucket: The state bucket.
        service_account: The automation service account that the stage's
            remote providers file impersonates.
    """

    bucket: str
    service_account: str

    @property
    def state_uri(self) -> str:
        """The `gs://` URI of the state object."""
        return f"gs://{self.bucket}/{REMOTE_OBJECT}"


def backend(prefix: str, stage: str) -> Backend:
    """Returns the remote state of a catalog stage.

    Mirrors the `providers` outputs of `0-bootstrap/outputs.tf`, which set
    no backend prefix for Stages 0 and 1, so each state is `default.tfstate`
    at the bucket root.

    Args:
        prefix: Deployment prefix.
        stage: Catalog stage `0` or `1`.

    Raises:
        KeyError: If the stage has no remote state of its own.
    """
    bucket, account = _BACKENDS[stage]
    return Backend(
        naming.state_bucket(prefix, bucket),
        naming.automation_sa_email(prefix, account),
    )


@dataclasses.dataclass(frozen=True)
class WorkloadRef:
    """The Assured Workloads workload as a state records it.

    Attributes:
        name: Workload name, or None.
        folder: Consumer folder as `folders/<id>`, or None.
    """

    name: str | None
    folder: str | None


@dataclasses.dataclass(frozen=True)
class StateSummary:
    """What a Terraform state file holds.

    Attributes:
        size: Bytes; Terraform empties the local file after a migration.
        parsed: Whether the content is a state document.
        serial: The state serial.
        lineage: The state lineage.
        addresses: Every resource instance address.
        outputs: Whether the state holds root module outputs.
        workload: The Assured Workloads workload, if the state has one.
    """

    size: int
    parsed: bool = False
    serial: int | None = None
    lineage: str | None = None
    addresses: frozenset[str] = frozenset()
    outputs: bool = False
    workload: WorkloadRef | None = None

    @property
    def empty(self) -> bool:
        """Whether there is nothing to migrate.

        Mirrors Terraform's `State.Empty`: no bytes, or a state without
        resources and without root outputs. Terraform migrates a state
        that only holds outputs.
        """
        return self.size == 0 or (
            self.parsed and not self.addresses and not self.outputs
        )

    def record(
        self, generation: int | None = None
    ) -> run_state_lib.StateRecord:
        """Returns the state as run-state records it.

        Its string form, `serial <serial> lineage <lineage>`, is how
        messages name a state.

        Args:
            generation: The Cloud Storage generation of a remote state.
        """
        return run_state_lib.StateRecord(
            lineage=self.lineage,
            serial=self.serial,
            remote_generation=generation,
        )


@dataclasses.dataclass(frozen=True)
class CachedBackend:
    """The backend that the last `terraform init` configured.

    Attributes:
        type: Backend type, such as `gcs`; None for the local backend.
        bucket: The configured bucket, or None.
    """

    type: str | None
    bucket: str | None


@dataclasses.dataclass(frozen=True)
class RemoteState:
    """The remote state object of a stage.

    Attributes:
        readable: Whether the read worked, so `exists` can be trusted.
        exists: Whether the object exists.
        generation: The object generation, which bucket versioning keeps.
        summary: What the object holds.
        error: Why the read failed.
    """

    readable: bool
    exists: bool = False
    generation: int | None = None
    summary: StateSummary | None = None
    error: str | None = None

    @property
    def empty(self) -> bool:
        """Whether the object is missing or holds no resources."""
        return self.summary is None or self.summary.empty

    @property
    def lineage(self) -> str | None:
        """The lineage of the remote state, or None."""
        return self.summary.lineage if self.summary else None

    @property
    def serial(self) -> int | None:
        """The serial of the remote state, or None."""
        return self.summary.serial if self.summary else None

    def readable_summary(self, target: Backend) -> StateSummary | None:
        """Returns `summary`, or raises when the object could not be read.

        Args:
            target: Where the state lives, which the error names.

        Raises:
            api.CloudError: If neither identity could read the object,
                which a check reports as UNKNOWN.
        """
        if not self.readable:
            raise api.CloudError(
                f"Cannot read the remote state {target.state_uri}: {self.error}"
            )
        return self.summary


@dataclasses.dataclass(frozen=True)
class Probe:
    """Every Stage 0 progress signal.

    Attributes:
        phase_file: Whether stellar's phase file is in the workspace.
        foreign_phase_file: Whether a phase file that stellar did not
            write is in the workspace.
        providers_remote: Whether the workspace providers file declares the
            remote backend.
        providers_match: Whether the workspace providers file has the bytes
            of the remote providers file under `fast-config`.
        outputs_providers: Whether Stage 0 wrote the remote providers file
            under `fast-config`, which its first apply does.
        cached: The backend the last init configured, or None.
        local: The local state file, or None when missing.
        backup: The local state backup Terraform keeps, or None.
        remote: The remote state object.
        backend: Where the remote state lives.
    """

    phase_file: bool
    foreign_phase_file: bool
    providers_remote: bool
    providers_match: bool
    outputs_providers: bool
    cached: CachedBackend | None
    local: StateSummary | None
    backup: StateSummary | None
    remote: RemoteState
    backend: Backend

    @property
    def configured(self) -> bool:
        """Whether init configured the remote backend in its bucket."""
        return (
            self.cached is not None
            and self.cached.type == GCS
            and self.cached.bucket == self.backend.bucket
        )

    @property
    def uses_remote(self) -> bool:
        """Whether Terraform reads the remote state in this workspace."""
        return self.providers_remote and self.configured

    @property
    def migrated(self) -> bool | None:
        """Whether the state lives in the bootstrap bucket.

        It needs the remote backend configured, the local state emptied,
        and the remote state present in the lineage of the local backup.

        Returns:
            None when the remote state cannot be read.
        """
        if not self.uses_remote:
            return False
        if self.local is not None and not self.local.empty:
            return False
        if not self.remote.readable:
            return None
        if self.remote.empty:
            return False
        backup = self.backup.lineage if self.backup else None
        return backup is None or backup == self.remote.lineage

    @property
    def state(self) -> StateSummary | None:
        """The state that Terraform reads: remote once configured."""
        if self.uses_remote:
            return self.remote.summary
        return self.local

    def readable_state(self) -> StateSummary | None:
        """Returns `state`, or raises when Terraform reads an unreadable one.

        Raises:
            api.CloudError: If the workspace uses the remote state and it
                cannot be read, which a check reports as UNKNOWN.
        """
        if self.uses_remote:
            return self.remote.readable_summary(self.backend)
        return self.local


class MigrateAction(enum.StrEnum):
    """How to initialize the Stage 0 workspace."""

    # Plain `init -input=false`.
    INIT = "init"
    # Back up the local state, then `init -migrate-state -force-copy`.
    MIGRATE = "migrate"
    # Archive and empty the local state, then plain init, which reads the
    # newer remote state.
    ARCHIVE = "archive"
    # Change nothing; the operator decides.
    REFUSE = "refuse"


@dataclasses.dataclass(frozen=True)
class MigrateDecision:
    """The init that `migrate_decision` chose.

    Attributes:
        action: What to do.
        reason: Why, with the lineages and serials it compared.
        remedy: What the operator does after a refusal that
            `refusal_remedy` does not cover, or None.
    """

    action: MigrateAction
    reason: str
    remedy: str | None = None


def _describe(summary: StateSummary | None, where: str) -> str:
    """Returns how a decision names one state, such as `local serial 3 ...`."""
    if summary is None:
        return f"{where} state absent"
    return f"{where} {summary.record()}"


def _states(probe: Probe) -> str:
    """Returns the local and the remote state, as a decision names them."""
    return (
        f"{_describe(probe.local, 'local')}; "
        f"{_describe(probe.remote.summary, 'remote')}"
    )


def _refuse(reason: str) -> MigrateDecision:
    """Returns the decision that changes nothing and stops the deploy."""
    return MigrateDecision(MigrateAction.REFUSE, reason)


def refusal_remedy(probe: Probe, decision: MigrateDecision) -> str:
    """Returns what the operator does after `migrate_decision` refuses.

    Args:
        probe: The Stage 0 signals the decision read.
        decision: The refusal, whose own remedy wins.
    """
    if decision.remedy:
        return decision.remedy
    return (
        f"Compare the local {STATE_FILE} with {probe.backend.state_uri}, "
        "keep the right one, and rerun stellar deploy. The bucket keeps "
        "noncurrent versions of the remote state."
    )


def _remote_elsewhere(probe: Probe) -> MigrateDecision | None:
    """Refuses a local init beside a Stage 0 state in the bucket.

    A workspace that `stellar render` created again, or a new home with
    the same answers, has the local providers file and no state, while
    the bootstrap bucket holds the state of earlier applies. A local init
    would plan against an empty state and create every resource again,
    such as a second Assured Workloads workload. The remote providers file
    under `fast-config` shows a first apply even when the bucket cannot be
    read.

    Returns:
        The refusal, or None when the local backend is right.
    """
    if probe.local is not None and not probe.local.empty:
        return None
    remote = probe.remote
    where = probe.backend.state_uri
    if remote.readable and not remote.empty:
        reason = (
            "The workspace uses the local backend and has no state, but "
            f"{where} holds the Stage 0 state, so a local init would plan "
            f"against an empty state. {_states(probe)}."
        )
    elif not remote.readable and probe.outputs_providers:
        reason = (
            "The workspace uses the local backend and has no state, but "
            f"Stage 0 already wrote fast-config/{_REMOTE_PROVIDERS}, and "
            f"{where} cannot be read: {remote.error}."
        )
    else:
        return None
    remedy = (
        "Run stellar deploy --only s0.remote_providers, or copy "
        f"fast-config/{_REMOTE_PROVIDERS} of the environment over "
        f"{workspace_lib.BOOTSTRAP_PROVIDERS} in the Stage 0 workspace, "
        "then rerun stellar deploy."
    )
    if not probe.outputs_providers:
        remedy = (
            f"Copy {_REMOTE_PROVIDERS} from the Stage 0 outputs bucket to "
            f"fast-config/{_REMOTE_PROVIDERS} of the environment first. "
            f"{remedy}"
        )
    return MigrateDecision(MigrateAction.REFUSE, reason, remedy)


def migrate_decision(probe: Probe) -> MigrateDecision:
    """Decides how to initialize the Stage 0 workspace.

    The table follows Terraform's backend initialization. Once init
    configured the bucket, init ignores the local file, so a non-empty
    local file there only goes to `plans/` when the remote state already
    holds it. Before that, a non-empty local state is copied over the
    remote one by `-force-copy`, so it is copied only when the remote
    state is absent, empty, or an older serial of the same lineage. A
    remote state at the local serial or newer wins: the local file goes to
    `plans/` and init reads the remote state. A different lineage, or a
    remote state that cannot be read, stops the deploy. A workspace on the
    local backend without a state also stops when the bucket holds a Stage
    0 state, or cannot be read after a first apply wrote the remote
    providers file. The decision never uses `-reconfigure` and never
    deletes `.terraform/`, which `scripts/deploy.sh` did.

    Args:
        probe: The Stage 0 signals.

    Returns:
        The init to run and why.
    """
    return _backend_decision(probe) or _state_decision(probe)


def _backend_decision(probe: Probe) -> MigrateDecision | None:
    """Decides from the providers file and the configured backend alone."""
    cached = probe.cached
    cached_gcs = cached is not None and cached.type == GCS
    if not probe.providers_remote:
        if cached_gcs:
            return _refuse(
                "The workspace providers file declares no backend, but "
                f"init configured the {GCS} backend; an init would copy "
                "the remote state over the local one. Copy the remote "
                "providers file into the workspace again."
            )
        return _remote_elsewhere(probe) or MigrateDecision(
            MigrateAction.INIT, "The workspace uses the local backend."
        )
    if probe.configured:
        return _configured_decision(probe)
    if cached is not None and cached_gcs:
        return _refuse(
            f"Init configured the bucket {cached.bucket}, not "
            f"{probe.backend.bucket}; check the workspace providers file."
        )
    return None


def _configured_decision(probe: Probe) -> MigrateDecision:
    """Decides once init configured the bucket.

    Init then ignores the local file, and `-migrate-state` copies nothing
    into a backend that is already configured, so a non-empty local file
    would keep `migrated` false on every rerun. It goes to `plans/` only
    when the remote state of the same lineage is as new or newer; any
    other local state stops the deploy.
    """
    configured = f"Init already configured gs://{probe.backend.bucket}"
    local = probe.local
    if local is None or local.empty:
        return MigrateDecision(MigrateAction.INIT, f"{configured}.")
    remote = probe.remote
    if not remote.readable:
        return _refuse(
            f"{configured}, which ignores the local state, and the remote "
            f"state cannot be read: {remote.error}. {_states(probe)}."
        )
    if (
        not remote.empty
        and remote.lineage == local.lineage
        and (remote.serial or 0) >= (local.serial or 0)
    ):
        return MigrateDecision(
            MigrateAction.ARCHIVE,
            f"{configured}, which ignores the local state; the remote state "
            "is as new or newer, so the local file is archived. "
            f"{_states(probe)}.",
        )
    return _refuse(
        f"{configured}, which ignores the local state, and the remote "
        "state does not hold it, so no init can move it there. "
        f"{_states(probe)}."
    )


def _state_decision(probe: Probe) -> MigrateDecision:
    """Decides by comparing the local and remote states."""
    if not probe.remote.readable:
        return _refuse(
            f"Cannot read the remote state {probe.backend.state_uri}: "
            f"{probe.remote.error}. {_states(probe)}."
        )
    local = probe.local
    if local is None or local.empty:
        return MigrateDecision(
            MigrateAction.INIT,
            "The local state is empty, so init reads the remote state. "
            f"{_states(probe)}.",
        )
    if probe.remote.empty:
        return MigrateDecision(
            MigrateAction.MIGRATE,
            "The remote state is absent, so the local state moves there. "
            f"{_states(probe)}.",
        )
    if probe.remote.lineage != local.lineage:
        return _refuse(
            "The local and remote states have different lineages, so "
            f"they are different states. {_states(probe)}."
        )
    if (probe.remote.serial or 0) < (local.serial or 0):
        return MigrateDecision(
            MigrateAction.MIGRATE,
            "The local state is newer than the remote state of the same "
            f"lineage. {_states(probe)}.",
        )
    return MigrateDecision(
        MigrateAction.ARCHIVE,
        "The remote state is as new as the local state or newer, so the "
        "local file is archived and init reads the remote state. "
        f"{_states(probe)}.",
    )


def instances(doc: Mapping[str, Any]) -> Iterator[tuple[str, dict[str, Any]]]:
    """Yields the address and the instance of every resource in a state.

    Args:
        doc: A Terraform state document, format version 4.

    Yields:
        The instance address, such as
        `module.x["k"].google_project.project[0]`, and the instance object
        as stored, so a caller can change its attributes.
    """
    for resource in doc.get("resources") or []:
        parts = [resource.get("module")]
        if resource.get("mode") == "data":
            parts.append("data")
        parts += [resource.get("type"), resource.get("name")]
        base = ".".join(str(part) for part in parts if part)
        for instance in resource.get("instances") or []:
            key = instance.get("index_key")
            # JSON quotes string keys and leaves numbers bare, as Terraform.
            suffix = "" if key is None else f"[{json.dumps(key)}]"
            yield f"{base}{suffix}", instance


def _workload(doc: Mapping[str, Any]) -> WorkloadRef | None:
    """Returns the workload and its consumer folder that a state holds."""
    for resource in doc.get("resources") or []:
        if resource.get("type") != repo_lib.WORKLOAD_RESOURCE:
            continue
        for instance in resource.get("instances") or []:
            attributes = instance.get("attributes") or {}
            folder = next(
                (
                    f"folders/{item.get('resource_id')}"
                    for item in attributes.get("resources") or []
                    if item.get("resource_type") == _CONSUMER_FOLDER
                ),
                None,
            )
            return WorkloadRef(attributes.get("name"), folder)
    return None


def summarize(data: bytes) -> StateSummary:
    """Returns what a state file holds.

    Args:
        data: The file content; empty after a migration.

    Returns:
        The summary. Content that is not a state document is reported as
        not parsed, never as empty.
    """
    if not data:
        return StateSummary(0)
    try:
        doc = json.loads(data)
    except ValueError:
        return StateSummary(len(data))
    if not isinstance(doc, dict):
        return StateSummary(len(data))
    serial, lineage = doc.get("serial"), doc.get("lineage")
    return StateSummary(
        size=len(data),
        parsed=True,
        # A corrupt state may hold other types, which run-state rejects.
        serial=serial if isinstance(serial, int) else None,
        lineage=lineage if isinstance(lineage, str) else None,
        addresses=frozenset(address for address, _ in instances(doc)),
        outputs=bool(doc.get("outputs")),
        workload=_workload(doc),
    )


def _file_summary(path: pathlib.Path) -> StateSummary | None:
    """Summarizes a state file, or returns None when it is missing."""
    data = fsutil.read_bytes_or_none(path)
    return None if data is None else summarize(data)


def _cached_backend(path: pathlib.Path) -> CachedBackend | None:
    """Reads the backend that `terraform init` recorded in a workspace."""
    data = fsutil.read_bytes_or_none(path)
    if data is None:
        return None
    try:
        doc = json.loads(data)
    except ValueError:
        return CachedBackend(None, None)
    found = doc.get("backend") if isinstance(doc, dict) else None
    if not isinstance(found, dict):
        return CachedBackend(None, None)
    config = found.get("config") or {}
    return CachedBackend(found.get("type"), config.get("bucket"))


def read_object_as(
    cloud: api.CloudApi, bucket: str, name: str, service_account: str
) -> api.ObjectData | None:
    """Reads an object with the credentials, then as a service account.

    The stage buckets grant the stage's automation service account, which
    the remote providers file impersonates, and not always the deployer.

    Args:
        cloud: Reads the object.
        bucket: The bucket.
        name: The object name.
        service_account: The service account to read as when Application
            Default Credentials are denied.

    Returns:
        The object, or None when it does not exist.

    Raises:
        api.AccessDeniedError: If both identities are denied, with both
            reasons.
        api.CloudError: If the read fails in another way.
        api.CredentialsError: If no Application Default Credentials exist.
    """
    errors = []
    for impersonate in (None, service_account):
        try:
            return cloud.read_object(bucket, name, impersonate=impersonate)
        except api.AccessDeniedError as error:
            errors.append(str(error))
    raise api.AccessDeniedError("; ".join(errors))


def read_remote(cloud: api.CloudApi, target: Backend) -> RemoteState:
    """Reads the remote state object of a stage; see `read_object_as`.

    Args:
        cloud: Reads the object.
        target: Where the state lives.

    Returns:
        The remote state; `readable` is False when neither identity can
        read it.
    """
    try:
        found = read_object_as(
            cloud, target.bucket, REMOTE_OBJECT, target.service_account
        )
    except api.CLOUD_ERRORS as error:
        return RemoteState(readable=False, error=str(error))
    if found is None:
        return RemoteState(readable=True)
    return RemoteState(
        readable=True,
        exists=True,
        generation=found.generation,
        summary=summarize(found.data),
    )


def probe(ctx: Source) -> Probe:
    """Reads the Stage 0 signals from files and the remote state object.

    Args:
        ctx: The deploy context, or anything with its `env`, `answers` and
            `cloud`.

    Returns:
        The probe. It never runs Terraform and never writes.
    """
    workspace = ctx.env.workspace(paths.BOOTSTRAP)
    phase_file = workspace / phase_lib.FILENAME
    present = phase_file.exists() or phase_file.is_symlink()
    generated = present and phase_lib.is_generated(phase_file)
    providers = fsutil.read_bytes_or_none(
        workspace / workspace_lib.BOOTSTRAP_PROVIDERS
    )
    outputs = fsutil.read_bytes_or_none(
        workspace_lib.remote_bootstrap_providers(ctx.env)
    )
    target = backend(ctx.answers.prefix, "0")
    text = (providers or b"").decode("utf-8", errors="replace")
    return Probe(
        phase_file=generated,
        foreign_phase_file=present and not generated,
        providers_remote=phase_lib.declares_remote_backend(text),
        providers_match=providers is not None and providers == outputs,
        outputs_providers=outputs is not None,
        cached=_cached_backend(workspace / CACHED_BACKEND),
        local=_file_summary(workspace / STATE_FILE),
        backup=_file_summary(workspace / BACKUP_FILE),
        remote=read_remote(ctx.cloud, target),
        backend=target,
    )
