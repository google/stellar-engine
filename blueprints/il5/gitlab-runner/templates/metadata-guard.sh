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

# Drops traffic from Docker bridge networks to the Compute Engine metadata
# server so CI job and service containers cannot read the runner service
# account token or instance metadata. gitlab-runner-metadata-guard.service
# runs this script after every docker.service start.

set -euo pipefail

add_drop_rule() {
  local ipt="$1"
  local dest="$2"
  "${ipt}" -w -N DOCKER-USER 2>/dev/null || true
  if ! "${ipt}" -w -C DOCKER-USER -d "${dest}" -j DROP 2>/dev/null; then
    "${ipt}" -w -I DOCKER-USER 1 -d "${dest}" -j DROP
  fi
}

# Docker only sends bridge traffic through DOCKER-USER when its iptables
# integration jumps there from FORWARD, so fail closed when it does not.
if ! iptables -w -C FORWARD -j DOCKER-USER 2>/dev/null; then
  echo "ERROR: FORWARD does not jump to DOCKER-USER; Docker must manage" \
    "iptables rules." >&2
  exit 1
fi
add_drop_rule iptables 169.254.169.254/32

# fd20:ce::254 serves metadata on IPv6-only instances.
if command -v ip6tables >/dev/null 2>&1 &&
  ip6tables -w -L -n >/dev/null 2>&1; then
  add_drop_rule ip6tables fd20:ce::254/128
fi
