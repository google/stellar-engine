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

"""Tests for the Google Cloud changes that deploy steps make."""

import dataclasses
import json

import pytest

import conftest
import helpers
import helpers_deploy
from stellar_engine import iam_diff
from stellar_engine import repo as repo_lib
from stellar_engine.deploy import cloud_ops
from stellar_engine.deploy import model
from stellar_engine.deploy import probe as probe_lib
from stellar_engine.gcp import api
from stellar_engine.preflight import checks
from stellar_engine.wizard import prompts

_FOLDER = "folders/123456789012"
_SA_EMAIL = "deployer@my-project.iam.gserviceaccount.com"
_ROLES = repo_lib.Repo(conftest.REPO_ROOT).required_roles()
_ORG_ROLES = [role for role in _ROLES if role != checks.BILLING_ADMIN_ROLE]


def _ctx(tmp_path, replies=(), **kwargs):
    prompter = prompts.ScriptedPrompter(list(replies))
    return helpers_deploy.make_ctx(tmp_path, prompter=prompter, **kwargs)


def _members(cloud, role):
    policy = iam_diff.Policy.from_json(cloud.policy)
    return policy.bindings.get(iam_diff.BindingKey(role), frozenset())


def _lacking(*roles, **kwargs):
    """Returns a FakeCloud on which preflight finds these roles missing.

    Without roles, every organization role of `setIAM.yaml.sample` is
    missing. Preflight tests Billing Account Administrator on the billing
    account, so that role passes.
    """
    roles = roles or _ORG_ROLES
    denied = {f"{role}.permission" for role in roles}
    return conftest.FakeCloud(denied_org_perms=denied, **kwargs)


def _group_policy():
    """Returns a policy that grants every role to an admins group."""
    policy = conftest.empty_policy()
    policy["bindings"] = [
        {"role": role, "members": [helpers_deploy.ADMINS]} for role in _ROLES
    ]
    return policy


def test_grant_roles_adds_the_deployer(tmp_path):
    cloud = _lacking()
    ctx = _ctx(tmp_path, [True], cloud=cloud)
    granted = cloud_ops.grant_roles(ctx)
    assert granted == _ORG_ROLES
    (write,) = cloud.writes
    assert write[0] == "set_org_iam_policy"
    assert write[3] == conftest.ETAG
    assert write[4] == ("bindings", "etag")
    for role in granted:
        assert f"user:{conftest.USER}" in _members(cloud, role)
    assert f"user:{conftest.USER}" not in _members(
        cloud, checks.BILLING_ADMIN_ROLE
    )
    (snapshot,) = ctx.run_state.iam.snapshots
    assert snapshot.reason == "grant"
    assert snapshot.etag == conftest.ETAG
    assert snapshot.path.startswith("iam-snapshots/")
    assert conftest.mode(ctx.env.root / snapshot.path) == 0o600
    # IAM has not applied the grants yet, so preflight still fails, but
    # the deployer now holds every role directly: a rerun writes nothing.
    ctx.invalidate()
    assert cloud_ops.grant_roles(ctx) == []
    assert len(cloud.writes) == 1


def test_grant_roles_grants_only_what_preflight_misses(tmp_path):
    # Every role reaches the deployer through a group, except one whose
    # permission the organization withholds.
    role = _ORG_ROLES[0]
    cloud = _lacking(role, policy=_group_policy())
    ctx = _ctx(tmp_path, yes=True, cloud=cloud)
    assert cloud_ops.grant_roles(ctx) == [role]
    user = f"user:{conftest.USER}"
    assert _members(cloud, role) == {helpers_deploy.ADMINS, user}
    for other in _ROLES[1:]:
        assert _members(cloud, other) == {helpers_deploy.ADMINS}, other


def test_grant_roles_passes_when_preflight_does(tmp_path):
    cloud = conftest.FakeCloud()
    ctx = _ctx(tmp_path, cloud=cloud)
    assert cloud_ops.grant_roles(ctx) == []
    assert cloud.writes == []
    assert helpers_deploy.asked(ctx) == []


