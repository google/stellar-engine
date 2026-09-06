#!/bin/bash
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

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

echo "==> Running Shell Script Syntax Validation (bash -n)"

FAILED=0
TOTAL=0

while IFS= read -r -d '' script; do
  TOTAL=$((TOTAL + 1))
  if bash -n "$script" 2>/dev/null; then
    echo "  [PASS] ${script#"${REPO_ROOT}/"}"
  else
    echo "  [FAIL] ${script#"${REPO_ROOT}/"}"
    bash -n "$script" || true
    FAILED=$((FAILED + 1))
  fi
done < <(find "${REPO_ROOT}" -type f -name "*.sh" -not -path "*/.git/*" -not -path "*/.terraform/*" -print0)

echo ""
echo "Summary: ${TOTAL} shell scripts checked, ${FAILED} failures."

if [[ ${FAILED} -gt 0 ]]; then
  exit 1
fi
exit 0
