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

"""Tests for the organization IAM policy model, targets and diff."""

import dataclasses
import datetime
import json
import pathlib

import pytest

import conftest
from stellar_engine import iam_diff
from stellar_engine import paths
from stellar_engine import repo as repo_lib
from stellar_engine.terraform import plan as plan_lib

ORG_ADMIN = "roles/resourcemanager.organizationAdmin"
DELEGATED = f"organizations/{conftest.ORG_ID}/roles/organizationIamAdmin"
STAGE0_SA = (
    "serviceAccount:abc-prod-resman-0@abc-prod-iac-core-0"
    ".iam.gserviceaccount.com"
)
CONDITION = {
    "title": "automation_sa_delegated_grants",
    "expression": "api.getAttribute('x', []).hasOnly(['roles/browser'])",
    "description": "Automation service account delegated grants.",
}
NOW = datetime.datetime(2026, 10, 29, 12, 0, tzinfo=datetime.UTC)


def gcloud_policy():
    """Returns a policy in the exact shape gcloud prints."""
    return {
        "version": 3,
        "etag": conftest.ETAG,
        "bindings": [
            {
                "role": ORG_ADMIN,
                "members": [
                    "group:gcp-organization-admins@example.com",
                    "user:admin@example.com",
                ],
            },
            {
                "role": DELEGATED,
                "members": [STAGE0_SA],
                "condition": CONDITION,
            },
        ],
        "auditConfigs": [
            {
                "service": "allServices",
                "auditLogConfigs": [
                    {"logType": "ADMIN_READ"},
                    {
                        "logType": "DATA_READ",
                        "exemptedMembers": ["user:quiet@example.com"],
                    },
                ],
            }
        ],
    }


def change(
    address,
    actions,
    *,
    before=None,
    after=None,
    after_unknown=None,
    kind=iam_diff.BINDING_TYPE,
    mode="managed",
):
    """Returns one `resource_changes` entry of a plan document."""
    return {
        "address": address,
        "mode": mode,
        "type": kind,
        "name": address.rsplit("[", 1)[0].rsplit(".", 1)[-1],
        "change": {
            "actions": actions,
            "before": before,
            "after": after,
            "after_unknown": after_unknown or {},
        },
    }


def binding(role, members, condition=None):
    """Returns the values of a google_organization_iam_binding."""
    return {
        "org_id": conftest.ORG_ID,
        "role": role,
        "members": members,
        "condition": [] if condition is None else [condition],
    }


def plan(*changes):
    """Returns the parsed plan of `resource_changes` entries."""
    return plan_lib.parse(
        {"format_version": "1.2", "resource_changes": list(changes)}
    )


def authoritative(role):
    return (
        "module.organization.google_organization_iam_binding"
        f'.authoritative["{role}"]'
    )