def test_grant_roles_keeps_the_existing_members(tmp_path):
    role = _ORG_ROLES[0]
    other = "user:other@example.com"
    policy = conftest.empty_policy()
    policy["bindings"] = [{"role": role, "members": [other]}]
    cloud = _lacking(role, policy=policy)
    ctx = _ctx(tmp_path, yes=True, cloud=cloud)
    cloud_ops.grant_roles(ctx)
    assert _members(cloud, role) == {other, f"user:{conftest.USER}"}


def test_grant_roles_types_a_service_account(tmp_path):
    principal = api.Principal(_SA_EMAIL, api.PrincipalKind.SERVICE_ACCOUNT)
    cloud = _lacking(principal=principal)
    ctx = _ctx(tmp_path, yes=True, cloud=cloud)
    role = cloud_ops.grant_roles(ctx)[0]
    assert f"serviceAccount:{_SA_EMAIL}" in _members(cloud, role)


def test_grant_roles_never_grants_billing_admin(tmp_path):
    role = _ORG_ROLES[0]
    cloud = _lacking(
        role, denied_billing_perms={f"{checks.BILLING_ADMIN_ROLE}.permission"}
    )
    ctx = _ctx(tmp_path, yes=True, cloud=cloud)
    with pytest.raises(model.BlockedError) as raised:
        cloud_ops.grant_roles(ctx)
    # The organization role is granted, and the billing role is handed to
    # a billing account administrator.
    assert f"Granted {role} on the organization." in str(raised.value)
    assert (
        f"gcloud billing accounts add-iam-policy-binding {conftest.BILLING} "
        f"--member=user:{conftest.USER} --role={checks.BILLING_ADMIN_ROLE}"
        in (raised.value.remedy or "")
    )
    assert f"user:{conftest.USER}" in _members(cloud, role)
    assert f"user:{conftest.USER}" not in _members(
        cloud, checks.BILLING_ADMIN_ROLE
    )


def test_grant_roles_hands_billing_admin_over_for_an_unknown_principal(
    tmp_path,
):
    cloud = conftest.FakeCloud(
        principal=api.Principal(None, api.PrincipalKind.UNKNOWN),
        denied_billing_perms={f"{checks.BILLING_ADMIN_ROLE}.permission"},
    )
    with pytest.raises(model.BlockedError) as raised:
        cloud_ops.grant_roles(_ctx(tmp_path, cloud=cloud))
    assert "--member=user:<deployer email>" in (raised.value.remedy or "")
    assert cloud.writes == []


def test_grant_roles_skips_billing_admin_without_billing_iam(tmp_path):
    answers = helpers.minimal_answers(
        billing={"account_id": conftest.BILLING, "no_iam": True}
    )
    cloud = conftest.FakeCloud(
        denied_billing_perms={f"{checks.BILLING_ADMIN_ROLE}.permission"}
    )
    ctx = _ctx(tmp_path, cloud=cloud, answers=answers)
    assert cloud_ops.grant_roles(ctx) == []
    assert cloud.writes == []


def test_grant_roles_blocks_when_preflight_cannot_test(tmp_path):
    cloud = conftest.FakeCloud()

    def denied(org_id, permissions):
        raise api.CloudError("quota exceeded")

    cloud.granted_org_permissions = denied
    with pytest.raises(model.BlockedError, match="quota exceeded") as raised:
        cloud_ops.grant_roles(_ctx(tmp_path, yes=True, cloud=cloud))
    remedy = raised.value.remedy or ""
    for role in _ROLES:
        assert f"--role={role} " in remedy, role
    assert cloud.writes == []


def test_grant_roles_unknown_principal(tmp_path):
    principal = api.Principal(None, api.PrincipalKind.UNKNOWN)
    cloud = _lacking(principal=principal)
    with pytest.raises(model.BlockedError) as raised:
        cloud_ops.grant_roles(_ctx(tmp_path, cloud=cloud))
    assert "gcloud organizations add-iam-policy-binding" in (
        raised.value.remedy or ""
    )
    assert cloud.writes == []


def test_grant_roles_declined(tmp_path):
    cloud = _lacking()
    with pytest.raises(model.StoppedError):
        cloud_ops.grant_roles(_ctx(tmp_path, [False], cloud=cloud))
    assert cloud.writes == []


