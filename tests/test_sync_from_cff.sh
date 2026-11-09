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

# The assertions take code as single-quoted strings and evaluate them later.
# shellcheck disable=SC2016,SC2294

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

TEST_COUNT=0
FAIL_COUNT=0

assert_true() {
  local desc="$1"
  shift
  TEST_COUNT=$((TEST_COUNT + 1))
  if eval "$@"; then
    echo "  [PASS] ${desc}"
  else
    echo "  [FAIL] ${desc}"
    FAIL_COUNT=$((FAIL_COUNT + 1))
  fi
}

assert_equals() {
  local desc="$1"
  local expected="$2"
  local actual="$3"
  TEST_COUNT=$((TEST_COUNT + 1))
  if [[ "$expected" == "$actual" ]]; then
    echo "  [PASS] ${desc}"
  else
    echo "  [FAIL] ${desc} (expected '$expected', got '$actual')"
    FAIL_COUNT=$((FAIL_COUNT + 1))
  fi
}

TMP="$(mktemp -d)"
trap 'rm -rf "${TMP}"' EXIT

export GIT_AUTHOR_NAME="Test" GIT_AUTHOR_EMAIL="test@example.com"
export GIT_COMMITTER_NAME="Test" GIT_COMMITTER_EMAIL="test@example.com"
export GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_GLOBAL=/dev/null

# versions_tf MODULE TAG PROVIDER_MAJOR prints a Fabric-style versions.tf.
versions_tf() {
  cat <<EOF
terraform {
  required_version = ">= 1.10.2"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= ${3}.0.0, < $(($3 + 1)).0.0"
    }
  }
  provider_meta "google" {
    module_name = "google-pso-tool/cloud-foundation-fabric/modules/${1}:${2}-tf"
  }
}
EOF
}

