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

"""Checks the Private Services Access example of the FedRAMP Stage 2."""

import ipaddress
import itertools
import pathlib
import re
import unittest

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
_STAGE_DIR = _REPO_ROOT / "fast/stages-aw/2-networking-a-fedramp"

_CIDR = r"\d+\.\d+\.\d+\.\d+/\d+"
_PSA_ENTRY = re.compile(
    r"^(?P<comment>#?)\s*(?P<env>\w+)\s*=\s*\[\{\s*ranges\s*=\s*\{\s*"
    r'default\s*=\s*"(?P<cidr>' + _CIDR + r')"\s*\}\s*\}\]\s*$',
    re.MULTILINE,
)


def _psa_ranges(text):
    """Returns the psa_ranges example in text as env => network."""
    block = re.search(r"^#? ?psa_ranges = \{\n(.*?)^#? ?\}", text, re.S | re.M)
    if block is None:
        raise AssertionError("psa_ranges example not found")
    return {
        m.group("env"): ipaddress.ip_network(m.group("cidr"))
        for m in _PSA_ENTRY.finditer(block.group(1))
    }


class TestFedrampPsaRangesExample(unittest.TestCase):
    def setUp(self):
        self.sample = (_STAGE_DIR / "terraform.tfvars.sample").read_text(
            encoding="utf-8"
        )
        self.readme = (_STAGE_DIR / "README.md").read_text(encoding="utf-8")
        self.psa = _psa_ranges(self.sample)

    def test_sample_has_one_range_per_environment(self):
        self.assertEqual(set(self.psa), {"prod", "int", "test"})

    def test_sample_ranges_do_not_overlap_sample_subnets(self):
        # A Private Services Access range cannot overlap a subnet of the
        # VPC, so the example must stay clear of every sample subnet,
        # including the commented centralized egress ones.
        subnets = [
            ipaddress.ip_network(cidr)
            for cidr in re.findall(
                r"\b(?:ip_cidr_range|subnet_cidr|proxy_subnet_cidr|Prod|Int"
                r'|Test)\s*=\s*"(' + _CIDR + r')"',
                self.sample,
            )
        ]
        self.assertGreaterEqual(len(subnets), 12)
        for env, psa in self.psa.items():
            for subnet in subnets:
                self.assertFalse(
                    psa.overlaps(subnet),
                    f"psa_ranges.{env} {psa} overlaps subnet {subnet}",
                )

    def test_sample_ranges_do_not_overlap_each_other(self):
        for a, b in itertools.combinations(self.psa.values(), 2):
            self.assertFalse(a.overlaps(b), f"{a} overlaps {b}")

    def test_readme_example_matches_the_sample(self):
        self.assertEqual(_psa_ranges(self.readme), self.psa)

    def test_readme_names_the_blueprint_that_needs_the_connection(self):
        section = self.readme.split("## 7 Private services access", 1)[1]
        section = section.split("\n<p ", 1)[0]
        self.assertIn("`psa_ranges`", section)
        self.assertIn("blueprints/fedramp-high/postgresql", section)
        self.assertIn("`psc_config`", section)


if __name__ == "__main__":
    unittest.main()
