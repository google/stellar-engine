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
# shellcheck disable=SC2016,SC2034,SC2294

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

TMP="$(mktemp -d)"
trap 'rm -rf "${TMP}"' EXIT

export GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_GLOBAL=/dev/null
export GIT_COMMITTER_NAME="Test" GIT_COMMITTER_EMAIL="test@example.com"

# A fake gh records its arguments and answers the queries the script makes.
mkdir -p "${TMP}/bin"
cat >"${TMP}/bin/gh" <<'EOF'
#!/bin/bash
echo "$*" >>"${GH_LOG}"
case "$1 $2" in
  "pr list") cat "${GH_PR_NUMBER_FILE}" 2>/dev/null || true ;;
  "pr view") cat "${GH_COMMENTS_FILE}" 2>/dev/null || true ;;
esac
exit 0
EOF
chmod +x "${TMP}/bin/gh"
export PATH="${TMP}/bin:${PATH}"
export GH_LOG="${TMP}/gh.log" GH_PR_NUMBER_FILE="${TMP}/pr-number"
export GH_COMMENTS_FILE="${TMP}/comments"

# Builds a remote repository and a checkout of it with a sync result.
git init -q --bare "${TMP}/remote.git"
git clone -q "${TMP}/remote.git" "${TMP}/work" 2>/dev/null
WORK="${TMP}/work"
mkdir -p "${WORK}/tools" "${WORK}/modules/alpha" "${WORK}/.github"
cp "${REPO_ROOT}/tools/cff-sync-pr.sh" "${WORK}/tools/"
cp "${REPO_ROOT}/.github/pull_request_template.md" "${WORK}/.github/"
printf 'v1\n' >"${WORK}/modules/alpha/main.tf"
mkdir -p "${WORK}/tests/fixtures"
printf 'fixture v1\n' >"${WORK}/tests/fixtures/shared.tf"
printf 'alpha alpha v1.0.0\ntests/fixtures tests/fixtures v1.0.0\n' \
  >"${WORK}/tools/cff-sync.bases"
git -C "${WORK}" add -A
git -C "${WORK}" -c user.name=Test -c user.email=test@example.com \
  commit -q -m base
git -C "${WORK}" push -q origin HEAD:refs/heads/main
printf '## Cloud Foundation Fabric sync to v2.0.0\n' >"${TMP}/report.md"

run_pr() {
  # $1 is the sync result to write into modules/alpha/main.tf.
  git -C "${WORK}" checkout -q -B main origin/main 2>/dev/null ||
    git -C "${WORK}" checkout -q main
  printf '%s\n' "$1" >"${WORK}/modules/alpha/main.tf"
  : >"${GH_LOG}"
  (
    cd "${WORK}"
    TARGET=v2.0.0 CONFLICTS="$2" PROVIDER_MAJOR_CHANGE=false \
      REPORT="${TMP}/report.md" bash tools/cff-sync-pr.sh >/dev/null 2>&1
  )
}

remote_head() {
  git -C "${TMP}/remote.git" rev-parse --verify --quiet \
    refs/heads/chore/cff-sync || true
}

echo "==> Running tools/cff-sync-pr.sh Unit Tests"

git -C "${WORK}" fetch -q origin

# 1. The first run pushes the branch and opens a draft pull request.
run_pr "v2" 1
FIRST="$(remote_head)"
assert_true "pushes the sync branch" '[[ -n "${FIRST}" ]]'
assert_true "opens a pull request" 'grep -q "^pr create" "${GH_LOG}"'
assert_true "opens it as a draft when files conflict" \
  'grep "^pr create" "${GH_LOG}" | grep -q -- "--draft"'

# 2. A rerun with the same result keeps the branch and edits the pull request.
printf '7\n' >"${GH_PR_NUMBER_FILE}"
run_pr "v2" 0
assert_true "keeps the branch when the result is unchanged" \
  '[[ "$(remote_head)" == "${FIRST}" ]]'
assert_true "edits the open pull request" 'grep -q "^pr edit 7" "${GH_LOG}"'
assert_true "does not mark a clean sync as a draft" \
  '! grep -q "^pr ready" "${GH_LOG}"'

# 3. A maintainer commit on the branch stops the next run from pushing.
git -C "${WORK}" fetch -q origin chore/cff-sync
git -C "${WORK}" checkout -q -B resolve FETCH_HEAD
printf 'resolved\n' >"${WORK}/modules/alpha/main.tf"
git -C "${WORK}" -c user.name=Maintainer -c user.email=maintainer@example.com \
  commit -q -am "resolve conflicts"
git -C "${WORK}" push -q origin HEAD:refs/heads/chore/cff-sync
RESOLVED="$(remote_head)"
run_pr "v3" 1
assert_true "leaves a branch with maintainer commits unchanged" \
  '[[ "$(remote_head)" == "${RESOLVED}" ]]'
assert_true "comments on the pull request instead" \
  'grep -q "^pr comment 7" "${GH_LOG}"'
assert_true "does not edit the pull request body" \
  '! grep -q "^pr edit" "${GH_LOG}"'

# 4. The comment is posted once per release.
printf '<!-- cff-sync:v2.0.0 -->\n' >"${GH_COMMENTS_FILE}"
run_pr "v3" 1
assert_true "comments only once per release" \
  '! grep -q "^pr comment" "${GH_LOG}"'

# 5. A sync that changes only a tracked path outside modules/ still commits.
git -C "${WORK}" checkout -q -B main origin/main
printf 'fixture v2\n' >"${WORK}/tests/fixtures/shared.tf"
printf 'new fixture\n' >"${WORK}/tests/fixtures/new.tf"
sed -i.bak 's/^tests\/fixtures tests\/fixtures v1.0.0$/tests\/fixtures tests\/fixtures v2.0.0/' \
  "${WORK}/tools/cff-sync.bases"
rm -f "${WORK}/tools/cff-sync.bases.bak"
: >"${GH_LOG}"
rm -f "${GH_PR_NUMBER_FILE}"
(
  cd "${WORK}"
  SYNC_BRANCH=chore/cff-sync-paths TARGET=v2.0.0 CONFLICTS=0 \
    PROVIDER_MAJOR_CHANGE=false REPORT="${TMP}/report.md" \
    bash tools/cff-sync-pr.sh >"${TMP}/paths.txt" 2>&1
)
PATHS_HEAD="$(git -C "${TMP}/remote.git" rev-parse --verify --quiet \
  refs/heads/chore/cff-sync-paths || true)"
assert_true "pushes a sync that changes only a tracked path" \
  '[[ -n "${PATHS_HEAD}" ]]'
assert_true "commits the changed file of a tracked path" \
  '[[ "$(git -C "${TMP}/remote.git" show "${PATHS_HEAD}:tests/fixtures/shared.tf")" == "fixture v2" ]]'
assert_true "commits a new file of a tracked path" \
  'git -C "${TMP}/remote.git" cat-file -e "${PATHS_HEAD}:tests/fixtures/new.tf"'
assert_true "names modules and tooling in the title" \
  'grep "^pr create" "${GH_LOG}" | grep -q "modules and tooling to v2.0.0"'

echo ""
echo "Summary: ${TEST_COUNT} tests run, ${FAIL_COUNT} failures."
if [[ ${FAIL_COUNT} -gt 0 ]]; then
  exit 1
fi