# Builds an upstream repository with releases v1.0.0 and v2.0.0.
UP="${TMP}/upstream"
mkdir -p "${UP}"
git -C "${UP}" init -q
(
  cd "${UP}"
  mkdir -p modules/alpha modules/beta modules/gamma modules/delta \
    modules/project modules/newmod
  printf 'line 1 v1\nline 2\nline 3\nline 4\nline 5\n' >modules/alpha/main.tf
  versions_tf alpha v1.0.0 6 >modules/alpha/versions.tf
  printf 'gone v1\n' >modules/alpha/gone.tf
  printf 'beta v1\n' >modules/beta/main.tf
  printf 'tofu v1\n' >modules/beta/versions.tofu
  versions_tf beta v1.0.0 6 >modules/beta/versions.tf
  printf 'gamma\n' >modules/gamma/main.tf
  printf 'old\n' >modules/gamma/old.tf
  printf 'shared v1\n' >modules/alpha/shared.json
  ln -s ../alpha/shared.json modules/gamma/shared.json
  versions_tf gamma v1.0.0 6 >modules/gamma/versions.tf
  printf 'delta v1\n' >modules/delta/main.tf
  versions_tf project v1.0.0 6 >modules/project/versions.tf
  versions_tf newmod v1.0.0 6 >modules/newmod/versions.tf
  mkdir -p tests/fixtures tests/examples tools
  printf 'fixture v1\n' >tests/fixtures/shared.tf
  printf 'old fixture\n' >tests/fixtures/old.tf
  printf 'def a():\n  return 1\n\n\ndef b():\n  return 2\n' >tools/tool.py
  printf 'def helper():\n  return 1\n' >tests/examples/utils.py
  printf 'not tracked\n' >tests/examples/test_plan.py
  printf '# Changelog\n' >CHANGELOG.md
  git add -A && git commit -q -m v1 && git tag v1.0.0

  printf 'line 1 v2\nline 2\nline 3\nline 4\nline 5\n' >modules/alpha/main.tf
  printf 'new\n' >modules/alpha/new.tf
  git rm -q modules/alpha/gone.tf
  printf '#!/bin/sh\n' >modules/gamma/run.sh
  chmod +x modules/gamma/run.sh
  printf 'module "dep" {\n  source = "../newmod"\n}\n' >modules/alpha/dep.tf
  versions_tf alpha v2.0.0 7 >modules/alpha/versions.tf
  printf 'beta v2\n' >modules/beta/main.tf
  printf 'tofu v2\n' >modules/beta/versions.tofu
  versions_tf beta v2.0.0 7 >modules/beta/versions.tf
  git rm -q modules/gamma/old.tf
  rm modules/gamma/shared.json
  printf 'gamma copy v2\n' >modules/gamma/shared.json
  ln -s main.tf modules/gamma/link.tf
  versions_tf gamma v2.0.0 7 >modules/gamma/versions.tf
  printf 'delta v2\n' >modules/delta/main.tf
  versions_tf project v2.0.0 7 >modules/project/versions.tf
  printf 'fixture v2\n' >tests/fixtures/shared.tf
  printf 'new fixture\n' >tests/fixtures/new.tf
  git rm -q tests/fixtures/old.tf
  printf 'def a():\n  return 10\n\n\ndef b():\n  return 2\n' >tools/tool.py
  printf 'def helper():\n  return 2\n' >tests/examples/utils.py
  printf 'not tracked v2\n' >tests/examples/test_plan.py
  cat >CHANGELOG.md <<'EOF'
# Changelog

## [v2.0.0](https://example.com/v2.0.0) - 2026-01-02

### BREAKING CHANGES

- `modules/alpha`: renamed a variable.
- `fast/stages/0-org-setup`: changed a stage.
- `modules/unvendored`: changed a module the fork does not use.

### MODULES

- [[#2](https://example.com/2)] Improve beta <!-- 2026-01-02 -->

## [v1.0.0](https://example.com/v1.0.0) - 2026-01-01

### BREAKING CHANGES

- `modules/alpha`: an older change.
EOF
  git add -A && git commit -q -m v2 && git tag v2.0.0
)

# new_fork DIR builds a fork that last synced from v1.0.0.
new_fork() {
  local fork="$1"
  mkdir -p "${fork}/tools" "${fork}/modules"
  cp "${REPO_ROOT}/tools/sync-from-cff.sh" "${REPO_ROOT}/tools/cff-sync.ignore" \
    "${fork}/tools/"
  printf 'delta delta v1.0.0\n' >"${fork}/tools/cff-sync.bases"
  git -C "${UP}" archive v1.0.0 modules | tar -x -C "${fork}"
  rm -rf "${fork}/modules/beta/versions.tofu" "${fork}/modules/newmod"
  # A local patch far from the upstream change merges cleanly.
  printf 'stellar patch\n' >>"${fork}/modules/alpha/main.tf"
  # A local change on the same line as the upstream change conflicts.
  printf 'beta stellar\n' >"${fork}/modules/beta/main.tf"
  # A Stellar copy of alpha that tracks the upstream alpha module.
  cp -R "${fork}/modules/alpha" "${fork}/modules/alpha-se"
  # A local change to a file that upstream deletes conflicts.
  printf 'gone stellar\n' >"${fork}/modules/alpha/gone.tf"
  git -C "${UP}" show v1.0.0:modules/alpha/main.tf \
    >"${fork}/modules/alpha-se/main.tf"
  # A Stellar-only module without a Fabric module_name.
  mkdir -p "${fork}/modules/local-only"
  printf 'terraform {}\n' >"${fork}/modules/local-only/versions.tf"
  git -C "${fork}" init -q
  git -C "${fork}" add -A
  git -C "${fork}" commit -q -m fork
}

echo "==> Running tools/sync-from-cff.sh Unit Tests"

# 1. A full sync with conflict markers.
FORK="${TMP}/fork"
new_fork "${FORK}"
status=0
"${BASH}" "${FORK}/tools/sync-from-cff.sh" --upstream "file://${UP}" \
  --report "${TMP}/report.md" >"${TMP}/out.txt" 2>&1 || status=$?
assert_equals "exits 3 when a file conflicts" "3" "${status}"
assert_true "resolves latest to v2.0.0" 'grep -q "to v2.0.0" "${TMP}/out.txt"'
assert_true "takes an upstream change into a locally patched file" \
  'grep -q "line 1 v2" "${FORK}/modules/alpha/main.tf"'
assert_true "keeps the local patch in a merged file" \
  'grep -q "stellar patch" "${FORK}/modules/alpha/main.tf"'
assert_true "adds a file that upstream added" \
  '[[ -f "${FORK}/modules/alpha/new.tf" ]]'
assert_true "updates module_name to the target release" \
  'grep -q "modules/alpha:v2.0.0-tf" "${FORK}/modules/alpha/versions.tf"'
assert_true "updates a copy that tracks another upstream module" \
  'grep -q "line 1 v2" "${FORK}/modules/alpha-se/main.tf"'
assert_true "keeps the upstream module name in the copy's module_name" \
  'grep -q "modules/alpha:v2.0.0-tf" "${FORK}/modules/alpha-se/versions.tf"'
assert_true "leaves conflict markers in a conflicting file" \
  'grep -q "^<<<<<<< stellar-engine" "${FORK}/modules/beta/main.tf"'
assert_true "never adds an ignored versions.tofu file" \
  '[[ ! -e "${FORK}/modules/beta/versions.tofu" ]]'
assert_true "deletes a file that upstream deleted" \
  '[[ ! -e "${FORK}/modules/gamma/old.tf" ]]'
assert_true "replaces a link that upstream turned into a file" \
  '[[ ! -L "${FORK}/modules/gamma/shared.json" ]]'
assert_equals "writes the upstream file instead of the link" "gamma copy v2" \
  "$(cat "${FORK}/modules/gamma/shared.json")"
assert_equals "leaves the old link target untouched" "shared v1" \
  "$(cat "${FORK}/modules/alpha/shared.json")"
assert_true "adds a link that upstream added" \
  '[[ -L "${FORK}/modules/gamma/link.tf" ]]'
assert_true "keeps the executable bit of an added file" \
  '[[ -x "${FORK}/modules/gamma/run.sh" ]]'
assert_equals "keeps a local change to a file that upstream deleted" \
  "gone stellar" "$(cat "${FORK}/modules/alpha/gone.tf")"
assert_true "reports a delete conflict as a kept path" \
  'grep -A4 "they are links or binary files" "${TMP}/report.md" | grep -q "modules/alpha/gone.tf"'
assert_equals "syncs a module listed in cff-sync.bases" "delta v2" \
  "$(cat "${FORK}/modules/delta/main.tf")"
assert_equals "records the new base in cff-sync.bases" "delta delta v2.0.0" \
  "$(cat "${FORK}/tools/cff-sync.bases")"
assert_equals "leaves a Stellar-only module alone" "terraform {}" \
  "$(cat "${FORK}/modules/local-only/versions.tf")"
assert_true "reports the conflicting file" \
  'grep -q "modules/beta/main.tf" "${TMP}/report.md"'
assert_true "reports the skipped Stellar-only module" \
  'grep -q "local-only" "${TMP}/report.md"'
assert_true "reports an upstream module that is not vendored" \
  'grep -q "newmod" "${TMP}/report.md"'
assert_true "reports a call to a module that is not vendored" \
  'grep -q "modules/alpha/dep.tf\` calls \`../newmod" "${TMP}/report.md"'
assert_true "flags a provider major version change" \
  'grep -q "new google provider major version" "${TMP}/report.md"'
assert_true "reports a breaking change of a vendored module" \
  'grep -q "v2.0.0: \`modules/alpha\`: renamed a variable." "${TMP}/report.md"'
assert_true "omits breaking changes of FAST stages" \
  '! grep -q "fast/stages" "${TMP}/report.md"'
assert_true "omits breaking changes of modules that are not vendored" \
  '! grep -q "modules/unvendored" "${TMP}/report.md"'
assert_true "omits breaking changes from the base release and earlier" \
  '! grep -q "an older change" "${TMP}/report.md"'

# 2. The ours conflict style keeps the local file.
FORK="${TMP}/fork-ours"
new_fork "${FORK}"
status=0
"${BASH}" "${FORK}/tools/sync-from-cff.sh" --upstream "file://${UP}" --to v2.0.0 \
  --conflict-style ours --report "${TMP}/report-ours.md" >/dev/null 2>&1 ||
  status=$?
assert_equals "exits 3 with the ours style too" "3" "${status}"
assert_equals "keeps the local copy of a conflicting file" "beta stellar" \
  "$(cat "${FORK}/modules/beta/main.tf")"
assert_true "keeps the base release of a module with conflicts" \
  'grep -q "modules/beta:v1.0.0-tf" "${FORK}/modules/beta/versions.tf"'
assert_true "reports the module that keeps its base release" \
  'grep -A4 "keep their base release" "${TMP}/report-ours.md" | grep -q "beta"'
assert_true "still moves a clean module to the target release" \
  'grep -q "modules/gamma:v2.0.0-tf" "${FORK}/modules/gamma/versions.tf"'
git -C "${FORK}" add -A
git -C "${FORK}" commit -q -m "sync with the ours style"
status=0
"${BASH}" "${FORK}/tools/sync-from-cff.sh" --upstream "file://${UP}" --to v2.0.0 \
  >/dev/null 2>&1 || status=$?
assert_equals "a markers rerun after the ours style still conflicts" "3" \
  "${status}"
assert_true "a markers rerun leaves conflict markers" \
  'grep -q "^<<<<<<< stellar-engine" "${FORK}/modules/beta/main.tf"'

# 3. A dry run changes nothing.
FORK="${TMP}/fork-dry"
new_fork "${FORK}"
status=0
"${BASH}" "${FORK}/tools/sync-from-cff.sh" --upstream "file://${UP}" --to v2.0.0 \
  --dry-run >/dev/null 2>&1 || status=$?
assert_equals "a dry run still reports the conflict" "3" "${status}"
assert_equals "a dry run leaves the work tree clean" "" \
  "$(git -C "${FORK}" status --porcelain)"

# 4. A sync with no conflicts exits 0.
FORK="${TMP}/fork-clean"
new_fork "${FORK}"
status=0
"${BASH}" "${FORK}/tools/sync-from-cff.sh" --upstream "file://${UP}" --to v2.0.0 \
  --modules alpha-se,gamma >/dev/null 2>&1 || status=$?
assert_equals "exits 0 without conflicts" "0" "${status}"
assert_equals "--modules limits the sync" "beta stellar" \
  "$(cat "${FORK}/modules/beta/main.tf")"

# 5. Uncommitted changes under modules/ stop the sync.
FORK="${TMP}/fork-dirty"
new_fork "${FORK}"
printf 'dirty\n' >>"${FORK}/modules/gamma/main.tf"
status=0
"${BASH}" "${FORK}/tools/sync-from-cff.sh" --upstream "file://${UP}" --to v2.0.0 \
  >/dev/null 2>&1 || status=$?
assert_equals "refuses to run on uncommitted module changes" "1" "${status}"

FORK="${TMP}/fork-dirty-bases"
new_fork "${FORK}"
printf 'gamma gamma v1.0.0\n' >>"${FORK}/tools/cff-sync.bases"
status=0
"${BASH}" "${FORK}/tools/sync-from-cff.sh" --upstream "file://${UP}" --to v2.0.0 \
  >/dev/null 2>&1 || status=$?
assert_equals "refuses to run on an uncommitted bases file" "1" "${status}"

# 6. Tracked repository paths outside modules/.
FORK="${TMP}/fork-paths"
new_fork "${FORK}"
(
  cd "${FORK}"
  git -C "${UP}" archive v1.0.0 tests/fixtures tests/examples/utils.py \
    tools/tool.py | tar -x -C .
  # The local copy uses 4-space indents and a local change far from the
  # upstream change.
  printf 'def a():\n    return 1\n\n\ndef b():\n    return 3\n' >tools/tool.py
  printf 'def helper():\n    return 1\n' >tests/examples/utils.py
  {
    printf 'tests/fixtures tests/fixtures v1.0.0\n'
    printf 'tests/examples/utils.py tests/examples/utils.py v1.0.0\n'
    printf 'tools/tool.py tools/tool.py v1.0.0\n'
  } >>tools/cff-sync.bases
  printf '#!/bin/bash\nsed "s/^  /    /"\n' >"${TMP}/fake-format.sh"
  git add -A && git commit -q -m "track paths"
)
status=0
CFF_SYNC_PY_FORMAT="bash ${TMP}/fake-format.sh" "${BASH}" \
  "${FORK}/tools/sync-from-cff.sh" --upstream "file://${UP}" --to v2.0.0 \
  --modules tests/fixtures,tests/examples/utils.py,tools/tool.py \
  --report "${TMP}/report-paths.md" >"${TMP}/out-paths.txt" 2>&1 ||
  status=$?
assert_equals "syncs tracked paths without conflicts" "0" "${status}"
assert_equals "updates a file in a tracked directory" "fixture v2" \
  "$(cat "${FORK}/tests/fixtures/shared.tf")"
assert_true "adds a file to a tracked directory" \
  '[[ -f "${FORK}/tests/fixtures/new.tf" ]]'
assert_true "deletes a file from a tracked directory" \
  '[[ ! -e "${FORK}/tests/fixtures/old.tf" ]]'
assert_equals "updates a tracked single file" "$(printf 'def helper():\n    return 2')" \
  "$(cat "${FORK}/tests/examples/utils.py")"
assert_true "leaves untracked files next to a tracked file alone" \
  '[[ ! -e "${FORK}/tests/examples/test_plan.py" ]]'
assert_equals "merges a formatted Python file with a local change" \
  "$(printf 'def a():\n    return 10\n\n\ndef b():\n    return 3')" \
  "$(cat "${FORK}/tools/tool.py")"
assert_true "records the new base of a tracked path" \
  'grep -qx "tests/fixtures tests/fixtures v2.0.0" "${FORK}/tools/cff-sync.bases"'
assert_true "records the new base of a tracked file" \
  'grep -qx "tools/tool.py tools/tool.py v2.0.0" "${FORK}/tools/cff-sync.bases"'
assert_true "keeps the module entries of cff-sync.bases" \
  'grep -qx "delta delta v1.0.0" "${FORK}/tools/cff-sync.bases"'
assert_true "reports a tracked path" \
  'grep -q "| \`tests/fixtures\` | \`tests/fixtures\` | v1.0.0 |" "${TMP}/report-paths.md"'

FORK="${TMP}/fork-paths-conflict"
new_fork "${FORK}"
(
  cd "${FORK}"
  git -C "${UP}" archive v1.0.0 tools/tool.py | tar -x -C .
  printf 'def a():\n    return 5\n\n\ndef b():\n    return 2\n' >tools/tool.py
  printf 'tools/tool.py tools/tool.py v1.0.0\n' >>tools/cff-sync.bases
  git add -A && git commit -q -m "track a conflicting file"
)
status=0
CFF_SYNC_PY_FORMAT="bash ${TMP}/fake-format.sh" "${BASH}" \
  "${FORK}/tools/sync-from-cff.sh" --upstream "file://${UP}" --to v2.0.0 \
  --modules tools/tool.py --conflict-style ours >"${TMP}/out-conflict.txt" \
  2>&1 || status=$?
assert_equals "reports a conflict in a tracked file" "3" "${status}"
assert_true "names the conflicting tracked file" \
  'grep -q "conflict: tools/tool.py" "${TMP}/out-conflict.txt"'
assert_true "keeps the base of a tracked file with conflicts" \
  'grep -qx "tools/tool.py tools/tool.py v1.0.0" "${FORK}/tools/cff-sync.bases"'

printf 'dirty\n' >>"${FORK}/tools/tool.py"
status=0
CFF_SYNC_PY_FORMAT="bash ${TMP}/fake-format.sh" "${BASH}" \
  "${FORK}/tools/sync-from-cff.sh" --upstream "file://${UP}" --to v2.0.0 \
  >/dev/null 2>&1 || status=$?
assert_equals "refuses to run on an uncommitted tracked path" "1" "${status}"

echo ""
echo "Summary: ${TEST_COUNT} tests run, ${FAIL_COUNT} failures."
if [[ ${FAIL_COUNT} -gt 0 ]]; then
  exit 1
fi
