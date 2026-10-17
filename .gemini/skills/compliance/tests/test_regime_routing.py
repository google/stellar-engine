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

"""Unsupported regimes fail closed before anything is written ."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from compliance_engine.file_helpers import REGIME_SUPPORT, Regime

_SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
_TF = 'resource "google_storage_bucket" "b" {\n  name     = "b"\n  location = "US"\n}\n'
_SAMPLES = {
    Regime.FEDRAMP_MODERATE: "FedRAMP Moderate",
    Regime.FEDRAMP_LOW: "FedRAMP Low",
    Regime.CJIS: "CJIS",
    Regime.GOVRAMP: "GovRAMP High",
    Regime.FISMA_MODERATE: "FISMA Moderate",
    Regime.DOD_IL2: "IL2",
    Regime.DOD_IL4: "IL4",
    Regime.DOD_IL6: "IL6",
    Regime.UNKNOWN: "FedRAMP Tailored LI-SaaS",
}


def _generate(impact: str) -> subprocess.CompletedProcess:
    tmp = tempfile.mkdtemp()
    target = Path(tmp) / "t"
    target.mkdir()
    (target / "main.tf").write_text(_TF, encoding="utf-8")
    sys_info = {"system_name": "Demo", "organization": "Example Agency", "impact_level": impact, "compliance_baseline": impact}
    roles = {role: {"name": "Example Person"} for role in ("authorizing_official", "system_owner", "issm", "isso")}
    inventory = {"system_information": sys_info, "personnel_roles": roles, "infrastructure_components": {}, "network_architecture": {}}
    (target / "system_inventory.json").write_text(json.dumps(inventory), encoding="utf-8")
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", COMPLIANCE_DISABLE_LIVE_SCANNERS="1")
    proc = subprocess.run([sys.executable, str(_SCRIPTS / "generate_compliance_artifacts.py"), str(target), "--policy-format=markdown", "--data-format=yaml"],
                          env=env, cwd=tmp, capture_output=True, text=True, timeout=300, check=False)
    proc.target = target  # type: ignore[attr-defined]
    return proc


class RegimeRoutingTest(unittest.TestCase):
    """Every regime switched off in REGIME_SUPPORT is refused by the generator."""

    def test_unsupported_regimes_fail_closed(self) -> None:
        for regime, text in _SAMPLES.items():
            if REGIME_SUPPORT[regime]:
                continue
            with self.subTest(regime=regime):
                proc = _generate(text)
                self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
                self.assertIn("Unsupported regime", proc.stderr)
                self.assertIn("FedRAMP High", proc.stderr)
                self.assertNotIn("Traceback", proc.stderr)
                self.assertFalse((proc.target / "ato_artifacts").exists())

    def test_govramp_and_tailored_rejected(self) -> None:
        for unsupported in ("GovRAMP High", "StateRAMP Moderate", "FedRAMP Tailored LI-SaaS"):
            with self.subTest(unsupported=unsupported):
                proc = _generate(unsupported)
                self.assertEqual(proc.returncode, 1)
                self.assertFalse((proc.target / "ato_artifacts").exists())


if __name__ == "__main__":
    unittest.main()
