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

"""Every regex literal in the engine runs in linear time on adversarial input."""

import ast
from pathlib import Path
import re
import tempfile
import time
import unittest

from compliance_engine import audit_log
from compliance_engine import extract_system_data
from compliance_engine import file_helpers

_PKG = Path(file_helpers.__file__).parent
_FUNCS = {"compile", "search", "match", "fullmatch", "finditer", "findall", "sub", "subn", "split"}
_FLAG_NAMES = {"I": re.I, "IGNORECASE": re.I, "M": re.M, "MULTILINE": re.M, "S": re.S, "DOTALL": re.S, "X": re.X, "VERBOSE": re.X}


def _literal(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left, right = _literal(node.left), _literal(node.right)
        return left + right if left is not None and right is not None else None
    return None


def _flags(call) -> int:
    flags = 0
    for node in list(call.args[1:]) + [k.value for k in call.keywords if k.arg == "flags"]:
        for sub in ast.walk(node):
            if isinstance(sub, ast.Attribute) and isinstance(sub.value, ast.Name) and sub.value.id == "re":
                flags |= _FLAG_NAMES.get(sub.attr, 0)
    return flags


def _engine_patterns():
    for path in sorted(_PKG.glob("*.py")):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr in _FUNCS
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "re"
                and node.args
            ):
                pattern = _literal(node.args[0])
                if pattern is not None:
                    yield f"{path.name}:{node.lineno}", pattern, _flags(node)


def _elapsed(rx, text: str) -> float:
    start = time.perf_counter()
    for _ in rx.finditer(text):
        pass
    return time.perf_counter() - start


class RegexBudgetTest(unittest.TestCase):
    """Quadratic patterns are caught on a 10k probe before the 100k measurement."""

    def test_patterns_linear_on_adversarial_inputs(self) -> None:
        probes = {
            "newlines": "\n", "spaces": " ", "letters": "a", "brackets": "[", "space_nl": " \n",
            "config_req": "[CONFIG_REQUIRED: ", "mark": "<mark>", "uri": "a:",
        }
        slow = []
        count = 0
        for where, pattern, flags in _engine_patterns():
            rx = re.compile(pattern, flags)
            count += 1
            for name, unit in probes.items():
                if _elapsed(rx, unit * (10_000 // len(unit))) > 0.05:
                    slow.append(f"{where} {name} (10k)")
                    break
            else:
                for name in ("newlines", "spaces", "letters"):
                    if _elapsed(rx, probes[name] * 100_000) > 1.0:
                        slow.append(f"{where} {name} (100k)")
        self.assertGreater(count, 150)
        self.assertEqual(slow, [])

    def test_audit_log_large_payload_fast(self) -> None:
        payload = {"blob": ("a" * 63 + "=") * 1100}
        start = time.perf_counter()
        normalized = audit_log._normalize_detail(payload)
        self.assertLess(time.perf_counter() - start, 0.5)
        self.assertIn("blob", normalized)

    def test_secret_scrubber_linear(self) -> None:
        for unit in ("a", "A", "a.", "https://a:"):
            text = unit * (100_000 // len(unit))
            start = time.perf_counter()
            file_helpers.scrub_sensitive_data({"v": text})
            self.assertLess(time.perf_counter() - start, 1.0, unit)
        self.assertEqual(file_helpers.scrub_sensitive_data({"v": "postgres://user:pw@db:5432/x"})["v"], "[REDACTED_SENSITIVE]")

    def test_blank_line_tfvars_extracts_quickly(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "t"
            target.mkdir()
            (target / "main.tf").write_text('resource "google_storage_bucket" "b" {\n  name = "b"\n}\n', encoding="utf-8")
            (target / "terraform.tfvars").write_text("\n" * 100_000 + 'project_id = "demo"\n', encoding="utf-8")
            start = time.perf_counter()
            parsed = extract_system_data.parse_tfvars_content((target / "terraform.tfvars").read_text(encoding="utf-8"))
            self.assertLess(time.perf_counter() - start, 5.0)
            self.assertEqual(parsed.get("project_id"), "demo")


if __name__ == "__main__":
    unittest.main()
