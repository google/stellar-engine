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

"""Tests for the Stage 0 probe and the state migration decision."""

import json

import pytest

import conftest
import helpers
import helpers_deploy
from stellar_engine import workspace as workspace_lib
from stellar_engine.deploy import probe as probe_lib
from stellar_engine.gcp import api
from stellar_engine.render import phase

_BUCKET = "tst-prod-iac-core-bootstrap-0"
_SA = "tst-prod-bootstrap-0@tst-prod-iac-core-0.iam.gserviceaccount.com"
_BACKEND = probe_lib.Backend(_BUCKET, _SA)
_REMOTE_PROVIDERS = f"""terraform {{
  backend "gcs" {{
    bucket                      = "{_BUCKET}"
    impersonate_service_account = "{_SA}"
  }}
}}
"""
_LOCAL_PROVIDERS = 'provider "google" {}\n'
_EXPECTED = probe_lib.CachedBackend(probe_lib.GCS, _BUCKET)
_OTHER = "00000000-9999-9999-9999-999999999999"


def _cached_backend(bucket=_BUCKET):
    return {
        "version": 3,
        "terraform_version": "1.13.3",
        "backend": {
            "type": "gcs",
            "config": {
                "bucket": bucket,
                "impersonate_service_account": _SA,
                "prefix": None,
            },
            "hash": 1,
        },
    }


def _summary(serial, lineage=helpers_deploy.LINEAGE):
    return probe_lib.summarize(
        helpers_deploy.state_bytes(
            helpers_deploy.project_state(serial, lineage)
        )
    )


def _remote(serial=None, lineage=helpers_deploy.LINEAGE, generation=7):
    if serial is None:
        return probe_lib.RemoteState(readable=True)
    return probe_lib.RemoteState(
        readable=True,
        exists=True,
        generation=generation,
        summary=_summary(serial, lineage),
    )


def _probe(
    *,
    providers_remote=True,
    cached=None,
    local=None,
    backup=None,
    remote=None,
    outputs_providers=True,
):
    return probe_lib.Probe(
        phase_file=False,
        foreign_phase_file=False,
        providers_remote=providers_remote,
        providers_match=providers_remote,
        outputs_providers=outputs_providers,
        cached=cached,
        local=local,
        backup=backup,
        remote=remote or probe_lib.RemoteState(readable=True),
        backend=_BACKEND,
    )


def test_backend_names():
    assert probe_lib.backend("tst", "0") == _BACKEND
    assert probe_lib.backend("tst", "1") == probe_lib.Backend(
        "tst-prod-iac-core-resman-0",
        "tst-prod-resman-0@tst-prod-iac-core-0.iam.gserviceaccount.com",
    )
    with pytest.raises(KeyError):
        probe_lib.backend("tst", "pre")
    assert _BACKEND.state_uri == f"gs://{_BUCKET}/default.tfstate"


def test_instances_build_terraform_addresses():
    doc = helpers_deploy.state_doc(
        [
            helpers_deploy.resource(
                'module.x["k"]',
                "google_project",
                "project",
                [helpers_deploy.instance({}, 0)],
            ),
            helpers_deploy.resource(
                None,
                "google_folder",
                "folder",
                [helpers_deploy.instance({}, "a b")],
            ),
            helpers_deploy.resource(
                "module.y",
                "google_client_config",
                "current",
                [helpers_deploy.instance({})],
                mode="data",
            ),
        ]
    )
    assert [address for address, _ in probe_lib.instances(doc)] == [
        'module.x["k"].google_project.project[0]',
        'google_folder.folder["a b"]',
        "module.y.data.google_client_config.current",
    ]


def test_summarize():
    empty = probe_lib.summarize(b"")
    assert (empty.size, empty.empty, empty.parsed) == (0, True, False)
    found = _summary(5)
    assert (found.serial, found.lineage) == (5, helpers_deploy.LINEAGE)
    assert str(found.record()) == f"serial 5 lineage {helpers_deploy.LINEAGE}"
    assert found.addresses == {
        "module.automation-project.google_project.project[0]"
    }
    assert not found.empty
    no_resources = probe_lib.summarize(
        helpers_deploy.state_bytes(helpers_deploy.state_doc())
    )
    assert no_resources.empty
    # Terraform migrates a state that holds only root outputs.
    outputs = helpers_deploy.state_doc()
    outputs["outputs"] = {"bucket": {"value": "x", "type": "string"}}
    assert not probe_lib.summarize(helpers_deploy.state_bytes(outputs)).empty
    garbage = probe_lib.summarize(b"{not a state")
    assert (garbage.parsed, garbage.empty, garbage.lineage) == (
        False,
        False,
        None,
    )


