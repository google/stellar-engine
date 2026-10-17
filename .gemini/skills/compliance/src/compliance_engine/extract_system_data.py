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

"""
System Infrastructure & Configuration Extractor

This script scans:
1. `compliance_config.yaml` / `variables.yaml` for user metadata, personnel roles, and version configs.
2. `.tf` and `.yaml` files across the codebase to discover:
   - All enabled GCP API Services (*.googleapis.com)
   - VPC Networks, Subnets, Firewall Rules
   - GKE Clusters, Cloud SQL Databases, BigQuery Datasets
   - Cloud KMS Key Rings and Crypto Keys
   - Compute Engine VMs, Bastion Hosts, Palo Alto NGFW Modules
   - Cloud Storage Buckets, Service Accounts, Logging Sinks
   - Assured Workloads compliance baselines
   - TDD-style IAM Groups, Personas, Roles, and Terraform IAM Bindings
   - ANY generic Terraform resource defined across the workspace
Outputs: `system_inventory.json`
"""

import argparse
import logging
import os
from pathlib import Path
import sys
from typing import Any, Dict, Optional, Sequence, Union

# Terraform HCL is parsed exclusively through the in-repo hardened facade, which
# is bound to the local name ``hcl2`` so that every existing call site
# (``hcl2.loads(...)``) keeps working unchanged.
from . import hcl_parser as hcl2
from ._app_sbom_scanner import (
    deep_scan_app_files,
    discover_or_generate_sbom,
    ingest_sbom_json,
    merge_app_data,
)
from ._config_doc_discovery import (
    LEGACY_CONFIG_KEY_ALIASES,
    _ALIASED_CONFIG_SECTIONS,
    _assemble_system_inventory_dict,
    _infer_regime_from_target_path,
    apply_legacy_config_aliases,
    deep_merge_dict,
    discover_system_documentation,
    extract_system_description_from_markdown,
    find_candidate_doc_files,
    infer_cloud_provider,
    infer_primary_location,
    infer_security_categorization,
    infer_system_name_and_abbr,
    load_all_system_configs,
    resolve_secops_and_external_systems,
)
from ._tf_hcl_helpers import (
    GENERIC_VAR_NAMES,
    HclBlock,
    LarkError,
    MAX_SUBPROCESS_OUTPUT_BYTES,
    SUBPROCESS_RETRY_BASE_SECONDS,
    _BARE_REF_PREFIX,
    _EXACT_VAR_REF,
    _PORTLESS_FIREWALL_PROTOCOLS,
    _REF_TAIL,
    _asset_identifier,
    _dict_to_hcl_body_str,
    _extract_balanced_hcl_blocks,
    _extract_hcl_local_assignments,
    _extract_nested_block_str,
    _extract_top_level_meta_arg,
    _find_trusted_binary,
    _hcl_val_to_str,
    _is_falsy_hcl_val,
    _literal_cidrs,
    _parse_hcl_list_items,
    _resolve_ast_variables,
    _resolve_optional_attr,
    _resolved_asset_name,
    _resolved_cmek_name,
    _sanitized_path_env,
    _text_attr_tristate,
    classify_resource_category,
    clean_interpolated_string,
    extract_hcl_attr,
    is_valid_cidr,
    is_valid_resource_name,
    parse_tfvars_content,
    resolve_iam_principal,
    safe_run_command,
)
from ._tf_resource_ingestor import (
    TERRAFORM_PLAN_FLAGS,
    _EXTERNAL_TOOL_ERRORS,
    _TERRAFORM_CREDENTIAL_ENV_PREFIXES,
    _TERRAFORM_CREDENTIAL_ENV_VARS,
    _evaluate_child_resource_condition,
    _has_target_terraform_plugins,
    _redact_tf_sensitive_values,
    _terraform_env,
    _terraform_show_json,
    classify_and_ingest_resource,
    deep_scan_tf_files,
    derive_authentication_summary,
    derive_connectivity_summary,
    derive_encryption_summary,
    derive_iam_roles_matrix,
    discover_or_generate_terraform_json,
    extract_resources_from_tf_json,
    finalize_terraform_data,
    infer_enabled_services_from_components,
    ingest_terraform_json,
    init_empty_tf_data,
)
from .audit_log import AuditEvent, audit_operation
from .file_helpers import (
    get_skill_root,
    parse_yaml_safe,
    read_text_file,
    require_supported_regime,
    resolve_cli_target,
    resolve_module_root,
    resolve_path,
    scrub_sensitive_data,
    validate_system_inventory_schema,
    write_json_file,
    write_text_file,
)

