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

"""Granular edge-case and negative tests for the hardened HCL2 lexer and parser.

Directly tests ``HclLexer``, ``HclParser``, ``loads()``, and ``load()`` in ``hcl_parser.py``:
- Lexer: numeric representations, escape sequences, heredoc varieties (stripped and unstripped),
  block and line comment handling, token budget enforcement, template sequences in strings.
- Parser: canonical Terraform blocks (resource, data, module, variable, output, locals, terraform, provider),
  custom labeled blocks, attribute duplicate list promotion, nested collection handling.
- loads(): CRLF and byte-order-mark normalization on both backends, backend result checks.
- Negative & failure conditions: unterminated constructs, depth budget overflows, syntax errors,
  unexpected tokens, stream size limits.
"""

import io
import os
import sys
import types
from typing import List, Optional
import unittest
from unittest import mock

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.abspath(os.path.join(TESTS_DIR, "..", "src"))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from compliance_engine import hcl_parser


class TestHclLexerEdges(unittest.TestCase):
    """Lexer tokenization, escape handling, and literal parsing edge cases."""

    def test_lexer_numeric_representations(self) -> None:
        """Numbers across integers, floats, signed values, and scientific notation."""
        source = "a = 42\nb = -100\nc = +5\nd = 3.14159\ne = -0.001\nf = 1.5e-3\ng = 2E+10\nh = -4.2e4"
        tokens = hcl_parser.HclLexer(source).tokenize()
        num_tokens = [tok for tok in tokens if tok.type == "NUMBER"]

        self.assertEqual(len(num_tokens), 8)
        self.assertEqual(num_tokens[0].value, 42)
        self.assertEqual(num_tokens[1].value, -100)
        self.assertEqual(num_tokens[2].value, 5)
        self.assertAlmostEqual(num_tokens[3].value, 3.14159)
        self.assertAlmostEqual(num_tokens[4].value, -0.001)
        self.assertAlmostEqual(num_tokens[5].value, 0.0015)
        self.assertEqual(num_tokens[6].value, 2e10)
        self.assertAlmostEqual(num_tokens[7].value, -42000.0)

    def test_lexer_string_escapes(self) -> None:
        """Escape sequences inside double-quoted string literals."""
        source = r'a = "hello\nworld\ttab\rreturn\"quote\\slash"'
        tokens = hcl_parser.HclLexer(source).tokenize()
        str_token = next(tok for tok in tokens if tok.type == "STRING")
        self.assertEqual(str_token.value, 'hello\nworld\ttab\rreturn"quote\\slash')

    def test_lexer_unrecognized_string_escapes_preserved(self) -> None:
        r"""An unrecognised escape (e.g. \a or \$) preserves the backslash sequence."""
        source = r'a = "cost is \$100 and \a bell"'
        tokens = hcl_parser.HclLexer(source).tokenize()
        str_token = next(tok for tok in tokens if tok.type == "STRING")
        self.assertEqual(str_token.value, r"cost is \$100 and \a bell")

    def test_lexer_heredoc_stripped_indentation(self) -> None:
        """Heredoc with <<- marker strips common leading indentation."""
        source = "script = <<-EOF\n    echo hello\n    echo world\nEOF\n"
        tokens = hcl_parser.HclLexer(source).tokenize()
        str_token = next(tok for tok in tokens if tok.type == "STRING")
        self.assertEqual(str_token.value, "echo hello\necho world")

    def test_lexer_heredoc_unstripped_indentation(self) -> None:
        """Heredoc with << marker preserves exact leading indentation."""
        source = "script = <<EOF\n    echo hello\n    echo world\nEOF\n"
        tokens = hcl_parser.HclLexer(source).tokenize()
        str_token = next(tok for tok in tokens if tok.type == "STRING")
        self.assertEqual(str_token.value, "    echo hello\n    echo world")

    def test_lexer_heredoc_empty_body(self) -> None:
        """Empty heredoc body produces an empty string token."""
        source = "empty = <<EOF\nEOF\n"
        tokens = hcl_parser.HclLexer(source).tokenize()
        str_token = next(tok for tok in tokens if tok.type == "STRING")
        self.assertEqual(str_token.value, "")

    def test_lexer_heredoc_unterminated_raises(self) -> None:
        """Heredoc without closing marker raises Hcl2Error."""
        source = "script = <<EOF\nline one\nline two\n"
        with self.assertRaises(hcl_parser.Hcl2Error):
            hcl_parser.HclLexer(source).tokenize()

    def test_lexer_heredoc_malformed_marker_raises(self) -> None:
        """Heredoc without a valid identifier marker raises Hcl2Error."""
        source = "script = << \nbody\nEOF\n"
        with self.assertRaises(hcl_parser.Hcl2Error):
            hcl_parser.HclLexer(source).tokenize()

    def test_lexer_heredoc_marker_with_dashes(self) -> None:
        """Heredoc delimiters are HCL identifiers and may contain dashes.

        The marker pattern used to stop at the first dash, so the closing line
        never matched and the whole file failed with "Unclosed heredoc".
        """
        source = "script = <<END-OF-SCRIPT\necho hi\nEND-OF-SCRIPT\nnext = 1\n"
        parsed = hcl_parser.HclParser(hcl_parser.HclLexer(source).tokenize()).parse()
        self.assertEqual(parsed, {"script": "echo hi", "next": 1})

    def test_lexer_block_comments_with_nested_asterisks(self) -> None:
        """Block comment containing asterisks and slash characters."""
        source = "/* * *** multi * line *** */ a = 1"
        tokens = hcl_parser.HclLexer(source).tokenize()
        self.assertEqual(tokens[0].type, "IDENTIFIER")
        self.assertEqual(tokens[0].value, "a")

    def test_lexer_unterminated_block_comment_raises(self) -> None:
        """Unclosed block comment raises Hcl2Error."""
        source = "/* unterminated block comment"
        with self.assertRaises(hcl_parser.Hcl2Error):
            hcl_parser.HclLexer(source).tokenize()

    def test_lexer_line_comments_hash_and_double_slash(self) -> None:
        """Line comments starting with # and // are ignored."""
        source = "# comment one\na = 1 // comment two\n# comment three\nb = 2"
        tokens = hcl_parser.HclLexer(source).tokenize()
        ident_tokens = [tok for tok in tokens if tok.type == "IDENTIFIER"]
        self.assertEqual([tok.value for tok in ident_tokens], ["a", "b"])

    def test_lexer_token_budget_overflow_raises(self) -> None:
        """Lexer aborts with Hcl2Error when max_tokens is exceeded."""
        source = "a = 1 b = 2 c = 3 d = 4 e = 5"
        lexer = hcl_parser.HclLexer(source, max_tokens=6)
        with self.assertRaises(hcl_parser.Hcl2Error):
            lexer.tokenize()

    def test_lexer_keywords_and_identifiers(self) -> None:
        """Booleans, null, and identifiers with special characters."""
        source = "is_active = true is_disabled = false empty_val = null my-var.name = 1"
        tokens = hcl_parser.HclLexer(source).tokenize()
        tok_dict = {tokens[i].value: tokens[i + 2] for i in range(0, len(tokens) - 1, 3)}

        self.assertIs(tok_dict["is_active"].value, True)
        self.assertEqual(tok_dict["is_active"].type, "BOOLEAN")
        self.assertIs(tok_dict["is_disabled"].value, False)
        self.assertEqual(tok_dict["is_disabled"].type, "BOOLEAN")
        self.assertIsNone(tok_dict["empty_val"].value)
        self.assertEqual(tok_dict["empty_val"].type, "NULL")


