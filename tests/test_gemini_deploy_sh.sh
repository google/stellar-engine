#!/bin/bash
# Copyright 2026 Google LLC
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

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
DEPLOY_SH="${REPO_ROOT}/blueprints/gemini-enterprise/deploy.sh"

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
    echo "  [FAIL] ${desc}"
    echo "    expected: ${expected}"
    echo "    actual:   ${actual}"
    FAIL_COUNT=$((FAIL_COUNT + 1))
  fi
}

assert_contains() {
  local desc="$1"
  local needle="$2"
  local haystack="$3"
  TEST_COUNT=$((TEST_COUNT + 1))
  if [[ "$haystack" == *"$needle"* ]]; then
    echo "  [PASS] ${desc}"
  else
    echo "  [FAIL] ${desc} (missing '${needle}')"
    FAIL_COUNT=$((FAIL_COUNT + 1))
  fi
}

assert_not_contains() {
  local desc="$1"
  local needle="$2"
  local haystack="$3"
  TEST_COUNT=$((TEST_COUNT + 1))
  if [[ "$haystack" != *"$needle"* ]]; then
    echo "  [PASS] ${desc}"
  else
    echo "  [FAIL] ${desc} (unexpected '${needle}')"
    FAIL_COUNT=$((FAIL_COUNT + 1))
  fi
}

echo "==> Running blueprints/gemini-enterprise/deploy.sh Unit Tests"

TMP_TEST_DIR=$(mktemp -d)
trap 'rm -rf "$TMP_TEST_DIR"' EXIT

# Source deploy.sh without executing main_menu (restoring nounset afterwards).
set +u
# shellcheck source=../blueprints/gemini-enterprise/deploy.sh
source "$DEPLOY_SH"
set -euo pipefail

# 1. update_tfvar_string escapes /, &, \, and quotes without corrupting comments.
TFVARS_FILE="${TMP_TEST_DIR}/terraform.tfvars"
cat > "$TFVARS_FILE" << 'EOF'
# prefix = "comment-keep"
other_prefix = "keep-other"
prefix = "old"
environment = "dev"
terraform_state_bucket = "old-bucket"
EOF

update_tfvar_string "$TFVARS_FILE" "prefix" 'a/b&c\d"e'
update_tfvar_string "$TFVARS_FILE" "environment" 'prod&1/2'
update_tfvar_string "$TFVARS_FILE" "terraform_state_bucket" 'my-bucket/sub&1'

UPDATED_TFVARS=$(cat "$TFVARS_FILE")
assert_contains "preserves comment line" '# prefix = "comment-keep"' "$UPDATED_TFVARS"
assert_contains "preserves other_prefix key" 'other_prefix = "keep-other"' "$UPDATED_TFVARS"
assert_contains "escapes special chars in prefix" 'prefix = "a/b&c\\d\"e"' "$UPDATED_TFVARS"
assert_contains "escapes & and / in environment" 'environment = "prod&1/2"' "$UPDATED_TFVARS"
assert_contains "escapes / and & in bucket" 'terraform_state_bucket = "my-bucket/sub&1"' "$UPDATED_TFVARS"

# 2. select_from_json_array validates integer bounds before $((...)) arithmetic.
SAMPLE_JSON='[{"name":"item-one"},{"name":"item-two"}]'
SEL1=$(select_from_json_array "$SAMPLE_JSON" "1" "name")
SEL2=$(select_from_json_array "$SAMPLE_JSON" "2" "name")
assert_equals "valid selection 1 returns first item" "item-one" "$SEL1"
assert_equals "valid selection 2 returns second item" "item-two" "$SEL2"

for bad_sel in 'a[0]' '$(echo pwn)' '1+1' '0' '08' '09' '010' '3' '-1' ''; do
  set +e
  BAD_OUT=$(select_from_json_array "$SAMPLE_JSON" "$bad_sel" "name" 2>&1)
  BAD_RC=$?
  set -e
  TEST_COUNT=$((TEST_COUNT + 1))
  if [[ $BAD_RC -ne 0 && -z "$BAD_OUT" ]]; then
    echo "  [PASS] rejects invalid selection '${bad_sel}'"
  else
    echo "  [FAIL] invalid selection '${bad_sel}' returned rc=${BAD_RC} out='${BAD_OUT}'"
    FAIL_COUNT=$((FAIL_COUNT + 1))
  fi
done

