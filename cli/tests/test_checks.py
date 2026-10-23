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

"""Tests for the individual preflight checks."""

import pytest

import conftest
from stellar_engine.gcp import api
from stellar_engine.preflight import checks
from stellar_engine.preflight import result

Status = result.Status


def by_id(results):
    return {item.check_id: item for item in results}


SA = "sa@example-project.iam.gserviceaccount.com"


def remedy(item):
    return item.remedy or ""


def statuses(results):
    return {item.check_id: item.status for item in results}


class TestTools:
    def test_pass(self, make_ctx):
        found = statuses(checks.check_tools(make_ctx()))
        assert found == {
            "tools.terraform": Status.PASS,
            "tools.jq": Status.PASS,
            "tools.gcloud": Status.PASS,
        }

    @pytest.mark.parametrize("installed", [None, "1.8.1"])
    def test_terraform_missing_or_old(self, make_ctx, local_tools, installed):
        local_tools.terraform = installed
        found = by_id(checks.check_tools(make_ctx()))
        assert found["tools.terraform"].status == Status.FAIL
        assert "1.10.2" in remedy(found["tools.terraform"])

    def test_gcloud_missing(self, make_ctx, local_tools):
        local_tools.gcloud = None
        found = statuses(checks.check_tools(make_ctx()))
        assert found["tools.gcloud"] == Status.FAIL


class TestIdentity:
    def test_user_pass(self, make_ctx):
        ctx = make_ctx()
        found = statuses(checks.check_identity(ctx))
        assert set(found.values()) == {Status.PASS}
        assert ctx.principal.email == conftest.USER

    def test_mismatch_fails(self, make_ctx, local_tools):
        local_tools.account = "other@example.com"
        found = by_id(checks.check_identity(make_ctx()))
        assert found["identity.match"].status == Status.FAIL
        assert "other@example.com" in found["identity.match"].detail

    def test_no_gcloud_account(self, make_ctx, local_tools):
        local_tools.account = None
        found = statuses(checks.check_identity(make_ctx()))
        assert found["identity.gcloud"] == Status.FAIL
        assert "identity.match" not in found

    def test_user_is_default_bootstrap_user(self, make_ctx):
        found = by_id(checks.check_identity(make_ctx()))
        bootstrap = found["identity.bootstrap_user"]
        assert bootstrap.status == Status.PASS
        assert f"-var bootstrap_user={conftest.USER}" in bootstrap.detail

    def test_service_account_without_bootstrap_user_fails(
        self, make_ctx, cloud, local_tools
    ):
        cloud.principal = api.Principal(SA, api.PrincipalKind.SERVICE_ACCOUNT)
        local_tools.account = SA
        found = by_id(checks.check_identity(make_ctx()))
        bootstrap = found["identity.bootstrap_user"]
        assert bootstrap.status == Status.FAIL
        assert "--bootstrap-user" in remedy(bootstrap)

    def test_service_account_with_bootstrap_user_passes(
        self, make_ctx, cloud, local_tools
    ):
        cloud.principal = api.Principal(SA, api.PrincipalKind.SERVICE_ACCOUNT)
        local_tools.account = SA
        ctx = make_ctx(bootstrap_user="admin@example.com")
        bootstrap = by_id(checks.check_identity(ctx))["identity.bootstrap_user"]
        assert bootstrap.status == Status.PASS
        assert "-var bootstrap_user=admin@example.com" in bootstrap.detail
        assert f"Terraform runs as {SA}" in bootstrap.detail

    def test_service_account_as_bootstrap_user_fails(self, make_ctx):
        ctx = make_ctx(bootstrap_user=SA)
        bootstrap = by_id(checks.check_identity(ctx))["identity.bootstrap_user"]
        assert bootstrap.status == Status.FAIL

    def test_missing_credentials(self, make_ctx, cloud):
        cloud.principal = api.CredentialsError("no ADC")
        found = by_id(checks.check_identity(make_ctx()))
        assert found["identity.adc"].status == Status.FAIL
        assert "application-default login" in remedy(found["identity.adc"])
        assert "identity.bootstrap_user" not in found

    def test_impersonation_warns(self, make_ctx):
        environ = {"GOOGLE_IMPERSONATE_SERVICE_ACCOUNT": "x@y.iam.com"}
        found = by_id(checks.check_identity(make_ctx(environ=environ)))
        assert found["identity.impersonation"].status == Status.WARN
        assert "unset" in remedy(found["identity.impersonation"])


