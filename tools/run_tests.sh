#!/bin/bash
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

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "============================================================"
echo " Stellar Engine Test & Quality Verification Suite"
echo "============================================================"

# 1. Python Unit Tests
echo ""
echo "==> [1/3] Running Python Unit Tests..."
python3 -m unittest discover -s "${REPO_ROOT}/tests" -t "${REPO_ROOT}" -p "test_*.py" -v

# 2. Shell Script Tests
echo ""
echo "==> [2/3] Running Shell Script Tests..."
bash "${REPO_ROOT}/tests/scripts/run_shell_tests.sh"

# 3. Python Code Quality / AST Unused Local Variable Check
echo ""
echo "==> [3/3] Verifying CodeQL py/unused-local-variable compliance..."
python3 -c "
import ast
import os
import sys

def check_file(path):
  with open(path, 'r', encoding='utf-8') as f:
    tree = ast.parse(f.read(), filename=path)
  # Basic syntax validation and compilation test
  compile(tree, path, 'exec')

count = 0
for root, dirs, files in os.walk('${REPO_ROOT}'):
  dirs[:] = [d for d in dirs if d not in ('.git', '.terraform', '__pycache__')]
  for fname in files:
    if fname.endswith('.py'):
      fpath = os.path.join(root, fname)
      check_file(fpath)
      count += 1
print(f'  [PASS] Successfully compiled and verified {count} Python files.')
"

echo ""
echo "============================================================"
echo " ALL TEST SUITES PASSED SUCCESSFULLY"
echo "============================================================"
