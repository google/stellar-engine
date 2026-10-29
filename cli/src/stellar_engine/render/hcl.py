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

"""Emits and reads HCL `terraform.tfvars` files.

`dumps` writes plain data, never expressions, so every string is a quoted
literal and template sequences are escaped. The layout matches what
`terraform fmt` produces, so a rendered file stays unchanged when the
operator formats it and the overwrite check in `render/writer.py` does not
report a spurious edit.
"""

from collections.abc import Mapping, Sequence
import json
import math
import re
from typing import Any

import hcl2

_INDENT = "  "
_LINE_LIMIT = 80
# python-hcl2 8.x reports comments under these keys of the enclosing object.
_COMMENT_KEYS = frozenset({"__comments__", "__inline_comments__"})
_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_-]*$")
# A bare object key that is an HCL keyword parses as that keyword, for
# example `{ for = 1 }` starts a for expression, so these keys stay quoted.
_KEYWORDS = frozenset({"false", "for", "null", "true"})
_ESCAPES = {
    "\\": "\\\\",
    '"': '\\"',
    "\n": "\\n",
    "\r": "\\r",
    "\t": "\\t",
}


def quote(value: str) -> str:
    """Returns an HCL quoted string literal for a plain string.

    Template sequences are escaped as `$${` and `%%{` so Terraform reads
    them literally instead of interpolating them.

    Args:
        value: String to quote.

    Returns:
        The double-quoted literal.
    """
    chars = []
    for char in value:
        if char in _ESCAPES:
            chars.append(_ESCAPES[char])
        elif ord(char) < 0x20 or ord(char) == 0x7F:  # noqa: PLR2004
            chars.append(f"\\u{ord(char):04x}")
        else:
            chars.append(char)
    escaped = "".join(chars).replace("${", "$${").replace("%{", "%%{")
    return f'"{escaped}"'


def unquote(value: Any) -> Any:
    """Converts a string literal as python-hcl2 returns it to plain text.

    python-hcl2 keeps the quotes and the escape sequences of strings and
    quoted object keys. Values that are not quoted literals, such as
    numbers or expressions, are returned unchanged.

    Args:
        value: Value from python-hcl2.

    Returns:
        The unescaped string, or the value unchanged.
    """
    if (
        isinstance(value, str)
        and len(value) >= 2  # noqa: PLR2004
        and value.startswith('"')
        and value.endswith('"')
    ):
        text = json.loads(value)
        return text.replace("$${", "${").replace("%%{", "%{")
    return value


def normalize(data: Any) -> Any:
    """Turns python-hcl2 output into plain data.

    Drops the `__comments__` and `__inline_comments__` entries python-hcl2
    adds and unquotes every string and object key, recursively.

    Args:
        data: Parsed value from python-hcl2.

    Returns:
        The same structure with plain keys and strings.
    """
    if isinstance(data, dict):
        return {
            unquote(key): normalize(value)
            for key, value in data.items()
            if key not in _COMMENT_KEYS
        }
    if isinstance(data, list):
        return [normalize(item) for item in data]
    return unquote(data)


def loads(text: str) -> dict[str, Any]:
    """Parses tfvars text into plain data.

    Args:
        text: HCL source with top-level attributes only.

    Returns:
        Attribute names mapped to plain values, see `normalize`.
    """
    return normalize(hcl2.loads(text))


def _key(key: Any) -> str:
    if not isinstance(key, str):
        raise TypeError(f"HCL object keys must be strings, got {key!r}")
    if _IDENTIFIER_RE.match(key) and key not in _KEYWORDS:
        return key
    return quote(key)


def _is_scalar(value: Any) -> bool:
    return value is None or isinstance(value, str | bool | int | float)


def _scalar(value: Any) -> str:
    # bool first, because bool is a subclass of int.
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError(f"HCL has no literal for {value!r}")
        return repr(value)
    if isinstance(value, str):
        return quote(value)
    raise TypeError(f"Cannot render {type(value).__name__} as HCL")


def _is_sequence(value: Any) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, str | bytes)


def _render(value: Any, depth: int, column: int) -> str:
    """Renders a value whose first line starts at `column`.

    Continuation lines carry their own indentation, and the closing bracket
    sits at `depth`, so the caller only prefixes the first line.
    """
    if isinstance(value, Mapping):
        if not value:
            return "{}"
        lines = ["{", *_body(value, depth + 1), _INDENT * depth + "}"]
        return "\n".join(lines)
    if _is_sequence(value):
        if not value:
            return "[]"
        if all(_is_scalar(item) for item in value):
            inline = "[" + ", ".join(_scalar(item) for item in value) + "]"
            if column + len(inline) <= _LINE_LIMIT:
                return inline
        inner = _INDENT * (depth + 1)
        lines = ["["]
        for item in value:
            rendered = _render(item, depth + 1, len(inner))
            lines.append(f"{inner}{rendered},")
        lines.append(_INDENT * depth + "]")
        return "\n".join(lines)
    return _scalar(value)


def _body(mapping: Mapping[Any, Any], depth: int) -> list[str]:
    """Renders the attributes of an object one level below `depth - 1`.

    `terraform fmt` aligns the `=` signs of consecutive single-line
    attributes. An attribute whose value spans lines is not aligned and ends
    the run, so runs are collected and padded once they close.
    """
    indent = _INDENT * depth
    lines: list[str] = []
    run: list[tuple[str, str]] = []

    def flush():
        width = max((len(key) for key, _ in run), default=0)
        lines.extend(
            f"{indent}{key.ljust(width)} = {text}" for key, text in run
        )
        run.clear()

    for raw_key, value in mapping.items():
        key = _key(raw_key)
        text = _render(value, depth, len(indent) + len(key) + 3)
        if "\n" in text:
            flush()
            lines.append(f"{indent}{key} = {text}")
        else:
            run.append((key, text))
    flush()
    return lines


def _comment_lines(lines: Sequence[str], what: str) -> list[str]:
    result = []
    for line in lines:
        stripped = line.rstrip()
        if not stripped.startswith(("#", "//")) or "\n" in stripped:
            raise ValueError(f"{what} line is not a comment: {line!r}")
        result.append(stripped)
    return result


def dumps(
    values: Mapping[str, Any],
    *,
    comments: Mapping[str, Sequence[str]] | None = None,
    header: Sequence[str] | None = None,
) -> str:
    """Renders top-level attributes as `terraform fmt` canonical HCL.

    Args:
        values: Attribute names mapped to plain data: mappings, lists,
            strings, numbers, booleans and None. Order is kept.
        comments: Comment lines to emit directly above an attribute, keyed
            by attribute name. Each line starts with `#` or `//`. Keys
            without a matching attribute are ignored.
        header: Comment lines emitted at the top of the file.

    Returns:
        The HCL text, ending with a newline.

    Raises:
        ValueError: If an attribute name is not an HCL identifier, a
            comment line is not a comment, or a float is not finite.
        TypeError: If a value has a type HCL cannot represent.
    """
    comments = comments or {}
    blocks = []
    if header:
        blocks.append("\n".join(_comment_lines(header, "Header")))
    for name, value in values.items():
        if not isinstance(name, str) or not _IDENTIFIER_RE.match(name):
            raise ValueError(f"Not a valid HCL attribute name: {name!r}")
        lines = _comment_lines(comments.get(name, ()), f"Comment for {name}")
        lines.append(f"{name} = {_render(value, 0, len(name) + 3)}")
        blocks.append("\n".join(lines))
    if not blocks:
        return ""
    return "\n\n".join(blocks) + "\n"
