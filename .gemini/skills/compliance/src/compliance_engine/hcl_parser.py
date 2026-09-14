#!/usr/bin/env python3
"""Hardened HCL2 (Terraform) parsing facade for the compliance engine.

Terraform sources are untrusted input from the perspective of this engine: they
are read from whatever workspace the operator points at. This module therefore
treats HCL parsing as a trust boundary and enforces explicit resource budgets.

Backend selection is explicit and fails closed:

1. If the genuine ``python-hcl2`` distribution is installed, it is used and
   reported via :data:`BACKEND`.
2. Otherwise the in-repo :func:`loads` recursive-descent parser is used.

Hardening applied to the in-repo parser:

* **CWE-674 (Uncontrolled Recursion)** - nesting depth is explicitly bounded, so
  a document such as ``a = [[[[[...`` raises :class:`Hcl2Error` instead of
  exhausting the interpreter stack.
* **CWE-400 (Uncontrolled Resource Consumption)** - document size and total token
  count are bounded, and an unterminated block comment or heredoc is reported as
  a syntax error rather than silently consuming the remainder of the file.
* **Quadratic parsing** - the lexer scans with anchored regular expressions over
  the original buffer (``pattern.match(text, pos)``) and never slices or
  concatenates per character, so tokenization is linear in document size.

.. note::
   This module is intentionally **not** named ``hcl2``. An earlier revision
   vendored a package literally named ``hcl2`` inside ``scripts/``, which silently
   shadowed the real PyPI distribution on ``sys.path`` and made the documented
   ``pip install python-hcl2`` a no-op.
"""

from __future__ import annotations

from contextlib import contextmanager
import logging
import os
from pathlib import Path
import re
import textwrap
from typing import Any, Dict, Final, IO, Iterator, List, Optional, Pattern

logger = logging.getLogger(__name__)

__all__ = [
    "BACKEND",
    "Hcl2Error",
    "MAX_HCL_BYTES",
    "MAX_HCL_DEPTH",
    "MAX_HCL_TOKENS",
    "Token",
    "load",
    "loads",
]


# ---------------------------------------------------------------------------
# Resource limits
# ---------------------------------------------------------------------------

_DEFAULT_MAX_HCL_BYTES: Final[int] = 16 * 1024 * 1024  # 16 MiB
_ABSOLUTE_MAX_HCL_BYTES: Final[int] = 128 * 1024 * 1024
_DEFAULT_MAX_HCL_DEPTH: Final[int] = 128
_ABSOLUTE_MAX_HCL_DEPTH: Final[int] = 512
_DEFAULT_MAX_HCL_TOKENS: Final[int] = 4_000_000
_ABSOLUTE_MAX_HCL_TOKENS: Final[int] = 20_000_000