def test_grant_roles_needs_yes_without_a_terminal(tmp_path):
    with pytest.raises(model.InputRequiredError):
        cloud_ops.grant_roles(
            _ctx(tmp_path, interactive=False, cloud=_lacking())
        )


def test_grant_roles_denied_lists_the_commands(tmp_path):
    cloud = _lacking(
        write_errors={"set_org_iam_policy": api.AccessDeniedError("no")}
    )
    with pytest.raises(model.BlockedError) as raised:
        cloud_ops.grant_roles(_ctx(tmp_path, yes=True, cloud=cloud))
    remedy = raised.value.remedy or ""
    assert f"setIAM.sh {conftest.USER} {conftest.ORG_ID}" in remedy
    assert (
        f"gcloud organizations add-iam-policy-binding {conftest.ORG_ID} "
        f"--member=user:{conftest.USER}" in remedy
    )


def test_grant_roles_read_denied(tmp_path):
    cloud = _lacking(policy=api.AccessDeniedError("no read"))
    with pytest.raises(model.BlockedError, match="no read"):
        cloud_ops.grant_roles(_ctx(tmp_path, yes=True, cloud=cloud))


def test_grant_roles_gives_up_after_conflicts(tmp_path):
    cloud = _lacking(
        write_errors={"set_org_iam_policy": api.ConflictError("etag")}
    )
    prompter = prompts.ScriptedPrompter([True])
    ctx = helpers_deploy.make_ctx(tmp_path, prompter=prompter, cloud=cloud)
    with pytest.raises(model.FailedError, match="changed during each"):
        cloud_ops.grant_roles(ctx)
    assert len(cloud.writes) == 3
    # The operator answers once, and every attempt snapshots first.
    assert len(prompter.asked) == 1
    assert len(ctx.run_state.iam.snapshots) == 3


def test_enable_services_enables_only_the_missing(tmp_path, repo):
    required = checks.required_services(repo)
    cloud = conftest.FakeCloud(services=set(required[2:]))
    ctx = _ctx(tmp_path, cloud=cloud)
    assert cloud_ops.enable_services(ctx, "my-project") == required[:2]
    assert cloud.writes == [
        ("enable_services", "my-project", tuple(required[:2]))
    ]
    assert cloud_ops.enable_services(ctx, "my-project") == []
    assert len(cloud.writes) == 1


def test_enable_services_errors_propagate(tmp_path):
    cloud = conftest.FakeCloud(
        services=set(),
        write_errors={"enable_services": api.AccessDeniedError("no")},
    )
    with pytest.raises(api.AccessDeniedError):
        cloud_ops.enable_services(_ctx(tmp_path, cloud=cloud), "my-project")


def test_bq_services_follow_the_billing_export(tmp_path):
    ctx = _ctx(tmp_path)
    assert cloud_ops.BQ_TRANSFER_SERVICE in cloud_ops.bq_services(ctx)
    answers = helpers.minimal_answers(
        billing={"account_id": conftest.BILLING, "no_iam": True}
    )
    ctx = _ctx(tmp_path / "no-iam", answers=answers)
    assert cloud_ops.bq_services(ctx) == cloud_ops.BQ_SERVICES


def _workload_state(ctx):
    workload = helpers_deploy.resource(
        None,
        "google_assured_workloads_workload",
        "primary",
        [
            helpers_deploy.instance(
                {
                    "name": helpers_deploy.WORKLOAD,
                    "resources": [
                        {
                            "resource_id": 123456789012,
                            "resource_type": "CONSUMER_FOLDER",
                        }
                    ],
                },
                0,
            )
        ],
    )
    path = ctx.workspace("0") / probe_lib.STATE_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(helpers_deploy.state_doc([workload])))


def test_locate_workload_from_the_state(tmp_path):
    cloud = conftest.FakeCloud()
    ctx = _ctx(tmp_path, cloud=cloud)
    _workload_state(ctx)
    assert cloud_ops.locate_workload(ctx) == probe_lib.WorkloadRef(
        helpers_deploy.WORKLOAD, _FOLDER
    )


