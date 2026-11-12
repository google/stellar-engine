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
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

TEST_COUNT=0
FAIL_COUNT=0

assert_equals() {
  local desc="$1"
  local expected="$2"
  local actual="$3"
  TEST_COUNT=$((TEST_COUNT + 1))
  if [[ "$expected" == "$actual" ]]; then
    echo "  [PASS] ${desc}"
  else
    echo "  [FAIL] ${desc} (expected '$expected', got '$actual')"
    FAIL_COUNT=$((FAIL_COUNT + 1))
  fi
}

echo "==> Running tools/tflint.sh Unit Tests"

if ! command -v tflint >/dev/null; then
  echo "  [SKIP] tflint is not installed; the CI tflint job runs these tests."
  exit 0
fi

TMP="$(mktemp -d)"
trap 'rm -rf "${TMP}"' EXIT

# Builds a minimal repository that uses the real script and configuration.
mkdir -p "${TMP}/tools" "${TMP}/fast/stage" "${TMP}/blueprints/bp" \
  "${TMP}/modules/own"
cp "${REPO_ROOT}/tools/tflint.sh" "${TMP}/tools/"
cp "${REPO_ROOT}/.tflint.hcl" "${TMP}/"
printf 'resource "null_resource" "good_name" {}\n' >"${TMP}/fast/stage/main.tf"
printf 'module "good-name" {\n  source = "../../modules/own"\n}\n' \
  >"${TMP}/blueprints/bp/main.tf"
printf 'resource "null_resource" "own" {}\n' >"${TMP}/modules/own/main.tf"

run() {
  local status=0
  bash "${TMP}/tools/tflint.sh" >"${TMP}/out.txt" 2>&1 || status=$?
  echo "${status}"
}

assert_equals "passes when every label follows the convention" "0" "$(run)"

printf 'resource "null_resource" "bad-name" {}\n' >"${TMP}/fast/stage/bad.tf"
assert_equals "fails on a resource label with a dash" "1" "$(run)"
rm "${TMP}/fast/stage/bad.tf"

printf 'module "bad_name" {\n  source = "../../modules/own"\n}\n' \
  >"${TMP}/blueprints/bp/bad.tf"
assert_equals "fails on a module label with an underscore" "1" "$(run)"
rm "${TMP}/blueprints/bp/bad.tf"

printf 'output "bad-output" {\n  value = 1\n}\n' >"${TMP}/modules/own/bad.tf"
assert_equals "fails on an output name with a dash" "1" "$(run)"
rm "${TMP}/modules/own/bad.tf"

rm -rf "${TMP}/fast" "${TMP}/blueprints" "${TMP}/modules"
mkdir -p "${TMP}/fast" "${TMP}/blueprints" "${TMP}/modules"
assert_equals "fails when no Terraform directory exists" "1" "$(run)"

echo ""
echo "Summary: ${TEST_COUNT} tests run, ${FAIL_COUNT} failures."
if [[ ${FAIL_COUNT} -gt 0 ]]; then
  exit 1
fi