def _bounded_int_from_env(env_var: str, default: int, ceiling: int) -> int:
    """Reads a positive integer tuning knob from the environment, clamped to a ceiling.

    Args:
        env_var: Name of the environment variable to consult.
        default: Value used when the variable is unset or malformed.
        ceiling: Inclusive maximum; larger configured values are clamped down.

    Returns:
        A positive integer no greater than ``ceiling``.
    """
    raw = os.environ.get(env_var, "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError:
        logger.warning("Ignoring non-integer %s=%r; using default %d", env_var, raw, default)
        return default
    if value <= 0:
        logger.warning("Ignoring non-positive %s=%d; using default %d", env_var, value, default)
        return default
    return min(value, ceiling)


MAX_HCL_BYTES: Final[int] = _bounded_int_from_env(
    "COMPLIANCE_MAX_HCL_BYTES", _DEFAULT_MAX_HCL_BYTES, _ABSOLUTE_MAX_HCL_BYTES
)
MAX_HCL_DEPTH: Final[int] = _bounded_int_from_env(
    "COMPLIANCE_MAX_HCL_DEPTH", _DEFAULT_MAX_HCL_DEPTH, _ABSOLUTE_MAX_HCL_DEPTH
)
MAX_HCL_TOKENS: Final[int] = _bounded_int_from_env(
    "COMPLIANCE_MAX_HCL_TOKENS", _DEFAULT_MAX_HCL_TOKENS, _ABSOLUTE_MAX_HCL_TOKENS
)


class Hcl2Error(ValueError):
    """Raised when HCL input is syntactically invalid or exceeds a resource budget."""


# ``python-hcl2`` surfaces parse failures as ``lark.LarkError``. Callers catch
# ``LarkError`` generically, so alias it to the local error type when the real
# library is unavailable.
LarkError = Hcl2Error


# ---------------------------------------------------------------------------
# Lexer
# ---------------------------------------------------------------------------

# Anchored patterns are matched against the original buffer at an offset, which
# avoids the O(n^2) behavior of repeatedly slicing ``text[pos:]``.
_RE_WHITESPACE: Final[Pattern[str]] = re.compile(r"[ \t\r\n]+")
_RE_LINE_COMMENT: Final[Pattern[str]] = re.compile(r"(?:#|//)[^\n]*")
_RE_NUMBER: Final[Pattern[str]] = re.compile(r"[+-]?[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?")
_RE_IDENTIFIER: Final[Pattern[str]] = re.compile(r"[A-Za-z0-9_.$-]+")
_RE_HEREDOC_MARKER: Final[Pattern[str]] = re.compile(r"[A-Za-z0-9_]+")

_PUNCTUATION: Final[frozenset] = frozenset("{}[]=(),:?")
_IDENTIFIER_START: Final[frozenset] = frozenset("_-.$")

_STRING_ESCAPES: Final[Dict[str, str]] = {
    '"': '"',
    "\\": "\\",
    "n": "\n",
    "r": "\r",
    "t": "\t",
}


class Token:
    """A single lexical token with its source position.

    Attributes:
        type: Token category (for example ``STRING``, ``NUMBER``, ``IDENTIFIER``,
            or a literal punctuation character).
        value: Decoded token value.
        line: 1-based source line where the token starts.
        col: 1-based source column where the token starts.
    """

    __slots__ = ("type", "value", "line", "col")

    def __init__(self, type_: str, value: Any, line: int, col: int) -> None:
        """Initializes the token.

        Args:
            type_: Token category.
            value: Decoded token value.
            line: 1-based source line.
            col: 1-based source column.
        """
        self.type = type_
        self.value = value
        self.line = line
        self.col = col

    def __repr__(self) -> str:
        """Returns an unambiguous debugging representation of the token."""
        return f"Token({self.type}, {self.value!r}, line={self.line}, col={self.col})"


class HclLexer:
    """Converts HCL2 source text into a bounded, flat list of tokens."""

    def __init__(self, text: str, max_tokens: int = MAX_HCL_TOKENS) -> None:
        """Initializes the lexer.

        Args:
            text: Raw HCL2 source text.
            max_tokens: Maximum number of tokens permitted before aborting.
        """
        self.text = text
        self.pos = 0
        self.len = len(text)
        self.line = 1
        self.col = 1
        self.max_tokens = max_tokens

    def _peek(self, offset: int = 0) -> str:
        """Returns the character at ``pos + offset`` or an empty string at EOF."""
        idx = self.pos + offset
        return self.text[idx] if idx < self.len else ""

    def _advance(self, count: int = 1) -> None:
        """Advances the cursor ``count`` characters, maintaining line/column state.

        Args:
            count: Number of characters to consume.
        """
        end = min(self.pos + count, self.len)
        segment = self.text[self.pos:end]
        newlines = segment.count("\n")
        if newlines:
            self.line += newlines
            self.col = len(segment) - segment.rfind("\n")
        else:
            self.col += len(segment)
        self.pos = end

    def tokenize(self) -> List[Token]:
        """Tokenizes the entire document.

        Returns:
            List of tokens terminated by a synthetic ``EOF`` token.

        Raises:
            Hcl2Error: On unterminated literals/comments or token budget overflow.
        """
        tokens: List[Token] = []
        while self.pos < self.len:
            if len(tokens) >= self.max_tokens:
                raise Hcl2Error(
                    f"HCL document exceeded the maximum token budget of {self.max_tokens}"
                )
            char = self.text[self.pos]

            whitespace = _RE_WHITESPACE.match(self.text, self.pos)
            if whitespace:
                self._advance(whitespace.end() - self.pos)
                continue

            line_comment = _RE_LINE_COMMENT.match(self.text, self.pos)
            if line_comment:
                self._advance(line_comment.end() - self.pos)
                continue

            if char == "/" and self._peek(1) == "*":
                self._consume_block_comment()
                continue

            if char == "<" and self._peek(1) == "<":
                tokens.append(self._tokenize_heredoc())
                continue

            if char in _PUNCTUATION:
                tokens.append(Token(char, char, self.line, self.col))
                self._advance()
                continue

            if char == '"':
                tokens.append(self._tokenize_string())
                continue

            if char.isdigit() or (char in "+-" and self._peek(1).isdigit()):
                number = self._tokenize_number()
                if number is not None:
                    tokens.append(number)
                    continue

            if char.isalpha() or char in _IDENTIFIER_START:
                tokens.append(self._tokenize_identifier())
                continue

            # Unrecognized punctuation is emitted verbatim so the parser can
            # produce a precise diagnostic rather than the lexer guessing.
            tokens.append(Token(char, char, self.line, self.col))
            self._advance()

        tokens.append(Token("EOF", "", self.line, self.col))
        return tokens

    def _consume_block_comment(self) -> None:
        """Consumes a ``/* ... */`` block comment.

        Raises:
            Hcl2Error: If the comment is never terminated.
        """
        start_line, start_col = self.line, self.col
        terminator = self.text.find("*/", self.pos + 2)
        if terminator == -1:
            raise Hcl2Error(
                f"Unterminated block comment starting at line {start_line}, col {start_col}"
            )
        self._advance((terminator + 2) - self.pos)

    def _tokenize_heredoc(self) -> Token:
        """Tokenizes a ``<<MARKER`` / ``<<-MARKER`` heredoc literal.

        Returns:
            A ``STRING`` token holding the heredoc body.

        Raises:
            Hcl2Error: If the marker is malformed or the heredoc is unterminated.
        """
        start_line, start_col = self.line, self.col
        self._advance(2)

        strip_indent = self._peek() == "-"
        if strip_indent:
            self._advance()

        marker_match = _RE_HEREDOC_MARKER.match(self.text, self.pos)
        if not marker_match:
            raise Hcl2Error(f"Malformed heredoc marker at line {start_line}, col {start_col}")
        marker = marker_match.group(0)
        self._advance(marker_match.end() - self.pos)

        # Skip any trailing content on the opening line.
        newline_idx = self.text.find("\n", self.pos)
        if newline_idx == -1:
            raise Hcl2Error(f"Unclosed heredoc {marker} started at line {start_line}")
        self._advance((newline_idx + 1) - self.pos)

        content_lines: List[str] = []
        while self.pos < self.len:
            line_end = self.text.find("\n", self.pos)
            if line_end == -1:
                line_str = self.text[self.pos:self.len]
                consumed = self.len - self.pos
            else:
                line_str = self.text[self.pos:line_end]
                consumed = (line_end + 1) - self.pos
            self._advance(consumed)

            if line_str.strip() == marker:
                body = "\n".join(content_lines)
                if strip_indent:
                    body = textwrap.dedent(body)
                return Token("STRING", body, start_line, start_col)
            content_lines.append(line_str)

        raise Hcl2Error(f"Unclosed heredoc {marker} started at line {start_line}")

    def _tokenize_string(self) -> Token:
        """Tokenizes a double-quoted string literal, resolving standard escapes.

        Returns:
            A ``STRING`` token.

        Raises:
            Hcl2Error: If the literal is unterminated.
        """
        start_line, start_col = self.line, self.col
        self._advance()
        parts: List[str] = []
        while self.pos < self.len:
            char = self.text[self.pos]
            if char == '"':
                self._advance()
                return Token("STRING", "".join(parts), start_line, start_col)
            if char == "\\":
                self._advance()
                if self.pos >= self.len:
                    break
                escaped = self.text[self.pos]
                parts.append(_STRING_ESCAPES.get(escaped, "\\" + escaped))
                self._advance()
                continue
            # Consume the whole run of ordinary characters at once.
            next_special = self.pos
            while next_special < self.len and self.text[next_special] not in ('"', "\\"):
                next_special += 1
            parts.append(self.text[self.pos:next_special])
            self._advance(next_special - self.pos)

        raise Hcl2Error(
            f"Unterminated string literal starting at line {start_line}, col {start_col}"
        )

    def _tokenize_number(self) -> Optional[Token]:
        """Tokenizes an integer, decimal, or scientific-notation number literal.

        Returns:
            A ``NUMBER`` token, or None if the cursor is not on a number.
        """
        start_line, start_col = self.line, self.col
        match = _RE_NUMBER.match(self.text, self.pos)
        if not match:
            return None
        raw = match.group(0)
        self._advance(len(raw))
        if any(marker in raw for marker in (".", "e", "E")):
            return Token("NUMBER", float(raw), start_line, start_col)
        return Token("NUMBER", int(raw), start_line, start_col)

    def _tokenize_identifier(self) -> Token:
        """Tokenizes a bareword identifier, keyword, or traversal reference.

        Returns:
            A ``BOOLEAN``, ``NULL``, or ``IDENTIFIER`` token.
        """
        start_line, start_col = self.line, self.col
        match = _RE_IDENTIFIER.match(self.text, self.pos)
        if not match:
            # Single non-alphanumeric identifier-start character (for example a
            # lone '$'); emit it verbatim so the parser can diagnose it.
            char = self.text[self.pos]
            self._advance()
            return Token("IDENTIFIER", char, start_line, start_col)
        identifier = match.group(0)
        self._advance(len(identifier))

        if identifier == "true":
            return Token("BOOLEAN", True, start_line, start_col)
        if identifier == "false":
            return Token("BOOLEAN", False, start_line, start_col)
        if identifier == "null":
            return Token("NULL", None, start_line, start_col)
        return Token("IDENTIFIER", identifier, start_line, start_col)


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------


class HclParser:
    """Recursive-descent HCL2 parser with an explicit nesting-depth budget."""

    def __init__(self, tokens: List[Token], max_depth: int = MAX_HCL_DEPTH) -> None:
        """Initializes the parser.

        Args:
            tokens: Token stream produced by :class:`HclLexer`.
            max_depth: Maximum permitted structural nesting depth.
        """
        self.tokens = tokens
        self.pos = 0
        self.max_depth = max_depth
        self._depth = 0

    def current(self) -> Token:
        """Returns the token at the cursor, or the terminal ``EOF`` token."""
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return self.tokens[-1]

    def peek(self, offset: int = 1) -> Token:
        """Returns the token ``offset`` positions ahead, clamped to ``EOF``.

        Args:
            offset: Lookahead distance in tokens.

        Returns:
            The looked-ahead token.
        """
        idx = self.pos + offset
        if idx < len(self.tokens):
            return self.tokens[idx]
        return self.tokens[-1]

    def consume(self, expected_type: Optional[str] = None) -> Token:
        """Consumes and returns the current token, optionally asserting its type.

        Args:
            expected_type: Required token type, or None to accept any token.

        Returns:
            The consumed token.

        Raises:
            Hcl2Error: If ``expected_type`` is set and does not match.
        """
        tok = self.current()
        if expected_type is not None and tok.type != expected_type:
            raise Hcl2Error(
                f"Expected {expected_type} but got {tok.type} ({tok.value!r}) "
                f"at line {tok.line}, col {tok.col}"
            )
        self.pos += 1
        return tok

    def _enter(self, tok: Token) -> None:
        """Increments the nesting depth counter, enforcing the depth budget.

        Args:
            tok: Token at which nesting is being entered, used for diagnostics.

        Raises:
            Hcl2Error: If the maximum nesting depth would be exceeded.
        """
        self._depth += 1
        if self._depth > self.max_depth:
            raise Hcl2Error(
                f"HCL nesting depth exceeded the maximum of {self.max_depth} "
                f"at line {tok.line}, col {tok.col}"
            )

    def _exit(self) -> None:
        """Decrements the nesting depth counter."""
        self._depth -= 1

    def parse(self) -> Dict[str, Any]:
        """Parses the full token stream into a python-hcl2 compatible dictionary.

        Returns:
            The parsed document body.

        Raises:
            Hcl2Error: On any syntax error or budget violation.
        """
        result: Dict[str, Any] = {}
        while self.current().type != "EOF":
            before = self.pos
            self._parse_statement(result)
            if self.pos == before:
                # Defensive: guarantees termination even if a future edit adds a
                # production that neither consumes a token nor raises.
                tok = self.current()
                raise Hcl2Error(
                    f"Parser made no progress at token {tok.type} ({tok.value!r}) "
                    f"on line {tok.line}, col {tok.col}"
                )
        return result

    def _parse_statement(self, container: Dict[str, Any]) -> None:
        """Parses a single top-level attribute assignment or block.

        Args:
            container: Dictionary receiving the parsed statement.

        Raises:
            Hcl2Error: On any syntax error.
        """
        tok = self.current()

        if tok.type not in ("IDENTIFIER", "STRING"):
            if tok.type == "}":
                self.consume("}")
                return
            raise Hcl2Error(f"Unexpected token {tok.value!r} at line {tok.line}, col {tok.col}")

        # Attribute assignment: IDENTIFIER = VALUE
        if self.peek(1).type in ("=", ":"):
            key = tok.value
            self.consume()
            self.consume()
            container[key] = self._parse_expression()
            if self.current().type == ",":
                self.consume(",")
            return

        # Block: IDENTIFIER [LABEL...] { ... }
        block_type = tok.value
        self.consume()
        labels: List[Any] = []
        while self.current().type in ("IDENTIFIER", "STRING"):
            labels.append(self.current().value)
            self.consume()

        if self.current().type == "{":
            self._enter(tok)
            try:
                self.consume("{")
                block_body = self._parse_block_body()
                self.consume("}")
            finally:
                self._exit()
            self._store_block(container, block_type, labels, block_body)
            return

        if self.current().type == "=":
            self.consume("=")
            container[block_type] = self._parse_expression()
            return

        raise Hcl2Error(
            f"Unexpected token {self.current().value!r} after {block_type!r} at line {tok.line}"
        )

    def _store_block(
        self,
        container: Dict[str, Any],
        block_type: str,
        labels: List[Any],
        block_body: Dict[str, Any],
    ) -> None:
        """Stores a parsed block using python-hcl2's canonical output shape.

        Args:
            container: Dictionary receiving the block.
            block_type: Block keyword (for example ``resource`` or ``module``).
            labels: Block labels in source order.
            block_body: Parsed block body.
        """
        if block_type in ("resource", "data"):
            res_type = labels[0] if labels else "unknown"
            res_name = labels[1] if len(labels) > 1 else "default"
            container.setdefault(block_type, []).append({res_type: {res_name: block_body}})
            return
        if block_type in ("module", "variable", "output", "provider"):
            name = labels[0] if labels else "default"
            container.setdefault(block_type, []).append({name: block_body})
            return
        if block_type in ("terraform", "locals"):
            container.setdefault(block_type, []).append(block_body)
            return

        nested: Any = block_body
        for label in reversed(labels):
            nested = {label: nested}
        self._add_nested_entry(container, block_type, nested)

    def _parse_block_body(self) -> Dict[str, Any]:
        """Parses the interior of a ``{ ... }`` block.

        Returns:
            Dictionary of attributes and nested blocks.

        Raises:
            Hcl2Error: On any syntax error.
        """
        body: Dict[str, Any] = {}
        while self.current().type not in ("}", "EOF"):
            tok = self.current()

            if tok.type == ",":
                self.consume(",")
                continue

            if tok.type not in ("IDENTIFIER", "STRING"):
                raise Hcl2Error(
                    f"Unexpected token {tok.value!r} in block body at line {tok.line}"
                )

            if self.peek(1).type in ("=", ":"):
                key = tok.value
                self.consume()
                self.consume()
                self._add_attribute(body, key, self._parse_expression())
                if self.current().type == ",":
                    self.consume(",")
                continue

            block_name = tok.value
            self.consume()
            labels: List[Any] = []
            while self.current().type in ("IDENTIFIER", "STRING"):
                labels.append(self.current().value)
                self.consume()

            if self.current().type != "{":
                raise Hcl2Error(
                    f"Unexpected token {self.current().value!r} after {block_name!r} "
                    f"at line {tok.line}"
                )

            self._enter(tok)
            try:
                self.consume("{")
                child_body = self._parse_block_body()
                self.consume("}")
            finally:
                self._exit()

            nested: Any = child_body
            for label in reversed(labels):
                nested = {label: nested}
            self._add_nested_entry(body, block_name, nested)

        return body

    @staticmethod
    def _add_attribute(container: Dict[str, Any], key: str, val: Any) -> None:
        """Adds an attribute, promoting duplicates to a list.

        Args:
            container: Dictionary receiving the attribute.
            key: Attribute name.
            val: Attribute value.
        """
        if key not in container:
            container[key] = val
            return
        existing = container[key]
        if isinstance(existing, list):
            existing.append(val)
        else:
            container[key] = [existing, val]

    @staticmethod
    def _add_nested_entry(container: Dict[str, Any], key: str, entry: Any) -> None:
        """Appends a nested block entry, always modeling the slot as a list.

        Args:
            container: Dictionary receiving the block.
            key: Block name.
            entry: Parsed block payload.
        """
        if key not in container:
            container[key] = [entry]
            return
        existing = container[key]
        if isinstance(existing, list):
            existing.append(entry)
        else:
            container[key] = [existing, entry]

    def _parse_expression(self) -> Any:
        """Parses an expression, including binary operators and ternary conditionals."""
        val = self._parse_value()

        # Handle chained binary/comparison operators (&&, ||, ==, !=, +, -, <, >)
        while self.current().type in ("&", "|", "+", "-", "=", "!", "<", ">"):
            op = str(self.current().value)
            self.consume()
            if self.current().type in ("&", "|", "=", ">"):
                op += str(self.current().value)
                self.consume()
            right = self._parse_value()
            val = f"{val} {op} {right}"

        # Handle ternary condition: cond ? true_val : false_val
        if self.current().type == "?":
            self.consume("?")
            true_val = self._parse_expression()
            if self.current().type == ":":
                self.consume(":")
                false_val = self._parse_expression()
            else:
                false_val = ""
            val = f"{val} ? {true_val} : {false_val}"

        return val

    def _parse_value(self) -> Any:
        """Parses a single HCL value (scalar, tuple, object, or expression).

        Returns:
            The parsed Python value.

        Raises:
            Hcl2Error: On any syntax error or depth budget violation.
        """
        tok = self.current()

        if tok.type in ("STRING", "NUMBER", "BOOLEAN"):
            self.consume()
            return tok.value

        if tok.type == "NULL":
            self.consume()
            return None

        if tok.type == "!":
            self.consume("!")
            val = self._parse_value()
            return f"!{val}"

        if tok.type == "(":
            self._enter(tok)
            try:
                self.consume("(")
                val = self._parse_expression()
                self.consume(")")
            finally:
                self._exit()
            return val

        if tok.type == "IDENTIFIER":
            # Barewords are traversal references (var.x, local.y) preserved verbatim.
            ident = tok.value
            self.consume()
            if self.current().type == "(":
                # Function call expression: ident(...)
                self._enter(tok)
                try:
                    self.consume("(")
                    args: List[Any] = []
                    while self.current().type not in (")", "EOF"):
                        args.append(self._parse_expression())
                        if self.current().type == ",":
                            self.consume(",")
                    self.consume(")")
                finally:
                    self._exit()
                return f"{ident}({', '.join(str(a) for a in args)})"
            return ident

        if tok.type == "[":
            self._enter(tok)
            try:
                self.consume("[")
                if self.current().type == "IDENTIFIER" and self.current().value == "for":
                    comp_parts = ["for"]
                    self.consume()
                    inner_depth = 1
                    while self.current().type != "EOF":
                        if self.current().type == "[":
                            inner_depth += 1
                        elif self.current().type == "]":
                            inner_depth -= 1
                            if inner_depth == 0:
                                self.consume("]")
                                break
                        comp_parts.append(str(self.current().value))
                        self.consume()
                    return f"[{' '.join(comp_parts)}]"
                items: List[Any] = []
                while self.current().type not in ("]", "EOF"):
                    items.append(self._parse_expression())
                    if self.current().type == ",":
                        self.consume(",")
                self.consume("]")
            finally:
                self._exit()
            return items

        if tok.type == "{":
            self._enter(tok)
            try:
                obj = self._parse_object()
            finally:
                self._exit()
            return obj

        raise Hcl2Error(
            f"Unexpected token for value: {tok.type} ({tok.value!r}) at line {tok.line}"
        )

    def _parse_object(self) -> Dict[str, Any]:
        """Parses an object/map literal delimited by braces.

        Returns:
            The parsed mapping.

        Raises:
            Hcl2Error: On any syntax error.
        """
        self.consume("{")
        if self.current().type == "IDENTIFIER" and self.current().value == "for":
            comp_parts = ["for"]
            self.consume()
            inner_depth = 1
            while self.current().type != "EOF":
                if self.current().type == "{":
                    inner_depth += 1
                elif self.current().type == "}":
                    inner_depth -= 1
                    if inner_depth == 0:
                        self.consume("}")
                        break
                comp_parts.append(str(self.current().value))
                self.consume()
            return {"_comprehension": " ".join(comp_parts)}

        obj: Dict[str, Any] = {}
        while self.current().type not in ("}", "EOF"):
            key_tok = self.current()

            if key_tok.type == ",":
                self.consume(",")
                continue

            if key_tok.type not in ("IDENTIFIER", "STRING"):
                raise Hcl2Error(
                    f"Unexpected token in map: {key_tok.value!r} at line {key_tok.line}"
                )

            self.consume()
            key = key_tok.value

            if self.current().type in ("=", ":"):
                self.consume()
                obj[key] = self._parse_expression()
            elif self.current().type == "{":
                self._enter(key_tok)
                try:
                    self.consume("{")
                    child_body = self._parse_block_body()
                    self.consume("}")
                finally:
                    self._exit()
                self._add_nested_entry(obj, key, child_body)
            else:
                raise Hcl2Error(
                    f"Expected '=' or ':' after key {key!r} in map at line {key_tok.line}"
                )

            if self.current().type == ",":
                self.consume(",")

        self.consume("}")
        return obj


# ---------------------------------------------------------------------------
# Backend selection and public API
# ---------------------------------------------------------------------------


#: Canary document used to verify that an external backend produces the canonical
#: python-hcl2 output shape this engine's consumers depend on.
_CANARY_SOURCE: Final[str] = 'resource "t" "n" {\n  name = "x"\n}\n'
_CANARY_EXPECTED: Final[Dict[str, Any]] = {"resource": [{"t": {"n": {"name": "x"}}}]}


#: Grammar-cache files that lark-based HCL backends drop into the current working
#: directory on first parse.
_PARSER_CACHE_GLOB: Final[str] = ".lark_cache_*"


@contextmanager
def _without_probe_cache_residue() -> Iterator[None]:
    """Removes parser-cache files created while probing a candidate backend.

    lark-based ``hcl2`` distributions serialize their compiled grammar into the
    *current working directory* on first parse. The shape canary below is a
    diagnostic the engine runs for its own benefit -- and usually ends in the
    backend being rejected -- so it must not leave a stray dotfile behind in
    whatever directory the operator happened to invoke the tool from.

    Only files that did not exist before the probe are removed, so a cache
    belonging to the operator's own tooling is never touched.

    Yields:
        None, for the duration of the probe.
    """
    cwd = Path.cwd()
    try:
        pre_existing = {entry.name for entry in cwd.glob(_PARSER_CACHE_GLOB)}
    except OSError as err:
        logger.debug("Could not enumerate parser cache files in '%s': %s", cwd, err)
        pre_existing = set()
    try:
        yield
    finally:
        # NOTE: this block must not contain a `return`. Returning from a `finally`
        # discards any exception propagating out of the `yield`, which would silently
        # mask a genuine backend failure as a successful probe.
        try:
            created = [
                entry for entry in cwd.glob(_PARSER_CACHE_GLOB)
                if entry.name not in pre_existing
            ]
        except OSError as err:
            logger.debug("Could not enumerate parser cache files in '%s': %s", cwd, err)
            created = []
        for stray in created:
            try:
                stray.unlink()
            except OSError as err:
                logger.debug("Could not remove parser cache residue '%s': %s", stray, err)


def _classify_incompatible_backend(canary: Any) -> str:
    """Fingerprints a rejected backend from its canary output.

    Several distributions publish under the ``hcl2`` import name with mutually
    incompatible output shapes. Naming the specific one that is installed turns an
    opaque rejection into an actionable diagnostic.

    Args:
        canary: Whatever the candidate backend returned for :data:`_CANARY_SOURCE`.

    Returns:
        A human-readable identification of the distribution, or a generic
        description when the shape matches no known fingerprint.
    """
    try:
        body = canary["resource"][0]
    except (KeyError, IndexError, TypeError):
        return "unrecognized distribution (canary output is not a Terraform resource map)"

    if not isinstance(body, dict) or not body:
        return "unrecognized distribution (empty resource body)"

    label = next(iter(body))

    # python-hcl2 8.x stops stripping the quote characters from block labels and
    # string values, and tags every block body with '__is_block__'.
    if isinstance(label, str) and label.startswith('"'):
        return (
            "python-hcl2 8.x, which retains quote characters on block labels and string "
            "values and injects a synthetic '__is_block__' key. The compliance engine "
            "requires the 7.x output shape"
        )

    inner = body.get(label)
    attrs = inner.get(next(iter(inner))) if isinstance(inner, dict) and inner else None
    if isinstance(attrs, dict):
        if "__start_line__" in attrs or "__end_line__" in attrs:
            return (
                "the 'bc-python-hcl2' fork vendored by checkov, which wraps every scalar "
                "attribute in a one-element list and injects synthetic "
                "'__start_line__' / '__end_line__' keys"
            )
        if any(isinstance(v, list) and len(v) == 1 for v in attrs.values()):
            return (
                "a fork that wraps every scalar attribute in a one-element list "
                "(pre-3.0 python-hcl2 output shape)"
            )

    return "unrecognized distribution with a non-canonical output shape"


def _load_hcl2_backend() -> Optional[Any]:
    """Imports and *verifies* an external ``hcl2`` backend before trusting it.

    Presence of a module named ``hcl2`` is not sufficient evidence that it is the
    genuine ``python-hcl2`` distribution. In practice several incompatible forks ship
    under that import name - most commonly ``bc-python-hcl2``, which is vendored by
    checkov and which returns a materially different structure: every attribute value
    is wrapped in a list (``{"name": ["x"]}`` rather than ``{"name": "x"}``) and
    synthetic ``__start_line__`` / ``__end_line__`` keys are injected into every block.

    Silently delegating to such a fork corrupts the extracted system inventory: every
    scalar attribute becomes a one-element list, so downstream code that reads
    ``bucket["name"]`` records the string ``"['x']"`` into the SSP. Because these forks
    are typically reachable only when an unrelated tool is installed, the corruption is
    environment-dependent and would not reproduce on a reviewer's machine.

    A backend is therefore accepted only if a canary document round-trips to the exact
    canonical shape. Anything else is rejected in favor of the in-repo parser.

    Returns:
        The verified ``hcl2`` module, or None when unavailable, incomplete, or
        shape-incompatible.
    """
    with _without_probe_cache_residue():
        try:
            import hcl2 as external_hcl2
        except ImportError:
            return None

        if not hasattr(external_hcl2, "loads"):
            logger.warning(
                "Module named 'hcl2' at %s does not expose loads(); using the in-repo "
                "hardened parser.",
                getattr(external_hcl2, "__file__", "<unknown>"),
            )
            return None

        try:
            canary = external_hcl2.loads(_CANARY_SOURCE)
        except Exception as err:  # noqa: BLE001 - any failure disqualifies the backend
            logger.warning(
                "External 'hcl2' backend at %s failed the canary parse (%s); using the "
                "in-repo hardened parser.",
                getattr(external_hcl2, "__file__", "<unknown>"),
                err,
            )
            return None

    if canary != _CANARY_EXPECTED:
        logger.warning(
            "External 'hcl2' backend at %s is shape-incompatible and has been REFUSED: %s\n"
            "  canary produced: %r\n"
            "  canary expected: %r\n"
            "Falling back to the in-repo hardened parser, which does not implement "
            "Terraform expression syntax (function calls, unary/binary operators, 'for' "
            "comprehensions). Files it cannot read are recorded in the "
            "'unparsed_terraform_files' inventory ledger and reported as a CA-2/RA-5 "
            "coverage gap, but they stay outside the assessed boundary. To restore full "
            "coverage install the supported backend: "
            "pip install 'python-hcl2==7.3.1'",
            getattr(external_hcl2, "__file__", "<unknown>"),
            _classify_incompatible_backend(canary),
            canary,
            _CANARY_EXPECTED,
        )
        return None

    logger.debug(
        "Verified external hcl2 backend at %s", getattr(external_hcl2, "__file__", "<unknown>")
    )
    return external_hcl2


_EXTERNAL_HCL2 = _load_hcl2_backend()

BACKEND: Final[str] = "python-hcl2" if _EXTERNAL_HCL2 is not None else "hcl_parser.HclParser"

if _EXTERNAL_HCL2 is not None:  # pragma: no cover - depends on optional dependency
    _external_lark_error = getattr(_EXTERNAL_HCL2, "LarkError", None)
    if isinstance(_external_lark_error, type) and issubclass(_external_lark_error, Exception):
        LarkError = _external_lark_error


def loads(text: str) -> Dict[str, Any]:
    """Parses HCL2 source text into a dictionary.

    Args:
        text: Raw HCL2 document text.

    Returns:
        Parsed document body; an empty dict for blank input.

    Raises:
        Hcl2Error: If the document is invalid or exceeds a configured resource budget.
    """
    if not text or not text.strip():
        return {}
    if len(text) > MAX_HCL_BYTES:
        raise Hcl2Error(
            f"HCL document of {len(text)} characters exceeds the maximum of {MAX_HCL_BYTES}"
        )

    if _EXTERNAL_HCL2 is not None:  # pragma: no cover - depends on optional dependency
        try:
            parsed = _EXTERNAL_HCL2.loads(text)
        except Exception as err:  # noqa: BLE001 - normalize third-party error taxonomy
            raise Hcl2Error(f"python-hcl2 failed to parse document: {err}") from err
        return parsed if isinstance(parsed, dict) else {"data": parsed}

    tokens = HclLexer(text).tokenize()
    return HclParser(tokens).parse()


def load(fp: IO[str]) -> Dict[str, Any]:
    """Parses HCL2 from an open text stream.

    Args:
        fp: Readable text stream positioned at the start of an HCL2 document.

    Returns:
        Parsed document body.

    Raises:
        Hcl2Error: If the document is invalid or exceeds a configured resource budget.
    """
    # Read one byte past the budget so oversize input is rejected without
    # materializing an arbitrarily large string.
    text = fp.read(MAX_HCL_BYTES + 1)
    if text is not None and len(text) > MAX_HCL_BYTES:
        raise Hcl2Error(f"HCL stream exceeds the maximum of {MAX_HCL_BYTES} characters")
    return loads(text or "")


logger.debug("hcl_parser initialized with backend %s", BACKEND)
