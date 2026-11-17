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

"""Answer rules that read their limits and lists from the repository.

The model in `models` checks formats. These rules need the checkout, such
as the prefix limit in the Stage 0 validation block, and report readable
sentences that name the field, so the wizard can re-ask only that section
and `stellar init --non-interactive` can print them all at once.
"""

import pathlib
import re

from stellar_engine import paths
from stellar_engine import repo as repo_lib
from stellar_engine.config import derive
from stellar_engine.config import models
from stellar_engine.preflight import regions

# Project and service account IDs share this limit, enforced by the
# validation blocks in `modules/project` and `modules/iam-service-account`.
ID_MAX_LENGTH = 30

# Keys that stellar owns, so an override would desync the workspace from
# the environment: the prefix names the env, its workspaces and its import
# IDs, outputs_location is the env's fast-config folder that Stage 1 links
# from, and bootstrap_user only goes into the phase file of the bootstrap
# phase, see `render.phase`.
_CLI_OWNED_KEYS = {
    paths.BOOTSTRAP: frozenset(
        {"bootstrap_user", "outputs_location", "prefix"}
    ),
    paths.RESMAN: frozenset({"outputs_location"}),
}

# The import ID of a google_assured_workloads_workload, the workload name.
_WORKLOAD_ID_RE = re.compile(
    r"organizations/(?P<org>[0-9]+)/locations/(?P<location>[^/]+)"
    r"/workloads/[^/]+"
)

_IDENT = r"[A-Za-z_][A-Za-z0-9_-]*"
_INDEX = r'\[(?:[0-9]+|"(?:[^"\\]|\\.)*")\]'
_MODULE_SEGMENT_RE = re.compile(rf"module\.{_IDENT}(?:{_INDEX})?\.")
_RESOURCE_RE = re.compile(
    rf"(?P<type>{_IDENT})\.(?P<name>{_IDENT})(?:{_INDEX})?"
)


def import_address_problems(address: str) -> list[str]:
    """Checks the syntax of a Terraform resource address for an import.

    A valid address is zero or more `module.<name>[<index>]` segments
    followed by `<type>.<name>[<index>]`, each index optional and either an
    integer or a quoted string, for example
    `module.billing-export-project[0].google_project.project[0]`.

    Args:
        address: The `to` address of an import block.

    Returns:
        Readable problems, empty when the address is valid.
    """
    if not address or address != address.strip():
        return [f"Import address {address!r} is empty or has spaces."]
    position = 0
    while match := _MODULE_SEGMENT_RE.match(address, position):
        position = match.end()
    if address.startswith("data.", position):
        return [f"Import address {address!r} is a data source."]
    resource = _RESOURCE_RE.fullmatch(address, position)
    if resource is None:
        return [
            f"Import address {address!r} is not a resource address such as "
            "module.<name>[<index>].<type>.<name>[<index>]."
        ]
    if resource.group("type") == "module":
        return [f"Import address {address!r} names a module, not a resource."]
    return []


def problems(answers: models.Answers, repo: repo_lib.Repo) -> list[str]:
    """Checks answers against the limits and lists in the repository.

    Args:
        answers: Answers that already passed model validation.
        repo: The engine checkout that renders them.

    Returns:
        Readable problems, each naming the field, empty when the answers
        are valid.
    """
    found = []
    limit = repo.prefix_max_length()
    if len(answers.prefix) > limit:
        found.append(
            f"prefix {answers.prefix} is longer than the {limit} characters "
            "Stage 0 allows."
        )
    regimes = repo.regime_names()
    regime = answers.compliance.regime
    if regime not in regimes:
        found.append(
            f"compliance.regime {regime} is not one of {', '.join(regimes)}."
        )
    known_groups = repo.default_groups()
    unknown = sorted(set(answers.groups) - set(known_groups))
    if unknown:
        found.append(
            f"groups keys {', '.join(unknown)} are not Stage 0 groups; use "
            f"{', '.join(sorted(known_groups))}."
        )
    found.extend(_phase_problems(answers))
    found.extend(_region_problems(answers))
    found.extend(_tenant_problems(answers, repo))
    for stage, imports in answers.imports.items():
        for address in imports:
            found.extend(
                f"imports.{stage}: {problem}"
                for problem in import_address_problems(address)
            )
    found.extend(_stage0_import_id_problems(answers, repo))
    found.extend(_workload_import_id_problems(answers, repo))
    found.extend(_org_policy_problems(answers, repo))
    found.extend(override_problems(answers, repo))
    return found


