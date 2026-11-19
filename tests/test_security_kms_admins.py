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

"""Checks the restricted KMS admin lists in the security stage."""

import pathlib
import re
import unittest

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
_SECURITY_DIR = _REPO_ROOT / "fast/stages-aw/3-security"

_ACCOUNT_REF = re.compile(r"var\.service_accounts\.([a-z-]+)")
_ATTRIBUTE = re.compile(r"^\s+([a-z-]+)\s+=\s+(\S+)$", re.MULTILINE)
_BRANCHES = ("data-platform", "gcve", "gke", "project-factory")


def _core_text(env):
    return (_SECURITY_DIR / f"core-{env}.tf").read_text(encoding="utf-8")


def _admin_accounts(env):
    """Returns the account keys inside the compact() call of the env list.

    Stage 1 emits null for the branches that are not enabled, so the match
    requires the compact() wrapper that drops those entries.
    """
    block = re.search(
        rf"{env}_kms_restricted_admins = \[\n"
        r"    for sa in distinct\(compact\(\[\n(.*?)\n    \]\)\) :",
        _core_text(env),
        re.DOTALL,
    )
    return _ACCOUNT_REF.findall(block.group(1))


def _service_accounts_type():
    """Returns the service_accounts attributes as a name to type mapping."""
    text = (_SECURITY_DIR / "variables.tf").read_text(encoding="utf-8")
    block = re.search(
        r'variable "service_accounts" \{.*?type = object\(\{\n(.*?)\n  \}\)',
        text,
        re.DOTALL,
    )
    return dict(_ATTRIBUTE.findall(block.group(1)))


class TestKmsRestrictedAdmins(unittest.TestCase):
    def test_lists_hold_only_matching_environment_accounts(self):
        for env in ("dev", "prod"):
            with self.subTest(env=env):
                self.assertEqual(
                    _admin_accounts(env),
                    [f"{branch}-{env}" for branch in _BRANCHES],
                )

    def test_accounts_are_referenced_only_inside_compact(self):
        # A reference outside the compact() call fails on a null account.
        for env in ("dev", "prod"):
            with self.subTest(env=env):
                self.assertEqual(
                    _ACCOUNT_REF.findall(_core_text(env)),
                    _admin_accounts(env),
                )

    def test_variable_declares_every_referenced_account(self):
        attributes = _service_accounts_type()
        referenced = _admin_accounts("dev") + _admin_accounts("prod")
        self.assertEqual(sorted(referenced), list(attributes))

    def test_gcve_and_gke_accounts_are_optional(self):
        attributes = _service_accounts_type()
        for key, attribute_type in attributes.items():
            with self.subTest(key=key):
                optional = key.startswith(("gcve-", "gke-"))
                self.assertEqual(
                    attribute_type,
                    "optional(string)" if optional else "string",
                )


if __name__ == "__main__":
    unittest.main()