logger = logging.getLogger("extract_system_data")

SKILL_BASE = str(get_skill_root())


def _backup_existing_inventory(out_path: str, target_dir: Union[str, Path]) -> None:
    """Preserves the previous ``system_inventory.json`` as ``system_inventory.json.bak``."""
    if os.path.islink(out_path):
        raise PermissionError(
            f"Refusing to regenerate '{out_path}': it is a symbolic link. Replace it with "
            "a regular file (or delete it) and rerun the extractor."
        )
    if not os.path.isfile(out_path):
        return

    backup_path = f"{out_path}.bak"
    try:
        previous = read_text_file(out_path, errors="strict", allowed_boundary=target_dir)
        if os.path.islink(backup_path):
            logger.warning(
                "Replacing the symbolic link at '%s' with a regular backup file; the link "
                "was not followed.",
                backup_path,
            )
            os.unlink(backup_path)
        write_text_file(backup_path, previous, allowed_boundary=target_dir)
        logger.info("Existing inventory preserved as '%s' before regeneration.", backup_path)
    except (OSError, ValueError) as err:
        logger.warning(
            "Could not back up the existing inventory '%s': %s. Continuing would "
            "discard any manual corrections, so the extraction is aborted.",
            out_path,
            err,
        )
        raise


def _validate_boundary_inputs_not_empty(
    target_path: Path,
    tf_json: Optional[Dict[str, Any]],
    tf_scanned: Dict[str, Any],
    app_scanned: Dict[str, Any],
) -> None:
    """Fails closed when a target folder has no readable Terraform or application inputs."""
    tf_files = list(tf_scanned.get("terraform_files_scanned") or [])
    has_app_inputs = any(app_scanned.get(k) for k in ("applications", "software_packages", "container_images"))
    if not tf_json and not tf_files and not has_app_inputs:
        raise ValueError(f"No Terraform (.tf), plan/state JSON or application inputs found in {target_path}")
    unparsed = [e for e in tf_scanned.get("unparsed_terraform_files", []) if isinstance(e, dict)]
    failed_paths = {e.get("path") for e in unparsed} | set(tf_scanned.get("terraform_ast_failures") or [])
    if not tf_json and tf_files and set(tf_files) <= failed_paths and not tf_scanned.get("all_resources"):
        detail = f" (first: {unparsed[0].get('path')}: {unparsed[0].get('error')})" if unparsed else ""
        raise ValueError(
            f"None of the {len(tf_files)} Terraform file(s) under {target_path} could be read or parsed{detail}"
        )


def _check_supported_regime_gate(target_path: Path, sys_info: Dict[str, Any]) -> None:
    """Enforces require_supported_regime when regime keys are set in config or inferred."""
    explicit_regime_in_cfg = False
    auth_cfg_file = target_path / "compliance_config.yaml"
    if auth_cfg_file.is_file() and not auth_cfg_file.is_symlink():
        try:
            raw_cfg = parse_yaml_safe(
                read_text_file(auth_cfg_file, allowed_boundary=target_path),
                source_name=str(auth_cfg_file),
            )
            raw_sys = (raw_cfg or {}).get("system_information")
            if isinstance(raw_sys, dict) and any(
                k in raw_sys for k in ("impact_level", "compliance_baseline", "governance_regime")
            ):
                explicit_regime_in_cfg = True
        except (OSError, ValueError):
            pass
    if explicit_regime_in_cfg or any(
        k in sys_info for k in ("impact_level", "compliance_baseline", "governance_regime")
    ):
        require_supported_regime(sys_info)


