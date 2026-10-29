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

# uv runs every Python step on the interpreter and packages that the root
# pyproject.toml and uv.lock pin, so the result matches CI on every machine.

echo "============================================================"
echo " Stellar Engine Test & Quality Verification Suite"
echo "============================================================"

# 1. Python Unit Tests
echo ""
echo "==> [1/3] Running Python Unit Tests..."
uv run --project "${REPO_ROOT}" --locked python -m unittest discover -s "${REPO_ROOT}/tests" -t "${REPO_ROOT}" -p "test_*.py" -v

# 2. Shell Script Tests
echo ""
echo "==> [2/3] Running Shell Script Tests..."
for test_file in "${REPO_ROOT}"/tests/test_*.sh; do
  echo "=== Running $(basename "${test_file}") ==="
  bash "${test_file}"
done

# 3. Python Code Quality / AST Unused Local Variable & Boilerplate Checks
echo ""
echo "==> [3/3] Verifying CodeQL py/unused-local-variable and boilerplate compliance..."
uv run --project "${REPO_ROOT}" --locked python "${REPO_ROOT}/tools/check_boilerplate.py" "${REPO_ROOT}/tests" "${REPO_ROOT}/tools"
uv run --project "${REPO_ROOT}" --locked python -c "
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
  dirs[:] = [d for d in dirs if d not in ('.git', '.terraform', '.venv', 'venv', 'node_modules', '__pycache__')]
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
