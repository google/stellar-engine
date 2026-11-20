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
VALIDATION_SH="${REPO_ROOT}/fast/stages-aw/3-security/validation.sh"

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "${TMP_DIR}"' EXIT

cat > "${TMP_DIR}/gcloud" <<'EOF'
#!/bin/bash
set -euo pipefail
echo "$*" >> "${MOCK_GCLOUD_LOG}"
case "$1 $2 $3" in
  "projects list "*)
    if [ "${MOCK_FAIL_PROJECTS_LIST:-0}" = "1" ]; then
      echo "ERROR: projects list failed" >&2
      exit 1
    fi
    if [[ "$*" == *"'^encl1-prod-iac-core-0$'"* ]]; then
      echo "encl1-prod-iac-core-0"
    elif [[ "$*" == *"'^missing-prod-iac-core-0$'"* ]]; then
      :
    else
      printf "encl1-prod-iac-core-0\nencl2-prod-iac-core-0\n"
    fi
    ;;
  "iam service-accounts list"*)
    args="$*"
    if [[ "${args}" == *"--project=nonexistent-project-0"* ]]; then
      echo "ERROR: project not found or unauthorized" >&2
      exit 1
    fi
    proj="${args#*--project=}"
    proj="${proj%% *}"
    echo "bootstrap-0@${proj}.iam.gserviceaccount.com"
    ;;
  "iam service-accounts describe"*)
    if [ "${MOCK_FAIL_SA_DESCRIBE:-0}" = "1" ]; then
      echo "ERROR: describe failed" >&2
      exit 1
    fi
    echo "True"
    ;;
  *)
    echo "Unexpected gcloud invocation: $*" >&2
    exit 1
    ;;
esac
EOF
chmod +x "${TMP_DIR}/gcloud"

export PATH="${TMP_DIR}:${PATH}"
export MOCK_GCLOUD_LOG="${TMP_DIR}/gcloud.log"

# validation.sh also reads the tfvars files in the current directory, so the
# flag tests below run in an empty one.
mkdir -p "${TMP_DIR}/empty"
cd "${TMP_DIR}/empty"

assert_rejected_without_gcloud() {
  local expected_err="$1"
  shift
  : > "${MOCK_GCLOUD_LOG}"
  local stderr_file="${TMP_DIR}/stderr.txt"
  if bash "${VALIDATION_SH}" "$@" >/dev/null 2>"${stderr_file}"; then
    echo "FAIL: expected rejection for args: $*"
    exit 1
  fi
  if [ -s "${MOCK_GCLOUD_LOG}" ]; then
    echo "FAIL: args ($*) invoked gcloud unexpectedly: $(cat "${MOCK_GCLOUD_LOG}")"
    exit 1
  fi
  if ! grep -qF "${expected_err}" "${stderr_file}"; then
    echo "FAIL: args ($*) stderr missing '${expected_err}'; got: $(cat "${stderr_file}")"
    exit 1
  fi
}

echo "==> Testing validation.sh default failure on multiple projects"
: > "${MOCK_GCLOUD_LOG}"
if bash "${VALIDATION_SH}" >/dev/null 2>&1; then
  echo "FAIL: expected failure when multiple -prod-iac-core-0 projects exist"
  exit 1
fi

echo "==> Testing validation.sh --prefix filtering"
: > "${MOCK_GCLOUD_LOG}"
OUTPUT="$(bash "${VALIDATION_SH}" --prefix encl1)"
if ! echo "${OUTPUT}" | grep -q "Found IaC Core Project: encl1-prod-iac-core-0"; then
  echo "FAIL: --prefix encl1 did not select encl1-prod-iac-core-0"
  exit 1
fi

echo "==> Testing validation.sh --prefix empty match message"
: > "${MOCK_GCLOUD_LOG}"
OUTPUT="$(bash "${VALIDATION_SH}" --prefix missing 2>&1 || true)"
if bash "${VALIDATION_SH}" --prefix missing >/dev/null 2>&1; then
  echo "FAIL: --prefix missing should exit non-zero"
  exit 1
fi
if ! echo "${OUTPUT}" | grep -qF "matching 'missing-prod-iac-core-0'"; then
  echo "FAIL: --prefix missing did not report expected suffix; got: ${OUTPUT}"
  exit 1
fi

echo "==> Testing validation.sh --project override skips projects list and passes --project"
: > "${MOCK_GCLOUD_LOG}"
OUTPUT="$(bash "${VALIDATION_SH}" --project=custom-iac-core-0)"
if ! echo "${OUTPUT}" | grep -q "Found IaC Core Project: custom-iac-core-0"; then
  echo "FAIL: --project=custom-iac-core-0 did not use override"
  exit 1
