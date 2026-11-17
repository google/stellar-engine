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

"""Writes the Stage 0 phase file that sets `bootstrap_user`.

The `bootstrap_user` variable of `0-bootstrap` switches the stage between
two modes. Set, the first apply grants the human user the bootstrap roles
and skips the organization policies, the essential contacts and the
organization policy factory. Unset, the final apply manages and imports the
organization policies. The DDG passes the variable with `-var` on the first
apply only, so a plain `terraform apply` silently picks the wrong mode.

The `stage0_phase` answer owns the mode instead. In the bootstrap phase the
renderer writes `0-bootstrap-phase.auto.tfvars`, which Terraform reads on
every run without a `-var` option; in the final phase it removes that file.
The file is a real file owned by the environment; `workspace.sync` never
links or removes it.
"""

import pathlib
import re

from stellar_engine import fsutil
from stellar_engine import paths
from stellar_engine import repo as repo_lib
from stellar_engine import workspace as workspace_lib
from stellar_engine.config import models
from stellar_engine.render import hcl
from stellar_engine.render import writer

FILENAME = f"{paths.BOOTSTRAP}-phase.auto.tfvars"
VARIABLE = "bootstrap_user"
# The bootstrap user is personal data, so only the owner reads the file.
_FILE_MODE = 0o600
# The remote providers file that the state migration copies into the
# workspace declares this backend; `providers.tf.tmp` declares none.
_REMOTE_BACKEND_RE = re.compile(r'^\s*backend\s+"gcs"', re.MULTILINE)


class PhaseFileError(Exception):
    """Raised when the phase file cannot be rendered or written."""


def header(prefix: str) -> list[str]:
    """Returns the generated header of the phase file.

    Args:
        prefix: Environment prefix.
    """
    return [
        f"{writer.MARKER}{prefix}/answers.yaml stage0_phase and {VARIABLE}.",
        "# The file exists only in the bootstrap phase, so every Stage 0",
        f"# run sets {VARIABLE} without a -var option. stellar deploy",
        "# removes it after the state migration. By hand, run",
        f"# stellar init --set stage0_phase={models.STAGE0_FINAL} and then",
        "# stellar render, which removes this file for the final apply.",
    ]


def text(answers: models.Answers, repo: repo_lib.Repo) -> str:
    """Returns the phase file text for the answers.

    Args:
        answers: The environment answers.
        repo: The engine checkout, whose Stage 0 must declare the variable.

    Returns:
        The file text, empty in the final phase.

    Raises:
        PhaseFileError: If the bootstrap phase lacks a bootstrap user, or
            Stage 0 declares no `bootstrap_user` variable.
    """
    if answers.stage0_phase != models.STAGE0_BOOTSTRAP:
        return ""
    if VARIABLE not in repo.stage_variable_names(paths.BOOTSTRAP):
        raise PhaseFileError(
            f"{paths.BOOTSTRAP} declares no variable {VARIABLE}, so this "
            "engine version has no bootstrap phase; set stage0_phase to "
            f"{models.STAGE0_FINAL}."
        )
    if answers.bootstrap_user is None:
        raise PhaseFileError(
            f"{VARIABLE} is required while stage0_phase is "
            f"{models.STAGE0_BOOTSTRAP}; set it in answers.yaml."
        )
    return hcl.dumps(
        {VARIABLE: answers.bootstrap_user}, header=header(answers.prefix)
    )


def declares_remote_backend(text: str) -> bool:
    """Returns whether a providers file declares the remote state backend.

    The remote providers file that Stage 0 writes declares `backend "gcs"`,
    and `providers.tf.tmp` declares none. The file turns remote when the
    operator or `stellar deploy` copies it into the workspace, which is
    before the state migration, so this alone never shows a migration.

    Args:
        text: The providers file text.
    """
    return _REMOTE_BACKEND_RE.search(text) is not None


def warnings(workspace: pathlib.Path, answers: models.Answers) -> list[str]:
    """Returns non-fatal findings about the phase of a Stage 0 workspace.

    Args:
        workspace: The Stage 0 workspace directory.
        answers: The environment answers.

    Returns:
        One sentence when the bootstrap phase meets a workspace whose state
        already moved to the remote backend, which only happens after the
        first apply, so the next apply is the final one.
    """
    if answers.stage0_phase != models.STAGE0_BOOTSTRAP:
        return []
    providers = workspace / workspace_lib.BOOTSTRAP_PROVIDERS
    if not declares_remote_backend(fsutil.read_text_or_none(providers) or ""):
        return []
    return [
        f"{providers} uses the remote state backend, so the first Stage 0 "
        "apply already ran, but stage0_phase is still "
        f"{models.STAGE0_BOOTSTRAP}; run stellar deploy --stage 0, whose "
        "s0.phase_final step switches it, or run stellar init --set "
        f"stage0_phase={models.STAGE0_FINAL} and stellar render before the "
        "next apply."
    ]


# Kept for the callers that check the phase file; see `writer.is_generated`.
is_generated = writer.is_generated


def planned(
    workspace: pathlib.Path, answers: models.Answers, repo: repo_lib.Repo
) -> str:
    """Returns the content the phase file gets, without writing it.

    Args:
        workspace: The Stage 0 workspace directory.
        answers: The environment answers.
        repo: The engine checkout.

    Returns:
        The file text, empty when the file must not exist.

    Raises:
        PhaseFileError: If the answers cannot be rendered, or a file of
            the same name exists that stellar did not generate.
    """
    target = workspace / FILENAME
    content = text(answers, repo)
    if (target.exists() or target.is_symlink()) and not is_generated(target):
        # In either phase the foreign file would set or unset the mode
        # behind the answers, so stellar neither replaces nor ignores it.
        raise PhaseFileError(
            f"stellar did not write {target}; move it away or delete it, "
            "then rerun stellar render."
        )
    return content


def write(
    workspace: pathlib.Path, answers: models.Answers, repo: repo_lib.Repo
) -> writer.Outcome | None:
    """Writes or removes the phase file in the Stage 0 workspace.

    Every render replaces the file, so it always matches the answers. In
    the final phase a previously generated file is removed, because a
    stale `bootstrap_user` would keep Stage 0 in the bootstrap mode.

    Args:
        workspace: The Stage 0 workspace directory.
        answers: The environment answers.
        repo: The engine checkout.

    Returns:
        What happened to the file: created, updated, unchanged or removed.
        None in the final phase when no generated file was there to remove.

    Raises:
        PhaseFileError: If the answers cannot be rendered, or a file of
            the same name exists that stellar did not generate.
    """
    content = planned(workspace, answers, repo)
    return writer.write_owned(workspace / FILENAME, content, _FILE_MODE)
