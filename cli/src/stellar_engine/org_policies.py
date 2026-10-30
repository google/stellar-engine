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

"""Records the existing organization policies that Stage 0 imports.

Stage 0 fails to create a policy that already exists on the organization,
so `existing_org_policies` in `answers.yaml` lists the existing policies
that Stage 0 declares, and `stellar render` writes an import block that
adopts them on the final Stage 0 apply.
"""

from collections.abc import Callable
import pathlib
from typing import Any

from stellar_engine import paths
from stellar_engine import repo as repo_lib
from stellar_engine.config import answers as answers_lib
from stellar_engine.config import models
from stellar_engine.gcp import api


def scan(
    answers: models.Answers, repo: repo_lib.Repo, cloud: api.CloudApi
) -> repo_lib.OrgPolicyScan:
    """Sorts the organization's policies by whether Stage 0 imports them.

    Args:
        answers: The environment answers, which name the organization and
            the regime whose policies count as declared.
        repo: The engine checkout that declares the Stage 0 policies.
        cloud: Lists the policies set on the organization.

    Returns:
        The existing policies in three lists. All three are empty when
        the organization has no policies.

    Raises:
        api.CloudError: If Google Cloud refuses to list the policies.
        api.CredentialsError: If no Application Default Credentials exist.
    """
    existing = cloud.list_org_policies(answers.organization.id)
    return repo.scan_org_policies(existing, answers.compliance.regime)


def keep_scanned(
    scanned: repo_lib.OrgPolicyScan,
) -> Callable[[dict[str, Any]], None]:
    """Returns the answers change that records the policies Stage 0 imports.

    The kept policies of the scan replace `existing_org_policies`, so a
    policy that is gone from the organization or that Stage 0 no longer
    declares drops out of the list.

    Args:
        scanned: The result of `scan`.

    Returns:
        A change for `answers.update`, which edits the answer data in
        place.
    """

    def change(data: dict[str, Any]) -> None:
        data["existing_org_policies"] = list(scanned.kept)

    return change


def record(
    env: paths.EnvPaths,
    scanned: repo_lib.OrgPolicyScan,
    repo: repo_lib.Repo,
    home: pathlib.Path,
) -> bool:
    """Saves the policies that Stage 0 imports to the answers.

    Args:
        env: The environment whose `answers.yaml` holds the list.
        scanned: The result of `scan`, which `keep_scanned` records.
        repo: The engine checkout that validates the updated answers.
        home: The home folder that holds the environment, which the
            answers must not point into.

    Returns:
        Whether the answers file changed. The save is skipped when the
        file already lists the kept policies.

    Raises:
        answers_lib.AnswersError: If the answers file cannot be read, or
            the updated answers have problems or cannot be saved.
    """
    outcome = answers_lib.update(
        env.answers, keep_scanned(scanned), repo=repo, home=home
    )
    return outcome.changed
