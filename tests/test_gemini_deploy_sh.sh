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

# 5. _is_managed_access_level matches exact resource boundaries.
MANAGED_STATE_SAMPLE="google_access_context_manager_access_level.status[0]"
if _is_managed_access_level "$MANAGED_STATE_SAMPLE" "us"; then
  assert_equals "rejects substring match for access level us" "false" "true"
else
  assert_equals "rejects substring match for access level us" "false" "false"
fi
if _is_managed_access_level "google_access_context_manager_access_level.us[0]" "us"; then
  assert_equals "matches exact resource name us" "true" "true"
else
  assert_equals "matches exact resource name us" "true" "false"
fi

# 6. configure_access_policies prefixes levels and avoids default IAP lockout.
ACM_GCLOUD_LOG="${TMP_TEST_DIR}/acm_gcloud.log"
cat > "${STUB_BIN}/gcloud" << 'EOF'
#!/bin/bash
printf '%s\n' "$*" >> "$ACM_GCLOUD_LOG"
exit 0
EOF
chmod +x "${STUB_BIN}/gcloud"

(
  set +u
  export PATH="${STUB_BIN}:${PATH}"
  export ACM_GCLOUD_LOG="$ACM_GCLOUD_LOG"
  export PREFIX="my-team"
  export ACCESS_POLICY_NUMBER="123456"
  export MANAGED_ACCESS_LEVELS=""
  configure_access_policies <<< $'\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n' >/dev/null
  printf '%s|%s|%s\n' \
    "$CREATE_LENIENT_DEVICE_ACCESS" \
    "$CREATE_MODERATE_DEVICE_ACCESS" \
    "$CREATE_STRICT_DEVICE_ACCESS" > "${TMP_TEST_DIR}/acm_flags.out"
)
ACM_FLAGS=$(cat "${TMP_TEST_DIR}/acm_flags.out")
assert_equals "defaults skip all device wrapper levels without lockout" "false|false|false" "$ACM_FLAGS"

DEPLOY_TEXT=$(cat "$DEPLOY_SH")
assert_contains "lenient list prefixes ACM level with ACM_PREFIX" '${PREFIX_PATH}/${ACM_PREFIX}_us' "$DEPLOY_TEXT"
assert_contains "deploy.sh emits strict_device_access_levels" 'strict_device_access_levels     = ${STRICT_STR}' "$DEPLOY_TEXT"
assert_contains "configure_gemini_apps runs post-deploy compliance patches" 'apply_gemini_app_post_deploy_patches' "$DEPLOY_TEXT"

# 7. GCS_INDEX is populated before IMPORT_GCS conditional, and IL4/IL5 omit certificatemanager.
GCS_IMPORT_BLOCK=$(sed -n '/Does the GCS bucket already exist/,/Added GCS Data Store:/p' "$DEPLOY_SH")
GCS_INDEX_LINE=$(grep -n -m1 'GCS_INDEX=' <<<"$GCS_IMPORT_BLOCK" | cut -d: -f1 || true)
IMPORT_IF_LINE=$(grep -n -m1 'IMPORT_GCS' <<<"$GCS_IMPORT_BLOCK" | cut -d: -f1 || true)
TEST_COUNT=$((TEST_COUNT + 1))
if [[ -n "$GCS_INDEX_LINE" && -n "$IMPORT_IF_LINE" && "$GCS_INDEX_LINE" -lt "$IMPORT_IF_LINE" ]]; then
  echo "  [PASS] GCS_INDEX computed before IMPORT_GCS conditional"
else
  echo "  [FAIL] GCS_INDEX should precede IMPORT_GCS check (${GCS_INDEX_LINE:-none} vs ${IMPORT_IF_LINE:-none})"
  FAIL_COUNT=$((FAIL_COUNT + 1))
fi

assert_not_contains "IL4/IL5 API block omits unconditional certificatemanager" 'gcloud services enable discoveryengine.googleapis.com certificatemanager.googleapis.com' "$DEPLOY_TEXT"
assert_contains "certificatemanager guarded outside IL4 and IL5" 'if [[ "$COMPLIANCE_REGIME" != "IL4" && "$COMPLIANCE_REGIME" != "IL5" ]]; then' "$DEPLOY_TEXT"