def test_locate_workload_from_the_import(tmp_path, repo):
    address = repo.assured_workload().address
    answers = helpers.minimal_answers(
        imports={"0-bootstrap": {address: helpers_deploy.WORKLOAD}}
    )
    info = api.WorkloadInfo(helpers_deploy.WORKLOAD, "IL5", _FOLDER)
    cloud = conftest.FakeCloud(workloads={helpers_deploy.WORKLOAD: info})
    ctx = _ctx(tmp_path, answers=answers, cloud=cloud)
    assert cloud_ops.locate_workload(ctx) == probe_lib.WorkloadRef(
        helpers_deploy.WORKLOAD, _FOLDER
    )


def test_locate_workload_by_folder_name(tmp_path):
    cloud = conftest.FakeCloud(folders=[_FOLDER])
    ctx = _ctx(tmp_path, cloud=cloud)
    assert cloud_ops.locate_workload(ctx) == probe_lib.WorkloadRef(
        None, _FOLDER
    )
    cloud.folders = [_FOLDER, "folders/2"]
    assert cloud_ops.locate_workload(ctx) == probe_lib.WorkloadRef(None, None)


def _bq_cloud(**kwargs):
    info = api.WorkloadInfo(
        helpers_deploy.WORKLOAD,
        "IL5",
        _FOLDER,
        (*cloud_ops.BQ_SERVICES, cloud_ops.BQ_TRANSFER_SERVICE),
    )
    return conftest.FakeCloud(
        restriction=api.ServiceRestriction(allowed=("storage.googleapis.com",)),
        workloads={helpers_deploy.WORKLOAD: info},
        **kwargs,
    )


def test_allow_bq_check(tmp_path):
    cloud = _bq_cloud()
    ctx = _ctx(tmp_path, cloud=cloud)
    _workload_state(ctx)
    found = cloud_ops.allow_bq_check(ctx)
    assert found.folder == _FOLDER
    assert set(found.missing) == set(cloud_ops.bq_services(ctx))
    assert not found.done
    cloud.restriction = api.ServiceRestriction()
    assert cloud_ops.allow_bq_check(ctx).done


def test_allow_bq_check_before_the_workload(tmp_path):
    found = cloud_ops.allow_bq_check(_ctx(tmp_path))
    assert found.folder is None
    assert not found.done


def test_allow_bq_run_appends_the_compliant_services(tmp_path):
    cloud = _bq_cloud()
    slept = []
    ctx = _ctx(tmp_path, [True], cloud=cloud, sleep=slept.append)
    _workload_state(ctx)
    assert cloud_ops.allow_bq_run(ctx) is True
    assert cloud.writes == [
        ("restrict_allowed_resources", helpers_deploy.WORKLOAD)
    ]
    assert slept == []


def test_allow_bq_run_lists_every_service_it_allows(tmp_path):
    # APPEND_COMPLIANT_RESOURCES allows every compliant service that the
    # folder blocks, so the question must not name BigQuery alone.
    extra = ("compute.googleapis.com", "container.googleapis.com")
    cloud = _bq_cloud()
    workload = cloud.workloads[helpers_deploy.WORKLOAD]
    cloud.workloads[helpers_deploy.WORKLOAD] = dataclasses.replace(
        workload,
        compliant_but_disallowed=(*workload.compliant_but_disallowed, *extra),
    )
    ctx = _ctx(tmp_path, cloud=cloud, yes=True, interactive=False)
    _workload_state(ctx)
    with pytest.raises(model.InputRequiredError, match="these 6 services"):
        cloud_ops.allow_bq_run(ctx)
    assert all(name in helpers_deploy.output(ctx) for name in extra)
    assert cloud.writes == []
    ctx = _ctx(tmp_path / "tty", [True], cloud=cloud)
    _workload_state(ctx)
    assert cloud_ops.allow_bq_run(ctx) is True
    assert helpers_deploy.asked(ctx) == [
        f"Allow these 6 services on {_FOLDER} through "
        f"{helpers_deploy.WORKLOAD}?"
    ]