def extract_system_inventory(
    target_dir: Union[str, Path],
    allow_terraform_plan: bool = False,
    allow_scanners: bool = False,
    module_root: Optional[Union[str, Path]] = None,
) -> Dict[str, Any]:
    """Extracts system inventory data from configs, Terraform, and applications.

    Orchestrates configuration aggregation, infrastructure scanning, application
    scanning, and metadata inference, saving the result as system_inventory.json.
    """
    raw_target = Path(target_dir)
    if raw_target.is_symlink():
        logger.warning(
            "Target directory '%s' is a symbolic link resolving to '%s'; writing inventory into '%s'.",
            raw_target,
            raw_target.resolve(),
            raw_target.resolve(),
        )
    target_path = resolve_path(target_dir)
    if not target_path.exists():
        raise FileNotFoundError(f"Target directory does not exist: {target_path}")
    if not target_path.is_dir():
        raise NotADirectoryError(f"Target path is not a directory: {target_path}")
    resolve_module_root(target_path, module_root)
    user_config = load_all_system_configs(str(target_path))

    sys_info = dict(user_config.get("system_information", {}) or {})
    path_impact, path_baseline = _infer_regime_from_target_path(target_dir, target_path)
    if not sys_info.get("impact_level") and path_impact:
        sys_info["impact_level"] = path_impact
    if not sys_info.get("compliance_baseline") and path_baseline:
        sys_info["compliance_baseline"] = path_baseline
    _check_supported_regime_gate(target_path, sys_info)
    user_config["system_information"] = sys_info

    tf_json = discover_or_generate_terraform_json(
        target_dir, user_config=user_config, allow_terraform_plan=allow_terraform_plan
    )
    if tf_json:
        logger.info("Ingesting resolved infrastructure architecture from Terraform JSON plan/state.")
        tf_scanned = ingest_terraform_json(tf_json, user_config=user_config, target_dir=target_dir)
    else:
        logger.info("No Terraform plan/state JSON detected or generated; scanning HCL blueprint files.")
        tf_scanned = deep_scan_tf_files(
            str(target_path), user_config=user_config, module_root=str(module_root) if module_root else None
        )

    sbom_json = discover_or_generate_sbom(target_dir, user_config=user_config, allow_scanners=allow_scanners)
    app_scanned = deep_scan_app_files(str(target_path))
    if sbom_json:
        logger.info("Ingesting software package catalog from SBOM (CycloneDX/SPDX/Syft).")
        app_scanned = merge_app_data(app_scanned, ingest_sbom_json(sbom_json))

    _validate_boundary_inputs_not_empty(target_path, tf_json, tf_scanned, app_scanned)

    readme_data = discover_system_documentation(target_dir)
    if readme_data and readme_data.get("source_path"):
        logger.info(
            "Discovered authentic system description from '%s' (Title: %s)",
            readme_data.get("source_path"),
            readme_data.get("title", "Untitled"),
        )

    inferred_sys_name, inferred_sys_abbr = infer_system_name_and_abbr(
        str(target_dir), tf_scanned, app_scanned, sys_info, readme_data=readme_data
    )
    inferred_loc = infer_primary_location(tf_scanned, app_scanned, sys_info)
    inferred_cloud = infer_cloud_provider(tf_scanned, sys_info)
    inf_c, inf_i, inf_a = infer_security_categorization(tf_scanned, app_scanned, sys_info)
    res_secops, res_ext = resolve_secops_and_external_systems(user_config, tf_scanned, target_dir)

    inventory = _assemble_system_inventory_dict(
        user_config=user_config,
        tf_scanned=tf_scanned,
        app_scanned=app_scanned,
        readme_data=readme_data,
        inferred_meta=(inferred_sys_name, inferred_sys_abbr, inferred_loc, inferred_cloud, inf_c, inf_i, inf_a),
        res_secops=res_secops,
        res_ext=res_ext,
    )

    scrubbed_inventory = scrub_sensitive_data(inventory)
    raw_secrets = inventory.get("infrastructure_components", {}).get("secrets")
    if isinstance(raw_secrets, list) and isinstance(scrubbed_inventory.get("infrastructure_components"), dict):
        scrubbed_inventory["infrastructure_components"]["secrets"] = [
            scrub_sensitive_data(s) for s in raw_secrets
        ]
    out_path = os.path.join(str(target_path), "system_inventory.json")
    validate_system_inventory_schema(scrubbed_inventory, source_path=out_path)
    _backup_existing_inventory(out_path, str(target_path))

    with audit_operation(event_type=AuditEvent.INVENTORY_EXTRACTED, obj=out_path):
        write_json_file(out_path, scrubbed_inventory, indent=2, allowed_boundary=str(target_path))

    logger.info(
        "Extracted system inventory with %d GCP APIs & %d applications to '%s'",
        len(tf_scanned["services"]),
        len(app_scanned["applications"]),
        out_path,
    )
    return scrubbed_inventory


