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

import json
import os
import pathlib
import re
import shutil
import stat
import subprocess
import tempfile
import unittest

import yaml

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
_BOOTSTRAP_DIR = _REPO_ROOT / "fast/stages-aw/0-bootstrap"
_RESMAN_DIR = _REPO_ROOT / "fast/stages-aw/1-resman"
_ASSETS_DIR = _REPO_ROOT / "fast/assets"
_STAGES_AW_DIRS = (
    _REPO_ROOT / "fast/stages-aw/0-bootstrap",
    _REPO_ROOT / "fast/stages-aw/1-resman",
    _REPO_ROOT / "fast/stages-aw/2-networking-a-fedramp",
    _REPO_ROOT / "fast/stages-aw/2-networking-b-il5-ngfw",
    _REPO_ROOT / "fast/stages-aw/3-security",
)
_SETIAM_SH = _BOOTSTRAP_DIR / "setIAM.sh"
_SETIAM_SAMPLE = _BOOTSTRAP_DIR / "setIAM.yaml.sample"
_SETIAM_TEST_SH = _REPO_ROOT / "tests/test_setiam.sh"

_GITHUB_TEMPLATES = (
    _BOOTSTRAP_DIR / "templates/workflow-github.yaml",
    _RESMAN_DIR / "templates/workflow-github.yaml",
    _ASSETS_DIR / "templates/workflow-github.yaml",
)
_GITLAB_TEMPLATES = (
    _BOOTSTRAP_DIR / "templates/workflow-gitlab.yaml",
    _RESMAN_DIR / "templates/workflow-gitlab.yaml",
    _ASSETS_DIR / "templates/workflow-gitlab.yaml",
)
_SOURCEREPO_TEMPLATES = (
    _BOOTSTRAP_DIR / "templates/workflow-sourcerepo.yaml",
    _RESMAN_DIR / "templates/workflow-sourcerepo.yaml",
    _ASSETS_DIR / "templates/workflow-sourcerepo.yaml",
)

_APPLY_SA = "apply@my-project.iam.gserviceaccount.com"
_PLAN_SA = "plan@my-project.iam.gserviceaccount.com"
_APPLY_PROVIDERS = "1-resman-providers.tf"
_PLAN_PROVIDERS = "1-resman-r-providers.tf"
_EXPECTED_TF_VERSION = "1.13.3"
_UNRENDERED_VAR_RE = re.compile(r"(?<!\$)\$\{[^{}]+\}")


def _render_template(content: str, tf_var_files: list[str]) -> str:
    """Renders FAST workflow templatefile() directives for offline testing."""
    rendered = content
    if tf_var_files:
        rendered = re.sub(
            r"[ \t]*%\{\s*~?\s*if tf_var_files != \[\]\s*~?\s*\}\n"
            r"([\s\S]*?)"
            r"[ \t]*%\{\s*~?\s*endif\s*~?\s*\}\n?",
            r"\1",
            rendered,
        )
        rendered = re.sub(
            r"[ \t]*%\{\s*~?\s*for f in tf_var_files\s*~?\s*\}\n"
            r"([\s\S]*?)"
            r"[ \t]*%\{\s*~?\s*endfor\s*~?\s*\}\n?",
            lambda m: "".join(
                m.group(1).replace("${f}", f) for f in tf_var_files
            ),
            rendered,
        )
    else:
        rendered = re.sub(
            r"[ \t]*%\{\s*~?\s*if tf_var_files != \[\]\s*~?\s*\}\n"
            r"[\s\S]*?"
            r"[ \t]*%\{\s*~?\s*endif\s*~?\s*\}\n?",
            "",
            rendered,
        )
        rendered = re.sub(
            r"[ \t]*%\{\s*~?\s*for f in tf_var_files\s*~?\s*\}\n"
            r"[\s\S]*?"
            r"[ \t]*%\{\s*~?\s*endfor\s*~?\s*\}\n?",
            "",
            rendered,
        )

    rendered = re.sub(
        r"[ \t]*%\{\s*~?\s*for aud in audiences\s*~?\s*\}\n"
        r"([\s\S]*?)"
        r"[ \t]*%\{\s*~?\s*endfor\s*~?\s*\}\n?",
        lambda m: m.group(1).replace("${aud}", "https://gitlab.example.com"),
        rendered,
    )
    replacements = {
        "${stage_name}": "1-resman",
        "${service_accounts.apply}": _APPLY_SA,
        "${service_accounts.plan}": _PLAN_SA,
        "${identity_provider}": (
            "projects/123456789012/locations/global/"
            "workloadIdentityPools/p/providers/w"
        ),
        "${outputs_bucket}": "my-outputs-bucket",
        "${tf_providers_files.apply}": _APPLY_PROVIDERS,
        "${tf_providers_files.plan}": _PLAN_PROVIDERS,
        '${join("\\n    ", tf_var_files)}': "\n    ".join(tf_var_files),
    }
    for key, val in replacements.items():
        rendered = rendered.replace(key, val)
    return rendered.replace("$${", "${")


