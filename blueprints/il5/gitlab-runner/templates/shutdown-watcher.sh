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

# Compute Engine runs metadata shutdown scripts only after a graceful
# shutdown period ends, so this watcher drains the runner as soon as the
# instance enters PENDING_STOP and then ends the period early.

set -uo pipefail

readonly MD_URL='http://metadata.google.internal/computeMetadata/v1'
readonly STATUS_URL="${MD_URL}/instance/attributes/shutdown-status"

shutdown_status() {
  curl -sf --max-time 10 -H 'Metadata-Flavor: Google' "${STATUS_URL}" ||
    true
}

until [[ "$(shutdown_status)" == "PENDING_STOP" ]]; do
  sleep 5
done

# The gitlab-runner.service drop-in turns this stop into a SIGQUIT drain
# bounded by TimeoutStopSec. The metadata shutdown script then unregisters
# the runner manager during the OS shutdown that follows.
systemctl stop gitlab-runner.service || true
exec shutdown -h now
