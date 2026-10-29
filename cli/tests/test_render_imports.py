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

"""Tests for the Terraform import blocks of pre-created resources."""

import hcl2
import pytest

import conftest
import helpers
from stellar_engine import workspace
from stellar_engine.render import imports
from stellar_engine.render import writer


def _with_imports(name="lab", stage="0-bootstrap", entries=None, **updates):
    data = {stage: entries} if entries is not None else {}
    return helpers.load_fixture(name, imports=data, **updates)


def test_filename():
    assert imports.filename("0") == "0-bootstrap-imports.tf"
    assert imports.filename("1-resman") == "1-resman-imports.tf"
    with pytest.raises(ValueError, match="2-networking"):
        imports.filename("2-networking")


def test_dumps_snapshot(snapshot):
    answers = helpers.load_fixture("lab")
    text = imports.dumps(
        answers.imports["0-bootstrap"],
        imports.header("0-bootstrap", answers.prefix),
    )
    assert text == snapshot


_POLICIES = [
    "storage.uniformBucketLevelAccess",
    "iam.allowedPolicyMemberDomains",
    "compute.managed.restrictProtocolForwardingCreationForTypes",
]


def test_text_with_org_policies_snapshot(snapshot):
    answers = helpers.load_fixture("lab", existing_org_policies=_POLICIES)
    assert imports.text(answers, "0") == snapshot


def test_text_without_org_policies_matches_dumps():
    answers = helpers.load_fixture("lab")
    assert imports.text(answers, "0-bootstrap") == imports.dumps(
        answers.imports["0-bootstrap"], imports.header("0", answers.prefix)
    )


def test_text_with_only_org_policies():
    answers = _with_imports(existing_org_policies=_POLICIES)
    text = imports.text(answers, "0")
    assert text.startswith(
        "# stellar render writes this file from envs/lab1/answers.yaml "
        "existing_org_policies.\n"
    )
    parsed = hcl2.loads(text)
    assert len(parsed["import"]) == 1
    block = parsed["import"][0]
    assert "google_org_policy_policy.default[each.key]" in block["to"]
    assert "var.bootstrap_user == null" in block["for_each"]
    names = parsed["locals"][0]["stellar_existing_org_policies"]
    assert [name.strip('"') for name in names] == sorted(_POLICIES)
    assert (
        "contains(keys(local.org_policies), name)"
        in (parsed["locals"][0]["stellar_org_policy_imports"])
    )


def test_text_puts_org_policies_only_in_stage0():
    answers = _with_imports(
        stage="1-resman",
        entries={"google_project.plain": "p"},
        existing_org_policies=_POLICIES,
    )
    resman = imports.text(answers, "1-resman")
    assert "org_policy" not in resman
    assert "existing_org_policies" not in resman
    assert imports.text(_with_imports(stage="1-resman"), "1") == ""


def test_dumps_sorts_and_quotes():
    text = imports.dumps(
        {
            conftest.LOG_EXPORT_ADDRESS: "b",
            conftest.AUTOMATION_ADDRESS: 'a"${x}',
        },
        ["# header"],
    )
    assert text == (
        "# header\n\n"
        "import {\n"
        f"  to = {conftest.AUTOMATION_ADDRESS}\n"
        '  id = "a\\"$${x}"\n'
        "}\n\n"
        "import {\n"
        f"  to = {conftest.LOG_EXPORT_ADDRESS}\n"
        '  id = "b"\n'
        "}\n"
    )


def test_dumps_parses_as_hcl():
    parsed = hcl2.loads(
        imports.dumps(
            {
                conftest.BILLING_EXPORT_ADDRESS: "p",
                conftest.AUTOMATION_ADDRESS: "q",
            },
            [],
        )
    )
    assert [block["id"] for block in parsed["import"]] == ['"q"', '"p"']


def test_dumps_empty():
    assert imports.dumps({}, ["# header"]) == ""


@pytest.mark.parametrize(
    "address",
    [
        "google_project",
        "module.automation-project",
        "module.x.data.google_project.p",
        'google_project.project["a"] extra',
        "google_project.project[0",
        "",
    ],
)
def test_dumps_rejects_invalid_address(address):
    with pytest.raises(imports.ImportBlockError):
        imports.dumps({address: "id"}, [])


def test_valid_address_forms(repo):
    answers = _with_imports(
        entries={
            conftest.BILLING_EXPORT_ADDRESS: "p",
            'module.a["k"].google_project.project["x"]': "q",
            "google_project.plain": "r",
        },
        billing={"account_id": conftest.BILLING},
    )
    assert imports.dumps(answers.imports["0-bootstrap"], [])
    assert imports.warnings(answers, "0", repo) == []