class TestCicdWorkflowHardening(unittest.TestCase):
    def test_github_workflows_separate_plan_and_apply_cleanly(self):
        var_cases = (
            [],
            ["0-bootstrap.auto.tfvars.json", "0-globals.auto.tfvars.json"],
        )
        for tpl_path in _GITHUB_TEMPLATES:
            raw = tpl_path.read_text(encoding="utf-8")
            for tf_var_files in var_cases:
                with self.subTest(
                    template=str(tpl_path.relative_to(_REPO_ROOT)),
                    tf_var_files=len(tf_var_files),
                ):
                    unsub = _UNRENDERED_VAR_RE.findall(
                        _render_template(
                            raw.replace("$${", "__ESCAPED_INTERP__"),
                            tf_var_files,
                        )
                    )
                    self.assertEqual(unsub, [])

                    rendered = _render_template(raw, tf_var_files)
                    parsed = yaml.safe_load(rendered)
                    self.assertIsInstance(parsed, dict)

                    # PyYAML 1.1 loads bare `on:` as boolean True.
                    triggers = parsed.get("on", parsed.get(True))
                    self.assertIsInstance(triggers, dict)
                    self.assertIn("pull_request", triggers)
                    self.assertIn("push", triggers)

                    pr_types = triggers["pull_request"]["types"]
                    self.assertEqual(
                        pr_types, ["opened", "synchronize", "reopened"]
                    )
                    self.assertNotIn("closed", pr_types)
                    self.assertEqual(triggers["push"]["branches"], ["main"])

                    # Top-level env must never expose the apply SA or provider.
                    self.assertEqual(parsed.get("permissions"), {})
                    top_env = parsed.get("env", {})
                    self.assertEqual(
                        top_env.get("TF_VERSION"), _EXPECTED_TF_VERSION
                    )
                    self.assertNotIn("FAST_SERVICE_ACCOUNT", top_env)
                    self.assertNotIn("TF_PROVIDERS_FILE", top_env)

                    jobs = parsed["jobs"]
                    self.assertIn("fast-plan", jobs)
                    self.assertIn("fast-apply", jobs)
                    self.assertNotIn("fast-pr", jobs)

                    plan_job = jobs["fast-plan"]
                    plan_yaml = yaml.safe_dump(plan_job)
                    self.assertEqual(
                        plan_job["if"], "github.event_name == 'pull_request'"
                    )
                    self.assertEqual(
                        plan_job["concurrency"]["group"],
                        "fast-1-resman-plan-${{ "
                        "github.event.pull_request.number || github.run_id }}",
                    )
                    self.assertEqual(
                        plan_job["concurrency"]["cancel-in-progress"],
                        "${{ github.event_name == 'pull_request' }}",
                    )
                    self.assertEqual(
                        plan_job["env"]["FAST_SERVICE_ACCOUNT_PLAN"], _PLAN_SA
                    )
                    self.assertEqual(
                        plan_job["env"]["TF_PROVIDERS_FILE_PLAN"],
                        _PLAN_PROVIDERS,
                    )
                    self.assertNotIn("FAST_SERVICE_ACCOUNT:", plan_yaml)
                    self.assertNotIn(_APPLY_SA, plan_yaml)
                    self.assertNotIn(_APPLY_PROVIDERS, plan_yaml)
                    self.assertNotIn("terraform apply", plan_yaml)
                    self.assertIn("-detailed-exitcode", plan_yaml)
                    self.assertIn("umask 077", plan_yaml)

                    apply_job = jobs["fast-apply"]
                    apply_yaml = yaml.safe_dump(apply_job)
                    self.assertEqual(
                        apply_job["if"],
                        "github.event_name == 'push' && "
                        "github.ref == 'refs/heads/main'",
                    )
                    self.assertEqual(
                        apply_job["concurrency"]["cancel-in-progress"], False
                    )
                    self.assertEqual(
                        apply_job["env"]["FAST_SERVICE_ACCOUNT"], _APPLY_SA
                    )
                    self.assertEqual(
                        apply_job["env"]["TF_PROVIDERS_FILE"], _APPLY_PROVIDERS
                    )
                    self.assertIn("umask 077", apply_yaml)
                    self.assertIn("-out=tfplan.binary", apply_yaml)
                    self.assertIn(
                        "terraform apply -input=false -no-color "
                        "-auto-approve tfplan.binary",
                        apply_yaml,
                    )
                    self.assertIn("rm -f tfplan.binary", apply_yaml)

    def test_gitlab_workflows_separate_mr_plan_and_protected_apply(self):
        var_cases = (
            [],
            ["0-bootstrap.auto.tfvars.json", "0-globals.auto.tfvars.json"],
        )
        for tpl_path in _GITLAB_TEMPLATES:
            raw = tpl_path.read_text(encoding="utf-8")
            for tf_var_files in var_cases:
                with self.subTest(
                    template=str(tpl_path.relative_to(_REPO_ROOT)),
                    tf_var_files=len(tf_var_files),
                ):
                    unsub = _UNRENDERED_VAR_RE.findall(
                        _render_template(
                            raw.replace("$${", "__ESCAPED_INTERP__"),
                            tf_var_files,
                        )
                    )
                    self.assertEqual(unsub, [])

                    rendered = _render_template(raw, tf_var_files)
                    parsed = yaml.safe_load(rendered)
                    self.assertIsInstance(parsed, dict)

                    top_vars = parsed.get("variables", {})
                    self.assertNotIn("FAST_SERVICE_ACCOUNT", top_vars)
                    self.assertNotIn("GOOGLE_CREDENTIALS", top_vars)
                    self.assertNotIn("TF_VAR_FILES", top_vars)

                    wif = parsed[".wif-auth"]
                    wif_before = "\n".join(wif["before_script"])
                    wif_after = "\n".join(wif["after_script"])
                    self.assertIn("umask 077", wif_before)
                    self.assertIn(".ci_job_jwt_file", wif_after)
                    self.assertIn(".gcp_temp_cred.json", wif_after)

                    for mr_job_name in ("gcp-setup-plan", "plan"):
                        mr_job = parsed[mr_job_name]
                        mr_yaml = yaml.safe_dump(mr_job)
                        self.assertEqual(
                            mr_job["variables"]["FAST_SERVICE_ACCOUNT_PLAN"],
                            _PLAN_SA,
                        )
                        self.assertNotIn(_APPLY_SA, mr_yaml)
                        self.assertNotIn(_APPLY_PROVIDERS, mr_yaml)
                        self.assertNotIn("terraform apply", mr_yaml)
                        self.assertNotIn("cicd-sa-credentials.json", mr_yaml)
                        self.assertEqual(
                            mr_job["rules"][0]["if"],
                            "$CI_PIPELINE_SOURCE == 'merge_request_event'",
                        )
                        self.assertEqual(mr_job["rules"][-1]["when"], "never")

                    # MR plan must not export binary plan files as artifacts.
                    plan_job = parsed["plan"]
                    plan_script = "\n".join(plan_job["script"])
                    self.assertEqual(
                        plan_job["image"]["name"],
                        f"hashicorp/terraform:{_EXPECTED_TF_VERSION}",
                    )
                    self.assertIn("umask 077", plan_script)
                    self.assertIn("-detailed-exitcode", plan_script)
                    self.assertNotIn("-out=tfplan.binary", plan_script)
                    self.assertNotIn("artifacts", plan_job)

                    for main_job_name in (
                        "gcp-setup-apply",
                        "plan-apply",
                        "apply",
                    ):
                        main_job = parsed[main_job_name]
                        self.assertIn("resource_group", main_job)
                        self.assertEqual(
                            main_job["variables"]["FAST_SERVICE_ACCOUNT"],
                            _APPLY_SA,
                        )
                        rule_if = main_job["rules"][0]["if"]
                        self.assertIn(
                            "$CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH", rule_if
                        )
                        self.assertIn(
                            "$CI_COMMIT_REF_PROTECTED == 'true'", rule_if
                        )
                        self.assertEqual(main_job["rules"][-1]["when"], "never")

                    # Setup and plan-apply artifact TTLs must stay aligned.
                    setup_apply_artifacts = parsed["gcp-setup-apply"][
                        "artifacts"
                    ]
                    plan_apply_job = parsed["plan-apply"]
                    plan_apply_artifacts = plan_apply_job["artifacts"]
                    self.assertEqual(
                        plan_apply_job["image"]["name"],
                        f"hashicorp/terraform:{_EXPECTED_TF_VERSION}",
                    )
                    self.assertEqual(
                        setup_apply_artifacts["expire_in"],
                        plan_apply_artifacts["expire_in"],
                    )
                    self.assertEqual(plan_apply_artifacts["when"], "on_success")
                    self.assertIn(
                        "tfplan.binary", plan_apply_artifacts["paths"]
                    )

                    apply_job = parsed["apply"]
                    self.assertEqual(
                        apply_job["image"]["name"],
                        f"hashicorp/terraform:{_EXPECTED_TF_VERSION}",
                    )
                    self.assertEqual(apply_job["allow_failure"], True)
                    self.assertEqual(apply_job["rules"][0]["when"], "manual")
                    apply_script = "\n".join(apply_job["script"])
                    apply_after = "\n".join(apply_job["after_script"])
                    self.assertIn("umask 077", apply_script)
                    self.assertIn(
                        "terraform apply -input=false -no-color "
                        "-auto-approve tfplan.binary",
                        apply_script,
                    )
                    self.assertIn(".ci_job_jwt_file", apply_after)
                    self.assertIn(".gcp_temp_cred.json", apply_after)
                    self.assertIn("tfplan.binary", apply_after)

    def test_bootstrap_resman_and_assets_templates_stay_identical(self):
        gh_contents = [p.read_text(encoding="utf-8") for p in _GITHUB_TEMPLATES]
        self.assertEqual(gh_contents[0], gh_contents[1])
        self.assertEqual(gh_contents[0], gh_contents[2])

        gl_contents = [p.read_text(encoding="utf-8") for p in _GITLAB_TEMPLATES]
        self.assertEqual(gl_contents[0], gl_contents[1])
        self.assertEqual(gl_contents[0], gl_contents[2])

        sr_contents = [
            p.read_text(encoding="utf-8") for p in _SOURCEREPO_TEMPLATES
        ]
        self.assertEqual(sr_contents[0], sr_contents[1])
        self.assertEqual(sr_contents[0], sr_contents[2])

    def test_workflows_use_gcloud_storage_and_supported_tf_version(self):
        for tpl_path in (
            _GITHUB_TEMPLATES + _GITLAB_TEMPLATES + _SOURCEREPO_TEMPLATES
        ):
            with self.subTest(template=str(tpl_path.relative_to(_REPO_ROOT))):
                content = tpl_path.read_text(encoding="utf-8")
                self.assertNotIn("gcloud alpha storage", content)
                self.assertNotIn("install_components: alpha", content)
                self.assertNotIn("gsutil", content)
                self.assertIn("gcloud storage cp", content)

        for tpl_path in _SOURCEREPO_TEMPLATES:
            with self.subTest(sourcerepo=str(tpl_path.relative_to(_REPO_ROOT))):
                placeholder = (
                    "${tf_var_files == [] ? \"''\" : "
                    'join("\\n    ", tf_var_files)}'
                )
                raw = tpl_path.read_text(encoding="utf-8").replace(
                    placeholder,
                    "0-bootstrap.auto.tfvars.json",
                )
                rendered = _render_template(
                    raw,
                    ["0-bootstrap.auto.tfvars.json"],
                )
                parsed = yaml.safe_load(rendered)
                self.assertEqual(
                    parsed["substitutions"]["_TF_VERSION"],
                    _EXPECTED_TF_VERSION,
                )

    def test_stages_aw_declare_versions_tf(self):
        for stage_dir in _STAGES_AW_DIRS:
            with self.subTest(stage=stage_dir.name):
                versions_tf = stage_dir / "versions.tf"
                self.assertTrue(
                    versions_tf.is_file(),
                    f"Missing {versions_tf.relative_to(_REPO_ROOT)}",
                )
                content = versions_tf.read_text(encoding="utf-8")
                self.assertIn('required_version = ">= 1.12.2"', content)
                self.assertIn('source  = "hashicorp/google"', content)
                self.assertIn('source  = "hashicorp/google-beta"', content)
                self.assertIn('version = ">= 8.10.0, < 9.0.0"', content)


