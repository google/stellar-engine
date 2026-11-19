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
SA_LOCKDOWN="${REPO_ROOT}/fast/stages-aw/3-security/sa_lockdown.sh"

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

echo "==> Running fast/stages-aw/3-security/sa_lockdown.sh Unit Tests"

TMP_TEST_DIR=$(mktemp -d)
trap 'rm -rf "$TMP_TEST_DIR"' EXIT

# Stub gcloud so each call lands in a log file instead of reaching the API.
STUB_DIR="${TMP_TEST_DIR}/bin"
GCLOUD_LOG="${TMP_TEST_DIR}/gcloud.log"
mkdir -p "$STUB_DIR"
cat > "${STUB_DIR}/gcloud" << 'EOF'
#!/bin/bash
echo "$*" >> "$GCLOUD_LOG"
EOF
chmod +x "${STUB_DIR}/gcloud"

# Sample tfvars files with the key layout that the 0-bootstrap and 1-resman
# stages write. The gcve, gke-prod, and teams branches are not deployed.
WORK_DIR="${TMP_TEST_DIR}/3-security"
SA_DOMAIN="my-project.iam.gserviceaccount.com"
mkdir -p "$WORK_DIR"
cat > "${WORK_DIR}/0-bootstrap.auto.tfvars.json" << EOF
{
  "automation": {
    "project_id": "my-project",
    "service_accounts": {
      "bootstrap": "bootstrap-0@${SA_DOMAIN}",
      "bootstrap-r": "bootstrap-0r@${SA_DOMAIN}",
      "resman": "resman-0@${SA_DOMAIN}",
      "resman-r": "resman-0r@${SA_DOMAIN}"
    }
  }
}
EOF
cat > "${WORK_DIR}/1-resman.auto.tfvars.json" << EOF
{
  "service_accounts": {
    "data-platform-dev": "dp-dev-0@${SA_DOMAIN}",
    "data-platform-dev-r": "dp-dev-0r@${SA_DOMAIN}",
    "data-platform-prod": "dp-prod-0@${SA_DOMAIN}",
    "data-platform-prod-r": "dp-prod-0r@${SA_DOMAIN}",
    "gcve-dev": null,
    "gcve-dev-r": null,
    "gcve-prod": null,
    "gcve-prod-r": null,
    "gke-dev": "gke-dev-0@${SA_DOMAIN}",
    "gke-dev-r": "gke-dev-0r@${SA_DOMAIN}",
    "gke-prod": null,
    "gke-prod-r": null,
    "networking": "net-0@${SA_DOMAIN}",
    "networking-r": "net-0r@${SA_DOMAIN}",
    "project-factory-dev": "pf-dev-0@${SA_DOMAIN}",
    "project-factory-dev-r": "pf-dev-0r@${SA_DOMAIN}",
    "project-factory-prod": "pf-prod-0@${SA_DOMAIN}",
    "project-factory-prod-r": "pf-prod-0r@${SA_DOMAIN}",
    "sandbox": "sandbox-0@${SA_DOMAIN}",
    "security": "sec-0@${SA_DOMAIN}",
    "security-r": "sec-0r@${SA_DOMAIN}",
    "team-alpha": "team-alpha-0@${SA_DOMAIN}"
  }
}
EOF

# Run sa_lockdown.sh in the sample directory with the stub first on PATH. The
# sorted gcloud calls land in LOCKDOWN_CALLS, the script output in
# LOCKDOWN_OUTPUT, and the exit status in LOCKDOWN_STATUS.
run_lockdown() {
  : > "$GCLOUD_LOG"
  set +e
  LOCKDOWN_OUTPUT=$(cd "$WORK_DIR" \
    && PATH="${STUB_DIR}:${PATH}" GCLOUD_LOG="$GCLOUD_LOG" \
      bash "$SA_LOCKDOWN" "$@" 2>&1)
  LOCKDOWN_STATUS=$?
  set -e
  LOCKDOWN_CALLS=$(sort "$GCLOUD_LOG")
}

# Print the sorted gcloud calls expected for an action and a list of account
# names, where each name is the part of the email before the "@".
expected_calls() {
  local action="$1"
  shift
  local account
  for account in "$@"; do
    echo "iam service-accounts ${action} ${account}@${SA_DOMAIN} --project=my-project --quiet"
  done | sort
}

DEPLOYED_ACCOUNTS=(
  bootstrap-0 bootstrap-0r resman-0 resman-0r
  net-0 net-0r sec-0 sec-0r
  dp-dev-0 dp-dev-0r dp-prod-0 dp-prod-0r
  gke-dev-0 gke-dev-0r
  pf-dev-0 pf-dev-0r pf-prod-0 pf-prod-0r
  sandbox-0 team-alpha-0
)

# 1. The default run disables every deployed account and skips null and
# absent keys.
run_lockdown
assert_equals "default run exits successfully" "0" "$LOCKDOWN_STATUS"
assert_equals "default run disables apply, plan, and branch accounts" \
  "$(expected_calls disable "${DEPLOYED_ACCOUNTS[@]}")" "$LOCKDOWN_CALLS"
assert_equals "default run prints nothing for null and absent keys" \
  "" "$LOCKDOWN_OUTPUT"

# 2. The --enable flag enables the same accounts.
run_lockdown --enable
assert_equals "--enable run exits successfully" "0" "$LOCKDOWN_STATUS"
assert_equals "--enable run enables apply, plan, and branch accounts" \
  "$(expected_calls enable "${DEPLOYED_ACCOUNTS[@]}")" "$LOCKDOWN_CALLS"

# 3. The original four names still select the stage apply accounts.
run_lockdown --sa "bootstrap,resman,networking,security"
assert_equals "--sa with the original names exits successfully" \
  "0" "$LOCKDOWN_STATUS"
assert_equals "--sa with the original names disables only those accounts" \
  "$(expected_calls disable bootstrap-0 resman-0 net-0 sec-0)" \
  "$LOCKDOWN_CALLS"

# 4. The --sa flag accepts plan, branch, and team names, and skips a null key.
run_lockdown --enable --sa "resman-r,gke-dev,gke-prod,teams,team-alpha"
assert_equals "--sa with plan and branch names exits successfully" \
  "0" "$LOCKDOWN_STATUS"
assert_equals "--sa enables the named accounts and skips null keys" \
  "$(expected_calls enable resman-0r gke-dev-0 team-alpha-0)" \
  "$LOCKDOWN_CALLS"

# 5. An unknown name fails validation before any gcloud call.
run_lockdown --sa "bootstrap,unknown"
assert_equals "--sa with an unknown name exits with status 1" \
  "1" "$LOCKDOWN_STATUS"
assert_contains "--sa with an unknown name reports it" \
  "Invalid names provided: unknown" "$LOCKDOWN_OUTPUT"
assert_equals "--sa with an unknown name makes no gcloud call" \
  "" "$LOCKDOWN_CALLS"

# 6. The usage text names the --sa flag that the parser accepts.
run_lockdown --names "bootstrap"
assert_equals "an unknown flag exits with status 1" "1" "$LOCKDOWN_STATUS"
assert_contains "usage text documents the --sa flag" \
  "[--sa <comma-separated list of names>]" "$LOCKDOWN_OUTPUT"
assert_equals "an unknown flag makes no gcloud call" "" "$LOCKDOWN_CALLS"

echo ""
echo "Summary: ${TEST_COUNT} tests run, ${FAIL_COUNT} failures."

if [[ ${FAIL_COUNT} -gt 0 ]]; then
  exit 1
fi
exit 0
