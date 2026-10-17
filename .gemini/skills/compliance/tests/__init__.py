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

"""Scoped test suite for Public Sector & Regulated Cloud Compliance Engine."""
import os
import sys

_TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
_SKILL_ROOT = os.path.abspath(os.path.join(_TESTS_DIR, ".."))
_SRC_DIR = os.path.join(_SKILL_ROOT, "src")
_SCRIPTS_DIR = os.path.join(_SKILL_ROOT, "scripts")

for _p in (_SRC_DIR, _SCRIPTS_DIR, _TESTS_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import importlib  # noqa: E402

_modules_to_alias = [
    "audit_log",
    "docx_generator",
    "excel_hydrator",
    "export_strategies",
    "extract_system_data",
    "file_helpers",
    "generate_compliance_artifacts",
    "hcl_parser",
    "oscal_generator",
    "poam_rules",
    "runbook_hydration",
    "safe_xml",
    "security_scanner_bridge",
    "semantic_linter",
    "service_catalog",
    "stig_resolver",
    "template_engine",
    "validate_compliance_artifacts",
]
# Older tests import engine modules by bare name; alias them to the package modules
# here (test-only) so a single module object is patched and asserted against.
for _mod_name in _modules_to_alias:
    sys.modules[_mod_name] = importlib.import_module(f"compliance_engine.{_mod_name}")