class TestSetIamHardening(unittest.TestCase):
    def test_setiam_static_hardening_invariants(self):
        content = _SETIAM_SH.read_text(encoding="utf-8")
        code_lines = "\n".join(
            line
            for line in content.splitlines()
            if not line.lstrip().startswith("#")
        )
        self.assertIn("set -euo pipefail", code_lines)
        self.assertIn("umask 077", code_lines)
        self.assertIn(
            "^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$", code_lines
        )
        self.assertIsNone(re.search(r"\bsed\b", code_lines))
        self.assertIsNone(re.search(r"\b(mapfile|readarray)\b", code_lines))
        self.assertNotIn("contains($user)", code_lines)
        self.assertNotIn('grep -q "^$role$"', code_lines)
        self.assertIn("index($user)", code_lines)
        self.assertIn('grep -Fxq -- "$role"', code_lines)
        self.assertIn("while IFS= read -r role; do", code_lines)

    def test_setiam_rejects_malformed_and_injection_emails(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = pathlib.Path(tmpdir)
            bin_dir = tmp / "bin"
            bin_dir.mkdir()
            gcloud_log = tmp / "gcloud.log"
            stub = bin_dir / "gcloud"
            stub.write_text(
                '#!/bin/bash\necho "$*" >> "$GCLOUD_LOG"\n',
                encoding="utf-8",
            )
            stub.chmod(stub.stat().st_mode | stat.S_IXUSR)

            env = os.environ.copy()
            env["PATH"] = f"{bin_dir}:{env.get('PATH', '')}"
            env["GCLOUD_LOG"] = str(gcloud_log)

            bad_emails = (
                "not-an-email",
                "admin@example.com;id",
                "admin@example.com/g;p",
                "$(id)@example.com",
                "admin@example.com\nuser:evil@example.com",
            )
            for email in bad_emails:
                with self.subTest(email=email):
                    res = subprocess.run(
                        ["bash", str(_SETIAM_SH), email, "123456789012"],
                        env=env,
                        capture_output=True,
                        text=True,
                        check=False,
                    )
                    self.assertNotEqual(res.returncode, 0)
                    self.assertFalse(gcloud_log.exists())

    def test_setiam_exact_match_and_idempotency(self):
        sample = json.loads(_SETIAM_SAMPLE.read_text(encoding="utf-8"))
        sample_roles = [b["role"] for b in sample["bindings"]]

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = pathlib.Path(tmpdir)
            bin_dir = tmp / "bin"
            bin_dir.mkdir()
            policy_in = tmp / "policy_in.json"
            policy_out = tmp / "policy_out.json"
            gcloud_log = tmp / "gcloud.log"

            stub = bin_dir / "gcloud"
            stub.write_text(
                "#!/bin/bash\n"
                "set -euo pipefail\n"
                'echo "$*" >> "$GCLOUD_LOG"\n'
                'if [[ "${2:-}" == "get-iam-policy" ]]; then\n'
                '  cat "$POLICY_IN"\n'
                'elif [[ "${2:-}" == "set-iam-policy" ]]; then\n'
                '  cat /dev/stdin > "$POLICY_OUT"\n'
                '  cat "$POLICY_OUT"\n'
                "fi\n",
                encoding="utf-8",
            )
            stub.chmod(stub.stat().st_mode | stat.S_IXUSR)

            env = os.environ.copy()
            env["PATH"] = f"{bin_dir}:{env.get('PATH', '')}"
            env["GCLOUD_LOG"] = str(gcloud_log)
            env["POLICY_IN"] = str(policy_in)
            env["POLICY_OUT"] = str(policy_out)

            # Only abob@example.com holds the roles; bob@example.com must still
            # receive all roles rather than matching by substring.
            policy_in.write_text(
                json.dumps(
                    {
                        "etag": "test-etag",
                        "bindings": [
                            {
                                "role": role,
                                "members": ["user:abob@example.com"],
                            }
                            for role in sample_roles
                        ],
                    }
                ),
                encoding="utf-8",
            )

            res = subprocess.run(
                ["bash", str(_SETIAM_SH), "bob@example.com", "123456789012"],
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(res.returncode, 0, res.stderr)
            updated = json.loads(policy_out.read_text(encoding="utf-8"))
            bob_roles = [
                b["role"]
                for b in updated["bindings"]
                if "user:bob@example.com" in b["members"]
            ]
            self.assertEqual(sorted(bob_roles), sorted(sample_roles))

            # Re-run with updated policy: must be a no-op with no set call.
            policy_in.write_text(json.dumps(updated), encoding="utf-8")
            gcloud_log.unlink()
            policy_out.unlink()

            res2 = subprocess.run(
                ["bash", str(_SETIAM_SH), "bob@example.com", "123456789012"],
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(res2.returncode, 0, res2.stderr)
            self.assertFalse(policy_out.exists())
            self.assertNotIn(
                "set-iam-policy", gcloud_log.read_text(encoding="utf-8")
            )

    def test_shellcheck_passes_for_setiam_scripts(self):
        shellcheck_bin = shutil.which("shellcheck")
        if shellcheck_bin is None:
            self.skipTest("shellcheck not installed on PATH")
        res = subprocess.run(
            [shellcheck_bin, str(_SETIAM_SH), str(_SETIAM_TEST_SH)],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)


if __name__ == "__main__":
    unittest.main()
