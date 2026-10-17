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

"""Public Sector & Regulated Cloud Compliance Engine package.

Generates NIST SP 800-53 Rev. 5 / FedRAMP / DoD RMF authorization artifacts (SSP,
SCTM, POA&M, PPSM, OSCAL, policy manuals, and incident response runbooks) from live
infrastructure-as-code and cloud environments.

This package exposes the stable, modular surface of the engine:

* Technical Discovery & Extraction: :mod:`compliance_engine.extract_system_data`
* Dual-Format Hydration & Generation: :mod:`compliance_engine.generate_compliance_artifacts`
* Pre-Flight Validation & STIG Audit: :mod:`compliance_engine.validate_compliance_artifacts`
* Shared I/O and sanitization primitives: :mod:`compliance_engine.file_helpers`
* Hardened deserialization facades: :mod:`compliance_engine.safe_xml` (XML) and
  :mod:`compliance_engine.hcl_parser` (HCL2)
* Tamper-evident structured audit logging: :mod:`compliance_engine.audit_log` (NIST AU-2/AU-3/AU-9)
* NIST OSCAL 1.2.3 / 1.1.0 emission: :mod:`compliance_engine.oscal_generator`
* OpenXML DOCX generation: :mod:`compliance_engine.docx_generator`
* Macro-enabled Excel hydration: :mod:`compliance_engine.excel_hydrator`
* DISA STIG / SRG version resolution: :mod:`compliance_engine.stig_resolver`
* Security scanner orchestration & SARIF bridge: :mod:`compliance_engine.security_scanner_bridge`
"""

from __future__ import annotations

import importlib
from typing import Any, Dict

__version__ = "1.1.0"

# Submodules are imported on first attribute access (PEP 562) so that importing the
# package stays cheap and never registers bare module names in sys.modules.
_SUBMODULES = (
    "audit_log",
    "baseline_registry",
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
)

# Re-exported names mapped to the submodule that defines them.
_EXPORTS: Dict[str, str] = {
    **dict.fromkeys(
        (
            "AuditEvent",
            "AuditLogger",
            "AuditOutcome",
            "audit_operation",
            "configure_audit_log",
            "get_audit_logger",
            "reset_audit_log",
        ),
        "audit_log",
    ),
    **dict.fromkeys(
        (
            "IGNORED_TRAVERSAL_DIRS",
            "MAX_TEXT_FILE_BYTES",
            "MAX_YAML_ALIASES",
            "MAX_YAML_BYTES",
            "clean_cell_value",
            "ensure_directory",
            "ensure_path_within_boundary",
            "escape_xml_text",
            "get_scripts_dir",
            "get_skill_root",
            "get_templates_dir",
            "is_ignored_traversal_dir",
            "parse_yaml_robust_file",
            "parse_yaml_safe",
            "read_json_file",
            "read_text_file",
            "read_yaml_file",
            "resolve_path",
            "sanitize_container_image_tag",
            "sanitize_filename",
            "sanitize_software_package_identity",
            "scrub_sensitive_data",
            "validate_compliance_config_schema",
            "validate_system_inventory_schema",
            "write_json_file",
            "write_text_file",
        ),
        "file_helpers",
    ),
    **dict.fromkeys(
        (
            "DEFAULT_OSCAL_VERSION",
            "SUPPORTED_OSCAL_VERSIONS",
            "export_oscal_artifacts",
            "generate_oscal_component_definition",
            "generate_oscal_ssp",
        ),
        "oscal_generator",
    ),
    **dict.fromkeys(
        (
            "ArtifactSemanticResult",
            "SemanticFinding",
            "SemanticLinterReport",
            "evaluate_architectural_drift",
            "evaluate_control_substance",
            "run_semantic_linter",
            "validate_poam_semantics",
            "validate_policy_semantics",
            "validate_ssp_semantics",
        ),
        "semantic_linter",
    ),
}

__all__ = ["__version__", *_SUBMODULES, *_EXPORTS]


def __getattr__(name: str) -> Any:
    if name in _SUBMODULES:
        return importlib.import_module(f"{__name__}.{name}")
    module_name = _EXPORTS.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    value = getattr(importlib.import_module(f"{__name__}.{module_name}"), name)
    globals()[name] = value
    return value


def __dir__() -> list:
    return sorted(set(globals()) | set(__all__))