def test_summarize_finds_the_workload():
    workload = helpers_deploy.resource(
        None,
        "google_assured_workloads_workload",
        "primary",
        [
            helpers_deploy.instance(
                {
                    "name": helpers_deploy.WORKLOAD,
                    "resources": [
                        {"resource_id": 111, "resource_type": "KEYRING"},
                        {
                            "resource_id": 123456789012,
                            "resource_type": "CONSUMER_FOLDER",
                        },
                    ],
                },
                0,
            )
        ],
    )
    found = probe_lib.summarize(
        helpers_deploy.state_bytes(helpers_deploy.state_doc([workload]))
    )
    assert found.workload == probe_lib.WorkloadRef(
        helpers_deploy.WORKLOAD, "folders/123456789012"
    )


def _write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data if isinstance(data, bytes) else data.encode())


def test_probe_reads_a_migrated_workspace(tmp_path):
    remote = helpers_deploy.project_state(298)
    cloud = conftest.FakeCloud(
        objects={
            (_BUCKET, probe_lib.REMOTE_OBJECT): api.AccessDeniedError("ADC"),
            (_BUCKET, probe_lib.REMOTE_OBJECT, _SA): api.ObjectData(
                helpers_deploy.state_bytes(remote), 17
            ),
        }
    )
    ctx = helpers_deploy.make_ctx(
        tmp_path,
        cloud=cloud,
        answers=helpers.minimal_answers(stage0_phase="final"),
    )
    ws = ctx.workspace("0")
    _write(ws / workspace_lib.BOOTSTRAP_PROVIDERS, _REMOTE_PROVIDERS)
    _write(
        ctx.env.fast_config / "providers" / workspace_lib.BOOTSTRAP_PROVIDERS,
        _REMOTE_PROVIDERS,
    )
    _write(ws / ".terraform/terraform.tfstate", json.dumps(_cached_backend()))
    _write(ws / probe_lib.STATE_FILE, b"")
    _write(
        ws / probe_lib.BACKUP_FILE,
        helpers_deploy.state_bytes(helpers_deploy.project_state(297)),
    )
    probe = probe_lib.probe(ctx)
    assert (probe.phase_file, probe.foreign_phase_file) == (False, False)
    assert probe.providers_remote and probe.providers_match
    assert probe.outputs_providers
    assert probe.cached == _EXPECTED
    assert probe.local == probe_lib.StateSummary(0)
    assert probe.backup is not None and probe.backup.serial == 297
    assert probe.remote.readable and probe.remote.exists
    assert (probe.remote.serial, probe.remote.generation) == (298, 17)
    assert probe.configured
    assert probe.migrated is True
    assert probe.state is probe.remote.summary
    reads = [call for call in cloud.calls if call[0] == "read_object"]
    assert [call[3] for call in reads] == [None, _SA]


def test_probe_reads_a_fresh_workspace(tmp_path):
    ctx = helpers_deploy.make_ctx(tmp_path)
    ws = ctx.workspace("0")
    _write(ws / workspace_lib.BOOTSTRAP_PROVIDERS, _LOCAL_PROVIDERS)
    _write(ws / phase.FILENAME, phase.text(ctx.answers, ctx.repo))
    probe = probe_lib.probe(ctx)
    assert probe.phase_file and not probe.foreign_phase_file
    assert not probe.providers_remote
    assert not probe.providers_match and not probe.outputs_providers
    assert probe.cached is None
    assert probe.local is None and probe.backup is None
    assert probe.remote == probe_lib.RemoteState(readable=True)
    assert probe.migrated is False
    assert probe.state is None


def test_probe_flags_a_foreign_phase_file(tmp_path):
    ctx = helpers_deploy.make_ctx(tmp_path)
    _write(ctx.workspace("0") / phase.FILENAME, 'bootstrap_user = "x"\n')
    probe = probe_lib.probe(ctx)
    assert probe.foreign_phase_file and not probe.phase_file


@pytest.mark.parametrize(
    ("errors", "readable"),
    [
        ((api.AccessDeniedError("a"), api.AccessDeniedError("b")), False),
        ((api.CloudError("down"),), False),
        ((api.CredentialsError("no ADC"),), False),
    ],
)
def test_read_remote_failures(errors, readable):
    cloud = conftest.FakeCloud(
        objects={
            (_BUCKET, probe_lib.REMOTE_OBJECT): errors[0],
            (_BUCKET, probe_lib.REMOTE_OBJECT, _SA): errors[-1],
        }
    )
    found = probe_lib.read_remote(cloud, _BACKEND)
    assert found.readable is readable
    assert found.error


