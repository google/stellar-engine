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

"""Utility script to execute the compliance engine automated test suite."""
import os
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
_SKILL_ROOT = os.path.abspath(os.path.join(_HERE, '..'))
_SRC = os.path.join(_SKILL_ROOT, 'src')
_TESTS = os.path.join(_SKILL_ROOT, 'tests')

for _p in (_SRC, _HERE, _TESTS):
    if _p not in sys.path:
        sys.path.insert(0, _p)

def main() -> int:
    suite = unittest.defaultTestLoader.discover(start_dir=_TESTS, top_level_dir=_SKILL_ROOT)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return 0 if result.wasSuccessful() else 1

if __name__ == '__main__':
    sys.exit(main())