class TestPolicyCodec:
    def test_gcloud_json_round_trips(self):
        data = gcloud_policy()
        policy = iam_diff.Policy.from_json(data)
        assert policy.to_json() == data
        assert iam_diff.Policy.from_json(policy.to_json()) == policy

    def test_conditional_binding_has_its_own_key(self):
        data = gcloud_policy()
        data["bindings"].append(
            {"role": DELEGATED, "members": ["user:x@example.com"]}
        )
        policy = iam_diff.Policy.from_json(data)
        condition = iam_diff.Condition.from_json(CONDITION)
        assert policy.bindings[iam_diff.BindingKey(DELEGATED, condition)] == {
            STAGE0_SA
        }
        assert policy.bindings[iam_diff.BindingKey(DELEGATED)] == {
            "user:x@example.com"
        }

    def test_audit_configs_sort_for_comparison(self):
        policy = iam_diff.Policy.from_json(gcloud_policy())
        assert policy.audit_configs["allServices"] == (
            iam_diff.AuditLogConfig("ADMIN_READ"),
            iam_diff.AuditLogConfig("DATA_READ", ("user:quiet@example.com",)),
        )

    def test_repeated_bindings_merge(self):
        data = {
            "bindings": [
                {"role": ORG_ADMIN, "members": ["user:a@example.com"]},
                {"role": ORG_ADMIN, "members": ["user:b@example.com"]},
            ]
        }
        policy = iam_diff.Policy.from_json(data)
        assert policy.version == 1
        assert policy.etag == ""
        assert policy.bindings == {
            iam_diff.BindingKey(ORG_ADMIN): {
                "user:a@example.com",
                "user:b@example.com",
            }
        }

    @pytest.mark.parametrize(
        "data",
        [
            [],
            {"bindings": {"role": ORG_ADMIN}},
            {"bindings": [{"members": ["user:a@example.com"]}]},
            {
                "bindings": [
                    {"role": ORG_ADMIN, "members": "user:a@example.com"}
                ]
            },
            {
                "auditConfigs": [
                    {"service": "allServices", "auditLogConfigs": [{}]}
                ]
            },
        ],
    )
    def test_malformed_policies_raise(self, data):
        with pytest.raises(ValueError):
            iam_diff.Policy.from_json(data)

    def test_grant_text(self):
        condition = iam_diff.Condition.from_json(CONDITION)
        plain = iam_diff.Grant(
            iam_diff.BindingKey(ORG_ADMIN), "user:a@example.com"
        )
        conditional = iam_diff.Grant(
            iam_diff.BindingKey(DELEGATED, condition), STAGE0_SA
        )
        assert str(plain) == f"{ORG_ADMIN} user:a@example.com"
        assert str(conditional) == (
            f"{DELEGATED} {STAGE0_SA} (condition {CONDITION['title']})"
        )