class TestOrganization:
    def test_pass_with_matching_values(self, make_ctx):
        ctx = make_ctx()
        found = statuses(checks.check_organization(ctx))
        assert found == {
            "org.access": Status.PASS,
            "org.domain": Status.PASS,
            "org.customer_id": Status.PASS,
        }
        assert ctx.org.org_id == conftest.ORG_ID

    def test_discovers_single_org(self, make_ctx):
        ctx = make_ctx(org_id=None)
        checks.check_organization(ctx)
        assert ctx.org.org_id == conftest.ORG_ID

    def test_multiple_orgs_fail(self, make_ctx, cloud):
        cloud.orgs = [
            api.Organization("1", "a.example", "C1"),
            api.Organization("2", "b.example", "C2"),
        ]
        ctx = make_ctx(org_id=None)
        found = by_id(checks.check_organization(ctx))
        assert found["org.access"].status == Status.FAIL
        assert "--org" in remedy(found["org.access"])
        assert ctx.org is None

    def test_unknown_org_fails(self, make_ctx):
        found = statuses(checks.check_organization(make_ctx(org_id="999")))
        assert found == {"org.access": Status.FAIL}

    def test_denied(self, make_ctx, cloud):
        cloud.orgs = api.AccessDeniedError("nope")
        found = by_id(checks.check_organization(make_ctx()))
        assert found["org.access"].status == Status.FAIL
        assert "nope" in found["org.access"].detail

    def test_domain_mismatch(self, make_ctx):
        found = by_id(checks.check_organization(make_ctx(domain="other.com")))
        assert found["org.domain"].status == Status.FAIL


def resolved(make_ctx, **overrides):
    ctx = make_ctx(**overrides)
    checks.check_organization(ctx)
    return ctx


class TestIamRoles:
    def test_all_granted(self, make_ctx, repo, cloud):
        found = statuses(checks.check_iam_roles(resolved(make_ctx)))
        assert len(found) == len(repo.required_roles())
        assert set(found.values()) == {Status.PASS}
        assert len(cloud.calls) == 1

    def test_missing_permission_fails(self, make_ctx, cloud):
        cloud.denied_org_perms = {"roles/owner.permission"}
        found = by_id(checks.check_iam_roles(resolved(make_ctx)))
        assert found["iam.roles/owner"].status == Status.FAIL
        assert "setIAM.sh" in remedy(found["iam.roles/owner"])

    def test_singular_permission_wording(self, make_ctx, cloud):
        found = by_id(checks.check_iam_roles(resolved(make_ctx)))
        detail = found["iam.roles/owner"].detail
        assert "holds the only testable permission on" in detail

    def test_untestable_role_warns(self, make_ctx, cloud):
        cloud.org_testable = set()
        found = statuses(
            checks.check_iam_roles(resolved(make_ctx, billing_account=None))
        )
        assert set(found.values()) == {Status.WARN}

    def test_billing_admin_tested_on_billing_account(self, make_ctx, cloud):
        cloud.denied_billing_perms = {"roles/billing.admin.permission"}
        found = by_id(checks.check_iam_roles(resolved(make_ctx)))
        billing = found["iam.roles/billing.admin"]
        assert billing.status == Status.FAIL
        assert "billing account" in billing.detail

    def test_billing_admin_on_org_without_account(self, make_ctx, cloud):
        cloud.denied_billing_perms = {"roles/billing.admin.permission"}
        found = by_id(
            checks.check_iam_roles(resolved(make_ctx, billing_account=None))
        )
        assert found["iam.roles/billing.admin"].status == Status.PASS
        assert "organization" in found["iam.roles/billing.admin"].detail

    def test_billing_admin_not_required_without_billing_iam(
        self, make_ctx, cloud
    ):
        cloud.denied_billing_perms = {"roles/billing.admin.permission"}
        found = statuses(
            checks.check_iam_roles(resolved(make_ctx, billing_no_iam=True))
        )
        assert "iam.roles/billing.admin" not in found
        assert set(found.values()) == {Status.PASS}

    def test_billing_api_disabled(self, make_ctx, cloud):
        cloud.billing_perm_error = api.ApiDisabledError(
            "cloudbilling.googleapis.com", "123"
        )
        found = by_id(checks.check_iam_roles(resolved(make_ctx)))
        billing = found["iam.roles/billing.admin"]
        assert billing.status == Status.FAIL
        assert "gcloud services enable cloudbilling" in billing.detail

    def test_skipped_without_org(self, make_ctx):
        found = statuses(checks.check_iam_roles(make_ctx()))
        assert found == {"iam.roles": Status.SKIP}