def override_problems(
    answers: models.Answers, repo: repo_lib.Repo
) -> list[str]:
    """Checks `answers.overrides` against what each stage accepts.

    An override must name a variable the stage declares, must not set a
    key that an `*.auto.tfvars.json` file provides, because Terraform reads
    those files after `terraform.tfvars` and silently ignores the override,
    and must not set a key that stellar derives for the environment.

    Args:
        answers: Answers that already passed model validation.
        repo: The engine checkout whose stage variables are used.

    Returns:
        Readable problems, each naming the override, empty when every
        override is valid.
    """
    return [
        problem
        for stage in paths.STAGES
        for problem in stage_override_problems(answers, repo, stage)
    ]


def stage_override_problems(
    answers: models.Answers, repo: repo_lib.Repo, stage: str
) -> list[str]:
    """Checks the overrides of one stage, as `override_problems` describes.

    Args:
        answers: Answers that already passed model validation.
        repo: The engine checkout whose stage variables are used.
        stage: Stage directory name, such as `0-bootstrap`.

    Returns:
        Readable problems, each naming the override.
    """
    overrides = answers.overrides.get(stage, {})
    if not overrides:
        return []
    found = []
    clashes = sorted(set(overrides) & repo.auto_tfvars_keys(stage))
    if clashes:
        found.append(
            f"overrides.{stage} sets {', '.join(clashes)}, which Stage 0 "
            f"outputs provide to {stage} through *.auto.tfvars.json; "
            "change it in the Stage 0 answers instead."
        )
    # Only Stage 0 versions that declare the variable read it, and stellar
    # derives it there; older versions reject it as unknown below.
    if (
        stage == paths.BOOTSTRAP
        and repo_lib.PROJECT_DELETION_POLICIES in overrides
        and repo_lib.PROJECT_DELETION_POLICIES
        in repo.stage_variable_names(stage)
    ):
        found.append(
            f"overrides.{stage} sets {repo_lib.PROJECT_DELETION_POLICIES}, "
            "which stellar derives from keep_imported_projects and "
            f"imports.{stage}; remove the override and set "
            "keep_imported_projects instead."
        )
    owned = sorted(set(overrides) & _CLI_OWNED_KEYS.get(stage, frozenset()))
    if owned:
        found.append(
            f"overrides.{stage} sets {', '.join(owned)}, which stellar "
            "derives for the environment; remove the override and change "
            "the answer itself, such as prefix or bootstrap_user."
        )
    unknown = sorted(set(overrides) - repo.stage_variable_names(stage))
    if unknown:
        found.append(
            f"overrides.{stage} sets {', '.join(unknown)}, but {stage} "
            "declares no such variable."
        )
    return found


def _stage0_import_id_problems(answers, repo):
    """Checks each Stage 0 project import ID against the derived ID.

    The `modules/project` call sets `project_id` from the prefix and the
    project name, and a different `project_id` forces a new project. An
    import of any other ID would make Terraform replace, and so delete, the
    adopted project.
    """
    imports = answers.imports.get(paths.BOOTSTRAP, {})
    found = []
    for project in repo.stage0_projects():
        import_id = imports.get(project.address)
        expected = derive.stage0_project_id(answers, project)
        if import_id is not None and import_id != expected:
            found.append(
                f"imports.{paths.BOOTSTRAP}: {project.address} imports "
                f"{import_id}, but Stage 0 names that project {expected} "
                f"from prefix {answers.prefix}, so Terraform would replace "
                f"the imported project; set the import ID to {expected}."
            )
    return found


def workload_name_pattern(answers):
    """Returns the workload name Stage 0 manages, with `<workload_id>`.

    Args:
        answers: The answers that name the organization and the regime,
            whose Assured Workloads location the name carries.
    """
    org = answers.organization.id
    location = derive.compliance_location(answers)
    return f"organizations/{org}/locations/{location}/workloads/<workload_id>"


