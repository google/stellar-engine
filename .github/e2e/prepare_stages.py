#!/usr/bin/env python3
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

"""Prepares Stage 0-3 E2E workspaces and enforces folder-scoped org flags."""

import argparse
from collections.abc import Mapping, Sequence
import json
import pathlib
import re
import sys
from typing import Any

from stellar_engine import paths
from stellar_engine import repo as repo_lib
from stellar_engine import workspace as workspace_lib
from stellar_engine.config import answers as answers_lib
from stellar_engine.config import models
from stellar_engine.render import hcl
from stellar_engine.render import sample as sample_lib

_NET_OUTPUT_LINKS = (
    "providers/2-networking-providers.tf",
    "tfvars/0-globals.auto.tfvars.json",
    "tfvars/0-bootstrap.auto.tfvars.json",
    "tfvars/1-resman.auto.tfvars.json",
)
_SEC_OUTPUT_LINKS = (
    "providers/3-security-providers.tf",
    "tfvars/0-globals.auto.tfvars.json",
    "tfvars/0-bootstrap.auto.tfvars.json",
    "tfvars/1-resman.auto.tfvars.json",
)
_VALID_NET_STAGES = frozenset(
    {"2-networking-a-fedramp", "2-networking-b-il5-ngfw"}
)
_OBJECT_ATTR_RE = re.compile(r"([A-Za-z_][A-Za-z0-9_-]*)\s*=")


def _declared_org_resource_keys(engine_root: pathlib.Path) -> list[str]:
    keys: set[str] = set()
    for stage in (paths.BOOTSTRAP, paths.RESMAN):
        vars_path = engine_root / paths.STAGES_DIR / stage / "variables.tf"
        declared = repo_lib._variables(vars_path)
        block = declared.get("deploy_org_resources")
        if not block or "type" not in block:
            raise ValueError(
                f"Missing deploy_org_resources variable in {vars_path}"
            )
        keys.update(_OBJECT_ATTR_RE.findall(str(block["type"])))
    if not keys:
        raise ValueError(
            "Could not parse any attributes from deploy_org_resources"
        )
    return sorted(keys)


def _assert_all_org_flags_false(
    flags: Any, expected_keys: Sequence[str], source: pathlib.Path
) -> None:
    if not isinstance(flags, Mapping):
        raise ValueError(
            f"Missing deploy_org_resources map in {source}: {flags!r}"
        )
    bad = [key for key in expected_keys if flags.get(key) is not False]
    extra_true = [
        key
        for key, val in flags.items()
        if key not in expected_keys and val is not False
    ]
    problems = sorted(set(bad + extra_true))
    if problems:
        raise ValueError(
            f"deploy_org_resources must be false for every key in {source}; "
            f"non-false keys: {', '.join(problems)}"
        )


def _replace_region(value: Any, region: str) -> Any:
    if isinstance(value, str):
        return region if value == "<region>" else value
    if isinstance(value, Mapping):
        return {k: _replace_region(v, region) for k, v in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, bytes):
        return [_replace_region(item, region) for item in value]
    return value


def _bootstrap_providers_hcl(prefix: str, *, remote_state: bool) -> str:
    blocks: list[str] = []
    if remote_state:
        bucket = f"{prefix}-prod-iac-core-bootstrap-0"
        blocks.append(
            "terraform {\n"
            '  backend "gcs" {\n'
            f'    bucket = "{bucket}"\n'
            "  }\n"
            "}"
        )
    for provider_name in ("google", "google-beta"):
        blocks.append(
            f'provider "{provider_name}" {{\n'
            "  project               = var.bootstrap_project\n"
            "  billing_project       = var.bootstrap_project\n"
            "  user_project_override = true\n"
            "}"
        )
    return "\n\n".join(blocks) + "\n"


