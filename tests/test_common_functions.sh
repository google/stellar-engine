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

# 11. Test check_os_environment on supported and unsupported platforms
assert_true "check_os_environment succeeds on Linux" 'check_os_environment "Linux" "linux-gnu"'
assert_true "check_os_environment succeeds on macOS (Darwin)" 'check_os_environment "Darwin" "darwin23"'
assert_false "check_os_environment fails on MINGW64" 'check_os_environment "MINGW64_NT-10.0" "msys" 2>/dev/null'
assert_false "check_os_environment fails on CYGWIN" 'check_os_environment "CYGWIN_NT-10.0" "cygwin" 2>/dev/null'
assert_true "check_os_environment succeeds when OS=Windows_NT inside WSL2" 'OS="Windows_NT" WSL_DISTRO_NAME="Ubuntu" check_os_environment "Linux" "linux-gnu"'
assert_false "check_os_environment fails when OS=Windows_NT outside WSL2" 'OS="Windows_NT" WSL_DISTRO_NAME="" check_os_environment "Windows_NT" "win32" 2>/dev/null'
OS_ERR_OUTPUT=$(check_os_environment "MINGW64_NT-10.0" "msys" 2>&1 || true)
assert_true "check_os_environment error recommends WSL2" '[[ "$OS_ERR_OUTPUT" == *"WSL2"* ]]'

# Run a snippet in a fresh bash process that sources common-functions.sh
# without set -e, the same way deploy.sh runs. Stdin comes from $2 and the exit
# status lands in ISOLATED_STATUS.
COMMON_FUNCTIONS="${REPO_ROOT}/scripts/common-functions.sh"
run_isolated() {
  local snippet="$1"
  local input="${2:-}"
  set +e
  bash -c "source \"\$1\"; ${snippet}" _ "$COMMON_FUNCTIONS" \
    < <(printf '%s' "$input") >/dev/null 2>&1
  ISOLATED_STATUS=$?
  set -e
}