class TestTargetFromPlan:
    def test_reads_authoritative_and_conditional_bindings(self):
        parsed = plan(
            change(
                authoritative(ORG_ADMIN),
                ["create"],
                after=binding(
                    ORG_ADMIN, ["group:gcp-organization-admins@example.com"]
                ),
                after_unknown={
                    "condition": [],
                    "etag": True,
                    "members": [False],
                },
            ),
            change(
                'module.organization.google_organization_iam_binding.bindings["organization_iam_admin_conditional"]',
                ["create"],
                after=binding(DELEGATED, [STAGE0_SA], CONDITION),
                after_unknown={"condition": [{}], "etag": True, "id": True},
            ),
        )
        target = iam_diff.target_from_plan(parsed)
        condition = iam_diff.Condition.from_json(CONDITION)
        assert target.bindings == {
            iam_diff.BindingKey(ORG_ADMIN): {
                "group:gcp-organization-admins@example.com"
            },
            iam_diff.BindingKey(DELEGATED, condition): {STAGE0_SA},
        }
        assert not target.empty

    def test_null_members_remove_every_member(self):
        # iam_delete_roles plans billing.creator with null members.
        parsed = plan(
            change(
                authoritative("roles/billing.creator"),
                ["create"],
                after=binding("roles/billing.creator", None),
            )
        )
        target = iam_diff.target_from_plan(parsed)
        live = iam_diff.Policy.from_json(
            {
                "bindings": [
                    {
                        "role": "roles/billing.creator",
                        "members": ["domain:example.com"],
                    }
                ]
            }
        )
        found = iam_diff.diff(live, target)
        assert target.bindings == {
            iam_diff.BindingKey("roles/billing.creator"): frozenset()
        }
        assert [str(grant) for grant in found.removed] == [
            "roles/billing.creator domain:example.com"
        ]

    @pytest.mark.parametrize(
        "after_unknown",
        [
            {"members": True},
            {"members": [False, True]},
            {"role": True},
            {"condition": [{"expression": True}]},
        ],
    )
    def test_unknown_values_fail_closed(self, after_unknown):
        address = authoritative(ORG_ADMIN)
        parsed = plan(
            change(
                address,
                ["update"],
                before=binding(ORG_ADMIN, ["user:a@example.com"]),
                after=binding(ORG_ADMIN, ["user:a@example.com"]),
                after_unknown=after_unknown,
            )
        )
        with pytest.raises(iam_diff.UnknownMembersError) as error:
            iam_diff.target_from_plan(parsed)
        assert error.value.address == address

    def test_unknown_audit_config_fails_closed(self):
        parsed = plan(
            change(
                "google_organization_iam_audit_config.organization",
                ["create"],
                after={"service": "allServices", "audit_log_config": []},
                after_unknown={"audit_log_config": True},
                kind=iam_diff.AUDIT_CONFIG_TYPE,
            )
        )
        with pytest.raises(iam_diff.UnknownMembersError):
            iam_diff.target_from_plan(parsed)

    def test_ignores_additive_members_and_unchanged_bindings(self):
        parsed = plan(
            change(
                'module.automation-tf-resman-r-sa.google_organization_iam_member.organization-roles["roles/viewer"]',
                ["create"],
                after={"role": "roles/viewer", "member": None},
                after_unknown={"member": True},
                kind="google_organization_iam_member",
            ),
            change(
                authoritative(ORG_ADMIN),
                ["no-op"],
                before=binding(ORG_ADMIN, ["user:a@example.com"]),
                after=binding(ORG_ADMIN, ["user:a@example.com"]),
            ),
            change(
                "data.google_organization_iam_binding.x",
                ["read"],
                after=binding("roles/browser", []),
                mode="data",
            ),
        )
        assert iam_diff.target_from_plan(parsed).empty
        # An unchanged binding still makes the deploy snapshot the policy.
        assert iam_diff.manages_iam(parsed)

    def test_manages_iam_ignores_members_and_reads(self):
        parsed = plan(
            change(
                'module.x.google_organization_iam_member.m["roles/viewer"]',
                ["create"],
                after={"role": "roles/viewer", "member": "user:a@example.com"},
                kind="google_organization_iam_member",
            ),
            change(
                "data.google_organization_iam_binding.x",
                ["read"],
                after=binding("roles/browser", []),
                mode="data",
            ),
        )
        assert not iam_diff.manages_iam(parsed)
        assert not iam_diff.manages_iam(plan())

    def test_delete_and_replace(self):
        old = {**CONDITION, "expression": "false"}
        parsed = plan(
            change(
                authoritative("roles/browser"),
                ["delete"],
                before=binding("roles/browser", ["domain:example.com"]),
            ),
            change(
                'module.organization.google_organization_iam_binding.bindings["x"]',
                ["delete", "create"],
                before=binding(DELEGATED, [STAGE0_SA], old),
                after=binding(DELEGATED, [STAGE0_SA], CONDITION),
            ),
        )
        target = iam_diff.target_from_plan(parsed)
        assert target.bindings == {
            iam_diff.BindingKey("roles/browser"): None,
            iam_diff.BindingKey(
                DELEGATED, iam_diff.Condition.from_json(old)
            ): None,
            iam_diff.BindingKey(
                DELEGATED, iam_diff.Condition.from_json(CONDITION)
            ): {STAGE0_SA},
        }

    def test_audit_config_create_overwrites_a_live_config(self):
        parsed = plan(
            change(
                "google_organization_iam_audit_config.organization",
                ["create"],
                after={
                    "service": "allServices",
                    "audit_log_config": [
                        {"log_type": "DATA_WRITE", "exempted_members": []},
                        {"log_type": "ADMIN_READ", "exempted_members": []},
                    ],
                },
                after_unknown={"etag": True, "id": True},
                kind=iam_diff.AUDIT_CONFIG_TYPE,
            )
        )
        target = iam_diff.target_from_plan(parsed)
        live = iam_diff.Policy.from_json(gcloud_policy())
        found = iam_diff.diff(live, target)
        assert target.audit_configs == {
            "allServices": (
                iam_diff.AuditLogConfig("ADMIN_READ"),
                iam_diff.AuditLogConfig("DATA_WRITE"),
            )
        }
        assert found.audit_overwrites == (
            iam_diff.AuditOverwrite(
                "allServices",
                live.audit_configs["allServices"],
                target.audit_configs["allServices"],
            ),
        )
        assert found.needs_review

    def test_audit_config_delete(self):
        parsed = plan(
            change(
                "google_organization_iam_audit_config.organization",
                ["delete"],
                before={"service": "allServices", "audit_log_config": []},
                kind=iam_diff.AUDIT_CONFIG_TYPE,
            )
        )
        target = iam_diff.target_from_plan(parsed)
        found = iam_diff.diff(
            iam_diff.Policy.from_json(gcloud_policy()), target
        )
        assert target.audit_configs == {"allServices": None}
        assert found.audit_overwrites[0].target is None


