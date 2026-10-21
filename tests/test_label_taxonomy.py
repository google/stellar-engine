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
import pathlib
import re
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
