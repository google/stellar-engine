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

"""Checks how Stage 1 resolves the GCS location of lightweight tenants.

The plan-level behavior is covered by the offline Terraform test in
fast/stages-aw/1-resman/tests/plan.tftest.hcl. These checks run without
Terraform and guard the expression and the test inputs against regressions.
"""

import pathlib
import re
import unittest

_STAGE_DIR = (
    pathlib.Path(__file__).resolve().parents[1] / "fast/stages-aw/1-resman"
)
_TENANT_BUCKET_MODULES = (
    "tenant-core-gcs",
    "tenant-self-iac-gcs-outputs",
    "tenant-self-iac-gcs-states",
)


def _squash(text):
    """Returns text with every whitespace run removed."""
    return re.sub(r"\s+", "", text)


def _module_block(text, name):
    """Returns the top-level module block with the given name."""
    match = re.search(rf'\nmodule "{re.escape(name)}" \{{[\s\S]*?\n\}}', text)
    if match is None:
        raise AssertionError(f"Module not found: {name}")
    return match.group(0)


class TestResmanTenantGcsLocation(unittest.TestCase):
    def setUp(self):
        self.tenants_tf = (_STAGE_DIR / "branch-tenants.tf").read_text(
            encoding="utf-8"
        )

    def test_null_and_empty_locations_fall_back_to_primary_region(self):
        # coalesce skips both null and "", and try covers tenants that
        # omit the optional locations object.
        self.assertIn(
            "gcs_locations={fork,vinvar.tenants:k=>coalesce("
            "try(v.locations.gcs,null),var.regions.primary)}",
            _squash(self.tenants_tf),
        )

    def test_null_unsafe_comparison_is_not_reintroduced(self):
        # In Terraform null != "" is true, so this guard selects a null
        # location instead of the fallback.
        self.assertNotRegex(self.tenants_tf, r'locations\.gcs\s*!=\s*""')

    def test_tenant_buckets_only_read_the_resolved_location(self):
        for name in _TENANT_BUCKET_MODULES:
            with self.subTest(module=name):
                block = _module_block(self.tenants_tf, name)
                self.assertRegex(
                    block,
                    r"\n\s*location\s*="
                    r" local\.gcs_locations\[each\.value\.tenant\]\n",
                )
                self.assertIn(
                    'split("-", local.gcs_locations[each.value.tenant])',
                    block,
                )
                self.assertNotIn("locations.gcs", block)

    def test_terraform_test_covers_every_location_shape(self):
        plan_test = _squash(
            (_STAGE_DIR / "tests/plan.tftest.hcl").read_text(encoding="utf-8")
        )
        for shape in (
            'locations={gcs=null,kms="us-east4"}',
            'locations={gcs="",kms="us-east4"}',
            'locations={gcs="us-central1",kms="us-east4"}',
            "locations=null",
        ):
            with self.subTest(shape=shape):
                self.assertIn(shape, plan_test)


if __name__ == "__main__":
    unittest.main()
