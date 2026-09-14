#!/usr/bin/env python3
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

"""CLI entrypoint and compatibility wrapper for Full Package Provisioning & Dual-Format Hydration.

Core implementation resides in :mod:`compliance_engine.generate_compliance_artifacts`.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_SRC = os.path.abspath(os.path.join(_HERE, '..', 'src'))
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

_is_main = (__name__ == '__main__')
from compliance_engine import generate_compliance_artifacts as _target

for _k in dir(_target):
    if not _k.startswith('__'):
        globals()[_k] = getattr(_target, _k)
sys.modules[__name__] = _target

if _is_main:
    _target.main()
