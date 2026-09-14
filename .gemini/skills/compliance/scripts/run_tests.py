#!/usr/bin/env python3
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
