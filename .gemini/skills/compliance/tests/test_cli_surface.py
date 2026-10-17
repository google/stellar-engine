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

"""CLI surface: no inert AI flags or LLM stub symbols."""

import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

_SKILL_ROOT = Path(__file__).resolve().parents[1]
_GENERATE = _SKILL_ROOT / "scripts" / "generate_compliance_artifacts.py"
_STUB_RE = re.compile(
    r"LLMProvider|DeterministicAssessorProvider|get_llm_provider|enrich_narrative_with_ai|AISemanticValidationReport|"
    r"PUBLIC_SECTOR_SECURITY_ENGINEER_PROMPT|run_mandatory_ai_validation|LLM semantic reasoning|--ai-enrich|--ai-model|"
    r"no-ai-validate|no-ai-strict|ai_enrich|ai_model"
)


class CliSurfaceTest(unittest.TestCase):
    """The generator exposes no AI options and the package no LLM stubs."""

    def _generate(self, *args: str) -> subprocess.CompletedProcess:
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        with tempfile.TemporaryDirectory() as tmp:
            return subprocess.run(
                [sys.executable, str(_GENERATE), *args], cwd=tmp, env=env, capture_output=True, text=True, timeout=120, check=False
            )

    def test_generate_has_no_ai_flags(self) -> None:
        help_proc = self._generate("--help")
        self.assertEqual(help_proc.returncode, 0, help_proc.stderr)
        self.assertNotIn("--ai-", help_proc.stdout)
        with tempfile.TemporaryDirectory() as target:
            proc = self._generate(target, "--ai-enrich")
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertIn("unrecognized arguments", proc.stderr)

    def test_no_llm_stub_symbols(self) -> None:
        paths = list((_SKILL_ROOT / "src" / "compliance_engine").glob("*.py")) + [_SKILL_ROOT / "SKILL.md"]
        hits = [f"{p.name}:{n}" for p in paths for n, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1) if _STUB_RE.search(line)]
        self.assertEqual(hits, [])


if __name__ == "__main__":
    unittest.main()
