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

"""Tests for the registry of known deploy failures.

The snippets are sanitized from the DDG, `scripts/deploy.sh` and the lab
logs, with placeholder project numbers, names and lock IDs.
"""

import pytest

import conftest
import helpers
import helpers_deploy
from stellar_engine.deploy import model
from stellar_engine.deploy import remedies
from stellar_engine.wizard import prompts

_PROJECT = "123456789012"
_LOCK_ID = "1700000000000000"
_API_DISABLED = f"""Error: Error creating KeyRing: googleapi: Error 403: Cloud \
Key Management Service (KMS) API has not been used in project {_PROJECT} \
before or it is disabled. Enable it by visiting https://console.developers.\
google.com/apis/api/cloudkms.googleapis.com/overview?project={_PROJECT} then \
retry.
Details:
[
  {{
    "@type": "type.googleapis.com/google.rpc.ErrorInfo",
    "domain": "googleapis.com",
    "metadata": {{
      "consumer": "projects/{_PROJECT}",
      "service": "cloudkms.googleapis.com"
    }},
    "reason": "SERVICE_DISABLED"
  }}
]"""
_STATE_LOCK = f"""Error: Error acquiring the state lock

Error message: writing "gs://tst-prod-iac-core-bootstrap-0/default.tflock"
failed: googleapi: Error 412: Precondition Failed, conditionNotMet
Lock Info:
  ID:        {_LOCK_ID}
  Path:      gs://tst-prod-iac-core-bootstrap-0/default.tflock
  Operation: OperationTypeApply
  Who:       user@example.com
  Version:   1.13.3
"""
_BUCKET_REPLACE = """\
  # module.log-export-logbucket["audit-logs"].google_logging_project_bucket\
_config.bucket[0] must be replaced
  # (imported from "projects/my-project/locations/us-east4/buckets/audit-logs")
  # Warning: this will destroy the imported resource
-/+ resource "google_logging_project_bucket_config" "bucket" {
      ~ project          = "projects/my-project" -> "my-project" # forces \
replacement
"""
_SNIPPETS = {
    remedies.BQ_RESTRICT_SERVICE_USAGE: (
        "Error: googleapi: Error 403: Request is disallowed by "
        "organization's constraints/gcp.restrictServiceUsage constraint for "
        f"'projects/{_PROJECT}' attempting to use service "
        "'bigquery.googleapis.com'."
    ),
    remedies.SA_PROPAGATION: (
        "Error: googleapi: Error 403: Permission "
        "'iam.serviceAccounts.getAccessToken' denied on resource (or it may "
        "not exist) for tst-prod-resman-0@tst-prod-iac-core-0.iam."
        "gserviceaccount.com"
    ),
    remedies.KMS_SERVICE_AGENT: (
        "Error: Error applying IAM policy for KMS CryptoKey: googleapi: "
        f"Error 400: Service account service-{_PROJECT}@gcp-sa-cloudkms."
        "iam.gserviceaccount.com does not exist."
    ),
    remedies.IL5_GCS_SERVICE_AGENT: (
        "Error: googleapi: Error 400: Service account "
        f"service-{_PROJECT}@gs-project-accounts.iam.gserviceaccount.com "
        "does not exist."
    ),
    remedies.API_DISABLED: _API_DISABLED,
    remedies.STATE_LOCK: _STATE_LOCK,
    remedies.BACKEND_INIT_REQUIRED: (
        'Error: Backend initialization required, please run "terraform init"'
    ),
    remedies.MIGRATE_REFUSED: (
        "Error: Can't ask approval for state migration when interactive "
        'input is disabled. Please remove the "-input=false" flag.'
    ),
    remedies.WORKLOAD_CREATE_FAILED: (
        "Error: Error waiting for Creating Workload: Error code 13, "
        "message: Failed to create workload. "
        "ERROR_CODE_CREATE_WORKLOAD_FAILURE"
    ),
    remedies.LOG_BUCKET_TIMEOUT: (
        "Error: Error waiting to create ProjectBucketConfig: timeout while "
        'waiting for state to become "done"\n  with module.log-export-'
        'logbucket["audit-logs"].google_logging_project_bucket_config.'
        "bucket[0],"
    ),
    remedies.IMPORT_REPLACE_15725: _BUCKET_REPLACE,
    remedies.CMEK_FOLDER_SETTINGS: (
        "Error: Error creating FolderSettings: googleapi: Error 400: "
        "Constraint `constraints/gcp.restrictNonCmekServices` violated for "
        "`logging.googleapis.com`. You have to provide a kms key with the "
        "request."
    ),
    remedies.CUSTOM_ROLE_EXISTS: (
        "Error: Error creating the custom organization role "
        f"organizations/{conftest.ORG_ID}/roles/tagViewer: googleapi: Error "
        "409: A role named tagViewer already exists., alreadyExists"
    ),
    remedies.SINK_EXISTS: (
        "Error: Error creating OrganizationLogSink: googleapi: Error 409: "
        "Requested entity already exists, alreadyExists for "
        f"organizations/{conftest.ORG_ID}/sinks/audit-logs"
    ),
    remedies.PROJECT_ID_TAKEN: (
        "Error: error creating project tst-prod-iac-core-0: googleapi: Error "
        "409: Requested entity already exists, alreadyExists for "
        "projects/tst-prod-iac-core-0"
    ),
    remedies.BILLING_UNLINKED: (
        "Error: googleapi: Error 403: The billing account for the owning "
        "project is disabled in state absent, accountDisabled"
    ),
    remedies.ADC_QUOTA_PROJECT: (
        "Error: googleapi: Error 403: Your application is authenticating "
        "by using local Application Default Credentials. The "
        "cloudkms.googleapis.com API requires a quota project, which is not "
        "set by default."
    ),
}


