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
ATO package generator: hydrates templates and writes Markdown, Word, YAML, Excel, and OSCAL.

Deliverables written under <target>/ato_artifacts/:
1. System Security Plan (SSP) and Path to Authorization (PTA) (.md and/or .docx)
2. Incident response runbooks (.md and/or .docx)
3. 20 NIST SP 800-53 Rev. 5 policy manuals (.md and/or .docx)
4. Hardware and Software Inventory (.yaml and/or .xlsm)
5. Plan of Action and Milestones (POA&M) (.yaml and/or .xlsm)
6. Ports, Protocols, and Services Matrix (PPSM) (.yaml and/or .xlsm)
7. Security Control Traceability Matrix (SCTM) (.yaml and/or .xlsm)
8. FIPS 140-3 Cryptographic Module Matrix (.md, .docx, .yaml)
9. NIST OSCAL SSP and component definition (.json and/or .yaml)

Format Preferences & CLI Options:
- Policy Formats: "both" (default), "docx", "markdown"
- Structured Data Formats: "both" (default), "excel", "yaml"
- OSCAL Formats: "both" (default), "json", "yaml", "none"
"""

import argparse
import hashlib
import ipaddress
import json
import logging
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

from .baseline_registry import (
    REGIME_SPEC_BY_REGIME,
    build_regime_odp_tokens,
    build_regime_template_flags,
    filter_policy_appendix_rows,
    get_regime_baseline,
    get_regime_spec,
    render_ssp_for_regime,
)
from .export_strategies import ExporterRegistry
from .file_helpers import (
    current_utc_datetime,
    classify_regime,
    derive_fips_199_impacts,
    is_dod_regime,
    require_supported_regime,
    resolve_default_csp_pato_package_id,
    summarize_kms_protection,
    ensure_directory,
    ensure_path_within_boundary,
    extract_clean_subnets,
    get_scripts_dir,
    get_skill_root,
    get_templates_dir,
    read_json_file,
    read_text_file,
    resolve_cli_target,
    resolve_path,
    run_bounded_command,
    safe_yaml_scalar,
    sanitize_container_image_tag,
    sanitize_filename,
    scrub_sensitive_data,
    validate_system_inventory_schema,
)
from .hardware_records import (
    build_hwsw_inventory_records,
    build_ppsm_records,
)
from .poam_rules import active_poam_target, derive_poam_findings, is_public_ingress_allow_rule, poam_run
from .security_scanner_bridge import resolve_scanner_policy
from .extract_system_data import clean_interpolated_string
from . import excel_hydrator
from . import stig_resolver
from .audit_log import (
    AuditEvent,
    AuditOutcome,
    configure_audit_log,
    get_audit_logger,
)
from .template_engine import (
    TemplateEngine,
    _sanitize_markdown_inline_value,
    evaluate_template_conditionals as engine_evaluate_conditionals,
)
from .runbook_hydration import (
    PROVENANCE_TOKENS,
    build_operator_context,
    find_operator_tokens,
    hydrate_operator_placeholders,
    render_discovered_context_block,
    reset_hydration_warnings,
    resolve_organization_domain,
    resolve_prepared_by,
)

import yaml  # noqa: E402  (resolved after file_helpers bootstraps the dependency path)

logger = logging.getLogger(__name__)

SKILL_BASE = str(get_skill_root())
SCRIPTS_DIR = str(get_scripts_dir())
TEMPLATES_DIR = str(get_templates_dir())


def _as_dict(val: Any) -> Dict[str, Any]:
    """Safely coerces a value to a dictionary, returning {} for non-dicts."""
    return val if isinstance(val, dict) else {}


def load_system_inventory(target_dir: Union[str, Path]) -> Dict[str, Any]:
    """Loads system inventory metadata from the target directory.

    If system_inventory.json does not exist, triggers extraction via
    extract_system_data.py before loading. Validates schema before returning.

    Args:
        target_dir: Absolute or relative path to the target foundation directory.

    Returns:
        A dictionary containing parsed system inventory metadata.

    Raises:
        FileNotFoundError: If system_inventory.json cannot be found or generated.
        ValueError: If system_inventory.json is malformed or fails schema validation.
    """
    target_path = resolve_path(target_dir)
    inventory_path = target_path / "system_inventory.json"
    if not inventory_path.exists():
        extractor_script = Path(SCRIPTS_DIR) / "extract_system_data.py"
        extract_cmd = (
            [sys.executable, str(extractor_script), "--", str(target_path)]
            if extractor_script.is_file()
            else [sys.executable, "-m", "compliance_engine.extract_system_data", "--", str(target_path)]
        )
        env = os.environ.copy()
        for k in ["LD_PRELOAD", "PYTHONPATH", "LD_LIBRARY_PATH"]:
            env.pop(k, None)
        try:
            res = run_bounded_command(
                extract_cmd,
                timeout=300,
                env=env,
                max_output_bytes=1024 * 1024,
            )
        except subprocess.TimeoutExpired:
            logger.error("extract_system_data.py timed out after 300 seconds for '%s'", target_path)
            raise
        except (subprocess.SubprocessError, OSError) as err:
            logger.error("Failed to execute extract_system_data.py for '%s': %s", target_path, err)
            raise
        if res.returncode != 0:
            detail = (res.stderr.strip() or res.stdout.strip()).splitlines()[-1:] or [""]
            raise ValueError(f"extract_system_data.py exited with code {res.returncode} for '{target_path}': {detail[0]}")

    if inventory_path.exists():
        inventory = read_json_file(inventory_path, allowed_boundary=target_path)
        validate_system_inventory_schema(inventory, source_path=inventory_path)
        sys_info = _as_dict(inventory.get("system_information"))
        for path_key in ("architecture_doc_path", "existing_policies_dir"):
            for container in (inventory, sys_info):
                raw_cfg_path = container.get(path_key)
                if isinstance(raw_cfg_path, str) and raw_cfg_path.strip():
                    candidate = Path(raw_cfg_path.strip())
                    if not candidate.is_absolute():
                        candidate = target_path / candidate
                    ensure_path_within_boundary(
                        candidate, target_path, allow_symlinks=False
                    )
        return scrub_sensitive_data(inventory)
    raise FileNotFoundError(f"Could not load system inventory from {inventory_path}")


def format_service_accounts(sa_list: List[Dict[str, Any]]) -> str:
    """Formats a list of service accounts into a Markdown bulleted list.

    Args:
        sa_list: List of service account dictionaries.

    Returns:
        A Markdown-formatted string describing the service accounts.
    """
    if not sa_list:
        return "- [NOT DETERMINED FROM SOURCE]"
    lines: List[str] = []
    for sa in sa_list:
        lines.append(f"- **{sa.get('account_id', 'SA')}**: Defined in `{sa.get('file', 'Terraform')}`")
    return "\n".join(lines)


def format_storage_buckets(bucket_list: List[Dict[str, Any]]) -> str:
    """Formats a list of GCS storage buckets into a Markdown bulleted list.

    Args:
        bucket_list: List of storage bucket dictionaries.

    Returns:
        A Markdown-formatted string describing buckets and CMEK encryption status.
    """
    if not bucket_list:
        return "- [NOT DETERMINED FROM SOURCE]"
    lines: List[str] = []
    for b in bucket_list:
        # Tri-state, not a boolean with an optimistic default. An absent value means
        # the extractor could not determine the encryption posture from the IaC; it
        # must never be rendered as an assurance of CMEK coverage in the SSP, which
        # would contradict the SC-28 POA&M rule that treats unknown as a gap.
        cmek_state = b.get("cmek_encrypted")
        cmek_display = "Not determined from IaC" if cmek_state is None else cmek_state
        location = b.get("location") or "Not determined from IaC"
        lines.append(
            f"- **{b.get('name', 'Storage Bucket')}**: Location `{location}`, CMEK Encrypted: `{cmek_display}`"
        )
    return "\n".join(lines)


def format_firewall_matrix(fw_list: List[Dict[str, Any]]) -> str:
    """Formats firewall rule definitions into a Markdown table.

    Args:
        fw_list: List of firewall rule dictionaries.

    Returns:
        A Markdown table string displaying firewall rules and actions.
    """
    header = "| Rule Name | Direction | Protocol | Ports | Action |\n|---|---|---|---|---|"
    if not fw_list:
        return header + "\n| [NOT DETERMINED FROM SOURCE] | N/A | N/A | N/A | N/A |"
    rows: List[str] = []
    for fw in fw_list:
        rows.append(
            f"| {fw.get('name')} | {fw.get('direction')} | {fw.get('protocol')} | {fw.get('ports')} | {fw.get('action')} |"
        )
    return header + "\n" + "\n".join(rows)


_RFC1918_NETWORKS = (
    ipaddress.IPv4Network("10.0.0.0/8"),
    ipaddress.IPv4Network("172.16.0.0/12"),
    ipaddress.IPv4Network("192.168.0.0/16"),
)


def _classify_cidr(cidr: str) -> str:
    """Classifies a CIDR as RFC 1918 private space or not.

    Args:
        cidr: CIDR string taken from the inventory.

    Returns:
        "Private (RFC 1918)", "Not RFC 1918", or "Unparsed CIDR" when the value is
        not a valid IPv4 network.
    """
    try:
        network = ipaddress.ip_network(cidr, strict=False)
    except ValueError:
        return "Unparsed CIDR"
    if isinstance(network, ipaddress.IPv4Network) and any(network.subnet_of(block) for block in _RFC1918_NETWORKS):
        return "Private (RFC 1918)"
    return "Not RFC 1918"


def format_subnet_boundary_table(inventory: Dict[str, Any]) -> str:
    """Formats a Markdown table of discovered network subnets and CIDR blocks.

    The address classification is computed from each CIDR. Reachability is not
    asserted here; it depends on the firewall rules, which are listed separately.

    Args:
        inventory: System inventory dictionary.

    Returns:
        A Markdown table string documenting all discovered subnet CIDR ranges.
    """
    net_info = inventory.get("network_architecture", {})
    clean_subnets = extract_clean_subnets(net_info.get("subnets_cidrs"))
    vpcs = [clean_interpolated_string(v) for v in net_info.get("vpcs", []) if clean_interpolated_string(v)]
    vpc_desc = ", ".join(vpcs) if vpcs else "[NOT DETERMINED FROM SOURCE]"
    if not clean_subnets:
        return "[NOT DETERMINED FROM SOURCE] No subnet CIDR ranges were found in the Terraform for this boundary."
    lines = [
        "| Subnet CIDR Range | Address Classification | VPC Network | Ingress Controls |",
        "| :--- | :--- | :--- | :--- |",
    ]
    for cidr in clean_subnets:
        lines.append(
            f"| `{cidr}` | {_classify_cidr(cidr)} | `{vpc_desc}` | See the firewall rule matrix |"
        )
    return "\n".join(lines)


def format_container_workload_table(inventory: Dict[str, Any]) -> str:
    """Formats a Markdown table of discovered container images and runtime environments.

    Args:
        inventory: System inventory dictionary.

    Returns:
        A Markdown table string documenting all container workload images.
    """
    app_info = inventory.get("application_components", {})
    containers = app_info.get("container_images", [])
    if not containers:
        return "No container images were found in the source for this boundary."
    lines = [
        "| Container Image Reference | Tag | Base Image / OS | Workload Source File |",
        "| :--- | :--- | :--- | :--- |",
    ]
    seen = set()
    for c in containers:
        raw_img = str(c.get("image") or c.get("base_image") or "container-image")
        img_name, img_ver = sanitize_container_image_tag(
            clean_interpolated_string(raw_img, default_val="container-image"),
            default_img="container-image",
        )
        if img_name in seen:
            continue
        seen.add(img_name)
        source_file = c.get("file", "Dockerfile")
        base_os = c.get("base_os") or "[NOT DETERMINED FROM SOURCE]"
        lines.append(f"| `{img_name}` | `{img_ver}` | {base_os} | `{source_file}` |")
    return "\n".join(lines)


def format_list_items(item_list: List[str]) -> str:
    """Formats a list of strings into indented Markdown bullet points.

    Args:
        item_list: List of string item names.

    Returns:
        An indented Markdown formatted list string.
    """
    if not item_list:
        return "  - [NOT DETERMINED FROM SOURCE]"
    return "\n".join([f"  - {item}" for item in item_list])


def _normalize_sod_binding_principal(
    raw_p: str,
    r_val: str,
    f_src: str,
    service_accounts: List[Dict[str, Any]],
    proj_id: str,
    proj_num: str,
) -> Tuple[Optional[str], str]:
    """Resolves HCL interpolations on an IAM binding principal and role, or returns (None, '')."""
    if not raw_p or "${each.value.role}" in r_val or r_val.startswith("${each."):
        return None, ""

    if "${each.value.member}" in raw_p or raw_p == "${each.value}":
        if "cryptoKey" in r_val or "kms" in f_src:
            raw_p = "CMEK Key Encrypter/Decrypter Service Agents (Storage, BigQuery, Pub/Sub, Cloud SQL)"
        elif "serviceusage" in r_val or "impersonator" in f_src:
            raw_p = "Deployment & CI/CD Pipeline Impersonators"
        else:
            return None, ""
    elif "secretmanager_sa" in raw_p:
        raw_p = f"serviceAccount:service-{proj_num}@gcp-sa-secretmanager.iam.gserviceaccount.com (Secret Manager CMEK)"
    elif "google_service_account." in raw_p:
        sa_res_match = re.search(r"google_service_account\.([a-zA-Z0-9_-]+)\.email", raw_p)
        if sa_res_match:
            sa_name = sa_res_match.group(1)
            matched_sa = next((s for s in service_accounts if s.get("resource_name") == sa_name), None)
            sa_acc = matched_sa.get("account_id") if matched_sa else sa_name.replace("_", "-")
            raw_p = f"serviceAccount:{sa_acc}@{proj_id}.iam.gserviceaccount.com"
    elif "local.sa_email" in raw_p:
        file_sas = [s for s in service_accounts if s.get("file") == f_src]
        sa_acc = file_sas[0].get("account_id") if file_sas else "[CONFIG_REQUIRED: service_account]"
        raw_p = f"serviceAccount:{sa_acc}@{proj_id}.iam.gserviceaccount.com"
    elif "${var.project_number}" in raw_p or "$var.project_number" in raw_p:
        raw_p = raw_p.replace("${var.project_number}", proj_num).replace("$var.project_number", proj_num)
    elif "${" in raw_p:
        raw_p = re.sub(r"\$\{([^}]+)\}", r"\1", raw_p).replace("var.", "").replace("local.", "")

    if "${" in r_val:
        r_val = re.sub(r"\$\{([^}]+)\}", r"\1", r_val).replace("var.", "").replace("local.", "")

    if "${" in raw_p or "each.value" in raw_p:
        return None, ""
    return raw_p, r_val


def _append_sod_iam_matrix_and_bindings(
    lines: List[str],
    iam_matrix: List[Dict[str, Any]],
    iam_bindings: List[Dict[str, Any]],
    service_accounts: List[Dict[str, Any]],
    proj_id: str,
    proj_num: str,
    rendered_principals: Set[str],
) -> None:
    """Appends IAM roles matrix and Terraform IAM binding rows to the separation-of-duties table."""
    for item in iam_matrix:
        p = item.get("principal")
        if not p:
            continue
        clean_p = p.strip("`").strip()
        if clean_p in rendered_principals:
            continue
        rendered_principals.add(clean_p)
        r_list = item.get("roles", [])
        f_src = item.get("file", "Foundation Config")
        if clean_p.startswith(("serviceAccount:", "user:", "group:")) and not (" " in clean_p or "(" in clean_p):
            p_display = f"`{clean_p}`"
        else:
            p_display = clean_p
        roles_str = ", ".join(r_list) if r_list else "Project Scope Permissions"
        lines.append(f"| {p_display} | {roles_str} | `{f_src}` |")

    grouped_bindings: Dict[str, Dict[str, Any]] = {}
    for b in iam_bindings:
        raw_p = str(b.get("principal", "")).strip()
        r_val = str(b.get("role", "Custom Role")).replace("roles/", "").strip()
        f_src = b.get("file", "Terraform Code")
        norm_p, norm_r = _normalize_sod_binding_principal(raw_p, r_val, f_src, service_accounts, proj_id, proj_num)
        if not norm_p:
            continue
        if norm_p.startswith(("serviceAccount:", "user:", "group:")) or not (" " in norm_p or "(" in norm_p):
            p_display = f"`{norm_p}`"
        else:
            p_display = norm_p
        entry = grouped_bindings.setdefault(p_display, {"roles": [], "file": f_src})
        if norm_r and norm_r not in entry["roles"]:
            entry["roles"].append(norm_r)

    for p_display, p_meta in grouped_bindings.items():
        clean_p = p_display.strip("`").strip()
        if clean_p not in rendered_principals:
            rendered_principals.add(clean_p)
            roles_str = ", ".join(sorted(p_meta["roles"])) if p_meta["roles"] else "Scoped Permissions"
            lines.append(f"| {p_display} | {roles_str} | `{p_meta['file']}` |")


def _append_sod_sa_and_fallback_rows(
    lines: List[str],
    inventory: Dict[str, Any],
    sys_info: Dict[str, Any],
    service_accounts: List[Dict[str, Any]],
    rendered_principals: Set[str],
    csp_abbr: str,
    csp_lower: str,
) -> bool:
    """Appends service-account, configured IAM group, or assumed baseline group rows."""
    for sa in service_accounts:
        sa_id = sa.get("account_id", "service-account")
        sa_res = sa.get("resource_name", "")
        sa_file = sa.get("file", "Terraform")
        if any(sa_id in p or (sa_res and sa_res in p) for p in rendered_principals):
            continue
        if sa_id not in rendered_principals:
            rendered_principals.add(sa_id)
            lines.append(f"| `serviceAccount:{sa_id}` | Principle of Least Privilege (Scoped Workload Account) | `{sa_file}` |")

    iam_groups = inventory.get("iam_groups", {})
    if not rendered_principals and iam_groups:
        for grp_role, grp_list in iam_groups.items():
            if not isinstance(grp_list, list):
                continue
            for g in grp_list:
                if g and f"`{g}`" not in rendered_principals:
                    p_name = f"`{g}`"
                    rendered_principals.add(p_name)
                    role_desc = grp_role.replace("_", " ").title()
                    lines.append(
                        f"| {p_name} | {role_desc} (Configured in foundation_variables.yaml) "
                        "| `foundation_configs/shared/foundation_variables.yaml` |"
                    )

    if rendered_principals:
        return False
    if sys_info.get("system_name") and csp_lower == "gcp":
        src = f"Baseline {csp_abbr} Foundation default (assumed; not found in target Terraform)"
        default_groups = (
            ("organization-admins", "resourcemanager.organizationAdmin, orgpolicy.policyAdmin, billing.user, resourcemanager.folderAdmin"),
            ("security-admins", "assuredworkloads.admin, iam.securityAdmin, securitycenter.adminViewer, logging.privateLogViewer"),
            ("network-admins", "compute.networkAdmin, compute.securityAdmin, compute.sharedVpcAdmin"),
            ("billing-admins", "billing.admin, billing.creator"),
            ("logging-admins", "logging.admin, logging.configWriter"),
            ("logging-viewers", "logging.privateLogViewer"),
            ("monitoring-admins", "monitoring.admin"),
        )
        for group_suffix, group_roles in default_groups:
            lines.append(f"| `{csp_lower}-{group_suffix}` | {group_roles} | {src} |")
        return True
    lines.append("| `[NOT DETERMINED FROM SOURCE]` | [NOT DETERMINED] | [NOT DETERMINED] |")
    return False


def format_separation_of_duties_table(inventory: Dict[str, Any]) -> str:
    """Formats an IAM separation of duties table from inventory components."""
    sys_info = inventory.get("system_information", {})
    csp_abbr = sys_info.get("cloud_service_provider_abbr") or "GCP"
    csp_lower = csp_abbr.lower()
    infra_info = inventory.get("infrastructure_components", {})
    iam_matrix = infra_info.get("iam_roles_matrix", [])
    iam_bindings = infra_info.get("iam_bindings", [])
    service_accounts = infra_info.get("service_accounts", [])
    proj_id = sys_info.get("project_id") or inventory.get("project_id") or "[CONFIG_REQUIRED: project_id]"
    proj_num = str(sys_info.get("project_number") or inventory.get("project_number") or "<PROJECT_NUMBER>")

    lines: List[str] = [
        f"| Role Group / Principal | Assigned {csp_abbr} IAM Roles & Permissions | Source Configuration / Codebase File |",
        "| :--- | :--- | :--- |",
    ]
    rendered_principals: Set[str] = set()
    _append_sod_iam_matrix_and_bindings(
        lines, iam_matrix, iam_bindings, service_accounts, proj_id, proj_num, rendered_principals
    )
    assumed_defaults = _append_sod_sa_and_fallback_rows(
        lines, inventory, sys_info, service_accounts, rendered_principals, csp_abbr, csp_lower
    )

    lines.append("")
    lines.append("> [!NOTE]")
    lines.append(
        "> **Separation of Duties Source**: Rows are derived from the IAM role matrix, Terraform IAM "
        "bindings, service accounts, and configured IAM groups found for this boundary."
    )
    if assumed_defaults:
        lines.append(
            "> No IAM bindings were found in the target Terraform. The rows marked as assumed are the "
            "baseline foundation's default administrative groups; confirm each group and its roles "
            "before submission."
        )
    return "\n".join(lines)


def _build_mission_profile_paragraphs(
    sys_info: Dict[str, Any],
    app_info: Dict[str, Any],
    user_desc: str,
    sys_name: str,
    sys_abbr: str,
    baseline: str,
    impact_level: str,
) -> List[str]:
    """Builds Section 1 (Architectural Mission & Workload Profile) paragraphs."""
    operational_desc = (sys_info.get("readme_system_description") or user_desc).strip()
    if operational_desc:
        paras = [p.strip() for p in operational_desc.split("\n\n") if p.strip()]
        if baseline.lower() not in operational_desc.lower() and impact_level.lower() not in operational_desc.lower():
            if sys_name.lower() not in operational_desc.lower() and not sys_name.startswith("[CONFIG_REQUIRED"):
                paras.append(
                    f"Under the **{sys_name}** (**{sys_abbr}**) accreditation boundary, the system is architected, "
                    f"operated, and maintained to satisfy {baseline} security controls under a formal {impact_level} authorization boundary."
                )
            else:
                paras.append(
                    f"The system is architected, operated, and maintained to satisfy {baseline} "
                    f"security controls under a formal {impact_level} authorization boundary."
                )
        return paras

    apps = app_info.get("applications", [])
    frameworks = app_info.get("frameworks", [])
    runtimes = app_info.get("runtimes", [])
    arch_parts = []
    if apps:
        arch_parts.append(f"hosts application services ({', '.join(a.get('name') for a in apps[:4])})")
    if frameworks:
        arch_parts.append(f"built with {', '.join(frameworks)}")
    if runtimes:
        arch_parts.append(f"executing within {', '.join(runtimes)} runtimes")

    if arch_parts:
        return [(
            f"The **{sys_name}** (**{sys_abbr}**) is an enterprise cloud information system engineered to deliver mission-critical digital capabilities. "
            f"The workload environment {'; '.join(arch_parts)}. The system is architected, operated, and maintained to satisfy {baseline} "
            f"security controls under a formal {impact_level} authorization boundary."
        )]
    return [(
        f"The **{sys_name}** (**{sys_abbr}**) is an enterprise cloud foundation and workload hosting platform "
        f"engineered to provide hardened multi-tenant computing, "
        f"centralized security visibility, automated identity governance, and cryptographic protection in compliance with {baseline} ({impact_level})."
    )]


def _build_compute_and_data_paragraphs(infra_info: Dict[str, Any], inventory: Dict[str, Any]) -> List[str]:
    """Builds Section 2 (Compute Infrastructure) and Section 3 (Data Persistence) paragraphs."""
    paras: List[str] = []
    gke = infra_info.get("gke_clusters", [])
    vms = infra_info.get("compute_instances", [])
    compute_parts = []
    if gke:
        c_names = ", ".join(c.get("name", "Cluster") if isinstance(c, dict) else str(c) for c in gke)
        compute_parts.append(
            f"managed Google Kubernetes Engine (GKE) private clusters ({c_names}) leveraging "
            "Shielded Nodes, Container-Optimized OS, and Workload Identity Federation"
        )
    if vms:
        compute_parts.append(
            f"{len(vms)} hardened Compute Engine virtual machine instance(s) running verified "
            "operating system images with Shielded VM vTPM integrity monitoring"
        )
    if infra_info.get("cloud_run_services"):
        compute_parts.append("serverless Cloud Run microservices with restricted private ingress and binary authorization verification")
    if infra_info.get("cloud_functions"):
        compute_parts.append("event-driven Cloud Functions executing in private VPC perimeters")
    if compute_parts:
        paras.append(
            f"**Workload Execution and Compute Tier**: Workloads execute within {'; '.join(compute_parts)}. "
            "All infrastructure assets are provisioned through declarative Infrastructure-as-Code (Terraform) "
            "modules to ensure immutable, repeatable, and audit-verifiable configuration baselines."
        )

    databases = infra_info.get("databases", [])
    buckets = infra_info.get("storage_buckets", [])
    data_parts = []
    if databases:
        db_details = [f"{db.get('name', 'db')} ({db.get('type', db.get('database_version', 'Managed Database'))})" for db in databases]
        data_parts.append(f"managed data persistence stores ({', '.join(db_details)})")
    if buckets:
        ubla_on = sum(1 for b in buckets if b.get("uniform_bucket_level_access") is True)
        vers_on = sum(1 for b in buckets if b.get("versioning") is True)
        bucket_desc = f"{len(buckets)} Cloud Storage bucket(s)"
        qualifiers = []
        if ubla_on:
            qualifiers.append(f"{ubla_on} enforcing uniform bucket-level access control")
        if vers_on:
            qualifiers.append(f"{vers_on} with object versioning enabled")
        if qualifiers:
            bucket_desc += f" ({', '.join(qualifiers)})"
        data_parts.append(bucket_desc)

    kms_keys = infra_info.get("kms_keys", [])
    raw_enc_sum = str(inventory.get("encryption_summary") or "").strip()
    if raw_enc_sum and not raw_enc_sum.startswith(("[NOT DETERMINED", "[CONFIG_REQUIRED")):
        enc_desc = raw_enc_sum
    elif kms_keys:
        enc_desc = summarize_kms_protection(kms_keys)
    else:
        enc_desc = "Google-managed default encryption at rest (no Customer-Managed Encryption Keys [CMEK] discovered in Terraform)"
    if data_parts:
        paras.append(
            f"**Data Persistence and Cryptographic Protection**: Sensitive system data is housed in {'; and '.join(data_parts)}. "
            f"Data at rest is cryptographically protected via {enc_desc}. "
            "Transport encryption settings (TLS versions per interface) are [NOT DETERMINED FROM SOURCE]."
        )
    return paras


def _build_network_and_iam_paragraphs(
    net_info: Dict[str, Any],
    infra_info: Dict[str, Any],
    sys_info: Dict[str, Any],
    inventory: Dict[str, Any],
) -> List[str]:
    """Builds Section 4 (Logical Network Architecture) and Section 5 (Identity & Audit Governance) paragraphs."""
    vpcs = net_info.get("vpcs", [])
    clean_subnets = extract_clean_subnets(net_info.get("subnets_cidrs"))
    net_parts = []
    if vpcs:
        net_parts.append(f"isolated Virtual Private Clouds ({', '.join(vpcs)})")
    if clean_subnets:
        net_parts.append(f"non-overlapping subnets ({', '.join(clean_subnets)})")
    conn_sum = inventory.get("connectivity_summary") or "Private Service Connect, Cloud Interconnect, and Cloud NAT"
    ids_sol = inventory.get("ids_solution") or "Cloud Next-Generation Firewall and Cloud IDS"
    has_public_ingress = any(is_public_ingress_allow_rule(fw) for fw in net_info.get("firewall_rules", []))

    if net_parts:
        addr_clause = "using private RFC 1918 addressing" if clean_subnets else "with subnet CIDR allocations pending configuration"
        ingress_clause = (
            "with zero direct external Internet ingress"
            if not has_public_ingress
            else "with boundary firewall ingress rules documented in the Firewall Matrix"
        )
        net_boundary_sentence = f"The logical network boundary is enforced through {'; '.join(net_parts)} {addr_clause} {ingress_clause}."
    else:
        net_boundary_sentence = "The logical network boundary is pending VPC and subnet CIDR discovery in Terraform ([NOT DETERMINED FROM SOURCE])."

    net_para = (
        f"**Network Perimeter and Boundary Protection**: {net_boundary_sentence} "
        f"Network transit is controlled by {conn_sum}. Ingress, egress, and lateral traffic "
        f"are inspected and protected by stateful firewall rules and {ids_sol}."
    )

    auth_sum = inventory.get("authentication_summary", "Cloud Identity with phishing-resistant MFA and least-privilege IAM")
    sec_ops = _as_dict(inventory.get("security_operations")) or _as_dict(sys_info.get("security_operations"))
    has_log_sinks = bool(
        infra_info.get("logging_sinks") or sec_ops.get("secops_enabled") or sec_ops.get("external_siem_type")
    )
    audit_sentence = (
        "Security telemetry, administrator activity, and system modification events are streamed "
        "in real time to centralized, immutable audit logging sinks for continuous monitoring and SIEM ingestion."
        if has_log_sinks
        else (
            "Security telemetry, administrator activity, and system modification events are recorded "
            "in Google Cloud Audit Logs (centralized export sinks not discovered in Terraform)."
        )
    )
    iam_para = (
        f"**Identity, Access Management, and Audit Governance**: System administration is strictly governed by {auth_sum}. "
        f"Privileged access requires multi-factor authentication (MFA) and least-privilege role-based access control (RBAC). {audit_sentence}"
    )
    return [net_para, iam_para]


def _clean_inline_narrative_val(val: Any) -> str:
    """Sanitizes an inline field (CR/LF and line-start Markdown prefixes) before narrative splicing."""
    return _sanitize_markdown_inline_value(str(val or ""), on_table_line=False, at_line_start=True)


def build_dynamic_system_description(inventory: Dict[str, Any]) -> str:
    """Synthesizes an authoritative system description from extracted components."""
    sys_info = _as_dict(inventory.get("system_information"))
    net_info = _as_dict(inventory.get("network_architecture"))
    infra_info = _as_dict(inventory.get("infrastructure_components"))
    app_info = _as_dict(inventory.get("application_components"))

    sys_name = _clean_inline_narrative_val(sys_info.get("system_name", "Enterprise Cloud Information System"))
    sys_abbr = _clean_inline_narrative_val(sys_info.get("system_abbreviation", "SYS"))
    baseline = _clean_inline_narrative_val(sys_info.get("compliance_baseline", "NIST SP 800-53 Rev. 5"))
    impact_level = _clean_inline_narrative_val(sys_info.get("impact_level", "IL5"))

    user_desc = str(sys_info.get("system_description") or "").strip()
    if user_desc and any(tier in user_desc for tier in ("**Workload Execution", "**Compute Tier", "**Data Persistence", "**Network Perimeter")):
        return user_desc

    desc_paras = _build_mission_profile_paragraphs(
        sys_info, app_info, user_desc, sys_name, sys_abbr, baseline, impact_level
    )
    desc_paras.extend(_build_compute_and_data_paragraphs(infra_info, inventory))
    desc_paras.extend(_build_network_and_iam_paragraphs(net_info, infra_info, sys_info, inventory))
    return "\n\n".join(desc_paras)


def evaluate_template_conditionals(text: str, flags: Dict[str, bool]) -> str:
    """Evaluates conditional blocks in template text based on system inventory flags.

    Supports:
      <!-- IF CONDITION -->...<!-- ENDIF [CONDITION] -->
      <!-- IF NOT CONDITION -->...<!-- ENDIF [NOT CONDITION] -->
      {{#IF CONDITION}}...{{/IF [CONDITION]}}
      {{#IF_NOT CONDITION}}...{{/IF_NOT [CONDITION]}}
      {% if CONDITION %}...{% endif %}
      {% if not CONDITION %}...{% endif %}

    Args:
        text: Raw template content containing conditional blocks.
        flags: Mapping of flag names (uppercase) to boolean state.

    Returns:
        Content with evaluated conditional blocks rendered or removed.
    """
    return engine_evaluate_conditionals(text, flags)


def build_threat_detection_implementation_narrative(inventory: Dict[str, Any]) -> str:
    """Builds an authoritative, non-conditional Threat Detection narrative for policy documents.

    Constructs exact implementation procedures reflecting the active security stack
    (SCC, Google SecOps, external CSSP, and external SIEM).


    Args:
        inventory: System inventory dictionary containing extracted metadata.

    Returns:
        A Markdown-formatted string describing the implementation.
    """
    sys_info = _as_dict(inventory.get("system_information"))
    is_dod = is_dod_regime(sys_info)
    org = _clean_inline_narrative_val(sys_info.get("organization", "{{ ORGANIZATION }}"))
    sys_name = _clean_inline_narrative_val(sys_info.get("system_name", "{{ SYSTEM_NAME }}"))
    sec_ops = _as_dict(inventory.get("security_operations")) or _as_dict(sys_info.get("security_operations"))
    scc_enabled = sec_ops.get("scc_enabled", False)
    scc_tier = str(sec_ops.get("scc_tier", "premium")).title()
    secops_enabled = sec_ops.get("secops_enabled", False)
    secops_instance = sec_ops.get("secops_instance_name") or "chronicle-secops-enclave"
    default_cssp = "DISA" if is_dod else "[CONFIG_REQUIRED: SOC / Incident Response Provider]"
    cssp_provider = sec_ops.get("cssp_provider") or default_cssp
    ext_siem = sec_ops.get("external_siem_type") or "[CONFIG_REQUIRED: External SIEM]"
    allow_etp = sec_ops.get("allow_unaccredited_scc_in_il5", False)
    ext_sys = _as_dict(inventory.get("external_systems")) or _as_dict(sys_info.get("external_systems"))
    itsm = ext_sys.get("itsm_system") or "[CONFIG_REQUIRED: ITSM System]"

    paras = []

    if scc_enabled:
        paras.append(
            f"The {org} {sys_name} enclave enforces automated threat detection and continuous security posture "
            f"monitoring natively through Google Cloud Security Command Center ({scc_tier}). Event Threat Detection (ETD) "
            f"continuously inspects Cloud Audit Logs, VPC Flow Logs, and DNS queries using machine learning and threat "
            f"intelligence models to identify suspicious binary executions, anomalous administrative privilege escalations, "
            f"malicious outbound connections, and data egress spikes. Container Threat Detection (CTD) continuously inspects container "
            f"runtimes within GKE node clusters to detect reverse shells, unauthorized library modifications, and malicious binary execution."
        )
        paras.append(
            f"Security Health Analytics (SHA) continuously audits all deployed cloud infrastructure within {sys_name} against "
            f"the Center for Internet Security (CIS) Google Cloud Platform Foundation Benchmark and authoritative NIST SP 800-53 "
            f"Rev. 5 baseline rules. Identified misconfigurations are assigned normalized severity ratings "
            f"(CRITICAL, HIGH, MEDIUM, LOW) and automatically published to Cloud Pub/Sub topics. Finding notifications stream in real "
            f"time to the organizational incident response pipeline, feeding directly into {sec_ops.get('external_siem_type') or 'the enterprise SIEM'} "
            f"and alerting security operations personnel within 15 minutes of discovery."
        )
        if is_dod and allow_etp:
            paras.append(
                f"**Authorizing Official Exception-to-Policy (ETP)**: Security Command Center ({scc_tier}) is deployed within "
                f"this DoD Impact Level enclave pursuant to an approved Authorizing Official Exception-to-Policy. Operational "
                f"findings and telemetry generated by SCC are correlated alongside mandatory Cloud Logging export sinks streaming "
                f"directly to {cssp_provider} to maintain continuous authorization readiness."
            )
        elif is_dod:
            paras.append(
                f"In addition to cloud-native posture alerting, all audit events and security finding records are streamed via "
                f"Cloud Logging Log Router sinks to accredited {cssp_provider} CSOC ingest endpoints to fulfill DoDI 8530.01 requirements."
            )

    elif secops_enabled:
        paras.append(
            f"The {org} {sys_name} enclave enforces centralized threat detection and automated security operations through "
            f"Google Cloud SecOps (Chronicle) under dedicated tenant instance `{secops_instance}`. Google Cloud Logging Log Router "
            f"aggregated sinks continuously stream all organization-wide audit trails, VPC Flow Logs, and firewall connection records "
            f"into the Chronicle security telemetry lake without filtering or truncation."
        )
        paras.append(
            f"Chronicle continuously applies automated YARA-L detection rules, machine learning behavioral models, and automated IOC "
            f"matching against authoritative threat intelligence feeds (including DHS CISA AIS, commercial feeds, and Google "
            f"Threat Intelligence). Rule detections immediately trigger automated alert generation, case record creation, and "
            f"dispatch notifications to the {org} Incident Response Team and {cssp_provider} CSOC operators."
        )

    elif is_dod:
        # External CSSP / External SIEM (e.g. DoD IL4/IL5 enclaves with C5ISR / DISA / NAVIFOR / 616 OC + Splunk)
        paras.append(
            f"In strict accordance with DoDI 8530.01, CJCSM 6510.01B, and DoD Cloud Computing SRG requirements, continuous "
            f"system monitoring and intrusion detection for the {org} {sys_name} enclave are executed by an accredited "
            f"Cloud Cybersecurity Service Provider ({cssp_provider}) in coordination with the organizational {ext_siem} SIEM. "
            f"Google Cloud Security Command Center is not utilized as a primary security authority in this accredited enclave."
        )
        paras.append(
            f"Continuous telemetry is established through automated Cloud Logging Log Router export sinks configured at the root "
            f"folder level of {sys_name}. All Admin Activity audit records, System Event logs, Data Access logs, VPC Flow Logs, and "
            f"boundary firewall connection logs stream continuously to {cssp_provider} ingestion endpoints and dedicated Pub/Sub "
            f"topics feeding {ext_siem}. Accredited {cssp_provider} Security Operations Center (SOC) personnel maintain 24/7/365 active "
            f"surveillance, executing multi-enclave event correlation, signature analysis, and anomalous behavioral detection."
        )
        paras.append(
            f"When anomalous traffic or potential intrusions are identified, {cssp_provider} operators execute technical triage "
            f"and transmit emergency incident notifications to the {org} Incident Response Team and Lead ISSM within mandatory "
            f"CJCSM 6510.01B Table C-A-1 impact-tiered reporting timelines ({CJCSM_6510_01B_HIGH_IMPACT_SUMMARY}) via {itsm}."
        )
    else:
        paras.append(
            f"In accordance with NIST SP 800-53 Rev. 5 and NIST SP 800-61 Rev. 2, continuous system monitoring and intrusion "
            f"detection for {org} {sys_name} are executed by {cssp_provider} in coordination with the organizational {ext_siem} SIEM."
        )
        paras.append(
            f"Continuous telemetry is established through automated Cloud Logging Log Router export sinks configured at the root "
            f"folder or project level of {sys_name}. Admin Activity audit records, System Event logs, Data Access logs, VPC Flow Logs, "
            f"and boundary firewall connection logs stream continuously to dedicated Pub/Sub topics feeding {ext_siem} and {cssp_provider} "
            f"for 24/7/365 event correlation, signature analysis, and anomalous behavioral detection."
        )
        paras.append(
            f"When anomalous traffic or potential intrusions are identified, {cssp_provider} operators execute technical triage "
            f"and transmit incident notifications to the {org} Incident Response Team and Lead ISSM via {itsm} in accordance with "
            f"organizational incident response procedures."
        )

    return "\n\n".join(paras)


def build_audit_and_siem_implementation_narrative(inventory: Dict[str, Any]) -> str:
    """Builds an authoritative, non-conditional Audit Logging and SIEM Ingestion narrative.

    Args:
        inventory: System inventory dictionary containing extracted metadata.

    Returns:
        A Markdown-formatted string describing the implementation.
    """
    sys_info = _as_dict(inventory.get("system_information"))
    is_dod = is_dod_regime(sys_info)
    org = _clean_inline_narrative_val(sys_info.get("organization", "{{ ORGANIZATION }}"))
    sys_name = _clean_inline_narrative_val(sys_info.get("system_name", "{{ SYSTEM_NAME }}"))
    sec_ops = _as_dict(inventory.get("security_operations")) or _as_dict(sys_info.get("security_operations"))
    secops_enabled = sec_ops.get("secops_enabled", False)
    default_cssp = "DISA" if is_dod else "[CONFIG_REQUIRED: SOC / Incident Response Provider]"
    cssp_provider = sec_ops.get("cssp_provider") or default_cssp
    ext_siem = sec_ops.get("external_siem_type") or "[CONFIG_REQUIRED: External SIEM]"
    # AU-6(3)/SI-4 assessors look for the aggregation destination, not just the
    # product name. Rendered only when the operator actually declared one or it was
    # discovered from a log sink; never invented.
    ext_siem_destination = str(sec_ops.get("external_siem_destination") or "").strip()

    paras = []
    paras.append(
        f"{org} mandates the automatic generation and continuous ingestion of Google Cloud Admin Activity audit logs, "
        f"System Event audit logs, and Data Access audit logs across all projects within the {sys_name} resource hierarchy. "
        f"Every audit record produced captures the timestamp (UTC), calling principal identity, caller IP address and user agent, "
        f"targeted resource URI, requested API method, and operation outcome (success or error code)."
    )

    if secops_enabled:
        paras.append(
            f"Audit telemetry is routed in real time via Cloud Logging Log Router aggregated sinks directly into Google Cloud "
            f"SecOps (Chronicle). Chronicle provides hot, searchable indexing for 365 calendar days with automated normalization "
            f"into the Unified Data Model (UDM), allowing instant threat hunting and forensic timeline reconstruction by {org} analysts."
        )
    elif ext_siem and ext_siem.lower() not in ("none", "not applicable", "n/a", ""):
        destination_clause = (
            f" The aggregated sink destination of record is `{ext_siem_destination}`."
            if ext_siem_destination
            else ""
        )
        paras.append(
            f"Audit telemetry is exported in real time via Cloud Logging Log Router aggregated sinks to dedicated Cloud Pub/Sub topics "
            f"ingested by {ext_siem} and streaming to {cssp_provider}. {ext_siem} indexes all security-relevant audit logs, "
            f"enforcing automated correlation rules, threshold alerting, and compliance reporting dashboards."
            f"{destination_clause}"
        )
    else:
        paras.append(
            "Audit telemetry is exported in real time via Cloud Logging Log Router aggregated sinks to BigQuery analytical datasets "
            "in a dedicated, isolated audit project. Scheduled SQL queries and Cloud Monitoring metric alerts continuously inspect "
            "audit records for unauthorized IAM modifications, anomalous network changes, and privilege escalations."
        )

    locked = [
        b for b in (inventory.get("infrastructure_components", {}) or {}).get("storage_buckets", []) or []
        if isinstance(b, dict) and (b.get("retention_policy") or b.get("retention_period"))
    ]
    if locked:
        paras.append(
            f"Audit archives: {len(locked)} Cloud Storage bucket(s) with a retention policy are defined in Terraform; "
            "whether the policy is locked is [NOT DETERMINED FROM SOURCE]."
        )
    else:
        paras.append(
            "Audit log archival with a retention lock is [NOT DETERMINED FROM SOURCE]: no Cloud Storage bucket with a "
            "retention policy was found in Terraform. [CONFIG_REQUIRED: audit record retention and protection approach]"
        )
    return "\n\n".join(paras)


#: Authoritative CJCSM 6510.01B Table B-A-2 category names and Table C-A-1 impact-tiered timelines.
CJCSM_6510_01B_HIGH_IMPACT_SUMMARY: str = (
    "High-impact Category 1 Root Level Intrusion, Category 2 User Level Intrusion, "
    "Category 4 Denial of Service, and Category 7 Malicious Logic incidents: "
    "initial notification to next tier within 15 minutes, initial report to next tier within 4 hours, "
    "and initial submission to JIMS within 6 hours per Table C-A-1 and [CONFIG_REQUIRED: CSSP agreement timeline]"
)

CJCSM_6510_01B_TABLE_B_A_2_AND_C_A_1_ITEMS: Tuple[Tuple[str, str], ...] = (
    (
        "Category 1 (Root Level Intrusion — Incident)",
        "High impact: initial notification to next tier within **15 minutes**, initial report to next tier within **4 hours**, "
        "initial submission to JIMS within **6 hours** (Moderate/Low impact per CJCSM 6510.01B Table C-A-1 and "
        "[CONFIG_REQUIRED: CSSP agreement timeline]).",
    ),
    (
        "Category 2 (User Level Intrusion — Incident)",
        "High impact: initial notification to next tier within **15 minutes**, initial report to next tier within **4 hours**, "
        "initial submission to JIMS within **6 hours** (Moderate/Low impact per CJCSM 6510.01B Table C-A-1 and "
        "[CONFIG_REQUIRED: CSSP agreement timeline]).",
    ),
    (
        "Category 3 (Unsuccessful Activity Attempt — Event)",
        "Initial notification to next tier within **4 hours** and initial report to next tier within **12 hours** "
        "per CJCSM 6510.01B Table C-A-1.",
    ),
    (
        "Category 4 (Denial of Service — Incident)",
        "High/Moderate impact: initial notification to next tier within **15 minutes**, initial report to next tier within **4 hours**, "
        "and initial submission to JIMS within **6 hours** per CJCSM 6510.01B Table C-A-1.",
    ),
    (
        "Category 7 (Malicious Logic — Incident)",
        "High impact: initial notification to next tier within **15 minutes**, initial report to next tier within **4 hours**, "
        "and initial submission to JIMS within **6 hours** per CJCSM 6510.01B Table C-A-1.",
    ),
    (
        "Category 8 (Investigating — Event)",
        "Initial report to next tier consistent with the most severe possible interpretation per CJCSM 6510.01B Table C-A-1 "
        "(recategorized to Categories 1–7 or 9 prior to closure; no event is closed out as Category 8).",
    ),
)


def build_incident_escalation_implementation_narrative(inventory: Dict[str, Any]) -> str:
    """Builds an authoritative, non-conditional Incident Escalation and SLA narrative.

    Args:
        inventory: System inventory dictionary containing extracted metadata.

    Returns:
        A Markdown-formatted string describing the implementation.
    """
    sys_info = _as_dict(inventory.get("system_information"))
    org = _clean_inline_narrative_val(sys_info.get("organization", "{{ ORGANIZATION }}"))
    sys_name = _clean_inline_narrative_val(sys_info.get("system_name", "{{ SYSTEM_NAME }}"))
    sec_ops = _as_dict(inventory.get("security_operations")) or _as_dict(sys_info.get("security_operations"))
    ext_sys = _as_dict(inventory.get("external_systems")) or _as_dict(sys_info.get("external_systems"))
    is_dod = is_dod_regime(sys_info)
    default_cssp = "DISA" if is_dod else "[CONFIG_REQUIRED: SOC / Incident Response Provider]"
    cssp_provider = sec_ops.get("cssp_provider") or default_cssp
    itsm = ext_sys.get("itsm_system") or "[CONFIG_REQUIRED: ITSM System]"

    paras = []
    if is_dod:
        paras.append(
            f"In accordance with CJCSM 6510.01B (*Cyber Incident Handling Program*, Table B-A-2 and Table C-A-1) and "
            f"DoDI 8530.01, {org} {sys_name} enforces standardized incident categorization and impact-tiered reporting "
            f"timelines through {cssp_provider} and {itsm}:"
        )
        paras.append(
            "\n".join(f"- **{cat_name}**: {cat_desc}" for cat_name, cat_desc in CJCSM_6510_01B_TABLE_B_A_2_AND_C_A_1_ITEMS)
        )
        paras.append(
            f"All confirmed security incidents are tracked end-to-end within {itsm} and recorded in the eMASS Plan of Action and "
            f"Milestones (POA&M) repository to document containment steps, root cause analysis, and corrective actions."
        )
    else:
        paras.append(
            f"In accordance with the FedRAMP Incident Communications Procedure (ICP), FedRAMP CR26 Incident Evaluation and "
            f"Communication requirements, CISA Federal Incident Notification Guidelines, and NIST SP 800-61 Rev. 3, {org} {sys_name} "
            f"enforces standardized incident reporting and triage procedures:"
        )
        paras.append(
            "- **Suspected or Confirmed Security Incidents**: Mandatory reporting within **1 hour** of identification to CISA via "
            "https://www.cisa.gov/forms/report, to FedRAMP at `fedramp_security@gsa.gov` (legacy ICP) or "
            "`fedramp_security@fedramp.gov` (CR26), and to affected agency customers (Authorizing Officials, AO representatives, "
            "and Agency Incident Response Teams) per agency procedure.\n"
            "- **Agency & Organizational Escalation Timelines**: Additional impact-tiered escalation timelines per "
            "[CONFIG_REQUIRED: Agency Incident Reporting Timeline].\n"
            "- **Low Impact Events / Anomalies**: Documented and reviewed during standard incident triage."
        )
        paras.append(
            f"Incident ticketing, responder task assignments, and evidence preservation workflows are managed through {itsm}, "
            f"ensuring complete forensic traceability and auditable chain of custody."
        )
    return "\n\n".join(paras)


def build_vulnerability_management_implementation_narrative(inventory: Dict[str, Any]) -> str:
    """Builds an authoritative, non-conditional Vulnerability Management and Patching narrative.

    Args:
        inventory: System inventory dictionary containing extracted metadata.

    Returns:
        A Markdown-formatted string describing the implementation.
    """
    sys_info = _as_dict(inventory.get("system_information"))
    org = _clean_inline_narrative_val(sys_info.get("organization", "{{ ORGANIZATION }}"))
    sys_name = _clean_inline_narrative_val(sys_info.get("system_name", "{{ SYSTEM_NAME }}"))
    ext_sys = _as_dict(inventory.get("external_systems")) or _as_dict(sys_info.get("external_systems"))
    scanner = ext_sys.get("vulnerability_scanner") or "[CONFIG_REQUIRED: Vulnerability Scanner]"
    cicd = ext_sys.get("cicd_platform") or "[CONFIG_REQUIRED: CI/CD Platform]"
    sec_ops = _as_dict(inventory.get("security_operations")) or _as_dict(sys_info.get("security_operations"))
    is_dod = is_dod_regime(sys_info)
    default_cssp = "DISA" if is_dod else "[CONFIG_REQUIRED: SOC / Incident Response Provider]"
    cssp_provider = sec_ops.get("cssp_provider") or default_cssp

    paras = []
    paras.append(
        f"{org} implements a multi-tier vulnerability management program across the {sys_name} technology stack, "
        f"combining automated pre-deployment pipeline scanning, container image analysis, and host-level vulnerability auditing."
    )

    if is_dod:
        paras.append(
            f"**DoD Flaw Remediation & IAVM Benchmarks**: Host-level and OS infrastructure assessments are executed "
            f"using {scanner}. Scans are conducted on a mandatory monthly schedule (and following significant configuration changes). "
            f"Flaw remediation is strictly governed by US Cyber Command (USCYBERCOM) Information Assurance Vulnerability Management "
            f"(IAVM) directives:\n"
            f"- **IAVA Directives / Critical Severity (CVSS 9.0 - 10.0)**: Mandatory remediation and verification within **15 calendar days**.\n"
            f"- **IAVB Directives / High Severity (CVSS 7.0 - 8.9)**: Mandatory remediation and verification within **30 calendar days**.\n"
            f"- **Medium Severity (CVSS 4.0 - 6.9)**: Remediation within **60 calendar days**.\n"
            f"- **Low Severity (CVSS 0.1 - 3.9)**: Remediation within **90 calendar days** or addressed during scheduled maintenance releases."
        )
        paras.append(
            f"Automated OS patch execution is orchestrated via Google Cloud VM Manager, enforcing approved package version baselines "
            f"across all Compute Engine nodes. Containerized workloads hosted in Google Artifact Registry are continuously scanned "
            f"upon push and daily for newly published CVEs. Container images with unmitigated Critical or High vulnerabilities are "
            f"automatically blocked from deployment by Binary Authorization admission controllers and {cicd} DevSecOps gates. "
            f"All unresolved findings are ingested into eMASS POA&M tracking in coordination with {cssp_provider}."
        )
    else:
        paras.append(
            f"**Flaw Remediation Benchmarks**: All components of {sys_name} are assessed using {scanner} and Artifact Registry "
            f"Container Analysis. Flaws identified across software, firmware, and operating system packages must be remediated "
            f"in accordance with organizational risk thresholds:\n"
            f"- **Critical Vulnerabilities (CVSS 9.0 - 10.0)**: Remediated within **30 calendar days**.\n"
            f"- **High Vulnerabilities (CVSS 7.0 - 8.9)**: Remediated within **60 calendar days**.\n"
            f"- **Medium Vulnerabilities (CVSS 4.0 - 6.9)**: Remediated within **90 calendar days**.\n"
            f"- **Low Vulnerabilities (CVSS 0.1 - 3.9)**: Remediated within **120 calendar days**."
        )
        paras.append(
            f"Automated patch management is orchestrated via Google Cloud VM Manager patch deployments. Pre-production "
            f"software builds are audited within {cicd} pipelines using static application security testing (SAST) and "
            f"software composition analysis (SCA). Build artifacts failing security threshold gates are blocked from deployment."
        )
    return "\n\n".join(paras)


def build_identity_and_access_implementation_narrative(inventory: Dict[str, Any]) -> str:
    """Builds an authoritative, non-conditional Identity Federation and Access Management narrative.

    Args:
        inventory: System inventory dictionary containing extracted metadata.

    Returns:
        A Markdown-formatted string describing the implementation.
    """
    sys_info = _as_dict(inventory.get("system_information"))
    org = _clean_inline_narrative_val(sys_info.get("organization", "{{ ORGANIZATION }}"))
    sys_name = _clean_inline_narrative_val(sys_info.get("system_name", "{{ SYSTEM_NAME }}"))
    is_dod = is_dod_regime(sys_info)

    ext_sys = _as_dict(inventory.get("external_systems")) or _as_dict(sys_info.get("external_systems"))
    idp = ext_sys.get("identity_provider") or (
        "Enterprise Identity Provider (DoD CAC / PIV)" if is_dod else "Enterprise Identity Provider (Cloud Identity / SSO)"
    )
    mfa = ext_sys.get("mfa_mechanism") or "[CONFIG_REQUIRED: MFA Mechanism]"

    paras = []
    paras.append(
        f"{org} enforces centralized identity federation, strict least-privilege role assignment, and multi-factor authentication "
        f"for all administrative and user access to {sys_name}."
    )

    if is_dod:
        paras.append(
            f"**DoD Identity & PKI Authentication**: Identity management is federated with {idp}. User authentication strictly "
            f"enforces DoD Common Access Card (CAC) / Personal Identity Verification (PIV) PKI certificates utilizing FIPS 140-2/3 "
            f"validated hardware tokens ({mfa}). Password-only authentication and unauthenticated API access are strictly prohibited "
            f"at the Google Cloud Identity boundary."
        )
        itsm_name = ext_sys.get("itsm_system") or "[CONFIG_REQUIRED: ITSM System]"
        paras.append(
            f"**Privileged Access Management (PAM)**: Permanent assignment of high-privilege IAM roles (such as Security Admin, "
            f"Network Admin, or Organization Administrator) is strictly prohibited. Privileged operations require Just-In-Time (JIT) "
            f"activation via Google Cloud Privileged Access Manager (PAM). PAM requests require explicit two-party approval from the "
            f"Lead ISSO, enforce a maximum lease duration of 4 hours, and require documented justification with associated {itsm_name} "
            f"change tickets. All elevated actions are logged immutably to Google Cloud Audit Logs."
        )
    else:
        paras.append(
            f"**Enterprise Identity & MFA**: Administrative identities are managed through {idp}. All administrative and console access "
            f"requires phishing-resistant multi-factor authentication ({mfa}). Session timeouts are enforced after 15 minutes of inactivity."
        )
        paras.append(
            "**Least Privilege & Role Elevation**: Role assignments follow custom predefined IAM roles mapped strictly to job functions. "
            "Elevated access is mediated through Google Cloud Privileged Access Manager (PAM) for temporary, time-bound session elevations "
            "with auditable approval trails."
        )
    return "\n\n".join(paras)


_INVARIANT_CACHE_CAPACITY = 32
_INVARIANT_REPLACEMENTS_CACHE: Dict[str, Dict[str, str]] = {}


def _inventory_digest(inventory: Dict[str, Any]) -> str:
    """Returns a SHA-256 digest of the inventory content, used as a cache key.

    Keying on content rather than ``id(inventory)`` matters: CPython reuses object
    ids after garbage collection, and an in-place edit need not change the size of
    any container, so an identity-based key can return another system's narratives.

    Args:
        inventory: System inventory dictionary.

    Returns:
        Hex digest of the canonical JSON form of the inventory.
    """
    try:
        canonical = json.dumps(inventory, sort_keys=True, default=str)
    except TypeError:
        # Mixed-type keys cannot be sorted; fall back to insertion order.
        canonical = json.dumps(inventory, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _get_cached_invariant_replacements(inventory: Dict[str, Any]) -> Dict[str, str]:
    """Retrieves or builds cached invariant deliverable replacement strings.

    The same narratives and tables are substituted into the SSP, PTA, runbooks and
    20 policy manuals, so they are computed once per distinct inventory.
    """
    infra_info = inventory.get("infrastructure_components", {})
    net_info = inventory.get("network_architecture", {})
    fw_rules = net_info.get("firewall_rules", [])
    cache_key = _inventory_digest(inventory)
    cached = _INVARIANT_REPLACEMENTS_CACHE.get(cache_key)
    if cached is not None:
        return cached

    if len(_INVARIANT_REPLACEMENTS_CACHE) >= _INVARIANT_CACHE_CAPACITY:
        _INVARIANT_REPLACEMENTS_CACHE.clear()

    threat_narrative = build_threat_detection_implementation_narrative(inventory)
    audit_narrative = build_audit_and_siem_implementation_narrative(inventory)
    incident_narrative = build_incident_escalation_implementation_narrative(inventory)
    vuln_narrative = build_vulnerability_management_implementation_narrative(inventory)
    iam_narrative = build_identity_and_access_implementation_narrative(inventory)

    computed = {
        "system_description": build_dynamic_system_description(inventory),
        "firewall_matrix": format_firewall_matrix(fw_rules),
        "service_accounts": format_service_accounts(infra_info.get("service_accounts", [])),
        "storage_buckets": format_storage_buckets(infra_info.get("storage_buckets", [])),
        "separation_of_duties": format_separation_of_duties_table(inventory),
        "threat_detection": threat_narrative,
        "audit_and_siem": audit_narrative,
        "incident_escalation": incident_narrative,
        "vulnerability_management": vuln_narrative,
        "identity_and_access": iam_narrative,
        "subnet_boundary_table": format_subnet_boundary_table(inventory),
        "container_workload_table": format_container_workload_table(inventory),
    }
    _INVARIANT_REPLACEMENTS_CACHE[cache_key] = computed
    return computed


def _first_nonempty(*candidates: Any, default: str = "") -> str:
    """Returns the first truthy string candidate, or default."""
    for c in candidates:
        if c:
            return str(c)
    return default


def _build_app_stack_summary(app_info: Dict[str, Any]) -> str:
    """Summarizes discovered runtimes, frameworks, and applications for {{ APPLICATION_STACK }}."""
    runtimes_list = app_info.get("runtimes", [])
    frameworks_list = app_info.get("frameworks", [])
    apps_list = app_info.get("applications", [])
    app_stack_summary = []
    if runtimes_list:
        app_stack_summary.append(f"Runtimes: {', '.join(runtimes_list)}")
    if frameworks_list:
        app_stack_summary.append(f"Frameworks: {', '.join(frameworks_list)}")
    if apps_list:
        app_stack_summary.append(f"Applications: {', '.join(a.get('name') for a in apps_list)}")
    return " | ".join(app_stack_summary) if app_stack_summary else "Cloud-Native Infrastructure & Services"


def _build_secops_and_governance_tokens(
    inventory: Dict[str, Any],
    sys_info: Dict[str, Any],
    net_info: Dict[str, Any],
    sec_ops_info: Dict[str, Any],
    ext_sys_info: Dict[str, Any],
    is_dod: bool,
) -> Tuple[Dict[str, Any], Dict[str, bool]]:
    """Resolves SecOps, external system, and governance tokens plus conditional flags."""
    scc_enabled = sec_ops_info.get("scc_enabled") if "scc_enabled" in sec_ops_info else sys_info.get("scc_enabled")
    scc_tier = _first_nonempty(sec_ops_info.get("scc_tier"), sys_info.get("scc_tier"), default="premium")
    secops_enabled = sec_ops_info.get("secops_enabled") if "secops_enabled" in sec_ops_info else sys_info.get("secops_enabled")
    default_cssp = "DISA" if is_dod else "[CONFIG_REQUIRED: SOC / Incident Response Provider]"
    cssp_provider = _first_nonempty(sec_ops_info.get("cssp_provider"), sys_info.get("cssp_provider"), default=default_cssp)
    ext_siem = _first_nonempty(
        sec_ops_info.get("external_siem_type"), sys_info.get("external_siem_type"), default="[CONFIG_REQUIRED: External SIEM]"
    )
    if secops_enabled:
        siem_tool = "Google Cloud SecOps (Chronicle)"
    elif ext_siem not in ("None", None, ""):
        siem_tool = ext_siem
    else:
        siem_tool = f"{cssp_provider} SIEM"

    conn_sum_val = net_info.get("connectivity_summary")
    default_interconn = (
        conn_sum_val if (conn_sum_val and not str(conn_sum_val).startswith("[")) else "Dedicated Cloud Interconnect / HA Cloud VPN"
    )
    sens_class = _first_nonempty(
        sys_info.get("sensitivity_classification"),
        sys_info.get("data_classification"),
        default="Controlled Unclassified Information (CUI)" if is_dod else "Sensitive / Confidential Unclassified Information",
    )
    tokens = {
        "{{ SCC_STATUS }}": (
            f"Security Command Center {str(scc_tier).title()}"
            if scc_enabled
            else "Security Command Center (Disabled / Not Utilized)"
        ),
        "{{ SCC_TIER }}": str(scc_tier).title(),
        "{{ SECOPS_STATUS }}": "Google Cloud SecOps (Chronicle)" if secops_enabled else "Google Cloud SecOps (Not Deployed)",
        "{{ CSSP_PROVIDER }}": cssp_provider,
        "{{ EXTERNAL_SIEM }}": ext_siem,
        "{{ SIEM_TOOL }}": siem_tool,
        "{{ TELEMETRY_PIPELINE }}": _first_nonempty(
            sec_ops_info.get("telemetry_summary"),
            sys_info.get("telemetry_summary"),
            default="Cloud Logging Log Router export sinks streaming to external accredited CSSP and Cloud Monitoring",
        ),
        "{{ THREAT_DETECTION_ENGINE }}": _first_nonempty(
            sec_ops_info.get("threat_detection_engine"),
            sys_info.get("threat_detection_engine"),
            default="Cloud Monitoring Anomaly Detection and Audit Log Analysis",
        ),
        "{{ IDENTITY_PROVIDER }}": _first_nonempty(
            ext_sys_info.get("identity_provider"),
            sys_info.get("identity_provider"),
            default="Enterprise Identity Provider (DoD CAC / PIV)" if is_dod else "Enterprise Identity Provider (Cloud Identity / SSO)",
        ),
        "{{ MFA_MECHANISM }}": _first_nonempty(
            ext_sys_info.get("mfa_mechanism"), sys_info.get("mfa_mechanism"), default="[CONFIG_REQUIRED: MFA Mechanism]"
        ),
        "{{ VULNERABILITY_SCANNER }}": _first_nonempty(
            ext_sys_info.get("vulnerability_scanner"),
            sys_info.get("vulnerability_scanner"),
            default="[CONFIG_REQUIRED: Vulnerability Scanner]",
        ),
        "{{ ITSM_SYSTEM }}": _first_nonempty(
            ext_sys_info.get("itsm_system"), sys_info.get("itsm_system"), default="[CONFIG_REQUIRED: ITSM System]"
        ),
        "{{ CICD_PLATFORM }}": _first_nonempty(
            ext_sys_info.get("cicd_platform"), sys_info.get("cicd_platform"), default="[CONFIG_REQUIRED: CI/CD Platform]"
        ),
        "{{ EDR_SOLUTION }}": _first_nonempty(
            ext_sys_info.get("edr_solution"), sys_info.get("edr_solution"), default="[CONFIG_REQUIRED: Endpoint Detection and Response]"
        ),
        "{{ PERIMETER_GATEWAY }}": _first_nonempty(
            ext_sys_info.get("perimeter_gateway"), sys_info.get("perimeter_gateway"), default="[CONFIG_REQUIRED: Perimeter Gateway]"
        ),
        "{{ WARNING_BANNER_TYPE }}": _first_nonempty(
            sys_info.get("warning_banner_type"),
            default="DoD Notice and Consent Warning Banner" if is_dod else "System Use Notification Warning Banner",
        ),
        "{{ ACCESS_AGREEMENT_TYPE }}": _first_nonempty(
            sys_info.get("access_agreement_type"),
            default="System Authorization Access Request (SAAR / DD Form 2875)"
            if is_dod
            else "Rules of Behavior & Access Authorization Agreement",
        ),
        "{{ RULES_OF_BEHAVIOR }}": _first_nonempty(
            sys_info.get("rules_of_behavior"),
            default="DoD Rules of Behavior" if is_dod else "Organizational Rules of Behavior",
        ),
        "{{ PKI_TRUST_TYPE }}": _first_nonempty(
            sys_info.get("pki_trust_type"),
            default="DoD PKI / Federal PKI trust anchors" if is_dod else "Federal / Enterprise PKI trust anchors",
        ),
        "{{ USER_IDENTIFIER_TYPE }}": _first_nonempty(
            sys_info.get("user_identifier_type"),
            default="DoD ID Number (EDIPI) / UPN" if is_dod else "Enterprise User ID / UPN",
        ),
        "{{ INTERCONNECT_TYPE }}": _first_nonempty(sys_info.get("interconnect_type"), default=default_interconn),
        "{{ SENSITIVITY_CLASSIFICATION }}": sens_class,
        "{{ DATA_CLASSIFICATION }}": sens_class,
        "{{ SECOPS_INSTANCE }}": _first_nonempty(sec_ops_info.get("secops_instance_name"), default="chronicle-secops-enclave"),
    }

    regime = classify_regime(sys_info)
    if regime in REGIME_SPEC_BY_REGIME:
        flags = build_regime_template_flags(regime, inventory)
    else:
        cssp_active = bool(cssp_provider and cssp_provider.lower() not in ("none", "not applicable", "n/a", ""))
        ext_siem_active = bool(ext_siem and ext_siem.lower() not in ("none", "not applicable", "n/a", ""))
        flags = {
            "SCC_ENABLED": bool(scc_enabled),
            "SCC_DISABLED": not bool(scc_enabled),
            "SECOPS_ENABLED": bool(secops_enabled),
            "SECOPS_DISABLED": not bool(secops_enabled),
            "CSSP_ENABLED": cssp_active,
            "CSSP_DISABLED": not cssp_active,
            "EXTERNAL_SIEM_ENABLED": ext_siem_active,
            "DOD_ENCLAVE": is_dod,
            "DOD_IL4": False,
            "DOD_IL5": is_dod,
            "FEDRAMP_ENCLAVE": not is_dod,
            "FISMA_ENCLAVE": False,
            "CIVILIAN_ENCLAVE": not is_dod,
            "COMMERCIAL_ENCLAVE": not is_dod,
            "HIGH_BASELINE": True,
            "MODERATE_BASELINE": False,
            "LOW_BASELINE": False,
            "MODERATE_OR_HIGH_BASELINE": True,
            "ALLOW_UNACCREDITED_SCC": bool(sec_ops_info.get("allow_unaccredited_scc_in_il5", False)),
        }
    return tokens, flags


def _build_personnel_and_conmon_tokens(
    inventory: Dict[str, Any],
    sys_info: Dict[str, Any],
    infra_info: Dict[str, Any],
    roles_info: Dict[str, Any],
    is_dod: bool,
) -> Dict[str, Any]:
    """Resolves personnel roles, continuous monitoring, IDS, and RTO/RPO tokens."""
    ao_info = _as_dict(roles_info.get("authorizing_official"))
    so_info = _as_dict(roles_info.get("system_owner"))
    issm_info = _as_dict(roles_info.get("issm"))
    isso_info = _as_dict(roles_info.get("isso"))
    conmon = _as_dict(inventory.get("continuous_monitoring"))
    contingency_info = _as_dict(inventory.get("contingency_planning"))

    has_fw_svc = any("firewall" in str(s).lower() for s in infra_info.get("services_enabled", []))
    ids_val = _first_nonempty(
        infra_info.get("ids_solution"),
        inventory.get("ids_solution"),
        sys_info.get("ids_solution"),
        default="Cloud Next-Generation Firewall (NGFW)" if has_fw_svc else "[CONFIG_REQUIRED: IDS/IPS Solution]",
    )
    default_grc = "[CONFIG_REQUIRED: GRC System e.g. eMASS / CSAM]" if is_dod else "[CONFIG_REQUIRED: GRC System e.g. CSAM / Agency GRC]"
    sys_org = sys_info.get("organization")
    return {
        "{{ CONMON_REVIEW_FREQUENCY }}": _first_nonempty(
            conmon.get("review_frequency"), default="[CONFIG_REQUIRED: ConMon Review Frequency]"
        ),
        "{{ CONMON_ASSESSMENT_TYPE }}": _first_nonempty(
            conmon.get("assessment_type"), default="[CONFIG_REQUIRED: ConMon Assessment Type]"
        ),
        "{{ GRC_TOOL_REFERENCE }}": _first_nonempty(
            conmon.get("grc_tool_reference"), sys_info.get("rmf_governance_system"), default="[CONFIG_REQUIRED: GRC Tool]"
        ),
        "{{ RMF_GOVERNANCE_SYSTEM }}": _first_nonempty(sys_info.get("rmf_governance_system"), default=default_grc),
        "{{ INTRUSION_DETECTION_SYSTEM }}": ids_val,
        "{{ IDS_IPS_SOLUTION }}": ids_val,
        "{{ RECOVERY_TIME_OBJECTIVE }}": _first_nonempty(
            contingency_info.get("recovery_time_objective"),
            sys_info.get("recovery_time_objective"),
            default="[CONFIG_REQUIRED: Recovery Time Objective]",
        ),
        "{{ RECOVERY_POINT_OBJECTIVE }}": _first_nonempty(
            contingency_info.get("recovery_point_objective"),
            sys_info.get("recovery_point_objective"),
            default="[CONFIG_REQUIRED: Recovery Point Objective]",
        ),
        "{{ RTO }}": _first_nonempty(
            contingency_info.get("recovery_time_objective"), default="[CONFIG_REQUIRED: Recovery Time Objective]"
        ),
        "{{ RPO }}": _first_nonempty(
            contingency_info.get("recovery_point_objective"), default="[CONFIG_REQUIRED: Recovery Point Objective]"
        ),
        "{{ AO_NAME }}": _first_nonempty(ao_info.get("name"), default="[CONFIG_REQUIRED: Authorizing Official Name]"),
        "{{ AO_TITLE }}": _first_nonempty(ao_info.get("title"), default="Authorizing Official (AO)"),
        "{{ AO_ORG }}": _first_nonempty(ao_info.get("organization"), default="[CONFIG_REQUIRED: AO Organization]"),
        "{{ AO_EMAIL }}": _first_nonempty(ao_info.get("email"), default="[CONFIG_REQUIRED: Authorizing Official Email]"),
        "{{ AO_PHONE }}": _first_nonempty(ao_info.get("phone"), default="[CONFIG_REQUIRED: Authorizing Official Phone]"),
        "{{ SO_NAME }}": _first_nonempty(so_info.get("name"), default="[CONFIG_REQUIRED: System Owner Name]"),
        "{{ SYSTEM_OWNER_NAME }}": _first_nonempty(so_info.get("name"), default="[CONFIG_REQUIRED: System Owner Name]"),
        "{{ SO_TITLE }}": _first_nonempty(so_info.get("title"), default="Information System Owner (SO)"),
        "{{ SO_ORG }}": _first_nonempty(so_info.get("organization"), sys_org, default="[CONFIG_REQUIRED: Organization]"),
        "{{ SO_EMAIL }}": _first_nonempty(so_info.get("email"), default="[CONFIG_REQUIRED: System Owner Email]"),
        "{{ SO_PHONE }}": _first_nonempty(so_info.get("phone"), default="[CONFIG_REQUIRED: System Owner Phone]"),
        "{{ ISSM_NAME }}": _first_nonempty(issm_info.get("name"), default="[CONFIG_REQUIRED: ISSM Name]"),
        "{{ ISSM_TITLE }}": _first_nonempty(issm_info.get("title"), default="Information System Security Manager (ISSM)"),
        "{{ ISSM_ORG }}": _first_nonempty(issm_info.get("organization"), sys_org, default="[CONFIG_REQUIRED: Organization]"),
        "{{ ISSM_EMAIL }}": _first_nonempty(issm_info.get("email"), default="[CONFIG_REQUIRED: ISSM Email]"),
        "{{ ISSM_PHONE }}": _first_nonempty(issm_info.get("phone"), default="[CONFIG_REQUIRED: ISSM Phone]"),
        "{{ ISSO_NAME }}": _first_nonempty(isso_info.get("name"), default="[CONFIG_REQUIRED: ISSO Name]"),
        "{{ ISSO_TITLE }}": _first_nonempty(isso_info.get("title"), default="Information System Security Officer (ISSO)"),
        "{{ ISSO_ORG }}": _first_nonempty(isso_info.get("organization"), sys_org, default="[CONFIG_REQUIRED: Organization]"),
        "{{ ISSO_EMAIL }}": _first_nonempty(isso_info.get("email"), default="[CONFIG_REQUIRED: ISSO Email]"),
        "{{ ISSO_PHONE }}": _first_nonempty(isso_info.get("phone"), default="[CONFIG_REQUIRED: ISSO Phone]"),
    }


def _resolve_org_domain_and_prepared_by(inventory: Dict[str, Any], sys_info: Dict[str, Any]) -> Tuple[str, str]:
    """Resolves (prepared_by_val, org_domain_val) for template hydration."""
    org_val = sys_info.get("organization") or ""
    default_prepared_by = (
        f"{org_val} Security Engineering Team"
        if (org_val and not org_val.startswith("["))
        else "Cybersecurity & Security Engineering Team"
    )
    prepared_by_val = resolve_prepared_by(inventory) or default_prepared_by
    org_domain = resolve_organization_domain(inventory)
    if not org_domain:
        top_level_org = inventory.get("organization")
        configured = top_level_org.get("domain_name") if isinstance(top_level_org, dict) else None
        if isinstance(configured, str) and configured.strip():
            org_domain = configured.strip().lower()
    return prepared_by_val, org_domain or "[CONFIG_REQUIRED: Organization Domain]"


def _build_core_placeholder_map(
    inventory: Dict[str, Any],
    sys_info: Dict[str, Any],
    net_info: Dict[str, Any],
    infra_info: Dict[str, Any],
    app_info: Dict[str, Any],
    invariants: Dict[str, Any],
    version_str: str,
) -> Dict[str, Any]:
    """Builds the core system, infrastructure, network, and narrative placeholder dictionary."""
    prepared_by_val, org_domain_val = _resolve_org_domain_and_prepared_by(inventory, sys_info)
    fips_c, fips_i, fips_a = derive_fips_199_impacts(sys_info)
    kms_names = [
        str(k.get("name") if isinstance(k, dict) else k)
        for k in infra_info.get("kms_keys", [])
        if (k.get("name") if isinstance(k, dict) else k)
    ]
    clean_subnets = extract_clean_subnets(net_info.get("subnets_cidrs"))
    today_fmt = current_utc_datetime().strftime("%B %d, %Y")
    return {
        "{{ PREPARED_BY }}": prepared_by_val,
        "{{ SYSTEM_NAME }}": _first_nonempty(sys_info.get("system_name"), default="[CONFIG_REQUIRED: System Name]"),
        "{{ SYSTEM_ABBREVIATION }}": _first_nonempty(
            sys_info.get("system_abbreviation"), default="[CONFIG_REQUIRED: System Abbreviation]"
        ),
        "{{ CLOUD_PROVIDER }}": _first_nonempty(sys_info.get("cloud_provider"), default="Google Cloud Platform"),
        "{{ CSP_ABBR }}": _first_nonempty(sys_info.get("cloud_service_provider_abbr"), default="GCP"),
        "{{ IAC_TOOL }}": _first_nonempty(infra_info.get("iac_tool"), default="Terraform"),
        "{{ IAC_VERSION }}": _first_nonempty(infra_info.get("terraform_engine_version"), default="1.5.7+"),
        "{{ DITPR_ID }}": _first_nonempty(sys_info.get("ditpr_id"), default="[CONFIG_REQUIRED: DITPR ID]"),
        "{{ EMASS_SYSTEM_ID }}": _first_nonempty(sys_info.get("emass_system_id"), default="[CONFIG_REQUIRED: eMASS System ID]"),
        "{{ SYSTEM_DESCRIPTION }}": invariants["system_description"],
        "{{ IMPACT_LEVEL }}": _first_nonempty(sys_info.get("impact_level"), default="[CONFIG_REQUIRED: Impact Level]"),
        "{{ COMPLIANCE_BASELINE }}": _first_nonempty(sys_info.get("compliance_baseline"), default="NIST SP 800-53 Rev. 5"),
        "{{ ORGANIZATION }}": _first_nonempty(sys_info.get("organization"), default="[CONFIG_REQUIRED: Organization Name]"),
        "{{ ORGANIZATION_NAME }}": _first_nonempty(sys_info.get("organization"), default="[CONFIG_REQUIRED: Organization Name]"),
        "{{ ORGANIZATION_DOMAIN }}": org_domain_val,
        "{{ BILLING_ACCOUNT }}": _first_nonempty(sys_info.get("billing_account"), default="[CONFIG_REQUIRED: Billing Account ID]"),
        "{{ PRIMARY_LOCATION }}": _first_nonempty(sys_info.get("primary_location"), default="[CONFIG_REQUIRED: Primary Location]"),
        "{{ SECONDARY_LOCATION }}": _first_nonempty(
            sys_info.get("secondary_location"),
            _as_dict(inventory.get("contingency_planning")).get("secondary_location"),
            default="[CONFIG_REQUIRED: Secondary Location]",
        ),
        "{{ CSP_PATO_PACKAGE_ID }}": resolve_default_csp_pato_package_id(sys_info),
        "{{ VERSION }}": version_str,
        "{{ DATE }}": _first_nonempty(sys_info.get("effective_date"), default=today_fmt),
        "{{ AUTHORIZATION_DATE }}": today_fmt,
        "{{ CONFIDENTIALITY_IMPACT }}": fips_c,
        "{{ INTEGRITY_IMPACT }}": fips_i,
        "{{ AVAILABILITY_IMPACT }}": fips_a,
        "{{ FIPS_199_CATEGORIZATION }}": f"Confidentiality: {fips_c} / Integrity: {fips_i} / Availability: {fips_a}",
        "{{ GOVERNANCE_REGIME }}": _first_nonempty(
            sys_info.get("governance_regime"), sys_info.get("compliance_baseline"), default="[CONFIG_REQUIRED: Governance Regime]"
        ),
        "{{ NETWORK_VPCS }}": ", ".join(net_info.get("vpcs") or ["[CONFIG_REQUIRED: VPCs]"]),
        "{{ SUBNET_CIDRS }}": ", ".join(clean_subnets) if clean_subnets else "[CONFIG_REQUIRED: Subnet CIDRs]",
        "{{ SUBNET_BOUNDARY_TABLE }}": invariants.get("subnet_boundary_table", ""),
        "{{ CONTAINER_WORKLOAD_TABLE }}": invariants.get("container_workload_table", ""),
        "{{ CONNECTIVITY }}": _first_nonempty(
            inventory.get("connectivity_summary"), default="[CONFIG_REQUIRED: Primary Network Connectivity]"
        ),
        "{{ FIREWALL_MATRIX }}": invariants["firewall_matrix"],
        "{{ AUTHENTICATION_MECHANISM }}": _first_nonempty(
            inventory.get("authentication_summary"), default="[CONFIG_REQUIRED: Authentication Mechanism]"
        ),
        "{{ SERVICE_ACCOUNTS_LIST }}": invariants["service_accounts"],
        "{{ STORAGE_BUCKETS_LIST }}": invariants["storage_buckets"],
        "{{ KMS_KEYS }}": ", ".join(kms_names) if kms_names else "[CONFIG_REQUIRED: KMS Key]",
        "{{ ENCRYPTION_STANDARD }}": _first_nonempty(
            inventory.get("encryption_summary"), default="[CONFIG_REQUIRED: Cryptographic Protection Standard]"
        ),
        "{{ GCP_SERVICES_ENABLED }}": format_list_items(infra_info.get("services_enabled", [])),
        "{{ TERRAFORM_MODULES }}": format_list_items(infra_info.get("modules_used", [])),
        "{{ RMF_PACKAGE_ID }}": _first_nonempty(sys_info.get("rmf_package_id"), default="[CONFIG_REQUIRED: RMF Package ID]"),
        "{{ SYSTEM_ABBR }}": _first_nonempty(sys_info.get("system_abbreviation"), sys_info.get("system_name"), default="SYS"),
        "{{ SEPARATION_OF_DUTIES_TABLE }}": invariants["separation_of_duties"],
        "{{ DISCOVERED_SERVICES_COUNT }}": len(infra_info.get("services_enabled", [])),
        "{{ DISCOVERED_MODULES_COUNT }}": len(infra_info.get("modules_used", [])),
        "{{ DISCOVERED_RESOURCES_COUNT }}": len(infra_info.get("all_resources", [])),
        "{{ APPLICATION_STACK }}": _build_app_stack_summary(app_info),
        "{{ DISCOVERED_APPLICATIONS_COUNT }}": len(app_info.get("applications", [])),
        "{{ DISCOVERED_PACKAGES_COUNT }}": len(app_info.get("software_packages", [])),
        "{{ DISCOVERED_CONTAINERS_COUNT }}": len(app_info.get("container_images", [])),
        "{{ DISCOVERED_APP_PORTS_COUNT }}": len(app_info.get("exposed_ports", [])),
        "{{ THREAT_DETECTION_IMPLEMENTATION }}": invariants["threat_detection"],
        "{{ AUDIT_AND_SIEM_IMPLEMENTATION }}": invariants["audit_and_siem"],
        "{{ INCIDENT_ESCALATION_IMPLEMENTATION }}": invariants["incident_escalation"],
        "{{ VULNERABILITY_MANAGEMENT_IMPLEMENTATION }}": invariants["vulnerability_management"],
        "{{ IDENTITY_ACCESS_IMPLEMENTATION }}": invariants["identity_and_access"],
    }


def _format_applicable_disa_stigs_table(inventory: Dict[str, Any]) -> str:
    """Renders the Markdown DISA STIG/SRG table from StigResolver.evaluate_applicable_stigs."""
    resolver = stig_resolver.StigResolver(config=_as_dict(inventory.get("disa_stigs")))
    items = resolver.evaluate_applicable_stigs(inventory)
    rows = [
        "| DISA STIG / SRG Benchmark | Version | Public Reference Link | Triggering Component / Scope | Action Required for Assessor Team | Status |",
        "| :--- | :--- | :--- | :--- | :--- | :--- |",
    ]
    for item in items:
        rows.append(
            f"| **{item['title']}** | `{item['version']}` | [{item['slug']}]({item['url']}) | "
            f"{item['scope']} | {item['action']} | `{item['status']}` |"
        )
    return "\n".join(rows)


def populate_placeholders(
    content: str,
    inventory: Dict[str, Any],
    doc_version: str = "1.0.0",
    target_format: str = "markdown",
    fill_examples: bool = False,
) -> str:
    """Populates template placeholders with system inventory values."""
    sys_info = _as_dict(inventory.get("system_information"))
    net_info = _as_dict(inventory.get("network_architecture"))
    infra_info = _as_dict(inventory.get("infrastructure_components"))
    roles_info = _as_dict(inventory.get("personnel_roles"))
    app_info = _as_dict(inventory.get("application_components"))

    version_str = doc_version or sys_info.get("version", "1.0.0")
    sec_ops_info = _as_dict(inventory.get("security_operations")) or _as_dict(sys_info.get("security_operations"))
    ext_sys_info = _as_dict(inventory.get("external_systems")) or _as_dict(sys_info.get("external_systems"))
    is_dod = is_dod_regime(sys_info)

    secops_tokens, flags = _build_secops_and_governance_tokens(
        inventory, sys_info, net_info, sec_ops_info, ext_sys_info, is_dod
    )
    content = evaluate_template_conditionals(content, flags)

    derivable_tokens_used, runtime_tokens_used = find_operator_tokens(content)
    provenance_tokens_used = [
        t for t in (derivable_tokens_used + runtime_tokens_used) if t in PROVENANCE_TOKENS
    ]
    operator_context = build_operator_context(inventory, tokens=provenance_tokens_used)
    content = hydrate_operator_placeholders(content, inventory, context=operator_context)

    invariants = _get_cached_invariant_replacements(inventory)
    replacements = _build_core_placeholder_map(
        inventory, sys_info, net_info, infra_info, app_info, invariants, version_str
    )
    replacements.update(_build_personnel_and_conmon_tokens(inventory, sys_info, infra_info, roles_info, is_dod))
    replacements.update(secops_tokens)

    regime = classify_regime(sys_info)
    if regime in REGIME_SPEC_BY_REGIME:
        replacements.update(build_regime_odp_tokens(regime, inventory))

    if "APPLICABLE_DISA_STIGS_TABLE" in content:
        replacements["{{ APPLICABLE_DISA_STIGS_TABLE }}"] = _format_applicable_disa_stigs_table(inventory)

    replacements["{{ DISCOVERED_ENVIRONMENT_CONTEXT }}"] = render_discovered_context_block(
        operator_context, tokens=provenance_tokens_used
    )

    engine = TemplateEngine(target_format=target_format, fill_examples=fill_examples)
    return engine.render(content, replacements)

# ------------------------------------------------------------------------------
# YAML Builders
# ------------------------------------------------------------------------------


def _render_hwsw_yaml_header_and_contacts(
    sys_info: Dict[str, Any],
    roles_info: Dict[str, Any],
    doc_version: str,
) -> List[str]:
    """Renders the system_metadata and personnel_contacts header lines for HW/SW YAML."""
    so_info = _as_dict(roles_info.get("system_owner"))
    isso_info = _as_dict(roles_info.get("isso"))
    sys_name = sys_info.get("system_name") or "[CONFIG_REQUIRED: System Name]"
    sys_abbr = sys_info.get("system_abbreviation") or "[CONFIG_REQUIRED: System Abbreviation]"
    impact = sys_info.get("impact_level") or "[CONFIG_REQUIRED: Impact Level]"
    org = sys_info.get("organization") or "[CONFIG_REQUIRED: Organization Name]"
    eff_date = sys_info.get("effective_date") or current_utc_datetime().strftime("%B %d, %Y")
    ditpr_id = (
        sys_info.get("ditpr_id")
        or sys_info.get("ditpr_don_id")
        or sys_info.get("ditpr_emass_id")
        or "[CONFIG_REQUIRED: DITPR ID]"
    )
    return [
        "# ==============================================================================",
        "# Hardware and Software Inventory (NIST SP 800-53 Rev. 5 / Public Sector Baseline)",
        "# Ref: HWSWList_Template.xlsm (Generic Platform Provisioning)",
        "# ==============================================================================\n",
        "system_metadata:",
        f"  system_name: {safe_yaml_scalar(sys_name)}",
        f"  system_abbreviation: {safe_yaml_scalar(sys_abbr)}",
        f"  impact_level: {safe_yaml_scalar(impact)}",
        f"  compliance_baseline: {safe_yaml_scalar(sys_info.get('compliance_baseline', 'NIST SP 800-53 Rev. 5'))}",
        f"  organization: {safe_yaml_scalar(org)}",
        f"  effective_date: {safe_yaml_scalar(eff_date)}",
        f"  document_version: {safe_yaml_scalar(doc_version)}",
        f"  ditpr_emass_id: {safe_yaml_scalar(ditpr_id)}\n",
        "personnel_contacts:",
        "  system_owner:",
        f"    name: {safe_yaml_scalar(so_info.get('name') or '[CONFIG_REQUIRED: System Owner Name]')}",
        f"    email: {safe_yaml_scalar(so_info.get('email') or '[CONFIG_REQUIRED: System Owner Email]')}",
        f"    phone: {safe_yaml_scalar(so_info.get('phone') or '[CONFIG_REQUIRED: System Owner Phone]')}",
        "  isso_poc:",
        f"    name: {safe_yaml_scalar(isso_info.get('name') or '[CONFIG_REQUIRED: ISSO Name]')}",
        f"    email: {safe_yaml_scalar(isso_info.get('email') or '[CONFIG_REQUIRED: ISSO Email]')}",
        f"    phone: {safe_yaml_scalar(isso_info.get('phone') or '[CONFIG_REQUIRED: ISSO Phone]')}\n",
    ]


def _append_hwsw_yaml_assets(lines: List[str], inventory: Dict[str, Any]) -> None:
    """Appends hardware_assets and software_and_services_inventory sections from canonical builders."""
    custom_svcs = inventory.get("custom_services") or {}
    resolve_hw = (lambda k: excel_hydrator.resolve_exact_hw_type(k)) if excel_hydrator else (lambda _k: "Server")
    resolve_sw = (lambda k: excel_hydrator.resolve_exact_sw_type(k, custom_svcs)) if excel_hydrator else (lambda _k: "API Service")
    hw_records, sw_records, _cloud_provider, _csp_abbr = build_hwsw_inventory_records(
        inventory, resolve_hw_type=resolve_hw, resolve_sw_type=resolve_sw
    )

    lines.append("hardware_assets:")
    for rec in hw_records:
        hw_id_str = f"{float(rec['hw_id']):.1f}"
        lines.extend([
            f"  - id: {safe_yaml_scalar(hw_id_str)}",
            f"    component_type: {safe_yaml_scalar(rec['component_type'])}",
            f"    asset_name: {safe_yaml_scalar(rec['asset_name'])}",
            f"    nickname: {safe_yaml_scalar(rec['nickname'])}",
            f"    asset_ip_address: {safe_yaml_scalar(rec['asset_ip_address'])}",
            f"    public_facing: {safe_yaml_scalar(rec['public_facing'])}",
            f"    virtual_asset: {safe_yaml_scalar(rec['virtual_asset'])}",
            f"    manufacturer: {safe_yaml_scalar(rec['manufacturer'])}",
            f"    model_number: {safe_yaml_scalar(rec['model_number'])}",
            f"    serial_number: {safe_yaml_scalar(rec['serial_number'])}",
        ])
        if not rec.get("omit_yaml_os_fw"):
            lines.append(f"    os_fw_version: {safe_yaml_scalar(rec['os_fw_version'])}")
        lines.extend([
            f"    location: {safe_yaml_scalar(rec['location'])}",
            f"    approval_status: {safe_yaml_scalar(rec['approval_status'])}",
            f"    critical_asset: {safe_yaml_scalar(rec['critical_asset'])}",
        ])

    lines.append("\nsoftware_and_services_inventory:")
    lines.append("  software_assets:")
    for srec in sw_records:
        lines.extend([
            f"    - id: {safe_yaml_scalar(str(srec['sw_id']))}",
            f"      category: {safe_yaml_scalar(srec['category'])}",
            f"      software_type: {safe_yaml_scalar(srec['software_type'])}",
            f"      software_name: {safe_yaml_scalar(srec['software_name'])}",
            f"      vendor: {safe_yaml_scalar(srec['vendor'])}",
            f"      version: {safe_yaml_scalar(srec['version'])}",
            f"      purpose: {safe_yaml_scalar(srec['purpose'])}",
            f"      approval_status: {safe_yaml_scalar(srec['approval_status'])}",
        ])


def generate_hwsw_inventory_yaml(inventory: Dict[str, Any], doc_version: str = "1.0.0") -> str:
    """Generates Hardware and Software Asset Inventory in YAML format."""
    sys_info = _as_dict(inventory.get("system_information"))
    roles_info = _as_dict(inventory.get("personnel_roles"))

    lines = _render_hwsw_yaml_header_and_contacts(sys_info, roles_info, doc_version)
    _append_hwsw_yaml_assets(lines, inventory)

    lines.append("\nrmf_team_manual_action:")
    lines.append(
        '  callout: "> [!IMPORTANT] **RMF TEAM ACTION REQUIRED**: Perform annual'
        " physical asset audits for local client workstations and confirm"
        ' eMASS hardware barcode serial numbers."'
    )
    return "\n".join(lines)


def _render_ppsm_yaml_header_and_firewall(
    sys_info: Dict[str, Any],
    roles_info: Dict[str, Any],
    fw_rules: List[Dict[str, Any]],
    doc_version: str,
) -> List[str]:
    """Renders system_metadata, personnel_contacts, and boundary_firewall_matrix for PPSM YAML."""
    so_info = _as_dict(roles_info.get("system_owner"))
    isso_info = _as_dict(roles_info.get("isso"))
    sys_name = sys_info.get("system_name") or "[CONFIG_REQUIRED: System Name]"
    sys_abbr = sys_info.get("system_abbreviation") or "[CONFIG_REQUIRED: System Abbreviation]"
    impact = sys_info.get("impact_level") or "[CONFIG_REQUIRED: Impact Level]"
    comp_base = sys_info.get("compliance_baseline") or "NIST SP 800-53 Rev. 5"
    org = sys_info.get("organization") or "[CONFIG_REQUIRED: Organization Name]"
    eff_date = sys_info.get("effective_date") or current_utc_datetime().strftime("%Y-%m-%d")
    emass_id = sys_info.get("emass_system_id") or sys_info.get("emass_id") or "[CONFIG_REQUIRED: eMASS System ID]"
    ditpr_id = (
        sys_info.get("ditpr_id")
        or sys_info.get("ditpr_don_id")
        or sys_info.get("ditpr_emass_id")
        or "[CONFIG_REQUIRED: DITPR ID]"
    )
    lines = [
        "# ==============================================================================",
        "# Ports, Protocols, and Services Matrix (PPSM)",
        "# Ref: PPSMBoundariesInformationExport_Template.xlsm",
        "# ==============================================================================\n",
        "system_metadata:",
        f"  system_name: {safe_yaml_scalar(sys_name)}",
        f"  system_abbreviation: {safe_yaml_scalar(sys_abbr)}",
        f"  impact_level: {safe_yaml_scalar(impact)}",
        f"  compliance_baseline: {safe_yaml_scalar(comp_base)}",
        f"  organization: {safe_yaml_scalar(org)}",
        f"  date_exported: {safe_yaml_scalar(eff_date)}",
        f"  document_version: {safe_yaml_scalar(doc_version)}",
        f"  emass_system_id: {safe_yaml_scalar(emass_id)}",
        f"  ditpr_id: {safe_yaml_scalar(ditpr_id)}\n",
        "personnel_contacts:",
        "  system_owner:",
        f"    name: {safe_yaml_scalar(so_info.get('name') or '[CONFIG_REQUIRED: System Owner Name]')}",
        f"    email: {safe_yaml_scalar(so_info.get('email') or '[CONFIG_REQUIRED: System Owner Email]')}",
        f"    phone: {safe_yaml_scalar(so_info.get('phone') or '[CONFIG_REQUIRED: System Owner Phone]')}",
        "  isso_poc:",
        f"    name: {safe_yaml_scalar(isso_info.get('name') or '[CONFIG_REQUIRED: ISSO Name]')}",
        f"    email: {safe_yaml_scalar(isso_info.get('email') or '[CONFIG_REQUIRED: ISSO Email]')}",
        f"    phone: {safe_yaml_scalar(isso_info.get('phone') or '[CONFIG_REQUIRED: ISSO Phone]')}\n",
        "boundary_firewall_matrix:",
    ]
    if not fw_rules:
        lines.append("  []")
    else:
        for fw in fw_rules:
            lines.extend([
                f"  - name: {safe_yaml_scalar(str(fw.get('name') or 'firewall-rule'))}",
                f"    direction: {safe_yaml_scalar(str(fw.get('direction') or 'INGRESS'))}",
                f"    protocol: {safe_yaml_scalar(str(fw.get('protocol') or 'TCP'))}",
                f"    ports: {safe_yaml_scalar(str(fw.get('ports') or '443'))}",
                f"    action: {safe_yaml_scalar(str(fw.get('action') or 'ALLOW'))}",
            ])
    lines.append("")
    return lines


def _append_ppsm_yaml_matrix_rows(
    lines: List[str],
    inventory: Dict[str, Any],
) -> None:
    """Appends ppsm_matrix YAML records using canonical build_ppsm_records."""
    lines.append("ppsm_matrix:")
    records = build_ppsm_records(inventory, cloud_provider_default="Google Cloud Platform (GCP)")
    if not records:
        lines.append("  []")
        return
    for rec in records:
        lines.extend([
            f"  - id: {safe_yaml_scalar(str(rec['id']))}",
            f"    type: {safe_yaml_scalar(rec['type'])}",
            f"    record_name: {safe_yaml_scalar(rec['record_name'])}",
            f"    protocol: {safe_yaml_scalar(rec['protocol'])}",
            f"    data_service: {safe_yaml_scalar(rec['data_service'])}",
            f"    port: {safe_yaml_scalar(rec['port'])}",
            f"    boundary: {safe_yaml_scalar(rec['boundary'])}",
            f"    source_device_name: {safe_yaml_scalar(rec['source_device_name'])}",
            f"    source_location: {safe_yaml_scalar(rec['source_location'])}",
            f"    source_ip: {safe_yaml_scalar(rec['source_ip'])}",
            f"    source_fqdn: {safe_yaml_scalar(rec['source_fqdn'])}",
            f"    logical_source_point: {safe_yaml_scalar(rec['logical_source_point'])}",
            f"    connection_logical_source_point: {safe_yaml_scalar(rec['logical_source_point'])}",
            f"    destination_device_name: {safe_yaml_scalar(rec['destination_device_name'])}",
            f"    destination_location: {safe_yaml_scalar(rec['destination_location'])}",
            f"    destination_ip: {safe_yaml_scalar(rec['destination_ip'])}",
            f"    destination_fqdn: {safe_yaml_scalar(rec['destination_fqdn'])}",
            f"    logical_destination_point: {safe_yaml_scalar(rec['logical_destination_point'])}",
            f"    connection_logical_destination_point: {safe_yaml_scalar(rec['logical_destination_point'])}",
            f"    vpn_encrypted_traffic: {safe_yaml_scalar(rec['vpn_encrypted_traffic'])}",
            f"    vpn_tunnel_type: {safe_yaml_scalar(rec['vpn_tunnel_type'])}",
            f"    purpose: {safe_yaml_scalar(rec['purpose'])}",
            f"    ppsm_status: {safe_yaml_scalar(rec['ppsm_status'])}",
        ])


def generate_ppsm_matrix_yaml(inventory: Dict[str, Any], doc_version: str = "1.0.0") -> str:
    """Generates Ports, Protocols, and Services Matrix (PPSM) in YAML format."""
    sys_info = _as_dict(inventory.get("system_information"))
    net_info = _as_dict(inventory.get("network_architecture"))
    roles_info = _as_dict(inventory.get("personnel_roles"))
    fw_rules = net_info.get("firewall_rules", [])

    lines = _render_ppsm_yaml_header_and_firewall(sys_info, roles_info, fw_rules, doc_version)
    _append_ppsm_yaml_matrix_rows(lines, inventory)

    lines.append("\nrmf_team_manual_action:")
    lines.append(
        '  callout: "> [!IMPORTANT] **RMF TEAM ACTION REQUIRED**: Confirm'
        " registration of all listed ports/protocols in the eMASS PPSM"
        ' Registry and upload approval certificates."'
    )
    return "\n".join(lines)


def generate_poam_matrix_yaml(
    inventory: Dict[str, Any],
    doc_version: str = "1.0.0",
    eff_date: Optional[str] = None,
) -> str:
    """Generates Plan of Action and Milestones (POA&M) in YAML format.

    Dynamically derives POA&M items from live infrastructure scans, security gap
    analysis, or user-configured POA&M items.

    Args:
        inventory: System inventory dictionary containing discovered components and gaps.
        doc_version: Version string for the generated POA&M tracking matrix.
        eff_date: Optional effective date override for derived POA&M items.

    Returns:
        Formatted YAML string for POA&M Matrix.
    """
    sys_info = _as_dict(inventory.get("system_information"))
    infra_info = _as_dict(inventory.get("infrastructure_components"))
    roles_info = _as_dict(inventory.get("personnel_roles"))

    sys_name = sys_info.get("system_name") or "[CONFIG_REQUIRED: System Name]"
    sys_abbr = sys_info.get("system_abbreviation") or "[CONFIG_REQUIRED: System Abbreviation]"
    impact = sys_info.get("impact_level") or "[CONFIG_REQUIRED: Impact Level]"
    baseline = sys_info.get("compliance_baseline") or "NIST SP 800-53 Rev. 5"
    governance_regime = sys_info.get("governance_regime") or baseline
    org = sys_info.get("organization") or "[CONFIG_REQUIRED: Organization Name]"
    location = sys_info.get("primary_location") or "[CONFIG_REQUIRED: Primary Location]"
    eff_date = eff_date or sys_info.get("effective_date") or current_utc_datetime().strftime("%B %d, %Y")
    rmf_system = sys_info.get("rmf_governance_system") or "Enterprise GRC (eMASS / CSAM)"

    isso_info = _as_dict(roles_info.get("isso"))
    ao_info = _as_dict(roles_info.get("authorizing_official"))

    isso_name = isso_info.get("name") or "[CONFIG_REQUIRED: ISSO Name]"
    isso_title = isso_info.get("title") or "Information System Security Officer"
    ao_name = ao_info.get("name") or "[CONFIG_REQUIRED: Authorizing Official Name]"
    ao_title = ao_info.get("title") or "Authorizing Official"

    # Derive real findings from infrastructure gaps and the run's scanner results
    poam_findings = derive_poam_findings(inventory, eff_date, target_dir=active_poam_target())

    high_count = sum(1 for i in poam_findings if str(i.get("severity", "")).upper() in ["HIGH", "VERY HIGH"])
    mod_count = sum(1 for i in poam_findings if str(i.get("severity", "")).upper() == "MODERATE")
    low_count = sum(1 for i in poam_findings if str(i.get("severity", "")).upper() in ["LOW", "VERY LOW"])

    lines = []
    lines.append("# ==============================================================================")
    lines.append("# Plan of Action and Milestones (POA&M) Compliance Tracking Matrix")
    lines.append("# Baseline: NIST SP 800-37 Rev. 2 (RMF) / FedRAMP High / DoD Cloud SRG IL5")
    lines.append("# Dynamically Derived from Live Infrastructure Scans & Security Gap Analysis")
    lines.append("# ==============================================================================\n")

    lines.append("system_metadata:")
    lines.append(f"  system_name: {safe_yaml_scalar(sys_name)}")
    lines.append(f"  system_abbreviation: {safe_yaml_scalar(sys_abbr)}")
    lines.append(f"  impact_level: {safe_yaml_scalar(impact)}")
    lines.append(f"  compliance_baseline: {safe_yaml_scalar(baseline)}")
    lines.append(f"  governance_regime: {safe_yaml_scalar(governance_regime)}")
    lines.append(f"  organization: {safe_yaml_scalar(org)}")
    lines.append(f"  effective_date: {safe_yaml_scalar(eff_date)}")
    lines.append(f"  document_version: {safe_yaml_scalar(doc_version)}")
    lines.append(f"  grc_repository_reference: {safe_yaml_scalar(rmf_system)}")
    lines.append(f"  security_point_of_contact: {safe_yaml_scalar(f'{isso_name} ({isso_title})')}")
    csp_abbr = (
        sys_info.get("cloud_service_provider_abbr")
        or "GCP"
    )
    csp_key = csp_abbr.lower()
    lines.append("  discovered_infrastructure_summary:")
    lines.append(f'    active_{csp_key}_apis: {len(infra_info.get("services_enabled", []))}')
    lines.append(f'    deployed_terraform_modules: {len(infra_info.get("modules_used", []))}')
    lines.append(f'    scanned_resources: {len(infra_info.get("all_resources", []))}')
    lines.append(f"    primary_{csp_key}_region: {safe_yaml_scalar(location)}\n")

    lines.append("poam_tracking_summary:")
    lines.append(f"  total_open_items: {len(poam_findings)}")
    lines.append(f"  high_risk_items: {high_count}")
    lines.append(f"  moderate_risk_items: {mod_count}")
    lines.append(f"  low_risk_items: {low_count}")
    unparsed_files = infra_info.get("unparsed_terraform_files") or []
    conditional_undetermined = infra_info.get("conditional_resources_undetermined") or []
    status_text = (
        f"{len(poam_findings)} open POA&M item(s) tracked; "
        f"{len(unparsed_files)} unparsed Terraform file(s); "
        f"{len(conditional_undetermined)} conditional/undetermined resource(s)"
    )
    lines.append(f"  automated_iac_coverage_status: {safe_yaml_scalar(status_text)}\n")

    lines.append("poam_items:")
    if not poam_findings:
        lines.append("  []")
    else:
        for item in poam_findings:
            lines.append(f"  - item_id: {safe_yaml_scalar(item.get('item_id', 'POAM-001'))}")
            lines.append(f"    control_identifier: {safe_yaml_scalar(item.get('control', 'CA-05'))}")
            w_name = str(item.get("weakness_name") or item.get("title") or item.get("desc", "Remediation item")).strip()
            if "\n" in w_name:
                w_name = w_name.split("\n")[0].strip()
            lines.append(f"    weakness_name: {safe_yaml_scalar(w_name)}")
            lines.append(f"    weakness_description: {safe_yaml_scalar(item.get('desc', 'Remediation item'))}")
            lines.append(f"    source_of_weakness: {safe_yaml_scalar(item.get('source', 'Security Assessment'))}")
            lines.append(f"    severity_risk_level: {safe_yaml_scalar(item.get('severity', 'Low'))}")
            lines.append(f"    scheduled_completion_date: {safe_yaml_scalar(item.get('sched_date', 'Pending'))}")
            lines.append("    milestones:")
            lines.append("      - step: 1")
            lines.append(f"        description: {safe_yaml_scalar(item.get('milestone_desc', 'Remediate finding'))}")
            lines.append(f"        target_date: {safe_yaml_scalar(item.get('sched_date', 'Pending'))}")
            lines.append(f"        status: {safe_yaml_scalar(item.get('milestone_status', 'Open'))}")
            lines.append(f"    point_of_contact: {safe_yaml_scalar(f'{isso_name} ({isso_title})')}")
            lines.append(f"    status: {safe_yaml_scalar(item.get('status', 'Ongoing'))}")

    lines.append("\ngovernance_instructions:")
    lines.append('  review_frequency: "Monthly (Every 30 Days) during Continuous Monitoring"')
    lines.append(f"  reporting_authority: {safe_yaml_scalar(f'{ao_name} ({ao_title})')}")
    lines.append(
        f'  rmf_team_callout: "> [!IMPORTANT] **RMF TEAM ACTION REQUIRED**: Review'
        f' and update POA&M milestone dates monthly in {rmf_system}. All findings'
        ' must retain an active remediation pathway or formal AO risk acceptance decision."'
    )

    return "\n".join(lines)


# ------------------------------------------------------------------------------
# Master Provisioning Orchestrator
# ------------------------------------------------------------------------------
def generate_ato_artifacts(
    target_dir: Union[str, Path],
    policy_format: Optional[str] = None,
    data_format: Optional[str] = None,
    oscal_format: Optional[str] = None,
    oscal_version: Optional[str] = None,
    registry: Optional[ExporterRegistry] = None,
    fill_examples: Optional[bool] = None,
    run_scanners: bool = False,
    scanners: Optional[List[str]] = None,
    semgrep_config: Optional[str] = None,
) -> Dict[str, List[str]]:
    """Main entry point to hydrate all RMF compliance package deliverables.

    Coordinates modular Strategy-pattern export of System Security Plan (SSP),
    Path to Authorization (PTA), 20 NIST SP 800-53 Rev. 5 policy manuals,
    incident response runbooks, structured YAML matrices, macro-enabled
    Excel workbooks, and machine-readable NIST OSCAL packages.

    Args:
        target_dir: Path to the target foundation directory containing system_inventory.json.
        policy_format: Export format for policies ("both", "docx", or "markdown").
        data_format: Export format for matrices ("both", "excel", or "yaml").
        oscal_format: Export format for OSCAL deliverables ("both", "json", "yaml", or "none").
        oscal_version: Target NIST OSCAL specification version (e.g. "1.2.3" or "1.1.0").
        registry: Optional ExporterRegistry instance for dependency injection.
        fill_examples: Whether to replace unfilled placeholders with example tags.
        run_scanners: Operator opt-in for live scanners (checkov, semgrep by default)
            on a private copy of the target. COMPLIANCE_DISABLE_LIVE_SCANNERS wins.
        scanners: Optional subset of live scanners to run when ``run_scanners`` is set.

    Returns:
        A dictionary mapping deliverable types ("markdown", "docx", "yaml", "excel", "oscal")
        to lists of generated absolute file paths.
    """
    target_path = resolve_path(target_dir)
    # Placeholder-hydration diagnostics are deduplicated per process; clear the
    # registry so each invocation reports its own fail-closed findings.
    reset_hydration_warnings()
    inventory = load_system_inventory(target_path)
    inventory = scrub_sensitive_data(inventory)
    # Fail closed before writing anything for a regime the templates do not cover (D6).
    require_supported_regime(_as_dict(inventory.get("system_information")))
    # Scanner and SARIF findings are collected once, scoped to the target, and
    # reused by the POA&M YAML/XLSM, SCTM and OSCAL builders below.
    with poam_run(inventory, target_path, resolve_scanner_policy(run_scanners, scanners, semgrep_config=semgrep_config)):
        return _generate_package(target_path, inventory, policy_format, data_format, oscal_format, oscal_version, registry, fill_examples)


def _init_generation_audit_and_exporters(
    target_path: Path,
    inventory: Dict[str, Any],
    policy_format: Optional[str],
    data_format: Optional[str],
    oscal_format: Optional[str],
    oscal_version: Optional[str],
    registry: Optional[ExporterRegistry],
    fill_examples: Optional[bool],
) -> Tuple[Path, Any, List[Any], List[Any], str, Optional[str], bool]:
    """Resolves export preferences, configures the audit log, and selects policy/data exporters."""
    export_prefs = _as_dict(inventory.get("export_preferences"))
    policy_fmt = policy_format or export_prefs.get("policy_formats") or "both"
    data_fmt = data_format or export_prefs.get("structured_data_formats") or "both"
    oscal_fmt = oscal_format or export_prefs.get("oscal_formats") or "both"
    if not oscal_version and "oscal_version" in export_prefs:
        oscal_version = export_prefs["oscal_version"]
    fill_ex_bool = bool(export_prefs.get("fill_examples", False)) if fill_examples is None else bool(fill_examples)

    oscal_pref = oscal_fmt.strip().lower() if oscal_fmt else "both"
    if oscal_pref not in ("none", "false", "disabled", "off"):
        from .oscal_generator import resolve_oscal_version
        oscal_version = resolve_oscal_version(inventory, oscal_version)

    out_dir = ensure_directory(target_path / "ato_artifacts")
    ensure_path_within_boundary(out_dir, target_path)

    try:
        audit_logger = configure_audit_log(
            sink_path=out_dir / "compliance_engine_audit.jsonl",
            component="compliance-engine",
            allowed_boundary=target_path,
        )
        audit_logger.emit(AuditEvent.PIPELINE_STARTED, detail={"target_dir": str(target_path)})
    except PermissionError:
        raise
    except OSError as e:
        logger.warning("Could not configure audit log: %s", e)
        audit_logger = None

    logger.info("=" * 80)
    logger.info("ATO COMPLIANCE PACKAGE GENERATION: %s", target_path)
    logger.info("   Policy Format Preference : %s", policy_fmt.upper())
    logger.info("   Data Format Preference   : %s", data_fmt.upper())
    logger.info("   OSCAL Format Preference  : %s", str(oscal_fmt).upper())
    logger.info("=" * 80)

    reg = registry if registry is not None else ExporterRegistry._get_default_instance()
    policy_exporters = reg.get_policy_exporters(policy_fmt)
    data_exporters = reg.get_data_exporters(data_fmt)
    return out_dir, audit_logger, policy_exporters, data_exporters, oscal_pref, oscal_version, fill_ex_bool


def _generate_oscal_and_log_summary(
    target_path: Path,
    out_dir: Path,
    inventory: Dict[str, Any],
    doc_versions: Dict[str, Any],
    oscal_pref: str,
    oscal_version: Optional[str],
    artifacts_generated: Dict[str, List[str]],
    audit_logger: Any,
) -> None:
    """Exports OSCAL deliverables (if enabled) and logs the final provisioning summary and next-step banner."""
    if oscal_pref not in ("none", "false", "disabled", "off"):
        target_oscal_ver = oscal_version or "1.2.3"
        logger.info("Generating NIST OSCAL %s Machine-Readable Package (%s)...", target_oscal_ver, oscal_pref.upper())
        try:
            from .oscal_generator import export_oscal_artifacts
            ssp_version = doc_versions.get("ssp", "1.0.0")
            oscal_files = export_oscal_artifacts(
                target_path,
                inventory,
                doc_version=ssp_version,
                oscal_format=oscal_pref,
                oscal_version=target_oscal_ver,
            )
            for of in oscal_files:
                ensure_path_within_boundary(of, out_dir)
                artifacts_generated.setdefault("oscal", []).append(str(of))
                if audit_logger:
                    audit_logger.emit(
                        AuditEvent.ARTIFACT_GENERATED, outcome=AuditOutcome.SUCCESS, obj=str(of), detail={"format": "oscal"}
                    )
        except Exception as oscal_err:
            try:
                get_audit_logger().emit(
                    AuditEvent.ARTIFACT_GENERATED,
                    outcome=AuditOutcome.FAILURE,
                    detail={"format": "oscal", "error": str(oscal_err)},
                )
            except OSError as audit_err:
                logger.error("Could not record OSCAL failure to audit trail: %s", audit_err)
            logger.error("Failed generating OSCAL deliverables: %s", oscal_err)
            raise RuntimeError(f"OSCAL generation failed: {oscal_err}") from oscal_err

    total_count = sum(len(v) for v in artifacts_generated.values())
    if audit_logger:
        audit_logger.emit(AuditEvent.PIPELINE_COMPLETED, detail={"total_artifacts": total_count})

    logger.info("=" * 80)
    logger.info("ATO PACKAGE PROVISIONING COMPLETE: Generated %d Total Deliverables", total_count)
    logger.info("=" * 80)
    logger.info("  • Markdown Artifacts (.md)   : %d", len(artifacts_generated.get("markdown", [])))
    logger.info("  • Word Policy Manuals (.docx): %d", len(artifacts_generated.get("docx", [])))
    logger.info("  • Structured YAMLs (.yaml)   : %d", len(artifacts_generated.get("yaml", [])))
    logger.info("  • Macro Excel Books (.xlsm)  : %d", len(artifacts_generated.get("excel", [])))
    if artifacts_generated.get("oscal"):
        logger.info("  • NIST OSCAL Packages        : %d", len(artifacts_generated["oscal"]))
    for fmt_k, items_v in artifacts_generated.items():
        if fmt_k not in ("markdown", "docx", "yaml", "excel", "oscal"):
            logger.info("  • Deliverables (%s)          : %d", fmt_k, len(items_v))
    logger.info("  • Output Directory           : %s", out_dir)
    logger.info("=" * 80)

    val_script_abs = Path(SCRIPTS_DIR) / "validate_compliance_artifacts.py"
    try:
        target_display = os.path.relpath(str(target_path), os.getcwd())
    except ValueError:
        target_display = str(target_path)
    if val_script_abs.is_file():
        try:
            val_script_display = os.path.relpath(str(val_script_abs), os.getcwd())
        except ValueError:
            val_script_display = str(val_script_abs)
        next_step_cmd = f"python3 {val_script_display} {target_display} --fix"
    else:
        next_step_cmd = f"compliance-validate {target_display} --fix"
    logger.info("=" * 80)
    logger.info("NEXT RECOMMENDED STEP (PART B): ATO PACKAGE VALIDATION & STIG AUDIT")
    logger.info("=" * 80)
    logger.info("To run package validation, check for drift, and inspect required DISA STIGs:")
    logger.info("  %s", next_step_cmd)
    logger.info("=" * 80)


def _generate_package(
    target_path: Path,
    inventory: Dict[str, Any],
    policy_format: Optional[str],
    data_format: Optional[str],
    oscal_format: Optional[str],
    oscal_version: Optional[str],
    registry: Optional[ExporterRegistry],
    fill_examples: Optional[bool],
) -> Dict[str, List[str]]:
    """Renders every deliverable for an already loaded inventory (see generate_ato_artifacts)."""
    doc_versions = _as_dict(inventory.get("document_versions"))
    policy_versions = _as_dict(doc_versions.get("policies"))
    out_dir, audit_logger, policy_exporters, data_exporters, oscal_pref, oscal_version, fill_ex_bool = (
        _init_generation_audit_and_exporters(
            target_path, inventory, policy_format, data_format, oscal_format, oscal_version, registry, fill_examples
        )
    )
    policies_out_dir = ensure_directory(out_dir / "Policies_and_Procedures")
    templates_root = Path(TEMPLATES_DIR)
    artifacts_generated: Dict[str, List[str]] = {"markdown": [], "docx": [], "yaml": [], "excel": [], "oscal": []}

    def _export_policy_document(raw_text: str, base_output_path: Path, doc_version: str = "1.0.0") -> None:
        ensure_path_within_boundary(base_output_path, out_dir)
        populated = populate_placeholders(raw_text, inventory, doc_version, target_format="markdown", fill_examples=fill_ex_bool)
        for exporter in policy_exporters:
            generated_path = exporter.export_document(populated, base_output_path, inventory, allowed_boundary=out_dir)
            ensure_path_within_boundary(generated_path, out_dir)
            artifacts_generated.setdefault(exporter.format_name, []).append(str(generated_path))
            if audit_logger:
                audit_logger.emit(
                    AuditEvent.ARTIFACT_GENERATED, outcome=AuditOutcome.SUCCESS, obj=str(generated_path), detail={"format": exporter.format_name}
                )

    sys_info = _as_dict(inventory.get("system_information"))
    active_regime = require_supported_regime(sys_info)
    regime_spec = get_regime_spec(active_regime)
    active_baseline = get_regime_baseline(active_regime)
    ssp_template_file = templates_root / "ssp" / regime_spec.ssp_template_filename
    if ssp_template_file.exists():
        ssp_folder = ensure_directory(out_dir / "SSP")
        rendered_ssp = render_ssp_for_regime(read_text_file(ssp_template_file), active_regime, active_baseline)
        if any(exp.format_name == "docx" for exp in policy_exporters):
            logger.info("Generating System Security Plan Word document (.docx)...")
        _export_policy_document(rendered_ssp, ssp_folder / "SSP_System_Security_Plan", doc_versions.get("ssp", "1.0.0"))

    pta_template_file = templates_root / "pta" / "Path_to_Authorization_Template.md"
    if pta_template_file.exists():
        _export_policy_document(read_text_file(pta_template_file), out_dir / "Path_to_Authorization", doc_versions.get("pta", "1.0.0"))

    runbooks_template_dir = templates_root / "runbooks"
    if runbooks_template_dir.exists():
        runbooks_folder = ensure_directory(out_dir / "Incident_Response_Runbooks")
        ir_version = (
            policy_versions.get("Incident_Response")
            or policy_versions.get("IncidentResponse")
            or doc_versions.get("incident_response_policy")
            or doc_versions.get("default_version", "1.0.0")
        )
        for rb_file in sorted(runbooks_template_dir.glob("*.md")):
            if rb_file.name == "Incident_Response_Runbook_Template.md":
                continue
            _export_policy_document(read_text_file(rb_file), runbooks_folder / sanitize_filename(rb_file.stem), ir_version)

    matrix_generators: Dict[str, Callable[..., Any]] = {
        "hwsw": generate_hwsw_inventory_yaml,
        "ppsm": generate_ppsm_matrix_yaml,
        "poam": generate_poam_matrix_yaml,
        "populate_placeholders": populate_placeholders,
    }
    for data_exporter in data_exporters:
        for mf in data_exporter.export_all_matrices(target_path, inventory, doc_versions, matrix_generators):
            ensure_path_within_boundary(mf, out_dir)
            artifacts_generated.setdefault(data_exporter.format_name, []).append(str(mf))
            if audit_logger:
                audit_logger.emit(
                    AuditEvent.ARTIFACT_GENERATED, outcome=AuditOutcome.SUCCESS, obj=str(mf), detail={"format": data_exporter.format_name}
                )

    fips_md_template = templates_root / "fips" / "FIPS_Cryptographic_Matrix_Template.md"
    if fips_md_template.exists():
        fips_folder = ensure_directory(out_dir / "FIPS_Cryptography")
        _export_policy_document(read_text_file(fips_md_template), fips_folder / "FIPS_Cryptographic_Matrix", doc_versions.get("fips_matrix", "1.0.0"))

    policies_dir = templates_root / "policies"
    if policies_dir.exists():
        for p_file in sorted(policies_dir.glob("*.md")):
            filtered_policy = filter_policy_appendix_rows(read_text_file(p_file), active_baseline["control_ids"])
            family_key = p_file.name.replace("_Policy_and_Procedures.md", "").replace("_Policy.md", "")
            policy_ver = policy_versions.get(family_key) or policy_versions.get(family_key.replace("_", "")) or doc_versions.get("default_version", "1.0.0")
            _export_policy_document(filtered_policy, policies_out_dir / sanitize_filename(p_file.stem), policy_ver)

    _generate_oscal_and_log_summary(
        target_path, out_dir, inventory, doc_versions, oscal_pref, oscal_version, artifacts_generated, audit_logger
    )
    return artifacts_generated


def main() -> None:
    """Parses command-line arguments and executes ATO compliance package provisioning."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(description="Master ATO Artifacts Provisioner & Dual-Format Hydration Engine")
    parser.add_argument("target_dir", help="Target blueprint folder (required; not a repository root or symlink)")
    parser.add_argument(
        "--policy-format", choices=["both", "docx", "markdown"], default=None,
        help="Export format for 20 policy manuals (overrides compliance_config.yaml)",
    )
    parser.add_argument(
        "--data-format", choices=["both", "excel", "yaml"], default=None,
        help="Export format for structured data matrices (overrides compliance_config.yaml)",
    )
    parser.add_argument(
        "--oscal-format", choices=["both", "json", "yaml", "none"], default=None,
        help="Export format for NIST OSCAL deliverables (overrides compliance_config.yaml)",
    )
    parser.add_argument("--oscal-version", default=None, help="Target NIST OSCAL specification version (e.g. 1.2.3 or 1.1.0; defaults to 1.2.3)")
    parser.add_argument(
        "--run-scanners", action="store_true",
        help="Run live scanners (Checkov, Semgrep) on a sanitized private copy of the target. Off by default; "
        "COMPLIANCE_DISABLE_LIVE_SCANNERS=1 always disables them.",
    )
    parser.add_argument(
        "--scanners", default=None,
        help="Comma-separated live scanners for --run-scanners (checkov, semgrep, trivy; default checkov,semgrep)",
    )
    parser.add_argument(
        "--semgrep-config", default=None,
        help="Operator-side Semgrep ruleset path or registry reference (or set COMPLIANCE_SEMGREP_CONFIG)",
    )
    args = parser.parse_args()

    try:
        target_abs = resolve_cli_target(args.target_dir)
        generate_ato_artifacts(
            target_abs,
            policy_format=args.policy_format,
            data_format=args.data_format,
            oscal_format=args.oscal_format,
            oscal_version=args.oscal_version,
            run_scanners=args.run_scanners,
            scanners=[s for s in args.scanners.split(",") if s.strip()] if args.scanners else None,
            semgrep_config=args.semgrep_config,
        )
    except (FileNotFoundError, NotADirectoryError, PermissionError, ValueError, yaml.YAMLError) as err:
        print(f"[ERROR] {err}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
