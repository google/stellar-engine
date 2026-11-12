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
import subprocess
import unittest

import release_please
import yaml

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]

_CURATED_LABELS = frozenset(
    {
        "Bug",
        "Dependencies - Docker",
        "Dependencies - GitHub Actions",
        "Dependencies - JavaScript",
        "Dependencies - Python",
        "Documentation",
        "Duplicate",
        "Enhancement",
        "Framework - FedRAMP High",
        "Framework - FedRAMP Moderate",
        "Framework - IL4",
        "Framework - IL5",
        "Gemini - Enterprise",
        "Gemini - Government",
        "Good First Issue",
        "Help Wanted",
        "Level of Effort - High",
        "Level of Effort - Low",
        "Level of Effort - Medium",
        "Priority - High",
        "Priority - Low",
        "Priority - Medium",
        "Project Management",
        "Question",
        "Release - Pending",
        "Release - Tagged",
        "Scope - Blueprint",
        "Scope - Fast",
        "Scope - Module",
        "Security",
        "Won't Fix",
    }
)


class TestLabelTaxonomy(unittest.TestCase):
    def test_labeler_uses_only_curated_labels(self):
        labeler_path = _REPO_ROOT / ".github/labeler.yml"
        config = yaml.safe_load(labeler_path.read_text(encoding="utf-8"))
        self.assertIsInstance(config, dict)
        self.assertTrue(set(config.keys()).issubset(_CURATED_LABELS))
        self.assertNotIn("Project Management", config)
        self.assertNotEqual(
            config.get("Gemini - Enterprise"),
            config.get("Gemini - Government"),
        )
        g4g_globs = [
            rule["changed-files"][0]["any-glob-to-any-file"]
            for rule in config.get("Gemini - Government", [])
            if "changed-files" in rule
        ]
        self.assertNotIn("blueprints/gemini-enterprise/**", g4g_globs[0])

    def test_issue_templates_use_only_curated_labels(self):
        template_dir = _REPO_ROOT / ".github/ISSUE_TEMPLATE"
        frontmatter_re = re.compile(r"^---\n(.*?)\n---", re.DOTALL)
        for template_path in sorted(template_dir.glob("*.md")):
            with self.subTest(template=template_path.name):
                match = frontmatter_re.match(
                    template_path.read_text(encoding="utf-8")
                )
                self.assertIsNotNone(match)
                frontmatter = yaml.safe_load(match.group(1))
                raw_labels = frontmatter.get("labels", [])
                labels = (
                    [s.strip() for s in raw_labels.split(",") if s.strip()]
                    if isinstance(raw_labels, str)
                    else list(raw_labels)
                )
                self.assertTrue(labels)
                self.assertTrue(set(labels).issubset(_CURATED_LABELS))

    def test_release_please_config_uses_curated_release_labels(self):
        config_path = _REPO_ROOT / ".github/release-please-config.json"
        config = json.loads(config_path.read_text(encoding="utf-8"))
        self.assertEqual(config.get("label"), "Release - Pending")
        self.assertEqual(config.get("release-label"), "Release - Tagged")
        self.assertEqual(
            config.get("pull-request-footer"),
            "---\nBeep Boop. This PR was generated with "
            "[Release Please](https://github.com/googleapis/release-please). "
            "See [documentation]"
            "(https://github.com/googleapis/release-please#release-please).",
        )

    def test_release_docs_and_workflow_omit_warning_symbol(self):
        for rel_path in ("RELEASES.md", "CHANGELOG.md"):
            content = (_REPO_ROOT / rel_path).read_text(encoding="utf-8")
            self.assertNotIn("\u26a0", content)

        gemini_md = (_REPO_ROOT / "GEMINI.md").read_text(encoding="utf-8")
        self.assertIn("`release-please-branches-main`", gemini_md)
        self.assertNotIn("`release-please--branches--main`", gemini_md)

        self.assertTrue(
            set(release_please.RELEASE_PR_LABELS).issubset(_CURATED_LABELS)
        )

        workflow_path = _REPO_ROOT / ".github/workflows/release.yml"
        workflow = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
        steps = workflow["jobs"]["release-please"]["steps"]
        run_commands = [step["run"] for step in steps if "run" in step]
        for cmd in run_commands:
            self.assertNotIn("${{", cmd)
        self.assertIn("python3 tools/release_please.py prepare", run_commands)
        self.assertIn("python3 tools/release_please.py label-pr", run_commands)

    def test_dependabot_uses_only_curated_labels(self):
        dependabot_path = _REPO_ROOT / ".github/dependabot.yml"
        config = yaml.safe_load(dependabot_path.read_text(encoding="utf-8"))
        for update in config.get("updates", []):
            with self.subTest(ecosystem=update.get("package-ecosystem")):
                labels = update.get("labels", [])
                self.assertTrue(labels)
                self.assertTrue(set(labels).issubset(_CURATED_LABELS))

    def test_labeler_covers_dependencies_and_security(self):
        labeler_path = _REPO_ROOT / ".github/labeler.yml"
        config = yaml.safe_load(labeler_path.read_text(encoding="utf-8"))
        for expected in (
            "Dependencies - Docker",
            "Dependencies - GitHub Actions",
            "Dependencies - JavaScript",
            "Dependencies - Python",
            "Security",
        ):
            self.assertIn(expected, config)

    def test_labeler_workflow_triage_logic_and_env_safety(self):
        workflow_path = _REPO_ROOT / ".github/workflows/labeler.yml"
        raw = workflow_path.read_text(encoding="utf-8")
        workflow = yaml.safe_load(raw)
        triggers = workflow.get("on") or workflow.get(True)
        self.assertIn("pull_request_target", triggers)
        self.assertIn("edited", triggers["pull_request_target"]["types"])
        self.assertIn("issues", triggers)
        self.assertIn("opened", triggers["issues"]["types"])
        self.assertIn("edited", triggers["issues"]["types"])

        run_script = workflow["jobs"]["label"]["steps"][1]["run"]
        self.assertNotIn("${{", run_script)
        self.assertNotIn("python", run_script)

        inferred_literals = set(
            re.findall(
                r'(?:inferred\+=\(|add_if\s+\S+\s+\'[^\']+\'\s+)"([^"$]+)"',
                run_script,
            )
        )
        self.assertTrue(inferred_literals)
        self.assertTrue(inferred_literals.issubset(_CURATED_LABELS))

        def run_triage(env_overrides):
            env = {
                **os.environ,
                "DRY_RUN": "1",
                "EXISTING_LABELS_OVERRIDE": "",
                **env_overrides,
            }
            out = subprocess.run(
                ["bash", "-e", "-o", "pipefail", "-c", run_script],
                env=env,
                capture_output=True,
                check=True,
                text=True,
            ).stdout
            return {line.strip() for line in out.splitlines() if line.strip()}

        pr_template = (
            _REPO_ROOT / ".github/pull_request_template.md"
        ).read_text(encoding="utf-8")
        dep_body = pr_template.replace(
            "*   **NIST 800-53r5 Controls:** (If this PR helps satisfy or "
            "modifies control implementations, list them here)",
            "*   **NIST 800-53r5 Controls:** SI-2",
        )
        self.assertEqual(
            run_triage(
                {
                    "EVENT_NAME": "pull_request_target",
                    "PR_NUMBER": "392",
                    "PR_TITLE": (
                        "build(deps): bump pyasn1 to 0.6.5 for four HIGH "
                        "advisories"
                    ),
                    "PR_BODY": dep_body,
                    "PR_ADDITIONS": "6",
                    "PR_DELETIONS": "6",
                    "PR_CHANGED_FILES": "2",
                    "EXISTING_LABELS_OVERRIDE": (
                        "Scope - Fast\nDependencies - Python"
                    ),
                }
            ),
            {"Security", "Level of Effort - Low", "Priority - High"},
        )

        feat_body = pr_template.replace(
            "- [ ] New feature", "- [x] New feature"
        ).replace("*   [ ] DoD IL5", "*   [x] DoD IL5")
        self.assertEqual(
            run_triage(
                {
                    "EVENT_NAME": "pull_request_target",
                    "PR_NUMBER": "386",
                    "PR_TITLE": "feat(cli): guided deploy",
                    "PR_BODY": feat_body,
                    "PR_ADDITIONS": "900",
                    "PR_DELETIONS": "50",
                    "PR_CHANGED_FILES": "12",
                    "EXISTING_LABELS_OVERRIDE": "Scope - Fast",
                }
            ),
            {
                "Enhancement",
                "Framework - IL5",
                "Level of Effort - High",
                "Priority - Medium",
            },
        )

        bug_template = (
            _REPO_ROOT / ".github/ISSUE_TEMPLATE/bug_report.md"
        ).read_text(encoding="utf-8")
        self.assertEqual(
            run_triage(
                {
                    "EVENT_NAME": "issues",
                    "ISSUE_NUMBER": "100",
                    "ISSUE_TITLE": "[Bug] unexpected error",
                    "ISSUE_BODY": bug_template,
                    "EXISTING_LABELS_OVERRIDE": "Bug",
                }
            ),
            set(),
        )

        populated_bug = bug_template.replace(
            "*   [ ] FedRAMP High", "*   [x] FedRAMP High"
        ).replace(
            "*   [ ] Stage 3 (Security and Audit)",
            "*   [x] Stage 3 (Security and Audit)",
        )
        self.assertEqual(
            run_triage(
                {
                    "EVENT_NAME": "issues",
                    "ISSUE_NUMBER": "101",
                    "ISSUE_TITLE": (
                        "[Bug] blueprints/fedramp-high: KMS grant error"
                    ),
                    "ISSUE_BODY": populated_bug,
                    "EXISTING_LABELS_OVERRIDE": "Bug",
                }
            ),
            {
                "Framework - FedRAMP High",
                "Scope - Blueprint",
                "Scope - Fast",
                "Security",
            },
        )

        self.assertEqual(
            run_triage(
                {
                    "EVENT_NAME": "issues",
                    "ISSUE_NUMBER": "387",
                    "ISSUE_TITLE": (
                        "Feature Request: Support regulated multi-tenancy"
                    ),
                    "ISSUE_BODY": (
                        "Extend fast/stages-aw/0-bootstrap for Gemini for "
                        "Government."
                    ),
                    "EXISTING_LABELS_OVERRIDE": "",
                }
            ),
            {
                "Enhancement",
                "Gemini - Government",
                "Scope - Fast",
            },
        )


if __name__ == "__main__":
    unittest.main()
