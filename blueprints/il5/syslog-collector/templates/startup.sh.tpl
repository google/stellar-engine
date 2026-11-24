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

set -euo pipefail
umask 077

readonly REGION="${region}"
readonly LOG_PROJECT_ID="${log_project_id}"
readonly SECRET_PROJECT_ID="${secret_project_id}"
readonly SERVER_CERT_SECRET_ID="${server_cert_secret_id}"
readonly SERVER_KEY_SECRET_ID="${server_key_secret_id}"
readonly CLIENT_CA_SECRET_ID="${client_ca_secret_id}"
readonly SYSLOG_PORT="${syslog_port}"
readonly HEALTH_CHECK_PORT="${health_check_port}"

# Store TLS material in a dedicated tmpfs directory outside systemd
# RuntimeDirectory=fluent-bit cleanup paths.
readonly RUNTIME_DIR="/run/fluent-bit-tls"
readonly CONFIG_DIR="/etc/fluent-bit"
readonly CONFIG_FILE="$${CONFIG_DIR}/fluent-bit.conf"
readonly SYSTEMD_DROPIN_DIR="/etc/systemd/system/fluent-bit.service.d"
readonly SYSTEMD_DROPIN_FILE="$${SYSTEMD_DROPIN_DIR}/10-startup-order.conf"

# Route Secret Manager API requests strictly to the regional endpoint.
readonly SM_ENDPOINT="https://secretmanager.$${REGION}.rep.googleapis.com/"
export CLOUDSDK_API_ENDPOINT_OVERRIDES_SECRETMANAGER="$${SM_ENDPOINT}"
export CLOUDSDK_CORE_DISABLE_PROMPTS=1

cleanup_tmp() {
  rm -f "$${RUNTIME_DIR}"/*.tmp.*
}
trap cleanup_tmp EXIT

require_binary() {
  local bin="$1"
  if ! command -v "$${bin}" >/dev/null 2>&1; then
    echo "ERROR: Pre-baked binary '$${bin}' missing in golden image." >&2
    exit 1
  fi
}

require_binary gcloud
require_binary systemctl

if command -v fluent-bit >/dev/null 2>&1; then
  FB_BIN="$(command -v fluent-bit)"
elif [[ -x /opt/fluent-bit/bin/fluent-bit ]]; then
  FB_BIN="/opt/fluent-bit/bin/fluent-bit"
else
  echo "ERROR: Pre-baked fluent-bit binary not found in golden image." >&2
  exit 1
fi
readonly FB_BIN

# Fail closed if /run is not RAM-backed tmpfs so private keys never touch disk.
if command -v findmnt >/dev/null 2>&1; then
  run_fstype="$(findmnt -n -o FSTYPE /run || true)"
  if [[ "$${run_fstype}" != "tmpfs" ]]; then
    echo "ERROR: /run must be mounted as tmpfs (found '$${run_fstype}')." >&2
    exit 1
  fi
fi

# Resolve service account identity configured on the pre-baked systemd unit.
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
install -d -m 0750 -o root -g "$${fb_group}" "$${CONFIG_DIR}"

if [[ ! -f "$${CONFIG_DIR}/parsers.conf" && \
  -f /opt/fluent-bit/etc/parsers.conf ]]; then
  install -m 0644 /opt/fluent-bit/etc/parsers.conf \
    "$${CONFIG_DIR}/parsers.conf"
fi

fetch_regional_secret() {
  local secret_id="$1"
  local dest_path="$2"
  local tmp_path="$${dest_path}.tmp.$$"
  local attempt=1
  local max_attempts=5
  local delay=2

  while (( attempt <= max_attempts )); do
    rm -f "$${tmp_path}"
    if gcloud secrets versions access latest \
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

cat > "$${CONFIG_FILE}" <<EOF
[SERVICE]
    Flush 5
    Daemon Off
    Log_Level info
    Parsers_File parsers.conf
    HTTP_Server On
    HTTP_Listen 0.0.0.0
    HTTP_Port $${HEALTH_CHECK_PORT}
    Health_Check On
    HC_Errors_Count 5
    HC_Retry_Failure_Count 5
    HC_Period 60

[INPUT]
    Name syslog
    Tag syslog.rfc5424
    Mode tcp
    Format ${syslog_framing_format}
    Listen 0.0.0.0
    Port $${SYSLOG_PORT}
    Parser syslog-rfc5424
    Buffer_Chunk_Size 32k
    Buffer_Max_Size 64k
    tls On
    tls.verify On
    tls.verify_client_cert On
    tls.min_version TLSv1.2
    tls.ca_file $${RUNTIME_DIR}/client-ca.crt
    tls.crt_file $${RUNTIME_DIR}/server.crt
    tls.key_file $${RUNTIME_DIR}/server.key

[OUTPUT]
    Name stackdriver
    Match syslog.*
    resource gce_instance
    export_to_project_id $${LOG_PROJECT_ID}
    tls On
    tls.verify On
    tls.min_version TLSv1.2
    Retry_Limit 5
EOF

chown "root:$${fb_group}" "$${CONFIG_FILE}"
chmod 0640 "$${CONFIG_FILE}"

# Ensure fluent-bit starts after startup scripts populate tmpfs TLS material on
# reboot so systemd does not crash-loop into StartLimitBurst.
install -d -m 0755 "$${SYSTEMD_DROPIN_DIR}"
cat > "$${SYSTEMD_DROPIN_FILE}" <<'EOF'
[Unit]
After=google-startup-scripts.service
EOF
chmod 0644 "$${SYSTEMD_DROPIN_FILE}"

# Open only syslog and health-check ports without flushing host nftables rules.
if command -v firewall-cmd >/dev/null 2>&1 && \
  systemctl is-active --quiet firewalld; then
  firewall-cmd --permanent --add-port="$${SYSLOG_PORT}/tcp"
  firewall-cmd --permanent --add-port="$${HEALTH_CHECK_PORT}/tcp"
  firewall-cmd --reload
fi

if command -v restorecon >/dev/null 2>&1; then
  restorecon -R \
    "$${RUNTIME_DIR}" "$${CONFIG_DIR}" "$${SYSTEMD_DROPIN_DIR}" || true
fi

# Validate config syntax and mTLS directives before restarting the service so
# older Fluent Bit binaries or broken TLS inputs fail closed immediately.
"$${FB_BIN}" --dry-run -c "$${CONFIG_FILE}"

systemctl daemon-reload
systemctl enable fluent-bit.service
systemctl reset-failed fluent-bit.service || true
systemctl restart fluent-bit.service
systemctl is-active --quiet fluent-bit.service
