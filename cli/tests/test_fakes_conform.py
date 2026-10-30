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

"""Checks that the fakes and live classes implement their protocols.

A protocol method that a fake lacks, or takes under other parameter names,
would only fail in the test that first calls it, so these tests compare
every protocol member up front.
"""

import inspect
import subprocess
import typing

import pytest

import conftest
from stellar_engine import tools as tools_lib
from stellar_engine.gcp import api
from stellar_engine.gcp import live
from stellar_engine.terraform import runner as runner_lib


def _parameters(function):
    """Returns the names and kinds of a callable's parameters, sans self."""
    return [
        (parameter.name, parameter.kind)
        for parameter in inspect.signature(function).parameters.values()
        if parameter.name != "self"
    ]


def _mismatches(protocol, implementation):
    """Lists protocol members missing from a class or taking other args."""
    found = []
    for name in sorted(typing.get_protocol_members(protocol)):
        member = getattr(implementation, name, None)
        if not callable(member):
            found.append(f"{name} is missing")
        elif _parameters(member) != _parameters(getattr(protocol, name)):
            found.append(f"{name} takes other parameters")
    return found


@pytest.mark.parametrize(
    ("protocol", "implementation"),
    [
        (api.CloudApi, conftest.FakeCloud),
        (api.CloudWriter, conftest.FakeCloud),
        (api.CloudApi, live.LiveCloudApi),
        (api.CloudWriter, live.LiveCloudApi),
        (tools_lib.LocalTools, conftest.FakeTools),
        (tools_lib.LocalTools, tools_lib.SystemTools),
    ],
    ids=lambda value: value.__name__,
)
def test_implements_every_protocol_member(protocol, implementation):
    assert _mismatches(protocol, implementation) == []


def test_fake_terraform_implements_the_runner():
    assert _mismatches(runner_lib.Runner, conftest.FakeTerraform) == []
    assert _mismatches(runner_lib.Runner, runner_lib.SystemRunner) == []


def test_fake_terraform_scripts_results_by_subcommand(tmp_path):
    failed = subprocess.CompletedProcess([], 1, "Error: plan failed\n", "")
    fake = conftest.FakeTerraform(
        results={"plan": [failed], "state pull": [RuntimeError("boom")]}
    )
    log = tmp_path / "logs" / "plan.log"
    found = fake.run(
        tmp_path,
        ["plan", "-no-color", "-out=x.tfplan"],
        env={"PATH": "/bin", "TF_IN_AUTOMATION": "1"},
        log=log,
        timeout=900,
    )
    assert found is failed
    assert log.read_text(encoding="utf-8") == (
        "Error: plan failed\n# exit status 1\n"
    )
    assert conftest.mode(log) == 0o600
    # Without a scripted result, a call succeeds with empty output.
    again = fake.capture(
        tmp_path, ["plan", "-no-color"], env={}, log=log, timeout=900
    )
    assert again.returncode == 0
    assert again.args == [
        "terraform",
        f"-chdir={tmp_path}",
        "plan",
        "-no-color",
    ]
    with pytest.raises(RuntimeError, match="boom"):
        fake.capture(tmp_path, ["state", "pull"], env={}, log=log, timeout=60)
    assert fake.calls == [
        (("plan", "-no-color", "-out=x.tfplan"), ("PATH", "TF_IN_AUTOMATION")),
        (("plan", "-no-color"), ()),
        (("state", "pull"), ()),
    ]


def test_fake_cloud_writes_change_what_it_reads():
    cloud = conftest.FakeCloud(services={"a.googleapis.com"})
    cloud.enable_services("my-project", ["b.googleapis.com"])
    assert cloud.enabled_services("my-project") == {
        "a.googleapis.com",
        "b.googleapis.com",
    }
    policy = cloud.get_org_iam_policy(conftest.ORG_ID)
    written = cloud.set_org_iam_policy(
        conftest.ORG_ID,
        policy,
        etag=policy.etag,
        update_mask=("bindings", "etag"),
    )
    assert cloud.get_org_iam_policy(conftest.ORG_ID) == written
    with pytest.raises(api.ConflictError):
        cloud.set_org_iam_policy(
            conftest.ORG_ID,
            policy,
            etag=policy.etag,
            update_mask=("bindings", "etag"),
        )
    member = "serviceAccount:sa@my-project.iam.gserviceaccount.com"
    cloud.add_billing_account_binding(
        conftest.BILLING, "roles/billing.user", member
    )
    billing = cloud.billing_account_iam(conftest.BILLING)
    assert member in next(iter(billing.bindings.values()))
    assert [write[0] for write in cloud.writes] == [
        "enable_services",
        "set_org_iam_policy",
        "set_org_iam_policy",
        "add_billing_account_binding",
    ]


def test_fake_cloud_restrict_allows_the_compliant_services():
    name = f"organizations/{conftest.ORG_ID}/locations/us-east4/workloads/w"
    cloud = conftest.FakeCloud(
        restriction=api.ServiceRestriction(allowed=("storage.googleapis.com",)),
        workloads={
            name: api.WorkloadInfo(
                name, "IL5", "folders/1", ("bigquery.googleapis.com",)
            )
        },
    )
    assert not cloud.effective_service_restriction("folders/1").allows(
        "bigquery.googleapis.com"
    )
    cloud.restrict_allowed_resources(name)
    assert cloud.effective_service_restriction("folders/1").allows(
        "bigquery.googleapis.com"
    )
    workload = cloud.assured_workload(name)
    assert workload is not None
    assert workload.compliant_but_disallowed == ()


def test_fake_cloud_write_errors_and_identity_objects():
    cloud = conftest.FakeCloud(
        write_errors={"enable_services": api.AccessDeniedError("no")},
        objects={
            ("bucket", "state"): api.AccessDeniedError("ADC cannot read"),
            ("bucket", "state", "sa@x.iam.gserviceaccount.com"): (
                api.ObjectData(b"{}", 3)
            ),
        },
    )
    with pytest.raises(api.AccessDeniedError):
        cloud.enable_services("my-project", ["x.googleapis.com"])
    assert cloud.writes == [
        ("enable_services", "my-project", ("x.googleapis.com",))
    ]
    with pytest.raises(api.AccessDeniedError):
        cloud.read_object("bucket", "state")
    found = cloud.read_object(
        "bucket", "state", impersonate="sa@x.iam.gserviceaccount.com"
    )
    assert found == api.ObjectData(b"{}", 3)
    assert cloud.read_object("bucket", "other") is None