fi
if grep -q "projects list" "${MOCK_GCLOUD_LOG}"; then
  echo "FAIL: --project should skip gcloud projects list"
  exit 1
fi
if ! grep -q "iam service-accounts list --project=custom-iac-core-0" "${MOCK_GCLOUD_LOG}"; then
  echo "FAIL: iam service-accounts list did not receive --project=custom-iac-core-0"
  exit 1
fi
if ! grep -q "iam service-accounts describe bootstrap-0@custom-iac-core-0.iam.gserviceaccount.com --project=custom-iac-core-0" "${MOCK_GCLOUD_LOG}"; then
  echo "FAIL: iam service-accounts describe did not receive --project=custom-iac-core-0"
  exit 1
fi

echo "==> Testing validation.sh rejects invalid, missing, equals-form, and conflicting flags"
assert_rejected_without_gcloud "❌ ERROR: --prefix requires a non-empty value." --prefix --help
assert_rejected_without_gcloud "❌ ERROR: --project requires a non-empty value." --project --prefix
assert_rejected_without_gcloud "❌ ERROR: --prefix requires a non-empty value." --prefix=-foo
assert_rejected_without_gcloud "❌ ERROR: --project requires a non-empty value." --project=-foo
assert_rejected_without_gcloud "❌ ERROR: --prefix requires a non-empty value." --prefix=
assert_rejected_without_gcloud "❌ ERROR: --project requires a non-empty value." --project=
assert_rejected_without_gcloud "❌ ERROR: --prefix requires a non-empty value." --prefix
assert_rejected_without_gcloud "❌ ERROR: --project requires a non-empty value." --project
assert_rejected_without_gcloud "❌ ERROR: Invalid --prefix" --prefix "bad'regex"
assert_rejected_without_gcloud "❌ ERROR: Invalid --project" --project "BAD_PROJECT"
assert_rejected_without_gcloud "❌ ERROR: --project and --prefix cannot be used together." --project custom-iac-core-0 --prefix encl1

echo "==> Testing validation.sh fails non-zero when gcloud commands fail"
: > "${MOCK_GCLOUD_LOG}"
if MOCK_FAIL_PROJECTS_LIST=1 bash "${VALIDATION_SH}" --prefix encl1 >/dev/null 2>"${TMP_DIR}/err.txt"; then
  echo "FAIL: gcloud projects list error should exit non-zero"
  exit 1
fi
if ! grep -qF "❌ ERROR: Failed to list GCP projects." "${TMP_DIR}/err.txt"; then
  echo "FAIL: missing projects list error message; got: $(cat "${TMP_DIR}/err.txt")"
  exit 1
fi

: > "${MOCK_GCLOUD_LOG}"
if bash "${VALIDATION_SH}" --project nonexistent-project-0 >/dev/null 2>"${TMP_DIR}/err.txt"; then
  echo "FAIL: gcloud iam service-accounts list error should exit non-zero"
  exit 1
fi
if ! grep -qF "❌ ERROR: Failed to list service accounts in project 'nonexistent-project-0'." "${TMP_DIR}/err.txt"; then
  echo "FAIL: missing service-accounts list error message; got: $(cat "${TMP_DIR}/err.txt")"
  exit 1
fi

: > "${MOCK_GCLOUD_LOG}"
if MOCK_FAIL_SA_DESCRIBE=1 bash "${VALIDATION_SH}" --project custom-iac-core-0 >/dev/null 2>"${TMP_DIR}/err.txt"; then
  echo "FAIL: gcloud iam service-accounts describe error should exit non-zero"
  exit 1
fi
if ! grep -qF "❌ ERROR: Failed to describe service account" "${TMP_DIR}/err.txt"; then
  echo "FAIL: missing service-accounts describe error message; got: $(cat "${TMP_DIR}/err.txt")"
  exit 1
fi

echo "PASS: all validation.sh filtering checks succeeded."

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
    echo "  [FAIL] ${desc} (found '${needle}')"
    FAIL_COUNT=$((FAIL_COUNT + 1))
  fi
}

echo "==> Testing validation.sh account coverage and exit status"

STAGES_DIR="${REPO_ROOT}/fast/stages-aw"
VALIDATION="$VALIDATION_SH"
SA_LOCKDOWN="${STAGES_DIR}/3-security/sa_lockdown.sh"
TMP_TEST_DIR="${TMP_DIR}/coverage"

