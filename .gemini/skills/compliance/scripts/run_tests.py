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
import argparse
import os
import sys
from typing import List, Optional
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
_SKILL_ROOT = os.path.abspath(os.path.join(_HERE, '..'))
_SRC = os.path.join(_SKILL_ROOT, 'src')
_TESTS = os.path.join(_SKILL_ROOT, 'tests')

for _p in (_SKILL_ROOT, _SRC, _HERE, _TESTS):
    if _p not in sys.path:
        sys.path.insert(0, _p)


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    """Parses command-line arguments for the test runner."""
    parser = argparse.ArgumentParser(
        description="Run compliance engine automated tests with optional test selection.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_const",
        dest="verbosity",
        const=2,
        default=2,
        help="Run tests with verbose output.",
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_const",
        dest="verbosity",
        const=1,
        help="Run tests with minimal output.",
    )
    parser.add_argument(
        "-f", "--failfast",
        action="store_true",
        help="Stop the test run on the first error or failure.",
    )
    parser.add_argument(
        "-k",
        dest="pattern",
        default=None,
        help="Only run tests whose name matches pattern (pattern substring match).",
    )
    parser.add_argument(
        "tests",
        nargs="*",
        help="Optional test module, class, or method selectors (e.g. tests.test_compliance_engine).",
    )
    return parser.parse_args(argv)


def _filter_suite_by_pattern(suite: unittest.TestSuite, pattern: str) -> unittest.TestSuite:
    """Filters tests in suite by pattern match against test id."""
    filtered = unittest.TestSuite()
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            sub = _filter_suite_by_pattern(item, pattern)
            if sub.countTestCases() > 0:
                filtered.addTest(sub)
        elif pattern.lower() in item.id().lower():
            filtered.addTest(item)
    return filtered


def main(argv: Optional[List[str]] = None) -> int:
    """Executes the test suite according to CLI arguments."""
    args = parse_args(argv)

    loader = unittest.defaultTestLoader
    if args.tests:
        suite = unittest.TestSuite()
        for name in args.tests:
            if os.path.isfile(name) or name.endswith('.py'):
                norm_path = os.path.abspath(name)
                start_dir = os.path.dirname(norm_path)
                pattern = os.path.basename(norm_path)
                sub_suite = loader.discover(start_dir=start_dir, pattern=pattern, top_level_dir=_SKILL_ROOT)
                suite.addTest(sub_suite)
            else:
                try:
                    suite.addTest(loader.loadTestsFromName(name))
                except (ImportError, AttributeError):
                    if not name.startswith("tests."):
                        try:
                            suite.addTest(loader.loadTestsFromName(f"tests.{name}"))
                        except (ImportError, AttributeError):
                            suite.addTest(loader.discover(start_dir=_TESTS, pattern=f"*{name}*", top_level_dir=_SKILL_ROOT))
                    else:
                        raise
    else:
        suite = loader.discover(start_dir=_TESTS, top_level_dir=_SKILL_ROOT)

    if args.pattern:
        suite = _filter_suite_by_pattern(suite, args.pattern)

    runner = unittest.TextTestRunner(verbosity=args.verbosity, failfast=args.failfast)
    result = runner.run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(main())
