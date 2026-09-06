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

import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
GEM4GOV_PATH = os.path.join(REPO_ROOT, 'blueprints', 'fedramp-high', 'gemini-enterprise', 'gem4gov-cli')
TOOLS_PATH = os.path.join(REPO_ROOT, 'tools')

for p in (REPO_ROOT, GEM4GOV_PATH, TOOLS_PATH):
  if p not in sys.path:
    sys.path.insert(0, p)
