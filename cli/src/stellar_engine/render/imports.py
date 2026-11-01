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

"""Writes Terraform `import` blocks for resources that already exist.

Some organizations pre-create the Stage 0 projects, because linking a
project to their billing account needs a human. Terraform must adopt those
projects instead of creating them, so the answers list each resource
address with its import ID and the renderer turns them into a
`<stage>-imports.tf` file in the workspace. The file is a real file owned
by the environment; `workspace.sync` never links or removes it.

Stage 0 also adopts the organization policies that `stellar imports scan`
records in `existing_org_policies`, replacing `0-bootstrap/import.sh`.
"""

from collections.abc import Mapping, Sequence
import pathlib

from stellar_engine import paths
from stellar_engine import repo as repo_lib
from stellar_engine.config import models
from stellar_engine.config import validate as validate_lib
from stellar_engine.render import hcl
from stellar_engine.render import writer

FILENAME_TEMPLATE = "{stage}-imports.tf"
_FILE_MODE = 0o644
# The stage locals that the import file adds; the prefix keeps them apart
# from the locals of the stage code.
_POLICIES_LOCAL = "stellar_existing_org_policies"
_IMPORTS_LOCAL = "stellar_org_policy_imports"
_ORG_POLICY_COMMENT = (
    "# stellar imports scan found these organization policies, which Stage 0",
    "# declares. The first apply passes bootstrap_user, so Stage 0 manages no",
    "# organization policies yet and nothing is imported. The final apply",
    "# adopts the policies that already exist instead of failing to create",
    "# them. The filter drops constraints that the regime templates omit.",
)


class ImportBlockError(Exception):
    """Raised when import blocks cannot be rendered or written."""


def filename(stage: str) -> str:
    """Returns the import file name of a stage.

    For example `0-bootstrap-imports.tf` for `0-bootstrap` or its alias `0`.

    Raises:
        ValueError: If the stage name is unknown.
    """
    return FILENAME_TEMPLATE.format(stage=paths.resolve_stage(stage))


def warnings(
    answers: models.Answers, stage: str, repo: repo_lib.Repo
) -> list[str]:
    """Returns non-fatal findings about the import blocks of a stage.

    An import into a resource that the configuration does not create fails
    at plan time, so the operator learns before running Terraform.

    Args:
        answers: The environment answers.
        stage: Stage name or alias.
        repo: The engine checkout whose Stage 0 projects are checked.

    Returns:
        Readable sentences, one per import into a project that Stage 0
        skips for the billing answers or into a workload that it skips for
        the regime.
    """
    stage = paths.resolve_stage(stage)
    if stage != paths.BOOTSTRAP:
        return []
    created = repo.created_stage0_projects(
        no_iam=answers.billing.no_iam,
        is_org_level=answers.billing.is_org_level,
    )
    # Only the billing export project depends on the billing answers; see
    # `repo.stage0_project_created`.
    skipped = [
        _module_prefix(project)
        for project in repo.stage0_projects()
        if project not in created
    ]
    imports = answers.imports.get(stage, {})
    found = [
        f"imports.{stage}: {address} targets the billing export project, "
        f"which Stage 0 only creates when {repo_lib.BILLING_EXPORT_CONDITION}"
        ", so the import would fail."
        for address in imports
        if address.startswith(tuple(skipped))
    ]
    workload = repo.assured_workload()
    regime = answers.compliance.regime
    if workload.address in imports and not workload.created(regime):
        found.append(
            f"imports.{stage}: {workload.address} targets the Assured "
            f"Workloads workload, which Stage 0 does not create for regime "
            f"{regime}, so the import would fail."
        )
    return found


def _module_prefix(project):
    """Returns the address prefix of every resource in a project module.

    For example `module.billing-export-project[0].`.
    """
    module, _, _ = project.address.partition(".google_project.")
    return f"{module}."


def header(
    stage: str,
    prefix: str,
    *,
    imports: bool = True,
    org_policies: bool = False,
) -> list[str]:
    """Returns the generated header of a stage's import file.

    Args:
        stage: Stage name or alias.
        prefix: Environment prefix.
        imports: Whether the file imports entries of `imports.<stage>`.
        org_policies: Whether the file imports `existing_org_policies`.
    """
    stage = paths.resolve_stage(stage)
    sources = [
        source
        for source, wanted in (
            (f"imports.{stage}", imports),
            ("existing_org_policies", org_policies),
        )
        if wanted
    ]
    return [
        f"{writer.MARKER}{prefix}/answers.yaml {' and '.join(sources)}.",
        "# Edit answers.yaml and rerun stellar render; the next render "
        "replaces manual edits.",
    ]


