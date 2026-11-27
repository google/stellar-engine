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
RESTORE="${REPO_ROOT}/scripts/restore.sh"
COMMON_FUNCTIONS="${REPO_ROOT}/scripts/common-functions.sh"

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

echo "==> Running scripts/restore.sh Unit Tests"

TMP_TEST_DIR=$(mktemp -d)
trap 'rm -rf "$TMP_TEST_DIR"' EXIT

STUB_DIR="${TMP_TEST_DIR}/bin"
CALL_LOG="${TMP_TEST_DIR}/calls.log"
mkdir -p "$STUB_DIR"

cat > "${STUB_DIR}/gcloud" << 'EOF'
#!/bin/bash
echo "gcloud $*" >> "$CALL_LOG"
EOF

cat > "${STUB_DIR}/terraform" << 'EOF'
#!/bin/bash
echo "terraform (${PWD}) $*" >> "$CALL_LOG"
EOF

cat > "${STUB_DIR}/sleep" << 'EOF'
#!/bin/bash
echo "sleep $*" >> "$CALL_LOG"
EOF

chmod +x "${STUB_DIR}/gcloud" "${STUB_DIR}/terraform" "${STUB_DIR}/sleep"

# Isolated layout mirroring scripts/ and fast/stages-aw/ so config.env loading
# can be tested without modifying the repository checkout.
ISO_ROOT="${TMP_TEST_DIR}/repo"
mkdir -p "${ISO_ROOT}/scripts" \
  "${ISO_ROOT}/fast/stages-aw/2-networking-a-fedramp" \
  "${ISO_ROOT}/fast/stages-aw/2-networking-b-il5-ngfw"
cp "$RESTORE" "${ISO_ROOT}/scripts/restore.sh"
cp "$COMMON_FUNCTIONS" "${ISO_ROOT}/scripts/common-functions.sh"

run_restore() {
  local script_path="$1"
  local stdin_data="$2"
  shift 2
  : > "$CALL_LOG"
  set +e
  RESTORE_OUTPUT=$(
    env -i \
      PATH="${STUB_DIR}:${PATH}" \
      CALL_LOG="$CALL_LOG" \
      "$@" \
      bash "$script_path" <<< "$stdin_data" 2>&1
  )
  RESTORE_STATUS=$?
  set -e
  RESTORE_CALLS=$(cat "$CALL_LOG")
}

# 1. Fails cleanly when config.env and required env vars are absent.
run_restore "${ISO_ROOT}/scripts/restore.sh" $'n\n'
assert_equals "fails without config.env or env vars" "1" "$RESTORE_STATUS"
assert_equals "makes no tool calls when unconfigured" "" "$RESTORE_CALLS"
assert_contains "reports missing config.env" "config.env" "$RESTORE_OUTPUT"

# 2. Loads config.env automatically and skips cleanly on 'n'.
cat > "${ISO_ROOT}/scripts/config.env" << 'EOF'
PREFIX="pfx"
BILLING_ACCOUNT="000000-AAAAAA-000000"
REGION="us-east4"
EOF

run_restore "${ISO_ROOT}/scripts/restore.sh" $'n\n'
assert_equals "exits 0 when user answers n" "0" "$RESTORE_STATUS"
assert_equals "makes no tool calls when user answers n" "" "$RESTORE_CALLS"

# 3. Exits 0 and makes no calls when user answers 's'.
run_restore "${ISO_ROOT}/scripts/restore.sh" $'s\n'
assert_equals "exits 0 when user answers s" "0" "$RESTORE_STATUS"
assert_equals "makes no tool calls when user answers s" "" "$RESTORE_CALLS"

# 4. Rejects invalid choice without running gcloud or terraform.
run_restore "${ISO_ROOT}/scripts/restore.sh" $'y\n9\n'
assert_equals "fails on invalid paradigm choice" "1" "$RESTORE_STATUS"
assert_equals "makes no tool calls on invalid choice" "" "$RESTORE_CALLS"
assert_contains "reports invalid choice" "Invalid choice" "$RESTORE_OUTPUT"

