#!/usr/bin/env bash
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

# Hardened GitLab Runner boot registration script for pre-baked golden images.
# Runtime package downloads are intentionally forbidden; required binaries must
# already exist on the golden image.

set -euo pipefail
umask 077

readonly GITLAB_URL='${gitlab_url}'
readonly REGION='${region}'
readonly RUNNER_NAME='${runner_name}'
readonly EXECUTOR='${executor}'
readonly DOCKER_IMAGE='${docker_image}'
readonly SECRET_ID='${secret_id}'
readonly SECRET_PROJECT_ID='${secret_project_id}'
readonly SECRET_VERSION='${secret_version}'
readonly CONFIG_DIR='/etc/gitlab-runner'
readonly CONFIG_FILE="$${CONFIG_DIR}/config.toml"
readonly MAX_ATTEMPTS=5
readonly SM_ENDPOINT="https://secretmanager.$${REGION}.rep.googleapis.com/"

export CLOUDSDK_CORE_DISABLE_PROMPTS=1
export CLOUDSDK_API_ENDPOINT_OVERRIDES_SECRETMANAGER="$${SM_ENDPOINT}"

cleanup() {
  unset CI_SERVER_TOKEN || true
}
trap cleanup EXIT

require_binary() {
  local bin="$1"
  if ! command -v "$${bin}" >/dev/null 2>&1; then
    echo "ERROR: pre-installed binary '$${bin}' missing from image." >&2
    exit 1
  fi
}

start_runner_service() {
  if command -v systemctl >/dev/null 2>&1; then
    systemctl enable --now gitlab-runner
  else
    gitlab-runner start
  fi
}

require_binary gitlab-runner
require_binary gcloud
if [[ "$${EXECUTOR}" == "docker" ]]; then
  require_binary docker
  if command -v systemctl >/dev/null 2>&1; then
    systemctl enable --now docker
  fi
fi

mkdir -p "$${CONFIG_DIR}"
chmod 0700 "$${CONFIG_DIR}"

if [[ -f "$${CONFIG_FILE}" ]] && \
  grep -q '^\[\[runners\]\]' "$${CONFIG_FILE}"; then
  chmod 0600 "$${CONFIG_FILE}"
  start_runner_service
  exit 0
fi

fetch_runner_token() {
  local attempt=1
  local delay=2
  local token=""
  while (( attempt <= MAX_ATTEMPTS )); do
    if token="$(
      gcloud secrets versions access "$${SECRET_VERSION}" \
        --secret="$${SECRET_ID}" \
        --project="$${SECRET_PROJECT_ID}" \
        --location="$${REGION}"
    )" && [[ -n "$${token}" ]]; then
      printf '%s' "$${token}"
      return 0
    fi
    if (( attempt == MAX_ATTEMPTS )); then
      echo "ERROR: failed to fetch runner token from Secret Manager." >&2
      return 1
    fi
    sleep "$${delay}"
    delay=$(( delay * 2 ))
    attempt=$(( attempt + 1 ))
  done
}

# Pass the authentication secret strictly through the CI_SERVER_TOKEN
# environment variable so process listings and audit logs never expose it.
CI_SERVER_TOKEN="$(fetch_runner_token)"
export CI_SERVER_TOKEN

register_args=(
  --non-interactive
  --config "$${CONFIG_FILE}"
  --url "$${GITLAB_URL}"
  --name "$${RUNNER_NAME}"
  --executor "$${EXECUTOR}"
)
if [[ "$${EXECUTOR}" == "docker" ]]; then
  register_args+=(--docker-image "$${DOCKER_IMAGE}")
fi

attempt=1
delay=2
while (( attempt <= MAX_ATTEMPTS )); do
  if gitlab-runner register "$${register_args[@]}"; then
    break
  fi
  if (( attempt == MAX_ATTEMPTS )); then
    unset CI_SERVER_TOKEN
    echo "ERROR: gitlab-runner registration failed." >&2
    exit 1
  fi
  sleep "$${delay}"
  delay=$(( delay * 2 ))
  attempt=$(( attempt + 1 ))
done

unset CI_SERVER_TOKEN

chmod 0600 "$${CONFIG_FILE}"
start_runner_service
