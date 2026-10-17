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

"""YAML alias-expansion and nesting budgets."""

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

from compliance_engine import extract_system_data
from compliance_engine import file_helpers

_SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def _alias_dag(levels: int = 9, width: int = 9) -> str:
    lines = ["x_anchors:", f"  a0: &a0 [{', '.join(['x'] * width)}]"]
    for i in range(1, levels + 1):
        lines.append(f"  a{i}: &a{i} [{', '.join([f'*a{i - 1}'] * width)}]")
    return "\n".join(lines) + "\n"


class YamlBudgetTest(unittest.TestCase):
    """parse_yaml_safe enforces MAX_YAML_EXPANDED_NODES; deep nesting is a clean ValueError."""

    def test_alias_dag_rejected(self) -> None:
        start = time.monotonic()
        with self.assertRaises(ValueError) as ctx:
            file_helpers.parse_yaml_safe(_alias_dag(), source_name="dag")
        self.assertLess(time.monotonic() - start, 2.0)
        self.assertIn("expanded-node budget", str(ctx.exception))
        self.assertIsInstance(ctx.exception, file_helpers.YamlBudgetError)

    def test_small_aliases_and_large_plain_documents_allowed(self) -> None:
        doc = "base: &b {k: v}\nitems:\n" + "  - *b\n" * 50
        self.assertEqual(len(file_helpers.parse_yaml_safe(doc)["items"]), 50)
        plain = "items:\n" + "".join(f"  - {{id: {i}, name: n{i}}}\n" for i in range(20000))
        self.assertEqual(len(file_helpers.parse_yaml_safe(plain)["items"]), 20000)

    def test_recursive_alias_rejected(self) -> None:
        with self.assertRaises(file_helpers.YamlBudgetError):
            file_helpers.parse_yaml_safe("a: &a [*a]\n")

    def test_front_matter_uses_parse_yaml_safe(self) -> None:
        content = "---\n" + _alias_dag() + "---\n# Title\n\nBody text.\n"
        with self.assertRaises(file_helpers.YamlBudgetError):
            extract_system_data.extract_system_description_from_markdown(content)
        desc, title = extract_system_data.extract_system_description_from_markdown("---\ntitle: Demo\n---\nBody text here.\n")
        self.assertEqual(title, "Demo")

    def test_deep_nesting_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "deep.json")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write("[" * 100000)
            with self.assertRaises(ValueError) as ctx:
                file_helpers.read_json_file(path)
            self.assertIn("nesting exceeds budget", str(ctx.exception))
        with self.assertRaises(ValueError):
            file_helpers.parse_yaml_safe("[" * 100000)

    def test_extract_cli_rejects_alias_config_quickly(self) -> None:
        for name, content in (
            ("compliance_config.yaml", "system_information:\n  system_name: Demo\n  impact_level: IL5\n" + _alias_dag()),
            ("README.md", "---\n" + _alias_dag() + "---\n# Demo\n"),
        ):
            with self.subTest(file=name), tempfile.TemporaryDirectory() as tmp:
                target = Path(tmp) / "target"
                target.mkdir()
                (target / "main.tf").write_text('resource "google_storage_bucket" "b" {\n  name = "b"\n}\n', encoding="utf-8")
                (target / name).write_text(content, encoding="utf-8")
                start = time.monotonic()
                proc = subprocess.run(
                    [sys.executable, str(_SCRIPTS / "extract_system_data.py"), str(target)],
                    cwd=tmp, capture_output=True, text=True, timeout=60, check=False,
                    env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1", COMPLIANCE_DISABLE_LIVE_SCANNERS="1"),
                )
                self.assertLess(time.monotonic() - start, 30.0)
                self.assertNotEqual(proc.returncode, 0, proc.stdout + proc.stderr)
                self.assertNotIn("Traceback", proc.stderr)
                self.assertFalse((target / "system_inventory.json").exists())


if __name__ == "__main__":
    unittest.main()
