#!/bin/bash

# Copyright 2023 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

FAILED_CHECKS=()

run_check() {
  local desc="$1"
  shift
  echo "-- $desc --"
  if "$@"; then
    echo "[PASS] $desc"
  else
    local status=$?
    echo "[FAIL] $desc (exit code $status)"
    FAILED_CHECKS+=("$desc")
  fi
}

run_check "Boilerplate check" uv run --locked python tools/check_boilerplate.py "$PWD"

run_check "Terraform format" terraform fmt -recursive -check -diff "$PWD"

run_check "Terraform lint" bash tools/tflint.sh -f compact

run_check "READMEs" uv run --locked python tools/check_documentation.py --no-show-summary modules fast blueprints

run_check "Links" uv run --locked python tools/check_links.py --no-show-summary "$PWD"

run_check "FAST Names" uv run --locked python tools/check_names.py --prefix-length=10 --failed-only fast/stages-aw

run_check "Python formatting" uv run --locked ruff format --check "$PWD"

run_check "Python lint" uv run --locked ruff check "$PWD"

run_check "Blueprint metadata" uv run --locked python tools/validate_metadata.py -v blueprints --verbose --failed-only

echo -- Version checks --
version_failed=0
while IFS= read -r -d '' vfile; do
  if ! grep -q 'required_version' "$vfile" || ! grep -q 'hashicorp/google' "$vfile"; then
    echo "Invalid versions.tf (missing required_version or hashicorp/google): $vfile"
    version_failed=1
  fi
done < <(find . \( -name '.git' -o -name '.terraform' -o -name '.venv' -o -name 'venv' -o -name 'node_modules' -o -name '__pycache__' \) -prune -o -type f -name 'versions.tf' -print0)

if [ $version_failed -eq 0 ]; then
  echo "[PASS] Version checks"
else
  echo "[FAIL] Version checks"
  FAILED_CHECKS+=("Version checks")
fi

echo ""
echo "================================================================================"
if [ ${#FAILED_CHECKS[@]} -eq 0 ]; then
  echo "All lint checks PASSED."
  exit 0
else
  echo "Lint checks FAILED: ${#FAILED_CHECKS[@]} check(s) reported errors:"
  for check in "${FAILED_CHECKS[@]}"; do
    echo "  - $check"
  done
  exit 1
fi
