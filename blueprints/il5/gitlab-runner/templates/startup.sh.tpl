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
# Images that ship the Google Cloud CLI as a Snap package install gcloud and
# docker-credential-gcloud under /snap/bin.
export PATH="$${PATH}:/snap/bin"

readonly GITLAB_URL='${gitlab_url}'
readonly REGION='${region}'
readonly RUNNER_NAME='${runner_name}'
readonly EXECUTOR='${executor}'
readonly DOCKER_IMAGE='${docker_image}'
readonly REGISTRY_HOSTS='${registry_hosts}'
readonly SECRET_ID='${secret_id}'
readonly SECRET_PROJECT_ID='${secret_project_id}'
readonly SECRET_VERSION='${secret_version}'
readonly FINGERPRINT='${fingerprint}'
readonly CONFIG_DIR='/etc/gitlab-runner'
readonly CONFIG_FILE="$${CONFIG_DIR}/config.toml"
readonly FINGERPRINT_FILE="$${CONFIG_DIR}/.registration-fingerprint"
readonly UNIT_DIR='/etc/systemd/system'
readonly DROPIN_DIR="$${UNIT_DIR}/gitlab-runner.service.d"
readonly GUARD_UNIT='gitlab-runner-metadata-guard.service'
readonly WATCHER_UNIT='gitlab-runner-shutdown-watcher.service'
readonly METADATA_IPV4='169.254.169.254/32'
readonly MAX_ATTEMPTS=5
readonly SM_ENDPOINT="https://secretmanager.$${REGION}.rep.googleapis.com/"
readonly -a ALLOWED_IMAGES=(
%{ for image in allowed_images ~}
  '${image}'
%{ endfor ~}
)
readonly -a ALLOWED_SERVICES=(
%{ for service in allowed_services ~}
  '${service}'
%{ endfor ~}
)
readonly -a CAP_ADD=(
%{ for cap in cap_add ~}
  '${cap}'
%{ endfor ~}
)

export CLOUDSDK_CORE_DISABLE_PROMPTS=1
export CLOUDSDK_API_ENDPOINT_OVERRIDES_SECRETMANAGER="$${SM_ENDPOINT}"

cleanup() {
  unset CI_SERVER_TOKEN || true
}
trap cleanup EXIT

require_binary() {
  local bin="$1"
  local reason="$${2:-}"
  if ! command -v "$${bin}" >/dev/null 2>&1; then
    echo "ERROR: pre-installed binary '$${bin}' missing from PATH." >&2
    if [[ -n "$${reason}" ]]; then
      echo "ERROR: $${reason}" >&2
    fi
    exit 1
  fi
}

# Atomically writes stdin to a root-owned file with the given mode, so a
# copy that a unit is executing keeps reading the old inode.
install_file() {
  local path="$1"
  local mode="$2"
  local tmp
  tmp="$(mktemp "$${path}.XXXXXX")"
  cat >"$${tmp}"
  chmod "$${mode}" "$${tmp}"
  mv -f "$${tmp}" "$${path}"
}

runner_registered() {
  [[ -f "$${CONFIG_FILE}" ]] && grep -q '^\[\[runners\]\]' "$${CONFIG_FILE}"
}

# Succeeds only when Docker filters bridge traffic through DOCKER-USER and
# the metadata server DROP rule is there. Running the idempotent guard
# script directly also applies rules updated since docker.service started.
metadata_guard_active() {
  systemctl enable --now "$${GUARD_UNIT}" &&
    /usr/local/sbin/gitlab-runner-metadata-guard &&
    iptables -w -C FORWARD -j DOCKER-USER &&
    iptables -w -C DOCKER-USER -d "$${METADATA_IPV4}" -j DROP
}

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

require_binary systemctl
require_binary gitlab-runner
require_binary gcloud
if [[ "$${EXECUTOR}" == "docker" ]]; then
  require_binary docker
  require_binary iptables
  require_binary docker-credential-gcloud \
    "Artifact Registry image pulls need the gcloud Docker credential helper."
fi
%{ if graceful_shutdown ~}
require_binary curl "The graceful shutdown watcher polls the metadata server."
%{ endif ~}

# SIGQUIT drain settings for every executor; for the docker executor the
# drop-in also makes gitlab-runner.service require the metadata guard.
mkdir -p "$${DROPIN_DIR}" /usr/local/sbin
install_file "$${DROPIN_DIR}/50-blueprint.conf" 0644 <<'DROPIN'
${runner_dropin}
DROPIN

if [[ "$${EXECUTOR}" == "docker" ]]; then
  install_file /usr/local/sbin/gitlab-runner-metadata-guard 0700 <<'GUARD'