def test_warns_on_billing_export_without_billing_iam(repo):
    answers = _with_imports(
        entries={conftest.BILLING_EXPORT_ADDRESS: "lab1-prod-billing-exp-0"}
    )
    assert answers.billing.no_iam
    found = imports.warnings(answers, "0-bootstrap", repo)
    assert len(found) == 1
    assert found[0].startswith(
        f"imports.0-bootstrap: {conftest.BILLING_EXPORT_ADDRESS} targets"
    )
    assert "billing.no_iam" in found[0]


def test_warns_on_billing_export_outside_the_org(repo):
    answers = _with_imports(
        "il4",
        entries={conftest.BILLING_EXPORT_ADDRESS: "il4-prod-billing-exp-0"},
    )
    assert len(imports.warnings(answers, "0", repo)) == 1


def test_no_warning_when_billing_export_exists(repo):
    answers = _with_imports(
        entries={conftest.BILLING_EXPORT_ADDRESS: "lab1-prod-billing-exp-0"},
        billing={"account_id": conftest.BILLING},
    )
    assert imports.warnings(answers, "0", repo) == []


def test_warns_on_workload_without_a_regime(repo):
    answers = _with_imports(
        entries={
            repo.assured_workload().address: (
                f"organizations/{conftest.ORG_ID}/locations/us-east4/"
                "workloads/abc123"
            )
        },
        billing={"account_id": conftest.BILLING},
    ).model_copy(deep=True)
    answers.compliance.regime = "COMPLIANCE_REGIME_UNSPECIFIED"
    (found,) = imports.warnings(answers, "0", repo)
    assert "Assured Workloads workload" in found
    assert "COMPLIANCE_REGIME_UNSPECIFIED" in found


def test_no_warning_for_other_stages(repo):
    answers = _with_imports(
        stage="1-resman",
        entries={conftest.BILLING_EXPORT_ADDRESS: "lab1-prod-billing-exp-0"},
    )
    assert imports.warnings(answers, "1", repo) == []


def test_write_creates_file(tmp_path):
    answers = helpers.load_fixture("lab")
    assert imports.write(tmp_path, "0", answers) == writer.Outcome.CREATED
    path = tmp_path / "0-bootstrap-imports.tf"
    assert conftest.mode(path) == 0o644
    text = path.read_text(encoding="utf-8")
    assert text == imports.dumps(
        answers.imports["0-bootstrap"], imports.header("0", "lab1")
    )
    assert text.startswith(
        "# stellar render writes this file from envs/lab1/answers.yaml "
        "imports.0-bootstrap.\n"
    )


def test_write_replaces_generated_file(tmp_path):
    lab = helpers.load_fixture("lab")
    imports.write(tmp_path, "0", lab)
    assert imports.write(tmp_path, "0", lab) == writer.Outcome.UNCHANGED
    answers = _with_imports(entries={conftest.AUTOMATION_ADDRESS: "other-id"})
    assert imports.write(tmp_path, "0", answers) == writer.Outcome.UPDATED
    path = tmp_path / imports.filename("0")
    assert '"other-id"' in path.read_text(encoding="utf-8")
    assert conftest.LOG_EXPORT_ADDRESS not in path.read_text(encoding="utf-8")


def test_write_removes_generated_file_when_empty(tmp_path):
    imports.write(tmp_path, "0", helpers.load_fixture("lab"))
    path = tmp_path / imports.filename("0")
    assert imports.write(tmp_path, "0", _with_imports()) == (
        writer.Outcome.REMOVED
    )
    assert not path.exists()
    # Nothing to remove the second time.
    assert imports.write(tmp_path, "0", _with_imports()) is None


def test_write_with_only_org_policies(tmp_path):
    answers = _with_imports(existing_org_policies=_POLICIES)
    assert imports.write(tmp_path, "0", answers) == writer.Outcome.CREATED
    path = tmp_path / imports.filename("0")
    assert path.read_text(encoding="utf-8") == imports.text(answers, "0")
    # Clearing the policies removes the generated file again.
    assert imports.write(tmp_path, "0", _with_imports()) == (
        writer.Outcome.REMOVED
    )
    assert not path.exists()


def test_write_drops_org_policies_and_keeps_projects(tmp_path):
    with_policies = helpers.load_fixture("lab", existing_org_policies=_POLICIES)
    imports.write(tmp_path, "0", with_policies)
    path = tmp_path / imports.filename("0")
    assert "stellar_existing_org_policies" in path.read_text(encoding="utf-8")
    imports.write(tmp_path, "0", helpers.load_fixture("lab"))
    text = path.read_text(encoding="utf-8")
    assert "stellar_existing_org_policies" not in text
    assert conftest.AUTOMATION_ADDRESS in text


