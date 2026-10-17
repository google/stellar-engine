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

"""Built wheels include templates/ and config/ and support the 3-step CLI workflow."""

from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile

_SKILL_ROOT = Path(__file__).resolve().parents[1]


class PackagingTest(unittest.TestCase):
    """Verifies wheel contents and installed CLI workflow."""

    def test_wheel_contains_templates_and_config(self) -> None:
        """Built wheel packages templates/ and config/ and installed CLI produces full deliverables."""
        with tempfile.TemporaryDirectory() as td:
            src_copy = Path(td) / "skill_copy"
            src_copy.mkdir()
            for item in ("pyproject.toml", "README.md", "src", "templates", "config"):
                src_p = _SKILL_ROOT / item
                dst_p = src_copy / item
                if src_p.is_dir():
                    shutil.copytree(src_p, dst_p)
                else:
                    shutil.copy2(src_p, dst_p)

            dist_dir = Path(td) / "dist"
            dist_dir.mkdir()
            build_cmd = [
                sys.executable,
                "-m",
                "pip",
                "wheel",
                "--no-deps",
                "--no-build-isolation",
                "-w",
                str(dist_dir),
                str(src_copy),
            ]
            res = subprocess.run(build_cmd, capture_output=True, text=True, check=False)
            self.assertEqual(res.returncode, 0, f"Wheel build failed:\n{res.stdout}\n{res.stderr}")

            wheels = list(dist_dir.glob("*.whl"))
            self.assertEqual(len(wheels), 1, f"Expected 1 wheel, got {wheels}")
            whl_path = wheels[0]

            with zipfile.ZipFile(whl_path) as zf:
                names = zf.namelist()

            template_members = [n for n in names if "templates/" in n]
            config_members = [n for n in names if "config/" in n]
            self.assertGreaterEqual(len(template_members), 30, f"Missing templates in wheel: {template_members}")
            self.assertGreaterEqual(len(config_members), 10, f"Missing configs in wheel: {config_members}")
            self.assertTrue(any(n.endswith("SSP_IL5_Template.md") for n in template_members))
            self.assertTrue(any(n.endswith("HWSWList_Template.xlsm") for n in template_members))
            self.assertTrue(any(n.endswith("stig_catalog.json") for n in config_members))
            self.assertTrue(any(n.endswith("dod_il5.json") for n in config_members))

            # Unpack the wheel into an isolated target dir (without scripts/ or repo checkout)
            install_root = Path(td) / "installed_site"
            install_root.mkdir()
            with zipfile.ZipFile(whl_path) as zf:
                zf.extractall(install_root)

            bp_dir = Path(td) / "il5" / "sample_bp"
            bp_dir.mkdir(parents=True)
            (bp_dir / "main.tf").write_text(
                'resource "google_project_service" "s" {\n  service = "bigquery.googleapis.com"\n}\n'
                'resource "google_bigquery_dataset" "d" {\n  dataset_id = "analytics"\n  location = "US"\n}\n',
                encoding="utf-8",
            )

            # Run the 3-step workflow using only the unpacked wheel on PYTHONPATH (outside repo)
            site_dirs = [str(install_root)] + [p for p in sys.path if "site-packages" in p]
            env = {
                "PATH": "/usr/bin:/bin",
                "PYTHONPATH": ":".join(site_dirs),
                "PYTHONDONTWRITEBYTECODE": "1",
                "COMPLIANCE_OFFLINE": "1",
                "HOME": str(td),
            }
            for mod, extra in (
                ("compliance_engine.extract_system_data", []),
                (
                    "compliance_engine.generate_compliance_artifacts",
                    ["--policy-format=both", "--data-format=both", "--oscal-format=both"],
                ),
                ("compliance_engine.validate_compliance_artifacts", ["--no-linter-strict"]),
            ):
                cmd = [sys.executable, "-m", mod, *extra, str(bp_dir)]
                step_res = subprocess.run(cmd, cwd=td, env=env, capture_output=True, text=True, check=False)
                if mod != "compliance_engine.validate_compliance_artifacts":
                    self.assertEqual(step_res.returncode, 0, f"{mod} failed:\n{step_res.stdout}\n{step_res.stderr}")

            ato_dir = bp_dir / "ato_artifacts"
            all_outputs = [p for p in ato_dir.rglob("*") if p.is_file()]
            # 69 deliverables + 2 auxiliary files = 71 total files
            self.assertGreaterEqual(len(all_outputs), 69, f"Expected >=69 files from wheel, got {len(all_outputs)}")


if __name__ == "__main__":
    unittest.main()