def _org_policy_blocks(names: Sequence[str]) -> list[str]:
    """Returns the locals and the `import` block of the organization policies.

    The import block mirrors the `import_defaults` block in
    `0-bootstrap/organization.tf`, which targets the same resources.
    """
    listed = [f"    {hcl.quote(name)}," for name in sorted(set(names))]
    locals_block = "\n".join(
        [
            *_ORG_POLICY_COMMENT,
            "locals {",
            f"  {_POLICIES_LOCAL} = [",
            *listed,
            "  ]",
            f"  {_IMPORTS_LOCAL} = toset([",
            f"    for name in local.{_POLICIES_LOCAL} :",
            "    name if contains(keys(local.org_policies), name)",
            "  ])",
            "}",
        ]
    )
    import_block = "\n".join(
        [
            "import {",
            "  for_each = (",
            "    var.bootstrap_user == null",
            f"    ? local.{_IMPORTS_LOCAL}",
            "    : toset([])",
            "  )",
            '  id = "organizations/${var.organization.id}/policies/'
            '${each.key}"',
            "  to = module.organization.google_org_policy_policy.default"
            "[each.key]",
            "}",
        ]
    )
    return [locals_block, import_block]


def dumps(
    imports: Mapping[str, str],
    header: Sequence[str],
    org_policies: Sequence[str] = (),
) -> str:
    """Renders one `import` block per entry, sorted by address.

    Args:
        imports: Resource address mapped to import ID.
        header: Comment lines emitted at the top of the file.
        org_policies: Constraints of existing organization policies that
            Stage 0 imports on its final apply, only for `0-bootstrap`.

    Returns:
        The HCL text in `terraform fmt` canonical form, empty when there
        are no imports and no organization policies.

    Raises:
        ImportBlockError: If an address is not a resource address.
    """
    if not imports and not org_policies:
        return ""
    found = [
        problem
        for address in imports
        for problem in validate_lib.import_address_problems(address)
    ]
    if found:
        raise ImportBlockError(" ".join(found))
    blocks = ["\n".join(header)] if header else []
    # `to` is a reference, not a string, so the address stays unquoted.
    blocks.extend(
        "\n".join(
            [
                "import {",
                f"  to = {address}",
                f"  id = {hcl.quote(imports[address])}",
                "}",
            ]
        )
        for address in sorted(imports)
    )
    if org_policies:
        blocks.extend(_org_policy_blocks(org_policies))
    return "\n\n".join(blocks) + "\n"


def text(answers: models.Answers, stage: str) -> str:
    """Returns the import file of a stage for the answers.

    Args:
        answers: The environment answers.
        stage: Stage name or alias.

    Returns:
        The file text, empty when the stage imports nothing.

    Raises:
        ImportBlockError: If an address is not a resource address.
    """
    stage = paths.resolve_stage(stage)
    entries = answers.imports.get(stage, {})
    policies = answers.existing_org_policies if stage == paths.BOOTSTRAP else []
    return dumps(
        entries,
        header(
            stage,
            answers.prefix,
            imports=bool(entries),
            org_policies=bool(policies),
        ),
        policies,
    )


def write(
    workspace: pathlib.Path, stage: str, answers: models.Answers
) -> writer.Outcome | None:
    """Writes or removes the import file of a stage in its workspace.

    Every render replaces the file, so it always matches the answers.
    When the stage has no imports and no organization policies to adopt, a
    previously generated file is removed, because a stale import block
    would adopt a resource the answers no longer name.

    Args:
        workspace: The stage workspace directory.
        stage: Stage name or alias.
        answers: The environment answers.

    Returns:
        What happened to the `filename(stage)` file in the workspace:
        created, updated, unchanged or removed. None when the stage imports
        nothing and no generated file was there to remove.

    Raises:
        ImportBlockError: If an address is invalid, or a file of the same
            name exists that stellar did not generate.
    """
    stage = paths.resolve_stage(stage)
    target = workspace / filename(stage)
    content = text(answers, stage)
    exists = target.exists() or target.is_symlink()
    if exists and not writer.is_generated(target):
        # With nothing to write, an operator's own file stays in place.
        if not content:
            return None
        raise ImportBlockError(
            f"stellar did not write {target}; move it away or delete it, "
            "then rerun stellar render."
        )
    return writer.write_owned(target, content, _FILE_MODE)
