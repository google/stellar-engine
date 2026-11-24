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
_DRY_RUN_SPEC = "var.vpc_sc.perimeter_default.dry_run_spec"
_OVERRIDES = (
    "access_levels",
    "egress_policies",
    "ingress_policies",
    "resources",
    "restricted_services",
)
_SPEC = "local.vpc_sc_perimeters.spec"
_STATUS = "local.vpc_sc_perimeters.status"
_USE_DRY_RUN_SPEC = "local._vpc_sc_use_dry_run_spec"


def _squash(text):
    """Drops comments and collapses whitespace in Terraform source text."""
    return " ".join(re.sub(r"#[^\n]*", "", text).split())


def _vpc_sc_tf():
    return (_STAGE_DIR / "vpc-sc.tf").read_text(encoding="utf-8")


def _local(name):
    """Returns the expression of a two-space indented local as source text."""
    block = re.search(
        rf"\n  {name} = ([\s\S]*?)\n  (?=[\w#])", _vpc_sc_tf() + "\n  #"
    )
    assert block is not None, f"local {name} not found in vpc-sc.tf"
    return _squash(block.group(1))


def _default_perimeter():
    """Returns the arguments of the default perimeter as source text."""
    block = re.search(
        r"\n  perimeters = \{\n    default = \{\n([\s\S]*?)\n    \}\n  \}\n",
        _vpc_sc_tf(),
    )
    assert block is not None, "default perimeter not found in vpc-sc.tf"
    # drop comments, then split the body on the argument names
    body = re.sub(r"#[^\n]*", "", block.group(1))
    parts = re.split(r"^      (\w+)\s*=", body, flags=re.MULTILINE)
    return {
        name: _squash(expression)
        for name, expression in zip(parts[1::2], parts[2::2])
    }


def _variable():
    """Returns the vpc_sc variable block as source text."""
    variables_tf = (_STAGE_DIR / "variables.tf").read_text(encoding="utf-8")
    block = re.search(r'variable "vpc_sc" \{[\s\S]*?\n\}', variables_tf)
    assert block is not None, "variable vpc_sc not found in variables.tf"
    return block.group(0)


def _evaluate(expression, terms):
    """Evaluates a boolean or conditional expression of known terms."""
    expression = expression.strip()
    if expression.startswith("(") and expression.endswith(")"):
        expression = expression[1:-1].strip()
    condition, question, branches = expression.partition(" ? ")
    # the conditions are a disjunction of optionally negated terms, any
    # other shape fails on the lookup so the test never guesses
    result = False
    for term in condition.split("||"):
        term = term.strip()
        negated = term.startswith("!") and not term.startswith("!=")
        value = terms[term.removeprefix("!").strip() if negated else term]
        result = result or (not value if negated else value)
    if not question:
        return result
    when_true, _, when_false = branches.partition(" : ")
    return (when_true if result else when_false).strip()


