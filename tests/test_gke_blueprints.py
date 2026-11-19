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

"""Checks node privacy and identifier inputs of the GKE blueprints."""

import pathlib
import re
import unittest

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
_GKE_DIR = _REPO_ROOT / "blueprints/il5/gke"
_GKE_HARDENED_DIR = _REPO_ROOT / "blueprints/il5/gke-hardened"

# The secret types Config Sync accepts for a Git repository.
_GIT_SECRET_TYPES = {
    "cookiefile",
    "gcenode",
    "gcpserviceaccount",
    "githubapp",
    "none",
    "ssh",
    "token",
}


def _read(directory, name):
    return (directory / name).read_text(encoding="utf-8")


def _top_block(text, header):
    """Returns the top-level HCL block that starts with header."""
    match = re.search(re.escape(header) + r"\s*\{[\s\S]*?\n\}", text)
    if match is None:
        raise AssertionError(f"Block not found: {header}")
    return match.group(0)


def _account_id(block):
    """Returns the account_id expression of a block without whitespace."""
    match = re.search(r"\n\s*account_id\s*=\s*([\s\S]*?\)\n|[^\n]*\n)", block)
    if match is None:
        raise AssertionError("account_id not found")
    return re.sub(r"\s+", "", match.group(1))


class TestGkeBlueprints(unittest.TestCase):
    def test_nodes_are_always_private(self):
        # Node privacy must not follow the control plane endpoint toggle.
        for directory in (_GKE_DIR, _GKE_HARDENED_DIR):
            with self.subTest(blueprint=directory.name):
                cluster = _top_block(
                    _read(directory, "main.tf"), 'module "cluster"'
                )
                self.assertEqual(
                    re.findall(r"private_nodes\s*=\s*(\S+)", cluster),
                    ["true"],
                )

    def test_service_account_ids_fit_the_length_limit(self):
        # Account IDs allow at most 30 characters and no trailing hyphen,
        # so the blueprints cut the ID and strip every trailing hyphen.
        cases = (
            (
                _GKE_DIR,
                'resource "google_service_account" "gke_cluster_sa"',
                '"gke-sa-${var.gke_cluster_name}"',
            ),
            (
                _GKE_HARDENED_DIR,
                'resource "google_service_account" "gke"',
                '"gke-${var.main_project_id}"',
            ),
        )
        for directory, header, name in cases:
            with self.subTest(blueprint=directory.name):
                block = _top_block(_read(directory, "main.tf"), header)
                self.assertEqual(
                    _account_id(block),
                    f'replace(substr({name},0,30),"/-+$/","")',
                )

    def test_config_sync_secret_type_is_a_validated_variable(self):
        main_tf = _read(_GKE_HARDENED_DIR, "main.tf")
        self.assertEqual(
            re.findall(r"secret_type\s*=\s*(\S+)", main_tf),
            ["var.config_sync_secret_type"],
        )
        variable = _top_block(
            _read(_GKE_HARDENED_DIR, "variables.tf"),
            'variable "config_sync_secret_type"',
        )
        # The default keeps the behavior of unauthenticated repositories.
        self.assertRegex(variable, r'\n\s*default\s*=\s*"none"\n')
        condition = re.search(
            r"condition\s*=\s*contains\(\s*\[([^\]]*)\]", variable
        )
        self.assertIsNotNone(condition)
        self.assertEqual(
            set(re.findall(r'"([^"]+)"', condition.group(1))),
            _GIT_SECRET_TYPES,
        )


if __name__ == "__main__":
    unittest.main()
