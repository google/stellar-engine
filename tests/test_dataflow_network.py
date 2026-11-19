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

"""Checks the Shared VPC networking of the Dataflow blueprint job."""

import pathlib
import re
import unittest

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
_DATAFLOW_DIR = _REPO_ROOT / "blueprints/il5/dataflow"


def _top_block(text, header):
    """Returns the top-level HCL block that starts with header."""
    match = re.search(re.escape(header) + r"\s*\{[\s\S]*?\n\}", text)
    if match is None:
        raise AssertionError(f"Block not found: {header}")
    return match.group(0)


class TestDataflowNetwork(unittest.TestCase):
    def test_job_derives_the_network_from_the_subnetwork(self):
        main_tf = (_DATAFLOW_DIR / "main.tf").read_text(encoding="utf-8")
        job = _top_block(main_tf, 'resource "google_dataflow_job" "job"')
        # The subnetwork lives in the Shared VPC host project, so the job
        # passes its complete URL and Dataflow derives the network from it.
        self.assertRegex(
            job,
            r"\n\s*subnetwork\s*=\s*"
            r"data\.google_compute_subnetwork\.subnetwork\.self_link\n",
        )
        # The network argument takes a name that Dataflow resolves in the
        # job project, which cannot address a Shared VPC host network.
        self.assertNotRegex(job, r"\n\s*network\s*=")


if __name__ == "__main__":
    unittest.main()
