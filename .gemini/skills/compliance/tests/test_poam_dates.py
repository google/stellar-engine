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

"""POA&M scheduled dates: user commitments are preserved, derived dates are never in the past."""

from datetime import datetime, timedelta
import unittest

from compliance_engine import file_helpers
from compliance_engine import poam_rules


class PoamDatesTest(unittest.TestCase):
    """normalize_poam_item and compute_poam_target_date."""

    def test_past_due_preserved(self) -> None:
        for status in ("Ongoing", "Open", "Delayed"):
            with self.subTest(status=status):
                item = poam_rules.normalize_poam_item(
                    {"control": "AC-2", "weakness_name": "Overdue", "status": status, "scheduled_completion_date": "2020-01-15"},
                    sys_abbr="SYS",
                    counter=1,
                    eff_date="2026-01-01",
                )
                self.assertEqual(item["sched_date"], "2020-01-15")

    def test_derived_target_date_never_past(self) -> None:
        today = datetime.now()
        expected = (today + timedelta(days=30)).strftime("%Y-%m-%d")
        self.assertEqual(file_helpers.compute_poam_target_date(30, "2001-01-01"), expected)
        future = today + timedelta(days=100)
        self.assertEqual(
            file_helpers.compute_poam_target_date(30, future), (future + timedelta(days=30)).strftime("%Y-%m-%d")
        )
        self.assertEqual(file_helpers.compute_poam_target_date(30, "not-a-date"), expected)


if __name__ == "__main__":
    unittest.main()
