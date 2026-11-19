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

"""Checks the security stage dry-run handling of the default perimeter."""

import itertools
import pathlib
import re
import unittest

_STAGE_DIR = (
    pathlib.Path(__file__).resolve().parents[1] / "fast/stages-aw/3-security"
)
_DRY_RUN = "var.vpc_sc.perimeter_default.dry_run"
_KEEP_ENFORCED = "var.vpc_sc.perimeter_default.dry_run_keep_enforced"
_PERIMETER = "local.vpc_sc_perimeter"


def _default_perimeter():
    """Returns the arguments of the default perimeter as source text."""
    vpc_sc_tf = (_STAGE_DIR / "vpc-sc.tf").read_text(encoding="utf-8")
    block = re.search(
        r"\n  perimeters = \{\n    default = \{\n([\s\S]*?)\n    \}\n  \}\n",
        vpc_sc_tf,
    )
    assert block is not None, "default perimeter not found in vpc-sc.tf"
    # drop comments, then split the body on the argument names
    body = re.sub(r"#[^\n]*", "", block.group(1))
    parts = re.split(r"^      (\w+)\s*=", body, flags=re.MULTILINE)
    return {
        name: " ".join(expression.split())
        for name, expression in zip(parts[1::2], parts[2::2])
    }


def _evaluate(expression, dry_run, keep_enforced):
    """Evaluates a boolean or conditional expression of the two flags."""
    expression = expression.strip()
    if expression.startswith("(") and expression.endswith(")"):
        expression = expression[1:-1].strip()
    condition, question, branches = expression.partition(" ? ")
    flags = {_DRY_RUN: dry_run, _KEEP_ENFORCED: keep_enforced}
    # the conditions are a disjunction of optionally negated flags, any
    # other shape fails on the lookup so the test never guesses
    result = False
    for term in condition.split("||"):
        term = term.strip()
        negated = term.startswith("!")
        value = flags[term.removeprefix("!").strip()]
        result = result or (not value if negated else value)
    if not question:
        return result
    when_true, _, when_false = branches.partition(" : ")
    return (when_true if result else when_false).strip()


class TestSecurityVpcScDryRun(unittest.TestCase):
    def setUp(self):
        self.perimeter = _default_perimeter()

    def _evaluate_all(self, dry_run, keep_enforced):
        return {
            name: _evaluate(self.perimeter[name], dry_run, keep_enforced)
            for name in ("spec", "status", "use_explicit_dry_run_spec")
        }

    def test_perimeter_sets_only_the_dry_run_arguments(self):
        self.assertEqual(
            sorted(self.perimeter),
            ["spec", "status", "use_explicit_dry_run_spec"],
        )

    def test_enforced_mode_ignores_the_opt_in(self):
        for keep_enforced in (False, True):
            with self.subTest(keep_enforced=keep_enforced):
                self.assertEqual(
                    self._evaluate_all(False, keep_enforced),
                    {
                        "spec": "null",
                        "status": _PERIMETER,
                        "use_explicit_dry_run_spec": False,
                    },
                )

    def test_dry_run_enforces_nothing_by_default(self):
        self.assertEqual(
            self._evaluate_all(True, False),
            {
                "spec": _PERIMETER,
                "status": "null",
                "use_explicit_dry_run_spec": True,
            },
        )

    def test_dry_run_keeps_the_enforced_perimeter_on_opt_in(self):
        self.assertEqual(
            self._evaluate_all(True, True),
            {
                "spec": _PERIMETER,
                "status": _PERIMETER,
                "use_explicit_dry_run_spec": True,
            },
        )

    def test_some_configuration_always_applies(self):
        for dry_run, keep_enforced in itertools.product(
            (False, True), repeat=2
        ):
            with self.subTest(dry_run=dry_run, keep_enforced=keep_enforced):
                result = self._evaluate_all(dry_run, keep_enforced)
                self.assertIn(_PERIMETER, (result["spec"], result["status"]))

    def test_opt_in_defaults_to_false(self):
        variables_tf = (_STAGE_DIR / "variables.tf").read_text(encoding="utf-8")
        block = re.search(
            r'variable "vpc_sc" \{[\s\S]*?\n\}', variables_tf
        ).group(0)
        self.assertRegex(block, r"\n\s*dry_run\s*=\s*optional\(bool, false\)\n")
        self.assertRegex(
            block,
            r"\n\s*dry_run_keep_enforced\s*=\s*optional\(bool, false\)\n",
        )

    def test_description_states_the_opt_in_enforces(self):
        variables_tf = (_STAGE_DIR / "variables.tf").read_text(encoding="utf-8")
        block = re.search(
            r'variable "vpc_sc" \{[\s\S]*?\n\}', variables_tf
        ).group(0)
        description = re.search(r'description\s*=\s*"([^"]*)"', block).group(1)
        self.assertIn("dry_run_keep_enforced", description)
        self.assertIn("enforces the perimeter", description)


if __name__ == "__main__":
    unittest.main()
