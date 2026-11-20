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

"""Checks that sa_lockdown.sh reaches every Stage 0 and Stage 1 account.

sa_lockdown.sh disables the accounts that the 0-bootstrap and 1-resman stages
write under "service_accounts" in their tfvars files. An account that a stage
creates and does not write there stays enabled after the lockdown.
"""

import pathlib
import re
import unittest

_STAGES_DIR = pathlib.Path(__file__).resolve().parents[1] / "fast/stages-aw"
_BOOTSTRAP_DIR = _STAGES_DIR / "0-bootstrap"
_RESMAN_DIR = _STAGES_DIR / "1-resman"
_SECURITY_DIR = _STAGES_DIR / "3-security"

# The tenant accounts reach the tenant stages through the tenant tfvars files,
# which sa_lockdown.sh does not read.
_TENANT_FILE = "branch-tenants.tf"

_MODULE_BLOCK = re.compile(
    r'^module "(?P<name>[^"]+)" \{\n(?P<body>.*?)^\}', re.MULTILINE | re.DOTALL
)
_STATIC_KEY = re.compile(r"^\s+(?P<key>[a-z0-9-]+)\s+=", re.MULTILINE)


def _read(path):
    return path.read_text(encoding="utf-8")


def _resman_service_accounts_block():
    """Returns the local.service_accounts expression of the 1-resman stage."""
    match = re.search(
        r"^  service_accounts = merge\(\n(?P<body>.*?)^  \)$",
        _read(_RESMAN_DIR / "outputs.tf"),
        re.MULTILINE | re.DOTALL,
    )
    if match is None:
        raise AssertionError("local.service_accounts not found in 1-resman.")
    return match.group("body")


def _resman_static_keys():
    """Returns the static keys of local.service_accounts in 1-resman."""
    static_map = _resman_service_accounts_block().split("},", 1)[0]
    return set(_STATIC_KEY.findall(static_map))


def _bootstrap_static_keys():
    """Returns the service_accounts keys in the 0-bootstrap tfvars file."""
    match = re.search(
        r"^    automation = \{\n.*?^      service_accounts = \{\n"
        r"(?P<body>.*?)^      \}$",
        _read(_BOOTSTRAP_DIR / "outputs.tf"),
        re.MULTILINE | re.DOTALL,
    )
    if match is None:
        raise AssertionError("service_accounts not found in 0-bootstrap.")
    return set(_STATIC_KEY.findall(match.group("body")))


def _lockdown_names():
    """Returns the VALID_NAMES entries of sa_lockdown.sh."""
    match = re.search(
        r"^VALID_NAMES=\(\n(?P<body>.*?)^\)$",
        _read(_SECURITY_DIR / "sa_lockdown.sh"),
        re.MULTILINE | re.DOTALL,
    )
    if match is None:
        raise AssertionError("VALID_NAMES not found in sa_lockdown.sh.")
    return re.findall(r'"([^"]+)"', match.group("body"))


def _resman_branch_accounts():
    """Returns module name to body for the 1-resman branch accounts."""
    accounts = {}
    for path in sorted(_RESMAN_DIR.glob("branch-*.tf")):
        if path.name == _TENANT_FILE:
            continue
        for match in _MODULE_BLOCK.finditer(_read(path)):
            if 'modules/iam-service-account"' in match.group("body"):
                accounts[match.group("name")] = match.group("body")
    return accounts


class TestLockdownAccountCoverage(unittest.TestCase):
    def test_envs_account_is_written_to_tfvars(self):
        self.assertRegex(
            _resman_service_accounts_block(),
            r"(?m)^\s+envs\s+= "
            r"try\(module\.branch-envs-sa\[0\]\.email, null\)$",
        )

    def test_envs_account_matches_expected_module(self):
        body = _resman_branch_accounts()["branch-envs-sa"]
        self.assertRegex(body, r'(?m)^\s+name\s+= "prod-resman-envs-0"$')
        self.assertRegex(
            body, r"(?m)^\s+count\s+= var\.fast_features\.envs \? 1 : 0$"
        )

    def test_every_branch_account_is_written_to_tfvars(self):
        block = _resman_service_accounts_block()
        accounts = _resman_branch_accounts()
        self.assertGreaterEqual(len(accounts), 24)
        missing = [
            name
            for name in accounts
            if not re.search(
                r"module\." + re.escape(name) + r"\b[^\n]*\bemail\b", block
            )
        ]
        self.assertEqual(
            [],
            missing,
            "1-resman creates these accounts and does not write them to "
            "service_accounts, so sa_lockdown.sh cannot disable them.",
        )

    def test_lockdown_names_match_stage_keys(self):
        names = _lockdown_names()
        self.assertEqual(len(names), len(set(names)))
        self.assertEqual(
            _bootstrap_static_keys() | _resman_static_keys(), set(names)
        )

    def test_lockdown_names_include_envs(self):
        self.assertIn("envs", _lockdown_names())
        self.assertIn("envs", _resman_static_keys())

    def test_cicd_accounts_stay_out_of_tfvars(self):
        # The 3-security README.md file documents that the "-1" and "-1r"
        # CI/CD accounts stay enabled. Update that section when this changes.
        self.assertNotIn("-cicd", _resman_service_accounts_block())
        self.assertEqual(
            {"bootstrap", "bootstrap-r", "resman", "resman-r"},
            _bootstrap_static_keys(),
        )
        for name in _lockdown_names():
            self.assertNotRegex(name, r"-1r?$")

    def test_validation_checks_envs_account(self):
        self.assertIn(
            "prod-resman-envs-0", _read(_SECURITY_DIR / "validation.sh")
        )


if __name__ == "__main__":
    unittest.main()