class TestBilling:
    def test_pass(self, make_ctx):
        found = statuses(checks.check_billing(make_ctx()))
        assert found == {
            "billing.account": Status.PASS,
            "billing.project": Status.PASS,
        }

    def test_closed_account(self, make_ctx, cloud):
        cloud.billing_account = api.BillingAccount(conftest.BILLING, False)
        found = by_id(checks.check_billing(make_ctx()))
        assert found["billing.account"].status == Status.FAIL
        assert "closed" in found["billing.account"].detail

    def test_missing_account(self, make_ctx, cloud):
        cloud.billing_account = None
        found = by_id(checks.check_billing(make_ctx()))
        assert found["billing.account"].status == Status.FAIL
        assert "gcloud billing accounts list" in remedy(
            found["billing.account"]
        )

    def test_unreadable_account_has_no_id_hint(self, make_ctx, cloud):
        cloud.billing_account = api.ApiDisabledError(
            "cloudbilling.googleapis.com", "123"
        )
        account = by_id(checks.check_billing(make_ctx()))["billing.account"]
        assert account.status == Status.FAIL
        assert "gcloud services enable cloudbilling" in account.detail
        assert account.remedy is None

    def test_project_on_other_account(self, make_ctx, cloud):
        cloud.project_link = api.ProjectBilling("111111-222222-333333", True)
        found = by_id(checks.check_billing(make_ctx()))
        assert found["billing.project"].status == Status.FAIL
        assert "gcloud billing projects link" in remedy(
            found["billing.project"]
        )

    def test_project_unbilled(self, make_ctx, cloud):
        cloud.project_link = api.ProjectBilling(None, False)
        found = by_id(checks.check_billing(make_ctx()))
        assert "no billing account" in found["billing.project"].detail

    def test_skipped(self, make_ctx):
        found = statuses(checks.check_billing(make_ctx(billing_account=None)))
        assert found == {"billing.account": Status.SKIP}

    def test_link_checked_without_billing_iam(self, make_ctx):
        found = by_id(checks.check_billing(make_ctx(billing_no_iam=True)))
        assert found["billing.link"].status == Status.PASS
        assert list(found) == [
            "billing.account",
            "billing.link",
            "billing.project",
        ]

    def test_link_not_checked_with_billing_iam(self, make_ctx):
        found = statuses(checks.check_billing(make_ctx()))
        assert "billing.link" not in found

    def test_link_denied(self, make_ctx, cloud):
        cloud.billing_account = api.AccessDeniedError("denied")
        cloud.denied_billing_perms = {checks.BILLING_LINK_PERMISSION}
        found = by_id(checks.check_billing(make_ctx(billing_no_iam=True)))
        link = found["billing.link"]
        assert link.status == Status.FAIL
        assert checks.BILLING_LINK_PERMISSION in link.detail
        assert "roles/billing.user" in remedy(link)

    def test_link_untestable(self, make_ctx, cloud):
        cloud.billing_perm_error = api.ApiDisabledError(
            "cloudbilling.googleapis.com", "123"
        )
        found = by_id(checks.check_billing(make_ctx(billing_no_iam=True)))
        assert found["billing.link"].status == Status.FAIL
        assert "Cannot test project linking" in found["billing.link"].detail


