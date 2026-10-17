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

Backend selection runs once, at import time. The tests that exercise it load a
private copy of ``hcl_parser.py`` against stand-in ``hcl2`` modules, so they give
the same result whatever the host has installed.
"""

import copy
import importlib.abc
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import types
from typing import Any, Callable, Optional
import unittest
from unittest import mock

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

from file_helpers import _bootstrap_environment  # noqa: E402

_bootstrap_environment()

import extract_system_data  # noqa: E402
import hcl_parser  # noqa: E402

HCL_PARSER_PATH = os.path.join(SRC_DIR, "compliance_engine", "hcl_parser.py")

#: Module name (and therefore logger name) of the private copies loaded below.
_ISOLATED_NAME = "hcl_parser_backend_probe_under_test"

_MISSING = object()


def _fake_distribution(**attrs: Any) -> types.ModuleType:
    """Builds a stand-in module that will be imported as ``hcl2``."""
    module = types.ModuleType("hcl2")
    module.__file__ = "/stand-in/site-packages/hcl2/__init__.py"
    for key, value in attrs.items():
        setattr(module, key, value)
    return module


def _canary_loads(
    canary_output: Any, document_loads: Optional[Callable[[str], Any]] = None
) -> Callable[[str], Any]:
    """Returns a ``loads`` that answers the canary with ``canary_output``."""

    def loads(text: str) -> Any:
        if text == hcl_parser._CANARY_SOURCE:
            return copy.deepcopy(canary_output)
        return document_loads(text) if document_loads is not None else {}

    return loads


class _FailingImport(importlib.abc.MetaPathFinder, importlib.abc.Loader):
    """Makes ``import hcl2`` raise something other than ImportError."""

    def find_spec(self, name: str, path: Any = None, target: Any = None) -> Any:
        if name == "hcl2":
            return importlib.util.spec_from_loader(name, self)
        return None

    def create_module(self, spec: Any) -> None:
        return None

    def exec_module(self, module: types.ModuleType) -> None:
        raise RuntimeError("broken hcl2 distribution")


def _load_isolated_parser(fake_hcl2: Any = _MISSING, finder: Any = None) -> types.ModuleType:
    """Executes a private copy of hcl_parser.py with ``import hcl2`` controlled.

    Args:
        fake_hcl2: Module to bind as ``hcl2``, or None to make the import fail
            as it does on a host without python-hcl2.
        finder: Optional meta path finder that resolves ``hcl2`` instead.

    Returns:
        The freshly executed module. The shared ``hcl_parser`` is not touched.
    """
    spec = importlib.util.spec_from_file_location(_ISOLATED_NAME, HCL_PARSER_PATH)
    module = importlib.util.module_from_spec(spec)
    saved = sys.modules.pop("hcl2", _MISSING)
    if fake_hcl2 is not _MISSING:
        sys.modules["hcl2"] = fake_hcl2
    if finder is not None:
        sys.meta_path.insert(0, finder)
    try:
        spec.loader.exec_module(module)
    finally:
        if finder is not None:
            sys.meta_path.remove(finder)
        sys.modules.pop("hcl2", None)
        if saved is not _MISSING:
            sys.modules["hcl2"] = saved
    return module


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
            "extract_system_data must parse Terraform through src/compliance_engine/hcl_parser.py. "
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
    """The extractor must import and parse with no ``hcl2`` distribution present."""

    def test_module_imports_when_no_hcl2_distribution_is_installed(self) -> None:
        """``requirements.txt`` documents an in-repo fallback; it must actually engage.

        Runs in a subprocess so backend selection is re-executed with ``hcl2``
        unresolvable from the start. An earlier version of this test installed the
        import blocker only after ``compliance_engine`` had been imported, so the
        real python-hcl2 was already selected and the test passed without ever
        exercising the fallback.

        The subprocess runs in an empty temporary directory, which also checks
        that importing the engine and parsing a document write nothing to the
        working directory.
        """
        program = (
            "import sys\n"
            "class Block:\n"
            "    def find_spec(self, name, path=None, target=None):\n"
            "        if name == 'hcl2' or name.startswith('hcl2.'):\n"
            "            raise ImportError('simulated clean install')\n"
            "        return None\n"
            "sys.meta_path.insert(0, Block())\n"
            f"sys.path.insert(0, {SRC_DIR!r})\n"
            "from compliance_engine import extract_system_data as esd, hcl_parser\n"
            "assert hcl_parser.BACKEND == 'hcl_parser.HclParser', hcl_parser.BACKEND\n"
            "assert esd.hcl2 is hcl_parser, esd.hcl2\n"
            "assert esd.LarkError is hcl_parser.Hcl2Error, esd.LarkError\n"
            "parsed = esd.hcl2.loads('resource \"t\" \"n\" {\\n  name = \"x\"\\n}\\n')\n"
            "assert parsed == {'resource': [{'t': {'n': {'name': 'x'}}}]}, parsed\n"
            "print('OK')\n"
        )
        with tempfile.TemporaryDirectory() as workdir:
            result = subprocess.run(
                [sys.executable, "-c", program],
                capture_output=True,
                text=True,
                timeout=180,
                cwd=workdir,
            )
            leftovers = sorted(os.listdir(workdir))
        self.assertEqual(
            result.returncode,
            0,
            f"extract_system_data is unusable without an hcl2 distribution.\n"
            f"stderr:\n{result.stderr}",
        )
        self.assertIn("OK", result.stdout)
        self.assertIn(
            "python-hcl2 is not importable",
            result.stderr,
            "Falling back to the in-repo parser must be announced, not silent.",
        )
        self.assertEqual(leftovers, [], "importing and parsing wrote files to the working directory")


class TestBackendVerification(unittest.TestCase):
    """The canary must reject every known shape-incompatible distribution."""

    #: Canary output captured from the real distributions.
    BC_PYTHON_HCL2 = {
        "resource": [{"t": {"n": {"name": ["x"], "__start_line__": 1, "__end_line__": 3}}}]
    }
    PYTHON_HCL2_8X = {"resource": [{'"t"': {'"n"': {"name": '"x"', "__is_block__": True}}}]}

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


class TestBackendSelectionWithStandInDistributions(unittest.TestCase):
    """Backend selection fails closed, with a warning, for every unusable ``hcl2``."""

    def test_canonical_backend_is_accepted_without_warnings(self) -> None:
        """A distribution that passes the canary is used, and nothing is logged."""
        fake = _fake_distribution(loads=_canary_loads(hcl_parser._CANARY_EXPECTED))
        with self.assertNoLogs(_ISOLATED_NAME, level="WARNING"):
            module = _load_isolated_parser(fake)
        self.assertEqual(module.BACKEND, "python-hcl2")
        self.assertIs(module._EXTERNAL_HCL2, fake)

    def test_shape_incompatible_distributions_are_refused_by_name(self) -> None:
        """bc-python-hcl2 and python-hcl2 8.x are refused, named, and never used."""
        for label, canary, expected_name in (
            ("bc-python-hcl2", TestBackendVerification.BC_PYTHON_HCL2, "bc-python-hcl2"),
            ("python-hcl2 8.x", TestBackendVerification.PYTHON_HCL2_8X, "8.x"),
        ):
            with self.subTest(distribution=label):
                fake = _fake_distribution(loads=_canary_loads(canary, lambda text: canary))
                with self.assertLogs(_ISOLATED_NAME, level="WARNING") as logs:
                    module = _load_isolated_parser(fake)
                self.assertEqual(module.BACKEND, "hcl_parser.HclParser")
                self.assertIsNone(module._EXTERNAL_HCL2)
                message = "\n".join(logs.output)
                self.assertIn("REFUSED", message)
                self.assertIn(expected_name, message)
                self.assertIn("python-hcl2==7.3.1", message)
                # Parsing goes through the in-repo parser, not the refused backend.
                self.assertEqual(
                    module.loads(hcl_parser._CANARY_SOURCE), hcl_parser._CANARY_EXPECTED
                )

    def test_unusable_distributions_fall_back_with_a_warning(self) -> None:
        """A missing, incomplete, or broken ``hcl2`` must not degrade silently.

        A failed import used to return None without logging anything, and an
        import that raised anything other than ImportError made the whole engine
        unimportable.
        """

        def failing_loads(text: str) -> Any:
            raise RuntimeError("grammar failed to load")

        cases = (
            ("not installed", {"fake_hcl2": None}, "python-hcl2 is not importable"),
            ("import raises", {"finder": _FailingImport()}, "RuntimeError: broken hcl2 distribution"),
            ("no loads()", {"fake_hcl2": _fake_distribution()}, "does not expose loads()"),
            (
                "canary raises",
                {"fake_hcl2": _fake_distribution(loads=failing_loads)},
                "failed the canary parse",
            ),
        )
        for label, kwargs, expected in cases:
            with self.subTest(case=label):
                with self.assertLogs(_ISOLATED_NAME, level="WARNING") as logs:
                    module = _load_isolated_parser(**kwargs)
                self.assertEqual(module.BACKEND, "hcl_parser.HclParser")
                message = "\n".join(logs.output)
                self.assertIn(expected, message)
                self.assertIn("python-hcl2==7.3.1", message)

    def test_parse_error_alias_matches_what_loads_raises(self) -> None:
        """Regression: a backend that exported ``LarkError`` used to rebind the alias.

        loads() wraps every backend failure in Hcl2Error, so after the rebind an
        ``except LarkError`` handler no longer caught parse failures.
        """

        class BackendError(Exception):
            pass

        def document_loads(text: str) -> Any:
            raise BackendError("syntax error")

        fake = _fake_distribution(
            loads=_canary_loads(hcl_parser._CANARY_EXPECTED, document_loads),
            LarkError=BackendError,
        )
        module = _load_isolated_parser(fake)
        self.assertEqual(module.BACKEND, "python-hcl2")
        self.assertIs(module.LarkError, module.Hcl2Error)
        with self.assertRaises(module.LarkError):
            module.loads("resource {\n")


class TestProbeCacheCleanup(unittest.TestCase):
    """The import-time probe may delete only lark cache files it can show are new."""

    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name).resolve()
        self.addCleanup(os.chdir, os.getcwd())
        os.chdir(self.root)

    def test_removes_only_new_regular_files(self) -> None:
        """Pre-existing files, directories, and symlinks survive; probe residue does not."""
        (self.root / ".lark_cache_preexisting.tmp").write_text("operator cache")
        target = self.root / "target.txt"
        target.write_text("keep")
        with hcl_parser._without_probe_cache_residue():
            (self.root / ".lark_cache_probe.tmp").write_text("probe residue")
            (self.root / ".lark_cache_dir").mkdir()
            try:
                os.symlink(target, self.root / ".lark_cache_link")
                made_link = True
            except (OSError, NotImplementedError):
                made_link = False
        self.assertFalse((self.root / ".lark_cache_probe.tmp").exists())
        self.assertTrue((self.root / ".lark_cache_preexisting.tmp").is_file())
        self.assertTrue((self.root / ".lark_cache_dir").is_dir())
        if made_link:
            self.assertTrue((self.root / ".lark_cache_link").is_symlink())
        self.assertEqual(target.read_text(), "keep")

    def test_unavailable_working_directory_does_not_break_import(self) -> None:
        """Regression: ``Path.cwd()`` ran outside the try block.

        A deleted working directory therefore raised FileNotFoundError while
        hcl_parser was being imported, which made the whole engine unimportable.
        """
        stub_path = mock.Mock()
        stub_path.cwd.side_effect = FileNotFoundError("working directory was deleted")
        ran = []
        with mock.patch.object(hcl_parser, "Path", stub_path):
            with hcl_parser._without_probe_cache_residue():
                ran.append(True)
        self.assertEqual(ran, [True])

    def test_nothing_is_deleted_without_a_baseline_listing(self) -> None:
        """Regression: a failed first listing made every matching file look new.

        The cleanup then deleted cache files that existed before the probe.
        """
        existing = self.root / ".lark_cache_preexisting.tmp"
        existing.write_text("operator cache")
        real_dir = self.root
        calls = []

        class FlakyDir:
            def glob(self, pattern: str) -> Any:
                calls.append(pattern)
                if len(calls) == 1:
                    raise PermissionError("listing denied")
                return real_dir.glob(pattern)

        stub_path = mock.Mock()
        stub_path.cwd.return_value = FlakyDir()
        with mock.patch.object(hcl_parser, "Path", stub_path):
            with hcl_parser._without_probe_cache_residue():
                pass
        self.assertTrue(existing.is_file())


class TestDependencyManifest(unittest.TestCase):
    """The manifest must require the backend that keeps the boundary complete."""

    def test_python_hcl2_is_a_required_pinned_dependency(self) -> None:
        """Leaving it optional costs a large share of a real estate's coverage.

        Measured on this repository on 2026-10-13: 768 of 820 ``.tf`` files parse
        with python-hcl2 7.3.1 versus 615 with the in-repo parser.
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
