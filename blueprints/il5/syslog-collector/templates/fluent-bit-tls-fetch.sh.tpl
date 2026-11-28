#!/usr/bin/env bash
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Fetches the Fluent Bit TLS server certificate, server key, and client CA
# bundle from Regional Secret Manager into RAM-backed /run/fluent-bit-tls.
# fluent-bit-tls.service runs this script before fluent-bit.service on every
# boot, so reboots load TLS material without the instance startup script.

set -euo pipefail
umask 077

readonly REGION="${region}"
readonly SECRET_PROJECT_ID="${secret_project_id}"
readonly SERVER_CERT_SECRET_ID="${server_cert_secret_id}"
readonly SERVER_KEY_SECRET_ID="${server_key_secret_id}"
readonly CLIENT_CA_SECRET_ID="${client_ca_secret_id}"

# Store TLS material in a dedicated tmpfs directory outside systemd
# RuntimeDirectory=fluent-bit cleanup paths.
readonly RUNTIME_DIR="/run/fluent-bit-tls"

# Route Secret Manager API requests strictly to the regional endpoint.
readonly SM_ENDPOINT="https://secretmanager.$${REGION}.rep.googleapis.com/"
export CLOUDSDK_API_ENDPOINT_OVERRIDES_SECRETMANAGER="$${SM_ENDPOINT}"
export CLOUDSDK_CORE_DISABLE_PROMPTS=1

cleanup_tmp() {
  rm -f "$${RUNTIME_DIR}"/*.tmp.*
}
trap cleanup_tmp EXIT

# Mirror the FB_BIN fallback: Snap-packaged Google Cloud CLI images install
# gcloud under /snap/bin.
if command -v gcloud >/dev/null 2>&1; then
  GCLOUD_BIN="$(command -v gcloud)"
elif [[ -x /snap/bin/gcloud ]]; then
  GCLOUD_BIN="/snap/bin/gcloud"
else
  echo "ERROR: Pre-baked binary 'gcloud' missing in golden image." >&2
  exit 1
fi
readonly GCLOUD_BIN

# Fail closed if /run is not RAM-backed tmpfs so private keys never touch disk.
if command -v findmnt >/dev/null 2>&1; then
  run_fstype="$(findmnt -n -o FSTYPE /run || true)"
  if [[ "$${run_fstype}" != "tmpfs" ]]; then
    echo "ERROR: /run must be mounted as tmpfs (found '$${run_fstype}')." >&2
    exit 1
  fi
fi

# Resolve the service identity configured on the pre-baked fluent-bit unit.
fb_user="$(
  systemctl show -p User --value fluent-bit.service 2>/dev/null || true
)"
fb_group="$(
  systemctl show -p Group --value fluent-bit.service 2>/dev/null || true
)"
if [[ -z "$${fb_user}" ]]; then
  fb_user="root"
fi
if [[ -z "$${fb_group}" ]]; then
  fb_group="$(id -gn "$${fb_user}")"
fi

install -d -m 0700 -o "$${fb_user}" -g "$${fb_group}" "$${RUNTIME_DIR}"

fetch_regional_secret() {
  local secret_id="$1"
  local dest_path="$2"
  local tmp_path="$${dest_path}.tmp.$$"
  local attempt=1
  local max_attempts=5
  local delay=2

  while (( attempt <= max_attempts )); do
    rm -f "$${tmp_path}"
    if "$${GCLOUD_BIN}" secrets versions access latest \
      --project="$${SECRET_PROJECT_ID}" \
      --location="$${REGION}" \
      --secret="$${secret_id}" \
      --out-file="$${tmp_path}"; then
      if [[ -s "$${tmp_path}" ]]; then
        chown "$${fb_user}:$${fb_group}" "$${tmp_path}"
        chmod 0600 "$${tmp_path}"
        mv -f "$${tmp_path}" "$${dest_path}"
        return 0
      fi
    fi
    rm -f "$${tmp_path}"
    if (( attempt < max_attempts )); then
      sleep "$${delay}"
      delay=$(( delay * 2 ))
    fi
    attempt=$(( attempt + 1 ))
  done

  echo "ERROR: Failed to fetch regional secret '$${secret_id}'." >&2
  return 1
}

fetch_regional_secret "$${SERVER_CERT_SECRET_ID}" "$${RUNTIME_DIR}/server.crt"
fetch_regional_secret "$${SERVER_KEY_SECRET_ID}" "$${RUNTIME_DIR}/server.key"
fetch_regional_secret "$${CLIENT_CA_SECRET_ID}" "$${RUNTIME_DIR}/client-ca.crt"

if command -v restorecon >/dev/null 2>&1; then
  restorecon -R "$${RUNTIME_DIR}" || true
fi
