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

"""Answer data, answer fixtures and Terraform helpers shared by the tests.

`minimal_data` and `minimal_answers` build the smallest valid answers from
placeholder values. `fixture_data` and `load_fixture` read the per-regime
answer files under `fixtures/answers`, which the render snapshots use.
"""

import pathlib
import re
import shutil
import subprocess

import yaml

import conftest
from stellar_engine import paths
from stellar_engine.config import models
from stellar_engine.render import stages

FIXTURES = pathlib.Path(__file__).resolve().parent / "fixtures"
ANSWERS_DIR = FIXTURES / "answers"
STAGE_OUTPUTS_DIR = FIXTURES / "stage-outputs"
# One fixture per regime plus the lab-shaped case with imports.
REGIME_FIXTURES = (
    "fedramp_high",
    "fedramp_moderate",
    "il4",
    "il5",
    "unspecified",
)
ALL_FIXTURES = (*REGIME_FIXTURES, "lab")
# A fixed home keeps `outputs_location` stable across snapshot runs.
SNAPSHOT_HOME = pathlib.Path("/home/operator/.stellar")
_TERRAFORM_TIMEOUT_SECONDS = 600
# Where the bootstrap-deletion-policy Stage 0 change wires its variable, as
# file, module label and `project_deletion_policies` key.
_DELETION_POLICY_MODULES = (
    ("automation.tf", "automation-project", "automation"),
    ("log-export.tf", "log-export-project", "logging"),
    ("billing.tf", "billing-export-project", "billing"),
)
_DELETION_POLICY_VARIABLE = """
variable "project_deletion_policies" {
  description = "Deletion policy of each Stage 0 project."
  type = object({
    automation = optional(string, "DELETE")
    billing    = optional(string, "DELETE")
    logging    = optional(string, "DELETE")
  })
  nullable = false
  default  = {}
}
"""
# The variable block up to its closing brace at column 0.
_DELETION_POLICY_VARIABLE_RE = re.compile(
    r'^variable "project_deletion_policies" \{\n.*?^\}\n',
    re.DOTALL | re.MULTILINE,
)
_DELETION_POLICY_USE_RE = re.compile(
    r"^ *deletion_policy *= *var\.project_deletion_policies\.\w+\n",
    re.MULTILINE,
)


def minimal_data(**overrides):
    """Returns minimal valid answer data with placeholder values."""
    data = {
        "prefix": "tst",
        "organization": {
            "id": conftest.ORG_ID,
            "domain": conftest.DOMAIN,
            "customer_id": conftest.CUSTOMER_ID,
        },
        "billing": {"account_id": conftest.BILLING},
        "bootstrap_project": conftest.PROJECT,
        "region": "us-east4",
        "compliance": {"regime": "IL5"},
        "alert_email": f"alerts@{conftest.DOMAIN}",
        # The default bootstrap phase requires the bootstrap user.
        "bootstrap_user": f"admin@{conftest.DOMAIN}",
    }
    data.update(overrides)
    return data


def minimal_answers(**overrides):
    """Returns `minimal_data` validated by the answers model."""
    return models.Answers.model_validate(minimal_data(**overrides))


def fixture_data(name):
    """Returns the raw answer data of a fixture."""
    path = ANSWERS_DIR / f"{name}.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_fixture(name, **updates):
    """Returns the validated answers of a fixture with top-level updates."""
    data = fixture_data(name)
    data.update(updates)
    return models.Answers.model_validate(data)


def env_paths(answers, home=SNAPSHOT_HOME):
    """Returns the EnvPaths of the answers' prefix under a home."""
    return paths.EnvPaths(home / "envs" / answers.prefix, answers.prefix)


def render(repo, name, stage, **updates):
    """Renders a stage from a fixture with top-level updates."""
    answers = load_fixture(name, **updates)
    return stages.build(stage, answers, repo, env_paths(answers))


def terraform(directory, *args, env=None, stdin=None):
    """Runs terraform in a directory and returns the completed process."""
    return subprocess.run(
        ["terraform", f"-chdir={directory}", *args, "-no-color"],
        input=stdin,
        capture_output=True,
        check=False,
        env=env,
        text=True,
        timeout=_TERRAFORM_TIMEOUT_SECONDS,
    )


def terraform_fmt(text):
    """Runs `terraform fmt -` on text and returns the completed process."""
    return subprocess.run(
        ["terraform", "fmt", "-"],
        input=text,
        capture_output=True,
        check=False,
        text=True,
        timeout=_TERRAFORM_TIMEOUT_SECONDS,
    )


def deletion_policy_engine(root, *, declared=True):
    """Builds an engine tree with or without project_deletion_policies.

    The tree copies the Stage 0 code, the Stage 1 variables and the
    `modules/project` files of the checkout under test. With `declared`,
    the tree wires the variable into each Stage 0 project module the way
    the Stage 0 change that adds it does, unless the checkout already
    has it. Without `declared`, the tree drops the variable and its uses,
    so the tests cover both engine versions whichever one the checkout is.

    Args:
        root: Empty directory for the engine tree.
        declared: Whether Stage 0 declares project_deletion_policies.

    Returns:
        The engine root.
    """
    source = conftest.REPO_ROOT
    bootstrap = paths.stage_dir(root, paths.BOOTSTRAP)
    shutil.copytree(
        paths.stage_dir(source, paths.BOOTSTRAP),
        bootstrap,
        symlinks=True,
        ignore=shutil.ignore_patterns(".terraform*", "terraform.tfstate*"),
    )
    resman = paths.stage_dir(root, paths.RESMAN)
    resman.mkdir(parents=True)
    shutil.copy2(paths.stage_dir(source, paths.RESMAN) / "variables.tf", resman)
    (root / "modules/project").mkdir(parents=True)
    for name in ("main.tf", "variables.tf"):
        shutil.copy2(
            source / "modules/project" / name, root / "modules/project"
        )
    variables = bootstrap / "variables.tf"
    text = variables.read_text(encoding="utf-8")
    present = _DELETION_POLICY_VARIABLE_RE.search(text) is not None
    if declared == present:
        return root
    if declared:
        variables.write_text(text + _DELETION_POLICY_VARIABLE, encoding="utf-8")
    else:
        variables.write_text(
            _DELETION_POLICY_VARIABLE_RE.sub("", text), encoding="utf-8"
        )
    for filename, module, key in _DELETION_POLICY_MODULES:
        path = bootstrap / filename
        text = path.read_text(encoding="utf-8")
        opening = f'module "{module}" {{\n'
        assert opening in text, f"{filename} has no module {module}"
        if declared:
            text = text.replace(
                opening,
                f"{opening}  deletion_policy = "
                f"var.project_deletion_policies.{key}\n",
            )
        else:
            text = _DELETION_POLICY_USE_RE.sub("", text)
        path.write_text(text, encoding="utf-8")
    return root