class TestHclParserEngine(unittest.TestCase):
    """Deep testing of the recursive descent parser engine and canonical shapes."""

    def test_parser_canonical_resource_and_data_blocks(self) -> None:
        """Resource and data blocks map into list of dicts with type and name keys."""
        source = (
            'resource "google_compute_network" "vpc" {\n'
            '  name = "custom-vpc"\n'
            '  auto_create_subnetworks = false\n'
            '}\n'
            'data "google_project" "current" {\n'
            '  project_id = "test-proj"\n'
            '}\n'
        )
        tokens = hcl_parser.HclLexer(source).tokenize()
        parsed = hcl_parser.HclParser(tokens).parse()

        self.assertIn("resource", parsed)
        self.assertIn("data", parsed)
        res = parsed["resource"][0]["google_compute_network"]["vpc"]
        self.assertEqual(res["name"], "custom-vpc")
        self.assertIs(res["auto_create_subnetworks"], False)

        data = parsed["data"][0]["google_project"]["current"]
        self.assertEqual(data["project_id"], "test-proj")

    def test_parser_module_and_variable_blocks(self) -> None:
        """Module and variable blocks format into name-keyed dictionaries."""
        source = (
            'module "vpc_hub" {\n'
            '  source = "./modules/net-vpc"\n'
            '  project_id = "my-prj"\n'
            '}\n'
            'variable "environment" {\n'
            '  type = "string"\n'
            '  default = "prod"\n'
            '}\n'
        )
        tokens = hcl_parser.HclLexer(source).tokenize()
        parsed = hcl_parser.HclParser(tokens).parse()

        mod = parsed["module"][0]["vpc_hub"]
        self.assertEqual(mod["source"], "./modules/net-vpc")
        self.assertEqual(mod["project_id"], "my-prj")

        var = parsed["variable"][0]["environment"]
        self.assertEqual(var["default"], "prod")

    def test_parser_locals_and_terraform_blocks(self) -> None:
        """Locals and terraform blocks map into lists of block bodies."""
        source = (
            "locals {\n"
            '  prefix = "afe"\n'
            "  env_code = 1\n"
            "}\n"
            "terraform {\n"
            '  required_version = ">= 1.5.0"\n'
            "}\n"
        )
        tokens = hcl_parser.HclLexer(source).tokenize()
        parsed = hcl_parser.HclParser(tokens).parse()

        self.assertEqual(parsed["locals"][0]["prefix"], "afe")
        self.assertEqual(parsed["locals"][0]["env_code"], 1)
        self.assertEqual(parsed["terraform"][0]["required_version"], ">= 1.5.0")

    def test_parser_attribute_promotion_to_list(self) -> None:
        """Duplicate attribute assignments within the same block are promoted to a list."""
        source = (
            "block {\n"
            '  tag = "web"\n'
            '  tag = "app"\n'
            '  tag = "db"\n'
            "}\n"
        )
        tokens = hcl_parser.HclLexer(source).tokenize()
        parsed = hcl_parser.HclParser(tokens).parse()

        block_body = parsed["block"][0]
        self.assertEqual(block_body["tag"], ["web", "app", "db"])

    def test_parser_colon_attribute_assignment(self) -> None:
        """JSON-style colon assignment is supported alongside equals."""
        source = 'item: "value", other: 123'
        tokens = hcl_parser.HclLexer(source).tokenize()
        parsed = hcl_parser.HclParser(tokens).parse()

        self.assertEqual(parsed["item"], "value")
        self.assertEqual(parsed["other"], 123)

    def test_parser_nested_maps_and_tuples(self) -> None:
        """Collections with trailing commas and mixed scalar types."""
        source = (
            "settings = {\n"
            "  enabled = true,\n"
            "  subnets = [10, 20, 30,],\n"
            "  metadata = { k1 = \"v1\", k2 = null, },\n"
            "}\n"
        )
        tokens = hcl_parser.HclLexer(source).tokenize()
        parsed = hcl_parser.HclParser(tokens).parse()

        settings = parsed["settings"]
        self.assertIs(settings["enabled"], True)
        self.assertEqual(settings["subnets"], [10, 20, 30])
        self.assertEqual(settings["metadata"]["k1"], "v1")
        self.assertIsNone(settings["metadata"]["k2"])

    def test_parser_depth_budget_overflow_raises(self) -> None:
        """Parser enforces nesting depth budget and raises Hcl2Error."""
        source = "a = [[[[[1]]]]]"
        tokens = hcl_parser.HclLexer(source).tokenize()
        parser = hcl_parser.HclParser(tokens, max_depth=3)
        with self.assertRaises(hcl_parser.Hcl2Error):
            parser.parse()

    def test_parser_unexpected_top_level_token_raises(self) -> None:
        """Unexpected punctuation at top-level surfaces a clean Hcl2Error."""
        source = "= bad_assignment"
        tokens = hcl_parser.HclLexer(source).tokenize()
        with self.assertRaises(hcl_parser.Hcl2Error):
            hcl_parser.HclParser(tokens).parse()

    def test_parser_unclosed_block_raises(self) -> None:
        """Block missing closing brace raises Hcl2Error."""
        source = 'resource "type" "name" {\n  attr = 1\n'
        tokens = hcl_parser.HclLexer(source).tokenize()
        with self.assertRaises(hcl_parser.Hcl2Error):
            hcl_parser.HclParser(tokens).parse()

    def test_parser_function_calls_and_expressions(self) -> None:
        """Function calls like toset(), ternaries, and unary negation parse without error."""
        source = (
            'resource "google_kms_crypto_key" "keys" {\n'
            '  for_each = toset(var.keys)\n'
            '  name = "key-${each.value}"\n'
            '  enabled = !var.disabled\n'
            '  tier = var.is_prod ? "high" : "low"\n'
            '}\n'
        )
        tokens = hcl_parser.HclLexer(source).tokenize()
        parsed = hcl_parser.HclParser(tokens).parse()
        res = parsed["resource"][0]["google_kms_crypto_key"]["keys"]
        self.assertIn("toset", str(res["for_each"]))
        self.assertEqual(res["name"], "key-${each.value}")
        self.assertIn("!var.disabled", str(res["enabled"]))
        self.assertIn("?", str(res["tier"]))

    def test_parser_comprehensions(self) -> None:
        """Tuple and map comprehensions parse safely."""
        source = (
            'locals {\n'
            '  tuple_comp = [for s in var.list : upper(s)]\n'
            '  map_comp = {for k, v in var.map : k => v}\n'
            '}\n'
        )
        tokens = hcl_parser.HclLexer(source).tokenize()
        parsed = hcl_parser.HclParser(tokens).parse()
        loc = parsed["locals"][0]
        self.assertIn("for", str(loc["tuple_comp"]))
        self.assertIn("_comprehension", loc["map_comp"])


