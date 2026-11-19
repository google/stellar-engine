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

# Unit tests for tools/run_terraform_tests.sh using a stub terraform binary.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUNNER="${REPO_ROOT}/tools/run_terraform_tests.sh"

TMP_ROOT="$(mktemp -d)"
trap 'rm -rf "${TMP_ROOT}"' EXIT

PASS=0
FAIL=0

assert_eq() {
  local name="$1" expected="$2" actual="$3"
  if [ "${expected}" = "${actual}" ]; then
    echo "  [PASS] ${name}"
    PASS=$((PASS + 1))
  else
    echo "  [FAIL] ${name}: expected '${expected}', got '${actual}'" >&2
    FAIL=$((FAIL + 1))
  fi
}

make_sandbox() {
  local dir="$1"
  mkdir -p "${dir}/tools" "${dir}/blueprints/il5/sample/tests" "${dir}/blueprints/fedramp-high" "${dir}/fast" "${dir}/modules" "${dir}/bin"
  cp "${RUNNER}" "${dir}/tools/run_terraform_tests.sh"
  chmod +x "${dir}/tools/run_terraform_tests.sh"
  touch "${dir}/blueprints/il5/sample/tests/plan.tftest.hcl"
  ln -s "../il5/sample" "${dir}/blueprints/fedramp-high/sample"
  cat > "${dir}/bin/terraform" <<'EOF'
#!/bin/bash
echo "$(pwd) $*" >> "${STUB_LOG}"
if [ -n "${STUB_ENV_LOG:-}" ] && [ "$1" = "test" ]; then
  printf 'ADC=%s CRED=%s TOKEN=%s\n' \
    "${GOOGLE_APPLICATION_CREDENTIALS:-}" \
    "${GOOGLE_CREDENTIALS:-}" \
    "${GOOGLE_OAUTH_ACCESS_TOKEN:-}" > "${STUB_ENV_LOG}"
fi
if [ "${STUB_FAIL_TEST:-0}" = "1" ] && [ "$1" = "test" ]; then
  exit 1
fi
exit 0
EOF
  chmod +x "${dir}/bin/terraform"
}

echo "Running tools/run_terraform_tests.sh unit tests..."

# 1. Discovers canonical directory once and skips symlink alias.
SB1="${TMP_ROOT}/sb1"
make_sandbox "${SB1}"
LOG1="${TMP_ROOT}/log1.txt"
: > "${LOG1}"
OUT1="$(PATH="${SB1}/bin:${PATH}" STUB_LOG="${LOG1}" bash "${SB1}/tools/run_terraform_tests.sh")"
INIT_COUNT="$(grep -c "init -backend=false -input=false" "${LOG1}")"
TEST_COUNT="$(grep -c " test$" "${LOG1}")"
assert_eq "canonical discovery runs init once" "1" "${INIT_COUNT}"
assert_eq "canonical discovery runs test once" "1" "${TEST_COUNT}"
assert_eq "summary reports 1 directory 0 failed" "1" "$(printf '%s\n' "${OUT1}" | grep -c 'checked 1 directories, 0 failed.')"

# 2. Fails closed when terraform test exits non-zero.
LOG2="${TMP_ROOT}/log2.txt"
: > "${LOG2}"
RC2=0
PATH="${SB1}/bin:${PATH}" STUB_LOG="${LOG2}" STUB_FAIL_TEST=1 bash "${SB1}/tools/run_terraform_tests.sh" >/dev/null 2>&1 || RC2=$?
assert_eq "fails closed on terraform test error" "1" "${RC2}"

# 3. Fails closed when an explicit directory argument does not exist.
RC3=0
PATH="${SB1}/bin:${PATH}" STUB_LOG="${LOG2}" bash "${SB1}/tools/run_terraform_tests.sh" blueprints/il5/does-not-exist >/dev/null 2>&1 || RC3=$?
assert_eq "fails closed on missing explicit directory" "1" "${RC3}"

# 4. Scrubs ambient GCP credentials before invoking terraform test.
ENV_LOG="${TMP_ROOT}/env.txt"
PATH="${SB1}/bin:${PATH}" STUB_LOG="${LOG2}" STUB_ENV_LOG="${ENV_LOG}" \
  GOOGLE_CREDENTIALS='placeholder' \
  GOOGLE_OAUTH_ACCESS_TOKEN='placeholder' \
  GOOGLE_APPLICATION_CREDENTIALS='/tmp/should-be-overridden.json' \
  bash "${SB1}/tools/run_terraform_tests.sh" >/dev/null
assert_eq "scrubs ambient GCP credentials" "ADC=/dev/null CRED= TOKEN=" "$(cat "${ENV_LOG}")"

echo "Summary: ${PASS} passed, ${FAIL} failed."
[ "${FAIL}" -eq 0 ]
