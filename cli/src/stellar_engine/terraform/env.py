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

"""Builds the environment of the Terraform processes that stellar runs.

Terraform reads environment variables that silently change what a saved
plan does. `TF_VAR_bootstrap_user` flips Stage 0 back to the bootstrap
phase, `TF_CLI_ARGS_plan` can inject `-target` or `-var`, and the Google
credential variables outrank the identity that preflight checked. So
`build_env` removes them, sets the automation variables, and reports the
names it removed and kept, never their values, for the log header and
run-state.
"""

from collections.abc import Mapping
import dataclasses
import os
import pathlib

# The impersonation variables that `fast/stage-links.sh` tells the operator
# to unset. Preflight warns about the same names.
IMPERSONATION_ENV_VARS = (
    "GOOGLE_IMPERSONATE_SERVICE_ACCOUNT",
    "CLOUDSDK_AUTH_IMPERSONATE_SERVICE_ACCOUNT",
)
# Every `TF_VAR_*` input, and `TF_CLI_ARGS` plus each `TF_CLI_ARGS_<cmd>`.
SCRUBBED_PREFIXES = ("TF_VAR_", "TF_CLI_ARGS")
SCRUBBED_NAMES = (
    # Select another state or move `.terraform` away from the workspace.
    "TF_WORKSPACE",
    "TF_DATA_DIR",
    # Credentials that outrank GOOGLE_APPLICATION_CREDENTIALS.
    "GOOGLE_OAUTH_ACCESS_TOKEN",
    "GOOGLE_CREDENTIALS",
    "GOOGLE_CLOUD_KEYFILE_JSON",
    "GCLOUD_KEYFILE_JSON",
    "GOOGLE_BACKEND_CREDENTIALS",
    # Quota settings that the remote providers file leaves to the stage.
    "GOOGLE_BILLING_PROJECT",
    "USER_PROJECT_OVERRIDE",
    # Backend settings that would encrypt the state with a foreign key or
    # send it to another endpoint during a state migration.
    "GOOGLE_ENCRYPTION_KEY",
    "GOOGLE_KMS_ENCRYPTION_KEY",
    "GOOGLE_BACKEND_STORAGE_CUSTOM_ENDPOINT",
    *IMPERSONATION_ENV_VARS,
    "GOOGLE_BACKEND_IMPERSONATE_SERVICE_ACCOUNT",
)
# Set in every child environment; the values override the parent's.
AUTOMATION_VARS = {"TF_IN_AUTOMATION": "1", "TF_INPUT": "0"}
CREDENTIALS_VAR = "GOOGLE_APPLICATION_CREDENTIALS"
CLOUDSDK_CONFIG_VAR = "CLOUDSDK_CONFIG"
ADC_FILENAME = "application_default_credentials.json"
# Kept file paths that Terraform would resolve against the workspace under
# `-chdir`, while preflight resolved them against the current directory.
_PATH_VARS = (CREDENTIALS_VAR, "TF_CLI_CONFIG_FILE")
# Kept variables whose names the log header and run-state record.
_RECORDED_PREFIXES = ("TF_", "GOOGLE_", "GCLOUD_", "CLOUDSDK_")


@dataclasses.dataclass(frozen=True)
class ChildEnv:
    """The environment of a Terraform process and how it was built.

    Attributes:
        env: Variables of the child process.
        scrubbed: Sorted names removed from the parent environment.
        kept: Sorted names of the Terraform and Google variables that the
            child environment carries, including the ones set here.
        problems: Reasons the child would run as another identity than
            preflight checked; empty when Terraform may run.
        pinned: The variable set from `CLOUDSDK_CONFIG`, or None.
    """

    env: Mapping[str, str]
    scrubbed: tuple[str, ...]
    kept: tuple[str, ...]
    problems: tuple[str, ...]
    pinned: str | None = None

    def header(self) -> list[str]:
        """Returns log header lines that name variables, never values."""
        lines = [
            "scrubbed environment variables: "
            + (", ".join(self.scrubbed) or "none"),
            "kept environment variables: " + (", ".join(self.kept) or "none"),
        ]
        if self.pinned:
            lines.append(
                f"{self.pinned} set to ${CLOUDSDK_CONFIG_VAR}/{ADC_FILENAME}"
            )
        lines.extend(f"problem: {problem}" for problem in self.problems)
        return lines


def is_scrubbed(name: str) -> bool:
    """Returns whether `build_env` removes a variable.

    Args:
        name: Environment variable name.
    """
    return name in SCRUBBED_NAMES or name.startswith(SCRUBBED_PREFIXES)


def build_env(environ: Mapping[str, str]) -> ChildEnv:
    """Returns the environment of the Terraform processes.

    The google provider and the GCS backend ignore `CLOUDSDK_CONFIG`, while
    the Python client libraries that preflight uses honor it. When only
    `CLOUDSDK_CONFIG` is set, the child therefore gets
    `GOOGLE_APPLICATION_CREDENTIALS` pointing at the application default
    credentials inside it, so Terraform runs as the identity that preflight
    checked. Relative credential and CLI configuration paths become
    absolute, because `-chdir` would resolve them against the workspace.

    Args:
        environ: The parent environment; it is not modified.

    Returns:
        The child environment with the names it scrubbed and kept.
    """
    env = {
        name: value for name, value in environ.items() if not is_scrubbed(name)
    }
    scrubbed = sorted(name for name in environ if is_scrubbed(name))
    env.update(AUTOMATION_VARS)
    problems = []
    pinned = None
    config = environ.get(CLOUDSDK_CONFIG_VAR)
    if config and not environ.get(CREDENTIALS_VAR):
        credentials = pathlib.Path(config) / ADC_FILENAME
        if credentials.is_file():
            env[CREDENTIALS_VAR] = str(credentials)
            pinned = CREDENTIALS_VAR
        else:
            problems.append(
                f"{CLOUDSDK_CONFIG_VAR} is set without {CREDENTIALS_VAR}, "
                f"and ${CLOUDSDK_CONFIG_VAR}/{ADC_FILENAME} does not exist, "
                "so Terraform would use other credentials than gcloud and "
                "preflight. Run `gcloud auth application-default login` "
                f"with this {CLOUDSDK_CONFIG_VAR}, or set {CREDENTIALS_VAR}."
            )
    for name in _PATH_VARS:
        if env.get(name):
            env[name] = os.path.abspath(env[name])
    kept = sorted(name for name in env if name.startswith(_RECORDED_PREFIXES))
    return ChildEnv(
        env=env,
        scrubbed=tuple(scrubbed),
        kept=tuple(kept),
        problems=tuple(problems),
        pinned=pinned,
    )
