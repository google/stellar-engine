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
