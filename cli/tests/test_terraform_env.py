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

"""Tests for the environment of the Terraform processes."""

import os
import pathlib
import re

import pytest

import conftest
from stellar_engine.preflight import checks
from stellar_engine.terraform import env as env_lib

SECRET = "s3cr3t-value"
# A gcloud configuration directory that does not exist.
CONFIG = pathlib.Path("/home/operator/gcloud")
# The line of `fast/stage-links.sh` that tells the operator what to unset.
_UNSET_RE = re.compile(r'^\s*echo "unset ([A-Z_ ]+)"$', re.MULTILINE)


def _build(environ):
    return env_lib.build_env(environ)


@pytest.fixture
def config(tmp_path):
    """Returns a gcloud configuration directory with credentials in it."""
    (tmp_path / env_lib.ADC_FILENAME).write_text("{}", encoding="utf-8")
    return tmp_path


@pytest.mark.parametrize("name", env_lib.SCRUBBED_NAMES)
def test_scrubs_each_name(name):
    child = _build({name: SECRET, "PATH": "/usr/bin"})
    assert name not in child.env
    assert child.scrubbed == (name,)
    assert child.env["PATH"] == "/usr/bin"


@pytest.mark.parametrize(
    "name",
    [
        "TF_VAR_bootstrap_user",
        "TF_VAR_billing_override",
        "TF_CLI_ARGS",
        "TF_CLI_ARGS_plan",
        "TF_CLI_ARGS_apply",
        "TF_CLI_ARGS_init",
    ],
)
def test_scrubs_each_prefix(name):
    child = _build({name: SECRET})
    assert name not in child.env
    assert child.scrubbed == (name,)


@pytest.mark.parametrize(
    "name",
    [
        "PATH",
        "HOME",
        "GOOGLE_APPLICATION_CREDENTIALS",
        "GOOGLE_CLOUD_QUOTA_PROJECT",
        "CLOUDSDK_CONFIG",
        "TF_PLUGIN_CACHE_DIR",
        "TF_CLI_CONFIG_FILE",
        "TF_LOG",
    ],
)
def test_keeps_other_names(name):
    child = _build({name: "/kept"})
    assert child.env[name] == "/kept"
    assert child.scrubbed == ()


def test_kept_lists_terraform_and_google_names_only():
    child = _build(
        {
            "PATH": "/usr/bin",
            "HOME": "/home/operator",
            "GOOGLE_APPLICATION_CREDENTIALS": "/keys/sa.json",
            "GOOGLE_CLOUD_QUOTA_PROJECT": "my-project",
            "TF_PLUGIN_CACHE_DIR": "/cache",
            "TF_VAR_prefix": "abc",
        }
    )
    assert child.kept == (
        "GOOGLE_APPLICATION_CREDENTIALS",
        "GOOGLE_CLOUD_QUOTA_PROJECT",
        "TF_INPUT",
        "TF_IN_AUTOMATION",
        "TF_PLUGIN_CACHE_DIR",
    )


def test_sets_the_automation_variables_over_the_parent():
    child = _build({"TF_INPUT": "1", "TF_IN_AUTOMATION": ""})
    assert child.env["TF_INPUT"] == "0"
    assert child.env["TF_IN_AUTOMATION"] == "1"


def test_leaves_the_parent_environment_unchanged():
    environ = {"TF_VAR_x": SECRET, "CLOUDSDK_CONFIG": str(CONFIG)}
    _build(environ)
    assert environ == {"TF_VAR_x": SECRET, "CLOUDSDK_CONFIG": str(CONFIG)}


@pytest.mark.parametrize("credentials", [None, ""])
def test_pins_credentials_to_the_cloudsdk_config(credentials, config):
    environ = {"CLOUDSDK_CONFIG": str(config)}
    if credentials is not None:
        environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials
    child = _build(environ)
    assert child.env["GOOGLE_APPLICATION_CREDENTIALS"] == str(
        config / env_lib.ADC_FILENAME
    )
    assert child.pinned == "GOOGLE_APPLICATION_CREDENTIALS"
    assert child.problems == ()