class TestStringTemplates(unittest.TestCase):
    """Quoted strings containing ``${ ... }`` / ``%{ ... }`` template sequences."""

    def _string_value(self, source: str) -> str:
        """Returns the value of the single STRING token in ``source``."""
        tokens = hcl_parser.HclLexer(source).tokenize()
        strings = [tok for tok in tokens if tok.type == "STRING"]
        self.assertEqual(len(strings), 1, tokens)
        return strings[0].value

    def test_quoted_argument_inside_interpolation_stays_in_one_token(self) -> None:
        """A quote inside ``${ ... }`` must not end the literal."""
        self.assertEqual(self._string_value('a = "x${f("y")}z"'), 'x${f("y")}z')

    def test_interpolated_string_does_not_capture_the_following_block(self) -> None:
        """Regression: a split literal used to re-attach the next block to a junk key.

        The lexer ended the string at the quote before ``logs``. The leftover
        tokens were read as a block named ``logs`` whose labels swallowed
        ``versioning``, so the bucket silently lost its versioning block.
        """
        source = (
            'resource "google_storage_bucket" "b" {\n'
            '  name = "${lookup(var.names, "logs", "default")}"\n'
            "  versioning {\n"
            "    enabled = true\n"
            "  }\n"
            "}\n"
        )
        parsed = hcl_parser.HclParser(hcl_parser.HclLexer(source).tokenize()).parse()
        self.assertEqual(
            parsed["resource"][0]["google_storage_bucket"]["b"],
            {
                "name": '${lookup(var.names, "logs", "default")}',
                "versioning": [{"enabled": True}],
            },
        )

    def test_nested_templates_and_object_braces(self) -> None:
        """Templates inside nested strings and braces inside templates are tracked."""
        source = 'a = "${f("${g("x")}")}-${ {k = "v"}["k"] }"'
        self.assertEqual(self._string_value(source), '${f("${g("x")}")}-${ {k = "v"}["k"] }')

    def test_template_directive_with_quoted_operands(self) -> None:
        """``%{ ... }`` directives are tracked like interpolations."""
        source = 'a = "%{ for s in var.l }${s == "x" ? "X" : s}%{ endfor }"'
        self.assertEqual(
            self._string_value(source), '%{ for s in var.l }${s == "x" ? "X" : s}%{ endfor }'
        )

    def test_escapes_are_decoded_only_outside_templates(self) -> None:
        """Literal text decodes escapes; template text is kept verbatim."""
        source = r'a = "tab\there ${f("q\"t")}"'
        self.assertEqual(self._string_value(source), 'tab\there ${f("q\\"t")}')

    def test_escaped_template_introducers_are_literal(self) -> None:
        """``$${`` and ``%%{`` do not open a template; a lone ``$`` or ``%`` is text."""
        source = 'a = "$${x} %%{y} costs $5, 100%"'
        self.assertEqual(self._string_value(source), "$${x} %%{y} costs $5, 100%")

    def test_unterminated_template_raises(self) -> None:
        """An unclosed template or nested string is a syntax error, not a silent split."""
        for source in ('a = "${f("x)}"', 'a = "${"', 'a = "${ {"'):
            with self.subTest(source=source):
                with self.assertRaises(hcl_parser.Hcl2Error):
                    hcl_parser.HclLexer(source).tokenize()

    def test_template_nesting_budget_is_enforced(self) -> None:
        """Nesting inside one literal is bounded, so pathological input fails cleanly."""
        source = 'a = "' + '${f("' * 4 + '"'
        with self.assertRaisesRegex(hcl_parser.Hcl2Error, "nesting"):
            hcl_parser.HclLexer(source, max_depth=3).tokenize()


