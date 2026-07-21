#!/bin/bash
# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
set -euo pipefail

# STIG SV-230489 (RHEL-08-040002) — sendmail must not be installed.
if rpm -q sendmail &>/dev/null; then
  dnf remove -y sendmail
fi

# Install Postfix if not present — RHUI egress rule allows access to
# Google's RHEL Update Infrastructure (35.190.247.13) for package operations.
if ! command -v postfix &>/dev/null; then
  dnf install -y postfix
fi

tee /etc/postfix/main.cf > /dev/null << 'POSTFIX_EOF'
myhostname = ${smtp_hostname}
mydomain = ${smtp_domain}

relayhost = [${disa_relay_host}]:${disa_relay_port}

inet_interfaces = all
mynetworks = 127.0.0.0/8 ${allowed_networks}

smtp_tls_security_level = encrypt
smtp_tls_mandatory_protocols = !SSLv2, !SSLv3, !TLSv1, !TLSv1.1
smtp_tls_protocols = !SSLv2, !SSLv3, !TLSv1, !TLSv1.1
smtp_tls_mandatory_ciphers = high
smtp_tls_fingerprint_digest = sha256
smtp_tls_loglevel = 1

# STIG SV-230550 (RHEL-08-040290) — prevent unrestricted mail relaying.
smtpd_client_restrictions = permit_mynetworks, reject
smtpd_relay_restrictions = permit_mynetworks, reject

disable_vrfy_command = yes

maillog_file = /var/log/maillog
POSTFIX_EOF

systemctl enable postfix
systemctl restart postfix