def _failure(output, findings=(), plan=None, stage="0"):
    return remedies.Failure(
        "s0.apply_final", stage, "apply", output, plan, findings
    )


def test_registry_holds_every_planned_key():
    assert set(remedies.REMEDIES) == set(_SNIPPETS)


@pytest.mark.parametrize("key", sorted(_SNIPPETS))
def test_snippet_matches_its_remedy_only(key):
    failure = _failure(_SNIPPETS[key])
    found = {
        name
        for name, item in remedies.REMEDIES.items()
        if item.matches(failure)
    }
    assert found == {key}
    assert remedies.match(failure, [key]) is remedies.REMEDIES[key]


def test_match_only_uses_the_step_keys():
    failure = _failure(_SNIPPETS[remedies.STATE_LOCK])
    assert remedies.match(failure, [remedies.API_DISABLED]) is None
    assert remedies.match(failure, []) is None
    found = remedies.match(
        failure, [remedies.API_DISABLED, remedies.STATE_LOCK]
    )
    assert found is remedies.REMEDIES[remedies.STATE_LOCK]


def test_match_rejects_unknown_keys():
    with pytest.raises(KeyError):
        remedies.match(_failure("x"), ["no_such_remedy"])


def test_match_reads_only_the_output_tail():
    output = "\n".join(
        [_SNIPPETS[remedies.STATE_LOCK], *["noise"] * remedies.TAIL_LINES]
    )
    assert remedies.match(_failure(output), [remedies.STATE_LOCK]) is None


def test_tail_keeps_the_last_lines():
    output = "\n".join(f"line {number}" for number in range(5)) + "\n\n"
    assert remedies.tail(output, 2) == "line 3\nline 4"
    assert _failure(output).tail == remedies.tail(output)


def test_guard_findings_match_by_key():
    failure = _failure("plan checks", findings=(remedies.IMPORT_REPLACE_15725,))
    found = remedies.match(failure, [remedies.IMPORT_REPLACE_15725])
    assert found is remedies.REMEDIES[remedies.IMPORT_REPLACE_15725]


def test_patterns_ignore_case():
    failure = _failure("error acquiring the STATE LOCK")
    assert remedies.match(failure, [remedies.STATE_LOCK])


@pytest.mark.parametrize("key", sorted(_SNIPPETS))
def test_docs_resolve(key):
    assert helpers.doc_resolves(remedies.REMEDIES[key].doc)


@pytest.mark.parametrize("key", sorted(_SNIPPETS))
def test_actions_are_bounded(key):
    remedy = remedies.REMEDIES[key]
    if remedy.action is None:
        assert remedy.max_attempts == 0
    else:
        assert remedy.max_attempts >= 1


def test_wait_repeats_the_last():
    remedy = remedies.REMEDIES[remedies.SA_PROPAGATION]
    assert [remedy.wait(n) for n in range(5)] == [10, 30, 60, 60, 60]
    assert remedies.REMEDIES[remedies.STATE_LOCK].wait(0) == 0


def test_disabled_api():
    assert remedies.disabled_api(_API_DISABLED) == (
        "cloudkms.googleapis.com",
        _PROJECT,
    )
    link = (
        "API has not been used in project my-project. Enable it by visiting "
        "https://console.developers.google.com/apis/api/pubsub.googleapis.com"
        "/overview?project=my-project then retry."
    )
    assert remedies.disabled_api(link) == (
        "pubsub.googleapis.com",
        "my-project",
    )
    assert remedies.disabled_api("nothing") is None


