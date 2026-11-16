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
    if [[ "$*" == *"'^encl1-prod-iac-core-0$'"* ]]; then
      echo "encl1-prod-iac-core-0"
    else
      printf "encl1-prod-iac-core-0\nencl2-prod-iac-core-0\n"
    fi
    ;;
  "iam service-accounts list"*)
    echo "bootstrap-0@encl1-prod-iac-core-0.iam.gserviceaccount.com"
    ;;
  "iam service-accounts describe"*)
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

echo "==> Testing validation.sh --project override skips projects list"
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

echo "==> Testing validation.sh rejects flag-like values and invalid inputs"
if bash "${VALIDATION_SH}" --prefix --help >/dev/null 2>&1; then
  echo "FAIL: --prefix --help should be rejected"
  exit 1
fi
if bash "${VALIDATION_SH}" --project --prefix >/dev/null 2>&1; then
  echo "FAIL: --project --prefix should be rejected"
  exit 1
fi
if bash "${VALIDATION_SH}" --prefix "bad'regex" >/dev/null 2>&1; then
  echo "FAIL: invalid --prefix should be rejected"
  exit 1
fi
if bash "${VALIDATION_SH}" --project "BAD_PROJECT" >/dev/null 2>&1; then
  echo "FAIL: invalid --project should be rejected"
  exit 1
fi

echo "PASS: all validation.sh filtering checks succeeded."
