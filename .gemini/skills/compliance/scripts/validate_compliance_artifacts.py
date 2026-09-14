#!/usr/bin/env python3
"""CLI entrypoint and compatibility wrapper for Compliance Package Validation & Drift Audit.

Core implementation resides in :mod:`compliance_engine.validate_compliance_artifacts`.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_SRC = os.path.abspath(os.path.join(_HERE, '..', 'src'))
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

_is_main = (__name__ == '__main__')
from compliance_engine import validate_compliance_artifacts as _target

for _k in dir(_target):
    if not _k.startswith('__'):
        globals()[_k] = getattr(_target, _k)
sys.modules[__name__] = _target

if _is_main:
    _target.main()
