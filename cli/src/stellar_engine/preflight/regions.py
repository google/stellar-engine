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

"""Assured Workloads regions supported by each compliance regime.

Source: https://cloud.google.com/assured-workloads/docs/locations, checked on
2026-10-20. Update this table when Google adds regions.
"""

import enum


class Regime(enum.StrEnum):
    """Compliance regimes accepted by `assured_workloads.regime` in Stage 0."""

    IL2 = "IL2"
    IL4 = "IL4"
    IL5 = "IL5"
    FEDRAMP_MODERATE = "FEDRAMP_MODERATE"
    FEDRAMP_HIGH = "FEDRAMP_HIGH"
    COMPLIANCE_REGIME_UNSPECIFIED = "COMPLIANCE_REGIME_UNSPECIFIED"


LOCATIONS_DOC = "https://cloud.google.com/assured-workloads/docs/locations"

_FEDRAMP_REGIONS = frozenset(
    {
        "us-central1",
        "us-east1",
        "us-east4",
        "us-east5",
        "us-south1",
        "us-west1",
        "us-west2",
        "us-west3",
        "us-west4",
    }
)

_IMPACT_LEVEL_REGIONS = _FEDRAMP_REGIONS - {"us-east5", "us-south1"}

SUPPORTED_REGIONS = {
    Regime.FEDRAMP_HIGH: _FEDRAMP_REGIONS,
    Regime.FEDRAMP_MODERATE: _FEDRAMP_REGIONS,
    Regime.IL4: _IMPACT_LEVEL_REGIONS,
    Regime.IL5: _IMPACT_LEVEL_REGIONS,
}


def supported_regions(regime):
    """Returns the regions documented for a regime.

    Args:
        regime: A regime name, such as `IL5`.

    Returns:
        A frozenset of region names, or None when the regime has no recorded
        table, such as IL2, CJIS, or COMPLIANCE_REGIME_UNSPECIFIED.
    """
    return SUPPORTED_REGIONS.get(regime)