# 8. apply_gemini_app_post_deploy_patches resolves COMPLIANCE_REGIME from tfvars.
STAGE0_MOCK_DIR="${TMP_TEST_DIR}/gemini-stage-0"
mkdir -p "$STAGE0_MOCK_DIR"
cat > "${STAGE0_MOCK_DIR}/terraform.tfvars" << 'EOF'
compliance_regime = "IL5"
main_project_id   = "mock-proj-1"
EOF
cat > "${STUB_BIN}/terraform" << 'EOF'
#!/bin/bash
case "$*" in
  *"output -raw main_project_id"*) printf 'mock-proj-1\n' ;;
  *"output -json gemini_apps_audit_logs"*) printf '{"eng-1":true}\n' ;;
  *"output -json gemini_apps_model_armor"*) printf '{"eng-1":false}\n' ;;
  *"output -raw model_armor_template_name"*) printf '' ;;
  *) exit 0 ;;
esac
EOF
chmod +x "${STUB_BIN}/terraform"
cat > "${STUB_BIN}/gcloud" << 'EOF'
#!/bin/bash
if [[ "$*" == *"print-access-token"* ]]; then
  printf 'example-test-bearer-value\n'
fi
exit 0
EOF
chmod +x "${STUB_BIN}/gcloud"
CURL_CALLS_LOG="${TMP_TEST_DIR}/curl_calls.log"
cat > "${STUB_BIN}/curl" << 'EOF'
#!/bin/bash
printf '%s\n' "$*" >> "$CURL_CALLS_LOG"
cat >/dev/null
printf '{"observabilityConfig":{"sensitiveLoggingEnabled":true}}\n200\n'
EOF
chmod +x "${STUB_BIN}/curl"

(
  set +u
  cd "$STAGE0_MOCK_DIR" || exit 1
  export PATH="${STUB_BIN}:${PATH}"
  export CURL_CALLS_LOG="$CURL_CALLS_LOG"
  export PROJECT_ID=""
  export COMPLIANCE_REGIME=""
  apply_gemini_app_post_deploy_patches >/dev/null
)
PATCH_CALLS=$(cat "$CURL_CALLS_LOG")
assert_contains "post-deploy patches use ENTERPRISE_WEB_SEARCH when regime loaded from tfvars" 'WEB_GROUNDING_TYPE_ENTERPRISE_WEB_SEARCH' "$PATCH_CALLS"
assert_contains "post-deploy patches disable location context under IL5" '"disableLocationContext": true' "$PATCH_CALLS"

# 9. connect_analytics_dashboard supports Shared VPC and user-writable proxy log.
SSH_GCLOUD_LOG="${TMP_TEST_DIR}/ssh_gcloud.log"
cat > "${STUB_BIN}/gcloud" << 'EOF'
#!/bin/bash
printf '%s\n' "$*" >> "$SSH_GCLOUD_LOG"
exit 0
EOF
chmod +x "${STUB_BIN}/gcloud"

(
  set +u
  export PATH="${STUB_BIN}:${PATH}"
  export SSH_GCLOUD_LOG="$SSH_GCLOUD_LOG"
  hydrate_from_state() {
    export STATE_CONTENT='{
      "outputs": {
        "main_project_id": {"value": "svc-proj-1"},
        "prefix": {"value": "g4g"},
        "region": {"value": "us-east4"},
        "use_shared_vpc": {"value": true},
        "network_project_id": {"value": "net-host-1"},
        "shared_vpc_network_name": {"value": "shared-vpc"},
        "shared_vpc_subnet_name": {"value": "shared-subnet"}
      }
    }'
  }
  connect_analytics_dashboard <<< $'\n\n\n\n\n' >/dev/null
)
SSH_CALLS=$(cat "$SSH_GCLOUD_LOG")
assert_contains "Shared VPC bastion check writes proxy log under HOME" '${HOME:-/tmp}/cloud-run-proxy.log' "$SSH_CALLS"
assert_not_contains "Shared VPC bastion SSH avoids root-only /var/log redirect" '> /var/log/cloud-run-proxy.log' "$SSH_CALLS"

CREATE_GCLOUD_LOG="${TMP_TEST_DIR}/create_gcloud.log"
cat > "${STUB_BIN}/gcloud" << 'EOF'
#!/bin/bash
printf '%s\n' "$*" >> "$CREATE_GCLOUD_LOG"
if [[ "$*" == *"compute instances describe"* ]]; then
  exit 1
fi
exit 0
EOF
chmod +x "${STUB_BIN}/gcloud"