def _sync_stage_workspace(
    env: paths.EnvPaths,
    engine_root: pathlib.Path,
    stage: str,
    output_links: tuple[str, ...],
) -> pathlib.Path:
    stage_dir = engine_root / paths.STAGES_DIR / stage
    if not stage_dir.is_dir():
        raise workspace_lib.WorkspaceError(
            f"The engine has no stage directory {stage_dir}"
        )
    workspace_dir = env.stages_dir / stage
    report = workspace_lib.SyncReport(stage, workspace_dir)
    env.ensure()
    paths.make_private_dir(workspace_dir)
    workspace_lib._ensure_link(env.modules_link, engine_root / "modules")
    workspace_lib._sync_engine_links(
        workspace_dir, stage_dir, env.fast_config, report
    )
    workspace_lib._sync_output_links(
        workspace_dir, env.fast_config, output_links, report
    )
    if report.pending:
        missing = ", ".join(report.pending)
        raise workspace_lib.WorkspaceError(
            f"Missing upstream stage outputs for {stage}: {missing}"
        )
    return workspace_dir


def _render_networking_tfvars(
    answers: models.Answers,
    env: paths.EnvPaths,
    stage_dir: pathlib.Path,
) -> str:
    sample = sample_lib.load(stage_dir / "terraform.tfvars.sample")
    values: dict[str, Any] = _replace_region(sample.values, answers.region)

    if "subnets" in values and isinstance(values["subnets"], dict):
        tenants = set(answers.resman.tenants)
        filtered_subnets: dict[str, list[dict[str, Any]]] = {}
        for net_key, subnet_list in values["subnets"].items():
            filtered_subnets[net_key] = [
                subnet
                for subnet in subnet_list
                if subnet.get("tenant") is None
                or subnet.get("tenant") in tenants
            ]
        values["subnets"] = filtered_subnets

    if "proxy_subnets" in values and isinstance(values["proxy_subnets"], dict):
        values["proxy_subnets"] = {
            env_key: cidr
            for env_key, cidr in values["proxy_subnets"].items()
            if env_key in answers.resman.envs
        }

    values["outputs_location"] = str(env.fast_config)
    if answers.billing_override is not None:
        values["billing_override"] = {
            "project": answers.billing_override.project,
            "billing_project": answers.billing_override.billing_project,
        }

    declared_vars = repo_lib._variables(stage_dir / "variables.tf")
    if "force_destroy" in declared_vars:
        values["force_destroy"] = True

    return hcl.dumps(values)


def _render_security_tfvars(
    answers: models.Answers,
    env: paths.EnvPaths,
) -> str:
    values: dict[str, Any] = {
        "kms_keys": {
            "default": {
                "rotation_period": "7776000s",
                "labels": {"environment": "security"},
                "locations": [answers.region],
            }
        },
        "vpc_sc": {
            "resource_discovery": {
                "enabled": False,
            }
        },
        "outputs_location": str(env.fast_config),
    }
    if answers.billing_override is not None:
        values["billing_override"] = {
            "project": answers.billing_override.project,
            "billing_project": answers.billing_override.billing_project,
        }
    return hcl.dumps(values)


def _cmd_prepare_answers(args: argparse.Namespace) -> int:
    engine_root = args.repo.expanduser().resolve()
    home = paths.Home(args.home.expanduser().resolve())
    raw = answers_lib.load_data(args.file)
    plain_data = answers_lib.plain(raw)
    if not isinstance(plain_data, dict):
        raise ValueError(f"{args.file} must contain a YAML mapping")

    org_keys = _declared_org_resource_keys(engine_root)
    overrides = dict(plain_data.get("overrides") or {})
    boot_overrides = dict(overrides.get(paths.BOOTSTRAP) or {})
    existing_flags = dict(boot_overrides.get("deploy_org_resources") or {})
    for key in set(existing_flags) | set(org_keys):
        existing_flags[key] = False
    boot_overrides["deploy_org_resources"] = dict(
        sorted(existing_flags.items())
    )
    overrides[paths.BOOTSTRAP] = boot_overrides
    plain_data["overrides"] = overrides

    answers = answers_lib.parse(plain_data, str(args.file))
    env = home.env(answers.prefix)
    home.ensure()
    env.ensure()
    answers_lib.save(env.answers, answers, home=home.root, previous=raw)
    print(answers.prefix)
    return 0


