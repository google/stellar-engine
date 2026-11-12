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

import base64
import json
import os
import pathlib
import shutil
import subprocess
import tempfile
import unittest
import unittest.mock

import release_please

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]

_UPSTREAM_TEMPLATE_HBS = (
    "{{> header}}\n\n"
    "{{#if noteGroups}}\n"
    "{{#each noteGroups}}\n\n"
    "### \u26a0 {{title}}\n\n"
    "{{#each notes}}\n"
    "* {{#if commit.scope}}**{{commit.scope}}:** {{/if}}{{text}}\n"
    "{{/each}}\n"
    "{{/each}}\n"
    "{{/if}}\n"
)


def _upstream_index_js(rendered_notes):
    return (
        "const fs = undefined;\n"
        "const RELEASE_PLEASE = 'release-please';\n"
        "const RELEASE_PLEASE_BRANCH_PREFIX = 'release-please--branches';\n"
        "const AUTORELEASE_PATTERN = "
        "/^release-?(?<component>[\\w-.]*)?-v(?<version>[0-9].*)$/;\n"
        "const NOTES_DELIMITER = '---';\n"
        "class BranchName {\n"
        "    static ofTargetBranch(targetBranch) {\n"
        "        return new DefaultBranchName("
        "`${RELEASE_PLEASE}--branches--${targetBranch}`);\n"
        "    }\n"
        "    getTargetBranch() { return this.targetBranch; }\n"
        "}\n"
        "class AutoreleaseBranchName extends BranchName {\n"
        "    static matches(branchName) {\n"
        "        if (branchName.startsWith(RELEASE_PLEASE_BRANCH_PREFIX)) {\n"
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
        "        if (match && match.groups) {\n"
        "            this.targetBranch = match.groups['branch'];\n"
        "        }\n"
        "    }\n"
        "    toString() {\n"
        "        return `${RELEASE_PLEASE}--branches--${this.targetBranch}`;\n"
        "    }\n"
        "}\n"
        "async function notifyRelease(github, comment, pullRequest) {\n"
        "    const note = {};\n"
        "    note.title = 'BREAKING CHANGES';\n"
        "    await this.github.commentOnIssue(comment, pullRequest.number);\n"
        "    return note.title;\n"
        "}\n"
        "const preset = {writerOpts: {}};\n"
        "const context = {};\n"
        "const changelogCommits = [];\n"
        f"const writer = {{parseArray: () => {json.dumps(rendered_notes)}}};\n"
        "const out = writer\n"
        "            .parseArray("
        "changelogCommits, context, preset.writerOpts)\n"
        "            .trim();\n"
        "console.log(JSON.stringify({\n"
        "    out,\n"
        "    delimiter: NOTES_DELIMITER,\n"
        "    branch: BranchName.ofTargetBranch('main').toString(),\n"
        "    matchesSingleDash: DefaultBranchName.matches("
        "'release-please-branches-main'),\n"
        "    parsedTarget: new DefaultBranchName("
        "'release-please-branches-main').getTargetBranch(),\n"
        "    autoreleaseHijack: AutoreleaseBranchName.matches("
        "'release-please-branches-v6.0'),\n"
        "}));\n"
    )