class TestLoadsInputNormalization(unittest.TestCase):
    """CRLF and byte-order-mark input must parse exactly like LF input."""

    LF_SOURCE = (
        'resource "google_storage_bucket" "b" {\n'
        '  name = "x"\n'
        "  versioning {\n"
        "    enabled = true\n"
        "  }\n"
        "  script = <<EOT\n"
        "line one\n"
        "EOT\n"
        "}\n"
    )

    def _assert_variants_match_lf(self) -> None:
        """Checks CRLF, BOM, and BOM+CRLF variants against the LF parse."""
        expected = hcl_parser.loads(self.LF_SOURCE)
        self.assertEqual(
            expected["resource"][0]["google_storage_bucket"]["b"]["script"], "line one"
        )
        variants = {
            "crlf": self.LF_SOURCE.replace("\n", "\r\n"),
            "bom": "\ufeff" + self.LF_SOURCE,
            "bom+crlf": "\ufeff" + self.LF_SOURCE.replace("\n", "\r\n"),
        }
        for label, text in variants.items():
            with self.subTest(variant=label):
                self.assertEqual(hcl_parser.loads(text), expected)

    def test_selected_backend(self) -> None:
        """python-hcl2 7.3.1 rejected CRLF and BOM files outright before normalization."""
        self._assert_variants_match_lf()

    def test_in_repo_parser(self) -> None:
        """The in-repo parser rejected a BOM and kept a stray CR in heredoc bodies."""
        with mock.patch.object(hcl_parser, "_EXTERNAL_HCL2", None):
            self._assert_variants_match_lf()

    def test_external_backend_receives_normalized_text(self) -> None:
        """Host-independent check of the contract, with a recording stand-in backend."""
        received: List[str] = []

        def recording_loads(text: str) -> dict:
            received.append(text)
            return {}

        fake = types.SimpleNamespace(loads=recording_loads)
        with mock.patch.object(hcl_parser, "_EXTERNAL_HCL2", fake):
            hcl_parser.loads("\ufeffa = 1\r\nb = 2\r\n")
        self.assertEqual(received, ["a = 1\nb = 2\n"])


