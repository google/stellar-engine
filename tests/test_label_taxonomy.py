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
                "console.log(out);\n",
                encoding="utf-8",
            )
            subprocess.run(
                ["node", "-", str(index_js)],
                input=node_block,
                text=True,
                check=True,
            )
            rendered = subprocess.check_output(
                ["node", str(index_js)],
                text=True,
                env={
                    **os.environ,
                    "GITHUB_REPOSITORY": "google/stellar-engine",
                },
            ).strip()
        self.assertEqual(rendered, f"{base_line}\n  * {expected_sub}")

    def test_dependabot_uses_only_curated_labels(self):
        dependabot_path = _REPO_ROOT / ".github/dependabot.yml"
        config = yaml.safe_load(dependabot_path.read_text(encoding="utf-8"))
        for update in config.get("updates", []):
            with self.subTest(ecosystem=update.get("package-ecosystem")):
                labels = update.get("labels", [])
                self.assertTrue(labels)
                self.assertTrue(set(labels).issubset(_CURATED_LABELS))


if __name__ == "__main__":
    unittest.main()