def test_allow_bq_run_waits_for_the_policy(tmp_path):
    cloud = _bq_cloud()
    slept = []
    ctx = _ctx(tmp_path, cloud=cloud, yes=True, sleep=slept.append)
    _workload_state(ctx)

    def no_change(name):
        # The write succeeds, but the policy never allows the services.
        cloud.writes.append(("restrict_allowed_resources", name))

    cloud.restrict_allowed_resources = no_change
    assert cloud_ops.allow_bq_run(ctx) is False
    poll = cloud_ops.ALLOW_BQ_POLL_SECONDS
    assert slept == [poll] * (cloud_ops.ALLOW_BQ_WAIT_SECONDS // poll)


def test_allow_bq_run_refuses_services_the_regime_lacks(tmp_path):
    info = api.WorkloadInfo(helpers_deploy.WORKLOAD, "IL5", _FOLDER, ())
    cloud = conftest.FakeCloud(
        restriction=api.ServiceRestriction(allowed=("storage.googleapis.com",)),
        workloads={helpers_deploy.WORKLOAD: info},
    )
    ctx = _ctx(tmp_path, cloud=cloud, yes=True)
    _workload_state(ctx)
    with pytest.raises(model.BlockedError, match="not compliant") as raised:
        cloud_ops.allow_bq_run(ctx)
    assert "scripts/allow_bq.sh" in (raised.value.remedy or "")
    assert cloud.writes == []


def test_allow_bq_run_denied(tmp_path):
    cloud = _bq_cloud(
        write_errors={"restrict_allowed_resources": api.AccessDeniedError("x")}
    )
    ctx = _ctx(tmp_path, cloud=cloud, yes=True)
    _workload_state(ctx)
    with pytest.raises(model.BlockedError, match="Cannot change the workload"):
        cloud_ops.allow_bq_run(ctx)


def test_allow_bq_run_without_the_workload(tmp_path):
    cloud = _bq_cloud(folders=[_FOLDER])
    with pytest.raises(model.BlockedError, match="Cannot find"):
        cloud_ops.allow_bq_run(_ctx(tmp_path, cloud=cloud, yes=True))


def test_allow_bq_run_declined(tmp_path):
    cloud = _bq_cloud()
    ctx = _ctx(tmp_path, [False], cloud=cloud)
    _workload_state(ctx)
    with pytest.raises(model.StoppedError):
        cloud_ops.allow_bq_run(ctx)
    assert cloud.writes == []


def test_allow_bq_run_needs_yes_without_a_terminal(tmp_path):
    cloud = _bq_cloud()
    ctx = _ctx(tmp_path, cloud=cloud, interactive=False)
    _workload_state(ctx)
    with pytest.raises(model.InputRequiredError):
        cloud_ops.allow_bq_run(ctx)
    assert cloud.writes == []


def _account(name, disabled):
    email = f"tst-prod-{name}@tst-prod-iac-core-0.iam.gserviceaccount.com"
    return api.ServiceAccount(email, disabled)


def test_service_accounts_enabled(tmp_path):
    cloud = conftest.FakeCloud(
        accounts=[
            _account("bootstrap-0", False),
            _account("resman-0", True),
            api.ServiceAccount(
                "other@my-project.iam.gserviceaccount.com", True
            ),
        ]
    )
    found = cloud_ops.service_accounts_enabled(_ctx(tmp_path, cloud=cloud))
    assert found.enabled is False
    assert found.disabled == (_account("resman-0", True).email,)
    assert found.remedy == (
        f"gcloud iam service-accounts enable {found.disabled[0]} "
        "--project=tst-prod-iac-core-0"
    )


def test_service_accounts_enabled_without_accounts(tmp_path):
    found = cloud_ops.service_accounts_enabled(_ctx(tmp_path))
    assert found.enabled is True
    cloud = conftest.FakeCloud(accounts=api.CloudError("no project"))
    found = cloud_ops.service_accounts_enabled(
        _ctx(tmp_path / "other", cloud=cloud)
    )
    assert found.enabled is None
    assert found.error == "no project"


def test_member():
    user = api.Principal(conftest.USER, api.PrincipalKind.USER)
    assert cloud_ops.member(user) == f"user:{conftest.USER}"
    unknown = api.Principal(conftest.USER, api.PrincipalKind.UNKNOWN)
    assert cloud_ops.member(unknown) is None
    assert cloud_ops.member(api.Principal(None, api.PrincipalKind.USER)) is None
