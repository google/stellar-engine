#!/bin/bash
# Copyright 2026 Google LLC
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

# Image must have chrony pre-installed — egress-deny blocks package managers.
if ! command -v chronyd &>/dev/null; then
  echo "ERROR: chronyd not found. Use an image with chrony pre-installed (e.g. RHEL 8)." >&2
  exit 1
fi

tee /etc/chrony.conf > /dev/null << 'CHRONY_EOF'
${server_lines}

${allow_lines}

driftfile /var/lib/chrony/drift
makestep 1.0 3
rtcsync
logdir /var/log/chrony
CHRONY_EOF

# Service unit is 'chronyd' on RHEL, 'chrony' on Debian/Ubuntu.
systemctl enable chronyd 2>/dev/null || systemctl enable chrony
systemctl restart chronyd 2>/dev/null || systemctl restart chrony
