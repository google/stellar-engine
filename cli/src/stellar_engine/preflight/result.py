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

"""Result types shared by preflight checks and reports."""

import dataclasses
import enum


class Status(enum.StrEnum):
    """Outcome of one preflight check.

    PASS and FAIL are verified outcomes. WARN flags a risk that does not
    block the deployment. MANUAL marks a prerequisite that only a person can
    confirm. SKIP means the inputs needed to run the check were not given.
    """

    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"
    MANUAL = "manual"
    SKIP = "skip"


class Category(enum.StrEnum):
    """Groups checks in the report, in the order of `docs/ddg.md`."""

    TOOLS = "Local tools"
    IDENTITY = "Identity"
    ORGANIZATION = "Organization"
    IAM = "Organization IAM roles"
    BILLING = "Billing"
    PROJECT = "Bootstrap project"
    GROUPS = "Administrative groups"
    NAMING = "Prefix and region"
    SHARED_ORG = "Shared organization risks"
    MANUAL = "Manual confirmations"
    INTERNAL = "Preflight errors"


@dataclasses.dataclass(frozen=True)
class CheckResult:
    """Outcome of a single preflight check.

    Attributes:
        check_id: Stable identifier, for example `iam.roles/owner`.
        category: Report section the check belongs to.
        title: Short human-readable name of the check.
        status: Outcome of the check.
        detail: What the check found.
        remedy: How to fix a failure, often an exact command.
        doc: Repository-relative link to the matching documentation.
    """

    check_id: str
    category: Category
    title: str
    status: Status
    detail: str
    remedy: str | None = None
    doc: str | None = None

    def to_dict(self):
        """Returns a JSON-serializable representation."""
        data = dataclasses.asdict(self)
        data["category"] = self.category.value
        data["status"] = self.status.value
        return data