def test_write_ignores_other_stages(tmp_path):
    assert (
        imports.write(tmp_path, "1-resman", helpers.load_fixture("lab")) is None
    )
    assert list(tmp_path.iterdir()) == []


def test_write_refuses_operator_file(tmp_path):
    target = tmp_path / "0-bootstrap-imports.tf"
    target.write_text("# mine\n", encoding="utf-8")
    with pytest.raises(imports.ImportBlockError, match="did not write"):
        imports.write(tmp_path, "0", helpers.load_fixture("lab"))
    assert target.read_text(encoding="utf-8") == "# mine\n"


def test_write_keeps_operator_file_when_empty(tmp_path):
    target = tmp_path / "0-bootstrap-imports.tf"
    target.write_text("# mine\n", encoding="utf-8")
    assert imports.write(tmp_path, "0", _with_imports()) is None
    assert target.read_text(encoding="utf-8") == "# mine\n"


def test_write_refuses_symlink(tmp_path):
    real = tmp_path / "real.tf"
    real.write_text(
        imports.dumps(
            {conftest.AUTOMATION_ADDRESS: "x"}, imports.header("0", "lab1")
        ),
        encoding="utf-8",
    )
    (tmp_path / "0-bootstrap-imports.tf").symlink_to(real)
    with pytest.raises(imports.ImportBlockError):
        imports.write(tmp_path, "0", helpers.load_fixture("lab"))


def test_write_rejects_invalid_address(tmp_path):
    answers = _with_imports(entries={"module.only": "x"})
    with pytest.raises(imports.ImportBlockError):
        imports.write(tmp_path, "0", answers)
    assert list(tmp_path.iterdir()) == []


def test_workspace_sync_keeps_imports_file(tmp_path):
    answers = helpers.load_fixture("lab")
    env = helpers.env_paths(answers, home=tmp_path)
    workspace.sync(env, conftest.REPO_ROOT, "0-bootstrap")
    imports.write(env.workspace("0"), "0", answers)
    path = env.workspace("0") / imports.filename("0")
    report = workspace.sync(env, conftest.REPO_ROOT, "0-bootstrap")
    assert path.name not in report.removed + report.conflicts
    assert path.is_file()
    assert not path.is_symlink()


@pytest.mark.terraform
def test_imports_validate_in_bootstrap_workspace(tmp_path):
    answers = _with_imports(
        entries={
            conftest.AUTOMATION_ADDRESS: "lab1-prod-iac-core-0",
            conftest.LOG_EXPORT_ADDRESS: "lab1-prod-audit-logs-0",
            conftest.BILLING_EXPORT_ADDRESS: "lab1-prod-billing-exp-0",
        }
    )
    env = helpers.env_paths(answers, home=tmp_path)
    workspace.sync(env, conftest.REPO_ROOT, "0-bootstrap")
    ws = env.workspace("0-bootstrap")
    imports.write(ws, "0", answers)
    init = helpers.terraform(ws, "init", "-backend=false", "-input=false")
    assert init.returncode == 0, init.stderr
    validate = helpers.terraform(ws, "validate")
    assert validate.returncode == 0, validate.stderr
    # The same check rejects an address the configuration does not define,
    # so the success above proves the addresses are real.
    wrong = _with_imports(entries={"module.no-such.google_project.p": "x"})
    imports.write(ws, "0", wrong)
    invalid = helpers.terraform(ws, "validate")
    assert invalid.returncode != 0
    assert "no-such" in invalid.stderr + invalid.stdout


@pytest.mark.terraform
def test_org_policy_imports_validate_in_bootstrap_workspace(tmp_path):
    answers = helpers.load_fixture("lab", existing_org_policies=_POLICIES)
    env = helpers.env_paths(answers, home=tmp_path)
    workspace.sync(env, conftest.REPO_ROOT, "0-bootstrap")
    ws = env.workspace("0-bootstrap")
    imports.write(ws, "0", answers)
    init = helpers.terraform(ws, "init", "-backend=false", "-input=false")
    assert init.returncode == 0, init.stderr
    validate = helpers.terraform(ws, "validate")
    assert validate.returncode == 0, validate.stderr + validate.stdout
    fmt = helpers.terraform(ws, "fmt", "-check", imports.filename("0"))
    assert fmt.returncode == 0, fmt.stdout


def test_dumps_imports_the_workload():
    workload_id = (
        f"organizations/{conftest.ORG_ID}/locations/us-east4/workloads/abc123"
    )
    text = imports.dumps(
        {"google_assured_workloads_workload.primary[0]": workload_id}, []
    )
    (block,) = hcl2.loads(text)["import"]
    assert block["to"] == "${google_assured_workloads_workload.primary[0]}"
    assert block["id"] == f'"{workload_id}"'
