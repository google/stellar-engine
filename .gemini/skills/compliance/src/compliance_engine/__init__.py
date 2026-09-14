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

from .audit_log import (
    AuditEvent,
    AuditLogger,
    AuditOutcome,
    audit_operation,
    configure_audit_log,
    get_audit_logger,
    reset_audit_log,
)
from .file_helpers import (
    MAX_TEXT_FILE_BYTES,
    MAX_YAML_ALIASES,
    MAX_YAML_BYTES,
    clean_cell_value,
    ensure_directory,
    ensure_path_within_boundary,
    escape_xml_text,
    get_scripts_dir,
    get_skill_root,
    get_src_dir,
    get_templates_dir,
    parse_yaml_robust_file,
    parse_yaml_safe,
    read_json_file,
    read_text_file,
    read_yaml_file,
    resolve_path,
    sanitize_container_image_tag,
    sanitize_filename,
    sanitize_software_package_identity,
    scrub_sensitive_data,
    validate_compliance_config_schema,
    validate_system_inventory_schema,
    write_json_file,
    write_text_file,
)
from .oscal_generator import (
    DEFAULT_OSCAL_VERSION,
    SUPPORTED_OSCAL_VERSIONS,
    export_oscal_artifacts,
    generate_oscal_component_definition,
    generate_oscal_ssp,
)
from . import safe_xml
from . import hcl_parser
from . import docx_generator
from . import excel_hydrator
from . import export_strategies
from . import poam_rules
from . import runbook_hydration
from . import security_scanner_bridge
from . import service_catalog
from . import stig_resolver
from . import template_engine
from . import utils
from . import extract_system_data
from . import generate_compliance_artifacts
from . import validate_compliance_artifacts
from . import semantic_linter
from .semantic_linter import (
    AISemanticValidationReport,
    ArtifactSemanticResult,
    DeterministicAssessorProvider,
    LLMProvider,
    PUBLIC_SECTOR_SECURITY_ENGINEER_PROMPT,
    SemanticFinding,
    SemanticLinterReport,
    enrich_narrative_with_ai,
    evaluate_architectural_drift,
    evaluate_control_substance,
    get_llm_provider,
    run_mandatory_ai_validation,
    run_semantic_linter,
    validate_poam_semantics,
    validate_policy_semantics,
    validate_ssp_semantics,
)

__version__ = "1.1.0"

__all__ = [
    # Version
    "__version__",
    # Audit logging (NIST SP 800-53 AU family)
    "AuditEvent",
    "AuditLogger",
    "AuditOutcome",
    "audit_operation",
    "configure_audit_log",
    "get_audit_logger",
    "reset_audit_log",
    # Resource budgets
    "MAX_TEXT_FILE_BYTES",
    "MAX_YAML_ALIASES",
    "MAX_YAML_BYTES",
    # Shared I/O, path confinement, and sanitization primitives
    "clean_cell_value",
    "ensure_directory",
    "ensure_path_within_boundary",
    "escape_xml_text",
    "get_scripts_dir",
    "get_skill_root",
    "get_src_dir",
    "get_templates_dir",
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
    # NIST OSCAL emission
    "DEFAULT_OSCAL_VERSION",
    "SUPPORTED_OSCAL_VERSIONS",
    "export_oscal_artifacts",
    "generate_oscal_component_definition",
    "generate_oscal_ssp",
    # Submodules
    "safe_xml",
    "hcl_parser",
    "docx_generator",
    "excel_hydrator",
    "export_strategies",
    "poam_rules",
    "runbook_hydration",
    "security_scanner_bridge",
    "service_catalog",
    "stig_resolver",
    "template_engine",
    "utils",
    "extract_system_data",
    "generate_compliance_artifacts",
    "validate_compliance_artifacts",
    "semantic_linter",
    # Semantic evaluation & drift analysis
    "SemanticLinterReport",
    "AISemanticValidationReport",
    "ArtifactSemanticResult",
    "DeterministicAssessorProvider",
    "LLMProvider",
    "PUBLIC_SECTOR_SECURITY_ENGINEER_PROMPT",
    "SemanticFinding",
    "enrich_narrative_with_ai",
    "evaluate_architectural_drift",
    "evaluate_control_substance",
    "get_llm_provider",
    "run_semantic_linter",
    "run_mandatory_ai_validation",
    "validate_poam_semantics",
    "validate_policy_semantics",
    "validate_ssp_semantics",
]
