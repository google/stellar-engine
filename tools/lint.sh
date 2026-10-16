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

run_check "Boilerplate check" python3 tools/check_boilerplate.py "$PWD"

run_check "Terraform format" terraform fmt -recursive -check -diff "$PWD"

run_check "READMEs" python3 tools/check_documentation.py --no-show-summary modules fast blueprints

run_check "Links" python3 tools/check_links.py --no-show-summary "$PWD"

run_check "FAST Names" python3 tools/check_names.py --prefix-length=10 --failed-only fast/stages

run_check "Python formatting" yapf --style="{based_on_style: google, indent_width: 2, SPLIT_BEFORE_NAMED_ASSIGNS: false}" -p -d -r \
     tools/*.py \
     blueprints

run_check "Blueprint metadata" python3 tools/validate_metadata.py -v blueprints --verbose --failed-only

echo -- Version checks --
version_failed=0
while IFS= read -r -d '' vfile; do
  if ! grep -q 'required_version' "$vfile" || ! grep -q 'hashicorp/google' "$vfile"; then
    echo "Invalid versions.tf (missing required_version or hashicorp/google): $vfile"
    version_failed=1
  fi
done < <(find . -type f -name 'versions.tf' -print0)

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