class TestProject:
    def test_pass(self, make_ctx):
        found = statuses(checks.check_project(make_ctx()))
        assert found == {
            "project.state": Status.PASS,
            "project.apis": Status.PASS,
        }

    def test_missing_monitoring_api(self, make_ctx, repo, cloud):
        cloud.services = set(repo.required_apis())
        found = by_id(checks.check_project(make_ctx()))
        apis = found["project.apis"]
        assert apis.status == Status.FAIL
        assert apis.detail == "Not enabled: monitoring.googleapis.com."
        assert "gcloud services enable monitoring.googleapis.com" in (
            remedy(apis)
        )

    @pytest.mark.parametrize(
        "state", [None, "DELETE_REQUESTED", api.AccessDeniedError("x")]
    )
    def test_project_unusable(self, make_ctx, cloud, state):
        cloud.projects = {conftest.PROJECT: state}
        found = statuses(checks.check_project(make_ctx()))
        assert found == {"project.state": Status.FAIL}


class TestGroups:
    def test_all_exist(self, make_ctx, repo):
        found = statuses(checks.check_groups(make_ctx()))
        expected = len(set(repo.default_groups().values()))
        assert len(found) == expected
        assert set(found.values()) == {Status.PASS}

    def test_missing_group(self, make_ctx, cloud):
        cloud.groups = {"gcp-devops@example.com"}
        found = statuses(checks.check_groups(make_ctx()))
        assert found["groups.gcp-devops@example.com"] == Status.PASS
        assert found["groups.gcp-security-admins@example.com"] == Status.FAIL

    def test_override_and_principal(self, make_ctx, cloud):
        cloud.groups = set()
        ctx = make_ctx(
            groups={
                "gcp-devops": "platform-ops",
                "gcp-billing-admins": "group:billing@example.org",
                "gcp-security-admins": "serviceAccount:x@example.com",
            }
        )
        found = statuses(checks.check_groups(ctx))
        # Like main.tf, a bare name becomes a group in the org domain, and a
        # value with a scheme is used as an IAM principal unchanged.
        assert "groups.platform-ops@example.com" in found
        assert "groups.billing@example.org" in found
        assert not any("serviceAccount" in key for key in found)

    def test_denied_becomes_manual(self, make_ctx, cloud):
        cloud.groups = api.ApiDisabledError("cloudidentity.googleapis.com", "1")
        found = by_id(checks.check_groups(make_ctx()))
        assert found["groups"].status == Status.MANUAL
        assert "cloudidentity" in found["groups"].detail

    def test_domain_from_org(self, make_ctx):
        ctx = resolved(make_ctx, domain=None)
        found = statuses(checks.check_groups(ctx))
        assert "groups.gcp-devops@example.com" in found


