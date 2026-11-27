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

# Best-effort Compute Engine shutdown script. Stopping gitlab-runner.service
# first lets the blueprint drop-in (KillSignal=SIGQUIT, KillMode=mixed, and
# a bounded TimeoutStopSec) drain running jobs. With runner authentication
# tokens (glrt-), unregister then removes only this VM's runner manager; the
# runner record stays in GitLab.

systemctl stop gitlab-runner.service || true
gitlab-runner unregister --config /etc/gitlab-runner/config.toml \
  --all-runners || true