# Placeholder members that a shared org holds on 13 roles before Stage 0.
_FOREIGN_ROLES = tuple(f"roles/example.role{index}" for index in range(13))
_FOREIGN = tuple(
    (_FOREIGN_ROLES[index % 13], f"user:person{index}@example.com")
    for index in range(45)
)
_STAGE0_MEMBER = "group:gcp-organization-admins@example.com"


def _shared_org():
    bindings = {}
    for role, member in _FOREIGN:
        bindings.setdefault(role, []).append(member)
    return iam_diff.Policy.from_json(
        {
            "version": 1,
            "etag": conftest.ETAG,
            "bindings": [
                {"role": role, "members": members}
                for role, members in bindings.items()
            ],
        }
    )


def _stage0_plan(keep):
    """Returns a plan that sets the 13 roles, keeping the foreign grants."""
    changes = []
    for role in _FOREIGN_ROLES:
        members = [_STAGE0_MEMBER]
        if keep:
            members += [member for found, member in _FOREIGN if found == role]
        changes.append(
            change(
                authoritative(role),
                ["update"],
                before=binding(role, [m for r, m in _FOREIGN if r == role]),
                after=binding(role, members),
            )
        )
    return plan(*changes)


@pytest.mark.parametrize(
    ("keep", "removed", "kept"), [(False, 45, 0), (True, 0, 45)]
)
def test_shared_org_removals(keep, removed, kept):
    found = iam_diff.diff(
        _shared_org(), iam_diff.target_from_plan(_stage0_plan(keep))
    )
    assert len(found.removed) == removed
    assert len(found.kept_foreign) == kept
    assert len(found.added) == 13
    assert found.needs_review is bool(removed)
    assert {grant.key.role for grant in found.removed} <= set(_FOREIGN_ROLES)


