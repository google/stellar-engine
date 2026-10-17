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

"""STIG version precedence verified against fixture catalogs, not pinned catalog literals."""

import json
import os
import tempfile
import unittest

from compliance_engine import file_helpers
from compliance_engine import stig_resolver


class StigPrecedenceTest(unittest.TestCase):
    """Baseline catalog < cache < user override, for any catalog content."""

    def test_baseline_versions_come_from_catalog_file(self) -> None:
        with tempfile.TemporaryDirectory() as target:
            resolver = stig_resolver.StigResolver(target_dir=target)
            catalog = file_helpers.read_json_file(resolver.catalog_path)["stigs"]
            for slug in ("kubernetes", "database_srg"):
                with self.subTest(slug=slug):
                    self.assertEqual(
                        resolver.resolve_version(slug),
                        (stig_resolver.parse_version_string(catalog[slug]["version"]), "Authoritative Baseline"),
                    )

    def test_stig_precedence_uses_fixture_catalog(self) -> None:
        base = file_helpers.read_json_file(stig_resolver.CATALOG_PATH)
        for k8s_ver, db_ver in (("V9R9", "V8R1"), ("V2R3", "V4R2")):
            with self.subTest(kubernetes=k8s_ver, database_srg=db_ver):
                catalog = json.loads(json.dumps(base))
                catalog["stigs"]["kubernetes"]["version"] = k8s_ver
                catalog["stigs"]["database_srg"]["version"] = db_ver
                with tempfile.TemporaryDirectory() as tmp:
                    cat_path = os.path.join(tmp, "catalog.json")
                    with open(cat_path, "w", encoding="utf-8") as fh:
                        json.dump(catalog, fh)
                    target = os.path.join(tmp, "target")
                    os.makedirs(target)
                    resolver = stig_resolver.StigResolver(target_dir=target, catalog_path=cat_path)
                    self.assertEqual(resolver.resolve_version("kubernetes"), (k8s_ver, "Authoritative Baseline"))
                    self.assertEqual(resolver.resolve_version("database_srg"), (db_ver, "Authoritative Baseline"))
                    resolver.cache = {"stigs": {"kubernetes": {"version": "v7R7"}}}
                    self.assertEqual(resolver.resolve_version("kubernetes")[0], "V7R7")
                    override = stig_resolver.StigResolver(
                        target_dir=target,
                        catalog_path=cat_path,
                        config={"disa_stigs": {"version_overrides": {"kubernetes": "v6R6"}}},
                    )
                    override.cache = {"stigs": {"kubernetes": {"version": "v7R7"}}}
                    ver, src = override.resolve_version("kubernetes")
                    self.assertEqual(ver, "V6R6")
                    self.assertIn("User Override", src)


if __name__ == "__main__":
    unittest.main()