TEN_JSON='[{"name":"n1"},{"name":"n2"},{"name":"n3"},{"name":"n4"},{"name":"n5"},{"name":"n6"},{"name":"n7"},{"name":"n8"},{"name":"n9"},{"name":"n10"}]'
SEL10=$(select_from_json_array "$TEN_JSON" "10" "name")
assert_equals "valid selection 10 returns tenth item" "n10" "$SEL10"
set +e
BAD_010_OUT=$(select_from_json_array "$TEN_JSON" "010" "name" 2>&1)
BAD_010_RC=$?
set -e
TEST_COUNT=$((TEST_COUNT + 1))
if [[ $BAD_010_RC -ne 0 && -z "$BAD_010_OUT" ]]; then
  echo "  [PASS] rejects zero-padded 010 on 10-item array without octal coercion"
else
  echo "  [FAIL] zero-padded 010 returned rc=${BAD_010_RC} out='${BAD_010_OUT}'"
  FAIL_COUNT=$((FAIL_COUNT + 1))
fi

# 3. validate_schema_file_path enforces directory boundary including sibling prefixes.
BASE_WORK="${TMP_TEST_DIR}/work"
SIBLING_WORK="${TMP_TEST_DIR}/work-other"
mkdir -p "${BASE_WORK}/nested" "${SIBLING_WORK}"
printf '{}' > "${BASE_WORK}/schema.json"
printf '{}' > "${BASE_WORK}/nested/schema.json"
printf '{}' > "${SIBLING_WORK}/schema.json"

set +e
validate_schema_file_path "${BASE_WORK}/schema.json" "$BASE_WORK" >/dev/null 2>&1
RC_IN_BASE=$?
validate_schema_file_path "${BASE_WORK}/nested/schema.json" "$BASE_WORK" >/dev/null 2>&1
RC_IN_NESTED=$?
validate_schema_file_path "${SIBLING_WORK}/schema.json" "$BASE_WORK" >/dev/null 2>&1
RC_SIBLING=$?
validate_schema_file_path "${BASE_WORK}/../work/schema.json" "$BASE_WORK" >/dev/null 2>&1
RC_TRAVERSAL=$?
set -e

assert_equals "accepts schema inside base directory" "0" "$RC_IN_BASE"
assert_equals "accepts schema inside nested directory" "0" "$RC_IN_NESTED"
assert_equals "rejects sibling prefix directory" "1" "$RC_SIBLING"
assert_equals "rejects explicit parent traversal" "1" "$RC_TRAVERSAL"

# 4. curl auth header is passed via stdin (-K -) and never in argv.
STUB_BIN="${TMP_TEST_DIR}/bin"
mkdir -p "$STUB_BIN"
CURL_ARGV_LOG="${TMP_TEST_DIR}/curl_argv.log"
CURL_STDIN_LOG="${TMP_TEST_DIR}/curl_stdin.log"
cat > "${STUB_BIN}/curl" << 'EOF'
#!/bin/bash
printf '%s\n' "$*" > "$CURL_ARGV_LOG"
cat > "$CURL_STDIN_LOG"
printf '{"ok":true}\n200\n'
EOF
chmod +x "${STUB_BIN}/curl"

SECRET_TOK="example-test-bearer-value"
PATH="${STUB_BIN}:${PATH}" \
  CURL_ARGV_LOG="$CURL_ARGV_LOG" \
  CURL_STDIN_LOG="$CURL_STDIN_LOG" \
  curl -s -K - "https://example.invalid" <<<"$(curl_auth_config "$SECRET_TOK")" >/dev/null

ARGV_RECORDED=$(cat "$CURL_ARGV_LOG")
STDIN_RECORDED=$(cat "$CURL_STDIN_LOG")
assert_contains "curl receives -K - flag" "-K -" "$ARGV_RECORDED"
assert_not_contains "curl argv omits bearer token" "$SECRET_TOK" "$ARGV_RECORDED"
assert_equals "curl stdin receives auth header config" "header = \"Authorization: Bearer ${SECRET_TOK}\"" "$STDIN_RECORDED"

# Static verification: deploy.sh must not pass Authorization: Bearer in argv.
set +e
ARGV_BEARER_HITS=$(grep -nE '(-H|--header)[[:space:]]+"Authorization:[[:space:]]*Bearer' "$DEPLOY_SH" || true)
set -e
assert_equals "deploy.sh contains no Authorization Bearer -H argv flags" "" "$ARGV_BEARER_HITS"

echo ""
echo "Summary: ${TEST_COUNT} tests run, ${FAIL_COUNT} failed."
if [[ ${FAIL_COUNT} -gt 0 ]]; then
  exit 1
fi