def main(argv: Optional[Sequence[str]] = None) -> None:
    """CLI entrypoint for extracting system inventory data."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    parser = argparse.ArgumentParser(
        prog="extract_system_data.py",
        description="Extracts infrastructure AST facts and software inventory from Terraform code into system_inventory.json.",
    )
    parser.add_argument("target_dir", help="Target blueprint folder (required; not a repository root or symlink)")
    parser.add_argument(
        "--allow-terraform-plan",
        action="store_true",
        help=(
            "Permit running 'terraform show -json' or 'terraform plan' when an initialized "
            "workspace or binary plan is found. WARNING: Only use on trusted workspaces; "
            "never use on untrusted content."
        ),
    )
    parser.add_argument(
        "--allow-scanners",
        action="store_true",
        help="Permit running Syft or Trivy to dynamically generate an SBOM.",
    )
    parser.add_argument(
        "--module-root",
        default=None,
        help="Read boundary for local child modules (an ancestor of the target). Default: the enclosing git work tree.",
    )
    parsed = parser.parse_args(sys.argv[1:] if argv is None else list(argv))
    try:
        target = resolve_cli_target(parsed.target_dir)
        extract_system_inventory(
            target,
            allow_terraform_plan=parsed.allow_terraform_plan,
            allow_scanners=parsed.allow_scanners,
            module_root=parsed.module_root,
        )
    except (FileNotFoundError, NotADirectoryError, ValueError, PermissionError) as err:
        print(f"[ERROR] {err}", file=sys.stderr)
        sys.exit(1)


__all__ = [
    "GENERIC_VAR_NAMES",
    "HclBlock",
    "LEGACY_CONFIG_KEY_ALIASES",
    "LarkError",
    "MAX_SUBPROCESS_OUTPUT_BYTES",
    "SKILL_BASE",
    "SUBPROCESS_RETRY_BASE_SECONDS",
    "TERRAFORM_PLAN_FLAGS",
    "_ALIASED_CONFIG_SECTIONS",
    "_BARE_REF_PREFIX",
    "_EXACT_VAR_REF",
    "_EXTERNAL_TOOL_ERRORS",
    "_PORTLESS_FIREWALL_PROTOCOLS",
    "_REF_TAIL",
    "_TERRAFORM_CREDENTIAL_ENV_PREFIXES",
    "_TERRAFORM_CREDENTIAL_ENV_VARS",
    "_asset_identifier",
    "_backup_existing_inventory",
    "_dict_to_hcl_body_str",
    "_evaluate_child_resource_condition",
    "_extract_balanced_hcl_blocks",
    "_extract_hcl_local_assignments",
    "_extract_nested_block_str",
    "_extract_top_level_meta_arg",
    "_find_trusted_binary",
    "_has_target_terraform_plugins",
    "_hcl_val_to_str",
    "_infer_regime_from_target_path",
    "_is_falsy_hcl_val",
    "_literal_cidrs",
    "_parse_hcl_list_items",
    "_redact_tf_sensitive_values",
    "_resolve_ast_variables",
    "_resolve_optional_attr",
    "_resolved_asset_name",
    "_resolved_cmek_name",
    "_sanitized_path_env",
    "_terraform_env",
    "_terraform_show_json",
    "_text_attr_tristate",
    "apply_legacy_config_aliases",
    "classify_and_ingest_resource",
    "classify_resource_category",
    "clean_interpolated_string",
    "deep_merge_dict",
    "deep_scan_app_files",
    "deep_scan_tf_files",
    "derive_authentication_summary",
    "derive_connectivity_summary",
    "derive_encryption_summary",
    "derive_iam_roles_matrix",
    "discover_or_generate_sbom",
    "discover_or_generate_terraform_json",
    "discover_system_documentation",
    "extract_hcl_attr",
    "extract_resources_from_tf_json",
    "extract_system_description_from_markdown",
    "extract_system_inventory",
    "finalize_terraform_data",
    "find_candidate_doc_files",
    "hcl2",
    "infer_cloud_provider",
    "infer_enabled_services_from_components",
    "infer_primary_location",
    "infer_security_categorization",
    "infer_system_name_and_abbr",
    "ingest_sbom_json",
    "ingest_terraform_json",
    "init_empty_tf_data",
    "is_valid_cidr",
    "is_valid_resource_name",
    "load_all_system_configs",
    "main",
    "merge_app_data",
    "parse_tfvars_content",
    "resolve_iam_principal",
    "resolve_secops_and_external_systems",
    "safe_run_command",
]


if __name__ == "__main__":
    main()
