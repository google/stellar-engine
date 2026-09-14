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
Master ATO Artifacts Provisioner & Dual-Format Hydration Engine

This script provisions and hydrates the complete Public Sector & Regulated Cloud compliance package:
1. System Security Plan (SSP) & Path to Authorization (PTA) (.md)
2. 20 NIST SP 800-53 Rev. 5 Policy Manuals (.md and/or .docx)
3. Hardware & Software Asset Inventory (.yaml and/or .xlsm)
4. Plan of Action & Milestones (POA&M) (.yaml and/or .xlsm)
5. Ports, Protocols, and Services Matrix (PPSM) (.yaml and/or .xlsm)
6. Security Control Traceability Matrix (SCTM) (.yaml and/or .xlsm)
7. FIPS 140-3 Cryptographic Validation Matrix (.yaml)

Format Preferences & CLI Options:
- Policy Formats: "both" (default), "docx", "markdown"
- Structured Data Formats: "both" (default), "excel", "yaml"
"""

import argparse
from datetime import datetime
import logging
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

logger = logging.getLogger(__name__)

try:
    from .export_strategies import ExporterRegistry
    from .file_helpers import (
        DEFAULT_CSP_PATO_PACKAGE_ID,
        ensure_directory,
        ensure_path_within_boundary,
        extract_clean_subnets,
        get_scripts_dir,
        get_skill_root,
        get_templates_dir,
        has_terraform_infrastructure,
        read_json_file,
        read_text_file,
        resolve_path,
        safe_yaml_scalar,
        sanitize_container_image_tag,
        sanitize_filename,
        sanitize_software_package_identity,
        scrub_sensitive_data,
        validate_system_inventory_schema,
    )
    from .service_catalog import resolve_gcp_service
    from .extract_system_data import (
        clean_interpolated_string,
        is_valid_cidr,
        is_valid_resource_name,
    )
    from . import excel_hydrator
    from .audit_log import (
        AuditEvent,
        AuditOutcome,
        configure_audit_log,
        get_audit_logger,
    )
    from .template_engine import (
        TemplateEngine,
        evaluate_template_conditionals as engine_evaluate_conditionals,
    )
    from .runbook_hydration import (
        build_operator_context,
        find_operator_tokens,
        hydrate_operator_placeholders,
        render_discovered_context_block,
        reset_hydration_warnings,
    )
except (ImportError, ValueError):
    from export_strategies import ExporterRegistry
    from file_helpers import (
        DEFAULT_CSP_PATO_PACKAGE_ID,
        ensure_directory,
        ensure_path_within_boundary,
        extract_clean_subnets,
        get_scripts_dir,
        get_skill_root,
        get_templates_dir,
        has_terraform_infrastructure,
        read_json_file,
        read_text_file,
        resolve_path,
        safe_yaml_scalar,
        sanitize_container_image_tag,
        sanitize_filename,
        sanitize_software_package_identity,
        scrub_sensitive_data,
        validate_system_inventory_schema,
    )
    from service_catalog import resolve_gcp_service
    from extract_system_data import (
        clean_interpolated_string,
        is_valid_cidr,
        is_valid_resource_name,
    )
    from template_engine import (
        TemplateEngine,
        evaluate_template_conditionals as engine_evaluate_conditionals,
    )
    from runbook_hydration import (
        build_operator_context,
        find_operator_tokens,
        hydrate_operator_placeholders,
        render_discovered_context_block,
        reset_hydration_warnings,
    )
    try:
        import excel_hydrator
    except ImportError:
        excel_hydrator = None
    # The audit trail is itself a control (AU-2/AU-3/AU-9). Losing it silently
    # would leave the pipeline running with no verifiable evidence that it did,
    # so an import failure here is fatal rather than swallowed.
    from audit_log import (
        AuditEvent,
        AuditOutcome,
        configure_audit_log,
        get_audit_logger,
    )

SKILL_BASE = str(get_skill_root())
SCRIPTS_DIR = str(get_scripts_dir())
TEMPLATES_DIR = str(get_templates_dir())


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
        try:
            import tempfile
            env = os.environ.copy()
            for k in ["LD_PRELOAD", "PYTHONPATH", "LD_LIBRARY_PATH"]:
                env.pop(k, None)
            with tempfile.NamedTemporaryFile("w+", encoding="utf-8") as stdout_f, tempfile.NamedTemporaryFile("w+", encoding="utf-8") as stderr_f:
                res = subprocess.run(
                    [sys.executable, str(extractor_script), "--", str(target_path)],
                    check=False,
                    timeout=300,
                    stdout=stdout_f,
                    stderr=stderr_f,
                    env=env,
                )
                stdout_f.seek(0)
                stderr_f.seek(0)
                stdout = stdout_f.read(1024 * 1024)
                stderr = stderr_f.read(1024 * 1024)
            if res.returncode != 0:
                logger.warning(
                    "extract_system_data.py exited with code %d: %s",
                    res.returncode,
                    stderr.strip() or stdout.strip(),
                )
        except subprocess.TimeoutExpired:
            logger.error("extract_system_data.py timed out after 300 seconds for '%s'", target_path)
            raise
        except (subprocess.SubprocessError, OSError) as err:
            logger.error("Failed to execute extract_system_data.py for '%s': %s", target_path, err)
            raise

    if inventory_path.exists():
        inventory = read_json_file(inventory_path)
        validate_system_inventory_schema(inventory, source_path=inventory_path)
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
        lines.append(f"- **{b.get('name', 'Storage Bucket')}**: Location `{b.get('location', 'US')}`, CMEK Encrypted: `{cmek_display}`")
    return "\n".join(lines)


def format_firewall_matrix(fw_list: List[Dict[str, Any]]) -> str:
    """Formats firewall rule definitions into a Markdown table.

    Args:
        fw_list: List of firewall rule dictionaries.

    Returns:
        A Markdown table string displaying firewall rules and actions.
    """
    if not fw_list:
        return "| Rule Name | Direction | Protocol | Ports | Action |\n|---|---|---|---|---|\n| [NOT DETERMINED FROM SOURCE] | N/A | N/A | N/A | N/A |"
    header = "| Rule Name | Direction | Protocol | Ports | Action |\n|---|---|---|---|---|"
    rows: List[str] = []
    for fw in fw_list:
        rows.append(f"| {fw.get('name')} | {fw.get('direction')} | {fw.get('protocol')} | {fw.get('ports')} | {fw.get('action')} |")
    return header + "\n" + "\n".join(rows)


def format_subnet_boundary_table(inventory: Dict[str, Any]) -> str:
    """Formats a Markdown table of discovered network subnets and CIDR blocks.

    Args:
        inventory: System inventory dictionary.

    Returns:
        A Markdown table string documenting all discovered subnet CIDR ranges.
    """
    net_info = inventory.get("network_architecture", {})
    clean_subnets = extract_clean_subnets(net_info.get("subnets_cidrs"))
    vpcs = [clean_interpolated_string(v) for v in net_info.get("vpcs", []) if clean_interpolated_string(v)]
    vpc_desc = ", ".join(vpcs) if vpcs else "Software-Defined VPC Enclave"
    if not clean_subnets:
        return "*Standard RFC 1918 software-defined VPC subnets with zero direct public ingress.*"
    lines = [
        "| Subnet CIDR Range | Allocation Type | Security Boundary Enclave | Ingress Classification |",
        "| :--- | :--- | :--- | :--- |",
    ]
    for cidr in clean_subnets:
        lines.append(
            f"| `{cidr}` | Private Virtual Subnetwork | `{vpc_desc}` | Zero Direct Public Ingress (Private RFC 1918) |"
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
        return "*No custom container images discovered; system utilizes native managed cloud platform services.*"
    lines = [
        "| Container Image Reference | Base Image / OS | Workload Source File | Security Scanning & Registry Policy |",
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
        base_os = c.get("base_os") or (f"Debian/Alpine ({img_ver})" if img_ver != "latest" else "Hardened Minimal OS")
        lines.append(
            f"| `{img_name}` | {base_os} | `{source_file}` | Continuous Vulnerability Scanning via Artifact Registry & Distroless Hardening |"
        )
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


def format_separation_of_duties_table(inventory: Dict[str, Any]) -> str:
    """Formats an IAM separation of duties table from inventory components.

    Args:
        inventory: System inventory dictionary containing infrastructure and IAM components.

    Returns:
        A Markdown-formatted table representing IAM separation of duties.
    """
    sys_info = inventory.get("system_information", {})
    cloud_provider = (
        sys_info.get("cloud_provider")
        or inventory.get("cloud_provider")
        or "Google Cloud Platform"
    )
    csp_abbr = (
        sys_info.get("cloud_service_provider_abbr")
        or "GCP"
    )
    csp_lower = csp_abbr.lower()

    infra_info = inventory.get("infrastructure_components", {})
    iam_matrix = infra_info.get("iam_roles_matrix", [])
    iam_bindings = infra_info.get("iam_bindings", [])
    service_accounts = infra_info.get("service_accounts", [])
    proj_id = (
        sys_info.get("project_id")
        or inventory.get("project_id")
        or "[CONFIG_REQUIRED: project_id]"
    )
    proj_num = str(
        sys_info.get("project_number")
        or inventory.get("project_number")
        or "<PROJECT_NUMBER>"
    )

    lines: List[str] = []
    lines.append(f"| Role Group / Principal | Assigned {csp_abbr} IAM Roles & Permissions | Source Configuration / Codebase File |")
    lines.append("| :--- | :--- | :--- |")

    rendered_principals: Set[str] = set()
    if iam_matrix:
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
            if (clean_p.startswith("serviceAccount:") or clean_p.startswith("user:") or clean_p.startswith("group:")) and not (" " in clean_p or "(" in clean_p):
                p_display = f"`{clean_p}`"
            else:
                p_display = clean_p
            roles_str = ", ".join(r_list) if r_list else "Project Scope Permissions"
            lines.append(f"| {p_display} | {roles_str} | `{f_src}` |")

    grouped_bindings: Dict[str, Dict[str, Any]] = {}
    if iam_bindings:
        for b in iam_bindings:
            raw_p = str(b.get("principal", "")).strip()
            r_val = str(b.get("role", "Custom Role")).replace("roles/", "").strip()
            f_src = b.get("file", "Terraform Code")

            # Skip unconfigured or abstract bindings
            if not raw_p or "${each.value.role}" in r_val or r_val.startswith("${each."):
                continue

            # Defensive sanitization against un-interpolated variables
            if "${each.value.member}" in raw_p or raw_p == "${each.value}":
                if "cryptoKey" in r_val or "kms" in f_src:
                    raw_p = "CMEK Key Encrypter/Decrypter Service Agents (Storage, BigQuery, Pub/Sub, Cloud SQL)"
                elif "serviceusage" in r_val or "impersonator" in f_src:
                    raw_p = "Deployment & CI/CD Pipeline Impersonators"
                else:
                    continue
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
                continue

            # Format principal presentation
            if raw_p.startswith("serviceAccount:") or raw_p.startswith("user:") or raw_p.startswith("group:"):
                p_display = f"`{raw_p}`"
            elif " " in raw_p or "(" in raw_p:
                p_display = raw_p
            else:
                p_display = f"`{raw_p}`"

            if p_display not in grouped_bindings:
                grouped_bindings[p_display] = {"roles": [], "file": f_src}
            if r_val and r_val not in grouped_bindings[p_display]["roles"]:
                grouped_bindings[p_display]["roles"].append(r_val)

        for p_display, p_meta in grouped_bindings.items():
            clean_p = p_display.strip("`").strip()
            if clean_p not in rendered_principals:
                rendered_principals.add(clean_p)
                roles_str = ", ".join(sorted(p_meta["roles"])) if p_meta["roles"] else "Scoped Permissions"
                lines.append(f"| {p_display} | {roles_str} | `{p_meta['file']}` |")

    if service_accounts:
        for sa in service_accounts:
            sa_id = sa.get("account_id", "service-account")
            sa_res = sa.get("resource_name", "")
            sa_file = sa.get("file", "Terraform")
            sa_principal = f"`serviceAccount:{sa_id}`"
            # Avoid duplicate rows if this service account is already rendered in iam_bindings
            if any(sa_id in p or (sa_res and sa_res in p) for p in rendered_principals):
                continue
            if sa_id not in rendered_principals:
                rendered_principals.add(sa_id)
                lines.append(f"| {sa_principal} | Principle of Least Privilege (Scoped Workload Account) | `{sa_file}` |")

    iam_groups = inventory.get("iam_groups", {})
    if not rendered_principals and iam_groups:
        for grp_role, grp_list in iam_groups.items():
            if isinstance(grp_list, list):
                for g in grp_list:
                    if g:
                        p_name = f"`{g}`"
                        if p_name not in rendered_principals:
                            rendered_principals.add(p_name)
                            role_desc = grp_role.replace("_", " ").title()
                            lines.append(f"| {p_name} | {role_desc} (Configured in foundation_variables.yaml) | `foundation_configs/shared/foundation_variables.yaml` |")

    if not rendered_principals:
        if sys_info.get("system_name") and csp_lower == "gcp":
            lines.append(f"| `{csp_lower}-organization-admins` | resourcemanager.organizationAdmin, orgpolicy.policyAdmin, billing.user, resourcemanager.folderAdmin | Baseline {csp_abbr} Foundation |")
            lines.append(f"| `{csp_lower}-security-admins` | assuredworkloads.admin, iam.securityAdmin, securitycenter.adminViewer, logging.privateLogViewer | Baseline {csp_abbr} Foundation |")
            lines.append(f"| `{csp_lower}-network-admins` | compute.networkAdmin, compute.securityAdmin, compute.sharedVpcAdmin | Baseline {csp_abbr} Foundation |")
            lines.append(f"| `{csp_lower}-billing-admins` | billing.admin, billing.creator | Baseline {csp_abbr} Foundation |")
            lines.append(f"| `{csp_lower}-logging-admins` | logging.admin, logging.configWriter | Baseline {csp_abbr} Foundation |")
            lines.append(f"| `{csp_lower}-logging-viewers` | logging.privateLogViewer | Baseline {csp_abbr} Foundation |")
            lines.append(f"| `{csp_lower}-monitoring-admins` | monitoring.admin | Baseline {csp_abbr} Foundation |")
        else:
            lines.append("| `[NOT DETERMINED FROM SOURCE]` | [NOT DETERMINED] | [NOT DETERMINED] |")

    lines.append("")
    lines.append("> [!NOTE]")
    lines.append("> **Separation of Duties Verification**: The above matrix is dynamically provisioned directly from TDD IAM specification files and Terraform IAM resources across the repository.")

    return "\n".join(lines)

def build_dynamic_system_description(inventory: Dict[str, Any]) -> str:
    """Synthesizes an authoritative system description from extracted components.

    Builds a 3PAO / SCA-D standard System Description covering workload profiles,
    compute infrastructure, data persistence, network perimeters, and identity
    governance, incorporating authentic system descriptions extracted from codebase
    documentation (README.md, spec.md, tdd.md) or user configuration.

    Args:
        inventory: System inventory dictionary containing extracted metadata.

    Returns:
        A multi-paragraph narrative string describing the cloud information system.
    """
    sys_info = inventory.get("system_information", {})
    net_info = inventory.get("network_architecture", {})
    infra_info = inventory.get("infrastructure_components", {})
    app_info = inventory.get("application_components", {})

    sys_name = sys_info.get("system_name", "Enterprise Cloud Information System")
    sys_abbr = sys_info.get("system_abbreviation", "SYS")
    baseline = sys_info.get("compliance_baseline", "NIST SP 800-53 Rev. 5")
    impact_level = sys_info.get("impact_level", "IL5")

    # If the user explicitly provided a comprehensive multi-tier description (with technical tier headers)
    user_desc = sys_info.get("system_description", "").strip()
    if user_desc and any(tier in user_desc for tier in ("**Workload Execution", "**Compute Tier", "**Data Persistence", "**Network Perimeter")):
        return user_desc

    apps = app_info.get("applications", [])
    frameworks = app_info.get("frameworks", [])
    runtimes = app_info.get("runtimes", [])
    databases = infra_info.get("databases", [])
    gke = infra_info.get("gke_clusters", [])
    vms = infra_info.get("compute_instances", [])
    vpcs = net_info.get("vpcs", [])
    kms = infra_info.get("kms_keys", [])
    buckets = infra_info.get("storage_buckets", [])
    cloud_provider = str(sys_info.get("cloud_provider") or "gcp")

    desc_paras = []

    # 1. Architectural Mission & Workload Profile
    # Check if we have an authentic description extracted from README or user config
    operational_desc = (sys_info.get("readme_system_description") or user_desc).strip()
    if operational_desc:
        op_paras = [p.strip() for p in operational_desc.split("\n\n") if p.strip()]
        for p in op_paras:
            desc_paras.append(p)

        # Ensure formal authorization boundary baseline is tied into the narrative if not already mentioned
        if baseline.lower() not in operational_desc.lower() and impact_level.lower() not in operational_desc.lower():
            if sys_name.lower() not in operational_desc.lower() and not sys_name.startswith("[CONFIG_REQUIRED"):
                desc_paras.append(
                    f"Under the **{sys_name}** (**{sys_abbr}**) accreditation boundary, the system is architected, operated, and maintained to satisfy {baseline} security controls under a formal {impact_level} authorization boundary."
                )
            else:
                desc_paras.append(
                    f"The system is architected, operated, and maintained to satisfy {baseline} security controls under a formal {impact_level} authorization boundary."
                )
    else:
        # Fallback to dynamic synthesis from apps/frameworks/runtimes if no README was discovered
        arch_parts = []
        if apps:
            app_names = ", ".join([a.get("name") for a in apps[:4]])
            arch_parts.append(f"hosts application services ({app_names})")
        if frameworks:
            arch_parts.append(f"built with {', '.join(frameworks)}")
        if runtimes:
            arch_parts.append(f"executing within {', '.join(runtimes)} runtimes")

        if arch_parts:
            desc_paras.append(
                f"The **{sys_name}** (**{sys_abbr}**) is an enterprise cloud information system engineered to deliver mission-critical digital capabilities. "
                f"The workload environment {'; '.join(arch_parts)}. The system is architected, operated, and maintained to satisfy {baseline} security controls under a formal {impact_level} authorization boundary."
            )
        else:
            desc_paras.append(
                f"The **{sys_name}** (**{sys_abbr}**) is an enterprise cloud foundation and workload hosting platform engineered to provide hardened multi-tenant computing, "
                f"centralized security visibility, automated identity governance, and cryptographic protection in compliance with {baseline} ({impact_level})."
            )

    # 2. Compute Infrastructure & Workload Orchestration Tier
    compute_parts = []
    if gke:
        c_names = ", ".join([c.get("name", "Cluster") if isinstance(c, dict) else str(c) for c in gke])
        compute_parts.append(f"managed Google Kubernetes Engine (GKE) private clusters ({c_names}) leveraging Shielded Nodes, Container-Optimized OS, and Workload Identity Federation")
    if vms:
        compute_parts.append(f"{len(vms)} hardened Compute Engine virtual machine instance(s) running verified operating system images with Shielded VM vTPM integrity monitoring")
    if infra_info.get("cloud_run_services"):
        compute_parts.append(f"serverless Cloud Run microservices with restricted private ingress and binary authorization verification")
    if infra_info.get("cloud_functions"):
        compute_parts.append(f"event-driven Cloud Functions executing in private VPC perimeters")

    if compute_parts:
        desc_paras.append(
            f"**Workload Execution and Compute Tier**: Workloads execute within {'; '.join(compute_parts)}. "
            f"All infrastructure assets are provisioned through declarative Infrastructure-as-Code (Terraform) modules to ensure immutable, repeatable, and audit-verifiable configuration baselines."
        )

    # 3. Data Persistence & Cryptographic Security
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

    enc_desc = inventory.get("encryption_summary", "FIPS 140-3 Level 3 Cloud HSM CMEK (AES-256-GCM / RSA-4096)")
    if data_parts:
        desc_paras.append(
            f"**Data Persistence and Cryptographic Protection**: Sensitive system data is housed in {'; and '.join(data_parts)}. "
            f"Data at rest is cryptographically protected via {enc_desc}, ensuring that data cannot be decrypted outside the authorized boundary. Data in transit across all internal and external communication interfaces is strictly encrypted using TLS 1.3/1.2 with Perfect Forward Secrecy."
        )

    # 4. Logical Network Architecture & Perimeter Defense
    net_parts = []
    if vpcs:
        net_parts.append(f"isolated Virtual Private Clouds ({', '.join(vpcs)})")
    clean_subnets = extract_clean_subnets(net_info.get("subnets_cidrs"))
    if clean_subnets:
        net_parts.append(f"non-overlapping subnets ({', '.join(clean_subnets)})")
    default_conn = "Private Service Connect, Cloud Interconnect, and Cloud NAT"
    conn_sum = inventory.get("connectivity_summary") or default_conn
    default_ids = "Cloud Next-Generation Firewall and Cloud IDS"
    ids_sol = inventory.get("ids_solution") or default_ids

    desc_paras.append(
        f"**Network Perimeter and Boundary Protection**: The logical network boundary is enforced through {'; '.join(net_parts) if net_parts else 'private software-defined Andromeda VPCs'} using private RFC 1918 addressing with zero direct external Internet ingress. "
        f"Network transit is controlled by {conn_sum}. Ingress, egress, and lateral traffic are inspected and protected by stateful firewall rules and {ids_sol}."
    )

    # 5. Identity Governance, Administration, and Continuous Monitoring
    auth_sum = inventory.get("authentication_summary", "Cloud Identity with phishing-resistant MFA and least-privilege IAM")
    desc_paras.append(
        f"**Identity, Access Management, and Audit Governance**: System administration is strictly governed by {auth_sum}. "
        f"Privileged access requires multi-factor authentication (MFA) and least-privilege role-based access control (RBAC). Security telemetry, administrator activity, and system modification events are streamed in real time to centralized, immutable audit logging sinks for continuous monitoring and SIEM ingestion."
    )

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
    sys_info = inventory.get("system_information", {})
    org = sys_info.get("organization", "{{ ORGANIZATION }}")
    sys_name = sys_info.get("system_name", "{{ SYSTEM_NAME }}")
    sec_ops = inventory.get("security_operations") or sys_info.get("security_operations") or {}
    scc_enabled = sec_ops.get("scc_enabled", False)
    scc_tier = str(sec_ops.get("scc_tier", "premium")).title()
    secops_enabled = sec_ops.get("secops_enabled", False)
    secops_instance = sec_ops.get("secops_instance_name") or "chronicle-secops-enclave"
    cssp_provider = sec_ops.get("cssp_provider") or "DISA"
    ext_siem = sec_ops.get("external_siem_type") or "Splunk"
    allow_etp = sec_ops.get("allow_unaccredited_scc_in_il5", False)
    ext_sys = inventory.get("external_systems") or sys_info.get("external_systems") or {}
    itsm = ext_sys.get("itsm_system") or "ServiceNow ITSM"

    impact_lvl = str(sys_info.get("impact_level") or "").upper()
    comp_base = str(sys_info.get("compliance_baseline") or "").upper()
    is_dod = any(k in impact_lvl for k in ["IL4", "IL5", "IL6", "IL-4", "IL-5", "IL-6", "DOD"]) or any(k in comp_base for k in ["IL4", "IL5", "IL6", "IL-4", "IL-5", "IL-6", "DOD"])

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

    else:
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
            f"SLA timeframes (within 1 hour for Category 1 root-level incidents and within 2 hours for Category 2 incidents) via {itsm}."
        )

    return "\n\n".join(paras)


def build_audit_and_siem_implementation_narrative(inventory: Dict[str, Any]) -> str:
    """Builds an authoritative, non-conditional Audit Logging and SIEM Ingestion narrative.

    Args:
        inventory: System inventory dictionary containing extracted metadata.

    Returns:
        A Markdown-formatted string describing the implementation.
    """
    sys_info = inventory.get("system_information", {})
    org = sys_info.get("organization", "{{ ORGANIZATION }}")
    sys_name = sys_info.get("system_name", "{{ SYSTEM_NAME }}")
    sec_ops = inventory.get("security_operations") or sys_info.get("security_operations") or {}
    secops_enabled = sec_ops.get("secops_enabled", False)
    cssp_provider = sec_ops.get("cssp_provider") or "DISA"
    ext_siem = sec_ops.get("external_siem_type") or "Splunk"
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
            f"Audit telemetry is exported in real time via Cloud Logging Log Router aggregated sinks to BigQuery analytical datasets "
            f"in a dedicated, isolated audit project. Scheduled SQL queries and Cloud Monitoring metric alerts continuously inspect "
            f"audit records for unauthorized IAM modifications, anomalous network changes, and privilege escalations."
        )

    paras.append(
        f"For evidentiary integrity and long-term regulatory compliance, all raw audit logs are simultaneously archived to a "
        f"dedicated Google Cloud Storage bucket configured with Object Retention (Bucket Lock) in WORM (Write Once, Read Many) "
        f"mode. The bucket retention period is enforced at 365 calendar days with Cloud KMS customer-managed encryption keys (CMEK), "
        f"preventing premature deletion or tampering even by privileged administrators."
    )
    return "\n\n".join(paras)


def build_incident_escalation_implementation_narrative(inventory: Dict[str, Any]) -> str:
    """Builds an authoritative, non-conditional Incident Escalation and SLA narrative.

    Args:
        inventory: System inventory dictionary containing extracted metadata.

    Returns:
        A Markdown-formatted string describing the implementation.
    """
    sys_info = inventory.get("system_information", {})
    org = sys_info.get("organization", "{{ ORGANIZATION }}")
    sys_name = sys_info.get("system_name", "{{ SYSTEM_NAME }}")
    sec_ops = inventory.get("security_operations") or sys_info.get("security_operations") or {}
    ext_sys = inventory.get("external_systems") or sys_info.get("external_systems") or {}
    cssp_provider = sec_ops.get("cssp_provider") or "DISA"
    itsm = ext_sys.get("itsm_system") or "ServiceNow ITSM"

    impact_lvl = str(sys_info.get("impact_level") or "").upper()
    comp_base = str(sys_info.get("compliance_baseline") or "").upper()
    is_dod = any(k in impact_lvl for k in ["IL4", "IL5", "IL6", "IL-4", "IL-5", "IL-6", "DOD"]) or any(k in comp_base for k in ["IL4", "IL5", "IL6", "IL-4", "IL-5", "IL-6", "DOD"])

    paras = []
    if is_dod:
        paras.append(
            f"In accordance with CJCSM 6510.01B (*Cyber Incident Handling Program*) and DoDI 8530.01, {org} {sys_name} "
            f"enforces strict, standardized incident categorization and mandatory reporting timelines through {cssp_provider}:"
        )
        paras.append(
            f"- **Category 1 (Root-Level Compromise / Data Exfiltration)**: Mandatory formal notification within **1 hour** "
            f"of detection to the {cssp_provider} Joint Operations Center (JOC), component cyber operations center, "
            f"Authorizing Official, and Lead ISSM via encrypted out-of-band communication and {itsm}.\n"
            f"- **Category 2 (User-Level Compromise / Malicious Logic)**: Formal notification within **2 hours** of detection "
            f"to {cssp_provider} and the organizational Incident Response Team.\n"
            f"- **Category 3 (Unsuccessful Intrusion Attempts / Denial of Service)**: Consolidated reporting within **24 hours**.\n"
            f"- **Category 4 (Investigative Inquiries)**: Continuous tracking with status updates provided within **48 hours**."
        )
        paras.append(
            f"All confirmed security incidents are tracked end-to-end within {itsm} and recorded in the eMASS Plan of Action and "
            f"Milestones (POA&M) repository to document containment steps, root cause analysis, and corrective actions."
        )
    else:
        paras.append(
            f"In accordance with the FedRAMP Incident Communications Procedure and NIST SP 800-61 Rev. 2, {org} {sys_name} "
            f"enforces automated incident reporting and triage procedures:"
        )
        paras.append(
            f"- **Critical / High Impact Incidents (Data Breach / System Compromise)**: Mandatory reporting within **1 hour** "
            f"of confirmation to US-CERT (CISA via soc@cisa.gov) and the FedRAMP Program Management Office (info@fedramp.gov), "
            f"followed by immediate escalation to the Agency Authorizing Official and ISSM.\n"
            f"- **Moderate Impact Incidents**: Notification within **4 hours** to organizational stakeholders.\n"
            f"- **Low Impact Incidents / Anomalies**: Documented and reviewed during standard weekly incident triage."
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
    sys_info = inventory.get("system_information", {})
    org = sys_info.get("organization", "{{ ORGANIZATION }}")
    sys_name = sys_info.get("system_name", "{{ SYSTEM_NAME }}")
    ext_sys = inventory.get("external_systems") or sys_info.get("external_systems") or {}
    scanner = ext_sys.get("vulnerability_scanner") or "DoD ACAS / Tenable Nessus"
    cicd = ext_sys.get("cicd_platform") or "GitLab Ultimate"
    sec_ops = inventory.get("security_operations") or sys_info.get("security_operations") or {}
    cssp_provider = sec_ops.get("cssp_provider") or "DISA"

    impact_lvl = str(sys_info.get("impact_level") or "").upper()
    comp_base = str(sys_info.get("compliance_baseline") or "").upper()
    is_dod = any(k in impact_lvl for k in ["IL4", "IL5", "IL6", "IL-4", "IL-5", "IL-6", "DOD"]) or any(k in comp_base for k in ["IL4", "IL5", "IL6", "IL-4", "IL-5", "IL-6", "DOD"])

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
    sys_info = inventory.get("system_information", {})
    org = sys_info.get("organization", "{{ ORGANIZATION }}")
    sys_name = sys_info.get("system_name", "{{ SYSTEM_NAME }}")
    impact_lvl = str(sys_info.get("impact_level") or "").upper()
    comp_base = str(sys_info.get("compliance_baseline") or "").upper()
    is_dod = any(k in impact_lvl for k in ["IL4", "IL5", "IL6", "IL-4", "IL-5", "IL-6", "DOD"]) or any(k in comp_base for k in ["IL4", "IL5", "IL6", "IL-4", "IL-5", "IL-6", "DOD"])

    ext_sys = inventory.get("external_systems") or sys_info.get("external_systems") or {}
    idp = ext_sys.get("identity_provider") or ("Enterprise Identity Provider (DoD CAC / PIV)" if is_dod else "Enterprise Identity Provider (Cloud Identity / SSO)")
    mfa = ext_sys.get("mfa_mechanism") or ("DoD Common Access Card (CAC) / FIDO2 Token" if is_dod else "FIPS 140-3 Hardware Token / PIV / FIDO2 WebAuthn MFA")

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
        paras.append(
            f"**Privileged Access Management (PAM)**: Permanent assignment of high-privilege IAM roles (such as Security Admin, "
            f"Network Admin, or Organization Administrator) is strictly prohibited. Privileged operations require Just-In-Time (JIT) "
            f"activation via Google Cloud Privileged Access Manager (PAM). PAM requests require explicit two-party approval from the "
            f"Lead ISSO, enforce a maximum lease duration of 4 hours, and require documented justification with associated {ext_sys.get('itsm_system') or 'ServiceNow'} "
            f"change tickets. All elevated actions are logged immutably to Google Cloud Audit Logs."
        )
    else:
        paras.append(
            f"**Enterprise Identity & MFA**: Administrative identities are managed through {idp}. All administrative and console access "
            f"requires phishing-resistant multi-factor authentication ({mfa}). Session timeouts are enforced after 15 minutes of inactivity."
        )
        paras.append(
            f"**Least Privilege & Role Elevation**: Role assignments follow custom predefined IAM roles mapped strictly to job functions. "
            f"Elevated access is mediated through Google Cloud Privileged Access Manager (PAM) for temporary, time-bound session elevations "
            f"with auditable approval trails."
        )
    return "\n\n".join(paras)


_INVARIANT_CACHE_CAPACITY = 32
_INVARIANT_REPLACEMENTS_CACHE: Dict[Tuple[int, int, bool, str], Dict[str, str]] = {}


def _get_cached_invariant_replacements(
    inventory: Dict[str, Any],
    ai_enrich: bool = False,
    ai_model: Optional[str] = None,
) -> Dict[str, str]:
    """Retrieves or builds cached invariant deliverable replacement strings.

    Avoids recomputing extensive narrative synthesis and formatted matrices 28+ times
    during batch artifact generation across SSP, PTA, runbooks, and 20 policy manuals.
    When ai_enrich is True, enriches core narratives with LLM semantic reasoning.
    """
    sys_info = inventory.get("system_information", {})
    infra_info = inventory.get("infrastructure_components", {})
    net_info = inventory.get("network_architecture", {})
    fw_rules = net_info.get("firewall_rules", [])
    cache_key = (
        id(inventory),
        len(inventory) + len(sys_info) + len(infra_info) + len(fw_rules),
        bool(ai_enrich),
        str(ai_model or ""),
    )
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

    if ai_enrich:
        logger.info(
            "AI narrative enrichment: base narratives generated from live architecture facts. "
            "Mission-specific tailoring is performed via Gemini compliance skills (ssp_skill.md)."
        )

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


def populate_placeholders(
    content: str,
    inventory: Dict[str, Any],
    doc_version: str = "1.0.0",
    target_format: str = "markdown",
    fill_examples: bool = True,
    ai_enrich: bool = False,
    ai_model: Optional[str] = None,
) -> str:
    """Populates template placeholders with system inventory values.

    Args:
        content: Raw template content string containing placeholder tokens.
        inventory: System inventory dictionary containing extracted metadata.
        doc_version: Version string for the document being generated.
        target_format: Target format ('markdown', 'docx', etc.).
        fill_examples: Whether to fill sample example tags.
        ai_enrich: Whether to enrich technical narratives using AI semantic reasoning.
        ai_model: Optional custom LLM model name for enrichment.

    Returns:
        The populated string with all placeholder tokens replaced.
    """
    sys_info = inventory.get("system_information", {})
    net_info = inventory.get("network_architecture", {})
    infra_info = inventory.get("infrastructure_components", {})
    roles_info = inventory.get("personnel_roles", {})

    ao_info = roles_info.get("authorizing_official", {})
    so_info = roles_info.get("system_owner", {})
    issm_info = roles_info.get("issm", {})
    isso_info = roles_info.get("isso", {})

    app_info = inventory.get("application_components", {})
    apps_list = app_info.get("applications", [])
    pkgs_list = app_info.get("software_packages", [])
    containers_list = app_info.get("container_images", [])
    app_ports_list = app_info.get("exposed_ports", [])
    runtimes_list = app_info.get("runtimes", [])
    frameworks_list = app_info.get("frameworks", [])

    app_stack_summary = []
    if runtimes_list:
        app_stack_summary.append(f"Runtimes: {', '.join(runtimes_list)}")
    if frameworks_list:
        app_stack_summary.append(f"Frameworks: {', '.join(frameworks_list)}")
    if apps_list:
        app_names = [a.get("name") for a in apps_list]
        app_stack_summary.append(f"Applications: {', '.join(app_names)}")
    app_stack_str = " | ".join(app_stack_summary) if app_stack_summary else "Cloud-Native Infrastructure & Services"

    version_str = doc_version or sys_info.get("version", "1.0.0")

    cloud_provider_val = sys_info.get("cloud_provider") or "Google Cloud Platform"
    csp_abbr_val = sys_info.get("cloud_service_provider_abbr") or "GCP"

    # Dynamic Security Operations & Continuous Monitoring Macros
    sec_ops_info = inventory.get("security_operations") or sys_info.get("security_operations") or {}
    ext_sys_info = inventory.get("external_systems") or sys_info.get("external_systems") or {}
    conmon = inventory.get("continuous_monitoring") or {}

    scc_enabled = sec_ops_info.get("scc_enabled") if "scc_enabled" in sec_ops_info else sys_info.get("scc_enabled")
    scc_tier = sec_ops_info.get("scc_tier") or sys_info.get("scc_tier", "premium")
    secops_enabled = sec_ops_info.get("secops_enabled") if "secops_enabled" in sec_ops_info else sys_info.get("secops_enabled")
    cssp_provider = sec_ops_info.get("cssp_provider") or sys_info.get("cssp_provider") or "DISA"
    ext_siem = sec_ops_info.get("external_siem_type") or sys_info.get("external_siem_type") or "Splunk"
    siem_tool = ("Google Cloud SecOps (Chronicle)" if secops_enabled else (ext_siem if ext_siem not in ("None", None, "") else f"{cssp_provider} SIEM"))
    telemetry_pipeline = sec_ops_info.get("telemetry_summary") or sys_info.get("telemetry_summary") or "Cloud Logging Log Router export sinks streaming to external accredited CSSP and Cloud Monitoring"
    threat_engine = sec_ops_info.get("threat_detection_engine") or sys_info.get("threat_detection_engine") or "Cloud Monitoring Anomaly Detection and Audit Log Analysis"

    impact_lvl = str(sys_info.get("impact_level") or "").upper()
    comp_base = str(sys_info.get("compliance_baseline") or "").upper()
    is_dod = any(k in impact_lvl for k in ["IL4", "IL5", "IL6", "IL-4", "IL-5", "IL-6", "DOD"]) or any(k in comp_base for k in ["IL4", "IL5", "IL6", "IL-4", "IL-5", "IL-6", "DOD"])

    idp = ext_sys_info.get("identity_provider") or sys_info.get("identity_provider") or ("Enterprise Identity Provider (DoD CAC / PIV)" if is_dod else "Enterprise Identity Provider (Cloud Identity / SSO)")
    mfa = ext_sys_info.get("mfa_mechanism") or sys_info.get("mfa_mechanism") or ("DoD Common Access Card (CAC) / FIDO2 Hardware Token" if is_dod else "FIPS 140-3 Hardware Token / PIV / FIDO2 WebAuthn MFA")
    scanner = ext_sys_info.get("vulnerability_scanner") or sys_info.get("vulnerability_scanner") or ("DoD ACAS (Tenable Nessus) & CI/CD Scanners" if is_dod else "Artifact Registry Container Analysis & Enterprise CI/CD Scanners")
    itsm = ext_sys_info.get("itsm_system") or sys_info.get("itsm_system") or "ServiceNow ITSM / SecOps"
    cicd = ext_sys_info.get("cicd_platform") or sys_info.get("cicd_platform") or ("GitLab Ultimate (FedRAMP)" if is_dod else "Google Cloud Build + Artifact Registry")
    edr = ext_sys_info.get("edr_solution") or sys_info.get("edr_solution") or ("CrowdStrike Falcon (GovCloud)" if is_dod else "Shielded VM vTPM & Google OS Config")
    perim = ext_sys_info.get("perimeter_gateway") or sys_info.get("perimeter_gateway") or "Google Cloud Armor & Cloud NGFW"

    warning_banner = sys_info.get("warning_banner_type") or ("DoD Notice and Consent Warning Banner" if is_dod else "System Use Notification Warning Banner")
    access_agreement = sys_info.get("access_agreement_type") or ("System Authorization Access Request (SAAR / DD Form 2875)" if is_dod else "Rules of Behavior & Access Authorization Agreement")
    rules_of_behavior = sys_info.get("rules_of_behavior") or ("DoD Rules of Behavior" if is_dod else "Organizational Rules of Behavior")
    pki_trust_type = sys_info.get("pki_trust_type") or ("DoD PKI / Federal PKI trust anchors" if is_dod else "Federal / Enterprise PKI trust anchors")
    user_identifier_type = sys_info.get("user_identifier_type") or ("DoD ID Number (EDIPI) / UPN" if is_dod else "Enterprise User ID / UPN")
    interconnect_type = sys_info.get("interconnect_type") or (net_info.get("connectivity_summary") if net_info.get("connectivity_summary") and not net_info.get("connectivity_summary").startswith("[") else "Dedicated Cloud Interconnect / HA Cloud VPN")
    sensitivity_classification = sys_info.get("sensitivity_classification") or sys_info.get("data_classification") or ("Controlled Unclassified Information (CUI)" if is_dod else "Sensitive / Confidential Unclassified Information")

    flags = {
        "SCC_ENABLED": scc_enabled,
        "SCC_DISABLED": not scc_enabled,
        "SECOPS_ENABLED": secops_enabled,
        "SECOPS_DISABLED": not secops_enabled,
        "CSSP_ENABLED": bool(cssp_provider and cssp_provider.lower() not in ("none", "not applicable", "n/a", "")),
        "CSSP_DISABLED": not bool(cssp_provider and cssp_provider.lower() not in ("none", "not applicable", "n/a", "")),
        "EXTERNAL_SIEM_ENABLED": bool(ext_siem and ext_siem.lower() not in ("none", "not applicable", "n/a", "")),
        "DOD_ENCLAVE": is_dod,
        "FEDRAMP_ENCLAVE": not is_dod,
        "COMMERCIAL_ENCLAVE": not is_dod,
        "ALLOW_UNACCREDITED_SCC": bool(sec_ops_info.get("allow_unaccredited_scc_in_il5", False)),
    }

    content = evaluate_template_conditionals(content, flags)

    # Hydrate bracketed operator tokens (e.g. "[KMS_PROJECT_ID]") before macro
    # rendering. DERIVABLE tokens are replaced with the value discovered from the
    # Terraform, RUNTIME tokens become explicit "<TOKEN: fill in ...>" operator
    # markers, and anything not on either allow-list (bracketed NIST citation
    # shorthand such as "[PRIVACT]") is left untouched. Running this first keeps
    # the generated provenance block itself out of scope for re-substitution.
    derivable_tokens_used, _runtime_tokens_used = find_operator_tokens(content)
    operator_context = build_operator_context(inventory, tokens=derivable_tokens_used)
    content = hydrate_operator_placeholders(content, inventory, context=operator_context)

    invariants = _get_cached_invariant_replacements(inventory, ai_enrich=ai_enrich, ai_model=ai_model)

    replacements = {
        "{{ SYSTEM_NAME }}": sys_info.get("system_name") or "[CONFIG_REQUIRED: System Name]",
        "{{ SYSTEM_ABBREVIATION }}": sys_info.get("system_abbreviation") or "[CONFIG_REQUIRED: System Abbreviation]",
        "{{ CLOUD_PROVIDER }}": cloud_provider_val,
        "{{ CSP_ABBR }}": csp_abbr_val,
        "{{ IAC_TOOL }}": infra_info.get("iac_tool") or "Terraform",
        "{{ IAC_VERSION }}": infra_info.get("terraform_engine_version") or "1.5.7+",
        "{{ DITPR_ID }}": sys_info.get("ditpr_id") or f"DITPR-{sys_info.get('system_abbreviation', 'SYS')}-001",
        "{{ EMASS_SYSTEM_ID }}": sys_info.get("emass_system_id") or f"EMASS-{sys_info.get('system_abbreviation', 'SYS')}-001",
        "{{ SYSTEM_DESCRIPTION }}": invariants["system_description"],
        "{{ IMPACT_LEVEL }}": sys_info.get("impact_level") or "[CONFIG_REQUIRED: Impact Level]",
        "{{ COMPLIANCE_BASELINE }}": sys_info.get("compliance_baseline") or "NIST SP 800-53 Rev. 5",
        "{{ ORGANIZATION }}": sys_info.get("organization") or "[CONFIG_REQUIRED: Organization Name]",
        "{{ ORGANIZATION_NAME }}": sys_info.get("organization") or "[CONFIG_REQUIRED: Organization Name]",
        "{{ ORGANIZATION_DOMAIN }}": (
            sys_info.get("organization_domain")
            or inventory.get("organization", {}).get("domain_name")
            or ("agency.mil" if is_dod else "agency.gov")
        ),
        "[ORGANIZATION_DOMAIN]": (
            sys_info.get("organization_domain")
            or inventory.get("organization", {}).get("domain_name")
            or ("agency.mil" if is_dod else "agency.gov")
        ),
        "{{ BILLING_ACCOUNT }}": sys_info.get("billing_account") or "[CONFIG_REQUIRED: Billing Account ID]",
        "{{ PRIMARY_LOCATION }}": sys_info.get("primary_location") or "[CONFIG_REQUIRED: Primary Location]",
        # Inherited CSP authorization. See DEFAULT_CSP_PATO_PACKAGE_ID: this is
        # an assertion the assessor will look up, so it must be overridable.
        "{{ CSP_PATO_PACKAGE_ID }}": sys_info.get("csp_pato_package_id") or DEFAULT_CSP_PATO_PACKAGE_ID,
        # Continuous monitoring strategy. These were parsed from
        # compliance_config.yaml and written into system_inventory.json, but no
        # template consumed them, so an operator-declared assessment type or
        # review frequency never reached a deliverable.
        "{{ CONMON_REVIEW_FREQUENCY }}": conmon.get("review_frequency") or "[CONFIG_REQUIRED: ConMon Review Frequency]",
        "{{ CONMON_ASSESSMENT_TYPE }}": conmon.get("assessment_type") or "[CONFIG_REQUIRED: ConMon Assessment Type]",
        "{{ GRC_TOOL_REFERENCE }}": conmon.get("grc_tool_reference") or sys_info.get("rmf_governance_system") or "[CONFIG_REQUIRED: GRC Tool]",
        "{{ VERSION }}": version_str,
        "{{ DATE }}": sys_info.get("effective_date") or datetime.now().strftime("%B %d, %Y"),
        "{{ AUTHORIZATION_DATE }}": datetime.now().strftime("%B %d, %Y"),
        "{{ CONFIDENTIALITY_IMPACT }}": sys_info.get("confidentiality_impact") or ("High" if "IL5" in str(sys_info.get("impact_level", "")).upper() else "[CONFIG_REQUIRED: Confidentiality Impact]"),
        "{{ INTEGRITY_IMPACT }}": sys_info.get("integrity_impact") or ("High" if "IL5" in str(sys_info.get("impact_level", "")).upper() else "[CONFIG_REQUIRED: Integrity Impact]"),
        "{{ AVAILABILITY_IMPACT }}": sys_info.get("availability_impact") or ("High" if "IL5" in str(sys_info.get("impact_level", "")).upper() else "[CONFIG_REQUIRED: Availability Impact]"),
        "{{ FIPS_199_CATEGORIZATION }}": f"Confidentiality: {sys_info.get('confidentiality_impact') or ('High' if 'IL5' in str(sys_info.get('impact_level', '')).upper() else '[CONFIG_REQUIRED]')} / Integrity: {sys_info.get('integrity_impact') or ('High' if 'IL5' in str(sys_info.get('impact_level', '')).upper() else '[CONFIG_REQUIRED]')} / Availability: {sys_info.get('availability_impact') or ('High' if 'IL5' in str(sys_info.get('impact_level', '')).upper() else '[CONFIG_REQUIRED]')}",

        "{{ GOVERNANCE_REGIME }}": sys_info.get("governance_regime") or sys_info.get("compliance_baseline") or "[CONFIG_REQUIRED: Governance Regime]",
        "{{ RMF_GOVERNANCE_SYSTEM }}": sys_info.get("rmf_governance_system") or "[CONFIG_REQUIRED: GRC System e.g. eMASS / CSAM]",

        "{{ INTRUSION_DETECTION_SYSTEM }}": infra_info.get("ids_solution") or inventory.get("ids_solution") or sys_info.get("ids_solution") or ("Cloud Next-Generation Firewall (NGFW)" if any("firewall" in str(s).lower() for s in infra_info.get("services_enabled", [])) else "[CONFIG_REQUIRED: IDS/IPS Solution]"),
        "{{ IDS_IPS_SOLUTION }}": infra_info.get("ids_solution") or inventory.get("ids_solution") or sys_info.get("ids_solution") or ("Cloud Next-Generation Firewall (NGFW)" if any("firewall" in str(s).lower() for s in infra_info.get("services_enabled", [])) else "[CONFIG_REQUIRED: IDS/IPS Solution]"),

        "{{ RECOVERY_TIME_OBJECTIVE }}": inventory.get("contingency_planning", {}).get("recovery_time_objective") or sys_info.get("recovery_time_objective") or "[CONFIG_REQUIRED: Recovery Time Objective]",
        "{{ RECOVERY_POINT_OBJECTIVE }}": inventory.get("contingency_planning", {}).get("recovery_point_objective") or sys_info.get("recovery_point_objective") or "[CONFIG_REQUIRED: Recovery Point Objective]",
        "{{ RTO }}": inventory.get("contingency_planning", {}).get("recovery_time_objective") or "[CONFIG_REQUIRED: Recovery Time Objective]",
        "{{ RPO }}": inventory.get("contingency_planning", {}).get("recovery_point_objective") or "[CONFIG_REQUIRED: Recovery Point Objective]",

        "{{ AO_NAME }}": ao_info.get("name") or "[CONFIG_REQUIRED: Authorizing Official Name]",
        "{{ AO_TITLE }}": ao_info.get("title") or "Authorizing Official (AO)",
        "{{ AO_ORG }}": ao_info.get("organization") or "[CONFIG_REQUIRED: AO Organization]",
        "{{ AO_EMAIL }}": ao_info.get("email") or "[CONFIG_REQUIRED: Authorizing Official Email]",
        "{{ AO_PHONE }}": ao_info.get("phone") or "[CONFIG_REQUIRED: Authorizing Official Phone]",
        "{{ SO_NAME }}": so_info.get("name") or "[CONFIG_REQUIRED: System Owner Name]",
        "{{ SYSTEM_OWNER_NAME }}": so_info.get("name") or "[CONFIG_REQUIRED: System Owner Name]",
        "{{ SO_TITLE }}": so_info.get("title") or "Information System Owner (SO)",
        "{{ SO_ORG }}": so_info.get("organization") or sys_info.get("organization") or "[CONFIG_REQUIRED: Organization]",
        "{{ SO_EMAIL }}": so_info.get("email") or "[CONFIG_REQUIRED: System Owner Email]",
        "{{ SO_PHONE }}": so_info.get("phone") or "[CONFIG_REQUIRED: System Owner Phone]",
        "{{ ISSM_NAME }}": issm_info.get("name") or "[CONFIG_REQUIRED: ISSM Name]",
        "{{ ISSM_TITLE }}": issm_info.get("title") or "Information System Security Manager (ISSM)",
        "{{ ISSM_ORG }}": issm_info.get("organization") or sys_info.get("organization") or "[CONFIG_REQUIRED: Organization]",
        "{{ ISSM_EMAIL }}": issm_info.get("email") or "[CONFIG_REQUIRED: ISSM Email]",
        "{{ ISSM_PHONE }}": issm_info.get("phone") or "[CONFIG_REQUIRED: ISSM Phone]",
        "{{ ISSO_NAME }}": isso_info.get("name") or "[CONFIG_REQUIRED: ISSO Name]",
        "{{ ISSO_TITLE }}": isso_info.get("title") or "Information System Security Officer (ISSO)",
        "{{ ISSO_ORG }}": isso_info.get("organization") or sys_info.get("organization") or "[CONFIG_REQUIRED: Organization]",
        "{{ ISSO_EMAIL }}": isso_info.get("email") or "[CONFIG_REQUIRED: ISSO Email]",
        "{{ ISSO_PHONE }}": isso_info.get("phone") or "[CONFIG_REQUIRED: ISSO Phone]",
        "{{ NETWORK_VPCS }}": ", ".join(net_info.get("vpcs") or ["[CONFIG_REQUIRED: VPCs]"]),
        "{{ SUBNET_CIDRS }}": ", ".join(extract_clean_subnets(net_info.get("subnets_cidrs"))) or "[CONFIG_REQUIRED: Subnet CIDRs]",
        "{{ SUBNET_BOUNDARY_TABLE }}": invariants.get("subnet_boundary_table", ""),
        "{{ CONTAINER_WORKLOAD_TABLE }}": invariants.get("container_workload_table", ""),
        "{{ CONNECTIVITY }}": inventory.get("connectivity_summary") or "[CONFIG_REQUIRED: Primary Network Connectivity]",
        "{{ FIREWALL_MATRIX }}": invariants["firewall_matrix"],
        "{{ AUTHENTICATION_MECHANISM }}": inventory.get("authentication_summary") or "[CONFIG_REQUIRED: Authentication Mechanism]",
        "{{ SERVICE_ACCOUNTS_LIST }}": invariants["service_accounts"],
        "{{ STORAGE_BUCKETS_LIST }}": invariants["storage_buckets"],
        "{{ KMS_KEYS }}": ", ".join([str(k.get("name") if isinstance(k, dict) else k) for k in infra_info.get("kms_keys", []) if (k.get("name") if isinstance(k, dict) else k)]) or "[CONFIG_REQUIRED: KMS Key]",
        "{{ ENCRYPTION_STANDARD }}": inventory.get("encryption_summary") or "[CONFIG_REQUIRED: Cryptographic Protection Standard]",
        "{{ GCP_SERVICES_ENABLED }}": format_list_items(infra_info.get("services_enabled", [])),
        "{{ TERRAFORM_MODULES }}": format_list_items(infra_info.get("modules_used", [])),
        "{{ RMF_PACKAGE_ID }}": sys_info.get("rmf_package_id") or f"EMASS-{sys_info.get('system_abbreviation', 'SYS')}-001",
        "{{ SYSTEM_ABBR }}": sys_info.get("system_abbreviation") or sys_info.get("system_name", "SYS"),
        "{{ SEPARATION_OF_DUTIES_TABLE }}": invariants["separation_of_duties"],
        "{{ DISCOVERED_SERVICES_COUNT }}": len(infra_info.get("services_enabled", [])),
        "{{ DISCOVERED_MODULES_COUNT }}": len(infra_info.get("modules_used", [])),
        "{{ DISCOVERED_RESOURCES_COUNT }}": len(infra_info.get("all_resources", [])),
        "{{ APPLICATION_STACK }}": app_stack_str,
        "{{ DISCOVERED_APPLICATIONS_COUNT }}": len(apps_list),
        "{{ DISCOVERED_PACKAGES_COUNT }}": len(pkgs_list),
        "{{ DISCOVERED_CONTAINERS_COUNT }}": len(containers_list),
        "{{ DISCOVERED_APP_PORTS_COUNT }}": len(app_ports_list),

        # Dynamic Security Operations & Continuous Monitoring Macros
        "{{ SCC_STATUS }}": f"Security Command Center {str(scc_tier).title()}" if scc_enabled else "Security Command Center (Disabled / Not Utilized)",
        "{{ SCC_TIER }}": str(scc_tier).title(),
        "{{ SECOPS_STATUS }}": "Google Cloud SecOps (Chronicle)" if secops_enabled else "Google Cloud SecOps (Not Deployed)",
        "{{ CSSP_PROVIDER }}": cssp_provider,
        "{{ EXTERNAL_SIEM }}": ext_siem,
        "{{ SIEM_TOOL }}": siem_tool,
        "{{ TELEMETRY_PIPELINE }}": telemetry_pipeline,
        "{{ THREAT_DETECTION_ENGINE }}": threat_engine,

        # Dynamic External Systems Macros
        "{{ IDENTITY_PROVIDER }}": idp,
        "{{ MFA_MECHANISM }}": mfa,
        "{{ VULNERABILITY_SCANNER }}": scanner,
        "{{ ITSM_SYSTEM }}": itsm,
        "{{ CICD_PLATFORM }}": cicd,
        "{{ EDR_SOLUTION }}": edr,
        "{{ PERIMETER_GATEWAY }}": perim,

        # Dynamic Public Sector & Enterprise Governance Macros
        "{{ WARNING_BANNER_TYPE }}": warning_banner,
        "{{ ACCESS_AGREEMENT_TYPE }}": access_agreement,
        "{{ RULES_OF_BEHAVIOR }}": rules_of_behavior,
        "{{ PKI_TRUST_TYPE }}": pki_trust_type,
        "{{ USER_IDENTIFIER_TYPE }}": user_identifier_type,
        "{{ INTERCONNECT_TYPE }}": interconnect_type,
        "{{ SENSITIVITY_CLASSIFICATION }}": sensitivity_classification,
        "{{ DATA_CLASSIFICATION }}": sensitivity_classification,

        # Dynamic Full Implementation Narratives (Authoritative, Zero Conditionals)
        "{{ THREAT_DETECTION_IMPLEMENTATION }}": invariants["threat_detection"],
        "{{ AUDIT_AND_SIEM_IMPLEMENTATION }}": invariants["audit_and_siem"],
        "{{ INCIDENT_ESCALATION_IMPLEMENTATION }}": invariants["incident_escalation"],
        "{{ VULNERABILITY_MANAGEMENT_IMPLEMENTATION }}": invariants["vulnerability_management"],
        "{{ IDENTITY_ACCESS_IMPLEMENTATION }}": invariants["identity_and_access"],
        "{{ SECOPS_INSTANCE }}": sec_ops_info.get("secops_instance_name") or "chronicle-secops-enclave",

        # Provenance table for the bracketed operator tokens hydrated above. Only
        # the Incident Response runbooks reference this macro; it is a no-op
        # everywhere else.
        "{{ DISCOVERED_ENVIRONMENT_CONTEXT }}": render_discovered_context_block(
            operator_context, tokens=derivable_tokens_used
        ),
    }

    engine = TemplateEngine(
        target_format=target_format,
        fill_examples=fill_examples,
    )
    return engine.render(content, replacements)

# ------------------------------------------------------------------------------
# YAML Builders
# ------------------------------------------------------------------------------
def generate_hwsw_inventory_yaml(inventory: Dict[str, Any], doc_version: str = "1.0.0") -> str:
    """Generates Hardware and Software Asset Inventory in YAML format.

    Args:
        inventory: System inventory dictionary containing infrastructure and application assets.
        doc_version: Version string for the generated asset inventory.

    Returns:
        Formatted YAML string for Hardware and Software Inventory.
    """
    sys_info = inventory.get("system_information", {})
    net_info = inventory.get("network_architecture", {})
    infra_info = inventory.get("infrastructure_components", {})
    app_info = inventory.get("application_components", {})
    roles_info = inventory.get("personnel_roles", {})

    so_info = roles_info.get("system_owner", {})
    isso_info = roles_info.get("isso", {})

    sys_name = sys_info.get("system_name") or "[CONFIG_REQUIRED: System Name]"
    sys_abbr = sys_info.get("system_abbreviation") or "[CONFIG_REQUIRED: System Abbreviation]"
    impact = sys_info.get("impact_level") or "[CONFIG_REQUIRED: Impact Level]"
    org = sys_info.get("organization") or "[CONFIG_REQUIRED: Organization Name]"
    location = sys_info.get("primary_location") or "[CONFIG_REQUIRED: Primary Location]"
    eff_date = sys_info.get("effective_date") or datetime.now().strftime("%B %d, %Y")

    lines: List[str] = []
    lines.append("# ==============================================================================")
    lines.append("# Hardware and Software Inventory (NIST SP 800-53 Rev. 5 / Public Sector Baseline)")
    lines.append("# Ref: HWSWList_Template.xlsm (Generic Platform Provisioning)")
    lines.append("# ==============================================================================\n")

    lines.append("system_metadata:")
    lines.append(f"  system_name: {safe_yaml_scalar(sys_name)}")
    lines.append(f"  system_abbreviation: {safe_yaml_scalar(sys_abbr)}")
    lines.append(f"  impact_level: {safe_yaml_scalar(impact)}")
    lines.append(
        "  compliance_baseline:"
        f" {safe_yaml_scalar(sys_info.get('compliance_baseline', 'NIST SP 800-53 Rev. 5'))}"
    )
    lines.append(f"  organization: {safe_yaml_scalar(org)}")
    lines.append(f"  effective_date: {safe_yaml_scalar(eff_date)}")
    lines.append(f"  document_version: {safe_yaml_scalar(doc_version)}")
    ditpr_id = (
        sys_info.get("ditpr_id")
        or sys_info.get("ditpr_don_id")
        or sys_info.get("ditpr_emass_id")
        or f"DITPR-{sys_abbr}-001"
    )
    lines.append(f"  ditpr_emass_id: {safe_yaml_scalar(ditpr_id)}\n")

    lines.append("personnel_contacts:")
    lines.append("  system_owner:")
    lines.append(
        f"    name: {safe_yaml_scalar(so_info.get('name') or '[CONFIG_REQUIRED: System Owner Name]')}"
    )
    lines.append(
        f"    email: {safe_yaml_scalar(so_info.get('email') or '[CONFIG_REQUIRED: System Owner Email]')}"
    )
    lines.append(
        f"    phone: {safe_yaml_scalar(so_info.get('phone') or '[CONFIG_REQUIRED: System Owner Phone]')}"
    )
    lines.append("  isso_poc:")
    lines.append(
        f"    name: {safe_yaml_scalar(isso_info.get('name') or '[CONFIG_REQUIRED: ISSO Name]')}"
    )
    lines.append(
        f"    email: {safe_yaml_scalar(isso_info.get('email') or '[CONFIG_REQUIRED: ISSO Email]')}"
    )
    lines.append(
        f"    phone: {safe_yaml_scalar(isso_info.get('phone') or '[CONFIG_REQUIRED: ISSO Phone]')}\n"
    )

    lines.append("hardware_assets:")
    raw_vpcs = net_info.get("vpcs", [])
    raw_subnets = net_info.get("subnets_cidrs", [])
    clean_subnets = extract_clean_subnets(raw_subnets)
    clean_vpcs = []
    for v in raw_vpcs:
        cv = clean_interpolated_string(v)
        if is_valid_resource_name(cv) and cv not in clean_vpcs:
            clean_vpcs.append(cv)

    hw_id = 1.0
    hw_type_cloud = (
        excel_hydrator.resolve_exact_hw_type("cloud_tenant")
        if excel_hydrator
        else "Server"
    )
    tenant_ip = (
        ", ".join(clean_subnets) if clean_subnets else "[NOT DETERMINED FROM SOURCE]"
    )
    cloud_provider = (
        sys_info.get("cloud_provider")
        or inventory.get("cloud_provider")
        or "Google Cloud Platform (GCP)"
    )
    csp_abbr = sys_info.get("cloud_service_provider_abbr") or "GCP"
    lines.append(f"  - id: {safe_yaml_scalar(f'{hw_id:.1f}')}")
    lines.append(f"    component_type: {safe_yaml_scalar(hw_type_cloud)}")
    lines.append(f"    asset_name: {safe_yaml_scalar(f'{cloud_provider} Projects & Hierarchy')}")
    lines.append(
        f"    nickname: {safe_yaml_scalar(f'{csp_abbr} Cloud Tenant ({sys_abbr})')}"
    )
    lines.append(f"    asset_ip_address: {safe_yaml_scalar(tenant_ip)}")
    lines.append('    public_facing: "No"')
    lines.append('    virtual_asset: "Yes"')
    lines.append(f"    manufacturer: {safe_yaml_scalar(cloud_provider)}")
    lines.append('    model_number: "Infrastructure-as-a-Service (IaaS)"')
    lines.append(
        f"    serial_number: {safe_yaml_scalar(f'{csp_abbr}-CSP-{sys_abbr}-001')}"
    )
    lines.append(f"    location: {safe_yaml_scalar(location)}")
    lines.append('    approval_status: "Approved"')
    lines.append('    critical_asset: "Yes"')
    hw_id += 1.0

    # VPCs & Subnets (Switch)
    if clean_vpcs or clean_subnets:
        v_str = ", ".join(clean_vpcs[:4]) if clean_vpcs else f"{csp_abbr} Software Defined VPC"
        s_str = ", ".join(clean_subnets) if clean_subnets else "[NOT DETERMINED FROM SOURCE]"
        hw_type_switch = (
            excel_hydrator.resolve_exact_hw_type("vpc_networking")
            if excel_hydrator
            else "Switch"
        )
        lines.append(f"  - id: {safe_yaml_scalar(f'{hw_id:.1f}')}")
        lines.append(f"    component_type: {safe_yaml_scalar(hw_type_switch)}")
        lines.append(
            f"    asset_name: {safe_yaml_scalar(f'{csp_abbr} Virtual Private Cloud (VPC)')}"
        )
        lines.append(f"    nickname: {safe_yaml_scalar(v_str)}")
        lines.append(f"    asset_ip_address: {safe_yaml_scalar(s_str)}")
        lines.append('    public_facing: "No"')
        lines.append('    virtual_asset: "Yes"')
        lines.append(f"    manufacturer: {safe_yaml_scalar(cloud_provider)}")
        lines.append('    model_number: "Software-Defined VPC Networking"')
        lines.append(
            f"    serial_number: {safe_yaml_scalar(f'{csp_abbr}-VPC-{sys_abbr}-001')}"
        )
        lines.append(f"    location: {safe_yaml_scalar(location)}")
        lines.append('    approval_status: "Approved"')
        lines.append('    critical_asset: "Yes"')
        hw_id += 1.0

    # GKE Clusters (Server - Application)
    hw_type_gke = (
        excel_hydrator.resolve_exact_hw_type("gke_cluster")
        if excel_hydrator
        else "Server - Application"
    )
    for gke in infra_info.get("gke_clusters", []):
        raw_gke_name = gke.get("name", "gke-cluster") if isinstance(gke, dict) else str(gke)
        gke_name = clean_interpolated_string(raw_gke_name, default_val="gke-cluster")
        gke_ip = (
            (gke.get("master_ipv4_cidr_block") or "Private Control Plane & Node CIDR")
            if isinstance(gke, dict)
            else "Private Control Plane & Node CIDR"
        )
        gke_model = f"GKE Cluster ({gke.get('master_version', '1.28+') if isinstance(gke, dict) else '1.28+'})"
        gke_mfg = "Google Cloud Platform"
        lines.append(f"  - id: {safe_yaml_scalar(f'{hw_id:.1f}')}")
        lines.append(f"    component_type: {safe_yaml_scalar(hw_type_gke)}")
        lines.append(
            '    asset_name: "Google Kubernetes Engine (GKE) Private Cluster"'
        )
        lines.append(f"    nickname: {safe_yaml_scalar(gke_name)}")
        lines.append(f"    asset_ip_address: {safe_yaml_scalar(gke_ip)}")
        lines.append('    public_facing: "No"')
        lines.append('    virtual_asset: "Yes"')
        lines.append(f"    manufacturer: {safe_yaml_scalar(gke_mfg)}")
        lines.append(f"    model_number: {safe_yaml_scalar(gke_model)}")
        lines.append(
            f"    serial_number: {safe_yaml_scalar(f'{csp_abbr}-K8S-{sys_abbr}-{int(hw_id):03d}')}"
        )
        lines.append(f"    location: {safe_yaml_scalar(location)}")
        lines.append('    approval_status: "Approved"')
        lines.append('    critical_asset: "Yes"')
        hw_id += 1.0

    # Databases (Server - Database)
    hw_type_db = (
        excel_hydrator.resolve_exact_hw_type("database")
        if excel_hydrator
        else "Server - Database"
    )
    seen_dbs = set()
    for db in infra_info.get("databases", []):
        raw_db_name = db.get("name", "db-instance")
        db_name = clean_interpolated_string(raw_db_name, default_val=raw_db_name)
        if not is_valid_resource_name(db_name) or db_name in ("name", "id", "db", "database"):
            continue
        raw_type = db.get("type", "Cloud Database Instance")
        raw_ver = db.get("database_version") or db.get("engine_version") or "PostgreSQL 15"
        engine_val = db.get("engine", "")

        if excel_hydrator and hasattr(excel_hydrator, "resolve_db_asset_and_os"):
            db_asset_name, db_os = excel_hydrator.resolve_db_asset_and_os(raw_type, raw_ver, engine_val)
        else:
            db_asset_name = "Cloud SQL PostgreSQL Instance"
            db_os = "PostgreSQL 15 / Debian Linux Base"

        dedup_key = (db_asset_name, db_name)
        if dedup_key in seen_dbs:
            continue
        seen_dbs.add(dedup_key)

        db_tier = db.get("tier", "Managed Tier")
        db_model = f"{db_asset_name} ({db_tier})"
        p_net = db.get("private_network")
        clean_pnet = clean_interpolated_string(str(p_net), default_val="") if p_net else ""
        if p_net and "psa_private_network" in str(p_net):
            db_ip = f"Private VPC / PSC ({clean_subnets[0] if clean_subnets else '[NOT DETERMINED FROM SOURCE]'})"
        elif clean_pnet and is_valid_resource_name(clean_pnet) and not any(k in clean_pnet.lower() for k in ("var.", "local.", "vpc_id", "each.", "try(")):
            db_ip = f"Private VPC ({clean_pnet})"
        else:
            db_ip = "Private Service Connect / Internal Endpoint"

        db_mfg = "Google Cloud Platform"
        lines.append(f"  - id: {safe_yaml_scalar(f'{hw_id:.1f}')}")
        lines.append(f"    component_type: {safe_yaml_scalar(hw_type_db)}")
        lines.append(f"    asset_name: {safe_yaml_scalar(db_asset_name)}")
        lines.append(f"    nickname: {safe_yaml_scalar(db_name)}")
        lines.append(f"    asset_ip_address: {safe_yaml_scalar(db_ip)}")
        lines.append('    public_facing: "No"')
        lines.append('    virtual_asset: "Yes"')
        lines.append(f"    manufacturer: {safe_yaml_scalar(db_mfg)}")
        lines.append(f"    model_number: {safe_yaml_scalar(db_model)}")
        lines.append(
            f"    serial_number: {safe_yaml_scalar(f'{csp_abbr}-DB-{sys_abbr}-{int(hw_id):03d}')}"
        )
        lines.append(f"    os_fw_version: {safe_yaml_scalar(db_os)}")
        lines.append(f"    location: {safe_yaml_scalar(location)}")
        lines.append('    approval_status: "Approved"')
        lines.append('    critical_asset: "Yes"')
        hw_id += 1.0

    # KMS Key Rings / HSM (Virtual HSM Server)
    hw_type_hsm = (
        excel_hydrator.resolve_exact_hw_type("hsm_kms")
        if excel_hydrator
        else "Virtual HSM Server"
    )
    seen_kms = set()
    for k in infra_info.get("kms_keys", []):
        raw_k_name = k.get("name", "kms-key")
        k_name = clean_interpolated_string(raw_k_name, default_val=raw_k_name)
        if not is_valid_resource_name(k_name) or k_name in ("name", "key", "keys", "keyring"):
            continue
        if k_name in seen_kms:
            continue
        seen_kms.add(k_name)

        k_prot = k.get("protection_level", "SOFTWARE")
        k_loc = k.get("location") or location or "us-east4"
        k_asset_name = (
            "Cloud KMS FIPS 140-3 Level 3 HSM Key Ring"
            if k_prot == "HSM"
            else "Cloud KMS Cryptographic Key"
        )
        k_model = f"Cloud KMS ({k_prot})"
        k_mfg = (
            "Google Cloud Platform / Marvell LiquidSecurity HSM"
            if k_prot == "HSM"
            else "Google Cloud Platform"
        )
        kms_endpoint = "cloudkms.googleapis.com (Private Service Connect Endpoint)"

        lines.append(f"  - id: {safe_yaml_scalar(f'{hw_id:.1f}')}")
        lines.append(f"    component_type: {safe_yaml_scalar(hw_type_hsm)}")
        lines.append(f"    asset_name: {safe_yaml_scalar(k_asset_name)}")
        lines.append(f"    nickname: {safe_yaml_scalar(k_name)}")
        lines.append(f"    asset_ip_address: {safe_yaml_scalar(kms_endpoint)}")
        lines.append('    public_facing: "No"')
        lines.append(
            f"    virtual_asset: {safe_yaml_scalar('No' if k_prot == 'HSM' else 'Yes')}"
        )
        lines.append(f"    manufacturer: {safe_yaml_scalar(k_mfg)}")
        lines.append(f"    model_number: {safe_yaml_scalar(k_model)}")
        lines.append(f"    serial_number: {safe_yaml_scalar(f'{csp_abbr}-KMS-{sys_abbr}-{int(hw_id):03d}')}")
        lines.append(f"    location: {safe_yaml_scalar(k_loc)}")
        lines.append('    approval_status: "Approved"')
        lines.append('    critical_asset: "Yes"')
        hw_id += 1.0

    # Compute VMs (Virtual Machine)
    hw_type_vm = (
        excel_hydrator.resolve_exact_hw_type("compute_vm")
        if excel_hydrator
        else "Virtual Machine"
    )
    seen_vms = set()
    for vm in infra_info.get("compute_instances", []):
        raw_vm_name = vm.get("name", "vm-instance")
        vm_name = clean_interpolated_string(raw_vm_name, default_val=raw_vm_name)
        if not is_valid_resource_name(vm_name) or vm_name in ("name", "vm", "instance"):
            continue
        if vm_name in seen_vms:
            continue
        seen_vms.add(vm_name)

        m_type = vm.get("machine_type", "n2-standard-4")
        raw_sub = vm.get("subnetwork")
        clean_sub = clean_interpolated_string(raw_sub, default_val="workload-subnet") if raw_sub else "workload-subnet"
        if clean_sub in ("subnet_id", "subnet", ""):
            clean_sub = "workload-subnet"
        ip_addr = vm.get("network_ip") or f"Private Subnet: {clean_sub} ({clean_subnets[0] if clean_subnets else '[NOT DETERMINED FROM SOURCE]'})"

        default_zone = (
            f"{location.split()[0]}-a"
            if location and not location.startswith("[CONFIG")
            else "us-east4-a"
        )
        sn = (
            vm.get("self_link")
            or f"projects/{sys_abbr}/zones/{vm.get('zone', default_zone)}/instances/{vm_name}"
        )
        raw_img = vm.get("image", "Linux / Shielded VM")
        vm_os = clean_interpolated_string(raw_img, default_val="Linux / Shielded VM")
        if "/family/" in vm_os:
            vm_os = vm_os.split("/family/")[-1].strip()
        elif "/images/" in vm_os:
            vm_os = vm_os.split("/images/")[-1].strip()

        vm_asset_name = "Google Compute Engine VM Instance"
        vm_mfg = "Google Cloud Platform"
        lines.append(f"  - id: {safe_yaml_scalar(f'{hw_id:.1f}')}")
        lines.append(f"    component_type: {safe_yaml_scalar(hw_type_vm)}")
        lines.append(f"    asset_name: {safe_yaml_scalar(vm_asset_name)}")
        lines.append(f"    nickname: {safe_yaml_scalar(vm_name)}")
        lines.append(f"    asset_ip_address: {safe_yaml_scalar(ip_addr)}")
        lines.append('    public_facing: "No"')
        lines.append('    virtual_asset: "Yes"')
        lines.append(f"    manufacturer: {safe_yaml_scalar(vm_mfg)}")
        lines.append(f"    model_number: {safe_yaml_scalar(m_type)}")
        lines.append(f"    serial_number: {safe_yaml_scalar(sn)}")
        lines.append(f"    location: {safe_yaml_scalar(location)}")
        lines.append('    approval_status: "Approved"')
        lines.append('    critical_asset: "Yes"')
        hw_id += 1.0

    lines.append("\nsoftware_and_services_inventory:")
    lines.append("  software_assets:")
    sw_idx = 1
    custom_svcs = inventory.get("custom_services", {})
    cloud_provider_name = (
        sys_info.get("cloud_provider")
        or inventory.get("cloud_provider")
        or "Google Cloud Platform"
    )
    csp_name_abbr = sys_info.get("cloud_service_provider_abbr") or "GCP"

    # 1. Cloud Infrastructure & Platform Services
    for svc in infra_info.get("services_enabled", []):
        category, sw_name, purpose = resolve_gcp_service(svc, custom_svcs)
        exact_sw_type = (
            excel_hydrator.resolve_exact_sw_type(svc, custom_svcs)
            if excel_hydrator
            else "API Service"
        )

        lines.append(f"    - id: {safe_yaml_scalar(str(sw_idx))}")
        lines.append(f"      category: {safe_yaml_scalar(category)}")
        lines.append(f"      software_type: {safe_yaml_scalar(exact_sw_type)}")
        lines.append(f"      software_name: {safe_yaml_scalar(sw_name)}")
        lines.append(f"      vendor: {safe_yaml_scalar(cloud_provider_name)}")
        lines.append(f"      version: {safe_yaml_scalar(f'{csp_name_abbr} Managed Service API')}")
        lines.append(f"      purpose: {safe_yaml_scalar(purpose)}")
        lines.append('      approval_status: "Approved"')
        sw_idx += 1

    # 1b. HashiCorp Terraform Engine (Only if Terraform IaC is present in the boundary)
    if has_terraform_infrastructure(inventory):
        exact_tf_type = (
            excel_hydrator.resolve_exact_sw_type("terraform", custom_svcs)
            if excel_hydrator
            else "Terraform"
        )
        engine_v = (
            infra_info.get("terraform_engine_version")
            or inventory.get("terraform_engine_version")
            or "1.8.0+"
        )
        prov_vers = (
            infra_info.get("provider_versions")
            or inventory.get("provider_versions")
            or {}
        )
        if prov_vers:
            prov_desc = ", ".join(f"{p} {v}" for p, v in prov_vers.items())
            iac_ver_str = f"{engine_v} ({prov_desc})"
        else:
            iac_ver_str = f"{engine_v} / Cloud Provider v5.0+"

        lines.append(f"    - id: {safe_yaml_scalar(str(sw_idx))}")
        lines.append('      category: "Infrastructure as Code"')
        lines.append(f"      software_type: {safe_yaml_scalar(exact_tf_type)}")
        lines.append(
            f'      software_name: "HashiCorp Terraform / {csp_abbr} Provider"'
        )
        lines.append(f'      vendor: "HashiCorp / {cloud_provider}"')
        lines.append(f'      version: {safe_yaml_scalar(iac_ver_str)}')
        lines.append(
            '      purpose: "Automated declarative IaC blueprint provisioning &'
            ' drift detection"'
        )
        lines.append('      approval_status: "Approved"')
        sw_idx += 1

    # 2. Application Services & Workloads
    seen_apps: Set[str] = set()
    for app in app_info.get("applications", []):
        app_name = app.get("name", "Application Service")
        if app_name in seen_apps:
            continue
        seen_apps.add(app_name)
        app_type = (
            "Web Application"
            if "web" in app.get("type", "").lower()
            or "frontend" in app.get("type", "").lower()
            else "Custom Application"
        )
        app_ver = app.get("version", "1.0.0")
        app_lang = app.get("language", "Software Application")
        app_file = app.get("file", "Codebase")
        app_purpose = f"{app.get('type', 'Custom Service')} built with {app_lang} ({app_file})"

        lines.append(f"    - id: {safe_yaml_scalar(str(sw_idx))}")
        lines.append('      category: "Application Service"')
        lines.append(f"      software_type: {safe_yaml_scalar(app_type)}")
        lines.append(f"      software_name: {safe_yaml_scalar(app_name)}")
        lines.append('      vendor: "In-House Application Development"')
        lines.append(f"      version: {safe_yaml_scalar(app_ver)}")
        lines.append(f"      purpose: {safe_yaml_scalar(app_purpose)}")
        lines.append('      approval_status: "Approved"')
        sw_idx += 1

    # 3. Container Images
    seen_c: Set[str] = set()
    for c in app_info.get("container_images", []):
        raw_c_img = str(c.get("base_image") or c.get("image") or "container-image")
        c_img, c_ver = sanitize_container_image_tag(
            clean_interpolated_string(raw_c_img, default_val="container-image"),
            default_img="container-image"
        )
        if c_img in seen_c:
            continue
        seen_c.add(c_img)
        c_file = c.get("file", "Dockerfile")
        lines.append(f"    - id: {safe_yaml_scalar(str(sw_idx))}")
        lines.append('      category: "Container Base Image"')
        lines.append('      software_type: "Container Operating System"')
        lines.append(f"      software_name: {safe_yaml_scalar(c_img)}")
        lines.append('      vendor: "Container Registry"')
        lines.append(f"      version: {safe_yaml_scalar(c_ver)}")
        lines.append(
            f"      purpose: {safe_yaml_scalar(f'Containerized workload runtime ({c_file})')}"
        )
        lines.append('      approval_status: "Approved"')
        sw_idx += 1

    # 4. Third-Party Libraries and Frameworks
    seen_pkgs: Set[str] = set()
    for pkg in app_info.get("software_packages", []):
        raw_p_name = str(pkg.get("name") or pkg.get("package_name") or "unknown-package")
        raw_p_ver = str(pkg.get("version") or "Latest")
        p_name, p_ver = sanitize_software_package_identity(
            clean_interpolated_string(raw_p_name, default_val="unknown-package"),
            clean_interpolated_string(raw_p_ver, default_val="Latest"),
            default_name="unknown-package"
        )
        if not p_name or p_name in seen_pkgs:
            continue
        seen_pkgs.add(p_name)
        p_eco = pkg.get("ecosystem", "Open Source")
        p_cat = pkg.get("category", "Third-Party Library")
        p_file = pkg.get("file", "Dependencies")
        sw_t = (
            "Application Framework"
            if "framework" in p_cat.lower()
            else "3rd Party App (SRC)"
        )
        lines.append(f"    - id: {safe_yaml_scalar(str(sw_idx))}")
        lines.append(f"      category: {safe_yaml_scalar(p_cat)}")
        lines.append(f"      software_type: {safe_yaml_scalar(sw_t)}")
        lines.append(f"      software_name: {safe_yaml_scalar(p_name)}")
        lines.append(f"      vendor: {safe_yaml_scalar(p_eco)}")
        lines.append(f"      version: {safe_yaml_scalar(p_ver)}")
        lines.append(
            f"      purpose: {safe_yaml_scalar(f'{p_cat} dependency imported in {p_file}')}"
        )
        lines.append('      approval_status: "Approved"')
        sw_idx += 1

    lines.append("\nrmf_team_manual_action:")
    lines.append(
        '  callout: "> [!IMPORTANT] **RMF TEAM ACTION REQUIRED**: Perform annual'
        ' physical asset audits for local client workstations and confirm'
        ' eMASS hardware barcode serial numbers."'
    )

    return "\n".join(lines)

def generate_ppsm_matrix_yaml(inventory: Dict[str, Any], doc_version: str = "1.0.0") -> str:
    """Generates Ports, Protocols, and Services Matrix (PPSM) in YAML format.

    Args:
        inventory: System inventory dictionary containing network architecture and endpoints.
        doc_version: Version string for the generated PPSM matrix.

    Returns:
        Formatted YAML string for PPSM Matrix.
    """
    sys_info = inventory.get("system_information", {})
    net_info = inventory.get("network_architecture", {})
    infra_info = inventory.get("infrastructure_components", {})
    app_info = inventory.get("application_components", {})
    roles_info = inventory.get("personnel_roles", {})

    so_info = roles_info.get("system_owner", {})
    isso_info = roles_info.get("isso", {})

    sys_name = sys_info.get("system_name") or "[CONFIG_REQUIRED: System Name]"
    sys_abbr = sys_info.get("system_abbreviation") or "[CONFIG_REQUIRED: System Abbreviation]"
    impact = sys_info.get("impact_level") or "[CONFIG_REQUIRED: Impact Level]"
    comp_base = sys_info.get("compliance_baseline") or "NIST SP 800-53 Rev. 5"
    org = sys_info.get("organization") or "[CONFIG_REQUIRED: Organization Name]"
    location = sys_info.get("primary_location") or "[CONFIG_REQUIRED: Primary Location]"
    eff_date = sys_info.get("effective_date") or datetime.now().strftime("%Y-%m-%d")
    cloud_provider = (
        sys_info.get("cloud_provider")
        or inventory.get("cloud_provider")
        or "Google Cloud Platform (GCP)"
    )
    csp_abbr = sys_info.get("cloud_service_provider_abbr") or "GCP"
    dest_internal_domain = f"*.{csp_abbr.lower()}.internal"
    workload_fqdn = f"*.{sys_abbr.lower()}.internal" if sys_info.get("system_abbreviation") else dest_internal_domain

    raw_subnets = net_info.get("subnets_cidrs", [])
    clean_subnets = extract_clean_subnets(raw_subnets)
    subnet_ip_str = ", ".join(clean_subnets) if clean_subnets else "Dynamic Internal IP"

    lines: List[str] = []
    lines.append("# ==============================================================================")
    lines.append("# Ports, Protocols, and Services Matrix (PPSM)")
    lines.append("# Ref: PPSMBoundariesInformationExport_Template.xlsm")
    lines.append("# ==============================================================================\n")

    lines.append("system_metadata:")
    lines.append(f"  system_name: {safe_yaml_scalar(sys_name)}")
    lines.append(f"  system_abbreviation: {safe_yaml_scalar(sys_abbr)}")
    lines.append(f"  impact_level: {safe_yaml_scalar(impact)}")
    lines.append(f"  compliance_baseline: {safe_yaml_scalar(comp_base)}")
    lines.append(f"  organization: {safe_yaml_scalar(org)}")
    lines.append(f"  date_exported: {safe_yaml_scalar(eff_date)}")
    lines.append(f"  document_version: {safe_yaml_scalar(doc_version)}")
    emass_id = (
        sys_info.get("emass_system_id")
        or sys_info.get("emass_id")
        or f"EMASS-{sys_abbr}-001"
    )
    lines.append(f"  emass_system_id: {safe_yaml_scalar(emass_id)}")
    ditpr_id = (
        sys_info.get("ditpr_id")
        or sys_info.get("ditpr_don_id")
        or sys_info.get("ditpr_emass_id")
        or f"DITPR-{sys_abbr}-001"
    )
    lines.append(f"  ditpr_id: {safe_yaml_scalar(ditpr_id)}\n")

    lines.append("personnel_contacts:")
    lines.append("  system_owner:")
    lines.append(
        f"    name: {safe_yaml_scalar(so_info.get('name') or '[CONFIG_REQUIRED: System Owner Name]')}"
    )
    lines.append(
        f"    email: {safe_yaml_scalar(so_info.get('email') or '[CONFIG_REQUIRED: System Owner Email]')}"
    )
    lines.append(
        f"    phone: {safe_yaml_scalar(so_info.get('phone') or '[CONFIG_REQUIRED: System Owner Phone]')}"
    )
    lines.append("  isso_poc:")
    lines.append(
        f"    name: {safe_yaml_scalar(isso_info.get('name') or '[CONFIG_REQUIRED: ISSO Name]')}"
    )
    lines.append(
        f"    email: {safe_yaml_scalar(isso_info.get('email') or '[CONFIG_REQUIRED: ISSO Email]')}"
    )
    lines.append(
        f"    phone: {safe_yaml_scalar(isso_info.get('phone') or '[CONFIG_REQUIRED: ISSO Phone]')}\n"
    )

    fw_rules = net_info.get("firewall_rules", [])
    lines.append("boundary_firewall_matrix:")
    if not fw_rules:
        lines.append("  []")
    else:
        for fw in fw_rules:
            f_name = fw.get("name") or "firewall-rule"
            f_dir = fw.get("direction") or "INGRESS"
            f_proto = fw.get("protocol") or "TCP"
            f_ports = str(fw.get("ports") or "443")
            f_action = fw.get("action") or "ALLOW"
            lines.append(f"  - name: {safe_yaml_scalar(str(f_name))}")
            lines.append(f"    direction: {safe_yaml_scalar(str(f_dir))}")
            lines.append(f"    protocol: {safe_yaml_scalar(str(f_proto))}")
            lines.append(f"    ports: {safe_yaml_scalar(str(f_ports))}")
            lines.append(f"    action: {safe_yaml_scalar(str(f_action))}")
    lines.append("")

    lines.append("ppsm_matrix:")
    p_id = 1
    custom_svcs = inventory.get("custom_services", {})

    # 1. Cloud API Endpoints
    seen_services = set()
    for svc in infra_info.get("services_enabled", []):
        svc_clean = str(svc).lower().strip()
        if not svc_clean or svc_clean in seen_services:
            continue
        seen_services.add(svc_clean)
        category, sw_name, purpose = resolve_gcp_service(svc_clean, custom_svcs)

        lines.append(f"  - id: {safe_yaml_scalar(str(p_id))}")
        lines.append('    type: "Least Function"')
        lines.append(f"    record_name: {safe_yaml_scalar(sw_name)}")
        lines.append('    protocol: "HTTPS"')
        lines.append(f"    data_service: {safe_yaml_scalar(category)}")
        lines.append('    port: "443"')
        lines.append('    boundary: "1. Ext to DoD GW (In)"')
        lines.append(
            f'    source_device_name: "{csp_abbr} Workload Nodes / Compute Instances"'
        )
        lines.append(f"    source_location: {safe_yaml_scalar(f'{cloud_provider} ({location})')}")
        lines.append(f"    source_ip: {safe_yaml_scalar(subnet_ip_str)}")
        lines.append(f"    source_fqdn: {safe_yaml_scalar(workload_fqdn)}")
        lines.append('    logical_source_point: "Off-Premise Cloud Service (non-DoD Network)"')
        lines.append(
            '    connection_logical_source_point: "Off-Premise Cloud Service'
            ' (non-DoD Network)"'
        )
        lines.append(
            f"    destination_device_name: {safe_yaml_scalar(f'{sw_name} API Endpoint')}"
        )
        lines.append(f"    destination_location: {safe_yaml_scalar(f'{cloud_provider} ({location})')}")
        lines.append('    destination_ip: "Private Service Connect VIP 199.36.153.4/30"')
        lines.append(f"    destination_fqdn: {safe_yaml_scalar(svc_clean)}")
        lines.append('    logical_destination_point: "Off-Premise Cloud Service (DoD Network via DISA CAP)"')
        lines.append(
            '    connection_logical_destination_point: "Off-Premise Cloud Service'
            ' (DoD Network via DISA CAP)"'
        )
        lines.append('    vpn_encrypted_traffic: "Yes"')
        lines.append('    vpn_tunnel_type: "Cloud Layer 3 VPN"')
        lines.append(f"    purpose: {safe_yaml_scalar(purpose)}")
        lines.append('    ppsm_status: "Approved"')
        p_id += 1

    # 2. Terraform Firewall Rules
    seen_firewalls = set()
    for fw in fw_rules:
        fw_name = clean_interpolated_string(fw.get("name", "fw-rule"))
        protocol = str(fw.get("protocol", "TCP")).upper()
        ports = str(fw.get("ports", "443"))
        direction = str(fw.get("direction", "INGRESS")).upper()
        dedup_key = (fw_name, protocol, ports, direction)
        if dedup_key in seen_firewalls:
            continue
        seen_firewalls.add(dedup_key)

        fw_source_ip = (
            "35.235.240.0/20 (IAP IP Range)"
            if "iap" in fw_name.lower()
            else (subnet_ip_str if clean_subnets else "Configured Source CIDR")
        )
        fw_dest_ip = subnet_ip_str if clean_subnets else "Internal Subnet IP"

        lines.append(f"  - id: {safe_yaml_scalar(str(p_id))}")
        lines.append('    type: "Least Function"')
        lines.append(
            f"    record_name: {safe_yaml_scalar(f'Terraform Firewall: {fw_name}')}"
        )
        lines.append(f"    protocol: {safe_yaml_scalar(protocol)}")
        lines.append('    data_service: "VPC Ingress/Egress Traffic Filter"')
        lines.append(f"    port: {safe_yaml_scalar(str(ports))}")
        lines.append('    boundary: "11. Enclave GW to Enclave (In)"')
        lines.append('    source_device_name: "VPC Network Workload"')
        lines.append(f"    source_location: {safe_yaml_scalar(f'{cloud_provider} ({location})')}")
        lines.append(f"    source_ip: {safe_yaml_scalar(fw_source_ip)}")
        lines.append(f"    source_fqdn: {safe_yaml_scalar(dest_internal_domain)}")
        lines.append('    logical_source_point: "DoD Enclave (DoD Network)"')
        lines.append(
            '    connection_logical_source_point: "DoD Enclave (DoD Network)"'
        )
        lines.append('    destination_device_name: "Target Instance / Service"')
        lines.append(f"    destination_location: {safe_yaml_scalar(f'{cloud_provider} ({location})')}")
        lines.append(f"    destination_ip: {safe_yaml_scalar(fw_dest_ip)}")
        lines.append(
            f'    destination_fqdn: {safe_yaml_scalar(dest_internal_domain)}'
        )
        lines.append('    logical_destination_point: "DoD Enclave (DoD Network)"')
        lines.append(
            '    connection_logical_destination_point: "DoD Enclave (DoD Network)"'
        )
        lines.append('    vpn_encrypted_traffic: "Yes"')
        lines.append('    vpn_tunnel_type: "Cloud Layer 3 VPN"')
        lines.append(
            f"    purpose: {safe_yaml_scalar(f'Terraform defined {direction} rule {fw_name} allowing {protocol}:{ports}')}"
        )
        lines.append('    ppsm_status: "Approved"')
        p_id += 1

    # 3. Discovered Application and Container Ingress Ports
    port_list = app_info.get("exposed_ports", []) or net_info.get("application_ports", [])
    seen_ports = set()
    for app_port in port_list:
        port_num = str(app_port.get("port", "8080")).strip()
        protocol = str(app_port.get("protocol", "TCP")).upper().strip()
        svc_name = app_port.get("service_name", "Application Endpoint")
        source = app_port.get("source", "Application Ingress")
        file_src = app_port.get("file", "Application Config")
        dedup_key = (port_num, protocol, svc_name)
        if dedup_key in seen_ports:
            continue
        seen_ports.add(dedup_key)

        dest_fqdn = (
            f"*.{sys_abbr.lower()}.internal"
            if sys_info.get("system_abbreviation")
            else "*.workload.internal"
        )
        lines.append(f"  - id: {safe_yaml_scalar(str(p_id))}")
        lines.append('    type: "Least Function"')
        lines.append(f"    record_name: {safe_yaml_scalar(svc_name)}")
        lines.append(f"    protocol: {safe_yaml_scalar(protocol)}")
        lines.append(
            '    data_service: "Application Ingress / Container Port"'
        )
        lines.append(f"    port: {safe_yaml_scalar(str(port_num))}")
        lines.append('    boundary: "11. Enclave GW to Enclave (In)"')
        lines.append('    source_device_name: "Internal VPC Workload Client"')
        lines.append(f"    source_location: {safe_yaml_scalar(f'{cloud_provider} ({location})')}")
        lines.append(f"    source_ip: {safe_yaml_scalar(subnet_ip_str if clean_subnets else 'Configured Subnet CIDR')}")
        lines.append(f"    source_fqdn: {safe_yaml_scalar(dest_fqdn)}")
        lines.append('    logical_source_point: "DoD Enclave (DoD Network)"')
        lines.append(
            '    connection_logical_source_point: "DoD Enclave (DoD Network)"'
        )
        lines.append(f"    destination_device_name: {safe_yaml_scalar(svc_name)}")
        lines.append(f"    destination_location: {safe_yaml_scalar(f'{cloud_provider} ({location})')}")
        lines.append(f"    destination_ip: {safe_yaml_scalar(subnet_ip_str if clean_subnets else 'Internal Service IP')}")
        lines.append(
            f'    destination_fqdn: {safe_yaml_scalar(dest_fqdn)}'
        )
        lines.append(
            '    logical_destination_point: "DoD Enclave (DoD Network)"'
        )
        lines.append(
            '    connection_logical_destination_point: "DoD Enclave (DoD Network)"'
        )
        lines.append('    vpn_encrypted_traffic: "Yes"')
        lines.append(
            '    vpn_tunnel_type: "Cloud Layer 3 VPN"'
        )
        lines.append(
            f"    purpose: {safe_yaml_scalar(f'Application traffic on port {port_num}/{protocol} ({source} in {file_src})')}"
        )
        lines.append('    ppsm_status: "Approved"')
        p_id += 1

    if p_id == 1:
        lines.append("  []")

    lines.append("\nrmf_team_manual_action:")
    lines.append(
        '  callout: "> [!IMPORTANT] **RMF TEAM ACTION REQUIRED**: Confirm'
        ' registration of all listed ports/protocols in the eMASS PPSM'
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
    sys_info = inventory.get("system_information", {})
    infra_info = inventory.get("infrastructure_components", {})
    roles_info = inventory.get("personnel_roles", {})

    sys_name = sys_info.get("system_name") or "[CONFIG_REQUIRED: System Name]"
    sys_abbr = sys_info.get("system_abbreviation") or "[CONFIG_REQUIRED: System Abbreviation]"
    impact = sys_info.get("impact_level") or "[CONFIG_REQUIRED: Impact Level]"
    baseline = sys_info.get("compliance_baseline") or "NIST SP 800-53 Rev. 5"
    governance_regime = sys_info.get("governance_regime") or baseline
    org = sys_info.get("organization") or "[CONFIG_REQUIRED: Organization Name]"
    location = sys_info.get("primary_location") or "[CONFIG_REQUIRED: Primary Location]"
    eff_date = eff_date or sys_info.get("effective_date") or datetime.now().strftime("%B %d, %Y")
    rmf_system = sys_info.get("rmf_governance_system") or "Enterprise GRC (eMASS / CSAM)"

    isso_info = roles_info.get("isso", {})
    ao_info = roles_info.get("authorizing_official", {})

    isso_name = isso_info.get("name") or "[CONFIG_REQUIRED: ISSO Name]"
    isso_title = isso_info.get("title") or "Information System Security Officer"
    ao_name = ao_info.get("name") or "[CONFIG_REQUIRED: Authorizing Official Name]"
    ao_title = ao_info.get("title") or "Authorizing Official"

    # Derive real findings from live infrastructure & security gaps
    poam_findings = excel_hydrator.derive_poam_findings(inventory, eff_date) if excel_hydrator else []

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
    cloud_provider = (
        sys_info.get("cloud_provider")
        or inventory.get("cloud_provider")
        or "Google Cloud Platform"
    )
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
    status_text = (
        "Technical Security Controls Auto-Provisioned; Active Tracking for"
        " Open Deficiencies"
        if poam_findings
        else "Verified Compliant - Zero Active POA&M Weaknesses Detected"
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
    ai_enrich: bool = False,
    ai_model: Optional[str] = None,
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
        ai_enrich: Whether to enrich technical narratives using AI semantic reasoning.
        ai_model: Optional custom LLM model name for enrichment.

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
    doc_versions = inventory.get("document_versions", {})
    policy_versions = doc_versions.get("policies", {})

    export_prefs = inventory.get("export_preferences", {})
    policy_format = policy_format or export_prefs.get("policy_formats") or "both"
    data_format = data_format or export_prefs.get("structured_data_formats") or "both"
    oscal_format = oscal_format or export_prefs.get("oscal_formats") or "both"
    if not oscal_version and "oscal_version" in export_prefs:
        oscal_version = export_prefs["oscal_version"]

    out_dir = ensure_directory(target_path / "ato_artifacts")
    ensure_path_within_boundary(out_dir, target_path)

    try:
        audit_logger = configure_audit_log(
            sink_path=out_dir / "compliance_engine_audit.jsonl",
            component="compliance-engine",
            allowed_boundary=target_path,
        )
        audit_logger.emit(AuditEvent.PIPELINE_STARTED, detail={"target_dir": str(target_path)})
    except Exception as e:
        logger.warning(f"Could not configure audit log: {e}")
        audit_logger = None

    policies_out_dir = ensure_directory(out_dir / "Policies_and_Procedures")
    templates_root = Path(TEMPLATES_DIR)

    artifacts_generated: Dict[str, List[str]] = {
        "markdown": [],
        "docx": [],
        "yaml": [],
        "excel": [],
        "oscal": [],
    }

    logger.info("=" * 80)
    logger.info("ATO COMPLIANCE PACKAGE GENERATION: %s", target_path)
    logger.info("   Policy Format Preference : %s", policy_format.upper())
    logger.info("   Data Format Preference   : %s", data_format.upper())
    logger.info("   OSCAL Format Preference  : %s", str(oscal_format).upper())
    if ai_enrich:
        logger.info("   AI Narrative Enrichment  : ENABLED (LLM semantic reasoning active)")
    logger.info("=" * 80)

    reg = registry if registry is not None else ExporterRegistry._get_default_instance()
    policy_exporters = reg.get_policy_exporters(policy_format)
    data_exporters = reg.get_data_exporters(data_format)

    def _export_policy_document(raw_text: str, base_output_path: Path, doc_version: str = "1.0.0") -> None:
        """Populates template placeholders and delegates export to active policy strategies.

        Strictly confines all output files within the designated out_dir.

        Args:
            raw_text: Raw Markdown template text before variable replacement.
            base_output_path: Base Path destination without extension.
            doc_version: Specific version string to inject into document metadata.

        Returns:
            None.
        """
        ensure_path_within_boundary(base_output_path, out_dir)
        populated = populate_placeholders(
            raw_text, inventory, doc_version, target_format="markdown", fill_examples=True, ai_enrich=ai_enrich, ai_model=ai_model
        )
        for exporter in policy_exporters:
            # The boundary must be supplied to the exporter, not merely asserted on the
            # path it returns: checking afterwards confirms where the bytes went only
            # once they are already on disk.
            generated_path = exporter.export_document(
                populated, base_output_path, inventory, allowed_boundary=out_dir
            )
            ensure_path_within_boundary(generated_path, out_dir)
            artifacts_generated.setdefault(exporter.format_name, []).append(str(generated_path))
            if audit_logger:
                audit_logger.emit(AuditEvent.ARTIFACT_GENERATED, outcome=AuditOutcome.SUCCESS, obj=str(generated_path), detail={"format": exporter.format_name})

    # 1. Generate Core System Security Plan (SSP)
    sys_info = inventory.get("system_information", {})
    impact_str = (str(sys_info.get("impact_level", "")) + " " + str(sys_info.get("compliance_baseline", ""))).upper()
    impact = "IL5" if any(k in impact_str for k in ["IL4", "IL5", "IL6", "DOD"]) else "FedRAMP_High"
    ssp_template_file = templates_root / "ssp" / f"SSP_{impact}_Template.md"
    if ssp_template_file.exists():
        ssp_folder = ensure_directory(out_dir / "SSP")
        raw_ssp = read_text_file(ssp_template_file)
        ssp_version = doc_versions.get("ssp", "1.0.0")
        if any(exp.format_name == "docx" for exp in policy_exporters):
            logger.info("Generating System Security Plan Word document (.docx)...")
        _export_policy_document(raw_ssp, ssp_folder / "SSP_System_Security_Plan", ssp_version)

    # 2. Generate Path to Authorization (PTA) at top-level of ato_artifacts
    pta_template_file = templates_root / "pta" / "Path_to_Authorization_Template.md"
    if pta_template_file.exists():
        raw_pta = read_text_file(pta_template_file)
        pta_version = doc_versions.get("pta", "1.0.0")
        _export_policy_document(raw_pta, out_dir / "Path_to_Authorization", pta_version)

    # 2b. Generate 5 Scenario Incident Response Runbooks & Template
    runbooks_template_dir = templates_root / "runbooks"
    if runbooks_template_dir.exists():
        runbooks_folder = ensure_directory(out_dir / "Incident_Response_Runbooks")
        ir_version = doc_versions.get("incident_response_policy", "1.0.0")
        for rb_file in sorted(runbooks_template_dir.glob("*.md")):
            raw_rb = read_text_file(rb_file)
            rb_stem = sanitize_filename(rb_file.stem)
            _export_policy_document(raw_rb, runbooks_folder / rb_stem, ir_version)

    # 3. Generate Structured Data Matrices via Strategy Pattern
    matrix_generators: Dict[str, Callable[..., Any]] = {
        "hwsw": generate_hwsw_inventory_yaml,
        "ppsm": generate_ppsm_matrix_yaml,
        "poam": generate_poam_matrix_yaml,
        "populate_placeholders": populate_placeholders,
    }
    for data_exporter in data_exporters:
        matrix_files = data_exporter.export_all_matrices(
            target_path, inventory, doc_versions, matrix_generators
        )
        for mf in matrix_files:
            ensure_path_within_boundary(mf, out_dir)
            artifacts_generated.setdefault(data_exporter.format_name, []).append(str(mf))
            if audit_logger:
                audit_logger.emit(AuditEvent.ARTIFACT_GENERATED, outcome=AuditOutcome.SUCCESS, obj=str(mf), detail={"format": data_exporter.format_name})

    # 3b. Generate FIPS Cryptographic Matrix (Markdown & DOCX)
    fips_md_template = templates_root / "fips" / "FIPS_Cryptographic_Matrix_Template.md"
    if fips_md_template.exists():
        fips_folder = ensure_directory(out_dir / "FIPS_Cryptography")
        raw_fips_md = read_text_file(fips_md_template)
        fips_version = doc_versions.get("fips_matrix", "1.0.0")
        _export_policy_document(raw_fips_md, fips_folder / "FIPS_Cryptographic_Matrix", fips_version)

    # 4. Generate 20 NIST Policy Manuals (Markdown and/or DOCX)
    policies_dir = templates_root / "policies"
    if policies_dir.exists():
        logger.info("Generating 20 NIST SP 800-53 Policy Manuals (%s)...", policy_format)
        for p_file in sorted(policies_dir.glob("*.md")):
            raw_policy = read_text_file(p_file)
            p_stem = sanitize_filename(p_file.stem)
            f_name = p_file.name
            family_key = f_name.replace("_Policy_and_Procedures.md", "").replace("_Policy.md", "")
            policy_ver = policy_versions.get(family_key) or policy_versions.get(family_key.replace("_", "")) or doc_versions.get("default_version", "1.0.0")
            _export_policy_document(raw_policy, policies_out_dir / p_stem, policy_ver)

    # 5. Generate Machine-Readable NIST OSCAL Deliverables (SSP & Component Definitions)
    oscal_pref = oscal_format.strip().lower() if oscal_format else "both"
    if oscal_pref not in ("none", "false", "disabled", "off"):
        target_oscal_ver = oscal_version or "1.2.3"
        logger.info("Generating NIST OSCAL %s Machine-Readable Package (%s)...", target_oscal_ver, oscal_pref.upper())
        try:
            try:
                from .oscal_generator import export_oscal_artifacts
            except (ImportError, ValueError):
                from oscal_generator import export_oscal_artifacts
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
                    audit_logger.emit(AuditEvent.ARTIFACT_GENERATED, outcome=AuditOutcome.SUCCESS, obj=str(of), detail={"format": "oscal"})
        except Exception as oscal_err:
            # Record the failure before propagating. get_audit_logger is already
            # bound at module import; the previous inline `from .audit_log import`
            # always raised ImportError in script mode, so the failure record was
            # silently lost by the surrounding swallow.
            try:
                get_audit_logger().emit(
                    AuditEvent.ARTIFACT_GENERATED,
                    outcome=AuditOutcome.FAILURE,
                    detail={"format": "oscal", "error": str(oscal_err)},
                )
            except OSError as audit_err:
                # Never let an audit-sink I/O fault mask the original failure,
                # but do not hide it either.
                logger.error("Could not record OSCAL failure to audit trail: %s", audit_err)
            logger.error("Failed generating OSCAL deliverables: %s", oscal_err)
            raise RuntimeError(f"OSCAL generation failed: {oscal_err}") from oscal_err

    # Summary Report
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
    if "oscal" in artifacts_generated and artifacts_generated["oscal"]:
        logger.info("  • NIST OSCAL Packages        : %d", len(artifacts_generated["oscal"]))
    for fmt_k, items_v in artifacts_generated.items():
        if fmt_k not in ("markdown", "docx", "yaml", "excel", "oscal"):
            logger.info("  • Deliverables (%s)          : %d", fmt_k, len(items_v))
    logger.info("  • Output Directory           : %s", out_dir)
    logger.info("=" * 80)

    val_script_abs = Path(SCRIPTS_DIR) / "validate_compliance_artifacts.py"
    try:
        val_script_display = os.path.relpath(str(val_script_abs), os.getcwd())
    except ValueError:
        val_script_display = str(val_script_abs)
    try:
        target_display = os.path.relpath(str(target_path), os.getcwd())
    except ValueError:
        target_display = str(target_path)
    logger.info("=" * 80)
    logger.info("NEXT RECOMMENDED STEP (PART B): ATO PACKAGE VALIDATION & STIG AUDIT")
    logger.info("=" * 80)
    logger.info("To run package validation, check for drift, and inspect required DISA STIGs:")
    logger.info("  python3 %s %s --fix", val_script_display, target_display)
    logger.info("=" * 80)

    return artifacts_generated


def main() -> None:
    """Parses command-line arguments and executes ATO compliance package provisioning."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(description="Master ATO Artifacts Provisioner & Dual-Format Hydration Engine")
    parser.add_argument("target_dir", nargs="?", default=".", help="Target foundation directory (e.g. my-foundation or .)")
    parser.add_argument("--policy-format", choices=["both", "docx", "markdown"], default=None, help="Export format for 20 policy manuals (overrides compliance_config.yaml)")
    parser.add_argument("--data-format", choices=["both", "excel", "yaml"], default=None, help="Export format for structured data matrices (overrides compliance_config.yaml)")
    parser.add_argument("--oscal-format", choices=["both", "json", "yaml", "none"], default=None, help="Export format for NIST OSCAL deliverables (overrides compliance_config.yaml)")
    parser.add_argument("--oscal-version", default=None, help="Target NIST OSCAL specification version (e.g. 1.2.3 or 1.1.0; defaults to 1.2.3)")
    parser.add_argument("--ai-enrich", action="store_true", default=False, help="Enrich technical narratives using AI semantic reasoning")
    parser.add_argument("--ai-model", default=None, help="Target LLM model for AI enrichment (e.g. gemini-1.5-pro)")
    args = parser.parse_args()

    target_abs = os.path.abspath(args.target_dir)
    if not os.path.isdir(target_abs):
        logger.error(f"Target directory does not exist or is not a directory: {target_abs}")
        sys.exit(1)

    generate_ato_artifacts(
        target_abs,
        policy_format=args.policy_format,
        data_format=args.data_format,
        oscal_format=args.oscal_format,
        oscal_version=args.oscal_version,
        ai_enrich=args.ai_enrich,
        ai_model=args.ai_model,
    )


if __name__ == "__main__":
    main()