def _cmd_bootstrap_providers(args: argparse.Namespace) -> int:
    engine_root = args.repo.expanduser().resolve()
    home = paths.Home(args.home.expanduser().resolve())
    env = home.env(args.prefix)
    stage0_dir = env.workspace(paths.BOOTSTRAP)
    paths.make_private_dir(stage0_dir)

    tfvars_path = stage0_dir / "terraform.tfvars"
    if not tfvars_path.is_file():
        raise ValueError(f"Expected rendered Stage 0 tfvars at {tfvars_path}")
    stage0_tfvars = hcl.loads(tfvars_path.read_text(encoding="utf-8"))
    org_keys = _declared_org_resource_keys(engine_root)
    _assert_all_org_flags_false(
        stage0_tfvars.get("deploy_org_resources"), org_keys, tfvars_path
    )

    remote_state = args.remote_state == "true"
    target = stage0_dir / workspace_lib.BOOTSTRAP_PROVIDERS
    target.write_text(
        _bootstrap_providers_hcl(args.prefix, remote_state=remote_state),
        encoding="utf-8",
    )
    return 0


def _cmd_verify_stage0_outputs(args: argparse.Namespace) -> int:
    engine_root = args.repo.expanduser().resolve()
    home = paths.Home(args.home.expanduser().resolve())
    env = home.env(args.prefix)
    auto_tfvars = env.fast_config / "tfvars/0-bootstrap.auto.tfvars.json"
    if not auto_tfvars.is_file():
        raise ValueError(f"Missing Stage 0 output file {auto_tfvars}")
    payload = json.loads(auto_tfvars.read_text(encoding="utf-8"))
    org_keys = _declared_org_resource_keys(engine_root)
    _assert_all_org_flags_false(
        payload.get("deploy_org_resources"), org_keys, auto_tfvars
    )
    return 0


def _cmd_later_stages(args: argparse.Namespace) -> int:
    if args.net_stage not in _VALID_NET_STAGES:
        raise ValueError(f"Unsupported networking stage: {args.net_stage!r}")
    home = paths.Home(args.home.expanduser().resolve())
    engine_root = args.repo.expanduser().resolve()
    env = home.env(args.prefix)
    answers = answers_lib.load(env.answers)

    _cmd_verify_stage0_outputs(args)

    net_ws = _sync_stage_workspace(
        env, engine_root, args.net_stage, _NET_OUTPUT_LINKS
    )
    net_stage_dir = engine_root / paths.STAGES_DIR / args.net_stage
    (net_ws / "terraform.tfvars").write_text(
        _render_networking_tfvars(answers, env, net_stage_dir),
        encoding="utf-8",
    )

    sec_ws = _sync_stage_workspace(
        env, engine_root, "3-security", _SEC_OUTPUT_LINKS
    )
    (sec_ws / "terraform.tfvars").write_text(
        _render_security_tfvars(answers, env),
        encoding="utf-8",
    )
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Prepare Stellar Engine Stage 0-3 E2E workspaces."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    prep = sub.add_parser("prepare-answers")
    prep.add_argument("--file", type=pathlib.Path, required=True)
    prep.add_argument("--repo", type=pathlib.Path, required=True)
    prep.add_argument("--home", type=pathlib.Path, required=True)
    prep.set_defaults(handler=_cmd_prepare_answers)

    boot = sub.add_parser("bootstrap-providers")
    boot.add_argument("--home", type=pathlib.Path, required=True)
    boot.add_argument("--repo", type=pathlib.Path, required=True)
    boot.add_argument("--prefix", required=True)
    boot.add_argument(
        "--remote-state", choices=("true", "false"), required=True
    )
    boot.set_defaults(handler=_cmd_bootstrap_providers)

    verify = sub.add_parser("verify-stage0-outputs")
    verify.add_argument("--home", type=pathlib.Path, required=True)
    verify.add_argument("--repo", type=pathlib.Path, required=True)
    verify.add_argument("--prefix", required=True)
    verify.set_defaults(handler=_cmd_verify_stage0_outputs)

    later = sub.add_parser("later-stages")
    later.add_argument("--home", type=pathlib.Path, required=True)
    later.add_argument("--repo", type=pathlib.Path, required=True)
    later.add_argument("--prefix", required=True)
    later.add_argument("--net-stage", required=True)
    later.set_defaults(handler=_cmd_later_stages)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Runs the CLI command and returns its exit status."""
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        return args.handler(args)
    except (
        ValueError,
        answers_lib.AnswersError,
        workspace_lib.WorkspaceError,
    ) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