class TestLoadsBackendContract(unittest.TestCase):
    """loads() reports every backend problem as Hcl2Error and returns only mappings."""

    def test_non_mapping_backend_output_is_rejected(self) -> None:
        """A non-dict result used to be wrapped as {"data": ...}.

        "data" is the key of Terraform data blocks, so the wrapper could be read as
        data sources instead of failing.
        """
        fake = types.SimpleNamespace(loads=lambda text: ["not", "a", "mapping"])
        with mock.patch.object(hcl_parser, "_EXTERNAL_HCL2", fake):
            with self.assertRaises(hcl_parser.Hcl2Error):
                hcl_parser.loads("a = 1\n")

    def test_backend_exceptions_are_wrapped(self) -> None:
        """Third-party failures surface as Hcl2Error, which LarkError aliases."""

        def failing_loads(text: str) -> dict:
            raise RuntimeError("backend failure")

        fake = types.SimpleNamespace(loads=failing_loads)
        with mock.patch.object(hcl_parser, "_EXTERNAL_HCL2", fake):
            with self.assertRaises(hcl_parser.LarkError) as ctx:
                hcl_parser.loads("a = 1\n")
        self.assertIsInstance(ctx.exception, hcl_parser.Hcl2Error)
        self.assertIsInstance(ctx.exception.__cause__, RuntimeError)

    def test_deep_nesting_raises_hcl2error_on_every_backend(self) -> None:
        """RecursionError must never escape loads(), whichever backend is selected.

        The in-repo parser stops at MAX_HCL_DEPTH. python-hcl2 7.3.1 raises
        RecursionError at this depth, which loads() reports as Hcl2Error.
        """
        source = "a = " + "[" * 5000 + "]" * 5000
        for label, backend in (("selected", hcl_parser._EXTERNAL_HCL2), ("in-repo", None)):
            with self.subTest(backend=label):
                with mock.patch.object(hcl_parser, "_EXTERNAL_HCL2", backend):
                    with self.assertRaises(hcl_parser.Hcl2Error):
                        hcl_parser.loads(source)


