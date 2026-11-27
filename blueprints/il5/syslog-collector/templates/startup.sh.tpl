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

readonly LOG_PROJECT_ID="${log_project_id}"
readonly SYSLOG_PORT="${syslog_port}"
readonly HEALTH_CHECK_PORT="${health_check_port}"

readonly RUNTIME_DIR="/run/fluent-bit-tls"
readonly CONFIG_DIR="/etc/fluent-bit"
readonly CONFIG_FILE="$${CONFIG_DIR}/fluent-bit.conf"
readonly STATE_DIR="/var/lib/fluent-bit"
readonly STORAGE_DIR="$${STATE_DIR}/buffer"
readonly TLS_FETCH_BIN="/usr/local/sbin/fluent-bit-tls-fetch"
readonly TLS_UNIT_FILE="/etc/systemd/system/fluent-bit-tls.service"
readonly SYSTEMD_DROPIN_DIR="/etc/systemd/system/fluent-bit.service.d"
readonly SYSTEMD_DROPIN_FILE="$${SYSTEMD_DROPIN_DIR}/10-tls-dependency.conf"

require_binary() {
  local bin="$1"
  if ! command -v "$${bin}" >/dev/null 2>&1; then
    echo "ERROR: Pre-baked binary '$${bin}' missing in golden image." >&2
    exit 1
  fi
}

# Write stdin to dest through an atomic rename so systemd, Fluent Bit, and a
# running fluent-bit-tls.service never read a partially written file.
write_file() {
  local mode="$1"
  local owner="$2"
  local dest="$3"
  local tmp
  tmp="$(mktemp "$${dest}.tmp.XXXXXX")"
  cat > "$${tmp}"
  chown "$${owner}" "$${tmp}"
  chmod "$${mode}" "$${tmp}"
  mv -f "$${tmp}" "$${dest}"
}

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

install -d -m 0750 -o root -g "$${fb_group}" "$${CONFIG_DIR}"
# Keep filesystem buffer chunks private to the Fluent Bit service identity.
install -d -m 0700 -o "$${fb_user}" -g "$${fb_group}" \
  "$${STATE_DIR}" "$${STORAGE_DIR}"
install -d -m 0755 "$${SYSTEMD_DROPIN_DIR}" "$(dirname "$${TLS_FETCH_BIN}")"

if [[ ! -f "$${CONFIG_DIR}/parsers.conf" && \
  -f /opt/fluent-bit/etc/parsers.conf ]]; then
  install -m 0644 /opt/fluent-bit/etc/parsers.conf \
    "$${CONFIG_DIR}/parsers.conf"
fi

# Install the TLS fetch script and a oneshot unit that systemd runs before
# fluent-bit.service on every boot. The unit has no ordering dependency on
# google-startup-scripts.service, so starting it from this script cannot
# deadlock, and reboots fetch TLS material without this script.
write_file 0700 root:root "$${TLS_FETCH_BIN}" <<'TLS_FETCH_EOF'
${tls_fetch_script}
TLS_FETCH_EOF

write_file 0644 root:root "$${TLS_UNIT_FILE}" <<EOF
[Unit]
Description=Fetch Fluent Bit TLS material from Regional Secret Manager
Wants=network-online.target
After=network-online.target
Before=fluent-bit.service

[Service]
Type=oneshot
RemainAfterExit=yes
UMask=0077
TimeoutStartSec=300
ExecStart=$${TLS_FETCH_BIN}

[Install]
WantedBy=multi-user.target
EOF

# fluent-bit.service never starts without TLS material, and it stops or
# restarts whenever fluent-bit-tls.service is stopped or restarted.
write_file 0644 root:root "$${SYSTEMD_DROPIN_FILE}" <<'EOF'
[Unit]
Requires=fluent-bit-tls.service
After=fluent-bit-tls.service
EOF

# Buffer chunks on the CMEK boot disk so Cloud Logging outages delay delivery
# instead of dropping logs or pausing the TLS listener. Filesystem storage
# bounds memory with storage.max_chunks_up (Mem_Buf_Limit only caps a
# storage.type memory fallback) and disk with storage.total_limit_size,
# which discards the oldest chunks first. Retry_Limit no_limits retries until
# delivery or eviction, and scheduler.cap limits retry backoff to 300 seconds.
write_file 0640 "root:$${fb_group}" "$${CONFIG_FILE}" <<EOF
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
    scheduler.cap 300
    storage.path $${STORAGE_DIR}/
    storage.max_chunks_up 128

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
    Mem_Buf_Limit 64M
    storage.type filesystem
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
    Retry_Limit no_limits
    storage.total_limit_size 5G
EOF

# Open only syslog and health-check ports without flushing host nftables rules.
if command -v firewall-cmd >/dev/null 2>&1 && \
  systemctl is-active --quiet firewalld; then
  firewall-cmd --permanent --add-port="$${SYSLOG_PORT}/tcp"
  firewall-cmd --permanent --add-port="$${HEALTH_CHECK_PORT}/tcp"
  firewall-cmd --reload
fi

if command -v restorecon >/dev/null 2>&1; then
  restorecon -R \
    "$${CONFIG_DIR}" "$${STATE_DIR}" "$${SYSTEMD_DROPIN_DIR}" \
    "$${TLS_UNIT_FILE}" "$${TLS_FETCH_BIN}" || true
fi

systemctl daemon-reload
systemctl enable fluent-bit-tls.service fluent-bit.service
systemctl start fluent-bit-tls.service

# Validate config syntax and mTLS directives before restarting the service so
# older Fluent Bit binaries or broken TLS inputs fail closed immediately.
"$${FB_BIN}" --dry-run -c "$${CONFIG_FILE}"

systemctl reset-failed fluent-bit.service || true
systemctl restart fluent-bit.service
systemctl is-active --quiet fluent-bit.service