# 5. Choice 2 restores FedRAMP/IL2 in 2-networking-a-fedramp using config.env.
run_restore "${ISO_ROOT}/scripts/restore.sh" $'y\n2\n'
assert_equals "choice 2 exits 0" "0" "$RESTORE_STATUS"
assert_contains "choice 2 undeletes hub host" "gcloud projects undelete pfx-net-hub-host" "$RESTORE_CALLS"
assert_contains "choice 2 undeletes prod spoke" "gcloud projects undelete pfx-prod-net-host" "$RESTORE_CALLS"
assert_contains "choice 2 links billing via GA gcloud billing" "gcloud billing projects link pfx-net-hub-host --billing-account 000000-AAAAAA-000000" "$RESTORE_CALLS"
assert_contains "choice 2 imports hub-project in 2-networking-a-fedramp" \
  "terraform (${ISO_ROOT}/fast/stages-aw/2-networking-a-fedramp) import module.hub-project.google_project.project[0] pfx-net-hub-host" \
  "$RESTORE_CALLS"
assert_not_contains "choice 2 does not invoke kms restore" "gcloud kms" "$RESTORE_CALLS"

# 6. Choice 3 restores IL4/IL5 in 2-networking-b-il5-ngfw including KMS.
run_restore "${ISO_ROOT}/scripts/restore.sh" $'y\n3\n'
assert_equals "choice 3 exits 0" "0" "$RESTORE_STATUS"
assert_contains "choice 3 undeletes vdss host" "gcloud projects undelete pfx-net-vdss-host" "$RESTORE_CALLS"
assert_contains "choice 3 imports vdss-host-project in 2-networking-b-il5-ngfw" \
  "terraform (${ISO_ROOT}/fast/stages-aw/2-networking-b-il5-ngfw) import module.vdss-host-project.google_project.project[0] pfx-net-vdss-host" \
  "$RESTORE_CALLS"
assert_contains "choice 3 restores kms key version" \
  "gcloud kms keys versions restore 1 --location=us-east4 --keyring=vdss-keyring --key=default --project=pfx-net-vdss-host" \
  "$RESTORE_CALLS"
assert_contains "choice 3 enables kms key version" \
  "gcloud kms keys versions enable 1 --location=us-east4 --keyring=vdss-keyring --key=default --project=pfx-net-vdss-host" \
  "$RESTORE_CALLS"
assert_contains "choice 3 imports kms keyring" \
  "terraform (${ISO_ROOT}/fast/stages-aw/2-networking-b-il5-ngfw) import module.kms.google_kms_key_ring.default[0] projects/pfx-net-vdss-host/locations/us-east4/keyRings/vdss-keyring" \
  "$RESTORE_CALLS"
assert_contains "choice 3 imports kms crypto key" \
  'terraform ('"${ISO_ROOT}"'/fast/stages-aw/2-networking-b-il5-ngfw) import module.kms.google_kms_crypto_key.default["default"] projects/pfx-net-vdss-host/locations/us-east4/keyRings/vdss-keyring/cryptoKeys/default' \
  "$RESTORE_CALLS"

# 7. Real scripts/restore.sh runs from repo checkout with exported env vars
# when no local gitignored scripts/config.env overrides exported inputs.
if [[ ! -f "${REPO_ROOT}/scripts/config.env" ]]; then
  run_restore "$RESTORE" $'y\n3\n' \
    PREFIX="real" BILLING_ACCOUNT="111111-BBBBBB-111111" REGION="us-central1"
  assert_equals "real scripts/restore.sh exits 0" "0" "$RESTORE_STATUS"
  assert_contains "real scripts/restore.sh imports in repo 2-networking-b-il5-ngfw" \
    "terraform (${REPO_ROOT}/fast/stages-aw/2-networking-b-il5-ngfw) import module.vdss-host-project.google_project.project[0] real-net-vdss-host" \
    "$RESTORE_CALLS"
fi

# 8. Choice 3 rejects missing REGION before running gcloud or terraform.
cat > "${ISO_ROOT}/scripts/config.env" << 'EOF'
PREFIX="pfx"
BILLING_ACCOUNT="000000-AAAAAA-000000"
EOF
run_restore "${ISO_ROOT}/scripts/restore.sh" $'y\n3\n'
assert_equals "choice 3 fails when REGION is unset" "1" "$RESTORE_STATUS"
assert_equals "choice 3 makes no tool calls when REGION is unset" "" "$RESTORE_CALLS"

echo ""
echo "Summary: ${TEST_COUNT} restore.sh unit tests run, ${FAIL_COUNT} failures."

if [[ ${FAIL_COUNT} -gt 0 ]]; then
  exit 1
fi
exit 0
