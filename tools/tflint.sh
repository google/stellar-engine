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

# Runs tflint with the repository's .tflint.hcl on every Terraform directory
# under fast/, blueprints/ and modules/, and fails if any directory reports an
# issue. Extra arguments are passed to tflint, for example `-f compact`.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Modules synced from upstream Cloud Foundation Fabric before Fabric adopted
# the naming rule in v55.4.0. The upstream sync that #308 tracks brings the
# upstream renames, moved blocks and tflint-ignore annotations, and removes
# this list.
UPSTREAM_PENDING_SYNC=(
  modules/billing-account
  modules/folder
  modules/iam-service-account
  modules/ncc-spoke-ra
  modules/net-firewall-policy
  modules/net-lb-int/recipe-ilb-next-hop
  modules/net-vpc-firewall
  modules/net-vpn-dynamic
  modules/net-vpn-static
  modules/organization
  modules/project
)

# Only the naming rule is enforced for now, because the recommended preset
# still reports existing findings. Label names are static, so tflint does not
# need to evaluate module calls, which also avoids evaluation errors in
# blueprints whose variables default to null.
TFLINT_ARGS=(
  --config "${REPO_ROOT}/.tflint.hcl"
  --only=terraform_naming_convention
  --call-module-type=none
)

is_pending_sync() {
  local dir="$1" pending
  for pending in "${UPSTREAM_PENDING_SYNC[@]}"; do
    if [[ "${dir}" == "${pending}" || "${dir}" == "${pending}"/* ]]; then
      return 0
    fi
  done
  return 1
}

command -v tflint >/dev/null || {
  echo "tflint not found; install it from https://github.com/terraform-linters/tflint"
  exit 1
}

cd "${REPO_ROOT}"

FAILED=0
TOTAL=0
while IFS= read -r dir; do
  if is_pending_sync "${dir}"; then
    continue
  fi
  TOTAL=$((TOTAL + 1))
  if ! tflint --chdir="${dir}" "${TFLINT_ARGS[@]}" "$@"; then
    echo "tflint failed in ${dir}"
    FAILED=$((FAILED + 1))
  fi
done < <(
  find fast blueprints modules \
    \( -name .git -o -name .terraform -o -name .venv -o -name venv \
    -o -name node_modules -o -name __pycache__ \) -prune \
    -o -type f -name '*.tf' -exec dirname {} + | sort -u
)

echo "tflint checked ${TOTAL} directories, ${FAILED} failed."
if [[ ${TOTAL} -eq 0 ]]; then
  echo "No Terraform directories found."
  exit 1
fi
if [[ ${FAILED} -gt 0 ]]; then
  exit 1
fi
