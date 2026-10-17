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

"""Live scanners: operator opt-in, kill switch authority, private sanitized copy ."""

import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from compliance_engine import file_helpers
from compliance_engine import poam_rules
from compliance_engine import security_scanner_bridge as ssb

_SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
_TF = 'resource "google_storage_bucket" "b" {\n  name     = "b"\n  location = "US"\n}\n'


def _fake_scanner(bin_dir: Path, name: str, log: Path) -> None:
    """Writes an executable that records argv, cwd, HOME and the scanned tree, then prints []."""
    script = bin_dir / name
    script.write_text(
        f"#!{sys.executable}\n"
        "import json, os, sys\n"
        "argv = sys.argv[1:]\n"
        "tree = []\n"
        "if '--directory' in argv:\n"
        "    root = argv[argv.index('--directory') + 1]\n"
        "    for dp, dn, fn in os.walk(root):\n"
        "        tree += [os.path.relpath(os.path.join(dp, f), root) for f in fn + dn]\n"
        "home = os.environ.get('HOME', '')\n"
        f"with open({str(log)!r}, 'a') as fh:\n"
        "    fh.write(json.dumps({'argv': argv, 'cwd': os.getcwd(), 'home': home,\n"
        "        'home_entries': sorted(os.listdir(home)) if home and os.path.isdir(home) else None,\n"
        "        'cwd_entries': sorted(os.listdir(os.getcwd())), 'tree': sorted(tree)}) + '\\n')\n"
        "print('[]')\n",
        encoding="utf-8",
    )
    script.chmod(script.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def _hostile_target(root: Path) -> Path:
    target = root / "target"
    (target / "modules" / "app").mkdir(parents=True)
    (target / "main.tf").write_text(_TF, encoding="utf-8")
    (target / "terraform.tfvars").write_text('project_id = "demo"\n', encoding="utf-8")
    (target / "modules" / "app" / "app.py").write_text("print('x')\n", encoding="utf-8")
    (target / ".checkov.yaml").write_text("external-checks-dir:\n  - /tmp/evil\nskip-check:\n  - CKV_GCP_62\n", encoding="utf-8")
    (target / "trivy.yaml").write_text("severity: LOW\n", encoding="utf-8")
    (target / ".semgrepignore").write_text("*\n", encoding="utf-8")
    (target / ".git").mkdir()
    (target / ".git" / "config").write_text("[core]\n", encoding="utf-8")
    (target / ".hidden").mkdir()
    (target / ".hidden" / "x.tf").write_text(_TF, encoding="utf-8")
    outside = root / "outside"
    outside.mkdir()
    (outside / "secret.tf").write_text(_TF, encoding="utf-8")
    os.symlink(outside, target / "linked")
    return target


class ScannerIsolationTest(unittest.TestCase):
    """The scan copy and the operator policy are the only inputs to live scanners."""

    def test_target_checkov_config_not_present_in_scan_copy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = _hostile_target(Path(tmp))
            copy = ssb.build_scan_copy(target, Path(tmp) / "copy")
            files = sorted(str(p.relative_to(copy)) for p in copy.rglob("*") if p.is_file())
            self.assertEqual(files, ["main.tf", "modules/app/app.py", "terraform.tfvars"])

    def test_dotfiles_excluded_from_scan_copy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = _hostile_target(Path(tmp))
            copy = ssb.build_scan_copy(target, Path(tmp) / "copy")
            names = {p.name for p in copy.rglob("*")}
            for banned in (".checkov.yaml", "trivy.yaml", ".semgrepignore", ".git", ".hidden", "linked", "secret.tf"):
                self.assertNotIn(banned, names)

    def test_scanners_off_without_operator_flag(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = _hostile_target(Path(tmp))
            inventory = {
                "system_information": {"impact_level": "IL5", "workspace_path": str(Path(tmp) / "outside")},
                "security_scanners": {"enabled": True, "run_checkov": True, "run_semgrep": True, "run_trivy": True},
            }
            with mock.patch.dict(os.environ, {"COMPLIANCE_DISABLE_LIVE_SCANNERS": ""}), \
                    mock.patch.object(ssb, "_safe_run_subprocess") as run:
                poam_rules.derive_poam_findings(inventory, target_dir=str(target))
                poam_rules.derive_poam_findings(inventory, target_dir=str(target), scanner_policy=ssb.resolve_scanner_policy(False))
            run.assert_not_called()

    def test_live_scan_runs_on_private_copy_with_empty_home_and_cwd(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = _hostile_target(root)
            bin_dir = root / "bin"
            bin_dir.mkdir()
            log = root / "scanner.log"
            _fake_scanner(bin_dir, "checkov", log)
            env = {"PATH": f"{bin_dir}{os.pathsep}{os.environ.get('PATH', '')}", "COMPLIANCE_DISABLE_LIVE_SCANNERS": ""}
            with mock.patch.dict(os.environ, env):
                ssb.reset_scan_cache()
                policy = ssb.resolve_scanner_policy(True, scanners=["checkov"])
                poam_rules.derive_poam_findings({"system_information": {"impact_level": "IL5"}}, target_dir=str(target), scanner_policy=policy)
            records = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(len(records), 1)
            rec = records[0]
            scanned = rec["argv"][rec["argv"].index("--directory") + 1]
            self.assertFalse(scanned.startswith(str(target)), scanned)
            self.assertNotIn(".checkov.yaml", rec["tree"])
            self.assertIn("main.tf", rec["tree"])
            self.assertIn("--config-file", rec["argv"])
            self.assertNotEqual(rec["home"], os.path.expanduser("~"))
            self.assertEqual(rec["home_entries"], [])
            self.assertNotEqual(Path(rec["cwd"]).resolve(), target.resolve())
            self.assertFalse(Path(scanned).exists(), "private scan copy must be removed after the run")

    def test_inventory_keys_cannot_choose_scan_root_or_enable_scanners(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = _hostile_target(root)
            # A target holding .git is a repository root, which the CLIs refuse.
            (target / ".git" / "config").unlink()
            (target / ".git").rmdir()
            bin_dir = root / "bin"
            bin_dir.mkdir()
            log = root / "scanner.log"
            for name in ("checkov", "semgrep", "trivy"):
                _fake_scanner(bin_dir, name, log)
            (target / "compliance_config.yaml").write_text(
                "system_information:\n  system_name: Demo\n  impact_level: IL5\n"
                "security_scanners:\n  enabled: true\n  run_checkov: true\n  run_semgrep: true\n",
                encoding="utf-8",
            )
            env = dict(os.environ, PATH=f"{bin_dir}{os.pathsep}{os.environ.get('PATH', '')}",
                       COMPLIANCE_DISABLE_LIVE_SCANNERS="1", PYTHONDONTWRITEBYTECODE="1")
            subprocess.run([sys.executable, str(_SCRIPTS / "extract_system_data.py"), str(target)],
                           env=env, cwd=tmp, capture_output=True, text=True, timeout=300, check=True)
            inv_path = target / "system_inventory.json"
            inventory = json.loads(inv_path.read_text(encoding="utf-8"))
            inventory["system_information"]["workspace_path"] = str(root / "outside")
            inventory["security_scanners"] = {"enabled": True, "run_checkov": True, "run_semgrep": True}
            inv_path.write_text(json.dumps(inventory), encoding="utf-8")
            for argv in (
                [str(_SCRIPTS / "generate_compliance_artifacts.py"), str(target), "--run-scanners", "--data-format=yaml", "--policy-format=markdown"],
                [str(_SCRIPTS / "validate_compliance_artifacts.py"), str(target), "--fix", "--run-scanners"],
            ):
                with self.subTest(cli=Path(argv[0]).name):
                    proc = subprocess.run([sys.executable, *argv], env=env, cwd=tmp, capture_output=True, text=True, timeout=600, check=False)
                    self.assertNotIn("Traceback", proc.stderr)
            self.assertFalse(log.exists(), log.read_text(encoding="utf-8") if log.exists() else "")
            poam = (target / "ato_artifacts" / "POAM" / "Plan_of_Action_and_Milestones.yaml").read_text(encoding="utf-8")
            self.assertNotIn("secret.tf", poam)
            self.assertNotIn(str(root / "outside"), poam)

    def test_env_kill_switch_overrides_target_config(self) -> None:
        for value in ("1", "true", "yes", "TRUE", "on"):
            with self.subTest(value=value), mock.patch.dict(os.environ, {"COMPLIANCE_DISABLE_LIVE_SCANNERS": value}):
                self.assertFalse(ssb.resolve_scanner_policy(True).run_live)
                with tempfile.TemporaryDirectory() as tmp, mock.patch.object(ssb, "run_checkov_scan") as checkov, \
                        mock.patch.object(ssb, "run_semgrep_scan") as semgrep:
                    Path(tmp, "main.tf").write_text(_TF, encoding="utf-8")
                    ssb.scan_and_derive_poam_items(tmp, config={"run_checkov": True, "run_semgrep": True, "enabled": True})
                    checkov.assert_not_called()
                    semgrep.assert_not_called()

    def test_truthy_parsing_consistent(self) -> None:
        for value, expected in (("1", True), ("true", True), ("Yes", True), ("on", True), ("0", False), ("", False), ("false", False), ("no", False)):
            with self.subTest(value=value), mock.patch.dict(os.environ, {"COMPLIANCE_DISABLE_LIVE_SCANNERS": value}):
                self.assertEqual(file_helpers.env_flag_enabled("COMPLIANCE_DISABLE_LIVE_SCANNERS"), expected)
                self.assertEqual(ssb.resolve_scanner_policy(True).run_live, not expected)


if __name__ == "__main__":
    unittest.main()
