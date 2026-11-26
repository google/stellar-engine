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
SET_IAM="${REPO_ROOT}/fast/stages-aw/0-bootstrap/setIAM.sh"
SAMPLE_FILE="${REPO_ROOT}/fast/stages-aw/0-bootstrap/setIAM.yaml.sample"

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

echo "==> Running fast/stages-aw/0-bootstrap/setIAM.sh Unit Tests"

TMP_TEST_DIR=$(mktemp -d)
trap 'rm -rf "$TMP_TEST_DIR"' EXIT

STUB_DIR="${TMP_TEST_DIR}/bin"
GCLOUD_LOG="${TMP_TEST_DIR}/gcloud.log"
POLICY_IN="${TMP_TEST_DIR}/policy_in.json"
POLICY_OUT="${TMP_TEST_DIR}/policy_out.json"
mkdir -p "$STUB_DIR"

cat > "${STUB_DIR}/gcloud" << 'EOF'
#!/bin/bash
set -euo pipefail
echo "$*" >> "$GCLOUD_LOG"
if [[ "${1:-}" == "organizations" && "${2:-}" == "get-iam-policy" ]]; then
  cat "$POLICY_IN"
elif [[ "${1:-}" == "organizations" && "${2:-}" == "set-iam-policy" ]]; then
  cat /dev/stdin > "$POLICY_OUT"
  cat "$POLICY_OUT"
else
  echo "Unexpected gcloud invocation: $*" >&2
  exit 1
fi
EOF
chmod +x "${STUB_DIR}/gcloud"

run_setiam() {
  : > "$GCLOUD_LOG"
  rm -f "$POLICY_OUT"
  set +e
  SETIAM_OUTPUT=$(
    PATH="${STUB_DIR}:${PATH}" \
      GCLOUD_LOG="$GCLOUD_LOG" \
      POLICY_IN="$POLICY_IN" \
      POLICY_OUT="$POLICY_OUT" \
      bash "$SET_IAM" "$@" 2>&1
  )
  SETIAM_STATUS=$?
  set -e
  SETIAM_CALLS=$(cat "$GCLOUD_LOG")
}

# 1. Invalid and injection email arguments fail before any gcloud call.
echo '{"bindings": []}' > "$POLICY_IN"
INVALID_EMAILS=(
  "not-an-email"
  "admin@example.com;id"
  "admin@example.com/g;p"
  "\$(whoami)@example.com"
  "admin@localhost"
  $'admin@example.com\nuser:evil@example.com'
)
for bad_email in "${INVALID_EMAILS[@]}"; do
  run_setiam "$bad_email" "123456789012"
  assert_equals "rejects malformed email: ${bad_email//$'\n'/\\n}" "1" "$SETIAM_STATUS"
  assert_equals "makes zero gcloud calls for malformed email" "" "$SETIAM_CALLS"
done

# 2. Non-numeric organization ID fails before any gcloud call.
run_setiam "admin@example.com" "org-123"
assert_equals "rejects non-numeric organization ID" "1" "$SETIAM_STATUS"
assert_equals "makes zero gcloud calls for bad org ID" "" "$SETIAM_CALLS"

# 3. Substring email match (abob@example.com) must not satisfy bob@example.com.
jq '{
  etag: "BwTestEtag==",
  version: 3,
  bindings: [.bindings[] | {role: .role, members: ["user:abob@example.com"]}]
}' "$SAMPLE_FILE" > "$POLICY_IN"

run_setiam "bob@example.com" "123456789012"
assert_equals "exact match vs substring exits 0" "0" "$SETIAM_STATUS"
assert_contains "set-iam-policy called when only substring user holds roles" \
  "organizations set-iam-policy 123456789012 /dev/stdin --format=json" \
  "$SETIAM_CALLS"

SAMPLE_COUNT=$(jq '.bindings | length' "$SAMPLE_FILE")
BOB_ROLE_COUNT=$(
  jq '[.bindings[] | select((.members | index("user:bob@example.com")) != null)] | length' \
    "$POLICY_OUT"
)
ABOB_ROLE_COUNT=$(
  jq '[.bindings[] | select((.members | index("user:abob@example.com")) != null)] | length' \
    "$POLICY_OUT"
)
OUT_ETAG=$(jq -r '.etag' "$POLICY_OUT")

assert_equals "bob@example.com receives every sample role" "$SAMPLE_COUNT" "$BOB_ROLE_COUNT"
assert_equals "abob@example.com retains every existing role" "$SAMPLE_COUNT" "$ABOB_ROLE_COUNT"
assert_equals "existing policy etag is preserved" "BwTestEtag==" "$OUT_ETAG"

# 4. Conditional bindings are left intact and do not satisfy unconditional roles.
cat > "$POLICY_IN" << 'EOF'
{
  "etag": "BwCondEtag==",
  "version": 3,
  "bindings": [
    {
      "role": "roles/owner",
      "members": ["user:admin@example.com"]
    },
    {
      "role": "roles/logging.admin",
      "members": ["user:admin@example.com"],
      "condition": {
        "title": "temporary",
        "expression": "request.time < timestamp('2099-01-01T00:00:00Z')"
      }
    },
    {
      "role": "roles/billing.admin",
      "members": ["user:other@example.com"]
    }
  ]
}
EOF

run_setiam "admin@example.com" "123456789012"
assert_equals "conditional and partial policy merge exits 0" "0" "$SETIAM_STATUS"
ADMIN_UNCOND_COUNT=$(
  jq '[.bindings[] | select(.condition == null and ((.members | index("user:admin@example.com")) != null))] | length' \
    "$POLICY_OUT"
)
COND_COUNT=$(
  jq '[.bindings[] | select(.role == "roles/logging.admin" and .condition != null)] | length' \
    "$POLICY_OUT"
)
OTHER_BILLING=$(
  jq '[.bindings[] | select(.role == "roles/billing.admin" and ((.members | index("user:other@example.com")) != null))] | length' \
    "$POLICY_OUT"
)
assert_equals "admin receives all unconditional sample roles" "$SAMPLE_COUNT" "$ADMIN_UNCOND_COUNT"
assert_equals "conditional logging.admin binding preserved" "1" "$COND_COUNT"
assert_equals "existing billing.admin member preserved" "1" "$OTHER_BILLING"

# 5. Idempotent no-op when the exact user already holds every sample role.
jq '{
  etag: "BwFullEtag==",
  version: 3,
  bindings: [.bindings[] | {role: .role, members: ["user:admin@example.com"]}]
}' "$SAMPLE_FILE" > "$POLICY_IN"

run_setiam "admin@example.com" "123456789012"
assert_equals "idempotent run exits 0" "0" "$SETIAM_STATUS"
assert_contains "idempotent run reports no new roles" \
  "No new roles to add" "$SETIAM_OUTPUT"
assert_equals "idempotent run skips set-iam-policy" \
  "organizations get-iam-policy 123456789012 --format=json" "$SETIAM_CALLS"

echo ""
echo "Summary: ${TEST_COUNT} tests run, ${FAIL_COUNT} failures."

if [[ ${FAIL_COUNT} -gt 0 ]]; then
  exit 1
fi
exit 0
