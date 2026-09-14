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

import compliance_engine

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
    "service_catalog",
    "stig_resolver",
    "template_engine",
    "utils",
    "validate_compliance_artifacts",
]
for _mod_name in _modules_to_alias:
    if hasattr(compliance_engine, _mod_name):
        sys.modules[_mod_name] = getattr(compliance_engine, _mod_name)
