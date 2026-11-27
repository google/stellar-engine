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
IMPORT_SH="${REPO_ROOT}/fast/stages-aw/0-bootstrap/import.sh"

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

echo "==> Running fast/stages-aw/0-bootstrap/import.sh Unit Tests"

TMP_TEST_DIR=$(mktemp -d)
trap 'rm -rf "${TMP_TEST_DIR}"' EXIT

STUB_DIR="${TMP_TEST_DIR}/bin"
WORK_DIR="${TMP_TEST_DIR}/work"
mkdir -p "${STUB_DIR}" "${WORK_DIR}"

cat > "${STUB_DIR}/gcloud" << 'EOF'
#!/bin/bash
set -euo pipefail
echo "gcloud $*" >> "${MOCK_LOG}"
if [[ "${1:-}" == "organizations" && "${2:-}" == "list" ]]; then
  printf '%s\n' "${MOCK_ORGS:-}"
elif [[ "${1:-}" == "org-policies" && "${2:-}" == "list" ]]; then
  printf '%s\n' "${MOCK_POLICIES:-}"
else
  echo "Unexpected gcloud invocation: $*" >&2
  exit 1
fi
EOF
chmod +x "${STUB_DIR}/gcloud"

cat > "${STUB_DIR}/terraform" << 'EOF'
#!/bin/bash
set -euo pipefail
echo "terraform $*" >> "${MOCK_LOG}"
case "${1:-}" in
  console)
    expr=$(cat)
    echo "console: ${expr}" >> "${MOCK_LOG}"
    case "${expr}" in
      "var.deploy_org_resources.org_policies")
        printf '%s\n' "${MOCK_DEPLOY_ORG_POLICIES:-true}"
        ;;
      "local.assured_workload_folder")
        printf '%s\n' "${MOCK_AW_FOLDER:-null}"
        ;;
      "keys(local.org_policies)")
        printf '%s\n' "${MOCK_ORG_DECLARED:-[]}"
        ;;
      "keys(local._root_folder_org_policies)")
        printf '%s\n' "${MOCK_FOLDER_DECLARED:-[]}"
        ;;
      *)
        echo "Unexpected console expr: ${expr}" >&2
        exit 1
        ;;
    esac
    ;;
  state)
    if [[ "${2:-}" == "list" ]]; then
      printf '%s\n' "${MOCK_STATE:-}"
    fi
    ;;
  apply)
    if [[ -f imports.tf ]]; then
      cp imports.tf "${MOCK_IMPORTS_COPY}"
    fi
    ;;
  *)
    echo "Unexpected terraform invocation: $*" >&2
    exit 1
    ;;
esac
EOF
chmod +x "${STUB_DIR}/terraform"

run_import() {
  : > "${MOCK_LOG}"
  rm -f "${WORK_DIR}/imports.tf" "${MOCK_IMPORTS_COPY}"
  set +e
  IMPORT_OUTPUT=$(
    cd "${WORK_DIR}" && \
    PATH="${STUB_DIR}:${PATH}" \
    MOCK_LOG="${MOCK_LOG}" \
    MOCK_IMPORTS_COPY="${MOCK_IMPORTS_COPY}" \
    bash "${IMPORT_SH}" "$@" 2>&1
  )
  IMPORT_STATUS=$?
  set -e
}

export MOCK_LOG="${TMP_TEST_DIR}/mock.log"
export MOCK_IMPORTS_COPY="${TMP_TEST_DIR}/staged_imports.tf"

# Test 1: Avoid mapfile (incompatible with macOS Bash 3.2)
TEST_COUNT=$((TEST_COUNT + 1))
if ! grep -q "mapfile" "${IMPORT_SH}"; then
  echo "  [PASS] import.sh avoids mapfile for Bash 3.2 compatibility"
else
  echo "  [FAIL] import.sh must not use mapfile"
  FAIL_COUNT=$((FAIL_COUNT + 1))
fi