def workload_name_problem(name, answers):
    """Checks that a workload name fits the organization and the location.

    The workload `organization` and `location` force a new workload, so a
    name from another organization or location would make Terraform
    replace the adopted workload.

    Args:
        name: The workload name, which is its import ID.
        answers: The answers that name the organization and the regime.

    Returns:
        None when the name fits, else what Stage 0 manages instead.
    """
    match = _WORKLOAD_ID_RE.fullmatch(name)
    location = derive.compliance_location(answers)
    if (
        match
        and match.group("org") == answers.organization.id
        and match.group("location").lower() == location.lower()
    ):
        return None
    return (
        f"Stage 0 manages the workload as {workload_name_pattern(answers)} "
        "for organization.id and the Assured Workloads location"
    )


def _workload_import_id_problems(answers, repo):
    """Checks the import ID of a pre-created Assured Workloads workload."""
    address = repo.assured_workload().address
    import_id = answers.imports.get(paths.BOOTSTRAP, {}).get(address)
    if import_id is None:
        return []
    problem = workload_name_problem(import_id, answers)
    if problem is None:
        return []
    return [
        f"imports.{paths.BOOTSTRAP}: {address} imports {import_id}, but "
        f"{problem}, so Terraform would replace the imported workload; use "
        "the workload name that the Assured Workloads API returns."
    ]


def _org_policy_problems(answers, repo):
    """Checks `existing_org_policies` against the Stage 0 policy files."""
    names = answers.existing_org_policies
    if not names:
        return []
    # Every regime counts here, so a regime change does not invalidate
    # the list; the import filter drops policies the regime omits, and
    # preflight compares the list with the regime's own policies.
    scan = repo.scan_org_policies(names)
    found = []
    if scan.custom:
        found.append(
            f"existing_org_policies lists {', '.join(scan.custom)}, which "
            "use custom constraints that Stage 0 creates in the same apply, "
            "so Stage 0 never imports them; remove them."
        )
    if scan.undeclared:
        found.append(
            f"existing_org_policies lists {', '.join(scan.undeclared)}, "
            "which Stage 0 does not declare in data/org-policies or "
            "data/custom-org-policies; remove them or rerun stellar imports "
            "scan."
        )
    config = answers.overrides.get(paths.BOOTSTRAP, {}).get(
        "org_policies_config"
    )
    if isinstance(config, dict) and config.get("import_defaults") is True:
        found.append(
            f"overrides.{paths.BOOTSTRAP}.org_policies_config."
            "import_defaults is true while existing_org_policies is set; "
            "import_defaults imports a fixed list of policies whether or "
            "not each one exists, so a missing policy fails the import, "
            "while the scan lists exactly the declared policies that "
            "exist; remove import_defaults."
        )
    return found


def _phase_problems(answers):
    """Checks that the bootstrap phase names its bootstrap user."""
    if (
        answers.stage0_phase != models.STAGE0_BOOTSTRAP
        or answers.bootstrap_user is not None
    ):
        return []
    return [
        "bootstrap_user is required while stage0_phase is "
        f"{models.STAGE0_BOOTSTRAP}, because the first Stage 0 apply grants "
        "that human user the roles to finish the bootstrap; set it, or set "
        f"stage0_phase to {models.STAGE0_FINAL} once the state migration is "
        "done."
    ]


def phase_change_problems(
    previous_phase: object, updated_phase: object
) -> list[str]:
    """Refuses to return `stage0_phase` from final to bootstrap.

    A bootstrap apply skips the organization policies, the essential
    contacts and the policy factory, so after a final apply it would
    delete what that apply created. Callers run this check only when the
    run-state records a final Stage 0 apply.

    The check compares raw values, so a caller can pass the phase of an
    answers file that no longer passes the model, which `stellar init`
    must still be able to repair.

    Args:
        previous_phase: The `stage0_phase` value before the change, None
            when the answers did not set it.
        updated_phase: The `stage0_phase` value after the change.

    Returns:
        One readable problem for the regression, else nothing.
    """
    if (
        previous_phase != models.STAGE0_FINAL
        or updated_phase != models.STAGE0_BOOTSTRAP
    ):
        return []
    return [
        f"stage0_phase cannot return from {models.STAGE0_FINAL} to "
        f"{models.STAGE0_BOOTSTRAP}: the final Stage 0 apply already ran, "
        "and a bootstrap apply would delete the organization policies and "
        f"essential contacts it manages; keep stage0_phase "
        f"{models.STAGE0_FINAL}."
    ]