class TestDiff:
    def test_deleted_members_never_count(self):
        live = iam_diff.Policy.from_json(
            {
                "bindings": [
                    {
                        "role": ORG_ADMIN,
                        "members": [
                            "deleted:user:gone@example.com?uid=1",
                            "user:a@example.com",
                        ],
                    }
                ]
            }
        )
        target = iam_diff.Target(
            {
                iam_diff.BindingKey(ORG_ADMIN): frozenset(
                    {
                        "user:a@example.com",
                        "deleted:user:gone@example.com?uid=1",
                    }
                ),
                iam_diff.BindingKey("roles/browser"): frozenset(
                    {"deleted:group:old@example.com?uid=2"}
                ),
            }
        )
        found = iam_diff.diff(live, target)
        assert found.removed == ()
        assert found.added == ()
        assert found.kept_foreign == (
            iam_diff.Grant(
                iam_diff.BindingKey(ORG_ADMIN), "user:a@example.com"
            ),
        )
        assert not found.needs_review

    def test_unmanaged_bindings_stay(self):
        live = iam_diff.Policy.from_json(gcloud_policy())
        found = iam_diff.diff(live, iam_diff.Target())
        assert found == iam_diff.Diff()

    def test_conditional_replacement(self):
        live = iam_diff.Policy.from_json(gcloud_policy())
        key = iam_diff.BindingKey(
            DELEGATED, iam_diff.Condition.from_json(CONDITION)
        )
        found = iam_diff.diff(
            live, iam_diff.Target({key: frozenset({"user:new@example.com"})})
        )
        assert found.conditional_replacements == (key,)
        assert [str(grant) for grant in found.removed] == [
            f"{DELEGATED} {STAGE0_SA} (condition {CONDITION['title']})"
        ]

    def test_deleted_binding_removes_every_member(self):
        live = iam_diff.Policy.from_json(gcloud_policy())
        found = iam_diff.diff(
            live, iam_diff.Target({iam_diff.BindingKey(ORG_ADMIN): None})
        )
        assert [grant.member for grant in found.removed] == [
            "group:gcp-organization-admins@example.com",
            "user:admin@example.com",
        ]

    def test_equal_audit_config_is_no_overwrite(self):
        live = iam_diff.Policy.from_json(gcloud_policy())
        target = iam_diff.Target(audit_configs=dict(live.audit_configs))
        assert iam_diff.diff(live, target).audit_overwrites == ()


class TestTargetFromPolicy:
    def test_round_trip_lists_every_change(self):
        before = iam_diff.Policy.from_json(gcloud_policy())
        after = iam_diff.Policy.from_json(
            {
                "bindings": [
                    {"role": ORG_ADMIN, "members": ["user:admin@example.com"]},
                    {
                        "role": "roles/browser",
                        "members": ["user:b@example.com"],
                    },
                ]
            }
        )
        found = iam_diff.diff(
            before, iam_diff.target_from_policy(after, keys_of=before)
        )
        assert [str(grant) for grant in found.removed] == [
            f"{DELEGATED} {STAGE0_SA} (condition {CONDITION['title']})",
            f"{ORG_ADMIN} group:gcp-organization-admins@example.com",
        ]
        assert [str(grant) for grant in found.added] == [
            "roles/browser user:b@example.com"
        ]
        assert [item.service for item in found.audit_overwrites] == [
            "allServices"
        ]
        # The same policy on both sides changes nothing.
        same = iam_diff.target_from_policy(before, keys_of=before)
        assert not iam_diff.diff(before, same).needs_review

    def test_rows_use_one_vocabulary(self):
        before = iam_diff.Policy.from_json(gcloud_policy())
        after = iam_diff.Policy.from_json(
            {"bindings": [{"role": "roles/browser", "members": ["user:b@x.y"]}]}
        )
        found = iam_diff.diff(
            before, iam_diff.target_from_policy(after, keys_of=before)
        )
        rows = iam_diff.rows(found, added=True)
        assert [row[0] for row in rows] == [
            "removed",
            "removed",
            "removed",
            "added",
            "audit",
            "rewrite",
        ]
        assert rows[-2][2] == "2 live log type configs are deleted"
        assert [row[0] for row in iam_diff.rows(found)].count("added") == 0


