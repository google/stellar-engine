# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Unit tests for tools/check_documentation.py."""

import os
import pathlib
import tempfile
import unittest
import unittest.mock as mock

import check_documentation
from click.testing import CliRunner


class TestCheckDocumentation(unittest.TestCase):
    """Validates README, TFDOC, and TOC enforcement in check_documentation."""

    def test_missing_readme_in_tf_dir(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            bp = root / "blueprints" / "sample"
            bp.mkdir(parents=True)
            (bp / "main.tf").write_text("# tf\n", encoding="utf-8")

            with mock.patch.object(check_documentation, "BASEDIR", root):
                results = list(check_documentation._check_dir("blueprints"))

            self.assertEqual(len(results), 1)
            self.assertEqual(results[0][0], "blueprints/sample/README.md")
            self.assertEqual(
                results[0][1], check_documentation.State.FAIL_MISSING_README
            )

    def test_missing_tfdoc_in_blueprint_vs_tf_docs_in_module(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            bp = root / "blueprints" / "no-tfdoc"
            bp.mkdir(parents=True)
            (bp / "main.tf").write_text("# tf\n", encoding="utf-8")
            (bp / "README.md").write_text("# Sample\n", encoding="utf-8")

            mod = root / "modules" / "legacy"
            mod.mkdir(parents=True)
            (mod / "main.tf").write_text("# tf\n", encoding="utf-8")
            (mod / "README.md").write_text(
                "# Legacy\n\n<!-- BEGIN_TF_DOCS -->\n<!-- END_TF_DOCS -->\n",
                encoding="utf-8",
            )

            with mock.patch.object(check_documentation, "BASEDIR", root):
                bp_results = list(check_documentation._check_dir("blueprints"))
                mod_results = list(check_documentation._check_dir("modules"))

            self.assertEqual(
                bp_results[0][1], check_documentation.State.FAIL_MISSING_TFDOC
            )
            self.assertEqual(mod_results, [])

    def test_malformed_and_duplicate_markers(self):
        cases = {
            "duplicate_tfdoc": (
                "# Sample\n\n"
                "<!-- BEGIN TFDOC -->\n<!-- END TFDOC -->\n"
                "<!-- BEGIN TFDOC -->\n<!-- END TFDOC -->\n"
            ),
            "mismatched_end_toc": (
                "# Sample\n\n<!-- BEGIN TFDOC -->\n<!-- END TOC -->\n"
            ),
            "legacy_toc_tag": (
                "# Sample\n\n<!-- TOC -->\n"
                "<!-- BEGIN TFDOC -->\n<!-- END TFDOC -->\n"
            ),
            "triple_dash_end_toc": (
                "# Sample\n\n<!-- BEGIN TOC -->\n<!--- END TOC -->\n"
                "<!-- BEGIN TFDOC -->\n<!-- END TFDOC -->\n"
            ),
            "start_toc_tag": (
                "# Sample\n\n<!-- START TOC -->\n<!-- END TOC -->\n"
                "<!-- BEGIN TFDOC -->\n<!-- END TFDOC -->\n"
            ),
        }
        for name, readme_text in cases.items():
            with (
                self.subTest(case=name),
                tempfile.TemporaryDirectory() as td,
            ):
                root = pathlib.Path(td)
                bp = root / "blueprints" / name
                bp.mkdir(parents=True)
                (bp / "main.tf").write_text("# tf\n", encoding="utf-8")
                (bp / "README.md").write_text(readme_text, encoding="utf-8")
                with mock.patch.object(check_documentation, "BASEDIR", root):
                    results = list(check_documentation._check_dir("blueprints"))
                self.assertEqual(len(results), 1)
                self.assertEqual(
                    results[0][1],
                    check_documentation.State.FAIL_MALFORMED_MARKERS,
                )

    def test_tfdoc_opts_allowed_and_docs_toc_checked(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            bp = root / "blueprints" / "gitlab"
            bp.mkdir(parents=True)
            (bp / "main.tf").write_text("# tf\n", encoding="utf-8")
            (bp / "README.md").write_text(
                "# Title\n\n<!-- TFDOC OPTS files:1 show_extra:1 -->\n"
                "<!-- BEGIN TFDOC -->\n\n"
                "## Files\n\n"
                "| name | description |\n"
                "|---|---|\n"
                "| [main.tf](./main.tf) | Module-level locals and resources."
                " |\n\n"
                "<!-- END TFDOC -->\n",
                encoding="utf-8",
            )

            link_parent = root / "blueprints" / "fedramp-high"
            link_parent.mkdir(parents=True)
            os.symlink(bp, link_parent / "gitlab")

            docs = root / "docs"
            docs.mkdir()
            (docs / "guide.md").write_text(
                "# Guide\n\n<!-- BEGIN TOC -->\n<!-- END TOC -->\n\n"
                "## Overview\n",
                encoding="utf-8",
            )

            runner = CliRunner()
            with mock.patch.object(check_documentation, "BASEDIR", root):
                res_bp = runner.invoke(
                    check_documentation.main,
                    ["--no-show-summary", "blueprints"],
                )
                self.assertEqual(res_bp.exit_code, 0, res_bp.output)

                res_docs = runner.invoke(
                    check_documentation.main, ["--no-show-summary", "docs"]
                )
                self.assertNotEqual(res_docs.exit_code, 0)
                self.assertIn("docs/guide.md", res_docs.output)

    def test_legacy_gitlab_toc_exemption(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            bp = root / "blueprints" / "third-party-solutions" / "gitlab"
            bp.mkdir(parents=True)
            (bp / "main.tf").write_text("# tf\n", encoding="utf-8")
            (bp / "README.md").write_text(
                "# Gitlab\n\n<!-- TOC -->\n* [Gitlab](#gitlab)\n"
                "<!-- TOC -->\n\n<!-- BEGIN TFDOC -->\n<!-- END TFDOC -->\n",
                encoding="utf-8",
            )
            with mock.patch.object(check_documentation, "BASEDIR", root):
                results = list(check_documentation._check_dir("blueprints"))
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0][1], check_documentation.State.OK)

            (bp / "README.md").write_text(
                "# Gitlab\n\n<!-- TOC -->\n"
                "<!-- BEGIN TFDOC -->\n<!-- END TFDOC -->\n",
                encoding="utf-8",
            )
            with mock.patch.object(check_documentation, "BASEDIR", root):
                results = list(check_documentation._check_dir("blueprints"))
            self.assertEqual(len(results), 1)
            self.assertEqual(
                results[0][1],
                check_documentation.State.FAIL_MALFORMED_MARKERS,
            )

    def test_skips_vendored_cff_modules_but_checks_se_and_stellar_modules(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            (root / "tools").mkdir()
            (root / "tools" / "cff-sync.bases").write_text(
                "project-factory project-factory v60.0.0\n"
                "tools/tfdoc.py tools/tfdoc.py v60.0.0\n",
                encoding="utf-8",
            )

            # Plain vendored CFF module via versions.tf provider_meta.
            cff_mod = root / "modules" / "artifact-registry"
            cff_mod.mkdir(parents=True)
            (cff_mod / "main.tf").write_text("# tf\n", encoding="utf-8")
            (cff_mod / "versions.tf").write_text(
                'terraform {\n  provider_meta "google" {\n'
                '    module_name = "google-pso-tool/'
                'cloud-foundation-fabric/modules/artifact-registry:v60.0.0-tf"'
                "\n  }\n}\n",
                encoding="utf-8",
            )
            (cff_mod / "README.md").write_text(
                "# Vendored stale\n", encoding="utf-8"
            )
            nested = cff_mod / "recipe-nested"
            nested.mkdir()
            (nested / "main.tf").write_text("# tf\n", encoding="utf-8")

            # Bare module tracked in tools/cff-sync.bases.
            factory = root / "modules" / "project-factory"
            factory.mkdir(parents=True)
            (factory / "main.tf").write_text("# tf\n", encoding="utf-8")
            (factory / "README.md").write_text("# Factory\n", encoding="utf-8")

            # -se fork must still be checked even if versions.tf has CFF meta.
            se_mod = root / "modules" / "spanner-instance-se"
            se_mod.mkdir(parents=True)
            (se_mod / "main.tf").write_text("# tf\n", encoding="utf-8")
            (se_mod / "versions.tf").write_text(
                'terraform {\n  provider_meta "google" {\n'
                '    module_name = "google-pso-tool/'
                'cloud-foundation-fabric/modules/spanner-instance:v60.0.0-tf"'
                "\n  }\n}\n",
                encoding="utf-8",
            )
            (se_mod / "README.md").write_text(
                "# Spanner SE\n", encoding="utf-8"
            )

            # Stellar-only module must still be checked.
            stellar_mod = root / "modules" / "app-engine"
            stellar_mod.mkdir(parents=True)
            (stellar_mod / "main.tf").write_text("# tf\n", encoding="utf-8")
            (stellar_mod / "README.md").write_text(
                "# App Engine\n", encoding="utf-8"
            )

            with mock.patch.object(check_documentation, "BASEDIR", root):
                results = list(check_documentation._check_dir("modules"))

            self.assertEqual(
                {rel: state for rel, state, _ in results},
                {
                    "modules/app-engine/README.md": (
                        check_documentation.State.FAIL_MISSING_TFDOC
                    ),
                    "modules/spanner-instance-se/README.md": (
                        check_documentation.State.FAIL_MISSING_TFDOC
                    ),
                },
            )


if __name__ == "__main__":
    unittest.main()
