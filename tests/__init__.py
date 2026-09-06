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
from unittest.mock import MagicMock

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
GEM4GOV_PATH = os.path.join(REPO_ROOT, 'blueprints', 'fedramp-high', 'gemini-enterprise', 'gem4gov-cli')
TOOLS_PATH = os.path.join(REPO_ROOT, 'tools')

if GEM4GOV_PATH not in sys.path:
  sys.path.insert(0, GEM4GOV_PATH)
if TOOLS_PATH not in sys.path:
  sys.path.insert(0, TOOLS_PATH)

# Graceful fallback mocks for dependencies if not installed in minimal environments
if 'click' not in sys.modules:
  try:
    import click
  except ImportError:
    sys.modules['click'] = MagicMock()

if 'google' not in sys.modules:
  try:
    import google
  except ImportError:
    google_mock = MagicMock()
    sys.modules['google'] = google_mock

if 'google.auth' not in sys.modules:
  try:
    import google.auth
  except ImportError:
    auth_mock = MagicMock()
    sys.modules['google.auth'] = auth_mock
    sys.modules['google'].auth = auth_mock

if 'google.api_core' not in sys.modules:
  try:
    import google.api_core
  except ImportError:
    api_core_mock = MagicMock()
    sys.modules['google.api_core'] = api_core_mock
    sys.modules['google'].api_core = api_core_mock

if 'google.api_core.client_options' not in sys.modules:
  try:
    import google.api_core.client_options
  except ImportError:
    client_options_mock = MagicMock()
    sys.modules['google.api_core.client_options'] = client_options_mock
    sys.modules['google.api_core'].client_options = client_options_mock

if 'googleapiclient' not in sys.modules:
  try:
    import googleapiclient
  except ImportError:
    gapi_mock = MagicMock()
    sys.modules['googleapiclient'] = gapi_mock

if 'googleapiclient.discovery' not in sys.modules:
  try:
    import googleapiclient.discovery
  except ImportError:
    disc_mock = MagicMock()
    sys.modules['googleapiclient.discovery'] = disc_mock
    sys.modules['googleapiclient'].discovery = disc_mock

if 'googleapiclient.errors' not in sys.modules:
  try:
    import googleapiclient.errors
  except ImportError:
    errors_mock = MagicMock()
    sys.modules['googleapiclient.errors'] = errors_mock
    sys.modules['googleapiclient'].errors = errors_mock

if 'marko' not in sys.modules:
  try:
    import marko
  except ImportError:
    sys.modules['marko'] = MagicMock()