class TestHclStreamAndLoadsFacade(unittest.TestCase):
    """Tests over hcl_parser.loads and hcl_parser.load APIs."""

    def test_loads_empty_and_whitespace(self) -> None:
        self.assertEqual(hcl_parser.loads(""), {})
        self.assertEqual(hcl_parser.loads("   \n\t  \n"), {})
        self.assertEqual(hcl_parser.loads("# only comments\n// another comment\n"), {})

    def test_loads_oversize_text_raises(self) -> None:
        oversize = "#" * (hcl_parser.MAX_HCL_BYTES + 1)
        with self.assertRaises(hcl_parser.Hcl2Error):
            hcl_parser.loads(oversize)

    def test_load_fp_valid(self) -> None:
        """The '//' inside the string value must not be read as a comment."""
        stream = io.StringIO('output "endpoint" { value = "https://example.gov" }')
        parsed = hcl_parser.load(stream)
        self.assertEqual(parsed["output"][0]["endpoint"]["value"], "https://example.gov")

    def test_load_fp_oversize_stream_raises_without_unbounded_read(self) -> None:
        """load() asks the stream for at most MAX_HCL_BYTES + 1 characters."""

        class _RecordingStream(io.TextIOBase):
            def __init__(self) -> None:
                super().__init__()
                self.requested: List[Optional[int]] = []

            def read(self, size: Optional[int] = -1) -> str:
                self.requested.append(size)
                if size is None or size < 0:
                    raise AssertionError("load() issued an unbounded read")
                return "#" * size

        stream = _RecordingStream()
        with self.assertRaises(hcl_parser.Hcl2Error):
            hcl_parser.load(stream)
        self.assertEqual(stream.requested, [hcl_parser.MAX_HCL_BYTES + 1])


if __name__ == "__main__":
    unittest.main(verbosity=2)
