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

"""Checks that the bastion pattern firewall rule targets the bastion."""

import pathlib
import re
import unittest

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
_MAIN_TF = _REPO_ROOT / "blueprints/il5/bastion-pattern/main.tf"
_SERVICE_ACCOUNT = "google_service_account.compute.email"


def _top_block(text, header):
    """Returns the top-level HCL block that starts with header."""
    match = re.search(re.escape(header) + r"\s*\{[\s\S]*?\n\}", text)
    if match is None:
        raise AssertionError(f"Block not found: {header}")
    return match.group(0)


class TestBastionPatternFirewall(unittest.TestCase):
    def setUp(self):
        self.main_tf = _MAIN_TF.read_text(encoding="utf-8")
        self.firewall = _top_block(
            self.main_tf, 'resource "google_compute_firewall" "default"'
        )

    def test_firewall_targets_the_bastion_service_account(self):
        # An ingress rule without a target applies to every instance in
        # the network, so the rule names the bastion service account.
        self.assertRegex(
            self.firewall,
            r"\n\s*target_service_accounts\s*=\s*\[\s*"
            + re.escape(_SERVICE_ACCOUNT)
            + r"\s*\]\n",
        )
        # The API rejects rules that mix service account and tag targets.
        self.assertNotIn("target_tags", self.firewall)
        self.assertNotIn("source_tags", self.firewall)

    def test_bastion_vm_runs_as_the_targeted_service_account(self):
        # The target only matches when the VM runs as the same account.
        bastion_vm = _top_block(self.main_tf, 'module "bastion-vm"')
        self.assertRegex(
            bastion_vm,
            r"service_account\s*=\s*\{\s*email\s*=\s*"
            + re.escape(_SERVICE_ACCOUNT)
            + r"\s*\}",
        )

    def test_firewall_keeps_source_ranges_and_logging(self):
        self.assertRegex(
            self.firewall,
            r"\n\s*source_ranges\s*=\s*var\.allowed_source_ranges\n",
        )
        self.assertRegex(
            self.firewall,
            r'log_config\s*\{\s*metadata\s*=\s*"INCLUDE_ALL_METADATA"\s*\}',
        )


if __name__ == "__main__":
    unittest.main()