class TestTargetFromRepo:
    def test_overrides_merge_like_organization_tf(self, repo):
        overrides = {
            "iam": {
                ORG_ADMIN: ["user:kept@example.com"],
                "roles/viewer": ["user:viewer@example.com"],
            },
            "iam_by_principals": {
                "user:auditor@example.com": [
                    "roles/browser",
                    "roles/example.auditor",
                ]
            },
        }
        target = iam_diff.target_from_repo(
            repo, lambda holder: f"holder:{holder.kind}", overrides
        )
        # Repository targets never delete a binding.
        bindings = {
            key: members or set() for key, members in target.bindings.items()
        }
        assert (
            "user:kept@example.com" in bindings[iam_diff.BindingKey(ORG_ADMIN)]
        )
        assert "holder:group" in bindings[iam_diff.BindingKey(ORG_ADMIN)]
        assert bindings[iam_diff.BindingKey("roles/viewer")] == {
            "user:viewer@example.com"
        }
        assert (
            "user:auditor@example.com"
            in bindings[iam_diff.BindingKey("roles/browser")]
        )
        assert bindings[iam_diff.BindingKey("roles/example.auditor")] == {
            "user:auditor@example.com"
        }
        # iam_delete_roles keep no member at all.
        assert bindings[iam_diff.BindingKey("roles/billing.creator")] == set()
        assert target.audit_configs == {}

    def test_unresolved_holders_stay_out(self, repo):
        target = iam_diff.target_from_repo(repo, lambda holder: None, {})
        assert set(target.bindings) == {
            iam_diff.BindingKey(role) for role in repo.authoritative_bindings()
        }
        assert all(not members for members in target.bindings.values())

    def test_stage0_audit_configs(self, repo):
        configs = iam_diff.stage0_audit_configs(repo)
        assert configs == {
            "allServices": (
                iam_diff.AuditLogConfig("ADMIN_READ"),
                iam_diff.AuditLogConfig("DATA_READ"),
                iam_diff.AuditLogConfig("DATA_WRITE"),
            )
        }
        target = iam_diff.target_from_repo(
            repo, lambda holder: None, {}, audit_configs=configs
        )
        assert target.audit_configs == configs


@pytest.mark.parametrize(
    ("holder", "expected"),
    [
        (repo_lib.Holder(repo_lib.HolderKind.GROUP, "gcp-devops"), "group:x"),
        (
            repo_lib.Holder(repo_lib.HolderKind.SERVICE_ACCOUNT, "bootstrap-0"),
            "serviceAccount:tst-prod-bootstrap-0@tst-prod-iac-core-0"
            ".iam.gserviceaccount.com",
        ),
        (
            repo_lib.Holder(repo_lib.HolderKind.BOOTSTRAP_USER, ""),
            f"user:{conftest.USER}",
        ),
        (repo_lib.Holder(repo_lib.HolderKind.DOMAIN, ""), "domain:example.com"),
    ],
)
def test_resolve_holder_resolves_each_holder_kind(holder, expected):
    member = iam_diff.resolve_holder(
        holder,
        prefix="tst",
        groups={"gcp-devops": "group:x"},
        bootstrap_user=conftest.USER,
        domain="example.com",
    )
    assert member == expected


def test_resolve_holder_needs_the_inputs_that_name_the_member():
    holder = repo_lib.Holder(repo_lib.HolderKind.SERVICE_ACCOUNT, "bootstrap-0")
    member = iam_diff.resolve_holder(
        holder, prefix=None, groups={}, bootstrap_user=None, domain=None
    )
    assert member is None


@pytest.fixture
def env(tmp_path):
    return paths.EnvPaths(tmp_path / "envs" / "abc", "abc")


def _meta(reason="gate", taken=NOW):
    return iam_diff.SnapshotMeta(
        org_id=conftest.ORG_ID,
        reason=reason,
        taken=taken,
        plan="plans/0-s0.apply_final-20261029T120000Z.tfplan",
        engine_commit="0123abc",
        principal=conftest.USER,
    )


