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

"""Repository hygiene checks: no internal review IDs, no filler prose, no smart quotes."""

from pathlib import Path
import re
import unittest

_SKILL_ROOT = Path(__file__).resolve().parents[1]

_INTERNAL_ID_RE = re.compile(
    r"\b(?:E2E-[0-9]+|SEC_[AB][0-9]*-[A-Z0-9-]+|CODE_[ABC]-[0-9]+|CODE_TESTS-[0-9]+"
    r"|HYG-[0-9]+|VULN-[0-9]+|ORCH-[0-9]+|Fixer\s+[0-9]+|V2-[0-9]{3})\b"
)
_FILLER_RE = re.compile(r"\b(?:comprehensive|robust|robustness|seamless|flawless)\b", re.IGNORECASE)

# Verbatim NIST SP 800-53 Rev. 5 catalog quotes that legally contain 'comprehensive'.
_REGULATORY_QUOTE_ALLOWLIST = {
    "templates/policies/Program_Management_Policy_and_Procedures.md",
    "templates/ssp/SSP_IL5_Template.md",
}


class RepoHygieneTest(unittest.TestCase):
    """Enforces clean public-facing prose and comments across the compliance skill."""

    def test_no_internal_review_ids(self) -> None:
        """No internal goal-v1 review IDs or [AI CONTEXTUAL EXAMPLE REQUIRED] branding remain."""
        offenders: list[str] = []
        for path in sorted(_SKILL_ROOT.rglob("*")):
            if not path.is_file() or "__pycache__" in path.parts or ".venv" in path.parts:
                continue
            if path.suffix not in {".py", ".md", ".yaml", ".yml", ".json", ".toml", ".txt"}:
                continue
            if path.name == "test_repo_hygiene.py":
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            rel = str(path.relative_to(_SKILL_ROOT))
            for idx, line in enumerate(text.splitlines(), 1):
                if _INTERNAL_ID_RE.search(line):
                    offenders.append(f"{rel}:{idx}: internal review ID: {line.strip()}")
                if "AI CONTEXTUAL EXAMPLE REQUIRED" in line:
                    offenders.append(f"{rel}:{idx}: legacy AI badge: {line.strip()}")
        self.assertEqual(offenders, [], "Internal IDs or AI badge remain:\n" + "\n".join(offenders[:30]))

    def test_no_filler_words(self) -> None:
        """No marketing/filler words appear in src/, tests/, or non-quoted templates/."""
        offenders: list[str] = []
        for subdir in ("src", "tests", "templates"):
            for path in sorted((_SKILL_ROOT / subdir).rglob("*")):
                if not path.is_file() or "__pycache__" in path.parts or path.name == "test_repo_hygiene.py":
                    continue
                if path.suffix not in {".py", ".md", ".yaml", ".yml"}:
                    continue
                rel = str(path.relative_to(_SKILL_ROOT)).replace("\\", "/")
                if rel in _REGULATORY_QUOTE_ALLOWLIST:
                    continue
                text = path.read_text(encoding="utf-8", errors="ignore")
                for idx, line in enumerate(text.splitlines(), 1):
                    if _FILLER_RE.search(line):
                        offenders.append(f"{rel}:{idx}: {line.strip()}")
        self.assertEqual(offenders, [], "Filler words found:\n" + "\n".join(offenders[:30]))

    def test_no_smart_quotes_in_ssp_templates(self) -> None:
        """SSP templates contain no curly smart quotes (U+2018 / U+2019)."""
        for name in ("SSP_FedRAMP_High_Template.md", "SSP_IL5_Template.md"):
            text = (_SKILL_ROOT / "templates" / "ssp" / name).read_text(encoding="utf-8")
            self.assertNotIn("\u2018", text, name)
            self.assertNotIn("\u2019", text, name)


if __name__ == "__main__":
    unittest.main()