class TestSecurityVpcScDryRun(unittest.TestCase):
    def setUp(self):
        self.perimeter = _default_perimeter()

    def _evaluate_all(self, dry_run, dry_run_spec):
        """Evaluates the perimeter arguments for one input combination."""
        use_dry_run_spec = _evaluate(
            _local("_vpc_sc_use_dry_run_spec"),
            {
                f"try({_DRY_RUN}, false)": dry_run,
                "local._vpc_sc_dry_run_spec != null": dry_run_spec,
            },
        )
        terms = {_DRY_RUN: dry_run, _USE_DRY_RUN_SPEC: use_dry_run_spec}
        return {
            name: _evaluate(self.perimeter[name], terms)
            for name in ("spec", "status", "use_explicit_dry_run_spec")
        }

    def test_perimeter_sets_only_the_dry_run_arguments(self):
        self.assertEqual(
            sorted(self.perimeter),
            ["spec", "status", "use_explicit_dry_run_spec"],
        )

    def test_enforced_mode_sets_only_the_status(self):
        self.assertEqual(
            self._evaluate_all(False, False),
            {
                "spec": "null",
                "status": _STATUS,
                "use_explicit_dry_run_spec": False,
            },
        )

    def test_dry_run_enforces_nothing(self):
        self.assertEqual(
            self._evaluate_all(True, False),
            {
                "spec": _SPEC,
                "status": "null",
                "use_explicit_dry_run_spec": True,
            },
        )

    def test_dry_run_spec_keeps_the_status_and_adds_the_spec(self):
        self.assertEqual(
            self._evaluate_all(False, True),
            {
                "spec": _SPEC,
                "status": _STATUS,
                "use_explicit_dry_run_spec": True,
            },
        )

    def test_status_depends_on_dry_run_only(self):
        for dry_run, dry_run_spec in itertools.product((False, True), repeat=2):
            with self.subTest(dry_run=dry_run, dry_run_spec=dry_run_spec):
                result = self._evaluate_all(dry_run, dry_run_spec)
                self.assertEqual(
                    result["status"], "null" if dry_run else _STATUS
                )

    def test_dry_run_spec_reads_the_variable(self):
        self.assertEqual(
            _local("_vpc_sc_dry_run_spec"), f"try({_DRY_RUN_SPEC}, null)"
        )

    def test_only_the_spec_receives_the_non_null_overrides(self):
        inputs = _local("_vpc_sc_perimeter_inputs")
        self.assertIn(
            "for k, v in { spec = ( local._vpc_sc_dry_run_spec == null ? {} "
            ": { for a, l in local._vpc_sc_dry_run_spec : a => l if l != null "
            "} ) status = {} } : k => merge({",
            inputs,
        )
        self.assertTrue(inputs.endswith("}, v) } )"), inputs)

    def test_overrides_apply_before_the_normalization(self):
        perimeters = _local("vpc_sc_perimeters")
        self.assertIn(
            "for k, v in local._vpc_sc_perimeter_inputs : k => {", perimeters
        )
        # the normalization reads the combined inputs only, so the enforced
        # status and the dry-run spec never bypass it
        self.assertNotIn("var.vpc_sc.perimeter_default", perimeters)
        self.assertNotIn("dry_run_spec", perimeters)
        for name in _OVERRIDES:
            with self.subTest(attribute=name):
                self.assertIn(f"v.{name}", perimeters)

    def test_variable_declares_the_optional_overrides(self):
        block = _variable()
        self.assertRegex(block, r"\n\s*dry_run\s*=\s*optional\(bool, false\)\n")
        dry_run_spec = re.search(
            r"\n      dry_run_spec = optional\(object\(\{\n([\s\S]*?)\n"
            r"      \}\)\)\n",
            block,
        )
        self.assertIsNotNone(dry_run_spec)
        self.assertEqual(
            [
                " ".join(line.split())
                for line in dry_run_spec.group(1).split("\n")
            ],
            [f"{name} = optional(list(string))" for name in _OVERRIDES],
        )

    def test_variable_rejects_ambiguous_inputs(self):
        conditions = [
            _squash(condition)
            for condition in re.findall(
                r"validation \{\n    condition = ([\s\S]*?)\n    error_message",
                _variable(),
            )
        ]
        self.assertEqual(
            conditions[:2],
            [
                # dry_run drops the status, so it never combines with a trial
                f"( try({_DRY_RUN_SPEC}, null) == null || "
                f"try({_DRY_RUN}, false) != true )",
                # an empty override would only duplicate the status
                f"( try({_DRY_RUN_SPEC}, null) == null || anytrue([ "
                f"for v in try(values({_DRY_RUN_SPEC}), []) : v != null ]) )",
            ],
        )
        self.assertEqual(len(conditions), 5)

    def test_stage_has_no_keep_enforced_flag(self):
        for name in ("README.md", "variables.tf", "vpc-sc.tf"):
            with self.subTest(file=name):
                self.assertNotIn(
                    "dry_run_keep_enforced",
                    (_STAGE_DIR / name).read_text(encoding="utf-8"),
                )


if __name__ == "__main__":
    unittest.main()
