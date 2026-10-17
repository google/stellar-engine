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

"""Child-module read boundary: enclosing git work tree only, no symlinks, reads recorded ."""

import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest import mock

from compliance_engine import extract_system_data
from compliance_engine import file_helpers

_REPO = Path(__file__).resolve().parents[4]
_MARKER_TF = 'resource "google_compute_instance" "OUTSIDE_MARKER" {\n  name = "x"\n}\n'
_CALLER_TF = 'module "other" {\n  source = "../other"\n}\n'


def _extract(target: Path, **kwargs):
    with mock.patch.dict(os.environ, {"COMPLIANCE_DISABLE_LIVE_SCANNERS": "1"}):
        return extract_system_data.extract_system_inventory(str(target), **kwargs)


class ChildModuleBoundaryTest(unittest.TestCase):
    """resolve_local_child_module_dir and extraction provenance."""

    def _layout(self, root: Path) -> Path:
        (root / "modules").mkdir()
        (root / "other").mkdir()
        (root / "other" / "main.tf").write_text(_MARKER_TF, encoding="utf-8")
        target = root / "t"
        target.mkdir()
        (target / "main.tf").write_text(_CALLER_TF + 'resource "google_storage_bucket" "b" {\n  name = "b"\n}\n', encoding="utf-8")
        return target

    def test_modules_dir_heuristic_does_not_widen_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = self._layout(Path(tmp))
            self.assertIsNone(file_helpers.find_enclosing_repo_root(target))
            self.assertNotIn("OUTSIDE_MARKER", json.dumps(_extract(target)))
            with_root = _extract(target, module_root=tmp)
            self.assertIn("OUTSIDE_MARKER", json.dumps(with_root["infrastructure_components"]["all_resources"]))
            with self.assertRaises(ValueError):
                _extract(target, module_root=str(target / "nowhere"))

    def test_out_of_target_reads_recorded(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = self._layout(root)
            (root / ".git").mkdir()
            inventory = _extract(target)
            self.assertIn("OUTSIDE_MARKER", json.dumps(inventory["infrastructure_components"]["all_resources"]))
            self.assertEqual(inventory["provenance"]["external_module_files"], ["other/main.tf"])
            self.assertEqual(inventory["provenance"]["module_root"], "git work tree")

    def test_symlinked_module_component_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".git").mkdir()
            target = self._layout(root)
            shutil.rmtree(root / "modules")
            os.symlink(root / "other", root / "linkmod")
            caller = 'module "l" {\n  source = "../linkmod"\n}\nresource "google_storage_bucket" "b" {\n  name = "b"\n}\n'
            (target / "main.tf").write_text(caller, encoding="utf-8")
            self.assertIsNone(file_helpers.resolve_local_child_module_dir(target, "../linkmod", target))
            self.assertNotIn("OUTSIDE_MARKER", json.dumps(_extract(target)))

    def test_cff_blueprint_modules_still_resolved(self) -> None:
        target = _REPO / "blueprints" / "il5" / "bigquery"
        resolved = file_helpers.resolve_local_child_module_dir(target, "../../../modules/bigquery-dataset", target.resolve())
        self.assertEqual(resolved, (_REPO / "modules" / "bigquery-dataset").resolve())


if __name__ == "__main__":
    unittest.main()
