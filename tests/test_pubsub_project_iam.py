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

"""Checks that the pub-sub-project blueprint grants no project-level role."""

import pathlib
import re
import unittest

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
_BLUEPRINT_DIR = _REPO_ROOT / "blueprints/il5/pub-sub-project"
_FEDRAMP_HIGH_LINK = _REPO_ROOT / "blueprints/fedramp-high/pub-sub-project"


def _block(text, header):
    """Returns the top-level block that starts with header."""
    match = re.search(re.escape(header) + r"\s*\{[\s\S]*?\n\}", text)
    if match is None:
        raise AssertionError(f"Block not found: {header}")
    return match.group(0)


def _argument(block, name):
    """Returns the multi-line map argument of a top-level block."""
    match = re.search(rf"\n  {name} = \{{\n[\s\S]*?\n  \}}", block)
    if match is None:
        raise AssertionError(f"Argument not found: {name}")
    return match.group(0)


class TestPubsubProjectIam(unittest.TestCase):
    def setUp(self):
        self.main_tf = (_BLUEPRINT_DIR / "main.tf").read_text(encoding="utf-8")
        self.module = _block(self.main_tf, 'module "pubsub"')

    def test_no_role_is_granted_on_the_project(self):
        self.assertNotRegex(
            self.main_tf, r"google_project_iam_(member|binding|policy)"
        )

    def test_publisher_is_bound_on_the_topic(self):
        topic_iam = _argument(self.module, "iam_bindings_additive")
        self.assertRegex(topic_iam, r"\n    publisher = \{\n")
        self.assertRegex(
            topic_iam,
            r"\n\s*member = google_service_account\.publisher\.member\n",
        )
        self.assertRegex(
            topic_iam, r'\n\s*role\s*= "roles/pubsub\.publisher"\n'
        )

    def test_subscriber_is_bound_on_each_subscription(self):
        subscriptions = _argument(self.module, "subscriptions")
        self.assertIn(
            "for k, v in var.subscriptions : k => merge(v, {", subscriptions
        )
        # The module merges the additive bindings of every subscription
        # into one map, so the key must name the subscription to stay
        # unique.
        self.assertRegex(subscriptions, r'\n\s*"\$\{k\}-subscriber" = \{\n')
        self.assertRegex(
            subscriptions,
            r"\n\s*member = google_service_account\.subscriber\.member\n",
        )
        self.assertRegex(
            subscriptions, r'\n\s*role\s*= "roles/pubsub\.subscriber"\n'
        )

    def test_subscriber_is_not_bound_on_the_topic(self):
        # On a topic the subscriber role only allows attaching new
        # subscriptions, which the subscriber service account never does.
        topic_iam = _argument(self.module, "iam_bindings_additive")
        self.assertNotIn("subscriber", topic_iam)
        self.assertEqual(self.main_tf.count('"roles/pubsub.subscriber"'), 1)
        self.assertEqual(self.main_tf.count('"roles/pubsub.publisher"'), 1)

    def test_grants_are_never_authoritative(self):
        # Authoritative arguments would remove grants that other
        # configurations manage on the same topic or subscription.
        self.assertNotRegex(
            self.module, r"\n\s*iam(_bindings|_by_principals)?\s*="
        )
        self.assertNotRegex(
            self.main_tf, r"google_pubsub_\w+_iam_(binding|policy)"
        )

    def test_subscriptions_default_to_none(self):
        # Callers that set no subscriptions must keep planning cleanly.
        variables_tf = (_BLUEPRINT_DIR / "variables.tf").read_text(
            encoding="utf-8"
        )
        variable = _block(variables_tf, 'variable "subscriptions"')
        self.assertRegex(variable, r"\n  default\s*= \{\}\n")
        self.assertRegex(variable, r"\n  nullable\s*= false\n")

    def test_fedramp_high_blueprint_follows_the_il5_blueprint(self):
        self.assertTrue(_FEDRAMP_HIGH_LINK.is_symlink())
        self.assertEqual(_FEDRAMP_HIGH_LINK.resolve(), _BLUEPRINT_DIR.resolve())


if __name__ == "__main__":
    unittest.main()
