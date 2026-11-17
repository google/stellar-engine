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

"""Answer data, answer fixtures, command and Terraform helpers for tests.

`minimal_data` and `minimal_answers` build the smallest valid answers from
placeholder values. `fixture_data` and `load_fixture` read the per-regime
answer files under `fixtures/answers`, which the render snapshots use.
`init_env` creates an environment from `REQUIRED_SETS`, and `invoke` runs
any `stellar` command against the checkout under test.
"""

import json
import pathlib
import re
import shutil
import subprocess

import yaml

import conftest
from stellar_engine import cli
from stellar_engine import paths
from stellar_engine.config import answers as answers_lib
from stellar_engine.config import models
from stellar_engine.deploy import run_state as run_state_lib
from stellar_engine.render import stages

FIXTURES = pathlib.Path(__file__).resolve().parent / "fixtures"
ANSWERS_DIR = FIXTURES / "answers"
STAGE_OUTPUTS_DIR = FIXTURES / "stage-outputs"
# Hand-built `terraform show -json` documents with placeholder values.
PLANS_DIR = FIXTURES / "plans"
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


def _assignments(data, path=""):
    """Yields a `key=value` assignment for each leaf of nested data."""
    for key, value in data.items():
        if isinstance(value, dict):
            yield from _assignments(value, f"{path}{key}.")
        else:
            yield f"{path}{key}={value}"


def _required_sets():
    """Returns `minimal_data` as `init --set` assignments.

    The prefix stays out: `init` takes it from `--prefix` or from the
    current environment.
    """
    data = minimal_data()
    del data["prefix"]
    return tuple(_assignments(data))


# Answers for a complete IL5 environment, as `init --set` assignments.
REQUIRED_SETS = _required_sets()


def minimal_answers(**overrides):
    """Returns `minimal_data` validated by the answers model."""
    return models.Answers.model_validate(minimal_data(**overrides))


def fixture_data(name):
    """Returns the raw answer data of a fixture."""
    path = ANSWERS_DIR / f"{name}.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def plan_fixture(name):
    """Returns the document of a plan fixture under `fixtures/plans`."""
    path = PLANS_DIR / f"{name}.json"
    return json.loads(path.read_text(encoding="utf-8"))


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


def set_args(*assignments):
    """Returns `--set` arguments for REQUIRED_SETS and more assignments."""
    args = []
    for assignment in [*REQUIRED_SETS, *assignments]:
        args += ["--set", assignment]
    return args


def init_env(runner, prefix: str | None = "tst", *extra, sets=()):
    """Runs a non-interactive `stellar init` with the required answers.

    Args:
        runner: The CliRunner.
        prefix: The `--prefix` value; None leaves the flag out.
        *extra: More `init` arguments.
        sets: More `--set` assignments after REQUIRED_SETS.

    Returns:
        The CliRunner result.
    """
    args = [
        "init",
        "--non-interactive",
        "--repo",
        str(conftest.REPO_ROOT),
        *(["--prefix", prefix] if prefix else []),
        *set_args(*sets),
        *extra,
    ]
    return runner.invoke(cli.app, args)


def invoke(runner, *args, **kwargs):
    """Runs a `stellar` command against the checkout under test.

    Args:
        runner: The CliRunner.
        *args: The command line, without `--repo`.
        **kwargs: Passed to `CliRunner.invoke`, such as `input`.
    """
    return runner.invoke(
        cli.app, [*args, "--repo", str(conftest.REPO_ROOT)], **kwargs
    )


def _slug(heading):
    """Returns the anchor GitHub gives a Markdown heading."""
    return re.sub(r"[^\w\- ]", "", heading.strip().lower()).replace(" ", "-")


def doc_resolves(doc):
    """Returns whether a `path#anchor` link names a heading of the file.

    Args:
        doc: A repository-relative link, such as `docs/ddg.md#variables`.
    """
    path, anchor = doc.split("#")
    text = (conftest.REPO_ROOT / path).read_text(encoding="utf-8")
    return anchor in {
        _slug(line.lstrip("#"))
        for line in text.splitlines()
        if line.startswith("#")
    }


def env(home, prefix="tst"):
    """Returns the EnvPaths of an environment in a home."""
    return paths.Home(home).env(prefix)


def run_state(home, prefix="tst"):
    """Returns the saved run-state of an environment in a home."""
    return run_state_lib.load(env(home, prefix))


def load_answers(home, prefix="tst"):
    """Returns the saved answers of an environment in a home."""
    return answers_lib.load(home / "envs" / prefix / "answers.yaml")


def workspace(home, stage, prefix="tst"):
    """Returns the workspace of a stage in an environment of a home."""
    return paths.stage_dir(home / "envs" / prefix, stage)


def engine_copy(root):
    """Links the repository's top-level entries into a fresh engine root.

    The default home lives inside the engine checkout, so a test that uses
    it needs a checkout it may write into.

    Args:
        root: Directory that receives the `engine` folder.

    Returns:
        The engine root.
    """
    engine = root / "engine"
    engine.mkdir()
    for entry in conftest.REPO_ROOT.iterdir():
        if entry.name not in (".git", ".stellar"):
            (engine / entry.name).symlink_to(entry)
    return engine


def module_manifest(workspace, modules_dir):
    """Writes the module manifest that `terraform init` leaves in a workspace.

    The records follow Terraform: the root, a local module of the stage
    resolved through the `modules` link, a local module that it calls,
    and a registry module under `.terraform/`.

    Args:
        workspace: The stage workspace.
        modules_dir: The resolved `modules` directory that init saw.

    Returns:
        The manifest path.
    """
    manifest = workspace / ".terraform" / "modules" / "modules.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    records = [
        {"Key": "", "Source": "", "Dir": "."},
        {
            "Key": "automation-project",
            "Source": "../../../modules/project",
            "Dir": str(modules_dir / "project"),
        },
        {
            "Key": "automation-project.iam",
            "Source": "../iam-service-account",
            "Dir": str(modules_dir / "iam-service-account"),
        },
        {
            "Key": "dns",
            "Source": "registry.terraform.io/example/dns/google",
            "Version": "1.0.0",
            "Dir": ".terraform/modules/dns",
        },
    ]
    manifest.write_text(json.dumps({"Modules": records}))
    return manifest


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


def terraform_init(directory, env=None):
    """Runs `terraform init` without a backend and asserts that it passes.

    Args:
        directory: The Terraform root module.
        env: Environment of the terraform process; None inherits it.

    Returns:
        The completed process.
    """
    completed = terraform(
        directory, "init", "-backend=false", "-input=false", env=env
    )
    assert completed.returncode == 0, completed.stderr
    return completed


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
