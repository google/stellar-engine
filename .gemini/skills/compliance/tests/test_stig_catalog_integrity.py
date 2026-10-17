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

"""Integrity tests for config/stig_catalog.json against DISA library fixtures."""

import ast
import json
from pathlib import Path
import re
import tempfile
import unittest

from compliance_engine import stig_resolver


SKILL_DIR = Path(__file__).resolve().parent.parent
CATALOG_PATH = SKILL_DIR / "config" / "stig_catalog.json"
RESOLVER_PATH = SKILL_DIR / "src" / "compliance_engine" / "stig_resolver.py"
PTA_TEMPLATE_PATH = SKILL_DIR / "templates" / "pta" / "Path_to_Authorization_Template.md"
DISA_LISTING_PATH = Path(__file__).resolve().parent / "fixtures" / "disa_library_listing.txt"


def _load_disa_listing() -> dict[tuple[str, str], dict[str, str]]:
    """Loads the DISA library fixture keyed by (disa_library_file, version)."""
    entries: dict[tuple[str, str], dict[str, str]] = {}
    for raw_line in DISA_LISTING_PATH.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 5:
            continue
        fname, ver, bench_date, status_raw, title = parts[:5]
        status = "sunset" if status_raw.startswith("sunset:") else status_raw
        sunset_date = status_raw.split(":", 1)[1] if status_raw.startswith("sunset:") else ""
        entries[(fname, ver)] = {
            "disa_library_file": fname,
            "version": ver,
            "release_date": bench_date,
            "status": status,
            "sunset_date": sunset_date,
            "title": title,
        }
    return entries


class TestStigCatalogIntegrity(unittest.TestCase):
    """Verifies every STIG catalog entry matches the DISA library fixture and resolver uses catalog versions."""

    def test_versions_in_disa_listing(self) -> None:
        """Every catalog entry version and release_date matches the DISA library fixture."""
        listing = _load_disa_listing()
        self.assertGreater(len(listing), 20)
        catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))

        self.assertEqual(catalog.get("library_edition"), "U_SRG-STIG_Library_October_2026")
        self.assertNotIn("last_updated", catalog)

        stigs = catalog.get("stigs", {})
        self.assertEqual(stigs["kubernetes"]["version"], "V2R6")
        self.assertEqual(stigs["database_srg"]["version"], "V4R6")

        for slug, entry in stigs.items():
            with self.subTest(slug=slug):
                self.assertNotIn("latest_benchmark_version", entry)
                fname = entry.get("disa_library_file")
                ver = entry.get("version")
                rdate = entry.get("release_date")
                status = entry.get("status")
                self.assertTrue(fname, f"{slug} missing disa_library_file")
                self.assertRegex(str(ver), r"^V\d+R\d+$", f"{slug} version must be uppercase V{{n}}R{{m}}")
                self.assertIn((fname, ver), listing, f"{slug} ({fname}, {ver}) not found in DISA listing fixture")
                ref = listing[(fname, ver)]
                self.assertEqual(rdate, ref["release_date"], f"{slug} release_date mismatch")
                self.assertEqual(status, ref["status"], f"{slug} status mismatch")
                if status == "sunset":
                    self.assertEqual(entry.get("sunset_date"), ref["sunset_date"], f"{slug} sunset_date mismatch")

    def test_resolver_has_no_literal_versions(self) -> None:
        """stig_resolver.py contains no hardcoded benchmark version literals in evaluation logic."""
        source = RESOLVER_PATH.read_text(encoding="utf-8")
        tree = ast.parse(source)
        ver_re = re.compile(r"^[vV]\d+R\d+$")
        offenders: list[str] = []

        for top_node in tree.body:
            if isinstance(top_node, ast.FunctionDef) and top_node.name == "parse_version_string":
                continue
            for node in ast.walk(top_node):
                if isinstance(node, ast.Constant) and isinstance(node.value, str):
                    if ver_re.match(node.value.strip()):
                        offenders.append(f"line {node.lineno}: {node.value!r}")

        self.assertEqual(offenders, [], f"Hardcoded STIG version literals in stig_resolver.py: {offenders}")

    def test_foundational_entries(self) -> None:
        """Foundational output lists Mission Owner OS (V1R3) and Network (V1R2) SRGs; no CC SRG V1R5."""
        listing = _load_disa_listing()
        with tempfile.TemporaryDirectory() as tmp:
            resolver = stig_resolver.StigResolver(target_dir=tmp, config={}, update_mode="offline")
            foundational = resolver.evaluate_applicable_stigs({})

        slugs = [item["slug"] for item in foundational]
        self.assertEqual(
            slugs,
            ["cloud_computing_mo_os_srg", "cloud_computing_mo_network_srg"],
        )
        by_slug = {item["slug"]: item for item in foundational}
        self.assertEqual(by_slug["cloud_computing_mo_os_srg"]["version"], "V1R3")
        self.assertEqual(by_slug["cloud_computing_mo_network_srg"]["version"], "V1R2")

        for slug, item in by_slug.items():
            entry = resolver.get_stig_entry(slug)
            self.assertIsNotNone(entry)
            self.assertIn((entry["disa_library_file"], item["version"]), listing)

        pta_text = PTA_TEMPLATE_PATH.read_text(encoding="utf-8")
        self.assertNotIn("Cloud Computing SRG (CC SRG)** | `V1R5`", pta_text)
        self.assertNotIn("V1R5", pta_text)


if __name__ == "__main__":
    unittest.main()
