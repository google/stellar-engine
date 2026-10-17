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

"""Regression tests for the shared security foundation of the compliance engine.

Covers the primitives owned by ``file_helpers``, the hardened deserialization facades
``safe_xml`` and ``hcl_parser``, and the structured audit trail in ``audit_log``.

Each test targets a specific, previously exploitable weakness rather than asserting on
implementation details, so the suite stays meaningful under refactoring.
"""

import io
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
import unittest
from unittest.mock import patch

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.abspath(os.path.join(TESTS_DIR, "..", "scripts"))
SRC_DIR = os.path.abspath(os.path.join(TESTS_DIR, "..", "src"))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from compliance_engine import audit_log  # noqa: E402
from compliance_engine import file_helpers as fh  # noqa: E402
from compliance_engine import hcl_parser  # noqa: E402
from compliance_engine import safe_xml  # noqa: E402


class TestNoShadowedDistributions(unittest.TestCase):
    """Verifies the engine no longer vendors packages under real PyPI names."""

    def test_no_vendored_package_shadows_a_real_distribution(self) -> None:
        """An in-repo package named after a real distribution silently hijacks it.

        ``scripts/`` and ``src/`` are placed on ``sys.path``, so a directory named
        ``defusedxml`` or ``hcl2`` there takes precedence over the genuine installed
        distribution. That made the documented ``pip install defusedxml python-hcl2``
        a no-op while the code appeared to be using audited libraries.
        """
        for search_dir in (SCRIPTS_DIR, SRC_DIR):
            for hijacked_name in ("defusedxml", "hcl2", "yaml", "openpyxl", "lark"):
                with self.subTest(search_dir=search_dir, name=hijacked_name):
                    self.assertFalse(
                        os.path.isdir(os.path.join(search_dir, hijacked_name)),
                        f"{search_dir}/{hijacked_name}/ would shadow the real '{hijacked_name}' distribution",
                    )
                    self.assertFalse(
                        os.path.isfile(os.path.join(search_dir, f"{hijacked_name}.py")),
                        f"{search_dir}/{hijacked_name}.py would shadow the real '{hijacked_name}' distribution",
                    )

    def test_parser_facades_report_a_known_backend(self) -> None:
        """Backend selection must be explicit and enumerable, never implicit."""
        self.assertIn(safe_xml.BACKEND, ("defusedxml.ElementTree", "safe_xml.HardenedXMLParser"))
        self.assertIn(hcl_parser.BACKEND, ("python-hcl2", "hcl_parser.HclParser"))