def test_read_remote_missing_object():
    found = probe_lib.read_remote(conftest.FakeCloud(), _BACKEND)
    assert found == probe_lib.RemoteState(readable=True)
    assert found.empty


def test_read_object_as_falls_back_to_the_service_account():
    cloud = conftest.FakeCloud(
        objects={
            (_BUCKET, "x"): api.AccessDeniedError("a"),
            (_BUCKET, "x", _SA): api.ObjectData(b"{}", 3),
        }
    )
    assert probe_lib.read_object_as(cloud, _BUCKET, "x", _SA) == api.ObjectData(
        b"{}", 3
    )
    cloud.objects[(_BUCKET, "x", _SA)] = api.AccessDeniedError("b")
    with pytest.raises(api.AccessDeniedError, match="a; b"):
        probe_lib.read_object_as(cloud, _BUCKET, "x", _SA)
    assert probe_lib.read_object_as(cloud, _BUCKET, "missing", _SA) is None


def test_migrated_is_unknown_without_the_remote_state():
    probe = _probe(
        cached=_EXPECTED,
        local=probe_lib.StateSummary(0),
        remote=probe_lib.RemoteState(readable=False, error="denied"),
    )
    assert probe.migrated is None
    # The check says UNKNOWN; the run refuses.
    decision = probe_lib.migrate_decision(
        _probe(
            remote=probe_lib.RemoteState(readable=False, error="denied"),
            local=_summary(3),
        )
    )
    assert decision.action is probe_lib.MigrateAction.REFUSE
    assert "denied" in decision.reason
    # A check of a state that Terraform reads remotely raises instead.
    with pytest.raises(api.CloudError, match=f"gs://{_BUCKET}/.*denied"):
        probe.readable_state()


@pytest.mark.parametrize(
    ("probe", "migrated"),
    [
        (_probe(cached=_EXPECTED, local=_summary(3), remote=_remote(3)), False),
        (_probe(cached=_EXPECTED, remote=_remote()), False),
        (
            _probe(
                cached=_EXPECTED,
                backup=_summary(3, _OTHER),
                remote=_remote(3),
            ),
            False,
        ),
        (_probe(cached=None, remote=_remote(3)), False),
        (_probe(cached=_EXPECTED, backup=_summary(3), remote=_remote(4)), True),
    ],
    ids=["local-left", "remote-absent", "other-lineage", "no-init", "done"],
)
def test_migrated(probe, migrated):
    assert probe.migrated is migrated


