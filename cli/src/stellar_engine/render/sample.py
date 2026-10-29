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

"""Reads a stage `terraform.tfvars.sample` file.

Rendered tfvars start from the sample so they keep its key order and the
guidance comments the DDG relies on. python-hcl2 returns comments as one
flat list without positions, so the comment blocks are recovered from the
text instead.
"""

from collections.abc import Iterator
import dataclasses
import pathlib
import re
from typing import Any

import hcl2

from stellar_engine.render import hcl

_ASSIGNMENT_RE = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_-]*)\s*=")
# Optional keys appear as commented-out assignments, for example
# `# kms_protection_level = "HSM"`. Prose such as `# logging_bucket_retention
# days; ...` does not match because a `=` must follow the name.
_COMMENTED_ASSIGNMENT_RE = re.compile(r"^\s*#\s*([a-z_][a-z0-9_]*)\s*=(.*)$")
_COMMENT_PREFIXES = ("#", "//")


@dataclasses.dataclass(frozen=True)
class Sample:
    """Contents of a tfvars sample.

    Attributes:
        values: Parsed top-level values with plain strings and keys.
        order: Top-level keys in file order, including commented-out keys
            that have no entry in `values`.
        comments: Comment lines directly above each key in `order`, empty
            when the key has none.
    """

    values: dict[str, Any]
    order: list[str]
    comments: dict[str, list[str]]


class _DepthScanner:
    """Tracks bracket nesting across lines, skipping strings and comments.

    Heredocs do not occur in tfvars samples and are not handled.
    """

    def __init__(self):
        self.depth = 0
        self.in_block_comment = False

    def feed(self, line: str) -> None:
        """Updates the nesting depth with the brackets on one line."""
        index = 0
        in_string = False
        while index < len(line):
            char = line[index]
            pair = line[index : index + 2]
            if self.in_block_comment:
                if pair == "*/":
                    self.in_block_comment = False
                    index += 1
            elif in_string:
                if char == "\\":
                    index += 1
                elif char == '"':
                    in_string = False
            elif char == '"':
                in_string = True
            elif char == "#" or pair == "//":
                return
            elif pair == "/*":
                self.in_block_comment = True
                index += 1
            elif char in "{[(":
                self.depth += 1
            elif char in "}])":
                self.depth -= 1
            index += 1


def _brace_balance(text: str) -> int:
    """Counts unclosed brackets in the body of a commented-out assignment."""
    scanner = _DepthScanner()
    scanner.feed(text)
    return scanner.depth


def _is_comment(line: str) -> bool:
    return line.lstrip().startswith(_COMMENT_PREFIXES)


def _keys(lines: list[str]) -> Iterator[tuple[str, int, set[int]]]:
    """Yields each depth-0 key with its line index and consumed lines.

    The consumed lines of a commented-out key are its assignment and the
    commented-out body lines that close its brackets, such as `#   amount =
    1000` and `# }`. They belong to the key, not to the comment block of
    the next key.
    """
    scanner = _DepthScanner()
    index = 0
    while index < len(lines):
        line = lines[index]
        if scanner.depth == 0 and not scanner.in_block_comment:
            commented = _COMMENTED_ASSIGNMENT_RE.match(line)
            assignment = _ASSIGNMENT_RE.match(line)
            if commented:
                consumed = {index}
                balance = _brace_balance(commented.group(2))
                while balance > 0 and index + 1 < len(lines):
                    if not _is_comment(lines[index + 1]):
                        break
                    index += 1
                    consumed.add(index)
                    balance += _brace_balance(lines[index].lstrip()[1:])
                yield commented.group(1), min(consumed), consumed
                index += 1
                continue
            if assignment:
                yield assignment.group(1), index, {index}
        scanner.feed(line)
        index += 1


def _comment_block(lines: list[str], start: int, taken: set[int]) -> list[str]:
    """Returns the contiguous comment lines directly above line `start`."""
    block = []
    index = start - 1
    while index >= 0 and index not in taken and _is_comment(lines[index]):
        block.append(lines[index].rstrip())
        index -= 1
    return block[::-1]


def parse(text: str) -> Sample:
    """Parses the text of a tfvars sample.

    Args:
        text: HCL source of the sample.

    Returns:
        The parsed sample.
    """
    values = hcl.normalize(hcl2.loads(text))
    lines = text.splitlines()
    order: list[str] = []
    comments: dict[str, list[str]] = {}
    taken: set[int] = set()
    for key, start, consumed in _keys(lines):
        if key in comments:
            continue
        order.append(key)
        comments[key] = _comment_block(lines, start, taken)
        taken |= consumed
    return Sample(values=values, order=order, comments=comments)


def load(path: pathlib.Path) -> Sample:
    """Loads a tfvars sample file.

    Args:
        path: Path of the `terraform.tfvars.sample` file.

    Returns:
        The parsed sample.
    """
    return parse(path.read_text(encoding="utf-8"))