class TestNaming:
    def test_pass(self, make_ctx):
        found = statuses(checks.check_naming(resolved(make_ctx)))
        assert set(found.values()) == {Status.PASS}
        assert "naming.folder" in found

    @pytest.mark.parametrize(
        ("regime", "region", "expected"),
        [
            ("IL5", "us-east4", Status.PASS),
            ("IL5", "us-central1", Status.PASS),
            ("IL5", "us-south1", Status.FAIL),
            ("IL4", "us-east5", Status.FAIL),
            ("FEDRAMP_HIGH", "us-south1", Status.PASS),
            ("FEDRAMP_MODERATE", "europe-west1", Status.FAIL),
            ("COMPLIANCE_REGIME_UNSPECIFIED", "us-east4", Status.PASS),
            ("COMPLIANCE_REGIME_UNSPECIFIED", "us", Status.FAIL),
        ],
    )
    def test_region(self, make_ctx, regime, region, expected):
        ctx = make_ctx(regime=regime, region=region)
        found = statuses(checks.check_naming(ctx))
        assert found["naming.region"] == expected

    @pytest.mark.parametrize(
        "prefix", ["toolong8", "1abc", "Abc", "ab_c", "abc-"]
    )
    def test_invalid_prefix(self, make_ctx, prefix):
        found = statuses(checks.check_naming(make_ctx(prefix=prefix)))
        assert found["naming.prefix"] == Status.FAIL
        assert "naming.projects" not in found

    def test_collisions_fail(self, make_ctx, cloud):
        cloud.projects["tst-prod-iac-core-0"] = "ACTIVE"
        cloud.buckets = {"tst-prod-iac-core-outputs-0"}
        cloud.folders = ["folders/1"]
        found = by_id(checks.check_naming(resolved(make_ctx)))
        for check_id in ("naming.projects", "naming.buckets", "naming.folder"):
            assert found[check_id].status == Status.FAIL
        assert "tst-prod-iac-core-0" in found["naming.projects"].detail
        assert "--redeploy" in remedy(found["naming.projects"])

    def test_collisions_warn_on_redeploy(self, make_ctx, cloud):
        cloud.projects["tst-prod-iac-core-0"] = "ACTIVE"
        found = statuses(checks.check_naming(resolved(make_ctx, redeploy=True)))
        assert found["naming.projects"] == Status.WARN

    def test_pass_notes_invisible_projects(self, make_ctx):
        found = by_id(checks.check_naming(resolved(make_ctx)))
        assert "outside this identity's view" in found["naming.projects"].detail

    def test_soft_deleted_project_fails_even_on_redeploy(self, make_ctx, cloud):
        cloud.projects["tst-prod-audit-logs-0"] = "DELETE_REQUESTED"
        ctx = resolved(make_ctx, redeploy=True)
        found = by_id(checks.check_naming(ctx))
        deleted = found["naming.deleted_projects"]
        assert deleted.status == Status.FAIL
        assert "tst-prod-audit-logs-0" in deleted.detail
        assert "gcloud projects undelete tst-prod-audit-logs-0" in remedy(
            deleted
        )
        assert found["naming.projects"].status == Status.PASS

    def test_no_soft_deleted_projects_pass(self, make_ctx):
        found = statuses(checks.check_naming(resolved(make_ctx)))
        assert found["naming.deleted_projects"] == Status.PASS

    def test_unrelated_prefix_projects_pass(self, make_ctx, cloud):
        cloud.projects["tst-bootstrap"] = "ACTIVE"
        found = statuses(checks.check_naming(resolved(make_ctx)))
        assert found["naming.projects"] == Status.PASS

    def test_disabled_api_warns_and_keeps_other_results(self, make_ctx, cloud):
        cloud.projects["tst-prod-iac-core-0"] = api.ApiDisabledError(
            "cloudresourcemanager.googleapis.com", "1"
        )
        found = statuses(checks.check_naming(resolved(make_ctx)))
        assert found["naming.projects"] == Status.WARN
        assert found["naming.buckets"] == Status.PASS
        assert found["naming.region"] == Status.PASS

    def test_skips_without_inputs(self, make_ctx):
        found = statuses(
            checks.check_naming(make_ctx(prefix=None, region=None))
        )
        assert found == {
            "naming.region": Status.SKIP,
            "naming.prefix": Status.SKIP,
        }