class TestSnapshots:
    def test_write_and_read(self, env):
        policy = iam_diff.Policy.from_json(gcloud_policy())
        path = iam_diff.write_snapshot(env, policy, _meta())
        assert path == env.iam_snapshots / "20261029T120000Z-gate.json"
        assert conftest.mode(env.iam_snapshots) == 0o700
        assert conftest.mode(path) == 0o600
        meta_path = env.iam_snapshots / "20261029T120000Z-gate.meta.json"
        assert conftest.mode(meta_path) == 0o600
        # The policy file stays in the gcloud shape for a manual restore,
        # without the etag, which setIamPolicy rejects once it is stale.
        expected = gcloud_policy()
        del expected["etag"]
        assert json.loads(path.read_text(encoding="utf-8")) == expected
        snapshot = iam_diff.read_snapshot(path)
        assert snapshot == iam_diff.Snapshot(
            path,
            dataclasses.replace(policy, etag=""),
            dataclasses.replace(_meta(), etag=conftest.ETAG),
        )

    def test_same_second_gets_a_counter(self, env):
        policy = iam_diff.Policy()
        first = iam_diff.write_snapshot(env, policy, _meta())
        second = iam_diff.write_snapshot(env, policy, _meta())
        assert first.name == "20261029T120000Z-gate.json"
        assert second.name == "20261029T120000Z-gate-1.json"
        latest = iam_diff.latest_snapshot(env)
        assert latest is not None
        assert latest.path == second

    def test_latest_snapshot(self, env):
        assert iam_diff.latest_snapshot(env) is None
        later = NOW + datetime.timedelta(minutes=5)
        iam_diff.write_snapshot(env, iam_diff.Policy(), _meta("grant", later))
        iam_diff.write_snapshot(env, iam_diff.Policy(), _meta("gate"))
        latest = iam_diff.latest_snapshot(env)
        assert latest is not None
        assert latest.meta is not None
        assert latest.path.name == "20261029T120500Z-grant.json"
        assert latest.meta.reason == "grant"

    @pytest.mark.parametrize("commit", ["0123abc", None])
    def test_snapshot_meta_records_the_engine(self, monkeypatch, commit):
        provenance = (
            None if commit is None else repo_lib.Provenance(commit, False)
        )
        monkeypatch.setattr(
            repo_lib.Repo, "provenance", lambda self: provenance
        )
        repository = repo_lib.Repo(conftest.REPO_ROOT)
        plan = "plans/0-s0.apply_final-20261029T120000Z.tfplan"
        meta = iam_diff.snapshot_meta(
            repository,
            org_id=conftest.ORG_ID,
            reason="gate",
            taken=NOW,
            principal=conftest.USER,
            plan=pathlib.Path(plan),
        )
        assert meta == dataclasses.replace(_meta(), engine_commit=commit)

    def test_reason_must_be_a_slug(self, env):
        with pytest.raises(ValueError, match="slug"):
            iam_diff.write_snapshot(env, iam_diff.Policy(), _meta("../up"))

    def test_gcloud_file_without_metadata(self, tmp_path):
        path = tmp_path / "policy.json"
        path.write_text(json.dumps(gcloud_policy()), encoding="utf-8")
        snapshot = iam_diff.read_snapshot(path)
        assert snapshot.meta is None
        assert snapshot.policy.etag == conftest.ETAG

    @pytest.mark.parametrize(
        "text",
        [
            "{",
            "[]",
            '{"bindings": 1}',
            '{"version": {"a": 1}}',
            '{"bindings": [{"role": "r", "condition": "c"}]}',
        ],
    )
    def test_malformed_snapshot(self, tmp_path, text):
        path = tmp_path / "policy.json"
        path.write_text(text, encoding="utf-8")
        with pytest.raises(iam_diff.SnapshotError, match="Cannot read"):
            iam_diff.read_snapshot(path)

    def test_malformed_metadata(self, env):
        path = iam_diff.write_snapshot(env, iam_diff.Policy(), _meta())
        meta_path = path.with_name(path.name.replace(".json", ".meta.json"))
        meta_path.write_text('{"org_id": "1"}', encoding="utf-8")
        with pytest.raises(iam_diff.SnapshotError):
            iam_diff.read_snapshot(path)

    def test_missing_snapshot(self, tmp_path):
        with pytest.raises(iam_diff.SnapshotError):
            iam_diff.read_snapshot(tmp_path / "missing.json")
