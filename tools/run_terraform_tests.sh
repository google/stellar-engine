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

# Discovers canonical (non-symlink) Terraform roots that contain
# tests/*.tftest.hcl under blueprints/, fast/, and modules/ (or explicit
# target directories passed as arguments), initializes each directory offline
# with a shared plugin cache, and runs `terraform test`.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

command -v terraform >/dev/null || {
  echo "terraform not found in PATH." >&2
  exit 1
}

CREATED_CACHE=false
if [ -z "${TF_PLUGIN_CACHE_DIR:-}" ]; then
  TMP_BASE="${TMPDIR:-/tmp}"
  TMP_BASE="${TMP_BASE%/}"
  TF_PLUGIN_CACHE_DIR="$(mktemp -d "${TMP_BASE}/stellar-tf-plugin-cache.XXXXXX")"
  export TF_PLUGIN_CACHE_DIR
  CREATED_CACHE=true
else
  mkdir -p "${TF_PLUGIN_CACHE_DIR}"
fi

cleanup() {
  if [ "${CREATED_CACHE}" = "true" ] && [ -n "${TF_PLUGIN_CACHE_DIR:-}" ]; then
    rm -rf "${TF_PLUGIN_CACHE_DIR}"
  fi
}
trap cleanup EXIT

cd "${REPO_ROOT}"

DIRS=()
if [ "$#" -gt 0 ]; then
  for arg in "$@"; do
    DIRS+=("${arg%/}")
  done
else
  while IFS= read -r tf_dir; do
    [ -n "${tf_dir}" ] && DIRS+=("${tf_dir}")
  done < <(
    find blueprints fast modules \
      \( -name .git -o -name .terraform -o -name .venv -o -name venv \
      -o -name node_modules -o -name __pycache__ \) -prune \
      -o -type f -path '*/tests/*.tftest.hcl' -print |
      awk '{sub(/\/tests\/[^\/]+$/, ""); print}' |
      sort -u
  )
fi

if [ "${#DIRS[@]}" -eq 0 ]; then
  echo "No Terraform test directories found."
  exit 0
fi

FAILED=0
TOTAL=0

for dir in "${DIRS[@]}"; do
  if [ ! -d "${dir}" ]; then
    echo "Terraform test directory not found: ${dir}" >&2
    FAILED=$((FAILED + 1))
    continue
  fi
  TOTAL=$((TOTAL + 1))
  echo "=== Running terraform test in ${dir} ==="
  if ! (
    cd "${dir}"
    terraform init -backend=false -input=false >/dev/null
    # Prevent unmocked Google providers from falling back to ambient ADC or GCE
    # metadata locally, so missing mock_provider blocks fail here as in CI.
    unset GOOGLE_CREDENTIALS GOOGLE_CLOUD_KEYFILE_JSON GCLOUD_KEYFILE_JSON \
      GOOGLE_OAUTH_ACCESS_TOKEN GOOGLE_IMPERSONATE_SERVICE_ACCOUNT \
      CLOUDSDK_AUTH_ACCESS_TOKEN
    GOOGLE_APPLICATION_CREDENTIALS=/dev/null terraform test
  ); then
    echo "terraform test failed in ${dir}" >&2
    FAILED=$((FAILED + 1))
  fi
done

echo "terraform test checked ${TOTAL} directories, ${FAILED} failed."
if [ "${FAILED}" -gt 0 ]; then
  exit 1
fi
