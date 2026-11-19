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

COMMON_FUNCTIONS="${REPO_ROOT}/scripts/common-functions.sh"
DESTROY="${REPO_ROOT}/scripts/destroy.sh"
RESTORE="${REPO_ROOT}/scripts/restore.sh"
SANDBOX="${REPO_ROOT}/tools/create_e2e_sandbox.sh"
MOCKS="${REPO_ROOT}/generate-mocks.sh"

TEST_COUNT=0
FAIL_COUNT=0

check() {
  local desc="$1"
  shift
  TEST_COUNT=$((TEST_COUNT + 1))
  if "$@"; then
    echo "  [PASS] ${desc}"
  else
    echo "  [FAIL] ${desc}"
    FAIL_COUNT=$((FAIL_COUNT + 1))
  fi
}

check_not() {
  local desc="$1"
  shift
  TEST_COUNT=$((TEST_COUNT + 1))
  if ! "$@"; then
    echo "  [PASS] ${desc}"
  else
    echo "  [FAIL] ${desc}"
    FAIL_COUNT=$((FAIL_COUNT + 1))
  fi
}

check_equals() {
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

echo "==> Running automation script tests"

TMP_TEST_DIR=$(mktemp -d)
trap 'rm -rf "$TMP_TEST_DIR"' EXIT

# 1. destroy.sh assigns variables without eval
check_not "destroy.sh does not call eval" \
  grep -qE '(^|[;&|[:space:]])eval[[:space:]]' "$DESTROY"

# 2. The config prompts of destroy.sh store typed input literally. The block
# between the two anchor lines runs here against the shared functions, with
# one hostile answer per prompt on stdin.
PROMPT_BLOCK="${TMP_TEST_DIR}/prompt_block.sh"
sed -n '/^    gcloud organizations list$/,/^    echo "--- Configuration Summary ---"$/p' "$DESTROY" |
  sed '1d;$d' > "$PROMPT_BLOCK"
PROMPT_COUNT=$(grep -c 'Enter your\|Enter the' "$PROMPT_BLOCK" || true)
check "destroy.sh config prompt block is found" [ "$PROMPT_COUNT" -gt 0 ]

MARKER="${TMP_TEST_DIR}/injected"
QUOTE_ANSWER="x\"; touch ${MARKER}; echo \""
SUBST_ANSWER="\$(touch ${MARKER})"
ANSWERS="${TMP_TEST_DIR}/answers"
{
  printf '%s\n' "$QUOTE_ANSWER" "$SUBST_ANSWER"
  for ((i = 2; i < PROMPT_COUNT; i++)); do
    printf 'value-%s\n' "$i"
  done
} > "$ANSWERS"

VALUES="${TMP_TEST_DIR}/values"
set +e
bash -c 'source "$1"; source "$2"; printf "%s\n" "$BILLING_ACCOUNT" "$BOOTSTRAP_PROJECT_ID" > "$3"' \
  _ "$COMMON_FUNCTIONS" "$PROMPT_BLOCK" "$VALUES" < "$ANSWERS" > /dev/null 2>&1
PROMPT_STATUS=$?
set -e
check_equals "destroy.sh config prompts complete" "0" "$PROMPT_STATUS"
check_not "destroy.sh config prompts do not execute typed input" [ -e "$MARKER" ]
check_equals "destroy.sh config prompts keep double quotes and semicolons" \
  "$QUOTE_ANSWER" "$(sed -n 1p "$VALUES" 2> /dev/null)"
check_equals "destroy.sh config prompts keep command substitutions" \
  "$SUBST_ANSWER" "$(sed -n 2p "$VALUES" 2> /dev/null)"

set +e
bash -c 'source "$1"; source "$2"; exit 0' _ "$COMMON_FUNCTIONS" "$PROMPT_BLOCK" \
  < /dev/null > /dev/null 2>&1
EOF_STATUS=$?
set -e
check_equals "destroy.sh config prompts stop when stdin closes" "1" "$EOF_STATUS"

# 3. mark_stage_complete sets the session flag and persists it
STAGE_FUNCTION="${TMP_TEST_DIR}/mark_stage_complete.sh"
sed -n '/^mark_stage_complete() {$/,/^}$/p' "$DESTROY" > "$STAGE_FUNCTION"
STAGE_FLAG=$(bash -c 'log_info() { :; }; source "$1"; SCRIPT_DIR="$2"; PREFIX=testpx
mark_stage_complete STAGE_2; printf "%s" "${STAGE_2_DESTROYED:-}"' _ "$STAGE_FUNCTION" "$TMP_TEST_DIR")
check_equals "mark_stage_complete sets the stage flag" "true" "$STAGE_FLAG"
check "mark_stage_complete persists the stage flag" \
  grep -qx 'STAGE_2_DESTROYED=true' "${TMP_TEST_DIR}/state/last_operation_testpx.env"

# 4. restore.sh has no import with a placeholder key and no resource ID
check_not "restore.sh has no terraform import with a literal {} key" \
  grep -qF '[\"{}\"]' "$RESTORE"

# 5. create_e2e_sandbox.sh creates main.tf with touch
# shellcheck disable=SC2016  # the pattern is the literal script line
check "create_e2e_sandbox.sh creates main.tf with touch" \
  grep -qxF 'touch "${DEST}/main.tf"' "$SANDBOX"

# 6. generate-mocks.sh only writes into stage directories that exist
STAGE_PATHS=$(grep -oE 'fast/stages-aw/[^/"[:space:]]+' "$MOCKS" | sort -u)
check "generate-mocks.sh references stage directories" [ -n "$STAGE_PATHS" ]
while IFS= read -r stage_path; do
  check "generate-mocks.sh target ${stage_path} exists" [ -d "${REPO_ROOT}/${stage_path}" ]
done <<< "$STAGE_PATHS"

echo ""
echo "Summary: ${TEST_COUNT} shell unit tests run, ${FAIL_COUNT} failures."

if [[ ${FAIL_COUNT} -gt 0 ]]; then
  exit 1
fi
exit 0
