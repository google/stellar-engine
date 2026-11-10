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
import subprocess
import tempfile
import unittest

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
        workflow = (_REPO_ROOT / ".github/workflows/release.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("s/### \u26a0 {{title}}/### {{title}}/g", workflow)
        self.assertIn(
            "s/note.title = 'BREAKING CHANGES'/"
            "note.title = 'Breaking Changes'/g",
            workflow,
        )
        self.assertIn(
            "s/const NOTES_DELIMITER = '---'/"
            "const NOTES_DELIMITER = '<!-- release-please-notes -->'/g",
            workflow,
        )
        self.assertIn(
            "s/await this.github.commentOnIssue(comment, pullRequest.number);/"
            "void 0;/g",
            workflow,
        )
        self.assertIn("/tmp/release_sub_bullets.json", workflow)
        self.assertIn("Ensure Curated Release PR Labels", workflow)
        self.assertIn("def normalize_gh_refs(text):", workflow)
        self.assertIn(
            "Format any GitHub issue or pull request reference strictly",
            workflow,
        )

    def test_release_workflow_normalizes_issue_and_pr_links_to_numbers(self):
        workflow = (_REPO_ROOT / ".github/workflows/release.yml").read_text(
            encoding="utf-8"
        )
        py_block = workflow.split("python3 - << 'PY'\n", 1)[1].split(
            "\n          PY", 1
        )[0]
        py_lines = [line[10:] for line in py_block.splitlines()]
        ns = {"re": re, "repo": "google/stellar-engine"}
        fn_src = "\n".join(py_lines).split("def extract_existing", 1)[0]
        fn_src = (
            "def normalize_gh_refs"
            + fn_src.split("def normalize_gh_refs", 1)[1]
        )
        exec(fn_src, ns)  # noqa: S102
        sample = (
            "Moves OS Login, fixing #197 and "
            "https://github.com/google/stellar-engine/pull/352#r1 and "
            "[Full Title (#14)]"
            "(https://github.com/google/stellar-engine/issues/14) "
            "plus aquasecurity/tfsec#99 while keeping `#42`."
        )
        expected_sub = (
            "Moves OS Login, fixing "
            "[#197](https://github.com/google/stellar-engine/issues/197) and "
            "[#352](https://github.com/google/stellar-engine/pull/352) and "
            "[#14](https://github.com/google/stellar-engine/issues/14) plus "
            "[aquasecurity/tfsec#99]"
            "(https://github.com/aquasecurity/tfsec/issues/99) "
            "while keeping `#42`."
        )
        self.assertEqual(ns["normalize_gh_refs"](sample), expected_sub)

        if not shutil.which("node"):
            return
        node_block = workflow.split(
            "node - \"${dir}/index.js\" << 'NODE'\n", 1
        )[1].split("\n          NODE", 1)[0]
        base_line = (
            "* **0-bootstrap:** gate "
            "([#293](https://github.com/google/stellar-engine/issues/293)) "
            "([936a692]"
            "(https://github.com/google/stellar-engine/commit/936a6925b2))"
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            index_js = pathlib.Path(tmpdir) / "index.js"
            index_js.write_text(
                "const fs = require('fs');\n"
                "const RELEASE_PLEASE = 'release-please';\n"
                "const RELEASE_PLEASE_BRANCH_PREFIX = "
                "'release-please--branches';\n"
                "const AUTORELEASE_PATTERN = "
                "/^release-?(?<component>[\\w-.]*)?-v(?<version>[0-9].*)$/;\n"
                "class BranchName {\n"
                "    static ofTargetBranch(targetBranch) {\n"
                "        return new DefaultBranchName("
                "`${RELEASE_PLEASE}--branches--${targetBranch}`);\n"
                "    }\n"
                "    getTargetBranch() { return this.targetBranch; }\n"
                "    getComponent() { return this.component; }\n"
                "}\n"
                "class AutoreleaseBranchName extends BranchName {\n"
                "    static matches(branchName) {\n"
                "        if (branchName.startsWith("
                "RELEASE_PLEASE_BRANCH_PREFIX)) {\n"
                "            return false;\n"
                "        }\n"
                "        return !!branchName.match(AUTORELEASE_PATTERN);\n"
                "    }\n"
                "}\n"
                "const DEFAULT_PATTERN = "
                "`^${RELEASE_PLEASE}--branches--(?<branch>.+)$`;\n"
                "class DefaultBranchName extends BranchName {\n"
                "    static matches(branchName) {\n"
                "        return !!branchName.match(DEFAULT_PATTERN);\n"
                "    }\n"
                "    constructor(branchName) {\n"
                "        super(branchName);\n"
                "        const match = branchName.match(DEFAULT_PATTERN);\n"
                "        if (match === null || match === void 0 "
                "? void 0 : match.groups) {\n"
                "            this.targetBranch = match.groups['branch'];\n"
                "        }\n"
                "    }\n"
                "    toString() {\n"
                "        return "
                "`${RELEASE_PLEASE}--branches--${this.targetBranch}`;\n"
                "    }\n"
                "}\n"
                "class ManifestStub {\n"
                "    constructor() { this.alwaysUpdate = false; }\n"
                "    async updateExistingPullRequest(existing, pr) {\n"
                "        return {mode: 'force', number: existing.number, "
                "headRefName: pr.headRefName};\n"
                "    }\n"
                "    async maybeUpdateExistingPullRequest(existing, pr) {\n"
                "        return {mode: 'maybe', number: existing.number, "
                "headRefName: pr.headRefName, "
                "title: pr.title.toString()};\n"
                "    }\n"
                "    async createOrUpdatePullRequest("
                "pullRequest, openPullRequests) {\n"
                "        const existing = openPullRequests.find("
                "openPullRequest => openPullRequest.headBranchName "
                "=== pullRequest.headRefName);\n"
                "        if (existing) {\n"
                "            return this.alwaysUpdate\n"
                "                ? await this.updateExistingPullRequest("
                "existing, pullRequest)\n"
                "                : await this.maybeUpdateExistingPullRequest("
                "existing, pullRequest);\n"
                "        }\n"
                "        return {mode: 'create', "
                "headRefName: pullRequest.headRefName};\n"
                "    }\n"
                "}\n"
                "const commits = [{sha: '936a6925b2', pullRequest: {body: "
                f"{json.dumps('## Description\n' + sample)}}}}}"
                "];\n"
                "const options = {commits: []};\n"
                "const preset = {writerOpts: {}};\n"
                "const context = {};\n"
                "const changelogCommits = [];\n"
                "const writer = {parseArray: () => "
                f"{json.dumps(base_line)}}};\n"
                "const out = writer\n"
                "            .parseArray("
                "changelogCommits, context, preset.writerOpts)\n"
                "            .trim();\n"
                "(async () => {\n"
                "  const m = new ManifestStub();\n"
                "  const cand = {\n"
                "    headRefName: BranchName.ofTargetBranch('main')"
                ".toString(),\n"
                "    title: {toString: () => 'release: v6.0.0'},\n"
                "  };\n"
                "  const legacyRes = await m.createOrUpdatePullRequest(\n"
                "    cand,\n"
                "    [{number: 394, headBranchName: "
                "'release-please--branches--main'}],\n"
                "  );\n"
                "  const freshRes = await m.createOrUpdatePullRequest("
                "cand, []);\n"
                "  console.log(JSON.stringify({\n"
                "    out,\n"
                "    generated: cand.headRefName,\n"
                "    matchesNew: DefaultBranchName.matches("
                "'release-please-branches-main'),\n"
                "    matchesLegacy: DefaultBranchName.matches("
                "'release-please--branches--main'),\n"
                "    parsedLegacy: new DefaultBranchName("
                "'release-please--branches--main').getTargetBranch(),\n"
                "    parsedNew: new DefaultBranchName("
                "'release-please-branches-main').getTargetBranch(),\n"
                "    autoreleaseHijack: AutoreleaseBranchName.matches("
                "'release-please-branches-v6.0'),\n"
                "    legacyRes,\n"
                "    freshRes,\n"
                "  }));\n"
                "})();\n",
                encoding="utf-8",
            )
            subprocess.run(
                ["node", "-", str(index_js)],
                input=node_block,
                text=True,
                check=True,
            )
            payload = json.loads(
                subprocess.check_output(
                    ["node", str(index_js)],
                    text=True,
                    env={
                        **os.environ,
                        "GITHUB_REPOSITORY": "google/stellar-engine",
                    },
                ).strip()
            )
        self.assertEqual(payload["out"], f"{base_line}\n  * {expected_sub}")
        self.assertEqual(payload["generated"], "release-please-branches-main")
        self.assertTrue(payload["matchesNew"])
        self.assertTrue(payload["matchesLegacy"])
        self.assertEqual(payload["parsedLegacy"], "main")
        self.assertEqual(payload["parsedNew"], "main")
        self.assertFalse(payload["autoreleaseHijack"])
        self.assertEqual(
            payload["legacyRes"],
            {
                "mode": "maybe",
                "number": 394,
                "headRefName": "release-please--branches--main",
                "title": "release: v6.0.0",
            },
        )
        self.assertEqual(
            payload["freshRes"],
            {"mode": "create", "headRefName": "release-please-branches-main"},
        )
        gemini_md = (_REPO_ROOT / "GEMINI.md").read_text(encoding="utf-8")
        self.assertIn("`release-please-branches-main`", gemini_md)
        self.assertNotIn("`release-please--branches--main`", gemini_md)

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
