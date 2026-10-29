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

"""Runs preflight checks and computes the exit status."""

from stellar_engine.preflight import checks
from stellar_engine.preflight import result


def run(ctx, check_functions=checks.ALL_CHECKS):
    """Runs every check in order and collects the results.

    A check that raises an unexpected error is reported as FAIL instead of
    aborting the run, so the operator always sees the full report.

    Args:
        ctx: A `checks.Context` shared by all checks.
        check_functions: Checks to run, in report order.

    Returns:
        A list of `result.CheckResult`.
    """
    results = []
    for check in check_functions:
        try:
            results.extend(check(ctx))
        except Exception as error:
            # Report the failure as a result instead of aborting the run.
            name = check.__name__.removeprefix("check_")
            results.append(
                result.CheckResult(
                    f"{name}.error",
                    result.Category.INTERNAL,
                    f"{name} check",
                    result.Status.FAIL,
                    f"The check failed with {type(error).__name__}: {error}",
                )
            )
    return results


def exit_code(results, strict=False):
    """Returns the process exit code for a set of results.

    Args:
        results: Results from `run`.
        strict: Whether warnings also fail the run.

    Returns:
        0 when nothing failed, otherwise 1.
    """
    failing = {result.Status.FAIL}
    if strict:
        failing.add(result.Status.WARN)
    return 1 if any(item.status in failing for item in results) else 0
