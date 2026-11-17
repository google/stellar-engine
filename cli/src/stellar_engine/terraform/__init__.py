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

"""Runs Terraform for `stellar deploy` and reads the plans it saves.

`env` builds the child environment, `runner` runs the binary and keeps a
log of every command, `plan` parses `terraform show -json`, and `guards`
decides which plans may be applied, which need the operator's
confirmation and which are refused.
"""