def test_missing_cloudsdk_credentials_are_a_problem():
    child = _build({"CLOUDSDK_CONFIG": str(CONFIG)})
    assert "GOOGLE_APPLICATION_CREDENTIALS" not in child.env
    assert child.pinned is None
    (problem,) = child.problems
    assert f"$CLOUDSDK_CONFIG/{env_lib.ADC_FILENAME} does not exist" in problem
    assert "gcloud auth application-default login" in problem


def test_explicit_credentials_are_never_replaced(config):
    child = _build(
        {
            "CLOUDSDK_CONFIG": str(config),
            "GOOGLE_APPLICATION_CREDENTIALS": "/keys/sa.json",
        }
    )
    assert child.env["GOOGLE_APPLICATION_CREDENTIALS"] == "/keys/sa.json"
    assert child.pinned is None
    assert child.problems == ()


def test_no_cloudsdk_config_needs_no_credentials():
    child = _build({"PATH": "/usr/bin"})
    assert "GOOGLE_APPLICATION_CREDENTIALS" not in child.env
    assert child.problems == ()


def test_relative_paths_become_absolute(monkeypatch, config):
    monkeypatch.chdir(config.parent)
    child = _build(
        {
            "GOOGLE_APPLICATION_CREDENTIALS": "keys/sa.json",
            "TF_CLI_CONFIG_FILE": "terraform.rc",
        }
    )
    assert child.env["GOOGLE_APPLICATION_CREDENTIALS"] == os.path.join(
        os.getcwd(), "keys/sa.json"
    )
    assert child.env["TF_CLI_CONFIG_FILE"] == os.path.join(
        os.getcwd(), "terraform.rc"
    )


def test_a_relative_cloudsdk_config_pins_an_absolute_path(monkeypatch, config):
    monkeypatch.chdir(config.parent)
    child = _build({"CLOUDSDK_CONFIG": config.name})
    assert child.env["GOOGLE_APPLICATION_CREDENTIALS"] == os.path.join(
        os.getcwd(), config.name, env_lib.ADC_FILENAME
    )


def test_header_names_variables_never_values():
    environ: dict[str, str] = dict.fromkeys(env_lib.SCRUBBED_NAMES, SECRET)
    environ.update(
        {
            "TF_VAR_bootstrap_user": SECRET,
            "GOOGLE_CLOUD_QUOTA_PROJECT": SECRET,
            "CLOUDSDK_CONFIG": SECRET,
        }
    )
    child = _build(environ)
    header = "\n".join(child.header())
    assert SECRET not in header
    assert "TF_VAR_bootstrap_user" in header
    assert "GOOGLE_CLOUD_QUOTA_PROJECT" in header
    assert "problem: CLOUDSDK_CONFIG is set" in header


def test_header_without_variables():
    assert _build({}).header() == [
        "scrubbed environment variables: none",
        "kept environment variables: TF_INPUT, TF_IN_AUTOMATION",
    ]


def test_impersonation_names_match_stage_links_script():
    script = conftest.REPO_ROOT / "fast/stage-links.sh"
    (unset,) = _UNSET_RE.findall(script.read_text(encoding="utf-8"))
    assert tuple(unset.split()) == env_lib.IMPERSONATION_ENV_VARS


def test_preflight_shares_the_impersonation_names():
    assert checks.IMPERSONATION_ENV_VARS is env_lib.IMPERSONATION_ENV_VARS


def test_backend_impersonation_is_scrubbed_too():
    assert env_lib.is_scrubbed("GOOGLE_BACKEND_IMPERSONATE_SERVICE_ACCOUNT")
    assert not env_lib.is_scrubbed("GOOGLE_APPLICATION_CREDENTIALS")
