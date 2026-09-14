#!/usr/bin/env python3
"""Backward-compatible test runner shim delegating to run_tests.py."""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import run_tests

if __name__ == '__main__':
    sys.exit(run_tests.main())
