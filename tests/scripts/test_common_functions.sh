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

# Source common functions
# shellcheck source=scripts/common-functions.sh
source "${REPO_ROOT}/scripts/common-functions.sh"

TEST_COUNT=0
FAIL_COUNT=0

assert_true() {
  local desc="$1"
  shift
  TEST_COUNT=$((TEST_COUNT + 1))
  if eval "$@"; then
    echo "  [PASS] ${desc}"
  else
    echo "  [FAIL] ${desc}"
    FAIL_COUNT=$((FAIL_COUNT + 1))
  fi
}

assert_false() {
  local desc="$1"
  shift
  TEST_COUNT=$((TEST_COUNT + 1))
  if ! eval "$@"; then
    echo "  [PASS] ${desc}"
  else
    echo "  [FAIL] ${desc}"
    FAIL_COUNT=$((FAIL_COUNT + 1))
  fi
}

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

echo "==> Running scripts/common-functions.sh Unit Tests"

# 1. Test validate_env_vars with all variables present
export TEST_VAR_A="val1"
export TEST_VAR_B="val2"
assert_true "validate_env_vars succeeds when variables exist" 'validate_env_vars "TEST_VAR_A" "TEST_VAR_B"'

# 2. Test validate_env_vars with missing variable
unset TEST_VAR_C || true
assert_false "validate_env_vars fails when a variable is missing" 'validate_env_vars "TEST_VAR_A" "TEST_VAR_C" 2>/dev/null'

# 3. Test validate_env_vars with empty variable
export TEST_VAR_EMPTY=""
assert_false "validate_env_vars fails when a variable is empty string" 'validate_env_vars "TEST_VAR_EMPTY" 2>/dev/null'

# 4. Test log_info output contains [INFO] tag
INFO_OUTPUT=$(log_info "Test info message" 2>&1)
assert_true "log_info outputs [INFO] tag" '[[ "$INFO_OUTPUT" == *"[INFO]"* ]]'

# 5. Test log_warn output contains [WARN] tag
WARN_OUTPUT=$(log_warn "Test warning message" 2>&1)
assert_true "log_warn outputs [WARN] tag" '[[ "$WARN_OUTPUT" == *"[WARN]"* ]]'

# 6. Test log_error output contains [ERROR] tag
ERROR_OUTPUT=$(log_error "Test error message" 2>&1)
assert_true "log_error outputs [ERROR] tag" '[[ "$ERROR_OUTPUT" == *"[ERROR]"* ]]'

# 7. Test log_debug when DEBUG=true
DEBUG="true"
DEBUG_OUTPUT=$(log_debug "Test debug message" 2>&1)
assert_true "log_debug outputs [DEBUG] when DEBUG=true" '[[ "$DEBUG_OUTPUT" == *"[DEBUG]"* ]]'

# 8. Test log_debug when DEBUG=false
DEBUG="false"
DEBUG_OUTPUT_EMPTY=$(log_debug "Test debug message" 2>&1 || true)
assert_equals "log_debug outputs nothing when DEBUG=false" "" "$DEBUG_OUTPUT_EMPTY"

# 9. Test backup_config
TMP_TEST_DIR=$(mktemp -d)
trap 'rm -rf "$TMP_TEST_DIR"' EXIT

SAMPLE_CONFIG="${TMP_TEST_DIR}/sample.env"
echo "KEY=VALUE" > "$SAMPLE_CONFIG"
BACKUP_DIR="${TMP_TEST_DIR}/backups"

assert_true "backup_config succeeds for existing file" 'backup_config "$SAMPLE_CONFIG" "$BACKUP_DIR" >/dev/null'
BACKUP_FILE=$(find "$BACKUP_DIR" -name "sample.env.backup.*" | head -n 1)
assert_true "backup file was created" '[[ -f "$BACKUP_FILE" ]]'
BACKUP_CONTENT=$(cat "$BACKUP_FILE")
assert_equals "backup file contains original contents" "KEY=VALUE" "$BACKUP_CONTENT"

# 10. Test backup_config with non-existent file
assert_false "backup_config fails for non-existent file" 'backup_config "${TMP_TEST_DIR}/nonexistent.env" "$BACKUP_DIR" 2>/dev/null'

echo ""
echo "Summary: ${TEST_COUNT} shell unit tests run, ${FAIL_COUNT} failures."

if [[ ${FAIL_COUNT} -gt 0 ]]; then
  exit 1
fi
exit 0