# Test 2: Org mode single-org auto-detection imports declared non-custom unmanaged policies
export MOCK_DEPLOY_ORG_POLICIES="true"
export MOCK_ORGS="111122223333"
export MOCK_POLICIES=$'organizations/111122223333/policies/compute.requireOsLogin\norganizations/111122223333/policies/compute.skipDefaultNetworkCreation\norganizations/111122223333/policies/custom.kmsRotation\norganizations/111122223333/policies/undeclared.policy'
export MOCK_ORG_DECLARED=$'[\n  "compute.requireOsLogin",\n  "compute.skipDefaultNetworkCreation",\n  "custom.kmsRotation",\n]'
export MOCK_STATE='module.organization.google_org_policy_policy.default["compute.skipDefaultNetworkCreation"]'
run_import
assert_equals "org mode exits 0 with single detected org" "0" "${IMPORT_STATUS}"
staged=$(cat "${MOCK_IMPORTS_COPY}")
assert_contains "org mode targets module.organization" 'module.organization.google_org_policy_policy.default["compute.requireOsLogin"]' "${staged}"
assert_contains "org mode sets organization self-link" 'organizations/111122223333/policies/compute.requireOsLogin' "${staged}"
assert_not_contains "org mode skips already-managed policy" "compute.skipDefaultNetworkCreation" "${staged}"
assert_not_contains "org mode skips custom policy" "custom.kmsRotation" "${staged}"
assert_not_contains "org mode skips undeclared policy" "undeclared.policy" "${staged}"
assert_equals "org mode cleans up temporary imports.tf" "false" "$([[ -f "${WORK_DIR}/imports.tf" ]] && echo true || echo false)"

# Test 3: Org mode rejects ambiguous multiple organizations
export MOCK_ORGS=$'111122223333\n444455556666'
run_import
assert_equals "org mode exits 1 when multiple orgs exist without explicit ID" "1" "${IMPORT_STATUS}"
assert_contains "org mode reports ambiguous organizations" "more than one organization is visible" "${IMPORT_OUTPUT}"

# Test 4: Folder mode imports declared folder policies into root-folder-config[0]
export MOCK_DEPLOY_ORG_POLICIES="false"
export MOCK_AW_FOLDER='"folders/987654321098"'
export MOCK_ORGS=$'111122223333\n444455556666'
export MOCK_POLICIES=$'folders/987654321098/policies/compute.requireOsLogin\nfolders/987654321098/policies/compute.skipDefaultNetworkCreation\nfolders/987654321098/policies/iam.allowedPolicyMemberDomains'
export MOCK_FOLDER_DECLARED=$'[\n  "compute.requireOsLogin",\n  "iam.allowedPolicyMemberDomains",\n]'
export MOCK_STATE='module.root-folder-config[0].google_org_policy_policy.default["iam.allowedPolicyMemberDomains"]'
run_import
assert_equals "folder mode exits 0 even when multiple orgs exist" "0" "${IMPORT_STATUS}"
mock_calls=$(cat "${MOCK_LOG}")
assert_contains "folder mode queries folder org policies" "gcloud org-policies list --folder=987654321098" "${mock_calls}"
assert_not_contains "folder mode does not call gcloud organizations list" "gcloud organizations list" "${mock_calls}"
staged=$(cat "${MOCK_IMPORTS_COPY}")
assert_contains "folder mode targets root-folder-config[0]" 'module.root-folder-config[0].google_org_policy_policy.default["compute.requireOsLogin"]' "${staged}"
assert_contains "folder mode sets folder self-link" 'folders/987654321098/policies/compute.requireOsLogin' "${staged}"
assert_not_contains "folder mode excludes AW-managed constraint not in _root_folder_org_policies" "compute.skipDefaultNetworkCreation" "${staged}"
assert_not_contains "folder mode skips already-managed folder policy" "iam.allowedPolicyMemberDomains" "${staged}"

# Test 5: Folder mode fails cleanly when assured_workload_folder is null
export MOCK_AW_FOLDER='null'
run_import
assert_equals "folder mode exits 1 when assured_workload_folder is null" "1" "${IMPORT_STATUS}"
assert_contains "folder mode explains missing assured_workload_folder" "local.assured_workload_folder is not yet created" "${IMPORT_OUTPUT}"

echo ""
echo "Summary: ${TEST_COUNT} tests run, ${FAIL_COUNT} failures."
[[ "${FAIL_COUNT}" -eq 0 ]]
