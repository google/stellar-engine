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

"""Two runs with SOURCE_DATE_EPOCH set produce byte-identical deliverables."""

import hashlib
import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

from compliance_engine import extract_system_data
from compliance_engine import generate_compliance_artifacts
from compliance_engine import validate_compliance_artifacts


class DeterminismTest(unittest.TestCase):
    """Verifies SOURCE_DATE_EPOCH makes .md/.yaml/.oscal.json/.docx/.xlsm byte-identical."""

    def test_source_date_epoch_byte_identical(self) -> None:
        """Two runs separated in wall-clock time produce identical bytes for every deliverable."""
        tf_source = (
            'resource "google_project_service" "s" {\n  service = "bigquery.googleapis.com"\n}\n'
            'resource "google_bigquery_dataset" "d" {\n  dataset_id = "analytics"\n  location = "US"\n}\n'
        )
        digests_by_run: list[dict[str, str]] = []
        with patch.dict(os.environ, {"SOURCE_DATE_EPOCH": "1760486400", "COMPLIANCE_OFFLINE": "1"}):
            for run_idx in range(2):
                if run_idx == 1:
                    time.sleep(1.1)
                with tempfile.TemporaryDirectory() as td:
                    bp = Path(td) / "il5" / "det_bp"
                    bp.mkdir(parents=True)
                    (bp / "main.tf").write_text(tf_source, encoding="utf-8")
                    extract_system_data.extract_system_inventory(bp)
                    generate_compliance_artifacts.generate_ato_artifacts(
                        str(bp), policy_format="both", data_format="both", oscal_format="both"
                    )
                    validate_compliance_artifacts.validate_compliance_package(
                        str(bp), run_linter=True, linter_strict=False
                    )
                    ato_dir = bp / "ato_artifacts"
                    run_digests: dict[str, str] = {}
                    for fp in sorted(ato_dir.rglob("*")):
                        if not fp.is_file():
                            continue
                        rel = str(fp.relative_to(ato_dir)).replace("\\", "/")
                        if rel == "compliance_engine_audit.jsonl":
                            continue
                        run_digests[rel] = hashlib.sha256(fp.read_bytes()).hexdigest()
                    digests_by_run.append(run_digests)

        self.assertEqual(set(digests_by_run[0]), set(digests_by_run[1]))
        diffs = [
            k for k in sorted(digests_by_run[0])
            if digests_by_run[0][k] != digests_by_run[1][k]
        ]
        self.assertEqual(diffs, [], f"Non-deterministic files across SOURCE_DATE_EPOCH runs: {diffs}")


if __name__ == "__main__":
    unittest.main()