# A second gcloud stub for the coverage tests. Each call lands in a log file,
# and the files in MOCK_DIR decide what each call prints and whether it fails.
STUB_DIR="${TMP_TEST_DIR}/bin"
MOCK_DIR="${TMP_TEST_DIR}/mock"
GCLOUD_LOG="${TMP_TEST_DIR}/gcloud.log"
mkdir -p "$STUB_DIR" "$MOCK_DIR"
cat > "${STUB_DIR}/gcloud" << 'EOF'
#!/bin/bash
PATH="$MOCK_REAL_PATH"
echo "$*" >> "$GCLOUD_LOG"
case "$1 $2 ${3:-}" in
  "projects list "*)
    if [[ -e "${MOCK_DIR}/projects.fail" ]]; then
      echo "ERROR: (gcloud.projects.list) stub failure" >&2
      exit 1
    fi
    # Apply a "projectId~'<regex>'" filter the way gcloud does on the server
    filter=""
    for arg in "$@"; do
      if [[ $arg == --filter=* ]]; then
        filter=${arg#--filter=}
      fi
    done
    if [[ $filter =~ ^projectId~\'(.*)\'$ ]]; then
      grep -E -- "${BASH_REMATCH[1]}" "${MOCK_DIR}/projects.txt" || true
    else
      cat "${MOCK_DIR}/projects.txt"
    fi
    ;;
  "iam service-accounts list")
    if [[ -e "${MOCK_DIR}/list.fail" ]]; then
      echo "ERROR: (gcloud.iam.service-accounts.list) stub failure" >&2
      exit 1
    fi
    # Apply an "email ~ '<regex>'" filter the way gcloud does on the server
    filter=""
    for arg in "$@"; do
      if [[ $arg == --filter=* ]]; then
        filter=${arg#--filter=}
      fi
    done
    if [[ $filter =~ ^email\ ~\ \'(.*)\'$ ]]; then
      grep -E -- "${BASH_REMATCH[1]}" "${MOCK_DIR}/listed.txt" || true
    else
      cat "${MOCK_DIR}/listed.txt"
    fi
    ;;
  "iam service-accounts describe")
    if grep -qxF -- "$4" "${MOCK_DIR}/describe_fail.txt"; then
      echo "ERROR: (gcloud.iam.service-accounts.describe) stub failure" >&2
      exit 1
    fi
    if grep -qxF -- "$4" "${MOCK_DIR}/disabled.txt"; then
      echo "True"
    else
      cat "${MOCK_DIR}/enabled_output.txt"
    fi
    ;;
  "iam service-accounts disable")
    ;;
  *)
    echo "ERROR: unexpected gcloud call: $*" >&2
    exit 64
    ;;
esac
EOF
chmod +x "${STUB_DIR}/gcloud"

IAC_PROJECT="pfx-prod-iac-core-0"
IAC_DOMAIN="${IAC_PROJECT}.iam.gserviceaccount.com"

# Account IDs that the 0-bootstrap and 1-resman stages create for the keys that
# sa_lockdown.sh covers, with a "pfx" deployment prefix and two teams.
LOCKDOWN_IDS=(
  pfx-bootstrap-0 pfx-bootstrap-0r pfx-resman-0 pfx-resman-0r
  pfx-prod-resman-net-0 pfx-prod-resman-net-0r
  pfx-security-0 pfx-prod-resman-sec-0r
  pfx-dev-resman-dp-0 pfx-dev-resman-dp-0r
  pfx-prod-resman-dp-0 pfx-prod-resman-dp-0r
  pfx-dev-resman-gcve-0 pfx-dev-resman-gcve-0r
  pfx-prod-resman-gcve-0 pfx-prod-resman-gcve-0r
  pfx-dev-resman-gke-0 pfx-dev-resman-gke-0r
  pfx-prod-resman-gke-0 pfx-prod-resman-gke-0r
  pfx-dev-resman-pf-0 pfx-dev-resman-pf-0r
  pfx-prod-resman-pf-0 pfx-prod-resman-pf-0r
  pfx-dev-resman-sbox-0 pfx-prod-resman-teams-0
  pfx-prod-teams-alpha-0 pfx-prod-teams-beta-gamma-0
)

# Accounts in the same project that sa_lockdown.sh does not cover, such as the
# CI/CD accounts and the envs branch account. They stay enabled in every test.
OTHER_IDS=(
  pfx-bootstrap-1 pfx-bootstrap-1r pfx-resman-1 pfx-resman-1r
  pfx-prod-resman-net-1 pfx-prod-resman-net-1r
  pfx-prod-resman-sec-1 pfx-prod-resman-sec-1r
  pfx-dev-resman-dp-1 pfx-prod-resman-dp-1r
  pfx-dev-pf-resman-pf-1 pfx-prod-resman-pf-1r
  pfx-prod-teams-alpha-1 pfx-prod-resman-envs-0
  pfx-billing-export pfx-app-runtime
)

# Print one email in the IaC core project for each account ID.
iac_emails() {
  local id
  for id in "$@"; do
    echo "${id}@${IAC_DOMAIN}"
  done
}

LOCKDOWN_EMAILS=$(iac_emails "${LOCKDOWN_IDS[@]}" | sort)
OTHER_EMAILS=$(iac_emails "${OTHER_IDS[@]}" | sort)
LOCKDOWN_TOTAL=${#LOCKDOWN_IDS[@]}

# Reset the stub to a locked-down deployment. The IaC core project lists every
# account, and only the accounts that sa_lockdown.sh covers are disabled.
reset_mock() {
  rm -f "${MOCK_DIR}"/*
  echo "$IAC_PROJECT" > "${MOCK_DIR}/projects.txt"
  printf '%s\n' "$LOCKDOWN_EMAILS" "$OTHER_EMAILS" | sort > "${MOCK_DIR}/listed.txt"
  printf '%s\n' "$LOCKDOWN_EMAILS" > "${MOCK_DIR}/disabled.txt"
  : > "${MOCK_DIR}/describe_fail.txt"
  # gcloud prints an empty value for an account that has no "disabled" field
  echo "" > "${MOCK_DIR}/enabled_output.txt"
}

# Mark an account as enabled in the stub.
enable_account() {
  grep -vxF -- "$1" "${MOCK_DIR}/disabled.txt" > "${MOCK_DIR}/disabled.tmp" || true
  mv "${MOCK_DIR}/disabled.tmp" "${MOCK_DIR}/disabled.txt"
}

# Run validation.sh in RUN_DIR with the stub first on RUN_PATH. The script
# output lands in VALIDATION_OUTPUT, the exit status in VALIDATION_STATUS, and
# the sorted emails of the describe calls in DESCRIBED.
BASH_BIN="$(command -v bash)"
REAL_PATH="$PATH"
EMPTY_DIR="${TMP_TEST_DIR}/empty"
mkdir -p "$EMPTY_DIR"
RUN_DIR="$EMPTY_DIR"
RUN_PATH="$REAL_PATH"
run_validation() {
  : > "$GCLOUD_LOG"
  set +e
  VALIDATION_OUTPUT=$(cd "$RUN_DIR" \
    && PATH="${STUB_DIR}:${RUN_PATH}" GCLOUD_LOG="$GCLOUD_LOG" \
      MOCK_DIR="$MOCK_DIR" MOCK_REAL_PATH="$REAL_PATH" \
      "$BASH_BIN" "$VALIDATION" "$@" 2>&1)
  VALIDATION_STATUS=$?
  set -e
  DESCRIBED=$(sed -n 's/^iam service-accounts describe \([^ ]*\) .*/\1/p' "$GCLOUD_LOG" | sort)
}

# Count the output lines that contain a string.
count_lines() {
  grep -cF -- "$1" <<< "$VALIDATION_OUTPUT" || true
}

# Print the VALID_NAMES list and the team prefix that a script defines.
lockdown_keys() {
  awk '/^VALID_NAMES=\(/,/^\)/' "$1" | grep -o '"[^"]*"' | sort
  grep '^TEAM_PREFIX=' "$1"
}

# Print the account IDs that a stage gives to the modules behind a tfvars
# "service_accounts" block, where the first argument is the stage directory
# and the rest is the awk range that selects the block in outputs.tf.
stage_account_ids() {
  local stage_dir="$1"
  local block_range="$2"
  local module_name
  local account_id
  while IFS= read -r module_name; do
    account_id=$(awk -v header="module \"${module_name}\" {" '
      $0 == header { found = 1 }
      found && $1 == "name" { gsub(/"/, "", $3); print $3; exit }
    ' "${stage_dir}"/*.tf)
    echo "pfx-${account_id//\$\{each.key\}/alpha}"
  done < <(awk "$block_range" "${stage_dir}/outputs.tf" \
    | grep -o 'module\.[a-z0-9-]*' | sed 's/^module\.//' | sort -u)
}

# 1. The tfvars keys match the keys that sa_lockdown.sh covers.
assert_equals "the key list matches VALID_NAMES in sa_lockdown.sh" \
  "$(lockdown_keys "$SA_LOCKDOWN")" "$(lockdown_keys "$VALIDATION")"
assert_equals "the key list holds 26 keys and the team prefix" \
  "27" "$(lockdown_keys "$VALIDATION" | wc -l | tr -d ' ')"

# 2. The sample account IDs are the IDs in the stage sources, so a renamed or
# new account in a stage fails this test until the pattern covers it.
STAGE_IDS=$(
  {
    stage_account_ids "${STAGES_DIR}/0-bootstrap" \
      '/^      service_accounts = \{/,/^      \}/'
    stage_account_ids "${STAGES_DIR}/1-resman" \
      '/^  service_accounts = merge\(/,/^  \)/'
  } | sort
)
assert_equals "the sample account IDs match the stage sources" \
  "$STAGE_IDS" \
  "$(printf '%s\n' "${LOCKDOWN_IDS[@]}" | grep -vx 'pfx-prod-teams-beta-gamma-0' | sort)"

# 3. The original invocation, with no arguments and no tfvars files, passes
# when every covered account is disabled and ignores the other accounts.
reset_mock
run_validation
assert_equals "a locked-down deployment exits with status 0" \
  "0" "$VALIDATION_STATUS"
assert_equals "the run checks apply, plan, branch, and team accounts only" \
  "$LOCKDOWN_EMAILS" "$DESCRIBED"
assert_equals "the run reports each covered account as disabled" \
  "$LOCKDOWN_TOTAL" "$(count_lines "✅ SUCCESS: ")"
assert_equals "the run reports no enabled account" \
  "0" "$(count_lines "❌ FAILED: ")"
assert_contains "the run prints the pass summary" \
  "✅ All ${LOCKDOWN_TOTAL} deployment service accounts are disabled." \
  "$VALIDATION_OUTPUT"
assert_contains "the run looks up the IaC core project as before" \
  "projects list --filter=projectId~'-prod-iac-core-0\$' --format=value(projectId)" \
  "$(cat "$GCLOUD_LOG")"
assert_contains "the run reads each status from the IaC core project" \
  "iam service-accounts describe pfx-security-0@${IAC_DOMAIN} --project=${IAC_PROJECT} --format=value(disabled)" \
  "$(cat "$GCLOUD_LOG")"

# 4. Each covered account fails the run on its own when it is still enabled,
# and the run still checks every other account.
for id in "${LOCKDOWN_IDS[@]}"; do
  reset_mock
  enable_account "${id}@${IAC_DOMAIN}"
  run_validation
  assert_equals "an enabled ${id} account exits with status 1" \
    "1 1 $((LOCKDOWN_TOTAL - 1))" \
    "${VALIDATION_STATUS} $(count_lines "❌ FAILED: ${id}@${IAC_DOMAIN} is still enabled.") $(count_lines "✅ SUCCESS: ")"
done

# 5. A deployment with no lockdown fails for every covered account, also when
# gcloud prints "False" instead of an empty value.
reset_mock
: > "${MOCK_DIR}/disabled.txt"
echo "False" > "${MOCK_DIR}/enabled_output.txt"
run_validation
assert_equals "a deployment with no lockdown exits with status 1" \
  "1" "$VALIDATION_STATUS"
assert_equals "a deployment with no lockdown reports each covered account" \
  "$LOCKDOWN_TOTAL" "$(count_lines "❌ FAILED: ")"
assert_contains "a deployment with no lockdown prints the failure summary" \
  "❌ Verification failed: 0 disabled, ${LOCKDOWN_TOTAL} still enabled, 0 errors." \
  "$VALIDATION_OUTPUT"

# 6. A gcloud failure while listing projects fails the run.
reset_mock
touch "${MOCK_DIR}/projects.fail"
run_validation
assert_equals "a failed project lookup exits with status 1" \
  "1" "$VALIDATION_STATUS"
assert_contains "a failed project lookup reports the error" \
  "❌ ERROR: Failed to list GCP projects." "$VALIDATION_OUTPUT"
assert_equals "a failed project lookup checks no account" "" "$DESCRIBED"

# 7. A missing or ambiguous IaC core project fails the run as before.
reset_mock
: > "${MOCK_DIR}/projects.txt"
run_validation
assert_equals "a missing IaC core project exits with status 1" \
  "1" "$VALIDATION_STATUS"
assert_contains "a missing IaC core project prints the warning" \
  "No IaC core project found matching '-prod-iac-core-0'." \
  "$VALIDATION_OUTPUT"

reset_mock
printf '%s\n' "$IAC_PROJECT" "other-prod-iac-core-0" > "${MOCK_DIR}/projects.txt"
run_validation
assert_equals "two IaC core projects exit with status 1" \
  "1" "$VALIDATION_STATUS"
assert_contains "two IaC core projects print the warning" \
  "Multiple possible IaC core projects found." "$VALIDATION_OUTPUT"
assert_equals "two IaC core projects check no account" "" "$DESCRIBED"

# 8. A gcloud failure while listing service accounts fails the run.
reset_mock
touch "${MOCK_DIR}/list.fail"
run_validation
assert_equals "a failed account listing exits with status 1" \
  "1" "$VALIDATION_STATUS"
assert_contains "a failed account listing reports the error" \
  "❌ ERROR: Failed to list service accounts in project '${IAC_PROJECT}'." \
  "$VALIDATION_OUTPUT"
assert_equals "a failed account listing checks no account" "" "$DESCRIBED"

# 9. A gcloud failure while reading one status fails the run, and the run
# still checks every other account.
reset_mock
echo "pfx-resman-0r@${IAC_DOMAIN}" > "${MOCK_DIR}/describe_fail.txt"
run_validation
assert_equals "a failed status read exits with status 1" \
  "1" "$VALIDATION_STATUS"
assert_contains "a failed status read reports the account" \
  "❌ ERROR: Failed to describe service account 'pfx-resman-0r@${IAC_DOMAIN}' in project '${IAC_PROJECT}'." \
  "$VALIDATION_OUTPUT"
assert_equals "a failed status read still checks the other accounts" \
  "$((LOCKDOWN_TOTAL - 1))" "$(count_lines "✅ SUCCESS: ")"
assert_not_contains "a failed status read prints no pass summary" \
  "deployment service accounts are disabled." "$VALIDATION_OUTPUT"

# 10. A project with no covered account fails the run, because the run
# verified nothing.
reset_mock
printf '%s\n' "$OTHER_EMAILS" > "${MOCK_DIR}/listed.txt"
run_validation
assert_equals "a project with no covered account exits with status 1" \
  "1" "$VALIDATION_STATUS"
assert_contains "a project with no covered account prints the warning" \
  "No standard deployment service accounts found in ${IAC_PROJECT}." \
  "$VALIDATION_OUTPUT"
assert_equals "a project with no covered account checks no account" \
  "" "$DESCRIBED"

reset_mock
: > "${MOCK_DIR}/listed.txt"
run_validation
assert_equals "a project with no account exits with status 1" \
  "1" "$VALIDATION_STATUS"

# Sample tfvars files with the key layout that the 0-bootstrap and 1-resman
# stages write. The accounts have custom IDs in a second project, so only the
# tfvars files lead to them. The gcve, gke-prod, and teams branches are not
# deployed, and the "other" key is not a key that sa_lockdown.sh covers.
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
      "resman": "pfx-resman-0@${IAC_DOMAIN}",
      "resman-r": "pfx-resman-0r@${IAC_DOMAIN}"
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
    "other": "other-0@${SA_DOMAIN}",
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

TFVARS_IDS=(
  bootstrap-0 bootstrap-0r net-0 net-0r sec-0 sec-0r
  dp-dev-0 dp-dev-0r dp-prod-0 dp-prod-0r
  gke-dev-0 gke-dev-0r
  pf-dev-0 pf-dev-0r pf-prod-0 pf-prod-0r
  sandbox-0 team-alpha-0
)
TFVARS_EMAILS=$(
  for id in "${TFVARS_IDS[@]}"; do
    echo "${id}@${SA_DOMAIN}"
  done | sort
)
ALL_EMAILS=$(printf '%s\n' "$LOCKDOWN_EMAILS" "$TFVARS_EMAILS" | sort)
ALL_TOTAL=$((LOCKDOWN_TOTAL + ${#TFVARS_IDS[@]}))

# Reset the stub to a locked-down deployment that also has the tfvars accounts.
reset_mock_with_tfvars() {
  reset_mock
  printf '%s\n' "$TFVARS_EMAILS" >> "${MOCK_DIR}/disabled.txt"
}

RUN_DIR="$WORK_DIR"

# 11. In a directory with tfvars files, the run also checks the accounts that
# sa_lockdown.sh reads from them, once each.
reset_mock_with_tfvars
run_validation
assert_equals "a locked-down tfvars deployment exits with status 0" \
  "0" "$VALIDATION_STATUS"
assert_equals "the tfvars run checks the project and the tfvars accounts once" \
  "$ALL_EMAILS" "$DESCRIBED"
assert_contains "the tfvars run prints the pass summary" \
  "✅ All ${ALL_TOTAL} deployment service accounts are disabled." \
  "$VALIDATION_OUTPUT"
assert_contains "the tfvars run reads each status from the account project" \
  "iam service-accounts describe team-alpha-0@${SA_DOMAIN} --project=my-project --format=value(disabled)" \
  "$(cat "$GCLOUD_LOG")"

# 12. The run checks every account that sa_lockdown.sh disables in the same
# directory.
: > "$GCLOUD_LOG"
(cd "$WORK_DIR" \
  && PATH="${STUB_DIR}:${REAL_PATH}" GCLOUD_LOG="$GCLOUD_LOG" \
    MOCK_DIR="$MOCK_DIR" MOCK_REAL_PATH="$REAL_PATH" \
    "$BASH_BIN" "$SA_LOCKDOWN" > /dev/null)
LOCKED_DOWN=$(sed -n 's/^iam service-accounts disable \([^ ]*\) .*/\1/p' "$GCLOUD_LOG" | sort)
assert_equals "sa_lockdown.sh disables the tfvars accounts" \
  "$((${#TFVARS_IDS[@]} + 2))" "$(wc -l <<< "$LOCKED_DOWN" | tr -d ' ')"
assert_equals "the tfvars run checks every account that sa_lockdown.sh disables" \
  "" "$(comm -23 <(echo "$LOCKED_DOWN") <(echo "$ALL_EMAILS"))"

# 13. An enabled account that only the tfvars files list fails the run.
for id in bootstrap-0r dp-dev-0 sandbox-0 team-alpha-0; do
  reset_mock_with_tfvars
  enable_account "${id}@${SA_DOMAIN}"
  run_validation
  assert_equals "an enabled tfvars ${id} account exits with status 1" \
    "1 1 $((ALL_TOTAL - 1))" \
    "${VALIDATION_STATUS} $(count_lines "❌ FAILED: ${id}@${SA_DOMAIN} is still enabled.") $(count_lines "✅ SUCCESS: ")"
done

# 14. A tfvars account that gcloud cannot read fails the run.
reset_mock_with_tfvars
echo "net-0@${SA_DOMAIN}" > "${MOCK_DIR}/describe_fail.txt"
run_validation
assert_equals "an unreadable tfvars account exits with status 1" \
  "1" "$VALIDATION_STATUS"
assert_contains "an unreadable tfvars account reports the account" \
  "❌ ERROR: Failed to describe service account 'net-0@${SA_DOMAIN}' in project 'my-project'." \
  "$VALIDATION_OUTPUT"

# 15. A tfvars file that jq cannot read fails the run, and the run still
# checks the accounts that it found.
BROKEN_DIR="${TMP_TEST_DIR}/broken"
mkdir -p "$BROKEN_DIR"
cp "${WORK_DIR}/0-bootstrap.auto.tfvars.json" "$BROKEN_DIR/"
echo '{"service_accounts": {' > "${BROKEN_DIR}/1-resman.auto.tfvars.json"
RUN_DIR="$BROKEN_DIR"
reset_mock_with_tfvars
run_validation
assert_equals "a malformed tfvars file exits with status 1" \
  "1" "$VALIDATION_STATUS"
assert_contains "a malformed tfvars file reports the file" \
  "❌ ERROR: jq failed to read ./1-resman.auto.tfvars.json." \
  "$VALIDATION_OUTPUT"
assert_equals "a malformed tfvars file still checks the other accounts" \
  "$((LOCKDOWN_TOTAL + 2))" "$(count_lines "✅ SUCCESS: ")"

# 16. A missing jq binary fails the run in a directory with tfvars files.
RUN_DIR="$WORK_DIR"
RUN_PATH="${TMP_TEST_DIR}/no-such-dir"
reset_mock_with_tfvars
run_validation
assert_equals "a missing jq binary exits with status 1" \
  "1" "$VALIDATION_STATUS"
assert_contains "a missing jq binary reports the error" \
  "❌ ERROR: jq is not installed." "$VALIDATION_OUTPUT"
assert_equals "a missing jq binary still checks the project accounts" \
  "$LOCKDOWN_TOTAL" "$(count_lines "✅ SUCCESS: ")"

# 17. A missing jq binary does not affect a directory with no tfvars files.
RUN_DIR="$EMPTY_DIR"
reset_mock
run_validation
assert_equals "a missing jq binary passes with no tfvars files" \
  "0" "$VALIDATION_STATUS"
RUN_PATH="$REAL_PATH"

# 18. The --prefix flag selects one of two IaC core projects and checks every
# covered account in it.
reset_mock
printf '%s\n' "$IAC_PROJECT" "other-prod-iac-core-0" > "${MOCK_DIR}/projects.txt"
run_validation --prefix pfx
assert_equals "--prefix with a locked-down deployment exits with status 0" \
  "0" "$VALIDATION_STATUS"
assert_equals "--prefix checks apply, plan, branch, and team accounts only" \
  "$LOCKDOWN_EMAILS" "$DESCRIBED"
assert_contains "--prefix filters the project lookup" \
  "projects list --filter=projectId~'^pfx-prod-iac-core-0\$' --format=value(projectId)" \
  "$(cat "$GCLOUD_LOG")"

enable_account "pfx-prod-resman-net-0r@${IAC_DOMAIN}"
run_validation --prefix pfx
assert_equals "--prefix with an enabled plan account exits with status 1" \
  "1 1 $((LOCKDOWN_TOTAL - 1))" \
  "${VALIDATION_STATUS} $(count_lines "❌ FAILED: pfx-prod-resman-net-0r@${IAC_DOMAIN} is still enabled.") $(count_lines "✅ SUCCESS: ")"

# 19. The --project flag skips the project lookup and checks every covered
# account in the named project.
reset_mock
run_validation --project "$IAC_PROJECT"
assert_equals "--project with a locked-down deployment exits with status 0" \
  "0" "$VALIDATION_STATUS"
assert_equals "--project checks apply, plan, branch, and team accounts only" \
  "$LOCKDOWN_EMAILS" "$DESCRIBED"
assert_not_contains "--project skips the project lookup" \
  "projects list" "$(cat "$GCLOUD_LOG")"

enable_account "pfx-dev-resman-gke-0@${IAC_DOMAIN}"
run_validation "--project=${IAC_PROJECT}"
assert_equals "--project with an enabled branch account exits with status 1" \
  "1 1 $((LOCKDOWN_TOTAL - 1))" \
  "${VALIDATION_STATUS} $(count_lines "❌ FAILED: pfx-dev-resman-gke-0@${IAC_DOMAIN} is still enabled.") $(count_lines "✅ SUCCESS: ")"

reset_mock
printf '%s\n' "$OTHER_EMAILS" > "${MOCK_DIR}/listed.txt"
run_validation --project "$IAC_PROJECT"
assert_equals "--project with no covered account exits with status 1" \
  "1" "$VALIDATION_STATUS"

# 20. With a flag, the run covers the selected project only. It skips the
# tfvars accounts of other projects and says so, also when they are enabled.
# Without a flag, the same directory fails on those accounts.
RUN_DIR="$WORK_DIR"
for flag in "--project=${IAC_PROJECT}" "--prefix=pfx"; do
  reset_mock
  run_validation "$flag"
  assert_equals "${flag} with tfvars of another project exits with status 0" \
    "0" "$VALIDATION_STATUS"
  assert_equals "${flag} checks the accounts of the selected project only" \
    "$LOCKDOWN_EMAILS" "$DESCRIBED"
  assert_contains "${flag} reports the skipped 0-bootstrap accounts" \
    "⚠️ WARNING: Skipped 2 accounts in ./0-bootstrap.auto.tfvars.json that are not in project ${IAC_PROJECT}." \
    "$VALIDATION_OUTPUT"
  assert_contains "${flag} reports the skipped 1-resman accounts" \
    "⚠️ WARNING: Skipped 16 accounts in ./1-resman.auto.tfvars.json that are not in project ${IAC_PROJECT}." \
    "$VALIDATION_OUTPUT"
done

reset_mock
run_validation
assert_equals "no flag with enabled tfvars accounts exits with status 1" \
  "1 ${#TFVARS_IDS[@]}" "${VALIDATION_STATUS} $(count_lines "❌ FAILED: ")"

# 21. With a flag, the run still checks the tfvars accounts of the selected
# project, which here have IDs that the pattern does not match.
CUSTOM_DIR="${TMP_TEST_DIR}/custom"
mkdir -p "$CUSTOM_DIR"
cat > "${CUSTOM_DIR}/1-resman.auto.tfvars.json" << EOF
{
  "service_accounts": {
    "networking": "custom-net@${IAC_DOMAIN}",
    "security": "sec-0@${SA_DOMAIN}",
    "team-zeta": "custom-team@${IAC_DOMAIN}"
  }
}
EOF
CUSTOM_EMAILS=$(printf '%s\n' "custom-net@${IAC_DOMAIN}" "custom-team@${IAC_DOMAIN}")
RUN_DIR="$CUSTOM_DIR"
for flag in "--project=${IAC_PROJECT}" "--prefix=pfx"; do
  reset_mock
  printf '%s\n' "$CUSTOM_EMAILS" >> "${MOCK_DIR}/disabled.txt"
  run_validation "$flag"
  assert_equals "${flag} with locked-down custom accounts exits with status 0" \
    "0" "$VALIDATION_STATUS"
  assert_equals "${flag} checks the custom accounts of the selected project" \
    "$(printf '%s\n' "$LOCKDOWN_EMAILS" "$CUSTOM_EMAILS" | sort)" "$DESCRIBED"

  enable_account "custom-team@${IAC_DOMAIN}"
  run_validation "$flag"
  assert_equals "${flag} with an enabled custom team account exits with status 1" \
    "1 1" \
    "${VALIDATION_STATUS} $(count_lines "❌ FAILED: custom-team@${IAC_DOMAIN} is still enabled.")"
done

echo ""
echo "Summary: ${TEST_COUNT} tests run, ${FAIL_COUNT} failures."

if [[ ${FAIL_COUNT} -gt 0 ]]; then
  exit 1
fi
exit 0
