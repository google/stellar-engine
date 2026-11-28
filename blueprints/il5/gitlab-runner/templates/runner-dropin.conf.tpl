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

# GitLab Runner treats SIGQUIT as a graceful shutdown: it stops requesting
# jobs and exits once running jobs finish. KillMode=mixed sends the signal
# only to the main process so job processes keep running, and TimeoutStopSec
# bounds the drain before systemd sends SIGKILL.
%{ if executor == "docker" ~}
[Unit]
# Never start the runner unless the metadata server block is in place.
Requires=gitlab-runner-metadata-guard.service
After=gitlab-runner-metadata-guard.service

%{ endif ~}
[Service]
%{ if executor == "docker" ~}
# GitLab Runner reads /root/.docker/config.json and docker-credential-gcloud
# reads its gcloud configuration through HOME, which systemd leaves unset
# for units without User= before systemd 255.
Environment=HOME=/root
%{ endif ~}
# /snap/bin covers images that ship the Google Cloud CLI as a Snap package.
Environment=PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/snap/bin
KillMode=mixed
KillSignal=SIGQUIT
TimeoutStopSec=${stop_timeout_secs}