(
  set +u
  export PATH="${STUB_BIN}:${PATH}"
  export CREATE_GCLOUD_LOG="$CREATE_GCLOUD_LOG"
  sleep() { return 0; }
  hydrate_from_state() {
    export STATE_CONTENT='{
      "outputs": {
        "main_project_id": {"value": "svc-proj-1"},
        "prefix": {"value": "g4g"},
        "region": {"value": "us-east4"},
        "use_shared_vpc": {"value": true},
        "network_project_id": {"value": "net-host-1"},
        "shared_vpc_network_name": {"value": "shared-vpc"},
        "shared_vpc_subnet_name": {"value": "shared-subnet"}
      }
    }'
  }
  connect_analytics_dashboard <<< $'\n\n\n\n\n' >/dev/null
)
CREATE_CALLS=$(cat "$CREATE_GCLOUD_LOG")
assert_contains "Shared VPC bastion create passes host network path" '--network=projects/net-host-1/global/networks/shared-vpc' "$CREATE_CALLS"
assert_contains "Shared VPC bastion create passes host subnet path" '--subnet=projects/net-host-1/regions/us-east4/subnetworks/shared-subnet' "$CREATE_CALLS"

# 10. deploy_analytics_dashboard uses analytics_build_sa_email when present.
BUILD_GCLOUD_LOG="${TMP_TEST_DIR}/build_gcloud.log"
cat > "${STUB_BIN}/gcloud" << 'EOF'
#!/bin/bash
printf '%s\n' "$*" >> "$BUILD_GCLOUD_LOG"
exit 0
EOF
chmod +x "${STUB_BIN}/gcloud"

(
  set +u
  export PATH="${STUB_BIN}:${PATH}"
  export BUILD_GCLOUD_LOG="$BUILD_GCLOUD_LOG"
  docker() { return 1; }
  pause() { return 0; }
  hydrate_from_state() {
    export STATE_CONTENT='{
      "outputs": {
        "main_project_id": {"value": "svc-proj-1"},
        "analytics_dataset_id": {"value": "g4g_gemini_analytics"},
        "analytics_sa_email": {"value": "sa@svc-proj-1.iam.gserviceaccount.com"},
        "analytics_build_sa_email": {"value": "build@svc-proj-1.iam.gserviceaccount.com"},
        "analytics_repo_name": {"value": "g4g-gemini-analytics"},
        "region": {"value": "us-east4"}
      }
    }'
  }
  deploy_analytics_dashboard </dev/null >/dev/null
)
BUILD_CALLS=$(cat "$BUILD_GCLOUD_LOG")
assert_contains "deploy_analytics_dashboard passes custom Cloud Build SA" '--service-account=projects/svc-proj-1/serviceAccounts/build@svc-proj-1.iam.gserviceaccount.com' "$BUILD_CALLS"
assert_contains "deploy_analytics_dashboard uses regional user-owned bucket" '--default-buckets-behavior=regional-user-owned-bucket' "$BUILD_CALLS"

# 11. Greenfield PREFIX default, _get_acm_prefix normalization, and analytics_kms_key_id persistence.
assert_equals "_get_acm_prefix defaults empty PREFIX to g4g" "g4g" "$(_get_acm_prefix "")"
assert_equals "_get_acm_prefix converts hyphens" "my_team" "$(_get_acm_prefix "my-team")"
assert_equals "_get_acm_prefix prepends p_ for leading digit" "p_1gov" "$(_get_acm_prefix "1gov")"
assert_equals "_get_acm_prefix prepends p_ for leading hyphen" "p__foo" "$(_get_acm_prefix "-foo")"

GREENFIELD_PREFIX=$(
  set +u
  export IS_BROWNFIELD="false"
  export IS_CUSTOM="false"
  PREFIX=""
  PREFIX_BLOCK=$(sed -n '/# 0\. Prefix Discovery/,/^    fi$/p' "$DEPLOY_SH")
  eval "$PREFIX_BLOCK" <<< $'\n' >/dev/null
  printf '%s' "$PREFIX"
)
assert_equals "Greenfield prompt defaults empty PREFIX to g4g" "g4g" "$GREENFIELD_PREFIX"

