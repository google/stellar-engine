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

import importlib
import os
import sys
from unittest.mock import MagicMock

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
GEM4GOV_PATH = os.path.join(REPO_ROOT, 'blueprints', 'fedramp-high', 'gemini-enterprise', 'gem4gov-cli')
TOOLS_PATH = os.path.join(REPO_ROOT, 'tools')

if GEM4GOV_PATH not in sys.path:
  sys.path.insert(0, GEM4GOV_PATH)
if TOOLS_PATH not in sys.path:
  sys.path.insert(0, TOOLS_PATH)

# Graceful fallback mocks for dependencies if not installed in minimal environments
for mod_name in [
    'click',
    'google',
    'google.auth',
    'google.api_core',
    'google.api_core.client_options',
    'googleapiclient',
    'googleapiclient.discovery',
    'googleapiclient.errors',
    'marko',
]:
  if mod_name not in sys.modules:
    try:
      importlib.import_module(mod_name)
    except ImportError:
      sys.modules[mod_name] = MagicMock()

if 'google' in sys.modules and 'google.auth' in sys.modules:
  setattr(sys.modules['google'], 'auth', sys.modules['google.auth'])
if 'google' in sys.modules and 'google.api_core' in sys.modules:
  setattr(sys.modules['google'], 'api_core', sys.modules['google.api_core'])
if 'google.api_core' in sys.modules and 'google.api_core.client_options' in sys.modules:
  setattr(sys.modules['google.api_core'], 'client_options', sys.modules['google.api_core.client_options'])
if 'googleapiclient' in sys.modules and 'googleapiclient.discovery' in sys.modules:
  setattr(sys.modules['googleapiclient'], 'discovery', sys.modules['googleapiclient.discovery'])
if 'googleapiclient' in sys.modules and 'googleapiclient.errors' in sys.modules:
  setattr(sys.modules['googleapiclient'], 'errors', sys.modules['googleapiclient.errors'])