class TestReleasePlease(unittest.TestCase):
    def test_normalize_gh_refs_formats_links_and_preserves_non_mentions(self):
        sample = (
            "Follows up on #197 with @Calvin-Cheng1. Also "
            "https://github.com/google/stellar-engine/pull/352#r1 and "
            "[Full Title (#14)]"
            "(https://github.com/google/stellar-engine/issues/14) "
            "plus aquasecurity/tfsec#99 while keeping `#42`, "
            "`#000000`/#000000, "
            "@google-cloud/storage, @pytest.fixture, and ops@example.com."
        )

        normalized = release_please.normalize_gh_refs(sample)

        self.assertEqual(
            normalized,
            "Follows up on "
            "[#197](https://github.com/google/stellar-engine/issues/197) "
            "with Calvin-Cheng1. Also "
            "[#352](https://github.com/google/stellar-engine/pull/352) and "
            "[#14](https://github.com/google/stellar-engine/issues/14) plus "
            "[aquasecurity/tfsec#99]"
            "(https://github.com/aquasecurity/tfsec/issues/99) "
            "while keeping `#42`, `#000000`/#000000, "
            "@google-cloud/storage, @pytest.fixture, and ops@example.com.",
        )

    def test_extract_existing_scopes_sections_and_handles_closes_suffix(self):
        commit_url = (
            "https://github.com/google/stellar-engine/commit/"
            "d87fdc39fef5b865012ac7e905ea824d105e7e83"
        )
        closes_url = (
            "https://github.com/google/stellar-engine/commit/"
            "d843aec5243d0207c048df819084b80babe307e1"
        )
        bullet = (
            f"* **networking:** modernize stage 2 ([d87fdc3]({commit_url}))"
        )
        closes_bullet = (
            f"* **deploy.sh:** remove kms vars ([d843aec]({closes_url})), "
            "closes [#229](https://github.com/google/stellar-engine/issues/229)"
        )
        changelog = (
            "## [6.0.0]\n\n"
            "### Breaking Changes\n\n"
            f"{bullet}\n"
            "  * Replaces legacy VDSS networking, requiring state "
            "migration.\n\n"
            "### Features\n\n"
            f"{bullet}\n"
            "  * Adds central hub-0 VPC and STAR NCC topology, fixing #404.\n\n"
            "### Bug Fixes\n\n"
            f"{closes_bullet}\n"
            "  * Resolves plan failure on deprecated KMS arguments.\n\n"
            "## [5.0.0]\n\n"
            "### Features\n\n"
            f"{bullet}\n"
            "  * Older entry that should not overwrite 6.0.0.\n"
        )

        extracted = release_please.extract_existing(changelog)

        self.assertEqual(
            extracted,
            {
                "breaking:d87fdc3": (
                    "Replaces legacy VDSS networking, requiring state "
                    "migration."
                ),
                "d87fdc3": (
                    "Adds central hub-0 VPC and STAR NCC topology, fixing "
                    "[#404](https://github.com/google/stellar-engine/"
                    "issues/404)."
                ),
                "d843aec": (
                    "Resolves plan failure on deprecated KMS arguments."
                ),
            },
        )

        repo_changelog = (_REPO_ROOT / "CHANGELOG.md").read_text(
            encoding="utf-8"
        )
        repo_extracted = release_please.extract_existing(repo_changelog)
        for closes_sha in ("d843aec", "6d7d08c", "1b0aa34", "2bec226"):
            self.assertIn(closes_sha, repo_extracted)

    def test_fallback_sub_bullet_skips_breaking_footer_duplication(self):
        pr_body = (
            "## Description\n"
            "Replaces `foo` with `bar` across Stage 2 templates so existing "
            "deployments must migrate state.\n"
        )
        commit_msg = (
            "feat(networking)!: replace foo with bar\n\n"
            "BREAKING CHANGE: `foo` is removed;\n"
            "use `bar` across Stage 2."
        )
        explicit_override = (
            "<!-- breaking-note: Removes `var.foo`. Set `var.bar` before "
            "upgrading. -->\n" + pr_body
        )

        self.assertEqual(
            release_please.fallback_sub_bullet(
                pr_body, commit_msg, breaking=True
            ),
            "Replaces `foo` with `bar` across Stage 2 templates so existing "
            "deployments must migrate state",
        )
        self.assertEqual(
            release_please.fallback_sub_bullet(
                explicit_override, commit_msg, breaking=True
            ),
            "Removes `var.foo`. Set `var.bar` before upgrading",
        )
        self.assertEqual(
            release_please.fallback_sub_bullet("", commit_msg, breaking=True),
            "",
        )

    def test_fallback_sub_bullet_joins_wrapped_paragraphs_and_splits_acronyms(
        self,
    ):
        wrapped_pr = (
            "## Description\n"
            "<!-- template comment -->\n"
            "Aligns U.S. Government KMS levels (e.g. FedRAMP High HSM vs.\n"
            "software keys) on private GKE. Follow-up details appear next.\n\n"
            "Fixes #311\n"
            "## Type of Change\n"
            "- [x] Bug fix\n"
        )
        bullet_pr = (
            "## Description\n"
            "Summary of changes:\n\n"
            "- **Central Hub**: Replaces the two-VPC topology with `hub-0`.\n"
        )
        body_only_commit = (
            "fix(cli): handle empty lists\n\n"
            "Returns an empty list when no data stores exist.\n"
            "Co-authored-by: Example User <user@example.com>\n"
        )

        self.assertEqual(
            release_please.fallback_sub_bullet(wrapped_pr, ""),
            "Aligns U.S. Government KMS levels (e.g. FedRAMP High HSM vs. "
            "software keys) on private GKE",
        )
        self.assertEqual(
            release_please.fallback_sub_bullet(bullet_pr, ""),
            "Replaces the two-VPC topology with `hub-0`",
        )
        self.assertEqual(
            release_please.fallback_sub_bullet("", body_only_commit),
            "Returns an empty list when no data stores exist",
        )

    def test_gemini_sub_bullet_calls_gemini_3_8_flash_and_normalizes_output(
        self,
    ):
        captured = {}

        class _FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self):
                return json.dumps(
                    {
                        "candidates": [
                            {
                                "content": {
                                    "parts": [
                                        {
                                            "text": (
                                                "- Updates Stage 2 routing "
                                                "with @Calvin-Cheng1, "
                                                "fixing #404\n"
                                            )
                                        }
                                    ]
                                }
                            }
                        ]
                    }
                ).encode("utf-8")

        def fake_urlopen(req, timeout=0):
            captured["url"] = req.full_url
            captured["timeout"] = timeout
            captured["body"] = json.loads(req.data.decode("utf-8"))
            return _FakeResponse()

        with unittest.mock.patch(
            "urllib.request.urlopen", side_effect=fake_urlopen
        ):
            summary = release_please.gemini_sub_bullet(
                "feat(networking)!: modernize stage 2 (#404)",
                "## Description\nModernizes Stage 2.",
                ["fast/stages-aw/2-networking-a-fedramp/main.tf"],
                gemini_key="test-gemini-key",
                breaking=True,
            )

        self.assertEqual(
            captured["url"],
            "https://generativelanguage.googleapis.com/v1beta/models/"
            "gemini-3.8-flash:generateContent?key=test-gemini-key",
        )
        self.assertEqual(
            summary,
            "Updates Stage 2 routing with Calvin-Cheng1, fixing "
            "[#404](https://github.com/google/stellar-engine/issues/404).",
        )

    def test_collect_sub_bullets_resolves_pr_from_commit_subject(self):
        manifest_b64 = base64.b64encode(b'{".": "6.0.0"}').decode("ascii")
        calls = []

        def fake_fetch(path):
            calls.append(path)
            if (
                path
                == "contents/.github/.release-please-manifest.json?ref=main"
            ):
                return {"content": manifest_b64}
            if path == "compare/v6.0.0...main":
                return {
                    "commits": [
                        {
                            "sha": "162c7feb644d3bc9",
                            "commit": {
                                "message": (
                                    "feat(modules)!: sync modules (#311)\n\n"
                                    "BREAKING CHANGE: Raises Terraform floor "
                                    "to >= 1.12.2."
                                )
                            },
                        },
                        {
                            "sha": "bbbb222000000000",
                            "commit": {
                                "message": (
                                    "fix(cli): guard empty response\n\n"
                                    "Prevents KeyError on empty store list, "
                                    "fixing #336."
                                )
                            },
                        },
                        {
                            "sha": "cccc333000000000",
                            "commit": {"message": "ci(lint): speed up cache"},
                        },
                    ]
                }
            if path == "pulls/311":
                return {
                    "body": (
                        "<!-- breaking-note: Upgrades provider floor to >= "
                        "8.10.0 across vendored modules. -->\n"
                        "## Description\n"
                        "Syncs vendored modules to v60.0.0, closing #308.\n"
                    )
                }
            if path == "commits/bbbb222000000000/pulls":
                return []
            return None

        sub_bullets = release_please.collect_sub_bullets(
            token="test-token", fetcher=fake_fetch
        )

        self.assertEqual(
            sub_bullets,
            {
                "breaking:162c7fe": (
                    "Upgrades provider floor to >= 8.10.0 across vendored "
                    "modules."
                ),
                "162c7fe": (
                    "Syncs vendored modules to v60.0.0, closing "
                    "[#308](https://github.com/google/stellar-engine/"
                    "issues/308)."
                ),
                "bbbb222": (
                    "Prevents KeyError on empty store list, fixing "
                    "[#336](https://github.com/google/stellar-engine/"
                    "issues/336)."
                ),
            },
        )
        self.assertNotIn("commits/162c7feb644d3bc9/pulls", calls)
        self.assertNotIn("commits/cccc333000000000/pulls", calls)

    def test_patch_dist_scopes_sub_bullets_and_matches_closes_suffix(self):
        if not shutil.which("node"):
            self.skipTest("node is required to execute patched bundle")

        commit_line = (
            "* **networking:** modernize stage 2 "
            "([d87fdc3](https://github.com/google/stellar-engine/"
            "commit/d87fdc39fef5b865))"
        )
        closes_line = (
            "* **deploy.sh:** remove kms vars "
            "([d843aec](https://github.com/google/stellar-engine/"
            "commit/d843aec5243d0207)), closes "
            "[#229](https://github.com/google/stellar-engine/issues/229)"
        )
        raw_notes = (
            f"### Breaking Changes\n\n{commit_line}\n\n"
            f"### Features\n\n{commit_line}\n\n"
            f"### Bug Fixes\n\n{closes_line}"
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            dist_dir = pathlib.Path(tmpdir) / "dist"
            dist_dir.mkdir()
            sub_path = pathlib.Path(tmpdir) / "sub_bullets.json"
            sub_path.write_text(
                json.dumps(
                    {
                        "breaking:d87fdc3": "Requires state migration.",
                        "d87fdc3": "Adds STAR NCC hub topology.",
                        "d843aec": "Removes deprecated KMS tfvars output.",
                    }
                ),
                encoding="utf-8",
            )
            (dist_dir / "template1.hbs").write_text(
                _UPSTREAM_TEMPLATE_HBS, encoding="utf-8"
            )
            (dist_dir / "index.js").write_text(
                _upstream_index_js(raw_notes), encoding="utf-8"
            )

            release_please.patch_dist(dist_dir, sub_bullets_path=sub_path)

            patched_hbs = (dist_dir / "template1.hbs").read_text(
                encoding="utf-8"
            )
            self.assertNotIn("\u26a0", patched_hbs)
            self.assertIn(
                "([{{commit.shortHash}}]"
                "({{@root.host}}/{{@root.owner}}/{{@root.repository}}/"
                "commit/{{commit.hash}}))",
                patched_hbs,
            )

            payload = json.loads(
                subprocess.check_output(
                    ["node", str(dist_dir / "index.js")],
                    text=True,
                    env={
                        **os.environ,
                        "RELEASE_SUB_BULLETS_PATH": str(sub_path),
                    },
                ).strip()
            )

        self.assertEqual(
            payload["out"],
            f"### Breaking Changes\n\n{commit_line}\n"
            "  * Requires state migration.\n\n"
            f"### Features\n\n{commit_line}\n"
            "  * Adds STAR NCC hub topology.\n\n"
            f"### Bug Fixes\n\n{closes_line}\n"
            "  * Removes deprecated KMS tfvars output.",
        )
        self.assertEqual(payload["delimiter"], "<!-- release-please-notes -->")
        self.assertEqual(payload["branch"], "release-please-branches-main")
        self.assertTrue(payload["matchesSingleDash"])
        self.assertEqual(payload["parsedTarget"], "main")
        self.assertFalse(payload["autoreleaseHijack"])

    def test_patch_dist_fails_atomically_when_index_anchor_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            dist_dir = pathlib.Path(tmpdir)
            hbs_path = dist_dir / "template1.hbs"
            hbs_path.write_text(_UPSTREAM_TEMPLATE_HBS, encoding="utf-8")
            (dist_dir / "index.js").write_text("", encoding="utf-8")

            with self.assertRaisesRegex(RuntimeError, "Expected 1 occurrence"):
                release_please.patch_dist(dist_dir)

            self.assertEqual(
                hbs_path.read_text(encoding="utf-8"), _UPSTREAM_TEMPLATE_HBS
            )

    def test_prepare_cli_patches_dist_and_tolerates_collection_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = pathlib.Path(tmpdir)
            runner_temp = root / "_temp"
            runner_temp.mkdir()
            dist_dir = (
                root / "_actions/googleapis/release-please-action/v5/dist"
            )
            dist_dir.mkdir(parents=True)
            (dist_dir / "template1.hbs").write_text(
                _UPSTREAM_TEMPLATE_HBS, encoding="utf-8"
            )
            (dist_dir / "index.js").write_text(
                _upstream_index_js("### Features"), encoding="utf-8"
            )
            sub_path = runner_temp / "sub_bullets.json"

            with (
                unittest.mock.patch.dict(
                    os.environ,
                    {
                        "RUNNER_TEMP": str(runner_temp),
                        "RELEASE_SUB_BULLETS_PATH": str(sub_path),
                    },
                    clear=False,
                ),
                unittest.mock.patch.object(
                    release_please,
                    "collect_sub_bullets",
                    side_effect=ValueError("malformed API payload"),
                ),
            ):
                release_please.main(["prepare"])

            self.assertEqual(
                json.loads(sub_path.read_text(encoding="utf-8")), {}
            )
            self.assertNotIn(
                "\u26a0",
                (dist_dir / "template1.hbs").read_text(encoding="utf-8"),
            )


if __name__ == "__main__":
    unittest.main()
