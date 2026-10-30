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

"""The ordered steps of `stellar guide`, `status` and `deploy`.

The catalog covers the prerequisites, Stage 0 and Stage 1, in the order of
the DDG. Each stage module holds its steps; a step that applies only to
some deployments says when in its `when`.
"""

from stellar_engine.deploy import model
from stellar_engine.deploy.catalog import pre
from stellar_engine.deploy.catalog import stage0
from stellar_engine.deploy.catalog import stage1

# The catalog stages in deployment order, with the title that `guide`
# heads each stage with and `status` puts in the title of each step.
STAGE_TITLES = {
    model.PRE_STAGE: "Prerequisites",
    stage0.STAGE: "Stage 0 - Bootstrap",
    stage1.STAGE: "Stage 1 - Resource Management",
}


def catalog() -> tuple[model.Step, ...]:
    """Returns every step in deployment order."""
    return (*pre.STEPS, *stage0.STEPS, *stage1.STEPS)