cat > "${STUB_BIN}/gcloud" << 'EOF'
#!/bin/bash
printf '%s\n' "$*" >> "$ACM_GCLOUD_LOG"
exit 0
EOF
chmod +x "${STUB_BIN}/gcloud"
DIGIT_ACM_OUT=$(
  set +u
  export PATH="${STUB_BIN}:${PATH}"
  export ACM_GCLOUD_LOG="$ACM_GCLOUD_LOG"
  export PREFIX="1gov"
  export ACCESS_POLICY_NUMBER="123456"
  export MANAGED_ACCESS_LEVELS=""
  configure_access_policies <<< $'\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n'
)
assert_contains "configure_access_policies prefixes digit PREFIX with p_" "prefix: p_1gov" "$DIGIT_ACM_OUT"

TFVARS_SNIPPET=$(sed -n '/# Generate terraform.tfvars/,/Configuration generated in gemini-stage-0/p' "$DEPLOY_SH")
STAGE0_GEN_DIR="${TMP_TEST_DIR}/stage0_gen"
mkdir -p "${STAGE0_GEN_DIR}/gemini-stage-0"
(
  set +u
  cd "$STAGE0_GEN_DIR" || exit 1
  export PROJECT_ID="my-project"
  export ENVIRONMENT="dev"
  export TENANT="ten1"
  export COMPLIANCE_REGIME="FEDRAMP_HIGH"
  export CMEK_US_RESOURCES_KEY="projects/my-project/locations/us/keyRings/kr/cryptoKeys/k"
  export BUCKET_NAME="test-bucket"
  export REGION="us-east4"
  export DOMAIN="example.com"
  export PREFIX="1gov"
  export DEPLOYMENT_TYPE="iap"
  export CERT_MANAGEMENT_CHOICE="self_managed"
  export CUSTOM_DOMAIN=""
  export ACCESS_POLICY_NUMBER="123456"
  export ADMIN_GROUP="admin@example.com"
  export USER_GROUP="users@example.com"
  export ACL_IDP_TYPE="WORKFORCE_IDENTITY"
  export ACL_POOL_NAME="pool"
  export ACL_PROVIDER_ID="provider"
  export USE_SHARED_VPC="false"
  export SHARED_VPC_HOST_PROJECT=""
  export SHARED_VPC_NETWORK=""
  export SHARED_VPC_SUBNET=""
  export SHARED_VPC_PROXY_SUBNET=""
  export CREATE_DS_BOOL="false"
  export ENABLE_ANALYTICS_FLAG="true"
  export CMEK_REGIONAL_ANALYTICS_KEY="projects/my-project/locations/us-east4/keyRings/akr/cryptoKeys/ak"
  export ENABLE_DS_CMEK="true"
  export CREATE_US_ACCESS="true"
  export CREATE_IP_BASED_ACCESS="false"
  export CREATE_TIME_ACCESS="false"
  export CREATE_EXPIRE_ACCESS="false"
  export CREATE_LENIENT_DEVICE_ACCESS="false"
  export CREATE_MODERATE_DEVICE_ACCESS="false"
  export CREATE_STRICT_DEVICE_ACCESS="false"
  export ENABLE_CEP_BOOL="false"
  export ACCESS_START_DAY=""
  export ACCESS_END_DAY=""
  export ACCESS_START_HOUR=""
  export ACCESS_END_HOUR=""
  export ACCESS_TIME_ZONE=""
  export ACCESS_EXPIRATION_TIMESTAMP=""
  export ALLOWED_IPS="[]"
  export APPS_OBJ="{}"
  eval "$TFVARS_SNIPPET" >/dev/null
)
GEN_TFVARS=$(cat "${STAGE0_GEN_DIR}/gemini-stage-0/terraform.tfvars")
assert_contains "fresh gemini-stage-0/terraform.tfvars persists analytics_kms_key_id" 'analytics_kms_key_id        = "projects/my-project/locations/us-east4/keyRings/akr/cryptoKeys/ak"' "$GEN_TFVARS"
assert_contains "digit-prefixed PREFIX writes p_1gov_us in lenient_device_access_levels" 'lenient_device_access_levels    = ["accessPolicies/123456/accessLevels/p_1gov_us"]' "$GEN_TFVARS"
assert_contains "digit-prefixed PREFIX writes p_1gov_us in strict_device_access_levels" 'strict_device_access_levels     = ["accessPolicies/123456/accessLevels/p_1gov_us"]' "$GEN_TFVARS"

echo ""
echo "Summary: ${TEST_COUNT} tests run, ${FAIL_COUNT} failed."
if [[ ${FAIL_COUNT} -gt 0 ]]; then
  exit 1
fi
