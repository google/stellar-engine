#!/usr/bin/env python3
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

"""Regression tests for extraction truthfulness and completeness."""

import contextlib
import json
from pathlib import Path
import shutil
import tempfile
from typing import Iterator
import unittest

from compliance_engine import extract_system_data
from compliance_engine import file_helpers
from compliance_engine import poam_rules

_TESTS_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _TESTS_DIR.parents[3]


@contextlib.contextmanager
def _mirror_blueprint(blueprint_rel: str) -> Iterator[Path]:
    """Copies a blueprint and the repo modules/ tree into a temporary git-like root."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp).resolve()
        (root / ".git").mkdir()
        shutil.copytree(_REPO_ROOT / "modules", root / "modules")
        dest = root / blueprint_rel
        shutil.copytree(_REPO_ROOT / blueprint_rel, dest, symlinks=False)
        yield dest


class ExtractionTruthfulnessTest(unittest.TestCase):
    """Verifies that static HCL extraction does not fabricate or drop boundary facts."""

    def test_conditional_module_resources_excluded(self) -> None:
        """Inactive (count=0/for_each={}) and unresolved child-module resources must not enter all_resources."""
        with _mirror_blueprint("blueprints/il5/bigquery") as bp_dir:
            inv = extract_system_data.extract_system_inventory(str(bp_dir))
        infra = inv["infrastructure_components"]
        all_res_types = {r["type"] for r in infra["all_resources"]}
        self.assertIn("google_bigquery_dataset", all_res_types)
        self.assertNotIn("google_bigquery_dataset_access", all_res_types)
        self.assertNotIn("google_bigquery_dataset_iam_binding", all_res_types)
        self.assertNotIn("google_bigquery_table", all_res_types)
        self.assertNotIn("google_bigquery_routine", all_res_types)
        self.assertNotIn("google_tags_location_tag_binding", all_res_types)
        undetermined_types = {
            r["type"] for r in infra.get("conditional_resources_undetermined", [])
        }
        self.assertIn("google_bigquery_table", undetermined_types)

        with _mirror_blueprint("blueprints/fedramp-high/cloud-run") as cr_dir:
            cr_inv = extract_system_data.extract_system_inventory(str(cr_dir))
        cr_types = {r["type"] for r in cr_inv["infrastructure_components"]["all_resources"]}
        self.assertIn("google_cloud_run_v2_service", cr_types)
        self.assertNotIn("google_cloud_run_v2_job", cr_types)
        self.assertNotIn("google_vpc_access_connector", cr_types)

    def test_unresolved_region_not_defaulted(self) -> None:
        """Unresolved region variables must not default to us-east4 (Ashburn) or US Multi-Region."""
        with _mirror_blueprint("blueprints/fedramp-high/cloud-run") as cr_dir:
            cr_inv = extract_system_data.extract_system_inventory(str(cr_dir))
        cr_loc = cr_inv["system_information"]["primary_location"]
        self.assertTrue(
            cr_loc.startswith("[CONFIG_REQUIRED") or cr_loc == file_helpers.NOT_DETERMINED,
            f"Expected undetermined/config-required primary_location, got {cr_loc!r}",
        )
        cr_services = cr_inv["infrastructure_components"]["cloud_run_services"]
        self.assertEqual(len(cr_services), 1)
        self.assertNotEqual(cr_services[0].get("location"), "us-east4")
        self.assertNotIn("us-east4", json.dumps(cr_inv))
        self.assertNotIn("Ashburn", json.dumps(cr_inv))

        with _mirror_blueprint("blueprints/il5/bigquery") as bq_dir:
            bq_inv = extract_system_data.extract_system_inventory(str(bq_dir))
        bq_loc = bq_inv["system_information"]["primary_location"]
        self.assertTrue(
            bq_loc.startswith("[CONFIG_REQUIRED") or bq_loc == file_helpers.NOT_DETERMINED,
            f"Expected undetermined/config-required primary_location for bigquery, got {bq_loc!r}",
        )

    def test_cmek_only_with_key_reference(self) -> None:
        """Unresolved encryption_key variables without defaults must not claim CMEK."""
        self.assertIsNone(
            extract_system_data._resolved_cmek_name("${var.encryption_key}", {})
        )
        self.assertIsNone(
            extract_system_data._resolved_cmek_name("var.kms_key_name", {})
        )
        self.assertIsNone(
            extract_system_data._resolved_cmek_name("${var.encryption_key}", {"encryption_key": None})
        )
        self.assertEqual(
            extract_system_data._resolved_cmek_name(
                "${var.encryption_key}", {"encryption_key": "projects/p/locations/l/keyRings/r/cryptoKeys/k"}
            ),
            "projects/p/locations/l/keyRings/r/cryptoKeys/k",
        )
        self.assertEqual(
            extract_system_data._resolved_cmek_name(
                "${data.google_kms_crypto_key.default.id}", {}
            ),
            "default",
        )
        self.assertEqual(
            extract_system_data._resolved_cmek_name(
                "${module.kms.keys.default.id}", {}
            ),
            "default",
        )

    def test_unknown_cloudsql_version_not_defaulted(self) -> None:
        """Unknown or variable-driven Cloud SQL versions must not default to PostgreSQL 15."""
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            (target / "variables.tf").write_text(
                'variable "db_version" {\n  type = string\n}\n'
                'variable "db_tier" {\n  type = string\n}\n',
                encoding="utf-8",
            )
            (target / "main.tf").write_text(
                'resource "google_sql_database_instance" "db" {\n'
                '  name             = "mysql-or-pg"\n'
                '  database_version = var.db_version\n'
                '  settings {\n'
                '    tier = var.db_tier\n'
                '  }\n'
                '}\n',
                encoding="utf-8",
            )
            scanned = extract_system_data.deep_scan_tf_files(str(target))
        self.assertEqual(len(scanned["databases"]), 1)
        db = scanned["databases"][0]
        self.assertEqual(db["database_version"], file_helpers.NOT_DETERMINED)
        self.assertEqual(db["tier"], file_helpers.NOT_DETERMINED)
        self.assertNotIn("POSTGRES", str(db["database_version"]).upper())

    def test_gke_hardened_kms_vpc_iam_extracted(self) -> None:
        """il5/gke-hardened inventory extracts non-empty kms_keys, vpcs, and iam_bindings."""
        with _mirror_blueprint("blueprints/il5/gke-hardened") as bp_dir:
            inv = extract_system_data.extract_system_inventory(str(bp_dir))
        infra = inv["infrastructure_components"]
        net = inv["network_architecture"]
        self.assertTrue(infra["kms_keys"], "expected non-empty kms_keys for gke-hardened")
        self.assertTrue(net["vpcs"], "expected non-empty vpcs for gke-hardened")
        self.assertTrue(infra["iam_bindings"], "expected non-empty iam_bindings for gke-hardened")
        self.assertNotIn("${var.", json.dumps(inv))

    def test_no_raw_var_interpolation(self) -> None:
        """No '${var.' substring may leak into system_inventory.json across blueprints."""
        for bp in (
            "blueprints/il5/bigquery",
            "blueprints/il5/postgresql",
            "blueprints/il5/gke-hardened",
            "blueprints/il5/compute-engine",
            "blueprints/fedramp-high/cloud-run",
        ):
            with self.subTest(blueprint=bp), _mirror_blueprint(bp) as bp_dir:
                inv = extract_system_data.extract_system_inventory(str(bp_dir))
                serialized = json.dumps(inv)
                self.assertNotIn("${var.", serialized)
                self.assertNotIn("service-number@", serialized)

    def test_readme_license_not_description(self) -> None:
        """README Apache-2.0 license preambles and tutorial steps are stripped from descriptions."""
        with _mirror_blueprint("blueprints/il5/postgresql") as pg_dir:
            pg_inv = extract_system_data.extract_system_inventory(str(pg_dir))
        pg_desc = pg_inv["system_information"]["system_description"]
        self.assertNotIn("Apache License", pg_desc)
        self.assertNotIn("http://www.apache.org/licenses", pg_desc)
        self.assertNotIn("WITHOUT WARRANTIES OR CONDITIONS", pg_desc)
        self.assertEqual(
            pg_inv["system_information"]["primary_location"],
            "us-east4 (Ashburn, Northern Virginia, USA)",
        )

        with _mirror_blueprint("blueprints/il5/bigquery") as bq_dir:
            bq_inv = extract_system_data.extract_system_inventory(str(bq_dir))
        bq_desc = bq_inv["system_information"]["system_description"]
        self.assertNotIn("<br />", bq_desc)
        self.assertNotIn("with your main GCP Project ID", bq_desc)

    def test_iam_member_placeholders_resolved(self) -> None:
        """IAM principals never equal 'member' and source files never equal 'terraform.tfplan' on HCL."""
        for bp in ("blueprints/il5/postgresql", "blueprints/il5/bigquery"):
            with self.subTest(blueprint=bp), _mirror_blueprint(bp) as bp_dir:
                inv = extract_system_data.extract_system_inventory(str(bp_dir))
                infra = inv["infrastructure_components"]
                for binding in infra["iam_bindings"]:
                    self.assertNotEqual(binding.get("principal"), "member")
                    self.assertNotEqual(binding.get("principal"), "terraform.tfplan")
                for row in infra["iam_roles_matrix"]:
                    self.assertNotEqual(row.get("principal"), "member")
                    self.assertNotEqual(row.get("file"), "terraform.tfplan")

    def test_unparseable_child_module_recorded(self) -> None:
        """Unparseable child-module .tf files are logged, recorded in unparsed files, and surface in POA&M."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            (root / ".git").mkdir()
            mod_dir = root / "modules" / "broken_mod"
            mod_dir.mkdir(parents=True)
            (mod_dir / "main.tf").write_text(
                'resource "google_storage_bucket" "b" {\n  name = "unclosed"\n',
                encoding="utf-8",
            )
            bp_dir = root / "blueprints" / "il5" / "app"
            bp_dir.mkdir(parents=True)
            (bp_dir / "main.tf").write_text(
                'module "broken" {\n  source = "../../../modules/broken_mod"\n}\n'
                'resource "google_project_service" "s" {\n  service = "iam.googleapis.com"\n}\n',
                encoding="utf-8",
            )
            with self.assertLogs("extract_system_data", level="WARNING"):
                inv = extract_system_data.extract_system_inventory(str(bp_dir))
            unparsed = inv["infrastructure_components"]["unparsed_terraform_files"]
            self.assertTrue(
                any("broken_mod" in str(u.get("path")) or "main.tf" in str(u.get("path")) for u in unparsed),
                f"Expected broken child module .tf in unparsed_terraform_files, got {unparsed}",
            )
            with file_helpers.poam_Scan_disabled() if hasattr(file_helpers, "poam_scan_disabled") else contextlib.nullcontext():
                poam_items = poam_rules.derive_poam_findings(inv, target_dir=str(bp_dir))
            self.assertTrue(
                any("could not be parsed" in str(item.get("title", "")) for item in poam_items),
                f"Expected unparsed child module to surface in POA&M, got {[i.get('title') for i in poam_items]}",
            )

    def test_govramp_label(self) -> None:
        """Engine emits 'GovRAMP High' instead of stale 'StateRAMP High'."""
        impact, baseline = extract_system_data._infer_regime_from_target_path(
            "blueprints/govramp/sample", Path("/tmp/blueprints/govramp/sample")
        )
        self.assertEqual(impact, "GovRAMP High")
        self.assertIn("GovRAMP", baseline or "")
        src_dir = _TESTS_DIR.parent / "src"
        for py_file in src_dir.rglob("*.py"):
            self.assertNotIn("StateRAMP High", py_file.read_text(encoding="utf-8"))

    def test_extract_module_decomposition_bounds(self) -> None:
        """extract_system_data.py <= 600 LOC and no function > 150 LOC or CC > 30 across B2 extraction modules."""
        import ast

        def _function_cc(fn_node: ast.AST) -> int:
            cc = 1
            for child in ast.walk(fn_node):
                if child is not fn_node and isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                if isinstance(
                    child,
                    (ast.If, ast.For, ast.AsyncFor, ast.While, ast.ExceptHandler, ast.IfExp, ast.Assert),
                ):
                    cc += 1
                elif isinstance(child, (ast.With, ast.AsyncWith)):
                    cc += len(child.items)
                elif isinstance(child, ast.BoolOp):
                    cc += len(child.values) - 1
                elif isinstance(child, ast.comprehension):
                    cc += 1 + len(child.ifs)
            return cc

        pkg_dir = _TESTS_DIR.parent / "src" / "compliance_engine"
        expected_files = (
            "extract_system_data.py",
            "_tf_hcl_helpers.py",
            "_tf_resource_ingestor.py",
            "_app_sbom_scanner.py",
            "_config_doc_discovery.py",
        )
        for fname in expected_files:
            fpath = pkg_dir / fname
            self.assertTrue(fpath.is_file(), f"Missing expected extraction module {fname}")
            text = fpath.read_text(encoding="utf-8")
            lines = text.splitlines()
            if fname == "extract_system_data.py":
                self.assertLessEqual(
                    len(lines),
                    600,
                    f"extract_system_data.py has {len(lines)} LOC (must be <= 600)",
                )
            tree = ast.parse(text, filename=fname)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    loc = (getattr(node, "end_lineno", node.lineno) - node.lineno) + 1
                    self.assertLessEqual(
                        loc,
                        150,
                        f"{fname}:{node.name} is {loc} LOC (must be <= 150)",
                    )
                    cc = _function_cc(node)
                    self.assertLessEqual(
                        cc,
                        30,
                        f"{fname}:{node.name} has CC={cc} (must be <= 30)",
                    )


if __name__ == "__main__":
    unittest.main()
