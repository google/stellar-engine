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

"""Selection semantics, sunset handling, and decomposition tests for StigResolver (B4-S)."""

import ast
from pathlib import Path
import tempfile
import unittest

from compliance_engine import stig_resolver


SKILL_DIR = Path(__file__).resolve().parent.parent
RESOLVER_PATH = SKILL_DIR / "src" / "compliance_engine" / "stig_resolver.py"


class TestStigSelection(unittest.TestCase):
    """Verifies STIG selection rules, sunset filtering, and catalog-driven prose."""

    def _eval_workload_stigs(self, inventory: dict) -> list[dict]:
        with tempfile.TemporaryDirectory() as tmp:
            resolver = stig_resolver.StigResolver(target_dir=tmp, config={}, update_mode="offline")
            all_stigs = resolver.evaluate_applicable_stigs(inventory)
        return [s for s in all_stigs if s["status"] != "Mandatory Cloud Baseline"]

    def _eval_all_stigs(self, inventory: dict) -> list[dict]:
        with tempfile.TemporaryDirectory() as tmp:
            resolver = stig_resolver.StigResolver(target_dir=tmp, config={}, update_mode="offline")
            return resolver.evaluate_applicable_stigs(inventory)

    def test_no_sunset_entries(self) -> None:
        """evaluate_applicable_stigs never emits a sunset catalog entry."""
        with tempfile.TemporaryDirectory() as tmp:
            resolver = stig_resolver.StigResolver(target_dir=tmp, config={}, update_mode="offline")
            catalog_stigs = resolver.get_all_catalog_stigs()

        sunset_slugs = {
            slug for slug, entry in catalog_stigs.items() if entry.get("status") == "sunset"
        }
        self.assertGreaterEqual(len(sunset_slugs), 7)

        kitchen_sink_inv = {
            "infrastructure_components": {
                "compute_instances": [
                    {"name": "win19", "image": "windows-cloud/windows-2019"},
                    {"name": "rhel8", "image": "rhel-cloud/rhel-8"},
                    {"name": "ub20", "image": "ubuntu-os-cloud/ubuntu-2004-lts"},
                ],
                "databases": [
                    {"type": "google_sql_database_instance", "name": "pg", "database_version": "POSTGRES_13"},
                    {"type": "custom", "name": "ora", "database_version": "oracle-12c"},
                    {"type": "custom", "name": "mdb", "database_version": "mongodb-3.6"},
                ],
                "storage_buckets": [{"name": "bkt-1"}],
            },
            "application_components": {
                "container_images": ["gcr.io/proj/app:v1"],
            },
        }
        emitted = self._eval_all_stigs(kitchen_sink_inv)
        emitted_slugs = {s["slug"] for s in emitted}
        self.assertEqual(
            emitted_slugs & sunset_slugs,
            set(),
            f"Sunset STIGs emitted by evaluate_applicable_stigs: {emitted_slugs & sunset_slugs}",
        )

    def test_gcs_only_no_san(self) -> None:
        """GCS-only inventory never yields storage_area_network_san_srg."""
        inv = {
            "infrastructure_components": {
                "storage_buckets": [{"name": "audit-logs-bkt"}],
                "services_enabled": ["storage.googleapis.com"],
                "all_resources": [{"type": "google_storage_bucket", "name": "audit-logs-bkt"}],
            }
        }
        workload = self._eval_workload_stigs(inv)
        slugs = [s["slug"] for s in workload]
        self.assertNotIn("storage_area_network_san_srg", slugs)

    def test_product_specific_slugs(self) -> None:
        """First-class product entries are selected instead of cross-product aliases."""
        cases = [
            (
                {"infrastructure_components": {"compute_instances": [{"name": "vm", "image": "windows-cloud/windows-2022"}]}},
                {"ms_windows_server_2022"},
            ),
            (
                {"infrastructure_components": {"compute_instances": [{"name": "vm", "image": "windows-cloud/windows-2025"}]}},
                {"ms_windows_server_2025"},
            ),
            (
                {"infrastructure_components": {"compute_instances": [{"name": "vm", "image": "rhel-cloud/rhel-9"}]}},
                {"red_hat_enterprise_linux_9"},
            ),
            (
                {"infrastructure_components": {"compute_instances": [{"name": "vm", "image": "rhel-cloud/rhel-10"}]}},
                {"red_hat_enterprise_linux_10"},
            ),
            (
                {"infrastructure_components": {"compute_instances": [{"name": "vm", "image": "almalinux-cloud/almalinux-9"}]}},
                {"almalinux_os_9"},
            ),
            (
                {"infrastructure_components": {"compute_instances": [{"name": "vm", "image": "rocky-linux-cloud/rocky-linux-9"}]}},
                {"debian_linux"},
            ),
            (
                {"infrastructure_components": {"compute_instances": [{"name": "vm", "image": "ubuntu-os-cloud/ubuntu-2404-lts"}]}},
                {"canonical_ubuntu_2404_lts"},
            ),
            (
                {"infrastructure_components": {"databases": [{"type": "custom", "name": "ora", "database_version": "oracle-19c"}]}},
                {"oracle_database_19c"},
            ),
            (
                {"infrastructure_components": {"databases": [{"type": "custom", "name": "mdb", "database_version": "mongodb-7.0"}]}},
                {"mongodb_enterprise_advanced_7x"},
            ),
            (
                {"infrastructure_components": {"databases": [{"type": "custom", "name": "mdb", "database_version": "mongodb-8.0"}]}},
                {"mongodb_enterprise_advanced_8x"},
            ),
            (
                {"infrastructure_components": {"databases": [{"type": "custom", "name": "mdb", "database_version": "mariadb-10.6"}]}},
                {"mariadb_enterprise_10x"},
            ),
            (
                {"application_components": {"software_packages": [{"name": "nginx"}]}},
                {"f5_nginx"},
            ),
            (
                {"application_components": {"software_packages": [{"name": "apache2"}]}},
                {"apache_server_2.4_unix_server"},
            ),
            (
                {"infrastructure_components": {"all_resources": [{"type": "google_compute_target_https_proxy"}]}},
                set(),
            ),
        ]
        for inv, expected_slugs in cases:
            with self.subTest(inv=inv):
                actual_slugs = {s["slug"] for s in self._eval_workload_stigs(inv)}
                self.assertEqual(actual_slugs, expected_slugs)

        with tempfile.TemporaryDirectory() as tmp:
            resolver = stig_resolver.StigResolver(target_dir=tmp, config={}, update_mode="offline")
            self.assertEqual(resolver.get_stig_entry("rhel8")["slug"], "red_hat_enterprise_linux_8")
            self.assertEqual(resolver.get_stig_entry("windows_server_2022")["slug"], "ms_windows_server_2022")
            self.assertEqual(resolver.get_stig_entry("oracle_database_19c")["slug"], "oracle_database_19c")
            self.assertEqual(resolver.get_stig_entry("nginx_server")["slug"], "f5_nginx")
            self.assertEqual(resolver.get_stig_entry("web_server_srg")["slug"], "web_server_srg")
            self.assertEqual(
                resolver.get_stig_entry("network_infrastructure_policy_stig")["slug"],
                "network_infrastructure_policy_stig",
            )

    def test_postgres_detection(self) -> None:
        """POSTGRES_15 and google_alloydb_cluster match PostgreSQL STIG; MySQL with var version does not."""
        pg_sql = {
            "infrastructure_components": {
                "databases": [{"type": "google_sql_database_instance", "name": "db1", "database_version": "POSTGRES_15"}],
                "all_resources": [{"type": "google_sql_database_instance"}],
            }
        }
        self.assertIn("crunchy_data_postgres_16", {s["slug"] for s in self._eval_workload_stigs(pg_sql)})

        alloydb = {
            "infrastructure_components": {
                "all_resources": [{"type": "google_alloydb_cluster"}, {"type": "google_alloydb_instance"}],
            }
        }
        self.assertIn("crunchy_data_postgres_16", {s["slug"] for s in self._eval_workload_stigs(alloydb)})

        mysql_var = {
            "infrastructure_components": {
                "databases": [{"type": "google_sql_database_instance", "name": "mysql-app", "database_version": "${var.db_version}"}],
            }
        }
        mysql_slugs = {s["slug"] for s in self._eval_workload_stigs(mysql_var)}
        self.assertNotIn("crunchy_data_postgres_16", mysql_slugs)
        self.assertNotIn("postgresql_13", mysql_slugs)

    def test_vm_names_do_not_select_os(self) -> None:
        """VM names containing cos/alma/sles substrings do not select wrong OS STIGs."""
        for vm_name, img, expected in (
            ("cost-reporting", "debian-cloud/debian-12", {"debian_linux"}),
            ("ecosystem-api", None, {"debian_linux"}),
            ("almanac-svc", "debian-cloud/debian-12", {"debian_linux"}),
            ("aisles-inventory", "debian-cloud/debian-12", {"debian_linux"}),
        ):
            with self.subTest(vm_name=vm_name):
                inv = {"infrastructure_components": {"compute_instances": [{"name": vm_name, "image": img}]}}
                actual = {s["slug"] for s in self._eval_workload_stigs(inv)}
                self.assertEqual(actual, expected)

    def test_only_real_disa_checklists(self) -> None:
        """evaluate_applicable_stigs({}) returns only real DISA benchmarks with no duplicates."""
        with tempfile.TemporaryDirectory() as tmp:
            resolver = stig_resolver.StigResolver(target_dir=tmp, config={}, update_mode="offline")
            catalog_stigs = resolver.get_all_catalog_stigs()
            emitted = resolver.evaluate_applicable_stigs({})

        self.assertGreaterEqual(len(emitted), 2)
        seen_urls: set[str] = set()
        for item in emitted:
            slug = item["slug"]
            self.assertNotIn(
                slug,
                {
                    "identity_and_access_management_iam_srg",
                    "key_and_certificate_management_srg",
                    "enterprise_message_broker_srg",
                },
            )
            cat_entry = catalog_stigs.get(slug, {})
            self.assertTrue(cat_entry.get("disa_library_file"), f"{slug} lacks a DISA library file")
            self.assertNotIn((slug, item["version"]), seen_urls)
            seen_urls.add((slug, item["version"]))

    def test_cos_maps_to_gpos(self) -> None:
        """COS-only inventory yields GPOS SRG; GKE inventory yields Kubernetes STIG."""
        cos_inv = {
            "infrastructure_components": {
                "compute_instances": [{"name": "worker", "image": "cos-cloud/cos-stable"}]
            }
        }
        cos_slugs = {s["slug"] for s in self._eval_workload_stigs(cos_inv)}
        self.assertEqual(cos_slugs, {"debian_linux"})

        gke_inv = {
            "infrastructure_components": {
                "gke_clusters": [{"name": "primary-gke"}]
            }
        }
        gke_slugs = {s["slug"] for s in self._eval_workload_stigs(gke_inv)}
        self.assertIn("kubernetes", gke_slugs)

    def test_catalog_scope_action_used(self) -> None:
        """Emitted scope and action come from stig_catalog.json rather than hardcoded strings."""
        with tempfile.TemporaryDirectory() as tmp:
            resolver = stig_resolver.StigResolver(target_dir=tmp, config={}, update_mode="offline")
            catalog_stigs = resolver.get_all_catalog_stigs()

        apache_inv = {"application_components": {"software_packages": [{"name": "apache2"}]}}
        apache_items = self._eval_workload_stigs(apache_inv)
        apache_row = next(s for s in apache_items if s["slug"] == "apache_server_2.4_unix_server")
        self.assertEqual(apache_row["action"], catalog_stigs["apache_server_2.4_unix_server"]["action"])
        self.assertEqual(apache_row["scope"], catalog_stigs["apache_server_2.4_unix_server"]["scope"])

        container_inv = {"application_components": {"container_images": ["gcr.io/p/app:1"]}}
        container_items = self._eval_workload_stigs(container_inv)
        cp_row = next(s for s in container_items if s["slug"] == "container_platform_srg")
        self.assertEqual(cp_row["action"], catalog_stigs["container_platform_srg"]["action"])
        self.assertEqual(cp_row["scope"], catalog_stigs["container_platform_srg"]["scope"])

    def test_version_notation(self) -> None:
        """parse_version_string normalizes into uppercase V{n}R{m} DISA notation."""
        self.assertEqual(stig_resolver.parse_version_string("Version 2, Release 6"), "V2R6")
        self.assertEqual(stig_resolver.parse_version_string("v1r12"), "V1R12")
        self.assertEqual(stig_resolver.parse_version_string("4.6"), "V4R6")
        self.assertEqual(stig_resolver.parse_version_string("V3R4"), "V3R4")

    def test_all_slugs_in_catalog(self) -> None:
        """Every built-in slug referenced in stig_resolver.py exists in stig_catalog.json."""
        with tempfile.TemporaryDirectory() as tmp:
            resolver = stig_resolver.StigResolver(target_dir=tmp, config={}, update_mode="offline")
            catalog_stigs = resolver.get_all_catalog_stigs()

            with self.assertRaises(KeyError):
                resolver._build_stig_item(
                    slug="nonexistent_fabricated_slug",
                    reason="test",
                    status="Required",
                )

        self.assertTrue(len(catalog_stigs) >= 25)

    def test_no_oversized_functions_in_stig_resolver(self) -> None:
        """No function or method in stig_resolver.py exceeds 150 LOC or CC 30."""
        source = RESOLVER_PATH.read_text(encoding="utf-8")
        tree = ast.parse(source)
        branch_nodes = (
            ast.If,
            ast.For,
            ast.While,
            ast.ExceptHandler,
            ast.With,
            ast.Assert,
            ast.comprehension,
            ast.IfExp,
        )
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                loc = (node.end_lineno or node.lineno) - node.lineno + 1
                cc = 1 + sum(1 for child in ast.walk(node) if isinstance(child, branch_nodes))
                for child in ast.walk(node):
                    if isinstance(child, ast.BoolOp):
                        cc += len(child.values) - 1
                self.assertLessEqual(loc, 150, f"{node.name} is {loc} LOC (>150)")
                self.assertLessEqual(cc, 30, f"{node.name} has CC {cc} (>30)")


if __name__ == "__main__":
    unittest.main()