class TestSharedOrg:
    def test_clean_org(self, make_ctx):
        found = statuses(checks.check_shared_org(resolved(make_ctx)))
        assert found == {
            "shared.resources": Status.PASS,
            "shared.iam": Status.PASS,
        }

    def test_existing_org_resources_warn(self, make_ctx, cloud):
        cloud.custom_roles = {"tagViewer"}
        cloud.constraints = {"custom.kmsRotation"}
        cloud.sinks = {"audit-logs"}
        found = by_id(checks.check_shared_org(resolved(make_ctx)))
        detail = found["shared.resources"].detail
        assert found["shared.resources"].status == Status.WARN
        for name in ("tagViewer", "custom.kmsRotation", "audit-logs"):
            assert name in detail

    def test_foreign_grants_on_authoritative_roles_warn(self, make_ctx, cloud):
        prefix_sa = (
            "serviceAccount:tst-prod-bootstrap-0@"
            "tst-prod-iac-core-0.iam.gserviceaccount.com"
        )
        cloud.bindings = [
            api.IamBinding(
                "roles/resourcemanager.organizationAdmin",
                (
                    "group:gcp-organization-admins@example.com",
                    f"user:{conftest.USER}",
                    prefix_sa,
                    "user:someone-else@example.com",
                    "deleted:user:gone@example.com",
                ),
            ),
            api.IamBinding("roles/browser", ("domain:example.com",)),
            api.IamBinding("roles/viewer", ("user:unmanaged@example.com",)),
        ]
        ctx = resolved(make_ctx)
        checks.check_identity(ctx)
        found = by_id(checks.check_shared_org(ctx))
        iam = found["shared.iam"]
        assert iam.status == Status.WARN
        assert "removes 1 existing grants" in iam.detail
        assert "someone-else@example.com" in iam.detail
        assert "unmanaged" not in iam.detail

    @pytest.mark.parametrize(
        ("role", "member", "removed"),
        [
            # setIAM.sh grants these directly, but bootstrap_user keeps only
            # five roles, so the first apply removes the others.
            ("roles/assuredworkloads.admin", f"user:{conftest.USER}", True),
            ("roles/axt.admin", f"user:{conftest.USER}", True),
            (
                "roles/resourcemanager.organizationAdmin",
                f"user:{conftest.USER}",
                False,
            ),
            # iam_delete_roles empties billing.creator entirely.
            (
                "roles/billing.creator",
                "group:gcp-organization-admins@example.com",
                True,
            ),
            # gcp-support resolves to gcp-devops, kept only on its roles.
            ("roles/logging.viewer", "group:gcp-devops@example.com", False),
            (
                "roles/resourcemanager.organizationAdmin",
                "group:gcp-devops@example.com",
                True,
            ),
            ("roles/browser", "domain:example.com", False),
            ("roles/axt.admin", "domain:example.com", True),
            (
                "roles/logging.admin",
                "serviceAccount:tst-prod-resman-0@"
                "tst-prod-iac-core-0.iam.gserviceaccount.com",
                False,
            ),
            (
                "roles/resourcemanager.organizationAdmin",
                "serviceAccount:tst-prod-resman-0@"
                "tst-prod-iac-core-0.iam.gserviceaccount.com",
                True,
            ),
        ],
    )
    def test_per_role_semantics(self, make_ctx, cloud, role, member, removed):
        cloud.bindings = [api.IamBinding(role, (member,))]
        ctx = resolved(make_ctx)
        checks.check_identity(ctx)
        iam = by_id(checks.check_shared_org(ctx))["shared.iam"]
        assert (iam.status == Status.WARN) is removed
        assert (member in iam.detail) is removed

    def test_named_bootstrap_user_is_kept(self, make_ctx, cloud):
        cloud.principal = api.Principal(SA, api.PrincipalKind.SERVICE_ACCOUNT)
        cloud.bindings = [
            api.IamBinding(
                "roles/resourcemanager.organizationAdmin",
                ("user:admin@example.com", f"serviceAccount:{SA}"),
            )
        ]
        ctx = resolved(make_ctx, bootstrap_user="admin@example.com")
        checks.check_identity(ctx)
        iam = by_id(checks.check_shared_org(ctx))["shared.iam"]
        assert "admin@example.com" not in iam.detail
        assert SA in iam.detail

    def test_policy_denied_warns(self, make_ctx, cloud):
        cloud.bindings = api.AccessDeniedError("nope")
        found = statuses(checks.check_shared_org(resolved(make_ctx)))
        assert found["shared.iam"] == Status.WARN

    def test_skipped_without_org(self, make_ctx):
        found = statuses(checks.check_shared_org(make_ctx()))
        assert found == {"shared": Status.SKIP}


def test_role_lookup_error_is_reported(make_ctx, cloud):
    def broken(full_resource_name):
        raise api.CloudError("boom")

    cloud.testable_permissions = broken
    found = by_id(checks.check_iam_roles(resolved(make_ctx)))
    assert found["iam.roles"].status == Status.FAIL
    assert "boom" in found["iam.roles"].detail


class TestToolsExtras:
    def test_missing_jq_warns(self, make_ctx, local_tools):
        local_tools.jq = None
        found = statuses(checks.check_tools(make_ctx()))
        assert found["tools.jq"] == Status.WARN

    def test_wrong_active_project_warns(self, make_ctx, local_tools):
        local_tools.project = "something-else"
        found = by_id(checks.check_identity(make_ctx()))
        project = found["identity.project"]
        assert project.status == Status.WARN
        assert f"gcloud config set project {conftest.PROJECT}" in remedy(
            project
        )


def test_manual_items(make_ctx):
    found = statuses(checks.check_manual(make_ctx()))
    assert found == {
        "manual.super_admin": Status.MANUAL,
        "manual.access_transparency": Status.MANUAL,
        "manual.quota": Status.MANUAL,
    }