class TestXmlHardening(unittest.TestCase):
    """XXE, entity expansion, and resource-exhaustion defenses (CWE-611, CWE-776, CWE-400)."""

    def test_external_entity_reference_is_rejected(self) -> None:
        """CWE-611: an external SYSTEM entity must never be resolved."""
        with self.assertRaises(safe_xml.DefusedXmlException):
            safe_xml.fromstring(
                '<!DOCTYPE r [<!ENTITY x SYSTEM "file:///etc/passwd">]><r>&x;</r>'
            )

    def test_entity_expansion_is_rejected(self) -> None:
        """CWE-776: nested entity declarations must be refused before expansion."""
        with self.assertRaises(safe_xml.DefusedXmlException):
            safe_xml.fromstring('<!DOCTYPE l [<!ENTITY a "aa"><!ENTITY b "&a;&a;">]><l>&b;</l>')

    def test_depth_bomb_is_rejected(self) -> None:
        """CWE-400: nesting beyond the configured depth budget must abort parsing."""
        depth = safe_xml.MAX_XML_DEPTH + 5
        with self.assertRaises(safe_xml.XmlLimitExceeded):
            safe_xml.fromstring("<r>" * depth + "</r>" * depth)

    def test_oversize_document_is_rejected(self) -> None:
        """CWE-400: a document above the byte budget is refused, not truncated."""
        oversize = b"<r>" + b"x" * (safe_xml.MAX_XML_BYTES + 1) + b"</r>"
        with self.assertRaises(safe_xml.XmlLimitExceeded):
            safe_xml.fromstring(oversize)

    def test_iterparse_traversal_is_not_recursive(self) -> None:
        """CWE-674: deep documents must not exhaust the interpreter stack.

        Depth is kept inside the parser's own budget, and the interpreter recursion
        limit is lowered instead. A recursive generator would need one frame per level
        and would raise RecursionError; an explicit-stack traversal will not.
        """
        depth = min(safe_xml.MAX_XML_DEPTH - 5, 200)
        deep = ("<r>" * depth + "</r>" * depth).encode("utf-8")
        original_limit = sys.getrecursionlimit()
        sys.setrecursionlimit(max(60, depth // 4))
        try:
            self.assertEqual(sum(1 for _ in safe_xml.iterparse(io.BytesIO(deep))), depth)
        finally:
            sys.setrecursionlimit(original_limit)

    def test_benign_namespaced_openxml_still_parses(self) -> None:
        """Hardening must not break legitimate OpenXML content."""
        root = safe_xml.fromstring('<a xmlns:w="urn:x"><b w:k="1">hi</b></a>')
        self.assertEqual(root.tag, "a")
        self.assertEqual(root[0].attrib, {"{urn:x}k": "1"})
        self.assertEqual(root[0].text, "hi")


class TestHclHardening(unittest.TestCase):
    """Terraform HCL parsing defenses against DoS and non-termination."""

    def test_stray_closing_brace_terminates(self) -> None:
        """The previous parser looped forever on a stray '}' at top level.

        ``_parse_statement`` returned without consuming the token while ``parse``
        looped until EOF, so a single malformed ``.tf`` file hung the extractor
        indefinitely. A stray top-level closing brace is a syntax error and must
        be rejected with Hcl2Error rather than silently returning an empty dict.
        """
        with self.assertRaises(hcl_parser.Hcl2Error):
            hcl_parser.loads("}")

    def test_depth_bomb_is_rejected(self) -> None:
        """CWE-674: deeply nested collections exceeding MAX_HCL_DEPTH must be rejected.

        ``_enforce_token_and_depth_budgets`` enforces ``MAX_HCL_DEPTH`` before
        delegating to either backend so deeply nested input always raises Hcl2Error.
        """
        depth = hcl_parser.MAX_HCL_DEPTH + 50
        source = "a = " + "[" * depth + "]" * depth
        with self.assertRaises(hcl_parser.Hcl2Error):
            hcl_parser.loads(source)

    def test_unterminated_constructs_are_reported(self) -> None:
        """An unterminated comment, string, or heredoc must be a syntax error."""
        for source in ("/* nope", 'a = "unterminated', "a = <<EOT\nbody\n"):
            with self.subTest(source=source):
                with self.assertRaises(hcl_parser.Hcl2Error):
                    hcl_parser.loads(source)

    def test_oversize_document_is_rejected(self) -> None:
        """CWE-400: documents above the byte budget are refused."""
        with self.assertRaises(hcl_parser.Hcl2Error):
            hcl_parser.loads("a = 1\n" * (hcl_parser.MAX_HCL_BYTES // 4))

    def test_representative_terraform_parses_to_expected_shape(self) -> None:
        """Output must retain the python-hcl2 canonical structure consumers rely on.

        The two accepted backends agree on block and collection shape but differ
        on interpolation: ``python-hcl2`` 7.x preserves the ``${...}`` wrapper on
        a bare traversal, while the in-repo parser yields the inner reference.
        Consumers treat both as an unresolved reference, so assert per backend.
        """
        parsed = hcl_parser.loads(
            'resource "google_storage_bucket" "b" {\n'
            '  name = "x"\n'
            "  versioning { enabled = true }\n"
            '  labels = { a = "1", b = "2" }\n'
            "  items = [1, 2.5, true, null, var.ref]\n"
            "}\n"
        )
        bucket = parsed["resource"][0]["google_storage_bucket"]["b"]
        self.assertEqual(bucket["name"], "x")
        self.assertEqual(bucket["versioning"], [{"enabled": True}])
        self.assertEqual(bucket["labels"], {"a": "1", "b": "2"})

        expected_ref = "var.ref" if hcl_parser.BACKEND == "hcl_parser.HclParser" else "${var.ref}"
        self.assertEqual(bucket["items"], [1, 2.5, True, None, expected_ref])


class TestPathConfinement(unittest.TestCase):
    """Directory traversal and symlink redirection defenses (CWE-22, CWE-59, CWE-367)."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name).resolve()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_traversal_outside_boundary_is_refused(self) -> None:
        """CWE-22: '..' segments must not escape the authorization boundary."""
        with self.assertRaises(PermissionError):
            fh.ensure_path_within_boundary(self.root / ".." / "escaped.md", self.root)

    def test_symlinked_component_inside_boundary_is_refused(self) -> None:
        """CWE-59: a symlink inside the boundary can be repointed after validation.

        The link points to a directory that is also inside the boundary, so the
        containment check passes and only the component walk can reject it. Before
        the walk used the caller's path, this case was accepted.
        """
        box = self.root / "box"
        (box / "real").mkdir(parents=True)
        (box / "out").symlink_to(box / "real")
        with self.assertRaises(PermissionError) as ctx:
            fh.ensure_path_within_boundary(box / "out" / "report.md", box)
        self.assertIn("symbolic link", str(ctx.exception))

    def test_symlinked_leaf_inside_boundary_is_refused(self) -> None:
        """A link as the final component is refused even when it stays inside."""
        box = self.root / "box"
        box.mkdir()
        (box / "real.md").write_text("x", encoding="utf-8")
        (box / "alias.md").symlink_to(box / "real.md")
        with self.assertRaises(PermissionError):
            fh.ensure_path_within_boundary(box / "alias.md", box)

    def test_dotdot_out_of_symlinked_directory_is_refused(self) -> None:
        """A link that a later '..' steps back out of is still a traversed link."""
        box = self.root / "box"
        (box / "real" / "sub").mkdir(parents=True)
        (box / "out").symlink_to(box / "real" / "sub")
        with self.assertRaises(PermissionError):
            fh.ensure_path_within_boundary(f"{box}/out/../report.md", box)

    def test_symlink_pointing_outside_boundary_is_refused(self) -> None:
        """CWE-22: a link that escapes the boundary fails the containment check."""
        box = self.root / "box"
        box.mkdir()
        (self.root / "outside").mkdir()
        (box / "out").symlink_to(self.root / "outside")
        with self.assertRaises(PermissionError) as ctx:
            fh.ensure_path_within_boundary(box / "out" / "report.md", box, allow_symlinks=True)
        self.assertIn("Path traversal detected", str(ctx.exception))

    def test_allow_symlinks_accepts_link_inside_boundary(self) -> None:
        """Read paths may opt in to in-boundary links; the resolved path is returned."""
        box = self.root / "box"
        (box / "real").mkdir(parents=True)
        (box / "out").symlink_to(box / "real")
        resolved = fh.ensure_path_within_boundary(box / "out" / "f.tf", box, allow_symlinks=True)
        self.assertEqual(resolved, box / "real" / "f.tf")

    def test_link_above_boundary_root_is_accepted(self) -> None:
        """A link that names the boundary itself (like macOS /var) is not traversed inside it."""
        box = self.root / "box"
        box.mkdir()
        alias = self.root / "alias"
        alias.symlink_to(box)
        self.assertEqual(fh.ensure_path_within_boundary(alias / "doc.md", box), box / "doc.md")
        self.assertEqual(fh.ensure_path_within_boundary(box / "doc.md", alias), box / "doc.md")

    def test_path_entering_boundary_through_outside_link_is_refused(self) -> None:
        """A link outside the boundary that points below its root is still a link."""
        box = self.root / "box"
        (box / "real").mkdir(parents=True)
        door = self.root / "door"
        door.symlink_to(box / "real")
        with self.assertRaises(PermissionError):
            fh.ensure_path_within_boundary(door / "doc.md", box)

    def test_reserved_device_name_above_boundary_is_accepted(self) -> None:
        """On POSIX a directory above the boundary may be named 'aux'."""
        box = self.root / "aux" / "box"
        box.mkdir(parents=True)
        self.assertEqual(fh.ensure_path_within_boundary(box / "doc.md", box), box / "doc.md")

    def test_reserved_device_name_below_boundary_is_refused(self) -> None:
        """Names the engine would create below the boundary are still checked."""
        with self.assertRaises(PermissionError):
            fh.ensure_path_within_boundary(self.root / "sub" / "nul.txt", self.root)

    def test_write_through_symlinked_directory_is_refused(self) -> None:
        """write_text_file must check the caller's path, not the resolved one."""
        box = self.root / "box"
        (box / "real").mkdir(parents=True)
        (box / "out").symlink_to(box / "real")
        with self.assertRaises(PermissionError):
            fh.write_text_file(box / "out" / "doc.md", "content", allowed_boundary=box)
        self.assertEqual(list((box / "real").iterdir()), [])

    def test_null_byte_in_path_is_refused(self) -> None:
        """A null byte can truncate a path at the syscall layer."""
        with self.assertRaises(PermissionError):
            fh.ensure_path_within_boundary(f"{self.root}/a\0b", self.root)

    def test_write_through_symlink_is_refused(self) -> None:
        """An artifact must never be written through a link that redirects it."""
        link = self.root / "report.md"
        link.symlink_to(self.root / "elsewhere.md")
        with self.assertRaises(PermissionError):
            fh.write_text_file(link, "content")

    def test_write_is_atomic_and_leaves_no_residue(self) -> None:
        """A reader must never observe a partially written compliance artifact."""
        target = fh.write_text_file(self.root / "nested" / "doc.md", "final")
        self.assertEqual(target.read_text(encoding="utf-8"), "final")
        self.assertEqual([p.name for p in target.parent.iterdir()], ["doc.md"])

    def test_multiply_encoded_filename_is_rejected(self) -> None:
        """Bounded decoding: a deliberately over-encoded name must be refused.

        Each additional ``25`` inserted after the ``%`` costs one decoding round, so
        this payload needs more rounds than the budget permits and must be rejected
        rather than silently decoded.
        """
        nested = "%" + "25" * (fh.MAX_PERCENT_DECODE_ROUNDS + 3) + "2e2e2f"
        with self.assertRaises(ValueError):
            fh.sanitize_filename(nested)

    def test_ordinary_encoded_filename_is_still_normalized(self) -> None:
        """Legitimate single-encoded names must survive sanitization."""
        self.assertEqual(fh.sanitize_filename("SSP%20Report.md"), "SSP Report.md")

    def test_traversal_filename_is_flattened(self) -> None:
        """Separators and parent references must not survive into a filename."""
        self.assertNotIn("/", fh.sanitize_filename("../../etc/passwd"))


class TestReadBudgets(unittest.TestCase):
    """Memory-safety budgets for untrusted file and YAML input (CWE-400, CWE-776)."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name).resolve()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_oversize_file_is_refused_not_truncated(self) -> None:
        """Silently truncating evidence would produce a wrong-but-plausible artifact."""
        big = self.root / "big.txt"
        big.write_text("z" * 4096, encoding="utf-8")
        with self.assertRaises(ValueError):
            fh.read_text_file(big, max_bytes=1024)

    def test_directory_is_not_read_as_text(self) -> None:
        """A directory passed where a file is expected must fail explicitly."""
        with self.assertRaises(ValueError):
            fh.read_text_file(self.root)

    def test_yaml_alias_bomb_is_refused(self) -> None:
        """CWE-776: PyYAML SafeLoader expands aliases with no budget of its own."""
        anchors = ["a: &a [x, x, x, x, x, x, x, x, x]"]
        previous = "a"
        for name in "bcdefghij":
            refs = ", ".join([f"*{previous}"] * 9)
            anchors.append(f"{name}: &{name} [{refs}]")
            previous = name
        bomb = "\n".join(anchors * 10)
        with self.assertRaises(ValueError) as ctx:
            fh.parse_yaml_safe(bomb)
        self.assertIn("alias", str(ctx.exception).lower())

    def test_ordinary_yaml_with_a_few_aliases_still_parses(self) -> None:
        """Anchors are legitimate YAML; only abusive volumes are rejected."""
        parsed = fh.parse_yaml_safe("defaults: &d\n  tier: high\nprod:\n  <<: *d\n")
        self.assertEqual(parsed["defaults"], {"tier": "high"})


class TestSecretScrubbing(unittest.TestCase):
    """Redaction correctness and traversal safety for the secret scrubber."""

    def test_sensitive_keys_and_values_are_redacted(self) -> None:
        """Both key-name matches and embedded high-entropy values must be redacted."""
        scrubbed = fh.scrub_sensitive_data(
            {"api_key": "value", "note": "ghp_" + "a" * 36, "safe": "hello"}
        )
        self.assertEqual(scrubbed["api_key"], "[REDACTED_SENSITIVE]")
        self.assertEqual(scrubbed["note"], "[REDACTED_SENSITIVE]")
        self.assertEqual(scrubbed["safe"], "hello")

    def test_self_referential_structure_terminates(self) -> None:
        """CWE-674: a cycle must be marked, not recursed into forever."""
        node = {"name": "root"}
        node["self"] = node
        scrubbed = fh.scrub_sensitive_data(node)
        self.assertEqual(scrubbed["self"], "[REDACTED_CYCLE]")

    def test_excessive_nesting_is_truncated_not_crashed(self) -> None:
        """A depth bomb must degrade to a marker rather than raise RecursionError."""
        nested: dict = {}
        cursor = nested
        for _ in range(fh.MAX_STRUCTURE_DEPTH + 20):
            child: dict = {}
            cursor["child"] = child
            cursor = child
        scrubbed = fh.scrub_sensitive_data(nested)
        rendered = json.dumps(scrubbed)
        self.assertIn("[REDACTED_DEPTH_LIMIT]", rendered)

    def test_unscannable_value_fails_closed(self) -> None:
        """A value too large to inspect must be redacted, never emitted verbatim."""
        huge = "a" * (fh.MAX_SECRET_SCAN_CHARS + 1)
        self.assertEqual(fh.scrub_sensitive_data(huge), "[REDACTED_UNSCANNABLE]")


class TestFormulaInjection(unittest.TestCase):
    """Spreadsheet formula injection defenses (CWE-1236)."""

    def test_formula_triggers_are_neutralized(self) -> None:
        """Every documented trigger character must be quote-prefixed."""
        for payload in ("=cmd|'/c calc'!A1", "@SUM(1)", "+1+1", "-1+1", "|ls", "%00"):
            with self.subTest(payload=payload):
                self.assertTrue(str(fh.clean_cell_value(payload)).startswith("'"))

    def test_masked_triggers_are_neutralized(self) -> None:
        """Leading whitespace, control, and zero-width characters must not bypass."""
        for prefix in (" ", "\t", "\u200b", "\u202e", "\ufeff"):
            with self.subTest(prefix=repr(prefix)):
                self.assertTrue(str(fh.clean_cell_value(prefix + "=1+1")).startswith("'"))

    def test_quote_prefixing_is_idempotent(self) -> None:
        """Re-sanitizing a stored value must not accumulate quotes."""
        once = fh.clean_cell_value("=1+1")
        self.assertEqual(fh.clean_cell_value(once), once)

    def test_genuine_numbers_are_not_quoted(self) -> None:
        """Negative and scientific-notation numerics must stay numeric."""
        for numeric in ("-42", "+3.14", "-1.5e-3"):
            with self.subTest(numeric=numeric):
                self.assertFalse(str(fh.clean_cell_value(numeric)).startswith("'"))

    def test_value_is_truncated_to_the_excel_cell_limit(self) -> None:
        """Exceeding Excel's 32,767 character limit corrupts the workbook."""
        result = fh.clean_cell_value("x" * (fh.MAX_EXCEL_CELL_LENGTH + 500))
        self.assertLessEqual(len(str(result)), fh.MAX_EXCEL_CELL_LENGTH)


class TestDependencyBootstrap(unittest.TestCase):
    """Supply-chain controls on ``sys.path`` mutation (CWE-426, CWE-732)."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name).resolve()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_world_writable_directory_is_refused(self) -> None:
        """A writable sys.path entry is arbitrary code execution at import time."""
        loose = self.root / "loose"
        loose.mkdir()
        os.chmod(loose, 0o777)
        self.assertFalse(fh._is_safe_site_packages_dir(str(loose)))

    def test_symlinked_directory_is_refused(self) -> None:
        """A symlinked import path can be repointed after validation."""
        real = self.root / "real"
        real.mkdir(mode=0o755)
        link = self.root / "link"
        link.symlink_to(real)
        self.assertFalse(fh._is_safe_site_packages_dir(str(link)))

    def test_relative_path_is_refused(self) -> None:
        """A relative sys.path entry resolves against the current directory."""
        self.assertFalse(fh._is_safe_site_packages_dir("relative/site-packages"))

    def test_well_permissioned_absolute_directory_is_accepted(self) -> None:
        """The control must not reject legitimate, correctly permissioned locations."""
        good = self.root / "good"
        good.mkdir(mode=0o755)
        os.chmod(good, 0o755)
        self.assertTrue(fh._is_safe_site_packages_dir(str(good)))

    def _bootstrap(self, env: dict, yaml_importable: bool) -> tuple:
        """Runs ``_bootstrap_environment`` in a controlled environment.

        A fake checkov virtualenv is created under the temp dir and is the only
        discovery pattern. Host ``COMPLIANCE_*`` variables are cleared first.

        Args:
            env: Environment variables to set for the call.
            yaml_importable: When False, ``import yaml`` raises ImportError.

        Returns:
            (entries appended to sys.path, fake borrowed dir, explicit dir).
        """
        borrowed = self.root / "pipx" / "checkov" / "lib" / "python3.99" / "site-packages"
        borrowed.mkdir(parents=True)
        os.chmod(borrowed, 0o755)
        explicit = self.root / "explicit"
        explicit.mkdir()
        os.chmod(explicit, 0o755)
        pattern = str(self.root / "pipx" / "checkov" / "lib" / "python*" / "site-packages")
        resolved_env = {key: value.format(explicit=explicit) for key, value in env.items()}
        original_path = list(sys.path)
        with patch.dict(os.environ), \
                patch.object(sys, "path", list(original_path)), \
                patch.object(fh, "_FOREIGN_TOOLCHAIN_PATTERNS", (pattern,)), \
                patch.dict(sys.modules, {} if yaml_importable else {"yaml": None}):
            for name in (fh._STRICT_DEPS_ENV, fh._ALLOW_BORROWED_DEPS_ENV, fh._SITE_PACKAGES_ENV):
                os.environ.pop(name, None)
            os.environ.update(resolved_env)
            fh._bootstrap_environment()
            added = [entry for entry in sys.path if entry not in original_path]
        return added, str(borrowed), str(explicit)

    def test_borrowing_requires_explicit_opt_in(self) -> None:
        """Positive control: with the opt-in and no PyYAML, the fake venv is used."""
        added, borrowed, _ = self._bootstrap({"COMPLIANCE_ALLOW_BORROWED_DEPS": "1"}, yaml_importable=False)
        self.assertEqual(added, [borrowed])

    def test_borrowing_is_off_by_default(self) -> None:
        """Without the opt-in a missing PyYAML never triggers discovery."""
        added, _, _ = self._bootstrap({}, yaml_importable=False)
        self.assertEqual(added, [])

    def test_strict_mode_overrides_borrowing_opt_in(self) -> None:
        """COMPLIANCE_STRICT_DEPS=1 wins over COMPLIANCE_ALLOW_BORROWED_DEPS=1."""
        added, _, _ = self._bootstrap(
            {"COMPLIANCE_STRICT_DEPS": "1", "COMPLIANCE_ALLOW_BORROWED_DEPS": "1"},
            yaml_importable=False,
        )
        self.assertEqual(added, [])

    def test_strict_mode_ignores_explicit_site_packages(self) -> None:
        """Strict mode adds nothing to sys.path, including COMPLIANCE_SITE_PACKAGES."""
        added, _, _ = self._bootstrap(
            {"COMPLIANCE_STRICT_DEPS": "true", "COMPLIANCE_SITE_PACKAGES": "{explicit}"},
            yaml_importable=True,
        )
        self.assertEqual(added, [])

    def test_explicit_site_packages_is_honored_without_strict_mode(self) -> None:
        """Positive control for the explicit, operator-curated path."""
        added, _, explicit = self._bootstrap({"COMPLIANCE_SITE_PACKAGES": "{explicit}"}, yaml_importable=True)
        self.assertEqual(added, [explicit])

    def test_truthy_env_values(self) -> None:
        """Only 1/true/yes/on (any case, surrounding spaces ignored) enable a switch."""
        for value, expected in (
            ("1", True), ("true", True), ("TRUE", True), (" yes ", True), ("On", True),
            ("", False), ("0", False), ("false", False), ("no", False), ("off", False), ("2", False),
        ):
            with self.subTest(value=value):
                with patch.dict(os.environ, {"COMPLIANCE_TEST_SWITCH": value}):
                    self.assertIs(fh.env_flag_enabled("COMPLIANCE_TEST_SWITCH"), expected)


class TestAuditTrail(unittest.TestCase):
    """Structured audit logging guarantees (NIST SP 800-53 AU-3, AU-8, AU-9)."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name).resolve()
        self.sink = self.root / "audit" / "trail.jsonl"
        self.audit = audit_log.AuditLogger(self.sink, "test", allowed_boundary=self.root)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_record_contains_required_audit_content(self) -> None:
        """AU-3: every record needs timestamp, type, outcome, subject, and object."""
        record = self.audit.emit(
            audit_log.AuditEvent.ARTIFACT_GENERATED,
            subject="operator",
            obj="SSP.docx",
        )
        for field in ("timestamp", "event_type", "outcome", "subject", "object", "sequence"):
            self.assertIn(field, record)
        self.assertTrue(record["timestamp"].endswith("+00:00"), "AU-8 requires an explicit UTC offset")

    def test_sink_is_owner_only(self) -> None:
        """AU-9: audit evidence must not be group- or world-readable."""
        self.audit.emit(audit_log.AuditEvent.PIPELINE_STARTED)
        mode = stat.S_IMODE(self.sink.stat().st_mode)
        self.assertEqual(mode & 0o077, 0, f"audit sink mode {mode:o} exposes records to other users")

    def test_detail_is_redacted_before_persistence(self) -> None:
        """The audit trail must never itself become the credential leak path."""
        self.audit.emit(
            audit_log.AuditEvent.CONFIG_LOADED,
            detail={"client_secret": "hunter2", "path": "config.yaml"},
        )
        persisted = self.sink.read_text(encoding="utf-8")
        self.assertNotIn("hunter2", persisted)
        self.assertIn("[REDACTED_SENSITIVE]", persisted)

    def test_chain_detects_tampering(self) -> None:
        """AU-9: altering a persisted record must break the digest chain."""
        self.audit.emit(audit_log.AuditEvent.PIPELINE_STARTED)
        self.audit.emit(audit_log.AuditEvent.PIPELINE_COMPLETED, detail={"count": 1})
        self.assertTrue(self.audit.verify_chain())

        tampered = self.sink.read_text(encoding="utf-8").replace('"count": 1', '"count": 9')
        self.sink.write_text(tampered, encoding="utf-8")
        self.assertFalse(self.audit.verify_chain())

    def test_chain_detects_deletion(self) -> None:
        """AU-9: removing a record must be detectable, not silent."""
        for _ in range(3):
            self.audit.emit(audit_log.AuditEvent.ARTIFACT_GENERATED)
        lines = self.sink.read_text(encoding="utf-8").splitlines()
        self.sink.write_text("\n".join(lines[:1] + lines[2:]) + "\n", encoding="utf-8")
        self.assertFalse(self.audit.verify_chain())

    def test_failure_outcome_is_recorded_and_exception_propagates(self) -> None:
        """The audit wrapper must observe failures without swallowing them."""
        audit_log.configure_audit_log(self.sink, "test", allowed_boundary=self.root)
        # `configure_audit_log` installs a process-wide singleton; leaving it bound
        # to this test's temporary sink would leak into every later test.
        self.addCleanup(audit_log.reset_audit_log)
        with self.assertRaises(RuntimeError):
            with audit_log.audit_operation(audit_log.AuditEvent.ARTIFACT_GENERATED, obj="x"):
                raise RuntimeError("boom")
        last = json.loads(self.sink.read_text(encoding="utf-8").splitlines()[-1])
        self.assertEqual(last["outcome"], audit_log.AuditOutcome.FAILURE)
        self.assertEqual(last["detail"]["error_type"], "RuntimeError")

    def test_sink_outside_boundary_is_refused(self) -> None:
        """The audit trail must stay inside the authorization boundary."""
        with self.assertRaises(PermissionError):
            audit_log.AuditLogger("/tmp/escaped-audit.jsonl", allowed_boundary=self.root)


if __name__ == "__main__":
    unittest.main(verbosity=2)