# 12. Test error_handler exits with the failing command's status
EH_DIR="${TMP_TEST_DIR}/error_handler"
mkdir -p "$EH_DIR"
run_isolated "SCRIPT_DIR='${EH_DIR}'; PREFIX=testpx; cleanup() { :; }
trap 'error_handler \$LINENO \$?' ERR
fail_with() { return \"\$1\"; }
fail_with 42
exit 0"
assert_equals "error_handler exits with the failing status when the trap passes it" "42" "$ISOLATED_STATUS"
assert_true "error_handler records the failed line in the state file" 'grep -q "^LAST_FAILED_LINE=" "${EH_DIR}/state/last_operation_testpx.env"'
assert_true "error_handler records deploy as the failed operation by default" 'grep -q "^LAST_FAILED_OPERATION=deploy$" "${EH_DIR}/state/last_operation_testpx.env"'

run_isolated "SCRIPT_DIR='${EH_DIR}'; cleanup() { :; }
trap 'error_handler \$LINENO' ERR
fail_with() { return \"\$1\"; }
fail_with 7
exit 0"
assert_equals "error_handler captures the failing status when the trap omits it" "7" "$ISOLATED_STATUS"

run_isolated "cleanup() { touch '${EH_DIR}/cleanup_ran'; }
trap 'error_handler \$LINENO \$?' ERR
false
exit 0"
assert_true "error_handler runs the cleanup function" '[[ -f "${EH_DIR}/cleanup_ran" ]]'

run_isolated "my_cleanup() { touch '${EH_DIR}/custom_cleanup_ran'; }
setup_error_handling my_cleanup
fail_with() { return \"\$1\"; }
fail_with 5
exit 0"
assert_equals "setup_error_handling installs the shared handler" "5" "$ISOLATED_STATUS"
assert_true "setup_error_handling runs the named cleanup function" '[[ -f "${EH_DIR}/custom_cleanup_ran" ]]'

# 13. Test handle_prompt with a "no" answer
HP_MARKER="${TMP_TEST_DIR}/handle_prompt_ran"
run_isolated "trap 'exit 99' ERR
handle_prompt 'Proceed?' 'touch ${HP_MARKER}' || true
exit 0" "n"$'\n'
assert_equals "handle_prompt with n returns without tripping the ERR trap" "0" "$ISOLATED_STATUS"
assert_false "handle_prompt with n does not run its commands" '[[ -f "$HP_MARKER" ]]'

run_isolated "handle_prompt 'Proceed?'" "n"$'\n'
assert_equals "handle_prompt with n returns 1" "1" "$ISOLATED_STATUS"

run_isolated "handle_prompt 'Proceed?' 'touch ${HP_MARKER}'" "s"$'\n'
assert_equals "handle_prompt with s returns 0" "0" "$ISOLATED_STATUS"
assert_false "handle_prompt with s does not run its commands" '[[ -f "$HP_MARKER" ]]'

run_isolated "handle_prompt 'Proceed?' 'touch ${HP_MARKER}'" "y"$'\n'
assert_equals "handle_prompt with y returns 0" "0" "$ISOLATED_STATUS"
assert_true "handle_prompt with y runs its commands" '[[ -f "$HP_MARKER" ]]'
rm -f "$HP_MARKER"

# 14. Test that only "yes" takes the then branch of handle_prompt_if
YES_BRANCH="if handle_prompt_if 'Proceed?'; then exit 10; else exit 20; fi"
run_isolated "$YES_BRANCH" "y"$'\n'
assert_equals "handle_prompt_if with y takes the yes branch" "10" "$ISOLATED_STATUS"
run_isolated "$YES_BRANCH" "n"$'\n'
assert_equals "handle_prompt_if with n takes the no branch" "20" "$ISOLATED_STATUS"
run_isolated "$YES_BRANCH" "s"$'\n'
assert_equals "handle_prompt_if with s takes the no branch" "20" "$ISOLATED_STATUS"

# 15. Test that NON_INTERACTIVE uses PROMPT_DEFAULT_RESPONSE without reading stdin
run_isolated "NON_INTERACTIVE=true; $YES_BRANCH" "y"$'\n'
assert_equals "NON_INTERACTIVE defaults to no for handle_prompt_if" "20" "$ISOLATED_STATUS"
run_isolated "NON_INTERACTIVE=true; handle_prompt 'Proceed?' 'touch ${HP_MARKER}'"
assert_equals "NON_INTERACTIVE defaults to no for handle_prompt" "1" "$ISOLATED_STATUS"
assert_false "NON_INTERACTIVE with the no default does not run commands" '[[ -f "$HP_MARKER" ]]'
run_isolated "NON_INTERACTIVE=true; PROMPT_DEFAULT_RESPONSE=y; $YES_BRANCH"
assert_equals "NON_INTERACTIVE with PROMPT_DEFAULT_RESPONSE=y takes the yes branch" "10" "$ISOLATED_STATUS"
run_isolated "NON_INTERACTIVE=true; PROMPT_DEFAULT_RESPONSE=y; handle_prompt 'Proceed?' 'touch ${HP_MARKER}'"
assert_equals "NON_INTERACTIVE with PROMPT_DEFAULT_RESPONSE=y returns 0" "0" "$ISOLATED_STATUS"
assert_true "NON_INTERACTIVE with PROMPT_DEFAULT_RESPONSE=y runs commands" '[[ -f "$HP_MARKER" ]]'

# 16. Test prompt_with_default
PWD_VALUE=""
PWD_VALUE=$(printf '\n' | { MY_VALUE=old; prompt_with_default MY_VALUE "Value" 2>/dev/null; echo "$MY_VALUE"; })
assert_equals "prompt_with_default keeps the current value on Enter" "old" "$PWD_VALUE"
PWD_VALUE=$(printf 'new\n' | { MY_VALUE=old; prompt_with_default MY_VALUE "Value" 2>/dev/null; echo "$MY_VALUE"; })
assert_equals "prompt_with_default replaces the current value with typed input" "new" "$PWD_VALUE"
PWD_VALUE=$(printf 'new' | { MY_VALUE=""; prompt_with_default MY_VALUE "Value" 2>/dev/null; echo "$MY_VALUE"; })
assert_equals "prompt_with_default accepts a final line without a newline" "new" "$PWD_VALUE"
assert_false "prompt_with_default fails when stdin closes without input" 'prompt_with_default MY_VALUE "Value" </dev/null 2>/dev/null'

# 17. Test the deploy.sh call sites of the prompt helpers. handle_prompt treats
# "skip" as success, so it must not guard a yes branch, and a "no" answer
# returns 1, so a bare call needs "|| true" to keep the ERR trap from firing.
DEPLOY_SH="${REPO_ROOT}/scripts/deploy.sh"
handle_prompt_guards_branch() {
  grep -nE "(if|\|\|) +handle_prompt [\"']" "$DEPLOY_SH"
}
bare_handle_prompt_without_true() {
  grep -E "^[[:space:]]*handle_prompt [\"']" "$DEPLOY_SH" \
    | grep -vE '\|\| true[[:space:]]*$'
}
assert_false "deploy.sh guards no yes branch with handle_prompt" 'handle_prompt_guards_branch'
assert_false "deploy.sh ends every bare handle_prompt call with || true" 'bare_handle_prompt_without_true'
# shellcheck disable=SC2016
assert_true "deploy.sh passes the failing status to error_handler" 'grep -qF "trap '"'"'error_handler \$LINENO \$?'"'"' ERR" "$DEPLOY_SH"'


# 18. Test load_config with valid and missing config.env
echo 'export CFG_VAR_1="ok"' > "${TMP_TEST_DIR}/config.env"
assert_true "load_config succeeds with valid config.env" 'load_config "$TMP_TEST_DIR" "CFG_VAR_1"'
assert_false "load_config fails when required var missing" 'load_config "$TMP_TEST_DIR" "MISSING_CFG_VAR" 2>/dev/null'
assert_false "load_config fails when directory has no config.env" 'load_config "${TMP_TEST_DIR}/nonexistent" "CFG_VAR_1" 2>/dev/null'

# 19. Test command_exists and retry_command
assert_true "command_exists succeeds for bash" 'command_exists bash'
assert_false "command_exists fails for nonexistent binary" 'command_exists nonexistent_binary_xyz_123'
assert_true "retry_command succeeds on passing command" 'retry_command 2 0 true'
assert_false "retry_command fails after max attempts" 'retry_command 2 0 false 2>/dev/null'

# 20. Test gcloud_safe, terraform_safe, check_prerequisites, check_gcp_quotas, resource_exists, safe_delete
export GCLOUD_CALL_LOG="${TMP_TEST_DIR}/gcloud_calls.log"
: > "$GCLOUD_CALL_LOG"
gcloud() {
  echo "$*" >> "$GCLOUD_CALL_LOG"
  if [[ "$*" == *"missing-res"* ]]; then return 1; fi
  if [[ "${1:-}" == "org-policies" && "${2:-}" == "list-custom-constraints" ]]; then
    echo "custom.myConstraint"
    return 0
  fi
  return 0
}
terraform() { return 0; }
export -f gcloud terraform
export GCLOUD_RETRY_DELAY=0 TERRAFORM_RETRY_DELAY=0
assert_true "gcloud_safe succeeds with mocked gcloud" 'gcloud_safe version >/dev/null 2>&1'
assert_true "terraform_safe succeeds with mocked terraform" 'terraform_safe version >/dev/null 2>&1'
assert_true "check_prerequisites succeeds with mocked gcloud and terraform" 'check_prerequisites >/dev/null 2>&1'
assert_true "check_gcp_quotas succeeds with mocked gcloud" 'check_gcp_quotas "test-proj" >/dev/null 2>&1'
for rtype in project org-policy custom-constraint storage-bucket iam-role; do
  assert_true "resource_exists succeeds for ${rtype}" "resource_exists '${rtype}' 'custom.myConstraint'"
  assert_true "safe_delete succeeds for existing ${rtype}" "safe_delete '${rtype}' 'custom.myConstraint' >/dev/null 2>&1"
done
assert_true "safe_delete records gcloud projects delete command" 'grep -q "projects delete custom.myConstraint --quiet" "$GCLOUD_CALL_LOG"'
: > "$GCLOUD_CALL_LOG"
assert_true "safe_delete skips deletion when resource does not exist" 'safe_delete "project" "missing-res" >/dev/null 2>&1'
assert_false "safe_delete does not invoke projects delete for missing resource" 'grep -q "projects delete missing-res" "$GCLOUD_CALL_LOG"'
assert_false "resource_exists fails for unknown type" 'resource_exists "invalid-type" "res" 2>/dev/null'

# 21. Test wait_for_consistency, display_header, cleanup, promptUser, confirm_destructive_operation
assert_true "wait_for_consistency succeeds with 0s delay" 'wait_for_consistency "op" 0 >/dev/null 2>&1'
assert_true "display_header prints banner" 'display_header "Test" "Desc" >/dev/null 2>&1'
assert_true "cleanup succeeds" 'cleanup >/dev/null 2>&1'
PROMPT_MARKER="${TMP_TEST_DIR}/prompt_executed"
rm -f "$PROMPT_MARKER"
assert_true "promptUser returns 0 in NON_INTERACTIVE=true with y default" 'NON_INTERACTIVE=true PROMPT_DEFAULT_RESPONSE=y promptUser "Proceed?" "touch $PROMPT_MARKER" >/dev/null 2>&1'
assert_true "promptUser executed command when response is y" '[[ -f "$PROMPT_MARKER" ]]'
rm -f "$PROMPT_MARKER"
assert_false "promptUser returns 1 in NON_INTERACTIVE=true with n default" 'NON_INTERACTIVE=true PROMPT_DEFAULT_RESPONSE=n promptUser "Proceed?" "touch $PROMPT_MARKER" >/dev/null 2>&1'
assert_true "promptUser did not execute command when response is n" '[[ ! -f "$PROMPT_MARKER" ]]'
assert_false "confirm_destructive_operation fails safe in NON_INTERACTIVE=true" 'NON_INTERACTIVE=true confirm_destructive_operation "Delete all" >/dev/null 2>&1'
assert_true "confirm_destructive_operation succeeds when user types DELETE" 'NON_INTERACTIVE=false confirm_destructive_operation "Delete all" <<<"DELETE" >/dev/null 2>&1'
assert_false "confirm_destructive_operation cancels when user types no" 'NON_INTERACTIVE=false confirm_destructive_operation "Delete all" <<<"no" >/dev/null 2>&1'

echo ""
echo "Summary: ${TEST_COUNT} shell unit tests run, ${FAIL_COUNT} failures."

if [[ ${FAIL_COUNT} -gt 0 ]]; then
  exit 1
fi
exit 0
