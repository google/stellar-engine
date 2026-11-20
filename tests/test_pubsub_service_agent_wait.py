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

"""Checks that the pub-sub-project blueprint waits for its service agent."""

import pathlib
import re
import unittest

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
_BLUEPRINT_DIR = _REPO_ROOT / "blueprints/il5/pub-sub-project"
_FEDRAMP_HIGH_DIR = _REPO_ROOT / "blueprints/fedramp-high/pub-sub-project"


def _top_block(text, header):
    """Returns the top-level HCL block that starts with header."""
    match = re.search(re.escape(header) + r"\s*\{[\s\S]*?\n\}", text)
    if match is None:
        raise AssertionError(f"Block not found: {header}")
    return match.group(0)


def _without_comments(block):
    """Returns the block without its full-line comments."""
    return "\n".join(
        line
        for line in block.splitlines()
        if not line.lstrip().startswith(("#", "//"))
    )


class TestPubsubServiceAgentWait(unittest.TestCase):
    def setUp(self):
        self.main_tf = (_BLUEPRINT_DIR / "main.tf").read_text(encoding="utf-8")
        self.provider_tf = (_BLUEPRINT_DIR / "provider.tf").read_text(
            encoding="utf-8"
        )

    def _key_grant(self):
        return _without_comments(
            _top_block(
                self.main_tf,
                'resource "google_kms_crypto_key_iam_member" "kms_access"',
            )
        )

    def test_service_agent_is_created_after_the_api_is_enabled(self):
        # Enabling pubsub.googleapis.com does not create the service agent on
        # a new project, so the blueprint has to create it.
        agent = _top_block(
            self.main_tf,
            'resource "google_project_service_identity" "pubsub_sa"',
        )
        self.assertRegex(agent, r"\n\s*provider\s*=\s*google-beta\n")
        self.assertRegex(agent, r"\n\s*project\s*=\s*var\.main_project_id\n")
        self.assertRegex(
            agent, r'\n\s*service\s*=\s*"pubsub\.googleapis\.com"\n'
        )
        self.assertRegex(
            agent,
            r"depends_on\s*=\s*\[google_project_service\.pubsub_api\]",
        )

    def test_wait_follows_the_service_agent(self):
        wait = _top_block(
            self.main_tf, 'resource "time_sleep" "pubsub_sa_propagation"'
        )
        self.assertRegex(wait, r'create_duration\s*=\s*"\d+[sm]"')
        self.assertRegex(
            wait,
            r"depends_on\s*=\s*"
            r"\[google_project_service_identity\.pubsub_sa\]",
        )

    def test_key_grant_waits_for_the_service_agent_to_propagate(self):
        # A grant issued right after the service agent is created fails,
        # because IAM does not recognize the new agent yet.
        self.assertRegex(
            self._key_grant(),
            r"depends_on\s*=\s*\[[^\]]*\btime_sleep\.pubsub_sa_propagation\b"
            r"[^\]]*\]",
        )

    def test_key_grant_key_does_not_come_from_the_service_agent(self):
        # The service agent member is unknown until apply, so a for_each key
        # built from it breaks the first plan. A different key would also
        # move the grant to a new state address on existing deployments.
        grant = self._key_grant()
        self.assertIn(
            '"serviceAccount:service-${data.google_project.current.number}'
            '@gcp-sa-pubsub.iam.gserviceaccount.com"',
            grant,
        )
        self.assertRegex(grant, r"\n\s*member\s*=\s*each\.key\n")
        self.assertNotIn("google_project_service_identity", grant)

    def test_topic_still_waits_for_the_key_grant(self):
        # The topic depends on the grant, and the grant on the wait, so the
        # topic is created only after the service agent can use the key.
        topic = _without_comments(_top_block(self.main_tf, 'module "pubsub"'))
        self.assertRegex(
            topic,
            r"depends_on\s*=\s*\[[^\]]*"
            r"\bgoogle_kms_crypto_key_iam_member\.kms_access\b[^\]]*\]",
        )

    def test_time_provider_is_declared(self):
        self.assertRegex(
            self.provider_tf,
            r'time = \{\s*source\s*=\s*"hashicorp/time"\s*'
            r'version\s*=\s*">= 0\.9\.1"',
        )

    def test_beta_provider_is_declared_and_configured(self):
        # The service identity uses google-beta, so it needs the same version
        # bounds and defaults as google.
        self.assertRegex(
            self.provider_tf,
            r'google-beta = \{\s*source\s*=\s*"hashicorp/google-beta"\s*'
            r'version\s*=\s*">= 8\.6\.0, < 9\.0\.0"',
        )
        google = _top_block(self.provider_tf, 'provider "google"')
        beta = _top_block(self.provider_tf, 'provider "google-beta"')
        for block in (google, beta):
            self.assertRegex(block, r"project\s*=\s*var\.main_project_id")
            self.assertRegex(block, r"region\s*=\s*var\.gcp_region")

    def test_fedramp_high_blueprint_shares_the_fix(self):
        # The FedRAMP High blueprint is a symlink to the IL5 blueprint, so
        # both regimes get the service agent and the wait.
        self.assertTrue(_FEDRAMP_HIGH_DIR.is_symlink())
        self.assertEqual(_FEDRAMP_HIGH_DIR.resolve(), _BLUEPRINT_DIR.resolve())


if __name__ == "__main__":
    unittest.main()
