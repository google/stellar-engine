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

"""Checks that Dependabot covers every pinned manifest in the repository."""

import pathlib
import subprocess
import unittest

import yaml

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
_MIN_COOLDOWN_DAYS = 14
# Types that semantic-pr.yml accepts and that never reach the CHANGELOG.
_SILENT_PREFIXES = frozenset({"build", "ci", "chore"})
# Manifest file names that each Dependabot ecosystem reads.
_MANIFESTS = {
    "docker": "Dockerfile",
    "npm": "package.json",
    "uv": "uv.lock",
}
_EXPECTED_LABELS = {
    "docker": ["Dependencies - Docker"],
    "github-actions": ["Dependencies - GitHub Actions"],
    "npm": ["Dependencies - JavaScript"],
    "uv": ["Dependencies - Python"],
}


def _load_updates():
    path = _REPO_ROOT / ".github/dependabot.yml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))["updates"]


def _directories(update):
    if "directories" in update:
        return set(update["directories"])
    return {update["directory"]}


def _is_synced_from_fabric(manifest_dir):
    """Reports whether tools/sync-from-cff.sh owns the manifest directory.

    The sync records the upstream release in each module's versions.tf file.
    Upstream Dependabot updates those manifests, so local updates would only
    conflict with the next sync.
    """
    parts = pathlib.PurePosixPath(manifest_dir).parts
    if len(parts) < 3 or parts[1] != "modules":
        return False
    versions = _REPO_ROOT / "modules" / parts[2] / "versions.tf"
    return versions.is_file() and "# Fabric release:" in versions.read_text(
        encoding="utf-8"
    )


def _tracked_manifest_dirs(file_name):
    output = subprocess.run(
        ["git", "ls-files", f"*{file_name}"],
        cwd=_REPO_ROOT,
        capture_output=True,
        check=True,
        text=True,
    ).stdout
    dirs = set()
    for path in output.splitlines():
        path = pathlib.PurePosixPath(path)
        if path.name == file_name:
            parent = str(path.parent)
            dirs.add("/" if parent == "." else f"/{parent}")
    return dirs


class TestDependabot(unittest.TestCase):
    def test_github_actions_are_covered(self):
        ecosystems = {update["package-ecosystem"] for update in _load_updates()}
        self.assertIn("github-actions", ecosystems)

    def test_every_manifest_is_covered(self):
        updates = _load_updates()
        for ecosystem, file_name in _MANIFESTS.items():
            with self.subTest(ecosystem=ecosystem):
                covered = set()
                for update in updates:
                    if update["package-ecosystem"] == ecosystem:
                        covered |= _directories(update)
                missing = {
                    d
                    for d in _tracked_manifest_dirs(file_name) - covered
                    if not _is_synced_from_fabric(d)
                }
                self.assertFalse(missing, f"no {ecosystem} entry for {missing}")

    def test_only_fabric_modules_skip_coverage(self):
        self.assertTrue(
            _is_synced_from_fabric(
                "/modules/api-gateway/recipe-multi-region/function"
            )
        )
        self.assertFalse(
            _is_synced_from_fabric("/modules/intrusion-detection-system")
        )
        self.assertFalse(_is_synced_from_fabric("/blueprints/x/modules/y"))

    def test_every_update_waits_and_uses_a_silent_prefix(self):
        for update in _load_updates():
            with self.subTest(ecosystem=update["package-ecosystem"]):
                self.assertGreaterEqual(
                    update["cooldown"]["default-days"], _MIN_COOLDOWN_DAYS
                )
                self.assertIn(
                    update["commit-message"]["prefix"], _SILENT_PREFIXES
                )
                self.assertEqual(update["commit-message"]["include"], "scope")
                self.assertEqual(
                    update["labels"],
                    _EXPECTED_LABELS[update["package-ecosystem"]],
                )


if __name__ == "__main__":
    unittest.main()
