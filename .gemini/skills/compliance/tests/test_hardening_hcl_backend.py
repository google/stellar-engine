#!/usr/bin/env python3
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

"""Regression tests for the Terraform HCL2 parsing backend contract.

These lock in a defect in which ``extract_system_data`` performed a bare
``import hcl2``. That import was written when ``scripts/`` vendored a package
literally named ``hcl2``, so it resolved to the in-repo parser. Once the shadow
package was removed the same statement silently bound whatever distribution
happened to publish under that name, producing two distinct failures:

1. On a host with checkov installed it bound ``bc-python-hcl2``, which wraps every
   scalar attribute in a one-element list and injects synthetic
   ``__start_line__``/``__end_line__`` keys -- corrupting the extracted inventory
   in an environment-dependent way, and bypassing every resource budget in
   ``hcl_parser``.
2. On a host with neither distribution installed the import raised ``ImportError``
   outright, making the module unimportable, even though ``requirements.txt``
   documents an in-repo fallback parser.
"""

import os
import subprocess
import sys
import unittest

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.abspath(os.path.join(TESTS_DIR, ".."))
SRC_DIR = os.path.join(SKILL_DIR, "src")
SCRIPTS_DIR = os.path.join(SKILL_DIR, "scripts")
for _p in (SRC_DIR, SCRIPTS_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import compliance_engine
for _m in ("file_helpers", "extract_system_data", "hcl_parser"):
    if hasattr(compliance_engine, _m):
        sys.modules[_m] = getattr(compliance_engine, _m)

import file_helpers  # noqa: E402,F401  (bootstraps the dependency search path)

import extract_system_data  # noqa: E402
import hcl_parser  # noqa: E402


class TestExtractorUsesHardenedFacade(unittest.TestCase):
    """The extractor must parse Terraform through the verified facade only."""

    def test_extractor_binds_the_hardened_facade_not_an_arbitrary_distribution(self) -> None:
        """A bare ``import hcl2`` binds whatever is first on ``sys.path``.

        Binding the facade is what guarantees the canary-verified backend selection,
        the byte/depth/token budgets, and a single canonical output shape across
        environments.
        """
        self.assertIs(
            extract_system_data.hcl2,
            hcl_parser,
            "extract_system_data must parse Terraform through scripts/hcl_parser.py. "
            f"It is currently bound to {getattr(extract_system_data.hcl2, '__file__', '?')}",
        )

    def test_parse_error_type_is_specific_rather_than_bare_exception(self) -> None:
        """``LarkError`` degrading to bare ``Exception`` widens every except clause.

        Genuine ``python-hcl2`` does not export ``LarkError``, so the previous
        ``getattr(hcl2, "LarkError", Exception)`` fallback always resolved to
        ``Exception``. The parse-failure handlers in ``extract_system_data`` catch
        ``(LarkError, KeyError, ValueError, TypeError)``, so that silently turned two
        targeted handlers into catch-alls that would swallow unrelated defects and
        misreport them as Terraform syntax errors.
        """
        self.assertIs(extract_system_data.LarkError, hcl_parser.LarkError)
        self.assertIsNot(
            extract_system_data.LarkError,
            Exception,
            "LarkError degraded to bare Exception; parse-failure handlers became catch-alls.",
        )
        self.assertTrue(issubclass(extract_system_data.LarkError, Exception))

    def test_extractor_output_shape_is_canonical(self) -> None:
        """Scalars must not be list-wrapped, and synthetic keys must not appear.

        ``bucket["name"]`` yielding ``["x"]`` rather than ``"x"`` writes the literal
        text ``['x']`` into the SSP.
        """
        parsed = extract_system_data.hcl2.loads('resource "t" "n" {\n  name = "x"\n}\n')
        self.assertEqual(parsed, {"resource": [{"t": {"n": {"name": "x"}}}]})

        body = parsed["resource"][0]["t"]["n"]
        self.assertNotIn("__start_line__", body)
        self.assertNotIn("__end_line__", body)
        self.assertIsInstance(body["name"], str)


class TestCleanInstallImportContract(unittest.TestCase):
    """The extractor must import with no ``hcl2`` distribution present at all."""

    def test_module_imports_when_no_hcl2_distribution_is_installed(self) -> None:
        """``requirements.txt`` documents an in-repo fallback; it must actually engage.

        Run in a subprocess so the import block is re-executed against a ``sys.path``
        on which ``hcl2`` is unresolvable.
        """
        program = (
            "import sys\n"
            f"for _p in ({SRC_DIR!r}, {SCRIPTS_DIR!r}):\n"
            "    if _p not in sys.path: sys.path.insert(0, _p)\n"
            "import compliance_engine\n"
            "for _m in ('file_helpers', 'extract_system_data', 'hcl_parser'):\n"
            "    sys.modules[_m] = getattr(compliance_engine, _m)\n"
            "class Block:\n"
            "    def find_spec(self, name, path=None, target=None):\n"
            "        if name == 'hcl2' or name.startswith('hcl2.'):\n"
            "            raise ImportError('simulated clean install')\n"
            "        return None\n"
            "import file_helpers\n"
            "for mod in [m for m in sys.modules if m == 'hcl2' or m.startswith('hcl2.')]:\n"
            "    del sys.modules[mod]\n"
            "sys.meta_path.insert(0, Block())\n"
            "import extract_system_data as esd\n"
            "assert esd.hcl2.__name__ in ('hcl_parser', 'compliance_engine.hcl_parser'), esd.hcl2.__name__\n"
            "assert esd.LarkError is not Exception\n"
            "print('OK')\n"
        )
        result = subprocess.run(
            [sys.executable, "-c", program],
            capture_output=True,
            text=True,
            timeout=180,
            cwd=SKILL_DIR,
        )
        self.assertEqual(
            result.returncode,
            0,
            f"extract_system_data is unimportable without an hcl2 distribution.\n"
            f"stderr:\n{result.stderr}",
        )
        self.assertIn("OK", result.stdout)


class TestBackendVerification(unittest.TestCase):
    """The canary must reject every known shape-incompatible distribution."""

    #: Canary output captured from the real distributions.
    BC_PYTHON_HCL2 = {
        "resource": [{"t": {"n": {"name": ["x"], "__start_line__": 1, "__end_line__": 3}}}]
    }
    PYTHON_HCL2_8X = {"resource": [{'"t"': {'"n"': {"name": '"x"', "__is_block__": True}}}]}

    def test_known_incompatible_shapes_are_not_the_accepted_shape(self) -> None:
        """Both real incompatible outputs must differ from the canary expectation."""
        self.assertNotEqual(self.BC_PYTHON_HCL2, hcl_parser._CANARY_EXPECTED)
        self.assertNotEqual(self.PYTHON_HCL2_8X, hcl_parser._CANARY_EXPECTED)

    def test_rejected_backends_are_identified_by_name(self) -> None:
        """An opaque rejection leaves the operator with no route to full coverage."""
        self.assertIn(
            "bc-python-hcl2",
            hcl_parser._classify_incompatible_backend(self.BC_PYTHON_HCL2),
        )
        self.assertIn(
            "8.x",
            hcl_parser._classify_incompatible_backend(self.PYTHON_HCL2_8X),
        )

    def test_classifier_never_raises_on_malformed_canary_output(self) -> None:
        """The classifier runs on the error path; raising there would mask the cause."""
        for canary in ({}, {"resource": []}, {"resource": [{}]}, "garbage", None, 7):
            with self.subTest(canary=canary):
                self.assertIsInstance(
                    hcl_parser._classify_incompatible_backend(canary), str
                )

    def test_selected_backend_produces_the_canonical_shape(self) -> None:
        """Whichever backend was selected, the observable output shape is identical."""
        self.assertEqual(
            hcl_parser.loads(hcl_parser._CANARY_SOURCE), hcl_parser._CANARY_EXPECTED
        )
        self.assertIn(hcl_parser.BACKEND, ("python-hcl2", "hcl_parser.HclParser"))

    def test_probe_context_manager_propagates_exceptions(self) -> None:
        """A ``return`` inside its ``finally`` would discard a genuine backend failure."""
        with self.assertRaises(RuntimeError):
            with hcl_parser._without_probe_cache_residue():
                raise RuntimeError("must propagate")


class TestDependencyManifest(unittest.TestCase):
    """The manifest must require the backend that keeps the boundary complete."""

    def test_python_hcl2_is_a_required_pinned_dependency(self) -> None:
        """Leaving it optional costs roughly two thirds of a real estate's coverage.

        Measured on a 269-file DoD IL5 reference estate: 247/269 files parse with
        python-hcl2 7.3.1 versus 90/269 with the in-repo fallback parser.
        """
        manifest = os.path.join(SKILL_DIR, "requirements.txt")
        with open(manifest, "r", encoding="utf-8") as handle:
            requirements = [
                line.strip()
                for line in handle
                if line.strip() and not line.lstrip().startswith("#")
            ]

        self.assertIn(
            "python-hcl2==7.3.1",
            requirements,
            "python-hcl2 must be a required, exactly-pinned dependency. The major "
            "version is load-bearing: 8.x emits a different output shape and is "
            "rejected by the backend canary.",
        )


if __name__ == "__main__":
    unittest.main()
