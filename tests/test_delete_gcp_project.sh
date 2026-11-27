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
DELETE_SCRIPT="${REPO_ROOT}/fast/stages-aw/3-security/delete_gcp_project.sh"

TEST_COUNT=0
FAIL_COUNT=0

assert_equals() {
  local desc="$1"
  local expected="$2"
  local actual="$3"
  TEST_COUNT=$((TEST_COUNT + 1))
  if [[ "${expected}" == "${actual}" ]]; then
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
  if [[ "${haystack}" == *"${needle}"* ]]; then
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
  if [[ "${haystack}" != *"${needle}"* ]]; then
    echo "  [PASS] ${desc}"
  else
    echo "  [FAIL] ${desc} (unexpected '${needle}')"
    FAIL_COUNT=$((FAIL_COUNT + 1))
  fi
}

echo "==> Running fast/stages-aw/3-security/delete_gcp_project.sh Unit Tests"

TMP_TEST_DIR=$(mktemp -d)
trap 'rm -rf "${TMP_TEST_DIR}"' EXIT

STUB_DIR="${TMP_TEST_DIR}/bin"
mkdir -p "${STUB_DIR}"

cat > "${STUB_DIR}/gcloud" << 'EOF'
#!/bin/bash
set -euo pipefail
echo "$*" >> "${GCLOUD_LOG}"
if [[ "${1:-}" == "config" && "${2:-}" == "get-value" ]]; then
  echo "admin@example.com"
elif [[ "${1:-}" == "projects" && "${2:-}" == "describe" ]]; then
  cat "${LIFECYCLE_STATE_FILE}"
elif [[ "${1:-}" == "projects" && "${2:-}" == "get-iam-policy" ]]; then
  printf '%s' "${MOCK_DELETER_ROLE:-}"
elif [[ "${1:-}" == "projects" && "${2:-}" == "add-iam-policy-binding" ]]; then
  exit 0
elif [[ "${1:-}" == "projects" && "${2:-}" == "remove-iam-policy-binding" ]]; then
  exit 0
elif [[ "${1:-}" == "projects" && "${2:-}" == "delete" ]]; then
  if [[ "${MOCK_DELETE_FAIL:-0}" == "1" ]]; then
    if [[ -n "${MOCK_DELETE_FAIL_NEXT_STATE:-}" ]]; then
      printf '%s\n' "${MOCK_DELETE_FAIL_NEXT_STATE}" > "${LIFECYCLE_STATE_FILE}"
    fi
    exit 1
  fi
  printf '%s\n' "DELETE_REQUESTED" > "${LIFECYCLE_STATE_FILE}"
  exit 0
else
  echo "Unexpected gcloud invocation: $*" >&2
  exit 1
fi
EOF
chmod +x "${STUB_DIR}/gcloud"

export GCLOUD_LOG="${TMP_TEST_DIR}/gcloud.log"
export LIFECYCLE_STATE_FILE="${TMP_TEST_DIR}/lifecycle_state"

run_delete() {
  local project_id="$1"
  local confirm_input="$2"
  : > "${GCLOUD_LOG}"
  set +e
  DELETE_OUTPUT=$(
    printf '%s\n' "${confirm_input}" \
      | PATH="${STUB_DIR}:${PATH}" \
        GCLOUD_LOG="${GCLOUD_LOG}" \
        LIFECYCLE_STATE_FILE="${LIFECYCLE_STATE_FILE}" \
        bash "${DELETE_SCRIPT}" --project-id="${project_id}" 2>&1
  )
  DELETE_STATUS=$?
  set -e
}

# Test 1: Successful delete adds projectDeleter temporarily and skips remove after delete
printf 'ACTIVE\n' > "${LIFECYCLE_STATE_FILE}"
export MOCK_DELETER_ROLE=""
export MOCK_DELETE_FAIL=0
export MOCK_DELETE_FAIL_NEXT_STATE=""
run_delete "pfx-bootstrap-0" "pfx-bootstrap-0"
calls=$(cat "${GCLOUD_LOG}")
assert_equals "successful delete exits 0" "0" "${DELETE_STATUS}"
assert_contains "adds temporary projectDeleter role when absent" "projects add-iam-policy-binding pfx-bootstrap-0" "${calls}"
assert_contains "deletes target project" "projects delete pfx-bootstrap-0 --quiet" "${calls}"
assert_not_contains "does not revoke role after project enters DELETE_REQUESTED" "remove-iam-policy-binding" "${calls}"
assert_not_contains "does not emit post-delete IAM warning" "WARNING: Failed to revoke projectDeleter role" "${DELETE_OUTPUT}"

# Test 2: Failed delete revokes projectDeleter if script added it and project stays ACTIVE
printf 'ACTIVE\n' > "${LIFECYCLE_STATE_FILE}"
export MOCK_DELETER_ROLE=""
export MOCK_DELETE_FAIL=1
export MOCK_DELETE_FAIL_NEXT_STATE=""
run_delete "pfx-bootstrap-0" "pfx-bootstrap-0"
calls=$(cat "${GCLOUD_LOG}")
assert_equals "failed delete exits 1" "1" "${DELETE_STATUS}"
assert_contains "failed delete rolls back temporary projectDeleter binding" "projects remove-iam-policy-binding pfx-bootstrap-0" "${calls}"

# Test 3: Failed delete leaves pre-existing projectDeleter intact
printf 'ACTIVE\n' > "${LIFECYCLE_STATE_FILE}"
export MOCK_DELETER_ROLE="roles/resourcemanager.projectDeleter"
export MOCK_DELETE_FAIL=1
export MOCK_DELETE_FAIL_NEXT_STATE=""
run_delete "pfx-bootstrap-0" "pfx-bootstrap-0"
calls=$(cat "${GCLOUD_LOG}")
assert_equals "failed delete with existing role exits 1" "1" "${DELETE_STATUS}"
assert_not_contains "does not add role when already granted" "add-iam-policy-binding" "${calls}"
assert_not_contains "does not remove pre-existing projectDeleter role" "remove-iam-policy-binding" "${calls}"

# Test 4: Failed delete skips IAM removal if project became DELETE_REQUESTED
printf 'ACTIVE\n' > "${LIFECYCLE_STATE_FILE}"
export MOCK_DELETER_ROLE=""
export MOCK_DELETE_FAIL=1
export MOCK_DELETE_FAIL_NEXT_STATE="DELETE_REQUESTED"
run_delete "pfx-bootstrap-0" "pfx-bootstrap-0"
calls=$(cat "${GCLOUD_LOG}")
assert_equals "failed delete exits 1 when project transitioned to DELETE_REQUESTED" "1" "${DELETE_STATUS}"
assert_not_contains "skips remove-iam-policy-binding when lifecycleState is DELETE_REQUESTED" "remove-iam-policy-binding" "${calls}"

# Test 5: Pre-check rejects already DELETE_REQUESTED projects
printf 'DELETE_REQUESTED\n' > "${LIFECYCLE_STATE_FILE}"
export MOCK_DELETER_ROLE=""
export MOCK_DELETE_FAIL=0
export MOCK_DELETE_FAIL_NEXT_STATE=""
run_delete "pfx-bootstrap-0" "pfx-bootstrap-0"
assert_equals "rejects project already in DELETE_REQUESTED" "1" "${DELETE_STATUS}"
assert_contains "reports DELETE_REQUESTED message" "marked for deletion" "${DELETE_OUTPUT}"

echo ""
echo "Summary: ${TEST_COUNT} tests run, ${FAIL_COUNT} failures."
[[ "${FAIL_COUNT}" -eq 0 ]]