def warnings(answers: models.Answers) -> list[str]:
    """Returns non-fatal findings about how the answers fit together.

    `billing.external_grant` only matters when Stage 0 manages no billing
    IAM and no `billing_override` links projects with the credentials that
    run Terraform.

    Args:
        answers: Answers that already passed model validation.

    Returns:
        Readable sentences, each naming the fields.
    """
    billing = answers.billing
    if not billing.external_grant:
        return []
    found = []
    if not billing.no_iam:
        found.append(
            "billing.external_grant is set while billing.no_iam is false, "
            "so Stage 0 and Stage 1 grant the stage service accounts "
            "billing access themselves and the external grant is redundant."
        )
    if answers.billing_override is not None:
        found.append(
            "billing.external_grant and billing_override are both set; "
            "billing_override links the projects with the credentials that "
            "run Terraform, so the stage service accounts never use the "
            "external grant."
        )
    return found


def _region_problems(answers):
    if answers.compliance.allow_unlisted_region:
        return []
    allowed = regions.supported_regions(answers.compliance.regime)
    if allowed is None or answers.region in allowed:
        return []
    return [
        f"region {answers.region} is not an Assured Workloads region for "
        f"{answers.compliance.regime}; use one of {', '.join(sorted(allowed))}"
        " or set compliance.allow_unlisted_region after checking "
        f"{regions.LOCATIONS_DOC}."
    ]


def _tenant_problems(answers, repo):
    found = []
    limit = repo.tenant_key_max_length()
    for tenant in answers.resman.tenants:
        if len(tenant) > limit:
            found.append(
                f"resman.tenants key {tenant} is longer than the {limit} "
                "characters Stage 1 allows."
            )
    for kind, ids in (
        ("project ID", derive.tenant_project_ids(answers)),
        ("service account ID", derive.tenant_service_account_ids(answers)),
    ):
        for tenant, names in ids.items():
            found.extend(
                f"resman.tenants.{tenant}: Stage 1 {kind} {name} is "
                f"{len(name)} characters, over the {ID_MAX_LENGTH} limit; "
                "shorten the prefix, env key or tenant key."
                for name in names
                if len(name) > ID_MAX_LENGTH
            )
    return found


def home_references(answers: models.Answers, home: pathlib.Path) -> list[str]:
    """Finds answer values that point into the home folder.

    stellar derives home-relative values such as `outputs_location` at
    render time, so a copied or moved home repoints on the next render. A
    stored path into the home would keep pointing at the old location. The
    recorded `engine.path` is exempt.

    Args:
        answers: The answers to save.
        home: The home folder.

    Returns:
        Readable problems naming each offending field.
    """
    root = home.expanduser().resolve()
    # stellar records the engine checkout itself and render compares it
    # with the checkout in use, so a home that holds the engine, such as a
    # private home repository with the engine as a submodule, is fine.
    data = answers.model_dump(
        mode="json", exclude_none=True, exclude={"engine"}
    )
    return [
        f"{field} points into the home {root}; stellar derives home paths "
        "at render time, so remove it."
        for field, value in _strings(data, "")
        if _is_inside(value, root)
    ]


def _strings(value, field):
    if isinstance(value, dict):
        for key, item in value.items():
            yield from _strings(item, f"{field}.{key}" if field else key)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _strings(item, f"{field}[{index}]")
    elif isinstance(value, str):
        yield field, value


def _is_inside(value, root):
    # Only absolute and home-directory paths are unambiguous; a relative
    # value such as a tenant key is not a path.
    if not value.startswith(("/", "~")):
        return False
    path = pathlib.Path(value).expanduser().resolve()
    return path == root or path.is_relative_to(root)