${guard_script}
GUARD
  install_file "$${UNIT_DIR}/$${GUARD_UNIT}" 0644 <<'UNIT'
${guard_unit}
UNIT
fi
%{ if graceful_shutdown ~}
install_file /usr/local/sbin/gitlab-runner-shutdown-watcher 0700 <<'WATCHER'
${watcher_script}
WATCHER
install_file "$${UNIT_DIR}/$${WATCHER_UNIT}" 0644 <<'UNIT'
${watcher_unit}
UNIT
%{ else ~}
systemctl disable --now "$${WATCHER_UNIT}" >/dev/null 2>&1 || true
rm -f "$${UNIT_DIR}/$${WATCHER_UNIT}" \
  /usr/local/sbin/gitlab-runner-shutdown-watcher
%{ endif ~}
systemctl daemon-reload

if [[ "$${EXECUTOR}" == "docker" ]]; then
  systemctl enable --now docker
  # Fail closed: never register or start the runner while job containers
  # can reach the metadata server.
  if ! metadata_guard_active; then
    systemctl stop gitlab-runner.service || true
    echo "ERROR: metadata server block for job containers is not active;" \
      "refusing to register or start the runner." >&2
    exit 1
  fi
  # gitlab-runner reads pull credentials from root's Docker config, which is
  # operator-owned; recent GitLab Runner releases refuse to run credential
  # helpers named in DOCKER_AUTH_CONFIG unless separately allowlisted.
  mkdir -p /root/.docker
  DOCKER_CONFIG=/root/.docker gcloud auth configure-docker \
    "$${REGISTRY_HOSTS}" --quiet
fi
%{ if graceful_shutdown ~}
# Restart so a watcher started at boot runs the script written above.
systemctl enable "$${WATCHER_UNIT}"
systemctl restart "$${WATCHER_UNIT}"
%{ endif ~}

mkdir -p "$${CONFIG_DIR}"
chmod 0700 "$${CONFIG_DIR}"

# Keep the existing registration only when it was made from the current
# inputs; Terraform updates this script in place without replacing the VM.
if runner_registered && [[ -f "$${FINGERPRINT_FILE}" ]] &&
  [[ "$(<"$${FINGERPRINT_FILE}")" == "$${FINGERPRINT}" ]]; then
  chmod 0600 "$${CONFIG_FILE}"
  systemctl enable --now gitlab-runner.service
  exit 0
fi

# Inputs changed, the fingerprint is missing, or the shutdown script already
# unregistered: drain running jobs and replace the registration.
systemctl stop gitlab-runner.service || true
if runner_registered; then
  gitlab-runner unregister --config "$${CONFIG_FILE}" --all-runners || true
fi
if runner_registered; then
  # gitlab-runner keeps entries that failed to unregister and writes the
  # [[runners]] tables after all global settings, so truncate from there.
  sed -i '/^\[\[runners\]\]/,$d' "$${CONFIG_FILE}"
fi
rm -f "$${FINGERPRINT_FILE}"

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
  # Job containers run unprivileged with every capability dropped, cannot
  # gain privileges through setuid binaries or replace image entrypoints,
  # and may only use allowlisted Artifact Registry images.
  register_args+=(
    --docker-image "$${DOCKER_IMAGE}"
    --docker-privileged=false
    --docker-disable-entrypoint-overwrite
    --docker-cap-drop ALL
    --docker-security-opt no-new-privileges=true
  )
  for image in "$${ALLOWED_IMAGES[@]}"; do
    register_args+=(--docker-allowed-images "$${image}")
  done
  for cap in "$${CAP_ADD[@]}"; do
    register_args+=(--docker-cap-add "$${cap}")
  done
  if (( $${#ALLOWED_SERVICES[@]} == 0 )); then
    # An empty allowed_services list permits any service image, so disable
    # CI services unless an allowlist is configured.
    register_args+=(--docker-services-limit 0)
  else
    register_args+=(
      --docker-services-cap-drop ALL
      --docker-services-security-opt no-new-privileges=true
    )
    for service in "$${ALLOWED_SERVICES[@]}"; do
      register_args+=(--docker-allowed-services "$${service}")
    done
    for cap in "$${CAP_ADD[@]}"; do
      register_args+=(--docker-services-cap-add "$${cap}")
    done
  fi
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
printf '%s\n' "$${FINGERPRINT}" >"$${FINGERPRINT_FILE}"
chmod 0600 "$${FINGERPRINT_FILE}"
systemctl enable --now gitlab-runner.service