def _action(key):
    action = remedies.REMEDIES[key].action
    assert action is not None
    return action


def test_api_disabled_enables_the_service(tmp_path):
    cloud = conftest.FakeCloud()
    ctx = helpers_deploy.make_ctx(tmp_path, cloud=cloud)
    assert _action(remedies.API_DISABLED)(ctx, _failure(_API_DISABLED))
    assert cloud.writes == [
        ("enable_services", _PROJECT, ("cloudkms.googleapis.com",))
    ]
    assert not _action(remedies.API_DISABLED)(ctx, _failure("SERVICE_DISABLED"))


def test_kms_agent_creates_the_identity(tmp_path):
    cloud = conftest.FakeCloud()
    ctx = helpers_deploy.make_ctx(tmp_path, cloud=cloud)
    failure = _failure(_SNIPPETS[remedies.KMS_SERVICE_AGENT])
    assert _action(remedies.KMS_SERVICE_AGENT)(ctx, failure)
    assert cloud.writes == [
        ("generate_service_identity", _PROJECT, "cloudkms.googleapis.com")
    ]


def test_gcs_agent_reads_the_agent(tmp_path):
    ctx = helpers_deploy.make_ctx(tmp_path)
    failure = _failure(_SNIPPETS[remedies.IL5_GCS_SERVICE_AGENT])
    assert _action(remedies.IL5_GCS_SERVICE_AGENT)(ctx, failure)
    assert _PROJECT in helpers_deploy.output(ctx)
    assert not _action(remedies.IL5_GCS_SERVICE_AGENT)(ctx, _failure("x"))


def test_sa_propagation_retries(tmp_path):
    ctx = helpers_deploy.make_ctx(tmp_path)
    assert _action(remedies.SA_PROPAGATION)(ctx, _failure("x"))


def test_state_lock_releases_after_a_confirmation(tmp_path):
    runner = conftest.FakeTerraform()
    ctx = helpers_deploy.make_ctx(
        tmp_path, runner=runner, prompter=prompts.ScriptedPrompter([True])
    )
    assert _action(remedies.STATE_LOCK)(ctx, _failure(_STATE_LOCK))
    (call,) = runner.calls
    assert call[0] == ("force-unlock", "-no-color", "-force", _LOCK_ID)


def test_state_lock_declined(tmp_path):
    runner = conftest.FakeTerraform()
    ctx = helpers_deploy.make_ctx(
        tmp_path, runner=runner, prompter=prompts.ScriptedPrompter([False])
    )
    with pytest.raises(model.StoppedError) as raised:
        _action(remedies.STATE_LOCK)(ctx, _failure(_STATE_LOCK))
    assert f"force-unlock {_LOCK_ID}" in (raised.value.remedy or "")
    assert runner.calls == []


def test_state_lock_stays_on_environment_problems(tmp_path):
    empty = tmp_path / "gcloud"
    empty.mkdir()
    runner = conftest.FakeTerraform()
    ctx = helpers_deploy.make_ctx(
        tmp_path,
        runner=runner,
        prompter=prompts.ScriptedPrompter([True]),
        environ={"CLOUDSDK_CONFIG": str(empty)},
    )
    with pytest.raises(model.BlockedError, match="CLOUDSDK_CONFIG"):
        _action(remedies.STATE_LOCK)(ctx, _failure(_STATE_LOCK))
    assert runner.calls == []


def test_state_lock_never_released_without_a_terminal(tmp_path):
    ctx = helpers_deploy.make_ctx(tmp_path, interactive=False, yes=True)
    with pytest.raises(model.InputRequiredError):
        _action(remedies.STATE_LOCK)(ctx, _failure(_STATE_LOCK))


def test_state_lock_without_an_id(tmp_path):
    ctx = helpers_deploy.make_ctx(tmp_path)
    failure = _failure("Error acquiring the state lock")
    assert not _action(remedies.STATE_LOCK)(ctx, failure)


def test_allow_bq_action_passes_when_allowed(tmp_path):
    cloud = conftest.FakeCloud(folders=["folders/123"])
    ctx = helpers_deploy.make_ctx(tmp_path, cloud=cloud)
    failure = _failure(_SNIPPETS[remedies.BQ_RESTRICT_SERVICE_USAGE])
    assert _action(remedies.BQ_RESTRICT_SERVICE_USAGE)(ctx, failure)
    assert cloud.writes == []