_A = probe_lib.MigrateAction
_UNREADABLE = probe_lib.RemoteState(readable=False, error="denied")
_DECISIONS = {
    "local-backend": (_probe(providers_remote=False), _A.INIT),
    "local-backend-local-state": (
        _probe(providers_remote=False, local=_summary(3), remote=_remote(5)),
        _A.INIT,
    ),
    # A workspace rendered again keeps the local providers file and no
    # state, while the bucket holds the state of earlier applies.
    "local-backend-remote-present": (
        _probe(
            providers_remote=False,
            local=probe_lib.StateSummary(0),
            remote=_remote(3),
        ),
        _A.REFUSE,
    ),
    "local-backend-unreadable-after-apply": (
        _probe(providers_remote=False, remote=_UNREADABLE),
        _A.REFUSE,
    ),
    # A fresh organization whose bucket cannot be read yet.
    "local-backend-unreadable-before-apply": (
        _probe(
            providers_remote=False,
            remote=_UNREADABLE,
            outputs_providers=False,
        ),
        _A.INIT,
    ),
    "providers-reverted": (
        _probe(providers_remote=False, cached=_EXPECTED),
        _A.REFUSE,
    ),
    "configured": (
        _probe(cached=_EXPECTED, local=probe_lib.StateSummary(0)),
        _A.INIT,
    ),
    "configured-local-missing": (
        _probe(cached=_EXPECTED, remote=_remote(3)),
        _A.INIT,
    ),
    # Init ignores a local file beside a configured backend, so only an
    # archive empties it, and only when the remote state holds it.
    "configured-remote-newer": (
        _probe(cached=_EXPECTED, local=_summary(5), remote=_remote(7)),
        _A.ARCHIVE,
    ),
    "configured-remote-equal": (
        _probe(cached=_EXPECTED, local=_summary(5), remote=_remote(5)),
        _A.ARCHIVE,
    ),
    "configured-local-newer": (
        _probe(cached=_EXPECTED, local=_summary(9), remote=_remote(3)),
        _A.REFUSE,
    ),
    "configured-other-lineage": (
        _probe(cached=_EXPECTED, local=_summary(5), remote=_remote(7, _OTHER)),
        _A.REFUSE,
    ),
    "configured-remote-absent": (
        _probe(cached=_EXPECTED, local=_summary(5)),
        _A.REFUSE,
    ),
    "configured-unreadable": (
        _probe(
            cached=_EXPECTED,
            local=_summary(5),
            remote=probe_lib.RemoteState(readable=False, error="denied"),
        ),
        _A.REFUSE,
    ),
    "other-bucket": (
        _probe(cached=probe_lib.CachedBackend(probe_lib.GCS, "other")),
        _A.REFUSE,
    ),
    "unreadable": (
        _probe(
            local=_summary(3),
            remote=probe_lib.RemoteState(readable=False, error="denied"),
        ),
        _A.REFUSE,
    ),
    "local-empty-remote-present": (
        _probe(local=probe_lib.StateSummary(0), remote=_remote(3)),
        _A.INIT,
    ),
    "local-missing-remote-absent": (_probe(), _A.INIT),
    "local-only": (_probe(local=_summary(3)), _A.MIGRATE),
    "remote-empty": (
        _probe(
            local=_summary(3),
            remote=probe_lib.RemoteState(
                readable=True,
                exists=True,
                generation=1,
                summary=probe_lib.StateSummary(0),
            ),
        ),
        _A.MIGRATE,
    ),
    "remote-older": (
        _probe(local=_summary(5), remote=_remote(4)),
        _A.MIGRATE,
    ),
    "remote-equal": (
        _probe(local=_summary(5), remote=_remote(5)),
        _A.ARCHIVE,
    ),
    "remote-newer": (
        _probe(local=_summary(5), remote=_remote(6)),
        _A.ARCHIVE,
    ),
    "other-lineage": (
        _probe(local=_summary(5), remote=_remote(9, _OTHER)),
        _A.REFUSE,
    ),
}


@pytest.mark.parametrize(
    ("probe", "action"), _DECISIONS.values(), ids=_DECISIONS.keys()
)
def test_migrate_decision(probe, action):
    assert probe_lib.migrate_decision(probe).action is action


def test_refusal_names_both_states():
    probe, _ = _DECISIONS["other-lineage"]
    reason = probe_lib.migrate_decision(probe).reason
    assert f"local serial 5 lineage {helpers_deploy.LINEAGE}" in reason
    assert f"remote serial 9 lineage {_OTHER}" in reason
    decision = probe_lib.migrate_decision(probe)
    assert _BACKEND.state_uri in probe_lib.refusal_remedy(probe, decision)


def test_local_backend_refusal_points_at_the_remote_providers():
    probe, _ = _DECISIONS["local-backend-remote-present"]
    decision = probe_lib.migrate_decision(probe)
    assert _BACKEND.state_uri in decision.reason
    assert f"remote serial 3 lineage {helpers_deploy.LINEAGE}" in (
        decision.reason
    )
    remedy = probe_lib.refusal_remedy(probe, decision)
    assert "stellar deploy --only s0.remote_providers" in remedy
    assert f"fast-config/{workspace_lib.REMOTE_BOOTSTRAP_PROVIDERS}" in remedy
    assert "outputs bucket" not in remedy
    probe, _ = _DECISIONS["local-backend-unreadable-after-apply"]
    reason = probe_lib.migrate_decision(probe).reason
    assert "cannot be read: denied" in reason
    # Without the file under fast-config, the outputs bucket has a copy.
    lost = _probe(
        providers_remote=False, remote=_remote(3), outputs_providers=False
    )
    decision = probe_lib.migrate_decision(lost)
    assert decision.action is _A.REFUSE
    remedy = probe_lib.refusal_remedy(lost, decision)
    assert remedy.startswith(
        f"Copy {workspace_lib.REMOTE_BOOTSTRAP_PROVIDERS} from the Stage 0 "
        "outputs bucket"
    )
    assert "--only s0.remote_providers" in remedy


def test_configured_refusal_names_both_states():
    probe, _ = _DECISIONS["configured-local-newer"]
    reason = probe_lib.migrate_decision(probe).reason
    assert "ignores the local state" in reason
    assert f"local serial 9 lineage {helpers_deploy.LINEAGE}" in reason
    assert f"remote serial 3 lineage {helpers_deploy.LINEAGE}" in reason
